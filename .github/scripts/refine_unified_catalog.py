from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

s, n = re.subn(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-03-cadastro-unificado-2" />', s, count=1)
if n != 1:
    raise SystemExit('version marker not found')

repls = [
("""        separatedProducts,
        onAddProduct,""", """        separatedProducts,
        currentUnit,
        onAddProduct,"""),
("""          ...separatedProducts.map((x) => ({ value: `revenda:${x.id}`, label: x.productName || x.name, hint: 'Revenda' }))""", """          ...separatedProducts.filter((x) => !currentUnit || x.unit === currentUnit).map((x) => ({ value: `revenda:${x.id}`, label: x.productName || x.name, hint: 'Revenda' }))"""),
("""          return separatedProducts.some((x) => normalizeName(x.productName || x.name) === nome);""", """          return separatedProducts.some((x) => (!currentUnit || x.unit === currentUnit) && normalizeName(x.productName || x.name) === nome);"""),
("""              separatedProducts={separatedProducts}
              onAddProduct={onAddProduct}""", """              separatedProducts={separatedProducts}
              currentUnit={currentUnit}
              onAddProduct={onAddProduct}"""),
("""const ProductCatalogView = ({ products, supplies, separatedProducts, onAddProduct, onAddSupply, onAddSeparatedProduct, onUpdateProduct, onDeleteProduct }) => {""", """const ProductCatalogView = ({ products, supplies, separatedProducts, currentUnit, onAddProduct, onAddSupply, onAddSeparatedProduct, onUpdateProduct, onDeleteProduct }) => {"""),
("""                  separatedProducts={separatedProducts}
                  onAddProduct={handleAddProduct}""", """                  separatedProducts={separatedProducts}
                  currentUnit={currentUnit}
                  onAddProduct={handleAddProduct}"""),
("""Cadastros novos ficam em Produtos → Cadastro geral""", """Cadastros novos ficam em Cadastros → Cadastro geral"""),
("""{ id: 'produtos', label: 'Produtos', fullLabel: 'Cadastro de Produtos', icon: Icons.Package }""", """{ id: 'produtos', label: 'Cadastros', fullLabel: 'Cadastro geral', icon: Icons.Package }""")
]
for old, new in repls:
    if old not in s:
        raise SystemExit('marker not found: ' + old[:80])
    s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('ok')
