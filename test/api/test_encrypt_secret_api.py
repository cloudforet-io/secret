import base64
import collections
import json
import os
import unittest
import uuid
from typing import Union

import boto3
import grpc
import grpc_testing
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from google.protobuf import symbol_database
from google.protobuf.json_format import MessageToDict, ParseDict
from google.protobuf.struct_pb2 import Struct
from moto import mock_kms, mock_secretsmanager
from spaceone.api.secret.v1.secret_pb2 import CreateSecretRequest, GetSecretRequest
from spaceone.core import config, utils
from spaceone.core.unittest.runner import RichTestRunner

from src.spaceone.secret.model.secret_model import Secret, _LOGGER
from test.api.test_encrypt_secret import SpaceoneTestCase
from test.factories.secret import EncryptSecretFactory, SecretFactory

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_PATH = os.path.join(ROOT_DIR, 'src')


def _get_proto_conf(package):
    proto_module = __import__(f'{package}.conf.proto_conf', fromlist=['proto_conf'])
    return getattr(proto_module, 'PROTO', {})


def _get_servicer():
    proto_conf = _get_proto_conf(config.get_package())

    serviceres = {}
    for module_path, servicer_names in proto_conf.items():
        for servicer_name in servicer_names:
            api_module = _import_module(module_path, servicer_name)
            if api_module:
                if hasattr(api_module, servicer_name):
                    servicer = getattr(api_module, servicer_name)()
                    serviceres[servicer.pb2.DESCRIPTOR.services_by_name[servicer_name]] = servicer

    return serviceres


def _import_module(module_path, servicer_name):
    module = None
    try:
        module = __import__(module_path, fromlist=[servicer_name])
    except Exception as e:
        _LOGGER.warning(f'[_import_module] Cannot import grpc servicer module. (reason = {e})')

    return module


class SpaceoneGrpcTestCase(SpaceoneTestCase):
    _test_server = None

    @classmethod
    def setUpClass(cls) -> None:
        super(SpaceoneGrpcTestCase, cls).setUpClass()

    @property
    def test_server(self):
        if not self._test_server:
            servicers = _get_servicer()

            self._test_server = grpc_testing.server_from_dictionary(
                servicers, grpc_testing.strict_real_time()
            )
        return self._test_server

    def get_method_descriptor(self, full_name):
        return symbol_database.Default().pool.FindMethodByName(full_name)

    def request_unary_unary(self, full_name, request, metadata=None, timeout=None, **kwargs):
        method = self.test_server.invoke_unary_unary(
            method_descriptor=self.get_method_descriptor(full_name),
            invocation_metadata=metadata or {},
            request=request, timeout=timeout, **kwargs)
        return method.termination()

    def assertGrpcStatusCodeOk(self, code):
        self.assertEqual(code, grpc.StatusCode.OK)


@mock_kms
@mock_secretsmanager
class TestDefaultSecretAPI(SpaceoneGrpcTestCase):
    config = {
        "ENCRYPT": False,
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

    def get_encrypt_context_by_vo(self, secret_vo: Union[Secret, dict]) -> str:
        context = collections.OrderedDict()
        context['domain_id'] = secret_vo['domain_id'] if isinstance(secret_vo, dict) else secret_vo.domain_id
        context['secret_id'] = secret_vo['secret_id'] if isinstance(secret_vo, dict) else secret_vo.secret_id
        return base64.b64encode(json.dumps(context).encode()).decode()


    def test_get_secret(self):
        SecretFactory.create_batch(10)
        secret_1 = SecretFactory()

        request = GetSecretRequest(secret_id=secret_1.secret_id, domain_id=secret_1.domain_id)
        response, metadata, code, details = self.request_unary_unary('spaceone.api.secret.v1.Secret.get', request)
        self.assertGrpcStatusCodeOk(code)
        self.assertEqual(secret_1.secret_id, response.secret_id)
        self.assertEqual(secret_1.domain_id, response.domain_id)

    def test_get_secret_data(self):
        SecretFactory.create_batch(10)
        secret_data = {"secret": f"{os.urandom(10)}"}
        secret_1 = SecretFactory(secret_data=secret_data)

        request = GetSecretRequest(secret_id=secret_1.secret_id, domain_id=secret_1.domain_id)
        response, metadata, code, details = self.request_unary_unary('spaceone.api.secret.v1.Secret.get_data', request)
        self.assertGrpcStatusCodeOk(code)
        self.assertFalse(response.encrypted)
        self.assertEqual(secret_data, MessageToDict(response)['data'])

    def _check_secretmanager_exists(self, secret_id):
        region = config.get_global('CONNECTORS', {}).get('AWSSecretManagerConnector', {}).get("region_name")
        client = boto3.client('secretsmanager', region_name=region)
        try:
            client.describe_secret(
                SecretId=secret_id
            )
            return True
        except Exception as e:
            return False

    def test_create_secret(self):
        SecretFactory.create_batch(10)
        secret_data = {
            "sample": "abcd"
        }
        secret_1 = {
            'name': 'sample',
            'data': ParseDict(secret_data, Struct()),
            'secret_type': 'CREDENTIALS',
            'domain_id': 'domain_1234',
        }

        request = CreateSecretRequest(**secret_1, )
        response, metadata, code, details = self.request_unary_unary('spaceone.api.secret.v1.Secret.create', request)
        self.assertGrpcStatusCodeOk(code)
        response = MessageToDict(response, preserving_proto_field_name=True)

        self.assertEqual(secret_1.get('domain_id'), response['domain_id'])
        self.assertEqual(secret_1.get('secret_type'), response['secret_type'])
        self.assertTrue(self._check_secretmanager_exists(response['secret_id']))


@mock_kms
@mock_secretsmanager
class TestEncryptSecretAPI(SpaceoneGrpcTestCase):
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

    def get_encrypt_context_by_vo(self, secret_vo: Union[Secret, dict]) -> str:
        context = collections.OrderedDict()
        context['domain_id'] = secret_vo['domain_id'] if isinstance(secret_vo, dict) else secret_vo.domain_id
        context['secret_id'] = secret_vo['secret_id'] if isinstance(secret_vo, dict) else secret_vo.secret_id
        return base64.b64encode(json.dumps(context).encode()).decode()

    def get_kms_client(self):
        region_name = config.get_global('CONNECTORS', {}).get('AWSKMSConnector', {}).get("region_name")
        return boto3.client('kms', region_name=region_name)

    def setup_kms_key(self):
        kms_cli = self.get_kms_client()
        self.kms_key_id = kms_cli.create_key()['KeyMetadata']['KeyId']
        config.set_global(CONNECTORS={"AWSKMSConnector": {"kms_key_id": self.kms_key_id}})

    def setUp(self):
        super(TestEncryptSecretAPI, self).setUp()
        self.setup_kms_key()

    def test_get_secret(self):
        tags = {"test": "tags"}
        EncryptSecretFactory.create_batch(10)
        secret_1 = EncryptSecretFactory(tags=tags)

        request = GetSecretRequest(secret_id=secret_1.secret_id, domain_id=secret_1.domain_id)
        response, metadata, code, details = self.request_unary_unary('spaceone.api.secret.v1.Secret.get', request)
        self.assertGrpcStatusCodeOk(code)
        self.assertEqual(secret_1.secret_id, response.secret_id)
        self.assertEqual(secret_1.domain_id, response.domain_id)

    def _check_secretmanager_exists(self, secret_id):
        region = config.get_global('CONNECTORS', {}).get('AWSSecretManagerConnector', {}).get("region_name")
        client = boto3.client('secretsmanager', region_name=region)
        try:
            client.describe_secret(
                SecretId=secret_id
            )
            return True
        except Exception as e:
            return False

    def test_create_secret(self):
        EncryptSecretFactory.create_batch(10)
        secret_data = {
            "sample": "abcd"
        }
        secret_1 = {
            'name': f'random_{uuid.uuid4()}',
            'data': ParseDict(secret_data, Struct()),
            'secret_type': 'CREDENTIALS',
            'domain_id': 'domain_1234',
        }
        request = CreateSecretRequest(**secret_1, )
        response, metadata, code, details = self.request_unary_unary('spaceone.api.secret.v1.Secret.create', request)
        self.assertGrpcStatusCodeOk(code)
        response = MessageToDict(response, preserving_proto_field_name=True)

        self.assertEqual(secret_1.get('domain_id'), response['domain_id'])
        self.assertEqual(secret_1.get('secret_type'), response['secret_type'])
        self.assertTrue(self._check_secretmanager_exists(response['secret_id']))

    def test_get_secret_data(self):
        secret_data = {"secret": utils.random_string()}
        secret_1 = EncryptSecretFactory(encrypted=True, secret_data=secret_data)

        request = GetSecretRequest(secret_id=secret_1.secret_id, domain_id=secret_1.domain_id)
        result, metadata, code, details = self.request_unary_unary('spaceone.api.secret.v1.Secret.get_data', request)
        self.assertGrpcStatusCodeOk(code)
        result = MessageToDict(result, preserving_proto_field_name=True)

        self.assertTrue(result['encrypted'])
        self.assertIsNone(result.get('data'))
        self.assertTrue(result['encrypted_data'])

        options = result['encrypt_options']
        options_key = options.keys()
        self.assertIn('nonce', options_key)
        self.assertIn('encrypt_type', options_key)
        self.assertIn('encrypt_context', options_key)
        self.assertIn('encrypt_data_key', options_key)

        self.assertEqual(options['encrypt_type'], 'AWS_KMS')
        self.assertEqual(options['encrypt_context'], self.get_encrypt_context_by_vo(secret_1))
        self.assertEqual(secret_1.encrypt_data_key, options['encrypt_data_key'])

        # check decrypt
        decrypt_secret_data = self._decrypt(options['encrypt_data_key'], options['nonce'], result['encrypted_data'],
                                            options['encrypt_context'].encode())
        self.assertEqual(secret_data, decrypt_secret_data)

    def _decrypt_data_key(self, encrypt_data_key):
        kms_cli = self.get_kms_client()
        kms_key_id = config.get_global('CONNECTORS')["AWSKMSConnector"]["kms_key_id"]
        response = kms_cli.decrypt(
            CiphertextBlob=encrypt_data_key,
            # KeyId=self.kms_key_id,
        )
        return response['Plaintext']

    def _dict_to_b64(self, data: dict):
        return base64.b64encode(json.dumps(data).encode())

    def _b64_to_dict(self, data: Union[str, bytes]):
        _data = data if isinstance(data, bytes) else data.encode()
        return json.loads(base64.b64decode(_data).decode())

    def _decrypt(self, encrypt_data_key, nonce, encrypt_secret_data, encrypt_context: bytes):
        encrypt_secret_data = base64.b64decode(encrypt_secret_data.encode())
        encrypt_data_key = base64.b64decode(encrypt_data_key.encode())
        nonce = base64.b64decode(nonce.encode())

        data_key = self._decrypt_data_key(encrypt_data_key)

        aesgcm = AESGCM(data_key)
        secret_data = aesgcm.decrypt(nonce, encrypt_secret_data, encrypt_context)
        return self._b64_to_dict(secret_data)

    def test_intergration_secret_service(self):
        secret_data = {
            "sample": "abcd"
        }
        secret_1 = {
            'name': f'random_{uuid.uuid4()}',
            'data': ParseDict(secret_data, Struct()),
            'secret_type': 'CREDENTIALS',
            'domain_id': 'domain_1234',
        }
        request = CreateSecretRequest(**secret_1, )
        response, metadata, code, details = self.request_unary_unary('spaceone.api.secret.v1.Secret.create', request)
        self.assertGrpcStatusCodeOk(code)
        response = MessageToDict(response, preserving_proto_field_name=True)

        self.assertEqual(secret_1.get('domain_id'), response['domain_id'])
        self.assertEqual(secret_1.get('secret_type'), response['secret_type'])
        self.assertTrue(self._check_secretmanager_exists(response['secret_id']))
        secret_id = response['secret_id']

        request = GetSecretRequest(secret_id=response['secret_id'], domain_id=response['domain_id'])
        response, metadata, code, details = self.request_unary_unary('spaceone.api.secret.v1.Secret.get_data', request)
        result = MessageToDict(response, preserving_proto_field_name=True)
        self.assertGrpcStatusCodeOk(code)
        self.assertTrue(result['encrypted'])

        # check decrypt
        options = result['encrypt_options']
        self.assertEqual(options['encrypt_context'],
                         self.get_encrypt_context_by_vo({"domain_id": secret_1['domain_id'], "secret_id": secret_id}))
        decrypt_secret_data = self._decrypt(options['encrypt_data_key'], options['nonce'], result['encrypted_data'],
                                            options['encrypt_context'].encode())
        self.assertEqual(secret_data, decrypt_secret_data)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
