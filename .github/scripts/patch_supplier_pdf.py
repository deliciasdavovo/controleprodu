from pathlib import Path

path = Path("index.html")
text = path.read_text(encoding="utf-8")
original = text


def require(condition, message):
    if not condition:
        raise SystemExit(message)


# 1) O gerador precisa saber qual visualização está selecionada.
old_signature = """      const htmlRelatorioCompletoFornecedores = ({
        unidadeNome,
        filtros,
        compras,
        itens,
        fornecedores,
        extrato,
        totalComprasFiltradas
      }) => {"""
new_signature = """      const htmlRelatorioCompletoFornecedores = ({
        unidadeNome,
        filtros,
        visao,
        compras,
        itens,
        fornecedores,
        extrato,
        totalComprasFiltradas
      }) => {"""
require(old_signature in text, "Assinatura do relatório completo não encontrada")
text = text.replace(old_signature, new_signature, 1)

# 2) Insere a visualização principal logo depois das linhas de compras já calculadas.
func_pos = text.find("const htmlRelatorioCompletoFornecedores = ({")
compras_pos = text.find("const linhasCompras = extrato.map", func_pos)
require(compras_pos >= 0, "linhasCompras não encontrada")
compras_end = text.find(".join('');", compras_pos)
require(compras_end >= 0, "Fim de linhasCompras não encontrado")
compras_end += len(".join('');")

visualizacao_js = r'''

        // O relatório completo acompanha a MESMA visualização escolhida na
        // página. Busca, categoria, período e demais filtros já chegam em
        // `compras`; aqui só muda a forma de apresentar os mesmos dados.
        const blocosFornecedores = fornecedores.map((f) => {
          const comprasDoFornecedor = [...f.lista].sort((a, b) => {
            const d = (b.data || '').localeCompare(a.data || '');
            return d !== 0 ? d : (b.criadoEm || '').localeCompare(a.criadoEm || '');
          });
          const linhas = comprasDoFornecedor.map((c) => `<tr>
            <td>${c.data ? formatDateBR(c.data) : '—'}</td>
            <td><b>${escaparHtml(c.item)}</b><small>${escaparHtml(c.tipo)}</small></td>
            <td class="num">${numeroCurtoBR(c.qty)} ${escaparHtml(c.unidade)}</td>
            <td class="num forte">${formatCurrencyBR(c.cost)}</td>
            <td class="num">${c.custoUnit > 0 ? formatPrecoInsumo(c.custoUnit, c.unidade) : '—'}</td>
          </tr>`).join('');
          return `<div class="grupo-fornecedor">
            <div class="grupo-fornecedor-cabecalho">
              <div class="grupo-fornecedor-nome">
                <b>${f.nome === 'Sem fornecedor' ? '<span class="quieto">Sem fornecedor</span>' : escaparHtml(f.nome)}</b>
                <small>${f.lista.length} ${f.lista.length === 1 ? 'compra' : 'compras'} · ${f.itens} ${f.itens === 1 ? 'item' : 'itens'}</small>
              </div>
              <div><span>Total filtrado</span><b>${formatCurrencyBR(f.total)}</b></div>
              <div><span>Última compra</span><b>${f.recente ? formatDateBR(f.recente) : '—'}</b></div>
            </div>
            <table class="t-fornecedor-compras">
              <thead><tr><th>Data</th><th>Item</th><th class="num">Qtd.</th><th class="num">Valor pago</th><th class="num">Preço</th></tr></thead>
              <tbody>${linhas || '<tr><td colspan="5" class="quieto">Nenhuma compra neste grupo.</td></tr>'}</tbody>
            </table>
          </div>`;
        }).join('');

        const secaoVisualizacao = visao === 'fornecedor'
          ? `<section>
              <h2>Por fornecedor (${fornecedores.length})</h2>
              <p class="nota">Os fornecedores estão na mesma ordem escolhida na página e cada grupo mostra somente as compras que passaram pelos filtros atuais.</p>
              ${blocosFornecedores || '<p class="quieto">Nenhum fornecedor nos filtros atuais.</p>'}
            </section>`
          : visao === 'compra'
            ? `<section>
                <h2>Por compra (${extrato.length}${extrato.length < totalComprasFiltradas ? ' de ' + totalComprasFiltradas : ''})</h2>
                <p class="nota">Mesma ordenação e mesma opção de quantidade de compras selecionadas na página.</p>
                <table class="t-compras"><thead><tr><th>Data</th><th>Item</th><th>Fornecedor</th><th class="num">Qtd.</th><th class="num">Valor pago</th><th class="num">Preço</th></tr></thead>
                <tbody>${linhasCompras || '<tr><td colspan="6" class="quieto">Nenhuma compra nos filtros atuais.</td></tr>'}</tbody></table>
              </section>`
            : `<section>
                <h2>Por item (${itens.length})</h2>
                <p class="nota">Mesma ordenação da página. As três compras mais recentes, a variação e a comparação de fornecedores respeitam os filtros atuais.</p>
                ${tabelasItensPorCategoria || '<p class="quieto">Nenhum item nos filtros atuais.</p>'}
              </section>`;
'''
text = text[:compras_end] + visualizacao_js + text[compras_end:]

# 3) Estilos para os grupos de fornecedor no PDF.
css_marker = """            .t-compras th:nth-child(5), .t-compras th:nth-child(6) { width: 16%; }
"""
require(css_marker in text, "Âncora CSS do relatório não encontrada")
css_extra = css_marker + """            .grupo-fornecedor { margin: 10px 0 16px; }
            .grupo-fornecedor-cabecalho { display: grid; grid-template-columns: minmax(0, 1fr) 150px 120px; gap: 8px; align-items: center; padding: 8px 9px; background: #ececea; border: 1px solid #cfcfcb; border-bottom: 0; break-after: avoid; page-break-after: avoid; }
            .grupo-fornecedor-cabecalho > div:not(.grupo-fornecedor-nome) { text-align: right; }
            .grupo-fornecedor-cabecalho span, .grupo-fornecedor-cabecalho small { display: block; color: #666; font-size: 7.5pt; }
            .grupo-fornecedor-cabecalho b { display: block; font-size: 10pt; }
            .grupo-fornecedor-nome b { font-size: 11pt; }
            .t-fornecedor-compras th:nth-child(1) { width: 12%; }
            .t-fornecedor-compras th:nth-child(2) { width: 38%; }
            .t-fornecedor-compras th:nth-child(3) { width: 14%; }
            .t-fornecedor-compras th:nth-child(4), .t-fornecedor-compras th:nth-child(5) { width: 18%; }
"""
text = text.replace(css_marker, css_extra, 1)

# 4) O corpo do relatório deixa de mostrar todas as visões ao mesmo tempo.
# A visão selecionada vira o bloco principal; categoria e mês continuam como
# resumos complementares do relatório completo.
html_return_pos = text.find("return `<!doctype html>", func_pos)
require(html_return_pos >= 0, "Início do HTML do relatório não encontrado")
start_marker = """          <div class="duas">
            <section>
              <h2>Resumo por categoria</h2>
"""
start = text.find(start_marker, html_return_pos)
end_marker = """          <footer>
            Este relatório usa os filtros que estavam aplicados na aba Fornecedores no momento da geração.
"""
end = text.find(end_marker, start)
require(start >= 0 and end >= 0, "Bloco principal do relatório não encontrado")

new_body = r'''          ${secaoVisualizacao}

          <div class="duas">
            <section>
              <h2>Resumo por categoria</h2>
              <table><thead><tr><th>Categoria</th><th class="num">Compras</th><th class="num">Itens</th><th class="num">Total</th></tr></thead>
              <tbody>${linhasCategoria || '<tr><td colspan="4" class="quieto">Sem dados.</td></tr>'}</tbody></table>
            </section>
            <section>
              <h2>Resumo por mês</h2>
              <table><thead><tr><th>Mês</th><th class="num">Compras</th><th class="num">Itens</th><th class="num">Forn.</th><th class="num">Total</th></tr></thead>
              <tbody>${linhasMes || '<tr><td colspan="5" class="quieto">Sem compras com data.</td></tr>'}</tbody></table>
            </section>
          </div>

'''
text = text[:start] + new_body + text[end:]

# 5) Passa a visualização atual para o gerador.
call_pos = text.find("janela.document.write(htmlRelatorioCompletoFornecedores({", func_pos)
require(call_pos >= 0, "Chamada do relatório completo não encontrada")
call_end = text.find("}));", call_pos)
require(call_end >= 0, "Fim da chamada do relatório não encontrado")
call_block = text[call_pos:call_end]
old_call_part = """            filtros,
            compras,
"""
require(old_call_part in call_block, "Parâmetros filtros/compras não encontrados na chamada")
call_block = call_block.replace(old_call_part, """            filtros,
            visao,
            compras,
""", 1)
text = text[:call_pos] + call_block + text[call_end:]

# Sanidade: cada inserção importante precisa existir uma única vez.
require(text.count("const secaoVisualizacao = visao === 'fornecedor'") == 1, "secaoVisualizacao duplicada/ausente")
require(text.count("grupo-fornecedor-cabecalho") >= 3, "CSS/HTML do grupo de fornecedor ausente")
require(text != original, "Nenhuma alteração foi aplicada")

path.write_text(text, encoding="utf-8")
print("Supplier PDF patch applied successfully")
