# -*- coding: utf-8 -*-
"""Lower level module for Google Cloud Messaging service.

This module is meant to provide basic functionality for sending push
notifications. The send functions don't try to do anything with the GCM server
responses other than return them as is. There is no exception handling of those
responses so error processing will need to be handled by the caller.

Google's documentation for GCM is available at:

- https://developer.android.com/google/gcm/index.html
- https://developer.android.com/google/gcm/server-ref.html
"""

import requests

from .utils import chunk, json_loads, json_dumps
from .exceptions import GCMError, GCMAuthError, gcm_server_errors


__all__ = (
    'send',
    'send_bulk',
)


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

    def __call__(self, payload):
        if isinstance(payload, dict):
            payload = json_dumps(payload)

        return self.session.post(self.url, payload)


class GCMResponse(object):
    """GCM server response with results parsed into :attr:`responses`,
    :attr:`payloads`, :attr:`registration_ids`, :attr:`data`,
    :attr:`successes`, :attr:`failures`, :attr:`errors`, and
    :attr:`canonical_ids`.
    """
    def __init__(self, responses):
        if not isinstance(responses, (list, tuple)):
            responses = [responses]

        #: List of ``request.Response`` objects from each GCM request.
        self.responses = responses
        #: List of payload data sent in each GCM request.
        self.payloads = []
        #: Combined list of all recipient registration IDs.
        self.registration_ids = []
        #: List of each GCM server response data.
        self.data = []
        #: List of registration IDs that were sent successfully.
        self.successes = []
        #: List of registration IDs that failed.
        self.failures = []
        #: List of exception objects correponding to the registration IDs that
        #: were not sent successfully. See :mod:`pushjack.exceptions`.
        self.errors = []
        #: List of registration IDs that have been reassigned a new ID. Each
        #: element is a tuple containing ``(old_id, new_id)``.
        self.canonical_ids = []

        self.parse_responses()

    def parse_responses(self):
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
                self.parse_results(registration_ids, data.get('results', []))
            elif response.status_code == 500:
                for registration_id in registration_ids:
                    self.add_failure(registration_id, 'InternalServerError')

    def parse_results(self, registration_ids, results):
        """Parse the results key from the server response into errors,
        failures, and successes.
        """
        for index, result in enumerate(results):
            registration_id = registration_ids[index]

            if 'error' in result:
                self.add_failure(registration_id, result['error'])
            else:
                self.add_success(registration_id)

            if 'registration_id' in result:
                self.add_canonical_id(registration_id,
                                      result['registration_id'])

    def add_success(self, registration_id):
        """Add `registration_id` to :attr:`successes` list."""
        self.successes.append(registration_id)

    def add_failure(self, registration_id, error_code):
        """Add `registration_id` to :attr:`failures` list and exception to errors
        list.
        """
        self.failures.append(registration_id)

        if error_code in gcm_server_errors:
            self.errors.append(gcm_server_errors[error_code](registration_id))

    def add_canonical_id(self, registration_id, canonical_id):
        """Add `registration_id` and `canonical_id` to :attr:`canonical_ids`
        list as tuple.
        """
        self.canonical_ids.append((registration_id, canonical_id))


def create_payload(registration_ids,
                   data,
                   collapse_key=None,
                   delay_while_idle=None,
                   time_to_live=None,
                   restricted_package_name=None,
                   dry_run=None):
    """Return notification payload in JSON format."""
    if not isinstance(registration_ids, (list, tuple)):
        registration_ids = [registration_ids]

    payload = {'registration_ids': registration_ids}

    if not isinstance(data, dict):
        data = {'message': data}

    if data is not None:
        payload['data'] = data

    if collapse_key is not None:
        payload['collapse_key'] = collapse_key

    if delay_while_idle is not None:
        payload['delay_while_idle'] = delay_while_idle

    if time_to_live is not None:
        payload['time_to_live'] = time_to_live

    if restricted_package_name is not None:
        payload['restricted_package_name'] = restricted_package_name

    if dry_run:
        payload['dry_run'] = True

    return payload


def send(registration_id, data, config, request=None, **options):
    """Sends a GCM notification to a single registration ID.

    Args:
        registration_id (str): GCM device registration ID.
        data (str|dict): Alert message or dictionary.
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
        GCMError: If GCM server response indicates failure.

    .. versionadded:: 0.0.1
    """
    if not config['GCM_API_KEY']:
        raise GCMAuthError('Missing GCM API key. Cannot send notifications.')

    if request is None:
        request = GCMRequest(config)

    payload = create_payload(registration_id, data, **options)
    return request(payload)


def send_bulk(registration_ids, data, config, request=None, **options):
    """Sends a GCM notification to one or more registration_ids.

    Args:
        registration_ids (list): List of GCM registration IDs.
        data (str|dict): Alert message or dictionary.
        config (dict): Configuration dictionary containing APNS configuration
            values. See :mod:`pushjack.config` for more details.
        request (callable, optional): Callable object that makes POST request
            to GCM service. Defaults to ``None`` which creates its own request
            callable.

    Returns:
        list: List of chunked ``requests.Response`` objects from GCM server
            grouped by ``GCM_MAX_RECIPIENTS``.

    See Also:
        See :func:`send` for a full listing of keyword arguments.

    .. versionadded:: 0.0.1
    """
    if request is None:
        request = GCMRequest(config)

    max_recipients = config.get('GCM_MAX_RECIPIENTS')

    results = []
    for _registration_ids in chunk(registration_ids, max_recipients):
        results.append(send(_registration_ids,
                            data,
                            config,
                            request=request,
                            **options))

    return results
