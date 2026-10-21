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
    id: idNovo(), operador: inicial ? 'igual' : 'menos_de',
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
    operador: ['igual', 'menos_de', 'mais_de', 'a_partir', 'texto'].includes(x.operador) ? x.operador : 'igual',
    quantidade: intPositivo(x.quantidade),
    rotulo: String(x.rotulo || '').slice(0, 90),
    itens: lerItens(x.itens)
  });
  const textoRegra = (r) => {
    if (r.operador === 'texto') return r.rotulo || 'Outra quantidade';
    const q = intPositivo(r.quantidade);
    if (r.operador === 'igual') return q + (q === 1 ? ' unidade' : ' unidades');
    return (r.operador === 'menos_de' ? 'Menos de ' : r.operador === 'a_partir' ? 'A partir de ' : 'Mais de ') + q + (q === 1 ? ' unidade' : ' unidades');
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
            const op = /^menos\s+de/i.test(rotulo) && numeroMatch ? 'menos_de'
              : /^mais\s+de/i.test(rotulo) && numeroMatch ? 'mais_de'
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

    const [precosEmbalagem, setPrecosEmbalagem] = useState({});
    useEffect(() => {
      let cancelado = false;
      if (!sb || !currentUnit) { setPrecosEmbalagem({}); return; }
      (async () => {
        try {
          const { data, error } = await sb.from('supply_purchases')
            .select('supply_id,purchase_date,qty,cost,purchase_unit,quantity_basis,unit_review_required')
            .order('purchase_date', { ascending: false })
            .limit(10000);
          if (error) throw error;
          const valores = {};
          for (const p of data || []) {
            const id = String(p.supply_id || '');
            if (!id || valores[id] || !(Number(p.qty) > 0) || !(Number(p.cost) > 0)) continue;
            const supply = supplies.find((x) => String(x.id) === id);
            if (!supply || p.quantity_basis === 'review' || p.unit_review_required) continue;
            const base = String(supply.unit || 'un').toLowerCase();
            const unidade = String(p.purchase_unit || supply.purchaseUnit || base).toLowerCase();
            let qtd = Number(p.qty);
            if (p.quantity_basis === 'purchase' && unidade !== base) {
              const equivalencias = supply.unitEquivalences || [];
              const eq = equivalencias.find((e) => String(e.fromUnit).toLowerCase() === unidade
                && String(e.toUnit).toLowerCase() === base && Number(e.factor) > 0);
              const inversa = equivalencias.find((e) => String(e.fromUnit).toLowerCase() === base
                && String(e.toUnit).toLowerCase() === unidade && Number(e.factor) > 0);
              if (eq) qtd *= Number(eq.factor);
              else if (inversa) qtd /= Number(inversa.factor);
              else if (Number(supply.packageUnits) > 0
                && ['cx', 'caixa', 'pct', 'pacote', 'fardo'].includes(unidade) && base === 'un')
                qtd *= Number(supply.packageUnits);
              else if (unidade === 'kg' && base === 'g') qtd *= 1000;
              else if (unidade === 'l' && base === 'ml') qtd *= 1000;
              else continue;
            }
            if (!['un', 'unidade', 'unidades'].includes(base)) continue;
            valores[id] = Number(p.cost) / qtd;
          }
          if (!cancelado) setPrecosEmbalagem(valores);
        } catch (err) {
          if (!cancelado) setPrecosEmbalagem({});
          console.warn('Preços de embalagens indisponíveis:', err);
        }
      })();
      return () => { cancelado = true; };
    }, [sb, currentUnit, supplies]);
    const formatarPrecoEmbalagem = (valor) => Number.isFinite(Number(valor)) && Number(valor) > 0
      ? Number(valor).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2, maximumFractionDigits: 4 }) + '/un'
      : 'Preço não cadastrado';

    const embalagens = useMemo(() => {
      const imagens = new Map(fotos.map((e) => [e.id, e.foto]));
      const existentes = supplies.filter((s) => s && s.id &&
        normalTexto(s.supplyClass) === 'embalagem').map((s) => ({
        id: String(s.id), nome: String(s.name || 'Embalagem'),
        foto: imagemValida(imagens.get(String(s.id))), precoUnitario: precosEmbalagem[String(s.id)] || null
      }));
      const ids = new Set(existentes.map((e) => e.id));
      return [...existentes, ...fotos.filter((e) => !ids.has(e.id))]
        .sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
    }, [supplies, fotos, precosEmbalagem]);
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
    // O HTML da janela incorpora fotos JPEG já guardadas no Supabase. Ao
    // imprimir/salvar como PDF, não depende de links externos de imagens.
    //
    // Manual feito para quem está no balcão: capa com "como usar" em três
    // passos, índice colorido por grupo, e cada produto como um passo a passo
    // visual — quantidade do pedido → embalagens com foto e "×N" em cima.
    // Preço não aparece: o manual é da equipe, o preço fica no sistema.
    const CORES_GRUPO = {
      'Salgados': '#d9733a', 'Doces e sobremesas': '#cc4f86', 'Pães': '#b88a1e',
      'Cafeteria': '#86593b', 'Bebidas': '#2a78d6', 'Bomboniere': '#7451c9', 'Outros': '#4f7a62'
    };
    const corGrupo = (nome) => CORES_GRUPO[nome] || '#4f7a62';
    const ordemVariacao = (v) => {
      const peso = { menos_de: 0, igual: 1, a_partir: 2, mais_de: 3, texto: 9 }[v.operador] ?? 9;
      return v.operador === 'texto' ? 1e9 : intPositivo(v.quantidade) * 10 + peso;
    };
    const etiquetaVariacao = (v) => {
      if (v.operador === 'texto') return '<span class="qtd-texto">' + esc(v.rotulo || 'Outra quantidade') + '</span>';
      const q = intPositivo(v.quantidade);
      const antes = { menos_de: 'menos de', mais_de: 'mais de', a_partir: 'a partir de' }[v.operador] || '';
      return (antes ? '<small>' + antes + '</small>' : '') + '<b>' + q + '</b><small>' +
        (q === 1 ? 'unidade' : 'unidades') + '</small>';
    };
    const ICONES = {
      buscar: '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>',
      contar: '<svg viewBox="0 0 24 24"><rect x="3" y="12" width="7" height="8" rx="1.5"/><rect x="14" y="12" width="7" height="8" rx="1.5"/><rect x="8.5" y="3" width="7" height="8" rx="1.5"/></svg>',
      caixa: '<svg viewBox="0 0 24 24"><path d="M3 8l9-5 9 5v8l-9 5-9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/></svg>',
      seta: '<svg viewBox="0 0 24 24"><path d="M4 12h15M13 6l6 6-6 6"/></svg>'
    };
    const construirManualHTML = (lista) => {
      const data = new Date().toLocaleDateString('pt-BR');
      const agrupadosMapa = new Map();
      lista.forEach((linha) => {
        const grupo = linha.grupo || 'Outros';
        if (!agrupadosMapa.has(grupo)) agrupadosMapa.set(grupo, []);
        agrupadosMapa.get(grupo).push(linha);
      });
      const agrupados = [...agrupadosMapa.entries()].sort(([a], [b]) => {
        const na = ordemGrupo.indexOf(a), nb = ordemGrupo.indexOf(b);
        return (na < 0 ? 999 : na) - (nb < 0 ? 999 : nb) || a.localeCompare(b, 'pt-BR');
      }).map(([nome, itens]) => [nome, [...itens].sort((a, b) => a.produto.localeCompare(b.produto, 'pt-BR'))]);
      const variacoesDe = (linha) => linha.variacoes.filter((v) => v.itens.length)
        .slice().sort((a, b) => ordemVariacao(a) - ordemVariacao(b));
      const totalRegras = lista.reduce((n, l) => n + variacoesDe(l).length, 0);
      const ancora = (linha) => 'p-' + nomeArquivo(linha.id || linha.produto);

      // Embalagens realmente usadas, com os produtos que pedem cada uma
      const usoEmbalagem = new Map();
      lista.forEach((linha) => variacoesDe(linha).forEach((v) => v.itens.forEach((item) => {
        if (!usoEmbalagem.has(item.embalagemId)) usoEmbalagem.set(item.embalagemId, new Set());
        usoEmbalagem.get(item.embalagemId).add(linha.produto);
      })));
      const semFoto = [...usoEmbalagem.keys()].filter((id) => {
        const emb = indiceEmbalagem.get(id);
        return !(emb && imagemValida(emb.foto));
      }).length;

      const fotoOuVazio = (emb, classe) => {
        const nome = emb ? emb.nome : 'Embalagem não encontrada no cadastro';
        const imagem = emb ? imagemValida(emb.foto) : '';
        return imagem
          ? '<img class="' + classe + '" loading="eager" src="' + imagem + '" alt="' + esc(nome) + '">'
          : '<div class="embalagem-sem-foto">' + ICONES.caixa + '<small>sem foto</small></div>';
      };
      const embalagemCard = (item) => {
        const emb = indiceEmbalagem.get(item.embalagemId);
        const nome = emb ? emb.nome : 'Embalagem não encontrada no cadastro';
        return '<article class="embalagem-card"><div class="embalagem-imagem">' + fotoOuVazio(emb, 'embalagem-foto') +
          '<span class="embalagem-quantidade">×' + numero(item.quantidade) + '</span></div>' +
          '<div class="embalagem-nome">' + esc(nome) + '</div></article>';
      };
      const produtoHTML = (linha, cor) => {
        const variacoes = variacoesDe(linha);
        return '<article class="produto" id="' + ancora(linha) + '" style="--cor:' + cor + '">' +
          '<div class="produto-cabecalho"><h3>' + esc(linha.produto) + '</h3>' +
          '<span class="produto-contador">' + variacoes.length + (variacoes.length === 1 ? ' situação' : ' situações') + '</span></div>' +
          variacoes.map((v) => '<section class="variacao">' +
            '<div class="variacao-titulo"><span class="variacao-legenda">Cliente levou</span>' +
            '<div class="qtd">' + etiquetaVariacao(v) + '</div></div>' +
            '<div class="variacao-seta">' + ICONES.seta + '<small>separe</small></div>' +
            '<div class="embalagens">' + v.itens.map(embalagemCard).join('') + '</div></section>').join('') +
          '</article>';
      };

      const indiceHTML = agrupados.map(([nome, itens]) =>
        '<div class="indice-grupo" style="--cor:' + corGrupo(nome) + '"><h3><i></i>' + esc(nome) +
        '<small>' + itens.length + '</small></h3><ol>' +
        itens.map((l) => '<li><a href="#' + ancora(l) + '">' + esc(l.produto) + '</a></li>').join('') +
        '</ol></div>').join('');

      const corpo = agrupados.map(([nome, itens], i) =>
        '<section class="grupo" style="--cor:' + corGrupo(nome) + '"><div class="grupo-cabecalho">' +
        '<span class="grupo-numero">' + String(i + 1).padStart(2, '0') + '</span><h2>' + esc(nome) + '</h2>' +
        '<span class="grupo-quantidade">' + itens.length + (itens.length === 1 ? ' produto' : ' produtos') + '</span></div>' +
        '<div class="grupo-produtos">' + itens.map((l) => produtoHTML(l, corGrupo(nome))).join('') +
        '</div></section>').join('');


      const notaFotos = semFoto
        ? '<div class="aviso-fotos"><strong>Faltam fotos:</strong> ' + semFoto +
          (semFoto === 1 ? ' embalagem usada ainda não tem foto.' : ' embalagens usadas ainda não têm foto.') +
          ' Envie em Produtos → Embalagens para o manual ficar completo.</div>'
        : '';
      return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Manual de embalagens - ${esc(unitName)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root{color-scheme:light;font-family:Montserrat,Arial,Helvetica,sans-serif;color:#1f3328;--verde:#285c3e}
  *{box-sizing:border-box}
  body{margin:0;background:#e9efe9;font-size:12px;line-height:1.4}
  svg{width:100%;height:100%;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
  .folha{max-width:880px;margin:20px auto;padding:30px 34px 36px;background:#fff;box-shadow:0 5px 28px #10291818}
  .acoes{position:sticky;top:0;z-index:3;display:flex;align-items:center;justify-content:space-between;gap:15px;padding:12px 16px;background:#e3eee5;border-bottom:1px solid #cfe0d3}
  .acoes span{font-size:12px;color:#3a6247}
  .acoes button{padding:11px 17px;border:0;border-radius:8px;background:var(--verde);color:#fff;font-size:13px;font-weight:700;cursor:pointer}
  .acoes button:disabled{opacity:.6;cursor:wait}
  /* Capa */
  .capa{display:flex;flex-direction:column;gap:22px}
  .assinatura{display:flex;gap:9px;align-items:center;font-size:10px;font-weight:800;letter-spacing:.14em;color:#51755e}
  .marca{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:8px;background:var(--verde);color:#fff;letter-spacing:0}
  h1{font-size:40px;line-height:1.05;letter-spacing:-.03em;margin:0;color:#1d4a30}
  .subtitulo{color:#5d7366;margin:8px 0 0;font-size:13px}
  .infos{display:flex;flex-wrap:wrap;gap:8px}
  .infos span{padding:7px 11px;background:#eef5f0;border-radius:20px;font-size:11px;font-weight:700;color:#3d6549}
  .como{border:2px solid #dbe8de;border-radius:14px;padding:16px 18px;background:#f8fbf8}
  .como h2{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#4c6f58;margin:0 0 12px}
  .passos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
  .passo{display:flex;gap:10px;align-items:flex-start}
  .passo-num{flex:none;width:34px;height:34px;border-radius:50%;background:var(--verde);color:#fff;font-size:17px;font-weight:800;display:flex;align-items:center;justify-content:center}
  .passo-ic{width:26px;height:26px;color:#2f6a46;margin-bottom:4px}
  .passo b{display:block;font-size:13px;color:#1f3d2b}
  .passo small{font-size:11px;color:#5f7567}
  .exemplo{display:flex;align-items:center;gap:12px;margin-top:14px;padding-top:12px;border-top:1px dashed #d3e2d7;font-size:11px;color:#4f6a59}
  .exemplo .mini{position:relative;width:46px;height:40px;border-radius:8px;background:#fff;border:1px solid #dce7df;display:flex;align-items:center;justify-content:center;color:#8aa293}
  .exemplo .mini svg{width:22px;height:22px}
  .exemplo .mini span{position:absolute;top:-8px;right:-10px;background:#1f3d2b;color:#fff;font-weight:800;font-size:11px;border-radius:12px;padding:2px 6px}
  .indice{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px 22px}
  .indice-titulo{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#4c6f58;margin:0 0 -6px}
  .indice-grupo h3{display:flex;align-items:center;gap:8px;font-size:14px;margin:0 0 6px;color:#1f3328}
  .indice-grupo h3 i{width:12px;height:12px;border-radius:4px;background:var(--cor)}
  .indice-grupo h3 small{margin-left:auto;font-size:11px;color:#8a9a90}
  .indice-grupo ol{margin:0;padding:0 0 0 20px;columns:1;font-size:12px;color:#33493b}
  .indice-grupo li{padding:2px 0;border-bottom:1px dotted #e2ebe4}
  .indice-grupo a{color:inherit;text-decoration:none}
  .aviso-fotos{padding:10px 13px;font-size:11px;border:1px solid #eddfb7;background:#fff9ea;color:#755b2d;border-radius:8px}
  /* Grupos e produtos */
  .grupo{margin-top:28px}
  .grupo-cabecalho{display:flex;align-items:center;gap:12px;background:var(--cor);color:#fff;padding:13px 16px;border-radius:12px;margin-bottom:14px}
  .grupo-numero{font-weight:800;font-size:13px;opacity:.8}
  h2{margin:0;font-size:20px;font-weight:800;letter-spacing:-.01em}
  .grupo-quantidade{margin-left:auto;font-size:11px;font-weight:700;opacity:.9;white-space:nowrap}
  /* Bloco comum (não flex): o Chrome só respeita "não quebrar o produto
     entre páginas" fora de flex/grid. */
  .grupo-produtos{display:block}
  .grupo-produtos>.produto+.produto{margin-top:14px}
  .produto{border:1.5px solid #dce6df;border-left:6px solid var(--cor);border-radius:12px;background:#fff}
  .produto-cabecalho{display:flex;gap:10px;align-items:center;padding:12px 16px;border-bottom:1px solid #edf1ee}
  h3{font-size:18px;line-height:1.2;margin:0;color:#1d3326;letter-spacing:-.01em}
  .produto-contador{margin-left:auto;font-size:10px;font-weight:700;color:#7c8f82;white-space:nowrap;text-transform:uppercase;letter-spacing:.06em}
  .variacao{display:grid;grid-template-columns:118px 46px minmax(0,1fr);align-items:center;gap:6px;padding:12px 16px}
  .variacao+.variacao{border-top:1px dashed #e0e9e3}
  .variacao-titulo{display:flex;flex-direction:column;align-items:center;gap:4px}
  .variacao-legenda{font-size:9px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:#8a9a90}
  .qtd{width:108px;min-height:74px;border-radius:12px;background:color-mix(in srgb,var(--cor) 12%,#fff);border:2px solid color-mix(in srgb,var(--cor) 45%,#fff);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:6px;text-align:center;color:#1d3326}
  .qtd b{font-size:32px;line-height:1;font-weight:800}
  .qtd small{font-size:10px;font-weight:700;color:#4e6457}
  .qtd-texto{font-size:12px;font-weight:800}
  .variacao-seta{display:flex;flex-direction:column;align-items:center;color:var(--cor)}
  .variacao-seta svg{width:30px;height:30px;stroke-width:2.5}
  .variacao-seta small{font-size:9px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:#8a9a90}
  .embalagens{display:flex;flex-wrap:wrap;gap:12px}
  .embalagem-card{width:118px;display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center}
  .embalagem-imagem{position:relative;width:110px;height:100px;border-radius:12px;background:#f4f7f4;border:1px solid #e3ebe5;display:flex;align-items:center;justify-content:center}
  .embalagem-foto{max-width:100%;max-height:100%;object-fit:contain;border-radius:11px}
  .embalagem-quantidade{position:absolute;top:-9px;right:-9px;min-width:38px;height:30px;padding:0 8px;border-radius:15px;background:#1f3d2b;color:#fff;font-size:16px;font-weight:800;display:flex;align-items:center;justify-content:center;box-shadow:0 0 0 3px #fff}
  .embalagem-sem-foto{display:flex;flex-direction:column;align-items:center;gap:4px;color:#9fb0a5}
  .embalagem-sem-foto svg{width:34px;height:34px}
  .embalagem-sem-foto small{font-size:9px;font-weight:700;text-transform:uppercase}
  .embalagem-nome{font-size:11.5px;font-weight:700;line-height:1.3;color:#2c4636;overflow-wrap:anywhere}
  .rodape{margin-top:22px;padding-top:12px;border-top:1px solid #e1ece3;color:#859889;font-size:10px}
  @page{size:A4 portrait;margin:11mm 10mm 13mm}
  @media print{
    html,body{background:#fff!important}
    body{-webkit-print-color-adjust:exact;print-color-adjust:exact}
    .acoes{display:none!important}
    .folha{width:auto;max-width:none;margin:0;padding:0;box-shadow:none}
    .capa{break-after:page}
    .grupo{margin-top:0;break-before:page}
    .grupo-cabecalho,.produto-cabecalho,.variacao-titulo{break-after:avoid-page}
    /* inline-block é indivisível para o Chrome: o produto nunca fica com
       o título numa página e as fotos na outra. */
    .produto{break-inside:avoid-page;page-break-inside:avoid;display:inline-block;width:100%;vertical-align:top}
    .variacao{break-inside:avoid-page;page-break-inside:avoid}
    .indice-grupo{break-inside:avoid}
  }
  @media(max-width:640px){
    .folha{margin:0;padding:20px 14px;box-shadow:none}
    .acoes{flex-wrap:wrap}
    h1{font-size:30px}
    .passos,.indice{grid-template-columns:1fr}
    .variacao{grid-template-columns:1fr;justify-items:start}
    .variacao-titulo{flex-direction:row}
    .variacao-seta{flex-direction:row;gap:6px}
    .variacao-seta svg{transform:rotate(90deg);width:22px;height:22px}
  }
</style></head><body>
<div class="acoes"><span>Pré-visualização do manual de embalagens</span>
<button type="button" id="salvar-pdf" onclick="imprimirManual()">Imprimir / Salvar PDF</button></div>
<main class="folha">
<header class="capa">
  <div class="assinatura"><span class="marca">DV</span> DELÍCIAS DA VOVÓ · MANUAL DA EQUIPE</div>
  <div>
    <h1>Manual de embalagens</h1>
    <p class="subtitulo">Qual embalagem usar em cada produto, conforme a quantidade do pedido.</p>
  </div>
  <div class="infos"><span>${esc(unitName)}</span><span>Atualizado em ${esc(data)}</span>
    <span>${lista.length} produtos</span><span>${totalRegras} situações</span><span>${usoEmbalagem.size} embalagens</span></div>
  <section class="como">
    <h2>Como usar</h2>
    <div class="passos">
      <div class="passo"><span class="passo-num">1</span><div><div class="passo-ic">${ICONES.buscar}</div><b>Ache o produto</b><small>Pelo índice abaixo ou pela cor do grupo.</small></div></div>
      <div class="passo"><span class="passo-num">2</span><div><div class="passo-ic">${ICONES.contar}</div><b>Veja quantas unidades</b><small>Encontre a linha com a quantidade que o cliente levou.</small></div></div>
      <div class="passo"><span class="passo-num">3</span><div><div class="passo-ic">${ICONES.caixa}</div><b>Separe as embalagens</b><small>Pegue exatamente as da foto, na quantidade indicada.</small></div></div>
    </div>
    <div class="exemplo"><div class="mini">${ICONES.caixa}<span>×2</span></div><div><b>×2</b> em cima da foto = use <b>2 unidades</b> daquela embalagem.</div></div>
  </section>
  ${notaFotos}
  <h2 class="indice-titulo">Índice</h2>
  <nav class="indice">${indiceHTML}</nav>
</header>
${corpo}
<footer class="rodape">Delícias da Vovó · ${esc(titulo)} · ${esc(unitName)} · ${esc(data)}</footer>
</main>
<script>
  async function imprimirManual(){
    const btn=document.getElementById('salvar-pdf');
    btn.disabled=true;btn.textContent='Preparando fotos…';
    try{
      // A Montserrat vem do Google Fonts: espera carregar para o PDF não sair com a fonte reserva.
      if (document.fonts && document.fonts.ready) await document.fonts.ready.catch(()=>{});
      await Promise.all(Array.from(document.querySelectorAll('img'))
        .map(img => img.decode ? img.decode().catch(()=>{}) :
          new Promise(resolve=>{if(img.complete)return resolve();
            img.onload=resolve;img.onerror=resolve;})));
      window.focus();window.print();
    } finally{
      btn.disabled=false;btn.textContent='Imprimir / Salvar PDF';
    }
  }
</script>
</body></html>`;
    };
    const imprimir = () => {
      const lista = linhasCatalogo.filter((l) =>
        l.variacoes.some((v) => v.itens && v.itens.length));
      if (!lista.length) return window.alert('Escolha embalagens em pelo menos um produto antes de criar o manual.');
      const win = window.open('', '_blank');
      if (!win) return window.alert('Autorize a janela do manual no navegador.');
      const html = construirManualHTML(lista);
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
          <button type="button" className="btn btn-primary btn-sm" onClick={imprimir}>Manual com fotos (PDF)</button>
        </div>
      </div>
      <div className="emb-status" role="status">{situacao}{erro && <span className="emb-erro"> — {erro}</span>}</div>

      <div className="emb2-intro">
        <div className="emb2-passos">
          <div><b>1.</b> Escolha um grupo e abra o produto</div>
          <div><b>2.</b> Adicione uma variação, como “Menos de 3”</div>
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
              <div className="emb2-preco-unitario">{formatarPrecoEmbalagem(e.precoUnitario)}</div>
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
                                  <option value="menos_de">Menos de</option>
                                  <option value="mais_de" disabled>Mais de (antigo)</option>
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
                    <span className="emb2-preco-unitario">{formatarPrecoEmbalagem(e.precoUnitario)}</span>
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
