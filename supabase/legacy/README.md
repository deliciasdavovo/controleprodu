# Migração do banco legado — backup 01/09/2026

Este repositório é público. O dump completo do Supabase/PostgreSQL e os SQLs contendo dados comerciais reais **não devem ser versionados aqui**.

## Fonte de verdade

A estrutura atual do banco está em `supabase/schema.sql`. Antes de qualquer importação de dados antigos, rode a versão atual desse arquivo no SQL Editor do Supabase.

## Mapeamento do backup antigo

| Banco antigo | Estrutura atual |
| --- | --- |
| `produtos` de fabricação | `products` |
| `produtos` de revenda realmente vendáveis | `products` + `separated_products` |
| itens antigos marcados como revenda mas sem preço de venda | `supplies` quando eram matéria-prima/compras |
| `ingredientes` | `supplies` |
| `ingrediente_compras` | `supply_purchases` |
| várias linhas em `receitas` do mesmo produto | uma única linha em `recipes` |
| `receita_itens` | `recipe_items` |
| `historico_producao` | `production_records` e, quando havia quantidade vendida, `sale_records` |
| `perdas` | `loss_records` |

## O que não é importado automaticamente

- schemas internos do Supabase (`auth`, `storage`, `realtime`), roles e configurações do cluster;
- vitrine atual, `fechamentos` e `vitrine_padrao` antigos, porque o app atual usa outro desenho físico de slots;
- `produto_compras`: o backup de 01/09/2026 contém 0 linhas nessa tabela, portanto não existe histórico antigo de compra de revenda com fornecedor/data para recuperar.

## Ajustes feitos na conversão

- categorias antigas são convertidas para as categorias oficiais atuais;
- `Outro` no responsável vira campo vazio;
- o campo antigo `fatia` vira `variation_factor` quando era a equivalência do insumo;
- nomes duplicados no legado são unidos no mesmo produto atual;
- fichas antigas são consolidadas por produto;
- produto vendido por kg com peso por unidade mantém a equivalência `1 un = X g`;
- datas claramente inválidas do legado não são reaproveitadas;
- estoques atuais não são inventados durante a migração.

## Segurança

Arquivos `*.backup`, `*.backup.gz`, dumps `db_cluster-*.gz` e seeds privados estão cobertos pelo `.gitignore` do projeto. O SQL privado de importação deve ser guardado fora deste repositório público e executado diretamente no Supabase.
