"""
Data models for AI/ML component analysis results.

This module defines the data structures used to represent AI/ML
components, models, and pipelines detected in codebases.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pathlib import Path


class FrameworkType(Enum):
    """Types of AI/ML frameworks."""
    
    DEEP_LEARNING = "deep_learning"
    MACHINE_LEARNING = "machine_learning"
    DATA_PROCESSING = "data_processing"
    COMPUTER_VISION = "computer_vision"
    NLP = "nlp"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    OPTIMIZATION = "optimization"
    STATISTICS = "statistics"


class ModelType(Enum):
    """Types of ML models."""
    
    NEURAL_NETWORK = "neural_network"
    TRANSFORMER = "transformer"
    CNN = "cnn"
    RNN = "rnn"
    LSTM = "lstm"
    GAN = "gan"
    AUTOENCODER = "autoencoder"
    DECISION_TREE = "decision_tree"
    RANDOM_FOREST = "random_forest"
    SVM = "svm"
    LINEAR_REGRESSION = "linear_regression"
    LOGISTIC_REGRESSION = "logistic_regression"
    CLUSTERING = "clustering"
    REINFORCEMENT = "reinforcement"
    CUSTOM = "custom"


class PipelineStage(Enum):
    """Stages in an ML pipeline."""
    
    DATA_INGESTION = "data_ingestion"
    DATA_PREPROCESSING = "data_preprocessing"
    FEATURE_ENGINEERING = "feature_engineering"
    MODEL_TRAINING = "model_training"
    MODEL_VALIDATION = "model_validation"
    MODEL_DEPLOYMENT = "model_deployment"
    INFERENCE = "inference"
    MONITORING = "monitoring"
    FEEDBACK = "feedback"


@dataclass
class Framework:
    """Detected AI/ML framework information."""
    
    name: str
    version: Optional[str] = None
    framework_type: FrameworkType = FrameworkType.MACHINE_LEARNING
    description: str = ""
    detected_in_files: List[str] = field(default_factory=list)
    import_statements: List[str] = field(default_factory=list)
    confidence_score: float = 0.0  # 0-1 confidence in detection
    
    def add_detection_file(self, file_path: str) -> None:
        """Add a file where this framework was detected."""
        if file_path not in self.detected_in_files:
            self.detected_in_files.append(file_path)
    
    def add_import_statement(self, import_stmt: str) -> None:
        """Add an import statement for this framework."""
        if import_stmt not in self.import_statements:
            self.import_statements.append(import_stmt)
    
    @property
    def usage_frequency(self) -> int:
        """Get usage frequency based on number of files."""
        return len(self.detected_in_files)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'version': self.version,
            'framework_type': self.framework_type.value,
            'description': self.description,
            'detected_in_files': self.detected_in_files,
            'import_statements': self.import_statements,
            'confidence_score': self.confidence_score,
            'usage_frequency': self.usage_frequency,
        }


@dataclass
class MLModel:
    """Detected ML model information."""
    
    name: str
    model_type: ModelType = ModelType.CUSTOM
    file_path: str = ""
    description: str = ""
    
    # Model characteristics
    input_shape: Optional[List[int]] = None
    output_shape: Optional[List[int]] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Training information
    training_file: Optional[str] = None
    dataset_info: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    
    # Associated files
    config_files: List[str] = field(default_factory=list)
    checkpoint_files: List[str] = field(default_factory=list)
    
    # Detection metadata
    confidence_score: float = 0.0
    detected_frameworks: List[str] = field(default_factory=list)
    
    def add_config_file(self, file_path: str) -> None:
        """Add a configuration file."""
        if file_path not in self.config_files:
            self.config_files.append(file_path)
    
    def add_checkpoint_file(self, file_path: str) -> None:
        """Add a checkpoint file."""
        if file_path not in self.checkpoint_files:
            self.checkpoint_files.append(file_path)
    
    def add_metric(self, metric_name: str, value: float) -> None:
        """Add a performance metric."""
        self.metrics[metric_name] = value
    
    def add_parameter(self, param_name: str, value: Any) -> None:
        """Add a model parameter."""
        self.parameters[param_name] = value
    
    @property
    def has_training_info(self) -> bool:
        """Check if training information is available."""
        return bool(self.training_file or self.dataset_info)
    
    @property
    def has_performance_metrics(self) -> bool:
        """Check if performance metrics are available."""
        return bool(self.metrics)
    
    @property
    def total_files(self) -> int:
        """Get total number of associated files."""
        return len(self.config_files) + len(self.checkpoint_files) + (1 if self.training_file else 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'model_type': self.model_type.value,
            'file_path': self.file_path,
            'description': self.description,
            'input_shape': self.input_shape,
            'output_shape': self.output_shape,
            'parameters': self.parameters,
            'training_file': self.training_file,
            'dataset_info': self.dataset_info,
            'metrics': self.metrics,
            'config_files': self.config_files,
            'checkpoint_files': self.checkpoint_files,
            'confidence_score': self.confidence_score,
            'detected_frameworks': self.detected_frameworks,
            'has_training_info': self.has_training_info,
            'has_performance_metrics': self.has_performance_metrics,
            'total_files': self.total_files,
        }


@dataclass
class PipelineStep:
    """A single step in an ML pipeline."""
    
    name: str
    stage: PipelineStage
    file_path: str = ""
    function_name: str = ""
    description: str = ""
    
    # Step characteristics
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    
    # Execution metadata
    estimated_runtime: Optional[float] = None  # in seconds
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    
    def add_input(self, input_name: str) -> None:
        """Add an input to this step."""
        if input_name not in self.inputs:
            self.inputs.append(input_name)
    
    def add_output(self, output_name: str) -> None:
        """Add an output from this step."""
        if output_name not in self.outputs:
            self.outputs.append(output_name)
    
    def add_dependency(self, dependency: str) -> None:
        """Add a dependency for this step."""
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'stage': self.stage.value,
            'file_path': self.file_path,
            'function_name': self.function_name,
            'description': self.description,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'parameters': self.parameters,
            'dependencies': self.dependencies,
            'estimated_runtime': self.estimated_runtime,
            'resource_requirements': self.resource_requirements,
        }


@dataclass
class Pipeline:
    """Detected ML pipeline information."""
    
    name: str
    description: str = ""
    pipeline_file: str = ""
    
    # Pipeline steps
    steps: List[PipelineStep] = field(default_factory=list)
    
    # Pipeline characteristics
    pipeline_type: str = "batch"  # batch, streaming, real-time
    orchestration_tool: Optional[str] = None  # airflow, kubeflow, etc.
    
    # Configuration
    config_files: List[str] = field(default_factory=list)
    environment_files: List[str] = field(default_factory=list)
    
    # Associated models
    models_used: List[str] = field(default_factory=list)
    
    # Detection metadata
    confidence_score: float = 0.0
    detected_at: datetime = field(default_factory=datetime.now)
    
    def add_step(self, step: PipelineStep) -> None:
        """Add a step to the pipeline."""
        self.steps.append(step)
        # Sort steps by stage order
        stage_order = {stage: i for i, stage in enumerate(PipelineStage)}
        self.steps.sort(key=lambda s: stage_order.get(s.stage, 999))
    
    def get_steps_by_stage(self, stage: PipelineStage) -> List[PipelineStep]:
        """Get all steps for a specific stage."""
        return [step for step in self.steps if step.stage == stage]
    
    def add_model(self, model_name: str) -> None:
        """Add a model used by this pipeline."""
        if model_name not in self.models_used:
            self.models_used.append(model_name)
    
    @property
    def total_steps(self) -> int:
        """Get total number of steps."""
        return len(self.steps)
    
    @property
    def stages_covered(self) -> List[PipelineStage]:
        """Get list of stages covered by this pipeline."""
        return list(set(step.stage for step in self.steps))
    
    @property
    def is_complete_pipeline(self) -> bool:
        """Check if this covers a complete ML pipeline."""
        required_stages = {
            PipelineStage.DATA_INGESTION,
            PipelineStage.MODEL_TRAINING,
            PipelineStage.INFERENCE
        }
        covered_stages = set(self.stages_covered)
        return required_stages.issubset(covered_stages)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'pipeline_file': self.pipeline_file,
            'pipeline_type': self.pipeline_type,
            'orchestration_tool': self.orchestration_tool,
            'config_files': self.config_files,
            'environment_files': self.environment_files,
            'models_used': self.models_used,
            'confidence_score': self.confidence_score,
            'detected_at': self.detected_at.isoformat(),
            'total_steps': self.total_steps,
            'stages_covered': [stage.value for stage in self.stages_covered],
            'is_complete_pipeline': self.is_complete_pipeline,
            'steps': [step.to_dict() for step in self.steps],
        }


@dataclass
class AIComponent:
    """Complete AI/ML component analysis for a codebase."""
    
    repository_path: str
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    
    # Detected components
    frameworks: List[Framework] = field(default_factory=list)
    models: List[MLModel] = field(default_factory=list)
    pipelines: List[Pipeline] = field(default_factory=list)
    
    # Additional findings
    training_scripts: List[str] = field(default_factory=list)
    inference_endpoints: List[str] = field(default_factory=list)
    data_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    
    # Analysis metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_framework(self, framework: Framework) -> None:
        """Add a detected framework."""
        self.frameworks.append(framework)
    
    def add_model(self, model: MLModel) -> None:
        """Add a detected model."""
        self.models.append(model)
    
    def add_pipeline(self, pipeline: Pipeline) -> None:
        """Add a detected pipeline."""
        self.pipelines.append(pipeline)
    
    def get_framework(self, name: str) -> Optional[Framework]:
        """Get framework by name."""
        for framework in self.frameworks:
            if framework.name == name:
                return framework
        return None
    
    def get_model(self, name: str) -> Optional[MLModel]:
        """Get model by name."""
        for model in self.models:
            if model.name == name:
                return model
        return None
    
    def get_pipeline(self, name: str) -> Optional[Pipeline]:
        """Get pipeline by name."""
        for pipeline in self.pipelines:
            if pipeline.name == name:
                return pipeline
        return None
    
    @property
    def has_ai_components(self) -> bool:
        """Check if any AI/ML components were detected."""
        return bool(self.frameworks or self.models or self.pipelines)
    
    @property
    def primary_frameworks(self) -> List[Framework]:
        """Get primary frameworks (highest confidence/usage)."""
        return sorted(
            self.frameworks, 
            key=lambda f: (f.confidence_score, f.usage_frequency), 
            reverse=True
        )[:3]
    
    @property
    def model_types_detected(self) -> List[ModelType]:
        """Get unique model types detected."""
        return list(set(model.model_type for model in self.models))
    
    @property
    def pipeline_stages_covered(self) -> List[PipelineStage]:
        """Get all pipeline stages covered across all pipelines."""
        stages = set()
        for pipeline in self.pipelines:
            stages.update(pipeline.stages_covered)
        return list(stages)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'repository_path': self.repository_path,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'summary': {
                'has_ai_components': self.has_ai_components,
                'total_frameworks': len(self.frameworks),
                'total_models': len(self.models),
                'total_pipelines': len(self.pipelines),
                'model_types_detected': [mt.value for mt in self.model_types_detected],
                'pipeline_stages_covered': [stage.value for stage in self.pipeline_stages_covered],
            },
            'frameworks': [f.to_dict() for f in self.frameworks],
            'models': [m.to_dict() for m in self.models],
            'pipelines': [p.to_dict() for p in self.pipelines],
            'primary_frameworks': [f.to_dict() for f in self.primary_frameworks],
            'training_scripts': self.training_scripts,
            'inference_endpoints': self.inference_endpoints,
            'data_files': self.data_files,
            'config_files': self.config_files,
            'metadata': self.metadata,
        }
