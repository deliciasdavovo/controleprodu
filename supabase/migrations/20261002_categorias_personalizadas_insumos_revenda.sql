-- Libera categorias personalizadas no Banco de dados.
-- Mantém os valores existentes e remove apenas as listas fechadas.
alter table public.supplies
  drop constraint if exists supplies_class_check;

alter table public.separated_products
  drop constraint if exists separated_products_category_check;
