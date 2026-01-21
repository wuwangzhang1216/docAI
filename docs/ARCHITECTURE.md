# XinShouCai System Architecture Document

> Version: 1.0.0 | Last Updated: 2025-01

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Design Principles](#2-architecture-design-principles)
3. [System Architecture Diagrams](#3-system-architecture-diagrams)
4. [Technology Stack](#4-technology-stack)
5. [Backend Architecture](#5-backend-architecture)
6. [Frontend Architecture](#6-frontend-architecture)
7. [Database Design](#7-database-design)
8. [AI Engine Architecture](#8-ai-engine-architecture)
9. [Security Architecture](#9-security-architecture)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Monitoring & Observability](#11-monitoring--observability)
12. [Scalability Design](#12-scalability-design)

---

## 1. System Overview

### 1.1 Project Background

XinShouCai is a mental health support platform designed specifically for political trauma survivors, providing:

- **AI Emotional Support**: Intelligent conversation system powered by Claude API
- **Doctor-Patient Collaboration**: Real-time communication and clinical data management
- **Risk Detection**: Multi-language automatic risk identification and alerting
- **Clinical Data Management**: Daily check-ins, psychological assessments, clinical notes

### 1.2 Core Functional Modules

```
┌─────────────────────────────────────────────────────────────────┐
│                      XinShouCai Platform                         │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│  AI Chat    │  Clinical   │  Messaging  │ Appointments│ Reports │
│  Engine     │  Data       │             │             │         │
│  - Patient  │  - Check-in │  - Realtime │  - Create   │ - PDF   │
│  - Doctor   │  - Assess   │  - Files    │  - Remind   │ - Export│
│  - Risk     │  - Notes    │  - WebSocket│  - Calendar │ - GDPR  │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────┘
```

### 1.3 User Roles

| Role | Description | Primary Functions |
|------|-------------|-------------------|
| **Patient** | Users requiring mental health support | AI chat, daily check-ins, assessments, messaging |
| **Doctor** | Healthcare professionals | Patient management, risk queue, AI assistant, appointments |
| **Admin** | System administrators | User management, system configuration, audit logs |

---

## 2. Architecture Design Principles

### 2.1 Core Principles

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Async-First** | All I/O operations use async patterns | FastAPI + SQLAlchemy async |
| **Layered Architecture** | Clear separation of concerns | API → Service → Repository |
| **Stateless Design** | No local state in service instances | JWT + Redis session management |
| **Security-First** | Medical data protection | Encryption, audit, GDPR compliance |
| **Observability** | Full-stack monitoring | Structured logging + Metrics |

### 2.2 Design Patterns

```
┌─────────────────────────────────────────────────────────────┐
│                    Design Pattern Usage                      │
├─────────────────┬───────────────────────────────────────────┤
│ Repository      │ Data access abstraction, separates        │
│                 │ business logic from data storage          │
│ Service Layer   │ Business logic encapsulation,             │
│                 │ coordinates multiple data sources         │
│ Dependency Inj. │ FastAPI Depends, loosely coupled          │
│ Factory         │ Session factory, engine factory           │
│ Strategy        │ AI engine strategies (patient/doctor)     │
│ Observer        │ WebSocket message broadcasting            │
└─────────────────┴───────────────────────────────────────────┘
```

---

## 3. System Architecture Diagrams

### 3.1 Overall Architecture

```
                                   ┌─────────────────┐
                                   │   CDN / WAF     │
                                   └────────┬────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
            ┌───────▼───────┐       ┌───────▼───────┐       ┌───────▼───────┐
            │   Frontend    │       │   Frontend    │       │   Frontend    │
            │   (Next.js)   │       │   (Next.js)   │       │   (Next.js)   │
            └───────┬───────┘       └───────┬───────┘       └───────┬───────┘
                    │                       │                       │
                    └───────────────────────┼───────────────────────┘
                                            │
                              ┌─────────────▼─────────────┐
                              │      Load Balancer        │
                              │     (Nginx / ALB)         │
                              └─────────────┬─────────────┘
                                            │
            ┌───────────────────────────────┼───────────────────────────────┐
            │                               │                               │
    ┌───────▼───────┐               ┌───────▼───────┐               ┌───────▼───────┐
    │   Backend     │               │   Backend     │               │   Backend     │
    │   Instance 1  │               │   Instance 2  │               │   Instance N  │
    │   (FastAPI)   │               │   (FastAPI)   │               │   (FastAPI)   │
    └───────┬───────┘               └───────┬───────┘               └───────┬───────┘
            │                               │                               │
            └───────────────────────────────┼───────────────────────────────┘
                                            │
        ┌───────────────┬───────────────────┼───────────────┬───────────────┐
        │               │                   │               │               │
┌───────▼───────┐ ┌─────▼─────┐ ┌───────────▼───────────┐ ┌─▼─────┐ ┌───────▼───────┐
│  PostgreSQL   │ │   Redis   │ │    MinIO / S3         │ │Claude │ │    SMTP       │
│  (Primary)    │ │  Cluster  │ │    Object Storage     │ │  API  │ │    Server     │
└───────┬───────┘ └───────────┘ └───────────────────────┘ └───────┘ └───────────────┘
        │
┌───────▼───────┐
│  PostgreSQL   │
│  (Replica)    │
└───────────────┘
```

### 3.2 Request Flow

```
┌────────┐    ┌──────────┐    ┌────────────┐    ┌─────────┐    ┌──────────┐
│ Client │───▶│  Nginx   │───▶│  FastAPI   │───▶│ Service │───▶│ Database │
└────────┘    └──────────┘    └────────────┘    └─────────┘    └──────────┘
                   │                │                │
                   │           ┌────▼────┐      ┌────▼────┐
                   │           │  Auth   │      │  Redis  │
                   │           │Middleware│      │  Cache  │
                   │           └─────────┘      └─────────┘
                   │
              ┌────▼────┐
              │   SSL   │
              │ Termina │
              └─────────┘
```

---

## 4. Technology Stack

### 4.1 Backend Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Web Framework** | FastAPI | 0.109.2 | Async API framework |
| **ASGI Server** | Uvicorn | 0.27.1 | High-performance server |
| **ORM** | SQLAlchemy | 2.0.25 | Async database access |
| **Database** | PostgreSQL | 15 | Primary data storage |
| **Cache** | Redis | 7 | Sessions, token blacklist |
| **Object Storage** | MinIO/S3 | - | Files, reports storage |
| **AI** | Anthropic Claude | >=0.40.0 | Conversation engine |
| **Auth** | python-jose | 3.3.0 | JWT tokens |
| **Password** | passlib + bcrypt | 1.7.4 | Password hashing |
| **PDF** | ReportLab | 4.0.8 | Report generation |
| **Email** | aiosmtplib | 3.0.1 | Async email |
| **MFA** | PyOTP | 2.9.0 | Two-factor auth |

### 4.2 Frontend Technology Stack

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Framework** | Next.js | 14.1 | React full-stack framework |
| **Language** | TypeScript | 5.3.3 | Type safety |
| **UI** | Tailwind CSS | 3.4.1 | Styling system |
| **Components** | Radix UI | - | Accessible components |
| **State** | Zustand | 4.5.0 | State management |
| **i18n** | next-intl | 4.5.8 | Multi-language support |
| **PWA** | next-pwa | 10.2.9 | Offline support |

### 4.3 DevOps Technology Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Containerization** | Docker | Application packaging |
| **Orchestration** | Docker Compose | Development environment |
| **CI/CD** | GitHub Actions | Automation pipeline |
| **Code Quality** | Black, isort, flake8 | Formatting, linting |
| **Type Checking** | mypy | Static type analysis |
| **Security Scanning** | Bandit, Safety | Vulnerability detection |
| **Testing** | pytest | Unit/integration tests |
| **Load Testing** | Locust | Performance testing |

---

## 5. Backend Architecture

### 5.1 Directory Structure

```
backend/
├── app/
│   ├── api/                    # API routing layer
│   │   ├── __init__.py         # Route registration
│   │   ├── auth.py             # Auth endpoints (9)
│   │   ├── chat.py             # AI chat endpoints (6)
│   │   ├── clinical.py         # Clinical data endpoints (16)
│   │   ├── messaging.py        # Messaging endpoints (5)
│   │   ├── appointments.py     # Appointment endpoints (7)
│   │   ├── reports.py          # Report endpoints (3)
│   │   ├── data_export.py      # Export endpoints (4)
│   │   ├── websocket.py        # WebSocket endpoints
│   │   └── mfa.py              # MFA endpoints
│   │
│   ├── models/                 # Data model layer (19 models)
│   │   ├── user.py             # User model
│   │   ├── patient.py          # Patient profile
│   │   ├── doctor.py           # Doctor profile
│   │   ├── conversation.py     # Conversation records
│   │   ├── checkin.py          # Daily check-ins
│   │   ├── assessment.py       # Psychological assessments
│   │   ├── risk_event.py       # Risk events
│   │   ├── messaging.py        # Messaging related
│   │   ├── appointment.py      # Appointments
│   │   └── ...                 # Other models
│   │
│   ├── schemas/                # Pydantic validation layer
│   │   ├── auth.py             # Auth schemas
│   │   ├── patient.py          # Patient schemas
│   │   ├── clinical.py         # Clinical schemas
│   │   └── ...                 # Other schemas
│   │
│   ├── services/               # Business logic layer
│   │   ├── ai/                 # AI engine
│   │   │   ├── hybrid_chat_engine.py    # Patient chat engine
│   │   │   ├── doctor_chat_engine.py    # Doctor assistant engine
│   │   │   ├── risk_detector.py         # Risk detector
│   │   │   ├── patient_context_aggregator.py  # Context aggregation
│   │   │   ├── prompts.py               # Prompt templates
│   │   │   └── tools.py                 # AI tool definitions
│   │   │
│   │   ├── reports/            # Report services
│   │   │   ├── pdf_generator.py         # PDF generation
│   │   │   └── pre_visit_report.py      # Pre-visit report
│   │   │
│   │   ├── email/              # Email services
│   │   │   ├── email_service.py         # Email queue
│   │   │   └── email_senders.py         # Senders
│   │   │
│   │   ├── data_export/        # Data export
│   │   │   └── export_service.py        # Export service
│   │   │
│   │   ├── storage.py          # S3/MinIO storage
│   │   ├── websocket_manager.py # WebSocket management
│   │   ├── token_blacklist.py  # Token blacklist
│   │   └── mfa_service.py      # MFA service
│   │
│   ├── utils/                  # Utility functions
│   │   ├── security.py         # Security utilities
│   │   ├── rate_limit.py       # Rate limiting
│   │   └── metrics.py          # Performance metrics
│   │
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection
│   └── main.py                 # Application entry point
│
├── alembic/                    # Database migrations
│   └── versions/               # Migration versions (11)
│
├── tests/                      # Test suite
│   ├── test_auth.py            # Auth tests
│   ├── test_clinical.py        # Clinical tests
│   ├── ...                     # Other tests
│   └── conftest.py             # Test configuration
│
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
├── Dockerfile                  # Container configuration
└── pyproject.toml              # Project configuration
```

### 5.2 API Design

#### Endpoint Overview

| Prefix | Module | Endpoints | Description |
|--------|--------|-----------|-------------|
| `/api/v1/auth` | Auth | 9 | Registration, login, password management |
| `/api/v1/chat` | AI Chat | 6 | Patient/doctor AI conversations |
| `/api/v1/clinical` | Clinical | 16 | Check-ins, assessments, risks |
| `/api/v1/messaging` | Messaging | 5 | Doctor-patient messaging |
| `/api/v1/appointments` | Appointments | 7 | Appointment management |
| `/api/v1/reports` | Reports | 3 | PDF report generation |
| `/api/v1/data-export` | Export | 4 | GDPR data export |
| `/api/v1/mfa` | MFA | 3 | Two-factor authentication |
| `/api/v1/ws` | WebSocket | 1 | Real-time communication |

#### Request/Response Format

```python
# Standard success response
{
    "success": true,
    "data": { ... },
    "message": "Operation successful"
}

# Standard error response
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": [ ... ]
    }
}

# Paginated response
{
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "has_next": true
}
```

### 5.3 Middleware Chain

```
Request ──▶ CORSMiddleware ──▶ ObservabilityMiddleware ──▶ RateLimitMiddleware ──▶ Route Handler
                                                                                        │
Response ◀── CORSMiddleware ◀── ObservabilityMiddleware ◀── RateLimitMiddleware ◀───────┘
```

---

## 6. Frontend Architecture

### 6.1 Directory Structure

```
frontend/src/
├── app/                        # Next.js App Router
│   ├── (patient)/              # Patient route group
│   │   ├── dashboard/          # Patient dashboard
│   │   ├── chat/               # AI chat
│   │   ├── health/             # Health data
│   │   ├── checkin/            # Daily check-in
│   │   ├── assessment/         # Psychological assessment
│   │   ├── messages/           # Messages with doctor
│   │   ├── my-appointments/    # My appointments
│   │   ├── profile/            # Personal profile
│   │   └── data-export/        # Data export
│   │
│   ├── (doctor)/               # Doctor route group
│   │   ├── dashboard/          # Doctor dashboard
│   │   ├── patients/           # Patient list
│   │   ├── risk-queue/         # Risk queue
│   │   ├── appointments/       # Appointment management
│   │   └── ai-assistant/       # AI assistant
│   │
│   ├── login/                  # Login page
│   └── layout.tsx              # Root layout
│
├── components/                 # Reusable components
│   ├── ui/                     # Base UI components
│   ├── chat/                   # Chat components
│   ├── forms/                  # Form components
│   └── layouts/                # Layout components
│
├── lib/                        # Utility library
│   ├── api.ts                  # API client
│   ├── auth.ts                 # Auth utilities
│   └── utils.ts                # Common utilities
│
├── stores/                     # Zustand state
│   ├── authStore.ts            # Auth state
│   ├── chatStore.ts            # Chat state
│   └── uiStore.ts              # UI state
│
├── hooks/                      # Custom hooks
├── types/                      # TypeScript types
└── i18n/                       # Internationalization
```

### 6.2 State Management

```
┌─────────────────────────────────────────────────────────────┐
│                     Zustand Store                           │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  authStore  │  chatStore  │  uiStore    │  patientStore   │
│  - user     │  - messages │  - theme    │  - patients     │
│  - token    │  - typing   │  - sidebar  │  - selected     │
│  - loading  │  - stream   │  - modal    │  - filters      │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

---

## 7. Database Design

### 7.1 ER Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │   Patient   │       │   Doctor    │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │──┬───▶│ id (PK)     │       │ id (PK)     │
│ email       │  │    │ user_id(FK) │◀──────│ user_id(FK) │
│ password    │  │    │ doctor_id   │───────▶│ specialty   │
│ role        │  │    │ profile     │       │ clinic      │
│ created_at  │  │    └─────────────┘       └─────────────┘
└─────────────┘  │           │                    │
                 │           │                    │
                 │    ┌──────▼──────┐      ┌──────▼──────┐
                 │    │ Conversation │      │DoctorConv   │
                 │    ├─────────────┤      ├─────────────┤
                 │    │ patient_id  │      │ doctor_id   │
                 │    │ messages    │      │ patient_id  │
                 │    │ created_at  │      │ messages    │
                 │    └─────────────┘      └─────────────┘
                 │           │
        ┌────────┴───────────┼───────────────┐
        │                    │               │
┌───────▼───────┐    ┌───────▼───────┐ ┌─────▼─────┐
│  DailyCheckin │    │  Assessment   │ │ RiskEvent │
├───────────────┤    ├───────────────┤ ├───────────┤
│ patient_id    │    │ patient_id    │ │patient_id │
│ mood_score    │    │ type (enum)   │ │ level     │
│ sleep_hours   │    │ responses     │ │ trigger   │
│ checkin_date  │    │ total_score   │ │ reviewed  │
└───────────────┘    └───────────────┘ └───────────┘
```

### 7.2 Core Models

| Model | Description | Key Fields |
|-------|-------------|------------|
| `User` | User account | id, email, hashed_password, role |
| `Patient` | Patient profile | user_id, primary_doctor_id, background |
| `Doctor` | Doctor profile | user_id, specialty, clinic_name |
| `Conversation` | AI conversations | patient_id, messages (JSONB), type |
| `DailyCheckin` | Daily check-ins | patient_id, mood_score, sleep_hours |
| `Assessment` | Psychological assessments | patient_id, type, responses, total_score |
| `RiskEvent` | Risk events | patient_id, level, trigger_text, doctor_reviewed |
| `DirectMessage` | Direct messages | thread_id, sender_id, content |
| `Appointment` | Appointments | doctor_id, patient_id, scheduled_at, status |

### 7.3 Index Strategy

```sql
-- Check-in query optimization
CREATE INDEX ix_checkins_patient_date ON daily_checkins(patient_id, checkin_date);

-- Assessment query optimization
CREATE INDEX ix_assessments_patient_created ON assessments(patient_id, created_at DESC);
CREATE INDEX ix_assessments_type ON assessments(assessment_type);

-- Risk queue optimization (critical doctor path)
CREATE INDEX ix_risks_unreviewed ON risk_events(doctor_reviewed, created_at DESC);
CREATE INDEX ix_risks_patient_created ON risk_events(patient_id, created_at DESC);

-- Message optimization
CREATE INDEX ix_messages_thread_unread ON direct_messages(thread_id, is_read);
CREATE INDEX ix_threads_last_message ON doctor_patient_threads(last_message_at DESC);

-- Patient management optimization
CREATE INDEX ix_patients_doctor ON patients(primary_doctor_id);
```

---

## 8. AI Engine Architecture

### 8.1 Hybrid Chat Engine

```
┌─────────────────────────────────────────────────────────────────────┐
│                     HybridChatEngine                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │   Client    │───▶│  FastAPI    │───▶│  HybridChatEngine       │ │
│  │   (SSE)     │◀───│  Streaming  │◀───│  - load_context()       │ │
│  └─────────────┘    └─────────────┘    │  - detect_risk()        │ │
│                                         │  - stream_response()    │ │
│                                         └───────────┬─────────────┘ │
│                                                     │                │
│         ┌───────────────────────────────────────────┼───────────────┤
│         │                                           │               │
│  ┌──────▼──────┐  ┌──────────────┐  ┌──────────────▼──────────────┐│
│  │PatientContext│  │ RiskDetector │  │    Claude API              ││
│  │ Aggregator   │  │ (multi-lang) │  │    - Tool Use              ││
│  │              │  │              │  │    - Streaming              ││
│  └──────────────┘  └──────────────┘  └─────────────────────────────┘│
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Just-in-Time Context Strategy

Traditional approach loads full context with every request, wasting tokens:

```
Traditional: [System Prompt] + [Full Patient History] + [All Assessments] + [User Message]
             ─────────────────── 10,000+ tokens ───────────────────
```

XinShouCai uses "Just-in-Time Context" approach:

```
Optimized: [System Prompt] + [User Message] + [AI requests tools for needed data]
           ───── 1,500 tokens ─────          ─── Load on demand ───

Result: 84% token reduction
```

### 8.3 Risk Detector

```python
# Multi-language Rules + LLM Hybrid Detection
class RiskDetector:
    # Supported languages
    LANGUAGES = ["zh", "en", "fa", "tr", "es"]

    # Risk levels
    LEVELS = {
        "CRITICAL": 4,  # Immediate danger
        "HIGH": 3,      # Requires intervention
        "MEDIUM": 2,    # Needs attention
        "LOW": 1        # Minor indicators
    }

    # Detection flow
    def detect(self, text: str) -> RiskResult:
        # 1. Rule-based matching (fast)
        rule_result = self.rule_based_detect(text)

        # 2. If rules trigger high risk, verify with LLM
        if rule_result.level >= HIGH:
            llm_result = self.llm_verify(text)
            return self.merge_results(rule_result, llm_result)

        return rule_result
```

### 8.4 Doctor AI Assistant

```
┌─────────────────────────────────────────────────────────────┐
│                   DoctorChatEngine                          │
├─────────────────────────────────────────────────────────────┤
│  Input: Doctor question + Patient ID                        │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  PatientContextAggregator                               ││
│  │  - Last 7 days check-in data                            ││
│  │  - Latest assessment scores & trends                    ││
│  │  - Risk event history                                   ││
│  │  - Recent AI conversation summary                       ││
│  └─────────────────────────────────────────────────────────┘│
│                           │                                  │
│                    ┌──────▼──────┐                          │
│                    │  Claude API │                          │
│                    │  Analysis   │                          │
│                    └──────┬──────┘                          │
│                           │                                  │
│  Output: Clinical recommendations + Risk assessment +       │
│          Treatment suggestions                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Security Architecture

### 9.1 Authentication Flow

```
┌────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Client │────▶│  Login  │────▶│ Verify  │────▶│ Generate│
└────────┘     │  API    │     │ Password│     │   JWT   │
               └─────────┘     └─────────┘     └────┬────┘
                                                    │
┌────────┐     ┌─────────┐     ┌─────────┐     ┌───▼────┐
│ Client │────▶│  API    │────▶│ Verify  │◀───│ Redis  │
│ + JWT  │     │ Request │     │   JWT   │     │Blacklist│
└────────┘     └─────────┘     └─────────┘     └────────┘
```

### 9.2 Security Measures

| Layer | Measure | Implementation |
|-------|---------|----------------|
| **Transport** | HTTPS | TLS 1.3 |
| **Authentication** | JWT | HS256, 24-hour expiry |
| **Password** | Hashing | bcrypt, 12 rounds |
| **2FA** | MFA | TOTP (PyOTP) |
| **Session** | Blacklist | Redis token blacklist |
| **API** | Rate Limiting | Sliding window throttling |
| **Input** | Validation | Pydantic strict mode |
| **Output** | Sanitization | XSS prevention |
| **Audit** | Logging | Full operation audit logs |

### 9.3 GDPR Compliance

```
┌─────────────────────────────────────────────────────────────┐
│                    GDPR Data Export Flow                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. User requests export ──▶ 2. Identity verification ──▶   │
│                                   3. Create export task      │
│                                              │               │
│                                       ┌──────▼──────┐       │
│  6. Download link ◀── 5. Generate    │  Async      │       │
│     (24h valid)       download token │  Processing │       │
│                                      │  - JSON     │       │
│                                      │  - CSV      │       │
│                                      │  - PDF      │       │
│                                      └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. Deployment Architecture

### 10.1 Development Environment

```yaml
# docker-compose.yml
services:
  postgres:     # PostgreSQL 15
  redis:        # Redis 7
  minio:        # MinIO (S3-compatible)
  backend:      # FastAPI + Uvicorn
```

### 10.2 Production Environment

```
┌─────────────────────────────────────────────────────────────┐
│                      Production Environment                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ CloudFlare  │───▶│   ALB/NLB   │───▶│   ECS/K8s   │     │
│  │    CDN      │    │             │    │  Cluster    │     │
│  └─────────────┘    └─────────────┘    └──────┬──────┘     │
│                                                │             │
│         ┌──────────────────────────────────────┼─────────┐  │
│         │                                      │         │  │
│  ┌──────▼──────┐  ┌──────────────┐  ┌─────────▼────────┐│  │
│  │   RDS       │  │ ElastiCache  │  │    S3 Bucket     ││  │
│  │ PostgreSQL  │  │   Redis      │  │    (Files)       ││  │
│  │ (Multi-AZ)  │  │   Cluster    │  │                  ││  │
│  └─────────────┘  └──────────────┘  └──────────────────┘│  │
│                                                          │  │
└──────────────────────────────────────────────────────────┴──┘
```

### 10.3 Environment Configuration

| Environment | Database | Cache | Storage | Monitoring |
|-------------|----------|-------|---------|------------|
| **Development** | SQLite | Local Redis | Local MinIO | Console logs |
| **Testing** | PostgreSQL | Redis standalone | MinIO | pytest reports |
| **Staging** | RDS | ElastiCache | S3 | CloudWatch |
| **Production** | RDS Multi-AZ | Redis Cluster | S3 + CDN | Full monitoring |

---

## 11. Monitoring & Observability

### 11.1 Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Observability Stack                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Metrics    │  │    Logs      │  │   Traces     │      │
│  │  Prometheus  │  │    Loki      │  │   Jaeger     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           │                                  │
│                    ┌──────▼──────┐                          │
│                    │   Grafana   │                          │
│                    │  Dashboard  │                          │
│                    └─────────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 11.2 Key Metrics

| Category | Metric | Threshold |
|----------|--------|-----------|
| **Latency** | P50 response time | < 200ms |
| **Latency** | P95 response time | < 500ms |
| **Latency** | P99 response time | < 1000ms |
| **Throughput** | Requests/second | > 100 RPS |
| **Errors** | Error rate | < 0.1% |
| **Saturation** | CPU usage | < 70% |
| **Saturation** | Memory usage | < 80% |
| **Saturation** | DB connections | < 80% pool |

### 11.3 Alert Rules

```yaml
# Critical alerts
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
  severity: critical

- alert: HighLatency
  expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 1
  severity: warning

- alert: DatabaseConnectionExhausted
  expr: db_pool_connections_used / db_pool_connections_max > 0.8
  severity: warning

- alert: RiskEventUnreviewed
  expr: risk_events_unreviewed_count > 10
  severity: warning
```

---

## 12. Scalability Design

### 12.1 Horizontal Scaling

```
                     ┌─────────────┐
                     │ Load Balancer│
                     └──────┬──────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │Instance │         │Instance │         │Instance │
   │    1    │         │    2    │         │    N    │
   └─────────┘         └─────────┘         └─────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                     ┌──────▼──────┐
                     │    Redis    │
                     │   Cluster   │
                     └─────────────┘
```

**Scaling Strategy**:
- Stateless application instances, can scale up/down freely
- Sessions stored in Redis
- Database read/write separation

### 12.2 Database Scaling

```
┌─────────────────────────────────────────────────────────────┐
│                     Database Scaling                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐         ┌─────────────┐                    │
│  │   Primary   │────────▶│   Replica   │  Read query offload│
│  │   (Write)   │         │   (Read)    │                    │
│  └─────────────┘         └─────────────┘                    │
│         │                                                    │
│  ┌──────▼──────┐                                            │
│  │  Connection │  PgBouncer connection pooling              │
│  │    Pool     │                                            │
│  └─────────────┘                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 12.3 Caching Strategy

| Data Type | Cache Location | TTL | Strategy |
|-----------|----------------|-----|----------|
| User sessions | Redis | 24h | Write-through |
| Token blacklist | Redis | 24h | Write-through |
| Patient list | Redis | 5min | Read-through |
| Assessment results | Redis | 10min | Read-through |
| Static config | Memory | Startup | Preload |

---

## Appendix

### A. Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# S3/MinIO
S3_ENDPOINT=https://s3.amazonaws.com
S3_ACCESS_KEY=xxx
S3_SECRET_KEY=xxx
S3_BUCKET=xinshoucai

# Authentication
SECRET_KEY=<strong-password>
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI
ANTHROPIC_API_KEY=sk-ant-xxx

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=xxx
SMTP_PASSWORD=xxx
```

### B. API Versioning Strategy

- Current version: `/api/v1`
- Version evolution: URL path versioning
- Deprecation policy: 6-month notice period

### C. Related Documentation

- [API Documentation](./API.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Development Guide](./DEVELOPMENT.md)
- [Security Policy](./SECURITY.md)
