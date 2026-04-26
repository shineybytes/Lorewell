from datetime import UTC
from zoneinfo import ZoneInfo, available_timezones

from fastapi import HTTPException

from app.schemas import TimeConvertRequest, TimeConvertResponse


def list_available_timezones() -> list[str]:
    return sorted(
        tz for tz in available_timezones()
        if "/" in tz and not tz.startswith("Etc/")
    )


def convert_local_time_to_utc(payload: TimeConvertRequest) -> TimeConvertResponse:
    if payload.local_datetime.tzinfo is not None:
        raise HTTPException(
            status_code=400,
            detail="local_datetime must not include a timezone or a Z suffix",
        )

    try:
        tz = ZoneInfo(payload.timezone)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid timezone")

    local_dt = payload.local_datetime.replace(tzinfo=tz)
    utc_dt = local_dt.astimezone(UTC)

    return TimeConvertResponse(
        local_datetime=payload.local_datetime.isoformat(),
        timezone=payload.timezone,
        utc_datetime=utc_dt.replace(tzinfo=None).isoformat(),
    )
