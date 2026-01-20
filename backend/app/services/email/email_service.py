"""
Core email service for sending and queuing emails.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.email import EmailLog, EmailPriority, EmailStatus, EmailType

logger = logging.getLogger(__name__)


class EmailService:
    """
    Async email sending service.

    Supports:
    - Template rendering with Jinja2
    - Email queuing for async processing
    - Direct sending (synchronous)
    - Retry logic with exponential backoff
    """

    def __init__(self):
        # Setup Jinja2 template environment
        template_dir = Path(__file__).parent.parent.parent / "templates" / "email"
        if template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )
        else:
            self.jinja_env = None
            logger.warning(f"Email template directory not found: {template_dir}")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send a single email directly.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body content
            text_content: Plain text body (optional)
            from_email: Sender email (defaults to settings)
            from_name: Sender name (defaults to settings)

        Returns:
            bool: True if sent successfully
        """
        if not settings.EMAIL_ENABLED:
            logger.info(f"Email disabled, skipping: {subject} -> {to_email}")
            return True

        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured, skipping email")
            return False

        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            import aiosmtplib

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{from_name or settings.EMAIL_FROM_NAME} <{from_email or settings.EMAIL_FROM}>"
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS,
                start_tls=settings.SMTP_START_TLS,
            )
            logger.info(f"Email sent successfully: {subject} -> {to_email}")
            return True

        except ImportError:
            logger.error("aiosmtplib not installed. Run: pip install aiosmtplib")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    def render_template(self, template_name: str, context: Dict[str, Any]) -> tuple[str, Optional[str]]:
        """
        Render an email template.

        Args:
            template_name: Template file name (without extension)
            context: Template variables

        Returns:
            tuple: (html_content, text_content or None)
        """
        if not self.jinja_env:
            raise ValueError("Template directory not configured")

        # Render HTML template
        try:
            html_template = self.jinja_env.get_template(f"{template_name}.html")
            html_content = html_template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render HTML template {template_name}: {e}")
            raise

        # Try to render plain text template (optional)
        text_content = None
        try:
            text_template = self.jinja_env.get_template(f"{template_name}.txt")
            text_content = text_template.render(**context)
        except Exception:
            # Plain text template is optional
            pass

        return html_content, text_content

    async def queue_email(
        self,
        db: AsyncSession,
        email_type: EmailType,
        recipient_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        recipient_user_id: Optional[str] = None,
        recipient_name: Optional[str] = None,
        template_id: Optional[str] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> EmailLog:
        """
        Queue an email for async processing.

        Args:
            db: Database session
            email_type: Type of email
            recipient_email: Recipient email address
            subject: Email subject
            html_content: HTML body content
            text_content: Plain text body (optional)
            priority: Email priority level
            recipient_user_id: Optional user ID
            recipient_name: Optional recipient name
            template_id: Optional template ID
            related_entity_type: Optional related entity type
            related_entity_id: Optional related entity ID
            metadata: Optional metadata dictionary

        Returns:
            EmailLog: Created email log record
        """
        email_log = EmailLog(
            template_id=template_id,
            email_type=email_type.value,
            recipient_email=recipient_email,
            recipient_user_id=recipient_user_id,
            recipient_name=recipient_name,
            sender_email=settings.EMAIL_FROM,
            sender_name=settings.EMAIL_FROM_NAME,
            subject=subject,
            body_html=html_content,
            body_text=text_content,
            status=EmailStatus.PENDING.value,
            priority=priority.value,
            max_retries=settings.EMAIL_MAX_RETRIES,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            metadata=metadata,
        )

        db.add(email_log)
        await db.commit()
        await db.refresh(email_log)

        logger.info(f"Email queued: {email_log.id} ({email_type.value}) -> {recipient_email}")

        return email_log

    async def process_queued_email(self, db: AsyncSession, email_log: EmailLog) -> bool:
        """
        Process a queued email and send it.

        Args:
            db: Database session
            email_log: Email log record to process

        Returns:
            bool: True if sent successfully
        """
        # Update status to sending
        email_log.status = EmailStatus.SENDING.value
        email_log.queued_at = datetime.utcnow()
        await db.commit()

        try:
            success = await self.send_email(
                to_email=email_log.recipient_email,
                subject=email_log.subject,
                html_content=email_log.body_html,
                text_content=email_log.body_text,
            )

            if success:
                email_log.status = EmailStatus.SENT.value
                email_log.sent_at = datetime.utcnow()
                await db.commit()
                return True
            else:
                raise Exception("send_email returned False")

        except Exception as e:
            email_log.retry_count += 1
            email_log.last_error = str(e)[:500]

            if email_log.retry_count >= email_log.max_retries:
                email_log.status = EmailStatus.FAILED.value
                email_log.failed_at = datetime.utcnow()
                logger.error(f"Email permanently failed: {email_log.id} - {e}")
            else:
                email_log.status = EmailStatus.PENDING.value
                logger.warning(
                    f"Email failed, will retry ({email_log.retry_count}/{email_log.max_retries}): {email_log.id}"
                )

            await db.commit()
            return False

    async def send_queued_email_now(self, db: AsyncSession, email_log: EmailLog) -> bool:
        """
        Convenience method to immediately process a just-queued email.
        For cases where we want synchronous behavior.
        """
        return await self.process_queued_email(db, email_log)


# Singleton instance
email_service = EmailService()
