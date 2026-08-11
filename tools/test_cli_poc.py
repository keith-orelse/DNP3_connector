"""
CLI Proof of Concept for Arcon DNP3 Client (Phase 1 First Deliverable).
"""

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dnp3.client import ArconDNP3Client
from dnp3.models import TYPE_ANALOG_INPUT, TYPE_BINARY_INPUT, TYPE_COUNTER

def run_poc():
    print("===================================================================")
    print("        ARCON DNP3 CLIENT - CLI PROOF OF CONCEPT")
    print("===================================================================")

    client = ArconDNP3Client(
        remote_ip="127.0.0.1",
        remote_port=20000,
        master_address=1,
        outstation_address=1024
    )

    print("DNP3 Master Starting...")
    print(f"Connecting to: {client.remote_ip}:{client.remote_port}")
    print(f"Master Address: {client.master_address}")
    print(f"Outstation Address: {client.outstation_address}\n")

    connected = client.connect()
    if not connected:
        print("[ERROR] Connection failed!")
        return

    print("Association established.")
    time.sleep(1.5)

    print("\nIssuing Class 0 Scan All request...")
    client.poll_all()
    time.sleep(2.0)

    print("\n------------------ MEASUREMENTS ------------------")
    measurements = client.store.get_all()
    for m in measurements:
        print(f"[{m.type.upper()}] Index {m.index}: Value = {m.value} | Quality = {m.quality} | Timestamp = {m.timestamp}")

    print("\n------------------ EVENTS ------------------")
    print("Waiting 6 seconds for simulator events...")
    time.sleep(6.0)

    events = client.events.get_events()
    for ev in events:
        print(f"Event received @ {ev.timestamp}: {ev.type} [{ev.index}] changed to {ev.value} (Quality: {ev.quality})")

    client.disconnect()
    print("\n[SUCCESS] CLI Proof of Concept completed successfully!")

if __name__ == "__main__":
    run_poc()
