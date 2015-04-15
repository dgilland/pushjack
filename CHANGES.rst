.. _changelog:

Changelog
=========


v0.4.0 (xxxx-xx-xx)
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
