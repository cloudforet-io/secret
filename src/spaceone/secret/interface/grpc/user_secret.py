from spaceone.api.secret.v1 import user_secret_pb2, user_secret_pb2_grpc
from spaceone.core.pygrpc import BaseAPI


class UserSecret(BaseAPI, user_secret_pb2_grpc.UserSecretServicer):
    pb2 = user_secret_pb2
    pb2_grpc = user_secret_pb2_grpc

    def create(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "UserSecretService", metadata
        ) as user_secret_service:
            return self.locator.get_info(
                "UserSecretInfo", user_secret_service.create(params)
            )

    def update(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "UserSecretService", metadata
        ) as user_secret_service:
            return self.locator.get_info(
                "UserSecretInfo", user_secret_service.update(params)
            )

    def delete(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "UserSecretService", metadata
        ) as user_secret_service:
            user_secret_service.delete(params)
            return self.locator.get_info("EmptyInfo")

    def update_data(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "UserSecretService", metadata
        ) as user_secret_service:
            user_secret_service.update_data(params)
            return self.locator.get_info("EmptyInfo")

    def get_data(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "UserSecretService", metadata
        ) as user_secret_service:
            user_secret_data = user_secret_service.get_data(params)
            return self.locator.get_info("UserSecretDataInfo", user_secret_data)

    def get(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "UserSecretService", metadata
        ) as user_secret_service:
            return self.locator.get_info(
                "UserSecretInfo", user_secret_service.get(params)
            )

    def list(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "UserSecretService", metadata
        ) as user_secret_service:
            user_secret_vos, total_count = user_secret_service.list(params)
            return self.locator.get_info(
                "UserSecretsInfo",
                user_secret_vos,
                total_count,
                minimal=self.get_minimal(params),
            )

    def stat(self, request, context):
        params, metadata = self.parse_request(request, context)

        with self.locator.get_service(
            "UserSecretService", metadata
        ) as user_secret_service:
            return self.locator.get_info(
                "StatisticsInfo", user_secret_service.stat(params)
            )
