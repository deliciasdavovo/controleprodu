from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: esperado 1 trecho, encontrado {count}')
    text = text.replace(old, new, 1)

# 1) O cadastro passa a carregar os dados da compra no mesmo formulário.
replace_once(
    "        const BLANK_SUPPLY = { name: '', unit: 'g', supplyClass: 'insumo' };",
    "        const BLANK_SUPPLY = { name: '', unit: 'g', supplyClass: 'insumo', supplier: '', purchaseDate: getTodayDateString(), qty: '', cost: '' };",
    'BLANK_SUPPLY'
)

# 2) Informações do insumo existente e última compra, para autocomplete/contexto.
anchor = "        const comprasDaRevenda = (id) => resalePurchases.filter((c) => c.separatedProductId === id);\n"
insert = anchor + "\n        const draftExistente = supplies.find((s) => normalizeName(s.name) === normalizeName(draft.name.trim())) || null;\n        const draftUltimaCompra = draftExistente ? ultimaCompra(comprasDoInsumo(draftExistente.id)) : null;\n\n        const aplicarInsumoExistente = (nome) => {\n          const existente = supplies.find((s) => normalizeName(s.name) === normalizeName(String(nome || '').trim()));\n          if (!existente) return;\n          setDraft((d) => ({\n            ...d,\n            name: existente.name,\n            unit: existente.unit || d.unit,\n            supplyClass: existente.supplyClass || 'insumo'\n          }));\n        };\n\n        const avancarCadastroInsumo = (e) => {\n          if (e.key !== 'Enter' || e.shiftKey || e.ctrlKey || e.metaKey || e.altKey) return;\n          const form = e.currentTarget.form;\n          if (!form) return;\n          const campos = Array.from(form.querySelectorAll('[data-insumo-flow]'));\n          const idx = campos.indexOf(e.currentTarget);\n          if (idx >= 0 && idx < campos.length - 1) {\n            e.preventDefault();\n            const proximo = campos[idx + 1];\n            proximo.focus();\n            if (proximo.select && proximo.tagName === 'INPUT') proximo.select();\n          }\n        };\n"
replace_once(anchor, insert, 'helpers cadastro')

# 3) Salvar insumo e, quando houver qtd + valor, registrar a compra junto.
old_cadastrar = """        const cadastrar = (e) => {
          e.preventDefault();
          const nome = draft.name.trim();
          if (!nome) return;
          // Nome repetido vira edição do insumo que já existe, como no catálogo
          const existente = supplies.find((s) => normalizeName(s.name) === normalizeName(nome));
          if (existente) {
            onUpdateSupply({ ...existente, unit: draft.unit, supplyClass: draft.supplyClass });
          } else {
            onAddSupply({ name: nome, unit: draft.unit, supplyClass: draft.supplyClass });
          }
          setDraft({ ...BLANK_SUPPLY, unit: draft.unit, supplyClass: draft.supplyClass });
          setTimeout(() => nomeRef.current && nomeRef.current.focus(), 50);
        };"""
new_cadastrar = """        const cadastrar = async (e) => {
          e.preventDefault();
          const nome = draft.name.trim();
          if (!nome) return;

          const qty = Number(draft.qty) || 0;
          const cost = Number(draft.cost) || 0;
          if ((qty > 0 || cost > 0) && !(qty > 0 && cost > 0)) {
            window.alert('Para registrar a compra, preencha quantidade e valor pago.');
            return;
          }

          // Se já existe, esta linha vira uma NOVA COMPRA do mesmo insumo.
          const existente = supplies.find((s) => normalizeName(s.name) === normalizeName(nome));
          let supplyId = existente?.id || null;
          if (existente) {
            onUpdateSupply({ ...existente, unit: draft.unit, supplyClass: draft.supplyClass });
          } else {
            const novo = await onAddSupply({ name: nome, unit: draft.unit, supplyClass: draft.supplyClass });
            supplyId = novo?.id || null;
          }

          if (supplyId && qty > 0 && cost > 0) {
            onAddSupplyPurchase(supplyId, {
              supplier: draft.supplier.trim(),
              purchaseDate: draft.purchaseDate || getTodayDateString(),
              qty,
              cost
            });
          }

          setDraft({ ...BLANK_SUPPLY, unit: draft.unit, supplyClass: draft.supplyClass, purchaseDate: getTodayDateString() });
          setTimeout(() => nomeRef.current && nomeRef.current.focus(), 50);
        };"""
replace_once(old_cadastrar, new_cadastrar, 'cadastrar')

# 4) Texto do card deixa claro que compra e insumo são um único lançamento.
replace_once(
    "                    A unidade é a menor em que ele é usado — grama, ml ou unidade. O preço vem depois, no carrinho de compras.",
    "                    Cadastre o insumo e a compra na mesma linha. Se o insumo já existir, o lançamento vira uma nova compra no histórico.",
    'texto cadastro'
)

# 5) Autocomplete do nome e fluxo por Enter.
old_name = """                          ref={nomeRef}
                          type=\"text\"
                          value={draft.name}
                          onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
                          placeholder=\"ex: Farinha de trigo\"
                          className=\"field field-md font-semibold\"
                        />"""
new_name = """                          ref={nomeRef}
                          type=\"text\"
                          list=\"cadastro-insumos-list\"
                          value={draft.name}
                          onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
                          onBlur={(e) => aplicarInsumoExistente(e.target.value)}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          placeholder=\"Digite ou escolha um insumo\"
                          className=\"field field-md font-semibold\"
                        />"""
replace_once(old_name, new_name, 'campo nome')

# Unidade e classe participam do fluxo Enter.
replace_once(
    "                          value={draft.unit}\n                          onChange={(e) => setDraft((d) => ({ ...d, unit: e.target.value }))}\n                          className=\"field field-md field-select\"",
    "                          value={draft.unit}\n                          onChange={(e) => setDraft((d) => ({ ...d, unit: e.target.value }))}\n                          onKeyDown={avancarCadastroInsumo}\n                          data-insumo-flow\n                          className=\"field field-md field-select\"",
    'unidade flow'
)
replace_once(
    "                          value={draft.supplyClass}\n                          onChange={(e) => setDraft((d) => ({ ...d, supplyClass: e.target.value }))}\n                          title=\"Só organiza a lista — as três entram no CMV do mesmo jeito\"",
    "                          value={draft.supplyClass}\n                          onChange={(e) => setDraft((d) => ({ ...d, supplyClass: e.target.value }))}\n                          onKeyDown={avancarCadastroInsumo}\n                          data-insumo-flow\n                          title=\"Só organiza a lista — as três entram no CMV do mesmo jeito\"",
    'classe flow'
)

# 6) Acrescenta fornecedor, data, quantidade e valor antes do botão.
old_button_col = """                      <div className=\"col-span-12 sm:col-span-2\">
                        <button type=\"submit\" className=\"btn btn-primary btn-md w-full\">
                          <Icons.Plus className=\"w-4 h-4\" />
                          Cadastrar
                        </button>
                      </div>"""
new_button_col = """                      <div className=\"col-span-12 sm:col-span-4\">
                        <label className=\"t-caption block mb-1\">Fornecedor</label>
                        <input
                          type=\"text\"
                          list=\"cadastro-fornecedores-list\"
                          value={draft.supplier}
                          onChange={(e) => setDraft((d) => ({ ...d, supplier: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          placeholder={draftUltimaCompra?.supplier || 'Fornecedor'}
                          className=\"field field-md\"
                        />
                      </div>
                      <div className=\"col-span-6 sm:col-span-2\">
                        <label className=\"t-caption block mb-1\">Data</label>
                        <input
                          type=\"date\"
                          value={draft.purchaseDate}
                          onChange={(e) => setDraft((d) => ({ ...d, purchaseDate: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          className=\"field field-md\"
                        />
                      </div>
                      <div className=\"col-span-6 sm:col-span-2\">
                        <label className=\"t-caption block mb-1\">Qtd. comprada</label>
                        <input
                          type=\"number\"
                          min=\"0\"
                          step=\"0.001\"
                          value={draft.qty}
                          onChange={(e) => setDraft((d) => ({ ...d, qty: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          placeholder={draftUltimaCompra?.qty ? String(draftUltimaCompra.qty) : '0'}
                          className=\"field field-md text-right tnum no-spin\"
                        />
                      </div>
                      <div className=\"col-span-6 sm:col-span-2\">
                        <label className=\"t-caption block mb-1\">Valor pago (R$)</label>
                        <input
                          type=\"number\"
                          min=\"0\"
                          step=\"0.01\"
                          value={draft.cost}
                          onChange={(e) => setDraft((d) => ({ ...d, cost: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          placeholder={draftUltimaCompra?.cost ? String(draftUltimaCompra.cost) : '0,00'}
                          className=\"field field-md text-right tnum no-spin\"
                        />
                      </div>
                      <div className=\"col-span-6 sm:col-span-2\">
                        <button type=\"submit\" className=\"btn btn-primary btn-md w-full\">
                          <Icons.Plus className=\"w-4 h-4\" />
                          {draftExistente ? 'Registrar compra' : 'Cadastrar + compra'}
                        </button>
                      </div>"""
replace_once(old_button_col, new_button_col, 'campos compra')

# 7) Datalists + resumo da última compra logo abaixo do formulário.
old_form_close = """                    </div>
                  </form>
                </div>

                <div className=\"card p-5 sm:p-6\">"""
new_form_close = """                    </div>
                    <datalist id=\"cadastro-insumos-list\">
                      {supplies.map((s) => <option key={s.id} value={s.name} />)}
                    </datalist>
                    <datalist id=\"cadastro-fornecedores-list\">
                      {fornecedores.map((f) => <option key={f} value={f} />)}
                    </datalist>
                  </form>
                  {draftExistente && (
                    <div className=\"mt-3 px-3 py-2 rounded-xl bg-black/[0.035] t-micro\">
                      <strong>{draftExistente.name}</strong>
                      {draftUltimaCompra ? (
                        <span>
                          {' · última compra: '}
                          {draftUltimaCompra.qty || 0} {draftExistente.unit}
                          {' · '}{formatCurrencyBR(Number(draftUltimaCompra.cost) || 0)}
                          {draftUltimaCompra.supplier ? ` · ${draftUltimaCompra.supplier}` : ''}
                          {draftUltimaCompra.purchaseDate ? ` · ${formatDateBR(draftUltimaCompra.purchaseDate)}` : ''}
                        </span>
                      ) : <span> · ainda sem compra registrada</span>}
                    </div>
                  )}
                </div>

                <div className=\"card p-5 sm:p-6\">"""
replace_once(old_form_close, new_form_close, 'datalist e ultima compra')

# 8) onAddSupply passa a devolver o novo registro para o formulário poder criar a primeira compra.
replace_once(
    "        const handleAddSupply = (supply) => {\n          write('Cadastrar insumo', async () => {",
    "        const handleAddSupply = (supply) => {\n          return write('Cadastrar insumo', async () => {",
    'return handleAddSupply'
)

# 9) ID robusto da ficha (number/string não bloqueia abertura).
replace_once(
    "        const fichaAberta = produtosComFicha.find((x) => x.produto.id === fichaProdutoId) || null;",
    "        const fichaAberta = produtosComFicha.find((x) => String(x.produto.id) === String(fichaProdutoId)) || null;",
    'fichaAberta id'
)

# 10) O editor deixa de nascer longe, embaixo da tabela, e vira uma tela de edição visível.
recipe_start = text.index('      const RecipeEditor = ({')
old_root = '<div className="card p-5 sm:p-6">'
root_pos = text.index(old_root, recipe_start)
text = text[:root_pos] + '<div role="dialog" aria-modal="true" className="fixed inset-0 z-[90] bg-white overflow-y-auto p-5 sm:p-8">' + text[root_pos + len(old_root):]

# Fechar ficha e excluir item nunca submetem algum formulário ancestral por acidente.
recipe_end = text.index('      // ==========================================\n      // CMV', recipe_start)
section = text[recipe_start:recipe_end]
section = section.replace('<button onClick={onClose} title="Fechar ficha"', '<button type="button" onClick={onClose} title="Fechar ficha"', 1)
section = section.replace('<button\n                            onClick={() => onDeleteItem(item.id)}', '<button\n                            type="button"\n                            onClick={() => onDeleteItem(item.id)}', 1)
text = text[:recipe_start] + section + text[recipe_end:]

# 11) Botão Montar/Abrir explicitamente é botão comum.
replace_once(
    "                              <button\n                                onClick={() => setFichaProdutoId(produto.id)}\n                                className=\"btn btn-secondary btn-sm\"",
    "                              <button\n                                type=\"button\"\n                                onClick={() => setFichaProdutoId(produto.id)}\n                                className=\"btn btn-secondary btn-sm\"",
    'botao montar'
)

# Marcador de versão para ficar óbvio que o navegador recebeu o arquivo novo.
text = text.replace('content="2026-08-27-clique-duplo-1"', 'content="2026-09-01-cmv-insumo-ficha-1"', 1)

# Checagens simples de segurança antes de gravar.
required = [
    'Cadastrar + compra',
    'Registrar compra',
    'cadastro-insumos-list',
    'role="dialog" aria-modal="true" className="fixed inset-0 z-[90]',
    '2026-09-01-cmv-insumo-ficha-1'
]
for marker in required:
    if marker not in text:
        raise SystemExit(f'marcador final ausente: {marker}')

path.write_text(text, encoding='utf-8')
print('Patch CMV aplicado com sucesso')
