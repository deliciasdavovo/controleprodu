-- Organização de embalagens por produto e unidade.
-- Dados salvos em uma linha por unidade, incluindo miniaturas JPEG compactadas no JSONB.
create table if not exists public.packaging_matrices (
  unit_code text primary key,
  layout jsonb not null default '{"titulo":"Organização das embalagens","embalagens":[],"linhas":[]}'::jsonb,
  updated_at timestamptz not null default now(),
  constraint packaging_matrices_layout_object check (jsonb_typeof(layout) = 'object'),
  constraint packaging_matrices_layout_limit check (octet_length(layout::text) < 3000000)
);
alter table public.packaging_matrices enable row level security;

-- A aplicação atual não implementa autenticação; esta política segue as tabelas
-- operacionais existentes. Restringir a usuários autenticados quando o login for implantado.
create policy packaging_matrices_full_access
on public.packaging_matrices
for all
to anon, authenticated
using (true)
with check (true);

grant select, insert, update, delete on public.packaging_matrices to anon, authenticated;
