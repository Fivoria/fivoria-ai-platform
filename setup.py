"""
Fivoria AI Platform Setup
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="fivoria-ai-platform",
    version="0.1.0",
    author="Fivoria AI",
    author_email="ai@fivoria.com",
    description="Fivoria AI Platform - Independent Foundation Model Infrastructure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fivoria/fivoria-ai-platform",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "isort>=5.12.0",
            "flake8>=6.1.0",
            "mypy>=1.7.0",
        ],
        "distributed": [
            "deepspeed>=0.12.0",
        ],
        "gpu": [
            "faiss-gpu>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "fivoria-train=fivoria_ai.model_platform.training.train:main",
            "fivoria-inference=fivoria_ai.inference.gateway:main",
            "fivoria-eval=fivoria_ai.model_platform.evaluation.evaluate:main",
        ],
    },
)
