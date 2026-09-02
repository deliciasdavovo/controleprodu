-- Categorias oficiais da Delícias da Vovó
-- Converte categorias antigas antes de restringir os valores permitidos.

update public.products
set category = case category
  when 'bolo' then 'doce'
  when 'confeitaria' then 'doce'
  when 'lanche' then 'salgado'
  when 'refeicao' then 'salgado'
  when 'bebida' then 'bebida_revenda'
  when 'encomenda' then 'outro'
  else category
end
where category in ('bolo', 'confeitaria', 'lanche', 'refeicao', 'bebida', 'encomenda');

alter table public.products
  drop constraint if exists products_category_check;

alter table public.products
  add constraint products_category_check
  check (category in (
    'doce',
    'salgado',
    'sobremesa',
    'cafeteria',
    'pao',
    'bomboniere',
    'bebida_revenda',
    'outro'
  ));
