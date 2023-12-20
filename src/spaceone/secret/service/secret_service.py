import logging

from spaceone.core.service import *
from spaceone.core.service.utils import *

from spaceone.secret.error.custom import *
from spaceone.secret.manager.identity_manager import IdentityManager
from spaceone.secret.manager.secret_manager import SecretManager
from spaceone.secret.model.secret_model import Secret
from spaceone.secret.manager.trusted_secret_manager import TrustedSecretManager
from spaceone.secret.manager.secret_connector_manager import SecretConnectorManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class SecretService(BaseService):
    resource = "Secret"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.secret_mgr: SecretManager = self.locator.get_manager("SecretManager")
        self.identity_mgr: IdentityManager = self.locator.get_manager("IdentityManager")

    @transaction(
        permission="secret:Secret.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["name", "data", "resource_group", "domain_id"])
    def create(self, params):
        """Create secret

        Args:
            params (dict): {
                'name': 'str',                  # required
                'data': 'dict',                 # required
                'schema_id': 'str',
                'tags': 'dict',
                'encrypted': 'bool',
                'encrypt_options': 'dict',
                'trusted_secret_id': 'str',
                'service_account_id': 'str',
                'resource_group': 'str',        # required
                'project_id': 'str',
                'workspace_id': 'str',          # inherited from auth
                'domain_id': 'str'              # inherited from auth (required)
            }

        Returns:
            secret_vo
        """

        resource_group = params["resource_group"]
        domain_id = params["domain_id"]
        workspace_id = params.get("workspace_id")

        # Check permission by resource group
        if resource_group == "PROJECT":
            if "service_account_id" in params:
                service_account_info = self.identity_mgr.get_service_account(
                    params["service_account_id"]
                )

                params["provider"] = service_account_info["provider"]
                params["project_id"] = service_account_info["project_id"]
                params["workspace_id"] = service_account_info["workspace_id"]
            elif "project_id" in params:
                project_info = self.identity_mgr.get_project(params["project_id"])
                params["workspace_id"] = project_info["workspace_id"]
            else:
                raise ERROR_REQUIRED_PARAMETER(key="project_id")
        elif resource_group == "WORKSPACE":
            if workspace_id is None:
                raise ERROR_REQUIRED_PARAMETER(key="workspace_id")

            self.identity_mgr.check_workspace(workspace_id, domain_id)
            params["project_id"] = "*"
        else:
            params["workspace_id"] = "*"
            params["project_id"] = "*"

        if "trusted_secret_id" in params:
            if workspace_id:
                workspace_id = [workspace_id, "*"]

            trusted_secret_mgr = self.locator.get_manager("TrustedSecretManager")
            trusted_secret_mgr.get_trusted_secret(
                params["trusted_secret_id"], domain_id, workspace_id
            )

        secret_vo = self.secret_mgr.create_secret(params)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )
        secret_conn_mgr.create_secret(secret_vo.secret_id, params["data"])

        return secret_vo

    @transaction(
        permission="secret:Secret.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["secret_id", "domain_id"])
    def update(self, params):
        """Update secret

        Args:
            params (dict): {
                'secret_id': 'str',         # required
                'name': 'str' ,
                'tags': 'dict',
                'project_id': 'str',
                'workspace_id': 'str',      # inherited from auth
                'domain_id': 'str'          # inherited from auth (required)
                'user_projects': 'list',    # inherited from auth
            }

        Returns:
            secret_vo
        """

        domain_id = params["domain_id"]
        secret_id = params["secret_id"]
        workspace_id = params.get("workspace_id")
        user_projects = params.get("user_projects")

        secret_vo: Secret = self.secret_mgr.get_secret(
            secret_id, domain_id, workspace_id, user_projects
        )

        if secret_vo.resource_group == "PROJECT":
            if project_id := params.get("project_id"):
                self.identity_mgr.get_project(project_id)
            else:
                raise ERROR_PERMISSION_DENIED()

        secret_vo = self.secret_mgr.update_secret_by_vo(params, secret_vo)

        return secret_vo

    @transaction(
        permission="secret:Secret.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["secret_id", "domain_id"])
    def delete(self, params):
        """Delete secret

        Args:
            params (dict): {
                'secret_id': 'str',         # required
                'workspace_id': 'str',      # inherited from auth
                'domain_id': 'str'.         # inherited from auth (required)
                'user_projects': 'list',    # inherited from auth
            }

        Returns:
            None
        """

        secret_id = params["secret_id"]
        domain_id = params["domain_id"]
        workspace_id = params.get("workspace_id")
        user_projects = params.get("user_projects")

        secret_vo = self.secret_mgr.get_secret(
            secret_id, domain_id, workspace_id, user_projects
        )

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )
        secret_conn_mgr.delete_secret(secret_id)

        self.secret_mgr.delete_secret_by_vo(secret_vo)

    @transaction(
        permission="secret:Secret.write",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @check_required(["secret_id", "data", "domain_id"])
    def update_data(self, params):
        """Update secret data through backend Secret service

        Args:
            params (dict): {
                'secret_id': 'str',             # required
                'schema_id': 'str',
                'data': 'dict',                 # required
                'encrypted': 'bool',
                'encrypt_options': 'dict',
                'workspace_id': 'str',          # inherited from auth
                'domain_id': 'str',             # inherited from auth (required)
                'user_projects': 'list',        # inherited from auth
            }

        Returns:
            secret_data (dict)
        """
        domain_id = params["domain_id"]
        secret_id = params["secret_id"]
        workspace_id = params.get("workspace_id")
        user_projects = params.get("user_projects")
        data = params["data"]

        secret_vo = self.secret_mgr.get_secret(
            secret_id, domain_id, workspace_id, user_projects
        )
        self.secret_mgr.update_secret_by_vo(params, secret_vo)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )
        secret_conn_mgr.update_secret(secret_id, data)

    @transaction(exclude=["authentication", "authorization", "mutation"])
    @check_required(["secret_id", "domain_id"])
    def get_data(self, params):
        """Get secret data through backend Secret service

        Args:
            params (dict): {
                'secret_id': 'str',         # required
                'workspace_id': 'str',      # inherited from auth
                'domain_id': 'str',         # inherited from auth (required)
                'user_projects': 'list',    # inherited from auth
            }

        Returns:
            secret_data (dict)
        """

        secret_id = params["secret_id"]
        domain_id = params["domain_id"]
        workspace_id = params.get("workspace_id")
        user_projects = params.get("user_projects")

        secret_vo: Secret = self.secret_mgr.get_secret(
            secret_id, domain_id, workspace_id, user_projects
        )
        secret_data = self._get_secret_data(secret_id)
        encrypt_options = secret_vo.encrypt_options

        if secret_vo.trusted_secret_id:
            trusted_secret_mgr: TrustedSecretManager = self.locator.get_manager(
                "TrustedSecretManager"
            )
            trusted_secret_vo = trusted_secret_mgr.get_trusted_secret(
                trusted_secret_id=secret_vo.trusted_secret_id, domain_id=domain_id
            )

            self._check_validation_trusted_secret(secret_vo, trusted_secret_vo)

            trusted_secret_data = self._get_secret_data(
                trusted_secret_vo.trusted_secret_id
            )
            trusted_secret_encrypt_options = trusted_secret_vo.encrypt_options

            if secret_vo.encrypted and trusted_secret_vo.encrypted:
                secret_data["trusted_encrypted_data"] = trusted_secret_data[
                    "encrypted_data"
                ]

                encrypt_options.update(
                    {
                        "trusted_encrypted_data_key": trusted_secret_encrypt_options.get(
                            "encrypted_data_key"
                        )
                    }
                )
            elif secret_vo.encrypted is False and trusted_secret_vo.encrypted is False:
                # Merge secret data & trusted secret data
                trusted_secret_data.update(secret_data)
                secret_data = trusted_secret_data

        return {
            "encrypted": secret_vo.encrypted,
            "encrypt_options": encrypt_options,
            "data": secret_data,
        }

    @transaction(
        permission="secret:Secret.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @change_value_by_rule("APPEND", "user_projects", "*")
    @check_required(["secret_id", "domain_id"])
    def get(self, params):
        """Get secret

        Args:
            params (dict): {
                'secret_id': 'str',         # required
                'workspace_id': 'str',      # inherited from auth
                'domain_id': 'str',         # inherited from auth (required)
                'user_projects': 'list',    # inherited from auth
            }

        Returns:
            secret_vo
        """

        return self.secret_mgr.get_secret(
            params["secret_id"],
            params["domain_id"],
            params.get("workspace_id"),
            params.get("user_projects"),
        )

    @transaction(
        permission="secret:Secret.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @change_value_by_rule("APPEND", "user_projects", "*")
    @check_required(["domain_id"])
    @append_query_filter(
        [
            "secret_id",
            "name",
            "schema_id",
            "provider",
            "trusted_secret_id",
            "service_account_id",
            "project_id",
            "workspace_id",
            "domain_id",
            "user_projects",
        ]
    )
    @append_keyword_filter(["secret_id", "name", "schema_id", "provider"])
    def list(self, params):
        """List secrets

        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'secret_id': 'str',
                'name': 'str',
                'schema_id': 'str',
                'provider': 'str',
                'trusted_secret_id': 'str',
                'service_account_id': 'str',
                'project_id': 'str',
                'workspace_id': 'str',          # inherited from auth
                'domain_id': 'str',             # inherited from auth (required)
                'user_projects': 'list',        # inherited from auth
            }

        Returns:
            results (list)
            total_count (int)
        """

        query = params.get("query", {})
        secret_vos, total_count = self.secret_mgr.list_secrets(query)

        return secret_vos, total_count

    @transaction(
        permission="secret:Secret.read",
        role_types=["DOMAIN_ADMIN", "WORKSPACE_OWNER", "WORKSPACE_MEMBER"],
    )
    @change_value_by_rule("APPEND", "workspace_id", "*")
    @change_value_by_rule("APPEND", "user_projects", "*")
    @check_required(["query", "domain_id"])
    @append_query_filter(["user_projects", "workspace_id", "domain_id"])
    @append_keyword_filter(["secret_id", "name", "schema_id", "provider"])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)', # required
                'workspace_id': 'str',      # inherited from auth
                'domain_id': 'str',         # inherited from auth (required)
                'user_projects': 'list',    # inherited from auth
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get("query", {})
        return self.secret_mgr.stat_secrets(query)

    def _get_secret_data(self, secret_id):
        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )
        return secret_conn_mgr.get_secret(secret_id)

    @staticmethod
    def _check_validation_trusted_secret(secret_vo, trusted_secret_vo):
        if secret_vo.encrypted != trusted_secret_vo.encrypted:
            raise ERROR_DIFF_SECRET_AND_TRUSTED_SECRET_ENCRYPTED()

        if secret_vo.encrypted and trusted_secret_vo.encrypted:
            secret_encrypt_options = secret_vo.encrypt_options
            trusted_secret_encrypt_options = trusted_secret_vo.encrypt_options

            secret_encrypt_algorithm = secret_encrypt_options.get("encrypt_algorithm")
            trusted_secret_encrypt_algorithm = trusted_secret_encrypt_options.get(
                "encrypt_algorithm"
            )

            if (
                secret_encrypt_algorithm
                and trusted_secret_encrypt_algorithm
                and secret_encrypt_algorithm == trusted_secret_encrypt_algorithm
            ):
                return True
            else:
                raise ERROR_DIFF_SECRET_AND_TRUSTED_SECRET_ENCRYPTED()

        return True
