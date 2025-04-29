## certbot-dns-rfc2136-cname

A Certbot plugin extending certbot-dns-rfc2136 with automatic CNAME following during DNS-01 challenges.

### About this fork

This plugin was created to overcome limitations when using DNS providers that:

- Do not have an API for creating TXT records,
- Do not allow direct TXT record creation (only delegation via CNAME),
- Do not support subdomain NS records for ACME challenges.

This fork adds transparent CNAME following to the original RFC2136 plugin, enabling successful DNS-01 validation in complex and constrained environments.

The code is based on Certbot's upstream plugin and tracks upstream changes conservatively for long-term maintainability.

### Features

- Fully compatible with Certbot ≥ 2.0.0
- Follows CNAME chains automatically for ```_acme-challenge``` records
- Supports loop detection and depth limiting
- Uses standard RFC 2136 authenticated DNS updates
- Tested with multiple Certbot versions and Python versions

### Project Status

| Certbot Version | Python 3.9 | Python 3.12 | 
|-------------|------------|-------------|
| 2.0.x | ✅ Tested | ✅ Tested | 
| 2.6.x | ✅ Tested | ✅ Tested | 
| 2.9.x | ✅ Tested | ✅ Tested | 
| development | ✅ Tested | ✅ Tested |

### Usage Example

```
certbot certonly \
  --authenticator dns-rfc2136-cname \
  --dns-rfc2136-cname-credentials /etc/letsencrypt/rfc2136.ini \
  --dns-rfc2136-cname-follow \
  --dns-rfc2136-cname-depth auto \
  --dns-rfc2136-cname-propagation-seconds 60 \
  -d example.com -d '*.example.com'
```

Example credentials file (rfc2136.ini):

```
dns_rfc2136_cname_server = 10.0.0.1
dns_rfc2136_cname_name = tsig-key-name
dns_rfc2136_cname_secret = tsig-key-secret
dns_rfc2136_cname_algorithm = HMAC-SHA256
```

### License

- Original work: © EFF Certbot Project
- Fork and CNAME extension: © algoNOVA-IT Lösungen e.K.

Distributed under the Apache License 2.0.

### Contribution and Issues

This project is maintained separately from upstream Certbot.

- For Certbot core issues, use [certbot/certbot](https://github.com/certbot/certbot/issues).
- For this plugin fork issues, create an Issue or PR in this repository.

### Legal

This project is provided by algoNOVA-IT Lösungen e.K.  
For legal information, please see the [IMPRINT](IMPRESSUM.md).
