"""
Patient metadata extraction utilities.

Handles extraction of patient information (name, age, gender, DOB) from PDF text.
"""
import re
from typing import Optional, Dict
from bloodwork.models import PatientInfo
from bloodwork.config import PATIENT_FIELD_PATTERNS
from bloodwork.parsers.extractors.date import DateExtractor


class MetadataExtractor:
    """Extract patient metadata from text."""

    def __init__(self, field_patterns: Optional[Dict[str, str]] = None):
        """
        Initialize metadata extractor.

        Args:
            field_patterns: Dictionary of field names to regex patterns (uses defaults if None)
        """
        self.field_patterns = field_patterns or PATIENT_FIELD_PATTERNS
        self.date_extractor = DateExtractor()

    def extract_patient_info(self, text: str, patient_id: str) -> PatientInfo:
        """
        Extract patient information from text.

        Args:
            text: Text to extract patient info from
            patient_id: Patient identifier (required)

        Returns:
            PatientInfo object with extracted data
        """
        # Extract name
        name = self._extract_field(text, 'name')

        # Extract age
        age_str = self._extract_field(text, 'age')
        age = int(age_str) if age_str and age_str.isdigit() else None

        # Extract gender
        gender = self._extract_field(text, 'gender')
        if gender:
            gender = gender.upper()

        # Extract date of birth
        dob_str = self._extract_field(text, 'dob')
        if not dob_str:
            dob_str = self._extract_field(text, 'dob_alt')

        dob = None
        if dob_str:
            dob = self.date_extractor.parse_date(dob_str)

        return PatientInfo(
            patient_id=patient_id,
            name=name,
            age=age,
            gender=gender,
            date_of_birth=dob
        )

    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Extract a specific field from text using configured patterns.

        Args:
            text: Text to search
            field_name: Name of field to extract

        Returns:
            Extracted field value or None if not found
        """
        if field_name not in self.field_patterns:
            return None

        pattern = self.field_patterns[field_name]
        match = re.search(pattern, text)

        if match:
            return match.group(1).strip()

        return None

    @staticmethod
    def merge_patient_info(existing: Optional[PatientInfo], new: PatientInfo) -> PatientInfo:
        """
        Merge new patient info with existing, preferring non-None values.

        Args:
            existing: Existing PatientInfo (may be None)
            new: New PatientInfo to merge

        Returns:
            Merged PatientInfo object
        """
        if existing is None:
            return new

        return PatientInfo(
            patient_id=new.patient_id,
            name=new.name or existing.name,
            age=new.age or existing.age,
            gender=new.gender or existing.gender,
            date_of_birth=new.date_of_birth or existing.date_of_birth
        )
