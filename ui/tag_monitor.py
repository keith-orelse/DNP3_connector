"""
DNP3 Tag Monitor Component for Arcon DNP3 Client.
Allows monitoring specific DNP3 points by user-defined names and descriptions.
"""

from typing import List, Dict, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLabel, QHBoxLayout, QPushButton,
    QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, Signal
from dnp3.models import (
    DNP3Measurement,
    TYPE_ANALOG_INPUT,
    TYPE_BINARY_INPUT,
    TYPE_COUNTER,
    TYPE_BINARY_OUTPUT_STATUS,
    TYPE_ANALOG_OUTPUT_STATUS,
)


class AddTagDialog(QDialog):
    """Modal dialog to add a new DNP3 monitored tag."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Monitored DNP3 Tag")
        self.resize(380, 220)
        self.init_ui()

    def init_ui(self):
        layout = QFormLayout(self)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("e.g. Bus Voltage")
        layout.addRow("Tag Name:", self.input_name)

        self.combo_type = QComboBox()
        self.combo_type.addItems([
            "Analog Input",
            "Binary Input",
            "Counter",
            "Analog Output Status",
            "Binary Output Status"
        ])
        layout.addRow("DNP3 Object Type:", self.combo_type)

        self.input_index = QLineEdit("0")
        layout.addRow("Point Index:", self.input_index)

        self.input_desc = QLineEdit()
        self.input_desc.setPlaceholderText("e.g. Main Substation Feeder 1")
        layout.addRow("Description:", self.input_desc)

        btn_box = QHBoxLayout()
        self.btn_ok = QPushButton("Add Tag")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(self.btn_ok)
        btn_box.addWidget(self.btn_cancel)
        layout.addRow(btn_box)

    def get_tag_data(self) -> Tuple[str, str, int, str]:
        name = self.input_name.text().strip() or "Unnamed Tag"
        type_str = self.combo_type.currentText().lower().replace(" ", "_")
        try:
            idx = int(self.input_index.text().strip())
        except ValueError:
            idx = 0
        desc = self.input_desc.text().strip()
        return name, type_str, idx, desc


class TagMonitor(QWidget):
    """
    GUI Panel for user-configured DNP3 Tag Monitoring.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_monitoring = True
        # List of tags: Dict[id, {name, type, index, desc}]
        self.tags = [
            {"name": "Bus Voltage", "type": TYPE_ANALOG_INPUT, "index": 0, "desc": "Phase A Voltage (V)"},
            {"name": "Line Current", "type": TYPE_ANALOG_INPUT, "index": 1, "desc": "Feeder Current (A)"},
            {"name": "Breaker Status", "type": TYPE_BINARY_INPUT, "index": 0, "desc": "Main Circuit Breaker"},
            {"name": "Active Energy", "type": TYPE_COUNTER, "index": 0, "desc": "Substation Meter (kWh)"},
        ]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Action Bar
        bar = QHBoxLayout()
        bar.addWidget(QLabel("<b>DNP3 Monitored Tags</b>"))
        bar.addStretch()

        self.btn_add = QPushButton("Add Tag")
        self.btn_add.clicked.connect(self.on_add_tag)
        bar.addWidget(self.btn_add)

        self.btn_remove = QPushButton("Remove Tag")
        self.btn_remove.clicked.connect(self.on_remove_tag)
        bar.addWidget(self.btn_remove)

        self.btn_toggle_mon = QPushButton("Stop Monitoring")
        self.btn_toggle_mon.clicked.connect(self.toggle_monitoring)
        bar.addWidget(self.btn_toggle_mon)

        layout.addLayout(bar)

        # Table Widget
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Tag Name", "Type", "Index", "Value", "Quality", "Description"])

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)

        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        layout.addWidget(self.table)
        self.setLayout(layout)
        self.refresh_tag_rows()

    def refresh_tag_rows(self):
        self.table.setRowCount(0)
        for tag in self.tags:
            row = self.table.rowCount()
            self.table.insertRow(row)

            item_name = QTableWidgetItem(tag["name"])
            item_type = QTableWidgetItem(tag["type"].replace("_", " ").title())
            item_index = QTableWidgetItem(str(tag["index"]))
            item_index.setTextAlignment(Qt.AlignCenter)

            item_val = QTableWidgetItem("N/A")
            item_val.setFont(QFont("Monospace", 9, QFont.Bold))
            item_quality = QTableWidgetItem("OFFLINE")
            item_desc = QTableWidgetItem(tag["desc"])

            self.table.setItem(row, 0, item_name)
            self.table.setItem(row, 1, item_type)
            self.table.setItem(row, 2, item_index)
            self.table.setItem(row, 3, item_val)
            self.table.setItem(row, 4, item_quality)
            self.table.setItem(row, 5, item_desc)

    def on_add_tag(self):
        dlg = AddTagDialog(self)
        if dlg.exec() == QDialog.Accepted:
            name, type_str, idx, desc = dlg.get_tag_data()
            self.tags.append({"name": name, "type": type_str, "index": idx, "desc": desc})
            self.refresh_tag_rows()

    def on_remove_tag(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        if 0 <= row < len(self.tags):
            self.tags.pop(row)
            self.refresh_tag_rows()

    def toggle_monitoring(self):
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.btn_toggle_mon.setText("Stop Monitoring")
            self.btn_toggle_mon.setStyleSheet("")
        else:
            self.btn_toggle_mon.setText("Start Monitoring")
            self.btn_toggle_mon.setStyleSheet("background-color: #00c853; color: white;")

    def update_tag_value(self, measurement: DNP3Measurement):
        if not self.is_monitoring:
            return

        for row, tag in enumerate(self.tags):
            if tag["type"] == measurement.type and tag["index"] == measurement.index:
                item_val = QTableWidgetItem(str(measurement.value))
                item_val.setFont(QFont("Monospace", 9, QFont.Bold))

                item_quality = QTableWidgetItem(measurement.quality)
                if "ONLINE" in measurement.quality and "OFFLINE" not in measurement.quality:
                    item_quality.setForeground(QColor("#00e676"))
                else:
                    item_quality.setForeground(QColor("#ff5252"))

                self.table.setItem(row, 3, item_val)
                self.table.setItem(row, 4, item_quality)
