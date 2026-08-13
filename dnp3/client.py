"""
Arcon DNP3 Client Wrapper Module.
Uses DNP3ProcessManager to execute OpenDNP3 in an isolated worker process.
Guarantees 100% thread safety and zero GIL deadlocks with PySide6.
"""

import time
from typing import Callable, Optional
from dnp3.worker import DNP3ProcessManager
from dnp3.models import DNP3Measurement
from dnp3.events import EventQueue, DNP3Event
from dnp3.measurements import MeasurementStore
from dnp3.connection import ConnectionManager, ConnectionState
from utils.logger import get_logger

_logger = get_logger()


class ArconDNP3Client:
    """
    Main DNP3 Master Client Manager.
    Delegates OpenDNP3 stack execution to an isolated background process via DNP3ProcessManager.
    """

    def __init__(
        self,
        remote_ip: str = "127.0.0.1",
        remote_port: int = 20000,
        master_address: int = 1,
        outstation_address: int = 1024,
        local_ip: str = "0.0.0.0",
        update_callback: Optional[Callable] = None
    ):
        self.remote_ip = remote_ip
        self.remote_port = remote_port
        self.master_address = master_address
        self.outstation_address = outstation_address
        self.local_ip = local_ip
        self.update_callback = update_callback

        self.store = MeasurementStore()
        self.events = EventQueue()
        self.connection = ConnectionManager()
        self.proc_mgr = DNP3ProcessManager()

    @property
    def is_connected(self) -> bool:
        return self.proc_mgr.is_running

    def connect(self) -> bool:
        """Launches isolated DNP3 worker process."""
        if self.is_connected:
            _logger.info("Already connected to DNP3 Outstation.")
            return True

        self.connection.set_state(ConnectionState.CONNECTING)
        _logger.info(
            f"Connecting DNP3 Master (Addr={self.master_address}) to Outstation "
            f"at {self.remote_ip}:{self.remote_port} (Addr={self.outstation_address})..."
        )

        config = {
            "remote_ip": self.remote_ip,
            "remote_port": self.remote_port,
            "master_address": self.master_address,
            "outstation_address": self.outstation_address,
            "local_ip": self.local_ip,
        }
        self.proc_mgr.start(config)
        return True

    def disconnect(self):
        """Cleanly stops DNP3 worker process."""
        if self.proc_mgr:
            self.proc_mgr.stop()
        self.connection.set_state(ConnectionState.DISCONNECTED)
        _logger.info("DNP3 Master disconnected cleanly.")

    def poll_all(self) -> bool:
        """Sends Poll All command to worker process."""
        if not self.is_connected:
            return False
        self.proc_mgr.send_cmd({"cmd": "POLL_ALL"})
        _logger.info("Issued Class 0 scan request.")
        return True

    def sync_events_from_worker(self):
        """
        Polls event_queue from worker process and dispatches updates to MeasurementStore & UI.
        """
        if not self.proc_mgr:
            return

        events = self.proc_mgr.get_events()
        for evt in events:
            etype = evt.get("type")
            if etype == "STATUS":
                state_str = evt.get("state")
                msg = evt.get("msg", "")
                if state_str == "CONNECTED":
                    self.connection.set_state(ConnectionState.CONNECTED, msg)
                elif state_str == "DISCONNECTED":
                    self.connection.set_state(ConnectionState.DISCONNECTED, msg)
                elif state_str == "CONNECTING":
                    self.connection.set_state(ConnectionState.CONNECTING, msg)
            elif etype == "LOG":
                _logger.info(evt.get("msg", ""))
            elif etype == "MEASUREMENT":
                m = DNP3Measurement(
                    type=evt.get("data_type"),
                    index=evt.get("index"),
                    value=evt.get("value"),
                    quality=evt.get("quality", "ONLINE"),
                    timestamp=evt.get("timestamp", time.strftime("%H:%M:%S")),
                    raw_flags=1
                )
                self.store.update_measurement(m)

                dnp3_evt = DNP3Event(
                    timestamp=m.timestamp,
                    type=m.type.replace("_", " ").title(),
                    index=m.index,
                    value=m.value,
                    quality=m.quality
                )
                self.events.add_event(dnp3_evt)

                if self.update_callback:
                    try:
                        self.update_callback(m, dnp3_evt)
                    except Exception as e:
                        _logger.debug(f"Error in update callback: {e}")
