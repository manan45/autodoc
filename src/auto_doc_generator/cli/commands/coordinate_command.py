"""
Coordinate command for running the MetaGPT/AutoGPT-style coordinator.

This command provides a CLI interface for running the intelligent
coordinator that can plan, delegate, and execute complex workflows.
"""

import asyncio
import logging
import argparse
from typing import Dict, Any
from pathlib import Path

from ...core.services.coordinator_service import CoordinatorService
from ...core.repositories.repository_factory import create_default_repository
from ...core.repositories.file_repository import FileRepository
from ...core.repositories.cache_repository import CacheRepository
from ...core.services.ai_service import AIService
from ...core.adapters.component_registry import ComponentRegistry
from ..utils.output_formatter import OutputFormatter

logger = logging.getLogger(__name__)


class CoordinateCommand:
    """
    Command for running coordinated documentation generation.
    
    This command uses the MetaGPT/AutoGPT-style coordinator to intelligently
    plan and execute documentation generation workflows.
    """
    
    def __init__(self, config: Dict[str, Any], output_formatter: OutputFormatter):
        """
        Initialize coordinate command.
        
        Args:
            config: Configuration dictionary
            output_formatter: Output formatter for results
        """
        self.config = config
        self.output_formatter = output_formatter
        self.logger = logging.getLogger(__name__)
        
        # Initialize repositories
        self.file_repository = FileRepository()
        self.cache_repository = CacheRepository(config.get('cache', {}))
        self.repository = create_default_repository(config)
        
        # Initialize AI service
        self.ai_service = AIService(
            file_repository=self.file_repository,
            cache_repository=self.cache_repository,
            config=config
        )
        
        # Initialize coordinator service
        self.coordinator_service = CoordinatorService(
            file_repository=self.file_repository,
            cache_repository=self.cache_repository,
            repository=self.repository,
            ai_service=self.ai_service,
            config=config
        )
        
        # Initialize component registry and register components
        self.component_registry = ComponentRegistry(config)
        self._register_components()
    
    def _register_components(self):
        """Register components with the coordinator."""
        # Get all component handlers from registry
        for component_name, handler in self.component_registry.component_handlers.items():
            self.coordinator_service.register_component(component_name, handler)
        
        self.logger.info(f"Registered {len(self.component_registry.component_handlers)} components with coordinator")
    
    async def execute_async(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Execute the coordinate command asynchronously.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Execution results
        """
        try:
            repository_path = Path(args.repo).resolve()
            output_path = Path(args.output).resolve()
            
            self.logger.info("🤖 Starting coordinated documentation generation")
            self.logger.info(f"📁 Repository: {repository_path}")
            self.logger.info(f"📊 Output: {output_path}")
            
            # Check repository availability
            repo_type = self.repository._get_database_type().value
            if self.repository.is_available():
                self.logger.info(f"✅ {repo_type.title()} repository enabled")
            else:
                self.logger.warning(f"⚠️  {repo_type.title()} repository disabled")
            
            # Start coordinated session
            session_id = await self.coordinator_service.start_session(
                repository_path=str(repository_path),
                session_type="coordinated_generation",
                output_format=getattr(args, 'format', 'html'),
                output_path=str(output_path)
            )
            
            if not session_id:
                return {
                    'success': False,
                    'error': 'Failed to start coordinated session',
                    'stats': {}
                }
            
            self.logger.info(f"🚀 Started session: {session_id}")
            
            # Execute coordinated workflow
            results = await self.coordinator_service.execute_workflow(str(repository_path))
            
            # Get session status
            session_status = self.coordinator_service.get_session_status()
            
            # Prepare results
            execution_results = {
                'success': results.get('success', False),
                'session_id': session_id,
                'execution_time': results.get('execution_time', 0),
                'workflow_results': results,
                'session_status': session_status,
                'stats': {
                    'total_tasks': session_status.get('task_stats', {}).get('total', 0),
                    'completed_tasks': session_status.get('task_stats', {}).get('completed', 0),
                    'failed_tasks': session_status.get('task_stats', {}).get('failed', 0),
                    'components_used': len(session_status.get('registered_components', [])),
                    'repository_type': self.repository._get_database_type().value,
                    'repository_enabled': self.repository.is_available()
                }
            }
            
            if results.get('success'):
                self.logger.info("✅ Coordinated workflow completed successfully")
            else:
                self.logger.error(f"❌ Coordinated workflow failed: {results.get('error', 'Unknown error')}")
            
            return execution_results
            
        except Exception as e:
            self.logger.exception(f"Error in coordinate command: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': {}
            }
    
    def execute(self, args: argparse.Namespace) -> Dict[str, Any]:
        """
        Execute the coordinate command.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            Execution results
        """
        try:
            # Run the async execution
            return asyncio.run(self.execute_async(args))
            
        except Exception as e:
            self.logger.exception(f"Error running coordinate command: {e}")
            return {
                'success': False,
                'error': str(e),
                'stats': {}
            }
    
    def get_component_status(self) -> Dict[str, Any]:
        """
        Get status of registered components.
        
        Returns:
            Component status information
        """
        return {
            'registry_status': self.component_registry.get_registry_status(),
            'coordinator_status': self.coordinator_service.get_session_status(),
            'repository_available': self.repository.is_available(),
            'repository_type': self.repository._get_database_type().value,
            'ai_service_available': self.ai_service is not None
        }
    
    async def test_components(self) -> Dict[str, Any]:
        """
        Test all registered components.
        
        Returns:
            Component test results
        """
        test_results = {}
        
        # Test input data
        test_input = {
            'repository_path': '.',
            'test_mode': True
        }
        
        for component_name, handler in self.component_registry.component_handlers.items():
            try:
                self.logger.info(f"Testing component: {component_name}")
                
                # Run component test
                result = await handler(test_input)
                
                test_results[component_name] = {
                    'success': result.get('success', False),
                    'execution_time': result.get('execution_time', 0),
                    'error': result.get('error', None)
                }
                
            except Exception as e:
                test_results[component_name] = {
                    'success': False,
                    'execution_time': 0,
                    'error': str(e)
                }
        
        return test_results
