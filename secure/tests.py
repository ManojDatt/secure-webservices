# must be first:
from django.conf import settings
settings.configure(
    ROOT_URLCONF='webservices.tests',
    ALLOWED_HOSTS='*',
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        },
    },
)

# real import
import sys
from unittest import TestCase

from django.test.testcases import TestCase as DjangoTestCase
from webservice.exceptions import BadRequest, WebserviceError
from webservice.models import Provider, BaseConsumer, _split_dsn
from webservice.sync import (
    provider_for_flask,
    FlaskTestingConsumer,
    provider_for_django,
    DjangoTestingConsumer,
)


urlpatterns = []


class GreetingProvider(Provider):
    keys = {
        'pubkey': 'privatekey'
    }

    def __init__(self):
        self.exceptions = []

    def get_private_key(self, key):
        return self.keys.get(key)

    def report_exception(self):
        self.exceptions.append(sys.exc_info())

    def provide(self, data):
        if data.get('error'):
            raise Exception('Error')
        name = data.get('name', 'World')
        return {'greeting': u'Hello %s!' % name}


class GetFlaskTestingConsumer(FlaskTestingConsumer):
    def send_request(self, url, data, headers):  # pragma: no cover
        response = self.test_client.get(url, data=data, headers=headers)
        self.raise_for_status(response.status_code, response.data)
        return response.data


class BaseTests(TestCase):
    def test_consume_base_consumer(self):
        consumer = BaseConsumer('http://localhost', 'pubkey', 'privatekey')
        self.assertRaises(NotImplementedError,
                          consumer.consume, '/', {'name': 'Test'})

    def test_split_dsn(self):
        dsn = 'https://pub:priv@hostname.tld:1234/path'
        base_url, public_key, private_key = _split_dsn(dsn)
        self.assertEqual(base_url, 'https://hostname.tld:1234/path')
        self.assertEqual(public_key, 'pub')
        self.assertEqual(private_key, 'priv')


class FlaskTests(TestCase):
    def setUp(self):
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        self.provider = GreetingProvider()
        provider_for_flask(app, '/', self.provider)
        self.client = app.test_client()

    def test_greeting_provider(self):
        consumer = FlaskTestingConsumer(
            self.client, 'http://localhost', 'pubkey', 'privatekey')
        output = consumer.consume('/', {'name': 'Test'})
        self.assertEqual(output['greeting'], 'Hello Test!')

    def test_greeting_provider_wrong_key(self):
        consumer = FlaskTestingConsumer(
            self.client, 'http://localhost', 'pubkey', 'wrongkey')
        self.assertRaises(BadRequest, consumer.consume, '/', {'name': 'Test'})

    def test_starts_with_slash(self):
        consumer = FlaskTestingConsumer(
            self.client, 'http://localhost', 'pubkey', 'wrongkey')
        self.assertRaises(ValueError,
                          consumer.consume, 'wrong', {'name': 'Test'})

    def test_method_not_allowed(self):
        consumer = GetFlaskTestingConsumer(
            self.client, 'http://localhost', 'pubkey', 'wrongkey')
        self.assertRaises(WebserviceError,
                          consumer.consume, '/', {'name': 'Test'})

    def test_exception_hook(self):
        consumer = FlaskTestingConsumer(
            self.client, 'http://localhost', 'pubkey', 'privatekey')
        self.assertRaises(BadRequest, consumer.consume, '/', {'error': True})
        self.assertEqual(len(self.provider.exceptions), 1)


class DjangoTests(DjangoTestCase):
    def setUp(self):
        from django.test.client import Client
        self.client = Client()

    @property
    def urls(self):
        from django.conf.urls import url, patterns
        return patterns(
            '',
            url(r'^$', provider_for_django(GreetingProvider())),
        )

    def test_greeting_provider(self):
        consumer = DjangoTestingConsumer(
            self.client, 'http://localhost', 'pubkey', 'privatekey')
        output = consumer.consume('/', {'name': 'Test'})
        self.assertEqual(output['greeting'], 'Hello Test!')

    def test_greeting_provider_wrong_key(self):
        consumer = DjangoTestingConsumer(
            self.client, 'http://localhost', 'pubkey', 'wrongkey')
        self.assertRaises(BadRequest, consumer.consume, '/', {'name': 'Test'})