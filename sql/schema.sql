-- ============================================================
-- SK STORE — Supabase database schema
-- HOW TO RUN: Supabase Dashboard → SQL Editor → New query →
-- paste this whole file → Run. Bas ek dafa chalana hai.
-- ============================================================

-- ---------- tables ----------
create table if not exists public.categories (
  id uuid primary key default gen_random_uuid(),
  name text unique not null,
  created_at timestamptz not null default now()
);

create table if not exists public.products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text not null default '',
  price numeric not null check (price >= 0),
  discount_percent numeric not null default 0
    check (discount_percent >= 0 and discount_percent <= 90),
  discount_price numeric check (discount_price is null or discount_price >= 0),
  buy_price numeric not null default 0 check (buy_price >= 0),
  delivery_expense numeric not null default 0 check (delivery_expense >= 0),
  packing_expense numeric not null default 0 check (packing_expense >= 0),
  category_id uuid references public.categories(id) on delete set null,
  images text[] not null default '{}',
  video_url text,
  youtube_url text,
  stock integer not null default 0 check (stock >= 0),
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);
create index if not exists products_active_idx
  on public.products (is_active, created_at desc);

create table if not exists public.banners (
  id uuid primary key default gen_random_uuid(),
  banner_type text not null
    check (banner_type in ('new', 'discount', 'announcement')),
  title text not null,
  subtitle text not null default '',
  image_url text,
  is_active boolean not null default true,
  sort_order integer not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists public.orders (
  id uuid primary key default gen_random_uuid(),
  order_number text unique not null,
  customer_name text not null,
  customer_email text,
  phone text not null,
  address text not null,
  city text not null,
  country text not null default 'Pakistan',
  items jsonb not null default '[]'::jsonb,
  subtotal numeric not null default 0,
  delivery_fee numeric not null default 0,
  total numeric not null default 0,
  status text not null default 'Pending'
    check (status in ('Pending','Confirmed','Shipped','Delivered','Cancelled')),
  tracking_id text,
  created_at timestamptz not null default now()
);
create index if not exists orders_number_idx on public.orders (order_number);
create index if not exists orders_created_idx on public.orders (created_at desc);

create table if not exists public.settings (
  key text primary key,
  value text not null,
  updated_at timestamptz not null default now()
);

insert into public.settings (key, value) values
  ('delivery_fee', '200'),
  ('free_delivery_over', '5000'),
  ('new_badge_days', '7'),
  ('store_name', 'SK Store'),
  ('site_theme', 'dark-gold')
on conflict (key) do nothing;

-- ---------- storage buckets (product images & videos) ----------
insert into storage.buckets (id, name, public)
values ('product-images', 'product-images', true),
       ('product-videos', 'product-videos', true)
on conflict (id) do update set public = true;

-- public read access so site visitors can see images/videos
drop policy if exists "sk public read images" on storage.objects;
create policy "sk public read images"
  on storage.objects for select
  using (bucket_id = 'product-images');

drop policy if exists "sk public read videos" on storage.objects;
create policy "sk public read videos"
  on storage.objects for select
  using (bucket_id = 'product-videos');

-- NOTE: uploads/deletes happen through the Streamlit backend using the
-- service_role key (kept in Streamlit secrets), which bypasses RLS.

-- ============================================================
-- MIGRATION (purani database ke liye — ek dafa chalao):
-- Naye columns add karo + purane discount_percent ko discount_price me badlo.
-- ============================================================
alter table public.products
  add column if not exists discount_price numeric
    check (discount_price is null or discount_price >= 0),
  add column if not exists buy_price numeric not null default 0
    check (buy_price >= 0),
  add column if not exists delivery_expense numeric not null default 0
    check (delivery_expense >= 0),
  add column if not exists packing_expense numeric not null default 0
    check (packing_expense >= 0);

update public.products
set discount_price = round(price * (1 - discount_percent / 100), 2)
where discount_price is null
  and coalesce(discount_percent, 0) > 0;
