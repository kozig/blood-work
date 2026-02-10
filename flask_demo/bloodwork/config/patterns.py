"""
LifeLabs-specific parsing patterns and configurations.

This module contains regex patterns, section headers, and other
lab-specific configurations for parsing LifeLabs PDF reports.
"""
import re
from typing import List, Dict

# LifeLabs test result section headers
LIFELABS_SECTIONS: List[str] = [
    "Hematology",
    "General Chemistry",
    "Lipids",
    "Thyroid Function",
    "Biochemical Investigation",
    "Differential",
    "Urinalysis",
    "Reproductive",
    "Adrenal Function",
    "Bone Markers",
    "Immunology",
    "Muscle Enzymes",
    "Serum Proteins",
    "Tumour Markers",
]

# Date format patterns for parsing
DATE_PATTERNS: List[str] = [
    r'Date of Service[:\s]*([\w\s,]+\d{4}\s+\d{2}:\d{2})',
    r'Collection Date[:\s]*([\w\s,]+\d{4})',
    r'Collected[:\s]*([\w\s,]+\d{4})',
]

# Date string formats to try when parsing
DATE_FORMATS: List[str] = [
    '%b %d %Y',      # Jun 10 2025
    '%d-%b-%Y',      # 10-JUN-2025
    '%B %d %Y',      # June 10 2025
    '%d %B %Y',      # 10 June 2025
    '%b-%d-%Y',      # Jun-10-2025
    '%d-%B-%Y',      # 10-June-2025
    '%Y-%m-%d',      # 2025-06-10
    '%m/%d/%Y',      # 06/10/2025
    '%d/%m/%Y',      # 10/06/2025
]

# Patient information field patterns
PATIENT_FIELD_PATTERNS: Dict[str, str] = {
    'name': r'Patient:\s*([A-Z]+,\s*[A-Z]+)',
    'age': r'Age:\s*(\d+)\s*years?',
    'gender': r'Gender:\s*([MFO])',
    'dob': r'Date of Birth[:\s]*([\w\s,]+\d{4})',
    'dob_alt': r'DOB[:\s]*([\w\s,]+\d{4})',
}

# Compiled regex patterns for test result parsing

# Pattern for test result with flag (HI/LO)
# Example: "HDL Cholesterol LO 0.97 >=1.00 mmol/L"
TEST_PATTERN_WITH_FLAG = re.compile(
    r'^'                                    # Start of line
    r'([A-Za-z0-9\s\(\)/\-\[\]]+?)'        # Test name (non-greedy)
    r'\s+'                                  # Whitespace separator
    r'(HI|LO)'                              # Flag indicator
    r'\s+'                                  # Whitespace
    r'([\d<>\.]+)'                          # Result value
    r'\s+'                                  # Whitespace
    r'([\d\.<>= \-]+)'                      # Reference range
    r'\s+'                                  # Whitespace
    r'([a-zA-Z0-9/%\s\*\^]+)'              # Units
    r'$',                                   # End of line
    re.VERBOSE
)

# Pattern for test result without flag
# Example: "WBC 5.9 4.0 - 11.0 x E9/L"
TEST_PATTERN_NO_FLAG = re.compile(
    r'^'                                    # Start of line
    r'([A-Za-z0-9\s\(\)/\-\[\]]+?)'        # Test name (non-greedy)
    r'\s+'                                  # Whitespace separator
    r'([\d<>\.]+)'                          # Result value
    r'\s+'                                  # Whitespace
    r'([\d\.<>= \-]+)'                      # Reference range
    r'\s+'                                  # Whitespace
    r'([a-zA-Z0-9/%\s\*\^]+)'              # Units
    r'$',                                   # End of line
    re.VERBOSE
)

# Lines to skip during parsing
SKIP_LINE_PATTERNS: List[str] = [
    r'^Lab -',
    r'^FINAL',
    r'IMPORTANT:',
    r'^Page ',
    r'Test Flag Result Reference',
    r'Patient:',
    r'Date of Service',
    r'Telephone:',
    r'Address:',
    r'Reported on',
    r'Collection',
    r'Lab No',
    r'Reference #',
]

# Compile skip patterns
COMPILED_SKIP_PATTERNS = [re.compile(pattern) for pattern in SKIP_LINE_PATTERNS]

def should_skip_line(line: str) -> bool:
    """
    Check if a line should be skipped during parsing.

    Args:
        line: Text line to check

    Returns:
        True if line should be skipped, False otherwise
    """
    if not line or line.strip() == '':
        return True

    for pattern in COMPILED_SKIP_PATTERNS:
        if pattern.search(line):
            return True

    return False
