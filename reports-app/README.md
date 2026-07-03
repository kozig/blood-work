# Flask Demo Application - Blood Work Analysis

This is a standalone Flask demonstration application showing how to integrate the `bloodwork` Python package into a web application.

## Features

- **Upload PDF Reports**: Upload LifeLabs blood work PDF reports
- **Parse & Store**: Automatically extract test results and store in database
- **View Results**: Browse all test results with filtering options
- **Abnormal Detection**: Identify out-of-range test values
- **Trend Analysis**: View trends for individual tests over time
- **Dashboard**: Summary statistics and recent results

## Quick Start

### 1. Install Dependencies

```bash
cd reports-app

# Self-contained: this installs Flask AND the vendored bloodwork package
# (bundled in ./bloodwork). No `pip install -e ..` needed.
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

### 3. Upload a Blood Work Report

1. Navigate to http://localhost:5000
2. Click "Upload" in the navigation
3. Select a LifeLabs PDF report
4. Click "Upload and Parse"
5. View your results in the dashboard

## Configuration

### Database

By default, the demo uses SQLite for simplicity:

```python
DATABASE_URL = 'sqlite:///./bloodwork_demo.db'
```

For production, use PostgreSQL or MySQL:

```bash
# Set environment variable
export BLOODWORK_DATABASE_URL="postgresql://user:pass@localhost/bloodwork"

# Then run the app
python app.py
```

### File Upload Limit

Maximum file size is set to 50MB. Adjust in `app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
```

## Project Structure

```
reports-app/
├── app.py                 # Main Flask application
├── wsgi.py                # gunicorn entrypoint
├── bloodwork/            # Vendored copy of the parsing/storage/analysis library
├── sync-lib.sh           # Resync ./bloodwork from the repo-root library
├── templates/            # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Home page
│   ├── upload.html        # Upload page
│   ├── dashboard.html     # Dashboard
│   ├── error.html         # Error page
│   └── about.html         # About page
├── static/               # Static files (CSS, JS, images)
├── uploads/              # Temporary upload directory
├── requirements.txt      # Python dependencies (incl. vendored lib's deps)
└── README.md            # This file
```

## API Endpoints

### Upload PDF
```
POST /upload
Content-Type: multipart/form-data
Body: pdf file

Response:
{
    "success": true,
    "num_results": 45,
    "num_abnormal": 3,
    "abnormal_tests": ["HDL Cholesterol", "Vitamin D"],
    "message": "Successfully parsed 45 test results!"
}
```

### Get Results
```
GET /api/results?test_name=HDL&start_date=2024-01-01

Response:
{
    "success": true,
    "count": 5,
    "results": [...]
}
```

### Get Visualization Data
```
GET /api/visualize/HDL%20Cholesterol

Response:
{
    "success": true,
    "chart_data": {
        "labels": ["2024-01-15", "2024-06-10"],
        "datasets": [...]
    }
}
```

## Pages

- **/** - Home page with quick links
- **/upload** - Upload PDF reports
- **/dashboard** - Summary dashboard with statistics
- **/results** - View all test results
- **/abnormal** - View abnormal test results
- **/test/{test_name}** - View trend for specific test
- **/about** - About this demo

## Authentication

This demo uses simple session-based "authentication" for demonstration purposes:

```python
def get_current_user_id():
    if 'user_id' not in session:
        session['user_id'] = 'demo-user'
    return session['user_id']
```

**For production, implement proper authentication:**
- JWT tokens
- OAuth2
- Flask-Login
- Flask-Security
- Or your existing auth system

## Production Deployment

This is a **demo application**. For production:

### 1. Use Production Database

```bash
# PostgreSQL
export BLOODWORK_DATABASE_URL="postgresql://user:pass@localhost:5432/bloodwork"

# Or MySQL
export BLOODWORK_DATABASE_URL="mysql+pymysql://user:pass@localhost:3306/bloodwork"
```

### 2. Add Proper Authentication

Replace session-based auth with:
- JWT tokens
- OAuth2 (Google, Microsoft, etc.)
- SAML for enterprise
- Your existing auth system

### 3. Enable HTTPS

Use a reverse proxy (nginx, Apache) with SSL/TLS:

```nginx
server {
    listen 443 ssl;
    server_name bloodwork.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

### 4. Use Production WSGI Server

Don't use Flask's development server. Use gunicorn or uWSGI:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 5. Environment Variables

Create a `.env` file or set environment variables:

```bash
export SECRET_KEY="your-secret-key-here"
export BLOODWORK_DATABASE_URL="postgresql://..."
export FLASK_ENV="production"
```

### 6. Security Headers

Add security headers in Flask:

```python
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

### 7. HIPAA Compliance

If handling real patient data:
- Implement audit logging
- Add data encryption at rest
- Set up proper backups
- Add data retention policies
- Implement role-based access control (RBAC)
- Add PHI redaction in logs
- Set up monitoring and alerts

## Troubleshooting

### Database Issues

```bash
# Reset database (WARNING: Deletes all data)
rm bloodwork_demo.db
python app.py  # Will recreate tables
```

### Upload Issues

```bash
# Check upload directory exists and is writable
mkdir -p uploads
chmod 755 uploads
```

### PDF Parsing Errors

- Ensure PDF is from LifeLabs
- Check file is not encrypted
- Verify file size is under 50MB
- Check pdfplumber is installed: `pip install pdfplumber`

## Development

### Run in Debug Mode

```python
# In app.py, the app.run() already has debug=True
python app.py
```

### Add New Features

1. Add routes in `app.py`
2. Create templates in `templates/`
3. Add static assets in `static/`
4. Use the bloodwork package services:
   - `ParserService` - PDF parsing
   - `AnalysisService` - Trend analysis
   - `VisualizationService` - Chart data

## Support

- Main Package Documentation: See parent directory README
- Issues: Report issues on GitHub
- Questions: Create a discussion on GitHub

## License

MIT License - See parent directory for details
