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
const RETURN_URL = new URL('./', window.location.href).href;
const CSS="\n@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap');\n@page{size:A4 landscape;margin:0}\n*{box-sizing:border-box}html{background:#edf0eb}body{margin:0;font-family:Lora,Georgia,serif;color:#26352a}\n.toolbar{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid #dce4da;padding:12px 24px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:center;font-size:12px}\n.toolbar strong{color:#294b38}.toolbar-actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap}\n.toolbar .return-app{display:inline-flex;align-items:center;justify-content:center;text-decoration:none;background:#fff;color:#294b38;border:1px solid #bacabb;border-radius:7px;padding:10px 13px;font:600 12px Lora,Georgia,serif;min-height:42px}\n.toolbar button{background:#294b38;border:0;border-radius:7px;color:#fff;padding:11px 15px;cursor:pointer;font:600 12px Lora,Georgia,serif;min-height:42px}\n.sheet{width:297mm;height:210mm;margin:22px auto;background:#fff;box-shadow:0 12px 32px #0002;display:grid;grid-template-columns:1fr 1fr;break-before:page;page-break-before:always;break-inside:avoid}\n.sheet:first-of-type{break-before:auto;page-break-before:auto}\n.half{position:relative;min-width:0;width:148.5mm;height:210mm;overflow:hidden;border-right:1px solid #dfe5dc;background:#fff}\n.half:last-child{border:0}.half.empty{background:#fff}\n.bg-photo{position:absolute;inset:0;z-index:0;pointer-events:none}\n.bg-photo img{display:block;width:100%;height:100%;object-fit:cover;object-position:center;opacity:.20}\n.recipe-content{position:relative;z-index:1;height:100%;display:flex;flex-direction:column;padding:11mm 9mm 8mm}\n.category{text-align:center;font-size:8pt;letter-spacing:1.7px;text-transform:uppercase;color:#5e7662;margin-bottom:2.5mm}\n.recipe-title{text-align:center;text-transform:uppercase;color:#263c2c;font-size:18pt;font-weight:500;line-height:1.2;margin:0;overflow-wrap:anywhere}\n.rule{height:1px;width:26mm;background:#aac0aa;margin:4mm auto 5mm;flex-shrink:0}\n.facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2.5mm;margin-bottom:5mm;flex-shrink:0}\n.fact{background:rgba(255,255,255,.72);padding:2.5mm 3mm;border:1px solid #dce6dc}\n.fact-label{display:block;color:#5a705e;font-size:8pt}.fact-value{display:block;font-size:10pt;font-weight:600;color:#294b38;margin-top:1mm}\n.cols{display:grid;grid-template-columns:minmax(0,42fr) minmax(0,58fr);gap:5.5mm;min-height:0;align-items:start}.cols>section{min-width:0}\n.cols h2{font-size:11pt;color:#294b38;font-weight:600;margin:0 0 3mm}\n.ingredient{display:flex;justify-content:space-between;align-items:baseline;gap:1.5mm;margin-bottom:1.7mm;font-size:8.7pt;line-height:1.47;break-inside:avoid}\n.ingredient span{flex:1;min-width:0;overflow-wrap:anywhere}.ingredient strong{font-size:8.3pt;white-space:nowrap;font-weight:600}\n.steps{list-style:none;counter-reset:step;padding:0;margin:0}\n.steps li{counter-increment:step;position:relative;padding-left:5mm;margin:0 0 2.5mm;font-size:8.7pt;line-height:1.53;overflow-wrap:anywhere;break-inside:avoid}\n.steps li:before{content:counter(step) \".\";position:absolute;left:0;font-weight:600;color:#4d7653}\n.observations{margin-top:4mm;padding-top:3mm;border-top:1px solid #bccdbc}.observations h3{font-size:9pt;color:#294b38;margin:0 0 2mm}\n.observations p{margin:0;font-size:8.5pt;line-height:1.48}.missing{font-size:8pt;color:#768877;font-style:italic}\n.footer{margin-top:auto;padding-top:3mm;border-top:1px solid #dce5d9;display:flex;justify-content:space-between;gap:6px;color:#748475;letter-spacing:.6px;font-size:7.1pt;flex-shrink:0}\n.half.compact .recipe-content{padding:8mm 7mm 6mm}.half.compact .recipe-title{font-size:16pt}.half.compact .rule{margin:3mm auto}\n.half.compact .facts{gap:1mm;margin-bottom:3mm}.half.compact .fact{padding:1.5mm}\n.half.compact .cols{gap:4mm}.half.compact .ingredient{font-size:8pt;line-height:1.38;margin-bottom:1mm}\n.half.compact .ingredient strong{font-size:7.7pt}.half.compact .steps li{font-size:8pt;line-height:1.4;margin-bottom:1.8mm}\n.half.dense .recipe-content{padding:7mm 6mm 5mm}.half.dense .recipe-title{font-size:14pt}\n.half.dense .facts{gap:1mm;margin-bottom:2mm}.half.dense .fact{padding:1mm}\n.half.dense .cols h2{font-size:9.5pt;margin-bottom:2mm}\n.half.dense .ingredient,.half.dense .steps li{font-size:7.3pt;line-height:1.27;margin-bottom:1mm}\n.half.dense .ingredient strong{font-size:7pt}.half.dense .observations{margin-top:2mm;padding-top:1.5mm}\n@media screen and (max-width:600px){.toolbar{padding:12px 14px;align-items:flex-start}.toolbar-actions{width:100%;display:grid;grid-template-columns:1fr 1fr;gap:8px}.toolbar .return-app,.toolbar button{width:100%;padding:10px 7px;font-size:11px}}\n@media print{html{background:#fff}.toolbar{display:none}.sheet{width:297mm;height:210mm;margin:0;box-shadow:none;break-before:page;page-break-before:always}.sheet:first-of-type{break-before:auto;page-break-before:auto}.sheet:last-of-type{break-after:auto;page-break-after:auto}.bg-photo img{print-color-adjust:exact;-webkit-print-color-adjust:exact}}\n";

function recipeCard(r,p,data,index){
 const parent=inheritedRecipe(r,p,data);
 const category=names[p.category]||p.category||'Outros';
 const photo=safeImage(r.image_url||parent?.image_url||p.image_url||p.photo_url||'');
 const amounts=yieldInfo(r),facts=[];
 if(amounts.portions!==null)facts.push(['Porções',fmt(amounts.portions)+' un']);
 if(amounts.kg!==null)facts.push(['Rendimento',fmt(amounts.kg)+' kg']);
 const mins=positive(r.preparation_time_minutes||r.prep_time_minutes||r.prep_minutes);
 if(mins)facts.push(['Preparo',fmt(mins)+' min']);
 const valid=positive(p.shelf_life_days);
 if(valid)facts.push(['Validade',fmt(valid)+(valid===1?' dia':' dias')]);
 const factHtml=facts.length?'<div class="facts">'+facts.map(([label,value])=>
  '<div class="fact"><span class="fact-label">'+esc(label)+'</span><strong class="fact-value">'+esc(value)+'</strong></div>').join('')+'</div>':'';
 const ingr=ingredients(r,p,data);
 const size=(ingr.match(/class="ingredient"/g)||[]).length;
 const prepLength=String(r.preparation_method||r.instructions||r.notes||'').length;
 const density=size>=22||prepLength>1250?' compact dense':size>=13||prepLength>750?' compact':'';
 return '<section class="half'+density+'">'+
  (photo?'<div class="bg-photo"><img src="'+esc(photo)+'" alt="" aria-hidden="true"></div>':'')+
  '<div class="recipe-content"><div class="category">'+esc(category)+'</div>'+
  '<h1 class="recipe-title">'+esc(p.name)+'</h1><div class="rule"></div>'+factHtml+
  '<div class="cols"><section><h2>Ingredientes</h2>'+ingr+'</section>'+
  '<section><h2>Modo de preparo</h2>'+prepare(r)+'</section></div>'+
  '<footer class="footer"><span>DELÍCIAS DA VOVÓ</span>'+
  '<span>RECEITA Nº '+String(index+1).padStart(2,'0')+'</span></footer></div></section>';
}
function pagesHtml(selection,data){
 let html='';
 for(let i=0;i<selection.length;i+=2){
  const left=selection[i],right=selection[i+1];
  html+='<article class="sheet">'+recipeCard(left.recipe,left.product,data,i)+
    (right?recipeCard(right.recipe,right.product,data,i+1):'<section class="half empty"></section>')+'</article>';
 }
 return html;
}
function backControl(){
 return '<a class="return-app" data-preview-back href="'+esc(RETURN_URL)+'" '+
  'onclick="try{if(window.opener&&!window.opener.closed){window.opener.focus();window.close();if(window.closed)return false}}catch(e){}">← Voltar ao Controle Produ</a>';
}
function buildHtml(selection,data,title){
 return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'+
  '<meta name="viewport" content="width=device-width,initial-scale=1">'+
  '<title>'+esc(title)+' · Delícias da Vovó</title><style>'+CSS+'</style></head><body>'+
  '<div class="toolbar"><div><strong>'+esc(title)+'</strong><div>'+selection.length+
  (selection.length===1?' receita':' receitas')+' · duas por folha</div></div>'+
  '<div class="toolbar-actions">'+backControl()+
  '<button type="button" onclick="window.print()">Imprimir / Salvar PDF</button></div></div>'+
  pagesHtml(selection,data)+'</body></html>';
}
async function openBook(opts={}){
 const pop=window.open('','_blank');
 if(!pop){window.alert('Permita pop-ups para abrir as receitas.');return false}
 pop.document.open();pop.document.write('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+CSS+'</style><div class="toolbar"><strong>Preparando o livro…</strong>'+backControl()+'</div><p style="padding:35px;font:15px Georgia">Carregando livro…</p>');pop.document.close();
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
  pop.document.open();pop.document.write('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>'+CSS+'</style><div class="toolbar"><strong>Não foi possível gerar o PDF</strong>'+backControl()+'</div><p style="font:15px Georgia;padding:32px;color:#992c2c">'+esc(e.message||e)+'</p>');pop.document.close();return false;
 }
}
window.ControleProduLivro=Object.freeze({openBook,buildHtml,yieldInfo});
})();