# -*- coding: utf-8 -*-
"""Client wrappers for push notification services that provide a higher level
of abstration over the underlying lower-level service module.
"""

import time

from . import apns
from . import gcm
from . import exceptions
from .config import Config


__all__ = (
    'APNSClient',
    'GCMClient',
)


class ClientBase(object):
    """Base class for push notification clients."""
    #: Adapter module for push notification operations.
    adapter = None

    def __init__(self, config):
        if isinstance(config, type) and issubclass(config, Config):
            config = config()

        self.config = config
        self._conn = None

    @property
    def conn(self):
        """Lazily return connection."""
        if not self._conn:
            self._conn = self.create_connection()
        return self._conn

    def create_connection(self):  # pragma: no cover
        """Must be implemented in subclass."""
        raise NotImplementedError


class GCMClient(ClientBase):
    """GCM client class.

    Raises:
        GCMAuthError: If ``GCM_API_KEY`` not set in `config`.

    See Also:
        :mod:`pushjack.gcm`
    """
    def create_connection(self):
        """Return GCM connection based on :attr:`config`."""
        if not self.config['GCM_API_KEY']:
            raise exceptions.GCMAuthError(('Missing GCM API key. '
                                           'Cannot send notifications.'))
        return gcm.GCMConnection(self.config['GCM_API_KEY'],
                                 self.config['GCM_URL'])

    def send(self, ids, data, **options):
        """Send push notification to single or multiple recipients.

        Args:
            ids (str|list): List of device IDs to send notification to.
            data (str|dict): Notification data to send.

        Keyword Args:
            See service module for more details.

        Returns:
            :class:`pushjack.gcm.GCMResponse`

        See Also:
            :func:`pushjack.gcm.send`

        .. versionadded:: 0.0.1
        """
        return gcm.send(ids, data, self.conn, **options)


class APNSClient(ClientBase):
    """APNS client class.

    See Also:
        :mod:`pushjack.apns`
    """
    def create_connection(self):
        """Return APNS connection based on :attr:`config`."""
        return apns.APNSConnection(self.config['APNS_CERTIFICATE'],
                                   self.config['APNS_HOST'],
                                   self.config['APNS_PORT'])

    def close(self):
        """Close APNS connection."""
        self.conn.close()

    def send(self, ids, data, **options):
        """Send push notification to single or multiple recipients.

        Args:
            ids (str|list): Device ID(s) to send notification to.
            data (str|dict): Notification data to send.

        Keyword Args:
            See service module for more details.

        Returns:
            None

        See Also:
            :func:`pushjack.apns.send`

        .. versionadded:: 0.0.1
        """
        options.setdefault('expiration',
                           (int(time.time()) +
                            self.config['APNS_DEFAULT_EXPIRATION_OFFSET']))
        options.setdefault('batch_size',
                           self.config['APNS_DEFAULT_BATCH_SIZE'])
        options.setdefault('error_timeout',
                           self.config['APNS_DEFAULT_ERROR_TIMEOUT'])

        return apns.send(ids, data, self.conn, **options)

    def get_expired_tokens(self):
        """Return list of expired tokens.

        Returns:
            list: List of :class:`pushjack.apns.APNSExpiredToken`.

        .. versionadded:: 0.0.1
        """
        return apns.get_expired_tokens(self.conn)
