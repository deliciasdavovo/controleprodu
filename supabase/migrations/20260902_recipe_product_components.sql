-- Delícias da Vovó — produto fabricado como componente de outra ficha
-- Rode uma vez no Supabase > SQL Editor.

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

create index if not exists recipe_items_component_product_idx
  on public.recipe_items (component_product_id);
