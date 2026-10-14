# Controle Produ — Delícias da Vovó

Sistema de compras, fornecedores, cadastro, equivalência, CMV e vitrine.

## Estrutura

- `index.html`: página de entrada, carregamento das bibliotecas e interface de inicialização.
- `styles/main.css`: estilos da aplicação, preservados na mesma ordem em que eram aplicados.
- `src/app.jsx`: lógica React, telas e integrações. Separado do HTML sem alterar as regras de negócio.
- `supabase/functions/`: funções de integração.
- `supabase/migrations/` e `supabase/schema.sql`: estrutura do banco de dados.

## Validação para evitar a tela branca

Antes de publicar uma alteração em `src/app.jsx`, valide a sintaxe JSX com esbuild:

```bash
npx --yes esbuild@0.25.12 src/app.jsx --loader:.jsx=jsx --outfile=/tmp/controleprodu-validado.js
```

O workflow `validar-jsx.yml` executa essa verificação automaticamente nas alterações do GitHub. Ele verifica sintaxe, **não** substitui testes do sistema no navegador.

### Histórico da reorganização

Em 14/10/2026, o HTML/CSS/React foram separados preservando a ordem do código. Corrigida uma chave solta na célula de data do preço atual em Fornecedores, que impedia a compilação JSX. O cadastro, equivalências e banco Supabase não tiveram alterações de regras de negócio nesta etapa.

**Próximo passo:** refatoração gradual do arquivo `src/app.jsx` em componentes e serviços com testes de integração; não dividir arbitrariamente código que compartilha estado.
