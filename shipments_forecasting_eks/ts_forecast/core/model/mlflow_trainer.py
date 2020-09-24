# Standard library imports
import logging
import os
import tempfile
import time
import uuid
from typing import List, Optional

import mlflow
import mxnet as mx
import numpy as np
from gluonts.core.exception import GluonTSUserError
from gluonts.dataset.loader import TrainDataLoader, ValidationDataLoader
from gluonts.gluonts_tqdm import tqdm
from gluonts.support.util import HybridContext
from gluonts.trainer._base import (
    STATE_ARTIFACT_FILE_NAME,
    BestEpochInfo,
    Trainer,
    loss_value,
)
from mxnet import autograd
from mxnet.gluon import nn

# Relative imports
# from gluonts.trainer import learning_rate_scheduler as lrs

LOGGER = logging.getLogger(__name__)

metrics_dict = {}

# make the IDE happy: mx.py does not explicitly import autograd
mx.autograd = autograd


class MetricAttentiveScheduler(mx.lr_scheduler.LRScheduler):
    r"""
    This scheduler decreases the learning rate based on the value of some
    validation metric to be optimized (maximized or minimized). The value
    of such metric is provided by calling the `step` method on the scheduler.
    A `patience` parameter must be provided, and the scheduler will reduce
    the learning rate if no improvement in the metric is done before
    `patience` observations of the metric.

    Examples:

        `patience = 0`: learning rate will decrease at every call to
        `step`, regardless of the metric value

        `patience = 1`: learning rate is reduced as soon `step` is called
        with a metric value which does not improve over the best encountered

        `patience = 10`: learning rate is reduced if no improvement in the
        metric is recorded in 10 successive calls to `step`

    Parameters
    ----------
    objective
        String, can either be `"min"` or `"max"`
    patience
        The patience to observe before reducing the learning rate, nonnegative integer.
    base_lr
        Initial learning rate to be used.
    decay_factor
        Factor (between 0 and 1) by which to decrease the learning rate.
    min_lr
        Lower bound for the learning rate, learning rate will never go below `min_lr`
    """

    def __init__(
        self,
        objective: str,
        patience: int,
        base_lr: float = 0.01,
        decay_factor: float = 0.5,
        min_lr: float = 0.0,
    ) -> None:

        assert base_lr > 0, f"base_lr should be positive, got {base_lr}"

        assert (
            base_lr > min_lr
        ), f"base_lr should greater than min_lr, {base_lr} <= {min_lr}"

        assert (
            0 < decay_factor < 1
        ), f"decay_factor factor should be between 0 and 1, got {decay_factor}"

        assert patience >= 0, f"patience should be nonnegative, got {patience}"

        assert objective in [
            "min",
            "max",
        ], f"objective should be 'min' or 'max', got {objective}"

        super(MetricAttentiveScheduler, self).__init__(base_lr=base_lr)

        self.decay_factor = decay_factor
        self.patience = patience
        self.objective = objective
        self.min_lr = min_lr
        self.best_metric = np.Inf if objective == "min" else -np.Inf
        self.prev_change = 0
        self.epoch_no = 0
        self.curr_lr = None

    def __call__(self, num_update: int) -> float:
        if self.curr_lr is None:
            self.curr_lr = self.base_lr
        assert self.curr_lr is not None

        return self.curr_lr

    def step(self, metric_value: float) -> bool:
        """
        Inform the scheduler of the new value of the metric that is being
        optimized. This method should be invoked at regular intervals (e.g.
        at the end of every epoch, after computing a validation score).

        Parameters
        ----------
        metric_value
            Value of the metric that is being optimized.

        Returns
        -------
        bool value indicating, whether to continue training
        """
        if self.curr_lr is None:
            self.curr_lr = self.base_lr
        assert self.curr_lr is not None

        metric_improved = (
            self.objective == "min" and metric_value < self.best_metric
        ) or (self.objective == "max" and metric_value > self.best_metric)

        if metric_improved:
            self.best_metric = metric_value
            self.prev_change = self.epoch_no

        if self.epoch_no - self.prev_change >= self.patience or not np.isfinite(
            metric_value
        ):
            if self.curr_lr == self.min_lr:
                return False
            self.curr_lr = max(self.min_lr, self.decay_factor * self.curr_lr)
            self.prev_change = self.epoch_no

        self.epoch_no += 1
        return True


class MlflowTrainer(Trainer):
    """
        Overriden, to include mlflow-metric logging for
            - Time-Elapsed,
            - Validation-Loss
        for each epoch
    """

    def __call__(
        self,
        net: nn.HybridBlock,
        input_names: List[str],
        train_iter: TrainDataLoader,
        validation_iter: Optional[ValidationDataLoader] = None,
    ) -> None:  # TODO: we may want to return some training information here
        is_validation_available = validation_iter is not None
        self.halt = False

        with tempfile.TemporaryDirectory(
            prefix="gluonts-trainer-temp-"
        ) as gluonts_temp:

            def base_path() -> str:
                return os.path.join(
                    gluonts_temp,
                    "{}_{}".format(STATE_ARTIFACT_FILE_NAME, uuid.uuid4()),
                )

            LOGGER.info("Start model training")

            net.initialize(ctx=self.ctx, init=self.init)

            with HybridContext(
                net=net, hybridize=self.hybridize, static_alloc=True, static_shape=True,
            ):
                batch_size = train_iter.batch_size

                best_epoch_info = BestEpochInfo(
                    params_path="%s-%s.params" % (base_path(), "init"),
                    epoch_no=-1,
                    metric_value=np.Inf,
                )

                lr_scheduler = MetricAttentiveScheduler(
                    objective="min",
                    patience=self.patience,
                    decay_factor=self.learning_rate_decay_factor,
                    min_lr=self.minimum_learning_rate,
                )

                optimizer = mx.optimizer.Adam(
                    learning_rate=self.learning_rate,
                    lr_scheduler=lr_scheduler,
                    wd=self.weight_decay,
                    clip_gradient=self.clip_gradient,
                )

                trainer = mx.gluon.Trainer(
                    net.collect_params(),
                    optimizer=optimizer,
                    kvstore="device",  # FIXME: initialize properly
                )

                def loop(
                    epoch_no, batch_iter, is_training: bool = True
                ) -> mx.metric.Loss:
                    tic = time.time()

                    epoch_loss = mx.metric.Loss()

                    with tqdm(batch_iter) as it:
                        for batch_no, data_entry in enumerate(it, start=1):
                            if self.halt:
                                break

                            inputs = [data_entry[k] for k in input_names]

                            with mx.autograd.record():
                                output = net(*inputs)

                                # network can returns several outputs,
                                # the first being always the loss
                                # when having multiple outputs,
                                # the forward returns a list in the case of hybrid and a
                                # tuple otherwise
                                # we may wrap network outputs in the future
                                # to avoid this type check
                                if isinstance(output, (list, tuple)):
                                    loss = output[0]
                                else:
                                    loss = output

                            if is_training:
                                loss.backward()
                                trainer.step(batch_size)

                            epoch_loss.update(None, preds=loss)
                            lv = loss_value(epoch_loss)

                            if not np.isfinite(lv):
                                LOGGER.warning("Epoch[%d] gave nan loss", epoch_no)
                                return epoch_loss

                            it.set_postfix(
                                ordered_dict={
                                    "epoch": f"{epoch_no + 1}/{self.epochs}",
                                    ("" if is_training else "validation_")
                                    + "avg_epoch_loss": lv,
                                },
                                refresh=False,
                            )
                            # print out parameters of the network at the first pass
                            if batch_no == 1 and epoch_no == 0:
                                net_name = type(net).__name__
                                num_model_param = self.count_model_params(net)
                                msg = (
                                    f"No of parameters in {net_name}: {num_model_param}"
                                )
                                LOGGER.info(msg)
                    # mark epoch end time and log time cost of current epoch
                    toc = time.time()
                    metrics_dict[f"Epoch_{epoch_no+1}_Elapsed_Time"] = toc - tic
                    LOGGER.info(
                        "Epoch[%d] Elapsed time %.3f seconds", epoch_no, (toc - tic),
                    )

                    metrics_dict[f"Epoch_{epoch_no+1}_Loss"] = lv
                    LOGGER.info(
                        "Epoch[%d] Evaluation metric '%s'=%f",
                        epoch_no,
                        ("" if is_training else "validation_") + "epoch_loss",
                        lv,
                    )
                    return epoch_loss

                for epoch_no in range(self.epochs):
                    if self.halt:
                        LOGGER.info(f"Epoch[{epoch_no}] Interrupting training")
                        break

                    curr_lr = trainer.learning_rate
                    LOGGER.info(f"Epoch[{epoch_no}] Learning rate is {curr_lr}")

                    epoch_loss = loop(epoch_no, train_iter)
                    if is_validation_available:
                        epoch_loss = loop(epoch_no, validation_iter, is_training=False)

                    should_continue = lr_scheduler.step(loss_value(epoch_loss))
                    if not should_continue:
                        LOGGER.info("Stopping training")
                        break

                    if loss_value(epoch_loss) < best_epoch_info.metric_value:
                        best_epoch_info = BestEpochInfo(
                            params_path="%s-%04d.params" % (base_path(), epoch_no),
                            epoch_no=epoch_no,
                            metric_value=loss_value(epoch_loss),
                        )
                        net.save_parameters(
                            best_epoch_info.params_path
                        )  # TODO: handle possible exception

                    if not trainer.learning_rate == curr_lr:
                        if best_epoch_info.epoch_no == -1:
                            raise GluonTSUserError(
                                """
                            Got NaN in first epoch. Try reducing initial learning rate.
                            """
                            )

                        LOGGER.info(
                            f"Loading parameters from best epoch "
                            f"({best_epoch_info.epoch_no})"
                        )
                        net.load_parameters(best_epoch_info.params_path, self.ctx)

                LOGGER.info(
                    f"Loading parameters from best epoch "
                    f"({best_epoch_info.epoch_no})"
                )
                net.load_parameters(best_epoch_info.params_path, self.ctx)

                LOGGER.info(
                    f"Final loss: {best_epoch_info.metric_value} "
                    f"(occurred at epoch {best_epoch_info.epoch_no})"
                )

                # save net parameters
                net.save_parameters(best_epoch_info.params_path)

                mlflow.log_metrics(metrics_dict)
                LOGGER.info("End model training")
