"""
Connection Configuration Panel for Arcon DNP3 Client.
"""

from PySide6.QtWidgets import (
    QWidget, QGroupBox, QGridLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from utils.validation import validate_ip_address, validate_port, validate_dnp3_address
from dnp3.connection import ConnectionState


class ConnectionPanel(QGroupBox):
    """
    GUI Panel for configuring DNP3 TCP connection parameters and address settings.
    """
    connect_requested = Signal(str, int, int, int, str)  # (remote_ip, remote_port, master_addr, outstation_addr, local_ip)
    disconnect_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("DNP3 Network Connection & Addressing", parent)
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()
        layout.setSpacing(10)

        # Remote IP
        layout.addWidget(QLabel("Remote IP Address:"), 0, 0)
        self.input_remote_ip = QLineEdit("127.0.0.1")
        self.input_remote_ip.setPlaceholderText("192.168.1.20")
        layout.addWidget(self.input_remote_ip, 0, 1)

        # Remote Port
        layout.addWidget(QLabel("Remote TCP Port:"), 0, 2)
        self.input_remote_port = QLineEdit("20000")
        layout.addWidget(self.input_remote_port, 0, 3)

        # Master Address
        layout.addWidget(QLabel("Master Address:"), 1, 0)
        self.input_master_addr = QLineEdit("1")
        layout.addWidget(self.input_master_addr, 1, 1)

        # Outstation Address
        layout.addWidget(QLabel("Outstation Address:"), 1, 2)
        self.input_outstation_addr = QLineEdit("1024")
        layout.addWidget(self.input_outstation_addr, 1, 3)

        # Local IP (Optional)
        layout.addWidget(QLabel("Local IP (Optional):"), 2, 0)
        self.input_local_ip = QLineEdit("0.0.0.0")
        layout.addWidget(self.input_local_ip, 2, 1)

        # Protocol Type
        layout.addWidget(QLabel("Protocol / Transport:"), 2, 2)
        self.combo_transport = QComboBox()
        self.combo_transport.addItems(["TCP/IP (Default)", "UDP/IP (Reserved)"])
        layout.addWidget(self.combo_transport, 2, 3)

        # Buttons & Status Bar
        btn_box = QHBoxLayout()
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setStyleSheet("background-color: #2b7fff; color: white; font-weight: bold; padding: 6px 16px;")
        self.btn_connect.clicked.connect(self.on_connect_clicked)

        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.setStyleSheet("padding: 6px 16px;")
        self.btn_disconnect.clicked.connect(self.on_disconnect_clicked)

        btn_box.addWidget(self.btn_connect)
        btn_box.addWidget(self.btn_disconnect)

        btn_box.addSpacing(20)
        btn_box.addWidget(QLabel("Status:"))

        self.lbl_status = QLabel("Disconnected")
        self.lbl_status.setStyleSheet("font-weight: bold; color: #888888; font-size: 13px;")
        btn_box.addWidget(self.lbl_status)
        btn_box.addStretch()

        layout.addLayout(btn_box, 3, 0, 1, 4)
        self.setLayout(layout)

    def on_connect_clicked(self):
        remote_ip = self.input_remote_ip.text().strip()
        port_str = self.input_remote_port.text().strip()
        master_str = self.input_master_addr.text().strip()
        outstation_str = self.input_outstation_addr.text().strip()
        local_ip = self.input_local_ip.text().strip() or "0.0.0.0"

        # Validations
        ok, err = validate_ip_address(remote_ip)
        if not ok:
            QMessageBox.critical(self, "Invalid Configuration", err)
            return

        ok, err = validate_port(port_str)
        if not ok:
            QMessageBox.critical(self, "Invalid Configuration", err)
            return

        ok, err = validate_dnp3_address(master_str, "Master Address")
        if not ok:
            QMessageBox.critical(self, "Invalid Configuration", err)
            return

        ok, err = validate_dnp3_address(outstation_str, "Outstation Address")
        if not ok:
            QMessageBox.critical(self, "Invalid Configuration", err)
            return

        self.connect_requested.emit(
            remote_ip, int(port_str), int(master_str), int(outstation_str), local_ip
        )

    def on_disconnect_clicked(self):
        self.disconnect_requested.emit()

    def update_connection_state(self, state: ConnectionState, message: str = ""):
        self.lbl_status.setText(state.value)
        if state == ConnectionState.CONNECTED:
            self.lbl_status.setStyleSheet("font-weight: bold; color: #00e676; font-size: 13px;")
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            self.set_inputs_enabled(False)
        elif state in (ConnectionState.CONNECTING, ConnectionState.RECONNECTING):
            self.lbl_status.setStyleSheet("font-weight: bold; color: #ffb300; font-size: 13px;")
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
        else: # Disconnected or Connection Lost
            self.lbl_status.setStyleSheet("font-weight: bold; color: #ff5252; font-size: 13px;")
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.set_inputs_enabled(True)

    def set_inputs_enabled(self, enabled: bool):
        self.input_remote_ip.setEnabled(enabled)
        self.input_remote_port.setEnabled(enabled)
        self.input_master_addr.setEnabled(enabled)
        self.input_outstation_addr.setEnabled(enabled)
        self.input_local_ip.setEnabled(enabled)
