Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_
and this project adheres to `Semantic Versioning <https://semver.org/>`.

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
