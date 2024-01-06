# Database Settings
DATABASE_AUTO_CREATE_INDEX = True
DATABASES = {
    "default": {
        # 'db': '',
        # 'host': '',
        # 'port': 0,
        # 'username': '',
        # 'password': '',
        # 'ssl': False,
        # 'ssl_ca_certs': ''
    }
}

# Cache Settings
CACHES = {
    "default": {},
    "local": {
        "backend": "spaceone.core.cache.local_cache.LocalCache",
        "max_size": 128,
        "ttl": 300,
    },
}

# Handler Settings
HANDLERS = {
    # "authentication": [{
    #     "backend": "spaceone.core.handler.authentication_handler:SpaceONEAuthenticationHandler"
    # }],
    # "authorization": [{
    #     "backend": "spaceone.core.handler.authorization_handler:SpaceONEAuthorizationHandler"
    # }],
    # "mutation": [{
    #     "backend": "spaceone.core.handler.mutation_handler:SpaceONEMutationHandler"
    # }],
    # "event": []
}

# Connector Settings
BACKEND = "AWSSecretManagerConnector"
CONNECTORS = {
    "SpaceConnector": {
        "backend": "spaceone.core.connector.space_connector:SpaceConnector",
        "endpoints": {"identity": "grpc://identity:50051"},
    },
    "AWSSecretManagerConnector": {},
    "VaultConnector": {
        # 'url': 'http://vault:8200',
        # 'token': 'myroot'
    },
    "ConsulConnector": {"host": "consul", "port": 8500},
    "EtcdConnector": {"host": "localhost", "port": 2379},
    "MongoDBConnector": {
        "host": "localhost",
        "port": 27017,
        "username": "",
        "password": "",
    },
}

LOG = {
    "filters": {
        "masking": {
            "rules": {
                "Secret.create": ["data"],
                "Secret.update_data": ["data"],
                "TrustedSecret.create": ["data"],
                "TrustedSecret.update_data": ["data"],
            }
        }
    }
}

# System Token Settings
TOKEN = ""
