#!/usr/bin/env python3
"""
Auto Documentation Generator Package

A comprehensive automatic documentation generation system with AI/ML pipeline support.
"""

__version__ = "1.0.0"
__author__ = "Auto Documentation Team"
__email__ = "docs@example.com"

from .main import main

# Import core services that are now implemented
from .core.services.analysis_service import AnalysisService

__all__ = [
    "main",
    "AnalysisService",
]
