#!/usr/bin/env python3
"""
===================================================================
ARCON DNP3 CLIENT - MAIN APPLICATION ENTRY POINT
===================================================================
Application Name: Arcon DNP3 Client
Description     : Standalone DNP3 Master Diagnostic and Monitoring Tool.
"""

import sys
import os
import argparse
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from utils.logger import get_logger

_logger = get_logger()


def parse_args():
    parser = argparse.ArgumentParser(
        prog="ArconDNP3Client",
        description="Arcon DNP3 Client - Master Diagnostic & Monitoring Application"
    )
    parser.add_argument("--ip", type=str, default=None, help="Remote Outstation IP Address (e.g. 192.168.1.20)")
    parser.add_argument("--port", type=int, default=None, help="Remote TCP Port (default: 20000)")
    parser.add_argument("--master-address", type=int, default=None, help="DNP3 Master Link Address (default: 1)")
    parser.add_argument("--outstation-address", type=int, default=None, help="DNP3 Outstation Link Address (default: 1024)")
    parser.add_argument("--poc", action="store_true", help="Run CLI Proof of Concept deliverable mode")

    return parser.parse_args()


def main():
    args = parse_args()

    # If --poc argument is passed, launch the CLI Proof of Concept
    if args.poc:
        from tools.test_cli_poc import run_poc
        run_poc()
        sys.exit(0)

    # Launch PySide6 GUI Desktop Application
    _logger.info("Starting Arcon DNP3 Client Desktop Interface...")
    app = QApplication(sys.argv)
    app.setApplicationName("Arcon DNP3 Client")
    app.setOrganizationName("Arcon")

    window = MainWindow(cli_args=args)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
