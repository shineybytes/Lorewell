from app.asset_timestamp import extract_timestamp_from_filename


def test_extract_timestamp_from_plain_filename():
    result = extract_timestamp_from_filename("20250712_210052.mp4")

    assert result.captured_at_guess is not None
    assert result.captured_at_guess.isoformat() == "2025-07-12T21:00:52"
    assert result.captured_at_guess_source == "filename"
    assert result.captured_at_guess_confidence == "high"
    assert result.captured_at_guess_matched_text == "20250712_210052"


def test_extract_timestamp_from_filename_with_suffix():
    result = extract_timestamp_from_filename("20250712_210052_3.mp4")

    assert result.captured_at_guess is not None
    assert result.captured_at_guess.isoformat() == "2025-07-12T21:00:52"
    assert result.captured_at_guess_source == "filename"
    assert result.captured_at_guess_confidence == "high"
    assert result.captured_at_guess_matched_text == "20250712_210052"


def test_extract_timestamp_ignores_img_style_names():
    result = extract_timestamp_from_filename("IMG_9689.mov")

    assert result.captured_at_guess is None
    assert result.captured_at_guess_source is None
    assert result.captured_at_guess_confidence is None
    assert result.captured_at_guess_matched_text is None


def test_extract_timestamp_ignores_semantic_names():
    result = extract_timestamp_from_filename("DJAlexMixingDemo_BriWright.mp4")

    assert result.captured_at_guess is None
    assert result.captured_at_guess_source is None
    assert result.captured_at_guess_confidence is None
    assert result.captured_at_guess_matched_text is None


def test_extract_timestamp_handles_double_extension_if_timestamp_is_present():
    result = extract_timestamp_from_filename("20241005_190810.mp4.3gpp")

    assert result.captured_at_guess is not None
    assert result.captured_at_guess.isoformat() == "2024-10-05T19:08:10"
    assert result.captured_at_guess_source == "filename"
    assert result.captured_at_guess_confidence == "high"
    assert result.captured_at_guess_matched_text == "20241005_190810"
