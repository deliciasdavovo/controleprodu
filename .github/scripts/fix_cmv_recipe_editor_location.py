from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

editor = """            {fichaAberta && (
              <RecipeEditor
                produto={fichaAberta.produto}
                ficha={fichaAberta.ficha}
                custoUn={fichaAberta.custoUn}
                supplies={supplies}
                supplyPurchases={supplyPurchases}
                supplyOptions={supplyOptions}
                products={products}
                recipes={recipes}
                recipeItems={recipeItems}
                onClose={() => setFichaProdutoId(null)}
                onUpdateRecipe={(campos) => onUpdateRecipe(fichaAberta.produto.id, campos)}
                onAddItem={(component) => onAddRecipeItem(fichaAberta.produto.id, component)}
                onUpdateItem={onUpdateRecipeItem}
                onDeleteItem={onDeleteRecipeItem}
              />
            )}

"""

# Remove somente a cópia extra que ficou depois do fechamento do painel de fichas.
wrong = """              </div>
            )}

""" + editor + """            {/* ---------------- REVENDA ---------------- */}
            {painel === 'revenda' && (
              <div className="card p-5 sm:p-6">
                <p className="t-body pb-4">
                  Os itens de fora da vitrine desta unidade. Informe a compra e o custo por unidade sai sozinho.
"""
right = """              </div>
            )}

            {/* ---------------- REVENDA ---------------- */}
            {painel === 'revenda' && (
              <div className="card p-5 sm:p-6">
                <p className="t-body pb-4">
                  Os itens de fora da vitrine desta unidade. Informe a compra e o custo por unidade sai sozinho.
"""
if wrong not in s:
    raise SystemExit('extra SuppliesRecipes editor marker not found')
s = s.replace(wrong, right, 1)

# Coloca o editor na tela de CMV, imediatamente depois da tabela de Produção.
cmv_marker = """                <p className="t-micro pt-3">
                  Produto sem ficha técnica aceita o custo digitado à mão na coluna “custo un.” — assim ele já entra na conta.
                </p>
              </div>
            )}

            {/* ---------------- REVENDA ---------------- */}
            {painel === 'revenda' && (
"""
cmv_replacement = """                <p className="t-micro pt-3">
                  Produto sem ficha técnica aceita o custo digitado à mão na coluna “custo un.” — assim ele já entra na conta.
                </p>
              </div>
            )}

""" + editor + """            {/* ---------------- REVENDA ---------------- */}
            {painel === 'revenda' && (
"""
if cmv_marker not in s:
    raise SystemExit('CMV production footer marker not found')
s = s.replace(cmv_marker, cmv_replacement, 1)

p.write_text(s, encoding='utf-8')
print('ok')
