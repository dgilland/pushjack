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
            config = Config()

        self.config = config

    def send(self, registration_id, alert, **options):
        """Send push notification to single recipient."""
        self.adapter.send(registration_id,
                          alert,
                          **options)
                                 self.config,

    def send_bulk(self, registration_ids, alert, **options):
        """Send push notification to multiple recipients."""
        self.adapter.send_bulk(registration_ids,
                               alert,
                               **options)
                                      self.config,


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
