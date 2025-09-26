"""
Dependency analysis for Python code.

This module analyzes import dependencies and module relationships
within Python codebases.
"""

import ast
from typing import Dict, List, Any, Set, Optional
from pathlib import Path
from datetime import datetime
import networkx as nx

from ..base.base_analyzer import BaseAnalyzer


class DependencyAnalyzer(BaseAnalyzer):
    """
    Analyzer that extracts and analyzes import dependencies.
    """
    
    def analyze(self, target: Path) -> Dict[str, Any]:
        """
        Analyze dependencies for Python files.
        
        Args:
            target: Directory or file path to analyze
            
        Returns:
            Dictionary containing dependency analysis results
        """
        self.log_analysis_start(str(target))
        
        result = self.create_result_template()
        result['timestamp'] = datetime.now().isoformat()
        
        if target.is_file():
            files = [target]
        else:
            files = self.find_python_files(target)
        
        dependency_map = {}
        all_imports = set()
        external_dependencies = set()
        internal_dependencies = set()
        
        # First pass: collect all imports
        for file_path in files:
            try:
                file_imports = self.extract_imports(file_path)
                if file_imports:
                    relative_path = str(file_path.relative_to(target if target.is_dir() else target.parent))
                    dependency_map[relative_path] = file_imports
                    all_imports.update(file_imports['imports'])
                    external_dependencies.update(file_imports['external'])
                    internal_dependencies.update(file_imports['internal'])
                    
            except Exception as e:
                result['errors'].append(f"Failed to analyze dependencies for {file_path}: {str(e)}")
        
        # Second pass: build dependency graph
        dependency_graph = self.build_dependency_graph(dependency_map)
        
        # Analyze circular dependencies
        circular_deps = self.find_circular_dependencies(dependency_graph)
        
        # Calculate dependency metrics
        metrics = self.calculate_dependency_metrics(dependency_map, dependency_graph)
        
        result['results'] = {
            'dependency_map': dependency_map,
            'external_dependencies': sorted(list(external_dependencies)),
            'internal_dependencies': sorted(list(internal_dependencies)),
            'circular_dependencies': circular_deps,
            'dependency_graph': {
                'nodes': list(dependency_graph.nodes()),
                'edges': list(dependency_graph.edges())
            },
            'metrics': metrics,
            'summary': {
                'total_files': len(dependency_map),
                'total_imports': len(all_imports),
                'external_count': len(external_dependencies),
                'internal_count': len(internal_dependencies),
                'circular_count': len(circular_deps)
            }
        }
        
        self.log_analysis_complete(str(target), len(dependency_map))
        return result
    
    def extract_imports(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract imports from a single Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with import information or None if analysis failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            imports = []
            external = set()
            internal = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        imports.append({
                            'type': 'import',
                            'module': module_name,
                            'alias': alias.asname,
                            'line': node.lineno
                        })
                        
                        # Classify as external or internal
                        if self.is_external_module(module_name):
                            external.add(module_name)
                        else:
                            internal.add(module_name)
                
                elif isinstance(node, ast.ImportFrom):
                    module_name = node.module or ''
                    for alias in node.names:
                        imports.append({
                            'type': 'from_import',
                            'module': module_name,
                            'name': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno,
                            'level': node.level
                        })
                        
                        # Classify as external or internal
                        if self.is_external_module(module_name):
                            external.add(module_name)
                        else:
                            internal.add(module_name)
            
            return {
                'imports': imports,
                'external': external,
                'internal': internal,
                'total_imports': len(imports)
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting imports from {file_path}: {e}")
            return None
    
    def is_external_module(self, module_name: str) -> bool:
        """
        Determine if a module is external (third-party or standard library).
        
        Args:
            module_name: Name of the module
            
        Returns:
            True if external, False if internal
        """
        if not module_name:
            return False
            
        # Standard library modules (partial list)
        stdlib_modules = {
            'os', 'sys', 'json', 'yaml', 'ast', 'logging', 'datetime', 'pathlib',
            'typing', 'collections', 'itertools', 'functools', 'argparse',
            'subprocess', 'threading', 're', 'math', 'random', 'hashlib',
            'urllib', 'http', 'email', 'xml', 'csv', 'sqlite3'
        }
        
        # Third-party modules (common ones)
        thirdparty_modules = {
            'numpy', 'pandas', 'matplotlib', 'seaborn', 'sklearn', 'tensorflow',
            'torch', 'flask', 'django', 'requests', 'beautifulsoup4', 'lxml',
            'pytest', 'click', 'pydantic', 'fastapi', 'sqlalchemy'
        }
        
        root_module = module_name.split('.')[0]
        
        # Check if it's a standard library or known third-party module
        if root_module in stdlib_modules or root_module in thirdparty_modules:
            return True
        
        # If it starts with a dot, it's a relative import (internal)
        if module_name.startswith('.'):
            return False
        
        # Heuristic: if it contains underscores or is all lowercase, likely external
        # This is not foolproof but covers many cases
        if '_' in root_module or root_module.islower():
            return True
        
        return False
    
    def build_dependency_graph(self, dependency_map: Dict[str, Dict[str, Any]]) -> nx.DiGraph:
        """
        Build a directed graph of dependencies.
        
        Args:
            dependency_map: Map of files to their dependencies
            
        Returns:
            NetworkX directed graph
        """
        graph = nx.DiGraph()
        
        # Add nodes for all files
        for file_path in dependency_map.keys():
            graph.add_node(file_path)
        
        # Add edges for internal dependencies
        for file_path, deps in dependency_map.items():
            for dep in deps['internal']:
                # Try to match internal dependencies to actual files
                for other_file in dependency_map.keys():
                    if self.matches_dependency(other_file, dep):
                        graph.add_edge(file_path, other_file)
        
        return graph
    
    def matches_dependency(self, file_path: str, dependency: str) -> bool:
        """
        Check if a file path matches a dependency import.
        
        Args:
            file_path: Path to a file
            dependency: Import dependency name
            
        Returns:
            True if they match
        """
        # Simple matching logic - can be improved
        file_module = file_path.replace('/', '.').replace('.py', '')
        return dependency in file_module or file_module.endswith(dependency)
    
    def find_circular_dependencies(self, graph: nx.DiGraph) -> List[List[str]]:
        """
        Find circular dependencies in the dependency graph.
        
        Args:
            graph: Dependency graph
            
        Returns:
            List of circular dependency cycles
        """
        try:
            cycles = list(nx.simple_cycles(graph))
            return cycles
        except Exception:
            return []
    
    def calculate_dependency_metrics(self, dependency_map: Dict[str, Dict[str, Any]], 
                                   graph: nx.DiGraph) -> Dict[str, Any]:
        """
        Calculate various dependency metrics.
        
        Args:
            dependency_map: Map of files to dependencies
            graph: Dependency graph
            
        Returns:
            Dictionary of metrics
        """
        metrics = {
            'fan_in': {},  # How many modules depend on this one
            'fan_out': {},  # How many modules this one depends on
            'stability': {},  # Fan_out / (Fan_in + Fan_out)
            'coupling': {}  # Total dependencies
        }
        
        for node in graph.nodes():
            fan_in = graph.in_degree(node)
            fan_out = graph.out_degree(node)
            
            metrics['fan_in'][node] = fan_in
            metrics['fan_out'][node] = fan_out
            
            total_coupling = fan_in + fan_out
            metrics['stability'][node] = fan_out / total_coupling if total_coupling > 0 else 0
            metrics['coupling'][node] = total_coupling
        
        return metrics
