from pathlib import Path

s = Path('index.html').read_text(encoding='utf-8')
lines = s.splitlines()
terms = [
    'const UnifiedCatalogEntry', 'const SuppliesRecipesView', 'Cadastro + compra',
    'Também é revenda?', 'Equivalência / variação', 'ProductCatalogView',
    'onChangeCatalogType', 'const handleChangeCatalogType', 'onSetSupplyResale',
    "activeTab === 'produtos'", "activeTab === 'insumos'"
]

hits=[]
for i,line in enumerate(lines,1):
    if any(t in line for t in terms): hits.append(i)

ranges=[]
for i in hits:
    a=max(1,i-80); b=min(len(lines),i+220)
    if ranges and a <= ranges[-1][1]+20:
        ranges[-1]=(ranges[-1][0],max(ranges[-1][1],b))
    else:
        ranges.append((a,b))

out=[]
for a,b in ranges:
    out.append(f'===== LINES {a}-{b} =====')
    for n in range(a,b+1): out.append(f'{n}: {lines[n-1]}')
    out.append('')
Path('.github/catalog_context.txt').write_text('\n'.join(out),encoding='utf-8')
print('ranges', ranges)
