# -*- coding: utf-8 -*-
"""Lower level module for Apple Push Notification service.

The algorithm used to send bulk push notifications is optimized to eagerly
check for errors within a single thread. During bulk sending, error checking is
performed after each send and is non-blocking until the last notification is
sent. A final, blocking error check is performed using the timeout provided in
the configuration settings. This eager error checking is done to ensure that
no errors are missed (e.g. by waiting too long to check errors before the
connection is closed by the APNS server) without having to use two threads to
read and write on the socket.

Apple's documentation for APNS is available at:

- `Apple Push Notification Service <http://goo.gl/wFVr2S>`_
- `Provider Communication with APNS <http://goo.gl/qMfByr>`_
"""

from binascii import hexlify, unhexlify
from collections import namedtuple
import select
import socket
import ssl
import struct
import time

from .utils import json_dumps, compact_dict
from .exceptions import (
    APNSError,
    APNSAuthError,
    APNSInvalidTokenError,
    APNSInvalidPayloadSizeError,
    APNSServerError,
    raise_apns_server_error
)


__all__ = (
    'send',
    'get_expired_tokens',
    'APNSExpiredToken',
)


# Constants derived from http://goo.gl/wFVr2S
APNS_PUSH_COMMAND = 2
APNS_PUSH_FRAME_ITEM_COUNT = 5
APNS_PUSH_FRAME_ITEM_PREFIX_LEN = 3
APNS_PUSH_IDENTIFIER_LEN = 4
APNS_PUSH_EXPIRATION_LEN = 4
APNS_PUSH_PRIORITY_LEN = 1

APNS_ERROR_RESPONSE_COMMAND = 8
APNS_ERROR_RESPONSE_LEN = 6
APNS_FEEDBACK_HEADER_LEN = 6
APNS_MAX_NOTIFICATION_SIZE = 2048


class APNSExpiredToken(namedtuple('APNSExpiredToken', ['token', 'timestamp'])):
    """Represents an expired APNS token with the timestamp of when it expired.

    Attributes:
        token (str): Expired APNS token.
        timestamp (int): Epoch timestamp.
    """
    pass


class APNSPayload(object):
    """APNS payload object that serializes to JSON."""
    def __init__(self,
                 alert,
                 badge=None,
                 sound=None,
                 category=None,
                 content_available=None,
                 title=None,
                 title_loc_key=None,
                 title_loc_args=None,
                 action_loc_key=None,
                 loc_key=None,
                 loc_args=None,
                 launch_image=None,
                 extra=None):
        self.alert = alert
        self.badge = badge
        self.sound = sound
        self.category = category
        self.content_available = content_available
        self.title = title
        self.title_loc_key = title_loc_key
        self.title_loc_args = title_loc_args
        self.action_loc_key = action_loc_key
        self.loc_key = loc_key
        self.loc_args = loc_args
        self.launch_image = launch_image
        self.extra = extra

    def to_dict(self):
        """Return payload as dictionary."""
        payload = {}

        if any([self.title,
                self.title_loc_key,
                self.title_loc_args,
                self.action_loc_key,
                self.loc_key,
                self.loc_args,
                self.launch_image]):
            alert = {
                'body': self.alert,
                'title': self.title,
                'title-loc-key': self.title_loc_key,
                'title-loc-args': self.title_loc_args,
                'action-loc-key': self.action_loc_key,
                'loc-key': self.loc_key,
                'loc-args': self.loc_args,
                'launch-image': self.launch_image,
            }

            alert = compact_dict(alert)
        else:
            alert = self.alert

        payload.update(self.extra or {})
        payload['aps'] = compact_dict({
            'alert': alert,
            'badge': self.badge,
            'sound': self.sound,
            'category': self.category,
            'content-available': 1 if self.content_available else None
        })

        return payload

    def to_json(self):
        """Return payload as JSON string."""
        return json_dumps(self.to_dict())

    def __len__(self):
        """Return length of serialized payload."""
        return len(self.to_json())


class APNSPayloadStream(object):
    """Iterable object that yields a binary APNS socket frame for each device
    token.
    """
    def __init__(self, tokens, payload, expiration, priority):
        self.tokens = tokens
        self.payload = payload
        self.expiration = expiration
        self.priority = priority

    def __iter__(self):
        """Iterate through each device token and yield APNS socket frame."""
        payload = self.payload.to_json()

        for identifier, id_ in enumerate(self.tokens):
            yield pack_frame(id_,
                             identifier,
                             payload,
                             self.expiration,
                             self.priority)


class APNSFeedbackStream(object):
    """An iterable object that yields an expired device token."""
    def __init__(self, conn):
        self.conn = conn

    def __iter__(self):
        """Iterate through and yield expired device tokens."""
        header_format = '!LH'
        buff = b''

        for chunk in self.conn.readchunks(4096):
            buff += chunk

            if not buff:
                break

            if len(buff) < APNS_FEEDBACK_HEADER_LEN:  # pragma: no cover
                break

            while len(buff) > APNS_FEEDBACK_HEADER_LEN:
                timestamp, token_len = struct.unpack(header_format, buff[:6])
                bytes_to_read = APNS_FEEDBACK_HEADER_LEN + token_len

                if len(buff) >= bytes_to_read:
                    token = struct.unpack('{0}s'.format(token_len),
                                          buff[6:bytes_to_read])
                    token = hexlify(token[0]).decode('utf8')

                    yield APNSExpiredToken(token, timestamp)

                    buff = buff[bytes_to_read:]
                else:  # pragma: no cover
                    break


class APNSConnection(object):
    """Manager for APNS socket connection."""
    def __init__(self, host, port, certfile):
        self.host = host
        self.port = port
        self.certfile = certfile
        self.sock = None

    def connect(self):
        """Lazily connect to APNS server. Re-establish connection if previously
        closed.
        """
        if self.sock:
            return

        self.sock = create_socket(self.host, self.port, self.certfile)

    def close(self):
        """Disconnect from APNS server."""
        if self.sock:
            self.sock.close()
        self.sock = None

    @property
    def client(self):
        """Return client socket connection to APNS server."""
        self.connect()
        return self.sock

    def writable(self, timeout):
        """Return whether connection is writable."""
        try:
            return select.select([], [self.client], [], timeout)[1]
        except Exception:  # pragma: no cover
            self.close()
            raise

    def readable(self, timeout):
        """Return whether connection is readable."""
        try:
            return select.select([self.client], [], [], timeout)[0]
        except Exception:  # pragma: no cover
            self.close()
            raise

    def read(self, buffsize, timeout=10):
        """Return read data up to `buffsize`."""
        data = b''

        while True:
            if not self.readable(timeout):  # pragma: no cover
                self.close()
                raise socket.timeout

            chunk = self.client.read(buffsize - len(data))
            data += chunk

            if not chunk or len(data) >= buffsize or not timeout:
                # Either we've read all data or this is a nonblocking read.
                break

        return data

    def readchunks(self, buffsize, timeout=10):
        """Return stream of socket data in chunks <= `buffsize` until no more
        data found.
        """
        while True:
            data = self.read(buffsize, timeout)
            yield data

            if not data:  # pragma: no cover
                break

    def write(self, data, timeout=10):
        """Write data to socket."""
        if not self.writable(timeout):
            self.close()
            raise socket.timeout

        return self.client.sendall(data)

    def check_error(self, timeout=10):
        """Check for APNS errors."""
        if not self.readable(timeout):
            # No error response.
            return

        data = self.read(APNS_ERROR_RESPONSE_LEN, timeout=0)
        command = struct.unpack('>B', data[:1])[0]

        if command != APNS_ERROR_RESPONSE_COMMAND:  # pragma: no cover
            self.close()
            raise APNSServerError(('Error response command must be {0}. '
                                   'Found: {1}'
                                   .format(APNS_ERROR_RESPONSE_COMMAND,
                                           command)))

        status, identifier = struct.unpack('>BI', data[1:])

        self.close()
        raise_apns_server_error(status, identifier)

    def send(self, frames, error_timeout):
        """Send stream of frames to APNS server."""
        for frame in frames:
            self.check_error(0)
            self.write(frame)

        self.check_error(error_timeout)


def create_socket(host, port, certfile):
    """Create a socket connection to the APNS server."""
    try:
        with open(certfile, 'r') as fileobj:
            fileobj.read()
    except Exception as ex:
        raise APNSAuthError(('The certfile at {0} is not readable: {1}'
                             .format(certfile, ex)))

    sock = socket.socket()

    # For some reason, pylint on TravisCI's Python 2.7 platform complains that
    # ssl.PROTOCOL_TLSv1 doesn't exist. Add a disable flag to bypass this.
    # pylint: disable=no-member
    sock = ssl.wrap_socket(sock,
                           ssl_version=ssl.PROTOCOL_TLSv1,
                           certfile=certfile,
                           do_handshake_on_connect=False)
    sock.connect((host, port))

    sock.setblocking(0)
    do_ssl_handshake(sock)

    return sock


def do_ssl_handshake(sock):
    """Perform SSL socket handshake."""
    while True:
        try:
            sock.do_handshake()
            break
        except ssl.SSLError as ex:  # pragma: no cover
            # For some reason, pylint on TravisCI's Python 2.7 platform
            # complains that these members don't exist. Add a disable flag to
            # bypass this.
            # pylint: disable=no-member
            if ex.args[0] == ssl.SSL_ERROR_WANT_READ:
                select.select([sock], [], [])
            elif ex.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                select.select([], [sock], [])
            else:
                raise


def pack_frame(token, identifier, payload, expiration, priority):
    """Return a packed APNS socket frame for given token."""
    token_bin = unhexlify(token)
    token_len = len(token_bin)
    payload_len = len(payload)

    frame_len = calc_frame_length(token_len, payload_len)
    frame_fmt = '>BIBH{0}sBH{1}sBHIBHIBHB'.format(token_len, payload_len)

    # NOTE: Each bare int below is the corresponding frame item ID.
    frame = struct.pack(frame_fmt,
                        APNS_PUSH_COMMAND, frame_len,  # BI
                        1, token_len, token_bin,  # BH{token_len}s
                        2, payload_len, payload,  # BH{payload_len}s
                        3, APNS_PUSH_IDENTIFIER_LEN, identifier,  # BHI
                        4, APNS_PUSH_EXPIRATION_LEN, expiration,  # BHI
                        5, APNS_PUSH_PRIORITY_LEN, priority)  # BHB

    return frame


def calc_frame_length(token_len, payload_len):
    """Return frame length for given token and payload lengths."""
    # |CMD|FRAMELEN|{token}|{payload}|{id:4}|{expiration:4}|{priority:1}
    # 5 items, each 3 bytes prefix, then each item length
    return (APNS_PUSH_FRAME_ITEM_COUNT * APNS_PUSH_FRAME_ITEM_PREFIX_LEN +
            token_len +
            payload_len +
            APNS_PUSH_IDENTIFIER_LEN +
            APNS_PUSH_EXPIRATION_LEN +
            APNS_PUSH_PRIORITY_LEN)


def valid_token(token):
    """Return whether token is in valid format."""
    try:
        assert unhexlify(token)
        assert len(token) == 64
        valid = True
    except Exception:
        valid = False

    return valid


def invalid_tokens(tokens):
    """Return list of invalid APNS tokens."""
    return [token for token in tokens if not valid_token(token)]


def validate_tokens(tokens):
    """Check whether `tokens` are all valid."""
    invalid = invalid_tokens(tokens)

    if invalid:
        raise APNSInvalidTokenError(('Invalid token format. '
                                     'Expected 64 character hex string: '
                                     '{0}'.format(', '.join(invalid))))


def validate_payload(payload):
    """Check whether `payload` is valid."""
    if len(payload) > APNS_MAX_NOTIFICATION_SIZE:
        raise APNSInvalidPayloadSizeError(
            ('Notification body cannot exceed '
             '{0} bytes'
             .format(APNS_MAX_NOTIFICATION_SIZE)))


def send(ids,
         alert,
         config,
         expiration=None,
         priority=10,
         **options):
    """Send push notification to single device.

    Args:
        ids (list): APNS device tokens. Each item is expected to be a 64
            character hex string.
        alert (str|dict): Alert message or dictionary.
        config (dict): Configuration dictionary containing APNS configuration
            values. See :mod:`pushjack.config` for more details.
        expiration (int, optional): Expiration time of message in seconds
            offset from now. Defaults to ``None`` which uses
            ``config['APNS_DEFAULT_EXPIRATION_OFFSET']``.
        priority (int, optional): The alert’s priority. Provide one of the
            following values:

            - 10
                The push message is sent immediately. The remote notification
                must trigger an alert, sound, or badge on the device. It is an
                error to use this priority for a push that contains only the
                ``content_available`` key.
            - 5
                The push message is sent at a time that conserves power on the
                device receiving it.

            Defaults to ``10``.

    Keyword Args:
        badge (int, optional): Badge number count for alert. Defaults to
            ``None``.
        sound (str, optional): Name of the sound file to play for alert.
            Defaults to ``None``.
        category (str, optional): Name of category. Defaults to ``None``.
        content_available (bool, optional): If ``True``, indicate that new
            content is available. Defaults to ``None``.
        title (str, optional): Alert title.
        title_loc_key (str, optional): The key to a title string in the
            ``Localizable.strings`` file for the current localization.
        title_loc_args (list, optional): List of string values to appear in
            place of the format specifiers in `title_loc_key`.
        action_loc_key (str, optional): Display an alert that includes the
            ``Close`` and ``View`` buttons. The string is used as a key to get
            a localized string in the current localization to use for the right
            button’s title instead of ``“View”``.
        loc_key (str, optional): A key to an alert-message string in a
            ``Localizable.strings`` file for the current localization.
        loc_args (list, optional): List of string values to appear in place of
            the format specifiers in ``loc_key``.
        launch_image (str, optional): The filename of an image file in the app
            bundle; it may include the extension or omit it.
        extra (dict, optional): Extra data to include with the alert.

    Returns:
        None

    Raises:
        APNSInvalidTokenError: Invalid token format.
        APNSInvalidPayloadSizeError: Notification payload size too large.
        APNSServerError: APNS error response from server. See
            :mod:`pushjack.exceptions` for full listing.

    .. versionadded:: 0.0.1

    .. versionchanged:: 0.4.0

        - Added support for bulk sending.
        - Made sending and error checking non-blocking.
        - Removed `sock`, `payload`, and `identifer` arguments.
    """
    if not isinstance(ids, (list, tuple)):
        ids = [ids]

    payload = APNSPayload(alert, **options)

    validate_tokens(ids)
    validate_payload(payload)

    if expiration is None:
        expiration = (int(time.time()) +
                      config['APNS_DEFAULT_EXPIRATION_OFFSET'])

    conn = APNSConnection(config['APNS_HOST'],
                          config['APNS_PORT'],
                          config['APNS_CERTIFICATE'])
    conn.send(APNSPayloadStream(ids, payload, expiration, priority),
              config['APNS_ERROR_TIMEOUT'])
    conn.close()


def get_expired_tokens(config):
    """Return inactive device ids that can't be pushed to anymore.

    Args:
        config (dict): Configuration dictionary containing APNS configuration
            values. See :mod:`pushjack.config` for more details.
        conn (APNSConnection, optional): Provide APNSConnection instance.
            Connection is assumed to have been preconfigured and ready
            to use. Default is ``None``.

    Returns:
        list: List of :class:`APNSExpiredToken`.

    .. versionadded:: 0.0.1
    """
    conn = APNSConnection(config['APNS_FEEDBACK_HOST'],
                          config['APNS_FEEDBACK_PORT'],
                          config['APNS_CERTIFICATE'])
    expired = list(APNSFeedbackStream(conn))
    conn.close()

    return expired
