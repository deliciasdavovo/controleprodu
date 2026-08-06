-- =====================================================================
-- Delícias da Vovó — Controle de Produção e Vitrine
-- Schema para Supabase (PostgreSQL)
--
-- Como usar:
--   1. Abra o painel do Supabase → SQL Editor → New query
--   2. Cole este arquivo inteiro e clique em "Run"
--
-- O script é idempotente: pode ser executado várias vezes sem erro.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. Função utilitária: mantém updated_at sempre atualizado
--    (gen_random_uuid() é nativo do Postgres 13+, não precisa de extensão)
-- ---------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;


-- ---------------------------------------------------------------------
-- 2. Unidades (lojas)
-- ---------------------------------------------------------------------
create table if not exists public.units (
  code        text primary key,
  name        text not null,
  created_at  timestamptz not null default now()
);

comment on table public.units is 'Unidades da rede: matriz e vila nova.';


-- ---------------------------------------------------------------------
-- 3. Catálogo de produtos
-- ---------------------------------------------------------------------
create table if not exists public.products (
  id                     uuid primary key default gen_random_uuid(),
  name                   text not null,
  responsible            text not null default '',
  category               text not null default 'salgado',
  default_unit           text not null default 'un',
  min_replenishment_qty  integer not null default 5,
  shelf_life_days        integer not null default 2,
  price                  numeric(10,2) not null default 0,
  is_active              boolean not null default true,
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now(),
  constraint products_name_unique unique (name),
  constraint products_category_check
    check (category in ('salgado', 'doce', 'sobremesa')),
  constraint products_min_qty_check check (min_replenishment_qty >= 0),
  constraint products_shelf_life_check check (shelf_life_days > 0),
  constraint products_price_check check (price >= 0)
);

-- Bancos criados antes do campo "responsável" recebem a coluna aqui
alter table public.products
  add column if not exists responsible text not null default '';

create index if not exists products_responsible_idx on public.products (responsible);

comment on table public.products is 'Salgados, doces e sobremesas produzidos pela casa.';
comment on column public.products.shelf_life_days is 'Validade em dias contados a partir da data de fabricação.';
comment on column public.products.responsible is 'Quem produz e responde pelo produto. Vazio = sem responsável definido.';


-- ---------------------------------------------------------------------
-- 4. Espaços físicos da vitrine (slots)
--    O código segue o padrão usado no app: matriz-salgada-s1-p1
-- ---------------------------------------------------------------------
create table if not exists public.showcase_slots (
  code           text primary key,
  unit_code      text not null references public.units (code) on delete cascade,
  showcase_type  text not null,
  shelf_number   integer not null,
  slot_number    integer not null,
  section_title  text not null,
  created_at     timestamptz not null default now(),
  constraint showcase_slots_type_check
    check (showcase_type in ('salgada', 'doce', 'sobremesa')),
  constraint showcase_slots_shelf_check check (shelf_number > 0),
  constraint showcase_slots_slot_check check (slot_number > 0),
  constraint showcase_slots_position_unique
    unique (unit_code, showcase_type, shelf_number, slot_number)
);

create index if not exists showcase_slots_unit_type_idx
  on public.showcase_slots (unit_code, showcase_type);

comment on table public.showcase_slots is 'Cada posição física da vitrine, por unidade e tipo.';


-- ---------------------------------------------------------------------
-- 5. Itens atualmente expostos na vitrine
-- ---------------------------------------------------------------------
create table if not exists public.slot_items (
  id                uuid primary key default gen_random_uuid(),
  slot_code         text not null references public.showcase_slots (code) on delete cascade,
  product_id        uuid not null references public.products (id) on delete restrict,
  produced_qty      integer not null default 0,
  current_qty       integer not null default 0,
  unit_of_measure   text not null default 'un',
  min_qty           integer not null default 0,
  manufacture_date  date not null default current_date,
  entry_date        date not null default current_date,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  constraint slot_items_produced_check check (produced_qty >= 0),
  constraint slot_items_current_check check (current_qty >= 0),
  constraint slot_items_min_check check (min_qty >= 0)
);

create index if not exists slot_items_slot_idx on public.slot_items (slot_code);
create index if not exists slot_items_product_idx on public.slot_items (product_id);
create index if not exists slot_items_manufacture_idx on public.slot_items (manufacture_date);

drop trigger if exists slot_items_set_updated_at on public.slot_items;
create trigger slot_items_set_updated_at
  before update on public.slot_items
  for each row execute function public.set_updated_at();

comment on table public.slot_items is 'O que está exposto agora em cada espaço da vitrine.';


-- ---------------------------------------------------------------------
-- 6. Vitrine padrão (planejamento por dia da semana)
-- ---------------------------------------------------------------------
create table if not exists public.standard_plans (
  id               uuid primary key default gen_random_uuid(),
  unit_code        text not null references public.units (code) on delete cascade,
  day_of_week      text not null,
  slot_code        text not null references public.showcase_slots (code) on delete cascade,
  product_id       uuid not null references public.products (id) on delete cascade,
  ideal_qty        integer not null default 1,
  unit_of_measure  text not null default 'un',
  priority         text not null default 'B',
  frequency        text not null default 'dias',
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  constraint standard_plans_day_check
    check (day_of_week in ('segunda', 'terca', 'quarta', 'quinta', 'sexta', 'sabado', 'domingo')),
  constraint standard_plans_ideal_check check (ideal_qty > 0),
  constraint standard_plans_slot_day_unique unique (unit_code, day_of_week, slot_code)
);

-- Classificação do item na vitrine padrão. Bancos criados antes recebem as
-- colunas aqui, já com o valor que o app usa como padrão.
alter table public.standard_plans
  add column if not exists priority text not null default 'B';
alter table public.standard_plans
  add column if not exists frequency text not null default 'dias';

alter table public.standard_plans drop constraint if exists standard_plans_priority_check;
alter table public.standard_plans
  add constraint standard_plans_priority_check check (priority in ('A', 'B', 'C', 'D'));

alter table public.standard_plans drop constraint if exists standard_plans_frequency_check;
alter table public.standard_plans
  add constraint standard_plans_frequency_check check (frequency in ('todo_dia', 'dias'));

create index if not exists standard_plans_unit_day_idx
  on public.standard_plans (unit_code, day_of_week);
create index if not exists standard_plans_priority_idx
  on public.standard_plans (unit_code, priority);

comment on column public.standard_plans.priority is
  'A = não pode faltar, B = importante, C = complementar, D = extra. Define quando o pedido de produção chama o item.';
comment on column public.standard_plans.frequency is
  'todo_dia = o item está nos sete dias; dias = só nos dias marcados na vitrine padrão.';

drop trigger if exists standard_plans_set_updated_at on public.standard_plans;
create trigger standard_plans_set_updated_at
  before update on public.standard_plans
  for each row execute function public.set_updated_at();

comment on table public.standard_plans is 'Como a vitrine deve ficar em cada dia da semana.';


-- ---------------------------------------------------------------------
-- 7. Registro de vendas
-- ---------------------------------------------------------------------
create table if not exists public.sale_records (
  id                uuid primary key default gen_random_uuid(),
  unit_code         text not null references public.units (code) on delete cascade,
  product_id        uuid references public.products (id) on delete set null,
  product_name      text not null,
  responsible       text not null default '',
  qty               integer not null,
  produced_qty      integer,
  unit_of_measure   text not null default 'un',
  manufacture_date  date,
  exposure_days     integer,
  sold_at           timestamptz not null default now(),
  created_at        timestamptz not null default now(),
  constraint sale_records_qty_check check (qty > 0)
);

-- Guarda quem era o responsável no momento da baixa
alter table public.sale_records
  add column if not exists responsible text not null default '';

create index if not exists sale_records_unit_date_idx
  on public.sale_records (unit_code, sold_at desc);
create index if not exists sale_records_product_idx on public.sale_records (product_id);

comment on table public.sale_records is 'Baixas por venda, com o tempo que o item ficou exposto.';
comment on column public.sale_records.responsible is 'Responsável pelo produto na data da venda.';


-- ---------------------------------------------------------------------
-- 8. Registro de perdas
-- ---------------------------------------------------------------------
create table if not exists public.loss_records (
  id                uuid primary key default gen_random_uuid(),
  unit_code         text not null references public.units (code) on delete cascade,
  product_id        uuid references public.products (id) on delete set null,
  product_name      text not null,
  responsible       text not null default '',
  qty               integer not null,
  produced_qty      integer,
  unit_of_measure   text not null default 'un',
  manufacture_date  date,
  loss_date         date not null default current_date,
  reason            text not null default 'vencido',
  details           text,
  slot_code         text references public.showcase_slots (code) on delete set null,
  created_at        timestamptz not null default now(),
  constraint loss_records_qty_check check (qty > 0),
  constraint loss_records_reason_check
    check (reason in ('vencido', 'danificado', 'qualidade', 'quebrado'))
);

-- Guarda quem era o responsável no momento da baixa
alter table public.loss_records
  add column if not exists responsible text not null default '';

create index if not exists loss_records_unit_date_idx
  on public.loss_records (unit_code, loss_date desc);
create index if not exists loss_records_product_idx on public.loss_records (product_id);
create index if not exists loss_records_responsible_idx on public.loss_records (unit_code, responsible);

comment on table public.loss_records is 'Baixas por perda, com motivo e observações.';
comment on column public.loss_records.responsible is 'Responsável pelo produto na data da perda.';


-- ---------------------------------------------------------------------
-- 9. Histórico de produção (o que foi colocado na vitrine)
--
-- slot_items mostra só o que está exposto agora e some quando o item
-- acaba. Esta tabela guarda cada lançamento, para a loja poder olhar
-- para trás e ver o que foi produzido em cada dia.
-- ---------------------------------------------------------------------
create table if not exists public.production_records (
  id                uuid primary key default gen_random_uuid(),
  unit_code         text not null references public.units (code) on delete cascade,
  product_id        uuid references public.products (id) on delete set null,
  product_name      text not null,
  responsible       text not null default '',
  qty               integer not null,
  unit_of_measure   text not null default 'un',
  manufacture_date  date,
  slot_code         text references public.showcase_slots (code) on delete set null,
  source            text not null default 'avulso',
  produced_at       timestamptz not null default now(),
  created_at        timestamptz not null default now(),
  constraint production_records_qty_check check (qty > 0),
  constraint production_records_source_check
    check (source in ('avulso', 'pedido'))
);

create index if not exists production_records_unit_date_idx
  on public.production_records (unit_code, produced_at desc);
create index if not exists production_records_product_idx
  on public.production_records (product_id);
create index if not exists production_records_responsible_idx
  on public.production_records (unit_code, responsible);

comment on table public.production_records is 'Cada item colocado na vitrine, com quantidade, espaço e responsável.';
comment on column public.production_records.source is 'avulso = lista de apoio; pedido = pedido de produção do dia.';


-- ---------------------------------------------------------------------
-- 10. Produtos fora da vitrine (revenda, cafeteria, encomenda)
-- ---------------------------------------------------------------------
create table if not exists public.separated_products (
  id               uuid primary key default gen_random_uuid(),
  unit_code        text not null references public.units (code) on delete cascade,
  name             text not null,
  category         text not null default 'revenda',
  current_qty      integer not null default 0,
  unit_of_measure  text not null default 'un',
  min_qty          integer not null default 0,
  price            numeric(10,2) not null default 0,
  is_active        boolean not null default true,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  constraint separated_products_category_check
    check (category in ('revenda', 'cafeteria', 'encomenda')),
  constraint separated_products_qty_check check (current_qty >= 0),
  constraint separated_products_price_check check (price >= 0),
  constraint separated_products_unit_name_unique unique (unit_code, name)
);

create index if not exists separated_products_unit_idx
  on public.separated_products (unit_code, category);

drop trigger if exists separated_products_set_updated_at on public.separated_products;
create trigger separated_products_set_updated_at
  before update on public.separated_products
  for each row execute function public.set_updated_at();

comment on table public.separated_products is 'Bebidas, cafeteria e encomendas — estoque fora da vitrine.';


-- ---------------------------------------------------------------------
-- 11. Dados iniciais
-- ---------------------------------------------------------------------

-- Unidades
insert into public.units (code, name) values
  ('matriz', 'Matriz'),
  ('vilanova', 'Vila Nova')
on conflict (code) do nothing;

-- Catálogo de produtos
--
-- Os responsáveis NÃO são preenchidos aqui: quem responde por cada produto é
-- só quem a loja cadastrar na tela "Produtos". Nada de nome inventado.
insert into public.products (name, category, default_unit, min_replenishment_qty, shelf_life_days, price) values
  ('Coxinha de Frango com Catupiry',          'salgado',   'un', 10, 2,  8.50),
  ('Empada de Frango',                        'salgado',   'un',  8, 2,  7.50),
  ('Pastel de Carne Assado',                  'salgado',   'un', 10, 2,  8.00),
  ('Croissant de Presunto e Queijo',          'salgado',   'un',  6, 1, 12.00),
  ('Pão de Queijo Tradicional',               'salgado',   'un', 15, 1,  4.50),
  ('Sonho de Creme',                          'doce',      'un',  8, 2,  6.50),
  ('Donut Glaceado',                          'doce',      'un',  8, 2,  7.00),
  ('Fatia de Bolo de Cenoura com Chocolate',  'sobremesa', 'un',  5, 3,  9.50),
  ('Torta Holandesa (Fatia)',                 'sobremesa', 'un',  4, 3, 14.00),
  ('Pudim de Leite Condensado (Fatia)',       'sobremesa', 'un',  6, 3, 10.00)
on conflict (name) do nothing;

-- Limpeza dos responsáveis de exemplo que versões antigas deste arquivo
-- gravaram sozinhas. Só apaga estes quatro nomes; qualquer responsável
-- cadastrado pela loja fica como está.
do $$
declare
  demo text[] := array['Dona Rita', 'Marcos Pereira', 'Juliana Alves', 'Camila Souza'];
begin
  update public.products           set responsible = '' where responsible = any (demo);
  update public.sale_records       set responsible = '' where responsible = any (demo);
  update public.loss_records       set responsible = '' where responsible = any (demo);
  update public.production_records set responsible = '' where responsible = any (demo);
end;
$$;

-- ---------------------------------------------------------------------
-- Espaços da vitrine — o desenho real das duas lojas
--
-- Cada linha da tabela abaixo é uma vitrine, com o número de espaços
-- que ela tem de verdade. Para mudar a loja, mude só o número da última
-- coluna e rode o script de novo.
--
--   Matriz     salgada 1  12  |  salgada 2  12  |  doce  12  |  sobremesa  12
--   Vila Nova  salgada    16  |  doce        8  |  sobremesa  8
--
-- ATENÇÃO: espaços que deixarem de existir no desenho abaixo são
-- apagados, junto com o que estiver exposto neles e com o que o padrão
-- da semana tiver planejado para eles. As vendas, perdas e o histórico
-- de produção continuam guardados — só perdem a ligação com o espaço.
--
-- Tudo em um comando só: o SQL Editor do Supabase pode rodar cada
-- comando em uma conexão diferente, então nada de tabela temporária.
-- ---------------------------------------------------------------------
with layout (unit_code, showcase_type, shelf_number, section_label, slots) as (
  values
    -- Matriz: duas vitrines de salgada, uma de doce e uma de sobremesa
    ('matriz',   'salgada',   1, 'Vitrine Salgada 1', 12),
    ('matriz',   'salgada',   2, 'Vitrine Salgada 2', 12),
    ('matriz',   'doce',      1, 'Vitrine Doce',      12),
    ('matriz',   'sobremesa', 1, 'Vitrine Sobremesa', 12),
    -- Vila Nova
    ('vilanova', 'salgada',   1, 'Vitrine Salgada',   16),
    ('vilanova', 'doce',      1, 'Vitrine Doce',       8),
    ('vilanova', 'sobremesa', 1, 'Vitrine Sobremesa',  8)
),
espacos as (
  select
    format('%s-%s-s%s-p%s', l.unit_code, l.showcase_type, l.shelf_number, s.n) as code,
    l.unit_code,
    l.showcase_type,
    l.shelf_number,
    s.n as slot_number,
    l.section_label
  from layout l
  cross join lateral generate_series(1, l.slots) as s(n)
),
-- Cria o que falta e renomeia as seções que mudaram de nome
gravados as (
  insert into public.showcase_slots (code, unit_code, showcase_type, shelf_number, slot_number, section_title)
  select code, unit_code, showcase_type, shelf_number, slot_number, section_label
  from espacos
  on conflict (code) do update
    set section_title = excluded.section_title
  returning code
)
-- E tira da loja os espaços que não existem mais
delete from public.showcase_slots sl
where sl.unit_code in (select unit_code from layout)
  and not exists (select 1 from espacos e where e.code = sl.code);

-- Itens fora da vitrine (exemplo inicial da Matriz)
insert into public.separated_products (unit_code, name, category, current_qty, unit_of_measure, min_qty, price) values
  ('matriz', 'Coca-Cola Zero 350ml',            'revenda',   24, 'un', 12, 6.50),
  ('matriz', 'Suco Del Valle Laranja 290ml',    'revenda',   18, 'un', 10, 7.00),
  ('matriz', 'Café Expresso Tradicional',       'cafeteria', 50, 'un', 20, 5.00),
  ('matriz', 'Cappuccino com Canela',           'cafeteria', 30, 'un', 15, 8.50)
on conflict (unit_code, name) do nothing;


-- ---------------------------------------------------------------------
-- 12. Visões de apoio
-- ---------------------------------------------------------------------

-- Situação de cada item na vitrine, com o status de validade já calculado
create or replace view public.showcase_status as
select
  si.id                as slot_item_id,
  s.unit_code,
  s.code               as slot_code,
  s.showcase_type,
  s.shelf_number,
  s.slot_number,
  s.section_title,
  p.id                 as product_id,
  p.name               as product_name,
  p.shelf_life_days,
  si.produced_qty,
  si.current_qty,
  si.unit_of_measure,
  si.manufacture_date,
  (current_date - si.manufacture_date) as days_in_showcase,
  case
    when (current_date - si.manufacture_date) >= p.shelf_life_days then 'vencido'
    when (current_date - si.manufacture_date) = p.shelf_life_days - 1 then 'atencao'
    else 'fresco'
  end as status,
  -- colunas novas entram no fim para que o create or replace continue funcionando
  p.responsible
from public.slot_items si
join public.showcase_slots s on s.code = si.slot_code
join public.products p on p.id = si.product_id;

-- Necessidade de produção: padrão ideal do dia menos o que já está na vitrine
create or replace view public.production_needs as
select
  sp.unit_code,
  sp.day_of_week,
  sp.slot_code,
  s.section_title,
  s.shelf_number,
  s.slot_number,
  sp.product_id,
  p.name as product_name,
  sp.ideal_qty,
  coalesce(atual.qty, 0) as current_qty,
  greatest(sp.ideal_qty - coalesce(atual.qty, 0), 0) as needed_qty,
  sp.unit_of_measure,
  -- colunas novas entram no fim para que o create or replace continue funcionando
  p.responsible,
  sp.priority,
  sp.frequency
from public.standard_plans sp
join public.showcase_slots s on s.code = sp.slot_code
join public.products p on p.id = sp.product_id
left join lateral (
  select coalesce(sum(si.current_qty), 0)::integer as qty
  from public.slot_items si
  where si.slot_code = sp.slot_code
    and si.product_id = sp.product_id
) as atual on true;

-- As visões devem respeitar o RLS de quem consulta.
-- O bloco abaixo é ignorado em versões do Postgres anteriores à 15.
do $$
begin
  execute 'alter view public.showcase_status set (security_invoker = true)';
  execute 'alter view public.production_needs set (security_invoker = true)';
exception
  when others then null;
end;
$$;


-- ---------------------------------------------------------------------
-- 13. Row Level Security
--
-- ATENÇÃO: o app roda sem tela de login, então as políticas abaixo
-- liberam leitura e escrita para a chave anon. Qualquer pessoa com essa
-- chave consegue ler e alterar os dados. Quando você adicionar login no
-- app, troque `to anon, authenticated` por `to authenticated` em todas
-- as políticas e rode o script de novo.
-- ---------------------------------------------------------------------
alter table public.units              enable row level security;
alter table public.products           enable row level security;
alter table public.showcase_slots     enable row level security;
alter table public.slot_items         enable row level security;
alter table public.standard_plans     enable row level security;
alter table public.sale_records       enable row level security;
alter table public.loss_records       enable row level security;
alter table public.production_records enable row level security;
alter table public.separated_products enable row level security;

do $$
declare
  t text;
begin
  foreach t in array array[
    'units', 'products', 'showcase_slots', 'slot_items',
    'standard_plans', 'sale_records', 'loss_records',
    'production_records', 'separated_products'
  ]
  loop
    execute format('drop policy if exists %I on public.%I', t || '_full_access', t);
    execute format(
      'create policy %I on public.%I for all to anon, authenticated using (true) with check (true)',
      t || '_full_access', t
    );
  end loop;
end;
$$;


-- ---------------------------------------------------------------------
-- 14. Permissões
-- ---------------------------------------------------------------------
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on all tables in schema public to anon, authenticated;
grant select on public.showcase_status, public.production_needs to anon, authenticated;

alter default privileges in schema public
  grant select, insert, update, delete on tables to anon, authenticated;
