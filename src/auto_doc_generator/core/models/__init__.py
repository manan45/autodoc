"""
Core data models for the auto documentation generator.

This module defines the domain models that represent the core entities
in the documentation generation system.
"""

from .analysis_models import AnalysisResult, CodeMetrics, ComplexityMetrics
from .documentation_models import DocumentationResult, DocumentSection, TemplateData
from .quality_models import QualityAssessment, QualityMetrics, QualityInsights
from .ai_models import AIComponent, MLModel, Pipeline, Framework

__all__ = [
    # Analysis models
    'AnalysisResult',
    'CodeMetrics', 
    'ComplexityMetrics',
    
    # Documentation models
    'DocumentationResult',
    'DocumentSection',
    'TemplateData',
    
    # Quality models
    'QualityAssessment',
    'QualityMetrics',
    'QualityInsights',
    
    # AI models
    'AIComponent',
    'MLModel',
    'Pipeline',
    'Framework',
]
