/* Navegação de volta para prévias HTML de impressão abertas pelo Controle Produ.
   Mantém o documento impresso intacto e funciona em celulares que não permitem fechar abas. */
(function () {
  'use strict';
  const nativeOpen = window.open;
  const returnUrl = window.location.href;
  window.open = function (url, ...rest) {
    const popup = nativeOpen.call(window, url, ...rest);
    // Apenas prévias HTML vazias abertas pelo próprio app. Links externos
    // (NF-e, fornecedores etc.) e visualizadores nativos de PDF não são alterados.
    if (!popup || String(url == null ? '' : url).trim() !== '') return popup;

    function addReturnControl() {
      try {
        if (popup.closed) return;
        const doc = popup.document;
        if (!doc || !doc.body || !doc.head) return;
        if (doc.querySelector('[data-preview-back], [data-preview-return]')) return;
        // Aguarda o relatório ser escrito para não criar botão em about:blank.
        if (!doc.body.children.length || !String(doc.body.textContent || '').trim()) return;

        const style = doc.createElement('style');
        style.textContent = '@media print { [data-preview-return] { display:none !important } }';
        doc.head.appendChild(style);
        const link = doc.createElement('a');
        link.setAttribute('data-preview-return', 'true');
        link.href = returnUrl;
        link.textContent = '← Voltar ao Controle Produ';
        link.setAttribute('aria-label', 'Voltar ao Controle Produ');
        link.style.cssText = 'position:fixed;top:14px;left:14px;z-index:2147483600;' +
          'display:inline-flex;justify-content:center;align-items:center;max-width:calc(100vw - 28px);' +
          'min-height:44px;box-sizing:border-box;padding:10px 14px;border-radius:9px;' +
          'border:1px solid #c8d4c8;background:#fff;color:#254735;' +
          'font:600 12px Arial,sans-serif;text-decoration:none;box-shadow:0 3px 14px #0002;';
        link.addEventListener('click', function (event) {
          try {
            if (popup.opener && !popup.opener.closed) {
              event.preventDefault();
              popup.opener.focus();
              popup.close();
              // Safari pode ignorar window.close(): nesse caso segue para a aplicação.
              if (!popup.closed) popup.location.assign(returnUrl);
            }
          } catch (error) {
            event.preventDefault();
            popup.location.assign(returnUrl);
          }
        });
        doc.body.insertBefore(link, doc.body.firstChild);
      } catch (error) {
        // A janela pode ter mudado para outro domínio ou sido fechada.
      }
    }

    try {
      popup.addEventListener('load', function () { setTimeout(addReturnControl, 0); });
    } catch (error) {}
    [100, 350, 800, 1600, 3200, 6000, 10000, 16000].forEach(function (ms) {
      setTimeout(addReturnControl, ms);
    });
    return popup;
  };
})();
