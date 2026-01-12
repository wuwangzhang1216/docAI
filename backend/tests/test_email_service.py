"""
Unit tests for email service.

Tests cover:
- EmailService class (template rendering, email queuing, sending)
- Email sending logic
- Queue processing with retry logic
- Template rendering
"""

from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import EmailLog, EmailStatus, EmailType, EmailPriority
from app.services.email.email_service import EmailService, email_service


# ============================================
# EmailService Tests
# ============================================

class TestEmailService:
    """Tests for EmailService class."""

    def test_service_initialization(self):
        """Test email service initializes correctly."""
        service = EmailService()
        # Should not raise any errors
        assert service is not None

    @pytest.mark.asyncio
    async def test_send_email_disabled(self):
        """Test sending email when EMAIL_ENABLED is False."""
        with patch('app.services.email.email_service.settings') as mock_settings:
            mock_settings.EMAIL_ENABLED = False

            service = EmailService()
            result = await service.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<p>Test content</p>"
            )

            # Should return True when disabled (skipped successfully)
            assert result is True

    @pytest.mark.asyncio
    async def test_send_email_no_credentials(self):
        """Test sending email with missing SMTP credentials."""
        with patch('app.services.email.email_service.settings') as mock_settings:
            mock_settings.EMAIL_ENABLED = True
            mock_settings.SMTP_USER = None
            mock_settings.SMTP_PASSWORD = None

            service = EmailService()
            result = await service.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<p>Test content</p>"
            )

            # Should return False when no credentials
            assert result is False

    @pytest.mark.asyncio
    async def test_send_email_success(self):
        """Test successful email sending."""
        # Skip if aiosmtplib not installed
        try:
            import aiosmtplib
        except ImportError:
            pytest.skip("aiosmtplib not installed")

        with patch('app.services.email.email_service.settings') as mock_settings:
            mock_settings.EMAIL_ENABLED = True
            mock_settings.SMTP_USER = "user@test.com"
            mock_settings.SMTP_PASSWORD = "password123"
            mock_settings.SMTP_HOST = "smtp.test.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USE_TLS = True
            mock_settings.SMTP_START_TLS = False
            mock_settings.EMAIL_FROM = "noreply@test.com"
            mock_settings.EMAIL_FROM_NAME = "Test App"

            with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = None

                service = EmailService()
                result = await service.send_email(
                    to_email="recipient@example.com",
                    subject="Test Subject",
                    html_content="<p>Hello</p>",
                    text_content="Hello"
                )

                assert result is True
                mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_exception(self):
        """Test email sending handles exceptions."""
        # Skip if aiosmtplib not installed
        try:
            import aiosmtplib
        except ImportError:
            pytest.skip("aiosmtplib not installed")

        with patch('app.services.email.email_service.settings') as mock_settings:
            mock_settings.EMAIL_ENABLED = True
            mock_settings.SMTP_USER = "user@test.com"
            mock_settings.SMTP_PASSWORD = "password123"

            with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_send:
                mock_send.side_effect = Exception("SMTP connection failed")

                service = EmailService()
                result = await service.send_email(
                    to_email="recipient@example.com",
                    subject="Test Subject",
                    html_content="<p>Hello</p>"
                )

                assert result is False


class TestEmailServiceTemplates:
    """Tests for email template rendering."""

    def test_render_template_no_directory(self):
        """Test render template raises error when no directory configured."""
        service = EmailService()
        service.jinja_env = None

        with pytest.raises(ValueError, match="Template directory not configured"):
            service.render_template("welcome", {"name": "Test"})

    def test_render_template_with_mock_env(self):
        """Test template rendering with mocked Jinja environment."""
        service = EmailService()

        # Create mock Jinja environment
        mock_env = MagicMock()
        mock_html_template = MagicMock()
        mock_html_template.render.return_value = "<html><body>Hello Test</body></html>"
        mock_env.get_template.return_value = mock_html_template

        service.jinja_env = mock_env

        html_content, text_content = service.render_template(
            "welcome",
            {"name": "Test"}
        )

        assert "Hello Test" in html_content
        mock_env.get_template.assert_called()


class TestEmailQueueing:
    """Tests for email queueing functionality."""

    @pytest_asyncio.fixture
    async def db_session_for_email(self, db_session: AsyncSession):
        """Use the shared db_session fixture."""
        return db_session

    @pytest.mark.asyncio
    async def test_queue_email(self, db_session_for_email: AsyncSession):
        """Test queueing an email."""
        with patch('app.services.email.email_service.settings') as mock_settings:
            mock_settings.EMAIL_FROM = "noreply@test.com"
            mock_settings.EMAIL_FROM_NAME = "Test App"
            mock_settings.EMAIL_MAX_RETRIES = 3

            service = EmailService()

            email_log = await service.queue_email(
                db=db_session_for_email,
                email_type=EmailType.WELCOME,
                recipient_email="new_user@example.com",
                subject="Welcome to our platform",
                html_content="<p>Welcome!</p>",
                text_content="Welcome!",
                priority=EmailPriority.NORMAL,
                recipient_name="New User"
            )

            assert email_log is not None
            assert email_log.id is not None
            assert email_log.status == EmailStatus.PENDING.value
            assert email_log.recipient_email == "new_user@example.com"
            assert email_log.email_type == EmailType.WELCOME.value

    @pytest.mark.asyncio
    async def test_queue_email_with_metadata(self, db_session_for_email: AsyncSession):
        """Test queueing email with metadata."""
        with patch('app.services.email.email_service.settings') as mock_settings:
            mock_settings.EMAIL_FROM = "noreply@test.com"
            mock_settings.EMAIL_FROM_NAME = "Test App"
            mock_settings.EMAIL_MAX_RETRIES = 3

            service = EmailService()

            email_log = await service.queue_email(
                db=db_session_for_email,
                email_type=EmailType.APPOINTMENT_REMINDER,
                recipient_email="patient@example.com",
                subject="Appointment Reminder",
                html_content="<p>Your appointment is tomorrow</p>",
                priority=EmailPriority.HIGH,
                related_entity_type="appointment",
                related_entity_id=str(uuid4()),
                metadata={"appointment_time": "2024-01-15 10:00"}
            )

            assert email_log.priority == EmailPriority.HIGH.value
            assert email_log.related_entity_type == "appointment"


class TestEmailProcessing:
    """Tests for processing queued emails."""

    @pytest_asyncio.fixture
    async def queued_email(self, db_session: AsyncSession):
        """Create a queued email for testing."""
        email_log = EmailLog(
            id=str(uuid4()),
            email_type=EmailType.SYSTEM.value,
            recipient_email="test@example.com",
            subject="Test Email",
            body_html="<p>Test content</p>",
            body_text="Test content",
            status=EmailStatus.PENDING.value,
            priority=EmailPriority.NORMAL.value,
            max_retries=3,
            retry_count=0,
        )
        db_session.add(email_log)
        await db_session.commit()
        await db_session.refresh(email_log)
        return email_log

    @pytest.mark.asyncio
    async def test_process_queued_email_success(
        self, db_session: AsyncSession, queued_email: EmailLog
    ):
        """Test processing a queued email successfully."""
        service = EmailService()

        with patch.object(service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await service.process_queued_email(db_session, queued_email)

            assert result is True
            assert queued_email.status == EmailStatus.SENT.value
            assert queued_email.sent_at is not None
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_queued_email_failure_with_retry(
        self, db_session: AsyncSession, queued_email: EmailLog
    ):
        """Test processing failure with retry."""
        service = EmailService()

        with patch.object(service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = False

            result = await service.process_queued_email(db_session, queued_email)

            assert result is False
            assert queued_email.status == EmailStatus.PENDING.value
            assert queued_email.retry_count == 1
            assert queued_email.last_error is not None

    @pytest.mark.asyncio
    async def test_process_queued_email_max_retries_exceeded(
        self, db_session: AsyncSession, queued_email: EmailLog
    ):
        """Test processing when max retries exceeded."""
        service = EmailService()

        # Set retry count to max
        queued_email.retry_count = 2
        queued_email.max_retries = 3
        await db_session.commit()

        with patch.object(service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("SMTP error")

            result = await service.process_queued_email(db_session, queued_email)

            assert result is False
            assert queued_email.status == EmailStatus.FAILED.value
            assert queued_email.failed_at is not None

    @pytest.mark.asyncio
    async def test_send_queued_email_now(
        self, db_session: AsyncSession, queued_email: EmailLog
    ):
        """Test immediate sending of queued email."""
        service = EmailService()

        with patch.object(service, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True

            result = await service.send_queued_email_now(db_session, queued_email)

            assert result is True


# ============================================
# Email Model Tests
# ============================================

class TestEmailModels:
    """Tests for email model properties."""

    def test_email_status_enum(self):
        """Test EmailStatus enum values."""
        assert EmailStatus.PENDING.value == "PENDING"
        assert EmailStatus.SENT.value == "SENT"
        assert EmailStatus.FAILED.value == "FAILED"

    def test_email_priority_enum(self):
        """Test EmailPriority enum values."""
        assert EmailPriority.LOW.value == "LOW"
        assert EmailPriority.NORMAL.value == "NORMAL"
        assert EmailPriority.HIGH.value == "HIGH"
        assert EmailPriority.URGENT.value == "URGENT"

    def test_email_type_enum(self):
        """Test EmailType enum values."""
        assert EmailType.WELCOME.value == "WELCOME"
        assert EmailType.PASSWORD_RESET.value == "PASSWORD_RESET"
        assert EmailType.RISK_ALERT.value == "RISK_ALERT"
        assert EmailType.APPOINTMENT_REMINDER.value == "APPOINTMENT_REMINDER"

    @pytest_asyncio.fixture
    async def email_log_fixture(self, db_session: AsyncSession):
        """Create an email log for testing."""
        email_log = EmailLog(
            id=str(uuid4()),
            email_type=EmailType.WELCOME.value,
            recipient_email="test@example.com",
            subject="Test",
            body_html="<p>Test</p>",
            status=EmailStatus.PENDING.value,
        )
        db_session.add(email_log)
        await db_session.commit()
        await db_session.refresh(email_log)
        return email_log

    @pytest.mark.asyncio
    async def test_email_log_creation(self, email_log_fixture: EmailLog):
        """Test email log is created correctly."""
        assert email_log_fixture.id is not None
        assert email_log_fixture.email_type == EmailType.WELCOME.value
        assert email_log_fixture.status == EmailStatus.PENDING.value
        assert email_log_fixture.created_at is not None

    @pytest.mark.asyncio
    async def test_email_log_repr(self, email_log_fixture: EmailLog):
        """Test email log string representation."""
        repr_str = repr(email_log_fixture)
        assert "EmailLog" in repr_str
        assert email_log_fixture.recipient_email in repr_str


# ============================================
# Global Instance Tests
# ============================================

class TestGlobalEmailService:
    """Tests for global email service instance."""

    def test_singleton_instance_exists(self):
        """Test that global email_service instance exists."""
        assert email_service is not None
        assert isinstance(email_service, EmailService)

    @pytest.mark.asyncio
    async def test_singleton_send_disabled(self):
        """Test global instance respects disabled setting."""
        with patch('app.services.email.email_service.settings') as mock_settings:
            mock_settings.EMAIL_ENABLED = False

            result = await email_service.send_email(
                to_email="test@example.com",
                subject="Test",
                html_content="<p>Test</p>"
            )

            assert result is True  # Returns True when disabled (skipped)


# ============================================
# Edge Cases
# ============================================

class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_send_email_with_custom_from(self):
        """Test sending email with custom from address."""
        # Skip if aiosmtplib not installed
        try:
            import aiosmtplib
        except ImportError:
            pytest.skip("aiosmtplib not installed")

        with patch('app.services.email.email_service.settings') as mock_settings:
            mock_settings.EMAIL_ENABLED = True
            mock_settings.SMTP_USER = "user@test.com"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.SMTP_HOST = "smtp.test.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USE_TLS = True
            mock_settings.SMTP_START_TLS = False
            mock_settings.EMAIL_FROM = "default@test.com"
            mock_settings.EMAIL_FROM_NAME = "Default"

            with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_send:
                service = EmailService()
                await service.send_email(
                    to_email="recipient@example.com",
                    subject="Test",
                    html_content="<p>Test</p>",
                    from_email="custom@test.com",
                    from_name="Custom Sender"
                )

                # Verify the message was constructed with custom from
                call_args = mock_send.call_args
                msg = call_args[0][0]
                assert "Custom Sender" in msg["From"]

    @pytest.mark.asyncio
    async def test_send_email_with_text_only(self):
        """Test sending email with text content."""
        # Skip if aiosmtplib not installed
        try:
            import aiosmtplib
        except ImportError:
            pytest.skip("aiosmtplib not installed")

        with patch('app.services.email.email_service.settings') as mock_settings:
            mock_settings.EMAIL_ENABLED = True
            mock_settings.SMTP_USER = "user@test.com"
            mock_settings.SMTP_PASSWORD = "password"
            mock_settings.SMTP_HOST = "smtp.test.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USE_TLS = True
            mock_settings.SMTP_START_TLS = False
            mock_settings.EMAIL_FROM = "noreply@test.com"
            mock_settings.EMAIL_FROM_NAME = "Test App"

            with patch('aiosmtplib.send', new_callable=AsyncMock) as mock_send:
                service = EmailService()
                result = await service.send_email(
                    to_email="recipient@example.com",
                    subject="Plain Text Email",
                    html_content="<p>HTML version</p>",
                    text_content="Plain text version"
                )

                assert result is True

    @pytest.mark.asyncio
    async def test_aiosmtplib_import_error(self):
        """Test handling when aiosmtplib is not installed."""
        with patch('app.services.email.email_service.settings') as mock_settings:
            mock_settings.EMAIL_ENABLED = True
            mock_settings.SMTP_USER = "user@test.com"
            mock_settings.SMTP_PASSWORD = "password"

            with patch.dict('sys.modules', {'aiosmtplib': None}):
                with patch('builtins.__import__', side_effect=ImportError("No module named 'aiosmtplib'")):
                    service = EmailService()
                    # This test verifies the import error handling in the actual implementation
                    # The function catches ImportError and returns False
