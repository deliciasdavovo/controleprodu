from pathlib import Path
import re

index_path = Path('index.html')
schema_path = Path('supabase/schema.sql')
text = index_path.read_text(encoding='utf-8')
schema = schema_path.read_text(encoding='utf-8')
original = text

# 1) Versão
text = re.sub(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-02-produtos-cmv-vitrine-1" />', text, count=1)

# 2) Produtos sai de Vitrine e entra em CMV
old_nav = """            { id: 'historico', label: 'Histórico', fullLabel: 'Produção, Vendas e Perdas', icon: Icons.History },
            { id: 'fora', label: 'Fora da vitrine', fullLabel: 'Fora da Vitrine', icon: Icons.Coffee },
            { id: 'produtos', label: 'Produtos', fullLabel: 'Produtos', icon: Icons.Package }
          ]
        },
        cmv: {
          label: 'CMV',
          title: 'Custo, preço e fornecedores',
          tabs: [
            { id: 'insumos', label: 'Insumos', fullLabel: 'Insumos & Fichas', icon: Icons.Layers },"""
new_nav = """            { id: 'historico', label: 'Histórico', fullLabel: 'Produção, Vendas e Perdas', icon: Icons.History },
            { id: 'fora', label: 'Fora da vitrine', fullLabel: 'Fora da Vitrine', icon: Icons.Coffee }
          ]
        },
        cmv: {
          label: 'CMV',
          title: 'Custo, preço e fornecedores',
          tabs: [
            { id: 'produtos', label: 'Produtos', fullLabel: 'Cadastro de Produtos', icon: Icons.Package },
            { id: 'insumos', label: 'Insumos', fullLabel: 'Insumos & Fichas', icon: Icons.Layers },"""
if old_nav not in text:
    raise SystemExit('nav marker not found')
text = text.replace(old_nav, new_nav, 1)

# 3) Categorias ampliadas
old_categories = """      const PRODUCT_CATEGORIES = [
        { value: 'salgado', label: 'Salgado' },
        { value: 'doce', label: 'Doce' },
        { value: 'sobremesa', label: 'Sobremesa' }
      ];"""
new_categories = """      const PRODUCT_CATEGORIES = [
        { value: 'salgado', label: 'Salgado' },
        { value: 'doce', label: 'Doce' },
        { value: 'sobremesa', label: 'Sobremesa' },
        { value: 'pao', label: 'Pão' },
        { value: 'bolo', label: 'Bolo' },
        { value: 'confeitaria', label: 'Confeitaria' },
        { value: 'lanche', label: 'Lanche' },
        { value: 'refeicao', label: 'Refeição' },
        { value: 'bebida', label: 'Bebida' },
        { value: 'cafeteria', label: 'Cafeteria' },
        { value: 'encomenda', label: 'Encomenda' },
        { value: 'outro', label: 'Outro' }
      ];"""
if old_categories not in text:
    raise SystemExit('categories marker not found')
text = text.replace(old_categories, new_categories, 1)

# 4) Categoria e vitrine ficam independentes. Categorias adicionais ainda têm
# um destino padrão se o produto for marcado para vitrine.
old_showcase = """      // Cada tipo de vitrine aceita uma categoria do catálogo
      const CATEGORY_BY_SHOWCASE = { salgada: 'salgado', doce: 'doce', sobremesa: 'sobremesa' };

      const showcaseTypeOfCategory = (category) =>
        category === 'doce' ? 'doce' : category === 'sobremesa' ? 'sobremesa' : 'salgada';

      const categoryOfShowcaseType = (showcaseType) => CATEGORY_BY_SHOWCASE[showcaseType] || 'salgado';

      // Produtos que podem entrar em uma vitrine deste tipo
      const productsForShowcaseType = (products, showcaseType) =>
        products.filter((p) => showcaseTypeOfCategory(p.category) === showcaseType);"""
new_showcase = """      // Categoria comercial e presença na vitrine são coisas diferentes.
      // A categoria organiza o catálogo/CMV; quando o produto participa da
      // vitrine, este mapa define o móvel padrão dele.
      const CATEGORY_BY_SHOWCASE = { salgada: 'salgado', doce: 'doce', sobremesa: 'sobremesa' };
      const SHOWCASE_BY_CATEGORY = {
        salgado: 'salgada', pao: 'salgada', lanche: 'salgada', refeicao: 'salgada',
        doce: 'doce', bolo: 'doce', confeitaria: 'doce',
        sobremesa: 'sobremesa'
      };

      const showcaseTypeOfCategory = (category) => SHOWCASE_BY_CATEGORY[category] || 'salgada';

      const categoryOfShowcaseType = (showcaseType) => CATEGORY_BY_SHOWCASE[showcaseType] || 'salgado';

      // Só entra nos fluxos de vitrine se estiver explicitamente habilitado.
      const productsForShowcaseType = (products, showcaseType) =>
        products.filter((p) => p.showcaseEnabled !== false && showcaseTypeOfCategory(p.category) === showcaseType);"""
if old_showcase not in text:
    raise SystemExit('showcase mapping marker not found')
text = text.replace(old_showcase, new_showcase, 1)

# 5) Carrega TODOS os produtos: is_active passa a representar "vai para vitrine".
old_load = "run('produtos', sb.from('products').select('*').eq('is_active', true).order('name'))"
new_load = "run('produtos', sb.from('products').select('*').order('name'))"
if old_load not in text:
    raise SystemExit('products load marker not found')
text = text.replace(old_load, new_load, 1)

# 6) Mapeia flag de vitrine
old_from = """        category: row.category,
        defaultUnit: row.default_unit,"""
new_from = """        category: row.category,
        showcaseEnabled: row.is_active !== false,
        defaultUnit: row.default_unit,"""
if old_from not in text:
    raise SystemExit('fromProduct marker not found')
text = text.replace(old_from, new_from, 1)

# 7) Novo produto grava a flag
old_add = """              responsible: prod.responsible,
              category: prod.category,
              default_unit: prod.defaultUnit,"""
new_add = """              responsible: prod.responsible,
              category: prod.category,
              is_active: prod.showcaseEnabled !== false,
              default_unit: prod.defaultUnit,"""
if old_add not in text:
    raise SystemExit('add product marker not found')
text = text.replace(old_add, new_add, 1)

# 8) Edição grava a flag
old_update = """          const campos = {
            responsible: cleanResponsible(updated.responsible),
            category: updated.category,
            shelf_life_days: updated.shelfLifeDays,"""
new_update = """          const campos = {
            responsible: cleanResponsible(updated.responsible),
            category: updated.category,
            is_active: updated.showcaseEnabled !== false,
            shelf_life_days: updated.shelfLifeDays,"""
if old_update not in text:
    raise SystemExit('update product marker not found')
text = text.replace(old_update, new_update, 1)

# 9) Draft do catálogo conhece a opção de vitrine
old_blank = "const BLANK_DRAFT = { name: '', responsible: '', category: 'salgado', shelfLifeDays: 2, price: 8.5 };"
new_blank = "const BLANK_DRAFT = { name: '', responsible: '', category: 'salgado', showcaseEnabled: true, shelfLifeDays: 2, price: 8.5 };"
if old_blank not in text:
    raise SystemExit('blank draft marker not found')
text = text.replace(old_blank, new_blank, 1)

old_found = """                responsible: found.responsible || '',
                category: found.category,
                shelfLifeDays: found.shelfLifeDays,"""
new_found = """                responsible: found.responsible || '',
                category: found.category,
                showcaseEnabled: found.showcaseEnabled !== false,
                shelfLifeDays: found.shelfLifeDays,"""
if old_found not in text:
    raise SystemExit('found draft marker not found')
text = text.replace(old_found, new_found, 1)

old_dados = """            responsible: cleanResponsible(draft.responsible),
            category: draft.category,
            shelfLifeDays: Math.max(1, Number(draft.shelfLifeDays) || 1),"""
new_dados = """            responsible: cleanResponsible(draft.responsible),
            category: draft.category,
            showcaseEnabled: draft.showcaseEnabled !== false,
            shelfLifeDays: Math.max(1, Number(draft.shelfLifeDays) || 1),"""
if old_dados not in text:
    raise SystemExit('save dados marker not found')
text = text.replace(old_dados, new_dados, 1)

old_reset = "setDraft({ ...BLANK_DRAFT, responsible: dados.responsible, category: dados.category });"
new_reset = "setDraft({ ...BLANK_DRAFT, responsible: dados.responsible, category: dados.category, showcaseEnabled: dados.showcaseEnabled });"
if old_reset not in text:
    raise SystemExit('draft reset marker not found')
text = text.replace(old_reset, new_reset, 1)

# 10) Texto da tela deixa claro que é cadastro mestre do CMV
text = text.replace('<p className="t-body mt-1.5">Salgados, doces e sobremesas da casa.</p>', '<p className="t-body mt-1.5">Cadastro mestre para CMV e fichas técnicas. O produto pode existir sem participar da vitrine.</p>', 1)

# 11) Checkbox no cadastro em linha, logo depois da categoria
category_form_pattern = re.compile(r'''(<div className="col-span-5 md:col-span-2">\s*<label className="t-caption block mb-1">Categoria</label>\s*<select\s*ref=\{categoryRef\}.*?</select>\s*</div>)''', re.S)
m = category_form_pattern.search(text)
if not m:
    raise SystemExit('category form block not found')
showcase_form = m.group(1) + """

                  <div className="col-span-7 md:col-span-2">
                    <label className="t-caption block mb-1">Vai para vitrine?</label>
                    <label className="field field-md flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={draft.showcaseEnabled !== false}
                        onChange={(e) => setField('showcaseEnabled', e.target.checked)}
                        className="w-4 h-4"
                      />
                      <span className="t-callout font-semibold">{draft.showcaseEnabled !== false ? 'Sim' : 'Não'}</span>
                    </label>
                  </div>"""
text = text[:m.start()] + showcase_form + text[m.end():]

# 12) Coluna Vitrine na tabela
old_head = """                      <th className="py-3 px-3 font-bold">Categoria</th>
                      <th className="py-3 px-3 text-center font-bold">Validade</th>"""
new_head = """                      <th className="py-3 px-3 font-bold">Categoria</th>
                      <th className="py-3 px-3 text-center font-bold">Vitrine</th>
                      <th className="py-3 px-3 text-center font-bold">Validade</th>"""
if old_head not in text:
    raise SystemExit('table head marker not found')
text = text.replace(old_head, new_head, 1)
text = text.replace('colSpan={6} className="text-center py-10"><p className="t-body text-[#86868b]">Nenhum produto encontrado', 'colSpan={7} className="text-center py-10"><p className="t-body text-[#86868b]">Nenhum produto encontrado', 1)

# 13) Toggle por produto, logo depois da categoria na tabela
category_cell_pattern = re.compile(r'''(<td className="py-2\.5 px-3">\s*<select\s*value=\{p\.category\}.*?title="Categoria do produto".*?</select>\s*</td>)''', re.S)
m = category_cell_pattern.search(text)
if not m:
    raise SystemExit('category table cell not found')
showcase_cell = m.group(1) + """
                          <td className="py-2.5 px-3 text-center">
                            <label className="inline-flex items-center gap-1.5 cursor-pointer" title="Define se este produto aparece nos fluxos de vitrine e produção">
                              <input
                                type="checkbox"
                                checked={p.showcaseEnabled !== false}
                                onChange={(e) => onUpdateProduct({ ...p, showcaseEnabled: e.target.checked })}
                                className="w-4 h-4"
                              />
                              <span className={`t-micro font-bold ${p.showcaseEnabled !== false ? 'text-[#274133]' : 'text-[#86868b]'}`}>
                                {p.showcaseEnabled !== false ? 'Sim' : 'Não'}
                              </span>
                            </label>
                          </td>"""
text = text[:m.start()] + showcase_cell + text[m.end():]

# 14) Seletores rápidos da vitrine só listam produtos habilitados.
text = re.sub(
    r'products\.forEach\(\(p\) => \{\n\s*const tipo = showcaseTypeOfCategory\(p\.category\);',
    "products.filter((p) => p.showcaseEnabled !== false).forEach((p) => {\n            const tipo = showcaseTypeOfCategory(p.category);",
    text
)

# 15) Produto marcado fora da vitrine não pode ser digitado manualmente para alocar.
old_allocate = """          write('Alocar na vitrine', async () => {
            let product = existente;

            // Produto digitado que ainda não existe entra no catálogo"""
new_allocate = """          write('Alocar na vitrine', async () => {
            let product = existente;
            if (product && product.showcaseEnabled === false) {
              throw new Error(`“${product.name}” está marcado como fora da vitrine. Ative “Vai para vitrine” no cadastro de Produtos.`);
            }

            // Produto digitado que ainda não existe entra no catálogo"""
if old_allocate not in text:
    raise SystemExit('allocate guard marker not found')
text = text.replace(old_allocate, new_allocate, 1)

# Produto criado diretamente pela vitrine nasce habilitado.
old_auto = """                category: tipoDestino ? categoryOfShowcaseType(tipoDestino) : 'salgado',
                default_unit: 'un',"""
new_auto = """                category: tipoDestino ? categoryOfShowcaseType(tipoDestino) : 'salgado',
                is_active: true,
                default_unit: 'un',"""
if old_auto not in text:
    raise SystemExit('auto product marker not found')
text = text.replace(old_auto, new_auto, 1)

if text == original:
    raise SystemExit('index unchanged')
index_path.write_text(text, encoding='utf-8')

# 16) Schema aceita as novas categorias. is_active continua coluna existente,
# mas agora seu significado funcional é participação na vitrine.
old_constraint = "check (category in ('salgado', 'doce', 'sobremesa'))"
new_constraint = "check (category in ('salgado', 'doce', 'sobremesa', 'pao', 'bolo', 'confeitaria', 'lanche', 'refeicao', 'bebida', 'cafeteria', 'encomenda', 'outro'))"
if old_constraint not in schema:
    raise SystemExit('schema category constraint marker not found')
schema = schema.replace(old_constraint, new_constraint, 1)

comment_marker = "comment on column public.products.responsible is 'Quem produz e responde pelo produto. Vazio = sem responsável definido.';"
if comment_marker in schema and "products.is_active is 'Sim = participa" not in schema:
    schema = schema.replace(comment_marker, comment_marker + "\ncomment on column public.products.is_active is 'Sim = participa da vitrine/produção. Não = permanece no catálogo apenas para CMV e ficha técnica.';", 1)
schema_path.write_text(schema, encoding='utf-8')

# 17) Migração pequena para aplicar no banco já existente.
migration = Path('supabase/migrations/20260902_produtos_cmv_vitrine.sql')
migration.parent.mkdir(parents=True, exist_ok=True)
migration.write_text("""-- Produtos: categoria comercial independente da presença na vitrine\nalter table public.products drop constraint if exists products_category_check;\nalter table public.products\n  add constraint products_category_check\n  check (category in ('salgado', 'doce', 'sobremesa', 'pao', 'bolo', 'confeitaria', 'lanche', 'refeicao', 'bebida', 'cafeteria', 'encomenda', 'outro'));\n\ncomment on column public.products.is_active is\n  'Sim = participa da vitrine/produção. Não = permanece no catálogo apenas para CMV e ficha técnica.';\n""", encoding='utf-8')

print('patch produtos/CMV/vitrine aplicado')
