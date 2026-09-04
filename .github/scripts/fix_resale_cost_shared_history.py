from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-04-cmv-revenda-historico-1" />',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('version marker not found')

if 'const custoRevendaComHistoricoCompartilhado' in s:
    raise SystemExit('shared resale helper already present')

start = s.index('      const custoRevenda = (item, purchases) => {')
end = s.index('\n      };', start) + len('\n      };')

helper = r'''

      // Revendas novas usam resale_purchases. Dados antigos/importados podem
      // ter a compra no mesmo item de supplies/supply_purchases. O CMV usa
      // primeiro a compra própria da revenda e só então reaproveita esse
      // histórico, convertendo a unidade quando necessário.
      const custoRevendaComHistoricoCompartilhado = (
        item,
        resalePurchases,
        supplies,
        supplyPurchases
      ) => {
        const direto = custoRevenda(item, resalePurchases);
        if (direto > 0) return direto;

        const insumo = (supplies || []).find(
          (s) => normalizeName(s.name) === normalizeName(item.productName)
        );
        if (!insumo) return 0;

        const custoBase = custoUnitarioInsumo(insumo.id, supplyPurchases);
        if (!(custoBase > 0)) return 0;

        const base = String(insumo.unit || 'un');
        const venda = String(item.priceUnit || item.unitOfMeasure || 'un');

        if (base === venda) return custoBase;
        if (base === 'g' && venda === 'kg') return custoBase * 1000;
        if (base === 'kg' && venda === 'g') return custoBase / 1000;
        if (base === 'ml' && venda === 'L') return custoBase * 1000;
        if (base === 'L' && venda === 'ml') return custoBase / 1000;

        const alt = String(insumo.variationUnit || '');
        const fator = Number(insumo.variationFactor) || 0;
        if (fator > 0 && alt) {
          // Base diferente de un: 1 unidade alternativa = fator unidades-base.
          if (base !== 'un' && alt === venda) return custoBase * fator;

          // Base un: 1 un = fator unidades alternativas.
          if (base === 'un') {
            if (alt === venda) return custoBase / fator;
            if (alt === 'g' && venda === 'kg') return (custoBase / fator) * 1000;
            if (alt === 'kg' && venda === 'g') return (custoBase / fator) / 1000;
            if (alt === 'ml' && venda === 'L') return (custoBase / fator) * 1000;
            if (alt === 'L' && venda === 'ml') return (custoBase / fator) / 1000;
          }
        }

        return 0;
      };'''

s = s[:end] + helper + s[end:]

cmv_old = '            const custo = custoRevenda(item, resalePurchases);'
cmv_new = '''            const custo = custoRevendaComHistoricoCompartilhado(
              item,
              resalePurchases,
              supplies,
              supplyPurchases
            );'''
if cmv_old not in s:
    raise SystemExit('CMV resale cost marker not found')
s = s.replace(cmv_old, cmv_new, 1)

# Atualiza a lista de dependências do useMemo da revenda sem depender da
# formatação exata do fechamento.
rev_start = s.index('        const linhasRevenda = useMemo(')
rev_end = s.index('        const placar = useMemo(', rev_start)
segment = s[rev_start:rev_end]
last_resale = segment.rfind('resalePurchases')
if last_resale < 0:
    raise SystemExit('resalePurchases dependency not found')
left = segment.rfind('[', 0, last_resale)
right = segment.find(']', last_resale)
if left < 0 or right < 0:
    raise SystemExit('CMV dependency array not found')
dep_text = segment[left + 1:right]
if 'separatedProducts' not in dep_text or 'currentUnit' not in dep_text:
    raise SystemExit(f'unexpected CMV dependency array: {dep_text!r}')
deps = [x.strip() for x in dep_text.split(',') if x.strip()]
for wanted in ['supplies', 'supplyPurchases']:
    if wanted not in deps:
        deps.append(wanted)
segment = segment[:left + 1] + ', '.join(deps) + segment[right:]
s = s[:rev_start] + segment + s[rev_end:]

# Mantém a mesma regra nos pontos da tela unificada que exibem custo da
# revenda, quando esses padrões existirem na versão atual.
s = s.replace(
    'const custoDaRevenda = custoRevenda(rev, resalePurchases);',
    'const custoDaRevenda = custoRevendaComHistoricoCompartilhado(rev, resalePurchases, supplies, supplyPurchases);'
)
s = s.replace(
    'custo: custoRevenda(x, resalePurchases)',
    'custo: custoRevendaComHistoricoCompartilhado(x, resalePurchases, supplies, supplyPurchases)'
)

p.write_text(s, encoding='utf-8')
print('shared resale purchase history fallback enabled')
