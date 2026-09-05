from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')

old_version = '<meta name="app-version" content="2026-09-05-formato-br-entrada-1" />'
new_version = '<meta name="app-version" content="2026-09-05-fornecedor-anterior-enter-1" />'
if old_version in s:
    s = s.replace(old_version, new_version, 1)
elif new_version not in s:
    raise SystemExit('app version marker not found')

old = """                          <PickerField
                            value={draft.supplier}
                            options={fornecedores.map((f) => ({ value: f, label: f }))}
                            onType={(supplier) => setDraft((d) => ({ ...d, supplier }))}
                            onPick={(opt) => setDraft((d) => ({ ...d, supplier: opt.value }))}
                            placeholder={compraExistente?.supplier || 'Fornecedor'}
                            emptyLabel=\"Fornecedor novo\"
                            className=\"field field-md\"
                          />"""

new = """                          <PickerField
                            value={draft.supplier}
                            options={[
                              ...(compraExistente?.supplier
                                ? [{
                                    value: compraExistente.supplier,
                                    label: compraExistente.supplier,
                                    hint: 'Última compra'
                                  }]
                                : []),
                              ...fornecedores
                                .filter((f) => String(f || '').trim().toLocaleLowerCase('pt-BR') !== String(compraExistente?.supplier || '').trim().toLocaleLowerCase('pt-BR'))
                                .map((f) => ({ value: f, label: f }))
                            ]}
                            onType={(supplier) => setDraft((d) => ({ ...d, supplier }))}
                            onPick={(opt) => setDraft((d) => ({ ...d, supplier: opt.value }))}
                            placeholder={compraExistente?.supplier || 'Fornecedor'}
                            emptyLabel=\"Fornecedor novo\"
                            className=\"field field-md\"
                          />"""

if old not in s:
    raise SystemExit('supplier picker block not found')
s = s.replace(old, new, 1)

for required in [
    '2026-09-05-fornecedor-anterior-enter-1',
    "hint: 'Última compra'",
    'value: compraExistente.supplier',
    "toLocaleLowerCase('pt-BR')"
]:
    if required not in s:
        raise SystemExit(f'missing required marker: {required}')

p.write_text(s, encoding='utf-8')
