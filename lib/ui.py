"""Shared page chrome: public header/footer, admin header/footer."""
import base64
import html
import os
from urllib.parse import quote_plus

import streamlit as st

from . import config, db


_LOGO_URI = None


def _logo_data_uri():
    """SK logo (assets/sk-logo.png) as base64 data URI; '' if missing."""
    global _LOGO_URI
    if _LOGO_URI is None:
        try:
            _p = os.path.normpath(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "..", "assets", "sk-logo.png"))
            with open(_p, "rb") as _f:
                _LOGO_URI = "data:image/png;base64," + base64.b64encode(_f.read()).decode("ascii")
        except Exception:
            _LOGO_URI = ""
    return _LOGO_URI


def _brand_mark(hero=True):
    """Animated logo img, ya fallback emoji (logo file na ho to)."""
    _logo = _logo_data_uri()
    if _logo:
        _cls = "sk-hero-logo" if hero else "sk-admin-logo"
        return f"<img class='{_cls}' src='{_logo}' alt='SK Store logo' />"
    return "<span class='sk-hero-emoji'>🛍️</span>"


def product_slideshow_html(images, uid, height=200, interval=3000):
    """Auto-cycling product image slideshow (custom HTML).
    Streamlit ka image widget istemal nahi hota — is liye koi fullscreen
    button ya extra chrome nahi ata."""
    imgs = (images or [])[:6]
    if not imgs:
        return ""
    slides = "\n".join(
        f'<img src="{html.escape(u, quote=True)}" '
        f'class="skcs-img{" skcs-on" if i == 0 else ""}" alt="">'
        for i, u in enumerate(imgs)
    )
    return f"""
<div class="skcs" id="skcs-{uid}" style="height:{int(height)}px">{slides}</div>
<style>
.skcs {{ position: relative; width: 100%; overflow: hidden;
         border-radius: 10px; background: #fff; }}
.skcs-img {{ position: absolute; inset: 0; width: 100%; height: 100%;
             object-fit: contain; opacity: 0; transition: opacity 0.8s ease; }}
.skcs-img.skcs-on {{ opacity: 1; }}
</style>
<script>
(function(){{
  var box = document.getElementById('skcs-{uid}');
  if (!box) return;
  var imgs = box.querySelectorAll('.skcs-img');
  if (imgs.length < 2) return;
  var i = 0;
  setInterval(function(){{
    imgs[i].classList.remove('skcs-on');
    i = (i + 1) % imgs.length;
    imgs[i].classList.add('skcs-on');
  }}, {int(interval)});
}})();
</script>
"""


def _banner_kicker(btype):
    return {"new": "🆕 NEW ARRIVAL", "discount": "🔥 DISCOUNT"}.get(btype, "📢 ANNOUNCEMENT")


def banner_ad_html(b):
    """Single cinematic ad-style banner card (pure HTML/CSS, page CSS se style hota hai).

    Shop Now target: product_id (in-app product page) > link_url (external) > decorative.
    """
    img = (b.get("image_url") or "").strip()
    if img:
        bg = f"<img class='sk-ad-bg' src='{html.escape(img, quote=True)}' alt='' loading='lazy' />"
    else:
        bg = "<div class='sk-ad-bg sk-ad-bg-fallback'></div>"
    pid = (b.get("product_id") or "").strip() if isinstance(b.get("product_id"), str) else b.get("product_id")
    link = (b.get("link_url") or "").strip()
    if pid:
        _pq = html.escape(str(pid), quote=True)
        cta = (f"<a class='sk-ad-cta sk-ad-prod' data-pid='{_pq}' "
               f"href='product?p={_pq}'>Shop Now &rarr;</a>")
    elif link:
        cta = (f"<a class='sk-ad-cta' href='{html.escape(link, quote=True)}' "
               f"target='_blank' rel='noopener'>Shop Now &rarr;</a>")
    else:
        cta = "<span class='sk-ad-cta sk-ad-cta-soon'>Shop Now &rarr;</span>"
    sub = f"<div class='sk-ad-sub'>{html.escape(b.get('subtitle') or '')}</div>" if b.get("subtitle") else ""
    return (
        "<div class='sk-ad'>"
        f"{bg}<div class='sk-ad-overlay'></div><div class='sk-ad-shine'></div>"
        "<div class='sk-ad-content'>"
        f"<div class='sk-ad-kicker'>{_banner_kicker(b.get('banner_type'))}</div>"
        f"<div class='sk-ad-title'>{html.escape(b.get('title') or '')}</div>"
        f"{sub}{cta}"
        "</div></div>"
    )


_AD_CSS = """
.sk-ad{position:relative;border-radius:18px;overflow:hidden;margin:12px 0 20px;
min-height:300px;display:flex;align-items:center;background:#0a0f22;
border:1px solid rgba(201,150,46,.35)}
.sk-ad-bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
animation:sk-kenburns 14s ease-in-out infinite alternate}
.sk-ad-bg-fallback{background:radial-gradient(120% 130% at 20% 10%,#2b2150 0%,#0a0f22 60%,#05070f 100%);animation:none}
@keyframes sk-kenburns{from{transform:scale(1)}to{transform:scale(1.14)}}
.sk-ad-overlay{position:absolute;inset:0;background:linear-gradient(92deg,rgba(4,7,18,.92) 18%,rgba(4,7,18,.55) 52%,rgba(4,7,18,.08) 100%)}
.sk-ad-shine{position:absolute;inset:0;overflow:hidden;pointer-events:none}
.sk-ad-shine::after{content:"";position:absolute;top:-20%;bottom:-20%;width:90px;
background:linear-gradient(100deg,transparent,rgba(255,255,255,.22),transparent);
transform:skewX(-18deg);animation:sk-ad-sweep 4.5s ease-in-out infinite}
@keyframes sk-ad-sweep{0%{left:-140px}55%,100%{left:130%}}
.sk-ad-content{position:relative;z-index:2;padding:38px 42px;max-width:62%;animation:sk-fadeup .7s ease both}
@keyframes sk-fadeup{from{opacity:0;transform:translateY(26px)}to{opacity:1;transform:none}}
.sk-ad-kicker{display:inline-block;font-size:12px;font-weight:800;letter-spacing:2.5px;color:#0a0f22;
background:linear-gradient(110deg,#f6d365,#fff3c4);padding:6px 14px;border-radius:20px}
.sk-ad-title{font-size:34px;font-weight:900;color:#fff;margin:12px 0 6px;line-height:1.15;text-shadow:0 2px 14px rgba(0,0,0,.5)}
.sk-ad-sub{color:#e9e2d2;font-size:16px;margin-bottom:18px}
.sk-ad-cta{display:inline-block;font-weight:800;font-size:15px;color:#0a0f22 !important;
background:linear-gradient(110deg,#e8c15a,#f6d365);padding:12px 28px;border-radius:30px;
text-decoration:none;box-shadow:0 4px 18px rgba(232,193,90,.45)}
.sk-ad-slide{display:none}.sk-ad-slide.active{display:block}
.sk-ad-slide .sk-ad{margin:12px 0 8px}
.sk-ad-dots{text-align:center;padding:6px 0 4px}
.sk-ad-dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.25);margin:0 5px;cursor:pointer}
.sk-ad-dot.active{background:#f6d365;width:28px;border-radius:6px}
@media(max-width:640px){.sk-ad{min-height:220px}.sk-ad-content{padding:24px;max-width:88%}.sk-ad-title{font-size:24px}}
"""


def banner_carousel_html(banners, uid="top"):
    """Auto-rotating cinematic ad carousel (iframe ke liye self-contained HTML+JS)."""
    slides = "\n".join(
        f"<div class='sk-ad-slide{' active' if i == 0 else ''}'>{banner_ad_html(b)}</div>"
        for i, b in enumerate(banners)
    )
    dots = "\n".join(
        f"<span class='sk-ad-dot{' active' if i == 0 else ''}' data-i='{i}'></span>"
        for i in range(len(banners))
    )
    return f"""
<div class='sk-ad-rot' id='skad-{uid}'>
<style>{_AD_CSS}</style>
{slides}
<div class='sk-ad-dots'>{dots}</div>
</div>
<script>
(function(){{
  var rot = document.getElementById('skad-{uid}');
  if (!rot) return;
  var slides = rot.querySelectorAll('.sk-ad-slide');
  var dots = rot.querySelectorAll('.sk-ad-dot');
  if (slides.length < 2) return;
  var i = 0, timer = null;
  function go(n){{
    slides[i].classList.remove('active'); dots[i].classList.remove('active');
    i = (n + slides.length) % slides.length;
    slides[i].classList.add('active'); dots[i].classList.add('active');
  }}
  function auto(){{ timer = setInterval(function(){{ go(i + 1); }}, 5000); }}
  dots.forEach(function(d){{
    d.addEventListener('click', function(){{
      clearInterval(timer); go(parseInt(d.getAttribute('data-i'), 10)); auto();
    }});
  }});
  // product-linked Shop Now: iframe ke andar relative URL toot jata hai,
  // is liye top window ko product page par bhejo (same-origin).
  rot.querySelectorAll('.sk-ad-prod').forEach(function(a){{
    a.addEventListener('click', function(e){{
      e.preventDefault();
      var url = '/product?p=' + encodeURIComponent(a.getAttribute('data-pid'));
      try {{ window.top.location.href = window.top.location.origin + url; }}
      catch(err) {{ window.open(url, '_top'); }}
    }});
  }});
  auto();
}})();
</script>
"""


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
        f"<div class='sk-hero-name'>{_brand_mark(hero=True)} "
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
    wa = _wa_url()
    if wa:
        # floating button: bottom-right, scroll ke saath fixed
        st.markdown(
            f"<a class='sk-wa-fixed' target='_blank' href='{wa}' "
            f"title='WhatsApp par rabta karein'>{_WA_SVG}</a>",
            unsafe_allow_html=True,
        )
    st.divider()


def admin_header():
    """Admin portal header: logo + ADMIN tag + Refresh + Logout. No public nav."""
    a1, a2, a3 = st.columns([5.4, 1.7, 1.7])
    with a1:
        st.markdown(
            f"<div class='sk-logo'>{_brand_mark(hero=False)} {config.STORE_NAME} <span class='sk-admin-tag'>ADMIN</span></div>",
            unsafe_allow_html=True,
        )
    with a2:
        if st.button("🔄 Refresh", use_container_width=True, key="admin_refresh"):
            st.rerun()
    with a3:
        if st.button("🚪 Logout", use_container_width=True, key="admin_logout"):
            st.session_state.admin_authed = False
            try:
                del st.query_params["key"]
            except Exception:
                pass
            st.switch_page("views/home.py")
    st.divider()


def public_footer():
    """Public footer: contact email + copyright. (WhatsApp floating button hai.)"""
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
