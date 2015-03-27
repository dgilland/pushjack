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
    GCM_API_KEY = None
    GCM_URL = 'https://android.googleapis.com/gcm/send'

    # GCM only allows up to 1000 reg ids per bulk message. Set lower if needed,
    # but not higher.
    # https://developer.android.com/google/gcm/gcm.html#request
    GCM_MAX_RECIPIENTS = 1000


class APNSConfig(Config):
    """Configuration for APNS in production."""
    APNS_CERTIFICATE = None

    APNS_HOST = 'gateway.push.apple.com'
    APNS_PORT = 2195

    APNS_FEEDBACK_HOST = 'feedback.push.apple.com'
    APNS_FEEDBACK_PORT = 2196

    APNS_ERROR_TIMEOUT = 0.5
    APNS_DEFAULT_EXPIRATION_OFFSET = 60 * 60 * 24 * 30  # 1 month

    APNS_MAX_NOTIFICATION_SIZE = 2048


class APNSSandboxConfig(APNSConfig):
    """Configuration for APNS in sandbox mode."""
    APNS_HOST = 'gateway.sandbox.push.apple.com'
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
