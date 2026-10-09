"""Admin 'System Check': real-time health checks with Roman-Urdu fix hints.

Har check (name, ok, hint) deta hai. Koi bhi check fail ho to hint me seedha
hal bataya jata hai — taake Kaleem khud theek kar sake.
"""
import urllib.request

from . import config, db


def _ok(name):
    return {"name": name, "ok": True, "hint": ""}


def _fail(name, hint):
    return {"name": name, "ok": False, "hint": hint}


def run_checks():
    """Saare checks chalao. Returns list of {name, ok, hint}."""
    checks = []

    # 1. code files (imports) — koi file upload karna bhool jaye to yahin pakra jayega
    mods = ["lib.config", "lib.db", "lib.ui", "lib.share", "lib.emailer",
            "lib.storage", "lib.utils", "lib.themes"]
    missing = []
    for m in mods:
        try:
            __import__(m)
        except Exception:  # noqa: BLE001
            missing.append(m.replace("lib.", "") + ".py")
    if missing:
        checks.append(_fail(
            "Code files",
            "Ye files GitHub par missing hain: " + ", ".join(missing) +
            " — inhe upload karo, warna site crash hogi."))
    else:
        checks.append(_ok("Code files"))

    # 2. Supabase connection
    try:
        sb = db.client()
        if not sb:
            raise RuntimeError("client nahi bana")
        sb.table("products").select("id").limit(1).execute()
        checks.append(_ok("Supabase connection"))
    except Exception as e:  # noqa: BLE001
        checks.append(_fail(
            "Supabase connection",
            f"Database se rabta nahi ho raha ({str(e)[:100]}). "
            "Streamlit Secrets me SUPABASE_URL / SUPABASE_SERVICE_KEY check karo."))
        return checks  # aage ke DB checks ka faida nahi

    # 3. zaroori columns (migration reh jaye to yahin pakra jayega)
    needed = ["slug", "tags", "buy_price", "delivery_expense", "packing_expense",
              "discount_price", "category_id", "images", "video_url",
              "youtube_url", "stock", "is_active"]
    missing_cols = []
    for col in needed:
        try:
            sb.table("products").select(col).limit(1).execute()
        except Exception:  # noqa: BLE001
            missing_cols.append(col)
    if missing_cols:
        checks.append(_fail(
            "Database columns",
            "Ye columns missing hain: " + ", ".join(missing_cols) +
            " — Supabase SQL Editor me sql/schema.sql wala migration chalao."))
    else:
        checks.append(_ok("Database columns"))

    # 4. storage buckets
    try:
        raw = sb.storage.list_buckets() or []
        names = set()
        for b in raw:
            names.add(b.get("name") if isinstance(b, dict) else getattr(b, "name", ""))
        miss_b = [b for b in ("product-images", "product-videos") if b not in names]
        if miss_b:
            checks.append(_fail(
                "Storage buckets",
                "Ye buckets nahi hain: " + ", ".join(miss_b) +
                " — schema.sql ka storage wala hissa Supabase me chalao."))
        else:
            checks.append(_ok("Storage buckets"))
    except Exception as e:  # noqa: BLE001
        checks.append(_fail("Storage buckets", f"Check nahi ho saka ({str(e)[:100]})."))

    # 5. secrets
    if config.SUPABASE_URL:
        checks.append(_ok("Secret: SUPABASE_URL"))
    else:
        checks.append(_fail("Secret: SUPABASE_URL", "Streamlit Secrets me SUPABASE_URL missing hai."))
    app_url = (config.APP_URL or "").strip()
    if not app_url:
        checks.append(_fail("Secret: APP_URL", "APP_URL missing hai — apni streamlit.app wali URL dalo."))
    elif "supabase.co" in app_url:
        checks.append(_fail(
            "Secret: APP_URL",
            "APP_URL me Supabase ka URL dala hua hai! Wahan apni SITE ki URL honi chahiye "
            "(jaise https://skstoresk-2.streamlit.app). Foran theek karo."))
    else:
        checks.append(_ok("Secret: APP_URL"))
    if config.ADMIN_PASS:
        checks.append(_ok("Secret: ADMIN_PASS"))
    else:
        checks.append(_fail("Secret: ADMIN_PASS", "ADMIN_PASS missing hai — admin login kaam nahi karega."))
    if (config.get_secret("GITHUB_TOKEN") or "").strip():
        checks.append(_ok("Auto share pages (token)"))
    else:
        checks.append(_fail(
            "Auto share pages (token)",
            "GITHUB_TOKEN secret missing hai — product save par share link auto nahi banega."))
    if config.email_configured():
        checks.append(_ok("Email (Gmail)"))
    else:
        checks.append(_fail(
            "Email (Gmail)",
            "GMAIL_USER / App Password missing hai — order confirmation emails nahi jayenge."))

    # 6. GitHub workflow file (public API — token ki zaroorat nahi)
    repo = (config.get_secret("GITHUB_REPO") or "skstoresk/skstoresk").strip()
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/contents/.github/workflows/share-pages.yml",
            headers={"User-Agent": "sk-store-check"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                checks.append(_ok("GitHub: share-pages workflow"))
            else:
                raise RuntimeError(f"status {resp.status}")
    except Exception:  # noqa: BLE001
        checks.append(_fail(
            "GitHub: share-pages workflow",
            "Workflow file repo me nahi mili — .github/workflows/share-pages.yml upload karo, "
            "warna auto share pages nahi banenge."))

    return checks
