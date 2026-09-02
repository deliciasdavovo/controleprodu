from pathlib import Path
import re

p = Path('index.html')
text = p.read_text(encoding='utf-8')
original = text

# version marker
text = re.sub(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-02-fornecedor-historico-filtros-1" />', text, count=1)

old_state = """        const [visao, setVisao] = useState('item');
        const [busca, setBusca] = useState('');
        const [tipoFiltro, setTipoFiltro] = useState('todos');
        const [ordem, setOrdem] = useState('variacao_desc');
        const [limite, setLimite] = useState('25');"""
new_state = """        const [visao, setVisao] = useState('item');
        const [busca, setBusca] = useState('');
        const [tipoFiltro, setTipoFiltro] = useState('todos');
        const [ordem, setOrdem] = useState('variacao_desc');
        const [limite, setLimite] = useState('25');
        const [mesFiltro, setMesFiltro] = useState('');
        const [dataInicio, setDataInicio] = useState('');
        const [dataFim, setDataFim] = useState('');
        const [historicoFornecedor, setHistoricoFornecedor] = useState(null);"""
if old_state not in text:
    raise SystemExit('supplier state marker not found')
text = text.replace(old_state, new_state, 1)

old_filter = """        // O filtro de tipo alimenta também o placar; a busca só estreita a lista
        const porTipo = tipoFiltro === 'todos' ? todas : todas.filter((c) => c.tipo === tipoFiltro);
        const termo = busca.trim().toLowerCase();
        const compras = termo
          ? porTipo.filter((c) => c.fornecedor.toLowerCase().includes(termo) || c.item.toLowerCase().includes(termo))
          : porTipo;

        const placar = useMemo(() => ({
          fornecedores: new Set(porTipo.filter((c) => c.fornecedor !== 'Sem fornecedor').map((c) => c.fornecedor)).size,
          compras: porTipo.length,
          total: porTipo.reduce((s, c) => s + c.cost, 0),
          itens: new Set(porTipo.map((c) => c.itemId)).size
        }), [porTipo]);"""
new_filter = """        // Tipo + período alimentam também o placar; a busca só estreita a lista.
        const porTipo = tipoFiltro === 'todos' ? todas : todas.filter((c) => c.tipo === tipoFiltro);
        const porPeriodo = porTipo.filter((c) => {
          const data = c.data || '';
          if (mesFiltro && !data.startsWith(mesFiltro)) return false;
          if (dataInicio && (!data || data < dataInicio)) return false;
          if (dataFim && (!data || data > dataFim)) return false;
          return true;
        });
        const termo = busca.trim().toLowerCase();
        const compras = termo
          ? porPeriodo.filter((c) => c.fornecedor.toLowerCase().includes(termo) || c.item.toLowerCase().includes(termo))
          : porPeriodo;

        const mesesDisponiveis = useMemo(() => {
          const valores = [...new Set(todas.map((c) => (c.data || '').slice(0, 7)).filter((m) => /^\\d{4}-\\d{2}$/.test(m)))].sort().reverse();
          return [
            { value: '', label: 'Todos os meses' },
            ...valores.map((m) => ({
              value: m,
              label: new Date(`${m}-01T12:00:00`).toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })
            }))
          ];
        }, [todas]);

        const comprasHistoricoFornecedor = historicoFornecedor
          ? [...porPeriodo.filter((c) => c.fornecedor === historicoFornecedor)].sort((a, b) => {
              const d = (b.data || '').localeCompare(a.data || '');
              return d !== 0 ? d : (b.criadoEm || '').localeCompare(a.criadoEm || '');
            })
          : [];

        const placar = useMemo(() => ({
          fornecedores: new Set(porPeriodo.filter((c) => c.fornecedor !== 'Sem fornecedor').map((c) => c.fornecedor)).size,
          compras: porPeriodo.length,
          total: porPeriodo.reduce((s, c) => s + c.cost, 0),
          itens: new Set(porPeriodo.map((c) => c.itemId)).size
        }), [porPeriodo]);"""
if old_filter not in text:
    raise SystemExit('supplier filter marker not found')
text = text.replace(old_filter, new_filter, 1)

old_search = """              <div className=\"relative flex-1 max-w-sm\">
                <Icons.Search className=\"w-3.5 h-3.5 text-[#86868b] absolute left-3 top-[11px]\" />
                <input
                  type=\"text\"
                  placeholder=\"Buscar fornecedor ou item…\"
                  value={busca}
                  onChange={(e) => setBusca(e.target.value)}
                  className=\"field field-sm field-search\"
                />
              </div>"""
new_search = old_search + """
              <div className=\"w-44\">
                <PickerField
                  value={mesFiltro}
                  options={mesesDisponiveis}
                  onPick={(opt) => {
                    setMesFiltro(opt.value);
                    if (opt.value) { setDataInicio(''); setDataFim(''); }
                  }}
                  className=\"field field-sm\"
                  title=\"Filtrar compras por mês\"
                />
              </div>
              <div className=\"flex items-center gap-1.5\">
                <input
                  type=\"date\"
                  value={dataInicio}
                  onChange={(e) => { setDataInicio(e.target.value); setMesFiltro(''); }}
                  title=\"Data inicial\"
                  className=\"field field-sm w-[136px]\"
                />
                <span className=\"t-micro\">até</span>
                <input
                  type=\"date\"
                  value={dataFim}
                  onChange={(e) => { setDataFim(e.target.value); setMesFiltro(''); }}
                  title=\"Data final\"
                  className=\"field field-sm w-[136px]\"
                />
              </div>
              {(mesFiltro || dataInicio || dataFim) && (
                <button
                  type=\"button\"
                  onClick={() => { setMesFiltro(''); setDataInicio(''); setDataFim(''); }}
                  className=\"btn btn-secondary btn-sm\"
                >
                  Limpar período
                </button>
              )}"""
if old_search not in text:
    raise SystemExit('supplier search marker not found')
text = text.replace(old_search, new_search, 1)

old_supplier_head = """                        <div className=\"flex flex-wrap items-baseline gap-x-3 gap-y-1 pb-2\">
                          <h3 className=\"t-title\">{f.nome}</h3>
                          <span className=\"t-micro tnum\">
                            {formatCurrencyBR(f.total)} · {f.lista.length} {f.lista.length === 1 ? 'compra' : 'compras'} · {f.itens} {f.itens === 1 ? 'item' : 'itens'}
                            {f.recente && ` · última em ${formatDateBR(f.recente)}`}
                          </span>
                        </div>"""
new_supplier_head = """                        <div className=\"flex flex-wrap items-center gap-x-3 gap-y-2 pb-2\">
                          <h3 className=\"t-title\">{f.nome}</h3>
                          <span className=\"t-micro tnum\">
                            {formatCurrencyBR(f.total)} · {f.lista.length} {f.lista.length === 1 ? 'compra' : 'compras'} · {f.itens} {f.itens === 1 ? 'item' : 'itens'}
                            {f.recente && ` · última em ${formatDateBR(f.recente)}`}
                          </span>
                          <button
                            type=\"button\"
                            onClick={() => setHistoricoFornecedor(f.nome)}
                            className=\"btn btn-secondary btn-sm ml-auto\"
                            title={`Histórico de compras de ${f.nome}`}
                          >
                            <Icons.ShoppingCart className=\"w-3.5 h-3.5\" />
                            Histórico
                          </button>
                        </div>"""
if old_supplier_head not in text:
    raise SystemExit('supplier header marker not found')
text = text.replace(old_supplier_head, new_supplier_head, 1)

old_return = """        return (
          <div className=\"space-y-5\">
            <div>
              <h2 className=\"t-display\">Fornecedores</h2>
              <p className=\"t-body mt-1\">
                {unitName} · o preço de cada item, compra a compra. Vermelho subiu, verde caiu.
              </p>
            </div>"""
modal = """        return (
          <div className=\"space-y-5\">
            {historicoFornecedor && (
              <div className=\"fixed inset-0 z-[180] flex items-end sm:items-center justify-center p-0 sm:p-6\">
                <button
                  type=\"button\"
                  aria-label=\"Fechar histórico\"
                  onClick={() => setHistoricoFornecedor(null)}
                  className=\"absolute inset-0 bg-black/35 backdrop-blur-[2px]\"
                />
                <div className=\"relative w-full sm:max-w-4xl max-h-[88vh] overflow-hidden bg-white rounded-t-[26px] sm:rounded-[24px] shadow-2xl border hairline\">
                  <div className=\"px-5 sm:px-6 py-4 border-b hairline flex items-start gap-3\">
                    <div className=\"w-10 h-10 rounded-2xl bg-black/[0.055] flex items-center justify-center shrink-0\">
                      <Icons.ShoppingCart className=\"w-4.5 h-4.5\" />
                    </div>
                    <div className=\"min-w-0 flex-1\">
                      <div className=\"t-overline\">Histórico de compras</div>
                      <h3 className=\"t-title truncate\">{historicoFornecedor}</h3>
                      <p className=\"t-micro mt-1 tnum\">
                        {comprasHistoricoFornecedor.length} {comprasHistoricoFornecedor.length === 1 ? 'compra' : 'compras'} · {formatCurrencyBR(comprasHistoricoFornecedor.reduce((s, c) => s + c.cost, 0))}
                        {mesFiltro ? ` · ${mesesDisponiveis.find((m) => m.value === mesFiltro)?.label || mesFiltro}` : ''}
                        {(dataInicio || dataFim) ? ` · ${dataInicio ? formatDateBR(dataInicio) : 'início'} até ${dataFim ? formatDateBR(dataFim) : 'hoje'}` : ''}
                      </p>
                    </div>
                    <button type=\"button\" onClick={() => setHistoricoFornecedor(null)} className=\"btn btn-secondary btn-sm\">Fechar</button>
                  </div>
                  <div className=\"overflow-auto max-h-[68vh] px-5 sm:px-6 pb-5\">
                    {comprasHistoricoFornecedor.length === 0 ? (
                      <p className=\"t-body text-center py-10 ink-quiet\">Nenhuma compra deste fornecedor no período selecionado.</p>
                    ) : (
                      <table className=\"w-full text-left tabela-larga\">
                        <thead className=\"sticky top-0 bg-white z-10\">
                          <tr className=\"t-overline-sm border-b hairline\">
                            <th className=\"py-3 pr-3 font-bold\">Data</th>
                            <th className=\"py-3 px-3 font-bold\">Item</th>
                            <th className=\"py-3 px-3 font-bold\">Tipo</th>
                            <th className=\"py-3 px-3 text-right font-bold\">Quantidade</th>
                            <th className=\"py-3 px-3 text-right font-bold\">Valor pago</th>
                            <th className=\"py-3 pl-3 text-right font-bold\">Custo unit.</th>
                          </tr>
                        </thead>
                        <tbody>
                          {comprasHistoricoFornecedor.map((c) => (
                            <tr key={`${c.tipo}-${c.id}`} className=\"border-t hairline\">
                              <td className=\"py-3 pr-3 t-callout whitespace-nowrap\">{c.data ? formatDateBR(c.data) : '—'}</td>
                              <td className=\"py-3 px-3 t-callout font-semibold\">{c.item}</td>
                              <td className=\"py-3 px-3\"><span className=\"pill tone-quiet\">{c.tipo}</span></td>
                              <td className=\"py-3 px-3 text-right t-callout tnum\">{c.qty || 0} {c.unidade}</td>
                              <td className=\"py-3 px-3 text-right t-callout tnum font-semibold\">{formatCurrencyBR(c.cost)}</td>
                              <td className=\"py-3 pl-3 text-right t-callout tnum\">{c.custoUnit > 0 ? `${formatCurrencyBR(c.custoUnit)}/${c.unidade}` : '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    )}
                  </div>
                </div>
              </div>
            )}

            <div>
              <h2 className=\"t-display\">Fornecedores</h2>
              <p className=\"t-body mt-1\">
                {unitName} · o preço de cada item, compra a compra. Vermelho subiu, verde caiu.
              </p>
            </div>"""
if old_return not in text:
    raise SystemExit('normal suppliers return marker not found')
text = text.replace(old_return, modal, 1)

if text == original:
    raise SystemExit('no changes made')

p.write_text(text, encoding='utf-8')
print('supplier history and period filters added')
