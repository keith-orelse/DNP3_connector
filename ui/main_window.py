"""
Main Window Dashboard for Arcon DNP3 Client.
Combines panels, live tables, tabs, and non-blocking background polling timers.
Fully thread-safe Qt Signal architecture for zero GUI freezes.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QStatusBar, QMessageBox, QApplication
)
from PySide6.QtCore import QTimer, Signal, Slot, Qt

from ui.connection_panel import ConnectionPanel
from ui.polling_panel import PollingPanel
from ui.measurement_table import MeasurementTable
from ui.event_table import EventTable
from ui.tag_monitor import TagMonitor
from ui.control_panel import ControlPanel
from ui.log_panel import LogPanel

from dnp3.client import ArconDNP3Client
from dnp3.models import DNP3Measurement
from dnp3.events import DNP3Event
from dnp3.connection import ConnectionState
from utils.logger import get_logger

_logger = get_logger()


class MainWindow(QMainWindow):
    """
    Main PySide6 Application Window for Arcon DNP3 Client.
    Thread-safe UI using Qt Signals for cross-thread DNP3 Master callbacks.
    """
    # Signal emitted when a new measurement or event arrives from background DNP3 thread
    measurement_signal = Signal(object, object)  # (DNP3Measurement, DNP3Event)
    connection_signal = Signal(object, str)       # (ConnectionState, message)

    def __init__(self, cli_args=None):
        super().__init__()
        self.setWindowTitle("Arcon DNP3 Client - Diagnostic & Monitoring Tool")
        self.resize(1100, 750)

        self.cli_args = cli_args
        self.dnp3_client = ArconDNP3Client(update_callback=self.on_dnp3_update)
        self.dnp3_client.connection.add_listener(self.on_connection_state_changed)

        # Connection health monitor timer
        self.conn_check_timer = QTimer(self)
        self.conn_check_timer.setInterval(500)
        self.conn_check_timer.timeout.connect(self.check_connection_health)

        # Cyclic polling timer
        self.polling_timer = QTimer(self)
        self.polling_timer.setInterval(1000)
        self.polling_timer.timeout.connect(self.on_polling_timer_tick)

        self.init_ui()
        self.apply_theme()
        self.process_cli_args()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # 1. Connection Panel
        self.conn_panel = ConnectionPanel()
        self.conn_panel.connect_requested.connect(self.on_connect_requested)
        self.conn_panel.disconnect_requested.connect(self.on_disconnect_requested)
        main_layout.addWidget(self.conn_panel)

        # 2. Polling Panel
        self.poll_panel = PollingPanel()
        self.poll_panel.read_all_requested.connect(self.on_read_all_requested)
        self.poll_panel.poll_selected_requested.connect(self.on_poll_selected_requested)
        self.poll_panel.interval_changed.connect(self.on_polling_interval_changed)
        self.poll_panel.auto_polling_toggled.connect(self.on_auto_polling_toggled)
        main_layout.addWidget(self.poll_panel)

        # 3. Tabbed View
        self.tabs = QTabWidget()

        self.measurement_table = MeasurementTable()
        self.event_table = EventTable()
        self.tag_monitor = TagMonitor()
        self.control_panel = ControlPanel()
        self.control_panel.set_client(self.dnp3_client)
        self.log_panel = LogPanel()

        self.tabs.addTab(self.measurement_table, "📊 Measurements")
        self.tabs.addTab(self.event_table, "⚡ Events")
        self.tabs.addTab(self.tag_monitor, "🏷️ Tag Monitor")
        self.tabs.addTab(self.control_panel, "🎛️ Control Operations")
        self.tabs.addTab(self.log_panel, "📝 Logs")

        main_layout.addWidget(self.tabs, stretch=1)
        self.setCentralWidget(central_widget)

        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Configure DNP3 Outstation parameters and click Connect.")

        # Thread-safe Qt signal connections
        self.measurement_signal.connect(self.handle_measurement_update)
        self.connection_signal.connect(self.handle_connection_state_changed)

    def apply_theme(self):
        """Applies a modern sleek dark theme."""
        dark_stylesheet = """
        QMainWindow {
            background-color: #1e1e24;
            color: #e0e0e0;
        }
        QWidget {
            background-color: #1e1e24;
            color: #e0e0e0;
            font-family: 'Segoe UI', Roboto, sans-serif;
            font-size: 12px;
        }
        QGroupBox {
            border: 1px solid #333340;
            border-radius: 6px;
            margin-top: 10px;
            font-weight: bold;
            color: #64b5f6;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 6px;
        }
        QLineEdit, QComboBox, QSpinBox {
            background-color: #2b2b36;
            border: 1px solid #3d3d4e;
            border-radius: 4px;
            padding: 5px;
            color: #ffffff;
        }
        QLineEdit:focus, QComboBox:focus {
            border: 1px solid #29b6f6;
        }
        QPushButton {
            background-color: #2b2b36;
            border: 1px solid #3d3d4e;
            border-radius: 4px;
            color: #ffffff;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #3d3d4e;
        }
        QPushButton:pressed {
            background-color: #1565c0;
        }
        QTabWidget::pane {
            border: 1px solid #333340;
            background-color: #1e1e24;
        }
        QTabBar::tab {
            background-color: #2b2b36;
            color: #b0bec5;
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #1565c0;
            color: #ffffff;
            font-weight: bold;
        }
        QTableWidget {
            background-color: #18181f;
            gridline-color: #2b2b36;
            border: none;
        }
        QHeaderView::section {
            background-color: #23232e;
            color: #90caf9;
            padding: 5px;
            border: 1px solid #2b2b36;
            font-weight: bold;
        }
        QStatusBar {
            background-color: #18181f;
            color: #aaaaaa;
        }
        """
        self.setStyleSheet(dark_stylesheet)

    def process_cli_args(self):
        """Pre-populates fields if command line arguments were passed."""
        if not self.cli_args:
            return

        if hasattr(self.cli_args, 'ip') and self.cli_args.ip:
            self.conn_panel.input_remote_ip.setText(self.cli_args.ip)
        if hasattr(self.cli_args, 'port') and self.cli_args.port:
            self.conn_panel.input_remote_port.setText(str(self.cli_args.port))
        if hasattr(self.cli_args, 'master_address') and self.cli_args.master_address:
            self.conn_panel.input_master_addr.setText(str(self.cli_args.master_address))
        if hasattr(self.cli_args, 'outstation_address') and self.cli_args.outstation_address:
            self.conn_panel.input_outstation_addr.setText(str(self.cli_args.outstation_address))

    def on_connect_requested(self, remote_ip, remote_port, master_addr, outstation_addr, local_ip):
        self.dnp3_client.remote_ip = remote_ip
        self.dnp3_client.remote_port = remote_port
        self.dnp3_client.master_address = master_addr
        self.dnp3_client.outstation_address = outstation_addr
        self.dnp3_client.local_ip = local_ip

        self.conn_panel.update_connection_state(ConnectionState.CONNECTING)
        success = self.dnp3_client.connect()
        if success:
            self.conn_check_timer.start()
            if self.poll_panel.chk_auto_poll.isChecked():
                self.polling_timer.start()

    def check_connection_health(self):
        if self.dnp3_client.is_connected:
            self.conn_panel.update_connection_state(ConnectionState.CONNECTED)

    def on_disconnect_requested(self):
        self.conn_check_timer.stop()
        self.polling_timer.stop()
        self.dnp3_client.disconnect()

    def on_read_all_requested(self):
        if not self.dnp3_client.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to a DNP3 outstation first.")
            return
        self.dnp3_client.poll_all()

    def on_poll_selected_requested(self, c0, c1, c2, c3):
        if not self.dnp3_client.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to a DNP3 outstation first.")
            return
        self.dnp3_client.poll_all()

    def on_polling_interval_changed(self, interval_ms: int):
        self.polling_timer.setInterval(interval_ms)
        _logger.info(f"Updated cyclic polling interval to {interval_ms} ms.")

    def on_auto_polling_toggled(self, enabled: bool):
        if enabled and self.dnp3_client.is_connected:
            self.polling_timer.start()
        else:
            self.polling_timer.stop()

    def on_polling_timer_tick(self):
        if self.dnp3_client.is_connected:
            self.dnp3_client.poll_all()

    def on_dnp3_update(self, measurement: DNP3Measurement, event: DNP3Event):
        """Thread-safe callback from OpenDNP3 C++ background thread via Qt Signal."""
        self.measurement_signal.emit(measurement, event)

    @Slot(object, object)
    def handle_measurement_update(self, measurement: DNP3Measurement, event: DNP3Event):
        """Slot handling measurement updates safely on the main GUI thread."""
        self.measurement_table.update_single_measurement(measurement)
        self.event_table.add_event(event)
        self.tag_monitor.update_tag_value(measurement)

    def on_connection_state_changed(self, state: ConnectionState, message: str):
        """Callback from background thread - emits Qt signal for main thread safety."""
        self.connection_signal.emit(state, message)

    @Slot(object, str)
    def handle_connection_state_changed(self, state: ConnectionState, message: str):
        """Slot executed safely on the Qt main GUI thread."""
        self.conn_panel.update_connection_state(state, message)
        self.status_bar.showMessage(f"DNP3 Master Status: {state.value} {message}")
        if state == ConnectionState.CONNECTED:
            QTimer.singleShot(200, self.dnp3_client.poll_all)

    def closeEvent(self, event):
        self.conn_check_timer.stop()
        self.polling_timer.stop()
        if self.dnp3_client:
            self.dnp3_client.disconnect()
        super().closeEvent(event)
