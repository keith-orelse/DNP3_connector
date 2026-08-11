"""
In-memory measurements database for Arcon DNP3 Client.
Thread-safe store mapping (data_type, index) to normalized DNP3Measurement objects.
"""

from threading import Lock
from typing import Dict, List, Optional, Tuple
from dnp3.models import (
    DNP3Measurement,
    TYPE_BINARY_INPUT,
    TYPE_ANALOG_INPUT,
    TYPE_COUNTER,
    TYPE_FROZEN_COUNTER,
    TYPE_BINARY_OUTPUT_STATUS,
    TYPE_ANALOG_OUTPUT_STATUS,
)


class MeasurementStore:
    """Thread-safe store of all active DNP3 point measurements."""
    
    def __init__(self):
        self._lock = Lock()
        # Key: (data_type, index) -> DNP3Measurement
        self._measurements: Dict[Tuple[str, int], DNP3Measurement] = {}

    def update_measurement(self, measurement: DNP3Measurement):
        """Updates or adds a measurement to the store."""
        with self._lock:
            key = (measurement.type, measurement.index)
            self._measurements[key] = measurement

    def get_measurement(self, data_type: str, index: int) -> Optional[DNP3Measurement]:
        """Retrieves a specific measurement."""
        with self._lock:
            return self._measurements.get((data_type, index))

    def get_all(self) -> List[DNP3Measurement]:
        """Returns a list of all current measurements sorted by type and index."""
        with self._lock:
            sorted_keys = sorted(self._measurements.keys(), key=lambda k: (k[0], k[1]))
            return [self._measurements[k] for k in sorted_keys]

    def get_by_type(self, data_type: str) -> List[DNP3Measurement]:
        """Returns measurements of a specific type."""
        with self._lock:
            keys = [k for k in self._measurements.keys() if k[0] == data_type]
            sorted_keys = sorted(keys, key=lambda k: k[1])
            return [self._measurements[k] for k in sorted_keys]

    def clear(self):
        """Clears all stored measurements."""
        with self._lock:
            self._measurements.clear()
