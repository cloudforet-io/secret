import logging
import functools
from spaceone.api.secret.v1 import user_secret_pb2
from spaceone.core.pygrpc.message_type import *
from spaceone.core import utils
from spaceone.secret.model.user_secret_model import UserSecret

__all__ = ["UserSecretInfo", "UserSecretsInfo", "UserSecretDataInfo"]
_LOGGER = logging.getLogger(__name__)


def UserSecretDataInfo(secret_data):
    info = {
        "encrypted": secret_data.get("encrypted", False),
        "encrypt_options": change_struct_type(secret_data.get("encrypt_options", {})),
        "data": change_struct_type(secret_data["data"]),
    }

    return user_secret_pb2.UserSecretDataInfo(**info)


def UserSecretInfo(secret_vo: UserSecret, minimal=False):
    info = {
        "user_secret_id": secret_vo.user_secret_id,
        "name": secret_vo.name,
        "schema_id": secret_vo.schema_id,
        "provider": secret_vo.provider,
    }

    if minimal is False:
        info.update(
            {
                "tags": change_struct_type(secret_vo.tags),
                "user_id": secret_vo.user_id,
                "domain_id": secret_vo.domain_id,
                "created_at": utils.datetime_to_iso8601(secret_vo.created_at),
            }
        )

    return user_secret_pb2.UserSecretInfo(**info)


def UserSecretsInfo(secret_vos, total_count, **kwargs):
    results = list(map(functools.partial(UserSecretInfo, **kwargs), secret_vos))

    return user_secret_pb2.UserSecretsInfo(results=results, total_count=total_count)
