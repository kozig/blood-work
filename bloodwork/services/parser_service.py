"""
Parser service for orchestrating PDF parsing workflow.

Handles PDF upload, parsing, and storage of blood work data.
"""
import logging
from typing import BinaryIO, Optional, List
from pydantic import BaseModel

from bloodwork.models import BloodTestResult, PatientInfo
from bloodwork.parsers import AbstractBloodWorkParser, LifeLabsParser, ParserError
from bloodwork.repositories import AbstractRepository, RepositoryError

logger = logging.getLogger(__name__)


class ParseResult(BaseModel):
    """Result of PDF parsing operation."""
    patient_info: PatientInfo
    num_results: int
    num_abnormal: int
    abnormal_tests: List[str]
    errors: List[str] = []
    success: bool = True

    class Config:
        arbitrary_types_allowed = True


class ParserService:
    """
    Service for parsing blood work PDFs and storing results.

    Orchestrates the workflow:
    1. Parse PDF using appropriate parser
    2. Store results in repository
    3. Return summary
    """

    def __init__(self, repository: AbstractRepository):
        """
        Initialize parser service.

        Args:
            repository: Repository for storing parsed data
        """
        self.repository = repository

    def parse_and_store(
        self,
        pdf_file: BinaryIO,
        patient_id: str,
        parser_type: str = "lifelabs"
    ) -> ParseResult:
        """
        Parse PDF file and store results.

        Args:
            pdf_file: File-like object containing PDF data
            patient_id: Patient identifier
            parser_type: Type of parser to use ("lifelabs" is default)

        Returns:
            ParseResult with summary of parsing operation

        Raises:
            ParserError: If parsing fails
            RepositoryError: If storage fails
        """
        try:
            # Get appropriate parser
            parser = self.get_parser(pdf_file, patient_id, parser_type)

            # Parse PDF
            logger.info(f"Parsing PDF for patient {patient_id}")
            patient_info, results = parser.parse()

            # Store patient info
            logger.info(f"Storing patient info for {patient_id}")
            self.repository.save_patient_info(patient_info)

            # Store results
            logger.info(f"Storing {len(results)} test results")
            self.repository.save_results(results)

            # Calculate summary statistics
            abnormal_results = [r for r in results if r.is_abnormal()]
            abnormal_test_names = list(set([r.test_name for r in abnormal_results]))

            return ParseResult(
                patient_info=patient_info,
                num_results=len(results),
                num_abnormal=len(abnormal_results),
                abnormal_tests=abnormal_test_names,
                success=True
            )

        except ParserError as e:
            logger.error(f"Parsing failed: {e}")
            raise

        except RepositoryError as e:
            logger.error(f"Storage failed: {e}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise ParserError(f"Failed to parse and store: {e}")

    def get_parser(
        self,
        pdf_file: BinaryIO,
        patient_id: str,
        parser_type: str
    ) -> AbstractBloodWorkParser:
        """
        Factory method to get appropriate parser.

        Args:
            pdf_file: PDF file to parse
            patient_id: Patient identifier
            parser_type: Type of parser ("lifelabs", etc.)

        Returns:
            Parser instance

        Raises:
            ValueError: If parser type is not supported
        """
        parser_type_lower = parser_type.lower()

        if parser_type_lower == "lifelabs":
            return LifeLabsParser(pdf_file, patient_id)
        else:
            raise ValueError(f"Unsupported parser type: {parser_type}")

    @staticmethod
    def validate_pdf_file(pdf_file: BinaryIO, max_size_mb: int = 50) -> bool:
        """
        Validate PDF file before parsing.

        Args:
            pdf_file: PDF file to validate
            max_size_mb: Maximum file size in MB

        Returns:
            True if valid

        Raises:
            ValueError: If file is invalid
        """
        # Check file size
        pdf_file.seek(0, 2)  # Seek to end
        file_size = pdf_file.tell()
        pdf_file.seek(0)  # Reset to beginning

        max_size_bytes = max_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise ValueError(
                f"File too large: {file_size / 1024 / 1024:.1f}MB "
                f"(max {max_size_mb}MB)"
            )

        # Check PDF header
        pdf_file.seek(0)
        header = pdf_file.read(5)
        pdf_file.seek(0)

        if header != b'%PDF-':
            raise ValueError("Invalid PDF file: missing PDF header")

        return True
