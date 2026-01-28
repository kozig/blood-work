"""
Unit tests for bloodwork.models module.
"""
import pytest
from datetime import date, datetime
from bloodwork.models import (
    ReferenceRange,
    BloodTestResult,
    PatientInfo,
    ResultFlag,
    TestCategory
)


class TestReferenceRange:
    """Tests for ReferenceRange model."""

    def test_parse_range_format(self):
        """Test parsing range format like '4.0 - 11.0'."""
        ref = ReferenceRange.parse("4.0 - 11.0")
        assert ref.min_value == 4.0
        assert ref.max_value == 11.0
        assert ref.original_text == "4.0 - 11.0"

    def test_parse_upper_limit(self):
        """Test parsing upper limit format like '<6.0'."""
        ref = ReferenceRange.parse("<6.0")
        assert ref.min_value is None
        assert ref.max_value == 6.0

    def test_parse_lower_limit(self):
        """Test parsing lower limit format like '>220' or '>=1.00'."""
        ref1 = ReferenceRange.parse(">220")
        assert ref1.min_value == 220.0
        assert ref1.max_value is None

        ref2 = ReferenceRange.parse(">=1.00")
        assert ref2.min_value == 1.0
        assert ref2.max_value is None

    def test_parse_invalid_format(self):
        """Test parsing invalid format returns original text."""
        ref = ReferenceRange.parse("invalid")
        assert ref.min_value is None
        assert ref.max_value is None
        assert ref.original_text == "invalid"

    def test_is_within_range(self):
        """Test checking if value is within range."""
        ref = ReferenceRange.parse("4.0 - 11.0")
        assert ref.is_within_range(5.0) is True
        assert ref.is_within_range(3.0) is False
        assert ref.is_within_range(12.0) is False

    def test_immutability(self):
        """Test that ReferenceRange is immutable."""
        ref = ReferenceRange.parse("4.0 - 11.0")
        with pytest.raises(Exception):  # Pydantic frozen model raises error
            ref.min_value = 5.0


class TestBloodTestResult:
    """Tests for BloodTestResult model."""

    def test_create_valid_result(self):
        """Test creating a valid blood test result."""
        ref_range = ReferenceRange.parse("4.0 - 11.0")
        result = BloodTestResult(
            patient_id="test123",
            test_date=date(2024, 6, 10),
            test_name="WBC",
            result_value=5.9,
            result_raw="5.9",
            reference_range=ref_range,
            units="x E9/L",
            flag="NORMAL"
        )

        assert result.patient_id == "test123"
        assert result.test_name == "WBC"
        assert result.result_value == 5.9
        assert result.is_abnormal() is False

    def test_validation_short_test_name(self):
        """Test validation fails for short test names."""
        ref_range = ReferenceRange.parse("4.0 - 11.0")
        with pytest.raises(ValueError, match="at least 2 characters"):
            BloodTestResult(
                patient_id="test123",
                test_date=date(2024, 6, 10),
                test_name="W",  # Too short
                result_value=5.9,
                result_raw="5.9",
                reference_range=ref_range,
                units="x E9/L"
            )

    def test_validation_empty_patient_id(self):
        """Test validation fails for empty patient ID."""
        ref_range = ReferenceRange.parse("4.0 - 11.0")
        with pytest.raises(ValueError, match="Patient ID cannot be empty"):
            BloodTestResult(
                patient_id="",
                test_date=date(2024, 6, 10),
                test_name="WBC",
                result_value=5.9,
                result_raw="5.9",
                reference_range=ref_range,
                units="x E9/L"
            )

    def test_is_abnormal(self):
        """Test abnormal detection."""
        ref_range = ReferenceRange.parse("4.0 - 11.0")

        # Normal result
        normal = BloodTestResult(
            patient_id="test123",
            test_date=date(2024, 6, 10),
            test_name="WBC",
            result_value=5.9,
            result_raw="5.9",
            reference_range=ref_range,
            units="x E9/L",
            flag="NORMAL"
        )
        assert normal.is_abnormal() is False

        # High result
        high = BloodTestResult(
            patient_id="test123",
            test_date=date(2024, 6, 10),
            test_name="WBC",
            result_value=15.0,
            result_raw="15.0",
            reference_range=ref_range,
            units="x E9/L",
            flag="HIGH"
        )
        assert high.is_abnormal() is True

    def test_get_deviation_percentage(self):
        """Test deviation percentage calculation."""
        ref_range = ReferenceRange.parse("4.0 - 11.0")

        # Below minimum
        below = BloodTestResult(
            patient_id="test123",
            test_date=date(2024, 6, 10),
            test_name="WBC",
            result_value=3.0,
            result_raw="3.0",
            reference_range=ref_range,
            units="x E9/L",
            flag="LOW"
        )
        deviation = below.get_deviation_percentage()
        assert deviation is not None
        assert deviation < 0  # Negative for below range

        # Above maximum
        above = BloodTestResult(
            patient_id="test123",
            test_date=date(2024, 6, 10),
            test_name="WBC",
            result_value=12.0,
            result_raw="12.0",
            reference_range=ref_range,
            units="x E9/L",
            flag="HIGH"
        )
        deviation = above.get_deviation_percentage()
        assert deviation is not None
        assert deviation > 0  # Positive for above range

    def test_to_dict_and_from_dict(self):
        """Test serialization and deserialization."""
        ref_range = ReferenceRange.parse("4.0 - 11.0")
        original = BloodTestResult(
            patient_id="test123",
            test_date=date(2024, 6, 10),
            test_name="WBC",
            result_value=5.9,
            result_raw="5.9",
            reference_range=ref_range,
            units="x E9/L",
            flag="NORMAL"
        )

        # Convert to dict
        data = original.to_dict()
        assert data["patient_id"] == "test123"
        assert data["test_name"] == "WBC"

        # Convert back from dict
        restored = BloodTestResult.from_dict(data)
        assert restored.patient_id == original.patient_id
        assert restored.test_name == original.test_name
        assert restored.result_value == original.result_value


class TestPatientInfo:
    """Tests for PatientInfo model."""

    def test_create_valid_patient(self):
        """Test creating valid patient info."""
        patient = PatientInfo(
            patient_id="test123",
            name="John Doe",
            age=42,
            gender="M",
            date_of_birth=date(1982, 2, 13)
        )

        assert patient.patient_id == "test123"
        assert patient.name == "John Doe"
        assert patient.age == 42
        assert patient.gender == "M"

    def test_validation_empty_patient_id(self):
        """Test validation fails for empty patient ID."""
        with pytest.raises(ValueError, match="Patient ID cannot be empty"):
            PatientInfo(patient_id="")

    def test_validation_invalid_gender(self):
        """Test validation fails for invalid gender."""
        with pytest.raises(ValueError, match="Gender must be M, F, or O"):
            PatientInfo(
                patient_id="test123",
                gender="X"  # Invalid
            )

    def test_validation_future_dob(self):
        """Test validation fails for future date of birth."""
        from datetime import timedelta
        future_date = date.today() + timedelta(days=1)

        with pytest.raises(ValueError, match="cannot be in the future"):
            PatientInfo(
                patient_id="test123",
                date_of_birth=future_date
            )

    def test_calculate_age_from_dob(self):
        """Test age calculation from date of birth."""
        patient = PatientInfo(
            patient_id="test123",
            date_of_birth=date(1982, 2, 13)
        )

        age = patient.calculate_age()
        assert age is not None
        assert age > 40  # Should be at least 40 years old

    def test_optional_fields(self):
        """Test that name, age, gender, DOB are optional."""
        patient = PatientInfo(patient_id="test123")
        assert patient.name is None
        assert patient.age is None
        assert patient.gender is None
        assert patient.date_of_birth is None


class TestResultFlag:
    """Tests for ResultFlag enum."""

    def test_from_lifelabs(self):
        """Test conversion from LifeLabs flag format."""
        assert ResultFlag.from_lifelabs("HI") == ResultFlag.HIGH
        assert ResultFlag.from_lifelabs("LO") == ResultFlag.LOW
        assert ResultFlag.from_lifelabs("") == ResultFlag.NORMAL
        assert ResultFlag.from_lifelabs(None) == ResultFlag.NORMAL


class TestTestCategory:
    """Tests for TestCategory enum."""

    def test_categorize_lipid_panel(self):
        """Test categorization of lipid panel tests."""
        assert TestCategory.categorize_test("HDL Cholesterol") == TestCategory.LIPID_PANEL
        assert TestCategory.categorize_test("LDL Cholesterol") == TestCategory.LIPID_PANEL
        assert TestCategory.categorize_test("Triglyceride") == TestCategory.LIPID_PANEL

    def test_categorize_liver_function(self):
        """Test categorization of liver function tests."""
        assert TestCategory.categorize_test("ALT") == TestCategory.LIVER_FUNCTION
        assert TestCategory.categorize_test("AST") == TestCategory.LIVER_FUNCTION
        assert TestCategory.categorize_test("Gamma Glutamyl Transferase") == TestCategory.LIVER_FUNCTION

    def test_categorize_complete_blood_count(self):
        """Test categorization of CBC tests."""
        assert TestCategory.categorize_test("WBC") == TestCategory.COMPLETE_BLOOD_COUNT
        assert TestCategory.categorize_test("RBC") == TestCategory.COMPLETE_BLOOD_COUNT
        assert TestCategory.categorize_test("Hemoglobin") == TestCategory.COMPLETE_BLOOD_COUNT

    def test_categorize_unknown(self):
        """Test categorization of unknown tests."""
        assert TestCategory.categorize_test("Unknown Test Name") == TestCategory.OTHER
