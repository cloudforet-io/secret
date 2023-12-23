import logging

from spaceone.core.service import *
from spaceone.core.service.utils import *

from spaceone.secret.manager.identity_manager import IdentityManager
from spaceone.secret.manager.user_secret_manager import UserSecretManager
from spaceone.secret.model.user_secret_model import UserSecret
from spaceone.secret.manager.secret_connector_manager import SecretConnectorManager

_LOGGER = logging.getLogger(__name__)


@authentication_handler
@authorization_handler
@mutation_handler
@event_handler
class UserSecretService(BaseService):
    resource = "UserSecret"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_secret_mgr: UserSecretManager = self.locator.get_manager(
            "UserSecretManager"
        )
        self.identity_mgr: IdentityManager = self.locator.get_manager("IdentityManager")

    @transaction(
        permission="secret:UserSecret.write",
        role_types=["USER"],
    )
    @check_required(["name", "data", "user_id", "domain_id"])
    def create(self, params):
        """Create user secret

        Args:
            params (dict): {
                'name': 'str',                  # required
                'data': 'dict',                 # required
                'schema_id': 'str',
                'tags': 'dict',
                'encrypted': 'bool',
                'encrypt_options': 'dict',
                'user_id': 'str',               # inherited from auth (required)
                'domain_id': 'str'              # inherited from auth (required)
            }

        Returns:
            user_secret_vo
        """

        user_secret_vo = self.user_secret_mgr.create_user_secret(params)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )
        secret_conn_mgr.create_secret(user_secret_vo.user_secret_id, params["data"])

        return user_secret_vo

    @transaction(
        permission="secret:UserSecret.write",
        role_types=["USER"],
    )
    @check_required(["user_secret_id", "user_id", "domain_id"])
    def update(self, params):
        """Update user secret

        Args:
            params (dict): {
                'user_secret_id': 'str',    # required
                'name': 'str' ,
                'tags': 'dict',
                'user_id': 'str',           # inherited from auth (required)
                'domain_id': 'str'          # inherited from auth (required)
            }

        Returns:
            user_secret_vo
        """

        user_id = params["user_id"]
        domain_id = params["domain_id"]
        user_secret_id = params["user_secret_id"]

        user_secret_vo: UserSecret = self.user_secret_mgr.get_user_secret(
            user_secret_id, domain_id, user_id
        )

        user_secret_vo = self.user_secret_mgr.update_user_secret_by_vo(
            params, user_secret_vo
        )

        return user_secret_vo

    @transaction(
        permission="secret:UserSecret.write",
        role_types=["USER"],
    )
    @check_required(["user_secret_id", "user_id", "domain_id"])
    def delete(self, params):
        """Delete user secret

        Args:
            params (dict): {
                'user_secret_id': 'str',        # required
                'user_id': 'str',               # inherited from auth (required)
                'domain_id': 'str'.             # inherited from auth (required)
            }

        Returns:
            None
        """

        user_secret_id = params["user_secret_id"]
        user_id = params["user_id"]
        domain_id = params["domain_id"]

        user_secret_vo = self.user_secret_mgr.get_user_secret(
            user_secret_id, domain_id, user_id
        )

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )
        secret_conn_mgr.delete_secret(user_secret_id)

        self.user_secret_mgr.delete_user_secret_by_vo(user_secret_vo)

    @transaction(
        permission="secret:UserSecret.write",
        role_types=["USER"],
    )
    @check_required(["user_secret_id", "data", "user_id", "domain_id"])
    def update_data(self, params):
        """Update user secret data

        Args:
            params (dict): {
                'user_secret_id': 'str',            # required
                'schema_id': 'str',
                'data': 'dict',                     # required
                'encrypted': 'bool',
                'encrypt_options': 'dict',
                'user_id': 'str',                   # inherited from auth (required)
                'domain_id': 'str',                 # inherited from auth (required)
            }

        Returns:
            user_secret_data (dict)
        """

        user_id = params["user_id"]
        domain_id = params["domain_id"]
        user_secret_id = params["user_secret_id"]
        data = params["data"]

        user_secret_vo = self.user_secret_mgr.get_user_secret(
            user_secret_id, domain_id, user_id
        )
        self.user_secret_mgr.update_user_secret_by_vo(params, user_secret_vo)

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )
        secret_conn_mgr.update_secret(user_secret_id, data)

    @transaction(exclude=["authentication", "authorization", "mutation"])
    @check_required(["user_secret_id", "domain_id"])
    def get_data(self, params):
        """Get user secret data

        Args:
            params (dict): {
                'user_secret_id': 'str',        # required
                'domain_id': 'str',             # required
            }

        Returns:
            user_secret_data (dict)
        """

        user_secret_id = params["user_secret_id"]
        domain_id = params["domain_id"]

        user_secret_vo: UserSecret = self.user_secret_mgr.get_user_secret(
            user_secret_id, domain_id
        )

        secret_conn_mgr: SecretConnectorManager = self.locator.get_manager(
            "SecretConnectorManager"
        )
        user_secret_data = secret_conn_mgr.get_secret(user_secret_id)

        return {
            "encrypted": user_secret_vo.encrypted,
            "encrypt_options": user_secret_vo.encrypt_options,
            "data": user_secret_data,
        }

    @transaction(
        permission="secret:UserSecret.read",
        role_types=["USER"],
    )
    @check_required(["user_secret_id", "user_id", "domain_id"])
    def get(self, params):
        """Get user secret

        Args:
            params (dict): {
                'user_secret_id': 'str',        # required
                'user_id': 'str',               # inherited from auth (required)
                'domain_id': 'str',             # inherited from auth (required)
            }

        Returns:
            user_secret_vo
        """

        return self.user_secret_mgr.get_user_secret(
            params["user_secret_id"],
            params["domain_id"],
            params["user_id"],
        )

    @transaction(
        permission="secret:UserSecret.read",
        role_types=["USER"],
    )
    @check_required(["user_id", "domain_id"])
    @append_query_filter(
        [
            "user_secret_id",
            "name",
            "schema_id",
            "provider",
            "user_id",
            "domain_id",
        ]
    )
    @append_keyword_filter(["user_secret_id", "name", "schema_id", "provider"])
    def list(self, params):
        """List user secrets

        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.Query)',
                'user_secret_id': 'str',
                'name': 'str',
                'schema_id': 'str',
                'provider': 'str',
                'user_id': 'str',               # inherited from auth (required)
                'domain_id': 'str',             # inherited from auth (required)
            }

        Returns:
            results (list)
            total_count (int)
        """

        query = params.get("query", {})
        user_secret_vos, total_count = self.user_secret_mgr.list_user_secrets(query)

        return user_secret_vos, total_count

    @transaction(
        permission="secret:UserSecret.read",
        role_types=["USER"],
    )
    @check_required(["query", "user_id", "domain_id"])
    @append_query_filter(["user_id", "domain_id"])
    @append_keyword_filter(["user_secret_id", "name", "schema_id", "provider"])
    def stat(self, params):
        """
        Args:
            params (dict): {
                'query': 'dict (spaceone.api.core.v1.StatisticsQuery)', # required
                'user_id': 'str',           # inherited from auth (required)
                'domain_id': 'str',         # inherited from auth (required)
            }

        Returns:
            values (list) : 'list of statistics data'

        """

        query = params.get("query", {})
        return self.user_secret_mgr.stat_user_secrets(query)
