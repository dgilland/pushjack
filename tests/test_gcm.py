# -*- coding: utf-8 -*-

import mock
import json

import pytest

from pushjack import GCMClient, GCMError, GCMConfig, create_gcm_config
from pushjack.gcm import Dispatcher
from pushjack.utils import json_dumps

from .fixtures import (
    gcm,
    gcm_response,
    gcm_failure_response,
    gcm_dispatcher,
    gcm_failure_dispatcher,
    parametrize
)


@parametrize('tokens,data,extra,expected', [
    ('abc', 'Hello world', {},
     {'registration_ids': ['abc'],
      'data': {'message': 'Hello world'}}),
    ('abc', {'message': 'Hello world'}, {'delay_while_idle': True,
                                         'time_to_live': 3600,
                                         'collapse_key': 'key'},
     {'registration_ids': ['abc'],
      'data': {'message': 'Hello world'},
      'delay_while_idle': True,
      'time_to_live': 3600,
      'collapse_key': 'key'}),
    ('abc',
     {'message': 'Hello world',
      'custom': {'key0': ['value0_0'],
                 'key1': 'value1',
                 'key2': {'key2_': 'value2_0'}}},
     {},
     {'registration_ids': ['abc'],
      'data': {'message': 'Hello world',
               'custom': {'key0': ['value0_0'],
                          'key1': 'value1',
                          'key2': {'key2_': 'value2_0'}}}}),
])
def test_gcm_send(gcm, gcm_dispatcher, tokens, data, extra, expected):
    gcm.send(tokens, data, dispatcher=gcm_dispatcher, **extra)
    gcm_dispatcher.assert_called_once_with(json_dumps(expected))


@parametrize('tokens,data,extra,expected', [
    (['abc', 'def', 'ghi'], 'Hello world', {},
     {'registration_ids': ['abc', 'def', 'ghi'],
      'data': {'message': 'Hello world'}}),
    (['abc', 'def', 'ghi'],
     {'message': 'Hello world'},
     {'delay_while_idle': True, 'time_to_live': 3600, 'collapse_key': 'key'},
     {'registration_ids': ['abc', 'def', 'ghi'],
      'data': {'message': 'Hello world'},
      'delay_while_idle': True,
      'time_to_live': 3600,
      'collapse_key': 'key'}),
    (['abc', 'def', 'ghi'],
     {'message': 'Hello world',
      'custom': {'key0': ['value0_0'],
                 'key1': 'value1',
                 'key2': {'key2_': 'value2_0'}}},
     {},
     {'registration_ids': ['abc', 'def', 'ghi'],
      'data': {'message': 'Hello world',
               'custom': {'key0': ['value0_0'],
                          'key1': 'value1',
                          'key2': {'key2_': 'value2_0'}}}}),
])
def test_gcm_send_bulk(gcm, gcm_dispatcher, tokens, data, extra, expected):
    gcm.send_bulk(tokens, data, dispatcher=gcm_dispatcher, **extra)
    gcm_dispatcher.assert_called_once_with(json_dumps(expected))


def test_gcm_send_failure(gcm, gcm_failure_dispatcher):
    with pytest.raises(GCMError):
        gcm.send('abc', {}, dispatcher=gcm_failure_dispatcher)


def test_gcm_invalid_api_key(gcm):
    gcm.config['GCM_API_KEY'] = None
    with pytest.raises(GCMError) as exc_info:
        gcm.send('abc', {})


def test_gcm_create_dispatcher():
    config = {
        'GCM_API_KEY': '1234',
        'GCM_URL': 'http://example.com'
    }

    dispatcher = Dispatcher(config)

    assert dispatcher.url == config['GCM_URL']
    assert dispatcher.session.auth == ('key', config['GCM_API_KEY'])
    assert dispatcher.session.headers['Content-Type'] == 'application/json'


@parametrize('method', [
    'send',
    'send_bulk'
])
def test_gcm_create_dispatcher_when_sending(gcm, method):
    with mock.patch('pushjack.gcm.Dispatcher') as dispatcher:
        getattr(gcm, method)(['abc'], {})
        dispatcher.assert_called_with(gcm.config)


@parametrize('method,tokens,data,extra,expected', [
    ('send',
     'abc',
     {},
     {},
     mock.call().post('https://android.googleapis.com/gcm/send',
                      b'{"data":{},"registration_ids":["abc"]}')),
    ('send_bulk',
     ['abc'],
     {},
     {},
     mock.call().post('https://android.googleapis.com/gcm/send',
                      b'{"data":{},"registration_ids":["abc"]}'))
])
def test_gcm_dispatcher_call(gcm, method, tokens, data, extra, expected):
    with mock.patch('requests.Session') as Session:
        getattr(gcm, method)(tokens, data, **extra)

        assert expected in Session.mock_calls


def test_gcm_config():
    config = create_gcm_config()
    assert isinstance(config, dict)
    assert isinstance(config, GCMConfig)
    assert config['GCM_API_KEY'] is None
    assert config['GCM_URL'] == 'https://android.googleapis.com/gcm/send'
    assert config['GCM_MAX_RECIPIENTS'] == 1000


def test_gcm_client_config_class():
    class TestGCMConfig(GCMConfig):
        GCM_API_KEY = 'api_key'

    client = GCMClient(TestGCMConfig)

    assert client.config['GCM_API_KEY'] == TestGCMConfig.GCM_API_KEY
