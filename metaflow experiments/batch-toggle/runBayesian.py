import configparser
import os
import pickle as pkl
from io import BytesIO
from pprint import pprint
from typing import List
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import tensorflow as tf
import tensorflow_probability as tfp
from metaflow import FlowSpec, Parameter, catch, resources, step, retry, batch
from scipy import stats

import dataUtils
import fileUtils
from log_management import get_logger
from utils import conditionally

tfd = tfp.distributions
tfb = tfp.bijectors

tf.config.threading.set_intra_op_parallelism_threads(1)
tf.config.threading.set_inter_op_parallelism_threads(1)
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)

RUN_TFP_ON_BATCH = False

class RunBayesianSixtyNineOne(FlowSpec):
    bucket_param = Parameter("bucket", type=str, default="mcd-metaflow-batch")
    key_param = Parameter("key", type=str, default="Inputs/config.ini")
    logger = get_logger(__name__, "logger.log")

    @batch(cpu=3, memory=6000)
    @step
    def start(self):
        print("start")
        self.config = dataUtils.read_s3_config(bucket=self.bucket_param, key=self.key_param)
        self.fldrs = fileUtils.S3().init(by="bayesian")
        self.next(self.start_clusters)

    @retry(times=2)
    @batch(cpu=3, memory=6000)
    @step
    def start_clusters(self):
        self.itemClusterFiles = fileUtils.S3().listDir(self.config['s3Config']['train_data_path'], self.logger)
        if len(self.itemClusterFiles) == 0:
            raise Exception("No cluster files")
        self.clusters = dataUtils.strSplit(self.config['runConfig']['clusters'])
        if not self.clusters:
            self.clusters = np.unique([ic.split('_')[1] for ic in self.itemClusterFiles])
        self.next(self.start_itemgroup_clusters, foreach="clusters")

    @retry(times=2)
    @batch(cpu=3, memory=6000)
    @step
    def start_itemgroup_clusters(self):
        batchSize = 50
        self.items = dataUtils.strSplit(self.config['runConfig']['items'])
        if not self.items:
            self.items = np.unique([ic.split('_')[0] for ic in self.itemClusterFiles])

        clusterItems = ['_'.join([item, self.input, self.config['runConfig']['train_end_date']])
                        for item in self.items]
        self.item_groups = [clusterItems[i*batchSize: (i+1)*batchSize] if (i+1)*batchSize < len(clusterItems)
                            else clusterItems[i*batchSize:] for i in range(int(np.ceil(len(clusterItems)/batchSize)))]
        self.next(self.start_item_clusters, foreach="item_groups")

    @retry(times=2)
    @batch(cpu=3, memory=6000)
    @step
    def start_item_clusters(self):
        self.item_group = self.input
        self.logger.info("Number of ItemClusters " + str(len(self.item_group)))
        self.next(self.run_tfp, foreach="item_group")

    @catch(var='tfpError')
    @conditionally(batch(cpu=3, memory=6000), RUN_TFP_ON_BATCH)
    @step
    def run_tfp(self):
        time.sleep(120)
        # train_df = pd.read_csv(os.path.join(
        #     self.config['pathself.config']['dataPath'], self.input))
        # param_dict = pkl.load(open(os.path.join(
        #     self.config['pathself.config']['paramPath']), self.input.split('.')[0]+'.dict'))

        s3Obj = fileUtils.S3()

        self.comboID = self.input

        train_df = s3Obj.read(os.path.join(
            self.config['s3Config']['train_data_path'], self.input+'.csv'), logger=self.logger, type='csv', comboID=self.comboID)
        param_dict = s3Obj.read(os.path.join(
            self.config['s3Config']['train_params_path'], self.input+'.dict'), logger=self.logger, type='pkl', comboID=self.comboID)

        if train_df is None and param_dict is None:
            raise FileNotFoundError

        prior_params = param_dict["prior_params"]
        fixed_effect_cols = param_dict["fixed_effect_cols"]
        random_effect_cols = param_dict["random_effect_cols"]
        Y_col = param_dict["Y_col"]
        group_id_col = param_dict["group_id_col"]
        likelihood_sd = param_dict["likelihood_sd"]
        bijector_info = param_dict["bijector_info"]
        additional_non_modeled_cols_for_output = param_dict["additional_non_modeled_cols_for_output"]
        save_tag = param_dict["save_tag"]
        item = param_dict["item"]
        cluster = param_dict["cluster"]
        rolling_date = param_dict["rolling"]
        # id_string = param_dict["id_string"]
        chains = int(self.config["elasticity_model"]["chains"])
        num_warmup_iters = int(
            self.config["elasticity_model"]["num_warmup_iters"])
        num_iters = int(
            self.config["elasticity_model"]["num_iters"])
        HMC_step_size = np.float(
            self.config["elasticity_model"]["HMC_step_size"])
        num_leapfrog_steps = int(
            self.config["elasticity_model"]["num_leapfrog_steps"])

        # additional output self.config
        save_plots_and_trace = False
        if self.config["elasticity_model"]["save_plots_and_trace"] == "True":
            save_plots_and_trace = True

        if save_plots_and_trace:
            if self.config["elasticity_model"]["plot_features"] == "":
                plot_features = []
            else:
                plot_features = dataUtils.strSplit(
                    self.config["elasticity_model"]["plot_features"])
                if plot_features == "all":
                    plot_features = []

            if self.config["elasticity_model"]["store_ids_to_trace_plot"] == "":
                groups_to_trace_plot = []
            elif self.config["elasticity_model"]["store_ids_to_trace_plot"] == "all":
                groups_to_trace_plot = train_df['store_id'].unique().tolist()
            else:
                groups_to_trace_plot = dataUtils.strSplit(
                    self.config["elasticity_model"]["store_ids_to_trace_plot"])
                groups_to_trace_plot = [
                    int(store) for store in groups_to_trace_plot]
        else:
            plot_features = []
            groups_to_trace_plot = []

        def get_value(dataframe, key, dtype):
            return dataframe[key].values.astype(dtype)

        def test_for_normal_dist(input_samples):
            try:
                _, p_value = stats.shapiro(input_samples)
                if p_value < 0.05:
                    return "Normal Dist"
                else:
                    return "Not Normal Dist"
            except:
                return "Normality test failed"

        def get_ce_item_columns(data: pd.DataFrame, type: str = 'all') -> List[str]:
            try:
                ce_item_cols: List[str] = []
                if type == 'all':
                    ce_item_cols = [x for x in data.columns if "_CE_MBP_" in x]
                elif type == 'substitutes':
                    ce_item_cols = [x for x in data.columns if "_CE_MBP_SUB" in x]
                elif type == 'compliments':
                    ce_item_cols = [x for x in data.columns if "_CE_MBP_COMP" in x]
                return ce_item_cols
            except Exception as e:
                self.logger.error(self.comboID, "Exception while getting cross elastic columns")
                self.logger.error(e, exc_info=True)

        @tf.function(experimental_compile=True, autograph=False)
        def affine(x, kernel_diag, bias=tf.zeros([])):
            kernel_diag = tf.ones_like(x) * kernel_diag
            bias = tf.ones_like(x) * bias
            return x * kernel_diag + bias

        # Encoding Group col and Retaining the mapping
        map_df = pd.DataFrame([list(train_df[group_id_col].unique())]).T.reset_index()
        map_df.sort_values(by=0, inplace=True)
        group_map_dict = map_df.set_index(0).to_dict()['index']
        train_df[group_id_col] = train_df[group_id_col].apply(
            lambda x: group_map_dict[x])

        # adding intercept column
        if "intercept" in train_df.columns:
            self.logger.info(
                "%s - intercept column already exist, using it with assumtion of having values = 1", self.comboID)
        else:
            train_df["intercept"] = 1
        fixed_effect_cols = sorted(fixed_effect_cols)
        random_effect_cols = sorted(random_effect_cols)
        group_count = train_df[group_id_col].nunique()

        # casting and storing feature wise data
        features_train = {
            k: get_value(train_df, key=k, dtype=np.float32)
            for k in random_effect_cols + fixed_effect_cols
        }
        features_train.update({group_id_col: get_value(train_df, key=group_id_col, dtype=np.int32)})

        week_dates = train_df["week_date"]
        if self.config['feature_engineering']['add_price_change_clip_flag'] == 'True':
            if self.config['elasticity_model']['price_column'] == "base_price":
                original_price = train_df[self.config['elasticity_model']
                                          ['price_column']+"_original"]
                clipped_price = train_df[self.config['elasticity_model']
                                         ['price_column']]
            else:
                original_price = train_df[self.config['elasticity_model']
                                          ['price_column']]
        else:
            original_price = train_df[self.config['elasticity_model']
                                      ['price_column']]

        if len(additional_non_modeled_cols_for_output) != 0:
            cross_elastic_cols = get_ce_item_columns(train_df)
            if (len(cross_elastic_cols) != 0):
                additional_non_modeled_cols_for_output = additional_non_modeled_cols_for_output + \
                    cross_elastic_cols
            additional_non_modeled_data_for_output = train_df[additional_non_modeled_cols_for_output]

        labels_train = get_value(train_df, key=Y_col, dtype=np.float32)

        # fixing topological order of features
        joint_dist_list_names = random_effect_cols + fixed_effect_cols
        joint_dist_list_names_reverse = joint_dist_list_names[::-1]

        self.logger.info("%s - generating joint distribution......", self.comboID)

        # master_intercept_mu_sd,master_intercept_sigma_sd,
        base_str = "def varying_intercepts_and_slopes_model(features,prior_params,fixed_effect_cols,random_effect_cols,joint_dist_list_names_reverse,likelihood_sd, group_count, group_id_col, affine): \n"

        # starting JointDistributionSequential
        base_str = base_str + "\treturn tfd.JointDistributionSequential(["

        # adding dists topologically
        for feature in joint_dist_list_names:
            if feature in random_effect_cols:
                if feature == "intercept":
                    base_str = base_str + \
                        "tfd.Normal(loc= float(1.0 *prior_params['" + feature + "']['mu'][0]),scale= float(1.0 *prior_params['" + \
                        feature + \
                        "']['mu'][1]) , name = 'master_mu_" + feature + "') ,"
                    base_str = base_str + \
                        "tfd.HalfCauchy(loc= float(1.0 *prior_params['" + feature + "']['sd'][0]),scale = float(1.0 *prior_params['" + \
                        feature + \
                        "']['sd'][1]) , name = 'master_sd_" + feature + "') ,"
                    base_str = base_str + "lambda " + "master_sd_" + feature + ", master_mu_" + feature + " : " + \
                        "tfd.Independent(tfd.Normal(loc = affine(tf.ones([group_count]) , master_mu_" + feature + \
                        "[..., tf.newaxis]) ,scale = tf.transpose(group_count * [master_sd_" + \
                        feature + "]) , name = 'RE_" + feature + "'), reinterpreted_batch_ndims=1) ,"

                else:
                    if prior_params[feature]["dist"] == "normal":
                        base_str = base_str + \
                            "tfd.Normal(loc= float(1.0 *prior_params['" + feature + "']['mu'][0]),scale= float(1.0 *prior_params['" + \
                            feature + \
                            "']['mu'][1]) , name = 'master_mu_" + \
                            feature + "') ,"
                        base_str = base_str + \
                            "tfd.HalfCauchy(loc= float(1.0 *prior_params['" + feature + "']['sd'][0]),scale = float(1.0 *prior_params['" + \
                            feature + \
                            "']['sd'][1]) , name = 'master_sd_" + \
                            feature + "') ,"
                        base_str = base_str + "lambda " + "master_sd_" + feature + ", master_mu_" + feature + " : " + \
                            "tfd.Independent(tfd.Normal(loc = affine(tf.ones([group_count]) , master_mu_" + feature + \
                            "[..., tf.newaxis]) ,scale = tf.transpose(group_count * [master_sd_" + \
                            feature + "]) , name = 'RE_" + feature + "'), reinterpreted_batch_ndims=1) ,"

            if feature in fixed_effect_cols:
                if prior_params[feature]["dist"] == "normal":
                    base_str = base_str + \
                        "tfd.Normal(loc=float(1.0 *prior_params['" + feature + "']['mu']),scale= float(1.0 *prior_params['" + \
                        feature + "']['sd']), name = 'FE_" + feature + "') ,"
        # adding SD of likelihood
        base_str = base_str + \
            "tfd.HalfCauchy(loc= 0., scale=likelihood_sd ,name='likelihood_sd'),"

        # writing lambda function argument names (reverse topological)
        base_str = base_str + "lambda "
        base_str = base_str + "likelihood_sd,"
        args_names_for_post_process = ["likelihood_sd"]
        for i in joint_dist_list_names_reverse:
            if i in random_effect_cols:
                if i == "intercept":
                    base_str = base_str + "RE_" + i + ","
                    args_names_for_post_process.append("RE_" + i)
                    base_str = base_str + "master_sd_" + i + ","
                    args_names_for_post_process.append("master_sd_" + i)
                    base_str = base_str + "master_mu_" + i + ","
                    args_names_for_post_process.append("master_mu_" + i)
                else:
                    if prior_params[i]["dist"] == "gamma":
                        base_str = base_str + "RE_" + i + ","
                        args_names_for_post_process.append("RE_" + i)
                        base_str = base_str + "master_beta_" + i + ","
                        args_names_for_post_process.append("master_beta_" + i)
                        base_str = base_str + "master_alpha_" + i + ","
                        args_names_for_post_process.append("master_alpha_" + i)
                    elif prior_params[i]["dist"] == "normal":
                        base_str = base_str + "RE_" + i + ","
                        args_names_for_post_process.append("RE_" + i)
                        base_str = base_str + "master_sd_" + i + ","
                        args_names_for_post_process.append("master_sd_" + i)
                        base_str = base_str + "master_mu_" + i + ","
                        args_names_for_post_process.append("master_mu_" + i)
            elif i in fixed_effect_cols:
                base_str = base_str + "FE_" + i + ","
                args_names_for_post_process.append("FE_" + i)

        # writing final likelhood dist and equation
        base_str = base_str[:-1] + " : tfd.MultivariateNormalDiag(loc ="

        # stitching likelihood equation
        for dist_name in joint_dist_list_names:
            if dist_name in random_effect_cols:
                base_str = base_str + \
                    "affine(features['" + dist_name + "'], tf.gather( RE_" + \
                    dist_name + ", features[group_id_col], axis = -1)) +  "
            elif dist_name in fixed_effect_cols:
                base_str = base_str + \
                    "affine(features['" + dist_name + "'], FE_" + \
                    dist_name + "[..., tf.newaxis]) + "
        base_str = base_str[:-3]
        base_str = base_str + ", scale_identity_multiplier=likelihood_sd)"

        # end of JointDistributionSequential
        base_str = base_str + "])"

        exec(base_str)
        varying_intercepts_and_slopes_model_ = locals()["varying_intercepts_and_slopes_model"]

        self.logger.debug(
            "%s - The graph of the distribution is as follows:", self.comboID)
        pprint(varying_intercepts_and_slopes_model_(features_train, prior_params, fixed_effect_cols, random_effect_cols, joint_dist_list_names_reverse,
                                                    likelihood_sd, group_count, group_id_col, affine).resolve_graph())  # master_intercept_mu_sd,master_intercept_sigma_sd

        @tf.function
        def varying_intercepts_and_slopes_log_prob(*a):
            a_ = list(a) + [labels_train]
            return varying_intercepts_and_slopes_model_(features_train, prior_params, fixed_effect_cols, random_effect_cols, joint_dist_list_names_reverse, likelihood_sd, group_count, group_id_col, affine).log_prob(a_)

        # wrapper for HMC sampling, Initial state and bijector declarations
        @tf.function(experimental_compile=True, autograph=False)
        def sample_varying_intercepts_and_slopes(num_chains, num_results, num_burnin_steps):
            self.logger.info("%s - defining NUTS Sampler....", self.comboID)

            self.logger.info(
                "%s - defining initial state and bijectors....", self.comboID)

            initial_state = []
            unconstraining_bijectors = []

            i = 0
            for feature in joint_dist_list_names:
                if feature in random_effect_cols:
                    if feature == "intercept":
                        initial_state.append(tf.ones(
                            [num_chains], name='init_master_1_'+feature)*prior_params[feature]['mu'][0])
                        i += 1
                        initial_state.append(tf.ones(
                            [num_chains], name='init_master_2_'+feature)*prior_params[feature]['sd'][1])
                        i += 1
                        unconstraining_bijectors.append(tfb.Identity())
                        unconstraining_bijectors.append(tfb.Identity())
                        initial_state.append(tf.ones(
                            [num_chains, group_count], name='init_re'+feature)*prior_params[feature]['mu'][0])
                        i += 1
                        unconstraining_bijectors.append(tfb.Identity())
                    elif feature in bijector_info:
                        if bijector_info[feature] == "exp":
                            initial_state.append(tf.ones(
                                [num_chains], name='init_master_1_'+feature)*prior_params[feature]['mu'][0])
                            i += 1
                            initial_state.append(tf.ones(
                                [num_chains], name='init_master_2_'+feature)*prior_params[feature]['sd'][1])
                            i += 1
                            unconstraining_bijectors.append(tfb.Identity())
                            unconstraining_bijectors.append(tfb.Identity())
                            initial_state.append(tf.ones(
                                [num_chains, group_count], name='init_re'+feature)*prior_params[feature]['mu'][0])
                            i += 1
                            unconstraining_bijectors.append(tfb.Exp())
                        else:
                            self.logger.error(
                                "%s - unknown bijector requested for: %s", self.comboID, feature)
                            return None
                    else:
                        initial_state.append(tf.ones(
                            [num_chains], name='init_master_1_'+feature)*prior_params[feature]['mu'][0])
                        i += 1
                        initial_state.append(tf.ones(
                            [num_chains], name='init_master_2_'+feature)*prior_params[feature]['sd'][1])
                        i += 1
                        unconstraining_bijectors.append(tfb.Identity())
                        unconstraining_bijectors.append(tfb.Identity())
                        initial_state.append(tf.ones(
                            [num_chains, group_count], name='init_re'+feature)*prior_params[feature]['mu'][0])
                        i += 1
                        unconstraining_bijectors.append(tfb.Identity())

                elif feature in fixed_effect_cols:
                    if feature in bijector_info:
                        if bijector_info[feature] == "exp":
                            initial_state.append(
                                tf.ones([num_chains], name='init_fe_'+feature)*prior_params[feature]['mu'])
                            i += 1
                            unconstraining_bijectors.append(tfb.Exp())
                        else:
                            self.logger.error(
                                "%s unknown bijector requested for: %s ", self.comboID, feature)
                            return None
                    else:
                        initial_state.append(
                            tf.ones([num_chains], name='init_fe_'+feature)*prior_params[feature]['mu'])
                        i += 1
                        unconstraining_bijectors.append(tfb.Identity())

            initial_state.append(
                tf.ones([num_chains], name='init_likelihood_Sd'))
            unconstraining_bijectors.append(tfb.Identity())

            self.logger.info(
                "%s - Started Sampling with mcmc.sample_chain()....", self.comboID)

            step_size = [tf.fill([num_chains] + [1] * (len(s.shape) - 1), tf.constant(HMC_step_size, np.float32)) for s
                         in
                         initial_state]
            kernel = tfp.mcmc.DualAveragingStepSizeAdaptation(
                tfp.mcmc.TransformedTransitionKernel(
                    inner_kernel=tfp.mcmc.NoUTurnSampler(
                        varying_intercepts_and_slopes_log_prob,
                        step_size=step_size,
                        seed=10, parallel_iterations=1
                    ),
                    bijector=unconstraining_bijectors
                ),
                target_accept_prob=.8,
                num_adaptation_steps=int(0.8 * num_burnin_steps),
                step_size_setter_fn=lambda pkr, new_step_size: pkr._replace(
                    inner_results=pkr.inner_results._replace(
                        step_size=new_step_size)
                ),
                step_size_getter_fn=lambda pkr: pkr.inner_results.step_size,
                log_accept_prob_getter_fn=lambda pkr: pkr.inner_results.log_accept_ratio,
            )

            samples, kernel_results = tfp.mcmc.sample_chain(
                num_results=num_results,
                num_burnin_steps=num_burnin_steps,
                current_state=initial_state,
                kernel=kernel,
                parallel_iterations=1
            )

            acceptance_probs = tf.reduce_mean(tf.cast(
                kernel_results.inner_results.inner_results.is_accepted, tf.float32), axis=0)

            return samples, acceptance_probs

        samples, acceptance_probs = sample_varying_intercepts_and_slopes(
            num_chains=chains, num_results=num_iters, num_burnin_steps=num_warmup_iters)
        self.logger.info("%s - ended Sampling", self.comboID)
        self.logger.info(
            "%s - generating and saving estimates summary...", self.comboID)

        # generating and saving summary of estimates
        a = args_names_for_post_process[::-1]
        b = samples
        sample_dict = dict(zip(a, b))
        Fixed_effect_summary = {}
        Random_effect_summary = {}
        for key in sample_dict:
            if ("master_" in key) or ("FE_" in key):
                temp_data = sample_dict[key].numpy()
                rhat = tfp.mcmc.potential_scale_reduction(temp_data)
                mean_estimate = np.mean(temp_data)
                Fixed_effect_summary[key+"_Rhat"] = {0: rhat.numpy()}
                Fixed_effect_summary[key+"_Mean_Est"] = {0: mean_estimate}
            elif "RE_" in key:
                Random_effect_summary[key + "_Rhat"] = {}
                Random_effect_summary[key + "_Mean_Est"] = {}
                Random_effect_summary[key + "_Mean_Variance"] = {}
                temp_data = sample_dict[key].numpy()
                number_of_groups = temp_data.shape[2]
                for i in range(number_of_groups):
                    group_data = temp_data[:, :, i]
                    rhat = tfp.mcmc.potential_scale_reduction(group_data)
                    mean_estimate = np.mean(group_data)
                    mean_variance_across_chains = np.mean(
                        np.var(group_data, axis=0))
                    Random_effect_summary[key + "_Rhat"][i] = rhat.numpy()
                    Random_effect_summary[key + "_Mean_Est"][i] = mean_estimate
                    Random_effect_summary[key +
                                          "_Mean_Variance"][i] = mean_variance_across_chains

        RE_summary_df = pd.DataFrame(Random_effect_summary)
        FE_summary_df = pd.DataFrame(Fixed_effect_summary)

        # adding Decoded Store Names
        RE_summary_df.reset_index(inplace=True)
        reverse_group_map_dict = {v: k for k, v in group_map_dict.items()}
        RE_summary_df[group_id_col] = RE_summary_df["index"].apply(
            lambda x: reverse_group_map_dict[x])

        # prediction from posteriors
        sample_shape = [num_iters]
        override_values = []
        train_yhat = []
        for group_id in train_df[group_id_col].unique():
            group_df = train_df[train_df["store_id"] == group_id]
            group_yhat = np.zeros(len(group_df))
            for fe in fixed_effect_cols:
                coef = Fixed_effect_summary['FE_' + fe + '_Mean_Est'][0]
                group_yhat = group_yhat + group_df[fe].values * coef
            for re in random_effect_cols:
                coef = Random_effect_summary['RE_' +
                                             re + '_Mean_Est'][group_id]
                group_yhat = group_yhat + group_df[re].values * coef
            group_pred_df = pd.DataFrame(group_yhat)
            group_pred_df[1] = group_id
            group_pred_df[2] = group_df[Y_col].values
            group_pred_df[3] = group_df["week_date"].values
            train_yhat.append(group_pred_df)

        train_yhat_df = pd.concat(train_yhat)
        train_yhat_df = pd.concat(train_yhat)
        train_yhat_df.columns = [Y_col+"_predicted",
                                 "group_id", Y_col, "week_date"]

        for feature in args_names_for_post_process[::-1]:
            if "RE_" in feature:
                override_values.append(tf.broadcast_to(np.mean(
                    np.mean(sample_dict[feature], axis=1), axis=0), sample_shape + [group_count]))
            elif ("master_" in feature) or ("FE_" in feature):
                override_values.append(tf.broadcast_to(
                    np.mean(sample_dict[feature]), sample_shape))
            elif "likelihood_sd" in feature:
                override_values.append(tf.broadcast_to(
                    np.mean(sample_dict[feature]), sample_shape))
        override_values.append(None)
        (*posterior_conditionals, predictive_treatment_effects) = varying_intercepts_and_slopes_model_(features_train, prior_params,
                                                                                                       fixed_effect_cols,
                                                                                                       random_effect_cols,
                                                                                                       joint_dist_list_names_reverse,
                                                                                                       likelihood_sd,
                                                                                                       group_count,
                                                                                                       group_id_col,
                                                                                                       affine).sample(value=tuple(override_values))
        y_hat_2 = np.mean(predictive_treatment_effects, axis=0)

        performance_summary = pd.DataFrame(
            [features_train[group_id_col], y_hat_2]).T
        performance_summary.columns = ["group_id", Y_col+"_post_pred_yhat"]
        performance_summary["week_date"] = list(week_dates)
        if len(additional_non_modeled_cols_for_output) != 0:
            for add_col in additional_non_modeled_cols_for_output:
                if (("_CE_MBP_COMP" in add_col) and (self.config["elasticity_model"]["constrain_cross_elasticities"] == "True")):
                    performance_summary[add_col] = list(
                        -1*additional_non_modeled_data_for_output[add_col])
                else:
                    performance_summary[add_col] = list(
                        additional_non_modeled_data_for_output[add_col])
        performance_summary[self.config['elasticity_model']
                            ['price_column']+"_original"] = list(original_price)
        performance_summary[self.config['elasticity_model']['price_column'] +
                            "_original"] = performance_summary[self.config['elasticity_model']['price_column']+"_original"] * -1
        if self.config['feature_engineering']['add_price_change_clip_flag'] == 'True':
            if self.config['elasticity_model']['price_column'] == "base_price":
                performance_summary[self.config['elasticity_model']
                                    ['price_column']+"_clipped"] = list(clipped_price)
                performance_summary[self.config['elasticity_model']['price_column'] +
                                    "_clipped"] = performance_summary[self.config['elasticity_model']['price_column']+"_clipped"] * -1
        performance_summary[group_id_col] = performance_summary["group_id"].apply(
            lambda x: reverse_group_map_dict[x])
        performance_summary["group_id"] = performance_summary["group_id"].astype(
            int)
        performance_summary = performance_summary.merge(
            train_yhat_df, on=["group_id", "week_date"], how="left")

        if self.config['feature_engineering']['log_model'] == 'True':
            performance_summary[Y_col] = np.exp(performance_summary[Y_col])
            performance_summary[Y_col+"_predicted"] = np.exp(
                performance_summary[Y_col+"_predicted"])
            performance_summary[Y_col+"_post_pred_yhat"] = np.exp(
                performance_summary[Y_col+"_post_pred_yhat"])
            performance_summary[self.config['elasticity_model']['price_column']+"_original"] = np.exp(
                performance_summary[self.config['elasticity_model']['price_column']+"_original"])
            if self.config['feature_engineering']['add_price_change_clip_flag'] == 'True':
                if self.config['elasticity_model']['price_column'] == "base_price":
                    performance_summary[self.config['elasticity_model']['price_column']+"_clipped"] = np.exp(
                        performance_summary[self.config['elasticity_model']['price_column']+"_clipped"])
            if len(additional_non_modeled_cols_for_output) != 0:
                for add_col in additional_non_modeled_cols_for_output:
                    if ("_CE_MBP_" in add_col):
                        performance_summary[add_col] = np.exp(
                            performance_summary[add_col])

        if self.config['feature_engineering']['scale_y_with_days_open'] == 'True':
            performance_summary[Y_col] = performance_summary[Y_col] * \
                performance_summary["days_open_this_week"]
            performance_summary[Y_col+"_predicted"] = performance_summary[Y_col +
                                                                          "_predicted"] * performance_summary["days_open_this_week"]
            performance_summary[Y_col+"_post_pred_yhat"] = performance_summary[Y_col +
                                                                               "_post_pred_yhat"] * performance_summary["days_open_this_week"]

        # adding metrics
        performance_summary["error (actual - predicted)"] = performance_summary[Y_col] - performance_summary[Y_col+"_predicted"]
        performance_summary["abs error"] = np.abs(performance_summary[Y_col] - performance_summary[Y_col+"_predicted"])
        performance_summary["precentage error"] = (performance_summary["error (actual - predicted)"]/performance_summary[Y_col])*100
        performance_summary["abs precentage error"] = np.abs(performance_summary["error (actual - predicted)"]/performance_summary[Y_col]) * 100

        group_obj = performance_summary.groupby(group_id_col)

        shapiro_results = group_obj["error (actual - predicted)"].apply(test_for_normal_dist)
        shapiro_results_df = shapiro_results.reset_index().rename(columns={"error (actual - predicted)": "store_post_predictive_err_dist"})

        mape_results = group_obj["abs precentage error"].mean()
        mape_results_df = mape_results.reset_index().rename(columns={"abs precentage error": "Store_MAPE"})
        mpe_results = group_obj["precentage error"].mean()
        mpe_results_df = mpe_results.reset_index().rename(columns={"precentage error": "Store_MPE"})
        mae_results = group_obj["abs error"].mean()
        mae_results_df = mae_results.reset_index().rename(columns={"abs error": "Store_MAE"})

        performance_summary = performance_summary.merge(shapiro_results_df, on=group_id_col, how="left")
        performance_summary = performance_summary.merge(mape_results_df, on=group_id_col, how="left")
        performance_summary = performance_summary.merge(mae_results_df, on=group_id_col, how="left")
        performance_summary = performance_summary.merge(mpe_results_df, on=group_id_col, how="left")

        performance_summary["item"] = item
        performance_summary["cluster"] = cluster
        performance_summary["rolling_date"] = rolling_date

        model_summary = performance_summary.merge(RE_summary_df, on=group_id_col, how="left")
        if "index" in list(FE_summary_df.columns):
            FE_summary_df.drop(columns=["index"])
        model_summary = pd.concat([model_summary, FE_summary_df], axis=1)

        for col in model_summary.columns:
            if ("_base_price_Mean_Est" in col):
                model_summary[col] = model_summary[col] * -1
            elif ((("_CE_MBP_COMP" in col) and ("_Mean_Est" in col)) and (self.config["elasticity_model"]["constrain_cross_elasticities"] == "True")):
                model_summary[col] = model_summary[col] * -1

        summaryFile = os.path.join(self.fldrs[0], save_tag + "_bayesian_predictions_estimates_metrics.csv")
        s3Obj.write(data=model_summary, filePath=summaryFile, type='csv', logger=self.logger, comboID=self.comboID)

        def plot_traces(var_name, samples, num_chains, path):
            try:
                if isinstance(samples, tf.Tensor):
                    samples = samples.numpy()  # convert to numpy array
                fig, axes = plt.subplots(1, 2, figsize=(
                    14, 2.5), sharex='col', sharey='col')
                for chain in range(num_chains):
                    axes[0].plot(samples[:, chain], alpha=0.7)
                    axes[0].title.set_text("'{}' trace".format(var_name))
                    sns.kdeplot(samples[:, chain], ax=axes[1], shade=False)
                    axes[1].title.set_text(
                        "'{}' distribution".format(var_name))
                    axes[0].set_xlabel('Iteration')
                    axes[1].set_xlabel(var_name)
                img_data = BytesIO()
                plt.savefig(img_data, format='png')
                plt.close()
                s3Obj.write(data=img_data, filePath=os.path.join(path, var_name + ".png"), type='img', logger=self.logger, comboID=self.comboID)
                del img_data
            except Exception as e:
                self.logger.error(
                    "%s - exception while plotting traces %s", self.comboID, feature)
                self.logger.error(e, exc_info=True)

        def save_traces(file_name, samples, path):
            try:
                if isinstance(samples, tf.Tensor):
                    samples = samples.numpy()
                group_trace = pd.DataFrame(samples)
                s3Obj.write(data=group_trace, filePath=os.path.join(path, file_name), type='csv', logger=self.logger, comboID=self.comboID)
            except Exception as e:
                self.logger.error("exception while plotting traces" + feature)
                self.logger.error(e, exc_info=True)

        if save_plots_and_trace:
            self.logger.info(
                "%s - generating and saving trace plots...", self.comboID)
            plot_path = self.fldrs[1]
            trace_path = self.fldrs[2]
            plot_features = plot_features + cross_elastic_cols
            for feature in plot_features:
                try:
                    if feature in random_effect_cols:
                        try:
                            temp_data = sample_dict["RE_"+feature].numpy()
                            if groups_to_trace_plot == "all":
                                number_of_groups = temp_data.shape[2]
                                plot_group_ids = list(range(number_of_groups))
                            else:
                                plot_group_ids = [group_map_dict[x] for x in groups_to_trace_plot if x in group_map_dict]
                        except Exception as e:
                            self.logger.error(
                                "failed fetching groups to plot:" + feature)
                            self.logger.error(e, exc_info=True)

                        try:
                            for i in plot_group_ids:
                                group_data = temp_data[:, :, i]
                                save_traces(save_tag + "_" + str(
                                    reverse_group_map_dict[i]) + "_" + feature + "_trace.csv", group_data, trace_path)
                                plot_traces(
                                    save_tag + "_" + str(reverse_group_map_dict[i]) + "_" + feature, group_data, chains, plot_path)
                        except Exception as e:
                            self.logger.error(
                                "failed saving/plotting trace for:" + feature)
                            self.logger.error(e, exc_info=True)

                        try:
                            if "master_mu_" + feature in sample_dict:
                                save_traces(save_tag + "_master_mu_" + feature + "_trace.csv",
                                            sample_dict["master_mu_" + feature], trace_path)
                                plot_traces(save_tag + "_master_mu_" + feature,
                                            sample_dict["master_mu_" + feature], chains, plot_path)
                            if "master_sd_" + feature in sample_dict:
                                save_traces(save_tag + "_master_sd_" + feature + "_trace.csv",
                                            sample_dict["master_sd_" + feature], trace_path)
                                plot_traces(save_tag + "_master_sd_" + feature,
                                            sample_dict["master_sd_" + feature], chains, plot_path)
                            if "master_alpha_" + feature in sample_dict:
                                save_traces(save_tag + "_master_alpha_" + feature + "_trace.csv",
                                            sample_dict["master_alpha_" + feature], trace_path)
                                plot_traces(save_tag + "_master_alpha_" + feature,
                                            sample_dict["master_alpha_" + feature], chains, plot_path)
                            if "master_beta_" + feature in sample_dict:
                                save_traces(save_tag + "_master_beta_" + feature + "_trace.csv",
                                            sample_dict["master_beta_" + feature], trace_path)
                                plot_traces(save_tag + "_master_beta_" + feature,
                                            sample_dict["master_beta_" + feature], chains, plot_path)
                        except Exception as e:
                            self.logger.error(
                                "failed saving/plotting trace for:" + feature)
                            self.logger.error(e, exc_info=True)

                    elif feature in fixed_effect_cols:
                        try:
                            save_traces(save_tag + "_FE_" + feature + "_trace.csv",
                                        sample_dict["FE_" + feature], trace_path)
                            plot_traces(
                                save_tag + "_FE_" + feature, sample_dict["FE_" + feature], chains, plot_path)
                        except Exception as e:
                            self.logger.error(
                                "failed saving/ploting trace for fixed effect:" + feature)
                            self.logger.error(e, exc_info=True)
                except Exception as e:
                    self.logger.error(e, exc_info=True)

        print(self.comboID, acceptance_probs)

        self.next(self.join_items)

    @batch(cpu=3, memory=6000)
    @step
    def join_items(self, inputs):
        # handle the errors from tfpRun
        # self.errored = [input.comboID for input in inputs if input.tfpError]
        self.next(self.join_item_groups)

    @batch(cpu=3, memory=6000)
    @step
    def join_item_groups(self, inputs):
        # handle the errors from tfpRun
        # self.errored = [input.comboID for input in inputs if input.tfpError]
        self.next(self.join_clusters)

    @batch(cpu=3, memory=6000)
    @step
    def join_clusters(self, inputs):
        self.next(self.end)

    @batch(cpu=3, memory=6000)
    @step
    def end(self):
        # aggregate the results
        pass


if __name__ == "__main__":
    RunBayesianSixtyNineOne()
