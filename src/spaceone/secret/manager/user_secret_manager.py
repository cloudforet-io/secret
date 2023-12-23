import logging

from spaceone.core.manager import BaseManager
from spaceone.secret.model.user_secret_model import UserSecret

_LOGGER = logging.getLogger(__name__)


class UserSecretManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_secret_model: UserSecret = self.locator.get_model("UserSecret")

    def create_user_secret(self, params):
        def _rollback(user_secret_vo):
            _LOGGER.info(
                f"[ROLLBACK] Delete user_secret : {user_secret_vo.name} ({user_secret_vo.user_secret_id})"
            )
            user_secret_vo.delete()

        user_secret_vo: UserSecret = self.user_secret_model.create(params)

        self.transaction.add_rollback(_rollback, user_secret_vo)

        return user_secret_vo

    def update_user_secret_by_vo(self, params, user_secret_vo):
        def _rollback(old_data):
            _LOGGER.info(
                f'[ROLLBACK] Revert Data : {old_data["name"]} ({old_data["user_secret_id"]})'
            )
            user_secret_vo.update(old_data)

        self.transaction.add_rollback(_rollback, user_secret_vo.to_dict())

        return user_secret_vo.update(params)

    @staticmethod
    def delete_user_secret_by_vo(user_secret_vo):
        user_secret_vo.delete()

    def get_user_secret(self, user_secret_id, domain_id, user_id=None):
        conditions = {
            "user_secret_id": user_secret_id,
            "domain_id": domain_id,
        }

        if user_id:
            conditions["user_id"] = user_id

        return self.user_secret_model.get(**conditions)

    def filter_user_secrets(self, **conditions):
        return self.user_secret_model.filter(**conditions)

    def list_user_secrets(self, query):
        return self.user_secret_model.query(**query)

    def stat_user_secrets(self, query):
        return self.user_secret_model.stat(**query)
