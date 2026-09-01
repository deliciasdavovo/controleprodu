from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')
original = text

# 1) PickerField fica acima do editor de ficha (editor = z-[90]).
old = """      .picker-panel {\n        position: fixed;\n        z-index: 60;"""
new = """      .picker-panel {\n        position: fixed;\n        z-index: 140;"""
if old not in text:
    raise SystemExit('picker-panel marker not found')
text = text.replace(old, new, 1)

# 2) SuppliesRecipesView recebe também a ação de criar item de revenda.
old = """        onAddSupplyPurchase,\n        onUpdateSupplyPurchase,\n        onDeleteSupplyPurchase,\n        onUpdateRecipe,"""
new = """        onAddSupplyPurchase,\n        onUpdateSupplyPurchase,\n        onDeleteSupplyPurchase,\n        onAddSeparatedProduct,\n        onUpdateRecipe,"""
if old not in text:
    raise SystemExit('SuppliesRecipesView props marker not found')
text = text.replace(old, new, 1)

# 3) Draft passa a saber se este insumo também deve existir em Revenda.
old = """        const BLANK_SUPPLY = { name: '', unit: 'g', supplyClass: 'insumo', supplier: '', purchaseDate: getTodayDateString(), qty: '', cost: '' };"""
new = """        const BLANK_SUPPLY = { name: '', unit: 'g', supplyClass: 'insumo', supplier: '', purchaseDate: getTodayDateString(), qty: '', cost: '', resaleAlso: false };"""
if old not in text:
    raise SystemExit('BLANK_SUPPLY marker not found')
text = text.replace(old, new, 1)

# 4) Helpers para saber/criar a contraparte de revenda sem duplicar.
old = """        const revendaDaUnidade = separatedProducts.filter((p) => p.unit === currentUnit);\n\n        const cadastrar = async (e) => {"""
new = """        const revendaDaUnidade = separatedProducts.filter((p) => p.unit === currentUnit);\n\n        const revendaDoInsumo = (nome) => revendaDaUnidade.find(\n          (p) => normalizeName(p.productName || p.name) === normalizeName(nome)\n        ) || null;\n\n        const criarRevendaDoInsumo = (nome, unidade = 'un') => {\n          const limpo = String(nome || '').trim();\n          if (!limpo || revendaDoInsumo(limpo) || !onAddSeparatedProduct) return;\n          onAddSeparatedProduct({\n            productName: limpo,\n            category: 'revenda',\n            currentQty: 0,\n            unitOfMeasure: unidade === 'un' ? 'un' : unidade,\n            minQty: 0,\n            price: 0\n          });\n        };\n\n        const cadastrar = async (e) => {"""
if old not in text:
    raise SystemExit('revenda helper marker not found')
text = text.replace(old, new, 1)

# 5) No submit único, cria também a entrada de revenda se marcada.
old = """          if (supplyId && qty > 0 && cost > 0) {\n            onAddSupplyPurchase(supplyId, {\n              supplier: draft.supplier.trim(),\n              purchaseDate: draft.purchaseDate || getTodayDateString(),\n              qty,\n              cost\n            });\n          }\n\n          setDraft({ ...BLANK_SUPPLY, unit: draft.unit, supplyClass: draft.supplyClass, purchaseDate: getTodayDateString() });"""
new = """          if (supplyId && qty > 0 && cost > 0) {\n            onAddSupplyPurchase(supplyId, {\n              supplier: draft.supplier.trim(),\n              purchaseDate: draft.purchaseDate || getTodayDateString(),\n              qty,\n              cost\n            });\n          }\n\n          if (draft.resaleAlso) {\n            criarRevendaDoInsumo(nome, draft.unit);\n          }\n\n          setDraft({ ...BLANK_SUPPLY, unit: draft.unit, supplyClass: draft.supplyClass, purchaseDate: getTodayDateString() });"""
if old not in text:
    raise SystemExit('cadastrar purchase marker not found')
text = text.replace(old, new, 1)

# 6) Checkbox Revenda também no formulário único.
old = """                      <div className=\"col-span-12 sm:col-span-4\">\n                        <label className=\"t-caption block mb-1\">Fornecedor</label>"""
new = """                      <div className=\"col-span-12 sm:col-span-2\">\n                        <label className=\"t-caption block mb-1\">Também é revenda?</label>\n                        <label className=\"field field-md flex items-center gap-2 cursor-pointer\">\n                          <input\n                            type=\"checkbox\"\n                            checked={draft.resaleAlso}\n                            onChange={(e) => setDraft((d) => ({ ...d, resaleAlso: e.target.checked }))}\n                            className=\"w-4 h-4\"\n                          />\n                          <span className=\"t-callout font-semibold\">Revenda também</span>\n                        </label>\n                      </div>\n                      <div className=\"col-span-12 sm:col-span-4\">\n                        <label className=\"t-caption block mb-1\">Fornecedor</label>"""
if old not in text:
    raise SystemExit('supplier form marker not found')
text = text.replace(old, new, 1)

# 7) Insumo já cadastrado também ganha ação para virar revenda.
old = """                                <select\n                                  value={s.supplyClass || 'insumo'}\n                                  onChange={(e) => onUpdateSupply({ ...s, supplyClass: e.target.value })}\n                                  className=\"field field-select h-8 pl-2.5 text-[12px] w-28\"\n                                >\n                                  {SUPPLY_CLASSES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}\n                                </select>\n                              </td>"""
new = """                                <select\n                                  value={s.supplyClass || 'insumo'}\n                                  onChange={(e) => onUpdateSupply({ ...s, supplyClass: e.target.value })}\n                                  className=\"field field-select h-8 pl-2.5 text-[12px] w-28\"\n                                >\n                                  {SUPPLY_CLASSES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}\n                                </select>\n                                {revendaDoInsumo(s.name) ? (\n                                  <div className=\"t-nano mt-1 font-bold text-[#274133]\">Revenda ✓</div>\n                                ) : (\n                                  <button\n                                    type=\"button\"\n                                    onClick={() => criarRevendaDoInsumo(s.name, s.unit)}\n                                    className=\"mt-1 t-nano underline underline-offset-2 text-[#0E0937] font-bold\"\n                                  >\n                                    + Revenda também\n                                  </button>\n                                )}\n                              </td>"""
if old not in text:
    raise SystemExit('existing supply class marker not found')
text = text.replace(old, new, 1)

# 8) Passa handler ao componente.
old = """                    onAddSupplyPurchase={handleAddSupplyPurchase}\n                    onUpdateSupplyPurchase={handleUpdateSupplyPurchase}\n                    onDeleteSupplyPurchase={handleDeleteSupplyPurchase}\n                    onUpdateRecipe={handleUpdateRecipe}"""
new = """                    onAddSupplyPurchase={handleAddSupplyPurchase}\n                    onUpdateSupplyPurchase={handleUpdateSupplyPurchase}\n                    onDeleteSupplyPurchase={handleDeleteSupplyPurchase}\n                    onAddSeparatedProduct={handleAddSeparatedProduct}\n                    onUpdateRecipe={handleUpdateRecipe}"""
if old not in text:
    raise SystemExit('component invocation marker not found')
text = text.replace(old, new, 1)

# version marker
text = text.replace('2026-09-01-cmv-insumo-ficha-1', '2026-09-01-picker-revenda-2', 1)

if text == original:
    raise SystemExit('nothing changed')
path.write_text(text, encoding='utf-8')
print('patch aplicado')
