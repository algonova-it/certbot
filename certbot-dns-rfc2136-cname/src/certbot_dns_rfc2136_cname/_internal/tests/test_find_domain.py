import sys
import pytest
from unittest import mock
from certbot.errors import PluginError
from certbot_dns_rfc2136_cname._internal.dns_rfc2136 import _RFC2136Client
import dns.name
import dns.rdtypes
import dns.rdatatype

SERVER = '192.0.2.1'
PORT = 53
NAME = 'a-tsig-key.'
SECRET = 'SSB3b25kZXIgd2hvIHdpbGwgYm90aGVyIHRvIGRlY29kZSB0aGlzIHRleHQK'


def make_txt_answer(target):
    """Create a dummy DNS answer for a CNAME."""
    mock_answer = mock.Mock()
    mock_answer.target = dns.name.from_text(target)
    return [mock_answer]

def make_no_answer():
    """Simulate no CNAME answer."""
    raise dns.resolver.NoAnswer()

def test_find_domain_with_single_cname(monkeypatch):
    client = _RFC2136Client(SERVER, PORT, NAME, SECRET, dns.tsig.HMAC_MD5,
        False, True, 5)

    monkeypatch.setattr('dns.resolver.resolve', lambda name, rdtype: make_txt_answer('real._acme-challenge.example.com') if name == '_acme-challenge.example.com' else make_no_answer())
    monkeypatch.setattr(client, '_query_soa', lambda domain: True)

    zone, record = client._find_domain('_acme-challenge.example.com')
    assert record == 'real._acme-challenge.example.com'
    assert zone == 'real._acme-challenge.example.com'

def test_find_domain_with_cname_loop(monkeypatch):
    client = _RFC2136Client(SERVER, PORT, NAME, SECRET, dns.tsig.HMAC_MD5,
        False, True, 0)

    def loop_cname(name, rdtype):
        if name == '_acme-challenge.example.com':
            return make_txt_answer('_acme-challenge2.example.com')
        elif name == '_acme-challenge2.example.com':
            return make_txt_answer('_acme-challenge.example.com')
        else:
            return make_no_answer()

    monkeypatch.setattr('dns.resolver.resolve', loop_cname)

    with pytest.raises(Exception) as excinfo:
        client._find_domain('_acme-challenge.example.com')
    assert "loop" in str(excinfo.value)

def test_find_domain_max_depth(monkeypatch):
    client = _RFC2136Client(SERVER, PORT, NAME, SECRET, dns.tsig.HMAC_MD5,
        False, True, 1)

    def one_cname(name, rdtype):
        if name == '_acme-challenge.example.com':
            return make_txt_answer('_acme-challenge2.example.com')
        else:
            return make_txt_answer('_acme-challenge3.example.com')

    monkeypatch.setattr('dns.resolver.resolve', one_cname)
    monkeypatch.setattr(client, '_query_soa', lambda domain: True)

    with pytest.raises(PluginError) as excinfo:
        client._find_domain('_acme-challenge.example.com')

    assert "Reached maximum CNAME depth" in str(excinfo.value)


if __name__ == "__main__":
    sys.exit(pytest.main(sys.argv[1:] + [__file__]))  # pragma: no cover
