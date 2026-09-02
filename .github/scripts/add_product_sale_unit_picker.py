from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'Marker not found: {label}')
    s = s.replace(old, new, 1)

s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-02-produto-preco-unidade-1" />',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('app version marker not found')

replace_once(
"""        const BLANK_DRAFT = { name: '', responsible: '', category: 'salgado', showcaseEnabled: true, shelfLifeDays: 2, price: 8.5 };""",
"""        const BLANK_DRAFT = { name: '', responsible: '', category: 'salgado', showcaseEnabled: true, shelfLifeDays: 2, price: 8.5, priceUnit: 'un' };""",
'blank product draft'
)

replace_once(
"""                shelfLifeDays: found.shelfLifeDays,
                price: found.price
              }""",
"""                shelfLifeDays: found.shelfLifeDays,
                price: found.price,
                priceUnit: found.priceUnit || 'un'
              }""",
'load existing product sale unit'
)

replace_once(
"""            shelfLifeDays: Math.max(1, Number(draft.shelfLifeDays) || 1),
            price: Math.max(0, Number(draft.price) || 0)
          };""",
"""            shelfLifeDays: Math.max(1, Number(draft.shelfLifeDays) || 1),
            price: Math.max(0, Number(draft.price) || 0),
            priceUnit: draft.priceUnit === 'kg' ? 'kg' : 'un'
          };""",
'save product sale unit'
)

replace_once(
"""          setDraft({ ...BLANK_DRAFT, responsible: dados.responsible, category: dados.category, showcaseEnabled: dados.showcaseEnabled });""",
"""          setDraft({ ...BLANK_DRAFT, responsible: dados.responsible, category: dados.category, showcaseEnabled: dados.showcaseEnabled, priceUnit: dados.priceUnit });""",
'keep sale unit after save'
)

old_price_form = """                  <div className=\"col-span-4 md:col-span-1\">
                    <label className=\"t-caption block mb-1\">Preço</label>
                    <input
                      ref={priceRef}
                      type=\"number\"
                      step=\"0.01\"
                      min=\"0\"
                      value={draft.price}
                      onChange={(e) => setField('price', e.target.value)}
                      className=\"field field-md text-right tnum\"
                    />
                  </div>"""
new_price_form = """                  <div className=\"col-span-8 md:col-span-2\">
                    <div className=\"grid grid-cols-[minmax(0,1fr)_108px] gap-2\">
                      <div>
                        <label className=\"t-caption block mb-1\">Preço de venda</label>
                        <div className=\"relative\">
                          <span className=\"t-micro absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none\">R$</span>
                          <input
                            ref={priceRef}
                            type=\"number\"
                            step=\"0.01\"
                            min=\"0\"
                            value={draft.price}
                            onChange={(e) => setField('price', e.target.value)}
                            className=\"field field-md text-right tnum pl-8\"
                          />
                        </div>
                      </div>
                      <div>
                        <label className=\"t-caption block mb-1\">Vendido por</label>
                        <PickerField
                          value={draft.priceUnit || 'un'}
                          options={[
                            { value: 'un', label: 'Unidade' },
                            { value: 'kg', label: 'Kg' }
                          ]}
                          onPick={(opt) => setField('priceUnit', opt.value)}
                          className=\"field field-md\"
                        />
                      </div>
                    </div>
                  </div>"""
replace_once(old_price_form, new_price_form, 'product price form')

replace_once(
"""                      <th className=\"py-3 px-3 text-right font-bold\">Preço</th>""",
"""                      <th className=\"py-3 px-3 text-right font-bold\">Preço de venda</th>""",
'table price header'
)

old_price_cell = """                          <td className=\"py-2.5 px-3\">
                            <div className=\"flex items-center justify-end gap-1.5\">
                              <span className=\"t-micro hidden sm:inline\">R$</span>
                              <input
                                type=\"number\"
                                step=\"0.01\"
                                min=\"0\"
                                value={p.price}
                                onChange={(e) => onUpdateProduct({ ...p, price: Math.max(0, Number(e.target.value) || 0) })}
                                title=\"Preço de venda\"
                                className=\"field h-8 px-2 text-[12px] text-right font-bold tnum w-20 sm:w-24\"
                              />
                            </div>
                          </td>"""
new_price_cell = """                          <td className=\"py-2.5 px-3\">
                            <div className=\"flex items-center justify-end gap-1.5 min-w-[190px]\">
                              <span className=\"t-micro\">R$</span>
                              <input
                                type=\"number\"
                                step=\"0.01\"
                                min=\"0\"
                                value={p.price}
                                onChange={(e) => onUpdateProduct({ ...p, price: Math.max(0, Number(e.target.value) || 0) })}
                                title={`Preço de venda por ${p.priceUnit === 'kg' ? 'kg' : 'unidade'}`}
                                className=\"field h-8 px-2 text-[12px] text-right font-bold tnum w-20 sm:w-24\"
                              />
                              <span className=\"t-micro\">/</span>
                              <div className=\"w-24\">
                                <PickerField
                                  value={p.priceUnit || 'un'}
                                  options={[
                                    { value: 'un', label: 'unidade' },
                                    { value: 'kg', label: 'kg' }
                                  ]}
                                  onPick={(opt) => onUpdateProduct({ ...p, priceUnit: opt.value })}
                                  title=\"Unidade do preço de venda\"
                                  className=\"field h-8 pl-2.5 text-[12px]\"
                                />
                              </div>
                            </div>
                          </td>"""
replace_once(old_price_cell, new_price_cell, 'product price table cell')

replace_once(
"""              shelf_life_days: prod.shelfLifeDays,
              price: prod.price
            }).select();""",
"""              shelf_life_days: prod.shelfLifeDays,
              price: prod.price,
              price_unit: prod.priceUnit || 'un'
            }).select();""",
'insert product price unit'
)

# Existing-product editing already knows price_unit; require it so a future
# refactor cannot silently make the new control visual-only.
if "campos.price_unit = updated.priceUnit || 'un';" not in s:
    raise SystemExit('product update does not persist price_unit')

p.write_text(s, encoding='utf-8')
print('ok')
