import os
import sys
import unittest
import uuid

import boto3
import pkg_resources
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
        tags = {"test": "tags"}
        SecretFactory.create_batch(10)
        secret_data = {"secret": f"{os.urandom(10)}"}
        secret_1 = SecretFactory(tags=tags, secret_data=secret_data)
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

    def setup_kms_key(self):
        region_name = config.get_global('CONNECTORS', {}).get('AWSKMSConnector', {}).get("region_name")

        key_id = boto3.client('kms', region_name=region_name).create_key()['KeyMetadata']['KeyId']
        config.set_global(CONNECTORS={"AWSKMSConnector": {"kms_key_id": key_id}})

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
        self.assertTrue(self._check_secretmanager_exists(result_vo.secret_id))

    def test_get_secret_data(self):
        tags = {"test": "tags"}
        EncryptSecretFactory.create_batch(10)
        secret_data = {"secret": utils.random_string()}
        secret_1 = EncryptSecretFactory(tags=tags, secret_data=secret_data)
        result = self.svc.get_data({"secret_id": secret_1.secret_id, "domain_id": secret_1.domain_id})
        self.assertEqual(secret_data, result)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
