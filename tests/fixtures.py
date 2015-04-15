# -*- coding: utf-8 -*-

import binascii
from contextlib import contextmanager
import socket
import struct
import time

import pytest
import httmock
import mock

import pushjack
from pushjack import (
    APNSClient,
    GCMClient,
    create_apns_config,
    create_gcm_config
)
from pushjack.apns import APNS_ERROR_RESPONSE_COMMAND
from pushjack.utils import json_dumps, json_loads


# pytest.mark is a generator so create alias for convenience
parametrize = pytest.mark.parametrize


@pytest.fixture
def apns_client():
    """Return APNS client."""
    config = create_apns_config()
    config['APNS_ERROR_TIMEOUT'] = 0
    return APNSClient(config)


def apns_socket_factory(connect=None):
    sock = mock.MagicMock()
    sock._sock = socket.socket()
    if connect:
        sock._sock.connect(connect)
    sock.fileno = lambda: sock._sock.fileno()
    return sock


def apns_socket_error_factory(return_status):
    sock = apns_socket_factory()
    sock.read = lambda n: struct.pack('>BBI',
                                      APNS_ERROR_RESPONSE_COMMAND,
                                      return_status,
                                      0)
    return sock


def apns_feedback_socket_factory(tokens):
    data = {'stream': b''}

    for token in tokens:
        token = binascii.unhexlify(token)
        data['stream'] += struct.pack('!LH', int(time.time()), len(token))
        data['stream'] += struct.pack('{0}s'.format(len(token)), token)

    def read(n):
        out = data['stream'][:n]
        data['stream'] = data['stream'][n:]
        return out

    sock = apns_socket_factory()
    sock.read = read

    return sock


@contextmanager
def apns_create_socket(connect=('0.0.0.0', 8080)):
    with mock.patch('pushjack.apns.create_socket') as create_socket:
        create_socket.return_value = apns_socket_factory(connect)
        yield create_socket
        create_socket._sock.close()


@contextmanager
def apns_create_error_socket(code):
    with mock.patch('pushjack.apns.create_socket') as create_socket:
        error_sock = apns_socket_error_factory(code)
        create_socket.return_value = error_sock
        yield create_socket
        create_socket._sock.close()


def gcm_server_response_factory(content, status_code=200):
    @httmock.all_requests
    def response(url, request):
        headers = {'content-type': 'application/json'}
        return httmock.response(status_code,
                                content,
                                headers,
                                None,
                                1,
                                request)
    return response


@httmock.all_requests
def gcm_server_response(url, request):
    payload = json_loads(request.body)
    headers = {'content-type': 'application/json'}
    content = {
        'multicast_id': 1,
        'success': len(payload['registration_ids']),
        'failure': 0,
        'canonical_ids': 0,
        'results': []
    }

    content['results'] = [{'message_id': registration_id}
                          for registration_id in payload['registration_ids']]

    return httmock.response(200, content, headers, None, 1, request)


@pytest.fixture
def gcm_client():
    """Return GCM client."""
    return GCMClient(create_gcm_config({'GCM_API_KEY': '1234'}))
