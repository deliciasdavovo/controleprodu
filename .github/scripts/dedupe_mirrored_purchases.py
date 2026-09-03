from pathlib import Path
import re

p = Path('index.html')
s = p.read_text(encoding='utf-8')

s, n = re.subn(
    r'<meta name="app-version" content="[^"]+" />',
    '<meta name="app-version" content="2026-09-03-insumo-revenda-um-form-2" />',
    s,
    count=1,
)
if n != 1:
    raise SystemExit('version marker not found')

old = r'''        separatedProducts.filter((p) => p.unit === currentUnit).forEach((p) => {
          resalePurchases.filter((c) => c.separatedProductId === p.id).forEach((c) => {
            compras.push({
              id: c.id,
              itemId: `r${p.id}`,
              item: p.productName,
              tipo: 'Revenda',
              unidade: c.purchaseUnit || p.priceUnit || 'un',
              fornecedor: (c.supplier || '').trim() || 'Sem fornecedor',
              data: c.purchaseDate || '',
              criadoEm: c.criadoEm,
              qty: Number(c.qty) || 0,
              cost: Number(c.cost) || 0
            });
          });
        });
'''

new = r'''        separatedProducts.filter((p) => p.unit === currentUnit).forEach((p) => {
          const insumoMesmoNome = supplies.find(
            (s) => normalizeName(s.name) === normalizeName(p.productName)
          );

          resalePurchases.filter((c) => c.separatedProductId === p.id).forEach((c) => {
            // Quando "Também é revenda" está marcado, a mesma entrada grava o
            // custo nos dois lados para alimentar ficha técnica e CMV. Na tela
            // de fornecedores, porém, é UMA compra só. O espelho de revenda é
            // ignorado aqui para o total comprado não aparecer em dobro.
            const espelhoDoInsumo = insumoMesmoNome && supplyPurchases.some((ci) => {
              if (ci.supplyId !== insumoMesmoNome.id) return false;
              const mesmoFornecedor = normalizeName(ci.supplier || '') === normalizeName(c.supplier || '');
              const mesmaData = (ci.purchaseDate || '') === (c.purchaseDate || '');
              const mesmoValor = Math.abs((Number(ci.cost) || 0) - (Number(c.cost) || 0)) < 0.005;
              if (!(mesmoFornecedor && mesmaData && mesmoValor)) return false;

              const ti = ci.criadoEm ? new Date(ci.criadoEm).getTime() : 0;
              const tr = c.criadoEm ? new Date(c.criadoEm).getTime() : 0;
              // Registros criados pelo mesmo submit nascem praticamente juntos.
              // Para dados antigos sem timestamp, fornecedor+data+valor é a
              // melhor assinatura disponível.
              return !ti || !tr || Math.abs(ti - tr) <= 120000;
            });
            if (espelhoDoInsumo) return;

            compras.push({
              id: c.id,
              itemId: `r${p.id}`,
              item: p.productName,
              tipo: 'Revenda',
              unidade: c.purchaseUnit || p.priceUnit || 'un',
              fornecedor: (c.supplier || '').trim() || 'Sem fornecedor',
              data: c.purchaseDate || '',
              criadoEm: c.criadoEm,
              qty: Number(c.qty) || 0,
              cost: Number(c.cost) || 0
            });
          });
        });
'''

if old not in s:
    raise SystemExit('reunirCompras resale block not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('dedupe mirror purchases patched')
