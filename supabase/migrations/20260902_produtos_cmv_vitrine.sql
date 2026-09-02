-- Produtos: categoria comercial independente da presença na vitrine
alter table public.products drop constraint if exists products_category_check;
alter table public.products
  add constraint products_category_check
  check (category in ('salgado', 'doce', 'sobremesa', 'pao', 'bolo', 'confeitaria', 'lanche', 'refeicao', 'bebida', 'cafeteria', 'encomenda', 'outro'));

comment on column public.products.is_active is
  'Sim = participa da vitrine/produção. Não = permanece no catálogo apenas para CMV e ficha técnica.';
