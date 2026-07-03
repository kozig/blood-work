"""
Abstract base class for blood work parsers.

Defines the interface that all lab-specific parsers must implement.
"""
from abc import ABC, abstractmethod
from typing import BinaryIO, Tuple, List, Set
from bloodwork.models import BloodTestResult, PatientInfo


class AbstractBloodWorkParser(ABC):
    """
    Abstract base class for parsing blood work PDF reports.

    Subclasses implement lab-specific parsing logic while following
    a common interface for use by the service layer.
    """

    def __init__(self, pdf_file: BinaryIO, patient_id: str):
        """
        Initialize parser with PDF file and patient identifier.

        Args:
            pdf_file: File-like object containing PDF data
            patient_id: Patient identifier (from parent application)
        """
        self.pdf_file = pdf_file
        self.patient_id = patient_id
        self.results: List[BloodTestResult] = []
        self.patient_info: PatientInfo = PatientInfo(patient_id=patient_id)

    @abstractmethod
    def parse(self) -> Tuple[PatientInfo, List[BloodTestResult]]:
        """
        Parse the PDF and extract blood work data.

        This is the main entry point for parsing. Subclasses must implement
        the specific parsing logic for their lab format.

        Returns:
            Tuple of (PatientInfo, List[BloodTestResult])

        Raises:
            ParserError: If parsing fails
        """
        pass

    def deduplicate_results(self, results: List[BloodTestResult]) -> List[BloodTestResult]:
        """
        Remove duplicate results based on (date, test_name, result_value).

        Args:
            results: List of BloodTestResult objects

        Returns:
            Deduplicated list of BloodTestResult objects
        """
        seen: Set[Tuple] = set()
        unique_results = []

        for result in results:
            key = (result.test_date, result.test_name, result.result_raw)
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        return unique_results

    def validate_results(self, results: List[BloodTestResult]) -> List[BloodTestResult]:
        """
        Validate and filter results.

        Removes results that don't meet minimum requirements
        (e.g., test name too short, invalid values).

        Args:
            results: List of BloodTestResult objects

        Returns:
            Filtered list of valid BloodTestResult objects
        """
        valid_results = []

        for result in results:
            # Basic validation
            if len(result.test_name) < 2:
                continue
            if result.result_value == 0 and result.result_raw == "0":
                # Might be legitimate, but often indicates parsing error
                pass

            valid_results.append(result)

        return valid_results


class ParserError(Exception):
    """Exception raised when parsing fails."""
    pass
