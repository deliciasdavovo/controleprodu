from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old_version = '<meta name="app-version" content="2026-09-05-autocomplete-enter-1" />'
new_version = '<meta name="app-version" content="2026-09-05-formato-br-entrada-1" />'
if old_version in s:
    s = s.replace(old_version, new_version, 1)
elif new_version not in s:
    raise SystemExit('app version marker not found')

marker = """      // ==========================================\n      // QUANTIDADE DA BAIXA SOBRE O LOTE"""
if marker not in s:
    raise SystemExit('QtyOfBatch marker not found')

component = r'''      // Campo numérico com leitura brasileira, mas valor interno normalizado.
      // Ex.: 1200 -> 1.200; 24,975 -> 24,975; dinheiro 1 -> 1,00 ao sair.
      const NumeroBRField = ({
        value = '',
        onValueChange,
        decimals = 3,
        fixedDecimals = false,
        onBlur,
        onFocus,
        ...props
      }) => {
        const ref = useRef(null);

        const formatValue = (v) => {
          if (v === '' || v === null || v === undefined) return '';
          const n = Number(v);
          if (!Number.isFinite(n)) return '';
          return n.toLocaleString('pt-BR', {
            minimumFractionDigits: fixedDecimals ? decimals : 0,
            maximumFractionDigits: decimals
          });
        };

        const [text, setText] = useState(() => formatValue(value));

        useEffect(() => {
          if (document.activeElement !== ref.current) setText(formatValue(value));
        }, [value, decimals, fixedDecimals]);

        const handleChange = (e) => {
          const raw = String(e.target.value || '')
            .replace(/\s/g, '')
            .replace(/[^\d,]/g, '');
          const hasComma = raw.includes(',');
          const partes = raw.split(',');
          let inteiro = partes.shift() || '';
          const decimal = partes.join('').slice(0, decimals);

          inteiro = inteiro.replace(/^0+(?=\d)/, '');
          if (!inteiro && (hasComma || decimal)) inteiro = '0';

          const agrupado = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
          const display = agrupado + (hasComma ? `,${decimal}` : '');
          setText(display);

          const normalized = display
            ? display.replace(/\./g, '').replace(',', '.')
            : '';
          onValueChange(normalized);
        };

        const handleBlur = (e) => {
          setText(formatValue(value));
          if (onBlur) onBlur(e);
        };

        return (
          <input
            ref={ref}
            type="text"
            inputMode="decimal"
            value={text}
            onChange={handleChange}
            onBlur={handleBlur}
            onFocus={onFocus}
            {...props}
          />
        );
      };

'''
s = s.replace(marker, component + marker, 1)

old_qty = r'''                        <input
                          type="number"
                          min="0"
                          step="0.001"
                          value={modoProducao ? '' : draft.qty}
                          disabled={modoProducao}
                          onChange={(e) => setDraft((d) => ({ ...d, qty: e.target.value }))}
                          placeholder={compraExistente?.qty ? String(compraExistente.qty) : '0'}
                          className="field field-md text-right tnum no-spin disabled:opacity-50"
                        />'''
new_qty = r'''                        <NumeroBRField
                          value={modoProducao ? '' : draft.qty}
                          disabled={modoProducao}
                          decimals={3}
                          onValueChange={(qty) => setDraft((d) => ({ ...d, qty }))}
                          placeholder={compraExistente?.qty ? Number(compraExistente.qty).toLocaleString('pt-BR', { maximumFractionDigits: 3 }) : '0'}
                          className="field field-md text-right tnum disabled:opacity-50"
                        />'''
if old_qty not in s:
    raise SystemExit('quantity input block not found')
s = s.replace(old_qty, new_qty, 1)

old_cost = r'''                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={modoProducao ? '' : draft.cost}
                          disabled={modoProducao}
                          onChange={(e) => setDraft((d) => ({ ...d, cost: e.target.value }))}
                          placeholder={compraExistente?.cost ? String(compraExistente.cost) : '0,00'}
                          className="field field-md text-right tnum no-spin disabled:opacity-50"
                        />'''
new_cost = r'''                        <NumeroBRField
                          value={modoProducao ? '' : draft.cost}
                          disabled={modoProducao}
                          decimals={2}
                          fixedDecimals={true}
                          onValueChange={(cost) => setDraft((d) => ({ ...d, cost }))}
                          placeholder={compraExistente?.cost ? Number(compraExistente.cost).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0,00'}
                          className="field field-md text-right tnum disabled:opacity-50"
                        />'''
if old_cost not in s:
    raise SystemExit('cost input block not found')
s = s.replace(old_cost, new_cost, 1)

old_price = r'''                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={modoProducao || temRevenda ? draft.price : ''}
                          disabled={!modoProducao && !temRevenda}
                          onChange={(e) => setDraft((d) => ({ ...d, price: e.target.value }))}
                          placeholder="0,00"
                          className="field field-md text-right tnum no-spin disabled:opacity-50"
                        />'''
new_price = r'''                        <NumeroBRField
                          value={modoProducao || temRevenda ? draft.price : ''}
                          disabled={!modoProducao && !temRevenda}
                          decimals={2}
                          fixedDecimals={true}
                          onValueChange={(price) => setDraft((d) => ({ ...d, price }))}
                          placeholder="0,00"
                          className="field field-md text-right tnum disabled:opacity-50"
                        />'''
if old_price not in s:
    raise SystemExit('price input block not found')
s = s.replace(old_price, new_price, 1)

for required in [
    '2026-09-05-formato-br-entrada-1',
    'const NumeroBRField = ({',
    'fixedDecimals={true}',
    "replace(/\\B(?=(\\d{3})+(?!\\d))/g, '.')",
    'onValueChange={(qty) => setDraft((d) => ({ ...d, qty }))}',
    'onValueChange={(cost) => setDraft((d) => ({ ...d, cost }))}',
    'onValueChange={(price) => setDraft((d) => ({ ...d, price }))}'
]:
    if required not in s:
        raise SystemExit(f'missing required marker: {required}')

p.write_text(s, encoding='utf-8')
