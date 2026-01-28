"""
Data models for blood test results.
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
import re


class ReferenceRange(BaseModel):
    """Reference range for a blood test result."""
    min_value: Optional[float] = Field(None, description="Minimum normal value")
    max_value: Optional[float] = Field(None, description="Maximum normal value")
    original_text: str = Field(..., description="Original reference range text")

    model_config = ConfigDict(frozen=True)  # Make immutable

    @classmethod
    def parse(cls, range_str: str) -> "ReferenceRange":
        """
        Parse reference range string into min/max values.

        Supports formats:
        - "4.0 - 11.0" -> min=4.0, max=11.0
        - "<6.0" -> min=None, max=6.0
        - ">220" or ">=1.00" -> min=220 or 1.0, max=None
        - "<=10" -> min=None, max=10

        Args:
            range_str: Reference range string from lab report

        Returns:
            ReferenceRange object
        """
        if not range_str or range_str.strip() == "":
            return cls(min_value=None, max_value=None, original_text="")

        range_str_clean = range_str.strip()

        # Handle range format: "4.0 - 11.0"
        if " - " in range_str_clean or "-" in range_str_clean:
            # Try with space around dash first
            if " - " in range_str_clean:
                parts = range_str_clean.split(" - ")
            else:
                # Handle cases like "4.0-11.0"
                parts = range_str_clean.split("-")

            if len(parts) == 2:
                try:
                    min_val = float(parts[0].strip().replace(",", ""))
                    max_val = float(parts[1].strip().replace(",", ""))
                    return cls(min_value=min_val, max_value=max_val, original_text=range_str)
                except ValueError:
                    pass

        # Handle upper limit: "<6.0" or "<=6.0"
        if range_str_clean.startswith("<="):
            try:
                max_val = float(range_str_clean[2:].strip().replace(",", ""))
                return cls(min_value=None, max_value=max_val, original_text=range_str)
            except ValueError:
                pass
        elif range_str_clean.startswith("<"):
            try:
                max_val = float(range_str_clean[1:].strip().replace(",", ""))
                return cls(min_value=None, max_value=max_val, original_text=range_str)
            except ValueError:
                pass

        # Handle lower limit: ">220" or ">=1.00"
        if range_str_clean.startswith(">="):
            try:
                min_val = float(range_str_clean[2:].strip().replace(",", ""))
                return cls(min_value=min_val, max_value=None, original_text=range_str)
            except ValueError:
                pass
        elif range_str_clean.startswith(">"):
            try:
                min_val = float(range_str_clean[1:].strip().replace(",", ""))
                return cls(min_value=min_val, max_value=None, original_text=range_str)
            except ValueError:
                pass

        # If we can't parse it, return with original text only
        return cls(min_value=None, max_value=None, original_text=range_str)

    def is_within_range(self, value: float) -> bool:
        """
        Check if a value is within the reference range.

        Args:
            value: Test result value

        Returns:
            True if within range, False otherwise
        """
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True

    def __str__(self) -> str:
        """String representation of the reference range."""
        return self.original_text


class BloodTestResult(BaseModel):
    """
    A single blood test result.

    This model represents one test result from a blood work report,
    including the test name, value, reference range, and any flags.
    """
    id: Optional[int] = Field(None, description="Database ID (auto-generated)")
    patient_id: str = Field(..., description="Patient identifier (from parent app)")
    test_date: date = Field(..., description="Date the test was performed")
    test_name: str = Field(..., min_length=2, description="Name of the blood test")
    result_value: float = Field(..., description="Numeric test result")
    result_raw: str = Field(..., description="Original result string from report")
    reference_range: ReferenceRange = Field(..., description="Normal range for this test")
    units: str = Field("", description="Units of measurement")
    flag: str = Field("NORMAL", description="Result flag (NORMAL, HIGH, LOW)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "patient_id": "user123",
                "test_date": "2024-06-10",
                "test_name": "HDL Cholesterol",
                "result_value": 0.97,
                "result_raw": "0.97",
                "reference_range": {
                    "min_value": 1.0,
                    "max_value": None,
                    "original_text": ">=1.00"
                },
                "units": "mmol/L",
                "flag": "LOW"
            }
        }
    )

    @field_validator("test_name")
    @classmethod
    def validate_test_name(cls, v: str) -> str:
        """Validate and normalize test name."""
        if not v or len(v.strip()) < 2:
            raise ValueError("Test name must be at least 2 characters long")
        return v.strip()

    @field_validator("result_raw")
    @classmethod
    def validate_result_raw(cls, v: str) -> str:
        """Validate that result contains some numeric data."""
        if not v or not re.search(r'\d', v):
            raise ValueError("Result must contain at least one digit")
        return v.strip()

    @field_validator("patient_id")
    @classmethod
    def validate_patient_id(cls, v: str) -> str:
        """Validate patient ID is not empty."""
        if not v or v.strip() == "":
            raise ValueError("Patient ID cannot be empty")
        return v.strip()

    def is_abnormal(self) -> bool:
        """
        Check if this test result is abnormal (outside reference range).

        Returns:
            True if result is abnormal, False otherwise
        """
        return self.flag in ["HIGH", "LOW"]

    def get_deviation_percentage(self) -> Optional[float]:
        """
        Calculate how far the result deviates from normal range (as percentage).

        Returns:
            Percentage deviation from normal range, or None if no range defined
        """
        if self.reference_range.min_value is not None and self.result_value < self.reference_range.min_value:
            # Below minimum
            deviation = ((self.reference_range.min_value - self.result_value) / self.reference_range.min_value) * 100
            return -deviation  # Negative for below range

        if self.reference_range.max_value is not None and self.result_value > self.reference_range.max_value:
            # Above maximum
            deviation = ((self.result_value - self.reference_range.max_value) / self.reference_range.max_value) * 100
            return deviation  # Positive for above range

        return None  # Within range or no range defined

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "test_date": self.test_date.isoformat(),
            "test_name": self.test_name,
            "result_value": self.result_value,
            "result_raw": self.result_raw,
            "reference_range": {
                "min_value": self.reference_range.min_value,
                "max_value": self.reference_range.max_value,
                "original_text": self.reference_range.original_text
            },
            "units": self.units,
            "flag": self.flag,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BloodTestResult":
        """
        Create BloodTestResult from dictionary.

        Args:
            data: Dictionary with test result data

        Returns:
            BloodTestResult instance
        """
        # Handle reference_range if it's a dict
        if isinstance(data.get("reference_range"), dict):
            data["reference_range"] = ReferenceRange(**data["reference_range"])

        # Handle date strings
        if isinstance(data.get("test_date"), str):
            data["test_date"] = date.fromisoformat(data["test_date"])

        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        return cls(**data)

    def __str__(self) -> str:
        """String representation of the test result."""
        flag_indicator = f" [{self.flag}]" if self.is_abnormal() else ""
        return f"{self.test_name}: {self.result_value} {self.units}{flag_indicator} (Ref: {self.reference_range})"
