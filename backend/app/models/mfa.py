"""
MFA (Multi-Factor Authentication) Models

Stores TOTP secrets and backup codes for users.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid() -> str:
    return str(uuid4())


class UserMFA(Base):
    """
    Stores MFA configuration for a user.

    Each user can have one MFA configuration with:
    - A TOTP secret for authenticator apps
    - A set of backup codes for recovery
    """

    __tablename__ = "user_mfa"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # TOTP Configuration
    totp_secret = Column(String(32), nullable=False)  # Base32 encoded secret
    is_enabled = Column(Boolean, default=False, nullable=False)  # MFA only active after verification
    is_verified = Column(Boolean, default=False, nullable=False)  # User has verified setup

    # Backup codes (JSON array of hashed codes)
    backup_codes_hash = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    enabled_at = Column(DateTime, nullable=True)  # When MFA was enabled
    last_used_at = Column(DateTime, nullable=True)  # Last successful MFA verification

    # Relationship
    user = relationship("User", backref="mfa_config")

    def __repr__(self):
        return f"<UserMFA user_id={self.user_id} enabled={self.is_enabled}>"


class MFABackupCode(Base):
    """
    Individual backup codes for MFA recovery.

    Backup codes are one-time use and are marked as used when consumed.
    """

    __tablename__ = "mfa_backup_codes"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_mfa_id = Column(String, ForeignKey("user_mfa.id", ondelete="CASCADE"), nullable=False)

    # Code is stored hashed (like passwords)
    code_hash = Column(String(128), nullable=False)

    # Usage tracking
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship
    mfa_config = relationship("UserMFA", backref="backup_codes")

    def __repr__(self):
        return f"<MFABackupCode id={self.id[:8]} used={self.is_used}>"
