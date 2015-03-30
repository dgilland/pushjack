# -*- coding: utf-8 -*-
"""Client wrappers for push notification services.
"""

from . import apns
from . import gcm
from .config import Config


__all__ = (
    'APNSClient',
    'GCMClient',
)


class Client(object):
    """Base class for push notification clients."""
    #: Adapter module for push notification operations.
    adapter = None

    def __init__(self, config):
        if isinstance(config, type) and issubclass(config, Config):
            config = config()

        self.config = config

    def send(self, registration_id, data, **options):
        return self.adapter.send(registration_id,
                                 data,
                                 self.config,
                                 **options)

        """Send push notification to multiple recipients."""
    def send_bulk(self, registration_ids, data, **options):
        return self.adapter.send_bulk(registration_ids,
                                      data,
                                      self.config,
                                      **options)


class GCMClient(Client):
    """GCM client class."""
    #: GCM adapter.
    adapter = gcm


class APNSClient(Client):
    """APNS client class."""
    #: APNS adapter.
    adapter = apns

    def get_expired_tokens(self):
        return self.adapter.get_expired_tokens(self.config)
