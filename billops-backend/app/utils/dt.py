"""
Date/Time Utilities

Provides functions for rounding, timezone handling, and duration calculations.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional


def utc_now() -> datetime:
    """Get current UTC time."""
    return datetime.now(timezone.utc)


def get_utc_timestamp(dt: Optional[datetime] = None) -> float:
    """
    Get Unix timestamp in UTC.

    Args:
        dt: Datetime object (defaults to now)

    Returns:
        Unix timestamp as float
    """
    if dt is None:
        dt = utc_now()

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.timestamp()


def from_timestamp(timestamp: float) -> datetime:
    """
    Create UTC datetime from Unix timestamp.

    Args:
        timestamp: Unix timestamp

    Returns:
        Timezone-aware datetime object
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is timezone-aware and in UTC.

    Args:
        dt: Datetime object (may be naive)

    Returns:
        Timezone-aware datetime in UTC
    """
    if dt.tzinfo is None:
        # Assume naive datetimes are in UTC
        return dt.replace(tzinfo=timezone.utc)

    if dt.tzinfo != timezone.utc:
        # Convert to UTC
        return dt.astimezone(timezone.utc)

    return dt


def round_to_minute(dt: datetime, nearest: int = 1) -> datetime:
    """
    Round datetime to nearest minute.

    Args:
        dt: Datetime object
        nearest: Round to nearest N minutes (default 1)

    Returns:
        Rounded datetime with seconds/microseconds set to 0

    Examples:
        >>> dt = datetime(2024, 1, 15, 10, 23, 45)
        >>> round_to_minute(dt)
        datetime.datetime(2024, 1, 15, 10, 24, 0)

        >>> round_to_minute(dt, nearest=15)
        datetime.datetime(2024, 1, 15, 10, 30, 0)
    """
    dt = ensure_utc(dt)

    # Round to nearest minute
    rounded = dt.replace(second=0, microsecond=0)
    remainder = rounded.minute % nearest

    if remainder >= nearest / 2:
        rounded += timedelta(minutes=(nearest - remainder))
    else:
        rounded -= timedelta(minutes=remainder)

    return rounded


def round_to_hour(dt: datetime) -> datetime:
    """
    Round datetime to nearest hour.

    Args:
        dt: Datetime object

    Returns:
        Rounded datetime with minutes/seconds/microseconds set to 0

    Examples:
        >>> dt = datetime(2024, 1, 15, 10, 35, 45)
        >>> round_to_hour(dt)
        datetime.datetime(2024, 1, 15, 11, 0, 0)
    """
    dt = ensure_utc(dt)

    rounded = dt.replace(minute=0, second=0, microsecond=0)

    # Round to nearest hour
    if dt.minute >= 30:
        rounded += timedelta(hours=1)

    return rounded


def round_down_to_hour(dt: datetime) -> datetime:
    """
    Round datetime down to the hour.

    Args:
        dt: Datetime object

    Returns:
        Rounded datetime with minutes/seconds/microseconds set to 0
    """
    dt = ensure_utc(dt)
    return dt.replace(minute=0, second=0, microsecond=0)


def round_down_to_day(dt: datetime) -> datetime:
    """
    Round datetime down to midnight of that day.

    Args:
        dt: Datetime object

    Returns:
        Datetime at midnight UTC
    """
    dt = ensure_utc(dt)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def round_up_to_day(dt: datetime) -> datetime:
    """
    Round datetime up to midnight of the next day.

    Args:
        dt: Datetime object

    Returns:
        Datetime at midnight UTC next day
    """
    dt = round_down_to_day(dt)

    if dt != ensure_utc(datetime(dt.year, dt.month, dt.day)):
        return dt

    return dt + timedelta(days=1)


def start_of_day(dt: Optional[datetime] = None) -> datetime:
    """
    Get start of day (midnight) for given date.

    Args:
        dt: Datetime object (defaults to today)

    Returns:
        Datetime at midnight UTC
    """
    if dt is None:
        dt = utc_now()

    dt = ensure_utc(dt)
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: Optional[datetime] = None) -> datetime:
    """
    Get end of day (23:59:59.999999) for given date.

    Args:
        dt: Datetime object (defaults to today)

    Returns:
        Datetime at end of day UTC
    """
    if dt is None:
        dt = utc_now()

    dt = ensure_utc(dt)
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def start_of_week(dt: Optional[datetime] = None, monday_start: bool = True) -> datetime:
    """
    Get start of week (Monday or Sunday).

    Args:
        dt: Datetime object (defaults to now)
        monday_start: If True, week starts on Monday; else Sunday

    Returns:
        Datetime at start of week at midnight UTC
    """
    if dt is None:
        dt = utc_now()

    dt = ensure_utc(dt)
    dt = start_of_day(dt)

    # Monday is 0, Sunday is 6
    days_back = dt.weekday() if monday_start else (dt.weekday() + 1) % 7

    return dt - timedelta(days=days_back)


def end_of_week(dt: Optional[datetime] = None, monday_start: bool = True) -> datetime:
    """
    Get end of week (Sunday or Saturday).

    Args:
        dt: Datetime object (defaults to now)
        monday_start: If True, week ends on Sunday; else Saturday

    Returns:
        Datetime at end of week at end of day UTC
    """
    dt = start_of_week(dt, monday_start)
    return end_of_day(dt + timedelta(days=6))


def start_of_month(dt: Optional[datetime] = None) -> datetime:
    """
    Get start of month (1st day at midnight).

    Args:
        dt: Datetime object (defaults to now)

    Returns:
        Datetime at start of month at midnight UTC
    """
    if dt is None:
        dt = utc_now()

    dt = ensure_utc(dt)
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def end_of_month(dt: Optional[datetime] = None) -> datetime:
    """
    Get end of month (last day at end of day).

    Args:
        dt: Datetime object (defaults to now)

    Returns:
        Datetime at end of month at end of day UTC
    """
    if dt is None:
        dt = utc_now()

    dt = ensure_utc(dt)

    # Move to first day of next month, then go back 1 second
    if dt.month == 12:
        next_month = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        next_month = dt.replace(month=dt.month + 1, day=1)

    return end_of_day(next_month - timedelta(days=1))


def start_of_year(dt: Optional[datetime] = None) -> datetime:
    """
    Get start of year (Jan 1 at midnight).

    Args:
        dt: Datetime object (defaults to now)

    Returns:
        Datetime at start of year at midnight UTC
    """
    if dt is None:
        dt = utc_now()

    dt = ensure_utc(dt)
    return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)


def end_of_year(dt: Optional[datetime] = None) -> datetime:
    """
    Get end of year (Dec 31 at end of day).

    Args:
        dt: Datetime object (defaults to now)

    Returns:
        Datetime at end of year at end of day UTC
    """
    if dt is None:
        dt = utc_now()

    dt = ensure_utc(dt)
    return dt.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)


def calculate_duration(
    start: datetime,
    end: datetime,
    unit: str = "hours",
) -> float:
    """
    Calculate duration between two datetimes.

    Args:
        start: Start datetime
        end: End datetime
        unit: Time unit ('seconds', 'minutes', 'hours', 'days')

    Returns:
        Duration as float in specified unit

    Raises:
        ValueError: If unit is invalid or end is before start

    Examples:
        >>> start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        >>> end = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
        >>> calculate_duration(start, end, 'hours')
        2.5

        >>> calculate_duration(start, end, 'minutes')
        150.0
    """
    start = ensure_utc(start)
    end = ensure_utc(end)

    if end < start:
        raise ValueError("End time must be after start time")

    delta = end - start
    total_seconds = delta.total_seconds()

    unit_map = {
        "seconds": 1,
        "minutes": 60,
        "hours": 3600,
        "days": 86400,
    }

    if unit not in unit_map:
        raise ValueError(f"Invalid unit: {unit}. Must be one of {list(unit_map.keys())}")

    return total_seconds / unit_map[unit]


def add_time(
    dt: datetime,
    seconds: int = 0,
    minutes: int = 0,
    hours: int = 0,
    days: int = 0,
    weeks: int = 0,
) -> datetime:
    """
    Add time to a datetime.

    Args:
        dt: Datetime object
        seconds: Seconds to add
        minutes: Minutes to add
        hours: Hours to add
        days: Days to add
        weeks: Weeks to add

    Returns:
        New datetime with time added

    Examples:
        >>> dt = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        >>> add_time(dt, hours=2, minutes=30)
        datetime.datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
    """
    dt = ensure_utc(dt)
    return dt + timedelta(
        seconds=seconds,
        minutes=minutes,
        hours=hours,
        days=days,
        weeks=weeks,
    )


def subtract_time(
    dt: datetime,
    seconds: int = 0,
    minutes: int = 0,
    hours: int = 0,
    days: int = 0,
    weeks: int = 0,
) -> datetime:
    """
    Subtract time from a datetime.

    Args:
        dt: Datetime object
        seconds: Seconds to subtract
        minutes: Minutes to subtract
        hours: Hours to subtract
        days: Days to subtract
        weeks: Weeks to subtract

    Returns:
        New datetime with time subtracted
    """
    return add_time(
        dt,
        seconds=-seconds,
        minutes=-minutes,
        hours=-hours,
        days=-days,
        weeks=-weeks,
    )


def is_business_day(dt: datetime) -> bool:
    """
    Check if datetime is on a business day (Monday-Friday).

    Args:
        dt: Datetime object

    Returns:
        True if Monday-Friday, False if Saturday/Sunday
    """
    dt = ensure_utc(dt)
    return dt.weekday() < 5  # Monday=0, Friday=4


def is_weekend(dt: datetime) -> bool:
    """
    Check if datetime is on a weekend (Saturday/Sunday).

    Args:
        dt: Datetime object

    Returns:
        True if Saturday or Sunday, False otherwise
    """
    return not is_business_day(dt)


def days_until(target: datetime, from_dt: Optional[datetime] = None) -> int:
    """
    Calculate days until a target datetime.

    Args:
        target: Target datetime
        from_dt: Start datetime (defaults to now)

    Returns:
        Number of days until target (negative if in past)

    Examples:
        >>> target = utc_now() + timedelta(days=5)
        >>> days_until(target)
        5
    """
    if from_dt is None:
        from_dt = utc_now()

    from_dt = ensure_utc(from_dt)
    target = ensure_utc(target)

    return (target - from_dt).days


def is_within_days(
    dt: datetime,
    days: int,
    from_dt: Optional[datetime] = None,
) -> bool:
    """
    Check if datetime is within N days from now.

    Args:
        dt: Datetime to check
        days: Number of days
        from_dt: Start datetime (defaults to now)

    Returns:
        True if datetime is within N days in the future
    """
    if from_dt is None:
        from_dt = utc_now()

    from_dt = ensure_utc(from_dt)
    dt = ensure_utc(dt)

    return from_dt <= dt <= from_dt + timedelta(days=days)


def format_duration(seconds: float, short: bool = False) -> str:
    """
    Format duration in seconds as human-readable string.

    Args:
        seconds: Duration in seconds
        short: If True, use abbreviated format (e.g. "2h 30m")

    Returns:
        Formatted duration string

    Examples:
        >>> format_duration(3665)
        '1 hour 1 minute 5 seconds'

        >>> format_duration(3665, short=True)
        '1h 1m 5s'
    """
    total_seconds = int(seconds)
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    parts = []

    if days > 0:
        parts.append(f"{days}d" if short else f"{days} day{'s' if days > 1 else ''}")

    if hours > 0:
        parts.append(f"{hours}h" if short else f"{hours} hour{'s' if hours > 1 else ''}")

    if minutes > 0:
        parts.append(f"{minutes}m" if short else f"{minutes} minute{'s' if minutes > 1 else ''}")

    if secs > 0 or not parts:
        parts.append(f"{secs}s" if short else f"{secs} second{'s' if secs > 1 else ''}")

    if short:
        return " ".join(parts)
    else:
        return " ".join(parts)
