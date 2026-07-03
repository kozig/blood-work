# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A framework-agnostic Python package (`bloodwork`) for parsing, storing, and analyzing blood work PDF reports — currently supports LifeLabs format. The package exposes parsers, repositories, and services that can be embedded in any web framework. The deployed Flask app lives in `reports-app/` (self-contained — it vendors its own copy of `bloodwork/`), with Django/FastAPI integration examples in `examples/`.

> **Note**: the root-level scripts referenced in older docs (`scrape_bloodwork_advanced.py`, `visualize_bloodwork.py`) have been moved to `legacy/`. New work should target the `bloodwork` package, not the legacy scripts.

## Key Commands

```bash
# Install in editable mode with dev extras
pip install -e .[dev]

# Run tests (config in pyproject.toml — auto-generates coverage report)
pytest
pytest tests/test_parsers.py                       # single file
pytest tests/test_parsers.py::TestLifeLabsParser   # single class
pytest -k "parse_range"                            # by name pattern

# Lint / format / type-check
black bloodwork/
flake8 bloodwork/
mypy bloodwork/

# Run the Flask demo (separate sub-app — has its own README and CLAUDE.md)
cd reports-app && pip install -r requirements.txt && python app.py

# Regenerate synthetic test PDFs
python demo_reports/generate_demo_reports.py
```

`pyproject.toml` configures pytest with `--cov=bloodwork --cov-report=html --cov-report=term` and black with `line-length = 100`. Mypy is set to `disallow_untyped_defs = true` — new functions need type annotations.

## Architecture

### Layered package design

The `bloodwork/` package follows clean layering. Consumers (Flask app, Django/FastAPI examples) compose these layers; they don't bypass them.

- **`models/`** — Pydantic data models (`BloodTestResult`, `PatientInfo`, `ReferenceRange`) and enums (`ResultFlag`, `TestCategory`). `ReferenceRange.parse()` handles `"4.0 - 11.0"`, `"<6.0"`, `">=1.00"`. Internal flags are `NORMAL`/`HIGH`/`LOW` — `ResultFlag.from_lifelabs()` translates LifeLabs' `"HI"/"LO"`.
- **`parsers/`** — `AbstractBloodWorkParser` interface. `LifeLabsParser` uses a hybrid strategy: table extraction via `pdfplumber` first, regex fallback on text, then dedup on `(date, test_name, result)`. The actual extraction work is split across `parsers/extractors/{date,metadata,table,text}.py` — modify those when LifeLabs' format changes, not the parser itself.
- **`repositories/`** — `AbstractRepository` interface. `DatabaseRepository` is the SQLAlchemy implementation; ORM models in `repositories/models.py` (`PatientInfoORM`, `BloodTestResultORM`). Tables auto-create on init. `save_results()` deduplicates at the DB level too. Pydantic↔ORM conversion happens in `_orm_to_model()`.
- **`services/`** — Orchestration. `ParserService.parse_and_store(file, patient_id)` is the main entry point. `AnalysisService` produces trends and abnormal-result summaries. `VisualizationService` emits Chart.js-compatible JSON (it does not render anything — rendering is the frontend's job).
- **`config/`** — `defaults.py` holds env-var-overridable settings (`BLOODWORK_DATABASE_URL`, `BLOODWORK_MAX_PDF_SIZE_MB`, `BLOODWORK_LOG_LEVEL`, `BLOODWORK_REDACT_PHI`). `patterns.py` holds the regex patterns for LifeLabs parsing — touch this when report layouts change.

Top-level `bloodwork/__init__.py` re-exports the public API. Prefer importing from `bloodwork` directly (`from bloodwork import ParserService, DatabaseRepository`) rather than reaching into submodules.

### Data flow

```
PDF upload → ParserService.validate_pdf_file() → LifeLabsParser.parse()
  → extractors (table + text) → in-parser dedup
  → DatabaseRepository.save_results() (DB-level dedup on (date, test_name, result))
  → ParseResult summary returned to caller
```

### Extending to new lab formats

Subclass `AbstractBloodWorkParser` (see `parsers/base.py`). `ParserService.get_parser()` is a factory that selects by parser-type string — register new formats there.

## Repository layout (orientation, not exhaustive)

- `bloodwork/` — the package (importable as `bloodwork`)
- `reports-app/` — the deployed, **self-contained** Flask app. **Has its own CLAUDE.md** that goes deeper on the Flask-specific routing, session model, and SQLite default. Read it before editing files in that directory. It vendors its own copy of the package at `reports-app/bloodwork/` (a mirror of the root `bloodwork/`), so it deploys with just `pip install -r requirements.txt` — no editable install. Run `reports-app/sync-lib.sh` after changing the root library to update the vendored copy.
- `examples/` — Django and FastAPI integration snippets (illustrative, not runnable apps)
- `tests/` — pytest suite (`test_models.py`, `test_parsers.py`, `test_services.py`); `conftest.py` adds project root to `sys.path`
- `demo_reports/` — sample PDFs plus `generate_demo_reports.py` for synthesizing new ones
- `legacy/` — pre-refactor scripts kept for reference; do not extend
- `REFACTORING_PLAN.md` — historical context on the legacy → package migration

## Implementation notes

- **Reference-range parsing edge case**: dash-separated ranges can collide with negative numbers — be careful when extending `ReferenceRange.parse()`.
- **Deduplication is done twice** (in-parser and in-repository) on purpose: the parser dedups across its own table+text hybrid; the repo dedups across separate uploads of the same report.
- **PHI**: this package handles Protected Health Information. The `BLOODWORK_REDACT_PHI` config gates whether PHI appears in log output — leave it on (`true`) unless you have a specific reason to disable it for local debugging.
- **No charting code in the package**: visualization is JSON-only. The legacy `matplotlib`-based scripts in `legacy/` are the exception, and `pandas`/`matplotlib` in `requirements.txt` exist only to keep those runnable.
