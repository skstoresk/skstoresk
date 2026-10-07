"""Central config — reads Streamlit secrets, degrades gracefully when missing."""

try:
    import streamlit as st

    def _read(name, default=""):
        try:
            return st.secrets.get(name, default)
        except Exception:
            return default
except Exception:  # not running inside streamlit (e.g. tools/)
    def _read(name, default=""):
        return default


def get_secret(name, default=""):
    return _read(name, default)


SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_ANON_KEY = get_secret("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = get_secret("SUPABASE_SERVICE_KEY")
ADMIN_USER = get_secret("ADMIN_USER", "admin")
ADMIN_PASS = get_secret("ADMIN_PASS", "")
GMAIL_USER = get_secret("GMAIL_USER", "")
GMAIL_APP_PASSWORD = get_secret("GMAIL_APP_PASSWORD", "")
ADMIN_NOTIFY_EMAIL = get_secret("ADMIN_NOTIFY_EMAIL", "")
STORE_NAME = get_secret("STORE_NAME", "SK Store")
APP_URL = get_secret("APP_URL", "").rstrip("/")


def supabase_configured() -> bool:
    return bool(SUPABASE_URL and (SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY))


def email_configured() -> bool:
    return bool(GMAIL_USER and GMAIL_APP_PASSWORD)
