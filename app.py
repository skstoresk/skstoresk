"""SK STORE — main app (Streamlit + Supabase)."""
import streamlit as st

from lib import config, db
from lib.themes import DEFAULT_THEME, theme_keys, theme_vars_css

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

# ---------- theme: admin ka default (public ke liye koi picker nahi) ----------
admin_theme = db.get_setting("site_theme", DEFAULT_THEME)
if admin_theme not in theme_keys():
    admin_theme = DEFAULT_THEME
st.markdown(theme_vars_css(admin_theme), unsafe_allow_html=True)

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

# header/footer har page khud render karta hai (lib/ui.py)
pg.run()
