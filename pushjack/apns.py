# -*- coding: utf-8 -*-
"""Apple Push Notification Service

Documentation is available on the iOS Developer Library:

http://goo.gl/wFVr2S
"""

from binascii import unhexlify
from contextlib import closing
import socket
import ssl
import struct
import time

from .utils import json_dumps
from .exceptions import APNSError, APNSDataOverflow, raise_apns_server_error


__all__ = (
    'send',
    'send_bulk',
)


# Apple protocol says command is always 8. See http://goo.gl/ENUjXg
APNS_ERROR_RESPONSE_COMMAND = 8

# 1 month
DEFAULT_EXPIRATION_OFFSET = 60 * 60 * 24 * 30


def is_valid_token(token):
    """Check if token is valid format."""
    try:
        assert unhexlify(token)
        assert len(token) == 64
        valid = True
    except Exception:
        valid = False

    return valid


def create_payload(alert,
                   badge=None,
                   sound=None,
                   category=None,
                   content_available=None,
                   action_loc_key=None,
                   loc_key=None,
                   loc_args=None,
                   extra=None):
    """Return notification payload in JSON format."""
    if loc_args is None:
        loc_args = []

    if extra is None:
        extra = {}

    data = {}
    aps_data = {}

    if any([action_loc_key, loc_key, loc_args]):
        alert = {'body': alert} if alert else {}

        if action_loc_key:
            alert['action-loc-key'] = action_loc_key

        if loc_key:
            alert['loc-key'] = loc_key

        if loc_args:
            alert['loc-args'] = loc_args

    if alert is not None:
        aps_data['alert'] = alert

    if badge is not None:
        aps_data['badge'] = badge

    if sound is not None:
        aps_data['sound'] = sound

    if category is not None:
        aps_data['category'] = category

    if content_available:
        aps_data['content-available'] = 1

    data['aps'] = aps_data
    data.update(extra)

    return json_dumps(data)


def create_socket(host, port, certfile):
    """Create a socket connection to the APNS server."""
    if not certfile:
        raise APNSError('Missing certfile. Cannot send notifications.')

    try:
        with open(certfile, 'r') as f:
            f.read()
    except Exception as ex:
        raise APNSError(('The certfile at {0} is not readable: {1}'
                        .format(certfile, ex)))

    sock = socket.socket()
    sock = ssl.wrap_socket(sock,
                           ssl_version=ssl.PROTOCOL_TLSv1,
                           certfile=certfile)
    sock.connect((host, port))

    return sock


def create_push_socket(settings):
    """Return socket connection to push server."""
    return create_socket(settings['APNS_HOST'],
                         settings['APNS_PORT'],
                         settings['APNS_CERTIFICATE'])


def create_feedback_socket(settings):
    """Return socket connection to feedback server."""
    return create_socket(settings['APNS_FEEDBACK_HOST'],
                         settings['APNS_FEEDBACK_PORT'],
                         settings['APNS_CERTIFICATE'])


def check_errors(sock, settings):
    """Check socket response for errors and raise status based exception if
    found.
    """
    timeout = settings['APNS_ERROR_TIMEOUT']

    if timeout is None:
        # Assume everything went fine.
        return

    original_timeout = sock.gettimeout()

    try:
        sock.settimeout(timeout)
        data = sock.recv(6)

        if data:
            command, status, identifier = struct.unpack("!BBI", data)

            if command != APNS_ERROR_RESPONSE_COMMAND:
                raise APNSError(('Error response command must be {0}. '
                                 'Found: {1}'
                                 .format(APNS_ERROR_RESPONSE_COMMAND,
                                         command)))

            if status != 0:
                raise_apns_server_error(status, identifier)

    except socket.timeout:
        # py3, See http://bugs.python.org/issue10272
        pass
    except ssl.SSLError as ex:
        # py2
        if 'timed out' not in ex.message:
            raise
    finally:
        sock.settimeout(original_timeout)


def pack_frame(token, payload, identifier, expiration, priority):
    """Return packed socket frame."""
    token_bin = unhexlify(token)
    token_len = len(token_bin)
    payload_len = len(payload)

    # |COMMAND|FRAME-LEN|{token}|{payload}|{id:4}|{expiration:4}|{priority:1}
    # 5 items, each 3 bytes prefix, then each item length
    frame_len = 3 * 5 + token_len + payload_len + 4 + 4 + 1
    frame_fmt = '!BIBH{0}sBH{1}sBHIBHIBHB'.format(token_len, payload_len)
    frame = struct.pack(frame_fmt,
                        2, frame_len,
                        1, token_len, token_bin,
                        2, payload_len, payload,
                        3, 4, identifier,
                        4, 4, expiration,
                        5, 1, priority)

    return frame


def read_and_unpack(sock, data_format):
    """Unpack and return socket frame."""
    length = struct.calcsize(data_format)
    data = sock.recv(length)

    if data:
        return struct.unpack_from(data_format, data, 0)
    else:
        return None


def receive_feedback(sock):
    """Return expired tokens from feedback server."""
    expired_tokens = []

    # Read a timestamp (4 bytes) and device token length (2 bytes).
    header_format = '!LH'
    has_data = True

    while has_data:
        try:
            # Read the header tuple.
            header_data = read_and_unpack(sock, header_format)

            if header_data is not None:
                timestamp, token_length = header_data

                # Unpack format for a single value of length bytes
                token_format = '%ss' % token_length
                device_token = read_and_unpack(socket, token_format)

                if device_token is not None:
                    # read_and_unpack() returns a tuple, but it's just one
                    # item, so get the first.
                    token = device_token[0].encode('hex')
                    expired_tokens.append((token, timestamp))
            else:
                has_data = False
        except socket.timeout:
            # py3, see http://bugs.python.org/issue10272
            pass
        except ssl.SSLError as ex:
            # py2
            if 'timed out' not in ex.message:
                raise

    return expired_tokens


def send(token,
         alert,
         settings,
         identifier=0,
         expiration=None,
         priority=10,
         sock=None,
         **options):
    """Send push notification to single device."""
    if not is_valid_token(token):
        raise APNSError(('Invalid token format. '
                         'Expected 64 character hex string.'))

    payload = create_payload(alert, **options)
    max_size = settings['APNS_MAX_NOTIFICATION_SIZE']
    default_expiration_offset = settings['APNS_DEFAULT_EXPIRATION_OFFSET']

    if len(payload) > max_size:
        raise APNSDataOverflow(('Notification body cannot exceed {0} bytes'
                                .format(max_size)))

    # If expiration isn't specified use default offset from now.
    expiration_time = (expiration if expiration is not None
                       else int(time.time()) + default_expiration_offset)

    frame = pack_frame(token,
                       payload,
                       identifier,
                       expiration_time,
                       priority)

    if sock:
        sock.write(frame)
    else:
        with closing(create_push_socket(settings)) as _sock:
            _sock.write(frame)
            check_errors(_sock, settings)


def send_bulk(tokens, alert, settings, **options):
    """Send push notification to multiple devices."""
    with closing(create_push_socket(settings)) as sock:
        for identifier, token in enumerate(tokens):
            send(token,
                 alert,
                 settings,
                 identifier=identifier,
                 sock=sock,
                 **options)

        check_errors(sock, settings)


def get_expired_tokens(settings):
    """Return inactive device ids that can't be pushed to anymore."""
    with closing(create_feedback_socket(settings)) as sock:
        return receive_feedback(sock)
