#!/usr/bin/env python
"""
Main entry point for Dynevi application.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from src.gui.main_window import run_app

if __name__ == "__main__":
    run_app()

