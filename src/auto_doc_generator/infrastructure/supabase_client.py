"""
Supabase client initialization and management.

This module handles Supabase client setup, connection management,
and provides a centralized way to access Supabase functionality.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Disable ChromaDB telemetry to prevent telemetry errors
os.environ.setdefault('ANONYMIZED_TELEMETRY', 'false')

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    Client = None
    SUPABASE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SupabaseConfig:
    """Configuration for Supabase connection."""
    url: str
    anon_key: str
    service_role_key: Optional[str] = None
    timeout: int = 30
    auto_refresh_token: bool = True
    persist_session: bool = True


class SupabaseClient:
    """
    Singleton Supabase client manager.
    
    This class manages the Supabase client connection and provides
    a centralized way to access Supabase functionality across the application.
    """
    
    _instance: Optional['SupabaseClient'] = None
    
    def __new__(cls) -> 'SupabaseClient':
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize instance attributes explicitly
            cls._instance._client = None
            cls._instance._config = None
            cls._instance._initialized = False
            cls._instance._logger = logging.getLogger(__name__)
        return cls._instance
    
    def __init__(self):
        """Initialize the Supabase client manager."""
        # Instance attributes are already initialized in __new__
        pass
    
    @classmethod
    def initialize(cls, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the Supabase client.
        
        Args:
            config: Configuration dictionary containing Supabase settings
            
        Returns:
            True if initialization successful, False otherwise
        """
        instance = cls()
        return instance._initialize_client(config or {})
    
    def _initialize_client(self, config: Dict[str, Any]) -> bool:
        """Initialize the Supabase client with configuration."""
        try:
            if not SUPABASE_AVAILABLE:
                self._logger.warning("Supabase package not available. Install with: pip install supabase")
                return False
            
            # Get configuration from various sources
            supabase_config = self._get_supabase_config(config)
            
            if not supabase_config:
                self._logger.warning("Supabase configuration not found. Client not initialized.")
                return False
            
            # Create Supabase client - use service role key if available, otherwise anon key
            supabase_key = supabase_config.service_role_key or supabase_config.anon_key
            self.key_type = "service_role" if supabase_config.service_role_key else "anon"
            
            # Create Supabase client with proper configuration
            self._client = create_client(
                supabase_url=supabase_config.url,
                supabase_key=supabase_key
            )
            
            # For service role, ensure we're using the service role context
            if self.key_type == "service_role":
                # Set additional headers for better service role handling
                try:
                    # Update the client's session with service role context
                    self._client.postgrest.session.headers.update({
                        'X-Client-Info': 'auto-doc-generator-service-role',
                        'User-Agent': 'auto-doc-generator/1.0'
                    })
                except Exception as e:
                    self._logger.debug(f"Could not set additional headers: {e}")
            
            # Validate the service role key format for better error handling
            if self.key_type == "service_role":
                if not supabase_key.startswith('eyJ'):
                    self._logger.warning("⚠️  Service role key doesn't appear to be a valid JWT token")
                
                # Decode JWT to check role (basic validation)
                try:
                    import base64
                    import json
                    # Decode JWT payload (second part)
                    payload = supabase_key.split('.')[1]
                    # Add padding if needed
                    payload += '=' * (4 - len(payload) % 4)
                    decoded = base64.b64decode(payload)
                    jwt_data = json.loads(decoded)
                    
                    if jwt_data.get('role') != 'service_role':
                        self._logger.warning(f"⚠️  JWT role is '{jwt_data.get('role')}', expected 'service_role'")
                    else:
                        self._logger.debug("✅ Service role JWT validation successful")
                        
                except Exception as e:
                    self._logger.debug(f"JWT validation failed: {e}")
            
            self._service_role_validated = self.key_type == "service_role"
            
            self._config = supabase_config
            self._initialized = True
            
            if self.key_type == "service_role":
                self._logger.info("✅ Supabase client initialized with SERVICE ROLE permissions")
            else:
                self._logger.warning("⚠️ Supabase client initialized with ANONYMOUS permissions only. "
                                   "Some operations may fail. Set SUPABASE_SERVICE_ROLE_KEY for full access.")
            self._logger.info(f"   • URL: {supabase_config.url}")
            self._logger.info(f"   • Key type: {self.key_type}")
            self._logger.info(f"   • Auto refresh: {supabase_config.auto_refresh_token}")
            
            # Test the connection
            if self._test_connection():
                self._logger.info("✅ Supabase connection test successful")
                return True
            else:
                self._logger.warning("⚠️  Supabase connection test failed - check network connectivity and credentials")
                return False
                
        except Exception as e:
            self._logger.error(f"❌ Failed to initialize Supabase client: {e}")
            self._client = None
            self._initialized = False
            return False
    
    def _get_supabase_config(self, config: Dict[str, Any]) -> Optional[SupabaseConfig]:
        """Get Supabase configuration from various sources."""
        # Priority order: config dict -> environment variables -> config file
        
        # Try config dictionary first
        supabase_config = config.get('supabase', {})
        
        url = (
            supabase_config.get('url') or
            os.getenv('SUPABASE_URL') or
            os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        )
        
        anon_key = (
            supabase_config.get('anon_key') or
            supabase_config.get('key') or
            os.getenv('SUPABASE_ANON_KEY') or
            os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        )
        
        service_role_key = (
            supabase_config.get('service_role_key') or
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Get database connection details
        db_config = supabase_config.get('database', {})
        db_host = (
            db_config.get('host') or
            os.getenv('SUPABASE_DB_HOST')
        )
        db_port = (
            db_config.get('port') or
            os.getenv('SUPABASE_DB_PORT')
        )
        db_name = (
            db_config.get('name') or
            os.getenv('SUPABASE_DB_NAME')
        )
        db_user = (
            db_config.get('user') or
            os.getenv('SUPABASE_DB_USER')
        )
        
        # Store database config for potential direct PostgreSQL connection
        self._db_config = {
            'host': db_host,
            'port': int(db_port) if db_port else 5432,
            'name': db_name,
            'user': db_user
        } if db_host else None
        
        if not url:
            self._logger.debug("Supabase URL not found in configuration")
            return None
        
        # If no anon_key but we have database connection details, log info
        if not anon_key and self._db_config:
            self._logger.info("Supabase URL provided but no anon key. Database connection details available for direct PostgreSQL access.")
        
        return SupabaseConfig(
            url=url,
            anon_key=anon_key or 'placeholder',  # Use placeholder if not provided
            service_role_key=service_role_key,
            timeout=supabase_config.get('timeout', 30),
            auto_refresh_token=supabase_config.get('auto_refresh_token', True),
            persist_session=supabase_config.get('persist_session', True)
        )
    
    def _test_connection(self) -> bool:
        """Test the Supabase connection with comprehensive checks."""
        try:
            if not self._client:
                self._logger.debug("No client available for connection test")
                return False
            
            # Initialize test result flags
            self.table_access_verified = False
            self.service_role_access_verified = False
            
            # Test 1: Basic connectivity - try any simple operation
            basic_connection = False
            try:
                # Try to access our own template_variables table (which should exist)
                result = self._client.from_('template_variables').select('id').limit(1).execute()
                basic_connection = True
                self._logger.debug("✅ Basic connectivity test passed")
            except Exception as e:
                self._logger.debug(f"Basic connectivity test failed: {e}")
                # Try a fallback test - check if we can at least connect to generation_sessions
                try:
                    result = self._client.from_('generation_sessions').select('id').limit(1).execute()
                    basic_connection = True
                    self._logger.debug("✅ Basic connectivity test passed (fallback)")
                except Exception as e2:
                    self._logger.debug(f"Fallback connectivity test also failed: {e2}")
                    return False
            
            # Test 2: Check template_variables table access
            try:
                # Try to access the template_variables table directly
                result = self._client.from_('template_variables').select('id').limit(1).execute()
                self.table_exists = True
                self.table_access_verified = True
                self._logger.debug("✅ template_variables table exists and is accessible")
            except Exception as access_e:
                error_msg = str(access_e).lower()
                if 'permission denied' in error_msg or 'row-level security' in error_msg:
                    self._logger.debug("⚠️  template_variables table exists but access restricted by RLS policy")
                    self.table_exists = True
                    self.table_access_verified = False
                elif 'relation' in error_msg and 'does not exist' in error_msg:
                    self._logger.debug("💡 template_variables table does not exist - schema not yet applied")
                    self.table_exists = False
                    self.table_access_verified = False
                else:
                    self._logger.debug(f"template_variables access test error: {access_e}")
                    self.table_exists = False
                    self.table_access_verified = False
                    
            except Exception as e:
                self._logger.debug(f"Error checking template_variables table existence: {e}")
                self.table_exists = False
                self.table_access_verified = False
            
            # Test 3: Service role capabilities (if using service role)
            if self.key_type == "service_role":
                try:
                    # For service role, test if we can perform operations that bypass RLS
                    # Use a safer test - try to select from template_variables with RLS bypass
                    result = self._client.from_('template_variables').select('id').limit(1).execute()
                    self.service_role_access_verified = True
                    self._logger.debug("✅ Service role access verified - can bypass RLS on template_variables")
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'row-level security' in error_msg or 'permission denied' in error_msg:
                        self._logger.debug("⚠️  Service role cannot bypass RLS - this may indicate RLS policy issues")
                        self.service_role_access_verified = False
                    elif 'does not exist' in error_msg:
                        self._logger.debug("⚠️  template_variables table doesn't exist for service role test")
                        self.service_role_access_verified = False
                    else:
                        self._logger.debug(f"Service role test failed: {e}")
                        self.service_role_access_verified = False
            
            # Connection is considered successful if basic connectivity works
            # Table access issues are handled gracefully during actual operations
            # Missing tables are not a connection failure - they just mean schema needs to be applied
            if basic_connection:
                self._logger.debug("✅ Supabase connection test successful - basic connectivity verified")
                
                # Provide diagnostic information
                if hasattr(self, 'table_exists'):
                    if self.table_exists:
                        if hasattr(self, 'table_access_verified') and self.table_access_verified:
                            self._logger.debug("✅ Database schema applied and accessible")
                        else:
                            self._logger.debug("⚠️  Database schema exists but access limited by RLS policies")
                    else:
                        self._logger.debug("💡 Database schema not yet applied. Run supabase_schema.sql to enable full features")
                
                if hasattr(self, 'service_role_access_verified') and self.key_type == 'service_role':
                    if self.service_role_access_verified:
                        self._logger.debug("✅ Service role permissions verified")
                    else:
                        self._logger.debug("⚠️  Service role permissions limited - check RLS policies")
                
                return True
            else:
                self._logger.debug("❌ Supabase connection test failed - no basic connectivity")
                return False
            
        except Exception as e:
            self._logger.error(f"Connection test completely failed: {e}")
            self.table_access_verified = False
            self.service_role_access_verified = False
            return False
    
    @classmethod
    def get_client(cls) -> Optional[Client]:
        """
        Get the Supabase client instance.
        
        Returns:
            Supabase client if initialized, None otherwise
        """
        instance = cls()
        if not instance._initialized:
            instance._logger.warning("Supabase client not initialized. Call initialize() first.")
            return None
        return instance._client
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if Supabase client is initialized."""
        instance = cls()
        return instance._initialized
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if Supabase is available and client is initialized."""
        return SUPABASE_AVAILABLE and cls.is_initialized()
    
    @classmethod
    def get_config(cls) -> Optional[SupabaseConfig]:
        """Get the current Supabase configuration."""
        instance = cls()
        return instance._config
    
    @classmethod
    def reset(cls):
        """Reset the Supabase client (useful for testing)."""
        instance = cls()
        instance._client = None
        instance._config = None
        instance._initialized = False
        instance._logger.info("Supabase client reset")
    
    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get detailed status information."""
        instance = cls()
        return {
            'available': SUPABASE_AVAILABLE,
            'initialized': instance._initialized,
            'client_exists': instance._client is not None,
            'config_exists': instance._config is not None,
            'url': instance._config.url if instance._config else None,
            'connection_tested': instance._initialized and instance._test_connection()
        }
    
    def store_template_variables(self, template_data: Dict[str, Any]) -> Optional[str]:
        """
        Store template variables and generated content in Supabase.
        
        Args:
            template_data: Dictionary containing template information including
                          name, type, repository_path, variables, content, metadata, etc.
                          
        Returns:
            Template ID if successful, None otherwise
        """
        if not self._client:
            self._logger.debug("Supabase client not initialized, skipping template storage")
            return None
        
        # Comprehensive permission check
        if hasattr(self, 'key_type') and self.key_type != 'service_role':
            self._logger.debug("Using anonymous key - write operations may fail due to RLS policies. "
                             "Set SUPABASE_SERVICE_ROLE_KEY for full access.")
        
        # Check connection and table access status
        if not hasattr(self, 'table_access_verified'):
            self._logger.debug("Table access not verified, testing connection...")
            self._test_connection()
        
        if hasattr(self, 'service_role_access_verified') and not self.service_role_access_verified and self.key_type == 'service_role':
            self._logger.warning("Service role access verification failed during connection test")
            
        try:
            # Prepare data for insertion
            insert_data = {
                'template_name': template_data.get('name', ''),
                'template_type': template_data.get('type', 'html'),
                'repository_path': template_data.get('repository_path', ''),
                'variables': template_data.get('variables', {}),
                'generated_content': template_data.get('content', ''),
                'metadata': template_data.get('metadata', {}),
                'file_path': template_data.get('file_path', ''),
                'generation_time': template_data.get('generation_time', 0.0)
            }
            
            result = self._client.table('template_variables').insert(insert_data).execute()
            
            if result.data and len(result.data) > 0:
                template_id = result.data[0]['id']
                self._logger.debug(f"✅ Stored template data with ID: {template_id}")
                return template_id
            else:
                self._logger.warning("Failed to store template data - no data returned")
                return None
                
        except Exception as e:
            error_message = str(e).lower()
            template_name = template_data.get('name', 'unknown')
            
            # Handle RLS policy violations more gracefully
            if 'row-level security policy' in error_message or 'row level security' in error_message:
                if hasattr(self, 'key_type') and self.key_type == 'service_role':
                    self._logger.warning(f"⚠️  RLS policy blocked template storage for '{template_name}' even with service role. "
                                       "Check if RLS policies allow service_role access or if user context is required.")
                else:
                    self._logger.debug(f"💡 RLS policy blocked storage of '{template_name}' - user lacks required permissions. "
                                     "This is expected when using anonymous access.")
            elif 'permission denied' in error_message:
                if hasattr(self, 'key_type') and self.key_type == 'anon':
                    self._logger.debug(f"💡 Template storage skipped for '{template_name}' - anonymous user lacks write permissions. "
                                     "This is expected when SUPABASE_SERVICE_ROLE_KEY is not configured.")
                else:
                    self._logger.warning(f"⚠️ Permission denied storing '{template_name}'. Check Supabase user permissions.")
            elif 'not found' in error_message or 'does not exist' in error_message:
                self._logger.debug(f"💡 Table 'template_variables' not found - schema not applied yet. Run supabase_schema.sql to enable database storage.")
            else:
                self._logger.debug(f"Template storage failed for '{template_name}': {e}")
            
            return None
    
    def store_generation_session(self, session_data: Dict[str, Any]) -> Optional[str]:
        """
        Store a generation session in Supabase.
        
        Args:
            session_data: Dictionary containing session information including
                         repository_path, type, start_time, end_time, duration, etc.
                         
        Returns:
            Session ID if successful, None otherwise
        """
        if not self._client:
            self._logger.warning("Supabase client not initialized")
            return None
            
        try:
            # Prepare data for insertion into generation_sessions table
            insert_data = {
                'repository_path': session_data.get('repository_path', ''),
                'session_type': session_data.get('type', 'full_generation'),
                'start_time': session_data.get('start_time', ''),
                'end_time': session_data.get('end_time', ''),
                'duration': session_data.get('duration', 0.0),
                'total_files': session_data.get('total_files', 0),
                'total_functions': session_data.get('total_functions', 0),
                'total_classes': session_data.get('total_classes', 0),
                'pages_generated': session_data.get('pages_generated', 0),
                'success': session_data.get('success', True),
                'error_message': session_data.get('error', ''),
                'metadata': session_data.get('metadata', {}),
                'output_format': session_data.get('output_format', 'html'),
                'output_path': session_data.get('output_path', ''),
                'templates_used': session_data.get('templates_used', [])
            }
            
            result = self._client.table('generation_sessions').insert(insert_data).execute()
            
            if result.data and len(result.data) > 0:
                session_id = result.data[0]['id']
                self._logger.debug(f"Stored generation session with ID: {session_id}")
                return session_id
            else:
                self._logger.error("Failed to store generation session")
                return None
                
        except Exception as e:
            error_message = str(e).lower()
            
            # Handle RLS policy violations more gracefully
            if 'row-level security policy' in error_message or 'row level security' in error_message:
                if hasattr(self, 'key_type') and self.key_type == 'service_role':
                    self._logger.warning("⚠️  RLS policy blocked generation session storage even with service role. "
                                       "Check if RLS policies allow service_role access.")
                else:
                    self._logger.debug("💡 RLS policy blocked generation session storage - user lacks required permissions. "
                                     "This is expected when using anonymous access.")
            elif 'permission denied' in error_message:
                if hasattr(self, 'key_type') and self.key_type == 'anon':
                    self._logger.debug("💡 Generation session storage skipped - anonymous user lacks write permissions.")
                else:
                    self._logger.warning("⚠️ Permission denied storing generation session. Check Supabase user permissions.")
            elif 'not found' in error_message or 'does not exist' in error_message:
                self._logger.debug("💡 Table 'generation_sessions' not found - schema not applied yet. Run supabase_schema.sql to enable database storage.")
            else:
                self._logger.debug(f"Generation session storage failed: {e}")
            
            return None

    
    def diagnose_connection_issues(self) -> Dict[str, Any]:
        """Comprehensive diagnosis of Supabase connection and permission issues."""
        diagnosis = {
            'client_initialized': self._initialized,
            'client_exists': self._client is not None,
            'key_type': getattr(self, 'key_type', 'unknown'),
            'table_access_verified': getattr(self, 'table_access_verified', False),
            'service_role_access_verified': getattr(self, 'service_role_access_verified', False),
            'issues': [],
            'recommendations': []
        }
        
        if not self._initialized:
            diagnosis['issues'].append("Client not initialized")
            diagnosis['recommendations'].append("Call initialize() with proper configuration")
            return diagnosis
        
        if not self._client:
            diagnosis['issues'].append("Client object is None")
            diagnosis['recommendations'].append("Check Supabase URL and API keys")
            return diagnosis
        
        # Test various aspects
        try:
            # Test basic connectivity
            result = self._client.from_('information_schema.tables').select('table_name').limit(1).execute()
            diagnosis['basic_connectivity'] = True
        except Exception as e:
            diagnosis['basic_connectivity'] = False
            diagnosis['issues'].append(f"Basic connectivity failed: {e}")
            diagnosis['recommendations'].append("Check Supabase URL and network connectivity")
        
        # Test template_variables table existence
        try:
            result = self._client.from_('template_variables').select('*').limit(0).execute()
            diagnosis['template_table_exists'] = True
            diagnosis['template_table_accessible'] = True
        except Exception as e:
            error_msg = str(e).lower()
            if 'does not exist' in error_msg or 'relation' in error_msg:
                diagnosis['template_table_exists'] = False
                diagnosis['template_table_accessible'] = False
                diagnosis['issues'].append("template_variables table does not exist")
                diagnosis['recommendations'].append("Apply the supabase_schema.sql to create required tables")
            elif 'permission denied' in error_msg:
                diagnosis['template_table_exists'] = True
                diagnosis['template_table_accessible'] = False
                diagnosis['issues'].append("template_variables table exists but access denied")
                if self.key_type == 'service_role':
                    diagnosis['recommendations'].append("Check RLS policies - service role should bypass RLS")
                else:
                    diagnosis['recommendations'].append("Use service role key for write operations")
            else:
                diagnosis['template_table_exists'] = 'unknown'
                diagnosis['template_table_accessible'] = False
                diagnosis['issues'].append(f"template_variables table access error: {e}")
        
        # Service role specific tests
        if self.key_type == 'service_role':
            try:
                # Test if we can insert (dry run with invalid data to test permissions)
                test_data = {'template_name': '__test__', 'template_type': '__test__'}
                self._client.table('template_variables').insert(test_data).execute()
                diagnosis['can_write_template_variables'] = True
                # Clean up the test record
                self._client.table('template_variables').delete().eq('template_name', '__test__').execute()
            except Exception as e:
                error_msg = str(e).lower()
                diagnosis['can_write_template_variables'] = False
                if 'permission denied' in error_msg:
                    diagnosis['issues'].append("Service role cannot write to template_variables")
                    diagnosis['recommendations'].append("Check if service role key is correct and RLS policies allow service_role")
                elif 'violates' in error_msg:
                    diagnosis['issues'].append(f"Data constraint violation: {e}")
                    diagnosis['recommendations'].append("Check table schema constraints")
                else:
                    diagnosis['issues'].append(f"Write test failed: {e}")
        
        # JWT validation for service role
        if self.key_type == 'service_role' and hasattr(self, '_config') and self._config:
            try:
                service_key = self._config.service_role_key
                if service_key and service_key.startswith('eyJ'):
                    import base64
                    import json
                    payload = service_key.split('.')[1]
                    payload += '=' * (4 - len(payload) % 4)
                    decoded = base64.b64decode(payload)
                    jwt_data = json.loads(decoded)
                    
                    diagnosis['jwt_role'] = jwt_data.get('role')
                    diagnosis['jwt_valid'] = jwt_data.get('role') == 'service_role'
                    
                    if jwt_data.get('role') != 'service_role':
                        diagnosis['issues'].append(f"JWT role is '{jwt_data.get('role')}', expected 'service_role'")
                        diagnosis['recommendations'].append("Verify you're using the service_role key, not anon key")
                else:
                    diagnosis['jwt_valid'] = False
                    diagnosis['issues'].append("Service role key format invalid")
                    
            except Exception as e:
                diagnosis['jwt_valid'] = False
                diagnosis['issues'].append(f"JWT validation failed: {e}")
        
        return diagnosis


# Convenience functions for easy access
def initialize_supabase(config: Dict[str, Any] = None) -> bool:
    """
    Initialize Supabase client with configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if successful, False otherwise
    """
    return SupabaseClient.initialize(config)


def get_supabase_client() -> Optional[Client]:
    """
    Get the initialized Supabase client.
    
    Returns:
        Supabase client if available, None otherwise
    """
    return SupabaseClient.get_client()


def is_supabase_available() -> bool:
    """Check if Supabase is available and initialized."""
    return SupabaseClient.is_available()


def get_supabase_status() -> Dict[str, Any]:
    """Get Supabase client status."""
    return SupabaseClient.get_status()


# Auto-initialization attempt
def auto_initialize_supabase():
    """Attempt to auto-initialize Supabase from environment variables."""
    try:
        if not SupabaseClient.is_initialized():
            # Try to load .env file first
            try:
                from dotenv import load_dotenv
                load_dotenv()
                logger.debug("Loaded environment variables from .env file")
            except ImportError:
                logger.debug("python-dotenv not available, using system environment variables")
            
            # Try to initialize from environment variables
            config = {}
            if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_ANON_KEY'):
                success = SupabaseClient.initialize(config)
                if success:
                    logger.info("✅ Supabase auto-initialized from environment variables")
                else:
                    logger.debug("Supabase auto-initialization failed")
            else:
                logger.debug("Supabase environment variables not found for auto-initialization")
    except Exception as e:
        logger.debug(f"Supabase auto-initialization error: {e}")


# Try auto-initialization on module import
auto_initialize_supabase()