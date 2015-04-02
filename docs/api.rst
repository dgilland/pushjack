.. _api:

*************
API Reference
*************


Clients
=======

.. automodule:: pushjack.clients

.. autoclass:: pushjack.clients.APNSClient
    :members: send, send_bulk, get_expired_tokens
    :exclude-members: adapter

.. autoclass:: pushjack.clients.GCMClient
    :members: send, send_bulk
    :exclude-members: adapter


APNS
====

.. automodule:: pushjack.apns
    :members:


GCM
===

.. automodule:: pushjack.gcm
    :members:

.. autoclass:: pushjack.gcm.GCMResponse
    :members: responses, payloads, registration_ids, data, successes, failures, errors, canonical_ids


Configuration
=============

.. automodule:: pushjack.config
    :members:


Exceptions
==========

.. automodule:: pushjack.exceptions
    :members:
