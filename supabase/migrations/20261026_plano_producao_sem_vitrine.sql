-- Permite planejamento semanal por produto sem associação a espaços físicos.
-- Os planejamentos antigos com slot_code preenchido são preservados.
alter table public.standard_plans alter column slot_code drop not null;

-- Novas linhas sem vitrine: somente um plano por unidade, dia e produto.
create unique index if not exists standard_plans_product_day_without_slot
  on public.standard_plans (unit_code, day_of_week, product_id)
  where slot_code is null;
