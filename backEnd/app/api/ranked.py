"""Determine active AMQ ranked windows and their remaining time."""

from datetime import datetime, time as dt_time, timezone
from zoneinfo import ZoneInfo

from api.schemas import RankedTimeStatus

# AMQ ranked runs from 20:30 to 21:23 local time in each region.
RANKED_REGIONS = (
    (ZoneInfo("Europe/Copenhagen"), "Central"),
    (ZoneInfo("America/Chicago"), "Western"),
    (ZoneInfo("Asia/Tokyo"), "Eastern"),
)
RANKED_START_TIME = dt_time(hour=20, minute=30)
RANKED_END_TIME = dt_time(hour=21, minute=23)


def is_ranked_time(date: datetime | None = None) -> bool:
    """Use the same schedule calculation as the ranked-status endpoint."""
    return get_ranked_time_info(date).active


def get_ranked_time_info(date: datetime | None = None) -> RankedTimeStatus:
    """Ranked status, active region, time remaining, and server time."""
    if date is None:
        dt_utc = datetime.now(timezone.utc)
    else:
        dt_utc = date.astimezone(timezone.utc) if date.tzinfo else date.replace(tzinfo=timezone.utc)
    server_time = dt_utc.isoformat()

    for tz_info, label in RANKED_REGIONS:
        local_dt = dt_utc.astimezone(tz_info)
        local_t = local_dt.time()
        if RANKED_START_TIME <= local_t < RANKED_END_TIME:
            local_end = local_dt.replace(
                hour=RANKED_END_TIME.hour,
                minute=RANKED_END_TIME.minute,
                second=0,
                microsecond=0,
            )
            remaining_total_seconds = max(0, int((local_end - local_dt).total_seconds()))
            return RankedTimeStatus(
                active=True,
                region=label,
                remaining_minutes=remaining_total_seconds // 60,
                remaining_seconds=remaining_total_seconds % 60,
                server_time=server_time,
            )

    return RankedTimeStatus(
        active=False,
        region=None,
        remaining_minutes=None,
        remaining_seconds=None,
        server_time=server_time,
    )
