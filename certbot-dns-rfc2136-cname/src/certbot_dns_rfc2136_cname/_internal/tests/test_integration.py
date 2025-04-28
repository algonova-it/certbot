import sys
import pytest
from unittest import mock
import dns.tsig
from certbot_dns_rfc2136_cname._internal.dns_rfc2136 import _RFC2136Client

SERVER = '192.0.2.1'
PORT = 53
NAME = 'a-tsig-key.'
SECRET = 'SSB3b25kZXIgd2hvIHdpbGwgYm90aGVyIHRvIGRlY29kZSB0aGlzIHRleHQK'

def test_real_dns_cname_following(monkeypatch):
    """Test resolving a real CNAME in public DNS."""
    client = _RFC2136Client(SERVER, PORT, NAME, SECRET, dns.tsig.HMAC_MD5,
        False, True, 1)

    monkeypatch.setattr(client, '_query_soa', mock.MagicMock(side_effect=[False, True]))

    validation_name = '_acme-challenge.algonova-it.de'  # Choose a known CNAME domain!

    zone, record = client._find_domain(validation_name)
    assert isinstance(zone, str)
    assert isinstance(record, str)
    assert record != validation_name
    assert record != zone

if __name__ == "__main__":
    sys.exit(pytest.main(sys.argv[1:] + [__file__]))  # pragma: no cover
