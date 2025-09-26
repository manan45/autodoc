"""
Analysis service for orchestrating codebase analysis.

This service coordinates different types of analysis (code, AI/ML, quality)
and provides a unified interface for the analysis process.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime

from ..models.analysis_models import AnalysisResult, ModuleAnalysis, CodeMetrics, ComplexityMetrics
from ..models.ai_models import AIComponent
from ..models.quality_models import QualityAssessment
from ..repositories.file_repository import FileRepository
from ..repositories.cache_repository import CacheRepository
from ..exceptions.analysis_exceptions import AnalysisError

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Service for orchestrating comprehensive codebase analysis.
    
    This service coordinates different analyzers and provides a unified
    interface for analyzing codebases.
    """
    
    def __init__(
        self, 
        file_repository: FileRepository,
        cache_repository: Optional[CacheRepository] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the analysis service.
        
        Args:
            file_repository: Repository for file operations
            cache_repository: Optional cache repository for performance
            config: Optional configuration dictionary
        """
        self.file_repository = file_repository
        self.cache_repository = cache_repository
        self.config = config or {}
        
        # Analysis configuration
        self.analysis_config = self.config.get('analysis', {})
        self.include_patterns = self.analysis_config.get('include_patterns', ['*.py'])
        self.exclude_patterns = self.analysis_config.get('exclude_patterns', [
            '*/tests/*', '*/__pycache__/*', '*/.git/*', '*/venv/*', '*/.venv/*',
            '*/node_modules/*', '*/env/*', '*/.env/*', '*/site-packages/*',
            '*/.pytest_cache/*', '*/.mypy_cache/*', '*/build/*', '*/dist/*'
        ])
        
        # Initialize analyzers (will be injected)
        self._code_analyzer = None
        self._ai_analyzer = None
        self._quality_analyzer = None
    
    def set_analyzers(self, code_analyzer=None, ai_analyzer=None, quality_analyzer=None):
        """
        Set the specific analyzers to use.
        
        This allows for dependency injection of different analyzer implementations.
        """
        self._code_analyzer = code_analyzer
        self._ai_analyzer = ai_analyzer
        self._quality_analyzer = quality_analyzer
    
    def analyze_codebase(self, repository_path: str) -> AnalysisResult:
        """
        Perform comprehensive analysis of a codebase.
        
        Args:
            repository_path: Path to the repository to analyze
            
        Returns:
            AnalysisResult: Complete analysis results
            
        Raises:
            AnalysisError: If analysis fails
        """
        try:
            logger.info(f"Starting codebase analysis for: {repository_path}")
            start_time = datetime.now()
            
            # Validate repository path
            repo_path = Path(repository_path)
            if not repo_path.exists():
                raise AnalysisError(f"Repository path does not exist: {repository_path}")
            
            # Check cache first
            cache_key = f"analysis_{repository_path}_{self._get_repo_hash(repo_path)}"
            if self.cache_repository:
                cached_result = self.cache_repository.get(cache_key)
                if cached_result and self._is_cache_valid(cached_result):
                    logger.info("Using cached analysis results")
                    return self._create_analysis_result_from_cache(cached_result)
            
            # Initialize analysis result
            analysis_result = AnalysisResult(
                repository_path=repository_path,
                analysis_timestamp=start_time
            )
            
            # Get list of files to analyze
            files_to_analyze = self._get_files_to_analyze(repo_path)
            logger.info(f"Found {len(files_to_analyze)} files to analyze")
            
            # Perform code structure analysis
            if self._code_analyzer:
                logger.info("Performing code structure analysis")
                code_analysis = self._code_analyzer.analyze(repo_path)
                self._merge_code_analysis(analysis_result, code_analysis)
            
            # Perform AI/ML component analysis
            ai_analysis = None
            if self._ai_analyzer and self.analysis_config.get('ai_analysis', {}).get('enabled', True):
                logger.info("Performing AI/ML component analysis")
                ai_analysis = self._ai_analyzer.analyze(repo_path)
                self._merge_ai_analysis(analysis_result, ai_analysis)
            
            # Perform quality analysis
            if self._quality_analyzer:
                logger.info("Performing quality analysis")
                quality_analysis = self._quality_analyzer.analyze(repo_path)
                # Quality analysis is separate but can be used to enhance the main result
                analysis_result.metadata['quality_analysis'] = quality_analysis
            
            # Calculate aggregate metrics
            self._calculate_aggregate_metrics(analysis_result)
            
            # Cache the results
            if self.cache_repository:
                self.cache_repository.set(cache_key, analysis_result.to_dict())
            
            analysis_duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Analysis completed in {analysis_duration:.2f} seconds")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise AnalysisError(f"Failed to analyze codebase: {str(e)}") from e
    
    def analyze_single_file(self, file_path: str) -> ModuleAnalysis:
        """
        Analyze a single file.
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            ModuleAnalysis: Analysis results for the file
        """
        try:
            if not self._code_analyzer:
                raise AnalysisError("Code analyzer not configured")
            
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise AnalysisError(f"File does not exist: {file_path}")
            
            return self._code_analyzer.analyze_single_file(file_path)
            
        except Exception as e:
            logger.error(f"Single file analysis failed: {str(e)}")
            raise AnalysisError(f"Failed to analyze file {file_path}: {str(e)}") from e
    
    def get_analysis_summary(self, analysis_result: AnalysisResult) -> Dict[str, Any]:
        """
        Get a summary of analysis results.
        
        Args:
            analysis_result: The analysis result to summarize
            
        Returns:
            Dict containing analysis summary
        """
        return {
            'repository_path': analysis_result.repository_path,
            'analysis_timestamp': analysis_result.analysis_timestamp.isoformat(),
            'overview': {
                'total_files': analysis_result.total_files,
                'total_lines': analysis_result.total_lines,
                'total_functions': analysis_result.total_functions,
                'total_classes': analysis_result.total_classes,
                'languages_detected': analysis_result.languages_detected,
                'project_type': analysis_result.project_type,
                'average_complexity': analysis_result.average_complexity,
                'test_coverage_estimate': analysis_result.test_coverage_estimate,
            },
            'complexity': {
                'high_complexity_modules': len(analysis_result.get_high_complexity_modules()),
                'average_complexity': analysis_result.average_complexity,
            },
            'dependencies': {
                'total_dependencies': len(analysis_result.dependency_graph),
                'circular_dependencies': len(analysis_result.circular_dependencies),
            },
            'modules_by_type': {
                module_type: len(analysis_result.get_modules_by_type(module_type))
                for module_type in set(m.module_type for m in analysis_result.modules)
            }
        }
    
    def _get_files_to_analyze(self, repo_path: Path) -> List[str]:
        """Get list of files to analyze based on include/exclude patterns."""
        return self.file_repository.find_files(
            repo_path, 
            include_patterns=self.include_patterns,
            exclude_patterns=self.exclude_patterns
        )
    
    def _get_repo_hash(self, repo_path: Path) -> str:
        """Generate a hash for the repository state (for caching)."""
        # Simple implementation - in production, consider git commit hash
        import hashlib
        
        files = self._get_files_to_analyze(repo_path)
        hash_content = ""
        
        for file_path in sorted(files)[:10]:  # Sample first 10 files
            try:
                mtime = Path(file_path).stat().st_mtime
                hash_content += f"{file_path}:{mtime};"
            except (OSError, IOError):
                continue
        
        return hashlib.md5(hash_content.encode()).hexdigest()[:8]
    
    def _is_cache_valid(self, cached_result: Dict[str, Any]) -> bool:
        """Check if cached analysis result is still valid."""
        # Simple time-based validation - could be enhanced
        cache_time = datetime.fromisoformat(cached_result.get('analysis_timestamp', ''))
        age_hours = (datetime.now() - cache_time).total_seconds() / 3600
        
        max_cache_age = self.analysis_config.get('cache_max_age_hours', 24)
        return age_hours < max_cache_age
    
    def _create_analysis_result_from_cache(self, cached_data: Dict[str, Any]) -> AnalysisResult:
        """Create AnalysisResult from cached data, handling the overview structure."""
        overview = cached_data.get('overview', {})
        
        # Create the analysis result with data from overview
        analysis_result = AnalysisResult(
            repository_path=cached_data.get('repository_path', ''),
            analysis_timestamp=datetime.fromisoformat(cached_data.get('analysis_timestamp', datetime.now().isoformat())),
            total_files=overview.get('total_files', 0),
            total_lines=overview.get('total_lines', 0),
            total_functions=overview.get('total_functions', 0),
            total_classes=overview.get('total_classes', 0),
            languages_detected=overview.get('languages_detected', []),
            project_type=overview.get('project_type', 'unknown')
        )
        
        # Add modules if present
        modules_data = cached_data.get('modules', [])
        for module_data in modules_data:
            module_analysis = self._create_module_analysis(module_data)
            analysis_result.modules.append(module_analysis)
        
        # Add dependency information
        dependencies = cached_data.get('dependencies', {})
        analysis_result.dependency_graph = dependencies.get('dependency_graph', {})
        analysis_result.circular_dependencies = dependencies.get('circular_dependencies', [])
        
        # Add complexity information
        complexity_data = cached_data.get('complexity', {})
        if complexity_data:
            analysis_result.overall_complexity = ComplexityMetrics(
                cyclomatic_complexity=complexity_data.get('average', 0.0),
                maintainability_index=80.0  # Default reasonable value
            )
        
        # Add metadata
        analysis_result.metadata = cached_data.get('metadata', {})
        
        return analysis_result
    
    def _merge_code_analysis(self, analysis_result: AnalysisResult, code_analysis: Dict[str, Any]):
        """Merge code analysis results into the main analysis result."""
        # Extract results from the analyzer response
        results = code_analysis.get('results', {})
        
        # Update overview statistics
        analysis_result.total_functions = results.get('total_functions', 0)
        analysis_result.total_classes = results.get('total_classes', 0)
        analysis_result.total_files = results.get('total_modules', 0)  # modules are essentially files
        analysis_result.languages_detected = ['python']  # AST analyzer is Python-specific
        analysis_result.project_type = 'python'
        
        # Add modules
        modules_data = results.get('modules', [])
        for module_data in modules_data:
            # Module data from AST analyzer is always a dict (from __dict__)
            # but may contain complex objects that need special handling
            if isinstance(module_data, dict):
                # Check if metrics is already a CodeMetrics object
                if 'metrics' in module_data and hasattr(module_data['metrics'], 'total_lines'):
                    # Create ModuleAnalysis directly from the dict with object metrics
                    analysis_result.modules.append(ModuleAnalysis(**module_data))
                else:
                    # Convert dict to ModuleAnalysis using the helper method
                    module_analysis = self._create_module_analysis(module_data)
                    analysis_result.modules.append(module_analysis)
            else:
                # It's already a ModuleAnalysis object
                analysis_result.modules.append(module_data)
        
        # Add dependency information
        analysis_result.dependency_graph = code_analysis.get('dependencies', {})
        analysis_result.circular_dependencies = code_analysis.get('circular_dependencies', [])
        
        # Add complexity information
        complexity_data = code_analysis.get('complexity', {})
        if complexity_data:
            analysis_result.overall_complexity = ComplexityMetrics(
                cyclomatic_complexity=complexity_data.get('avg_complexity', 0.0),
                maintainability_index=complexity_data.get('maintainability_index', 0.0)
            )
    
    def _merge_ai_analysis(self, analysis_result: AnalysisResult, ai_analysis: Dict[str, Any]):
        """Merge AI analysis results into the main analysis result."""
        if ai_analysis and ai_analysis.get('results'):
            results = ai_analysis.get('results', {})
            analysis_result.metadata['ai_components'] = results
            
            # Update project type if AI frameworks detected
            frameworks = results.get('frameworks_detected', [])
            if analysis_result.project_type == 'python' and frameworks:
                analysis_result.project_type = 'ai_ml'
    
    def _create_module_analysis(self, module_data: Dict[str, Any]) -> ModuleAnalysis:
        """Create ModuleAnalysis from raw module data."""
        # Create metrics
        metrics_data = module_data.get('metrics', {})
        metrics = CodeMetrics(
            file_path=module_data.get('path', ''),
            total_lines=metrics_data.get('total_lines', 0),
            code_lines=metrics_data.get('code_lines', 0),
            comment_lines=metrics_data.get('comment_lines', 0),
            blank_lines=metrics_data.get('blank_lines', 0),
            function_count=metrics_data.get('function_count', 0),
            class_count=metrics_data.get('class_count', 0),
            import_count=metrics_data.get('import_count', 0),
            docstring_coverage=metrics_data.get('docstring_coverage', 0.0)
        )
        
        # Create complexity metrics
        complexity_data = module_data.get('complexity', {})
        complexity = ComplexityMetrics(
            cyclomatic_complexity=complexity_data.get('cyclomatic_complexity', 0.0),
            cognitive_complexity=complexity_data.get('cognitive_complexity', 0.0),
            maintainability_index=complexity_data.get('maintainability_index', 0.0)
        )
        
        return ModuleAnalysis(
            module_path=module_data.get('path', ''),
            module_name=module_data.get('name', ''),
            module_type=module_data.get('type', 'module'),
            description=module_data.get('description', ''),
            metrics=metrics,
            complexity=complexity,
            dependencies=module_data.get('dependencies', []),
            functions=module_data.get('functions', []),
            classes=module_data.get('classes', []),
            imports=module_data.get('imports', []),
            docstrings=module_data.get('docstrings', {}),
            issues=module_data.get('issues', [])
        )
    
    def _calculate_aggregate_metrics(self, analysis_result: AnalysisResult):
        """Calculate aggregate metrics from individual modules."""
        if not analysis_result.modules:
            return
        
        # Calculate overall metrics
        total_lines = sum(m.metrics.total_lines for m in analysis_result.modules)
        total_code_lines = sum(m.metrics.code_lines for m in analysis_result.modules)
        total_functions = sum(m.metrics.function_count for m in analysis_result.modules)
        total_classes = sum(m.metrics.class_count for m in analysis_result.modules)
        
        analysis_result.overall_metrics = CodeMetrics(
            file_path="<aggregate>",
            total_lines=total_lines,
            code_lines=total_code_lines,
            function_count=total_functions,
            class_count=total_classes
        )
        
        # Calculate overall complexity
        if analysis_result.modules:
            avg_cyclomatic = sum(m.complexity.cyclomatic_complexity for m in analysis_result.modules) / len(analysis_result.modules)
            avg_cognitive = sum(m.complexity.cognitive_complexity for m in analysis_result.modules) / len(analysis_result.modules)
            avg_maintainability = sum(m.complexity.maintainability_index for m in analysis_result.modules) / len(analysis_result.modules)
            
            analysis_result.overall_complexity = ComplexityMetrics(
                cyclomatic_complexity=avg_cyclomatic,
                cognitive_complexity=avg_cognitive,
                maintainability_index=avg_maintainability
            )
