# -*- coding: utf-8 -*-
"""Configuration module that provides configuration classes for use with push
notification services.
"""

from . import apns
from . import gcm
from ._compat import iteritems


__all__ = (
    'APNSConfig',
    'APNSSandboxConfig',
    'GCMConfig',
    'create_apns_config',
    'create_apns_sandbox_config',
    'create_gcm_config',
)


class Config(dict):
    """Configuration loader which acts like a dict but supports loading
    values from an object limited to ``ALL_CAPS_ATTRIBUTES``.
    """
    def __init__(self, config=None):
        self.from_object(self)
        self.update(config or {})

    def from_object(self, obj):
        """Pull ``dir(obj)`` keys from `obj` and set onto ``self``."""
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)

    def update(self, dct):
        """Pull keys from `dct` and set onto ``self``."""
        for key, value in iteritems(dct):
            if key.isupper():
                self[key] = value


class GCMConfig(Config):
    """Configuration for GCM in production."""
    #: GCM API key.
    GCM_API_KEY = None

    #: GCM push server URL.
    GCM_URL = gcm.GCM_URL


class APNSConfig(Config):
    """Configuration for APNS in production."""
    #: Path to APNS certificate file.
    APNS_CERTIFICATE = None

    #: APNS production push server host.
    APNS_HOST = apns.APNS_HOST
    #: APNS production push server port.
    APNS_PORT = apns.APNS_PORT

    #: APNS production feedback server host.
    APNS_FEEDBACK_HOST = apns.APNS_FEEDBACK_HOST
    #: APNS production feedback port host.
    APNS_FEEDBACK_PORT = apns.APNS_FEEDBACK_PORT

    #: Default timeout used when performing error checking after sending is
    #: complete. During sending a non-blocking poll cycle is used for error
    #: checking after each notification batch is sent. If no error is
    #: immediately available, then sending continues uninterrupted.
    APNS_DEFAULT_ERROR_TIMEOUT = apns.APNS_DEFAULT_ERROR_TIMEOUT

    #: Default message expiration to set when not provided.
    APNS_DEFAULT_EXPIRATION_OFFSET = apns.APNS_DEFAULT_EXPIRATION_OFFSET

    #: Number of notications to group together when sending a bulk
    #: notification to many recipients. This default value is set
    #: conservatively low. There is no hard-and-fast rule on what the optimal
    #: value for this should be. Having too large a value could cause issues
    #: related to TCP socket buffering, though.
    APNS_DEFAULT_BATCH_SIZE = apns.APNS_DEFAULT_BATCH_SIZE


class APNSSandboxConfig(APNSConfig):
    """Configuration for APNS in sandbox mode."""
    #: APNS sandbox push server host.
    APNS_HOST = apns.APNS_SANDBOX_HOST

    #: APNS sandbox feedback server host.
    APNS_FEEDBACK_HOST = apns.APNS_FEEDBACK_SANDBOX_HOST


def create_gcm_config(config=None):
    """Convenience method to create a GCM config."""
    return GCMConfig(config)


def create_apns_config(config=None):
    """Convenience method to create an APNS config."""
    return APNSConfig(config)


def create_apns_sandbox_config(config=None):
    """Convenience method to create an APNS sandbox config."""
    return APNSSandboxConfig(config)
