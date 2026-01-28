# Legacy Code (Proof of Concept)

This directory contains the original proof-of-concept code for blood work analysis. These files are kept for reference but should not be used in production.

## Files

- **scrape_bloodwork_advanced.py** - Original monolithic parser (LifeLabs)
- **scrape_bloodwork_pdf.py** - Original fallback parser
- **visualize_bloodwork.py** - Original matplotlib visualization script
- **visualize_bloodwork.html** - Original standalone HTML visualization
- **README.md** - Original project README
- **PDF_SCRAPER_README.md** - Original scraper documentation
- **SCRAPER_QUICK_START.txt** - Original quick start guide

## Migration to New Package

The functionality from these files has been refactored into the `bloodwork/` package with:

- Modular architecture (models, parsers, repositories, services)
- Type-safe Pydantic models
- Database storage with SQLAlchemy
- Framework-agnostic design
- Multi-user support

## Use the New Package Instead

```python
# OLD (legacy - don't use):
from scrape_bloodwork_advanced import LifeLabsParser
parser = LifeLabsParser('file.pdf')
results = parser.parse_pdf()
parser.export_to_csv('output.csv')

# NEW (use this):
from bloodwork import ParserService, DatabaseRepository
repository = DatabaseRepository("postgresql://localhost/bloodwork")
service = ParserService(repository)
with open('file.pdf', 'rb') as f:
    result = service.parse_and_store(f, patient_id='user123')
```

See the main project README for complete documentation.
