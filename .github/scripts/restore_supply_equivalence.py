from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Version
s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-03-equivalencia-insumo-1" />',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('version marker not found')

# Common alternative units shown in the editable equivalence picker. PickerField
# still allows free typing, so this list is only a shortcut.
old_types = """        const TIPOS_TABELA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'insumo_revenda', label: 'Insumo + revenda' },
          { value: 'producao', label: 'Produção' }
        ];"""
new_types = """        const TIPOS_TABELA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'insumo_revenda', label: 'Insumo + revenda' },
          { value: 'producao', label: 'Produção' }
        ];
        const UNIDADES_EQUIVALENCIA = [
          'un', 'kg', 'g', 'L', 'ml', 'fatia', 'pacote', 'caixa', 'lata', 'pote', 'sachê'
        ].map((value) => ({ value, label: value }));"""
if old_types not in s:
    raise SystemExit('TIPOS_TABELA marker not found')
s = s.replace(old_types, new_types, 1)

# Draft fields
old_blank = """          unit: 'g',
          supplyClass: 'insumo',
          resaleAlso: false,"""
new_blank = """          unit: 'g',
          supplyClass: 'insumo',
          variationUnit: '',
          variationFactor: '',
          resaleAlso: false,"""
if old_blank not in s:
    raise SystemExit('BLANK_ENTRY supply fields marker not found')
s = s.replace(old_blank, new_blank, 1)

# Existing supply selection restores its saved equivalence into the form.
old_pick_supply = """              unit: x.unit || 'g',
              supplyClass: x.supplyClass || 'insumo',
              resaleAlso: !!rev,"""
new_pick_supply = """              unit: x.unit || 'g',
              supplyClass: x.supplyClass || 'insumo',
              variationUnit: x.variationUnit || '',
              variationFactor: x.variationFactor || '',
              resaleAlso: !!rev,"""
if old_pick_supply not in s:
    raise SystemExit('supply picker marker not found')
s = s.replace(old_pick_supply, new_pick_supply, 1)

old_pick_resale = """              unit: ins?.unit || unidadeBaseDaRevenda(x.priceUnit || x.unitOfMeasure),
              supplyClass: ins?.supplyClass || 'insumo',
              resaleAlso: true,"""
new_pick_resale = """              unit: ins?.unit || unidadeBaseDaRevenda(x.priceUnit || x.unitOfMeasure),
              supplyClass: ins?.supplyClass || 'insumo',
              variationUnit: ins?.variationUnit || '',
              variationFactor: ins?.variationFactor || '',
              resaleAlso: true,"""
if old_pick_resale not in s:
    raise SystemExit('resale picker marker not found')
s = s.replace(old_pick_resale, new_pick_resale, 1)

# New supply registration now sends the equivalence fields that the DB already supports.
old_add = """            insumo = await onAddSupply({
              name: nome,
              unit: draft.unit || 'g',
              supplyClass: draft.supplyClass || 'insumo'
            });"""
new_add = """            insumo = await onAddSupply({
              name: nome,
              unit: draft.unit || 'g',
              supplyClass: draft.supplyClass || 'insumo',
              variationUnit: String(draft.variationUnit || '').trim() || null,
              variationFactor: Number(draft.variationFactor) > 0 ? Number(draft.variationFactor) : null
            });"""
if old_add not in s:
    raise SystemExit('onAddSupply in cadastrar marker not found')
s = s.replace(old_add, new_add, 1)

# If an existing item was selected and the equivalence was edited in the entry
# form, persist it. Blank draft fields never erase an existing equivalence by
# accident; clearing is available in the master table below.
needle = """          if (insumo?.id && qty > 0 && cost > 0) {"""
insert = """          if (insumo && (String(draft.variationUnit || '').trim() || Number(draft.variationFactor) > 0)) {
            const variationUnit = String(draft.variationUnit || '').trim() || null;
            const variationFactor = Number(draft.variationFactor) > 0 ? Number(draft.variationFactor) : null;
            if (variationUnit !== (insumo.variationUnit || null) || variationFactor !== (Number(insumo.variationFactor) || null)) {
              onUpdateSupply({ ...insumo, variationUnit, variationFactor });
              insumo = { ...insumo, variationUnit, variationFactor };
            }
          }

          if (insumo?.id && qty > 0 && cost > 0) {"""
if needle not in s:
    raise SystemExit('purchase marker not found')
s = s.replace(needle, insert, 1)

# Restore the equivalence UI between the identity fields and resale-specific
# fields. It is deliberately part of the same purchase form.
form_marker = """                    {draft.resaleAlso && (
                      <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end mt-3 pt-3 border-t hairline">"""
form_block = """                    {!modoProducao && (
                      <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end mt-3 pt-3 border-t hairline">
                        <div className="col-span-12 sm:col-span-3">
                          <div className="t-caption font-semibold">Equivalência / variação <span className="font-normal text-[#86868b]">(opcional)</span></div>
                          <p className="t-micro mt-1">Para usar na ficha como fatia, unidade, pacote, kg etc.</p>
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
                          <div className="field field-md flex items-center px-3 bg-black/[0.035] t-callout font-semibold">
                            {draft.unit === 'un'
                              ? `1 un = ${draft.variationFactor || '…'} ${draft.variationUnit || '…'}`
                              : `1 ${draft.variationUnit || '…'} = ${draft.variationFactor || '…'} ${draft.unit || 'g'}`}
                          </div>
                        </div>
                      </div>
                    )}

                    {draft.resaleAlso && (
                      <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end mt-3 pt-3 border-t hairline">"""
if form_marker not in s:
    raise SystemExit('resale detail form marker not found')
s = s.replace(form_marker, form_block, 1)

# Add a visible editable Equiv. column to the unified catalog table.
old_header = """                          <th className="py-3 px-3 font-bold">Un.</th>
                          <th className="py-3 px-3 font-bold">Fornecedor</th>"""
new_header = """                          <th className="py-3 px-3 font-bold">Un.</th>
                          <th className="py-3 px-3 font-bold">Equiv.</th>
                          <th className="py-3 px-3 font-bold">Fornecedor</th>"""
if old_header not in s:
    raise SystemExit('table header marker not found')
s = s.replace(old_header, new_header, 1)
s = s.replace('''<tr><td colSpan={9} className="text-center py-10"><p className="t-body ink-quiet">Nenhum cadastro encontrado</p></td></tr>''', '''<tr><td colSpan={10} className="text-center py-10"><p className="t-body ink-quiet">Nenhum cadastro encontrado</p></td></tr>''', 1)

# Insert equivalence cell immediately after the existing unit cell. Target a
# stable boundary: unit td closes and supplier td begins.
unit_to_supplier = """                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'producao' ? <span className="t-empty">—</span> : (
                                  <div className="w-28 sm:w-36"><PickerField value={c?.supplier || ''}"""
equiv_cell = """                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'insumo' || linha.tipo === 'insumo_revenda' ? (
                                  <div className="flex items-center gap-1 min-w-[210px]">
                                    {x.unit === 'un' ? (
                                      <>
                                        <span className="t-micro whitespace-nowrap">1 un =</span>
                                        <input
                                          type="number"
                                          min="0"
                                          step="0.001"
                                          value={x.variationFactor ?? ''}
                                          onChange={(e) => onUpdateSupply({...x, variationFactor: Number(e.target.value) > 0 ? Number(e.target.value) : null})}
                                          placeholder="0"
                                          className="field h-8 px-2 text-[12px] text-right tnum no-spin w-16"
                                        />
                                        <div className="w-24">
                                          <PickerField
                                            value={x.variationUnit || ''}
                                            options={UNIDADES_EQUIVALENCIA}
                                            onType={(v) => onUpdateSupply({...x,variationUnit:v})}
                                            onPick={(opt) => onUpdateSupply({...x,variationUnit:opt.value})}
                                            placeholder="unid."
                                            emptyLabel="Unidade nova"
                                            className="field h-8 pl-2 text-[11px]"
                                          />
                                        </div>
                                      </>
                                    ) : (
                                      <>
                                        <span className="t-micro">1</span>
                                        <div className="w-24">
                                          <PickerField
                                            value={x.variationUnit || ''}
                                            options={UNIDADES_EQUIVALENCIA}
                                            onType={(v) => onUpdateSupply({...x,variationUnit:v})}
                                            onPick={(opt) => onUpdateSupply({...x,variationUnit:opt.value})}
                                            placeholder="fatia"
                                            emptyLabel="Unidade nova"
                                            className="field h-8 pl-2 text-[11px]"
                                          />
                                        </div>
                                        <span className="t-micro">=</span>
                                        <input
                                          type="number"
                                          min="0"
                                          step="0.001"
                                          value={x.variationFactor ?? ''}
                                          onChange={(e) => onUpdateSupply({...x, variationFactor: Number(e.target.value) > 0 ? Number(e.target.value) : null})}
                                          placeholder="0"
                                          className="field h-8 px-2 text-[12px] text-right tnum no-spin w-16"
                                        />
                                        <span className="t-micro whitespace-nowrap">{x.unit}</span>
                                      </>
                                    )}
                                  </div>
                                ) : <span className="t-empty">—</span>}
                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'producao' ? <span className="t-empty">—</span> : (
                                  <div className="w-28 sm:w-36"><PickerField value={c?.supplier || ''}"""
if unit_to_supplier not in s:
    raise SystemExit('unit to supplier boundary not found')
s = s.replace(unit_to_supplier, equiv_cell, 1)

old_note = """                  <p className="t-micro pt-3">O tipo pode ser Insumo, Revenda, Insumo + revenda ou Produção. Itens híbridos aparecem uma única vez na tabela.</p>"""
new_note = """                  <p className="t-micro pt-3">O tipo pode ser Insumo, Revenda, Insumo + revenda ou Produção. Itens híbridos aparecem uma única vez. Em Equiv. você pode registrar coisas como 1 fatia = 30 g ou 1 un = 500 g.</p>"""
if old_note not in s:
    raise SystemExit('table note marker not found')
s = s.replace(old_note, new_note, 1)

p.write_text(s, encoding='utf-8')
print('restored supply equivalence UI')
