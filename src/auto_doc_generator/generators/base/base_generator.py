"""
Base generator class providing common functionality.

This module defines the base class that all generators should inherit from,
providing common patterns and utilities for documentation generation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
from datetime import datetime

from ...core.models.documentation_models import DocumentationResult, OutputFormat

logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """
    Abstract base class for all documentation generators.
    
    This class provides common functionality and defines the interface
    that all generators must implement.
    """
    
    def __init__(
        self, 
        template_dir: str = "templates",
        output_dir: str = "docs", 
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the generator.
        
        Args:
            template_dir: Directory containing templates
            output_dir: Directory for output files
            config: Optional configuration dictionary
        """
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def generate(self, analysis_data: Dict[str, Any]) -> DocumentationResult:
        """
        Generate documentation from analysis data.
        
        Args:
            analysis_data: Analysis results to generate documentation from
            
        Returns:
            DocumentationResult containing generation results
        """
        pass
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value with dot notation support.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def write_file(self, file_path: Path, content: str, encoding: str = 'utf-8') -> None:
        """
        Write content to a file.
        
        Args:
            file_path: Path to write to
            content: Content to write
            encoding: File encoding
        """
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            self.logger.debug(f"Wrote file: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to write file {file_path}: {e}")
            raise
    
    def read_template(self, template_name: str, encoding: str = 'utf-8') -> str:
        """
        Read a template file.
        
        Args:
            template_name: Name of the template file
            encoding: File encoding
            
        Returns:
            Template content
        """
        template_path = self.template_dir / template_name
        
        try:
            with open(template_path, 'r', encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            self.logger.warning(f"Template not found: {template_path}")
            return ""
        except Exception as e:
            self.logger.error(f"Failed to read template {template_path}: {e}")
            raise
    
    def copy_static_files(self, source_dir: Path, target_dir: Path) -> None:
        """
        Copy static files (CSS, JS, images) to output directory.
        
        Args:
            source_dir: Source directory containing static files
            target_dir: Target directory to copy files to
        """
        import shutil
        
        if not source_dir.exists():
            self.logger.warning(f"Static source directory not found: {source_dir}")
            return
        
        try:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            
            shutil.copytree(source_dir, target_dir)
            self.logger.debug(f"Copied static files: {source_dir} -> {target_dir}")
            
        except Exception as e:
            self.logger.error(f"Failed to copy static files: {e}")
            raise
    
    def create_result_template(self) -> Dict[str, Any]:
        """
        Create a standard result template for generators.
        
        Returns:
            Dictionary with standard result structure
        """
        return {
            'generator': self.__class__.__name__,
            'version': '1.0.0',
            'timestamp': None,  # Should be set by implementing class
            'results': {},
            'metadata': {},
            'errors': [],
            'warnings': []
        }
    
    def create_documentation_result(self, output_format: OutputFormat) -> DocumentationResult:
        """
        Create a DocumentationResult with basic information.
        
        Args:
            output_format: Output format for the documentation
            
        Returns:
            Initialized DocumentationResult
        """
        return DocumentationResult(
            output_directory=str(self.output_dir),
            format=output_format,
            generated_at=datetime.now()
        )
    
    def validate_analysis_data(self, analysis_data: Dict[str, Any]) -> List[str]:
        """
        Validate analysis data for generation.
        
        Args:
            analysis_data: Analysis data to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not isinstance(analysis_data, dict):
            errors.append("Analysis data must be a dictionary")
            return errors
        
        # Check for required sections
        required_sections = ['overview', 'modules']
        for section in required_sections:
            if section not in analysis_data:
                errors.append(f"Missing required section: {section}")
        
        # Validate overview
        overview = analysis_data.get('overview', {})
        if not isinstance(overview, dict):
            errors.append("Overview section must be a dictionary")
        
        # Validate modules
        modules = analysis_data.get('modules', [])
        if not isinstance(modules, list):
            errors.append("Modules section must be a list")
        
        return errors
    
    def log_generation_start(self, target: str) -> None:
        """Log the start of generation."""
        self.logger.info(f"Starting {self.__class__.__name__} generation for: {target}")
    
    def log_generation_complete(self, target: str, files_generated: int = None) -> None:
        """Log the completion of generation."""
        if files_generated is not None:
            self.logger.info(f"Completed {self.__class__.__name__} generation for {target}: {files_generated} files")
        else:
            self.logger.info(f"Completed {self.__class__.__name__} generation for {target}")
    
    def format_timestamp(self, timestamp: datetime = None) -> str:
        """
        Format timestamp for display.
        
        Args:
            timestamp: Timestamp to format (default: now)
            
        Returns:
            Formatted timestamp string
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file system usage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        import re
        
        # Replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = 'untitled'
        
        return sanitized
