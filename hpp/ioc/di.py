import logging
import logging.config

import s3fs

import dependency_injector.containers as containers
import dependency_injector.providers as providers


def create_logger():
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s:%(message)s"
    )
    return logging.getLogger(__name__)


class Core(containers.DeclarativeContainer):
    """
    IoC container of core component providers.

    """
    config = providers.Configuration("config")

    logger = providers.Singleton(create_logger)


class Gateways(containers.DeclarativeContainer):
    """
    IoC container of gateway (API clients to remote services) providers.

    """

    s3_fs = providers.Singleton(
        s3fs.S3FileSystem,
        key=Core.config.credentials.access_key,
        secret=Core.config.credentials.secret,
    )
