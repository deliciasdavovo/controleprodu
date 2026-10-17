/* Busca e agrupamento para a versão compilada do Controle Produ. */
(function(){
  const norm=v=>String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  const categorias={doce:'Doces',salgado:'Salgados',sobremesa:'Sobremesas',cafeteria:'Cafeteria',pao:'Pães',bomboniere:'Bomboniere',bebida_revenda:'Bebidas',outro:'Outros'};
  let timer;
  function install(){
    document.querySelectorAll('div.t-overline').forEach(title=>{
      if(norm(title.textContent)!=='fichas tecnicas')return;
      const card=title.closest('.card');
      if(!card || card.querySelector('[data-ficha-busca]'))return;
      const table=card.querySelector('table');
      if(!table)return;
      const group=document.createElement('div');
      group.dataset.fichaBusca='true';
      group.style.cssText='display:flex;flex-wrap:wrap;align-items:center;gap:12px;margin:0 0 16px';
      const input=document.createElement('input');input.type='search';input.placeholder='Buscar produto pelo nome…';input.setAttribute('aria-label','Buscar produto na ficha técnica');input.className='field field-sm';input.style.cssText='flex:1;min-width:200px';
      const label=document.createElement('label');label.style.cssText='display:flex;align-items:center;gap:7px;font-size:12px;cursor:pointer';
      const chk=document.createElement('input');chk.type='checkbox';label.append(chk,document.createTextNode('Agrupar por categoria'));
      const count=document.createElement('span');count.style.cssText='font-size:11px;color:#63756a';
      group.append(input,label,count);table.parentNode.before(group);
      let lastSnapshot='';
      const render=()=>{
        const body=table.tBodies[0];if(!body)return;
        const rows=[...body.rows].filter(row=>row.querySelector('select')&&row.cells.length>=8);
        const selected=card.querySelector('select')?.value||'todos';
        rows.forEach(row=>{
          const name=norm(row.cells[0]?.textContent);
          const cat=row.cells[1]?.querySelector('select')?.value||'outro';
          row.hidden=!!input.value&&!name.includes(norm(input.value));
          if(selected!=='todos'&&cat!==selected)row.hidden=true;
        });
        if(chk.checked)rows.sort((a,b)=>{
          const ca=Object.keys(categorias).indexOf(a.cells[1]?.querySelector('select')?.value||'outro');
          const cb=Object.keys(categorias).indexOf(b.cells[1]?.querySelector('select')?.value||'outro');
          return ca-cb||a.cells[0].textContent.localeCompare(b.cells[0].textContent,'pt-BR');
        }).forEach((row,index)=>{if(body.rows[index]!==row)body.insertBefore(row,body.rows[index]||null)});
        count.textContent=rows.filter(r=>!r.hidden).length+' produtos';
      };
      input.addEventListener('input',render);chk.addEventListener('change',render);
      card.addEventListener('change',e=>{if(e.target.tagName==='SELECT')setTimeout(render,10)});
      new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(render,30)}).observe(table.tBodies[0],{childList:true});
      render();
    });
  }
  new MutationObserver(()=>requestAnimationFrame(install)).observe(document.documentElement,{childList:true,subtree:true});
  install();
})();
