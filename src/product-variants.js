(function(){
"use strict";
const endpoint="https://rnycjwlmzpackuodflki.supabase.co", key="sb_publishable_W9Z02Rr3nlUqS1ec5_OCiw_Ezoc_iWk";
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let sb, products=[], recipes=[], recipeItems=[], supplies=[], currentId="", selectedId="", extrasDraft=[], saving=false;
function client(){if(!window.supabase)throw Error("Biblioteca Supabase indisponível");return sb||(sb=window.supabase.createClient(endpoint,key,{auth:{persistSession:true,storageKey:"sb-"+new URL(endpoint).hostname.split(".")[0]+"-auth-token"}}));}
async function load(){
 const all=[];for(let start=0;start<10000;start+=1000){const {data,error}=await client().from("products").select("*").order("name").range(start,start+999);if(error)throw error;all.push(...data);if(!data||data.length<1000)break;}products=all;
 const fetchTable=async(table)=>{const rows=[];for(let start=0;start<10000;start+=1000){const {data,error}=await client().from(table).select("*").range(start,start+999);if(error)throw error;rows.push(...(data||[]));if(!data||data.length<1000)break;}return rows;};
 [recipes,recipeItems,supplies]=await Promise.all(["recipes","recipe_items","supplies"].map(fetchTable));
 supplies.sort((a,b)=>a.name.localeCompare(b.name,"pt-BR"));
}
function byId(id){return products.find(p=>p.id===id);}
function parents(){return products.filter(p=>!p.parent_product_id);}
function children(id){return products.filter(p=>p.parent_product_id===id).sort((a,b)=>(a.variant_sort_order||0)-(b.variant_sort_order||0)||a.name.localeCompare(b.name,"pt-BR"));}

function ficha(id){return recipes.find(r=>String(r.product_id)===String(id));}
function ingredientes(id){const r=ficha(id);return r?recipeItems.filter(i=>String(i.recipe_id)===String(r.id)):[];}
function unidade(id,tipo){return tipo==="supply"?(supplies.find(i=>String(i.id)===String(id))?.unit||"un"):(ficha(id)?.yield_unit||"un");}
function opcoesComponentes(){
 return '<option value="">Selecionar recheio ou preparo</option>'+
 '<optgroup label="Insumos">'+supplies.map(i=>'<option value="supply:'+esc(i.id)+'">'+esc(i.name)+'</option>').join("")+'</optgroup>'+
 '<optgroup label="Preparos da padaria">'+products.filter(i=>i.id!==currentId&&!!ficha(i.id)).map(i=>'<option value="product:'+esc(i.id)+'">'+esc(i.name)+'</option>').join("")+'</optgroup>';
}
function variantesComBase(id){return ingredientes(id).find(i=>String(i.component_product_id)===String(currentId));}
function renderComponentes(){
 const el=document.getElementById("pv-complementos");if(!el)return;
 el.innerHTML=extrasDraft.map((x,i)=>{
   const ref=x.ref?x.type+":"+x.ref:"";
   const u=x.ref?unidade(x.ref,x.type):"un";
   const units=[u];
   if(u==="g")units.push("kg");else if(u==="kg")units.push("g");
   else if(u==="ml")units.push("L");else if(u==="L")units.push("ml");
   return '<div class="pv-ingredient" data-index="'+i+'"><label>Recheio / complemento<select data-field="ref">'+
     opcoesComponentes().replace('value="'+esc(ref)+'"','value="'+esc(ref)+'" selected')+
     '</select></label><label>Quantidade<input data-field="qty" type="number" step="any" min="0.001" value="'+esc(x.qty??"")+'"></label>'+
     '<label>Unidade<select data-field="unit">'+units.map(u0=>'<option '+(u0===x.unit?'selected':'')+' value="'+esc(u0)+'">'+esc(u0)+'</option>').join("")+
     '</select></label><button type="button" data-remove="'+i+'" aria-label="Remover ingrediente">×</button></div>';
 }).join("");
 el.querySelectorAll("[data-index]").forEach(row=>{
  const i=Number(row.dataset.index);
  row.querySelector('[data-field="ref"]').onchange=e=>{const parts=e.target.value.split(":");extrasDraft[i].type=parts[0]||"supply";extrasDraft[i].ref=parts[1]||"";extrasDraft[i].unit=unidade(parts[1],parts[0]);renderComponentes();};
  row.querySelector('[data-field="qty"]').oninput=e=>{extrasDraft[i].qty=e.target.value;};
  row.querySelector('[data-field="unit"]').onchange=e=>{extrasDraft[i].unit=e.target.value;};
  row.querySelector("[data-remove]").onclick=()=>{extrasDraft.splice(i,1);renderComponentes();};
 });
}
function evitarCircular(componente,produto,visitados=new Set()){
 if(componente===produto)return true;
 if(visitados.has(componente))return false;visitados.add(componente);
 return ingredientes(componente).some(i=>i.component_product_id&&evitarCircular(i.component_product_id,produto,visitados));
}

function msg(t,error){const el=document.getElementById("pv-status");if(el){el.textContent=t;el.style.color=error?"#9b2530":"#31513d";}}
function render(){
 const host=document.getElementById("pv-root");if(!host)return;
 if(!currentId||!byId(currentId))currentId=parents()[0]?.id||"";
 const base=byId(currentId), variants=children(currentId);
 host.innerHTML='<div class="pv-toolbar"><label>Produto principal<select id="pv-parent">'+parents().map(p=>'<option value="'+esc(p.id)+'" '+(p.id===currentId?'selected':'')+'>'+esc(p.name)+'</option>').join("")+'</select></label><label>Buscar produto<input id="pv-search" placeholder="Nome do produto" /></label></div><div class="pv-layout"><div class="pv-list"><b>'+esc(base?.name||"Produtos")+'</b><small>'+variants.length+' variação(ões)</small><div class="pv-rows">'+variants.map(v=>'<button class="pv-row" data-edit="'+esc(v.id)+'"><span>'+esc(v.variant_name)+'</span><small>'+esc(v.name)+'</small></button>').join("")+'</div><button id="pv-add" class="pv-action">+ Nova variação</button><button id="pv-link" class="pv-secondary">Vincular produto já cadastrado</button></div><div id="pv-editor" class="pv-edit"><p>Cadastre a massa uma vez na ficha do produto principal. Para cada sabor, escolha apenas o recheio e a quantidade usada. O custo da base é reaproveitado automaticamente.</p></div></div><p id="pv-status" role="status"></p>';
 document.getElementById("pv-parent").onchange=e=>{currentId=e.target.value;selectedId="";render();};
 document.getElementById("pv-search").oninput=e=>{const q=e.target.value.toLocaleLowerCase("pt-BR");[...e.target.closest(".pv-toolbar").querySelector("#pv-parent").options].forEach(o=>o.hidden=!o.text.toLocaleLowerCase("pt-BR").includes(q));};
 document.getElementById("pv-add").onclick=()=>editor(null);
 document.getElementById("pv-link").onclick=link;
 host.querySelectorAll("[data-edit]").forEach(b=>b.onclick=()=>editor(byId(b.dataset.edit)));
 if(selectedId&&byId(selectedId)?.parent_product_id===currentId)editor(byId(selectedId));
}
function editor(v){
 selectedId=v?.id||"";const base=byId(currentId),host=document.getElementById("pv-editor");
 const baseFicha=ficha(currentId),existing=ficha(v?.id),old=ingredientes(v?.id),baseItem=v?variantesComBase(v.id):null;
 const herancaAntiga=!!v&&old.length>0&&!baseItem;
 extrasDraft=old.filter(i=>i.id!==baseItem?.id).map(i=>({id:i.id,type:i.supply_id?"supply":"product",
   ref:i.supply_id||i.component_product_id,qty:i.qty,unit:i.usage_unit||unidade(i.supply_id||i.component_product_id,i.supply_id?"supply":"product")}));
 const baseUnit=baseFicha?.yield_unit||"un";
 const flavor=v?.variant_name||"";
 const needsReview=herancaAntiga;
 host.innerHTML='<h3>'+(v?'Editar sabor':'Novo sabor')+'</h3>'+
 '<p class="pv-info">A receita da massa continua apenas na ficha de <b>'+esc(base?.name)+'</b>. Aqui você informa a quantidade dessa base usada no produto e os recheios que mudam.</p>'+
 (!baseFicha||!ingredientes(currentId).length?'<p class="pv-alert">Cadastre primeiro os ingredientes da receita base na ficha técnica do produto principal.</p>':'')+
 (needsReview?'<div class="pv-alert"><strong>Ficha antiga independente</strong><p>Este produto já tem ingredientes cadastrados. Remova abaixo os itens da massa antes de vincular a receita base para evitar custo em dobro.</p><label class="pv-check"><input id="pv-review" type="checkbox"> Conferi os ingredientes e retirei a massa duplicada</label></div>':'')+
 '<form id="pv-form"><label>Sabor ou recheio<input name="variant" required maxlength="100" value="'+esc(flavor)+'" placeholder="Ex.: Doce de leite"></label>'+
 '<div class="pv-two"><label>Quantidade da base usada<input name="baseQty" type="number" required min="0.001" step="any" value="'+esc(baseItem?.qty??(baseUnit==="un"?1:""))+'"></label>'+
 '<label>Unidade da base<input readonly value="'+esc(baseUnit)+'"></label></div>'+
 '<div class="pv-two"><label>Rendimento da ficha final<input name="yield" type="number" required min="0.001" step="any" value="'+esc(existing?.yield_qty||1)+'"></label>'+
 '<label>Unidade produzida<select name="yieldUnit">'+["un","kg","g","ml","L"].map(u=>'<option value="'+u+'" '+(u===(existing?.yield_unit||"un")?'selected':'')+'>'+u+'</option>').join("")+'</select></label></div>'+
 '<div class="pv-ingredient-head"><b>O que muda neste sabor?</b><button type="button" class="pv-secondary" id="pv-add-ingredient">+ Ingrediente</button></div>'+
 '<div id="pv-complementos"></div><label>Preço de venda (R$)<input name="price" type="number" step="0.01" min="0" value="'+esc(v?.price??base?.price??0)+'"></label>'+
 '<button class="pv-action" type="submit">Salvar produto e ficha</button></form>'+
 '<p class="pv-info">A ficha final usa a base como componente de fabricação própria. Isso atualiza o CMV sem copiar os ingredientes da massa.</p>';
 host.querySelector("#pv-add-ingredient").onclick=()=>{extrasDraft.push({type:"supply",ref:"",qty:"",unit:"un"});renderComponentes();};
 renderComponentes();
 host.querySelector("form").onsubmit=async e=>{
   e.preventDefault();if(saving)return;
   const fd=new FormData(e.currentTarget),variant=String(fd.get("variant")||"").trim();
   const qtyBase=Number(fd.get("baseQty")),yieldQty=Number(fd.get("yield")),price=Number(fd.get("price"));
   if(!baseFicha||!ingredientes(currentId).length)return msg("A receita base ainda não tem ingredientes.",true);
   if(needsReview&&!host.querySelector("#pv-review")?.checked)return msg("Revise a ficha antiga antes de vincular a base.",true);
   if(!variant||!(qtyBase>0)||!(yieldQty>0)||!Number.isFinite(price)||price<0)return msg("Confira sabor, quantidade, rendimento e preço.",true);
   if(!v&&!extrasDraft.length)return msg("Escolha ao menos um recheio ou complemento.",true);
   const refs=new Set();
   for(const ingredient of extrasDraft){
     const k=ingredient.type+":"+ingredient.ref;
     if(!ingredient.ref||!(Number(ingredient.qty)>0))return msg("Escolha todos os complementos e suas quantidades.",true);
     if(refs.has(k))return msg("O mesmo ingrediente foi adicionado duas vezes.",true);
     refs.add(k);
     if(ingredient.type==="product"&&(ingredient.ref===currentId||evitarCircular(ingredient.ref,v?.id||currentId)))return msg("Este componente criaria uma receita circular ou duplicaria a base.",true);
     const valid=ingredient.type==="supply"?supplies.some(s=>s.id===ingredient.ref):products.some(p=>p.id===ingredient.ref);
     if(!valid)return msg("Ingrediente não encontrado. Reabra a tela.",true);
   }
   saving=true;const saveButton=host.querySelector("[type=submit]");saveButton.disabled=true;msg("Salvando receita compartilhada…");
   try{
     const prodPayload={variant_name:variant,price,parent_product_id:currentId};
     let id=v?.id;
     if(v){
       const {error}=await client().from("products").update(prodPayload).eq("id",v.id);if(error)throw error;
     }else{
       const name=base.name+" - "+variant;
       if(products.some(p=>p.name.toLocaleLowerCase("pt-BR")===name.toLocaleLowerCase("pt-BR")))throw Error("Produto já cadastrado. Use Vincular produto existente.");
       Object.assign(prodPayload,{name,category:base.category,default_unit:base.default_unit||"un",
        price_unit:base.price_unit||base.default_unit||"un",shelf_life_days:base.shelf_life_days||1,
        min_replenishment_qty:base.min_replenishment_qty||0,responsible:base.responsible||"",is_active:base.is_active!==false,
        variant_sort_order:children(currentId).length+1});
       const {data,error}=await client().from("products").insert(prodPayload).select("id").single();
       if(error)throw error;id=data.id;
     }
     let row=ficha(id);
     const rPayload={yield_qty:yieldQty,yield_unit:fd.get("yieldUnit")||"un",inherit_parent_recipe:false};
     if(row){
       const {error}=await client().from("recipes").update(rPayload).eq("id",row.id);if(error)throw error;
     }else{
       const {data,error}=await client().from("recipes").insert({...rPayload,product_id:id}).select("id").single();
       if(error)throw error;row=data;
     }
     const basePayload={recipe_id:row.id,component_product_id:currentId,supply_id:null,qty:qtyBase,usage_unit:baseUnit};
     if(baseItem){
       const {error}=await client().from("recipe_items").update(basePayload).eq("id",baseItem.id);if(error)throw error;
     }else{
       const {error}=await client().from("recipe_items").insert(basePayload);if(error)throw error;
     }
     for(const ingredient of extrasDraft){
       const payload={recipe_id:row.id,supply_id:ingredient.type==="supply"?ingredient.ref:null,
         component_product_id:ingredient.type==="product"?ingredient.ref:null,
         qty:Number(ingredient.qty),usage_unit:ingredient.unit||unidade(ingredient.ref,ingredient.type)};
       const query=ingredient.id?client().from("recipe_items").update(payload).eq("id",ingredient.id).eq("recipe_id",row.id)
         :client().from("recipe_items").insert(payload);
       const {error}=await query;if(error)throw error;
     }
     const remain=new Set(extrasDraft.map(x=>x.id).filter(Boolean));
     for(const oldItem of old){
       if(oldItem.id===baseItem?.id||remain.has(oldItem.id))continue;
       const {error}=await client().from("recipe_items").delete().eq("id",oldItem.id).eq("recipe_id",row.id);if(error)throw error;
     }
     await load();selectedId=id;render();
     msg("Salvo! A massa é compartilhada, o recheio é específico e o CMV usa as duas partes. Atualize a tela principal para ver o produto.");
   }catch(err){msg("Não foi possível concluir: "+err.message+". Confira o cadastro antes de repetir.",true);}
   finally{saving=false;const btn=document.querySelector("#pv-form [type=submit]");if(btn)btn.disabled=false;}
 };
}
function link(){
 const available=parents().filter(p=>p.id!==currentId); const host=document.getElementById("pv-editor");
 host.innerHTML='<h3>Vincular produto existente</h3><p>Preserva a ficha técnica e o histórico do produto selecionado.</p><form id="pv-link-form"><label>Produto já cadastrado<select name="product" required>'+available.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.name)+'</option>').join("")+'</select></label><label>Nome da variação<input name="variant" required placeholder="Ex.: Frango"></label><button class="pv-action" type="submit">Vincular</button></form>';
 host.querySelector("form").onsubmit=async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);try{const {error}=await client().from("products").update({parent_product_id:currentId,variant_name:String(fd.get("variant")).trim()}).eq("id",fd.get("product"));if(error)throw error;await load();selectedId=String(fd.get("product"));render();msg("Produto vinculado sem apagar sua ficha e seu histórico.");}catch(err){msg(err.message,true)}};
}
async function open(){
 document.getElementById("pv-modal")?.remove();
 const root=document.createElement("div");root.id="pv-modal";root.innerHTML='<div class="pv-shade" data-close></div><section class="pv-dialog" role="dialog" aria-modal="true" aria-label="Receitas e sabores"><header><div><small>DELÍCIAS DA VOVÓ · BANCO DE DADOS</small><h2>Receitas e sabores</h2></div><button type="button" data-close aria-label="Fechar">×</button></header><div id="pv-root">Carregando produtos…</div></section>';
 document.body.appendChild(root);root.querySelectorAll("[data-close]").forEach(b=>b.onclick=()=>root.remove());
 try{await load();render()}catch(err){root.querySelector("#pv-root").textContent="Não foi possível acessar o cadastro: "+err.message;}
}
window.abrirVariacoesProdutos=open;
function attachBanco(){
 document.querySelectorAll("h1,h2,h3").forEach(h=>{
  if(h.textContent?.trim()!=="Banco de Dados"||h.parentElement?.querySelector("[data-receitas-sabores]"))return;
  const b=document.createElement("button");
  b.dataset.receitasSabores="true";b.type="button";b.className="pv-inline-entry";b.textContent="Receitas e sabores";
  b.onclick=open;h.parentElement.appendChild(b);
 });
}
document.addEventListener("DOMContentLoaded",()=>{
 attachBanco();
 let queued=false;
 new MutationObserver(()=>{if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;attachBanco();});})
  .observe(document.getElementById("root")||document.body,{childList:true,subtree:true});
});
})();