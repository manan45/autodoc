"""
Supabase repository for data operations.

This repository handles all Supabase database operations including
session tracking, prompt logging, and coordinator task management.
"""

import os
import json
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone
import logging
from dataclasses import asdict

from .base_repository import (
    BaseRepository, DatabaseType, SessionData, TaskData, 
    PromptData, DecisionData, InteractionData
)
from ...infrastructure.supabase_client import SupabaseClient, initialize_supabase

try:
    from supabase import Client
except ImportError:
    Client = None

logger = logging.getLogger(__name__)


class SupabaseRepository(BaseRepository):
    """
    Repository for Supabase database operations.
    
    Handles all database interactions for the auto documentation generator
    including session tracking, logging, and coordinator task management.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Supabase repository.
        
        Args:
            config: Configuration dictionary containing Supabase settings
        """
        super().__init__(config)
        self.client: Optional[Client] = None
        self._initialize_client(config)
    
    def _get_database_type(self) -> DatabaseType:
        """Get database type."""
        return DatabaseType.SUPABASE
    
    def _initialize_client(self, config: Dict[str, Any]):
        """Initialize Supabase client using the centralized client manager."""
        try:
            # Initialize the centralized Supabase client
            if not SupabaseClient.is_initialized():
                success = initialize_supabase(config)
                if not success:
                    logger.warning("Supabase client initialization failed")
                    return
            
            # Get the initialized client
            self.client = SupabaseClient.get_client()
            
            if self.client:
                logger.info("✅ Supabase repository initialized with centralized client")
            else:
                logger.warning("⚠️  Supabase client not available - using fallback repository")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase repository: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Supabase client is available."""
        return self.client is not None
    
    def initialize(self) -> bool:
        """Initialize the database connection."""
        return self.is_available()
    
    # Generation Session Management
    
    def create_session(self, repository_path: str, session_type: str = "full_generation",
                      output_format: str = "html", output_path: str = "") -> Optional[str]:
        """
        Create a new generation session.
        
        Args:
            repository_path: Path to the repository being documented
            session_type: Type of generation session
            output_format: Output format (html, markdown, etc.)
            output_path: Path where output will be generated
            
        Returns:
            Session ID if successful, None otherwise
        """
        if not self.is_available():
            return None
            
        try:
            session_data = {
                'repository_path': repository_path,
                'session_type': session_type,
                'output_format': output_format,
                'output_path': output_path,
                'start_time': datetime.now(timezone.utc).isoformat(),
                'metadata': {}
            }
            
            result = self.client.table('generation_sessions').insert(session_data).execute()
            
            if result.data and len(result.data) > 0:
                session_id = result.data[0]['id']
                logger.info(f"Created generation session: {session_id}")
                return session_id
            else:
                logger.error("Failed to create generation session")
                return None
                
        except Exception as e:
            logger.error(f"Error creating generation session: {e}")
            return None
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a generation session.
        
        Args:
            session_id: Session ID to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available() or not session_id:
            return False
            
        try:
            # Add end time if marking as completed
            if updates.get('success') is not None:
                updates['end_time'] = datetime.now(timezone.utc).isoformat()
            
            result = self.client.table('generation_sessions').update(updates).eq('id', session_id).execute()
            
            if result.data:
                logger.debug(f"Updated session {session_id}")
                return True
            else:
                logger.error(f"Failed to update session {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {e}")
            return False
    
    # Prompt and Response Logging
    
    def log_prompt(self, session_id: str, prompt_type: str, prompt_content: str,
                  context: str = "", repository_path: str = "", component_id: str = "",
                  variables: Dict[str, Any] = None, metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Log a prompt to the database.
        
        Args:
            session_id: Associated session ID
            prompt_type: Type of prompt
            prompt_content: The actual prompt content
            context: Context information
            repository_path: Repository path
            component_id: Component identifier
            variables: Template variables used
            metadata: Additional metadata
            
        Returns:
            Prompt ID if successful, None otherwise
        """
        if not self.is_available():
            return None
            
        try:
            prompt_data = {
                'prompt_type': prompt_type,
                'prompt_content': prompt_content,
                'context': context,
                'repository_path': repository_path,
                'component_id': component_id,
                'variables': variables or {},
                'metadata': {**(metadata or {}), 'session_id': session_id}
            }
            
            result = self.client.table('prompts').insert(prompt_data).execute()
            
            if result.data and len(result.data) > 0:
                prompt_id = result.data[0]['id']
                logger.debug(f"Logged prompt: {prompt_id}")
                return prompt_id
            else:
                logger.error("Failed to log prompt")
                return None
                
        except Exception as e:
            logger.error(f"Error logging prompt: {e}")
            return None
    
    def log_response(self, prompt_id: str, response_content: str, model_used: str = "",
                    tokens_used: int = 0, success: bool = True) -> bool:
        """
        Log a response to an existing prompt.
        
        Args:
            prompt_id: ID of the associated prompt
            response_content: The response content
            model_used: Model that generated the response
            tokens_used: Number of tokens used
            success: Whether the response was successful
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available() or not prompt_id:
            return False
            
        try:
            updates = {
                'response_content': response_content,
                'model_used': model_used,
                'tokens_used': tokens_used,
                'success': success
            }
            
            result = self.client.table('prompts').update(updates).eq('id', prompt_id).execute()
            
            if result.data:
                logger.debug(f"Logged response for prompt: {prompt_id}")
                return True
            else:
                logger.error(f"Failed to log response for prompt: {prompt_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging response for prompt {prompt_id}: {e}")
            return False
    
    # Coordinator Task Management
    
    def create_task(self, session_id: str, task_type: str, task_description: str,
                   task_priority: int = 1, parent_task_id: str = None,
                   dependencies: List[str] = None, assigned_component: str = "",
                   input_data: Dict[str, Any] = None, execution_plan: Dict[str, Any] = None,
                   metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Create a coordinator task.
        
        Args:
            session_id: Associated session ID
            task_type: Type of task
            task_description: Description of the task
            task_priority: Task priority (higher number = higher priority)
            parent_task_id: Parent task ID if this is a subtask
            dependencies: List of task IDs this task depends on
            assigned_component: Component assigned to execute the task
            input_data: Input data for the task
            execution_plan: Execution plan for the task
            metadata: Additional metadata
            
        Returns:
            Task ID if successful, None otherwise
        """
        if not self.is_available():
            return None
            
        try:
            task_data = {
                'session_id': session_id,
                'task_type': task_type,
                'task_description': task_description,
                'task_priority': task_priority,
                'parent_task_id': parent_task_id,
                'dependencies': dependencies or [],
                'assigned_component': assigned_component,
                'input_data': input_data or {},
                'execution_plan': execution_plan or {},
                'metadata': metadata or {}
            }
            
            result = self.client.table('coordinator_tasks').insert(task_data).execute()
            
            if result.data and len(result.data) > 0:
                task_id = result.data[0]['id']
                logger.debug(f"Created coordinator task: {task_id}")
                return task_id
            else:
                logger.error("Failed to create coordinator task")
                return None
                
        except Exception as e:
            logger.error(f"Error creating coordinator task: {e}")
            return None
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a coordinator task.
        
        Args:
            task_id: Task ID to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available() or not task_id:
            return False
            
        try:
            result = self.client.table('coordinator_tasks').update(updates).eq('id', task_id).execute()
            
            if result.data:
                logger.debug(f"Updated task {task_id}")
                return True
            else:
                logger.error(f"Failed to update task {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return False
    
    def get_pending_tasks(self, session_id: str, assigned_component: str = None) -> List[Dict[str, Any]]:
        """
        Get pending tasks for a session.
        
        Args:
            session_id: Session ID
            assigned_component: Optional component filter
            
        Returns:
            List of pending tasks
        """
        if not self.is_available():
            return []
            
        try:
            query = self.client.table('coordinator_tasks').select('*').eq('session_id', session_id).eq('task_status', 'pending')
            
            if assigned_component:
                query = query.eq('assigned_component', assigned_component)
            
            result = query.order('task_priority', desc=True).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting pending tasks: {e}")
            return []
    
    # Coordinator Decision Logging
    
    def log_decision(self, session_id: str, task_id: str, decision_type: str,
                    decision_prompt: str, decision_response: str = "", reasoning: str = "",
                    confidence_score: float = 0.0, alternatives_considered: List[str] = None,
                    context: Dict[str, Any] = None, model_used: str = "",
                    tokens_used: int = 0, execution_time_ms: int = 0) -> Optional[str]:
        """
        Log a coordinator decision.
        
        Args:
            session_id: Associated session ID
            task_id: Associated task ID
            decision_type: Type of decision
            decision_prompt: The prompt used for decision making
            decision_response: The AI response
            reasoning: Reasoning behind the decision
            confidence_score: Confidence score (0.0 to 1.0)
            alternatives_considered: List of alternatives considered
            context: Decision context
            model_used: Model used for decision
            tokens_used: Tokens used
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            Decision ID if successful, None otherwise
        """
        if not self.is_available():
            return None
            
        try:
            decision_data = {
                'session_id': session_id,
                'task_id': task_id,
                'decision_type': decision_type,
                'decision_prompt': decision_prompt,
                'decision_response': decision_response,
                'reasoning': reasoning,
                'confidence_score': confidence_score,
                'alternatives_considered': alternatives_considered or [],
                'context': context or {},
                'model_used': model_used,
                'tokens_used': tokens_used,
                'execution_time_ms': execution_time_ms
            }
            
            result = self.client.table('coordinator_decisions').insert(decision_data).execute()
            
            if result.data and len(result.data) > 0:
                decision_id = result.data[0]['id']
                logger.debug(f"Logged coordinator decision: {decision_id}")
                return decision_id
            else:
                logger.error("Failed to log coordinator decision")
                return None
                
        except Exception as e:
            logger.error(f"Error logging coordinator decision: {e}")
            return None
    
    # Component Interaction Logging
    
    def log_interaction(self, session_id: str, task_id: str, from_component: str,
                       to_component: str, interaction_type: str, message_content: str = "",
                       request_data: Dict[str, Any] = None, response_data: Dict[str, Any] = None,
                       success: bool = True, error_message: str = "", execution_time_ms: int = 0) -> Optional[str]:
        """
        Log a component interaction.
        
        Args:
            session_id: Associated session ID
            task_id: Associated task ID
            from_component: Source component
            to_component: Target component
            interaction_type: Type of interaction
            message_content: Message content
            request_data: Request data
            response_data: Response data
            success: Whether interaction was successful
            error_message: Error message if failed
            execution_time_ms: Execution time in milliseconds
            
        Returns:
            Interaction ID if successful, None otherwise
        """
        if not self.is_available():
            return None
            
        try:
            interaction_data = {
                'session_id': session_id,
                'task_id': task_id,
                'from_component': from_component,
                'to_component': to_component,
                'interaction_type': interaction_type,
                'message_content': message_content,
                'request_data': request_data or {},
                'response_data': response_data or {},
                'success': success,
                'error_message': error_message,
                'execution_time_ms': execution_time_ms
            }
            
            result = self.client.table('component_interactions').insert(interaction_data).execute()
            
            if result.data and len(result.data) > 0:
                interaction_id = result.data[0]['id']
                logger.debug(f"Logged component interaction: {interaction_id}")
                return interaction_id
            else:
                logger.error("Failed to log component interaction")
                return None
                
        except Exception as e:
            logger.error(f"Error logging component interaction: {e}")
            return None
    
    # Workflow Management
    
    def create_workflow(self, session_id: str, workflow_name: str, workflow_description: str,
                       workflow_steps: List[Dict[str, Any]], input_requirements: Dict[str, Any] = None,
                       output_expectations: Dict[str, Any] = None, estimated_duration_seconds: int = 0,
                       metadata: Dict[str, Any] = None) -> Optional[str]:
        """
        Create an execution workflow.
        
        Args:
            session_id: Associated session ID
            workflow_name: Name of the workflow
            workflow_description: Description of the workflow
            workflow_steps: List of workflow steps
            input_requirements: Input requirements
            output_expectations: Expected outputs
            estimated_duration_seconds: Estimated duration
            metadata: Additional metadata
            
        Returns:
            Workflow ID if successful, None otherwise
        """
        if not self.is_available():
            return None
            
        try:
            workflow_data = {
                'session_id': session_id,
                'workflow_name': workflow_name,
                'workflow_description': workflow_description,
                'workflow_steps': workflow_steps,
                'input_requirements': input_requirements or {},
                'output_expectations': output_expectations or {},
                'estimated_duration_seconds': estimated_duration_seconds,
                'metadata': metadata or {}
            }
            
            result = self.client.table('execution_workflows').insert(workflow_data).execute()
            
            if result.data and len(result.data) > 0:
                workflow_id = result.data[0]['id']
                logger.info(f"Created execution workflow: {workflow_id}")
                return workflow_id
            else:
                logger.error("Failed to create execution workflow")
                return None
                
        except Exception as e:
            logger.error(f"Error creating execution workflow: {e}")
            return None
    
    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an execution workflow.
        
        Args:
            workflow_id: Workflow ID to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available() or not workflow_id:
            return False
            
        try:
            result = self.client.table('execution_workflows').update(updates).eq('id', workflow_id).execute()
            
            if result.data:
                logger.debug(f"Updated workflow {workflow_id}")
                return True
            else:
                logger.error(f"Failed to update workflow {workflow_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating workflow {workflow_id}: {e}")
            return False