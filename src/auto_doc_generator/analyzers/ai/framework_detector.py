"""
AI/ML Framework Detection.

This module detects AI/ML frameworks and libraries used in the codebase.
"""

import re
from typing import Dict, List, Any, Set
from pathlib import Path
from datetime import datetime

from ..base.base_analyzer import BaseAnalyzer
from ...core.models.ai_models import Framework, FrameworkType


class FrameworkDetector(BaseAnalyzer):
    """
    Detects AI/ML frameworks and libraries in the codebase.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        
        # Framework mappings
        self.framework_mappings = {
            'tensorflow': {
                'type': FrameworkType.DEEP_LEARNING,
                'patterns': ['tensorflow', 'tf\\.', 'keras'],
                'imports': ['tensorflow', 'tf', 'keras']
            },
            'pytorch': {
                'type': FrameworkType.DEEP_LEARNING,
                'patterns': ['torch', 'pytorch'],
                'imports': ['torch', 'torchvision', 'torchaudio']
            },
            'scikit-learn': {
                'type': FrameworkType.MACHINE_LEARNING,
                'patterns': ['sklearn', 'scikit.learn'],
                'imports': ['sklearn', 'scikit_learn']
            },
            'pandas': {
                'type': FrameworkType.DATA_PROCESSING,
                'patterns': ['pandas', 'pd\\.'],
                'imports': ['pandas']
            },
            'numpy': {
                'type': FrameworkType.DATA_PROCESSING,
                'patterns': ['numpy', 'np\\.'],
                'imports': ['numpy']
            },
            'transformers': {
                'type': FrameworkType.NLP,
                'patterns': ['transformers', 'huggingface'],
                'imports': ['transformers']
            },
            'opencv': {
                'type': FrameworkType.COMPUTER_VISION,
                'patterns': ['cv2', 'opencv'],
                'imports': ['cv2', 'opencv']
            },
            'mlflow': {
                'type': FrameworkType.MACHINE_LEARNING,
                'patterns': ['mlflow'],
                'imports': ['mlflow']
            },
            'wandb': {
                'type': FrameworkType.MACHINE_LEARNING,
                'patterns': ['wandb'],
                'imports': ['wandb']
            }
        }
    
    def analyze(self, target: Path) -> Dict[str, Any]:
        """
        Detect AI/ML frameworks in the target directory.
        
        Args:
            target: Directory path to analyze
            
        Returns:
            Dictionary containing framework detection results
        """
        self.log_analysis_start(str(target))
        
        result = self.create_result_template()
        result['timestamp'] = datetime.now().isoformat()
        
        detected_frameworks = []
        
        if target.is_file():
            python_files = [target]
        else:
            python_files = self.find_python_files(target)
        
        # Track framework usage across files
        framework_usage = {}
        
        for file_path in python_files:
            try:
                content = self.read_file_safe(file_path)
                if not content:
                    continue
                
                file_frameworks = self._detect_frameworks_in_file(file_path, content)
                
                for framework_name, framework_info in file_frameworks.items():
                    if framework_name not in framework_usage:
                        framework_usage[framework_name] = {
                            'files': set(),
                            'imports': set(),
                            'confidence_scores': []
                        }
                    
                    framework_usage[framework_name]['files'].add(str(file_path))
                    framework_usage[framework_name]['imports'].update(framework_info['imports'])
                    framework_usage[framework_name]['confidence_scores'].append(framework_info['confidence'])
                    
            except Exception as e:
                result['errors'].append(f"Failed to analyze {file_path}: {str(e)}")
        
        # Create Framework objects
        for framework_name, usage_info in framework_usage.items():
            if framework_name in self.framework_mappings:
                mapping = self.framework_mappings[framework_name]
                
                framework = Framework(
                    name=framework_name,
                    framework_type=mapping['type'],
                    detected_in_files=list(usage_info['files']),
                    import_statements=list(usage_info['imports']),
                    confidence_score=sum(usage_info['confidence_scores']) / len(usage_info['confidence_scores'])
                )
                
                detected_frameworks.append(framework)
        
        # Sort by confidence and usage frequency
        detected_frameworks.sort(
            key=lambda f: (f.confidence_score, f.usage_frequency), 
            reverse=True
        )
        
        result['results'] = {
            'frameworks': [f.to_dict() for f in detected_frameworks],
            'total_frameworks': len(detected_frameworks),
            'primary_frameworks': [f.to_dict() for f in detected_frameworks[:3]],
            'framework_types': list(set(f.framework_type.value for f in detected_frameworks))
        }
        
        self.log_analysis_complete(str(target), len(detected_frameworks))
        return result
    
    def _detect_frameworks_in_file(self, file_path: Path, content: str) -> Dict[str, Dict[str, Any]]:
        """Detect frameworks in a single file."""
        detected = {}
        
        for framework_name, mapping in self.framework_mappings.items():
            confidence = 0.0
            found_imports = set()
            
            # Check import statements
            for import_pattern in mapping['imports']:
                if re.search(rf'import\s+{re.escape(import_pattern)}', content, re.IGNORECASE):
                    confidence += 0.8
                    found_imports.add(import_pattern)
                elif re.search(rf'from\s+{re.escape(import_pattern)}', content, re.IGNORECASE):
                    confidence += 0.8
                    found_imports.add(import_pattern)
            
            # Check usage patterns
            for pattern in mapping['patterns']:
                matches = len(re.findall(pattern, content, re.IGNORECASE))
                if matches > 0:
                    confidence += min(matches * 0.1, 0.5)
            
            # Normalize confidence score
            confidence = min(confidence, 1.0)
            
            if confidence > 0.1:  # Minimum threshold
                detected[framework_name] = {
                    'confidence': confidence,
                    'imports': found_imports,
                    'file_path': str(file_path)
                }
        
        return detected
