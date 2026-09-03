from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# version
s, n = re.subn(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-03-equivalencia-insumo-1" />', s, count=1)
if n != 1:
    raise SystemExit('version marker not found')

# reusable alternative units
tipos = """        const TIPOS_TABELA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'insumo_revenda', label: 'Insumo + revenda' },
          { value: 'producao', label: 'Produção' }
        ];"""
if tipos not in s:
    raise SystemExit('TIPOS_TABELA marker not found')
s = s.replace(tipos, tipos + """
        const UNIDADES_EQUIVALENCIA = [
          'un', 'kg', 'g', 'L', 'ml', 'fatia', 'pacote', 'caixa', 'lata', 'pote', 'sachê'
        ].map((value) => ({ value, label: value }));""", 1)

# draft
old = """          unit: 'g',
          supplyClass: 'insumo',
          resaleAlso: false,"""
new = """          unit: 'g',
          supplyClass: 'insumo',
          variationUnit: '',
          variationFactor: '',
          resaleAlso: false,"""
if old not in s: raise SystemExit('blank marker not found')
s = s.replace(old, new, 1)

# picker: supply
old = """              unit: x.unit || 'g',
              supplyClass: x.supplyClass || 'insumo',
              resaleAlso: !!rev,"""
new = """              unit: x.unit || 'g',
              supplyClass: x.supplyClass || 'insumo',
              variationUnit: x.variationUnit || '',
              variationFactor: x.variationFactor || '',
              resaleAlso: !!rev,"""
if old not in s: raise SystemExit('supply picker marker not found')
s = s.replace(old, new, 1)

# picker: resale that also has supply
old = """              unit: ins?.unit || unidadeBaseDaRevenda(x.priceUnit || x.unitOfMeasure),
              supplyClass: ins?.supplyClass || 'insumo',
              resaleAlso: true,"""
new = """              unit: ins?.unit || unidadeBaseDaRevenda(x.priceUnit || x.unitOfMeasure),
              supplyClass: ins?.supplyClass || 'insumo',
              variationUnit: ins?.variationUnit || '',
              variationFactor: ins?.variationFactor || '',
              resaleAlso: true,"""
if old not in s: raise SystemExit('resale picker marker not found')
s = s.replace(old, new, 1)

# new supply registration
old = """            insumo = await onAddSupply({
              name: nome,
              unit: draft.unit || 'g',
              supplyClass: draft.supplyClass || 'insumo'
            });"""
new = """            insumo = await onAddSupply({
              name: nome,
              unit: draft.unit || 'g',
              supplyClass: draft.supplyClass || 'insumo',
              variationUnit: String(draft.variationUnit || '').trim() || null,
              variationFactor: Number(draft.variationFactor) > 0 ? Number(draft.variationFactor) : null
            });"""
if old not in s: raise SystemExit('new supply marker not found')
s = s.replace(old, new, 1)

# existing supply: only write if the user actually filled an equivalence; blank
# entry fields never erase existing data accidentally.
needle = "          if (insumo?.id && qty > 0 && cost > 0) {"
if needle not in s: raise SystemExit('purchase marker not found')
s = s.replace(needle, """          if (insumo && (String(draft.variationUnit || '').trim() || Number(draft.variationFactor) > 0)) {
            const variationUnit = String(draft.variationUnit || '').trim() || null;
            const variationFactor = Number(draft.variationFactor) > 0 ? Number(draft.variationFactor) : null;
            if (variationUnit !== (insumo.variationUnit || null) || variationFactor !== (Number(insumo.variationFactor) || null)) {
              onUpdateSupply({ ...insumo, variationUnit, variationFactor });
              insumo = { ...insumo, variationUnit, variationFactor };
            }
          }

          if (insumo?.id && qty > 0 && cost > 0) {""", 1)

# form block: find the resale-detail section inside SuppliesRecipesView and put
# the equivalence row immediately before it.
start = s.index('const SuppliesRecipesView')
pos = s.find('{draft.resaleAlso && (', start)
if pos < 0:
    raise SystemExit('draft.resaleAlso section not found')
line_start = s.rfind('\n', start, pos) + 1
indent = s[line_start:pos]
block = f"""{indent}{{!modoProducao && (
{indent}  <div className=\"grid grid-cols-12 gap-2 sm:gap-3 items-end mt-3 pt-3 border-t hairline\">
{indent}    <div className=\"col-span-12 sm:col-span-3\">
{indent}      <div className=\"t-caption font-semibold\">Equivalência / variação <span className=\"font-normal text-[#86868b]\">(opcional)</span></div>
{indent}      <p className=\"t-micro mt-1\">Para usar na ficha como fatia, unidade, pacote, kg etc.</p>
{indent}    </div>
{indent}    <div className=\"col-span-6 sm:col-span-3\">
{indent}      <label className=\"t-caption block mb-1\">Unidade alternativa</label>
{indent}      <PickerField
{indent}        value={{draft.variationUnit}}
{indent}        options={{UNIDADES_EQUIVALENCIA}}
{indent}        onType={{(variationUnit) => setDraft((d) => ({{ ...d, variationUnit }}))}}
{indent}        onPick={{(opt) => setDraft((d) => ({{ ...d, variationUnit: opt.value }}))}}
{indent}        placeholder=\"Ex: fatia\"
{indent}        emptyLabel=\"Usar esta unidade\"
{indent}        className=\"field field-md\"
{indent}      />
{indent}    </div>
{indent}    <div className=\"col-span-6 sm:col-span-2\">
{indent}      <label className=\"t-caption block mb-1\">Quanto vale</label>
{indent}      <input
{indent}        type=\"number\"
{indent}        min=\"0\"
{indent}        step=\"0.001\"
{indent}        value={{draft.variationFactor}}
{indent}        onChange={{(e) => setDraft((d) => ({{ ...d, variationFactor: e.target.value }}))}}
{indent}        placeholder=\"Ex: 30\"
{indent}        className=\"field field-md text-right tnum no-spin\"
{indent}      />
{indent}    </div>
{indent}    <div className=\"col-span-12 sm:col-span-4\">
{indent}      <label className=\"t-caption block mb-1\">Leitura</label>
{indent}      <div className=\"field field-md flex items-center px-3 bg-black/[0.035] t-callout font-semibold\">
{indent}        {{draft.unit === 'un'
{indent}          ? `1 un = ${{draft.variationFactor || '…'}} ${{draft.variationUnit || '…'}}`
{indent}          : `1 ${{draft.variationUnit || '…'}} = ${{draft.variationFactor || '…'}} ${{draft.unit || 'g'}}`}}
{indent}      </div>
{indent}    </div>
{indent}  </div>
{indent})}}

"""
s = s[:line_start] + block + s[line_start:]

# table header
old = """                          <th className="py-3 px-3 font-bold">Un.</th>
                          <th className="py-3 px-3 font-bold">Fornecedor</th>"""
new = """                          <th className="py-3 px-3 font-bold">Un.</th>
                          <th className="py-3 px-3 font-bold">Equiv.</th>
                          <th className="py-3 px-3 font-bold">Fornecedor</th>"""
if old not in s: raise SystemExit('table header not found')
s = s.replace(old, new, 1)
s = s.replace('<tr><td colSpan={9} className="text-center py-10"><p className="t-body ink-quiet">Nenhum cadastro encontrado</p></td></tr>', '<tr><td colSpan={10} className="text-center py-10"><p className="t-body ink-quiet">Nenhum cadastro encontrado</p></td></tr>', 1)

# table equivalence cell between unit and supplier
boundary = """                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'producao' ? <span className="t-empty">—</span> : (
                                  <div className="w-28 sm:w-36"><PickerField value={c?.supplier || ''}"""
if boundary not in s:
    raise SystemExit('unit/supplier boundary not found')
cell = """                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'insumo' || linha.tipo === 'insumo_revenda' ? (
                                  <div className="flex items-center gap-1 min-w-[210px]">
                                    {x.unit === 'un' ? (
                                      <>
                                        <span className="t-micro whitespace-nowrap">1 un =</span>
                                        <input type="number" min="0" step="0.001" value={x.variationFactor ?? ''} onChange={(e) => onUpdateSupply({...x, variationFactor: Number(e.target.value) > 0 ? Number(e.target.value) : null})} placeholder="0" className="field h-8 px-2 text-[12px] text-right tnum no-spin w-16" />
                                        <div className="w-24"><PickerField value={x.variationUnit || ''} options={UNIDADES_EQUIVALENCIA} onType={(v) => onUpdateSupply({...x,variationUnit:v})} onPick={(opt) => onUpdateSupply({...x,variationUnit:opt.value})} placeholder="unid." emptyLabel="Unidade nova" className="field h-8 pl-2 text-[11px]" /></div>
                                      </>
                                    ) : (
                                      <>
                                        <span className="t-micro">1</span>
                                        <div className="w-24"><PickerField value={x.variationUnit || ''} options={UNIDADES_EQUIVALENCIA} onType={(v) => onUpdateSupply({...x,variationUnit:v})} onPick={(opt) => onUpdateSupply({...x,variationUnit:opt.value})} placeholder="fatia" emptyLabel="Unidade nova" className="field h-8 pl-2 text-[11px]" /></div>
                                        <span className="t-micro">=</span>
                                        <input type="number" min="0" step="0.001" value={x.variationFactor ?? ''} onChange={(e) => onUpdateSupply({...x, variationFactor: Number(e.target.value) > 0 ? Number(e.target.value) : null})} placeholder="0" className="field h-8 px-2 text-[12px] text-right tnum no-spin w-16" />
                                        <span className="t-micro whitespace-nowrap">{x.unit}</span>
                                      </>
                                    )}
                                  </div>
                                ) : <span className="t-empty">—</span>}
                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'producao' ? <span className="t-empty">—</span> : (
                                  <div className="w-28 sm:w-36"><PickerField value={c?.supplier || ''}"""
s = s.replace(boundary, cell, 1)

old = '<p className="t-micro pt-3">O tipo pode ser Insumo, Revenda, Insumo + revenda ou Produção. Itens híbridos aparecem uma única vez na tabela.</p>'
new = '<p className="t-micro pt-3">O tipo pode ser Insumo, Revenda, Insumo + revenda ou Produção. Itens híbridos aparecem uma única vez. Em Equiv. você pode registrar coisas como 1 fatia = 30 g ou 1 un = 500 g.</p>'
if old not in s: raise SystemExit('table note not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('restored supply equivalence UI v2')
