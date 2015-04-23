.. _upgrading:

Upgrading
=========


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
