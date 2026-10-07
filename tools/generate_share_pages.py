"""Generate Facebook-friendly share pages (OG tags) for every product.

Har product ke liye docs/share/<product_id>.html banta hai jisme
Open Graph tags (title, image, price) hote hain — Facebook link paste
karte hi auto preview card bana leta hai. Page khulne par customer
foran asal product page par redirect ho jata hai.

Usage:
    python tools/generate_share_pages.py

Secrets: .streamlit/secrets.toml (SUPABASE_URL, SUPABASE_SERVICE_KEY, APP_URL)
         ya environment variables.
Phir: git add docs/share && git commit && git push
GitHub repo → Settings → Pages → Deploy from branch → docs/ folder.
Share link format: https://<user>.github.io/<repo>/share/<product_id>.html
"""
import html
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from supabase import create_client
except ImportError:
    print("supabase package nahi mila. Pehle: pip install supabase")
    sys.exit(1)


def load_conf():
    conf = {}
    p = ROOT / ".streamlit" / "secrets.toml"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            m = re.match(r'\s*([A-Z_]+)\s*=\s*"(.*)"\s*$', line)
            if m:
                conf[m.group(1)] = m.group(2)
    for k in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY", "APP_URL"):
        conf.setdefault(k, os.environ.get(k, ""))
    return conf


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
<p>Redirecting to <a href="{target}">{title}</a>…</p>
<script>window.location.replace("{target}");</script>
</body>
</html>
"""


def main():
    conf = load_conf()
    if not conf["SUPABASE_URL"] or not conf["SUPABASE_SERVICE_KEY"]:
        print("SUPABASE_URL / SUPABASE_SERVICE_KEY nahi mile (.streamlit/secrets.toml ya env).")
        sys.exit(1)
    if not conf["APP_URL"]:
        print("APP_URL nahi mila (jaise https://skstore.streamlit.app).")
        sys.exit(1)

    sb = create_client(conf["SUPABASE_URL"], conf["SUPABASE_SERVICE_KEY"])
    products = (
        sb.table("products").select("id,name,description,price,discount_percent,images")
        .eq("is_active", True).execute().data or []
    )

    # GitHub Pages base: GITHUB_PAGES_BASE env ya guess
    pages_base = os.environ.get("GITHUB_PAGES_BASE", "").rstrip("/")
    outdir = ROOT / "docs" / "share"
    outdir.mkdir(parents=True, exist_ok=True)

    for p in products:
        pid = p["id"]
        title = p.get("name") or "Product"
        desc = (p.get("description") or "")[:200]
        disc = float(p.get("discount_percent") or 0)
        price = round(float(p.get("price") or 0) * (1 - disc / 100))
        image = (p.get("images") or [""])[0]
        target = f"{conf['APP_URL'].rstrip('/')}/product?p={pid}"
        page_url = f"{pages_base}/share/{pid}.html" if pages_base else target
        (outdir / f"{pid}.html").write_text(
            PAGE.format(
                title=html.escape(title), desc=html.escape(desc),
                image=html.escape(image), price=price,
                store=html.escape(conf.get("STORE_NAME", "SK Store")),
                target=html.escape(target), page_url=html.escape(page_url),
            ),
            encoding="utf-8",
        )
        print(f"  wrote share/{pid}.html — {title}")

    (outdir / "index.html").write_text(
        f'<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url={conf["APP_URL"]}" />'
        "</head><body></body></html>",
        encoding="utf-8",
    )
    print(f"\nDone: {len(products)} share pages → docs/share/")
    print("Ab: git add docs/share && git commit -m 'share pages' && git push")


if __name__ == "__main__":
    main()
