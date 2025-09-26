"""
Documentation generation service.

This service orchestrates the documentation generation process,
coordinating between different generators and managing the overall workflow.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

from ..repositories.file_repository import FileRepository
from ..repositories.cache_repository import CacheRepository
from ...generators.documentation.unified_html_generator import UnifiedHTMLGenerator
from ...generators.documentation.markdown_generator import MarkdownGenerator


class DocumentationService:
    """
    Service that orchestrates documentation generation.
    
    This service coordinates between different generators to create
    comprehensive documentation from analysis results.
    """
    
    def __init__(self, file_repository: FileRepository, 
                 cache_repository: CacheRepository, config: Dict[str, Any]):
        """
        Initialize documentation service.
        
        Args:
            file_repository: File operations repository
            cache_repository: Caching repository
            config: Configuration dictionary
        """
        self.file_repository = file_repository
        self.cache_repository = cache_repository
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize generators based on config
        self.generators = {}
        self._initialize_generators()
    
    def _initialize_generators(self):
        """Initialize documentation generators based on configuration."""
        doc_config = self.config.get('documentation', {})
        
        # HTML generator
        if doc_config.get('html', {}).get('enabled', True):
            self.generators['html'] = UnifiedHTMLGenerator(
                self.config,
                template_dir=doc_config.get('html', {}).get('template_dir', None),
                output_dir=doc_config.get('output_dir', 'docs')
            )
        
        # Markdown generator
        if doc_config.get('markdown', {}).get('enabled', False):
            self.generators['markdown'] = MarkdownGenerator(
                self.config,
                output_dir=doc_config.get('output_dir', 'docs')
            )
        
        self.logger.info(f"Initialized {len(self.generators)} documentation generators")
    
    def generate_documentation(self, analysis_data: Dict[str, Any], 
                             output_format: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate documentation from analysis data.
        
        Args:
            analysis_data: Combined analysis results from all analyzers
            output_format: Specific format to generate (html, markdown, or None for all)
            
        Returns:
            Dictionary containing generation results
        """
        self.logger.info("Starting documentation generation")
        
        results = {
            'success': True,
            'generated_formats': [],
            'output_paths': {},
            'errors': [],
            'stats': {
                'total_pages': 0,
                'total_assets': 0
            }
        }
        
        try:
            # Determine which generators to use
            generators_to_use = {}
            if output_format:
                if output_format in self.generators:
                    generators_to_use[output_format] = self.generators[output_format]
                else:
                    raise ValueError(f"Unknown output format: {output_format}")
            else:
                generators_to_use = self.generators
            
            # Generate documentation for each format
            for format_name, generator in generators_to_use.items():
                try:
                    self.logger.info(f"Generating {format_name} documentation")
                    
                    # Generate documentation
                    generation_result = generator.generate(analysis_data)
                    
                    if generation_result.get('success', True):
                        results['generated_formats'].append(format_name)
                        
                        # Save generated documentation
                        documentation = generation_result.get('results', {}).get('documentation', {})
                        if documentation:
                            output_dir = generation_result.get('results', {}).get('output_directory')
                            if output_dir:
                                results['output_paths'][format_name] = output_dir
                                generator.save_documentation(documentation)
                                
                                # Update stats
                                results['stats']['total_pages'] += len(documentation)
                        
                        self.logger.info(f"Successfully generated {format_name} documentation")
                    else:
                        error_msg = f"Failed to generate {format_name} documentation"
                        results['errors'].append(error_msg)
                        self.logger.error(error_msg)
                        
                except Exception as e:
                    error_msg = f"Error generating {format_name} documentation: {str(e)}"
                    results['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            # Update success status
            results['success'] = len(results['generated_formats']) > 0
            
            self.logger.info(f"Documentation generation completed. Generated formats: {results['generated_formats']}")
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Documentation generation failed: {str(e)}")
            self.logger.error(f"Documentation generation failed: {e}")
        
        return results
    
    def get_available_formats(self) -> List[str]:
        """
        Get list of available documentation formats.
        
        Returns:
            List of available format names
        """
        return list(self.generators.keys())
    
    def validate_analysis_data(self, analysis_data: Dict[str, Any]) -> bool:
        """
        Validate that analysis data contains required fields for documentation.
        
        Args:
            analysis_data: Analysis data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['code_analysis']
        
        for field in required_fields:
            if field not in analysis_data:
                self.logger.warning(f"Missing required field for documentation: {field}")
                return False
        
        return True
    
    def get_generation_status(self) -> Dict[str, Any]:
        """
        Get status of documentation generation capabilities.
        
        Returns:
            Dictionary with status information
        """
        return {
            'available_generators': list(self.generators.keys()),
            'total_generators': len(self.generators),
            'config': self.config.get('documentation', {}),
            'ready': len(self.generators) > 0
        }
