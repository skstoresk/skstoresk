"""SK Store — Product detail: gallery, video, price, add to cart."""
import streamlit as st

from lib import db
from lib.utils import format_price, is_new, sale_price, youtube_id

pid = st.query_params.get("p")
if not pid:
    st.error("Product nahi mila.")
    if st.button("⬅ Back to Home"):
        st.switch_page("views/home.py")
    st.stop()

p = db.get_product(pid)
if not p or not p.get("is_active"):
    st.error("Ye product ab available nahi hai.")
    if st.button("⬅ Back to Home"):
        st.switch_page("views/home.py")
    st.stop()

if st.button("⬅ Back"):
    st.switch_page("views/home.py")

st.title(p["name"])
cat_name = (p.get("categories") or {}).get("name")
if cat_name:
    st.caption(f"📁 {cat_name}")

new_days = int(db.get_setting("new_badge_days", "7") or 7)
disc = float(p.get("discount_percent") or 0)
badges = ""
if is_new(p.get("created_at"), new_days):
    badges += "<span class='sk-badge sk-badge-new'>NEW</span> "
if disc > 0:
    badges += f"<span class='sk-badge sk-badge-disc'>-{disc:g}% OFF</span>"
if badges:
    st.markdown(badges, unsafe_allow_html=True)

left, right = st.columns([3, 2])

with left:
    imgs = p.get("images") or []
    sel_key = f"img_sel_{pid}"
    sel = st.session_state.get(sel_key, 0)
    if imgs:
        sel = min(sel, len(imgs) - 1)
        st.image(imgs[sel], use_container_width=True)
        if len(imgs) > 1:
            thumbs = st.columns(min(len(imgs), 6))
            for i, url in enumerate(imgs[:6]):
                with thumbs[i]:
                    if st.button(f"#{i+1}", key=f"thumb_{pid}_{i}"):
                        st.session_state[sel_key] = i
                        st.rerun()
                    st.image(url, use_container_width=True)

    # video (uploaded file OR youtube link)
    if p.get("video_url"):
        st.subheader("🎬 Product Video")
        st.video(p["video_url"])
    elif p.get("youtube_url") and youtube_id(p["youtube_url"]):
        st.subheader("🎬 Product Video")
        st.video(p["youtube_url"])

with right:
    if disc > 0:
        st.markdown(
            f"<span class='sk-price-big'>{format_price(sale_price(p['price'], disc))}</span> "
            f"<span class='sk-price-old'>{format_price(p['price'])}</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<span class='sk-price-big'>{format_price(p['price'])}</span>", unsafe_allow_html=True)

    stock = int(p.get("stock") or 0)
    if stock <= 0:
        st.error("Out of Stock")
    elif stock <= 5:
        st.warning(f"⚡ Sirf {stock} reh gaye hain!")
    else:
        st.success("✅ In Stock")

    qty = st.number_input("Quantity", min_value=1, max_value=max(stock, 1), value=1, step=1)

    if st.button("🛒 Add to Cart", use_container_width=True, disabled=stock <= 0, type="primary"):
        cart = st.session_state.get("cart", {})
        cart[pid] = cart.get(pid, 0) + int(qty)
        st.session_state.cart = cart
        st.toast("✅ Added to cart — Only Cash on Delivery service available hai filhal", icon="💵")

    st.info("💵 **Cash on Delivery** — payment ghar par product milne par.")

    if p.get("description"):
        st.subheader("📝 Description")
        st.write(p["description"])
