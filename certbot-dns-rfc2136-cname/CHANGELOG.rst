Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_
and this project adheres to `Semantic Versioning <https://semver.org/>`.

4.1.0.dev1 (2025-04-28)
-----------------------

- Add CNAME-following support for DNS-01 challenges.
- Allow resolving and following multiple chained CNAME records during validation.
- Introduce two new CLI options:
  - ``--dns-rfc2136-cname-follow``: enable CNAME following (optional).
  - ``--dns-rfc2136-cname-depth {integer|auto}``: limit maximum CNAME depth or auto-detect loops.
- Adapt internal client logic to dynamically follow CNAME targets before SOA lookup and dynamic update.
- Improve test coverage with unit and integration tests for CNAME handling.
- **Breaking change** for developers: ``_find_domain()`` now returns a tuple (base zone, resolved record_name).
- Fully compatible with Certbot 4.x plugin API.

0.1.0 - 2025-04-28
------------------

**Added**

- Initial fork of ``certbot-dns-rfc2136``.
- Setup standalone pip-installable project structure.
- No changes to original behavior yet; all functionality matches upstream plugin.

Future versions will introduce:

- Optional CNAME following for DNS-01 challenges.
- Configurable maximum CNAME depth.
- Automatic CNAME loop detection.
- Comprehensive unit test coverage.
