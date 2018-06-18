# -*- coding: utf-8 -*-

import datetime
import socket

import mock
import pytest

from pushjack import (
    apns,
    exceptions
)
from pushjack.utils import json_dumps

from .fixtures import (
    apns_client,
    apns_feedback_socket_factory,
    apns_create_error_socket,
    apns_socket,
    apns_tokens,
    parametrize,
    TCP_HOST,
    TCP_PORT
)


@parametrize('tokens,alert,extra,expected', [
    (apns_tokens(1),
     'Hello world',
     {'badge': 1,
      'sound': 'chime',
      'category': 'Pushjack',
      'content_available': True,
      'extra': {'custom_data': 12345},
      'expiration': 3,
      'low_priority': True},
     (json_dumps({'aps': {'alert': 'Hello world',
                          'badge': 1,
                          'sound': 'chime',
                          'category': 'Pushjack',
                          'content-available': 1},
                  'custom_data': 12345}),
      0, 3, 5)),
    (apns_tokens(1),
     None,
     {'loc_key': 'lk',
      'action_loc_key': 'alk',
      'loc_args': 'la',
      'expiration': 3},
     (json_dumps({'aps': {'alert': {'action-loc-key': 'alk',
                                    'loc-args': 'la',
                                    'loc-key': 'lk'}}}),
      0, 3, 10)),
    (apns_tokens(5),
     'Hello world',
     {'loc_key': 'lk',
      'action_loc_key': 'alk',
      'loc_args': 'la',
      'expiration': 3},
     (json_dumps({'aps': {'alert': {'body': 'Hello world',
                                    'action-loc-key': 'alk',
                                    'loc-args': 'la',
                                    'loc-key': 'lk'}}}),
      0, 3, 10)),
    (apns_tokens(5),
     'Hello world',
     {'title': 'title',
      'title_loc_key': 'tlk',
      'title_loc_args': 'tla',
      'launch_image': 'image',
      'expiration': 3},
     (json_dumps({'aps': {'alert': {'body': 'Hello world',
                                    'title': 'title',
                                    'title-loc-key': 'tlk',
                                    'title-loc-args': 'tla',
                                    'launch-image': 'image'}}}),
      0, 3, 10)),
])
def test_apns_send(apns_client, apns_socket, tokens, alert, extra, expected):
    with mock.patch('pushjack.apns.APNSMessageStream.pack') as pack_frame:
        apns_client.send(tokens, alert, **extra)

        if not isinstance(tokens, list):
            tokens = [tokens]

        for identifier, token in enumerate(tokens):
            call = mock.call(token, identifier, expected[0], *expected[2:])
            assert call in pack_frame.mock_calls

        apns_client.close()


@parametrize('tokens,identifiers,exception', [
    (apns_tokens(50), [1], exceptions.APNSProcessingError),
    (apns_tokens(50), [1, 5, 7], exceptions.APNSProcessingError),
    (apns_tokens(500), [1, 5, 99, 150, 210], exceptions.APNSProcessingError),
])
def test_apns_resend(apns_client, apns_socket, tokens, identifiers, exception):
    tracker = {'errors': []}

    def sendall(data):
        for ident in identifiers:
            if ident not in tracker['errors']:
                tracker['errors'].append(ident)
                raise exceptions.APNSProcessingError(ident)

    apns_socket.sendall = sendall

    res = apns_client.send(tokens, 'foo')

    expected_failures = [token for i, token in enumerate(tokens)
                         if i in identifiers]
    expected_successes = [token for i, token in enumerate(tokens)
                          if i not in identifiers]

    assert isinstance(res, apns.APNSResponse)
    assert res.tokens == tokens
    assert isinstance(res.message, apns.APNSMessage)
    assert all([isinstance(error, exception) for error in res.errors])
    assert res.failures == expected_failures
    assert res.successes == expected_successes
    assert set(res.failures) == set(res.token_errors.keys())
    assert set(res.errors) == set(res.token_errors.values())


@parametrize('token', [
    '1' * 64,
    '1' * 108,
    'abcdef0123456789' * 4,
])
def test_valid_token(apns_client, apns_socket, token):
    apns_client.send(token, '')
    assert apns_socket.sendall.called


@parametrize('token', [
    '1',
    'x' * 64,
    'x' * 108,
])
def test_invalid_token(apns_client, apns_socket, token):
    with pytest.raises(exceptions.APNSInvalidTokenError) as exc_info:
        apns_client.send(token, '')

    assert 'Invalid token format' in str(exc_info.value)


def test_apns_use_extra(apns_client, apns_socket):
    test_token = apns_tokens(1)

    with mock.patch('pushjack.apns.APNSMessageStream.pack') as pack_frame:
        apns_client.send(test_token,
                         'sample',
                         extra={'foo': 'bar'},
                         expiration=30)

        expected_payload = b'{"aps":{"alert":"sample"},"foo":"bar"}'
        pack_frame.assert_called_once_with(test_token,
                                           0,
                                           expected_payload,
                                           30,
                                           10)


def test_apns_socket_write(apns_client, apns_socket):
    apns_client.send('1' * 64,
                     'sample',
                     extra={'foo': 'bar'},
                     expiration=30)

    expected = mock.call.sendall(
        b'\x02\x00\x00\x00^\x01\x00 \x11\x11\x11\x11\x11'
        b'\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11'
        b'\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11'
        b'\x11\x11\x11\x11\x11\x02\x00&'
        b'{"aps":{"alert":"sample"},"foo":"bar"}'
        b'\x03\x00\x04\x00\x00\x00\x00\x04\x00\x04\x00\x00'
        b'\x00\x1e\x05\x00\x01\n')

    assert expected in apns_socket.mock_calls


@parametrize('exception,alert', [
    (exceptions.APNSInvalidPayloadSizeError, '_' * 2049),
])
def test_apns_invalid_payload_size(apns_client, exception, alert):
    with mock.patch('pushjack.apns.APNSMessageStream.pack') as pack_frame:
        with pytest.raises(exception):
            apns_client.send(apns_tokens(1), alert)

        assert not pack_frame.called


@parametrize('alert', [
    ('_' * 2049),
])
def test_apns_max_payload_length(apns_client, apns_socket, alert):
    with mock.patch('pushjack.apns.APNSMessageStream.pack') as pack_frame:
        apns_client.send(apns_tokens(1), alert, max_payload_length=2048)
        assert pack_frame.called
        apns_client.close()


@parametrize('code,exception', [
    (1, exceptions.APNSProcessingError),
    (2, exceptions.APNSMissingTokenError),
    (3, exceptions.APNSMissingTopicError),
    (4, exceptions.APNSMissingPayloadError),
    (5, exceptions.APNSInvalidTokenSizeError),
    (6, exceptions.APNSInvalidTopicSizeError),
    (7, exceptions.APNSInvalidPayloadSizeError),
    (8, exceptions.APNSInvalidTokenError),
    (10, exceptions.APNSShutdownError),
    (255, exceptions.APNSUnknownError),
])
def test_apns_error_handling(apns_client, code, exception):
    with apns_create_error_socket(code):
        res = apns_client.send(apns_tokens(1), 'foo')
        assert isinstance(res.errors[0], exception)


def test_apns_send_timeout_error(apns_client):
    def throw(*args, **kargs):
        raise socket.error('socket error')

    with mock.patch.object(apns_client.conn, 'write', side_effect=throw):
        res = apns_client.send(apns_tokens(1), 'foo')

    assert isinstance(res.errors[0], exceptions.APNSTimeoutError)


@parametrize('tokens', [
    ['1' * 64, '2' * 64, '3' * 64],
])
def test_apns_get_expired_tokens(apns_client, tokens):
    with mock.patch('pushjack.apns.create_socket') as create_socket:
        create_socket.return_value = apns_feedback_socket_factory(tokens)
        expired_tokens = apns_client.get_expired_tokens()

        assert len(expired_tokens) == len(tokens)

        for i, token in enumerate(tokens):
            expired_token, timestamp = expired_tokens[i]

            assert expired_token == token
            assert (datetime.datetime.utcfromtimestamp(timestamp) <
                    datetime.datetime.utcnow())


def test_apns_create_socket(tmpdir):
    certificate = tmpdir.join('certifiate.pem')
    certificate.write('content')

    with mock.patch('ssl.wrap_socket') as wrap_socket:
        wrap_socket.do_handshake = lambda: True

        apns.create_socket(TCP_HOST, TCP_PORT, str(certificate))

        assert wrap_socket.called

        expected = {'ssl_version': 3,
                    'certfile': str(certificate),
                    'do_handshake_on_connect': False}

        assert wrap_socket.mock_calls[0][2] == expected


def test_apns_create_socket_missing_certificate():
    with pytest.raises(exceptions.APNSAuthError):
        apns.create_socket(TCP_HOST, TCP_PORT, 'missing.pem')


def test_apns_create_socket_no_certificate():
    with pytest.raises(exceptions.APNSAuthError):
        apns.create_socket(TCP_HOST, TCP_PORT, None)


def test_apns_create_socket_empty_certificate(tmpdir):
    certificate = tmpdir.join('certificate.pem')

    with pytest.raises(exceptions.APNSAuthError):
        apns.create_socket(TCP_HOST, TCP_PORT, str(certificate))
