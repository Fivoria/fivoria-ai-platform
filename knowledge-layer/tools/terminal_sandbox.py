"""
Secure Terminal Sandbox
Provides safe execution of shell commands with isolation and restrictions
"""

import asyncio
import subprocess
import tempfile
import os
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime


class TerminalSandbox:
    """
    Secure sandbox for terminal command execution
    """
    
    # Dangerous commands that are blocked
    BLOCKED_COMMANDS = {
        'rm -rf /',
        'rm -rf /*',
        'mkfs',
        'dd if=',
        ':(){:|:&};:',  # Fork bomb
        'chmod 777 /',
        'chown root',
        'sudo',
        'su',
        'passwd',
        'usermod',
        'userdel',
        'groupdel',
        'shutdown',
        'reboot',
        'halt',
        'poweroff',
        'init 0',
        'killall',
        'pkill -9',
    }
    
    # Allowed commands (whitelist approach for safety)
    ALLOWED_COMMANDS = {
        'ls', 'cd', 'pwd', 'cat', 'echo', 'mkdir', 'touch',
        'cp', 'mv', 'rm', 'grep', 'find', 'head', 'tail',
        'wc', 'sort', 'uniq', 'cut', 'sed', 'awk', 'tr',
        'date', 'whoami', 'id', 'uname', 'df', 'du',
        'ps', 'top', 'htop', 'free', 'netstat', 'ss',
        'ping', 'curl', 'wget', 'git', 'npm', 'pip',
        'python', 'python3', 'node', 'npm', 'yarn',
        'gcc', 'g++', 'make', 'cmake', 'javac', 'java',
        'go', 'rustc', 'cargo', 'ruby', 'gem', 'perl',
        'bash', 'sh', 'zsh', 'fish', 'docker', 'docker-compose'
    }
    
    def __init__(self, workspace_path: Optional[str] = None, timeout_seconds: int = 30):
        self.workspace_path = workspace_path or tempfile.mkdtemp(prefix='fivoria-sandbox-')
        self.timeout_seconds = timeout_seconds
        self._ensure_workspace()
    
    def _ensure_workspace(self):
        """Ensure workspace directory exists"""
        if not os.path.exists(self.workspace_path):
            os.makedirs(self.workspace_path, exist_ok=True)
    
    def _is_command_safe(self, command: str) -> tuple[bool, Optional[str]]:
        """
        Check if command is safe to execute
        
        Returns:
            (is_safe, reason)
        """
        # Check for blocked commands
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in command:
                return False, f"Command contains blocked pattern: {blocked}"
        
        # Extract base command
        parts = command.strip().split()
        if not parts:
            return False, "Empty command"
        
        base_cmd = parts[0]
        
        # Check if base command is in allowed list
        if base_cmd not in self.ALLOWED_COMMANDS:
            return False, f"Command '{base_cmd}' is not in allowed list"
        
        # Check for command chaining that could bypass restrictions
        if '&&' in command or '||' in command or ';' in command:
            return False, "Command chaining is not allowed"
        
        # Check for pipe to shell
        if '| sh' in command or '| bash' in command:
            return False, "Piping to shell is not allowed"
        
        return True, None
    
    async def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a command in the sandbox
        
        Args:
            command: Command to execute
            working_dir: Working directory (defaults to workspace)
            env: Environment variables
        
        Returns:
            Dict with execution results
        """
        # Check command safety
        is_safe, reason = self._is_command_safe(command)
        if not is_safe:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': f"Command blocked: {reason}",
                'execution_time_ms': 0,
                'command': command
            }
        
        # Set working directory
        work_dir = working_dir or self.workspace_path
        if not os.path.exists(work_dir):
            os.makedirs(work_dir, exist_ok=True)
        
        # Prepare environment
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        # Restrict PATH for safety
        process_env['PATH'] = '/usr/local/bin:/usr/bin:/bin'
        
        start_time = datetime.utcnow()
        
        try:
            # Execute command with timeout
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=process_env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout_seconds
                )
                
                stdout_text = stdout.decode('utf-8', errors='replace')
                stderr_text = stderr.decode('utf-8', errors='replace')
                
                end_time = datetime.utcnow()
                execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
                
                return {
                    'success': process.returncode == 0,
                    'exit_code': process.returncode,
                    'stdout': stdout_text,
                    'stderr': stderr_text,
                    'execution_time_ms': execution_time_ms,
                    'command': command,
                    'working_dir': work_dir
                }
                
            except asyncio.TimeoutError:
                # Kill process on timeout
                process.kill()
                await process.communicate()
                
                end_time = datetime.utcnow()
                execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
                
                return {
                    'success': False,
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': f"Command timed out after {self.timeout_seconds} seconds",
                    'execution_time_ms': execution_time_ms,
                    'command': command
                }
                
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e),
                'execution_time_ms': execution_time_ms,
                'command': command
            }
    
    def cleanup(self):
        """Clean up workspace directory"""
        if os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)
    
    def get_workspace_path(self) -> str:
        """Get the workspace path"""
        return self.workspace_path
