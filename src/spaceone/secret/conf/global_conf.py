# -*- coding: utf-8 -*-

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
        'ttl': 86400
    }
}

HANDLERS = {}
ENCRYPT = False
ENCRYPT_TYPE = 'AWS_KMS'

CONNECTORS = {
    'IdentityConnector': {},
    'AWSSecretManagerConnector': {},
    'AWSKMSConnector': {
        # "aws_access_key_id":"",
        # "aws_secret_access_key":"",
        # "region_name" : "",
    },
    'VaultConnector': {
#        url = 'http://vault:8200',
#        token = 'myroot'
    }
}

ENDPOINTS = {}

LOG = {}

