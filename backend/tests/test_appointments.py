"""
Unit tests for appointment management API endpoints.

Tests cover:
- Doctor appointment creation, update, and management
- Patient appointment viewing and cancellation
- Calendar views (month, week)
- Appointment statistics
- Time conflict detection
- Status transitions (confirm, complete, cancel, no-show)
"""

from datetime import date, time, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserType
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType, CancelledBy
from app.utils.security import hash_password, create_access_token


def auth_headers(token: str) -> dict:
    """Create authorization headers."""
    return {"Authorization": f"Bearer {token}"}


# ============================================
# Fixtures
# ============================================

@pytest_asyncio.fixture
async def doctor_with_patient(db_session: AsyncSession):
    """Create a doctor with an assigned patient."""
    # Create doctor user
    doctor_user = User(
        id=str(uuid4()),
        email=f"apt_doctor_{uuid4().hex[:8]}@test.com",
        password_hash=hash_password("testpassword123"),
        user_type=UserType.DOCTOR,
        is_active=True,
    )
    db_session.add(doctor_user)
    await db_session.flush()

    doctor = Doctor(
        id=str(uuid4()),
        user_id=doctor_user.id,
        first_name="Appointment",
        last_name="Doctor",
        specialty="Psychology",
    )
    db_session.add(doctor)
    await db_session.flush()

    # Create patient user
    patient_user = User(
        id=str(uuid4()),
        email=f"apt_patient_{uuid4().hex[:8]}@test.com",
        password_hash=hash_password("testpassword123"),
        user_type=UserType.PATIENT,
        is_active=True,
    )
    db_session.add(patient_user)
    await db_session.flush()

    patient = Patient(
        id=str(uuid4()),
        user_id=patient_user.id,
        first_name="Appointment",
        last_name="Patient",
        date_of_birth=date(1990, 5, 15),
        primary_doctor_id=doctor.id,
    )
    db_session.add(patient)
    await db_session.commit()

    doctor_token = create_access_token({
        "sub": doctor_user.id,
        "type": doctor_user.user_type.value
    })
    patient_token = create_access_token({
        "sub": patient_user.id,
        "type": patient_user.user_type.value
    })

    return {
        "doctor": doctor,
        "doctor_user": doctor_user,
        "doctor_token": doctor_token,
        "patient": patient,
        "patient_user": patient_user,
        "patient_token": patient_token,
    }


@pytest_asyncio.fixture
async def existing_appointment(db_session: AsyncSession, doctor_with_patient: dict):
    """Create an existing appointment for testing."""
    tomorrow = date.today() + timedelta(days=1)

    appointment = Appointment(
        id=str(uuid4()),
        doctor_id=doctor_with_patient["doctor"].id,
        patient_id=doctor_with_patient["patient"].id,
        appointment_date=tomorrow,
        start_time=time(10, 0),
        end_time=time(11, 0),
        appointment_type=AppointmentType.FOLLOW_UP.value,
        status=AppointmentStatus.PENDING.value,
        reason="Regular check-up",
    )
    db_session.add(appointment)
    await db_session.commit()
    await db_session.refresh(appointment)

    return appointment


# ============================================
# Doctor Create Appointment Tests
# ============================================

class TestDoctorCreateAppointment:
    """Tests for doctor creating appointments."""

    @pytest.mark.asyncio
    async def test_create_appointment_success(
        self, client: AsyncClient, doctor_with_patient: dict
    ):
        """Test successful appointment creation."""
        tomorrow = date.today() + timedelta(days=1)

        response = await client.post(
            "/api/v1/appointments/doctor",
            json={
                "patient_id": doctor_with_patient["patient"].id,
                "appointment_date": tomorrow.isoformat(),
                "start_time": "14:00:00",
                "end_time": "15:00:00",
                "appointment_type": "FOLLOW_UP",
                "reason": "Weekly follow-up session",
            },
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 201
        data = response.json()
        assert data["patient_id"] == doctor_with_patient["patient"].id
        assert data["doctor_id"] == doctor_with_patient["doctor"].id
        assert data["status"] == "PENDING"
        assert data["appointment_type"] == "FOLLOW_UP"
        assert data["reason"] == "Weekly follow-up session"

    @pytest.mark.asyncio
    async def test_create_appointment_patient_not_assigned(
        self, client: AsyncClient, db_session: AsyncSession, doctor_with_patient: dict
    ):
        """Test creating appointment for patient not assigned to doctor."""
        # Create another patient not assigned to this doctor
        other_patient_user = User(
            id=str(uuid4()),
            email=f"other_patient_{uuid4().hex[:8]}@test.com",
            password_hash=hash_password("testpassword123"),
            user_type=UserType.PATIENT,
            is_active=True,
        )
        db_session.add(other_patient_user)
        await db_session.flush()

        other_patient = Patient(
            id=str(uuid4()),
            user_id=other_patient_user.id,
            first_name="Other",
            last_name="Patient",
            date_of_birth=date(1985, 3, 20),
            # No primary_doctor_id - not assigned
        )
        db_session.add(other_patient)
        await db_session.commit()

        tomorrow = date.today() + timedelta(days=1)

        response = await client.post(
            "/api/v1/appointments/doctor",
            json={
                "patient_id": other_patient.id,
                "appointment_date": tomorrow.isoformat(),
                "start_time": "14:00:00",
                "end_time": "15:00:00",
                "appointment_type": "FOLLOW_UP",
            },
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 404
        assert "not found or not assigned" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_appointment_time_conflict(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test creating appointment with time conflict."""
        # Try to create overlapping appointment
        response = await client.post(
            "/api/v1/appointments/doctor",
            json={
                "patient_id": doctor_with_patient["patient"].id,
                "appointment_date": existing_appointment.appointment_date.isoformat(),
                "start_time": "10:30:00",  # Overlaps with 10:00-11:00
                "end_time": "11:30:00",
                "appointment_type": "FOLLOW_UP",
            },
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_appointment_invalid_time_range(
        self, client: AsyncClient, doctor_with_patient: dict
    ):
        """Test creating appointment with end time before start time."""
        tomorrow = date.today() + timedelta(days=1)

        response = await client.post(
            "/api/v1/appointments/doctor",
            json={
                "patient_id": doctor_with_patient["patient"].id,
                "appointment_date": tomorrow.isoformat(),
                "start_time": "15:00:00",
                "end_time": "14:00:00",  # End before start
                "appointment_type": "FOLLOW_UP",
            },
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_create_appointment_all_types(
        self, client: AsyncClient, doctor_with_patient: dict
    ):
        """Test creating appointments with all appointment types."""
        appointment_types = ["INITIAL", "FOLLOW_UP", "EMERGENCY", "CONSULTATION"]

        for i, apt_type in enumerate(appointment_types):
            future_date = date.today() + timedelta(days=i + 2)

            response = await client.post(
                "/api/v1/appointments/doctor",
                json={
                    "patient_id": doctor_with_patient["patient"].id,
                    "appointment_date": future_date.isoformat(),
                    "start_time": "09:00:00",
                    "end_time": "10:00:00",
                    "appointment_type": apt_type,
                },
                headers=auth_headers(doctor_with_patient["doctor_token"])
            )

            assert response.status_code == 201
            assert response.json()["appointment_type"] == apt_type


# ============================================
# Doctor Update Appointment Tests
# ============================================

class TestDoctorUpdateAppointment:
    """Tests for doctor updating appointments."""

    @pytest.mark.asyncio
    async def test_update_appointment_success(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test successful appointment update."""
        new_date = date.today() + timedelta(days=3)

        response = await client.put(
            f"/api/v1/appointments/doctor/{existing_appointment.id}",
            json={
                "appointment_date": new_date.isoformat(),
                "start_time": "16:00:00",
                "end_time": "17:00:00",
                "reason": "Updated reason",
            },
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["appointment_date"] == new_date.isoformat()
        assert data["reason"] == "Updated reason"

    @pytest.mark.asyncio
    async def test_update_appointment_not_found(
        self, client: AsyncClient, doctor_with_patient: dict
    ):
        """Test updating non-existent appointment."""
        fake_id = str(uuid4())

        response = await client.put(
            f"/api/v1/appointments/doctor/{fake_id}",
            json={"reason": "New reason"},
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_cancelled_appointment_fails(
        self, client: AsyncClient, db_session: AsyncSession,
        doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test updating cancelled appointment fails."""
        # Cancel the appointment first
        existing_appointment.status = AppointmentStatus.CANCELLED.value
        await db_session.commit()

        response = await client.put(
            f"/api/v1/appointments/doctor/{existing_appointment.id}",
            json={"reason": "Try to update"},
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 400
        assert "cancelled" in response.json()["detail"].lower()


# ============================================
# Doctor Appointment Status Changes
# ============================================

class TestDoctorAppointmentStatus:
    """Tests for doctor changing appointment status."""

    @pytest.mark.asyncio
    async def test_confirm_appointment(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test confirming a pending appointment."""
        response = await client.post(
            f"/api/v1/appointments/doctor/{existing_appointment.id}/confirm",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        assert response.json()["status"] == "CONFIRMED"

    @pytest.mark.asyncio
    async def test_confirm_non_pending_fails(
        self, client: AsyncClient, db_session: AsyncSession,
        doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test confirming already confirmed appointment fails."""
        existing_appointment.status = AppointmentStatus.CONFIRMED.value
        await db_session.commit()

        response = await client.post(
            f"/api/v1/appointments/doctor/{existing_appointment.id}/confirm",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_complete_appointment(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test completing an appointment."""
        response = await client.post(
            f"/api/v1/appointments/doctor/{existing_appointment.id}/complete",
            json={"completion_notes": "Session went well. Patient showing improvement."},
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["completion_notes"] == "Session went well. Patient showing improvement."
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_mark_no_show(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test marking appointment as no-show."""
        response = await client.post(
            f"/api/v1/appointments/doctor/{existing_appointment.id}/no-show",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        assert response.json()["status"] == "NO_SHOW"

    @pytest.mark.asyncio
    async def test_doctor_cancel_appointment(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test doctor cancelling an appointment."""
        response = await client.post(
            f"/api/v1/appointments/doctor/{existing_appointment.id}/cancel",
            json={"cancel_reason": "Emergency scheduling conflict"},
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"
        assert data["cancelled_by"] == "DOCTOR"
        assert data["cancel_reason"] == "Emergency scheduling conflict"
        assert data["cancelled_at"] is not None


# ============================================
# Doctor Calendar Views
# ============================================

class TestDoctorCalendarViews:
    """Tests for doctor calendar view endpoints."""

    @pytest.mark.asyncio
    async def test_get_month_calendar(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test getting monthly calendar view."""
        apt_date = existing_appointment.appointment_date

        response = await client.get(
            f"/api/v1/appointments/doctor/calendar?year={apt_date.year}&month={apt_date.month}",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["year"] == apt_date.year
        assert data["month"] == apt_date.month
        assert data["total_appointments"] >= 1
        assert len(data["days"]) >= 1

    @pytest.mark.asyncio
    async def test_get_week_view(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test getting weekly calendar view."""
        start_date = existing_appointment.appointment_date - timedelta(days=1)

        response = await client.get(
            f"/api/v1/appointments/doctor/week?start_date={start_date.isoformat()}",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["start_date"] == start_date.isoformat()
        assert data["total_appointments"] >= 1

    @pytest.mark.asyncio
    async def test_get_doctor_appointment_stats(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test getting appointment statistics."""
        response = await client.get(
            "/api/v1/appointments/doctor/stats",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "confirmed" in data
        assert "completed" in data
        assert "cancelled" in data
        assert "today_count" in data
        assert "this_week_count" in data
        assert "this_month_count" in data


# ============================================
# Doctor List and Detail Views
# ============================================

class TestDoctorAppointmentList:
    """Tests for doctor appointment list and detail views."""

    @pytest.mark.asyncio
    async def test_get_appointment_list(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test getting appointment list."""
        response = await client.get(
            "/api/v1/appointments/doctor/list",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_get_appointment_list_with_filters(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test getting appointment list with filters."""
        response = await client.get(
            "/api/v1/appointments/doctor/list?status=PENDING&appointment_type=FOLLOW_UP",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        for apt in data:
            assert apt["status"] == "PENDING"
            assert apt["appointment_type"] == "FOLLOW_UP"

    @pytest.mark.asyncio
    async def test_get_appointment_list_by_patient(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test filtering appointments by patient."""
        patient_id = doctor_with_patient["patient"].id

        response = await client.get(
            f"/api/v1/appointments/doctor/list?patient_id={patient_id}",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        for apt in data:
            assert apt["patient_id"] == patient_id

    @pytest.mark.asyncio
    async def test_get_appointment_detail(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test getting appointment detail."""
        response = await client.get(
            f"/api/v1/appointments/doctor/{existing_appointment.id}",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == existing_appointment.id
        assert "patient" in data
        assert "doctor" in data


# ============================================
# Patient Appointment Tests
# ============================================

class TestPatientAppointments:
    """Tests for patient appointment endpoints."""

    @pytest.mark.asyncio
    async def test_patient_get_appointments(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test patient getting their appointments."""
        response = await client.get(
            "/api/v1/appointments/patient/list",
            headers=auth_headers(doctor_with_patient["patient_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    @pytest.mark.asyncio
    async def test_patient_get_upcoming_appointments(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test patient getting upcoming appointments."""
        response = await client.get(
            "/api/v1/appointments/patient/upcoming",
            headers=auth_headers(doctor_with_patient["patient_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All should be pending or confirmed and in the future
        for apt in data:
            assert apt["status"] in ["PENDING", "CONFIRMED"]

    @pytest.mark.asyncio
    async def test_patient_get_appointment_detail(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test patient getting appointment detail."""
        response = await client.get(
            f"/api/v1/appointments/patient/{existing_appointment.id}",
            headers=auth_headers(doctor_with_patient["patient_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == existing_appointment.id

    @pytest.mark.asyncio
    async def test_patient_update_notes(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test patient updating their notes."""
        response = await client.put(
            f"/api/v1/appointments/patient/{existing_appointment.id}/notes",
            json={"patient_notes": "I want to discuss my sleep issues."},
            headers=auth_headers(doctor_with_patient["patient_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["patient_notes"] == "I want to discuss my sleep issues."

    @pytest.mark.asyncio
    async def test_patient_cancel_appointment(
        self, client: AsyncClient, doctor_with_patient: dict, existing_appointment: Appointment
    ):
        """Test patient cancelling their appointment."""
        response = await client.post(
            f"/api/v1/appointments/patient/{existing_appointment.id}/cancel",
            json={"cancel_reason": "Schedule conflict"},
            headers=auth_headers(doctor_with_patient["patient_token"])
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "CANCELLED"
        assert data["cancelled_by"] == "PATIENT"
        assert data["cancel_reason"] == "Schedule conflict"

    @pytest.mark.asyncio
    async def test_patient_cannot_access_other_appointment(
        self, client: AsyncClient, db_session: AsyncSession, doctor_with_patient: dict
    ):
        """Test patient cannot access another patient's appointment."""
        # Create another patient and appointment
        other_patient_user = User(
            id=str(uuid4()),
            email=f"other_{uuid4().hex[:8]}@test.com",
            password_hash=hash_password("testpassword123"),
            user_type=UserType.PATIENT,
            is_active=True,
        )
        db_session.add(other_patient_user)
        await db_session.flush()

        other_patient = Patient(
            id=str(uuid4()),
            user_id=other_patient_user.id,
            first_name="Other",
            last_name="Patient",
            date_of_birth=date(1985, 3, 20),
            primary_doctor_id=doctor_with_patient["doctor"].id,
        )
        db_session.add(other_patient)
        await db_session.flush()

        other_appointment = Appointment(
            id=str(uuid4()),
            doctor_id=doctor_with_patient["doctor"].id,
            patient_id=other_patient.id,
            appointment_date=date.today() + timedelta(days=5),
            start_time=time(14, 0),
            end_time=time(15, 0),
            appointment_type=AppointmentType.FOLLOW_UP.value,
            status=AppointmentStatus.PENDING.value,
        )
        db_session.add(other_appointment)
        await db_session.commit()

        # Try to access with original patient token
        response = await client.get(
            f"/api/v1/appointments/patient/{other_appointment.id}",
            headers=auth_headers(doctor_with_patient["patient_token"])
        )

        assert response.status_code == 404


# ============================================
# Authorization Tests
# ============================================

class TestAppointmentAuthorization:
    """Tests for appointment endpoint authorization."""

    @pytest.mark.asyncio
    async def test_patient_cannot_create_appointment(
        self, client: AsyncClient, doctor_with_patient: dict
    ):
        """Test patient cannot create appointments (doctor only)."""
        tomorrow = date.today() + timedelta(days=1)

        response = await client.post(
            "/api/v1/appointments/doctor",
            json={
                "patient_id": doctor_with_patient["patient"].id,
                "appointment_date": tomorrow.isoformat(),
                "start_time": "14:00:00",
                "end_time": "15:00:00",
                "appointment_type": "FOLLOW_UP",
            },
            headers=auth_headers(doctor_with_patient["patient_token"])
        )

        # Should fail - patients can't access doctor endpoints
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_doctor_cannot_access_patient_endpoint(
        self, client: AsyncClient, doctor_with_patient: dict
    ):
        """Test doctor cannot use patient-specific endpoints."""
        response = await client.get(
            "/api/v1/appointments/patient/upcoming",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        # Should fail - doctors can't access patient endpoints
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_unauthenticated_access_denied(self, client: AsyncClient):
        """Test unauthenticated access is denied."""
        response = await client.get("/api/v1/appointments/doctor/list")
        assert response.status_code == 401


# ============================================
# Edge Cases
# ============================================

class TestAppointmentEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_create_appointment_with_notes(
        self, client: AsyncClient, doctor_with_patient: dict
    ):
        """Test creating appointment with all optional fields."""
        tomorrow = date.today() + timedelta(days=1)

        response = await client.post(
            "/api/v1/appointments/doctor",
            json={
                "patient_id": doctor_with_patient["patient"].id,
                "appointment_date": tomorrow.isoformat(),
                "start_time": "09:00:00",
                "end_time": "09:30:00",
                "appointment_type": "INITIAL",
                "reason": "Initial consultation for anxiety symptoms",
                "notes": "Patient referred by GP. Prepare anxiety assessment.",
            },
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 201
        data = response.json()
        assert data["reason"] == "Initial consultation for anxiety symptoms"
        assert data["notes"] == "Patient referred by GP. Prepare anxiety assessment."

    @pytest.mark.asyncio
    async def test_appointment_duration_calculation(
        self, client: AsyncClient, doctor_with_patient: dict
    ):
        """Test appointment duration is calculated correctly."""
        tomorrow = date.today() + timedelta(days=1)

        response = await client.post(
            "/api/v1/appointments/doctor",
            json={
                "patient_id": doctor_with_patient["patient"].id,
                "appointment_date": tomorrow.isoformat(),
                "start_time": "10:00:00",
                "end_time": "11:30:00",  # 90 minutes
                "appointment_type": "FOLLOW_UP",
            },
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 201
        data = response.json()
        assert data["duration_minutes"] == 90

    @pytest.mark.asyncio
    async def test_pagination(
        self, client: AsyncClient, db_session: AsyncSession, doctor_with_patient: dict
    ):
        """Test appointment list pagination."""
        # Create multiple appointments
        for i in range(15):
            apt = Appointment(
                id=str(uuid4()),
                doctor_id=doctor_with_patient["doctor"].id,
                patient_id=doctor_with_patient["patient"].id,
                appointment_date=date.today() + timedelta(days=i + 1),
                start_time=time(10, 0),
                end_time=time(11, 0),
                appointment_type=AppointmentType.FOLLOW_UP.value,
                status=AppointmentStatus.PENDING.value,
            )
            db_session.add(apt)
        await db_session.commit()

        # Test limit
        response = await client.get(
            "/api/v1/appointments/doctor/list?limit=5",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )
        assert response.status_code == 200
        assert len(response.json()) == 5

        # Test offset
        response = await client.get(
            "/api/v1/appointments/doctor/list?limit=5&offset=5",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )
        assert response.status_code == 200
        assert len(response.json()) == 5

    @pytest.mark.asyncio
    async def test_date_range_filter(
        self, client: AsyncClient, db_session: AsyncSession, doctor_with_patient: dict
    ):
        """Test filtering appointments by date range."""
        # Create appointments on different dates
        base_date = date.today() + timedelta(days=10)

        for i in range(5):
            apt = Appointment(
                id=str(uuid4()),
                doctor_id=doctor_with_patient["doctor"].id,
                patient_id=doctor_with_patient["patient"].id,
                appointment_date=base_date + timedelta(days=i),
                start_time=time(10, 0),
                end_time=time(11, 0),
                appointment_type=AppointmentType.FOLLOW_UP.value,
                status=AppointmentStatus.PENDING.value,
            )
            db_session.add(apt)
        await db_session.commit()

        # Filter by date range
        start_date = base_date + timedelta(days=1)
        end_date = base_date + timedelta(days=3)

        response = await client.get(
            f"/api/v1/appointments/doctor/list?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=auth_headers(doctor_with_patient["doctor_token"])
        )

        assert response.status_code == 200
        data = response.json()
        for apt in data:
            apt_date = date.fromisoformat(apt["appointment_date"])
            assert start_date <= apt_date <= end_date
