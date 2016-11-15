.. _api:

API Reference
=============


APNS
----

.. automodule:: pushjack.apns
    :members:


Exceptions
++++++++++

The :class:`.APNSServerError` class of exceptions represent error responses from APNS. These exceptions will contain attributes for ``code``, ``description``, and ``identifier``. The ``identifier`` attribute is the list index of the token that failed. However, none of these exceptions will be raised directly. Instead, APNS server errors are collected and packaged into a :class:`.APNSResponse` object and returned by :meth:`.APNSClient.send`. This object provides a list of the raw exceptions as well as a mapping of the actual token and its associated error.

Below is a listing of APNS Server exceptions:


=====================================  ====  ====================
Exception                              Code  Description
=====================================  ====  ====================
:class:`.APNSProcessingError`          1     Processing error
:class:`.APNSMissingTokenError`        2     Missing token
:class:`.APNSMissingTopicError`        3     Missing topic
:class:`.APNSMissingPayloadError`      4     Missing payload
:class:`.APNSInvalidTokenSizeError`    5     Invalid token size
:class:`.APNSInvalidTopicSizeError`    6     Invalid topic size
:class:`.APNSInvalidPayloadSizeError`  7     Invalid payload size
:class:`.APNSInvalidTokenError`        8     Invalid token
:class:`.APNSShutdownError`            10    Shutdown
:class:`.APNSUnknownError`             255   Unknown
=====================================  ====  ====================


.. autoclass:: pushjack.exceptions.APNSError
    :members:

.. autoclass:: pushjack.exceptions.APNSAuthError
    :members:

.. autoclass:: pushjack.exceptions.APNSServerError
    :members:

.. autoclass:: pushjack.exceptions.APNSProcessingError
    :members:

.. autoclass:: pushjack.exceptions.APNSMissingTokenError
    :members:

.. autoclass:: pushjack.exceptions.APNSMissingTopicError
    :members:

.. autoclass:: pushjack.exceptions.APNSMissingPayloadError
    :members:

.. autoclass:: pushjack.exceptions.APNSInvalidTokenSizeError
    :members:

.. autoclass:: pushjack.exceptions.APNSInvalidTopicSizeError
    :members:

.. autoclass:: pushjack.exceptions.APNSInvalidPayloadSizeError
    :members:

.. autoclass:: pushjack.exceptions.APNSInvalidTokenError
    :members:

.. autoclass:: pushjack.exceptions.APNSShutdownError
    :members:

.. autoclass:: pushjack.exceptions.APNSUnknownError
    :members:


GCM
---

.. automodule:: pushjack.gcm
    :members:


Exceptions
++++++++++

The :class:`.GCMServerError` class of exceptions are contained in :attr:`.GCMResponse.errors`. Each exception contains attributes for ``code``, ``description``, and ``identifier`` (i.e. the registration ID that failed).

Below is a listing of GCM Server exceptions:


===========================================  =========================  =======================
Exception                                    Code                       Description
===========================================  =========================  =======================
:class:`.GCMMissingRegistrationError`        MissingRegistration        Missing registration ID
:class:`.GCMInvalidRegistrationError`        InvalidRegistration        Invalid registration ID
:class:`.GCMUnregisteredDeviceError`         NotRegistered              Device not registered
:class:`.GCMInvalidPackageNameError`         InvalidPackageName         Invalid package name
:class:`.GCMMismatchedSenderError`           MismatchSenderId           Mismatched sender ID
:class:`.GCMMessageTooBigError`              MessageTooBig              Message too big
:class:`.GCMInvalidDataKeyError`             InvalidDataKey             Invalid data key
:class:`.GCMInvalidTimeToLiveError`          InvalidTtl                 Invalid time to live
:class:`.GCMTimeoutError`                    Unavailable                Timeout
:class:`.GCMInternalServerError`             InternalServerError        Internal server error
:class:`.GCMDeviceMessageRateExceededError`  DeviceMessageRateExceeded  Message rate exceeded
===========================================  =========================  =======================


.. autoclass:: pushjack.exceptions.GCMError
    :members:

.. autoclass:: pushjack.exceptions.GCMAuthError
    :members:

.. autoclass:: pushjack.exceptions.GCMServerError
    :members:

.. autoclass:: pushjack.exceptions.GCMMissingRegistrationError
    :members:

.. autoclass:: pushjack.exceptions.GCMInvalidRegistrationError
    :members:

.. autoclass:: pushjack.exceptions.GCMUnregisteredDeviceError
    :members:

.. autoclass:: pushjack.exceptions.GCMInvalidPackageNameError
    :members:

.. autoclass:: pushjack.exceptions.GCMMismatchedSenderError
    :members:

.. autoclass:: pushjack.exceptions.GCMMessageTooBigError
    :members:

.. autoclass:: pushjack.exceptions.GCMInvalidDataKeyError
    :members:

.. autoclass:: pushjack.exceptions.GCMInvalidTimeToLiveError
    :members:

.. autoclass:: pushjack.exceptions.GCMTimeoutError
    :members:

.. autoclass:: pushjack.exceptions.GCMInternalServerError
    :members:

.. autoclass:: pushjack.exceptions.GCMDeviceMessageRateExceededError
    :members:


Logging
-------

Internal logging is handled with the `logging module <https://docs.python.org/library/logging.html>`_. The logger names used are:

- ``pushjack``
- ``pushjack.apns``
- ``pushjack.gcm``


Enabling
++++++++

To enable logging using an imperative approach:

.. code-block:: python

    import logging
    import pushjack

    logger = logging.getLogger('pushjack')
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)


To enable logging using a configuration approach:

.. code-block:: python

    import logging
    import logging.config
    import pushjack

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG'
            }
        },
        'loggers': {
            'pushjack': {
                'handlers': ['console']
            }
        }
    })

For additional configuration options, you may wish to install `logconfig <https://logconfig.readthedocs.io/>`_:

::

    pip install logconfig


.. code-block:: python

    import logconfig
    import pushjack

    logconfig.from_yaml('path/to/logconfig.yml')
