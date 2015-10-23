.. _changelog:

Changelog
=========


v1.1.0 (2015-10-22)
-------------------

- Add support for ``notification`` field to GCM messages. [``GCM``]
- Replace ``registration_ids`` field with ``to`` field when sending to a single recipient since ``registration_ids`` field has been deprecated for single recipients. [``GCM``]


v1.0.1 (2015-05-07)
-------------------

- Fix incorrect authorization header in GCM client. Thanks `Brad Montgomery`_!


v1.0.0 (2015-04-28)
-------------------

- Add ``APNSSandboxClient`` for sending notifications to APNS sandbox server.
- Add ``message`` attribute to ``APNSResponse``.
- Add internal logging.
- Fix APNS error checking to properly handle reading when no data returned.
- Make APNS sending stop during iteration if a fatal error is received from APNS server (e.g. invalid topic, invalid payload size, etc).
- Make APNS and GCM clients maintain an active connection to server.
- Make APNS always return ``APNSResponse`` object instead of only raising ``APNSSendError`` when errors encountered. (**breaking change**)
- Remove APNS/GCM module send functions and only support client interfaces. (**breaking change**)
- Remove ``config`` argument from ``APNSClient`` and use individual method parameters as mapped below instead: (**breaking change**)

    - ``APNS_ERROR_TIMEOUT`` => ``default_error_timeout``
    - ``APNS_DEFAULT_EXPIRATION_OFFSET`` => ``default_expiration_offset``
    - ``APNS_DEFAULT_BATCH_SIZE`` => ``default_batch_size``

- Remove ``config`` argument from ``GCMClient`` and use individual method parameters as mapped below instead: (**breaking change**)

    - ``GCM_API_KEY`` => ``api_key``

- Remove ``pushjack.clients`` module. (**breaking change**)
- Remove ``pushjack.config`` module. (**breaking change**)
- Rename ``GCMResponse.payloads`` to ``GCMResponse.messages``. (**breaking change**)


v0.5.0 (2015-04-22)
-------------------

- Add new APNS configuration value ``APNS_DEFAULT_BATCH_SIZE`` and set to ``100``.
- Add ``batch_size`` parameter to APNS ``send`` that can be used to override ``APNS_DEFAULT_BATCH_SIZE``.
- Make APNS ``send`` batch multiple notifications into a single payload. Previously, individual socket writes were performed for each token. Now, socket writes are batched based on either the ``APNS_DEFAULT_BATCH_SIZE`` configuration value or the ``batch_size`` function argument value.
- Make APNS ``send`` resume sending from after the failed token when an error response is received.
- Make APNS ``send`` raise an ``APNSSendError`` when one or more error responses received. ``APNSSendError`` contains an aggregation of errors, all tokens attempted, failed tokens, and successful tokens. (**breaking change**)
- Replace ``priority`` argument to APNS ``send`` with ``low_priority=False``. (**breaking change**)


v0.4.0 (2015-04-15)
-------------------

- Improve error handling in APNS so that errors aren't missed.
- Improve handling of APNS socket connection during bulk sending so that connection is re-established when lost.
- Make APNS socket read/writes non-blocking.
- Make APNS socket frame packing easier to grok.
- Remove APNS and GCM ``send_bulk`` function. Modify ``send`` to support bulk notifications. (**breaking change**)
- Remove ``APNS_MAX_NOTIFICATION_SIZE`` as config option.
- Remove ``GCM_MAX_RECIPIENTS`` as config option.
- Remove ``request`` argument from GCM send function. (**breaking change**)
- Remove ``sock`` argument from APNS send function. (**breaking change**)
- Return namedtuple for GCM canonical ids.
- Return namedtuple class for APNS expired tokens.


v0.3.0 (2015-04-01)
-------------------

- Add ``restricted_package_name`` and ``dry_run`` fields to GCM sending.
- Add exceptions for all GCM server error responses.
- Make ``apns.get_expired_tokens`` and ``APNSClient.get_expired_tokens`` accept an optional ``sock`` argument to provide a custom socket connection.
- Raise ``APNSAuthError`` instead of ``APNSError`` if certificate file cannot be read.
- Raise ``APNSInvalidPayloadSizeError`` instead of ``APNSDataOverflow``. (**breaking change**)
- Raise ``APNSInvalidTokenError`` instead of ``APNSError``.
- Raise ``GCMAuthError`` if ``GCM_API_KEY`` is not set.
- Rename several function parameters:  (**breaking change**)

    - GCM: ``alert`` to ``data``
    - GCM: ``token``/``tokens`` to ``registration_id``/``registration_ids``
    - GCM: ``Dispatcher``/``dispatcher`` to ``GCMRequest``/``request``
    - Clients: ``registration_id`` to ``device_id``

- Return ``GCMResponse`` object for ``GCMClient.send/send_bulk``. (**breaking change**)
- Return ``requests.Response`` object(s) for ``gcm.send/send_bulk``. (**breaking change**)


v0.2.2 (2015-03-30)
-------------------

- Fix payload key assigments for ``title-loc``, ``title-loc-args``, and ``launch-image``. Previously, ``'_'`` was used in place of ``'-'``.


v0.2.1 (2015-03-28)
-------------------

- Fix incorrect variable reference in ``apns.receive_feedback``.


v0.2.0 (2015-03-28)
-------------------

- Fix handling of ``config`` in clients when ``config`` is a class object and subclass of ``Config``.
- Make ``apns.send/send_bulk`` accept additional ``alert`` fields: ``title``, ``title-loc``, ``title-loc-args``, and ``launch-image``.
- Make ``gcm.send/send_bulk`` raise a ``GCMError`` exception if ``GCM_API_KEY`` is not set.
- Make gcm payload creation cast ``data`` to dict if isn't not passed in as one. Original value of ``data`` is then set to ``{'message': data}``. (**breaking change**)
- Make gcm payload creation not set defaults for optional keyword arguments. (**breaking change**)


v0.1.0 (2015-03-26)
-------------------

- Rename ``pushjack.settings`` module to ``pushjack.config``. (**breaking change**)
- Allow config settings overrides to be passed into ``create_gcm_config``, ``create_apns_config``, and ``create_apns_sandbox_config``.
- Override ``Config``'s ``update()`` method with custom method that functions similarly to ``from_object()`` except that it accepts a ``dict`` instead.


v0.0.1 (2015-03-25)
-------------------

- First release.


.. _Brad Montgomery: https://github.com/bradmontgomery
