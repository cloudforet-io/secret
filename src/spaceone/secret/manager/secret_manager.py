import logging

from spaceone.core.manager import BaseManager
from spaceone.secret.model.secret_model import Secret

_LOGGER = logging.getLogger(__name__)


class SecretManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_model: Secret = self.locator.get_model("Secret")

    def create_secret(self, params):
        def _rollback(secret_vo):
            _LOGGER.info(
                f"[ROLLBACK] Delete secret : {secret_vo.name} ({secret_vo.secret_id})"
            )
            secret_vo.delete()

        secret_vo: Secret = self.secret_model.create(params)

        self.transaction.add_rollback(_rollback, secret_vo)

        return secret_vo

    def update_secret_by_vo(self, params, secret_vo):
        def _rollback(old_data):
            _LOGGER.info(
                f'[ROLLBACK] Revert Data : {old_data["name"]} ({old_data["secret_id"]})'
            )
            secret_vo.update(old_data)

        self.transaction.add_rollback(_rollback, secret_vo.to_dict())

        return secret_vo.update(params)

    @staticmethod
    def delete_secret_by_vo(secret_vo):
        secret_vo.delete()

    def get_secret(self, secret_id, domain_id, workspace_id=None, user_projects=None):
        conditions = {
            "secret_id": secret_id,
            "domain_id": domain_id,
        }

        if workspace_id:
            conditions["workspace_id"] = workspace_id

        if user_projects:
            conditions["project_id"] = user_projects

        return self.secret_model.get(**conditions)

    def filter_secrets(self, **conditions):
        return self.secret_model.filter(**conditions)

    def list_secrets(self, query):
        return self.secret_model.query(**query)

    def stat_secrets(self, query):
        return self.secret_model.stat(**query)
