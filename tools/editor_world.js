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
    $('#worlded-add',root).onclick=()=>{let n=1,id; do{id='destino_'+n++;}while(config.adventures.some(x=>x.id===id)); config.adventures.push({id:id,nome:'Novo destino',x:50,y:50,fome:0,sede:0,dungeons:[],espera_retorno:{modo:'fixa',rodadas:0,dados:''},oculto_ate_liberar:false,outro_rota:'',requisito:{tipo:'nenhum',valor:''}});selected=id;render();};
    $('#worlded-save',root).onclick=async()=>{const status=$('#worlded-status',root);if(!window.EDITOR_SAVE||!window.EDITOR_SAVE.saveWorldAdventures){status.textContent='Ligue o servidor para salvar.';return;}status.textContent='Salvando…';
      const ES=window.EDITOR_STORY;
      // Envia a forma mínima da história (string quando é 1 slide só-texto).
      const aventuras=config.adventures.map(av=>Object.assign({},av,{
        outro_rota: av._outroRotaSt ? (ES.storyToSaved(av._outroRotaSt)||'') : (av.outro_rota||''),
        dungeons:(av.dungeons||[]).map(s=>{
        if(typeof s==='string') return s;
        const o={file:s.file,encadear:!!s.encadear};
        const i=s._introSt?ES.storyToSaved(s._introSt):s.intro;
        const u=s._outroSt?ES.storyToSaved(s._outroSt):s.outro;
        if(i) o.intro=i; if(u) o.outro=u;
        return o;
      })}));
      try{config=await window.EDITOR_SAVE.saveWorldAdventures(config.locations,aventuras);status.textContent='✓ Mapa salvo.';render();}catch(e){status.textContent='Erro ao salvar: '+e.message;}};
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
    // Etapa: string (formato antigo) ou {file,encadear,intro,outro}. `intro`/`outro`
    // viram objetos de slides em memória (_introSt/_outroSt) e voltam à forma
    // mínima no salvar, via EDITOR_STORY.
    const ES=window.EDITOR_STORY;
    a.dungeons=a.dungeons.map(d=>{
      const st=(typeof d==='string')?{file:d,encadear:false,intro:'',outro:''}
                                    :{file:d.file,encadear:!!d.encadear,intro:d.intro||'',outro:d.outro||'',
                                      _introSt:d._introSt,_outroSt:d._outroSt};
      if(!st._introSt) st._introSt=ES.storyFromSaved(st.intro);
      if(!st._outroSt) st._outroSt=ES.storyFromSaved(st.outro);
      return st;
    });
    a.espera_retorno=Object.assign({modo:'fixa',rodadas:0,dados:''},a.espera_retorno||{});
    // História de fim de rota: objeto de slides em memória, forma mínima ao salvar.
    if(!a._outroRotaSt) a._outroRotaSt=ES.storyFromSaved(a.outro_rota);
    const catalog=config.dungeons||[];
    const dungeonName=file=>{const d=catalog.find(x=>x.file===file);return d?(d.name||d.file):file;};
    const available=catalog.filter(d=>!a.dungeons.some(s=>s.file===d.file));
    const req=a.requisito||(a.requisito={});
    const options=available.map(d=>'<option value="'+esc(d.file)+'">'+esc(d.name||d.file)+'</option>').join('')||'<option value="">Nenhuma masmorra disponível</option>';
    // Sem nenhum requisito preenchido, ocultar não faria efeito: requisito vazio
    // passa em _avaliar_requisito, então o ponto continuaria visível.
    const temReq = Number(req.renome_min)>0 || Number(req.nivel_grupo_min)>0
                || !!(req.item_id||'').trim() || !!(req.fato||'').trim()
                || !!(req.aventura_id||'').trim();
    const sequence=a.dungeons.map((stage,index)=>'<div class="worlded-sequence-row"><b>'+String(index+1)+'ª</b><span>'+esc(dungeonName(stage.file))+'</span><button type="button" data-stage-up="'+index+'"'+(index===0?' disabled':'')+' title="Mover para cima">↑</button><button type="button" data-stage-down="'+index+'"'+(index===a.dungeons.length-1?' disabled':'')+' title="Mover para baixo">↓</button><button type="button" data-stage-remove="'+index+'" title="Remover">×</button>'
      +'<label title="A próxima etapa começa imediatamente, sem voltar ao mapa-múndi"><input type="checkbox" data-stage-chain="'+index+'"'+(stage.encadear?' checked':'')+(index===a.dungeons.length-1?' disabled':'')+'> ⛓️ emendar na próxima</label>'
      +'<span class="worlded-stage-hist">'
      +  ES.histButtonHTML('stage-intro-'+index, stage._introSt).replace('história','abertura')
      +  ES.histButtonHTML('stage-outro-'+index, stage._outroSt).replace('história','encerramento')
      +'</span>'
      +'</div>').join('')||'<small>Nenhuma masmorra vinculada. Adicione a primeira etapa abaixo.</small>';
    host.innerHTML='<h3>Destino</h3><label>Nome<input id="we-name" value="'+esc(a.nome)+'"></label><div class="worlded-cost"><label>🍖 Fome<input id="we-hunger" type="number" min="0" value="'+Number(a.fome||0)+'"></label><label>💧 Sede<input id="we-thirst" type="number" min="0" value="'+Number(a.sede||0)+'"></label></div><div class="worlded-cost"><label>Espera para retornar<select id="we-wait-mode"><option value="fixa"'+(a.espera_retorno.modo==='fixa'?' selected':'')+'>Fixa (rodadas)</option><option value="dados"'+(a.espera_retorno.modo==='dados'?' selected':'')+'>Dados</option></select></label><label>Rodadas<input id="we-wait-rounds" type="number" min="0" max="99" value="'+Number(a.espera_retorno.rodadas||0)+'"></label><label>Fórmula<input id="we-wait-dice" value="'+esc(a.espera_retorno.dados||'')+'" placeholder="1d4"></label></div><label>Renome por etapa concluída<input id="we-renome-reward" type="number" min="0" value="'+Number(a.renome_recompensa==null?1:a.renome_recompensa)+'"></label><div class="worlded-cost"><span title="Aparece ao concluir a última etapa, depois do encerramento dela.">'+ES.histButtonHTML('we-outro-rota', a._outroRotaSt).replace('história','fim da rota').replace('📖','🏁')+'</span></div><div class="worlded-sequence"><b>Requisitos para iniciar a rota</b><small>Todos os requisitos preenchidos devem ser atendidos.</small><label>Renome mínimo<input id="we-req-renome" type="number" min="0" value="'+Number(req.renome_min||0)+'"></label><label>Nível mínimo do grupo<input id="we-req-level" type="number" min="0" value="'+Number(req.nivel_grupo_min||0)+'"></label><label>Item-chave (id)<input id="we-req-item" value="'+esc(req.item_id||'')+'"></label><label>Fato/conversa exigida<input id="we-req-fact" value="'+esc(req.fato||'')+'"></label><label>Rota anterior concluída (id)<input id="we-req-adventure" value="'+esc(req.aventura_id||'')+'"></label><label title="'+(temReq?'O ponto só aparece no mapa quando o requisito for cumprido.':'Preencha um requisito para poder ocultar.')+'"><input type="checkbox" id="we-hidden"'+(a.oculto_ate_liberar?' checked':'')+(temReq?'':' disabled')+'> 🕵️ ocultar no mapa até liberar</label></div><div class="worlded-sequence"><b>Rota de masmorras</b><small>A etapa 1 fica disponível. Cada etapa seguinte só libera ao concluir a anterior.</small>'+sequence+'</div><label>Adicionar masmorra<select id="we-dungeon-catalog">'+options+'</select></label><button id="we-add-dungeon" type="button"'+(available.length?'':' disabled')+'>+ Adicionar à sequência</button><button id="we-delete" type="button">Remover destino</button>';
    const sync=()=>{a.nome=$('#we-name',host).value;a.fome=Math.max(0,Number($('#we-hunger',host).value)||0);a.sede=Math.max(0,Number($('#we-thirst',host).value)||0);a.renome_recompensa=Math.max(0,Number($('#we-renome-reward',host).value)||0);a.requisito={renome_min:Math.max(0,Number($('#we-req-renome',host).value)||0),nivel_grupo_min:Math.max(0,Number($('#we-req-level',host).value)||0),item_id:$('#we-req-item',host).value,fato:$('#we-req-fact',host).value,aventura_id:$('#we-req-adventure',host).value};
      a.espera_retorno={modo:$('#we-wait-mode',host).value==='dados'?'dados':'fixa',rodadas:Math.max(0,Math.min(99,Number($('#we-wait-rounds',host).value)||0)),dados:$('#we-wait-dice',host).value.trim()};
      const cbH=$('#we-hidden',host); a.oculto_ate_liberar=!!(cbH&&cbH.checked&&!cbH.disabled);};
    host.querySelectorAll('input').forEach(x=>x.onchange=sync);
    // Preencher um requisito habilita o checkbox de ocultar na hora.
    ['#we-req-renome','#we-req-level','#we-req-item','#we-req-fact','#we-req-adventure']
      .forEach(sel=>{const el=$(sel,host); if(el) el.onchange=()=>{sync();render();};});
    $('#we-wait-mode',host).onchange=sync;
    const bFim=host.querySelector('.we-outro-rota');
    if(bFim) bFim.onclick=()=>ES.openHistoryEditor(a._outroRotaSt, 'fim da rota — '+(a.nome||''), render);
    $('#we-add-dungeon',host).onclick=()=>{const file=$('#we-dungeon-catalog',host).value;if(file&&!a.dungeons.some(s=>s.file===file)){a.dungeons.push({file:file,encadear:false,intro:'',outro:''});render();}};
    host.querySelectorAll('[data-stage-up]').forEach(btn=>btn.onclick=()=>{const i=Number(btn.dataset.stageUp);if(i>0){[a.dungeons[i-1],a.dungeons[i]]=[a.dungeons[i],a.dungeons[i-1]];render();}});
    host.querySelectorAll('[data-stage-down]').forEach(btn=>btn.onclick=()=>{const i=Number(btn.dataset.stageDown);if(i<a.dungeons.length-1){[a.dungeons[i+1],a.dungeons[i]]=[a.dungeons[i],a.dungeons[i+1]];render();}});
    host.querySelectorAll('[data-stage-remove]').forEach(btn=>btn.onclick=()=>{a.dungeons.splice(Number(btn.dataset.stageRemove),1);render();});
    host.querySelectorAll('[data-stage-chain]').forEach(cb=>cb.onchange=()=>{a.dungeons[Number(cb.dataset.stageChain)].encadear=cb.checked;});
    a.dungeons.forEach((stage,index)=>{
      const bi=host.querySelector('.stage-intro-'+index), bo=host.querySelector('.stage-outro-'+index);
      if(bi) bi.onclick=()=>ES.openHistoryEditor(stage._introSt, 'abertura da etapa '+(index+1), render);
      if(bo) bo.onclick=()=>ES.openHistoryEditor(stage._outroSt, 'encerramento da etapa '+(index+1), render);
    });
    $('#we-delete',host).onclick=()=>{config.adventures=config.adventures.filter(x=>x.id!==a.id);selected=null;render();};
  }
  window.EDITOR_WORLD={render:render,reload:()=>{config=null;return load().then(render);}};
})();
