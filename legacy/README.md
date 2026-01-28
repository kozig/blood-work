# Blood Work Visualization

Your blood work data has been extracted and is ready to visualize!

## Quick Start - HTML Version (Easiest!)

**Open the visualization in your browser:**

```bash
# Option 1: Open with default browser (WSL)
wslview visualize_bloodwork.html

# Option 2: Navigate to the file in Windows Explorer
# The file is at: \\wsl$\Ubuntu\home\goob\blood-work\visualize_bloodwork.html
# Double-click to open in your browser
```

The HTML file contains:
- ✅ Interactive charts for all major blood markers
- ✅ Organized by category (Lipid Panel, Liver, Hormones, etc.)
- ✅ Reference ranges shown as shaded areas
- ✅ Abnormal values highlighted in red
- ✅ Trend lines showing changes over time
- ✅ Summary of all abnormal findings

---

## Alternative - Python Version (Requires Installation)

If you want to use the Python script for high-quality PDF/PNG outputs:

### 1. Install Required Packages

```bash
# For Ubuntu/Debian-based systems:
sudo apt update
sudo apt install python3-pandas python3-matplotlib -y

# Or using pip (if available):
pip3 install pandas matplotlib --user
```

### 2. Run the Script

```bash
python3 visualize_bloodwork.py
```

This will generate:
- `blood_work_trends.png` - High-resolution PNG image
- `blood_work_trends.pdf` - Publication-quality PDF

---

## Files in This Directory

- `blood_work_results.csv` - Your extracted blood work data
- `visualize_bloodwork.html` - Interactive web visualization (RECOMMENDED)
- `visualize_bloodwork.py` - Python visualization script
- `README.md` - This file
- `Reports_librepdf.pdf` - Original lab reports

---

## Key Findings Summary

Based on your blood work from 2021-2025:

### 🔴 Consistently Abnormal:
- **Gamma Glutamyl Transferase (GGT)**: Elevated (69-127 U/L, normal <65)
  - Liver enzyme - may indicate liver stress or alcohol use

- **HDL Cholesterol**: Low on Jun 2025 (0.97 mmol/L, should be ≥1.00)
  - "Good" cholesterol - consider dietary changes

### 🟡 Intermittently Abnormal:
- **Vitamin B12**: Borderline low on Nov 2024 (183 pmol/L)
- **Vitamin D**: Low on several occasions (below 75 nmol/L)
- **Free Testosterone**: Low on Dec 2021 (184 pmol/L)

### ✅ Positive Trends:
- Blood sugar/A1C: Consistently normal
- Kidney function (eGFR): Good
- Blood counts: Normal and stable
- Cholesterol (total): Generally well-controlled

---

## Recommendations

1. **Open the HTML file** to explore your trends interactively
2. **Discuss elevated GGT** with your doctor (consistently high)
3. **Consider vitamin D supplementation** (frequently low)
4. **Monitor cholesterol** - HDL could be higher

---

## Questions?

The visualization shows data from **15 test dates** spanning **December 2021 to June 2025**.

To update with new results:
1. Add new rows to `blood_work_results.csv`
2. Re-open the HTML file (it will auto-refresh)
