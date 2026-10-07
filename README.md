# 🛍️ SK Store — Setup Guide

Professional online store: **Streamlit** (website) + **Supabase** (database + images/videos) + **GitHub** (code).

Tumhara account teeno par bana hua hai — bas neeche diye steps follow karo. Koi step samajh na aye to mujh se pooch lena.

---

## Step 1 — Supabase: Database banao (5 min)

1. [supabase.com](https://supabase.com) → login → **New project**
2. Name: `sk-store`, database password koi mazboot rakho → **Create new project**
3. Left menu → **SQL Editor** → **New query**
4. Is repo ki file `sql/schema.sql` ka **poora content copy** karke paste karo → **Run**
   - Tables ban jayengi: products, categories, orders, banners, settings
   - 2 storage buckets ban jayenge: product-images, product-videos

## Step 2 — Supabase: API keys copy karo (2 min)

1. Supabase → **Project Settings** (⚙️) → **API**
2. Ye 3 cheezein kahi mehfooz likh lo:
   - **Project URL** (jaise `https://xyzcompany.supabase.co`)
   - **anon public** key
   - **service_role** key (⚠️ ye secret hai — sirf Streamlit Secrets me dalna)

## Step 3 — GitHub: Code push karo (5 min)

1. [github.com](https://github.com) → **New repository** → naam `sk-store` → **Public** → Create
2. Apne computer par terminal me:

```bash
cd sk-store
git init
git add .
git commit -m "SK Store launch"
git branch -M main
git remote add origin https://github.com/skstoresk/sk-store.git
git push -u origin main
```

> Agar ye mushkil lage to mujhe batao — main GitHub Desktop ka asaan tareeqa bata dunga.

## Step 4 — Streamlit Cloud: Site live karo (5 min)

1. [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Repository: `sk-store`, Branch: `main`, Main file: `app.py` → **Deploy**
3. App khulne ke baad → **Settings → Secrets** → neeche wala template paste karke apni values bharo:

```toml
SUPABASE_URL = "https://xyzcompany.supabase.co"
SUPABASE_ANON_KEY = "paste-anon-key"
SUPABASE_SERVICE_KEY = "paste-service-role-key"
ADMIN_USER = "admin"
ADMIN_PASS = "apna-mazboot-password"
STORE_NAME = "SK Store"
APP_URL = "https://tumhari-app.streamlit.app"
GMAIL_USER = "tumhari@gmail.com"
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"
ADMIN_NOTIFY_EMAIL = "tumhari@gmail.com"
```

4. **Save** → app reboot hogi → site live! 🎉

## Step 5 — Gmail: Order emails ke liye App Password (3 min)

> Ye step zaroori hai taake order par **customer aur tum (admin) dono** ko email jaye.

1. [myaccount.google.com](https://myaccount.google.com) → **Security**
2. **2-Step Verification** ON karo (agar off hai)
3. Wapas Security me **App passwords** → app: **Mail** → **Generate**
4. 16-harf ka password milega → Streamlit Secrets me `GMAIL_APP_PASSWORD` me paste karo
5. `ADMIN_NOTIFY_EMAIL` me wo email likho jahan new-order alerts ane chahiye

## Step 6 — Facebook: Product link auto-preview (5 min)

Jab product ka link Facebook par paste hoga to photo + naam + price ka card auto show hoga:

1. Apne computer par `sk-store/.streamlit/secrets.toml` banao (Step 4 wali values)
2. Terminal me: `python tools/generate_share_pages.py`
3. `git add docs/share && git commit -m "share pages" && git push`
4. GitHub repo → **Settings → Pages** → Branch: `main`, folder: `/docs` → Save
5. Share link hoga: `https://skstoresk.github.io/sk-store/share/<product-id>.html`
   - Product ID: admin portal → Products me har product ki ID nazar ayegi
   - Jab naye products add ho jayen to generator dobara chalao

## Step 7 — Admin portal use karo

1. Site ka link kholo, end me `/admin` lagao → jaise `https://tumhari-app.streamlit.app/admin`
2. Login (wohi `ADMIN_USER` / `ADMIN_PASS` jo secrets me dala)
3. **Products** → pehla product add karo:
   - Naam, description, price, discount %, category
   - **Images: minimum 2, maximum 6** (upload karo)
   - **Video:** file upload karo **ya** YouTube link paste karo
   - Stock likho → Save → site par **foran live** ✅
4. **Orders** → koi order aye to status update karo (Pending → Confirmed → Shipped → Delivered)
   aur courier ki **Tracking ID** usi order me likho → customer ko email bhi chali jayegi
5. **Banners** → new product / discount banners lagao
6. **Settings** → delivery fee, free-delivery limit, NEW badge ke din

---

## Features checklist

- ✅ `/admin` portal — login protected, products add/edit/delete (real-time update)
- ✅ Product: 2–6 images, video upload **ya** YouTube link
- ✅ Orders: status update + tracking ID per order, customer email alerts
- ✅ Gmail confirmation: customer + admin dono ko
- ✅ New product banner, discount banner, NEW badge (7 din)
- ✅ Categories + search
- ✅ Cart par COD message: *"Only Cash on Delivery service available hai filhal"*
- ✅ Pakistan-only delivery (professional error message)
- ✅ Customer order tracking page (order number se)
- ✅ Footer: Made with ❤ | © Kaleem
- ✅ Facebook share links — auto preview card

Kuch atak jaye to screenshot bhej dena, main dekh lunga. 👍
