#!/usr/bin/env python3
"""
Advanced Blood Work PDF Scraper for LifeLabs Reports
Uses table extraction and pattern matching for better accuracy
"""

import re
import csv
from datetime import datetime
import sys

try:
    import pdfplumber
except ImportError:
    print("❌ ERROR: pdfplumber not installed")
    print("\nInstall with one of:")
    print("  pip3 install pdfplumber --user")
    print("  python3 -m pip install pdfplumber --user")
    print("  sudo apt install python3-pip && pip3 install pdfplumber --user")
    sys.exit(1)


class LifeLabsParser:
    """Advanced parser specifically for LifeLabs PDF format"""

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.results = []
        self.patient_info = {}

    def parse_pdf(self):
        """Extract blood work data using table extraction"""
        print(f"📄 Opening PDF: {self.pdf_path}")

        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"📊 Found {len(pdf.pages)} pages\n")

            for page_num, page in enumerate(pdf.pages, 1):
                print(f"   Page {page_num}/{len(pdf.pages)}...", end=' ')
                results_count = len(self.results)
                self._parse_page_advanced(page)
                new_results = len(self.results) - results_count
                print(f"extracted {new_results} results")

        print(f"\n✓ Total extracted: {len(self.results)} test results")
        return self.results

    def _parse_page_advanced(self, page):
        """Parse page using both table extraction and text patterns"""

        # Extract text for metadata
        text = page.extract_text()
        if not text:
            return

        # Get date and patient info
        current_date = self._extract_date(text)
        if not self.patient_info:
            self._extract_patient_info(text)

        # Try table extraction first (most reliable for structured data)
        tables = page.extract_tables()
        if tables:
            for table in tables:
                self._parse_table(table, current_date)

        # Fallback: parse text line by line
        self._parse_text_format(text, current_date)

    def _parse_table(self, table, current_date):
        """Parse extracted table data"""
        if not table or len(table) < 2:
            return

        # Find column indices
        header_row = None
        for i, row in enumerate(table[:3]):  # Check first 3 rows for header
            row_str = ' '.join([str(cell) if cell else '' for cell in row]).lower()
            if 'test' in row_str and 'result' in row_str:
                header_row = i
                break

        if header_row is None:
            return

        headers = [str(cell).strip() if cell else '' for cell in table[header_row]]

        # Find column indices
        test_col = flag_col = result_col = range_col = units_col = None

        for i, header in enumerate(headers):
            header_lower = header.lower()
            if 'test' in header_lower and test_col is None:
                test_col = i
            elif 'flag' in header_lower:
                flag_col = i
            elif 'result' in header_lower:
                result_col = i
            elif 'reference' in header_lower or 'range' in header_lower:
                range_col = i
            elif 'unit' in header_lower:
                units_col = i

        # Parse data rows
        for row in table[header_row + 1:]:
            if not row or len(row) < 3:
                continue

            try:
                test_name = str(row[test_col]).strip() if test_col is not None and len(row) > test_col and row[test_col] else None
                flag = str(row[flag_col]).strip() if flag_col is not None and len(row) > flag_col and row[flag_col] else ''
                result = str(row[result_col]).strip() if result_col is not None and len(row) > result_col and row[result_col] else None
                ref_range = str(row[range_col]).strip() if range_col is not None and len(row) > range_col and row[range_col] else ''
                units = str(row[units_col]).strip() if units_col is not None and len(row) > units_col and row[units_col] else ''

                # Validate test name and result
                if not test_name or test_name == 'None' or len(test_name) < 3:
                    continue
                if not result or result == 'None':
                    continue

                # Skip if result is not numeric (likely not a test result)
                if not re.search(r'\d', result):
                    continue

                # Clean up values
                test_name = re.sub(r'\s+', ' ', test_name)
                result = result.replace(' ', '')
                flag = flag.strip() if flag and flag not in ['None', 'null', ''] else ''

                if current_date:
                    self.results.append({
                        'date': current_date,
                        'test_name': test_name,
                        'result': result,
                        'reference_range': ref_range,
                        'units': units,
                        'flag': flag
                    })

            except (IndexError, AttributeError):
                continue

    def _parse_text_format(self, text, current_date):
        """Parse text format when table extraction doesn't work"""
        lines = text.split('\n')

        # Track if we're in a test results section
        in_results_section = False
        section_headers = ['Hematology', 'General Chemistry', 'Lipids', 'Thyroid Function',
                          'Biochemical Investigation', 'Differential', 'Urinalysis',
                          'Reproductive', 'Adrenal Function', 'Bone Markers', 'Immunology',
                          'Muscle Enzymes', 'Serum Proteins', 'Tumour Markers']

        for line in lines:
            line = line.strip()

            # Check if entering a results section
            if any(header in line for header in section_headers):
                in_results_section = True
                continue

            # Skip if not in results section
            if not in_results_section:
                continue

            # End of results section indicators
            if any(x in line for x in ['Lab -', 'FINAL RESULTS', 'IMPORTANT:', 'Page ']):
                in_results_section = False
                continue

            # Parse result line
            # Pattern: TestName [Flag] Result RefRange Units
            # Example: "WBC 5.9 4.0 - 11.0 x E9/L"
            # Example: "HDL Cholesterol LO 0.97 >=1.00 mmol/L"

            # Try pattern with flag
            match = re.match(r'^([A-Za-z0-9\s\(\)/\-\[\]]+?)\s+(HI|LO)\s+([\d<>\.]+)\s+([\d\.<>= \-]+)\s+([a-zA-Z0-9/%\s]+)$', line)
            if match:
                test_name = match.group(1).strip()
                flag = match.group(2).strip()
                result = match.group(3).strip()
                ref_range = match.group(4).strip()
                units = match.group(5).strip()

                if len(test_name) >= 3 and current_date:
                    # Check if not already added (avoid duplicates)
                    if not any(r['test_name'] == test_name and r['date'] == current_date for r in self.results):
                        self.results.append({
                            'date': current_date,
                            'test_name': test_name,
                            'result': result,
                            'reference_range': ref_range,
                            'units': units,
                            'flag': flag
                        })
                continue

            # Try pattern without flag
            match = re.match(r'^([A-Za-z0-9\s\(\)/\-\[\]]+?)\s+([\d<>\.]+)\s+([\d\.<>= \-]+)\s+([a-zA-Z0-9/%\s]+)$', line)
            if match:
                test_name = match.group(1).strip()
                result = match.group(2).strip()
                ref_range = match.group(3).strip()
                units = match.group(4).strip()
                flag = ''

                if len(test_name) >= 3 and current_date:
                    # Check if not already added
                    if not any(r['test_name'] == test_name and r['date'] == current_date for r in self.results):
                        self.results.append({
                            'date': current_date,
                            'test_name': test_name,
                            'result': result,
                            'reference_range': ref_range,
                            'units': units,
                            'flag': flag
                        })

    def _extract_date(self, text):
        """Extract date of service from text"""
        date_match = re.search(r'Date of Service[:\s]*([\w\s,]+\d{4}\s+\d{2}:\d{2})', text)
        if date_match:
            date_str = date_match.group(1).strip()
            return self._parse_date(date_str)
        return None

    def _extract_patient_info(self, text):
        """Extract patient information"""
        name_match = re.search(r'Patient:\s*([A-Z]+,\s*[A-Z]+)', text)
        if name_match:
            self.patient_info['name'] = name_match.group(1)

        age_match = re.search(r'Age:\s*(\d+)\s*years', text)
        if age_match:
            self.patient_info['age'] = age_match.group(1)

        gender_match = re.search(r'Gender:\s*([MF])', text)
        if gender_match:
            self.patient_info['gender'] = gender_match.group(1)

        dob_match = re.search(r'Date of Birth[:\s]*([\w\s,]+\d{4})', text)
        if dob_match:
            self.patient_info['dob'] = dob_match.group(1).strip()

    def _parse_date(self, date_str):
        """Parse date string to YYYY-MM-DD format"""
        try:
            date_str = re.sub(r'\s+\d{2}:\d{2}.*', '', date_str).strip()

            formats = [
                '%b %d %Y', '%d-%b-%Y', '%B %d %Y', '%d %B %Y',
                '%b-%d-%Y', '%d-%B-%Y', '%Y-%m-%d'
            ]

            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            return date_str
        except:
            return date_str

    def export_to_csv(self, output_path='blood_work_extracted.csv'):
        """Export results to CSV file"""
        if not self.results:
            print("⚠️  No results to export")
            return False

        print(f"\n💾 Exporting to: {output_path}")

        # Remove duplicates (same test, date, result)
        unique_results = []
        seen = set()
        for result in self.results:
            key = (result['date'], result['test_name'], result['result'])
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        print(f"   Removed {len(self.results) - len(unique_results)} duplicate entries")

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date of Service', 'Test Name', 'Result', 'Reference Range', 'Units', 'Flag']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in sorted(unique_results, key=lambda x: (x['date'], x['test_name'])):
                writer.writerow({
                    'Date of Service': result['date'],
                    'Test Name': result['test_name'],
                    'Result': result['result'],
                    'Reference Range': result['reference_range'],
                    'Units': result['units'],
                    'Flag': result['flag']
                })

        print(f"✓ Successfully exported {len(unique_results)} unique results\n")
        self._print_summary(unique_results)
        return True

    def _print_summary(self, results):
        """Print summary of extracted data"""
        print("="*70)
        print("EXTRACTION SUMMARY")
        print("="*70)

        if self.patient_info:
            if 'name' in self.patient_info:
                print(f"Patient: {self.patient_info['name']}")
            if 'dob' in self.patient_info:
                print(f"Date of Birth: {self.patient_info['dob']}")
            if 'age' in self.patient_info:
                print(f"Age: {self.patient_info['age']} years")
            if 'gender' in self.patient_info:
                print(f"Gender: {self.patient_info['gender']}")

        dates = sorted(set(r['date'] for r in results if r['date']))
        if dates:
            print(f"\nDate Range: {dates[0]} to {dates[-1]}")
            print(f"Number of Test Dates: {len(dates)}")

        print(f"Total Test Results: {len(results)}")

        # Count flagged results
        flagged = [r for r in results if r['flag']]
        if flagged:
            print(f"\n⚠️  ABNORMAL RESULTS: {len(flagged)}")
            print("-" * 70)
            for result in flagged[:15]:
                print(f"   {result['date']} | {result['test_name']:35s} | "
                      f"{result['result']:8s} {result['flag']:3s} | Normal: {result['reference_range']}")
            if len(flagged) > 15:
                print(f"   ... and {len(flagged) - 15} more abnormal results")

        # Show test categories
        test_types = sorted(set(r['test_name'] for r in results))
        print(f"\nUnique Test Types: {len(test_types)}")

        print("="*70)


def main():
    """Main execution function"""
    print("="*70)
    print("🩸 ADVANCED BLOOD WORK PDF SCRAPER")
    print("   Optimized for LifeLabs Reports")
    print("="*70)
    print()

    pdf_file = 'Reports_librepdf.pdf'
    output_file = 'blood_work_extracted.csv'

    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    try:
        parser = LifeLabsParser(pdf_file)
        parser.parse_pdf()
        success = parser.export_to_csv(output_file)

        if success:
            print("\n✅ SUCCESS! Blood work data extracted and saved.")
            print(f"📁 Output file: {output_file}")
            print(f"\nNext steps:")
            print(f"  • Open {output_file} in Excel/LibreOffice")
            print(f"  • Run: python3 visualize_bloodwork.py")
            print(f"  • Open: visualize_bloodwork.html in browser")
        else:
            print("\n⚠️  No data was extracted. Check if PDF format is supported.")

    except FileNotFoundError:
        print(f"❌ ERROR: File '{pdf_file}' not found")
        print(f"\nUsage: python3 {sys.argv[0]} [pdf_file] [output_csv]")
        print(f"Example: python3 {sys.argv[0]} Reports_librepdf.pdf results.csv")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
