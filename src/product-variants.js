(function(){
"use strict";
/* Receitas e sabores em grade: cada linha é um sabor do produto principal.
 * A massa fica só na ficha da base; cada sabor guarda a quantidade da base e
 * os recheios que mudam. O CMV é calculado ao vivo com as contas do app
 * (window.ControleCMV), e tudo é salvo de uma vez. */
const endpoint="https://rnycjwlmzpackuodflki.supabase.co", key="sb_publishable_W9Z02Rr3nlUqS1ec5_OCiw_Ezoc_iWk";
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const norm=v=>String(v||"").normalize("NFD").replace(/[̀-ͯ]/g,"").toLocaleLowerCase("pt-BR").trim();
const brl=n=>Number(n||0).toLocaleString("pt-BR",{style:"currency",currency:"BRL"});
const num=v=>{const t=String(v??"").replace(/r\$\s*/i,"").trim();if(!t)return NaN;return Number(t.includes(",")?t.replace(/\./g,"").replace(",","."):t);};
let sb, products=[], recipes=[], recipeItems=[], supplies=[], purchases=[], mapped=null;
let currentId="", rows=[], seq=0, saving=false;
function client(){if(!window.supabase)throw Error("Biblioteca Supabase indisponível");return sb||(sb=window.supabase.createClient(endpoint,key,{auth:{persistSession:true,storageKey:"sb-"+new URL(endpoint).hostname.split(".")[0]+"-auth-token"}}));}
async function load(){
 const fetchTable=async(table,order)=>{const rows=[];for(let start=0;start<20000;start+=1000){let q=client().from(table).select("*");if(order)q=q.order(order);const {data,error}=await q.range(start,start+999);if(error)throw error;rows.push(...(data||[]));if(!data||data.length<1000)break;}return rows;};
 [products,recipes,recipeItems,supplies,purchases]=await Promise.all([fetchTable("products","name"),fetchTable("recipes"),fetchTable("recipe_items"),fetchTable("supplies"),fetchTable("supply_purchases")]);
 supplies.sort((a,b)=>a.name.localeCompare(b.name,"pt-BR"));
 const C=window.ControleCMV;
 mapped=C?{products:products.map(C.fromProduct),recipes:recipes.map(C.fromRecipe),items:recipeItems.map(C.fromRecipeItem),supplies:supplies.map(C.fromSupply),purchases:purchases.map(C.fromSupplyPurchase)}:null;
}
function byId(id){return products.find(p=>p.id===id);}
function parents(){return products.filter(p=>!p.parent_product_id);}
function children(id){return products.filter(p=>p.parent_product_id===id).sort((a,b)=>(a.variant_sort_order||0)-(b.variant_sort_order||0)||a.name.localeCompare(b.name,"pt-BR"));}
function ficha(id){return recipes.find(r=>String(r.product_id)===String(id));}
function ingredientes(id){const r=ficha(id);return r?recipeItems.filter(i=>String(i.recipe_id)===String(r.id)):[];}
function unidade(id,tipo){return tipo==="supply"?(supplies.find(i=>String(i.id)===String(id))?.unit||"un"):(ficha(id)?.yield_unit||"un");}
function nomeComponente(x){return x.type==="supply"?supplies.find(s=>s.id===x.ref)?.name:byId(x.ref)?.name;}
function baseUnit(){return ficha(currentId)?.yield_unit||"un";}
function baseOk(){return !!ficha(currentId)&&ingredientes(currentId).length>0;}
function evitarCircular(componente,produto,visitados=new Set()){
 if(componente===produto)return true;
 if(visitados.has(componente))return false;visitados.add(componente);
 return ingredientes(componente).some(i=>i.component_product_id&&evitarCircular(i.component_product_id,produto,visitados));
}
function unidadesPara(u){const units=[u];if(u==="g")units.push("kg");else if(u==="kg")units.push("g");else if(u==="ml")units.push("L");else if(u==="L")units.push("ml");return units;}
function opcoesComponentes(sel){
 return '<option value="">Escolher recheio…</option>'+
 '<optgroup label="Insumos">'+supplies.map(i=>'<option value="supply:'+esc(i.id)+'"'+(sel==="supply:"+i.id?" selected":"")+'>'+esc(i.name)+'</option>').join("")+'</optgroup>'+
 '<optgroup label="Preparos da padaria">'+products.filter(i=>i.id!==currentId&&!!ficha(i.id)).map(i=>'<option value="product:'+esc(i.id)+'"'+(sel==="product:"+i.id?" selected":"")+'>'+esc(i.name)+'</option>').join("")+'</optgroup>';
}

/* ---------- modelo da grade ---------- */
function rowFromProduct(v){
 const baseItem=ingredientes(v.id).find(i=>String(i.component_product_id)===String(currentId));
 const old=ingredientes(v.id),r=ficha(v.id);
 return {key:"r"+(++seq),id:v.id,variant:v.variant_name||"",baseQty:baseItem?.qty??(baseUnit()==="un"?1:""),
  yieldQty:r?.yield_qty||1,yieldUnit:r?.yield_unit||"un",price:v.price??0,
  extras:old.filter(i=>i.id!==baseItem?.id).map(i=>({id:i.id,type:i.supply_id?"supply":"product",ref:i.supply_id||i.component_product_id,qty:i.qty,unit:i.usage_unit||unidade(i.supply_id||i.component_product_id,i.supply_id?"supply":"product")})),
  legacy:old.length>0&&!baseItem,reviewed:false,dirty:false,open:false,error:""};
}
function newRow(from){
 const base=byId(currentId),last=from||rows[rows.length-1];
 return {key:"r"+(++seq),id:null,variant:"",baseQty:last?last.baseQty:(baseUnit()==="un"?1:""),yieldQty:last?last.yieldQty:1,yieldUnit:last?last.yieldUnit:"un",
  price:last?last.price:(base?.price??0),extras:from?from.extras.map(x=>({...x,id:undefined})):[],legacy:false,reviewed:false,dirty:true,open:!from,error:""};
}
function buildRows(){rows=children(currentId).map(rowFromProduct);}
function rowByKey(k){return rows.find(r=>r.key===k);}
function pending(){return rows.filter(r=>r.dirty);}

function validate(r){
 const v=r.variant.trim();
 if(!v)return "Informe o sabor.";
 if(rows.some(o=>o!==r&&norm(o.variant)===norm(v)))return "Sabor repetido na grade.";
 if(!(num(r.baseQty)>0))return "Quantidade da base inválida.";
 if(!(num(r.yieldQty)>0))return "Rendimento inválido.";
 const p=num(r.price);if(!Number.isFinite(p)||p<0)return "Preço inválido.";
 if(!r.id&&!r.extras.length)return "Escolha ao menos um recheio.";
 if(r.legacy&&!r.reviewed)return "Ficha antiga: confira os ingredientes.";
 const refs=new Set();
 for(const x of r.extras){
  if(!x.ref||!(num(x.qty)>0))return "Complete recheio e quantidade.";
  const k=x.type+":"+x.ref;if(refs.has(k))return "Recheio repetido.";refs.add(k);
  if(x.type==="product"&&(x.ref===currentId||(r.id&&evitarCircular(x.ref,r.id))))return "Recheio criaria receita circular.";
 }
 if(r.id&&evitarCircular(currentId,r.id))return "Receita circular com a base.";
 return "";
}

/* CMV ao vivo: monta uma ficha temporária com a base + recheios e usa as
 * mesmas funções do app. Sem a ponte (versão antiga em cache), mostra “—”. */
function calc(r){
 const C=window.ControleCMV;if(!C||!mapped)return null;
 const base=byId(currentId),pid="__sabor__",rid="__sabor_ficha__";
 const recipe={id:rid,productId:pid,yieldQty:num(r.yieldQty)||0,yieldUnit:r.yieldUnit||"un",weightPerUnit:null};
 const items=[{id:"b",recipeId:rid,componentProductId:currentId,supplyId:null,qty:num(r.baseQty)||0,usageUnit:baseUnit()}]
  .concat(r.extras.filter(x=>x.ref).map((x,i)=>({id:"x"+i,recipeId:rid,supplyId:x.type==="supply"?x.ref:null,componentProductId:x.type==="product"?x.ref:null,qty:num(x.qty)||0,usageUnit:x.unit})));
 const prod={id:pid,name:r.variant,priceUnit:base?.price_unit||"un",manualCost:0};
 const f=C.fichaDoProduto(pid,mapped.recipes.concat(recipe),mapped.items.concat(items),mapped.supplies,mapped.purchases,mapped.products.concat(prod));
 const custo=C.custoPorUnidadeDeVenda(prod,f),cmv=C.calcularCmv(custo,num(r.price)||0);
 return {custo,cmv,pendente:!!f?.custoPendente,status:cmv>0?C.getCmvStatus(cmv,"fabricacao").label:""};
}
function baseResumo(){
 const C=window.ControleCMV,f=C&&mapped?C.fichaDoProduto(currentId,mapped.recipes,mapped.items,mapped.supplies,mapped.purchases,mapped.products):null;
 if(!f)return "";const y=Number(f.yieldQty)||0;
 return y>0&&f.custo>0?" · custo "+brl(f.custo/y)+" por "+esc(f.yieldUnit||"un"):"";
}

/* ---------- desenho ---------- */
function msg(t,error){const el=document.getElementById("pv-status");if(el){el.textContent=t;el.classList.toggle("pv-error",!!error);}}
function resumoExtras(r){
 const ok=r.extras.filter(x=>x.ref);
 if(!ok.length)return '<span class="pv-muted">'+(r.extras.length?'Escolher recheio…':'+ recheio')+'</span>';
 return ok.map(x=>esc(nomeComponente(x)||"?")+(x.qty?' <small>'+esc(x.qty)+' '+esc(x.unit)+'</small>':"")).join(", ");
}
function rowHtml(r){
 const units=["un","kg","g","ml","L"];
 const badge=r.error?'<span class="pv-badge is-error" title="'+esc(r.error)+'">!</span>':!r.id?'<span class="pv-badge is-new" title="Novo">novo</span>':r.dirty?'<span class="pv-badge is-dirty" title="Alterado">•</span>':r.legacy?'<span class="pv-badge is-error" title="Ficha antiga para revisar">!</span>':"";
 let h='<tr class="pv-main'+(r.open?' is-open':'')+'">'+
  '<td class="pv-c-state">'+badge+'</td>'+
  '<td><input data-f="variant" value="'+esc(r.variant)+'" placeholder="Ex.: Doce de leite" maxlength="100" aria-label="Sabor"></td>'+
  '<td><div class="pv-unit"><input data-f="baseQty" inputmode="decimal" value="'+esc(r.baseQty)+'" aria-label="Quantidade da base"><span>'+esc(baseUnit())+'</span></div></td>'+
  '<td><button type="button" class="pv-extras" data-toggle aria-expanded="'+r.open+'">'+resumoExtras(r)+'</button></td>'+
  '<td><div class="pv-unit"><input data-f="yieldQty" inputmode="decimal" value="'+esc(r.yieldQty)+'" aria-label="Rendimento"><select data-f="yieldUnit" aria-label="Unidade produzida">'+units.map(u=>'<option'+(u===r.yieldUnit?' selected':'')+'>'+u+'</option>').join("")+'</select></div></td>'+
  '<td><input data-f="price" inputmode="decimal" value="'+esc(r.price)+'" aria-label="Preço de venda"></td>'+
  '<td class="pv-num" data-out="custo">—</td><td class="pv-num" data-out="cmv">—</td>'+
  '<td class="pv-c-act"><button type="button" data-dup title="Duplicar sabor" aria-label="Duplicar">⧉</button>'+(r.id?'':'<button type="button" data-del title="Remover linha" aria-label="Remover linha">×</button>')+'</td></tr>';
 if(r.open){
  h+='<tr class="pv-detail"><td></td><td colspan="8">'+
   (r.legacy?'<div class="pv-alert"><strong>Ficha antiga independente.</strong> Este produto já tinha ingredientes próprios. Remova abaixo os itens da massa antes de vincular a base, para não contar custo em dobro.<label class="pv-check"><input type="checkbox" data-reviewed'+(r.reviewed?' checked':'')+'> Conferi e retirei a massa duplicada</label></div>':'')+
   '<div class="pv-ings">'+r.extras.map((x,i)=>{
     const ref=x.ref?x.type+":"+x.ref:"",u=x.ref?unidade(x.ref,x.type):"un";
     return '<div class="pv-ingredient" data-i="'+i+'"><select data-x="ref" aria-label="Recheio">'+opcoesComponentes(ref)+'</select>'+
      '<input data-x="qty" inputmode="decimal" value="'+esc(x.qty??"")+'" placeholder="Qtd" aria-label="Quantidade">'+
      '<select data-x="unit" aria-label="Unidade">'+unidadesPara(u).map(u0=>'<option'+(u0===x.unit?' selected':'')+'>'+esc(u0)+'</option>').join("")+'</select>'+
      '<button type="button" data-xdel aria-label="Remover recheio">×</button></div>';
   }).join("")+'</div><button type="button" class="pv-link" data-xadd>+ Recheio ou complemento</button>'+
   (r.error?'<p class="pv-row-error">'+esc(r.error)+'</p>':'')+'</td></tr>';
 }
 return h;
}
function mountRow(r){
 const old=document.querySelector('#pv-grid tbody[data-key="'+r.key+'"]');
 const tb=document.createElement("tbody");tb.dataset.key=r.key;tb.innerHTML=rowHtml(r);
 if(old)old.replaceWith(tb);else document.querySelector("#pv-grid").appendChild(tb);
 bindRow(r,tb);updateCalc(r,tb);
}
function updateCalc(r,tb){
 tb=tb||document.querySelector('#pv-grid tbody[data-key="'+r.key+'"]');if(!tb)return;
 const c=calc(r),cu=tb.querySelector('[data-out="custo"]'),cm=tb.querySelector('[data-out="cmv"]');
 if(!c){cu.textContent="—";cm.textContent="—";cm.className="pv-num";return;}
 cu.textContent=c.pendente?"pendente":c.custo>0?brl(c.custo):"—";
 cu.title=c.pendente?"Algum insumo tem conversão de unidade pendente no cadastro.":"";
 cm.textContent=c.cmv>0?c.cmv.toLocaleString("pt-BR",{maximumFractionDigits:1})+"%":"—";
 cm.className="pv-num pv-cmv"+(c.status?" is-"+norm(c.status).replace(/\s/g,""):"");
 cm.title=c.status?"CMV "+c.status+" (meta de fabricação: até 28%)":"";
}
function touch(r,tb){r.dirty=true;r.error="";const b=tb.querySelector(".pv-c-state");if(b&&!r.error)b.innerHTML=!r.id?'<span class="pv-badge is-new">novo</span>':'<span class="pv-badge is-dirty" title="Alterado">•</span>';updateCalc(r,tb);updateFooter();}
function bindRow(r,tb){
 tb.querySelectorAll("[data-f]").forEach(el=>{
  el.addEventListener(el.tagName==="SELECT"?"change":"input",()=>{r[el.dataset.f]=el.value;touch(r,tb);});
  el.addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();moveDown(r,el.dataset.f);}});
 });
 tb.querySelector("[data-toggle]").onclick=()=>{r.open=!r.open;if(r.open&&!r.extras.length)r.extras.push({type:"supply",ref:"",qty:"",unit:"un"});mountRow(r);tb=null;const s=document.querySelector('#pv-grid tbody[data-key="'+r.key+'"] [data-x="ref"]');if(s&&!s.value)s.focus();};
 tb.querySelector("[data-dup]").onclick=()=>{const n=newRow(r);n.variant="";n.open=true;rows.splice(rows.indexOf(r)+1,0,n);renderGrid();focusRow(n);updateFooter();};
 const del=tb.querySelector("[data-del]");if(del)del.onclick=()=>{rows=rows.filter(o=>o!==r);tb.remove();updateFooter();};
 const rev=tb.querySelector("[data-reviewed]");if(rev)rev.onchange=()=>{r.reviewed=rev.checked;touch(r,tb);};
 tb.querySelectorAll("[data-i]").forEach(line=>{
  const i=Number(line.dataset.i),x=r.extras[i];
  line.querySelector('[data-x="ref"]').onchange=e=>{const [t,id]=e.target.value.split(":");x.type=t||"supply";x.ref=id||"";x.unit=unidade(x.ref,x.type);r.dirty=true;r.error="";mountRow(r);updateFooter();const q=document.querySelector('#pv-grid tbody[data-key="'+r.key+'"] [data-i="'+i+'"] [data-x="qty"]');if(q)q.focus();};
  line.querySelector('[data-x="qty"]').oninput=e=>{x.qty=e.target.value;touch(r,tb);tb.querySelector("[data-toggle]").innerHTML=resumoExtras(r);};
  line.querySelector('[data-x="qty"]').onkeydown=e=>{if(e.key==="Enter"){e.preventDefault();r.extras.push({type:"supply",ref:"",qty:"",unit:"un"});r.dirty=true;mountRow(r);updateFooter();const s=document.querySelectorAll('#pv-grid tbody[data-key="'+r.key+'"] [data-x="ref"]');s[s.length-1]?.focus();}};
  line.querySelector('[data-x="unit"]').onchange=e=>{x.unit=e.target.value;touch(r,tb);tb.querySelector("[data-toggle]").innerHTML=resumoExtras(r);};
  line.querySelector("[data-xdel]").onclick=()=>{r.extras.splice(i,1);r.dirty=true;mountRow(r);updateFooter();};
 });
 const add=tb.querySelector("[data-xadd]");if(add)add.onclick=()=>{r.extras.push({type:"supply",ref:"",qty:"",unit:"un"});r.dirty=true;mountRow(r);updateFooter();const s=document.querySelectorAll('#pv-grid tbody[data-key="'+r.key+'"] [data-x="ref"]');s[s.length-1]?.focus();};
}
/* Enter desce para a mesma coluna da linha de baixo; na última, cria um sabor novo. */
function moveDown(r,f){
 let i=rows.indexOf(r)+1;
 if(i>=rows.length){addRow();return;}
 document.querySelector('#pv-grid tbody[data-key="'+rows[i].key+'"] [data-f="'+f+'"]')?.focus();
}
function focusRow(r,f){const el=document.querySelector('#pv-grid tbody[data-key="'+r.key+'"] [data-f="'+(f||"variant")+'"]');if(el){el.focus();el.select?.();}}
function addRow(){const r=newRow();r.open=false;rows.push(r);mountRow(r);focusRow(r);updateFooter();}
function renderGrid(){
 const g=document.getElementById("pv-grid");if(!g)return;
 g.querySelectorAll("tbody").forEach(t=>t.remove());
 rows.forEach(mountRow);
 document.getElementById("pv-empty").hidden=rows.length>0;
}
function updateFooter(){
 const n=pending().length,btn=document.getElementById("pv-save"),undo=document.getElementById("pv-discard");
 if(btn){btn.disabled=!n||saving||!baseOk();btn.textContent=saving?"Salvando…":n?"Salvar "+n+(n>1?" alterações":" alteração"):"Tudo salvo";}
 if(undo)undo.hidden=!n;
 const cnt=document.getElementById("pv-count");if(cnt)cnt.textContent=rows.length+(rows.length===1?" sabor":" sabores");
}
function render(){
 const host=document.getElementById("pv-root");if(!host)return;
 if(!currentId||!byId(currentId))currentId=parents()[0]?.id||"";
 const base=byId(currentId);buildRows();
 host.innerHTML=
 '<div class="pv-toolbar"><label class="pv-pick">Produto principal (base)<input id="pv-search" list="pv-parents" placeholder="Buscar produto…" value="'+esc(base?.name||"")+'" autocomplete="off"><datalist id="pv-parents">'+parents().map(p=>'<option value="'+esc(p.name)+'">').join("")+'</datalist></label>'+
 '<div class="pv-tools"><button type="button" class="pv-secondary" id="pv-paste-btn">Colar lista</button><button type="button" class="pv-secondary" id="pv-link-btn">Vincular existente</button><button type="button" class="pv-action" id="pv-add">+ Novo sabor</button></div></div>'+
 '<div class="pv-baseinfo"><span><b>'+esc(base?.name||"—")+'</b> · base em '+esc(baseUnit())+baseResumo()+' · <span id="pv-count"></span></span>'+
 (baseOk()?'':'<span class="pv-alert-inline">Cadastre primeiro os ingredientes da massa na ficha técnica deste produto.</span>')+
 (window.ControleCMV?'':'<span class="pv-muted">CMV ao vivo aparece após atualizar a página.</span>')+'</div>'+
 '<div id="pv-panel"></div>'+
 '<div class="pv-scroll"><table id="pv-grid" class="pv-grid"><thead><tr><th></th><th>Sabor</th><th>Base</th><th>Recheios</th><th>Rende</th><th>Preço R$</th><th class="pv-num">Custo/un</th><th class="pv-num">CMV</th><th></th></tr></thead></table>'+
 '<p id="pv-empty" class="pv-empty">Nenhum sabor ainda. Clique em <b>+ Novo sabor</b> ou <b>Colar lista</b>.</p></div>'+
 '<footer class="pv-foot"><p id="pv-status" role="status">Dica: <kbd>Enter</kbd> desce para a próxima linha; na última, cria um sabor novo.</p><button type="button" class="pv-secondary" id="pv-discard" hidden>Descartar</button><button type="button" class="pv-action" id="pv-save">Tudo salvo</button></footer>';
 const search=document.getElementById("pv-search");
 search.onchange=()=>{const p=parents().find(x=>norm(x.name)===norm(search.value));if(!p||p.id===currentId)return;if(pending().length&&!confirm("Há alterações não salvas nesta grade. Trocar de produto e descartar?")){search.value=base?.name||"";return;}currentId=p.id;render();};
 search.onfocus=()=>search.select();
 document.getElementById("pv-add").onclick=addRow;
 document.getElementById("pv-paste-btn").onclick=pastePanel;
 document.getElementById("pv-link-btn").onclick=linkPanel;
 document.getElementById("pv-save").onclick=saveAll;
 document.getElementById("pv-discard").onclick=()=>{if(confirm("Descartar as alterações não salvas?"))render();};
 renderGrid();updateFooter();
}

/* ---------- colar lista (Excel, WhatsApp, bloco de notas) ---------- */
function pastePanel(){
 const p=document.getElementById("pv-panel");
 if(p.dataset.mode==="paste"){p.innerHTML="";p.dataset.mode="";return;}
 p.dataset.mode="paste";
 p.innerHTML='<div class="pv-card"><b>Colar vários sabores</b><p class="pv-muted">Um por linha. Colunas separadas por tabulação (Excel) ou ponto e vírgula: <code>Sabor ; Recheio ; Quantidade ; Preço</code>. Só o sabor é obrigatório. Ex.: <code>Ninho ; Leite Ninho ; 40 ; 18,90</code></p><textarea id="pv-paste" rows="6" placeholder="Doce de leite ; Doce de leite ; 80 ; 18,00&#10;Brigadeiro ; Brigadeiro ; 70&#10;Prestígio"></textarea><div class="pv-tools"><button type="button" class="pv-secondary" id="pv-paste-cancel">Cancelar</button><button type="button" class="pv-action" id="pv-paste-ok">Adicionar à grade</button></div></div>';
 document.getElementById("pv-paste").focus();
 document.getElementById("pv-paste-cancel").onclick=pastePanel;
 document.getElementById("pv-paste-ok").onclick=()=>{
  const lines=document.getElementById("pv-paste").value.split(/\r?\n/).map(l=>l.trim()).filter(Boolean);
  let added=0;const missing=[];
  lines.forEach(l=>{
   const c=l.split(/\t|;/).map(x=>x.trim());
   if(!c[0]||/^sabor$/i.test(c[0]))return;
   const r=newRow();r.variant=c[0];r.open=false;
   let recheio=c[1]||"",qty=c[2]||"",price=c[3]||"";
   if(c.length===2&&Number.isFinite(num(c[1]))){recheio="";price=c[1];}
   if(price&&Number.isFinite(num(price)))r.price=price.replace(/r\$\s*/i,"");
   if(recheio){
    const s=supplies.find(x=>norm(x.name)===norm(recheio))||supplies.find(x=>norm(x.name).startsWith(norm(recheio)));
    const pr=!s&&products.find(x=>x.id!==currentId&&ficha(x.id)&&norm(x.name)===norm(recheio));
    if(s||pr){const type=s?"supply":"product",ref=(s||pr).id;r.extras.push({type,ref,qty:Number.isFinite(num(qty))?num(qty):"",unit:unidade(ref,type)});}
    else{missing.push(recheio);r.error="Recheio “"+recheio+"” não encontrado: escolha na lista.";r.open=true;r.extras.push({type:"supply",ref:"",qty:Number.isFinite(num(qty))?num(qty):"",unit:"un"});}
   }
   rows.push(r);added++;
  });
  pastePanel();renderGrid();updateFooter();
  msg(added+" sabor(es) adicionado(s) à grade. Confira e clique em Salvar."+(missing.length?" Recheios não encontrados: "+missing.join(", ")+".":""),missing.length>0);
 };
}

/* ---------- vincular produto já cadastrado ---------- */
function linkPanel(){
 const p=document.getElementById("pv-panel");
 if(p.dataset.mode==="link"){p.innerHTML="";p.dataset.mode="";return;}
 p.dataset.mode="link";
 const available=parents().filter(x=>x.id!==currentId);
 p.innerHTML='<form class="pv-card pv-linkform"><b>Vincular produto já cadastrado</b><p class="pv-muted">Preserva a ficha técnica e o histórico do produto.</p><div class="pv-two"><label>Produto<select name="product" required>'+available.map(x=>'<option value="'+esc(x.id)+'">'+esc(x.name)+'</option>').join("")+'</select></label><label>Nome do sabor<input name="variant" required placeholder="Ex.: Frango"></label></div><div class="pv-tools"><button type="button" class="pv-secondary" data-cancel>Cancelar</button><button class="pv-action" type="submit">Vincular</button></div></form>';
 p.querySelector("[data-cancel]").onclick=linkPanel;
 p.querySelector("form").onsubmit=async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);
  if(pending().length&&!confirm("Vincular recarrega a grade e descarta as alterações não salvas. Continuar?"))return;
  try{if(evitarCircular(currentId,String(fd.get("product"))))throw Error("Este vínculo criaria uma receita circular.");const {error}=await client().from("products").update({parent_product_id:currentId,variant_name:String(fd.get("variant")).trim()}).eq("id",fd.get("product"));if(error)throw error;await load();render();window.ControleProduRecarregar?.();msg("Produto vinculado sem apagar sua ficha e seu histórico.");}catch(err){msg(err.message,true)}};
}

/* ---------- salvar ---------- */
async function saveRow(r){
 const base=byId(currentId),bUnit=baseUnit(),v=r.id?byId(r.id):null;
 const variant=r.variant.trim(),price=num(r.price),qtyBase=num(r.baseQty),yieldQty=num(r.yieldQty);
 const old=v?ingredientes(v.id):[],baseItem=v?old.find(i=>String(i.component_product_id)===String(currentId)):null;
 const prodPayload={variant_name:variant,price,parent_product_id:currentId};
 let id=v?.id;
 if(v){const {error}=await client().from("products").update(prodPayload).eq("id",v.id);if(error)throw error;}
 else{
  const name=base.name+" - "+variant;
  if(products.some(p=>norm(p.name)===norm(name)))throw Error("“"+name+"” já existe. Use Vincular existente.");
  Object.assign(prodPayload,{name,category:base.category,default_unit:base.default_unit||"un",
   price_unit:base.price_unit||base.default_unit||"un",shelf_life_days:base.shelf_life_days||1,
   min_replenishment_qty:base.min_replenishment_qty||0,responsible:base.responsible||"",is_active:base.is_active!==false,
   variant_sort_order:rows.indexOf(r)+1});
  const {data,error}=await client().from("products").insert(prodPayload).select("id").single();
  if(error)throw error;id=data.id;r.id=id;
 }
 let row=ficha(id);
 const rPayload={yield_qty:yieldQty,yield_unit:r.yieldUnit||"un",inherit_parent_recipe:false};
 if(row){const {error}=await client().from("recipes").update(rPayload).eq("id",row.id);if(error)throw error;}
 else{const {data,error}=await client().from("recipes").insert({...rPayload,product_id:id}).select("id").single();if(error)throw error;row=data;}
 const basePayload={recipe_id:row.id,component_product_id:currentId,supply_id:null,qty:qtyBase,usage_unit:bUnit};
 if(baseItem){const {error}=await client().from("recipe_items").update(basePayload).eq("id",baseItem.id);if(error)throw error;}
 else{const {error}=await client().from("recipe_items").insert(basePayload);if(error)throw error;}
 for(const x of r.extras){
  const payload={recipe_id:row.id,supply_id:x.type==="supply"?x.ref:null,component_product_id:x.type==="product"?x.ref:null,qty:num(x.qty),usage_unit:x.unit||unidade(x.ref,x.type)};
  const q=x.id?client().from("recipe_items").update(payload).eq("id",x.id).eq("recipe_id",row.id):client().from("recipe_items").insert(payload);
  const {error}=await q;if(error)throw error;
 }
 const remain=new Set(r.extras.map(x=>x.id).filter(Boolean));
 for(const o of old){
  if(o.id===baseItem?.id||remain.has(o.id))continue;
  const {error}=await client().from("recipe_items").delete().eq("id",o.id).eq("recipe_id",row.id);if(error)throw error;
 }
}
async function saveAll(){
 if(saving)return;
 if(!baseOk())return msg("A receita base ainda não tem ingredientes.",true);
 const todo=pending();let bad=0;
 todo.forEach(r=>{r.error=validate(r);if(r.error){bad++;r.open=r.open||r.extras.length>0||!r.id;}});
 if(bad){renderGrid();updateFooter();return msg(bad+" linha(s) com problema, marcadas com “!”. Passe o mouse ou abra os recheios para ver o motivo.",true);}
 saving=true;updateFooter();
 let ok=0;const failed=[];
 for(const r of todo){
  msg("Salvando "+(ok+failed.length+1)+" de "+todo.length+"…");
  try{await saveRow(r);r.dirty=false;ok++;}catch(err){r.error=err.message;failed.push(r);}
 }
 try{await load();}catch(err){msg("Salvo, mas não foi possível recarregar: "+err.message,true);}
 saving=false;
 buildRows();
 failed.forEach(f=>{const i=rows.findIndex(r=>r.id&&r.id===f.id);f.open=true;if(i>=0)rows[i]=f;else rows.push(f);});
 renderGrid();updateFooter();
 window.ControleProduRecarregar?.();
 if(failed.length)msg(ok+" salvo(s); "+failed.length+" com erro: "+failed.map(f=>(f.variant||"sem nome")+" ("+f.error+")").join("; "),true);
 else msg("✓ "+ok+(ok>1?" sabores salvos":" sabor salvo")+". A massa continua compartilhada e o CMV já considera base + recheio.");
}

/* ---------- janela ---------- */
function close(){
 if(pending().length&&!confirm("Há alterações não salvas. Fechar mesmo assim?"))return;
 document.getElementById("pv-modal")?.remove();document.removeEventListener("keydown",onKey);
}
function onKey(e){if(e.key==="Escape"&&!e.target.closest?.("#pv-panel"))close();}
async function open(productId){
 document.getElementById("pv-modal")?.remove();rows=[];
 const root=document.createElement("div");root.id="pv-modal";root.innerHTML='<div class="pv-shade" data-close></div><section class="pv-dialog" role="dialog" aria-modal="true" aria-label="Receitas e sabores"><header><div><small>DELÍCIAS DA VOVÓ · BANCO DE DADOS</small><h2>Receitas e sabores</h2></div><button type="button" data-close aria-label="Fechar">×</button></header><div id="pv-root">Carregando produtos…</div></section>';
 document.body.appendChild(root);root.querySelectorAll("[data-close]").forEach(b=>b.onclick=close);
 document.addEventListener("keydown",onKey);
 try{await load();
  // Aberta a partir de um produto: mostra a grade da base dele.
  const alvo=typeof productId==="string"&&byId(productId);if(alvo)currentId=alvo.parent_product_id||alvo.id;
  render()}catch(err){root.querySelector("#pv-root").textContent="Não foi possível acessar o cadastro: "+err.message;}
}
window.abrirVariacoesProdutos=open;
function attachBanco(){
 document.querySelectorAll("h1,h2,h3").forEach(h=>{
  if(h.textContent?.trim()!=="Banco de Dados"||h.parentElement?.querySelector("[data-receitas-sabores]"))return;
  const b=document.createElement("button");
  b.dataset.receitasSabores="true";b.type="button";b.className="pv-inline-entry";b.textContent="Receitas e sabores";
  b.onclick=()=>open();h.parentElement.appendChild(b);
 });
}
document.addEventListener("DOMContentLoaded",()=>{
 attachBanco();
 let queued=false;
 new MutationObserver(()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;attachBanco();});})
  .observe(document.getElementById("root")||document.body,{childList:true,subtree:true});
});
})();
