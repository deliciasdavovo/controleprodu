from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Versão
s, n = re.subn(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-04-cadastros-unificados-1" />', s, count=1)
assert n == 1

# Navegação CMV: um único cadastro mestre
old = """            { id: 'produtos', label: 'Produtos', fullLabel: 'Produtos de fabricação', icon: Icons.Package },
            { id: 'insumos', label: 'Entradas', fullLabel: 'Entradas, compras e fichas', icon: Icons.Layers },"""
new = """            { id: 'insumos', label: 'Cadastros', fullLabel: 'Cadastros, compras e fichas', icon: Icons.Layers },"""
assert old in s
s = s.replace(old, new, 1)

# Tipos do formulário e estado
old = """        const TIPOS_ENTRADA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'producao', label: 'Produção' }
        ];"""
new = """        const TIPOS_ENTRADA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'insumo_revenda', label: 'Insumo + revenda' },
          { value: 'producao', label: 'Produção' }
        ];"""
assert old in s
s = s.replace(old, new, 1)

old = """        const BLANK_ENTRY = {
          type: 'insumo',
          name: '',"""
new = """        const BLANK_ENTRY = {
          type: 'insumo',
          purchaseKind: 'insumo',
          name: '',"""
assert old in s
s = s.replace(old, new, 1)

old = """        const modoProducao = draft.type === 'producao';

        const nomeDraft"""
new = """        const modoProducao = draft.type === 'producao';
        const tipoCompra = draft.purchaseKind || (draft.resaleAlso ? 'insumo_revenda' : 'insumo');
        const temInsumo = !modoProducao && (tipoCompra === 'insumo' || tipoCompra === 'insumo_revenda');
        const temRevenda = !modoProducao && (tipoCompra === 'revenda' || tipoCompra === 'insumo_revenda');
        const tipoCadastroAtual = modoProducao ? 'producao' : tipoCompra;

        const nomeDraft"""
assert old in s
s = s.replace(old, new, 1)

# Carregar cadastro existente preservando o tipo real
old = """              type: 'insumo',
              name: x.name,
              unit: x.unit || 'g',
              supplyClass: x.supplyClass || 'insumo',
              variationUnit: x.variationUnit || '',
              variationFactor: x.variationFactor || '',
              resaleAlso: !!rev,"""
new = """              type: 'insumo',
              purchaseKind: rev ? 'insumo_revenda' : 'insumo',
              name: x.name,
              unit: x.unit || 'g',
              supplyClass: x.supplyClass || 'insumo',
              variationUnit: x.variationUnit || '',
              variationFactor: x.variationFactor || '',
              resaleAlso: !!rev,"""
assert old in s
s = s.replace(old, new, 1)

old = """              type: 'insumo',
              name: x.productName,
              unit: ins?.unit || unidadeBaseDaRevenda(x.priceUnit || x.unitOfMeasure),
              supplyClass: ins?.supplyClass || 'insumo',
              variationUnit: ins?.variationUnit || '',
              variationFactor: ins?.variationFactor || '',
              resaleAlso: true,"""
new = """              type: 'insumo',
              purchaseKind: ins ? 'insumo_revenda' : 'revenda',
              name: x.productName,
              unit: ins?.unit || unidadeBaseDaRevenda(x.priceUnit || x.unitOfMeasure),
              supplyClass: ins?.supplyClass || 'insumo',
              variationUnit: ins?.variationUnit || '',
              variationFactor: ins?.variationFactor || '',
              resaleAlso: true,"""
assert old in s
s = s.replace(old, new, 1)

# Salvar compra/cadastro: insumo puro, revenda pura ou híbrido
start = s.index("          // Todo item comprado nasce/continua como insumo mestre.")
end_marker = "          setDraft((d) => ({\n            ...BLANK_ENTRY,\n            type: 'insumo',"
end = s.index(end_marker, start)
replacement = """          // Um cadastro comprado pode ser só insumo, só revenda ou os dois.
          // A mesma linha de compra alimenta apenas os históricos que pertencem
          // àquele tipo — sem obrigar revenda pura a nascer como insumo.
          let insumo = supplyExistente;
          if (temInsumo) {
            if (!insumo) {
              insumo = await onAddSupply({
                name: nome,
                unit: draft.unit || 'g',
                supplyClass: draft.supplyClass || 'insumo',
                variationUnit: String(draft.variationUnit || '').trim() || null,
                variationFactor: Number(draft.variationFactor) > 0 ? Number(draft.variationFactor) : null
              });
            }

            if (insumo) {
              const variationUnit = String(draft.variationUnit || '').trim() || null;
              const variationFactor = Number(draft.variationFactor) > 0 ? Number(draft.variationFactor) : null;
              if (variationUnit !== (insumo.variationUnit || null)
                || variationFactor !== (Number(insumo.variationFactor) || null)) {
                onUpdateSupply({ ...insumo, variationUnit, variationFactor });
                insumo = { ...insumo, variationUnit, variationFactor };
              }
            }

            if (insumo?.id && qty > 0 && cost > 0) {
              const qtdBase = temRevenda
                ? qtdCompraNaBase(qty, draft.purchaseUnit || draft.unit, insumo.unit || draft.unit)
                : qty;
              await onAddSupplyPurchase(insumo.id, {
                supplier: String(draft.supplier || '').trim(),
                purchaseDate: draft.purchaseDate || getTodayDateString(),
                qty: qtdBase,
                cost
              });
            }
          }

          let revenda = revendaExistente;
          if (temRevenda) {
            const dadosRevenda = {
              productName: nome,
              category: draft.resaleCategory || 'revenda',
              currentQty: revenda?.currentQty || 0,
              unitOfMeasure: draft.priceUnit || 'un',
              minQty: revenda?.minQty || 0,
              price: Math.max(0, Number(draft.price) || 0),
              priceUnit: draft.priceUnit || 'un'
            };

            if (!revenda) {
              revenda = await onAddSeparatedProduct(dadosRevenda);
            } else {
              onUpdateSeparatedProduct({ ...revenda, ...dadosRevenda });
            }

            if (revenda?.id && qty > 0 && cost > 0) {
              await onAddResalePurchase(revenda.id, {
                supplier: String(draft.supplier || '').trim(),
                purchaseDate: draft.purchaseDate || getTodayDateString(),
                qty,
                purchaseUnit: draft.purchaseUnit || draft.priceUnit || 'un',
                cost
              });
            }
          } else if (revendaExistente && insumo && onSetSupplyResale) {
            // Desmarcar a face de revenda em um insumo existente não apaga o
            // histórico; apenas tira o item da revenda ativa.
            onSetSupplyResale(insumo, false);
          }

"""
s = s[:start] + replacement + s[end:]

# Reset mantém o tipo escolhido para lançar vários itens seguidos
old = """            ...BLANK_ENTRY,
            type: 'insumo',
            unit: d.unit,"""
new = """            ...BLANK_ENTRY,
            type: 'insumo',
            purchaseKind: d.purchaseKind || 'insumo',
            resaleAlso: (d.purchaseKind || 'insumo') === 'insumo_revenda',
            unit: d.unit,"""
assert old in s
s = s.replace(old, new, 1)

# Título da tela
s = s.replace('<h2 className="t-display">Entradas &amp; fichas</h2>', '<h2 className="t-display">Cadastros, compras &amp; fichas</h2>', 1)
s = s.replace('Insumo e revenda entram pelo mesmo formulário de compra. Produção fica separada, porque o custo vem da ficha técnica.', 'Um único cadastro para Insumo, Revenda, Insumo + revenda e Produção. Compras e fichas ficam no mesmo lugar.', 1)

# Seletor principal: quatro tipos no mesmo formulário
old = """                    <div className="segmented w-full lg:w-auto lg:inline-flex shrink-0">
                      <button
                        type="button"
                        data-active={!modoProducao}
                        onClick={() => setDraft((d) => ({ ...BLANK_ENTRY, type: 'insumo', unit: d.unit, supplyClass: d.supplyClass, purchaseDate: getTodayDateString() }))}
                        className="flex-1 lg:flex-none h-9 px-4"
                      >
                        Insumo / revenda
                      </button>
                      <button
                        type="button"
                        data-active={modoProducao}
                        onClick={() => setDraft((d) => ({ ...BLANK_ENTRY, type: 'producao', productCategory: d.productCategory, priceUnit: d.priceUnit, purchaseDate: getTodayDateString() }))}
                        className="flex-1 lg:flex-none h-9 px-4"
                      >
                        Produção
                      </button>
                    </div>"""
new = """                    <div className="segmented w-full lg:w-auto lg:inline-flex shrink-0 overflow-x-auto">
                      {TIPOS_ENTRADA.map((tipo) => (
                        <button
                          key={tipo.value}
                          type="button"
                          data-active={tipoCadastroAtual === tipo.value}
                          onClick={() => setDraft((d) => tipo.value === 'producao'
                            ? {
                                ...BLANK_ENTRY,
                                type: 'producao',
                                productCategory: d.productCategory,
                                priceUnit: d.priceUnit,
                                purchaseDate: getTodayDateString()
                              }
                            : {
                                ...BLANK_ENTRY,
                                type: 'insumo',
                                purchaseKind: tipo.value,
                                resaleAlso: tipo.value === 'insumo_revenda',
                                unit: d.unit,
                                supplyClass: d.supplyClass,
                                priceUnit: d.priceUnit,
                                purchaseUnit: d.purchaseUnit,
                                resaleCategory: d.resaleCategory,
                                purchaseDate: getTodayDateString()
                              })}
                          className="flex-1 lg:flex-none h-9 px-4"
                        >
                          {tipo.label}
                        </button>
                      ))}
                    </div>"""
assert old in s
s = s.replace(old, new, 1)

s = s.replace('Um único formulário para insumo e revenda. Marque <strong>Também é revenda?</strong> quando o item também é vendido.', 'Escolha o tipo acima. Revenda apenas e Insumo + revenda usam a mesma linha de compra, sem cadastro duplicado.', 1)

# Primeira linha: unidade/classe só quando o item realmente tem lado de insumo
old = """                      {!modoProducao && (
                        <>
                          <div className="col-span-4 lg:col-span-2">
                            <label className="t-caption block mb-1">Unidade base</label>
                            {supplyExistente ? (
                              <div className="field field-md flex items-center px-3 bg-black/[0.035] text-[#86868b]">{supplyExistente.unit}</div>
                            ) : (
                              <PickerField
                                value={draft.unit}
                                options={SUPPLY_UNITS.map((u) => ({ value: u, label: u }))}
                                onPick={(opt) => setDraft((d) => ({ ...d, unit: opt.value }))}
                                className="field field-md"
                              />
                            )}
                          </div>
                          <div className="col-span-8 lg:col-span-3">
                            <label className="t-caption block mb-1">Classe</label>
                            {supplyExistente ? (
                              <div className="field field-md flex items-center px-3 bg-black/[0.035] text-[#86868b]">
                                {SUPPLY_CLASSES.find((c) => c.value === supplyExistente.supplyClass)?.label || 'Ingrediente'}
                              </div>
                            ) : (
                              <PickerField
                                value={draft.supplyClass}
                                options={SUPPLY_CLASSES}
                                onPick={(opt) => setDraft((d) => ({ ...d, supplyClass: opt.value }))}
                                className="field field-md"
                              />
                            )}
                          </div>
                          <div className="col-span-12 lg:col-span-3">
                            <label className="t-caption block mb-1">Também é revenda?</label>
                            <label className="field field-md flex items-center gap-2 cursor-pointer">
                              <input
                                type="checkbox"
                                checked={!!draft.resaleAlso}
                                onChange={(e) => setDraft((d) => ({ ...d, resaleAlso: e.target.checked }))}
                                className="w-4 h-4"
                              />
                              <span className="t-callout font-semibold">
                                {draft.resaleAlso ? 'Sim · também vendo este item' : 'Não · só uso/compro como insumo'}
                              </span>
                            </label>
                          </div>
                        </>
                      )}"""
new = """                      {temInsumo && (
                        <>
                          <div className="col-span-4 lg:col-span-2">
                            <label className="t-caption block mb-1">Unidade base</label>
                            {supplyExistente ? (
                              <div className="field field-md flex items-center px-3 bg-black/[0.035] text-[#86868b]">{supplyExistente.unit}</div>
                            ) : (
                              <PickerField
                                value={draft.unit}
                                options={SUPPLY_UNITS.map((u) => ({ value: u, label: u }))}
                                onPick={(opt) => setDraft((d) => ({ ...d, unit: opt.value }))}
                                className="field field-md"
                              />
                            )}
                          </div>
                          <div className="col-span-8 lg:col-span-3">
                            <label className="t-caption block mb-1">Classe</label>
                            {supplyExistente ? (
                              <div className="field field-md flex items-center px-3 bg-black/[0.035] text-[#86868b]">
                                {SUPPLY_CLASSES.find((c) => c.value === supplyExistente.supplyClass)?.label || 'Ingrediente'}
                              </div>
                            ) : (
                              <PickerField
                                value={draft.supplyClass}
                                options={SUPPLY_CLASSES}
                                onPick={(opt) => setDraft((d) => ({ ...d, supplyClass: opt.value }))}
                                className="field field-md"
                              />
                            )}
                          </div>
                        </>
                      )}

                      {!modoProducao && !temInsumo && (
                        <div className="col-span-8 lg:col-span-5">
                          <div className="field field-md flex items-center px-3 bg-black/[0.035] t-callout font-semibold">
                            Revenda apenas · comprado pronto para vender
                          </div>
                        </div>
                      )}"""
assert old in s
s = s.replace(old, new, 1)

# Refaz as três seções inferiores do formulário: revenda, equivalência e compra.
start_marker = "                    {!modoProducao && draft.resaleAlso && ("
start = s.index(start_marker)
end = s.index("                  </form>", start)
new_sections = r'''                    {!modoProducao && temRevenda && (
                      <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end mt-3 pt-3 border-t hairline">
                        <div className="col-span-6 sm:col-span-3">
                          <label className="t-caption block mb-1">Preço de venda</label>
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={draft.price}
                            onChange={(e) => setDraft((d) => ({ ...d, price: e.target.value }))}
                            placeholder="0,00"
                            className="field field-md text-right tnum no-spin"
                          />
                        </div>
                        <div className="col-span-6 sm:col-span-2">
                          <label className="t-caption block mb-1">Vendido por</label>
                          <PickerField
                            value={draft.priceUnit}
                            options={[{ value: 'un', label: 'unidade' }, { value: 'kg', label: 'kg' }, { value: 'g', label: 'g' }]}
                            onPick={(opt) => setDraft((d) => ({ ...d, priceUnit: opt.value, purchaseUnit: d.purchaseUnit || opt.value }))}
                            className="field field-md"
                          />
                        </div>
                        <div className="col-span-12 sm:col-span-3">
                          <label className="t-caption block mb-1">Categoria da revenda</label>
                          <PickerField
                            value={draft.resaleCategory}
                            options={[{ value: 'revenda', label: 'Revenda' }, { value: 'cafeteria', label: 'Cafeteria' }, { value: 'encomenda', label: 'Encomenda' }]}
                            onPick={(opt) => setDraft((d) => ({ ...d, resaleCategory: opt.value }))}
                            className="field field-md"
                          />
                        </div>
                        <div className="col-span-12 sm:col-span-4">
                          <div className="rounded-xl bg-black/[0.035] px-3 py-2 t-micro min-h-11 flex items-center">
                            {temInsumo
                              ? 'A compra abaixo alimenta o insumo e o CMV da revenda ao mesmo tempo.'
                              : 'Revenda apenas: a compra abaixo alimenta diretamente custo e CMV.'}
                          </div>
                        </div>
                      </div>
                    )}

                    {!modoProducao && temInsumo && (
                      <div className="mt-3 pt-3 border-t hairline">
                        <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end">
                          <div className="col-span-12 lg:col-span-3 lg:self-center">
                            <div className="t-caption font-semibold">Equivalência / variação <span className="font-normal text-[#86868b]">(opcional)</span></div>
                            <p className="t-micro mt-1">Ex.: 1 fatia = 30 g · 1 un = 500 g.</p>
                          </div>
                          <div className="col-span-6 sm:col-span-3">
                            <label className="t-caption block mb-1">Unidade alternativa</label>
                            <PickerField
                              value={draft.variationUnit}
                              options={UNIDADES_EQUIVALENCIA}
                              onType={(variationUnit) => setDraft((d) => ({ ...d, variationUnit }))}
                              onPick={(opt) => setDraft((d) => ({ ...d, variationUnit: opt.value }))}
                              placeholder="Ex: fatia"
                              emptyLabel="Usar esta unidade"
                              className="field field-md"
                            />
                          </div>
                          <div className="col-span-6 sm:col-span-2">
                            <label className="t-caption block mb-1">Quanto vale</label>
                            <input
                              type="number"
                              min="0"
                              step="0.001"
                              value={draft.variationFactor}
                              onChange={(e) => setDraft((d) => ({ ...d, variationFactor: e.target.value }))}
                              placeholder="Ex: 30"
                              className="field field-md text-right tnum no-spin"
                            />
                          </div>
                          <div className="col-span-12 sm:col-span-4">
                            <label className="t-caption block mb-1">Leitura</label>
                            <div className="field field-md flex items-center px-3 bg-black/[0.035] t-callout font-semibold whitespace-nowrap overflow-hidden text-ellipsis">
                              {draft.unit === 'un'
                                ? `1 un = ${draft.variationFactor || '…'} ${draft.variationUnit || '…'}`
                                : `1 ${draft.variationUnit || '…'} = ${draft.variationFactor || '…'} ${draft.unit || 'g'}`}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {!modoProducao && (
                      <div className="mt-3 pt-3 border-t hairline">
                        <div className="t-overline mb-2">Compra</div>
                        <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end">
                          <div className="col-span-12 sm:col-span-6 lg:col-span-3">
                            <label className="t-caption block mb-1">Fornecedor</label>
                            <PickerField
                              value={draft.supplier}
                              options={fornecedores.map((f) => ({ value: f, label: f }))}
                              onType={(supplier) => setDraft((d) => ({ ...d, supplier }))}
                              onPick={(opt) => setDraft((d) => ({ ...d, supplier: opt.value }))}
                              placeholder={compraExistente?.supplier || 'Fornecedor'}
                              emptyLabel="Fornecedor novo"
                              className="field field-md"
                            />
                          </div>
                          <div className="col-span-6 sm:col-span-3 lg:col-span-2">
                            <label className="t-caption block mb-1">Data</label>
                            <input type="date" value={draft.purchaseDate} onChange={(e) => setDraft((d) => ({ ...d, purchaseDate: e.target.value }))} className="field field-md" />
                          </div>
                          <div className="col-span-6 sm:col-span-3 lg:col-span-2">
                            <label className="t-caption block mb-1">Qtd. comprada{temInsumo && !temRevenda ? ` (${draft.unit})` : ''}</label>
                            <input
                              type="number"
                              min="0"
                              step="0.001"
                              value={draft.qty}
                              onChange={(e) => setDraft((d) => ({ ...d, qty: e.target.value }))}
                              placeholder={compraExistente?.qty ? String(compraExistente.qty) : '0'}
                              className="field field-md text-right tnum no-spin"
                            />
                          </div>
                          {temRevenda && (
                            <div className="col-span-4 sm:col-span-3 lg:col-span-1">
                              <label className="t-caption block mb-1">Un. compra</label>
                              <PickerField
                                value={draft.purchaseUnit}
                                options={[{ value: 'un', label: 'un' }, { value: 'kg', label: 'kg' }, { value: 'g', label: 'g' }, { value: 'L', label: 'L' }, { value: 'ml', label: 'ml' }]}
                                onPick={(opt) => setDraft((d) => ({ ...d, purchaseUnit: opt.value }))}
                                className="field field-md"
                              />
                            </div>
                          )}
                          <div className="col-span-8 sm:col-span-3 lg:col-span-2">
                            <label className="t-caption block mb-1">Valor pago</label>
                            <input
                              type="number"
                              min="0"
                              step="0.01"
                              value={draft.cost}
                              onChange={(e) => setDraft((d) => ({ ...d, cost: e.target.value }))}
                              placeholder={compraExistente?.cost ? String(compraExistente.cost) : '0,00'}
                              className="field field-md text-right tnum no-spin"
                            />
                          </div>
                          <div className="col-span-12 sm:col-span-6 lg:col-span-2">
                            <button type="submit" className="btn btn-primary btn-md w-full">
                              <Icons.Plus className="w-4 h-4" />
                              {cadastroExistente ? 'Registrar compra' : 'Cadastrar + compra'}
                            </button>
                          </div>
                        </div>
                      </div>
                    )}
'''
s = s[:start] + new_sections + s[end:]

# Aba antiga Produtos deixa de aparecer/renderizar: tudo está na aba Cadastros.
product_render = re.compile(r"\n\s*\{activeTab === 'produtos' && \(\n\s*<ProductCatalogView[\s\S]*?\n\s*/>\n\s*\)\}\n", re.M)
s, n = product_render.subn('\n', s, count=1)
assert n == 1, 'Product tab render not removed'

# Texto de apoio da tabela unificada
s = s.replace('O tipo pode ser Insumo, Revenda, Insumo + revenda ou Produção. Itens híbridos aparecem uma única vez. Em Equiv. você pode registrar coisas como 1 fatia = 30 g ou 1 un = 500 g.', 'Todos os cadastros ficam nesta tabela: Insumo, Revenda, Insumo + revenda e Produção. Itens híbridos aparecem uma única vez; use o seletor Tipo para corrigir a classificação.', 1)

# Verificações estruturais
checks = [
  '2026-09-04-cadastros-unificados-1',
  "{ value: 'insumo_revenda', label: 'Insumo + revenda' }",
  'const temInsumo', 'const temRevenda', 'tipoCadastroAtual',
  'Revenda apenas · comprado pronto para vender',
  'Cadastros, compras &amp; fichas',
  'Revenda apenas: a compra abaixo alimenta diretamente custo e CMV.',
  'Ex.: 1 fatia = 30 g · 1 un = 500 g.',
]
for c in checks:
    assert c in s, c
assert "{ id: 'produtos', label: 'Produtos'" not in s
assert "activeTab === 'produtos'" not in s
assert 'Também é revenda?</label>' not in s
# O bloco de equivalência não pode estar aninhado na grade da compra antiga.
assert s.count('Equivalência / variação') >= 2

p.write_text(s, encoding='utf-8')
print('patch ok')
