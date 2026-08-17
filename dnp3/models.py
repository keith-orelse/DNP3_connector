"""
Normalized Measurement Data Model for Arcon DNP3 Client.
Standardizes DNP3 object measurements for internal processing and Arcon integration.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union


# Data Type Constants
TYPE_BINARY_INPUT = "binary_input"
TYPE_ANALOG_INPUT = "analog_input"
TYPE_COUNTER = "counter"
TYPE_FROZEN_COUNTER = "frozen_counter"
TYPE_BINARY_OUTPUT_STATUS = "binary_output_status"
TYPE_ANALOG_OUTPUT_STATUS = "analog_output_status"


@dataclass
class DNP3Measurement:
    """
    Normalized measurement representation compliant with Arcon Connector standards.
    """
    protocol: str = "DNP3"
    type: str = TYPE_ANALOG_INPUT
    index: int = 0
    value: Union[bool, float, int, str] = 0
    quality: str = "ONLINE"
    timestamp: str = "N/A"
    source: str = "outstation"
    raw_flags: int = 0x01
    group: Optional[int] = None
    variation: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts measurement object to normalized dictionary format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DNP3Measurement":
        valid_keys = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        return cls(**filtered)


def parse_dnp3_quality(flags: int, data_type: str = TYPE_ANALOG_INPUT) -> str:
    """
    Parses OpenDNP3 quality flag bitmask into human-readable strings.
    Supported flags: ONLINE, OFFLINE, RESTART, COMM_LOST, REMOTE_FORCED, LOCAL_FORCED, CHATTER_FILTER, OVERRANGE, REFERENCE_ERR
    """
    if flags is None:
        return "UNKNOWN"

    try:
        flags = int(flags)
    except (ValueError, TypeError):
        return "UNKNOWN"

    qualities = []

    # Common Bitmasks across OpenDNP3 Quality Enums
    # Bit 0: ONLINE (0x01)
    # Bit 1 (0x02) or Bit 7 (0x80): RESTART / STATE
    # Bit 2: COMM_LOST (0x04)
    # Bit 3: REMOTE_FORCED (0x08)
    # Bit 4: LOCAL_FORCED (0x10)
    # Bit 5: OVERRANGE / CHATTER_FILTER / ROLLOVER (0x20)
    # Bit 6: REFERENCE_ERR (0x40)

    if flags & 0x01:
        qualities.append("ONLINE")
    else:
        qualities.append("OFFLINE")

    if (flags & 0x02) or (flags & 0x80):
        qualities.append("RESTART")
    if flags & 0x04:
        qualities.append("COMM_LOST")
    if flags & 0x08:
        qualities.append("REMOTE_FORCED")
    if flags & 0x10:
        qualities.append("LOCAL_FORCED")

    if data_type in (TYPE_ANALOG_INPUT, TYPE_ANALOG_OUTPUT_STATUS):
        if flags & 0x20:
            qualities.append("OVERRANGE")
        if flags & 0x40:
            qualities.append("REFERENCE_ERR")
    elif data_type == TYPE_BINARY_INPUT:
        if flags & 0x20:
            qualities.append("CHATTER_FILTER")

    return " | ".join(qualities) if qualities else "ONLINE"


def parse_dnp3_timestamp(dnp_timestamp: Any) -> str:
    """
    Parses OpenDNP3 DNPTime object or epoch timestamp into ISO 8601 string.
    Generates ISO 8601 UTC timestamp if unavailable or zero.
    """
    if dnp_timestamp is not None:
        try:
            millis = getattr(dnp_timestamp, 'value', dnp_timestamp)
            if isinstance(millis, (int, float)) and millis > 0:
                dt = datetime.fromtimestamp(millis / 1000.0, tz=timezone.utc)
                return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        except Exception:
            pass

    # Fallback to current UTC receive time in ISO-8601 format
    now_dt = datetime.now(timezone.utc)
    return now_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
