# Blood Work Analysis - Modular Architecture Refactoring Plan

## Overview
Refactor the proof-of-concept blood work analysis code into a framework-agnostic Python package with clean API boundaries, suitable for integration into Django, Flask, FastAPI, or any other web framework.

## Goals
1. Create reusable Python package with clear separation of concerns
2. Support multiple patients/users without built-in authentication (delegate to parent app)
3. Use PostgreSQL/MySQL database for storage
4. Focus on LifeLabs format for now (design for future extensibility)
5. Provide both programmatic API and CLI interface
6. Enable integration: User uploads PDF → Parse & store → Visualize trends + flag out-of-range tests

## Current State Analysis
- **scrape_bloodwork_advanced.py** (480 lines): Monolithic LifeLabsParser class with parsing, storage, and output mixed together
- **scrape_bloodwork_pdf.py** (293 lines): Similar fallback parser
- **visualize_bloodwork.py** (211 lines): Hardcoded matplotlib visualization with patient name embedded
- **Issues**: Hardcoded paths, no data models, no abstraction layers, PHI exposure in code

## Proposed Architecture

```
bloodwork/                           # Main package
├── __init__.py                      # Package exports
├── models/                          # Data models
│   ├── __init__.py
│   ├── result.py                    # BloodTestResult, ReferenceRange models
│   ├── patient.py                   # PatientInfo model
│   └── enums.py                     # ResultFlag, TestCategory enums
├── parsers/                         # PDF parsing layer
│   ├── __init__.py
│   ├── base.py                      # AbstractBloodWorkParser
│   ├── lifelabs.py                  # LifeLabsParser (refactored)
│   └── extractors/                  # Extraction utilities
│       ├── __init__.py
│       ├── table.py                 # Table extraction logic
│       ├── text.py                  # Text pattern matching
│       ├── date.py                  # Date parsing
│       └── metadata.py              # Patient info extraction
├── repositories/                    # Storage layer
│   ├── __init__.py
│   ├── base.py                      # AbstractRepository interface
│   ├── database.py                  # SQLAlchemy repository
│   └── models.py                    # SQLAlchemy ORM models
├── services/                        # Business logic layer
│   ├── __init__.py
│   ├── parser_service.py            # Orchestrate PDF parsing
│   ├── analysis_service.py          # Trend analysis, out-of-range detection
│   └── visualization_service.py     # Generate visualization data
├── config/                          # Configuration
│   ├── __init__.py
│   ├── defaults.py                  # Default values
│   └── patterns.py                  # LifeLabs patterns (sections, regex)
└── utils/                           # Shared utilities
    ├── __init__.py
    ├── validation.py                # Input validation
    └── normalization.py             # Data normalization
```

## Implementation Plan

### Phase 1: Foundation - Data Models (Week 1, Days 1-2)

**File: bloodwork/models/result.py**
- Create `ReferenceRange` model with min/max values and parsing logic
- Create `BloodTestResult` model (replaces plain dict)
  - Fields: id, patient_id, date, test_name, result (float), result_raw (str), reference_range, units, flag, created_at
  - Validation: numeric result, valid date format, test name length
  - Methods: `is_abnormal()`, `to_dict()`, `from_dict()`

**File: bloodwork/models/patient.py**
- Create `PatientInfo` model
  - Fields: patient_id, name (optional), age, gender, dob
  - NOTE: Authentication/user management handled by parent app
  - `patient_id` is the foreign key linking to parent app's user system

**File: bloodwork/models/enums.py**
- Create `ResultFlag` enum: NORMAL, HIGH, LOW
- Create `TestCategory` enum: LIPID_PANEL, LIVER_FUNCTION, CBC, HORMONES, etc.

**Technology**: Use Pydantic BaseModel for validation and serialization

### Phase 2: Database Layer (Week 1, Days 3-4)

**File: bloodwork/repositories/models.py**
- Create SQLAlchemy ORM models matching Pydantic models
- Tables:
  - `blood_test_results`: Stores all test results
  - `patient_info`: Stores patient metadata (linked to parent app via patient_id)
- Indexes: patient_id, date, test_name, flag
- Relationships: patient → results (one-to-many)

**File: bloodwork/repositories/base.py**
- Create `AbstractRepository` interface:
  - `save_results(results: List[BloodTestResult]) -> None`
  - `get_results(patient_id: str, start_date=None, end_date=None) -> List[BloodTestResult]`
  - `get_abnormal_results(patient_id: str) -> List[BloodTestResult]`
  - `get_patient_info(patient_id: str) -> Optional[PatientInfo]`
  - `save_patient_info(patient: PatientInfo) -> None`

**File: bloodwork/repositories/database.py**
- Implement `DatabaseRepository` using SQLAlchemy
- Connection string from config (PostgreSQL/MySQL)
- Transaction handling, error handling

**File: bloodwork/alembic/** (optional but recommended)
- Database migration scripts for schema versioning

### Phase 3: Parser Refactoring (Week 1, Days 5-7)

**File: bloodwork/parsers/extractors/table.py**
- Extract table parsing logic from LifeLabsParser
- Class: `TableExtractor`
  - `extract_tables(page) -> List[Table]`
  - `parse_table_row(row, headers) -> Optional[BloodTestResult]`
- Remove hardcoded column matching, make configurable

**File: bloodwork/parsers/extractors/text.py**
- Extract text parsing logic
- Class: `TextExtractor`
  - `parse_text_line(line, patterns) -> Optional[BloodTestResult]`
  - Configurable regex patterns from config

**File: bloodwork/parsers/extractors/date.py**
- Extract date parsing logic
- Class: `DateExtractor`
  - `extract_date(text, patterns) -> Optional[date]`
  - `parse_date(date_str, formats) -> Optional[date]`

**File: bloodwork/parsers/extractors/metadata.py**
- Extract patient info parsing
- Class: `MetadataExtractor`
  - `extract_patient_info(text) -> PatientInfo`

**File: bloodwork/parsers/base.py**
- Create `AbstractBloodWorkParser` base class
  - Constructor: `__init__(pdf_file: BinaryIO, patient_id: str)`
  - Abstract methods: `parse() -> Tuple[PatientInfo, List[BloodTestResult]]`
  - Shared utilities: deduplication, validation

**File: bloodwork/parsers/lifelabs.py**
- Refactor `LifeLabsParser` to extend `AbstractBloodWorkParser`
- Use injected extractors (table, text, date, metadata)
- Remove all print statements (use logging)
- Remove hardcoded paths and filenames
- Constructor accepts file-like object (not file path) for web upload support
- Return structured data (not write to CSV)

**Critical Changes:**
```python
# OLD:
parser = LifeLabsParser('/path/to/file.pdf')
results = parser.parse_pdf()
parser.export_to_csv('output.csv')

# NEW:
from io import BytesIO
parser = LifeLabsParser(pdf_file=uploaded_file, patient_id='user123')
patient_info, results = parser.parse()  # Returns models, doesn't write files
```

### Phase 4: Service Layer (Week 2, Days 1-3)

**File: bloodwork/services/parser_service.py**
- Create `ParserService` class to orchestrate parsing workflow
- Methods:
  - `parse_and_store(pdf_file: BinaryIO, patient_id: str) -> ParseResult`
  - `get_parser(file_type: str) -> AbstractBloodWorkParser` (factory method)
- Uses repository to save results
- Handles errors gracefully
- Returns summary: `ParseResult(patient_info, num_results, num_abnormal, errors)`

**File: bloodwork/services/analysis_service.py**
- Create `AnalysisService` class for trend analysis
- Methods:
  - `get_abnormal_results(patient_id: str) -> List[BloodTestResult]`
  - `get_test_trend(patient_id: str, test_name: str) -> TrendData`
  - `get_all_trends(patient_id: str) -> Dict[str, TrendData]`
  - `group_by_category(results: List[BloodTestResult]) -> Dict[TestCategory, List]`
- Returns structured data (not charts)

**File: bloodwork/services/visualization_service.py**
- Create `VisualizationService` class
- Generate JSON data structures suitable for client-side charting (Chart.js, D3, etc.)
- Methods:
  - `generate_chart_data(results: List[BloodTestResult]) -> Dict`
  - `generate_summary_stats(results: List[BloodTestResult]) -> SummaryStats`
- No matplotlib, no patient names in output

**Example Visualization Output:**
```json
{
  "test_name": "HDL Cholesterol",
  "unit": "mmol/L",
  "reference_range": {"min": 1.0, "max": null},
  "data_points": [
    {"date": "2024-01-15", "value": 0.97, "flag": "LOW"},
    {"date": "2024-06-10", "value": 1.12, "flag": "NORMAL"}
  ],
  "trend": "improving"
}
```

### Phase 5: Configuration (Week 2, Day 4)

**File: bloodwork/config/defaults.py**
- Default configuration values
- Database connection defaults
- Parser settings (max file size, supported formats)

**File: bloodwork/config/patterns.py**
- LifeLabs-specific patterns:
  - `LIFELABS_SECTIONS` = ['Hematology', 'General Chemistry', ...]
  - `DATE_PATTERNS` = [r'Date of Service[:\s]*...', ...]
  - `TEST_REGEX_PATTERNS` = [compiled patterns]
  - `PATIENT_FIELD_PATTERNS` = {...}

**File: bloodwork/config/__init__.py**
- Export `Config` class
- Load from environment variables (DATABASE_URL, etc.)
- Override defaults with env vars

### Phase 6: Public API (Week 2, Days 5-6)

**File: bloodwork/__init__.py**
- Clean public API exports
```python
from bloodwork.services import ParserService, AnalysisService, VisualizationService
from bloodwork.models import BloodTestResult, PatientInfo
from bloodwork.repositories import DatabaseRepository

# Simple usage:
# parser_service = ParserService(repository)
# result = parser_service.parse_and_store(pdf_file, patient_id='user123')
```

**File: bloodwork/api.py** (optional convenience wrapper)
- High-level functions for common operations:
```python
def initialize_database(connection_string: str) -> None:
    """Create tables and set up database"""

def parse_pdf(pdf_file: BinaryIO, patient_id: str, repository=None) -> ParseResult:
    """Parse PDF and store results. Auto-creates repository if not provided."""

def get_patient_results(patient_id: str, repository=None) -> List[BloodTestResult]:
    """Retrieve all results for a patient"""

def get_visualization_data(patient_id: str, repository=None) -> Dict:
    """Get chart-ready data for frontend"""
```

### Phase 7: Integration Examples (Week 2, Day 7)

**File: examples/django_integration.py**
- Example Django view using the package
```python
from django.http import JsonResponse
from django.views import View
from bloodwork import ParserService, DatabaseRepository

class BloodWorkUploadView(View):
    def post(self, request):
        pdf_file = request.FILES['pdf']
        patient_id = request.user.id  # From Django auth

        repository = DatabaseRepository(connection_string=settings.DATABASE_URL)
        service = ParserService(repository)
        result = service.parse_and_store(pdf_file, patient_id)

        return JsonResponse({
            'success': True,
            'num_results': result.num_results,
            'num_abnormal': result.num_abnormal
        })
```

**File: examples/fastapi_integration.py**
- Example FastAPI endpoint
```python
from fastapi import FastAPI, UploadFile
from bloodwork import parse_pdf, get_visualization_data

@app.post("/bloodwork/upload")
async def upload_bloodwork(file: UploadFile, patient_id: str):
    result = parse_pdf(file.file, patient_id)
    return result.to_dict()

@app.get("/bloodwork/visualize/{patient_id}")
async def visualize(patient_id: str):
    return get_visualization_data(patient_id)
```

**File: examples/flask_integration.py**
- Example Flask route

### Phase 8: Testing & Documentation (Ongoing)

**File: tests/test_models.py**
- Unit tests for Pydantic models
- Test validation, serialization

**File: tests/test_parsers.py**
- Unit tests for parser extractors
- Mock PDF data

**File: tests/test_repositories.py**
- Integration tests with test database
- Test CRUD operations

**File: tests/test_services.py**
- Test service layer orchestration
- Mock repository

**File: README.md**
- Installation instructions
- Quick start guide
- API documentation
- Integration examples

**File: docs/**
- Detailed documentation
- Architecture diagrams
- Contributing guide

## Migration Strategy

### Step 1: Create new package structure
- Set up bloodwork/ directory with submodules
- Install dependencies: pydantic, sqlalchemy, psycopg2, pdfplumber

### Step 2: Extract models (non-breaking)
- Create Pydantic models
- Keep old dict format working alongside

### Step 3: Extract parsers (parallel development)
- Create new modular parser
- Keep old monolithic parser until new one is tested
- Compare outputs to ensure parity

### Step 4: Create repository layer
- Set up database schema
- Implement DatabaseRepository
- Migration script to import existing CSV data

### Step 5: Create service layer
- Build services using new components
- Create integration examples

### Step 6: Deprecate old files
- Mark scrape_bloodwork_advanced.py as deprecated
- Update CLAUDE.md with new architecture
- Keep old files for reference until fully migrated

## File Changes Required

### New Files (to create):
1. `bloodwork/__init__.py` - Package initialization
2. `bloodwork/models/result.py` - BloodTestResult, ReferenceRange
3. `bloodwork/models/patient.py` - PatientInfo
4. `bloodwork/models/enums.py` - Enums
5. `bloodwork/parsers/base.py` - Abstract parser
6. `bloodwork/parsers/lifelabs.py` - Refactored parser
7. `bloodwork/parsers/extractors/table.py` - Table extraction
8. `bloodwork/parsers/extractors/text.py` - Text extraction
9. `bloodwork/parsers/extractors/date.py` - Date parsing
10. `bloodwork/parsers/extractors/metadata.py` - Patient info
11. `bloodwork/repositories/base.py` - Repository interface
12. `bloodwork/repositories/database.py` - SQLAlchemy repository
13. `bloodwork/repositories/models.py` - ORM models
14. `bloodwork/services/parser_service.py` - Parser orchestration
15. `bloodwork/services/analysis_service.py` - Trend analysis
16. `bloodwork/services/visualization_service.py` - Chart data
17. `bloodwork/config/defaults.py` - Configuration
18. `bloodwork/config/patterns.py` - LifeLabs patterns
19. `examples/django_integration.py` - Django example
20. `examples/fastapi_integration.py` - FastAPI example
21. `tests/test_models.py` - Model tests
22. `tests/test_parsers.py` - Parser tests
23. `setup.py` - Package setup
24. `pyproject.toml` - Modern Python packaging

### Files to Update:
1. `requirements.txt` - Add pydantic, sqlalchemy, psycopg2-binary
2. `CLAUDE.md` - Document new architecture
3. `.gitignore` - Ignore test databases, __pycache__

### Files to Deprecate (keep for reference):
1. `scrape_bloodwork_advanced.py` - Will be replaced by modular parser
2. `scrape_bloodwork_pdf.py` - Fallback logic integrated into new parser
3. `visualize_bloodwork.py` - Replaced by VisualizationService
4. `visualize_bloodwork.html` - Frontend will consume JSON from service

## Key Design Decisions

### 1. Framework-Agnostic Design
- Package exports clean Python classes and functions
- No web framework dependencies in core package
- Parent application provides: authentication, routing, file upload handling
- Package provides: parsing, storage, analysis, data serialization

### 2. Multi-User Without Built-in Auth
- `patient_id` parameter required for all operations
- Parent app responsible for authentication and mapping user → patient_id
- No user management, roles, permissions in this package
- Repository layer supports multi-tenancy via patient_id filtering

### 3. Database-First Approach
- PostgreSQL/MySQL as primary storage
- CSV export available as utility function
- Migration tools for existing CSV data
- Proper indexing for performance

### 4. LifeLabs Focus (Extensible Design)
- Implement LifeLabsParser fully
- Design AbstractBloodWorkParser for future formats
- Configuration-driven patterns (easy to add new lab formats later)
- Document how to add new parsers

### 5. Separation of Concerns
- **Parsers**: Extract data from PDFs → return models
- **Repositories**: Store/retrieve data from database
- **Services**: Business logic, orchestration
- **Models**: Data validation, serialization
- **Config**: All hardcoded values externalized

### 6. JSON Output for Visualization
- No matplotlib in package
- Services return JSON-serializable data structures
- Frontend (React, Vue, etc.) handles actual chart rendering
- Flexibility: client chooses chart library (Chart.js, D3, Plotly)

## Success Criteria

✅ **Functional Requirements:**
1. User can upload PDF via web form
2. System extracts all test results and stores in database
3. System identifies patient info and links to patient_id
4. System returns list of abnormal (out-of-range) tests
5. System generates trend data for visualization
6. Multiple patients can use system concurrently

✅ **Non-Functional Requirements:**
1. Package can be imported into Django, Flask, FastAPI
2. No hardcoded file paths or patient names
3. All configuration via environment variables or config objects
4. Comprehensive test coverage (>80%)
5. Clear API documentation with examples
6. Type hints throughout codebase

✅ **Security Requirements:**
1. No PHI in logs or console output
2. File uploads validated (size, type)
3. Input sanitization (CSV injection prevention)
4. Database connections properly managed
5. Repository pattern prevents SQL injection

## Next Steps After Plan Approval

1. Create package structure and __init__.py files
2. Set up development environment (pytest, black, mypy)
3. Create Pydantic models (start with models/result.py)
4. Set up database schema with SQLAlchemy
5. Extract and refactor LifeLabsParser incrementally
6. Create service layer
7. Write integration examples
8. Add comprehensive tests

## Timeline Estimate

- **Week 1**: Foundation (models, database, parser refactoring)
- **Week 2**: Services, API, examples, testing
- **Week 3**: Documentation, refinement, production readiness

Total: **~3 weeks** for complete modular package with examples and tests.

## Questions to Resolve Before Implementation

1. ~~Do you have an existing database schema we should match?~~ → New schema is fine
2. Do you want CSV import utility to migrate existing data?
3. Should we include a CLI tool for testing (e.g., `bloodwork parse file.pdf --patient-id=123`)?
4. What level of logging do you need (INFO, DEBUG)?
5. Do you have sample PDFs from other patients we can test with (anonymized)?
