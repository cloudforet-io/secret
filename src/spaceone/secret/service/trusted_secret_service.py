import logging

from spaceone.core.service import *
from spaceone.core.service.utils import *

from spaceone.secret.error.custom import *
from spaceone.secret.manager.identity_manager import IdentityManager
from spaceone.secret.manager.secret_manager import SecretManager
from spaceone.secret.manager.trusted_secret_manager import TrustedSecretManager
from spaceone.secret.manager.secret_connector_manager import SecretConnectorManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class TrustedSecretService(BaseService):
    resource = "TrustedSecret"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trusted_secret_mgr: TrustedSecretManager = self.locator.get_manager(
            "TrustedSecretManager"
        )
        self.identity_mgr: IdentityManager = self.locator.get_manager("IdentityManager")

    @transaction(
        permission="secret:TrustedSecret.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @check_required(["name", "data", "resource_group", "domain_id"])
    def create(self, params):
        """Create trusted secret

        Args:
            params (dict): {
                'name': 'str',                  # required
                'data': 'dict',                 # required
                'schema_id': 'str',
                'tags': 'dict',
                'encrypted': 'bool',
                'encrypt_options': 'dict',
                'trusted_account_id': 'str',
                'resource_group': 'str',        # required
                'workspace_id': 'str',          # injected from auth
                'domain_id': 'str'              # injected from auth (required)
            }

        Returns:
            trusted_secret_vo
        """

        # Check permission by resource group
        if params["resource_group"] == "WORKSPACE":
            if "workspace_id" not in params:
                raise ERROR_REQUIRED_PARAMETER(key="workspace_id")

            self.identity_mgr.check_workspace(
                params["workspace_id"], params["domain_id"]
            )
        else:
            params["workspace_id"] = "*"

        if "trusted_account_id" in params:
            trusted_account_info = self.identity_mgr.get_trusted_account(
                params["trusted_account_id"]
            )
            params["provider"] = trusted_account_info.get("provider")

        trusted_secret_vo = self.trusted_secret_mgr.create_trusted_secret(params)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )

        secret_conn_mgr.create_secret(
            trusted_secret_vo.trusted_secret_id, params["data"]
        )

        return trusted_secret_vo

    @transaction(
        permission="secret:TrustedSecret.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @check_required(["trusted_secret_id", "domain_id"])
    def update(self, params):
        """Update trusted secret

        Args:
            params (dict): {
                'trusted_secret_id': 'str',         # required
                'name': 'str' ,
                'tags': 'dict',
                'workspace_id': 'str',              # injected from auth
                'domain_id': 'str'                  # injected from auth (required)
            }

        Returns:
            trusted_secret_vo
        """

        trusted_secret_id = params["trusted_secret_id"]
        domain_id = params["domain_id"]
        workspace_id = params.get("workspace_id")

        trusted_secret_vo = self.trusted_secret_mgr.get_trusted_secret(
            trusted_secret_id, domain_id, workspace_id
        )
        update_trusted_secret_vo = self.trusted_secret_mgr.update_trusted_secret_by_vo(
            params, trusted_secret_vo
        )

        return update_trusted_secret_vo

    @transaction(
        permission="secret:TrustedSecret.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @check_required(["trusted_secret_id", "domain_id"])
    def delete(self, params):
        """Delete trusted secret

        Args:
            params (dict): {
                'trusted_secret_id': 'str',     # required
                'domain_id': 'str'              # injected from auth (required)
            }

        Returns:
            None
        """

        domain_id = params["domain_id"]
        trusted_secret_id = params["trusted_secret_id"]
        workspace_id = params.get("workspace_id")

        trusted_secret_vo = self.trusted_secret_mgr.get_trusted_secret(
            trusted_secret_id, domain_id, workspace_id
        )

        self._check_related_secret(trusted_secret_id, domain_id)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )
        secret_conn_mgr.delete_secret(trusted_secret_id)

        self.trusted_secret_mgr.delete_trusted_secret_by_vo(trusted_secret_vo)

    @transaction(
        permission="secret:TrustedSecret.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER"],
    )
    @check_required(["trusted_secret_id", "data", "domain_id"])
    def update_data(self, params):
        """Update trusted secret data through backend Secret service

        Args:
            params (dict): {
                'trusted_secret_id': 'str',     # required
                'schema_id': 'str',
                'data': 'dict',                 # required
                'encrypted': 'bool',
                'encrypt_options': 'dict',
                'workspace_id': 'str',          # injected from auth
                'domain_id': 'str'              # injected from auth (required)
            }

        Returns:
            None
        """

        domain_id = params["domain_id"]
        trusted_secret_id = params["trusted_secret_id"]
        workspace_id = params.get("workspace_id")
        data = params["data"]

        trusted_secret_vo = self.trusted_secret_mgr.get_trusted_secret(
            trusted_secret_id, domain_id, workspace_id
        )
        self.trusted_secret_mgr.update_trusted_secret_by_vo(params, trusted_secret_vo)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )
        secret_conn_mgr.update_secret(trusted_secret_id, data)

    @transaction(
        permission="secret:TrustedSecret.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @check_required(["trusted_secret_id", "domain_id"])
    def get(self, params):
        """Get trusted secret

        Args:
            params (dict): {
                'trusted_secret_id': 'str',         # required
                'workspace_id': 'list',             # injected from auth
                'domain_id': 'str',                 # injected from auth (required)
            }

        Returns:
            trusted_secret_vo
        """

        return self.trusted_secret_mgr.get_trusted_secret(
            params["trusted_secret_id"], params["domain_id"], params.get("workspace_id")
        )

    @transaction(
        permission="secret:TrustedSecret.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @check_required(["domain_id"])
    @append_query_filter(
        [
            "trusted_secret_id",
            "name",
            "schema_id",
            "provider",
            "trusted_account_id",
            "workspace_id",
            "domain_id",
        ]
    )
    @append_keyword_filter(["trusted_secret_id", "name", "schema_id", "provider"])
    def list(self, params):
        """List trusted secrets

        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'trusted_secret_id': 'str',
                'name': 'str',
                'schema_id': 'str',
                'provider': 'str',
                'trusted_account_id': 'str',
                'workspace_id': 'list',             # injected from auth
                'domain_id': 'str',                 # injected from auth (required)
            }

        Returns:
            results (list)
            total_count (int)
        """

        query = params.get("query", {})
        trusted_secret_vos, total_count = self.trusted_secret_mgr.list_trusted_secrets(
            query
        )

        return trusted_secret_vos, total_count

    @transaction(
        permission="secret:TrustedSecret.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @check_required(["query", "domain_id"])
    @append_query_filter(["workspace_id", "domain_id"])
    @append_keyword_filter(["trusted_secret_id", "name", "schema_id", "provider"])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)',     # required
                'workspace_id': 'list',         # injected from auth
                'domain_id': 'str',             # injected from auth (required)
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get("query", {})
        return self.trusted_secret_mgr.stat_trusted_secrets(query)

    def _check_related_secret(self, trusted_secret_id, domain_id):
        secret_mgr: SecretManager = self.locator.get_manager("SecretManager")
        secret_vos = secret_mgr.filter_secrets(
            trusted_secret_id=trusted_secret_id, domain_id=domain_id
        )
        if secret_vos.count() > 0:
            raise ERROR_EXIST_RELATED_SECRET(secret_id=secret_vos[0].secret_id)
