import os
import unittest
from google.protobuf.json_format import MessageToDict

from spaceone.core import utils, pygrpc
from spaceone.core.unittest.result import print_message
from spaceone.core.unittest.runner import RichTestRunner


class TestSecretGroup(unittest.TestCase):
    config = utils.load_yaml_from_file(
        os.environ.get('SPACEONE_TEST_CONFIG_FILE', './config.yml'))

    identity_v1 = None
    secret_v1 = None
    domain = None
    domain_owner = None
    owner_id = None
    owner_pw = None
    token = None

    @classmethod
    def setUpClass(cls):
        super(TestSecretGroup, cls).setUpClass()
        endpoints = cls.config.get('ENDPOINTS', {})
        cls.identity_v1 = pygrpc.client(endpoint=endpoints.get('identity', {}).get('v1'), version='v1')
        cls.secret_v1 = pygrpc.client(endpoint=endpoints.get('secret', {}).get('v1'), version='v1')

        cls._create_domain()
        cls._create_domain_owner()
        cls._issue_owner_token()

    @classmethod
    def tearDownClass(cls):
        super(TestSecretGroup, cls).tearDownClass()
        cls.identity_v1.DomainOwner.delete({
            'domain_id': cls.domain.domain_id,
            'owner_id': cls.owner_id
        })

        if cls.domain:
            cls.identity_v1.Domain.delete({'domain_id': cls.domain.domain_id})

    def setUp(self):
        self.secret_groups = []
        self.secrets = []

        self.secret = None
        self.secret_group = None

    def tearDown(self):
        for secret in self.secrets:
            self.secret_v1.Secret.delete(
                {'secret_id': secret.secret_id,
                 'domain_id': self.domain.domain_id},
                metadata=(('token', self.token),)
            )
            print(f'delete secret: {secret.secret_id}')

        for secret_group in self.secret_groups:
            self.secret_v1.SecretGroup.delete(
                {'secret_group_id': secret_group.secret_group_id,
                 'domain_id': self.domain.domain_id},
                metadata=(('token', self.token),)
            )
            print(f'delete secret group: {secret_group.secret_group_id}')

    @classmethod
    def _create_domain(cls):
        name = utils.random_string()
        param = {
            'name': name
        }

        cls.domain = cls.identity_v1.Domain.create(param)
        print(f'domain_id: {cls.domain.domain_id}')
        print(f'domain_name: {cls.domain.name}')

    @classmethod
    def _create_domain_owner(cls):
        cls.owner_id = utils.random_string()[0:10]
        cls.owner_pw = 'qwerty'

        param = {
            'owner_id': cls.owner_id,
            'password': cls.owner_pw,
            'name': 'Steven' + utils.random_string()[0:5],
            'timezone': 'utc+9',
            'email': 'Steven' + utils.random_string()[0:5] + '@mz.co.kr',
            'mobile': '+821026671234',
            'domain_id': cls.domain.domain_id
        }

        owner = cls.identity_v1.DomainOwner.create(
            param
        )
        cls.domain_owner = owner
        print(f'owner_id: {cls.owner_id}')
        print(f'owner_pw: {cls.owner_pw}')

    @classmethod
    def _issue_owner_token(cls):
        token_param = {
            'credentials': {
                'user_type': 'DOMAIN_OWNER',
                'user_id': cls.owner_id,
                'password': cls.owner_pw
            },
            'domain_id': cls.domain.domain_id
        }

        issue_token = cls.identity_v1.Token.issue(token_param)
        cls.token = issue_token.access_token
        print(f'token: {cls.token}')

    def test_create_secret(self):
        name = utils.random_string()
        self.data = {
            utils.random_string(): utils.random_string(),
            utils.random_string(): utils.random_string()
        }
        param = {
            'name': name,
            'domain_id': self.domain.domain_id,
            'data': self.data,
            'secret_type': 'CREDENTIALS'
        }

        self.secret = self.secret_v1.Secret.create(param, metadata=(('token', self.token),))
        self.secrets.append(self.secret)
        self.assertEqual(self.secret.name, name)

    def test_create_secret_group_only(self):
        name = utils.random_string()
        param = {
            'name': name,
            'domain_id': self.domain.domain_id,
            'tags': [
                {
                    'key': utils.random_string(),
                    'value': utils.random_string()
                }, {
                    'key': utils.random_string(),
                    'value': utils.random_string()
                }
            ]
        }

        self.secret_group = self.secret_v1.SecretGroup.create(param, metadata=(('token', self.token),))

        print_message(self.secret_group, 'test_create_secret_group_only')

        self.secret_groups.append(self.secret_group)
        self.assertEqual(self.secret_group.name, name)

    def test_create_secret_group(self, name=None):
        self.test_create_secret()
        self.test_create_secret()

        if name is None:
            name = utils.random_string()

        param = {
            'name': name,
            'domain_id': self.domain.domain_id,
            'tags': [
                {
                    'key': utils.random_string(),
                    'value': utils.random_string()
                }, {
                    'key': utils.random_string(),
                    'value': utils.random_string()
                }
            ]
        }

        self.secret_group = self.secret_v1.SecretGroup.create(param, metadata=(('token', self.token),))

        for secret in self.secrets:
            self._add_secret_to_secret_group(secret.secret_id)

        print_message(self.secret_group, 'test_create_secret_group')

        self.secret_groups.append(self.secret_group)
        self.assertEqual(self.secret_group.name, name)

    def _add_secret_to_secret_group(self, secret_id):
        result = self.secret_v1.SecretGroup.add_secret({
            'secret_group_id': self.secret_group.secret_group_id,
            'secret_id': secret_id,
            'domain_id': self.domain.domain_id
        }, metadata=(('token', self.token),))

        print_message(result, '_add_secret_to_secret_group')

    def test_update_secret_group_tag(self):
        self.test_create_secret_group_only()

        tags = [
            {
                'key': 'aaa',
                'value': '123'
            }
        ]
        param = {
            'secret_group_id': self.secret_group.secret_group_id,
            'domain_id': self.domain.domain_id,
            'tags': tags
        }

        self.secret_group = self.secret_v1.SecretGroup.update(param, metadata=(('token', self.token),))
        secret_group_data = MessageToDict(self.secret_group, preserving_proto_field_name=True)
        self.assertEqual(secret_group_data['tags'], tags)

    def test_update_secret_group_name(self):
        self.test_create_secret_group_only()

        name = 'cred-test-000'
        param = {'secret_group_id': self.secret_group.secret_group_id,
                 'name': name,
                 'domain_id': self.domain.domain_id,
                }

        self.secret_group = self.secret_v1.SecretGroup.update(param, metadata=(('token', self.token),))

        self.assertEqual(self.secret_group.name, name)

    def test_get_secret_group(self):
        self.test_create_secret_group_only()
        param = {
            'secret_group_id': self.secret_group.secret_group_id,
            'domain_id': self.domain.domain_id
        }
        secret_group = self.secret_v1.SecretGroup.get(param, metadata=(('token', self.token),))
        self.assertEqual(self.secret_group.name, secret_group.name)

    def test_list_secret_groups(self):
        self.test_create_secret_group_only()
        self.test_create_secret_group_only()
        self.test_create_secret_group_only()
        self.test_create_secret_group_only()
        self.test_create_secret_group_only()

        param = {
            'query': {
                'filter': [
                    {'k': 'name', 'v': self.secret_group.name, 'o': 'eq'}
                ]
            }, 'domain_id': self.domain.domain_id
        }

        result = self.secret_v1.SecretGroup.list(param, metadata=(('token', self.token),))

        self.assertEqual(result.total_count, 1)

    def test_list_secret_groups_query_1(self):
        self.test_create_secret_group()

        param = {
            'secret_id': self.secret.secret_id,
            'domain_id': self.domain.domain_id
        }

        result = self.secret_v1.SecretGroup.list(param, metadata=(('token', self.token),))
        print_message(result, 'test_list_secret_groups_query_1')

        self.assertEqual(1, result.total_count)

    def test_list_secret_groups_query_2(self):
        self.test_create_secret_group(name='jhsong-test-000')
        self.test_create_secret_group(name='jhsong-test-002')
        self.test_create_secret_group(name='new-corona-test-001')

        param = {
            'query': {
                'filter': [
                    {'k': 'name', 'v': 'jhsong', 'o': 'contain'}
                ]
            },
            'domain_id': self.domain.domain_id
        }

        result = self.secret_v1.SecretGroup.list(param, metadata=(('token', self.token),))

        self.assertEqual(result.total_count, 2)

    def test_stat_secret_group(self):
        self.test_list_secret_groups()

        params = {
            'domain_id': self.domain.domain_id,
            'query': {
                'aggregate': {
                    'group': {
                        'keys': [{
                            'key': 'secret_group_id',
                            'name': 'Id'
                        }],
                        'fields': [{
                            'operator': 'count',
                            'name': 'Count'
                        }]
                    }
                },
                'sort': {
                    'name': 'Count',
                    'desc': True
                }
            }
        }

        result = self.secret_v1.SecretGroup.stat(
            params, metadata=(('token', self.token),))

        print(result)

    def test_add_secret_in_group(self):
        self.test_create_secret_group()
        self.test_create_secret_group_only()
        self.test_create_secret()

        param = {'secret_group_id': self.secret_group.secret_group_id,
                 'secret_id': self.secret.secret_id,
                 'domain_id': self.domain.domain_id
                }

        secret_group_map = self.secret_v1.SecretGroup.add_secret(param, metadata=(('token', self.token),))

        print_message(secret_group_map, 'test_add_secret_in_group')
        self.assertEqual(secret_group_map.secret_info.secret_id, self.secret.secret_id)
        self.assertEqual(secret_group_map.secret_group_info.secret_group_id, self.secret_group.secret_group_id)

    def test_add_secret_duplicate_in_group(self):
        self.test_create_secret_group_only()
        self.test_create_secret()

        param = {'secret_group_id': self.secret_group.secret_group_id,
                 'secret_id': self.secret.secret_id,
                 'domain_id': self.domain.domain_id
                 }

        self.secret_group = self.secret_v1.SecretGroup.add_secret(param, metadata=(('token', self.token),))

        with self.assertRaises(Exception):
            self.secret_v1.SecretGroup.add_secret(param, metadata=(('token', self.token),))

    def test_remove_secret_in_group(self):
        self.test_create_secret_group()
        self.test_create_secret()

        param = {
            'secret_group_id': self.secret_group.secret_group_id,
            'secret_id': self.secret.secret_id,
            'domain_id': self.domain.domain_id
        }

        self.secret_v1.SecretGroup.add_secret(param, metadata=(('token', self.token),))

        param = {
            'secret_group_id': self.secret_group.secret_group_id,
            'secret_id': self.secret.secret_id,
            'domain_id': self.domain.domain_id
        }

        self.secret_v1.SecretGroup.remove_secret(param, metadata=(('token', self.token),))

        param = {
            'secret_group_id': self.secret_group.secret_group_id,
            'include_secret_group': True,
            'domain_id': self.domain.domain_id
        }

        results = self.secret_v1.Secret.list(param, metadata=(('token', self.token),))
        self.assertEqual(self.secret_group.secret_group_id, self.secret_group.secret_group_id)


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
