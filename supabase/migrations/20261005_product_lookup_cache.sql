create table if not exists public.product_lookup_cache (
  code text primary key,
  results jsonb not null default '[]'::jsonb,
  searched_at timestamptz not null default now(),
  expires_at timestamptz not null default (now() + interval '30 days')
);

alter table public.product_lookup_cache enable row level security;

comment on table public.product_lookup_cache is
  'Cache de resultados de busca externa por código de produto. Acesso somente por Edge Function administrativa.';

create index if not exists product_lookup_cache_expires_idx
  on public.product_lookup_cache (expires_at);
