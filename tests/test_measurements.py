"""
Unit tests for MeasurementStore and EventQueue.
"""

import pytest
from dnp3.models import DNP3Measurement, TYPE_ANALOG_INPUT, TYPE_BINARY_INPUT
from dnp3.measurements import MeasurementStore
from dnp3.events import EventQueue, DNP3Event


def test_measurement_store():
    store = MeasurementStore()

    m1 = DNP3Measurement(type=TYPE_ANALOG_INPUT, index=0, value=230.5)
    m2 = DNP3Measurement(type=TYPE_BINARY_INPUT, index=0, value=True)

    store.update_measurement(m1)
    store.update_measurement(m2)

    retrieved_m1 = store.get_measurement(TYPE_ANALOG_INPUT, 0)
    assert retrieved_m1.value == 230.5

    all_ms = store.get_all()
    assert len(all_ms) == 2

    analog_ms = store.get_by_type(TYPE_ANALOG_INPUT)
    assert len(analog_ms) == 1
    assert analog_ms[0].index == 0

    store.clear()
    assert len(store.get_all()) == 0


def test_event_queue():
    queue = EventQueue(max_size=3)

    e1 = DNP3Event("10:00:00", "Analog Input", 0, 230.5, "ONLINE")
    e2 = DNP3Event("10:00:01", "Binary Input", 0, True, "ONLINE")
    e3 = DNP3Event("10:00:02", "Counter", 0, 100, "ONLINE")
    e4 = DNP3Event("10:00:03", "Analog Input", 1, 10.2, "ONLINE")

    queue.add_event(e1)
    queue.add_event(e2)
    queue.add_event(e3)
    assert len(queue.get_events()) == 3

    queue.add_event(e4)
    events = queue.get_events()
    assert len(events) == 3
    assert events[0].value == 10.2  # Most recent first
    assert events[-1].value == True # Oldest e1 dropped due to max_size=3
