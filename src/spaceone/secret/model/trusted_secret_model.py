import logging
from mongoengine import *
from spaceone.core.model.mongo_model import MongoModel

_LOGGER = logging.getLogger(__name__)


class TrustedSecret(MongoModel):
    trusted_secret_id = StringField(max_length=40, generate_id='trusted-secret', unique=True)
    name = StringField(max_length=255, unique_with='domain_id')
    tags = DictField()
    schema = StringField(max_length=40, null=True, default=None)
    provider = StringField(max_length=40, null=True, default=None)
    encrypted = BooleanField(default=False)
    encrypt_options = DictField()
    service_account_id = StringField(max_length=40, null=True, default=None)
    domain_id = StringField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        'updatable_fields': [
            'name',
            'tags',
            'schema',
            'encrypted',
            'encrypt_options'
        ],
        'minimal_fields': [
            'trusted_secret_id',
            'name',
            'provider',
            'encrypted'
        ],
        'change_query_keys': {},
        'ordering': [
            'name'
        ],
        'indexes': [
            'schema',
            'provider',
            'encrypted',
            'service_account_id',
            'domain_id',
        ]
    }
