"""
DNP3 Measurement Normalizer Module.
Translates structured DNP3 headers and point records into normalized DNP3Measurement objects.
Ensures zero value-based measurement type guessing.
"""

import re
from typing import List, Optional, Dict
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
from utils.logger import get_logger

_logger = get_logger()

# DNP3 Object Group Number -> Application Measurement Type Mapping
GROUP_TYPE_MAP: Dict[int, str] = {
    1: TYPE_BINARY_INPUT,
    2: TYPE_BINARY_INPUT,
    3: TYPE_BINARY_INPUT,
    4: TYPE_BINARY_INPUT,
    10: TYPE_BINARY_OUTPUT_STATUS,
    20: TYPE_COUNTER,
    21: TYPE_FROZEN_COUNTER,
    22: TYPE_COUNTER,
    23: TYPE_FROZEN_COUNTER,
    30: TYPE_ANALOG_INPUT,
    32: TYPE_ANALOG_INPUT,
    40: TYPE_ANALOG_OUTPUT_STATUS,
    42: TYPE_ANALOG_OUTPUT_STATUS,
}


class MeasurementNormalizer:
    """
    Parses OpenDNP3 C++ PrintingSOEHandler output stream line-by-line using DNP3 Group metadata.
    Completely eliminates numerical value-based data type guessing.
    Does NOT default unknown DNP3 groups to ANALOG_INPUT.
    """

    def __init__(self):
        self.current_group: Optional[int] = 30
        self.current_variation: Optional[int] = 1
        self.current_data_type: Optional[str] = TYPE_ANALOG_INPUT

        # Regex patterns for PrintingSOEHandler output
        # Header: Group30Var1, Count: 3, Qualifier: 0x00
        self.header_pattern = re.compile(r'Header:\s*Group(\d+)Var(\d+)', re.IGNORECASE)

        # Record: [0] : 230.5 : 1 : 0  (Index : Value : Flags : Time)
        self.record_pattern_4 = re.compile(r'^\s*\[(\d+)\]\s*:\s*([^:]+)\s*:\s*(\d+)\s*:\s*(\d+)')
        # Record fallback: [0] : 230.5 : 1
        self.record_pattern_3 = re.compile(r'^\s*\[(\d+)\]\s*:\s*([^:]+)\s*:\s*(\d+)')

    def parse_line(self, line: str) -> Optional[DNP3Measurement]:
        """
        Parses a single line of text from PrintingSOEHandler stream.
        Updates internal Group state or returns a normalized DNP3Measurement object.
        Returns None for unsupported or unknown DNP3 groups.
        """
        line_str = line.strip()
        if not line_str:
            return None

        # Check for Header line (e.g. Header: Group30Var1)
        h_match = self.header_pattern.search(line_str)
        if h_match:
            try:
                group = int(h_match.group(1))
                variation = int(h_match.group(2))
                self.current_group = group
                self.current_variation = variation
                mapped_type = GROUP_TYPE_MAP.get(group)
                if mapped_type is None:
                    _logger.debug(f"Ignoring unsupported/unmapped DNP3 group {group}Var{variation}")
                    self.current_data_type = None
                else:
                    self.current_data_type = mapped_type
            except Exception as e:
                _logger.debug(f"Failed to parse header line '{line_str}': {e}")
            return None

        # Check for Header string fallback (e.g., "Binary Input" or "Analog Input")
        if "Header:" in line_str or "Group" in line_str:
            if "Binary Output" in line_str:
                self.current_data_type = TYPE_BINARY_OUTPUT_STATUS
            elif "Binary" in line_str:
                self.current_data_type = TYPE_BINARY_INPUT
            elif "Analog Output" in line_str:
                self.current_data_type = TYPE_ANALOG_OUTPUT_STATUS
            elif "Analog" in line_str:
                self.current_data_type = TYPE_ANALOG_INPUT
            elif "Frozen Counter" in line_str:
                self.current_data_type = TYPE_FROZEN_COUNTER
            elif "Counter" in line_str:
                self.current_data_type = TYPE_COUNTER
            else:
                self.current_data_type = None
            return None

        # Ignore records if current group is unsupported / unmapped
        if self.current_data_type is None:
            return None

        # Check for point record line
        rec_match = self.record_pattern_4.search(line_str)
        source_ts_ms = 0
        if rec_match:
            idx = int(rec_match.group(1))
            raw_v = rec_match.group(2).strip()
            flags = int(rec_match.group(3))
            source_ts_ms = int(rec_match.group(4))
        else:
            rec_match = self.record_pattern_3.search(line_str)
            if rec_match:
                idx = int(rec_match.group(1))
                raw_v = rec_match.group(2).strip()
                flags = int(rec_match.group(3))
            else:
                return None

        # Value coercion strictly based on current_data_type (NO VALUE MAGNITUDE GUESSING)
        val = self._coerce_value(raw_v, self.current_data_type)

        # Quality flag conversion
        quality = parse_dnp3_quality(flags, self.current_data_type)

        # Timestamp conversion
        timestamp = parse_dnp3_timestamp(source_ts_ms if source_ts_ms > 0 else None)

        return DNP3Measurement(
            protocol="DNP3",
            type=self.current_data_type,
            index=idx,
            value=val,
            quality=quality,
            timestamp=timestamp,
            source="outstation",
            raw_flags=flags,
            group=self.current_group,
            variation=self.current_variation
        )

    def parse_text_stream(self, text: str) -> List[DNP3Measurement]:
        """
        Parses a multi-line text stream and returns a list of normalized DNP3Measurement objects.
        """
        measurements = []
        if not text:
            return measurements

        for line in text.splitlines():
            try:
                m = self.parse_line(line)
                if m:
                    measurements.append(m)
            except Exception as e:
                _logger.debug(f"Error parsing line '{line}': {e}")
        return measurements

    def _coerce_value(self, raw_v: str, data_type: str):
        """Coerces raw string value to appropriate Python type based on DNP3 data_type."""
        if data_type in (TYPE_BINARY_INPUT, TYPE_BINARY_OUTPUT_STATUS):
            return raw_v.lower() in ("true", "1")
        elif data_type in (TYPE_ANALOG_INPUT, TYPE_ANALOG_OUTPUT_STATUS):
            try:
                val = float(raw_v)
                return round(val, 4)
            except ValueError:
                return raw_v
        elif data_type in (TYPE_COUNTER, TYPE_FROZEN_COUNTER):
            try:
                return int(float(raw_v))
            except ValueError:
                return raw_v
        return raw_v
