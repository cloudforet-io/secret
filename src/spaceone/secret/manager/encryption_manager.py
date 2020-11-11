import base64
import json
import logging
import os
import secrets
from typing import NewType, TypedDict, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from spaceone.core import config
from spaceone.core.manager import BaseManager

import test.factories.secret
from src.spaceone.secret.model.secret_model import Secret

_LOGGER = logging.getLogger(__name__)


class EnvelopeEncryptionData(TypedDict):
    encrypt_data: str
    nonce: str
    encrypt_data_key: str


EncryptContext = NewType('EncryptContext', dict)


class EncryptionManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        connector = config.get_global('CONNECTORS')
        kms_config = connector.get('AWSKMSConnector')
        if kms_config:
            _LOGGER.debug(f'[EncryptionManager] Create AWSKMSConnector')
            self.secret_conn = self.locator.get_connector('AWSKMSConnector')
        else:
            _LOGGER.error('Unsupported Connector')

    def get_encrypt_context_by_vo(self, secret_vo: Secret):
        return {
            "domain_id": secret_vo.domain_id,
            "secret_id": secret_vo.secret_id,
            "service": "secret",
            "token": secrets.token_urlsafe(30),
        }

    def _dict_to_b64(self, data: dict):
        return base64.b64encode(json.dumps(data).encode())

    def _b64_to_dict(self, data: Union[str,bytes]):
        _data = data if isinstance(data, bytes) else data.encode()
        return json.loads(base64.b64decode(_data).decode())

    def _make_EnvelopeEncryptionData(self, encrypt_data, nonce, encrypt_data_key):
        return EnvelopeEncryptionData(
            encrypt_data=base64.b64encode(encrypt_data).decode(),
            nonce=base64.b64encode(nonce).decode(),
            encrypt_data_key=base64.b64encode(encrypt_data_key).decode(),
        )

    def encrypt(self, secret_data, encrypt_context) -> (EnvelopeEncryptionData, EncryptContext):
        secret_data_b64 = self._dict_to_b64(secret_data)
        encrypt_context_b64 = self._dict_to_b64(encrypt_context)
        nonce = os.urandom(12)
        data_key, encrypt_data_key = test.factories.secret.generate_data_key(
            encrypt_context)  # data_key spec must be AES_128

        aesgcm = AESGCM(data_key)
        encrypt_data = aesgcm.encrypt(nonce, secret_data_b64, encrypt_context_b64)
        del data_key
        env_encrypt_data = self._make_EnvelopeEncryptionData(encrypt_data, nonce, encrypt_data_key)

        return env_encrypt_data, encrypt_context

    def encrypt_by_vo(self, secret_data, secret_vo):
        encrypt_context = self.get_encrypt_context_by_vo(secret_vo)
        return self.encrypt(secret_data, encrypt_context)

    def decrypt_by_vo(self, encrypt_data, secret_vo: Secret):
        return self.decrypt(encrypt_data, secret_vo.encrypt_context)

    def decrypt(self, encrypt_data: EnvelopeEncryptionData, encrypt_context: dict):
        encrypt_secret_data = base64.b64decode(encrypt_data['encrypt_data'].encode())
        encrypt_data_key = base64.b64decode(encrypt_data['encrypt_data_key'].encode())
        nonce = base64.b64decode(encrypt_data['nonce'].encode())
        encrypt_context_b64 = self._dict_to_b64(encrypt_context)

        data_key = self.secret_conn.decrypt_data_key(encrypt_data_key, encrypt_context)
        aesgcm = AESGCM(data_key)
        secret_data = aesgcm.decrypt(nonce, encrypt_secret_data, encrypt_context_b64)

        return self._b64_to_dict(secret_data)
