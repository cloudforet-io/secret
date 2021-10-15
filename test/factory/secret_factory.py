import factory

from spaceone.core import utils
from spaceone.secret.model.secret_model import Secret, SecretTag


class SecretTagFactory(factory.mongoengine.MongoEngineFactory):

    class Meta:
        model = SecretTag

    key = utils.random_string()
    value = utils.random_string()


class SecretFactory(factory.mongoengine.MongoEngineFactory):

    class Meta:
        model = Secret

    secret_id = factory.LazyAttribute(lambda o: utils.generate_id('secret'))
    name = factory.LazyAttribute(lambda o: utils.random_string())
    secret_type = 'CREDENTIALS'
    schema = 'aws_access_key'
    provider = 'aws'
    encrypted = True
    encrypt_options = {
        'encrypt_algorithm': 'SPACEONE_DEFAULT',
        'encrypted_data_key': utils.random_string()
    }
    service_account_id = utils.generate_id('sa')
    project_id = utils.generate_id('project')
    domain_id = utils.generate_id('domain')
    created_at = factory.Faker('date_time')
