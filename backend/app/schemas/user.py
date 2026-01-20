from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


from app.models.user import UserType


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    password: str = Field(..., min_length=6)
    user_type: UserType
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str
    user_type: UserType
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"
    user_type: UserType
    user_id: str
    password_must_change: bool = False
    mfa_required: bool = False  # True if MFA verification is needed


class PatientCreate(BaseModel):
    """Schema for creating patient profile."""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=20)
    emergency_contact: Optional[str] = Field(None, max_length=100)
    emergency_phone: Optional[str] = Field(None, max_length=20)


class PatientUpdate(BaseModel):
    """Schema for updating patient profile."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    phone: Optional[str] = Field(None, max_length=20)
    emergency_contact: Optional[str] = Field(None, max_length=100)
    emergency_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)

    # Extended profile fields
    gender: Optional[str] = Field(None, max_length=20)
    preferred_language: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)

    # Medical information
    current_medications: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None

    # Mental health context
    therapy_history: Optional[str] = None
    mental_health_goals: Optional[str] = None
    support_system: Optional[str] = None
    triggers_notes: Optional[str] = None
    coping_strategies: Optional[str] = None


class PatientResponse(BaseModel):
    """Schema for patient response."""
    id: str
    user_id: str
    first_name: str
    last_name: str
    full_name: Optional[str] = None  # Computed property from model
    date_of_birth: Optional[date]
    phone: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    emergency_contact_relationship: Optional[str]
    primary_doctor_id: Optional[str]
    consent_signed: bool
    consent_signed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    # Extended profile fields
    gender: Optional[str]
    preferred_language: Optional[str]
    address: Optional[str]
    city: Optional[str]
    country: Optional[str]

    # Medical information
    current_medications: Optional[str]
    medical_conditions: Optional[str]
    allergies: Optional[str]

    # Mental health context
    therapy_history: Optional[str]
    mental_health_goals: Optional[str]
    support_system: Optional[str]
    triggers_notes: Optional[str]
    coping_strategies: Optional[str]

    class Config:
        from_attributes = True


class DoctorCreate(BaseModel):
    """Schema for creating doctor profile."""
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    license_number: Optional[str] = Field(None, max_length=50)
    specialty: Optional[str] = Field(None, max_length=100)


class DoctorUpdate(BaseModel):
    """Schema for updating doctor profile."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    license_number: Optional[str] = Field(None, max_length=50)
    specialty: Optional[str] = Field(None, max_length=100)

    # Contact information
    phone: Optional[str] = Field(None, max_length=20)

    # Professional information
    bio: Optional[str] = None
    years_of_experience: Optional[str] = Field(None, max_length=10)
    education: Optional[str] = None
    languages: Optional[str] = Field(None, max_length=255)

    # Clinic information
    clinic_name: Optional[str] = Field(None, max_length=200)
    clinic_address: Optional[str] = Field(None, max_length=255)
    clinic_city: Optional[str] = Field(None, max_length=100)
    clinic_country: Optional[str] = Field(None, max_length=100)

    # Availability
    consultation_hours: Optional[str] = Field(None, max_length=255)


class DoctorResponse(BaseModel):
    """Schema for doctor response."""
    id: str
    user_id: str
    first_name: str
    last_name: str
    full_name: Optional[str] = None  # Computed property from model
    license_number: Optional[str]
    specialty: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    # Contact information
    phone: Optional[str]

    # Professional information
    bio: Optional[str]
    years_of_experience: Optional[str]
    education: Optional[str]
    languages: Optional[str]

    # Clinic information
    clinic_name: Optional[str]
    clinic_address: Optional[str]
    clinic_city: Optional[str]
    clinic_country: Optional[str]

    # Availability
    consultation_hours: Optional[str]

    class Config:
        from_attributes = True


class DoctorPublicProfile(BaseModel):
    """Schema for doctor public profile (viewable by patients)."""
    id: str
    first_name: str
    last_name: str
    full_name: Optional[str] = None  # Computed property from model
    specialty: Optional[str]
    phone: Optional[str]
    bio: Optional[str]
    years_of_experience: Optional[str]
    education: Optional[str]
    languages: Optional[str]
    clinic_name: Optional[str]
    clinic_address: Optional[str]
    clinic_city: Optional[str]
    clinic_country: Optional[str]
    consultation_hours: Optional[str]

    class Config:
        from_attributes = True


# ============ Doctor creates patient schemas ============

class DoctorCreatePatient(BaseModel):
    """Schema for doctor creating a new patient account."""
    # Required fields
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

    # Optional basic info
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    preferred_language: Optional[str] = Field(None, max_length=10)

    # Emergency contact
    emergency_contact: Optional[str] = Field(None, max_length=100)
    emergency_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)

    # Medical information
    current_medications: Optional[str] = None
    medical_conditions: Optional[str] = None
    allergies: Optional[str] = None

    # Mental health context
    therapy_history: Optional[str] = None
    mental_health_goals: Optional[str] = None
    support_system: Optional[str] = None
    triggers_notes: Optional[str] = None
    coping_strategies: Optional[str] = None


class DoctorCreatePatientResponse(BaseModel):
    """Response schema for doctor creating a patient."""
    patient_id: str
    user_id: str
    email: str
    full_name: str
    default_password: str
    message: str


# ============ Password change schemas ============

class PasswordChange(BaseModel):
    """Schema for changing password."""
    current_password: str
    new_password: str = Field(..., min_length=6)
