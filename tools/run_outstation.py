#!/usr/bin/env python3
"""
===================================================================
ARCON DNP3 CLIENT - DEVELOPMENT OUTSTATION SIMULATOR
===================================================================
MARKING: DEVELOPMENT / TEST ONLY

This script simulates a DNP3 Outstation / RTU for testing the Arcon DNP3 Client.
Exposes Binary Inputs, Analog Inputs, Counters, and Output Status points.
Periodically alters measurement values to test polling, events, quality, and tag monitoring.
"""

import sys
import os
import time
import random
import argparse
import signal
from pydnp3 import opendnp3

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dnp3_python.dnp3station.outstation_new import MyOutStationNew
from utils.logger import get_logger

_logger = get_logger()

running = True


def signal_handler(sig, frame):
    global running
    print("\n[SIMULATOR] Stopping DNP3 Outstation simulator...")
    running = False


def run_simulator(ip: str = "0.0.0.0", port: int = 20000, master_id: int = 1, outstation_id: int = 1024):
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("===================================================================")
    print("        ARCON DNP3 OUTSTATION SIMULATOR (DEVELOPMENT ONLY)")
    print("===================================================================")
    print(f" Listening Address   : {ip}:{port}")
    print(f" DNP3 Master Address : {master_id}")
    print(f" DNP3 Outstation Addr: {outstation_id}")
    print(" Press Ctrl+C to stop.")
    print("===================================================================")

    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((ip, port))
        sock.close()
    except Exception as e:
        print(f"[ERROR] Port {port} is already in use or unavailable: {e}")
        print("Please stop any running process using this port and try again.")
        sys.exit(1)

    _logger.info(f"Initializing DNP3 Outstation simulator on {ip}:{port}...")

    # Initialize Outstation (Note: master_id and outstation_id must match master config)
    outstation = MyOutStationNew(
        outstation_ip=ip,
        port=port,
        master_id=master_id,
        outstation_id=outstation_id
    )
    outstation.start()
    _logger.info("DNP3 Outstation server started successfully.")

    # Initialize sample values per Section 20 requirements
    # Binary Inputs
    outstation.apply_update(opendnp3.Binary(value=True, flags=opendnp3.Flags(opendnp3.BinaryQuality.ONLINE)), 0)   # BI[0] Breaker Status
    outstation.apply_update(opendnp3.Binary(value=False, flags=opendnp3.Flags(opendnp3.BinaryQuality.ONLINE)), 1)  # BI[1] Alarm Status
    outstation.apply_update(opendnp3.Binary(value=True, flags=opendnp3.Flags(opendnp3.BinaryQuality.ONLINE)), 2)   # BI[2] Isolator Status

    # Analog Inputs
    outstation.apply_update(opendnp3.Analog(value=230.5, flags=opendnp3.Flags(opendnp3.AnalogQuality.ONLINE)), 0)  # AI[0] Bus Voltage (V)
    outstation.apply_update(opendnp3.Analog(value=10.2, flags=opendnp3.Flags(opendnp3.AnalogQuality.ONLINE)), 1)   # AI[1] Line Current (A)
    outstation.apply_update(opendnp3.Analog(value=52.7, flags=opendnp3.Flags(opendnp3.AnalogQuality.ONLINE)), 2)   # AI[2] Active Power (kW)

    # Counters
    outstation.apply_update(opendnp3.Counter(value=1000, flags=opendnp3.Flags(opendnp3.CounterQuality.ONLINE)), 0)  # Counter[0] Energy (kWh)

    # Binary & Analog Output Status
    outstation.apply_update(opendnp3.BinaryOutputStatus(value=False, flags=opendnp3.Flags(opendnp3.BinaryOutputStatusQuality.ONLINE)), 0)
    outstation.apply_update(opendnp3.AnalogOutputStatus(value=100.0, flags=opendnp3.Flags(opendnp3.AnalogOutputStatusQuality.ONLINE)), 0)

    _logger.info("Configured initial points (BI[0..2], AI[0..2], Counter[0], BO[0], AO[0]).")

    tick = 0
    voltage_base = 230.5
    counter_val = 1000
    bi0_val = True

    try:
        while running:
            time.sleep(1.0)
            tick += 1

            # AI[0] changes every 5 seconds (jitter between 225.0V and 235.0V)
            if tick % 5 == 0:
                voltage_val = round(voltage_base + random.uniform(-4.5, 4.5), 2)
                current_val = round(10.2 + random.uniform(-1.0, 1.5), 2)
                power_val = round(voltage_val * current_val / 1000.0, 2)
                
                outstation.apply_update(opendnp3.Analog(value=voltage_val, flags=opendnp3.Flags(opendnp3.AnalogQuality.ONLINE)), 0)
                outstation.apply_update(opendnp3.Analog(value=current_val, flags=opendnp3.Flags(opendnp3.AnalogQuality.ONLINE)), 1)
                outstation.apply_update(opendnp3.Analog(value=power_val, flags=opendnp3.Flags(opendnp3.AnalogQuality.ONLINE)), 2)
                print(f"[SIMULATOR EVENT] AI[0] updated to {voltage_val} V | AI[1] = {current_val} A")

            # BI[0] toggles every 10 seconds
            if tick % 10 == 0:
                bi0_val = not bi0_val
                outstation.apply_update(opendnp3.Binary(value=bi0_val, flags=opendnp3.Flags(opendnp3.BinaryQuality.ONLINE)), 0)
                print(f"[SIMULATOR EVENT] BI[0] toggled to {bi0_val}")

            # Counter[0] increments every 3 seconds
            if tick % 3 == 0:
                counter_val += random.randint(1, 5)
                outstation.apply_update(opendnp3.Counter(value=counter_val, flags=opendnp3.Flags(opendnp3.CounterQuality.ONLINE)), 0)
                print(f"[SIMULATOR EVENT] Counter[0] incremented to {counter_val}")

    except KeyboardInterrupt:
        pass
    finally:
        print("[SIMULATOR] Shutting down outstation...")
        outstation.shutdown()
        print("[SIMULATOR] Outstation stopped cleanly.")


def main():
    parser = argparse.ArgumentParser(
        description="Development DNP3 Outstation Simulator (TEST ONLY)"
    )
    parser.add_argument("--ip", default="0.0.0.0", help="Outstation listening IP (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=20000, help="Outstation listening port (default: 20000)")
    parser.add_argument("--master-address", type=int, default=1, help="Expected DNP3 Master Address (default: 1)")
    parser.add_argument("--outstation-address", type=int, default=1024, help="DNP3 Outstation Address (default: 1024)")

    args = parser.parse_args()
    run_simulator(args.ip, args.port, args.master_address, args.outstation_address)


if __name__ == "__main__":
    main()
