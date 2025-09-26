"""
Base repository interface for database operations.

This module provides abstract base classes that define the interface
for database operations, allowing different database implementations
to be used interchangeably.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum


class DatabaseType(Enum):
    """Supported database types."""
    SUPABASE = "supabase"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MONGODB = "mongodb"
    MEMORY = "memory"
    FILE = "file"


@dataclass
class SessionData:
    """Data structure for generation sessions."""
    id: Optional[str] = None
    repository_path: str = ""
    session_type: str = "full_generation"
    output_format: str = "html"
    output_path: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    success: bool = True
    error_message: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TaskData:
    """Data structure for coordinator tasks."""
    id: Optional[str] = None
    session_id: str = ""
    task_type: str = ""
    task_description: str = ""
    task_priority: int = 1
    task_status: str = "pending"
    parent_task_id: Optional[str] = None
    dependencies: List[str] = None
    assigned_component: str = ""
    input_data: Dict[str, Any] = None
    output_data: Dict[str, Any] = None
    execution_plan: Dict[str, Any] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.input_data is None:
            self.input_data = {}
        if self.output_data is None:
            self.output_data = {}
        if self.execution_plan is None:
            self.execution_plan = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PromptData:
    """Data structure for LLM prompts and responses."""
    id: Optional[str] = None
    session_id: str = ""
    prompt_type: str = ""
    prompt_content: str = ""
    context: str = ""
    repository_path: str = ""
    component_id: str = ""
    variables: Dict[str, Any] = None
    metadata: Dict[str, Any] = None
    model_used: str = ""
    tokens_used: int = 0
    response_content: str = ""
    success: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class DecisionData:
    """Data structure for coordinator decisions."""
    id: Optional[str] = None
    session_id: str = ""
    task_id: Optional[str] = None
    decision_type: str = ""
    decision_prompt: str = ""
    decision_response: str = ""
    reasoning: str = ""
    confidence_score: float = 0.0
    alternatives_considered: List[str] = None
    context: Dict[str, Any] = None
    model_used: str = ""
    tokens_used: int = 0
    execution_time_ms: int = 0
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.alternatives_considered is None:
            self.alternatives_considered = []
        if self.context is None:
            self.context = {}


@dataclass
class InteractionData:
    """Data structure for component interactions."""
    id: Optional[str] = None
    session_id: str = ""
    task_id: Optional[str] = None
    from_component: str = ""
    to_component: str = ""
    interaction_type: str = ""
    message_content: str = ""
    request_data: Dict[str, Any] = None
    response_data: Dict[str, Any] = None
    success: bool = True
    error_message: str = ""
    execution_time_ms: int = 0
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.request_data is None:
            self.request_data = {}
        if self.response_data is None:
            self.response_data = {}


class BaseRepository(ABC):
    """
    Abstract base class for database repositories.
    
    This class defines the interface that all database repositories
    must implement, ensuring consistency across different database types.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the repository.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.db_type = self._get_database_type()
    
    @abstractmethod
    def _get_database_type(self) -> DatabaseType:
        """Get the database type for this repository."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the repository is available and connected."""
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the database connection and schema."""
        pass
    
    # Session Management
    
    @abstractmethod
    def create_session(self, session_data: SessionData) -> Optional[str]:
        """
        Create a new generation session.
        
        Args:
            session_data: Session data to store
            
        Returns:
            Session ID if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            Session data if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a session.
        
        Args:
            session_id: Session ID to update
            updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def list_sessions(self, limit: int = 100, offset: int = 0) -> List[SessionData]:
        """
        List sessions.
        
        Args:
            limit: Maximum number of sessions to return
            offset: Number of sessions to skip
            
        Returns:
            List of session data
        """
        pass
    
    # Task Management
    
    @abstractmethod
    def create_task(self, task_data: TaskData) -> Optional[str]:
        """
        Create a new task.
        
        Args:
            task_data: Task data to store
            
        Returns:
            Task ID if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def get_task(self, task_id: str) -> Optional[TaskData]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID to retrieve
            
        Returns:
            Task data if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a task.
        
        Args:
            task_id: Task ID to update
            updates: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_pending_tasks(self, session_id: str, assigned_component: str = None) -> List[TaskData]:
        """
        Get pending tasks for a session.
        
        Args:
            session_id: Session ID
            assigned_component: Optional component filter
            
        Returns:
            List of pending tasks
        """
        pass
    
    # Prompt and Response Logging
    
    @abstractmethod
    def log_prompt(self, prompt_data: PromptData) -> Optional[str]:
        """
        Log a prompt.
        
        Args:
            prompt_data: Prompt data to store
            
        Returns:
            Prompt ID if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def update_prompt_response(self, prompt_id: str, response_content: str, 
                              model_used: str = "", tokens_used: int = 0, 
                              success: bool = True) -> bool:
        """
        Update a prompt with its response.
        
        Args:
            prompt_id: Prompt ID to update
            response_content: Response content
            model_used: Model that generated the response
            tokens_used: Number of tokens used
            success: Whether the response was successful
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    # Decision Logging
    
    @abstractmethod
    def log_decision(self, decision_data: DecisionData) -> Optional[str]:
        """
        Log a coordinator decision.
        
        Args:
            decision_data: Decision data to store
            
        Returns:
            Decision ID if successful, None otherwise
        """
        pass
    
    # Interaction Logging
    
    @abstractmethod
    def log_interaction(self, interaction_data: InteractionData) -> Optional[str]:
        """
        Log a component interaction.
        
        Args:
            interaction_data: Interaction data to store
            
        Returns:
            Interaction ID if successful, None otherwise
        """
        pass
    
    # Analytics and Reporting
    
    @abstractmethod
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """
        Get analytics for a specific session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Analytics data
        """
        pass
    
    @abstractmethod
    def get_overall_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get overall analytics for the specified period.
        
        Args:
            days: Number of days to include in analytics
            
        Returns:
            Overall analytics data
        """
        pass
    
    # Cleanup and Maintenance
    
    @abstractmethod
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Clean up old data.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Dictionary with counts of deleted records
        """
        pass
    
    @abstractmethod
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics.
        
        Returns:
            Storage statistics
        """
        pass


class MemoryRepository(BaseRepository):
    """
    In-memory implementation of the base repository.
    
    This implementation stores all data in memory and is useful
    for testing and development when no database is available.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize memory repository."""
        super().__init__(config)
        self.sessions: Dict[str, SessionData] = {}
        self.tasks: Dict[str, TaskData] = {}
        self.prompts: Dict[str, PromptData] = {}
        self.decisions: Dict[str, DecisionData] = {}
        self.interactions: Dict[str, InteractionData] = {}
        self._id_counter = 0
    
    def _get_database_type(self) -> DatabaseType:
        """Get database type."""
        return DatabaseType.MEMORY
    
    def _generate_id(self) -> str:
        """Generate a new ID."""
        self._id_counter += 1
        return f"mem_{self._id_counter:06d}"
    
    def is_available(self) -> bool:
        """Check if repository is available."""
        return True
    
    def initialize(self) -> bool:
        """Initialize the repository."""
        return True
    
    # Session Management
    
    def create_session(self, session_data: SessionData) -> Optional[str]:
        """Create a new session."""
        session_id = self._generate_id()
        session_data.id = session_id
        if session_data.start_time is None:
            session_data.start_time = datetime.now()
        self.sessions[session_id] = session_data
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update a session."""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        return True
    
    def list_sessions(self, limit: int = 100, offset: int = 0) -> List[SessionData]:
        """List sessions."""
        sessions = list(self.sessions.values())
        return sessions[offset:offset + limit]
    
    # Task Management
    
    def create_task(self, task_data: TaskData) -> Optional[str]:
        """Create a new task."""
        task_id = self._generate_id()
        task_data.id = task_id
        if task_data.created_at is None:
            task_data.created_at = datetime.now()
        self.tasks[task_id] = task_data
        return task_id
    
    def get_task(self, task_id: str) -> Optional[TaskData]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a task."""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        return True
    
    def get_pending_tasks(self, session_id: str, assigned_component: str = None) -> List[TaskData]:
        """Get pending tasks."""
        tasks = []
        for task in self.tasks.values():
            if (task.session_id == session_id and 
                task.task_status == "pending" and
                (assigned_component is None or task.assigned_component == assigned_component)):
                tasks.append(task)
        
        # Sort by priority (higher number = higher priority)
        tasks.sort(key=lambda x: x.task_priority, reverse=True)
        return tasks
    
    # Prompt and Response Logging
    
    def log_prompt(self, prompt_data: PromptData) -> Optional[str]:
        """Log a prompt."""
        prompt_id = self._generate_id()
        prompt_data.id = prompt_id
        if prompt_data.created_at is None:
            prompt_data.created_at = datetime.now()
        self.prompts[prompt_id] = prompt_data
        return prompt_id
    
    def update_prompt_response(self, prompt_id: str, response_content: str,
                              model_used: str = "", tokens_used: int = 0,
                              success: bool = True) -> bool:
        """Update prompt response."""
        if prompt_id not in self.prompts:
            return False
        
        prompt = self.prompts[prompt_id]
        prompt.response_content = response_content
        prompt.model_used = model_used
        prompt.tokens_used = tokens_used
        prompt.success = success
        
        return True
    
    # Decision Logging
    
    def log_decision(self, decision_data: DecisionData) -> Optional[str]:
        """Log a decision."""
        decision_id = self._generate_id()
        decision_data.id = decision_id
        if decision_data.created_at is None:
            decision_data.created_at = datetime.now()
        self.decisions[decision_id] = decision_data
        return decision_id
    
    # Interaction Logging
    
    def log_interaction(self, interaction_data: InteractionData) -> Optional[str]:
        """Log an interaction."""
        interaction_id = self._generate_id()
        interaction_data.id = interaction_id
        if interaction_data.created_at is None:
            interaction_data.created_at = datetime.now()
        self.interactions[interaction_id] = interaction_data
        return interaction_id
    
    # Analytics and Reporting
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get session analytics."""
        session = self.sessions.get(session_id)
        if not session:
            return {}
        
        session_tasks = [t for t in self.tasks.values() if t.session_id == session_id]
        session_prompts = [p for p in self.prompts.values() if p.session_id == session_id]
        session_decisions = [d for d in self.decisions.values() if d.session_id == session_id]
        session_interactions = [i for i in self.interactions.values() if i.session_id == session_id]
        
        return {
            'session_id': session_id,
            'session_data': session,
            'task_count': len(session_tasks),
            'completed_tasks': len([t for t in session_tasks if t.task_status == 'completed']),
            'failed_tasks': len([t for t in session_tasks if t.task_status == 'failed']),
            'prompt_count': len(session_prompts),
            'decision_count': len(session_decisions),
            'interaction_count': len(session_interactions),
            'total_tokens_used': sum(p.tokens_used for p in session_prompts)
        }
    
    def get_overall_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get overall analytics."""
        return {
            'total_sessions': len(self.sessions),
            'total_tasks': len(self.tasks),
            'total_prompts': len(self.prompts),
            'total_decisions': len(self.decisions),
            'total_interactions': len(self.interactions),
            'database_type': self.db_type.value
        }
    
    # Cleanup and Maintenance
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """Clean up old data."""
        # For memory repository, we don't actually delete anything
        return {
            'sessions_deleted': 0,
            'tasks_deleted': 0,
            'prompts_deleted': 0,
            'decisions_deleted': 0,
            'interactions_deleted': 0
        }
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        return {
            'sessions_count': len(self.sessions),
            'tasks_count': len(self.tasks),
            'prompts_count': len(self.prompts),
            'decisions_count': len(self.decisions),
            'interactions_count': len(self.interactions),
            'storage_type': 'memory'
        }
