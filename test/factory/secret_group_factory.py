import factory

from spaceone.core import utils
from spaceone.secret.model.secret_group_model import SecretGroup, SecretGroupTag


class SecretGroupTagFactory(factory.mongoengine.MongoEngineFactory):

    class Meta:
        model = SecretGroupTag

    key = utils.random_string()
    value = utils.random_string()


class SecretGroupFactory(factory.mongoengine.MongoEngineFactory):

    class Meta:
        model = SecretGroup

    secret_group_id = factory.LazyAttribute(lambda o: utils.generate_id('secret-grp'))
    name = factory.LazyAttribute(lambda o: utils.random_string())
    domain_id = utils.generate_id('domain')
    created_at = factory.Faker('date_time')
