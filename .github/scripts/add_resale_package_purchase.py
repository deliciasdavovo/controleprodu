from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old_version = '<meta name="app-version" content="2026-09-05-fornecedor-anterior-enter-1" />'
new_version = '<meta name="app-version" content="2026-09-05-revenda-compra-volume-1" />'
if old_version in s:
    s = s.replace(old_version, new_version, 1)
elif new_version not in s:
    raise SystemExit('app version marker not found')

# -----------------------------------------------------------------------------
# 1. Compra de revenda por volume: usamos purchase_unit para persistir o pacote
#    sem precisar alterar o banco. qty continua sendo o total vendavel.
# -----------------------------------------------------------------------------
converter_marker = """      const converterQtdRevenda = (qtd, origem, destino) => {
        const n = Number(qtd) || 0;
        const de = origem || 'un';
        const para = destino || 'un';"""
helpers_and_converter = r'''      const TIPOS_VOLUME_REVENDA = [
        { value: 'caixa', label: 'Caixa' },
        { value: 'pacote', label: 'Pacote' },
        { value: 'fardo', label: 'Fardo' },
        { value: 'display', label: 'Display' },
        { value: 'bandeja', label: 'Bandeja' },
        { value: 'outro', label: 'Outro' }
      ];

      // A unidade da compra continua em um campo texto do banco. Para revenda
      // vendida por unidade guardamos, por exemplo, pack:caixa:50. A quantidade
      // salva e sempre o total de unidades (2 caixas x 50 = 100 un), portanto
      // CMV, custo unitario e historico antigo continuam compativeis.
      const lerUnidadeCompraVolume = (valor) => {
        const match = String(valor || '').match(/^pack:([a-z_]+):([0-9]+(?:\.[0-9]+)?)$/i);
        if (!match) return null;
        const unidades = Number(match[2]) || 0;
        return unidades > 0 ? { tipo: String(match[1]).toLowerCase(), unidades } : null;
      };

      const criarUnidadeCompraVolume = (tipo, unidades) =>
        `pack:${String(tipo || 'caixa').toLowerCase()}:${Number(unidades) || 1}`;

      const unidadeCompraEfetiva = (unidade) =>
        lerUnidadeCompraVolume(unidade) ? 'un' : (unidade || 'un');

      const pluralVolumeRevenda = (tipo, qtd = 2) => {
        const singular = Number(qtd) === 1;
        const nomes = {
          caixa: singular ? 'caixa' : 'caixas',
          pacote: singular ? 'pacote' : 'pacotes',
          fardo: singular ? 'fardo' : 'fardos',
          display: singular ? 'display' : 'displays',
          bandeja: singular ? 'bandeja' : 'bandejas',
          outro: singular ? 'volume' : 'volumes'
        };
        return nomes[tipo] || (singular ? 'volume' : 'volumes');
      };

      const numeroCurtoBR = (valor) => Number(valor || 0).toLocaleString('pt-BR', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 3
      });

      const resumoCompraVolume = (compra) => {
        const pacote = lerUnidadeCompraVolume(compra?.purchaseUnit);
        if (!pacote) return '';
        const total = Number(compra?.qty) || 0;
        const volumes = pacote.unidades > 0 ? total / pacote.unidades : 0;
        return `${numeroCurtoBR(volumes)} ${pluralVolumeRevenda(pacote.tipo, volumes)} × ${numeroCurtoBR(pacote.unidades)} un = ${numeroCurtoBR(total)} un`;
      };

      const converterQtdRevenda = (qtd, origem, destino) => {
        const n = Number(qtd) || 0;
        const de = unidadeCompraEfetiva(origem || 'un');
        const para = destino || 'un';'''
if converter_marker not in s:
    raise SystemExit('converterQtdRevenda marker not found')
s = s.replace(converter_marker, helpers_and_converter, 1)

# -----------------------------------------------------------------------------
# 2. Historico/carrinho: revenda por unidade tambem lanca pacote/fardo/caixa.
# -----------------------------------------------------------------------------
modal_sig_old = """        unidadeBase,
        unidadesCompra = null,
        fornecedores = [],"""
modal_sig_new = """        unidadeBase,
        unidadesCompra = null,
        compraPorVolume = false,
        fornecedores = [],"""
if modal_sig_old not in s:
    raise SystemExit('PurchaseHistoryModal signature marker not found')
s = s.replace(modal_sig_old, modal_sig_new, 1)

modal_blank_old = """        const BLANK = {
          supplier: '',
          purchaseDate: getTodayDateString(),
          qty: '',
          purchaseUnit: unidadesCompra ? unidadesCompra[0] : '',
          cost: ''
        };
        const [draft, setDraft] = useState(BLANK);"""
modal_blank_new = """        const pacoteAnterior = lerUnidadeCompraVolume(comprasOrdenadas(compras)[0]?.purchaseUnit);
        const BLANK = {
          supplier: '',
          purchaseDate: getTodayDateString(),
          qty: '',
          purchaseUnit: unidadesCompra ? unidadesCompra[0] : '',
          packageType: pacoteAnterior?.tipo || 'caixa',
          unitsPerPackage: pacoteAnterior?.unidades ? String(pacoteAnterior.unidades) : '',
          cost: ''
        };
        const [draft, setDraft] = useState(BLANK);"""
if modal_blank_old not in s:
    raise SystemExit('PurchaseHistoryModal BLANK marker not found')
s = s.replace(modal_blank_old, modal_blank_new, 1)

modal_save_old = """        const salvar = (e) => {
          e.preventDefault();
          const qty = Number(draft.qty) || 0;
          const cost = Number(draft.cost) || 0;
          if (qty <= 0 || cost <= 0) return;
          onAdd({
            supplier: draft.supplier.trim(),
            purchaseDate: draft.purchaseDate || null,
            qty,
            purchaseUnit: draft.purchaseUnit || undefined,
            cost
          });
          setDraft({ ...BLANK, supplier: draft.supplier, purchaseDate: draft.purchaseDate });
        };"""
modal_save_new = """        const salvar = (e) => {
          e.preventDefault();
          const qtdInformada = Number(draft.qty) || 0;
          const unidadesPorVolume = compraPorVolume ? (Number(draft.unitsPerPackage) || 0) : 0;
          const qty = compraPorVolume ? qtdInformada * unidadesPorVolume : qtdInformada;
          const cost = Number(draft.cost) || 0;
          if (qtdInformada <= 0 || cost <= 0) return;
          if (compraPorVolume && unidadesPorVolume <= 0) {
            window.alert('Informe quantas unidades vêm em cada embalagem.');
            return;
          }
          onAdd({
            supplier: draft.supplier.trim(),
            purchaseDate: draft.purchaseDate || null,
            qty,
            purchaseUnit: compraPorVolume
              ? criarUnidadeCompraVolume(draft.packageType, unidadesPorVolume)
              : (draft.purchaseUnit || undefined),
            cost
          });
          setDraft({ ...BLANK, supplier: draft.supplier, purchaseDate: draft.purchaseDate });
        };"""
if modal_save_old not in s:
    raise SystemExit('PurchaseHistoryModal save marker not found')
s = s.replace(modal_save_old, modal_save_new, 1)

modal_qty_old = """                  <div className={unidadesCompra ? 'col-span-3 sm:col-span-1' : 'col-span-6 sm:col-span-2'}>
                    <label className=\"t-caption block mb-1\">Qtd</label>
                    <input
                      type=\"number\"
                      min=\"0\"
                      step=\"0.001\"
                      value={draft.qty}
                      onChange={(e) => setField('qty', e.target.value)}
                      placeholder={unidadeBase === 'un' ? 'ex: 12' : 'ex: 5000'}
                      title={`Quantidade comprada, em ${unidadeBase}`}
                      className=\"field field-sm text-right tnum no-spin\"
                    />
                  </div>
                  {unidadesCompra && (
                    <div className=\"col-span-3 sm:col-span-2\">
                      <label className=\"t-caption block mb-1\">Unid.</label>
                      <select
                        value={draft.purchaseUnit}
                        onChange={(e) => setField('purchaseUnit', e.target.value)}
                        className=\"field field-sm field-select\"
                      >
                        {unidadesCompra.map((u) => <option key={u} value={u}>{u}</option>)}
                      </select>
                    </div>
                  )}"""
modal_qty_new = """                  <div className={unidadesCompra ? 'col-span-3 sm:col-span-2' : 'col-span-6 sm:col-span-2'}>
                    <label className=\"t-caption block mb-1\">{compraPorVolume ? 'Qtd. volumes' : 'Qtd'}</label>
                    <input
                      type=\"number\"
                      min=\"0\"
                      step=\"0.001\"
                      value={draft.qty}
                      onChange={(e) => setField('qty', e.target.value)}
                      placeholder={compraPorVolume ? 'ex: 2' : (unidadeBase === 'un' ? 'ex: 12' : 'ex: 5000')}
                      title={compraPorVolume ? 'Quantidade de caixas, pacotes, fardos ou outros volumes comprados' : `Quantidade comprada, em ${unidadeBase}`}
                      className=\"field field-sm text-right tnum no-spin\"
                    />
                  </div>
                  {compraPorVolume ? (
                    <>
                      <div className=\"col-span-3 sm:col-span-2\">
                        <label className=\"t-caption block mb-1\">Embalagem</label>
                        <select
                          value={draft.packageType}
                          onChange={(e) => setField('packageType', e.target.value)}
                          className=\"field field-sm field-select\"
                        >
                          {TIPOS_VOLUME_REVENDA.map((x) => <option key={x.value} value={x.value}>{x.label}</option>)}
                        </select>
                      </div>
                      <div className=\"col-span-3 sm:col-span-2\">
                        <label className=\"t-caption block mb-1\">Un./volume</label>
                        <input
                          type=\"number\"
                          min=\"1\"
                          step=\"1\"
                          value={draft.unitsPerPackage}
                          onChange={(e) => setField('unitsPerPackage', e.target.value)}
                          placeholder={pacoteAnterior?.unidades ? String(pacoteAnterior.unidades) : 'ex: 12'}
                          className=\"field field-sm text-right tnum no-spin\"
                        />
                      </div>
                    </>
                  ) : unidadesCompra && (
                    <div className=\"col-span-3 sm:col-span-2\">
                      <label className=\"t-caption block mb-1\">Unid.</label>
                      <select
                        value={draft.purchaseUnit}
                        onChange={(e) => setField('purchaseUnit', e.target.value)}
                        className=\"field field-sm field-select\"
                      >
                        {unidadesCompra.map((u) => <option key={u} value={u}>{u}</option>)}
                      </select>
                    </div>
                  )}"""
if modal_qty_old not in s:
    raise SystemExit('PurchaseHistoryModal quantity block not found')
s = s.replace(modal_qty_old, modal_qty_new, 1)

history_unit_old = '<span className="t-micro">{c.purchaseUnit || unidadeBase}</span>'
history_unit_new = '''<span className="t-micro max-w-44 text-right">{resumoCompraVolume(c) || unidadeCompraEfetiva(c.purchaseUnit || unidadeBase)}</span>'''
if history_unit_old not in s:
    raise SystemExit('history purchase unit display not found')
s = s.replace(history_unit_old, history_unit_new, 1)

history_cost_old = '{formatPrecoInsumo(custoUnitDe(c), c.purchaseUnit || unidadeBase)}'
history_cost_new = '{formatPrecoInsumo(custoUnitDe(c), unidadeCompraEfetiva(c.purchaseUnit || unidadeBase))}'
if history_cost_old not in s:
    raise SystemExit('history cost unit display not found')
s = s.replace(history_cost_old, history_cost_new, 1)

caller_old = """                  unidadeBase={item.priceUnit || 'un'}
                  unidadesCompra={['un', 'kg', 'g']}
                  fornecedores={fornecedores}"""
caller_new = """                  unidadeBase={item.priceUnit || 'un'}
                  unidadesCompra={['un', 'kg', 'g']}
                  compraPorVolume={(item.priceUnit || 'un') === 'un'}
                  fornecedores={fornecedores}"""
if caller_old not in s:
    raise SystemExit('resale PurchaseHistoryModal caller not found')
s = s.replace(caller_old, caller_new, 1)

# -----------------------------------------------------------------------------
# 3. Entrada principal: campos fixos para volumes quando a revenda vende por un.
# -----------------------------------------------------------------------------
blank_old = """          cost: '',
          purchaseUnit: 'un',
          responsible: '',"""
blank_new = """          cost: '',
          purchaseUnit: 'un',
          packageType: 'caixa',
          unitsPerPackage: '',
          responsible: '',"""
if blank_old not in s:
    raise SystemExit('BLANK_ENTRY package marker not found')
s = s.replace(blank_old, blank_new, 1)

flags_old = """        const temInsumo = !modoProducao && (tipoCompra === 'insumo' || tipoCompra === 'insumo_revenda');
        const temRevenda = !modoProducao && (tipoCompra === 'revenda' || tipoCompra === 'insumo_revenda');
        const tipoCadastroAtual = modoProducao"""
flags_new = """        const temInsumo = !modoProducao && (tipoCompra === 'insumo' || tipoCompra === 'insumo_revenda');
        const temRevenda = !modoProducao && (tipoCompra === 'revenda' || tipoCompra === 'insumo_revenda');
        const compraPorVolume = temRevenda && (draft.priceUnit || 'un') === 'un';
        const tipoCadastroAtual = modoProducao"""
if flags_old not in s:
    raise SystemExit('unified entry flags marker not found')
s = s.replace(flags_old, flags_new, 1)

compra_exist_old = """        const compraExistente = !modoProducao
          ? ultimaCompra([
              ...(supplyExistente ? comprasDoInsumo(supplyExistente.id) : []),
              ...(revendaExistente ? comprasDaRevenda(revendaExistente.id) : [])
            ])
          : null;

        const unidadeBaseDaRevenda"""
compra_exist_new = """        const compraExistente = !modoProducao
          ? ultimaCompra([
              ...(supplyExistente ? comprasDoInsumo(supplyExistente.id) : []),
              ...(revendaExistente ? comprasDaRevenda(revendaExistente.id) : [])
            ])
          : null;
        const compraRevendaExistente = revendaExistente
          ? ultimaCompra(comprasDaRevenda(revendaExistente.id))
          : null;
        const volumeAnterior = lerUnidadeCompraVolume(compraRevendaExistente?.purchaseUnit);

        const unidadeBaseDaRevenda"""
if compra_exist_old not in s:
    raise SystemExit('compraExistente marker not found')
s = s.replace(compra_exist_old, compra_exist_new, 1)

select_supply_old = """            const rev = revendaDaUnidade.find((r) => normalizeName(r.productName) === normalizeName(x.name));
            const usoInterno = x.supplyClass === 'embalagem' || x.supplyClass === 'limpeza';
            setDraft((d) => ({"""
select_supply_new = """            const rev = revendaDaUnidade.find((r) => normalizeName(r.productName) === normalizeName(x.name));
            const compraRev = rev ? ultimaCompra(comprasDaRevenda(rev.id)) : null;
            const volumeRev = lerUnidadeCompraVolume(compraRev?.purchaseUnit);
            const usoInterno = x.supplyClass === 'embalagem' || x.supplyClass === 'limpeza';
            setDraft((d) => ({"""
if select_supply_old not in s:
    raise SystemExit('select existing supply marker not found')
s = s.replace(select_supply_old, select_supply_new, 1)

select_supply_fields_old = """              priceUnit: rev?.priceUnit || d.priceUnit || 'un',
              purchaseUnit: rev?.priceUnit || d.purchaseUnit || x.unit || 'un',
              resaleCategory: rev?.category || d.resaleCategory || 'revenda'"""
select_supply_fields_new = """              priceUnit: rev?.priceUnit || d.priceUnit || 'un',
              purchaseUnit: volumeRev ? 'un' : (rev?.priceUnit || d.purchaseUnit || x.unit || 'un'),
              packageType: volumeRev?.tipo || d.packageType || 'caixa',
              unitsPerPackage: volumeRev?.unidades ? String(volumeRev.unidades) : d.unitsPerPackage,
              resaleCategory: rev?.category || d.resaleCategory || 'revenda'"""
if select_supply_fields_old not in s:
    raise SystemExit('select existing supply fields marker not found')
s = s.replace(select_supply_fields_old, select_supply_fields_new, 1)

select_resale_old = """            const ins = supplies.find((i) => normalizeName(i.name) === normalizeName(x.productName));
            setDraft((d) => ({"""
select_resale_new = """            const ins = supplies.find((i) => normalizeName(i.name) === normalizeName(x.productName));
            const compraRev = ultimaCompra(comprasDaRevenda(x.id));
            const volumeRev = lerUnidadeCompraVolume(compraRev?.purchaseUnit);
            setDraft((d) => ({"""
if select_resale_old not in s:
    raise SystemExit('select existing resale marker not found')
s = s.replace(select_resale_old, select_resale_new, 1)

select_resale_fields_old = """              priceUnit: x.priceUnit || 'un',
              purchaseUnit: x.priceUnit || 'un',
              resaleCategory: x.category || 'revenda'"""
select_resale_fields_new = """              priceUnit: x.priceUnit || 'un',
              purchaseUnit: volumeRev ? 'un' : (x.priceUnit || 'un'),
              packageType: volumeRev?.tipo || d.packageType || 'caixa',
              unitsPerPackage: volumeRev?.unidades ? String(volumeRev.unidades) : d.unitsPerPackage,
              resaleCategory: x.category || 'revenda'"""
if select_resale_fields_old not in s:
    raise SystemExit('select existing resale fields marker not found')
s = s.replace(select_resale_fields_old, select_resale_fields_new, 1)

save_qty_old = """          const qty = Number(draft.qty) || 0;
          const cost = Number(draft.cost) || 0;
          if ((qty > 0 || cost > 0) && !(qty > 0 && cost > 0)) {
            window.alert('Para registrar a compra, preencha quantidade e valor pago.');
            return;
          }"""
save_qty_new = """          const qtdInformada = Number(draft.qty) || 0;
          const cost = Number(draft.cost) || 0;
          const unidadesPorVolume = compraPorVolume
            ? (Number(draft.unitsPerPackage) || Number(volumeAnterior?.unidades) || 0)
            : 0;
          const tipoVolume = draft.packageType || volumeAnterior?.tipo || 'caixa';
          const qty = compraPorVolume ? qtdInformada * unidadesPorVolume : qtdInformada;
          const unidadeCompraSalva = compraPorVolume
            ? criarUnidadeCompraVolume(tipoVolume, unidadesPorVolume)
            : (draft.purchaseUnit || draft.priceUnit || draft.unit || 'un');
          if ((qtdInformada > 0 || cost > 0) && !(qtdInformada > 0 && cost > 0)) {
            window.alert('Para registrar a compra, preencha quantidade e valor pago.');
            return;
          }
          if (compraPorVolume && qtdInformada > 0 && cost > 0 && unidadesPorVolume <= 0) {
            window.alert('Informe quantas unidades vêm em cada embalagem.');
            return;
          }"""
if save_qty_old not in s:
    raise SystemExit('save quantity marker not found')
s = s.replace(save_qty_old, save_qty_new, 1)

supply_qtd_old = "? qtdCompraNaBase(qty, draft.purchaseUnit || draft.unit, insumo.unit || draft.unit)"
supply_qtd_new = "? qtdCompraNaBase(qty, unidadeCompraEfetiva(unidadeCompraSalva), insumo.unit || draft.unit)"
if supply_qtd_old not in s:
    raise SystemExit('hybrid supply quantity conversion marker not found')
s = s.replace(supply_qtd_old, supply_qtd_new, 1)

resale_purchase_unit_old = "purchaseUnit: draft.purchaseUnit || draft.priceUnit || 'un',"
resale_purchase_unit_new = "purchaseUnit: unidadeCompraSalva,"
if resale_purchase_unit_old not in s:
    raise SystemExit('resale purchase unit save marker not found')
s = s.replace(resale_purchase_unit_old, resale_purchase_unit_new, 1)

reset_old = """            priceUnit: d.priceUnit,
            purchaseUnit: d.purchaseUnit,
            resaleCategory: d.resaleCategory,"""
reset_new = """            priceUnit: d.priceUnit,
            purchaseUnit: d.purchaseUnit,
            packageType: d.packageType || 'caixa',
            unitsPerPackage: d.unitsPerPackage,
            resaleCategory: d.resaleCategory,"""
if reset_old not in s:
    raise SystemExit('unified entry reset marker not found')
s = s.replace(reset_old, reset_new, 1)

# Main form quantity label / placeholder.
qty_label_old = '<label className="t-caption block mb-1">Qtd. comprada{temInsumo && !temRevenda ? ` (${draft.unit})` : \'\'}</label>'
qty_label_new = '<label className="t-caption block mb-1">{compraPorVolume ? \'Qtd. volumes\' : `Qtd. comprada${temInsumo && !temRevenda ? ` (${draft.unit})` : \'\'}`}</label>'
if qty_label_old not in s:
    raise SystemExit('main quantity label not found')
s = s.replace(qty_label_old, qty_label_new, 1)

qty_placeholder_old = "placeholder={compraExistente?.qty ? Number(compraExistente.qty).toLocaleString('pt-BR', { maximumFractionDigits: 3 }) : '0'}"
qty_placeholder_new = """placeholder={compraPorVolume && volumeAnterior?.unidades && compraRevendaExistente?.qty
                            ? numeroCurtoBR((Number(compraRevendaExistente.qty) || 0) / Number(volumeAnterior.unidades))
                            : (compraExistente?.qty ? Number(compraExistente.qty).toLocaleString('pt-BR', { maximumFractionDigits: 3 }) : '0')}"""
if qty_placeholder_old not in s:
    raise SystemExit('main quantity placeholder not found')
s = s.replace(qty_placeholder_old, qty_placeholder_new, 1)

unit_select_old = """                        <select
                          value={temInsumo && !temRevenda ? draft.unit : draft.purchaseUnit}
                          disabled={modoProducao || (temInsumo && !temRevenda)}
                          onChange={(e) => setDraft((d) => ({ ...d, purchaseUnit: e.target.value }))}
                          className=\"field field-md field-select disabled:opacity-50\"
                        >
                          {['un', 'kg', 'g', 'L', 'ml'].map((u) => <option key={u} value={u}>{u}</option>)}
                        </select>
                      </div>

                      <div className=\"col-span-8 sm:col-span-3 lg:col-span-2\">
                        <label className=\"t-caption block mb-1\">Valor pago</label>"""
unit_select_new = """                        <select
                          value={compraPorVolume ? 'un' : (temInsumo && !temRevenda ? draft.unit : draft.purchaseUnit)}
                          disabled={modoProducao || compraPorVolume || (temInsumo && !temRevenda)}
                          onChange={(e) => setDraft((d) => ({ ...d, purchaseUnit: e.target.value }))}
                          className=\"field field-md field-select disabled:opacity-50\"
                        >
                          {['un', 'kg', 'g', 'L', 'ml'].map((u) => <option key={u} value={u}>{u}</option>)}
                        </select>
                      </div>

                      <div className=\"col-span-4 sm:col-span-3 lg:col-span-1\">
                        <label className=\"t-caption block mb-1\">Embalagem</label>
                        <select
                          value={compraPorVolume ? draft.packageType : ''}
                          disabled={!compraPorVolume}
                          onChange={(e) => setDraft((d) => ({ ...d, packageType: e.target.value }))}
                          className=\"field field-md field-select disabled:opacity-50\"
                        >
                          {!compraPorVolume && <option value=\"\">—</option>}
                          {TIPOS_VOLUME_REVENDA.map((x) => <option key={x.value} value={x.value}>{x.label}</option>)}
                        </select>
                      </div>

                      <div className=\"col-span-4 sm:col-span-3 lg:col-span-1\">
                        <label className=\"t-caption block mb-1\">Un./volume</label>
                        <NumeroBRField
                          value={compraPorVolume ? draft.unitsPerPackage : ''}
                          disabled={!compraPorVolume}
                          decimals={0}
                          onValueChange={(unitsPerPackage) => setDraft((d) => ({ ...d, unitsPerPackage }))}
                          placeholder={volumeAnterior?.unidades ? numeroCurtoBR(volumeAnterior.unidades) : 'ex: 12'}
                          className=\"field field-md text-right tnum disabled:opacity-50\"
                        />
                      </div>

                      <div className=\"col-span-8 sm:col-span-3 lg:col-span-2\">
                        <label className=\"t-caption block mb-1\">Valor pago</label>"""
if unit_select_old not in s:
    raise SystemExit('main purchase unit block not found')
s = s.replace(unit_select_old, unit_select_new, 1)

# Move sale price/unit to the third row so row 2 remains readable with package fields.
price_blocks = """

                      <div className=\"col-span-4 sm:col-span-3 lg:col-span-1\">
                        <label className=\"t-caption block mb-1\">Preço venda</label>
                        <NumeroBRField
                          value={modoProducao || temRevenda ? draft.price : ''}
                          disabled={!modoProducao && !temRevenda}
                          decimals={2}
                          fixedDecimals={true}
                          onValueChange={(price) => setDraft((d) => ({ ...d, price }))}
                          placeholder=\"0,00\"
                          className=\"field field-md text-right tnum disabled:opacity-50\"
                        />
                      </div>

                      <div className=\"col-span-4 sm:col-span-3 lg:col-span-1\">
                        <label className=\"t-caption block mb-1\">Vende por</label>
                        <select
                          value={modoProducao || temRevenda ? draft.priceUnit : ''}
                          disabled={!modoProducao && !temRevenda}
                          onChange={(e) => setDraft((d) => ({ ...d, priceUnit: e.target.value }))}
                          className=\"field field-md field-select disabled:opacity-50\"
                        >
                          {!modoProducao && !temRevenda && <option value=\"\">—</option>}
                          <option value=\"un\">un</option>
                          <option value=\"kg\">kg</option>
                          {!modoProducao && <option value=\"g\">g</option>}
                        </select>
                      </div>"""
if price_blocks not in s:
    raise SystemExit('price/vende blocks not found')
s = s.replace(price_blocks, '', 1)

third_row_marker = """                      <div className=\"col-span-6 sm:col-span-9 lg:col-span-7\">
                        <div className=\"rounded-xl bg-black/[0.035] px-3 py-2 t-micro min-h-11 flex items-center\">"""
third_row_replacement = """                      <div className=\"col-span-4 sm:col-span-3 lg:col-span-1\">
                        <label className=\"t-caption block mb-1\">Preço venda</label>
                        <NumeroBRField
                          value={modoProducao || temRevenda ? draft.price : ''}
                          disabled={!modoProducao && !temRevenda}
                          decimals={2}
                          fixedDecimals={true}
                          onValueChange={(price) => setDraft((d) => ({ ...d, price }))}
                          placeholder=\"0,00\"
                          className=\"field field-md text-right tnum disabled:opacity-50\"
                        />
                      </div>
                      <div className=\"col-span-4 sm:col-span-3 lg:col-span-1\">
                        <label className=\"t-caption block mb-1\">Vende por</label>
                        <select
                          value={modoProducao || temRevenda ? draft.priceUnit : ''}
                          disabled={!modoProducao && !temRevenda}
                          onChange={(e) => setDraft((d) => ({ ...d, priceUnit: e.target.value }))}
                          className=\"field field-md field-select disabled:opacity-50\"
                        >
                          {!modoProducao && !temRevenda && <option value=\"\">—</option>}
                          <option value=\"un\">un</option>
                          <option value=\"kg\">kg</option>
                          {!modoProducao && <option value=\"g\">g</option>}
                        </select>
                      </div>
                      <div className=\"col-span-12 sm:col-span-6 lg:col-span-5\">
                        <div className=\"rounded-xl bg-black/[0.035] px-3 py-2 t-micro min-h-11 flex items-center\">"""
if third_row_marker not in s:
    raise SystemExit('third row helper marker not found')
s = s.replace(third_row_marker, third_row_replacement, 1)

helper_revenda_old = """                                  : temRevenda
                                    ? 'Revenda: a compra alimenta diretamente custo e CMV.'
                                    : 'Insumo: a compra alimenta o custo usado nas fichas técnicas.'}"""
helper_revenda_new = """                                  : temRevenda
                                    ? (compraPorVolume
                                      ? (() => {
                                          const volumes = Number(draft.qty) || 0;
                                          const porVolume = Number(draft.unitsPerPackage) || Number(volumeAnterior?.unidades) || 0;
                                          const total = volumes * porVolume;
                                          const custoUn = total > 0 ? (Number(draft.cost) || 0) / total : 0;
                                          const calculo = total > 0
                                            ? ` · ${numeroCurtoBR(volumes)} ${pluralVolumeRevenda(draft.packageType || volumeAnterior?.tipo || 'caixa', volumes)} × ${numeroCurtoBR(porVolume)} = ${numeroCurtoBR(total)} un${custoUn > 0 ? ` · ${formatCurrencyBR(custoUn)}/un` : ''}`
                                            : '';
                                          return `Revenda por unidade: informe os volumes comprados e quantas unidades vêm em cada embalagem${calculo}.`;
                                        })()
                                      : 'Revenda: a compra alimenta diretamente custo e CMV.')
                                    : 'Insumo: a compra alimenta o custo usado nas fichas técnicas.'}"""
if helper_revenda_old not in s:
    raise SystemExit('revenda helper text marker not found')
s = s.replace(helper_revenda_old, helper_revenda_new, 1)

# Master table: encoded package should never appear as raw pack:caixa:50.
row_vars_old = """                          const x = linha.source;
                          const c = linha.compra;
                          const ehSupply"""
row_vars_new = """                          const x = linha.source;
                          const c = linha.compra;
                          const volumeCompraLinha = c ? lerUnidadeCompraVolume(c.purchaseUnit) : null;
                          const ehSupply"""
if row_vars_old not in s:
    raise SystemExit('master table row vars marker not found')
s = s.replace(row_vars_old, row_vars_new, 1)

master_qty_old = """                                    <input type=\"number\" min=\"0\" step=\"0.001\" value={c?.qty || ''} onChange={(e) => atualizarCompraLinha(linha,{qty:Number(e.target.value)||0})} className=\"field h-8 px-2 text-[12px] text-right tnum no-spin w-20\" />
                                    {linha.tipo === 'revenda' || (linha.tipo === 'insumo_revenda' && linha.compraOrigem === 'revenda') ? (
                                      <div className=\"w-14\"><PickerField value={c?.purchaseUnit || (linha.resaleSource || x).priceUnit || 'un'} options={[{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]} onPick={(opt) => atualizarCompraLinha(linha,{purchaseUnit:opt.value})} className=\"field h-8 pl-2 text-[11px]\" /></div>
                                    ) : <span className=\"t-micro\">{x.unit}</span>}"""
master_qty_new = """                                    {volumeCompraLinha ? (
                                      <div className=\"min-w-[170px] text-right\">
                                        <div className=\"t-micro font-semibold whitespace-nowrap\">{resumoCompraVolume(c)}</div>
                                        <div className=\"t-nano\">total comprado</div>
                                      </div>
                                    ) : (
                                      <>
                                        <input type=\"number\" min=\"0\" step=\"0.001\" value={c?.qty || ''} onChange={(e) => atualizarCompraLinha(linha,{qty:Number(e.target.value)||0})} className=\"field h-8 px-2 text-[12px] text-right tnum no-spin w-20\" />
                                        {linha.tipo === 'revenda' || (linha.tipo === 'insumo_revenda' && linha.compraOrigem === 'revenda') ? (
                                          <div className=\"w-14\"><PickerField value={unidadeCompraEfetiva(c?.purchaseUnit || (linha.resaleSource || x).priceUnit || 'un')} options={[{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]} onPick={(opt) => atualizarCompraLinha(linha,{purchaseUnit:opt.value})} className=\"field h-8 pl-2 text-[11px]\" /></div>
                                        ) : <span className=\"t-micro\">{x.unit}</span>}
                                      </>
                                    )}"""
if master_qty_old not in s:
    raise SystemExit('master table quantity purchase block not found')
s = s.replace(master_qty_old, master_qty_new, 1)

required = [
    '2026-09-05-revenda-compra-volume-1',
    "const lerUnidadeCompraVolume = (valor) => {",
    "pack:${String(tipo || 'caixa').toLowerCase()}",
    "const compraPorVolume = temRevenda && (draft.priceUnit || 'un') === 'un';",
    "packageType: 'caixa'",
    "unitsPerPackage: ''",
    "Qtd. volumes",
    "Un./volume",
    "compraPorVolume={(item.priceUnit || 'un') === 'un'}",
    "purchaseUnit: unidadeCompraSalva",
    "resumoCompraVolume(c) || unidadeCompraEfetiva"
]
for marker in required:
    if marker not in s:
        raise SystemExit(f'missing required marker: {marker}')

p.write_text(s, encoding='utf-8')
