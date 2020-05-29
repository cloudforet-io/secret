import logging
from spaceone.core.manager import BaseManager
from spaceone.secret.model.secret_group_model import SecretGroup, SecretGroupMap

_LOGGER = logging.getLogger(__name__)


class SecretGroupManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_group_model: SecretGroup = self.locator.get_model('SecretGroup')
        self.secret_group_map_model: SecretGroupMap = self.locator.get_model('SecretGroupMap')

    def create_secret_group(self, params):
        def _rollback(secret_group_vo):
            _LOGGER.info(
                f'[ROLLBACK] Delete secret group : {secret_group_vo.name} ({secret_group_vo.secret_group_id})')
            secret_group_vo.delete()

        secret_group_vo: SecretGroup = self.secret_group_model.create(params)
        self.transaction.add_rollback(_rollback, secret_group_vo)

        return secret_group_vo

    def update_secret_group(self, params):
        self.update_secret_group_by_vo(params, self.get_secret_group(params['secret_group_id'],
                                                                     params['domain_id']))

    def update_secret_group_by_vo(self, params, secret_group_vo):
        def _rollback(old_data):
            _LOGGER.info(f'[ROLLBACK] Revert Data : {old_data["name"]} ({old_data["secret_group_id"]})')
            secret_group_vo.update(old_data)

        self.transaction.add_rollback(_rollback, secret_group_vo.to_dict())

        return secret_group_vo.update(params)

    def delete_secret_group(self, secret_group_id, domain_id):
        self.delete_secret_group_by_vo(self.get_secret_group(secret_group_id, domain_id))

    def get_secret_group(self, secret_group_id, domain_id, only=None):
        return self.secret_group_model.get(secret_group_id=secret_group_id, domain_id=domain_id, only=only)

    def list_secret_groups(self, query):
        return self.secret_group_model.query(**query)

    def stat_secret_groups(self, query):
        return self.secret_group_model.stat(**query)

    def list_secret_group_maps(self, query):
        return self.secret_group_map_model.query(**query)

    @staticmethod
    def add_secret(secret_group_vo, secret_vo):
        return secret_group_vo.append('secrets', secret_vo)

    @staticmethod
    def remove_secret(secret_group_vo, secret_group_map_vo):
        secret_group_vo.remove('secrets', secret_group_map_vo)

    @staticmethod
    def delete_secret_group_by_vo(secret_group_vo):
        secret_group_vo.delete()
