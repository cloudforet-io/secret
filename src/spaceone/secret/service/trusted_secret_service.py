import logging

from spaceone.core.service import *
from spaceone.secret.error.custom import *
from spaceone.secret.manager.identity_manager import IdentityManager
from spaceone.secret.manager.secret_manager import SecretManager
from spaceone.secret.manager.trusted_secret_manager import TrustedSecretManager
from spaceone.secret.manager.secret_connector_manager import SecretConnectorManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class TrustedSecretService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trusted_secret_mgr: TrustedSecretManager = self.locator.get_manager('TrustedSecretManager')

    @transaction(append_meta={
        'authorization.scope': 'DOMAIN'
    })
    @check_required(['name', 'data', 'domain_id'])
    def create(self, params):
        """ Create trusted secret

        Args:
            params (dict): {
                'name': 'str',
                'data': 'dict',
                'tags': 'dict',
                'schema': 'str',
                'service_account_id': 'str',
                'domain_id': 'str
            }

        Returns:
            trusted_secret_vo
        """
        domain_id = params['domain_id']

        if 'service_account_id' in params:
            service_account_info = self._check_service_accounts(params, domain_id)
            params['provider'] = service_account_info.get('provider')

        trusted_secret_vo = self.trusted_secret_mgr.create_trusted_secret(params)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager('SecretConnectorManager')
        secret_conn_mgr.create_secret(trusted_secret_vo.trusted_secret_id, params['data'])

        return trusted_secret_vo

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['trusted_secret_id', 'domain_id'])
    def update(self, params):
        """ Update trusted secret

        Args:
            params (dict): {
                'trusted_secret_id': 'str',
                'name': 'str' ,
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            trusted_secret_vo
        """

        domain_id = params['domain_id']
        trusted_secret_id = params['trusted_secret_id']
        trusted_secret_vo = self.trusted_secret_mgr.get_trusted_secret(trusted_secret_id, domain_id)
        update_trusted_secret_vo = self.trusted_secret_mgr.update_trusted_secret_by_vo(params, trusted_secret_vo)

        return update_trusted_secret_vo

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['trusted_secret_id', 'domain_id'])
    def delete(self, params):
        """ Delete trusted secret

        Args:
            params (dict): {
                'trusted_secret_id': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """
        secret_mgr: SecretManager = self.locator.get_manager('SecretManager')

        domain_id = params['domain_id']
        trusted_secret_id = params['trusted_secret_id']
        trusted_secret_vo = self.trusted_secret_mgr.get_trusted_secret(trusted_secret_id, domain_id)

        self._check_related_secret(secret_mgr, trusted_secret_id, domain_id)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager('SecretConnectorManager')
        secret_conn_mgr.delete_secret(trusted_secret_id)

        self.trusted_secret_mgr.delete_trusted_secret_by_vo(trusted_secret_vo)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['trusted_secret_id', 'data', 'domain_id'])
    def update_data(self, params):
        """ Update trusted secret data through backend Secret service

        Args:
            params (dict): {
                'trusted_secret_id': 'str',
                'data': 'dict',
                'schema': 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """
        domain_id = params['domain_id']
        trusted_secret_id = params['trusted_secret_id']
        data = params['data']

        trusted_secret_vo = self.trusted_secret_mgr.get_trusted_secret(trusted_secret_id, domain_id)
        self.trusted_secret_mgr.update_trusted_secret_by_vo(params, trusted_secret_vo)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager('SecretConnectorManager')
        secret_conn_mgr.update_secret(trusted_secret_id, data)

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['trusted_secret_id', 'domain_id'])
    def get(self, params):
        """ Get trusted secret

        Args:
            params (dict): {
                'trusted_secret_id': 'str',
                'domain_id': 'str',
                'only': 'list'
            }

        Returns:
            trusted_secret_vo
        """

        return self.trusted_secret_mgr.get_trusted_secret(params['trusted_secret_id'],
                                                          params['domain_id'],
                                                          params.get('only'))

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['domain_id'])
    @append_query_filter(['trusted_secret_id', 'name', 'schema', 'provider',
                          'service_account_id', 'domain_id'])
    @append_keyword_filter(['trusted_secret_id', 'name', 'schema', 'provider'])
    def list(self, params):
        """ List trusted secrets

        Args:
            params (dict): {
                'trusted_secret_id': 'str',
                'name': 'str',
                'schema': 'str',
                'provider': 'str',
                'service_account_id': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)'
            }

        Returns:
            results (list)
            total_count (int)
        """

        query = params.get('query', {})
        trusted_secret_vos, total_count = self.trusted_secret_mgr.list_trusted_secrets(query)

        return trusted_secret_vos, total_count

    @transaction(append_meta={'authorization.scope': 'DOMAIN'})
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id'])
    @append_keyword_filter(['trusted_secret_id', 'name', 'schema', 'provider'])
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

    def _check_service_accounts(self, params, domain_id):
        query = {
            'filter': [
                {'k': 'service_account_id', 'v': params['service_account_id'], 'o': 'eq'},
                {'k': 'service_account_type', 'v': 'TRUSTED', 'o': 'eq'},
            ]
        }
        identity_mgr: IdentityManager = self.locator.get_manager('IdentityManager')
        response = identity_mgr.list_service_accounts(query, domain_id)

        _LOGGER.debug(f'[_check_service_accounts] list_service_accounts response: {response}')

        if response.get('total_count', 0) == 0:
            raise ERROR_NOT_EXIST_TRUST_SERVICE_ACCOUNT()
        else:
            return response['results'][0]

    @staticmethod
    def _check_related_secret(secret_mgr, trusted_secret_id, domain_id):
        secret_query = {
            'filter': [
                {'k': 'trusted_secret_id', 'v': trusted_secret_id, 'o': 'eq'},
                {'k': 'domain_id', 'v': domain_id, 'o': 'eq'}
            ]
        }
        secret_vos, secret_total_count = secret_mgr.list_secrets(secret_query)
        if secret_total_count > 0:
            raise ERROR_EXIST_RELATED_SECRET(secret_id=secret_vos[0].secret_id)
