window.abrirLivroReceita = function({produto, ficha, supplies, products}) {
 const safe=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const items=(ficha?.itens||[]).map(i=>{const s=supplies.find(x=>x.id===i.supplyId),p=products.find(x=>x.id===i.componentProductId);return {nome:s?.name||p?.name||i._name||'Componente',qty:i.qty,unit:i.usageUnit||s?.unit||'un'};});
 const win=window.open('','_blank'); if(!win){alert('Permita pop-ups para abrir o livro.');return;}
 const css='@import url("https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap");@page{size:A4 landscape;margin:0}*{box-sizing:border-box}body{font-family:Lora,Georgia,serif;margin:0;background:#eae9e6;color:#222}.bar{font:13px Arial;background:white;padding:12px 25px;display:flex;justify-content:space-between;gap:10px}.book{width:min(1180px,96vw);aspect-ratio:1.414;margin:35px auto;background:white;box-shadow:0 12px 45px #0002;display:grid;grid-template-columns:1fr 1fr}.photo{background:#f1f0ed;border-right:1px solid #ccc;display:flex;align-items:center;justify-content:center;color:#727870;text-align:center;overflow:hidden}.photo img{width:100%;height:100%;object-fit:cover}.page{padding:7%;display:flex;flex-direction:column;overflow:hidden}.eyebrow{font:10px Arial;letter-spacing:3px;color:#3c5947}h1{font-size:38px;line-height:1.12;font-weight:400;margin:17px 0 20px}h2{font:11px Arial;letter-spacing:3px;margin:18px 0 12px}.stats{font:12px Arial;border-top:1px solid #ddd;border-bottom:1px solid #ddd;padding:13px 0}.ingredients{columns:2;column-gap:22px;border-bottom:1px solid #ddd;padding-bottom:18px}.item{break-inside:avoid;font-size:12px;padding:5px 0;border-bottom:1px solid #eee;display:flex;justify-content:space-between;gap:7px}.item span:last-child{white-space:nowrap}.editable{font:14px/1.7 Lora,Georgia,serif;min-height:45px;color:#444;outline:none}.foot{margin-top:auto;font:9px Arial;color:#777;border-top:1px solid #ddd;padding-top:12px}button,label{font:12px Arial;cursor:pointer;padding:9px;border:1px solid #ddd;border-radius:4px;background:white}.hint{font:11px Arial;color:#777;max-width:1180px;margin:auto}@media print{body{background:white}.bar,.hint{display:none}.book{width:297mm;height:210mm;margin:0;box-shadow:none}.page{padding:14mm}h1{font-size:32px}.item{font-size:10px}.editable{font-size:11px}}@media(max-width:700px){.book{display:block;aspect-ratio:auto}.photo{height:300px}.page{min-height:600px}}';
 const rows=items.map(i=>'<div class="item"><span>'+safe(i.nome)+'</span><span>'+safe(i.qty)+' '+safe(i.unit)+'</span></div>').join('');
 const html='<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>'+safe(produto.name)+' — Livro de receitas</title><style>'+css+'</style></head><body>'+
 '<div class="bar"><strong>Delícias da Vovó · Livro de Receitas</strong><div><button onclick="window.print()">Imprimir / Salvar PDF</button></div></div>'+
 '<main class="book"><section class="photo" id="photo">Foto não cadastrada nesta receita</section><section class="page"><div class="eyebrow">DELÍCIAS DA VOVÓ / RECEITAS DE PRODUÇÃO</div><h1>'+safe(produto.name)+'</h1><div class="stats">Rendimento: '+safe(ficha?.yieldQty||'—')+' '+safe(ficha?.yieldUnit||produto.priceUnit||'un')+(ficha?.weightPerUnit?' · Peso/un: '+safe(ficha.weightPerUnit)+' g':'')+'</div>'+
 '<h2>INGREDIENTES</h2><div class="ingredients">'+(rows||'Cadastre os ingredientes na ficha técnica.')+'</div><h2>MODO DE PREPARO</h2><div class="editable" contenteditable="false" data-preparo>Carregando modo de preparo salvo…</div><div class="foot">DELÍCIAS DA VOVÓ · FICHA DE PRODUÇÃO</div></section></main><p class="hint">Para alterar a foto ou o modo de preparo, abra a ficha técnica no Controle Produ.</p></body></html>';
 win.document.open();win.document.write(html);win.document.close();
 const modo=win.document.querySelector('[data-preparo]');
 (async () => {
   try {
     if (!window.supabase) throw new Error('Supabase indisponível.');
     const sb=window.supabase.createClient('https://rnycjwlmzpackuodflki.supabase.co','sb_publishable_W9Z02Rr3nlUqS1ec5_OCiw_Ezoc_iWk');
     const {data:productsFound,error:productError}=await sb.from('products').select('id,name').ilike('name',produto.name).limit(20);
     if (productError) throw productError;
     const selected=(productsFound||[]).find(row=>String(row.name).trim().toLocaleLowerCase('pt-BR')===String(produto.name).trim().toLocaleLowerCase('pt-BR'));
     if (!selected) throw new Error('Produto não localizado no cadastro.');
     const {data:recipe,error:recipeError}=await sb.from('recipes').select('notes,image_url').eq('product_id',selected.id).maybeSingle();
     if (recipeError) throw recipeError;
     modo.textContent=recipe?.notes?.trim()||'Modo de preparo não cadastrado. Preencha na ficha técnica.';
     if (recipe?.image_url && /^https:\/\//i.test(recipe.image_url)) {
       const photo=win.document.getElementById('photo');
       photo.textContent='';
       const img=win.document.createElement('img');
       img.src=recipe.image_url;
       img.alt='Foto real de '+produto.name;
       photo.appendChild(img);
     }
   } catch (error) {
     modo.textContent='Não foi possível carregar os dados salvos: '+(error.message||error);
   }
 })();

};

// Disponibiliza o livro também na versão compilada em produção.
(function instalarBotaoLivro(){
 const aplicar=()=>{
  document.querySelectorAll('[role="dialog"][aria-label^="Ficha técnica de "]').forEach(dialog=>{
   if(dialog.querySelector('[data-livro-receitas]')) return;
   const title=dialog.querySelector('h3'); if(!title)return;
   const button=document.createElement('button');button.type='button';button.dataset.livroReceitas='true';button.textContent='Livro de receitas / PDF';
   button.style.cssText='background:#31513d;color:white;border:0;border-radius:8px;padding:8px 12px;font:600 12px Arial;cursor:pointer;margin:8px 0';
   button.onclick=()=>{
    const productName=title.textContent.trim();
    const rows=[...dialog.querySelectorAll('tbody tr')].filter(row=>row.querySelectorAll('td').length>=3).map(row=>{
     const cells=row.querySelectorAll('td');
     return {supplyId:null,componentProductId:null,qty:cells[1]?.querySelector('input')?.value||cells[1]?.textContent?.trim()||'',usageUnit:cells[2]?.querySelector('input')?.value||cells[2]?.textContent?.trim()||'',_name:cells[0]?.textContent?.trim()||''};
    }).filter(i=>i._name);
    const inputs=[...dialog.querySelectorAll('input[type="number"]')];
    const yieldInput=inputs.find(input=>input.title?.includes('receita produz'))||inputs[0];
    window.abrirLivroReceita({produto:{name:productName,priceUnit:'un'},ficha:{yieldQty:yieldInput?.value||'—',yieldUnit:'un',itens:rows},supplies:[],products:[]});
   };
   title.parentElement?.appendChild(button);
  });
 };
 const observer=new MutationObserver(()=>{if(!document.querySelector('[data-livro-receitas]')&&document.querySelector('[role="dialog"][aria-label^="Ficha técnica de "]'))aplicar()});
 observer.observe(document.documentElement,{childList:true,subtree:true});aplicar();
})();