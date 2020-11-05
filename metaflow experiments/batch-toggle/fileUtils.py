"""
    Helper functions for file operations like
        checking for existence,
        creating directories,
        list directories,
        set permission

"""

import configparser
import json
import os
import pickle as pkl
from io import BytesIO, StringIO

import boto3
import pandas as pd
import dataUtils

# import s3fs


class S3:
    s3_cli = boto3.client("s3")
    s3_resource = boto3.resource("s3")
    config = dataUtils.read_s3_config(bucket="mcd-metaflow-batch", key="Inputs/config.ini")
    bucket = config['s3Config']['bucket']

    def init(self, by: str):
        self.create(os.path.join(self.config['s3Config']['output_path'], self.config['s3Config']
                                 ['output_folder'], self.config['s3Config']['experiment_name']+'/'))
        expPath = os.path.join(self.config['s3Config']['output_path'], self.config['s3Config']
                               ['output_folder'], self.config['s3Config']['experiment_name'])
        if by == 'bayesian':
            self.create(os.path.join(expPath, 'bayesianOutput', 'bayesian_model_train_summary/'))
            self.create(os.path.join(expPath, 'bayesianOutput', 'plots/'))
            self.create(os.path.join(expPath, 'bayesianOutput', 'traces/'))
            fldrs = [os.path.join(expPath, 'bayesianOutput', 'bayesian_model_train_summary'), os.path.join(
                expPath, 'bayesianOutput', 'plots'), os.path.join(expPath, 'bayesianOutput', 'traces')]
            return fldrs

        if by == 'lme':
            self.create(os.path.join(expPath, 'lmeOutput', 'metrics'))
            fldrs = [os.path.join(expPath, 'lmeOutput', 'metrics')]
            return fldrs

        if by == 'lstm':
            self.create(os.path.join(expPath, 'lstmPredictions', 'Predictions'))
            self.create(os.path.join(expPath, 'lstmPredictions', 'StoreLogs'))
            self.create(os.path.join(expPath, 'lstmPredictions', 'PriceElasticity'))
            fldrs = [os.path.join(expPath, 'lstmPredictions', 'Predictions'), os.path.join(
                expPath, 'lstmPredictions', 'StoreLogs'), os.path.join(expPath, 'lstmPredictions', 'PriceElasticity')]
            return fldrs
        return

    def create(self, path):
        if self.checkKey(path) != -1:
            self.s3_cli.put_object(Bucket=self.bucket, Key=path)
        return

    def read(self, filePath, logger, type='csv', comboID=""):
        if not self.checkKey(filePath, logger):
            logger.info(comboID + "- type "" - file missing for item_cluster or errored on locating file")
        try:
            response = self.s3_cli.get_object(Bucket=self.bucket, Key=filePath)
            if type == 'csv':
                df = pd.read_csv(response["Body"])
                return df
            if type == 'pkl':
                body = response['Body'].read()
                return pkl.loads(body)
        except Exception as e:
            logger.error("%s - failed while reading " + type, comboID)
            logger.error(e, exc_info=True)
        return None

    def checkKey(self, filePath, logger=None, comboID=""):
        try:
            response = self.s3_cli.list_objects_v2(Bucket=self.bucket, Prefix=filePath)
            if response["KeyCount"] > 0:
                if response['KeyCount'] == 1:
                    return True
                else:
                    return -1
            elif response["KeyCount"] == 0:
                return False
            elif logger is not None:
                logger.info("%s - bad response during file exist check", comboID)
                return
        except Exception as e:
            if logger is not None:
                logger.error("%s - Failed while checking file exists", comboID)
                logger.error(e, exc_info=True)
            return

    def write(self, data, filePath, logger, type='csv', comboID="", index=False, args=None):
        try:
            if type == 'csv':
                buffer = StringIO()
                data.to_csv(buffer, index=index)
                self.s3_cli.put_object(Bucket=self.bucket, Key=filePath, Body=buffer.getvalue())
            if type == 'img':
                data.seek(0)
                self.s3_cli.put_object(Bucket=self.bucket, Body=data, ContentType="image/png", Key=filePath)
        except Exception as e:
            logger.error(comboID, " failed while saving ", type, "file")
            logger.error(e, exc_info=True)

        return

    def listDir(self, path, logger, withPath=False):
        try:
            bucketObj = self.s3_resource.Bucket(self.bucket)
            if not withPath:
                return [file.key.split(os.path.sep)[-1] for file in list(bucketObj.objects.filter(Prefix=path))][1:]
            else:
                return [file.key for file in list(bucketObj.objects.filter(Prefix=path))][1:]
        except Exception as e:
            logger.error("failed getting list of files")
            logger.error(e, exc_info=True)


def read(filePath, type='csv', args={}):
    """ Reads a file from the given path

        Args:
            filePath:   path of the file to read

            type:   default - 'csv'. 'xl', 'pkl' are also supported

            args:   optional arguments for reading the file as dict
                    'indexCol'  - col to be read as index for csv and xl files. skipped if not available in the data
                    'sheetName' - name of the sheet in xl to be read

        Returns:
            pandas dataframe

        Raises:
            FileNotFoundError - if file not found

    """
    if not isexist(filePath):
        # raise FileNotFoundError
        return None

    if type == 'csv':
        if 'indexCol' in args.keys():
            try:
                return pd.read_csv(filePath, index_col=args['indexCol'])
            except:
                return pd.read_csv(filePath)
        else:
            return pd.read_csv(filePath)

    if type == 'pkl':
        return(pkl.load(open(filePath, 'rb')))

    if type == 'xl':
        if 'sheetName' in args.keys():
            if 'indexCol' in args.keys():
                try:
                    return pd.read_excel(filePath, sheet_name=args['sheetName'], index_col=args['indexCol'])
                except:
                    return pd.read_excel(filePath, sheet_name=args['sheetName'])
        else:
            return pd.read_excel(filePath)


def isexist(path):
    """ Check is  the path exists

        Args:
            path:  path to check

        Returns:
            Boolean True id the path exists. Boolean False otherwise
    """
    return os.path.exists(path)


def mkdir(path):
    """ Creates a directory/ a tree of directories

        Args: 
            path: path of the directory or the tree to create

        Returns:
            None if successful or Boolean False otherwise
    """
    if not isexist(path):
        os.makedirs(path)

    pathDirs = path.split(os.path.sep)
    for ind in range(1, len(pathDirs)+1):
        chmod(os.path.join(*pathDirs[:ind+1]))
    chmod(pathDirs[0])
    return


def chmod(path):
    """ Set permission to a path

        Args:
            path:  path to set permission
    """
    try:
        os.chmod(path, 0o0770)
    except:
        pass
    return
