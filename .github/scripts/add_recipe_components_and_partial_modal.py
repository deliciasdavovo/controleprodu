from pathlib import Path
import re

index_path = Path('index.html')
schema_path = Path('supabase/schema.sql')
migration_path = Path('supabase/migrations/20260902_recipe_product_components.sql')

text = index_path.read_text(encoding='utf-8')
schema = schema_path.read_text(encoding='utf-8')
original = text
original_schema = schema


def replace_once(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f'{label} marker not found')
    text = text.replace(old, new, 1)

# Version marker
text = re.sub(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-02-ficha-parcial-componentes-1" />',
    text,
    count=1,
)

# ------------------------------------------------------------------
# CMV calculations: a recipe line can be a purchased supply OR a
# product manufactured by the bakery with its own technical sheet.
# ------------------------------------------------------------------
old_cost_block = """      // Custo de uma linha da ficha — só daquele insumo, na quantidade usada
      const custoDoItemDaFicha = (item, supplies, purchases) => {
        const supply = supplies.find((s) => s.id === item.supplyId);
        if (!supply) return 0;
        return custoUnitarioInsumo(supply.id, purchases) * qtdNaUnidadeBase(item, supply);
      };

      // Custo da receita inteira, do jeito que ela é produzida
      const custoDaFicha = (itens, supplies, purchases) =>
        (itens || []).reduce((total, item) => total + custoDoItemDaFicha(item, supplies, purchases), 0);

      // Custo de UMA unidade do produto, já na unidade em que ele é vendido.
      // Produto vendido a quilo precisa do peso da unidade: a receita rende 40
      // fatias de 120 g, então rende 4,8 kg — e é por kg que o preço é dado.
      const custoPorUnidadeDeVenda = (product, ficha) => {
        if (!ficha || !(ficha.custo > 0)) return Number(product?.manualCost) || 0;
        const rendimento = Number(ficha.yieldQty) || 0;
        if (rendimento <= 0) return 0;
        if ((product?.priceUnit || 'un') === 'kg') {
          const pesoG = Number(ficha.weightPerUnit) || 0;
          if (pesoG > 0) return ficha.custo / ((rendimento * pesoG) / 1000);
        }
        return ficha.custo / rendimento;
      };
"""
new_cost_block = """      // Produto fabricado pela própria casa também pode ser ingrediente de outra
      // ficha. Ex.: a ficha do lanche usa 1 un do pão de brioche, e o custo do
      // pão vem da ficha do próprio brioche. Assim uma mudança na farinha
      // atravessa automaticamente todas as fichas que usam aquele pão.
      const converterQtdComponente = (qtd, origem, destino) => {
        const n = Number(qtd) || 0;
        const de = origem || destino || 'un';
        const para = destino || de;
        if (!n || de === para) return n;
        if (de === 'kg' && para === 'g') return n * 1000;
        if (de === 'g' && para === 'kg') return n / 1000;
        if (de === 'L' && para === 'ml') return n * 1000;
        if (de === 'ml' && para === 'L') return n / 1000;
        return n;
      };

      const unidadesDeComponente = (unidade) => {
        const u = unidade || 'un';
        if (u === 'g') return ['g', 'kg'];
        if (u === 'kg') return ['kg', 'g'];
        if (u === 'ml') return ['ml', 'L'];
        if (u === 'L') return ['L', 'ml'];
        return [u];
      };

      // Verifica dependência entre produtos para não criar uma ficha circular:
      // A usa B e B usa A. Além de confundir a operação, isso nunca teria um
      // custo final calculável.
      const produtoDependeDe = (productId, targetId, recipes, recipeItems, visitados = new Set()) => {
        if (!productId || !targetId) return false;
        if (productId === targetId) return true;
        if (visitados.has(productId)) return false;
        const proximosVisitados = new Set(visitados);
        proximosVisitados.add(productId);
        const ficha = recipes.find((r) => r.productId === productId);
        if (!ficha) return false;
        return recipeItems
          .filter((i) => i.recipeId === ficha.id && i.componentProductId)
          .some((i) => i.componentProductId === targetId
            || produtoDependeDe(i.componentProductId, targetId, recipes, recipeItems, proximosVisitados));
      };

      // Custo de uma linha da ficha. A linha pode vir de uma compra (supplyId)
      // ou de uma fabricação própria (componentProductId).
      const custoDoItemDaFicha = (
        item, supplies, purchases, products = [], recipes = [], recipeItems = [], pilha = new Set()
      ) => {
        if (item?.componentProductId) {
          const componente = products.find((p) => p.id === item.componentProductId);
          if (!componente || pilha.has(componente.id)) return 0;
          const fichaComponente = fichaDoProduto(
            componente.id, recipes, recipeItems, supplies, purchases, products, pilha
          );
          if (!fichaComponente || !(fichaComponente.custo > 0)) return 0;
          const rendimento = Number(fichaComponente.yieldQty) || 0;
          if (rendimento <= 0) return 0;
          const unidadeSaida = fichaComponente.yieldUnit || 'un';
          const qtd = converterQtdComponente(
            item.qty,
            item.usageUnit || unidadeSaida,
            unidadeSaida
          );
          return (fichaComponente.custo / rendimento) * qtd;
        }

        const supply = supplies.find((s) => s.id === item?.supplyId);
        if (!supply) return 0;
        return custoUnitarioInsumo(supply.id, purchases) * qtdNaUnidadeBase(item, supply);
      };

      // Custo da receita inteira, do jeito que ela é produzida.
      const custoDaFicha = (
        itens, supplies, purchases, products = [], recipes = [], recipeItems = [], pilha = new Set()
      ) => (itens || []).reduce(
        (total, item) => total + custoDoItemDaFicha(
          item, supplies, purchases, products, recipes, recipeItems, pilha
        ),
        0
      );

      // Custo de UMA unidade do produto, já na unidade em que ele é vendido.
      // Produto vendido a quilo precisa do peso da unidade: a receita rende 40
      // fatias de 120 g, então rende 4,8 kg — e é por kg que o preço é dado.
      const custoPorUnidadeDeVenda = (product, ficha) => {
        if (!ficha || !(ficha.custo > 0)) return Number(product?.manualCost) || 0;
        const rendimento = Number(ficha.yieldQty) || 0;
        if (rendimento <= 0) return 0;
        if ((product?.priceUnit || 'un') === 'kg') {
          const pesoG = Number(ficha.weightPerUnit) || 0;
          if (pesoG > 0) return ficha.custo / ((rendimento * pesoG) / 1000);
        }
        return ficha.custo / rendimento;
      };
"""
replace_once(old_cost_block, new_cost_block, 'cost block')

old_ficha = """      const fichaDoProduto = (productId, recipes, recipeItems, supplies, purchases) => {
        const recipe = recipes.find((r) => r.productId === productId);
        if (!recipe) return null;
        const itens = recipeItems.filter((i) => i.recipeId === recipe.id);
        return {
          ...recipe,
          itens,
          custo: custoDaFicha(itens, supplies, purchases)
        };
      };"""
new_ficha = """      const fichaDoProduto = (
        productId, recipes, recipeItems, supplies, purchases, products = [], pilha = new Set()
      ) => {
        if (pilha.has(productId)) return null;
        const recipe = recipes.find((r) => r.productId === productId);
        if (!recipe) return null;
        const itens = recipeItems.filter((i) => i.recipeId === recipe.id);
        const proximaPilha = new Set(pilha);
        proximaPilha.add(productId);
        return {
          ...recipe,
          itens,
          custo: custoDaFicha(
            itens, supplies, purchases, products, recipes, recipeItems, proximaPilha
          )
        };
      };"""
replace_once(old_ficha, new_ficha, 'ficha helper')

# Adapter for new DB column.
replace_once(
"""      const fromRecipeItem = (row) => ({
        id: row.id,
        recipeId: row.recipe_id,
        supplyId: row.supply_id,
        qty: Number(row.qty) || 0,
        usageUnit: row.usage_unit || ''
      });""",
"""      const fromRecipeItem = (row) => ({
        id: row.id,
        recipeId: row.recipe_id,
        supplyId: row.supply_id || null,
        componentProductId: row.component_product_id || null,
        qty: Number(row.qty) || 0,
        usageUnit: row.usage_unit || ''
      });""",
'fromRecipeItem')

# All product ficha calculations in views need the product catalog available so
# manufactured sub-components can resolve their own recipes.
text, ficha_call_count = re.subn(
    r'fichaDoProduto\(([^,()]+), recipes, recipeItems, supplies, supplyPurchases\)',
    r'fichaDoProduto(\1, recipes, recipeItems, supplies, supplyPurchases, products)',
    text,
)
if ficha_call_count < 2:
    raise SystemExit(f'expected at least 2 fichaDoProduto view calls, got {ficha_call_count}')

# Supplies -> RecipeEditor receives enough context for manufactured components.
replace_once(
"""                    supplies={supplies}
                    supplyPurchases={supplyPurchases}
                    supplyOptions={supplyOptions}
                    onClose={() => setFichaProdutoId(null)}""",
"""                    supplies={supplies}
                    supplyPurchases={supplyPurchases}
                    supplyOptions={supplyOptions}
                    products={products}
                    recipes={recipes}
                    recipeItems={recipeItems}
                    onClose={() => setFichaProdutoId(null)}""",
'recipe editor props')

replace_once(
"""                    onAddItem={(supplyId) => onAddRecipeItem(fichaAberta.produto.id, supplyId)}""",
"""                    onAddItem={(component) => onAddRecipeItem(fichaAberta.produto.id, component)}""",
'recipe add callback')

# RecipeEditor signature + component options + partial modal.
replace_once(
"""        supplyPurchases,
        supplyOptions,
        onClose,""",
"""        supplyPurchases,
        supplyOptions,
        products,
        recipes,
        recipeItems,
        onClose,""",
'recipe editor signature')

replace_once(
"""        const [novoInsumo, setNovoInsumo] = useState('');

        const itens = ficha?.itens || [];
        const custoTotal = ficha?.custo || 0;
        const rendimento = ficha?.yieldQty || 1;
        const preco = Number(produto.price) || 0;
        const cmv = calcularCmv(custoUn, preco);
        const calculavel = preco > 0 && custoUn > 0;

        const adicionar = (opt) => {
          if (!opt?.value) return;
          onAddItem(opt.value);
          setNovoInsumo('');
        };""",
"""        const [novoComponente, setNovoComponente] = useState('');

        const itens = ficha?.itens || [];
        const custoTotal = ficha?.custo || 0;
        const rendimento = ficha?.yieldQty || 1;
        const preco = Number(produto.price) || 0;
        const cmv = calcularCmv(custoUn, preco);
        const calculavel = preco > 0 && custoUn > 0;

        const opcoesComponentes = useMemo(() => {
          const comprados = supplyOptions.map((o) => ({
            ...o,
            value: `insumo:${o.value}`,
            hint: `Comprado${o.hint ? ` · ${o.hint}` : ''}`
          }));

          const fabricados = products
            .filter((p) => p.id !== produto.id && !produtoDependeDe(p.id, produto.id, recipes, recipeItems))
            .map((p) => {
              const fichaP = fichaDoProduto(p.id, recipes, recipeItems, supplies, supplyPurchases, products);
              const rendimentoP = Number(fichaP?.yieldQty) || 0;
              const unidadeP = fichaP?.yieldUnit || 'un';
              const custoP = fichaP && rendimentoP > 0 ? fichaP.custo / rendimentoP : 0;
              return {
                value: `produto:${p.id}`,
                label: p.name,
                hint: custoP > 0
                  ? `Fabricação própria · ${formatCurrencyBR(custoP)}/${unidadeP}`
                  : 'Fabricação própria · sem ficha/custo'
              };
            });

          return [...comprados, ...fabricados];
        }, [supplyOptions, products, recipes, recipeItems, supplies, supplyPurchases, produto.id]);

        const interpretarComponente = (value) => {
          const raw = String(value || '');
          if (raw.startsWith('produto:')) {
            return { supplyId: null, componentProductId: raw.slice('produto:'.length) };
          }
          if (raw.startsWith('insumo:')) {
            return { supplyId: raw.slice('insumo:'.length), componentProductId: null };
          }
          return null;
        };

        const adicionar = (opt) => {
          const componente = interpretarComponente(opt?.value);
          if (!componente) return;
          onAddItem(componente);
          setNovoComponente('');
        };""",
'recipe editor options')

replace_once(
"""        return (
          <div role="dialog" aria-modal="true" className="fixed inset-0 z-[90] bg-white overflow-y-auto p-5 sm:p-8">
            <div className="flex items-start justify-between gap-3 pb-4 border-b hairline">""",
"""        return (
          <div
            role="dialog"
            aria-modal="true"
            aria-label={`Ficha técnica de ${produto.name}`}
            className="fixed inset-0 z-[90] bg-black/30 backdrop-blur-[2px] flex items-start sm:items-center justify-center p-3 sm:p-6 overflow-y-auto"
          >
            <button
              type="button"
              aria-label="Fechar ficha técnica"
              onClick={onClose}
              className="absolute inset-0"
            />
            <div className="relative bg-white rounded-[24px] w-full max-w-5xl max-h-[88vh] overflow-y-auto shadow-[0_24px_64px_rgba(0,0,0,0.24)] border hairline my-auto">
              <div className="p-5 sm:p-6">
            <div className="flex items-start justify-between gap-3 pb-4 border-b hairline">""",
'partial recipe modal')

replace_once(
"""                <label className="t-caption block mb-1">Adicionar insumo à ficha</label>
                <PickerField
                  value={novoInsumo}
                  options={supplyOptions}
                  onPick={adicionar}
                  placeholder="Escolha um insumo…"
                  className="field field-sm"
                />""",
"""                <label className="t-caption block mb-1">Adicionar ingrediente ou produto da casa</label>
                <PickerField
                  value={novoComponente}
                  options={opcoesComponentes}
                  onPick={adicionar}
                  placeholder="Insumo comprado ou fabricação própria…"
                  className="field field-sm"
                />
                <p className="t-nano mt-1.5">
                  Produto da casa usa automaticamente o custo da própria ficha técnica.
                </p>""",
'component picker')

replace_once(
"""                    <th className="py-3 pr-3 font-bold">Insumo</th>
                    <th className="py-3 px-3 text-right font-bold">Quantidade</th>
                    <th className="py-3 px-3 font-bold">Unidade</th>
                    <th className="py-3 px-3 text-right font-bold">Preço do insumo</th>""",
"""                    <th className="py-3 pr-3 font-bold">Ingrediente / componente</th>
                    <th className="py-3 px-3 text-right font-bold">Quantidade</th>
                    <th className="py-3 px-3 font-bold">Unidade</th>
                    <th className="py-3 px-3 text-right font-bold">Custo de origem</th>""",
'table headers')

replace_once(
"""                    <tr><td colSpan={7} className="text-center py-10"><p className="t-body ink-quiet">Ficha vazia — escolha o primeiro insumo acima</p></td></tr>""",
"""                    <tr><td colSpan={7} className="text-center py-10"><p className="t-body ink-quiet">Ficha vazia — escolha o primeiro ingrediente ou produto da casa acima</p></td></tr>""",
'empty recipe')

old_row_prep = """                  ) : itens.map((item) => {
                    const supply = supplies.find((s) => s.id === item.supplyId);
                    const custoLinha = custoDoItemDaFicha(item, supplies, supplyPurchases);
                    const peso = custoTotal > 0 ? (custoLinha / custoTotal) * 100 : 0;
                    const unidades = supply
                      ? [supply.unit, ...(supply.variationUnit && Number(supply.variationFactor) > 0 ? [supply.variationUnit] : [])]
                      : ['un'];
                    return ("""
new_row_prep = """                  ) : itens.map((item) => {
                    const supply = item.supplyId ? supplies.find((s) => s.id === item.supplyId) : null;
                    const componentProduct = item.componentProductId
                      ? products.find((p) => p.id === item.componentProductId)
                      : null;
                    const componentFicha = componentProduct
                      ? fichaDoProduto(componentProduct.id, recipes, recipeItems, supplies, supplyPurchases, products, new Set([produto.id]))
                      : null;
                    const custoLinha = custoDoItemDaFicha(
                      item, supplies, supplyPurchases, products, recipes, recipeItems, new Set([produto.id])
                    );
                    const peso = custoTotal > 0 ? (custoLinha / custoTotal) * 100 : 0;
                    const unidadeBase = supply?.unit || componentFicha?.yieldUnit || 'un';
                    const unidades = supply
                      ? [supply.unit, ...(supply.variationUnit && Number(supply.variationFactor) > 0 ? [supply.variationUnit] : [])]
                      : unidadesDeComponente(unidadeBase);
                    const seletorValue = item.componentProductId
                      ? `produto:${item.componentProductId}`
                      : `insumo:${item.supplyId || ''}`;
                    const rendimentoComponente = Number(componentFicha?.yieldQty) || 0;
                    const custoOrigem = supply
                      ? formatPrecoInsumo(custoUnitarioInsumo(supply.id, supplyPurchases), supply.unit)
                      : (componentFicha && rendimentoComponente > 0 && componentFicha.custo > 0
                        ? `${formatCurrencyBR(componentFicha.custo / rendimentoComponente)}/${unidadeBase}`
                        : '—');
                    return ("""
replace_once(old_row_prep, new_row_prep, 'recipe row prep')

replace_once(
"""                            <PickerField
                              value={item.supplyId}
                              options={supplyOptions}
                              onPick={(opt) => onUpdateItem({ ...item, supplyId: opt.value, usageUnit: '' })}
                              placeholder="Insumo"
                              className="field h-8 pl-2.5 text-[12px] font-semibold"
                            />""",
"""                            <PickerField
                              value={seletorValue}
                              options={opcoesComponentes}
                              onPick={(opt) => {
                                const componente = interpretarComponente(opt.value);
                                if (!componente) return;
                                onUpdateItem({ ...item, ...componente, usageUnit: '' });
                              }}
                              placeholder="Ingrediente"
                              className="field h-8 pl-2.5 text-[12px] font-semibold"
                            />""",
'row component picker')

replace_once(
"""                          <select
                            value={item.usageUnit || (supply?.unit || 'un')}
                            onChange={(e) => onUpdateItem({ ...item, usageUnit: e.target.value === supply?.unit ? '' : e.target.value })}
                            title="A unidade em que a quantidade acima está escrita"
                            className="field field-select h-8 pl-2.5 text-[12px] w-20"
                          >
                            {unidades.map((u) => <option key={u} value={u}>{u}</option>)}
                          </select>""",
"""                          <div className="w-20">
                            <PickerField
                              value={item.usageUnit || unidadeBase}
                              options={unidades.map((u) => ({ value: u, label: u }))}
                              onPick={(opt) => onUpdateItem({
                                ...item,
                                usageUnit: opt.value === unidadeBase ? '' : opt.value
                              })}
                              title="A unidade em que a quantidade acima está escrita"
                              className="field h-8 pl-2.5 text-[12px]"
                            />
                          </div>""",
'row usage unit picker')

replace_once(
"""                          {supply ? formatPrecoInsumo(custoUnitarioInsumo(supply.id, supplyPurchases), supply.unit) : '—'}""",
"""                          {custoOrigem}""",
'origin cost')

replace_once(
"""                            title="Tirar insumo da ficha"""",
"""                            title="Tirar componente da ficha""",
'delete title')

replace_once(
"""            <p className="t-micro pt-3">
              Insumo sem compra lançada entra com custo zero — o CMV do produto fica menor do que é de verdade.
            </p>
          </div>
        );""",
"""            <p className="t-micro pt-3">
              Insumo sem compra e produto da casa sem ficha entram com custo zero — complete a origem para o CMV ficar correto.
            </p>
              </div>
            </div>
          </div>
        );""",
'recipe modal close')

# App handlers: write either supply_id OR component_product_id.
replace_once(
"""        const handleAddRecipeItem = (productId, supplyId) => {
          write('Adicionar insumo à ficha', async () => {
            const ficha = await garantirFicha(productId);
            const linhas = await run('recipe_items', sb.from('recipe_items').insert({
              recipe_id: ficha.id,
              supply_id: supplyId,
              qty: 0,
              usage_unit: ''
            }).select());
            setRecipeItems((prev) => [...prev, fromRecipeItem(linhas[0])]);
          });
        };""",
"""        const handleAddRecipeItem = (productId, component) => {
          const supplyId = component?.supplyId || null;
          const componentProductId = component?.componentProductId || null;
          if (!supplyId && !componentProductId) return;
          if (componentProductId && produtoDependeDe(componentProductId, productId, recipes, recipeItems)) {
            window.alert('Esse produto criaria uma ficha circular. Escolha outro componente.');
            return;
          }

          write(componentProductId ? 'Adicionar fabricação própria à ficha' : 'Adicionar insumo à ficha', async () => {
            const ficha = await garantirFicha(productId);
            const linhas = await run('recipe_items', sb.from('recipe_items').insert({
              recipe_id: ficha.id,
              supply_id: supplyId,
              component_product_id: componentProductId,
              qty: 0,
              usage_unit: ''
            }).select());
            setRecipeItems((prev) => [...prev, fromRecipeItem(linhas[0])]);
          });
        };""",
'add recipe component handler')

replace_once(
"""        const handleUpdateRecipeItem = (updated) => {
          setRecipeItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
          writeSoon(`ficha-item:${updated.id}`, 'Atualizar item da ficha', () =>
            run('recipe_items', sb.from('recipe_items').update({
              supply_id: updated.supplyId,
              qty: Number(updated.qty) || 0,
              usage_unit: updated.usageUnit || ''
            }).eq('id', updated.id))
          );
        };""",
"""        const handleUpdateRecipeItem = (updated) => {
          const fichaPai = recipes.find((r) => r.id === updated.recipeId);
          if (updated.componentProductId && fichaPai
            && produtoDependeDe(updated.componentProductId, fichaPai.productId, recipes, recipeItems)) {
            window.alert('Esse produto criaria uma ficha circular. Escolha outro componente.');
            return;
          }

          const normalizado = {
            ...updated,
            supplyId: updated.componentProductId ? null : (updated.supplyId || null),
            componentProductId: updated.componentProductId || null
          };
          setRecipeItems((prev) => prev.map((i) => (i.id === normalizado.id ? normalizado : i)));
          writeSoon(`ficha-item:${normalizado.id}`, 'Atualizar item da ficha', () =>
            run('recipe_items', sb.from('recipe_items').update({
              supply_id: normalizado.supplyId,
              component_product_id: normalizado.componentProductId,
              qty: Number(normalizado.qty) || 0,
              usage_unit: normalizado.usageUnit || ''
            }).eq('id', normalizado.id))
          );
        };""",
'update recipe component handler')

text = text.replace("write('Remover insumo da ficha'", "write('Remover componente da ficha'", 1)

# ------------------------------------------------------------------
# Schema: recipe_items accepts exactly one source: supply OR product.
# ------------------------------------------------------------------
old_schema_table = """create table if not exists public.recipe_items (
  id          uuid primary key default gen_random_uuid(),
  recipe_id   uuid not null references public.recipes (id) on delete cascade,
  supply_id   uuid not null references public.supplies (id) on delete restrict,
  qty         numeric(12,3) not null default 0,
  usage_unit  text not null default '',
  created_at  timestamptz not null default now(),
  constraint recipe_items_qty_check check (qty >= 0)
);

create index if not exists recipe_items_recipe_idx on public.recipe_items (recipe_id);
create index if not exists recipe_items_supply_idx on public.recipe_items (supply_id);"""
new_schema_table = """create table if not exists public.recipe_items (
  id                    uuid primary key default gen_random_uuid(),
  recipe_id             uuid not null references public.recipes (id) on delete cascade,
  supply_id             uuid references public.supplies (id) on delete restrict,
  component_product_id  uuid references public.products (id) on delete restrict,
  qty                   numeric(12,3) not null default 0,
  usage_unit            text not null default '',
  created_at            timestamptz not null default now(),
  constraint recipe_items_qty_check check (qty >= 0),
  constraint recipe_items_source_check check (
    (supply_id is not null and component_product_id is null)
    or (supply_id is null and component_product_id is not null)
  )
);

-- Bancos anteriores tinham supply_id obrigatório. Agora uma linha pode vir de
-- um produto fabricado pela própria casa, mas nunca das duas origens ao mesmo tempo.
alter table public.recipe_items
  add column if not exists component_product_id uuid references public.products (id) on delete restrict;
alter table public.recipe_items
  alter column supply_id drop not null;
alter table public.recipe_items
  drop constraint if exists recipe_items_source_check;
alter table public.recipe_items
  add constraint recipe_items_source_check check (
    (supply_id is not null and component_product_id is null)
    or (supply_id is null and component_product_id is not null)
  );

create index if not exists recipe_items_recipe_idx on public.recipe_items (recipe_id);
create index if not exists recipe_items_supply_idx on public.recipe_items (supply_id);
create index if not exists recipe_items_component_product_idx on public.recipe_items (component_product_id);"""
if old_schema_table not in schema:
    raise SystemExit('schema recipe_items marker not found')
schema = schema.replace(old_schema_table, new_schema_table, 1)

schema = schema.replace(
"""-- Cada linha é um insumo dentro da receita. usage_unit vazio significa
-- que a quantidade está na unidade base do insumo; preenchido, ela está
-- na variação dele (2 latas, 3 fatias) e o app converte na hora da conta.""",
"""-- Cada linha é um componente da receita: ou um insumo comprado, ou outro
-- produto fabricado pela própria casa. usage_unit vazio significa que a
-- quantidade está na unidade base/origem; preenchido, o app converte na conta.""",
1)

migration = """-- Delícias da Vovó — produto fabricado como componente de outra ficha
-- Rode uma vez no Supabase > SQL Editor.

alter table public.recipe_items
  add column if not exists component_product_id uuid references public.products (id) on delete restrict;

alter table public.recipe_items
  alter column supply_id drop not null;

alter table public.recipe_items
  drop constraint if exists recipe_items_source_check;

alter table public.recipe_items
  add constraint recipe_items_source_check check (
    (supply_id is not null and component_product_id is null)
    or (supply_id is null and component_product_id is not null)
  );

create index if not exists recipe_items_component_product_idx
  on public.recipe_items (component_product_id);
"""

if text == original:
    raise SystemExit('index unchanged')
if schema == original_schema:
    raise SystemExit('schema unchanged')

index_path.write_text(text, encoding='utf-8')
schema_path.write_text(schema, encoding='utf-8')
migration_path.parent.mkdir(parents=True, exist_ok=True)
migration_path.write_text(migration, encoding='utf-8')
print('partial recipe modal + manufactured product components applied')
