import unittest
from unittest.mock import patch
from mongoengine import connect, disconnect

from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.model.mongo_model import MongoModel
from spaceone.core.transaction import Transaction
from spaceone.secret.service.secret_group_service import SecretGroupService
from spaceone.secret.model.secret_group_model import SecretGroup
from spaceone.secret.info.secret_group_info import *
from spaceone.secret.info.common_info import StatisticsInfo
from test.factory.secret_group_factory import SecretGroupFactory


class TestSecretGroupService(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.secret')
        connect('test', host='mongomock://localhost')

        cls.domain_id = utils.generate_id('domain')
        cls.transaction = Transaction({
            'service': 'secret',
            'api_class': 'SecretGroup'
        })
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        disconnect()

    @patch.object(MongoModel, 'connect', return_value=None)
    def tearDown(self, *args) -> None:
        print()
        print('(tearDown) ==> Delete all secret group')
        secret_group_vos = SecretGroup.objects.filter()
        secret_group_vos.delete()

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_create_secret_group(self, *args):
        name = utils.random_string()

        params = {
            'name': name,
            'tags': {
                'description': 'test'
            },
            'domain_id': self.domain_id,
        }

        self.transaction.method = 'create'
        secret_group_svc = SecretGroupService(transaction=self.transaction)
        secret_group_vo = secret_group_svc.create(params.copy())

        self.assertIsInstance(secret_group_vo, SecretGroup)
        self.assertEqual(secret_group_vo.name, name)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_update_secret_group(self, *args):
        secret_group_vo = SecretGroupFactory(domain_id=self.domain_id)

        name = utils.random_string()

        params = {
            'secret_group_id': secret_group_vo.secret_group_id,
            'name': name,
            'domain_id': self.domain_id,
        }

        self.transaction.method = 'update'
        secret_group_svc = SecretGroupService(transaction=self.transaction)
        secret_group_vo = secret_group_svc.update(params.copy())

        self.assertIsInstance(secret_group_vo, SecretGroup)
        self.assertEqual(secret_group_vo.name, name)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_delete_secret_group(self, *args):
        secret_group_vo = SecretGroupFactory(domain_id=self.domain_id)

        params = {
            'secret_group_id': secret_group_vo.secret_group_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'delete'
        secret_group_svc = SecretGroupService(transaction=self.transaction)
        result = secret_group_svc.delete(params.copy())

        self.assertIsNone(result)

    @patch.object(MongoModel, 'connect', return_value=None)
    def test_get_secret_group(self, *args):
        secret_group_vo = SecretGroupFactory(domain_id=self.domain_id)

        params = {
            'secret_group_id': secret_group_vo.secret_group_id,
            'domain_id': self.domain_id
        }

        self.transaction.method = 'get'
        secret_group_svc = SecretGroupService(transaction=self.transaction)
        secret_group_vo = secret_group_svc.get(params)

        print_data(secret_group_vo.to_dict(), 'test_get_secret_group')
        SecretGroupInfo(secret_group_vo)

        self.assertIsInstance(secret_group_vo, SecretGroup)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)