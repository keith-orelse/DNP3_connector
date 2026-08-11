"""
Arcon DNP3 Client Wrapper Module.
Wraps OpenDNP3 Master stack, SOEHandler callbacks, and bridges events to UI / Measurement Store.
"""

import time
import logging
from typing import Callable, List, Optional
from pydnp3 import opendnp3, asiodnp3, openpal

from dnp3_python.dnp3station.master_new import MyMasterNew
from dnp3_python.dnp3station.station_utils import SOEHandler

from dnp3.models import (
    DNP3Measurement,
    parse_dnp3_quality,
    parse_dnp3_timestamp,
    TYPE_BINARY_INPUT,
    TYPE_ANALOG_INPUT,
    TYPE_COUNTER,
    TYPE_FROZEN_COUNTER,
    TYPE_BINARY_OUTPUT_STATUS,
    TYPE_ANALOG_OUTPUT_STATUS,
)
from dnp3.measurements import MeasurementStore
from dnp3.events import EventQueue, DNP3Event
from dnp3.connection import ConnectionManager, ConnectionState
from utils.logger import get_logger

_logger = get_logger()


class CustomChannelListener(asiodnp3.IChannelListener):
    """
    Channel state listener receiving real-time C++ ASIO channel state callbacks.
    """
    def __init__(self, callback: Callable[[ConnectionState, str], None]):
        super().__init__()
        self.callback = callback

    def OnStateChange(self, state):
        state_str = opendnp3.ChannelStateToString(state)
        _logger.info(f"DNP3 Channel State Changed: {state_str}")
        
        if state == opendnp3.ChannelState.OPEN:
            self.callback(ConnectionState.CONNECTED, "DNP3 TCP Channel Open")
        elif state == opendnp3.ChannelState.OPENING:
            self.callback(ConnectionState.CONNECTING, "TCP Channel Opening...")
        elif state in (opendnp3.ChannelState.CLOSED, opendnp3.ChannelState.SHUTDOWN):
            self.callback(ConnectionState.DISCONNECTED, f"Channel {state_str}")


class CustomSOEHandler(SOEHandler):
    """
    Custom Sequence of Events (SOE) Handler that intercepts OpenDNP3 callbacks
    and updates the MeasurementStore and EventQueue in real-time.
    Uses dnp3_python native Foreach visitor parsing to ensure zero C++ GIL crashes.
    """
    def __init__(self, measurement_store: MeasurementStore, event_queue: EventQueue, update_callback: Optional[Callable] = None):
        super().__init__()
        self.store = measurement_store
        self.event_queue = event_queue
        self.update_callback = update_callback

    def _notify(self, measurement: DNP3Measurement):
        self.store.update_measurement(measurement)
        
        event = DNP3Event(
            timestamp=measurement.timestamp if measurement.timestamp != "N/A" else time.strftime("%H:%M:%S"),
            type=measurement.type.replace("_", " ").title(),
            index=measurement.index,
            value=measurement.value,
            quality=measurement.quality
        )
        self.event_queue.add_event(event)

        if self.update_callback:
            try:
                self.update_callback(measurement, event)
            except Exception as e:
                _logger.debug(f"Error in update callback: {e}")

    def Process(self, info, values):
        """
        Overrides OpenDNP3 SOEHandler Process method safely using super().Process.
        """
        try:
            # Let SOEHandler's native C++ Foreach visitors parse values cleanly
            super().Process(info, values)

            group = info.gv.group
            if group == 30:
                type_name = TYPE_ANALOG_INPUT
            elif group == 1:
                type_name = TYPE_BINARY_INPUT
            elif group == 20:
                type_name = TYPE_COUNTER
            elif group == 21:
                type_name = TYPE_FROZEN_COUNTER
            elif group == 10:
                type_name = TYPE_BINARY_OUTPUT_STATUS
            elif group == 40:
                type_name = TYPE_ANALOG_OUTPUT_STATUS
            else:
                return

            ind_val_dict = self._gv_index_value_nested_dict.get(info.gv)
            if not ind_val_dict:
                return

            ts_now = time.strftime("%H:%M:%S")
            for index, raw_val in ind_val_dict.items():
                if raw_val is None:
                    continue
                
                if isinstance(raw_val, float):
                    val = round(raw_val, 4)
                else:
                    val = raw_val

                m = DNP3Measurement(
                    type=type_name,
                    index=index,
                    value=val,
                    quality="ONLINE",
                    timestamp=ts_now,
                    raw_flags=1
                )
                self._notify(m)
        except Exception as e:
            _logger.error(f"Error in CustomSOEHandler.Process: {e}")


class ArconDNP3Client:
    """
    Main DNP3 Master Client Manager.
    Coordinates connection, polling, measurements, events, and control execution.
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

        self.store = MeasurementStore()
        self.events = EventQueue()
        self.connection = ConnectionManager()
        self.soe_handler = CustomSOEHandler(self.store, self.events, update_callback)
        self.channel_listener = CustomChannelListener(self._on_channel_state_change)
        self.master_app: Optional[MyMasterNew] = None

    def _on_channel_state_change(self, state: ConnectionState, message: str):
        self.connection.set_state(state, message)

    @property
    def is_connected(self) -> bool:
        if self.master_app:
            return self.master_app.is_connected
        return False

    def connect(self) -> bool:
        """Establishes DNP3 TCP connection and Master association."""
        if self.is_connected:
            _logger.info("Already connected to DNP3 Outstation.")
            return True

        self.connection.set_state(ConnectionState.CONNECTING)
        _logger.info(
            f"Connecting DNP3 Master (Addr={self.master_address}) to Outstation "
            f"at {self.remote_ip}:{self.remote_port} (Addr={self.outstation_address})..."
        )

        try:
            self.master_app = MyMasterNew(
                master_ip=self.local_ip,
                outstation_ip=self.remote_ip,
                port=self.remote_port,
                master_id=self.master_address,
                outstation_id=self.outstation_address,
                soe_handler=self.soe_handler,
                listener=self.channel_listener
            )
            self.master_app.start()
            return True
        except Exception as e:
            err = f"Unable to connect to DNP3 outstation at {self.remote_ip}:{self.remote_port}. Error: {e}"
            self.connection.set_state(ConnectionState.DISCONNECTED, err)
            _logger.error(err)
            return False

    def disconnect(self):
        """Cleanly shuts down DNP3 Master and closes TCP channel."""
        if self.master_app:
            _logger.info("Disconnecting DNP3 Master...")
            try:
                self.master_app.shutdown()
            except Exception as e:
                _logger.debug(f"Shutdown error: {e}")
            self.master_app = None

        self.connection.set_state(ConnectionState.DISCONNECTED)
        _logger.info("DNP3 Master disconnected cleanly.")

    def poll_all(self) -> bool:
        """Triggers a Scan All (Class 0, 1, 2, 3) request."""
        if not self.master_app:
            return False
        try:
            self.master_app.send_scan_all_request()
            _logger.info("Issued Class 0 scan request.")
            return True
        except Exception as e:
            _logger.error(f"Poll request failed: {e}")
            return False
