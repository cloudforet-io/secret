import factory

from spaceone.core import utils
from spaceone.secret.model.trusted_secret_model import TrustedSecret


class TrustedSecretFactory(factory.mongoengine.MongoEngineFactory):

    class Meta:
        model = TrustedSecret

    trusted_secret_id = factory.LazyAttribute(lambda o: utils.generate_id('trusted-secret'))
    name = factory.LazyAttribute(lambda o: utils.random_string())
    schema = 'aws_access_key'
    provider = 'aws'
    encrypted = True
    encrypt_options = {
        'encrypt_algorithm': 'SPACEONE_DEFAULT',
        'encrypted_data_key': utils.random_string()
    }
    service_account_id = utils.generate_id('sa')
    domain_id = utils.generate_id('domain')
    created_at = factory.Faker('date_time')
