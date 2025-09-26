"""
Base analyzer class providing common functionality.

This module defines the base class that all analyzers should inherit from,
providing common patterns and utilities.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class BaseAnalyzer(ABC):
    """
    Abstract base class for all analyzers.
    
    This class provides common functionality and defines the interface
    that all analyzers must implement.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the analyzer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def analyze(self, target: Any) -> Dict[str, Any]:
        """
        Perform analysis on the target.
        
        Args:
            target: The target to analyze (file path, directory, etc.)
            
        Returns:
            Dictionary containing analysis results
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
    
    def should_analyze_file(self, file_path: Path) -> bool:
        """
        Check if a file should be analyzed based on include/exclude patterns and content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file should be analyzed, False otherwise
        """
        import fnmatch
        
        file_str = str(file_path)
        
        # Check exclude patterns first
        exclude_patterns = self.get_config('analysis.exclude_patterns', [])
        for pattern in exclude_patterns:
            # Use fnmatch for glob pattern matching
            if fnmatch.fnmatch(file_str, pattern) or pattern.strip('*/') in file_str:
                return False
        
        # Check include patterns
        include_patterns = self.get_config('analysis.include_patterns', ['*.py'])
        if not include_patterns:
            return True
        
        pattern_matched = False
        for pattern in include_patterns:
            if fnmatch.fnmatch(file_str, pattern) or file_path.match(pattern):
                pattern_matched = True
                break
        
        if not pattern_matched:
            return False
        
        # Check if file has meaningful content (configurable filtering)
        file_filtering = self.get_config('analysis.file_filtering', {})
        skip_empty = file_filtering.get('skip_empty_files', True)
        min_size = file_filtering.get('min_file_size_bytes', 1)
        skip_whitespace_only = file_filtering.get('skip_whitespace_only_files', True)
        
        if skip_empty or min_size > 0:
            try:
                file_size = file_path.stat().st_size
                
                if skip_empty and file_size == 0:
                    self.logger.debug(f"Skipping empty file: {file_path}")
                    return False
                
                if file_size < min_size:
                    self.logger.debug(f"Skipping file smaller than {min_size} bytes: {file_path}")
                    return False
                
                # For small files, check if they only contain whitespace
                if skip_whitespace_only and file_size < 50:  # Less than 50 bytes
                    content = self.read_file_safe(file_path)
                    if content is not None and not content.strip():
                        self.logger.debug(f"Skipping whitespace-only file: {file_path}")
                        return False
            except (OSError, IOError):
                # If we can't read the file, let the analyzer handle it
                pass
        
        return True
    
    def read_file_safe(self, file_path: Path, encoding: str = 'utf-8') -> Optional[str]:
        """
        Safely read a file, handling encoding errors.
        
        Args:
            file_path: Path to the file
            encoding: File encoding
            
        Returns:
            File contents or None if reading failed
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, IOError) as e:
            self.logger.warning(f"Failed to read {file_path}: {e}")
            return None
    
    def find_python_files(self, directory: Path) -> List[Path]:
        """
        Find Python files in a directory.
        
        Args:
            directory: Directory to search
            
        Returns:
            List of Python file paths
        """
        python_files = []
        
        for file_path in directory.rglob("*.py"):
            if self.should_analyze_file(file_path):
                python_files.append(file_path)
        
        return sorted(python_files)
    
    def log_analysis_start(self, target: str) -> None:
        """Log the start of analysis."""
        self.logger.info(f"Starting {self.__class__.__name__} analysis of: {target}")
    
    def log_analysis_complete(self, target: str, results_count: int = None) -> None:
        """Log the completion of analysis."""
        if results_count is not None:
            self.logger.info(f"Completed {self.__class__.__name__} analysis of {target}: {results_count} items")
        else:
            self.logger.info(f"Completed {self.__class__.__name__} analysis of {target}")
    
    def create_result_template(self) -> Dict[str, Any]:
        """
        Create a standard result template.
        
        Returns:
            Dictionary with standard result structure
        """
        return {
            'analyzer': self.__class__.__name__,
            'version': '1.0.0',
            'timestamp': None,  # Should be set by implementing class
            'results': {},
            'metadata': {},
            'errors': [],
            'warnings': []
        }
