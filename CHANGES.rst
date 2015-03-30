.. _changelog:

Changelog
=========


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
