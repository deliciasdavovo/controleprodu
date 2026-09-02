from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-02-ficha-seletores-separados-1" />',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('app version marker not found')

needle = """        }, [supplyOptions, products, recipes, recipeItems, supplies, supplyPurchases, produto.id]);

        const interpretarComponente = (value) => {"""
replacement = """        }, [supplyOptions, products, recipes, recipeItems, supplies, supplyPurchases, produto.id]);

        // O fluxo normal da ficha é insumo comprado. Fabricação própria é uma
        // exceção e por isso fica num seletor separado, sem misturar as listas.
        const opcoesInsumos = useMemo(
          () => opcoesComponentes.filter((o) => String(o.value || '').startsWith('insumo:')),
          [opcoesComponentes]
        );
        const opcoesFabricados = useMemo(
          () => opcoesComponentes.filter((o) => String(o.value || '').startsWith('produto:')),
          [opcoesComponentes]
        );

        const interpretarComponente = (value) => {"""
if needle not in s:
    raise SystemExit('component options end marker not found')
s = s.replace(needle, replacement, 1)

old_ui = """            <div className=\"py-4\">
              <div className=\"w-full sm:max-w-sm\">
                <label className=\"t-caption block mb-1\">Adicionar ingrediente ou produto da casa</label>
                <PickerField
                  value={novoComponente}
                  options={opcoesComponentes}
                  onPick={adicionar}
                  placeholder=\"Insumo comprado ou fabricação própria…\"
                  className=\"field field-sm\"
                />
                <p className=\"t-nano mt-1.5\">
                  Produto da casa usa automaticamente o custo da própria ficha técnica.
                </p>
              </div>
            </div>"""
new_ui = """            <div className=\"py-4 border-b hairline\">
              <div className=\"grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_260px] gap-3 items-end\">
                <div className=\"min-w-0\">
                  <label className=\"t-caption block mb-1\">Adicionar insumo</label>
                  <PickerField
                    value={novoComponente}
                    options={opcoesInsumos}
                    onPick={adicionar}
                    placeholder=\"Escolha um insumo…\"
                    className=\"field field-sm\"
                  />
                </div>

                <div className=\"min-w-0\">
                  <div className=\"flex items-center justify-between gap-2 mb-1\">
                    <label className=\"t-caption\">Fabricação própria</label>
                    <span className=\"t-nano\">uso eventual</span>
                  </div>
                  <PickerField
                    value=\"\"
                    options={opcoesFabricados}
                    onPick={adicionar}
                    placeholder=\"Produto da casa…\"
                    className=\"field field-sm bg-black/[0.018]\"
                    emptyLabel=\"Nenhum produto disponível\"
                  />
                </div>
              </div>
            </div>"""
if old_ui not in s:
    raise SystemExit('recipe component picker UI marker not found')
s = s.replace(old_ui, new_ui, 1)

p.write_text(s, encoding='utf-8')
print('ok')
