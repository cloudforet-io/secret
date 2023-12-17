from spaceone.api.secret.v1 import trusted_secret_pb2, trusted_secret_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class TrustedSecret(BaseAPI, trusted_secret_pb2_grpc.TrustedSecretServicer):

    pb2 = trusted_secret_pb2
    pb2_grpc = trusted_secret_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('TrustedSecretService', metadata) as trusted_secret_service:
            return self.locator.get_info('TrustedSecretInfo', trusted_secret_service.create(params))

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('TrustedSecretService', metadata) as trusted_secret_service:
            return self.locator.get_info('TrustedSecretInfo', trusted_secret_service.update(params))

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('TrustedSecretService', metadata) as trusted_secret_service:
            trusted_secret_service.delete(params)
            return self.locator.get_info('EmptyInfo')

    def update_data(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('TrustedSecretService', metadata) as trusted_secret_service:
            trusted_secret_service.update_data(params)
            return self.locator.get_info('EmptyInfo')

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('TrustedSecretService', metadata) as trusted_secret_service:
            return self.locator.get_info('TrustedSecretInfo', trusted_secret_service.get(params))

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('TrustedSecretService', metadata) as trusted_secret_service:
            trusted_secret_vos, total_count = trusted_secret_service.list(params)
            return self.locator.get_info('TrustedSecretsInfo', trusted_secret_vos, total_count,
                                         minimal=self.get_minimal(params))

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service('TrustedSecretService', metadata) as trusted_secret_service:
            return self.locator.get_info('StatisticsInfo', trusted_secret_service.stat(params))
