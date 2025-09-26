"""
Repository factory for creating appropriate database repositories.

This factory automatically selects and creates the best available
repository based on configuration and available dependencies.
"""

import logging
from typing import Dict, Any, Optional, Type

from .base_repository import BaseRepository, DatabaseType, MemoryRepository
from .supabase_repository import SupabaseRepository

logger = logging.getLogger(__name__)


class RepositoryFactory:
    """
    Factory for creating database repositories.
    
    This factory automatically selects the best available repository
    based on configuration and available dependencies.
    """
    
    # Registry of available repository types
    REPOSITORY_TYPES: Dict[DatabaseType, Type[BaseRepository]] = {
        DatabaseType.SUPABASE: SupabaseRepository,
        DatabaseType.MEMORY: MemoryRepository,
    }
    
    @classmethod
    def create_repository(cls, config: Dict[str, Any], 
                         preferred_type: Optional[DatabaseType] = None) -> BaseRepository:
        """
        Create the best available repository.
        
        Args:
            config: Configuration dictionary
            preferred_type: Preferred database type (optional)
            
        Returns:
            Repository instance
        """
        # If preferred type is specified, try to create it
        if preferred_type and preferred_type in cls.REPOSITORY_TYPES:
            try:
                repo_class = cls.REPOSITORY_TYPES[preferred_type]
                repo = repo_class(config)
                if repo.initialize() and repo.is_available():
                    logger.info(f"Created {preferred_type.value} repository")
                    return repo
                else:
                    logger.warning(f"Failed to initialize {preferred_type.value} repository")
            except Exception as e:
                logger.warning(f"Failed to create {preferred_type.value} repository: {e}")
        
        # Try repositories in order of preference
        preference_order = [
            DatabaseType.SUPABASE,
            DatabaseType.MEMORY,  # Always available as fallback
        ]
        
        for db_type in preference_order:
            if db_type in cls.REPOSITORY_TYPES:
                try:
                    repo_class = cls.REPOSITORY_TYPES[db_type]
                    repo = repo_class(config)
                    
                    if repo.initialize() and repo.is_available():
                        logger.info(f"Created {db_type.value} repository")
                        return repo
                    else:
                        logger.debug(f"{db_type.value} repository not available")
                        
                except Exception as e:
                    logger.debug(f"Failed to create {db_type.value} repository: {e}")
        
        # This should never happen since MemoryRepository is always available
        logger.error("No repository could be created, falling back to memory repository")
        return MemoryRepository(config)
    
    @classmethod
    def get_available_types(cls, config: Dict[str, Any]) -> Dict[DatabaseType, bool]:
        """
        Get availability status of all repository types.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dictionary mapping repository types to availability status
        """
        availability = {}
        
        for db_type, repo_class in cls.REPOSITORY_TYPES.items():
            try:
                repo = repo_class(config)
                availability[db_type] = repo.is_available()
            except Exception:
                availability[db_type] = False
        
        return availability
    
    @classmethod
    def register_repository_type(cls, db_type: DatabaseType, 
                                repo_class: Type[BaseRepository]):
        """
        Register a new repository type.
        
        Args:
            db_type: Database type
            repo_class: Repository class
        """
        cls.REPOSITORY_TYPES[db_type] = repo_class
        logger.info(f"Registered repository type: {db_type.value}")


def create_default_repository(config: Dict[str, Any]) -> BaseRepository:
    """
    Create the default repository for the application.
    
    This is a convenience function that creates the best available
    repository using the factory.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Repository instance
    """
    return RepositoryFactory.create_repository(config)


def create_repository_with_fallback(config: Dict[str, Any], 
                                   preferred_types: list = None) -> BaseRepository:
    """
    Create repository with custom fallback order.
    
    Args:
        config: Configuration dictionary
        preferred_types: List of preferred database types in order
        
    Returns:
        Repository instance
    """
    if not preferred_types:
        preferred_types = [DatabaseType.SUPABASE, DatabaseType.MEMORY]
    
    for db_type in preferred_types:
        try:
            if db_type in RepositoryFactory.REPOSITORY_TYPES:
                repo_class = RepositoryFactory.REPOSITORY_TYPES[db_type]
                repo = repo_class(config)
                
                if repo.initialize() and repo.is_available():
                    logger.info(f"Created {db_type.value} repository")
                    return repo
                    
        except Exception as e:
            logger.debug(f"Failed to create {db_type.value} repository: {e}")
    
    # Final fallback to memory repository
    logger.warning("All preferred repositories failed, using memory repository")
    return MemoryRepository(config)
