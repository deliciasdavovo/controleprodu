from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old_version = '<meta name="app-version" content="2026-09-04-cadastros-mestre-copiar-ficha-1" />'
new_version = '<meta name="app-version" content="2026-09-04-formulario-unico-enter-1" />'
if old_version in s:
    s = s.replace(old_version, new_version, 1)
elif new_version not in s:
    raise SystemExit('app version marker not found')

anchor = "        const opcoesCadastro = modoProducao ? opcoesProducao : opcoesCompra;\n"
helpers = r'''

        // Um formulário só para qualquer entrada. O tipo muda a classificação
        // do cadastro, mas não troca a tela nem desmonta os campos digitados.
        const aplicarTipoEntrada = (tipo) => {
          setDraft((d) => {
            if (tipo === 'producao') {
              return {
                ...d,
                type: 'producao',
                purchaseKind: 'insumo',
                resaleAlso: false
              };
            }
            if (tipo === 'embalagem' || tipo === 'limpeza') {
              return {
                ...d,
                type: 'insumo',
                purchaseKind: 'insumo',
                resaleAlso: false,
                supplyClass: tipo
              };
            }
            return {
              ...d,
              type: 'insumo',
              purchaseKind: tipo,
              resaleAlso: tipo === 'insumo_revenda',
              supplyClass: 'insumo'
            };
          });
        };

        // Fluxo rápido de teclado, como no cadastro de compras antigo:
        // Enter aceita o valor do campo atual e avança para o próximo campo
        // habilitado. No fim ele para no botão Salvar; o próximo Enter grava.
        const avancarEntradaRapida = (e) => {
          if (e.key !== 'Enter' || e.shiftKey || e.ctrlKey || e.metaKey || e.altKey) return;
          const alvo = e.target;
          if (!alvo || alvo.tagName === 'BUTTON' || alvo.tagName === 'TEXTAREA') return;
          const form = e.currentTarget;
          const campos = Array.from(form.querySelectorAll(
            'input:not([type="hidden"]):not([disabled]), select:not([disabled]), button[type="submit"]:not([disabled])'
          )).filter((el) => el.offsetParent !== null);
          const idx = campos.indexOf(alvo);
          if (idx < 0 || idx >= campos.length - 1) return;
          e.preventDefault();
          const proximo = campos[idx + 1];
          requestAnimationFrame(() => {
            proximo.focus();
            if (proximo.tagName === 'INPUT' && proximo.select && proximo.type !== 'date') proximo.select();
          });
        };
'''
if 'const avancarEntradaRapida = (e) =>' not in s:
    if anchor not in s:
        raise SystemExit('opcoesCadastro anchor not found')
    s = s.replace(anchor, anchor + helpers, 1)

section = s.index("            {painel === 'entradas' && (")
start = s.index('                <div className="card p-6 sm:p-7">', section)
end = s.index('                <div className="card p-5 sm:p-6">', start)

new_card = r'''                <div className="card p-6 sm:p-7">
                  <div>
                    <div className="t-overline flex items-center gap-1.5 mb-2">
                      <Icons.ShoppingCart className="w-3.5 h-3.5" />
                      Entrada principal
                    </div>
                    <h3 className="t-title">Cadastro + compra</h3>
                    <p className="t-body mt-1.5">
                      Um formulário só para tudo. Escolha o tipo no primeiro campo e siga com Enter. A equivalência fica na tabela abaixo para não atrapalhar o lançamento da compra.
                    </p>
                  </div>

                  <form onSubmit={cadastrar} onKeyDown={avancarEntradaRapida} className="mt-5 pt-5 border-t hairline">
                    <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end">
                      <div className="col-span-6 sm:col-span-4 lg:col-span-2">
                        <label className="t-caption block mb-1">Tipo</label>
                        <select
                          value={tipoCadastroAtual}
                          onChange={(e) => aplicarTipoEntrada(e.target.value)}
                          className="field field-md field-select font-semibold"
                        >
                          {TIPOS_ENTRADA.map((tipo) => <option key={tipo.value} value={tipo.value}>{tipo.label}</option>)}
                        </select>
                      </div>

                      <div className="col-span-12 sm:col-span-8 lg:col-span-4">
                        <label className="t-caption block mb-1">Item</label>
                        <PickerField
                          inputRef={nomeRef}
                          value={draft.name}
                          options={opcoesCadastro}
                          onType={(name) => setDraft((d) => ({ ...d, name }))}
                          onPick={selecionarCadastro}
                          placeholder={modoProducao ? 'Digite ou escolha um produto' : 'Digite ou escolha um item'}
                          emptyLabel="Item novo — será cadastrado ao salvar"
                          className="field field-md font-semibold"
                        />
                      </div>

                      <div className="col-span-4 sm:col-span-3 lg:col-span-2">
                        <label className="t-caption block mb-1">Unidade base</label>
                        <select
                          value={temInsumo ? draft.unit : ''}
                          disabled={!temInsumo || !!supplyExistente}
                          onChange={(e) => setDraft((d) => ({ ...d, unit: e.target.value, purchaseUnit: e.target.value }))}
                          className="field field-md field-select disabled:opacity-50"
                        >
                          {!temInsumo && <option value="">—</option>}
                          {SUPPLY_UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
                        </select>
                      </div>

                      <div className="col-span-8 sm:col-span-5 lg:col-span-2">
                        <label className="t-caption block mb-1">Categoria</label>
                        <select
                          value={modoProducao ? draft.productCategory : (temRevenda ? draft.resaleCategory : '')}
                          disabled={!modoProducao && !temRevenda}
                          onChange={(e) => setDraft((d) => modoProducao
                            ? ({ ...d, productCategory: e.target.value })
                            : ({ ...d, resaleCategory: e.target.value }))}
                          className="field field-md field-select disabled:opacity-50"
                        >
                          {!modoProducao && !temRevenda && <option value="">—</option>}
                          {modoProducao
                            ? PRODUCT_CATEGORIES.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)
                            : [
                                { value: 'revenda', label: 'Revenda' },
                                { value: 'cafeteria', label: 'Cafeteria' },
                                { value: 'encomenda', label: 'Encomenda' }
                              ].map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                        </select>
                      </div>

                      <div className="col-span-6 sm:col-span-4 lg:col-span-2">
                        <label className="t-caption block mb-1">Responsável</label>
                        <input
                          value={modoProducao ? draft.responsible : ''}
                          disabled={!modoProducao}
                          onChange={(e) => setDraft((d) => ({ ...d, responsible: e.target.value }))}
                          placeholder={modoProducao ? 'Quem produz' : '—'}
                          className="field field-md disabled:opacity-50"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end mt-3 pt-3 border-t hairline">
                      <div className="col-span-12 sm:col-span-6 lg:col-span-3">
                        <label className="t-caption block mb-1">Fornecedor</label>
                        {modoProducao ? (
                          <input value="" disabled placeholder="Não se aplica" className="field field-md disabled:opacity-50" />
                        ) : (
                          <PickerField
                            value={draft.supplier}
                            options={fornecedores.map((f) => ({ value: f, label: f }))}
                            onType={(supplier) => setDraft((d) => ({ ...d, supplier }))}
                            onPick={(opt) => setDraft((d) => ({ ...d, supplier: opt.value }))}
                            placeholder={compraExistente?.supplier || 'Fornecedor'}
                            emptyLabel="Fornecedor novo"
                            className="field field-md"
                          />
                        )}
                      </div>

                      <div className="col-span-6 sm:col-span-3 lg:col-span-2">
                        <label className="t-caption block mb-1">Data</label>
                        <input
                          type="date"
                          value={modoProducao ? '' : draft.purchaseDate}
                          disabled={modoProducao}
                          onChange={(e) => setDraft((d) => ({ ...d, purchaseDate: e.target.value }))}
                          className="field field-md disabled:opacity-50"
                        />
                      </div>

                      <div className="col-span-6 sm:col-span-3 lg:col-span-2">
                        <label className="t-caption block mb-1">Qtd. comprada{temInsumo && !temRevenda ? ` (${draft.unit})` : ''}</label>
                        <input
                          type="number"
                          min="0"
                          step="0.001"
                          value={modoProducao ? '' : draft.qty}
                          disabled={modoProducao}
                          onChange={(e) => setDraft((d) => ({ ...d, qty: e.target.value }))}
                          placeholder={compraExistente?.qty ? String(compraExistente.qty) : '0'}
                          className="field field-md text-right tnum no-spin disabled:opacity-50"
                        />
                      </div>

                      <div className="col-span-4 sm:col-span-3 lg:col-span-1">
                        <label className="t-caption block mb-1">Un. compra</label>
                        <select
                          value={temInsumo && !temRevenda ? draft.unit : draft.purchaseUnit}
                          disabled={modoProducao || (temInsumo && !temRevenda)}
                          onChange={(e) => setDraft((d) => ({ ...d, purchaseUnit: e.target.value }))}
                          className="field field-md field-select disabled:opacity-50"
                        >
                          {['un', 'kg', 'g', 'L', 'ml'].map((u) => <option key={u} value={u}>{u}</option>)}
                        </select>
                      </div>

                      <div className="col-span-8 sm:col-span-3 lg:col-span-2">
                        <label className="t-caption block mb-1">Valor pago</label>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={modoProducao ? '' : draft.cost}
                          disabled={modoProducao}
                          onChange={(e) => setDraft((d) => ({ ...d, cost: e.target.value }))}
                          placeholder={compraExistente?.cost ? String(compraExistente.cost) : '0,00'}
                          className="field field-md text-right tnum no-spin disabled:opacity-50"
                        />
                      </div>

                      <div className="col-span-4 sm:col-span-3 lg:col-span-1">
                        <label className="t-caption block mb-1">Preço venda</label>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={modoProducao || temRevenda ? draft.price : ''}
                          disabled={!modoProducao && !temRevenda}
                          onChange={(e) => setDraft((d) => ({ ...d, price: e.target.value }))}
                          placeholder="0,00"
                          className="field field-md text-right tnum no-spin disabled:opacity-50"
                        />
                      </div>

                      <div className="col-span-4 sm:col-span-3 lg:col-span-1">
                        <label className="t-caption block mb-1">Vende por</label>
                        <select
                          value={modoProducao || temRevenda ? draft.priceUnit : ''}
                          disabled={!modoProducao && !temRevenda}
                          onChange={(e) => setDraft((d) => ({ ...d, priceUnit: e.target.value }))}
                          className="field field-md field-select disabled:opacity-50"
                        >
                          {!modoProducao && !temRevenda && <option value="">—</option>}
                          <option value="un">un</option>
                          <option value="kg">kg</option>
                          {!modoProducao && <option value="g">g</option>}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end mt-3">
                      <div className="col-span-6 sm:col-span-3 lg:col-span-2">
                        <label className="t-caption block mb-1">Validade (dias)</label>
                        <input
                          type="number"
                          min="1"
                          value={modoProducao ? draft.shelfLifeDays : ''}
                          disabled={!modoProducao}
                          onChange={(e) => setDraft((d) => ({ ...d, shelfLifeDays: e.target.value }))}
                          placeholder="—"
                          className="field field-md text-center tnum disabled:opacity-50"
                        />
                      </div>
                      <div className="col-span-6 sm:col-span-9 lg:col-span-7">
                        <div className="rounded-xl bg-black/[0.035] px-3 py-2 t-micro min-h-11 flex items-center">
                          {tipoCadastroAtual === 'embalagem'
                            ? 'Embalagem · uso interno. Não precisa escolher Insumo/Revenda.'
                            : tipoCadastroAtual === 'limpeza'
                              ? 'Material de limpeza · uso interno. Não precisa escolher Insumo/Revenda.'
                              : modoProducao
                                ? 'Produção: fornecedor, quantidade e valor pago não se aplicam; o custo vem da ficha técnica.'
                                : temRevenda && temInsumo
                                  ? 'Insumo + revenda: a mesma compra alimenta o custo do insumo e o CMV da revenda.'
                                  : temRevenda
                                    ? 'Revenda: a compra alimenta diretamente custo e CMV.'
                                    : 'Insumo: a compra alimenta o custo usado nas fichas técnicas.'}
                        </div>
                      </div>
                      <div className="col-span-12 sm:col-span-12 lg:col-span-3">
                        <button type="submit" className="btn btn-primary btn-md w-full">
                          <Icons.Plus className="w-4 h-4" />
                          {modoProducao
                            ? (produtoExistente ? 'Salvar produto' : 'Cadastrar produto')
                            : (cadastroExistente ? 'Registrar compra' : 'Cadastrar + compra')}
                        </button>
                      </div>
                    </div>
                  </form>

                  {!modoProducao && cadastroExistente && (
                    <div className="mt-3 px-3 py-2 rounded-xl bg-black/[0.035] t-micro">
                      <strong>{supplyExistente?.name || revendaExistente?.productName}</strong>
                      <span>
                        {' · '}
                        {tipoCadastroAtual === 'embalagem'
                          ? 'embalagem'
                          : tipoCadastroAtual === 'limpeza'
                            ? 'material de limpeza'
                            : supplyExistente
                              ? (revendaExistente ? 'insumo + revenda' : 'insumo')
                              : 'revenda'}
                      </span>
                      {compraExistente && (
                        <span>
                          {' · última compra '}{formatCurrencyBR(Number(compraExistente.cost) || 0)}
                          {compraExistente.supplier ? ` · ${compraExistente.supplier}` : ''}
                        </span>
                      )}
                    </div>
                  )}
                </div>

'''
s = s[:start] + new_card + s[end:]

# No formulário novo, equivalência fica só na tabela mestre.
entry_start = s.index("            {painel === 'entradas' && (")
entry_table = s.index('                <div className="card p-5 sm:p-6">', entry_start)
entry_form = s[entry_start:entry_table]
if 'Equivalência / variação' in entry_form:
    raise SystemExit('equivalence still present in entry form')
if 'TIPOS_ENTRADA.map((tipo) => (' in entry_form:
    raise SystemExit('segmented type buttons still present in entry form')
if 'onKeyDown={avancarEntradaRapida}' not in entry_form:
    raise SystemExit('Enter flow not wired')
if '<label className="t-caption block mb-1">Tipo</label>' not in entry_form:
    raise SystemExit('single type field missing')
if '<th className="py-3 px-3 font-bold">Equiv.</th>' not in s:
    raise SystemExit('equivalence table column missing')
if '<th className="py-3 px-3 font-bold">Preço venda</th>' not in s:
    raise SystemExit('sale price table column missing')
if 'onDeleteCatalogItem(linha)' not in s:
    raise SystemExit('catalog delete action missing')

p.write_text(s, encoding='utf-8')
print('single entry form patch applied')
