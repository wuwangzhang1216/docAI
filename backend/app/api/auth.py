import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import settings
from app.models.user import User, UserType
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.email import PasswordResetToken
from app.schemas.user import (
    UserCreate,
    UserLogin,
    TokenResponse,
    UserResponse,
    PatientResponse,
    PatientUpdate,
    DoctorResponse,
    PasswordChange,
)
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_token_expiration,
    get_token_jti,
    decode_token,
)
from app.utils.deps import get_current_active_user, get_current_patient, get_current_doctor
from app.services.token_blacklist import TokenBlacklist
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# HTTP Bearer for logout endpoint
security = HTTPBearer()


# Password reset schemas
class PasswordResetRequest(BaseModel):
    """Request password reset email."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""
    token: str
    new_password: str = Field(..., min_length=6)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.

    Creates a user account and corresponding profile (patient or doctor).
    Returns a JWT token for immediate authentication.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        user_type=request.user_type
    )
    db.add(user)
    await db.flush()  # Get user.id

    # Create profile based on user type
    if request.user_type == UserType.PATIENT:
        patient = Patient(
            user_id=user.id,
            first_name=request.first_name,
            last_name=request.last_name
        )
        db.add(patient)
    elif request.user_type == UserType.DOCTOR:
        doctor = Doctor(
            user_id=user.id,
            first_name=request.first_name,
            last_name=request.last_name
        )
        db.add(doctor)

    await db.commit()
    await db.refresh(user)

    # Generate token
    token = create_access_token({
        "sub": str(user.id),
        "type": user.user_type.value
    })

    return TokenResponse(
        access_token=token,
        user_type=user.user_type,
        user_id=user.id
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.

    Returns a JWT token for authentication.
    If MFA is enabled, a partial token is returned and mfa_required=True.
    The client must then call /auth/login/mfa to complete authentication.
    """
    from app.services.mfa_service import MFAService

    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Check if MFA is enabled
    mfa_enabled = await MFAService.is_mfa_enabled(db, user.id)

    # Check if password must be changed (for doctor-created accounts)
    password_must_change = getattr(user, 'password_must_change', False) or False

    if mfa_enabled:
        # Generate a temporary token for MFA verification
        # This token has limited scope and short expiration
        temp_token = create_access_token(
            {
                "sub": str(user.id),
                "type": user.user_type.value,
                "mfa_pending": True,  # Mark as pending MFA
            },
            expires_delta=timedelta(minutes=5)  # Short expiration for MFA flow
        )

        return TokenResponse(
            access_token=temp_token,
            user_type=user.user_type,
            user_id=user.id,
            password_must_change=password_must_change,
            mfa_required=True
        )

    # Generate full access token
    token = create_access_token({
        "sub": str(user.id),
        "type": user.user_type.value
    })

    return TokenResponse(
        access_token=token,
        user_type=user.user_type,
        user_id=user.id,
        password_must_change=password_must_change,
        mfa_required=False
    )


class MFALoginRequest(BaseModel):
    """Request to complete MFA login."""
    code: str = Field(..., min_length=6, max_length=10)


@router.post("/login/mfa", response_model=TokenResponse)
async def login_with_mfa(
    request: MFALoginRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Complete login with MFA verification.

    Requires the temporary token from /login and a valid MFA code.
    Returns a full access token upon successful verification.
    """
    from app.services.mfa_service import MFAService

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
        mfa_pending = payload.get("mfa_pending", False)

        if not user_id or not mfa_pending:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    # Get user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    # Verify MFA code
    is_valid, code_type = await MFAService.verify_mfa_code(db, user, request.code)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA code"
        )

    # Generate full access token
    token = create_access_token({
        "sub": str(user.id),
        "type": user.user_type.value
    })

    password_must_change = getattr(user, 'password_must_change', False) or False

    return TokenResponse(
        access_token=token,
        user_type=user.user_type,
        user_id=user.id,
        password_must_change=password_must_change,
        mfa_required=False
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout the current user by blacklisting their token.

    The token will be added to a blacklist and rejected on future requests.
    The blacklist entry automatically expires when the token would have expired.
    """
    token = credentials.credentials
    jti = get_token_jti(token)
    expires_at = get_token_expiration(token)

    if jti and expires_at:
        await TokenBlacklist.add_to_blacklist(
            jti=jti,
            expires_at=expires_at,
            user_id=str(current_user.id),
            reason="logout"
        )

    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return current_user


@router.get("/me/patient", response_model=PatientResponse)
async def get_current_patient_profile(
    patient: Patient = Depends(get_current_patient)
):
    """Get current patient profile."""
    return patient


@router.put("/me/patient", response_model=PatientResponse)
async def update_current_patient_profile(
    update_data: PatientUpdate,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db)
):
    """Update current patient profile."""
    # Update only the fields that are provided
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        setattr(patient, field, value)

    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/me/doctor", response_model=DoctorResponse)
async def get_current_doctor_profile(
    doctor: Doctor = Depends(get_current_doctor)
):
    """Get current doctor profile."""
    return doctor


@router.post("/change-password")
async def change_password(
    request: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change the current user's password.

    Requires the current password for verification.
    If the user was created by a doctor (password_must_change=True),
    this will clear that flag after successful password change.
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Check if new password is same as current
    if request.current_password == request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # Update password
    current_user.password_hash = hash_password(request.new_password)

    # Clear password_must_change flag if it was set
    if getattr(current_user, 'password_must_change', False):
        current_user.password_must_change = False

    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/forgot-password")
async def request_password_reset(
    request_body: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset email.

    For security, this endpoint always returns success even if the email
    doesn't exist, to prevent email enumeration attacks.
    """
    result = await db.execute(
        select(User).where(User.email == request_body.email)
    )
    user = result.scalar_one_or_none()

    if user:
        # Invalidate any existing tokens for this user
        existing_tokens = await db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None)
            )
        )
        for token in existing_tokens.scalars().all():
            token.used_at = datetime.utcnow()  # Mark as used

        # Generate new reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at,
            request_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", "")[:500] if request.headers else None,
        )
        db.add(reset_token)
        await db.commit()

        # Send password reset email
        try:
            from app.services.email.email_senders import send_password_reset_email
            await send_password_reset_email(
                db=db,
                user=user,
                reset_token=token,
                expires_minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES,
            )
        except Exception as e:
            # Log but don't expose error to user
            import logging
            logging.error(f"Failed to send password reset email: {e}")

    # Always return success for security
    return {"message": "如果该邮箱已注册，您将收到密码重置邮件"}


@router.post("/reset-password")
async def reset_password(
    request_body: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using a valid reset token.

    The token must be valid (not expired and not used).
    """
    # Find the reset token
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token == request_body.token,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > datetime.utcnow(),
        )
    )
    reset_token = result.scalar_one_or_none()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或已过期的重置链接"
        )

    # Get the user
    user_result = await db.execute(
        select(User).where(User.id == reset_token.user_id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户不存在"
        )

    # Update password
    user.password_hash = hash_password(request_body.new_password)

    # Clear password_must_change flag if set
    if getattr(user, 'password_must_change', False):
        user.password_must_change = False

    # Mark token as used
    reset_token.used_at = datetime.utcnow()

    await db.commit()

    return {"message": "密码重置成功"}
