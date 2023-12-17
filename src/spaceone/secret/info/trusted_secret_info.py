import logging
import functools
from spaceone.api.secret.v1 import trusted_secret_pb2
from spaceone.core.pygrpc.message_type import *
from spaceone.core import utils
from spaceone.secret.model.trusted_secret_model import TrustedSecret

__all__ = ["TrustedSecretInfo", "TrustedSecretsInfo"]
_LOGGER = logging.getLogger(__name__)


def TrustedSecretInfo(trusted_secret_vo: TrustedSecret, minimal=False):
    info = {
        "trusted_secret_id": trusted_secret_vo.trusted_secret_id,
        "name": trusted_secret_vo.name,
        "schema_id": trusted_secret_vo.schema_id,
        "provider": trusted_secret_vo.provider,
    }

    if minimal is False:
        info.update(
            {
                "tags": change_struct_type(trusted_secret_vo.tags),
                "trusted_account_id": trusted_secret_vo.trusted_account_id,
                "resource_group": trusted_secret_vo.resource_group,
                "workspace_id": trusted_secret_vo.workspace_id,
                "domain_id": trusted_secret_vo.domain_id,
                "created_at": utils.datetime_to_iso8601(trusted_secret_vo.created_at),
            }
        )

    return trusted_secret_pb2.TrustedSecretInfo(**info)


def TrustedSecretsInfo(trusted_secret_vos, total_count, **kwargs):
    results = list(
        map(functools.partial(TrustedSecretInfo, **kwargs), trusted_secret_vos)
    )
    return trusted_secret_pb2.TrustedSecretsInfo(
        results=results, total_count=total_count
    )
