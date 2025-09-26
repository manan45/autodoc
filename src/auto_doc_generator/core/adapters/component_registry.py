"""
Component registry for coordinator integration.

This registry manages component registration and provides a centralized
way to access and coordinate between different system components.
"""

import logging
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from enum import Enum

from .analyzer_adapter import AnalyzerAdapter
from .generator_adapter import GeneratorAdapter

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Types of components in the system."""
    ANALYZER = "analyzer"
    GENERATOR = "generator"
    COORDINATOR = "coordinator"
    SERVICE = "service"
    UTILITY = "utility"


@dataclass
class ComponentInfo:
    """Information about a registered component."""
    name: str
    component_type: ComponentType
    handler: Callable
    description: str = ""
    capabilities: List[str] = None
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class ComponentRegistry:
    """
    Registry for managing system components.
    
    This registry provides a centralized way to register, discover,
    and interact with different components in the system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize component registry.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Component storage
        self.components: Dict[str, ComponentInfo] = {}
        self.component_handlers: Dict[str, Callable] = {}
        
        # Adapters
        self.analyzer_adapter = AnalyzerAdapter(config)
        self.generator_adapter = GeneratorAdapter(config)
        
        # Initialize default components
        self._register_default_components()
        
        self.logger.info("Component registry initialized")
    
    def _register_default_components(self):
        """Register default system components."""
        # Register analyzer components
        self.register_component(
            name="code_analyzer",
            component_type=ComponentType.ANALYZER,
            handler=self.analyzer_adapter.analyze_code_structure,
            description="Analyzes code structure using AST analysis",
            capabilities=["ast_analysis", "function_detection", "class_detection"],
            dependencies=[]
        )
        
        self.register_component(
            name="ai_analyzer",
            component_type=ComponentType.ANALYZER,
            handler=self.analyzer_adapter.analyze_ai_components,
            description="Analyzes AI/ML components and frameworks",
            capabilities=["framework_detection", "model_analysis", "pipeline_analysis"],
            dependencies=[]
        )
        
        self.register_component(
            name="quality_analyzer",
            component_type=ComponentType.ANALYZER,
            handler=self.analyzer_adapter.analyze_quality_metrics,
            description="Analyzes code quality metrics and provides insights",
            capabilities=["metrics_analysis", "llm_insights", "quality_scoring"],
            dependencies=[]
        )
        
        # Register generator components
        self.register_component(
            name="documentation_generator",
            component_type=ComponentType.GENERATOR,
            handler=self.generator_adapter.generate_html_documentation,
            description="Generates HTML documentation from analysis results",
            capabilities=["html_generation", "template_processing"],
            dependencies=["code_analyzer"]
        )
        
        self.register_component(
            name="diagram_generator",
            component_type=ComponentType.GENERATOR,
            handler=self.generator_adapter.generate_architecture_diagrams,
            description="Generates architecture diagrams",
            capabilities=["diagram_generation", "visualization"],
            dependencies=["code_analyzer", "ai_analyzer"]
        )
        
        self.register_component(
            name="template_processor",
            component_type=ComponentType.GENERATOR,
            handler=self.generator_adapter.process_templates,
            description="Processes templates with generated content",
            capabilities=["template_processing", "content_assembly"],
            dependencies=["documentation_generator"]
        )
        
        self.register_component(
            name="file_manager",
            component_type=ComponentType.UTILITY,
            handler=self.generator_adapter.manage_file_operations,
            description="Manages file operations for output generation",
            capabilities=["file_operations", "output_management"],
            dependencies=["template_processor"]
        )
        
        # Register coordinator as a component (for self-referential tasks)
        self.register_component(
            name="coordinator",
            component_type=ComponentType.COORDINATOR,
            handler=self._coordinator_handler,
            description="Coordinates tasks and makes decisions",
            capabilities=["task_planning", "decision_making", "workflow_coordination"],
            dependencies=[]
        )
    
    def register_component(self, name: str, component_type: ComponentType, handler: Callable,
                          description: str = "", capabilities: List[str] = None,
                          dependencies: List[str] = None, metadata: Dict[str, Any] = None):
        """
        Register a component.
        
        Args:
            name: Component name
            component_type: Type of component
            handler: Handler function for the component
            description: Description of the component
            capabilities: List of capabilities
            dependencies: List of component dependencies
            metadata: Additional metadata
        """
        component_info = ComponentInfo(
            name=name,
            component_type=component_type,
            handler=handler,
            description=description,
            capabilities=capabilities or [],
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        self.components[name] = component_info
        self.component_handlers[name] = handler
        
        self.logger.info(f"Registered component: {name} ({component_type.value})")
    
    def get_component(self, name: str) -> Optional[ComponentInfo]:
        """
        Get component information.
        
        Args:
            name: Component name
            
        Returns:
            Component information if found
        """
        return self.components.get(name)
    
    def get_handler(self, name: str) -> Optional[Callable]:
        """
        Get component handler.
        
        Args:
            name: Component name
            
        Returns:
            Component handler if found
        """
        return self.component_handlers.get(name)
    
    def list_components(self, component_type: Optional[ComponentType] = None) -> List[ComponentInfo]:
        """
        List registered components.
        
        Args:
            component_type: Optional filter by component type
            
        Returns:
            List of component information
        """
        if component_type:
            return [comp for comp in self.components.values() if comp.component_type == component_type]
        else:
            return list(self.components.values())
    
    def get_components_by_capability(self, capability: str) -> List[ComponentInfo]:
        """
        Get components that have a specific capability.
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of components with the capability
        """
        return [comp for comp in self.components.values() if capability in comp.capabilities]
    
    def check_dependencies(self, component_name: str) -> Dict[str, bool]:
        """
        Check if component dependencies are satisfied.
        
        Args:
            component_name: Name of component to check
            
        Returns:
            Dictionary mapping dependency names to availability status
        """
        component = self.components.get(component_name)
        if not component:
            return {}
        
        dependency_status = {}
        for dep in component.dependencies:
            dependency_status[dep] = dep in self.components
        
        return dependency_status
    
    def get_execution_order(self, component_names: List[str]) -> List[str]:
        """
        Get optimal execution order based on dependencies.
        
        Args:
            component_names: List of component names
            
        Returns:
            Ordered list of component names
        """
        # Simple topological sort
        ordered = []
        remaining = set(component_names)
        
        while remaining:
            # Find components with no unresolved dependencies
            ready = []
            for name in remaining:
                component = self.components.get(name)
                if not component:
                    continue
                
                unresolved_deps = [dep for dep in component.dependencies 
                                 if dep in remaining and dep not in ordered]
                
                if not unresolved_deps:
                    ready.append(name)
            
            if not ready:
                # Circular dependency or missing component - add remaining in order
                ready = list(remaining)
            
            # Add ready components to ordered list
            for name in ready:
                ordered.append(name)
                remaining.discard(name)
        
        return ordered
    
    def get_registry_status(self) -> Dict[str, Any]:
        """
        Get registry status information.
        
        Returns:
            Registry status information
        """
        component_stats = {}
        for comp_type in ComponentType:
            components = self.list_components(comp_type)
            component_stats[comp_type.value] = {
                'count': len(components),
                'names': [comp.name for comp in components]
            }
        
        return {
            'total_components': len(self.components),
            'component_stats': component_stats,
            'registered_components': list(self.components.keys()),
            'adapters_initialized': {
                'analyzer_adapter': self.analyzer_adapter is not None,
                'generator_adapter': self.generator_adapter is not None
            }
        }
    
    async def _coordinator_handler(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handler for coordinator self-referential tasks.
        
        Args:
            input_data: Input data for coordinator task
            
        Returns:
            Coordinator task results
        """
        try:
            task_type = input_data.get('task_type', 'unknown')
            
            if task_type == 'decision_making':
                return await self._handle_decision_making(input_data)
            elif task_type == 'coordination':
                return await self._handle_coordination(input_data)
            else:
                return {
                    "success": True,
                    "data": {"message": f"Coordinator handled task: {task_type}"},
                    "metadata": {"task_type": task_type}
                }
            
        except Exception as e:
            self.logger.error(f"Error in coordinator handler: {e}")
            return {"success": False, "error": str(e)}
    
    async def _handle_decision_making(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle decision making tasks."""
        try:
            analysis_results = input_data.get('analysis_results', {})
            
            # Simple decision making logic
            decisions = {
                'documentation_approach': 'comprehensive',
                'include_diagrams': True,
                'include_quality_metrics': True,
                'priority_order': ['code_analysis', 'documentation_generation', 'diagram_generation']
            }
            
            return {
                "success": True,
                "data": {
                    "decisions": decisions,
                    "reasoning": "Based on comprehensive analysis approach"
                },
                "metadata": {"decision_type": "documentation_planning"}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _handle_coordination(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle coordination tasks."""
        try:
            # Simple coordination logic
            coordination_result = {
                'components_coordinated': list(self.components.keys()),
                'execution_plan': {
                    'phase_1': ['code_analyzer', 'ai_analyzer', 'quality_analyzer'],
                    'phase_2': ['documentation_generator', 'diagram_generator'],
                    'phase_3': ['template_processor', 'file_manager']
                }
            }
            
            return {
                "success": True,
                "data": coordination_result,
                "metadata": {"coordination_type": "workflow_planning"}
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
