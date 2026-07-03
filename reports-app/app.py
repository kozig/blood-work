"""
Flask Demo Application for Blood Work Analysis

This is a standalone demo application showing how to integrate the bloodwork package.
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta, timezone
import secrets

# Import bloodwork package
from bloodwork import (
    ParserService,
    AnalysisService,
    VisualizationService,
    DatabaseRepository
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))
app.config['PREFFERED_URL_SCHEME'] = 'https'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Database configuration
DATABASE_URL = os.environ.get(
    'BLOODWORK_DATABASE_URL',
    'sqlite:///./bloodwork_demo.db'  # SQLite for demo
)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- TEMPORARY: auto-wipe stale-session data (demo hygiene) ---------------
# Idle timeout (minutes) after which a visitor's uploaded data is deleted so
# PHI does not linger between visits. Remove this block, SESSION_STALE_MINUTES,
# and the clear_stale_session_data() hook below once real auth/retention exists.
SESSION_STALE_MINUTES = int(os.environ.get('SESSION_STALE_MINUTES', '30'))

# Initialize repository (singleton pattern)
repository = None


def get_repository():
    """Get or create database repository."""
    global repository
    if repository is None:
        repository = DatabaseRepository(DATABASE_URL)
    return repository


def get_current_user_id():
    """Get current user ID from session (demo uses session, not real auth)."""
    if 'user_id' not in session:
        # For demo purposes, create a demo user
        session['user_id'] = 'demo-user'
    return session['user_id']


# --- TEMPORARY: auto-wipe stale-session data (demo hygiene) ---------------
@app.before_request
def clear_stale_session_data():
    """TEMPORARY: wipe a visitor's data once their session goes stale.

    On every request, compare now against the last-seen timestamp stored in
    the session. If the gap exceeds SESSION_STALE_MINUTES, delete this
    visitor's data and reset the session so the next visit starts clean.
    Remove this hook once real auth/retention exists.
    """
    # Don't touch the DB for static assets.
    if request.endpoint == 'static':
        return

    now = datetime.now(timezone.utc)
    last_seen_raw = session.get('last_seen')
    if last_seen_raw:
        try:
            last_seen = datetime.fromisoformat(last_seen_raw)
        except (ValueError, TypeError):
            last_seen = now
        if now - last_seen > timedelta(minutes=SESSION_STALE_MINUTES):
            user_id = session.get('user_id')
            if user_id:
                try:
                    get_repository().delete_patient_data(user_id)
                except Exception:
                    pass  # best-effort cleanup; never block the request
            session.clear()

    session['last_seen'] = now.isoformat()


# Routes

@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload blood work PDF."""
    if request.method == 'GET':
        return render_template('upload.html')

    # Handle POST - file upload
    if 'pdf' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not file.filename.endswith('.pdf'):
        return jsonify({'success': False, 'error': 'File must be a PDF'}), 400

    try:
        # Get user ID
        user_id = get_current_user_id()

        # Initialize services
        repo = get_repository()
        parser_service = ParserService(repo)

        # Validate PDF
        ParserService.validate_pdf_file(file, max_size_mb=50)

        # Parse and store
        file.seek(0)
        result = parser_service.parse_and_store(file, user_id)

        return jsonify({
            'success': True,
            'num_results': result.num_results,
            'num_abnormal': result.num_abnormal,
            'abnormal_tests': result.abnormal_tests,
            'message': f'Successfully parsed {result.num_results} test results!'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/results')
def results():
    """View all blood test results."""
    try:
        user_id = get_current_user_id()
        repo = get_repository()

        # Get all results
        all_results = repo.get_results(user_id)

        return render_template('results.html', results=all_results)

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/api/results')
def api_results():
    """API endpoint for results."""
    try:
        user_id = get_current_user_id()
        repo = get_repository()

        # Get query parameters
        test_name = request.args.get('test_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Convert dates if provided
        from datetime import date
        if start_date:
            start_date = date.fromisoformat(start_date)
        if end_date:
            end_date = date.fromisoformat(end_date)

        # Get results
        results = repo.get_results(
            user_id,
            start_date=start_date,
            end_date=end_date,
            test_name=test_name
        )

        return jsonify({
            'success': True,
            'count': len(results),
            'results': [r.to_dict() for r in results]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/abnormal')
def abnormal():
    """View abnormal test results."""
    try:
        user_id = get_current_user_id()
        repo = get_repository()
        analysis_service = AnalysisService(repo)

        # Get abnormal results
        abnormal_results = analysis_service.get_abnormal_results(user_id)

        # Convert to dict
        abnormal_data = [r.to_dict() for r in abnormal_results]

        return render_template('abnormal.html', abnormal=abnormal_data)

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/dashboard')
def dashboard():
    """Main dashboard with summary and visualizations."""
    try:
        user_id = get_current_user_id()
        repo = get_repository()
        viz_service = VisualizationService(repo)

        # Get dashboard data
        dashboard_data = viz_service.generate_summary_dashboard(user_id)

        # Get actual test names grouped by category, with chart data pre-generated
        from bloodwork.models import TestCategory
        from collections import OrderedDict
        import json
        test_names = repo.get_unique_test_names(user_id)
        categories = OrderedDict()
        all_chart_data = {}
        for name in test_names:
            cat = TestCategory.categorize_test(name)
            categories.setdefault(cat.value, []).append(name)
            try:
                all_chart_data[name] = viz_service.export_to_chartjs_format(user_id, name)
            except Exception:
                all_chart_data[name] = {}

        return render_template(
            'dashboard.html',
            dashboard=dashboard_data,
            test_categories=categories,
            chart_data_json=json.dumps(all_chart_data)
        )

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/api/visualize/<test_name>')
def api_visualize(test_name):
    """API endpoint for visualization data."""
    try:
        user_id = get_current_user_id()
        repo = get_repository()
        viz_service = VisualizationService(repo)

        # Get chart data in Chart.js format
        chart_data = viz_service.export_to_chartjs_format(user_id, test_name)

        return jsonify({
            'success': True,
            'chart_data': chart_data
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/test/<test_name>')
def test_detail(test_name):
    """View detailed trend for a specific test."""
    try:
        user_id = get_current_user_id()
        repo = get_repository()
        analysis_service = AnalysisService(repo)

        # Get trend data
        trend = analysis_service.get_test_trend(user_id, test_name)

        return render_template('test_detail.html', test_name=test_name, trend=trend)

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/changes')
def changes():
    """View in/out-of-range status transitions across draws."""
    try:
        user_id = get_current_user_id()
        repo = get_repository()
        analysis_service = AnalysisService(repo)

        transitions = [t.to_dict() for t in analysis_service.get_status_transitions(user_id)]
        latest_draw_date = transitions[0]['to_date'] if transitions else None
        since_last = [t for t in transitions if t['to_date'] == latest_draw_date]

        return render_template(
            'changes.html',
            transitions=transitions,
            since_last=since_last,
            latest_draw_date=latest_draw_date,
        )

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/about')
def about():
    """About page."""
    return render_template('about.html')

@app.route('/reset', methods=['POST'])
def reset_data():
  """Reset all blood work data for current user."""
  try:
      user_id = get_current_user_id()
      repo = get_repository()
      repo.delete_patient_data(user_id)
      return jsonify({'success': True, 'message': 'All data has been reset.'})
  except Exception as e:
      return jsonify({'success': False, 'error': str(e)}),400

# Error handlers

@app.errorhandler(404)
def not_found(e):
    """404 error handler."""
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def server_error(e):
    """500 error handler."""
    return render_template('error.html', error='Internal server error'), 500


# Run app
if __name__ == '__main__':
    print("=" * 60)
    print("Blood Work Analysis - Flask Demo")
    print("=" * 60)
    print(f"Database: {DATABASE_URL}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print("=" * 60)
    print("\nStarting server at http://localhost:5000")
    print("=" * 60)

    app.run(debug=False, host='0.0.0.0', port=5000)
