"""Shared page chrome: public header/footer, admin header/footer."""
from urllib.parse import quote_plus

import streamlit as st

from . import config, db


_WA_SVG = (
    '<svg viewBox="0 0 24 24" width="24" height="24" fill="#ffffff">'
    '<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 '
    '1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-'
    '.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-'
    '.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-'
    '1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.'
    '712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-'
    '.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 '
    '01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 '
    '5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 '
    '4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 '
    '11.821 0 00-3.48-8.413z"/></svg>'
)


def _wa_url():
    """WhatsApp chat link ya None (number Settings me na ho to)."""
    wa = (db.get_setting("whatsapp_number", "") or "").strip()
    if not wa:
        return None
    digits = "".join(ch for ch in wa if ch.isdigit())
    if digits.startswith("0"):
        digits = "92" + digits[1:]
    if not digits:
        return None
    text = quote_plus("Assalam-o-Alaikum! Mujhe SK Store se maloomat chahiye.")
    return f"https://wa.me/{digits}?text={text}"


def public_header():
    """Animated big store-name hero + compact nav + WhatsApp (top-right)."""
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
    n1, n2, n3, n4 = st.columns([1.15, 1.45, 1.15, 0.55])
    with n1:
        if st.button("🏠 Home", use_container_width=True, key="nav_home"):
            st.switch_page("views/home.py")
    with n2:
        if st.button(f"🛒 Cart ({cart_count})", use_container_width=True, key="nav_cart"):
            st.switch_page("views/cart.py")
    with n3:
        if st.button("🚚 Track", use_container_width=True, key="nav_track"):
            st.switch_page("views/track.py")
    with n4:
        wa = _wa_url()
        if wa:
            st.markdown(
                f"<div style='text-align:center;padding-top:2px'>"
                f"<a class='sk-wa-float' target='_blank' href='{wa}'>{_WA_SVG}</a></div>",
                unsafe_allow_html=True,
            )
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
    """Public footer: contact email + copyright. (WhatsApp ab header me hai.)"""
    email = config.GMAIL_USER or ""
    st.markdown(
        "<div class='sk-footer'>"
        f"<div class='sk-footer-contact'>📧 {email}</div>"
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
