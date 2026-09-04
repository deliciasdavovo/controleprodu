from pathlib import Path

s = Path('index.html').read_text(encoding='utf-8')
lines = s.splitlines()
keywords = [
    'Vitrine', 'vitrine', 'confer', 'lote', 'validade',
    'production_records', 'sale_records', 'loss_records',
    'vitrine_padrao', 'shelfLife', 'currentUnit'
]

hits = []
for i, line in enumerate(lines, start=1):
    if any(k in line for k in keywords):
        hits.append(i)

# Agrupa janelas próximas para não gerar um arquivo gigante.
ranges = []
for i in hits:
    a, b = max(1, i-8), min(len(lines), i+16)
    if ranges and a <= ranges[-1][1] + 3:
        ranges[-1] = (ranges[-1][0], max(ranges[-1][1], b))
    else:
        ranges.append((a,b))

out = []
for a,b in ranges[:80]:
    out.append(f'===== LINES {a}-{b} =====')
    for n in range(a,b+1):
        out.append(f'{n}: {lines[n-1]}')
    out.append('')

Path('.github/vitrine_context.txt').write_text('\n'.join(out), encoding='utf-8')
print(f'wrote {len(ranges[:80])} ranges, {len(out)} lines')
