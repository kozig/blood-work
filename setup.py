"""
Setup configuration for bloodwork package.
"""
from setuptools import setup, find_packages

with open("README_PACKAGE.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bloodwork",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Framework-agnostic Python package for parsing and analyzing blood work reports",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/bloodwork",
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.7",
    install_requires=[
        "pdfplumber>=0.9.0",
        "pydantic>=2.0.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "python-dateutil>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "flake8>=6.0.0",
        ],
        "mysql": [
            "pymysql>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bloodwork=bloodwork.cli:main",  # Optional CLI tool
        ],
    },
)
