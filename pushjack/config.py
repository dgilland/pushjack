# -*- coding: utf-8 -*-
"""Configuration module that provides configuration classes for use with push
notification services.
"""

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
    GCM_URL = 'https://android.googleapis.com/gcm/send'


class APNSConfig(Config):
    """Configuration for APNS in production."""
    #: Path to APNS certificate file.
    APNS_CERTIFICATE = None

    #: APNS production push server host.
    APNS_HOST = 'gateway.push.apple.com'
    #: APNS production push server port.
    APNS_PORT = 2195

    #: APNS production feedback server host.
    APNS_FEEDBACK_HOST = 'feedback.push.apple.com'
    #: APNS production feedback port host.
    APNS_FEEDBACK_PORT = 2196

    #: Timeout used when performing error checking after sending is complete.
    #: During sending a non-blocking poll cycle is used for error checking
    #: after each notification batch is sent. If no error is immediately
    #: available, then sending continues uninterrupted.
    APNS_ERROR_TIMEOUT = 10

    #: Default message expiration to set when not provided.
    APNS_DEFAULT_EXPIRATION_OFFSET = 60 * 60 * 24 * 30  # 1 month

    #: Number of notications to group together when sending a bulk
    #: notification to many recipients. This default value is set
    #: conservatively low. There is no hard-and-fast rule on what the optimal
    #: value for this is. Having too large a value could cause issues related
    #: to TCP socket buffering, though.
    APNS_DEFAULT_BATCH_SIZE = 100


class APNSSandboxConfig(APNSConfig):
    """Configuration for APNS in sandbox mode."""
    #: APNS sandbox push server host.
    APNS_HOST = 'gateway.sandbox.push.apple.com'

    #: APNS sandbox feedback server host.
    APNS_FEEDBACK_HOST = 'feedback.sandbox.push.apple.com'


def create_gcm_config(config=None):
    """Convenience method to create a GCM config."""
    return GCMConfig(config)


def create_apns_config(config=None):
    """Convenience method to create an APNS config."""
    return APNSConfig(config)


def create_apns_sandbox_config(config=None):
    """Convenience method to create an APNS sandbox config."""
    return APNSSandboxConfig(config)
