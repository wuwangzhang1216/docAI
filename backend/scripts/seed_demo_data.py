#!/usr/bin/env python3
"""
Demo Data Seed Script for 心守AI

This script creates mock data for demo purposes including:
- 2 doctors
- 3 patients (with various risk levels and data)
- Daily check-ins (30 days of data)
- Assessments (PHQ-9, GAD-7, PCL-5)
- AI conversations with risk events
- Doctor-patient connections
- Messages between doctors and patients
- Appointments

Usage:
    cd backend
    python scripts/seed_demo_data.py
"""

import asyncio
import json
import random
from datetime import datetime, timedelta, date, time
from uuid import uuid4

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

from app.config import settings
from app.database import Base
from app.models.user import User, UserType
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.checkin import DailyCheckin
from app.models.assessment import Assessment, AssessmentType, SeverityLevel
from app.models.conversation import Conversation, ConversationType
from app.models.risk_event import RiskEvent, RiskLevel, RiskType
from app.models.connection_request import PatientConnectionRequest, ConnectionStatus
from app.models.messaging import DoctorPatientThread, DirectMessage, MessageType
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.utils.security import hash_password


# ==================== DEMO ACCOUNT CREDENTIALS ====================
DEMO_PASSWORD = "Demo123!"

DEMO_DOCTORS = [
    {
        "email": "dr.sarah@demo.com",
        "first_name": "Sarah",
        "last_name": "Mitchell",
        "specialty": "Clinical Psychology",
        "license_number": "PSY-2024-001",
        "phone": "+1-416-555-0101",
        "bio": "Dr. Mitchell specializes in trauma therapy and has over 10 years of experience working with refugees and political trauma survivors.",
        "years_of_experience": "10",
        "education": "PhD in Clinical Psychology, University of Toronto",
        "languages": "English, French, Farsi",
        "clinic_name": "Heart Guardian Mental Health Center",
        "clinic_address": "123 Wellness Street",
        "clinic_city": "Toronto",
        "clinic_country": "Canada",
        "consultation_hours": "Mon-Fri 9:00-17:00",
    },
    {
        "email": "dr.james@demo.com",
        "first_name": "James",
        "last_name": "Thompson",
        "specialty": "Psychiatry",
        "license_number": "PSY-2024-002",
        "phone": "+1-416-555-0102",
        "bio": "Dr. Thompson is a board-certified psychiatrist focusing on anxiety disorders and PTSD treatment.",
        "years_of_experience": "8",
        "education": "MD, McGill University; Psychiatry Residency, University of British Columbia",
        "languages": "English, French",
        "clinic_name": "Heart Guardian Mental Health Center",
        "clinic_address": "123 Wellness Street",
        "clinic_city": "Toronto",
        "clinic_country": "Canada",
        "consultation_hours": "Mon-Thu 10:00-18:00",
    },
]

DEMO_PATIENTS = [
    {
        "email": "patient.michael@demo.com",
        "first_name": "Michael",
        "last_name": "Roberts",
        "date_of_birth": date(1985, 3, 15),
        "phone": "+1-416-555-0201",
        "gender": "male",
        "preferred_language": "en",
        "address": "456 Maple Street",
        "city": "Toronto",
        "country": "Canada",
        "current_medications": "Sertraline 50mg daily",
        "medical_conditions": "Mild hypertension",
        "allergies": "None",
        "therapy_history": "Previous CBT for 6 months in 2022",
        "mental_health_goals": "Manage anxiety, improve sleep quality, process past trauma",
        "support_system": "Wife, local community group",
        "triggers_notes": "News about political events, anniversary dates",
        "coping_strategies": "Deep breathing, journaling, walking",
        "emergency_contact": "Jennifer Roberts",
        "emergency_phone": "+1-416-555-0202",
        "emergency_contact_relationship": "Spouse",
        "consent_signed": True,
        # Demo scenario: moderate risk, connected to Dr. Mitchell
        "risk_level": "MEDIUM",
        "mood_trend": "improving",  # mood will trend upward
    },
    {
        "email": "patient.emily@demo.com",
        "first_name": "Emily",
        "last_name": "Chen",
        "date_of_birth": date(1990, 8, 22),
        "phone": "+1-416-555-0203",
        "gender": "female",
        "preferred_language": "en",
        "address": "789 Oak Avenue",
        "city": "Vancouver",
        "country": "Canada",
        "current_medications": "None",
        "medical_conditions": "None",
        "allergies": "Penicillin",
        "therapy_history": "First time seeking mental health support",
        "mental_health_goals": "Understand my emotions, build resilience",
        "support_system": "Friends, online community",
        "triggers_notes": "Social isolation, work stress",
        "coping_strategies": "Meditation, exercise",
        "emergency_contact": "David Chen",
        "emergency_phone": "+1-604-555-0204",
        "emergency_contact_relationship": "Brother",
        "consent_signed": True,
        # Demo scenario: high risk (recent crisis), connected to Dr. Mitchell
        "risk_level": "HIGH",
        "mood_trend": "fluctuating",  # mood will fluctuate
    },
    {
        "email": "patient.david@demo.com",
        "first_name": "David",
        "last_name": "Wilson",
        "date_of_birth": date(1978, 12, 5),
        "phone": "+1-514-555-0205",
        "gender": "male",
        "preferred_language": "en",
        "address": "321 Pine Drive",
        "city": "Montreal",
        "country": "Canada",
        "current_medications": "Escitalopram 10mg daily, Trazodone 50mg as needed",
        "medical_conditions": "Type 2 diabetes",
        "allergies": "Sulfa drugs",
        "therapy_history": "Long-term therapy since 2019, multiple therapists",
        "mental_health_goals": "Stability, reduce medication dependency",
        "support_system": "Therapist, support group, church community",
        "triggers_notes": "Family conflicts, financial stress, political news",
        "coping_strategies": "Support group meetings, prayer, gardening",
        "emergency_contact": "Susan Wilson",
        "emergency_phone": "+1-514-555-0206",
        "emergency_contact_relationship": "Wife",
        "consent_signed": True,
        # Demo scenario: low risk, stable, connected to Dr. Thompson
        "risk_level": "LOW",
        "mood_trend": "stable",  # mood will be stable around 6-7
    },
]


# ==================== SAMPLE CONVERSATIONS ====================
SAMPLE_CONVERSATIONS = {
    "HIGH": [
        {"role": "user", "content": "I've been feeling really hopeless lately. Nothing seems to matter anymore."},
        {"role": "assistant", "content": "I hear that you're going through a very difficult time, and I appreciate you sharing this with me. Feeling hopeless can be incredibly overwhelming. Can you tell me more about what's been happening that's making you feel this way?"},
        {"role": "user", "content": "Ever since I left my country, I feel like I've lost everything. My family is still there and I can't help them. Sometimes I think they'd be better off without me."},
        {"role": "assistant", "content": "What you're experiencing sounds incredibly painful - the separation from your family and feeling powerless to help them. These feelings of guilt and hopelessness are very common among survivors of political trauma. When you say they'd be 'better off without you,' I want to make sure I understand - are you having thoughts of harming yourself?"},
        {"role": "user", "content": "I don't want to die, but sometimes I just want the pain to stop. I feel so alone."},
        {"role": "assistant", "content": "Thank you for being honest with me. The pain you're feeling is real and valid. You're not alone in this - many people who have experienced what you have feel this way. I'm here with you right now, and there are people who care about you and want to help. Your doctor has been notified to provide additional support. Would you like to talk about some ways we can help make this moment feel a bit more manageable?"},
    ],
    "MEDIUM": [
        {"role": "user", "content": "I couldn't sleep again last night. Kept having nightmares about the past."},
        {"role": "assistant", "content": "I'm sorry to hear you're struggling with sleep and nightmares. That must be exhausting. Can you tell me a bit about what these nightmares involve, if you feel comfortable sharing?"},
        {"role": "user", "content": "It's always about the day I had to leave. The fear, the chaos. I wake up with my heart racing."},
        {"role": "assistant", "content": "Those kinds of vivid memories intruding on your sleep are a common response to traumatic experiences. Your mind is trying to process what happened, even though it's painful. How often are you experiencing these nightmares?"},
        {"role": "user", "content": "Almost every night this week. I'm so tired but I'm scared to go to sleep."},
        {"role": "assistant", "content": "That fear of sleeping because of nightmares creates a difficult cycle. There are some techniques that might help - would you like me to share some strategies for managing nighttime anxiety and creating a sense of safety before bed?"},
    ],
    "LOW": [
        {"role": "user", "content": "Hi, I wanted to check in today. I've been feeling pretty good actually."},
        {"role": "assistant", "content": "Hello! It's great to hear from you. I'm glad you're feeling good. What do you think has been contributing to this positive feeling?"},
        {"role": "user", "content": "I've been sticking to my routine - morning walks, taking my medication, and I joined a local community group."},
        {"role": "assistant", "content": "That's wonderful progress! Building routines and community connections are such important parts of maintaining mental wellness. How has the community group been for you?"},
        {"role": "user", "content": "It's been nice to meet people who understand what I've been through. I don't feel so alone anymore."},
        {"role": "assistant", "content": "Finding that sense of belonging and being understood is so valuable. It sounds like you're building a strong support system. How are things going with your sleep and overall energy levels?"},
    ],
}


# ==================== HELPER FUNCTIONS ====================

def generate_checkin_data(mood_trend: str, days: int = 30) -> list:
    """Generate daily check-in data based on mood trend."""
    checkins = []
    today = date.today()

    for i in range(days):
        checkin_date = today - timedelta(days=days - 1 - i)

        if mood_trend == "improving":
            # Start low, gradually improve
            base_mood = 3 + (i / days) * 4  # 3 -> 7
            mood = min(10, max(1, int(base_mood + random.randint(-1, 1))))
        elif mood_trend == "fluctuating":
            # Fluctuate between 2 and 7
            mood = random.randint(2, 7)
        else:  # stable
            # Stay around 6-7
            mood = random.randint(5, 8)

        sleep_hours = round(random.uniform(4.5, 8.5), 1)
        sleep_quality = random.randint(2, 5) if sleep_hours >= 6 else random.randint(1, 3)
        medication_taken = random.random() > 0.1  # 90% compliance

        notes_options = [
            None,
            "Feeling a bit better today",
            "Had a productive day",
            "Struggled with anxiety in the morning",
            "Good therapy session",
            "Spent time with friends",
            "Difficult day, but managed",
            "Practiced breathing exercises",
            "Went for a long walk",
            "Wrote in my journal",
        ]

        checkins.append({
            "checkin_date": checkin_date,
            "mood_score": mood,
            "sleep_hours": sleep_hours,
            "sleep_quality": sleep_quality,
            "medication_taken": medication_taken,
            "notes": random.choice(notes_options),
        })

    return checkins


def generate_phq9_responses(severity: str) -> tuple:
    """Generate PHQ-9 assessment responses based on severity."""
    # PHQ-9 has 9 questions, each scored 0-3
    if severity == "SEVERE":
        responses = {f"q{i}": random.randint(2, 3) for i in range(1, 10)}
        responses["q9"] = 2  # Suicidal ideation question
    elif severity == "MODERATE":
        responses = {f"q{i}": random.randint(1, 2) for i in range(1, 10)}
        responses["q9"] = random.randint(0, 1)
    else:  # MILD or MINIMAL
        responses = {f"q{i}": random.randint(0, 1) for i in range(1, 10)}
        responses["q9"] = 0

    total = sum(responses.values())

    if total >= 20:
        severity_level = SeverityLevel.SEVERE
    elif total >= 15:
        severity_level = SeverityLevel.MODERATELY_SEVERE
    elif total >= 10:
        severity_level = SeverityLevel.MODERATE
    elif total >= 5:
        severity_level = SeverityLevel.MILD
    else:
        severity_level = SeverityLevel.MINIMAL

    risk_flags = ["suicidal_ideation"] if responses["q9"] >= 2 else None

    return responses, total, severity_level, risk_flags


def generate_gad7_responses(severity: str) -> tuple:
    """Generate GAD-7 assessment responses based on severity."""
    # GAD-7 has 7 questions, each scored 0-3
    if severity == "SEVERE":
        responses = {f"q{i}": random.randint(2, 3) for i in range(1, 8)}
    elif severity == "MODERATE":
        responses = {f"q{i}": random.randint(1, 2) for i in range(1, 8)}
    else:
        responses = {f"q{i}": random.randint(0, 1) for i in range(1, 8)}

    total = sum(responses.values())

    if total >= 15:
        severity_level = SeverityLevel.SEVERE
    elif total >= 10:
        severity_level = SeverityLevel.MODERATE
    elif total >= 5:
        severity_level = SeverityLevel.MILD
    else:
        severity_level = SeverityLevel.MINIMAL

    return responses, total, severity_level, None


async def seed_demo_data():
    """Main function to seed demo data."""
    print("=" * 60)
    print("Starting Demo Data Seed for 心守AI")
    print("=" * 60)

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        try:
            # ==================== CREATE DOCTORS ====================
            print("\n[1/8] Creating doctor accounts...")
            doctors = []

            for doc_data in DEMO_DOCTORS:
                user = User(
                    id=str(uuid4()),
                    email=doc_data["email"],
                    password_hash=hash_password(DEMO_PASSWORD),
                    user_type=UserType.DOCTOR,
                    is_active=True,
                )
                db.add(user)
                await db.flush()

                doctor = Doctor(
                    id=str(uuid4()),
                    user_id=user.id,
                    first_name=doc_data["first_name"],
                    last_name=doc_data["last_name"],
                    specialty=doc_data["specialty"],
                    license_number=doc_data["license_number"],
                    phone=doc_data["phone"],
                    bio=doc_data["bio"],
                    years_of_experience=doc_data["years_of_experience"],
                    education=doc_data["education"],
                    languages=doc_data["languages"],
                    clinic_name=doc_data["clinic_name"],
                    clinic_address=doc_data["clinic_address"],
                    clinic_city=doc_data["clinic_city"],
                    clinic_country=doc_data["clinic_country"],
                    consultation_hours=doc_data["consultation_hours"],
                )
                db.add(doctor)
                doctors.append(doctor)
                print(f"  ✓ Created Dr. {doc_data['first_name']} {doc_data['last_name']} ({doc_data['email']})")

            await db.flush()

            # ==================== CREATE PATIENTS ====================
            print("\n[2/8] Creating patient accounts...")
            patients = []

            for i, pat_data in enumerate(DEMO_PATIENTS):
                user = User(
                    id=str(uuid4()),
                    email=pat_data["email"],
                    password_hash=hash_password(DEMO_PASSWORD),
                    user_type=UserType.PATIENT,
                    is_active=True,
                )
                db.add(user)
                await db.flush()

                # Assign primary doctor: first two patients to Dr. Wang, third to Dr. Chen
                primary_doctor = doctors[0] if i < 2 else doctors[1]

                patient = Patient(
                    id=str(uuid4()),
                    user_id=user.id,
                    first_name=pat_data["first_name"],
                    last_name=pat_data["last_name"],
                    date_of_birth=pat_data["date_of_birth"],
                    phone=pat_data["phone"],
                    gender=pat_data["gender"],
                    preferred_language=pat_data["preferred_language"],
                    address=pat_data["address"],
                    city=pat_data["city"],
                    country=pat_data["country"],
                    current_medications=pat_data["current_medications"],
                    medical_conditions=pat_data["medical_conditions"],
                    allergies=pat_data["allergies"],
                    therapy_history=pat_data["therapy_history"],
                    mental_health_goals=pat_data["mental_health_goals"],
                    support_system=pat_data["support_system"],
                    triggers_notes=pat_data["triggers_notes"],
                    coping_strategies=pat_data["coping_strategies"],
                    emergency_contact=pat_data["emergency_contact"],
                    emergency_phone=pat_data["emergency_phone"],
                    emergency_contact_relationship=pat_data["emergency_contact_relationship"],
                    consent_signed=pat_data["consent_signed"],
                    consent_signed_at=datetime.utcnow() - timedelta(days=30),
                    primary_doctor_id=primary_doctor.id,
                )
                db.add(patient)
                patients.append((patient, pat_data))
                print(f"  ✓ Created Patient {pat_data['first_name']} {pat_data['last_name']} ({pat_data['email']})")

            await db.flush()

            # ==================== CREATE DAILY CHECK-INS ====================
            print("\n[3/8] Creating daily check-in history (30 days)...")

            for patient, pat_data in patients:
                checkins = generate_checkin_data(pat_data["mood_trend"], days=30)
                for checkin_data in checkins:
                    checkin = DailyCheckin(
                        id=str(uuid4()),
                        patient_id=patient.id,
                        **checkin_data
                    )
                    db.add(checkin)
                print(f"  ✓ Created 30 check-ins for {patient.first_name} {patient.last_name}")

            await db.flush()

            # ==================== CREATE ASSESSMENTS ====================
            print("\n[4/8] Creating psychological assessments...")

            assessment_dates = [
                datetime.utcnow() - timedelta(days=28),
                datetime.utcnow() - timedelta(days=14),
                datetime.utcnow() - timedelta(days=3),
            ]

            for patient, pat_data in patients:
                risk_level = pat_data["risk_level"]
                severity_map = {"HIGH": "SEVERE", "MEDIUM": "MODERATE", "LOW": "MILD"}
                severity = severity_map[risk_level]

                # Create PHQ-9 assessments
                for i, assess_date in enumerate(assessment_dates):
                    # Severity improves over time for improving mood
                    if pat_data["mood_trend"] == "improving" and i > 0:
                        severity = "MODERATE" if i == 1 else "MILD"

                    responses, total, severity_level, risk_flags = generate_phq9_responses(severity)
                    assessment = Assessment(
                        id=str(uuid4()),
                        patient_id=patient.id,
                        assessment_type=AssessmentType.PHQ9,
                        responses_json=json.dumps(responses),
                        total_score=total,
                        severity=severity_level,
                        risk_flags_json=json.dumps(risk_flags) if risk_flags else None,
                        created_at=assess_date,
                    )
                    db.add(assessment)

                # Create GAD-7 assessment (most recent)
                responses, total, severity_level, _ = generate_gad7_responses(severity)
                assessment = Assessment(
                    id=str(uuid4()),
                    patient_id=patient.id,
                    assessment_type=AssessmentType.GAD7,
                    responses_json=json.dumps(responses),
                    total_score=total,
                    severity=severity_level,
                    created_at=datetime.utcnow() - timedelta(days=5),
                )
                db.add(assessment)

                print(f"  ✓ Created 4 assessments for {patient.first_name} {patient.last_name}")

            await db.flush()

            # ==================== CREATE CONVERSATIONS AND RISK EVENTS ====================
            print("\n[5/8] Creating AI conversations and risk events...")

            for patient, pat_data in patients:
                risk_level = pat_data["risk_level"]
                messages = SAMPLE_CONVERSATIONS[risk_level]

                conversation = Conversation(
                    id=str(uuid4()),
                    patient_id=patient.id,
                    conv_type=ConversationType.SUPPORTIVE_CHAT,
                    messages_json=json.dumps(messages),
                    is_active=True,
                    created_at=datetime.utcnow() - timedelta(hours=2),
                )
                db.add(conversation)
                await db.flush()

                # Create risk event for HIGH and MEDIUM risk patients
                if risk_level in ["HIGH", "MEDIUM"]:
                    risk_event = RiskEvent(
                        id=str(uuid4()),
                        patient_id=patient.id,
                        conversation_id=conversation.id,
                        risk_level=RiskLevel.CRITICAL if risk_level == "HIGH" else RiskLevel.MEDIUM,
                        risk_type=RiskType.SUICIDAL if risk_level == "HIGH" else RiskType.OTHER,
                        trigger_text=messages[2]["content"] if len(messages) > 2 else messages[0]["content"],
                        ai_confidence=0.92 if risk_level == "HIGH" else 0.75,
                        doctor_reviewed=False,
                        created_at=datetime.utcnow() - timedelta(hours=1),
                    )
                    db.add(risk_event)
                    print(f"  ✓ Created conversation + RISK EVENT for {patient.first_name} {patient.last_name}")
                else:
                    print(f"  ✓ Created conversation for {patient.first_name} {patient.last_name}")

            await db.flush()

            # ==================== CREATE CONNECTIONS ====================
            print("\n[6/8] Creating doctor-patient connections...")

            # All patients are already connected (primary_doctor_id set)
            # Create accepted connection requests for record
            for patient, pat_data in patients:
                connection = PatientConnectionRequest(
                    id=str(uuid4()),
                    doctor_id=patient.primary_doctor_id,
                    patient_id=patient.id,
                    status=ConnectionStatus.ACCEPTED,
                    message="Welcome to our mental health support program. I'm here to help you on your journey.",
                    created_at=datetime.utcnow() - timedelta(days=30),
                    responded_at=datetime.utcnow() - timedelta(days=29),
                )
                db.add(connection)

            print(f"  ✓ Created {len(patients)} doctor-patient connections")
            await db.flush()

            # ==================== CREATE MESSAGE THREADS ====================
            print("\n[7/8] Creating message threads and messages...")

            sample_messages = [
                ("DOCTOR", "Welcome! I've reviewed your intake information. Please feel free to message me anytime you need support."),
                ("PATIENT", "Thank you, doctor. I appreciate you taking the time to help me."),
                ("DOCTOR", "Of course. I noticed from your check-ins that you've been having some difficulty sleeping. Would you like to discuss this in our next session?"),
                ("PATIENT", "Yes, that would be helpful. The nightmares have been getting worse lately."),
                ("DOCTOR", "I understand. Let's schedule a session to work on some strategies together. In the meantime, try the breathing exercises we discussed."),
            ]

            for patient, pat_data in patients:
                thread = DoctorPatientThread(
                    id=str(uuid4()),
                    doctor_id=patient.primary_doctor_id,
                    patient_id=patient.id,
                    last_message_at=datetime.utcnow() - timedelta(hours=3),
                    doctor_unread_count=1,
                    patient_unread_count=0,
                )
                db.add(thread)
                await db.flush()

                # Add messages
                for i, (sender_type, content) in enumerate(sample_messages):
                    sender_id = patient.primary_doctor_id if sender_type == "DOCTOR" else patient.id
                    message = DirectMessage(
                        id=str(uuid4()),
                        thread_id=thread.id,
                        sender_type=sender_type,
                        sender_id=sender_id,
                        content=content,
                        message_type=MessageType.TEXT,
                        is_read=i < len(sample_messages) - 1,  # Last message unread
                        created_at=datetime.utcnow() - timedelta(days=5-i, hours=random.randint(0, 12)),
                    )
                    db.add(message)

                print(f"  ✓ Created message thread for {patient.first_name} {patient.last_name}")

            await db.flush()

            # ==================== CREATE APPOINTMENTS ====================
            print("\n[8/8] Creating appointments...")

            appointment_data = [
                # Past appointment (completed)
                {
                    "days_offset": -7,
                    "start_time": time(10, 0),
                    "end_time": time(11, 0),
                    "status": AppointmentStatus.COMPLETED.value,
                    "type": AppointmentType.FOLLOW_UP.value,
                    "reason": "Regular follow-up session",
                    "notes": "Discussed sleep issues and coping strategies. Patient showing improvement.",
                },
                # Upcoming appointment
                {
                    "days_offset": 3,
                    "start_time": time(14, 0),
                    "end_time": time(15, 0),
                    "status": AppointmentStatus.CONFIRMED.value,
                    "type": AppointmentType.FOLLOW_UP.value,
                    "reason": "Follow-up on medication adjustment",
                },
                # Future appointment
                {
                    "days_offset": 10,
                    "start_time": time(11, 0),
                    "end_time": time(12, 0),
                    "status": AppointmentStatus.PENDING.value,
                    "type": AppointmentType.CONSULTATION.value,
                    "reason": "Monthly check-in",
                },
            ]

            for patient, pat_data in patients:
                for appt_data in appointment_data:
                    appointment = Appointment(
                        id=str(uuid4()),
                        doctor_id=patient.primary_doctor_id,
                        patient_id=patient.id,
                        appointment_date=date.today() + timedelta(days=appt_data["days_offset"]),
                        start_time=appt_data["start_time"],
                        end_time=appt_data["end_time"],
                        status=appt_data["status"],
                        appointment_type=appt_data["type"],
                        reason=appt_data["reason"],
                        notes=appt_data.get("notes"),
                    )
                    db.add(appointment)

                print(f"  ✓ Created 3 appointments for {patient.first_name} {patient.last_name}")

            # Commit all changes
            await db.commit()

            print("\n" + "=" * 60)
            print("Demo Data Seed Complete!")
            print("=" * 60)
            print("\n📋 DEMO ACCOUNT CREDENTIALS")
            print("-" * 40)
            print(f"Password for all accounts: {DEMO_PASSWORD}")
            print("\n👨‍⚕️ DOCTOR ACCOUNTS:")
            for doc in DEMO_DOCTORS:
                print(f"  • {doc['email']}")
            print("\n👤 PATIENT ACCOUNTS:")
            for pat in DEMO_PATIENTS:
                print(f"  • {pat['email']} ({pat['risk_level']} risk)")
            print("-" * 40)

        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
