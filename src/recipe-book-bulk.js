/* Exportação em lote de fichas técnicas: mesmo banco, PDF único, sem custos de CMV. */
(function(){
const escapeText = value => String(value == null ? '' : value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels={doce:'Doces',salgado:'Salgados',sobremesa:'Sobremesas',cafeteria:'Cafeteria',pao:'Pães',bomboniere:'Bomboniere',bebida_revenda:'Bebidas',outro:'Outros'};
const endpoint="https://rnycjwlmzpackuodflki.supabase.co";const anon="sb_publishable_W9Z02Rr3nlUqS1ec5_OCiw_Ezoc_iWk";
async function fetchAll(client, table){const rows=[];for(let start=0;start<10000;start+=1000){const {data,error}=await client.from(table).select('*').range(start,start+999);if(error)throw new Error('Não foi possível carregar '+table+': '+error.message);rows.push(...(data||[]));if(!data||data.length<1000)break;}return rows;}
async function exportBook(category, button){
 const original=button.textContent;button.disabled=true;button.textContent='Preparando livro…';
 const win=window.open('','_blank');if(!win){alert('Permita janelas pop-up para gerar o livro.');button.disabled=false;button.textContent=original;return;}
 win.document.write('<p style="font:16px Arial;padding:40px">Preparando o livro de receitas…</p>');
 try{
  if(!window.supabase)throw Error('Conexão com banco indisponível.');
  const sb=window.supabase.createClient(endpoint,anon,{auth:{persistSession:true,storageKey:'sb-'+new URL(endpoint).hostname.split('.')[0]+'-auth-token'}});
  const [products,recipes,items,supplies]=await Promise.all(['products','recipes','recipe_items','supplies'].map(t=>fetchAll(sb,t)));
  const productById=new Map(products.map(p=>[String(p.id),p]));const supplyById=new Map(supplies.map(p=>[String(p.id),p]));
  const selection=recipes.map(r=>({recipe:r,product:productById.get(String(r.product_id))})).filter(x=>x.product&&(category==='todos'||x.product.category===category)).sort((a,b)=>{const cats=Object.keys(labels);return cats.indexOf(a.product.category)-cats.indexOf(b.product.category)||a.product.name.localeCompare(b.product.name,'pt-BR')});
  if(!selection.length)throw Error('Nenhuma ficha técnica cadastrada para esta categoria.');
  let categoriaAnterior = null;
  const pages=selection.map(({recipe:r,product:p},idx)=>{
    const categoriaAtual=labels[p.category]||p.category||'Outros';
    const divisoria=categoriaAtual!==categoriaAnterior?'<section class="category-divider"><span>DELÍCIAS DA VOVÓ · LIVRO DE RECEITAS</span><h1>'+escapeText(categoriaAtual)+'</h1></section>':'';
    categoriaAnterior=categoriaAtual;
    const inheritedRecipe = r.inherit_parent_recipe && p.parent_product_id ? recipes.find(base=>String(base.product_id)===String(p.parent_product_id)) : null;
    const inheritedItems = inheritedRecipe ? items.filter(i=>String(i.recipe_id)===String(inheritedRecipe.id)) : [];
    const inheritedIds = new Set(inheritedItems.map(i=>String(i.supply_id||'')+'|'+String(i.component_product_id||'')));
    const variantItems = items.filter(i=>String(i.recipe_id)===String(r.id));
    const combinedItems = [...inheritedItems.filter(i=>!variantItems.some(v=>String(v.supply_id||'')+'|'+String(v.component_product_id||'')===String(i.supply_id||'')+'|'+String(i.component_product_id||''))),...variantItems];
    const ingredients=combinedItems.map(i=>{const name=i.supply_id?supplyById.get(String(i.supply_id))?.name:productById.get(String(i.component_product_id))?.name;const unit=i.usage_unit||(i.supply_id?supplyById.get(String(i.supply_id))?.unit:'un')||'un';return '<div class="ingredient"><span>'+escapeText(name||'Componente')+'</span><strong>'+escapeText(i.qty)+' '+escapeText(unit)+'</strong></div>';}).join('');
    const photo=r.image_url||inheritedRecipe?.image_url||p.image_url||p.photo_url||p.image||p.photo||'';const safePhoto=/^https:\/\//i.test(photo)?'<img src="'+escapeText(photo)+'" alt="Fotografia de '+escapeText(p.name)+'">':'<div class="photo-empty">Fotografia do produto<br><small>Espaço reservado</small></div>';
    const procedimento=String(r.preparation_method||r.instructions||r.notes||'').split(/\n+/).map(x=>x.trim()).filter(Boolean);
    const passos=procedimento.length?'<ol class="passos">'+procedimento.map(x=>'<li>'+escapeText(x.replace(/^\\d+[.)-]?\\s*/,''))+'</li>').join('')+'</ol>':'<p>Modo de preparo não cadastrado.</p>';
    const prazo=p.shelf_life_days?'<div><span class="symbol">▦</span><b>VALIDADE</b><strong>até '+escapeText(p.shelf_life_days)+' dias</strong></div>':'';
    const quantidade=Number(r.yield_qty)||0;
    const unidade=String(r.yield_unit||'un').toLowerCase();
    const pesoUn=Number(r.weight_per_unit)||0;
    const porcoes=unidade==='un'&&quantidade>0?quantidade:(unidade==='kg'&&pesoUn>0?quantidade*1000/pesoUn:null);
    const rendimentoKg=unidade==='kg'&&quantidade>0?quantidade:(unidade==='g'&&quantidade>0?quantidade/1000:(unidade==='un'&&pesoUn>0?quantidade*pesoUn/1000:null));
    const formatar=n=>Number(n).toLocaleString('pt-BR',{maximumFractionDigits:2});
    return divisoria+'<article class="sheet"><section class="left"><div class="micro">RECEITAS DA DELÍCIAS DA VOVÓ</div><p class="category">'+escapeText(categoriaAtual)+'</p><h1>'+escapeText(p.name)+'</h1><div class="short-rule"></div><div class="photo">'+safePhoto+'</div></section><section class="right"><header>RECEITA N.º '+String(idx+1).padStart(2,'0')+'</header><div class="metrics"><div><span class="symbol">♧</span><b>PORÇÕES</b><strong>'+escapeText(porcoes==null?'—':formatar(porcoes))+' un</strong></div><div><span class="symbol">♨</span><b>RENDIMENTO</b><strong>'+escapeText(rendimentoKg==null?'—':formatar(rendimentoKg))+' kg</strong></div>'+prazo+'</div><h2>INGREDIENTES</h2><div class="ingredients">'+(ingredients||'<p>Ingredientes não cadastrados.</p>')+'</div><h2>MODO DE PREPARO</h2>'+passos+(r.notes&&r.preparation_method?'<div class="production"><h2>OBSERVAÇÕES DE PRODUÇÃO</h2><p>'+escapeText(r.notes).replace(/\\n/g,'<br>')+'</p></div>':'')+'</section></article>';

   }).join('');
  const css=`@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap');
@page{size:A4 landscape;margin:0}*{box-sizing:border-box}body{margin:0;background:#d8ded4;color:#202c23;font-family:Lora,Georgia,serif}.top{padding:14px 24px;background:#fff;display:flex;justify-content:space-between;align-items:center;font-size:13px;position:sticky;top:0;z-index:5}.top button{background:#294b38;color:#fff;padding:11px 18px;border:0;border-radius:8px;cursor:pointer}
.category-divider{width:min(1180px,98vw);margin:25px auto 0;background:#fff;padding:30px 50px;border-bottom:2px solid #335340;break-before:page}.category-divider span{font-size:10px;letter-spacing:3px}.category-divider h1{font-size:36px;font-weight:400}
.sheet{width:min(1180px,98vw);aspect-ratio:297/210;margin:22px auto 34px;background:#fff;display:grid;grid-template-columns:49% 51%;box-shadow:0 12px 35px #0002;break-after:page;page-break-after:always;break-inside:avoid;overflow:hidden}.left{padding:22px 20px 16px;display:flex;flex-direction:column;min-width:0;border-right:1px solid #d0cbbf}.micro,.right header{font-size:9px;letter-spacing:2.5px;border-bottom:1px solid #7b8a7b;padding-bottom:10px}.category{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#536b55;margin:12px 0 5px}.left h1{font-size:43px;line-height:1.12;font-weight:400;color:#193922;margin:0;max-height:110px;overflow:hidden}.short-rule{width:50px;height:3px;background:#a7834d;margin:10px 0}.photo{flex:1;min-height:0;width:100%;overflow:hidden;display:flex;align-items:center;justify-content:center}.photo img{display:block;width:100%;height:100%;object-fit:cover;object-position:center}.photo-empty{text-align:center;color:#8c8a7c;font-size:15px}.signature{color:#778968;font-size:19px;font-style:italic;margin-top:15px}.right{padding:31px 36px 26px;min-width:0;display:flex;flex-direction:column;overflow:hidden}.right header{text-align:right}.metrics{display:flex;justify-content:space-around;padding:22px 0 16px;border-bottom:1px solid #ded5c5}.metrics>div{flex:1;text-align:center;padding:0 6px;border-right:1px solid #d7d0bf}.metrics>div:last-child{border-right:0}.symbol{display:block;border-radius:50%;background:#d8dfca;width:34px;height:34px;line-height:34px;margin:0 auto 10px;font-size:19px}.metrics b{display:block;font-size:11px;letter-spacing:1.5px}.metrics strong{display:block;margin-top:8px;font-size:15px;font-weight:400}.right h2{font-size:15px;letter-spacing:3px;margin:22px 0 13px;border-bottom:1px solid #8d9d8a;padding-bottom:8px}.ingredients{columns:2;column-gap:17px;max-height:112px;overflow:hidden}.ingredient{font-size:12px;line-height:1.4;display:flex;justify-content:space-between;gap:5px;border-bottom:1px dotted #bcb7aa;padding:3px 0;break-inside:avoid}.ingredient strong{white-space:nowrap;font-weight:400}.passos{list-style:none;counter-reset:step;padding:0;margin:0}.passos li{counter-increment:step;position:relative;padding:0 0 9px 29px;font-size:12px;line-height:1.52}.passos li:before{content:counter(step);position:absolute;left:0;top:0;border-radius:50%;width:20px;height:20px;background:#7b9173;color:white;text-align:center;line-height:20px}.production{background:#f4f6f2;border-radius:11px;padding:10px 14px;margin-top:10px;font-size:12px}.production h2{margin:3px 0 7px}.production p{margin:0;line-height:1.55}
@media print{body{background:#fff}.top{display:none}.sheet{margin:0;width:297mm;height:210mm;box-shadow:none}.category-divider{margin:0;width:297mm;break-before:page}.sheet:last-child{break-after:auto;page-break-after:auto}}@media screen and (max-width:800px){.sheet{width:1160px}}`;

  win.document.open();win.document.write('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Livro de Receitas — Delícias da Vovó</title><style>'+css+'</style></head><body><div class="top"><div><strong>Livro de Receitas · '+escapeText(category==='todos'?'Todas as categorias':labels[category]||category)+'</strong><br>'+selection.length+' receitas</div><button onclick="window.print()">Imprimir / salvar PDF</button></div>'+pages+'</body></html>');win.document.close();
 }catch(e){win.document.open();win.document.write('<p style="font:16px Arial;padding:35px;color:#8a2929">'+escapeText(e.message)+'</p>');win.document.close();}finally{button.disabled=false;button.textContent=original;}
}
function install(){
 document.querySelectorAll('div.t-overline').forEach(title=>{if(title.textContent.trim()!=='Fichas técnicas')return;const card=title.closest('.card');if(!card||card.querySelector('[data-export-book]'))return;
 const select=card.querySelector('select');if(!select||!Array.from(select.options).some(x=>x.value==='todos'))return;
 const button=document.createElement('button');button.type='button';button.dataset.exportBook='true';button.textContent='Baixar livro de receitas (PDF)';button.className='btn btn-primary btn-sm';button.style.cssText='margin-top:10px;padding:10px 14px;background:#294b38;color:white;border-radius:8px;font:600 12px Arial;cursor:pointer';button.addEventListener('click',()=>exportBook(select.value,button));title.parentElement.appendChild(button);
 });
}
let scheduled=false;new MutationObserver(()=>{if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;install()})}).observe(document.documentElement,{childList:true,subtree:true});install();
})();