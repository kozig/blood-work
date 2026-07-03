"""
Visualization service for generating chart-ready data.

Generates JSON-serializable data structures suitable for
client-side chart libraries (Chart.js, D3, Plotly, etc.).
"""
import logging
from typing import List, Dict, Optional
from datetime import date

from bloodwork.models import BloodTestResult
from bloodwork.repositories import AbstractRepository
from bloodwork.services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class VisualizationService:
    """
    Service for generating visualization data.

    Produces JSON-serializable data structures for frontend rendering.
    Does NOT generate actual charts - that's handled by the frontend.
    """

    def __init__(self, repository: AbstractRepository):
        """
        Initialize visualization service.

        Args:
            repository: Repository for retrieving data
        """
        self.repository = repository
        self.analysis_service = AnalysisService(repository)

    def generate_chart_data(
        self,
        patient_id: str,
        test_name: Optional[str] = None
    ) -> Dict:
        """
        Generate chart data for a specific test or all tests.

        Args:
            patient_id: Patient identifier
            test_name: Optional specific test name (if None, returns all tests)

        Returns:
            Dictionary with chart-ready data
        """
        if test_name:
            return self._generate_single_test_chart(patient_id, test_name)
        else:
            return self._generate_all_tests_charts(patient_id)

    def _generate_single_test_chart(
        self,
        patient_id: str,
        test_name: str
    ) -> Dict:
        """Generate chart data for a single test."""
        # Get test history
        results = self.repository.get_test_history(patient_id, test_name)

        if not results:
            return {
                "test_name": test_name,
                "data_points": [],
                "message": "No data available"
            }

        # Sort by date
        results.sort(key=lambda x: x.test_date)

        # Get reference range from first result
        ref_range = results[0].reference_range

        # Build data points
        data_points = []
        for result in results:
            data_points.append({
                "date": result.test_date.isoformat(),
                "value": result.result_value,
                "flag": result.flag,
                "is_abnormal": result.is_abnormal()
            })

        # Get trend analysis
        trend_data = self.analysis_service.get_test_trend(patient_id, test_name)

        return {
            "test_name": test_name,
            "units": results[0].units,
            "reference_range": {
                "min": ref_range.min_value,
                "max": ref_range.max_value,
                "text": ref_range.original_text
            },
            "data_points": data_points,
            "trend": trend_data.trend,
            "statistics": {
                "min": trend_data.min_value,
                "max": trend_data.max_value,
                "avg": trend_data.avg_value,
                "num_abnormal": trend_data.num_abnormal
            }
        }

    def _generate_all_tests_charts(
        self,
        patient_id: str
    ) -> Dict:
        """Generate chart data for all tests."""
        # Get all unique test names
        test_names = self.repository.get_unique_test_names(patient_id)

        charts = {}
        for test_name in test_names:
            try:
                charts[test_name] = self._generate_single_test_chart(
                    patient_id, test_name
                )
            except Exception as e:
                logger.error(f"Failed to generate chart for {test_name}: {e}")

        return {
            "charts": charts,
            "test_count": len(charts)
        }

    def generate_summary_dashboard(
        self,
        patient_id: str
    ) -> Dict:
        """
        Generate summary dashboard data.

        Args:
            patient_id: Patient identifier

        Returns:
            Dictionary with dashboard data (statistics, abnormal tests, trends)
        """
        logger.info(f"Generating dashboard for patient {patient_id}")

        # Get summary statistics
        stats = self.analysis_service.get_summary_statistics(patient_id)

        # Get abnormal results
        abnormal_results = self.analysis_service.get_abnormal_results(patient_id)

        # Group abnormal by test name
        abnormal_by_test: Dict[str, List[Dict]] = {}
        for result in abnormal_results:
            if result.test_name not in abnormal_by_test:
                abnormal_by_test[result.test_name] = []

            abnormal_by_test[result.test_name].append({
                "date": result.test_date.isoformat(),
                "value": result.result_value,
                "flag": result.flag,
                "reference_range": result.reference_range.original_text
            })

        # Get recent results (last 10 unique tests)
        all_results = self.repository.get_results(patient_id)
        all_results.sort(key=lambda x: x.test_date, reverse=True)

        recent_tests = []
        seen_tests = set()
        for result in all_results:
            if result.test_name not in seen_tests:
                recent_tests.append({
                    "test_name": result.test_name,
                    "date": result.test_date.isoformat(),
                    "value": result.result_value,
                    "units": result.units,
                    "flag": result.flag,
                    "is_abnormal": result.is_abnormal()
                })
                seen_tests.add(result.test_name)

                if len(recent_tests) >= 10:
                    break

        return {
            "statistics": stats,
            "abnormal_tests": abnormal_by_test,
            "recent_tests": recent_tests
        }

    def export_to_chartjs_format(
        self,
        patient_id: str,
        test_name: str
    ) -> Dict:
        """
        Export data in Chart.js compatible format.

        Args:
            patient_id: Patient identifier
            test_name: Test name

        Returns:
            Dictionary in Chart.js dataset format
        """
        chart_data = self._generate_single_test_chart(patient_id, test_name)

        if not chart_data.get("data_points"):
            return {}

        # Extract data for Chart.js
        labels = [dp["date"] for dp in chart_data["data_points"]]
        values = [dp["value"] for dp in chart_data["data_points"]]
        colors = [
            "rgb(255, 99, 132)" if dp["is_abnormal"] else "rgb(75, 192, 192)"
            for dp in chart_data["data_points"]
        ]

        # Reference range data
        ref_range = chart_data["reference_range"]
        min_line = [ref_range["min"]] * len(labels) if ref_range["min"] else None
        max_line = [ref_range["max"]] * len(labels) if ref_range["max"] else None

        datasets = [
            {
                "label": test_name,
                "data": values,
                "backgroundColor": colors,
                "borderColor": "rgb(75, 192, 192)",
                "borderWidth": 2,
                "fill": False
            }
        ]

        # Add reference range lines
        if min_line:
            datasets.append({
                "label": "Min Reference",
                "data": min_line,
                "borderColor": "rgb(201, 203, 207)",
                "borderWidth": 1,
                "borderDash": [5, 5],
                "fill": False,
                "pointRadius": 0
            })

        if max_line:
            datasets.append({
                "label": "Max Reference",
                "data": max_line,
                "borderColor": "rgb(201, 203, 207)",
                "borderWidth": 1,
                "borderDash": [5, 5],
                "fill": False,
                "pointRadius": 0
            })

        return {
            "labels": labels,
            "datasets": datasets
        }
