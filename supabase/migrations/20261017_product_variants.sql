-- Controle Produ: variações de produtos (aplicada no Supabase em 2026-10-17)
-- Produto principal e cada sabor continuam sendo registros em products.
alter table public.products
  add column if not exists parent_product_id uuid references public.products(id) on delete restrict,
  add column if not exists variant_name text,
  add column if not exists variant_sort_order integer not null default 0;
create index if not exists products_parent_product_id_idx on public.products(parent_product_id);
create unique index if not exists products_parent_variant_unique_idx
  on public.products(parent_product_id, lower(btrim(variant_name)))
  where parent_product_id is not null and variant_name is not null;
create or replace function public.validate_product_variant()
returns trigger language plpgsql security invoker set search_path = '' as $$
declare ancestor_parent uuid;
begin
  if new.parent_product_id is null then
    if new.variant_name is not null and btrim(new.variant_name) = '' then new.variant_name := null; end if;
    return new;
  end if;
  if new.parent_product_id = new.id then
    raise exception 'Uma variação não pode ser seu próprio produto principal';
  end if;
  if new.variant_name is null or btrim(new.variant_name) = '' then
    raise exception 'Informe o nome da variação';
  end if;
  new.variant_name := btrim(new.variant_name);
  select p.parent_product_id into ancestor_parent from public.products p where p.id = new.parent_product_id;
  if not found then raise exception 'Produto principal não encontrado'; end if;
  if ancestor_parent is not null then
    raise exception 'Uma variação não pode ser produto principal de outra variação';
  end if;
  if exists (select 1 from public.products p where p.parent_product_id = new.id) then
    raise exception 'Um produto com variações não pode virar uma variação';
  end if;
  return new;
end;
$$;
drop trigger if exists products_validate_variant on public.products;
create trigger products_validate_variant
before insert or update of parent_product_id, variant_name on public.products
for each row execute function public.validate_product_variant();
comment on column public.products.parent_product_id is 'UUID do produto principal (nulo no registro pai).';
comment on column public.products.variant_name is 'Nome do sabor ou recheio específico.';
comment on column public.products.variant_sort_order is 'Ordem na exibição do catálogo.';
alter table public.recipes
  add column if not exists inherit_parent_recipe boolean not null default false;
comment on column public.recipes.inherit_parent_recipe is 'Indica que a interface pode combinar ingredientes de base com os próprios desta receita.';
-- Campos existentes products.price, recipes.image_url e recipe_items preservados.
