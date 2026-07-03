"""
Blood Work Analysis Package

A framework-agnostic Python package for parsing, storing, and analyzing
blood work reports from various laboratory formats.

Example usage:

    from bloodwork import ParserService, DatabaseRepository

    # Initialize repository
    repository = DatabaseRepository("postgresql://user:pass@localhost/bloodwork")

    # Parse PDF and store results
    service = ParserService(repository)
    with open("report.pdf", "rb") as f:
        result = service.parse_and_store(f, patient_id="user123")

    print(f"Parsed {result.num_results} test results")
    print(f"Found {result.num_abnormal} abnormal results")
"""

__version__ = "0.1.0"

# Models
from bloodwork.models import (
    BloodTestResult,
    PatientInfo,
    ReferenceRange,
    ResultFlag,
    TestCategory
)

# Repositories
from bloodwork.repositories import (
    AbstractRepository,
    DatabaseRepository,
    RepositoryError
)

# Services
from bloodwork.services import (
    ParserService,
    ParseResult,
    AnalysisService,
    TrendData,
    StatusTransition,
    VisualizationService
)

# Parsers
from bloodwork.parsers import (
    AbstractBloodWorkParser,
    LifeLabsParser,
    ParserError
)

# Configuration
from bloodwork.config import Config, config

__all__ = [
    # Version
    "__version__",

    # Models
    "BloodTestResult",
    "PatientInfo",
    "ReferenceRange",
    "ResultFlag",
    "TestCategory",

    # Repositories
    "AbstractRepository",
    "DatabaseRepository",
    "RepositoryError",

    # Services
    "ParserService",
    "ParseResult",
    "AnalysisService",
    "TrendData",
    "StatusTransition",
    "VisualizationService",

    # Parsers
    "AbstractBloodWorkParser",
    "LifeLabsParser",
    "ParserError",

    # Configuration
    "Config",
    "config",
]
