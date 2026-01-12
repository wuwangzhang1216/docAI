"""
Reports API endpoints for generating and retrieving clinical reports.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.utils.deps import get_current_user, require_user_type
from app.models.user import UserType
from app.schemas.reports import (
    ReportGenerateRequest,
    ReportResponse,
    ReportListResponse,
    ReportListItem,
)
from app.services.reports.pre_visit_report import pre_visit_report_service


router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "/pre-visit-summary/{summary_id}/pdf",
    response_model=ReportResponse,
    summary="Generate Pre-Visit Summary PDF",
    description="Generate a PDF report for a pre-visit summary. Only accessible by doctors."
)
async def generate_pre_visit_report(
    summary_id: str,
    request: ReportGenerateRequest = ReportGenerateRequest(),
    current_user: User = Depends(require_user_type(UserType.DOCTOR)),
    db: AsyncSession = Depends(get_db)
) -> ReportResponse:
    """
    Generate a Pre-Visit Clinical Summary PDF report.

    This endpoint generates a PDF containing:
    - Patient information
    - Chief complaint
    - Mental health assessment results
    - Risk alerts
    - Recent check-in trends
    - Conversation summary

    Only doctors assigned to the patient can generate reports.
    """
    try:
        result = await pre_visit_report_service.generate_report(
            db=db,
            summary_id=summary_id,
            generated_by=current_user,
            options=request
        )
        return ReportResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get Report Details",
    description="Get report details and a fresh download URL."
)
async def get_report(
    report_id: str,
    current_user: User = Depends(require_user_type(UserType.DOCTOR)),
    db: AsyncSession = Depends(get_db)
) -> ReportResponse:
    """
    Get report details and a fresh presigned download URL.

    The download URL expires after 1 hour. Use this endpoint to get
    a fresh URL if the previous one has expired.
    """
    try:
        result = await pre_visit_report_service.get_report(
            db=db,
            report_id=report_id,
            user=current_user
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )

        return ReportResponse(**result)

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}"
        )


@router.get(
    "",
    response_model=ReportListResponse,
    summary="List Reports",
    description="List generated reports with optional filtering."
)
async def list_reports(
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(require_user_type(UserType.DOCTOR)),
    db: AsyncSession = Depends(get_db)
) -> ReportListResponse:
    """
    List generated reports.

    Returns a paginated list of reports. If patient_id is provided,
    only reports for that patient are returned. Otherwise, returns
    reports for all patients assigned to the doctor.
    """
    try:
        result = await pre_visit_report_service.list_reports(
            db=db,
            user=current_user,
            patient_id=patient_id,
            limit=limit,
            offset=offset
        )

        return ReportListResponse(
            reports=[ReportListItem(**r) for r in result['reports']],
            total=result['total']
        )

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}"
        )
