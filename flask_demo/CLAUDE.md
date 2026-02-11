# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask web application for uploading, parsing, and visualizing LifeLabs blood work PDF reports. Built on the `bloodwork` Python package (in `bloodwork/` subdirectory) which provides the core parsing, storage, and analysis logic as a framework-agnostic library.

## Commands

```bash
# Install (bloodwork package from parent dir + Flask dependencies)
pip install -e .. && pip install -r requirements.txt

# Run dev server (http://localhost:5000)
python app.py

# Production server
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Reset database
rm bloodwork_demo.db && python app.py
```

## Architecture

### Layered Design

The `bloodwork/` package follows a clean layered architecture. The Flask app (`app.py`) is a thin consumer of these layers:

**Models** (`bloodwork/models/`) — Pydantic models used throughout:
- `BloodTestResult` + `ReferenceRange`: Core data model. `ReferenceRange.parse()` handles formats like `"4.0 - 11.0"`, `"<6.0"`, `">=1.00"`. Flags are `"NORMAL"`, `"HIGH"`, `"LOW"` (not LifeLabs' `"HI"/"LO"`).
- `PatientInfo`: Demographics. `patient_id` is the foreign key from the parent app (in Flask demo, it's `session['user_id']` = `"demo-user"`).
- `TestCategory` enum: Auto-categorizes tests by name via keyword matching in `categorize_test()`.

**Parsers** (`bloodwork/parsers/`) — PDF extraction via `AbstractBloodWorkParser` interface:
- `LifeLabsParser`: Hybrid approach — tries table extraction first (`pdfplumber`), then falls back to text regex, deduplicates across both. New lab formats should subclass `AbstractBloodWorkParser`.
- Extractors (`parsers/extractors/`): Separated concerns — `DateExtractor`, `MetadataExtractor`, `TableExtractor`, `TextExtractor`.

**Repositories** (`bloodwork/repositories/`) — Storage via `AbstractRepository` interface:
- `DatabaseRepository`: SQLAlchemy implementation. ORM models in `models.py` (`PatientInfoORM`, `BloodTestResultORM`). Tables auto-created on init. Deduplicates on `(test_date, test_name, result_value)` during `save_results()`. Patient delete cascades to results.

**Services** (`bloodwork/services/`) — Business logic orchestration:
- `ParserService`: Ties parsing to storage. `parse_and_store(file, patient_id)` is the main entry point. Factory method `get_parser()` selects parser by type string.
- `AnalysisService`: Trend analysis, abnormal detection, grouping by category.
- `VisualizationService`: Generates Chart.js-compatible JSON. Does NOT render charts — that's frontend.

### Flask App (`app.py`)

Thin routing layer. Uses a singleton `DatabaseRepository` (lazy-initialized via `get_repository()`). Session-based demo auth (`"demo-user"`). Routes serve both HTML templates and JSON API endpoints (`/api/results`, `/api/visualize/<test_name>`). `POST /reset` deletes all data for current user.

### Data Flow

```
PDF upload → ParserService.validate_pdf_file() → LifeLabsParser.parse()
  → (table extraction + text extraction + dedup)
  → DatabaseRepository.save_results() (with DB-level dedup)
  → ParseResult summary returned to Flask route
```

## Configuration

- `BLOODWORK_DATABASE_URL` env var (default: `sqlite:///./bloodwork_demo.db` in Flask app, PostgreSQL in package defaults)
- `SECRET_KEY` env var for Flask sessions
- All `bloodwork` package config in `bloodwork/config/defaults.py`, overridable via `BLOODWORK_*` env vars

## Key Patterns

- Regex patterns for LifeLabs parsing live in `bloodwork/config/patterns.py` — modify these when report format changes
- `ResultFlag.from_lifelabs()` converts LifeLabs `"HI"/"LO"` to internal `"HIGH"/"LOW"`
- Reference range parsing handles edge cases (negative numbers may conflict with dash-separated ranges)
- ORM ↔ Pydantic conversion happens in `DatabaseRepository._orm_to_model()`
