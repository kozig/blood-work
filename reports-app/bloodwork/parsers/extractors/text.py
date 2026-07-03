"""
Text extraction utilities for PDF parsing.

Handles extraction of test results from text using regex patterns
(fallback when table extraction doesn't work).
"""
import re
from typing import List, Optional, Set
from datetime import date
from bloodwork.models import BloodTestResult, ReferenceRange, ResultFlag
from bloodwork.config import (
    LIFELABS_SECTIONS,
    TEST_PATTERN_WITH_FLAG,
    TEST_PATTERN_NO_FLAG,
    should_skip_line
)


class TextExtractor:
    """Extract blood test results from unstructured text."""

    def __init__(self, patient_id: str):
        """
        Initialize text extractor.

        Args:
            patient_id: Patient identifier for results
        """
        self.patient_id = patient_id
        self.sections = LIFELABS_SECTIONS

    def extract_from_text(
        self,
        text: str,
        current_date: Optional[date],
        existing_results: Optional[Set[tuple]] = None
    ) -> List[BloodTestResult]:
        """
        Extract test results from text using regex patterns.

        Args:
            text: Text to parse
            current_date: Date for these results
            existing_results: Set of (date, test_name, result) tuples to avoid duplicates

        Returns:
            List of extracted BloodTestResult objects
        """
        if not text or not current_date:
            return []

        results = []
        existing_keys = existing_results or set()

        lines = text.split('\n')
        in_results_section = False

        for line in lines:
            line = line.strip()

            # Skip empty lines and known patterns
            if should_skip_line(line):
                continue

            # Check if entering a results section
            if any(section in line for section in self.sections):
                in_results_section = True
                continue

            # Skip if not in results section
            if not in_results_section:
                continue

            # End of results section indicators
            if any(x in line for x in ['Lab -', 'FINAL RESULTS', 'IMPORTANT:', 'Page ']):
                in_results_section = False
                continue

            # Try to parse result from line
            result = self._parse_result_line(line, current_date)

            if result:
                # Check for duplicates
                key = (result.test_date, result.test_name, result.result_raw)
                if key not in existing_keys:
                    results.append(result)
                    existing_keys.add(key)

        return results

    def _parse_result_line(
        self,
        line: str,
        current_date: date
    ) -> Optional[BloodTestResult]:
        """
        Parse a single line of text into a BloodTestResult.

        Args:
            line: Text line to parse
            current_date: Date for this result

        Returns:
            BloodTestResult if successfully parsed, None otherwise
        """
        # Try pattern with flag first
        match = TEST_PATTERN_WITH_FLAG.match(line)
        if match:
            test_name = match.group(1).strip()
            flag_str = match.group(2).strip()
            result_raw = match.group(3).strip()
            ref_range_str = match.group(4).strip()
            units = match.group(5).strip()

            if len(test_name) >= 3:
                return self._create_result(
                    test_name, result_raw, ref_range_str, units, flag_str, current_date
                )

        # Try pattern without flag
        match = TEST_PATTERN_NO_FLAG.match(line)
        if match:
            test_name = match.group(1).strip()
            result_raw = match.group(2).strip()
            ref_range_str = match.group(3).strip()
            units = match.group(4).strip()

            if len(test_name) >= 3:
                return self._create_result(
                    test_name, result_raw, ref_range_str, units, "", current_date
                )

        return None

    def _create_result(
        self,
        test_name: str,
        result_raw: str,
        ref_range_str: str,
        units: str,
        flag_str: str,
        current_date: date
    ) -> Optional[BloodTestResult]:
        """
        Create a BloodTestResult from parsed components.

        Args:
            test_name: Name of the test
            result_raw: Raw result string
            ref_range_str: Reference range string
            units: Units of measurement
            flag_str: Flag string (HI/LO or empty)
            current_date: Date for this result

        Returns:
            BloodTestResult if successfully created, None otherwise
        """
        try:
            # Parse numeric result
            result_value = float(result_raw.replace(',', ''))

            # Parse reference range
            reference_range = ReferenceRange.parse(ref_range_str)

            # Parse flag
            flag = ResultFlag.from_lifelabs(flag_str).value

            return BloodTestResult(
                patient_id=self.patient_id,
                test_date=current_date,
                test_name=test_name,
                result_value=result_value,
                result_raw=result_raw,
                reference_range=reference_range,
                units=units,
                flag=flag
            )

        except (ValueError, Exception):
            return None
