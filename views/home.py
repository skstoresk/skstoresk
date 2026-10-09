"""SK Store — Home: banners, new arrivals, discounts, search & categories."""
import html

import streamlit as st
import streamlit.components.v1 as components

from lib import db, ui
from lib.utils import format_price, is_new, sale_price

ui.public_header()


def _card_slideshow(p):
    """Product card image: auto-cycling slideshow (3s, fade). No Streamlit chrome."""
    imgs = (p.get("images") or [])[:6]
    if not imgs:
        return ""
    pid = p["id"]
    slides = "\n".join(
        f'<img src="{html.escape(u, quote=True)}" class="skcs-img{" skcs-on" if i == 0 else ""}" alt="">'
        for i, u in enumerate(imgs)
    )
    return f"""
<div class="skcs" id="skcs-{pid}">{slides}</div>
<style>
.skcs {{ position: relative; width: 100%; height: 200px; overflow: hidden;
         border-radius: 10px; background: #fff; }}
.skcs-img {{ position: absolute; inset: 0; width: 100%; height: 100%;
             object-fit: contain; opacity: 0; transition: opacity 0.8s ease; }}
.skcs-img.skcs-on {{ opacity: 1; }}
</style>
<script>
(function(){{
  var box = document.getElementById('skcs-{pid}');
  if (!box) return;
  var imgs = box.querySelectorAll('.skcs-img');
  if (imgs.length < 2) return;
  var i = 0;
  setInterval(function(){{
    imgs[i].classList.remove('skcs-on');
    i = (i + 1) % imgs.length;
    imgs[i].classList.add('skcs-on');
  }}, 3000);
}})();
</script>
"""

# ---------------- banners (4 placements: top / middle / bottom / product) ----------------
def _banner_html(b):
    img = f"<img src='{b['image_url']}' class='sk-banner-img' />" if b.get("image_url") else ""
    return (
        f"<div class='sk-banner sk-banner-{b['banner_type']}'>{img}"
        f"<div class='sk-banner-text'><div class='sk-banner-kicker'>"
        f"{'🆕 NEW ARRIVAL' if b['banner_type']=='new' else ('🔥 DISCOUNT' if b['banner_type']=='discount' else '📢')}</div>"
        f"<div class='sk-banner-title'>{b['title']}</div>"
        f"<div class='sk-banner-sub'>{b.get('subtitle','')}</div></div></div>"
    )


def show_banners(placement):
    try:
        banners = db.get_banners(placement=placement, active_only=True)
    except Exception:
        # purani DB (placement column nahi) — sab kuch top par dikhao
        banners = db.get_banners(active_only=True) if placement == "top" else []
    for b in banners:
        st.markdown(_banner_html(b), unsafe_allow_html=True)


show_banners("top")

# ---------------- search + category filter (compact, centered) ----------------
cats = db.get_categories()
cat_options = ["All categories"] + [c["name"] for c in cats]
cat_map = {c["name"]: c["id"] for c in cats}

_s1, _s2, _s3 = st.columns([1, 2.4, 1])
with _s2:
    _t1, _t2 = st.columns([2.3, 1])
    search = _t1.text_input("🔍 Search products", placeholder="🔍  Search products…",
                            label_visibility="collapsed")
    chosen_cat = _t2.selectbox("Category", cat_options, label_visibility="collapsed")

products = db.get_products(
    category_id=cat_map.get(chosen_cat) if chosen_cat != "All categories" else None,
    search=search or None,
)
new_days = int(db.get_setting("new_badge_days", "7") or 7)


def product_card(p, key_prefix=""):
    imgs = p.get("images") or []
    with st.container(border=True):
        if imgs:
            components.html(_card_slideshow(p), height=210, scrolling=False)
        badges = ""
        if is_new(p.get("created_at"), new_days):
            badges += "<span class='sk-badge sk-badge-new'>NEW</span> "
        sp = sale_price(p)
        list_price = float(p.get("price") or 0)
        if sp < list_price and list_price > 0:
            pct = round((1 - sp / list_price) * 100)
            badges += f"<span class='sk-badge sk-badge-disc'>-{pct:g}%</span>"
        if badges:
            st.markdown(badges, unsafe_allow_html=True)
        st.markdown(f"<span class='sk-card-name'>{html.escape(p['name'])}</span>",
                    unsafe_allow_html=True)
        if sp < list_price:
            st.markdown(
                f"<span class='sk-price'>{format_price(sp)}</span> "
                f"<span class='sk-price-old'>{format_price(list_price)}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"<span class='sk-price'>{format_price(list_price)}</span>", unsafe_allow_html=True)
        stock = int(p.get("stock") or 0)
        if stock <= 0:
            st.markdown("<span class='sk-out'>Out of Stock</span>", unsafe_allow_html=True)
        if st.button("View 👀", key=f"view_{key_prefix}_{p['id']}", use_container_width=True, disabled=stock <= 0):
            st.session_state["view_pid"] = p["id"]
            st.query_params["p"] = p["id"]
            st.switch_page("views/product.py")


def product_grid(items, cols=3, key_prefix=""):
    if not items:
        st.info("Koi product nahi mila. 🔍")
        return
    for i in range(0, len(items), cols):
        row = st.columns(cols)
        for j, p in enumerate(items[i : i + cols]):
            with row[j]:
                product_card(p, key_prefix=key_prefix)


# ---------------- sections ----------------
if not search and chosen_cat == "All categories":
    new_items = [p for p in products if is_new(p.get("created_at"), new_days)][:6]
    if new_items:
        st.subheader("🆕 New Arrivals")
        product_grid(new_items, key_prefix="new")

    disc_items = [p for p in products if sale_price(p) < float(p.get("price") or 0)][:6]
    if disc_items:
        st.subheader("🔥 On Discount")
        product_grid(disc_items, key_prefix="disc")

    show_banners("middle")

    st.subheader("🛒 All Products")

product_grid(products, key_prefix="all")
show_banners("bottom")

ui.public_footer()
