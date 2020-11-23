import base64
import json
import os
from datetime import datetime
from functools import partial
import collections
import boto3
import factory
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from factory import fuzzy
from spaceone.core import config, utils
from spaceone.secret.manager.encryption_manager import EnvelopeEncryptionData
from spaceone.secret.model import Secret


def dict_to_b64(data: dict):
    return base64.b64encode(json.dumps(data).encode())


def generate_data_key():
    kms_config = config.get_global('CONNECTORS', {}).get('AWSKMSConnector', {})
    client = boto3.client('kms', region_name=kms_config.get("region_name"))
    result = client.generate_data_key(
        KeyId=kms_config.get('kms_key_id'),
        KeySpec='AES_256',
    )
    return result['Plaintext'], result['CiphertextBlob']


def encrypt_data(encrypt_context, secret_data):
    secret_data_b64 = dict_to_b64(secret_data)
    encrypt_context_b64 = dict_to_b64(encrypt_context)
    nonce = os.urandom(12)

    data_key, encrypt_data_key = generate_data_key()  # data_key spec must be AES_256
    print({
        "data_key": data_key,
        "nonce": nonce,
        "encrypt_context": encrypt_context,
        "secret_data": secret_data
    })
    print(data_key, secret_data)
    aesgcm = AESGCM(data_key)
    encrypt_data = aesgcm.encrypt(nonce, secret_data_b64, encrypt_context_b64)
    del data_key
    encrypt_data_key = base64.b64encode(encrypt_data_key).decode()
    return EnvelopeEncryptionData(
        encrypt_data=base64.b64encode(encrypt_data).decode(),
        nonce=base64.b64encode(nonce).decode(),
    ), encrypt_data_key


class SecretFactory(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = Secret

    secret_id = factory.LazyFunction(partial(utils.generate_id, 'secret'))
    name = fuzzy.FuzzyText()
    schema = None
    encrypted = False
    provider = None
    service_account_id = None
    secret_type = fuzzy.FuzzyChoice(['CREDENTIALS'])
    domain_id = factory.LazyFunction(partial(utils.generate_id, 'domain'))
    created_at = factory.LazyFunction(datetime.now)
    encrypt_data_key = None

    @factory.post_generation
    def secret_data(obj: Secret, create, extracted=None, **kwargs):
        if not create:
            return
        secret_data = extracted or {
            utils.random_string(): utils.random_string(),
            utils.random_string(): utils.random_string()
        }
        if obj.encrypted:
            secret_data, encrypt_data_key = encrypt_data(get_encrypt_context(obj), secret_data)
            obj.encrypt_data_key = encrypt_data_key
            obj.encrypt_type = 'AWS_KMS'
            obj.save()

        region = config.get_global('CONNECTORS', {}).get('AWSSecretManagerConnector', {}).get("region_name")

        client = boto3.client('secretsmanager', region_name=region)
        result = client.create_secret(
            Name=obj.secret_id,
            SecretString=json.dumps(secret_data),
        )
        # print(result)


def get_encrypt_context(obj):
    context = collections.OrderedDict()
    context['domain_id'] = obj.domain_id
    context['secret_id'] = obj.secret_id
    return context


class EncryptSecretFactory(SecretFactory):
    class Meta:
        model = Secret

    encrypted = fuzzy.FuzzyChoice([True, False])
    service_account_id = None
    encrypt_data_key = None

