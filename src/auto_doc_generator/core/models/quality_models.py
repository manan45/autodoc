"""
Data models for code quality assessment results.

This module defines the data structures used to represent quality
analysis and assessment results.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


class QualityLevel(Enum):
    """Quality assessment levels."""
    
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class QualityCategory(Enum):
    """Categories of quality metrics."""
    
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    SECURITY = "security"
    PERFORMANCE = "performance"
    READABILITY = "readability"
    TESTABILITY = "testability"
    DOCUMENTATION = "documentation"


@dataclass
class QualityMetric:
    """A single quality metric measurement."""
    
    name: str
    value: Union[float, int, str]
    category: QualityCategory
    description: str = ""
    threshold_good: Optional[float] = None
    threshold_poor: Optional[float] = None
    unit: str = ""
    
    @property
    def normalized_value(self) -> float:
        """Get normalized value (0-100 scale)."""
        if isinstance(self.value, str):
            return 0.0
        
        # Simple normalization - can be enhanced based on metric type
        if self.threshold_good and self.threshold_poor:
            if self.value >= self.threshold_good:
                return 100.0
            elif self.value <= self.threshold_poor:
                return 0.0
            else:
                # Linear interpolation between thresholds
                range_size = self.threshold_good - self.threshold_poor
                position = self.value - self.threshold_poor
                return (position / range_size) * 100.0
        
        # Default normalization for values without thresholds
        return min(max(float(self.value), 0), 100)
    
    @property
    def quality_level(self) -> QualityLevel:
        """Get quality level based on normalized value."""
        normalized = self.normalized_value
        
        if normalized >= 90:
            return QualityLevel.EXCELLENT
        elif normalized >= 70:
            return QualityLevel.GOOD
        elif normalized >= 50:
            return QualityLevel.FAIR
        elif normalized >= 30:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL


@dataclass
class QualityMetrics:
    """Collection of quality metrics for a module or system."""
    
    module_path: str = ""
    metrics: List[QualityMetric] = field(default_factory=list)
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def add_metric(self, metric: QualityMetric) -> None:
        """Add a quality metric."""
        self.metrics.append(metric)
    
    def get_metric(self, name: str) -> Optional[QualityMetric]:
        """Get a metric by name."""
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None
    
    def get_metrics_by_category(self, category: QualityCategory) -> List[QualityMetric]:
        """Get all metrics in a specific category."""
        return [m for m in self.metrics if m.category == category]
    
    @property
    def overall_score(self) -> float:
        """Calculate overall quality score (0-100)."""
        if not self.metrics:
            return 0.0
        
        total_score = sum(metric.normalized_value for metric in self.metrics)
        return total_score / len(self.metrics)
    
    @property
    def overall_level(self) -> QualityLevel:
        """Get overall quality level."""
        score = self.overall_score
        
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 70:
            return QualityLevel.GOOD
        elif score >= 50:
            return QualityLevel.FAIR
        elif score >= 30:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def get_category_scores(self) -> Dict[QualityCategory, float]:
        """Get average scores by category."""
        category_scores = {}
        
        for category in QualityCategory:
            category_metrics = self.get_metrics_by_category(category)
            if category_metrics:
                avg_score = sum(m.normalized_value for m in category_metrics) / len(category_metrics)
                category_scores[category] = avg_score
            else:
                category_scores[category] = 0.0
        
        return category_scores
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'module_path': self.module_path,
            'calculated_at': self.calculated_at.isoformat(),
            'overall_score': self.overall_score,
            'overall_level': self.overall_level.value,
            'category_scores': {
                cat.value: score for cat, score in self.get_category_scores().items()
            },
            'metrics': [
                {
                    'name': m.name,
                    'value': m.value,
                    'category': m.category.value,
                    'normalized_value': m.normalized_value,
                    'quality_level': m.quality_level.value,
                    'description': m.description,
                    'unit': m.unit,
                }
                for m in self.metrics
            ]
        }


@dataclass
class QualityInsights:
    """AI-generated insights about code quality."""
    
    module_path: str
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    priority_actions: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    confidence_score: float = 0.0  # AI confidence in the assessment (0-1)
    
    def add_insight(self, insight: str) -> None:
        """Add a quality insight."""
        self.insights.append(insight)
    
    def add_recommendation(self, recommendation: str) -> None:
        """Add a quality recommendation."""
        self.recommendations.append(recommendation)
    
    def add_strength(self, strength: str) -> None:
        """Add a code strength."""
        self.strengths.append(strength)
    
    def add_issue(self, issue: str) -> None:
        """Add a code issue."""
        self.issues.append(issue)
    
    def add_priority_action(self, action: str) -> None:
        """Add a priority action item."""
        self.priority_actions.append(action)
    
    @property
    def has_insights(self) -> bool:
        """Check if there are any insights."""
        return bool(self.insights or self.recommendations or self.strengths or self.issues)
    
    @property
    def total_items(self) -> int:
        """Get total number of insight items."""
        return (len(self.insights) + len(self.recommendations) + 
                len(self.strengths) + len(self.issues) + len(self.priority_actions))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'module_path': self.module_path,
            'generated_at': self.generated_at.isoformat(),
            'confidence_score': self.confidence_score,
            'insights': self.insights,
            'recommendations': self.recommendations,
            'strengths': self.strengths,
            'issues': self.issues,
            'priority_actions': self.priority_actions,
            'has_insights': self.has_insights,
            'total_items': self.total_items,
        }


@dataclass
class ModuleQualityAssessment:
    """Complete quality assessment for a single module."""
    
    module_path: str
    module_name: str
    metrics: QualityMetrics = field(default_factory=lambda: QualityMetrics(""))
    insights: Optional[QualityInsights] = None
    assessed_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Set module path in metrics if not set."""
        if self.metrics.module_path == "":
            self.metrics.module_path = self.module_path
        
        if self.insights and self.insights.module_path == "":
            self.insights.module_path = self.module_path
    
    @property
    def overall_score(self) -> float:
        """Get overall quality score."""
        return self.metrics.overall_score
    
    @property
    def overall_level(self) -> QualityLevel:
        """Get overall quality level."""
        return self.metrics.overall_level
    
    @property
    def has_ai_insights(self) -> bool:
        """Check if AI insights are available."""
        return self.insights is not None and self.insights.has_insights
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'module_path': self.module_path,
            'module_name': self.module_name,
            'assessed_at': self.assessed_at.isoformat(),
            'overall_score': self.overall_score,
            'overall_level': self.overall_level.value,
            'metrics': self.metrics.to_dict(),
            'has_ai_insights': self.has_ai_insights,
        }
        
        if self.insights:
            result['insights'] = self.insights.to_dict()
        
        return result


@dataclass
class QualityAssessment:
    """Complete quality assessment for an entire codebase."""
    
    repository_path: str
    assessment_timestamp: datetime = field(default_factory=datetime.now)
    
    # Module-level assessments
    module_assessments: List[ModuleQualityAssessment] = field(default_factory=list)
    
    # Global insights (system-wide quality analysis)
    global_insights: Optional[QualityInsights] = None
    
    # Assessment metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_module_assessment(self, assessment: ModuleQualityAssessment) -> None:
        """Add a module quality assessment."""
        self.module_assessments.append(assessment)
    
    def get_module_assessment(self, module_path: str) -> Optional[ModuleQualityAssessment]:
        """Get assessment for a specific module."""
        for assessment in self.module_assessments:
            if assessment.module_path == module_path:
                return assessment
        return None
    
    def get_assessments_by_level(self, level: QualityLevel) -> List[ModuleQualityAssessment]:
        """Get all assessments at a specific quality level."""
        return [a for a in self.module_assessments if a.overall_level == level]
    
    @property
    def total_modules(self) -> int:
        """Get total number of assessed modules."""
        return len(self.module_assessments)
    
    @property
    def average_score(self) -> float:
        """Calculate average quality score across all modules."""
        if not self.module_assessments:
            return 0.0
        
        total_score = sum(a.overall_score for a in self.module_assessments)
        return total_score / len(self.module_assessments)
    
    @property
    def median_score(self) -> float:
        """Calculate median quality score."""
        if not self.module_assessments:
            return 0.0
        
        scores = sorted([a.overall_score for a in self.module_assessments])
        n = len(scores)
        
        if n % 2 == 0:
            return (scores[n//2 - 1] + scores[n//2]) / 2
        else:
            return scores[n//2]
    
    @property
    def quality_distribution(self) -> Dict[QualityLevel, int]:
        """Get distribution of modules by quality level."""
        distribution = {level: 0 for level in QualityLevel}
        
        for assessment in self.module_assessments:
            distribution[assessment.overall_level] += 1
        
        return distribution
    
    @property
    def best_modules(self) -> List[ModuleQualityAssessment]:
        """Get top 5 best quality modules."""
        return sorted(
            self.module_assessments, 
            key=lambda a: a.overall_score, 
            reverse=True
        )[:5]
    
    @property
    def worst_modules(self) -> List[ModuleQualityAssessment]:
        """Get top 5 worst quality modules."""
        return sorted(
            self.module_assessments, 
            key=lambda a: a.overall_score
        )[:5]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            'repository_path': self.repository_path,
            'assessment_timestamp': self.assessment_timestamp.isoformat(),
            'overview': {
                'total_modules': self.total_modules,
                'average_score': self.average_score,
                'median_score': self.median_score,
            },
            'quality_distribution': {
                level.value: count for level, count in self.quality_distribution.items()
            },
            'module_assessments': [a.to_dict() for a in self.module_assessments],
            'best_modules': [a.to_dict() for a in self.best_modules],
            'worst_modules': [a.to_dict() for a in self.worst_modules],
            'metadata': self.metadata,
        }
        
        if self.global_insights:
            result['global_insights'] = self.global_insights.to_dict()
        
        return result
