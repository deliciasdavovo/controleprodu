-- Classificacao de materiais de obra no fluxo unico de compras.
-- Nao altera nem reclassifica registros existentes.
alter table public.supplies
  add column if not exists expense_category text not null default '';
comment on column public.supplies.expense_category is
  'Categoria de gasto: construcao, eletrica, hidraulica, pintura, acabamento, equipamentos etc. Vazio para cadastros anteriores.';

alter table public.supply_purchases
  add column if not exists purchase_purpose text not null default 'operacao';
comment on column public.supply_purchases.purchase_purpose is
  'Finalidade por item de compra: operacao, construcao_reforma ou investimento. Itens de uma mesma NF-e podem ter finalidades diferentes.';

create index if not exists supplies_expense_category_idx
  on public.supplies (expense_category);
create index if not exists supply_purchases_purpose_date_idx
  on public.supply_purchases (purchase_purpose, purchase_date desc);

-- Classificacao recomendada no campo supplies.supply_class (texto livre):
-- 'material_obra' para material de construcao e 'imobilizado' para bens duraveis.
-- Essas classes nao devem entrar em fichas tecnicas/CMV automaticamente.
-- O app precisa expor esses campos e preservar a classificacao na importacao XML.
