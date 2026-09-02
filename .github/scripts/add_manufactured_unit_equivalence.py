from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'Marker not found: {label}')
    s = s.replace(old, new, 1)

s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-02-fabricacao-equivalencia-unidade-1" />',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('app version marker not found')

replace_once(
"""      const converterQtdComponente = (qtd, origem, destino) => {
        const n = Number(qtd) || 0;
        const de = origem || destino || 'un';
        const para = destino || de;
        if (!n || de === para) return n;
        if (de === 'kg' && para === 'g') return n * 1000;
        if (de === 'g' && para === 'kg') return n / 1000;
        if (de === 'L' && para === 'ml') return n * 1000;
        if (de === 'ml' && para === 'L') return n / 1000;
        return n;
      };

      const unidadesDeComponente = (unidade) => {
        const u = unidade || 'un';
        if (u === 'g') return ['g', 'kg'];
        if (u === 'kg') return ['kg', 'g'];
        if (u === 'ml') return ['ml', 'L'];
        if (u === 'L') return ['L', 'ml'];
        return [u];
      };""",
"""      const converterQtdComponente = (qtd, origem, destino, pesoUnidadeG = 0) => {
        const n = Number(qtd) || 0;
        const de = origem || destino || 'un';
        const para = destino || de;
        const pesoG = Number(pesoUnidadeG) || 0;
        if (!n || de === para) return n;
        if (de === 'kg' && para === 'g') return n * 1000;
        if (de === 'g' && para === 'kg') return n / 1000;
        if (de === 'L' && para === 'ml') return n * 1000;
        if (de === 'ml' && para === 'L') return n / 1000;

        // Produto da casa vendido por kg também pode ser usado por unidade em
        // outra ficha quando existe uma equivalência, ex.: 1 chipa = 50 g.
        if (pesoG > 0 && de === 'un' && para === 'g') return n * pesoG;
        if (pesoG > 0 && de === 'un' && para === 'kg') return (n * pesoG) / 1000;
        if (pesoG > 0 && de === 'g' && para === 'un') return n / pesoG;
        if (pesoG > 0 && de === 'kg' && para === 'un') return (n * 1000) / pesoG;

        // Nunca trate 1 unidade como 1 kg por falta da equivalência.
        if (de === 'un' || para === 'un') return 0;
        return n;
      };

      const unidadesDeComponente = (unidade, pesoUnidadeG = 0) => {
        const u = unidade || 'un';
        if (u === 'g') return ['g', 'kg'];
        if (u === 'kg') return Number(pesoUnidadeG) > 0 ? ['kg', 'g', 'un'] : ['kg', 'g'];
        if (u === 'ml') return ['ml', 'L'];
        if (u === 'L') return ['L', 'ml'];
        return [u];
      };""",
'component conversion helpers'
)

replace_once(
"""          const qtd = converterQtdComponente(
            item.qty,
            item.usageUnit || unidadeSaida,
            unidadeSaida
          );""",
"""          const qtd = converterQtdComponente(
            item.qty,
            item.usageUnit || unidadeSaida,
            unidadeSaida,
            fichaComponente.weightPerUnit
          );""",
'component cost conversion'
)

replace_once(
"""          if (unidadeVenda === 'kg' && Number(ficha.weightPerUnit) > 0) {
            const kg = ((Number(ficha.yieldQty) || 1) * Number(ficha.weightPerUnit)) / 1000;
            onUpdateRecipe({ yieldQty: kg || 1, yieldUnit: 'kg', weightPerUnit: null });
            return;
          }
          onUpdateRecipe({ yieldUnit: unidadeVenda, weightPerUnit: unidadeVenda === 'kg' ? null : ficha.weightPerUnit });""",
"""          if (unidadeVenda === 'kg' && Number(ficha.weightPerUnit) > 0) {
            const kg = ((Number(ficha.yieldQty) || 1) * Number(ficha.weightPerUnit)) / 1000;
            // O peso por unidade continua útil: agora ele é a equivalência para
            // usar este produto vendido por kg como "un" em outra ficha.
            onUpdateRecipe({ yieldQty: kg || 1, yieldUnit: 'kg', weightPerUnit: ficha.weightPerUnit });
            return;
          }
          onUpdateRecipe({ yieldUnit: unidadeVenda, weightPerUnit: ficha.weightPerUnit });""",
'preserve manufactured unit weight'
)

replace_once(
"""                      yieldQty: Number(e.target.value) || 1,
                      yieldUnit: unidadeVenda,
                      weightPerUnit: unidadeVenda === 'kg' ? null : ficha?.weightPerUnit
                    })}""",
"""                      yieldQty: Number(e.target.value) || 1,
                      yieldUnit: unidadeVenda,
                      weightPerUnit: ficha?.weightPerUnit
                    })}""",
'preserve equivalence on yield edit'
)

replace_once(
"""                <p className=\"t-nano mt-1.5\">
                  {unidadeVenda === 'kg'
                    ? 'Produto vendido por kg · informe o peso total que a receita rende.'
                    : 'Produto vendido por unidade · informe quantas unidades a receita rende.'}
                </p>
              </div>""",
"""                <p className=\"t-nano mt-1.5\">
                  {unidadeVenda === 'kg'
                    ? 'Produto vendido por kg · informe o peso total que a receita rende.'
                    : 'Produto vendido por unidade · informe quantas unidades a receita rende.'}
                </p>

                {unidadeVenda === 'kg' && (
                  <div className=\"mt-3 pt-3 border-t hairline\">
                    <label className=\"t-caption block mb-1\">Equivalência para usar por unidade</label>
                    <div className=\"flex items-center gap-2\">
                      <span className=\"t-callout font-semibold whitespace-nowrap\">1 un =</span>
                      <input
                        type=\"number\"
                        min=\"0\"
                        step=\"0.1\"
                        value={ficha?.weightPerUnit || ''}
                        onChange={(e) => onUpdateRecipe({ weightPerUnit: Number(e.target.value) || null })}
                        placeholder=\"ex: 50\"
                        title=\"Peso em gramas de uma unidade deste produto\"
                        className=\"field field-sm text-right tnum no-spin w-24\"
                      />
                      <span className=\"t-callout font-semibold\">g</span>
                    </div>
                    <p className=\"t-nano mt-1.5\">Opcional · permite usar este produto como un em outra ficha técnica.</p>
                  </div>
                )}
              </div>""",
'equivalence field UI'
)

replace_once(
"""              const unidadeP = fichaP?.yieldUnit || 'un';
              const custoP = fichaP && rendimentoP > 0 ? fichaP.custo / rendimentoP : 0;
              return {
                value: `produto:${p.id}`,
                label: p.name,
                hint: custoP > 0
                  ? `Fabricação própria · ${formatCurrencyBR(custoP)}/${unidadeP}`
                  : 'Fabricação própria · sem ficha/custo'
              };""",
"""              const unidadeP = fichaP?.yieldUnit || 'un';
              const custoP = fichaP && rendimentoP > 0 ? fichaP.custo / rendimentoP : 0;
              const pesoUnP = Number(fichaP?.weightPerUnit) || 0;
              const equivalenciaP = unidadeP === 'kg' && pesoUnP > 0 ? ` · 1 un = ${pesoUnP} g` : '';
              return {
                value: `produto:${p.id}`,
                label: p.name,
                hint: custoP > 0
                  ? `Fabricação própria · ${formatCurrencyBR(custoP)}/${unidadeP}${equivalenciaP}`
                  : `Fabricação própria · sem ficha/custo${equivalenciaP}`
              };""",
'manufactured picker hint'
)

replace_once(
"""                      : unidadesDeComponente(unidadeBase);""",
"""                      : unidadesDeComponente(unidadeBase, componentFicha?.weightPerUnit);""",
'manufactured usage units'
)

p.write_text(s, encoding='utf-8')
print('ok')
