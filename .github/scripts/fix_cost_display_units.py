from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old_version = '<meta name="app-version" content="2026-09-04-ficha-tipo-picker-largo-1" />'
new_version = '<meta name="app-version" content="2026-09-05-custo-kg-litro-unidade-1" />'
if old_version in s:
    s = s.replace(old_version, new_version, 1)
elif new_version not in s:
    raise SystemExit('app version marker not found')

old = "{c.custoUnit > 0 ? `${formatCurrencyBR(c.custoUnit)}/${c.unidade}` : '—'}"
new = "{c.custoUnit > 0 ? formatPrecoInsumo(c.custoUnit, c.unidade) : '—'}"
count = s.count(old)
if count != 2:
    raise SystemExit(f'expected 2 raw history cost displays, found {count}')
s = s.replace(old, new)

# Segurança: o helper comercial deve continuar convertendo base pequena para
# a unidade que a loja realmente usa para comparar preço.
for marker in [
    "if (unidade === 'g') return { valor: (Number(custoUnit) || 0) * 1000, label: 'kg' };",
    "if (unidade === 'ml') return { valor: (Number(custoUnit) || 0) * 1000, label: 'L' };",
    "2026-09-05-custo-kg-litro-unidade-1"
]:
    if marker not in s:
        raise SystemExit(f'missing marker: {marker}')

p.write_text(s, encoding='utf-8')
