#!/usr/bin/env python3
"""
Main entry point for the auto documentation generator package.

This module allows the package to be run with python -m auto_doc_generator.
"""

import os
import sys
from pathlib import Path

# Disable ChromaDB telemetry early
os.environ.setdefault('ANONYMIZED_TELEMETRY', 'false')

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

from auto_doc_generator.main import main

if __name__ == "__main__":
    sys.exit(main())
