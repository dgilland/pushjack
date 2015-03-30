# -*- coding: utf-8 -*-

import struct

import pytest
import mock

from pushjack import (
    APNSClient,
    GCMClient,
    create_apns_config,
    create_gcm_config
)

from pushjack.apns import APNS_ERROR_RESPONSE_COMMAND


# pytest.mark is a generator so create alias for convenience
parametrize = pytest.mark.parametrize


def apns_socket_factory(return_status):
    class MagicSocket(mock.MagicMock):
        def write(self, frame):
            self.frame = frame

    sock = mock.MagicMock()
    sock.recv = lambda n: struct.pack('!BBI',
                                      APNS_ERROR_RESPONSE_COMMAND,
                                      return_status,
                                      0)

    return sock


@pytest.fixture
def apns():
    """Return APNS client."""
    return APNSClient(create_apns_config())


@pytest.fixture
def apns_sock():
    """Return mock for APNS socket client."""
    sock = mock.MagicMock()
    sock.recv = lambda n: ''
    return sock


@pytest.fixture
def gcm():
    """Return GCM client."""
    return GCMClient(create_gcm_config({'GCM_API_KEY': '1234'}))


@pytest.fixture
def gcm_response():
    """Return mock for HTTP response."""
    response = mock.MagicMock()
    response.json = lambda: {}
    return response


@pytest.fixture
def gcm_failure_response():
    """Return mock for failure HTTP response."""
    response = mock.MagicMock()
    response.json = lambda: {'failure': True}
    return response


@pytest.fixture
def gcm_request(gcm_response):
    """Return mock for GCM request function."""
    return mock.MagicMock(return_value=gcm_response)


@pytest.fixture
def gcm_failure_request(gcm_failure_response):
    """Return mock for GCM request function that returns failure."""
    return mock.MagicMock(return_value=gcm_failure_response)
