import base64
import json
import logging
import os
from typing import NewType, TypedDict, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from spaceone.core import config
from spaceone.core.error import ERROR_CONNECTOR_CONFIGURATION
from spaceone.core.manager import BaseManager

from src.spaceone.secret.model.secret_model import Secret

_LOGGER = logging.getLogger(__name__)


class EnvelopeEncryptionData(TypedDict):
    encrypt_data: str
    nonce: str


EncryptDataKey = NewType('EncryptDataKey', str)

EncryptTypeConnector = {
    'AWS_KMS':"AWSKMSConnector"
}


class EncryptionManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        encrypt_type = config.get_global('ENCRYPT_TYPE',"AWS_KMS")
        if connector := EncryptTypeConnector.get(encrypt_type):
            _LOGGER.debug(f'[EncryptionManager] Create {connector}')
            self.secret_conn = self.locator.get_connector(connector)
        else:
            _LOGGER.error('Unsupported ENCRYPT_TYPE')
            raise ERROR_CONNECTOR_CONFIGURATION(backend='EncryptionManager')


    def get_encrypt_context_by_vo(self, secret_vo: Secret):
        return {
            "domain_id": secret_vo.domain_id,
            "secret_id": secret_vo.secret_id,
        }

    def _dict_to_b64(self, data: dict):
        return base64.b64encode(json.dumps(data).encode())

    def _b64_to_dict(self, data: Union[str, bytes]):
        _data = data if isinstance(data, bytes) else data.encode()
        return json.loads(base64.b64decode(_data).decode())

    def _make_EnvelopeEncryptionData(self, encrypt_data, nonce ):
        return EnvelopeEncryptionData(
            encrypt_data=base64.b64encode(encrypt_data).decode(),
            nonce=base64.b64encode(nonce).decode(),
        )

    def encrypt(self, secret_data, encrypt_context) -> (EnvelopeEncryptionData, EncryptDataKey):
        secret_data_b64 = self._dict_to_b64(secret_data)
        encrypt_context_b64 = self._dict_to_b64(encrypt_context)
        nonce = os.urandom(12)
        data_key, encrypt_data_key = self.secret_conn.generate_data_key()  # data_key spec must be AES_256

        aesgcm = AESGCM(data_key)
        encrypt_data = aesgcm.encrypt(nonce, secret_data_b64, encrypt_context_b64)
        del data_key

        envelope_encrypt_data = self._make_EnvelopeEncryptionData(encrypt_data, nonce )
        encrypt_data_key = base64.b64encode(encrypt_data_key).decode()
        return envelope_encrypt_data, encrypt_data_key

    def encrypt_by_vo(self, secret_data, secret_vo):
        encrypt_context = self.get_encrypt_context_by_vo(secret_vo)
        return self.encrypt(secret_data, encrypt_context)
