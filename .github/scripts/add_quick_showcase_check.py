from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-04-vitrine-conferencia-rapida-1" />',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('version marker not found')

if 'const ShowcaseQuickChecklist' in s:
    raise SystemExit('quick checklist already present')

marker = '''      // ==========================================\n      // PAINEL DO AGORA'''
if marker not in s:
    raise SystemExit('panel marker not found')

component = r'''
      // ==========================================
      // CONFERÊNCIA RÁPIDA DA VITRINE
      //
      // O checklist antigo continua disponível no botão "Item a item", mas a
      // entrada principal agora é uma folha única: a pessoa olha a vitrine
      // física, digita o que está vendo e confirma a linha. O normal some da
      // fila; a aba Atenção segura só o que precisa de decisão.
      // ==========================================
      const ShowcaseQuickChecklist = ({
        currentUnit, slots, slotItems, products, standardPlans, showcaseType,
        onRecordSale, onRecordLoss, onSetQty, onUndoBaixa, onClose
      }) => {
        const [modoDetalhado, setModoDetalhado] = useState(false);
        const [escopo, setEscopo] = useState(showcaseType);
        const [filtro, setFiltro] = useState('conferir');
        const [busca, setBusca] = useState('');
        const [conferidos, setConferidos] = useState({});
        const [contagens, setContagens] = useState({});
        const [destinos, setDestinos] = useState({});
        const [motivos, setMotivos] = useState({});
        const [salvando, setSalvando] = useState('');
        const [ultima, setUltima] = useState(null);

        const dayOfWeek = getTodayDayOfWeek();

        useEffect(() => {
          setConferidos({});
          setContagens({});
          setDestinos({});
          setMotivos({});
          setUltima(null);
          setFiltro('conferir');
        }, [escopo]);

        const linhas = useMemo(() => {
          const unitSlots = slots.filter(
            (slot) => slot.unit === currentUnit && (escopo === 'todas' || slot.showcaseType === escopo)
          );
          const slotById = {};
          unitSlots.forEach((slot) => { slotById[slot.id] = slot; });

          return slotItems
            .filter((item) => slotById[item.slotId] && (item.currentQty || 0) > 0)
            .map((item) => {
              const slot = slotById[item.slotId];
              const product = products.find((p) => p.id === item.productId);
              const planos = standardPlans.filter(
                (sp) => sp.unit === currentUnit
                  && sp.dayOfWeek === dayOfWeek
                  && sp.slotId === item.slotId
                  && sp.productId === item.productId
              );
              return {
                id: item.id,
                item,
                slot,
                product,
                status: getSlotItemStatus(item, product),
                padrao: planos.reduce((acc, sp) => acc + (Number(sp.idealQty) || 0), 0),
                minimo: planos.reduce((acc, sp) => acc + (Number(sp.minQty) || 0), 0)
              };
            })
            .sort((a, b) =>
              compareShowcase(a.slot, b.slot)
              || a.slot.slotNumber - b.slot.slotNumber
              || a.item.productName.localeCompare(b.item.productName, 'pt-BR')
            );
        }, [escopo, currentUnit, slots, slotItems, products, standardPlans, dayOfWeek]);

        const qtdDaLinha = (linha) => (
          contagens[linha.id] === undefined
            ? Number(linha.item.currentQty) || 0
            : Math.max(0, Number(contagens[linha.id]) || 0)
        );

        const leituraLinha = (linha, qtd = qtdDaLinha(linha)) => {
          if (linha.status.status === 'expired') {
            return { tipo: 'vencido', label: 'Retirar da vitrine', detail: `${qtd} ${linha.item.unit}`, tone: 'text-[var(--expired-ink)]' };
          }
          if (linha.status.status === 'warning') {
            return { tipo: 'ultimo', label: 'Último dia', detail: 'vender primeiro', tone: 'text-[var(--last-ink)]' };
          }
          if (linha.padrao > 0 && qtd < linha.padrao) {
            const falta = Math.max(0, linha.padrao - qtd);
            const chamou = linha.minimo > 0 ? qtd <= linha.minimo : qtd <= 0;
            return {
              tipo: chamou ? 'produzir' : 'falta',
              label: chamou ? `Produzir ${falta}` : `Faltam ${falta}`,
              detail: linha.minimo > 0 ? `mín. ${linha.minimo}` : 'abaixo da meta',
              tone: chamou ? 'text-[var(--expired-ink)]' : 'text-[var(--last-ink)]'
            };
          }
          if (linha.padrao > 0 && qtd > linha.padrao) {
            return { tipo: 'excesso', label: `+${qtd - linha.padrao} acima`, detail: 'do padrão', tone: 'text-[var(--last-ink)]' };
          }
          if (linha.padrao <= 0) {
            return { tipo: 'sempadrao', label: 'Sem padrão', detail: 'só conferir', tone: 'text-[#86868b]' };
          }
          return { tipo: 'ok', label: 'OK', detail: 'no padrão', tone: 'text-[var(--fresh-ink)]' };
        };

        const precisaAtencao = (linha) => !['ok', 'sempadrao'].includes(leituraLinha(linha).tipo);
        const total = linhas.length;
        const totalConferidos = linhas.filter((l) => conferidos[l.id]).length;
        const totalAtencao = linhas.filter(precisaAtencao).length;
        const faltamConferir = Math.max(0, total - totalConferidos);

        const visiveis = useMemo(() => {
          const termo = normalizeName(busca);
          return linhas.filter((linha) => {
            if (termo && !normalizeName(linha.item.productName).includes(termo)) return false;
            if (filtro === 'conferir') return !conferidos[linha.id];
            if (filtro === 'atencao') return precisaAtencao(linha);
            return true;
          });
        }, [linhas, filtro, busca, conferidos, contagens]);

        const setQtd = (linha, valor) => {
          const novo = Math.max(0, Math.floor(Number(valor) || 0));
          setContagens((prev) => ({ ...prev, [linha.id]: novo }));
          setConferidos((prev) => ({ ...prev, [linha.id]: false }));
        };

        const destinoDaLinha = (linha) => destinos[linha.id]
          || (linha.status.status === 'expired' ? 'perda' : 'venda');

        const confirmarLinha = async (linha) => {
          if (salvando) return;
          const antes = Number(linha.item.currentQty) || 0;
          const depois = qtdDaLinha(linha);
          const diferenca = antes - depois;
          setSalvando(linha.id);
          try {
            let baixa = null;
            if (diferenca > 0) {
              const destino = destinoDaLinha(linha);
              if (destino === 'perda') {
                baixa = await onRecordLoss(
                  linha.item.id,
                  diferenca,
                  motivos[linha.id] || 'vencido',
                  'Conferência rápida da vitrine'
                );
              } else {
                baixa = await onRecordSale(linha.item.id, diferenca);
              }
              if (baixa) {
                setUltima({
                  baixa,
                  linhaId: linha.id,
                  antes,
                  texto: `${diferenca} ${linha.item.unit} de ${linha.item.productName}`
                });
              }
            } else if (depois > antes) {
              await onSetQty(linha.item.id, depois);
              setUltima(null);
            } else {
              setUltima(null);
            }
            setConferidos((prev) => ({ ...prev, [linha.id]: true }));
          } finally {
            setSalvando('');
          }
        };

        const desfazerUltima = async () => {
          if (!ultima) return;
          await onUndoBaixa(ultima.baixa);
          setContagens((prev) => ({ ...prev, [ultima.linhaId]: ultima.antes }));
          setConferidos((prev) => ({ ...prev, [ultima.linhaId]: false }));
          setUltima(null);
          setFiltro('conferir');
        };

        const finalizar = () => {
          if (faltamConferir > 0) {
            const ok = window.confirm(`Ainda faltam ${faltamConferir} ${faltamConferir === 1 ? 'item' : 'itens'} para conferir. Fechar mesmo assim?`);
            if (!ok) return;
          }
          onClose();
        };

        if (modoDetalhado) {
          return (
            <ShowcaseChecklist
              currentUnit={currentUnit}
              slots={slots}
              slotItems={slotItems}
              products={products}
              standardPlans={standardPlans}
              showcaseType={escopo === 'todas' ? showcaseType : escopo}
              onRecordSale={onRecordSale}
              onRecordLoss={onRecordLoss}
              onSetQty={onSetQty}
              onUndoBaixa={onUndoBaixa}
              onClose={onClose}
            />
          );
        }

        return (
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Conferência rápida da vitrine"
            className="fixed inset-0 z-50 bg-black/30 backdrop-blur-[2px] flex items-start justify-center p-2 sm:p-5 overflow-y-auto"
          >
            <div className="bg-white rounded-[24px] w-full max-w-5xl my-2 sm:my-auto shadow-[0_24px_64px_rgba(0,0,0,0.24)] overflow-hidden">
              <div className="px-4 sm:px-6 pt-4 pb-4 border-b hairline space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <span className="t-overline">Vitrine operacional</span>
                    <h2 className="t-title mt-0.5">Conferência rápida</h2>
                    <p className="t-micro mt-1">Conte olhando a vitrine. O que está normal some; o que precisa de ação fica na aba Atenção.</p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button onClick={() => setModoDetalhado(true)} className="btn btn-secondary btn-sm hidden sm:inline-flex">
                      Item a item
                    </button>
                    <button
                      onClick={finalizar}
                      title="Fechar conferência"
                      aria-label="Fechar conferência"
                      className="w-8 h-8 rounded-full bg-black/[0.05] hover:bg-black/[0.09] flex items-center justify-center"
                    >
                      <Icons.X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="rounded-xl bg-black/[0.035] px-3 py-2">
                    <span className="t-nano block">Conferidos</span>
                    <strong className="t-metric-xs tnum">{totalConferidos}/{total}</strong>
                  </div>
                  <div className="rounded-xl bg-[var(--last-soft)] px-3 py-2">
                    <span className="t-nano block">Atenção</span>
                    <strong className="t-metric-xs tnum">{totalAtencao}</strong>
                  </div>
                  <div className="rounded-xl bg-black/[0.035] px-3 py-2">
                    <span className="t-nano block">Faltam conferir</span>
                    <strong className="t-metric-xs tnum">{faltamConferir}</strong>
                  </div>
                </div>

                <div className="h-1.5 rounded-full bg-black/[0.07] overflow-hidden">
                  <div
                    className="h-full bg-[#0E0937] rounded-full transition-all"
                    style={{ width: `${total ? Math.round((totalConferidos / total) * 100) : 100}%` }}
                  />
                </div>

                <div className="flex flex-col lg:flex-row lg:items-center gap-2">
                  <div className="segmented flex w-full lg:w-auto">
                    {[...SHOWCASE_TYPES, 'todas'].map((tipo) => (
                      <button
                        key={tipo}
                        className="flex-1 lg:flex-none"
                        data-active={escopo === tipo}
                        onClick={() => setEscopo(tipo)}
                      >
                        {tipo === 'todas' ? 'Todas' : SHOWCASE_TYPE_LABELS[tipo]}
                      </button>
                    ))}
                  </div>
                  <div className="segmented flex w-full lg:w-auto">
                    <button className="flex-1" data-active={filtro === 'conferir'} onClick={() => setFiltro('conferir')}>
                      Conferir ({faltamConferir})
                    </button>
                    <button className="flex-1" data-active={filtro === 'atencao'} onClick={() => setFiltro('atencao')}>
                      Atenção ({totalAtencao})
                    </button>
                    <button className="flex-1" data-active={filtro === 'todos'} onClick={() => setFiltro('todos')}>
                      Todos
                    </button>
                  </div>
                  <input
                    type="search"
                    value={busca}
                    onChange={(e) => setBusca(e.target.value)}
                    placeholder="Buscar produto…"
                    className="field field-sm lg:ml-auto lg:w-56"
                  />
                </div>
              </div>

              <div className="max-h-[68vh] overflow-y-auto">
                {total === 0 ? (
                  <div className="py-12 px-5 text-center">
                    <p className="t-body text-[#86868b]">Não há itens nesta vitrine para conferir.</p>
                  </div>
                ) : visiveis.length === 0 ? (
                  <div className="py-12 px-5 text-center space-y-2">
                    <Icons.CheckCircle2 className="w-7 h-7 mx-auto text-[var(--fresh-ink)]" />
                    <p className="t-headline">Nada aqui.</p>
                    <p className="t-micro">
                      {filtro === 'conferir'
                        ? 'Você já conferiu todos os itens deste filtro.'
                        : filtro === 'atencao'
                          ? 'Nenhum item precisa de atenção agora.'
                          : 'Nenhum produto com esse nome.'}
                    </p>
                  </div>
                ) : (
                  <div className="divide-y hairline">
                    {visiveis.map((linha) => {
                      const qtd = qtdDaLinha(linha);
                      const leitura = leituraLinha(linha, qtd);
                      const antes = Number(linha.item.currentQty) || 0;
                      const diminuiu = qtd < antes;
                      const destino = destinoDaLinha(linha);
                      const estaSalvando = salvando === linha.id;

                      return (
                        <div key={linha.id} className={`px-4 sm:px-6 py-3 ${conferidos[linha.id] ? 'bg-black/[0.018]' : ''}`}>
                          <div className="grid grid-cols-12 gap-2 sm:gap-3 items-center">
                            <div className="col-span-12 sm:col-span-4 min-w-0">
                              <div className="flex items-center gap-2 min-w-0">
                                <span className={`w-2 h-2 rounded-full shrink-0 ${
                                  linha.status.status === 'expired' ? 'bg-[var(--expired)]'
                                    : linha.status.status === 'warning' ? 'bg-[var(--last)]'
                                      : leitura.tipo === 'ok' ? 'bg-[var(--fresh)]' : 'bg-[#c7c7cc]'
                                }`} />
                                <strong className="t-body text-[#1d1d1f] truncate">{linha.item.productName}</strong>
                              </div>
                              <div className="t-nano mt-0.5 ml-4">
                                {linha.slot.sectionTitle} · espaço {linha.slot.slotNumber}
                                {linha.item.manufactureDate && ` · lote ${formatDateBR(linha.item.manufactureDate)}`}
                              </div>
                            </div>

                            <div className="col-span-7 sm:col-span-3">
                              <span className="t-nano block mb-1">Quanto tem agora?</span>
                              <div className="flex items-center gap-1.5">
                                <button
                                  type="button"
                                  onClick={() => setQtd(linha, qtd - 1)}
                                  className="w-8 h-8 rounded-full bg-black/[0.05] hover:bg-black/[0.09] font-bold shrink-0"
                                >−</button>
                                <input
                                  type="number"
                                  min="0"
                                  step="1"
                                  value={qtd}
                                  onChange={(e) => setQtd(linha, e.target.value)}
                                  onFocus={(e) => e.target.select()}
                                  onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                      e.preventDefault();
                                      confirmarLinha(linha);
                                    }
                                  }}
                                  className="field h-8 min-w-0 px-1 text-center tnum font-extrabold no-spin"
                                />
                                <button
                                  type="button"
                                  onClick={() => setQtd(linha, qtd + 1)}
                                  className="w-8 h-8 rounded-full bg-black/[0.05] hover:bg-black/[0.09] font-bold shrink-0"
                                >+</button>
                                <button
                                  type="button"
                                  onClick={() => setQtd(linha, 0)}
                                  title="Zerou"
                                  className="btn btn-secondary h-8 px-2 text-[10px] shrink-0"
                                >0</button>
                              </div>

                              {diminuiu && (
                                <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                                  <div className="segmented inline-flex">
                                    <button
                                      type="button"
                                      data-active={destino === 'venda'}
                                      onClick={() => setDestinos((p) => ({ ...p, [linha.id]: 'venda' }))}
                                    >Venda</button>
                                    <button
                                      type="button"
                                      data-active={destino === 'perda'}
                                      onClick={() => setDestinos((p) => ({ ...p, [linha.id]: 'perda' }))}
                                    >Perda</button>
                                  </div>
                                  {destino === 'perda' && (
                                    <select
                                      value={motivos[linha.id] || 'vencido'}
                                      onChange={(e) => setMotivos((p) => ({ ...p, [linha.id]: e.target.value }))}
                                      className="field h-8 py-0 text-[11px] field-select w-auto"
                                    >
                                      {CHECKLIST_MOTIVOS.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
                                    </select>
                                  )}
                                </div>
                              )}
                            </div>

                            <div className="col-span-2 sm:col-span-1 text-center">
                              <span className="t-nano block">Meta</span>
                              <strong className="t-body tnum text-[#1d1d1f]">{linha.padrao > 0 ? linha.padrao : '—'}</strong>
                            </div>

                            <div className="col-span-3 sm:col-span-2 min-w-0">
                              <span className={`text-[12px] font-bold block ${leitura.tone}`}>{leitura.label}</span>
                              <span className="t-nano block truncate">{leitura.detail}</span>
                            </div>

                            <div className="col-span-12 sm:col-span-2 flex sm:justify-end">
                              <button
                                type="button"
                                disabled={estaSalvando}
                                onClick={() => confirmarLinha(linha)}
                                className={`btn btn-sm w-full sm:w-auto ${conferidos[linha.id] ? 'btn-secondary' : 'btn-primary'}`}
                              >
                                <Icons.CheckCircle2 className="w-3.5 h-3.5" />
                                {estaSalvando ? 'Salvando…' : conferidos[linha.id] ? 'Conferido' : 'OK'}
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="px-4 sm:px-6 py-3 border-t hairline flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-[#fafafa]">
                <div className="t-micro">
                  {faltamConferir === 0
                    ? totalAtencao > 0
                      ? `Conferência completa · ${totalAtencao} ${totalAtencao === 1 ? 'item ainda pede' : 'itens ainda pedem'} atenção.`
                      : 'Conferência completa · vitrine em ordem.'
                    : `${faltamConferir} ${faltamConferir === 1 ? 'item ainda falta' : 'itens ainda faltam'} conferir.`}
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setModoDetalhado(true)} className="btn btn-secondary btn-sm sm:hidden">Item a item</button>
                  <button onClick={finalizar} className="btn btn-primary btn-sm">Finalizar</button>
                </div>
              </div>

              {ultima && (
                <div className="px-4 sm:px-6 py-2.5 bg-[#1d1d1f] text-white flex items-center justify-between gap-3">
                  <span className="text-[12px] font-semibold truncate">Última baixa · <span className="tnum">{ultima.texto}</span></span>
                  <button onClick={desfazerUltima} className="btn btn-sm bg-white/[0.14] text-white hover:bg-white/25 shrink-0">
                    <Icons.History className="w-3.5 h-3.5" />
                    Desfazer
                  </button>
                </div>
              )}
            </div>
          </div>
        );
      };

'''

s = s.replace(marker, component + marker, 1)

old_render = '''            {checklistAberto && (\n              <ShowcaseChecklist\n                key={showcaseFilter}'''
new_render = '''            {checklistAberto && (\n              <ShowcaseQuickChecklist\n                key={showcaseFilter}'''
if old_render not in s:
    raise SystemExit('checklist render marker not found')
s = s.replace(old_render, new_render, 1)

p.write_text(s, encoding='utf-8')
print('quick showcase checklist added')
