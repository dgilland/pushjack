********
pushjack
********

|version| |travis| |coveralls| |license|

Push notifications for APNS (iOS) and GCM (Android).


Links
=====

- Project: https://github.com/dgilland/pushjack
- Documentation: http://pushjack.readthedocs.org
- PyPi: https://pypi.python.org/pypi/pushjack/
- TravisCI: https://travis-ci.org/dgilland/pushjack


Quickstart
==========

Whether using ``APNS`` or ``GCM``, pushjack provides a common API interface for each.


APNS
----

.. code-block:: python

    from pushjack import APNSClient, create_apns_config

    settings = create_apns_config({
        'APNS_CERTIFICATE': '<path/to/certificate.pem>'
    })

    client = APNSClient(settings)

    # Send to single device.
    client.send(token, alert, **options)

    # Sent to multiple devices.
    client.send_bulk(tokens, alert, **options)

    # Get expired tokens.
    expired = client.get_expired_tokens()


GCM
---

.. code-block:: python

    from pushjack import GCMClient, create_gcm_config

    settings = create_gcm_config({
        'GCM_API_KEY': '<api key>'
    })

    client = GCMClient(settings)

    # Send to single device.
    client.send(token, alert, **options)

    # Sent to multiple devices.
    client.send_bulk(tokens, alert, **options)


Settings
--------

The settings object for configuring a client is expected to be a ``dict`` or subclass of ``dict``:


.. code-block:: python

    gcm_settings = {
        'GCM_API_KEY': '<api key>',
        'GCM_URL': 'https://android.googleapis.com/gcm/send',
        'GCM_MAX_RECIPIENTS': 1000
    }

    apns_settings = {
        'APNS_CERTIFICATE': '<path/to/certificate.pem>',
        'APNS_HOST': 'gateway.push.apple.com',
        'APNS_PORT': 2195,
        'APNS_FEEDBACK_HOST': 'feedback.push.apple.com',
        'APNS_FEEDBACK_PORT': 2196,
        'APNS_ERROR_TIMEOUT': 0.5,
        'APNS_DEFAULT_EXPIRATION_OFFSET': 60 * 60 * 24 * 30
        'APNS_MAX_NOTIFICATION_SIZE': 2048
    }


For a class based approached, configuration classes are provided for subclassing which can be passed to each client class. By default, both ``GCMConfig``, ``APNSConfig``, and ``APNSSandboxConfig`` will set default values for the settings that shouldn't change. You will need to set ``GCM_API_KEY`` or ``APNS_CERTIFICATE`` appropriately though:


.. code-block:: python

    from pushjack import GCMClient, GCMConfig, APNSConfig, APNSSandboxConfig

    class MyGCMConfig(GCMConfig):
        GCM_API_KEY = '<api key>'

    class MyAPNSConfig(APNSConfig):
        APNS_CERTIFICATE = '<path/to/certificate.pem>'

    class MyAPNSSandboxConfig(APNSConfig):
        APNS_CERTIFICATE = '<path/to/certificate.pem>'


    client = GCMClient(MyGCMConfig)


**NOTE:** You can only pass in a class to the client initializer if it is a subclass of one of the provided ``*Config`` classes.



For more details, please see the full documentation at http://pushjack.readthedocs.org.


.. |version| image:: http://img.shields.io/pypi/v/pushjack.svg?style=flat-square
    :target: https://pypi.python.org/pypi/pushjack/

.. |travis| image:: http://img.shields.io/travis/dgilland/pushjack/master.svg?style=flat-square
    :target: https://travis-ci.org/dgilland/pushjack

.. |coveralls| image:: http://img.shields.io/coveralls/dgilland/pushjack/master.svg?style=flat-square
    :target: https://coveralls.io/r/dgilland/pushjack

.. |license| image:: http://img.shields.io/pypi/l/pushjack.svg?style=flat-square
    :target: https://pypi.python.org/pypi/pushjack/
