from pathlib import Path
import re

index_path = Path('index.html')
schema_path = Path('supabase/schema.sql')
index = index_path.read_text(encoding='utf-8')
schema = schema_path.read_text(encoding='utf-8')
orig_index = index
orig_schema = schema

# Version marker
index = re.sub(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-02-categorias-ddv-1" />', index, count=1)

# Exact bakery categories requested by user.
old_categories = """      const PRODUCT_CATEGORIES = [
        { value: 'salgado', label: 'Salgado' },
        { value: 'doce', label: 'Doce' },
        { value: 'sobremesa', label: 'Sobremesa' },
        { value: 'pao', label: 'Pão' },
        { value: 'bolo', label: 'Bolo' },
        { value: 'confeitaria', label: 'Confeitaria' },
        { value: 'lanche', label: 'Lanche' },
        { value: 'refeicao', label: 'Refeição' },
        { value: 'bebida', label: 'Bebida' },
        { value: 'cafeteria', label: 'Cafeteria' },
        { value: 'encomenda', label: 'Encomenda' },
        { value: 'outro', label: 'Outro' }
      ];"""
new_categories = """      const PRODUCT_CATEGORIES = [
        { value: 'doce', label: 'Doces' },
        { value: 'salgado', label: 'Salgados' },
        { value: 'sobremesa', label: 'Sobremesas' },
        { value: 'cafeteria', label: 'Cafeteria' },
        { value: 'pao', label: 'Pães' },
        { value: 'bomboniere', label: 'Bomboniere' },
        { value: 'bebida_revenda', label: 'Bebidas Revenda' },
        { value: 'outro', label: 'Outros' }
      ];"""
if old_categories not in index:
    raise SystemExit('PRODUCT_CATEGORIES marker not found')
index = index.replace(old_categories, new_categories, 1)

# Keep physical showcase mapping coherent with the three existing showcase types.
old_map = """      const SHOWCASE_BY_CATEGORY = {
        salgado: 'salgada', pao: 'salgada', lanche: 'salgada', refeicao: 'salgada',
        doce: 'doce', bolo: 'doce', confeitaria: 'doce',
        sobremesa: 'sobremesa'
      };"""
new_map = """      const SHOWCASE_BY_CATEGORY = {
        salgado: 'salgada', pao: 'salgada',
        doce: 'doce',
        sobremesa: 'sobremesa',
        cafeteria: 'doce', bomboniere: 'doce', bebida_revenda: 'salgada', outro: 'salgada'
      };"""
if old_map not in index:
    raise SystemExit('SHOWCASE_BY_CATEGORY marker not found')
index = index.replace(old_map, new_map, 1)

# Schema: replace category check with the exact requested set.
old_check = "check (category in ('salgado', 'doce', 'sobremesa', 'pao', 'bolo', 'confeitaria', 'lanche', 'refeicao', 'bebida', 'cafeteria', 'encomenda', 'outro'))"
new_check = "check (category in ('doce', 'salgado', 'sobremesa', 'cafeteria', 'pao', 'bomboniere', 'bebida_revenda', 'outro'))"
if old_check not in schema:
    raise SystemExit('schema category check marker not found')
schema = schema.replace(old_check, new_check, 1)

if index == orig_index:
    raise SystemExit('index unchanged')
if schema == orig_schema:
    raise SystemExit('schema unchanged')

index_path.write_text(index, encoding='utf-8')
schema_path.write_text(schema, encoding='utf-8')

# Safe migration for an already-populated database.
migration = Path('supabase/migrations/20260902_categorias_produtos_ddv.sql')
migration.write_text("""-- Categorias oficiais da Delícias da Vovó
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
""", encoding='utf-8')

print('categories updated')
