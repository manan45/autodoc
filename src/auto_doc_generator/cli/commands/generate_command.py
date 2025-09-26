"""
Generate command implementation.

This module implements the generate command for the CLI.
"""

import argparse
from typing import Dict, Any
from pathlib import Path

from ...core.services.analysis_service import AnalysisService
from ..utils.output_formatter import OutputFormatter


class GenerateCommand:
    """Command for generating documentation."""
    
    def __init__(self, analysis_service: AnalysisService, output_formatter: OutputFormatter):
        """
        Initialize generate command.
        
        Args:
            analysis_service: Service for performing analysis
            output_formatter: Formatter for CLI output
        """
        self.analysis_service = analysis_service
        self.formatter = output_formatter
    
    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Execute the generate command.
        
        Args:
            args: Command line arguments
            
        Returns:
            Dictionary with execution results
        """
        try:
            from datetime import datetime
            from ...core.services.documentation_service import DocumentationService
            from ...core.services.ai_service import AIService
            from ...core.services.knowledge_graph_service import KnowledgeGraphService
            from ...infrastructure.vector_db import VectorDatabase
            from ...infrastructure.supabase_client import SupabaseClient
            from ...generators.documentation.unified_html_generator import UnifiedHTMLGenerator
            
            repo_path = Path(args.repo).resolve()
            output_path = Path(args.output).resolve()
            
            self.formatter.print_header("DOCUMENTATION GENERATION")
            self.formatter.print_info(f"Repository: {repo_path}")
            self.formatter.print_info(f"Output: {output_path}")
            
            start_time = datetime.now()
            
            # Step 1: Run analysis
            self.formatter.print_info("Running codebase analysis...")
            analysis_result = self.analysis_service.analyze_codebase(str(repo_path))
            
            # Convert analysis result to dictionary format
            if hasattr(analysis_result, 'to_dict'):
                analysis_data = analysis_result.to_dict()
            else:
                analysis_data = analysis_result
            
            # Step 2: Initialize enhanced services
            self.formatter.print_info("Initializing enhanced services...")
            
            # Initialize vector database
            vector_db = None
            try:
                vector_db = VectorDatabase(
                    db_path=str(output_path / "vector_db"),
                    collection_name="code_analysis"
                )
                self.formatter.print_success("Vector database initialized")
            except Exception as e:
                self.formatter.print_warning(f"Vector database initialization failed: {e}")
            
            # Initialize AI service
            ai_service = None
            try:
                ai_service = AIService(
                    file_repository=self.analysis_service.file_repository,
                    cache_repository=self.analysis_service.cache_repository,
                    config=self.analysis_service.config
                )
                self.formatter.print_success("AI service initialized")
            except Exception as e:
                self.formatter.print_warning(f"AI service initialization failed: {e}")
            
            # Initialize knowledge graph service
            kg_service = None
            if ai_service and vector_db:
                try:
                    kg_service = KnowledgeGraphService(
                        ai_service=ai_service,
                        vector_db=vector_db
                    )
                    self.formatter.print_success("Knowledge graph service initialized")
                except Exception as e:
                    self.formatter.print_warning(f"Knowledge graph service initialization failed: {e}")
            
            # Initialize Supabase client
            supabase_client = None
            try:
                supabase_client = SupabaseClient()
                if supabase_client.is_initialized():
                    self.formatter.print_success("Supabase client initialized")
                else:
                    self.formatter.print_warning("Supabase client not configured")
            except Exception as e:
                self.formatter.print_warning(f"Supabase client initialization failed: {e}")
            
            # Step 3: Generate documentation
            self.formatter.print_info("Generating enhanced HTML documentation...")
            
            html_generator = UnifiedHTMLGenerator(
                config={},
                template_dir=None,
                output_dir=str(output_path),
                vector_db=vector_db,
                knowledge_graph_service=kg_service,
                supabase_client=supabase_client
            )
            
            generation_result = html_generator.generate(analysis_data)
            
            # Step 4: Store generation session in Supabase
            if supabase_client and supabase_client.is_initialized():
                try:
                    session_data = {
                        'repository_path': str(repo_path),
                        'type': 'full_generation',
                        'start_time': start_time.isoformat(),
                        'end_time': datetime.now().isoformat(),
                        'duration': (datetime.now() - start_time).total_seconds(),
                        'total_files': analysis_data.get('total_files', 0),
                        'total_functions': analysis_data.get('total_functions', 0),
                        'total_classes': analysis_data.get('total_classes', 0),
                        'pages_generated': len(generation_result['results'].get('documentation', {})) if generation_result['success'] else 0,
                        'templates_used': list(generation_result['results'].get('documentation', {}).keys()) if generation_result['success'] else [],
                        'success': generation_result['success'],
                        'error': ', '.join(generation_result['errors']) if generation_result['errors'] else '',
                        'metadata': generation_result['metadata'],
                        'output_format': args.format or 'html',
                        'output_path': str(output_path)
                    }
                    
                    supabase_client.store_generation_session(session_data)
                    self.formatter.print_success("Generation session stored in Supabase")
                except Exception as e:
                    self.formatter.print_warning(f"Failed to store session in Supabase: {e}")
            
            if generation_result['success']:
                pages_generated = len(generation_result['results'].get('documentation', {}))
                self.formatter.print_success(f"Documentation generated successfully!")
                self.formatter.print_info(f"Generated {pages_generated} pages")
                self.formatter.print_info(f"Output directory: {output_path}")
                
                return {
                    'success': True,
                    'analysis_result': analysis_result,
                    'generation_result': generation_result,
                    'stats': {
                        'pages_generated': pages_generated,
                        'diagrams_created': 0,  # TODO: Implement diagram generation
                        'output_format': args.format or 'html',
                        'vector_db_used': bool(vector_db),
                        'knowledge_graph_used': bool(kg_service),
                        'supabase_used': bool(supabase_client and supabase_client.is_initialized())
                    }
                }
            else:
                error_msg = ', '.join(generation_result['errors']) if generation_result['errors'] else "Unknown error"
                self.formatter.print_error(f"Documentation generation failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'analysis_result': analysis_result
                }
            
        except Exception as e:
            self.formatter.print_error(f"Generation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
