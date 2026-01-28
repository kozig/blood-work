"""
Unit tests for bloodwork.parsers module.
"""
import pytest
from datetime import date
from bloodwork.parsers.extractors import DateExtractor, MetadataExtractor
from bloodwork.models import PatientInfo


class TestDateExtractor:
    """Tests for DateExtractor."""

    def test_parse_date_format_1(self):
        """Test parsing 'Jun 10 2025' format."""
        extractor = DateExtractor()
        result = extractor.parse_date("Jun 10 2025")
        assert result == date(2025, 6, 10)

    def test_parse_date_format_2(self):
        """Test parsing '10-JUN-2025' format."""
        extractor = DateExtractor()
        result = extractor.parse_date("10-JUN-2025")
        assert result == date(2025, 6, 10)

    def test_parse_date_with_time(self):
        """Test parsing date with time removes time portion."""
        extractor = DateExtractor()
        result = extractor.parse_date("Jun 10 2025 08:07")
        assert result == date(2025, 6, 10)

    def test_parse_date_invalid(self):
        """Test parsing invalid date returns None."""
        extractor = DateExtractor()
        result = extractor.parse_date("invalid date")
        assert result is None

    def test_extract_date_from_text(self):
        """Test extracting date from text."""
        extractor = DateExtractor()
        text = "Date of Service: Jun 10 2025 08:07\nPatient: John Doe"
        result = extractor.extract_date(text)
        assert result == date(2025, 6, 10)

    def test_extract_date_not_found(self):
        """Test when date pattern not found in text."""
        extractor = DateExtractor()
        text = "Patient: John Doe\nTest: WBC"
        result = extractor.extract_date(text)
        assert result is None

    def test_format_date(self):
        """Test formatting date to ISO string."""
        test_date = date(2025, 6, 10)
        result = DateExtractor.format_date(test_date)
        assert result == "2025-06-10"


class TestMetadataExtractor:
    """Tests for MetadataExtractor."""

    def test_extract_patient_info_complete(self):
        """Test extracting complete patient info."""
        extractor = MetadataExtractor()
        text = """
        Patient: DOE, JOHN
        Age: 42 years
        Gender: M
        Date of Birth: Feb 13 1982
        """

        patient = extractor.extract_patient_info(text, "test123")

        assert patient.patient_id == "test123"
        assert patient.name == "DOE, JOHN"
        assert patient.age == 42
        assert patient.gender == "M"
        assert patient.date_of_birth == date(1982, 2, 13)

    def test_extract_patient_info_partial(self):
        """Test extracting partial patient info."""
        extractor = MetadataExtractor()
        text = """
        Patient: DOE, JOHN
        Age: 42 years
        """

        patient = extractor.extract_patient_info(text, "test123")

        assert patient.patient_id == "test123"
        assert patient.name == "DOE, JOHN"
        assert patient.age == 42
        assert patient.gender is None
        assert patient.date_of_birth is None

    def test_extract_patient_info_missing(self):
        """Test extracting when no patient info present."""
        extractor = MetadataExtractor()
        text = "Some random text with no patient information"

        patient = extractor.extract_patient_info(text, "test123")

        assert patient.patient_id == "test123"
        assert patient.name is None
        assert patient.age is None

    def test_merge_patient_info(self):
        """Test merging patient info."""
        existing = PatientInfo(
            patient_id="test123",
            name="DOE, JOHN",
            age=42
        )

        new = PatientInfo(
            patient_id="test123",
            gender="M",
            date_of_birth=date(1982, 2, 13)
        )

        merged = MetadataExtractor.merge_patient_info(existing, new)

        assert merged.patient_id == "test123"
        assert merged.name == "DOE, JOHN"  # From existing
        assert merged.age == 42  # From existing
        assert merged.gender == "M"  # From new
        assert merged.date_of_birth == date(1982, 2, 13)  # From new

    def test_merge_patient_info_none_existing(self):
        """Test merging when existing is None."""
        new = PatientInfo(
            patient_id="test123",
            name="DOE, JOHN"
        )

        merged = MetadataExtractor.merge_patient_info(None, new)

        assert merged.patient_id == "test123"
        assert merged.name == "DOE, JOHN"


# Note: For table and text extractors, we'd need mock PDF data
# These tests would require actual PDF fixtures or mocked pdfplumber objects
class TestTableExtractor:
    """Tests for TableExtractor (requires PDF fixtures)."""

    def test_table_extractor_initialization(self):
        """Test table extractor can be initialized."""
        from bloodwork.parsers.extractors import TableExtractor
        extractor = TableExtractor("test123")
        assert extractor.patient_id == "test123"


class TestTextExtractor:
    """Tests for TextExtractor (requires more complex setup)."""

    def test_text_extractor_initialization(self):
        """Test text extractor can be initialized."""
        from bloodwork.parsers.extractors import TextExtractor
        extractor = TextExtractor("test123")
        assert extractor.patient_id == "test123"


class TestLifeLabsParser:
    """Tests for LifeLabsParser."""

    def test_parser_initialization(self):
        """Test parser can be initialized."""
        from bloodwork.parsers import LifeLabsParser
        from io import BytesIO

        pdf_content = BytesIO(b"%PDF-1.4\n%fake pdf")
        parser = LifeLabsParser(pdf_content, "test123")

        assert parser.patient_id == "test123"
        assert parser.results == []

    # Full parser tests would require actual PDF fixtures
    # which we can add later with test data
