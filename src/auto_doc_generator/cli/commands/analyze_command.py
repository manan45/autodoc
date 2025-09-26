"""
Analyze command implementation.

This module implements the analyze command for the CLI.
"""

import argparse
from typing import Dict, Any
from pathlib import Path

from ...core.services.analysis_service import AnalysisService
from ..utils.output_formatter import OutputFormatter


class AnalyzeCommand:
    """Command for analyzing codebases."""
    
    def __init__(self, analysis_service: AnalysisService, output_formatter: OutputFormatter):
        """
        Initialize analyze command.
        
        Args:
            analysis_service: Service for performing analysis
            output_formatter: Formatter for CLI output
        """
        self.analysis_service = analysis_service
        self.formatter = output_formatter
    
    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Execute the analyze command.
        
        Args:
            args: Command line arguments
            
        Returns:
            Dictionary with execution results
        """
        try:
            repo_path = Path(args.repo).resolve()
            
            self.formatter.print_header("CODEBASE ANALYSIS")
            self.formatter.print_info(f"Repository: {repo_path}")
            
            # Perform analysis
            result = self.analysis_service.analyze_codebase(str(repo_path))
            
            # Display results
            self.formatter.print_analysis_summary(result.to_dict())
            
            return {
                'success': True,
                'analysis_result': result,
                'stats': {
                    'total_files': result.total_files,
                    'total_functions': result.total_functions,
                    'total_classes': result.total_classes,
                    'average_complexity': result.average_complexity,
                }
            }
            
        except Exception as e:
            self.formatter.print_error(f"Analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
