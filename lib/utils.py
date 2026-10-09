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


def _num(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def sale_price(p) -> float:
    """Product ki asal selling price.

    Pehle `discount_price` (direct sale wali qeemat) dekhta hai.
    Purani rows ke liye `discount_percent` se calculate karta hai,
    warna list `price` wapas karta hai.
    """
    price = _num(p.get("price"))
    dp = _num(p.get("discount_price"))
    if dp > 0:
        return round(dp, 2)
    dpc = _num(p.get("discount_percent"))
    if dpc > 0:
        return round(price * (1 - dpc / 100), 2)
    return round(price, 2)


def profit_per_unit(p) -> float:
    """Tumhara profit per unit: sale price − buy price − delivery − packing."""
    return round(
        sale_price(p)
        - _num(p.get("buy_price"))
        - _num(p.get("delivery_expense"))
        - _num(p.get("packing_expense")),
        2,
    )


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
