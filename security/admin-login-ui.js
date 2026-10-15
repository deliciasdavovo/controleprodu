/* Tela de autenticação para a versão de testes.
   Requer window.supabase.createClient e window.ControleProduAdminAuth.
   Não habilitar em produção antes de configurar RLS. */
(function () {
  'use strict';
  window.ControleProduLogin = {
    mount: function (container, client, email, onAuthenticated) {
      if (!container || !client || !email) throw new Error('Login não configurado.');
      container.replaceChildren();
      const form = document.createElement('form');
      form.style.cssText = 'max-width:360px;margin:12vh auto;padding:32px;border:1px solid #dce6dc;border-radius:16px;font-family:Manrope,Arial,sans-serif;background:white';
      const heading = document.createElement('h1');
      heading.textContent = 'Controle Produ';
      heading.style.cssText = 'color:#2f5d45;font-size:24px;margin:0 0 10px';
      const desc = document.createElement('p');
      desc.textContent = 'Acesso administrativo';
      desc.style.cssText = 'color:#59675b;margin:0 0 24px';
      const label = document.createElement('label');
      label.textContent = 'Senha';
      label.style.cssText = 'display:block;font-size:14px;margin-bottom:8px';
      const input = document.createElement('input');
      input.type = 'password';
      input.autocomplete = 'current-password';
      input.required = true;
      input.minLength = 8;
      input.style.cssText = 'width:100%;box-sizing:border-box;padding:12px;border:1px solid #a5b9a9;border-radius:8px';
      const button = document.createElement('button');
      button.type = 'submit';
      button.textContent = 'Entrar';
      button.style.cssText = 'width:100%;padding:13px;margin-top:20px;border:0;border-radius:8px;background:#2f5d45;color:white;cursor:pointer';
      const error = document.createElement('p');
      error.setAttribute('role','alert');
      error.style.cssText = 'color:#a33333;font-size:13px;min-height:20px';
      form.append(heading,desc,label,input,button,error);
      container.append(form);
      form.addEventListener('submit',async function (event) {
        event.preventDefault();
        button.disabled = true;
        error.textContent = '';
        try {
          const session = await window.ControleProduAdminAuth.signIn(client,email,input.value);
          input.value = '';
          if (typeof onAuthenticated === 'function') onAuthenticated(session);
        } catch (e) {
          error.textContent = 'Não foi possível entrar. Confira a senha e tente novamente.';
        } finally {
          button.disabled = false;
        }
      });
      return form;
    }
  };
})();
