import logging
from mongoengine import *
from spaceone.core.model.mongo_model import MongoModel

_LOGGER = logging.getLogger(__name__)


class UserSecret(MongoModel):
    user_secret_id = StringField(max_length=40, generate_id="user-secret", unique=True)
    name = StringField(max_length=255)
    schema_id = StringField(max_length=40, null=True, default=None)
    provider = StringField(max_length=40, null=True, default=None)
    tags = DictField()
    encrypted = BooleanField(default=False)
    encrypt_options = DictField()
    user_id = StringField(max_length=255)
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
        "minimal_fields": ["user_secret_id", "name", "schema_id", "provider"],
        "ordering": ["name"],
        "indexes": [
            "name",
            "schema_id",
            "provider",
            "user_id",
            "domain_id",
        ],
    }
