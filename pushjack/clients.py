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

    def send(self, device_id, data, **options):
        """Send push notification to single recipient.

        Args:
            device_id (str): Device ID to send notification to.
            data (str|dict): Notification data to send.

        Keyword Args:
            See push notification service's module for more details.

        Returns:
            See push notification service's module for more details.

        .. versionadded:: 0.0.1
        """
        return self.adapter.send(device_id,
                                 data,
                                 self.config,
                                 **options)

    def send_bulk(self, device_ids, data, **options):
        """Send push notification to multiple recipients.

        Args:
            device_ids (list): List of device IDs to send notification
                to.
            data (str|dict): Notification data to send.

        Keyword Args:
            See push notification service's module for more details.

        Returns:
            See push notification service's module for more details.

        .. versionadded:: 0.0.1
        """
        return self.adapter.send_bulk(device_ids,
                                      data,
                                      self.config,
                                      **options)


class GCMClient(Client):
    """GCM client class.

    See Also:
        For more details on the supported keyword arguments of each method,
        consult:

        - :mod:`pushjack.gcm.send`
        - :mod:`pushjack.gcm.send_bulk`
    """
    #: GCM adapter.
    adapter = gcm


class APNSClient(Client):
    """APNS client class.

    See Also:
        For more details on the supported keyword arguments of each method,
        consult:

        - :mod:`pushjack.apns.send`
        - :mod:`pushjack.apns.send_bulk`
    """
    #: APNS adapter.
    adapter = apns

    def get_expired_tokens(self):
        """Return list of expired tokens.

        Returns:
            list: List of tuples containing ``(token, timestamp)``.

        .. versionadded:: 0.0.1
        """
        return self.adapter.get_expired_tokens(self.config)
