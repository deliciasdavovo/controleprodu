-- Libera as categorias dos produtos de produção própria.
--
-- A lista fechada (doce, salgado, sobremesa, cafeteria, pao, bomboniere,
-- bebida_revenda, outro) recusava a categoria "chapa" e qualquer categoria
-- personalizada criada no Banco de Dados ("violates check constraint
-- products_category_check"). Insumos e revenda já tiveram a lista liberada em
-- 20261002_categorias_personalizadas_insumos_revenda.sql; aqui vale o mesmo
-- para produtos. Continua proibido gravar categoria vazia.
alter table public.products
  drop constraint if exists products_category_check;

alter table public.products
  drop constraint if exists products_category_not_blank;

alter table public.products
  add constraint products_category_not_blank
  check (length(trim(category)) > 0);
