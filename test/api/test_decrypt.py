import os
import os
import unittest

import boto3
import botocore
from google.protobuf.json_format import MessageToDict
from moto import mock_kms, mock_secretsmanager
from spaceone.api.secret.v1.secret_pb2 import GetSecretRequest
from spaceone.core import config, utils
from spaceone.core.unittest.runner import RichTestRunner

from src.spaceone.secret.lib.encrypt import aws_kms_decrypt
from test.api.test_encrypt_secret_api import SpaceoneGrpcTestCase
from test.factories.secret import EncryptSecretFactory

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_PATH = os.path.join(ROOT_DIR, 'src')


@mock_kms
@mock_secretsmanager
class TestAwsKMSDecrypt(SpaceoneGrpcTestCase):
    config = {
        "SET_LOGGING": False,
        "ENCRYPT": True,
        "CONNECTORS": {
            'AWSSecretManagerConnector': {
                "region_name": "ap-northeast-2",

            },
            'AWSKMSConnector': {
                "region_name": "ap-northeast-2",
                "kms_key_id": ""
            },
        }
    }
    src_path = SRC_PATH
    package = 'spaceone.secret'

    def get_kms_client(self):
        region_name = config.get_global('CONNECTORS', {}).get('AWSKMSConnector', {}).get("region_name")
        return boto3.client('kms', region_name=region_name)

    def setup_kms_key(self):
        kms_cli = self.get_kms_client()
        self.kms_key_id = kms_cli.create_key()['KeyMetadata']['KeyId']
        config.set_global(CONNECTORS={"AWSKMSConnector": {"kms_key_id": self.kms_key_id}})

    def setUp(self):
        super(TestAwsKMSDecrypt, self).setUp()
        self.setup_kms_key()

    def test_get_secret_data(self):
        secret_data = {"secret": utils.random_string()}
        secret_1 = EncryptSecretFactory(encrypted=True, secret_data=secret_data)

        request = GetSecretRequest(secret_id=secret_1.secret_id, domain_id=secret_1.domain_id)
        result, metadata, code, details = self.request_unary_unary('spaceone.api.secret.v1.Secret.get_data', request)
        self.assertGrpcStatusCodeOk(code)
        result = MessageToDict(result, preserving_proto_field_name=True)
        options = result['encrypt_options']
        # check decrypt
        region_name = config.get_global('CONNECTORS', {}).get('AWSKMSConnector', {}).get("region_name")

        decrypt_secret_data = aws_kms_decrypt(options['encrypt_data_key'], options['nonce'], result['encrypted_data'],
                                              options['encrypt_context'], region_name=region_name)
        self.assertEqual(secret_data, decrypt_secret_data)

    def test_get_secret_data_custom_client(self):
        secret_data = {"secret": utils.random_string()}
        secret_1 = EncryptSecretFactory(encrypted=True, secret_data=secret_data)

        request = GetSecretRequest(secret_id=secret_1.secret_id, domain_id=secret_1.domain_id)
        result, metadata, code, details = self.request_unary_unary('spaceone.api.secret.v1.Secret.get_data', request)
        self.assertGrpcStatusCodeOk(code)
        result = MessageToDict(result, preserving_proto_field_name=True)
        options = result['encrypt_options']
        # check decrypt
        kms_client = self.get_kms_client()
        decrypt_secret_data = aws_kms_decrypt(options['encrypt_data_key'], options['nonce'], result['encrypted_data'],
                                              options['encrypt_context'], kms_client=kms_client)

        self.assertEqual(secret_data, decrypt_secret_data)
        with self.assertRaises(botocore.exceptions.ClientError):
            aws_kms_decrypt(options['encrypt_data_key'], options['nonce'], result['encrypted_data'],
                            options['encrypt_context'],
                            kms_client=boto3.client('kms', region_name='me-south-1'))


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
