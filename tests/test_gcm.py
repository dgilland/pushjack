# -*- coding: utf-8 -*-

import httmock
import mock
import pytest

from pushjack import (
    GCMClient,
    GCMError,
    exceptions
)
from pushjack.gcm import GCMConnection
from pushjack.utils import json_dumps

from .fixtures import (
    gcm_client,
    gcm_server_response,
    gcm_server_response_factory,
    parametrize
)


@parametrize('tokens,data,extra,message', [
    ('abc', 'Hello world', {},
     {'to': 'abc',
      'data': {'message': 'Hello world'}, 'priority': 'high'}),
    ('abc', 'Hello world', {'low_priority': True},
     {'to': 'abc',
      'data': {'message': 'Hello world'}}),
    ('abc', {'message': 'Hello world'}, {'delay_while_idle': True,
                                         'time_to_live': 3600,
                                         'collapse_key': 'key',
                                         'restricted_package_name': 'name',
                                         'dry_run': True},
     {'to': 'abc',
      'data': {'message': 'Hello world'},
      'delay_while_idle': True,
      'time_to_live': 3600,
      'collapse_key': 'key',
      'priority': 'high',
      'restricted_package_name': 'name',
      'dry_run': True}),
    ('abc',
     {'message': 'Hello world',
      'custom': {'key0': ['value0_0'],
                 'key1': 'value1',
                 'key2': {'key2_': 'value2_0'}}},
     {},
     {'to': 'abc',
      'data': {'message': 'Hello world',
               'custom': {'key0': ['value0_0'],
                          'key1': 'value1',
                          'key2': {'key2_': 'value2_0'}}},
      'priority': 'high'}),
    ('abc', 'Hello world', {'notification': {'title': 'Title',
                                             'body': 'Body',
                                             'icon': 'Icon'}},
     {'to': 'abc',
      'data': {'message': 'Hello world'},
      'priority': 'high',
      'notification': {'title': 'Title',
                       'body': 'Body',
                       'icon': 'Icon'}}),
    ('abc',
     {'message': 'Hello world',
      'notification': {'title': 'Title',
                       'body': 'Body',
                       'icon': 'Icon'}},
     {},
     {'to': 'abc',
      'data': {'message': 'Hello world'},
      'priority': 'high',
      'notification': {'title': 'Title',
                       'body': 'Body',
                       'icon': 'Icon'}}),
    (['abc', 'def', 'ghi'], 'Hello world', {},
     {'registration_ids': ['abc', 'def', 'ghi'],
      'data': {'message': 'Hello world'},
      'priority': 'high'}),
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
      'priority': 'high',
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
                          'key2': {'key2_': 'value2_0'}}},
      'priority': 'high'}),
])
def test_gcm_send(gcm_client, tokens, data, extra, message):
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
        assert res.messages == [message]
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
    gcm_client.api_key = None
    with pytest.raises(GCMError):
        gcm_client.send('abc', {})


@parametrize('tokens,data,extra,auth,expected', [
    ('abc',
     {},
     {},
     mock.call().headers.update({'Authorization': 'key=1234',
                                 'Content-Type': 'application/json'}),
     mock.call().post('https://fcm.googleapis.com/fcm/send',
                      b'{"data":{},"priority":"high","to":"abc"}')),
    (['abc'],
     {},
     {},
     mock.call().headers.update({'Authorization': 'key=1234',
                                 'Content-Type': 'application/json'}),
     mock.call().post('https://fcm.googleapis.com/fcm/send',
                      b'{"data":{},"priority":"high","to":"abc"}'))
])
def test_gcm_connection_call(gcm_client, tokens, data, extra, auth, expected):
    with mock.patch('requests.Session') as Session:
        gcm_client.send(tokens, data, **extra)
        assert auth in Session.mock_calls
        assert expected in Session.mock_calls
