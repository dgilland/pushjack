.. _upgrading:

Upgrading
=========


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

    # Broken v0.3.0 code
    apns.send_bulk(tokens, **options)
    gcm.send_bulk(tokens, **options)

    # Fixed v0.4.0 code
    apns.send(tokens, **options)
    gcm.send(tokens, **options)
