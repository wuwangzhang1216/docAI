"""
Tests for authentication API endpoints.

Covers:
- User registration (patient and doctor)
- User login with valid/invalid credentials
- Token validation and protected endpoints
- Password change functionality
- Password reset flow
- Doctor profile management
"""

import secrets
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import PasswordResetToken
from app.utils.security import hash_password
from tests.conftest import auth_headers


class TestRegister:
    """Test user registration endpoints."""

    @pytest.mark.asyncio
    async def test_register_patient_success(self, client: AsyncClient):
        """Test successful patient registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newpatient@test.com",
                "password": "SecurePass123!",
                "user_type": "PATIENT",
                "first_name": "New",
                "last_name": "Patient"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user_type"] == "PATIENT"
        assert "user_id" in data

    @pytest.mark.asyncio
    async def test_register_doctor_success(self, client: AsyncClient):
        """Test successful doctor registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newdoctor@test.com",
                "password": "SecurePass123!",
                "user_type": "DOCTOR",
                "first_name": "New",
                "last_name": "Doctor"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user_type"] == "DOCTOR"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_patient_user):
        """Test registration with existing email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "patient@test.com",  # Already exists from fixture
                "password": "SecurePass123!",
                "user_type": "PATIENT",
                "first_name": "Duplicate",
                "last_name": "User"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123!",
                "user_type": "PATIENT",
                "first_name": "Test",
                "last_name": "User"
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, client: AsyncClient):
        """Test registration with missing required fields."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@test.com",
                # Missing password, user_type, etc.
            }
        )

        assert response.status_code == 422


class TestLogin:
    """Test user login endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_patient_user):
        """Test successful login with valid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "patient@test.com",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user_type"] == "PATIENT"
        assert data["user_id"] == test_patient_user.id

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_patient_user):
        """Test login with incorrect password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "patient@test.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent email."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@test.com",
                "password": "anypassword"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, db_session, test_patient_user):
        """Test login with inactive user account."""
        # Deactivate user
        test_patient_user.is_active = False
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "patient@test.com",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()


class TestTokenValidation:
    """Test JWT token validation."""

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(
        self, client: AsyncClient, test_patient_user, patient_token
    ):
        """Test getting current user with valid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "patient@test.com"
        assert data["user_type"] == "PATIENT"

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers("invalid.token.here")
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_no_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401  # No credentials (Unauthorized)

    @pytest.mark.asyncio
    async def test_get_patient_profile(
        self, client: AsyncClient, test_patient_user, patient_token
    ):
        """Test getting patient profile with valid token."""
        response = await client.get(
            "/api/v1/auth/me/patient",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Test"
        assert data["last_name"] == "Patient"

    @pytest.mark.asyncio
    async def test_doctor_cannot_access_patient_profile(
        self, client: AsyncClient, test_doctor_user, doctor_token
    ):
        """Test doctor cannot access patient profile endpoint."""
        response = await client.get(
            "/api/v1/auth/me/patient",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_doctor_profile(
        self, client: AsyncClient, test_doctor_user, doctor_token
    ):
        """Test getting doctor profile with valid token."""
        response = await client.get(
            "/api/v1/auth/me/doctor",
            headers=auth_headers(doctor_token)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == "Test"
        assert data["last_name"] == "Doctor"


class TestPasswordChange:
    """Test password change functionality."""

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, client: AsyncClient, test_patient_user, patient_token
    ):
        """Test successful password change."""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers(patient_token),
            json={
                "current_password": "testpassword123",
                "new_password": "newSecurePass456!"
            }
        )

        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

        # Verify can login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "patient@test.com",
                "password": "newSecurePass456!"
            }
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(
        self, client: AsyncClient, test_patient_user, patient_token
    ):
        """Test password change with wrong current password."""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers(patient_token),
            json={
                "current_password": "wrongpassword",
                "new_password": "newSecurePass456!"
            }
        )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_change_password_same_as_current(
        self, client: AsyncClient, test_patient_user, patient_token
    ):
        """Test password change to same password fails."""
        response = await client.post(
            "/api/v1/auth/change-password",
            headers=auth_headers(patient_token),
            json={
                "current_password": "testpassword123",
                "new_password": "testpassword123"
            }
        )

        assert response.status_code == 400
        assert "different" in response.json()["detail"].lower()


class TestUpdatePatientProfile:
    """Test patient profile update functionality."""

    @pytest.mark.asyncio
    async def test_update_patient_profile(
        self, client: AsyncClient, test_patient_user, patient_token
    ):
        """Test updating patient profile."""
        response = await client.put(
            "/api/v1/auth/me/patient",
            headers=auth_headers(patient_token),
            json={
                "phone": "+1234567890",
                "address": "123 Test Street",
                "city": "Toronto",
                "country": "Canada",
                "preferred_language": "zh"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "+1234567890"
        assert data["city"] == "Toronto"
        assert data["preferred_language"] == "zh"

    @pytest.mark.asyncio
    async def test_update_patient_emergency_contact(
        self, client: AsyncClient, test_patient_user, patient_token
    ):
        """Test updating patient emergency contact info."""
        response = await client.put(
            "/api/v1/auth/me/patient",
            headers=auth_headers(patient_token),
            json={
                "emergency_contact": "Jane Doe",
                "emergency_phone": "+1987654321",
                "emergency_contact_relationship": "Spouse"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["emergency_contact"] == "Jane Doe"
        assert data["emergency_contact_relationship"] == "Spouse"

    @pytest.mark.asyncio
    async def test_update_patient_medical_info(
        self, client: AsyncClient, test_patient_user, patient_token
    ):
        """Test updating patient medical information."""
        response = await client.put(
            "/api/v1/auth/me/patient",
            headers=auth_headers(patient_token),
            json={
                "medical_conditions": "Anxiety, Insomnia",
                "current_medications": "Melatonin 3mg",
                "allergies": "Penicillin"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["medical_conditions"] == "Anxiety, Insomnia"
        assert data["allergies"] == "Penicillin"

    @pytest.mark.asyncio
    async def test_doctor_cannot_update_patient_profile(
        self, client: AsyncClient, test_doctor_user, doctor_token
    ):
        """Test doctor cannot access patient profile update."""
        response = await client.put(
            "/api/v1/auth/me/patient",
            headers=auth_headers(doctor_token),
            json={"phone": "+1234567890"}
        )

        assert response.status_code == 403


class TestPasswordReset:
    """Test password reset functionality."""

    @pytest.mark.asyncio
    async def test_forgot_password_existing_email(
        self, client: AsyncClient, test_patient_user
    ):
        """Test requesting password reset for existing email."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "patient@test.com"}
        )

        # Always returns success for security
        assert response.status_code == 200
        assert "邮件" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(
        self, client: AsyncClient
    ):
        """Test requesting password reset for non-existent email."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@test.com"}
        )

        # Always returns success to prevent email enumeration
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_password_valid_token(
        self, client: AsyncClient, test_patient_user, db_session: AsyncSession
    ):
        """Test resetting password with valid token."""
        # Create a valid reset token
        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=test_patient_user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db_session.add(reset_token)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "newSecurePass789!"
            }
        )

        assert response.status_code == 200
        assert "成功" in response.json()["message"]

        # Verify can login with new password
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "patient@test.com",
                "password": "newSecurePass789!"
            }
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, client: AsyncClient):
        """Test resetting password with invalid token."""
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid_token_here",
                "new_password": "newSecurePass789!"
            }
        )

        assert response.status_code == 400
        assert "无效" in response.json()["detail"] or "过期" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_reset_password_expired_token(
        self, client: AsyncClient, test_patient_user, db_session: AsyncSession
    ):
        """Test resetting password with expired token."""
        # Create an expired token
        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=test_patient_user.id,
            token=token,
            expires_at=datetime.utcnow() - timedelta(hours=1)  # Already expired
        )
        db_session.add(reset_token)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "newSecurePass789!"
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_used_token(
        self, client: AsyncClient, test_patient_user, db_session: AsyncSession
    ):
        """Test resetting password with already used token."""
        # Create a used token
        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=test_patient_user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            used_at=datetime.utcnow()  # Already used
        )
        db_session.add(reset_token)
        await db_session.commit()

        response = await client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": token,
                "new_password": "newSecurePass789!"
            }
        )

        assert response.status_code == 400


class TestPatientCannotAccessDoctor:
    """Test patient cannot access doctor endpoints."""

    @pytest.mark.asyncio
    async def test_patient_cannot_access_doctor_profile(
        self, client: AsyncClient, test_patient_user, patient_token
    ):
        """Test patient cannot access doctor profile endpoint."""
        response = await client.get(
            "/api/v1/auth/me/doctor",
            headers=auth_headers(patient_token)
        )

        assert response.status_code == 403


class TestLoginEdgeCases:
    """Test login edge cases."""

    @pytest.mark.asyncio
    async def test_login_doctor_success(
        self, client: AsyncClient, test_doctor_user
    ):
        """Test successful doctor login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "doctor@test.com",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_type"] == "DOCTOR"
        assert "access_token" in data

    @pytest.mark.asyncio
    async def test_login_case_insensitive_email(
        self, client: AsyncClient, test_patient_user
    ):
        """Test login with different email case."""
        # This test checks if emails are handled case-sensitively/insensitively
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "PATIENT@TEST.COM",  # Uppercase
                "password": "testpassword123"
            }
        )

        # May return 200 (case-insensitive) or 401 (case-sensitive)
        assert response.status_code in [200, 401]

    @pytest.mark.asyncio
    async def test_login_empty_password(self, client: AsyncClient, test_patient_user):
        """Test login with empty password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "patient@test.com",
                "password": ""
            }
        )

        # Should fail validation or authentication
        assert response.status_code in [400, 401, 422]


class TestRegisterEdgeCases:
    """Test registration edge cases."""

    @pytest.mark.asyncio
    async def test_register_with_short_password(self, client: AsyncClient):
        """Test registration with too short password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "shortpass@test.com",
                "password": "abc",  # Too short
                "user_type": "PATIENT",
                "first_name": "Test",
                "last_name": "User"
            }
        )

        # Should fail validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_user_type(self, client: AsyncClient):
        """Test registration with invalid user type."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalidtype@test.com",
                "password": "SecurePass123!",
                "user_type": "INVALID_TYPE",
                "first_name": "Test",
                "last_name": "User"
            }
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_with_whitespace_name(self, client: AsyncClient):
        """Test registration with names containing whitespace."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "whitespace@test.com",
                "password": "SecurePass123!",
                "user_type": "PATIENT",
                "first_name": "  John  ",
                "last_name": "  Doe  "
            }
        )

        # Should succeed and potentially trim whitespace
        assert response.status_code == 201


class TestTokenEdgeCases:
    """Test token-related edge cases."""

    @pytest.mark.asyncio
    async def test_malformed_token_format(self, client: AsyncClient):
        """Test with malformed token format."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt.token.at.all"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_bearer_prefix(self, client: AsyncClient, patient_token):
        """Test with token but missing Bearer prefix."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": patient_token}  # Missing "Bearer " prefix
        )

        # Should fail - invalid format
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_authorization_header(self, client: AsyncClient):
        """Test with empty authorization header."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": ""}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_bearer_only_no_token(self, client: AsyncClient):
        """Test with only 'Bearer' but no token."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer "}
        )

        assert response.status_code == 401
