create table if not exists public.nfe_fiscal_admins (user_id uuid primary key references auth.users(id) on delete cascade, created_at timestamptz default now());
alter table public.nfe_fiscal_admins enable row level security;
