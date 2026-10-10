"""SK Store — Home: banners, new arrivals, discounts, search & categories."""
import html

import streamlit as st
import streamlit.components.v1 as components

from lib import db, ui
from lib.utils import format_price, is_new, sale_price

ui.public_header()


# ---------------- quick buy: banner Shop Now → same page par buy (koi naya page nahi) ----------------
def _clear_quickbuy():
    try:
        del st.query_params["quickbuy"]
    except Exception:
        pass


_qb_id = st.query_params.get("quickbuy")
if _qb_id:
    _qp = db.get_product(_qb_id)
    if _qp and _qp.get("is_active", True):
        _qimgs = _qp.get("images") or []
        _qstock = int(_qp.get("stock") or 0)
        with st.container(border=True):
            _qh1, _qh2 = st.columns([6, 1])
            with _qh1:
                st.markdown("### ⚡ Quick Buy")
            with _qh2:
                if st.button("✖", key=f"qb_x_{_qb_id}"):
                    _clear_quickbuy()
                    st.rerun()
            _qc1, _qc2 = st.columns([1, 1.6])
            with _qc1:
                if _qimgs:
                    st.image(_qimgs[0], use_container_width=True)
            with _qc2:
                st.markdown(f"**{_qp['name']}**")
                st.markdown(f"## {format_price(sale_price(_qp))}")
                if _qp.get("discount_price"):
                    st.caption(f"~~{format_price(_qp['price'])}~~  🔥 Discount!")
                if _qstock <= 0:
                    st.error("Out of Stock")
                elif _qstock <= 5:
                    st.warning(f"⚡ Sirf {_qstock} reh gaye hain!")
                _qqty = st.number_input("Quantity", min_value=1, max_value=max(_qstock, 1),
                                        value=1, step=1, key=f"qb_qty_{_qb_id}")
                _qb1, _qb2 = st.columns(2)
                with _qb1:
                    if st.button("🛒 Add to Cart", key=f"qb_add_{_qb_id}",
                                 disabled=_qstock <= 0, use_container_width=True):
                        _cart = st.session_state.get("cart", {})
                        _cart[_qb_id] = _cart.get(_qb_id, 0) + int(_qqty)
                        st.session_state.cart = _cart
                        _clear_quickbuy()
                        st.toast("✅ Cart mein add ho gaya", icon="🛒")
                        st.rerun()
                with _qb2:
                    if st.button("⚡ Buy Now", key=f"qb_buy_{_qb_id}", type="primary",
                                 disabled=_qstock <= 0, use_container_width=True):
                        _cart = st.session_state.get("cart", {})
                        _cart[_qb_id] = _cart.get(_qb_id, 0) + int(_qqty)
                        st.session_state.cart = _cart
                        _clear_quickbuy()
                        st.switch_page("views/cart.py")
    else:
        _clear_quickbuy()


# ---------------- banners: cinematic ad-style (top = auto carousel) ----------------
def show_banners(placement):
    try:
        banners = db.get_banners(placement=placement, active_only=True)
    except Exception:
        # purani DB (placement column nahi) — sab kuch top par dikhao
        banners = db.get_banners(active_only=True) if placement == "top" else []
    if not banners:
        return
    if placement == "top" and len(banners) > 1:
        components.html(ui.banner_carousel_html(banners), height=372, scrolling=False)
    else:
        for b in banners:
            st.markdown(ui.banner_ad_html(b), unsafe_allow_html=True)


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
            components.html(ui.product_slideshow_html(imgs, p["id"], height=200, interval=3000),
                            height=210, scrolling=False)
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
