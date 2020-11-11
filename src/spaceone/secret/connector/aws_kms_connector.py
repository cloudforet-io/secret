# -*- coding: utf-8 -*-
import logging

import boto3
from spaceone.core.connector import BaseConnector
from spaceone.core.error import *

__all__ = ['AWSKMSConnector']

import test.factories.secret

_LOGGER = logging.getLogger(__name__)


class AWSKMSConnector(BaseConnector):

    def __init__(self, transaction, config):
        super().__init__(transaction, config)
        aws_access_key_id = self.config.get('aws_access_key_id')
        aws_secret_access_key = self.config.get('aws_secret_access_key')
        region_name = self.config.get('region_name')
        self.kms_key_id = self.config.get('kms_key_id')

        if not all([region_name, self.kms_key_id]):
            raise ERROR_CONNECTOR_CONFIGURATION(backend='AWSKMSConnector')

        if aws_access_key_id and aws_secret_access_key:
            self.client = boto3.client('kms', aws_access_key_id=aws_access_key_id,
                                       aws_secret_access_key=aws_secret_access_key, region_name=region_name)
        else:
            self.client = boto3.client('kms', region_name=region_name)
        self.kms_key_id = self.config.get('kms_key_id')

    def generate_data_key(self,encrypt_context:dict=None):
        data_key = test.factories.secret.generate_data_key(
            KeyId=self.kms_key_id,
            KeySpec='AES_128',
            EncryptionContext=encrypt_context,
        )
        return data_key['Plaintext'], data_key['CiphertextBlob']

    def decrypt_data_key(self, encrypt_data_key,encrypt_context:dict=None):
        response = self.client.decrypt(
            CiphertextBlob=encrypt_data_key,
            KeyId=self.kms_key_id,
            EncryptionContext=encrypt_context
        )
        return response['Plaintext']
