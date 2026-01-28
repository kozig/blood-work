"""
FastAPI integration example for blood work analysis.

This example shows how to integrate the bloodwork package into a FastAPI application.
"""

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from datetime import date as date_type
import os

from bloodwork import (
    ParserService,
    AnalysisService,
    VisualizationService,
    DatabaseRepository,
    ParseResult
)

# Initialize FastAPI app
app = FastAPI(
    title="Blood Work Analysis API",
    description="API for parsing and analyzing blood work reports",
    version="0.1.0"
)

# Database configuration
DATABASE_URL = os.getenv(
    "BLOODWORK_DATABASE_URL",
    "postgresql://bloodwork:bloodwork@localhost/bloodwork"
)


# Dependency: Get database repository
def get_repository() -> DatabaseRepository:
    """Dependency for database repository."""
    return DatabaseRepository(DATABASE_URL)


# Dependency: Get current user (placeholder - implement your auth)
async def get_current_user() -> str:
    """
    Get current authenticated user ID.

    IMPORTANT: Implement your actual authentication here!
    This is a placeholder that should be replaced with your auth system
    (JWT, OAuth, etc.)
    """
    # TODO: Implement actual authentication
    # Example with JWT:
    # from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    # credentials = Depends(HTTPBearer())
    # token = credentials.credentials
    # user_id = verify_jwt_token(token)
    # return user_id

    # For demo purposes only:
    return "demo-user-123"


# Routes

@app.post("/bloodwork/upload", response_model=dict)
async def upload_bloodwork(
    file: UploadFile = File(...),
    patient_id: str = Depends(get_current_user),
    repository: DatabaseRepository = Depends(get_repository)
):
    """
    Upload and parse blood work PDF.

    Args:
        file: PDF file upload
        patient_id: Current user ID (from authentication)
        repository: Database repository (injected)

    Returns:
        ParseResult with summary of parsed data
    """
    # Validate file type
    if not file.content_type == "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="File must be a PDF"
        )

    try:
        # Initialize parser service
        service = ParserService(repository)

        # Read file content
        pdf_content = await file.read()

        # Validate PDF
        from io import BytesIO
        pdf_file = BytesIO(pdf_content)
        ParserService.validate_pdf_file(pdf_file, max_size_mb=50)

        # Parse and store
        pdf_file.seek(0)  # Reset after validation
        result = service.parse_and_store(pdf_file, patient_id)

        return {
            "success": True,
            "num_results": result.num_results,
            "num_abnormal": result.num_abnormal,
            "abnormal_tests": result.abnormal_tests,
            "patient_info": result.patient_info.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/bloodwork/results", response_model=dict)
async def get_results(
    start_date: Optional[date_type] = Query(None),
    end_date: Optional[date_type] = Query(None),
    test_name: Optional[str] = Query(None),
    patient_id: str = Depends(get_current_user),
    repository: DatabaseRepository = Depends(get_repository)
):
    """
    Get blood work results for current user.

    Args:
        start_date: Optional start date filter
        end_date: Optional end date filter
        test_name: Optional test name filter
        patient_id: Current user ID
        repository: Database repository

    Returns:
        List of blood test results
    """
    try:
        results = repository.get_results(
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date,
            test_name=test_name
        )

        return {
            "success": True,
            "count": len(results),
            "results": [r.to_dict() for r in results]
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/bloodwork/abnormal", response_model=dict)
async def get_abnormal_results(
    patient_id: str = Depends(get_current_user),
    repository: DatabaseRepository = Depends(get_repository)
):
    """
    Get abnormal blood work results for current user.

    Args:
        patient_id: Current user ID
        repository: Database repository

    Returns:
        List of abnormal results
    """
    try:
        analysis_service = AnalysisService(repository)
        abnormal = analysis_service.get_abnormal_results(patient_id)

        return {
            "success": True,
            "count": len(abnormal),
            "results": [r.to_dict() for r in abnormal]
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/bloodwork/visualize", response_model=dict)
@app.get("/bloodwork/visualize/{test_name}", response_model=dict)
async def get_visualization(
    test_name: Optional[str] = None,
    patient_id: str = Depends(get_current_user),
    repository: DatabaseRepository = Depends(get_repository)
):
    """
    Get visualization data for charts.

    Args:
        test_name: Optional specific test name (if None, returns all tests)
        patient_id: Current user ID
        repository: Database repository

    Returns:
        Chart-ready data
    """
    try:
        viz_service = VisualizationService(repository)
        chart_data = viz_service.generate_chart_data(patient_id, test_name)

        return {
            "success": True,
            "chart_data": chart_data
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/bloodwork/dashboard", response_model=dict)
async def get_dashboard(
    patient_id: str = Depends(get_current_user),
    repository: DatabaseRepository = Depends(get_repository)
):
    """
    Get summary dashboard data.

    Args:
        patient_id: Current user ID
        repository: Database repository

    Returns:
        Dashboard summary data
    """
    try:
        viz_service = VisualizationService(repository)
        dashboard = viz_service.generate_summary_dashboard(patient_id)

        return {
            "success": True,
            "dashboard": dashboard
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/bloodwork/trends/{test_name}", response_model=dict)
async def get_test_trend(
    test_name: str,
    patient_id: str = Depends(get_current_user),
    repository: DatabaseRepository = Depends(get_repository)
):
    """
    Get trend analysis for a specific test.

    Args:
        test_name: Name of the test
        patient_id: Current user ID
        repository: Database repository

    Returns:
        Trend analysis data
    """
    try:
        analysis_service = AnalysisService(repository)
        trend_data = analysis_service.get_test_trend(patient_id, test_name)

        return {
            "success": True,
            "trend": trend_data.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "bloodwork-api"}


# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
