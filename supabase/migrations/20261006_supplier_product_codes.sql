-- Codigo comercial especifico do fornecedor. Nao substitui product_code legado.
create table if not exists public.supplier_product_codes (
  id uuid primary key default gen_random_uuid(),
  supplier_name text not null,
  product_code text not null,
  supply_id uuid references public.supplies(id) on delete cascade,
  separated_product_id uuid references public.separated_products(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint supplier_product_codes_target_check check (num_nonnulls(supply_id, separated_product_id) = 1),
  constraint supplier_product_codes_supplier_not_blank check (length(btrim(supplier_name)) > 0),
  constraint supplier_product_codes_code_not_blank check (length(btrim(product_code)) > 0)
);
create unique index if not exists supplier_product_codes_supplier_code_unique
on public.supplier_product_codes (lower(btrim(supplier_name)), lower(btrim(product_code)));
create index if not exists supplier_product_codes_supply_idx on public.supplier_product_codes(supply_id);
create index if not exists supplier_product_codes_resale_idx on public.supplier_product_codes(separated_product_id);
alter table public.supplier_product_codes enable row level security;
create policy supplier_product_codes_full_access on public.supplier_product_codes
for all to anon, authenticated using (true) with check (true);
grant select, insert, update, delete on public.supplier_product_codes to anon, authenticated;
comment on table public.supplier_product_codes is 'Cada codigo comercial pertence a um fornecedor e referencia um unico produto mestre.';
