"""SK Store — Customer order tracking by order number."""
import streamlit as st

from lib import db, ui
from lib.utils import format_price

ui.public_header(active="track")
st.title("🚚 Track Your Order")

default_o = st.query_params.get("o", "")
order_number = st.text_input("Order Number", value=default_o, placeholder="e.g. SK-AB12CD")

STEPS = ["Pending", "Confirmed", "Shipped", "Delivered"]

if st.button("🔍 Track", type="primary") or default_o:
    if not order_number.strip():
        st.warning("Apna order number likhein.")
        ui.stop_with_footer()
    order = db.get_order_by_number(order_number)
    if not order:
        st.error("❌ Is number ka koi order nahi mila. Number dobara check karein.")
        ui.stop_with_footer()

    st.subheader(f"Order `{order['order_number']}`")
    status = order["status"]

    if status == "Cancelled":
        st.error("❌ Ye order cancel kar diya gaya hai.")
    else:
        # timeline
        cols = st.columns(len(STEPS))
        cur = STEPS.index(status) if status in STEPS else 0
        for i, step in enumerate(STEPS):
            with cols[i]:
                if i < cur:
                    st.markdown(f"✅ **{step}**")
                elif i == cur:
                    st.markdown(f"🟢 **{step}** ⬅")
                else:
                    st.markdown(f"⚪ {step}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Status**")
        st.markdown(f"### {status}")
    with c2:
        st.markdown("**Tracking ID**")
        if order.get("tracking_id"):
            st.markdown(f"### `{order['tracking_id']}`")
            st.caption("Courier ki website par ye ID daal kar live location dekhein.")
        else:
            st.caption("Abhi assign nahi hui — jald update hogi.")

    with st.expander("🧾 Order details"):
        for it in order.get("items", []) or []:
            st.markdown(f"- {it.get('name')} × {it.get('qty')} — {format_price(it.get('price',0)*it.get('qty',1))}")
        st.markdown(f"**Total (COD): {format_price(order.get('total',0))}**")
        st.caption(f"📍 {order['address']}, {order['city']}")

ui.public_footer()
