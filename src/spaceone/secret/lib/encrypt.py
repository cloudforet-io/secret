import base64
import json
from functools import partial
from typing import Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

import boto3

"""
Secrete Service Decrypt Example

>>> request = GetSecretRequest(secret_id=secret_id, domain_id=domain_id)
>>> result = grpc_secret_stub.get_data(request)
>>> result = MessageToDict(result, preserving_proto_field_name=True)
>>> result
{
   "encrypted":True,
   "encrypted_data":"xxxxxx",
   "encrypt_options": {
        "nonce":"xxxxx_b64",
        "encrypt_type":"AWS_KMS",
        "encrypt_context":"xxxxx_b64",
        "encrypt_data_key":"xxxxx_b64",
   },
}
>>> region_name = 'xxx'
>>> options = result['encrypt_options']
>>> secret_data = aws_kms_decrypt(
>>>                        options['encrypt_data_key'],
>>>                        options['nonce'],
>>>                        result['encrypt_secret_data'], # result!! not options
>>>                        options['encrypt_context'],
>>>                        region_name=region_name
>>>                        )

"""


def _b64_to_dict(data: Union[str, bytes]):
    _data = data if isinstance(data, bytes) else data.encode()
    return json.loads(base64.b64decode(_data).decode())


def _aws_kms_decrypt_data_key(encrypt_data_key: bytes, kms_client=None,region_name=None):
    kms = kms_client or boto3.client('kms',region_name=region_name)
    response = kms.decrypt(CiphertextBlob=encrypt_data_key)
    return response['Plaintext']


def aws_kms_decrypt(encrypt_data_key: str, nonce: str, encrypt_secret_data: str, encrypt_context: str, kms_client=None,region_name=None):
    encrypt_secret_data = base64.b64decode(encrypt_secret_data.encode())
    encrypt_data_key = base64.b64decode(encrypt_data_key.encode())
    encrypt_context = encrypt_context.encode()
    nonce = base64.b64decode(nonce.encode())

    data_key = _aws_kms_decrypt_data_key(encrypt_data_key,kms_client=kms_client,region_name=region_name)

    aesgcm = AESGCM(data_key)
    secret_data = aesgcm.decrypt(nonce, encrypt_secret_data, encrypt_context)
    return _b64_to_dict(secret_data)
