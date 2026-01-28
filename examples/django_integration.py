"""
Django integration example for blood work analysis.

This example shows how to integrate the bloodwork package into a Django application.
"""

# Example Django views.py
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.conf import settings

from bloodwork import ParserService, AnalysisService, VisualizationService, DatabaseRepository


# Initialize repository (typically done once in settings or middleware)
def get_repository():
    """Get database repository from Django settings."""
    # Use Django's DATABASE_URL or configure in settings.py
    connection_string = settings.DATABASES.get('bloodwork', {}).get('URL') or \
                       "postgresql://user:pass@localhost/bloodwork"
    return DatabaseRepository(connection_string)


@method_decorator(csrf_exempt, name='dispatch')
class BloodWorkUploadView(View):
    """
    Handle blood work PDF uploads.

    POST /bloodwork/upload
    Body: multipart/form-data with 'pdf' file
    """

    def post(self, request):
        """Upload and parse blood work PDF."""
        # Get uploaded file
        pdf_file = request.FILES.get('pdf')
        if not pdf_file:
            return JsonResponse({
                'success': False,
                'error': 'No PDF file provided'
            }, status=400)

        # Get patient ID from authenticated user
        patient_id = str(request.user.id)  # Assumes Django authentication

        try:
            # Initialize services
            repository = get_repository()
            service = ParserService(repository)

            # Validate and parse PDF
            ParserService.validate_pdf_file(pdf_file)
            result = service.parse_and_store(pdf_file, patient_id)

            return JsonResponse({
                'success': True,
                'num_results': result.num_results,
                'num_abnormal': result.num_abnormal,
                'abnormal_tests': result.abnormal_tests,
                'patient_info': result.patient_info.to_dict()
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class BloodWorkResultsView(View):
    """
    Get blood work results for authenticated user.

    GET /bloodwork/results
    Query params: start_date, end_date, test_name (all optional)
    """

    def get(self, request):
        """Get blood work results."""
        patient_id = str(request.user.id)

        # Get query parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        test_name = request.GET.get('test_name')

        try:
            repository = get_repository()

            # Get results
            results = repository.get_results(
                patient_id=patient_id,
                start_date=start_date,
                end_date=end_date,
                test_name=test_name
            )

            # Serialize results
            return JsonResponse({
                'success': True,
                'count': len(results),
                'results': [r.to_dict() for r in results]
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class BloodWorkAbnormalView(View):
    """
    Get abnormal blood work results.

    GET /bloodwork/abnormal
    """

    def get(self, request):
        """Get abnormal results."""
        patient_id = str(request.user.id)

        try:
            repository = get_repository()
            analysis_service = AnalysisService(repository)

            # Get abnormal results
            abnormal = analysis_service.get_abnormal_results(patient_id)

            return JsonResponse({
                'success': True,
                'count': len(abnormal),
                'results': [r.to_dict() for r in abnormal]
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class BloodWorkVisualizationView(View):
    """
    Get visualization data for frontend charts.

    GET /bloodwork/visualize/{test_name}
    """

    def get(self, request, test_name=None):
        """Get visualization data."""
        patient_id = str(request.user.id)

        try:
            repository = get_repository()
            viz_service = VisualizationService(repository)

            # Get chart data
            chart_data = viz_service.generate_chart_data(patient_id, test_name)

            return JsonResponse({
                'success': True,
                'chart_data': chart_data
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class BloodWorkDashboardView(View):
    """
    Get summary dashboard data.

    GET /bloodwork/dashboard
    """

    def get(self, request):
        """Get dashboard data."""
        patient_id = str(request.user.id)

        try:
            repository = get_repository()
            viz_service = VisualizationService(repository)

            # Get dashboard data
            dashboard = viz_service.generate_summary_dashboard(patient_id)

            return JsonResponse({
                'success': True,
                'dashboard': dashboard
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


# URL configuration (urls.py)
"""
from django.urls import path
from . import views

urlpatterns = [
    path('bloodwork/upload', views.BloodWorkUploadView.as_view(), name='bloodwork_upload'),
    path('bloodwork/results', views.BloodWorkResultsView.as_view(), name='bloodwork_results'),
    path('bloodwork/abnormal', views.BloodWorkAbnormalView.as_view(), name='bloodwork_abnormal'),
    path('bloodwork/visualize', views.BloodWorkVisualizationView.as_view(), name='bloodwork_visualize_all'),
    path('bloodwork/visualize/<str:test_name>', views.BloodWorkVisualizationView.as_view(), name='bloodwork_visualize'),
    path('bloodwork/dashboard', views.BloodWorkDashboardView.as_view(), name='bloodwork_dashboard'),
]
"""

# Settings configuration (settings.py)
"""
# Database configuration for bloodwork package
DATABASES = {
    'default': {
        # Your main Django database
        ...
    },
    'bloodwork': {
        'URL': os.environ.get('BLOODWORK_DATABASE_URL', 'postgresql://user:pass@localhost/bloodwork'),
    }
}

# Or use a single database for everything:
# The bloodwork package will use the URL you provide to DatabaseRepository
"""
