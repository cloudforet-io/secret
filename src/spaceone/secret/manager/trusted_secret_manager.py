import logging

from spaceone.core.manager import BaseManager
from spaceone.secret.model.trusted_secret_model import TrustedSecret

_LOGGER = logging.getLogger(__name__)


class TrustedSecretManager(BaseManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trusted_secret_model: TrustedSecret = self.locator.get_model(
            "TrustedSecret"
        )

    def create_trusted_secret(self, params):
        def _rollback(trusted_secret_vo):
            _LOGGER.info(
                f"[ROLLBACK] Delete trusted secret : {trusted_secret_vo.name} ({trusted_secret_vo.trusted_secret_id})"
            )
            trusted_secret_vo.delete()

        trusted_secret_vo: TrustedSecret = self.trusted_secret_model.create(params)

        self.transaction.add_rollback(_rollback, trusted_secret_vo)

        return trusted_secret_vo

    def update_trusted_secret_by_vo(self, params, trusted_secret_vo):
        def _rollback(old_data):
            _LOGGER.info(
                f'[ROLLBACK] Revert Data : {old_data["name"]} ({old_data["trusted_secret_id"]})'
            )
            trusted_secret_vo.update(old_data)

        self.transaction.add_rollback(_rollback, trusted_secret_vo.to_dict())

        return trusted_secret_vo.update(params)

    @staticmethod
    def delete_trusted_secret_by_vo(trusted_secret_vo):
        trusted_secret_vo.delete()

    def get_trusted_secret(self, trusted_secret_id, domain_id, workspace_id=None):
        conditions = {
            "trusted_secret_id": trusted_secret_id,
            "domain_id": domain_id,
        }

        if workspace_id:
            conditions["workspace_id"] = workspace_id

        return self.trusted_secret_model.get(**conditions)

    def filter_trusted_secrets(self, **conditions):
        return self.trusted_secret_model.filter(**conditions)

    def list_trusted_secrets(self, query):
        return self.trusted_secret_model.query(**query)

    def stat_trusted_secrets(self, query):
        return self.trusted_secret_model.stat(**query)
