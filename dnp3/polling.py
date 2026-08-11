"""
DNP3 Class Polling and Read Scheduler Module.
Configures and manages periodic/manual reads of DNP3 Classes (0, 1, 2, 3).
"""

from typing import Any, Dict, Optional
from utils.logger import get_logger
from pydnp3 import opendnp3, openpal

_logger = get_logger()


class PollingManager:
    """Manages manual and scheduled class polling requests for a DNP3 Master."""

    def __init__(self):
        self.class_0_enabled = True
        self.class_1_enabled = True
        self.class_2_enabled = True
        self.class_3_enabled = True
        self.interval_ms = 1000

    def poll_all_classes(self, master_app: Any) -> bool:
        """Issues an Integrity Poll (Scan All / Class 0, 1, 2, 3) to the outstation."""
        if not master_app or not master_app.is_connected:
            _logger.warning("Cannot poll: Master station is not connected.")
            return False

        try:
            _logger.info("Issuing Read All / Class 0,1,2,3 poll request...")
            master_app.send_scan_all_request()
            return True
        except Exception as e:
            _logger.error(f"Class poll request rejected by outstation: {e}")
            return False

    def poll_selected_classes(
        self,
        master_app: Any,
        c0: bool = True,
        c1: bool = True,
        c2: bool = True,
        c3: bool = True
    ) -> bool:
        """Issues a targeted class poll request for enabled classes."""
        if not master_app or not master_app.is_connected:
            _logger.warning("Cannot poll: Master station is not connected.")
            return False

        try:
            # Build ClassField bitmask
            mask = 0
            if c0:
                mask |= opendnp3.ClassField.CLASS_0
            if c1:
                mask |= opendnp3.ClassField.CLASS_1
            if c2:
                mask |= opendnp3.ClassField.CLASS_2
            if c3:
                mask |= opendnp3.ClassField.CLASS_3

            if mask == 0:
                _logger.info("No DNP3 classes selected for polling.")
                return True

            field = opendnp3.ClassField(mask)
            _logger.info(f"Issuing class poll request for selected classes (Field mask: {mask})...")
            
            # Using master's scan or direct DemandScan
            master_app.master.Scan(field, opendnp3.TaskConfig().Default())
            return True
        except Exception as e:
            _logger.error(f"Class poll request failed: {e}")
            return False
