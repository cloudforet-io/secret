import logging
from pymongo import MongoClient
from spaceone.core.connector import BaseConnector


__all__ = ['MongoDBConnector']
_LOGGER = logging.getLogger(__name__)


class MongoDBConnector(BaseConnector):

    def __init__(self, transaction, config):
        super().__init__(transaction, config)
        client = MongoClient(**config)
        db = client.secret_data
        self.secret_data = db.secret_data

    def create_secret(self, secret_id, data):
        _document = {'secret_id': secret_id, 'data': data}
        return self.secret_data.insert_one(_document)

    def delete_secret(self, secret_id):
        self.secret_data.delete_one({'secret_id': secret_id})

    def update_secret(self, secret_id, data):
        _query = {'secret_id': secret_id}
        self.secret_data.update_one(_query, {'$set': {'data': data}})

    def get_secret(self, secret_id):
        secret_data_info = self.secret_data.find_one({'secret_id': secret_id})
        return secret_data_info.get('data', {})


