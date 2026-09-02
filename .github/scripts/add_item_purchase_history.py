from pathlib import Path
import re

p = Path('index.html')
text = p.read_text(encoding='utf-8')
original = text

# Version marker
text = re.sub(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-02-item-historico-compras-1" />', text, count=1)

# State for item history modal.
old_state = """        const [historicoFornecedor, setHistoricoFornecedor] = useState(null);"""
new_state = """        const [historicoFornecedor, setHistoricoFornecedor] = useState(null);
        const [historicoItem, setHistoricoItem] = useState(null);"""
if old_state not in text:
    raise SystemExit('item history state marker not found')
text = text.replace(old_state, new_state, 1)

# Purchases shown in item history follow the same month/date/type period filters.
old_calc = """        const comprasHistoricoFornecedor = historicoFornecedor
          ? [...porPeriodo.filter((c) => c.fornecedor === historicoFornecedor)].sort((a, b) => {
              const d = (b.data || '').localeCompare(a.data || '');
              return d !== 0 ? d : (b.criadoEm || '').localeCompare(a.criadoEm || '');
            })
          : [];

        const placar = useMemo(() => ({"""
new_calc = """        const comprasHistoricoFornecedor = historicoFornecedor
          ? [...porPeriodo.filter((c) => c.fornecedor === historicoFornecedor)].sort((a, b) => {
              const d = (b.data || '').localeCompare(a.data || '');
              return d !== 0 ? d : (b.criadoEm || '').localeCompare(a.criadoEm || '');
            })
          : [];

        const comprasHistoricoItem = historicoItem
          ? [...porPeriodo.filter((c) => c.itemId === historicoItem.itemId)].sort((a, b) => {
              const d = (b.data || '').localeCompare(a.data || '');
              return d !== 0 ? d : (b.criadoEm || '').localeCompare(a.criadoEm || '');
            })
          : [];

        const placar = useMemo(() => ({"""
if old_calc not in text:
    raise SystemExit('item history calc marker not found')
text = text.replace(old_calc, new_calc, 1)

# Insert item history modal after supplier history modal.
marker = """            )}

            <div>
              <h2 className=\"t-display\">Fornecedores</h2>"""
item_modal = """            )}

            {historicoItem && (
              <div className=\"fixed inset-0 z-[180] flex items-end sm:items-center justify-center p-0 sm:p-6\">
                <button
                  type=\"button\"
                  aria-label=\"Fechar histórico do item\"
                  onClick={() => setHistoricoItem(null)}
                  className=\"absolute inset-0 bg-black/35 backdrop-blur-[2px]\"
                />
                <div className=\"relative w-full sm:max-w-4xl max-h-[88vh] overflow-hidden bg-white rounded-t-[26px] sm:rounded-[24px] shadow-2xl border hairline\">
                  <div className=\"px-5 sm:px-6 py-4 border-b hairline flex items-start gap-3\">
                    <div className=\"w-10 h-10 rounded-2xl bg-black/[0.055] flex items-center justify-center shrink-0\">
                      <Icons.ShoppingCart className=\"w-4.5 h-4.5\" />
                    </div>
                    <div className=\"min-w-0 flex-1\">
                      <div className=\"t-overline\">Histórico de compras do item</div>
                      <h3 className=\"t-title truncate\">{historicoItem.item}</h3>
                      <p className=\"t-micro mt-1 tnum\">
                        {comprasHistoricoItem.length} {comprasHistoricoItem.length === 1 ? 'compra' : 'compras'} · {formatCurrencyBR(comprasHistoricoItem.reduce((s, c) => s + c.cost, 0))}
                        {mesFiltro ? ` · ${mesesDisponiveis.find((m) => m.value === mesFiltro)?.label || mesFiltro}` : ''}
                        {(dataInicio || dataFim) ? ` · ${dataInicio ? formatDateBR(dataInicio) : 'início'} até ${dataFim ? formatDateBR(dataFim) : 'hoje'}` : ''}
                      </p>
                    </div>
                    <button type=\"button\" onClick={() => setHistoricoItem(null)} className=\"btn btn-secondary btn-sm\">Fechar</button>
                  </div>
                  <div className=\"overflow-auto max-h-[68vh] px-5 sm:px-6 pb-5\">
                    {comprasHistoricoItem.length === 0 ? (
                      <p className=\"t-body text-center py-10 ink-quiet\">Nenhuma compra deste item no período selecionado.</p>
                    ) : (
                      <table className=\"w-full text-left tabela-larga\">
                        <thead className=\"sticky top-0 bg-white z-10\">
                          <tr className=\"t-overline-sm border-b hairline\">
                            <th className=\"py-3 pr-3 font-bold\">Data</th>
                            <th className=\"py-3 px-3 font-bold\">Fornecedor</th>
                            <th className=\"py-3 px-3 font-bold\">Tipo</th>
                            <th className=\"py-3 px-3 text-right font-bold\">Quantidade</th>
                            <th className=\"py-3 px-3 text-right font-bold\">Valor pago</th>
                            <th className=\"py-3 pl-3 text-right font-bold\">Custo unit.</th>
                          </tr>
                        </thead>
                        <tbody>
                          {comprasHistoricoItem.map((c) => (
                            <tr key={`${c.tipo}-${c.id}`} className=\"border-t hairline\">
                              <td className=\"py-3 pr-3 t-callout whitespace-nowrap\">{c.data ? formatDateBR(c.data) : '—'}</td>
                              <td className=\"py-3 px-3 t-callout font-semibold\">{c.fornecedor}</td>
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
              <h2 className=\"t-display\">Fornecedores</h2>"""
if marker not in text:
    raise SystemExit('item modal insertion marker not found')
text = text.replace(marker, item_modal, 1)

# Turn the purchase count in the By Item table into a cart/history button.
old_cell = """                            <td className=\"py-2.5 pl-3 text-center t-body tnum\">{i.compras}</td>"""
new_cell = """                            <td className=\"py-2.5 pl-3 text-center\">
                              <button
                                type=\"button\"
                                onClick={() => setHistoricoItem({ itemId: i.itemId, item: i.item })}
                                title={`Histórico de compras de ${i.item}`}
                                className=\"btn btn-secondary btn-sm mx-auto\"
                              >
                                <Icons.ShoppingCart className=\"w-3.5 h-3.5\" />
                                <span className=\"tnum\">{i.compras}</span>
                              </button>
                            </td>"""
if old_cell not in text:
    raise SystemExit('item cart cell marker not found')
text = text.replace(old_cell, new_cell, 1)

if text == original:
    raise SystemExit('no changes made')

p.write_text(text, encoding='utf-8')
print('item purchase history added')
