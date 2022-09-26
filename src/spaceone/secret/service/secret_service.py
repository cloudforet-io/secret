import logging

from spaceone.core.service import *
from spaceone.secret.error.custom import *
from spaceone.secret.manager.identity_manager import IdentityManager
from spaceone.secret.manager.secret_manager import SecretManager
from spaceone.secret.model.secret_model import Secret
from spaceone.secret.manager.trusted_secret_manager import TrustedSecretManager
from spaceone.secret.manager.secret_connector_manager import SecretConnectorManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler(exclude=['get_data'])
@mutation_handler
@event_handler
class SecretService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_mgr: SecretManager = self.locator.get_manager('SecretManager')

    @transaction(append_meta={
        'authorization.scope': 'PROJECT',
        'authorization.require_project_id': True
    })
    @check_required(['name', 'data', 'secret_type', 'domain_id'])
    def create(self, params):
        """ Create secret

        Args:
            params (dict): {
                'name': 'str',
                'data': 'dict',
                'secret_type': 'str',
                'tags': 'dict',
                'schema': 'str',
                'encrypted': 'bool',
                'encrypt_options': 'dict',
                'service_account_id': 'str',
                'project_id': 'str',
                'trusted_secret_id': 'str',
                'domain_id': 'str
            }

        Returns:
            secret_vo
        """

        domain_id = params['domain_id']

        if 'service_account_id' in params:
            service_account_info = self._get_service_account(params['service_account_id'], domain_id)
            params['provider'] = service_account_info.get('provider')
            params['project_id'] = service_account_info.get('project_info', {}).get('project_id')
        else:
            if 'project_id' in params:
                self._check_project(params['project_id'], domain_id)

        if 'trusted_secret_id' in params:
            trusted_secret_mgr = self.locator.get_manager('TrustedSecretManager')
            trusted_secret_mgr.get_trusted_secret(params['trusted_secret_id'], domain_id)

        secret_vo = self.secret_mgr.create_secret(params)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager('SecretConnectorManager')
        secret_conn_mgr.create_secret(secret_vo.secret_id, params['data'])

        return secret_vo

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['secret_id', 'domain_id'])
    def update(self, params):
        """ Update secret

        Args:
            params (dict): {
                'secret_id': 'str',
                'name': 'str' ,
                'tags': 'dict',
                'project_id': 'str',
                'release_project': 'bool',
                'domain_id': 'str'
            }

        Returns:
            secret_vo
        """

        domain_id = params['domain_id']
        secret_id = params['secret_id']
        project_id = params.get('project_id')
        release_project = params.get('release_project', False)

        secret_vo = self.secret_mgr.get_secret(secret_id, domain_id)

        if release_project:
            params['project_id'] = None
        else:
            if project_id:
                self._check_project(project_id, domain_id)

        secret_vo = self.secret_mgr.update_secret_by_vo(params, secret_vo)

        return secret_vo

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['secret_id', 'domain_id'])
    def delete(self, params):
        """ Delete secret

        Args:
            params (dict): {
                'secret_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """

        domain_id = params['domain_id']
        secret_id = params['secret_id']

        secret_vo = self.secret_mgr.get_secret(secret_id, domain_id)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager('SecretConnectorManager')
        secret_conn_mgr.delete_secret(secret_id)

        self.secret_mgr.delete_secret_by_vo(secret_vo)

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['secret_id', 'data', 'domain_id'])
    def update_data(self, params):
        """ Update secret data through backend Secret service

        Args:
            params (dict): {
                'secret_id': 'str',
                'data': 'dict',
                'schema': 'str',
                'encrypted': 'bool',
                'encrypt_options': 'dict',
                'domain_id': 'str'
            }

        Returns:
            secret_data (dict)
        """
        domain_id = params['domain_id']
        secret_id = params['secret_id']
        data = params['data']

        secret_vo = self.secret_mgr.get_secret(secret_id, domain_id)
        self.secret_mgr.update_secret_by_vo(params, secret_vo)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager('SecretConnectorManager')
        secret_conn_mgr.update_secret(secret_id, data)

    @transaction(append_meta={'authorization.scope': 'SYSTEM'})
    @check_required(['secret_id', 'domain_id'])
    def get_data(self, params):
        """ Get secret data through backend Secret service

        Args:
            params (dict): {
                'secret_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            secret_data (dict)
        """

        secret_id = params['secret_id']
        domain_id = params['domain_id']

        secret_vo: Secret = self.secret_mgr.get_secret(secret_id, domain_id)
        secret_data = self._get_secret_data(secret_id)
        encrypt_options = secret_vo.encrypt_options

        if secret_vo.trusted_secret_id:
            trusted_secret_mgr: TrustedSecretManager = self.locator.get_manager('TrustedSecretManager')
            trusted_secret_vo = trusted_secret_mgr.get_trusted_secret(trusted_secret_id=secret_vo.trusted_secret_id,
                                                                      domain_id=domain_id)

            self._check_validation_trusted_secret(secret_vo, trusted_secret_vo)

            trusted_secret_data = self._get_secret_data(trusted_secret_vo.trusted_secret_id)
            trusted_secret_encrypt_options = trusted_secret_vo.encrypt_options

            if secret_vo.encrypted and trusted_secret_vo.encrypted:
                secret_data['trusted_encrypted_data'] = trusted_secret_data['encrypted_data']

                encrypt_options.update({
                    'trusted_encrypted_data_key': trusted_secret_encrypt_options.get('encrypted_data_key')
                })
            elif secret_vo.encrypted is False and trusted_secret_vo.encrypted is False:
                # Merge secret data & trusted secret data
                trusted_secret_data.update(secret_data)
                secret_data = trusted_secret_data

        return {
            'encrypted': secret_vo.encrypted,
            'encrypt_options': encrypt_options,
            'data': secret_data
        }

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['secret_id', 'domain_id'])
    def get(self, params):
        """ Get secret

        Args:
            params (dict): {
                'secret_id': 'str',
                'domain_id': 'str',
                'only': 'list'
            }

        Returns:
            secret_vo
        """

        return self.secret_mgr.get_secret(params['secret_id'], params['domain_id'], params.get('only'))

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['domain_id'])
    @append_query_filter(['secret_id', 'name', 'secret_type', 'schema', 'provider',
                          'service_account_id', 'trusted_secret_id', 'domain_id', 'user_projects'])
    @append_keyword_filter(['secret_id', 'name', 'schema', 'provider'])
    def list(self, params):
        """ List secrets

        Args:
            params (dict): {
                'secret_id': 'str',
                'name': 'str',
                'secret_type': 'str',
                'schema': 'str',
                'provider': 'str',
                'service_account_id': 'str',
                'trusted_secret_id': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)',
                'user_projects': 'list', // from meta
            }

        Returns:
            results (list)
            total_count (int)
        """

        query = params.get('query', {})
        include_secret_group = params.get('include_secret_group', False)
        secret_vos, total_count = self.secret_mgr.list_secrets(query)

        if include_secret_group:
            secret_vos = self.secret_mgr.get_related_secret_groups(secret_vos)

        return secret_vos, total_count

    @transaction(append_meta={'authorization.scope': 'PROJECT'})
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id'])
    @append_keyword_filter(['secret_id', 'name', 'schema', 'provider'])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',
                'user_projects': 'list', // from meta
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get('query', {})
        return self.secret_mgr.stat_secrets(query)

    def _get_secret_data(self, secret_id):
        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager('SecretConnectorManager')
        return secret_conn_mgr.get_secret(secret_id)

    def _get_service_account(self, service_account_id, domain_id):
        identity_mgr: IdentityManager = self.locator.get_manager('IdentityManager')
        return identity_mgr.get_service_account(service_account_id, domain_id)

    def _check_project(self, project_id, domain_id):
        identity_mgr: IdentityManager = self.locator.get_manager('IdentityManager')
        identity_mgr.get_project(project_id, domain_id)

        return True

    @staticmethod
    def _check_validation_trusted_secret(secret_vo, trusted_secret_vo):
        if secret_vo.encrypted != trusted_secret_vo.encrypted:
            raise ERROR_DIFF_SECRET_AND_TRUSTED_SECRET_ENCRYPTED()

        if secret_vo.encrypted and trusted_secret_vo.encrypted:
            secret_encrypt_options = secret_vo.encrypt_options
            trusted_secret_encrypt_options = trusted_secret_vo.encrypt_options

            secret_encrypt_algorithm = secret_encrypt_options.get('encrypt_algorithm')
            trusted_secret_encrypt_algorithm = trusted_secret_encrypt_options.get('encrypt_algorithm')

            if secret_encrypt_algorithm and trusted_secret_encrypt_algorithm and \
                    secret_encrypt_algorithm == trusted_secret_encrypt_algorithm:
                return True
            else:
                raise ERROR_DIFF_SECRET_AND_TRUSTED_SECRET_ENCRYPTED()

        return True
