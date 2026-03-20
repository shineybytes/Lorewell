from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}

MAX_IMAGE_SIZE_BYTES = 8 * 1024 * 1024
MAX_VIDEO_SIZE_BYTES = 300 * 1024 * 1024


def validate_media_file(filename: str, file_size_bytes: int) -> tuple[str, str | None]:
    ext = Path(filename).suffix.lower()

    if ext in IMAGE_EXTENSIONS:
        if file_size_bytes > MAX_IMAGE_SIZE_BYTES:
            return "image", "Image exceeds 8 MB maximum size."
        return "image", None

    if ext in VIDEO_EXTENSIONS:
        if file_size_bytes > MAX_VIDEO_SIZE_BYTES:
            return "video", "Video exceeds 300 MB maximum size."
        return "video", None

    return "unknown", "Unsupported file type. Only JPEG, MP4, and MOV are currently supported."
