"""Shared page chrome: public header/footer, admin header/footer."""
from urllib.parse import quote_plus

import streamlit as st

from . import config, db


def public_header():
    """Animated big store-name hero + compact nav (no wasted space, no theme picker)."""
    st.session_state.setdefault("cart", {})
    cart_count = sum(st.session_state["cart"].values())
    st.markdown(
        "<div class='sk-hero'>"
        "<div class='sk-hero-name'><span class='sk-hero-emoji'>🛍️</span> "
        f"<span class='sk-hero-text'>{config.STORE_NAME.upper()}</span></div>"
        "<div class='sk-hero-tag'>Quality Products &nbsp;•&nbsp; Cash on Delivery</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    n1, n2, n3 = st.columns(3)
    with n1:
        if st.button("🏠 Home", use_container_width=True, key="nav_home"):
            st.switch_page("views/home.py")
    with n2:
        if st.button(f"🛒 Cart ({cart_count})", use_container_width=True, key="nav_cart"):
            st.switch_page("views/cart.py")
    with n3:
        if st.button("🚚 Track", use_container_width=True, key="nav_track"):
            st.switch_page("views/track.py")
    st.divider()


def admin_header():
    """Admin portal header: logo + ADMIN tag + Logout. No public nav."""
    a1, a2 = st.columns([6, 1.4])
    with a1:
        st.markdown(
            f"<div class='sk-logo'>🛍️ {config.STORE_NAME} <span class='sk-admin-tag'>ADMIN</span></div>",
            unsafe_allow_html=True,
        )
    with a2:
        if st.button("🚪 Logout", use_container_width=True, key="admin_logout"):
            st.session_state.admin_authed = False
            st.switch_page("views/home.py")
    st.divider()


def public_footer():
    """Public footer: contact email + WhatsApp button + copyright."""
    wa = (db.get_setting("whatsapp_number", "") or "").strip()
    wa_btn = ""
    if wa:
        digits = "".join(ch for ch in wa if ch.isdigit())
        if digits.startswith("0"):
            digits = "92" + digits[1:]
        if digits:
            text = quote_plus("Assalam-o-Alaikum! Mujhe SK Store se maloomat chahiye.")
            wa_btn = (
                f"<a class='sk-wa-btn' target='_blank' "
                f"href='https://wa.me/{digits}?text={text}'>💬 WhatsApp par rabta karein</a>"
            )
    email = config.GMAIL_USER or ""
    st.markdown(
        "<div class='sk-footer'>"
        f"<div class='sk-footer-contact'>📧 {email}</div>"
        f"{wa_btn}"
        "<div class='sk-footer-copy'>Made with ❤ &nbsp;|&nbsp; © 2026 Kaleem. All rights reserved.</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def admin_footer():
    st.markdown(
        "<div class='sk-footer sk-footer-admin'>© 2026 Kaleem — Admin Portal</div>",
        unsafe_allow_html=True,
    )


def stop_with_footer():
    """st.stop() jaisi, lekin footer dikha kar — taake adhoore pages par bhi footer aye."""
    public_footer()
    st.stop()
