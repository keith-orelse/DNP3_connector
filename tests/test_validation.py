"""
Unit tests for validation functions in utils/validation.py.
"""

import pytest
from utils.validation import (
    validate_ip_address,
    validate_port,
    validate_dnp3_address,
    validate_polling_interval,
)


def test_validate_ip_address():
    ok, err = validate_ip_address("192.168.1.20")
    assert ok is True
    assert err is None

    ok, err = validate_ip_address("127.0.0.1")
    assert ok is True

    ok, err = validate_ip_address("invalid_ip")
    assert ok is False
    assert "Invalid IP address" in err

    ok, err = validate_ip_address("")
    assert ok is False


def test_validate_port():
    ok, err = validate_port(20000)
    assert ok is True

    ok, err = validate_port("20000")
    assert ok is True

    ok, err = validate_port(0)
    assert ok is False

    ok, err = validate_port(70000)
    assert ok is False


def test_validate_dnp3_address():
    ok, err = validate_dnp3_address(1)
    assert ok is True

    ok, err = validate_dnp3_address(1024)
    assert ok is True

    ok, err = validate_dnp3_address(65519)
    assert ok is True

    ok, err = validate_dnp3_address(65520)  # Broadcast address
    assert ok is False
    assert "reserved for DNP3 broadcast" in err

    ok, err = validate_dnp3_address(-1)
    assert ok is False


def test_validate_polling_interval():
    ok, err = validate_polling_interval(1000)
    assert ok is True

    ok, err = validate_polling_interval(50)  # Too small
    assert ok is False

    ok, err = validate_polling_interval(5000000)  # Too large
    assert ok is False
