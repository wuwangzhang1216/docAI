"""
Unit tests for Storage Service.

Tests file validation, S3 operations, and thumbnail generation.
Uses mocking to avoid actual S3/MinIO dependency.
"""

import io
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import pytest
from PIL import Image

from app.services.storage import StorageService


class TestStorageServiceValidation:
    """Tests for file validation logic."""

    @pytest.fixture
    def storage_service(self):
        """Create storage service with mocked S3 client."""
        with patch('app.services.storage.boto3.client') as mock_client:
            mock_client.return_value = MagicMock()
            service = StorageService()
            service._initialized = True
            return service

    def test_validate_valid_image(self, storage_service):
        """Test validation of valid image file."""
        is_valid, error = storage_service.validate_file(
            content_type="image/jpeg",
            file_size=1024 * 1024,  # 1MB
            is_image=True
        )

        assert is_valid is True
        assert error is None

    def test_validate_valid_pdf(self, storage_service):
        """Test validation of valid PDF file."""
        is_valid, error = storage_service.validate_file(
            content_type="application/pdf",
            file_size=5 * 1024 * 1024,  # 5MB
            is_image=False
        )

        assert is_valid is True
        assert error is None

    def test_validate_file_too_large(self, storage_service):
        """Test validation fails for oversized file."""
        is_valid, error = storage_service.validate_file(
            content_type="image/jpeg",
            file_size=15 * 1024 * 1024,  # 15MB > 10MB limit
            is_image=True
        )

        assert is_valid is False
        assert "exceeds" in error.lower()
        assert "10MB" in error

    def test_validate_invalid_content_type(self, storage_service):
        """Test validation fails for unsupported file type."""
        is_valid, error = storage_service.validate_file(
            content_type="application/x-executable",
            file_size=1024,
            is_image=False
        )

        assert is_valid is False
        assert "not allowed" in error.lower()

    def test_validate_image_only_rejects_pdf(self, storage_service):
        """Test image-only validation rejects PDF."""
        is_valid, error = storage_service.validate_file(
            content_type="application/pdf",
            file_size=1024,
            is_image=True  # Image-only mode
        )

        assert is_valid is False
        assert "not allowed" in error.lower()

    @pytest.mark.parametrize("content_type,expected_ext", [
        ("image/jpeg", ".jpg"),
        ("image/png", ".png"),
        ("image/gif", ".gif"),
        ("image/webp", ".webp"),
        ("application/pdf", ".pdf"),
        ("text/plain", ".txt"),
        ("unknown/type", ""),
    ])
    def test_get_extension(self, storage_service, content_type, expected_ext):
        """Test file extension lookup."""
        extension = storage_service.get_extension(content_type)
        assert extension == expected_ext

    @pytest.mark.parametrize("content_type,expected", [
        ("image/jpeg", True),
        ("image/png", True),
        ("application/pdf", False),
        ("text/plain", False),
        ("unknown/type", False),
    ])
    def test_is_image(self, storage_service, content_type, expected):
        """Test image type detection."""
        result = storage_service.is_image(content_type)
        assert result == expected


class TestStorageServiceUpload:
    """Tests for file upload functionality."""

    @pytest.fixture
    def storage_service(self):
        """Create storage service with mocked S3 client."""
        with patch('app.services.storage.boto3.client') as mock_client:
            mock_s3 = MagicMock()
            mock_client.return_value = mock_s3
            service = StorageService()
            service._initialized = True
            service.s3_client = mock_s3
            return service

    @pytest.mark.asyncio
    async def test_upload_file_success(self, storage_service):
        """Test successful file upload."""
        file_content = b"test file content"
        filename = "test.pdf"
        content_type = "application/pdf"

        s3_key, thumbnail_key = await storage_service.upload_file(
            file_content=file_content,
            filename=filename,
            content_type=content_type,
            folder="test"
        )

        assert s3_key is not None
        assert "test/" in s3_key
        assert s3_key.endswith(".pdf")
        assert thumbnail_key is None  # No thumbnail for PDF

        # Verify S3 put_object was called
        storage_service.s3_client.put_object.assert_called_once()
        call_args = storage_service.s3_client.put_object.call_args
        assert call_args.kwargs['Body'] == file_content
        assert call_args.kwargs['ContentType'] == content_type

    @pytest.mark.asyncio
    async def test_upload_image_with_thumbnail(self, storage_service):
        """Test image upload generates thumbnail."""
        # Create a test image
        img = Image.new('RGB', (500, 500), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        file_content = buffer.getvalue()

        s3_key, thumbnail_key = await storage_service.upload_file(
            file_content=file_content,
            filename="test_image.jpg",
            content_type="image/jpeg",
            folder="images"
        )

        assert s3_key is not None
        assert thumbnail_key is not None
        assert "_thumb.jpg" in thumbnail_key

        # Should have 2 uploads: main file and thumbnail
        assert storage_service.s3_client.put_object.call_count == 2

    @pytest.mark.asyncio
    async def test_upload_image_thumbnail_failure_continues(self, storage_service):
        """Test upload succeeds even if thumbnail creation fails."""
        # Create an invalid "image" that will fail thumbnail creation
        file_content = b"not a real image"

        with patch.object(storage_service, '_create_thumbnail', side_effect=Exception("Thumbnail failed")):
            s3_key, thumbnail_key = await storage_service.upload_file(
                file_content=file_content,
                filename="test.jpg",
                content_type="image/jpeg",
                folder="images"
            )

        # Main upload should succeed
        assert s3_key is not None
        # Thumbnail should be None due to failure
        assert thumbnail_key is None

    @pytest.mark.asyncio
    async def test_upload_not_initialized_raises_error(self):
        """Test upload fails when S3 not initialized."""
        with patch('app.services.storage.boto3.client') as mock_client:
            mock_client.side_effect = Exception("Connection failed")
            service = StorageService()
            service._initialized = False

            with pytest.raises(RuntimeError) as exc_info:
                await service.upload_file(
                    file_content=b"test",
                    filename="test.pdf",
                    content_type="application/pdf"
                )

            assert "not available" in str(exc_info.value)


class TestStorageServicePresignedUrl:
    """Tests for presigned URL generation."""

    @pytest.fixture
    def storage_service(self):
        """Create storage service with mocked S3 client."""
        with patch('app.services.storage.boto3.client') as mock_client:
            mock_s3 = MagicMock()
            mock_s3.generate_presigned_url.return_value = "https://s3.example.com/signed-url"
            mock_client.return_value = mock_s3
            service = StorageService()
            service._initialized = True
            service.s3_client = mock_s3
            return service

    def test_get_presigned_url_success(self, storage_service):
        """Test presigned URL generation."""
        url = storage_service.get_presigned_url("test/file.pdf")

        assert url == "https://s3.example.com/signed-url"
        storage_service.s3_client.generate_presigned_url.assert_called_once()

    def test_get_presigned_url_custom_expiry(self, storage_service):
        """Test presigned URL with custom expiry."""
        storage_service.get_presigned_url("test/file.pdf", expiry=7200)

        call_args = storage_service.s3_client.generate_presigned_url.call_args
        assert call_args.kwargs['ExpiresIn'] == 7200

    def test_get_presigned_url_not_initialized(self):
        """Test presigned URL returns None when not initialized."""
        with patch('app.services.storage.boto3.client') as mock_client:
            mock_client.side_effect = Exception("Connection failed")
            service = StorageService()
            service._initialized = False

            url = service.get_presigned_url("test/file.pdf")

            assert url is None


class TestStorageServiceDelete:
    """Tests for file deletion."""

    @pytest.fixture
    def storage_service(self):
        """Create storage service with mocked S3 client."""
        with patch('app.services.storage.boto3.client') as mock_client:
            mock_s3 = MagicMock()
            mock_client.return_value = mock_s3
            service = StorageService()
            service._initialized = True
            service.s3_client = mock_s3
            return service

    def test_delete_file_success(self, storage_service):
        """Test successful file deletion."""
        result = storage_service.delete_file("test/file.pdf")

        assert result is True
        storage_service.s3_client.delete_object.assert_called_once()

    def test_delete_file_error(self, storage_service):
        """Test file deletion handles errors gracefully."""
        from botocore.exceptions import ClientError
        storage_service.s3_client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "500", "Message": "Server error"}},
            "DeleteObject"
        )

        result = storage_service.delete_file("test/file.pdf")

        assert result is False

    def test_delete_files_batch(self, storage_service):
        """Test batch file deletion."""
        keys = ["file1.pdf", "file2.pdf", "file3.pdf"]

        result = storage_service.delete_files(keys)

        assert result is True
        storage_service.s3_client.delete_objects.assert_called_once()
        call_args = storage_service.s3_client.delete_objects.call_args
        objects = call_args.kwargs['Delete']['Objects']
        assert len(objects) == 3

    def test_delete_files_empty_list(self, storage_service):
        """Test batch deletion with empty list."""
        result = storage_service.delete_files([])

        assert result is True
        storage_service.s3_client.delete_objects.assert_not_called()

    def test_delete_file_not_initialized(self):
        """Test deletion returns False when not initialized."""
        with patch('app.services.storage.boto3.client') as mock_client:
            mock_client.side_effect = Exception("Connection failed")
            service = StorageService()
            service._initialized = False

            result = service.delete_file("test/file.pdf")

            assert result is False


class TestStorageServiceS3KeyGeneration:
    """Tests for S3 key generation."""

    @pytest.fixture
    def storage_service(self):
        """Create storage service with mocked S3 client."""
        with patch('app.services.storage.boto3.client') as mock_client:
            mock_client.return_value = MagicMock()
            service = StorageService()
            service._initialized = True
            return service

    def test_generate_s3_key_format(self, storage_service):
        """Test S3 key follows expected format."""
        key = storage_service._generate_s3_key("attachments", "test.pdf", ".pdf")

        parts = key.split("/")
        assert parts[0] == "attachments"
        # Date part: YYYY/MM/DD
        assert len(parts[1]) == 4  # Year
        assert len(parts[2]) == 2  # Month
        assert len(parts[3]) == 2  # Day
        # Filename part: uuid_filename.ext
        assert parts[4].endswith(".pdf")
        assert "_" in parts[4]

    def test_generate_s3_key_sanitizes_filename(self, storage_service):
        """Test S3 key sanitizes dangerous characters."""
        key = storage_service._generate_s3_key(
            "test",
            "../../etc/passwd",  # Path traversal attempt
            ".txt"
        )

        # Slashes should be removed (path traversal prevented)
        # The key should be in format: folder/date/uuid_sanitized.ext
        assert key.count("/") == 4  # test/YYYY/MM/DD/filename.txt
        assert "/../" not in key  # No actual path traversal possible

    def test_generate_s3_key_truncates_long_filename(self, storage_service):
        """Test S3 key truncates very long filenames."""
        long_name = "a" * 200  # Very long filename
        key = storage_service._generate_s3_key("test", long_name, ".txt")

        # Filename part should be truncated
        filename_part = key.split("/")[-1]
        assert len(filename_part) <= 70  # uuid (8) + _ + filename (50) + ext
