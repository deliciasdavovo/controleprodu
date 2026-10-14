/* Organizador de embalagens — componente isolado do Controle Produ.
   A versão atual do site usa Babel Standalone e React globais, sem bundler. */
(function () {
  const { useState, useEffect, useMemo, useRef } = React;

  const novoId = () => (window.crypto && window.crypto.randomUUID)
    ? window.crypto.randomUUID()
    : String(Date.now()) + '-' + Math.random().toString(36).slice(2);
  const somenteInteiro = (valor) => {
    if (valor === '') return '';
    const num = Number(valor);
    return Number.isFinite(num) ? Math.max(0, Math.floor(num)) : 0;
  };
  const inteiro = (valor) => Math.max(0, Number(valor) || 0);
  const escapar = (valor) => String(valor == null ? '' : valor).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
  const imagemSegura = (valor) =>
    (typeof valor === 'string' && valor.length < 300000 && /^data:image\/jpeg;base64,[A-Za-z0-9+/=]+$/.test(valor)) ? valor : '';
  const nomeArquivo = (texto) => String(texto || 'embalagens').normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '').slice(0,70);
  const guardarArquivo = (nome, conteudo, tipo) => {
    const url = URL.createObjectURL(new Blob([conteudo], { type: tipo }));
    const link = document.createElement('a');
    link.href = url;
    link.download = nome;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const comprimirFoto = async (arquivo) => {
    if (!arquivo || !arquivo.type.startsWith('image/')) throw new Error('Escolha uma imagem JPG, PNG ou WEBP.');
    if (arquivo.size > 8 * 1024 * 1024) throw new Error('A imagem deve ter até 8 MB.');
    const url = URL.createObjectURL(arquivo);
    try {
      const foto = new Image();
      foto.src = url;
      await foto.decode();
      const tela = document.createElement('canvas');
      const fator = Math.min(1, 460 / Math.max(foto.naturalWidth, foto.naturalHeight));
      tela.width = Math.max(1, Math.round(foto.naturalWidth * fator));
      tela.height = Math.max(1, Math.round(foto.naturalHeight * fator));
      const desenho = tela.getContext('2d');
      if (!desenho) throw new Error('Não foi possível preparar a foto.');
      desenho.fillStyle = '#ffffff';
      desenho.fillRect(0, 0, tela.width, tela.height);
      desenho.drawImage(foto, 0, 0, tela.width, tela.height);
      let dados = tela.toDataURL('image/jpeg', 0.72);
      if (dados.length > 160000) dados = tela.toDataURL('image/jpeg', 0.48);
      if (dados.length > 160000) throw new Error('Foto muito grande. Tente uma imagem menor.');
      return dados;
    } finally {
      URL.revokeObjectURL(url);
    }
  };

  const normalizar = (dados) => {
    const objeto = dados && typeof dados === 'object' && !Array.isArray(dados) ? dados : {};
    return {
      titulo: typeof objeto.titulo === 'string' ? objeto.titulo : 'Tabela de embalagens por quantidade',
      embalagens: Array.isArray(objeto.embalagens) ? objeto.embalagens.slice(0, 24).filter((x) => x && x.id).map((x) => ({
        id: String(x.id), nome: String(x.nome || ''), foto: imagemSegura(x.foto)
      })) : [],
      linhas: Array.isArray(objeto.linhas) ? objeto.linhas.slice(0, 500).filter((x) => x && x.id).map((x) => ({
        id: String(x.id), produto: String(x.produto || ''), quantidade: Math.max(1, inteiro(x.quantidade)),
        alocacoes: x.alocacoes && typeof x.alocacoes === 'object' && !Array.isArray(x.alocacoes) ? x.alocacoes : {}
      })) : []
    };
  };

  const PackagingMatrixView = ({ sb, currentUnit, unitName, products = [], separatedProducts = [], supplies = [] }) => {
    const [titulo, setTitulo] = useState('Tabela de embalagens por quantidade');
    const [embalagens, setEmbalagens] = useState([]);
    const [linhas, setLinhas] = useState([]);
    const [novaEmbalagem, setNovaEmbalagem] = useState('');
    const [carregada, setCarregada] = useState('');
    const [situacao, setSituacao] = useState('Carregando…');
    const [erro, setErro] = useState('');
    const sequenciaLeitura = useRef(0);
    const filaGravacao = useRef(Promise.resolve());
    const ultimoSalvo = useRef('');
    const unidadeAtual = useRef(currentUnit);
    unidadeAtual.current = currentUnit;

    const opcoesProdutos = useMemo(() => {
      const todos = [...products, ...separatedProducts, ...supplies]
        .map((item) => String(item.name || item.productName || '').trim())
        .filter(Boolean);
      return [...new Set(todos)].sort((a, b) => a.localeCompare(b, 'pt-BR'));
    }, [products, separatedProducts, supplies]);

    useEffect(() => {
      const idLeitura = ++sequenciaLeitura.current;
      setCarregada('');
      setSituacao('Carregando…');
      setErro('');
      if (!sb || !currentUnit) {
        setErro('Não foi possível conectar o organizador ao banco de dados.');
        return;
      }
      sb.from('packaging_matrices').select('layout').eq('unit_code', currentUnit).maybeSingle()
        .then(({ data, error }) => {
          if (idLeitura !== sequenciaLeitura.current) return;
          if (error) throw error;
          const atual = normalizar(data ? data.layout : null);
          setTitulo(atual.titulo);
          setEmbalagens(atual.embalagens);
          setLinhas(atual.linhas);
          ultimoSalvo.current = JSON.stringify(atual);
          setCarregada(currentUnit);
          setSituacao(data ? 'Salvo no Supabase' : 'Novo organizador');
        })
        .catch((e) => {
          if (idLeitura !== sequenciaLeitura.current) return;
          setErro('Não foi possível carregar as embalagens: ' + e.message);
          setSituacao('Erro ao carregar');
        });
      return () => { sequenciaLeitura.current += 1; };
    }, [sb, currentUnit]);

    const dados = useMemo(() => ({ titulo, embalagens, linhas }), [titulo, embalagens, linhas]);
    const json = useMemo(() => JSON.stringify(dados), [dados]);

    // Salva somente depois de terminar a leitura da unidade ativa.
    // A fila impede que requisições antigas sobrescrevam edições mais novas.
    useEffect(() => {
      if (carregada !== currentUnit || !sb || json === ultimoSalvo.current) return;
      setSituacao('Alterações pendentes…');
      const timer = setTimeout(() => {
        setSituacao('Salvando…');
        const unidadeDaGravacao = currentUnit;
        const registro = { unit_code: unidadeDaGravacao, layout: dados, updated_at: new Date().toISOString() };
        const promessa = filaGravacao.current.then(async () => {
          const { error } = await sb.from('packaging_matrices').upsert(registro, { onConflict: 'unit_code' });
          if (error) throw error;
        });
        filaGravacao.current = promessa.catch(() => {});
        promessa.then(() => {
          if (unidadeAtual.current === unidadeDaGravacao) {
            ultimoSalvo.current = json;
            setErro('');
            setSituacao('Salvo no Supabase');
          }
        }).catch((e) => {
          if (unidadeAtual.current === unidadeDaGravacao) {
            setErro('Não foi possível salvar: ' + e.message);
            setSituacao('Erro ao salvar');
          }
        });
      }, 700);
      return () => clearTimeout(timer);
    }, [json, carregada, currentUnit, sb]);

    const alterarLinha = (id, campos) => setLinhas((antigas) =>
      antigas.map((linha) => linha.id === id ? { ...linha, ...campos } : linha));
    const alterarCelula = (linhaId, embalagemId, valor) => setLinhas((antigas) =>
      antigas.map((linha) => linha.id === linhaId
        ? { ...linha, alocacoes: { ...linha.alocacoes, [embalagemId]: somenteInteiro(valor) } }
        : linha));
    // Uma linha representa UMA REGRA DE EMBALAGEM para uma quantidade exata.
    // Ex.: Croissant | 1 | 1 saquinho.
    //      Croissant | 2 | 1 bandejinha + 1 saquinho.
    // A quantidade NÃO multiplica os materiais: escolhe uma combinação diferente.
    const linhasValidas = linhas.filter((linha) => linha.produto.trim() && inteiro(linha.quantidade) >= 1);
    const composicaoDe = (linha) => embalagens
      .map((embalagem) => ({ nome: embalagem.nome.trim(), qtd: inteiro(linha.alocacoes[embalagem.id]) }))
      .filter((item) => item.qtd > 0)
      .map((item) => item.qtd + ' ' + item.nome)
      .join(' + ');
    const contagemRegras = (produto, quantidade, excetoId) =>
      linhas.filter((linha) => linha.id !== excetoId
        && linha.produto.trim().toLocaleLowerCase('pt-BR') === produto.trim().toLocaleLowerCase('pt-BR')
        && inteiro(linha.quantidade) === inteiro(quantidade)).length;
    const adicionarRegra = (linhaOrigem) => {
      setLinhas((anteriores) => {
        const index = linhaOrigem ? anteriores.findIndex((x) => x.id === linhaOrigem.id) : -1;
        const produto = linhaOrigem ? linhaOrigem.produto : '';
        const usadas = new Set(anteriores.filter((x) => x.produto.trim().toLocaleLowerCase('pt-BR') === produto.trim().toLocaleLowerCase('pt-BR'))
          .map((x) => inteiro(x.quantidade)));
        let quantidade = linhaOrigem ? inteiro(linhaOrigem.quantidade) + 1 : 1;
        while (usadas.has(quantidade)) quantidade += 1;
        const regra = { id: novoId(), produto, quantidade, alocacoes: {} };
        const proximas = anteriores.slice();
        proximas.splice(index >= 0 ? index + 1 : proximas.length, 0, regra);
        return proximas;
      });
    };

    const adicionarFoto = async (id, arquivo) => {
      if (!arquivo) return;
      try {
        const foto = await comprimirFoto(arquivo);
        setEmbalagens((antigas) => antigas.map((embalagem) =>
          embalagem.id === id ? { ...embalagem, foto } : embalagem));
        setErro('');
      } catch (e) {
        setErro(e.message);
      }
    };
    const excluirEmbalagem = (id) => {
      if (!window.confirm('Excluir esta embalagem e sua coluna da tabela?')) return;
      setEmbalagens((antigas) => antigas.filter((embalagem) => embalagem.id !== id));
      setLinhas((antigas) => antigas.map((linha) => {
        const alocacoes = { ...linha.alocacoes };
        delete alocacoes[id];
        return { ...linha, alocacoes };
      }));
    };

    const baixarCSV = () => {
      if (!linhasValidas.length) return window.alert('Cadastre um produto e a quantidade correspondente antes de exportar.');
      const linhasCSV = [
        [titulo || 'Tabela de embalagens por quantidade'],
        ['Unidade', unitName],
        ['Data', new Date().toLocaleDateString('pt-BR')],
        ['Orientação', 'Cada linha mostra como embalar aquela quantidade específica de produtos. Os números nas colunas são embalagens para a combinação inteira, não por unidade.'],
        [],
        ['Produto', 'Quantidade de produtos', 'Embalagem utilizada', ...embalagens.map((x) => x.nome)],
        ...linhasValidas.map((linha) => [
          linha.produto,
          inteiro(linha.quantidade),
          composicaoDe(linha) || 'Embalagem ainda não definida',
          ...embalagens.map((item) => inteiro(linha.alocacoes[item.id]) || '')
        ])
      ];
      const celulaCSV = (dado) => {
        let texto = String(dado == null ? '' : dado);
        if (/^[\s]*[=+\-@]/.test(texto)) texto = "'" + texto;
        return '"' + texto.replace(/"/g, '""') + '"';
      };
      guardarArquivo(nomeArquivo(titulo || 'tabela-embalagens') + '.csv', '\uFEFF' +
        linhasCSV.map((linha) => linha.map(celulaCSV).join(';')).join('\r\n'),
        'text/csv;charset=utf-8;');
    };

    const imprimir = () => {
      if (!linhasValidas.length) return window.alert('Cadastre um produto e a quantidade correspondente antes de gerar o relatório.');
      const janela = window.open('', '_blank');
      if (!janela) return window.alert('Autorize a janela de impressão para salvar o relatório em PDF.');
      const cabecalho = embalagens.map((item) =>
        '<th><div class="foto">' +
        (imagemSegura(item.foto) ? '<img alt="" src="' + item.foto + '">' : '<span>SEM FOTO</span>') +
        '</div><strong>' + escapar(item.nome) + '</strong></th>').join('');
      const corpo = linhasValidas.map((linha) => '<tr>' +
        '<td class="produto">' + escapar(linha.produto) + '</td>' +
        '<td class="numero">' + inteiro(linha.quantidade) + '</td>' +
        '<td class="descricao">' + escapar(composicaoDe(linha) || 'Não definida') + '</td>' +
        embalagens.map((item) => '<td class="numero">' + (inteiro(linha.alocacoes[item.id]) || '—') + '</td>').join('') +
        '</tr>').join('');
      const pagina = '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>' +
        escapar(titulo) + '</title><style>' +
        '@page{size:A4 landscape;margin:12mm}*{box-sizing:border-box}body{font:12px Arial,sans-serif;color:#21362b;margin:0}' +
        'header{border-bottom:2px solid #2c6045;padding-bottom:14px;margin-bottom:16px}' +
        'h1{font-size:22px;margin:0 0 7px}p{margin:0;color:#64756a}table{border-collapse:collapse;width:100%;table-layout:auto}' +
        'th,td{border:1px solid #cedbd1;padding:9px 8px;text-align:center;vertical-align:middle;overflow-wrap:anywhere}' +
        'th{background:#edf3ee;font-size:10px}th:first-child,td:first-child{text-align:left;min-width:110px}' +
        'th:nth-child(2),td:nth-child(2){width:82px}th:nth-child(3),td:nth-child(3){text-align:left;min-width:150px}' +
        '.produto{font-weight:700}.descricao{color:#385a43}.numero{font-weight:700;font-size:12px}' +
        'tbody tr:nth-child(even){background:#f8faf8}.foto{height:55px;display:flex;justify-content:center;align-items:center;margin-bottom:4px}' +
        '.foto img{max-width:62px;max-height:52px;object-fit:contain}.foto span{color:#b3bcb5;font-size:9px}' +
        '.acoes{text-align:right;margin:0 0 18px}.acoes button{padding:9px 14px;border:0;border-radius:6px;background:#28563c;color:white;cursor:pointer}' +
        '@media print{.acoes{display:none}thead{display:table-header-group}tr{page-break-inside:avoid}}' +
        '</style></head><body><div class="acoes"><button onclick="window.print()">Imprimir / Salvar PDF</button></div>' +
        '<header><h1>' + escapar(titulo || 'Tabela de embalagens por quantidade') + '</h1><p>' +
        escapar(unitName) + ' · ' + new Date().toLocaleDateString('pt-BR') +
        ' · A embalagem depende da quantidade de produtos.</p></header>' +
        '<table><thead><tr><th>PRODUTO</th><th>QUANTIDADE DE PRODUTOS</th>' +
        '<th>COMPOSIÇÃO DA EMBALAGEM</th>' + cabecalho +
        '</tr></thead><tbody>' + corpo + '</tbody></table></body></html>';
      janela.document.open();
      janela.document.write(pagina);
      janela.document.close();
      janela.focus();
    };

    if (carregada !== currentUnit) {
      return <section className="emb-area">
        <h1>Organização das embalagens</h1>
        <p>{erro || 'Carregando embalagens da unidade…'}</p>
        {erro && <button type="button" className="btn btn-secondary" onClick={() => window.location.reload()}>Tentar novamente</button>}
      </section>;
    }

    return (
      <section className="emb-area">
        <div className="emb-cabecalho">
          <div>
            <span className="emb-sobretitulo">Controle de embalagens · {unitName}</span>
            <h1>Organização das embalagens</h1>
            <p>A quantidade define como o produto deve ser embalado: 1 croissant usa 1 saquinho; 2 croissants usam 1 bandejinha + 1 saquinho.</p>
          </div>
          <div className="emb-acoes">
            <button className="btn btn-secondary btn-sm" type="button" onClick={baixarCSV}>Baixar Excel (CSV)</button>
            <button className="btn btn-primary btn-sm" type="button" onClick={imprimir}>Imprimir / Salvar PDF</button>
          </div>
        </div>
        <div className="emb-status" role="status">{situacao}{erro ? <span className="emb-erro"> — {erro}</span> : null}</div>

        <div className="emb-bloco">
          <div className="emb-linha-titulo">
            <div><h2>1. Cadastro de embalagens</h2><p>Cadastre cada embalagem uma vez, com nome e foto. Ela aparecerá nas colunas da tabela.</p></div>
          </div>
          <form className="emb-adicionar" onSubmit={(e) => {
            e.preventDefault();
            const nome = novaEmbalagem.trim();
            if (!nome) return;
            setEmbalagens((antigas) => [...antigas, { id: novoId(), nome, foto: '' }]);
            setNovaEmbalagem('');
          }}>
            <input className="field field-md" value={novaEmbalagem}
              onChange={(e) => setNovaEmbalagem(e.target.value)}
              placeholder="Ex.: Caixa bolo família, bandeja B03, saco kraft…" maxLength={90}
              aria-label="Nome da nova embalagem" />
            <button type="submit" className="btn btn-secondary btn-sm" disabled={!novaEmbalagem.trim()}>+ Embalagem</button>
          </form>
          <div className="emb-galeria">
            {embalagens.map((embalagem) => <div className="emb-cartao" key={embalagem.id}>
              <div className="emb-foto">
                {embalagem.foto ? <img src={imagemSegura(embalagem.foto)} alt={embalagem.nome} /> :
                  <span>Sem foto</span>}
              </div>
              <input className="field field-sm" aria-label="Nome da embalagem"
                maxLength={90} value={embalagem.nome}
                onChange={(e) => setEmbalagens((antigas) => antigas.map((x) =>
                  x.id === embalagem.id ? { ...x, nome: e.target.value } : x))} />
              <div className="emb-cartao-acoes">
                <label className="emb-upload">
                  {embalagem.foto ? 'Trocar foto' : '+ Enviar foto'}
                  <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => {
                    const arquivo = e.target.files && e.target.files[0];
                    adicionarFoto(embalagem.id, arquivo);
                    e.target.value = '';
                  }} />
                </label>
                <button type="button" className="emb-excluir" onClick={() => excluirEmbalagem(embalagem.id)}
                  aria-label={'Excluir ' + embalagem.nome}>Excluir</button>
              </div>
            </div>)}
            {!embalagens.length && <div className="emb-vazio">Adicione a primeira embalagem acima. Ela aparecerá como uma coluna na tabela.</div>}
          </div>
        </div>

        <div className="emb-bloco">
          <div className="emb-linha-titulo">
            <div><h2>2. Regra de embalagem por quantidade</h2><p>Crie <strong>uma linha para cada quantidade</strong> do mesmo produto. Ex.: Croissant / 1 / saquinho; Croissant / 2 / bandejinha + saquinho. Cada célula indica quantas embalagens usar nessa situação.</p></div>
            <button type="button" className="btn btn-secondary btn-sm"
              onClick={() => adicionarRegra(null)}>+ Produto / quantidade</button>
          </div>
          <label className="emb-rotulo-titulo">Título do relatório
            <input className="field field-md" value={titulo} onChange={(e) => setTitulo(e.target.value)}
              maxLength={110} placeholder="Tabela de embalagens por quantidade" />
          </label>
          <div className="emb-rolagem">
            <table className="emb-tabela">
              <thead>
                <tr><th className="emb-col-produto">Produto / Regra</th><th className="emb-col-quantidade">Quantidade <small className="emb-th-ajuda">de produtos</small></th>
                  {embalagens.map((item) => <th key={item.id} className="emb-col-embalagem">
                    <div className="emb-th-foto">{item.foto && <img src={imagemSegura(item.foto)} alt="" />}</div>
                    <span>{item.nome}</span><small className="emb-th-ajuda">quantidade de embalagens</small>
                  </th>)}
                  <th className="emb-col-excluir" aria-label="Ações"></th>
                </tr>
              </thead>
              <tbody>
                {linhas.map((linha) => <tr key={linha.id}>
                  <td className="emb-col-produto">
                    <input className="emb-input-produto" type="text"
                      aria-label="Produto" list="emb-produtos-cadastrados" value={linha.produto}
                      placeholder="Selecione ou digite" maxLength={130}
                      onChange={(e) => alterarLinha(linha.id, { produto: e.target.value })} />
                    <div className="emb-composicao">{composicaoDe(linha) || 'Defina as embalagens para esta quantidade'}</div>
                    {contagemRegras(linha.produto, linha.quantidade, linha.id) > 0 &&
                      <div className="emb-regra-alerta">Quantidade repetida para o mesmo produto</div>}
                    <button type="button" className="emb-adicionar-variacao"
                      title={'Criar outra regra de embalagem para ' + (linha.produto || 'este produto')}
                      onClick={() => adicionarRegra(linha)}>+ Outra quantidade</button>
                  </td>
                  <td><input className="emb-input-numero" type="number" min="1" step="1"
                    aria-label={'Quantidade de produtos nesta regra para ' + (linha.produto || 'produto')}
                    title="Ex.: 1 croissant usa saquinho; 2 croissants usam bandejinha mais saquinho."
                    value={linha.quantidade} placeholder="1"
                    onChange={(e) => alterarLinha(linha.id, { quantidade: e.target.value === '' ? '' : Math.max(1, somenteInteiro(e.target.value)) })} /></td>
                  {embalagens.map((embalagem) => <td key={embalagem.id}>
                    <div className="emb-quantidade-por-produto">
                      <input className="emb-input-numero" type="number" min="0" step="1"
                        aria-label={'Quantidade de ' + embalagem.nome + ' para ' + (linha.quantidade || '?') + ' unidades de ' + (linha.produto || 'produto')}
                        title={'Quantas unidades da embalagem ' + embalagem.nome + ' são usadas para embalar ' + linha.quantidade + ' unidades deste produto?'}
                        value={linha.alocacoes[embalagem.id] == null ? '' : linha.alocacoes[embalagem.id]}
                        placeholder="—" onChange={(e) => alterarCelula(linha.id, embalagem.id, e.target.value)} />
                      {inteiro(linha.alocacoes[embalagem.id]) > 0 && <small className="emb-por-produto">nesta quantidade</small>}
                    </div>
                  </td>)}
                  <td className="emb-col-excluir">
                    <button type="button" className="emb-remover-linha" title="Remover linha"
                      onClick={() => setLinhas((anteriores) => anteriores.filter((x) => x.id !== linha.id))}>×</button>
                  </td>
                </tr>)}
                {!linhas.length && <tr><td colSpan={embalagens.length + 3} className="emb-vazio-celula">Clique em + Produto / quantidade para cadastrar a primeira regra.</td></tr>}
              </tbody>

            </table>
            <datalist id="emb-produtos-cadastrados">{opcoesProdutos.map((x) => <option key={x} value={x} />)}</datalist>
          </div>
          <div className="emb-rodape">
            <span>{linhas.length} regras por quantidade · {embalagens.length} tipos de embalagem</span>
            <div className="emb-acoes">
              <button type="button" className="btn btn-secondary btn-sm" onClick={baixarCSV}>Baixar Excel (CSV)</button>
              <button type="button" className="btn btn-primary btn-sm" onClick={imprimir}>Imprimir / Salvar PDF</button>
            </div>
          </div>
        </div>
      </section>
    );
  };

  window.PackagingMatrixView = PackagingMatrixView;
})();
