.. _changelog:

Changelog
=========


v0.1.0 (2015-03-26)
-------------------

- Rename ``pushjack.settings`` module to ``pushjack.config``. (**breaking change**)
- Allow config settings overrides to be passed into ``create_gcm_config``, ``create_apns_config``, and ``create_apns_sandbox_config``.
- Override ``Config``'s ``update()`` method with custom method that functions similarly to ``from_object()`` except that it accepts a ``dict`` instead.


v0.0.1 (2015-03-25)
-------------------

- First release.
