"""
Tests for messaging API endpoints.

Covers:
- Thread management (list, get, create)
- Message sending and receiving
- Read receipts
- Unread counts
- Access control between doctors and patients
"""

import pytest
import pytest_asyncio
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import auth_headers
from app.models.messaging import DoctorPatientThread, DirectMessage, MessageType


class TestThreadManagement:
    """Test thread management endpoints."""

    @pytest.mark.asyncio
    async def test_get_threads_patient_empty(
        self, client: AsyncClient, patient_token, test_patient
    ):
        """Test patient getting threads when none exist."""
        response = await client.get(
            "/api/v1/messaging/threads",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_threads_doctor_empty(
        self, client: AsyncClient, doctor_token, test_doctor
    ):
        """Test doctor getting threads when none exist."""
        response = await client.get(
            "/api/v1/messaging/threads",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_doctor_start_thread_with_connected_patient(
        self, client: AsyncClient, doctor_token, connected_patient_doctor
    ):
        """Test doctor creating a thread with connected patient."""
        patient, doctor = connected_patient_doctor

        response = await client.post(
            f"/api/v1/messaging/doctor/patients/{patient.id}/thread",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["other_party_id"] == patient.id
        assert data["other_party_type"] == "PATIENT"
        assert data["can_send_message"] is True

    @pytest.mark.asyncio
    async def test_doctor_start_thread_with_unconnected_patient(
        self, client: AsyncClient, doctor_token, test_patient
    ):
        """Test doctor cannot create thread with unconnected patient."""
        response = await client.post(
            f"/api/v1/messaging/doctor/patients/{test_patient.id}/thread",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_threads_after_creation(
        self, client: AsyncClient, doctor_token, connected_patient_doctor, db_session
    ):
        """Test getting threads after creating one."""
        patient, doctor = connected_patient_doctor

        # Create thread
        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        db_session.add(thread)
        await db_session.commit()

        # Get threads
        response = await client.get(
            "/api/v1/messaging/threads",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["other_party_name"] == "Test Patient"


class TestMessageSending:
    """Test message sending functionality."""

    @pytest_asyncio.fixture
    async def thread_with_connection(
        self, db_session, connected_patient_doctor
    ) -> str:
        """Create a thread between connected doctor and patient. Returns thread ID."""
        patient, doctor = connected_patient_doctor

        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        db_session.add(thread)
        await db_session.commit()
        await db_session.refresh(thread)
        return thread.id

    @pytest.mark.asyncio
    async def test_doctor_send_text_message(
        self, client: AsyncClient, doctor_token, thread_with_connection
    ):
        """Test doctor sending a text message."""
        thread_id = thread_with_connection  # fixture now returns thread ID directly
        response = await client.post(
            f"/api/v1/messaging/threads/{thread_id}/messages",
            headers=auth_headers(doctor_token),
            json={
                "content": "Hello, how are you feeling today?",
                "message_type": "TEXT"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello, how are you feeling today?"
        assert data["sender_type"] == "DOCTOR"
        assert data["message_type"] == "TEXT"
        assert data["is_read"] is False

    @pytest.mark.asyncio
    async def test_patient_send_text_message(
        self, client: AsyncClient, patient_token, thread_with_connection
    ):
        """Test patient sending a text message."""
        thread_id = thread_with_connection  # fixture now returns thread ID directly
        response = await client.post(
            f"/api/v1/messaging/threads/{thread_id}/messages",
            headers=auth_headers(patient_token),
            json={
                "content": "I'm doing better, thank you!",
                "message_type": "TEXT"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sender_type"] == "PATIENT"
        assert data["content"] == "I'm doing better, thank you!"

    @pytest.mark.asyncio
    async def test_send_empty_text_message_fails(
        self, client: AsyncClient, doctor_token, thread_with_connection
    ):
        """Test sending empty text message fails."""
        thread_id = thread_with_connection  # fixture now returns thread ID directly
        response = await client.post(
            f"/api/v1/messaging/threads/{thread_id}/messages",
            headers=auth_headers(doctor_token),
            json={
                "content": "",
                "message_type": "TEXT"
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_send_message_to_nonexistent_thread(
        self, client: AsyncClient, doctor_token
    ):
        """Test sending message to non-existent thread."""
        response = await client.post(
            "/api/v1/messaging/threads/nonexistent-thread-id/messages",
            headers=auth_headers(doctor_token),
            json={
                "content": "Test message",
                "message_type": "TEXT"
            }
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unconnected_user_cannot_send_message(
        self, client: AsyncClient, db_session, doctor_token, test_patient, test_doctor
    ):
        """Test user not in thread cannot send message."""
        # Create a thread but don't connect patient to doctor
        thread = DoctorPatientThread(
            doctor_id=test_doctor.id,
            patient_id=test_patient.id
        )
        db_session.add(thread)
        await db_session.commit()

        # Try to send message (patient not connected)
        response = await client.post(
            f"/api/v1/messaging/threads/{thread.id}/messages",
            headers=auth_headers(doctor_token),
            json={
                "content": "Test message",
                "message_type": "TEXT"
            }
        )

        assert response.status_code == 403


class TestReadReceipts:
    """Test message read receipt functionality."""

    @pytest.fixture
    async def thread_with_messages(
        self, db_session, connected_patient_doctor
    ) -> tuple[DoctorPatientThread, list[DirectMessage]]:
        """Create a thread with some messages."""
        patient, doctor = connected_patient_doctor

        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id,
            doctor_unread_count=2,
            patient_unread_count=1
        )
        db_session.add(thread)
        await db_session.flush()

        messages = [
            DirectMessage(
                thread_id=thread.id,
                sender_type="DOCTOR",
                sender_id=doctor.id,
                content="How are you?",
                message_type=MessageType.TEXT,
                is_read=False
            ),
            DirectMessage(
                thread_id=thread.id,
                sender_type="PATIENT",
                sender_id=patient.id,
                content="I'm good",
                message_type=MessageType.TEXT,
                is_read=False
            ),
            DirectMessage(
                thread_id=thread.id,
                sender_type="PATIENT",
                sender_id=patient.id,
                content="Thanks for asking",
                message_type=MessageType.TEXT,
                is_read=False
            ),
        ]

        for msg in messages:
            db_session.add(msg)

        await db_session.commit()
        return thread, messages

    @pytest.mark.asyncio
    async def test_patient_mark_thread_read(
        self, client: AsyncClient, patient_token, thread_with_messages
    ):
        """Test patient marking thread as read."""
        thread, messages = thread_with_messages

        response = await client.post(
            f"/api/v1/messaging/threads/{thread.id}/read",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_doctor_mark_thread_read(
        self, client: AsyncClient, doctor_token, thread_with_messages
    ):
        """Test doctor marking thread as read."""
        thread, messages = thread_with_messages

        response = await client.post(
            f"/api/v1/messaging/threads/{thread.id}/read",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200


class TestUnreadCounts:
    """Test unread message count functionality."""

    @pytest.mark.asyncio
    async def test_get_unread_count_empty(
        self, client: AsyncClient, patient_token, test_patient
    ):
        """Test getting unread count when no threads exist."""
        response = await client.get(
            "/api/v1/messaging/unread",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_unread"] == 0
        assert data["threads"] == []

    @pytest.mark.asyncio
    async def test_get_unread_count_with_messages(
        self, client: AsyncClient, patient_token, db_session, connected_patient_doctor
    ):
        """Test getting unread count with unread messages."""
        patient, doctor = connected_patient_doctor

        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id,
            patient_unread_count=3
        )
        db_session.add(thread)
        await db_session.commit()

        response = await client.get(
            "/api/v1/messaging/unread",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_unread"] == 3
        assert len(data["threads"]) == 1
        assert data["threads"][0]["unread_count"] == 3


class TestThreadDetail:
    """Test thread detail and message retrieval."""

    @pytest.fixture
    async def thread_with_messages(
        self, db_session, connected_patient_doctor
    ) -> DoctorPatientThread:
        """Create a thread with messages for detail tests."""
        patient, doctor = connected_patient_doctor

        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id,
            last_message_at=datetime.utcnow()
        )
        db_session.add(thread)
        await db_session.flush()

        # Add messages
        for i in range(5):
            msg = DirectMessage(
                thread_id=thread.id,
                sender_type="DOCTOR" if i % 2 == 0 else "PATIENT",
                sender_id=doctor.id if i % 2 == 0 else patient.id,
                content=f"Message {i + 1}",
                message_type=MessageType.TEXT
            )
            db_session.add(msg)

        await db_session.commit()
        await db_session.refresh(thread)
        return thread

    @pytest.mark.asyncio
    async def test_get_thread_detail(
        self, client: AsyncClient, doctor_token, thread_with_messages
    ):
        """Test getting thread detail with messages."""
        response = await client.get(
            f"/api/v1/messaging/threads/{thread_with_messages.id}",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == thread_with_messages.id
        assert len(data["messages"]) == 5
        assert data["other_party_type"] == "PATIENT"

    @pytest.mark.asyncio
    async def test_get_thread_detail_unauthorized(
        self, client: AsyncClient, patient_token, db_session, test_doctor
    ):
        """Test unauthorized user cannot get thread detail."""
        # Create a thread that patient is not part of
        from app.models.patient import Patient

        # Create another patient
        other_patient = Patient(
            user_id="other-user-id",
            first_name="Other",
            last_name="Patient"
        )
        db_session.add(other_patient)
        await db_session.flush()

        thread = DoctorPatientThread(
            doctor_id=test_doctor.id,
            patient_id=other_patient.id
        )
        db_session.add(thread)
        await db_session.commit()

        # Original patient tries to access
        response = await client.get(
            f"/api/v1/messaging/threads/{thread.id}",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_thread_with_pagination(
        self, client: AsyncClient, doctor_token, thread_with_messages
    ):
        """Test thread detail with message limit."""
        response = await client.get(
            f"/api/v1/messaging/threads/{thread_with_messages.id}?limit=2",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) <= 2
        assert data["has_more"] is True


class TestThreadSearch:
    """Test thread search functionality."""

    @pytest.fixture
    async def multiple_threads(self, db_session, test_doctor):
        """Create multiple threads for search testing."""
        from app.models.patient import Patient
        from app.models.user import User, UserType
        from app.utils.security import hash_password

        threads = []
        patients = []

        for i, name in enumerate(["Alice Smith", "Bob Johnson", "Charlie Brown"]):
            first, last = name.split()

            user = User(
                email=f"{first.lower()}@test.com",
                password_hash=hash_password("test"),
                user_type=UserType.PATIENT
            )
            db_session.add(user)
            await db_session.flush()

            patient = Patient(
                user_id=user.id,
                first_name=first,
                last_name=last,
                primary_doctor_id=test_doctor.id
            )
            db_session.add(patient)
            await db_session.flush()
            patients.append(patient)

            thread = DoctorPatientThread(
                doctor_id=test_doctor.id,
                patient_id=patient.id
            )
            db_session.add(thread)
            threads.append(thread)

        await db_session.commit()
        return threads, patients

    @pytest.mark.asyncio
    async def test_search_threads_by_name(
        self, client: AsyncClient, doctor_token, multiple_threads
    ):
        """Test searching threads by patient name."""
        threads, patients = multiple_threads

        response = await client.get(
            "/api/v1/messaging/threads?search=Alice",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "Alice" in data["items"][0]["other_party_name"]

    @pytest.mark.asyncio
    async def test_search_threads_partial_match(
        self, client: AsyncClient, doctor_token, multiple_threads
    ):
        """Test partial name matching in search."""
        threads, patients = multiple_threads

        response = await client.get(
            "/api/v1/messaging/threads?search=son",  # Matches "Johnson"
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestAttachmentUpload:
    """Test file attachment upload functionality."""

    @pytest.mark.asyncio
    async def test_upload_attachment_unauthorized(self, client: AsyncClient):
        """Test upload without authentication fails."""
        response = await client.post(
            "/api/v1/messaging/upload",
            files={"file": ("test.txt", b"Hello World", "text/plain")}
        )
        assert response.status_code == 401


class TestDoctorStartThread:
    """Test doctor starting thread functionality."""

    @pytest.mark.asyncio
    async def test_doctor_start_thread_patient_not_found(
        self, client: AsyncClient, doctor_token
    ):
        """Test starting thread with non-existent patient."""
        response = await client.post(
            "/api/v1/messaging/doctor/patients/nonexistent-id/thread",
            headers=auth_headers(doctor_token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_doctor_start_thread_creates_new_thread(
        self, client: AsyncClient, doctor_token, connected_patient_doctor
    ):
        """Test starting a new thread with connected patient."""
        patient, doctor = connected_patient_doctor

        response = await client.post(
            f"/api/v1/messaging/doctor/patients/{patient.id}/thread",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["other_party_id"] == patient.id
        assert data["can_send_message"] is True

    @pytest.mark.asyncio
    async def test_doctor_start_thread_returns_existing(
        self, client: AsyncClient, doctor_token, connected_patient_doctor, db_session
    ):
        """Test starting thread returns existing thread if one exists."""
        patient, doctor = connected_patient_doctor

        # Create existing thread
        from app.models.messaging import DoctorPatientThread
        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        db_session.add(thread)
        await db_session.commit()

        # Try to start again
        response = await client.post(
            f"/api/v1/messaging/doctor/patients/{patient.id}/thread",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == thread.id


class TestThreadPagination:
    """Test thread list pagination."""

    @pytest.mark.asyncio
    async def test_threads_pagination_offset(
        self, client: AsyncClient, doctor_token, db_session, test_doctor
    ):
        """Test thread list pagination with offset."""
        from app.models.patient import Patient
        from app.models.user import User, UserType
        from app.models.messaging import DoctorPatientThread
        from app.utils.security import hash_password

        # Create multiple threads
        for i in range(5):
            user = User(
                email=f"page_patient_{i}@test.com",
                password_hash=hash_password("test"),
                user_type=UserType.PATIENT
            )
            db_session.add(user)
            await db_session.flush()

            patient = Patient(
                user_id=user.id,
                first_name=f"Page{i}",
                last_name="Patient",
                primary_doctor_id=test_doctor.id
            )
            db_session.add(patient)
            await db_session.flush()

            thread = DoctorPatientThread(
                doctor_id=test_doctor.id,
                patient_id=patient.id
            )
            db_session.add(thread)

        await db_session.commit()

        # Test pagination
        response = await client.get(
            "/api/v1/messaging/threads?limit=2&offset=0",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["has_more"] is True

    @pytest.mark.asyncio
    async def test_threads_patient_search(
        self, client: AsyncClient, patient_token, connected_patient_doctor, db_session
    ):
        """Test patient searching threads by doctor name."""
        patient, doctor = connected_patient_doctor

        # Create thread
        from app.models.messaging import DoctorPatientThread
        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        db_session.add(thread)
        await db_session.commit()

        response = await client.get(
            "/api/v1/messaging/threads?search=Doctor",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


class TestUnreadCountDoctor:
    """Test unread count for doctors."""

    @pytest.mark.asyncio
    async def test_doctor_unread_count(
        self, client: AsyncClient, doctor_token, connected_patient_doctor, db_session
    ):
        """Test doctor getting unread message count."""
        patient, doctor = connected_patient_doctor

        from app.models.messaging import DoctorPatientThread
        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id,
            doctor_unread_count=5
        )
        db_session.add(thread)
        await db_session.commit()

        response = await client.get(
            "/api/v1/messaging/unread",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_unread"] == 5


class TestMessageTypes:
    """Test different message types."""

    @pytest_asyncio.fixture
    async def thread_for_message_types(
        self, db_session, connected_patient_doctor
    ) -> str:
        """Create a thread for testing message types."""
        patient, doctor = connected_patient_doctor

        from app.models.messaging import DoctorPatientThread
        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        db_session.add(thread)
        await db_session.commit()
        return thread.id

    @pytest.mark.asyncio
    async def test_send_image_message_type(
        self, client: AsyncClient, doctor_token, thread_for_message_types
    ):
        """Test sending IMAGE message type."""
        response = await client.post(
            f"/api/v1/messaging/threads/{thread_for_message_types}/messages",
            headers=auth_headers(doctor_token),
            json={
                "content": "Image description",
                "message_type": "IMAGE"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message_type"] == "IMAGE"

    @pytest.mark.asyncio
    async def test_send_file_message_type(
        self, client: AsyncClient, doctor_token, thread_for_message_types
    ):
        """Test sending FILE message type."""
        response = await client.post(
            f"/api/v1/messaging/threads/{thread_for_message_types}/messages",
            headers=auth_headers(doctor_token),
            json={
                "content": "File description",
                "message_type": "FILE"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message_type"] == "FILE"


class TestThreadDetailPatient:
    """Test thread detail for patients."""

    @pytest.mark.asyncio
    async def test_patient_get_thread_detail(
        self, client: AsyncClient, patient_token, connected_patient_doctor, db_session
    ):
        """Test patient getting thread detail."""
        patient, doctor = connected_patient_doctor

        from app.models.messaging import DoctorPatientThread, DirectMessage, MessageType
        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        db_session.add(thread)
        await db_session.flush()

        msg = DirectMessage(
            thread_id=thread.id,
            sender_type="DOCTOR",
            sender_id=doctor.id,
            content="Hello patient",
            message_type=MessageType.TEXT
        )
        db_session.add(msg)
        await db_session.commit()

        response = await client.get(
            f"/api/v1/messaging/threads/{thread.id}",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["other_party_type"] == "DOCTOR"
        assert len(data["messages"]) == 1

    @pytest.mark.asyncio
    async def test_get_thread_with_before_timestamp(
        self, client: AsyncClient, doctor_token, connected_patient_doctor, db_session
    ):
        """Test getting thread with before timestamp pagination."""
        patient, doctor = connected_patient_doctor
        from datetime import datetime, timedelta

        from app.models.messaging import DoctorPatientThread, DirectMessage, MessageType
        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        db_session.add(thread)
        await db_session.flush()

        # Add messages with different timestamps
        now = datetime.utcnow()
        for i in range(3):
            msg = DirectMessage(
                thread_id=thread.id,
                sender_type="DOCTOR",
                sender_id=doctor.id,
                content=f"Message {i}",
                message_type=MessageType.TEXT,
                created_at=now - timedelta(hours=i)
            )
            db_session.add(msg)
        await db_session.commit()

        # Get messages before a certain time
        before_time = (now - timedelta(hours=1)).isoformat()
        response = await client.get(
            f"/api/v1/messaging/threads/{thread.id}?before={before_time}",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200


class TestEdgeCases:
    """Test edge cases for messaging."""

    @pytest.mark.asyncio
    async def test_nonexistent_thread_detail(
        self, client: AsyncClient, doctor_token
    ):
        """Test getting detail for non-existent thread."""
        response = await client.get(
            "/api/v1/messaging/threads/nonexistent-thread-id",
            headers=auth_headers(doctor_token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_mark_read_nonexistent_thread(
        self, client: AsyncClient, doctor_token
    ):
        """Test marking non-existent thread as read."""
        response = await client.post(
            "/api/v1/messaging/threads/nonexistent-thread-id/read",
            headers=auth_headers(doctor_token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthorized_thread_access(
        self, client: AsyncClient, patient_token, db_session, test_doctor
    ):
        """Test patient cannot access thread they're not part of."""
        from app.models.patient import Patient
        from app.models.user import User, UserType
        from app.models.messaging import DoctorPatientThread
        from app.utils.security import hash_password

        # Create another patient
        user = User(
            email="other_patient_msg@test.com",
            password_hash=hash_password("test"),
            user_type=UserType.PATIENT
        )
        db_session.add(user)
        await db_session.flush()

        other_patient = Patient(
            user_id=user.id,
            first_name="Other",
            last_name="Patient"
        )
        db_session.add(other_patient)
        await db_session.flush()

        thread = DoctorPatientThread(
            doctor_id=test_doctor.id,
            patient_id=other_patient.id
        )
        db_session.add(thread)
        await db_session.commit()

        # Original patient tries to access
        response = await client.get(
            f"/api/v1/messaging/threads/{thread.id}",
            headers=auth_headers(patient_token)
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_patient_cannot_start_thread(
        self, client: AsyncClient, patient_token, test_doctor
    ):
        """Test patient cannot use doctor endpoint to start thread."""
        response = await client.post(
            f"/api/v1/messaging/doctor/patients/{test_doctor.id}/thread",
            headers=auth_headers(patient_token)
        )
        # Should fail - patients can't use doctor endpoints
        assert response.status_code in [401, 403]
