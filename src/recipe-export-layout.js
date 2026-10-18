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
const CSS="\n@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap');\n@page{size:A4 portrait;margin:15mm}\n*{box-sizing:border-box}html{background:#f0f1ee}body{margin:0;font-family:Lora,Georgia,serif;color:#252c27}\n.toolbar{position:sticky;top:0;z-index:5;background:#fff;padding:14px 25px;display:flex;justify-content:space-between;gap:15px;align-items:center;border-bottom:1px solid #e1e4de;font-size:12px}\n.toolbar strong{color:#294b38}.toolbar button{background:#294b38;color:#fff;border:0;border-radius:8px;padding:12px 17px;font:600 12px Lora,Georgia,serif;cursor:pointer}\n.recipe{background:#fff;width:210mm;min-height:297mm;padding:15mm;margin:22px auto;box-shadow:0 10px 30px #0002;break-before:page;page-break-before:always}\n.recipe:first-of-type{break-before:auto;page-break-before:auto}\n.category-heading{font-size:9pt;text-align:center;letter-spacing:2px;color:#294b38;border-bottom:1px solid #cad3c9;padding-bottom:3mm;margin-bottom:6mm;text-transform:uppercase}\n.photo{width:100%;height:85mm;overflow:hidden;margin-bottom:9mm;break-inside:avoid}.photo img{display:block;width:100%;height:100%;object-fit:cover;object-position:center}\n.recipe-heading{text-align:center;margin:0 0 8mm}.category{font-size:9pt;letter-spacing:1.8px;text-transform:uppercase;color:#6b816d;margin-bottom:3mm}\nh1{margin:0;color:#294b38;font-size:26pt;line-height:1.2;font-weight:400;overflow-wrap:anywhere}\n.line{width:34mm;height:1px;background:#aebbad;margin:5mm auto 0}\n.meta{display:flex;align-items:start;justify-content:center;border-top:1px solid #e5e9e5;border-bottom:1px solid #e5e9e5;padding:3mm 0;margin:0 0 10mm}\n.meta-item{flex:1;text-align:center;padding:0 3mm;border-right:1px solid #e4e9e3}.meta-item:last-child{border:0}\n.meta-item span{display:block;font-size:9pt;color:#708175;margin-bottom:1.5mm}.meta-item b{display:block;color:#294b38;font-size:12pt;font-weight:500}\n.columns{display:grid;grid-template-columns:40fr 60fr;gap:9mm;align-items:start}.columns section{min-width:0}\nh2{font-size:12pt;font-weight:600;color:#294b38;border-bottom:1px solid #d5ded5;padding-bottom:3mm;margin:0 0 4mm}\n.ingredient{display:flex;justify-content:space-between;align-items:baseline;gap:3mm;border-bottom:1px solid #eef0ec;padding:2mm 0;font-size:11pt;line-height:1.5;break-inside:avoid}\n.ingredient span{flex:1;overflow-wrap:anywhere}.ingredient strong{font-weight:500;text-align:right;flex-shrink:0}\n.steps{list-style:none;counter-reset:step;padding:0;margin:0}.steps li{position:relative;padding-left:8mm;margin:0 0 5mm;font-size:11pt;line-height:1.5;overflow-wrap:anywhere;break-inside:avoid}\n.steps li:before{counter-increment:step;content:counter(step);position:absolute;left:0;top:0;width:5mm;height:5mm;border:1px solid #8ba18b;border-radius:50%;color:#294b38;font-size:9pt;display:flex;justify-content:center;align-items:center}\n.observations{margin-top:7mm}.observations h3{font-size:10pt;color:#294b38;margin:0 0 3mm}.observations p{font-size:10pt;line-height:1.5;margin:0}\n.missing{color:#8a978d;font-size:10pt;font-style:italic}.footer{margin-top:15mm;border-top:1px solid #e4e8e3;padding-top:4mm;display:flex;justify-content:space-between;font-size:8pt;color:#7a8b7c;letter-spacing:1px}\n@media print{html{background:#fff}.toolbar{display:none}.recipe{width:180mm;min-height:0;margin:0;padding:0;box-shadow:none}.recipe:not(:first-of-type){break-before:page;page-break-before:always}.columns,.columns section{break-inside:auto}.recipe-heading,.meta,h2{break-after:avoid}}\n";
function article(r,p,data,index,first){
 const category=names[p.category]||p.category||'Outros';
 const parent=inheritedRecipe(r,p,data);
 const photo=safeImage(r.image_url||parent?.image_url||p.image_url||p.photo_url||'');
 const hero=photo?'<div class="photo"><img src="'+esc(photo)+'" alt="Fotografia real de '+esc(p.name)+'"></div>':'';
 const y=yieldInfo(r),meta=[];
 if(y.portions!==null)meta.push(['Porções',fmt(y.portions)+' un']);
 if(y.kg!==null)meta.push(['Rendimento',fmt(y.kg)+' kg']);
 const mins=positive(r.preparation_time_minutes||r.prep_time_minutes||r.prep_minutes);
 if(mins)meta.push(['Preparo',fmt(mins)+' min']);
 const valid=positive(p.shelf_life_days);
 if(valid)meta.push(['Validade',fmt(valid)+(valid===1?' dia':' dias')]);
 const summary=meta.length?'<div class="meta">'+meta.map(([label,val])=>
  '<div class="meta-item"><span>'+esc(label)+'</span><b>'+esc(val)+'</b></div>').join('')+'</div>':'';
 return '<article class="recipe">'+
  (first?'<div class="category-heading">DELÍCIAS DA VOVÓ · '+esc(category)+'</div>':'')+
  hero+'<div class="recipe-heading"><div class="category">'+esc(category)+'</div><h1>'+esc(p.name)+
  '</h1><div class="line"></div></div>'+summary+
  '<div class="columns"><section><h2>Ingredientes</h2>'+ingredients(r,p,data)+'</section>'+
  '<section><h2>Modo de preparo</h2>'+prepare(r)+'</section></div>'+
  '<div class="footer">DELÍCIAS DA VOVÓ <span>RECEITA Nº '+String(index+1).padStart(2,'0')+'</span></div></article>';
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