from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.user import User, UserType
from app.services.token_blacklist import TokenBlacklist
from app.utils.security import decode_token

# HTTP Bearer security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Authenticated User object

    Raises:
        HTTPException: If token is invalid, blacklisted, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_revoked_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has been revoked",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")

        if user_id is None:
            raise credentials_exception

        # Check if token is blacklisted
        if jti and await TokenBlacklist.is_blacklisted(jti):
            raise token_revoked_exception

    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Active User object

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_user_type(*allowed_types: UserType) -> Callable:
    """
    Dependency factory to require specific user types.

    Args:
        allowed_types: User types that are allowed to access the endpoint

    Returns:
        Dependency function that validates user type
    """

    async def user_type_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.user_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User type {current_user.user_type} not allowed. Required: {list(allowed_types)}",
            )
        return current_user

    return user_type_checker


async def get_current_patient(
    current_user: User = Depends(require_user_type(UserType.PATIENT)),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    """
    Get the current patient profile.

    Args:
        current_user: Current authenticated user (must be PATIENT)
        db: Database session

    Returns:
        Patient profile object

    Raises:
        HTTPException: If patient profile not found
    """
    result = await db.execute(select(Patient).where(Patient.user_id == current_user.id))
    patient = result.scalar_one_or_none()

    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient profile not found")

    return patient


async def get_current_doctor(
    current_user: User = Depends(require_user_type(UserType.DOCTOR)),
    db: AsyncSession = Depends(get_db),
) -> Doctor:
    """
    Get the current doctor profile.

    Args:
        current_user: Current authenticated user (must be DOCTOR)
        db: Database session

    Returns:
        Doctor profile object

    Raises:
        HTTPException: If doctor profile not found
    """
    result = await db.execute(select(Doctor).where(Doctor.user_id == current_user.id))
    doctor = result.scalar_one_or_none()

    if doctor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor profile not found")

    return doctor
