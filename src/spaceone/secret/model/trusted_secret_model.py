import logging
from mongoengine import *
from spaceone.core.model.mongo_model import MongoModel

_LOGGER = logging.getLogger(__name__)


class TrustedSecret(MongoModel):
    trusted_secret_id = StringField(
        max_length=40, generate_id="trusted-secret", unique=True
    )
    name = StringField(max_length=255)
    schema_id = StringField(max_length=40, null=True, default=None)
    provider = StringField(max_length=40, null=True, default=None)
    tags = DictField()
    encrypted = BooleanField(default=False)
    encrypt_options = DictField()
    trusted_account_id = StringField(max_length=40, null=True, default=None)
    resource_group = StringField(max_length=40, choices=("DOMAIN", "WORKSPACE"))
    workspace_id = StringField(max_length=40)
    domain_id = StringField(max_length=40)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        "updatable_fields": [
            "name",
            "schema_id",
            "tags",
            "encrypted",
            "encrypt_options",
        ],
        "minimal_fields": ["trusted_secret_id", "name", "schema_id", "provider"],
        "ordering": ["name"],
        "indexes": [
            "name",
            "schema_id",
            "provider",
            "trusted_account_id",
            "resource_group",
            "workspace_id",
            "domain_id",
        ],
    }
