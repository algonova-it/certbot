"""DNS Authenticator using RFC 2136 Dynamic Updates."""
import logging
from typing import Any, Union
from typing import Callable
from typing import cast
from typing import Optional

import dns.flags
import dns.message
import dns.name
import dns.query
import dns.rdataclass
import dns.rdatatype
import dns.resolver
import dns.tsig
import dns.tsigkeyring
import dns.update

from certbot import errors
from certbot.plugins import dns_common
from certbot.plugins.dns_common import CredentialsConfiguration
from certbot.util import is_ipaddress

logger = logging.getLogger(__name__)

DEFAULT_NETWORK_TIMEOUT = 45


class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator using RFC 2136 Dynamic Updates

    This Authenticator uses RFC 2136 Dynamic Updates to fulfill a dns-01 challenge.
    """

    ALGORITHMS = {
      'HMAC-MD5': dns.tsig.HMAC_MD5,
      'HMAC-SHA1': dns.tsig.HMAC_SHA1,
      'HMAC-SHA224': dns.tsig.HMAC_SHA224,
      'HMAC-SHA256': dns.tsig.HMAC_SHA256,
      'HMAC-SHA384': dns.tsig.HMAC_SHA384,
      'HMAC-SHA512': dns.tsig.HMAC_SHA512
    }

    PORT = 53

    description = 'Obtain certificates using a DNS TXT record (if you are using BIND for DNS).'
    ttl = 120

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.credentials: Optional[CredentialsConfiguration] = None
        self.follow: bool = False
        self.depth: Union[int, str] = 1

    @classmethod
    def add_parser_arguments(cls, add: Callable[..., None],
                             default_propagation_seconds: int = 60) -> None:
        super().add_parser_arguments(add, default_propagation_seconds=60)
        add('credentials', help='RFC 2136 credentials INI file.')
        add('follow', action='store_true', help='Follow CNAMEs for DNS-01 challenges.')
        add('depth', help='Maximum number of CNAMEs to follow (integer or "auto").')

    def more_info(self) -> str:
        return 'This plugin configures a DNS TXT record to respond to a dns-01 challenge using ' + \
               'RFC 2136 Dynamic Updates. It can follow CNAMEs for the challenge.'

    def _validate_credentials(self, credentials: CredentialsConfiguration) -> None:
        server = cast(str, credentials.conf('server'))
        if not is_ipaddress(server):
            raise errors.PluginError("The configured target DNS server ({0}) is not a valid IPv4 "
                                     "or IPv6 address. A hostname is not allowed.".format(server))
        algorithm = credentials.conf('algorithm')
        if algorithm:
            if not self.ALGORITHMS.get(algorithm.upper()):
                raise errors.PluginError("Unknown algorithm: {0}.".format(algorithm))

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            'credentials',
            'RFC 2136 credentials INI file',
            {
                'name': 'TSIG key name',
                'secret': 'TSIG key secret',
                'server': 'The target DNS server'
            },
            self._validate_credentials
        )

    def _perform(self, _domain: str, validation_name: str, validation: str) -> None:
        follow_conf = self.conf('follow')
        if not follow_conf is None:
            self.follow = follow_conf

        depth_conf = self.conf('depth')
        if not depth_conf is None:
            if depth_conf.lower() == 'auto':
                self.depth = 'auto'
            else:
                try:
                    depth_int = int(depth_conf)
                    if depth_int < 1:
                        raise errors.PluginError("CNAME depth must be >=1 or 'auto'.")
                    self.depth = depth_int
                except ValueError:
                    raise errors.PluginError("Invalid value for CNAME depth: must be an integer or 'auto'.")

        self._get_rfc2136_client().add_txt_record(validation_name, validation, self.ttl)

    def _cleanup(self, _domain: str, validation_name: str, validation: str) -> None:
        self._get_rfc2136_client().del_txt_record(validation_name, validation)

    def _get_rfc2136_client(self) -> "_RFC2136Client":
        if not self.credentials:  # pragma: no cover
            raise errors.Error("Plugin has not been prepared.")

        algorithm: str = (self.credentials.conf('algorithm') or '').upper()

        return _RFC2136Client(cast(str, self.credentials.conf('server')),
                              int(cast(str, self.credentials.conf('port')) or self.PORT),
                              cast(str, self.credentials.conf('name')),
                              cast(str, self.credentials.conf('secret')),
                              self.ALGORITHMS.get(algorithm, dns.tsig.HMAC_MD5),
                              (self.credentials.conf('sign_query') or '').upper() == "TRUE",
                              self.follow,
                              (0 if self.depth == "auto" else self.depth))


class _RFC2136Client:
    """
    Encapsulates all communication with the target DNS server.
    """
    def __init__(self, server: str, port: int, key_name: str, key_secret: str,
                 key_algorithm: dns.name.Name, sign_query: bool,
                 cname_follow: bool, cname_depth: int,
                 timeout: int = DEFAULT_NETWORK_TIMEOUT) -> None:
        self.server = server
        self.port = port
        self.keyring = dns.tsigkeyring.from_text({
            key_name: key_secret
        })
        self.algorithm = key_algorithm
        self.sign_query = sign_query
        self.cname_follow = cname_follow
        self.cname_depth = cname_depth
        self._default_timeout = timeout

    def add_txt_record(self, record_name: str, record_content: str, record_ttl: int) -> None:
        """
        Add a TXT record using the supplied information.

        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :param int record_ttl: The record TTL (number of seconds that the record may be cached).
        :raises certbot.errors.PluginError: if an error occurs communicating with the DNS server
        """

        domain, record_name = self._find_domain(record_name)

        n = dns.name.from_text(record_name)
        o = dns.name.from_text(domain)
        rel = n.relativize(o)

        update = dns.update.Update(
            domain,
            keyring=self.keyring,
            keyalgorithm=self.algorithm)
        update.add(rel, record_ttl, dns.rdatatype.TXT, record_content)

        try:
            response = dns.query.tcp(update, self.server, self._default_timeout, self.port)
        except Exception as e:
            raise errors.PluginError('Encountered error adding TXT record: {0}'
                                     .format(e))
        rcode = response.rcode()

        if rcode == dns.rcode.NOERROR:
            logger.debug('Successfully added TXT record %s', record_name)
        else:
            raise errors.PluginError('Received response from server: {0}'
                                     .format(dns.rcode.to_text(rcode)))

    def del_txt_record(self, record_name: str, record_content: str) -> None:
        """
        Delete a TXT record using the supplied information.

        :param str record_name: The record name (typically beginning with '_acme-challenge.').
        :param str record_content: The record content (typically the challenge validation).
        :param int record_ttl: The record TTL (number of seconds that the record may be cached).
        :raises certbot.errors.PluginError: if an error occurs communicating with the DNS server
        """

        domain, record_name = self._find_domain(record_name)

        n = dns.name.from_text(record_name)
        o = dns.name.from_text(domain)
        rel = n.relativize(o)

        update = dns.update.Update(
            domain,
            keyring=self.keyring,
            keyalgorithm=self.algorithm)
        update.delete(rel, dns.rdatatype.TXT, record_content)

        try:
            response = dns.query.tcp(update, self.server, self._default_timeout, self.port)
        except Exception as e:
            raise errors.PluginError('Encountered error deleting TXT record: {0}'
                                     .format(e))
        rcode = response.rcode()

        if rcode == dns.rcode.NOERROR:
            logger.debug('Successfully deleted TXT record %s', record_name)
        else:
            raise errors.PluginError('Received response from server: {0}'
                                     .format(dns.rcode.to_text(rcode)))

    def _find_domain(self, record_name: str) -> tuple[str, str]:
        """
        Find the authoritative zone for a given record name.

        :param str record_name: The record name for which to find the closest SOA record.
        :returns: The domain or zone, and the record name or the final resolved CNAME.
        :rtype: Tuple[str, str]
        :raises certbot.errors.PluginError: if no SOA record can be found.
        """

        # Follow CNAMEs to find the correct base domain

        if self.cname_follow:
            visited = set()
            hops = 0

            while True:
                if record_name in visited:
                    raise errors.PluginError(f"CNAME loop detected at {record_name}")

                visited.add(record_name)

                try:
                    answers = dns.resolver.resolve(record_name, 'CNAME')
                    target = str(answers[0].target).rstrip('.')
                    logger.debug(f"Following CNAME: {record_name} -> {target}")
                    record_name = target
                    hops += 1

                    if 0 < self.cname_depth < hops:
                        raise errors.PluginError(f"Reached maximum CNAME depth ({self.cname_depth}).")

                except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.LifetimeTimeout,
                        dns.exception.DNSException):
                    # No CNAME found, stop
                    logger.debug(
                        f"No further CNAME for {record_name}, proceeding to find base domain.")
                    break

        # Continue with upstream code

        domain_name_guesses = dns_common.base_domain_name_guesses(record_name)

        # Loop through until we find an authoritative SOA record
        for guess in domain_name_guesses:
            if self._query_soa(guess):
                return guess, record_name

        raise errors.PluginError('Unable to determine base domain for {0} using names: {1}.'
                                 .format(record_name, domain_name_guesses))

    def _query_soa(self, domain_name: str) -> bool:
        """
        Query a domain name for an authoritative SOA record.

        :param str domain_name: The domain name to query for an SOA record.
        :returns: True if found, False otherwise.
        :rtype: bool
        :raises certbot.errors.PluginError: if no response is received.
        """

        domain = dns.name.from_text(domain_name)

        request = dns.message.make_query(domain, dns.rdatatype.SOA, dns.rdataclass.IN)
        # Turn off Recursion Desired bit in query
        request.flags ^= dns.flags.RD
        # Use our TSIG keyring if configured
        if self.sign_query:
            request.use_tsig(self.keyring, algorithm=self.algorithm)

        try:
            try:
                response = dns.query.tcp(request, self.server, self._default_timeout, self.port)
            except (OSError, dns.exception.Timeout) as e:
                logger.debug('TCP query failed, fallback to UDP: %s', e)
                response = dns.query.udp(request, self.server, self._default_timeout, self.port)
            rcode = response.rcode()

            # Authoritative Answer bit should be set
            if (rcode == dns.rcode.NOERROR
                    and response.get_rrset(response.answer,
                                           domain, dns.rdataclass.IN, dns.rdatatype.SOA)
                    and response.flags & dns.flags.AA):
                logger.debug('Received authoritative SOA response for %s', domain_name)
                return True

            logger.debug('No authoritative SOA record found for %s', domain_name)
            return False
        except Exception as e:
            raise errors.PluginError('Encountered error when making query: {0}'
                                     .format(e))
