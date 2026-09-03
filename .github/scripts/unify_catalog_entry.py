from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Version marker
s, n = re.subn(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-03-cadastro-unificado-1" />', s, count=1)
if n != 1:
    raise SystemExit('version marker not found')

marker = """      // ==========================================\n      // PRODUCT CATALOG VIEW\n      // ==========================================\n"""
if marker not in s:
    raise SystemExit('product catalog marker not found')

unified = r'''      // ==========================================
      // CADASTRO GERAL
      // Um único ponto de entrada para fabricação, insumo e revenda.
      // O seletor muda os campos do cadastro novo; ele não converte registros
      // antigos automaticamente, porque isso pode quebrar ficha e histórico.
      // ==========================================
      const UnifiedCatalogEntry = ({
        products,
        supplies,
        separatedProducts,
        onAddProduct,
        onAddSupply,
        onAddSeparatedProduct
      }) => {
        const [tipo, setTipo] = useState('fabricacao');
        const [salvando, setSalvando] = useState(false);
        const BLANK = {
          name: '', responsible: '', productCategory: 'salgado', showcaseEnabled: true,
          shelfLifeDays: 2, price: '', priceUnit: 'un',
          supplyUnit: 'g', supplyClass: 'insumo', resaleCategory: 'revenda'
        };
        const [draft, setDraft] = useState(BLANK);

        const setField = (field, value) => setDraft((d) => ({ ...d, [field]: value }));
        const tipoInfo = {
          fabricacao: { label: 'Fabricação', icon: Icons.ChefHat || Icons.Package, help: 'Produto feito pela casa · pode ter ficha técnica e CMV de produção.' },
          insumo: { label: 'Insumo', icon: Icons.Package, help: 'Matéria-prima, embalagem ou item de limpeza que a casa compra.' },
          revenda: { label: 'Revenda', icon: Icons.ShoppingCart, help: 'Item comprado pronto para vender, como bebidas e bomboniere.' }
        };

        const nomes = [
          ...products.map((x) => ({ value: `fabricacao:${x.id}`, label: x.name, hint: 'Fabricação' })),
          ...supplies.map((x) => ({ value: `insumo:${x.id}`, label: x.name, hint: 'Insumo' })),
          ...separatedProducts.map((x) => ({ value: `revenda:${x.id}`, label: x.productName || x.name, hint: 'Revenda' }))
        ];

        const jaExiste = () => {
          const nome = normalizeName(draft.name);
          if (!nome) return false;
          if (tipo === 'fabricacao') return products.some((x) => normalizeName(x.name) === nome);
          if (tipo === 'insumo') return supplies.some((x) => normalizeName(x.name) === nome);
          return separatedProducts.some((x) => normalizeName(x.productName || x.name) === nome);
        };

        const salvar = async (e) => {
          e.preventDefault();
          const name = String(draft.name || '').trim();
          if (!name || salvando) return;
          if (jaExiste()) {
            window.alert(`“${name}” já existe como ${tipoInfo[tipo].label.toLowerCase()}. Use a tabela abaixo para editar.`);
            return;
          }

          setSalvando(true);
          try {
            if (tipo === 'fabricacao') {
              await onAddProduct({
                name,
                responsible: cleanResponsible(draft.responsible),
                category: draft.productCategory,
                showcaseEnabled: draft.showcaseEnabled !== false,
                shelfLifeDays: Math.max(1, Number(draft.shelfLifeDays) || 1),
                price: Math.max(0, Number(draft.price) || 0),
                priceUnit: draft.priceUnit === 'kg' ? 'kg' : 'un',
                defaultUnit: 'un',
                minReplenishmentQty: 5
              });
            } else if (tipo === 'insumo') {
              await onAddSupply({
                name,
                unit: draft.supplyUnit || 'g',
                supplyClass: draft.supplyClass || 'insumo'
              });
            } else {
              await onAddSeparatedProduct({
                productName: name,
                category: draft.resaleCategory || 'revenda',
                currentQty: 0,
                unitOfMeasure: draft.priceUnit || 'un',
                minQty: 0,
                price: Math.max(0, Number(draft.price) || 0),
                priceUnit: draft.priceUnit || 'un'
              });
            }
            setDraft((d) => ({ ...BLANK, priceUnit: d.priceUnit, supplyUnit: d.supplyUnit, supplyClass: d.supplyClass, productCategory: d.productCategory, resaleCategory: d.resaleCategory }));
          } finally {
            setSalvando(false);
          }
        };

        return (
          <div className="card p-6 sm:p-7">
            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
              <div>
                <div className="t-overline flex items-center gap-1.5 mb-2">
                  <Icons.Plus className="w-3.5 h-3.5" />
                  Cadastro geral
                </div>
                <h2 className="t-title">O que você quer cadastrar?</h2>
                <p className="t-body mt-1.5">Produto de fabricação, insumo e revenda entram pelo mesmo formulário.</p>
              </div>
              <div className="segmented w-full lg:w-auto lg:inline-flex shrink-0">
                {['fabricacao', 'insumo', 'revenda'].map((t) => (
                  <button
                    key={t}
                    type="button"
                    data-active={tipo === t}
                    onClick={() => setTipo(t)}
                    className="flex-1 lg:flex-none h-9 px-4"
                  >
                    {tipoInfo[t].label}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 px-3 py-2 rounded-xl bg-black/[0.035] t-micro">
              <strong>{tipoInfo[tipo].label}</strong> · {tipoInfo[tipo].help}
              <span className="block mt-0.5">Para trocar o cadastro, clique em outro tipo acima. O nome digitado continua no campo.</span>
            </div>

            <form onSubmit={salvar} className="mt-5 pt-5 border-t hairline">
              <div className="grid grid-cols-12 gap-2 sm:gap-3 items-end">
                <div className="col-span-12 md:col-span-4">
                  <label className="t-caption block mb-1">Nome</label>
                  <PickerField
                    value={draft.name}
                    options={nomes}
                    onType={(v) => setField('name', v)}
                    onPick={(opt) => setField('name', opt.label)}
                    placeholder={tipo === 'fabricacao' ? 'Ex: Chipa' : tipo === 'insumo' ? 'Ex: Farinha de trigo' : 'Ex: Coca-Cola 350 ml'}
                    emptyLabel="Nome novo — será cadastrado"
                    className="field field-md font-semibold"
                  />
                </div>

                {tipo === 'fabricacao' && (
                  <>
                    <div className="col-span-6 md:col-span-2">
                      <label className="t-caption block mb-1">Responsável</label>
                      <input value={draft.responsible} onChange={(e) => setField('responsible', e.target.value)} placeholder="Quem produz" className="field field-md" />
                    </div>
                    <div className="col-span-6 md:col-span-2">
                      <label className="t-caption block mb-1">Categoria</label>
                      <PickerField value={draft.productCategory} options={PRODUCT_CATEGORIES} onPick={(opt) => setField('productCategory', opt.value)} className="field field-md" />
                    </div>
                    <div className="col-span-4 md:col-span-1">
                      <label className="t-caption block mb-1">Validade</label>
                      <input type="number" min="1" value={draft.shelfLifeDays} onChange={(e) => setField('shelfLifeDays', e.target.value)} className="field field-md text-center tnum" />
                    </div>
                    <div className="col-span-4 md:col-span-1">
                      <label className="t-caption block mb-1">Preço</label>
                      <input type="number" min="0" step="0.01" value={draft.price} onChange={(e) => setField('price', e.target.value)} placeholder="0,00" className="field field-md text-right tnum no-spin" />
                    </div>
                    <div className="col-span-4 md:col-span-1">
                      <label className="t-caption block mb-1">Vende por</label>
                      <PickerField value={draft.priceUnit} options={[{value:'un',label:'Unidade'},{value:'kg',label:'Kg'}]} onPick={(opt) => setField('priceUnit', opt.value)} className="field field-md" />
                    </div>
                    <div className="col-span-6 md:col-span-1">
                      <label className="t-caption block mb-1">Vitrine</label>
                      <label className="field field-md flex items-center gap-2 cursor-pointer">
                        <input type="checkbox" checked={draft.showcaseEnabled !== false} onChange={(e) => setField('showcaseEnabled', e.target.checked)} className="w-4 h-4" />
                        <span className="t-callout font-semibold">{draft.showcaseEnabled !== false ? 'Sim' : 'Não'}</span>
                      </label>
                    </div>
                  </>
                )}

                {tipo === 'insumo' && (
                  <>
                    <div className="col-span-6 md:col-span-2">
                      <label className="t-caption block mb-1">Unidade base</label>
                      <PickerField value={draft.supplyUnit} options={SUPPLY_UNITS.map((u) => ({value:u,label:u}))} onPick={(opt) => setField('supplyUnit', opt.value)} className="field field-md" />
                    </div>
                    <div className="col-span-6 md:col-span-3">
                      <label className="t-caption block mb-1">Classe</label>
                      <PickerField value={draft.supplyClass} options={SUPPLY_CLASSES} onPick={(opt) => setField('supplyClass', opt.value)} className="field field-md" />
                    </div>
                    <div className="col-span-12 md:col-span-3">
                      <p className="t-micro pb-2">Depois do cadastro, fornecedor, quantidade e valor da compra são lançados na tabela de Insumos.</p>
                    </div>
                  </>
                )}

                {tipo === 'revenda' && (
                  <>
                    <div className="col-span-6 md:col-span-2">
                      <label className="t-caption block mb-1">Categoria</label>
                      <PickerField value={draft.resaleCategory} options={[{value:'revenda',label:'Revenda'},{value:'cafeteria',label:'Cafeteria'},{value:'encomenda',label:'Encomenda'}]} onPick={(opt) => setField('resaleCategory', opt.value)} className="field field-md" />
                    </div>
                    <div className="col-span-3 md:col-span-2">
                      <label className="t-caption block mb-1">Preço</label>
                      <input type="number" min="0" step="0.01" value={draft.price} onChange={(e) => setField('price', e.target.value)} placeholder="0,00" className="field field-md text-right tnum no-spin" />
                    </div>
                    <div className="col-span-3 md:col-span-2">
                      <label className="t-caption block mb-1">Vende por</label>
                      <PickerField value={draft.priceUnit} options={[{value:'un',label:'Unidade'},{value:'kg',label:'Kg'},{value:'g',label:'g'}]} onPick={(opt) => setField('priceUnit', opt.value)} className="field field-md" />
                    </div>
                    <div className="col-span-12 md:col-span-2">
                      <p className="t-micro pb-2">A compra e o estoque são lançados depois na tabela de Revenda.</p>
                    </div>
                  </>
                )}

                <div className="col-span-12 md:col-span-2 md:col-start-11">
                  <button type="submit" disabled={salvando || !String(draft.name || '').trim()} className="btn btn-primary btn-md w-full disabled:opacity-45">
                    <Icons.Plus className="w-4 h-4" />
                    {salvando ? 'Salvando…' : `Cadastrar ${tipoInfo[tipo].label.toLowerCase()}`}
                  </button>
                </div>
              </div>
            </form>
          </div>
        );
      };

'''
s = s.replace(marker, unified + marker, 1)

# ProductCatalogView receives the three catalogs and three creation handlers.
old_sig = "const ProductCatalogView = ({ products, onAddProduct, onUpdateProduct, onDeleteProduct }) => {"
new_sig = "const ProductCatalogView = ({ products, supplies, separatedProducts, onAddProduct, onAddSupply, onAddSeparatedProduct, onUpdateProduct, onDeleteProduct }) => {"
if old_sig not in s:
    raise SystemExit('ProductCatalogView signature not found')
s = s.replace(old_sig, new_sig, 1)

# Replace the old product-only entry card with the unified entry card, keeping the catalog table below.
start = s.index(new_sig)
end = s.index("      // ==========================================\n      // SUPPLIES", start) if "      // ==========================================\n      // SUPPLIES" in s[start:] else s.index("      // ==========================================\n      // A FICHA", start)
seg = s[start:end]
ret = '<div className="space-y-5">'
first = seg.index('<div className="card p-6 sm:p-7">', seg.index(ret))
second_marker = '<div className="card p-5 sm:p-6 space-y-1">'
second = seg.index(second_marker, first)
replacement = '''<UnifiedCatalogEntry
              products={products}
              supplies={supplies}
              separatedProducts={separatedProducts}
              onAddProduct={onAddProduct}
              onAddSupply={onAddSupply}
              onAddSeparatedProduct={onAddSeparatedProduct}
            />

            '''
seg = seg[:first] + replacement + seg[second:]
s = s[:start] + seg + s[end:]

# In the Insumos panel, remove the second creation form so the app has one point of entry.
ins_marker = """            {painel === 'insumos' && (\n              <div className=\"space-y-5\">\n                <div className=\"card p-6 sm:p-7\">"""
if ins_marker not in s:
    raise SystemExit('insumos creation card marker not found')
ins_start = s.index(ins_marker)
first_card = s.index('<div className="card p-6 sm:p-7">', ins_start)
second_card = s.index('<div className="card p-5 sm:p-6">', first_card)
notice = '''<div className="card-quiet px-4 py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <div className="t-callout font-bold text-[#1d1d1f]">Cadastros novos ficam em Produtos → Cadastro geral</div>
                    <p className="t-micro mt-0.5">Aqui você lança compras, corrige preço de insumo e acompanha o histórico.</p>
                  </div>
                  <span className="pill tone-quiet">Fabricação · Insumo · Revenda</span>
                </div>

                '''
s = s[:first_card] + notice + s[second_card:]

# Revenda creation must persist its sale unit too.
old_resale = """              min_qty: prod.minQty || 0,\n              price: prod.price\n            }).select());"""
new_resale = """              min_qty: prod.minQty || 0,\n              price: prod.price,\n              price_unit: prod.priceUnit || 'un'\n            }).select());"""
if old_resale not in s:
    raise SystemExit('resale insert marker not found')
s = s.replace(old_resale, new_resale, 1)

# Wire the unified form to App handlers/data.
old_app = """                <ProductCatalogView\n                  products={products}\n                  onAddProduct={handleAddProduct}\n                  onUpdateProduct={handleUpdateProduct}\n                  onDeleteProduct={handleDeleteProduct}\n                />"""
new_app = """                <ProductCatalogView\n                  products={products}\n                  supplies={supplies}\n                  separatedProducts={separatedProducts}\n                  onAddProduct={handleAddProduct}\n                  onAddSupply={handleAddSupply}\n                  onAddSeparatedProduct={handleAddSeparatedProduct}\n                  onUpdateProduct={handleUpdateProduct}\n                  onDeleteProduct={handleDeleteProduct}\n                />"""
if old_app not in s:
    raise SystemExit('ProductCatalogView App call not found')
s = s.replace(old_app, new_app, 1)

p.write_text(s, encoding='utf-8')
print('ok')
