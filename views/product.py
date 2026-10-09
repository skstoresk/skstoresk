"""SK Store — Product detail: gallery, video, price, add to cart."""
import html
import json

import streamlit as st
import streamlit.components.v1 as components

from lib import config, db, ui
from lib.utils import format_price, is_new, sale_price, youtube_id

ui.public_header()


def _gallery_html(images):
    """Professional image gallery: arrows + clickable thumbnails + hover zoom.
    Self-contained JS — no Streamlit rerun needed for image switching."""
    thumbs = "\n".join(
        f'<img src="{html.escape(u, quote=True)}" class="skg-thumb'
        f'{" skg-active" if i == 0 else ""}" data-i="{i}" alt="thumbnail {i + 1}">'
        for i, u in enumerate(images)
    )
    return f"""
<div class="skg">
  <div class="skg-main" id="skg-main">
    <img id="skg-img" src="{html.escape(images[0], quote=True)}" alt="product image">
    <button class="skg-arrow skg-left" id="skg-prev" aria-label="previous image">&#10094;</button>
    <button class="skg-arrow skg-right" id="skg-next" aria-label="next image">&#10095;</button>
    <div class="skg-count" id="skg-count">1 / {len(images)}</div>
  </div>
  <div class="skg-thumbs">{thumbs}</div>
</div>
<style>
.skg-main {{
  position: relative; width: 100%; height: 440px; background: #fff;
  border: 1px solid #eee; border-radius: 12px; overflow: hidden;
  display: flex; align-items: center; justify-content: center; cursor: zoom-in;
}}
.skg-main img {{
  width: 100%; height: 100%; object-fit: contain;
  transition: transform 0.25s ease;
}}
.skg-arrow {{
  position: absolute; top: 50%; transform: translateY(-50%);
  width: 44px; height: 44px; border-radius: 50%; border: none;
  background: rgba(255,255,255,0.94); box-shadow: 0 2px 8px rgba(0,0,0,0.20);
  font-size: 18px; cursor: pointer; z-index: 3; color: #333; line-height: 1;
}}
.skg-left {{ left: 12px; }} .skg-right {{ right: 12px; }}
.skg-arrow:hover {{ background: #C9A227; color: #fff; }}
.skg-count {{
  position: absolute; bottom: 10px; right: 12px; z-index: 3;
  background: rgba(0,0,0,0.55); color: #fff; font-size: 12px;
  padding: 3px 10px; border-radius: 20px;
}}
.skg-thumbs {{
  display: flex; gap: 10px; margin-top: 12px;
  overflow-x: auto; padding-bottom: 4px;
}}
.skg-thumb {{
  width: 74px; height: 74px; object-fit: cover; border-radius: 10px;
  border: 2px solid #eee; cursor: pointer; flex-shrink: 0; background: #fff;
}}
.skg-thumb:hover {{ border-color: #C9A227; }}
.skg-thumb.skg-active {{ border-color: #C9A227; }}
</style>
<script>
(function(){{
  const imgs = {json.dumps(images)};
  const n = imgs.length;
  let idx = 0;
  const mainImg = document.getElementById('skg-img');
  const mainWrap = document.getElementById('skg-main');
  const count = document.getElementById('skg-count');
  const thumbs = Array.from(document.querySelectorAll('.skg-thumb'));
  let autoTimer = null;
  function startAuto(){{ stopAuto(); autoTimer = setInterval(() => show(idx + 1), 4000); }}
  function stopAuto(){{ if (autoTimer) {{ clearInterval(autoTimer); autoTimer = null; }} }}
  function show(i){{
    idx = (i + n) % n;
    mainImg.style.transform = 'scale(1)';
    mainImg.src = imgs[idx];
    count.textContent = (idx + 1) + ' / ' + n;
    thumbs.forEach((t, k) => t.classList.toggle('skg-active', k === idx));
    startAuto();
  }}
  document.getElementById('skg-prev').addEventListener('click', e => {{ e.stopPropagation(); show(idx - 1); }});
  document.getElementById('skg-next').addEventListener('click', e => {{ e.stopPropagation(); show(idx + 1); }});
  thumbs.forEach(t => t.addEventListener('click', () => show(parseInt(t.dataset.i, 10))));
  imgs.forEach(u => {{ const im = new Image(); im.src = u; }});
  mainWrap.addEventListener('mousemove', e => {{
    const r = mainWrap.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * 100;
    const y = ((e.clientY - r.top) / r.height) * 100;
    mainImg.style.transformOrigin = x + '% ' + y + '%';
    mainImg.style.transform = 'scale(1.9)';
  }});
  mainWrap.addEventListener('mouseenter', stopAuto);
  mainWrap.addEventListener('mouseleave', () => {{ mainImg.style.transform = 'scale(1)'; startAuto(); }});
  show(0);
}})();
</script>
"""

pid = st.query_params.get("p") or st.session_state.get("view_pid")
if not pid:
    st.error("Product nahi mila.")
    if st.button("⬅ Back to Home"):
        st.switch_page("views/home.py")
    ui.stop_with_footer()

p = db.get_product(pid)
if not p or not p.get("is_active"):
    st.error("Ye product ab available nahi hai.")
    if st.button("⬅ Back to Home"):
        st.switch_page("views/home.py")
    ui.stop_with_footer()

if st.button("⬅ Back"):
    st.switch_page("views/home.py")

st.title(p["name"])
cat_name = (p.get("categories") or {}).get("name")
if cat_name:
    st.caption(f"📁 {cat_name}")

new_days = int(db.get_setting("new_badge_days", "7") or 7)
sp = sale_price(p)
list_price = float(p.get("price") or 0)
badges = ""
if is_new(p.get("created_at"), new_days):
    badges += "<span class='sk-badge sk-badge-new'>NEW</span> "
if sp < list_price and list_price > 0:
    pct = round((1 - sp / list_price) * 100)
    badges += f"<span class='sk-badge sk-badge-disc'>-{pct:g}% OFF</span>"
if badges:
    st.markdown(badges, unsafe_allow_html=True)

# ad link copy (Facebook ad chalane ke liye product ka link)
_ad_url = f"{(config.APP_URL or '').rstrip('/')}/product?p={pid}"
components.html(
    f"""<button id="sk-copylink" style="background:#1877F2;color:#fff;border:none;border-radius:20px;
padding:8px 18px;font-weight:700;font-size:14px;cursor:pointer;">
📋 Ad Link Copy Karo</button>
<script>
document.getElementById('sk-copylink').addEventListener('click', function(){{
  var ta = document.createElement('textarea');
  ta.value = "{_ad_url}";
  document.body.appendChild(ta); ta.select();
  try {{ document.execCommand('copy'); }} catch(e) {{}}
  document.body.removeChild(ta);
  var b = document.getElementById('sk-copylink');
  b.textContent = '✅ Link Copied!';
  setTimeout(function(){{ b.textContent = '📋 Ad Link Copy Karo'; }}, 2000);
}});
</script>""",
    height=50,
)

left, right = st.columns([3, 2])

with left:
    imgs = p.get("images") or []
    if imgs:
        components.html(_gallery_html(imgs[:6]), height=600, scrolling=False)

    # video (uploaded file OR youtube link)
    if p.get("video_url"):
        st.subheader("🎬 Product Video")
        st.video(p["video_url"])
    elif p.get("youtube_url") and youtube_id(p["youtube_url"]):
        st.subheader("🎬 Product Video")
        st.video(p["youtube_url"])

with right:
    if sp < list_price:
        st.markdown(
            f"<span class='sk-price-big'>{format_price(sp)}</span> "
            f"<span class='sk-price-old'>{format_price(list_price)}</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<span class='sk-price-big'>{format_price(list_price)}</span>", unsafe_allow_html=True)

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

    # product-page promo banners (Add to Cart ke paas)
    try:
        _pbanners = db.get_banners(placement="product", active_only=True)
    except Exception:
        _pbanners = []
    for _b in _pbanners:
        _img = f"<img src='{_b['image_url']}' class='sk-banner-img' />" if _b.get("image_url") else ""
        st.markdown(
            f"<div class='sk-banner sk-banner-{_b['banner_type']}'>{_img}"
            f"<div class='sk-banner-text'><div class='sk-banner-kicker'>"
            f"{'🆕 NEW ARRIVAL' if _b['banner_type']=='new' else ('🔥 DISCOUNT' if _b['banner_type']=='discount' else '📢')}</div>"
            f"<div class='sk-banner-title'>{_b['title']}</div>"
            f"<div class='sk-banner-sub'>{_b.get('subtitle','')}</div></div></div>",
            unsafe_allow_html=True,
        )

    if p.get("description"):
        st.subheader("📝 Description")
        st.write(p["description"])

# ---------------- related products (sirf tab jab related hon) ----------------
_others = [x for x in db.get_products() if x["id"] != pid]
_pcat = p.get("category_id")
_same = [x for x in _others if _pcat and x.get("category_id") == _pcat]
_rest = [x for x in _others if x not in _same]
related = (_same + _rest)[:4]
if related:
    st.divider()
    st.subheader("🔗 Is se milte-julte products")
    _cols = st.columns(len(related))
    for _col, rp in zip(_cols, related):
        with _col:
            with st.container(border=True):
                _rimg = (rp.get("images") or [""])[0]
                if _rimg:
                    st.image(_rimg, use_container_width=True)
                st.markdown(f"<span class='sk-card-name'>{html.escape(rp['name'])}</span>",
                            unsafe_allow_html=True)
                _rsp = sale_price(rp)
                _rlp = float(rp.get("price") or 0)
                if _rsp < _rlp:
                    st.markdown(
                        f"<span class='sk-price'>{format_price(_rsp)}</span> "
                        f"<span class='sk-price-old'>{format_price(_rlp)}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(f"<span class='sk-price'>{format_price(_rlp)}</span>",
                                unsafe_allow_html=True)
                if st.button("View 👀", key=f"rel_{rp['id']}", use_container_width=True):
                    st.session_state["view_pid"] = rp["id"]
                    st.query_params["p"] = rp["id"]
                    st.rerun()

ui.public_footer()
