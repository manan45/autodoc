"""
Data access repositories for the auto documentation generator.

This module contains repositories that handle data access operations
for files, caching, and external services.
"""

from .file_repository import FileRepository
from .cache_repository import CacheRepository
from .supabase_repository import SupabaseRepository

__all__ = [
    'FileRepository',
    'CacheRepository',
    'SupabaseRepository',
]
