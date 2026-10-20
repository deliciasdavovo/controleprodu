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
// O nome comercial do insumo continua no cadastro para compras e CMV.
// No livro de produção, mostramos apenas o ingrediente culinário relevante.
function nomeIngredienteNoLivro(nomeOriginal){
 const nome=String(nomeOriginal||'').replace(/\s+/g,' ').trim();
 const normalizado=clean(nome);
 const chocolateEmPo=/\bchocolate\s+(?:em\s+)?po\b/.test(normalizado);
 if(chocolateEmPo){
  // Preserva a concentração: 33%, 50% e 70% não são intercambiáveis.
  const concentracao=nome.match(/(?:^|[^\d])(\d{1,3})\s*(?:%|por\s*cento)/i);
  if(concentracao){
   const percentual=Number(concentracao[1]);
   if(percentual>0&&percentual<=100)return 'Chocolate em pó '+percentual+'%';
  }
  // Identificação solicitada para o chocolate em pó Melken de 2 kg.
  // Não aplica 50% a outros chocolates quando a concentração é desconhecida.
  if(/\bmelken\b/.test(normalizado)&&/\b2\s*(?:kg|quilo|quilos)\b/.test(normalizado)){
   return 'Chocolate em pó 50%';
  }
 }
 return nome;
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
  const label=nomeIngredienteNoLivro(supply?.name||product?.name||'Ingrediente não identificado');
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
const CSS="\n@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&display=swap');\n@page{size:A4 landscape;margin:0}\n*{box-sizing:border-box}\nhtml{background:#f0f0ed}\nbody{margin:0;font-family:Lora,Georgia,serif;color:#242721}\n.toolbar{position:sticky;top:0;z-index:5;background:#fff;border-bottom:1px solid #dce1da;padding:12px 24px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;font-size:12px}\n.toolbar strong{color:#294b38}\n.toolbar-actions{display:flex;align-items:center;gap:9px;flex-wrap:wrap}\n.toolbar .return-app{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:10px 13px;background:#fff;color:#294b38;border:1px solid #bacabb;border-radius:7px;text-decoration:none;font:600 12px Lora,Georgia,serif}\n.toolbar button{background:#294b38;border:0;border-radius:7px;color:#fff;padding:11px 15px;cursor:pointer;min-height:42px;font:600 12px Lora,Georgia,serif}\n.sheet{width:297mm;height:210mm;display:grid;grid-template-columns:1fr 1fr;margin:22px auto;background:#fff;box-shadow:0 12px 32px #0002;break-before:page;page-break-before:always;break-inside:avoid}\n.sheet:first-of-type{break-before:auto;page-break-before:auto}\n.half{--accent:#b88a5a;--accent-soft:#f6f1eb;--accent-border:#dfcdb9;width:148.5mm;height:210mm;position:relative;min-width:0;min-height:0;overflow:hidden;border-right:1px solid #dedede;background:white}\n.half:last-child{border-right:0}.half.empty{background:#fff}\n.recipe-content{height:100%;display:flex;flex-direction:column;padding:10mm 9mm 8mm;background:#fff}\n.recipe-head{text-align:center;margin:0 0 6mm}\n.recipe-head .category{text-transform:uppercase;letter-spacing:1.6px;font-size:7.5pt;margin:0 0 2.5mm;color:#737b6c}\n.recipe-title{text-transform:uppercase;font-weight:500;letter-spacing:1px;font-size:17pt;line-height:1.3;color:#252923;overflow-wrap:anywhere;margin:0}\n.recipe-head .rule{width:23mm;height:1px;background:var(--accent);margin:4mm auto 0}\n.intro{width:100%;height:52mm;display:grid;grid-template-columns:34% 66%;margin:0 0 7mm;flex-shrink:0;border:1px solid var(--accent-border);border-radius:2mm;overflow:hidden;background:var(--accent-soft)}\n.intro.no-photo{grid-template-columns:1fr;height:auto;min-height:33mm}\n.quick-facts{padding:4.8mm 3.5mm;background:var(--accent-soft);display:flex;flex-direction:column;justify-content:center;gap:3mm}\n.intro.no-photo .quick-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:3mm}\n.fact{display:grid;grid-template-columns:6mm 1fr;align-items:start;gap:1.5mm;min-width:0}\n.fact svg{width:5.5mm;height:5.5mm;stroke:#565c52;stroke-width:1.3;fill:none;stroke-linecap:round;stroke-linejoin:round}\n.fact-label{display:block;font-size:7.3pt;font-weight:600;color:#3b453c;line-height:1.2}\n.fact-value{display:block;font-size:8.7pt;font-weight:400;line-height:1.42;color:#222c23;margin-top:.5mm;overflow-wrap:anywhere}\n.photo{background:var(--accent-soft);overflow:hidden;min-width:0;min-height:0;border-left:1px solid var(--accent-border)}\n.photo img{display:block;width:100%;height:100%;object-fit:cover;object-position:center;opacity:1;filter:none}\n.cols{display:grid;grid-template-columns:minmax(0,40fr) minmax(0,60fr);gap:6mm;align-items:start}\n.cols>section{min-width:0}\n.cols h2{margin:0 0 4mm;font-size:11pt;line-height:1.3;font-weight:600;color:#252a24}\n.ingredient{display:flex;justify-content:space-between;align-items:baseline;gap:1.7mm;font-size:8.9pt;line-height:1.5;margin-bottom:1.5mm;break-inside:avoid}\n.ingredient span{flex:1;min-width:0;overflow-wrap:anywhere}\n.ingredient strong{flex-shrink:0;white-space:nowrap;font-size:8.2pt;font-weight:500;text-align:right}\n.steps{list-style:none;counter-reset:step;padding:0;margin:0}\n.steps li{position:relative;padding-left:5mm;counter-increment:step;font-size:8.9pt;line-height:1.6;margin:0 0 3.1mm;overflow-wrap:anywhere;break-inside:avoid}\n.steps li:before{content:counter(step) \".\";position:absolute;left:0;top:0;color:#576951;font-weight:600}\n.observations{margin-top:6mm}.observations h3{font-size:9.1pt;font-weight:600;font-style:italic;margin:0 0 2.5mm;color:#39493a}.observations p{font-size:8.6pt;line-height:1.5;margin:0}\n.missing{font-size:8.8pt;color:#7c857a;font-style:italic}\n.footer{margin-top:auto;flex-shrink:0;padding-top:3mm;border-top:1px solid #e3e7e1;display:flex;justify-content:space-between;gap:6px;letter-spacing:.5px;font-size:7pt;color:#7f897f}\n.half.compact .recipe-content{padding:8mm 7mm 6mm}\n.half.compact .recipe-head{margin-bottom:4mm}\n.half.compact .recipe-title{font-size:15pt}\n.half.compact .intro{height:44mm;margin-bottom:5mm}\n.half.compact .cols h2{font-size:10pt;margin-bottom:2.5mm}\n.half.compact .ingredient,.half.compact .steps li{font-size:8pt;line-height:1.39;margin-bottom:1.4mm}\n.half.compact .ingredient strong{font-size:7.5pt}\n.half.dense .recipe-content{padding:7mm 6mm 5mm}\n.half.dense .recipe-title{font-size:14pt}\n.half.dense .intro{height:35mm;margin-bottom:3mm}\n.half.dense .fact{gap:1mm}\n.half.dense .quick-facts{padding:2mm;gap:1.7mm}\n.half.dense .cols h2{font-size:9.5pt}\n.half.dense .ingredient,.half.dense .steps li{font-size:7.3pt;line-height:1.28;margin-bottom:1mm}\n.half.dense .ingredient strong{font-size:7pt}\n@media screen and (max-width:600px){.toolbar{padding:12px 14px;align-items:flex-start}.toolbar-actions{width:100%;display:grid;grid-template-columns:1fr 1fr;gap:8px}.toolbar .return-app,.toolbar button{width:100%;padding:10px 7px;font-size:11px}}\n@media print{html{background:#fff}.intro,.quick-facts,.photo{-webkit-print-color-adjust:exact;print-color-adjust:exact}.toolbar{display:none}.sheet{width:297mm;height:210mm;margin:0;box-shadow:none;break-before:page;page-break-before:always}.sheet:first-of-type{break-before:auto;page-break-before:auto}.sheet:last-of-type{break-after:auto;page-break-after:auto}.photo img{-webkit-print-color-adjust:exact;print-color-adjust:exact}}\n";

function factIcon(label){
 const icons={
  'Porções':'<path d="M4 2v8M7 2v8M10 2v8M4 7h6M7 10v12M17 2v20M17 2c5 3 5 10 0 12"/>',
  'Rendimento':'<path d="M4 5h16M7 5l-4 9h8L7 5M17 5l-4 9h8l-4-9M12 3v18M7 21h10"/>',
  'Preparo':'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>',
  'Validade':'<rect x="3" y="5" width="18" height="16" rx="1"/><path d="M7 3v4M17 3v4M3 10h18M7 14h2M12 14h2"/>'
 };
 return '<svg viewBox="0 0 24 24" aria-hidden="true">'+(icons[label]||icons['Preparo'])+'</svg>';
}
function recipeCard(r,p,data,index){
 const parent=inheritedRecipe(r,p,data);
 const category=names[p.category]||p.category||'Outros';
 const photo=safeImage(r.image_url||parent?.image_url||p.image_url||p.photo_url||'');
 const values=yieldInfo(r),facts=[];
 if(values.portions!==null)facts.push(['Porções',fmt(values.portions)+' un']);
 if(values.kg!==null)facts.push(['Rendimento',fmt(values.kg)+' kg']);
 const minutes=positive(r.preparation_time_minutes||r.prep_time_minutes||r.prep_minutes);
 if(minutes)facts.push(['Preparo',fmt(minutes)+' min']);
 const valid=positive(p.shelf_life_days);
 if(valid)facts.push(['Validade',fmt(valid)+(valid===1?' dia':' dias')]);
 const factHtml=facts.length?facts.map(([label,val])=>'<div class="fact">'+factIcon(label)+
  '<div><span class="fact-label">'+esc(label)+'</span><span class="fact-value">'+esc(val)+'</span></div></div>').join(''):'';
 const image=photo?'<div class="photo"><img src="'+esc(photo)+'" alt="Foto colorida de '+esc(p.name)+'"></div>':'';
 const upper=facts.length||photo?'<div class="intro'+(photo?'':' no-photo')+'"><div class="quick-facts">'+
  factHtml+'</div>'+image+'</div>':'';
 const ing=ingredients(r,p,data);
 const ingLength=(ing.match(/class="ingredient"/g)||[]).length;
 const textLength=String(r.preparation_method||r.instructions||r.notes||'').length;
 const density=ingLength>21||textLength>1300?' compact dense':ingLength>12||textLength>750?' compact':'';
 return '<section class="half'+density+'"><div class="recipe-content">'+
  '<header class="recipe-head"><div class="category">'+esc(category)+'</div>'+
  '<h1 class="recipe-title">'+esc(p.name)+'</h1><div class="rule"></div></header>'+
  upper+'<div class="cols"><section><h2>Ingredientes</h2>'+ing+'</section>'+
  '<section><h2>Modo de preparo</h2>'+prepare(r)+'</section></div>'+
  '<footer class="footer"><span>DELÍCIAS DA VOVÓ</span><span>RECEITA Nº '+
  String(index+1).padStart(2,'0')+'</span></footer></div></section>';
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

const PHOTO_ACCENTS = `<script>
(function(){
 'use strict';
 function apply(img){
  try{
   var canvas=document.createElement('canvas'),ctx=canvas.getContext('2d',{willReadFrequently:true});
   canvas.width=32;canvas.height=32;
   ctx.drawImage(img,0,0,32,32);
   var pixels=ctx.getImageData(0,0,32,32).data;
   var buckets=new Map();
   for(var i=0;i<pixels.length;i+=4){
    if(pixels[i+3]<230)continue;
    var r=pixels[i],g=pixels[i+1],b=pixels[i+2];
    var max=Math.max(r,g,b),min=Math.min(r,g,b);
    if(max>243&&min>232)continue;
    if(max<28)continue;
    var key=[Math.round(r/32),Math.round(g/32),Math.round(b/32)].join('-');
    var weight=1+(max-min)/255;
    var v=buckets.get(key)||{r:0,g:0,b:0,w:0};
    v.r+=r*weight;v.g+=g*weight;v.b+=b*weight;v.w+=weight;buckets.set(key,v);
   }
   var best=null;
   buckets.forEach(function(v){if(!best||v.w>best.w)best=v});
   if(!best)return;
   var r=best.r/best.w,g=best.g/best.w,b=best.b/best.w;
   // Acento mais suave e escuro para manter elegância e contraste no papel.
   var accent=[r,g,b].map(function(c){return Math.round(c*.64+83*.36)});
   var soft=[r,g,b].map(function(c){return Math.round(c*.08+249*.92)});
   var border=[r,g,b].map(function(c){return Math.round(c*.26+222*.74)});
   var half=img.closest('.half');if(!half)return;
   half.style.setProperty('--accent','rgb('+accent.join(',')+')');
   half.style.setProperty('--accent-soft','rgb('+soft.join(',')+')');
   half.style.setProperty('--accent-border','rgb('+border.join(',')+')');
  }catch(e){/* Foto externa sem permissão de leitura: mantém cor neutra. */}
 }
 function init(){
  document.querySelectorAll('.half .photo img').forEach(function(img){
   if(img.complete&&img.naturalWidth)apply(img);
   else img.addEventListener('load',function(){apply(img)},{once:true});
  });
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
<\/script>`;

function buildHtml(selection,data,title){
 return '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'+
  '<meta name="viewport" content="width=device-width,initial-scale=1">'+
  '<title>'+esc(title)+' · Delícias da Vovó</title><style>'+CSS+'</style></head><body>'+
  '<div class="toolbar"><div><strong>'+esc(title)+'</strong><div>'+selection.length+
  (selection.length===1?' receita':' receitas')+' · duas por folha</div></div>'+
  '<div class="toolbar-actions">'+backControl()+
  '<button type="button" onclick="window.print()">Imprimir / Salvar PDF</button></div></div>'+
  pagesHtml(selection,data)+PHOTO_ACCENTS+'</body></html>';
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