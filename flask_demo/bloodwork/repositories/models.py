"""
SQLAlchemy ORM models for database persistence.

These models map to database tables and provide the persistence layer
for blood work analysis data.
"""
from datetime import datetime, date
from typing import List
from sqlalchemy import (
    String, Float, Integer, Date, DateTime, Text, Index,
    ForeignKey, create_engine
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, Session
)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class PatientInfoORM(Base):
    """
    Patient information table.

    Stores demographic information for patients. The patient_id links to
    the parent application's user management system.
    """
    __tablename__ = "patient_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    gender: Mapped[str] = mapped_column(String(1), nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationship to test results
    test_results: Mapped[List["BloodTestResultORM"]] = relationship(
        "BloodTestResultORM", back_populates="patient", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PatientInfo(patient_id='{self.patient_id}', age={self.age}, gender='{self.gender}')>"


class BloodTestResultORM(Base):
    """
    Blood test results table.

    Stores individual test results with reference ranges and flags.
    """
    __tablename__ = "blood_test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("patient_info.patient_id"), nullable=False, index=True
    )
    test_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    test_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    result_value: Mapped[float] = mapped_column(Float, nullable=False)
    result_raw: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_range_min: Mapped[float] = mapped_column(Float, nullable=True)
    reference_range_max: Mapped[float] = mapped_column(Float, nullable=True)
    reference_range_text: Mapped[str] = mapped_column(String(100), nullable=False)
    units: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    flag: Mapped[str] = mapped_column(String(20), nullable=False, default="NORMAL", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to patient
    patient: Mapped["PatientInfoORM"] = relationship("PatientInfoORM", back_populates="test_results")

    # Composite index for efficient queries
    __table_args__ = (
        Index("idx_patient_test_date", "patient_id", "test_date"),
        Index("idx_patient_test_name", "patient_id", "test_name"),
        Index("idx_test_date_flag", "test_date", "flag"),
    )

    def __repr__(self) -> str:
        return (
            f"<BloodTestResult(patient_id='{self.patient_id}', "
            f"test_date={self.test_date}, test_name='{self.test_name}', "
            f"result={self.result_value}, flag='{self.flag}')>"
        )


def create_tables(engine):
    """
    Create all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """
    Drop all database tables (use with caution!).

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.drop_all(engine)
