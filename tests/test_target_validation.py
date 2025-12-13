import pytest
from api.utils.target_utils import validate_ip_address, validate_cidr, validate_hostname

def test_validate_ip_address():
    """Test validation of valid IP addresses"""
    assert validate_ip_address('192.168.1.1') is True
    assert validate_ip_address('10.0.0.1') is True
    assert validate_ip_address('127.0.0.1') is True
    assert validate_ip_address('invalid-ip') is False
    assert validate_ip_address('256.256.256.256') is False

def test_validate_cidr():
    """Test validation of valid CIDR ranges"""
    assert validate_cidr('192.168.1.0/24') is True
    assert validate_cidr('10.0.0.0/8') is True
    assert validate_cidr('192.168.1.1') is False # Missing /
    assert validate_cidr('invalid-cidr') is False

def test_validate_hostname():
    """Test validation of valid hostnames"""
    assert validate_hostname('example.com') is True
    assert validate_hostname('sub.example.com') is True
    assert validate_hostname('localhost') is True
    assert validate_hostname('http://example.com') is True # It strips protocol
    assert validate_hostname('') is False

