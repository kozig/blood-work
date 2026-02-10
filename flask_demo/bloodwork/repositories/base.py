"""
Abstract repository interface for storage operations.

This module defines the contract for data persistence, allowing different
storage backends (database, file, API, etc.) to be swapped out.
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from bloodwork.models import BloodTestResult, PatientInfo


class AbstractRepository(ABC):
    """
    Abstract base class for data repositories.

    Defines the interface for storing and retrieving blood work data.
    Implementations can use database, files, APIs, or other storage backends.
    """

    @abstractmethod
    def save_patient_info(self, patient: PatientInfo) -> None:
        """
        Save or update patient information.

        Args:
            patient: PatientInfo object to save

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    def get_patient_info(self, patient_id: str) -> Optional[PatientInfo]:
        """
        Retrieve patient information by ID.

        Args:
            patient_id: Patient identifier

        Returns:
            PatientInfo object if found, None otherwise

        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def save_results(self, results: List[BloodTestResult]) -> None:
        """
        Save blood test results (bulk operation).

        Args:
            results: List of BloodTestResult objects to save

        Raises:
            RepositoryError: If save operation fails
        """
        pass

    @abstractmethod
    def get_results(
        self,
        patient_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        test_name: Optional[str] = None
    ) -> List[BloodTestResult]:
        """
        Retrieve blood test results with optional filtering.

        Args:
            patient_id: Patient identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            test_name: Optional test name for filtering

        Returns:
            List of BloodTestResult objects matching criteria

        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def get_abnormal_results(
        self,
        patient_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[BloodTestResult]:
        """
        Retrieve abnormal blood test results (flagged as HIGH or LOW).

        Args:
            patient_id: Patient identifier
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            List of abnormal BloodTestResult objects

        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def get_test_history(
        self,
        patient_id: str,
        test_name: str,
        limit: Optional[int] = None
    ) -> List[BloodTestResult]:
        """
        Retrieve historical results for a specific test.

        Args:
            patient_id: Patient identifier
            test_name: Name of the test
            limit: Optional limit on number of results (most recent first)

        Returns:
            List of BloodTestResult objects for the specified test

        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def get_unique_test_names(self, patient_id: str) -> List[str]:
        """
        Get list of unique test names for a patient.

        Args:
            patient_id: Patient identifier

        Returns:
            List of unique test names

        Raises:
            RepositoryError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def delete_patient_data(self, patient_id: str) -> None:
        """
        Delete all data for a patient (patient info and test results).

        WARNING: This is a destructive operation!

        Args:
            patient_id: Patient identifier

        Raises:
            RepositoryError: If delete operation fails
        """
        pass


class RepositoryError(Exception):
    """Exception raised for repository operation errors."""
    pass
