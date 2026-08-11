# Arcon DNP3 Client

**Arcon DNP3 Client** is a standalone, open-source DNP3 Master diagnostic and monitoring desktop application built with Python 3.9+, PySide6, and the official open-source Step Function I/O OpenDNP3 C++ stack (`dnp3-python` v0.2.3b2).

It is designed to read, monitor, diagnose, and normalized data from remote DNP3 Outstations / RTUs, and can be packaged into a standalone executable (`ArconDNP3Client.exe`) for publishing on the **Arcon Marketplace**.

---

## 1. DNP3 Concepts & Terminology

### What is DNP3?
**DNP3 (Distributed Network Protocol 3)** is an IEEE 1815 standardized communications protocol widely used in electric utilities, water management, oil & gas, and industrial SCADA systems.

### What is a DNP3 Master?
The **DNP3 Master** is the client application that initiates communication, requests data, polls measurements, and receives events from remote RTUs or outstations. **Arcon DNP3 Client acts as the DNP3 Master.**

### What is a DNP3 Outstation?
A **DNP3 Outstation** (RTU, IED, or Smart Meter) is the remote field device that contains physical measurement sensors, digital status inputs, and control outputs.

### Where DNP3 is Used
- Electric Power Distribution & Substations
- Water Treatment & Pipeline SCADA
- Gas Distribution Networks
- Renewable Energy Integration (Solar/Wind Farms)

---

## 2. Architecture & Data Flow

```
                         ARCON MARKETPLACE
                                |
                                v
                       ARCON DNP3 CONNECTOR
                                |
                                v
                     ARCON DNP3 CLIENT TOOL
                                |
                                v
                     DNP3 OPEN-SOURCE STACK (dnp3-python / OpenDNP3)
                                |
                                | DNP3 over TCP/IP
                                | Default port 20000
                                v
                     DNP3 OUTSTATION / RTU
                                |
                                v
                   Sensors / Breakers / RTUs
```

### Internal Data Flow
```
DNP3 Outstation / RTU
        |
        | Measurements / Events over TCP/IP
        v
OpenDNP3 Stack (C++ / pybind11)
        |
        v
SOEHandler Callback (CustomSOEHandler)
        |
        v
Data Normalization ({protocol, type, index, value, quality, timestamp})
        |
        +----> Live Measurement Table
        |
        +----> Sequence of Events (SOE) Table
        |
        +----> Monitored Tag List
        |
        +----> Application Audit Log
```

---

## 3. Supported DNP3 Data Types

| Measurement Type | Description | Example |
| :--- | :--- | :--- |
| **Binary Input** | Digital status inputs (breakers, switches, alarms) | `BI[0] = TRUE (ONLINE)` |
| **Analog Input** | Floating point sensor readings (voltage, current, power) | `AI[0] = 230.5 V (ONLINE)` |
| **Counter** | Accumulator counters (energy kWh, pulse counts) | `Counter[0] = 1000 (ONLINE)` |
| **Frozen Counter** | Latched historical counter snapshots | `FrozenCounter[0] = 950 (ONLINE)` |
| **Binary Output Status**| Feedback status of digital control relays | `BOStatus[0] = FALSE` |
| **Analog Output Status**| Feedback status of analog setpoints | `AOStatus[0] = 100.0` |

---

## 4. Installation & Setup

### Prerequisites
- Python 3.9+ installed
- `cmake` (automatically handled via virtual environment)

### Installation Steps
```bash
# 1. Clone the repository
cd DNP3_connector

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 5. Running the Application

### Launching Desktop GUI
```bash
python app.py
```

### Launching with Pre-Configured Command Line Parameters
```bash
python app.py --ip 192.168.1.20 --port 20000 --master-address 1 --outstation-address 1024
```

### Running CLI Proof of Concept Deliverable
```bash
python app.py --poc
```

---

## 6. Running the Development DNP3 Outstation Simulator

The project includes a standalone DNP3 RTU simulator (`tools/run_outstation.py`) for offline testing:

```bash
# Run simulator on port 20000
python tools/run_outstation.py --port 20000 --master-address 1 --outstation-address 1024
```

The simulator periodically alters values (voltage AI[0] every 5s, breaker BI[0] every 10s, counter[0] every 3s) to test real-time monitoring and event reception.

---

## 7. Features & Operations

### Connection Panel
- **Remote IP**: IP address of the Outstation RTU (Default `127.0.0.1`).
- **Remote TCP Port**: Port number (Default `20000`).
- **Master Address**: DNP3 Link Layer Address for Master (Default `1`).
- **Outstation Address**: DNP3 Link Layer Address for Outstation (Default `1024`).

### Class Polling
- **Read All**: Triggers an Integrity Poll (Class 0, 1, 2, 3 scan).
- **Poll Now**: Polls selected classes (Class 0, Class 1, Class 2, Class 3).
- **Cyclic Interval**: Configurable polling timer (1000 ms, 2000 ms, 5000 ms, 10000 ms).

### Tag Monitor
- Allows adding custom tag names, DNP3 object types, point indexes, and descriptions.
- Supports `[Add Tag]`, `[Remove Tag]`, `[Start Monitoring]`, and `[Stop Monitoring]`.

### Control / Write Operations (Secondary Feature)
- Supports Binary Output (Group 10) and Analog Output (Group 40) commands.
- **Safety Guarantee**: Control commands are **NEVER executed automatically**.
- Displays mandatory warning modal confirmation dialog before execution.
- Generates detailed execution audit logs with timestamps and status.

---

## 8. Building Standalone Executable (Windows EXE)

To package the application as a standalone executable:

```bash
# Generate standalone executable using PyInstaller spec
pyinstaller arcon_dnp3_client.spec
```

The compiled executable `ArconDNP3Client.exe` (or macOS binary) will be generated inside the `dist/` directory.

---

## 9. Testing

Run the automated test suite with `pytest`:

```bash
PYTHONPATH=. pytest tests/
```

---

## 10. Third-Party Licenses

- **OpenDNP3 Stack (`dnp3-python`)**: Apache License 2.0
- **PySide6 (Qt for Python)**: LGPL v3
- See `THIRD_PARTY_LICENSES.md` for full license disclosures.
