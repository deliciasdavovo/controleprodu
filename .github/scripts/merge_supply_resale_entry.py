from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Version marker
s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-03-insumo-revenda-um-form-1" />',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('version marker not found')

component_start = s.index('      const SuppliesRecipesView = ({')
logic_start = s.index('        const TIPOS_ENTRADA = [', component_start)
logic_end = s.index('        // Produtos de fabricação, com a ficha e o custo já resolvidos', logic_start)

new_logic = r'''        // A tabela continua distinguindo os três tipos. No formulário de compra,
        // porém, insumo e revenda são a MESMA entrada: revenda é uma opção do
        // insumo, como era no fluxo rápido original.
        const TIPOS_ENTRADA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'producao', label: 'Produção' }
        ];
        const BLANK_ENTRY = {
          type: 'insumo',
          name: '',
          unit: 'g',
          supplyClass: 'insumo',
          resaleAlso: false,
          supplier: '',
          purchaseDate: getTodayDateString(),
          qty: '',
          cost: '',
          purchaseUnit: 'un',
          responsible: '',
          productCategory: 'salgado',
          shelfLifeDays: 2,
          price: '',
          priceUnit: 'un',
          resaleCategory: 'revenda'
        };
        const [draft, setDraft] = useState(BLANK_ENTRY);
        const nomeRef = useRef(null);

        const comprasDoInsumo = (id) => supplyPurchases.filter((c) => c.supplyId === id);
        const comprasDaRevenda = (id) => resalePurchases.filter((c) => c.separatedProductId === id);
        const revendaDaUnidade = separatedProducts.filter((p) => p.unit === currentUnit);
        const modoProducao = draft.type === 'producao';

        const nomeDraft = normalizeName(String(draft.name || '').trim());
        const supplyExistente = nomeDraft
          ? supplies.find((x) => normalizeName(x.name) === nomeDraft) || null
          : null;
        const revendaExistente = nomeDraft
          ? revendaDaUnidade.find((x) => normalizeName(x.productName) === nomeDraft) || null
          : null;
        const produtoExistente = nomeDraft
          ? products.find((x) => normalizeName(x.name) === nomeDraft) || null
          : null;

        const cadastroExistente = modoProducao
          ? produtoExistente
          : (supplyExistente || revendaExistente);

        // Na entrada única, a última compra pode estar no histórico de insumo
        // ou no histórico de revenda (dados antigos). Usamos a mais recente só
        // para sugerir fornecedor/quantidade/valor no formulário.
        const compraExistente = !modoProducao
          ? ultimaCompra([
              ...(supplyExistente ? comprasDoInsumo(supplyExistente.id) : []),
              ...(revendaExistente ? comprasDaRevenda(revendaExistente.id) : [])
            ])
          : null;

        const unidadeBaseDaRevenda = (unidade) => {
          const u = String(unidade || 'un');
          if (u === 'kg' || u === 'g') return 'g';
          if (u === 'L' || u === 'ml') return 'ml';
          return 'un';
        };

        const qtdCompraNaBase = (qtd, unidadeCompra, unidadeBase) => {
          const q = Number(qtd) || 0;
          const de = String(unidadeCompra || unidadeBase || 'un');
          const para = String(unidadeBase || 'un');
          if (!q || de === para) return q;
          if (de === 'kg' && para === 'g') return q * 1000;
          if (de === 'g' && para === 'kg') return q / 1000;
          if (de === 'L' && para === 'ml') return q * 1000;
          if (de === 'ml' && para === 'L') return q / 1000;
          return q;
        };

        // Um nome só no autocomplete. Se o item já é insumo + revenda, ele
        // aparece uma vez e o hint deixa isso claro.
        const opcoesCompra = useMemo(() => {
          const mapa = new Map();
          supplies.forEach((x) => {
            const rev = revendaDaUnidade.find((r) => normalizeName(r.productName) === normalizeName(x.name));
            mapa.set(normalizeName(x.name), {
              value: `insumo:${x.id}`,
              label: x.name,
              hint: rev ? `Insumo · ${x.unit} · revenda também` : `Insumo · ${x.unit}`
            });
          });
          revendaDaUnidade.forEach((x) => {
            const key = normalizeName(x.productName);
            if (!mapa.has(key)) {
              mapa.set(key, {
                value: `revenda:${x.id}`,
                label: x.productName,
                hint: `Revenda · ${x.priceUnit || 'un'}`
              });
            }
          });
          return Array.from(mapa.values()).sort((a, b) => a.label.localeCompare(b.label, 'pt-BR'));
        }, [supplies, revendaDaUnidade]);

        const opcoesProducao = useMemo(
          () => products
            .map((x) => ({ value: `producao:${x.id}`, label: x.name, hint: `Produção · ${x.priceUnit || 'un'}` }))
            .sort((a, b) => a.label.localeCompare(b.label, 'pt-BR')),
          [products]
        );

        const opcoesCadastro = modoProducao ? opcoesProducao : opcoesCompra;

        const selecionarCadastro = (opt) => {
          const [tipo, id] = String(opt?.value || '').split(':');

          if (tipo === 'producao') {
            const x = products.find((i) => String(i.id) === id);
            if (x) setDraft((d) => ({
              ...d,
              type: 'producao',
              name: x.name,
              responsible: x.responsible || '',
              productCategory: x.category || 'salgado',
              shelfLifeDays: x.shelfLifeDays || 2,
              price: x.price || '',
              priceUnit: x.priceUnit || 'un'
            }));
            return;
          }

          if (tipo === 'insumo') {
            const x = supplies.find((i) => String(i.id) === id);
            if (!x) return;
            const rev = revendaDaUnidade.find((r) => normalizeName(r.productName) === normalizeName(x.name));
            setDraft((d) => ({
              ...d,
              type: 'insumo',
              name: x.name,
              unit: x.unit || 'g',
              supplyClass: x.supplyClass || 'insumo',
              resaleAlso: !!rev,
              price: rev?.price || '',
              priceUnit: rev?.priceUnit || d.priceUnit || 'un',
              purchaseUnit: rev?.priceUnit || d.purchaseUnit || x.unit || 'un',
              resaleCategory: rev?.category || d.resaleCategory || 'revenda'
            }));
            return;
          }

          if (tipo === 'revenda') {
            const x = revendaDaUnidade.find((i) => String(i.id) === id);
            if (!x) return;
            const ins = supplies.find((i) => normalizeName(i.name) === normalizeName(x.productName));
            setDraft((d) => ({
              ...d,
              type: 'insumo',
              name: x.productName,
              unit: ins?.unit || unidadeBaseDaRevenda(x.priceUnit || x.unitOfMeasure),
              supplyClass: ins?.supplyClass || 'insumo',
              resaleAlso: true,
              price: x.price || '',
              priceUnit: x.priceUnit || 'un',
              purchaseUnit: x.priceUnit || 'un',
              resaleCategory: x.category || 'revenda'
            }));
          }
        };

        const cadastrar = async (e) => {
          e.preventDefault();
          const nome = String(draft.name || '').trim();
          if (!nome) return;

          if (modoProducao) {
            const dados = {
              name: nome,
              responsible: cleanResponsible(draft.responsible),
              category: draft.productCategory || 'outro',
              showcaseEnabled: produtoExistente ? produtoExistente.showcaseEnabled !== false : false,
              shelfLifeDays: Math.max(1, Number(draft.shelfLifeDays) || 2),
              price: Math.max(0, Number(draft.price) || 0),
              priceUnit: draft.priceUnit === 'kg' ? 'kg' : 'un',
              defaultUnit: 'un',
              minReplenishmentQty: produtoExistente?.minReplenishmentQty || 5
            };
            if (produtoExistente) onUpdateProduct({ ...produtoExistente, ...dados });
            else await onAddProduct(dados);
            setDraft((d) => ({
              ...BLANK_ENTRY,
              type: 'producao',
              productCategory: d.productCategory,
              priceUnit: d.priceUnit,
              purchaseDate: getTodayDateString()
            }));
            setTimeout(() => nomeRef.current && nomeRef.current.focus(), 50);
            return;
          }

          const qty = Number(draft.qty) || 0;
          const cost = Number(draft.cost) || 0;
          if ((qty > 0 || cost > 0) && !(qty > 0 && cost > 0)) {
            window.alert('Para registrar a compra, preencha quantidade e valor pago.');
            return;
          }

          // Todo item comprado nasce/continua como insumo mestre. A opção
          // "Também é revenda" só acrescenta a face de venda do MESMO item.
          let insumo = supplyExistente;
          if (!insumo) {
            insumo = await onAddSupply({
              name: nome,
              unit: draft.unit || 'g',
              supplyClass: draft.supplyClass || 'insumo'
            });
          }

          if (insumo?.id && qty > 0 && cost > 0) {
            const qtdBase = draft.resaleAlso
              ? qtdCompraNaBase(qty, draft.purchaseUnit || draft.unit, insumo.unit || draft.unit)
              : qty;
            await onAddSupplyPurchase(insumo.id, {
              supplier: String(draft.supplier || '').trim(),
              purchaseDate: draft.purchaseDate || getTodayDateString(),
              qty: qtdBase,
              cost
            });
          }

          if (draft.resaleAlso) {
            let revenda = revendaExistente;
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

            // Revenda também precisa de histórico de compra próprio para CMV.
            // A mesma entrada alimenta os dois lados sem pedir tudo de novo.
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
            // Se a pessoa desmarcou conscientemente em um item já existente,
            // o cadastro deixa de aparecer como revenda, mas o histórico fica.
            onSetSupplyResale(insumo, false);
          }

          setDraft((d) => ({
            ...BLANK_ENTRY,
            type: 'insumo',
            unit: d.unit,
            supplyClass: d.supplyClass,
            priceUnit: d.priceUnit,
            purchaseUnit: d.purchaseUnit,
            resaleCategory: d.resaleCategory,
            purchaseDate: getTodayDateString()
          }));
          setTimeout(() => nomeRef.current && nomeRef.current.focus(), 50);
        };

'''

s = s[:logic_start] + new_logic + s[logic_end:]

# Update the page explanation.
s = s.replace(
    'Cadastre produção, insumo ou revenda e já lance a compra no mesmo lugar. É daqui que sai o CMV.',
    'Insumo e revenda entram pelo mesmo formulário de compra. Produção fica separada, porque o custo vem da ficha técnica.',
    1,
)

# Replace only the first card in the Entradas panel. The unified table below is
# intentionally preserved because it is where the type is visible/editable.
panel_start = s.index("            {painel === 'entradas' && (", component_start)
card_start = s.index('                <div className="card p-6 sm:p-7">', panel_start)
next_card = s.index('                <div className="card p-5 sm:p-6">', card_start)

new_card = r'''                <div className="card p-6 sm:p-7">
                  <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                    <div>
                      <div className="t-overline flex items-center gap-1.5 mb-2">
                        <Icons.ShoppingCart className="w-3.5 h-3.5" />
                        Entrada principal
                      </div>
                      <h3 className="t-title">Cadastro + compra</h3>
                      <p className="t-body mt-1.5">
                        Um único formulário para insumo e revenda. Marque <strong>Também é revenda?</strong> quando o item também é vendido.
                      </p>
                    </div>
                    <div className="segmented w-full lg:w-auto lg:inline-flex shrink-0">
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
                    </div>
                  </div>

                  <form onSubmit={cadastrar} className="mt-5 pt-5 border-t hairline">
                    <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end">
                      <div className="col-span-12 lg:col-span-4">
                        <label className="t-caption block mb-1">Item</label>
                        <PickerField
                          inputRef={nomeRef}
                          value={draft.name}
                          options={opcoesCadastro}
                          onType={(name) => setDraft((d) => ({ ...d, name }))}
                          onPick={selecionarCadastro}
                          placeholder={modoProducao ? 'Digite ou escolha um produto' : 'Digite ou escolha um insumo / revenda'}
                          emptyLabel="Item novo — será cadastrado ao salvar"
                          className="field field-md font-semibold"
                        />
                      </div>

                      {!modoProducao && (
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
                      )}

                      {modoProducao && (
                        <>
                          <div className="col-span-6 lg:col-span-2">
                            <label className="t-caption block mb-1">Responsável</label>
                            <input value={draft.responsible} onChange={(e) => setDraft((d) => ({ ...d, responsible: e.target.value }))} placeholder="Quem produz" className="field field-md" />
                          </div>
                          <div className="col-span-6 lg:col-span-2">
                            <label className="t-caption block mb-1">Categoria</label>
                            <PickerField value={draft.productCategory} options={PRODUCT_CATEGORIES} onPick={(opt) => setDraft((d) => ({ ...d, productCategory: opt.value }))} className="field field-md" />
                          </div>
                          <div className="col-span-4 lg:col-span-1">
                            <label className="t-caption block mb-1">Validade</label>
                            <input type="number" min="1" value={draft.shelfLifeDays} onChange={(e) => setDraft((d) => ({ ...d, shelfLifeDays: e.target.value }))} className="field field-md text-center tnum" />
                          </div>
                          <div className="col-span-4 lg:col-span-1">
                            <label className="t-caption block mb-1">Preço</label>
                            <input type="number" min="0" step="0.01" value={draft.price} onChange={(e) => setDraft((d) => ({ ...d, price: e.target.value }))} placeholder="0,00" className="field field-md text-right tnum no-spin" />
                          </div>
                          <div className="col-span-4 lg:col-span-1">
                            <label className="t-caption block mb-1">Vende por</label>
                            <PickerField value={draft.priceUnit} options={[{ value: 'un', label: 'un' }, { value: 'kg', label: 'kg' }]} onPick={(opt) => setDraft((d) => ({ ...d, priceUnit: opt.value }))} className="field field-md" />
                          </div>
                          <div className="col-span-12 lg:col-span-2">
                            <button type="submit" className="btn btn-primary btn-md w-full">
                              <Icons.Plus className="w-4 h-4" />
                              {produtoExistente ? 'Salvar produto' : 'Cadastrar produto'}
                            </button>
                          </div>
                        </>
                      )}
                    </div>

                    {!modoProducao && draft.resaleAlso && (
                      <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end mt-3 pt-3 border-t hairline">
                        <div className="col-span-4 sm:col-span-2">
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
                        <div className="col-span-4 sm:col-span-2">
                          <label className="t-caption block mb-1">Vendido por</label>
                          <PickerField
                            value={draft.priceUnit}
                            options={[{ value: 'un', label: 'unidade' }, { value: 'kg', label: 'kg' }, { value: 'g', label: 'g' }]}
                            onPick={(opt) => setDraft((d) => ({ ...d, priceUnit: opt.value, purchaseUnit: d.purchaseUnit || opt.value }))}
                            className="field field-md"
                          />
                        </div>
                        <div className="col-span-4 sm:col-span-3">
                          <label className="t-caption block mb-1">Categoria da revenda</label>
                          <PickerField
                            value={draft.resaleCategory}
                            options={[{ value: 'revenda', label: 'Revenda' }, { value: 'cafeteria', label: 'Cafeteria' }, { value: 'encomenda', label: 'Encomenda' }]}
                            onPick={(opt) => setDraft((d) => ({ ...d, resaleCategory: opt.value }))}
                            className="field field-md"
                          />
                        </div>
                        <div className="col-span-12 sm:col-span-5">
                          <p className="t-micro pb-2">
                            A compra abaixo vale para o insumo e também alimenta o histórico/CMV da revenda — sem preencher duas vezes.
                          </p>
                        </div>
                      </div>
                    )}

                    {!modoProducao && (
                      <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end mt-3 pt-3 border-t hairline">
                        <div className="col-span-12 sm:col-span-4">
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
                        <div className="col-span-6 sm:col-span-2">
                          <label className="t-caption block mb-1">Data</label>
                          <input type="date" value={draft.purchaseDate} onChange={(e) => setDraft((d) => ({ ...d, purchaseDate: e.target.value }))} className="field field-md" />
                        </div>
                        <div className={`${draft.resaleAlso ? 'col-span-3 sm:col-span-1' : 'col-span-6 sm:col-span-2'}`}>
                          <label className="t-caption block mb-1">Qtd. comprada</label>
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
                        {draft.resaleAlso && (
                          <div className="col-span-3 sm:col-span-1">
                            <label className="t-caption block mb-1">Un. compra</label>
                            <PickerField
                              value={draft.purchaseUnit}
                              options={[{ value: 'un', label: 'un' }, { value: 'kg', label: 'kg' }, { value: 'g', label: 'g' }, { value: 'L', label: 'L' }, { value: 'ml', label: 'ml' }]}
                              onPick={(opt) => setDraft((d) => ({ ...d, purchaseUnit: opt.value }))}
                              className="field field-md"
                            />
                          </div>
                        )}
                        <div className={`${draft.resaleAlso ? 'col-span-6 sm:col-span-2' : 'col-span-6 sm:col-span-2'}`}>
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
                        <div className="col-span-6 sm:col-span-2">
                          <button type="submit" className="btn btn-primary btn-md w-full">
                            <Icons.Plus className="w-4 h-4" />
                            {cadastroExistente ? 'Registrar compra' : 'Cadastrar + compra'}
                          </button>
                        </div>
                      </div>
                    )}
                  </form>

                  {!modoProducao && cadastroExistente && (
                    <div className="mt-3 px-3 py-2 rounded-xl bg-black/[0.035] t-micro">
                      <strong>{supplyExistente?.name || revendaExistente?.productName}</strong>
                      <span>
                        {' · '}
                        {supplyExistente ? 'insumo' : 'revenda'}
                        {revendaExistente && supplyExistente ? ' + revenda' : ''}
                      </span>
                      {compraExistente && (
                        <span>
                          {' · última compra '}{formatCurrencyBR(Number(compraExistente.cost) || 0)}
                          {compraExistente.supplier ? ` · ${compraExistente.supplier}` : ''}
                        </span>
                      )}
                    </div>
                  )}
                </div>'''

s = s[:card_start] + new_card + '\n\n' + s[next_card:]

p.write_text(s, encoding='utf-8')
print('patched supply + resale single form')
