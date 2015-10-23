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


Whether using ``APNS`` or ``GCM``, pushjack provides clients for each.


APNS
----

Send notifications using the ``APNSClient`` class:


.. code-block:: python

    from pushjack import APNSClient

    client = APNSClient(certificate='<path/to/certificate.pem>',
                        default_error_timeout=10,
                        default_expiration_offset=2592000,
                        default_batch_size=100)

    token = '<device token>'
    alert = 'Hello world.'

    # Send to single device.
    # NOTE: Keyword arguments are optional.
    res = client.send(token,
                      alert,
                      badge='badge count',
                      sound='sound to play',
                      category='category',
                      content_available=True,
                      title='Title',
                      title_loc_key='t_loc_key',
                      title_loc_args='t_loc_args',
                      action_loc_key='a_loc_key',
                      loc_key='loc_key',
                      launch_image='path/to/image.jpg',
                      extra={'custom': 'data'})

    # List of all tokens sent.
    res.tokens

    # List of any subclassed APNSServerError objects.
    res.errors

    # Dict mapping token => APNSServerError.
    res.token_errors


    # Send to multiple devices by passing a list of tokens.
    client.send([token], alert, **options)

    # Override defaults for error_timeout, expiration_offset, and batch_size.
    client.send(token,
                alert,
                expiration=int(time.time() + 604800),
                error_timeout=5,
                batch_size=200)

    # Get expired tokens.
    expired_tokens = client.get_expired_tokens()

    # Close APNS connection
    client.close()


For the APNS sandbox, use ``APNSSandboxClient`` instead:


.. code-block:: python

    from pushjack import APNSSandboxClient


GCM
---

Send notifications using the ``GCMClient`` class:


.. code-block:: python

    from pushjack import GCMClient

    client = GCMClient(api_key='<api-key>')

    registration_id = '<registration id>'
    alert = 'Hello world.'
    notification = {'title': 'Title', 'body': 'Body', 'icon': 'icon'}

    # Send to single device.
    # NOTE: Keyword arguments are optional.
    res = client.send(registration_id,
                      alert,
                      notification=notification,
                      collapse_key='collapse_key',
                      delay_while_idle=True,
                      time_to_live=604800)

    # Alert can also be be a dictionary with data fields.
    alert = {'message': 'Hello world', 'custom_field': 'Custom Data'}

    # Alert can also contain the notification payload.
    alert = {'message': 'Hello world', 'notification': notification}

    # List of requests.Response objects from GCM Server.
    res.responses

    # List of messages sent.
    res.messages

    # List of registration ids sent.
    res.registration_ids

    # List of server response data from GCM.
    res.data

    # List of successful registration ids.
    res.successes

    # List of failed registration ids.
    res.failures

    # List of exceptions.
    res.errors

    # List of canonical ids (registration ids that have changed).
    res.canonical_ids


    # Send to multiple devices by passing a list of ids.
    client.send([registration_id], alert, **options)


For more details, please see the full documentation at http://pushjack.readthedocs.org.


.. |version| image:: http://img.shields.io/pypi/v/pushjack.svg?style=flat-square
    :target: https://pypi.python.org/pypi/pushjack/

.. |travis| image:: http://img.shields.io/travis/dgilland/pushjack/master.svg?style=flat-square
    :target: https://travis-ci.org/dgilland/pushjack

.. |coveralls| image:: http://img.shields.io/coveralls/dgilland/pushjack/master.svg?style=flat-square
    :target: https://coveralls.io/r/dgilland/pushjack

.. |license| image:: http://img.shields.io/pypi/l/pushjack.svg?style=flat-square
    :target: https://pypi.python.org/pypi/pushjack/
