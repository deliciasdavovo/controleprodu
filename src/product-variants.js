(function(){
"use strict";
const endpoint="https://rnycjwlmzpackuodflki.supabase.co", key="sb_publishable_W9Z02Rr3nlUqS1ec5_OCiw_Ezoc_iWk";
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let sb, products=[], currentId="", selectedId="";
function client(){if(!window.supabase)throw Error("Biblioteca Supabase indisponível");return sb||(sb=window.supabase.createClient(endpoint,key,{auth:{persistSession:true,storageKey:"sb-"+new URL(endpoint).hostname.split(".")[0]+"-auth-token"}}));}
async function load(){
 const all=[];for(let start=0;start<10000;start+=1000){const {data,error}=await client().from("products").select("*").order("name").range(start,start+999);if(error)throw error;all.push(...data);if(!data||data.length<1000)break;}products=all;
}
function byId(id){return products.find(p=>p.id===id);}
function parents(){return products.filter(p=>!p.parent_product_id);}
function children(id){return products.filter(p=>p.parent_product_id===id).sort((a,b)=>(a.variant_sort_order||0)-(b.variant_sort_order||0)||a.name.localeCompare(b.name,"pt-BR"));}
function msg(t,error){const el=document.getElementById("pv-status");if(el){el.textContent=t;el.style.color=error?"#9b2530":"#31513d";}}
function render(){
 const host=document.getElementById("pv-root");if(!host)return;
 if(!currentId||!byId(currentId))currentId=parents()[0]?.id||"";
 const base=byId(currentId), variants=children(currentId);
 host.innerHTML='<div class="pv-toolbar"><label>Produto principal<select id="pv-parent">'+parents().map(p=>'<option value="'+esc(p.id)+'" '+(p.id===currentId?'selected':'')+'>'+esc(p.name)+'</option>').join("")+'</select></label><label>Buscar produto<input id="pv-search" placeholder="Nome do produto" /></label></div><div class="pv-layout"><div class="pv-list"><b>'+esc(base?.name||"Produtos")+'</b><small>'+variants.length+' variação(ões)</small><div class="pv-rows">'+variants.map(v=>'<button class="pv-row" data-edit="'+esc(v.id)+'"><span>'+esc(v.variant_name)+'</span><small>'+esc(v.name)+'</small></button>').join("")+'</div><button id="pv-add" class="pv-action">+ Nova variação</button><button id="pv-link" class="pv-secondary">Vincular produto já cadastrado</button></div><div id="pv-editor" class="pv-edit"><p>Selecione uma variação ou crie uma nova. Cada uma terá receita, preço e custo independentes.</p></div></div><p id="pv-status" role="status"></p>';
 document.getElementById("pv-parent").onchange=e=>{currentId=e.target.value;selectedId="";render();};
 document.getElementById("pv-search").oninput=e=>{const q=e.target.value.toLocaleLowerCase("pt-BR");[...e.target.closest(".pv-toolbar").querySelector("#pv-parent").options].forEach(o=>o.hidden=!o.text.toLocaleLowerCase("pt-BR").includes(q));};
 document.getElementById("pv-add").onclick=()=>editor(null);
 document.getElementById("pv-link").onclick=link;
 host.querySelectorAll("[data-edit]").forEach(b=>b.onclick=()=>editor(byId(b.dataset.edit)));
 if(selectedId&&byId(selectedId)?.parent_product_id===currentId)editor(byId(selectedId));
}
function editor(v){
 selectedId=v?.id||"";const base=byId(currentId), host=document.getElementById("pv-editor");
 host.innerHTML='<h3>'+(v?"Editar variação":"Nova variação")+'</h3><form id="pv-form"><label>Nome da variação<input name="variant" required maxlength="100" value="'+esc(v?.variant_name||"")+'" placeholder="Ex.: Ovomaltine"></label><label>Nome completo no cadastro<input name="name" required maxlength="200" value="'+esc(v?.name||base?.name+" - ")+'"></label><div class="pv-two"><label>Preço de venda (R$)<input name="price" type="number" step="0.01" min="0" value="'+esc(v?.price??base?.price??0)+'"></label><label>Ordem<input name="sort" type="number" min="0" step="1" value="'+esc(v?.variant_sort_order??children(currentId).length+1)+'"></label></div><label class="pv-check"><input name="inherit" type="checkbox" '+(v?"":"checked")+'> Usar ingredientes da receita principal como base (no Livro de Receitas)</label><button class="pv-action" type="submit">Salvar variação</button></form><p class="pv-info">Ingredientes específicos e modo de preparo podem ser editados na ficha técnica deste produto. Os ingredientes herdados não são copiados e não entram duas vezes no CMV.</p>';
 host.querySelector("#pv-form").onsubmit=async e=>{e.preventDefault();const form=e.currentTarget, fd=new FormData(form), variant=String(fd.get("variant")||"").trim(),name=String(fd.get("name")||"").trim(),price=Number(fd.get("price")),sort=Number(fd.get("sort"));if(!variant||!name||!Number.isFinite(price)||price<0)return msg("Confira os campos.",true);
 try{msg("Salvando…");const payload={name,variant_name:variant,variant_sort_order:sort,price,parent_product_id:currentId};
 let id=v?.id;
 if(v){const {error}=await client().from("products").update(payload).eq("id",v.id);if(error)throw error;}
 else{Object.assign(payload,{category:base.category,default_unit:base.default_unit,price_unit:base.price_unit||base.default_unit,shelf_life_days:base.shelf_life_days,min_replenishment_qty:base.min_replenishment_qty,responsible:base.responsible||"",is_active:base.is_active});const {data,error}=await client().from("products").insert(payload).select("id").single();if(error)throw error;id=data.id;}
 const {data:recipe,error:lookupError}=await client().from("recipes").select("id,inherit_parent_recipe").eq("product_id",id).maybeSingle();if(lookupError)throw lookupError;
 if(recipe){if(recipe.inherit_parent_recipe!==fd.has("inherit")){const {error}=await client().from("recipes").update({inherit_parent_recipe:fd.has("inherit")}).eq("id",recipe.id);if(error)throw error;}}
 else if(fd.has("inherit")){const {error}=await client().from("recipes").insert({product_id:id,inherit_parent_recipe:true,yield_qty:1,yield_unit:base.default_unit||"un"});if(error)throw error;}
 await load();selectedId=id;render();msg("Variação salva no Supabase. Abra a ficha técnica para adicionar ingredientes específicos.");}
 catch(err){msg("Erro ao salvar: "+err.message,true);}
 };
}
function link(){
 const available=parents().filter(p=>p.id!==currentId); const host=document.getElementById("pv-editor");
 host.innerHTML='<h3>Vincular produto existente</h3><p>Preserva a ficha técnica e o histórico do produto selecionado.</p><form id="pv-link-form"><label>Produto já cadastrado<select name="product" required>'+available.map(p=>'<option value="'+esc(p.id)+'">'+esc(p.name)+'</option>').join("")+'</select></label><label>Nome da variação<input name="variant" required placeholder="Ex.: Frango"></label><button class="pv-action" type="submit">Vincular</button></form>';
 host.querySelector("form").onsubmit=async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);try{const {error}=await client().from("products").update({parent_product_id:currentId,variant_name:String(fd.get("variant")).trim()}).eq("id",fd.get("product"));if(error)throw error;await load();selectedId=String(fd.get("product"));render();msg("Produto vinculado sem apagar sua ficha e seu histórico.");}catch(err){msg(err.message,true)}};
}
async function open(){
 document.getElementById("pv-modal")?.remove();
 const root=document.createElement("div");root.id="pv-modal";root.innerHTML='<div class="pv-shade" data-close></div><section class="pv-dialog" role="dialog" aria-modal="true" aria-label="Variações de produtos"><header><div><small>DELÍCIAS DA VOVÓ · BANCO DE DADOS</small><h2>Variações de produtos</h2></div><button type="button" data-close aria-label="Fechar">×</button></header><div id="pv-root">Carregando produtos…</div></section>';
 document.body.appendChild(root);root.querySelectorAll("[data-close]").forEach(b=>b.onclick=()=>root.remove());
 try{await load();render()}catch(err){root.querySelector("#pv-root").textContent="Não foi possível acessar o cadastro: "+err.message;}
}
window.abrirVariacoesProdutos=open;
const btn=document.createElement("button");btn.id="pv-floating";btn.type="button";btn.textContent="◈ Variações";btn.title="Gerenciar sabores e recheios dos produtos";btn.onclick=open;
document.addEventListener("DOMContentLoaded",()=>document.body.appendChild(btn));
})();