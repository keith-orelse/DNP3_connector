"""
Automated PySide6 GUI test suite for Arcon DNP3 Client.
Verifies all tabs, widgets, table populators, and connection state transitions.
"""

import sys
import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from dnp3.models import DNP3Measurement, TYPE_ANALOG_INPUT, TYPE_BINARY_INPUT
from dnp3.events import DNP3Event
from dnp3.connection import ConnectionState


@pytest.fixture(scope="module")
def app():
    app_inst = QApplication.instance()
    if not app_inst:
        app_inst = QApplication(sys.argv)
    yield app_inst


def test_main_window_structure(app):
    win = MainWindow()
    assert win.windowTitle() == "Arcon DNP3 Client - Diagnostic & Monitoring Tool"
    assert win.tabs.count() == 5
    assert "Measurements" in win.tabs.tabText(0)
    assert "Events" in win.tabs.tabText(1)
    assert "Tag Monitor" in win.tabs.tabText(2)
    assert "Control Operations" in win.tabs.tabText(3)
    assert "Logs" in win.tabs.tabText(4)
    win.close()


def test_gui_measurement_and_event_signals(app):
    win = MainWindow()
    
    m = DNP3Measurement(
        type=TYPE_ANALOG_INPUT,
        index=0,
        value=230.5,
        quality="ONLINE",
        timestamp="14:30:00"
    )
    e = DNP3Event("14:30:00", "Analog Input", 0, 230.5, "ONLINE")

    # Emit signal to test thread-safe UI update
    win.handle_measurement_update(m, e)

    # Verify measurement table updated
    assert win.measurement_table.table.rowCount() == 1
    assert win.measurement_table.table.item(0, 0).text() == "Analog Input"
    assert win.measurement_table.table.item(0, 2).text() == "230.5"

    # Verify event table updated
    assert win.event_table.table.rowCount() == 1
    assert win.event_table.table.item(0, 3).text() == "230.5"

    # Verify tag monitor updated
    assert win.tag_monitor.table.item(0, 3).text() == "230.5"
    win.close()


def test_connection_state_ui_update(app):
    win = MainWindow()
    win.on_connection_state_changed(ConnectionState.CONNECTED, "Test connected")
    assert win.conn_panel.lbl_status.text() == "Connected"
    assert win.conn_panel.btn_connect.isEnabled() is False
    assert win.conn_panel.btn_disconnect.isEnabled() is True

    win.on_connection_state_changed(ConnectionState.DISCONNECTED, "Test disconnected")
    assert win.conn_panel.lbl_status.text() == "Disconnected"
    assert win.conn_panel.btn_connect.isEnabled() is True
    assert win.conn_panel.btn_disconnect.isEnabled() is False
    win.close()
