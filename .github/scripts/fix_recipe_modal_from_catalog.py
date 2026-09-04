from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old_version = '<meta name="app-version" content="2026-09-04-formulario-unico-enter-1" />'
new_version = '<meta name="app-version" content="2026-09-04-ficha-cadastro-modal-1" />'
if old_version in s:
    s = s.replace(old_version, new_version, 1)
elif new_version not in s:
    raise SystemExit('app version marker not found')

block = '''                {fichaAberta && (\n                  <RecipeEditor\n                    produto={fichaAberta.produto}\n                    ficha={fichaAberta.ficha}\n                    custoUn={fichaAberta.custoUn}\n                    supplies={supplies}\n                    supplyPurchases={supplyPurchases}\n                    supplyOptions={supplyOptions}\n                    products={products}\n                    recipes={recipes}\n                    recipeItems={recipeItems}\n                    onClose={() => setFichaProdutoId(null)}\n                    onUpdateRecipe={(campos) => onUpdateRecipe(fichaAberta.produto.id, campos)}\n                    onAddItem={(component) => onAddRecipeItem(fichaAberta.produto.id, component)}\n                    onUpdateItem={onUpdateRecipeItem}\n                    onDeleteItem={onDeleteRecipeItem}\n                  />\n                )}\n'''

if s.count(block) != 1:
    raise SystemExit(f'expected exactly one recipe editor block, found {s.count(block)}')

# Remove o editor de dentro do painel Fichas. Ali ele só renderizava quando a aba
# Fichas técnicas estava ativa, então o botão da tabela de Cadastros parecia não fazer nada.
s = s.replace(block, '', 1)

anchor = "            {/* Histórico de compras, o mesmo para insumo e revenda */}\n"
if anchor not in s:
    raise SystemExit('history anchor not found')

outside = '''            {/* Ficha técnica é modal global desta tela: pode ser aberta tanto\n                pela tabela de Cadastros quanto pela aba Fichas técnicas. */}\n            {fichaAberta && (\n              <RecipeEditor\n                produto={fichaAberta.produto}\n                ficha={fichaAberta.ficha}\n                custoUn={fichaAberta.custoUn}\n                supplies={supplies}\n                supplyPurchases={supplyPurchases}\n                supplyOptions={supplyOptions}\n                products={products}\n                recipes={recipes}\n                recipeItems={recipeItems}\n                onClose={() => setFichaProdutoId(null)}\n                onUpdateRecipe={(campos) => onUpdateRecipe(fichaAberta.produto.id, campos)}\n                onAddItem={(component) => onAddRecipeItem(fichaAberta.produto.id, component)}\n                onUpdateItem={onUpdateRecipeItem}\n                onDeleteItem={onDeleteRecipeItem}\n              />\n            )}\n\n'''
s = s.replace(anchor, outside + anchor, 1)

# Validações simples para impedir um commit que deixe dois modais ou nenhum.
if s.count('{fichaAberta && (') != 1:
    raise SystemExit(f'expected one global fichaAberta modal, found {s.count("{fichaAberta && (")}')
if 'Ficha técnica é modal global desta tela' not in s:
    raise SystemExit('global modal marker missing')
if 'onClick={() => setFichaProdutoId(x.id)} title="Abrir ficha técnica"' not in s:
    raise SystemExit('catalog recipe button missing')

p.write_text(s, encoding='utf-8')
