from pathlib import Path
import re
p = Path('index.html')
s = p.read_text(encoding='utf-8')
s, n = re.subn(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-03-tipo-insumo-revenda-2" />', s, count=1)
if n != 1:
    raise SystemExit('version marker not found')
old = '''            if (novoTipo === 'producao') {
              await onSetSupplyResale(linha.source, false);
              return onChangeCatalogType({ ...linha, tipo: 'insumo' }, 'producao');
            }'''
new = '''            if (novoTipo === 'producao') {
              window.alert('Para mudar Insumo + revenda para Produção, mude primeiro para Insumo. O sistema confere os vínculos da ficha antes da segunda troca sem desligar a revenda por engano.');
              return;
            }'''
if old not in s:
    raise SystemExit('hybrid production branch not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('guarded hybrid -> production conversion')
