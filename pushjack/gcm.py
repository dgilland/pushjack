# -*- coding: utf-8 -*-
"""Google Cloud Messaging service

Documentation is available on the Android Developer website:

https://developer.android.com/google/gcm/index.html
"""

from functools import partial

import requests

from .utils import chunk, json_dumps
from .exceptions import GCMError


__all__ = (
    'send',
    'send_bulk',
)


class Dispatcher(object):
    """Wrapper around requests session bound to GCM config."""
    def __init__(self, config):
        self.api_key = config.get('GCM_API_KEY')
        self.url = config.get('GCM_URL')

        self.session = requests.Session()
        self.session.auth = ('key', self.api_key)
        self.session.headers.update({
            'Content-Type': 'application/json',
        })

    def __call__(self, data, **options):
        return self.session.post(self.url, data, **options)


def create_dispatcher(config):
    """Return dispatcher callable for making HTTP request to GCM URL."""
    return Dispatcher(config)


def create_payload(tokens,
                   data,
                   collapse_key=None,
                   delay_while_idle=False,
                   time_to_live=0):
    """Return notification payload in JSON format."""
    if not isinstance(tokens, (list, tuple)):
        tokens = [tokens]

    payload = {'registration_ids': tokens}

    if data is not None:
        payload['data'] = data

    if collapse_key:
        payload['collapse_key'] = collapse_key

    if delay_while_idle:
        payload['delay_while_idle'] = delay_while_idle

    if time_to_live:
        payload['time_to_live'] = time_to_live

    return json_dumps(payload)


def send(token, data, config, dispatcher=None, **options):
    """Sends a GCM notification to a single token."""
    if dispatcher is None:
        dispatcher = create_dispatcher(config)

    payload = create_payload(token, data, **options)
    response = dispatcher(payload)
    results = response.json()

    if 'failure' in results and results.get('failure'):
        raise GCMError(results)

    return results


def send_bulk(tokens, data, config, dispatcher=None, **options):
    """Sends a GCM notification to one or more tokens."""
    if dispatcher is None:
        dispatcher = create_dispatcher(config)

    max_recipients = config.get('GCM_MAX_RECIPIENTS')

    results = []
    for _tokens in chunk(tokens, max_recipients):
        results.append(send(_tokens,
                            data,
                            config,
                            dispatcher=dispatcher,
                            **options))

    return results
