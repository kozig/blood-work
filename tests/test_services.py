"""
Unit tests for bloodwork.services module.
"""
import pytest
from datetime import date
from bloodwork.models import BloodTestResult, ReferenceRange, PatientInfo
from bloodwork.services import AnalysisService, TrendData
from bloodwork.repositories import AbstractRepository


class MockRepository(AbstractRepository):
    """Mock repository for testing."""

    def __init__(self):
        self.patients = {}
        self.results = []

    def save_patient_info(self, patient):
        self.patients[patient.patient_id] = patient

    def get_patient_info(self, patient_id):
        return self.patients.get(patient_id)

    def save_results(self, results):
        self.results.extend(results)

    def get_results(self, patient_id, start_date=None, end_date=None, test_name=None):
        filtered = [r for r in self.results if r.patient_id == patient_id]

        if start_date:
            filtered = [r for r in filtered if r.test_date >= start_date]
        if end_date:
            filtered = [r for r in filtered if r.test_date <= end_date]
        if test_name:
            filtered = [r for r in filtered if r.test_name == test_name]

        return filtered

    def get_abnormal_results(self, patient_id, start_date=None, end_date=None):
        filtered = [r for r in self.results if r.patient_id == patient_id and r.is_abnormal()]

        if start_date:
            filtered = [r for r in filtered if r.test_date >= start_date]
        if end_date:
            filtered = [r for r in filtered if r.test_date <= end_date]

        return filtered

    def get_test_history(self, patient_id, test_name, limit=None):
        history = [r for r in self.results if r.patient_id == patient_id and r.test_name == test_name]
        history.sort(key=lambda x: x.test_date, reverse=True)

        if limit:
            history = history[:limit]

        return history

    def get_unique_test_names(self, patient_id):
        names = set(r.test_name for r in self.results if r.patient_id == patient_id)
        return sorted(names)

    def delete_patient_data(self, patient_id):
        self.patients.pop(patient_id, None)
        self.results = [r for r in self.results if r.patient_id != patient_id]


class TestAnalysisService:
    """Tests for AnalysisService."""

    @pytest.fixture
    def mock_repo(self):
        """Create mock repository with test data."""
        repo = MockRepository()

        # Add test results
        ref_range_hdl = ReferenceRange.parse(">=1.00")
        ref_range_wbc = ReferenceRange.parse("4.0 - 11.0")

        results = [
            BloodTestResult(
                patient_id="test123",
                test_date=date(2024, 1, 15),
                test_name="HDL Cholesterol",
                result_value=0.97,
                result_raw="0.97",
                reference_range=ref_range_hdl,
                units="mmol/L",
                flag="LOW"
            ),
            BloodTestResult(
                patient_id="test123",
                test_date=date(2024, 6, 10),
                test_name="HDL Cholesterol",
                result_value=1.12,
                result_raw="1.12",
                reference_range=ref_range_hdl,
                units="mmol/L",
                flag="NORMAL"
            ),
            BloodTestResult(
                patient_id="test123",
                test_date=date(2024, 1, 15),
                test_name="WBC",
                result_value=5.9,
                result_raw="5.9",
                reference_range=ref_range_wbc,
                units="x E9/L",
                flag="NORMAL"
            ),
        ]

        repo.save_results(results)
        return repo

    def test_get_abnormal_results(self, mock_repo):
        """Test retrieving abnormal results."""
        service = AnalysisService(mock_repo)
        abnormal = service.get_abnormal_results("test123")

        assert len(abnormal) == 1
        assert abnormal[0].test_name == "HDL Cholesterol"
        assert abnormal[0].flag == "LOW"

    def test_get_test_trend(self, mock_repo):
        """Test trend analysis for a specific test."""
        service = AnalysisService(mock_repo)
        trend = service.get_test_trend("test123", "HDL Cholesterol")

        assert isinstance(trend, TrendData)
        assert trend.test_name == "HDL Cholesterol"
        assert len(trend.values) == 2
        assert trend.min_value == 0.97
        assert trend.max_value == 1.12
        assert trend.num_abnormal == 1
        assert trend.trend == "improving"  # Value increased from LOW to NORMAL

    def test_get_all_trends(self, mock_repo):
        """Test getting trends for all tests."""
        service = AnalysisService(mock_repo)
        trends = service.get_all_trends("test123")

        assert len(trends) == 2  # HDL Cholesterol and WBC
        assert "HDL Cholesterol" in trends
        assert "WBC" in trends

    def test_group_by_category(self, mock_repo):
        """Test grouping results by category."""
        service = AnalysisService(mock_repo)
        results = mock_repo.get_results("test123")
        grouped = service.group_by_category(results)

        from bloodwork.models import TestCategory
        assert TestCategory.LIPID_PANEL in grouped
        assert TestCategory.COMPLETE_BLOOD_COUNT in grouped

    def test_get_summary_statistics(self, mock_repo):
        """Test getting summary statistics."""
        service = AnalysisService(mock_repo)
        stats = service.get_summary_statistics("test123")

        assert stats["total_results"] == 3
        assert stats["num_abnormal"] == 1
        assert stats["unique_tests"] == 2
        assert "date_range" in stats


class TestTrendData:
    """Tests for TrendData class."""

    def test_trend_data_with_improvement(self):
        """Test trend calculation for improving values."""
        ref_range = ReferenceRange.parse(">=1.00")

        results = [
            BloodTestResult(
                patient_id="test123",
                test_date=date(2024, 1, 15),
                test_name="HDL Cholesterol",
                result_value=0.97,
                result_raw="0.97",
                reference_range=ref_range,
                units="mmol/L",
                flag="LOW"
            ),
            BloodTestResult(
                patient_id="test123",
                test_date=date(2024, 6, 10),
                test_name="HDL Cholesterol",
                result_value=1.12,
                result_raw="1.12",
                reference_range=ref_range,
                units="mmol/L",
                flag="NORMAL"
            ),
        ]

        trend = TrendData("HDL Cholesterol", results)

        assert trend.trend == "improving"
        assert trend.min_value == 0.97
        assert trend.max_value == 1.12
        assert trend.num_abnormal == 1

    def test_trend_data_stable(self):
        """Test trend calculation for stable values."""
        ref_range = ReferenceRange.parse("4.0 - 11.0")

        results = [
            BloodTestResult(
                patient_id="test123",
                test_date=date(2024, 1, 15),
                test_name="WBC",
                result_value=5.9,
                result_raw="5.9",
                reference_range=ref_range,
                units="x E9/L",
                flag="NORMAL"
            ),
            BloodTestResult(
                patient_id="test123",
                test_date=date(2024, 6, 10),
                test_name="WBC",
                result_value=6.1,
                result_raw="6.1",
                reference_range=ref_range,
                units="x E9/L",
                flag="NORMAL"
            ),
        ]

        trend = TrendData("WBC", results)

        assert trend.trend == "stable"  # Less than 5% change

    def test_trend_data_to_dict(self):
        """Test serialization to dictionary."""
        ref_range = ReferenceRange.parse("4.0 - 11.0")

        results = [
            BloodTestResult(
                patient_id="test123",
                test_date=date(2024, 1, 15),
                test_name="WBC",
                result_value=5.9,
                result_raw="5.9",
                reference_range=ref_range,
                units="x E9/L",
                flag="NORMAL"
            ),
        ]

        trend = TrendData("WBC", results)
        data = trend.to_dict()

        assert data["test_name"] == "WBC"
        assert data["num_results"] == 1
        assert data["latest_value"] == 5.9
        assert "latest_date" in data
