import logging
import logging.config

import dependency_injector.containers as containers
import dependency_injector.providers as providers
import s3fs


def create_s3fs():
    return s3fs.S3FileSystem()


def create_logger(log_config):
    logging.config.dictConfig(log_config)
    return logging.getLogger(__name__)


def create_db_connection(db_config):
    from ts_forecast.core.utils.sql import DBConnection

    uri = db_config["uri"].format(**db_config)
    return DBConnection(uri)


class Core(containers.DeclarativeContainer):
    """IoC container of core component providers."""

    config = providers.Configuration("config")
    logger = providers.Singleton(create_logger, config.logger)


class Gateways(containers.DeclarativeContainer):
    """IoC container of gateway (API clients to remote services) providers."""

    tld_s3 = providers.Factory(create_s3fs)
    middleware_s3 = providers.Factory(create_s3fs)

    warehouse_db = providers.Singleton(
        create_db_connection, Core.config.credentials.data_warehouse_redshift
    )
    forecast_db = providers.Singleton(
        create_db_connection, Core.config.credentials.forecastdb_aurora
    )
