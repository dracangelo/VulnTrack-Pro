"""
Utility functions for target management including CIDR expansion and hostname resolution.
"""
import ipaddress
import socket
import re


def validate_cidr(cidr_notation):
    """
    Validate CIDR notation format.
    
    Args:
        cidr_notation (str): CIDR notation string (e.g., "192.168.1.0/24")
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        ipaddress.ip_network(cidr_notation, strict=False)
        return True
    except (ValueError, TypeError):
        return False


def expand_cidr(cidr_notation):
    """
    Expand CIDR notation into a list of individual IP addresses.
    Excludes network and broadcast addresses for IPv4.
    
    Args:
        cidr_notation (str): CIDR notation string (e.g., "192.168.1.0/24")
    
    Returns:
        list: List of IP address strings
    
    Raises:
        ValueError: If CIDR notation is invalid
    """
    try:
        network = ipaddress.ip_network(cidr_notation, strict=False)
        
        # For IPv4, exclude network and broadcast addresses
        if network.version == 4:
            # For /31 and /32, include all addresses
            if network.prefixlen >= 31:
                return [str(ip) for ip in network.hosts()] or [str(network.network_address)]
            else:
                # Exclude network and broadcast addresses
                return [str(ip) for ip in network.hosts()]
        else:
            # For IPv6, include all addresses
            return [str(ip) for ip in network.hosts()]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid CIDR notation: {cidr_notation}") from e


def validate_hostname(hostname):
    """
    Validate hostname format.
    
    Args:
        hostname (str): Hostname to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not hostname or len(hostname) > 253:
        return False
    
    # Remove trailing dot if present
    if hostname.endswith('.'):
        hostname = hostname[:-1]
    
    # Hostname regex pattern
    pattern = re.compile(
        r'^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$'
    )
    
    return bool(pattern.match(hostname))


def resolve_hostname(hostname):
    """
    Resolve hostname to IP address.
    
    Args:
        hostname (str): Hostname to resolve
    
    Returns:
        str: Resolved IP address
    
    Raises:
        ValueError: If hostname cannot be resolved
    """
    try:
        # Get address info
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        
        # Prefer IPv4 over IPv6
        ipv4_addresses = [info[4][0] for info in addr_info if info[0] == socket.AF_INET]
        if ipv4_addresses:
            return ipv4_addresses[0]
        
        # Fall back to IPv6 if no IPv4 available
        ipv6_addresses = [info[4][0] for info in addr_info if info[0] == socket.AF_INET6]
        if ipv6_addresses:
            return ipv6_addresses[0]
        
        raise ValueError(f"Could not resolve hostname: {hostname}")
    except socket.gaierror as e:
        raise ValueError(f"Could not resolve hostname: {hostname}") from e


def validate_ip_address(ip_address):
    """
    Validate IP address format (IPv4 or IPv6).
    
    Args:
        ip_address (str): IP address to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        ipaddress.ip_address(ip_address)
        return True
    except (ValueError, TypeError):
        return False
