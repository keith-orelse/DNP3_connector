"""
Polling Controls Panel for Arcon DNP3 Client.
"""

from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QVBoxLayout, QPushButton, QCheckBox,
    QComboBox, QLabel
)
from PySide6.QtCore import Signal


class PollingPanel(QGroupBox):
    """
    GUI Panel for configuring DNP3 class polling and execution triggers.
    """
    read_all_requested = Signal()
    poll_selected_requested = Signal(bool, bool, bool, bool)  # (c0, c1, c2, c3)
    interval_changed = Signal(int)                           # interval_ms
    auto_polling_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__("DNP3 Class Polling & Cyclic Schedule", parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setSpacing(12)

        # Buttons
        self.btn_read_all = QPushButton("Read All (Integrity)")
        self.btn_read_all.setStyleSheet("font-weight: bold; padding: 5px 12px;")
        self.btn_read_all.clicked.connect(lambda: self.read_all_requested.emit())

        self.btn_poll_now = QPushButton("Poll Selected")
        self.btn_poll_now.setStyleSheet("padding: 5px 12px;")
        self.btn_poll_now.clicked.connect(self.on_poll_now_clicked)

        layout.addWidget(self.btn_read_all)
        layout.addWidget(self.btn_poll_now)
        layout.addSpacing(15)

        # Class Checkboxes
        layout.addWidget(QLabel("Classes:"))
        self.chk_class0 = QCheckBox("Class 0 (Static)")
        self.chk_class0.setChecked(True)
        self.chk_class1 = QCheckBox("Class 1")
        self.chk_class1.setChecked(True)
        self.chk_class2 = QCheckBox("Class 2")
        self.chk_class2.setChecked(True)
        self.chk_class3 = QCheckBox("Class 3")
        self.chk_class3.setChecked(True)

        layout.addWidget(self.chk_class0)
        layout.addWidget(self.chk_class1)
        layout.addWidget(self.chk_class2)
        layout.addWidget(self.chk_class3)
        layout.addSpacing(15)

        # Cyclic Interval
        layout.addWidget(QLabel("Cyclic Interval:"))
        self.combo_interval = QComboBox()
        self.combo_interval.addItems(["1000 ms", "2000 ms", "5000 ms", "10000 ms"])
        self.combo_interval.currentIndexChanged.connect(self.on_interval_changed)
        layout.addWidget(self.combo_interval)

        # Cyclic Polling Toggle
        self.chk_auto_poll = QCheckBox("Enable Cyclic Polling")
        self.chk_auto_poll.setChecked(True)
        self.chk_auto_poll.toggled.connect(lambda checked: self.auto_polling_toggled.emit(checked))
        layout.addWidget(self.chk_auto_poll)

        layout.addStretch()
        self.setLayout(layout)

    def on_poll_now_clicked(self):
        c0 = self.chk_class0.isChecked()
        c1 = self.chk_class1.isChecked()
        c2 = self.chk_class2.isChecked()
        c3 = self.chk_class3.isChecked()
        self.poll_selected_requested.emit(c0, c1, c2, c3)

    def on_interval_changed(self, index: int):
        intervals = [1000, 2000, 5000, 10000]
        if 0 <= index < len(intervals):
            self.interval_changed.emit(intervals[index])
