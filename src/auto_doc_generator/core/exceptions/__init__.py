"""
Custom exceptions for the auto documentation generator.

This module defines custom exceptions used throughout the application
for better error handling and debugging.
"""

from .analysis_exceptions import AnalysisError, CodeAnalysisError, QualityAnalysisError
from .generation_exceptions import GenerationError, TemplateError, OutputError

__all__ = [
    'AnalysisError',
    'CodeAnalysisError', 
    'QualityAnalysisError',
    'GenerationError',
    'TemplateError',
    'OutputError',
]
