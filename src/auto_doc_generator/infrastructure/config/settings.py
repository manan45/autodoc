"""
Application settings and configuration management.

This module handles loading configuration from various sources and
provides a unified interface for accessing settings.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Settings:
    """
    Centralized configuration management.
    
    This class loads configuration from multiple sources with precedence:
    1. Environment variables (highest priority)
    2. Configuration files
    3. Default values (lowest priority)
    """
    
    def __init__(self, config_file: str = "documentor.yaml"):
        """
        Initialize settings.
        
        Args:
            config_file: Path to the main configuration file
        """
        self.config_file = config_file
        self._config = None
        self._load_config()
    
    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration dictionary."""
        return self._config.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'database.host')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
    
    def reload(self) -> None:
        """Reload configuration from sources."""
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from all sources."""
        # Start with default configuration
        self._config = self._get_default_config()
        
        # Load from configuration file
        file_config = self._load_config_file()
        if file_config:
            self._merge_config(self._config, file_config)
        
        # Override with environment variables
        env_config = self._load_env_config()
        if env_config:
            self._merge_config(self._config, env_config)
        
        logger.debug("Configuration loaded successfully")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            'agent': {
                'name': 'AutoDoc Agent',
                'version': '2.0.0'
            },
            'analysis': {
                'include_patterns': ['*.py'],
                'exclude_patterns': [
                    '*/tests/*', '*/__pycache__/*', '*/.git/*', 
                    '*/venv/*', '*/env/*', '*/node_modules/*'
                ],
                'cache_max_age_hours': 24,
                'ai_analysis': {
                    'enabled': True,
                    'detect_frameworks': True,
                    'analyze_pipelines': True,
                    'generate_flow_diagrams': True
                }
            },
            'documentation': {
                'output_format': 'html',
                'theme': 'material',
                'sections': {
                    'overview': True,
                    'architecture': True,
                    'api_reference': True,
                    'onboarding': True,
                    'ai_models': True,
                    'ai_pipelines': True,
                    'complexity_report': True,
                    'quality_report': True
                },
                'diagrams': {
                    'enabled': True,
                    'format': 'mermaid'
                }
            },
            'quality': {
                'enabled': True,
                'max_detailed_reports': 5,
                'llm_enhancement': True,
                'metrics': {
                    'complexity_threshold': 10,
                    'maintainability_threshold': 60,
                    'documentation_threshold': 0.8
                }
            },
            'ai': {
                'openai': {
                    'enabled': False,
                    'model': 'gpt-4',
                    'max_tokens': 2000,
                    'temperature': 0.1
                },
                'anthropic': {
                    'enabled': False,
                    'model': 'claude-3-sonnet-20240229',
                    'max_tokens': 2000,
                    'temperature': 0.1
                }
            },
            'database': {
                'supabase': {
                    'enabled': False,
                    'url': None,
                    'anon_key': None,
                    'database': {
                        'host': None,
                        'port': 5432,
                        'name': None,
                        'user': None
                    }
                }
            },
            'cache': {
                'enabled': True,
                'type': 'memory',  # memory, file, redis
                'ttl_seconds': 3600,
                'max_size': 1000
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': None,
                'console': True
            },
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'debug': False
            },
            'embeddings': {
                'enabled': True,
                'provider': 'openai',  # openai, huggingface, local
                'model': 'text-embedding-ada-002',
                'dimensions': 1536
            }
        }
    
    def _load_config_file(self) -> Optional[Dict[str, Any]]:
        """Load configuration from YAML file."""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.debug(f"Loaded configuration from {config_path}")
                return config
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
            return None
    
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        env_config = {}
        
        # Define environment variable mappings
        env_mappings = {
            'AUTODOC_LOG_LEVEL': 'logging.level',
            'AUTODOC_OUTPUT_FORMAT': 'documentation.output_format',
            'AUTODOC_CACHE_ENABLED': 'cache.enabled',
            'AUTODOC_AI_ENABLED': 'analysis.ai_analysis.enabled',
            'OPENAI_API_KEY': 'ai.openai.api_key',
            'ANTHROPIC_API_KEY': 'ai.anthropic.api_key',
            'SUPABASE_URL': 'database.supabase.url',
            'SUPABASE_ANON_KEY': 'database.supabase.anon_key',
            'SUPABASE_DB_HOST': 'database.supabase.database.host',
            'SUPABASE_DB_PORT': 'database.supabase.database.port',
            'SUPABASE_DB_NAME': 'database.supabase.database.name',
            'SUPABASE_DB_USER': 'database.supabase.database.user',
            'AUTODOC_SERVER_PORT': 'server.port',
            'AUTODOC_SERVER_HOST': 'server.host',
        }
        
        # Also map OPENAI_API_KEY to llm.openai_api_key for AIService compatibility
        if os.getenv('OPENAI_API_KEY'):
            self._set_nested_value(env_config, 'llm.openai_api_key', os.getenv('OPENAI_API_KEY'))
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                converted_value = self._convert_env_value(value)
                self._set_nested_value(env_config, config_key, converted_value)
        
        # Enable AI services if API keys are provided
        if os.getenv('OPENAI_API_KEY'):
            self._set_nested_value(env_config, 'ai.openai.enabled', True)
        
        if os.getenv('ANTHROPIC_API_KEY'):
            self._set_nested_value(env_config, 'ai.anthropic.enabled', True)
        
        # Enable Supabase if credentials are provided
        if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY'):
            self._set_nested_value(env_config, 'database.supabase.enabled', True)
        
        return env_config
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type."""
        # Boolean conversion
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any) -> None:
        """Set a nested configuration value using dot notation."""
        keys = key.split('.')
        current = config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def validate_config(self) -> List[str]:
        """
        Validate configuration and return list of validation errors.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate required settings when features are enabled
        if self.get('analysis.ai_analysis.enabled') and not (
            self.get('ai.openai.enabled') or self.get('ai.anthropic.enabled')
        ):
            errors.append("AI analysis enabled but no AI provider configured")
        
        if self.get('ai.openai.enabled') and not self.get('ai.openai.api_key'):
            errors.append("OpenAI enabled but no API key provided")
        
        if self.get('ai.anthropic.enabled') and not self.get('ai.anthropic.api_key'):
            errors.append("Anthropic enabled but no API key provided")
        
        if self.get('database.supabase.enabled') and not (
            self.get('database.supabase.url') and self.get('database.supabase.anon_key')
        ):
            errors.append("Supabase enabled but credentials not provided")
        
        # Validate numeric ranges
        port = self.get('server.port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append(f"Invalid server port: {port}")
        
        cache_ttl = self.get('cache.ttl_seconds')
        if not isinstance(cache_ttl, int) or cache_ttl < 0:
            errors.append(f"Invalid cache TTL: {cache_ttl}")
        
        return errors
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of current configuration for logging/debugging."""
        return {
            'config_file': self.config_file,
            'analysis_enabled': self.get('analysis.ai_analysis.enabled'),
            'ai_providers': {
                'openai': self.get('ai.openai.enabled'),
                'anthropic': self.get('ai.anthropic.enabled'),
            },
            'database': {
                'supabase': self.get('database.supabase.enabled'),
            },
            'cache_enabled': self.get('cache.enabled'),
            'output_format': self.get('documentation.output_format'),
            'log_level': self.get('logging.level'),
        }
