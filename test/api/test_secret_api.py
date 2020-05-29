import unittest
import os
from unittest.mock import patch
from mongoengine import connect, disconnect
from google.protobuf.json_format import MessageToDict

from spaceone.core.unittest.result import print_message
from spaceone.core.unittest.runner import RichTestRunner
from spaceone.core import config
from spaceone.core import utils
from spaceone.core.service import BaseService
from spaceone.secret.api.v1.secret import Secret
from test.factories.secret_factory import SecretFactory


class _MockSecretService(BaseService):

    def create(self, params):
        return SecretFactory(**self._get_model_data(params))

    @staticmethod
    def _get_model_data(params):
        model_data = {}
        if 'name' in params:
            model_data['name'] = params['name']

        if 'secret_type' in params:
            model_data['secret_type'] = params['secret_type']

        if 'schema' in params:
            model_data['schema'] = params['schema']

        if 'provider' in params:
            model_data['provider'] = params['provider']

        if 'service_account_id' in params:
            model_data['service_account_id'] = params['service_account_id']

        if 'project_id' in params:
            model_data['project_id'] = params['project_id']

        if 'domain_id' in params:
            model_data['domain_id'] = params['domain_id']

        if 'tags' in params:
            model_data['tags'] = params['tags']

        return model_data


class TestSecretAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.init_conf(service='secret')
        connect('test', host='mongomock://localhost')
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        disconnect()

    @patch('spaceone.core.pygrpc.BaseAPI.__init__', return_value=None)
    @patch('spaceone.core.locator.Locator.get_service', return_value=_MockSecretService())
    @patch('spaceone.core.pygrpc.BaseAPI.parse_request')
    def test_create_secret(self, mock_parse_request, *args):
        params = {
            'name': utils.random_string(),
            'secret_type': 'CREDENTIALS',
            'data': {},
            'tags': {
                'key': 'value'
            },
            'service_account_id': utils.generate_id('svc-account'),
            'provider': 'aws',
            'schema': 'aws_access_key',
            'domain_id': utils.generate_id('domain')
        }
        mock_parse_request.return_value = (params, {})

        secret_servicer = Secret()
        secret_info = secret_servicer.create({}, {})

        print_message(secret_info, 'test_create_secret')

        self.assertEqual(secret_info.name, params['name'])
        self.assertEqual(secret_info.domain_id, params['domain_id'])
        self.assertEqual(secret_info.schema, params.get('schema', ''))
        self.assertEqual(secret_info.provider, params.get('provider', ''))
        self.assertEqual(secret_info.service_account_id, params.get('service_account_id', ''))
        self.assertEqual(secret_info.project_id, params.get('project_id', ''))
        self.assertDictEqual(MessageToDict(secret_info.tags), params['tags'])
        self.assertIsNone(getattr(secret_info, 'data', None))


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
