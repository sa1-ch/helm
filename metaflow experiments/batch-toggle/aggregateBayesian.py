import pandas as pd
import numpy as np
import pdb
import os

import fileUtils


def aggregate_results_bayesian(df_list, output_path, config):
    df_final = pd.DataFrame()
    aggregated_summary = pd.DataFrame()
    cluster_aggregated_summary = pd.DataFrame()
    for df in df_list:
        FE_columns = [x for x in df.columns if "FE_" in x]
        # TODO: add sales if present in config

        fe_agg_df = df[
            ['store_id', 'item', 'cluster', 'rolling_date', 'store_post_predictive_err_dist', "actual_sales", 'Store_MAPE', 'Store_MAE',
             'Store_MPE'] + FE_columns]
        fe_agg_df.drop_duplicates(subset=['store_id', 'item'], inplace=True)
        fe_agg_df[FE_columns] = fe_agg_df[FE_columns].fillna(method='ffill')
        fe_agg_df = fe_agg_df.groupby('cluster').mean().reset_index()
        fe_agg_df.drop(columns=['store_id'], inplace=True)
        cluster_aggregated_summary = cluster_aggregated_summary.append(fe_agg_df)

        RE_columns = [x for x in df.columns if "RE_" in x]
        agg_df = df[
            ['store_id', 'item', 'cluster', 'rolling_date', "actual_sales", 'store_post_predictive_err_dist', 'Store_MAPE', 'Store_MAE',
             'Store_MPE'] + RE_columns]
        agg_df = agg_df.groupby(["store_id", "rolling_date"]).mean().reset_index()
        aggregated_summary = aggregated_summary.append(agg_df)

    for df in df_list:
        ce_columns = [x for x in df.columns if "_MBP_" in x and "_Mean_Est" in x and "master_" not in x]
        ce_items_list = []
        base_price_column = [x for x in df.columns if config['elasticity_model'][
            'price_column'] in x and "_Mean_Est" in x and "master_" not in x]
        for x in ce_columns:
            ce_items_list.append(x.split('_')[1])
        col_list = ['rolling_date', 'store_id', 'item'] + base_price_column + ce_columns
        df = df[col_list]
        df_g = df.groupby(['store_id']).mean().reset_index()
        df_g = df_g.fillna(method='ffill')
        df_g = df_g.fillna(method='bfill')
        item = str(df_g['item'].unique()[0])
        elasticity_cols = [item] + ce_items_list
        df_g.columns = ['store_id', 'item'] + elasticity_cols
        df_g = pd.melt(df_g, id_vars=['store_id', 'item'], value_vars=elasticity_cols,
                       var_name='peItem', value_name='elasticity')
        df_g['Rolling_Flag'] = df['rolling_date'][0]
        df_final = df_final.append(df_g)

    df_final = df_final[['Rolling_Flag', 'store_id', 'item', 'peItem', 'elasticity']]
    df_final.columns = ['Rolling_Flag', 'StoreID', 'SLD_MENU_ITM_ID', 'peItem', 'elasticity']
    df_final['Rolling_Flag'] = pd.to_datetime(df_final['Rolling_Flag'])
    df_final['Rolling_Flag'] = ["rolling_train_end_" + x.strftime('%Y-%m-%d') for x in df_final['Rolling_Flag']]

    if not os.path.exists(os.path.join(output_path, 'LSTM_Input')):
        os.makedirs(os.path.join(output_path, 'LSTM_Input'))
    output_file = os.path.join(output_path, 'LSTM_Input', 'Elasticity_model_output.csv')
    df_final.to_csv(output_file)

    agg_summary_with_category = aggregated_summary.copy()

    if not os.path.exists(os.path.join(output_path, 'elasticity_model_output')):
        os.makedirs(os.path.join(output_path, 'elasticity_model_output'))
    agg_summary_file = os.path.join(output_path, 'elasticity_model_output', 'Store_Item_Metrics.csv')
    agg_summary_with_category.to_csv(agg_summary_file, index=False)
    agg_summary_file = os.path.join(output_path, 'elasticity_model_output', 'Cluster_Item_Metrics.csv')
    cluster_aggregated_summary.to_csv(agg_summary_file, index=False)


if __name__ == "__main__":

    import glob
    files = glob.glob(os.path.join('../../bayesianOutput/outputs', "*.csv"))
    dfs = list(map(pd.read_csv, files))
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    aggregate_results_bayesian(df_list=dfs, output_path='../../bayesianOutput', config=config)
    pdb.set_trace()
