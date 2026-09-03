from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'Marker not found: {label}')
    s = s.replace(old, new, 1)

# Marca a versão para facilitar conferir o deploy.
s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-03-cmv-ficha-botao-1" />',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('app version marker not found')

replace_once(
"""        onUpdateProduct,
        onUpdateSeparatedProduct
      }) => {
        const [painel, setPainel] = useState('producao');
        const [ordem, setOrdem] = useState('cmv');""",
"""        onUpdateProduct,
        onUpdateSeparatedProduct,
        onUpdateRecipe,
        onAddRecipeItem,
        onUpdateRecipeItem,
        onDeleteRecipeItem
      }) => {
        const [painel, setPainel] = useState('producao');
        const [ordem, setOrdem] = useState('cmv');
        const [fichaProdutoId, setFichaProdutoId] = useState(null);""",
'cmv props and recipe state'
)

replace_once(
"""        const linhasRevenda = useMemo(() => separatedProducts""",
"""        const fichaAberta = linhasProducao.find(
          (linha) => String(linha.produto.id) === String(fichaProdutoId)
        ) || null;

        const supplyOptions = supplies.map((s) => ({
          value: s.id,
          label: s.name,
          hint: formatPrecoInsumo(custoUnitarioInsumo(s.id, supplyPurchases), s.unit)
        }));

        const linhasRevenda = useMemo(() => separatedProducts""",
'cmv open recipe data'
)

replace_once(
"""                        <th className=\"py-3 px-3 text-right font-bold\">Margem</th>
                        <th className=\"py-3 pl-3 text-center font-bold\">Rende</th>""",
"""                        <th className=\"py-3 px-3 text-right font-bold\">Margem</th>
                        <th className=\"py-3 px-3 text-center font-bold\">Rende</th>
                        <th className=\"py-3 pl-3 text-right font-bold\">Ficha</th>""",
'production recipe header'
)

replace_once(
"""                        <tr><td colSpan={10} className=\"text-center py-10\"><p className=\"t-body ink-quiet\">Nenhum produto cadastrado</p></td></tr>""",
"""                        <tr><td colSpan={11} className=\"text-center py-10\"><p className=\"t-body ink-quiet\">Nenhum produto cadastrado</p></td></tr>""",
'production empty colspan'
)

replace_once(
"""                          <td className=\"py-2.5 pl-3 text-center t-body tnum\">
                            {ficha ? `${ficha.yieldQty} ${ficha.yieldUnit}` : <span className=\"ink-quiet\">—</span>}
                          </td>
                        </tr>""",
"""                          <td className=\"py-2.5 px-3 text-center t-body tnum\">
                            {ficha ? `${ficha.yieldQty} ${ficha.yieldUnit}` : <span className=\"ink-quiet\">—</span>}
                          </td>
                          <td className=\"py-2.5 pl-3 text-right\">
                            <button
                              type=\"button\"
                              onClick={() => setFichaProdutoId(produto.id)}
                              title={`Abrir ficha técnica de ${produto.name}`}
                              className=\"btn btn-secondary btn-sm\"
                            >
                              <Icons.ClipboardList className=\"w-3.5 h-3.5\" />
                              {ficha && ficha.itens.length > 0 ? 'Abrir' : 'Montar'}
                            </button>
                          </td>
                        </tr>""",
'production recipe button'
)

replace_once(
"""            {/* ---------------- REVENDA ---------------- */}
            {painel === 'revenda' && (""",
"""            {fichaAberta && (
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

            {/* ---------------- REVENDA ---------------- */}
            {painel === 'revenda' && (""",
'cmv recipe editor'
)

replace_once(
"""                    onUpdateProduct={handleUpdateProduct}
                    onUpdateSeparatedProduct={handleUpdateSeparatedProduct}
                  />""",
"""                    onUpdateProduct={handleUpdateProduct}
                    onUpdateSeparatedProduct={handleUpdateSeparatedProduct}
                    onUpdateRecipe={handleUpdateRecipe}
                    onAddRecipeItem={handleAddRecipeItem}
                    onUpdateRecipeItem={handleUpdateRecipeItem}
                    onDeleteRecipeItem={handleDeleteRecipeItem}
                  />""",
'app cmv recipe handlers'
)

p.write_text(s, encoding='utf-8')
print('ok')
