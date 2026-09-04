from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# ------------------------------------------------------------------
# Versão
# ------------------------------------------------------------------
s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-04-cadastros-mestre-copiar-ficha-1" />',
    s,
    count=1,
)
assert n == 1

# ------------------------------------------------------------------
# Props da tela mestre
# ------------------------------------------------------------------
old = """        onAddRecipeItem,
        onUpdateRecipeItem,
        onDeleteRecipeItem,
        onUpdateSeparatedProduct,"""
new = """        onAddRecipeItem,
        onUpdateRecipeItem,
        onDeleteRecipeItem,
        onCopyRecipe,
        onUpdateSeparatedProduct,"""
assert old in s
s = s.replace(old, new, 1)

old = """        onDeleteResalePurchase,
        onChangeCatalogType
      }) => {"""
new = """        onDeleteResalePurchase,
        onChangeCatalogType,
        onDeleteCatalogItem
      }) => {"""
assert old in s
s = s.replace(old, new, 1)

# Estado para copiar ficha
old = """        // Produto cuja ficha está aberta
        const [fichaProdutoId, setFichaProdutoId] = useState(null);

        // A tabela continua distinguindo os três tipos."""
new = """        // Produto cuja ficha está aberta
        const [fichaProdutoId, setFichaProdutoId] = useState(null);
        // Copiar uma ficha pronta para outro produto sem remontar insumo por insumo
        const [copiarFichaDe, setCopiarFichaDe] = useState(null);
        const [produtoDestinoCopia, setProdutoDestinoCopia] = useState('');
        const [copiandoFicha, setCopiandoFicha] = useState(false);

        // A tabela mestre distingue cadastro, classe e finalidade operacional."""
assert old in s
s = s.replace(old, new, 1)

# Tipos: embalagem e limpeza viram escolha direta; não exigem uma segunda classificação
old = """        const TIPOS_ENTRADA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'insumo_revenda', label: 'Insumo + revenda' },
          { value: 'producao', label: 'Produção' }
        ];
        const TIPOS_TABELA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'insumo_revenda', label: 'Insumo + revenda' },
          { value: 'producao', label: 'Produção' }
        ];"""
new = """        const TIPOS_ENTRADA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'insumo_revenda', label: 'Insumo + revenda' },
          { value: 'embalagem', label: 'Embalagem' },
          { value: 'limpeza', label: 'Limpeza' },
          { value: 'producao', label: 'Produção' }
        ];
        const TIPOS_TABELA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'insumo_revenda', label: 'Insumo + revenda' },
          { value: 'embalagem', label: 'Embalagem' },
          { value: 'limpeza', label: 'Limpeza' },
          { value: 'producao', label: 'Produção' }
        ];"""
assert old in s
s = s.replace(old, new, 1)

# Tipo atual: embalagem/limpeza vêm da classe e não de uma pergunta de revenda
old = """        const modoProducao = draft.type === 'producao';
        const tipoCompra = draft.purchaseKind || (draft.resaleAlso ? 'insumo_revenda' : 'insumo');
        const temInsumo = !modoProducao && (tipoCompra === 'insumo' || tipoCompra === 'insumo_revenda');
        const temRevenda = !modoProducao && (tipoCompra === 'revenda' || tipoCompra === 'insumo_revenda');
        const tipoCadastroAtual = modoProducao ? 'producao' : tipoCompra;"""
new = """        const modoProducao = draft.type === 'producao';
        const tipoCompra = draft.purchaseKind || (draft.resaleAlso ? 'insumo_revenda' : 'insumo');
        const classeInterna = draft.supplyClass === 'embalagem' || draft.supplyClass === 'limpeza';
        const temInsumo = !modoProducao && (tipoCompra === 'insumo' || tipoCompra === 'insumo_revenda');
        const temRevenda = !modoProducao && (tipoCompra === 'revenda' || tipoCompra === 'insumo_revenda');
        const tipoCadastroAtual = modoProducao
          ? 'producao'
          : (classeInterna && tipoCompra === 'insumo' ? draft.supplyClass : tipoCompra);"""
assert old in s
s = s.replace(old, new, 1)

# Carregar embalagem/limpeza já existentes como uso interno, mesmo que haja resíduo antigo de revenda
old = """            const rev = revendaDaUnidade.find((r) => normalizeName(r.productName) === normalizeName(x.name));
            setDraft((d) => ({
              ...d,
              type: 'insumo',
              purchaseKind: rev ? 'insumo_revenda' : 'insumo',
              name: x.name,
              unit: x.unit || 'g',
              supplyClass: x.supplyClass || 'insumo',
              variationUnit: x.variationUnit || '',
              variationFactor: x.variationFactor || '',
              resaleAlso: !!rev,"""
new = """            const rev = revendaDaUnidade.find((r) => normalizeName(r.productName) === normalizeName(x.name));
            const usoInterno = x.supplyClass === 'embalagem' || x.supplyClass === 'limpeza';
            setDraft((d) => ({
              ...d,
              type: 'insumo',
              purchaseKind: usoInterno ? 'insumo' : (rev ? 'insumo_revenda' : 'insumo'),
              name: x.name,
              unit: x.unit || 'g',
              supplyClass: x.supplyClass || 'insumo',
              variationUnit: x.variationUnit || '',
              variationFactor: x.variationFactor || '',
              resaleAlso: usoInterno ? false : !!rev,"""
assert old in s
s = s.replace(old, new, 1)

# Reset mantém embalagem/limpeza corretamente
old = """            purchaseKind: d.purchaseKind || 'insumo',
            resaleAlso: (d.purchaseKind || 'insumo') === 'insumo_revenda',
            unit: d.unit,
            supplyClass: d.supplyClass,"""
new = """            purchaseKind: (d.supplyClass === 'embalagem' || d.supplyClass === 'limpeza') ? 'insumo' : (d.purchaseKind || 'insumo'),
            resaleAlso: (d.supplyClass === 'embalagem' || d.supplyClass === 'limpeza') ? false : (d.purchaseKind || 'insumo') === 'insumo_revenda',
            unit: d.unit,
            supplyClass: d.supplyClass,"""
assert old in s
s = s.replace(old, new, 1)

# ------------------------------------------------------------------
# Tabela unificada: embalagem/limpeza têm tipo próprio
# ------------------------------------------------------------------
old = """          const insumos = supplies.map((x) => {
            const rev = revendaDaUnidade.find(
              (r) => normalizeName(r.productName) === normalizeName(x.name)
            );
            const compraInsumo = ultimaCompra(comprasDoInsumo(x.id));
            if (!rev) {
              return {
                key: `insumo:${x.id}`,
                tipo: 'insumo', id: x.id, name: x.name, source: x,
                unidade: x.unit || 'g', compra: compraInsumo, compraOrigem: 'insumo',
                custo: custoUnitarioInsumo(x.id, supplyPurchases)
              };
            }"""
new = """          const insumos = supplies.map((x) => {
            const tipoBase = x.supplyClass === 'embalagem'
              ? 'embalagem'
              : x.supplyClass === 'limpeza' ? 'limpeza' : 'insumo';
            // Embalagem e limpeza são uso interno; não viram híbrido por acaso.
            const rev = tipoBase === 'insumo'
              ? revendaDaUnidade.find((r) => normalizeName(r.productName) === normalizeName(x.name))
              : null;
            const compraInsumo = ultimaCompra(comprasDoInsumo(x.id));
            if (!rev) {
              return {
                key: `${tipoBase}:${x.id}`,
                tipo: tipoBase, id: x.id, name: x.name, source: x,
                unidade: x.unit || 'g', compra: compraInsumo, compraOrigem: 'insumo',
                custo: custoUnitarioInsumo(x.id, supplyPurchases)
              };
            }"""
assert old in s
s = s.replace(old, new, 1)

old = """          const revendas = revendaDaUnidade
            .filter((x) => !supplies.some((s) => normalizeName(s.name) === normalizeName(x.productName)))"""
new = """          const revendas = revendaDaUnidade
            .filter((x) => !supplies.some((s) => s.supplyClass === 'insumo' && normalizeName(s.name) === normalizeName(x.productName)))"""
assert old in s
s = s.replace(old, new, 1)

# ------------------------------------------------------------------
# Troca de tipo na tabela: classe interna é uma troca simples do supply_class
# ------------------------------------------------------------------
marker = """        const alterarTipoDaTabela = async (linha, novoTipo) => {
          if (!novoTipo || novoTipo === linha.tipo) return;

          if (novoTipo === 'insumo_revenda') {"""
replacement = """        const alterarTipoDaTabela = async (linha, novoTipo) => {
          if (!novoTipo || novoTipo === linha.tipo) return;

          const tiposSupply = ['insumo', 'embalagem', 'limpeza'];
          if (tiposSupply.includes(novoTipo)) {
            const novaClasse = novoTipo === 'insumo' ? 'insumo' : novoTipo;
            if (tiposSupply.includes(linha.tipo)) {
              return onUpdateSupply({ ...linha.source, supplyClass: novaClasse });
            }
            if (linha.tipo === 'insumo_revenda') {
              onSetSupplyResale(linha.source, false);
              return onUpdateSupply({ ...linha.source, supplyClass: novaClasse });
            }
            if (linha.tipo === 'revenda' && novoTipo !== 'insumo') {
              window.alert('Transforme a revenda em Insumo primeiro; depois escolha Embalagem ou Limpeza. Assim o histórico da compra é preservado.');
              return;
            }
            if (linha.tipo === 'producao' && novoTipo !== 'insumo') {
              window.alert('Transforme o produto em Insumo primeiro; depois escolha Embalagem ou Limpeza.');
              return;
            }
          }

          if (tiposSupply.includes(linha.tipo) && linha.tipo !== 'insumo') {
            const comoInsumo = { ...linha, tipo: 'insumo', source: { ...linha.source, supplyClass: 'insumo' } };
            if (novoTipo === 'insumo_revenda') {
              onUpdateSupply({ ...linha.source, supplyClass: 'insumo' });
              return onSetSupplyResale({ ...linha.source, supplyClass: 'insumo' }, true);
            }
            return onChangeCatalogType(comoInsumo, novoTipo);
          }

          if (novoTipo === 'insumo_revenda') {"""
assert marker in s
s = s.replace(marker, replacement, 1)

# ------------------------------------------------------------------
# Seletor do formulário: Embalagem/Limpeza já definem a classe
# ------------------------------------------------------------------
old = """                          onClick={() => setDraft((d) => tipo.value === 'producao'
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
                              })}"""
new = """                          onClick={() => setDraft((d) => tipo.value === 'producao'
                            ? {
                                ...BLANK_ENTRY,
                                type: 'producao',
                                productCategory: d.productCategory,
                                priceUnit: d.priceUnit,
                                purchaseDate: getTodayDateString()
                              }
                            : (tipo.value === 'embalagem' || tipo.value === 'limpeza')
                              ? {
                                  ...BLANK_ENTRY,
                                  type: 'insumo',
                                  purchaseKind: 'insumo',
                                  resaleAlso: false,
                                  unit: d.unit,
                                  supplyClass: tipo.value,
                                  priceUnit: d.priceUnit,
                                  purchaseUnit: d.purchaseUnit,
                                  resaleCategory: d.resaleCategory,
                                  purchaseDate: getTodayDateString()
                                }
                              : {
                                  ...BLANK_ENTRY,
                                  type: 'insumo',
                                  purchaseKind: tipo.value,
                                  resaleAlso: tipo.value === 'insumo_revenda',
                                  unit: d.unit,
                                  supplyClass: 'insumo',
                                  priceUnit: d.priceUnit,
                                  purchaseUnit: d.purchaseUnit,
                                  resaleCategory: d.resaleCategory,
                                  purchaseDate: getTodayDateString()
                                })}"""
assert old in s
s = s.replace(old, new, 1)

# Remove o seletor redundante Classe e deixa só a classificação já escolhida no topo
old = """                          <div className="col-span-8 lg:col-span-3">
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
                          </div>"""
new = """                          <div className="col-span-8 lg:col-span-3">
                            <label className="t-caption block mb-1">Classificação</label>
                            <div className="field field-md flex items-center px-3 bg-black/[0.035] t-callout font-semibold">
                              {draft.supplyClass === 'embalagem'
                                ? 'Embalagem · uso interno'
                                : draft.supplyClass === 'limpeza'
                                  ? 'Material de limpeza · uso interno'
                                  : tipoCompra === 'insumo_revenda'
                                    ? 'Insumo + revenda'
                                    : 'Insumo'}
                            </div>
                          </div>"""
assert old in s
s = s.replace(old, new, 1)

# Texto da tela
s = s.replace(
    'Escolha o tipo acima. Revenda apenas e Insumo + revenda usam a mesma linha de compra, sem cadastro duplicado.',
    'Escolha o que o item é. Embalagem e Limpeza já são uso interno; Revenda e Insumo + revenda usam a mesma linha de compra.',
    1,
)

# ------------------------------------------------------------------
# Tabela mestre: preço + detalhes completos + ações/remover
# ------------------------------------------------------------------
old = """                          <th className="py-3 px-3 text-right font-bold">Custo</th>
                          <th className="py-3 pl-3 font-bold">Detalhes</th>
                        </tr>"""
new = """                          <th className="py-3 px-3 text-right font-bold">Custo</th>
                          <th className="py-3 px-3 font-bold">Preço venda</th>
                          <th className="py-3 px-3 font-bold">Detalhes</th>
                          <th className="py-3 pl-3 text-right font-bold">Ações</th>
                        </tr>"""
assert old in s
s = s.replace(old, new, 1)
s = s.replace('<tr><td colSpan={10} className="text-center py-10"><p className="t-body ink-quiet">Nenhum cadastro encontrado</p></td></tr>', '<tr><td colSpan={12} className="text-center py-10"><p className="t-body ink-quiet">Nenhum cadastro encontrado</p></td></tr>', 1)

old = """                          const x = linha.source;
                          const c = linha.compra;
                          return ("""
new = """                          const x = linha.source;
                          const c = linha.compra;
                          const ehSupply = ['insumo', 'embalagem', 'limpeza', 'insumo_revenda'].includes(linha.tipo);
                          const venda = linha.tipo === 'insumo_revenda'
                            ? linha.resaleSource
                            : (linha.tipo === 'revenda' || linha.tipo === 'producao' ? x : null);
                          const comprasLinha = linha.tipo === 'revenda'
                            ? comprasDaRevenda(x.id)
                            : linha.tipo === 'producao' ? [] : comprasDoInsumo(x.id);
                          return ("""
assert old in s
s = s.replace(old, new, 1)

# Unidade e equivalência passam a considerar embalagem/limpeza também
s = s.replace("{linha.tipo === 'insumo' || linha.tipo === 'insumo_revenda' ? (", "{ehSupply ? (", 2)

# Substitui a célula Detalhes antiga por Preço + Detalhes + Ações
old = """                              <td className="py-2.5 pl-3">
                                {linha.tipo === 'insumo' ? (
                                  <div className="w-28"><PickerField value={x.supplyClass || 'insumo'} options={SUPPLY_CLASSES} onPick={(opt) => onUpdateSupply({...x,supplyClass:opt.value})} className="field h-8 pl-2.5 text-[12px]" /></div>
                                ) : linha.tipo === 'insumo_revenda' ? (
                                  <div className="flex items-center gap-1.5 min-w-[220px]">
                                    <div className="w-24"><PickerField value={x.supplyClass || 'insumo'} options={SUPPLY_CLASSES} onPick={(opt) => onUpdateSupply({...x,supplyClass:opt.value})} className="field h-8 pl-2 text-[11px]" /></div>
                                    <span className="t-micro">Venda</span>
                                    <input type="number" min="0" step="0.01" value={linha.resaleSource?.price || ''} onChange={(e) => linha.resaleSource && onUpdateSeparatedProduct({...linha.resaleSource,price:Number(e.target.value)||0})} className="field h-8 px-2 text-[12px] text-right font-bold tnum no-spin w-20" />
                                    <span className="t-micro">/{linha.resaleSource?.priceUnit || 'un'}</span>
                                  </div>
                                ) : (
                                  <div className="flex items-center gap-1">
                                    <span className="t-micro">Preço</span>
                                    <input type="number" min="0" step="0.01" value={x.price || ''} onChange={(e) => linha.tipo === 'revenda' ? onUpdateSeparatedProduct({...x,price:Number(e.target.value)||0}) : onUpdateProduct({...x,price:Number(e.target.value)||0})} className="field h-8 px-2 text-[12px] text-right font-bold tnum no-spin w-20" />
                                  </div>
                                )}
                              </td>"""
new = """                              <td className="py-2.5 px-3">
                                {venda ? (
                                  <div className="flex items-center gap-1 min-w-[170px]">
                                    <span className="t-micro">R$</span>
                                    <input
                                      type="number"
                                      min="0"
                                      step="0.01"
                                      value={venda.price || ''}
                                      onChange={(e) => linha.tipo === 'producao'
                                        ? onUpdateProduct({ ...venda, price: Number(e.target.value) || 0 })
                                        : onUpdateSeparatedProduct({ ...venda, price: Number(e.target.value) || 0 })}
                                      className="field h-8 px-2 text-[12px] text-right font-bold tnum no-spin w-20"
                                    />
                                    <div className="w-20">
                                      <PickerField
                                        value={venda.priceUnit || 'un'}
                                        options={linha.tipo === 'producao'
                                          ? [{value:'un',label:'un'},{value:'kg',label:'kg'}]
                                          : [{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]}
                                        onPick={(opt) => linha.tipo === 'producao'
                                          ? onUpdateProduct({ ...venda, priceUnit: opt.value })
                                          : onUpdateSeparatedProduct({ ...venda, priceUnit: opt.value })}
                                        className="field h-8 pl-2 text-[11px]"
                                      />
                                    </div>
                                  </div>
                                ) : <span className="t-empty">—</span>}
                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'producao' ? (
                                  <div className="flex items-center gap-1.5 min-w-[430px]">
                                    <input
                                      value={x.responsible || ''}
                                      onChange={(e) => onUpdateProduct({ ...x, responsible: e.target.value })}
                                      placeholder="Responsável"
                                      className="field h-8 px-2 text-[11px] w-28"
                                    />
                                    <div className="w-28">
                                      <PickerField value={x.category} options={PRODUCT_CATEGORIES} onPick={(opt) => onUpdateProduct({ ...x, category: opt.value })} className="field h-8 pl-2 text-[11px]" />
                                    </div>
                                    <span className="t-micro">Val.</span>
                                    <input
                                      type="number"
                                      min="1"
                                      value={x.shelfLifeDays || 1}
                                      onChange={(e) => onUpdateProduct({ ...x, shelfLifeDays: Math.max(1, Number(e.target.value) || 1) })}
                                      className="field h-8 px-2 text-[11px] text-center tnum w-14"
                                    />
                                    <label className="inline-flex items-center gap-1 t-micro whitespace-nowrap cursor-pointer">
                                      <input type="checkbox" checked={x.showcaseEnabled !== false} onChange={(e) => onUpdateProduct({ ...x, showcaseEnabled: e.target.checked })} className="w-4 h-4" />
                                      Vitrine
                                    </label>
                                  </div>
                                ) : linha.tipo === 'revenda' ? (
                                  <div className="w-28">
                                    <PickerField value={x.category || 'revenda'} options={[{value:'revenda',label:'Revenda'},{value:'cafeteria',label:'Cafeteria'},{value:'encomenda',label:'Encomenda'}]} onPick={(opt) => onUpdateSeparatedProduct({ ...x, category: opt.value })} className="field h-8 pl-2 text-[11px]" />
                                  </div>
                                ) : linha.tipo === 'insumo_revenda' ? (
                                  <div className="flex items-center gap-2 min-w-[210px]">
                                    <span className="pill tone-quiet">Insumo</span>
                                    <span className="t-micro">+</span>
                                    <div className="w-28">
                                      <PickerField value={linha.resaleSource?.category || 'revenda'} options={[{value:'revenda',label:'Revenda'},{value:'cafeteria',label:'Cafeteria'},{value:'encomenda',label:'Encomenda'}]} onPick={(opt) => linha.resaleSource && onUpdateSeparatedProduct({ ...linha.resaleSource, category: opt.value })} className="field h-8 pl-2 text-[11px]" />
                                    </div>
                                  </div>
                                ) : (
                                  <span className="t-callout font-semibold">
                                    {linha.tipo === 'embalagem' ? 'Uso interno · embalagem' : linha.tipo === 'limpeza' ? 'Uso interno · limpeza' : 'Ingrediente / insumo'}
                                  </span>
                                )}
                              </td>
                              <td className="py-2.5 pl-3">
                                <div className="flex items-center justify-end gap-1.5 min-w-[120px]">
                                  {linha.tipo === 'producao' ? (
                                    <button type="button" onClick={() => setFichaProdutoId(x.id)} title="Abrir ficha técnica" className="w-8 h-8 rounded-full bg-black/[0.05] hover:bg-black/[0.09] flex items-center justify-center">
                                      <Icons.ClipboardList className="w-3.5 h-3.5" />
                                    </button>
                                  ) : (
                                    <button
                                      type="button"
                                      onClick={() => setHistorico(linha.tipo === 'revenda' ? { tipo: 'revenda', id: x.id } : { tipo: 'insumo', id: x.id })}
                                      title={`Histórico de compras${comprasLinha.length ? ` · ${comprasLinha.length}` : ''}`}
                                      className="w-8 h-8 rounded-full bg-black/[0.05] hover:bg-black/[0.09] flex items-center justify-center relative"
                                    >
                                      <Icons.ShoppingCart className="w-3.5 h-3.5" />
                                      {comprasLinha.length > 1 && <span className="absolute -top-1 -right-1 min-w-4 h-4 px-1 text-[9px] font-bold rounded-full bg-[#0E0937] text-white flex items-center justify-center tnum">{comprasLinha.length}</span>}
                                    </button>
                                  )}
                                  <button type="button" onClick={() => onDeleteCatalogItem(linha)} title={`Remover ${linha.name}`} className="w-8 h-8 rounded-full icon-danger flex items-center justify-center">
                                    <Icons.Trash2 className="w-4 h-4" />
                                  </button>
                                </div>
                              </td>"""
assert old in s
s = s.replace(old, new, 1)

s = s.replace(
    'Todos os cadastros ficam nesta tabela: Insumo, Revenda, Insumo + revenda e Produção. Itens híbridos aparecem uma única vez; use o seletor Tipo para corrigir a classificação.',
    'Esta é a tabela mestre: tipo, unidade, equivalência, compras, custo, preço, dados do produto e remover ficam na mesma linha. Embalagem e Limpeza aparecem como uso interno.',
    1,
)

# ------------------------------------------------------------------
# Fichas: copiar ficha pronta
# ------------------------------------------------------------------
s = s.replace('Cadastre produtos na aba Produtos primeiro', 'Cadastre um item de Produção em Cadastros primeiro', 1)

old = """                            <td className="py-2.5 pl-3 text-right">
                              <button
                                type="button"
                                onClick={() => setFichaProdutoId(produto.id)}
                                className="btn btn-secondary btn-sm"
                              >
                                <Icons.ClipboardList className="w-3.5 h-3.5" />
                                {ficha && ficha.itens.length > 0 ? 'Abrir' : 'Montar'}
                              </button>
                            </td>"""
new = """                            <td className="py-2.5 pl-3 text-right">
                              <div className="flex items-center justify-end gap-1.5">
                                {ficha && ficha.itens.length > 0 && (
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setCopiarFichaDe({ produto, ficha });
                                      setProdutoDestinoCopia('');
                                    }}
                                    className="btn btn-secondary btn-sm"
                                    title="Copiar esta ficha para outro produto"
                                  >
                                    <Icons.ClipboardList className="w-3.5 h-3.5" />
                                    Copiar
                                  </button>
                                )}
                                <button
                                  type="button"
                                  onClick={() => setFichaProdutoId(produto.id)}
                                  className="btn btn-secondary btn-sm"
                                >
                                  <Icons.ClipboardList className="w-3.5 h-3.5" />
                                  {ficha && ficha.itens.length > 0 ? 'Abrir' : 'Montar'}
                                </button>
                              </div>
                            </td>"""
assert old in s
s = s.replace(old, new, 1)

# Modal de cópia antes do editor aberto
old = """                {fichaAberta && (
                  <RecipeEditor"""
new = """                {copiarFichaDe && (
                  <div className="fixed inset-0 z-[95] bg-black/30 backdrop-blur-[2px] flex items-center justify-center p-4">
                    <button type="button" className="absolute inset-0" aria-label="Fechar cópia de ficha" onClick={() => !copiandoFicha && setCopiarFichaDe(null)} />
                    <form
                      className="relative bg-white rounded-[22px] w-full max-w-lg p-5 sm:p-6 shadow-[0_24px_64px_rgba(0,0,0,0.24)] border hairline"
                      onSubmit={async (e) => {
                        e.preventDefault();
                        if (!produtoDestinoCopia || copiandoFicha) return;
                        setCopiandoFicha(true);
                        try {
                          await onCopyRecipe(copiarFichaDe.produto.id, produtoDestinoCopia);
                          setCopiarFichaDe(null);
                          setFichaProdutoId(produtoDestinoCopia);
                          setProdutoDestinoCopia('');
                        } finally {
                          setCopiandoFicha(false);
                        }
                      }}
                    >
                      <div className="t-overline mb-1">Copiar ficha técnica</div>
                      <h3 className="t-title">{copiarFichaDe.produto.name}</h3>
                      <p className="t-body mt-1 mb-4">Copia rendimento e todos os componentes para outro produto. Se o destino já tiver ficha, você confirma antes de substituir.</p>
                      <label className="t-caption block mb-1">Produto de destino</label>
                      <PickerField
                        value={produtoDestinoCopia}
                        options={products
                          .filter((p) => p.id !== copiarFichaDe.produto.id)
                          .map((p) => ({ value: p.id, label: p.name, hint: recipes.some((r) => r.productId === p.id) ? 'Já tem ficha' : 'Sem ficha' }))}
                        onPick={(opt) => setProdutoDestinoCopia(opt.value)}
                        placeholder="Escolha o produto que vai receber a ficha"
                        className="field field-md"
                      />
                      <div className="flex justify-end gap-2 mt-5">
                        <button type="button" disabled={copiandoFicha} onClick={() => setCopiarFichaDe(null)} className="btn btn-secondary btn-md">Cancelar</button>
                        <button type="submit" disabled={!produtoDestinoCopia || copiandoFicha} className="btn btn-primary btn-md disabled:opacity-45">
                          {copiandoFicha ? 'Copiando…' : 'Copiar ficha'}
                        </button>
                      </div>
                    </form>
                  </div>
                )}

                {fichaAberta && (
                  <RecipeEditor"""
assert old in s
s = s.replace(old, new, 1)

# ------------------------------------------------------------------
# App: copiar ficha no banco
# ------------------------------------------------------------------
old = """        const handleDeleteRecipeItem = (id) => {
          setRecipeItems((prev) => prev.filter((i) => i.id !== id));
          write('Remover componente da ficha', () =>
            run('recipe_items', sb.from('recipe_items').delete().eq('id', id))
          );
        };

        // Liga/desliga a opção de revenda"""
new = """        const handleDeleteRecipeItem = (id) => {
          setRecipeItems((prev) => prev.filter((i) => i.id !== id));
          write('Remover componente da ficha', () =>
            run('recipe_items', sb.from('recipe_items').delete().eq('id', id))
          );
        };

        const handleCopyRecipe = (sourceProductId, targetProductId) => {
          if (!sourceProductId || !targetProductId || sourceProductId === targetProductId) return;
          const origem = recipesRef.current.find((r) => r.productId === sourceProductId);
          const itensOrigem = origem ? recipeItems.filter((i) => i.recipeId === origem.id) : [];
          const produtoOrigem = products.find((p) => p.id === sourceProductId);
          const produtoDestino = products.find((p) => p.id === targetProductId);
          if (!origem || itensOrigem.length === 0 || !produtoDestino) {
            window.alert('A ficha de origem ainda não tem componentes para copiar.');
            return;
          }

          const destinoAtual = recipesRef.current.find((r) => r.productId === targetProductId);
          const itensDestino = destinoAtual ? recipeItems.filter((i) => i.recipeId === destinoAtual.id) : [];
          if (itensDestino.length > 0) {
            const ok = window.confirm(`“${produtoDestino.name}” já tem uma ficha com ${itensDestino.length} ${itensDestino.length === 1 ? 'item' : 'itens'}. Substituir pela ficha de “${produtoOrigem?.name || 'origem'}”?`);
            if (!ok) return;
          }

          const circular = itensOrigem.find((i) => i.componentProductId && (
            i.componentProductId === targetProductId
            || produtoDependeDe(i.componentProductId, targetProductId, recipes, recipeItems)
          ));
          if (circular) {
            window.alert('Essa cópia criaria uma ficha circular por causa de um produto de fabricação própria usado como componente.');
            return;
          }

          return write('Copiar ficha técnica', async () => {
            const destino = await garantirFicha(targetProductId);
            await run('recipe_items', sb.from('recipe_items').delete().eq('recipe_id', destino.id));

            const targetUnit = (produtoDestino.priceUnit || 'un') === 'kg' ? 'kg' : 'un';
            const sourceUnit = origem.yieldUnit || 'un';
            const pesoUn = Number(origem.weightPerUnit) || 0;
            let rendimento = Number(origem.yieldQty) || 1;
            if (sourceUnit !== targetUnit && pesoUn > 0) {
              if (sourceUnit === 'un' && targetUnit === 'kg') rendimento = (rendimento * pesoUn) / 1000;
              if (sourceUnit === 'kg' && targetUnit === 'un') rendimento = (rendimento * 1000) / pesoUn;
            }

            const linhasFicha = await run('recipes', sb.from('recipes').update({
              yield_qty: Math.max(0.001, rendimento || 1),
              yield_unit: targetUnit,
              weight_per_unit: origem.weightPerUnit || null,
              notes: origem.notes || ''
            }).eq('id', destino.id).select());

            let novosItens = [];
            if (itensOrigem.length > 0) {
              novosItens = await run('recipe_items', sb.from('recipe_items').insert(
                itensOrigem.map((i) => ({
                  recipe_id: destino.id,
                  supply_id: i.supplyId || null,
                  component_product_id: i.componentProductId || null,
                  qty: Number(i.qty) || 0,
                  usage_unit: i.usageUnit || ''
                }))
              ).select());
            }

            const fichaNova = fromRecipe(linhasFicha[0]);
            aplicarRecipes([
              ...recipesRef.current.filter((r) => r.id !== destino.id),
              fichaNova
            ]);
            setRecipeItems((prev) => [
              ...prev.filter((i) => i.recipeId !== destino.id),
              ...novosItens.map(fromRecipeItem)
            ]);
          });
        };

        // Liga/desliga a opção de revenda"""
assert old in s
s = s.replace(old, new, 1)

# Revenda também pode ser removida da tabela mestre
old = """        const handleUpdateSeparatedProduct = (updated) => {
          setSeparatedProducts((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
          writeSoon(`sep-cmv:${updated.id}`, 'Atualizar item de revenda', () =>
            run('separated_products', sb.from('separated_products').update({
              name: String(updated.productName || '').trim() || undefined,
              category: updated.category || 'revenda',
              unit_of_measure: updated.unitOfMeasure || updated.priceUnit || 'un',
              price: Number(updated.price) || 0,
              price_unit: updated.priceUnit || 'un',
              cost: Number(updated.cost) || 0
            }).eq('id', updated.id))
          );
        };

        const handleAddResalePurchase"""
new = """        const handleUpdateSeparatedProduct = (updated) => {
          setSeparatedProducts((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
          writeSoon(`sep-cmv:${updated.id}`, 'Atualizar item de revenda', () =>
            run('separated_products', sb.from('separated_products').update({
              name: String(updated.productName || '').trim() || undefined,
              category: updated.category || 'revenda',
              unit_of_measure: updated.unitOfMeasure || updated.priceUnit || 'un',
              price: Number(updated.price) || 0,
              price_unit: updated.priceUnit || 'un',
              cost: Number(updated.cost) || 0
            }).eq('id', updated.id))
          );
        };

        const handleDeleteSeparatedProduct = (id) => {
          const alvo = separatedProducts.find((i) => i.id === id);
          if (!alvo) return;
          const avisoEstoque = Number(alvo.currentQty) > 0 ? `\\n\\nAtenção: ainda constam ${alvo.currentQty} ${alvo.priceUnit || alvo.unitOfMeasure || 'un'} em estoque.` : '';
          const ok = window.confirm(`Excluir a revenda “${alvo.productName}”? As compras registradas nela saem junto.${avisoEstoque}`);
          if (!ok) return;
          return write('Excluir revenda', async () => {
            await run('separated_products', sb.from('separated_products').delete().eq('id', id));
            setSeparatedProducts((prev) => prev.filter((i) => i.id !== id));
            setResalePurchases((prev) => prev.filter((c) => c.separatedProductId !== id));
          });
        };

        const handleAddResalePurchase"""
assert old in s
s = s.replace(old, new, 1)

# Exclusão unificada depois do handler de produto
old = """        const handleDeleteProduct = (id) => {
          const emUso = slotItems.some((i) => i.productId === id);
          if (emUso) {
            setErrorMsg('Este produto está na vitrine agora. Dê baixa nele antes de excluir.');
            return;
          }

          write('Excluir produto', async () => {
            const { error } = await sb.from('products').delete().eq('id', id);
            // A trava do banco (on delete restrict) impede apagar produto com histórico
            if (error) throw new Error(
              error.code === '23503'
                ? 'o produto tem lançamentos ligados a ele e não pode ser apagado'
                : error.message
            );
            setProducts((prev) => prev.filter((p) => p.id !== id));
          });
        };

        const handleChangeCatalogType"""
new = """        const handleDeleteProduct = (id) => {
          const emUso = slotItems.some((i) => i.productId === id);
          if (emUso) {
            setErrorMsg('Este produto está na vitrine agora. Dê baixa nele antes de excluir.');
            return;
          }

          return write('Excluir produto', async () => {
            const { error } = await sb.from('products').delete().eq('id', id);
            // A trava do banco (on delete restrict) impede apagar produto com histórico
            if (error) throw new Error(
              error.code === '23503'
                ? 'o produto tem lançamentos ligados a ele e não pode ser apagado'
                : error.message
            );
            setProducts((prev) => prev.filter((p) => p.id !== id));
          });
        };

        const handleDeleteCatalogItem = (item) => {
          if (!item) return;
          if (['insumo', 'embalagem', 'limpeza'].includes(item.tipo)) {
            return handleDeleteSupply(item.id);
          }
          if (item.tipo === 'revenda') {
            return handleDeleteSeparatedProduct(item.id);
          }
          if (item.tipo === 'producao') {
            const ok = window.confirm(`Excluir o produto de produção “${item.name}”? A ficha técnica dele também será removida.`);
            if (!ok) return;
            return handleDeleteProduct(item.id);
          }
          if (item.tipo === 'insumo_revenda') {
            const emFichas = recipeItems.filter((i) => i.supplyId === item.id);
            if (emFichas.length > 0) {
              setErrorMsg(`“${item.name}” está sendo usado em ficha técnica. Tire o insumo das fichas antes de excluir o cadastro completo.`);
              return;
            }
            const ok = window.confirm(`Excluir completamente “${item.name}” (insumo + revenda)? As compras dos dois lados saem junto.`);
            if (!ok) return;
            return write('Excluir insumo + revenda', async () => {
              if (item.resaleId) await run('separated_products', sb.from('separated_products').delete().eq('id', item.resaleId));
              await run('supplies', sb.from('supplies').delete().eq('id', item.id));
              setSeparatedProducts((prev) => prev.filter((x) => x.id !== item.resaleId));
              setResalePurchases((prev) => prev.filter((c) => c.separatedProductId !== item.resaleId));
              setSupplies((prev) => prev.filter((x) => x.id !== item.id));
              setSupplyPurchases((prev) => prev.filter((c) => c.supplyId !== item.id));
            });
          }
        };

        const handleChangeCatalogType"""
assert old in s
s = s.replace(old, new, 1)

# Props no App
old = """                    onAddRecipeItem={handleAddRecipeItem}
                    onUpdateRecipeItem={handleUpdateRecipeItem}
                    onDeleteRecipeItem={handleDeleteRecipeItem}
                    onUpdateSeparatedProduct={handleUpdateSeparatedProduct}"""
new = """                    onAddRecipeItem={handleAddRecipeItem}
                    onUpdateRecipeItem={handleUpdateRecipeItem}
                    onDeleteRecipeItem={handleDeleteRecipeItem}
                    onCopyRecipe={handleCopyRecipe}
                    onUpdateSeparatedProduct={handleUpdateSeparatedProduct}"""
assert old in s
s = s.replace(old, new, 1)

old = """                    onDeleteResalePurchase={handleDeleteResalePurchase}
                    onChangeCatalogType={handleChangeCatalogType}
                  />"""
new = """                    onDeleteResalePurchase={handleDeleteResalePurchase}
                    onChangeCatalogType={handleChangeCatalogType}
                    onDeleteCatalogItem={handleDeleteCatalogItem}
                  />"""
assert old in s
s = s.replace(old, new, 1)

# Sanidade
checks = [
    '2026-09-04-cadastros-mestre-copiar-ficha-1',
    "{ value: 'embalagem', label: 'Embalagem' }",
    'Material de limpeza · uso interno',
    'Preço venda',
    'onDeleteCatalogItem(linha)',
    'const handleCopyRecipe',
    'Copiar ficha técnica',
    'onCopyRecipe={handleCopyRecipe}',
    'const handleDeleteSeparatedProduct',
]
for c in checks:
    assert c in s, c
assert 'Também é revenda?</label>' not in s

p.write_text(s, encoding='utf-8')
print('catalog master + copy recipe patch ok')
