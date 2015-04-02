# -*- coding: utf-8 -*-
"""Client wrappers for push notification services that provide a higher level
of abstration over the underlying lower-level service module.
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


class GCMClient(Client):
    """GCM client class.

    See Also:
        :mod:`pushjack.gcm`
    """
    #: GCM adapter.
    adapter = gcm

    def send(self, device_id, data, **options):
        """Send push notification to single recipient.

        Args:
            device_id (str): Device ID to send notification to.
            data (str|dict): Notification data to send.

        Keyword Args:
            See service module for more details.

        Returns:
            :class:`pushjack.gcm.GCMResponse`

        See Also:
            :func:`pushjack.gcm.send`

        .. versionadded:: 0.0.1
        """
        response = self.adapter.send(device_id,
                                     data,
                                     self.config,
                                     **options)

        return gcm.GCMResponse(response)

    def send_bulk(self, device_ids, data, **options):
        """Send push notification to multiple recipients.

        Args:
            device_ids (list): List of device IDs to send notification to.
            data (str|dict): Notification data to send.

        Keyword Args:
            See service module for more details.

        Returns:
            :class:`pushjack.gcm.GCMResponse`

        See Also:
            :func:`pushjack.gcm.send_bulk`

        .. versionadded:: 0.0.1
        """
        responses = self.adapter.send_bulk(device_ids,
                                           data,
                                           self.config,
                                           **options)

        return gcm.GCMResponse(responses)


class APNSClient(Client):
    """APNS client class.

    See Also:
        :mod:`pushjack.apns`
    """
    #: APNS adapter.
    adapter = apns

    def send(self, device_id, data, **options):
        """Send push notification to single recipient.

        Args:
            device_id (str): Device ID to send notification to.
            data (str|dict): Notification data to send.

        Keyword Args:
            See service module for more details.

        Returns:
            None

        See Also:
            :func:`pushjack.apns.send`

        .. versionadded:: 0.0.1
        """
        return self.adapter.send(device_id,
                                 data,
                                 self.config,
                                 **options)

    def send_bulk(self, device_ids, data, **options):
        """Send push notification to multiple recipients.

        Args:
            device_ids (list): List of device IDs to send notification to.
            data (str|dict): Notification data to send.

        Keyword Args:
            See service module for more details.

        Returns:
            None

        See Also:
            :func:`pushjack.apns.send_bulk`

        .. versionadded:: 0.0.1
        """
        return self.adapter.send_bulk(device_ids,
                                      data,
                                      self.config,
                                      **options)

    def get_expired_tokens(self, sock=None):
        """Return list of expired tokens.

        Returns:
            list: List of tuples containing ``(expired_token, timestamp)``.

        .. versionadded:: 0.0.1
        """
        return self.adapter.get_expired_tokens(self.config, sock=sock)
