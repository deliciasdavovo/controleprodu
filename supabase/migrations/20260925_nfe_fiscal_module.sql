-- NF-e fiscal module
-- Live production migration applied on 2026-09-25.
-- The fiscal access token itself is provisioned outside this file and is never committed.

create extension if not exists pgcrypto;
create extension if not exists supabase_vault with schema vault;

create table if not exists public.nfe_documents (
  id uuid primary key default gen_random_uuid(),
  access_key text not null unique check (access_key ~ '^[0-9]{44}$'),
  nsu text,
  source_profile text not null default 'default',
  schema_name text not null default '',
  document_kind text not null default 'summary'
    check (document_kind in ('summary','full')),
  status text not null default 'received'
    check (status in ('received','awaiting_xml','ready','needs_mapping','imported','cancelled','error')),
  environment smallint not null default 1 check (environment in (1,2)),
  issuer_cnpj text not null default '',
  issuer_name text not null default '',
  recipient_cnpj text not null default '',
  issue_date date,
  total_value numeric(14,2) not null default 0 check (total_value >= 0),
  nfe_number text not null default '',
  series text not null default '',
  raw_xml text,
  raw_summary text,
  imported_unit_code text,
  imported_at timestamptz,
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.nfe_items (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.nfe_documents(id) on delete cascade,
  item_number integer not null check (item_number > 0),
  supplier_product_code text not null default '',
  description text not null default '',
  ncm text not null default '',
  cfop text not null default '',
  gtin text not null default '',
  commercial_unit text not null default '',
  qty numeric(18,6) not null default 0 check (qty >= 0),
  unit_value numeric(18,6) not null default 0 check (unit_value >= 0),
  total_value numeric(14,2) not null default 0 check (total_value >= 0),
  supply_id uuid references public.supplies(id) on delete set null,
  separated_product_id uuid references public.separated_products(id) on delete set null,
  purchase_qty numeric(18,6),
  purchase_unit text not null default '',
  mapping_status text not null default 'unmapped'
    check (mapping_status in ('unmapped','mapped_supply','mapped_resale','ignored','imported')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(document_id, item_number),
  check (not (supply_id is not null and separated_product_id is not null))
);

create table if not exists public.nfe_product_mappings (
  id uuid primary key default gen_random_uuid(),
  source_profile text not null default 'default',
  issuer_cnpj text not null,
  supplier_product_code text not null,
  description_hint text not null default '',
  supply_id uuid references public.supplies(id) on delete cascade,
  separated_product_id uuid references public.separated_products(id) on delete cascade,
  qty_multiplier numeric(18,6) not null default 1 check (qty_multiplier > 0),
  purchase_unit text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check ((supply_id is not null)::int + (separated_product_id is not null)::int = 1)
);

create table if not exists public.nfe_sync_state (
  id text primary key default 'default',
  last_nsu text not null default '000000000000000',
  max_nsu text not null default '000000000000000',
  last_status_code text not null default '',
  last_status_message text not null default '',
  last_sync_at timestamptz,
  updated_at timestamptz not null default now()
);

create table if not exists public.nfe_settings (
  id text primary key default 'default',
  access_token_hash text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.supply_purchases
  add column if not exists nfe_document_id uuid references public.nfe_documents(id) on delete set null,
  add column if not exists nfe_item_id uuid references public.nfe_items(id) on delete set null;

alter table public.resale_purchases
  add column if not exists nfe_document_id uuid references public.nfe_documents(id) on delete set null,
  add column if not exists nfe_item_id uuid references public.nfe_items(id) on delete set null;

create unique index if not exists nfe_documents_profile_nsu_unique
  on public.nfe_documents(source_profile, nsu)
  where nsu is not null;
create index if not exists nfe_documents_profile_date_idx on public.nfe_documents(source_profile, issue_date desc);
create index if not exists nfe_documents_issue_date_idx on public.nfe_documents(issue_date desc);
create index if not exists nfe_documents_status_idx on public.nfe_documents(status);
create index if not exists nfe_documents_issuer_idx on public.nfe_documents(issuer_cnpj, issue_date desc);
create index if not exists nfe_items_document_idx on public.nfe_items(document_id);
create index if not exists nfe_items_mapping_status_idx on public.nfe_items(mapping_status);
create index if not exists nfe_items_supply_id_idx on public.nfe_items(supply_id);
create index if not exists nfe_items_separated_product_id_idx on public.nfe_items(separated_product_id);
create unique index if not exists nfe_product_mappings_profile_supplier_code_unique
  on public.nfe_product_mappings(source_profile, issuer_cnpj, supplier_product_code);
create index if not exists nfe_product_mappings_profile_idx on public.nfe_product_mappings(source_profile);
create index if not exists nfe_product_mappings_supply_id_idx on public.nfe_product_mappings(supply_id);
create index if not exists nfe_product_mappings_separated_product_id_idx on public.nfe_product_mappings(separated_product_id);
create unique index if not exists supply_purchases_nfe_item_unique
  on public.supply_purchases(nfe_item_id) where nfe_item_id is not null;
create unique index if not exists resale_purchases_nfe_item_unique
  on public.resale_purchases(nfe_item_id) where nfe_item_id is not null;
create index if not exists supply_purchases_nfe_document_id_idx on public.supply_purchases(nfe_document_id);
create index if not exists resale_purchases_nfe_document_id_idx on public.resale_purchases(nfe_document_id);

alter table public.nfe_documents enable row level security;
alter table public.nfe_items enable row level security;
alter table public.nfe_product_mappings enable row level security;
alter table public.nfe_sync_state enable row level security;
alter table public.nfe_settings enable row level security;

-- Intentionally no anon/authenticated policies on fiscal tables.
-- The Edge Function uses service_role and is the only browser-facing bridge.

create or replace function public.nfe_store_secret(
  p_name text,
  p_value text,
  p_description text default ''
)
returns void
language plpgsql
security definer
set search_path = public, vault
as $$
declare
  v_id uuid;
begin
  if p_name is null or btrim(p_name) = '' then
    raise exception 'Nome do segredo obrigatório';
  end if;

  select id into v_id
  from vault.secrets
  where name = p_name
  limit 1;

  if v_id is null then
    perform vault.create_secret(p_value, p_name, p_description);
  else
    perform vault.update_secret(v_id, p_value, p_name, p_description);
  end if;
end;
$$;

create or replace function public.nfe_read_secret(p_name text)
returns text
language sql
security definer
set search_path = public, vault
as $$
  select decrypted_secret
  from vault.decrypted_secrets
  where name = p_name
  order by updated_at desc
  limit 1;
$$;

create or replace function public.nfe_delete_secret(p_name text)
returns void
language plpgsql
security definer
set search_path = public, vault
as $$
begin
  delete from vault.secrets where name = p_name;
end;
$$;

revoke all on function public.nfe_store_secret(text,text,text) from public, anon, authenticated;
revoke all on function public.nfe_read_secret(text) from public, anon, authenticated;
revoke all on function public.nfe_delete_secret(text) from public, anon, authenticated;

grant execute on function public.nfe_store_secret(text,text,text) to service_role;
grant execute on function public.nfe_read_secret(text) to service_role;
grant execute on function public.nfe_delete_secret(text) to service_role;
