"""SK STORE — main app (Streamlit + Supabase)."""
import streamlit as st

from lib import config

st.set_page_config(
    page_title=f"{config.STORE_NAME} — Online Shopping",
    page_icon="🛍️",
    layout="wide",
)

# theme
try:
    with open("assets/style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

if not config.supabase_configured():
    st.error(
        "⚙️ **Setup incomplete.** Streamlit Secrets me `SUPABASE_URL` aur keys add karein.\n\n"
        "README.md me step-by-step guide hai."
    )
    st.stop()

if "cart" not in st.session_state:
    st.session_state.cart = {}

home = st.Page("views/home.py", title="Home", icon="🏠", default=True)
product = st.Page("views/product.py", title="Product", icon="📦", url_path="product")
cart = st.Page("views/cart.py", title="Cart", icon="🛒", url_path="cart")
checkout = st.Page("views/checkout.py", title="Checkout", icon="💳", url_path="checkout")
track = st.Page("views/track.py", title="Track Order", icon="🚚", url_path="track")
admin = st.Page("views/admin.py", title="Admin", icon="🔐", url_path="admin")

pg = st.navigation(
    [home, product, cart, checkout, track, admin],
    position="hidden",
)

# ---------- custom top header ----------
cart_count = sum(st.session_state.cart.values())
h1, h2, h3, h4 = st.columns([5, 1.2, 1.4, 1.2])
with h1:
    st.markdown(f"<div class='sk-logo'>🛍️ {config.STORE_NAME}</div>", unsafe_allow_html=True)
with h2:
    if st.button("🏠 Home", use_container_width=True, key="nav_home"):
        st.switch_page("views/home.py")
with h3:
    if st.button(f"🛒 Cart ({cart_count})", use_container_width=True, key="nav_cart"):
        st.switch_page("views/cart.py")
with h4:
    if st.button("🚚 Track", use_container_width=True, key="nav_track"):
        st.switch_page("views/track.py")
st.divider()

pg.run()

# ---------- footer ----------
st.markdown(
    "<div class='sk-footer'>Made with ❤ &nbsp;&nbsp;|&nbsp;&nbsp; © 2026 Kaleem. All rights reserved.</div>",
    unsafe_allow_html=True,
)
