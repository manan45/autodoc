"""
Generator adapter for coordinator integration.

This adapter provides a standardized interface for the coordinator
to interact with various generators in the system.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from ...generators.documentation.unified_html_generator import UnifiedHTMLGenerator
from ...generators.documentation.markdown_generator import MarkdownGenerator
from ...generators.diagrams.architecture_diagrams import ArchitectureDiagramGenerator
from ...generators.quality.quality_reports import QualityReportGenerator
from ...infrastructure.vector_db import VectorDatabase
from ...infrastructure.supabase_client import SupabaseClient
from ..services.knowledge_graph_service import KnowledgeGraphService
from ..services.ai_service import AIService

logger = logging.getLogger(__name__)


class GeneratorAdapter:
    """
    Adapter that provides a unified interface for all generators.
    
    This adapter allows the coordinator to interact with different
    generators through a consistent async interface.
    """
    
    def __init__(self, config: Dict[str, Any], ai_service: Optional[AIService] = None):
        """
        Initialize generator adapter with database services.
        
        Args:
            config: Configuration dictionary
            ai_service: Optional AI service for enhanced features
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ai_service = ai_service
        
        # Initialize database services
        self._initialize_database_services()
        
        # Initialize generators
        self._initialize_generators()
    
    def _initialize_database_services(self):
        """Initialize database and AI services for enhanced generator functionality."""
        try:
            # Initialize Vector Database
            self.vector_db = None
            vector_config = self.config.get('vector_db', {})
            if vector_config.get('enabled', False):
                try:
                    self.vector_db = VectorDatabase(vector_config)
                    self.logger.info("Vector database initialized for generators")
                except Exception as e:
                    self.logger.warning(f"Vector database initialization failed: {e}")
            
            # Get Supabase client instance if available
            self.supabase_client = None
            try:
                if SupabaseClient.is_initialized():
                    self.supabase_client = SupabaseClient()  # Get the instance, not raw client
                    self.logger.info("Supabase client instance available for generators")
                else:
                    self.logger.info("Supabase client not initialized")
            except Exception as e:
                self.logger.warning(f"Failed to get Supabase client: {e}")
            
            # Initialize Knowledge Graph Service
            self.knowledge_graph_service = None
            kg_config = self.config.get('knowledge_graph', {})
            if kg_config.get('enabled', True) and (self.ai_service or self.vector_db):
                try:
                    self.knowledge_graph_service = KnowledgeGraphService(
                        ai_service=self.ai_service,
                        vector_db=self.vector_db,
                        config=self.config
                    )
                    self.logger.info("Knowledge graph service initialized for generators")
                except Exception as e:
                    self.logger.warning(f"Knowledge graph service initialization failed: {e}")
            
            self.logger.info("Database services initialization completed")
            
        except Exception as e:
            self.logger.error(f"Error initializing database services: {e}")
            # Set defaults
            self.vector_db = None
            self.supabase_client = None
            self.knowledge_graph_service = None
    
    def _initialize_generators(self):
        """Initialize all available generators."""
        try:
            # Get nested config sections
            doc_config = self.config.get('documentation', {})
            
            # Documentation generators
            self.html_generator = UnifiedHTMLGenerator(
                config=self.config,
                template_dir=doc_config.get('html', {}).get('template_dir', None),
                output_dir=doc_config.get('output_dir', 'docs'),
                vector_db=self.vector_db,
                knowledge_graph_service=self.knowledge_graph_service,
                supabase_client=self.supabase_client
            )
            self.markdown_generator = MarkdownGenerator(
                self.config,
                output_dir=doc_config.get('output_dir', 'docs')
            )
            
            # Diagram generators
            self.architecture_diagram_generator = ArchitectureDiagramGenerator(self.config)
            
            # Quality generators  
            self.quality_report_generator = QualityReportGenerator(
                self.config,
                output_dir=doc_config.get('output_dir', 'docs')
            )
            
            self.logger.info("All generators initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing generators: {e}")
            # Log more details for debugging
            self.logger.error(f"Config structure: {list(self.config.keys()) if isinstance(self.config, dict) else type(self.config)}")
            raise
    
    async def generate_html_documentation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate HTML documentation.
        
        Args:
            input_data: Input data containing plan and analysis results
            
        Returns:
            Generation results
        """
        try:
            start_time = time.time()
            plan = input_data.get('plan', {})
            analysis_results = input_data.get('analysis_results', {})
            
            self.logger.info("Generating HTML documentation")
            
            # Run HTML generation in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_html_generation,
                plan,
                analysis_results
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "generation_type": "html_documentation",
                "execution_time": execution_time,
                "data": result,
                "metadata": {
                    "generator": "html_generator",
                    "pages_generated": len(result.get("pages", [])),
                    "output_path": result.get("output_path", "")
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in HTML documentation generation: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_html_generation(self, plan: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run HTML generation synchronously."""
        try:
            # Prepare generation context
            context = {
                'plan': plan,
                'analysis_results': analysis_results,
                'timestamp': time.time(),
                'format': 'html'
            }
            
            # Generate documentation
            result = self.html_generator.generate(context)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in HTML generation: {e}")
            return {"error": str(e)}
    
    async def generate_markdown_documentation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Markdown documentation.
        
        Args:
            input_data: Input data containing plan and analysis results
            
        Returns:
            Generation results
        """
        try:
            start_time = time.time()
            plan = input_data.get('plan', {})
            analysis_results = input_data.get('analysis_results', {})
            
            self.logger.info("Generating Markdown documentation")
            
            # Run Markdown generation in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_markdown_generation,
                plan,
                analysis_results
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "generation_type": "markdown_documentation",
                "execution_time": execution_time,
                "data": result,
                "metadata": {
                    "generator": "markdown_generator",
                    "files_generated": len(result.get("files", [])),
                    "output_path": result.get("output_path", "")
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in Markdown documentation generation: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_markdown_generation(self, plan: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run Markdown generation synchronously."""
        try:
            # Prepare generation context
            context = {
                'plan': plan,
                'analysis_results': analysis_results,
                'timestamp': time.time(),
                'format': 'markdown'
            }
            
            # Generate documentation
            result = self.markdown_generator.generate(context)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in Markdown generation: {e}")
            return {"error": str(e)}
    
    async def generate_architecture_diagrams(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate architecture diagrams.
        
        Args:
            input_data: Input data containing plan and analysis results
            
        Returns:
            Diagram generation results
        """
        try:
            start_time = time.time()
            plan = input_data.get('plan', {})
            analysis_results = input_data.get('analysis_results', {})
            
            self.logger.info("Generating architecture diagrams")
            
            # Run diagram generation in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_diagram_generation,
                plan,
                analysis_results
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "generation_type": "architecture_diagrams",
                "execution_time": execution_time,
                "data": result,
                "metadata": {
                    "generator": "architecture_diagram_generator",
                    "diagrams_generated": len(result.get("diagrams", [])),
                    "output_path": result.get("output_path", "")
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in architecture diagram generation: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_diagram_generation(self, plan: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run diagram generation synchronously."""
        try:
            # Prepare generation context
            context = {
                'plan': plan,
                'analysis_results': analysis_results,
                'timestamp': time.time(),
                'diagram_types': ['architecture', 'component', 'flow']
            }
            
            # Generate diagrams
            result = self.architecture_diagram_generator.generate(context)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in diagram generation: {e}")
            return {"error": str(e)}
    
    async def generate_quality_reports(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate quality reports.
        
        Args:
            input_data: Input data containing plan and analysis results
            
        Returns:
            Quality report generation results
        """
        try:
            start_time = time.time()
            plan = input_data.get('plan', {})
            analysis_results = input_data.get('analysis_results', {})
            
            self.logger.info("Generating quality reports")
            
            # Run quality report generation in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_quality_generation,
                plan,
                analysis_results
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "generation_type": "quality_reports",
                "execution_time": execution_time,
                "data": result,
                "metadata": {
                    "generator": "quality_report_generator",
                    "reports_generated": len(result.get("reports", [])),
                    "output_path": result.get("output_path", "")
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in quality report generation: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_quality_generation(self, plan: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Run quality report generation synchronously."""
        try:
            # Prepare generation context
            context = {
                'plan': plan,
                'analysis_results': analysis_results,
                'timestamp': time.time(),
                'report_types': ['metrics', 'trends', 'recommendations']
            }
            
            # Generate quality reports
            result = self.quality_report_generator.generate(context)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in quality report generation: {e}")
            return {"error": str(e)}
    
    async def process_templates(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process templates with generated content.
        
        Args:
            input_data: Input data containing content results
            
        Returns:
            Template processing results
        """
        try:
            start_time = time.time()
            content_results = input_data.get('content_results', {})
            
            self.logger.info("Processing templates")
            
            # Extract documentation and diagrams
            documentation = content_results.get('documentation', {})
            diagrams = content_results.get('diagrams', {})
            
            # Combine into template data
            template_data = {
                'documentation': documentation,
                'diagrams': diagrams,
                'timestamp': time.time(),
                'generation_metadata': {
                    'docs_success': documentation.get('success', False),
                    'diagrams_success': diagrams.get('success', False)
                }
            }
            
            # Run template processing in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_template_processing,
                template_data
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "processing_type": "template_processing",
                "execution_time": execution_time,
                "data": result,
                "metadata": {
                    "templates_processed": len(result.get("templates", [])),
                    "output_files": len(result.get("output_files", []))
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in template processing: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_template_processing(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run template processing synchronously."""
        try:
            # Process templates using HTML generator's template engine
            result = self.html_generator.process_templates(template_data)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in template processing: {e}")
            return {"error": str(e)}
    
    async def manage_file_operations(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manage file operations for output generation.
        
        Args:
            input_data: Input data containing content results
            
        Returns:
            File operation results
        """
        try:
            start_time = time.time()
            content_results = input_data.get('content_results', {})
            output_path = input_data.get('output_path', 'docs')
            
            self.logger.info(f"Managing file operations for output: {output_path}")
            
            # Run file operations in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._run_file_operations,
                content_results,
                output_path
            )
            
            execution_time = time.time() - start_time
            
            return {
                "success": True,
                "operation_type": "file_operations",
                "execution_time": execution_time,
                "data": result,
                "metadata": {
                    "files_written": len(result.get("files_written", [])),
                    "output_path": output_path
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in file operations: {e}")
            return {"success": False, "error": str(e)}
    
    def _run_file_operations(self, content_results: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """Run file operations synchronously."""
        try:
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            files_written = []
            
            # Write documentation files
            documentation = content_results.get('documentation', {})
            if 'data' in documentation:
                doc_data = documentation['data']
                if 'pages' in doc_data:
                    for page in doc_data['pages']:
                        file_path = output_dir / page['filename']
                        file_path.write_text(page['content'], encoding='utf-8')
                        files_written.append(str(file_path))
            
            # Write diagram files
            diagrams = content_results.get('diagrams', {})
            if 'data' in diagrams:
                diagram_data = diagrams['data']
                if 'diagrams' in diagram_data:
                    for diagram in diagram_data['diagrams']:
                        file_path = output_dir / diagram['filename']
                        if diagram.get('binary_content'):
                            file_path.write_bytes(diagram['binary_content'])
                        else:
                            file_path.write_text(diagram.get('content', ''), encoding='utf-8')
                        files_written.append(str(file_path))
            
            return {
                "files_written": files_written,
                "output_path": str(output_dir),
                "total_files": len(files_written)
            }
            
        except Exception as e:
            self.logger.error(f"Error in file operations: {e}")
            return {"error": str(e)}
    
    async def get_generation_summary(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a comprehensive generation summary.
        
        Args:
            input_data: Input data containing plan and analysis results
            
        Returns:
            Comprehensive generation summary
        """
        try:
            plan = input_data.get('plan', {})
            
            # Run all generations based on plan
            tasks = []
            
            # Always generate HTML documentation
            tasks.append(self.generate_html_documentation(input_data))
            
            # Generate diagrams if requested
            if plan.get('include_diagrams', True):
                tasks.append(self.generate_architecture_diagrams(input_data))
            
            # Generate quality reports if requested
            if plan.get('include_quality_metrics', True):
                tasks.append(self.generate_quality_reports(input_data))
            
            # Execute all generations
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Combine results
            summary = {
                "plan": plan,
                "generation_timestamp": time.time(),
                "html_documentation": results[0] if len(results) > 0 and not isinstance(results[0], Exception) else {"error": str(results[0]) if len(results) > 0 else "No result"},
                "diagrams": results[1] if len(results) > 1 and not isinstance(results[1], Exception) else {"error": str(results[1]) if len(results) > 1 else "Not generated"},
                "quality_reports": results[2] if len(results) > 2 and not isinstance(results[2], Exception) else {"error": str(results[2]) if len(results) > 2 else "Not generated"},
                "execution_times": {
                    "html_documentation": results[0].get("execution_time", 0) if len(results) > 0 and isinstance(results[0], dict) else 0,
                    "diagrams": results[1].get("execution_time", 0) if len(results) > 1 and isinstance(results[1], dict) else 0,
                    "quality_reports": results[2].get("execution_time", 0) if len(results) > 2 and isinstance(results[2], dict) else 0
                },
                "success_status": {
                    "html_documentation": results[0].get("success", False) if len(results) > 0 and isinstance(results[0], dict) else False,
                    "diagrams": results[1].get("success", False) if len(results) > 1 and isinstance(results[1], dict) else False,
                    "quality_reports": results[2].get("success", False) if len(results) > 2 and isinstance(results[2], dict) else False
                }
            }
            
            return {
                "success": True,
                "generation_type": "comprehensive_summary",
                "data": summary,
                "metadata": {
                    "total_execution_time": sum(summary["execution_times"].values()),
                    "generations_completed": sum(summary["success_status"].values()),
                    "generations_total": len(summary["success_status"])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive summary: {e}")
            return {"success": False, "error": str(e)}
