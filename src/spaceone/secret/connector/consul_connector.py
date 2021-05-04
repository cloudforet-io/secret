# -*- coding: utf-8 -*-

import logging
import json
import consul

from spaceone.core.error import *
from spaceone.core.connector import BaseConnector

__all__ = ['ConsulConnector']
_LOGGER = logging.getLogger(__name__)


class ConsulConnector(BaseConnector):
    """ Consul Backend
    """
    def __init__(self, transaction, config):
        super().__init__(transaction, config)

        self.config = self._validate_config(config)

        # No configuration
        if self.config == {}:
            raise ERROR_CONNECTOR_CONFIGURATION(backend='ConsulConnector')

        # Create client
        self.client = consul.Consul(**self.config)

    def _validate_config(self, config):
        """
        Parameter for Consul
        - host, port=8500, token=None, scheme=http, consistency=default, dc=None, verify=True, cert=None
        """
        options = ['host', 'port', 'token', 'scheme', 'consistency', 'dc', 'verify', 'cert']
        result = {}
        for item in options:
            value = config.get(item, None)
            if value:
                result[item] = value
        return result

    @staticmethod
    def _response(response):
        # TODO: error check
        if isinstance(response, dict):
            return True

        return False

    @staticmethod
    def _response_value(response):
        index, data = response
        # TODO: error check
        if 'Value' not in data:
            return False
        value = data['Value'].decode('ascii')
        secret = json.loads(value)
        print("##################")
        print(secret)
        print("-----------------")
        name = secret.get("Name", None)
        secret_string = secret.get("SecretString", None)
        if name == None or secret_string == None:
            _LOGGER.error(f'[_response_value] {secret}')
        return json.loads( secret_string)

    def create_secret(self, secret_id, data):
        secret_params = {
            'Name': secret_id,
            'SecretString': json.dumps(data),
        }
        return self._response(self.client.kv.put(secret_id, json.dumps(secret_params)))

    def delete_secret(self, secret_id):
        response = self.client.kv.delete(secret_id)
        return self._response(response)

    def update_secret(self, secret_id, data):
        self.delete_secret(secret_id)
        response = self.create_secret(secret_id, data)

        return self._response(response)

    def get_secret(self, secret_id):
        return self._response_value(self.client.kv.get(secret_id))
