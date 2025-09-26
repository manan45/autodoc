"""
Configuration management for the auto documentation generator.

This module handles loading and managing application configuration
from various sources (files, environment variables, etc.).
"""

from .settings import Settings
from .logging_config import setup_logging

__all__ = [
    'Settings',
    'setup_logging',
]
