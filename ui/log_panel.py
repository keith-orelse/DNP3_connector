"""
Log Viewer Component for Arcon DNP3 Client.
Displays real-time application events, connection logs, and DNP3 protocol messages thread-safely.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QHBoxLayout, QPushButton, QLabel
)
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QFont
from utils.logger import add_ui_log_listener, remove_ui_log_listener


class LogPanel(QWidget):
    """
    GUI Component displaying live structured application & communication logs.
    Uses Qt Signals to ensure thread-safe text append operations.
    """
    log_signal = Signal(str, str, str)  # (timestamp, level, msg)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.log_signal.connect(self.handle_log_append)
        add_ui_log_listener(self.on_log_received)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header Bar
        bar = QHBoxLayout()
        bar.addWidget(QLabel("<b>Application & DNP3 Protocol Logs</b>"))
        bar.addStretch()

        self.btn_clear = QPushButton("Clear Logs")
        self.btn_clear.clicked.connect(self.clear)
        bar.addWidget(self.btn_clear)

        layout.addLayout(bar)

        # Text Console Widget
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Monospace", 9))
        self.txt_log.setStyleSheet("background-color: #121212; color: #e0e0e0;")

        layout.addWidget(self.txt_log)

    def on_log_received(self, timestamp: str, level: str, msg: str):
        """Callback from logging thread - emits Qt signal for main thread safety."""
        self.log_signal.emit(timestamp, level, msg)

    @Slot(str, str, str)
    def handle_log_append(self, timestamp: str, level: str, msg: str):
        """Slot executed on Qt main GUI thread to safely update QTextEdit."""
        color = "#e0e0e0"
        if level in ("ERROR", "CRITICAL"):
            color = "#ff5252"
        elif level == "WARNING":
            color = "#ffb74d"
        elif "Connected" in msg or "SUCCESS" in msg:
            color = "#00e676"
        elif "CONTROL" in msg:
            color = "#29b6f6"

        formatted = f'<span style="color: #757575;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">[{level}]</span> <span style="color: {color};">{msg}</span>'
        self.txt_log.append(formatted)

    def clear(self):
        self.txt_log.clear()

    def closeEvent(self, event):
        remove_ui_log_listener(self.on_log_received)
        super().closeEvent(event)
