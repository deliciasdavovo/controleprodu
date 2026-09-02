from pathlib import Path
import re

p = Path('index.html')
text = p.read_text(encoding='utf-8')
original = text

# Version marker
text = re.sub(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-02-insumo-master-fields-1" />', text, count=1)

# 1) Existing supplies are master records: do not update class/unit from the quick purchase form.
old = """          if (existente) {
            onUpdateSupply({ ...existente, unit: draft.unit, supplyClass: draft.supplyClass });
          } else {
            const novo = await onAddSupply({ name: nome, unit: draft.unit, supplyClass: draft.supplyClass });"""
new = """          if (existente) {
            // Unidade, classe e revenda são dados mestres do insumo.
            // No formulário rápido de compra, insumo existente não altera esses campos.
          } else {
            const novo = await onAddSupply({ name: nome, unit: draft.unit, supplyClass: draft.supplyClass });"""
if old not in text:
    raise SystemExit('existing supply save marker not found')
text = text.replace(old, new, 1)

# 2) Lock Unit when an existing supply is selected.
old = """                        <select
                          value={draft.unit}
                          onChange={(e) => setDraft((d) => ({ ...d, unit: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          className="field field-md field-select"
                        >"""
new = """                        <select
                          value={draft.unit}
                          onChange={(e) => setDraft((d) => ({ ...d, unit: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          disabled={!!draftExistente}
                          title={draftExistente ? 'Unidade fixa do cadastro. Para alterar, use a tabela de insumos.' : 'Unidade do novo insumo'}
                          className="field field-md field-select disabled:bg-black/[0.035] disabled:text-[#86868b] disabled:cursor-not-allowed"
                        >"""
if old not in text:
    raise SystemExit('unit select marker not found')
text = text.replace(old, new, 1)

# 3) Lock Class when an existing supply is selected.
old = """                        <select
                          value={draft.supplyClass}
                          onChange={(e) => setDraft((d) => ({ ...d, supplyClass: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          title="Só organiza a lista — as três entram no CMV do mesmo jeito"
                          className="field field-md field-select"
                        >"""
new = """                        <select
                          value={draft.supplyClass}
                          onChange={(e) => setDraft((d) => ({ ...d, supplyClass: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          disabled={!!draftExistente}
                          title={draftExistente ? 'Classe fixa do cadastro. Para alterar, use a tabela de insumos.' : 'Só organiza a lista — as três entram no CMV do mesmo jeito'}
                          className="field field-md field-select disabled:bg-black/[0.035] disabled:text-[#86868b] disabled:cursor-not-allowed"
                        >"""
if old not in text:
    raise SystemExit('class select marker not found')
text = text.replace(old, new, 1)

# 4) Resale checkbox in quick form is fixed for existing supply and mirrors current table state.
old = """                            type="checkbox"
                            checked={draft.resaleAlso}
                            onChange={(e) => setDraft((d) => ({ ...d, resaleAlso: e.target.checked }))}
                            className="w-4 h-4"
                          />
                          <span className="t-callout font-semibold">Revenda também</span>"""
new = """                            type="checkbox"
                            checked={draftExistente ? !!revendaDoInsumo(draftExistente.name) : draft.resaleAlso}
                            disabled={!!draftExistente}
                            onChange={(e) => setDraft((d) => ({ ...d, resaleAlso: e.target.checked }))}
                            className="w-4 h-4 disabled:opacity-55 disabled:cursor-not-allowed"
                          />
                          <span className={`t-callout font-semibold ${draftExistente ? 'text-[#86868b]' : ''}`}>
                            Revenda também{draftExistente ? ' · edite na tabela' : ''}
                          </span>"""
if old not in text:
    raise SystemExit('quick resale checkbox marker not found')
text = text.replace(old, new, 1)

# 5) Add a real resale master toggle callback to SuppliesRecipesView props.
old = """        onAddSeparatedProduct,
        onUpdateRecipe,"""
new = """        onAddSeparatedProduct,
        onSetSupplyResale,
        onUpdateRecipe,"""
if old not in text:
    raise SystemExit('component props marker not found')
text = text.replace(old, new, 1)

# 6) Replace old one-way resale badge/button in the supply table with editable checkbox.
pattern = re.compile(r'''\{revendaDoInsumo\(s\.name\) \? \(\s*<span className="[^\"]*">Revenda ✓</span>\s*\) : \(\s*<button\s*type="button"\s*onClick=\{\(\) => criarRevendaDoInsumo\(s\.name, s\.unit\)\}.*?>\s*\+ Revenda também\s*</button>\s*\)\}''', re.S)
m = pattern.search(text)
if not m:
    raise SystemExit('table resale marker not found')
replacement = """<label className="mt-1.5 inline-flex items-center gap-1.5 cursor-pointer" title="Define se este insumo também aparece como item de revenda">
                                  <input
                                    type="checkbox"
                                    checked={!!revendaDoInsumo(s.name)}
                                    onChange={(e) => onSetSupplyResale(s, e.target.checked)}
                                    className="w-3.5 h-3.5"
                                  />
                                  <span className={`t-nano font-bold ${revendaDoInsumo(s.name) ? 'text-[#274133]' : 'text-[#86868b]'}`}>
                                    Revenda {revendaDoInsumo(s.name) ? 'Sim' : 'Não'}
                                  </span>
                                </label>"""
text = text[:m.start()] + replacement + text[m.end():]

# 7) Parent handler: activate/deactivate the matching separated product safely.
marker = """        // Preço, unidade de venda e custo dos itens de fora da vitrine — o que
        // a tela do CMV precisa mexer neles. A quantidade em estoque continua
        // sendo assunto do handleUpdateSeparatedQty.
        const handleUpdateSeparatedProduct = (updated) => {"""
if marker not in text:
    raise SystemExit('parent handler insertion marker not found')
handler = """        // Liga/desliga a opção de revenda a partir do cadastro mestre do insumo.
        // Se já houve revenda antes, reativa o mesmo registro em vez de criar duplicado.
        const handleSetSupplyResale = (supply, enabled) => {
          const nome = String(supply?.name || '').trim();
          if (!nome) return;

          write(enabled ? 'Ativar revenda do insumo' : 'Desativar revenda do insumo', async () => {
            const { data: existentes, error: buscaError } = await sb
              .from('separated_products')
              .select('*')
              .eq('unit_code', currentUnit)
              .eq('name', nome)
              .limit(1);
            if (buscaError) throw buscaError;

            const existente = existentes && existentes[0];

            if (enabled) {
              let linha;
              if (existente) {
                const { data, error } = await sb.from('separated_products').update({
                  is_active: true,
                  category: 'revenda',
                  unit_of_measure: supply.unit || existente.unit_of_measure || 'un'
                }).eq('id', existente.id).select();
                if (error) throw error;
                linha = data && data[0];
              } else {
                const { data, error } = await sb.from('separated_products').insert({
                  unit_code: currentUnit,
                  name: nome,
                  category: 'revenda',
                  current_qty: 0,
                  unit_of_measure: supply.unit || 'un',
                  min_qty: 0,
                  price: 0,
                  is_active: true
                }).select();
                if (error) throw error;
                linha = data && data[0];
              }

              if (linha) {
                const convertido = fromSeparated(linha);
                setSeparatedProducts((prev) => [
                  ...prev.filter((i) => i.id !== convertido.id && !(i.unit === currentUnit && normalizeName(i.productName) === normalizeName(nome))),
                  convertido
                ].sort((a, b) => a.productName.localeCompare(b.productName, 'pt-BR')));
              }
            } else if (existente) {
              const { error } = await sb.from('separated_products').update({ is_active: false }).eq('id', existente.id);
              if (error) throw error;
              setSeparatedProducts((prev) => prev.filter((i) => i.id !== existente.id));
            }
          });
        };

""" + marker
text = text.replace(marker, handler, 1)

# 8) Pass callback into SuppliesRecipesView.
old = """                    onAddSeparatedProduct={handleAddSeparatedProduct}
                    onUpdateRecipe={handleUpdateRecipe}"""
new = """                    onAddSeparatedProduct={handleAddSeparatedProduct}
                    onSetSupplyResale={handleSetSupplyResale}
                    onUpdateRecipe={handleUpdateRecipe}"""
if old not in text:
    raise SystemExit('component invocation marker not found')
text = text.replace(old, new, 1)

if text == original:
    raise SystemExit('index unchanged')

p.write_text(text, encoding='utf-8')
print('patched index.html')
