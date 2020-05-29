# -*- coding: utf-8 -*-
import logging
from mongoengine import *

from spaceone.core.locator import Locator
from spaceone.core.model.mongo_model import MongoModel
from spaceone.secret.model.secret_model import Secret

_LOGGER = logging.getLogger(__name__)


class SecretGroup(MongoModel):
    secret_group_id = StringField(max_length=40, generate_id='secret-grp', unique=True)
    name = StringField(max_length=255, unique_with='domain_id')
    tags = DictField()
    domain_id = StringField(max_length=255)
    created_at = DateTimeField(auto_now_add=True)

    meta = {
        'updatable_fields': [
            'name',
            'tags'
        ],
        'exact_fields': [
            'secret_group_id',
            'domain_id'
        ],
        'minimal_fields': [
            'secret_group_id',
            'name'
        ],
        'ordering': [
            'name'
        ],
        'indexes': [
            'secret_group_id',
            'domain_id'
        ]
    }

    def append(self, key, data):
        if key == 'secrets':
            secret_group_map_vo = SecretGroupMap.create({
                'secret_group': self,
                'secret': data
            })
            return secret_group_map_vo
        else:
            super().append(key, data)
            return self

    def remove(self, key, data):
        if key == 'secrets':
            data.delete()
        else:
            super().remove(key, data)

    @classmethod
    def query(cls, *args, **kwargs):
        change_filter = []

        for condition in kwargs.get('filter', []):
            key = condition.get('k') or condition.get('key')
            if key == 'secret_id':
                change_filter.append(cls._change_secret_id_filter(condition))

            else:
                change_filter.append(condition)

        kwargs['filter'] = change_filter

        return super().query(*args, **kwargs)

    @staticmethod
    def _change_secret_id_filter(condition):
        value = condition.get('v') or condition.get('value')
        operator = condition.get('o') or condition.get('operator')

        map_query = {
            'filter': [{
                'k': 'secret_id',
                'v': value,
                'o': operator
            }]
        }

        locator = Locator()
        secret_group_map_model = locator.get_model('SecretGroupMap')
        map_vos, total_count = secret_group_map_model.query(**map_query)

        return {
            'k': 'secret_group_id',
            'v': list(map(lambda map_vo: map_vo.secret_group.secret_group_id, map_vos)),
            'o': 'in'
        }


class SecretGroupMap(MongoModel):
    secret_group = ReferenceField('SecretGroup', reverse_delete_rule=CASCADE)
    secret = ReferenceField('Secret', reverse_delete_rule=CASCADE)

    meta = {
        'reference_query_keys': {
            'secret_group': SecretGroup,
            'secret': Secret
        },
        'change_query_keys': {
            'secret_group_id': 'secret_group.secret_group_id',
            'secret_id': 'secret.secret_id'
        },
        'indexes': [
            'secret_group',
            'secret'
        ]
    }
