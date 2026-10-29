/* Controle Produ — NF-e: autenticação administrativa com MFA TOTP.
   Não guarda senha do usuário, certificado ou segredo TOTP em código ou logs. */
(() => {
  "use strict";
  let inflight = null;

  const secureSession = async (client) => {
    const { data: { session }, error: sessionError } = await client.auth.getSession();
    if (sessionError || !session?.access_token) return false;
    const { data: { user }, error: userError } = await client.auth.getUser();
    if (userError || !user || user.is_anonymous) return false;
    const { data: aal, error: aalError } = await client.auth.mfa.getAuthenticatorAssuranceLevel();
    return !aalError && aal?.currentLevel === "aal2";
  };

  const showLogin = (client) => new Promise((resolve, reject) => {
    const overlay = document.createElement("div");
    overlay.setAttribute("role", "presentation");
    overlay.style.cssText = "position:fixed;inset:0;z-index:99999;background:rgba(10,24,16,.75);display:flex;align-items:center;justify-content:center;padding:16px";
    overlay.innerHTML = `
      <section role="dialog" aria-modal="true" aria-labelledby="nfe-admin-title" style="width:100%;max-width:440px;max-height:96vh;overflow:auto;background:white;border-radius:14px;padding:24px;box-shadow:0 18px 64px #0006;font:14px Manrope,Arial,sans-serif;color:#20352a">
        <h2 id="nfe-admin-title" style="font-size:20px;font-weight:700;margin:0 0 10px">Acesso fiscal protegido</h2>
        <p id="nfe-auth-help" style="line-height:1.5;color:#536358;margin:0 0 20px">Para consultar ou importar notas fiscais, entre com a conta autorizada. A verificação por aplicativo autenticador é obrigatória.</p>
        <form id="nfe-auth-login" style="display:flex;flex-direction:column;gap:12px">
          <label>E-mail administrativo<input id="nfe-auth-email" type="email" required autocomplete="username" style="display:block;width:100%;box-sizing:border-box;padding:12px;border:1px solid #ccc;border-radius:8px;margin-top:5px"></label>
          <label>Senha da conta<input id="nfe-auth-password" type="password" required autocomplete="current-password" style="display:block;width:100%;box-sizing:border-box;padding:12px;border:1px solid #ccc;border-radius:8px;margin-top:5px"></label>
          <button type="submit" style="padding:12px;background:#285a41;color:white;border:0;border-radius:8px;font-weight:700;cursor:pointer">Entrar com segurança</button>
        </form>
        <div id="nfe-auth-mfa" style="display:none">
          <p id="nfe-auth-instructions" style="line-height:1.5"></p>
          <img id="nfe-auth-qr" alt="Código QR para configurar o autenticador" style="display:none;width:190px;height:190px;margin:12px auto">
          <label>Código de 6 dígitos<input id="nfe-auth-code" type="text" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" autocomplete="one-time-code" style="display:block;width:100%;box-sizing:border-box;padding:12px;border:1px solid #ccc;border-radius:8px;margin-top:5px"></label>
          <button id="nfe-auth-verify" type="button" style="width:100%;padding:12px;margin-top:12px;background:#285a41;color:white;border:0;border-radius:8px;font-weight:700;cursor:pointer">Validar código</button>
        </div>
        <p id="nfe-auth-error" role="alert" style="color:#9a1d2a;min-height:20px;line-height:1.4"></p>
        <button id="nfe-auth-cancel" type="button" style="background:transparent;border:0;padding:8px;color:#526b5b;text-decoration:underline;cursor:pointer">Cancelar</button>
      </section>
    `;
    document.body.appendChild(overlay);
    const get = (id) => overlay.querySelector("#" + id);
    const loginForm = get("nfe-auth-login");
    const mfaPanel = get("nfe-auth-mfa");
    const err = get("nfe-auth-error");
    const help = get("nfe-auth-help");
    const qr = get("nfe-auth-qr");
    const instructions = get("nfe-auth-instructions");
    const code = get("nfe-auth-code");
    const cancel = get("nfe-auth-cancel");
    const verify = get("nfe-auth-verify");
    let factorId = null;
    let busy = false;
    let finished = false;
    let previousFocus = document.activeElement;

    const finish = (error) => {
      if (finished) return;
      finished = true;
      const pwd = get("nfe-auth-password");
      if (pwd) pwd.value = "";
      code.value = "";
      qr.removeAttribute("src");
      overlay.remove();
      if (previousFocus?.focus) previousFocus.focus();
      if (error) reject(error); else resolve();
    };
    const fail = (e) => { err.textContent = e?.message || "Não foi possível autenticar. Verifique os dados."; };
    const waiting = (value) => {
      busy = value;
      loginForm.querySelector("button").disabled = value;
      verify.disabled = value;
    };

    const setupSecondFactor = async () => {
      const { data: assurance, error: levelError } = await client.auth.mfa.getAuthenticatorAssuranceLevel();
      if (levelError) throw levelError;
      if (assurance?.currentLevel === "aal2") return finish();
      const { data: factors, error: factorsError } = await client.auth.mfa.listFactors();
      if (factorsError) throw factorsError;
      const existing = (factors?.totp || []).find((f) => f.status === "verified");
      if (existing) {
        factorId = existing.id;
        instructions.textContent = "Digite o código do seu aplicativo autenticador para continuar.";
      } else {
        const { data: enrollment, error: enrollError } = await client.auth.mfa.enroll({
          factorType: "totp", friendlyName: "Controle Produ - NF-e"
        });
        if (enrollError) throw enrollError;
        factorId = enrollment.id;
        instructions.textContent = "Primeiro, escaneie o QR Code usando Google Authenticator, Microsoft Authenticator ou outro aplicativo TOTP. Depois digite o código gerado.";
        if (enrollment.totp?.qr_code && /^data:image\/(svg\+xml|png)/i.test(enrollment.totp.qr_code)) {
          qr.src = enrollment.totp.qr_code;
          qr.style.display = "block";
        } else {
          instructions.textContent += " Caso o QR Code não apareça, entre em contato com o suporte antes de cadastrar o certificado.";
        }
      }
      loginForm.style.display = "none";
      mfaPanel.style.display = "block";
      help.textContent = "Segunda etapa de segurança obrigatória.";
      code.focus();
    };

    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (busy) return;
      err.textContent = "";
      waiting(true);
      try {
        const email = get("nfe-auth-email").value.trim();
        const password = get("nfe-auth-password").value;
        const { error } = await client.auth.signInWithPassword({ email, password });
        get("nfe-auth-password").value = "";
        if (error) throw error;
        await setupSecondFactor();
      } catch (e) { fail(e); } finally { waiting(false); }
    });

    verify.addEventListener("click", async () => {
      if (busy || !factorId) return;
      const oneTimeCode = code.value.trim().replace(/\D/g, "");
      if (!/^[0-9]{6}$/.test(oneTimeCode)) {
        err.textContent = "Digite os 6 dígitos do aplicativo autenticador.";
        return;
      }
      err.textContent = "";
      waiting(true);
      try {
        const { data: challenge, error: challengeError } = await client.auth.mfa.challenge({ factorId });
        if (challengeError) throw challengeError;
        const { error: verifyError } = await client.auth.mfa.verify({
          factorId, challengeId: challenge.id, code: oneTimeCode
        });
        code.value = "";
        if (verifyError) throw verifyError;
        if (!(await secureSession(client))) throw new Error("A segunda etapa não foi confirmada.");
        finish();
      } catch (e) { fail(e); } finally { waiting(false); }
    });
    code.addEventListener("keydown", (event) => {
      if (event.key === "Enter") { event.preventDefault(); verify.click(); }
    });
    cancel.addEventListener("click", () => {
      if (busy) return;
      client.auth.signOut({ scope: "local" }).catch(() => {});
      finish(new Error("Autenticação fiscal cancelada."));
    });

    // Continue MFA when a valid account session already exists.
    client.auth.getSession().then(({ data }) => {
      if (data?.session && !finished) setupSecondFactor().catch(fail);
      else get("nfe-auth-email")?.focus();
    }).catch(fail);
  });

  async function ensureReady(client) {
    if (!client) throw new Error("Autenticação fiscal indisponível.");
    if (inflight) return inflight;
    inflight = (async () => {
      if (await secureSession(client)) return;
      await showLogin(client);
      if (!(await secureSession(client))) throw new Error("A autenticação com duas etapas é obrigatória.");
    })().finally(() => { inflight = null; });
    return inflight;
  }
  window.DDVFiscalAuth = Object.freeze({ ensureReady });
})();
