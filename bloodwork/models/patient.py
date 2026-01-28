"""
Data models for patient information.
"""
from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class PatientInfo(BaseModel):
    """
    Patient demographic information.

    NOTE: Authentication and user management is handled by the parent application.
    The patient_id is the foreign key linking to the parent app's user system.
    """
    patient_id: str = Field(..., description="Patient identifier (links to parent app)")
    name: Optional[str] = Field(None, description="Patient name (optional for privacy)")
    age: Optional[int] = Field(None, ge=0, le=150, description="Patient age in years")
    gender: Optional[Literal["M", "F", "O"]] = Field(None, description="Patient gender (M/F/O)")
    date_of_birth: Optional[date] = Field(None, description="Patient date of birth")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Record creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Record update timestamp")

    @field_validator("patient_id")
    @classmethod
    def validate_patient_id(cls, v: str) -> str:
        """Validate patient ID is not empty."""
        if not v or v.strip() == "":
            raise ValueError("Patient ID cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize patient name."""
        if v is None:
            return None
        v = v.strip()
        if len(v) == 0:
            return None
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        """Validate gender value."""
        if v is None:
            return None
        v_upper = v.strip().upper()
        if v_upper not in ["M", "F", "O"]:
            raise ValueError("Gender must be M, F, or O")
        return v_upper

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        """Validate date of birth is not in the future."""
        if v is not None and v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

    def calculate_age(self) -> Optional[int]:
        """
        Calculate current age from date of birth.

        Returns:
            Age in years, or None if DOB not available
        """
        if self.date_of_birth is None:
            return self.age

        today = date.today()
        age = today.year - self.date_of_birth.year
        # Adjust if birthday hasn't occurred yet this year
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1

        return age

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "patient_id": self.patient_id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PatientInfo":
        """
        Create PatientInfo from dictionary.

        Args:
            data: Dictionary with patient data

        Returns:
            PatientInfo instance
        """
        # Handle date strings
        if isinstance(data.get("date_of_birth"), str):
            data["date_of_birth"] = date.fromisoformat(data["date_of_birth"])

        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return cls(**data)

    def __str__(self) -> str:
        """String representation (privacy-conscious)."""
        # Don't expose full name in string representation
        age_str = f", {self.age}y" if self.age else ""
        gender_str = f", {self.gender}" if self.gender else ""
        return f"Patient({self.patient_id}{age_str}{gender_str})"
