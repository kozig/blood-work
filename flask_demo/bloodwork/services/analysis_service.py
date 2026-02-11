"""
Analysis service for blood work trend analysis and insights.

Provides methods for analyzing test results, detecting trends,
and grouping by category.
"""
import logging
from typing import List, Dict, Optional
from datetime import date
from collections import defaultdict

from bloodwork.models import BloodTestResult, TestCategory
from bloodwork.repositories import AbstractRepository

logger = logging.getLogger(__name__)


class TrendData:
    """Trend analysis data for a specific test."""

    def __init__(self, test_name: str, results: List[BloodTestResult]):
        """
        Initialize trend data.

        Args:
            test_name: Name of the test
            results: List of results (should be sorted by date)
        """
        self.test_name = test_name
        self.results = results

        # Calculate statistics
        self.values = [r.result_value for r in results]
        self.dates = [r.test_date for r in results]

        self.min_value = min(self.values) if self.values else None
        self.max_value = max(self.values) if self.values else None
        self.avg_value = sum(self.values) / len(self.values) if self.values else None

        # Determine trend direction
        self.trend = self._calculate_trend()

        # Count abnormal results
        self.num_abnormal = sum(1 for r in results if r.is_abnormal())

    def _calculate_trend(self) -> str:
        """
        Calculate overall trend direction.

        Returns:
            "improving", "worsening", "stable", or "insufficient_data"
        """
        if len(self.values) < 2:
            return "insufficient_data"

        # Simple linear trend based on first and last values
        first_value = self.values[0]
        last_value = self.values[-1]

        if first_value == 0:
            return "stable" if last_value == 0 else "increasing"

        change_percent = ((last_value - first_value) / first_value) * 100

        # Consider reference range if available
        if self.results[0].reference_range:
            ref_range = self.results[0].reference_range

            # If moving away from abnormal range, it's improving
            if ref_range.min_value and first_value < ref_range.min_value:
                # Was below range
                if last_value > first_value:
                    return "improving"
                elif last_value < first_value:
                    return "worsening"

            if ref_range.max_value and first_value > ref_range.max_value:
                # Was above range
                if last_value < first_value:
                    return "improving"
                elif last_value > first_value:
                    return "worsening"

        # If no clear improvement/worsening based on range, use threshold
        if abs(change_percent) < 5:
            return "stable"
        elif change_percent > 0:
            return "increasing"
        else:
            return "decreasing"

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "test_name": self.test_name,
            "num_results": len(self.results),
            "min_value": self.min_value,
            "max_value": self.max_value,
            "avg_value": self.avg_value,
            "trend": self.trend,
            "num_abnormal": self.num_abnormal,
            "latest_value": self.values[-1] if self.values else None,
            "latest_date": self.dates[-1].isoformat() if self.dates else None
        }


class AnalysisService:
    """
    Service for analyzing blood work results.

    Provides trend analysis, abnormal result detection, and grouping.
    """

    def __init__(self, repository: AbstractRepository):
        """
        Initialize analysis service.

        Args:
            repository: Repository for retrieving data
        """
        self.repository = repository

    def get_abnormal_results(
        self,
        patient_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[BloodTestResult]:
        """
        Get all abnormal (flagged) results for a patient.

        Args:
            patient_id: Patient identifier
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of abnormal BloodTestResult objects
        """
        logger.info(f"Retrieving abnormal results for patient {patient_id}")
        return self.repository.get_abnormal_results(patient_id, start_date, end_date)

    def get_test_trend(
        self,
        patient_id: str,
        test_name: str,
        limit: Optional[int] = None
    ) -> TrendData:
        """
        Get trend analysis for a specific test.

        Args:
            patient_id: Patient identifier
            test_name: Name of the test
            limit: Optional limit on number of results (most recent)

        Returns:
            TrendData object with analysis
        """
        logger.info(f"Analyzing trend for {test_name}")

        results = self.repository.get_test_history(patient_id, test_name, limit)

        if not results:
            logger.warning(f"No results found for test: {test_name}")

        # Sort by date (oldest first) for trend analysis
        results.sort(key=lambda x: x.test_date)

        return TrendData(test_name, results)

    def get_all_trends(
        self,
        patient_id: str
    ) -> Dict[str, TrendData]:
        """
        Get trend analysis for all tests for a patient.

        Args:
            patient_id: Patient identifier

        Returns:
            Dictionary mapping test names to TrendData objects
        """
        logger.info(f"Analyzing all trends for patient {patient_id}")

        # Get unique test names
        test_names = self.repository.get_unique_test_names(patient_id)

        trends = {}
        for test_name in test_names:
            try:
                trends[test_name] = self.get_test_trend(patient_id, test_name)
            except Exception as e:
                logger.error(f"Failed to analyze trend for {test_name}: {e}")

        return trends

    def group_by_category(
        self,
        results: List[BloodTestResult]
    ) -> Dict[TestCategory, List[BloodTestResult]]:
        """
        Group results by test category.

        Args:
            results: List of BloodTestResult objects

        Returns:
            Dictionary mapping TestCategory to list of results
        """
        grouped: Dict[TestCategory, List[BloodTestResult]] = defaultdict(list)

        for result in results:
            category = TestCategory.categorize_test(result.test_name)
            grouped[category].append(result)

        return dict(grouped)

    def get_summary_statistics(
        self,
        patient_id: str
    ) -> Dict:
        """
        Get summary statistics for a patient.

        Args:
            patient_id: Patient identifier

        Returns:
            Dictionary with summary statistics
        """
        logger.info(f"Calculating summary statistics for patient {patient_id}")

        # Get all results
        all_results = self.repository.get_results(patient_id)

        if not all_results:
            return {
                "total_results": 0,
                "num_abnormal": 0,
                "unique_tests": 0,
                "date_range": None
            }

        # Get abnormal results
        abnormal_results = [r for r in all_results if r.is_abnormal()]

        # Get date range
        dates = sorted([r.test_date for r in all_results])
        date_range = {
            "start": dates[0].isoformat(),
            "end": dates[-1].isoformat()
        }

        # Get unique test names
        unique_tests = len(set([r.test_name for r in all_results]))

        # Group by category
        categories = self.group_by_category(all_results)
        category_counts = {
            category.value: len(results)
            for category, results in categories.items()
        }

        return {
            "total_results": len(all_results),
            "num_abnormal": len(abnormal_results),
            "abnormal_percentage": (len(abnormal_results) / len(all_results)) * 100,
            "unique_tests": unique_tests,
            "date_range": date_range,
            "category_counts": category_counts
        }
