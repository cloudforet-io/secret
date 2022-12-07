DATABASE_AUTO_CREATE_INDEX = True
DATABASES = {
    'default': {
        'db': 'secret',
        'host': 'localhost',
        'port': 27017,
        'username': '',
        'password': ''
    }
}

CACHES = {
    'default': {},
    'local': {
        'backend': 'spaceone.core.cache.local_cache.LocalCache',
        'max_size': 128,
        'ttl': 300
    }
}

HANDLERS = {}

BACKEND = ""
CONNECTORS = {
    'SpaceConnector': {
        'backend': 'spaceone.core.connector.space_connector.SpaceConnector',
        'endpoints': {
            'identity': 'grpc://identity:50051'
        }
    },
    'AWSSecretManagerConnector': {},
    'VaultConnector': {
       # 'url': 'http://vault:8200',
       # 'token': 'myroot'
    },
    'ConsulConnector': {
        'host': 'consul',
        'port': 8500
    },
    'EtcdConnector': {
        'host': 'localhost',
        'port': 2379
    },
    'MongoDBConnector': {
        'host': 'localhost',
        'port': 27017,
        'username': '',
        'password': ''
    },
}

ENDPOINTS = {}

LOG = {
    'filters': {
        'masking': {
            'rules': {
                'Secret.create': [
                    'data'
                ],
                'Secret.update_data': [
                    'data'
                ],
                'TrustedSecret.create': [
                    'data'
                ],
                'TrustedSecret.update_data': [
                    'data'
                ]
            }
        }
    }
}
