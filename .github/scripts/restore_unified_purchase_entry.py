from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Version
s, n = re.subn(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-03-entrada-unificada-compras-1" />', s, count=1)
if n != 1:
    raise SystemExit('version marker not found')

# Navigation: the operational entry lives in the purchase/ficha screen again.
s = s.replace("{ id: 'produtos', label: 'Cadastros', fullLabel: 'Cadastro geral', icon: Icons.Package }", "{ id: 'produtos', label: 'Produtos', fullLabel: 'Produtos de fabricação', icon: Icons.Package }", 1)
s = s.replace("{ id: 'insumos', label: 'Insumos', fullLabel: 'Insumos & Fichas', icon: Icons.Layers }", "{ id: 'insumos', label: 'Entradas', fullLabel: 'Entradas, compras e fichas', icon: Icons.Layers }", 1)

# Remove the duplicate catalog-only entry from Products. Product table remains.
unified_render = '''            <UnifiedCatalogEntry
              products={products}
              supplies={supplies}
              separatedProducts={separatedProducts}
              currentUnit={currentUnit}
              onAddProduct={onAddProduct}
              onAddSupply={onAddSupply}
              onAddSeparatedProduct={onAddSeparatedProduct}
            />

'''
if unified_render not in s:
    raise SystemExit('duplicate unified entry render not found')
s = s.replace(unified_render, '''            <div className="card-quiet px-4 py-3">
              <div className="t-callout font-bold text-[#1d1d1f]">Cadastro e compras ficam em Entradas</div>
              <p className="t-micro mt-0.5">Esta tabela continua sendo o cadastro mestre dos produtos de fabricação.</p>
            </div>

''', 1)

# Creation handlers must return the created row so a new resale item can receive
# its purchase in the same submit.
old_sep = '''        const handleAddSeparatedProduct = (prod) => {
          write('Cadastrar item fora da vitrine', async () => {
            const linhas = await run('separated_products', sb.from('separated_products').insert({
              unit_code: currentUnit,
              name: prod.productName,
              category: prod.category,
              current_qty: prod.currentQty,
              unit_of_measure: prod.unitOfMeasure || 'un',
              min_qty: prod.minQty || 0,
              price: prod.price,
              price_unit: prod.priceUnit || 'un'
            }).select());
            setSeparatedProducts((prev) => [...prev, fromSeparated(linhas[0])]);
          });
        };
'''
new_sep = '''        const handleAddSeparatedProduct = (prod) => {
          return write('Cadastrar item fora da vitrine', async () => {
            const linhas = await run('separated_products', sb.from('separated_products').insert({
              unit_code: currentUnit,
              name: prod.productName,
              category: prod.category,
              current_qty: prod.currentQty,
              unit_of_measure: prod.unitOfMeasure || 'un',
              min_qty: prod.minQty || 0,
              price: prod.price,
              price_unit: prod.priceUnit || 'un'
            }).select());
            const novo = fromSeparated(linhas[0]);
            setSeparatedProducts((prev) => [...prev, novo]);
            return novo;
          });
        };
'''
if old_sep not in s:
    raise SystemExit('handleAddSeparatedProduct marker not found')
s = s.replace(old_sep, new_sep, 1)

old_prod_head = """        const handleAddProduct = (prod) => {
          write('Cadastrar produto', async () => {"""
new_prod_head = """        const handleAddProduct = (prod) => {
          return write('Cadastrar produto', async () => {"""
if old_prod_head not in s:
    raise SystemExit('handleAddProduct head not found')
s = s.replace(old_prod_head, new_prod_head, 1)
old_prod_tail = '''            if (error) throw traduzirErroProduto(error);
            setProducts((prev) => [...prev, fromProduct(data[0])].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')));
          });
        };

        const handleUpdateProduct'''
new_prod_tail = '''            if (error) throw traduzirErroProduto(error);
            const novo = fromProduct(data[0]);
            setProducts((prev) => [...prev, novo].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')));
            return novo;
          });
        };

        const handleUpdateProduct'''
if old_prod_tail not in s:
    raise SystemExit('handleAddProduct tail not found')
s = s.replace(old_prod_tail, new_prod_tail, 1)

# Revenda master edits from the unified table include name/category as well.
old_update_sep = '''            run('separated_products', sb.from('separated_products').update({
              price: Number(updated.price) || 0,
              price_unit: updated.priceUnit || 'un',
              cost: Number(updated.cost) || 0
            }).eq('id', updated.id))'''
new_update_sep = '''            run('separated_products', sb.from('separated_products').update({
              name: String(updated.productName || '').trim() || undefined,
              category: updated.category || 'revenda',
              unit_of_measure: updated.unitOfMeasure || updated.priceUnit || 'un',
              price: Number(updated.price) || 0,
              price_unit: updated.priceUnit || 'un',
              cost: Number(updated.cost) || 0
            }).eq('id', updated.id))'''
if old_update_sep not in s:
    raise SystemExit('handleUpdateSeparatedProduct body not found')
s = s.replace(old_update_sep, new_update_sep, 1)

# Safe type conversion. Insumo/revenda are soft-deactivated so historical
# purchases stay in the database. Production is only converted when it has no
# operational links; otherwise the UI explains what must be resolved first.
insert_marker = """        if (!isSupabaseConfigured) return <SetupScreen />;"""
if insert_marker not in s:
    raise SystemExit('App conversion insertion marker not found')
conversion = r'''        const handleChangeCatalogType = (item, novoTipo) => {
          const tipoAtual = item?.tipo;
          const id = item?.id;
          const nome = String(item?.name || item?.source?.name || item?.source?.productName || '').trim();
          if (!id || !nome || !novoTipo || novoTipo === tipoAtual) return;

          const rotulo = { producao: 'Produção', insumo: 'Insumo', revenda: 'Revenda' };
          const ok = window.confirm(`Alterar “${nome}” de ${rotulo[tipoAtual]} para ${rotulo[novoTipo]}?`);
          if (!ok) return;

          return write('Alterar tipo do cadastro', async () => {
            const unidadeInsumo = (u) => {
              const x = String(u || '').toLowerCase();
              if (x === 'kg' || x === 'g') return 'g';
              if (x === 'l' || x === 'ml') return 'ml';
              return 'un';
            };

            const garantirInsumo = async (unidade = 'g') => {
              let { data, error } = await sb.from('supplies').select('*').eq('name', nome).limit(1);
              if (error) throw error;
              let row = data && data[0];
              if (row) {
                const resp = await sb.from('supplies').update({ is_active: true }).eq('id', row.id).select();
                if (resp.error) throw resp.error;
                row = resp.data && resp.data[0];
              } else {
                const resp = await sb.from('supplies').insert({
                  name: nome,
                  unit: unidadeInsumo(unidade),
                  supply_class: 'insumo',
                  is_active: true
                }).select();
                if (resp.error) throw resp.error;
                row = resp.data && resp.data[0];
              }
              const convertido = fromSupply(row);
              setSupplies((prev) => [
                ...prev.filter((x) => x.id !== convertido.id && normalizeName(x.name) !== normalizeName(nome)),
                convertido
              ].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')));
              return convertido;
            };

            const garantirRevenda = async (origem = null) => {
              let { data, error } = await sb.from('separated_products')
                .select('*').eq('unit_code', currentUnit).eq('name', nome).limit(1);
              if (error) throw error;
              let row = data && data[0];
              if (row) {
                const resp = await sb.from('separated_products').update({ is_active: true }).eq('id', row.id).select();
                if (resp.error) throw resp.error;
                row = resp.data && resp.data[0];
              } else {
                const pu = origem?.priceUnit || origem?.unit || 'un';
                const resp = await sb.from('separated_products').insert({
                  unit_code: currentUnit,
                  name: nome,
                  category: 'revenda',
                  current_qty: 0,
                  unit_of_measure: pu,
                  min_qty: 0,
                  price: Number(origem?.price) || 0,
                  price_unit: pu,
                  is_active: true
                }).select();
                if (resp.error) throw resp.error;
                row = resp.data && resp.data[0];
              }
              const convertido = fromSeparated(row);
              setSeparatedProducts((prev) => [
                ...prev.filter((x) => x.id !== convertido.id && !(x.unit === currentUnit && normalizeName(x.productName) === normalizeName(nome))),
                convertido
              ].sort((a, b) => a.productName.localeCompare(b.productName, 'pt-BR')));
              return convertido;
            };

            const garantirProduto = async (origem = null) => {
              const local = products.find((p) => normalizeName(p.name) === normalizeName(nome));
              if (local) return local;
              const { data, error } = await sb.from('products').insert({
                name: nome,
                responsible: '',
                category: 'outro',
                is_active: false,
                default_unit: 'un',
                min_replenishment_qty: 5,
                shelf_life_days: 2,
                price: Number(origem?.price) || 0,
                price_unit: origem?.priceUnit === 'kg' ? 'kg' : 'un'
              }).select();
              if (error) throw traduzirErroProduto(error);
              const convertido = fromProduct(data[0]);
              setProducts((prev) => [...prev, convertido].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')));
              return convertido;
            };

            const copiarComprasInsumoParaRevenda = async (supplyId, revendaId, unidade) => {
              if (resalePurchases.some((c) => c.separatedProductId === revendaId)) return;
              const origem = supplyPurchases.filter((c) => c.supplyId === supplyId);
              if (!origem.length) return;
              const { data, error } = await sb.from('resale_purchases').insert(origem.map((c) => ({
                separated_product_id: revendaId,
                supplier: c.supplier || '',
                purchase_date: c.purchaseDate || null,
                qty: Number(c.qty) || 0,
                purchase_unit: unidade || 'un',
                cost: Number(c.cost) || 0
              }))).select();
              if (error) throw error;
              setResalePurchases((prev) => [...prev, ...(data || []).map(fromResalePurchase)]);
            };

            const copiarComprasRevendaParaInsumo = async (revendaId, supplyId, unidadeBase) => {
              if (supplyPurchases.some((c) => c.supplyId === supplyId)) return;
              const origem = resalePurchases.filter((c) => c.separatedProductId === revendaId);
              if (!origem.length) return;
              const qtdConvertida = (c) => {
                const q = Number(c.qty) || 0;
                const u = String(c.purchaseUnit || 'un').toLowerCase();
                if (unidadeBase === 'g' && u === 'kg') return q * 1000;
                if (unidadeBase === 'ml' && u === 'l') return q * 1000;
                return q;
              };
              const { data, error } = await sb.from('supply_purchases').insert(origem.map((c) => ({
                supply_id: supplyId,
                supplier: c.supplier || '',
                purchase_date: c.purchaseDate || null,
                qty: qtdConvertida(c),
                cost: Number(c.cost) || 0
              }))).select();
              if (error) throw error;
              setSupplyPurchases((prev) => [...prev, ...(data || []).map(fromSupplyPurchase)]);
            };

            if (tipoAtual === 'insumo') {
              const origem = supplies.find((x) => x.id === id) || item.source;
              const emFicha = recipeItems.some((ri) => ri.supplyId === id);
              if (emFicha) throw new Error(`“${nome}” está sendo usado em ficha técnica. Tire-o das fichas antes de mudar o tipo.`);

              if (novoTipo === 'revenda') {
                const alvo = await garantirRevenda({ unit: origem?.unit || 'un' });
                await copiarComprasInsumoParaRevenda(id, alvo.id, origem?.unit || 'un');
              } else {
                await garantirProduto({ priceUnit: origem?.unit === 'g' ? 'kg' : 'un' });
              }

              const { error } = await sb.from('supplies').update({ is_active: false }).eq('id', id);
              if (error) throw error;
              setSupplies((prev) => prev.filter((x) => x.id !== id));
              return;
            }

            if (tipoAtual === 'revenda') {
              const origem = separatedProducts.find((x) => x.id === id) || item.source;
              if (novoTipo === 'producao' && Number(origem?.currentQty) > 0) {
                throw new Error(`“${nome}” ainda tem ${origem.currentQty} em estoque. Zere ou dê baixa no estoque antes de mudar para Produção.`);
              }

              if (novoTipo === 'insumo') {
                const alvo = await garantirInsumo(origem?.priceUnit || origem?.unitOfMeasure || 'un');
                await copiarComprasRevendaParaInsumo(id, alvo.id, alvo.unit);
              } else {
                await garantirProduto(origem);
              }

              const { error } = await sb.from('separated_products').update({ is_active: false }).eq('id', id);
              if (error) throw error;
              setSeparatedProducts((prev) => prev.filter((x) => x.id !== id));
              return;
            }

            // Produção: só sai desta tabela quando não existe nada ligado a ela.
            const temLigacao =
              slotItems.some((x) => x.productId === id) ||
              standardPlans.some((x) => x.productId === id) ||
              recipes.some((x) => x.productId === id) ||
              recipeItems.some((x) => x.componentProductId === id) ||
              saleRecords.some((x) => x.productId === id) ||
              lossRecords.some((x) => x.productId === id) ||
              productionRecords.some((x) => x.productId === id);
            if (temLigacao) {
              throw new Error(`“${nome}” já tem ficha, vitrine ou histórico de produção/venda. Para não perder vínculos, ele não pode trocar de Produção automaticamente.`);
            }

            const origem = products.find((x) => x.id === id) || item.source;
            if (novoTipo === 'insumo') await garantirInsumo(origem?.priceUnit === 'kg' ? 'g' : 'un');
            else await garantirRevenda(origem);

            const { error } = await sb.from('products').delete().eq('id', id);
            if (error) throw error;
            setProducts((prev) => prev.filter((x) => x.id !== id));
          });
        };

'''
s = s.replace(insert_marker, conversion + insert_marker, 1)

# SuppliesRecipesView gets product handlers + type conversion callback.
old_sig = '''        fornecedores,
        onAddSupply,
        onUpdateSupply,'''
new_sig = '''        fornecedores,
        onAddProduct,
        onUpdateProduct,
        onAddSupply,
        onUpdateSupply,'''
if old_sig not in s:
    raise SystemExit('SuppliesRecipesView product props marker not found')
s = s.replace(old_sig, new_sig, 1)
old_sig2 = '''        onDeleteResalePurchase
      }) => {
        const [painel, setPainel] = useState('insumos');'''
new_sig2 = '''        onDeleteResalePurchase,
        onChangeCatalogType
      }) => {
        const [painel, setPainel] = useState('entradas');'''
if old_sig2 not in s:
    raise SystemExit('SuppliesRecipesView tail props marker not found')
s = s.replace(old_sig2, new_sig2, 1)

# Replace the old insumo-only draft logic with the unified entry logic.
logic_start = s.index("        const BLANK_SUPPLY =", s.index("const SuppliesRecipesView"))
logic_end = s.index("        // Produtos de fabricação, com a ficha e o custo já resolvidos", logic_start)
new_logic = r'''        const TIPOS_ENTRADA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'producao', label: 'Produção' }
        ];
        const BLANK_ENTRY = {
          type: 'insumo', name: '', unit: 'g', supplyClass: 'insumo',
          supplier: '', purchaseDate: getTodayDateString(), qty: '', cost: '', purchaseUnit: 'un',
          responsible: '', productCategory: 'salgado', shelfLifeDays: 2,
          price: '', priceUnit: 'un', resaleCategory: 'revenda'
        };
        const [draft, setDraft] = useState(BLANK_ENTRY);
        const nomeRef = useRef(null);

        const comprasDoInsumo = (id) => supplyPurchases.filter((c) => c.supplyId === id);
        const comprasDaRevenda = (id) => resalePurchases.filter((c) => c.separatedProductId === id);
        const revendaDaUnidade = separatedProducts.filter((p) => p.unit === currentUnit);

        const cadastroExistente = (() => {
          const nome = normalizeName(String(draft.name || '').trim());
          if (!nome) return null;
          if (draft.type === 'producao') return products.find((x) => normalizeName(x.name) === nome) || null;
          if (draft.type === 'revenda') return revendaDaUnidade.find((x) => normalizeName(x.productName) === nome) || null;
          return supplies.find((x) => normalizeName(x.name) === nome) || null;
        })();

        const compraExistente = cadastroExistente
          ? draft.type === 'revenda'
            ? ultimaCompra(comprasDaRevenda(cadastroExistente.id))
            : draft.type === 'insumo'
              ? ultimaCompra(comprasDoInsumo(cadastroExistente.id))
              : null
          : null;

        const opcoesCadastro = useMemo(() => [
          ...supplies.map((x) => ({ value: `insumo:${x.id}`, label: x.name, hint: `Insumo · ${x.unit}` })),
          ...revendaDaUnidade.map((x) => ({ value: `revenda:${x.id}`, label: x.productName, hint: `Revenda · ${x.priceUnit || 'un'}` })),
          ...products.map((x) => ({ value: `producao:${x.id}`, label: x.name, hint: `Produção · ${x.priceUnit || 'un'}` }))
        ].sort((a, b) => a.label.localeCompare(b.label, 'pt-BR')), [supplies, revendaDaUnidade, products]);

        const selecionarCadastro = (opt) => {
          const [tipo, id] = String(opt?.value || '').split(':');
          if (tipo === 'insumo') {
            const x = supplies.find((i) => String(i.id) === id);
            if (x) setDraft((d) => ({ ...d, type: 'insumo', name: x.name, unit: x.unit || 'g', supplyClass: x.supplyClass || 'insumo' }));
            return;
          }
          if (tipo === 'revenda') {
            const x = revendaDaUnidade.find((i) => String(i.id) === id);
            if (x) setDraft((d) => ({ ...d, type: 'revenda', name: x.productName, price: x.price || '', priceUnit: x.priceUnit || 'un', purchaseUnit: x.priceUnit || 'un', resaleCategory: x.category || 'revenda' }));
            return;
          }
          if (tipo === 'producao') {
            const x = products.find((i) => String(i.id) === id);
            if (x) setDraft((d) => ({ ...d, type: 'producao', name: x.name, responsible: x.responsible || '', productCategory: x.category || 'salgado', shelfLifeDays: x.shelfLifeDays || 2, price: x.price || '', priceUnit: x.priceUnit || 'un' }));
          }
        };

        const cadastrar = async (e) => {
          e.preventDefault();
          const nome = String(draft.name || '').trim();
          if (!nome) return;

          if (draft.type === 'producao') {
            const dados = {
              name: nome,
              responsible: cleanResponsible(draft.responsible),
              category: draft.productCategory || 'outro',
              showcaseEnabled: cadastroExistente ? cadastroExistente.showcaseEnabled !== false : false,
              shelfLifeDays: Math.max(1, Number(draft.shelfLifeDays) || 2),
              price: Math.max(0, Number(draft.price) || 0),
              priceUnit: draft.priceUnit === 'kg' ? 'kg' : 'un',
              defaultUnit: 'un',
              minReplenishmentQty: cadastroExistente?.minReplenishmentQty || 5
            };
            if (cadastroExistente) onUpdateProduct({ ...cadastroExistente, ...dados });
            else await onAddProduct(dados);
            setDraft((d) => ({ ...BLANK_ENTRY, type: d.type, productCategory: d.productCategory, priceUnit: d.priceUnit, purchaseDate: getTodayDateString() }));
            setTimeout(() => nomeRef.current && nomeRef.current.focus(), 50);
            return;
          }

          const qty = Number(draft.qty) || 0;
          const cost = Number(draft.cost) || 0;
          if ((qty > 0 || cost > 0) && !(qty > 0 && cost > 0)) {
            window.alert('Para registrar a compra, preencha quantidade e valor pago.');
            return;
          }

          if (draft.type === 'insumo') {
            let alvo = cadastroExistente;
            if (!alvo) alvo = await onAddSupply({ name: nome, unit: draft.unit || 'g', supplyClass: draft.supplyClass || 'insumo' });
            if (alvo?.id && qty > 0 && cost > 0) {
              await onAddSupplyPurchase(alvo.id, {
                supplier: String(draft.supplier || '').trim(),
                purchaseDate: draft.purchaseDate || getTodayDateString(),
                qty,
                cost
              });
            }
          } else {
            let alvo = cadastroExistente;
            if (!alvo) {
              alvo = await onAddSeparatedProduct({
                productName: nome,
                category: draft.resaleCategory || 'revenda',
                currentQty: 0,
                unitOfMeasure: draft.priceUnit || 'un',
                minQty: 0,
                price: Math.max(0, Number(draft.price) || 0),
                priceUnit: draft.priceUnit || 'un'
              });
            } else if (Number(draft.price) !== Number(alvo.price) || draft.priceUnit !== alvo.priceUnit) {
              onUpdateSeparatedProduct({ ...alvo, price: Math.max(0, Number(draft.price) || 0), priceUnit: draft.priceUnit || 'un' });
            }
            if (alvo?.id && qty > 0 && cost > 0) {
              await onAddResalePurchase(alvo.id, {
                supplier: String(draft.supplier || '').trim(),
                purchaseDate: draft.purchaseDate || getTodayDateString(),
                qty,
                purchaseUnit: draft.purchaseUnit || draft.priceUnit || 'un',
                cost
              });
            }
          }

          setDraft((d) => ({
            ...BLANK_ENTRY,
            type: d.type,
            unit: d.unit,
            supplyClass: d.supplyClass,
            priceUnit: d.priceUnit,
            purchaseUnit: d.purchaseUnit,
            resaleCategory: d.resaleCategory,
            purchaseDate: getTodayDateString()
          }));
          setTimeout(() => nomeRef.current && nomeRef.current.focus(), 50);
        };

'''
s = s[:logic_start] + new_logic + s[logic_end:]

# Add unified rows after the product/ficha calculation.
ficha_marker = """        const fichaAberta = produtosComFicha.find((x) => String(x.produto.id) === String(fichaProdutoId)) || null;

"""
if ficha_marker not in s:
    raise SystemExit('fichaAberta marker not found')
rows = r'''        const fichaAberta = produtosComFicha.find((x) => String(x.produto.id) === String(fichaProdutoId)) || null;

        const cadastrosUnificados = useMemo(() => {
          const producao = produtosComFicha.map(({ produto, ficha, custoUn }) => ({
            key: `producao:${produto.id}`,
            tipo: 'producao', id: produto.id, name: produto.name, source: produto,
            unidade: produto.priceUnit || 'un', compra: null, custo: custoUn,
            ficha
          }));
          const insumos = supplies.map((x) => ({
            key: `insumo:${x.id}`,
            tipo: 'insumo', id: x.id, name: x.name, source: x,
            unidade: x.unit || 'g', compra: ultimaCompra(comprasDoInsumo(x.id)),
            custo: custoUnitarioInsumo(x.id, supplyPurchases)
          }));
          const revendas = revendaDaUnidade.map((x) => ({
            key: `revenda:${x.id}`,
            tipo: 'revenda', id: x.id, name: x.productName, source: x,
            unidade: x.priceUnit || 'un', compra: ultimaCompra(comprasDaRevenda(x.id)),
            custo: custoRevenda(x, resalePurchases)
          }));
          return [...insumos, ...revendas, ...producao].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'));
        }, [produtosComFicha, supplies, supplyPurchases, revendaDaUnidade, resalePurchases]);

        const cadastrosFiltrados = cadastrosUnificados.filter((x) => {
          const bateTexto = x.name.toLowerCase().includes(busca.toLowerCase());
          const bateTipo = classeFiltro === 'todos' || x.tipo === classeFiltro;
          return bateTexto && bateTipo;
        });

'''
s = s.replace(ficha_marker, rows, 1)

# Panels / titles
s = s.replace("{ id: 'insumos', label: 'Insumos' },\n          { id: 'fichas', label: 'Fichas técnicas' },\n          { id: 'revenda', label: 'Revenda' }", "{ id: 'entradas', label: 'Entradas & compras' },\n          { id: 'fichas', label: 'Fichas técnicas' }", 1)
s = s.replace('<h2 className="t-display">Insumos &amp; fichas</h2>', '<h2 className="t-display">Entradas &amp; fichas</h2>', 1)
s = s.replace('O que a casa compra e o que entra em cada produto. É daqui que sai o CMV.', 'Cadastre produção, insumo ou revenda e já lance a compra no mesmo lugar. É daqui que sai o CMV.', 1)

# Replace the removed/insumo-only entry+table with the unified operational form/table.
block_start = s.index("            {/* ---------------- INSUMOS ---------------- */}", s.index("const SuppliesRecipesView"))
block_end = s.index("            {/* ---------------- FICHAS TÉCNICAS ---------------- */}", block_start)
new_block = r'''            {/* ---------------- ENTRADAS / COMPRAS ---------------- */}
            {painel === 'entradas' && (
              <div className="space-y-5">
                <div className="card p-6 sm:p-7">
                  <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                    <div>
                      <div className="t-overline flex items-center gap-1.5 mb-2">
                        <Icons.ShoppingCart className="w-3.5 h-3.5" />
                        Entrada principal
                      </div>
                      <h3 className="t-title">Cadastro + compra</h3>
                      <p className="t-body mt-1.5">Escolha o tipo e faça tudo na mesma entrada. Item já cadastrado vira uma nova compra.</p>
                    </div>
                    <div className="segmented w-full lg:w-auto lg:inline-flex shrink-0">
                      {TIPOS_ENTRADA.map((t) => (
                        <button
                          key={t.value}
                          type="button"
                          data-active={draft.type === t.value}
                          onClick={() => setDraft((d) => ({ ...d, type: t.value, name: '' }))}
                          className="flex-1 lg:flex-none h-9 px-4"
                        >
                          {t.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  <form onSubmit={cadastrar} className="mt-5 pt-5 border-t hairline">
                    <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end">
                      <div className="col-span-12 lg:col-span-4">
                        <label className="t-caption block mb-1">Item</label>
                        <PickerField
                          inputRef={nomeRef}
                          value={draft.name}
                          options={opcoesCadastro}
                          onType={(name) => setDraft((d) => ({ ...d, name }))}
                          onPick={selecionarCadastro}
                          placeholder="Digite ou escolha um item"
                          emptyLabel="Item novo — será cadastrado ao salvar"
                          className="field field-md font-semibold"
                        />
                      </div>

                      {draft.type === 'insumo' && (
                        <>
                          <div className="col-span-4 lg:col-span-2">
                            <label className="t-caption block mb-1">Unidade base</label>
                            {cadastroExistente ? (
                              <div className="field field-md flex items-center px-3 bg-black/[0.035] text-[#86868b]">{cadastroExistente.unit}</div>
                            ) : (
                              <PickerField value={draft.unit} options={SUPPLY_UNITS.map((u) => ({value:u,label:u}))} onPick={(opt) => setDraft((d) => ({...d,unit:opt.value}))} className="field field-md" />
                            )}
                          </div>
                          <div className="col-span-8 lg:col-span-3">
                            <label className="t-caption block mb-1">Classe</label>
                            {cadastroExistente ? (
                              <div className="field field-md flex items-center px-3 bg-black/[0.035] text-[#86868b]">{SUPPLY_CLASSES.find((c) => c.value === cadastroExistente.supplyClass)?.label || 'Insumo'}</div>
                            ) : (
                              <PickerField value={draft.supplyClass} options={SUPPLY_CLASSES} onPick={(opt) => setDraft((d) => ({...d,supplyClass:opt.value}))} className="field field-md" />
                            )}
                          </div>
                        </>
                      )}

                      {draft.type === 'revenda' && (
                        <>
                          <div className="col-span-4 lg:col-span-2">
                            <label className="t-caption block mb-1">Preço venda</label>
                            <input type="number" min="0" step="0.01" value={draft.price} onChange={(e) => setDraft((d) => ({...d,price:e.target.value}))} placeholder="0,00" className="field field-md text-right tnum no-spin" />
                          </div>
                          <div className="col-span-4 lg:col-span-1">
                            <label className="t-caption block mb-1">Vende por</label>
                            <PickerField value={draft.priceUnit} options={[{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]} onPick={(opt) => setDraft((d) => ({...d,priceUnit:opt.value,purchaseUnit:opt.value}))} className="field field-md" />
                          </div>
                          <div className="col-span-4 lg:col-span-2">
                            <label className="t-caption block mb-1">Categoria</label>
                            <PickerField value={draft.resaleCategory} options={[{value:'revenda',label:'Revenda'},{value:'cafeteria',label:'Cafeteria'},{value:'encomenda',label:'Encomenda'}]} onPick={(opt) => setDraft((d) => ({...d,resaleCategory:opt.value}))} className="field field-md" />
                          </div>
                        </>
                      )}

                      {draft.type === 'producao' && (
                        <>
                          <div className="col-span-6 lg:col-span-2">
                            <label className="t-caption block mb-1">Responsável</label>
                            <input value={draft.responsible} onChange={(e) => setDraft((d) => ({...d,responsible:e.target.value}))} placeholder="Quem produz" className="field field-md" />
                          </div>
                          <div className="col-span-6 lg:col-span-2">
                            <label className="t-caption block mb-1">Categoria</label>
                            <PickerField value={draft.productCategory} options={PRODUCT_CATEGORIES} onPick={(opt) => setDraft((d) => ({...d,productCategory:opt.value}))} className="field field-md" />
                          </div>
                          <div className="col-span-4 lg:col-span-1">
                            <label className="t-caption block mb-1">Validade</label>
                            <input type="number" min="1" value={draft.shelfLifeDays} onChange={(e) => setDraft((d) => ({...d,shelfLifeDays:e.target.value}))} className="field field-md text-center tnum" />
                          </div>
                          <div className="col-span-4 lg:col-span-1">
                            <label className="t-caption block mb-1">Preço</label>
                            <input type="number" min="0" step="0.01" value={draft.price} onChange={(e) => setDraft((d) => ({...d,price:e.target.value}))} placeholder="0,00" className="field field-md text-right tnum no-spin" />
                          </div>
                          <div className="col-span-4 lg:col-span-1">
                            <label className="t-caption block mb-1">Vende por</label>
                            <PickerField value={draft.priceUnit} options={[{value:'un',label:'un'},{value:'kg',label:'kg'}]} onPick={(opt) => setDraft((d) => ({...d,priceUnit:opt.value}))} className="field field-md" />
                          </div>
                          <div className="col-span-12 lg:col-span-2">
                            <button type="submit" className="btn btn-primary btn-md w-full"><Icons.Plus className="w-4 h-4" />{cadastroExistente ? 'Salvar produto' : 'Cadastrar produto'}</button>
                          </div>
                        </>
                      )}
                    </div>

                    {draft.type !== 'producao' && (
                      <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end mt-3 pt-3 border-t hairline">
                        <div className="col-span-12 sm:col-span-4">
                          <label className="t-caption block mb-1">Fornecedor</label>
                          <PickerField
                            value={draft.supplier}
                            options={fornecedores.map((f) => ({value:f,label:f}))}
                            onType={(supplier) => setDraft((d) => ({...d,supplier}))}
                            onPick={(opt) => setDraft((d) => ({...d,supplier:opt.value}))}
                            placeholder={compraExistente?.supplier || 'Fornecedor'}
                            emptyLabel="Fornecedor novo"
                            className="field field-md"
                          />
                        </div>
                        <div className="col-span-6 sm:col-span-2">
                          <label className="t-caption block mb-1">Data</label>
                          <input type="date" value={draft.purchaseDate} onChange={(e) => setDraft((d) => ({...d,purchaseDate:e.target.value}))} className="field field-md" />
                        </div>
                        <div className="col-span-3 sm:col-span-2">
                          <label className="t-caption block mb-1">Qtd. comprada</label>
                          <input type="number" min="0" step="0.001" value={draft.qty} onChange={(e) => setDraft((d) => ({...d,qty:e.target.value}))} placeholder={compraExistente?.qty ? String(compraExistente.qty) : '0'} className="field field-md text-right tnum no-spin" />
                        </div>
                        {draft.type === 'revenda' && (
                          <div className="col-span-3 sm:col-span-1">
                            <label className="t-caption block mb-1">Un. compra</label>
                            <PickerField value={draft.purchaseUnit} options={[{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]} onPick={(opt) => setDraft((d) => ({...d,purchaseUnit:opt.value}))} className="field field-md" />
                          </div>
                        )}
                        <div className={`${draft.type === 'revenda' ? 'col-span-6 sm:col-span-1' : 'col-span-6 sm:col-span-2'}`}>
                          <label className="t-caption block mb-1">Valor pago</label>
                          <input type="number" min="0" step="0.01" value={draft.cost} onChange={(e) => setDraft((d) => ({...d,cost:e.target.value}))} placeholder={compraExistente?.cost ? String(compraExistente.cost) : '0,00'} className="field field-md text-right tnum no-spin" />
                        </div>
                        <div className="col-span-6 sm:col-span-2">
                          <button type="submit" className="btn btn-primary btn-md w-full"><Icons.Plus className="w-4 h-4" />{cadastroExistente ? 'Registrar compra' : 'Cadastrar + compra'}</button>
                        </div>
                      </div>
                    )}
                  </form>

                  {cadastroExistente && (
                    <div className="mt-3 px-3 py-2 rounded-xl bg-black/[0.035] t-micro">
                      <strong>{cadastroExistente.name || cadastroExistente.productName}</strong>
                      <span> · já cadastrado como {TIPOS_ENTRADA.find((t) => t.value === draft.type)?.label}</span>
                      {compraExistente && <span> · última compra {formatCurrencyBR(Number(compraExistente.cost) || 0)}{compraExistente.supplier ? ` · ${compraExistente.supplier}` : ''}</span>}
                    </div>
                  )}
                </div>

                <div className="card p-5 sm:p-6">
                  <div className="flex flex-col sm:flex-row sm:items-center gap-2 pb-4">
                    <div className="relative flex-1 max-w-sm">
                      <Icons.Search className="w-3.5 h-3.5 text-[#86868b] absolute left-3 top-[11px]" />
                      <input type="text" placeholder="Pesquisar cadastro…" value={busca} onChange={(e) => setBusca(e.target.value)} className="field field-sm field-search" />
                    </div>
                    <div className="w-44">
                      <PickerField value={classeFiltro} options={[{value:'todos',label:'Todos os tipos'}, ...TIPOS_ENTRADA]} onPick={(opt) => setClasseFiltro(opt.value)} className="field field-sm" />
                    </div>
                  </div>

                  <div className="rola-x">
                    <table className="w-full text-left tabela-larga">
                      <thead>
                        <tr className="t-overline-sm border-b hairline">
                          <th className="py-3 pr-3 font-bold sticky left-0 bg-white z-10">Item</th>
                          <th className="py-3 px-3 font-bold">Tipo</th>
                          <th className="py-3 px-3 font-bold">Un.</th>
                          <th className="py-3 px-3 font-bold">Fornecedor</th>
                          <th className="py-3 px-3 font-bold">Data</th>
                          <th className="py-3 px-3 text-right font-bold">Qtd comprada</th>
                          <th className="py-3 px-3 text-right font-bold">Valor pago</th>
                          <th className="py-3 px-3 text-right font-bold">Custo</th>
                          <th className="py-3 pl-3 font-bold">Detalhes</th>
                        </tr>
                      </thead>
                      <tbody>
                        {cadastrosFiltrados.length === 0 ? (
                          <tr><td colSpan={9} className="text-center py-10"><p className="t-body ink-quiet">Nenhum cadastro encontrado</p></td></tr>
                        ) : cadastrosFiltrados.map((linha) => {
                          const x = linha.source;
                          const c = linha.compra;
                          return (
                            <tr key={linha.key} className="border-t hairline hover:bg-black/[0.015] transition-colors">
                              <td className="py-2.5 pr-3 sticky left-0 bg-white z-10">
                                {linha.tipo === 'revenda' ? (
                                  <input value={x.productName} onChange={(e) => onUpdateSeparatedProduct({...x,productName:e.target.value})} className="field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48" />
                                ) : linha.tipo === 'insumo' ? (
                                  <input value={x.name} onChange={(e) => onUpdateSupply({...x,name:e.target.value})} className="field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48" />
                                ) : (
                                  <input value={x.name} onChange={(e) => onUpdateProduct({...x,name:e.target.value})} className="field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48" />
                                )}
                              </td>
                              <td className="py-2.5 px-3">
                                <div className="w-28">
                                  <PickerField value={linha.tipo} options={TIPOS_ENTRADA} onPick={(opt) => opt.value !== linha.tipo && onChangeCatalogType(linha, opt.value)} className="field h-8 pl-2.5 text-[12px] font-bold" />
                                </div>
                              </td>
                              <td className="py-2.5 px-3">
                                <div className="w-16">
                                  {linha.tipo === 'insumo' ? (
                                    <PickerField value={x.unit} options={SUPPLY_UNITS.map((u) => ({value:u,label:u}))} onPick={(opt) => onUpdateSupply({...x,unit:opt.value})} className="field h-8 pl-2.5 text-[12px]" />
                                  ) : linha.tipo === 'revenda' ? (
                                    <PickerField value={x.priceUnit || 'un'} options={[{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]} onPick={(opt) => onUpdateSeparatedProduct({...x,priceUnit:opt.value})} className="field h-8 pl-2.5 text-[12px]" />
                                  ) : (
                                    <PickerField value={x.priceUnit || 'un'} options={[{value:'un',label:'un'},{value:'kg',label:'kg'}]} onPick={(opt) => onUpdateProduct({...x,priceUnit:opt.value})} className="field h-8 pl-2.5 text-[12px]" />
                                  )}
                                </div>
                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'producao' ? <span className="t-empty">—</span> : (
                                  <div className="w-28 sm:w-36"><PickerField value={c?.supplier || ''} options={fornecedores.map((f) => ({value:f,label:f}))} onType={(v) => linha.tipo === 'insumo' ? onSetUltimaCompraInsumo(x.id,{supplier:v}) : onSetUltimaCompraRevenda(x.id,{supplier:v})} onPick={(opt) => linha.tipo === 'insumo' ? onSetUltimaCompraInsumo(x.id,{supplier:opt.value}) : onSetUltimaCompraRevenda(x.id,{supplier:opt.value})} placeholder="Fornecedor" emptyLabel="Fornecedor novo" className="field h-8 pl-2.5 text-[12px]" /></div>
                                )}
                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'producao' ? <span className="t-empty">—</span> : <input type="date" value={c?.purchaseDate || ''} onChange={(e) => linha.tipo === 'insumo' ? onSetUltimaCompraInsumo(x.id,{purchaseDate:e.target.value}) : onSetUltimaCompraRevenda(x.id,{purchaseDate:e.target.value})} className="field h-8 px-2 text-[12px] w-32 sm:w-36" />}
                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'producao' ? <span className="t-empty block text-right">—</span> : (
                                  <div className="flex items-center justify-end gap-1">
                                    <input type="number" min="0" step="0.001" value={c?.qty || ''} onChange={(e) => linha.tipo === 'insumo' ? onSetUltimaCompraInsumo(x.id,{qty:Number(e.target.value)||0}) : onSetUltimaCompraRevenda(x.id,{qty:Number(e.target.value)||0})} className="field h-8 px-2 text-[12px] text-right tnum no-spin w-20" />
                                    {linha.tipo === 'revenda' ? (
                                      <div className="w-14"><PickerField value={c?.purchaseUnit || x.priceUnit || 'un'} options={[{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]} onPick={(opt) => onSetUltimaCompraRevenda(x.id,{purchaseUnit:opt.value})} className="field h-8 pl-2 text-[11px]" /></div>
                                    ) : <span className="t-micro">{x.unit}</span>}
                                  </div>
                                )}
                              </td>
                              <td className="py-2.5 px-3">
                                {linha.tipo === 'producao' ? <span className="t-empty block text-right">—</span> : <input type="number" min="0" step="0.01" value={c?.cost || ''} onChange={(e) => linha.tipo === 'insumo' ? onSetUltimaCompraInsumo(x.id,{cost:Number(e.target.value)||0}) : onSetUltimaCompraRevenda(x.id,{cost:Number(e.target.value)||0})} className="field h-8 px-2 text-[12px] text-right font-bold tnum no-spin w-24 ml-auto block" />}
                              </td>
                              <td className="py-2.5 px-3 text-right t-callout tnum font-semibold">
                                {linha.custo > 0 ? `${formatCurrencyBR(linha.custo)}/${linha.unidade}` : '—'}
                              </td>
                              <td className="py-2.5 pl-3">
                                {linha.tipo === 'insumo' ? (
                                  <div className="w-28"><PickerField value={x.supplyClass || 'insumo'} options={SUPPLY_CLASSES} onPick={(opt) => onUpdateSupply({...x,supplyClass:opt.value})} className="field h-8 pl-2.5 text-[12px]" /></div>
                                ) : (
                                  <div className="flex items-center gap-1">
                                    <span className="t-micro">Preço</span>
                                    <input type="number" min="0" step="0.01" value={x.price || ''} onChange={(e) => linha.tipo === 'revenda' ? onUpdateSeparatedProduct({...x,price:Number(e.target.value)||0}) : onUpdateProduct({...x,price:Number(e.target.value)||0})} className="field h-8 px-2 text-[12px] text-right font-bold tnum no-spin w-20" />
                                  </div>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <p className="t-micro pt-3">O tipo pode ser corrigido na própria tabela. O sistema bloqueia a troca quando ela quebraria ficha técnica, vitrine ou histórico.</p>
                </div>
              </div>
            )}

'''
s = s[:block_start] + new_block + s[block_end:]

# App passes the extra handlers.
old_pass = '''                    fornecedores={fornecedoresUsados}
                    onAddSupply={handleAddSupply}'''
new_pass = '''                    fornecedores={fornecedoresUsados}
                    onAddProduct={handleAddProduct}
                    onUpdateProduct={handleUpdateProduct}
                    onAddSupply={handleAddSupply}'''
if old_pass not in s:
    raise SystemExit('SuppliesRecipesView pass marker 1 not found')
s = s.replace(old_pass, new_pass, 1)
old_pass2 = '''                    onUpdateResalePurchase={handleUpdateResalePurchase}
                    onDeleteResalePurchase={handleDeleteResalePurchase}
                  />'''
new_pass2 = '''                    onUpdateResalePurchase={handleUpdateResalePurchase}
                    onDeleteResalePurchase={handleDeleteResalePurchase}
                    onChangeCatalogType={handleChangeCatalogType}
                  />'''
if old_pass2 not in s:
    raise SystemExit('SuppliesRecipesView pass marker 2 not found')
s = s.replace(old_pass2, new_pass2, 1)

p.write_text(s, encoding='utf-8')
print('patched unified purchase entry')
