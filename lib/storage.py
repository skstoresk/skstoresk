"""Uploads product images/videos to Supabase Storage (public buckets)."""
import uuid

from .db import client

IMAGE_BUCKET = "product-images"
VIDEO_BUCKET = "product-videos"

_ALLOWED_IMAGES = {"jpg", "jpeg", "png", "webp"}
_ALLOWED_VIDEOS = {"mp4", "webm", "mov"}


def _ext(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def upload_image(file) -> str:
    """file: streamlit UploadedFile. Returns public URL."""
    ext = _ext(file.name)
    if ext not in _ALLOWED_IMAGES:
        raise ValueError(f"Image type .{ext} not allowed (jpg, png, webp only)")
    return _upload(IMAGE_BUCKET, file, ext, f"image/{ext}")


def upload_video(file) -> str:
    ext = _ext(file.name)
    if ext not in _ALLOWED_VIDEOS:
        raise ValueError(f"Video type .{ext} not allowed (mp4, webm, mov only)")
    return _upload(VIDEO_BUCKET, file, ext, f"video/{ext}")


def _upload(bucket: str, file, ext: str, content_type: str) -> str:
    sb = client()
    path = f"{uuid.uuid4().hex}.{ext}"
    data = file.getvalue()
    sb.storage.from_(bucket).upload(
        path, data, file_options={"content-type": content_type, "upsert": "true"}
    )
    return sb.storage.from_(bucket).get_public_url(path)


def delete_by_url(url: str):
    """Best-effort delete of a storage object given its public URL."""
    try:
        sb = client()
        for bucket in (IMAGE_BUCKET, VIDEO_BUCKET):
            marker = f"/{bucket}/"
            if marker in url:
                path = url.split(marker, 1)[1].split("?")[0]
                sb.storage.from_(bucket).remove([path])
                return
    except Exception:
        pass
