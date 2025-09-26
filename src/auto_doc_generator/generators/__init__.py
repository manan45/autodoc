"""
Documentation generators for the auto documentation generator.

This module contains feature-based generators that create different
types of documentation output.
"""

from .base.base_generator import BaseGenerator
from .documentation.unified_html_generator import UnifiedHTMLGenerator
from .documentation.markdown_generator import MarkdownGenerator
from .diagrams.architecture_diagrams import ArchitectureDiagramGenerator
from .quality.quality_reports import QualityReportGenerator
from .ai.ai_coordinator import AICoordinator

__all__ = [
    'BaseGenerator',
    'UnifiedHTMLGenerator',
    'MarkdownGenerator', 
    'ArchitectureDiagramGenerator',
    'QualityReportGenerator',
    'AICoordinator',
]