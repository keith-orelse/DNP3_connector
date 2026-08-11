"""
Event Table Component for Arcon DNP3 Client.
Displays real-time incoming DNP3 events (Sequence of Events).
"""

from typing import List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QHBoxLayout, QPushButton
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
from dnp3.events import DNP3Event


class EventTable(QWidget):
    """
    GUI Component displaying real-time incoming DNP3 events.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header Bar
        bar = QHBoxLayout()
        bar.addWidget(QLabel("<b>DNP3 Real-Time Sequence of Events (SOE)</b>"))
        bar.addStretch()

        self.btn_clear = QPushButton("Clear Events")
        self.btn_clear.clicked.connect(self.clear)
        bar.addWidget(self.btn_clear)

        layout.addLayout(bar)

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Time", "Event Type", "Index", "Value", "Quality"])

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def add_event(self, event: DNP3Event):
        """Inserts a new event at the top of the table."""
        self.table.insertRow(0)

        item_time = QTableWidgetItem(event.timestamp)
        item_time.setForeground(QColor("#aaaaaa"))
        item_type = QTableWidgetItem(event.type)
        item_index = QTableWidgetItem(str(event.index))
        item_index.setTextAlignment(Qt.AlignCenter)

        item_val = QTableWidgetItem(str(event.value))
        item_val.setFont(QFont("Monospace", 9, QFont.Bold))
        item_val.setForeground(QColor("#29b6f6"))

        item_quality = QTableWidgetItem(event.quality)
        if "ONLINE" in event.quality and "OFFLINE" not in event.quality:
            item_quality.setForeground(QColor("#00e676"))
        else:
            item_quality.setForeground(QColor("#ff5252"))

        self.table.setItem(0, 0, item_time)
        self.table.setItem(0, 1, item_type)
        self.table.setItem(0, 2, item_index)
        self.table.setItem(0, 3, item_val)
        self.table.setItem(0, 4, item_quality)

        # Limit displayed rows to max 300
        if self.table.rowCount() > 300:
            self.table.removeRow(300)

    def update_events(self, events: List[DNP3Event]):
        self.table.setRowCount(0)
        for ev in reversed(events):
            self.add_event(ev)

    def clear(self):
        self.table.setRowCount(0)
