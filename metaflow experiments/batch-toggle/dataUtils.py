"""
    Common data transformations like Scaling, String Split, dict to df or vice versa 
"""


import glob
import os
import configparser
import boto3


def strSplit(string, sep=', '):
    if len(string.split(sep)) == 1 and string.split(sep)[0] == '':
        return None
    return string.split(sep)


def read_s3_config(bucket, key):
    s3_boto = boto3.client('s3')
    obj = s3_boto.get_object(Bucket=bucket, Key=key)

    config = configparser.ConfigParser()
    config.read_string(obj['Body'].read().decode())
    print(config['s3Config']['output_path'], "******************************************")

    return config
