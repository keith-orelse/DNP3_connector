"""
Validation utilities for DNP3 Client configuration parameters.
"""

import ipaddress
from typing import Tuple, Optional


def validate_ip_address(ip_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validates an IPv4 or IPv6 address string.
    Returns (is_valid, error_message).
    """
    if not ip_str or not isinstance(ip_str, str):
        return False, "IP address cannot be empty."
    
    cleaned = ip_str.strip()
    try:
        ipaddress.ip_address(cleaned)
        return True, None
    except ValueError:
        return False, f"Invalid IP address format: '{ip_str}'. Expected valid IPv4 (e.g. 192.168.1.20) or IPv6."


def validate_port(port: int) -> Tuple[bool, Optional[str]]:
    """
    Validates TCP/UDP port number (1 to 65535).
    Returns (is_valid, error_message).
    """
    try:
        port_int = int(port)
        if 1 <= port_int <= 65535:
            return True, None
        return False, f"Port number {port} is out of valid range (1-65535)."
    except (ValueError, TypeError):
        return False, f"Invalid port value: '{port}'. Must be an integer."


def validate_dnp3_address(address: int, label: str = "DNP3 Address") -> Tuple[bool, Optional[str]]:
    """
    Validates DNP3 Link Layer Address (0 to 65519, reserving broadcast addresses 65520-65535).
    Returns (is_valid, error_message).
    """
    try:
        addr_int = int(address)
        if 0 <= addr_int <= 65519:
            return True, None
        elif 65520 <= addr_int <= 65535:
            return False, f"{label} {addr_int} is reserved for DNP3 broadcast (65520-65535)."
        return False, f"{label} {address} is out of valid DNP3 range (0-65519)."
    except (ValueError, TypeError):
        return False, f"Invalid {label} value: '{address}'. Must be an integer."


def validate_polling_interval(interval_ms: int) -> Tuple[bool, Optional[str]]:
    """
    Validates polling interval in milliseconds (min 100ms, max 3600000ms).
    """
    try:
        val = int(interval_ms)
        if 100 <= val <= 3600000:
            return True, None
        return False, f"Polling interval {interval_ms}ms out of range (100ms - 3600000ms)."
    except (ValueError, TypeError):
        return False, f"Invalid polling interval: '{interval_ms}'. Must be an integer."
