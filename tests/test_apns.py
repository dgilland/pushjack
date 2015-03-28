# -*- coding: utf-8 -*-

import mock
import pytest

from pushjack import (
    APNSClient,
    APNSError,
    APNSDataOverflow,
    APNSConfig,
    create_apns_config,
    create_apns_sandbox_config
)
from pushjack.utils import json_dumps

from .fixtures import apns, apns_sock, parametrize


test_token = '1' * 64


@parametrize('token,alert,extra,expected', [
    (test_token,
     'Hello world',
     {'badge': 1,
      'sound': 'chime',
      'category': 'Pushjack',
      'content_available': True,
      'extra': {'custom_data': 12345},
      'expiration': 3},
     (json_dumps({'aps': {'alert': 'Hello world',
                          'badge': 1,
                          'sound': 'chime',
                          'category': 'Pushjack',
                          'content-available': 1},
                  'custom_data': 12345}),
      0, 3, 10)),
    (test_token,
     None,
     {'loc_key': 'lk',
      'action_loc_key': 'alk',
      'loc_args': 'la',
      'expiration': 3},
     (json_dumps({'aps': {'alert': {'action-loc-key': 'alk',
                                    'loc-args': 'la',
                                    'loc-key': 'lk'}}}),
      0, 3, 10)),
    (test_token,
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
    (test_token,
     'Hello world',
     {'title': 'title',
      'title_loc_key': 'tlk',
      'title_loc_args': 'tla',
      'launch_image': 'image',
      'expiration': 3},
     (json_dumps({'aps': {'alert': {'body': 'Hello world',
                                    'title': 'title',
                                    'title_loc_key': 'tlk',
                                    'title_loc_args': 'tla',
                                    'launch_image': 'image'}}}),
      0, 3, 10)),
])
def test_apns_send(apns, apns_sock, token, alert, extra, expected):
    with mock.patch('pushjack.apns.pack_frame') as pack_frame:
        apns.send(token, alert, sock=apns_sock, **extra)
        pack_frame.assert_called_once_with(token, *expected)


@parametrize('tokens,alert,extra,expected', [
    ([test_token] * 5,
     'Hello world',
     {'badge': 1,
      'sound': 'chime',
      'category': 'Pushjack',
      'content_available': True,
      'extra': {'custom_data': 12345},
      'expiration': 3},
     (json_dumps({'aps': {'alert': 'Hello world',
                          'badge': 1,
                          'sound': 'chime',
                          'category': 'Pushjack',
                          'content-available': 1},
                  'custom_data': 12345}),
      0, 3, 10)),
    ([test_token] * 5,
     None,
     {'loc_key': 'lk',
      'action_loc_key': 'alk',
      'loc_args': 'la',
      'expiration': 3},
     (json_dumps({'aps': {'alert': {'action-loc-key': 'alk',
                                    'loc-args': 'la',
                                    'loc-key': 'lk'}}}),
      0, 3, 10)),
    ([test_token] * 5,
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
    ([test_token] * 5,
     'Hello world',
     {'title': 'title',
      'title_loc_key': 'tlk',
      'title_loc_args': 'tla',
      'launch_image': 'image',
      'expiration': 3},
     (json_dumps({'aps': {'alert': {'body': 'Hello world',
                                    'title': 'title',
                                    'title_loc_key': 'tlk',
                                    'title_loc_args': 'tla',
                                    'launch_image': 'image'}}}),
      0, 3, 10)),
])
def test_apns_send_bulk(apns, apns_sock, tokens, alert, extra, expected):
    with mock.patch('pushjack.apns.create_push_socket') as create_socket:
        create_socket.return_value = apns_sock

        with mock.patch('pushjack.apns.pack_frame') as pack_frame:
            apns.send_bulk(tokens, alert, **extra)
            calls = [mock.call(token, expected[0], identifier, *expected[2:])
                     for identifier, token in enumerate(tokens)]
            pack_frame.assert_has_calls(calls)


@parametrize('token', [
    '1' * 64,
    'abcdef0123456789' * 4,
])
def test_valid_token(apns, token, apns_sock):
    apns.send(token, None, sock=apns_sock)
    assert apns_sock.write.called


@parametrize('token', [
    '1',
    'x' * 64,
])
def test_invalid_token(apns, token, apns_sock):
    with pytest.raises(APNSError) as exc_info:
        apns.send(token, None, sock=apns_sock)

    assert 'Invalid token format' in str(exc_info.value)


def test_apns_use_extra(apns, apns_sock):
    with mock.patch('pushjack.apns.pack_frame') as pack_frame:
        apns.send(test_token,
                  'sample',
                  extra={'foo': 'bar'},
                  identifier=10,
                  expiration=30,
                  priority=10,
                  sock=apns_sock)

        expected_payload = b'{"aps":{"alert":"sample"},"foo":"bar"}'
        pack_frame.assert_called_once_with(test_token,
                                           expected_payload,
                                           10,
                                           30,
                                           10)


def test_apns_socket_write(apns, apns_sock):
    apns.send(test_token,
              'sample',
              extra={'foo': 'bar'},
              identifier=10,
              expiration=30,
              priority=10,
              sock=apns_sock)

    expected = mock.call.write(
        b'\x02\x00\x00\x00^\x01\x00 \x11\x11\x11\x11\x11'
        b'\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11'
        b'\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11\x11'
        b'\x11\x11\x11\x11\x11\x02\x00&'
        b'{"aps":{"alert":"sample"},"foo":"bar"}'
        b'\x03\x00\x04\x00\x00\x00\n\x04\x00\x04\x00\x00'
        b'\x00\x1e\x05\x00\x01\n')

    assert expected in apns_sock.mock_calls


def test_apns_oversized_payload(apns, apns_sock):
    with mock.patch('pushjack.apns.pack_frame') as pack_frame:
        with pytest.raises(APNSDataOverflow):
            apns.send(test_token, '_' * 2049, sock=apns_sock)

        assert not pack_frame.called


def test_apns_config():
    config = create_apns_config()
    assert isinstance(config, dict)
    assert isinstance(config, APNSConfig)
    assert config['APNS_HOST'] == 'gateway.push.apple.com'
    assert config['APNS_PORT'] == 2195
    assert config['APNS_FEEDBACK_HOST'] == 'feedback.push.apple.com'
    assert config['APNS_FEEDBACK_PORT'] == 2196
    assert config['APNS_CERTIFICATE'] == None
    assert config['APNS_ERROR_TIMEOUT'] == 0.5
    assert config['APNS_DEFAULT_EXPIRATION_OFFSET'] == 60 * 60 * 24 * 30
    assert config['APNS_MAX_NOTIFICATION_SIZE'] == 2048


def test_apns_sandbox_config():
    config = create_apns_sandbox_config()
    assert isinstance(config, dict)
    assert isinstance(config, APNSConfig)
    assert config['APNS_HOST'] == 'gateway.sandbox.push.apple.com'
    assert config['APNS_PORT'] == 2195
    assert config['APNS_FEEDBACK_HOST'] == 'feedback.sandbox.push.apple.com'
    assert config['APNS_FEEDBACK_PORT'] == 2196
    assert config['APNS_CERTIFICATE'] == None
    assert config['APNS_ERROR_TIMEOUT'] == 0.5
    assert config['APNS_MAX_NOTIFICATION_SIZE'] == 2048


def test_apns_client_config_class():
    class TestAPNSConfig(APNSConfig):
        APNS_CERTIFICATE = 'certificate.pem'

    client = APNSClient(TestAPNSConfig)

    assert client.config['APNS_CERTIFICATE'] == TestAPNSConfig.APNS_CERTIFICATE
