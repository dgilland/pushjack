# -*- coding: utf-8 -*-
"""Lower level module for Google Cloud Messaging service.

This module is meant to provide basic functionality for sending push
notifications. The send functions don't try to do anything with the GCM server
responses other than return them as is. There is no exception handling of those
responses so error processing will need to be handled by the caller.

Google's documentation for GCM is available at:

- `GCM for Android <http://goo.gl/swDCy>`_
- `GCM Server Reference <http://goo.gl/GPjNwV>`_
"""

from collections import namedtuple
import logging

import requests

from .utils import chunk, compact_dict, json_loads, json_dumps
from .exceptions import GCMError, GCMAuthError, gcm_server_errors


__all__ = (
    'send',
    'GCMCanonicalID',
    'GCMResponse',
)


log = logging.getLogger(__name__)


# GCM only allows up to 1000 reg ids per bulk message.
GCM_MAX_RECIPIENTS = 1000


class GCMCanonicalID(namedtuple('GCMCanonicalID', ['old_id', 'new_id'])):
    """Represents a canonical ID returned by the GCM Server. This object
    indicates that a previously registered ID has changed to a new one.

    Attributes:
        old_id (str): Previously registered ID.
        new_id (str): New registration ID that should replace :attr:`old_id`.
    """
    pass


class GCMPayload(object):
    """GCM payload object that serializes to JSON."""
    def __init__(self,
                 registration_ids,
                 alert,
                 collapse_key=None,
                 delay_while_idle=None,
                 time_to_live=None,
                 restricted_package_name=None,
                 dry_run=None):
        self.registration_ids = registration_ids
        self.alert = alert
        self.collapse_key = collapse_key
        self.delay_while_idle = delay_while_idle
        self.time_to_live = time_to_live
        self.restricted_package_name = restricted_package_name
        self.dry_run = dry_run

    def to_dict(self):
        """Return payload as dictionary."""
        return compact_dict({
            'registration_ids': self.registration_ids,
            'data': (self.alert if isinstance(self.alert, dict)
                     else {'message': self.alert}),
            'collapse_key': self.collapse_key,
            'delay_while_idle': self.delay_while_idle,
            'time_to_live': self.time_to_live,
            'restricted_package_name': self.restricted_package_name,
            'dry_run': True if self.dry_run else None
        })

    def to_json(self):
        """Return payload as JSON string."""
        return json_dumps(self.to_dict())


class GCMPayloadStream(object):
    """Iterable object that yields GCM payloads in chunks."""
    def __init__(self, payload):
        self.payload = payload

    def __iter__(self):
        """Iterate through and yield chunked payloads."""
        for ids in chunk(self.payload.registration_ids, GCM_MAX_RECIPIENTS):
            payload = self.payload.to_dict()
            payload['registration_ids'] = ids
            yield json_dumps(payload)


class GCMRequest(object):
    """Wrapper around requests session bound to GCM config."""
    def __init__(self, config):
        self.api_key = config.get('GCM_API_KEY')
        self.url = config.get('GCM_URL')

        self.session = requests.Session()
        self.session.auth = ('key', self.api_key)
        self.session.headers.update({
            'Content-Type': 'application/json',
        })

    def send(self, payloads):
        """Send payloads to GCM server and return list of responses."""
        return [self.session.post(self.url, payload) for payload in payloads]


class GCMResponse(object):
    """GCM server response with results parsed into :attr:`responses`,
    :attr:`payloads`, :attr:`registration_ids`, :attr:`data`,
    :attr:`successes`, :attr:`failures`, :attr:`errors`, and
    :attr:`canonical_ids`.

    Attributes:
        responses (list): List of ``request.Response`` objects from each GCM
            request.
        payloads (list): List of payload data sent in each GCM request.
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
        self.payloads = []
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
                payload = json_loads(response.request.body)
            except (TypeError, ValueError):
                payload = None

            self.payloads.append(payload)
            registration_ids = (payload or {}).get('registration_ids', [])

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


def send(ids, alert, config, **options):
    """Sends a GCM notification to one or more IDs.

    Args:
        id_ (str): GCM device registration ID.
        alert (str|dict): Alert message or dictionary.
        config (dict): Configuration dictionary containing APNS configuration
            values. See :mod:`pushjack.config` for more details.
        request (callable, optional): Callable object that makes POST request
            to GCM service. Defaults to ``None`` which creates its own request
            callable.

    Keyword Args:
        collapse_key (str, optional): Identifier for a group of messages that
            can be collapsed so that only the last message gets sent when
            delivery can be resumed. Defaults to ``None``.
        delay_while_idle (bool, optional): If ``True`` indicates that the
            message should not be sent until the device becomes active.
        time_to_live (int, optional): How long (in seconds) the message should
            be kept in GCM storage if the device is offline. The maximum time
            to live supported is 4 weeks. Defaults to ``None`` which uses the
            GCM default of 4 weeks.
        restricted_package_name (str, optional): Package name of the
            application where the registration IDs must match in order to
            receive the message. Defaults to ``None``.
        dry_run (bool, optional): If ``True`` no message will be sent but
            request will be tested.

    Returns:
        Response: ``requests.Response`` object from GCM server.

    Raises:
        GCMAuthError: If ``GCM_API_KEY`` not set in `config`.
        GCMServerError: If GCM server response indicates failure. See
            :mod:`pushjack.exceptions` for full listing.

    .. versionadded:: 0.0.1

    .. versionchanged:: 0.4.0

        - Added support for bulk sending.
        - Removed `request` argument.
    """
    if not config['GCM_API_KEY']:
        raise GCMAuthError('Missing GCM API key. Cannot send notifications.')

    if not isinstance(ids, (list, tuple)):
        ids = [ids]

    request = GCMRequest(config)
    payload = GCMPayload(ids, alert, **options)
    responses = request.send(GCMPayloadStream(payload))

    return GCMResponse(responses)
