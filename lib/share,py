"""Product share links: slug URLs + auto-build trigger via GitHub Actions.

Flow: admin saves product -> slug (product-name based, stable) stored in DB ->
repository_dispatch sent to GitHub -> Action writes docs/share/<slug>.html ->
GitHub Pages deploys (~1-2 min). Facebook gets OG preview + direct product link.
"""
import json
import re
import unicodedata
import urllib.request

from . import config
from .utils import sale_price

PAGES_BASE = "https://skstoresk.github.io/skstoresk"


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:60] or "product"


def unique_slug(base: str, taken: set) -> str:
    if base not in taken:
        return base
    i = 2
    while f"{base}-{i}" in taken:
        i += 1
    return f"{base}-{i}"


def share_url_for(p: dict) -> str:
    slug = (p.get("slug") or "").strip()
    return f"{PAGES_BASE}/share/{slug or p['id']}.html"


def build_product_payload(p: dict) -> dict:
    return {
        "id": p.get("id"),
        "slug": (p.get("slug") or "").strip() or slugify(p.get("name") or ""),
        "name": p.get("name") or "Product",
        "description": (p.get("description") or "")[:200],
        "price": int(round(sale_price(p))),
        "image": (p.get("images") or [""])[0],
    }


def trigger_share_build(action: str, product: dict):
    """Fire repository_dispatch so the GitHub Action (re)builds the share page.
    Returns (ok: bool, message: str). Never raises."""
    token = (config.get_secret("GITHUB_TOKEN") or "").strip()
    repo = (config.get_secret("GITHUB_REPO") or "skstoresk/skstoresk").strip()
    if not token:
        return False, "GITHUB_TOKEN secret Streamlit me missing hai"
    if not product.get("id"):
        return False, "product id missing"
    try:
        body = json.dumps({
            "event_type": "generate-share-pages",
            "client_payload": {"action": action, "product": product},
        }).encode()
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/dispatches",
            data=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status in (200, 201, 204):
                return True, "ok"
            return False, f"GitHub status {resp.status}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)[:120]
