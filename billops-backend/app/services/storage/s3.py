"""S3 storage utility."""
from __future__ import annotations

import io
from typing import Optional
from datetime import datetime

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config.settings import get_settings


def upload_to_s3(
    data: bytes,
    key: str,
    content_type: str = "application/pdf",
    acl: str = "private",
) -> Optional[str]:
    """Upload data to S3 and return the public URL (if configured).

    Args:
        data: File bytes to upload.
        key: Object key within the bucket.
        content_type: MIME type of the object.
        acl: Access control list (e.g., 'private', 'public-read').

    Returns:
        URL string if upload succeeded, else None.
    """
    settings = get_settings()
    bucket = getattr(settings, "s3_bucket_name", None)
    region = getattr(settings, "aws_region", "us-east-1")

    if not bucket:
        # S3 is not configured
        return None

    session = boto3.session.Session(
        aws_access_key_id=getattr(settings, "aws_access_key_id", None),
        aws_secret_access_key=getattr(settings, "aws_secret_access_key", None),
        region_name=region,
    )
    s3 = session.client("s3")

    # Normalize base path
    base_path = getattr(settings, "s3_base_path", "").strip("/")
    prefix = f"{base_path}/" if base_path else ""
    object_key = f"{prefix}{key}"

    try:
        s3.put_object(
            Bucket=bucket,
            Key=object_key,
            Body=io.BytesIO(data),
            ContentType=content_type,
            ACL=acl,
        )
    except (BotoCoreError, ClientError):
        return None

    # Construct URL (non-signed)
    url = f"https://{bucket}.s3.{region}.amazonaws.com/{object_key}"
    return url
