# -*- coding: utf-8 -*-

import logging

from spaceone.core.service import *
from spaceone.secret.error.custom import *
from spaceone.secret.manager.secret_group_manager import SecretGroupManager
from spaceone.secret.manager.secret_manager import SecretManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@event_handler
class SecretGroupService(BaseService):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_group_mgr: SecretGroupManager = self.locator.get_manager('SecretGroupManager')

    @transaction
    @check_required(['name', 'domain_id'])
    def create(self, params):
        """ Create secret group

        Args:
            params (dict): {
                'name': 'str',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            secret_group_vo
        """

        return self.secret_group_mgr.create_secret_group(params)

    @transaction
    @check_required(['secret_group_id', 'domain_id'])
    def update(self, params):
        """ Update secret group

        Args:
            params (dict): {
                'secret_group_id' : 'str',
                'name': 'str',
                'tags': 'dict',
                'domain_id': 'str'
            }

        Returns:
            secret_group_vo
        """

        secret_group_vo = self.secret_group_mgr.get_secret_group(params['secret_group_id'],
                                                                 params['domain_id'])

        return self.secret_group_mgr.update_secret_group_by_vo(params, secret_group_vo)

    @transaction
    @check_required(['secret_group_id', 'domain_id'])
    def delete(self, params):
        """ Delete secret group

        Args:
            params (dict): {
                'secret_group_id' : 'str',
                'domain_id': 'str'
            }

        Returns:
            None
        """

        secret_group_vo = self.secret_group_mgr.get_secret_group(params['secret_group_id'],
                                                                 params['domain_id'])

        self.secret_group_mgr.delete_secret_group_by_vo(secret_group_vo)

    @transaction
    @check_required(['secret_group_id', 'secret_id', 'domain_id'])
    def add_secret(self, params):
        """ Add secret to secret group

        Args:
            params (dict): {
                'secret_group_id' : 'str',
                'secret_id: 'str',
                'domain_id': 'str'
            }

        Returns:
            secret_group_map_vo
        """
        secret_mgr: SecretManager = self.locator.get_manager('SecretManager')
        secret_group_id = params['secret_group_id']
        secret_id = params['secret_id']
        domain_id = params['domain_id']

        secret_group_vo = self.secret_group_mgr.get_secret_group(secret_group_id, domain_id)
        secret_vo = secret_mgr.get_secret(secret_id, domain_id)

        self._check_not_exist_secret_in_group(secret_group_vo, secret_vo)
        secret_group_map_vo = self.secret_group_mgr.add_secret(secret_group_vo, secret_vo)

        return secret_group_map_vo

    @transaction
    @check_required(['secret_group_id', 'secret_id', 'domain_id'])
    def remove_secret(self, params):
        """ Remove secret from secret group

        Args:
            params (dict): {
                'secret_group_id' : 'str',
                'secret_id: 'str',
                'domain_id': 'str'
            }

        Returns:
            secret_group_map_vo
        """
        secret_mgr: SecretManager = self.locator.get_manager('SecretManager')
        secret_group_id = params['secret_group_id']
        secret_id = params['secret_id']
        domain_id = params['domain_id']

        secret_group_vo = self.secret_group_mgr.get_secret_group(secret_group_id, domain_id)
        secret_vo = secret_mgr.get_secret(secret_id, domain_id)

        secret_group_map_vo = self._get_secret_group_map(secret_group_vo, secret_vo)
        self.secret_group_mgr.remove_secret(secret_group_vo, secret_group_map_vo)

    @transaction
    @check_required(['secret_group_id', 'domain_id'])
    def get(self, params):
        """ Get secret group

        Args:
            params (dict): {
                'secret_group_id': 'str',
                'domain_id': 'str',
                'only': 'list'
            }

        Returns:
            secret_group_vo

        """

        return self.secret_group_mgr.get_secret_group(params['secret_group_id'], params['domain_id'],
                                                      params.get('only'))

    @transaction
    @check_required(['domain_id'])
    @append_query_filter(['secret_group_id', 'name', 'secret_id', 'domain_id'])
    @append_keyword_filter(['secret_group_id', 'name'])
    def list(self, params):
        """ List secret groups

        Args:
            params (dict): {
                'secret_group_id': 'str',
                'name': 'str',
                'secret_id': 'str',
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.Query)'
            }

        Returns:
            results (list)
            total_count (int)
        """

        query = params.get('query', {})
        return self.secret_group_mgr.list_secret_groups(query)

    @transaction
    @check_required(['query', 'domain_id'])
    @append_query_filter(['domain_id'])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'domain_id': 'str',
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)'
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get('query', {})
        return self.secret_group_mgr.stat_secret_groups(query)

    def _check_not_exist_secret_in_group(self, secret_group_vo, secret_vo):
        secret_group_map_vos, total_count = self._list_secret_group_map(secret_group_vo, secret_vo)

        if total_count > 0:
            raise ERROR_ALREADY_EXIST_SECRET_IN_GROUP(secret_id=secret_vo.secret_id,
                                                      secret_group_id=secret_group_vo.secret_group_id)

    def _get_secret_group_map(self, secret_group_vo, secret_vo):
        secret_group_map_vos, total_count = self._list_secret_group_map(secret_group_vo, secret_vo)

        if total_count == 0:
            raise ERROR_NOT_EXIST_SECRET_IN_GROUP(secret_id=secret_vo.secret_id,
                                                  secret_group_id=secret_group_vo.secret_group_id)

        return secret_group_map_vos[0]

    def _list_secret_group_map(self, secret_group_vo, secret_vo):
        query = {
            'filter': [
                {'k': 'secret_group_id', 'v': secret_group_vo.secret_group_id, 'o': 'eq'},
                {'k': 'secret_id', 'v': secret_vo.secret_id, 'o': 'eq'}
            ]
        }

        return self.secret_group_mgr.list_secret_group_maps(query)
