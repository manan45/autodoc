"""
Coordinator Service - MetaGPT/AutoGPT style task orchestration.

This service implements an intelligent coordinator that can plan, delegate,
and execute complex documentation generation workflows by breaking them down
into manageable tasks and coordinating between different components.
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict, is_dataclass
from typing import Dict, List, Any, Optional, Callable, Union
from enum import Enum
from datetime import datetime, timezone
import uuid

from ..repositories.base_repository import BaseRepository, SessionData, TaskData, PromptData, DecisionData, InteractionData
from ..repositories.file_repository import FileRepository
from ..repositories.cache_repository import CacheRepository
from .ai_service import AIService


class DataclassJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for dataclass objects and other complex types."""
    
    def default(self, obj):
        if is_dataclass(obj):
            # Use to_dict() if available, otherwise convert to dict
            if hasattr(obj, 'to_dict'):
                return obj.to_dict()
            else:
                return asdict(obj)
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Types of tasks the coordinator can manage."""
    ANALYSIS = "analysis"
    CODE_ANALYSIS = "code_analysis"
    AI_ANALYSIS = "ai_analysis"
    QUALITY_ANALYSIS = "quality_analysis"
    DOCUMENTATION_GENERATION = "documentation_generation"
    DIAGRAM_GENERATION = "diagram_generation"
    TEMPLATE_PROCESSING = "template_processing"
    FILE_OPERATIONS = "file_operations"
    COORDINATION = "coordination"
    DECISION_MAKING = "decision_making"


@dataclass
class Task:
    """Represents a task in the coordinator system."""
    id: str
    task_type: TaskType
    description: str
    priority: int = 1
    status: TaskStatus = TaskStatus.PENDING
    parent_task_id: Optional[str] = None
    dependencies: List[str] = None
    assigned_component: str = ""
    input_data: Dict[str, Any] = None
    output_data: Dict[str, Any] = None
    execution_plan: Dict[str, Any] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.input_data is None:
            self.input_data = {}
        if self.output_data is None:
            self.output_data = {}
        if self.execution_plan is None:
            self.execution_plan = {}
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class DecisionContext:
    """Context for coordinator decision making."""
    session_id: str
    task_id: Optional[str]
    decision_type: str
    available_options: List[str]
    context_data: Dict[str, Any]
    constraints: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = {}


class CoordinatorService:
    """
    MetaGPT/AutoGPT-style coordinator service.
    
    This service implements intelligent task planning, delegation, and execution
    coordination with AI-driven decision making and comprehensive logging.
    """
    
    def __init__(self, file_repository: FileRepository, cache_repository: CacheRepository,
                 repository: BaseRepository, ai_service: AIService, config: Dict[str, Any]):
        """
        Initialize the coordinator service.
        
        Args:
            file_repository: File operations repository
            cache_repository: Caching repository
            repository: Database repository (any type)
            ai_service: AI service for decision making
            config: Configuration dictionary
        """
        self.file_repository = file_repository
        self.cache_repository = cache_repository
        self.repository = repository
        self.ai_service = ai_service
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Task management
        self.tasks: Dict[str, Task] = {}
        self.component_registry: Dict[str, Callable] = {}
        self.current_session_id: Optional[str] = None
        self.current_workflow_id: Optional[str] = None
        
        # Execution state
        self.is_running = False
        self.max_concurrent_tasks = config.get('coordinator', {}).get('max_concurrent_tasks', 3)
        self.task_timeout_seconds = config.get('coordinator', {}).get('task_timeout_seconds', 300)
        
        self.logger.info("Coordinator service initialized")
    
    def register_component(self, component_name: str, component_handler: Callable):
        """
        Register a component handler.
        
        Args:
            component_name: Name of the component
            component_handler: Handler function for the component
        """
        self.component_registry[component_name] = component_handler
        self.logger.info(f"Registered component: {component_name}")
    
    async def start_session(self, repository_path: str, session_type: str = "coordinated_generation",
                           output_format: str = "html", output_path: str = "") -> Optional[str]:
        """
        Start a new coordinated session.
        
        Args:
            repository_path: Path to the repository
            session_type: Type of session
            output_format: Output format
            output_path: Output path
            
        Returns:
            Session ID if successful
        """
        try:
            # Create session in database
            session_data = SessionData(
                repository_path=repository_path,
                session_type=session_type,
                output_format=output_format,
                output_path=output_path,
                start_time=datetime.now(timezone.utc)
            )
            
            session_id = self.repository.create_session(session_data)
            
            if session_id:
                self.current_session_id = session_id
                self.logger.info(f"Started coordinated session: {session_id}")
                
                # Create initial workflow
                await self._create_initial_workflow(repository_path, output_format)
                
                return session_id
            else:
                self.logger.error("Failed to create session")
                return None
                
        except Exception as e:
            self.logger.error(f"Error starting session: {e}")
            return None
    
    async def _create_initial_workflow(self, repository_path: str, output_format: str):
        """Create the comprehensive initial workflow for best-in-class documentation generation."""
        try:
            # Enhanced workflow with comprehensive analysis phases
            workflow_steps = [
                {
                    "step": 1,
                    "name": "Deep Repository Discovery",
                    "description": "Comprehensive repository structure and technology stack analysis",
                    "tasks": [
                        "repository_structure_analysis",
                        "technology_stack_detection",
                        "dependency_mapping",
                        "file_type_classification",
                        "entry_point_identification"
                    ],
                    "estimated_time": 120,
                    "parallel_execution": True
                },
                {
                    "step": 2,
                    "name": "Multi-Dimensional Code Analysis",
                    "description": "Advanced code analysis across multiple dimensions",
                    "tasks": [
                        "ast_deep_analysis",
                        "complexity_metrics_analysis",
                        "design_pattern_detection",
                        "api_endpoint_discovery",
                        "database_schema_analysis",
                        "configuration_analysis"
                    ],
                    "estimated_time": 180,
                    "parallel_execution": True,
                    "dependencies": ["step_1"]
                },
                {
                    "step": 3,
                    "name": "AI/ML Component Intelligence",
                    "description": "Advanced AI/ML component detection and analysis",
                    "tasks": [
                        "ml_framework_detection",
                        "model_architecture_analysis",
                        "training_pipeline_discovery",
                        "data_flow_analysis",
                        "inference_endpoint_mapping",
                        "model_versioning_analysis"
                    ],
                    "estimated_time": 150,
                    "parallel_execution": True,
                    "dependencies": ["step_1"]
                },
                {
                    "step": 4,
                    "name": "Advanced Quality Assessment",
                    "description": "Comprehensive code quality and maintainability analysis",
                    "tasks": [
                        "code_quality_metrics",
                        "security_vulnerability_scan",
                        "performance_bottleneck_detection",
                        "test_coverage_analysis",
                        "documentation_gap_analysis",
                        "technical_debt_assessment",
                        "llm_code_review"
                    ],
                    "estimated_time": 200,
                    "parallel_execution": True,
                    "dependencies": ["step_2"]
                },
                {
                    "step": 5,
                    "name": "Intelligent Documentation Planning",
                    "description": "AI-driven documentation structure and content planning",
                    "tasks": [
                        "audience_analysis",
                        "documentation_type_selection",
                        "content_prioritization",
                        "narrative_structure_planning",
                        "visual_element_planning",
                        "interactive_element_planning"
                    ],
                    "estimated_time": 120,
                    "parallel_execution": False,
                    "dependencies": ["step_2", "step_3", "step_4"]
                },
                {
                    "step": 6,
                    "name": "Multi-Format Content Generation",
                    "description": "Generate comprehensive documentation in multiple formats",
                    "tasks": [
                        "api_documentation_generation",
                        "architecture_documentation",
                        "user_guide_generation",
                        "developer_guide_generation",
                        "deployment_guide_generation",
                        "troubleshooting_guide_generation",
                        "changelog_generation"
                    ],
                    "estimated_time": 300,
                    "parallel_execution": True,
                    "dependencies": ["step_5"]
                },
                {
                    "step": 7,
                    "name": "Advanced Visualization Generation",
                    "description": "Create comprehensive visual documentation elements",
                    "tasks": [
                        "system_architecture_diagrams",
                        "data_flow_diagrams",
                        "api_interaction_diagrams",
                        "deployment_architecture_diagrams",
                        "component_dependency_graphs",
                        "user_journey_flowcharts",
                        "performance_metrics_visualizations"
                    ],
                    "estimated_time": 180,
                    "parallel_execution": True,
                    "dependencies": ["step_5"]
                },
                {
                    "step": 8,
                    "name": "Interactive Elements Creation",
                    "description": "Generate interactive documentation components",
                    "tasks": [
                        "interactive_api_explorer",
                        "code_example_playground",
                        "configuration_wizard",
                        "troubleshooting_decision_tree",
                        "performance_dashboard",
                        "search_and_navigation_system"
                    ],
                    "estimated_time": 240,
                    "parallel_execution": True,
                    "dependencies": ["step_6"]
                },
                {
                    "step": 9,
                    "name": "Quality Assurance and Enhancement",
                    "description": "Comprehensive quality check and content enhancement",
                    "tasks": [
                        "content_accuracy_validation",
                        "consistency_check",
                        "accessibility_compliance",
                        "seo_optimization",
                        "cross_reference_validation",
                        "broken_link_detection",
                        "content_freshness_analysis"
                    ],
                    "estimated_time": 150,
                    "parallel_execution": True,
                    "dependencies": ["step_6", "step_7", "step_8"]
                },
                {
                    "step": 10,
                    "name": "Final Assembly and Optimization",
                    "description": "Assemble, optimize, and deploy final documentation",
                    "tasks": [
                        "content_assembly",
                        "template_processing",
                        "asset_optimization",
                        "performance_optimization",
                        "responsive_design_implementation",
                        "final_quality_check",
                        "deployment_preparation"
                    ],
                    "estimated_time": 120,
                    "parallel_execution": False,
                    "dependencies": ["step_9"]
                }
            ]
            
            # Calculate total estimated time
            total_estimated_time = sum(step.get("estimated_time", 60) for step in workflow_steps)
            
            # Create workflow data structure
            workflow_data = {
                "session_id": self.current_session_id,
                "workflow_name": "Comprehensive AI-Coordinated Documentation Generation",
                "workflow_description": f"Best-in-class AI-coordinated documentation generation for {repository_path} using advanced multi-phase analysis and generation",
                "workflow_steps": workflow_steps,
                "input_requirements": {
                    "repository_path": repository_path,
                    "analysis_depth": "comprehensive",
                    "quality_level": "production",
                    "audience_types": ["developers", "users", "administrators", "contributors"]
                },
                "output_expectations": {
                    "format": output_format,
                    "completeness": "comprehensive",
                    "quality": "production",
                    "interactivity": "high",
                    "accessibility": "wcag_aa_compliant",
                    "seo_optimized": True
                },
                "estimated_duration_seconds": total_estimated_time,
                "metadata": {
                    "workflow_version": "2.0",
                    "analysis_type": "comprehensive",
                    "ai_enhanced": True,
                    "multi_format": True,
                    "interactive": True,
                    "total_phases": len(workflow_steps),
                    "parallel_phases": len([s for s in workflow_steps if s.get("parallel_execution", False)]),
                    "sequential_phases": len([s for s in workflow_steps if not s.get("parallel_execution", False)])
                }
            }
            
            # Store workflow if repository is available
            workflow_id = None
            if hasattr(self.repository, 'create_workflow'):
                try:
                    workflow_id = self.repository.create_workflow(**workflow_data)
                except Exception as e:
                    self.logger.warning(f"Could not store workflow in repository: {e}")
            
            if workflow_id:
                self.current_workflow_id = workflow_id
                self.logger.info(f"✅ Created comprehensive workflow: {workflow_id}")
            else:
                # Store workflow locally if database storage fails
                self.current_workflow_id = f"local_{len(workflow_steps)}_phase_workflow"
                self.logger.info(f"✅ Created local comprehensive workflow with {len(workflow_steps)} phases")
            
            # Log workflow details
            self.logger.info(f"📋 Workflow Overview:")
            self.logger.info(f"   • Total Phases: {len(workflow_steps)}")
            self.logger.info(f"   • Estimated Duration: {total_estimated_time // 60} minutes")
            self.logger.info(f"   • Parallel Phases: {len([s for s in workflow_steps if s.get('parallel_execution', False)])}")
            self.logger.info(f"   • Analysis Depth: Comprehensive")
            self.logger.info(f"   • AI Enhanced: Yes")
            
            # Store workflow details for execution
            self.workflow_config = workflow_data
            
        except Exception as e:
            self.logger.error(f"Error creating comprehensive workflow: {e}")
            # Set basic workflow configuration as backup
            self.workflow_config = {
                "workflow_name": "Comprehensive AI-Coordinated Documentation Generation",
                "workflow_steps": workflow_steps if 'workflow_steps' in locals() else [],
                "estimated_duration_seconds": total_estimated_time if 'total_estimated_time' in locals() else 1800
            }
            self.current_workflow_id = "local_comprehensive_workflow"
    
    async def execute_workflow(self, repository_path: str) -> Dict[str, Any]:
        """
        Execute the complete coordinated workflow.
        
        Args:
            repository_path: Path to the repository to analyze
            
        Returns:
            Execution results
        """
        try:
            self.is_running = True
            start_time = time.time()
            
            self.logger.info("🚀 Starting comprehensive coordinated workflow execution")
            
            # Phase 1: Deep Repository Discovery
            discovery_results = await self._execute_discovery_phase(repository_path)
            
            # Phase 2: Multi-Dimensional Analysis (parallel execution)
            analysis_results = await self._execute_comprehensive_analysis_phase(repository_path, discovery_results)
            
            # Phase 3: Intelligent Planning
            plan = await self._execute_intelligent_planning_phase(analysis_results)
            
            # Phase 4: Multi-Format Content Generation (parallel execution)
            content_results = await self._execute_comprehensive_generation_phase(plan, analysis_results)
            
            # Phase 5: Quality Assurance and Enhancement
            enhanced_results = await self._execute_quality_enhancement_phase(content_results)
            
            # Phase 6: Final Assembly and Optimization
            output_results = await self._execute_final_assembly_phase(enhanced_results)
            
            # Finalize session
            execution_time = time.time() - start_time
            await self._finalize_session(True, execution_time, output_results)
            
            self.logger.info(f"✅ Workflow completed successfully in {execution_time:.2f} seconds")
            
            return {
                'success': True,
                'execution_time': execution_time,
                'discovery_results': discovery_results,
                'analysis_results': analysis_results,
                'plan': plan,
                'content_results': content_results,
                'enhanced_results': enhanced_results,
                'output_results': output_results,
                'workflow_stats': {
                    'total_phases': 6,
                    'parallel_phases': 2,
                    'tasks_executed': len(self.tasks),
                    'workflow_version': '2.0'
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Workflow execution failed: {e}")
            await self._finalize_session(False, time.time() - start_time, {"error": str(e)})
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            self.is_running = False
    
    async def _execute_discovery_phase(self, repository_path: str) -> Dict[str, Any]:
        """Execute the deep repository discovery phase."""
        self.logger.info("🔍 Executing deep repository discovery phase")
        
        # Create discovery tasks
        tasks = []
        
        # Repository structure analysis
        structure_task = await self.create_task(
            task_type=TaskType.ANALYSIS,
            description="Deep repository structure and technology stack analysis",
            assigned_component="code_analyzer",
            input_data={
                "repository_path": repository_path,
                "analysis_type": "structure_discovery",
                "depth": "comprehensive"
            },
            priority=5
        )
        if structure_task:
            tasks.append(structure_task)
        
        # Technology stack detection
        tech_task = await self.create_task(
            task_type=TaskType.AI_ANALYSIS,
            description="Technology stack and framework detection",
            assigned_component="ai_analyzer",
            input_data={
                "repository_path": repository_path,
                "analysis_type": "technology_detection",
                "include_dependencies": True
            },
            priority=4
        )
        if tech_task:
            tasks.append(tech_task)
        
        # Execute discovery tasks concurrently
        results = await self._execute_tasks_concurrently(tasks)
        
        # Combine discovery results
        combined_results = {
            'repository_structure': results.get(structure_task, {}) if structure_task else {},
            'technology_stack': results.get(tech_task, {}) if tech_task else {},
            'discovery_metadata': {
                'phase': 'discovery',
                'depth': 'comprehensive',
                'tasks_executed': len(tasks)
            }
        }
        
        self.logger.info("✅ Discovery phase completed")
        return combined_results
    
    async def _execute_comprehensive_analysis_phase(self, repository_path: str, discovery_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the comprehensive multi-dimensional analysis phase."""
        self.logger.info("📊 Executing comprehensive analysis phase")
        
        # Create comprehensive analysis tasks
        tasks = []
        
        # Deep code analysis
        code_task = await self.create_task(
            task_type=TaskType.CODE_ANALYSIS,
            description="Multi-dimensional code analysis with AST, complexity, and patterns",
            assigned_component="code_analyzer",
            input_data={
                "repository_path": repository_path,
                "discovery_context": discovery_results,
                "analysis_depth": "comprehensive",
                "include_patterns": True,
                "include_complexity": True,
                "include_dependencies": True
            },
            priority=5
        )
        if code_task:
            tasks.append(code_task)
        
        # Advanced AI/ML analysis
        ai_task = await self.create_task(
            task_type=TaskType.AI_ANALYSIS,
            description="Advanced AI/ML component intelligence and pipeline analysis",
            assigned_component="ai_analyzer",
            input_data={
                "repository_path": repository_path,
                "discovery_context": discovery_results,
                "analysis_type": "comprehensive",
                "include_models": True,
                "include_pipelines": True,
                "include_data_flow": True
            },
            priority=4
        )
        if ai_task:
            tasks.append(ai_task)
        
        # Comprehensive quality analysis
        quality_task = await self.create_task(
            task_type=TaskType.QUALITY_ANALYSIS,
            description="Advanced quality assessment with security, performance, and maintainability",
            assigned_component="quality_analyzer",
            input_data={
                "repository_path": repository_path,
                "discovery_context": discovery_results,
                "include_security": True,
                "include_performance": True,
                "include_maintainability": True,
                "include_test_coverage": True,
                "include_technical_debt": True
            },
            priority=3
        )
        if quality_task:
            tasks.append(quality_task)
        
        # Execute analysis tasks concurrently
        results = await self._execute_tasks_concurrently(tasks)
        
        # Combine comprehensive analysis results
        combined_results = {
            'comprehensive_code_analysis': results.get(code_task, {}) if code_task else {},
            'advanced_ai_analysis': results.get(ai_task, {}) if ai_task else {},
            'comprehensive_quality_analysis': results.get(quality_task, {}) if quality_task else {},
            'analysis_metadata': {
                'phase': 'comprehensive_analysis',
                'depth': 'advanced',
                'parallel_execution': True,
                'tasks_executed': len(tasks),
                'discovery_integration': True
            }
        }
        
        self.logger.info("✅ Comprehensive analysis phase completed")
        return combined_results
    
    async def _execute_intelligent_planning_phase(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the intelligent documentation planning phase."""
        self.logger.info("🧠 Executing intelligent planning phase")
        
        # Create intelligent planning task
        planning_task = await self.create_task(
            task_type=TaskType.DECISION_MAKING,
            description="AI-driven comprehensive documentation planning and structure design",
            assigned_component="coordinator",
            input_data={
                "analysis_results": analysis_results,
                "planning_depth": "comprehensive",
                "include_audience_analysis": True,
                "include_content_prioritization": True,
                "include_narrative_planning": True,
                "include_visual_planning": True,
                "include_interactive_planning": True
            },
            priority=5
        )
        
        if planning_task:
            # Execute intelligent planning
            plan_results = await self._execute_task(planning_task)
            
            # Make comprehensive AI-driven decisions about documentation
            plan = await self._make_comprehensive_documentation_plan(analysis_results)
            
            self.logger.info("✅ Intelligent planning phase completed")
            return plan
        else:
            self.logger.error("Failed to create intelligent planning task")
            return await self._make_comprehensive_documentation_plan(analysis_results)
    
    async def _execute_comprehensive_generation_phase(self, plan: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the comprehensive multi-format content generation phase."""
        self.logger.info("📝 Executing comprehensive generation phase")
        
        tasks = []
        
        # Multi-format documentation generation
        doc_task = await self.create_task(
            task_type=TaskType.DOCUMENTATION_GENERATION,
            description="Generate comprehensive multi-format documentation",
            assigned_component="documentation_generator",
            input_data={
                "plan": plan,
                "analysis_results": analysis_results,
                "formats": ["api_docs", "architecture_docs", "user_guide", "developer_guide", "deployment_guide", "troubleshooting"],
                "quality_level": "production",
                "include_examples": True,
                "include_tutorials": True
            },
            priority=5
        )
        if doc_task:
            tasks.append(doc_task)
        
        # Advanced visualization generation
        diagram_task = await self.create_task(
            task_type=TaskType.DIAGRAM_GENERATION,
            description="Generate comprehensive visual documentation elements",
            assigned_component="diagram_generator",
            input_data={
                "plan": plan,
                "analysis_results": analysis_results,
                "diagram_types": ["architecture", "data_flow", "api_interactions", "deployment", "dependencies", "user_journeys"],
                "interactive": True,
                "high_resolution": True
            },
            priority=4
        )
        if diagram_task:
            tasks.append(diagram_task)
        
        # Execute generation tasks concurrently
        results = await self._execute_tasks_concurrently(tasks)
        
        combined_results = {
            'comprehensive_documentation': results.get(doc_task, {}) if doc_task else {},
            'advanced_visualizations': results.get(diagram_task, {}) if diagram_task else {},
            'generation_metadata': {
                'phase': 'comprehensive_generation',
                'parallel_execution': True,
                'multi_format': True,
                'production_quality': True,
                'tasks_executed': len(tasks)
            }
        }
        
        self.logger.info("✅ Comprehensive generation phase completed")
        return combined_results
    
    async def _execute_quality_enhancement_phase(self, content_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the quality assurance and enhancement phase."""
        self.logger.info("🔍 Executing quality enhancement phase")
        
        # Create quality enhancement task
        quality_task = await self.create_task(
            task_type=TaskType.QUALITY_ANALYSIS,
            description="Comprehensive quality assurance and content enhancement",
            assigned_component="quality_analyzer",
            input_data={
                "content_results": content_results,
                "quality_checks": [
                    "content_accuracy_validation",
                    "consistency_check", 
                    "accessibility_compliance",
                    "seo_optimization",
                    "cross_reference_validation",
                    "broken_link_detection",
                    "content_freshness_analysis"
                ],
                "enhancement_level": "production",
                "compliance_standards": ["wcag_aa", "seo_best_practices"]
            },
            priority=4
        )
        
        if quality_task:
            # Execute quality enhancement
            quality_results = await self._execute_task(quality_task)
            
            enhanced_results = {
                'original_content': content_results,
                'quality_enhancements': quality_results,
                'enhancement_metadata': {
                    'phase': 'quality_enhancement',
                    'standards_applied': ['wcag_aa', 'seo_best_practices'],
                    'checks_performed': 7,
                    'enhancement_level': 'production'
                }
            }
            
            self.logger.info("✅ Quality enhancement phase completed")
            return enhanced_results
        else:
            self.logger.warning("Failed to create quality enhancement task, using original content")
            return {'original_content': content_results, 'quality_enhancements': {}}
    
    async def _execute_final_assembly_phase(self, enhanced_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the final assembly and optimization phase."""
        self.logger.info("🔧 Executing final assembly phase")
        
        tasks = []
        
        # Template processing and assembly
        template_task = await self.create_task(
            task_type=TaskType.TEMPLATE_PROCESSING,
            description="Process templates and assemble final documentation",
            assigned_component="template_processor",
            input_data={
                "enhanced_results": enhanced_results,
                "assembly_type": "comprehensive",
                "optimization_level": "production",
                "responsive_design": True,
                "performance_optimization": True
            },
            priority=4
        )
        if template_task:
            tasks.append(template_task)
        
        # Final file operations and deployment preparation
        file_task = await self.create_task(
            task_type=TaskType.FILE_OPERATIONS,
            description="Final file operations and deployment preparation",
            assigned_component="file_manager",
            input_data={
                "enhanced_results": enhanced_results,
                "deployment_ready": True,
                "asset_optimization": True,
                "compression": True,
                "cdn_preparation": True
            },
            priority=3,
            dependencies=[template_task] if template_task else []
        )
        if file_task:
            tasks.append(file_task)
        
        # Execute assembly tasks sequentially (file operations depend on template processing)
        results = await self._execute_tasks_sequentially(tasks)
        
        combined_results = {
            'template_processing': results.get(template_task, {}) if template_task else {},
            'file_operations': results.get(file_task, {}) if file_task else {},
            'assembly_metadata': {
                'phase': 'final_assembly',
                'optimization_level': 'production',
                'deployment_ready': True,
                'responsive_design': True,
                'performance_optimized': True,
                'tasks_executed': len(tasks)
            }
        }
        
        self.logger.info("✅ Final assembly phase completed")
        return combined_results
    
    async def _execute_assembly_phase(self, content_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the assembly and output phase."""
        self.logger.info("🔧 Executing assembly phase")
        
        # Template processing task
        template_task = await self.create_task(
            task_type=TaskType.TEMPLATE_PROCESSING,
            description="Process templates with generated content",
            assigned_component="template_processor",
            input_data={"content_results": content_results},
            priority=3
        )
        
        # File operations task
        file_task = await self.create_task(
            task_type=TaskType.FILE_OPERATIONS,
            description="Write output files",
            assigned_component="file_manager",
            input_data={"content_results": content_results},
            priority=2,
            dependencies=[template_task] if template_task else []
        )
        
        # Execute tasks in order
        tasks = [template_task, file_task] if template_task and file_task else []
        results = await self._execute_tasks_sequentially(tasks)
        
        combined_results = {
            'template_processing': results.get(template_task, {}) if template_task else {},
            'file_operations': results.get(file_task, {}) if file_task else {}
        }
        
        self.logger.info("✅ Assembly phase completed")
        return combined_results
    
    async def create_task(self, task_type: TaskType, description: str, assigned_component: str = "",
                         input_data: Dict[str, Any] = None, priority: int = 1,
                         parent_task_id: str = None, dependencies: List[str] = None,
                         execution_plan: Dict[str, Any] = None, metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Create a new task.
        
        Args:
            task_type: Type of task
            description: Task description
            assigned_component: Component to execute the task
            input_data: Input data for the task
            priority: Task priority
            parent_task_id: Parent task ID
            dependencies: Task dependencies
            execution_plan: Execution plan
            metadata: Additional metadata
            
        Returns:
            Task ID if successful
        """
        try:
            task_id = str(uuid.uuid4())
            
            task = Task(
                id=task_id,
                task_type=task_type,
                description=description,
                priority=priority,
                parent_task_id=parent_task_id,
                dependencies=dependencies or [],
                assigned_component=assigned_component,
                input_data=input_data or {},
                execution_plan=execution_plan or {},
                metadata=metadata or {}
            )
            
            # Store task locally
            self.tasks[task_id] = task
            
            # Store task in database
            if self.current_session_id and hasattr(self.repository, 'create_task'):
                task_data = TaskData(
                    session_id=self.current_session_id,
                    task_type=task_type.value,
                    task_description=description,
                    task_priority=priority,
                    parent_task_id=parent_task_id,
                    dependencies=dependencies or [],
                    assigned_component=assigned_component,
                    input_data=input_data or {},
                    execution_plan=execution_plan or {},
                    metadata=metadata or {}
                )
                db_task_id = self.repository.create_task(task_data)
                
                if db_task_id:
                    task.metadata['db_id'] = db_task_id
            
            self.logger.info(f"Created task: {task_id} - {description}")
            return task_id
            
        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            return None
    
    async def _execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a single task."""
        if task_id not in self.tasks:
            self.logger.error(f"Task not found: {task_id}")
            return {"success": False, "error": "Task not found"}
        
        task = self.tasks[task_id]
        
        try:
            # Update task status
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now(timezone.utc)
            await self._update_task_status(task_id, TaskStatus.IN_PROGRESS)
            
            self.logger.info(f"Executing task: {task.description}")
            
            # Get component handler
            if task.assigned_component not in self.component_registry:
                raise ValueError(f"Component not registered: {task.assigned_component}")
            
            handler = self.component_registry[task.assigned_component]
            
            # Log interaction start
            interaction_start = time.time()
            interaction_id = None
            if hasattr(self.repository, 'log_interaction'):
                interaction_data = InteractionData(
                    session_id=self.current_session_id,
                    task_id=task_id,
                    from_component="coordinator",
                    to_component=task.assigned_component,
                    interaction_type="task_execution",
                    message_content=task.description,
                    request_data=task.input_data
                )
                interaction_id = self.repository.log_interaction(interaction_data)
            
            # Execute task
            result = await handler(task.input_data)
            
            # Log interaction completion
            execution_time_ms = int((time.time() - interaction_start) * 1000)
            if hasattr(self.repository, 'log_interaction'):
                completion_data = InteractionData(
                    session_id=self.current_session_id,
                    task_id=task_id,
                    from_component=task.assigned_component,
                    to_component="coordinator",
                    interaction_type="task_result",
                    response_data=result,
                    success=result.get('success', True),
                    error_message=result.get('error', ''),
                    execution_time_ms=execution_time_ms
                )
                self.repository.log_interaction(completion_data)
            
            # Update task
            task.output_data = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now(timezone.utc)
            await self._update_task_status(task_id, TaskStatus.COMPLETED, result)
            
            self.logger.info(f"✅ Task completed: {task.description}")
            return result
            
        except Exception as e:
            # Handle task failure
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now(timezone.utc)
            await self._update_task_status(task_id, TaskStatus.FAILED, {"error": str(e)})
            
            self.logger.error(f"❌ Task failed: {task.description} - {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_tasks_concurrently(self, task_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Execute multiple tasks concurrently."""
        if not task_ids:
            return {}
        
        self.logger.info(f"Executing {len(task_ids)} tasks concurrently")
        
        # Create tasks for concurrent execution
        tasks = [self._execute_task(task_id) for task_id in task_ids]
        
        # Execute concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results to task IDs
        result_map = {}
        for i, task_id in enumerate(task_ids):
            if i < len(results):
                if isinstance(results[i], Exception):
                    result_map[task_id] = {"success": False, "error": str(results[i])}
                else:
                    result_map[task_id] = results[i]
            else:
                result_map[task_id] = {"success": False, "error": "No result"}
        
        return result_map
    
    async def _execute_tasks_sequentially(self, task_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Execute multiple tasks sequentially."""
        if not task_ids:
            return {}
        
        self.logger.info(f"Executing {len(task_ids)} tasks sequentially")
        
        result_map = {}
        for task_id in task_ids:
            result = await self._execute_task(task_id)
            result_map[task_id] = result
            
            # Stop on failure if configured
            if not result.get('success', True):
                break
        
        return result_map
    
    async def _make_comprehensive_documentation_plan(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Make comprehensive AI-driven decisions about documentation structure and content."""
        try:
            # Prepare comprehensive decision context
            context = DecisionContext(
                session_id=self.current_session_id,
                task_id=None,
                decision_type="comprehensive_documentation_planning",
                available_options=[
                    "comprehensive_multi_audience",
                    "developer_focused_deep_dive",
                    "user_centric_with_tutorials",
                    "enterprise_deployment_ready",
                    "open_source_community_driven"
                ],
                context_data=analysis_results,
                constraints={
                    "quality_level": "production",
                    "accessibility": "wcag_aa_compliant",
                    "seo_optimized": True,
                    "multi_format": True,
                    "interactive": True,
                    "performance_optimized": True
                }
            )
            
            # Create comprehensive AI prompt for decision making
            prompt = self._build_comprehensive_planning_prompt(analysis_results)
            
            # Get AI decision with extended context
            decision_start = time.time()
            ai_response = self.ai_service.analyze_with_context(
                prompt=prompt,
                context=json.dumps(analysis_results, indent=2, cls=DataclassJSONEncoder),
                max_tokens=2500
            )
            
            execution_time_ms = int((time.time() - decision_start) * 1000)
            
            # Log comprehensive decision
            if hasattr(self.repository, 'log_decision'):
                decision_data = DecisionData(
                    session_id=self.current_session_id,
                    decision_type="comprehensive_documentation_planning",
                    decision_prompt=prompt,
                    decision_response=json.dumps(ai_response, cls=DataclassJSONEncoder),
                    reasoning=ai_response.get('reasoning', ''),
                    confidence_score=ai_response.get('confidence', 0.9),
                    alternatives_considered=context.available_options,
                    context=context.context_data,
                    model_used=ai_response.get('model', 'gpt-4'),
                    tokens_used=ai_response.get('tokens_used', 0),
                    execution_time_ms=execution_time_ms
                )
                self.repository.log_decision(decision_data)
            
            # Extract comprehensive plan from AI response
            plan = {
                'approach': ai_response.get('approach', 'comprehensive_multi_audience'),
                'target_audiences': ai_response.get('target_audiences', ['developers', 'users', 'administrators', 'contributors']),
                'documentation_types': ai_response.get('documentation_types', [
                    'api_reference', 'architecture_overview', 'user_guide', 'developer_guide',
                    'deployment_guide', 'troubleshooting', 'tutorials', 'examples'
                ]),
                'content_structure': ai_response.get('content_structure', {
                    'landing_page': {'priority': 10, 'interactive': True},
                    'getting_started': {'priority': 9, 'tutorials': True},
                    'api_reference': {'priority': 8, 'interactive_explorer': True},
                    'architecture': {'priority': 7, 'diagrams': True},
                    'guides': {'priority': 6, 'step_by_step': True},
                    'examples': {'priority': 5, 'code_playground': True},
                    'troubleshooting': {'priority': 4, 'decision_tree': True},
                    'deployment': {'priority': 3, 'environment_specific': True}
                }),
                'visual_elements': ai_response.get('visual_elements', {
                    'architecture_diagrams': True,
                    'data_flow_diagrams': True,
                    'api_interaction_diagrams': True,
                    'deployment_diagrams': True,
                    'user_journey_flows': True,
                    'performance_charts': True,
                    'interactive_components': True
                }),
                'interactive_features': ai_response.get('interactive_features', {
                    'api_explorer': True,
                    'code_playground': True,
                    'configuration_wizard': True,
                    'troubleshooting_assistant': True,
                    'search_system': True,
                    'feedback_system': True
                }),
                'quality_standards': ai_response.get('quality_standards', {
                    'accessibility': 'wcag_aa',
                    'seo_optimization': True,
                    'performance_score': 95,
                    'mobile_responsive': True,
                    'cross_browser_compatible': True,
                    'load_time_target': '< 3 seconds'
                }),
                'content_priorities': ai_response.get('content_priorities', [
                    'core_functionality_documentation',
                    'getting_started_experience',
                    'api_reference_completeness',
                    'architecture_clarity',
                    'troubleshooting_coverage',
                    'deployment_guidance',
                    'performance_optimization',
                    'security_best_practices'
                ]),
                'estimated_scope': ai_response.get('estimated_scope', {
                    'total_pages': 25,
                    'api_endpoints': 50,
                    'code_examples': 100,
                    'diagrams': 15,
                    'interactive_elements': 8,
                    'tutorials': 12
                }),
                'reasoning': ai_response.get('reasoning', 'Comprehensive multi-audience approach for maximum value'),
                'implementation_strategy': ai_response.get('implementation_strategy', {
                    'phased_approach': True,
                    'parallel_development': True,
                    'continuous_integration': True,
                    'user_feedback_integration': True,
                    'analytics_tracking': True
                })
            }
            
            self.logger.info(f"📋 Comprehensive Plan Created:")
            self.logger.info(f"   • Approach: {plan['approach']}")
            self.logger.info(f"   • Target Audiences: {len(plan['target_audiences'])}")
            self.logger.info(f"   • Documentation Types: {len(plan['documentation_types'])}")
            self.logger.info(f"   • Interactive Features: {len([k for k, v in plan['interactive_features'].items() if v])}")
            self.logger.info(f"   • Estimated Pages: {plan['estimated_scope']['total_pages']}")
            
            return plan
            
        except Exception as e:
            self.logger.error(f"Error making comprehensive documentation plan: {e}")
            # Return comprehensive default plan
            return {
                'approach': 'comprehensive_multi_audience',
                'target_audiences': ['developers', 'users', 'administrators'],
                'documentation_types': ['api_reference', 'user_guide', 'architecture_overview'],
                'content_structure': {
                    'landing_page': {'priority': 10},
                    'api_reference': {'priority': 8},
                    'architecture': {'priority': 7},
                    'user_guide': {'priority': 6}
                },
                'visual_elements': {
                    'architecture_diagrams': True,
                    'api_interaction_diagrams': True
                },
                'interactive_features': {
                    'api_explorer': True,
                    'search_system': True
                },
                'quality_standards': {
                    'accessibility': 'wcag_aa',
                    'seo_optimization': True,
                    'performance_score': 90
                },
                'estimated_scope': {
                    'total_pages': 15,
                    'api_endpoints': 30,
                    'diagrams': 8
                },
                'reasoning': f'Comprehensive default plan created due to planning error: {e}'
            }
    
    def _build_comprehensive_planning_prompt(self, analysis_results: Dict[str, Any]) -> str:
        """Build comprehensive AI prompt for advanced documentation planning."""
        return f"""
Based on the comprehensive code analysis results, create the best-in-class documentation plan for maximum user value:

COMPREHENSIVE ANALYSIS RESULTS:
{json.dumps(analysis_results, indent=2, cls=DataclassJSONEncoder)}

Create a production-ready documentation plan that includes:

1. **APPROACH SELECTION**: Choose the optimal documentation approach:
   - comprehensive_multi_audience: Complete documentation serving all user types
   - developer_focused_deep_dive: Technical depth for developers and contributors
   - user_centric_with_tutorials: User experience focused with guided learning
   - enterprise_deployment_ready: Business and deployment focused
   - open_source_community_driven: Community contribution and collaboration focused

2. **TARGET AUDIENCES**: Define specific audience segments and their needs:
   - Primary audiences (developers, end users, administrators, etc.)
   - Secondary audiences (contributors, stakeholders, etc.)
   - Audience-specific content requirements and preferences

3. **DOCUMENTATION TYPES**: Specify comprehensive documentation categories:
   - API reference with interactive examples
   - Architecture overview with visual diagrams
   - User guides with step-by-step tutorials
   - Developer guides with advanced topics
   - Deployment and configuration guides
   - Troubleshooting and FAQ sections
   - Code examples and playground

4. **CONTENT STRUCTURE**: Design hierarchical content organization:
   - Landing page with clear value proposition
   - Navigation structure and information architecture
   - Content prioritization and progressive disclosure
   - Cross-references and content relationships

5. **VISUAL ELEMENTS**: Plan comprehensive visual documentation:
   - System architecture diagrams
   - Data flow and process diagrams
   - API interaction and sequence diagrams
   - Deployment and infrastructure diagrams
   - User interface mockups and screenshots
   - Performance and metrics visualizations

6. **INTERACTIVE FEATURES**: Design engaging user experiences:
   - Interactive API explorer with live testing
   - Code playground with runnable examples
   - Configuration wizard for setup guidance
   - Troubleshooting decision trees
   - Advanced search and filtering
   - User feedback and rating systems

7. **QUALITY STANDARDS**: Define production-level quality requirements:
   - Accessibility compliance (WCAG AA)
   - SEO optimization for discoverability
   - Performance targets (< 3 second load times)
   - Mobile responsiveness and cross-browser compatibility
   - Content accuracy and freshness standards

8. **CONTENT PRIORITIES**: Rank content development priorities:
   - Critical path documentation for immediate user success
   - Core functionality coverage
   - Getting started and onboarding experience
   - Advanced features and customization options
   - Integration and extensibility guidance

9. **ESTIMATED SCOPE**: Provide realistic scope estimates:
   - Total documentation pages and sections
   - API endpoints to document
   - Code examples and tutorials needed
   - Diagrams and visual elements required
   - Interactive components to develop

10. **IMPLEMENTATION STRATEGY**: Plan development and maintenance approach:
    - Phased development timeline
    - Parallel development opportunities
    - Continuous integration and updates
    - User feedback integration process
    - Analytics and usage tracking

11. **REASONING**: Provide detailed justification for all decisions based on:
    - Analysis results and codebase characteristics
    - Target audience needs and preferences
    - Industry best practices and standards
    - Competitive analysis and differentiation
    - Resource constraints and priorities

Respond in structured JSON format with comprehensive details for each section. Focus on creating documentation that will be the gold standard in its category.
"""
    
    async def _update_task_status(self, task_id: str, status: TaskStatus, output_data: Dict[str, Any] = None):
        """Update task status in database."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            
            updates = {
                'task_status': status.value
            }
            
            if output_data:
                updates['output_data'] = output_data
            
            if status == TaskStatus.FAILED and task.error_message:
                updates['error_message'] = task.error_message
            
            # Update in database
            if 'db_id' in task.metadata and hasattr(self.repository, 'update_task'):
                self.repository.update_task(task.metadata['db_id'], updates)
    
    async def _finalize_session(self, success: bool, execution_time: float, results: Dict[str, Any]):
        """Finalize the current session."""
        if self.current_session_id:
            updates = {
                'success': success,
                'metadata': {
                    'execution_time_seconds': execution_time,
                    'results_summary': results,
                    'total_tasks': len(self.tasks),
                    'completed_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                    'failed_tasks': sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
                }
            }
            
            if not success and 'error' in results:
                updates['error_message'] = results['error']
            
            if hasattr(self.repository, 'update_session'):
                self.repository.update_session(self.current_session_id, updates)
            
            # Update workflow
            if self.current_workflow_id:
                workflow_updates = {
                    'workflow_status': 'completed' if success else 'failed',
                    'actual_duration_seconds': int(execution_time)
                }
                if hasattr(self.repository, 'update_workflow'):
                    self.repository.update_workflow(self.current_workflow_id, workflow_updates)
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status."""
        if not self.current_session_id:
            return {"status": "no_active_session"}
        
        task_stats = {
            'total': len(self.tasks),
            'pending': sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
            'in_progress': sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS),
            'completed': sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
            'failed': sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        }
        
        return {
            'session_id': self.current_session_id,
            'workflow_id': self.current_workflow_id,
            'is_running': self.is_running,
            'task_stats': task_stats,
            'registered_components': list(self.component_registry.keys())
        }
