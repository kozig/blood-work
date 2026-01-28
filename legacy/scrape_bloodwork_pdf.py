#!/usr/bin/env python3
"""
Blood Work PDF Scraper for LifeLabs Reports
Extracts test results from LifeLabs PDF reports and exports to CSV
"""

import re
import csv
from datetime import datetime
import sys

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed")
    print("Install with: pip3 install pdfplumber --user")
    sys.exit(1)


class BloodWorkParser:
    """Parser for LifeLabs blood work PDF reports"""

    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.results = []
        self.current_date = None
        self.patient_info = {}

    def parse_pdf(self):
        """Extract all blood work data from PDF"""
        print(f"📄 Opening PDF: {self.pdf_path}")

        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"📊 Found {len(pdf.pages)} pages")

            for page_num, page in enumerate(pdf.pages, 1):
                print(f"   Processing page {page_num}...")
                self._parse_page(page)

        print(f"✓ Extracted {len(self.results)} test results")
        return self.results

    def _parse_page(self, page):
        """Parse a single page of the PDF"""
        text = page.extract_text()

        if not text:
            return

        lines = text.split('\n')

        # Extract date of service
        date_match = re.search(r'Date of Service[:\s]*([\w\s,]+\d{4}\s+\d{2}:\d{2})', text)
        if date_match:
            date_str = date_match.group(1).strip()
            self.current_date = self._parse_date(date_str)

        # Extract patient info from first page
        if not self.patient_info:
            self._extract_patient_info(text)

        # Parse test results
        self._parse_test_results(lines)

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

    def _parse_date(self, date_str):
        """Parse date string to YYYY-MM-DD format"""
        try:
            # Handle formats like "Jun 10 2025 08:07" or "10-JUN-2025"
            date_str = re.sub(r'\s+\d{2}:\d{2}.*', '', date_str).strip()

            # Try different date formats
            formats = [
                '%b %d %Y',      # Jun 10 2025
                '%d-%b-%Y',      # 10-JUN-2025
                '%B %d %Y',      # June 10 2025
                '%d %B %Y',      # 10 June 2025
            ]

            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue

            return date_str  # Return as-is if parsing fails
        except:
            return date_str

    def _parse_test_results(self, lines):
        """Parse test results from text lines"""
        current_test = None
        current_result = None
        current_ref_range = None
        current_units = None
        current_flag = None

        # Patterns for test result lines
        # Looking for patterns like: "TestName    Result    RefRange    Units    Flag"
        test_patterns = [
            # Pattern: test name with numerical result
            r'^([A-Za-z\s\(\)/\-]+?)\s+([\d<>\.]+)\s+([\d\.<>= \-]+)\s+([a-zA-Z/%]+)\s*$',
            # Pattern with flag
            r'^([A-Za-z\s\(\)/\-]+?)\s+([A-Z]{2,3})\s+([\d<>\.]+)\s+([\d\.<>= \-]+)\s+([a-zA-Z/%]+)\s*$',
        ]

        for i, line in enumerate(lines):
            line = line.strip()

            if not line or line.startswith('Lab -') or line.startswith('FINAL'):
                continue

            # Skip header and footer lines
            if any(x in line for x in ['Test Flag Result Reference', 'Patient:', 'Date of Service',
                                       'IMPORTANT:', 'Page', 'Telephone:', 'Address:']):
                continue

            # Try to match common test patterns from the PDF structure
            # LifeLabs format: Test Name | Flag | Result | Reference Range | Units

            # Check if this looks like a test category header
            if line.isupper() or line.endswith(':'):
                continue

            # Parse structured table-like data
            # Example: "WBC 5.9 4.0 - 11.0 x E9/L"
            match = re.match(r'^([A-Za-z0-9\s\(\)/\-]+?)\s+([\d<>\.]+)\s+([\d\.<>= \-]+)\s+(.+)$', line)
            if match:
                test_name = match.group(1).strip()
                result = match.group(2).strip()
                ref_range = match.group(3).strip()
                units = match.group(4).strip()
                flag = ''

                # Skip if test name is too short (likely not a real test)
                if len(test_name) < 3:
                    continue

                # Skip common false matches
                skip_terms = ['Reported on', 'Collection', 'Lab No', 'Reference #']
                if any(term in test_name for term in skip_terms):
                    continue

                # Add to results
                if self.current_date:
                    self.results.append({
                        'date': self.current_date,
                        'test_name': test_name,
                        'result': result,
                        'reference_range': ref_range,
                        'units': units,
                        'flag': flag
                    })

            # Check for flagged results (HI/LO appear before result)
            match_flagged = re.match(r'^([A-Za-z0-9\s\(\)/\-]+?)\s+(HI|LO)\s+([\d<>\.]+)\s+([\d\.<>= \-]+)\s+(.+)$', line)
            if match_flagged:
                test_name = match_flagged.group(1).strip()
                flag = match_flagged.group(2).strip()
                result = match_flagged.group(3).strip()
                ref_range = match_flagged.group(4).strip()
                units = match_flagged.group(5).strip()

                if len(test_name) >= 3 and self.current_date:
                    self.results.append({
                        'date': self.current_date,
                        'test_name': test_name,
                        'result': result,
                        'reference_range': ref_range,
                        'units': units,
                        'flag': flag
                    })

    def export_to_csv(self, output_path='blood_work_extracted.csv'):
        """Export results to CSV file"""
        if not self.results:
            print("⚠️  No results to export")
            return

        print(f"💾 Exporting to: {output_path}")

        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date of Service', 'Test Name', 'Result', 'Reference Range', 'Units', 'Flag']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for result in self.results:
                writer.writerow({
                    'Date of Service': result['date'],
                    'Test Name': result['test_name'],
                    'Result': result['result'],
                    'Reference Range': result['reference_range'],
                    'Units': result['units'],
                    'Flag': result['flag']
                })

        print(f"✓ Successfully exported {len(self.results)} results")

        # Print summary
        self._print_summary()

    def _print_summary(self):
        """Print summary of extracted data"""
        if not self.results:
            return

        print("\n" + "="*60)
        print("EXTRACTION SUMMARY")
        print("="*60)

        if self.patient_info:
            print(f"Patient: {self.patient_info.get('name', 'Unknown')}")
            print(f"Age: {self.patient_info.get('age', 'Unknown')}")
            print(f"Gender: {self.patient_info.get('gender', 'Unknown')}")

        # Get unique dates
        dates = sorted(set(r['date'] for r in self.results))
        print(f"\nDate Range: {dates[0]} to {dates[-1]}")
        print(f"Number of Test Dates: {len(dates)}")
        print(f"Total Test Results: {len(self.results)}")

        # Count flagged results
        flagged = [r for r in self.results if r['flag']]
        if flagged:
            print(f"\n⚠️  Abnormal Results: {len(flagged)}")
            for result in flagged[:10]:  # Show first 10
                print(f"   • {result['test_name']}: {result['result']} ({result['flag']}) on {result['date']}")
            if len(flagged) > 10:
                print(f"   ... and {len(flagged) - 10} more")

        # Show unique test types
        test_types = sorted(set(r['test_name'] for r in self.results))
        print(f"\nUnique Tests: {len(test_types)}")

        print("="*60)


def main():
    """Main execution function"""
    print("="*60)
    print("🩸 Blood Work PDF Scraper")
    print("="*60)
    print()

    # Default PDF file
    pdf_file = 'Reports_librepdf.pdf'
    output_file = 'blood_work_extracted.csv'

    # Check for command line arguments
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    try:
        # Parse PDF
        parser = BloodWorkParser(pdf_file)
        parser.parse_pdf()

        # Export to CSV
        parser.export_to_csv(output_file)

        print("\n✅ SUCCESS! Your blood work data has been extracted.")
        print(f"📁 Output file: {output_file}")

    except FileNotFoundError:
        print(f"❌ ERROR: File '{pdf_file}' not found")
        print("Usage: python3 scrape_bloodwork_pdf.py [pdf_file] [output_csv]")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
