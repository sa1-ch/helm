import configparser
import logging
import os
import pickle
import sys
from logging import FileHandler

# from utils import check_create_folder_s3

FORMATTER = logging.Formatter(
    "%(asctime)s — %(name)s — %(levelname)s — %(message)s")
ROOT_PATH = os.path.dirname(__file__)

# config = configparser.ConfigParser()
# config.read('config.ini')


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler(file: str):
    config = configparser.ConfigParser()
    config.read('config.ini')
    with open("../run_mode_config.dict", "rb") as handle:
        change_dict = pickle.load(handle)
    log_path: str = "exp_logs/" + \
        config["common"]['output_path'].split("/")[-2] + "/" + "logs/"
    # bucket_name = config["common"]['bucket_name']
    # log_path = "logs/"
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    file_handler = FileHandler(log_path + file)
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(logger_name: str, log_file: str, ):
    logger = logging.getLogger(logger_name)
    if not getattr(logger, 'handler_set', None):
        logger.setLevel(logging.DEBUG)
        logger.addHandler(get_console_handler())
        # logger.addHandler(get_file_handler(log_file))
        logger.propagate = False
        logger.handler_set = True
    return logger
