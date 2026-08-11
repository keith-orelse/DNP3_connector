"""
Structured logging module for Arcon DNP3 Client.
Supports broadcasting log events to UI listeners thread-safely.
"""

import logging
import sys
from datetime import datetime
from typing import Callable, List, Optional


class UILogHandler(logging.Handler):
    """Custom logging handler that broadcasts log messages to registered UI callbacks."""
    
    def __init__(self):
        super().__init__()
        self._listeners: List[Callable[[str, str, str], None]] = []

    def add_listener(self, callback: Callable[[str, str, str], None]):
        """Adds a listener callback(timestamp, level, message)."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str, str, str], None]):
        """Removes a listener callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        level = record.levelname
        for listener in self._listeners:
            try:
                listener(timestamp, level, msg)
            except Exception:
                pass


_ui_handler = UILogHandler()
_ui_handler.setFormatter(logging.Formatter('%(message)s'))

_logger = logging.getLogger("ArconDNP3Client")
_logger.setLevel(logging.INFO)

# Console Handler
_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(name)s: %(message)s', '%H:%M:%S'))

_logger.addHandler(_console_handler)
_logger.addHandler(_ui_handler)


def get_logger() -> logging.Logger:
    return _logger


def add_ui_log_listener(callback: Callable[[str, str, str], None]):
    _ui_handler.add_listener(callback)


def remove_ui_log_listener(callback: Callable[[str, str, str], None]):
    _ui_handler.remove_listener(callback)
