from fastapi import APIRouter

from app.api import auth, chat, clinical, messaging, reports, appointments, data_export, mfa

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router)
api_router.include_router(mfa.router)
api_router.include_router(chat.router)
api_router.include_router(clinical.router)
api_router.include_router(messaging.router)
api_router.include_router(reports.router)
api_router.include_router(appointments.router)
api_router.include_router(data_export.router)
