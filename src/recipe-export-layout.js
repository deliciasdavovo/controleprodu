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
const CSS="\n@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap');\n@page{size:A4 landscape;margin:0}\n*{box-sizing:border-box}\nhtml{background:#eef0ee}\nbody{margin:0;color:#26372b;font-family:Lora,Georgia,serif}\n.toolbar{position:sticky;top:0;z-index:10;display:flex;align-items:center;justify-content:space-between;gap:15px;padding:14px 25px;background:#fff;border-bottom:1px solid #e2e8e0;font-size:12px}\n.toolbar strong{color:#294b38}\n.toolbar button{background:#294b38;color:#fff;border:0;border-radius:7px;padding:12px 18px;cursor:pointer;font:600 12px Lora,Georgia,serif}\n.recipe{width:min(1180px,98vw);aspect-ratio:297/210;min-height:0;display:grid;grid-template-columns:50% 50%;margin:26px auto;background:#fff;box-shadow:0 14px 40px #0002;break-before:page;page-break-before:always;break-inside:avoid}\n.recipe:first-of-type{break-before:auto;page-break-before:auto}\n.photo-page{position:relative;min-width:0;min-height:0;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;background:#f8faf8;color:#294b38}\n.photo-page.has-photo{background:#2e3f31;color:white}\n.photo-page .hero{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center;z-index:0}\n.photo-page.has-photo:after{content:\"\";position:absolute;inset:0;pointer-events:none;background:linear-gradient(to top,rgba(16,28,18,.91),rgba(16,28,18,.43) 25%,transparent 66%),linear-gradient(to bottom,rgba(18,32,20,.34),transparent 21%);z-index:1}\n.topline{z-index:2;position:relative;display:flex;gap:10px;justify-content:space-between;align-items:center;padding:9mm 10mm 3mm;font-size:7.5pt;letter-spacing:1.1px;border:0}\n.topline span:last-child{text-align:right}\n.photo-heading{z-index:2;position:relative;padding:16mm 12mm 13mm}\n.photo-heading .category{text-transform:uppercase;letter-spacing:3px;font-size:10pt;margin-bottom:5mm;font-weight:600}\n.photo-heading h1{font-size:32pt;font-weight:500;line-height:1.12;max-width:100%;overflow-wrap:anywhere;margin:0;text-shadow:0 2px 16px rgba(0,0,0,.18)}\n.photo-heading .accent{width:20mm;height:2px;background:#e1cf98;margin-top:7mm}\n.no-photo .photo-heading h1{text-shadow:none}\n.no-photo .photo-heading .accent{background:#a38d64}\n.info-page{min-width:0;min-height:0;display:flex;flex-direction:column;padding:9mm 11mm 8mm;background:#fff}\n.info-header{display:flex;justify-content:space-between;gap:10px;color:#496452;font-size:7pt;letter-spacing:1.7px;border-bottom:1px solid #d2dbd1;padding-bottom:3.5mm}\n.info-header span:last-child{text-align:right}\n.meta{display:flex;align-items:stretch;justify-content:space-between;padding:6mm 0 4mm;gap:0}\n.metric{min-width:0;flex:1;text-align:center;border-right:1px solid #dce4db;padding:0 2mm}\n.metric:last-child{border-right:0}\n.metric span{display:block;text-transform:uppercase;color:#4b6450;font-size:7pt;letter-spacing:.75px;line-height:1.2;margin-bottom:2mm}\n.metric b{display:block;color:#263a2b;font-size:11.5pt;font-weight:500;line-height:1.3}\n.info-page h2{display:flex;align-items:center;gap:4mm;color:#294b38;text-transform:uppercase;letter-spacing:2px;font-size:11pt;line-height:1.25;font-weight:600;margin:0 0 4mm}\n.info-page h2:after{content:\"\";flex:1;height:1px;background:#abbcac}\n.ingredients{margin-top:5mm}\n.ingredients-grid{columns:2;column-gap:8mm;column-rule:1px solid #e0e6de}\n.ingredient{display:flex;align-items:baseline;justify-content:space-between;gap:2mm;font-size:9pt;line-height:1.5;margin-bottom:1.5mm;padding-bottom:1mm;border-bottom:1px dotted #ced7cb;break-inside:avoid}\n.ingredient span{min-width:0;flex:1;overflow-wrap:anywhere}\n.ingredient strong{font-weight:500;flex-shrink:0;white-space:nowrap;text-align:right}\n.method{margin-top:7mm}\n.steps{list-style:none;counter-reset:step;margin:0;padding:0}\n.steps li{counter-increment:step;position:relative;padding-left:8mm;font-size:9.2pt;line-height:1.55;margin:0 0 3mm;overflow-wrap:anywhere;break-inside:avoid}\n.steps li:before{content:counter(step);position:absolute;top:0;left:0;display:flex;align-items:center;justify-content:center;width:5.2mm;height:5.2mm;border-radius:50%;background:#7e9377;color:white;font-size:8pt;line-height:1}\n.observations{margin:5mm 0 0;border-top:1px solid #d8e0d7;padding-top:3mm}\n.observations h3{margin:0 0 2mm;text-transform:uppercase;letter-spacing:1px;font-size:9pt;color:#294b38}\n.observations p{font-size:9pt;line-height:1.5;margin:0}\n.missing{font-size:9pt;color:#76897a;font-style:italic;margin:0}\n.footer{display:flex;justify-content:space-between;gap:15px;align-items:center;margin-top:auto;padding-top:3mm;border-top:1px solid #e2e7e0;color:#88968a;font-size:7pt;letter-spacing:1px}\n.recipe.compact .info-page{padding:7mm 9mm 6mm}\n.recipe.compact .meta{padding:4mm 0 3mm}\n.recipe.compact .ingredients{margin-top:3mm}\n.recipe.compact .method{margin-top:4mm}\n.recipe.compact .info-page h2{font-size:10pt;margin-bottom:2mm}\n.recipe.compact .ingredient{font-size:8pt;margin-bottom:.5mm;padding-bottom:.5mm}\n.recipe.compact .steps li{font-size:8.2pt;margin-bottom:1.5mm;line-height:1.4}\n.recipe.compact .observations{margin-top:3mm}\n@media screen and (max-width:760px){.recipe{width:980px}.toolbar{width:100%}}\n@media print{\n html{background:white}\n .toolbar{display:none}\n .recipe{width:297mm;min-height:210mm;aspect-ratio:297/210;margin:0;box-shadow:none;break-after:page;page-break-after:always;break-inside:avoid}\n .recipe:last-of-type{break-after:auto;page-break-after:auto}\n .photo-page,.info-page{print-color-adjust:exact;-webkit-print-color-adjust:exact}\n}\n";
function article(r,p,data,index,first){
 const category=names[p.category]||p.category||'Outros';
 const parent=inheritedRecipe(r,p,data);
 const photo=safeImage(r.image_url||parent?.image_url||p.image_url||p.photo_url||'');
 const values=yieldInfo(r),stats=[];
 if(values.portions!==null)stats.push(['Porções',fmt(values.portions)+' un']);
 if(values.kg!==null)stats.push(['Rendimento',fmt(values.kg)+' kg']);
 const minutes=positive(r.preparation_time_minutes||r.prep_time_minutes||r.prep_minutes);
 if(minutes)stats.push(['Preparo',fmt(minutes)+' min']);
 const shelf=positive(p.shelf_life_days);
 if(shelf)stats.push(['Validade',fmt(shelf)+(shelf===1?' dia':' dias')]);
 const meta=stats.length?'<div class="meta">'+stats.map(([label,value])=>
  '<div class="metric"><span>'+esc(label)+'</span><b>'+esc(value)+'</b></div>').join('')+'</div>':'';
 const preparation=prepare(r);
 const components=ingredients(r,p,data);
 const ingredientCount=(components.match(/class="ingredient"/g)||[]).length;
 const longText=String(r.preparation_method||r.instructions||r.notes||'').length;
 const density=ingredientCount>16||longText>1450?' compact':'';
 const name=esc(p.name),safeCategory=esc(category);
 const left='<section class="photo-page '+(photo?'has-photo':'no-photo')+'">'+
  (photo?'<img class="hero" src="'+esc(photo)+'" alt="Foto real de '+name+'">':'')+
  '<div class="topline"><span>DELÍCIAS DA VOVÓ</span><span>RECEITAS DA CASA</span></div>'+
  '<div class="photo-heading"><div class="category">'+safeCategory+'</div>'+
  '<h1>'+name+'</h1><div class="accent"></div></div></section>';
 const right='<section class="info-page"><header class="info-header"><span>RECEITAS DA NOSSA PADARIA</span>'+
  '<span>RECEITA Nº '+String(index+1).padStart(2,'0')+'</span></header>'+
  meta+
  '<section class="ingredients"><h2>Ingredientes</h2><div class="ingredients-grid">'+components+'</div></section>'+
  '<section class="method"><h2>Modo de preparo</h2>'+preparation+'</section>'+
  '<footer class="footer"><span>DELÍCIAS DA VOVÓ</span><span>'+safeCategory+'</span></footer></section>';
 return '<article class="recipe'+density+'">'+left+right+'</article>';
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