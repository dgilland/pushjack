# -*- coding: utf-8 -*-
"""Client module for Apple Push Notification service.

The algorithm used to send bulk push notifications is optimized to eagerly
check for errors using a single thread. Error checking is performed after each
batch send (bulk notifications may be broken up into multiple batches) and is
non-blocking until the last notification is sent. A final, blocking error check
is performed using a customizable error timeout. This style of error checking
is done to ensure that no errors are missed (e.g. by waiting too long to check
errors before the connection is closed by the APNS server) without having to
use two threads to read and write.

The return from a send operation will contain a response object that includes
any errors encountered while sending. These errors will be associated with the
failed tokens.

For more details regarding Apple's APNS documentation, consult the following:

- `Apple Push Notification Service <http://goo.gl/wFVr2S>`_
- `Provider Communication with APNS <http://goo.gl/qMfByr>`_
"""

from binascii import hexlify, unhexlify
from collections import namedtuple
import logging
import select
import socket
import ssl
import struct
import time

from .utils import json_dumps, chunk, compact_dict
from .exceptions import (
    APNSError,
    APNSAuthError,
    APNSInvalidTokenError,
    APNSInvalidPayloadSizeError,
    APNSMissingPayloadError,
    APNSServerError,
    APNSTimeoutError,
    APNSUnsendableError,
    raise_apns_server_error
)


__all__ = (
    'APNSClient',
    'APNSSandboxClient',
    'APNSResponse',
    'APNSExpiredToken',
)


log = logging.getLogger(__name__)


APNS_HOST = 'gateway.push.apple.com'
APNS_SANDBOX_HOST = 'gateway.sandbox.push.apple.com'
APNS_PORT = 2195
APNS_FEEDBACK_HOST = 'feedback.push.apple.com'
APNS_FEEDBACK_SANDBOX_HOST = 'feedback.sandbox.push.apple.com'
APNS_FEEDBACK_PORT = 2196

APNS_DEFAULT_EXPIRATION_OFFSET = 60 * 60 * 24 * 30  # 1 month
APNS_DEFAULT_BATCH_SIZE = 100
APNS_DEFAULT_ERROR_TIMEOUT = 10
APNS_DEFAULT_MAX_PAYLOAD_LENGTH = 0
APNS_DEFAULT_RETRIES = 5

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

#: Indicates that the push message should be sent at a time that conserves
#: power on the device receiving it.
APNS_LOW_PRIORITY = 5

#: Indicates that the push message should be sent immediately. The remote
#: notification must trigger an alert, sound, or badge on the device. It is an
#: error to use this priority for a push that contains only the
#: ``content_available`` key.
APNS_HIGH_PRIORITY = 10


class APNSClient(object):
    """APNS client class."""
    host = APNS_HOST
    port = APNS_PORT
    feedback_host = APNS_FEEDBACK_HOST
    feedback_port = APNS_FEEDBACK_PORT

    def __init__(self,
                 certificate,
                 default_error_timeout=APNS_DEFAULT_ERROR_TIMEOUT,
                 default_expiration_offset=APNS_DEFAULT_EXPIRATION_OFFSET,
                 default_batch_size=APNS_DEFAULT_BATCH_SIZE,
                 default_max_payload_length=APNS_DEFAULT_MAX_PAYLOAD_LENGTH,
                 default_retries=APNS_DEFAULT_RETRIES):
        self.certificate = certificate
        self.default_error_timeout = default_error_timeout
        self.default_expiration_offset = default_expiration_offset
        self.default_batch_size = default_batch_size
        self.default_max_payload_length = default_max_payload_length
        self.default_retries = default_retries
        self._conn = None

    @property
    def conn(self):
        """Reference to lazy APNS connection."""
        if not self._conn:
            self._conn = self.create_connection()
        return self._conn

    def create_connection(self):
        """Create and return new APNS connection to push server."""
        return APNSConnection(self.host, self.port, self.certificate)

    def create_feedback_connection(self):
        """Create and return new APNS connection to feedback server."""
        return APNSConnection(self.feedback_host,
                              self.feedback_port,
                              self.certificate)

    def close(self):
        """Close APNS connection."""
        self.conn.close()

    def send(self,
             ids,
             message=None,
             expiration=None,
             low_priority=None,
             batch_size=None,
             error_timeout=None,
             max_payload_length=None,
             retries=None,
             **options):
        """Send push notification to single or multiple recipients.

        Args:
            ids (list): APNS device tokens. Each item is expected to be a hex
                string.
            message (str|dict): Message string or APS dictionary. Set to
                ``None`` to send an empty alert notification.
            expiration (int, optional): Expiration time of message in seconds
                offset from now. Defaults to ``None`` which uses
                :attr:`default_expiration_offset`.
            low_priority (boolean, optional): Whether to send notification with
                the low priority flag. Defaults to ``False``.
            batch_size (int, optional): Number of notifications to group
                together when sending. Defaults to ``None`` which uses
                attr:`default_batch_size`.
            error_timeout (int, optional): Time in seconds to wait for the
                error response after sending messages. Defaults to ``None``
                which uses attr:`default_error_timeout`.
            max_payload_length (int, optional): The maximum length of the
                payload to send. Message will be trimmed if the size is
                exceeded. Use 0 to turn off. Defaults to ``None`` which uses
                attr:`default_max_payload_length`.
            retries (int, optional): Number of times to retry when the send
                operation fails. Defaults to ``None`` which uses
                :attr:`default_retries`.

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
                ``Close`` and ``View`` buttons. The string is used as a key to
                get a localized string in the current localization to use for
                the right button’s title instead of ``"View"``.
            loc_key (str, optional): A key to an alert-message string in a
                ``Localizable.strings`` file for the current localization.
            loc_args (list, optional): List of string values to appear in place
                of the format specifiers in ``loc_key``.
            launch_image (str, optional): The filename of an image file in the
                app bundle; it may include the extension or omit it.
            mutable_content (bool, optional): if ``True``, triggers Apple
                Notification Service Extension. Defaults to ``None``.
            thread_id (str, optional): Identifier for grouping notifications.
                iOS groups notifications with the same thread identifier
                together in Notification Center. Defaults to ``None``.
            extra (dict, optional): Extra data to include with the alert.

        Returns:
            :class:`APNSResponse`: Response from APNS containing tokens sent
                and any errors encountered.

        Raises:
            APNSInvalidTokenError: Invalid token format.
                :class:`.APNSInvalidTokenError`
            APNSInvalidPayloadSizeError: Notification payload size too large.
                :class:`.APNSInvalidPayloadSizeError`
            APNSMissingPayloadError: Notificationpayload is empty.
                :class:`.APNSMissingPayloadError`

        .. versionadded:: 0.0.1

        .. versionchanged:: 0.4.0
            - Added support for bulk sending.
            - Made sending and error checking non-blocking.
            - Removed `sock`, `payload`, and `identifer` arguments.

        .. versionchanged:: 0.5.0
            - Added ``batch_size`` argument.
            - Added ``error_timeout`` argument.
            - Replaced ``priority`` argument with ``low_priority=False``.
            - Resume sending notifications when a sent token has an error
              response.
            - Raise ``APNSSendError`` if any tokens
              have an error response.

        .. versionchanged:: 1.0.0
            - Return :class:`APNSResponse` instead of raising
              ``APNSSendError``.
            - Raise :class:`.APNSMissingPayloadError` if
              payload is empty.

        .. versionchanged:: 1.4.0
            Added ``retries`` argument.
        """
        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        if max_payload_length is None:
            max_payload_length = self.default_max_payload_length

        message = APNSMessage(message,
                              max_payload_length=max_payload_length,
                              **options)

        validate_tokens(ids)
        validate_message(message)

        if low_priority:
            priority = APNS_LOW_PRIORITY
        else:
            priority = APNS_HIGH_PRIORITY

        if expiration is None:
            expiration = int(time.time() + self.default_expiration_offset)

        if batch_size is None:
            batch_size = self.default_batch_size

        if error_timeout is None:
            error_timeout = self.default_error_timeout

        if retries is None:
            retries = self.default_retries

        stream = APNSMessageStream(ids,
                                   message,
                                   expiration,
                                   priority,
                                   batch_size)

        return self.conn.sendall(stream, error_timeout, retries=retries)

    def get_expired_tokens(self):
        """Return inactive device tokens that are no longer registered to
        receive notifications.

        Returns:
            list: List of :class:`APNSExpiredToken` instances.

        .. versionadded:: 0.0.1
        """
        log.debug('Preparing to check for expired APNS tokens.')

        conn = self.create_feedback_connection()
        tokens = list(APNSFeedbackStream(conn))
        conn.close()

        log.debug('Received {0} expired APNS tokens.'.format(len(tokens)))

        return tokens


class APNSSandboxClient(APNSClient):
    """APNS client class for sandbox server."""
    host = APNS_SANDBOX_HOST
    feedback_host = APNS_FEEDBACK_SANDBOX_HOST


class APNSConnection(object):
    """Manager for APNS socket connection."""
    def __init__(self, host, port, certificate):
        self.host = host
        self.port = port
        self.certificate = certificate
        self.sock = None

    def connect(self):
        """Lazily connect to APNS server. Re-establish connection if previously
        closed.
        """
        if self.sock:
            return

        log.debug('Establishing connection to APNS on {0}:{1} using '
                  'certificate at {2}'
                  .format(self.host, self.port, self.certificate))

        self.sock = create_socket(self.host, self.port, self.certificate)

        log.debug('Established connection to APNS on {0}:{1}.'
                  .format(self.host, self.port))

    def close(self):
        """Disconnect from APNS server."""
        if self.sock:
            log.debug('Closing connection to APNS.')
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
            log.debug('Error while waiting for APNS socket to become '
                      'writable.')
            self.close()
            raise

    def readable(self, timeout):
        """Return whether connection is readable."""
        try:
            return select.select([self.client], [], [], timeout)[0]
        except Exception:  # pragma: no cover
            log.debug('Error while waiting for APNS socket to become '
                      'readable.')
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

    def write(self, data, timeout=10):
        """Write data to socket."""
        if not self.writable(timeout):  # pragma: no cover
            self.close()
            raise socket.timeout

        log.debug('Sending APNS notification batch containing {0} bytes.'
                  .format(len(data)))

        return self.client.sendall(data)

    def check_error(self, timeout=10):
        """Check for APNS errors."""
        if not self.readable(timeout):
            # No error response.
            return

        try:
            data = self.read(APNS_ERROR_RESPONSE_LEN, timeout=0)
        except socket.error as ex:  # pragma: no cover
            log.error('Could not read response: {0}.'.format(ex))
            self.close()
            return

        if not data:  # pragma: no cover
            return

        command = struct.unpack('>B', data[:1])[0]

        if command != APNS_ERROR_RESPONSE_COMMAND:  # pragma: no cover
            self.close()
            return

        code, identifier = struct.unpack('>BI', data[1:])

        log.debug('Received APNS error response with '
                  'code={0} for identifier={1}.'
                  .format(code, identifier))

        self.close()
        raise_apns_server_error(code, identifier)

    def send(self, frames, retries=APNS_DEFAULT_RETRIES):
        """Send stream of frames to APNS server."""
        if retries <= 0:  # pragma: no cover
            retries = 1

        current_identifier = frames.next_identifier

        for frame in frames:
            success = False
            last_ex = None

            while not success and retries:
                try:
                    self.write(frame)
                    success = True
                except socket.error as ex:
                    last_ex = ex
                    log.warning('Could not send frame to server: {0}. '
                                'Retrying send operation.'
                                .format(ex))
                    self.close()
                    retries -= 1

            if not success:
                log.error('Could not send frame to server: {0}.'
                          .format(last_ex))
                raise APNSTimeoutError(current_identifier)

            self.check_error(0)
            current_identifier = frames.next_identifier

    def sendall(self,
                stream,
                error_timeout=APNS_DEFAULT_ERROR_TIMEOUT,
                retries=APNS_DEFAULT_RETRIES):
        """Send all notifications while handling errors. If an error occurs,
        then resume sending starting from after the token that failed. If any
        tokens failed, raise an error after sending all tokens.
        """
        log.debug('Preparing to send {0} notifications to APNS.'
                  .format(len(stream)))

        errors = []

        while True:
            try:
                self.send(stream, retries=retries)

                # Perform the final error check here before exiting. A large
                # enough timeout should be used so that no errors are missed.
                self.check_error(error_timeout)
            except APNSServerError as ex:
                errors.append(ex)
                stream.seek(ex.identifier)

                if ex.fatal:
                    # We can't continue due to a fatal error. Go ahead and
                    # convert remaining notifications to errors.
                    errors += [APNSUnsendableError(i + stream.next_identifier)
                               for i, _ in enumerate(stream.peek())]
                    break

            if stream.eof():
                break

        log.debug('Sent {0} notifications to APNS.'.format(len(stream)))

        if errors:
            log.debug('Encountered {0} errors while sending to APNS.'
                      .format(len(errors)))

        return APNSResponse(stream.tokens, stream.message, errors)


class APNSMessage(object):
    """APNs message object that serializes to JSON."""
    def __init__(self,
                 message=None,
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
                 mutable_content=None,
                 thread_id=None,
                 extra=None,
                 max_payload_length=None):
        self.message = message
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
        self.mutable_content = mutable_content
        self.thread_id = thread_id
        self.extra = extra
        self.max_payload_length = max_payload_length

    def _construct_dict(self, message=None):
        """Return message as dictionary, overriding message."""
        msg = {}

        if any([self.title,
                self.title_loc_key,
                self.title_loc_args,
                self.action_loc_key,
                self.loc_key,
                self.loc_args,
                self.launch_image]):
            alert = {
                'body': message,
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
            alert = message

        msg.update(self.extra or {})
        msg['aps'] = compact_dict({
            'alert': alert,
            'badge': self.badge,
            'sound': self.sound,
            'category': self.category,
            'content-available': 1 if self.content_available else None,
            'mutable-content': 1 if self.mutable_content else None,
            'thread-id': self.thread_id
        })

        return msg

    def _construct_truncated_dict(self, message):
        """Return truncated message as dictionary."""
        msg = None
        ending = ''

        while message:
            data = self._construct_dict(message + ending)

            if len(json_dumps(data)) <= self.max_payload_length:
                msg = data
                break

            message = message[0:-1]
            ending = '...'

        if msg is None:  # pragma: no cover
            msg = self._construct_dict()

        return msg

    def to_dict(self):
        """Return message as dictionary, truncating if needed."""
        if self.message and self.max_payload_length:
            return self._construct_truncated_dict(self.message)

        return self._construct_dict(self.message)

    def to_json(self):
        """Return message as JSON string."""
        return json_dumps(self.to_dict())

    def __len__(self):
        """Return length of serialized message."""
        return len(self.to_json())


class APNSMessageStream(object):
    """Iterable object that yields a binary APNS socket frame for each device
    token.
    """
    def __init__(self,
                 tokens,
                 message,
                 expiration,
                 priority,
                 batch_size=1):
        self.tokens = tokens
        self.message = message
        self.expiration = expiration
        self.priority = priority
        self.batch_size = batch_size
        self.next_identifier = 0

    def seek(self, identifier):
        """Move token index to resume processing after token with index equal
        to `identifier`.

        Typically, `identifier` will be the token index that generated an error
        during send. Seeking to this identifier will result in processing the
        tokens that come after the error-causing token.

        Args:
            identifier (int): Index of tokens to skip.
        """
        self.next_identifier = identifier + 1

    def peek(self, n=None):
        return self.tokens[self.next_identifier:n]

    def eof(self):
        """Return whether all tokens have been processed."""
        return self.next_identifier >= len(self.tokens)

    def pack(self, token, identifier, message, expiration, priority):
        """Return a packed APNS socket frame for given token."""
        token_bin = unhexlify(token)
        token_len = len(token_bin)
        message_len = len(message)

        # |CMD|FRAMELEN|{token}|{message}|{id:4}|{expiration:4}|{priority:1}
        # 5 items, each 3 bytes prefix, then each item length
        frame_len = (
            APNS_PUSH_FRAME_ITEM_COUNT * APNS_PUSH_FRAME_ITEM_PREFIX_LEN +
            token_len +
            message_len +
            APNS_PUSH_IDENTIFIER_LEN +
            APNS_PUSH_EXPIRATION_LEN +
            APNS_PUSH_PRIORITY_LEN)
        frame_fmt = '>BIBH{0}sBH{1}sBHIBHIBHB'.format(token_len, message_len)

        # NOTE: Each bare int below is the corresponding frame item ID.
        frame = struct.pack(
            frame_fmt,
            APNS_PUSH_COMMAND, frame_len,  # BI
            1, token_len, token_bin,  # BH{token_len}s
            2, message_len, message,  # BH{message_len}s
            3, APNS_PUSH_IDENTIFIER_LEN, identifier,  # BHI
            4, APNS_PUSH_EXPIRATION_LEN, expiration,  # BHI
            5, APNS_PUSH_PRIORITY_LEN, priority)  # BHB

        return frame

    def __len__(self):
        """Return count of number of notifications."""
        return len(self.tokens)

    def __iter__(self):
        """Iterate through each device token and yield APNS socket frame."""
        message = self.message.to_json()

        data = b''
        tokens = self.tokens[self.next_identifier:]

        for token_chunk in chunk(tokens, self.batch_size):
            for token in token_chunk:
                log.debug('Preparing notification for APNS token {0}'
                          .format(token))

                data += self.pack(token,
                                  self.next_identifier,
                                  message,
                                  self.expiration,
                                  self.priority)
                self.next_identifier += 1

            yield data

            data = b''


class APNSFeedbackStream(object):
    """An iterable object that yields an expired device token."""
    def __init__(self, conn):
        self.conn = conn

    def __iter__(self):
        """Iterate through and yield expired device tokens."""
        header_format = '!LH'

        while True:
            data = self.conn.read(APNS_FEEDBACK_HEADER_LEN)

            if not data:
                break

            timestamp, token_len = struct.unpack(header_format, data)
            token_data = self.conn.read(token_len)

            if token_data:
                token = struct.unpack('{0}s'.format(token_len), token_data)
                token = hexlify(token[0]).decode('utf8')

                yield APNSExpiredToken(token, timestamp)


class APNSResponse(object):
    """Response from APNS after sending tokens.

    Attributes:
        tokens (list): List of all tokens sent during bulk sending.
        message (APNSMessage): :class:`APNSMessage` object sent.
        errors (list): List of APNS exceptions for each failed token.
        failures (list): List of all failed tokens.
        successes (list): List of all successful tokens.
        token_errors (dict): Dict mapping the failed tokens to their respective
            APNS exception.

    .. versionadded:: 1.0.0
    """
    def __init__(self, tokens, message, errors):
        self.tokens = tokens
        self.message = message
        self.errors = errors
        self.failures = []
        self.successes = []
        self.token_errors = {}

        for err in errors:
            tok = tokens[err.identifier]
            self.failures.append(tok)
            self.token_errors[tok] = err

        self.successes = [token for token in tokens
                          if token not in self.failures]


class APNSExpiredToken(namedtuple('APNSExpiredToken', ['token', 'timestamp'])):
    """Represents an expired APNS token with the timestamp of when it expired.

    Attributes:
        token (str): Expired APNS token.
        timestamp (int): Epoch timestamp.
    """
    pass


def create_socket(host, port, certificate):
    """Create a socket connection to the APNS server."""
    try:
        with open(certificate, 'r') as fileobj:
            fileobj.read()
    except Exception as ex:
        raise APNSAuthError('The certificate at {0} is not readable: {1}'
                            .format(certificate, ex))

    sock = socket.socket()

    # For some reason, pylint on TravisCI's Python 2.7 platform complains that
    # ssl.PROTOCOL_TLSv1 doesn't exist. Add a disable flag to bypass this.
    # pylint: disable=no-member
    sock = ssl.wrap_socket(sock,
                           ssl_version=ssl.PROTOCOL_TLSv1,
                           certfile=certificate,
                           do_handshake_on_connect=False)
    sock.connect((host, port))
    sock.setblocking(0)

    log.debug('Performing SSL handshake with APNS on {0}:{1}'
              .format(host, port))

    do_ssl_handshake(sock)

    return sock


def do_ssl_handshake(sock):
    """Perform SSL socket handshake for non-blocking socket."""
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


def valid_token(token):
    """Return whether token is in valid format."""
    try:
        valid = token and unhexlify(token)
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
        raise APNSInvalidTokenError('Invalid token format. '
                                    'Expected hex string: {0}'
                                    .format(', '.join(invalid)))


def validate_message(message):
    """Check whether `message` is valid."""
    if len(message) > APNS_MAX_NOTIFICATION_SIZE:
        raise APNSInvalidPayloadSizeError('Notification body cannot exceed '
                                          '{0} bytes'
                                          .format(APNS_MAX_NOTIFICATION_SIZE))
