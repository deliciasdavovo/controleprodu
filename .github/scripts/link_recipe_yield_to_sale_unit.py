from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'Marker not found: {label}')
    s = s.replace(old, new, 1)

replace_once(
"""      const custoPorUnidadeDeVenda = (product, ficha) => {
        if (!ficha || !(ficha.custo > 0)) return Number(product?.manualCost) || 0;
        const rendimento = Number(ficha.yieldQty) || 0;
        if (rendimento <= 0) return 0;
        if ((product?.priceUnit || 'un') === 'kg') {
          const pesoG = Number(ficha.weightPerUnit) || 0;
          if (pesoG > 0) return ficha.custo / ((rendimento * pesoG) / 1000);
        }
        return ficha.custo / rendimento;
      };""",
"""      const custoPorUnidadeDeVenda = (product, ficha) => {
        if (!ficha || !(ficha.custo > 0)) return Number(product?.manualCost) || 0;
        const rendimento = Number(ficha.yieldQty) || 0;
        if (rendimento <= 0) return 0;
        if ((product?.priceUnit || 'un') === 'kg') {
          // Ficha nova: o rendimento já é o total produzido em kg.
          if ((ficha.yieldUnit || 'un') === 'kg') return ficha.custo / rendimento;

          // Compatibilidade com fichas antigas: antes a tela guardava número
          // de unidades + peso por unidade para chegar ao rendimento em kg.
          const pesoG = Number(ficha.weightPerUnit) || 0;
          if (pesoG > 0) return ficha.custo / ((rendimento * pesoG) / 1000);
        }
        return ficha.custo / rendimento;
      };""",
'cost per sale unit')

replace_once(
"""        const itens = ficha?.itens || [];
        const custoTotal = ficha?.custo || 0;
        const rendimento = ficha?.yieldQty || 1;
        const preco = Number(produto.price) || 0;""",
"""        const itens = ficha?.itens || [];
        const custoTotal = ficha?.custo || 0;
        const rendimento = ficha?.yieldQty || 1;
        const unidadeVenda = (produto.priceUnit || 'un') === 'kg' ? 'kg' : 'un';
        const preco = Number(produto.price) || 0;

        // A unidade do rendimento pertence ao produto, não à ficha. Fichas
        // antigas podem ter ficado em "un" mesmo quando o produto era vendido
        // por kg; ao abrir, convertemos sem alterar o custo calculado.
        useEffect(() => {
          if (!ficha || ficha.yieldUnit === unidadeVenda) return;
          if (unidadeVenda === 'kg' && Number(ficha.weightPerUnit) > 0) {
            const kg = ((Number(ficha.yieldQty) || 1) * Number(ficha.weightPerUnit)) / 1000;
            onUpdateRecipe({ yieldQty: kg || 1, yieldUnit: 'kg', weightPerUnit: null });
            return;
          }
          onUpdateRecipe({ yieldUnit: unidadeVenda, weightPerUnit: unidadeVenda === 'kg' ? null : ficha.weightPerUnit });
        }, [ficha?.id, produto.priceUnit]);""",
'recipe editor yield vars')

old_block = """            {/* Rendimento e peso: o que transforma o custo da fornada em custo
                de uma unidade */}
            <div className=\"grid grid-cols-12 gap-2 sm:gap-3 items-end py-4 border-b hairline\">
              <div className=\"col-span-4 sm:col-span-2\">
                <label className=\"t-caption block mb-1\">Rende</label>
                <input
                  type=\"number\"
                  min=\"0.001\"
                  step=\"0.001\"
                  value={rendimento}
                  onChange={(e) => onUpdateRecipe({ yieldQty: Number(e.target.value) || 1 })}
                  title=\"Quantas unidades a receita inteira rende\"
                  className=\"field field-sm text-right tnum no-spin\"
                />
              </div>
              <div className=\"col-span-4 sm:col-span-2\">
                <label className=\"t-caption block mb-1\">Unidade</label>
                <input
                  type=\"text\"
                  value={ficha?.yieldUnit || 'un'}
                  onChange={(e) => onUpdateRecipe({ yieldUnit: e.target.value })}
                  placeholder=\"un\"
                  className=\"field field-sm\"
                />
              </div>
              {(produto.priceUnit || 'un') === 'kg' && (
                <div className=\"col-span-4 sm:col-span-3\">
                  <label className=\"t-caption block mb-1\">Peso da unidade (g)</label>
                  <input
                    type=\"number\"
                    min=\"0\"
                    step=\"0.1\"
                    value={ficha?.weightPerUnit || ''}
                    onChange={(e) => onUpdateRecipe({ weightPerUnit: Number(e.target.value) || null })}
                    placeholder=\"ex: 120\"
                    title=\"Sem o peso da unidade, o custo por quilo não sai\"
                    className=\"field field-sm text-right tnum no-spin\"
                  />
                </div>
              )}
              <div className=\"col-span-12 sm:col-span-5 flex flex-wrap items-center gap-4 sm:justify-end\">"""
new_block = """            {/* O rendimento usa a mesma unidade em que o produto é vendido.
                Não existe mais uma segunda unidade solta dentro da ficha. */}
            <div className=\"grid grid-cols-12 gap-2 sm:gap-3 items-end py-4 border-b hairline\">
              <div className=\"col-span-12 sm:col-span-4\">
                <label className=\"t-caption block mb-1\">Rendimento da receita</label>
                <div className=\"flex items-stretch\">
                  <input
                    type=\"number\"
                    min=\"0.001\"
                    step=\"0.001\"
                    value={rendimento}
                    onChange={(e) => onUpdateRecipe({
                      yieldQty: Number(e.target.value) || 1,
                      yieldUnit: unidadeVenda,
                      weightPerUnit: unidadeVenda === 'kg' ? null : ficha?.weightPerUnit
                    })}
                    title={unidadeVenda === 'kg'
                      ? 'Quantos quilos esta receita produz no total'
                      : 'Quantas unidades esta receita produz no total'}
                    className=\"field field-sm text-right tnum no-spin rounded-r-none border-r-0\"
                  />
                  <div
                    className=\"field field-sm w-16 rounded-l-none bg-black/[0.035] text-[#6e6e73] font-bold flex items-center justify-center cursor-default\"
                    title=\"Esta unidade vem do cadastro do produto\"
                  >
                    {unidadeVenda}
                  </div>
                </div>
                <p className=\"t-nano mt-1.5\">
                  {unidadeVenda === 'kg'
                    ? 'Produto vendido por kg · informe o peso total que a receita rende.'
                    : 'Produto vendido por unidade · informe quantas unidades a receita rende.'}
                </p>
              </div>
              <div className=\"col-span-12 sm:col-span-8 flex flex-wrap items-center gap-4 sm:justify-end\">"""
replace_once(old_block, new_block, 'recipe yield UI')

replace_once(
"""            const linhas = await run('recipes', sb.from('recipes').insert({ product_id: productId }).select());""",
"""            const produto = products.find((p) => p.id === productId);
            const linhas = await run('recipes', sb.from('recipes').insert({
              product_id: productId,
              yield_unit: (produto?.priceUnit || 'un') === 'kg' ? 'kg' : 'un'
            }).select());""",
'new recipe default yield unit')

replace_once(
'<meta name="app-version" content="2026-09-02-ficha-parcial-componentes-1" />',
'<meta name="app-version" content="2026-09-02-ficha-rendimento-venda-1" />',
'app version')

p.write_text(s, encoding='utf-8')
print('patched')
