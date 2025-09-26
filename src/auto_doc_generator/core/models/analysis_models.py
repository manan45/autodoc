"""
Data models for code analysis results.

This module defines the data structures used to represent the results
of code analysis operations.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


@dataclass
class CodeMetrics:
    """Metrics for a single code file or module."""
    
    file_path: str
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    docstring_coverage: float = 0.0
    
    def __post_init__(self):
        """Validate metrics after initialization."""
        if self.total_lines < 0:
            raise ValueError("Total lines cannot be negative")
        if self.code_lines > self.total_lines:
            raise ValueError("Code lines cannot exceed total lines")


@dataclass
class ComplexityMetrics:
    """Complexity metrics for code analysis."""
    
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    halstead_complexity: Dict[str, float] = field(default_factory=dict)
    maintainability_index: float = 0.0
    technical_debt_ratio: float = 0.0
    
    @property
    def overall_complexity_score(self) -> float:
        """Calculate overall complexity score (0-100)."""
        # Weighted average of different complexity metrics
        weights = {
            'cyclomatic': 0.3,
            'cognitive': 0.4,
            'maintainability': 0.3
        }
        
        score = (
            weights['cyclomatic'] * min(self.cyclomatic_complexity / 10, 10) +
            weights['cognitive'] * min(self.cognitive_complexity / 15, 10) +
            weights['maintainability'] * (100 - self.maintainability_index) / 10
        )
        
        return min(max(score, 0), 100)


@dataclass
class ModuleAnalysis:
    """Analysis result for a single module."""
    
    module_path: str
    module_name: str
    module_type: str = "module"  # module, service, utility, test, etc.
    description: str = ""
    metrics: CodeMetrics = field(default_factory=lambda: CodeMetrics(""))
    complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    dependencies: List[str] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    docstrings: Dict[str, str] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    
    @property
    def is_test_module(self) -> bool:
        """Check if this is a test module."""
        return 'test' in self.module_path.lower() or self.module_type == 'test'
    
    @property
    def has_documentation(self) -> bool:
        """Check if module has documentation."""
        return bool(self.description or self.docstrings)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Dictionary-like get method for backward compatibility.
        
        This allows ModuleAnalysis to behave like a dictionary
        when code expects dict-like access patterns.
        """
        # Map common dictionary keys to dataclass attributes
        attribute_map = {
            'module_path': 'module_path',
            'module_name': 'module_name', 
            'module_type': 'module_type',
            'description': 'description',
            'metrics': 'metrics',
            'complexity': 'complexity',
            'dependencies': 'dependencies',
            'functions': 'functions',
            'classes': 'classes',
            'imports': 'imports',
            'docstrings': 'docstrings',
            'issues': 'issues',
            # Common alternative names used in the codebase
            'path': 'module_path',
            'name': 'module_name',
            'type': 'module_type',
            'docstring': 'description'
        }
        
        if key in attribute_map:
            attr_name = attribute_map[key]
            return getattr(self, attr_name, default)
        
        # Fallback for any other attribute access
        return getattr(self, key, default)


@dataclass
class AnalysisResult:
    """Complete analysis result for a codebase."""
    
    repository_path: str
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    total_files: int = 0
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    languages_detected: List[str] = field(default_factory=list)
    project_type: str = "unknown"
    
    # Module-level analysis
    modules: List[ModuleAnalysis] = field(default_factory=list)
    
    # Aggregate metrics
    overall_metrics: CodeMetrics = field(default_factory=lambda: CodeMetrics(""))
    overall_complexity: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    
    # Dependency analysis
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    circular_dependencies: List[List[str]] = field(default_factory=list)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_module_by_path(self, path: str) -> Optional[ModuleAnalysis]:
        """Get module analysis by file path."""
        for module in self.modules:
            if module.module_path == path:
                return module
        return None
    
    def get_modules_by_type(self, module_type: str) -> List[ModuleAnalysis]:
        """Get all modules of a specific type."""
        return [m for m in self.modules if m.module_type == module_type]
    
    def get_high_complexity_modules(self, threshold: float = 70.0) -> List[ModuleAnalysis]:
        """Get modules with high complexity scores."""
        return [
            m for m in self.modules 
            if m.complexity.overall_complexity_score >= threshold
        ]
    
    @property
    def average_complexity(self) -> float:
        """Calculate average complexity across all modules."""
        if not self.modules:
            return 0.0
        
        total_complexity = sum(
            m.complexity.overall_complexity_score for m in self.modules
        )
        return total_complexity / len(self.modules)
    
    @property
    def test_coverage_estimate(self) -> float:
        """Estimate test coverage based on test modules vs regular modules."""
        test_modules = len(self.get_modules_by_type('test'))
        regular_modules = len([m for m in self.modules if not m.is_test_module])
        
        if regular_modules == 0:
            return 100.0
        
        return min((test_modules / regular_modules) * 100, 100.0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'repository_path': self.repository_path,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'overview': {
                'total_files': self.total_files,
                'total_lines': self.total_lines,
                'total_functions': self.total_functions,
                'total_classes': self.total_classes,
                'languages_detected': self.languages_detected,
                'project_type': self.project_type,
                'average_complexity': self.average_complexity,
                'test_coverage_estimate': self.test_coverage_estimate,
            },
            'modules': [
                {
                    'path': m.module_path,
                    'name': m.module_name,
                    'type': m.module_type,
                    'description': m.description,
                    'metrics': {
                        'total_lines': m.metrics.total_lines,
                        'code_lines': m.metrics.code_lines,
                        'function_count': m.metrics.function_count,
                        'class_count': m.metrics.class_count,
                    },
                    'complexity_score': m.complexity.overall_complexity_score,
                    'has_documentation': m.has_documentation,
                }
                for m in self.modules
            ],
            'complexity': {
                'average': self.average_complexity,
                'high_complexity_modules': len(self.get_high_complexity_modules()),
            },
            'dependencies': {
                'dependency_graph': self.dependency_graph,
                'circular_dependencies': self.circular_dependencies,
            },
            'metadata': self.metadata,
        }
