"""
Git Operations
Provides real Git operations for version control
"""

import asyncio
import subprocess
import os
from typing import Dict, List, Optional, Any
from datetime import datetime


class GitOperations:
    """
    Real Git operations for version control
    """
    
    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
    
    async def _execute_git_command(self, args: List[str]) -> Dict[str, Any]:
        """
        Execute a git command
        
        Args:
            args: Git command arguments
        
        Returns:
            Dict with execution results
        """
        try:
            command = ['git'] + args
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir
            )
            
            stdout, stderr = await process.communicate()
            
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            return {
                'success': process.returncode == 0,
                'exit_code': process.returncode,
                'stdout': stdout_text,
                'stderr': stderr_text
            }
        except Exception as e:
            return {
                'success': False,
                'exit_code': -1,
                'stdout': '',
                'stderr': str(e)
            }
    
    async def init(self) -> Dict[str, Any]:
        """Initialize a new Git repository"""
        result = await self._execute_git_command(['init'])
        return {
            'success': result['success'],
            'message': 'Repository initialized' if result['success'] else result['stderr'],
            'output': result['stdout']
        }
    
    async def status(self) -> Dict[str, Any]:
        """Get repository status"""
        result = await self._execute_git_command(['status', '--porcelain'])
        
        if not result['success']:
            return {
                'success': False,
                'message': result['stderr'],
                'files': []
            }
        
        # Parse status output
        files = []
        for line in result['stdout'].strip().split('\n'):
            if line:
                status_code = line[:2]
                file_path = line[3:]
                files.append({
                    'status': status_code,
                    'path': file_path
                })
        
        return {
            'success': True,
            'files': files,
            'total': len(files)
        }
    
    async def add(self, files: List[str] = None) -> Dict[str, Any]:
        """Stage files for commit"""
        if files is None:
            args = ['add', '.']
        else:
            args = ['add'] + files
        
        result = await self._execute_git_command(args)
        return {
            'success': result['success'],
            'message': 'Files staged' if result['success'] else result['stderr'],
            'output': result['stdout']
        }
    
    async def commit(self, message: str) -> Dict[str, Any]:
        """Create a commit"""
        result = await self._execute_git_command(['commit', '-m', message])
        return {
            'success': result['success'],
            'message': 'Commit created' if result['success'] else result['stderr'],
            'output': result['stdout']
        }
    
    async def log(self, limit: int = 10) -> Dict[str, Any]:
        """Get commit history"""
        result = await self._execute_git_command([
            'log',
            f'--max-count={limit}',
            '--pretty=format:%H|%an|%ae|%ad|%s',
            '--date=iso'
        ])
        
        if not result['success']:
            return {
                'success': False,
                'message': result['stderr'],
                'commits': []
            }
        
        # Parse log output
        commits = []
        for line in result['stdout'].strip().split('\n'):
            if line:
                parts = line.split('|', 4)
                if len(parts) >= 5:
                    commits.append({
                        'hash': parts[0],
                        'author_name': parts[1],
                        'author_email': parts[2],
                        'date': parts[3],
                        'message': parts[4]
                    })
        
        return {
            'success': True,
            'commits': commits,
            'total': len(commits)
        }
    
    async def branch(self, list_all: bool = False) -> Dict[str, Any]:
        """List branches"""
        args = ['branch']
        if list_all:
            args.append('-a')
        
        result = await self._execute_git_command(args)
        
        if not result['success']:
            return {
                'success': False,
                'message': result['stderr'],
                'branches': []
            }
        
        # Parse branch output
        branches = []
        for line in result['stdout'].strip().split('\n'):
            if line:
                is_current = line.startswith('*')
                branch_name = line[2:].strip()
                branches.append({
                    'name': branch_name,
                    'current': is_current
                })
        
        return {
            'success': True,
            'branches': branches,
            'total': len(branches)
        }
    
    async def checkout(self, branch: str, create: bool = False) -> Dict[str, Any]:
        """Checkout a branch"""
        args = ['checkout']
        if create:
            args.append('-b')
        args.append(branch)
        
        result = await self._execute_git_command(args)
        return {
            'success': result['success'],
            'message': f'Checked out {branch}' if result['success'] else result['stderr'],
            'output': result['stdout']
        }
    
    async def push(self, remote: str = 'origin', branch: str = None) -> Dict[str, Any]:
        """Push changes to remote"""
        args = ['push', remote]
        if branch:
            args.append(branch)
        
        result = await self._execute_git_command(args)
        return {
            'success': result['success'],
            'message': 'Pushed successfully' if result['success'] else result['stderr'],
            'output': result['stdout']
        }
    
    async def pull(self, remote: str = 'origin', branch: str = None) -> Dict[str, Any]:
        """Pull changes from remote"""
        args = ['pull', remote]
        if branch:
            args.append(branch)
        
        result = await self._execute_git_command(args)
        return {
            'success': result['success'],
            'message': 'Pulled successfully' if result['success'] else result['stderr'],
            'output': result['stdout']
        }
    
    async def clone(self, url: str, destination: str = None) -> Dict[str, Any]:
        """Clone a repository"""
        args = ['clone', url]
        if destination:
            args.append(destination)
        
        result = await self._execute_git_command(args)
        return {
            'success': result['success'],
            'message': 'Repository cloned' if result['success'] else result['stderr'],
            'output': result['stdout']
        }
    
    async def remote(self, action: str = 'list', name: str = None, url: str = None) -> Dict[str, Any]:
        """Manage remotes"""
        if action == 'list':
            result = await self._execute_git_command(['remote', '-v'])
            
            if not result['success']:
                return {
                    'success': False,
                    'message': result['stderr'],
                    'remotes': []
                }
            
            # Parse remote output
            remotes = []
            for line in result['stdout'].strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        remotes.append({
                            'name': parts[0],
                            'url': parts[1]
                        })
            
            return {
                'success': True,
                'remotes': remotes
            }
        
        elif action == 'add' and name and url:
            result = await self._execute_git_command(['remote', 'add', name, url])
            return {
                'success': result['success'],
                'message': f'Remote {name} added' if result['success'] else result['stderr']
            }
        
        elif action == 'remove' and name:
            result = await self._execute_git_command(['remote', 'remove', name])
            return {
                'success': result['success'],
                'message': f'Remote {name} removed' if result['success'] else result['stderr']
            }
        
        else:
            return {
                'success': False,
                'message': 'Invalid remote action or missing parameters'
            }
