import pytest
from fastapi import HTTPException

from app.schemas import TimeConvertRequest
from app.services.time import convert_local_time_to_utc


def test_convert_local_time_to_utc():
    result = convert_local_time_to_utc(
        TimeConvertRequest(
            local_datetime="2026-03-25T18:30:00",
            timezone="America/Los_Angeles",
        )
    )

    assert result.timezone == "America/Los_Angeles"
    assert result.utc_datetime == "2026-03-26T01:30:00"


def test_convert_local_time_rejects_invalid_timezone():
    with pytest.raises(HTTPException) as exc:
        convert_local_time_to_utc(
            TimeConvertRequest(
                local_datetime="2026-03-25T18:30:00",
                timezone="Mars/Olympus",
            )
        )

    assert exc.value.status_code == 400
