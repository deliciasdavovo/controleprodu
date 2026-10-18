/* Diagramação única A4 vertical para PDF individual e livro completo. */
(function(){
'use strict';
const API='https://rnycjwlmzpackuodflki.supabase.co';
const KEY='sb_publishable_W9Z02Rr3nlUqS1ec5_OCiw_Ezoc_iWk';
const cats=[['doce','Doces'],['salgado','Salgados'],['sobremesa','Sobremesas'],['cafeteria','Cafeteria'],['pao','Pães'],['bomboniere','Bomboniere'],['bebida_revenda','Bebidas'],['outro','Outros']];
const names=Object.fromEntries(cats), order=new Map(cats.map(([id],i)=>[id,i]));
const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const clean=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').trim().toLocaleLowerCase('pt-BR');
const fmt=v=>Number(v).toLocaleString('pt-BR',{maximumFractionDigits:2});
const positive=v=>Number.isFinite(Number(v))&&Number(v)>0?Number(v):null;
const safeImage=v=>/^https:\/\//i.test(String(v||''))?String(v):'';
async function fetchAll(sb,table){
 const list=[];
 for(let i=0;i<10000;i+=1000){
  const {data,error}=await sb.from(table).select('*').range(i,i+999);
  if(error)throw Error('Erro ao carregar '+table+': '+error.message);
  list.push(...(data||[]));if(!data||data.length<1000)break;
 }
 return list;
}
function yieldInfo(r){
 const n=positive(r.yield_qty),unit=String(r.yield_unit||'').toLowerCase(),g=positive(r.weight_per_unit);
 let portions=null,kg=null;
 if(unit==='un'&&n){portions=n;if(g)kg=n*g/1000}
 else if(unit==='kg'&&n){kg=n;if(g)portions=n*1000/g}
 else if(unit==='g'&&n){kg=n/1000;if(g)portions=n/g}
 return {portions,kg};
}
function inheritedRecipe(r,p,data){
 return r.inherit_parent_recipe&&p.parent_product_id?data.recipes.find(item=>String(item.product_id)===String(p.parent_product_id)):null;
}
function ingredients(r,p,data){
 const parent=inheritedRecipe(r,p,data);
 const own=data.items.filter(item=>String(item.recipe_id)===String(r.id));
 const shared=parent?data.items.filter(item=>String(item.recipe_id)===String(parent.id)):[];
 const key=i=>String(i.supply_id||'')+'|'+String(i.component_product_id||'');
 const ownIds=new Set(own.map(key));
 const rows=[...shared.filter(i=>!ownIds.has(key(i))),...own];
 const output=rows.map(i=>{
  const supply=i.supply_id?data.supplyById.get(String(i.supply_id)):null;
  const product=i.component_product_id?data.productById.get(String(i.component_product_id)):null;
  const recipe=product?data.recipes.find(x=>String(x.product_id)===String(product.id)):null;
  const label=supply?.name||product?.name||'Ingrediente não identificado';
  const unit=i.usage_unit||supply?.unit||recipe?.yield_unit||product?.price_unit||'un';
  return '<div class="ingredient"><span>'+esc(label)+'</span><strong>'+esc(fmt(Number(i.qty)||0))+' '+esc(unit)+'</strong></div>';
 }).join('');
 return output||'<p class="missing">Ingredientes ainda não cadastrados.</p>';
}
function prepare(r){
 const content=String(r.preparation_method||r.instructions||r.notes||'').trim();
 const lines=content.split(/\r?\n/).map(s=>s.trim()).filter(Boolean);
 const steps=lines.length?'<ol class="steps">'+lines.map(step=>'<li>'+esc(step.replace(/^\d+[.)]\s*/,''))+'</li>').join('')+'</ol>':
   '<p class="missing">Modo de preparo ainda não cadastrado.</p>';
 const obs=(r.preparation_method||r.instructions)&&r.notes?.trim()?
   '<div class="observations"><h3>Observações de produção</h3><p>'+esc(r.notes).replace(/\r?\n/g,'<br>')+'</p></div>':'';
 return steps+obs;
}
const CSS="\n@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap');\n@page{size:A4 portrait;margin:0}\n*{box-sizing:border-box}\nhtml{background:#eeefec}\nbody{margin:0;background:transparent;font-family:Lora,Georgia,serif;color:#282b28}\n.toolbar{position:sticky;top:0;z-index:5;display:flex;align-items:center;justify-content:space-between;gap:16px;background:white;border-bottom:1px solid #dbe0d9;padding:13px 23px;font-size:12px}\n.toolbar strong{color:#294b38}\n.toolbar button{background:#294b38;color:white;padding:11px 16px;border:0;border-radius:7px;cursor:pointer;font:600 12px Lora,Georgia,serif}\n.recipe{width:210mm;min-height:297mm;margin:22px auto;padding:19mm 17mm 16mm;background:white;box-shadow:0 12px 36px #0002;break-before:page;page-break-before:always}\n.recipe:first-of-type{break-before:auto;page-break-before:auto}\n.recipe-head{text-align:center;margin-bottom:8mm}\n.kicker{font-size:8pt;text-transform:uppercase;color:#637664;letter-spacing:1.8px;margin:0 0 4mm}\n.recipe-head h1{font-size:24pt;line-height:1.25;font-weight:500;letter-spacing:1.1px;text-transform:uppercase;overflow-wrap:anywhere;color:#26372b;margin:0}\n.head-rule{width:30mm;height:1px;background:#bdc9bc;margin:5mm auto 0}\n.intro{display:grid;grid-template-columns:37% 63%;height:61mm;margin:0 0 10mm;break-inside:avoid}\n.intro.no-photo{grid-template-columns:1fr;height:auto}\n.quick-facts{background:#f5f4f1;padding:6mm 6.5mm;display:flex;flex-direction:column;justify-content:center;gap:4mm}\n.intro.no-photo .quick-facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:5mm;min-height:28mm}\n.fact{display:grid;grid-template-columns:9mm 1fr;align-items:center;gap:3mm;min-width:0}\n.fact svg{width:8mm;height:8mm;stroke:#5b665b;fill:none;stroke-width:1.35;stroke-linecap:round;stroke-linejoin:round}\n.fact .fact-label{display:block;font-size:8pt;line-height:1.3;color:#3f5041;font-weight:600}\n.fact .fact-value{display:block;font-size:10pt;line-height:1.4;margin-top:1mm;font-weight:400}\n.hero-photo{min-width:0;min-height:0;overflow:hidden;background:#f2f3f0}\n.hero-photo img{display:block;width:100%;height:100%;object-fit:cover;object-position:center}\n.content{display:grid;grid-template-columns:39% 61%;gap:10mm;align-items:start}\n.content>section{min-width:0}\n.content h2{font-size:14pt;font-weight:600;line-height:1.3;letter-spacing:0;margin:0 0 5mm;color:#263b2d}\n.ingredient{display:flex;justify-content:space-between;gap:3mm;align-items:baseline;font-size:10.5pt;line-height:1.55;margin-bottom:2.3mm;break-inside:avoid}\n.ingredient span{flex:1;overflow-wrap:anywhere}\n.ingredient strong{flex-shrink:0;white-space:nowrap;text-align:right;font-size:10pt;font-weight:500}\n.steps{padding:0;list-style:none;counter-reset:step;margin:0}\n.steps li{position:relative;padding-left:7mm;font-size:10.5pt;line-height:1.65;margin-bottom:5mm;overflow-wrap:anywhere;break-inside:avoid}\n.steps li:before{counter-increment:step;content:counter(step)'.';position:absolute;top:0;left:0;color:#667d69;font-weight:600;font-size:10pt}\n.observations{margin-top:7mm;border-top:1px solid #e3e8e1;padding-top:4mm}\n.observations h3{font-size:10pt;color:#354d39;font-weight:600;font-style:italic;margin:0 0 3mm}\n.observations p{font-size:10pt;line-height:1.6;margin:0}\n.missing{font-size:10pt;color:#78857a;font-style:italic}\n.footer{display:flex;justify-content:space-between;align-items:center;gap:10px;border-top:1px solid #e6e9e4;margin-top:12mm;padding-top:3mm;font-size:8pt;color:#7b897e;letter-spacing:.8px;break-inside:avoid}\n@media print{\n html{background:white}\n .toolbar{display:none}\n .recipe{width:210mm;min-height:297mm;padding:19mm 17mm 16mm;margin:0;box-shadow:none;break-before:page;page-break-before:always}\n .recipe:first-of-type{break-before:auto;page-break-before:auto}\n .recipe:last-of-type{break-after:auto;page-break-after:auto}\n .intro{break-inside:avoid}\n .content,.content>section{break-inside:auto}\n .content h2{break-after:avoid}\n}\n@media screen and (max-width:800px){.recipe{width:210mm}}\n";

function factIcon(label){
  const paths={
    'Porções':'<path d="M4 2v8M7 2v8M10 2v8M4 7h6M7 10v12M17 2v20M17 2c5 3 5 10 0 12"/>',
    'Rendimento':'<path d="M12 3v18M4 7h16M6 7l-4 7h8l-4-7M18 7l-4 7h8l-4-7M7 21h10"/>',
    'Preparo':'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>',
    'Validade':'<rect x="3" y="5" width="18" height="16" rx="1"/><path d="M7 3v4M17 3v4M3 10h18M7 14h2M12 14h2"/>'
  };
  return '<svg viewBox="0 0 24 24" aria-hidden="true">'+(paths[label]||paths['Preparo'])+'</svg>';
}
function article(r,p,data,index,first){
 const category=names[p.category]||p.category||'Outros';
 const parent=inheritedRecipe(r,p,data);
 const photo=safeImage(r.image_url||parent?.image_url||p.image_url||p.photo_url||'');
 const amounts=yieldInfo(r),stats=[];
 if(amounts.portions!==null)stats.push(['Porções',fmt(amounts.portions)+' un']);
 if(amounts.kg!==null)stats.push(['Rendimento',fmt(amounts.kg)+' kg']);
 const minutes=positive(r.preparation_time_minutes||r.prep_time_minutes||r.prep_minutes);
 if(minutes)stats.push(['Preparo',fmt(minutes)+' min']);
 const shelf=positive(p.shelf_life_days);
 if(shelf)stats.push(['Validade',fmt(shelf)+(shelf===1?' dia':' dias')]);
 const facts=stats.length?stats.map(([label,value])=>'<div class="fact">'+factIcon(label)+
   '<div><span class="fact-label">'+esc(label)+'</span><span class="fact-value">'+esc(value)+'</span></div></div>').join(''):
   '<div class="fact"><div></div><span class="missing">Informações adicionais não cadastradas</span></div>';
 const intro='<div class="intro'+(photo?'':' no-photo')+'"><div class="quick-facts">'+facts+'</div>'+
   (photo?'<div class="hero-photo"><img src="'+esc(photo)+'" alt="Foto real de '+esc(p.name)+'"></div>':'')+'</div>';
 return '<article class="recipe"><header class="recipe-head"><p class="kicker">Delícias da Vovó · '+esc(category)+'</p>'+
   '<h1>'+esc(p.name)+'</h1><div class="head-rule"></div></header>'+intro+
   '<main class="content"><section><h2>Ingredientes</h2>'+ingredients(r,p,data)+'</section>'+
   '<section><h2>Modo de preparo</h2>'+prepare(r)+'</section></main>'+
   '<footer class="footer"><span>DELÍCIAS DA VOVÓ</span><span>RECEITA Nº '+String(index+1).padStart(2,'0')+'</span></footer></article>';
}
function buildHtml(selection,data,title){
 let previous=null;
 const html=selection.map(({recipe,product},i)=>{
  const category=product.category||'outro';const first=category!==previous;previous=category;
  return article(recipe,product,data,i,first);
 }).join('');
 return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+
  '<title>'+esc(title)+' · Delícias da Vovó</title><style>'+CSS+'</style></head><body>'+
  '<div class="toolbar"><div><strong>'+esc(title)+'</strong><div>'+selection.length+' receitas</div></div>'+
  '<button type="button" onclick="window.print()">Imprimir / Salvar PDF</button></div>'+html+'</body></html>';
}
async function openBook(opts={}){
 const pop=window.open('','_blank');
 if(!pop){window.alert('Permita pop-ups para abrir as receitas.');return false}
 pop.document.open();pop.document.write('<!doctype html><meta charset="utf-8"><p style="padding:35px;font:15px Georgia">Carregando livro…</p>');pop.document.close();
 try{
  if(!window.supabase)throw Error('Biblioteca Supabase indisponível.');
  const sb=window.supabase.createClient(API,KEY);
  const [products,recipes,items,supplies]=await Promise.all(['products','recipes','recipe_items','supplies'].map(t=>fetchAll(sb,t)));
  const productById=new Map(products.map(p=>[String(p.id),p]));
  const data={products,recipes,items,supplies,productById,supplyById:new Map(supplies.map(x=>[String(x.id),x]))};
  let selection=recipes.map(recipe=>({recipe,product:productById.get(String(recipe.product_id))})).filter(x=>x.product);
  if(opts.productName)selection=selection.filter(x=>clean(x.product.name)===clean(opts.productName));
  else if(opts.category&&opts.category!=='todos')selection=selection.filter(x=>(x.product.category||'outro')===opts.category);
  selection.sort((a,b)=>(order.get(a.product.category||'outro')??999)-(order.get(b.product.category||'outro')??999)||
   String(a.product.name).localeCompare(String(b.product.name),'pt-BR'));
  if(!selection.length)throw Error('Nenhuma receita encontrada para a seleção.');
  const title=opts.productName||(opts.category&&opts.category!=='todos'?names[opts.category]||opts.category:'Livro de receitas');
  pop.document.open();pop.document.write(buildHtml(selection,data,title));pop.document.close();return true;
 }catch(e){
  pop.document.open();pop.document.write('<!doctype html><meta charset="utf-8"><p style="font:15px Georgia;padding:32px;color:#992c2c">'+esc(e.message||e)+'</p>');pop.document.close();return false;
 }
}
window.ControleProduLivro=Object.freeze({openBook,buildHtml,yieldInfo});
})();