from typing import List, Optional

from gluonts.core.component import validated
from gluonts.distribution.lds import ParameterBounds
from gluonts.model.deepstate import DeepStateEstimator
from gluonts.model.deepstate._network import DeepStateTrainingNetwork
from gluonts.model.deepstate.issm import ISSM
from gluonts.support.util import copy_parameters
from gluonts.time_feature import TimeFeature
from gluonts.trainer import Trainer


class IncrementalDeepStateEstimator(DeepStateEstimator):
    """ Estimator that uses a pre-trained network to initialize network parameters.
    """

    @validated()
    def __init__(
        self,
        network: DeepStateTrainingNetwork,
        freq: str,
        prediction_length: int,
        cardinality: List[int],
        add_trend: bool = False,
        past_length: Optional[int] = None,
        num_periods_to_train: int = 4,
        trainer: Trainer = Trainer(
            epochs=100, num_batches_per_epoch=50, hybridize=False
        ),
        num_layers: int = 2,
        num_cells: int = 40,
        cell_type: str = "lstm",
        num_parallel_samples: int = 100,
        dropout_rate: float = 0.1,
        use_feat_dynamic_real: bool = False,
        use_feat_static_cat: bool = True,
        embedding_dimension: Optional[List[int]] = None,
        issm: Optional[ISSM] = None,
        scaling: bool = True,
        time_features: Optional[List[TimeFeature]] = None,
        noise_std_bounds: ParameterBounds = ParameterBounds(1e-6, 1.0),
        prior_cov_bounds: ParameterBounds = ParameterBounds(1e-6, 1.0),
        innovation_bounds: ParameterBounds = ParameterBounds(1e-6, 0.01),
    ):
        self.base_network = network
        # print(f'Calling super init with {kwargs}')
        super(IncrementalDeepStateEstimator, self).__init__(
            freq=freq,
            prediction_length=prediction_length,
            cardinality=cardinality,
            add_trend=add_trend,
            past_length=past_length,
            num_periods_to_train=num_periods_to_train,
            trainer=trainer,
            num_layers=num_layers,
            num_cells=num_cells,
            cell_type=cell_type,
            num_parallel_samples=num_parallel_samples,
            dropout_rate=dropout_rate,
            use_feat_dynamic_real=use_feat_dynamic_real,
            use_feat_static_cat=use_feat_static_cat,
            embedding_dimension=embedding_dimension,
            issm=issm,
            scaling=scaling,
            time_features=time_features,
            noise_std_bounds=noise_std_bounds,
            prior_cov_bounds=prior_cov_bounds,
            innovation_bounds=innovation_bounds,
        )

    def create_training_network(self):
        params = self.base_network.collect_params()
        net = DeepStateTrainingNetwork(
            num_layers=self.num_layers,
            num_cells=self.num_cells,
            cell_type=self.cell_type,
            past_length=self.past_length,
            prediction_length=self.prediction_length,
            issm=self.issm,
            dropout_rate=self.dropout_rate,
            # trainer=self.trainer,
            cardinality=self.cardinality,
            embedding_dimension=self.embedding_dimension,
            scaling=self.scaling,
            noise_std_bounds=self.noise_std_bounds,
            prior_cov_bounds=self.prior_cov_bounds,
            innovation_bounds=self.innovation_bounds,
            params=params,
        )
        copy_parameters(self.base_network, net)
        return net
