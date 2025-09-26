"""
Quality analysis service.

This service orchestrates quality analysis operations,
coordinating between different quality analyzers and managing quality metrics.
"""

from typing import Dict, List, Any, Optional
import logging

from ..repositories.file_repository import FileRepository
from ..repositories.cache_repository import CacheRepository
from ...analyzers.quality.metrics_analyzer import MetricsAnalyzer
from ...analyzers.quality.llm_analyzer import LLMAnalyzer


class QualityService:
    """
    Service that orchestrates quality analysis operations.
    
    This service coordinates between different quality analyzers to provide
    comprehensive code quality assessment.
    """
    
    def __init__(self, file_repository: FileRepository, 
                 cache_repository: CacheRepository, config: Dict[str, Any]):
        """
        Initialize quality service.
        
        Args:
            file_repository: File operations repository
            cache_repository: Caching repository
            config: Configuration dictionary
        """
        self.file_repository = file_repository
        self.cache_repository = cache_repository
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize quality analyzers
        self.metrics_analyzer = MetricsAnalyzer(config)
        self.llm_analyzer = LLMAnalyzer(config)
        
        self.logger.info("Quality service initialized")
    
    def analyze_quality(self, target_path: str, code_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform comprehensive quality analysis.
        
        Args:
            target_path: Path to analyze
            code_analysis: Optional code analysis results to enhance quality analysis
            
        Returns:
            Combined quality analysis results
        """
        self.logger.info(f"Starting quality analysis for: {target_path}")
        
        try:
            from pathlib import Path
            target = Path(target_path)
            
            # Run metrics-based quality analysis
            metrics_result = self.metrics_analyzer.analyze(target)
            
            # Run LLM-enhanced quality analysis if enabled
            llm_result = self.llm_analyzer.analyze(target)
            
            # Combine results
            combined_result = self._combine_quality_results(metrics_result, llm_result, code_analysis)
            
            # Cache results
            cache_key = f"quality_analysis_{target_path}"
            self.cache_repository.set(cache_key, combined_result)
            
            self.logger.info("Quality analysis completed successfully")
            return combined_result
            
        except Exception as e:
            self.logger.error(f"Quality analysis failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'results': {},
                'timestamp': self._get_timestamp()
            }
    
    def _combine_quality_results(self, metrics_result: Dict[str, Any], 
                                llm_result: Dict[str, Any], 
                                code_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Combine results from different quality analyzers.
        
        Args:
            metrics_result: Results from metrics analyzer
            llm_result: Results from LLM analyzer
            code_analysis: Optional code analysis for context
            
        Returns:
            Combined quality analysis results
        """
        combined = {
            'success': True,
            'timestamp': self._get_timestamp(),
            'analyzers_used': [],
            'results': {}
        }
        
        # Include metrics analysis
        if metrics_result.get('success', True) and metrics_result.get('results'):
            combined['results'].update(metrics_result['results'])
            combined['analyzers_used'].append('metrics')
        
        # Include LLM analysis if available
        if llm_result.get('success', True) and llm_result.get('results'):
            llm_data = llm_result['results']
            
            # Merge LLM assessments with metrics assessments
            if 'assessments' in llm_data and 'module_assessments' in combined['results']:
                for module_path, llm_assessment in llm_data['assessments'].items():
                    if module_path in combined['results']['module_assessments']:
                        combined['results']['module_assessments'][module_path]['llm_assessment'] = llm_assessment
            
            # Add global LLM insights
            if 'global_insights' in llm_data:
                combined['results']['llm_insights'] = llm_data['global_insights']
            
            combined['analyzers_used'].append('llm')
        
        # Enhance with code analysis context if provided
        if code_analysis:
            combined['results']['code_context'] = {
                'total_files': code_analysis.get('overview', {}).get('total_files', 0),
                'total_functions': code_analysis.get('overview', {}).get('total_functions', 0),
                'total_classes': code_analysis.get('overview', {}).get('total_classes', 0),
                'project_type': code_analysis.get('overview', {}).get('project_type', 'unknown')
            }
        
        # Calculate enhanced metrics
        combined['results'] = self._calculate_enhanced_metrics(combined['results'])
        
        return combined
    
    def _calculate_enhanced_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate enhanced quality metrics from combined results.
        
        Args:
            results: Combined analysis results
            
        Returns:
            Results with enhanced metrics
        """
        try:
            module_assessments = results.get('module_assessments', {})
            
            if not module_assessments:
                return results
            
            # Calculate enhanced overview statistics
            scores = [assessment.get('overall_score', 0) for assessment in module_assessments.values()]
            
            if scores:
                enhanced_overview = {
                    'total_modules': len(scores),
                    'average_quality_score': sum(scores) / len(scores),
                    'median_quality_score': sorted(scores)[len(scores)//2],
                    'min_quality_score': min(scores),
                    'max_quality_score': max(scores),
                    'standard_deviation': self._calculate_std_dev(scores)
                }
                
                # Update or create overview
                if 'overview' in results:
                    results['overview'].update(enhanced_overview)
                else:
                    results['overview'] = enhanced_overview
                
                # Enhanced quality distribution
                enhanced_distribution = self._calculate_enhanced_distribution(scores)
                results['quality_distribution'] = enhanced_distribution
            
        except Exception as e:
            self.logger.error(f"Enhanced metrics calculation failed: {e}")
        
        return results
    
    def _calculate_std_dev(self, scores: List[float]) -> float:
        """Calculate standard deviation of quality scores."""
        if not scores:
            return 0.0
        
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance ** 0.5
    
    def _calculate_enhanced_distribution(self, scores: List[float]) -> Dict[str, Any]:
        """Calculate enhanced quality distribution metrics."""
        if not scores:
            return {}
        
        # Quality ranges
        ranges = {
            'excellent': sum(1 for s in scores if s >= 0.9),
            'good': sum(1 for s in scores if 0.8 <= s < 0.9),
            'fair': sum(1 for s in scores if 0.7 <= s < 0.8),
            'poor': sum(1 for s in scores if 0.6 <= s < 0.7),
            'critical': sum(1 for s in scores if s < 0.6)
        }
        
        total = len(scores)
        percentages = {k: (v / total) * 100 for k, v in ranges.items()}
        
        return {
            'quality_ranges': ranges,
            'distribution_percentages': percentages,
            'total_modules': total
        }
    
    def get_quality_summary(self, target_path: str) -> Dict[str, Any]:
        """
        Get a quick quality summary for a target.
        
        Args:
            target_path: Path to analyze
            
        Returns:
            Quality summary
        """
        # Check cache first
        cache_key = f"quality_summary_{target_path}"
        cached = self.cache_repository.get(cache_key)
        if cached:
            return cached
        
        try:
            # Run quick analysis
            from pathlib import Path
            target = Path(target_path)
            
            # Use metrics analyzer for quick summary
            result = self.metrics_analyzer.analyze(target)
            
            if result.get('success', True) and result.get('results'):
                overview = result['results'].get('overview', {})
                summary = {
                    'average_score': overview.get('average_quality_score', 0),
                    'total_modules': overview.get('total_modules', 0),
                    'timestamp': self._get_timestamp(),
                    'quick_analysis': True
                }
                
                # Cache summary
                self.cache_repository.set(cache_key, summary, ttl=3600)  # 1 hour cache
                return summary
            
        except Exception as e:
            self.logger.error(f"Quality summary failed: {e}")
        
        return {
            'average_score': 0,
            'total_modules': 0,
            'error': 'Summary generation failed',
            'timestamp': self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
