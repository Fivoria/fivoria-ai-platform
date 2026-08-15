"""
Fivoria AI Repository Indexer Worker
Indexes and analyzes code repositories for AI understanding
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from celery import Celery
import logging
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

celery_app = Celery(
    'repository_indexer',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task(bind=True)
def index_repository(self, project_id: str, repo_path: str):
    """Index repository for AI understanding"""
    try:
        logger.info(f"Indexing repository {project_id} at {repo_path}")
        
        # Get all files
        files = list_files(repo_path)
        
        # Index each file
        indexed_files = []
        for file_path in files:
            try:
                content = read_file(file_path)
                file_info = {
                    "path": str(file_path.relative_to(repo_path)),
                    "size": len(content),
                    "language": detect_language(file_path),
                    "content": content
                }
                indexed_files.append(file_info)
            except Exception as e:
                logger.warning(f"Failed to index {file_path}: {str(e)}")
        
        # Analyze structure
        structure = analyze_structure(indexed_files)
        
        logger.info(f"Successfully indexed {len(indexed_files)} files")
        return {
            "status": "success",
            "files_indexed": len(indexed_files),
            "structure": structure
        }
        
    except Exception as e:
        logger.error(f"Failed to index repository: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)
        return {"status": "failed", "error": str(e)}

def list_files(repo_path: str) -> list[Path]:
    """List all files in repository"""
    repo = Path(repo_path)
    files = []
    
    for path in repo.rglob('*'):
        if path.is_file() and not should_ignore(path):
            files.append(path)
    
    return files

def should_ignore(path: Path) -> bool:
    """Check if file should be ignored"""
    ignore_patterns = ['.git', 'node_modules', '__pycache__', '.venv', 'dist', 'build']
    return any(pattern in str(path) for pattern in ignore_patterns)

def read_file(file_path: Path) -> str:
    """Read file content"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def detect_language(file_path: Path) -> str:
    """Detect programming language from file extension"""
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
    }
    ext = file_path.suffix.lower()
    return ext_map.get(ext, 'unknown')

def analyze_structure(files: list) -> dict:
    """Analyze repository structure"""
    languages = {}
    total_size = 0
    
    for file_info in files:
        lang = file_info['language']
        languages[lang] = languages.get(lang, 0) + 1
        total_size += file_info['size']
    
    return {
        "total_files": len(files),
        "total_size": total_size,
        "languages": languages,
        "main_language": max(languages.items(), key=lambda x: x[1])[0] if languages else None
    }

if __name__ == "__main__":
    celery_app.start()
