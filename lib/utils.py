"""Small helpers: prices, YouTube links, NEW-badge logic."""
import re
from datetime import datetime, timezone


def format_price(amount) -> str:
    """1299 -> 'Rs 1,299'"""
    try:
        n = float(amount)
    except (TypeError, ValueError):
        n = 0.0
    return f"Rs {n:,.0f}"


def sale_price(price, discount_percent) -> float:
    try:
        d = float(discount_percent or 0)
    except (TypeError, ValueError):
        d = 0.0
    return round(float(price or 0) * (1 - d / 100))


def youtube_id(url: str):
    if not url:
        return None
    m = re.search(
        r"(?:youtube\.com/(?:watch\?v=|shorts/|embed/|live/)|youtu\.be/)([\w\-]{6,})",
        url,
    )
    return m.group(1) if m else None


def youtube_embed(url: str):
    vid = youtube_id(url)
    return f"https://www.youtube.com/embed/{vid}" if vid else None


def _parse_ts(value):
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_new(created_at, days: int = 7) -> bool:
    """True if the product was created within the last `days` days."""
    dt = _parse_ts(created_at)
    if not dt:
        return False
    try:
        days = int(days)
    except (TypeError, ValueError):
        days = 7
    return (datetime.now(timezone.utc) - dt).days < days
