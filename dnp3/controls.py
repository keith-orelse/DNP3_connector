"""
Control Operations Module for DNP3 Master.
Handles Binary Output (CROB) and Analog Output (Command) execution with logging.
"""

import time
from typing import Tuple, Optional, Any
from utils.logger import get_logger

_logger = get_logger()


class DNP3ControlExecutor:
    """Executes controlled write/output commands against a DNP3 Master instance."""

    @staticmethod
    def send_binary_output(
        master_app: Any,
        index: int,
        val: bool,
        op_type: str = "DIRECT"
    ) -> Tuple[bool, str]:
        """
        Sends a Binary Output / CROB command to the specified point index.
        val: True (PULSE_ON/LATCH_ON) or False (LATCH_OFF)
        """
        if not master_app or not master_app.is_connected:
            return False, "Master is not connected to an outstation."

        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            _logger.info(f"[CONTROL] Sending Binary Output [{index}] = {val} ({op_type}) at {timestamp}")
            
            # Group 10 Variation 2: Binary Output Status / Control
            if op_type.upper() == "SELECT_OPERATE":
                master_app.send_select_and_operate_point_command(
                    group=10, variation=2, index=index, val_to_set=val
                )
            else:
                master_app.send_direct_point_command(
                    group=10, variation=2, index=index, val_to_set=val
                )

            res_msg = f"Binary Output [{index}] set to {val} ({op_type}) successfully."
            _logger.info(f"[CONTROL RESULT] {res_msg}")
            return True, res_msg
        except Exception as e:
            err_msg = f"Failed to execute Binary Output on index {index}: {e}"
            _logger.error(f"[CONTROL ERROR] {err_msg}")
            return False, err_msg

    @staticmethod
    def send_analog_output(
        master_app: Any,
        index: int,
        val: float,
        op_type: str = "DIRECT"
    ) -> Tuple[bool, str]:
        """
        Sends an Analog Output command to the specified point index.
        """
        if not master_app or not master_app.is_connected:
            return False, "Master is not connected to an outstation."

        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            _logger.info(f"[CONTROL] Sending Analog Output [{index}] = {val} ({op_type}) at {timestamp}")

            # Group 40 Variation 4: Analog Output Command / Status
            if op_type.upper() == "SELECT_OPERATE":
                master_app.send_select_and_operate_point_command(
                    group=40, variation=4, index=index, val_to_set=float(val)
                )
            else:
                master_app.send_direct_point_command(
                    group=40, variation=4, index=index, val_to_set=float(val)
                )

            res_msg = f"Analog Output [{index}] set to {val} ({op_type}) successfully."
            _logger.info(f"[CONTROL RESULT] {res_msg}")
            return True, res_msg
        except Exception as e:
            err_msg = f"Failed to execute Analog Output on index {index}: {e}"
            _logger.error(f"[CONTROL ERROR] {err_msg}")
            return False, err_msg
