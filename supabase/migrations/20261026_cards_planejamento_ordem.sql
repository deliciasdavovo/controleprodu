-- Ordem dos cards do planejamento independente dos espaços de vitrine.
-- Não altera quantidades, histórico ou registros já existentes.
alter table public.standard_plans
  add column if not exists display_order integer not null default 0;
