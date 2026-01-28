# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python-based blood work analysis toolkit for extracting and visualizing medical lab results from LifeLabs PDF reports. The project consists of three main components:

1. **PDF Scraping**: Extract structured data from LifeLabs PDF reports
2. **Data Processing**: Parse and clean blood test results into CSV format
3. **Visualization**: Generate interactive HTML and static charts showing trends over time

## Key Commands

### PDF Extraction

```bash
# First-time setup: Run automated setup script (creates venv + installs dependencies)
chmod +x setup_and_run.sh
./setup_and_run.sh

# For subsequent runs: Activate venv first
source venv/bin/activate

# Extract blood work data from PDF (recommended - advanced scraper)
python scrape_bloodwork_advanced.py [input.pdf] [output.csv]

# Default: reads Reports_librepdf.pdf, outputs to blood_work_extracted.csv
python scrape_bloodwork_advanced.py

# Fallback scraper (if advanced fails)
python scrape_bloodwork_pdf.py [input.pdf] [output.csv]
```

### Visualization

```bash
# Activate venv (if not already active)
source venv/bin/activate

# Generate charts from CSV data
python visualize_bloodwork.py

# Opens HTML visualization in browser (WSL)
wslview visualize_bloodwork.html

# Or navigate to file in Windows Explorer
# \\wsl$\Ubuntu\home\goob\blood-work\visualize_bloodwork.html
```

### Installation

```bash
# Recommended: Use the automated setup script (creates venv automatically)
chmod +x setup_and_run.sh
./setup_and_run.sh

# Manual setup with venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# To activate venv in future sessions
source venv/bin/activate

# To deactivate venv
deactivate
```

## Architecture

### PDF Scraping Architecture

Two scraping strategies with shared goals but different approaches:

**scrape_bloodwork_advanced.py** (Recommended):
- `LifeLabsParser` class: Main parser with table extraction and text fallback
- **Table extraction first**: Uses `pdfplumber`'s table detection for structured data
- **Text parsing fallback**: Regex patterns for unstructured sections
- **Hybrid approach**: Combines both methods for maximum accuracy
- Handles multi-page reports, deduplication, patient metadata extraction

**scrape_bloodwork_pdf.py** (Fallback):
- `BloodWorkParser` class: Simpler text-based parser
- **Text-only parsing**: Uses regex patterns on extracted text
- Better for reports where table extraction fails

Both scrapers:
- Extract patient info (name, age, gender, DOB) from first page
- Parse dates from "Date of Service" headers
- Identify test categories (Hematology, General Chemistry, Lipids, etc.)
- Flag abnormal results (HI/LO indicators)
- Output to CSV with columns: Date of Service, Test Name, Result, Reference Range, Units, Flag

### Data Flow

```
PDF Report (Reports_librepdf.pdf)
    ↓
LifeLabsParser/BloodWorkParser
    ↓ [pdfplumber extraction + regex parsing]
    ↓
CSV Export (blood_work_extracted.csv)
    ↓
visualize_bloodwork.py (pandas + matplotlib)
    ↓
Output: PNG/PDF charts + HTML interactive visualization
```

### Visualization Architecture

**visualize_bloodwork.py**:
- Reads CSV using pandas
- Generates 6x4 grid of subplots (24 test panels)
- Test categories:
  - Lipid Panel (Cholesterol, HDL, LDL, Triglycerides)
  - Liver Function (ALT, GGT, ALP, AST)
  - Complete Blood Count (WBC, RBC, Hemoglobin, Platelets)
  - Hormones (Testosterone, Free T, TSH, Vitamin D)
  - Metabolic Panel (Glucose, HbA1C, Creatinine, eGFR)
  - Inflammation & Other (CRP, Iron, B12, Transferrin Saturation)
- Reference range visualization: shaded areas or threshold lines
- Abnormal values highlighted in red with X markers
- Outputs: blood_work_trends.png (300 DPI) and blood_work_trends.pdf

**visualize_bloodwork.html**:
- Standalone interactive HTML with embedded JavaScript
- No external dependencies required
- Charts generated client-side using HTML5 Canvas or inline SVG
- Organized by test category with expandable sections
- Shows trend lines and abnormal findings summary

### Reference Range Parsing

`parse_range()` function handles multiple formats:
- Range: `"4.0 - 11.0"` → (4.0, 11.0)
- Upper limit: `"<6.0"` → (None, 6.0)
- Lower limit: `">220"` or `">=1.00"` → (220, None) or (1.0, None)

### Test Categories Recognized

The scrapers identify these LifeLabs section headers:
- Hematology
- General Chemistry
- Lipids
- Thyroid Function
- Biochemical Investigation
- Differential
- Urinalysis
- Reproductive
- Adrenal Function
- Bone Markers
- Immunology
- Muscle Enzymes
- Serum Proteins
- Tumour Markers

## Dependencies

- **pdfplumber (≥0.9.0)**: PDF text and table extraction
- **pandas (≥1.5.0)**: Data manipulation and CSV processing
- **matplotlib (≥3.5.0)**: Chart generation

Python 3.7+ required (project was developed with Python 3.12.3)

## File Structure

```
blood-work/
├── venv/                           # Python virtual environment (not in git)
├── scrape_bloodwork_advanced.py    # Advanced scraper (table + text)
├── scrape_bloodwork_pdf.py         # Fallback scraper (text only)
├── visualize_bloodwork.py          # Chart generator
├── visualize_bloodwork.html        # Interactive visualization
├── setup_and_run.sh                # Automated setup script
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git exclusions (venv, output files, PDFs)
├── README.md                       # User-facing documentation
├── PDF_SCRAPER_README.md           # Detailed scraper documentation
└── SCRAPER_QUICK_START.txt         # Quick reference guide
```

## Implementation Notes

### When Modifying Scrapers

1. **Test pattern matching**: LifeLabs format varies by test type; verify regex patterns against actual PDFs
2. **Deduplication logic**: The advanced scraper checks `(date, test_name, result)` tuples to avoid duplicates from table + text parsing
3. **Date parsing**: Supports multiple formats (see `_parse_date()` method)
4. **Patient privacy**: Ensure any logging or output doesn't expose PHI beyond necessary extraction

### When Modifying Visualizations

1. **Test name consistency**: Visualization expects exact test names as extracted by scrapers
2. **Date format**: CSV must use parseable date format (YYYY-MM-DD recommended)
3. **Missing data**: `plot_test()` gracefully handles missing or non-numeric data
4. **Layout**: 6x4 grid is hardcoded; adding tests requires modifying both `plots` list and `n_rows`

### Common Issues

- **No data extracted**: Check if PDF is encrypted or has unexpected format
- **Duplicate results**: Advanced scraper handles this automatically; basic scraper may need manual deduplication
- **Missing tests in visualization**: Add test name to `plots` list in visualize_bloodwork.py
- **Reference range not showing**: Verify CSV contains valid Reference Range values

## Virtual Environment

The project uses a Python virtual environment (`venv/`) to isolate dependencies:
- Created automatically by `setup_and_run.sh`
- Located in `venv/` directory (excluded from git)
- Must be activated before running scripts: `source venv/bin/activate`
- When active, use `python` command (not `python3`)
- Deactivate with: `deactivate`

## WSL-Specific Notes

- HTML file can be opened with `wslview` command or via Windows path `\\wsl$\Ubuntu\...`
- Python scripts should use `python` when venv is active, `python3` otherwise
- File paths in scripts use forward slashes (Linux convention)
