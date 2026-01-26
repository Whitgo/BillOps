"""
S3 Upload and Download Utilities

Provides functions for uploading, downloading, and managing files in AWS S3.
"""

import logging
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Optional
from urllib.parse import urljoin

import boto3
from botocore.exceptions import ClientError

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class S3StorageService:
    """Service for managing S3 uploads and downloads."""

    def __init__(self):
        """Initialize S3 client with AWS credentials from settings."""
        settings = get_settings()

        if not settings.s3_bucket_name:
            raise ValueError("S3_BUCKET_NAME must be configured")

        self.bucket_name = settings.s3_bucket_name
        self.base_path = settings.s3_base_path or "invoices"
        self.region = settings.aws_region or "us-east-1"

        # Initialize S3 client
        self.client = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    def _build_key(self, filename: str, subfolder: Optional[str] = None) -> str:
        """
        Build S3 object key from filename and optional subfolder.

        Args:
            filename: Name of the file
            subfolder: Optional subfolder within base_path

        Returns:
            Full S3 object key
        """
        path = Path(self.base_path)

        if subfolder:
            path = path / subfolder

        return str(path / filename)

    def upload_file(
        self,
        file_obj: BinaryIO,
        filename: str,
        subfolder: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
        public: bool = False,
    ) -> str:
        """
        Upload a file to S3.

        Args:
            file_obj: File-like object or bytes
            filename: Name of the file in S3
            subfolder: Optional subfolder within base_path
            content_type: MIME type (e.g., 'application/pdf')
            metadata: Optional metadata dict to store with object
            public: If True, make file publicly readable

        Returns:
            S3 object key (path)

        Raises:
            ValueError: If file is too large or invalid
            ClientError: If S3 upload fails
        """
        try:
            key = self._build_key(filename, subfolder)

            # Prepare extra args
            extra_args = {}

            if content_type:
                extra_args["ContentType"] = content_type

            if metadata:
                extra_args["Metadata"] = metadata

            if public:
                extra_args["ACL"] = "public-read"

            # Upload file
            self.client.upload_fileobj(
                file_obj,
                self.bucket_name,
                key,
                ExtraArgs=extra_args,
            )

            logger.info(f"Uploaded file to S3: {key}")
            return key

        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise

    def upload_bytes(
        self,
        data: bytes,
        filename: str,
        subfolder: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
        public: bool = False,
    ) -> str:
        """
        Upload bytes to S3.

        Args:
            data: File data as bytes
            filename: Name of the file in S3
            subfolder: Optional subfolder within base_path
            content_type: MIME type (e.g., 'application/pdf')
            metadata: Optional metadata dict to store with object
            public: If True, make file publicly readable

        Returns:
            S3 object key (path)
        """
        file_obj = BytesIO(data)
        return self.upload_file(
            file_obj,
            filename,
            subfolder,
            content_type,
            metadata,
            public,
        )

    def download_file(
        self,
        filename: str,
        subfolder: Optional[str] = None,
    ) -> bytes:
        """
        Download a file from S3.

        Args:
            filename: Name of the file in S3
            subfolder: Optional subfolder within base_path

        Returns:
            File data as bytes

        Raises:
            ClientError: If file not found or download fails
        """
        try:
            key = self._build_key(filename, subfolder)

            # Download file to BytesIO object
            file_obj = BytesIO()
            self.client.download_fileobj(self.bucket_name, key, file_obj)

            file_obj.seek(0)
            return file_obj.getvalue()

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.warning(f"File not found in S3: {filename}")
                raise FileNotFoundError(f"File not found: {filename}") from e
            logger.error(f"Failed to download file from S3: {e}")
            raise

    def download_to_file(
        self,
        filename: str,
        filepath: str,
        subfolder: Optional[str] = None,
    ) -> None:
        """
        Download a file from S3 to local filesystem.

        Args:
            filename: Name of the file in S3
            filepath: Local file path to save to
            subfolder: Optional subfolder within base_path

        Raises:
            ClientError: If download fails
        """
        try:
            key = self._build_key(filename, subfolder)
            self.client.download_file(self.bucket_name, key, filepath)
            logger.info(f"Downloaded file from S3 to {filepath}")
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise

    def delete_file(
        self,
        filename: str,
        subfolder: Optional[str] = None,
    ) -> None:
        """
        Delete a file from S3.

        Args:
            filename: Name of the file in S3
            subfolder: Optional subfolder within base_path

        Raises:
            ClientError: If deletion fails
        """
        try:
            key = self._build_key(filename, subfolder)
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Deleted file from S3: {key}")
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            raise

    def delete_files(
        self,
        filenames: list[str],
        subfolder: Optional[str] = None,
    ) -> None:
        """
        Delete multiple files from S3.

        Args:
            filenames: List of filenames to delete
            subfolder: Optional subfolder within base_path

        Raises:
            ClientError: If deletion fails
        """
        try:
            objects_to_delete = []

            for filename in filenames:
                key = self._build_key(filename, subfolder)
                objects_to_delete.append({"Key": key})

            if objects_to_delete:
                self.client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={"Objects": objects_to_delete},
                )
                logger.info(f"Deleted {len(filenames)} files from S3")

        except ClientError as e:
            logger.error(f"Failed to delete files from S3: {e}")
            raise

    def file_exists(
        self,
        filename: str,
        subfolder: Optional[str] = None,
    ) -> bool:
        """
        Check if a file exists in S3.

        Args:
            filename: Name of the file in S3
            subfolder: Optional subfolder within base_path

        Returns:
            True if file exists, False otherwise
        """
        try:
            key = self._build_key(filename, subfolder)
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error(f"Error checking file existence: {e}")
            raise

    def get_file_url(
        self,
        filename: str,
        subfolder: Optional[str] = None,
        expiration: int = 3600,
    ) -> str:
        """
        Get a pre-signed URL for a file in S3.

        Args:
            filename: Name of the file in S3
            subfolder: Optional subfolder within base_path
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Pre-signed URL string

        Raises:
            ClientError: If URL generation fails
        """
        try:
            key = self._build_key(filename, subfolder)

            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expiration,
            )

            logger.info(f"Generated pre-signed URL for: {key}")
            return url

        except ClientError as e:
            logger.error(f"Failed to generate pre-signed URL: {e}")
            raise

    def get_file_metadata(
        self,
        filename: str,
        subfolder: Optional[str] = None,
    ) -> dict:
        """
        Get metadata for a file in S3.

        Args:
            filename: Name of the file in S3
            subfolder: Optional subfolder within base_path

        Returns:
            Dictionary with file metadata (size, modified time, etc.)

        Raises:
            ClientError: If metadata retrieval fails
        """
        try:
            key = self._build_key(filename, subfolder)
            response = self.client.head_object(Bucket=self.bucket_name, Key=key)

            return {
                "size": response.get("ContentLength"),
                "modified": response.get("LastModified"),
                "content_type": response.get("ContentType"),
                "metadata": response.get("Metadata", {}),
            }

        except ClientError as e:
            logger.error(f"Failed to get file metadata: {e}")
            raise

    def list_files(
        self,
        subfolder: Optional[str] = None,
        prefix: Optional[str] = None,
    ) -> list[dict]:
        """
        List files in S3 folder.

        Args:
            subfolder: Optional subfolder within base_path
            prefix: Optional filename prefix to filter by

        Returns:
            List of file dictionaries with keys: name, size, modified

        Raises:
            ClientError: If listing fails
        """
        try:
            key = self._build_key("", subfolder) if subfolder else self.base_path
            list_prefix = key

            if prefix:
                list_prefix = f"{key}/{prefix}"

            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=list_prefix,
            )

            files = []

            if "Contents" in response:
                for obj in response["Contents"]:
                    if not obj["Key"].endswith("/"):
                        files.append(
                            {
                                "name": Path(obj["Key"]).name,
                                "size": obj["Size"],
                                "modified": obj["LastModified"],
                            }
                        )

            return files

        except ClientError as e:
            logger.error(f"Failed to list files in S3: {e}")
            raise

    def copy_file(
        self,
        source_filename: str,
        dest_filename: str,
        source_subfolder: Optional[str] = None,
        dest_subfolder: Optional[str] = None,
    ) -> None:
        """
        Copy a file within S3.

        Args:
            source_filename: Name of file to copy
            dest_filename: Name for copied file
            source_subfolder: Optional subfolder of source file
            dest_subfolder: Optional subfolder for destination

        Raises:
            ClientError: If copy fails
        """
        try:
            source_key = self._build_key(source_filename, source_subfolder)
            dest_key = self._build_key(dest_filename, dest_subfolder)

            self.client.copy_object(
                CopySource={"Bucket": self.bucket_name, "Key": source_key},
                Bucket=self.bucket_name,
                Key=dest_key,
            )

            logger.info(f"Copied file in S3: {source_key} -> {dest_key}")

        except ClientError as e:
            logger.error(f"Failed to copy file in S3: {e}")
            raise


# Singleton instance
_storage_service: Optional[S3StorageService] = None


def get_storage_service() -> S3StorageService:
    """Get or create S3 storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = S3StorageService()
    return _storage_service
