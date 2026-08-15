"""
Setup script for backend services
Creates virtual environments and installs dependencies
"""

import os
import sys
import subprocess
from pathlib import Path

SERVICES = [
    'services/web-api',
    'services/agent-api',
    'services/project-service',
    'services/model-gateway',
    'services/preview-service',
    'services/api-gateway',
    'services/monitoring',
]

def create_venv(service_path):
    """Create virtual environment for service"""
    venv_path = os.path.join(service_path, 'venv')
    
    if os.path.exists(venv_path):
        print(f"  ✓ Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, '-m', 'venv', venv_path], check=True)
        print(f"  ✓ Virtual environment created")
        return True
    except Exception as e:
        print(f"  ✗ Failed to create virtual environment: {e}")
        return False

def install_dependencies(service_path):
    """Install dependencies for service"""
    venv_python = os.path.join(service_path, 'venv', 'Scripts', 'python.exe') if os.name == 'nt' else os.path.join(service_path, 'venv', 'bin', 'python')
    requirements_path = os.path.join(service_path, 'requirements.txt')
    
    if not os.path.exists(requirements_path):
        print(f"  ! No requirements.txt found")
        return True
    
    try:
        subprocess.run([venv_python, '-m', 'pip', 'install', '-r', requirements_path], check=True)
        print(f"  ✓ Dependencies installed")
        return True
    except Exception as e:
        print(f"  ✗ Failed to install dependencies: {e}")
        return False

def setup_service(service_path):
    """Setup a single service"""
    service_name = os.path.basename(service_path)
    print(f"\nSetting up {service_name}...")
    
    if not os.path.exists(service_path):
        print(f"  ✗ Service directory not found: {service_path}")
        return False
    
    if create_venv(service_path):
        install_dependencies(service_path)
    
    return True

if __name__ == "__main__":
    print("Setting up Fivoria AI Platform backend services...")
    print()
    
    base_path = Path(__file__).parent
    
    for service in SERVICES:
        service_path = base_path / service
        setup_service(str(service_path))
    
    print()
    print("Backend services setup complete!")
    print()
    print("To start services:")
    print("  cd services/web-api && venv\\Scripts\\python main.py")
    print("  cd services/agent-api && venv\\Scripts\\python main.py")
    print("  etc.")
