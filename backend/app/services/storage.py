"""
Storage service for handling file uploads to DigitalOcean Spaces (S3-compatible).
"""

import uuid
import logging
from typing import Optional, BinaryIO
from io import BytesIO

import boto3
from botocore.exceptions import ClientError
from PIL import Image

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage in DigitalOcean Spaces."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy-load the S3 client."""
        if self._client is None:
            if not settings.SPACES_ACCESS_KEY or not settings.SPACES_SECRET_KEY:
                logger.warning("Spaces credentials not configured")
                return None

            self._client = boto3.client(
                "s3",
                region_name=settings.SPACES_REGION,
                endpoint_url=settings.spaces_endpoint_url,
                aws_access_key_id=settings.SPACES_ACCESS_KEY,
                aws_secret_access_key=settings.SPACES_SECRET_KEY,
            )
        return self._client

    def _generate_key(
        self, tenant_id: str, filename: str, folder: str = "inventory"
    ) -> str:
        """Generate a unique storage key for a file."""
        # Extract extension
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        # Generate unique filename
        unique_id = uuid.uuid4().hex[:12]
        return f"{tenant_id}/{folder}/{unique_id}.{ext}"

    def _optimize_image(
        self,
        file_content: bytes,
        max_width: int = 1200,
        max_height: int = 1200,
        quality: int = 85,
    ) -> tuple[bytes, str]:
        """
        Optimize an image by resizing and compressing.
        Returns the optimized image bytes and content type.
        """
        try:
            img = Image.open(BytesIO(file_content))

            # Convert RGBA to RGB for JPEG
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(
                    img, mask=img.split()[-1] if img.mode == "RGBA" else None
                )
                img = background

            # Resize if necessary
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Save to bytes
            output = BytesIO()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            output.seek(0)

            return output.read(), "image/jpeg"
        except Exception as e:
            logger.error(f"Failed to optimize image: {e}")
            # Return original if optimization fails
            return file_content, "image/jpeg"

    async def upload_image(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        tenant_id: str,
        optimize: bool = True,
    ) -> Optional[str]:
        """
        Upload an image to Spaces.

        Args:
            file_content: The file content as bytes
            filename: Original filename
            content_type: MIME type of the file
            tenant_id: Tenant ID for organizing files
            optimize: Whether to optimize the image

        Returns:
            The storage key if successful, None otherwise
        """
        if not self.client:
            logger.error("Storage client not available")
            return None

        try:
            # Validate content type
            if content_type not in settings.allowed_image_types_list:
                logger.error(f"Invalid content type: {content_type}")
                return None

            # Validate file size
            if len(file_content) > settings.MAX_UPLOAD_SIZE:
                logger.error(f"File too large: {len(file_content)} bytes")
                return None

            # Optimize image if requested
            if optimize:
                file_content, content_type = self._optimize_image(file_content)

            # Generate unique key
            key = self._generate_key(tenant_id, filename)

            # Upload to Spaces
            self.client.put_object(
                Bucket=settings.SPACES_BUCKET,
                Key=key,
                Body=file_content,
                ContentType=content_type,
                # Private by default - use signed URLs to access
                ACL="private",
            )

            logger.info(f"Successfully uploaded image: {key}")
            return key

        except ClientError as e:
            logger.error(f"Failed to upload to Spaces: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading image: {e}")
            return None

    def get_signed_url(self, key: str, expiration: int = None) -> Optional[str]:
        """
        Generate a signed URL for accessing a private object.

        Args:
            key: The storage key of the object
            expiration: URL expiration in seconds (default from settings)

        Returns:
            Signed URL if successful, None otherwise
        """
        if not self.client:
            logger.error("Storage client not available")
            return None

        if not key:
            return None

        try:
            expiration = expiration or settings.SPACES_URL_EXPIRATION

            url = self.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": settings.SPACES_BUCKET,
                    "Key": key,
                },
                ExpiresIn=expiration,
            )
            return url

        except ClientError as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return None

    async def delete_image(self, key: str) -> bool:
        """
        Delete an image from Spaces.

        Args:
            key: The storage key of the object

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Storage client not available")
            return False

        if not key:
            return True  # Nothing to delete

        try:
            self.client.delete_object(
                Bucket=settings.SPACES_BUCKET,
                Key=key,
            )
            logger.info(f"Successfully deleted image: {key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete from Spaces: {e}")
            return False


# Singleton instance
storage_service = StorageService()
