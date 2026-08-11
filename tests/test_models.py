"""
Unit tests for normalized measurement models and quality/timestamp parsers.
"""

import pytest
from dnp3.models import (
    DNP3Measurement,
    parse_dnp3_quality,
    parse_dnp3_timestamp,
    TYPE_ANALOG_INPUT,
    TYPE_BINARY_INPUT,
    TYPE_COUNTER,
)


def test_measurement_normalization():
    m = DNP3Measurement(
        type=TYPE_ANALOG_INPUT,
        index=0,
        value=230.5,
        quality="ONLINE",
        timestamp="2026-08-11 12:00:00.000",
        source="outstation"
    )
    d = m.to_dict()
    assert d["protocol"] == "DNP3"
    assert d["type"] == TYPE_ANALOG_INPUT
    assert d["index"] == 0
    assert d["value"] == 230.5
    assert d["quality"] == "ONLINE"

    m_reconstructed = DNP3Measurement.from_dict(d)
    assert m_reconstructed == m


def test_parse_dnp3_quality():
    q_online = parse_dnp3_quality(0x01, TYPE_ANALOG_INPUT)
    assert "ONLINE" in q_online

    q_offline = parse_dnp3_quality(0x00, TYPE_ANALOG_INPUT)
    assert "OFFLINE" in q_offline

    q_overrange = parse_dnp3_quality(0x21, TYPE_ANALOG_INPUT)
    assert "ONLINE" in q_overrange
    assert "OVERRANGE" in q_overrange

    q_chatter = parse_dnp3_quality(0x21, TYPE_BINARY_INPUT)
    assert "ONLINE" in q_chatter
    assert "CHATTER_FILTER" in q_chatter


def test_parse_dnp3_timestamp():
    ts = parse_dnp3_timestamp(1700000000000)
    assert ts != "N/A"
    assert "2023" in ts

    ts_none = parse_dnp3_timestamp(None)
    assert ts_none == "N/A"
