import unittest
from unittest.mock import patch
from mongoengine import connect, disconnect

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.model.mongo_model import MongoModel
from spaceone.core.transaction import Transaction
from spaceone.secret.error import *
from spaceone.secret.service.secret_service import SecretService
from spaceone.secret.model.secret_model import Secret

from spaceone.secret.connector.aws_secret_manager_connector import AWSSecretManagerConnector
from spaceone.secret.connector.mongodb_connector import MongoDBConnector

from spaceone.secret.info.secret_info import *
from spaceone.secret.info.common_info import StatisticsInfo
from test.factory.secret_factory import SecretFactory


class TestSecretService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.secret')
        config.set_service_config()
        config.set_global(MOCK_MODE=True)
        connect('test', host='mongomock://localhost')

        cls.domain_id = utils.generate_id('domain')
        cls.transaction = Transaction({
            'service': 'secret',
            'api_class': 'Secret'
        })
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        disconnect()

    @patch.object(MongoModel, 'connect', return_value=None)
    def tearDown(self, *args) -> None:
        print()
        print('(tearDown) ==> Delete all secret')
        secret_vos = Secret.objects.filter()
        secret_vos.delete()

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(MongoDBConnector, '__init__', return_value=None)
    @patch.object(MongoDBConnector, 'create_secret', return_value={'secret_id': 'secret-xyz', 'name': 'Secret'})
    def test_create_secret(self, *args):
        name = utils.random_string()

        params = {
            'name': name,
            'data': {
                'xxx': 'yyy'
            },
            'secret_type': 'CREDENTIALS',
            'tags': {
                'description': 'abcdef'
            },
            'domain_id': self.domain_id,
        }

        self.transaction.method = 'create'
        secret_svc = SecretService(transaction=self.transaction)
        secret_vo = secret_svc.create(params.copy())

        self.assertIsInstance(secret_vo, Secret)
        self.assertEqual(secret_vo.name, name)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_update_secret(self, *args):
        secret_vo = SecretFactory(domain_id=self.domain_id)

        name = utils.random_string()

        params = {
            'secret_id': secret_vo.secret_id,
            'name': name,
            'domain_id': self.domain_id,
        }

        self.transaction.method = 'update'
        secret_svc = SecretService(transaction=self.transaction)
        secret_vo = secret_svc.update(params.copy())

        self.assertIsInstance(secret_vo, Secret)
        self.assertEqual(secret_vo.name, name)

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(AWSSecretManagerConnector, '__init__', return_value=None)
    @patch.object(AWSSecretManagerConnector, 'update_secret', return_value={'secret_id': 'secret-xyz', 'name': 'Secret'})
    def test_update_secret_data(self, *args):
        secret_vo = SecretFactory(domain_id=self.domain_id)

        params = {
            'secret_id': secret_vo.secret_id,
            'data': {
                'bbb': 'ccc'
            },
            'domain_id': self.domain_id,
        }

        self.transaction.method = 'update_data'
        secret_svc = SecretService(transaction=self.transaction)
        secret_svc.update_data(params.copy())

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(AWSSecretManagerConnector, '__init__', return_value=None)
    @patch.object(AWSSecretManagerConnector, 'delete_secret',
                  return_value=None)
    def test_delete_secret(self, *args):
        secret_vo = SecretFactory(domain_id=self.domain_id)

        params = {
            'secret_id': secret_vo.secret_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'delete'
        secret_svc = SecretService(transaction=self.transaction)
        result = secret_svc.delete(params.copy())

        self.assertIsNone(result)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_get_secret(self, *args):
        secret_vo = SecretFactory(domain_id=self.domain_id)

        params = {
            'secret_id': secret_vo.secret_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'get'
        secret_svc = SecretService(transaction=self.transaction)
        secret_vo = secret_svc.get(params)

        print_data(secret_vo.to_dict(), 'test_get_secret')
        SecretInfo(secret_vo)

        self.assertIsInstance(secret_vo, Secret)

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(AWSSecretManagerConnector, '__init__', return_value=None)
    @patch.object(AWSSecretManagerConnector, 'get_secret', return_value={'data': 'xyz'})
    def test_get_secret_data(self, *args):
        secret_vo = SecretFactory(domain_id=self.domain_id)

        params = {
            'secret_id': secret_vo.secret_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'get_data'
        secret_svc = SecretService(transaction=self.transaction)
        secret_dict = secret_svc.get_data(params)

        print_data(secret_dict, 'test_get_secret_data')
        SecretDataInfo(secret_dict)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)