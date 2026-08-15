"""
Agent Orchestration System
Manages multi-agent coordination and task execution
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent states"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(Enum):
    """Task statuses"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Task definition"""
    task_id: str
    description: str
    agent_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class Agent:
    """Agent definition"""
    agent_id: str
    name: str
    role: str
    capabilities: List[str]
    state: AgentState = AgentState.IDLE
    current_task: Optional[str] = None
    performance_metrics: Dict = field(default_factory=dict)


class BaseAgent:
    """Base agent class"""

    def __init__(self, agent_id: str, name: str, role: str, capabilities: List[str]):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.state = AgentState.IDLE
        self.current_task = None

    async def think(self, context: Dict) -> Dict:
        """Think and plan action"""
        raise NotImplementedError

    async def act(self, action: Dict) -> Any:
        """Execute action"""
        raise NotImplementedError

    async def execute_task(self, task: Task) -> Any:
        """Execute a task"""
        self.state = AgentState.THINKING
        self.current_task = task.task_id
        
        try:
            # Think about the task
            context = {
                'task': task.description,
                'metadata': task.metadata
            }
            action_plan = await self.think(context)
            
            # Execute the action
            self.state = AgentState.ACTING
            result = await self.act(action_plan)
            
            self.state = AgentState.COMPLETED
            return result
        except Exception as e:
            logger.error(f"Agent {self.agent_id} failed task {task.task_id}: {e}")
            self.state = AgentState.FAILED
            raise
        finally:
            self.current_task = None


class ToolUsingAgent(BaseAgent):
    """Agent that uses tools"""

    def __init__(self, agent_id: str, name: str, role: str, capabilities: List[str], tools: Dict):
        super().__init__(agent_id, name, role, capabilities)
        self.tools = tools

    async def think(self, context: Dict) -> Dict:
        """Think and plan tool usage"""
        task = context['task']
        
        # Simple planning: select relevant tools
        relevant_tools = []
        for tool_name, tool in self.tools.items():
            if any(cap in task.lower() for cap in tool.get('capabilities', [])):
                relevant_tools.append(tool_name)
        
        return {
            'action': 'use_tools',
            'tools': relevant_tools,
            'task': task
        }

    async def act(self, action: Dict) -> Any:
        """Execute tool actions"""
        results = []
        
        for tool_name in action.get('tools', []):
            if tool_name in self.tools:
                tool = self.tools[tool_name]
                try:
                    # Execute tool using tool framework
                    result = await self.tool_framework.execute_tool(
                        tool_name=tool_name,
                        inputs=action.get('tool_inputs', {}),
                        user_id=context.get('user_id')
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Tool {tool_name} failed: {e}")
        
        return results


class ReasoningAgent(BaseAgent):
    """Agent specialized in reasoning"""

    async def think(self, context: Dict) -> Dict:
        """Think about the problem"""
        task = context['task']
        
        # Decompose task into steps
        steps = self._decompose_task(task)
        
        return {
            'action': 'reason',
            'steps': steps,
            'task': task
        }

    def _decompose_task(self, task: str) -> List[str]:
        """Decompose task into steps"""
        # Simple decomposition
        return [
            f"Analyze: {task}",
            "Identify key components",
            "Plan solution",
            "Execute steps",
            "Verify result"
        ]

    async def act(self, action: Dict) -> Any:
        """Execute reasoning steps"""- woud use tual rasning engin
        results = []
        
        for step in action.get('steps', []):
            # Execute reasoning step (placeholder)
            result = f"Completed: {step}"
            results.append(result)
        
        return results


class AgentOrchestrator:
    """Orchestrates multiple agents"""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: List[Task] = []
        self.running = False

    def register_agent(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.agent_id] = agent
        logger.info(f"Registered agent: {agent.agent_id}")

    def create_task(
        self,
        task_id: str,
        description: str,
        agent_id: Optional[str] = None,
        dependencies: List[str] = None,
        metadata: Dict = None
    ) -> Task:
        """Create a new task"""
        task = Task(
            task_id=task_id,
            description=description,
            agent_id=agent_id,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        self.task_queue.append(task)
        
        logger.info(f"Created task: {task_id}")
        return task

    def select_agent(self, task: Task) -> Optional[BaseAgent]:
        """Select appropriate agent for task"""
        if task.agent_id:
            return self.agents.get(task.agent_id)
        
        # Select agent based on capabilities
        for agent in self.agents.values():
            if agent.state == AgentState.IDLE:
                # Check if agent has relevant capabilities
                task_lower = task.description.lower()
                if any(cap in task_lower for cap in agent.capabilities):
                    return agent
        
        return None

    async def execute_task(self, task: Task) -> Any:
        """Execute a task"""
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.now()
        
        # Check dependencies
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                logger.warning(f"Task {task.task_id} waiting for dependency {dep_id}")
                task.status = TaskStatus.PENDING
                return None
        
        # Select agent
        agent = self.select_agent(task)
        if not agent:
            logger.warning(f"No agent available for task {task.task_id}")
            task.status = TaskStatus.FAILED
            task.error = "No agent available"
            return None
        
        try:
            # Execute task
            result = await agent.execute_task(task)
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            logger.info(f"Task {task.task_id} completed")
            return result
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error(f"Task {task.task_id} failed: {e}")
            raise

    async def run(self):
        """Run the orchestrator"""
        self.running = True
        
        while self.running:
            # Process task queue
            if self.task_queue:
                task = self.task_queue.pop(0)
                await self.execute_task(task)
            
            # Small delay
            await asyncio.sleep(0.1)

    def stop(self):
        """Stop the orchestrator"""
        self.running = False

    def get_status(self) -> Dict:
        """Get orchestrator status"""
        return {
            'agents': {
                agent_id: {
                    'name': agent.name,
                    'state': agent.state.value,
                    'current_task': agent.current_task
                }
                for agent_id, agent in self.agents.items()
            },
            'tasks': {
                task_id: {
                    'description': task.description,
                    'status': task.status.value,
                    'agent_id': task.agent_id
                }
                for task_id, task in self.tasks.items()
            },
            'queue_length': len(self.task_queue)
        }


class MultiAgentSystem:
    """Multi-agent system with coordination"""

    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self.communication_channel: Dict[str, List[Dict]] = {}

    def add_agent(self, agent: BaseAgent):
        """Add agent to system"""
        self.orchestrator.register_agent(agent)

    def create_workflow(self, workflow_id: str, steps: List[Dict]) -> List[Task]:
        """Create a workflow of tasks"""
        tasks = []
        prev_task_id = None
        
        for i, step in enumerate(steps):
            task_id = f"{workflow_id}_step_{i}"
            dependencies = [prev_task_id] if prev_task_id else []
            
            task = self.orchestrator.create_task(
                task_id=task_id,
                description=step['description'],
                agent_id=step.get('agent_id'),
                dependencies=dependencies,
                metadata=step.get('metadata', {})
            )
            
            tasks.append(task)
            prev_task_id = task_id
        
        return tasks

    async def send_message(self, from_agent: str, to_agent: str, message: Dict):
        """Send message between agents"""
        if to_agent not in self.communication_channel:
            self.communication_channel[to_agent] = []
        
        self.communication_channel[to_agent].append({
            'from': from_agent,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })

    async def receive_messages(self, agent_id: str) -> List[Dict]:
        """Receive messages for agent"""
        messages = self.communication_channel.get(agent_id, [])
        self.communication_channel[agent_id] = []
        return messages

    async def run(self):
        """Run the multi-agent system"""
        await self.orchestrator.run()

    def stop(self):
        """Stop the system"""
        self.orchestrator.stop()


def main():
    """Example usage"""
    # Create multi-agent system
    system = MultiAgentSystem()
    
    # Add agents
    tool_agent = ToolUsingAgent(
        agent_id="tool_agent_1",
        name="Tool Agent",
        role="tool_user",
        capabilities=["search", "calculation", "api"],
        tools={
            'search': {'capabilities': ['search', 'find']},
            'calculator': {'capabilities': ['calculation', 'math']}
        }
    )
    
    reasoning_agent = ReasoningAgent(
        agent_id="reasoning_agent_1",
        name="Reasoning Agent",
        role="reasoner",
        capabilities=["reasoning", "planning", "analysis"]
    )
    
    system.add_agent(tool_agent)
    system.add_agent(reasoning_agent)
    
    # Create workflow
    workflow = system.create_workflow(
        workflow_id="example_workflow",
        steps=[
            {'description': "Analyze the problem", 'agent_id': 'reasoning_agent_1'},
            {'description': "Search for information", 'agent_id': 'tool_agent_1'},
            {'description': "Calculate results", 'agent_id': 'tool_agent_1'},
            {'description': "Synthesize answer", 'agent_id': 'reasoning_agent_1'}
        ]
    )
    
    print(f"Created workflow with {len(workflow)} tasks")
    print(f"System status: {system.orchestrator.get_status()}")


if __name__ == "__main__":
    main()
