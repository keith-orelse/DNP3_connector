"""
Automated Test Suite for DNP3 Protocol Measurement Normalization.
Verifies Group-based measurement type normalization, quality bitmask conversion,
ISO-8601 timestamps, type stability regardless of value magnitude, and error handling.
"""

import pytest
from dnp3.models import (
    DNP3Measurement,
    TYPE_BINARY_INPUT,
    TYPE_ANALOG_INPUT,
    TYPE_COUNTER,
    TYPE_FROZEN_COUNTER,
    TYPE_BINARY_OUTPUT_STATUS,
    TYPE_ANALOG_OUTPUT_STATUS,
    parse_dnp3_quality,
    parse_dnp3_timestamp,
)
from dnp3.normalizer import MeasurementNormalizer


def test_analog_input_normalization():
    normalizer = MeasurementNormalizer()
    text = "Header: Group30Var1\n  [0] : 230.5 : 1 : 0\n  [1] : 10.2 : 1 : 0"
    measurements = normalizer.parse_text_stream(text)

    assert len(measurements) == 2
    m0 = measurements[0]
    assert m0.type == TYPE_ANALOG_INPUT
    assert m0.index == 0
    assert m0.value == 230.5
    assert m0.quality == "ONLINE"
    assert "T" in m0.timestamp and "Z" in m0.timestamp
    assert m0.group == 30
    assert m0.variation == 1


def test_binary_input_normalization():
    normalizer = MeasurementNormalizer()
    text = "Header: Group1Var2\n  [0] : 1 : 129 : 0\n  [1] : 0 : 1 : 0"
    measurements = normalizer.parse_text_stream(text)

    assert len(measurements) == 2
    m0, m1 = measurements[0], measurements[1]

    assert m0.type == TYPE_BINARY_INPUT
    assert m0.index == 0
    assert m0.value is True
    assert "ONLINE" in m0.quality
    assert "RESTART" in m0.quality

    assert m1.type == TYPE_BINARY_INPUT
    assert m1.index == 1
    assert m1.value is False
    assert m1.quality == "ONLINE"


def test_counter_normalization():
    normalizer = MeasurementNormalizer()
    text = "Header: Group20Var1\n  [0] : 1005 : 1 : 0"
    measurements = normalizer.parse_text_stream(text)

    assert len(measurements) == 1
    m0 = measurements[0]
    assert m0.type == TYPE_COUNTER
    assert m0.index == 0
    assert m0.value == 1005
    assert m0.quality == "ONLINE"


def test_output_status_and_frozen_counter_normalization():
    normalizer = MeasurementNormalizer()
    text = """
Header: Group10Var2
  [0] : 1 : 1 : 0
Header: Group40Var1
  [0] : 100.5 : 1 : 0
Header: Group21Var1
  [0] : 5000 : 1 : 0
"""
    measurements = normalizer.parse_text_stream(text)
    assert len(measurements) == 3

    m_bo = measurements[0]
    assert m_bo.type == TYPE_BINARY_OUTPUT_STATUS
    assert m_bo.index == 0
    assert m_bo.value is True

    m_ao = measurements[1]
    assert m_ao.type == TYPE_ANALOG_OUTPUT_STATUS
    assert m_ao.index == 0
    assert m_ao.value == 100.5

    m_fc = measurements[2]
    assert m_fc.type == TYPE_FROZEN_COUNTER
    assert m_fc.index == 0
    assert m_fc.value == 5000


def test_unsupported_dnp3_group_ignored_safely():
    """
    Verifies that unknown/unsupported DNP3 groups (e.g., Group 50 TimeAndInterval or Group 120)
    are ignored safely without being defaulted to ANALOG_INPUT or throwing exceptions.
    """
    normalizer = MeasurementNormalizer()
    text = """
Header: Group50Var1
  [0] : 1700000000 : 1 : 0
Header: Group120Var1
  [0] : 9999 : 1 : 0
Header: Group30Var1
  [0] : 230.5 : 1 : 0
"""
    measurements = normalizer.parse_text_stream(text)
    assert len(measurements) == 1
    assert measurements[0].type == TYPE_ANALOG_INPUT
    assert measurements[0].index == 0
    assert measurements[0].value == 230.5


def test_high_analog_value_remains_analog_input_regression():
    """
    CRITICAL REGRESSION TEST:
    Analog Input index 0 with value 1000.0 MUST remain ANALOG_INPUT.
    It MUST NEVER be mutated into a COUNTER merely because value > 500.
    """
    normalizer = MeasurementNormalizer()
    text = "Header: Group30Var2\n  [0] : 1000.0 : 1 : 0"
    measurements = normalizer.parse_text_stream(text)

    assert len(measurements) == 1
    m = measurements[0]
    assert m.type == TYPE_ANALOG_INPUT
    assert m.value == 1000.0
    assert m.type != TYPE_COUNTER


def test_low_counter_value_remains_counter_regression():
    """
    CRITICAL REGRESSION TEST:
    Counter index 0 with value 10 MUST remain COUNTER.
    It MUST NEVER be mutated into ANALOG_INPUT or BINARY_INPUT.
    """
    normalizer = MeasurementNormalizer()
    text = "Header: Group20Var1\n  [0] : 10 : 1 : 0"
    measurements = normalizer.parse_text_stream(text)

    assert len(measurements) == 1
    m = measurements[0]
    assert m.type == TYPE_COUNTER
    assert m.value == 10


def test_quality_bitmask_parsing_across_data_types():
    # Analog Input Flags
    assert parse_dnp3_quality(0x01, TYPE_ANALOG_INPUT) == "ONLINE"
    assert parse_dnp3_quality(0x00, TYPE_ANALOG_INPUT) == "OFFLINE"
    assert parse_dnp3_quality(0x21, TYPE_ANALOG_INPUT) == "ONLINE | OVERRANGE"
    assert parse_dnp3_quality(0x41, TYPE_ANALOG_INPUT) == "ONLINE | REFERENCE_ERR"

    # Binary Input Flags
    assert parse_dnp3_quality(0x21, TYPE_BINARY_INPUT) == "ONLINE | CHATTER_FILTER"
    assert parse_dnp3_quality(0x81, TYPE_BINARY_INPUT) == "ONLINE | RESTART"

    # Counter / Frozen Counter Flags
    assert parse_dnp3_quality(0x21, TYPE_COUNTER) == "ONLINE | ROLLOVER"
    assert parse_dnp3_quality(0x41, TYPE_COUNTER) == "ONLINE | DISCONTINUITY"
    assert parse_dnp3_quality(0x21, TYPE_FROZEN_COUNTER) == "ONLINE | ROLLOVER"

    # Binary Output Status Flags
    assert parse_dnp3_quality(0x05, TYPE_BINARY_OUTPUT_STATUS) == "ONLINE | COMM_LOST"

    # Analog Output Status Flags
    assert parse_dnp3_quality(0x21, TYPE_ANALOG_OUTPUT_STATUS) == "ONLINE | OVERRANGE"


def test_iso_8601_timestamp_parsing():
    # Valid epoch millisecond timestamp
    ts_str = parse_dnp3_timestamp(1700000000000)
    assert "2023-" in ts_str
    assert "T" in ts_str and "Z" in ts_str

    # Fallback when None or 0
    fallback_ts = parse_dnp3_timestamp(None)
    assert "T" in fallback_ts and "Z" in fallback_ts
    assert len(fallback_ts) >= 20


def test_malformed_lines_handled_safely():
    normalizer = MeasurementNormalizer()
    text = "Corrupted line\nHeader: Invalid\n[bad] : val\nHeader: Group30Var1\n  [0] : 230.5 : 1 : 0"
    measurements = normalizer.parse_text_stream(text)

    # Corrupted lines ignored safely, valid line parsed cleanly
    assert len(measurements) == 1
    assert measurements[0].type == TYPE_ANALOG_INPUT
    assert measurements[0].value == 230.5


def test_dnp3_measurement_serialization():
    m = DNP3Measurement(
        protocol="DNP3",
        type=TYPE_ANALOG_INPUT,
        index=0,
        value=230.5,
        quality="ONLINE",
        timestamp="2026-08-17T12:00:00.000Z",
        raw_flags=1,
        group=30,
        variation=1
    )
    d = m.to_dict()
    assert d["type"] == TYPE_ANALOG_INPUT
    assert d["value"] == 230.5
    assert d["group"] == 30

    m_reconstructed = DNP3Measurement.from_dict(d)
    assert m_reconstructed == m
