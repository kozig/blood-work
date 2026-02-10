"""
LifeLabs PDF parser implementation.

Parses blood work reports from LifeLabs using hybrid table + text extraction.
"""
import logging
from typing import BinaryIO, Tuple, List, Set
from datetime import date

try:
    import pdfplumber
except ImportError:
    raise ImportError(
        "pdfplumber is required for PDF parsing. "
        "Install it with: pip install pdfplumber"
    )

from bloodwork.models import BloodTestResult, PatientInfo
from bloodwork.parsers.base import AbstractBloodWorkParser, ParserError
from bloodwork.parsers.extractors import (
    DateExtractor,
    MetadataExtractor,
    TableExtractor,
    TextExtractor
)

logger = logging.getLogger(__name__)


class LifeLabsParser(AbstractBloodWorkParser):
    """
    Parser for LifeLabs blood work PDF reports.

    Uses a hybrid approach:
    1. Table extraction for structured data
    2. Text pattern matching for unstructured data
    3. Automatic deduplication
    """

    def __init__(self, pdf_file: BinaryIO, patient_id: str):
        """
        Initialize LifeLabs parser.

        Args:
            pdf_file: File-like object containing PDF data
            patient_id: Patient identifier
        """
        super().__init__(pdf_file, patient_id)

        # Initialize extractors
        self.date_extractor = DateExtractor()
        self.metadata_extractor = MetadataExtractor()
        self.table_extractor = TableExtractor(patient_id)
        self.text_extractor = TextExtractor(patient_id)

        # Track patient info found
        self.patient_info_extracted = False

    def parse(self) -> Tuple[PatientInfo, List[BloodTestResult]]:
        """
        Parse LifeLabs PDF and extract blood work data.

        Returns:
            Tuple of (PatientInfo, List[BloodTestResult])

        Raises:
            ParserError: If PDF cannot be opened or parsed
        """
        try:
            with pdfplumber.open(self.pdf_file) as pdf:
                logger.info(f"Parsing PDF with {len(pdf.pages)} pages")

                all_results = []
                existing_keys: Set[Tuple] = set()

                for page_num, page in enumerate(pdf.pages, 1):
                    logger.debug(f"Processing page {page_num}/{len(pdf.pages)}")

                    # Parse this page
                    page_results = self._parse_page(page, existing_keys)
                    all_results.extend(page_results)

                    # Update existing keys
                    for result in page_results:
                        key = (result.test_date, result.test_name, result.result_raw)
                        existing_keys.add(key)

                logger.info(f"Extracted {len(all_results)} test results")

                # Deduplicate and validate
                all_results = self.deduplicate_results(all_results)
                all_results = self.validate_results(all_results)

                # Sort by date and test name
                all_results.sort(key=lambda x: (x.test_date, x.test_name))

                return (self.patient_info, all_results)

        except Exception as e:
            logger.error(f"Failed to parse PDF: {e}")
            raise ParserError(f"Failed to parse PDF: {e}")

    def _parse_page(
        self,
        page,
        existing_keys: Set[Tuple]
    ) -> List[BloodTestResult]:
        """
        Parse a single PDF page.

        Args:
            page: pdfplumber page object
            existing_keys: Set of existing (date, test_name, result) tuples

        Returns:
            List of BloodTestResult objects from this page
        """
        results = []

        # Extract text
        text = page.extract_text()
        if not text:
            return results

        # Extract date for this page
        current_date = self.date_extractor.extract_date(text)

        # Extract patient info if not already done
        if not self.patient_info_extracted:
            page_patient_info = self.metadata_extractor.extract_patient_info(
                text, self.patient_id
            )
            self.patient_info = page_patient_info
            self.patient_info_extracted = True

        if not current_date:
            logger.warning(f"Could not extract date from page")
            return results

        # Try table extraction first
        tables = page.extract_tables()
        if tables:
            table_results = self.table_extractor.extract_from_tables(
                tables, current_date
            )
            results.extend(table_results)

            # Update existing keys
            for result in table_results:
                key = (result.test_date, result.test_name, result.result_raw)
                existing_keys.add(key)

        # Fallback: text extraction (will skip duplicates)
        text_results = self.text_extractor.extract_from_text(
            text, current_date, existing_keys
        )
        results.extend(text_results)

        return results
