# 🩸 Blood Work PDF Scraper

Automated extraction of blood test results from LifeLabs PDF reports.

## 📋 What You Have

I've created **TWO** Python scripts to scrape your LifeLabs PDF:

1. **`scrape_bloodwork_pdf.py`** - Basic scraper
2. **`scrape_bloodwork_advanced.py`** - Advanced scraper with table extraction ⭐ **RECOMMENDED**

---

## 🚀 Quick Start

### Option 1: Auto-Install and Run (Easiest)

```bash
chmod +x setup_and_run.sh
./setup_and_run.sh
```

This will:
- ✅ Check Python installation
- ✅ Install required packages
- ✅ Run the advanced scraper
- ✅ Generate CSV output

---

### Option 2: Manual Installation

#### Step 1: Install pdfplumber

Choose ONE of these methods:

**Method A: Using apt-get (Ubuntu/Debian)** ⭐ Recommended for WSL
```bash
sudo apt update
sudo apt install python3-pip -y
pip3 install pdfplumber --user
```

**Method B: Download pip installer**
```bash
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
pip3 install pdfplumber --user
```

**Method C: System package manager**
```bash
sudo apt install python3-pdfplumber -y
```

#### Step 2: Run the Scraper

```bash
python3 scrape_bloodwork_advanced.py
```

Or specify custom files:
```bash
python3 scrape_bloodwork_advanced.py input.pdf output.csv
```

---

## 📊 What the Script Does

### Input
- **`Reports_librepdf.pdf`** - Your LifeLabs blood work PDF

### Output
- **`blood_work_extracted.csv`** - Structured data with columns:
  - Date of Service
  - Test Name
  - Result
  - Reference Range
  - Units
  - Flag (HI/LO for abnormal values)

### Features
- ✅ Extracts patient information
- ✅ Parses all test dates from PDF
- ✅ Identifies abnormal results (flagged as HI/LO)
- ✅ Handles multiple pages
- ✅ Removes duplicate entries
- ✅ Generates summary report

---

## 📁 File Descriptions

### Scripts

| File | Description | When to Use |
|------|-------------|-------------|
| `scrape_bloodwork_advanced.py` | Advanced table extraction | **Use this first** ⭐ |
| `scrape_bloodwork_pdf.py` | Basic text parsing | Fallback if advanced fails |
| `setup_and_run.sh` | Automated setup | First-time setup |

### Data Files

| File | Description |
|------|-------------|
| `Reports_librepdf.pdf` | Original LifeLabs PDF report |
| `blood_work_results.csv` | **Already extracted** - your current data |
| `blood_work_extracted.csv` | Output from scraper (will be created) |

---

## 🔧 Troubleshooting

### Problem: "No module named pdfplumber"

**Solution 1:** Install using apt
```bash
sudo apt update
sudo apt install python3-pip
pip3 install pdfplumber --user
```

**Solution 2:** Install pip first
```bash
sudo apt install python3-pip -y
```

### Problem: "pip: command not found"

**Solution:** Install pip
```bash
sudo apt update
sudo apt install python3-pip -y
```

Or download pip installer:
```bash
wget https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
export PATH=$PATH:~/.local/bin
```

### Problem: "Permission denied"

**Solution:** Make scripts executable
```bash
chmod +x scrape_bloodwork_advanced.py
chmod +x setup_and_run.sh
```

### Problem: No data extracted

**Possible causes:**
1. PDF format not recognized
2. File path incorrect
3. PDF is encrypted/protected

**Solution:**
```bash
# Check if PDF exists
ls -lh Reports_librepdf.pdf

# Try both scrapers
python3 scrape_bloodwork_advanced.py
python3 scrape_bloodwork_pdf.py
```

---

## 📖 Usage Examples

### Basic Usage
```bash
# Use default files (Reports_librepdf.pdf → blood_work_extracted.csv)
python3 scrape_bloodwork_advanced.py
```

### Custom Input/Output
```bash
# Specify custom PDF and output CSV
python3 scrape_bloodwork_advanced.py my_report.pdf my_results.csv
```

### Batch Processing
```bash
# Process multiple PDFs
for pdf in *.pdf; do
    output="${pdf%.pdf}.csv"
    python3 scrape_bloodwork_advanced.py "$pdf" "$output"
done
```

---

## 🎯 Expected Output

When you run the scraper successfully, you'll see:

```
======================================================================
🩸 ADVANCED BLOOD WORK PDF SCRAPER
   Optimized for LifeLabs Reports
======================================================================

📄 Opening PDF: Reports_librepdf.pdf
📊 Found 34 pages

   Page 1/34... extracted 15 results
   Page 2/34... extracted 12 results
   ...

✓ Total extracted: 241 test results

💾 Exporting to: blood_work_extracted.csv
   Removed 0 duplicate entries
✓ Successfully exported 241 unique results

======================================================================
EXTRACTION SUMMARY
======================================================================
Patient: KOZIOL, GREGORY
Date of Birth: Feb 13 1982
Age: 43 years
Gender: M

Date Range: 2021-12-09 to 2025-06-10
Number of Test Dates: 15
Total Test Results: 241

⚠️  ABNORMAL RESULTS: 23
----------------------------------------------------------------------
   2025-06-10 | Gamma Glutamyl Transferase        | 84       HI  | Normal: <65
   2024-11-15 | Vitamin B12                       | 183      LO  | Normal: >220
   ...
======================================================================

✅ SUCCESS! Blood work data extracted and saved.
📁 Output file: blood_work_extracted.csv
```

---

## 🔄 Workflow

### Complete Workflow

```
1. PDF Report (Reports_librepdf.pdf)
         ↓
2. Run Scraper (scrape_bloodwork_advanced.py)
         ↓
3. CSV Output (blood_work_extracted.csv)
         ↓
4. Visualize (visualize_bloodwork.html or .py)
         ↓
5. Analyze Trends
```

### After Extraction

Once you have the CSV, you can:

1. **Compare with existing data:**
```bash
diff blood_work_results.csv blood_work_extracted.csv
```

2. **Merge with existing data** (if you have new PDFs)

3. **Visualize the data:**
```bash
# Option 1: Open HTML (no installation needed)
wslview visualize_bloodwork.html

# Option 2: Generate charts with Python
python3 visualize_bloodwork.py
```

---

## 📚 Technical Details

### Dependencies

- **Python 3.7+** (✅ You have Python 3.12.3)
- **pdfplumber** - PDF parsing library
  - Uses `pdfminer.six` under the hood
  - Extracts tables and text from PDFs
  - Handles complex PDF structures

### How It Works

1. **PDF Loading**: Opens PDF with pdfplumber
2. **Page Iteration**: Processes each page sequentially
3. **Table Extraction**: Attempts to extract structured tables
4. **Text Parsing**: Falls back to regex pattern matching
5. **Data Validation**: Filters invalid/duplicate entries
6. **CSV Export**: Writes structured data to CSV

### Supported LifeLabs Formats

The scraper is optimized for:
- ✅ Standard LifeLabs blood work reports
- ✅ Multi-page reports
- ✅ Reports with date stamps on each page
- ✅ Flagged results (HI/LO indicators)
- ✅ Various test categories (Hematology, Chemistry, Hormones, etc.)

---

## 🆘 Need Help?

### Check Installation
```bash
# Check Python version
python3 --version

# Check if pdfplumber is installed
python3 -c "import pdfplumber; print('✓ pdfplumber installed')"

# List installed packages
pip3 list | grep pdf
```

### Test the Script
```bash
# Run with verbose error messages
python3 scrape_bloodwork_advanced.py 2>&1 | tee scraper_log.txt
```

### Alternative: Use the Already Extracted Data

Remember: **You already have `blood_work_results.csv`** which I manually extracted!

The scraper is for:
- ✅ Processing NEW lab reports
- ✅ Automating future extractions
- ✅ Verifying/cross-checking the manual extraction

---

## 💡 Tips

1. **Start with the advanced scraper** - it's more accurate
2. **Check the summary output** - confirms what was extracted
3. **Compare with manual extraction** - ensures accuracy
4. **Use for future reports** - automate your next lab results

---

## 🎓 Learning Resources

If you want to understand how PDF scraping works:

- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)
- [PDF Structure Basics](https://www.adobe.com/devnet/pdf/pdf_reference.html)
- [Python CSV Module](https://docs.python.org/3/library/csv.html)

---

## ✅ Success Checklist

- [ ] pdfplumber installed
- [ ] Script runs without errors
- [ ] CSV file created
- [ ] Summary shows expected number of results
- [ ] Abnormal results flagged correctly
- [ ] Ready to visualize!

---

**Questions? The scripts have detailed error messages to guide you through any issues.**
