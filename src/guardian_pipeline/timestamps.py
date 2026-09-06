"""Decoding Unix timestamps, and rendering datetimes in Zulu format with second
precision (``2026-05-22T23:11:34Z``) — the one string format the pipeline's data
files use."""

import datetime


def from_unix(timestamp: int) -> datetime.datetime:
    """Decode a Unix timestamp as an aware UTC datetime."""
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc)


def format_iso_utc(dt: datetime.datetime) -> str:
    """Format an aware datetime in Zulu format."""
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(f'naive datetime: {dt!r}')
    return dt.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def now_iso_utc() -> str:
    """Current UTC time in Zulu format."""
    return format_iso_utc(datetime.datetime.now(datetime.timezone.utc))
