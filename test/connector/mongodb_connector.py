import unittest
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.transaction import Transaction
from spaceone.secret.connector.mongodb_connector import MongoDBConnector


class TestMongoDBConnector(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(package='spaceone.secret')
        config.set_service_config()
        config.set_global()
        connector_conf = config.get_global('CONNECTORS').get('MongoDBConnector')

        cls.secret_id = utils.generate_id('secret')
        cls.transaction = Transaction({
            'service': 'secret',
            'api_class': 'Secret'
        })
        cls.mongo_connector = MongoDBConnector(cls.transaction, connector_conf)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()

    def tearDown(self, *args) -> None:
        print('(tearDown) ==> Delete data')
        self.test_delete_secret()

    def test_create_secret(self, *args):
        # print(self.secret_id)
        data = {'test': utils.random_string()}

        self.mongo_connector.create_secret(self.secret_id, data)

    def test_update_secret(self, *args):
        self.test_create_secret()
        data = {'xxxxxxxx': 'yyyyyyyyyy'}
        self.mongo_connector.update_secret(self.secret_id, data)

    def test_delete_secret(self, *args):
        self.mongo_connector.delete_secret(self.secret_id)

    def test_get_secret(self, *args):
        self.test_create_secret()
        result = self.mongo_connector.get_secret(self.secret_id)
        print(result)

if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)