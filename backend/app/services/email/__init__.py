"""
Email service module for handling email notifications.

This module provides:
- EmailService: Core email sending and queuing service
- Specialized senders for different email types
- Background task processing for async email delivery
"""

from app.services.email.email_service import EmailService, email_service

__all__ = [
    "EmailService",
    "email_service",
]
