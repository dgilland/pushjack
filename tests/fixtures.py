# -*- coding: utf-8 -*-

import binascii
from contextlib import contextmanager
import hashlib
import socket
import struct
import threading
import time

try:
    # py3
    import socketserver
except ImportError:
    # py2
    import SocketServer as socketserver

import pytest
import httmock
import mock

import pushjack
from pushjack import (
    APNSClient,
    GCMClient,
)
from pushjack.apns import APNS_ERROR_RESPONSE_COMMAND
from pushjack.utils import json_dumps, json_loads


# pytest.mark is a generator so create alias for convenience
parametrize = pytest.mark.parametrize


TCP_HOST = '0.0.0.0'
TCP_PORT = 12345
TCP_CONNECT = (TCP_HOST, TCP_PORT)


class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(4096)


class TCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


class TCPClientServer(object):
    def __init__(self, connect=None):
        self.server = TCPServer(connect, TCPHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        self.client = socket.socket()
        self.client.connect(connect)

    def shutdown(self):
        self.client.close()
        self.server.server_close()
        self.server.shutdown()
        self.server_thread.join()


@pytest.fixture
def apns_client():
    """Return APNS client."""
    return APNSClient(certificate=None, default_error_timeout=0)


def apns_socket_factory(connect=None):
    sock = mock.MagicMock()

    if connect:
        sock._client_server = TCPClientServer(connect)
        sock._sock = sock._client_server.client
    else:
        sock._sock = socket.socket()

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


def apns_tokens(num=1):
    tokens = [hashlib.sha256(str(n).encode('utf8')).hexdigest()
              for n in range(num)]
    return tokens[0] if num == 1 else tokens


@pytest.fixture
def apns_socket():
    with mock.patch('pushjack.apns.create_socket') as create_socket:
        sock = apns_socket_factory(TCP_CONNECT)
        create_socket.return_value = sock

        yield create_socket()

        sock._client_server.shutdown()


@contextmanager
def apns_create_error_socket(code):
    with mock.patch('pushjack.apns.create_socket') as create_socket:
        sock = apns_socket_error_factory(code)
        create_socket.return_value = sock

        yield create_socket

        sock._sock.close()


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
    registration_ids = gcm_registration_ids(payload)
    content = {
        'multicast_id': 1,
        'success': len(registration_ids),
        'failure': 0,
        'canonical_ids': 0,
        'results': []
    }

    content['results'] = [{'message_id': registration_id}
                          for registration_id in registration_ids]

    return httmock.response(200, content, headers, None, 1, request)


@pytest.fixture
def gcm_client():
    """Return GCM client."""
    return GCMClient(api_key='1234')


def gcm_registration_ids(payload):
    if 'registration_ids' in payload:
        ids = payload['registration_ids']
    else:
        ids = [payload['to']]

    return ids
