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
    check (category in ('doce', 'salgado', 'sobremesa', 'cafeteria', 'pao', 'bomboniere', 'bebida_revenda', 'outro')),
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
comment on column public.products.is_active is 'Sim = participa da vitrine/produção. Não = permanece no catálogo apenas para CMV e ficha técnica.';


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

-- Quantidade mínima do item naquele dia: é ela que decide quando o pedido de
-- produção chama o item. Antes o mínimo era uma porcentagem da letra A–D
-- (A 50%, B 30%, C 20%, D 10% do padrão), calculada só no app. Agora é um
-- número digitado por item e por dia da semana.
--
-- O bloco abaixo só age quando a coluna está entrando: bancos que já a têm
-- ficam intocados, para que rodar o script de novo não apague um mínimo que a
-- loja digitou. Na entrada, cada linha recebe o mínimo que a conta antiga
-- daria, para o pedido não mudar de comportamento de um dia para o outro.
do $$
begin
  if not exists (
    select 1 from information_schema.columns
    where table_schema = 'public'
      and table_name = 'standard_plans'
      and column_name = 'min_qty'
  ) then
    alter table public.standard_plans add column min_qty integer not null default 0;

    update public.standard_plans
      set min_qty = greatest(1, ceil(ideal_qty * case priority
        when 'A' then 0.50
        when 'B' then 0.30
        when 'C' then 0.20
        else 0.10
      end))::integer;
  end if;
end;
$$;

alter table public.standard_plans drop constraint if exists standard_plans_min_check;
alter table public.standard_plans
  add constraint standard_plans_min_check check (min_qty >= 0);

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
  'A = não pode faltar, B = importante, C = complementar, D = extra. Etiqueta de organização: ordena e filtra as listas, não entra em nenhuma conta.';
comment on column public.standard_plans.frequency is
  'todo_dia = o item está nos sete dias; dias = só nos dias marcados na vitrine padrão.';
comment on column public.standard_plans.min_qty is
  'Quantidade mínima do item neste dia. O pedido de produção chama o item quando o estoque bom da loja fica igual ou abaixo dela. 0 = só quando acabar.';

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

-- =====================================================================
-- CMV — Custo da Mercadoria Vendida (seções 11 a 15)
--
-- O CMV nasce da compra: o preço pago no insumo vira custo por grama,
-- a ficha técnica diz quantos gramas entram no produto e o rendimento
-- diz para quantas unidades aquilo rende. Daí sai o custo de uma
-- unidade, que dividido pelo preço de venda é o CMV.
--
-- Nada aqui mexe na vitrine: são tabelas novas, ao lado das que já
-- existem. Rodar este arquivo de novo não apaga nenhum lançamento.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 11. Insumos
--
-- Tudo que é comprado para produzir: ingrediente, embalagem e material
-- de limpeza. Os três entram no CMV quando usados numa ficha técnica —
-- a classe serve para organizar a lista, não muda conta nenhuma.
--
-- A unidade é sempre a menor (g, ml ou un): é nela que o custo unitário
-- é calculado. A variação é o jeito como a loja compra ou usa o insumo
-- ("1 lata = 395 g", "1 un = 12 fatias"), para ninguém precisar
-- converter de cabeça na hora de montar a ficha.
-- ---------------------------------------------------------------------
create table if not exists public.supplies (
  id                uuid primary key default gen_random_uuid(),
  name              text not null,
  unit              text not null default 'g',
  variation_unit    text,
  variation_factor  numeric(12,3),
  supply_class      text not null default 'insumo',
  is_active         boolean not null default true,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now(),
  constraint supplies_name_unique unique (name),
  constraint supplies_unit_check check (unit in ('g', 'ml', 'un')),
  constraint supplies_class_check
    check (supply_class in ('insumo', 'embalagem', 'limpeza')),
  constraint supplies_variation_check
    check (variation_factor is null or variation_factor > 0)
);

create index if not exists supplies_class_idx on public.supplies (supply_class);

drop trigger if exists supplies_set_updated_at on public.supplies;
create trigger supplies_set_updated_at
  before update on public.supplies
  for each row execute function public.set_updated_at();

comment on table public.supplies is 'Insumos, embalagens e material de limpeza usados na produção.';
comment on column public.supplies.unit is 'Unidade base do insumo (g, ml ou un). O custo unitário é calculado nela.';
comment on column public.supplies.variation_factor is
  'Quanto vale uma variação na unidade base. Base g/ml: 1 variação = N base (1 lata = 395 g). Base un: 1 un = N variações (1 un = 12 fatias).';


-- ---------------------------------------------------------------------
-- 12. Compras de insumo
--
-- Cada compra fica guardada, não só a última. O custo do insumo é
-- sempre o da compra mais recente — é o que a loja vai pagar para
-- repor —, e o histórico é o que deixa a tela de fornecedores mostrar
-- se o preço subiu ou caiu e com quem sai mais barato.
-- ---------------------------------------------------------------------
create table if not exists public.supply_purchases (
  id             uuid primary key default gen_random_uuid(),
  supply_id      uuid not null references public.supplies (id) on delete cascade,
  supplier       text not null default '',
  purchase_date  date,
  qty            numeric(12,3) not null default 0,
  cost           numeric(10,2) not null default 0,
  created_at     timestamptz not null default now(),
  constraint supply_purchases_qty_check check (qty >= 0),
  constraint supply_purchases_cost_check check (cost >= 0)
);

create index if not exists supply_purchases_supply_idx
  on public.supply_purchases (supply_id, purchase_date desc);

comment on table public.supply_purchases is 'Histórico de compras de cada insumo, com fornecedor e data.';
comment on column public.supply_purchases.qty is 'Quantidade comprada, na unidade base do insumo.';


-- ---------------------------------------------------------------------
-- 13. Fichas técnicas
--
-- Uma ficha por produto: o que entra nele e quanto aquilo rende. O peso
-- por unidade só é preciso em produto vendido por quilo — é ele que
-- transforma o custo da fornada em custo por quilo.
-- ---------------------------------------------------------------------
create table if not exists public.recipes (
  id               uuid primary key default gen_random_uuid(),
  product_id       uuid not null references public.products (id) on delete cascade,
  yield_qty        numeric(12,3) not null default 1,
  yield_unit       text not null default 'un',
  weight_per_unit  numeric(12,3),
  notes            text not null default '',
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  constraint recipes_yield_check check (yield_qty > 0),
  constraint recipes_weight_check check (weight_per_unit is null or weight_per_unit > 0),
  constraint recipes_product_unique unique (product_id)
);

drop trigger if exists recipes_set_updated_at on public.recipes;
create trigger recipes_set_updated_at
  before update on public.recipes
  for each row execute function public.set_updated_at();

comment on table public.recipes is 'Ficha técnica do produto: rendimento da receita.';
comment on column public.recipes.yield_qty is 'Quantas unidades a receita inteira rende.';
comment on column public.recipes.weight_per_unit is 'Peso de uma unidade em gramas. Só usado em produto vendido por quilo.';


-- ---------------------------------------------------------------------
-- 14. Itens da ficha técnica
--
-- Cada linha é um componente da receita: ou um insumo comprado, ou outro
-- produto fabricado pela própria casa. usage_unit vazio significa que a
-- quantidade está na unidade base/origem; preenchido, o app converte na conta.
-- ---------------------------------------------------------------------
create table if not exists public.recipe_items (
  id                    uuid primary key default gen_random_uuid(),
  recipe_id             uuid not null references public.recipes (id) on delete cascade,
  supply_id             uuid references public.supplies (id) on delete restrict,
  component_product_id  uuid references public.products (id) on delete restrict,
  qty                   numeric(12,3) not null default 0,
  usage_unit            text not null default '',
  created_at            timestamptz not null default now(),
  constraint recipe_items_qty_check check (qty >= 0),
  constraint recipe_items_source_check check (
    (supply_id is not null and component_product_id is null)
    or (supply_id is null and component_product_id is not null)
  )
);

-- Bancos anteriores tinham supply_id obrigatório. Agora uma linha pode vir de
-- um produto fabricado pela própria casa, mas nunca das duas origens ao mesmo tempo.
alter table public.recipe_items
  add column if not exists component_product_id uuid references public.products (id) on delete restrict;
alter table public.recipe_items
  alter column supply_id drop not null;
alter table public.recipe_items
  drop constraint if exists recipe_items_source_check;
alter table public.recipe_items
  add constraint recipe_items_source_check check (
    (supply_id is not null and component_product_id is null)
    or (supply_id is null and component_product_id is not null)
  );

create index if not exists recipe_items_recipe_idx on public.recipe_items (recipe_id);
create index if not exists recipe_items_supply_idx on public.recipe_items (supply_id);
create index if not exists recipe_items_component_product_idx on public.recipe_items (component_product_id);

comment on table public.recipe_items is 'Os insumos de cada ficha técnica, com a quantidade usada.';
comment on column public.recipe_items.usage_unit is 'Vazio = quantidade na unidade base do insumo. Preenchido = na variação dele.';


-- ---------------------------------------------------------------------
-- 15. Compras de revenda
--
-- O mesmo histórico dos insumos, para os itens de fora da vitrine
-- (bebida, cafeteria). Aqui a compra pode vir numa unidade diferente da
-- de venda — compra-se o fardo, vende-se a lata —, então a unidade da
-- compra fica gravada junto.
-- ---------------------------------------------------------------------
create table if not exists public.resale_purchases (
  id                    uuid primary key default gen_random_uuid(),
  separated_product_id  uuid not null references public.separated_products (id) on delete cascade,
  supplier              text not null default '',
  purchase_date         date,
  qty                   numeric(12,3) not null default 0,
  purchase_unit         text not null default 'un',
  cost                  numeric(10,2) not null default 0,
  created_at            timestamptz not null default now(),
  constraint resale_purchases_qty_check check (qty >= 0),
  constraint resale_purchases_cost_check check (cost >= 0)
);

create index if not exists resale_purchases_product_idx
  on public.resale_purchases (separated_product_id, purchase_date desc);

comment on table public.resale_purchases is 'Histórico de compras dos itens de revenda, com fornecedor e data.';


-- ---------------------------------------------------------------------
-- Colunas do CMV nas tabelas que já existiam
--
-- price_unit diz se o preço cadastrado é por unidade ou por quilo — sem
-- isso o CMV de um produto vendido a peso sai errado por mil.
-- manual_cost é a saída para o produto que ainda não tem ficha técnica:
-- a loja digita o custo que conhece e já enxerga o CMV dele.
-- ---------------------------------------------------------------------
alter table public.products
  add column if not exists price_unit text not null default 'un';
alter table public.products
  add column if not exists manual_cost numeric(10,2) not null default 0;

alter table public.products drop constraint if exists products_price_unit_check;
alter table public.products
  add constraint products_price_unit_check check (price_unit in ('un', 'kg'));
alter table public.products drop constraint if exists products_manual_cost_check;
alter table public.products
  add constraint products_manual_cost_check check (manual_cost >= 0);

comment on column public.products.price_unit is 'Se o preço é por unidade (un) ou por quilo (kg).';
comment on column public.products.manual_cost is 'Custo digitado à mão, usado no CMV enquanto o produto não tem ficha técnica.';

alter table public.separated_products
  add column if not exists price_unit text not null default 'un';
alter table public.separated_products
  add column if not exists cost numeric(10,2) not null default 0;

alter table public.separated_products drop constraint if exists separated_products_price_unit_check;
alter table public.separated_products
  add constraint separated_products_price_unit_check check (price_unit in ('un', 'kg', 'g'));
alter table public.separated_products drop constraint if exists separated_products_cost_check;
alter table public.separated_products
  add constraint separated_products_cost_check check (cost >= 0);

comment on column public.separated_products.price_unit is 'Unidade em que o item é vendido (un, kg ou g).';
comment on column public.separated_products.cost is 'Custo por unidade de venda. Sai sozinho da última compra registrada.';



-- ---------------------------------------------------------------------
-- 16. Dados iniciais
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
-- 17. Visões de apoio
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
  sp.frequency,
  sp.min_qty,
  (coalesce(atual.qty, 0) <= sp.min_qty) as below_min
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
-- 18. Row Level Security
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
alter table public.supplies           enable row level security;
alter table public.supply_purchases   enable row level security;
alter table public.recipes            enable row level security;
alter table public.recipe_items       enable row level security;
alter table public.resale_purchases   enable row level security;

do $$
declare
  t text;
begin
  foreach t in array array[
    'units', 'products', 'showcase_slots', 'slot_items',
    'standard_plans', 'sale_records', 'loss_records',
    'production_records', 'separated_products',
    'supplies', 'supply_purchases', 'recipes', 'recipe_items', 'resale_purchases'
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
-- 19. Permissões
-- ---------------------------------------------------------------------
grant usage on schema public to anon, authenticated;
grant select, insert, update, delete on all tables in schema public to anon, authenticated;
grant select on public.showcase_status, public.production_needs to anon, authenticated;

alter default privileges in schema public
  grant select, insert, update, delete on tables to anon, authenticated;
