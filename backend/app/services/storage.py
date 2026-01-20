"""
S3/MinIO storage service for file uploads.
"""

import io
import uuid
from datetime import datetime
from typing import Optional, Tuple

import boto3
from botocore.exceptions import ClientError
from PIL import Image

from app.config import settings


class StorageService:
    """Service for handling file uploads to S3/MinIO."""

    # Allowed file types
    ALLOWED_IMAGE_TYPES = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }

    ALLOWED_FILE_TYPES = {
        "application/pdf": ".pdf",
        "text/plain": ".txt",
        "application/msword": ".doc",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    }

    # Size limits
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    THUMBNAIL_SIZE = (200, 200)
    PRESIGNED_URL_EXPIRY = 3600  # 1 hour

    def __init__(self):
        self.s3_client = None
        self.bucket = settings.S3_BUCKET
        self._initialized = False
        self._init_error = None
        self._try_initialize()

    def _try_initialize(self):
        """Try to initialize the S3 client. Can be retried later if it fails."""
        try:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT,
                aws_access_key_id=settings.S3_ACCESS_KEY,
                aws_secret_access_key=settings.S3_SECRET_KEY,
            )
            self._ensure_bucket_exists()
            self._initialized = True
            self._init_error = None
        except Exception as e:
            self._init_error = str(e)
            print(f"Warning: S3 storage service initialization failed: {e}")
            print("File uploads will not be available until MinIO/S3 is running.")

    def _ensure_initialized(self):
        """Ensure the service is initialized, retry if not."""
        if not self._initialized:
            self._try_initialize()
        if not self._initialized:
            raise RuntimeError(
                f"S3 storage service is not available. "
                f"Please ensure MinIO/S3 is running at {settings.S3_ENDPOINT}. "
                f"Error: {self._init_error}"
            )

    def _ensure_bucket_exists(self):
        """Create the bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket)
            except ClientError as e:
                # Bucket might already exist or we don't have permissions
                print(f"Warning: Could not create bucket: {e}")

    def _generate_s3_key(self, folder: str, filename: str, extension: str) -> str:
        """Generate a unique S3 key for a file."""
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")[:50]
        return f"{folder}/{timestamp}/{unique_id}_{safe_filename}{extension}"

    def validate_file(self, content_type: str, file_size: int, is_image: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Validate file type and size.
        Returns (is_valid, error_message).
        """
        if file_size > self.MAX_FILE_SIZE:
            return (
                False,
                f"File size exceeds {self.MAX_FILE_SIZE // (1024*1024)}MB limit",
            )

        allowed_types = (
            self.ALLOWED_IMAGE_TYPES if is_image else {**self.ALLOWED_IMAGE_TYPES, **self.ALLOWED_FILE_TYPES}
        )

        if content_type not in allowed_types:
            return False, f"File type '{content_type}' is not allowed"

        return True, None

    def get_extension(self, content_type: str) -> str:
        """Get file extension for a content type."""
        all_types = {**self.ALLOWED_IMAGE_TYPES, **self.ALLOWED_FILE_TYPES}
        return all_types.get(content_type, "")

    def is_image(self, content_type: str) -> bool:
        """Check if content type is an image."""
        return content_type in self.ALLOWED_IMAGE_TYPES

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        folder: str = "attachments",
    ) -> Tuple[str, Optional[str]]:
        """
        Upload a file to S3.
        Returns (s3_key, thumbnail_s3_key or None).
        """
        self._ensure_initialized()

        extension = self.get_extension(content_type)
        s3_key = self._generate_s3_key(folder, filename, extension)

        # Upload main file
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type,
        )

        thumbnail_key = None

        # Generate thumbnail for images
        if self.is_image(content_type):
            try:
                thumbnail_key = await self._create_thumbnail(file_content, s3_key, content_type)
            except Exception as e:
                # Thumbnail creation failed, but main upload succeeded
                print(f"Warning: Thumbnail creation failed: {e}")

        return s3_key, thumbnail_key

    async def _create_thumbnail(self, image_content: bytes, original_key: str, content_type: str) -> Optional[str]:
        """Create and upload a thumbnail for an image."""
        try:
            image = Image.open(io.BytesIO(image_content))

            # Convert to RGB if necessary (for PNG with transparency)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Create thumbnail
            image.thumbnail(self.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

            # Save to bytes
            thumb_buffer = io.BytesIO()
            image.save(thumb_buffer, format="JPEG", quality=80)
            thumb_buffer.seek(0)

            # Generate thumbnail key
            thumb_key = original_key.rsplit(".", 1)[0] + "_thumb.jpg"

            # Upload thumbnail
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=thumb_key,
                Body=thumb_buffer.getvalue(),
                ContentType="image/jpeg",
            )

            return thumb_key
        except Exception as e:
            print(f"Thumbnail creation error: {e}")
            return None

    def get_presigned_url(self, s3_key: str, expiry: int = None) -> Optional[str]:
        """
        Generate a presigned URL for file download.
        Returns None if S3 is not available.
        """
        if not self._initialized:
            return None

        if expiry is None:
            expiry = self.PRESIGNED_URL_EXPIRY

        url = self.s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": s3_key,
            },
            ExpiresIn=expiry,
        )
        return url

    def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3."""
        if not self._initialized:
            return False

        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=s3_key,
            )
            return True
        except ClientError as e:
            print(f"Error deleting file {s3_key}: {e}")
            return False

    def delete_files(self, s3_keys: list) -> bool:
        """Delete multiple files from S3."""
        if not s3_keys:
            return True

        if not self._initialized:
            return False

        try:
            objects = [{"Key": key} for key in s3_keys if key]
            if objects:
                self.s3_client.delete_objects(
                    Bucket=self.bucket,
                    Delete={"Objects": objects},
                )
            return True
        except ClientError as e:
            print(f"Error deleting files: {e}")
            return False


# Singleton instance
storage_service = StorageService()
