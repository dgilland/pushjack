.. _upgrading:

Upgrading
=========


From v0.5.0 to v1.0.0
---------------------

There were several, major breaking changes in ``v1.0.0``:

- Make APNS always return ``APNSResponse`` object instead of only raising ``APNSSendError`` when errors encountered. (**breaking change**)
- Remove APNS/GCM module send functions and only support client interfaces. (**breaking change**)
- Remove ``config`` argument from ``APNSClient`` and use individual function parameters as mapped below instead: (**breaking change**)

    - ``APNS_ERROR_TIMEOUT`` => ``default_error_timeout``
    - ``APNS_DEFAULT_EXPIRATION_OFFSET`` => ``default_expiration_offset``
    - ``APNS_DEFAULT_BATCH_SIZE`` => ``default_batch_size``

- Remove ``config`` argument from ``GCMClient`` and use individual functionm parameters as mapped below instead: (**breaking change**)

    - ``GCM_API_KEY`` => ``api_key``

- Remove ``pushjack.clients`` module. (**breaking change**)
- Remove ``pushjack.config`` module. (**breaking change**)
- Rename ``GCMResponse.payloads`` to ``GCMResponse.messages``. (**breaking change**)

The motiviation behind these drastic changes were to eliminate multiple methods for sending tokens (removing module functions in favor of using client classes) and to simplify the overall implementation (eliminating a separate configuration module/implementation and instead passing config parameters directly into client class). This has lead to a smaller, easier to maintain codebase with fewer implementation details.

The module send functions are no longer implemented:

.. code-block:: python

    # This no longer works on v1.0.0.
    from pushjack import apns, gcm

    apns.send(...)
    gcm.send(...)


Instead, the respective client classes must be used instead:

.. code-block:: python

    # This works on v1.0.0.
    from pushjack import APNSClient, APNSSandboxClient, GCMClient

    apns = APNSClient(...)
    apns.send(...)

    apns_sandbox = APNSSandboxClient(...)
    apns_sandbox.send(...)

    gcm = GCMClient(...)
    gcm.send(...)


The configuration module has been eliminated:

.. code-block:: python

    # This fails on v1.0.0.
    from pushjack import APNSClient, GCMClient, create_apns_config, create_gcm_config

    apns = APNSClient(create_apns_config({
        'APNS_CERTIFICATE': '<path/to/certificate.pem>',
        'APNS_ERROR_TIMEOUT': 10,
        'APNS_DEFAULT_EXPIRATION_OFFSET: 60 * 60 * 24 * 30,
        'APNS_DEFAULT_BATCH_SIZE': 100
    }))
    apns.send(tokens, alert, **options)

    gcm = GCMClient(create_gcm_config({
        'GCM_API_KEY': '<api-key>'
    }))
    gcm.send(tokens, alert, **options)


Instead, configuration values are passed directly during class instance creation:

.. code-block:: python

    # This works on v1.0.0.
    from pushjack import APNSClient, APNSSandboxClient, GCMClient

    apns = APNSClient('<path/to/certificate.pem>',
                      default_error_timeout=10,
                      default_expiration_offset=60 * 60 * 24 * 30,
                      default_batch_size=100)

    # or if wanting to use the sandbox:
    # sandbox = APNSSandboxClient(...)

    apns.send(tokens, alert, **options)

    gcm = GCMClient('<api-key>')
    gcm.send(tokens, alert, **options)


APNS sending no longer raises an ``APNSSendError`` when error encountered:

.. code-block:: python

    # This fails on v1.0.0
    from pushjack APNSSendError

    try:
        apns.send(tokens, alert, **options)
    except APNSSendError as ex:
        ex.errors


Instead, APNS sending returns an :class:`pushjack.apns.APNSResponse` object:

.. code-block:: python

    # This works on v1.0.0
    res = apns.send(tokens, alert, **options)
    res.errors
    res.error_tokens


From v0.4.0 to v0.5.0
---------------------

There were two breaking changes in ``v0.5.0``:

- Make APNS ``send`` raise an ``APNSSendError`` when one or more error responses received. ``APNSSendError`` contains an aggregation of errors, all tokens attempted, failed tokens, and successful tokens. (**breaking change**)
- Replace ``priority`` argument to APNS ``send`` with ``low_priority=False``. (**breaking change**)

The new exception ``APNSSendError`` replaces individually raised APNS server errors. So instead of catching the base server exception, ``APNSServerError``, catch ``APNSSendError`` instead:


.. code-block:: python

    from pushjack import apns

    # On v0.4.0
    try:
        apns.send(tokens, **options)
    except APNSServerError:
        pass

    # Updated for v0.5.0
    try:
        apns.send(tokens, **options)
    except APNSSendError:
        pass


The new ``low_priority`` argument makes setting the APNS notification priority more straight-forward:


.. code-block:: python

    from pushjack import apns

    # On v0.4.0

    ## High priority (the default)
    apns.send(tokens, alert)
    apns.send(tokens, alert, priority=10)

    ## Low priority
    apns.send(tokens, alert, priority=5)

    # Updated for v0.5.0

    ## High priority (the default)
    apns.send(tokens, alert)
    apns.send(tokens, alert, low_priority=False)

    ## Low priority
    apns.send(tokens, alert, low_priority=True)


From v0.3.0 to v0.4.0
---------------------

There were several breaking changes in ``v0.4.0``:

- Remove ``request`` argument from GCM send function. (**breaking change**)
- Remove ``sock`` argument from APNS send function. (**breaking change**)
- Remove APNS and GCM ``send_bulk`` function. Modify ``send`` to support bulk notifications. (**breaking change**)

The first two items should be fairly minor as these arguments were not well documented nor encouraged. In ``v0.4.0`` the APNS socket and GCM request objects are now managed within the send functions.

The last item is more likely to break code since ``send_bulk`` was removed. However, replacing ``send_bulk`` with ``send`` will fix it:


.. code-block:: python

    from pushjack import apns, gcm

    # On v0.3.0
    apns.send_bulk(tokens, **options)
    gcm.send_bulk(tokens, **options)

    # Updated for v0.4.0
    apns.send(tokens, **options)
    gcm.send(tokens, **options)
