"""
Scheduled task interfaces.

This module defines the interfaces for components in the Scheduled layer,
which is responsible for managing periodic tasks and background jobs.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import enum

class TaskStatus(str, enum.Enum):
    """Status of a scheduled task"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskResult:
    """Result of a scheduled task execution"""
    
    def __init__(
        self,
        success: bool = True,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        logs: Optional[List[str]] = None,
        duration: Optional[float] = None
    ):
        self.success = success
        self.data = data or {}
        self.error = error
        self.logs = logs or []
        self.duration = duration
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task result to dictionary"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "logs": self.logs,
            "duration": self.duration,
            "timestamp": self.timestamp.isoformat()
        }

class TaskSchedule:
    """Schedule configuration for a task"""
    
    def __init__(
        self,
        interval: Optional[timedelta] = None,
        cron_expression: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: timedelta = timedelta(minutes=5)
    ):
        self.interval = interval
        self.cron_expression = cron_expression
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule to dictionary"""
        result = {
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay.total_seconds()
        }
        
        if self.interval:
            result["interval_seconds"] = self.interval.total_seconds()
        
        if self.cron_expression:
            result["cron_expression"] = self.cron_expression
            
        return result

class ScheduledTask(ABC):
    """Interface for scheduled tasks"""
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any] = None) -> TaskResult:
        """
        Execute the task
        
        Args:
            params: Optional parameters for the task
            
        Returns:
            Task execution result
        """
        pass
    
    @abstractmethod
    def get_schedule(self) -> TaskSchedule:
        """
        Get the scheduling configuration for this task
        
        Returns:
            TaskSchedule object defining when the task should run
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name of the task
        
        Returns:
            Task name
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        Get a description of what the task does
        
        Returns:
            Task description
        """
        pass

class TaskManager(ABC):
    """Interface for task schedulers and managers"""
    
    @abstractmethod
    async def schedule_task(self, task: ScheduledTask) -> str:
        """
        Schedule a task for execution
        
        Args:
            task: Task to schedule
            
        Returns:
            Task ID
        """
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled task
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if cancellation was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get the status of a task
        
        Args:
            task_id: ID of the task to check
            
        Returns:
            Task status if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """
        Get the result of a completed task
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task result if available, None otherwise
        """
        pass