"""
MFA (Multi-Factor Authentication) API Endpoints

Provides endpoints for:
- Setting up MFA (TOTP)
- Verifying MFA during login
- Managing backup codes
- Disabling MFA
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services.mfa_service import MFAService
from app.utils.deps import get_current_active_user

router = APIRouter(prefix="/mfa", tags=["mfa"])


# ========== Schemas ==========


class MFASetupResponse(BaseModel):
    """Response after initiating MFA setup."""

    secret: str  # For manual entry
    qr_code: str  # Base64 encoded QR code image
    backup_codes: List[str]  # One-time backup codes
    message: str


class MFAVerifyRequest(BaseModel):
    """Request to verify MFA code."""

    code: str = Field(..., min_length=6, max_length=10)


class MFAVerifyResponse(BaseModel):
    """Response after verifying MFA code."""

    success: bool
    message: str


class MFAStatusResponse(BaseModel):
    """MFA status for the current user."""

    is_enabled: bool
    is_verified: bool
    remaining_backup_codes: int
    enabled_at: Optional[str]


class BackupCodesResponse(BaseModel):
    """Response with new backup codes."""

    backup_codes: List[str]
    message: str


# ========== Endpoints ==========


@router.post("/setup", response_model=MFASetupResponse)
async def setup_mfa(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Initialize MFA setup for the current user.

    Returns a TOTP secret, QR code, and backup codes.
    The user must verify the setup by providing a valid code
    before MFA is actually enabled.

    **Important:** Save the backup codes securely. They cannot be
    retrieved again and are needed if you lose access to your
    authenticator app.
    """
    secret, qr_code, backup_codes = await MFAService.setup_mfa(db, current_user)

    return MFASetupResponse(
        secret=secret,
        qr_code=qr_code,
        backup_codes=backup_codes,
        message="Scan the QR code with your authenticator app, then verify with a code",
    )


@router.post("/verify-setup", response_model=MFAVerifyResponse)
async def verify_mfa_setup(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify MFA setup and enable it.

    After scanning the QR code and adding to your authenticator app,
    provide a code to verify the setup is correct.

    Once verified, MFA will be required for all future logins.
    """
    success = await MFAService.verify_and_enable_mfa(db, current_user, request.code)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please try again.",
        )

    return MFAVerifyResponse(success=True, message="MFA has been enabled successfully")


@router.get("/status", response_model=MFAStatusResponse)
async def get_mfa_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the current MFA status for the user.

    Returns whether MFA is enabled and how many backup codes remain.
    """
    from sqlalchemy import select

    from app.models.mfa import UserMFA

    result = await db.execute(select(UserMFA).where(UserMFA.user_id == current_user.id))
    mfa_config = result.scalar_one_or_none()

    if not mfa_config:
        return MFAStatusResponse(
            is_enabled=False,
            is_verified=False,
            remaining_backup_codes=0,
            enabled_at=None,
        )

    remaining = await MFAService.get_remaining_backup_codes(db, current_user)

    return MFAStatusResponse(
        is_enabled=mfa_config.is_enabled,
        is_verified=mfa_config.is_verified,
        remaining_backup_codes=remaining,
        enabled_at=mfa_config.enabled_at.isoformat() if mfa_config.enabled_at else None,
    )


@router.post("/disable", response_model=MFAVerifyResponse)
async def disable_mfa(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Disable MFA for the current user.

    Requires a valid MFA code to confirm the action.
    """
    # Verify the code first
    is_valid, _ = await MFAService.verify_mfa_code(db, current_user, request.code)

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

    success = await MFAService.disable_mfa(db, current_user)

    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled")

    return MFAVerifyResponse(success=True, message="MFA has been disabled")


@router.post("/regenerate-backup-codes", response_model=BackupCodesResponse)
async def regenerate_backup_codes(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate backup codes.

    Requires a valid MFA code. All existing backup codes will be
    invalidated and new ones generated.

    **Important:** Save the new backup codes securely.
    """
    # Verify the code first
    is_valid, _ = await MFAService.verify_mfa_code(db, current_user, request.code)

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

    backup_codes = await MFAService.regenerate_backup_codes(db, current_user)

    if backup_codes is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled")

    return BackupCodesResponse(
        backup_codes=backup_codes,
        message="New backup codes generated. Save them securely.",
    )


@router.post("/verify", response_model=MFAVerifyResponse)
async def verify_mfa_code(
    request: MFAVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Verify an MFA code.

    This endpoint can be used to verify a code during login
    or for sensitive operations.

    Accepts either a TOTP code or a backup code.
    """
    is_valid, code_type = await MFAService.verify_mfa_code(db, current_user, request.code)

    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid MFA code")

    message = "Code verified successfully"
    if code_type == "backup":
        remaining = await MFAService.get_remaining_backup_codes(db, current_user)
        message = f"Backup code used. {remaining} codes remaining."

    return MFAVerifyResponse(success=True, message=message)
