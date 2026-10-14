/* Controle Produ — Organizador visual de embalagens por faixa de quantidade.
 * Um produto por linha; cada celula contem MULTIPLAS embalagens cadastradas.
 * Compatível com Babel Standalone e com o formato anterior salvo no Supabase. */
(function () {
  const { useState, useEffect, useMemo, useRef } = React;
  const idNovo = () => (window.crypto && window.crypto.randomUUID)
    ? window.crypto.randomUUID()
    : String(Date.now()) + '-' + Math.random().toString(36).slice(2);
  const numero = (valor) => {
    const n = Number(valor);
    return Number.isFinite(n) ? Math.max(0, Math.floor(n)) : 0;
  };
  const escapar = (valor) => String(valor == null ? '' : valor).replace(/[&<>"']/g,
    (caractere) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[caractere]));
  const fotoSegura = (valor) => typeof valor === 'string' && valor.length < 300000 &&
    /^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(valor) ? valor : '';
  const colunasIniciais = () => [
    { id: 'quantidade-1', rotulo: '1 unidade' },
    { id: 'quantidade-maior', rotulo: 'Mais de X unidades' }
  ];
  const slug = (valor) => String(valor || 'embalagens').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 65);
  const arquivo = (nome, conteudo, tipo) => {
    const url = URL.createObjectURL(new Blob([conteudo], { type: tipo }));
    const link = document.createElement('a');
    link.href = url;
    link.download = nome;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  };
  const fotoCompactada = async (arq) => {
    if (!arq || !['image/png', 'image/jpeg', 'image/webp'].includes(arq.type)) {
      throw new Error('Escolha uma foto em JPG, PNG ou WEBP.');
    }
    if (arq.size > 8 * 1024 * 1024) throw new Error('A foto deve ter até 8 MB.');
    const link = URL.createObjectURL(arq);
    try {
      const img = new Image();
      img.src = link;
      await img.decode();
      const escala = Math.min(1, 460 / Math.max(img.naturalWidth, img.naturalHeight));
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(img.naturalWidth * escala));
      canvas.height = Math.max(1, Math.round(img.naturalHeight * escala));
      const ctx = canvas.getContext('2d');
      if (!ctx) throw new Error('Não foi possível preparar a imagem.');
      ctx.fillStyle = '#fff';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      let dados = canvas.toDataURL('image/jpeg', .72);
      if (dados.length > 160000) dados = canvas.toDataURL('image/jpeg', .45);
      if (dados.length > 160000) throw new Error('Imagem grande demais. Envie outra foto.');
      return dados;
    } finally {
      URL.revokeObjectURL(link);
    }
  };

  const celulaLimpa = (entrada) => {
    if (!Array.isArray(entrada)) return [];
    const vistos = new Set();
    return entrada.slice(0, 80).filter((item) => {
      const id = item && String(item.embalagemId || '');
      if (!id || vistos.has(id) || numero(item.quantidade) < 1) return false;
      vistos.add(id);
      return true;
    }).map((item) => ({ embalagemId: String(item.embalagemId), quantidade: numero(item.quantidade) }));
  };

  const lerDados = (salvo) => {
    const dados = salvo && typeof salvo === 'object' && !Array.isArray(salvo) ? salvo : {};
    const embalagens = Array.isArray(dados.embalagens) ? dados.embalagens.slice(0, 24)
      .filter((e) => e && e.id)
      .map((e) => ({ id: String(e.id), nome: String(e.nome || ''), foto: fotoSegura(e.foto) })) : [];
    const originais = Array.isArray(dados.linhas) ? dados.linhas.slice(0, 500) : [];
    const formatoNovo = Array.isArray(dados.faixas) && dados.faixas.length > 0;
    if (formatoNovo) {
      const faixas = dados.faixas.slice(0, 20).filter((x) => x && x.id)
        .map((x) => ({ id: String(x.id), rotulo: String(x.rotulo || '').slice(0, 90) }));
      const linhas = originais.filter((x) => x && x.id).map((x) => {
        const celulas = {};
        faixas.forEach((faixa) => {
          celulas[faixa.id] = celulaLimpa(x.celulas && x.celulas[faixa.id]);
        });
        return { id: String(x.id), productId: String(x.productId || ''), produto: String(x.produto || ''), celulas };
      });
      return { titulo: String(dados.titulo || 'Tabela de embalagens por quantidade'), embalagens,
        faixas: faixas.length ? faixas : colunasIniciais(), linhas };
    }
    // Migração não destrutiva das versões anteriores (uma linha por quantidade).
    // Dados antigos são agrupados em uma linha por produto, com uma coluna por quantidade.
    const regras = originais.filter((x) => x && x.id);
    if (!regras.length) {
      return { titulo: String(dados.titulo || 'Tabela de embalagens por quantidade'),
        embalagens, faixas: colunasIniciais(), linhas: [] };
    }
    const quantidades = [...new Set(regras.map((x) => Math.max(1, numero(x.quantidade))))].sort((a, b) => a - b);
    const faixas = quantidades.map((q) => ({
      id: 'legado-' + q, rotulo: q === 1 ? '1 unidade' : q + ' unidades'
    }));
    if (!quantidades.includes(1)) faixas.unshift({ id: 'quantidade-1', rotulo: '1 unidade' });
    const porProduto = new Map();
    regras.forEach((x) => {
      const nome = String(x.produto || '');
      const chave = nome.trim().toLocaleLowerCase('pt-BR') || String(x.id);
      if (!porProduto.has(chave)) porProduto.set(chave, {
        id: String(x.id), produto: nome, celulas: {}
      });
      const linha = porProduto.get(chave);
      const coluna = 'legado-' + Math.max(1, numero(x.quantidade));
      const alocacoes = x.alocacoes && typeof x.alocacoes === 'object' ? x.alocacoes : {};
      linha.celulas[coluna] = celulaLimpa(
        Object.entries(alocacoes).map(([embalagemId, quantidade]) => ({ embalagemId, quantidade }))
      );
    });
    return { titulo: String(dados.titulo || 'Tabela de embalagens por quantidade'), embalagens,
      faixas, linhas: [...porProduto.values()] };
  };

  const PackagingMatrixView = ({ sb, currentUnit, unitName, products = [], separatedProducts = [], supplies = [] }) => {
    const [titulo, setTitulo] = useState('Tabela de embalagens por quantidade');
    const [embalagens, setEmbalagens] = useState([]);
    const [faixas, setFaixas] = useState(colunasIniciais);
    const [linhas, setLinhas] = useState([]);
    const [buscaEmbalagem, setBuscaEmbalagem] = useState('');
    const [buscaProduto, setBuscaProduto] = useState('');
    const [mostrarInativos, setMostrarInativos] = useState(false);
    const [carregada, setCarregada] = useState('');
    const [erro, setErro] = useState('');
    const [estado, setEstado] = useState('Carregando…');
    const [editando, setEditando] = useState(null);
    const leituraAtual = useRef(0);
    const fila = useRef(Promise.resolve());
    const ultimo = useRef('');
    const unidadeAtiva = useRef(currentUnit);
    unidadeAtiva.current = currentUnit;

    const embalagensDisponiveis = useMemo(() => {
      const fotos = new Map(embalagens.map((e) => [e.id, e.foto]));
      const originais = supplies.filter((e) => e && e.id && String(e.supplyClass || '').toLowerCase() === 'embalagem')
        .map((e) => ({ id: String(e.id), nome: String(e.name || 'Embalagem'),
          foto: fotoSegura(fotos.get(String(e.id))) }));
      const ids = new Set(originais.map((e) => e.id));
      const antigas = embalagens.filter((e) => !ids.has(e.id));
      return [...originais, ...antigas].sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'));
    }, [supplies, embalagens]);
    const indiceEmbalagens = useMemo(() =>
      new Map(embalagensDisponiveis.map((e) => [e.id, e])), [embalagensDisponiveis]);
    const produtosProducao = useMemo(() => products
      .filter((p) => p && p.id && p.name && (mostrarInativos || p.showcaseEnabled !== false))
      .sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')), [products, mostrarInativos]);
    const linhasCatalogo = useMemo(() => {
      const porId = new Map(linhas.filter((x) => x.productId).map((x) => [x.productId, x]));
      const porNome = new Map();
      linhas.filter((x) => !x.productId).forEach((x) => {
        const nome = x.produto.trim().toLocaleLowerCase('pt-BR');
        if (nome && !porNome.has(nome)) porNome.set(nome, x);
      });
      const utilizadas = new Set();
      const daProducao = produtosProducao.map((p) => {
        const antigo = porId.get(String(p.id)) || porNome.get(p.name.trim().toLocaleLowerCase('pt-BR'));
        if (antigo) utilizadas.add(antigo.id);
        return antigo ? { ...antigo, productId: String(p.id), produto: p.name }
          : { id: 'producao-' + p.id, productId: String(p.id), produto: p.name, celulas: {} };
      });
      const extras = linhas.filter((x) => !utilizadas.has(x.id) &&
        (!x.productId || !products.some((p) => p.id === x.productId)));
      return [...daProducao, ...extras];
    }, [produtosProducao, products, linhas]);
    const linhasVisiveis = useMemo(() => {
      const termo = buscaProduto.trim().toLocaleLowerCase('pt-BR');
      return termo ? linhasCatalogo.filter((x) => x.produto.toLocaleLowerCase('pt-BR').includes(termo)) : linhasCatalogo;
    }, [linhasCatalogo, buscaProduto]);
    const embalagensVisiveis = useMemo(() => {
      const termo = buscaEmbalagem.trim().toLocaleLowerCase('pt-BR');
      return termo ? embalagensDisponiveis.filter((x) => x.nome.toLocaleLowerCase('pt-BR').includes(termo)) : embalagensDisponiveis;
    }, [embalagensDisponiveis, buscaEmbalagem]);

    useEffect(() => {
      const leitura = ++leituraAtual.current;
      setCarregada('');
      setEstado('Carregando…');
      setErro('');
      setEditando(null);
      if (!sb || !currentUnit) {
        setErro('Não foi possível conectar ao banco de dados.');
        return;
      }
      sb.from('packaging_matrices').select('layout').eq('unit_code', currentUnit).maybeSingle()
        .then(({ data, error }) => {
          if (leitura !== leituraAtual.current) return;
          if (error) throw error;
          const registro = lerDados(data && data.layout);
          setTitulo(registro.titulo);
          setEmbalagens(registro.embalagens);
          setFaixas(registro.faixas);
          setLinhas(registro.linhas);
          ultimo.current = JSON.stringify(registro);
          setCarregada(currentUnit);
          setEstado(data ? 'Salvo no Supabase' : 'Novo organizador');
        }).catch((e) => {
          if (leitura !== leituraAtual.current) return;
          setErro('Erro ao carregar: ' + e.message);
          setEstado('Erro');
        });
      return () => { leituraAtual.current += 1; };
    }, [sb, currentUnit]);

    const layout = useMemo(() => ({ titulo, embalagens, faixas, linhas }), [titulo, embalagens, faixas, linhas]);
    const conteudo = useMemo(() => JSON.stringify(layout), [layout]);
    useEffect(() => {
      if (!sb || carregada !== currentUnit || ultimo.current === conteudo) return;
      setEstado('Alterações pendentes…');
      const t = setTimeout(() => {
        setEstado('Salvando…');
        const unidade = currentUnit;
        const pacote = { unit_code: unidade, layout, updated_at: new Date().toISOString() };
        const gravacao = fila.current.then(async () => {
          const { error } = await sb.from('packaging_matrices').upsert(pacote, { onConflict: 'unit_code' });
          if (error) throw error;
        });
        fila.current = gravacao.catch(() => {});
        gravacao.then(() => {
          if (unidadeAtiva.current !== unidade) return;
          ultimo.current = conteudo;
          setEstado('Salvo no Supabase');
          setErro('');
        }).catch((e) => {
          if (unidadeAtiva.current !== unidade) return;
          setEstado('Erro ao salvar');
          setErro('Não foi possível salvar: ' + e.message);
        });
      }, 700);
      return () => clearTimeout(t);
    }, [sb, currentUnit, carregada, conteudo]);

    const atualizarCelula = (linhaId, faixaId, atualizar) => {
      const origem = linhasCatalogo.find((x) => x.id === linhaId);
      if (!origem) return;
      setLinhas((anteriores) => {
        const existe = anteriores.some((x) => x.id === linhaId);
        const atualizadas = existe ? anteriores : [...anteriores, { ...origem, celulas: { ...origem.celulas } }];
        return atualizadas.map((linha) => {
          if (linha.id !== linhaId) return linha;
          const atual = Array.isArray(linha.celulas[faixaId]) ? linha.celulas[faixaId] : [];
          return { ...linha, celulas: { ...linha.celulas, [faixaId]: atualizar(atual) } };
        });
      });
    };
    const adicionarNaCelula = (linhaId, faixaId, embalagemId) => {
      if (!embalagemId) return;
      atualizarCelula(linhaId, faixaId, (lista) => lista.some((x) => x.embalagemId === embalagemId)
        ? lista : [...lista, { embalagemId, quantidade: 1 }]);
    };
    const alterarQuantidade = (linhaId, faixaId, embalagemId, quantidade) =>
      atualizarCelula(linhaId, faixaId, (lista) => lista.map((x) => x.embalagemId === embalagemId
        ? { ...x, quantidade: quantidade === '' ? '' : Math.max(1, numero(quantidade)) } : x));
    const excluirDaCelula = (linhaId, faixaId, embalagemId) =>
      atualizarCelula(linhaId, faixaId, (lista) => lista.filter((x) => x.embalagemId !== embalagemId));
    const apagarFoto = (id) => setEmbalagens((prev) => prev.filter((e) => e.id !== id));
    const apagarColuna = (id) => {
      if (faixas.length <= 1) return window.alert('A tabela precisa ter pelo menos uma coluna.');
      if (!window.confirm('Remover esta coluna e suas embalagens selecionadas?')) return;
      setFaixas((prev) => prev.filter((x) => x.id !== id));
      setLinhas((prev) => prev.map((linha) => {
        const celulas = { ...linha.celulas };
        delete celulas[id];
        return { ...linha, celulas };
      }));
    };
    const carregarFoto = async (id, arq) => {
      if (!arq) return;
      try {
        const foto = await fotoCompactada(arq);
        setEmbalagens((prev) => {
          const existe = prev.some((e) => e.id === id);
          if (existe) return prev.map((e) => e.id === id ? { ...e, foto } : e);
          const item = embalagensDisponiveis.find((e) => e.id === id);
          return [...prev, { id, nome: item ? item.nome : 'Embalagem', foto }];
        });
        setErro('');
      } catch (e) {
        setErro(e.message);
      }
    };
    const partes = (linha, faixaId) => (linha.celulas[faixaId] || [])
      .filter((x) => indiceEmbalagens.has(x.embalagemId))
      .map((x) => ({ embalagem: indiceEmbalagens.get(x.embalagemId), quantidade: x.quantidade }));
    const descricaoCelula = (linha, faixaId) => partes(linha, faixaId)
      .filter((item) => numero(item.quantidade) > 0)
      .map(({ embalagem, quantidade }) => numero(quantidade) + ' × ' + embalagem.nome).join(' + ');

    const csv = () => {
      const validas = linhasCatalogo.filter((linha) => linha.produto.trim() &&
        faixas.some((faixa) => (linha.celulas[faixa.id] || []).some((x) => numero(x.quantidade) > 0)));
      if (!validas.length) return window.alert('Adicione pelo menos um produto ao relatório.');
      const tabela = [
        [titulo || 'Tabela de embalagens por quantidade'],
        ['Unidade', unitName],
        ['Data', new Date().toLocaleDateString('pt-BR')],
        [],
        ['Produto', ...faixas.map((f) => f.rotulo || 'Quantidade')],
        ...validas.map((linha) => [linha.produto, ...faixas.map((f) => descricaoCelula(linha, f.id))])
      ];
      const celula = (v) => {
        let valor = String(v == null ? '' : v);
        if (/^\s*[=+\-@]/.test(valor)) valor = "'" + valor;
        return '"' + valor.replace(/"/g, '""') + '"';
      };
      arquivo(slug(titulo || 'tabela-embalagens') + '.csv', '\uFEFF' +
        tabela.map((linha) => linha.map(celula).join(';')).join('\r\n'), 'text/csv;charset=utf-8');
    };
    const imprimir = () => {
      const validas = linhasCatalogo.filter((linha) => linha.produto.trim() &&
        faixas.some((faixa) => (linha.celulas[faixa.id] || []).some((x) => numero(x.quantidade) > 0)));
      if (!validas.length) return window.alert('Adicione pelo menos um produto ao relatório.');
      const win = window.open('', '_blank');
      if (!win) return window.alert('Autorize a janela de impressão para salvar o relatório em PDF.');
      const celulaHTML = (linha, faixa) => {
        const itens = partes(linha, faixa.id).filter((item) => numero(item.quantidade) > 0);
        return itens.length ? itens.map(({ embalagem, quantidade }) =>
          '<div class="item">' +
          (fotoSegura(embalagem.foto) ? '<img src="' + embalagem.foto + '" alt="">' : '') +
          '<div><b>' + quantidade + ' × ' + escapar(embalagem.nome) + '</b></div></div>'
        ).join('') : '<span class="vazio">—</span>';
      };
      const pagina = '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">' +
        '<title>' + escapar(titulo) + '</title><style>' +
        '@page{size:A4 landscape;margin:12mm}*{box-sizing:border-box}' +
        'body{font:12px Arial,sans-serif;color:#274334;margin:0}.acoes{text-align:right;margin-bottom:16px}' +
        '.acoes button{background:#275b3e;border:0;color:#fff;padding:10px 15px;border-radius:6px;cursor:pointer}' +
        'header{border-bottom:2px solid #2c6045;padding-bottom:12px;margin-bottom:15px}' +
        'h1{font-size:21px;margin:0 0 6px}header p{margin:0;color:#748476}' +
        'table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{border:1px solid #d5dfd7;padding:9px;text-align:left;vertical-align:top;overflow-wrap:anywhere}' +
        'th{background:#edf3ee;font-size:11px}th:first-child{width:23%}td:first-child{font-weight:bold}' +
        'tr:nth-child(even) td{background:#f9fbf9}.item{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #eaf0eb}' +
        '.item:last-child{border:0}.item img{max-width:44px;width:44px;height:44px;object-fit:contain;border:1px solid #e1e8e3;border-radius:4px}' +
        '.vazio{color:#aaa}@media print{.acoes{display:none}thead{display:table-header-group}tr{break-inside:avoid}}' +
        '</style></head><body><div class="acoes"><button onclick="window.print()">Imprimir / Salvar PDF</button></div>' +
        '<header><h1>' + escapar(titulo || 'Tabela de embalagens por quantidade') + '</h1>' +
        '<p>' + escapar(unitName) + ' · ' + new Date().toLocaleDateString('pt-BR') + '</p></header>' +
        '<table><thead><tr><th>Produto</th>' +
        faixas.map((faixa) => '<th>' + escapar(faixa.rotulo || 'Quantidade') + '</th>').join('') +
        '</tr></thead><tbody>' +
        validas.map((linha) => '<tr><td>' + escapar(linha.produto) + '</td>' +
          faixas.map((faixa) => '<td>' + celulaHTML(linha, faixa) + '</td>').join('') + '</tr>').join('') +
        '</tbody></table></body></html>';
      win.document.open();
      win.document.write(pagina);
      win.document.close();
      win.focus();
    };

    if (carregada !== currentUnit) {
      return <section className="emb-area"><h1>Organização das embalagens</h1>
        <p>{erro || 'Carregando tabela da unidade…'}</p>
        {erro && <button type="button" className="btn btn-secondary"
          onClick={() => window.location.reload()}>Tentar novamente</button>}
      </section>;
    }

    return <section className="emb-area">
      <header className="emb-cabecalho">
        <div>
          <div className="emb-sobretitulo">Controle de embalagens · {unitName}</div>
          <h1>Organização das embalagens</h1>
          <p>Produtos da Produção e embalagens de Cadastros, vinculados ao Supabase. Escolha as embalagens dentro de cada célula.</p>
        </div>
        <div className="emb-acoes">
          <button type="button" className="btn btn-secondary btn-sm" onClick={csv}>Baixar Excel (CSV)</button>
          <button type="button" className="btn btn-primary btn-sm" onClick={imprimir}>Imprimir / Salvar PDF</button>
        </div>
      </header>
      <div className="emb-status" role="status">{estado}{erro ? <span className="emb-erro"> — {erro}</span> : null}</div>

      <div className="emb-bloco">
        <div className="emb-linha-titulo">
          <div><h2>1. Embalagens cadastradas</h2>
            <p>Os itens classificados como Embalagem em Cadastros aparecem automaticamente. Aqui você só adiciona a foto.</p></div>
        </div>
        <div className="emb-adicionar emb-filtros">
          <input className="field field-md" value={buscaEmbalagem}
            onChange={(e) => setBuscaEmbalagem(e.target.value)} placeholder="Buscar embalagem no cadastro…"
            aria-label="Buscar embalagem"/>
          <span className="emb-contagem">{embalagensDisponiveis.length} embalagens cadastradas</span>
        </div>
        <div className="emb-galeria">
          {embalagensVisiveis.map((e) => <div className="emb-cartao" key={e.id}>
            <div className="emb-foto">
              {e.foto ? <img src={fotoSegura(e.foto)} alt={e.nome}/> : <span>Sem foto</span>}
            </div>
            <div className="emb-nome-cadastro" title={e.nome}>{e.nome}</div>
            <div className="emb-cartao-acoes">
              <label className="emb-upload">
                {e.foto ? 'Trocar foto' : '+ Enviar foto'}
                <input type="file" accept="image/png,image/jpeg,image/webp"
                  onChange={(evento) => {
                    const item = evento.target.files && evento.target.files[0];
                    carregarFoto(e.id, item);
                    evento.target.value = '';
                  }}/>
              </label>
              {e.foto && <button type="button" className="emb-excluir" onClick={() => apagarFoto(e.id)}
                aria-label={'Remover foto de ' + e.nome}>Remover foto</button>}
            </div>
          </div>)}
          {!embalagensVisiveis.length && <div className="emb-vazio">
            {embalagensDisponiveis.length ? 'Nenhuma embalagem corresponde à busca.' :
              'Nenhuma embalagem encontrada. Classifique os itens em Cadastros como Embalagem.'}
          </div>}
        </div>
      </div>

      <div className="emb-bloco">
        <div className="emb-linha-titulo">
          <div><h2>2. Tabela por quantidade</h2>
            <p>Produtos ativos de Produção aparecem automaticamente nas linhas. Escolha as embalagens em cada célula.</p></div>
          <div className="emb-acoes">
            <button type="button" className="btn btn-secondary btn-sm" onClick={() =>
              setFaixas((prev) => prev.length >= 20 ? prev : [...prev, { id: idNovo(), rotulo: 'Outra quantidade' }])}>
              + Coluna
            </button>
            <label className="emb-mostrar-inativos">
              <input type="checkbox" checked={mostrarInativos} onChange={(e) => setMostrarInativos(e.target.checked)}/>
              Incluir inativos
            </label>
          </div>
        </div>
        <label className="emb-rotulo-titulo">Título do relatório
          <input className="field field-md" maxLength={110} value={titulo}
            onChange={(e) => setTitulo(e.target.value)}/>
        </label>
        <div className="emb-adicionar emb-filtros">
          <input className="field field-md" value={buscaProduto}
            onChange={(e) => setBuscaProduto(e.target.value)} placeholder="Buscar produto da Produção…"
            aria-label="Buscar produto"/>
          <span className="emb-contagem">{produtosProducao.length} produtos de Produção</span>
        </div>
        <div className="emb-rolagem">
          <table className="emb-tabela emb-matriz">
            <thead>
              <tr>
                <th className="emb-col-produto">PRODUTO</th>
                {faixas.map((faixa) => <th key={faixa.id} className="emb-cabecalho-coluna">
                  <input className="emb-faixa-titulo" aria-label="Nome da coluna de quantidade"
                    maxLength={90} value={faixa.rotulo}
                    onChange={(e) => setFaixas((prev) => prev.map((f) =>
                      f.id === faixa.id ? { ...f, rotulo: e.target.value } : f))}/>
                  <span className="emb-ajuda-coluna">Quantas embalagens usar?</span>
                  <button type="button" className="emb-remover-coluna"
                    title="Remover esta coluna" aria-label={'Remover coluna ' + faixa.rotulo}
                    disabled={faixas.length <= 1} onClick={() => apagarColuna(faixa.id)}>×</button>
                </th>)}
                <th className="emb-col-excluir"></th>
              </tr>
            </thead>
            <tbody>
              {linhasVisiveis.map((linha) => <tr key={linha.id}>
                <td className="emb-col-produto">
                  <span className="emb-produto-do-cadastro" title={linha.produto}>{linha.produto}</span>
                </td>
                {faixas.map((faixa) => {
                  const lista = partes(linha, faixa.id);
                  const abertas = editando && editando.linha === linha.id && editando.faixa === faixa.id;
                  return <td key={faixa.id} className="emb-celula">
                    <div className="emb-itens-celula">
                      {lista.map(({ embalagem, quantidade }) =>
                        <div className="emb-chip" key={embalagem.id}>
                          {embalagem.foto
                            ? <img className="emb-chip-foto" src={fotoSegura(embalagem.foto)} alt=""/>
                            : <span className="emb-chip-foto emb-chip-sem-foto">□</span>}
                          <div className="emb-chip-conteudo">
                            <div title={embalagem.nome} className="emb-chip-nome">{embalagem.nome}</div>
                            <label className="emb-chip-qtd">
                              <span>Qtd.</span>
                              <input type="number" min="1" step="1" value={quantidade}
                                aria-label={'Quantidade de ' + embalagem.nome + ' para ' + linha.produto + ' em ' + faixa.rotulo}
                                onChange={(e) => alterarQuantidade(linha.id, faixa.id, embalagem.id, e.target.value)}/>
                            </label>
                          </div>
                          <button type="button" className="emb-chip-remover" title="Remover embalagem"
                            aria-label={'Remover ' + embalagem.nome + ' desta célula'}
                            onClick={() => excluirDaCelula(linha.id, faixa.id, embalagem.id)}>×</button>
                        </div>)}
                      {!lista.length && <div className="emb-celula-vazia">Nenhuma embalagem</div>}
                      {embalagensDisponiveis.length > 0
                        ? <div className="emb-adicao-celula">
                            {abertas && <select autoFocus className="emb-select-embalagem" value=""
                              aria-label={'Escolher embalagem para ' + linha.produto + ' em ' + faixa.rotulo}
                              onChange={(e) => {
                                adicionarNaCelula(linha.id, faixa.id, e.target.value);
                                setEditando(null);
                              }}>
                              <option value="">Escolha a embalagem…</option>
                              {embalagensDisponiveis.filter((e) => !lista.some((x) => x.embalagem.id === e.id))
                                .map((e) => <option key={e.id} value={e.id}>{e.nome}</option>)}
                            </select>}
                            <button className="emb-adicionar-na-celula" type="button"
                              disabled={lista.length >= embalagensDisponiveis.length}
                              onClick={() => setEditando(abertas ? null : { linha: linha.id, faixa: faixa.id })}>
                              {abertas ? 'Cancelar' : '+ Embalagem'}
                            </button>
                          </div>
                        : <span className="emb-celula-vazia">Nenhuma embalagem no cadastro</span>}
                    </div>
                  </td>;
                })}
                <td className="emb-col-excluir"></td>
              </tr>)}
              {!linhasVisiveis.length && <tr><td colSpan={faixas.length + 2} className="emb-vazio-celula">
                Nenhum produto da Produção encontrado com estes filtros.
              </td></tr>}
            </tbody>
          </table>
        </div>
        <div className="emb-rodape">
          <span>{linhasVisiveis.length} produtos exibidos · {faixas.length} faixas de quantidade · {embalagensDisponiveis.length} embalagens cadastradas</span>
          <div className="emb-acoes">
            <button type="button" className="btn btn-secondary btn-sm" onClick={csv}>Baixar Excel (CSV)</button>
            <button type="button" className="btn btn-primary btn-sm" onClick={imprimir}>Imprimir / Salvar PDF</button>
          </div>
        </div>
      </div>
    </section>;
  };
  window.PackagingMatrixView = PackagingMatrixView;
})();
