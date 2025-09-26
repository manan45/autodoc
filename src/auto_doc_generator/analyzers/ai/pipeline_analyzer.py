"""
AI/ML pipeline analysis.

This module analyzes AI/ML pipelines and workflows in Python codebases
to identify data processing, training, and deployment patterns.
"""

import ast
import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from datetime import datetime

from ..base.base_analyzer import BaseAnalyzer


class PipelineAnalyzer(BaseAnalyzer):
    """
    Analyzer that identifies and analyzes AI/ML pipelines and workflows.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Pipeline-related patterns
        self.pipeline_patterns = {
            'sklearn_pipeline': [
                r'Pipeline\(',
                r'make_pipeline\(',
                r'FeatureUnion\(',
                r'ColumnTransformer\('
            ],
            'data_processing': [
                r'pandas\.',
                r'pd\.',
                r'numpy\.',
                r'np\.',
                r'preprocessing\.',
                r'StandardScaler',
                r'MinMaxScaler',
                r'LabelEncoder',
                r'OneHotEncoder'
            ],
            'model_training': [
                r'train_test_split',
                r'cross_val_score',
                r'GridSearchCV',
                r'RandomizedSearchCV',
                r'fit\(',
                r'fit_transform\('
            ],
            'model_evaluation': [
                r'accuracy_score',
                r'precision_score',
                r'recall_score',
                r'f1_score',
                r'roc_auc_score',
                r'mean_squared_error',
                r'classification_report',
                r'confusion_matrix'
            ],
            'deep_learning': [
                r'DataLoader',
                r'Dataset',
                r'torch\.utils\.data',
                r'tf\.data',
                r'ImageDataGenerator',
                r'fit_generator'
            ],
            'mlops': [
                r'mlflow\.',
                r'wandb\.',
                r'tensorboard',
                r'joblib\.dump',
                r'pickle\.dump',
                r'model\.save',
                r'checkpoint'
            ]
        }
        
        # Workflow step patterns
        self.workflow_steps = [
            'data_loading',
            'data_preprocessing',
            'feature_engineering',
            'model_training',
            'model_evaluation',
            'model_deployment',
            'monitoring'
        ]
    
    def analyze(self, target: Path) -> Dict[str, Any]:
        """
        Analyze AI/ML pipelines in Python files.
        
        Args:
            target: Directory or file path to analyze
            
        Returns:
            Dictionary containing pipeline analysis results
        """
        self.log_analysis_start(str(target))
        
        result = self.create_result_template()
        result['timestamp'] = datetime.now().isoformat()
        
        if target.is_file():
            files = [target]
        else:
            files = self.find_python_files(target)
        
        pipelines = []
        workflow_files = []
        pipeline_types = set()
        
        for file_path in files:
            try:
                file_analysis = self.analyze_file_pipelines(file_path)
                if file_analysis:
                    if file_analysis['pipelines']:
                        pipelines.extend(file_analysis['pipelines'])
                    
                    pipeline_types.update(file_analysis['pipeline_types'])
                    
                    if file_analysis['is_workflow']:
                        workflow_files.append({
                            'file': str(file_path.relative_to(target if target.is_dir() else target.parent)),
                            'workflow_steps': file_analysis['workflow_steps'],
                            'complexity': file_analysis['complexity']
                        })
                        
            except Exception as e:
                result['errors'].append(f"Failed to analyze pipelines in {file_path}: {str(e)}")
        
        # Identify pipeline relationships
        pipeline_graph = self.build_pipeline_graph(pipelines, workflow_files)
        
        result['results'] = {
            'pipelines': pipelines,
            'workflow_files': workflow_files,
            'pipeline_types': sorted(list(pipeline_types)),
            'pipeline_graph': pipeline_graph,
            'summary': {
                'total_pipelines': len(pipelines),
                'workflow_files_count': len(workflow_files),
                'pipeline_types_count': len(pipeline_types)
            }
        }
        
        self.log_analysis_complete(str(target), len(pipelines))
        return result
    
    def analyze_file_pipelines(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze pipelines in a single Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with pipeline analysis or None if analysis failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Extract pipeline classes and functions
            pipelines = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    pipeline_info = self.analyze_pipeline_class(node, content)
                    if pipeline_info:
                        pipelines.append(pipeline_info)
                elif isinstance(node, ast.FunctionDef):
                    pipeline_info = self.analyze_pipeline_function(node, content)
                    if pipeline_info:
                        pipelines.append(pipeline_info)
            
            # Detect pipeline types
            pipeline_types = self.detect_pipeline_types(content)
            
            # Analyze workflow steps
            workflow_steps = self.identify_workflow_steps(content)
            is_workflow = len(workflow_steps) > 2  # Has multiple workflow steps
            
            # Calculate complexity
            complexity = self.calculate_pipeline_complexity(content, workflow_steps)
            
            return {
                'file_path': str(file_path),
                'pipelines': pipelines,
                'pipeline_types': pipeline_types,
                'workflow_steps': workflow_steps,
                'is_workflow': is_workflow,
                'complexity': complexity
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing pipelines in {file_path}: {e}")
            return None
    
    def analyze_pipeline_class(self, node: ast.ClassDef, content: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a class to determine if it's a pipeline.
        
        Args:
            node: AST class node
            content: File content
            
        Returns:
            Dictionary with pipeline information or None if not a pipeline
        """
        # Check if class name suggests it's a pipeline
        pipeline_indicators = [
            'Pipeline', 'Workflow', 'Processor', 'Trainer', 'Predictor',
            'ETL', 'DataPipeline', 'MLPipeline', 'ModelPipeline'
        ]
        
        is_pipeline = any(indicator in node.name for indicator in pipeline_indicators)
        
        if not is_pipeline:
            # Check methods for pipeline patterns
            methods = [item.name for item in node.body if isinstance(item, ast.FunctionDef)]
            pipeline_methods = ['fit', 'transform', 'predict', 'process', 'run', 'execute']
            is_pipeline = any(method in methods for method in pipeline_methods)
        
        if not is_pipeline:
            return None
        
        # Extract pipeline steps from methods
        steps = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                step_info = self.analyze_pipeline_step(item, content)
                if step_info:
                    steps.append(step_info)
        
        return {
            'type': 'class',
            'name': node.name,
            'line_start': node.lineno,
            'steps': steps,
            'docstring': ast.get_docstring(node)
        }
    
    def analyze_pipeline_function(self, node: ast.FunctionDef, content: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a function to determine if it's a pipeline.
        
        Args:
            node: AST function node
            content: File content
            
        Returns:
            Dictionary with pipeline information or None if not a pipeline
        """
        # Check function name for pipeline indicators
        pipeline_indicators = [
            'pipeline', 'workflow', 'process', 'train', 'predict',
            'etl', 'preprocess', 'postprocess', 'run_', 'execute_'
        ]
        
        is_pipeline = any(indicator in node.name.lower() for indicator in pipeline_indicators)
        
        if not is_pipeline:
            # Check if function contains multiple pipeline steps
            function_content = ast.get_source_segment(content, node) if hasattr(ast, 'get_source_segment') else ''
            if function_content:
                steps = self.identify_workflow_steps(function_content)
                is_pipeline = len(steps) > 2
        
        if not is_pipeline:
            return None
        
        # Analyze function body for pipeline steps
        steps = self.extract_function_steps(node, content)
        
        return {
            'type': 'function',
            'name': node.name,
            'line_start': node.lineno,
            'args': len(node.args.args),
            'steps': steps,
            'docstring': ast.get_docstring(node)
        }
    
    def analyze_pipeline_step(self, node: ast.FunctionDef, content: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a method as a potential pipeline step.
        
        Args:
            node: AST function node
            content: File content
            
        Returns:
            Dictionary with step information or None
        """
        step_types = {
            'load': ['load', 'read', 'fetch', 'get_data'],
            'preprocess': ['preprocess', 'clean', 'transform', 'normalize'],
            'feature': ['feature', 'extract', 'select', 'engineer'],
            'train': ['train', 'fit', 'learn'],
            'evaluate': ['evaluate', 'test', 'validate', 'score'],
            'predict': ['predict', 'infer', 'forecast'],
            'save': ['save', 'dump', 'store', 'persist']
        }
        
        step_type = 'unknown'
        for stype, keywords in step_types.items():
            if any(keyword in node.name.lower() for keyword in keywords):
                step_type = stype
                break
        
        return {
            'name': node.name,
            'type': step_type,
            'line': node.lineno,
            'args': len(node.args.args)
        }
    
    def extract_function_steps(self, node: ast.FunctionDef, content: str) -> List[Dict[str, Any]]:
        """
        Extract pipeline steps from a function body.
        
        Args:
            node: AST function node
            content: File content
            
        Returns:
            List of pipeline steps
        """
        steps = []
        
        # Simple heuristic: look for function calls that might be steps
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    func_name = child.func.id
                elif isinstance(child.func, ast.Attribute):
                    func_name = child.func.attr
                else:
                    continue
                
                # Check if this looks like a pipeline step
                step_indicators = [
                    'load', 'read', 'preprocess', 'transform', 'fit',
                    'predict', 'evaluate', 'save', 'dump'
                ]
                
                if any(indicator in func_name.lower() for indicator in step_indicators):
                    steps.append({
                        'name': func_name,
                        'line': child.lineno,
                        'type': 'function_call'
                    })
        
        return steps
    
    def detect_pipeline_types(self, content: str) -> Set[str]:
        """
        Detect types of pipelines from file content.
        
        Args:
            content: File content
            
        Returns:
            Set of detected pipeline types
        """
        types = set()
        
        for pipeline_type, patterns in self.pipeline_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    types.add(pipeline_type)
                    break
        
        return types
    
    def identify_workflow_steps(self, content: str) -> List[str]:
        """
        Identify workflow steps in content.
        
        Args:
            content: File content
            
        Returns:
            List of identified workflow steps
        """
        steps = []
        
        step_patterns = {
            'data_loading': [r'read_csv', r'load_data', r'pd\.read', r'np\.load'],
            'data_preprocessing': [r'preprocess', r'clean', r'fillna', r'dropna'],
            'feature_engineering': [r'feature', r'transform', r'fit_transform', r'StandardScaler'],
            'model_training': [r'\.fit\(', r'train', r'GridSearchCV', r'cross_val'],
            'model_evaluation': [r'score', r'evaluate', r'predict', r'accuracy'],
            'model_deployment': [r'save', r'dump', r'export', r'deploy'],
            'monitoring': [r'log', r'monitor', r'track', r'mlflow', r'wandb']
        }
        
        for step, patterns in step_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    steps.append(step)
                    break
        
        return steps
    
    def calculate_pipeline_complexity(self, content: str, workflow_steps: List[str]) -> str:
        """
        Calculate pipeline complexity.
        
        Args:
            content: File content
            workflow_steps: List of workflow steps
            
        Returns:
            Complexity level (low, medium, high)
        """
        complexity_score = 0
        
        # Base score from workflow steps
        complexity_score += len(workflow_steps) * 2
        
        # Additional complexity indicators
        if re.search(r'GridSearchCV|RandomizedSearchCV', content):
            complexity_score += 5
        
        if re.search(r'cross_val|KFold', content):
            complexity_score += 3
        
        if re.search(r'Pipeline|FeatureUnion', content):
            complexity_score += 3
        
        if re.search(r'mlflow|wandb|tensorboard', content):
            complexity_score += 2
        
        # Count number of imports (indicator of complexity)
        import_count = len(re.findall(r'^import |^from ', content, re.MULTILINE))
        complexity_score += import_count // 5
        
        if complexity_score >= 15:
            return 'high'
        elif complexity_score >= 8:
            return 'medium'
        else:
            return 'low'
    
    def build_pipeline_graph(self, pipelines: List[Dict[str, Any]], 
                           workflow_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build a graph representation of pipeline relationships.
        
        Args:
            pipelines: List of identified pipelines
            workflow_files: List of workflow files
            
        Returns:
            Dictionary representing pipeline graph
        """
        nodes = []
        edges = []
        
        # Add pipeline nodes
        for pipeline in pipelines:
            nodes.append({
                'id': f"{pipeline.get('name', 'unknown')}_{pipeline.get('line_start', 0)}",
                'name': pipeline.get('name', 'Unknown'),
                'type': pipeline.get('type', 'unknown'),
                'steps': len(pipeline.get('steps', []))
            })
        
        # Add workflow file nodes
        for workflow in workflow_files:
            nodes.append({
                'id': workflow['file'],
                'name': workflow['file'],
                'type': 'workflow_file',
                'complexity': workflow['complexity']
            })
        
        # Simple edge detection based on shared steps or similar names
        # This is a basic implementation and could be enhanced
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                if self.are_related_pipelines(node1, node2):
                    edges.append({
                        'source': node1['id'],
                        'target': node2['id'],
                        'relationship': 'related'
                    })
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def are_related_pipelines(self, node1: Dict[str, Any], node2: Dict[str, Any]) -> bool:
        """
        Determine if two pipeline nodes are related.
        
        Args:
            node1: First pipeline node
            node2: Second pipeline node
            
        Returns:
            True if pipelines appear to be related
        """
        # Simple heuristic: similar names or one contains the other
        name1 = node1['name'].lower()
        name2 = node2['name'].lower()
        
        # Check for shared keywords
        keywords1 = set(name1.split('_'))
        keywords2 = set(name2.split('_'))
        
        shared_keywords = keywords1.intersection(keywords2)
        return len(shared_keywords) > 0
