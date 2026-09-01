from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')
original = text

old_handler = """        const avancarCadastroInsumo = (e) => {
          if (e.key !== 'Enter' || e.shiftKey || e.ctrlKey || e.metaKey || e.altKey) return;
          const form = e.currentTarget.form;
          if (!form) return;
          const campos = Array.from(form.querySelectorAll('[data-insumo-flow]'));
          const idx = campos.indexOf(e.currentTarget);
          if (idx >= 0 && idx < campos.length - 1) {
            e.preventDefault();
            const proximo = campos[idx + 1];
            proximo.focus();
            if (proximo.select && proximo.tagName === 'INPUT') proximo.select();
          }
        };"""

new_handler = """        const primeiraSugestaoCadastro = (lista, texto, getLabel = (x) => x) => {
          const termo = normalizeName(String(texto || '').trim());
          if (!termo) return null;
          const rotulo = (item) => normalizeName(String(getLabel(item) || ''));
          return lista.find((item) => rotulo(item) === termo)
            || lista.find((item) => rotulo(item).startsWith(termo))
            || lista.find((item) => rotulo(item).includes(termo))
            || null;
        };

        const aceitarSugestaoCadastroInsumo = (campo) => {
          const tipo = campo?.dataset?.insumoField || '';

          if (tipo === 'nome') {
            const sugestao = primeiraSugestaoCadastro(supplies, campo.value, (s) => s.name);
            if (!sugestao) return false;
            setDraft((d) => ({
              ...d,
              name: sugestao.name,
              unit: sugestao.unit || d.unit,
              supplyClass: sugestao.supplyClass || 'insumo'
            }));
            return true;
          }

          if (tipo === 'fornecedor') {
            const digitado = String(campo.value || '').trim();
            const sugestao = digitado
              ? primeiraSugestaoCadastro(fornecedores, digitado)
              : (draftUltimaCompra?.supplier || '');
            if (!sugestao) return false;
            setDraft((d) => ({ ...d, supplier: String(sugestao) }));
            return true;
          }

          if (tipo === 'qtd' && !String(campo.value || '').trim() && draftUltimaCompra?.qty) {
            setDraft((d) => ({ ...d, qty: String(draftUltimaCompra.qty) }));
            return true;
          }

          if (tipo === 'custo' && !String(campo.value || '').trim() && draftUltimaCompra?.cost) {
            setDraft((d) => ({ ...d, cost: String(draftUltimaCompra.cost) }));
            return true;
          }

          return false;
        };

        const avancarCadastroInsumo = (e) => {
          if (e.key !== 'Enter' || e.shiftKey || e.ctrlKey || e.metaKey || e.altKey) return;
          const form = e.currentTarget.form;
          if (!form) return;

          // Enter primeiro aceita a sugestão visível/autocomplete daquele campo.
          aceitarSugestaoCadastroInsumo(e.currentTarget);

          const campos = Array.from(form.querySelectorAll('[data-insumo-flow]'));
          const idx = campos.indexOf(e.currentTarget);
          if (idx >= 0 && idx < campos.length - 1) {
            e.preventDefault();
            const proximo = campos[idx + 1];
            requestAnimationFrame(() => {
              proximo.focus();
              if (proximo.select && proximo.tagName === 'INPUT') proximo.select();
            });
          }
        };"""

if old_handler not in text:
    raise SystemExit('handler marker not found')
text = text.replace(old_handler, new_handler, 1)

repls = [
    ("""                          onKeyDown={avancarCadastroInsumo}\n                          data-insumo-flow\n                          placeholder=\"Digite ou escolha um insumo\"""",
     """                          onKeyDown={avancarCadastroInsumo}\n                          data-insumo-flow\n                          data-insumo-field=\"nome\"\n                          placeholder=\"Digite ou escolha um insumo\""""),
    ("""                          onKeyDown={avancarCadastroInsumo}\n                          data-insumo-flow\n                          placeholder={draftUltimaCompra?.supplier || 'Fornecedor'}""",
     """                          onKeyDown={avancarCadastroInsumo}\n                          data-insumo-flow\n                          data-insumo-field=\"fornecedor\"\n                          placeholder={draftUltimaCompra?.supplier || 'Fornecedor'}"""),
    ("""                          onKeyDown={avancarCadastroInsumo}\n                          data-insumo-flow\n                          placeholder={draftUltimaCompra?.qty ? String(draftUltimaCompra.qty) : '0'}""",
     """                          onKeyDown={avancarCadastroInsumo}\n                          data-insumo-flow\n                          data-insumo-field=\"qtd\"\n                          placeholder={draftUltimaCompra?.qty ? String(draftUltimaCompra.qty) : '0'}"""),
    ("""                          onKeyDown={avancarCadastroInsumo}\n                          data-insumo-flow\n                          placeholder={draftUltimaCompra?.cost ? String(draftUltimaCompra.cost) : '0,00'}""",
     """                          onKeyDown={avancarCadastroInsumo}\n                          data-insumo-flow\n                          data-insumo-field=\"custo\"\n                          placeholder={draftUltimaCompra?.cost ? String(draftUltimaCompra.cost) : '0,00'}""")
]

for old, new in repls:
    if old not in text:
        raise SystemExit('field marker not found: ' + old[:70])
    text = text.replace(old, new, 1)

# Atualiza versão para ajudar a confirmar que o navegador carregou esta revisão.
import re
text = re.sub(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-01-insumo-enter-autocomplete-3" />', text, count=1)

if text == original:
    raise SystemExit('nothing changed')
path.write_text(text, encoding='utf-8')
print('autocomplete por Enter corrigido')
