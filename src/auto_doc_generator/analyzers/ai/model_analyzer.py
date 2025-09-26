"""
AI/ML model analysis.

This module analyzes AI/ML models in Python codebases to identify
model architectures, training patterns, and inference endpoints.
"""

import ast
import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from datetime import datetime

from ..base.base_analyzer import BaseAnalyzer


class ModelAnalyzer(BaseAnalyzer):
    """
    Analyzer that identifies and analyzes AI/ML models in code.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Model-related patterns
        self.model_patterns = {
            'tensorflow': [
                r'tf\.keras\.Model',
                r'tf\.keras\.Sequential',
                r'keras\.Model',
                r'keras\.Sequential',
                r'tf\.estimator',
                r'tf\.nn\.',
                r'tf\.layers\.'
            ],
            'pytorch': [
                r'torch\.nn\.Module',
                r'nn\.Module',
                r'torch\.nn\.',
                r'F\.',
                r'torch\.optim',
                r'torch\.utils\.data'
            ],
            'sklearn': [
                r'sklearn\.',
                r'from sklearn',
                r'LinearRegression',
                r'RandomForestClassifier',
                r'SVC',
                r'KMeans'
            ],
            'huggingface': [
                r'transformers\.',
                r'AutoModel',
                r'AutoTokenizer',
                r'pipeline',
                r'from transformers'
            ],
            'xgboost': [
                r'xgboost',
                r'XGBClassifier',
                r'XGBRegressor'
            ],
            'lightgbm': [
                r'lightgbm',
                r'LGBMClassifier',
                r'LGBMRegressor'
            ]
        }
        
        # Training-related patterns
        self.training_patterns = [
            r'\.fit\(',
            r'\.train\(',
            r'\.compile\(',
            r'optimizer\s*=',
            r'loss\s*=',
            r'epochs\s*=',
            r'batch_size\s*=',
            r'learning_rate\s*=',
            r'\.backward\(',
            r'\.step\(',
            r'DataLoader',
            r'Dataset'
        ]
        
        # Inference patterns
        self.inference_patterns = [
            r'\.predict\(',
            r'\.predict_proba\(',
            r'\.transform\(',
            r'\.forward\(',
            r'model\(',
            r'\.eval\(',
            r'torch\.no_grad',
            r'tf\.function'
        ]
    
    def analyze(self, target: Path) -> Dict[str, Any]:
        """
        Analyze AI/ML models in Python files.
        
        Args:
            target: Directory or file path to analyze
            
        Returns:
            Dictionary containing model analysis results
        """
        self.log_analysis_start(str(target))
        
        result = self.create_result_template()
        result['timestamp'] = datetime.now().isoformat()
        
        if target.is_file():
            files = [target]
        else:
            files = self.find_python_files(target)
        
        models = []
        frameworks_detected = set()
        training_files = []
        inference_files = []
        
        for file_path in files:
            try:
                file_analysis = self.analyze_file_models(file_path)
                if file_analysis:
                    if file_analysis['models']:
                        models.extend(file_analysis['models'])
                    
                    frameworks_detected.update(file_analysis['frameworks'])
                    
                    if file_analysis['has_training']:
                        training_files.append(str(file_path.relative_to(target if target.is_dir() else target.parent)))
                    
                    if file_analysis['has_inference']:
                        inference_files.append(str(file_path.relative_to(target if target.is_dir() else target.parent)))
                        
            except Exception as e:
                result['errors'].append(f"Failed to analyze models in {file_path}: {str(e)}")
        
        result['results'] = {
            'models': models,
            'frameworks_detected': sorted(list(frameworks_detected)),
            'training_files': training_files,
            'inference_files': inference_files,
            'summary': {
                'total_models': len(models),
                'frameworks_count': len(frameworks_detected),
                'training_files_count': len(training_files),
                'inference_files_count': len(inference_files)
            }
        }
        
        self.log_analysis_complete(str(target), len(models))
        return result
    
    def analyze_file_models(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Analyze models in a single Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with model analysis or None if analysis failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Extract models from classes
            models = []
            frameworks = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    model_info = self.analyze_model_class(node, content)
                    if model_info:
                        models.append(model_info)
                        if model_info.get('framework'):
                            frameworks.add(model_info['framework'])
            
            # Detect frameworks from imports and content
            detected_frameworks = self.detect_frameworks(content)
            frameworks.update(detected_frameworks)
            
            # Check for training and inference patterns
            has_training = self.has_training_code(content)
            has_inference = self.has_inference_code(content)
            
            return {
                'file_path': str(file_path),
                'models': models,
                'frameworks': frameworks,
                'has_training': has_training,
                'has_inference': has_inference
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing models in {file_path}: {e}")
            return None
    
    def analyze_model_class(self, node: ast.ClassDef, content: str) -> Optional[Dict[str, Any]]:
        """
        Analyze a class to determine if it's an AI/ML model.
        
        Args:
            node: AST class node
            content: File content for additional analysis
            
        Returns:
            Dictionary with model information or None if not a model
        """
        # Check if class inherits from known model base classes
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(ast.unparse(base) if hasattr(ast, 'unparse') else str(base))
        
        # Determine if this is a model class
        model_indicators = [
            'Model', 'Sequential', 'Module', 'Estimator', 'Classifier', 'Regressor',
            'Pipeline', 'Transformer', 'BaseModel'
        ]
        
        is_model = any(indicator in ' '.join(base_classes) for indicator in model_indicators)
        
        if not is_model:
            # Check class name for model patterns
            is_model = any(indicator in node.name for indicator in model_indicators)
        
        if not is_model:
            return None
        
        # Extract model information
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append({
                    'name': item.name,
                    'line': item.lineno,
                    'args': len(item.args.args),
                    'docstring': ast.get_docstring(item)
                })
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append({
                            'name': target.id,
                            'line': item.lineno
                        })
        
        # Determine framework
        framework = self.determine_model_framework(base_classes, content)
        
        # Determine model type
        model_type = self.determine_model_type(node.name, methods, content)
        
        return {
            'name': node.name,
            'line_start': node.lineno,
            'base_classes': base_classes,
            'framework': framework,
            'model_type': model_type,
            'methods': methods,
            'attributes': attributes,
            'docstring': ast.get_docstring(node)
        }
    
    def detect_frameworks(self, content: str) -> Set[str]:
        """
        Detect AI/ML frameworks from file content.
        
        Args:
            content: File content
            
        Returns:
            Set of detected frameworks
        """
        frameworks = set()
        
        for framework, patterns in self.model_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    frameworks.add(framework)
                    break
        
        return frameworks
    
    def determine_model_framework(self, base_classes: List[str], content: str) -> Optional[str]:
        """
        Determine the framework of a model based on base classes and content.
        
        Args:
            base_classes: List of base class names
            content: File content
            
        Returns:
            Framework name or None
        """
        # Check base classes first
        for base_class in base_classes:
            if 'keras' in base_class.lower() or 'tf.' in base_class:
                return 'tensorflow'
            elif 'torch' in base_class.lower() or 'nn.Module' in base_class:
                return 'pytorch'
            elif 'sklearn' in base_class.lower():
                return 'sklearn'
        
        # Fall back to content analysis
        frameworks = self.detect_frameworks(content)
        return list(frameworks)[0] if frameworks else None
    
    def determine_model_type(self, class_name: str, methods: List[Dict], content: str) -> str:
        """
        Determine the type of model (classifier, regressor, etc.).
        
        Args:
            class_name: Name of the model class
            methods: List of methods in the class
            content: File content
            
        Returns:
            Model type string
        """
        class_name_lower = class_name.lower()
        
        if 'classifier' in class_name_lower:
            return 'classifier'
        elif 'regressor' in class_name_lower:
            return 'regressor'
        elif 'detector' in class_name_lower:
            return 'detector'
        elif 'generator' in class_name_lower:
            return 'generator'
        elif 'discriminator' in class_name_lower:
            return 'discriminator'
        elif 'encoder' in class_name_lower:
            return 'encoder'
        elif 'decoder' in class_name_lower:
            return 'decoder'
        elif 'transformer' in class_name_lower:
            return 'transformer'
        elif 'cnn' in class_name_lower or 'conv' in class_name_lower:
            return 'cnn'
        elif 'rnn' in class_name_lower or 'lstm' in class_name_lower or 'gru' in class_name_lower:
            return 'rnn'
        else:
            return 'model'
    
    def has_training_code(self, content: str) -> bool:
        """
        Check if file contains training code.
        
        Args:
            content: File content
            
        Returns:
            True if training code is detected
        """
        for pattern in self.training_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def has_inference_code(self, content: str) -> bool:
        """
        Check if file contains inference code.
        
        Args:
            content: File content
            
        Returns:
            True if inference code is detected
        """
        for pattern in self.inference_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
