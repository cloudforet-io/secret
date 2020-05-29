# -*- coding: utf-8 -*-
from spaceone.core.manager import BaseManager
from spaceone.secret.connector.identity_connector import IdentityConnector


class IdentityManager(BaseManager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.identity_conn: IdentityConnector = self.locator.get_connector('IdentityConnector')

    def get_service_account(self, service_account_id, domain_id):
        return self.identity_conn.get_service_account(service_account_id, domain_id)

    def list_service_accounts(self, query, domain_id):
        return self.identity_conn.list_service_accounts(query, domain_id)

    def get_project(self, project_id, domain_id):
        return self.identity_conn.get_project(project_id, domain_id)

    def list_projects(self, query, domain_id):
        return self.identity_conn.list_projects(query, domain_id)
