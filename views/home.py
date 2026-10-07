"""SK Store — Home: banners, new arrivals, discounts, search & categories."""
import streamlit as st

from lib import config, db
from lib.utils import format_price, is_new, sale_price

st.title(f"🛍️ {config.STORE_NAME}")

# ---------------- banners ----------------
banners = db.get_banners(active_only=True)
for b in banners:
    img = f"<img src='{b['image_url']}' class='sk-banner-img' />" if b.get("image_url") else ""
    st.markdown(
        f"<div class='sk-banner sk-banner-{b['banner_type']}'>{img}"
        f"<div class='sk-banner-text'><div class='sk-banner-kicker'>"
        f"{'🆕 NEW ARRIVAL' if b['banner_type']=='new' else ('🔥 DISCOUNT' if b['banner_type']=='discount' else '📢')}</div>"
        f"<div class='sk-banner-title'>{b['title']}</div>"
        f"<div class='sk-banner-sub'>{b.get('subtitle','')}</div></div></div>",
        unsafe_allow_html=True,
    )

# ---------------- search + category filter ----------------
cats = db.get_categories()
cat_options = ["All categories"] + [c["name"] for c in cats]
cat_map = {c["name"]: c["id"] for c in cats}

c1, c2 = st.columns([2, 1])
search = c1.text_input("🔍 Search products", placeholder="e.g. watch, shoes…", label_visibility="collapsed")
chosen_cat = c2.selectbox("Category", cat_options, label_visibility="collapsed")

products = db.get_products(
    category_id=cat_map.get(chosen_cat) if chosen_cat != "All categories" else None,
    search=search or None,
)
new_days = int(db.get_setting("new_badge_days", "7") or 7)


def product_card(p):
    imgs = p.get("images") or []
    with st.container(border=True):
        if imgs:
            st.image(imgs[0], use_container_width=True)
        badges = ""
        if is_new(p.get("created_at"), new_days):
            badges += "<span class='sk-badge sk-badge-new'>NEW</span> "
        disc = float(p.get("discount_percent") or 0)
        if disc > 0:
            badges += f"<span class='sk-badge sk-badge-disc'>-{disc:g}%</span>"
        if badges:
            st.markdown(badges, unsafe_allow_html=True)
        st.markdown(f"**{p['name']}**")
        if disc > 0:
            st.markdown(
                f"<span class='sk-price'>{format_price(sale_price(p['price'], disc))}</span> "
                f"<span class='sk-price-old'>{format_price(p['price'])}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f"<span class='sk-price'>{format_price(p['price'])}</span>", unsafe_allow_html=True)
        stock = int(p.get("stock") or 0)
        if stock <= 0:
            st.markdown("<span class='sk-out'>Out of Stock</span>", unsafe_allow_html=True)
        if st.button("View 👀", key=f"view_{p['id']}", use_container_width=True, disabled=stock <= 0):
            st.query_params["p"] = p["id"]
            st.switch_page("views/product.py")


def product_grid(items, cols=3):
    if not items:
        st.info("Koi product nahi mila. 🔍")
        return
    for i in range(0, len(items), cols):
        row = st.columns(cols)
        for j, p in enumerate(items[i : i + cols]):
            with row[j]:
                product_card(p)


# ---------------- sections ----------------
if not search and chosen_cat == "All categories":
    new_items = [p for p in products if is_new(p.get("created_at"), new_days)][:6]
    if new_items:
        st.subheader("🆕 New Arrivals")
        product_grid(new_items)

    disc_items = [p for p in products if float(p.get("discount_percent") or 0) > 0][:6]
    if disc_items:
        st.subheader("🔥 On Discount")
        product_grid(disc_items)

    st.subheader("🛒 All Products")

product_grid(products)
