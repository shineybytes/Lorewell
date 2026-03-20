from app.media_validation import (
    validate_media_file,
    MAX_IMAGE_SIZE_BYTES,
    MAX_VIDEO_SIZE_BYTES,
)


def test_validate_jpeg_under_limit():
    media_type, error = validate_media_file("photo.jpg", MAX_IMAGE_SIZE_BYTES - 1)
    assert media_type == "image"
    assert error is None


def test_validate_jpeg_at_limit():
    media_type, error = validate_media_file("photo.jpeg", MAX_IMAGE_SIZE_BYTES)
    assert media_type == "image"
    assert error is None


def test_validate_jpeg_over_limit():
    media_type, error = validate_media_file("photo.jpg", MAX_IMAGE_SIZE_BYTES + 1)
    assert media_type == "image"
    assert error == "Image exceeds 8 MB maximum size."


def test_validate_mp4_under_limit():
    media_type, error = validate_media_file("clip.mp4", MAX_VIDEO_SIZE_BYTES - 1)
    assert media_type == "video"
    assert error is None


def test_validate_mov_under_limit():
    media_type, error = validate_media_file("clip.mov", MAX_VIDEO_SIZE_BYTES)
    assert media_type == "video"
    assert error is None


def test_validate_video_over_limit():
    media_type, error = validate_media_file("clip.mp4", MAX_VIDEO_SIZE_BYTES + 1)
    assert media_type == "video"
    assert error == "Video exceeds 300 MB maximum size."


def test_validate_png_is_unsupported():
    media_type, error = validate_media_file("image.png", 1024)
    assert media_type == "unknown"
    assert error == "Unsupported file type. Only JPEG, MP4, and MOV are currently supported."


def test_validate_gif_is_unsupported():
    media_type, error = validate_media_file("anim.gif", 1024)
    assert media_type == "unknown"
    assert error == "Unsupported file type. Only JPEG, MP4, and MOV are currently supported."


def test_validate_no_extension_is_unsupported():
    media_type, error = validate_media_file("mysteryfile", 1024)
    assert media_type == "unknown"
    assert error == "Unsupported file type. Only JPEG, MP4, and MOV are currently supported."
