"""
Recovery and Cancellation Manager
Handles task recovery, cancellation, and cleanup
"""

import asyncio
from typing import Dict, Optional, Set
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    FAILED = "failed"


class RecoveryManager:
    """Manages task recovery and cancellation"""
    
    def __init__(self):
        # Store task states: {task_id: TaskState}
        self.task_states: Dict[str, Dict] = {}
        # Store cancellation requests: {task_id: cancellation_reason}
        self.cancellation_requests: Dict[str, str] = {}
        # Store paused tasks: {task_id: pause_timestamp}
        self.paused_tasks: Dict[str, datetime] = {}
    
    def register_task(self, task_id: str, user_id: str, task_type: str, metadata: Optional[Dict] = None):
        """Register a new task for tracking"""
        self.task_states[task_id] = {
            "task_id": task_id,
            "user_id": user_id,
            "task_type": task_type,
            "status": TaskStatus.PENDING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "checkpoint": None
        }
        logger.info(f"Registered task {task_id} for user {user_id}")
    
    def update_task_status(self, task_id: str, status: TaskStatus, checkpoint: Optional[Dict] = None):
        """Update task status"""
        if task_id in self.task_states:
            self.task_states[task_id]["status"] = status.value
            self.task_states[task_id]["updated_at"] = datetime.utcnow().isoformat()
            
            if checkpoint:
                self.task_states[task_id]["checkpoint"] = checkpoint
            
            logger.info(f"Task {task_id} status updated to {status.value}")
    
    def request_cancellation(self, task_id: str, reason: str = "User cancelled") -> bool:
        """Request cancellation of a task"""
        if task_id not in self.task_states:
            return False
        
        task_status = self.task_states[task_id]["status"]
        
        # Only allow cancellation for running or pending tasks
        if task_status in [TaskStatus.RUNNING.value, TaskStatus.PENDING.value]:
            self.cancellation_requests[task_id] = reason
            logger.info(f"Cancellation requested for task {task_id}: {reason}")
            return True
        
        return False
    
    def is_cancellation_requested(self, task_id: str) -> tuple[bool, Optional[str]]:
        """Check if cancellation was requested for a task"""
        if task_id in self.cancellation_requests:
            return True, self.cancellation_requests[task_id]
        return False, None
    
    def acknowledge_cancellation(self, task_id: str):
        """Acknowledge that cancellation was processed"""
        if task_id in self.cancellation_requests:
            del self.cancellation_requests[task_id]
            self.update_task_status(task_id, TaskStatus.CANCELLED)
    
    def pause_task(self, task_id: str) -> bool:
        """Pause a running task"""
        if task_id not in self.task_states:
            return False
        
        task_status = self.task_states[task_id]["status"]
        
        if task_status == TaskStatus.RUNNING.value:
            self.paused_tasks[task_id] = datetime.utcnow()
            self.update_task_status(task_id, TaskStatus.PAUSED)
            logger.info(f"Task {task_id} paused")
            return True
        
        return False
    
    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        if task_id not in self.paused_tasks:
            return False
        
        del self.paused_tasks[task_id]
        self.update_task_status(task_id, TaskStatus.RUNNING)
        logger.info(f"Task {task_id} resumed")
        return True
    
    def get_task_state(self, task_id: str) -> Optional[Dict]:
        """Get current task state"""
        return self.task_states.get(task_id)
    
    def get_all_tasks(self, user_id: Optional[str] = None) -> list:
        """Get all tasks, optionally filtered by user"""
        tasks = list(self.task_states.values())
        
        if user_id:
            tasks = [t for t in tasks if t["user_id"] == user_id]
        
        return tasks
    
    def cleanup_old_tasks(self, older_than_hours: int = 24):
        """Clean up old completed/failed tasks"""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        
        tasks_to_remove = []
        
        for task_id, task_state in self.task_states.items():
            task_time = datetime.fromisoformat(task_state["updated_at"])
            
            # Remove old completed/failed/cancelled tasks
            if (task_state["status"] in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value] 
                and task_time < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.task_states[task_id]
            logger.info(f"Cleaned up old task {task_id}")
        
        return len(tasks_to_remove)
    
    def create_checkpoint(self, task_id: str, checkpoint_data: Dict):
        """Create a checkpoint for task recovery"""
        if task_id in self.task_states:
            self.task_states[task_id]["checkpoint"] = {
                "data": checkpoint_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.info(f"Checkpoint created for task {task_id}")
    
    def recover_from_checkpoint(self, task_id: str) -> Optional[Dict]:
        """Recover task from checkpoint"""
        if task_id in self.task_states:
            checkpoint = self.task_states[task_id].get("checkpoint")
            if checkpoint:
                logger.info(f"Recovering task {task_id} from checkpoint")
                return checkpoint.get("data")
        return None
    
    def get_statistics(self) -> Dict:
        """Get recovery manager statistics"""
        status_counts = {}
        
        for task_state in self.task_states.values():
            status = task_state["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": len(self.task_states),
            "status_breakdown": status_counts,
            "cancellation_requests": len(self.cancellation_requests),
            "paused_tasks": len(self.paused_tasks),
            "tasks_with_checkpoints": sum(1 for t in self.task_states.values() if t.get("checkpoint"))
        }


# Global recovery manager instance
recovery_manager = RecoveryManager()
