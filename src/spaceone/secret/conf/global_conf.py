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
    'IdentityConnector': {},
    'AWSSecretManagerConnector': {},
    'VaultConnector': {
       # 'url': 'http://vault:8200',
       # 'token': 'myroot'
    },
    'ConsulConnector': {
        'host': 'consul',
        'port': 8500
    }
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
                ]
            }
        }
    }
}
