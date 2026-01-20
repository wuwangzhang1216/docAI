# Heart Guardian AI - Mental Health Support Platform

An AI-powered mental health support platform designed for political trauma survivors (refugees, dissidents, etc.), providing emotional support conversations, health tracking, psychological assessments, and doctor-patient collaboration features.

## Key Features

- **AI Emotional Support**: 24/7 streaming AI conversations powered by Anthropic Claude with on-demand context loading (~84% token reduction)
- **Multi-Level Risk Detection**: Automatic detection of CRITICAL/HIGH/MEDIUM/LOW risk content with confidence scoring, supporting 5 languages (Chinese/English/Persian/Turkish/Spanish)
- **Political Trauma-Specific Detection**: Specialized detection for exile despair, survivor's guilt, persecution fear, and other trauma patterns
- **Health Tracking**: Daily check-ins recording mood scores (0-10), sleep hours/quality, and medication adherence
- **Professional Assessments**: PHQ-9, GAD-7, PSS, ISI, PCL-5 standardized psychological assessment scales with severity levels
- **Doctor AI Assistant**: AI-assisted patient analysis with automatic clinical context aggregation
- **Real-Time Messaging**: WebSocket-based doctor-patient communication with file attachments
- **Appointment Management**: Full scheduling system with calendar views, reminders, and completion tracking
- **Report Generation**: Pre-visit summary PDF generation with patient data, trends, and AI recommendations
- **Data Export**: GDPR-compliant multi-format export (JSON/CSV/PDF) with selective data options
- **Email Notifications**: Risk alerts, password reset, patient invitations with queue system
- **Multi-Language Support**: 12+ languages with next-intl
- **PWA Offline Support**: Progressive Web App with offline capabilities
- **Responsive Design**: Mobile-first design with dark/light theme switching

## Tech Stack

### Backend
- **Framework**: FastAPI 0.109.2 (Python async web framework)
- **ORM**: SQLAlchemy 2.0.25 (async support)
- **Database**: PostgreSQL 15 (production) / SQLite (development)
- **Cache**: Redis 7
- **Object Storage**: MinIO (S3 compatible)
- **AI**: Anthropic Claude API
- **Authentication**: JWT (python-jose) + bcrypt
- **PDF Generation**: ReportLab 4.0.8
- **Email**: aiosmtplib + Jinja2 templates
- **WebSocket**: Real-time messaging with heartbeat
- **Server**: Uvicorn 0.27.1 (ASGI)

### Frontend
- **Framework**: Next.js 14.1 (App Router)
- **Language**: TypeScript 5.3.3
- **React**: 18.2.0
- **Styling**: Tailwind CSS 3.4.1 + CSS variable themes
- **UI Components**: Radix UI + Headless UI
- **Animation**: Framer Motion
- **State Management**: Zustand
- **Internationalization**: next-intl
- **PWA**: @ducanh2912/next-pwa

## Project Structure

```
docAI/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/                # API route modules
│   │   │   ├── auth.py         # Authentication (login/register/password management)
│   │   │   ├── chat.py         # AI conversations (streaming SSE)
│   │   │   ├── clinical.py     # Clinical data (check-ins/assessments/doctor-patient)
│   │   │   ├── messaging.py    # Messaging system (doctor-patient communication)
│   │   │   ├── appointments.py # Appointment management
│   │   │   ├── reports.py      # Report generation
│   │   │   ├── data_export.py  # Data export
│   │   │   └── websocket.py    # WebSocket real-time messaging
│   │   ├── models/             # SQLAlchemy ORM models (18 models)
│   │   │   ├── user.py         # Users (PATIENT/DOCTOR/ADMIN)
│   │   │   ├── patient.py      # Patient profiles
│   │   │   ├── doctor.py       # Doctor profiles
│   │   │   ├── conversation.py # AI conversation records
│   │   │   ├── doctor_conversation.py # Doctor-AI conversations
│   │   │   ├── checkin.py      # Daily check-ins
│   │   │   ├── assessment.py   # Psychological assessments
│   │   │   ├── risk_event.py   # Risk events
│   │   │   ├── appointment.py  # Appointments
│   │   │   ├── messaging.py    # Direct messages & threads
│   │   │   ├── connection_request.py # Doctor-patient connections
│   │   │   ├── pre_visit_summary.py # Pre-visit summaries
│   │   │   ├── generated_report.py # Generated reports
│   │   │   ├── data_export.py  # Data export requests
│   │   │   ├── email.py        # Email queue & password reset
│   │   │   ├── clinical_note.py # Clinical notes
│   │   │   └── audit_log.py    # Audit trail
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── services/           # Business logic
│   │   │   ├── ai/             # AI services
│   │   │   │   ├── hybrid_chat_engine.py     # Main chat engine with tools
│   │   │   │   ├── doctor_chat_engine.py     # Doctor AI assistant
│   │   │   │   ├── risk_detector.py          # Multi-language risk detection
│   │   │   │   ├── patient_context_aggregator.py # Patient context builder
│   │   │   │   ├── tools.py                  # AI tool definitions
│   │   │   │   └── prompts.py                # System prompts
│   │   │   ├── data_export/    # Data export services
│   │   │   ├── reports/        # Report generation services
│   │   │   ├── email/          # Email services
│   │   │   ├── storage.py      # S3/MinIO storage
│   │   │   └── websocket_manager.py # WebSocket connection manager
│   │   ├── utils/              # Utility functions
│   │   │   ├── security.py     # JWT/password
│   │   │   ├── deps.py         # Dependency injection
│   │   │   ├── rate_limit.py   # Rate limiting
│   │   │   └── metrics.py      # Performance metrics
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # Database connection
│   │   └── main.py             # Application entry point
│   ├── alembic/                # Database migrations (10 versions)
│   ├── tests/                  # Test suite (24 test files)
│   │   ├── unit/               # Unit tests
│   │   ├── integration/        # Integration tests
│   │   ├── performance/        # Performance tests
│   │   └── load/               # Load tests (Locust)
│   └── requirements.txt
├── frontend/                   # Next.js frontend
│   └── src/
│       ├── app/
│       │   ├── (patient)/      # Patient route group
│       │   │   ├── dashboard/  # Home dashboard
│       │   │   ├── chat/       # AI emotional support
│       │   │   ├── health/     # Health center
│       │   │   ├── checkin/    # Daily check-in
│       │   │   ├── assessment/ # Psychological assessment
│       │   │   ├── conversations/ # Conversation history
│       │   │   ├── messages/   # Doctor messages
│       │   │   ├── my-appointments/ # Appointments
│       │   │   ├── profile/    # Personal profile
│       │   │   └── data-export/ # Data export
│       │   ├── (doctor)/       # Doctor route group
│       │   │   ├── patients/   # Patient list
│       │   │   ├── patients/[id]/ # Patient details
│       │   │   ├── patients/[id]/ai-assistant/ # AI analysis
│       │   │   ├── patients/create/ # Create patient account
│       │   │   ├── risk-queue/ # Risk queue
│       │   │   ├── appointments/ # Appointment management
│       │   │   ├── doctor-messages/ # Message center
│       │   │   ├── pending-requests/ # Connection requests
│       │   │   └── my-profile/ # Doctor profile
│       │   ├── login/          # Login page
│       │   └── change-password/ # Password change
│       ├── lib/
│       │   ├── api.ts          # Type-safe API client
│       │   ├── auth.ts         # Authentication management
│       │   ├── messaging.ts    # Messaging utilities
│       │   ├── i18n.ts         # Internationalization
│       │   ├── theme.ts        # Theme management
│       │   └── utils.ts        # Helper utilities
│       ├── components/
│       │   ├── ui/             # Base UI component library
│       │   ├── chat/           # Chat components (StreamingMessage)
│       │   ├── doctor/         # Doctor-specific components
│       │   ├── messaging/      # Messaging components
│       │   └── landing/        # Landing page components
│       ├── stores/             # Zustand state stores
│       ├── hooks/              # Custom React hooks
│       └── i18n/locales/       # i18n locale files
├── docker-compose.yml          # Container orchestration
└── README.md
```

## Quick Start

### 1. Start Base Services

```bash
docker-compose up -d
```

This will start:
- **PostgreSQL 15** (port 5432) - Main database
- **Redis 7** (port 6379) - Cache and sessions
- **MinIO** (port 9000, console 9001) - Object storage

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables (copy .env.example or create .env)
# Required: ANTHROPIC_API_KEY

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

Backend service will run at http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run at http://localhost:3000

## Feature Modules

### Patient Features

| Feature | Description |
|---------|-------------|
| **AI Emotional Support** | Streaming AI conversations with real-time risk detection, on-demand context loading, and personalized responses |
| **Health Center** | Daily check-ins (mood 0-10, sleep hours/quality, medication), psychological assessment entry |
| **Psychological Assessments** | PHQ-9 (depression), GAD-7 (anxiety), PSS (stress), ISI (insomnia), PCL-5 (trauma) with severity scoring |
| **Conversation History** | View historical AI conversations with summaries |
| **Doctor-Patient Connection** | Accept/reject doctor connection requests, view assigned doctor profile |
| **Messaging System** | Real-time WebSocket messaging with doctors, supporting text/images/files |
| **Appointment Management** | View appointments, add notes, cancel appointments |
| **Data Export** | GDPR-compliant export (JSON/CSV/PDF) with selective data options |
| **Personal Profile** | Manage personal info, medical info, psychological background |

### Doctor Features

| Feature | Description |
|---------|-------------|
| **Patient List** | Patient overview with sorting by risk/mood/name, pagination |
| **Risk Queue** | Handle AI-detected risk events with priority levels (CRITICAL/HIGH/MEDIUM/LOW) |
| **Patient Details** | View check-in trends, assessment records, AI conversations, pre-visit summaries |
| **AI-Assisted Analysis** | Dedicated AI assistant for patient analysis with automatic clinical context aggregation |
| **Report Generation** | Generate pre-visit summary PDFs with patient data, trends, and AI recommendations |
| **Messaging System** | Real-time WebSocket communication with patients |
| **Appointment Management** | Create/confirm/complete appointments, calendar view, reminders |
| **Connection Requests** | Send/manage connection requests to patients |
| **Create Patient** | Create accounts for patients (first login requires password change) |
| **Clinical Notes** | Add and manage clinical notes for patients |

## API Endpoints

### Authentication `/api/v1/auth`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | User registration |
| POST | `/login` | User login, returns JWT |
| GET | `/me` | Get current user info |
| GET | `/me/patient` | Get patient profile |
| PUT | `/me/patient` | Update patient profile |
| GET | `/me/doctor` | Get doctor profile |
| POST | `/change-password` | Change password |
| POST | `/forgot-password` | Request password reset email |
| POST | `/reset-password` | Confirm password reset |

### Conversations `/api/v1/chat`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Send message (single response) |
| POST | `/stream` | Streaming conversation (SSE) with risk detection |
| GET | `/conversations` | Get conversation list |
| GET | `/conversations/{id}` | Get conversation details with full history |
| POST | `/conversations/{id}/end` | End conversation and generate summary |
| POST | `/pre-visit` | Pre-visit information gathering |

### Clinical Data `/api/v1/clinical`

**Patient Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/checkin` | Submit daily check-in |
| GET | `/checkin/today` | Get today's check-in |
| GET | `/checkins` | Get check-in history |
| POST | `/assessment` | Submit psychological assessment |
| GET | `/assessments` | Get assessment list |
| GET | `/patient/connection-requests` | View pending doctor requests |
| POST | `/patient/connection-requests/{id}/accept` | Accept connection |
| POST | `/patient/connection-requests/{id}/reject` | Reject connection |
| GET | `/patient/my-doctor` | Get assigned doctor |
| DELETE | `/patient/disconnect-doctor` | Disconnect from doctor |
| GET | `/patient/my-doctor/profile` | Doctor profile view |

**Doctor Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/doctor/patients` | Patient list with sorting/pagination |
| GET | `/doctor/risk-queue` | Risk events priority queue |
| POST | `/doctor/risk-events/{id}/review` | Mark risk reviewed |
| GET | `/doctor/patients/{id}/profile` | Patient profile view |
| GET | `/doctor/patients/{id}/checkins` | Patient check-in trends |
| GET | `/doctor/patients/{id}/assessments` | Patient assessments |
| GET | `/doctor/patients/{id}/pre-visit-summaries` | Pre-visit records |
| GET | `/doctor/profile` | Doctor profile |
| PUT | `/doctor/profile` | Update doctor profile |
| POST | `/doctor/connection-requests` | Send connection request |
| GET | `/doctor/connection-requests` | View sent requests |
| DELETE | `/doctor/connection-requests/{id}` | Cancel request |
| POST | `/doctor/patients/{id}/ai-chat` | AI-assisted patient analysis |
| GET | `/doctor/patients/{id}/ai-conversations` | AI conversation history |
| GET | `/doctor/patients/{id}/ai-conversations/{cid}` | Conversation detail |
| POST | `/doctor/patients/{id}/ai-conversations/{cid}/summarize` | Generate summary |
| POST | `/doctor/patients` | Create patient account |

### Messaging `/api/v1/messaging`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/threads` | Get message threads |
| GET | `/threads/{id}` | Thread details and messages |
| POST | `/threads/{id}/messages` | Send message |
| POST | `/upload` | Upload attachment |
| GET | `/unread` | Unread message count |

### WebSocket `/api/v1/ws`
| Feature | Description |
|---------|-------------|
| Connection | Real-time messaging with heartbeat (30s interval) |
| Subscribe | Subscribe/unsubscribe to message threads |
| Notifications | Message notifications, read receipts |

### Appointments `/api/v1/appointments`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/doctor` | Create appointment (doctor) |
| GET | `/doctor/calendar` | Doctor calendar view |
| GET | `/doctor/list` | Doctor appointment list |
| PUT | `/doctor/{id}` | Update appointment |
| POST | `/doctor/{id}/complete` | Complete appointment |
| DELETE | `/doctor/{id}` | Cancel appointment |
| GET | `/patient/list` | Patient appointment list |
| GET | `/patient/upcoming` | Upcoming appointments |

### Reports `/api/v1/reports`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/pre-visit-summary/{id}/pdf` | Generate pre-visit PDF |
| GET | `/{id}` | Get report |
| GET | `/` | Report list |

### Data Export `/api/v1/data-export`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/request` | Request data export |
| GET | `/requests` | Export request list |
| GET | `/requests/{id}` | Export status |
| GET | `/download/{token}` | Download export file |

## Database Schema

### Main Tables (20 Tables)

| Table | Description |
|-------|-------------|
| `users` | User accounts (PATIENT/DOCTOR/ADMIN) |
| `patients` | Patient profiles (medical info, psychological background) |
| `doctors` | Doctor profiles (specialty, education, clinic info) |
| `conversations` | Patient-AI conversation records |
| `doctor_conversations` | Doctor-AI conversations about patients |
| `daily_checkins` | Daily check-ins (mood, sleep, medication) |
| `assessments` | Psychological assessments (PHQ9/GAD7/PSS/ISI/PCL5) |
| `risk_events` | Risk events (level, type, AI confidence, review status) |
| `doctor_patient_threads` | Doctor-patient message threads |
| `direct_messages` | Direct messages |
| `message_attachments` | Message file attachments |
| `appointments` | Appointment records |
| `connection_requests` | Doctor-patient connection requests |
| `pre_visit_summaries` | Pre-visit summaries |
| `generated_reports` | Generated PDF reports |
| `data_exports` | Data export requests |
| `clinical_notes` | Doctor clinical notes |
| `password_reset_tokens` | Password reset tokens |
| `email_queue` | Email delivery tracking |
| `audit_logs` | System audit trail |

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/heartguardian
# Local development can use SQLite:
# DATABASE_URL=sqlite+aiosqlite:///./heartguardian.db

# Redis
REDIS_URL=redis://localhost:6379/0

# S3 / MinIO
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=heartguardian

# Authentication
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ALGORITHM=HS256

# AI
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Application
DEBUG=true
APP_NAME=HeartGuardianAI
API_V1_PREFIX=/api/v1

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@heartguardian.com
FRONTEND_URL=http://localhost:3000
EMAIL_ENABLED=false

# Password Reset
PASSWORD_RESET_EXPIRE_HOURS=24

# File Upload
MAX_FILE_SIZE_MB=10
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Risk Detection System

### Risk Levels
| Level | Description | Handling |
|-------|-------------|----------|
| CRITICAL | Immediate danger (suicidal tonight, prepared plan) | Emergency doctor notification |
| HIGH | Serious concern (wanting to die, life meaningless) | Priority notification |
| MEDIUM | Needs attention (world-weary, persistent low mood) | Regular notification |
| LOW | Minor concern | Record for observation |

### Risk Types
- **SUICIDAL**: Suicide risk
- **SELF_HARM**: Self-harm behavior
- **VIOLENCE**: Violence tendency
- **PERSECUTION_FEAR**: Persecution fear (political trauma-specific)
- **OTHER**: Other risks

### Multi-Language Support
Risk detection supports: Chinese, English, Persian, Turkish, Spanish

### Political Trauma-Specific Patterns
- Exile despair
- Survivor's guilt
- Persecution fear
- Identity loss
- Cultural displacement

## AI Features

### Patient Chat Engine
- **Streaming SSE**: Real-time response streaming
- **On-Demand Context**: ~84% token reduction through tool-based context loading
- **Risk Detection**: Automatic risk assessment with confidence scoring
- **Conversation Memory**: Maintains context across sessions
- **Multi-Language**: Responds in user's preferred language

### Doctor AI Assistant
- **Patient Context Aggregation**: Automatic loading of relevant patient data
- **Trend Analysis**: Check-in trends, assessment patterns
- **Risk Assessment**: Historical risk event analysis
- **Conversation History**: Access to patient-AI conversation summaries
- **Clinical Recommendations**: AI-generated insights

## Frontend Page Structure

### Patient Side `/app/(patient)/`
```
/dashboard        - Home dashboard
/chat             - AI emotional support conversation
/health           - Health center
/checkin          - Daily check-in
/assessment       - Psychological assessment
/conversations    - Conversation history
/messages         - Messages with doctor
/my-appointments  - Appointment management
/profile          - Personal profile
/data-export      - Data export
```

### Doctor Side `/app/(doctor)/`
```
/patients              - Patient list
/patients/[id]         - Patient details
/patients/[id]/ai-assistant - AI analysis page
/patients/create       - Create patient account
/risk-queue            - Risk queue
/appointments          - Appointment management
/doctor-messages       - Message center
/pending-requests      - Connection requests
/my-profile            - Doctor profile
```

## Testing

### Test Structure
```
tests/
├── unit/              # Unit tests
│   ├── test_auth.py
│   ├── test_chat_engine.py
│   ├── test_clinical.py
│   ├── test_data_export.py
│   ├── test_doctor_chat_engine.py
│   ├── test_email_service.py
│   ├── test_messaging.py
│   ├── test_pdf_generator.py
│   ├── test_rate_limit.py
│   ├── test_risk_detector.py
│   ├── test_security.py
│   ├── test_storage_service.py
│   ├── test_websocket.py
│   └── test_metrics.py
├── integration/       # Integration tests
│   ├── test_patient_journey.py
│   └── test_doctor_workflow.py
├── performance/       # Performance tests
│   ├── test_api_benchmarks.py
│   └── test_database_performance.py
└── load/              # Load tests
    └── locustfile.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/unit/test_risk_detector.py

# Run load tests
locust -f tests/load/locustfile.py
```

## Deployment

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### Production Environment Considerations

1. **Security Configuration**
   - Replace `SECRET_KEY` with a strong random string
   - Change database passwords
   - Configure HTTPS
   - Set correct CORS domains

2. **Database**
   - Use PostgreSQL (not SQLite)
   - Configure database backups
   - Run migrations: `alembic upgrade head`
   - Performance indexes are included in migrations

3. **AI Features**
   - Configure `ANTHROPIC_API_KEY`
   - Consider API call rate limiting
   - Monitor token usage

4. **Email Service**
   - Configure SMTP settings
   - Set `EMAIL_ENABLED=true`
   - Test email delivery

5. **Object Storage**
   - Production environment recommends AWS S3 or dedicated MinIO cluster
   - Configure proper bucket policies

6. **Monitoring**
   - Enable audit logging
   - Configure metrics collection
   - Set up health check monitoring

## Important Notes

1. **First Login**: Patient accounts created by doctors require password change on first login
2. **New User Onboarding**: Patients see a 5-step onboarding flow on first login
3. **Risk Detection**: AI automatically detects conversation risks and notifies doctors
4. **Data Privacy**: Supports GDPR-compliant data export with rate limiting (1 per 24 hours)
5. **Offline Support**: PWA technology supports basic offline functionality
6. **Real-Time Features**: WebSocket messaging with 30-second heartbeat interval
7. **Audit Trail**: All significant actions are logged for compliance

## License

MIT License
