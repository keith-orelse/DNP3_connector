"""
Event handling and normalisation module for DNP3 Master.
Captures real-time value changes and event notifications from OpenDNP3 SOEHandler.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from dnp3.models import DNP3Measurement


@dataclass
class DNP3Event:
    """
    Represents an incoming DNP3 event notification.
    """
    timestamp: str
    type: str
    index: int
    value: Any
    quality: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EventQueue:
    """
    Thread-safe event storage buffer for displaying incoming DNP3 events.
    """
    def __init__(self, max_size: int = 500):
        self.max_size = max_size
        self._events: List[DNP3Event] = []

    def add_event(self, event: DNP3Event):
        self._events.insert(0, event)
        if len(self._events) > self.max_size:
            self._events.pop()

    def get_events(self) -> List[DNP3Event]:
        return list(self._events)

    def clear(self):
        self._events.clear()
