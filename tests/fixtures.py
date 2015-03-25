# -*- coding: utf-8 -*-

import pytest
import mock

from pushjack import (
    APNSClient,
    GCMClient,
    create_apns_config,
    create_gcm_config
)

# pytest.mark is a generator so create alias for convenience
parametrize = pytest.mark.parametrize


@pytest.fixture
def apns():
    """Return APNS client."""
    return APNSClient(create_apns_config())


@pytest.fixture
def apns_sock():
    """Return mock for APNS socket client."""
    return mock.MagicMock()


@pytest.fixture
def gcm():
    """Return GCM client."""
    return GCMClient(create_gcm_config())


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
def gcm_dispatcher(gcm_response):
    """Return mock for GCM dispatcher function."""
    return mock.MagicMock(return_value=gcm_response)


@pytest.fixture
def gcm_failure_dispatcher(gcm_failure_response):
    """Return mock for GCM dispatcher function that returns failure."""
    return mock.MagicMock(return_value=gcm_failure_response)
