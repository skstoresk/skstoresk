"""SK STORE — Admin portal (/admin). Login required."""
import hmac

import streamlit as st

from lib import config, db, emailer, storage
from lib.themes import DEFAULT_THEME, theme_keys, theme_label
from lib.utils import format_price, sale_price

st.title("🔐 Admin Portal")

# ---------------- login ----------------
if not config.ADMIN_PASS:
    st.error("ADMIN_PASS secrets me set nahi hai. Pehle Streamlit Secrets configure karein.")
    st.stop()

if not st.session_state.get("admin_authed"):
    with st.form("admin_login"):
        st.subheader("Login")
        u = st.text_input("User ID")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary"):
            if hmac.compare_digest(u, config.ADMIN_USER) and hmac.compare_digest(p, config.ADMIN_PASS):
                st.session_state.admin_authed = True
                st.rerun()
            else:
                st.error("❌ Ghalat User ID ya Password.")
    st.stop()

if st.button("🚪 Logout"):
    st.session_state.admin_authed = False
    st.rerun()

tabs = st.tabs(["📊 Dashboard", "📦 Products", "🧾 Orders", "🖼️ Banners", "📁 Categories", "⚙️ Settings"])

# ================= DASHBOARD =================
with tabs[0]:
    st.subheader("Dashboard")
    products = db.get_products(active_only=False)
    orders = db.get_orders()
    pending = [o for o in orders if o["status"] == "Pending"]
    revenue = sum(float(o.get("total") or 0) for o in orders if o["status"] != "Cancelled")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Products", len(products))
    m2.metric("Total Orders", len(orders))
    m3.metric("Pending Orders", len(pending))
    m4.metric("Revenue (non-cancelled)", format_price(revenue))
    if pending:
        st.warning(f"⚠️ {len(pending)} orders pending hain — Orders tab me confirm karein.")

# ================= PRODUCTS =================
with tabs[1]:
    st.subheader("Products")
    cats = db.get_categories()
    cat_names = ["(No category)"] + [c["name"] for c in cats]
    cat_id_of = {c["name"]: c["id"] for c in cats}

    editing = st.session_state.get("editing_product")
    if editing:
        st.info(f"✏️ Editing: **{editing['name']}**")
        if st.button("❌ Cancel edit"):
            st.session_state.editing_product = None
            st.rerun()

    ex = editing or {}
    ex_images = list(ex.get("images") or [])

    with st.form("product_form", clear_on_submit=editing is None):
        name = st.text_input("Product Name *", value=ex.get("name", ""))
        description = st.text_area("Description", value=ex.get("description", ""))
        c1, c2, c3 = st.columns(3)
        price = c1.number_input("Price (Rs) *", min_value=0.0, value=float(ex.get("price") or 0))
        discount = c2.number_input("Discount %", min_value=0.0, max_value=90.0,
                                   value=float(ex.get("discount_percent") or 0))
        stock = c3.number_input("Stock *", min_value=0, value=int(ex.get("stock") or 0))
        cur_cat = next((c["name"] for c in cats if c["id"] == ex.get("category_id")), "(No category)")
        category = st.selectbox("Category", cat_names,
                                index=cat_names.index(cur_cat) if cur_cat in cat_names else 0)

        st.markdown("**Images (minimum 2, maximum 6)** *")
        if ex_images:
            st.caption(f"Abhi {len(ex_images)} image(s) hain — hatane ke liye select karein:")
            remove = st.multiselect("Remove images", ex_images, format_func=lambda u: u[-40:])
            kept = [u for u in ex_images if u not in remove]
            for u in kept:
                st.image(u, width=120)
        else:
            kept = []
        new_imgs = st.file_uploader("Nayi images upload karein (jpg/png/webp)",
                                    type=["jpg", "jpeg", "png", "webp"],
                                    accept_multiple_files=True)
        st.caption(f"Total images hongi: {len(kept) + len(new_imgs or [])} (2–6 zaroori)")

        st.markdown("**Product Video (optional)**")
        vchoice = st.radio("Video source", ["No video", "Upload video", "YouTube link"],
                           index=0 if not ex.get("video_url") and not ex.get("youtube_url")
                           else (1 if ex.get("video_url") else 2))
        video_file, youtube_link = None, ""
        if vchoice == "Upload video":
            video_file = st.file_uploader("Video file (mp4/webm/mov)", type=["mp4", "webm", "mov"])
