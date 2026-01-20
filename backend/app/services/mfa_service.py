"""
MFA (Multi-Factor Authentication) Service

Provides TOTP-based two-factor authentication using pyotp.
Supports:
- TOTP setup and verification
- QR code generation for authenticator apps
- Backup codes for recovery
"""

import pyotp
import qrcode
import qrcode.image.svg
import secrets
import hashlib
import io
import base64
from datetime import datetime
from typing import Optional, Tuple, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.mfa import UserMFA, MFABackupCode
from app.models.user import User
from app.config import settings


class MFAService:
    """
    Service for managing Multi-Factor Authentication.
    """

    # Number of backup codes to generate
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8

    # App name shown in authenticator apps
    APP_NAME = "docAI"

    @classmethod
    def generate_totp_secret(cls) -> str:
        """
        Generate a new TOTP secret.

        Returns:
            Base32 encoded secret string
        """
        return pyotp.random_base32()

    @classmethod
    def get_totp_uri(cls, secret: str, email: str) -> str:
        """
        Generate the otpauth:// URI for QR codes.

        Args:
            secret: TOTP secret
            email: User's email address

        Returns:
            otpauth:// URI string
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=cls.APP_NAME)

    @classmethod
    def generate_qr_code(cls, secret: str, email: str) -> str:
        """
        Generate a QR code as a base64 encoded PNG.

        Args:
            secret: TOTP secret
            email: User's email address

        Returns:
            Base64 encoded PNG image string
        """
        uri = cls.get_totp_uri(secret, email)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    @classmethod
    def verify_totp(cls, secret: str, code: str) -> bool:
        """
        Verify a TOTP code.

        Args:
            secret: TOTP secret
            code: 6-digit code from authenticator

        Returns:
            True if code is valid, False otherwise
        """
        totp = pyotp.TOTP(secret)
        # Allow 1 code window tolerance (30 seconds before/after)
        return totp.verify(code, valid_window=1)

    @classmethod
    def generate_backup_codes(cls) -> List[str]:
        """
        Generate a set of backup codes.

        Returns:
            List of plain-text backup codes
        """
        codes = []
        for _ in range(cls.BACKUP_CODE_COUNT):
            # Generate alphanumeric code in format XXXX-XXXX
            code = secrets.token_hex(cls.BACKUP_CODE_LENGTH // 2).upper()
            formatted = f"{code[:4]}-{code[4:]}"
            codes.append(formatted)
        return codes

    @classmethod
    def hash_backup_code(cls, code: str) -> str:
        """
        Hash a backup code for storage.

        Args:
            code: Plain-text backup code

        Returns:
            Hashed code string
        """
        # Normalize: remove dashes, lowercase
        normalized = code.replace("-", "").lower()
        return hashlib.sha256(normalized.encode()).hexdigest()

    @classmethod
    async def setup_mfa(
        cls,
        db: AsyncSession,
        user: User
    ) -> Tuple[str, str, List[str]]:
        """
        Initialize MFA setup for a user.

        Creates a new MFA configuration with a TOTP secret.
        The user must verify the setup before MFA is enabled.

        Args:
            db: Database session
            user: User to set up MFA for

        Returns:
            Tuple of (secret, qr_code_base64, backup_codes)
        """
        # Check if MFA already exists
        result = await db.execute(
            select(UserMFA).where(UserMFA.user_id == user.id)
        )
        existing_mfa = result.scalar_one_or_none()

        # Generate new secret and codes
        secret = cls.generate_totp_secret()
        backup_codes = cls.generate_backup_codes()
        qr_code = cls.generate_qr_code(secret, user.email)

        if existing_mfa:
            # Update existing config (reset)
            existing_mfa.totp_secret = secret
            existing_mfa.is_enabled = False
            existing_mfa.is_verified = False
            existing_mfa.enabled_at = None

            # Remove old backup codes
            await db.execute(
                MFABackupCode.__table__.delete().where(
                    MFABackupCode.user_mfa_id == existing_mfa.id
                )
            )

            mfa_config = existing_mfa
        else:
            # Create new config
            mfa_config = UserMFA(
                user_id=user.id,
                totp_secret=secret,
                is_enabled=False,
                is_verified=False,
            )
            db.add(mfa_config)
            await db.flush()

        # Create backup codes
        for code in backup_codes:
            backup_code = MFABackupCode(
                user_mfa_id=mfa_config.id,
                code_hash=cls.hash_backup_code(code),
            )
            db.add(backup_code)

        await db.commit()

        return secret, qr_code, backup_codes

    @classmethod
    async def verify_and_enable_mfa(
        cls,
        db: AsyncSession,
        user: User,
        code: str
    ) -> bool:
        """
        Verify TOTP code and enable MFA.

        This is called after setup to confirm the user
        has correctly configured their authenticator app.

        Args:
            db: Database session
            user: User verifying MFA
            code: TOTP code from authenticator

        Returns:
            True if verified and enabled, False otherwise
        """
        result = await db.execute(
            select(UserMFA).where(UserMFA.user_id == user.id)
        )
        mfa_config = result.scalar_one_or_none()

        if not mfa_config:
            return False

        if not cls.verify_totp(mfa_config.totp_secret, code):
            return False

        mfa_config.is_verified = True
        mfa_config.is_enabled = True
        mfa_config.enabled_at = datetime.utcnow()

        await db.commit()
        return True

    @classmethod
    async def verify_mfa_code(
        cls,
        db: AsyncSession,
        user: User,
        code: str
    ) -> Tuple[bool, str]:
        """
        Verify an MFA code (TOTP or backup code).

        Args:
            db: Database session
            user: User to verify
            code: TOTP code or backup code

        Returns:
            Tuple of (is_valid, code_type) where code_type is "totp" or "backup"
        """
        result = await db.execute(
            select(UserMFA).where(UserMFA.user_id == user.id)
        )
        mfa_config = result.scalar_one_or_none()

        if not mfa_config or not mfa_config.is_enabled:
            return False, ""

        # Try TOTP first
        if cls.verify_totp(mfa_config.totp_secret, code):
            mfa_config.last_used_at = datetime.utcnow()
            await db.commit()
            return True, "totp"

        # Try backup code
        code_hash = cls.hash_backup_code(code)
        backup_result = await db.execute(
            select(MFABackupCode).where(
                MFABackupCode.user_mfa_id == mfa_config.id,
                MFABackupCode.code_hash == code_hash,
                MFABackupCode.is_used == False
            )
        )
        backup_code = backup_result.scalar_one_or_none()

        if backup_code:
            backup_code.is_used = True
            backup_code.used_at = datetime.utcnow()
            mfa_config.last_used_at = datetime.utcnow()
            await db.commit()
            return True, "backup"

        return False, ""

    @classmethod
    async def disable_mfa(
        cls,
        db: AsyncSession,
        user: User
    ) -> bool:
        """
        Disable MFA for a user.

        Args:
            db: Database session
            user: User to disable MFA for

        Returns:
            True if disabled, False if MFA wasn't enabled
        """
        result = await db.execute(
            select(UserMFA).where(UserMFA.user_id == user.id)
        )
        mfa_config = result.scalar_one_or_none()

        if not mfa_config:
            return False

        # Delete the MFA config and backup codes
        await db.delete(mfa_config)
        await db.commit()

        return True

    @classmethod
    async def is_mfa_enabled(
        cls,
        db: AsyncSession,
        user_id: str
    ) -> bool:
        """
        Check if MFA is enabled for a user.

        Args:
            db: Database session
            user_id: User ID to check

        Returns:
            True if MFA is enabled, False otherwise
        """
        result = await db.execute(
            select(UserMFA).where(
                UserMFA.user_id == user_id,
                UserMFA.is_enabled == True
            )
        )
        return result.scalar_one_or_none() is not None

    @classmethod
    async def get_remaining_backup_codes(
        cls,
        db: AsyncSession,
        user: User
    ) -> int:
        """
        Get the count of remaining (unused) backup codes.

        Args:
            db: Database session
            user: User to check

        Returns:
            Number of unused backup codes
        """
        result = await db.execute(
            select(UserMFA).where(UserMFA.user_id == user.id)
        )
        mfa_config = result.scalar_one_or_none()

        if not mfa_config:
            return 0

        backup_result = await db.execute(
            select(MFABackupCode).where(
                MFABackupCode.user_mfa_id == mfa_config.id,
                MFABackupCode.is_used == False
            )
        )
        return len(backup_result.scalars().all())

    @classmethod
    async def regenerate_backup_codes(
        cls,
        db: AsyncSession,
        user: User
    ) -> Optional[List[str]]:
        """
        Regenerate backup codes for a user.

        Args:
            db: Database session
            user: User to regenerate codes for

        Returns:
            List of new backup codes, or None if MFA not enabled
        """
        result = await db.execute(
            select(UserMFA).where(UserMFA.user_id == user.id)
        )
        mfa_config = result.scalar_one_or_none()

        if not mfa_config or not mfa_config.is_enabled:
            return None

        # Delete old backup codes
        await db.execute(
            MFABackupCode.__table__.delete().where(
                MFABackupCode.user_mfa_id == mfa_config.id
            )
        )

        # Generate new codes
        backup_codes = cls.generate_backup_codes()

        for code in backup_codes:
            backup_code = MFABackupCode(
                user_mfa_id=mfa_config.id,
                code_hash=cls.hash_backup_code(code),
            )
            db.add(backup_code)

        await db.commit()

        return backup_codes
