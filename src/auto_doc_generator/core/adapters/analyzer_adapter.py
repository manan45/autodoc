"""
Analyzer adapter for coordinator integration.

This adapter provides a standardized interface for the coordinator
to interact with various analyzers in the system.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from ...analyzers.code.ast_analyzer import ASTAnalyzer
from ...analyzers.ai.framework_detector import FrameworkDetector
from ...analyzers.ai.model_analyzer import ModelAnalyzer
from ...analyzers.ai.pipeline_analyzer import PipelineAnalyzer
from ...analyzers.quality.metrics_analyzer import MetricsAnalyzer
from ...analyzers.quality.llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)


class AnalyzerAdapter:
    """
    Adapter that provides a unified interface for all analyzers.
    
    This adapter allows the coordinator to interact with different
    analyzers through a consistent async interface.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize analyzer adapter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize analyzers
        self._initialize_analyzers()
    
    def _initialize_analyzers(self):
        """Initialize all available analyzers."""
        try:
            # Code analyzers
            self.ast_analyzer = ASTAnalyzer(self.config)
            
            # AI analyzers
            self.framework_detector = FrameworkDetector(self.config)
            self.model_analyzer = ModelAnalyzer(self.config)
            self.pipeline_analyzer = PipelineAnalyzer(self.config)
            
            # Quality analyzers
            self.metrics_analyzer = MetricsAnalyzer(self.config)
            self.llm_analyzer = LLMAnalyzer(self.config)
            
            self.logger.info("All analyzers initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing analyzers: {e}")
    
    async def analyze_code_structure(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code structure using AST analyzer.
        
        Args:
            input_data: Input data containing repository_path
            
        Returns:
            Analysis results
        """
        try:
            start_time = time.time()
            repository_path = input_data.get('repository_path', '')
            
            if not repository_path:
                return {"success": False, "error": "Repository path not provided"}
            
            self.logger.info(f"Analyzing code structure for: {repository_path}")
            
            # Run AST analysis in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_ast_analysis,
                repository_path
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "analysis_type": "code_structure",
                "execution_time": execution_time,
                "data": result,
                "metadata": {
                    "analyzer": "ast_analyzer",
                    "repository_path": repository_path
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in code structure analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_ast_analysis(self, repository_path: str) -> Dict[str, Any]:
        """Run AST analysis synchronously."""
        try:
            # Get files to analyze
            repo_path = Path(repository_path)
            python_files = list(repo_path.rglob("*.py"))
            
            results = {
                "total_files": len(python_files),
                "analyzed_files": 0,
                "total_functions": 0,
                "total_classes": 0,
                "files": {},
                "summary": {}
            }
            
            for file_path in python_files[:50]:  # Limit to first 50 files for performance
                try:
                    file_analysis = self.ast_analyzer.analyze_single_file(file_path)
                    if file_analysis:
                        relative_path = str(file_path.relative_to(repo_path))
                        results["files"][relative_path] = file_analysis.__dict__
                        results["analyzed_files"] += 1
                        results["total_functions"] += len(file_analysis.functions)
                        results["total_classes"] += len(file_analysis.classes)
                except Exception as e:
                    self.logger.warning(f"Failed to analyze {file_path}: {e}")
            
            # Generate summary
            results["summary"] = {
                "analysis_coverage": results["analyzed_files"] / results["total_files"] if results["total_files"] > 0 else 0,
                "avg_functions_per_file": results["total_functions"] / results["analyzed_files"] if results["analyzed_files"] > 0 else 0,
                "avg_classes_per_file": results["total_classes"] / results["analyzed_files"] if results["analyzed_files"] > 0 else 0
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in AST analysis: {e}")
            return {"error": str(e)}
    
    async def analyze_ai_components(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze AI/ML components in the repository.
        
        Args:
            input_data: Input data containing repository_path
            
        Returns:
            AI analysis results
        """
        try:
            start_time = time.time()
            repository_path = input_data.get('repository_path', '')
            
            if not repository_path:
                return {"success": False, "error": "Repository path not provided"}
            
            self.logger.info(f"Analyzing AI components for: {repository_path}")
            
            # Run AI analyses in parallel
            loop = asyncio.get_event_loop()
            
            # Create tasks for parallel execution
            framework_task = loop.run_in_executor(None, self._run_framework_detection, repository_path)
            model_task = loop.run_in_executor(None, self._run_model_analysis, repository_path)
            pipeline_task = loop.run_in_executor(None, self._run_pipeline_analysis, repository_path)
            
            # Wait for all tasks to complete
            framework_result, model_result, pipeline_result = await asyncio.gather(
                framework_task, model_task, pipeline_task, return_exceptions=True
            )
            
            execution_time = time.time() - start_time
            
            # Combine results
            combined_result = {
                "frameworks": framework_result if not isinstance(framework_result, Exception) else {"error": str(framework_result)},
                "models": model_result if not isinstance(model_result, Exception) else {"error": str(model_result)},
                "pipelines": pipeline_result if not isinstance(pipeline_result, Exception) else {"error": str(pipeline_result)}
            }
            
            return {
                "success": True,
                "analysis_type": "ai_components",
                "execution_time": execution_time,
                "data": combined_result,
                "metadata": {
                    "analyzers": ["framework_detector", "model_analyzer", "pipeline_analyzer"],
                    "repository_path": repository_path
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in AI component analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_framework_detection(self, repository_path: str) -> Dict[str, Any]:
        """Run framework detection synchronously."""
        try:
            return self.framework_detector.analyze(Path(repository_path))
        except Exception as e:
            return {"error": str(e)}
    
    def _run_model_analysis(self, repository_path: str) -> Dict[str, Any]:
        """Run model analysis synchronously."""
        try:
            return self.model_analyzer.analyze(Path(repository_path))
        except Exception as e:
            return {"error": str(e)}
    
    def _run_pipeline_analysis(self, repository_path: str) -> Dict[str, Any]:
        """Run pipeline analysis synchronously."""
        try:
            return self.pipeline_analyzer.analyze(Path(repository_path))
        except Exception as e:
            return {"error": str(e)}
    
    async def analyze_quality_metrics(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze code quality metrics.
        
        Args:
            input_data: Input data containing repository_path
            
        Returns:
            Quality analysis results
        """
        try:
            start_time = time.time()
            repository_path = input_data.get('repository_path', '')
            
            if not repository_path:
                return {"success": False, "error": "Repository path not provided"}
            
            self.logger.info(f"Analyzing quality metrics for: {repository_path}")
            
            # Run quality analyses in parallel
            loop = asyncio.get_event_loop()
            
            metrics_task = loop.run_in_executor(None, self._run_metrics_analysis, repository_path)
            llm_task = loop.run_in_executor(None, self._run_llm_analysis, repository_path)
            
            metrics_result, llm_result = await asyncio.gather(
                metrics_task, llm_task, return_exceptions=True
            )
            
            execution_time = time.time() - start_time
            
            # Combine results
            combined_result = {
                "metrics": metrics_result if not isinstance(metrics_result, Exception) else {"error": str(metrics_result)},
                "llm_insights": llm_result if not isinstance(llm_result, Exception) else {"error": str(llm_result)}
            }
            
            return {
                "success": True,
                "analysis_type": "quality_metrics",
                "execution_time": execution_time,
                "data": combined_result,
                "metadata": {
                    "analyzers": ["metrics_analyzer", "llm_analyzer"],
                    "repository_path": repository_path
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in quality metrics analysis: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_metrics_analysis(self, repository_path: str) -> Dict[str, Any]:
        """Run metrics analysis synchronously."""
        try:
            return self.metrics_analyzer.analyze(Path(repository_path))
        except Exception as e:
            return {"error": str(e)}
    
    def _run_llm_analysis(self, repository_path: str) -> Dict[str, Any]:
        """Run LLM analysis synchronously."""
        try:
            return self.llm_analyzer.analyze(Path(repository_path))
        except Exception as e:
            return {"error": str(e)}
    
    async def get_analysis_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a comprehensive analysis summary.
        
        Args:
            input_data: Input data containing repository_path
            
        Returns:
            Comprehensive analysis summary
        """
        try:
            repository_path = input_data.get('repository_path', '')
            
            # Run all analyses
            code_analysis = await self.analyze_code_structure(input_data)
            ai_analysis = await self.analyze_ai_components(input_data)
            quality_analysis = await self.analyze_quality_metrics(input_data)
            
            # Combine into summary
            summary = {
                "repository_path": repository_path,
                "analysis_timestamp": time.time(),
                "code_structure": code_analysis.get("data", {}),
                "ai_components": ai_analysis.get("data", {}),
                "quality_metrics": quality_analysis.get("data", {}),
                "execution_times": {
                    "code_analysis": code_analysis.get("execution_time", 0),
                    "ai_analysis": ai_analysis.get("execution_time", 0),
                    "quality_analysis": quality_analysis.get("execution_time", 0)
                },
                "success_status": {
                    "code_analysis": code_analysis.get("success", False),
                    "ai_analysis": ai_analysis.get("success", False),
                    "quality_analysis": quality_analysis.get("success", False)
                }
            }
            
            return {
                "success": True,
                "analysis_type": "comprehensive_summary",
                "data": summary,
                "metadata": {
                    "total_execution_time": sum(summary["execution_times"].values()),
                    "analyses_completed": sum(summary["success_status"].values()),
                    "analyses_total": len(summary["success_status"])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating analysis summary: {e}")
            return {"success": False, "error": str(e)}
