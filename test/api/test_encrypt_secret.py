import base64
import json
import os
import sys
import unittest
import uuid
from typing import Union

import boto3
import pkg_resources
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from mongoengine import connect, disconnect_all
from moto import mock_kms, mock_secretsmanager
from spaceone.core import config, utils
from spaceone.core.locator import Locator
from spaceone.core.unittest.runner import RichTestRunner

from src.spaceone.secret.model.secret_model import Secret
from src.spaceone.secret.service.secret_service import SecretService
from test.factories.secret import EncryptSecretFactory, SecretFactory

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_PATH = os.path.join(ROOT_DIR, 'src')


def set_python_path(src_path: str, package: str):
    sys.path.insert(0, src_path)
    pkg_resources.declare_namespace(package)
    try:
        __import__(package)
    except Exception:
        raise Exception(f'The package({package}) can not imported. '
                        'Please check the module path.')


class SpaceoneTestCase(unittest.TestCase):
    config: dict = {}
    package: str = None
    src_path: str = None
    _locator: Locator = None

    @property
    def locator(self):
        if not self._locator:
            self._locator = Locator()
        return self._locator

    @classmethod
    def setUpClass(cls) -> None:
        super(SpaceoneTestCase, cls).setUpClass()
        set_python_path(cls.src_path, cls.package)
        config.init_conf(
            package=cls.package,
            server_type='grpc',
        )
        config.set_service_config()
        config.set_global(**cls.config)
        connect('default', host='mongomock://localhost')

    @classmethod
    def tearDownClass(cls) -> None:
        disconnect_all()


@mock_kms
@mock_secretsmanager
class TestDefaultSecretService(SpaceoneTestCase):
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

    def setUp(self):
        super(TestDefaultSecretService, self).setUp()
        self.svc: SecretService = self.locator.get_service('SecretService')

    def test_get_secret(self):
        tags = {"test": "tags"}
        SecretFactory.create_batch(10)
        secret_1 = SecretFactory(tags=tags)

        result = self.svc.get({"secret_id": secret_1.secret_id, "domain_id": secret_1.domain_id})

        self.assertEqual(secret_1.secret_id, result.secret_id)
        self.assertEqual(secret_1.domain_id, result.domain_id)
        self.assertEqual(secret_1.tags, result.tags)

    def test_get_secret_data(self):
        SecretFactory.create_batch(10)
        secret_data = {"secret": f"{os.urandom(10)}"}
        secret_1 = SecretFactory( secret_data=secret_data)
        result = self.svc.get_data({"secret_id": secret_1.secret_id, "domain_id": secret_1.domain_id})
        self.assertEqual(secret_data, result)

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
            'data': secret_data,
            'secret_type': 'CREDENTIALS',
            'domain_id': 'domain_1234',
        }
        result_vo: Secret = self.svc.create(secret_1)
        self.assertEqual(secret_1.get('domain_id'), result_vo.domain_id)
        self.assertEqual(secret_1.get('secret_type'), result_vo.secret_type)
        self.assertTrue(self._check_secretmanager_exists(result_vo.secret_id))


@mock_kms
@mock_secretsmanager
class TestEncryptSecretService(SpaceoneTestCase):
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
        super(TestEncryptSecretService, self).setUp()
        self.setup_kms_key()
        self.svc: SecretService = self.locator.get_service('SecretService')

    def test_get_secret(self):
        tags = {"test": "tags"}
        EncryptSecretFactory.create_batch(10)
        secret_1 = EncryptSecretFactory(tags=tags)

        result = self.svc.get({"secret_id": secret_1.secret_id, "domain_id": secret_1.domain_id})

        self.assertEqual(secret_1.secret_id, result.secret_id)
        self.assertEqual(secret_1.domain_id, result.domain_id)
        self.assertEqual(secret_1.tags, result.tags)

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
            'data': secret_data,
            'secret_type': 'CREDENTIALS',
            'domain_id': 'domain_1234',
        }
        result_vo: Secret = self.svc.create(secret_1)
        self.assertEqual(secret_1.get('domain_id'), result_vo.domain_id)
        self.assertEqual(secret_1.get('secret_type'), result_vo.secret_type)
        self.assertTrue(result_vo.encrypt)
        self.assertTrue(self._check_secretmanager_exists(result_vo.secret_id))

    def test_get_secret_data(self):
        EncryptSecretFactory.create_batch(10)
        secret_data = {"secret": utils.random_string()}
        secret_1 = EncryptSecretFactory(encrypt=True, secret_data=secret_data)
        result = self.svc.get_data({"secret_id": secret_1.secret_id, "domain_id": secret_1.domain_id})
        self.assertNotEqual(secret_data, result)
        self.assertEqual(result['encrypt_context'], {"secret_id": secret_1.secret_id, "domain_id": secret_1.domain_id})
        self.assertEqual(secret_1.encrypt_data_key, result['encrypt_data_key'])

        # check decrypt
        decrypt_secret_data = self._decrypt(result['encrypt_data_key'], result['nonce'], result['encrypt_data'],
                                            result['encrypt_context'])
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

    def _decrypt(self, encrypt_data_key, nonce, encrypt_secret_data, encrypt_context: dict):
        encrypt_secret_data = base64.b64decode(encrypt_secret_data.encode())
        encrypt_data_key = base64.b64decode(encrypt_data_key.encode())
        nonce = base64.b64decode(nonce.encode())
        encrypt_context_b64 = self._dict_to_b64(encrypt_context)

        data_key = self._decrypt_data_key(encrypt_data_key)
        aesgcm = AESGCM(data_key)

        secret_data = aesgcm.decrypt(nonce, encrypt_secret_data, encrypt_context_b64)

        return self._b64_to_dict(secret_data)

    def test_intergration_secret_service(self):
        secret_data = {
            "sample": "abcd"
        }
        secret_1 = {
            'name': f'random_{uuid.uuid4()}',
            'data': secret_data,
            'secret_type': 'CREDENTIALS',
            'domain_id': 'domain_1234',
        }
        result_vo: Secret = self.svc.create(secret_1)
        self.assertEqual(secret_1.get('domain_id'), result_vo.domain_id)
        self.assertEqual(secret_1.get('secret_type'), result_vo.secret_type)
        self.assertTrue(result_vo.encrypt)
        self.assertTrue(self._check_secretmanager_exists(result_vo.secret_id))

        result = self.svc.get_data({"secret_id": result_vo.secret_id, "domain_id": result_vo.domain_id})
        self.assertNotEqual(secret_data, result)
        self.assertEqual(result['encrypt_context'],
                         {"domain_id": result_vo.domain_id, "secret_id": result_vo.secret_id})

        # check decrypt
        decrypt_secret_data = self._decrypt(result['encrypt_data_key'], result['nonce'], result['encrypt_data'],
                                            result['encrypt_context'])
        self.assertEqual(secret_data, decrypt_secret_data)

    def test_legacy_secret_data(self):
        legacy_secret_data = {
            "not_encrypt": "hahaha"
        }
        legacy_secret = {
            'name': f'legacy_random_{uuid.uuid4()}',
            'data': legacy_secret_data,
            'secret_type': 'CREDENTIALS',
            'domain_id': 'domain_1234',
        }

        secret_data = {
            "sample": "abcd"
        }
        secret_1 = {
            'name': f'random_{uuid.uuid4()}',
            'data': secret_data,
            'secret_type': 'CREDENTIALS',
            'domain_id': 'domain_1234',
        }

        config.set_global(ENCRYPT=False)
        legacy_vo: Secret = self.svc.create(legacy_secret)
        self.assertFalse(legacy_vo.encrypt)

        config.set_global(ENCRYPT=True)
        result_vo: Secret = self.svc.create(secret_1)
        self.assertTrue(self._check_secretmanager_exists(result_vo.secret_id))


        self.assertTrue(config.get_global('ENCRYPT'))
        # check legacy secret decrypt
        result = self.svc.get_data({"secret_id": legacy_vo.secret_id, "domain_id": legacy_vo.domain_id})
        self.assertEqual(legacy_secret_data, result)


        result = self.svc.get_data({"secret_id": result_vo.secret_id, "domain_id": result_vo.domain_id})
        self.assertNotEqual(secret_data, result)
        self.assertEqual(result['encrypt_context'],
                         {"domain_id": result_vo.domain_id, "secret_id": result_vo.secret_id})

        # check decrypt
        decrypt_secret_data = self._decrypt(result['encrypt_data_key'], result['nonce'], result['encrypt_data'],
                                            result['encrypt_context'])
        self.assertEqual(secret_data, decrypt_secret_data)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
