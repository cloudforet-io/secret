from spaceone.core.manager import BaseManager
from spaceone.core.connector.space_connector import SpaceConnector

class IdentityManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_conn: SpaceConnector = self.locator.get_connector('SpaceConnector', service='identity')

    def get_service_account(self, service_account_id, domain_id):
        return self.identity_conn.dispatch(
            'ServiceAccount.get', {'service_account_id': service_account_id, 'domain_id': domain_id})

    def list_service_accounts(self, query, domain_id):
        return self.identity_conn.dispatch(
            'ServiceAccount.list', {'query': query, 'domain_id': domain_id})

    def get_project(self, project_id, domain_id):
        return self.identity_conn.dispatch(
            'Project.get', {'project_id': project_id, 'domain_id': domain_id})

    def list_projects(self, query, domain_id):
        return self.identity_conn.dispatch(
            'Project.list', {'query': query, 'domain_id': domain_id})
