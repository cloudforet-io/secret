from spaceone.api.secret.v1 import secret_group_pb2, secret_group_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class SecretGroup(BaseAPI, secret_group_pb2_grpc.SecretGroupServicer):

    pb2 = secret_group_pb2
    pb2_grpc = secret_group_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretGroupService', metadata) as secret_group_service:
            return self.locator.get_info('SecretGroupInfo', secret_group_service.create(params))

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretGroupService', metadata) as secret_group_service:
            return self.locator.get_info('SecretGroupInfo', secret_group_service.update(params))

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretGroupService', metadata) as secret_group_service:
            secret_group_service.delete(params)
            return self.locator.get_info('EmptyInfo')

    def add_secret(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretGroupService', metadata) as secret_group_service:
            return self.locator.get_info('SecretGroupSecretInfo', secret_group_service.add_secret(params))

    def remove_secret(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretGroupService', metadata) as secret_group_service:
            secret_group_service.remove_secret(params)
            return self.locator.get_info('EmptyInfo')

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretGroupService', metadata) as secret_group_service:
            return self.locator.get_info('SecretGroupInfo', secret_group_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretGroupService', metadata) as secret_group_service:
            secret_group_vos, total_count = secret_group_service.list(params)
            return self.locator.get_info('SecretGroupsInfo', secret_group_vos, total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretGroupService', metadata) as secret_group_service:
            return self.locator.get_info('StatisticsInfo', secret_group_service.stat(params))
