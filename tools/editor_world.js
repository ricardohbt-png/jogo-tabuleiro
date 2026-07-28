// Editor visual de cidades e entradas de masmorra no mapa-múndi.
(function () {
  let config = null, loading = null, selected = null, dragging = null;
  const $ = (sel, root) => (root || document).querySelector(sel);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function fallbackConfig() {
    const catalog = window.EDITOR_DUNGEONS || [];
    return { map_image:'assets/city/varluzia - Copia.png', locations:[
      {id:'alva_e_luz', nome:'Alva e Luz', x:47.5, y:51.2}, {id:'vila_riacho', nome:'Vila do Riacho', x:45, y:42.5},
      {id:'vila_corvin', nome:'Vila de Corvin', x:55.8, y:30.8}, {id:'graciero', nome:'Graciero', x:40.3, y:31}
    ], adventures:[], dungeons:catalog.map(d => ({file:d.file, name:d.name || d.file}))};
  }
  function load() {
    if (config) return Promise.resolve(config); if (loading) return loading;
    config = fallbackConfig();
    if (!window.EDITOR_SAVE || !window.EDITOR_SAVE.loadWorldAdventures) return Promise.resolve(config);
    loading = window.EDITOR_SAVE.loadWorldAdventures().then(c => { if (c && c.locations) config = c; return config; }).catch(() => config).finally(() => loading = null);
    return loading;
  }
  const current = () => (config.adventures || []).find(x => x.id === selected) || null;
  function render() {
    const root = $('#world-editor-view'); if (!root) return;
    if (!config) { root.innerHTML='<p>Carregando mapa-múndi…</p>'; load().then(render); return; }
    const a=current();
    root.innerHTML='<section class="worlded"><div class="worlded-head"><h2>🧭 Mapa do Mundo — Varlúzia</h2><p>Arraste cidades e destinos até a coordenada correta.</p></div><div class="worlded-layout"><div id="worlded-map" class="worlded-map"><img src="../'+esc(config.map_image)+'" alt="Mapa de Varlúzia"></div><aside class="worlded-panel"><button id="worlded-add" type="button">+ Adicionar destino</button><div id="worlded-form"></div><button id="worlded-save" type="button">Salvar mapa do mundo</button><div id="worlded-status"></div></aside></div></section>';
    const map=$('#worlded-map',root); (config.locations||[]).forEach(x=>marker(map,x,'city')); (config.adventures||[]).forEach(x=>marker(map,x,'adventure'));
    $('#worlded-add',root).onclick=()=>{let n=1,id; do{id='destino_'+n++;}while(config.adventures.some(x=>x.id===id)); config.adventures.push({id:id,nome:'Novo destino',x:50,y:50,fome:0,sede:0,dungeons:[],requisito:{tipo:'nenhum',valor:''}});selected=id;render();};
    $('#worlded-save',root).onclick=async()=>{const status=$('#worlded-status',root);if(!window.EDITOR_SAVE||!window.EDITOR_SAVE.saveWorldAdventures){status.textContent='Ligue o servidor para salvar.';return;}status.textContent='Salvando…';try{config=await window.EDITOR_SAVE.saveWorldAdventures(config.locations,config.adventures);status.textContent='✓ Mapa salvo.';render();}catch(e){status.textContent='Erro ao salvar: '+e.message;}};
    form(root,a);
  }
  function marker(map,item,kind) {
    const el=document.createElement('button'), x=Number(item.x)||0,y=Number(item.y)||0; el.type='button';el.className='worlded-marker '+kind+(selected===item.id?' selected':'');el.style.left=x+'%';el.style.top=y+'%';el.innerHTML='<span>✦</span><small>'+esc(item.nome)+'</small>';el.title=item.nome;
    el.onpointerdown=e=>{dragging={item:item,el:el};el.setPointerCapture&&el.setPointerCapture(e.pointerId);e.preventDefault();};el.onclick=()=>{if(kind==='adventure'){selected=item.id;render();}};map.appendChild(el);
  }
  document.addEventListener('pointermove',e=>{if(!dragging)return;const map=$('#worlded-map');if(!map)return;const r=map.getBoundingClientRect(),x=Math.max(0,Math.min(100,(e.clientX-r.left)*100/r.width)),y=Math.max(0,Math.min(100,(e.clientY-r.top)*100/r.height));dragging.item.x=Math.round(x*100)/100;dragging.item.y=Math.round(y*100)/100;dragging.el.style.left=x+'%';dragging.el.style.top=y+'%';});document.addEventListener('pointerup',()=>dragging=null);
  function form(root,a) {
    const host=$('#worlded-form',root);if(!a){host.innerHTML='<p>As cidades já estão marcadas. Selecione “Adicionar destino” para criar uma entrada de masmorra.</p>';return;}
    a.dungeons=Array.isArray(a.dungeons)?a.dungeons:[];
    const catalog=config.dungeons||[];
    const dungeonName=file=>{const d=catalog.find(x=>x.file===file);return d?(d.name||d.file):file;};
    const available=catalog.filter(d=>!a.dungeons.includes(d.file));
    const req=a.requisito||(a.requisito={});
    const options=available.map(d=>'<option value="'+esc(d.file)+'">'+esc(d.name||d.file)+'</option>').join('')||'<option value="">Nenhuma masmorra disponível</option>';
    const sequence=a.dungeons.map((file,index)=>'<div class="worlded-sequence-row"><b>'+String(index+1)+'ª</b><span>'+esc(dungeonName(file))+'</span><button type="button" data-stage-up="'+index+'"'+(index===0?' disabled':'')+' title="Mover para cima">↑</button><button type="button" data-stage-down="'+index+'"'+(index===a.dungeons.length-1?' disabled':'')+' title="Mover para baixo">↓</button><button type="button" data-stage-remove="'+index+'" title="Remover">×</button></div>').join('')||'<small>Nenhuma masmorra vinculada. Adicione a primeira etapa abaixo.</small>';
    host.innerHTML='<h3>Destino</h3><label>Nome<input id="we-name" value="'+esc(a.nome)+'"></label><div class="worlded-cost"><label>🍖 Fome<input id="we-hunger" type="number" min="0" value="'+Number(a.fome||0)+'"></label><label>💧 Sede<input id="we-thirst" type="number" min="0" value="'+Number(a.sede||0)+'"></label></div><label>Renome por etapa concluída<input id="we-renome-reward" type="number" min="0" value="'+Number(a.renome_recompensa==null?1:a.renome_recompensa)+'"></label><div class="worlded-sequence"><b>Requisitos para iniciar a rota</b><small>Todos os requisitos preenchidos devem ser atendidos.</small><label>Renome mínimo<input id="we-req-renome" type="number" min="0" value="'+Number(req.renome_min||0)+'"></label><label>Nível mínimo do grupo<input id="we-req-level" type="number" min="0" value="'+Number(req.nivel_grupo_min||0)+'"></label><label>Item-chave (id)<input id="we-req-item" value="'+esc(req.item_id||'')+'"></label><label>Fato/conversa exigida<input id="we-req-fact" value="'+esc(req.fato||'')+'"></label><label>Rota anterior concluída (id)<input id="we-req-adventure" value="'+esc(req.aventura_id||'')+'"></label></div><div class="worlded-sequence"><b>Rota de masmorras</b><small>A etapa 1 fica disponível. Cada etapa seguinte só libera ao concluir a anterior.</small>'+sequence+'</div><label>Adicionar masmorra<select id="we-dungeon-catalog">'+options+'</select></label><button id="we-add-dungeon" type="button"'+(available.length?'':' disabled')+'>+ Adicionar à sequência</button><button id="we-delete" type="button">Remover destino</button>';
    const sync=()=>{a.nome=$('#we-name',host).value;a.fome=Math.max(0,Number($('#we-hunger',host).value)||0);a.sede=Math.max(0,Number($('#we-thirst',host).value)||0);a.renome_recompensa=Math.max(0,Number($('#we-renome-reward',host).value)||0);a.requisito={renome_min:Math.max(0,Number($('#we-req-renome',host).value)||0),nivel_grupo_min:Math.max(0,Number($('#we-req-level',host).value)||0),item_id:$('#we-req-item',host).value,fato:$('#we-req-fact',host).value,aventura_id:$('#we-req-adventure',host).value};};
    host.querySelectorAll('input').forEach(x=>x.onchange=sync);
    $('#we-add-dungeon',host).onclick=()=>{const file=$('#we-dungeon-catalog',host).value;if(file&&!a.dungeons.includes(file)){a.dungeons.push(file);render();}};
    host.querySelectorAll('[data-stage-up]').forEach(btn=>btn.onclick=()=>{const i=Number(btn.dataset.stageUp);if(i>0){[a.dungeons[i-1],a.dungeons[i]]=[a.dungeons[i],a.dungeons[i-1]];render();}});
    host.querySelectorAll('[data-stage-down]').forEach(btn=>btn.onclick=()=>{const i=Number(btn.dataset.stageDown);if(i<a.dungeons.length-1){[a.dungeons[i+1],a.dungeons[i]]=[a.dungeons[i],a.dungeons[i+1]];render();}});
    host.querySelectorAll('[data-stage-remove]').forEach(btn=>btn.onclick=()=>{a.dungeons.splice(Number(btn.dataset.stageRemove),1);render();});
    $('#we-delete',host).onclick=()=>{config.adventures=config.adventures.filter(x=>x.id!==a.id);selected=null;render();};
  }
  window.EDITOR_WORLD={render:render,reload:()=>{config=null;return load().then(render);}};
})();
