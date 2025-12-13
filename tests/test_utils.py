import pytest
import socket
from unittest.mock import patch, MagicMock
from api.utils.target_utils import (
    validate_cidr, expand_cidr,
    validate_hostname, resolve_hostname,
    validate_ip_address
)

class TestTargetUtils:
    
    # CIDR Validation Tests
    def test_validate_cidr_valid(self):
        assert validate_cidr('192.168.1.0/24') is True
        assert validate_cidr('10.0.0.0/8') is True
        assert validate_cidr('2001:db8::/32') is True

    def test_validate_cidr_invalid(self):
        assert validate_cidr('192.168.1.256/24') is False
        assert validate_cidr('invalid') is False
        assert validate_cidr('192.168.1.1') is False # Missing mask (though ip_network might accept it, strict=False handles it differently depending on implementation, let's check behavior)
        # ipaddress.ip_network('192.168.1.1', strict=False) creates a /32. 
        # But usually we want explicit CIDR. 
        # The current implementation allows single IPs as /32 if strict=False.
        # Let's verify what we expect. The code uses strict=False.
        
    def test_validate_cidr_edge_cases(self):
        assert validate_cidr('0.0.0.0/0') is True
        
    # CIDR Expansion Tests
    def test_expand_cidr_ipv4(self):
        # /30 gives 4 IPs. Network and Broadcast excluded -> 2 IPs.
        ips = expand_cidr('192.168.1.0/30')
        assert len(ips) == 2
        assert '192.168.1.1' in ips
        assert '192.168.1.2' in ips
        assert '192.168.1.0' not in ips
        assert '192.168.1.3' not in ips

    def test_expand_cidr_ipv4_small(self):
        # /31 and /32 should include all
        ips_31 = expand_cidr('192.168.1.0/31')
        assert len(ips_31) == 2
        
        ips_32 = expand_cidr('192.168.1.1/32')
        assert len(ips_32) == 1
        assert ips_32[0] == '192.168.1.1'

    def test_expand_cidr_invalid(self):
        with pytest.raises(ValueError):
            expand_cidr('invalid')

    # Hostname Validation Tests
    def test_validate_hostname_valid(self):
        assert validate_hostname('example.com') is True
        assert validate_hostname('sub.example.com') is True
        assert validate_hostname('localhost') is True
        assert validate_hostname('http://example.com') is True
        assert validate_hostname('https://example.com/path') is True

    def test_validate_hostname_invalid(self):
        assert validate_hostname('-start.com') is False
        assert validate_hostname('end-.com') is False
        assert validate_hostname('a' * 256) is False
        assert validate_hostname('') is False

    # Hostname Resolution Tests
    @patch('socket.getaddrinfo')
    def test_resolve_hostname_ipv4(self, mock_getaddrinfo):
        # Mock socket.getaddrinfo to return IPv4
        mock_getaddrinfo.return_value = [
            (2, 1, 6, '', ('192.168.1.1', 0))
        ]
        assert resolve_hostname('example.com') == '192.168.1.1'

    @patch('socket.getaddrinfo')
    def test_resolve_hostname_ipv6(self, mock_getaddrinfo):
        # Mock socket.getaddrinfo to return IPv6 only
        mock_getaddrinfo.return_value = [
            (10, 1, 6, '', ('2001:db8::1', 0, 0, 0))
        ]
        assert resolve_hostname('ipv6.example.com') == '2001:db8::1'

    @patch('socket.getaddrinfo')
    def test_resolve_hostname_failure(self, mock_getaddrinfo):
        mock_getaddrinfo.side_effect = socket.gaierror("DNS Error")
        with pytest.raises(ValueError):
            resolve_hostname('invalid.local')

    # IP Validation Tests
    def test_validate_ip_valid(self):
        assert validate_ip_address('192.168.1.1') is True
        assert validate_ip_address('2001:db8::1') is True

    def test_validate_ip_invalid(self):
        assert validate_ip_address('256.256.256.256') is False
        assert validate_ip_address('invalid') is False
