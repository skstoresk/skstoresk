#!/usr/bin/env python3
"""GitHub Action worker: writes docs/share/<slug>.html from the dispatch payload.

Triggered by repository_dispatch event 'generate-share-pages' with client_payload:
  {"action": "upsert"|"delete",
   "product": {"id", "slug", "name", "description", "price", "image"}}

Writes both <slug>.html (short, product-name link) and <id>.html (stable alias
so older links keep working). No Supabase access needed — payload has everything.
"""
import html
import json
import os
import sys
from pathlib import Path

APP_URL = "https://skstoresk-2.streamlit.app"
PAGES_BASE = "https://skstoresk.github.io/skstoresk"
STORE = "SK Store"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>{title} | {store}</title>
<meta name="description" content="{desc}" />
<meta property="og:type" content="product" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{desc}" />
<meta property="og:image" content="{image}" />
<meta property="og:url" content="{page_url}" />
<meta property="og:site_name" content="{store}" />
<meta property="product:price:amount" content="{price}" />
<meta property="product:price:currency" content="PKR" />
<link rel="canonical" href="{target}" />
<meta http-equiv="refresh" content="0; url={target}" />
</head>
<body>
<p>Redirecting to <a href="{target}">{title}</a>...</p>
<script>window.location.replace("{target}");</script>
</body>
</html>
"""

INDEX = ('<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url='
         + APP_URL + '" /></head><body></body></html>')


def main() -> int:
    raw = os.environ.get("PAYLOAD", "").strip()
    if not raw:
        print("No PAYLOAD env — nothing to do.")
        return 0
    payload = json.loads(raw)
    action = payload.get("action", "upsert")
    prod = payload.get("product") or {}
    pid = str(prod.get("id") or "")
    slug = str(prod.get("slug") or "").strip() or pid
    if not pid:
        print("No product id in payload.")
        return 0

    outdir = Path("docs/share")
    outdir.mkdir(parents=True, exist_ok=True)
    idx = outdir / "index.html"
    if not idx.exists():
        idx.write_text(INDEX, encoding="utf-8")

    targets = [f"{slug}.html"]
    if pid != slug:
        targets.append(f"{pid}.html")

    if action == "delete":
        for t in targets:
            p = outdir / t
            if p.exists():
                p.unlink()
                print(f"deleted {t}")
        return 0

    title = prod.get("name") or "Product"
    desc = str(prod.get("description") or "")[:200]
    price = prod.get("price", "")
    image = prod.get("image") or ""
    target = f"{APP_URL}/product?p={pid}"
    page_url = f"{PAGES_BASE}/share/{slug}.html"
    body = PAGE.format(
        title=html.escape(title), desc=html.escape(desc),
        image=html.escape(image), price=html.escape(str(price)),
        store=html.escape(STORE), target=html.escape(target),
        page_url=html.escape(page_url),
    )
    for t in targets:
        (outdir / t).write_text(body, encoding="utf-8")
        print(f"wrote {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
