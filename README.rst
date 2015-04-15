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

Install using pip:


::

    pip install pushjack


Whether using ``APNS`` or ``GCM``, pushjack provides a common API interface for each.


APNS
----

Using the ``APNSClient`` class:


.. code-block:: python

    from pushjack import APNSClient, create_apns_config

    config = create_apns_config({
        'APNS_CERTIFICATE': '<path/to/certificate.pem>'
    })

    client = APNSClient(config)

    token = '<device token>'
    alert = 'Hello world.'

    # Send to single device.
    # Keyword arguments are optional.
    client.send(token,
                alert,
                badge='badge count',
                sound='sound to play',
                category='category',
                content_available=True,
                title='Title',
                title_loc_key='t_loc_key',
                title_loc_args='loc_args',
                action_loc_key='a_loc_key',
                loc_key='loc_key',
                launch_image='path/to/image.jpg',
                extra={'custom': 'data'})

    # Send to multiple devices by passing a list of tokens.
    client.send([token], alert, **options)

    # Get expired tokens.
    expired = client.get_expired_tokens()


Using the APNS module directly:


.. code-block:: python

    from pushjack import apns

    # Call signature is the same as APNSClient
    # except the configuration must be passed in.
    apns.send(token, alert, config, **options)


GCM
---

Using the ``GCMClient`` class:


.. code-block:: python

    from pushjack import GCMClient, create_gcm_config

    config = create_gcm_config({
        'GCM_API_KEY': '<api key>'
    })

    client = GCMClient(config)

    registration_id = '<registration id>'
    alert = 'Hello world.'

    # Send to single device.
    # Keyword arguments are optional.
    client.send(registration_id,
                data,
                collapse_key='collapse_key',
                delay_while_idle=True,
                time_to_live=100)

    # Send to multiple devices by passing a list of ids
    client.send([registration_id], alert, **options)


Using the GCM module directly:


.. code-block:: python

    from pushjack import gcm

    # Call signature is the same as GCMClient
    # except the configuration must be passed in.
    gcm.send(token, alert, config, **options)


Config
------

The config object for configuring a client is expected to be a ``dict`` or subclass of ``dict``:


.. code-block:: python

    gcm_config = {
        'GCM_API_KEY': '<api key>',
        'GCM_URL': 'https://android.googleapis.com/gcm/send'
    }

    apns_config = {
        'APNS_CERTIFICATE': '<path/to/certificate.pem>',
        'APNS_HOST': 'gateway.push.apple.com',
        'APNS_PORT': 2195,
        'APNS_FEEDBACK_HOST': 'feedback.push.apple.com',
        'APNS_FEEDBACK_PORT': 2196,
        'APNS_ERROR_TIMEOUT': 0.5,
        'APNS_DEFAULT_EXPIRATION_OFFSET': 60 * 60 * 24 * 30
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
