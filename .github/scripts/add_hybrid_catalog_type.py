from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

# Version
s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-03-tipo-insumo-revenda-1" />',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('version marker not found')

# The entry form still has two operational modes (purchase vs production), but
# the master table needs a fourth visible state: the same item is both supply
# and resale.
old_tipos = '''        const TIPOS_ENTRADA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'producao', label: 'Produção' }
        ];'''
new_tipos = '''        const TIPOS_ENTRADA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'producao', label: 'Produção' }
        ];
        const TIPOS_TABELA = [
          { value: 'insumo', label: 'Insumo' },
          { value: 'revenda', label: 'Revenda' },
          { value: 'insumo_revenda', label: 'Insumo + revenda' },
          { value: 'producao', label: 'Produção' }
        ];'''
if old_tipos not in s:
    raise SystemExit('TIPOS_ENTRADA marker not found')
s = s.replace(old_tipos, new_tipos, 1)

# We need to await this when changing a hybrid row to another type.
old_return = """          write(enabled ? 'Ativar revenda do insumo' : 'Desativar revenda do insumo', async () => {"""
new_return = """          return write(enabled ? 'Ativar revenda do insumo' : 'Desativar revenda do insumo', async () => {"""
if old_return not in s:
    raise SystemExit('handleSetSupplyResale write marker not found')
s = s.replace(old_return, new_return, 1)

old_catalog = '''        const cadastrosUnificados = useMemo(() => {
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
new_catalog = '''        const cadastrosUnificados = useMemo(() => {
          const producao = produtosComFicha.map(({ produto, ficha, custoUn }) => ({
            key: `producao:${produto.id}`,
            tipo: 'producao', id: produto.id, name: produto.name, source: produto,
            unidade: produto.priceUnit || 'un', compra: null, compraOrigem: null, custo: custoUn,
            ficha
          }));

          // Um item marcado como “Também é revenda” existe fisicamente nas duas
          // tabelas do banco, mas operacionalmente é UM cadastro. A tabela une
          // os dois pelo nome e mostra “Insumo + revenda”.
          const insumos = supplies.map((x) => {
            const rev = revendaDaUnidade.find(
              (r) => normalizeName(r.productName) === normalizeName(x.name)
            );
            const compraInsumo = ultimaCompra(comprasDoInsumo(x.id));
            if (!rev) {
              return {
                key: `insumo:${x.id}`,
                tipo: 'insumo', id: x.id, name: x.name, source: x,
                unidade: x.unit || 'g', compra: compraInsumo, compraOrigem: 'insumo',
                custo: custoUnitarioInsumo(x.id, supplyPurchases)
              };
            }

            const compraRevenda = ultimaCompra(comprasDaRevenda(rev.id));
            const custoInsumo = custoUnitarioInsumo(x.id, supplyPurchases);
            const custoDaRevenda = custoRevenda(rev, resalePurchases);
            return {
              key: `insumo_revenda:${x.id}:${rev.id}`,
              tipo: 'insumo_revenda', id: x.id, resaleId: rev.id,
              name: x.name, source: x, resaleSource: rev,
              unidade: custoInsumo > 0 ? (x.unit || 'g') : (rev.priceUnit || 'un'),
              compra: compraInsumo || compraRevenda,
              compraOrigem: compraInsumo ? 'insumo' : 'revenda',
              custo: custoInsumo > 0 ? custoInsumo : custoDaRevenda
            };
          });

          // Revenda sem um insumo de mesmo nome continua sendo revenda pura.
          // As híbridas já foram incorporadas acima e não entram de novo.
          const revendas = revendaDaUnidade
            .filter((x) => !supplies.some((s) => normalizeName(s.name) === normalizeName(x.productName)))
            .map((x) => ({
              key: `revenda:${x.id}`,
              tipo: 'revenda', id: x.id, name: x.productName, source: x,
              unidade: x.priceUnit || 'un', compra: ultimaCompra(comprasDaRevenda(x.id)),
              compraOrigem: 'revenda', custo: custoRevenda(x, resalePurchases)
            }));

          return [...insumos, ...revendas, ...producao].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'));
        }, [produtosComFicha, supplies, supplyPurchases, revendaDaUnidade, resalePurchases]);

        const cadastrosFiltrados = cadastrosUnificados.filter((x) => {
          const bateTexto = x.name.toLowerCase().includes(busca.toLowerCase());
          const bateTipo = classeFiltro === 'todos' || x.tipo === classeFiltro;
          return bateTexto && bateTipo;
        });

        const atualizarCompraLinha = (linha, campos) => {
          if (linha.tipo === 'producao') return;
          const usaRevenda = linha.tipo === 'revenda'
            || (linha.tipo === 'insumo_revenda' && linha.compraOrigem === 'revenda');
          if (usaRevenda) {
            const rev = linha.resaleSource || linha.source;
            onSetUltimaCompraRevenda(rev.id, campos);
          } else {
            onSetUltimaCompraInsumo(linha.source.id, campos);
          }
        };

        const alterarTipoDaTabela = async (linha, novoTipo) => {
          if (!novoTipo || novoTipo === linha.tipo) return;

          if (novoTipo === 'insumo_revenda') {
            if (linha.tipo === 'insumo') {
              return onSetSupplyResale(linha.source, true);
            }
            if (linha.tipo === 'revenda') {
              let insumo = supplies.find((s) => normalizeName(s.name) === normalizeName(linha.name));
              if (!insumo) {
                insumo = await onAddSupply({
                  name: linha.name,
                  unit: unidadeBaseDaRevenda(linha.source.priceUnit || linha.source.unitOfMeasure),
                  supplyClass: 'insumo'
                });
              }
              if (insumo) return onSetSupplyResale(insumo, true);
              return;
            }
            window.alert('Para transformar um produto de produção em Insumo + revenda, mude primeiro para Insumo. Assim o sistema consegue conferir os vínculos da ficha e da vitrine com segurança.');
            return;
          }

          if (linha.tipo === 'insumo_revenda') {
            if (novoTipo === 'insumo') {
              return onSetSupplyResale(linha.source, false);
            }
            if (novoTipo === 'revenda') {
              return onChangeCatalogType({ ...linha, tipo: 'insumo' }, 'revenda');
            }
            if (novoTipo === 'producao') {
              await onSetSupplyResale(linha.source, false);
              return onChangeCatalogType({ ...linha, tipo: 'insumo' }, 'producao');
            }
          }

          return onChangeCatalogType(linha, novoTipo);
        };
'''
if old_catalog not in s:
    raise SystemExit('cadastrosUnificados block not found')
s = s.replace(old_catalog, new_catalog, 1)

# Filter includes hybrid type.
old_filter = """<PickerField value={classeFiltro} options={[{value:'todos',label:'Todos os tipos'}, ...TIPOS_ENTRADA]} onPick={(opt) => setClasseFiltro(opt.value)} className="field field-sm" />"""
new_filter = """<PickerField value={classeFiltro} options={[{value:'todos',label:'Todos os tipos'}, ...TIPOS_TABELA]} onPick={(opt) => setClasseFiltro(opt.value)} className="field field-sm" />"""
if old_filter not in s:
    raise SystemExit('type filter marker not found')
s = s.replace(old_filter, new_filter, 1)

# Name cell: hybrid edits both physical records together.
old_name = '''                                {linha.tipo === 'revenda' ? (
                                  <input value={x.productName} onChange={(e) => onUpdateSeparatedProduct({...x,productName:e.target.value})} className="field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48" />
                                ) : linha.tipo === 'insumo' ? (
                                  <input value={x.name} onChange={(e) => onUpdateSupply({...x,name:e.target.value})} className="field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48" />
                                ) : (
                                  <input value={x.name} onChange={(e) => onUpdateProduct({...x,name:e.target.value})} className="field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48" />
                                )}'''
new_name = '''                                {linha.tipo === 'revenda' ? (
                                  <input value={x.productName} onChange={(e) => onUpdateSeparatedProduct({...x,productName:e.target.value})} className="field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48" />
                                ) : linha.tipo === 'insumo_revenda' ? (
                                  <input
                                    value={x.name}
                                    onChange={(e) => {
                                      const name = e.target.value;
                                      onUpdateSupply({...x,name});
                                      if (linha.resaleSource) onUpdateSeparatedProduct({...linha.resaleSource,productName:name});
                                    }}
                                    className="field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48"
                                  />
                                ) : linha.tipo === 'insumo' ? (
                                  <input value={x.name} onChange={(e) => onUpdateSupply({...x,name:e.target.value})} className="field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48" />
                                ) : (
                                  <input value={x.name} onChange={(e) => onUpdateProduct({...x,name:e.target.value})} className="field h-8 px-2.5 text-[13px] font-semibold w-36 sm:w-48" />
                                )}'''
if old_name not in s:
    raise SystemExit('name cell marker not found')
s = s.replace(old_name, new_name, 1)

old_type_picker = '''                                  <PickerField value={linha.tipo} options={TIPOS_ENTRADA} onPick={(opt) => opt.value !== linha.tipo && onChangeCatalogType(linha, opt.value)} className="field h-8 pl-2.5 text-[12px] font-bold" />'''
new_type_picker = '''                                  <PickerField value={linha.tipo} options={TIPOS_TABELA} onPick={(opt) => alterarTipoDaTabela(linha, opt.value)} className="field h-8 pl-2.5 text-[12px] font-bold" />'''
if old_type_picker not in s:
    raise SystemExit('table type picker marker not found')
s = s.replace(old_type_picker, new_type_picker, 1)

# Unit cell: a hybrid line keeps the supply base unit here; sale unit/price live
# together in details on the same row.
old_unit = '''                                  {linha.tipo === 'insumo' ? (
                                    <PickerField value={x.unit} options={SUPPLY_UNITS.map((u) => ({value:u,label:u}))} onPick={(opt) => onUpdateSupply({...x,unit:opt.value})} className="field h-8 pl-2.5 text-[12px]" />
                                  ) : linha.tipo === 'revenda' ? (
                                    <PickerField value={x.priceUnit || 'un'} options={[{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]} onPick={(opt) => onUpdateSeparatedProduct({...x,priceUnit:opt.value})} className="field h-8 pl-2.5 text-[12px]" />
                                  ) : (
                                    <PickerField value={x.priceUnit || 'un'} options={[{value:'un',label:'un'},{value:'kg',label:'kg'}]} onPick={(opt) => onUpdateProduct({...x,priceUnit:opt.value})} className="field h-8 pl-2.5 text-[12px]" />
                                  )}'''
new_unit = '''                                  {linha.tipo === 'insumo' || linha.tipo === 'insumo_revenda' ? (
                                    <PickerField value={x.unit} options={SUPPLY_UNITS.map((u) => ({value:u,label:u}))} onPick={(opt) => onUpdateSupply({...x,unit:opt.value})} className="field h-8 pl-2.5 text-[12px]" />
                                  ) : linha.tipo === 'revenda' ? (
                                    <PickerField value={x.priceUnit || 'un'} options={[{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]} onPick={(opt) => onUpdateSeparatedProduct({...x,priceUnit:opt.value})} className="field h-8 pl-2.5 text-[12px]" />
                                  ) : (
                                    <PickerField value={x.priceUnit || 'un'} options={[{value:'un',label:'un'},{value:'kg',label:'kg'}]} onPick={(opt) => onUpdateProduct({...x,priceUnit:opt.value})} className="field h-8 pl-2.5 text-[12px]" />
                                  )}'''
if old_unit not in s:
    raise SystemExit('unit cell marker not found')
s = s.replace(old_unit, new_unit, 1)

# Route edits to the purchase record actually shown by the merged row.
repls = {
'''onType={(v) => linha.tipo === 'insumo' ? onSetUltimaCompraInsumo(x.id,{supplier:v}) : onSetUltimaCompraRevenda(x.id,{supplier:v})} onPick={(opt) => linha.tipo === 'insumo' ? onSetUltimaCompraInsumo(x.id,{supplier:opt.value}) : onSetUltimaCompraRevenda(x.id,{supplier:opt.value})}''':
'''onType={(v) => atualizarCompraLinha(linha,{supplier:v})} onPick={(opt) => atualizarCompraLinha(linha,{supplier:opt.value})}''',
'''onChange={(e) => linha.tipo === 'insumo' ? onSetUltimaCompraInsumo(x.id,{purchaseDate:e.target.value}) : onSetUltimaCompraRevenda(x.id,{purchaseDate:e.target.value})}''':
'''onChange={(e) => atualizarCompraLinha(linha,{purchaseDate:e.target.value})}''',
'''onChange={(e) => linha.tipo === 'insumo' ? onSetUltimaCompraInsumo(x.id,{qty:Number(e.target.value)||0}) : onSetUltimaCompraRevenda(x.id,{qty:Number(e.target.value)||0})}''':
'''onChange={(e) => atualizarCompraLinha(linha,{qty:Number(e.target.value)||0})}''',
'''onChange={(e) => linha.tipo === 'insumo' ? onSetUltimaCompraInsumo(x.id,{cost:Number(e.target.value)||0}) : onSetUltimaCompraRevenda(x.id,{cost:Number(e.target.value)||0})}''':
'''onChange={(e) => atualizarCompraLinha(linha,{cost:Number(e.target.value)||0})}'''
}
for old, new in repls.items():
    if old not in s:
        raise SystemExit(f'purchase edit marker not found: {old[:60]}')
    s = s.replace(old, new, 1)

old_purchase_unit = '''                                    {linha.tipo === 'revenda' ? (
                                      <div className="w-14"><PickerField value={c?.purchaseUnit || x.priceUnit || 'un'} options={[{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]} onPick={(opt) => onSetUltimaCompraRevenda(x.id,{purchaseUnit:opt.value})} className="field h-8 pl-2 text-[11px]" /></div>
                                    ) : <span className="t-micro">{x.unit}</span>}'''
new_purchase_unit = '''                                    {linha.tipo === 'revenda' || (linha.tipo === 'insumo_revenda' && linha.compraOrigem === 'revenda') ? (
                                      <div className="w-14"><PickerField value={c?.purchaseUnit || (linha.resaleSource || x).priceUnit || 'un'} options={[{value:'un',label:'un'},{value:'kg',label:'kg'},{value:'g',label:'g'}]} onPick={(opt) => atualizarCompraLinha(linha,{purchaseUnit:opt.value})} className="field h-8 pl-2 text-[11px]" /></div>
                                    ) : <span className="t-micro">{x.unit}</span>}'''
if old_purchase_unit not in s:
    raise SystemExit('purchase unit marker not found')
s = s.replace(old_purchase_unit, new_purchase_unit, 1)

old_details = '''                                {linha.tipo === 'insumo' ? (
                                  <div className="w-28"><PickerField value={x.supplyClass || 'insumo'} options={SUPPLY_CLASSES} onPick={(opt) => onUpdateSupply({...x,supplyClass:opt.value})} className="field h-8 pl-2.5 text-[12px]" /></div>
                                ) : (
                                  <div className="flex items-center gap-1">
                                    <span className="t-micro">Preço</span>
                                    <input type="number" min="0" step="0.01" value={x.price || ''} onChange={(e) => linha.tipo === 'revenda' ? onUpdateSeparatedProduct({...x,price:Number(e.target.value)||0}) : onUpdateProduct({...x,price:Number(e.target.value)||0})} className="field h-8 px-2 text-[12px] text-right font-bold tnum no-spin w-20" />
                                  </div>
                                )}'''
new_details = '''                                {linha.tipo === 'insumo' ? (
                                  <div className="w-28"><PickerField value={x.supplyClass || 'insumo'} options={SUPPLY_CLASSES} onPick={(opt) => onUpdateSupply({...x,supplyClass:opt.value})} className="field h-8 pl-2.5 text-[12px]" /></div>
                                ) : linha.tipo === 'insumo_revenda' ? (
                                  <div className="flex items-center gap-1.5 min-w-[220px]">
                                    <div className="w-24"><PickerField value={x.supplyClass || 'insumo'} options={SUPPLY_CLASSES} onPick={(opt) => onUpdateSupply({...x,supplyClass:opt.value})} className="field h-8 pl-2 text-[11px]" /></div>
                                    <span className="t-micro">Venda</span>
                                    <input type="number" min="0" step="0.01" value={linha.resaleSource?.price || ''} onChange={(e) => linha.resaleSource && onUpdateSeparatedProduct({...linha.resaleSource,price:Number(e.target.value)||0})} className="field h-8 px-2 text-[12px] text-right font-bold tnum no-spin w-20" />
                                    <span className="t-micro">/{linha.resaleSource?.priceUnit || 'un'}</span>
                                  </div>
                                ) : (
                                  <div className="flex items-center gap-1">
                                    <span className="t-micro">Preço</span>
                                    <input type="number" min="0" step="0.01" value={x.price || ''} onChange={(e) => linha.tipo === 'revenda' ? onUpdateSeparatedProduct({...x,price:Number(e.target.value)||0}) : onUpdateProduct({...x,price:Number(e.target.value)||0})} className="field h-8 px-2 text-[12px] text-right font-bold tnum no-spin w-20" />
                                  </div>
                                )}'''
if old_details not in s:
    raise SystemExit('details marker not found')
s = s.replace(old_details, new_details, 1)

# Longer type label needs a little more room.
s = s.replace('<div className="w-28">\n                                  <PickerField value={linha.tipo} options={TIPOS_TABELA}', '<div className="w-40">\n                                  <PickerField value={linha.tipo} options={TIPOS_TABELA}', 1)

old_help = 'O tipo pode ser corrigido na própria tabela. O sistema bloqueia a troca quando ela quebraria ficha técnica, vitrine ou histórico.'
new_help = 'O tipo pode ser Insumo, Revenda, Insumo + revenda ou Produção. Itens híbridos aparecem uma única vez na tabela.'
if old_help not in s:
    raise SystemExit('table help marker not found')
s = s.replace(old_help, new_help, 1)

p.write_text(s, encoding='utf-8')
print('patched hybrid catalog type')
