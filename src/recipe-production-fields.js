/* Campos de produção para a interface compilada: foto real e modo de preparo.
 * Salva sempre no registro public.recipes utilizado pelo livro de receitas.
 */
(function () {
  'use strict';
  const SUPABASE_URL = 'https://rnycjwlmzpackuodflki.supabase.co';
  const SUPABASE_KEY = 'sb_publishable_W9Z02Rr3nlUqS1ec5_OCiw_Ezoc_iWk';
  const PHOTO_CATALOG = './src/pedidos-cardapio-photos.json?v=20261017-01';
  const clean = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR').replace(/[^a-z0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
  let client = null;
  let catalog = null;
  let catalogLoading = null;

  function getClient() {
    if (!window.supabase) throw new Error('Biblioteca do Supabase indisponível.');
    if (!client) client = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
    return client;
  }

  async function getCatalog() {
    if (catalog) return catalog;
    if (!catalogLoading) {
      catalogLoading = fetch(PHOTO_CATALOG, { cache: 'no-cache' })
        .then(async response => {
          if (!response.ok) throw new Error('Catálogo de fotos indisponível.');
          const data = await response.json();
          if (!Array.isArray(data.photos)) throw new Error('Formato de catálogo inválido.');
          catalog = data.photos.filter(photo => photo.name && /^https:\/\//i.test(photo.url));
          return catalog;
        }).catch(error => { catalogLoading = null; throw error; });
    }
    return catalogLoading;
  }

  function mount(dialog) {
    if (dialog.dataset.productionRecipeMounted) return;
    if (dialog.textContent.includes('Foto real do produto para o livro')) return; // editor nativo atualizado
    dialog.dataset.productionRecipeMounted = '1';
    const name = (dialog.getAttribute('aria-label') || '').replace(/^Ficha técnica de\s*/i, '').trim();
    const container = dialog.querySelector('.relative.bg-white .p-5') || dialog.querySelector('.relative.bg-white');
    if (!container || !name) return;
    const heading = container.querySelector('h3');
    const anchor = heading?.closest('.flex.items-start') || heading?.closest('.border-b') || null;
    const box = document.createElement('section');
    box.setAttribute('data-recipe-production-fields', '');
    box.style.cssText = 'margin:16px 0;padding:18px;border:1px solid #d5ded4;border-radius:14px;background:#fff;color:#29402f;font:13px/1.5 Arial,sans-serif';
    box.innerHTML = [
      '<h4 style="font:600 19px Lora,Georgia,serif;margin:0 0 4px;color:#29402f">Foto e modo de preparo</h4>',
      '<p style="margin:0 0 12px;color:#69786e;font-size:12px">Salvos na ficha técnica e usados no livro de receitas.</p>',
      '<p data-initial-state>Carregando receita…</p>',
      '<div data-form hidden>',
        '<div style="display:flex;flex-wrap:wrap;gap:16px">',
          '<div style="flex:1 1 220px;min-width:0">',
            '<label style="display:block;font-weight:600;margin-bottom:7px">Foto real do produto</label>',
            '<img data-preview alt="Foto da receita" style="display:none;width:100%;max-width:350px;height:185px;object-fit:contain;border:1px solid #ebece7;border-radius:10px;margin-bottom:8px">',
            '<div data-empty-photo style="border:1px dashed #b9c7ba;border-radius:10px;padding:22px;text-align:center;color:#7c887e;margin-bottom:8px">Nenhuma foto escolhida</div>',
            '<div style="display:flex;flex-wrap:wrap;gap:8px">',
              '<label style="background:#31513d;color:#fff;border-radius:7px;padding:9px 12px;cursor:pointer;font-size:12px">Enviar foto<input data-upload type="file" accept="image/jpeg,image/png,image/webp" style="display:none"></label>',
              '<button data-menu-toggle type="button" style="background:#f4f6f2;color:#31513d;border:1px solid #c9d5c7;border-radius:7px;padding:9px 12px;cursor:pointer;font-size:12px">Escolher do Pedidos Cardápio</button>',
              '<button data-remove type="button" style="background:#fff;border:1px solid #ddd;border-radius:7px;padding:9px 12px;cursor:pointer;font-size:12px">Remover foto</button>',
            '</div>',
          '</div>',
          '<div style="flex:1 1 265px;min-width:0">',
            '<label for="recipe-production-notes" style="display:block;font-weight:600;margin-bottom:7px">Modo de preparo</label>',
            '<textarea data-notes id="recipe-production-notes" rows="8" placeholder="Descreva cada etapa em uma linha…" style="box-sizing:border-box;width:100%;min-height:185px;resize:vertical;border:1px solid #cdd9ce;border-radius:9px;padding:11px;font:13px/1.6 Arial,sans-serif"></textarea>',
            '<p style="font-size:11px;color:#758178;margin:6px 0">Salva automaticamente enquanto você digita ou ao sair do campo.</p>',
            '<button data-save-notes type="button" style="background:#31513d;color:white;border:0;border-radius:7px;padding:8px 12px;cursor:pointer;font-size:12px">Salvar modo de preparo</button>',
          '</div>',
        '</div>',
        '<div data-catalog hidden style="margin-top:16px;padding:12px;background:#fafbf9;border:1px solid #d9e2d7;border-radius:10px">',
          '<label style="font-weight:600;font-size:12px;display:block;margin-bottom:8px">Buscar foto do Pedidos Cardápio</label>',
          '<input data-catalog-search type="search" placeholder="Nome do produto…" style="width:100%;box-sizing:border-box;padding:9px;border:1px solid #cbd6cb;border-radius:7px;font-size:13px">',
          '<div data-results style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:9px;margin-top:12px;max-height:290px;overflow:auto"></div>',
          '<p data-catalog-status style="font-size:11px;color:#63756a;margin:7px 0 0"></p>',
        '</div>',
        '<div style="margin-top:13px">',
          '<label style="display:block;font-size:12px;margin-bottom:4px">Ou colar link direto da foto</label>',
          '<input data-image-url type="url" placeholder="https://..." style="width:100%;box-sizing:border-box;padding:9px;border:1px solid #cbd6cb;border-radius:7px">',
          '<p style="font-size:11px;color:#7c877c;margin:5px 0 0">Ao mudar o link e sair do campo, a imagem é salva.</p>',
        '</div>',
        '<p data-status role="status" aria-live="polite" style="font-size:12px;color:#31513d;min-height:18px;margin:12px 0 0"></p>',
      '</div>'
    ].join('');
    if (anchor?.parentNode) anchor.insertAdjacentElement('afterend', box);
    else container.prepend(box);

    const el = selector => box.querySelector(selector);
    const state = el('[data-initial-state]');
    const form = el('[data-form]');
    const notes = el('[data-notes]');
    const urlField = el('[data-image-url]');
    const preview = el('[data-preview]');
    const empty = el('[data-empty-photo]');
    const status = el('[data-status]');
    const panel = el('[data-catalog]');
    const search = el('[data-catalog-search]');
    const results = el('[data-results]');
    const catalogStatus = el('[data-catalog-status]');
    let productId = null;
    let recipeId = null;
    let savedNotes = '';
    let savedImage = '';
    let saveQueue = Promise.resolve();
    let notesTimer = null;

    const say = (message, error = false) => {
      status.textContent = message;
      status.style.color = error ? '#a43a32' : '#31513d';
    };
    const showImage = url => {
      preview.style.display = url ? 'block' : 'none';
      empty.style.display = url ? 'none' : 'block';
      if (url) preview.src = url;
      else preview.removeAttribute('src');
    };

    function persist(patch) {
      saveQueue = saveQueue.catch(() => {}).then(async () => {
        const sb = getClient();
        say('Salvando…');
        let result;
        if (recipeId) {
          result = await sb.from('recipes').update(patch).eq('id', recipeId).select('id, notes, image_url').single();
        } else {
          result = await sb.from('recipes').insert({ product_id: productId, ...patch }).select('id, notes, image_url').single();
          if (result.error && /duplicate|unique/i.test(result.error.message || '')) {
            const found = await sb.from('recipes').select('id').eq('product_id', productId).maybeSingle();
            if (!found.error && found.data?.id) {
              recipeId = found.data.id;
              result = await sb.from('recipes').update(patch).eq('id', recipeId).select('id, notes, image_url').single();
            }
          }
        }
        if (result.error) throw result.error;
        recipeId = result.data.id;
        if (Object.hasOwn(patch, 'notes')) savedNotes = patch.notes;
        if (Object.hasOwn(patch, 'image_url')) savedImage = patch.image_url || '';
        say('Alterações salvas na ficha.');
      }).catch(error => { say('Não foi possível salvar: ' + (error.message || error), true); });
      return saveQueue;
    }

    function saveNotes() {
      clearTimeout(notesTimer);
      if (!productId || notes.value === savedNotes) return;
      persist({ notes: notes.value });
    }
    notes.addEventListener('input', () => {
      clearTimeout(notesTimer);
      say('Modo de preparo alterado. Salvando…');
      notesTimer = setTimeout(saveNotes, 850);
    });
    notes.addEventListener('blur', saveNotes);
    el('[data-save-notes]').addEventListener('click', saveNotes);

    urlField.addEventListener('change', () => {
      const url = urlField.value.trim();
      if (url && !/^https:\/\//i.test(url)) { say('Use um endereço HTTPS para a foto.', true); return; }
      showImage(url);
      if (url !== savedImage) persist({ image_url: url || null });
    });
    el('[data-remove]').addEventListener('click', () => {
      urlField.value = '';
      showImage('');
      persist({ image_url: null });
    });

    async function choosePhoto(photo) {
      urlField.value = photo.url;
      showImage(photo.url);
      await persist({ image_url: photo.url });
      panel.hidden = true;
    }

    function renderPhotos(photos) {
      const q = clean(search.value);
      const matches = photos.filter(photo => !q || clean(photo.name).includes(q)).slice(0, 48);
      results.replaceChildren();
      matches.forEach(photo => {
        const button = document.createElement('button');
        button.type = 'button';
        button.style.cssText = 'padding:5px;background:white;border:1px solid #d5ded3;border-radius:8px;cursor:pointer;text-align:left;font:11px/1.4 Arial,sans-serif;color:#263b2c';
        const img = document.createElement('img');
        img.loading = 'lazy';
        img.src = photo.url;
        img.alt = '';
        img.style.cssText = 'width:100%;height:86px;object-fit:cover;border-radius:5px;margin-bottom:5px';
        const caption = document.createElement('span');
        caption.textContent = photo.name;
        button.append(img, caption);
        button.addEventListener('click', () => choosePhoto(photo));
        results.append(button);
      });
      catalogStatus.textContent = matches.length ? matches.length + ' fotos encontradas. Clique para selecionar.' : 'Nenhuma foto encontrada. Tente outra palavra ou envie a sua foto.';
    }

    el('[data-menu-toggle]').addEventListener('click', async () => {
      panel.hidden = !panel.hidden;
      if (panel.hidden) return;
      catalogStatus.textContent = 'Carregando as fotos do Pedidos Cardápio…';
      try {
        const photos = await getCatalog();
        search.value = name;
        renderPhotos(photos);
        if (!results.childElementCount) { search.value = ''; renderPhotos(photos); }
      } catch (error) { catalogStatus.textContent = 'Não foi possível carregar o catálogo: ' + (error.message || error); }
    });
    search.addEventListener('input', () => { if (catalog) renderPhotos(catalog); });

    el('[data-upload]').addEventListener('change', async event => {
      const file = event.target.files?.[0];
      event.target.value = '';
      if (!file) return;
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { say('Envie JPG, PNG ou WebP.', true); return; }
      if (file.size > 8 * 1024 * 1024) { say('O limite por foto é 8 MB.', true); return; }
      try {
        const sb = getClient();
        say('Enviando foto…');
        const ext = file.type === 'image/png' ? 'png' : file.type === 'image/webp' ? 'webp' : 'jpg';
        const id = window.crypto?.randomUUID ? window.crypto.randomUUID() : String(Date.now());
        const path = productId + '/' + id + '.' + ext;
        const { error } = await sb.storage.from('recipe-photos').upload(path, file, { contentType: file.type, upsert: false });
        if (error) throw error;
        const { data } = sb.storage.from('recipe-photos').getPublicUrl(path);
        if (!data?.publicUrl) throw new Error('O armazenamento não retornou a URL.');
        urlField.value = data.publicUrl;
        showImage(data.publicUrl);
        await persist({ image_url: data.publicUrl });
      } catch (error) { say('Erro ao enviar foto: ' + (error.message || error), true); }
    });

    (async () => {
      try {
        const sb = getClient();
        const { data: found, error: productError } = await sb.from('products').select('id,name').ilike('name', name).limit(20);
        if (productError) throw productError;
        const product = (found || []).find(p => clean(p.name) === clean(name));
        if (!product) throw new Error('Produto não encontrado no banco. Confira o nome no cadastro.');
        productId = product.id;
        const { data: recipe, error: recipeError } = await sb.from('recipes').select('id,notes,image_url').eq('product_id', productId).maybeSingle();
        if (recipeError) throw recipeError;
        recipeId = recipe?.id || null;
        savedNotes = recipe?.notes || '';
        savedImage = recipe?.image_url || '';
        notes.value = savedNotes;
        urlField.value = savedImage;
        showImage(savedImage);
        state.remove();
        form.hidden = false;
      } catch (error) {
        state.textContent = 'Não foi possível abrir foto e modo de preparo: ' + (error.message || error);
        state.style.color = '#a43a32';
      }
    })();
  }

  function scan() {
    document.querySelectorAll('[role="dialog"][aria-label^="Ficha técnica de "]').forEach(mount);
  }
  let scheduled = false;
  const observer = new MutationObserver(() => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; scan(); });
  });
  observer.observe(document.documentElement, { childList: true, subtree: true });
  scan();
})();