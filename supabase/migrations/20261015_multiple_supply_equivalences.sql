-- As novas relações complementam as equivalências legadas e não alteram compras históricas.
alter table public.supplies
  add column if not exists unit_equivalences jsonb not null default '[]'::jsonb;

alter table public.supplies
  drop constraint if exists supplies_unit_equivalences_array_check;

alter table public.supplies
  add constraint supplies_unit_equivalences_array_check
    check (jsonb_typeof(unit_equivalences) = 'array');

comment on column public.supplies.unit_equivalences is
  'Conversões do produto: [{"fromUnit":"un","toUnit":"g","factor":1800},{"fromUnit":"fatia","toUnit":"g","factor":30}]. A relação antiga continua suportada.';
