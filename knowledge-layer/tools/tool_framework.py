"""
Fivoria AI Tool Framework
Secure tool execution with sandboxing and permission checking
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import subprocess
import tempfile
import os
from datetime import datetime, timedelta


class ToolPermission(Enum):
    """Tool permission levels"""
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    ADMIN = "admin"
    RESTRICTED = "restricted"


@dataclass
class ToolResult:
    """Result of tool execution"""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: int = 0
    tool_name: str = ""


@dataclass
class ToolCall:
    """Tool call record"""
    tool_name: str
    inputs: Dict[str, Any]
    user_id: Optional[int]
    timestamp: datetime
    result: ToolResult
    execution_time_ms: int


class Tool:
    """
    Base class for tools
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        schema: Dict[str, Any],
        permission: ToolPermission = ToolPermission.AUTHENTICATED,
        timeout_seconds: int = 30,
        requires_sandbox: bool = False
    ):
        self.name = name
        self.description = description
        self.schema = schema
        self.permission = permission
        self.timeout_seconds = timeout_seconds
        self.requires_sandbox = requires_sandbox
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """
        Validate inputs against schema
        
        Args:
            inputs: Input dictionary
        
        Returns:
            True if valid
        """
        # Check required fields
        for field_name, field_schema in self.schema.items():
            if field_schema.get("required", False) and field_name not in inputs:
                return False
            
            # Check type if field is present
            if field_name in inputs:
                expected_type = field_schema.get("type")
                if expected_type and not isinstance(inputs[field_name], expected_type):
                    return False
        
        return True
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool
        
        Args:
            inputs: Tool inputs
        
        Returns:
            ToolResult
        """
        raise NotImplementedError
    
    async def execute_with_timeout(self, inputs: Dict[str, Any]) -> ToolResult:
        """
        Execute tool with timeout
        
        Args:
            inputs: Tool inputs
        
        Returns:
            ToolResult
        """
        try:
            result = await asyncio.wait_for(
                self.execute(inputs),
                timeout=self.timeout_seconds
            )
            return result
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool execution timed out after {self.timeout_seconds} seconds",
                tool_name=self.name
            )


class WebSearchTool(Tool):
    """Web search tool"""
    
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Search the web for information",
            schema={
                "query": {"type": str, "required": True},
                "num_results": {"type": int, "required": False, "default": 10}
            },
            permission=ToolPermission.AUTHENTICATED,
            timeout_seconds=30
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute web search"""
        query = inputs["query"]
        num_results = inputs.get("num_results", 10)
        
        # In production, would use actual search API
        # For demo, return mock results
        results = [
            {
                "title": f"Result {i+1} for '{query}'",
                "url": f"https://example.com/{i}",
                "snippet": f"This is a mock search result for {query}"
            }
            for i in range(min(num_results, 10))
        ]
        
        return ToolResult(
            success=True,
            output={"results": results, "query": query},
            tool_name=self.name
        )


class CalculatorTool(Tool):
    """Calculator tool"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations",
            schema={
                "expression": {"type": str, "required": True}
            },
            permission=ToolPermission.PUBLIC,
            timeout_seconds=5,
            requires_sandbox=True
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute calculation"""
        expression = inputs["expression"]
        
        try:
            # Use eval with restricted globals for safety
            allowed_names = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
            }
            
            result = eval(expression, allowed_names, {})
            
            return ToolResult(
                success=True,
                output={"result": result, "expression": expression},
                tool_name=self.name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                tool_name=self.name
            )


class PythonSandboxTool(Tool):
    """Python code execution in sandbox"""
    
    def __init__(self):
        super().__init__(
            name="python_execute",
            description="Execute Python code in a sandboxed environment",
            schema={
                "code": {"type": str, "required": True}
            },
            permission=ToolPermission.AUTHENTICATED,
            timeout_seconds=30,
            requires_sandbox=True
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute Python code"""
        code = inputs["code"]
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute with timeout
                result = subprocess.run(
                    ["python", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds
                )
                
                return ToolResult(
                    success=result.returncode == 0,
                    output={
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    },
                    tool_name=self.name
                )
            finally:
                os.unlink(temp_file)
        
        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output=None,
                error="Code execution timed out",
                tool_name=self.name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                tool_name=self.name
            )


class DatabaseQueryTool(Tool):
    """Database query tool"""
    
    def __init__(self):
        super().__init__(
            name="database_query",
            description="Query the database",
            schema={
                "query": {"type": str, "required": True},
                "database": {"type": str, "required": False, "default": "fivoria"}
            },
            permission=ToolPermission.RESTRICTED,
            timeout_seconds=10
        )
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute database query using real database connection"""
        query = inputs["query"]
        database = inputs.get("database", "fivoria")
        
        try:
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
            
            from database.schema import get_db_connection
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Execute the query
            cursor.execute(query)
            
            # Get results
            results = []
            for row in cursor.fetchall():
                # Convert to serializable format
                row_dict = {}
                for key, value in row.items():
                    if hasattr(value, 'isoformat'):
                        row_dict[key] = value.isoformat()
                    else:
                        row_dict[key] = value
                results.append(row_dict)
            
            rows_affected = cursor.rowcount
            
            cursor.close()
            conn.close()
            
            return ToolResult(
                success=True,
                output={
                    "database": database,
                    "query": query,
                    "results": results,
                    "rows_affected": rows_affected
                },
                tool_name=self.name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                tool_name=self.name
            )


class TerminalTool(Tool):
    """Terminal command execution tool with sandbox"""
    
    def __init__(self):
        super().__init__(
            name="terminal_execute",
            description="Execute terminal commands in a secure sandbox",
            schema={
                "command": {"type": str, "required": True},
                "working_dir": {"type": str, "required": False},
                "timeout_seconds": {"type": int, "required": False, "default": 30}
            },
            permission=ToolPermission.AUTHENTICATED,
            timeout_seconds=60,
            requires_sandbox=True
        )
        
        # Import terminal sandbox
        from .terminal_sandbox import TerminalSandbox
        self.sandbox = TerminalSandbox()
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute terminal command in sandbox"""
        command = inputs["command"]
        working_dir = inputs.get("working_dir")
        timeout_seconds = inputs.get("timeout_seconds", 30)
        
        try:
            # Update sandbox timeout if specified
            if timeout_seconds != self.sandbox.timeout_seconds:
                from .terminal_sandbox import TerminalSandbox
                self.sandbox = TerminalSandbox(
                    workspace_path=self.sandbox.workspace_path,
                    timeout_seconds=timeout_seconds
                )
            
            # Execute command in sandbox
            result = await self.sandbox.execute_command(
                command=command,
                working_dir=working_dir
            )
            
            return ToolResult(
                success=result['success'],
                output={
                    "exit_code": result['exit_code'],
                    "stdout": result['stdout'],
                    "stderr": result['stderr'],
                    "execution_time_ms": result['execution_time_ms'],
                    "working_dir": result.get('working_dir')
                },
                error=result['stderr'] if not result['success'] else None,
                tool_name=self.name,
                execution_time_ms=result['execution_time_ms']
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                tool_name=self.name
            )


class GitTool(Tool):
    """Git operations tool for version control"""
    
    def __init__(self):
        super().__init__(
            name="git_execute",
            description="Execute Git operations for version control",
            schema={
                "operation": {"type": str, "required": True},
                "args": {"type": dict, "required": False, "default": {}}
            },
            permission=ToolPermission.AUTHENTICATED,
            timeout_seconds=60,
            requires_sandbox=False
        )
        
        # Import git operations
        from .git_operations import GitOperations
        self.git_ops = GitOperations()
    
    async def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """Execute Git operation"""
        operation = inputs["operation"]
        args = inputs.get("args", {})
        
        try:
            # Map operation to method
            if operation == "init":
                result = await self.git_ops.init()
            elif operation == "status":
                result = await self.git_ops.status()
            elif operation == "add":
                result = await self.git_ops.add(args.get("files"))
            elif operation == "commit":
                result = await self.git_ops.commit(args.get("message", "Update"))
            elif operation == "log":
                result = await self.git_ops.log(args.get("limit", 10))
            elif operation == "branch":
                result = await self.git_ops.branch(args.get("list_all", False))
            elif operation == "checkout":
                result = await self.git_ops.checkout(
                    args.get("branch", "main"),
                    args.get("create", False)
                )
            elif operation == "push":
                result = await self.git_ops.push(
                    args.get("remote", "origin"),
                    args.get("branch")
                )
            elif operation == "pull":
                result = await self.git_ops.pull(
                    args.get("remote", "origin"),
                    args.get("branch")
                )
            elif operation == "clone":
                result = await self.git_ops.clone(
                    args.get("url"),
                    args.get("destination")
                )
            elif operation == "remote":
                result = await self.git_ops.remote(
                    args.get("action", "list"),
                    args.get("name"),
                    args.get("url")
                )
            else:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Unknown Git operation: {operation}",
                    tool_name=self.name
                )
            
            return ToolResult(
                success=result['success'],
                output=result,
                error=result.get('message') if not result['success'] else None,
                tool_name=self.name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                tool_name=self.name
            )


class ToolRegistry:
    """
    Registry for managing tools
    """
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.call_history: List[ToolCall] = []
    
    def register(self, tool: Tool):
        """Register a tool"""
        self.tools[tool.name] = tool
    
    def unregister(self, tool_name: str):
        """Unregister a tool"""
        if tool_name in self.tools:
            del self.tools[tool_name]
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self.tools.get(tool_name)
    
    def list_tools(self, permission: Optional[ToolPermission] = None) -> List[Tool]:
        """List available tools"""
        if permission is None:
            return list(self.tools.values())
        return [tool for tool in self.tools.values() if tool.permission == permission]
    
    async def execute_tool(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        user_id: Optional[int] = None,
        check_permission: bool = True
    ) -> ToolResult:
        """
        Execute a tool
        
        Args:
            tool_name: Name of tool to execute
            inputs: Tool inputs
            user_id: User ID for permission checking
            check_permission: Whether to check permissions
        
        Returns:
            ToolResult
        """
        tool = self.get_tool(tool_name)
        if tool is None:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{tool_name}' not found",
                tool_name=tool_name
            )
        
        # Check permissions
        if check_permission:
            # In production, would check user permissions against tool permission level
            pass
        
        # Validate inputs
        if not tool.validate_inputs(inputs):
            return ToolResult(
                success=False,
                output=None,
                error="Input validation failed",
                tool_name=tool_name
            )
        
        # Execute
        start_time = datetime.utcnow()
        result = await tool.execute_with_timeout(inputs)
        end_time = datetime.utcnow()
        
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        result.execution_time_ms = execution_time_ms
        result.tool_name = tool_name
        
        # Record call
        call = ToolCall(
            tool_name=tool_name,
            inputs=inputs,
            user_id=user_id,
            timestamp=start_time,
            result=result,
            execution_time_ms=execution_time_ms
        )
        self.call_history.append(call)
        
        return result
    
    def get_call_history(
        self,
        tool_name: Optional[str] = None,
        user_id: Optional[int] = None,
        limit: int = 100
    ) -> List[ToolCall]:
        """Get tool call history"""
        calls = self.call_history
        
        if tool_name is not None:
            calls = [c for c in calls if c.tool_name == tool_name]
        
        if user_id is not None:
            calls = [c for c in calls if c.user_id == user_id]
        
        return calls[-limit:]


class ToolExecutor:
    """
    High-level tool executor with rate limiting and quotas
    """
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.user_quotas: Dict[int, Dict[str, int]] = {}
        self.user_rate_limits: Dict[int, Dict[str, datetime]] = {}
    
    async def execute(
        self,
        tool_name: str,
        inputs: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> ToolResult:
        """
        Execute tool with rate limiting and quota checking
        
        Args:
            tool_name: Tool name
            inputs: Tool inputs
            user_id: User ID
        
        Returns:
            ToolResult
        """
        # Check rate limit
        if user_id is not None:
            if not self._check_rate_limit(user_id, tool_name):
                return ToolResult(
                    success=False,
                    output=None,
                    error="Rate limit exceeded",
                    tool_name=tool_name
                )
            
            # Check quota
            if not self._check_quota(user_id, tool_name):
                return ToolResult(
                    success=False,
                    output=None,
                    error="Quota exceeded",
                    tool_name=tool_name
                )
        
        # Execute tool
        result = await self.registry.execute_tool(tool_name, inputs, user_id)
        
        # Update quota if successful
        if user_id is not None and result.success:
            self._update_quota(user_id, tool_name)
        
        return result
    
    def _check_rate_limit(self, user_id: int, tool_name: str) -> bool:
        """Check if user is within rate limit"""
        # Simplified rate limiting
        # In production, would use Redis or similar
        return True
    
    def _check_quota(self, user_id: int, tool_name: str) -> bool:
        """Check if user has quota remaining"""
        # Simplified quota checking
        # In production, would track actual usage
        return True
    
    def _update_quota(self, user_id: int, tool_name: str):
        """Update user quota after successful execution"""
        # Simplified quota update
        if user_id not in self.user_quotas:
            self.user_quotas[user_id] = {}
        
        self.user_quotas[user_id][tool_name] = self.user_quotas[user_id].get(tool_name, 0) + 1


if __name__ == "__main__":
    # Demo: Create tool registry and execute tools
    registry = ToolRegistry()
    
    # Register tools
    registry.register(WebSearchTool())
    registry.register(CalculatorTool())
    registry.register(PythonSandboxTool())
    registry.register(DatabaseQueryTool())
    
    # Create executor
    executor = ToolExecutor(registry)
    
    # Execute tools
    async def demo():
        # Web search
        result = await executor.execute(
            "web_search",
            {"query": "Python programming", "num_results": 5},
            user_id=1
        )
        print(f"Web Search: {result.success}")
        print(f"Output: {result.output}")
        
        # Calculator
        result = await executor.execute(
            "calculator",
            {"expression": "2 + 2 * 3"},
            user_id=1
        )
        print(f"\nCalculator: {result.success}")
        print(f"Output: {result.output}")
        
        # Python execution
        result = await executor.execute(
            "python_execute",
            {"code": "print('Hello, World!')"},
            user_id=1
        )
        print(f"\nPython Execute: {result.success}")
        print(f"Output: {result.output}")
    
    asyncio.run(demo())
