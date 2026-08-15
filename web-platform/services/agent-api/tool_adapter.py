"""
Tool Adapter
Adapts the Tool Framework for use with Agent API
"""

import sys
import os
from typing import Dict, List, Optional, Any

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from knowledge_layer.tools.tool_framework import (
    ToolRegistry,
    WebSearchTool,
    CalculatorTool,
    PythonSandboxTool,
    DatabaseQueryTool,
    TerminalTool,
    GitTool,
    ToolPermission
)


class ToolAdapter:
    """Adapter for Tool Framework with real implementations"""
    
    def __init__(self):
        self.registry = ToolRegistry()
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        # Register web search tool
        self.registry.register(WebSearchTool())
        
        # Register calculator tool
        self.registry.register(CalculatorTool())
        
        # Register Python sandbox tool
        self.registry.register(PythonSandboxTool())
        
        # Register database query tool
        self.registry.register(DatabaseQueryTool())
        
        # Register terminal sandbox tool
        self.registry.register(TerminalTool())
        
        # Register Git operations tool
        self.registry.register(GitTool())
    
    async def execute_tool(self, tool_name: str, inputs: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a tool"""
        try:
            result = await self.registry.execute_tool(
                tool_name=tool_name,
                inputs=inputs,
                user_id=int(user_id) if user_id else None
            )
            
            return {
                'success': result.success,
                'output': result.output,
                'error': result.error,
                'execution_time_ms': result.execution_time_ms,
                'tool_name': result.tool_name
            }
        except Exception as e:
            return {
                'success': False,
                'output': None,
                'error': str(e),
                'tool_name': tool_name
            }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        tools = []
        for tool_name, tool in self.registry.tools.items():
            tools.append({
                'name': tool.name,
                'description': tool.description,
                'schema': tool.schema,
                'permission': tool.permission.value,
                'requires_sandbox': tool.requires_sandbox,
                'timeout_seconds': tool.timeout_seconds
            })
        return tools
    
    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get tool information"""
        if tool_name in self.registry.tools:
            tool = self.registry.tools[tool_name]
            return {
                'name': tool.name,
                'description': tool.description,
                'schema': tool.schema,
                'permission': tool.permission.value,
                'requires_sandbox': tool.requires_sandbox,
                'timeout_seconds': tool.timeout_seconds
            }
        return None
