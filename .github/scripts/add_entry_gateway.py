from pathlib import Path
import re

p = Path('index.html')
text = p.read_text(encoding='utf-8')
original = text

# version
text = re.sub(r'<meta name="app-version" content="[^"]+" />', '<meta name="app-version" content="2026-09-02-home-vitrine-cmv-1" />', text, count=1)

# Add gateway component right before MAIN APP COMPONENT
marker = """      // ==========================================\n      // MAIN APP COMPONENT\n      // ==========================================\n      function App() {"""
if marker not in text:
    raise SystemExit('main app marker not found')

gateway = r'''      // ==========================================
      // TELA INICIAL — ESCOLHA DO MÓDULO
      //
      // Antes de abrir qualquer informação operacional, a pessoa escolhe
      // qual assunto veio resolver. Isso separa o balcão (Vitrine) da gestão
      // de custo (CMV) e reduz a quantidade de informação na primeira tela.
      // ==========================================
      const EntryScreen = ({ onChoose }) => (
        <div className="min-h-screen bg-[var(--bg-canvas)] flex items-center justify-center px-4 py-10">
          <div className="w-full max-w-4xl">
            <div className="text-center mb-8 sm:mb-10">
              <div className="w-14 h-14 rounded-[18px] bg-[#0E0937] text-white flex items-center justify-center mx-auto text-[20px] font-extrabold tracking-tight shadow-apple">
                DV
              </div>
              <p className="t-overline mt-4">Delícias da Vovó</p>
              <h1 className="t-display mt-2">Onde você quer entrar?</h1>
              <p className="t-body mt-2">Escolha uma área para começar.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
              <button
                type="button"
                onClick={() => onChoose('vitrine')}
                className="card group text-left p-6 sm:p-8 min-h-[220px] sm:min-h-[260px] flex flex-col justify-between hover:-translate-y-0.5 hover:shadow-apple-lg transition-all"
              >
                <div className="w-12 h-12 rounded-2xl bg-[#0E0937] text-white flex items-center justify-center">
                  <Icons.LayoutGrid className="w-6 h-6" />
                </div>
                <div className="mt-8">
                  <h2 className="text-[28px] sm:text-[32px] leading-none font-extrabold tracking-[-0.03em] text-[#1d1d1f]">Vitrine</h2>
                  <p className="t-body mt-3">Operação da loja, padrão, produção, perdas e histórico.</p>
                  <span className="inline-flex items-center gap-1.5 mt-5 text-[13px] font-bold text-[#0E0937]">
                    Entrar na Vitrine <Icons.ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
                  </span>
                </div>
              </button>

              <button
                type="button"
                onClick={() => onChoose('cmv')}
                className="card group text-left p-6 sm:p-8 min-h-[220px] sm:min-h-[260px] flex flex-col justify-between hover:-translate-y-0.5 hover:shadow-apple-lg transition-all"
              >
                <div className="w-12 h-12 rounded-2xl bg-[#274133] text-white flex items-center justify-center">
                  <Icons.TrendingUp className="w-6 h-6" />
                </div>
                <div className="mt-8">
                  <h2 className="text-[28px] sm:text-[32px] leading-none font-extrabold tracking-[-0.03em] text-[#1d1d1f]">CMV</h2>
                  <p className="t-body mt-3">Produtos, insumos, fichas técnicas, custos e fornecedores.</p>
                  <span className="inline-flex items-center gap-1.5 mt-5 text-[13px] font-bold text-[#274133]">
                    Entrar no CMV <Icons.ChevronRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5" />
                  </span>
                </div>
              </button>
            </div>
          </div>
        </div>
      );

      // ==========================================
      // MAIN APP COMPONENT
      // ==========================================
      function App() {'''
text = text.replace(marker, gateway, 1)

# State for gateway
old_state = """        const [currentUnit, setCurrentUnit] = useState('');
        const [activeTab, setActiveTab] = useState('vitrine');"""
new_state = """        const [currentUnit, setCurrentUnit] = useState('');
        const [entryMode, setEntryMode] = useState(null);
        const [activeTab, setActiveTab] = useState('vitrine');"""
if old_state not in text:
    raise SystemExit('app state marker not found')
text = text.replace(old_state, new_state, 1)

# Gateway before main app content after load/error states
old_return = """        if (loadState === 'loading') return <LoadingScreen />;
        if (loadState === 'error') return <ConnectionErrorScreen message={errorMsg} onRetry={() => { setLoadState('loading'); reload(); }} />;

        return (
          <div className=\"min-h-screen flex flex-col font-sans\">"""
new_return = """        if (loadState === 'loading') return <LoadingScreen />;
        if (loadState === 'error') return <ConnectionErrorScreen message={errorMsg} onRetry={() => { setLoadState('loading'); reload(); }} />;

        if (!entryMode) {
          return (
            <EntryScreen
              onChoose={(mode) => {
                setEntryMode(mode);
                setActiveTab(mode === 'cmv' ? 'cmv' : 'vitrine');
              }}
            />
          );
        }

        return (
          <div className=\"min-h-screen flex flex-col font-sans\">"""
if old_return not in text:
    raise SystemExit('app return marker not found')
text = text.replace(old_return, new_return, 1)

# Navbar receives onHome
old_sig = "const Navbar = ({ units, currentUnit, onUnitChange, activeTab, onTabChange, totalAlerts }) => {"
new_sig = "const Navbar = ({ units, currentUnit, onUnitChange, activeTab, onTabChange, totalAlerts, onHome }) => {"
if old_sig not in text:
    raise SystemExit('navbar signature marker not found')
text = text.replace(old_sig, new_sig, 1)

# Add Home button after brand block, before divider
old_brand_end = """                  </div>

                  <div className=\"h-5 w-px bg-black/10 hidden sm:block\" />

                  {/* As unidades vêm da tabela units do Supabase */}"""
new_brand_end = """                  </div>

                  <button
                    type=\"button\"
                    onClick={onHome}
                    title=\"Voltar à tela inicial\"
                    className=\"btn btn-secondary btn-sm shrink-0\"
                  >
                    <Icons.ChevronLeft className=\"w-3.5 h-3.5\" />
                    <span className=\"hidden sm:inline\">Início</span>
                  </button>

                  <div className=\"h-5 w-px bg-black/10 hidden sm:block\" />

                  {/* As unidades vêm da tabela units do Supabase */}"""
if old_brand_end not in text:
    raise SystemExit('navbar brand marker not found')
text = text.replace(old_brand_end, new_brand_end, 1)

# Pass callback into Navbar
old_nav_props = """              activeTab={activeTab}
              onTabChange={setActiveTab}
              totalAlerts={totalAlerts}
            />"""
new_nav_props = """              activeTab={activeTab}
              onTabChange={setActiveTab}
              totalAlerts={totalAlerts}
              onHome={() => setEntryMode(null)}
            />"""
if old_nav_props not in text:
    raise SystemExit('navbar props marker not found')
text = text.replace(old_nav_props, new_nav_props, 1)

if text == original:
    raise SystemExit('no changes')
p.write_text(text, encoding='utf-8')
