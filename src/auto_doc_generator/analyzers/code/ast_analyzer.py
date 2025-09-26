"""
AST-based code analysis.

This module provides AST-based analysis of Python code to extract
structural information like classes, functions, imports, etc.
"""

import ast
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from ..base.base_analyzer import BaseAnalyzer
from ...core.models.analysis_models import ModuleAnalysis, CodeMetrics


class ASTAnalyzer(BaseAnalyzer):
    """
    Analyzer that uses Python's AST to extract code structure information.
    """
    
    def analyze(self, target: Path) -> Dict[str, Any]:
        """
        Analyze Python files using AST parsing.
        
        Args:
            target: Directory path to analyze
            
        Returns:
            Dictionary containing AST analysis results
        """
        self.log_analysis_start(str(target))
        
        result = self.create_result_template()
        result['timestamp'] = datetime.now().isoformat()
        
        if target.is_file():
            modules = [self.analyze_single_file(target)]
        else:
            python_files = self.find_python_files(target)
            modules = []
            
            for file_path in python_files:
                try:
                    module_analysis = self.analyze_single_file(file_path)
                    if module_analysis:
                        modules.append(module_analysis)
                except Exception as e:
                    result['errors'].append(f"Failed to analyze {file_path}: {str(e)}")
        
        result['results'] = {
            'modules': [m.__dict__ if hasattr(m, '__dict__') else m for m in modules],
            'total_modules': len(modules),
            'total_functions': sum(len(m.functions) for m in modules if hasattr(m, 'functions')),
            'total_classes': sum(len(m.classes) for m in modules if hasattr(m, 'classes')),
        }
        
        self.log_analysis_complete(str(target), len(modules))
        return result
    
    def analyze_file(self, file_path: Path) -> Optional[ModuleAnalysis]:
        """
        Analyze a single Python file using AST.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            ModuleAnalysis object or None if analysis failed
        """
        return self.analyze_single_file(file_path)
    
    def analyze_single_file(self, file_path: Path) -> Optional[ModuleAnalysis]:
        """
        Analyze a single Python file using AST.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            ModuleAnalysis object or None if analysis failed
        """
        try:
            content = self.read_file_safe(file_path)
            if not content:
                return None
            
            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError as e:
                self.logger.warning(f"Syntax error in {file_path}: {e}")
                return None
            
            # Extract information
            module_info = self._extract_module_info(tree, file_path, content)
            
            # Create metrics
            metrics = self._calculate_metrics(content, module_info)
            
            # Create ModuleAnalysis
            return ModuleAnalysis(
                module_path=str(file_path),
                module_name=file_path.stem,
                module_type=self._infer_module_type(file_path, content),
                description=module_info.get('docstring', ''),
                metrics=metrics,
                functions=module_info.get('functions', []),
                classes=module_info.get('classes', []),
                imports=module_info.get('imports', []),
                docstrings=module_info.get('docstrings', {}),
                dependencies=module_info.get('dependencies', [])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze {file_path}: {e}")
            return None
    
    def _extract_module_info(self, tree: ast.AST, file_path: Path, content: str) -> Dict[str, Any]:
        """Extract information from AST tree."""
        info = {
            'functions': [],
            'classes': [],
            'imports': [],
            'dependencies': [],
            'docstrings': {},
            'docstring': ''
        }
        
        # Extract module docstring
        if (tree.body and isinstance(tree.body[0], ast.Expr) 
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
            info['docstring'] = tree.body[0].value.value.strip()
        
        # Walk the AST
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._extract_function_info(node)
                info['functions'].append(func_info)
                
                # Store docstring if exists
                docstring = ast.get_docstring(node)
                if docstring:
                    info['docstrings'][node.name] = docstring
            
            elif isinstance(node, ast.ClassDef):
                class_info = self._extract_class_info(node)
                info['classes'].append(class_info)
                
                # Store docstring if exists
                docstring = ast.get_docstring(node)
                if docstring:
                    info['docstrings'][node.name] = docstring
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._extract_import_info(node)
                info['imports'].extend(import_info)
        
        # Extract dependencies from imports
        info['dependencies'] = list(set(
            imp.split('.')[0] for imp in info['imports'] 
            if not imp.startswith('.')
        ))
        
        return info
    
    def _extract_function_info(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Extract function information from AST node."""
        return {
            'name': node.name,
            'line': node.lineno,
            'end_line': getattr(node, 'end_lineno', node.lineno),
            'args': [arg.arg for arg in node.args.args],
            'arg_count': len(node.args.args),
            'docstring': ast.get_docstring(node),
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'is_method': False,  # Will be determined by context
            'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list],
            'returns': self._get_annotation_name(node.returns) if node.returns else None,
        }
    
    def _extract_class_info(self, node: ast.ClassDef) -> Dict[str, Any]:
        """Extract class information from AST node."""
        methods = []
        properties = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = self._extract_function_info(item)
                method_info['is_method'] = True
                
                # Classify method type
                if item.name.startswith('__') and item.name.endswith('__'):
                    method_info['method_type'] = 'magic'
                elif item.name.startswith('_'):
                    method_info['method_type'] = 'private'
                elif any(dec.id == 'property' if hasattr(dec, 'id') else False 
                        for dec in item.decorator_list):
                    method_info['method_type'] = 'property'
                    properties.append(method_info)
                    continue
                else:
                    method_info['method_type'] = 'public'
                
                methods.append(method_info)
        
        return {
            'name': node.name,
            'line': node.lineno,
            'end_line': getattr(node, 'end_lineno', node.lineno),
            'docstring': ast.get_docstring(node),
            'methods': methods,
            'properties': properties,
            'method_count': len(methods),
            'property_count': len(properties),
            'bases': [self._get_name(base) for base in node.bases],
            'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list],
        }
    
    def _extract_import_info(self, node: ast.AST) -> List[str]:
        """Extract import information from AST node."""
        imports = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                if module:
                    imports.append(f"{module}.{alias.name}")
                else:
                    imports.append(alias.name)
        
        return imports
    
    def _calculate_metrics(self, content: str, module_info: Dict[str, Any]) -> CodeMetrics:
        """Calculate code metrics for the module."""
        lines = content.splitlines()
        
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        code_lines = total_lines - blank_lines - comment_lines
        
        function_count = len(module_info.get('functions', []))
        class_count = len(module_info.get('classes', []))
        import_count = len(module_info.get('imports', []))
        
        # Calculate docstring coverage
        total_items = function_count + class_count + (1 if module_info.get('docstring') else 0)
        documented_items = len(module_info.get('docstrings', {})) + (1 if module_info.get('docstring') else 0)
        docstring_coverage = documented_items / total_items if total_items > 0 else 0.0
        
        return CodeMetrics(
            file_path=module_info.get('file_path', ''),
            total_lines=total_lines,
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
            function_count=function_count,
            class_count=class_count,
            import_count=import_count,
            docstring_coverage=docstring_coverage
        )
    
    def _infer_module_type(self, file_path: Path, content: str) -> str:
        """Infer the type of module based on path and content."""
        path_str = str(file_path).lower()
        content_lower = content.lower()
        
        if 'test' in path_str or 'spec' in path_str:
            return 'test'
        elif '__init__.py' in str(file_path):
            return 'package'
        elif 'main.py' in str(file_path) or 'app.py' in str(file_path):
            return 'entry_point'
        elif any(term in content_lower for term in ['flask', 'fastapi', 'django']):
            return 'api'
        elif any(term in content_lower for term in ['tensorflow', 'torch', 'sklearn']):
            return 'ai'
        elif 'util' in path_str or 'helper' in path_str:
            return 'utility'
        elif 'service' in path_str or 'manager' in path_str:
            return 'service'
        elif 'config' in path_str or 'setting' in path_str:
            return 'config'
        else:
            return 'module'
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name from AST node."""
        if hasattr(decorator, 'id'):
            return decorator.id
        elif hasattr(decorator, 'attr'):
            return decorator.attr
        else:
            return str(decorator)
    
    def _get_annotation_name(self, annotation: ast.AST) -> str:
        """Get type annotation name from AST node."""
        if hasattr(annotation, 'id'):
            return annotation.id
        elif hasattr(annotation, 'attr'):
            return annotation.attr
        else:
            return str(annotation)
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if hasattr(node, 'id'):
            return node.id
        elif hasattr(node, 'attr'):
            return node.attr
        else:
            return str(node)
