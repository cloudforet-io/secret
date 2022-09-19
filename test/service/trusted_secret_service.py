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
from spaceone.secret.service.trusted_secret_service import TrustedSecretService
from spaceone.secret.model.trusted_secret_model import TrustedSecret

from spaceone.secret.connector.aws_secret_manager_connector import AWSSecretManagerConnector

from spaceone.secret.info.trusted_secret_info import *
from spaceone.secret.info.common_info import StatisticsInfo
from test.factory.secret_factory import SecretFactory
from test.factory.trusted_secret_factory import TrustedSecretFactory


class TestTrustedSecretService(unittest.TestCase):

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
        print('(tearDown) ==> Delete all trusted secret')
        trusted_secret_vos = TrustedSecret.objects.filter()
        trusted_secret_vos.delete()

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(AWSSecretManagerConnector, '__init__', return_value=None)
    @patch.object(AWSSecretManagerConnector, 'create_secret', return_value={'secret_id': 'secret-xyz', 'name': 'Secret'})
    def test_create_trusted_secret(self, *args):
        name = utils.random_string()

        params = {
            'name': name,
            'data': {
                'xxx': 'yyy'
            },
            'tags': {
                'description': 'abcdef'
            },
            'domain_id': self.domain_id,
        }

        self.transaction.method = 'create'
        trusted_secret_svc = TrustedSecretService(transaction=self.transaction)
        trusted_secret_vo = trusted_secret_svc.create(params.copy())

        self.assertIsInstance(trusted_secret_vo, TrustedSecret)
        self.assertEqual(trusted_secret_vo.name, name)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_update_trusted_secret(self, *args):
        trusted_secret_vo = TrustedSecretFactory(domain_id=self.domain_id)

        name = utils.random_string()

        params = {
            'trusted_secret_id': trusted_secret_vo.trusted_secret_id,
            'name': name,
            'domain_id': self.domain_id,
        }

        self.transaction.method = 'update'
        trusted_secret_svc = TrustedSecretService(transaction=self.transaction)
        trusted_secret_vo = trusted_secret_svc.update(params.copy())

        self.assertIsInstance(trusted_secret_vo, TrustedSecret)
        self.assertEqual(trusted_secret_vo.name, name)

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(AWSSecretManagerConnector, '__init__', return_value=None)
    @patch.object(AWSSecretManagerConnector, 'update_secret', return_value={'secret_id': 'secret-xyz', 'name': 'Secret'})
    def test_update_trusted_secret_data(self, *args):
        trusted_secret_vo = TrustedSecretFactory(domain_id=self.domain_id)

        params = {
            'trusted_secret_id': trusted_secret_vo.trusted_secret_id,
            'data': {
                'bbb': 'ccc'
            },
            'domain_id': self.domain_id,
        }

        self.transaction.method = 'update_data'
        trusted_secret_svc = TrustedSecretService(transaction=self.transaction)
        trusted_secret_svc.update_data(params.copy())

    @patch.object(MongoModel, 'connect', return_value=None)
    @patch.object(AWSSecretManagerConnector, '__init__', return_value=None)
    @patch.object(AWSSecretManagerConnector, 'delete_secret',
                  return_value=None)
    def test_delete_trusted_secret(self, *args):
        trusted_secret_vo = TrustedSecretFactory(domain_id=self.domain_id)

        params = {
            'trusted_secret_id': trusted_secret_vo.trusted_secret_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'delete'
        trusted_secret_svc = TrustedSecretService(transaction=self.transaction)
        result = trusted_secret_svc.delete(params.copy())

        self.assertIsNone(result)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_get_trusted_secret(self, *args):
        trusted_secret_vo = TrustedSecretFactory(domain_id=self.domain_id)

        params = {
            'trusted_secret_id': trusted_secret_vo.trusted_secret_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'get'
        trusted_secret_svc = TrustedSecretService(transaction=self.transaction)
        trusted_secret_vo = trusted_secret_svc.get(params)

        print_data(trusted_secret_vo.to_dict(), 'test_get_secret')
        TrustedSecretInfo(trusted_secret_vo)

        self.assertIsInstance(trusted_secret_vo, TrustedSecret)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)