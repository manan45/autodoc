"""
Code quality metrics analysis.

This module calculates various code quality metrics including
maintainability, readability, and best practices adherence.
"""

import ast
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import math

from ..base.base_analyzer import BaseAnalyzer


class MetricsAnalyzer(BaseAnalyzer):
    """
    Analyzer that calculates comprehensive code quality metrics.
    """
    
    def analyze(self, target: Path) -> Dict[str, Any]:
        """
        Analyze quality metrics for Python files.
        
        Args:
            target: Directory or file path to analyze
            
        Returns:
            Dictionary containing quality metrics analysis results
        """
        self.log_analysis_start(str(target))
        
        result = self.create_result_template()
        result['timestamp'] = datetime.now().isoformat()
        
        if target.is_file():
            files = [target]
        else:
            files = self.find_python_files(target)
        
        module_assessments = {}
        overall_metrics = {
            'total_lines': 0,
            'total_functions': 0,
            'total_classes': 0,
            'total_issues': 0
        }
        
        for file_path in files:
            try:
                assessment = self.analyze_file_quality(file_path)
                if assessment:
                    relative_path = str(file_path.relative_to(target if target.is_dir() else target.parent))
                    module_assessments[relative_path] = assessment
                    
                    # Update overall metrics
                    overall_metrics['total_lines'] += assessment['metrics'].get('lines_of_code', 0)
                    overall_metrics['total_functions'] += assessment['metrics'].get('function_count', 0)
                    overall_metrics['total_classes'] += assessment['metrics'].get('class_count', 0)
                    overall_metrics['total_issues'] += len(assessment.get('issues', []))
                    
            except Exception as e:
                result['errors'].append(f"Failed to analyze quality for {file_path}: {str(e)}")
        
        # Calculate aggregate metrics
        quality_scores = [assessment['overall_score'] for assessment in module_assessments.values()]
        
        overview = {
            'total_modules': len(module_assessments),
            'average_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'median_quality_score': sorted(quality_scores)[len(quality_scores)//2] if quality_scores else 0,
            'min_quality_score': min(quality_scores) if quality_scores else 0,
            'max_quality_score': max(quality_scores) if quality_scores else 0
        }
        
        # Quality distribution
        quality_distribution = self.calculate_quality_distribution(quality_scores)
        
        result['results'] = {
            'module_assessments': module_assessments,
            'overview': overview,
            'quality_distribution': quality_distribution,
            'overall_metrics': overall_metrics,
            'metadata': {
                'total_modules_analyzed': len(module_assessments),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
        
        self.log_analysis_complete(str(target), len(module_assessments))
        return result
    
    def analyze_file_quality(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze quality metrics for a single Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with quality assessment or None if analysis failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Calculate various metrics
            metrics = self.calculate_metrics(tree, content)
            
            # Identify issues
            issues = self.identify_issues(tree, content)
            
            # Calculate overall score
            overall_score = self.calculate_overall_score(metrics, issues)
            
            return {
                'file_path': str(file_path),
                'metrics': metrics,
                'issues': issues,
                'overall_score': overall_score,
                'grade': self.score_to_grade(overall_score)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing quality for {file_path}: {e}")
            return None
    
    def calculate_metrics(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """
        Calculate various code quality metrics.
        
        Args:
            tree: AST tree
            content: File content
            
        Returns:
            Dictionary of calculated metrics
        """
        lines = content.splitlines()
        
        # Basic counts
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        # Complexity metrics
        total_complexity = sum(self.calculate_cyclomatic_complexity(func) for func in functions)
        avg_complexity = total_complexity / len(functions) if functions else 0
        
        # Documentation metrics
        documented_functions = sum(1 for func in functions if ast.get_docstring(func))
        documented_classes = sum(1 for cls in classes if ast.get_docstring(cls))
        
        doc_coverage = 0
        if functions or classes:
            doc_coverage = (documented_functions + documented_classes) / (len(functions) + len(classes))
        
        # Code style metrics
        long_lines = sum(1 for line in lines if len(line) > 100)
        empty_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        
        # Maintainability metrics
        avg_function_length = self.calculate_avg_function_length(functions, content)
        max_function_length = self.calculate_max_function_length(functions, content)
        
        # Import analysis
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        
        return {
            'lines_of_code': len(lines),
            'function_count': len(functions),
            'class_count': len(classes),
            'import_count': len(imports),
            'total_complexity': total_complexity,
            'avg_complexity': avg_complexity,
            'max_complexity': max(self.calculate_cyclomatic_complexity(func) for func in functions) if functions else 0,
            'documentation_coverage': doc_coverage,
            'documented_functions': documented_functions,
            'documented_classes': documented_classes,
            'long_lines_count': long_lines,
            'empty_lines_count': empty_lines,
            'comment_lines_count': comment_lines,
            'avg_function_length': avg_function_length,
            'max_function_length': max_function_length,
            'comment_ratio': comment_lines / len(lines) if lines else 0
        }
    
    def calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def calculate_avg_function_length(self, functions: List[ast.FunctionDef], content: str) -> float:
        """Calculate average function length in lines."""
        if not functions:
            return 0
        
        total_lines = 0
        for func in functions:
            # Estimate function length (this is approximate)
            func_lines = 1  # At least the def line
            for node in ast.walk(func):
                if hasattr(node, 'lineno'):
                    func_lines = max(func_lines, node.lineno - func.lineno + 1)
            total_lines += func_lines
        
        return total_lines / len(functions)
    
    def calculate_max_function_length(self, functions: List[ast.FunctionDef], content: str) -> int:
        """Calculate maximum function length in lines."""
        if not functions:
            return 0
        
        max_lines = 0
        for func in functions:
            func_lines = 1
            for node in ast.walk(func):
                if hasattr(node, 'lineno'):
                    func_lines = max(func_lines, node.lineno - func.lineno + 1)
            max_lines = max(max_lines, func_lines)
        
        return max_lines
    
    def identify_issues(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """
        Identify code quality issues.
        
        Args:
            tree: AST tree
            content: File content
            
        Returns:
            List of identified issues
        """
        issues = []
        lines = content.splitlines()
        
        # Check for long lines
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append({
                    'type': 'style',
                    'severity': 'minor',
                    'message': f'Line {i} exceeds 100 characters ({len(line)} chars)',
                    'line': i
                })
        
        # Check for missing docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    issues.append({
                        'type': 'documentation',
                        'severity': 'minor',
                        'message': f'{type(node).__name__} "{node.name}" missing docstring',
                        'line': node.lineno
                    })
        
        # Check for high complexity functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = self.calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    issues.append({
                        'type': 'complexity',
                        'severity': 'major' if complexity > 15 else 'minor',
                        'message': f'Function "{node.name}" has high complexity ({complexity})',
                        'line': node.lineno,
                        'complexity': complexity
                    })
        
        # Check for too many arguments
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                arg_count = len(node.args.args)
                if arg_count > 7:
                    issues.append({
                        'type': 'design',
                        'severity': 'minor',
                        'message': f'Function "{node.name}" has too many arguments ({arg_count})',
                        'line': node.lineno
                    })
        
        # Check for deep nesting
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                max_depth = self.calculate_nesting_depth(node)
                if max_depth > 4:
                    issues.append({
                        'type': 'complexity',
                        'severity': 'minor',
                        'message': f'Function "{node.name}" has deep nesting (depth {max_depth})',
                        'line': node.lineno
                    })
        
        return issues
    
    def calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth in a node."""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                child_depth = self.calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self.calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth
    
    def calculate_overall_score(self, metrics: Dict[str, Any], issues: List[Dict[str, Any]]) -> float:
        """
        Calculate overall quality score from metrics and issues.
        
        Args:
            metrics: Dictionary of metrics
            issues: List of issues
            
        Returns:
            Overall quality score (0-1)
        """
        score = 1.0
        
        # Penalize for complexity
        avg_complexity = metrics.get('avg_complexity', 0)
        if avg_complexity > 5:
            score -= min(0.3, (avg_complexity - 5) * 0.05)
        
        # Reward documentation
        doc_coverage = metrics.get('documentation_coverage', 0)
        score = score * (0.7 + 0.3 * doc_coverage)
        
        # Penalize for issues
        major_issues = sum(1 for issue in issues if issue.get('severity') == 'major')
        minor_issues = sum(1 for issue in issues if issue.get('severity') == 'minor')
        
        score -= major_issues * 0.1
        score -= minor_issues * 0.02
        
        # Penalize for long functions
        max_func_length = metrics.get('max_function_length', 0)
        if max_func_length > 50:
            score -= min(0.2, (max_func_length - 50) * 0.002)
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def calculate_quality_distribution(self, scores: List[float]) -> Dict[str, Any]:
        """Calculate distribution of quality scores."""
        if not scores:
            return {}
        
        ranges = {
            'excellent': sum(1 for s in scores if s >= 0.9),
            'good': sum(1 for s in scores if 0.8 <= s < 0.9),
            'fair': sum(1 for s in scores if 0.7 <= s < 0.8),
            'poor': sum(1 for s in scores if 0.6 <= s < 0.7),
            'critical': sum(1 for s in scores if s < 0.6)
        }
        
        return {
            'quality_ranges': ranges,
            'distribution_percentages': {
                k: (v / len(scores)) * 100 for k, v in ranges.items()
            }
        }
