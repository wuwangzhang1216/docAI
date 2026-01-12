"""
Pytest configuration and fixtures for testing.

This module provides:
- Async test support with pytest-asyncio
- In-memory SQLite database for isolated testing
- Test client with httpx for async API testing
- Factory fixtures for creating test data
"""

import asyncio
from datetime import date, datetime
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserType
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.utils.security import hash_password, create_access_token
import app.utils.rate_limit as rate_limit_module


# Test database URL - using in-memory SQLite for speed
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state before each test to avoid rate limit interference."""
    # Reset in-memory rate limiter
    rate_limit_module._memory_limiter = None
    rate_limit_module._redis_limiter = None
    yield


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============ User Fixtures ============

@pytest_asyncio.fixture
async def test_patient_user(db_session: AsyncSession) -> User:
    """Create a test patient user."""
    user = User(
        id=str(uuid4()),
        email="patient@test.com",
        password_hash=hash_password("testpassword123"),
        user_type=UserType.PATIENT,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    patient = Patient(
        id=str(uuid4()),
        user_id=user.id,
        first_name="Test",
        last_name="Patient",
        date_of_birth=date(1990, 1, 1),
    )
    db_session.add(patient)
    await db_session.commit()

    return user


@pytest_asyncio.fixture
async def test_doctor_user(db_session: AsyncSession) -> User:
    """Create a test doctor user."""
    user = User(
        id=str(uuid4()),
        email="doctor@test.com",
        password_hash=hash_password("testpassword123"),
        user_type=UserType.DOCTOR,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    doctor = Doctor(
        id=str(uuid4()),
        user_id=user.id,
        first_name="Test",
        last_name="Doctor",
    )
    db_session.add(doctor)
    await db_session.commit()

    return user


@pytest_asyncio.fixture
async def test_patient(db_session: AsyncSession, test_patient_user: User) -> Patient:
    """Get the test patient profile."""
    from sqlalchemy import select
    result = await db_session.execute(
        select(Patient).where(Patient.user_id == test_patient_user.id)
    )
    return result.scalar_one()


@pytest_asyncio.fixture
async def test_doctor(db_session: AsyncSession, test_doctor_user: User) -> Doctor:
    """Get the test doctor profile."""
    from sqlalchemy import select
    result = await db_session.execute(
        select(Doctor).where(Doctor.user_id == test_doctor_user.id)
    )
    return result.scalar_one()


@pytest_asyncio.fixture
async def connected_patient_doctor(
    db_session: AsyncSession,
    test_patient: Patient,
    test_doctor: Doctor
) -> tuple[Patient, Doctor]:
    """Create a connected patient-doctor relationship."""
    test_patient.primary_doctor_id = test_doctor.id
    await db_session.commit()
    await db_session.refresh(test_patient)
    return test_patient, test_doctor


# ============ Token Fixtures ============

@pytest.fixture
def patient_token(test_patient_user: User) -> str:
    """Create a JWT token for the test patient."""
    return create_access_token({
        "sub": test_patient_user.id,
        "type": test_patient_user.user_type.value
    })


@pytest.fixture
def doctor_token(test_doctor_user: User) -> str:
    """Create a JWT token for the test doctor."""
    return create_access_token({
        "sub": test_doctor_user.id,
        "type": test_doctor_user.user_type.value
    })


def auth_headers(token: str) -> dict:
    """Create authorization headers with the given token."""
    return {"Authorization": f"Bearer {token}"}


# ============ Messaging Fixtures ============

@pytest_asyncio.fixture
async def message_thread(
    db_session: AsyncSession,
    connected_patient_doctor: tuple[Patient, Doctor]
) -> "DoctorPatientThread":
    """Create a message thread between connected patient and doctor."""
    from app.models.messaging import DoctorPatientThread

    patient, doctor = connected_patient_doctor

    thread = DoctorPatientThread(
        id=str(uuid4()),
        doctor_id=doctor.id,
        patient_id=patient.id
    )
    db_session.add(thread)
    await db_session.commit()
    await db_session.refresh(thread)

    return thread


@pytest_asyncio.fixture
async def thread_with_messages(
    db_session: AsyncSession,
    connected_patient_doctor: tuple[Patient, Doctor]
) -> tuple["DoctorPatientThread", list["DirectMessage"]]:
    """Create a thread with several messages."""
    from app.models.messaging import DoctorPatientThread, DirectMessage, MessageType

    patient, doctor = connected_patient_doctor

    thread = DoctorPatientThread(
        id=str(uuid4()),
        doctor_id=doctor.id,
        patient_id=patient.id,
        doctor_unread_count=2,
        patient_unread_count=1
    )
    db_session.add(thread)
    await db_session.flush()

    messages = []
    for i in range(5):
        msg = DirectMessage(
            id=str(uuid4()),
            thread_id=thread.id,
            sender_type="DOCTOR" if i % 2 == 0 else "PATIENT",
            sender_id=doctor.id if i % 2 == 0 else patient.id,
            content=f"Test message {i + 1}",
            message_type=MessageType.TEXT,
            is_read=i < 3  # First 3 messages are read
        )
        db_session.add(msg)
        messages.append(msg)

    await db_session.commit()
    return thread, messages
