/* Login administrativo — ativar somente depois de criar usuário no Supabase Auth.
 * O e-mail é um identificador público, NÃO uma credencial secreta.
 * A proteção real depende de políticas RLS no banco; ocultar a interface não basta.
 */
(function () {
  'use strict';
  window.ControleProduAdminAuth = {
    async signIn(supabaseClient, adminEmail, password) {
      if (!supabaseClient || !adminEmail || !password) throw new Error('Configuração de acesso incompleta.');
      const { data, error } = await supabaseClient.auth.signInWithPassword({
        email: adminEmail, password
      });
      if (error) throw new Error('Senha incorreta ou acesso indisponível.');
      return data.session;
    },
    async getSession(supabaseClient) {
      const { data, error } = await supabaseClient.auth.getSession();
      if (error) throw error;
      return data.session;
    },
    async signOut(supabaseClient) {
      const { error } = await supabaseClient.auth.signOut();
      if (error) throw error;
    }
  };
})();
