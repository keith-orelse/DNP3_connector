"""
Integration test for Arcon DNP3 Client using simulator outstation.
"""

import time
import pytest
from dnp3_python.dnp3station.outstation_new import MyOutStationNew
from pydnp3 import opendnp3
from dnp3.client import ArconDNP3Client


def test_dnp3_client_integration():
    test_port = 20045

    # Start outstation
    outstation = MyOutStationNew(outstation_ip="0.0.0.0", port=test_port, master_id=1, outstation_id=1024)
    outstation.start()

    # Pre-populate measurements
    outstation.apply_update(opendnp3.Analog(value=230.2, flags=opendnp3.Flags(opendnp3.AnalogQuality.ONLINE)), 0)
    outstation.apply_update(opendnp3.Binary(value=True, flags=opendnp3.Flags(opendnp3.BinaryQuality.ONLINE)), 0)
    outstation.apply_update(opendnp3.Counter(value=500, flags=opendnp3.Flags(opendnp3.CounterQuality.ONLINE)), 0)

    # Initialize client
    client = ArconDNP3Client(
        remote_ip="127.0.0.1",
        remote_port=test_port,
        master_address=1,
        outstation_address=1024
    )

    connected = client.connect()
    assert connected is True

    time.sleep(1.0)
    client.poll_all()
    time.sleep(1.5)

    client.disconnect()
    outstation.shutdown()
