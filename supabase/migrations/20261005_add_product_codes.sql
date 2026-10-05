alter table public.supplies
  add column if not exists product_code text;

alter table public.separated_products
  add column if not exists product_code text;

create index if not exists supplies_product_code_idx
  on public.supplies (product_code);

create index if not exists separated_products_product_code_idx
  on public.separated_products (unit_code, product_code);

comment on column public.supplies.product_code is
  'Código de busca do produto/insumo usado no cadastro e no lançamento de compras.';

comment on column public.separated_products.product_code is
  'Código de busca do produto de revenda usado no cadastro e no lançamento de compras.';
