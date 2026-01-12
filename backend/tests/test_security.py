"""
Tests for security utilities.

Covers:
- Password hashing and verification
- JWT token creation and validation
- Token expiration
"""

import pytest
from datetime import timedelta
from jose import jwt, JWTError
import time

from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token
)
from app.config import settings


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a hash."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_different_each_time(self):
        """Test that same password creates different hashes (due to salt)."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts = different hashes

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_password(self):
        """Test verifying empty password against hash."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False

    def test_hash_empty_password(self):
        """Test hashing empty password."""
        hashed = hash_password("")
        assert hashed is not None
        assert verify_password("", hashed) is True

    def test_hash_unicode_password(self):
        """Test hashing unicode password."""
        password = "密码测试123!@#"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_hash_long_password(self):
        """Test hashing very long password."""
        password = "a" * 1000
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test creating an access token."""
        data = {"sub": "user123", "type": "PATIENT"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Test creating token with custom expiration."""
        data = {"sub": "user123"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)

        decoded = decode_token(token)
        assert decoded["sub"] == "user123"

    def test_decode_token_valid(self):
        """Test decoding a valid token."""
        data = {"sub": "user123", "type": "PATIENT", "custom": "value"}
        token = create_access_token(data)

        decoded = decode_token(token)

        assert decoded["sub"] == "user123"
        assert decoded["type"] == "PATIENT"
        assert decoded["custom"] == "value"
        assert "exp" in decoded

    def test_decode_token_invalid(self):
        """Test decoding an invalid token raises error."""
        with pytest.raises(JWTError):
            decode_token("invalid.token.here")

    def test_decode_token_wrong_signature(self):
        """Test decoding token with wrong signature."""
        # Create token with different secret
        data = {"sub": "user123"}
        fake_token = jwt.encode(data, "wrong-secret", algorithm="HS256")

        with pytest.raises(JWTError):
            decode_token(fake_token)

    def test_token_expiration(self):
        """Test that expired token raises error."""
        data = {"sub": "user123"}
        # Create token that expires immediately
        expires = timedelta(seconds=-1)  # Already expired
        token = create_access_token(data, expires_delta=expires)

        with pytest.raises(JWTError):
            decode_token(token)

    def test_token_contains_expiration(self):
        """Test that token contains expiration claim."""
        data = {"sub": "user123"}
        token = create_access_token(data)

        decoded = decode_token(token)

        assert "exp" in decoded
        assert decoded["exp"] > time.time()  # Should be in the future

    def test_token_preserves_original_data(self):
        """Test that encoding/decoding preserves data."""
        original_data = {
            "sub": "user-uuid-123",
            "type": "DOCTOR",
            "email": "test@test.com"
        }
        token = create_access_token(original_data)
        decoded = decode_token(token)

        for key, value in original_data.items():
            assert decoded[key] == value

    def test_token_different_algorithms_fail(self):
        """Test that token with different algorithm fails."""
        data = {"sub": "user123"}
        # Create token with different algorithm
        wrong_algo_token = jwt.encode(
            data,
            settings.SECRET_KEY,
            algorithm="HS384"  # Different from HS256
        )

        with pytest.raises(JWTError):
            decode_token(wrong_algo_token)


class TestTokenDataIntegrity:
    """Test token data integrity and edge cases."""

    def test_token_with_special_characters(self):
        """Test token with special characters in data."""
        data = {
            "sub": "user-123",
            "name": "用户名 Test <script>",
            "emoji": "🎉"
        }
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded["name"] == "用户名 Test <script>"
        assert decoded["emoji"] == "🎉"

    def test_token_with_nested_data(self):
        """Test token with nested dictionary data."""
        data = {
            "sub": "user123",
            "profile": {
                "name": "Test User",
                "role": "admin"
            }
        }
        token = create_access_token(data)
        decoded = decode_token(token)

        assert decoded["profile"]["name"] == "Test User"
        assert decoded["profile"]["role"] == "admin"

    def test_multiple_tokens_unique(self):
        """Test that multiple tokens for same data are unique."""
        data = {"sub": "user123"}
        tokens = [create_access_token(data) for _ in range(5)]

        # All tokens should be unique (due to different exp times)
        assert len(set(tokens)) == len(tokens)
