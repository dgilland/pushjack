# -*- coding: utf-8 -*-
"""Client module for Google Cloud Messaging service.

By default, sending notifications is optimized to deliver notifications to the
maximum number of allowable recipients per HTTP request (currently 1,000
recipients as specified in the GCM documentation).

The return from a send operation will contain a response object that parses all
GCM HTTP responses and groups them by errors, successful registration ids,
failed registration ids, canonical ids, and the raw responses from each
request.

For more details regarding Google's GCM documentation, consult the following:

- `GCM for Android <http://goo.gl/swDCy>`_
- `GCM Server Reference <http://goo.gl/GPjNwV>`_
"""

from collections import namedtuple
import logging

import requests

from .utils import chunk, compact_dict, json_loads, json_dumps
from .exceptions import GCMError, GCMAuthError, gcm_server_errors
from ._compat import iteritems


__all__ = (
    'GCMClient',
    'GCMResponse',
    'GCMCanonicalID',
)


log = logging.getLogger(__name__)


GCM_URL = 'https://fcm.googleapis.com/fcm/send'

# GCM only allows up to 1000 reg ids per bulk message.
GCM_MAX_RECIPIENTS = 1000

#: Indicates that the push message should be sent with low priority. Low
#: priority optimizes the client app's battery consumption, and should be used
#: unless immediate delivery is required. For messages with low priority, the
#: app may receive the message with unspecified delay.
GCM_LOW_PRIORITY = 'normal'

#: Indicates that the push message should be sent with a high priority. When a
#: message is sent with high priority, it is sent immediately, and the app can
#: wake a sleeping device and open a network connection to your server.
GCM_HIGH_PRIORITY = 'high'


class GCMClient(object):
    """GCM client class."""
    url = GCM_URL

    def __init__(self, api_key):
        self.api_key = api_key
        self._conn = None

    @property
    def conn(self):
        """Reference to lazy GCM connection."""
        if not self._conn:
            self._conn = self.create_connection()
        return self._conn

    def create_connection(self):
        """Create and return new GCM connection."""
        return GCMConnection(self.api_key, self.url)

    def send(self, ids, message, **options):
        """Send push notification to single or multiple recipients.

        Args:
            ids (list): GCM device registration IDs.
            message (str|dict): Message string or dictionary. If ``message``
                is a dict and contains the field ``notification``, then it will
                be used for the ``notification`` payload.

        Keyword Args:
            notificatoin (dict, optional): Notification payload. Can include
                the fields ``body``, ``title``, and ``icon``.
            collapse_key (str, optional): Identifier for a group of messages
                that can be collapsed so that only the last message gets sent
                when delivery can be resumed. Defaults to ``None``.
            delay_while_idle (bool, optional): If ``True`` indicates that the
                message should not be sent until the device becomes active.
            time_to_live (int, optional): How long (in seconds) the message
                should be kept in GCM storage if the device is offline. The
                maximum time to live supported is 4 weeks. Defaults to ``None``
                which uses the GCM default of 4 weeks.
            low_priority (boolean, optional): Whether to send notification with
                the low priority flag. Defaults to ``False``.
            restricted_package_name (str, optional): Package name of the
                application where the registration IDs must match in order to
                receive the message. Defaults to ``None``.
            dry_run (bool, optional): If ``True`` no message will be sent but
                request will be tested.

        Returns:
            :class:`GCMResponse`: Response from GCM server.

        Raises:
            GCMAuthError: If :attr:`api_key` not set.
                :class:`.GCMAuthError`

        .. versionadded:: 0.0.1

        .. versionchanged:: 0.4.0
            - Added support for bulk sending.
            - Removed `request` argument.

        .. versionchanged:: 1.2.0
            - Added ``low_priority`` argument.
        """
        if not self.api_key:
            raise GCMAuthError('Missing GCM API key.')

        if not isinstance(ids, (list, tuple)):
            ids = [ids]

        message = GCMMessage(ids, message, **options)
        response = self.conn.send(GCMMessageStream(message))

        return response


class GCMConnection(object):
    """Wrapper around requests session bound to GCM config."""
    def __init__(self, api_key, url=GCM_URL):
        self.api_key = api_key
        self.url = url

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': 'key={0}'.format(self.api_key),
            'Content-Type': 'application/json',
        })

    def post(self, message):
        """Send single POST request with message to GCM server."""
        log.debug('Sending GCM notification batch containing {0} bytes.'
                  .format(len(message)))
        return self.session.post(self.url, message)

    def send(self, stream):
        """Send messages to GCM server and return list of responses."""
        log.debug('Preparing to send {0} notifications to GCM.'
                  .format(len(stream)))

        response = GCMResponse([self.post(message) for message in stream])

        log.debug('Sent {0} notifications to GCM.'.format(len(stream)))

        if response.failures:
            log.debug('Encountered {0} errors while sending to GCM.'
                      .format(len(response.failures)))

        return response


class GCMMessage(object):
    """GCM message object that serializes to JSON."""
    def __init__(self,
                 registration_ids,
                 message,
                 notification=None,
                 collapse_key=None,
                 delay_while_idle=None,
                 time_to_live=None,
                 restricted_package_name=None,
                 low_priority=None,
                 dry_run=None):
        self.registration_ids = registration_ids
        self.message = message
        self.collapse_key = collapse_key
        self.delay_while_idle = delay_while_idle
        self.time_to_live = time_to_live
        self.restricted_package_name = restricted_package_name
        self.dry_run = dry_run
        self.notification = notification
        self.data = {}

        if low_priority:
            self.priority = None
        else:
            self.priority = GCM_HIGH_PRIORITY

        self._parse_message()

    def _parse_message(self):
        """Parse and filter :attr:`message` to set :attr:`data` and
        :attr:`notification`.
        """
        if not isinstance(self.message, dict):
            self.data['message'] = self.message
        else:
            if 'notification' in self.message:
                self.notification = self.message['notification']

            self.message = dict((key, value)
                                for key, value in iteritems(self.message)
                                if key not in ('notification',))

            self.data.update(self.message)

    def to_dict(self):
        """Return message as dictionary."""
        return compact_dict({
            'registration_ids': self.registration_ids,
            'notification': self.notification,
            'data': self.data,
            'collapse_key': self.collapse_key,
            'delay_while_idle': self.delay_while_idle,
            'time_to_live': self.time_to_live,
            'priority': self.priority,
            'restricted_package_name': self.restricted_package_name,
            'dry_run': True if self.dry_run else None
        })

    def to_json(self):  # pragma: no cover
        """Return message as JSON string."""
        return json_dumps(self.to_dict())


class GCMMessageStream(object):
    """Iterable object that yields GCM messages in chunks."""
    def __init__(self, message):
        self.message = message

    def __len__(self):
        """Return count of number of notifications."""
        return len(self.message.registration_ids)

    def __iter__(self):
        """Iterate through and yield chunked messages."""
        message = self.message.to_dict()
        del message['registration_ids']

        for ids in chunk(self.message.registration_ids, GCM_MAX_RECIPIENTS):
            for id in ids:
                log.debug('Preparing notification for GCM id {0}'
                          .format(id))

            if len(ids) > 1:
                to_field = 'registration_ids'
            else:
                to_field = 'to'
                ids = ids[0]

            message[to_field] = ids

            yield json_dumps(message)


class GCMResponse(object):
    """GCM server response with results parsed into :attr:`responses`,
    :attr:`messages`, :attr:`registration_ids`, :attr:`data`,
    :attr:`successes`, :attr:`failures`, :attr:`errors`, and
    :attr:`canonical_ids`.

    Attributes:
        responses (list): List of ``requests.Response`` objects from each GCM
            request.
        messages (list): List of message data sent in each GCM request.
        registration_ids (list): Combined list of all recipient registration
            IDs.
        data (list): List of each GCM server response data.
        successes (list): List of registration IDs that were sent successfully.
        failures (list): List of registration IDs that failed.
        errors (list): List of exception objects correponding to the
            registration IDs that ere not sent successfully. See
            :mod:`pushjack.exceptions`.
        canonical_ids (list): List of registration IDs that have been
            reassigned a new ID. Each element is an instance of
            :class:`GCMCanonicalID`.
    """
    def __init__(self, responses):
        if not isinstance(responses, (list, tuple)):  # pragma: no cover
            responses = [responses]

        self.responses = responses
        self.messages = []
        self.registration_ids = []
        self.data = []
        self.successes = []
        self.failures = []
        self.errors = []
        self.canonical_ids = []

        self._parse_responses()

    def _parse_responses(self):
        """Parse each server response."""
        for response in self.responses:
            try:
                message = json_loads(response.request.body)
            except (TypeError, ValueError):
                message = None

            self.messages.append(message)
            message = message or {}

            if 'registration_ids' in message:
                registration_ids = message['registration_ids']
            elif 'to' in message:
                registration_ids = [message['to']]
            else:
                registration_ids = []

            if not registration_ids:
                continue

            self.registration_ids.extend(registration_ids)

            if response.status_code == 200:
                data = response.json()
                self.data.append(data)
                self._parse_results(registration_ids, data.get('results', []))
            elif response.status_code == 500:
                for registration_id in registration_ids:
                    self._add_failure(registration_id, 'InternalServerError')

    def _parse_results(self, registration_ids, results):
        """Parse the results key from the server response into errors,
        failures, and successes.
        """
        for index, result in enumerate(results):
            registration_id = registration_ids[index]

            if 'error' in result:
                self._add_failure(registration_id, result['error'])
            else:
                self._add_success(registration_id)

            if 'registration_id' in result:
                self._add_canonical_id(registration_id,
                                       result['registration_id'])

    def _add_success(self, registration_id):
        """Add `registration_id` to :attr:`successes` list."""
        self.successes.append(registration_id)

    def _add_failure(self, registration_id, error_code):
        """Add `registration_id` to :attr:`failures` list and exception to
        errors list.
        """
        self.failures.append(registration_id)

        if error_code in gcm_server_errors:
            self.errors.append(gcm_server_errors[error_code](registration_id))

    def _add_canonical_id(self, registration_id, canonical_id):
        """Add `registration_id` and `canonical_id` to :attr:`canonical_ids`
        list as tuple.
        """
        self.canonical_ids.append(GCMCanonicalID(registration_id,
                                                 canonical_id))


class GCMCanonicalID(namedtuple('GCMCanonicalID', ['old_id', 'new_id'])):
    """Represents a canonical ID returned by the GCM Server. This object
    indicates that a previously registered ID has changed to a new one.

    Attributes:
        old_id (str): Previously registered ID.
        new_id (str): New registration ID that should replace :attr:`old_id`.
    """
    pass
