import logging
import json
import etcd3
from spaceone.core.connector import BaseConnector


__all__ = ['EtcdConnector']
_LOGGER = logging.getLogger(__name__)


class EtcdConnector(BaseConnector):

    def __init__(self, transaction, config):
        super().__init__(transaction, config)
        self.client = etcd3.client(host=config.get('host'), port=config.get('port'))

    @staticmethod
    def _response_value(response):
        try:
            if response:
                data_bytes = response[0]

                if data_bytes:
                    return json.loads(data_bytes)

            return {}
        except Exception as e:
            _LOGGER.error(f'Response Error: {e}')
            return {}

    def create_secret(self, secret_id, data):
        self.client.put(secret_id, json.dumps(data))

    def delete_secret(self, secret_id):
        self.client.delete(secret_id)

    def update_secret(self, secret_id, data):
        self.delete_secret(secret_id)
        self.create_secret(secret_id, data)

    def get_secret(self, secret_id):
        return self._response_value(self.client.get(secret_id))
