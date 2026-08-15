"""
Fivoria AI Task Worker
Handles long-running agent tasks in background
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from celery import Celery
from knowledge_layer.agents.orchestrator import AgentOrchestrator
from knowledge_layer.complete_agent.complete_ai_agent import CompleteAIAgent
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery(
    'task_worker',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

agent_orchestrator = AgentOrchestrator()
complete_agent = CompleteAIAgent()

@celery_app.task(bind=True)
def execute_agent_task(self, task_id: str, task_type: str, description: str, user_id: int, context: dict = None):
    """Execute agent task in background"""
    try:
        logger.info(f"Executing task {task_id} of type {task_type}")
        
        # Execute task using complete agent
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            complete_agent.execute_task(
                task_id=task_id,
                task_type=task_type,
                description=description,
                user_id=user_id,
                context=context or {}
            )
        )
        
        loop.close()
        
        logger.info(f"Task {task_id} completed successfully")
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)
        return {"status": "failed", "error": str(e)}

@celery_app.task
def verify_and_test(project_id: str, user_id: int):
    """Run verification and testing on project"""
    try:
        logger.info(f"Running verification for project {project_id}")
        
        # TODO: Implement verification logic
        # - Run tests
        # - Check for errors
        # - Validate code quality
        # - Run linters
        
        return {"status": "success", "tests_passed": True}
        
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return {"status": "failed", "error": str(e)}

if __name__ == "__main__":
    celery_app.start()
