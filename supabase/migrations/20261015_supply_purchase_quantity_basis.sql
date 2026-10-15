-- Diferenciar quantidades gravadas na unidade interna daquelas lançadas na unidade comercial.
-- Nenhuma quantidade nem valor pago é alterado.
alter table public.supply_purchases
 add column if not exists quantity_basis text not null default 'base';
alter table public.supply_purchases
 drop constraint if exists supply_purchases_quantity_basis_check;
alter table public.supply_purchases
 add constraint supply_purchases_quantity_basis_check
 check (quantity_basis in ('base','purchase','review'));
comment on column public.supply_purchases.quantity_basis is
 'base: qty já em g/ml/un internos; purchase: qty na unidade comercial e exige conversão específica; review: unidade ainda não reconciliada.';

update public.supply_purchases sp set quantity_basis='purchase'
from public.supplies s
where sp.supply_id=s.id and s.unit='g'
 and sp.qty>0 and sp.qty<100
 and (sp.purchase_unit in ('kg','un') or sp.purchase_unit like 'pack:%')
 and sp.quantity_basis='base';
