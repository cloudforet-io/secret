from spaceone.api.secret.v1 import secret_pb2, secret_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class Secret(BaseAPI, secret_pb2_grpc.SecretServicer):

    pb2 = secret_pb2
    pb2_grpc = secret_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretService', metadata) as secret_service:
            return self.locator.get_info('SecretInfo', secret_service.create(params))

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretService', metadata) as secret_service:
            return self.locator.get_info('SecretInfo', secret_service.update(params))

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretService', metadata) as secret_service:
            secret_service.delete(params)
            return self.locator.get_info('EmptyInfo')

    def get_data(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretService', metadata) as secret_service:
            secret_data = secret_service.get_data(params)
            return self.locator.get_info('SecretDataInfo', secret_data)

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretService', metadata) as secret_service:
            return self.locator.get_info('SecretInfo', secret_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretService', metadata) as secret_service:
            secret_vos, total_count = secret_service.list(params)
            return self.locator.get_info('SecretsInfo', secret_vos, total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('SecretService', metadata) as secret_service:
            return self.locator.get_info('StatisticsInfo', secret_service.stat(params))
