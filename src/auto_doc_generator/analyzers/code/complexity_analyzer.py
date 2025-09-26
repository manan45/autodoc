"""
Complexity analysis for Python code.

This module provides complexity metrics calculation for Python code
using various algorithms and heuristics.
"""

import ast
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from ..base.base_analyzer import BaseAnalyzer
from ...core.models.analysis_models import ComplexityMetrics


class ComplexityAnalyzer(BaseAnalyzer):
    """
    Analyzer that calculates complexity metrics for Python code.
    """
    
    def analyze(self, target: Path) -> Dict[str, Any]:
        """
        Analyze complexity metrics for Python files.
        
        Args:
            target: Directory or file path to analyze
            
        Returns:
            Dictionary containing complexity analysis results
        """
        self.log_analysis_start(str(target))
        
        result = self.create_result_template()
        result['timestamp'] = datetime.now().isoformat()
        
        if target.is_file():
            files = [target]
        else:
            files = self.find_python_files(target)
        
        complexity_results = []
        total_complexity = 0
        max_complexity = 0
        high_complexity_functions = []
        
        for file_path in files:
            try:
                file_complexity = self.analyze_file_complexity(file_path)
                if file_complexity:
                    complexity_results.append(file_complexity)
                    total_complexity += file_complexity.get('total_complexity', 0)
                    file_max = file_complexity.get('max_complexity', 0)
                    if file_max > max_complexity:
                        max_complexity = file_max
                    
                    # Collect high complexity functions
                    for func in file_complexity.get('functions', []):
                        if func.get('complexity', 0) > 10:  # Threshold for high complexity
                            high_complexity_functions.append({
                                'file': str(file_path),
                                'function': func['name'],
                                'complexity': func['complexity']
                            })
                            
            except Exception as e:
                result['errors'].append(f"Failed to analyze complexity for {file_path}: {str(e)}")
        
        result['results'] = {
            'files': complexity_results,
            'summary': {
                'total_files': len(complexity_results),
                'total_complexity': total_complexity,
                'avg_complexity': total_complexity / len(complexity_results) if complexity_results else 0,
                'max_complexity': max_complexity,
                'high_complexity_functions': high_complexity_functions
            }
        }
        
        self.log_analysis_complete(str(target), len(complexity_results))
        return result
    
    def analyze_file_complexity(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze complexity for a single Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with complexity metrics or None if analysis failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self.calculate_cyclomatic_complexity(node)
                    functions.append({
                        'name': node.name,
                        'line_start': node.lineno,
                        'complexity': complexity,
                        'args_count': len(node.args.args)
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    class_complexity = sum(
                        self.calculate_cyclomatic_complexity(method) for method in methods
                    )
                    classes.append({
                        'name': node.name,
                        'line_start': node.lineno,
                        'complexity': class_complexity,
                        'methods_count': len(methods)
                    })
            
            total_complexity = sum(f['complexity'] for f in functions)
            max_complexity = max([f['complexity'] for f in functions] + [0])
            
            return {
                'file_path': str(file_path.relative_to(Path.cwd())),
                'total_complexity': total_complexity,
                'max_complexity': max_complexity,
                'avg_complexity': total_complexity / len(functions) if functions else 0,
                'functions': functions,
                'classes': classes,
                'lines_of_code': len(content.splitlines())
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing complexity for {file_path}: {e}")
            return None
    
    def calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """
        Calculate cyclomatic complexity for a function.
        
        Args:
            node: AST function node
            
        Returns:
            Cyclomatic complexity score
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points that increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With, ast.AsyncWith):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # And/Or operations
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ListComp):
                # List comprehensions
                complexity += len(child.generators)
            elif isinstance(child, ast.DictComp):
                # Dict comprehensions
                complexity += len(child.generators)
            elif isinstance(child, ast.SetComp):
                # Set comprehensions
                complexity += len(child.generators)
            elif isinstance(child, ast.GeneratorExp):
                # Generator expressions
                complexity += len(child.generators)
        
        return complexity
