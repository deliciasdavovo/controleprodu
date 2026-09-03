from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old = """        // Cada produto de fabricação com custo, CMV e margem já resolvidos
        const linhasProducao = useMemo(() => products.map((p) => {
"""
new = """        // Cada produto de fabricação com custo, CMV e margem já resolvidos.
        // Itens que também existem em separatedProducts são revenda e não podem
        // aparecer novamente na aba Produção.
        const linhasProducao = useMemo(() => products
          .filter((p) => !separatedProducts.some((r) => normalizeName(r.productName) === normalizeName(p.name)))
          .map((p) => {
"""
if old not in s:
    raise SystemExit('start marker not found')
s = s.replace(old, new, 1)

old_dep = """        }), [products, recipes, recipeItems, supplies, supplyPurchases]);"""
new_dep = """        }), [products, recipes, recipeItems, supplies, supplyPurchases, separatedProducts]);"""
if old_dep not in s:
    raise SystemExit('dependency marker not found')
s = s.replace(old_dep, new_dep, 1)

p.write_text(s, encoding='utf-8')
print('CMV production now excludes resale items')
