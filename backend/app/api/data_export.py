"""
Data export API endpoints for patient data portability.

Allows patients to request and download their data.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.data_export import DataExportRequest, ExportStatus
from app.models.patient import Patient
from app.schemas.data_export import (
    ExportProgressResponse,
    ExportRequestCreate,
    ExportRequestListItem,
    ExportRequestResponse,
)
from app.services.data_export.export_service import export_service
from app.utils.deps import get_current_patient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-export", tags=["data-export"])


def export_to_response(export_request: DataExportRequest) -> ExportRequestResponse:
    """Convert model to response schema."""
    return ExportRequestResponse(
        id=export_request.id,
        patient_id=export_request.patient_id,
        export_format=export_request.export_format,
        status=export_request.status,
        include_profile=export_request.include_profile,
        include_checkins=export_request.include_checkins,
        include_assessments=export_request.include_assessments,
        include_conversations=export_request.include_conversations,
        include_messages=export_request.include_messages,
        date_from=export_request.date_from,
        date_to=export_request.date_to,
        progress_percent=export_request.progress_percent,
        error_message=export_request.error_message,
        file_size_bytes=export_request.file_size_bytes,
        download_count=export_request.download_count,
        max_downloads=export_request.max_downloads,
        download_token=export_request.download_token,
        can_download=export_request.can_download,
        is_expired=export_request.is_expired,
        is_processing=export_request.is_processing,
        created_at=export_request.created_at,
        processing_started_at=export_request.processing_started_at,
        completed_at=export_request.completed_at,
        download_expires_at=export_request.download_expires_at,
        last_downloaded_at=export_request.last_downloaded_at,
    )


def export_to_list_item(export_request: DataExportRequest) -> ExportRequestListItem:
    """Convert model to list item schema."""
    return ExportRequestListItem(
        id=export_request.id,
        export_format=export_request.export_format,
        status=export_request.status,
        progress_percent=export_request.progress_percent,
        file_size_bytes=export_request.file_size_bytes,
        download_token=export_request.download_token,
        can_download=export_request.can_download,
        is_expired=export_request.is_expired,
        created_at=export_request.created_at,
        completed_at=export_request.completed_at,
    )


@router.post(
    "/request",
    response_model=ExportRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_data_export(
    request_body: ExportRequestCreate,
    request: Request,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Request a data export.

    Patients can export their data in JSON, CSV, or PDF summary format.
    Rate limited to 1 request per 24 hours.
    """
    # Check if can request
    can_request, reason = await export_service.can_request_export(db, patient.id)
    if not can_request:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=reason)

    # Create export request
    export_request = await export_service.create_export_request(
        db=db,
        patient_id=patient.id,
        export_format=request_body.export_format.value,
        include_profile=request_body.include_profile,
        include_checkins=request_body.include_checkins,
        include_assessments=request_body.include_assessments,
        include_conversations=request_body.include_conversations,
        include_messages=request_body.include_messages,
        date_from=request_body.date_from,
        date_to=request_body.date_to,
        request_ip=request.client.host if request.client else None,
        user_agent=(request.headers.get("user-agent", "")[:500] if request.headers else None),
    )

    # Process export immediately (in production, this would be a background task)
    try:
        export_request = await export_service.process_export(db, export_request.id)
    except Exception as e:
        logger.error(f"Export processing failed: {e}")
        # Request is created but failed - user can see error in their history

    return export_to_response(export_request)


@router.get("/requests", response_model=List[ExportRequestListItem])
async def get_export_requests(
    limit: int = Query(10, ge=1, le=50),
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Get export request history.

    Returns the patient's export request history.
    """
    export_requests = await export_service.get_export_requests(db, patient.id, limit)
    return [export_to_list_item(er) for er in export_requests]


@router.get("/requests/{request_id}", response_model=ExportRequestResponse)
async def get_export_request_detail(
    request_id: str,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Get export request details.

    Returns detailed information about a specific export request.
    """
    result = await db.execute(
        select(DataExportRequest).where(
            DataExportRequest.id == request_id,
            DataExportRequest.patient_id == patient.id,
        )
    )
    export_request = result.scalar_one_or_none()

    if not export_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export request not found")

    return export_to_response(export_request)


@router.get("/requests/{request_id}/progress", response_model=ExportProgressResponse)
async def get_export_progress(
    request_id: str,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Get export progress.

    Returns progress information for a processing export.
    """
    result = await db.execute(
        select(DataExportRequest).where(
            DataExportRequest.id == request_id,
            DataExportRequest.patient_id == patient.id,
        )
    )
    export_request = result.scalar_one_or_none()

    if not export_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export request not found")

    return ExportProgressResponse(
        id=export_request.id,
        status=export_request.status,
        progress_percent=export_request.progress_percent,
        error_message=export_request.error_message,
    )


@router.get("/download/{download_token}")
async def download_export(
    download_token: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Download export file.

    Downloads the exported data file using a secure token.
    The token is included in the export request response.
    Limited to 3 downloads before the link expires.
    """
    result = await export_service.get_download_info(db, download_token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download not found, expired, or download limit reached",
        )

    export_request, file_content, file_name = result

    # Determine content type
    if export_request.export_format == "JSON":
        content_type = "application/json"
    elif export_request.export_format == "CSV":
        content_type = "application/zip"
    else:
        content_type = "application/pdf"

    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Content-Length": str(len(file_content)),
        },
    )


@router.delete("/requests/{request_id}")
async def cancel_export_request(
    request_id: str,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel or delete an export request.

    Can only cancel pending or processing requests.
    Completed requests cannot be cancelled.
    """
    result = await db.execute(
        select(DataExportRequest).where(
            DataExportRequest.id == request_id,
            DataExportRequest.patient_id == patient.id,
        )
    )
    export_request = result.scalar_one_or_none()

    if not export_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export request not found")

    if export_request.status not in [
        ExportStatus.PENDING.value,
        ExportStatus.PROCESSING.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending or processing requests",
        )

    export_request.status = ExportStatus.FAILED.value
    export_request.error_message = "Cancelled by user"
    await db.commit()

    return {"message": "Export request cancelled"}
