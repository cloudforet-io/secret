# -*- coding: utf-8 -*-

import logging
import json
import boto3

from spaceone.core.error import *
from spaceone.core.connector import BaseConnector

__all__ = ['AWSSecretManagerConnector']
_LOGGER = logging.getLogger(__name__)


class AWSSecretManagerConnector(BaseConnector):

    def __init__(self, transaction, config):
        super().__init__(transaction, config)

        aws_access_key_id = self.config.get('aws_access_key_id')
        aws_secret_access_key = self.config.get('aws_secret_access_key')
        region_name = self.config.get('region_name')

        if region_name is None:
            raise ERROR_CONNECTOR_CONFIGURATION(backend='AWSSecretManagerConnector')

        if aws_access_key_id and aws_secret_access_key:
            self.client = boto3.client('secretsmanager', aws_access_key_id=aws_access_key_id,
                                       aws_secret_access_key=aws_secret_access_key, region_name=region_name)
        else:
            self.client = boto3.client('secretsmanager', region_name=region_name)

    @staticmethod
    def _convert_tags(tags):
        return list(map(lambda k: {'Key': k, 'Value': tags[k]}, tags))

    @staticmethod
    def _response(response):
        if 'ResponseMetadata' in response and 'HTTPStatusCode' in response['ResponseMetadata'] and \
                response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True

        return False

    @staticmethod
    def _response_value(response):
        data_string = response.get('SecretString', False)

        if data_string:
            return json.loads(data_string)

        return data_string

    def create_secret(self, secret_id, data):
        secret_params = {
            'Name': secret_id,
            'SecretString': json.dumps(data),
        }

        return self._response(self.client.create_secret(**secret_params))

    def delete_secret(self, secret_id):
        response = self.client.delete_secret(
            SecretId=secret_id,
            ForceDeleteWithoutRecovery=True
        )

        return self._response(response)

    def get_secret(self, secret_id):
        return self._response_value(self.client.get_secret_value(SecretId=secret_id))
