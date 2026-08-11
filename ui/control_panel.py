"""
Control / Write Operations Panel for Arcon DNP3 Client.
Requires mandatory explicit user confirmation modal dialog before sending output commands.
"""

from PySide6.QtWidgets import (
    QGroupBox, QGridLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QHBoxLayout, QVBoxLayout, QWidget, QTextEdit
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal
from dnp3.controls import DNP3ControlExecutor
from utils.logger import get_logger

_logger = get_logger()


class ControlPanel(QWidget):
    """
    GUI Panel for executing secondary DNP3 output / write commands.
    """
    control_executed = Signal(str, int, str, bool) # (cmd_type, index, value_str, success)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.master_client = None
        self.init_ui()

    def set_client(self, client):
        self.master_client = client

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Warning Header
        warn_box = QGroupBox("⚠️ Safety & Operations Warning")
        warn_layout = QVBoxLayout()
        lbl_warn = QLabel(
            "<b>IMPORTANT NOTICE:</b> Control operations send direct write commands to the connected DNP3 outstation / RTU.<br>"
            "Commands are NEVER executed automatically. All write operations require explicit user confirmation."
        )
        lbl_warn.setStyleSheet("color: #ffb74d;")
        warn_layout.addWidget(lbl_warn)
        warn_box.setLayout(warn_layout)
        main_layout.addWidget(warn_box)

        # Binary Output (CROB) Section
        bo_box = QGroupBox("Binary Output Control (CROB / Group 10)")
        bo_layout = QGridLayout()

        bo_layout.addWidget(QLabel("Point Index:"), 0, 0)
        self.input_bo_index = QLineEdit("0")
        bo_layout.addWidget(self.input_bo_index, 0, 1)

        bo_layout.addWidget(QLabel("Command State:"), 0, 2)
        self.combo_bo_val = QComboBox()
        self.combo_bo_val.addItems(["TRIP / LATCH_OFF (0)", "CLOSE / LATCH_ON (1)"])
        bo_layout.addWidget(self.combo_bo_val, 0, 3)

        bo_layout.addWidget(QLabel("Operation Mode:"), 1, 0)
        self.combo_bo_mode = QComboBox()
        self.combo_bo_mode.addItems(["DIRECT_OPERATE", "SELECT_BEFORE_OPERATE"])
        bo_layout.addWidget(self.combo_bo_mode, 1, 1)

        self.btn_send_bo = QPushButton("Execute Binary Output")
        self.btn_send_bo.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 6px;")
        self.btn_send_bo.clicked.connect(self.on_execute_binary_output)
        bo_layout.addWidget(self.btn_send_bo, 1, 2, 1, 2)

        bo_box.setLayout(bo_layout)
        main_layout.addWidget(bo_box)

        # Analog Output Section
        ao_box = QGroupBox("Analog Output Control (Group 40)")
        ao_layout = QGridLayout()

        ao_layout.addWidget(QLabel("Point Index:"), 0, 0)
        self.input_ao_index = QLineEdit("0")
        ao_layout.addWidget(self.input_ao_index, 0, 1)

        ao_layout.addWidget(QLabel("Setpoint Value:"), 0, 2)
        self.input_ao_val = QLineEdit("100.0")
        ao_layout.addWidget(self.input_ao_val, 0, 3)

        ao_layout.addWidget(QLabel("Operation Mode:"), 1, 0)
        self.combo_ao_mode = QComboBox()
        self.combo_ao_mode.addItems(["DIRECT_OPERATE", "SELECT_BEFORE_OPERATE"])
        ao_layout.addWidget(self.combo_ao_mode, 1, 1)

        self.btn_send_ao = QPushButton("Execute Analog Output")
        self.btn_send_ao.setStyleSheet("background-color: #d32f2f; color: white; font-weight: bold; padding: 6px;")
        self.btn_send_ao.clicked.connect(self.on_execute_analog_output)
        ao_layout.addWidget(self.btn_send_ao, 1, 2, 1, 2)

        ao_box.setLayout(ao_layout)
        main_layout.addWidget(ao_box)

        # Command Audit Log
        audit_box = QGroupBox("Command Execution Audit Log")
        audit_layout = QVBoxLayout()
        self.txt_audit = QTextEdit()
        self.txt_audit.setReadOnly(True)
        self.txt_audit.setFont(QFont("Monospace", 9))
        audit_layout.addWidget(self.txt_audit)
        audit_box.setLayout(audit_layout)

        main_layout.addWidget(audit_box)

    def confirm_command(self, cmd_type: str, index: int, value_str: str) -> bool:
        """
        Displays mandatory warning dialog per Section 16 requirements.
        """
        reply = QMessageBox.warning(
            self,
            "CONFIRM CONTROL COMMAND",
            f"<b>WARNING:</b><br>"
            f"This operation will send a control command to the connected DNP3 outstation.<br><br>"
            f"<b>Command Type:</b> {cmd_type}<br>"
            f"<b>Point Index:</b> {index}<br>"
            f"<b>Target Value:</b> {value_str}<br><br>"
            f"Are you sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def on_execute_binary_output(self):
        if not self.master_client or not self.master_client.is_connected:
            QMessageBox.critical(self, "Command Rejected", "DNP3 Master is not connected to an outstation.")
            return

        try:
            idx = int(self.input_bo_index.text().strip())
        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Point index must be an integer.")
            return

        val_bool = self.combo_bo_val.currentIndex() == 1
        val_str = "CLOSE (1)" if val_bool else "TRIP (0)"
        mode = "SELECT_OPERATE" if "SELECT" in self.combo_bo_mode.currentText() else "DIRECT"

        if not self.confirm_command("Binary Output (Group 10)", idx, val_str):
            _logger.info("[CONTROL CANCELLED] User cancelled Binary Output execution.")
            return

        success, msg = DNP3ControlExecutor.send_binary_output(
            self.master_client.master_app, idx, val_bool, mode
        )
        self.txt_audit.append(f"[{msg}]")
        self.control_executed.emit("Binary Output", idx, val_str, success)

    def on_execute_analog_output(self):
        if not self.master_client or not self.master_client.is_connected:
            QMessageBox.critical(self, "Command Rejected", "DNP3 Master is not connected to an outstation.")
            return

        try:
            idx = int(self.input_ao_index.text().strip())
        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Point index must be an integer.")
            return

        try:
            val_float = float(self.input_ao_val.text().strip())
        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Setpoint value must be a valid float number.")
            return

        mode = "SELECT_OPERATE" if "SELECT" in self.combo_ao_mode.currentText() else "DIRECT"

        if not self.confirm_command("Analog Output (Group 40)", idx, str(val_float)):
            _logger.info("[CONTROL CANCELLED] User cancelled Analog Output execution.")
            return

        success, msg = DNP3ControlExecutor.send_analog_output(
            self.master_client.master_app, idx, val_float, mode
        )
        self.txt_audit.append(f"[{msg}]")
        self.control_executed.emit("Analog Output", idx, str(val_float), success)
