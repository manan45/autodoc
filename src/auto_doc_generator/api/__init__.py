"""
API layer for the auto documentation generator.

This module provides HTTP API endpoints for accessing documentation
generation functionality programmatically.
"""

from .controllers.analysis_controller import AnalysisController
from .controllers.documentation_controller import DocumentationController
from .controllers.repository_controller import RepositoryController

__all__ = [
    'AnalysisController',
    'DocumentationController',
    'RepositoryController',
]
