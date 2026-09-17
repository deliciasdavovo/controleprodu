-- Preserva o formato de caixa/pacote/fardo em cada compra de insumo e mantém
-- o custo resumido da revenda sincronizado com sua compra mais recente.

alter table if exists public.supply_purchases
  add column if not exists purchase_unit text not null default '';

comment on column public.supply_purchases.purchase_unit is
  'Formato original da compra. Vazio = unidade base; pack:tipo:quantidade preserva caixa, pacote ou fardo daquela nota.';

create or replace function public.sync_separated_product_cost_from_purchase()
returns trigger
language plpgsql
set search_path = public
as $$
declare
  target_id uuid;
  old_target_id uuid;
begin
  target_id := case when tg_op = 'DELETE' then old.separated_product_id else new.separated_product_id end;
  old_target_id := case when tg_op = 'UPDATE' then old.separated_product_id else null end;

  update public.separated_products p
  set cost = coalesce((
    select rp.cost / nullif(
      case
        when (case when rp.purchase_unit like 'pack:%' then 'un' else rp.purchase_unit end) = p.price_unit
          then rp.qty
        when rp.purchase_unit = 'g' and p.price_unit = 'kg' then rp.qty / 1000
        when rp.purchase_unit = 'kg' and p.price_unit = 'g' then rp.qty * 1000
        else rp.qty
      end,
      0
    )
    from public.resale_purchases rp
    where rp.separated_product_id = target_id
      and rp.qty > 0
      and rp.cost > 0
    order by rp.purchase_date desc nulls last, rp.created_at desc
    limit 1
  ), 0)
  where p.id = target_id;

  if old_target_id is not null and old_target_id <> target_id then
    update public.separated_products p
    set cost = coalesce((
      select rp.cost / nullif(
        case
          when (case when rp.purchase_unit like 'pack:%' then 'un' else rp.purchase_unit end) = p.price_unit
            then rp.qty
          when rp.purchase_unit = 'g' and p.price_unit = 'kg' then rp.qty / 1000
          when rp.purchase_unit = 'kg' and p.price_unit = 'g' then rp.qty * 1000
          else rp.qty
        end,
        0
      )
      from public.resale_purchases rp
      where rp.separated_product_id = old_target_id
        and rp.qty > 0
        and rp.cost > 0
      order by rp.purchase_date desc nulls last, rp.created_at desc
      limit 1
    ), 0)
    where p.id = old_target_id;
  end if;

  return case when tg_op = 'DELETE' then old else new end;
end;
$$;

revoke execute on function public.sync_separated_product_cost_from_purchase() from public, anon, authenticated;

drop trigger if exists resale_purchases_sync_cost on public.resale_purchases;
create trigger resale_purchases_sync_cost
  after insert or update or delete on public.resale_purchases
  for each row execute function public.sync_separated_product_cost_from_purchase();

-- Corrige o resumo já existente sem alterar o histórico de compras.
update public.separated_products p
set cost = (
  select rp.cost / nullif(
    case
      when (case when rp.purchase_unit like 'pack:%' then 'un' else rp.purchase_unit end) = p.price_unit
        then rp.qty
      when rp.purchase_unit = 'g' and p.price_unit = 'kg' then rp.qty / 1000
      when rp.purchase_unit = 'kg' and p.price_unit = 'g' then rp.qty * 1000
      else rp.qty
    end,
    0
  ) as unit_cost
  from public.resale_purchases rp
  where rp.separated_product_id = p.id
    and rp.qty > 0
    and rp.cost > 0
  order by rp.purchase_date desc nulls last, rp.created_at desc
  limit 1
)
where exists (
  select 1
  from public.resale_purchases rp
  where rp.separated_product_id = p.id
    and rp.qty > 0
    and rp.cost > 0
);

notify pgrst, 'reload schema';
