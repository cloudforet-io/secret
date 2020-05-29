# -*- coding: utf-8 -*-

import logging
import functools

from spaceone.core.pygrpc.message_type import *
from spaceone.api.secret.v1 import secret_pb2
from spaceone.secret.model.secret_model import Secret


__all__ = ['SecretInfo', 'SecretsInfo', 'SecretDataInfo']
_LOGGER = logging.getLogger(__name__)


def SecretDataInfo(secret_data):
    info = {
        'data': change_struct_type(secret_data)
    }

    return secret_pb2.SecretDataInfo(**info)


def SecretInfo(secret_vo: Secret, minimal=False):
    info = {
        'secret_id': secret_vo.secret_id,
        'name': secret_vo.name,
        'secret_type': secret_vo.secret_type
    }

    if minimal is False:
        info.update({
            'tags': change_struct_type(secret_vo.tags),
            'schema': secret_vo.schema,
            'provider': secret_vo.provider,
            'service_account_id': secret_vo.service_account_id,
            'project_id': secret_vo.project_id,
            'domain_id': secret_vo.domain_id,
            'created_at': change_timestamp_type(secret_vo.created_at)
        })

        if getattr(secret_vo, 'secret_groups', None) is not None:
            secret_group_infos = list(map(lambda secret_group: SecretGroupInfo(secret_group),
                                          secret_vo.secret_groups))

            info.update({
                'secret_groups': change_list_value_type(secret_group_infos)
            })

    return secret_pb2.SecretInfo(**info)


def SecretsInfo(secret_vos, total_count, **kwargs):
    results = list(map(functools.partial(SecretInfo, **kwargs), secret_vos))

    return secret_pb2.SecretsInfo(results=results, total_count=total_count)


def SecretGroupInfo(secret_group_vo):
    return {
        'secret_group_id': secret_group_vo.secret_group_id,
        'name': secret_group_vo.name
    }
