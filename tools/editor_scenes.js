"use strict";
/* Biblioteca de Cenas da Campanha.  Dados ficam em campaigns/cenas.json e os
   vínculos são gravados na própria campanha/masmorra; não altera as conversas
   de cidade já existentes. */
(function () {
  let data = { schema_version: 1, scenes: {} }, selected = null, selectedVisualEvent = null;
  const $ = (s, r=document) => r.querySelector(s);
  const esc = s => String(s == null ? "" : s).replace(/[&<>\"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]));
  const slug = s => String(s||"cena").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]+/g,"_").replace(/^_+|_+$/g,"") || "cena";
  const newid = () => "ev_" + Math.random().toString(36).slice(2,8);
  const scene = () => selected && data.scenes[selected];
  const ensure = () => { if(!data.scenes) data.scenes={}; };
  function blank(id, name) { return { id, name, background:"", music:"", ambience:"", start:"inicio", events:[{id:"inicio",type:"dialogue",speaker:"Narrador",text:"",next:"",mandatory:false}] }; }
  function eventTypes(){ return ["dialogue","choice","test_cd","show_character","hide_character","expression","background","illustration","music","sound","wait","set_variable","give_key","give_item","remove_item","goto","end"]; }
  function render(){
    const root=$("#scenes-editor-view"); if(!root)return; ensure(); const sc=scene();
    root.innerHTML='<div class="sceneed"><header><div><h1>🎬 Biblioteca de Cenas</h1><p>Cenas reutilizáveis de campanha. As conversas atuais de cidade permanecem separadas.</p></div><button id="scene-save">Salvar biblioteca</button></header>'+
      '<div class="sceneed-layout"><aside class="sceneed-list"><button id="scene-new">＋ Nova cena</button>'+Object.entries(data.scenes).map(([id,s])=>'<button class="scene-row '+(id===selected?'on':'')+'" data-scene="'+esc(id)+'">'+esc(s.name||id)+'<small>'+esc(id)+'</small></button>').join('')+'</aside>'+
      '<main class="sceneed-main">'+(sc ? sceneForm(sc) : '<p class="sceneed-empty">Crie ou selecione uma cena.</p>')+'</main></div>';
    $("#scene-new",root).onclick=()=>{ const name=prompt("Nome da cena", "Nova cena"); if(!name)return; let id=slug(name), n=2; while(data.scenes[id])id=slug(name)+"_"+n++; data.scenes[id]=blank(id,name); selected=id; selectedVisualEvent=null; render(); };
    root.querySelectorAll("[data-scene]").forEach(b=>b.onclick=()=>{selected=b.dataset.scene;selectedVisualEvent=null;render();});
    if(!sc)return;
    $("#scene-name",root).oninput=e=>{sc.name=e.target.value;}; $("#scene-id",root).oninput=e=>{const to=slug(e.target.value); if(to!==selected&&!data.scenes[to]){delete data.scenes[selected];selected=to;data.scenes[to]=sc;sc.id=to;} e.target.value=selected;};
    ["background","music","ambience","start"].forEach(k=>$("#scene-"+k,root).oninput=e=>{sc[k]=e.target.value;if(k==='background'||k==='start')refreshScenePreview(root,sc);});
    root.querySelectorAll('[data-scene-file]').forEach(btn=>btn.onclick=()=>{
      const kind=btn.dataset.sceneFile, inp=document.createElement('input');
      inp.type='file'; inp.accept=['background','character','illustration'].includes(kind)?'image/png,image/jpeg,image/webp,image/gif':'audio/mpeg,audio/ogg,audio/wav,audio/mp4';
      inp.onchange=async()=>{const file=inp.files[0];if(!file)return;if(!window.EDITOR_SAVE||!window.EDITOR_SAVE.uploadSceneMedia){alert('Inicie o servidor para enviar o arquivo.');return;}btn.disabled=true;btn.textContent='Enviando…';try{const path=await window.EDITOR_SAVE.uploadSceneMedia(file,kind);const field=kind==='background'?'background':kind;sc[field]=path;$("#scene-"+field,root).value=path;btn.textContent='✓ '+file.name;}catch(err){alert(err.message);btn.textContent='Escolher arquivo';}finally{btn.disabled=false;}};
      inp.click();
    });
    $("#scene-add-event",root).onclick=()=>{const e={id:newid(),type:"dialogue",speaker:"Narrador",text:"",next:"",mandatory:false};sc.events.push(e);selectedVisualEvent=e.id;render();};
    $("#scene-delete",root).onclick=()=>{if(confirm('Excluir esta cena? Vínculos existentes serão invalidados e aparecerão na validação.')){delete data.scenes[selected];selected=null;render();}};
    root.querySelectorAll(".scene-event").forEach((card,i)=>{ card.dataset.order=String(i+1); bindEvent(card,sc,root); addVisualControls(card,sc,root); });
    mountScenePreview(root,sc);
    if(selectedVisualEvent){
      const layer=root.querySelector('.sceneed-layer-box[data-preview-event="'+selectedVisualEvent+'"]');
      const card=root.querySelector('.scene-event[data-eid="'+selectedVisualEvent+'"]');
      if(layer) layer.classList.add('selected');
      if(card){ card.classList.add('selected'); const timeline=root.querySelector('.sceneed-timeline'),first=timeline&&timeline.querySelector('.scene-event'); if(first&&first!==card)timeline.insertBefore(card,first); }
    }
    $("#scene-save",root).onclick=save;
  }
  function sceneForm(sc){ return '<section class="sceneed-props"><label>Nome<input id="scene-name" value="'+esc(sc.name)+'"></label><label>ID<input id="scene-id" value="'+esc(sc.id)+'"></label><label>Fundo<input id="scene-background" placeholder="assets/cenas/fundos/..." value="'+esc(sc.background)+'"><button type="button" data-scene-file="background">Escolher imagem</button></label><label>Música<input id="scene-music" placeholder="assets/cenas/audio/..." value="'+esc(sc.music)+'"><button type="button" data-scene-file="music">Escolher áudio</button></label><label>Ambiente<input id="scene-ambience" placeholder="assets/cenas/audio/..." value="'+esc(sc.ambience)+'"><button type="button" data-scene-file="ambience">Escolher áudio</button></label><label>Evento inicial<input id="scene-start" value="'+esc(sc.start)+'"></label><button id="scene-delete" class="scene-danger">Excluir cena</button></section><section class="sceneed-timeline"><h2>Timeline</h2><p>Use <b>Próximo</b> para um caminho normal. Escolhas e testes podem apontar para outros IDs.</p>'+(sc.events||[]).map(eventCard).join('')+'<button id="scene-add-event">＋ Adicionar evento</button></section>'; }
  function eventCard(e){return '<article class="scene-event" data-eid="'+esc(e.id)+'"><div><label>ID<input data-k="id" value="'+esc(e.id)+'"></label><label>Tipo<select data-k="type">'+eventTypes().map(t=>'<option '+(t===e.type?'selected':'')+' value="'+t+'">'+t+'</option>').join('')+'</select></label><label>Próximo<input data-k="next" value="'+esc(e.next)+'"></label><label><input data-k="mandatory" type="checkbox" '+(e.mandatory?'checked':'')+'> obrigatório</label></div><label>Personagem/Narrador<input data-k="speaker" value="'+esc(e.speaker)+'"></label><label>Texto<input data-k="text" value="'+esc(e.text)+'"></label><label>Opções / dados / efeitos (JSON)<textarea data-k="data" placeholder='+'"Ex.: [{\"id\":\"sim\",\"text\":\"Sim\",\"next\":\"sucesso\"}]">'+esc(e.data?JSON.stringify(e.data,null,2):'')+'</textarea></label><div><button data-up>↑</button><button data-down>↓</button><button data-del>Excluir</button></div></article>';}
  function bindEvent(card,sc,root){const e=sc.events.find(x=>x.id===card.dataset.eid);if(!e)return; card.querySelectorAll('[data-k]').forEach(inp=>inp.onchange=()=>{const k=inp.dataset.k;if(k==='mandatory')e[k]=inp.checked;else if(k==='data'){try{e.data=inp.value.trim()?JSON.parse(inp.value):undefined;inp.classList.remove('bad');}catch(_){inp.classList.add('bad');}}else e[k]=inp.value;refreshScenePreview(root,sc);});card.querySelector('[data-del]').onclick=()=>{sc.events=sc.events.filter(x=>x!==e);render();};card.querySelector('[data-up]').onclick=()=>move(sc,e,-1);card.querySelector('[data-down]').onclick=()=>move(sc,e,1);card.addEventListener('click',()=>{if(selectedVisualEvent!==e.id){selectedVisualEvent=e.id;refreshScenePreview(root,sc);}});}
  function addVisualControls(card,sc,root){
    const e=sc.events.find(x=>x.id===card.dataset.eid); if(!e)return;
    const d=(!Array.isArray(e.data)&&e.data)||{}; if(!e.data||Array.isArray(e.data))e.data=d;
    const box=document.createElement('div'); box.className='scene-event-visual';
    box.innerHTML='<label>Imagem do slide<button type="button" data-pick-character>Escolher imagem</button><small data-image-path></small></label><label>Fundo deste slide<button type="button" data-pick-background>Escolher fundo</button><small data-background-path></small></label><label>Slot<select data-slot><option>Left</option><option>CenterLeft</option><option>Center</option><option>CenterRight</option><option>Right</option></select></label><label>Transição<select data-transition><option value="instantâneo">Instantâneo</option><option value="fade">Fade</option><option value="slide_left">Slide Left</option><option value="slide_right">Slide Right</option><option value="slide_up">Slide Up</option><option value="slide_down">Slide Down</option><option value="zoom">Zoom</option><option value="dissolve">Dissolve</option></select></label>';
    const sync=()=>{const t=card.querySelector('[data-k="data"]');if(t)t.value=JSON.stringify(e.data,null,2);};
    const slot=box.querySelector('[data-slot]'),tr=box.querySelector('[data-transition]'); slot.value=d.slot||'Center';tr.value=d.transition||'fade';slot.onchange=()=>{d.slot=slot.value;sync();};tr.onchange=()=>{d.transition=tr.value;sync();};
    const path=box.querySelector('[data-image-path]');path.textContent=d.image||'Nenhuma imagem selecionada';
    box.querySelector('[data-pick-character]').onclick=()=>{const inp=document.createElement('input');inp.type='file';inp.accept='image/png,image/jpeg,image/webp,image/gif';inp.onchange=async()=>{const f=inp.files[0];if(!f)return;try{const kind=e.type==='illustration'?'illustration':'character';d.image=await window.EDITOR_SAVE.uploadSceneMedia(f,kind);path.textContent=d.image;sync();refreshScenePreview(root,sc);}catch(err){alert(err.message);}};inp.click();};
    const bgPath=box.querySelector('[data-background-path]');bgPath.textContent=d.background||'Usa o fundo padrão da cena';
    box.querySelector('[data-pick-background]').onclick=()=>{const inp=document.createElement('input');inp.type='file';inp.accept='image/png,image/jpeg,image/webp,image/gif';inp.onchange=async()=>{const f=inp.files[0];if(!f)return;try{d.background=await window.EDITOR_SAVE.uploadSceneMedia(f,'background');bgPath.textContent=d.background;sync();refreshScenePreview(root,sc);}catch(err){alert(err.message);}};inp.click();};
    card.insertBefore(box,card.firstChild);
  }
  function slotDefault(slot){return {Left:{x:3},CenterLeft:{x:22},Center:{x:38},CenterRight:{x:55},Right:{x:72}}[slot]||{x:38};}
  function sceneLayers(sc,eventId){const e=(sc.events||[]).find(x=>x.id===eventId)||(sc.events||[]).find(x=>x.id===sc.start)||(sc.events||[])[0];if(!e)return [];const d=e.data||{};return d.image&&(e.type==='show_character'||e.type==='dialogue'||e.type==='illustration'||(e.type==='background'&&/\/personagens\//.test(d.image)))?[e]:[];}
  function slideBackground(sc,eventId){const e=(sc.events||[]).find(x=>x.id===eventId)||(sc.events||[]).find(x=>x.id===sc.start)||(sc.events||[])[0],d=(e&&e.data)||{};return d.background||((e&&e.type==='background'&&d.image&&!/\/personagens\//.test(d.image))?d.image:sc.background)||'';}
  function refreshScenePreview(root,sc){const old=root.querySelector('.sceneed-preview');if(old)old.remove();mountScenePreview(root,sc);}
  function mountScenePreview(root,sc){
    const host=document.createElement('section');host.className='sceneed-preview';
    // O editor é servido de tools/, enquanto os caminhos das cenas são da raiz.
    const current=selectedVisualEvent||(sc.events||[]).find(e=>e.id===sc.start)?.id||((sc.events||[])[0]||{}).id||'';
    const background=slideBackground(sc,current),bg=background?'background-image:url(../'+esc(encodeURI(background))+')':'';
    host.innerHTML='<div class="sceneed-preview-head"><div><h2>Prévia do slide</h2><p>Clique em um evento para ver somente aquele slide. Arraste a imagem para posicioná-la.</p></div><button type="button" class="sceneed-play">▶ Reproduzir cena</button></div><div class="sceneed-stage" style="'+bg+'"></div>';
    const timeline=root.querySelector('.sceneed-timeline');timeline.parentElement.insertBefore(host,timeline);
    const stage=host.querySelector('.sceneed-stage');
    host.querySelector('.sceneed-play').onclick=()=>playScene(sc);
    // Captura antes do manipulador de arraste: mantém a seleção mesmo depois
    // que o preview é redesenhado ao soltar a imagem.
    stage.addEventListener('pointerdown',ev=>{const box=ev.target.closest('[data-preview-event]');if(box)selectedVisualEvent=box.dataset.previewEvent;},true);
    sceneLayers(sc,current).forEach(e=>{const d=e.data||{},def=slotDefault(d.slot||'Center'),box=document.createElement('div'),scale=Math.max(.2,Math.min(2,Number(d.scale)||100)/100);box.className='sceneed-layer-box';box.dataset.previewEvent=e.id;box.style.left=(d.x??def.x)+'%';box.style.top=(d.y??10)+'%';box.style.width=(d.w??25)+'%';box.style.height=(d.h??75)+'%';box.style.transform='scale('+scale+')';box.style.transformOrigin='center center';const im=document.createElement('img');im.src='../'+d.image;im.draggable=false;box.appendChild(im);const handle=document.createElement('i');handle.className='sceneed-resize-handle';box.appendChild(handle);stage.appendChild(box);});
    let drag=null;const selectLayer=box=>{stage.querySelectorAll('.sceneed-layer-box').forEach(x=>x.classList.toggle('selected',x===box));const card=root.querySelector('.scene-event[data-eid="'+box.dataset.previewEvent+'"]');const timeline=root.querySelector('.sceneed-timeline');if(card&&timeline){const first=timeline.querySelector('.scene-event');if(first&&card!==first)timeline.insertBefore(card,first);card.classList.add('selected');setTimeout(()=>card.classList.remove('selected'),1600);}};
    stage.addEventListener('pointerdown',ev=>{const box=ev.target.closest('[data-preview-event]');if(!box)return;const e=(sc.events||[]).find(x=>x.id===box.dataset.previewEvent);if(!e)return;selectLayer(box);const d=e.data||(e.data={}),resize=ev.target.classList.contains('sceneed-resize-handle');drag={box,e,resize,ox:ev.clientX,oy:ev.clientY,x:Number(d.x??slotDefault(d.slot||'Center').x),y:Number(d.y??10),w:Number(d.w??25),h:Number(d.h??75)};box.setPointerCapture(ev.pointerId);ev.preventDefault();});stage.addEventListener('pointermove',ev=>{if(!drag)return;const r=stage.getBoundingClientRect(),d=drag.e.data||(drag.e.data={}),dx=(ev.clientX-drag.ox)*100/r.width,dy=(ev.clientY-drag.oy)*100/r.height;if(drag.resize){d.w=Math.max(1,drag.w+dx*1.7);d.h=Math.max(1,drag.h+dy*1.7);drag.box.style.width=d.w+'%';drag.box.style.height=d.h+'%';}else{d.x=drag.x+dx;d.y=drag.y+dy;drag.box.style.left=d.x+'%';drag.box.style.top=d.y+'%';}});stage.addEventListener('pointerup',()=>{if(drag){render();drag=null;}});
  }
  function playScene(sc){
    let id=sc.start||((sc.events||[])[0]||{}).id, chars={}, audio=null;
    const byId=x=>(sc.events||[]).find(e=>e.id===x), ov=document.createElement('div');ov.className='sceneed-play-overlay';document.body.appendChild(ov);
    if(sc.music){audio=new Audio('../'+sc.music);audio.loop=true;audio.volume=.55;audio.play().catch(()=>{});}
    const close=()=>{if(audio){audio.pause();audio.src='';}ov.remove();};
    function visual(e){const d=e.data||{};if(d.background)sc={...sc,background:d.background};if(e.type==='show_character'&&d.image)chars[d.slot||'Center']=d;if(e.type==='hide_character')delete chars[d.slot||'Center'];if(e.type==='background'&&d.image){if(d.slot&&/assets\/cenas\/personagens\//.test(d.image))chars[d.slot||'Center']=d;else sc={...sc,background:d.image};}if(e.type==='dialogue'&&d.image)chars[d.slot||'Center']=d;}
    function paint(){const e=byId(id);if(!e){close();return;}visual(e);const bg=sc.background?'background-image:url(../'+esc(encodeURI(sc.background))+')':'',trans=['fade','slide_left','slide_right','slide_up','slide_down','zoom','dissolve'].includes((e.data||{}).transition)?e.data.transition:'fade';ov.innerHTML='<div class="sceneed-play-stage scene-transition-'+trans+'" style="'+bg+'"><div class="sceneed-play-shade"></div><div class="sceneed-play-chars"></div><div class="sceneed-play-dialog"><b></b><p></p><div class="sceneed-play-actions"></div></div><button class="sceneed-play-close">×</button></div>';ov.querySelector('.sceneed-play-close').onclick=close;const ch=ov.querySelector('.sceneed-play-chars');Object.entries(chars).forEach(([slot,d])=>{const im=document.createElement('img'),def=slotDefault(slot);im.src='../'+d.image;im.style.left=(d.x??def.x)+'%';im.style.top=(d.y??10)+'%';im.style.width=(d.w??25)+'%';im.style.height=(d.h??75)+'%';im.style.transform='scale('+(Math.max(.2,Math.min(2,Number(d.scale)||100)/100))+')';ch.appendChild(im);});ov.querySelector('.sceneed-play-dialog b').textContent=e.speaker||sc.name||'Narrador';ov.querySelector('.sceneed-play-dialog p').textContent=e.text||'';const a=ov.querySelector('.sceneed-play-actions');if(e.type==='choice'){(e.data||[]).forEach(o=>{const b=document.createElement('button');b.textContent=o.text||o.id;b.onclick=()=>{id=o.next||e.next;paint();};a.appendChild(b);});}else if(e.type==='test_cd'){const b=document.createElement('button');b.textContent='Testar';b.onclick=()=>{const d=e.data||{},roll=1+Math.floor(Math.random()*20),ok=roll>=Number(d.cd||10);b.textContent=(ok?'Sucesso':'Falha')+' ('+roll+')';id=d[ok?'success':'failure']||e.next;setTimeout(paint,650);};a.appendChild(b);}else if(e.type==='end'){const b=document.createElement('button');b.textContent='Concluir';b.onclick=close;a.appendChild(b);}else{const b=document.createElement('button');b.textContent=e.next?'Continuar ›':'Concluir';b.onclick=()=>{if(e.next){id=e.next;paint();}else close();};a.appendChild(b);}}
    paint();
  }
  function move(sc,e,d){const i=sc.events.indexOf(e),j=i+d;if(j<0||j>=sc.events.length)return;sc.events.splice(i,1);sc.events.splice(j,0,e);render();}
  function validate(){const err=[];for(const [id,s] of Object.entries(data.scenes||{})){const ids=new Set();for(const e of s.events||[]){if(!e.id||ids.has(e.id))err.push(id+': evento sem ID único');ids.add(e.id);if(e.next&&!ids.has(e.next)&&!(s.events||[]).some(x=>x.id===e.next))err.push(id+': próximo inexistente '+e.next);}}return err;}
  function save(){const errors=validate();if(errors.length){alert('Corrija antes de salvar:\n- '+errors.join('\n- '));return;}if(!window.EDITOR_SAVE||!window.EDITOR_SAVE.saveScenes){alert('Inicie o servidor para salvar.');return;}$("#scene-save").textContent='Salvando…';window.EDITOR_SAVE.saveScenes(data).then(()=>{ $("#scene-save").textContent='✓ Salvo'; }).catch(e=>{alert(e.message);$("#scene-save").textContent='Salvar biblioteca';});}
  function load(){
    if(!window.EDITOR_SAVE||!window.EDITOR_SAVE.loadScenes){render();return Promise.resolve(data);}
    return window.EDITOR_SAVE.loadScenes().then(v=>{
      data=(v&&v.scenes)?v:{schema_version:1,scenes:{}};
      selected=Object.keys(data.scenes)[0]||null;render();return data;
    }).catch(()=>{render();return data;});
  }
  window.EDITOR_SCENES={render,load,getData:()=>data};
})();
