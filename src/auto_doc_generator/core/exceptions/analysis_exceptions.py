"""
Analysis-related exceptions.

This module defines exceptions that can occur during codebase analysis.
"""


class AnalysisError(Exception):
    """Base exception for analysis-related errors."""
    
    def __init__(self, message: str, file_path: str = None, details: dict = None):
        """
        Initialize analysis error.
        
        Args:
            message: Error message
            file_path: Optional file path where error occurred
            details: Optional additional error details
        """
        self.file_path = file_path
        self.details = details or {}
        
        if file_path:
            message = f"{message} (file: {file_path})"
        
        super().__init__(message)


class CodeAnalysisError(AnalysisError):
    """Exception for code structure analysis errors."""
    pass


class QualityAnalysisError(AnalysisError):
    """Exception for quality analysis errors."""
    pass


class AIAnalysisError(AnalysisError):
    """Exception for AI/ML component analysis errors."""
    pass


class DependencyAnalysisError(AnalysisError):
    """Exception for dependency analysis errors."""
    pass


class ComplexityAnalysisError(AnalysisError):
    """Exception for complexity analysis errors."""
    pass
