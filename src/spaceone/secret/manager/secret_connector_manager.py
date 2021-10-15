# -*- coding: utf-8 -*-

import logging

from spaceone.core import config
from spaceone.core.manager import BaseManager
from spaceone.secret.connector.aws_secret_manager_connector import AWSSecretManagerConnector
from spaceone.secret.connector.vault_connector import VaultConnector
from spaceone.secret.connector.consul_connector import ConsulConnector
from spaceone.secret.error import *

_LOGGER = logging.getLogger(__name__)


class SecretConnectorManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        connector = config.get_global('CONNECTORS')
        backend = config.get_global('BACKEND', 'AWSSecretManagerConnector')
        try:
            _LOGGER.debug(f'[SecretConnectorManager] Create {backend}')
            self.secret_conn = self.locator.get_connector(backend)
        except Exception as e:
            _LOGGER.error(f'[SecretConnectorManager] not defined backend {backend}')
            raise ERROR_DEFINE_SECRET_BACKEND(backend=backend)

    def create_secret(self, secret_id, data):
        def _rollback(secret_id):
            _LOGGER.info(f'[ROLLBACK] Delete secret data in secret store : {secret_id}')
            self.secret_conn.delete_secret(secret_id)

        response = self.secret_conn.create_secret(secret_id, data)
        self.transaction.add_rollback(_rollback, secret_id)

    def update_secret(self, secret_id, data):
        self.secret_conn.update_secret(secret_id, data)

    def delete_secret(self, secret_id):
        self.secret_conn.delete_secret(secret_id)

    def get_secret(self, secret_id):
        return self.secret_conn.get_secret(secret_id)
