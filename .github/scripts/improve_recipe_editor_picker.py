from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old_version = '<meta name="app-version" content="2026-09-04-carrinho-esquerda-item-1" />'
new_version = '<meta name="app-version" content="2026-09-04-ficha-tipo-picker-largo-1" />'
if old_version in s:
    s = s.replace(old_version, new_version, 1)
elif new_version not in s:
    raise SystemExit('app version marker not found')

# PickerField: permitir que listas com nome + custo abram mais largas que o campo.
old_sig = """        inputProps = {},\n        emptyLabel = 'Nada encontrado'\n      }) => {"""
new_sig = """        inputProps = {},\n        emptyLabel = 'Nada encontrado',\n        panelMinWidth = 0\n      }) => {"""
if old_sig not in s:
    raise SystemExit('PickerField signature marker not found')
s = s.replace(old_sig, new_sig, 1)

old_measure = """          const r = el.getBoundingClientRect();\n          const below = window.innerHeight - r.bottom;\n          const flip = below < 180 && r.top > below;\n          setBox({\n            left: r.left,\n            width: r.width,\n            top: flip ? null : r.bottom + 6,\n            bottom: flip ? window.innerHeight - r.top + 6 : null,\n            maxHeight: Math.max(120, Math.min(260, (flip ? r.top : below) - 16))\n          });"""
new_measure = """          const r = el.getBoundingClientRect();\n          const below = window.innerHeight - r.bottom;\n          const flip = below < 180 && r.top > below;\n          const larguraDesejada = Math.max(r.width, Number(panelMinWidth) || 0);\n          const larguraPainel = Math.min(Math.max(160, window.innerWidth - 16), larguraDesejada);\n          const esquerdaPainel = Math.max(8, Math.min(r.left, window.innerWidth - larguraPainel - 8));\n          setBox({\n            left: esquerdaPainel,\n            width: larguraPainel,\n            top: flip ? null : r.bottom + 6,\n            bottom: flip ? window.innerHeight - r.top + 6 : null,\n            maxHeight: Math.max(120, Math.min(300, (flip ? r.top : below) - 16))\n          });"""
if old_measure not in s:
    raise SystemExit('PickerField measure marker not found')
s = s.replace(old_measure, new_measure, 1)

# RecipeEditor recebe a troca de tipo do produto da ficha.
old_props = """        onUpdateRecipe,\n        onAddItem,\n        onUpdateItem,\n        onDeleteItem\n      }) => {"""
new_props = """        onUpdateRecipe,\n        onAddItem,\n        onUpdateItem,\n        onDeleteItem,\n        catalogTypeOptions = [],\n        onChangeProductType\n      }) => {"""
if old_props not in s:
    raise SystemExit('RecipeEditor props marker not found')
s = s.replace(old_props, new_props, 1)

# Dicas mais curtas e legíveis.
s = s.replace("hint: `Comprado${o.hint ? ` · ${o.hint}` : ''}`", "hint: `Insumo${o.hint ? ` · ${o.hint}` : ''}`", 1)
s = s.replace("? `Fabricação própria · ${formatCurrencyBR(custoP)}/${unidadeP}${equivalenciaP}`", "? `Produção · ${formatCurrencyBR(custoP)}/${unidadeP}${equivalenciaP}`", 1)
s = s.replace(": `Fabricação própria · sem ficha/custo${equivalenciaP}`", ": `Produção · sem ficha/custo${equivalenciaP}`", 1)

# Cabeçalho da ficha: tipo do cadastro editável no próprio modal.
old_header = """              <div className=\"min-w-0\">\n                <div className=\"t-overline flex items-center gap-1.5 mb-1\">\n                  <Icons.ClipboardList className=\"w-3.5 h-3.5\" />\n                  Ficha técnica\n                </div>\n                <h3 className=\"t-title truncate\">{produto.name}</h3>\n              </div>"""
new_header = """              <div className=\"min-w-0 flex-1\">\n                <div className=\"t-overline flex items-center gap-1.5 mb-1\">\n                  <Icons.ClipboardList className=\"w-3.5 h-3.5\" />\n                  Ficha técnica\n                </div>\n                <div className=\"flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3\">\n                  <h3 className=\"t-title truncate flex-1\">{produto.name}</h3>\n                  {onChangeProductType && (\n                    <div className=\"w-full sm:w-40 shrink-0\">\n                      <label className=\"t-nano block mb-1\">Tipo do cadastro</label>\n                      <PickerField\n                        value=\"producao\"\n                        options={catalogTypeOptions}\n                        onPick={(opt) => onChangeProductType(opt.value)}\n                        className=\"field h-8 pl-2.5 text-[12px] font-bold\"\n                        panelMinWidth={190}\n                        title=\"Alterar o tipo deste produto\"\n                      />\n                    </div>\n                  )}\n                </div>\n              </div>"""
if old_header not in s:
    raise SystemExit('RecipeEditor header marker not found')
s = s.replace(old_header, new_header, 1)

# Os dois seletores principais usam a mesma largura e menus amplos.
s = s.replace('grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_260px] gap-3 items-end', 'grid grid-cols-1 sm:grid-cols-2 gap-3 items-end', 1)

old_insumo_picker = """                    placeholder=\"Escolha um insumo…\"\n                    className=\"field field-sm\"\n                  />"""
new_insumo_picker = """                    placeholder=\"Escolha um insumo…\"\n                    className=\"field field-sm\"\n                    panelMinWidth={520}\n                  />"""
if old_insumo_picker not in s:
    raise SystemExit('add supply picker marker not found')
s = s.replace(old_insumo_picker, new_insumo_picker, 1)

old_prod_picker = """                    placeholder=\"Produto da casa…\"\n                    className=\"field field-sm bg-black/[0.018]\"\n                    emptyLabel=\"Nenhum produto disponível\"\n                  />"""
new_prod_picker = """                    placeholder=\"Produto da casa…\"\n                    className=\"field field-sm bg-black/[0.018]\"\n                    emptyLabel=\"Nenhum produto disponível\"\n                    panelMinWidth={520}\n                  />"""
if old_prod_picker not in s:
    raise SystemExit('manufactured picker marker not found')
s = s.replace(old_prod_picker, new_prod_picker, 1)

# Seletor dentro da tabela: mais espaço para o nome e menu largo.
s = s.replace('<div className="w-40 sm:w-56">\n                            <PickerField', '<div className="w-60 sm:w-72">\n                            <PickerField', 1)
old_row_picker = """                              placeholder=\"Ingrediente\"\n                              className=\"field h-8 pl-2.5 text-[12px] font-semibold\"\n                            />"""
new_row_picker = """                              placeholder=\"Ingrediente\"\n                              className=\"field h-8 pl-2.5 text-[12px] font-semibold\"\n                              panelMinWidth={520}\n                            />"""
if old_row_picker not in s:
    raise SystemExit('recipe row picker marker not found')
s = s.replace(old_row_picker, new_row_picker, 1)

# Passa a troca de tipo para o modal global de ficha.
old_recipe_call = """                onAddItem={(component) => onAddRecipeItem(fichaAberta.produto.id, component)}\n                onUpdateItem={onUpdateRecipeItem}\n                onDeleteItem={onDeleteRecipeItem}\n              />"""
new_recipe_call = """                onAddItem={(component) => onAddRecipeItem(fichaAberta.produto.id, component)}\n                onUpdateItem={onUpdateRecipeItem}\n                onDeleteItem={onDeleteRecipeItem}\n                catalogTypeOptions={TIPOS_TABELA.filter((t) => ['producao', 'insumo', 'revenda'].includes(t.value))}\n                onChangeProductType={(novoTipo) => {\n                  const linha = cadastrosUnificados.find((c) => c.tipo === 'producao' && c.id === fichaAberta.produto.id);\n                  if (linha) alterarTipoDaTabela(linha, novoTipo);\n                }}\n              />"""
if old_recipe_call not in s:
    raise SystemExit('global RecipeEditor call marker not found')
s = s.replace(old_recipe_call, new_recipe_call, 1)

# Produção pode sair para Insumo/Revenda quando o único vínculo é sua própria
# ficha. Vitrine, histórico e uso como componente continuam bloqueando.
old_prod_conversion = """            // Produção: só sai desta tabela quando não existe nada ligado a ela.\n            const temLigacao =\n              slotItems.some((x) => x.productId === id) ||\n              standardPlans.some((x) => x.productId === id) ||\n              recipes.some((x) => x.productId === id) ||\n              recipeItems.some((x) => x.componentProductId === id) ||\n              saleRecords.some((x) => x.productId === id) ||\n              lossRecords.some((x) => x.productId === id) ||\n              productionRecords.some((x) => x.productId === id);\n            if (temLigacao) {\n              throw new Error(`“${nome}” já tem ficha, vitrine ou histórico de produção/venda. Para não perder vínculos, ele não pode trocar de Produção automaticamente.`);\n            }\n\n            const origem = products.find((x) => x.id === id) || item.source;\n            if (novoTipo === 'insumo') await garantirInsumo(origem?.priceUnit === 'kg' ? 'g' : 'un');\n            else await garantirRevenda(origem);\n\n            const { error } = await sb.from('products').delete().eq('id', id);\n            if (error) throw error;\n            setProducts((prev) => prev.filter((x) => x.id !== id));"""
new_prod_conversion = """            // Produção: a própria ficha pode ser removida na conversão. O que\n            // continua bloqueando é vínculo operacional externo: vitrine, histórico\n            // ou este produto sendo componente de outra ficha.\n            const receitasDoProduto = recipes.filter((x) => x.productId === id);\n            const idsReceitasDoProduto = new Set(receitasDoProduto.map((x) => x.id));\n            const temLigacaoExterna =\n              slotItems.some((x) => x.productId === id) ||\n              standardPlans.some((x) => x.productId === id) ||\n              recipeItems.some((x) => x.componentProductId === id) ||\n              saleRecords.some((x) => x.productId === id) ||\n              lossRecords.some((x) => x.productId === id) ||\n              productionRecords.some((x) => x.productId === id);\n            if (temLigacaoExterna) {\n              throw new Error(`“${nome}” tem vitrine, histórico ou é usado em outra ficha. Para não perder vínculos, ele não pode trocar de Produção automaticamente.`);\n            }\n            if (receitasDoProduto.length > 0) {\n              const apagarFicha = window.confirm(`“${nome}” tem ficha técnica. Ao mudar de Produção para ${novoTipo === 'insumo' ? 'Insumo' : 'Revenda'}, essa ficha será removida. Continuar?`);\n              if (!apagarFicha) return;\n            }\n\n            const origem = products.find((x) => x.id === id) || item.source;\n            if (novoTipo === 'insumo') await garantirInsumo(origem?.priceUnit === 'kg' ? 'g' : 'un');\n            else await garantirRevenda(origem);\n\n            const { error } = await sb.from('products').delete().eq('id', id);\n            if (error) throw error;\n            setProducts((prev) => prev.filter((x) => x.id !== id));\n            if (idsReceitasDoProduto.size > 0) {\n              setRecipes((prev) => prev.filter((x) => !idsReceitasDoProduto.has(x.id)));\n              setRecipeItems((prev) => prev.filter((x) => !idsReceitasDoProduto.has(x.recipeId)));\n            }"""
if old_prod_conversion not in s:
    raise SystemExit('production conversion block not found')
s = s.replace(old_prod_conversion, new_prod_conversion, 1)

# Verificações de segurança.
checks = [
    '2026-09-04-ficha-tipo-picker-largo-1',
    'panelMinWidth = 0',
    'panelMinWidth={520}',
    'Tipo do cadastro',
    'catalogTypeOptions={TIPOS_TABELA.filter',
    'temLigacaoExterna',
    'essa ficha será removida'
]
for marker in checks:
    if marker not in s:
        raise SystemExit(f'missing marker: {marker}')

p.write_text(s, encoding='utf-8')
