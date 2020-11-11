import factory
from spaceone.core import utils
from spaceone.secret.model import Secret


class SecretFactory(factory.mongoengine.MongoEngineFactory):
    class Meta:
        model = Secret

    secret_id = utils.generate_id('secret')
    name = 'AWS Access Key'
    secret_type = 'credentials'
    tags = {}
    schema = None
    provider = None
    service_account_id = None
    project_id = None
    domain_id = utils.generate_id('domain')
    created_at = factory.Faker('date_time')


