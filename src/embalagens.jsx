/* Controle Produ — fichas de embalagem com regras por produto (React + Supabase).
   Dados canônicos: Produção (products) e embalagens do cadastro (supplies). */
(function () {
  const { useState, useEffect, useMemo, useRef } = React;
  const idNovo = () => window.crypto && window.crypto.randomUUID
    ? window.crypto.randomUUID()
    : String(Date.now()) + Math.random().toString(36).slice(2);
  const intPositivo = (valor) => {
    const n = Number(valor);
    return Number.isFinite(n) ? Math.max(1, Math.floor(n)) : 1;
  };
  const numero = (valor) => Math.max(0, Math.floor(Number(valor) || 0));
  const normalTexto = (txt) => String(txt || '').trim().toLocaleLowerCase('pt-BR');
  const esc = (v) => String(v == null ? '' : v).replace(/[&<>"']/g,
    (a) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[a]));
  const imagemValida = (s) => typeof s === 'string' && s.length < 300000 &&
    /^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(s) ? s : '';
  const nomeArquivo = (s) => String(s || 'fichas-embalagem').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9-]+/g, '-')
    .replace(/^-+|-+$/g, '').slice(0,60);
  const baixar = (nome, dados, tipo) => {
    const url = URL.createObjectURL(new Blob([dados], { type: tipo }));
    const a = document.createElement('a');
    a.href = url;
    a.download = nome;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1400);
  };
  const fotoComprimida = async (arq) => {
    if (!arq || !['image/jpeg', 'image/png', 'image/webp'].includes(arq.type)) {
      throw Error('Envie uma foto em JPG, PNG ou WEBP.');
    }
    if (arq.size > 8 * 1024 * 1024) throw Error('A foto precisa ter até 8 MB.');
    const url = URL.createObjectURL(arq);
    try {
      const foto = new Image();
      foto.src = url;
      await foto.decode();
      const escala = Math.min(1, 320 / Math.max(foto.naturalWidth, foto.naturalHeight));
      const c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(foto.naturalWidth * escala));
      c.height = Math.max(1, Math.round(foto.naturalHeight * escala));
      const ctx = c.getContext('2d');
      if (!ctx) throw Error('Não foi possível preparar a foto.');
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, c.width, c.height);
      ctx.drawImage(foto, 0, 0, c.width, c.height);
      let img = c.toDataURL('image/jpeg', .58);
      if (img.length > 45000) img = c.toDataURL('image/jpeg', .35);
      if (img.length > 45000) img = c.toDataURL('image/jpeg', .22);
      if (img.length > 45000) throw Error('Foto muito grande. Escolha uma imagem mais simples.');
      return img;
    } finally { URL.revokeObjectURL(url); }
  };
  const gruposNomes = {
    salgado: 'Salgados', doce: 'Doces e sobremesas',
    sobremesa: 'Doces e sobremesas', cafeteria: 'Cafeteria',
    pao: 'Pães', bebida_revenda: 'Bebidas',
    bomboniere: 'Bomboniere', outro: 'Outros'
  };
  const grupoDe = (cat) => gruposNomes[normalTexto(cat)] || (
    cat ? String(cat).charAt(0).toUpperCase() + String(cat).slice(1) : 'Outros'
  );
  const ordemGrupo = ['Salgados', 'Doces e sobremesas', 'Pães', 'Cafeteria', 'Bebidas', 'Bomboniere', 'Outros'];
  const regraNova = (inicial = false) => ({
    id: idNovo(), operador: inicial ? 'igual' : 'mais_de',
    quantidade: inicial ? 1 : 3, itens: []
  });
  const lerItens = (origem) => {
    if (!Array.isArray(origem)) return [];
    const ids = new Set();
    return origem.slice(0, 80).filter((x) => {
      const key = String(x && x.embalagemId || '');
      if (!key || ids.has(key) || numero(x.quantidade) < 1) return false;
      ids.add(key);
      return true;
    }).map((x) => ({ embalagemId: String(x.embalagemId), quantidade: intPositivo(x.quantidade) }));
  };
  const regraNormal = (x) => ({
    id: String(x.id || idNovo()),
    operador: ['igual', 'mais_de', 'a_partir', 'texto'].includes(x.operador) ? x.operador : 'igual',
    quantidade: intPositivo(x.quantidade),
    rotulo: String(x.rotulo || '').slice(0, 90),
    itens: lerItens(x.itens)
  });
  const textoRegra = (r) => {
    if (r.operador === 'texto') return r.rotulo || 'Outra quantidade';
    const q = intPositivo(r.quantidade);
    if (r.operador === 'igual') return q + (q === 1 ? ' unidade' : ' unidades');
    return (r.operador === 'a_partir' ? 'A partir de ' : 'Mais de ') + q + (q === 1 ? ' unidade' : ' unidades');
  };
  const lerLayout = (bruto) => {
    const x = bruto && typeof bruto === 'object' && !Array.isArray(bruto) ? bruto : {};
    const fotos = Array.isArray(x.embalagens) ? x.embalagens.slice(0, 100)
      .filter((e) => e && e.id)
      .map((e) => ({ id: String(e.id), nome: String(e.nome || ''), foto: imagemValida(e.foto) })) : [];
    const faixasAntigas = Array.isArray(x.faixas) ? x.faixas : [];
    const linhas = (Array.isArray(x.linhas) ? x.linhas : []).slice(0, 500)
      .filter((linha) => linha && linha.id).map((linha) => {
        let variacoes = [];
        if (Array.isArray(linha.variacoes)) {
          variacoes = linha.variacoes.slice(0, 30).map(regraNormal);
        } else if (linha.celulas && typeof linha.celulas === 'object') {
          variacoes = faixasAntigas.map((faixa) => {
            const itens = lerItens(linha.celulas[faixa.id]);
            if (!itens.length) return null;
            const rotulo = String(faixa.rotulo || '').trim();
            const numeroMatch = rotulo.match(/\d+/);
            const q = numeroMatch ? intPositivo(numeroMatch[0]) : 1;
            const op = /^mais\s+de/i.test(rotulo) && numeroMatch ? 'mais_de'
              : /^a\s+partir/i.test(rotulo) && numeroMatch ? 'a_partir'
              : /^\d+\s+un/i.test(rotulo) ? 'igual' : 'texto';
            return { id: String(faixa.id || idNovo()), operador: op, quantidade: q,
              rotulo: op === 'texto' ? rotulo : '', itens };
          }).filter(Boolean);
        } else if (linha.alocacoes && typeof linha.alocacoes === 'object') {
          const itens = lerItens(Object.entries(linha.alocacoes)
            .map(([embalagemId, quantidade]) => ({ embalagemId, quantidade })));
          if (itens.length) variacoes = [{ ...regraNova(true), quantidade: intPositivo(linha.quantidade), itens }];
        }
        return { id: String(linha.id), productId: String(linha.productId || ''),
          produto: String(linha.produto || ''), variacoes };
      });
    return { titulo: String(x.titulo || 'Guia de embalagens por produto'), embalagens: fotos, linhas };
  };

  const PackagingMatrixView = ({ sb, currentUnit, unitName, products = [], supplies = [] }) => {
    const [titulo, setTitulo] = useState('Guia de embalagens por produto');
    const [fotos, setFotos] = useState([]);
    const [linhas, setLinhas] = useState([]);
    const [carregada, setCarregada] = useState('');
    const [situacao, setSituacao] = useState('Carregando…');
    const [erro, setErro] = useState('');
    const [busca, setBusca] = useState('');
    const [buscaEmbalagem, setBuscaEmbalagem] = useState('');
    const [buscarNaCelula, setBuscarNaCelula] = useState('');
    const [mostrarInativos, setMostrarInativos] = useState(false);
    const [mostrarFotos, setMostrarFotos] = useState(false);
    const [grupoAberto, setGrupoAberto] = useState({ 'Salgados': true, 'Doces e sobremesas': true });
    const [produtoAberto, setProdutoAberto] = useState({});
    const [selecionando, setSelecionando] = useState(null);
    const [uploadEmCurso, setUploadEmCurso] = useState('');
    const leituraSeq = useRef(0);
    const fila = useRef(Promise.resolve());
    const salvoJson = useRef('');
    const unidadeVigente = useRef(currentUnit);
    unidadeVigente.current = currentUnit;

    const embalagens = useMemo(() => {
      const imagens = new Map(fotos.map((e) => [e.id, e.foto]));
      const existentes = supplies.filter((s) => s && s.id &&
        normalTexto(s.supplyClass) === 'embalagem').map((s) => ({
        id: String(s.id), nome: String(s.name || 'Embalagem'),
        foto: imagemValida(imagens.get(String(s.id)))
      }));
      const ids = new Set(existentes.map((e) => e.id));
      return [...existentes, ...fotos.filter((e) => !ids.has(e.id))]
        .sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
    }, [supplies, fotos]);
    const indiceEmbalagem = useMemo(() => new Map(embalagens.map((x) => [x.id, x])), [embalagens]);
    const fotosListadas = useMemo(() => {
      const filtro = normalTexto(buscaEmbalagem);
      return embalagens.filter((item) => !filtro || normalTexto(item.nome).includes(filtro));
    }, [embalagens, buscaEmbalagem]);
    const produtosVisiveis = useMemo(() => products.filter((p) =>
      p && p.id && p.name && (mostrarInativos || p.showcaseEnabled !== false))
      .sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')), [products, mostrarInativos]);
    const linhasCatalogo = useMemo(() => {
      const ids = new Map(linhas.filter((l) => l.productId).map((l) => [l.productId, l]));
      const nomes = new Map(linhas.filter((l) => !l.productId)
        .map((l) => [normalTexto(l.produto), l]));
      const usadas = new Set();
      const normais = produtosVisiveis.map((p) => {
        const antiga = ids.get(String(p.id)) || nomes.get(normalTexto(p.name));
        if (antiga) usadas.add(antiga.id);
        return antiga
          ? { ...antiga, productId: String(p.id), produto: p.name, grupo: grupoDe(p.category) }
          : { id: 'produto-' + p.id, productId: String(p.id), produto: p.name,
            variacoes: [], grupo: grupoDe(p.category) };
      });
      const legadas = linhas.filter((l) => !usadas.has(l.id) && (!l.productId ||
        !products.some((p) => String(p.id) === l.productId)))
        .map((l) => ({ ...l, grupo: 'Outros' }));
      return [...normais, ...legadas];
    }, [linhas, products, produtosVisiveis]);
    const grupos = useMemo(() => {
      const filtro = normalTexto(busca);
      const itens = linhasCatalogo.filter((l) => !filtro || normalTexto(l.produto).includes(filtro));
      const m = new Map();
      itens.forEach((l) => {
        const nome = l.grupo || 'Outros';
        if (!m.has(nome)) m.set(nome, []);
        m.get(nome).push(l);
      });
      return [...m.entries()].sort(([a], [b]) => {
        const na = ordemGrupo.indexOf(a), nb = ordemGrupo.indexOf(b);
        return (na < 0 ? 999 : na) - (nb < 0 ? 999 : nb) || a.localeCompare(b, 'pt-BR');
      }).map(([nome, lista]) => ({ nome, lista }));
    }, [linhasCatalogo, busca]);
    const configurados = (l) => l.variacoes.filter((v) => v.itens.some((e) => numero(e.quantidade) > 0)).length;

    useEffect(() => {
      const seq = ++leituraSeq.current;
      setCarregada('');
      setSituacao('Carregando…');
      setErro('');
      setSelecionando(null);
      if (!sb || !currentUnit) {
        setErro('Falha de conexão com o Supabase.');
        return;
      }
      sb.from('packaging_matrices').select('layout').eq('unit_code', currentUnit).maybeSingle()
        .then(({ data, error }) => {
          if (seq !== leituraSeq.current) return;
          if (error) throw error;
          const registro = lerLayout(data ? data.layout : null);
          setTitulo(registro.titulo);
          setFotos(registro.embalagens);
          setLinhas(registro.linhas);
          salvoJson.current = JSON.stringify(registro);
          setCarregada(currentUnit);
          setSituacao(data ? 'Salvo no Supabase' : 'Novo guia');
        }).catch((e) => {
          if (seq !== leituraSeq.current) return;
          setSituacao('Erro ao carregar');
          setErro(e.message);
        });
      return () => { leituraSeq.current++; };
    }, [sb, currentUnit]);

    const layout = useMemo(() => ({ titulo, embalagens: fotos, linhas }), [titulo, fotos, linhas]);
    const json = useMemo(() => JSON.stringify(layout), [layout]);
    useEffect(() => {
      if (!sb || carregada !== currentUnit || salvoJson.current === json) return;
      setSituacao('Alterações pendentes…');
      const timer = setTimeout(() => {
        setSituacao('Salvando…');
        const unidadeGravada = currentUnit;
        const dados = { unit_code: unidadeGravada, layout, updated_at: new Date().toISOString() };
        const p = fila.current.then(async () => {
          const { error } = await sb.from('packaging_matrices').upsert(dados, { onConflict: 'unit_code' });
          if (error) throw error;
        });
        fila.current = p.catch(() => {});
        p.then(() => {
          if (unidadeVigente.current !== unidadeGravada) return;
          salvoJson.current = json;
          setSituacao('Salvo no Supabase');
          setErro('');
        }).catch((e) => {
          if (unidadeVigente.current !== unidadeGravada) return;
          setSituacao('Erro ao salvar');
          setErro(e.message);
        });
      }, 650);
      return () => clearTimeout(timer);
    }, [json, sb, currentUnit, carregada]);

    const atualizarLinha = (id, editar) => {
      const original = linhasCatalogo.find((l) => l.id === id);
      if (!original) return;
      setLinhas((prev) => {
        const existente = prev.some((l) => l.id === id);
        const base = existente ? prev : [...prev, { id: original.id,
          productId: original.productId, produto: original.produto, variacoes: original.variacoes }];
        return base.map((l) => l.id === id ? editar(l) : l);
      });
    };
    const atualizarVariacao = (id, varId, editar) => atualizarLinha(id, (l) => ({
      ...l, variacoes: l.variacoes.map((v) => v.id === varId ? editar(v) : v)
    }));
    const abrirProduto = (linha) => {
      const aberto = !!produtoAberto[linha.id];
      setProdutoAberto((prev) => ({ ...prev, [linha.id]: !aberto }));
      if (!aberto && !linha.variacoes.length) {
        atualizarLinha(linha.id, (l) => ({ ...l, variacoes: [regraNova(true)] }));
      }
    };
    const adicionarVariacao = (linha) => {
      atualizarLinha(linha.id, (l) => {
        const maior = l.variacoes.reduce((m, v) => Math.max(m, intPositivo(v.quantidade)), 2);
        return { ...l, variacoes: [...l.variacoes, { ...regraNova(false), quantidade: Math.max(3, maior + 1) }] };
      });
      setProdutoAberto((prev) => ({ ...prev, [linha.id]: true }));
      setSelecionando(null);
    };
    const excluirVariacao = (linha, varId) => {
      if (!window.confirm('Excluir esta variação e as embalagens associadas?')) return;
      atualizarLinha(linha.id, (l) => ({ ...l, variacoes: l.variacoes.filter((v) => v.id !== varId) }));
      setSelecionando(null);
    };
    const adicionarItem = (linhaId, varId, embalagemId) => {
      atualizarVariacao(linhaId, varId, (v) => v.itens.some((x) => x.embalagemId === embalagemId) ? v :
        { ...v, itens: [...v.itens, { embalagemId, quantidade: 1 }] });
    };
    const quantidadeItem = (linhaId, varId, embalagemId, n) =>
      atualizarVariacao(linhaId, varId, (v) => ({ ...v, itens: v.itens.map((x) =>
        x.embalagemId === embalagemId ? { ...x, quantidade: intPositivo(n) } : x) }));
    const removerItem = (linhaId, varId, embalagemId) =>
      atualizarVariacao(linhaId, varId, (v) => ({
        ...v, itens: v.itens.filter((x) => x.embalagemId !== embalagemId)
      }));
    const uploadFoto = async (id, arq) => {
      if (!arq) return;
      setUploadEmCurso(id);
      try {
        const foto = await fotoComprimida(arq);
        const item = embalagens.find((e) => e.id === id);
        setFotos((prev) => prev.some((e) => e.id === id)
          ? prev.map((e) => e.id === id ? { ...e, foto } : e)
          : [...prev, { id, nome: item ? item.nome : 'Embalagem', foto }]);
        setErro('');
      } catch (e) { setErro(e.message); }
      finally { setUploadEmCurso(''); }
    };
    const removerFoto = (id) => setFotos((prev) => prev.filter((e) => e.id !== id));
    useEffect(() => {
      if (!selecionando) return;
      const anterior = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      const fechar = (e) => { if (e.key === 'Escape') setSelecionando(null); };
      window.addEventListener('keydown', fechar);
      return () => {
        document.body.style.overflow = anterior;
        window.removeEventListener('keydown', fechar);
      };
    }, [selecionando]);

    const descricaoItens = (v) => v.itens.filter((item) => indiceEmbalagem.has(item.embalagemId))
      .map((item) => item.quantidade + ' × ' + indiceEmbalagem.get(item.embalagemId).nome).join(' + ');

    const exportarCSV = () => {
      const temFicha = linhasCatalogo.filter((l) => l.variacoes.some((v) => v.itens.length));
      if (!temFicha.length) return window.alert('Preencha ao menos uma ficha antes de baixar.');
      const r = [
        [titulo], ['Unidade', unitName], ['Data', new Date().toLocaleDateString('pt-BR')],
        [], ['Grupo', 'Produto', 'Variação', 'Embalagens'],
        ...temFicha.flatMap((l) => l.variacoes.filter((v) => v.itens.length)
          .map((v) => [l.grupo, l.produto, textoRegra(v), descricaoItens(v)]))
      ];
      const fmt = (v) => {
        let t = String(v == null ? '' : v);
        if (/^\s*[=+\-@]/.test(t)) t = "'" + t;
        return '"' + t.replace(/"/g, '""') + '"';
      };
      baixar(nomeArquivo(titulo) + '.csv', '\uFEFF' + r.map((x) => x.map(fmt).join(';')).join('\r\n'),
        'text/csv;charset=utf-8;');
    };
    const imprimir = () => {
      const lista = linhasCatalogo.filter((l) => l.variacoes.some((v) => v.itens.length));
      if (!lista.length) return window.alert('Preencha ao menos uma ficha para imprimir.');
      const win = window.open('', '_blank');
      if (!win) return window.alert('Autorize a janela de impressão.');
      const itensHTML = (v) => v.itens.map((item) => {
        const emb = indiceEmbalagem.get(item.embalagemId);
        if (!emb) return '';
        return '<div class="item">' +
          (imagemValida(emb.foto) ? '<img alt="" src="' + emb.foto + '">' : '') +
          '<b>' + numero(item.quantidade) + ' × ' + esc(emb.nome) + '</b></div>';
      }).join('');
      const body = lista.flatMap((l) => l.variacoes.filter((v) => v.itens.length)
        .map((v) => '<tr><td>' + esc(l.grupo) + '</td><td><b>' + esc(l.produto) +
          '</b></td><td>' + esc(textoRegra(v)) + '</td><td>' + itensHTML(v) + '</td></tr>')).join('');
      const html = '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>' +
        esc(titulo) + '</title><style>@page{size:A4 landscape;margin:12mm}' +
        'body{font:12px Arial;color:#2a4934}.btn{display:block;text-align:right;margin-bottom:15px}' +
        'button{background:#285b3e;color:#fff;padding:10px 15px;border:0;border-radius:6px}' +
        'header{border-bottom:2px solid #2b6447;padding-bottom:12px;margin-bottom:14px}' +
        'h1{font-size:22px;margin:0 0 6px}header p{color:#7b8c80;margin:0}' +
        'table{width:100%;border-collapse:collapse}th,td{text-align:left;vertical-align:top;' +
        'border:1px solid #d9e5dd;padding:9px}th{background:#eaf2ec}tr:nth-child(even){background:#fafcfa}' +
        '.item{display:inline-flex;gap:6px;align-items:center;margin:3px 10px 3px 0;vertical-align:middle}' +
        '.item img{width:38px;height:38px;object-fit:contain;border:1px solid #e2e9e3;border-radius:4px}' +
        '@media print{.btn{display:none}tr{break-inside:avoid}thead{display:table-header-group}}' +
        '</style></head><body><div class="btn"><button onclick="window.print()">Imprimir / Salvar PDF</button></div>' +
        '<header><h1>' + esc(titulo) + '</h1><p>' + esc(unitName) + ' · ' +
        new Date().toLocaleDateString('pt-BR') + '</p></header>' +
        '<table><thead><tr><th>Grupo</th><th>Produto</th><th>Quantidade</th><th>Embalagens</th></tr>' +
        '</thead><tbody>' + body + '</tbody></table></body></html>';
      win.document.open();
      win.document.write(html);
      win.document.close();
      win.focus();
    };

    const linhaSelecionada = selecionando ? linhasCatalogo.find((l) => l.id === selecionando.linha) : null;
    const regraSelecionada = linhaSelecionada && linhaSelecionada.variacoes.find((v) => v.id === selecionando.variacao);
    const jaSelecionadas = new Set(regraSelecionada ? regraSelecionada.itens.map((item) => item.embalagemId) : []);
    const opcoesFiltradas = embalagens.filter((e) => normalTexto(e.nome).includes(normalTexto(buscarNaCelula)));

    if (carregada !== currentUnit) return <section className="emb-area">
      <h1>Guia de embalagens</h1>
      <p>{erro || 'Carregando cadastros e regras do Supabase…'}</p>
      {erro && <button type="button" className="btn btn-secondary"
        onClick={() => window.location.reload()}>Tentar novamente</button>}
    </section>;

    return <section className="emb-area emb2-area">
      <div className="emb-cabecalho">
        <div>
          <div className="emb-sobretitulo">Controle de embalagens · {unitName}</div>
          <h1>Guia de embalagens por produto</h1>
          <p>Abra um produto, crie as variações de quantidade e monte as embalagens de cada situação.</p>
        </div>
        <div className="emb-acoes">
          <button type="button" className="btn btn-secondary btn-sm" onClick={exportarCSV}>Baixar Excel (CSV)</button>
          <button type="button" className="btn btn-primary btn-sm" onClick={imprimir}>Imprimir / Salvar PDF</button>
        </div>
      </div>
      <div className="emb-status" role="status">{situacao}{erro && <span className="emb-erro"> — {erro}</span>}</div>

      <div className="emb2-intro">
        <div className="emb2-passos">
          <div><b>1.</b> Escolha um grupo e abra o produto</div>
          <div><b>2.</b> Adicione uma variação, como “Mais de 3”</div>
          <div><b>3.</b> Selecione saquinhos, bandejas e outras embalagens com foto</div>
        </div>
        <button type="button" className="emb2-galeria-toggle"
          onClick={() => setMostrarFotos((prev) => !prev)}>
          <span> <strong>Catálogo de embalagens</strong><small>{embalagens.length} cadastradas · {fotos.filter((e) => e.foto).length} com fotos</small></span>
          <span>{mostrarFotos ? 'Ocultar fotos  −' : 'Ver / enviar fotos  +'}</span>
        </button>
        {mostrarFotos && <div className="emb2-galeria">
          <div className="emb2-galeria-topo">
            <input className="field field-md" value={buscaEmbalagem}
              placeholder="Buscar embalagem para adicionar foto…"
              onChange={(e) => setBuscaEmbalagem(e.target.value)}/>
            <span>As fotos ficam vinculadas ao cadastro existente, sem duplicá-lo.</span>
          </div>
          <div className="emb2-fotos-grid">
            {fotosListadas.map((e) => <div className="emb2-foto-card" key={e.id}>
              <div className="emb2-foto-capa">
                {e.foto ? <img src={imagemValida(e.foto)} alt={e.nome}/>
                  : <span>Sem foto</span>}
              </div>
              <div className="emb2-foto-nome" title={e.nome}>{e.nome}</div>
              <label className="emb2-upload">
                {e.foto ? 'Trocar foto' : '+ Enviar foto'}
                <input type="file" accept="image/jpeg,image/png,image/webp"
                  onChange={(event) => {
                    uploadFoto(e.id, event.target.files && event.target.files[0]);
                    event.target.value = '';
                  }}/>
              </label>
              {e.foto && <button type="button" className="emb2-remover-foto"
                onClick={() => removerFoto(e.id)}>Remover foto</button>}
            </div>)}
            {!fotosListadas.length && <p>Nenhuma embalagem encontrada.</p>}
          </div>
        </div>}
      </div>

      <div className="emb2-toolbar">
        <div className="emb2-busca">
          <span aria-hidden="true">⌕</span>
          <input value={busca} onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar produto da Produção…" aria-label="Buscar produto"/>
        </div>
        <label className="emb-mostrar-inativos">
          <input type="checkbox" checked={mostrarInativos}
            onChange={(e) => setMostrarInativos(e.target.checked)}/>
          Mostrar inativos
        </label>
        <span className="emb2-contagem">{produtosVisiveis.length} produtos · {grupos.length} grupos</span>
      </div>

      <div className="emb2-grupos">
        {grupos.map((grupo) => {
          const aberto = !!grupoAberto[grupo.nome] || !!busca.trim();
          const prontos = grupo.lista.filter((l) => configurados(l) > 0).length;
          return <section className="emb2-grupo" key={grupo.nome}>
            <button type="button" className="emb2-grupo-header"
              aria-expanded={aberto}
              onClick={() => setGrupoAberto((old) => ({ ...old, [grupo.nome]: !old[grupo.nome] }))}>
              <span className="emb2-chevron">{aberto ? '⌄' : '›'}</span>
              <strong>{grupo.nome}</strong>
              <span className="emb2-num-produtos">{grupo.lista.length} produtos</span>
              <span className="emb2-prontos">{prontos} configurados</span>
            </button>
            {aberto && <div className="emb2-produtos">
              {grupo.lista.map((linha) => {
                const expandido = !!produtoAberto[linha.id];
                return <div key={linha.id} className={'emb2-produto ' + (expandido ? 'emb2-produto-aberto' : '')}>
                  <div className="emb2-produto-linha">
                    <button type="button" className="emb2-produto-titulo" aria-expanded={expandido}
                      onClick={() => abrirProduto(linha)}>
                      <span className="emb2-chevron">{expandido ? '⌄' : '›'}</span>
                      <strong>{linha.produto}</strong>
                    </button>
                    <div className="emb2-mini-variacoes">
                      {linha.variacoes.filter((v) => v.itens.length).map((v) =>
                        <span key={v.id} className="emb2-mini-chip" title={descricaoItens(v)}>
                          {textoRegra(v)} · {v.itens.length} {v.itens.length === 1 ? 'embalagem' : 'embalagens'}
                        </span>)}
                      {!configurados(linha) && <span className="emb2-sem-regra">Sem embalagem definida</span>}
                    </div>
                    <button type="button" className="emb2-btn-nova" onClick={() => adicionarVariacao(linha)}>
                      + Variação
                    </button>
                  </div>
                  {expandido && <div className="emb2-produto-detalhe">
                    <div className="emb2-detalhe-topo">
                      <span>Embalagens conforme a quantidade do pedido</span>
                      <button type="button" onClick={() => adicionarVariacao(linha)}>+ Adicionar outra quantidade</button>
                    </div>
                    <div className="emb2-variacoes">
                      {linha.variacoes.map((variante, indice) => {
                        const ativa = !!selecionando && selecionando.linha === linha.id && selecionando.variacao === variante.id;
                        return <div key={variante.id} className="emb2-var-card">
                          <div className="emb2-var-topo">
                            <span className="emb2-var-numero">{indice + 1}</span>
                            <div className="emb2-regra-campos">
                              <label>
                                <span>Quando o pedido tiver</span>
                                <select value={variante.operador} onChange={(e) =>
                                  atualizarVariacao(linha.id, variante.id, (v) => ({ ...v, operador: e.target.value }))}>
                                  <option value="igual">Exatamente</option>
                                  <option value="mais_de">Mais de</option>
                                  <option value="a_partir">A partir de</option>
                                  <option value="texto">Descrição personalizada</option>
                                </select>
                              </label>
                              {variante.operador === 'texto'
                                ? <label className="emb2-regra-personalizada"><span>Descrição</span>
                                    <input value={variante.rotulo || ''} maxLength={90}
                                      placeholder="Ex.: Caixa presente"
                                      onChange={(e) => atualizarVariacao(linha.id, variante.id,
                                        (v) => ({ ...v, rotulo: e.target.value }))}/>
                                  </label>
                                : <label className="emb2-regra-quantidade">
                                    <span>Quantidade</span>
                                    <input type="number" min="1" step="1" value={variante.quantidade}
                                      onChange={(e) => atualizarVariacao(linha.id, variante.id,
                                        (v) => ({ ...v, quantidade: e.target.value === '' ? '' : intPositivo(e.target.value) }))}/>
                                    <em>un.</em>
                                  </label>}
                            </div>
                            <button className="emb2-var-excluir" type="button"
                              title="Excluir variação" onClick={() => excluirVariacao(linha, variante.id)}>×</button>
                          </div>
                          <div className="emb2-var-corpo">
                            <div className="emb2-var-subtitulo">EMBALAGENS PARA {textoRegra(variante).toUpperCase()}</div>
                            <div className="emb2-itens">
                              {variante.itens.map((item) => {
                                const emb = indiceEmbalagem.get(item.embalagemId);
                                if (!emb) return null;
                                return <div className="emb2-item" key={item.embalagemId}>
                                  <div className="emb2-item-foto">
                                    {emb.foto ? <img src={imagemValida(emb.foto)} alt={emb.nome}/> :
                                      <span>Sem foto</span>}
                                  </div>
                                  <div className="emb2-item-info">
                                    <strong>{emb.nome}</strong>
                                    <div className="emb2-qtd-comandos">
                                      <span>Usar</span>
                                      <button type="button" aria-label={'Diminuir ' + emb.nome}
                                        onClick={() => quantidadeItem(linha.id, variante.id, emb.id,
                                          Math.max(1, numero(item.quantidade) - 1))}>−</button>
                                      <input type="number" min="1" value={item.quantidade}
                                        aria-label={'Quantidade de ' + emb.nome}
                                        onChange={(e) => quantidadeItem(linha.id, variante.id, emb.id, e.target.value)}/>
                                      <button type="button" aria-label={'Aumentar ' + emb.nome}
                                        onClick={() => quantidadeItem(linha.id, variante.id, emb.id,
                                          numero(item.quantidade) + 1)}>+</button>
                                      <span>unidade(s)</span>
                                    </div>
                                  </div>
                                  <button type="button" className="emb2-item-excluir"
                                    aria-label={'Remover ' + emb.nome}
                                    onClick={() => removerItem(linha.id, variante.id, emb.id)}>×</button>
                                </div>;
                              })}
                              {!variante.itens.length && <div className="emb2-var-vazia">
                                Nenhuma embalagem escolhida. Adicione uma ou mais abaixo.
                              </div>}
                            </div>
                            <button type="button" className="emb2-botao-escolher"
                              disabled={variante.itens.length >= embalagens.length}
                              onClick={() => {
                                setSelecionando(ativa ? null : { linha: linha.id, variacao: variante.id });
                                setBuscarNaCelula('');
                              }}>
                              {ativa ? 'Fechar seleção' : '+ Escolher embalagem por foto'}
                            </button>
                          </div>
                        </div>;
                      })}
                    </div>
                    {!linha.variacoes.length && <div className="emb2-sem-variacao">
                      Nenhuma variação criada. Clique em “+ Adicionar outra quantidade”.
                    </div>}
                  </div>}
                </div>;
              })}
            </div>}
          </section>;
        })}
        {!grupos.length && <div className="emb2-nenhum">Nenhum produto encontrado na Produção.</div>}
      </div>
      {regraSelecionada && ReactDOM.createPortal(
        <div className="emb2-modal-overlay" role="presentation">
          <button type="button" className="emb2-modal-fundo" aria-label="Fechar escolha de embalagens"
            onClick={() => setSelecionando(null)}/>
          <div className="emb2-modal" role="dialog" aria-modal="true"
            aria-label={'Selecionar embalagens para ' + linhaSelecionada.produto}>
            <div className="emb2-modal-cabecalho">
              <div>
                <strong>Escolher embalagens</strong>
                <span>{linhaSelecionada.produto} · {textoRegra(regraSelecionada)}</span>
              </div>
              <button type="button" className="emb2-modal-fechar" aria-label="Fechar seleção"
                onClick={() => setSelecionando(null)}>×</button>
            </div>
            <div className="emb2-modal-busca">
              <input className="emb2-picker-busca" value={buscarNaCelula}
                placeholder="Buscar bandeja, saco, caixa…"
                onChange={(e) => setBuscarNaCelula(e.target.value)}
                aria-label="Buscar embalagens cadastradas"/>
              <span>{regraSelecionada.itens.length} selecionada(s)</span>
            </div>
            <div className="emb2-modal-conteudo">
              <p className="emb2-modal-ajuda">Toque em <b>Usar embalagem</b> para adicioná-la. Para colocar a foto, toque em <b>Enviar foto</b> no próprio cartão.</p>
              <div className="emb2-modal-grid">
                {opcoesFiltradas.map((e) =>
                  <div className={'emb2-modal-cartao ' + (jaSelecionadas.has(e.id) ? 'selecionada' : '')} key={e.id}>
                    <div className="emb2-modal-foto">
                      {e.foto ? <img src={imagemValida(e.foto)} alt={e.nome}/> :
                        <span>Sem foto</span>}
                    </div>
                    <strong title={e.nome}>{e.nome}</strong>
                    <label className="emb2-modal-enviar">
                      {uploadEmCurso === e.id ? 'Preparando foto…' : e.foto ? 'Trocar foto' : 'Enviar foto'}
                      <input type="file" accept="image/jpeg,image/png,image/webp"
                        aria-label={'Enviar foto de ' + e.nome}
                        disabled={uploadEmCurso === e.id}
                        onChange={(event) => {
                          uploadFoto(e.id, event.target.files && event.target.files[0]);
                          event.target.value = '';
                        }}/>
                    </label>
                    <button type="button" className="emb2-modal-usar"
                      disabled={jaSelecionadas.has(e.id)}
                      onClick={() => adicionarItem(linhaSelecionada.id, regraSelecionada.id, e.id)}>
                      {jaSelecionadas.has(e.id) ? '✓ Adicionada' : '+ Usar embalagem'}
                    </button>
                  </div>
                )}
              </div>
              {!opcoesFiltradas.length && <p className="emb2-picker-vazio">Nenhuma embalagem encontrada. Confira o nome no cadastro.</p>}
            </div>
            <div className="emb2-modal-rodape">
              <span>{situacao}{erro ? ' — ' + erro : ''}</span>
              <button type="button" onClick={() => setSelecionando(null)}>Concluir</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </section>;
  };
  window.PackagingMatrixView = PackagingMatrixView;
})();
