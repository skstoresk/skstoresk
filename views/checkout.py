"""SK Store — Checkout (Cash on Delivery only, Pakistan delivery only)."""
import re

import streamlit as st

from lib import db, emailer
from lib.utils import format_price, sale_price

COUNTRIES = [
    "Pakistan", "United Arab Emirates", "Saudi Arabia", "United Kingdom",
    "United States", "Canada", "Australia", "Qatar", "Kuwait", "Oman",
    "Bahrain", "Malaysia", "Turkey", "China", "India", "Bangladesh",
    "Afghanistan", "Iran", "Germany", "France", "Italy", "Spain",
    "Netherlands", "Other",
]

st.title("💳 Checkout")
st.info("💵 Payment method: **Cash on Delivery** — ghar par product milne par payment.")

cart = st.session_state.get("cart", {})
if not cart:
    st.warning("Cart khaali hai.")
    if st.button("⬅ Back to Home"):
        st.switch_page("views/home.py")
    st.stop()

# ---- order summary ----
delivery_fee = float(db.get_setting("delivery_fee", "200") or 200)
free_over = float(db.get_setting("free_delivery_over", "5000") or 5000)
items, subtotal = [], 0.0
for pid, qty in cart.items():
    p = db.get_product(pid)
    if not p or not p.get("is_active"):
        continue
    price = sale_price(p)
    subtotal += price * qty
    items.append({
        "product_id": pid, "name": p["name"], "price": price, "qty": qty,
        "image": (p.get("images") or [None])[0],
    })
if not items:
    st.error("Cart ke products ab available nahi hain.")
    st.stop()
fee = 0.0 if subtotal >= free_over else delivery_fee
total = subtotal + fee

with st.expander("🧾 Order Summary", expanded=True):
    for it in items:
        st.markdown(f"- {it['name']} × {it['qty']} — **{format_price(it['price']*it['qty'])}**")
    st.markdown(f"Delivery: **{format_price(fee)}**")
    st.markdown(f"### Total (COD): {format_price(total)}")

# ---- customer form ----
st.subheader("📋 Delivery Details")
with st.form("checkout_form"):
    name = st.text_input("Full Name *")
    email = st.text_input("Email (order confirmation ke liye)")
    phone = st.text_input("Phone Number *", placeholder="03XXXXXXXXX")
    address = st.text_area("Complete Address *", placeholder="House, street, area…")
    c1, c2 = st.columns(2)
    city = c1.text_input("City *")
    country = c2.selectbox("Country *", COUNTRIES, index=0)
    submitted = st.form_submit_button("🛍️ Place Order (Cash on Delivery)", type="primary")

if submitted:
    errors = []
    if not name.strip():
        errors.append("Naam likhna zaroori hai.")
    if len(re.sub(r"\D", "", phone)) < 10:
        errors.append("Sahi phone number likhein (kam az kam 10 digits).")
    if not address.strip():
        errors.append("Address likhna zaroori hai.")
    if not city.strip():
        errors.append("City likhna zaroori hai.")
    if country != "Pakistan":
        # professional out-of-Pakistan message
        st.error(
            "🌍 **Sorry! We currently deliver within Pakistan only.**\n\n"
            "International shipping is not available at the moment — "
            "we're working on it and will announce it soon. Thank you for understanding! ❤️"
        )
        st.stop()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append("Email ka format sahi nahi hai.")
    # stock check
    for it in items:
        p = db.get_product(it["product_id"])
        if int(p.get("stock") or 0) < it["qty"]:
            errors.append(f"'{it['name']}' ka itna stock nahi hai (available: {p.get('stock')}).")
    if errors:
        for e in errors:
            st.error(e)
        st.stop()

    order_data = {
        "customer_name": name.strip(),
        "customer_email": email.strip() or None,
        "phone": phone.strip(),
        "address": address.strip(),
        "city": city.strip(),
        "country": country,
        "items": items,
        "subtotal": subtotal,
        "delivery_fee": fee,
        "total": total,
        "status": "Pending",
    }
    try:
        resp = db.create_order(order_data)
        order = resp.data[0]
    except Exception as e:  # noqa: BLE001
        st.error(f"Order save nahi ho saka. Dobara try karein. ({e})")
        st.stop()

    # decrement stock
    for it in items:
        p = db.get_product(it["product_id"])
        try:
            db.update_product(it["product_id"], {"stock": max(0, int(p.get("stock") or 0) - it["qty"])})
        except Exception:
            pass

    # emails (best effort — order is already saved)
    cust_ok, cust_msg = emailer.send_customer_confirmation(order)
    adm_ok, adm_msg = emailer.send_admin_alert(order)

    st.session_state.cart = {}
    st.session_state.last_order = order["order_number"]

    st.success("🎉 **Order placed successfully!**")
    st.markdown(f"### Order Number: `{order['order_number']}`")
    st.info(
        "📞 Hamari team jald aap se rabta karke order confirm karegi. "
        "Payment **Cash on Delivery** hogi."
    )
    if cust_ok:
        st.success(f"📧 Confirmation email bhej di gayi: {email}")
    elif email:
        st.warning(f"Email nahi bheji ja saki ({cust_msg}) — order mehfooz hai.")
    if not adm_ok:
        st.caption(f"(admin alert: {adm_msg})")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚚 Track My Order", use_container_width=True):
            st.query_params["o"] = order["order_number"]
            st.switch_page("views/track.py")
    with col2:
        if st.button("🛍️ Continue Shopping", use_container_width=True):
            st.switch_page("views/home.py")
