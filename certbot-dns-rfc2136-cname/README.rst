certbot-dns-rfc2136-cname
==========================

A Certbot DNS plugin for RFC 2136 dynamic updates, with optional CNAME following.

This project is a carefully maintained fork of the original ``certbot-dns-rfc2136`` plugin
from the Certbot project (Electronic Frontier Foundation). It is intended for use cases
where the ACME DNS-01 challenge TXT record is CNAMEd to a different domain that the user controls.

The codebase preserves the structure and behavior of the upstream plugin for auditability and traceability,
with minimal initial changes. All modifications are introduced in clearly separated commits.

Project Goals
-------------

- **Auditability:** Maintain maximum similarity with upstream ``certbot-dns-rfc2136``.
- **Security:** Clear separation of modifications; no hidden changes.
- **Functionality:** Allow Certbot to follow CNAMEs automatically during DNS-01 challenges.
- **Compatibility:** Fully compatible with Certbot 2.x and Python 3.9+.

Installation
------------

First, activate your Python virtual environment:

.. code-block:: bash

    python3 -m venv venv
    source venv/bin/activate

Then install the plugin in editable mode:

.. code-block:: bash

    cd certbot-dns-rfc2136-cname
    pip install -e .

Usage
-----

You can use this plugin with Certbot by specifying ``dns-rfc2136-cname`` as the authenticator.

Example:

.. code-block:: bash

    certbot certonly \
      --authenticator dns-rfc2136-cname \
      --dns-rfc2136-cname-credentials /etc/letsencrypt/rfc2136.ini \
      --dns-rfc2136-cname-propagation-seconds 60 \
      --dns-rfc2136-cname-follow \
      --dns-rfc2136-cname-depth auto \
      -d example.com -d '*.example.com'

New Options
^^^^^^^^^^^

- ``--dns-rfc2136-cname-follow``
  Enable CNAME following when inserting TXT records.

- ``--dns-rfc2136-cname-depth {integer|auto}``
  Maximum number of CNAMEs to follow. Default is 1.
  Set to ``auto`` for automatic loop detection.

Compatibility
-------------

- Python 3.9+
- Certbot 2.x
- BIND and other RFC2136-compatible dynamic DNS servers
- Let's Encrypt and other ACME CAs

License
-------

Apache License 2.0

Acknowledgements
-----------------

This plugin is based on the original ``certbot-dns-rfc2136`` plugin developed by the Certbot Project at EFF.

