"""
File system operations repository.

This repository handles all file system operations including reading,
writing, and searching for files.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import fnmatch
import logging

logger = logging.getLogger(__name__)


class FileRepository:
    """Repository for file system operations."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize file repository.
        
        Args:
            base_path: Optional base path for relative operations
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
    
    def read_file(self, file_path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """
        Read contents of a file.
        
        Args:
            file_path: Path to the file
            encoding: File encoding (default: utf-8)
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read
        """
        try:
            path = self._resolve_path(file_path)
            with open(path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise
    
    def write_file(
        self, 
        file_path: Union[str, Path], 
        content: str, 
        encoding: str = 'utf-8',
        create_dirs: bool = True
    ) -> None:
        """
        Write content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding (default: utf-8)
            create_dirs: Whether to create parent directories
            
        Raises:
            IOError: If file can't be written
        """
        try:
            path = self._resolve_path(file_path)
            
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
                
            logger.debug(f"Wrote file: {path}")
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            raise
    
    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """
        Check if a file exists.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            path = self._resolve_path(file_path)
            return path.exists() and path.is_file()
        except Exception:
            return False
    
    def directory_exists(self, dir_path: Union[str, Path]) -> bool:
        """
        Check if a directory exists.
        
        Args:
            dir_path: Path to check
            
        Returns:
            True if directory exists, False otherwise
        """
        try:
            path = self._resolve_path(dir_path)
            return path.exists() and path.is_dir()
        except Exception:
            return False
    
    def create_directory(self, dir_path: Union[str, Path], parents: bool = True) -> None:
        """
        Create a directory.
        
        Args:
            dir_path: Path to create
            parents: Whether to create parent directories
            
        Raises:
            OSError: If directory can't be created
        """
        try:
            path = self._resolve_path(dir_path)
            path.mkdir(parents=parents, exist_ok=True)
            logger.debug(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise
    
    def delete_file(self, file_path: Union[str, Path]) -> None:
        """
        Delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Raises:
            FileNotFoundError: If file doesn't exist
            OSError: If file can't be deleted
        """
        try:
            path = self._resolve_path(file_path)
            path.unlink()
            logger.debug(f"Deleted file: {path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise
    
    def delete_directory(self, dir_path: Union[str, Path], recursive: bool = False) -> None:
        """
        Delete a directory.
        
        Args:
            dir_path: Path to the directory to delete
            recursive: Whether to delete recursively
            
        Raises:
            OSError: If directory can't be deleted
        """
        try:
            path = self._resolve_path(dir_path)
            if recursive:
                shutil.rmtree(path)
            else:
                path.rmdir()
            logger.debug(f"Deleted directory: {path}")
        except Exception as e:
            logger.error(f"Failed to delete directory {dir_path}: {e}")
            raise
    
    def copy_file(self, src_path: Union[str, Path], dst_path: Union[str, Path]) -> None:
        """
        Copy a file.
        
        Args:
            src_path: Source file path
            dst_path: Destination file path
            
        Raises:
            FileNotFoundError: If source file doesn't exist
            OSError: If file can't be copied
        """
        try:
            src = self._resolve_path(src_path)
            dst = self._resolve_path(dst_path)
            
            # Create destination directory if needed
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(src, dst)
            logger.debug(f"Copied file: {src} -> {dst}")
        except Exception as e:
            logger.error(f"Failed to copy file {src_path} to {dst_path}: {e}")
            raise
    
    def find_files(
        self, 
        search_path: Union[str, Path], 
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
        recursive: bool = True
    ) -> List[str]:
        """
        Find files matching patterns.
        
        Args:
            search_path: Path to search in
            include_patterns: Patterns to include (e.g., ['*.py', '*.js'])
            exclude_patterns: Patterns to exclude (e.g., ['*/tests/*', '*/__pycache__/*'])
            recursive: Whether to search recursively
            
        Returns:
            List of matching file paths
        """
        try:
            search_path = self._resolve_path(search_path)
            include_patterns = include_patterns or ['*']
            exclude_patterns = exclude_patterns or []
            
            found_files = []
            
            if recursive:
                for root, dirs, files in os.walk(search_path):
                    # Filter directories to exclude
                    dirs[:] = [d for d in dirs if not self._matches_patterns(
                        os.path.join(root, d), exclude_patterns
                    )]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Check include patterns
                        if not self._matches_patterns(file_path, include_patterns):
                            continue
                        
                        # Check exclude patterns
                        if self._matches_patterns(file_path, exclude_patterns):
                            continue
                        
                        found_files.append(file_path)
            else:
                for file_path in search_path.iterdir():
                    if not file_path.is_file():
                        continue
                    
                    file_str = str(file_path)
                    
                    # Check include patterns
                    if not self._matches_patterns(file_str, include_patterns):
                        continue
                    
                    # Check exclude patterns
                    if self._matches_patterns(file_str, exclude_patterns):
                        continue
                    
                    found_files.append(file_str)
            
            logger.debug(f"Found {len(found_files)} files in {search_path}")
            return sorted(found_files)
            
        except Exception as e:
            logger.error(f"Failed to find files in {search_path}: {e}")
            raise
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            path = self._resolve_path(file_path)
            stat = path.stat()
            
            return {
                'path': str(path),
                'name': path.name,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'created': stat.st_ctime,
                'is_file': path.is_file(),
                'is_directory': path.is_dir(),
                'extension': path.suffix,
            }
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            raise
    
    def list_directory(self, dir_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        List contents of a directory.
        
        Args:
            dir_path: Path to the directory
            
        Returns:
            List of file/directory information dictionaries
        """
        try:
            path = self._resolve_path(dir_path)
            contents = []
            
            for item in path.iterdir():
                try:
                    info = self.get_file_info(item)
                    contents.append(info)
                except Exception as e:
                    logger.warning(f"Failed to get info for {item}: {e}")
                    continue
            
            return sorted(contents, key=lambda x: (not x['is_directory'], x['name']))
            
        except Exception as e:
            logger.error(f"Failed to list directory {dir_path}: {e}")
            raise
    
    def _resolve_path(self, file_path: Union[str, Path]) -> Path:
        """Resolve path relative to base path."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        return path.resolve()
    
    def _matches_patterns(self, file_path: str, patterns: List[str]) -> bool:
        """Check if file path matches any of the patterns."""
        if not patterns:
            return False
        
        # Normalize path for pattern matching
        normalized_path = file_path.replace(os.sep, '/')
        
        for pattern in patterns:
            # Convert pattern to use forward slashes
            normalized_pattern = pattern.replace(os.sep, '/')
            
            # Use fnmatch for glob-style pattern matching
            if fnmatch.fnmatch(normalized_path, normalized_pattern):
                return True
            
            # Also check if pattern matches the basename
            if fnmatch.fnmatch(os.path.basename(normalized_path), normalized_pattern):
                return True
        
        return False
