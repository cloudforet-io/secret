import unittest
from spaceone.core.unittest.result import print_data
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.secret.connector.etcd_connector import EtcdConnector


class TestEtcdConnector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.secret')
        config.set_service_config()
        config.set_global(MOCK_MODE=True)
        connector_conf = config.get_global('CONNECTORS').get('EtcdConnector')

        cls.secret_id = utils.generate_id('secret')
        cls.transaction = Transaction({
            'service': 'secret',
            'api_class': 'Secret'
        })
        cls.etcd_connector = EtcdConnector(cls.transaction, connector_conf)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def tearDown(self, *args) -> None:
        print('(tearDown) ==> Delete data')
        self.test_delete_secret()

    def test_create_secret(self, *args):
        print(self.secret_id)
        data = {'test': utils.random_string()}

        self.etcd_connector.create_secret(self.secret_id, data)

        # self.assertIsInstance(secret_vo, Secret)
        # self.assertEqual(secret_vo.name, name)

    def test_update_secret(self, *args):
        data = {'xxx': 'yyy'}
        self.etcd_connector.update_secret(self.secret_id, data)

    def test_delete_secret(self, *args):
        self.etcd_connector.delete_secret(self.secret_id)

    def test_get_secret(self, *args):
        self.test_create_secret()
        self.etcd_connector.get_secret(self.secret_id)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)