import os
import unittest
import pprint
from google.protobuf.json_format import MessageToDict

from spaceone.core import utils, pygrpc
from spaceone.core.unittest.result import print_message
from spaceone.core.unittest.runner import RichTestRunner


class TestSecret(unittest.TestCase):
    config = utils.load_yaml_from_file(
        os.environ.get('SPACEONE_TEST_CONFIG_FILE', './config.yml'))

    pp = pprint.PrettyPrinter(indent=4)
    identity_v1 = None
    secret_v1 = None
    domain = None
    domain_owner = None
    owner_id = None
    owner_pw = None
    owner_token = None

    def _print_data(self, data, description=None):
        print()
        if description:
            print(f'[ {description} ]')

        self.pp.pprint(MessageToDict(data, preserving_proto_field_name=True))

    @classmethod
    def setUpClass(cls):
        super(TestSecret, cls).setUpClass()
        endpoints = cls.config.get('ENDPOINTS', {})
        cls.identity_v1 = pygrpc.client(endpoint=endpoints.get('identity', {}).get('v1'), version='v1')
        cls.secret_v1 = pygrpc.client(endpoint=endpoints.get('secret', {}).get('v1'), version='v1')

        cls._create_domain()
        cls._create_domain_owner()
        cls._issue_owner_token()

    @classmethod
    def tearDownClass(cls):
        super(TestSecret, cls).tearDownClass()
        cls.identity_v1.DomainOwner.delete(
            {
                'domain_id': cls.domain.domain_id,
                'owner_id': cls.owner_id
            },
            metadata=(('token', cls.owner_token),)
        )
        print(f'>> delete domain owner: {cls.owner_id}')

        if cls.domain:
            cls.identity_v1.Domain.delete(
                {
                    'domain_id': cls.domain.domain_id
                },
                metadata=(('token', cls.owner_token),)
            )
            print(f'>> delete domain: {cls.domain.name} ({cls.domain.domain_id})')

    @classmethod
    def _create_domain(cls):
        name = utils.random_string()
        params = {
            'name': name
        }

        cls.domain = cls.identity_v1.Domain.create(params)
        print(f'domain_id: {cls.domain.domain_id}')
        print(f'domain_name: {cls.domain.name}')

    @classmethod
    def _create_domain_owner(cls):
        cls.owner_id = utils.random_string()
        cls.owner_pw = utils.generate_password()

        owner = cls.identity_v1.DomainOwner.create({
            'owner_id': cls.owner_id,
            'password': cls.owner_pw,
            'domain_id': cls.domain.domain_id
        })

        cls.domain_owner = owner
        print(f'owner_id: {cls.owner_id}')
        print(f'owner_pw: {cls.owner_pw}')

    @classmethod
    def _issue_owner_token(cls):
        token_params = {
            'user_type': 'DOMAIN_OWNER',
            'user_id': cls.owner_id,
            'credentials': {
                'password': cls.owner_pw
            },
            'domain_id': cls.domain.domain_id
        }

        issue_token = cls.identity_v1.Token.issue(token_params)
        cls.owner_token = issue_token.access_token

    def setUp(self):
        self.service_accounts = []
        self.service_account = None
        self.projects = []
        self.project = None
        self.project_groups = []
        self.project_group = None
        self.secrets = []
        self.secret = None
        self.secret_groups = []
        self.secret_group = None
        self.secret_data = None

    def tearDown(self):
        print()
        for secret in self.secrets:
            self.secret_v1.Secret.delete(
                {'secret_id': secret.secret_id,
                 'domain_id': self.domain.domain_id},
                metadata=(('token', self.owner_token),)
            )
            print(f'delete secret: {secret.name} ({secret.secret_id})')

        for secret_group in self.secret_groups:
            self.secret_v1.SecretGroup.delete(
                {'secret_group_id': secret_group.secret_group_id,
                 'domain_id': self.domain.domain_id},
                metadata=(('token', self.owner_token),)
            )
            print(f'delete secret group: {secret_group.name} ({secret_group.secret_group_id})')

        for service_account in self.service_accounts:
            self.identity_v1.ServiceAccount.delete(
                {'service_account_id': service_account.service_account_id,
                 'domain_id': self.domain.domain_id},
                metadata=(('token', self.owner_token),)
            )
            print(f'>> delete service account: {service_account.name} ({service_account.service_account_id})')

        for project in self.projects:
            self.identity_v1.Project.delete(
                {'project_id': project.project_id,
                 'domain_id': self.domain.domain_id},
                metadata=(('token', self.owner_token),)
            )
            print(f'>> delete project: {project.name} ({project.project_id})')

        for project_group in self.project_groups:
            self.identity_v1.ProjectGroup.delete(
                {'project_group_id': project_group.project_group_id,
                 'domain_id': self.domain.domain_id},
                metadata=(('token', self.owner_token),)
            )
            print(f'>> delete project group: {project_group.name} ({project_group.project_group_id})')

    def _create_project_group(self, name=None):
        if name is None:
            name = 'ProjectGroup-' + utils.random_string()[0:5]

        params = {
            'name': name,
            'domain_id': self.domain.domain_id
        }

        self.project_group = self.identity_v1.ProjectGroup.create(
            params,
            metadata=(('token', self.owner_token),)
        )

        self.project_groups.append(self.project_group)
        self.assertEqual(self.project_group.name, params['name'])

    def _create_project(self, project_group_id, name=None):
        if name is None:
            name = 'Project-' + utils.random_string()[0:5]

        params = {
            'name': name,
            'project_group_id': project_group_id,
            'domain_id': self.domain.domain_id
        }

        self.project = self.identity_v1.Project.create(
            params,
            metadata=(('token', self.owner_token),)
        )

        self.projects.append(self.project)
        self.assertEqual(self.project.name, params['name'])

    def _create_service_account(self, project_id, name=None):
        if name is None:
            name = 'SA-' + utils.random_string()[0:5]

        params = {
            'name': name,
            'data': {
                'account_id': 'xxxxx'
            },
            'project_id': project_id,
            'provider': 'aws',
            'domain_id': self.domain.domain_id
        }

        self.service_account = self.identity_v1.ServiceAccount.create(
            params,
            metadata=(('token', self.owner_token),)
        )

        self.service_accounts.append(self.service_account)
        self.assertEqual(self.service_account.name, params['name'])

    def test_create_secret(self, name=None):
        if name is None:
            name = utils.random_string()

        self.secret_data = {
            utils.random_string(): utils.random_string(),
            utils.random_string(): utils.random_string()
        }

        param = {
            'name': name,
            'domain_id': self.domain.domain_id,
            'tags': {
                utils.random_string(): utils.random_string(),
                utils.random_string(): utils.random_string()
            },
            'data': self.secret_data,
            'secret_type': 'CREDENTIALS'
        }

        self.secret = self.secret_v1.Secret.create(param, metadata=(('token', self.owner_token),))
        print_message(self.secret, 'test_create_secret')
        self.secrets.append(self.secret)
        self.assertEqual(self.secret.name, name)

    def test_create_secret_with_service_account(self):
        self._create_project_group()
        self._create_project(self.project_group.project_group_id)
        self._create_service_account(self.project.project_id)

        self.secret_data = {
            utils.random_string(): utils.random_string(),
            utils.random_string(): utils.random_string()
        }

        param = {'name': utils.random_string(),
                 'domain_id': self.domain.domain_id,
                 'service_account_id': self.service_account.service_account_id,
                 'data': self.secret_data,
                 'secret_type': 'CREDENTIALS'
                 }

        self.secret = self.secret_v1.Secret.create(param, metadata=(('token', self.owner_token),))
        print_message(self.secret, 'test_create_secret_with_service_account')
        self.secrets.append(self.secret)
        self.assertEqual(self.secret.service_account_id, self.service_account.service_account_id)

    def test_create_secret_with_project(self, project_id=None):
        if project_id is None:
            self._create_project_group()
            self._create_project(self.project_group.project_group_id)

        self.secret_data = {
            utils.random_string(): utils.random_string(),
            utils.random_string(): utils.random_string()
        }

        param = {'name': utils.random_string(),
                 'domain_id': self.domain.domain_id,
                 'project_id': self.project.project_id,
                 'data': self.secret_data,
                 'secret_type': 'CREDENTIALS'
                 }

        self.secret = self.secret_v1.Secret.create(param, metadata=(('token', self.owner_token),))
        print_message(self.secret, 'test_create_secret_with_project')
        self.secrets.append(self.secret)
        self.assertEqual(self.secret.project_id, self.project.project_id)

    def test_update_secret_name(self):
        self.test_create_secret()

        name = 'cred-test-000'
        param = {'secret_id': self.secret.secret_id,
                 'domain_id': self.domain.domain_id,
                 'name': name}

        self.secret = self.secret_v1.Secret.update(param, metadata=(('token', self.owner_token),))
        print_message(self.secret, 'test_update_secret_name')
        self.assertEqual(self.secret.name, name)

    def test_update_secret_tag(self):
        self.test_create_secret()

        tags = {
            'update_key': 'update_value'
        }
        param = {
            'secret_id': self.secret.secret_id,
            'domain_id': self.domain.domain_id,
            'tags': tags
        }

        self.secret = self.secret_v1.Secret.update(param, metadata=(('token', self.owner_token),))
        print_message(self.secret, 'test_update_secret_tag')
        secret_data = MessageToDict(self.secret, preserving_proto_field_name=True)
        self.assertEqual(secret_data['tags'], tags)

    def test_update_secret_project(self):
        self.test_create_secret_with_project()
        self._create_project(self.project_group.project_group_id)

        param = {'secret_id': self.secret.secret_id,
                 'domain_id': self.domain.domain_id,
                 'project_id': self.project.project_id}

        self.secret = self.secret_v1.Secret.update(param, metadata=(('token', self.owner_token),))
        print_message(self.secret, 'test_update_secret_project')
        self.assertEqual(self.secret.project_id, self.project.project_id)

    def test_release_secret_project(self):
        self.test_create_secret_with_project()

        param = {'secret_id': self.secret.secret_id,
                 'domain_id': self.domain.domain_id,
                 'release_project': True}

        self.secret = self.secret_v1.Secret.update(param, metadata=(('token', self.owner_token),))
        print_message(self.secret, 'test_release_secret_project')
        self.assertEqual(self.secret.project_id, '')

    def test_get_secret(self):
        self.test_create_secret()

        param = {
            'secret_id': self.secret.secret_id,
            'domain_id': self.domain.domain_id
        }
        secret = self.secret_v1.Secret.get(param, metadata=(('token', self.owner_token),))
        print_message(self.secret, 'test_get_secret')
        self.assertEqual(self.secret.name, secret.name)

    def test_list_secrets(self):
        self.test_create_secret()
        self.test_create_secret()
        self.test_create_secret()

        param = {
            'query': {
                'filter': [
                    {'k': 'name', 'v': self.secret.name, 'o': 'eq'}
                ]
            },
            'domain_id': self.domain.domain_id
        }

        result = self.secret_v1.Secret.list(param, metadata=(('token', self.owner_token),))
        print_message(result, 'test_list_secrets')
        self.assertEqual(result.total_count, 1)

    def test_list_secrets_include_secret_group(self):
        self.test_create_secret()
        self.test_create_secret()
        self.test_create_secret()
        self.test_create_secret()
        self.test_create_secret()

        secrets = map(lambda secret: secret.secret_id, self.secrets)

        self._create_secret_group(secrets)

        param = {
            'query': {
                'filter': [
                    {'k': 'name', 'v': self.secret.name, 'o': 'eq'}
                ]
            },
            'include_secret_group': True,
            'domain_id': self.domain.domain_id
        }

        result = self.secret_v1.Secret.list(param, metadata=(('token', self.owner_token),))
        print_message(result, 'test_list_secrets_include_secret_group')
        self.assertEqual(result.total_count, 1)

    def test_list_secrets_secret_group_id(self):
        self.test_create_secret()
        self.test_create_secret()
        self.test_create_secret()
        self.test_create_secret()
        self.test_create_secret()

        secrets = list(map(lambda secret: secret.secret_id, self.secrets))
        secrets.remove(self.secret.secret_id)

        self._create_secret_group(secrets)

        param = {
            'query': {},
            'secret_group_id': self.secret_group.secret_group_id,
            'domain_id': self.domain.domain_id
        }

        result = self.secret_v1.Secret.list(param, metadata=(('token', self.owner_token),))

        self.assertEqual(result.total_count, 4)

    def test_update_secret_data(self):
        self.test_create_secret()

        update_secret_data = {
            utils.random_string(): utils.random_string(),
            utils.random_string(): utils.random_string()
        }

        param = {
            'secret_id': self.secret.secret_id,
            'data': update_secret_data,
            'domain_id': self.domain.domain_id
        }

        self.secret_v1.Secret.update_data(param, metadata=(('token', self.owner_token),))

        param = {
            'secret_id': self.secret.secret_id,
            'domain_id': self.domain.domain_id
        }
        result = self.secret_v1.Secret.get_data(param, metadata=(('token', self.owner_token),))
        self.assertEqual(MessageToDict(result.data), update_secret_data)

    def test_get_secret_data(self):
        self.test_create_secret()

        param = {
            'secret_id': self.secret.secret_id,
            'domain_id': self.domain.domain_id
        }
        result = self.secret_v1.Secret.get_data(param, metadata=(('token', self.owner_token),))

        print_message(result, 'test_get_secret_data')

        self.assertEqual(MessageToDict(result.data), self.secret_data)

    def test_list_secrets_by_name(self):
        name = 'song-test'
        self.test_create_secret(name=name)

        param = {
            'name': name,
            'secret_id': self.secret.secret_id,
            'domain_id': self.domain.domain_id
        }
        secrets = self.secret_v1.Secret.list(param, metadata=(('token', self.owner_token),))

        self.assertEqual(secrets.total_count, 1)

    def test_stat_secret(self):
        self.test_list_secrets()

        params = {
            'domain_id': self.domain.domain_id,
            'query': {
                'aggregate': [{
                    'group': {
                        'keys': [{
                            'key': 'secret_id',
                            'name': 'Id'
                        }],
                        'fields': [{
                            'operator': 'count',
                            'name': 'Count'
                        }]
                    }
                }, {
                    'sort': {
                        'key': 'Count',
                        'desc': True
                    }
                }]
            }
        }

        result = self.secret_v1.Secret.stat(
            params, metadata=(('token', self.owner_token),))

        self._print_data(result, 'test_stat_secret')

    def test_stat_secret_distinct(self):
        self.test_list_secrets()

        params = {
            'domain_id': self.domain.domain_id,
            'query': {
                'distinct': 'secret_id',
                'page': {
                    'start': 2,
                    'limit': 1
                }
            }
        }

        result = self.secret_v1.Secret.stat(
            params, metadata=(('token', self.owner_token),))

        self._print_data(result, 'test_stat_secret_distinct')

    def _create_secret_group(self, secrets=[]):
        name = utils.random_string()
        param = {
            'name': name,
            'domain_id': self.domain.domain_id
        }

        self.secret_group = self.secret_v1.SecretGroup.create(param, metadata=(('token', self.owner_token),))

        if secrets:
            for secret_id in secrets:
                self._add_secret_to_secret_group(secret_id)

        self.secret_groups.append(self.secret_group)

    def _add_secret_to_secret_group(self, secret_id):
        result = self.secret_v1.SecretGroup.add_secret({
            'secret_group_id': self.secret_group.secret_group_id,
            'secret_id': secret_id,
            'domain_id': self.domain.domain_id
        }, metadata=(('token', self.owner_token),))

        print_message(result, '_create_secret_group.add_secret')


if __name__ == "__main__":
    unittest.main(testRunner=RichTestRunner)
