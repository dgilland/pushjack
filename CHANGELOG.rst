.. _changelog:

Changelog
=========


v1.4.0 (2017-11-09)
-------------------

- apns: Add exceptions ``APNSProtocolError`` and ``APNSTimeoutError``.  Thanks `Jakub Kleň`_!
- apns: Add retry mechanism to ``APNSClient.send``. Thanks `Jakub Kleň`_!

  - Add ``default_retries`` argument to ``APNSClient`` initialization. Defaults to ``5``.
  - Add ``retries`` argument to ``APNSClient.send``. By default will use ``APNSClient.default_retries`` unless explicitly passed in.
  - If unable to send after ``retries``, an ``APNSTimeoutError`` will be raised.

- apns: Fix bug in bulk ``APNSClient.send`` that resulted in an off-by-one error for message identifier in returned errors. Thanks `Jakub Kleň`_!
- apns: Add max payload truncation option to ``APNSClient.send``.  Thanks `Jakub Kleň`_!

  - Add ``default_max_payload_length`` argument to ``APNSClient`` initialization. Defaults to ``0`` which disabled max payload length check.
  - Add ``max_payload_length`` argument to ``APNSClient.send``. By default will use ``APNSClient.default_max_payload_length`` unless explicitly passed in.
  - When ``max_payload_length`` set, messages will be truncated to fit within the length restriction by trimming the "message" text and appending it with "...".


v1.3.0 (2017-03-11)
-------------------

- apns: Optimize reading from APNS Feedback so that the number of bytes read are based on header and token lengths.
- apns: Explicitly close connection to APNS Feedback service after reading data.
- apns: Add support for ``mutable-content`` field (Apple Notification Service Extension) via ``mutable_content`` argument to ``APNSClient.send()``. Thanks `Ahmed Khedr`_!
- apns: Add support for ``thread-id`` field (group identifier in Notification Center) via ``thread_id`` argument to ``APNSClient.send()``. Thanks `Ahmed Khedr`_!


v1.2.1 (2015-12-14)
-------------------

- apns: Fix implementation of empty APNS notifications and allow notifications with ``{"aps": {}}`` to be sent. Thanks `Julius Seporaitis`_!


v1.2.0 (2015-12-04)
-------------------

- gcm: Add support for ``priority`` field to GCM messages via ``low_priority`` keyword argument. Default behavior is for all messages to be ``"high"`` priority. This is the opposite of GCM messages but mirrors the behavior in the APNS module where the default priority is ``"high"``.


v1.1.0 (2015-10-22)
-------------------

- gcm: Add support for ``notification`` field to GCM messages.
- gcm: Replace ``registration_ids`` field with ``to`` field when sending to a single recipient since ``registration_ids`` field has been deprecated for single recipients.


v1.0.1 (2015-05-07)
-------------------

- gcm: Fix incorrect authorization header in GCM client. Thanks `Brad Montgomery`_!


v1.0.0 (2015-04-28)
-------------------

- apns: Add ``APNSSandboxClient`` for sending notifications to APNS sandbox server.
- apns: Add ``message`` attribute to ``APNSResponse``.
- pushjack: Add internal logging.
- apns: Fix APNS error checking to properly handle reading when no data returned.
- apns: Make APNS sending stop during iteration if a fatal error is received from APNS server (e.g. invalid topic, invalid payload size, etc).
- apns/gcm: Make APNS and GCM clients maintain an active connection to server.
- apns: Make APNS always return ``APNSResponse`` object instead of only raising ``APNSSendError`` when errors encountered. (**breaking change**)
- apns/gcm: Remove APNS/GCM module send functions and only support client interfaces. (**breaking change**)
- apns: Remove ``config`` argument from ``APNSClient`` and use individual method parameters as mapped below instead: (**breaking change**)

    - ``APNS_ERROR_TIMEOUT`` => ``default_error_timeout``
    - ``APNS_DEFAULT_EXPIRATION_OFFSET`` => ``default_expiration_offset``
    - ``APNS_DEFAULT_BATCH_SIZE`` => ``default_batch_size``

- gcm: Remove ``config`` argument from ``GCMClient`` and use individual method parameters as mapped below instead: (**breaking change**)

    - ``GCM_API_KEY`` => ``api_key``

- pushjack: Remove ``pushjack.clients`` module. (**breaking change**)
- pushjack: Remove ``pushjack.config`` module. (**breaking change**)
- gcm: Rename ``GCMResponse.payloads`` to ``GCMResponse.messages``. (**breaking change**)


v0.5.0 (2015-04-22)
-------------------

- apns: Add new APNS configuration value ``APNS_DEFAULT_BATCH_SIZE`` and set to ``100``.
- apns: Add ``batch_size`` parameter to APNS ``send`` that can be used to override ``APNS_DEFAULT_BATCH_SIZE``.
- apns: Make APNS ``send`` batch multiple notifications into a single payload. Previously, individual socket writes were performed for each token. Now, socket writes are batched based on either the ``APNS_DEFAULT_BATCH_SIZE`` configuration value or the ``batch_size`` function argument value.
- apns: Make APNS ``send`` resume sending from after the failed token when an error response is received.
- apns: Make APNS ``send`` raise an ``APNSSendError`` when one or more error responses received. ``APNSSendError`` contains an aggregation of errors, all tokens attempted, failed tokens, and successful tokens. (**breaking change**)
- apns: Replace ``priority`` argument to APNS ``send`` with ``low_priority=False``. (**breaking change**)


v0.4.0 (2015-04-15)
-------------------

- apns: Improve error handling in APNS so that errors aren't missed.
- apns: Improve handling of APNS socket connection during bulk sending so that connection is re-established when lost.
- apns: Make APNS socket read/writes non-blocking.
- apns: Make APNS socket frame packing easier to grok.
- apns/gmc: Remove APNS and GCM ``send_bulk`` function. Modify ``send`` to support bulk notifications. (**breaking change**)
- apns: Remove ``APNS_MAX_NOTIFICATION_SIZE`` as config option.
- gcm: Remove ``GCM_MAX_RECIPIENTS`` as config option.
- gcm: Remove ``request`` argument from GCM send function. (**breaking change**)
- apns: Remove ``sock`` argument from APNS send function. (**breaking change**)
- gcm: Return namedtuple for GCM canonical ids.
- apns: Return namedtuple class for APNS expired tokens.


v0.3.0 (2015-04-01)
-------------------

- gcm: Add ``restricted_package_name`` and ``dry_run`` fields to GCM sending.
- gcm: Add exceptions for all GCM server error responses.
- apns: Make ``apns.get_expired_tokens`` and ``APNSClient.get_expired_tokens`` accept an optional ``sock`` argument to provide a custom socket connection.
- apns: Raise ``APNSAuthError`` instead of ``APNSError`` if certificate file cannot be read.
- apns: Raise ``APNSInvalidPayloadSizeError`` instead of ``APNSDataOverflow``. (**breaking change**)
- apns: Raise ``APNSInvalidTokenError`` instead of ``APNSError``.
- gcm: Raise ``GCMAuthError`` if ``GCM_API_KEY`` is not set.
- pushjack: Rename several function parameters:  (**breaking change**)

    - gcm: ``alert`` to ``data``
    - gcm: ``token``/``tokens`` to ``registration_id``/``registration_ids``
    - gcm: ``Dispatcher``/``dispatcher`` to ``GCMRequest``/``request``
    - Clients: ``registration_id`` to ``device_id``

- gcm: Return ``GCMResponse`` object for ``GCMClient.send/send_bulk``. (**breaking change**)
- gcm: Return ``requests.Response`` object(s) for ``gcm.send/send_bulk``. (**breaking change**)


v0.2.2 (2015-03-30)
-------------------

- apns: Fix payload key assigments for ``title-loc``, ``title-loc-args``, and ``launch-image``. Previously, ``'_'`` was used in place of ``'-'``.


v0.2.1 (2015-03-28)
-------------------

- apns: Fix incorrect variable reference in ``apns.receive_feedback``.


v0.2.0 (2015-03-28)
-------------------

- pushjack: Fix handling of ``config`` in clients when ``config`` is a class object and subclass of ``Config``.
- apns: Make ``apns.send/send_bulk`` accept additional ``alert`` fields: ``title``, ``title-loc``, ``title-loc-args``, and ``launch-image``.
- gcm: Make ``gcm.send/send_bulk`` raise a ``GCMError`` exception if ``GCM_API_KEY`` is not set.
- gcm: Make gcm payload creation cast ``data`` to dict if isn't not passed in as one. Original value of ``data`` is then set to ``{'message': data}``. (**breaking change**)
- gcm: Make gcm payload creation not set defaults for optional keyword arguments. (**breaking change**)


v0.1.0 (2015-03-26)
-------------------

- pushjack: Rename ``pushjack.settings`` module to ``pushjack.config``. (**breaking change**)
- apns/gcm: Allow config settings overrides to be passed into ``create_gcm_config``, ``create_apns_config``, and ``create_apns_sandbox_config``.
- pushjack: Override ``Config``'s ``update()`` method with custom method that functions similarly to ``from_object()`` except that it accepts a ``dict`` instead.


v0.0.1 (2015-03-25)
-------------------

- First release.


.. _Brad Montgomery: https://github.com/bradmontgomery
.. _Julius Seporaitis: https://github.com/seporaitis
.. _Ahmed Khedr: https://github.com/aakhedr
.. _Jakub Kleň: https://github.com/kukosk
