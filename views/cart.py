"""SK Store — Shopping cart."""
import streamlit as st

from lib import db
from lib.utils import format_price, sale_price

st.title("🛒 Your Cart")
st.info("💵 **Note:** Only Cash on Delivery service available hai filhal.")

cart = st.session_state.get("cart", {})
if not cart:
    st.warning("Cart khaali hai. Kuch pasand karo! 🛍️")
    if st.button("⬅ Continue Shopping"):
        st.switch_page("views/home.py")
    st.stop()

delivery_fee = float(db.get_setting("delivery_fee", "200") or 200)
free_over = float(db.get_setting("free_delivery_over", "5000") or 5000)

subtotal = 0.0
valid_ids = []
for pid, qty in list(cart.items()):
    p = db.get_product(pid)
    if not p or not p.get("is_active"):
        del cart[pid]
        continue
    valid_ids.append(pid)
    price = sale_price(p["price"], p.get("discount_percent"))
    line = price * qty
    subtotal += line
    c1, c2, c3 = st.columns([1, 3, 2])
    with c1:
        imgs = p.get("images") or []
        if imgs:
            st.image(imgs[0], use_container_width=True)
    with c2:
        st.markdown(f"**{p['name']}**")
        st.caption(f"{format_price(price)} each")
        q1, q2, q3 = st.columns([1, 1, 1])
        with q1:
            if st.button("➖", key=f"dec_{pid}"):
                cart[pid] = max(1, qty - 1)
                st.rerun()
        with q2:
            st.markdown(f"<div style='text-align:center;font-size:20px'>{qty}</div>", unsafe_allow_html=True)
        with q3:
            if st.button("➕", key=f"inc_{pid}"):
                cart[pid] = qty + 1
                st.rerun()
        if st.button("🗑 Remove", key=f"rm_{pid}"):
            del cart[pid]
            st.session_state.cart = cart
            st.rerun()
    with c3:
        st.markdown(f"**{format_price(line)}**")
    st.divider()

st.session_state.cart = cart

fee = 0.0 if subtotal >= free_over else delivery_fee
st.markdown(f"Subtotal: **{format_price(subtotal)}**")
if fee == 0:
    st.markdown("Delivery: **FREE** 🎉")
else:
    st.markdown(f"Delivery: **{format_price(fee)}** (FREE on orders over {format_price(free_over)})")
st.markdown(f"### Total: {format_price(subtotal + fee)}")

col1, col2 = st.columns(2)
with col1:
    if st.button("⬅ Continue Shopping", use_container_width=True):
        st.switch_page("views/home.py")
with col2:
    if st.button("✅ Proceed to Checkout", use_container_width=True, type="primary"):
        st.switch_page("views/checkout.py")
