# Blood Work Analysis Package

A framework-agnostic Python package for parsing, storing, and analyzing blood work reports from various laboratory formats.

## Features

- **PDF Parsing**: Extract structured data from laboratory PDF reports (currently supports LifeLabs)
- **Database Storage**: Store results in PostgreSQL or MySQL with SQLAlchemy
- **Data Models**: Type-safe Pydantic models with validation
- **Trend Analysis**: Analyze test results over time and detect abnormal values
- **Visualization Data**: Generate JSON data for client-side charting
- **Framework-Agnostic**: Works with Django, Flask, FastAPI, or any Python web framework
- **Multi-User Support**: Built-in support for multiple patients/users

## Installation

```bash
# Basic installation
pip install bloodwork

# With MySQL support
pip install bloodwork[mysql]

# Development installation
pip install bloodwork[dev]
```

Or install from source:

```bash
git clone https://github.com/yourusername/bloodwork.git
cd bloodwork
pip install -e .
```

## Quick Start

```python
from bloodwork import ParserService, DatabaseRepository

# Initialize database repository
repository = DatabaseRepository("postgresql://user:pass@localhost/bloodwork")

# Parse PDF and store results
service = ParserService(repository)

with open("report.pdf", "rb") as f:
    result = service.parse_and_store(f, patient_id="user123")

print(f"Parsed {result.num_results} test results")
print(f"Found {result.num_abnormal} abnormal results: {result.abnormal_tests}")
```

## Architecture

The package is organized into modular layers:

```
bloodwork/
├── models/          # Pydantic data models
├── parsers/         # PDF parsing (supports multiple lab formats)
├── repositories/    # Database storage layer (SQLAlchemy)
├── services/        # Business logic (parsing, analysis, visualization)
└── config/          # Configuration and patterns
```

### Key Components

**Models**: Type-safe data structures
- `BloodTestResult`: Individual test result with validation
- `PatientInfo`: Patient demographic information
- `ReferenceRange`: Normal range for tests
- Enums for flags and categories

**Repositories**: Storage abstraction
- `AbstractRepository`: Interface for storage backends
- `DatabaseRepository`: PostgreSQL/MySQL implementation
- Easy to add other backends (MongoDB, API, etc.)

**Services**: High-level business logic
- `ParserService`: Orchestrate PDF parsing and storage
- `AnalysisService`: Trend analysis and abnormal detection
- `VisualizationService`: Generate chart-ready JSON data

**Parsers**: Lab-specific extraction
- `LifeLabsParser`: LifeLabs PDF format (hybrid table + text)
- Extensible for other lab formats (Quest, Mayo, etc.)

## Usage Examples

### Parsing and Storage

```python
from bloodwork import ParserService, DatabaseRepository
from io import BytesIO

# Initialize
repository = DatabaseRepository("postgresql://user:pass@localhost/bloodwork")
parser_service = ParserService(repository)

# Parse PDF (from file upload in web app)
pdf_bytes = request.files['pdf'].read()
pdf_file = BytesIO(pdf_bytes)

result = parser_service.parse_and_store(pdf_file, patient_id="user123")
```

### Retrieving Results

```python
from bloodwork import DatabaseRepository

repository = DatabaseRepository("postgresql://user:pass@localhost/bloodwork")

# Get all results for a patient
results = repository.get_results(patient_id="user123")

# Get results for specific date range
from datetime import date
results = repository.get_results(
    patient_id="user123",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)

# Get specific test history
cholesterol = repository.get_test_history("user123", "HDL Cholesterol")
```

### Analysis

```python
from bloodwork import AnalysisService, DatabaseRepository

repository = DatabaseRepository("postgresql://user:pass@localhost/bloodwork")
analysis = AnalysisService(repository)

# Get abnormal results
abnormal = analysis.get_abnormal_results("user123")

# Analyze trends for a specific test
trend = analysis.get_test_trend("user123", "HDL Cholesterol")
print(f"Trend: {trend.trend}")  # "improving", "worsening", "stable"
print(f"Average: {trend.avg_value}")

# Get summary statistics
stats = analysis.get_summary_statistics("user123")
print(f"Total tests: {stats['total_results']}")
print(f"Abnormal: {stats['num_abnormal']}")
```

### Visualization

```python
from bloodwork import VisualizationService, DatabaseRepository

repository = DatabaseRepository("postgresql://user:pass@localhost/bloodwork")
viz = VisualizationService(repository)

# Get chart data for a specific test
chart_data = viz.generate_chart_data("user123", "HDL Cholesterol")
# Returns JSON with data_points, reference_range, trend, etc.

# Get dashboard summary
dashboard = viz.generate_summary_dashboard("user123")
# Returns statistics, abnormal_tests, recent_tests

# Export in Chart.js format
chartjs_data = viz.export_to_chartjs_format("user123", "HDL Cholesterol")
```

## Web Framework Integration

### Django

```python
# views.py
from django.http import JsonResponse
from django.views import View
from bloodwork import ParserService, DatabaseRepository

class BloodWorkUploadView(View):
    def post(self, request):
        pdf_file = request.FILES['pdf']
        patient_id = str(request.user.id)

        repository = DatabaseRepository(settings.DATABASE_URL)
        service = ParserService(repository)
        result = service.parse_and_store(pdf_file, patient_id)

        return JsonResponse({
            'success': True,
            'num_results': result.num_results,
            'num_abnormal': result.num_abnormal
        })
```

See [examples/django_integration.py](examples/django_integration.py) for complete example.

### FastAPI

```python
from fastapi import FastAPI, UploadFile, Depends
from bloodwork import ParserService, DatabaseRepository

app = FastAPI()

def get_repository():
    return DatabaseRepository("postgresql://user:pass@localhost/bloodwork")

@app.post("/bloodwork/upload")
async def upload(file: UploadFile, repo: DatabaseRepository = Depends(get_repository)):
    service = ParserService(repo)
    result = service.parse_and_store(file.file, patient_id="user123")
    return {"success": True, "num_results": result.num_results}
```

See [examples/fastapi_integration.py](examples/fastapi_integration.py) for complete example.

### Flask

```python
from flask import Flask, request, jsonify
from bloodwork import ParserService, DatabaseRepository

app = Flask(__name__)
repository = DatabaseRepository("postgresql://user:pass@localhost/bloodwork")

@app.route('/bloodwork/upload', methods=['POST'])
def upload():
    pdf_file = request.files['pdf']
    service = ParserService(repository)
    result = service.parse_and_store(pdf_file, patient_id="user123")
    return jsonify(success=True, num_results=result.num_results)
```

## Database Setup

### PostgreSQL

```bash
# Create database
createdb bloodwork

# Initialize tables (automatic on first use)
```

```python
from bloodwork.repositories import DatabaseRepository, create_tables
from sqlalchemy import create_engine

engine = create_engine("postgresql://user:pass@localhost/bloodwork")
create_tables(engine)
```

### MySQL

```bash
# Create database
mysql -u root -p -e "CREATE DATABASE bloodwork;"
```

```python
repository = DatabaseRepository("mysql+pymysql://user:pass@localhost/bloodwork")
```

## Configuration

Configuration via environment variables:

```bash
# Database
export BLOODWORK_DATABASE_URL="postgresql://user:pass@localhost/bloodwork"

# Parser settings
export BLOODWORK_MAX_PDF_SIZE_MB="50"

# Logging
export BLOODWORK_LOG_LEVEL="INFO"

# Privacy
export BLOODWORK_REDACT_PHI="true"
```

Or programmatically:

```python
from bloodwork.config import Config

config = Config()
config.MAX_PDF_SIZE_MB = 100
config.LOG_LEVEL = "DEBUG"
```

## Supported Lab Formats

Currently supported:
- **LifeLabs** (Canada)

Coming soon:
- Quest Diagnostics (USA)
- LabCorp (USA)
- Mayo Clinic Laboratories (USA)

### Adding New Lab Formats

Create a new parser by extending `AbstractBloodWorkParser`:

```python
from bloodwork.parsers import AbstractBloodWorkParser

class QuestParser(AbstractBloodWorkParser):
    def parse(self):
        # Implement Quest-specific parsing logic
        pass
```

## Development

```bash
# Clone repository
git clone https://github.com/yourusername/bloodwork.git
cd bloodwork

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Format code
black bloodwork/

# Type checking
mypy bloodwork/
```

## Security Considerations

This package handles Protected Health Information (PHI). Important security measures:

1. **No PHI in logs**: Set `BLOODWORK_REDACT_PHI=true`
2. **Database encryption**: Use encrypted connections
3. **File permissions**: Restrict access to uploaded PDFs
4. **Authentication**: Always authenticate users in your application layer
5. **Input validation**: PDF files are validated before parsing

See security documentation for more details.

## License

MIT License - see LICENSE file

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## Support

- Issues: https://github.com/yourusername/bloodwork/issues
- Documentation: https://bloodwork.readthedocs.io
- Email: support@example.com

## Changelog

### 0.1.0 (2024-01-12)
- Initial release
- LifeLabs parser support
- PostgreSQL/MySQL storage
- Django and FastAPI examples
- Trend analysis and visualization data generation
