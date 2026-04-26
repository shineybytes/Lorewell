import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


TIMESTAMP_PATTERN = re.compile(r"(\d{8})_(\d{6})(?:[_\.]|$)")


@dataclass
class TimestampGuess:
    captured_at_guess: datetime | None
    captured_at_guess_source: str | None
    captured_at_guess_confidence: str | None
    captured_at_guess_matched_text: str | None


def extract_timestamp_from_filename(filename: str) -> TimestampGuess:
    """
    Extract a naive datetime guess from a filename.

    Supported v1 patterns:
    - YYYYMMDD_HHMMSS
    - YYYYMMDD_HHMMSS_<anything>

    Examples:
    - 20250712_210052.mp4
    - 20250712_210052_3.mp4

    Everything else returns no guess for now.
    """
    basename = Path(filename).name
    match = TIMESTAMP_PATTERN.search(basename)

    if not match:
        return TimestampGuess(
            captured_at_guess=None,
            captured_at_guess_source=None,
            captured_at_guess_confidence=None,
            captured_at_guess_matched_text=None,
        )

    date_part = match.group(1)
    time_part = match.group(2)
    matched_text = f"{date_part}_{time_part}"

    try:
        parsed = datetime.strptime(matched_text, "%Y%m%d_%H%M%S")
    except ValueError:
        return TimestampGuess(
            captured_at_guess=None,
            captured_at_guess_source=None,
            captured_at_guess_confidence=None,
            captured_at_guess_matched_text=None,
        )

    return TimestampGuess(
        captured_at_guess=parsed,
        captured_at_guess_source="filename",
        captured_at_guess_confidence="high",
        captured_at_guess_matched_text=matched_text,
    )
