#!/usr/bin/env python3
"""
Setup script for Auto Documentation Generation System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = requirements_path.read_text(encoding="utf-8").splitlines()
    # Filter out comments and empty lines
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="auto-doc-generator",
    version="1.0.0",
    author="Auto Documentation Team",
    author_email="docs@example.com",
    description="Automatic code documentation generation system with AI/ML pipeline support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/manan45/auto-doc-generator",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "diagrams": [
            "diagrams>=0.23.0",
        ],
        "full": [
            "diagrams>=0.23.0",
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ]
    },
    entry_points={
        "console_scripts": [
            "auto-doc-gen=auto_doc_generator.main:main",
            "autodoc=auto_doc_generator.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["templates/*.md", "config/*.yaml"],
    },
    keywords="documentation, automatic, code-analysis, ai, ml, python, mkdocs",
    project_urls={
        "Bug Reports": "https://github.com/manan45/auto-doc-generator/issues",
        "Source": "https://github.com/manan45/auto-doc-generator",
        "Documentation": "https://manan45.github.io/auto-doc-generator/",
    },
)
