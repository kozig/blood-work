"""
Table extraction utilities for PDF parsing.

Handles extraction of structured data from PDF tables using pdfplumber.
"""
import re
from typing import List, Optional, Dict
from datetime import date
from bloodwork.models import BloodTestResult, ReferenceRange, ResultFlag


class TableExtractor:
    """Extract blood test results from PDF tables."""

    def __init__(self, patient_id: str):
        """
        Initialize table extractor.

        Args:
            patient_id: Patient identifier for results
        """
        self.patient_id = patient_id

    def extract_from_tables(
        self,
        tables: List[List[List[Optional[str]]]],
        current_date: Optional[date]
    ) -> List[BloodTestResult]:
        """
        Extract test results from PDF tables.

        Args:
            tables: List of tables from pdfplumber (each table is a list of rows)
            current_date: Date for these results

        Returns:
            List of extracted BloodTestResult objects
        """
        if not tables or not current_date:
            return []

        results = []

        for table in tables:
            if not table or len(table) < 2:
                continue

            # Find header row and column indices
            header_info = self._find_header_row(table)
            if not header_info:
                continue

            header_row_idx, column_indices = header_info

            # Parse data rows
            for row in table[header_row_idx + 1:]:
                result = self._parse_table_row(row, column_indices, current_date)
                if result:
                    results.append(result)

        return results

    def _find_header_row(
        self,
        table: List[List[Optional[str]]]
    ) -> Optional[tuple[int, Dict[str, int]]]:
        """
        Find the header row and determine column indices.

        Args:
            table: Table data from pdfplumber

        Returns:
            Tuple of (header_row_index, column_indices_dict) or None if not found
        """
        # Check first 3 rows for header
        for i, row in enumerate(table[:3]):
            if not row:
                continue

            row_str = ' '.join([str(cell) if cell else '' for cell in row]).lower()

            # Check if this looks like a header row
            if 'test' in row_str and 'result' in row_str:
                headers = [str(cell).strip().lower() if cell else '' for cell in row]

                # Find column indices
                column_indices = {}
                for col_idx, header in enumerate(headers):
                    if 'test' in header and 'test' not in column_indices:
                        column_indices['test'] = col_idx
                    elif 'flag' in header:
                        column_indices['flag'] = col_idx
                    elif 'result' in header:
                        column_indices['result'] = col_idx
                    elif 'reference' in header or 'range' in header:
                        column_indices['range'] = col_idx
                    elif 'unit' in header:
                        column_indices['units'] = col_idx

                # Must have at least test and result columns
                if 'test' in column_indices and 'result' in column_indices:
                    return (i, column_indices)

        return None

    def _parse_table_row(
        self,
        row: List[Optional[str]],
        column_indices: Dict[str, int],
        current_date: date
    ) -> Optional[BloodTestResult]:
        """
        Parse a single table row into a BloodTestResult.

        Args:
            row: Table row data
            column_indices: Dictionary mapping column names to indices
            current_date: Date for this result

        Returns:
            BloodTestResult if successfully parsed, None otherwise
        """
        if not row or len(row) < 3:
            return None

        try:
            # Extract values from row
            test_name = self._get_cell_value(row, column_indices.get('test'))
            result_raw = self._get_cell_value(row, column_indices.get('result'))
            flag_str = self._get_cell_value(row, column_indices.get('flag', -1))
            range_str = self._get_cell_value(row, column_indices.get('range', -1))
            units = self._get_cell_value(row, column_indices.get('units', -1))

            # Validate test name and result
            if not test_name or test_name == 'None' or len(test_name) < 3:
                return None

            if not result_raw or result_raw == 'None':
                return None

            # Skip if result doesn't contain a digit
            if not re.search(r'\d', result_raw):
                return None

            # Clean up values
            test_name = re.sub(r'\s+', ' ', test_name)
            result_raw_clean = result_raw.replace(' ', '')

            # Parse numeric result
            try:
                result_value = float(result_raw_clean.replace(',', ''))
            except ValueError:
                # Try extracting first number from string
                match = re.search(r'([\d\.]+)', result_raw_clean)
                if match:
                    result_value = float(match.group(1))
                else:
                    return None

            # Parse reference range
            reference_range = ReferenceRange.parse(range_str or "")

            # Parse flag
            flag = ResultFlag.from_lifelabs(flag_str or "").value

            # Create BloodTestResult
            return BloodTestResult(
                patient_id=self.patient_id,
                test_date=current_date,
                test_name=test_name,
                result_value=result_value,
                result_raw=result_raw,
                reference_range=reference_range,
                units=units or "",
                flag=flag
            )

        except (IndexError, AttributeError, ValueError) as e:
            # Skip rows that can't be parsed
            return None

    @staticmethod
    def _get_cell_value(row: List[Optional[str]], index: Optional[int]) -> str:
        """
        Safely get cell value from row.

        Args:
            row: Table row
            index: Column index

        Returns:
            Cell value as string, or empty string if not available
        """
        if index is None or index < 0 or index >= len(row):
            return ""

        cell = row[index]
        if cell is None or str(cell).strip() in ['None', 'null', '']:
            return ""

        return str(cell).strip()
