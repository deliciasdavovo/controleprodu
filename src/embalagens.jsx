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
            .select('supply_id,purchase_date,created_at,qty,cost,purchase_unit,quantity_basis')
            .eq('unit_code', currentUnit)
            .order('purchase_date', { ascending: false })
            .limit(2000);
          if (error) throw error;
          const valores = {};
          for (const p of data || []) {
            const id = String(p.supply_id || '');
            if (!id || valores[id] || !(Number(p.qty) > 0) || !(Number(p.cost) > 0)) continue;
            const unidade = String(p.purchase_unit || '').toLowerCase();
            if (p.quantity_basis === 'base' && !['un','unidade','unidades'].includes(unidade)) continue;
            valores[id] = Number(p.cost) / Number(p.qty);
          }
          if (!cancelado) setPrecosEmbalagem(valores);
        } catch (err) {
          if (!cancelado) setPrecosEmbalagem({});
          console.warn('Preços de embalagens indisponíveis:', err);
        }
      })();
      return () => { cancelado = true; };
    }, [sb, currentUnit]);
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
    const construirManualHTML = (lista) => {
      const data = new Date().toLocaleDateString('pt-BR');
      const agrupados = new Map();
      lista.forEach((linha) => {
        const grupo = linha.grupo || 'Outros';
        if (!agrupados.has(grupo)) agrupados.set(grupo, []);
        agrupados.get(grupo).push(linha);
      });
      const totalRegras = lista.reduce((n, l) => n + l.variacoes.filter((v) => v.itens.length).length, 0);
      let semFoto = 0;
      const embalagemCard = (item) => {
        const emb = indiceEmbalagem.get(item.embalagemId);
        const nome = emb ? emb.nome : 'Embalagem não encontrada no cadastro';
        const imagem = emb ? imagemValida(emb.foto) : '';
        if (!imagem) semFoto++;
        const foto = imagem
          ? '<img class="embalagem-foto" loading="eager" src="' + imagem +
              '" alt="' + esc(nome) + '">'
          : '<div class="embalagem-sem-foto"><b>Sem foto</b><small>Cadastre no sistema</small></div>';
        return '<article class="embalagem-card">' +
          '<div class="embalagem-imagem">' + foto + '</div>' +
          '<div class="embalagem-info"><b class="embalagem-quantidade">' + numero(item.quantidade) +
          ' <small>×</small></b><div class="embalagem-nome">' + esc(nome) +
          '</div><div class="embalagem-preco">' + esc(formatarPrecoEmbalagem(emb && emb.precoUnitario)) + '</div></div></article>';
      };
      const produtoHTML = (linha, indice) => {
        const variacoes = linha.variacoes.filter((v) => v.itens.length);
        return '<article class="produto"><div class="produto-cabecalho"><span class="produto-indice">' +
          String(indice).padStart(2, '0') + '</span><h3>' + esc(linha.produto) +
          '</h3><span class="produto-contador">' + variacoes.length +
          (variacoes.length === 1 ? ' variação' : ' variações') + '</span></div>' +
          variacoes.map((v) => '<section class="variacao"><div class="variacao-titulo">' +
            '<span class="variacao-sinal"></span><h4>' + esc(textoRegra(v)) +
            '</h4><span class="variacao-legenda">Embalagens necessárias</span></div>' +
            '<div class="embalagens">' + v.itens.map(embalagemCard).join('') +
            '</div></section>').join('') + '</article>';
      };
      let indice = 0;
      const corpo = [...agrupados.entries()].map(([nome, grupo], i) =>
        '<section class="grupo"><div class="grupo-cabecalho"><span class="grupo-numero">' +
        String(i + 1).padStart(2, '0') + '</span><h2>' + esc(nome) +
        '</h2><span class="grupo-quantidade">' + grupo.length +
        (grupo.length === 1 ? ' produto' : ' produtos') + '</span></div>' +
        '<div class="grupo-produtos">' + grupo.map((l) => produtoHTML(l, ++indice)).join('') +
        '</div></section>').join('');
      const notaFotos = semFoto
        ? '<div class="aviso-fotos"><strong>Atenção:</strong> ' + semFoto +
          (semFoto === 1 ? ' embalagem usada ainda não tem foto.' : ' embalagens usadas ainda não têm foto.') +
          ' Para completar o manual, abra CMV → Embalagens e envie as imagens nos cartões.</div>'
        : '<div class="aviso-ok">Todas as embalagens utilizadas possuem fotos cadastradas.</div>';
      return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Manual de embalagens - ${esc(unitName)}</title>
<style>
  :root{color-scheme:light;font-family:Arial,Helvetica,sans-serif;color:#274733}
  *{box-sizing:border-box}
  body{margin:0;background:#edf2ee;font-size:12px;line-height:1.4}
  .folha{max-width:900px;margin:20px auto;padding:28px 33px 36px;background:#fff;box-shadow:0 5px 28px #10291818}
  .acoes{position:sticky;top:0;z-index:3;display:flex;align-items:center;justify-content:space-between;gap:15px;padding:13px 16px;background:#e8f1e9;border-bottom:1px solid #d4e5d8}
  .acoes span{font-size:12px;color:#3a6247}
  .acoes button{padding:11px 17px;border:0;border-radius:6px;background:#285c3e;color:#fff;font-size:13px;font-weight:700;cursor:pointer}
  .acoes button:disabled{opacity:.6;cursor:wait}
  .capa{border-bottom:3px solid #326447;padding-bottom:21px;margin-bottom:20px}
  .assinatura{display:flex;gap:9px;align-items:center;font-size:10px;font-weight:700;letter-spacing:.13em;color:#51755e}
  .marca{display:inline-flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:7px;background:#285c3e;color:#fff;letter-spacing:0}
  .tipo{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#799080;margin:20px 0 5px}
  h1{font-size:29px;line-height:1.12;letter-spacing:-.02em;margin:0;color:#254c34}
  .subtitulo{color:#63786a;margin:9px 0 0;font-size:12px}
  .infos{display:flex;flex-wrap:wrap;gap:7px;margin-top:15px}
  .infos span{padding:6px 10px;background:#edf4ef;border:1px solid #d9e8dc;border-radius:6px;font-size:11px;font-weight:650;color:#446950}
  .aviso-fotos,.aviso-ok{padding:10px 13px;font-size:11px;border:1px solid #dfebdf;background:#fafcf7;border-radius:7px;margin:16px 0}
  .aviso-fotos{background:#fff9ea;border-color:#eddfb7;color:#755b2d}
  .aviso-ok{color:#42694d}
  .grupo{margin:23px 0 25px}
  .grupo-cabecalho{display:flex;align-items:center;gap:11px;background:#e6f0e8;color:#245438;padding:11px 13px;border-radius:8px;margin-bottom:12px}
  .grupo-numero{font-weight:800;color:#70977b;font-size:12px}
  h2{margin:0;font-size:16px;font-weight:800}
  .grupo-quantidade{margin-left:auto;font-size:10px;font-weight:700;color:#668572;white-space:nowrap}
  .grupo-produtos{display:flex;flex-direction:column;gap:13px}
  .produto{border:1px solid #d8e5db;border-radius:9px;overflow:hidden;background:#fff}
  .produto-cabecalho{display:flex;gap:10px;align-items:center;padding:12px 14px;background:#f5f9f6;border-bottom:1px solid #e4eee6}
  .produto-indice{font-size:10px;color:#96a79a;min-width:22px}
  h3{font-size:15px;line-height:1.25;margin:0;color:#294d37}
  .produto-contador{margin-left:auto;font-size:10px;color:#738d7a;white-space:nowrap}
  .variacao{padding:13px 14px 15px}
  .variacao+.variacao{border-top:1px dashed #dce8de}
  .variacao-titulo{display:flex;align-items:center;gap:8px;margin-bottom:10px}
  .variacao-sinal{width:4px;height:17px;background:#3e8659;border-radius:3px}
  h4{font-size:12px;font-weight:800;margin:0;color:#305d42}
  .variacao-legenda{color:#8b9c90;font-size:10px;margin-left:auto}
  .embalagens{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}
  .embalagem-card{display:flex;gap:10px;align-items:center;min-height:100px;border:1px solid #e0e9e2;border-radius:7px;padding:8px;background:#fff}
  .embalagem-imagem{width:89px;height:83px;flex:0 0 89px;border-radius:5px;background:#f3f6f3;display:flex;align-items:center;justify-content:center;overflow:hidden}
  .embalagem-foto{width:100%;height:100%;object-fit:contain}
  .embalagem-sem-foto{text-align:center;color:#87998c;font-size:10px;display:flex;flex-direction:column;gap:3px}
  .embalagem-sem-foto small{font-size:8px;color:#abb9ad}
  .embalagem-info{min-width:0}
  .embalagem-quantidade{font-size:23px;line-height:1;color:#2c6844}
  .embalagem-quantidade small{font-size:12px;color:#719582}
  .embalagem-nome{font-size:12px;font-weight:700;line-height:1.35;margin-top:6px;overflow-wrap:anywhere;color:#385441}
  .embalagem-preco{font-size:11px;font-weight:700;color:#2f5d45;margin-top:5px}
  .rodape{margin-top:20px;padding-top:12px;border-top:1px solid #e1ece3;color:#859889;font-size:10px}
  @page{size:A4 portrait;margin:12mm 11mm 15mm}
  @media print{
    html,body{background:#fff!important}
    body{-webkit-print-color-adjust:exact;print-color-adjust:exact}
    .acoes{display:none!important}
    .folha{width:auto;max-width:none;margin:0;padding:0;box-shadow:none}
    .capa{break-after:avoid-page}
    .grupo-cabecalho,.produto-cabecalho,.variacao-titulo{break-after:avoid-page}
    .grupo,.grupo-produtos{break-inside:auto}
    .produto{break-inside:avoid-page;page-break-inside:avoid}
    .variacao{break-inside:avoid-page;page-break-inside:avoid}
    .embalagem-card{break-inside:avoid;page-break-inside:avoid}
    .grupo{margin:20px 0 21px}
    .embalagens{grid-template-columns:repeat(2,minmax(0,1fr))}
    .embalagem-card{min-height:91px}
    .embalagem-imagem{width:79px;height:73px;flex-basis:79px}
    .rodape{break-before:avoid}
  }
  @media(max-width:600px){
    .folha{margin:0;padding:19px 15px;box-shadow:none}
    .acoes{flex-wrap:wrap}
    .embalagens{grid-template-columns:1fr}
    h1{font-size:25px}
  }
</style></head><body>
<div class="acoes"><span>Pré-visualização do manual com fotos</span>
<button type="button" id="salvar-pdf" onclick="imprimirManual()">Imprimir / Salvar PDF</button></div>
<main class="folha">
<header class="capa">
  <div class="assinatura"><span class="marca">DV</span> DELÍCIAS DA VOVÓ</div>
  <div class="tipo">Manual prático para a equipe</div>
  <h1>Manual de embalagens</h1>
  <p class="subtitulo">${esc(titulo)} · Orientações por produto e quantidade do pedido</p>
  <div class="infos"><span>Unidade: ${esc(unitName)}</span>
    <span>Atualizado em: ${esc(data)}</span>
    <span>${lista.length} produtos</span><span>${totalRegras} variações</span></div>
</header>
${notaFotos}
${corpo}
<footer class="rodape">Delícias da Vovó · Consulte a variação do produto e separe as embalagens indicadas antes de montar o pedido.</footer>
</main>
<script>
  async function imprimirManual(){
    const btn=document.getElementById('salvar-pdf');
    btn.disabled=true;btn.textContent='Preparando fotos…';
    try{
      await Promise.all(Array.from(document.querySelectorAll('.embalagem-foto'))
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
