"""
Unit tests for data export API endpoints.

Tests cover:
- Creating export requests
- Listing export request history
- Getting export request details and progress
- Downloading exports
- Cancelling export requests
- Rate limiting
- Authorization
"""

from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserType
from app.models.patient import Patient
from app.models.data_export import DataExportRequest, ExportStatus, ExportFormat
from app.utils.security import hash_password, create_access_token


def auth_headers(token: str) -> dict:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {token}"}


# ============================================
# Fixtures
# ============================================

@pytest_asyncio.fixture
async def test_patient_for_export(db_session: AsyncSession):
    """Create a test patient for export tests."""
    # Create user
    user = User(
        id=str(uuid4()),
        email=f"export_patient_{uuid4().hex[:8]}@test.com",
        password_hash=hash_password("testpassword123"),
        user_type=UserType.PATIENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    # Create patient
    patient = Patient(
        id=str(uuid4()),
        user_id=user.id,
        first_name="Export",
        last_name="TestPatient",
        date_of_birth=datetime(1990, 5, 15).date(),
    )
    db_session.add(patient)
    await db_session.commit()

    token = create_access_token({
        "sub": user.id,
        "type": user.user_type.value
    })

    return {
        "user": user,
        "patient": patient,
        "token": token,
    }


@pytest_asyncio.fixture
async def existing_export_request(db_session: AsyncSession, test_patient_for_export: dict):
    """Create an existing export request."""
    export_request = DataExportRequest(
        id=str(uuid4()),
        patient_id=test_patient_for_export["patient"].id,
        export_format=ExportFormat.JSON.value,
        status=ExportStatus.PENDING.value,
        include_profile=True,
        include_checkins=True,
        include_assessments=True,
        include_conversations=True,
        include_messages=True,
        progress_percent=0,
    )
    db_session.add(export_request)
    await db_session.commit()
    await db_session.refresh(export_request)

    return export_request


@pytest_asyncio.fixture
async def completed_export_request(db_session: AsyncSession, test_patient_for_export: dict):
    """Create a completed export request with download token."""
    download_token = f"test_token_{uuid4().hex[:16]}"

    export_request = DataExportRequest(
        id=str(uuid4()),
        patient_id=test_patient_for_export["patient"].id,
        export_format=ExportFormat.JSON.value,
        status=ExportStatus.COMPLETED.value,
        include_profile=True,
        include_checkins=True,
        include_assessments=True,
        include_conversations=False,
        include_messages=False,
        progress_percent=100,
        download_token=download_token,
        download_expires_at=datetime.utcnow() + timedelta(days=7),
        s3_key="exports/test_export.json",
        file_size_bytes=1024,
        completed_at=datetime.utcnow(),
        download_count=0,
        max_downloads=3,
    )
    db_session.add(export_request)
    await db_session.commit()
    await db_session.refresh(export_request)

    return export_request


# ============================================
# Create Export Request Tests
# ============================================

class TestCreateExportRequest:
    """Tests for creating export requests."""

    @pytest.mark.asyncio
    async def test_create_export_request_success(
        self, client: AsyncClient, test_patient_for_export: dict
    ):
        """Test successful export request creation."""
        with patch('app.api.data_export.export_service') as mock_service:
            # Mock the service methods
            mock_service.can_request_export = AsyncMock(return_value=(True, None))

            mock_export = MagicMock()
            mock_export.id = str(uuid4())
            mock_export.patient_id = test_patient_for_export["patient"].id
            mock_export.export_format = "JSON"
            mock_export.status = "PENDING"
            mock_export.include_profile = True
            mock_export.include_checkins = True
            mock_export.include_assessments = True
            mock_export.include_conversations = True
            mock_export.include_messages = True
            mock_export.date_from = None
            mock_export.date_to = None
            mock_export.progress_percent = 0
            mock_export.error_message = None
            mock_export.file_size_bytes = None
            mock_export.download_count = 0
            mock_export.max_downloads = 3
            mock_export.download_token = None
            mock_export.can_download = False
            mock_export.is_expired = True
            mock_export.is_processing = True
            mock_export.created_at = datetime.utcnow()
            mock_export.processing_started_at = None
            mock_export.completed_at = None
            mock_export.download_expires_at = None
            mock_export.last_downloaded_at = None

            mock_service.create_export_request = AsyncMock(return_value=mock_export)
            mock_service.process_export = AsyncMock(return_value=mock_export)

            response = await client.post(
                "/api/v1/data-export/request",
                json={
                    "export_format": "JSON",
                    "include_profile": True,
                    "include_checkins": True,
                    "include_assessments": True,
                    "include_conversations": True,
                    "include_messages": True,
                },
                headers=auth_headers(test_patient_for_export["token"])
            )

            assert response.status_code == 201
            data = response.json()
            assert data["export_format"] == "JSON"
            assert data["include_profile"] is True

    @pytest.mark.asyncio
    async def test_create_export_request_rate_limited(
        self, client: AsyncClient, test_patient_for_export: dict
    ):
        """Test export request rate limiting."""
        with patch('app.api.data_export.export_service') as mock_service:
            mock_service.can_request_export = AsyncMock(
                return_value=(False, "请在 23 小时后再请求导出")
            )

            response = await client.post(
                "/api/v1/data-export/request",
                json={"export_format": "JSON"},
                headers=auth_headers(test_patient_for_export["token"])
            )

            assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_create_export_all_formats(
        self, client: AsyncClient, test_patient_for_export: dict
    ):
        """Test creating exports in all supported formats."""
        formats = ["JSON", "CSV", "PDF_SUMMARY"]

        for export_format in formats:
            with patch('app.api.data_export.export_service') as mock_service:
                mock_service.can_request_export = AsyncMock(return_value=(True, None))

                mock_export = MagicMock()
                mock_export.id = str(uuid4())
                mock_export.patient_id = test_patient_for_export["patient"].id
                mock_export.export_format = export_format
                mock_export.status = "PENDING"
                mock_export.include_profile = True
                mock_export.include_checkins = True
                mock_export.include_assessments = True
                mock_export.include_conversations = True
                mock_export.include_messages = True
                mock_export.date_from = None
                mock_export.date_to = None
                mock_export.progress_percent = 0
                mock_export.error_message = None
                mock_export.file_size_bytes = None
                mock_export.download_count = 0
                mock_export.max_downloads = 3
                mock_export.download_token = None
                mock_export.can_download = False
                mock_export.is_expired = True
                mock_export.is_processing = True
                mock_export.created_at = datetime.utcnow()
                mock_export.processing_started_at = None
                mock_export.completed_at = None
                mock_export.download_expires_at = None
                mock_export.last_downloaded_at = None

                mock_service.create_export_request = AsyncMock(return_value=mock_export)
                mock_service.process_export = AsyncMock(return_value=mock_export)

                response = await client.post(
                    "/api/v1/data-export/request",
                    json={"export_format": export_format},
                    headers=auth_headers(test_patient_for_export["token"])
                )

                assert response.status_code == 201
                assert response.json()["export_format"] == export_format

    @pytest.mark.asyncio
    async def test_create_export_with_date_range(
        self, client: AsyncClient, test_patient_for_export: dict
    ):
        """Test creating export with date range filter."""
        with patch('app.api.data_export.export_service') as mock_service:
            mock_service.can_request_export = AsyncMock(return_value=(True, None))

            date_from = datetime(2024, 1, 1)
            date_to = datetime(2024, 12, 31)

            mock_export = MagicMock()
            mock_export.id = str(uuid4())
            mock_export.patient_id = test_patient_for_export["patient"].id
            mock_export.export_format = "JSON"
            mock_export.status = "PENDING"
            mock_export.include_profile = True
            mock_export.include_checkins = True
            mock_export.include_assessments = True
            mock_export.include_conversations = True
            mock_export.include_messages = True
            mock_export.date_from = date_from
            mock_export.date_to = date_to
            mock_export.progress_percent = 0
            mock_export.error_message = None
            mock_export.file_size_bytes = None
            mock_export.download_count = 0
            mock_export.max_downloads = 3
            mock_export.download_token = None
            mock_export.can_download = False
            mock_export.is_expired = True
            mock_export.is_processing = True
            mock_export.created_at = datetime.utcnow()
            mock_export.processing_started_at = None
            mock_export.completed_at = None
            mock_export.download_expires_at = None
            mock_export.last_downloaded_at = None

            mock_service.create_export_request = AsyncMock(return_value=mock_export)
            mock_service.process_export = AsyncMock(return_value=mock_export)

            response = await client.post(
                "/api/v1/data-export/request",
                json={
                    "export_format": "JSON",
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                },
                headers=auth_headers(test_patient_for_export["token"])
            )

            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_export_selective_data(
        self, client: AsyncClient, test_patient_for_export: dict
    ):
        """Test creating export with selective data inclusion."""
        with patch('app.api.data_export.export_service') as mock_service:
            mock_service.can_request_export = AsyncMock(return_value=(True, None))

            mock_export = MagicMock()
            mock_export.id = str(uuid4())
            mock_export.patient_id = test_patient_for_export["patient"].id
            mock_export.export_format = "JSON"
            mock_export.status = "PENDING"
            mock_export.include_profile = True
            mock_export.include_checkins = True
            mock_export.include_assessments = False
            mock_export.include_conversations = False
            mock_export.include_messages = False
            mock_export.date_from = None
            mock_export.date_to = None
            mock_export.progress_percent = 0
            mock_export.error_message = None
            mock_export.file_size_bytes = None
            mock_export.download_count = 0
            mock_export.max_downloads = 3
            mock_export.download_token = None
            mock_export.can_download = False
            mock_export.is_expired = True
            mock_export.is_processing = True
            mock_export.created_at = datetime.utcnow()
            mock_export.processing_started_at = None
            mock_export.completed_at = None
            mock_export.download_expires_at = None
            mock_export.last_downloaded_at = None

            mock_service.create_export_request = AsyncMock(return_value=mock_export)
            mock_service.process_export = AsyncMock(return_value=mock_export)

            response = await client.post(
                "/api/v1/data-export/request",
                json={
                    "export_format": "JSON",
                    "include_profile": True,
                    "include_checkins": True,
                    "include_assessments": False,
                    "include_conversations": False,
                    "include_messages": False,
                },
                headers=auth_headers(test_patient_for_export["token"])
            )

            assert response.status_code == 201
            data = response.json()
            assert data["include_assessments"] is False
            assert data["include_conversations"] is False
            assert data["include_messages"] is False


# ============================================
# List Export Requests Tests
# ============================================

class TestListExportRequests:
    """Tests for listing export requests."""

    @pytest.mark.asyncio
    async def test_get_export_requests(
        self, client: AsyncClient, test_patient_for_export: dict, existing_export_request
    ):
        """Test getting export request list."""
        with patch('app.api.data_export.export_service') as mock_service:
            mock_list_item = MagicMock()
            mock_list_item.id = existing_export_request.id
            mock_list_item.export_format = "JSON"
            mock_list_item.status = "PENDING"
            mock_list_item.progress_percent = 0
            mock_list_item.file_size_bytes = None
            mock_list_item.download_token = None
            mock_list_item.can_download = False
            mock_list_item.is_expired = True
            mock_list_item.created_at = datetime.utcnow()
            mock_list_item.completed_at = None

            mock_service.get_export_requests = AsyncMock(return_value=[mock_list_item])

            response = await client.get(
                "/api/v1/data-export/requests",
                headers=auth_headers(test_patient_for_export["token"])
            )

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_get_export_requests_with_limit(
        self, client: AsyncClient, test_patient_for_export: dict
    ):
        """Test getting export requests with limit parameter."""
        with patch('app.api.data_export.export_service') as mock_service:
            mock_service.get_export_requests = AsyncMock(return_value=[])

            response = await client.get(
                "/api/v1/data-export/requests?limit=5",
                headers=auth_headers(test_patient_for_export["token"])
            )

            assert response.status_code == 200
            assert isinstance(response.json(), list)


# ============================================
# Get Export Request Detail Tests
# ============================================

class TestGetExportRequestDetail:
    """Tests for getting export request details."""

    @pytest.mark.asyncio
    async def test_get_export_request_detail(
        self, client: AsyncClient, test_patient_for_export: dict, existing_export_request
    ):
        """Test getting export request details."""
        response = await client.get(
            f"/api/v1/data-export/requests/{existing_export_request.id}",
            headers=auth_headers(test_patient_for_export["token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == existing_export_request.id
        assert data["export_format"] == "JSON"

    @pytest.mark.asyncio
    async def test_get_export_request_not_found(
        self, client: AsyncClient, test_patient_for_export: dict
    ):
        """Test getting non-existent export request."""
        fake_id = str(uuid4())

        response = await client.get(
            f"/api/v1/data-export/requests/{fake_id}",
            headers=auth_headers(test_patient_for_export["token"])
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_export_request_other_patient(
        self, client: AsyncClient, db_session: AsyncSession, test_patient_for_export: dict
    ):
        """Test patient cannot access another patient's export request."""
        # Create another patient's export request
        other_user = User(
            id=str(uuid4()),
            email=f"other_{uuid4().hex[:8]}@test.com",
            password_hash=hash_password("testpassword123"),
            user_type=UserType.PATIENT,
            is_active=True,
        )
        db_session.add(other_user)
        await db_session.flush()

        other_patient = Patient(
            id=str(uuid4()),
            user_id=other_user.id,
            first_name="Other",
            last_name="Patient",
            date_of_birth=datetime(1985, 3, 20).date(),
        )
        db_session.add(other_patient)
        await db_session.flush()

        other_export = DataExportRequest(
            id=str(uuid4()),
            patient_id=other_patient.id,
            export_format=ExportFormat.JSON.value,
            status=ExportStatus.PENDING.value,
        )
        db_session.add(other_export)
        await db_session.commit()

        # Try to access with original patient token
        response = await client.get(
            f"/api/v1/data-export/requests/{other_export.id}",
            headers=auth_headers(test_patient_for_export["token"])
        )

        assert response.status_code == 404


# ============================================
# Get Export Progress Tests
# ============================================

class TestGetExportProgress:
    """Tests for getting export progress."""

    @pytest.mark.asyncio
    async def test_get_export_progress(
        self, client: AsyncClient, test_patient_for_export: dict, existing_export_request
    ):
        """Test getting export progress."""
        response = await client.get(
            f"/api/v1/data-export/requests/{existing_export_request.id}/progress",
            headers=auth_headers(test_patient_for_export["token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress_percent" in data
        assert data["id"] == existing_export_request.id

    @pytest.mark.asyncio
    async def test_get_export_progress_not_found(
        self, client: AsyncClient, test_patient_for_export: dict
    ):
        """Test getting progress for non-existent export."""
        fake_id = str(uuid4())

        response = await client.get(
            f"/api/v1/data-export/requests/{fake_id}/progress",
            headers=auth_headers(test_patient_for_export["token"])
        )

        assert response.status_code == 404


# ============================================
# Download Export Tests
# ============================================

class TestDownloadExport:
    """Tests for downloading exports."""

    @pytest.mark.asyncio
    async def test_download_export_success(
        self, client: AsyncClient, completed_export_request
    ):
        """Test successful export download."""
        with patch('app.api.data_export.export_service') as mock_service:
            mock_service.get_download_info = AsyncMock(
                return_value=(
                    completed_export_request,
                    b'{"test": "data"}',
                    "export_data.json"
                )
            )

            response = await client.get(
                f"/api/v1/data-export/download/{completed_export_request.download_token}"
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"

    @pytest.mark.asyncio
    async def test_download_export_not_found(self, client: AsyncClient):
        """Test download with invalid token."""
        with patch('app.api.data_export.export_service') as mock_service:
            mock_service.get_download_info = AsyncMock(return_value=None)

            response = await client.get(
                "/api/v1/data-export/download/invalid_token"
            )

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_csv_export(
        self, client: AsyncClient, db_session: AsyncSession, test_patient_for_export: dict
    ):
        """Test downloading CSV export (returns zip)."""
        csv_export = DataExportRequest(
            id=str(uuid4()),
            patient_id=test_patient_for_export["patient"].id,
            export_format=ExportFormat.CSV.value,
            status=ExportStatus.COMPLETED.value,
            download_token=f"csv_token_{uuid4().hex[:16]}",
            download_expires_at=datetime.utcnow() + timedelta(days=7),
            s3_key="exports/test_export.zip",
            file_size_bytes=2048,
            completed_at=datetime.utcnow(),
        )
        db_session.add(csv_export)
        await db_session.commit()

        with patch('app.api.data_export.export_service') as mock_service:
            mock_service.get_download_info = AsyncMock(
                return_value=(
                    csv_export,
                    b'PK\x03\x04...',  # ZIP file signature
                    "export_data.zip"
                )
            )

            response = await client.get(
                f"/api/v1/data-export/download/{csv_export.download_token}"
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/zip"


# ============================================
# Cancel Export Request Tests
# ============================================

class TestCancelExportRequest:
    """Tests for cancelling export requests."""

    @pytest.mark.asyncio
    async def test_cancel_pending_export(
        self, client: AsyncClient, test_patient_for_export: dict, existing_export_request
    ):
        """Test cancelling a pending export request."""
        response = await client.delete(
            f"/api/v1/data-export/requests/{existing_export_request.id}",
            headers=auth_headers(test_patient_for_export["token"])
        )

        assert response.status_code == 200
        assert "cancelled" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_processing_export(
        self, client: AsyncClient, db_session: AsyncSession, test_patient_for_export: dict
    ):
        """Test cancelling a processing export request."""
        processing_export = DataExportRequest(
            id=str(uuid4()),
            patient_id=test_patient_for_export["patient"].id,
            export_format=ExportFormat.JSON.value,
            status=ExportStatus.PROCESSING.value,
            progress_percent=50,
        )
        db_session.add(processing_export)
        await db_session.commit()

        response = await client.delete(
            f"/api/v1/data-export/requests/{processing_export.id}",
            headers=auth_headers(test_patient_for_export["token"])
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_cancel_completed_export_fails(
        self, client: AsyncClient, test_patient_for_export: dict, completed_export_request
    ):
        """Test cancelling a completed export fails."""
        response = await client.delete(
            f"/api/v1/data-export/requests/{completed_export_request.id}",
            headers=auth_headers(test_patient_for_export["token"])
        )

        assert response.status_code == 400
        assert "pending or processing" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cancel_export_not_found(
        self, client: AsyncClient, test_patient_for_export: dict
    ):
        """Test cancelling non-existent export."""
        fake_id = str(uuid4())

        response = await client.delete(
            f"/api/v1/data-export/requests/{fake_id}",
            headers=auth_headers(test_patient_for_export["token"])
        )

        assert response.status_code == 404


# ============================================
# Authorization Tests
# ============================================

class TestExportAuthorization:
    """Tests for export endpoint authorization."""

    @pytest.mark.asyncio
    async def test_unauthenticated_access_denied(self, client: AsyncClient):
        """Test unauthenticated access is denied."""
        response = await client.get("/api/v1/data-export/requests")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_doctor_cannot_access_export(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test doctors cannot use patient export endpoints."""
        # Create a doctor
        doctor_user = User(
            id=str(uuid4()),
            email=f"export_doctor_{uuid4().hex[:8]}@test.com",
            password_hash=hash_password("testpassword123"),
            user_type=UserType.DOCTOR,
            is_active=True,
        )
        db_session.add(doctor_user)
        await db_session.commit()

        doctor_token = create_access_token({
            "sub": doctor_user.id,
            "type": doctor_user.user_type.value
        })

        response = await client.get(
            "/api/v1/data-export/requests",
            headers=auth_headers(doctor_token)
        )

        # Should fail - doctors can't access patient export endpoints
        assert response.status_code in [401, 403]


# ============================================
# Edge Cases
# ============================================

class TestExportEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_export_request_with_processing_error(
        self, client: AsyncClient, test_patient_for_export: dict
    ):
        """Test handling of processing errors."""
        with patch('app.api.data_export.export_service') as mock_service:
            mock_service.can_request_export = AsyncMock(return_value=(True, None))

            mock_export = MagicMock()
            mock_export.id = str(uuid4())
            mock_export.patient_id = test_patient_for_export["patient"].id
            mock_export.export_format = "JSON"
            mock_export.status = "FAILED"
            mock_export.include_profile = True
            mock_export.include_checkins = True
            mock_export.include_assessments = True
            mock_export.include_conversations = True
            mock_export.include_messages = True
            mock_export.date_from = None
            mock_export.date_to = None
            mock_export.progress_percent = 0
            mock_export.error_message = "Processing failed"
            mock_export.file_size_bytes = None
            mock_export.download_count = 0
            mock_export.max_downloads = 3
            mock_export.download_token = None
            mock_export.can_download = False
            mock_export.is_expired = True
            mock_export.is_processing = False
            mock_export.created_at = datetime.utcnow()
            mock_export.processing_started_at = None
            mock_export.completed_at = None
            mock_export.download_expires_at = None
            mock_export.last_downloaded_at = None

            mock_service.create_export_request = AsyncMock(return_value=mock_export)
            mock_service.process_export = AsyncMock(side_effect=Exception("Processing error"))

            response = await client.post(
                "/api/v1/data-export/request",
                json={"export_format": "JSON"},
                headers=auth_headers(test_patient_for_export["token"])
            )

            # Request should still be created even if processing fails
            assert response.status_code == 201
