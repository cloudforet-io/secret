from spaceone.core.pygrpc.server import GRPCServer
from spaceone.secret.interface.grpc.secret import Secret
from spaceone.secret.interface.grpc.user_secret import UserSecret
from spaceone.secret.interface.grpc.trusted_secret import TrustedSecret

_all_ = ["app"]

app = GRPCServer()
app.add_service(Secret)
app.add_service(UserSecret)
app.add_service(TrustedSecret)
