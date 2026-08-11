"""
Measurement Table Component for Arcon DNP3 Client.
Displays real-time normalized DNP3 measurements (BI, AI, Counter, Status).
"""

from typing import List, Dict, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QHBoxLayout, QLineEdit
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt
from dnp3.models import DNP3Measurement


class MeasurementTable(QWidget):
    """
    GUI Component displaying all normalized live measurements.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        # Storage mapping (type, index) -> row
        self._row_map: Dict[Tuple[str, int], int] = {}

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Header / Search Filter Bar
        bar = QHBoxLayout()
        bar.addWidget(QLabel("<b>Live DNP3 Measurements</b>"))
        bar.addStretch()

        bar.addWidget(QLabel("Filter:"))
        self.input_filter = QLineEdit()
        self.input_filter.setPlaceholderText("Search index/value...")
        self.input_filter.textChanged.connect(self.filter_table)
        bar.addWidget(self.input_filter)

        layout.addLayout(bar)

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Data Type", "Index", "Value", "Quality", "Timestamp"])

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        layout.addWidget(self.table)
        self.setLayout(layout)

    def update_measurements(self, measurements: List[DNP3Measurement]):
        """Bulk updates or populates the measurement table."""
        self.table.setSortingEnabled(False)
        for m in measurements:
            self.update_single_measurement(m)
        self.table.setSortingEnabled(True)

    def update_single_measurement(self, m: DNP3Measurement):
        """Updates or inserts a single measurement row."""
        key = (m.type, m.index)
        
        if key in self._row_map:
            row = self._row_map[key]
        else:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._row_map[key] = row
            
            # Static type and index items
            item_type = QTableWidgetItem(m.type.replace("_", " ").title())
            item_index = QTableWidgetItem(str(m.index))
            item_index.setTextAlignment(Qt.AlignCenter)
            
            self.table.setItem(row, 0, item_type)
            self.table.setItem(row, 1, item_index)

        # Value
        item_val = QTableWidgetItem(str(m.value))
        item_val.setFont(QFont("Monospace", 9, QFont.Bold))
        self.table.setItem(row, 2, item_val)

        # Quality
        item_quality = QTableWidgetItem(m.quality)
        if "ONLINE" in m.quality and "OFFLINE" not in m.quality:
            item_quality.setForeground(QColor("#00e676"))
        else:
            item_quality.setForeground(QColor("#ff5252"))
        self.table.setItem(row, 3, item_quality)

        # Timestamp
        item_ts = QTableWidgetItem(m.timestamp)
        item_ts.setForeground(QColor("#aaaaaa"))
        self.table.setItem(row, 4, item_ts)

    def clear(self):
        self.table.setRowCount(0)
        self._row_map.clear()

    def filter_table(self, text: str):
        query = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and query in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
