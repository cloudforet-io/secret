# -*- coding: utf-8 -*-
import logging
from mongoengine import *

from spaceone.core.locator import Locator
from spaceone.core.model.mongo_model import MongoModel

_LOGGER = logging.getLogger(__name__)


class Secret(MongoModel):
    secret_id = StringField(max_length=40, generate_id='secret', unique=True)
    name = StringField(max_length=255, unique_with='domain_id')
    secret_type = StringField(max_length=40, choices=('CREDENTIALS',))
    tags = DictField()
    schema = StringField(max_length=40, null=True, default=None)
    provider = StringField(max_length=40, null=True, default=None)
    service_account_id = StringField(max_length=40, null=True, default=None)
    project_id = StringField(max_length=40, null=True, default=None)
    domain_id = StringField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        'updatable_fields': [
            'name',
            'tags',
            'project_id'
        ],
        'exact_fields': [
            'secret_id',
            'secret_type',
            'schema',
            'provider',
            'service_account_id',
            'project_id',
            'domain_id'
        ],
        'minimal_fields': [
            'secret_id',
            'name',
            'secret_type'
        ],
        'ordering': [
            'name'
        ],
        'indexes': [
            'secret_id',
            'secret_type',
            'schema',
            'provider',
            'service_account_id',
            'project_id',
            'domain_id'
        ]
    }

    @classmethod
    def query(cls, *args, **kwargs):
        change_filter = []

        for condition in kwargs.get('filter', []):
            key = condition.get('k') or condition.get('key')
            if key == 'secret_group_id':
                change_filter.append(cls._change_secret_group_id_filter(condition))

            else:
                change_filter.append(condition)

        kwargs['filter'] = change_filter

        return super().query(*args, **kwargs)

    @staticmethod
    def _change_secret_group_id_filter(condition):
        value = condition.get('v') or condition.get('value')
        operator = condition.get('o') or condition.get('operator')

        map_query = {
            'filter': [{
                'k': 'secret_group_id',
                'v': value,
                'o': operator
            }]
        }
        locator = Locator()
        secret_group_map_model = locator.get_model('SecretGroupMap')

        map_vos, total_count = secret_group_map_model.query(**map_query)

        return {
            'k': 'secret_id',
            'v': list(map(lambda map_vo: map_vo.secret.secret_id, map_vos)),
            'o': 'in'
        }
