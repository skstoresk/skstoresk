"""Supabase data layer. All calls go through the Streamlit backend
using the service_role key from secrets (never exposed to the browser)."""
import random
import re
import string

from supabase import create_client

from . import config

_client = None


def client():
    """Supabase client, or None when secrets are not configured yet."""
    global _client
    if not config.supabase_configured():
        return None
    if _client is None:
        key = config.SUPABASE_SERVICE_KEY or config.SUPABASE_ANON_KEY
        _client = create_client(config.SUPABASE_URL, key)
    return _client


def _ok(resp):
    return resp.data if resp else []


# ---------------- categories ----------------
def get_categories():
    sb = client()
    if not sb:
        return []
    return _ok(sb.table("categories").select("*").order("name").execute())


def add_category(name: str):
    return client().table("categories").insert({"name": name.strip()}).execute()


def delete_category(cat_id: str):
    return client().table("categories").delete().eq("id", cat_id).execute()


# ---------------- products ----------------
def _base_products_query(sb, active_only=True, category_id=None):
    q = sb.table("products").select("*, categories(name)")
    if active_only:
        q = q.eq("is_active", True)
    if category_id:
        q = q.eq("category_id", category_id)
    return q


def get_products(active_only=True, category_id=None, search=None):
    sb = client()
    if not sb:
        return []
    if search:
        # query todne wale characters hatao
        search = re.sub(r"[%(),]", "", search).strip()
    if search:
        # name, description ya tags me se kahin bhi mile
        try:
            q = _base_products_query(sb, active_only, category_id)
            return _ok(
                q.or_(f"name.ilike.%{search}%,description.ilike.%{search}%,"
                      f"tags.ilike.%{search}%")
                 .order("created_at", desc=True)
                 .execute()
            )
        except Exception:
            # purani DB (tags column nahi) — sirf name me dhoondo
            q = _base_products_query(sb, active_only, category_id)
            return _ok(q.ilike("name", f"%{search}%").order("created_at", desc=True).execute())
    q = _base_products_query(sb, active_only, category_id)
    q = q.order("created_at", desc=True)
    return _ok(q.execute())


def get_product(pid: str):
    sb = client()
    if not sb:
        return None
    rows = _ok(sb.table("products").select("*, categories(name)").eq("id", pid).execute())
    return rows[0] if rows else None


def create_product(data: dict):
    return client().table("products").insert(data).execute()


def update_product(pid: str, data: dict):
    return client().table("products").update(data).eq("id", pid).execute()


def delete_product(pid: str):
    return client().table("products").delete().eq("id", pid).execute()


# ---------------- banners ----------------
def get_banners(banner_type=None, placement=None, active_only=True):
    sb = client()
    if not sb:
        return []
    q = sb.table("banners").select("*")
    if active_only:
        q = q.eq("is_active", True)
    if banner_type:
        q = q.eq("banner_type", banner_type)
    if placement:
        q = q.eq("placement", placement)
    q = q.order("sort_order").order("created_at", desc=True)
    return _ok(q.execute())


def create_banner(data: dict):
    return client().table("banners").insert(data).execute()


def update_banner(bid: str, data: dict):
    return client().table("banners").update(data).eq("id", bid).execute()


def delete_banner(bid: str):
    return client().table("banners").delete().eq("id", bid).execute()


# ---------------- orders ----------------
ORDER_STATUSES = ["Pending", "Confirmed", "Shipped", "Delivered", "Cancelled"]


def _gen_order_number():
    return "SK-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_order(data: dict):
    sb = client()
    for _ in range(5):
        data["order_number"] = _gen_order_number()
        try:
            return sb.table("orders").insert(data).execute()
        except Exception:
            continue
    raise RuntimeError("Could not generate a unique order number")


def get_orders(limit=200):
    sb = client()
    if not sb:
        return []
    return _ok(sb.table("orders").select("*").order("created_at", desc=True).limit(limit).execute())


def get_order_by_number(order_number: str):
    sb = client()
    if not sb:
        return None
    rows = _ok(
        sb.table("orders")
        .select("*")
        .eq("order_number", order_number.strip().upper())
        .execute()
    )
    return rows[0] if rows else None


def update_order(oid: str, fields: dict):
    return client().table("orders").update(fields).eq("id", oid).execute()


# ---------------- settings ----------------
def get_setting(key: str, default=""):
    sb = client()
    if not sb:
        return default
    rows = _ok(sb.table("settings").select("value").eq("key", key).execute())
    return rows[0]["value"] if rows else default


def set_setting(key: str, value: str):
    return (
        client()
        .table("settings")
        .upsert({"key": key, "value": str(value)}, on_conflict="key")
        .execute()
    )


# ---------------- reviews ----------------
def get_reviews(product_id, approved_only=True):
    sb = client()
    if not sb:
        return []
    q = sb.table("reviews").select("*").eq("product_id", product_id)
    if approved_only:
        q = q.eq("is_approved", True)
    q = q.order("created_at", desc=True)
    return _ok(q.execute())


def create_review(data: dict):
    return client().table("reviews").insert(data).execute()


def get_all_reviews():
    sb = client()
    if not sb:
        return []
    return _ok(sb.table("reviews").select("*, products(name)")
               .order("created_at", desc=True).execute())


def update_review(rid: str, data: dict):
    return client().table("reviews").update(data).eq("id", rid).execute()


def delete_review(rid: str):
    return client().table("reviews").delete().eq("id", rid).execute()
