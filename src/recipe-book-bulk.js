/* Livro completo ou por categoria usando o mesmo formato da ficha individual. */
(function () {
  function install() {
    document.querySelectorAll('div.t-overline').forEach(title => {
      if (title.textContent.trim() !== 'Fichas técnicas') return;
      const card = title.closest('.card');
      if (!card || card.querySelector('[data-export-book]')) return;
      const select = [...card.querySelectorAll('select')]
        .find(element => [...element.options].some(option => option.value === 'todos'));
      if (!select) return;

      const holder = document.createElement('div');
      holder.dataset.exportBook = 'true';
      holder.style.cssText = 'display:flex;gap:9px;flex-wrap:wrap;margin-top:11px';
      function button(label, readCategory, primary) {
        const el = document.createElement('button');
        el.type = 'button';
        el.textContent = label;
        el.className = 'btn ' + (primary ? 'btn-primary' : 'btn-secondary') + ' btn-sm';
        el.style.cssText = 'border-radius:8px;padding:10px 14px;font-size:12px;cursor:pointer';
        el.addEventListener('click', async () => {
          const previous = el.textContent;
          el.disabled = true;
          el.textContent = 'Preparando PDF…';
          try {
            if (!window.ControleProduLivro) throw Error('Gerador não disponível. Atualize a página.');
            await window.ControleProduLivro.openBook({ category: readCategory ? select.value : 'todos' });
          } catch (error) { window.alert(error.message || error); }
          finally { el.disabled = false; el.textContent = previous; }
        });
        return el;
      }
      holder.append(button('PDF da categoria selecionada', true, false), button('Livro completo · PDF', false, true));
      title.parentElement.appendChild(holder);
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