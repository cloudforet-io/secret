# -*- coding: utf-8 -*-

import logging
import json
import hvac

from spaceone.core.error import *
from spaceone.core.connector import BaseConnector

__all__ = ['VaultConnector']
_LOGGER = logging.getLogger(__name__)


class VaultConnector(BaseConnector):
    """ Vault backend is for develop use
    """
    def __init__(self, transaction, config):
        super().__init__(transaction, config)

        vault_url = config.get('url')
        token = config.get('token')
        if vault_url and token:
            self.client = hvac.Client(url=vault_url)
            self.client.token = token
        else:
            raise ERROR_CONNECTOR_CONFIGURATION(backend='VaultConnector')

    @staticmethod
    def _response(response):
        # TODO: error check
        if isinstance(response, dict):
            return True

        return False

    @staticmethod
    def _response_value(response):
        # TODO: error check
        if 'data' not in response:
            return False
        data = response['data']
        if 'data' not in data:
            return False
        data = data['data']
        data_string = data.get('SecretString', False)
        if data_string:
            return json.loads(data_string)

        return data_string

    def create_secret(self, secret_id, data):
        secret_params = {
            'Name': secret_id,
            'SecretString': json.dumps(data),
        }

        return self._response(self.client.secrets.kv.v2.create_or_update_secret(path=secret_id, secret=secret_params))

    def delete_secret(self, secret_id):
        response = self.client.secrets.kv.delete_metadata_and_all_versions(secret_id)
        return self._response(response)

    def get_secret(self, secret_id):
        return self._response_value(self.client.secrets.kv.read_secret_version(path=secret_id))
