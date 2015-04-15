# -*- coding: utf-8 -*-

import httmock
import mock
import pytest

from pushjack import (
    GCMClient,
    GCMError,
    GCMConfig,
    create_gcm_config,
    exceptions
)
from pushjack.gcm import GCMRequest
from pushjack.utils import json_dumps

from .fixtures import (
    gcm_client,
    gcm_server_response,
    gcm_server_response_factory,
    parametrize
)


@parametrize('tokens,data,extra,payload', [
    ('abc', 'Hello world', {},
     {'registration_ids': ['abc'],
      'data': {'message': 'Hello world'}}),
    ('abc', {'message': 'Hello world'}, {'delay_while_idle': True,
                                         'time_to_live': 3600,
                                         'collapse_key': 'key',
                                         'restricted_package_name': 'name',
                                         'dry_run': True},
     {'registration_ids': ['abc'],
      'data': {'message': 'Hello world'},
      'delay_while_idle': True,
      'time_to_live': 3600,
      'collapse_key': 'key',
      'restricted_package_name': 'name',
      'dry_run': True}),
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
    (['abc', 'def', 'ghi'], 'Hello world', {},
     {'registration_ids': ['abc', 'def', 'ghi'],
      'data': {'message': 'Hello world'}}),
    (['abc', 'def', 'ghi'],
     {'message': 'Hello world'},
     {'delay_while_idle': True,
      'time_to_live': 3600,
      'collapse_key': 'key',
      'restricted_package_name': 'name',
      'dry_run': True},
     {'registration_ids': ['abc', 'def', 'ghi'],
      'data': {'message': 'Hello world'},
      'delay_while_idle': True,
      'time_to_live': 3600,
      'collapse_key': 'key',
      'restricted_package_name': 'name',
      'dry_run': True}),
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
def test_gcm_send(gcm_client, tokens, data, extra, payload):
    with httmock.HTTMock(gcm_server_response):
        res = gcm_client.send(tokens, data, **extra)

        if not isinstance(tokens, list):
            tokens = [tokens]

        assert len(res.responses) == 1
        assert res.registration_ids == tokens
        assert res.data == [{'multicast_id': 1,
                             'success': len(tokens),
                             'failure': 0,
                             'canonical_ids': 0,
                             'results': [{'message_id': token}
                                         for token in tokens]}]
        assert res.successes == tokens
        assert res.payloads == [payload]
        assert res.errors == []
        assert res.canonical_ids == []


@parametrize('tokens,status_code,results,expected', [
    ([1, 2, 3, 4, 5],
     200,
     [{'error': 'MissingRegistration'},
      {'message_id': 2},
      {'error': 'DeviceMessageRateExceeded'},
      {'message_id': 4, 'registration_id': 44},
      {'message_id': 5, 'registration_id': 55}],
     {'registration_ids': [1, 2, 3, 4, 5],
      'errors': [(exceptions.GCMMissingRegistrationError, 1),
                 (exceptions.GCMDeviceMessageRateExceededError, 3)],
      'failures': [1, 3],
      'successes': [2, 4, 5],
      'canonical_ids': [(4, 44), (5, 55)]}),
    ([1, 2, 3, 4, 5],
     500,
     [],
     {'registration_ids': [1, 2, 3, 4, 5],
      'errors': [(exceptions.GCMInternalServerError, 1),
                 (exceptions.GCMInternalServerError, 2),
                 (exceptions.GCMInternalServerError, 3),
                 (exceptions.GCMInternalServerError, 4),
                 (exceptions.GCMInternalServerError, 5)],
      'failures': [1, 2, 3, 4, 5],
      'successes': [],
      'canonical_ids': []}),
])
def test_gcm_response(gcm_client, tokens, status_code, results, expected):
    content = {'results': results}
    response = gcm_server_response_factory(content, status_code)

    with httmock.HTTMock(response):
        res = gcm_client.send(tokens, {})
        assert res.registration_ids == expected['registration_ids']
        assert res.failures == expected['failures']
        assert res.successes == expected['successes']
        assert res.canonical_ids == expected['canonical_ids']

        assert len(res.errors) == len(expected['errors'])

        for i, (ex_class, registration_id) in enumerate(expected['errors']):
            error = res.errors[i]
            assert isinstance(error, ex_class)
            assert error.identifier == registration_id


def test_gcm_invalid_api_key(gcm_client):
    gcm_client.config['GCM_API_KEY'] = None
    with pytest.raises(GCMError) as exc_info:
        gcm_client.send('abc', {})


def test_gcm_create_request():
    config = {
        'GCM_API_KEY': '1234',
        'GCM_URL': 'http://example.com'
    }

    request = GCMRequest(config)

    assert request.url == config['GCM_URL']
    assert request.session.auth == ('key', config['GCM_API_KEY'])
    assert request.session.headers['Content-Type'] == 'application/json'


@parametrize('method', [
    'send',
])
def test_gcm_create_request_when_sending(gcm_client, method):
    with mock.patch('pushjack.gcm.GCMRequest') as request:
        getattr(gcm_client, method)(['abc'], {})
        request.assert_called_with(gcm_client.config)


@parametrize('tokens,data,extra,expected', [
    ('abc',
     {},
     {},
     mock.call().post('https://android.googleapis.com/gcm/send',
                      b'{"data":{},"registration_ids":["abc"]}')),
    (['abc'],
     {},
     {},
     mock.call().post('https://android.googleapis.com/gcm/send',
                      b'{"data":{},"registration_ids":["abc"]}'))
])
def test_gcm_request_call(gcm_client, tokens, data, extra, expected):
    with mock.patch('requests.Session') as Session:
        gcm_client.send(tokens, data, **extra)
        assert expected in Session.mock_calls


def test_gcm_config():
    config = create_gcm_config()
    assert isinstance(config, dict)
    assert isinstance(config, GCMConfig)
    assert config['GCM_API_KEY'] is None
    assert config['GCM_URL'] == 'https://android.googleapis.com/gcm/send'


def test_gcm_client_config_class():
    class TestGCMConfig(GCMConfig):
        GCM_API_KEY = 'api_key'

    client = GCMClient(TestGCMConfig)

    assert client.config['GCM_API_KEY'] == TestGCMConfig.GCM_API_KEY
