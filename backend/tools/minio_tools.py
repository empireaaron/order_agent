"""
MinIO 工具函数
"""
import logging
from io import BytesIO
from minio import Minio
from minio.error import S3Error

from config import settings

logger = logging.getLogger(__name__)


def get_minio_client():
    """获取 MinIO 客户端"""
    return Minio(
        settings.settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.settings.MINIO_SECURE
    )


def ensure_bucket_exists():
    """确保 bucket 存在"""
    client = get_minio_client()
    try:
        if not client.bucket_exists(settings.MINIO_BUCKET):
            client.make_bucket(settings.MINIO_BUCKET)
    except S3Error as e:
        logger.error("Error creating bucket: %s", e)


def upload_file(file_data: bytes, object_name: str, content_type: str = "application/octet-stream"):
    """
    上传文件到 MinIO

    Args:
        file_data: 文件二进制数据
        object_name: 对象名称（路径）
        content_type: 内容类型

    Returns:
        (是否成功, 文件URL或错误信息)
    """
    ensure_bucket_exists()
    client = get_minio_client()

    try:
        # 上传文件
        client.put_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_name,
            data=BytesIO(file_data),
            length=len(file_data),
            content_type=content_type
        )

        # 生成 URL
        url = f"http{'s' if settings.MINIO_SECURE else ''}://{settings.MINIO_ENDPOINT}/{settings.MINIO_BUCKET}/{object_name}"
        return True, url

    except S3Error as e:
        return False, str(e)


def download_file(object_name: str) -> bytes:
    """
    从 MinIO 下载文件

    Args:
        object_name: 对象名称

    Returns:
        文件二进制数据
    """
    client = get_minio_client()

    try:
        response = client.get_object(settings.MINIO_BUCKET, object_name)
        return response.read()
    except S3Error as e:
        logger.error("Error downloading file: %s", e)
        return b""
    finally:
        response.close()
        response.release_conn()


def delete_file(object_name: str) -> bool:
    """
    从 MinIO 删除文件

    Args:
        object_name: 对象名称

    Returns:
        是否成功
    """
    client = get_minio_client()

    try:
        client.remove_object(settings.MINIO_BUCKET, object_name)
        return True
    except S3Error as e:
        logger.error("Error deleting file: %s", e)
        return False


def get_presigned_url(object_name: str, expires: int = 3600) -> str:
    """
    获取预签名 URL（用于临时访问私有文件）

    Args:
        object_name: 对象名称
        expires: URL 过期时间（秒），默认1小时

    Returns:
        预签名 URL
    """
    client = get_minio_client()

    try:
        url = client.presigned_get_object(settings.MINIO_BUCKET, object_name, expires=expires)
        return url
    except S3Error as e:
        logger.error("Error generating presigned URL: %s", e)
        return ""