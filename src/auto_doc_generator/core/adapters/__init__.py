"""
Component adapters for coordinator integration.

This module contains adapters that allow the coordinator to interact
with existing analyzers and generators through a standardized interface.
"""

from .analyzer_adapter import AnalyzerAdapter
from .generator_adapter import GeneratorAdapter
from .component_registry import ComponentRegistry

__all__ = [
    'AnalyzerAdapter',
    'GeneratorAdapter', 
    'ComponentRegistry'
]
