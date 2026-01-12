"""
Database Query Performance Tests.

Tests database operations and validates query performance.
Identifies N+1 queries, slow queries, and missing indexes.

Run with: pytest tests/performance/test_database_performance.py -v -s
"""

import asyncio
import statistics
import time
from datetime import date, datetime, timedelta
from typing import List
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.database import Base
from app.models.user import User, UserType
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.checkin import DailyCheckin
from app.models.assessment import Assessment, AssessmentType, SeverityLevel
from app.models.risk_event import RiskEvent, RiskLevel, RiskType
from app.models.conversation import Conversation, ConversationType
from app.models.messaging import DoctorPatientThread, DirectMessage, MessageType
from app.utils.security import hash_password


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class QueryCounter:
    """Count and track SQL queries for N+1 detection."""

    def __init__(self):
        self.queries: List[str] = []
        self.start_time: float = 0
        self.query_times: List[float] = []

    def clear(self):
        self.queries = []
        self.query_times = []

    @property
    def count(self) -> int:
        return len(self.queries)

    @property
    def total_time_ms(self) -> float:
        return sum(self.query_times)

    def __enter__(self):
        self.clear()
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        pass


# Global query counter
query_counter = QueryCounter()


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine with query logging."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Register query listener for tracking
    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        query_counter.queries.append(statement)
        conn.info.setdefault('query_start_time', []).append(time.perf_counter())

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start_times = conn.info.get('query_start_time', [])
        if start_times:
            elapsed = (time.perf_counter() - start_times.pop()) * 1000
            query_counter.query_times.append(elapsed)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create database session."""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def seed_data(db_session: AsyncSession):
    """Seed database with test data for performance testing."""
    # Create doctors
    doctors = []
    for i in range(5):
        user = User(
            id=str(uuid4()),
            email=f"doctor{i}@test.com",
            password_hash=hash_password("password"),
            user_type=UserType.DOCTOR,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        doctor = Doctor(
            id=str(uuid4()),
            user_id=user.id,
            first_name=f"Doctor{i}",
            last_name="Test",
        )
        db_session.add(doctor)
        doctors.append(doctor)

    await db_session.flush()

    # Create patients with data
    patients = []
    for i in range(50):  # 50 patients
        user = User(
            id=str(uuid4()),
            email=f"patient{i}@test.com",
            password_hash=hash_password("password"),
            user_type=UserType.PATIENT,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        patient = Patient(
            id=str(uuid4()),
            user_id=user.id,
            first_name=f"Patient{i}",
            last_name="Test",
            date_of_birth=date(1980 + (i % 30), (i % 12) + 1, (i % 28) + 1),
            primary_doctor_id=doctors[i % 5].id,
        )
        db_session.add(patient)
        patients.append(patient)

        # Create check-ins for each patient (30 days)
        for day in range(30):
            checkin = DailyCheckin(
                id=str(uuid4()),
                patient_id=patient.id,
                checkin_date=date.today() - timedelta(days=day),
                mood_score=(i + day) % 10 + 1,
                sleep_hours=6 + (day % 4),
                sleep_quality=(day % 5) + 1,
                medication_taken=day % 2 == 0,
            )
            db_session.add(checkin)

        # Create assessments for each patient (5 each)
        for j in range(5):
            assessment = Assessment(
                id=str(uuid4()),
                patient_id=patient.id,
                assessment_type=AssessmentType.PHQ9 if j % 2 == 0 else AssessmentType.GAD7,
                responses_json='{"1": 2, "2": 1, "3": 2}',
                total_score=5 + (j * 2),
                severity=SeverityLevel.MILD if j < 3 else SeverityLevel.MODERATE,
                created_at=datetime.utcnow() - timedelta(days=j * 7),
            )
            db_session.add(assessment)

        # Create conversations for each patient
        for k in range(3):
            conv = Conversation(
                id=str(uuid4()),
                patient_id=patient.id,
                conv_type=ConversationType.SUPPORTIVE_CHAT,
                messages_json='[{"role": "user", "content": "Test"}, {"role": "assistant", "content": "Response"}]',
                is_active=k == 0,
            )
            db_session.add(conv)

            # Create risk events for some conversations
            if i % 5 == 0:
                risk = RiskEvent(
                    id=str(uuid4()),
                    patient_id=patient.id,
                    conversation_id=conv.id,
                    risk_level=RiskLevel.MEDIUM if k == 0 else RiskLevel.LOW,
                    risk_type=RiskType.OTHER,
                    trigger_text="Test trigger",
                    ai_confidence=0.75,
                    doctor_reviewed=k > 0,
                )
                db_session.add(risk)

    await db_session.flush()

    # Create message threads
    for i, patient in enumerate(patients[:20]):  # 20 patients have threads
        doctor = doctors[i % 5]
        thread = DoctorPatientThread(
            id=str(uuid4()),
            doctor_id=doctor.id,
            patient_id=patient.id,
            last_message_at=datetime.utcnow(),
        )
        db_session.add(thread)
        await db_session.flush()

        # Create messages in thread
        for j in range(10):
            msg = DirectMessage(
                id=str(uuid4()),
                thread_id=thread.id,
                sender_type="DOCTOR" if j % 2 == 0 else "PATIENT",
                sender_id=doctor.id if j % 2 == 0 else patient.id,
                content=f"Test message {j}",
                message_type=MessageType.TEXT,
                is_read=j < 5,
            )
            db_session.add(msg)

    await db_session.commit()

    return {"doctors": doctors, "patients": patients}


class TestQueryPerformance:
    """Test individual query performance."""

    @pytest.mark.asyncio
    async def test_patient_list_query_count(self, db_session: AsyncSession, seed_data):
        """Test that patient list doesn't cause N+1 queries."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        query_counter.clear()

        # This should be a single query with eager loading
        result = await db_session.execute(
            select(Patient)
            .options(selectinload(Patient.primary_doctor))
            .limit(20)
        )
        patients = result.scalars().all()

        # Access related data
        for patient in patients:
            _ = patient.primary_doctor

        # Should be at most 2 queries (patients + doctors batch)
        assert query_counter.count <= 2, \
            f"N+1 detected: {query_counter.count} queries for {len(patients)} patients"
        print(f"\nPatient list: {query_counter.count} queries for {len(patients)} patients")

    @pytest.mark.asyncio
    async def test_checkin_range_query(self, db_session: AsyncSession, seed_data):
        """Test check-in range query performance."""
        from sqlalchemy import select, and_

        patients = seed_data["patients"]
        patient = patients[0]

        times = []
        for _ in range(20):
            query_counter.clear()
            start = time.perf_counter()

            result = await db_session.execute(
                select(DailyCheckin)
                .where(
                    and_(
                        DailyCheckin.patient_id == patient.id,
                        DailyCheckin.checkin_date >= date.today() - timedelta(days=30),
                        DailyCheckin.checkin_date <= date.today()
                    )
                )
                .order_by(DailyCheckin.checkin_date.desc())
            )
            checkins = result.scalars().all()

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        print(f"\nCheckin range query: avg={avg_time:.2f}ms, p95={p95_time:.2f}ms")
        assert p95_time < 50, f"Check-in query P95 {p95_time:.2f}ms exceeds 50ms"

    @pytest.mark.asyncio
    async def test_assessment_aggregation_query(self, db_session: AsyncSession, seed_data):
        """Test assessment aggregation performance."""
        from sqlalchemy import select, func

        times = []
        for _ in range(20):
            start = time.perf_counter()

            # Aggregate assessment scores by type
            result = await db_session.execute(
                select(
                    Assessment.assessment_type,
                    func.count(Assessment.id).label('count'),
                    func.avg(Assessment.total_score).label('avg_score')
                )
                .group_by(Assessment.assessment_type)
            )
            _ = result.all()

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)
        print(f"\nAssessment aggregation: avg={avg_time:.2f}ms")
        assert avg_time < 100, f"Aggregation avg {avg_time:.2f}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_risk_queue_query(self, db_session: AsyncSession, seed_data):
        """Test risk queue query performance (critical for doctors)."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        doctors = seed_data["doctors"]
        doctor = doctors[0]

        times = []
        for _ in range(20):
            query_counter.clear()
            start = time.perf_counter()

            # Get unreviewed risk events for doctor's patients
            result = await db_session.execute(
                select(RiskEvent)
                .join(Patient, RiskEvent.patient_id == Patient.id)
                .where(
                    Patient.primary_doctor_id == doctor.id,
                    RiskEvent.doctor_reviewed == False
                )
                .options(selectinload(RiskEvent.patient))
                .order_by(RiskEvent.created_at.desc())
                .limit(50)
            )
            risks = result.scalars().all()

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        print(f"\nRisk queue query: avg={avg_time:.2f}ms, p95={p95_time:.2f}ms, queries={query_counter.count}")
        assert p95_time < 100, f"Risk queue P95 {p95_time:.2f}ms exceeds 100ms"

    @pytest.mark.asyncio
    async def test_message_thread_query(self, db_session: AsyncSession, seed_data):
        """Test message thread with messages query."""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        patients = seed_data["patients"]
        patient = patients[0]

        times = []
        query_counts = []

        for _ in range(20):
            query_counter.clear()
            start = time.perf_counter()

            result = await db_session.execute(
                select(DoctorPatientThread)
                .where(DoctorPatientThread.patient_id == patient.id)
                .options(
                    selectinload(DoctorPatientThread.messages),
                    selectinload(DoctorPatientThread.doctor)
                )
            )
            threads = result.scalars().all()

            # Access related data
            for thread in threads:
                _ = thread.messages
                _ = thread.doctor

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
            query_counts.append(query_counter.count)

        avg_time = statistics.mean(times)
        avg_queries = statistics.mean(query_counts)

        print(f"\nThread query: avg={avg_time:.2f}ms, avg_queries={avg_queries:.1f}")
        assert avg_queries <= 3, f"Too many queries: {avg_queries}"


class TestBulkOperations:
    """Test bulk operation performance."""

    @pytest.mark.asyncio
    async def test_bulk_checkin_insert(self, db_session: AsyncSession, seed_data):
        """Test bulk check-in insertion performance."""
        patients = seed_data["patients"]
        patient = patients[-1]  # Use last patient to avoid conflicts

        checkins = []
        for i in range(100):
            checkins.append(DailyCheckin(
                id=str(uuid4()),
                patient_id=patient.id,
                checkin_date=date.today() - timedelta(days=100 + i),
                mood_score=(i % 10) + 1,
                sleep_hours=7,
            ))

        start = time.perf_counter()
        db_session.add_all(checkins)
        await db_session.flush()
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\nBulk insert 100 check-ins: {elapsed:.2f}ms ({elapsed/100:.2f}ms each)")
        assert elapsed < 1000, f"Bulk insert took {elapsed:.2f}ms, exceeds 1000ms"

    @pytest.mark.asyncio
    async def test_bulk_message_insert(self, db_session: AsyncSession, seed_data):
        """Test bulk message insertion performance."""
        from sqlalchemy import select

        # Get a thread
        result = await db_session.execute(select(DoctorPatientThread).limit(1))
        thread = result.scalar_one_or_none()

        if not thread:
            pytest.skip("No thread found")

        messages = []
        for i in range(100):
            messages.append(DirectMessage(
                id=str(uuid4()),
                thread_id=thread.id,
                sender_type="PATIENT",
                sender_id=thread.patient_id,
                content=f"Bulk test message {i}",
                message_type=MessageType.TEXT,
            ))

        start = time.perf_counter()
        db_session.add_all(messages)
        await db_session.flush()
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\nBulk insert 100 messages: {elapsed:.2f}ms ({elapsed/100:.2f}ms each)")
        assert elapsed < 1000, f"Bulk insert took {elapsed:.2f}ms"


class TestIndexEffectiveness:
    """Test that indexes are effective."""

    @pytest.mark.asyncio
    async def test_patient_id_index(self, db_session: AsyncSession, seed_data):
        """Test patient_id index on check-ins."""
        from sqlalchemy import select, text

        patients = seed_data["patients"]

        # Query using patient_id index
        times = []
        for patient in patients[:10]:
            start = time.perf_counter()

            result = await db_session.execute(
                select(DailyCheckin)
                .where(DailyCheckin.patient_id == patient.id)
                .order_by(DailyCheckin.checkin_date.desc())
                .limit(10)
            )
            _ = result.scalars().all()

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)
        print(f"\nPatient ID indexed query: avg={avg_time:.2f}ms")
        assert avg_time < 20, f"Indexed query avg {avg_time:.2f}ms exceeds 20ms"

    @pytest.mark.asyncio
    async def test_date_range_index(self, db_session: AsyncSession, seed_data):
        """Test checkin_date index effectiveness."""
        from sqlalchemy import select, and_

        times = []
        for day_offset in range(10):
            start = time.perf_counter()

            target_date = date.today() - timedelta(days=day_offset)
            result = await db_session.execute(
                select(DailyCheckin)
                .where(DailyCheckin.checkin_date == target_date)
                .limit(100)
            )
            _ = result.scalars().all()

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)
        print(f"\nDate indexed query: avg={avg_time:.2f}ms")
        assert avg_time < 20, f"Date query avg {avg_time:.2f}ms exceeds 20ms"

    @pytest.mark.asyncio
    async def test_compound_index_simulation(self, db_session: AsyncSession, seed_data):
        """Test query that would benefit from compound index (patient_id, created_at)."""
        from sqlalchemy import select, and_

        patients = seed_data["patients"]
        patient = patients[0]

        times = []
        for _ in range(20):
            start = time.perf_counter()

            # Query that benefits from compound index
            result = await db_session.execute(
                select(Assessment)
                .where(
                    and_(
                        Assessment.patient_id == patient.id,
                        Assessment.created_at >= datetime.utcnow() - timedelta(days=30)
                    )
                )
                .order_by(Assessment.created_at.desc())
            )
            _ = result.scalars().all()

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = statistics.mean(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        print(f"\nCompound query (patient_id + created_at): avg={avg_time:.2f}ms, p95={p95_time:.2f}ms")
        # This would be faster with a compound index
        assert p95_time < 50, f"Query P95 {p95_time:.2f}ms exceeds 50ms"


class TestConnectionPooling:
    """Test connection pool behavior under load."""

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, db_engine):
        """Test handling of concurrent database connections."""
        async_session_maker = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async def run_query(session_maker, query_id):
            async with session_maker() as session:
                start = time.perf_counter()
                result = await session.execute(text("SELECT 1"))
                _ = result.scalar()
                return (time.perf_counter() - start) * 1000

        # Run 20 concurrent queries
        tasks = [run_query(async_session_maker, i) for i in range(20)]
        times = await asyncio.gather(*tasks)

        avg_time = statistics.mean(times)
        max_time = max(times)

        print(f"\n20 concurrent queries: avg={avg_time:.2f}ms, max={max_time:.2f}ms")
        assert max_time < 100, f"Max query time {max_time:.2f}ms exceeds 100ms"
