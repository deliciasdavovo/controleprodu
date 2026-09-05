from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old_version = '<meta name="app-version" content="2026-09-05-custo-kg-litro-unidade-1" />'
new_version = '<meta name="app-version" content="2026-09-05-autocomplete-enter-1" />'
if old_version in s:
    s = s.replace(old_version, new_version, 1)
elif new_version not in s:
    raise SystemExit('app version marker not found')

old = """          // Enter só escolhe quando alguém está destacado na lista;\n          // fora isso o Enter segue para quem usa o campo\n          if (e.key === 'Enter' && open && visible[active]) {\n            e.preventDefault();\n            choose(visible[active]);\n            return;\n          }"""
new = """          // No autocomplete, Enter confirma a sugestão antes de avançar\n          // no formulário. Se a pessoa ainda não usou as setas, a primeira\n          // sugestão visível é a opção natural. O stopPropagation impede o\n          // formulário pai de pular para o próximo campo no mesmo Enter.\n          if (e.key === 'Enter' && open && visible.length > 0) {\n            const escolha = visible[active >= 0 ? active : 0];\n            e.preventDefault();\n            e.stopPropagation();\n            choose(escolha);\n            return;\n          }"""
if old not in s:
    raise SystemExit('PickerField Enter block not found')
s = s.replace(old, new, 1)

for marker in [
    '2026-09-05-autocomplete-enter-1',
    'const escolha = visible[active >= 0 ? active : 0];',
    'e.stopPropagation();',
    'onKeyDown={avancarEntradaRapida}',
    'onPick={selecionarCadastro}'
]:
    if marker not in s:
        raise SystemExit(f'missing marker: {marker}')

p.write_text(s, encoding='utf-8')
