# -*- coding: utf-8 -*-

import logging
import functools

from spaceone.core.pygrpc.message_type import *
from spaceone.api.secret.v1 import secret_group_pb2
from spaceone.secret.model.secret_group_model import SecretGroup
from spaceone.secret.info.secret_info import SecretInfo

__all__ = ['SecretGroupSecretInfo', 'SecretGroupInfo', 'SecretGroupsInfo']
_LOGGER = logging.getLogger(__name__)


def SecretGroupSecretInfo(secret_group_map_vo):
    info = {
        'secret_group_info': SecretGroupInfo(secret_group_map_vo.secret_group, minimal=True),
        'secret_info': SecretInfo(secret_group_map_vo.secret, minimal=True),
        'domain_id': secret_group_map_vo.secret.domain_id
    }

    return secret_group_pb2.SecretGroupSecretInfo(**info)


def SecretGroupInfo(secret_group_vo: SecretGroup, minimal=False):
    info = {
        'secret_group_id': secret_group_vo.secret_group_id,
        'name': secret_group_vo.name
    }

    if minimal is False:
        info.update({
            'tags': change_struct_type(secret_group_vo.tags),
            'domain_id': secret_group_vo.domain_id,
            'created_at': change_timestamp_type(secret_group_vo.created_at)
        })

    return secret_group_pb2.SecretGroupInfo(**info)


def SecretGroupsInfo(secret_group_vos, total_count, **kwargs):
    results = list(map(functools.partial(SecretGroupInfo, **kwargs), secret_group_vos))

    return secret_group_pb2.SecretGroupsInfo(results=results, total_count=total_count)
