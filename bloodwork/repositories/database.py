"""
Database repository implementation using SQLAlchemy.

Provides persistence for blood work data using PostgreSQL or MySQL.
"""
from datetime import date
from typing import List, Optional
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from bloodwork.models import BloodTestResult, PatientInfo, ReferenceRange
from bloodwork.repositories.base import AbstractRepository, RepositoryError
from bloodwork.repositories.models import (
    Base, BloodTestResultORM, PatientInfoORM, create_tables
)


class DatabaseRepository(AbstractRepository):
    """
    Database-backed repository using SQLAlchemy.

    Supports PostgreSQL and MySQL databases.
    """

    def __init__(self, connection_string: str, echo: bool = False):
        """
        Initialize database repository.

        Args:
            connection_string: SQLAlchemy database URL
                Examples:
                - PostgreSQL: "postgresql://user:pass@localhost/dbname"
                - MySQL: "mysql+pymysql://user:pass@localhost/dbname"
                - SQLite (testing): "sqlite:///./test.db"
            echo: If True, log all SQL statements (for debugging)

        Raises:
            RepositoryError: If database connection fails
        """
        try:
            self.engine = create_engine(connection_string, echo=echo)
            self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

            # Create tables if they don't exist
            create_tables(self.engine)

        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to initialize database: {e}")

    def save_patient_info(self, patient: PatientInfo) -> None:
        """Save or update patient information."""
        with self.SessionLocal() as session:
            try:
                # Check if patient exists
                stmt = select(PatientInfoORM).where(
                    PatientInfoORM.patient_id == patient.patient_id
                )
                existing = session.execute(stmt).scalar_one_or_none()

                if existing:
                    # Update existing patient
                    if patient.name is not None:
                        existing.name = patient.name
                    if patient.age is not None:
                        existing.age = patient.age
                    if patient.gender is not None:
                        existing.gender = patient.gender
                    if patient.date_of_birth is not None:
                        existing.date_of_birth = patient.date_of_birth
                else:
                    # Create new patient
                    patient_orm = PatientInfoORM(
                        patient_id=patient.patient_id,
                        name=patient.name,
                        age=patient.age,
                        gender=patient.gender,
                        date_of_birth=patient.date_of_birth
                    )
                    session.add(patient_orm)

                session.commit()

            except SQLAlchemyError as e:
                session.rollback()
                raise RepositoryError(f"Failed to save patient info: {e}")

    def get_patient_info(self, patient_id: str) -> Optional[PatientInfo]:
        """Retrieve patient information by ID."""
        with self.SessionLocal() as session:
            try:
                stmt = select(PatientInfoORM).where(
                    PatientInfoORM.patient_id == patient_id
                )
                patient_orm = session.execute(stmt).scalar_one_or_none()

                if patient_orm is None:
                    return None

                return PatientInfo(
                    patient_id=patient_orm.patient_id,
                    name=patient_orm.name,
                    age=patient_orm.age,
                    gender=patient_orm.gender,
                    date_of_birth=patient_orm.date_of_birth,
                    created_at=patient_orm.created_at,
                    updated_at=patient_orm.updated_at
                )

            except SQLAlchemyError as e:
                raise RepositoryError(f"Failed to retrieve patient info: {e}")

    def save_results(self, results: List[BloodTestResult]) -> None:
        """Save blood test results (bulk operation)."""
        if not results:
            return

        with self.SessionLocal() as session:
            try:
                # Ensure patient exists
                patient_id = results[0].patient_id
                patient_exists = session.execute(
                    select(PatientInfoORM).where(
                        PatientInfoORM.patient_id == patient_id
                    )
                ).scalar_one_or_none()

                if not patient_exists:
                    # Create minimal patient record
                    patient_orm = PatientInfoORM(patient_id=patient_id)
                    session.add(patient_orm)

                # Add test results
                for result in results:
                    result_orm = BloodTestResultORM(
                        patient_id=result.patient_id,
                        test_date=result.test_date,
                        test_name=result.test_name,
                        result_value=result.result_value,
                        result_raw=result.result_raw,
                        reference_range_min=result.reference_range.min_value,
                        reference_range_max=result.reference_range.max_value,
                        reference_range_text=result.reference_range.original_text,
                        units=result.units,
                        flag=result.flag
                    )
                    session.add(result_orm)

                session.commit()

            except SQLAlchemyError as e:
                session.rollback()
                raise RepositoryError(f"Failed to save test results: {e}")

    def get_results(
        self,
        patient_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        test_name: Optional[str] = None
    ) -> List[BloodTestResult]:
        """Retrieve blood test results with optional filtering."""
        with self.SessionLocal() as session:
            try:
                stmt = select(BloodTestResultORM).where(
                    BloodTestResultORM.patient_id == patient_id
                )

                if start_date:
                    stmt = stmt.where(BloodTestResultORM.test_date >= start_date)
                if end_date:
                    stmt = stmt.where(BloodTestResultORM.test_date <= end_date)
                if test_name:
                    stmt = stmt.where(BloodTestResultORM.test_name == test_name)

                stmt = stmt.order_by(BloodTestResultORM.test_date.desc())

                results_orm = session.execute(stmt).scalars().all()

                return [self._orm_to_model(r) for r in results_orm]

            except SQLAlchemyError as e:
                raise RepositoryError(f"Failed to retrieve test results: {e}")

    def get_abnormal_results(
        self,
        patient_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[BloodTestResult]:
        """Retrieve abnormal blood test results."""
        with self.SessionLocal() as session:
            try:
                stmt = select(BloodTestResultORM).where(
                    and_(
                        BloodTestResultORM.patient_id == patient_id,
                        BloodTestResultORM.flag.in_(["HIGH", "LOW"])
                    )
                )

                if start_date:
                    stmt = stmt.where(BloodTestResultORM.test_date >= start_date)
                if end_date:
                    stmt = stmt.where(BloodTestResultORM.test_date <= end_date)

                stmt = stmt.order_by(BloodTestResultORM.test_date.desc())

                results_orm = session.execute(stmt).scalars().all()

                return [self._orm_to_model(r) for r in results_orm]

            except SQLAlchemyError as e:
                raise RepositoryError(f"Failed to retrieve abnormal results: {e}")

    def get_test_history(
        self,
        patient_id: str,
        test_name: str,
        limit: Optional[int] = None
    ) -> List[BloodTestResult]:
        """Retrieve historical results for a specific test."""
        with self.SessionLocal() as session:
            try:
                stmt = select(BloodTestResultORM).where(
                    and_(
                        BloodTestResultORM.patient_id == patient_id,
                        BloodTestResultORM.test_name == test_name
                    )
                ).order_by(BloodTestResultORM.test_date.desc())

                if limit:
                    stmt = stmt.limit(limit)

                results_orm = session.execute(stmt).scalars().all()

                return [self._orm_to_model(r) for r in results_orm]

            except SQLAlchemyError as e:
                raise RepositoryError(f"Failed to retrieve test history: {e}")

    def get_unique_test_names(self, patient_id: str) -> List[str]:
        """Get list of unique test names for a patient."""
        with self.SessionLocal() as session:
            try:
                stmt = (
                    select(BloodTestResultORM.test_name)
                    .where(BloodTestResultORM.patient_id == patient_id)
                    .distinct()
                    .order_by(BloodTestResultORM.test_name)
                )

                result = session.execute(stmt).scalars().all()
                return list(result)

            except SQLAlchemyError as e:
                raise RepositoryError(f"Failed to retrieve test names: {e}")

    def delete_patient_data(self, patient_id: str) -> None:
        """Delete all data for a patient."""
        with self.SessionLocal() as session:
            try:
                # Delete patient (cascade will delete test results)
                stmt = select(PatientInfoORM).where(
                    PatientInfoORM.patient_id == patient_id
                )
                patient = session.execute(stmt).scalar_one_or_none()

                if patient:
                    session.delete(patient)
                    session.commit()

            except SQLAlchemyError as e:
                session.rollback()
                raise RepositoryError(f"Failed to delete patient data: {e}")

    def _orm_to_model(self, orm: BloodTestResultORM) -> BloodTestResult:
        """Convert ORM object to Pydantic model."""
        reference_range = ReferenceRange(
            min_value=orm.reference_range_min,
            max_value=orm.reference_range_max,
            original_text=orm.reference_range_text
        )

        return BloodTestResult(
            id=orm.id,
            patient_id=orm.patient_id,
            test_date=orm.test_date,
            test_name=orm.test_name,
            result_value=orm.result_value,
            result_raw=orm.result_raw,
            reference_range=reference_range,
            units=orm.units,
            flag=orm.flag,
            created_at=orm.created_at
        )
