from pathlib import Path
import re

p = Path('index.html')
text = p.read_text(encoding='utf-8')
original = text


def replace_once(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f'{label} marker not found')
    text = text.replace(old, new, 1)

# Version
text = re.sub(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-02-picker-design-1" />', text, count=1)

# PickerField: allow disabled state and data attributes so custom pickers can be used in keyboard flows.
replace_once(
"""        inputRef,
        onKeyDown,
        title,
        emptyLabel = 'Nada encontrado'
      }) => {""",
"""        inputRef,
        onKeyDown,
        title,
        disabled = false,
        inputProps = {},
        emptyLabel = 'Nada encontrado'
      }) => {""",
'picker props')

replace_once(
"""        const openList = () => { setSearch(''); setTyped(false); setActive(-1); setOpen(true); };
        const close = () => { setOpen(false); setActive(-1); setTyped(false); };""",
"""        const openList = () => {
          if (disabled) return;
          setSearch('');
          setTyped(false);
          setActive(-1);
          setOpen(true);
        };
        const close = () => { setOpen(false); setActive(-1); setTyped(false); };""",
'picker openList')

replace_once(
"""        const handleChange = (e) => {
          const texto = e.target.value;""",
"""        const handleChange = (e) => {
          if (disabled) return;
          const texto = e.target.value;""",
'picker handleChange')

replace_once(
"""              autoComplete="off"
              title={title}
              placeholder={placeholderAtual}
              value={texto}
              onChange={handleChange}
              onMouseDown={() => { if (!open) openList(); }}
              onBlur={close}
              onKeyDown={handleKeyDown}
              className={`${className} field-select`}
            />""",
"""              autoComplete="off"
              title={title}
              disabled={disabled}
              placeholder={placeholderAtual}
              value={texto}
              onChange={handleChange}
              onMouseDown={() => { if (!disabled && !open) openList(); }}
              onBlur={close}
              onKeyDown={handleKeyDown}
              {...inputProps}
              className={`${className} field-select ${disabled ? 'picker-disabled' : ''}`}
            />""",
'picker input')

# Picker visual polish: same surface/radius hierarchy as the rest of the app.
replace_once(
"""      .picker-panel {
        position: fixed;
        z-index: 140;
        padding: 4px;
        background: var(--bg-surface);
        border: 1px solid var(--hairline);
        border-radius: var(--radius-md);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 40px rgba(0, 0, 0, 0.16);
        overflow-y: auto;
        overscroll-behavior: contain;
      }
      .picker-option {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        width: 100%;
        text-align: left;
        padding: 7px 10px;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: -0.01em;
        color: var(--ink-1);
        transition: background-color .12s ease, color .12s ease;
      }
      .picker-option[data-active=\"true\"] { background: var(--accent); color: #fff; }""",
"""      .picker-panel {
        position: fixed;
        z-index: 140;
        padding: 6px;
        background: rgba(255, 255, 255, 0.98);
        border: 1px solid rgba(60, 60, 67, 0.12);
        border-radius: 16px;
        box-shadow: 0 18px 50px rgba(14, 9, 55, 0.16), 0 2px 8px rgba(0, 0, 0, 0.06);
        overflow-y: auto;
        overscroll-behavior: contain;
        backdrop-filter: saturate(180%) blur(18px);
        -webkit-backdrop-filter: saturate(180%) blur(18px);
      }
      .picker-option {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        width: 100%;
        min-height: 38px;
        text-align: left;
        padding: 8px 11px;
        border-radius: 11px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: -0.01em;
        color: var(--ink-1);
        transition: background-color .12s ease, color .12s ease, transform .1s ease;
      }
      .picker-option:hover { background: rgba(14, 9, 55, 0.055); }
      .picker-option:active { transform: scale(0.99); }
      .picker-option[data-active=\"true\"] { background: var(--accent); color: #fff; }
      .picker-disabled {
        background-color: rgba(118, 118, 128, 0.055) !important;
        color: var(--ink-4) !important;
        cursor: not-allowed !important;
        opacity: .88;
      }""",
'picker css')

# Quick supply Enter can also accept custom Unit/Class pickers.
insert_marker = """          if (tipo === 'fornecedor') {
            const digitado = String(campo.value || '').trim();"""
if insert_marker not in text:
    raise SystemExit('autocomplete insert marker not found')
text = text.replace(insert_marker, """          if (tipo === 'unidade') {
            const sugestao = primeiraSugestaoCadastro(SUPPLY_UNITS, campo.value);
            if (!sugestao) return false;
            setDraft((d) => ({ ...d, unit: String(sugestao) }));
            return true;
          }

          if (tipo === 'classe') {
            const sugestao = primeiraSugestaoCadastro(SUPPLY_CLASSES, campo.value, (c) => c.label);
            if (!sugestao) return false;
            setDraft((d) => ({ ...d, supplyClass: sugestao.value }));
            return true;
          }

""" + insert_marker, 1)

# Quick Supply: replace browser datalist with the app PickerField.
old_name = """                        <input
                          ref={nomeRef}
                          type=\"text\"
                          list=\"cadastro-insumos-list\"
                          value={draft.name}
                          onChange={(e) => setDraft((d) => ({ ...d, name: e.target.value }))}
                          onBlur={(e) => aplicarInsumoExistente(e.target.value)}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          data-insumo-field=\"nome\"
                          placeholder=\"Digite ou escolha um insumo\"
                          className=\"field field-md font-semibold\"
                        />"""
new_name = """                        <PickerField
                          inputRef={nomeRef}
                          value={draft.name}
                          options={supplies.map((s) => ({
                            value: s.name,
                            label: s.name,
                            hint: `${s.unit} · ${SUPPLY_CLASSES.find((c) => c.value === (s.supplyClass || 'insumo'))?.label || 'Ingrediente'}`
                          }))}
                          onType={(nome) => {
                            const existente = supplies.find((s) => normalizeName(s.name) === normalizeName(String(nome || '').trim()));
                            setDraft((d) => existente
                              ? { ...d, name: nome, unit: existente.unit || d.unit, supplyClass: existente.supplyClass || 'insumo' }
                              : { ...d, name: nome });
                          }}
                          onPick={(opt) => aplicarInsumoExistente(opt.value)}
                          onKeyDown={avancarCadastroInsumo}
                          inputProps={{ 'data-insumo-flow': true, 'data-insumo-field': 'nome' }}
                          placeholder=\"Digite ou escolha um insumo\"
                          emptyLabel=\"Insumo novo — será cadastrado ao salvar\"
                          className=\"field field-md font-semibold\"
                        />"""
replace_once(old_name, new_name, 'quick supply name')

old_unit = """                        <select
                          value={draft.unit}
                          onChange={(e) => setDraft((d) => ({ ...d, unit: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          disabled={!!draftExistente}
                          title={draftExistente ? 'Unidade fixa do cadastro. Para alterar, use a tabela de insumos.' : 'Unidade do novo insumo'}
                          className=\"field field-md field-select disabled:bg-black/[0.035] disabled:text-[#86868b] disabled:cursor-not-allowed\"
                        >
                          {SUPPLY_UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
                        </select>"""
new_unit = """                        {draftExistente ? (
                          <div
                            title=\"Unidade fixa do cadastro. Para alterar, use a tabela de insumos.\"
                            className=\"field field-md flex items-center px-3 bg-black/[0.035] text-[#86868b] cursor-not-allowed\"
                          >
                            {draft.unit}
                          </div>
                        ) : (
                          <PickerField
                            value={draft.unit}
                            options={SUPPLY_UNITS.map((u) => ({ value: u, label: u }))}
                            onPick={(opt) => setDraft((d) => ({ ...d, unit: opt.value }))}
                            onKeyDown={avancarCadastroInsumo}
                            inputProps={{ 'data-insumo-flow': true, 'data-insumo-field': 'unidade' }}
                            title=\"Unidade do novo insumo\"
                            className=\"field field-md\"
                          />
                        )}"""
replace_once(old_unit, new_unit, 'quick supply unit')

old_class = """                        <select
                          value={draft.supplyClass}
                          onChange={(e) => setDraft((d) => ({ ...d, supplyClass: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          disabled={!!draftExistente}
                          title={draftExistente ? 'Classe fixa do cadastro. Para alterar, use a tabela de insumos.' : 'Só organiza a lista — as três entram no CMV do mesmo jeito'}
                          className=\"field field-md field-select disabled:bg-black/[0.035] disabled:text-[#86868b] disabled:cursor-not-allowed\"
                        >
                          {SUPPLY_CLASSES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                        </select>"""
new_class = """                        {draftExistente ? (
                          <div
                            title=\"Classe fixa do cadastro. Para alterar, use a tabela de insumos.\"
                            className=\"field field-md flex items-center px-3 bg-black/[0.035] text-[#86868b] cursor-not-allowed\"
                          >
                            {SUPPLY_CLASSES.find((c) => c.value === draft.supplyClass)?.label || draft.supplyClass}
                          </div>
                        ) : (
                          <PickerField
                            value={draft.supplyClass}
                            options={SUPPLY_CLASSES}
                            onPick={(opt) => setDraft((d) => ({ ...d, supplyClass: opt.value }))}
                            onKeyDown={avancarCadastroInsumo}
                            inputProps={{ 'data-insumo-flow': true, 'data-insumo-field': 'classe' }}
                            title=\"Classe do novo insumo\"
                            className=\"field field-md\"
                          />
                        )}"""
replace_once(old_class, new_class, 'quick supply class')

old_supplier = """                        <input
                          type=\"text\"
                          list=\"cadastro-fornecedores-list\"
                          value={draft.supplier}
                          onChange={(e) => setDraft((d) => ({ ...d, supplier: e.target.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          data-insumo-flow
                          data-insumo-field=\"fornecedor\"
                          placeholder={draftUltimaCompra?.supplier || 'Fornecedor'}
                          className=\"field field-md\"
                        />"""
new_supplier = """                        <PickerField
                          value={draft.supplier}
                          options={fornecedores.map((f) => ({ value: f, label: f }))}
                          onType={(supplier) => setDraft((d) => ({ ...d, supplier }))}
                          onPick={(opt) => setDraft((d) => ({ ...d, supplier: opt.value }))}
                          onKeyDown={avancarCadastroInsumo}
                          inputProps={{ 'data-insumo-flow': true, 'data-insumo-field': 'fornecedor' }}
                          placeholder={draftUltimaCompra?.supplier || 'Fornecedor'}
                          emptyLabel=\"Fornecedor novo — será salvo com esta compra\"
                          className=\"field field-md\"
                        />"""
replace_once(old_supplier, new_supplier, 'quick supplier')

# Remove browser datalists completely.
text, n = re.subn(r'''\n\s*<datalist id=\"cadastro-insumos-list\">.*?</datalist>\s*<datalist id=\"cadastro-fornecedores-list\">.*?</datalist>''', '', text, count=1, flags=re.S)
if n != 1:
    raise SystemExit('datalist block not found')

# Supply class filter -> custom picker.
replace_once(
"""                    <select
                      value={classeFiltro}
                      onChange={(e) => setClasseFiltro(e.target.value)}
                      className=\"field field-sm field-select field-auto\"
                    >
                      <option value=\"todos\">Todas as classes</option>
                      {SUPPLY_CLASSES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>""",
"""                    <div className=\"w-40\">
                      <PickerField
                        value={classeFiltro}
                        options={[{ value: 'todos', label: 'Todas as classes' }, ...SUPPLY_CLASSES]}
                        onPick={(opt) => setClasseFiltro(opt.value)}
                        className=\"field field-sm\"
                      />
                    </div>""",
'supply filter')

# Supply table unit.
replace_once(
"""                                <select
                                  value={s.unit}
                                  onChange={(e) => onUpdateSupply({ ...s, unit: e.target.value })}
                                  className=\"field field-select h-8 pl-2.5 text-[12px] w-16\"
                                >
                                  {SUPPLY_UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
                                </select>""",
"""                                <div className=\"w-16\">
                                  <PickerField
                                    value={s.unit}
                                    options={SUPPLY_UNITS.map((u) => ({ value: u, label: u }))}
                                    onPick={(opt) => onUpdateSupply({ ...s, unit: opt.value })}
                                    className=\"field h-8 pl-2.5 text-[12px]\"
                                  />
                                </div>""",
'table supply unit')

# Supply variation unit.
replace_once(
"""                                  <select
                                    value={s.variationUnit || ''}
                                    onChange={(e) => onUpdateSupply({ ...s, variationUnit: e.target.value })}
                                    title=\"Como a loja compra ou usa este insumo\"
                                    className=\"field field-select h-8 pl-2.5 text-[12px] w-20\"
                                  >
                                    <option value=\"\">—</option>
                                    {VARIATION_UNITS.filter((u) => u !== s.unit).map((u) => <option key={u} value={u}>{u}</option>)}
                                  </select>""",
"""                                  <div className=\"w-20\">
                                    <PickerField
                                      value={s.variationUnit || ''}
                                      options={[{ value: '', label: '—' }, ...VARIATION_UNITS.filter((u) => u !== s.unit).map((u) => ({ value: u, label: u }))]}
                                      onPick={(opt) => onUpdateSupply({ ...s, variationUnit: opt.value })}
                                      title=\"Como a loja compra ou usa este insumo\"
                                      className=\"field h-8 pl-2.5 text-[12px]\"
                                    />
                                  </div>""",
'table variation unit')

# Supply table class.
replace_once(
"""                                <select
                                  value={s.supplyClass || 'insumo'}
                                  onChange={(e) => onUpdateSupply({ ...s, supplyClass: e.target.value })}
                                  className=\"field field-select h-8 pl-2.5 text-[12px] w-28\"
                                >
                                  {SUPPLY_CLASSES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                                </select>""",
"""                                <div className=\"w-28\">
                                  <PickerField
                                    value={s.supplyClass || 'insumo'}
                                    options={SUPPLY_CLASSES}
                                    onPick={(opt) => onUpdateSupply({ ...s, supplyClass: opt.value })}
                                    className=\"field h-8 pl-2.5 text-[12px]\"
                                  />
                                </div>""",
'table supply class')

# Product category form.
replace_once(
"""                    <select
                      ref={categoryRef}
                      value={draft.category}
                      onChange={(e) => setField('category', e.target.value)}
                      onKeyDown={goToField(shelfLifeRef)}
                      className=\"field field-md field-select\"
                    >
                      {PRODUCT_CATEGORIES.map((c) => (
                        <option key={c.value} value={c.value}>{c.label}</option>
                      ))}
                    </select>""",
"""                    <PickerField
                      inputRef={categoryRef}
                      value={draft.category}
                      options={PRODUCT_CATEGORIES}
                      onPick={(opt) => setField('category', opt.value)}
                      onKeyDown={goToField(shelfLifeRef)}
                      className=\"field field-md\"
                    />""",
'product category form')

# Product responsible filter.
replace_once(
"""                <select
                  value={filterResponsible}
                  onChange={(e) => setFilterResponsible(e.target.value)}
                  className=\"field field-sm field-select field-auto\"
                >
                  <option value=\"todos\">Todos os responsáveis</option>
                  {responsibleOptions.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                  {hasUnassigned && <option value=\"sem\">{NO_RESPONSIBLE_LABEL}</option>}
                </select>""",
"""                <div className=\"w-52 max-w-full\">
                  <PickerField
                    value={filterResponsible}
                    options={[
                      { value: 'todos', label: 'Todos os responsáveis' },
                      ...responsibleOptions.map((r) => ({ value: r, label: r })),
                      ...(hasUnassigned ? [{ value: 'sem', label: NO_RESPONSIBLE_LABEL }] : [])
                    ]}
                    onPick={(opt) => setFilterResponsible(opt.value)}
                    className=\"field field-sm\"
                  />
                </div>""",
'product responsible filter')

# Product table category.
replace_once(
"""                            <select
                              value={p.category}
                              onChange={(e) => onUpdateProduct({ ...p, category: e.target.value })}
                              title=\"Categoria do produto\"
                              className=\"field field-select h-8 pl-2.5 text-[12px] w-28 sm:w-32\"
                            >
                              {PRODUCT_CATEGORIES.map((c) => (
                                <option key={c.value} value={c.value}>{c.label}</option>
                              ))}
                            </select>""",
"""                            <div className=\"w-28 sm:w-32\">
                              <PickerField
                                value={p.category}
                                options={PRODUCT_CATEGORIES}
                                onPick={(opt) => onUpdateProduct({ ...p, category: opt.value })}
                                title=\"Categoria do produto\"
                                className=\"field h-8 pl-2.5 text-[12px]\"
                              />
                            </div>""",
'product table category')

if text == original:
    raise SystemExit('index unchanged')

p.write_text(text, encoding='utf-8')
print('picker design updated')
