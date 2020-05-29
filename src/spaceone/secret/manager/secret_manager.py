import logging

from spaceone.core.manager import BaseManager
from spaceone.secret.model.secret_model import Secret
from spaceone.secret.model.secret_group_model import SecretGroupMap

_LOGGER = logging.getLogger(__name__)


class SecretManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_model: Secret = self.locator.get_model('Secret')

    def create_secret(self, params):
        def _rollback(secret_vo):
            _LOGGER.info(f'[ROLLBACK] Delete secret : {secret_vo.name} ({secret_vo.secret_id})')
            secret_vo.delete()

        secret_vo: Secret = self.secret_model.create(params)

        self.transaction.add_rollback(_rollback, secret_vo)

        return secret_vo

    def update_secret(self, params):
        self.update_secret_by_vo(params, self.get_secret(params['secret_id'], params['domain_id']))

    def update_secret_by_vo(self, params, secret_vo):
        def _rollback(old_data):
            _LOGGER.info(f'[ROLLBACK] Revert Data : {old_data["name"]} ({old_data["secret_id"]})')
            secret_vo.update(old_data)

        self.transaction.add_rollback(_rollback, secret_vo.to_dict())

        return secret_vo.update(params)

    def delete_secret(self, secret_id, domain_id):
        self.delete_secret_by_vo(self.get_secret(secret_id, domain_id))

    @staticmethod
    def delete_secret_by_vo(secret_vo):
        secret_vo.delete()

    def get_secret(self, secret_id, domain_id, only=None):
        return self.secret_model.get(secret_id=secret_id, domain_id=domain_id, only=only)

    def list_secrets(self, query):
        return self.secret_model.query(**query)

    def stat_secrets(self, query):
        return self.secret_model.stat(**query)

    def get_related_secret_groups(self, secret_vos):
        include_secret_group_filter = {
            'filter': [{
                'k': 'secret_id',
                'v': list(map(lambda secret_vo: secret_vo.secret_id, secret_vos)),
                'o': 'in'
            }]
        }

        secret_group_map_model: SecretGroupMap = self.locator.get_model('SecretGroupMap')
        map_vos, total_count = secret_group_map_model.query(include_secret_group_filter)

        for secret_vo in secret_vos:
            secret_groups = []
            for map_vo in map_vos:
                if map_vo.secret == secret_vo:
                    secret_groups.append(map_vo.secret_group)

            setattr(secret_vo, 'secret_groups', secret_groups)

        return secret_vos
