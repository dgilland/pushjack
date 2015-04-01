# -*- coding: utf-8 -*-
"""Google Cloud Messaging service

Documentation is available on the Android Developer website:

- https://developer.android.com/google/gcm/index.html
- https://developer.android.com/google/gcm/server-ref.html
"""

from functools import partial

import requests

from .utils import chunk, json_dumps
from .exceptions import GCMError, GCMAuthError


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
        dict: Response from GCM server.

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
    response = request(payload)
    results = response.json()

    if 'failure' in results and results.get('failure'):
        raise GCMError(results)

    return results


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
        list: List of chunked GCM server responses grouped by
            ``GCM_MAX_RECIPIENTS``.

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
