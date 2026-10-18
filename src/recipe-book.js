/* Livro individual: mesmo layout A4 vertical do livro completo. */
window.abrirLivroReceita = function({ produto }) {
  if (!window.ControleProduLivro) {
    window.alert('O gerador de receitas ainda não carregou. Atualize a página.');
    return;
  }
  return window.ControleProduLivro.openBook({ productName: produto?.name });
};
(function () {
  function install() {
    document.querySelectorAll('[role="dialog"][aria-label^="Ficha técnica de "]').forEach(dialog => {
      if (dialog.querySelector('[data-recipe-book-single]')) return;
      const name = dialog.getAttribute('aria-label').replace(/^Ficha técnica de\s*/i, '').trim();
      const title = dialog.querySelector('h3');
      if (!title || !name) return;
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.recipeBookSingle = 'true';
      button.className = 'btn btn-secondary btn-sm';
      button.textContent = 'Receita em PDF';
      button.style.cssText = 'margin:7px 0;background:#294b38;color:white;border:0;border-radius:8px;padding:9px 14px;font-size:12px;cursor:pointer';
      button.addEventListener('click', () => window.ControleProduLivro.openBook({ productName: name }));
      title.parentElement?.appendChild(button);
    });
  }
  let scheduled = false;
  new MutationObserver(() => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; install(); });
  }).observe(document.documentElement, { childList: true, subtree: true });
  install();
})();