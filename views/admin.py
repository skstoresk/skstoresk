"""SK STORE — Admin portal (/admin). Login required."""
import hashlib
import hmac

import streamlit as st

from lib import config, db, emailer, storage, ui

try:
    from lib import share
except ImportError:  # lib/share.py upload karna bhool jaye to admin crash na ho
    share = None
try:
    from lib import diagnostics
except ImportError:
    diagnostics = None
from lib.themes import DEFAULT_THEME, theme_keys, theme_label
from lib.utils import format_price, profit_per_unit, sale_price


def _admin_token():
    """Browser refresh ke baad bhi login qaim rakhne wala token (URL me)."""
    return hmac.new(b"skstore-admin", config.ADMIN_PASS.encode(),
                    hashlib.sha256).hexdigest()[:32]


# ---------------- login ----------------
if not config.ADMIN_PASS:
    st.error("ADMIN_PASS secrets me set nahi hai. Pehle Streamlit Secrets configure karein.")
    st.stop()

# refresh ke baad: URL me sahi token ho to dobara login nahi mangna
if st.query_params.get("key") == _admin_token():
    st.session_state.admin_authed = True

if not st.session_state.get("admin_authed"):
    with st.form("admin_login"):
        st.subheader("Login")
        u = st.text_input("User ID")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary"):
            if hmac.compare_digest(u, config.ADMIN_USER) and hmac.compare_digest(p, config.ADMIN_PASS):
                st.session_state.admin_authed = True
                st.query_params["key"] = _admin_token()
                st.rerun()
            else:
                st.error("❌ Ghalat User ID ya Password.")
    st.stop()

ui.admin_header()

tabs = st.tabs(["📊 Dashboard", "📦 Products", "🧾 Orders", "🖼️ Banners", "⚙️ Settings",
                "🔧 System Check"])

# ================= DASHBOARD =================
with tabs[0]:
    st.subheader("Dashboard")
    products = db.get_products(active_only=False)
    orders = db.get_orders()
    pending = [o for o in orders if o["status"] == "Pending"]
    revenue = sum(float(o.get("total") or 0) for o in orders if o["status"] != "Cancelled")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Products", len(products))
    m2.metric("Total Orders", len(orders))
    m3.metric("Pending Orders", len(pending))
    m4.metric("Revenue (non-cancelled)", format_price(revenue))
    if pending:
        st.warning(f"⚠️ {len(pending)} orders pending hain — Orders tab me confirm karein.")

# ================= PRODUCTS =================
with tabs[1]:
    st.subheader("Products")
    _lsu = st.session_state.pop("last_share_url", None)
    if _lsu:
        _lmsg = st.session_state.pop("last_share_msg", "")
        if st.session_state.pop("last_share_ok", True):
            st.success("🔗 Share link ban raha hai — ~2 minute me live ho jayega:")
        else:
            st.warning(f"Share page auto-build trigger nahi ho saka — wajah: {_lmsg}")
        st.code(_lsu)
        st.caption("↑ Ye link copy karke Facebook mein paste karo — photo + price ka preview khud ban jayega.")
    cats = db.get_categories()
    cat_names = ["(No category)", "➕ Nayi category..."] + [c["name"] for c in cats]
    cat_id_of = {c["name"]: c["id"] for c in cats}

    editing = st.session_state.get("editing_product")
    if editing:
        st.info(f"✏️ Editing: **{editing['name']}**")
        if st.button("❌ Cancel edit"):
            st.session_state.editing_product = None
            st.rerun()

    ex = editing or {}
    ex_images = list(ex.get("images") or [])
    _eid = editing["id"] if editing else "new"

    # ---- Category + Video selectors FORM KE BAHAR ----
    # (form ke andar option badalne par page refresh nahi hota, is liye
    # conditional field kabhi khulta hi nahi tha)
    _cur_cat = next((c["name"] for c in cats if c["id"] == ex.get("category_id")),
                    "(No category)")
    _cat_choice = st.selectbox(
        "Category", cat_names,
        index=cat_names.index(_cur_cat) if _cur_cat in cat_names else 0,
        key=f"cat_choice_{_eid}")
    _new_cat_name = ""
    if _cat_choice == "➕ Nayi category...":
        _new_cat_name = st.text_input("Nayi category ka naam *",
                                      placeholder="jaise: Kitchen, Beauty",
                                      key=f"new_cat_name_{_eid}")

    st.markdown("**Product Video (optional)**")
    _vchoice = st.radio(
        "Video source", ["No video", "Upload video", "YouTube link"],
        index=0 if not ex.get("video_url") and not ex.get("youtube_url")
        else (1 if ex.get("video_url") else 2),
        key=f"vchoice_{_eid}", horizontal=True)
    _video_file, _youtube_link = None, ""
    if _vchoice == "Upload video":
        _video_file = st.file_uploader("Video file (mp4/webm/mov)",
                                       type=["mp4", "webm", "mov"],
                                       key=f"video_file_{_eid}")
        if ex.get("video_url"):
            st.caption("Pehle se ek video lagi hai — nayi upload karne par replace ho jayegi.")
    elif _vchoice == "YouTube link":
        _youtube_link = st.text_input("YouTube link paste karein",
                                      value=ex.get("youtube_url") or "",
                                      key=f"youtube_link_{_eid}")

    with st.form("product_form", clear_on_submit=editing is None):
        name = st.text_input("Product Name *", value=ex.get("name", ""))
        description = st.text_area("Description", value=ex.get("description", ""))
        c1, c2 = st.columns(2)
        price = c1.number_input("Price (Rs) * — asal qeemat", min_value=0.0,
                                value=float(ex.get("price") or 0))
        discount_price = c2.number_input("Discount price (Rs) — sale wali qeemat (0 = no discount)",
                                         min_value=0.0,
                                         value=float(ex.get("discount_price") or 0))
        c4, c5, c6, c7 = st.columns(4)
        buy_price = c4.number_input("Buy price (Rs) * — tumhari khareed", min_value=0.0,
                                    value=float(ex.get("buy_price") or 0))
        delivery_exp = c5.number_input("Delivery exp (Rs)", min_value=0.0,
                                       value=float(ex.get("delivery_expense") or 0))
        packing_exp = c6.number_input("Packing exp (Rs)", min_value=0.0,
                                      value=float(ex.get("packing_expense") or 0))
        stock = c7.number_input("Stock *", min_value=0, value=int(ex.get("stock") or 0))

        _sp = float(discount_price) if float(discount_price) > 0 else float(price)
        _profit = _sp - float(buy_price) - float(delivery_exp) - float(packing_exp)
        if _profit >= 0:
            st.success(f"💰 Profit per unit: **{format_price(_profit)}** "
                       f"(sale {format_price(_sp)} − buy − delivery − packing)")
        else:
            st.error(f"⚠️ Per unit nuqsan: **{format_price(_profit)}** — qeemat check karo!")
        tags = st.text_input("🏷️ Tags * (comma se alag karein)",
                             value=ex.get("tags") or "",
                             placeholder="trimmer, shaver, grooming kit, men gift",
                             help="Kam az kam 3 words, zyada se zyada 500 words. "
                                  "Customer in words se search karke ye product payega.")

        st.markdown("**Images (minimum 2, maximum 6)** *")
        if ex_images:
            st.caption(f"Abhi {len(ex_images)} image(s) hain — hatane ke liye select karein:")
            remove = st.multiselect("Remove images", ex_images, format_func=lambda u: u[-40:])
            kept = [u for u in ex_images if u not in remove]
            for u in kept:
                st.image(u, width=120)
        else:
            kept = []
        new_imgs = st.file_uploader("Nayi images upload karein (jpg/png/webp)",
                                    type=["jpg", "jpeg", "png", "webp"],
                                    accept_multiple_files=True)
        st.caption(f"Total images hongi: {len(kept) + len(new_imgs or [])} (2–6 zaroori)")

        is_active = st.checkbox("Active (site par show ho)", value=ex.get("is_active", True))
        submitted = st.form_submit_button("💾 Save Product", type="primary")

    if submitted:
        errs = []
        if not name.strip():
            errs.append("Product name zaroori hai.")
        if price <= 0:
            errs.append("Price 0 se zyada honi chahiye.")
        if buy_price <= 0:
            errs.append("Buy price 0 se zyada honi chahiye.")
        if float(discount_price) > 0 and float(discount_price) >= float(price):
            errs.append("Discount price asal price se kam honi chahiye.")
        total_imgs = len(kept) + len(new_imgs or [])
        if total_imgs < 2:
            errs.append(f"Minimum 2 images zaroori hain (abhi {total_imgs}).")
        if total_imgs > 6:
            errs.append(f"Maximum 6 images allowed hain (abhi {total_imgs}).")
        if _vchoice == "YouTube link" and _youtube_link and "youtu" not in _youtube_link:
            errs.append("YouTube link sahi nahi lag raha.")
        tag_words = [w for w in tags.replace(",", " ").split() if w]
        if not (3 <= len(tag_words) <= 500):
            errs.append(f"Tags me kam az kam 3 words aur zyada se zyada 500 words hon "
                        f"(abhi {len(tag_words)} words).")
        if _cat_choice == "➕ Nayi category..." and not _new_cat_name.strip():
            errs.append("Nayi category ka naam likhein.")
        if errs:
            for e in errs:
                st.error(e)
            st.stop()

        with st.spinner("Uploading…"):
            if _cat_choice == "➕ Nayi category...":
                _nc = _new_cat_name.strip()
                _new_id = None
                try:
                    _res = db.add_category(_nc)
                    _data = getattr(_res, "data", None)
                    if _data:
                        _new_id = _data[0].get("id")
                except Exception:  # noqa: BLE001
                    _new_id = None
                if not _new_id:
                    _match = [c for c in db.get_categories()
                              if c["name"].strip().lower() == _nc.lower()]
                    _new_id = _match[0]["id"] if _match else None
                if not _new_id:
                    st.error("Category nahi ban saki — dobara try karein.")
                    st.stop()
                category_id = _new_id
            else:
                category_id = cat_id_of.get(_cat_choice)
            urls = list(kept)
            for f in new_imgs or []:
                try:
                    urls.append(storage.upload_image(f))
                except Exception as e:  # noqa: BLE001
                    st.error(f"Image upload failed ({f.name}): {e}")
                    st.stop()
            video_url, yt_url = ex.get("video_url"), ex.get("youtube_url")
            if _vchoice == "Upload video" and _video_file:
                try:
                    video_url = storage.upload_video(_video_file)
                except Exception as e:  # noqa: BLE001
                    st.error(f"Video upload failed: {e}")
                    st.stop()
                yt_url = None
            elif _vchoice == "YouTube link":
                yt_url = _youtube_link.strip() or None
                video_url = None
            elif _vchoice == "No video":
                video_url, yt_url = None, None

            norm_tags = ", ".join(t.strip() for t in tags.split(",") if t.strip())
            # slug: product-name based short link; stable across edits
            _old_slug = ((editing or {}).get("slug") or "").strip()
            if _old_slug:
                _slug = _old_slug
            elif share:
                try:
                    _taken = {str(x.get("slug") or "").strip()
                              for x in db.get_products(active_only=False) if x.get("slug")}
                except Exception:  # noqa: BLE001
                    _taken = set()
                _slug = share.unique_slug(share.slugify(name), _taken)
            else:
                _slug = ""
            data = {
                "name": name.strip(),
                "description": description.strip(),
                "slug": _slug,
                "tags": norm_tags,
                "price": price,
                "discount_price": float(discount_price) if float(discount_price) > 0 else None,
                "buy_price": buy_price,
                "delivery_expense": delivery_exp,
                "packing_expense": packing_exp,
                "category_id": category_id,
                "images": urls,
                "video_url": video_url,
                "youtube_url": yt_url,
                "stock": int(stock),
                "is_active": is_active,
            }
            try:
                if editing:
                    db.update_product(editing["id"], data)
                    _saved = dict(editing)
                    _saved.update(data)
                    _saved["id"] = editing["id"]
                    st.success("✅ Product updated!")
                else:
                    _res = db.create_product(data)
                    _rows = getattr(_res, "data", None) or []
                    _saved = dict(data)
                    _saved["id"] = _rows[0]["id"] if _rows else None
                    st.success("✅ Product added — site par live ho gaya!")
                # ---- auto share page (GitHub Action, ~2 min me live) ----
                if share:
                    _ok, _msg = share.trigger_share_build(
                        "upsert", share.build_product_payload(_saved))
                    _share_url = share.share_url_for(_saved)
                else:
                    _ok, _msg = False, "lib/share.py GitHub par upload nahi hui"
                    _share_url = (f"https://skstoresk.github.io/skstoresk"
                                  f"/share/{_saved['id']}.html")
                st.session_state["last_share_url"] = _share_url
                st.session_state["last_share_ok"] = _ok
                st.session_state["last_share_msg"] = _msg
                if not _ok:
                    st.warning(f"Share auto-build trigger: {_msg}")
            except Exception as e:  # noqa: BLE001
                st.error(f"Save nahi ho saka: {e}")
                st.stop()
        # form ke bahar wale selectors reset (agle product ke liye saaf)
        for _k in list(st.session_state.keys()):
            if _k.startswith(("cat_choice_", "new_cat_name_", "vchoice_",
                              "video_file_", "youtube_link_")):
                st.session_state.pop(_k, None)
        st.session_state.editing_product = None
        st.rerun()

    st.divider()
    st.subheader("All Products")
    for p in db.get_products(active_only=False):
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 2])
            with c1:
                if p.get("images"):
                    st.image(p["images"][0], use_container_width=True)
            with c2:
                st.markdown(f"**{p['name']}**")
                sp = sale_price(p)
                list_price = float(p.get("price") or 0)
                price_txt = format_price(sp)
                if sp < list_price:
                    price_txt += f"  (was {format_price(list_price)})"
                st.caption(f"{price_txt} | Stock: {p.get('stock')} | "
                           f"💰 Profit/unit: {format_price(profit_per_unit(p))} | "
                           f"{'🟢 Active' if p.get('is_active') else '🔴 Hidden'}")
            with c3:
                if st.button("✏️ Edit", key=f"edit_{p['id']}"):
                    st.session_state.editing_product = p
                    st.rerun()
                if st.button("🔗 Share Link", key=f"share_{p['id']}",
                             help="Facebook ad ke liye share link (preview ke saath)"):
                    st.session_state[f"show_share_{p['id']}"] = \
                        not st.session_state.get(f"show_share_{p['id']}")
                if st.button("🗑️ Delete", key=f"del_{p['id']}"):
                    st.session_state[f"confirm_del_{p['id']}"] = True
                if st.session_state.get(f"confirm_del_{p['id']}"):
                    st.warning("Pakka delete karna hai?")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("Yes, delete", key=f"yesdel_{p['id']}"):
                            _del_urls = list(p.get("images") or [])
                            if p.get("video_url"):
                                _del_urls.append(p["video_url"])
                            for u in _del_urls:
                                storage.delete_by_url(u)
                            db.delete_product(p["id"])
                            if share:
                                share.trigger_share_build(
                                    "delete", {"id": p["id"],
                                               "slug": (p.get("slug") or "").strip()})
                            st.session_state.pop(f"confirm_del_{p['id']}", None)
                            st.success("Deleted.")
                            st.rerun()
                    with cc2:
                        if st.button("Cancel", key=f"nodel_{p['id']}"):
                            st.session_state.pop(f"confirm_del_{p['id']}", None)
                            st.rerun()
        if st.session_state.get(f"show_share_{p['id']}"):
            _surl = (share.share_url_for(p) if share
                     else f"https://skstoresk.github.io/skstoresk/share/{p['id']}.html")
            st.code(_surl)
            st.caption("↑ Ye link copy karke Facebook mein paste karo — "
                       "photo + price ka preview khud ban jayega.")

# ================= ORDERS =================
with tabs[2]:
    st.subheader("Orders")
    orders = db.get_orders()
    if not orders:
        st.info("Abhi koi order nahi aya. 🛒")
    fstatus = st.selectbox("Filter by status", ["All"] + db.ORDER_STATUSES)
    for o in orders:
        if fstatus != "All" and o["status"] != fstatus:
            continue
        label = (f"{o['order_number']} — {o['customer_name']} — "
                 f"{format_price(o.get('total',0))} — **{o['status']}**")
        with st.expander(label):
            st.markdown(f"📞 {o['phone']} &nbsp;&nbsp; 📧 {o.get('customer_email') or '—'}")
            st.markdown(f"📍 {o['address']}, {o['city']}, {o['country']}")
            st.markdown(f"🕐 {o.get('created_at','')[:16].replace('T',' ')}")
            for it in o.get("items", []) or []:
                st.markdown(f"- {it.get('name')} × {it.get('qty')} — "
                            f"{format_price(it.get('price',0)*it.get('qty',1))}")
            st.markdown(f"**Total (COD): {format_price(o.get('total',0))}**")
            st.divider()
            c1, c2 = st.columns(2)
            new_status = c1.selectbox("Order Status", db.ORDER_STATUSES,
                                      index=db.ORDER_STATUSES.index(o["status"]),
                                      key=f"st_{o['id']}")
            tracking = c2.text_input("Tracking ID (courier wali)",
                                     value=o.get("tracking_id") or "",
                                     key=f"tr_{o['id']}",
                                     placeholder="e.g. TCS-12345678")
            notify = st.checkbox("Customer ko email bhejo (status update)", value=True,
                                 key=f"em_{o['id']}")
            if st.button("💾 Update Order", key=f"sv_{o['id']}", type="primary"):
                try:
                    db.update_order(o["id"], {
                        "status": new_status,
                        "tracking_id": tracking.strip() or None,
                    })
                    st.success("✅ Order updated!")
                    if notify:
                        updated = dict(o, status=new_status,
                                       tracking_id=tracking.strip() or None)
                        ok, msg = emailer.send_status_update(updated)
                        if ok:
                            st.success("📧 Customer ko email bhej di.")
                        else:
                            st.warning(f"Email nahi bheji ja saki: {msg}")
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    st.error(f"Update failed: {e}")

# ================= BANNERS =================
PLACEMENT_LABELS = {
    "top": "⬆️ Top — home page ke bilkul upar",
    "middle": "↔️ Middle — home page darmiyan me (products ke beech)",
    "bottom": "⬇️ Bottom — home page ke neeche",
    "product": "📦 Product page — Add to Cart ke paas",
}

with tabs[3]:
    st.subheader("Banners (4 jaga lag sakte hain)")
    with st.form("banner_form", clear_on_submit=True):
        btype = st.selectbox("Banner type", ["new", "discount", "announcement"],
                             format_func=lambda x: {"new": "🆕 New Product",
                                                    "discount": "🔥 Discount",
                                                    "announcement": "📢 Announcement"}[x])
        bplace = st.selectbox("Banner ki jaga", list(PLACEMENT_LABELS.keys()),
                              format_func=lambda k: PLACEMENT_LABELS[k])
        btitle = st.text_input("Title *", placeholder="e.g. New Winter Collection!")
        bsub = st.text_input("Subtitle", placeholder="e.g. Flat 20% off — limited time")
        bimg = st.file_uploader("Banner image (optional)", type=["jpg", "jpeg", "png", "webp"])
        bsort = st.number_input("Sort order (chhota number = pehle)", min_value=0, value=0)
        if st.form_submit_button("➕ Add Banner", type="primary"):
            if not btitle.strip():
                st.error("Title zaroori hai.")
                st.stop()
            img_url = None
            if bimg:
                try:
                    img_url = storage.upload_image(bimg)
                except Exception as e:  # noqa: BLE001
                    st.error(f"Image upload failed: {e}")
                    st.stop()
            db.create_banner({"banner_type": btype, "placement": bplace,
                              "title": btitle.strip(),
                              "subtitle": bsub.strip(), "image_url": img_url,
                              "sort_order": int(bsort), "is_active": True})
            st.success("✅ Banner added!")
            st.rerun()
    st.divider()
    for b in db.get_banners(active_only=False):
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                _pl = PLACEMENT_LABELS.get(b.get("placement") or "top", "top")
                st.markdown(f"**[{b['banner_type']}] {b['title']}**")
                st.caption(f"{_pl} | {b.get('subtitle','')} | "
                           f"{'🟢 Active' if b['is_active'] else '🔴 Hidden'}")
            with c2:
                if st.button("🔄 Toggle", key=f"bt_{b['id']}"):
                    db.update_banner(b["id"], {"is_active": not b["is_active"]})
                    st.rerun()
                if st.button("🗑️", key=f"bd_{b['id']}"):
                    if b.get("image_url"):
                        storage.delete_by_url(b["image_url"])
                    db.delete_banner(b["id"])
                    st.rerun()

# ================= SETTINGS =================
with tabs[4]:
    st.subheader("Store Settings")
    with st.form("settings_form"):
        dfee = st.text_input("Delivery Fee (Rs)", value=db.get_setting("delivery_fee", "200"))
        ffree = st.text_input("FREE delivery is order se upar (Rs)",
                              value=db.get_setting("free_delivery_over", "5000"))
        ndays = st.text_input("NEW badge kitne din tak (days)",
                              value=db.get_setting("new_badge_days", "7"))
        cur_theme = db.get_setting("site_theme", DEFAULT_THEME)
        theme = st.selectbox(
            "🎨 Site ka theme (sab visitors ko yahi nazar ayega)",
            theme_keys(),
            index=theme_keys().index(cur_theme) if cur_theme in theme_keys() else 0,
            format_func=theme_label,
        )
        wa = st.text_input("💬 WhatsApp number (footer me rabta button ke liye)",
                           value=db.get_setting("whatsapp_number", ""),
                           placeholder="03001234567")
        if st.form_submit_button("💾 Save Settings", type="primary"):
            try:
                float(dfee); float(ffree); int(ndays)
            except ValueError:
                st.error("Sirf numbers likhein.")
                st.stop()
            db.set_setting("delivery_fee", dfee)
            db.set_setting("free_delivery_over", ffree)
            db.set_setting("new_badge_days", ndays)
            db.set_setting("site_theme", theme)
            db.set_setting("whatsapp_number", wa.strip())
            st.success("✅ Settings saved!")

# ================= SYSTEM CHECK =================
with tabs[5]:
    st.subheader("🔧 System Check")
    st.caption("Button dabao — sara system real-time check hoga. "
               "Kahin masla hua to hal bhi saath batayega.")
    if st.button("🔍 Abhi Check Karo", type="primary"):
        if not diagnostics:
            st.error("❌ lib/diagnostics.py GitHub par upload nahi hui.")
        else:
            with st.spinner("Check ho raha hai…"):
                results = diagnostics.run_checks()
            ok_n = sum(1 for r in results if r["ok"])
            if ok_n == len(results):
                st.success(f"🎉 Sab theek hai! {ok_n}/{len(results)} checks OK.")
            else:
                st.warning(f"⚠️ {ok_n}/{len(results)} checks OK — neeche masle dekho:")
            for r in results:
                if r["ok"]:
                    st.success(f"✅ {r['name']}")
                else:
                    st.error(f"❌ {r['name']}\n\n💡 {r['hint']}")

ui.admin_footer()
