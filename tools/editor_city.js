/* Editor de cidades: estabelecimentos físicos, com abas internas de estoque. */
(function () {
  "use strict";
  const root = document.getElementById("city-editor-view");
  let config = null, cityId = null, storeId = "ferreiro", tabId = null, mode = "shops", loading = null, selectedNpcId = null, selectedCityPointId = null, selectedSceneId = null;
  let cityDraft = null;   // cidade em edição/criação no painel (null = painel fechado)
  const esc = v => String(v == null ? "" : v).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const isVenom = i => i.effect === "coat_poison" || !!i.veneno_id || /^veneno_/.test(i.id || "")
    || /veneno|peçonha/i.test(i.name || "");
  const isThrowable = i => !!i.arremessavel || i.effect === "throwable"
    || /granada|fogo grego|incendiári|óleo|ácido|cola alquímica|rede/i.test(i.name || "");
  const isInstrument = i => i.tipo_item === "instrumento" || /^instrumento_/.test(i.id || "")
    || /harpa|tambor|sino|alaúde|alaude|trompa|lira|flauta|violino|gaita/i.test(i.name || "");
  const merchantTab = {
    geral: i => !isVenom(i) && !isThrowable(i) && !isInstrument(i)
      && !["ring", "head", "item", "boots"].includes(i.item_slot),
    venenos: isVenom,
    arremessaveis: isThrowable,
    acessorios: i => ["ring", "head", "item", "boots"].includes(i.item_slot),
    instrumentos: isInstrument,
  };
  const STORES = {
    ferreiro: { label:"🔨 Ferreiro", sources:["ferreiro_weapon","ferreiro_armor","ferreiro_ammo"], tabs:[
      ["ferreiro_weapon","Armas"], ["ferreiro_armor","Armaduras"], ["ferreiro_ammo","Munições"] ] },
    mercador: { label:"🛒 Mercador", sources:["mercador"], tabs:[
      ["geral","Itens gerais"], ["venenos","Venenos"], ["arremessaveis","Arremessáveis"],
      ["acessorios","Acessórios"], ["instrumentos","Instrumentos"] ] },
    templo: { label:"⛪ Templo", sources:["templo"], tabs:[["templo","Itens sagrados"]] },
    taverna: { label:"🍺 Taverna", sources:["taverna"], tabs:[["taverna","Comidas e bebidas"]] },
  };
  function ensure() {
    if (config) return Promise.resolve(config);
    if (loading) return loading;
    if (!window.EDITOR_SAVE || !window.EDITOR_SAVE.loadCityShops) return Promise.reject(new Error("Inicie o servidor para editar as lojas."));
    loading = window.EDITOR_SAVE.loadCityShops().then(c => { config = c; cityId = cityId || (c.cities[0] || {}).id; return c; }).finally(() => { loading = null; });
    return loading;
  }
  function city() { return (config.cities || []).find(c => c.id === cityId) || {}; }
  function stock() { return config.stock[cityId] || (config.stock[cityId] = {}); }
  function store() { return STORES[storeId] || STORES.ferreiro; }
  function sourceForTab() { return storeId === "mercador" ? "mercador" : tabId; }
  function itemsForTab() {
    const source = sourceForTab();
    let all = (config.catalog || []).filter(i => i.shop === source);
    if (storeId === "mercador") all = all.filter(merchantTab[tabId] || merchantTab.geral);
    return all;
  }
  function storeActive(id) { return STORES[id].sources.some(source => Array.isArray(stock()[source])); }
  function cityTabs() {
    const botao = (id, rotulo) => '<button data-city-mode="' + id + '" class="' + (mode === id ? "active" : "") + '">' + rotulo + '</button>';
    return '<div class="cityed-mode">' + botao("shops", "🛒 Lojas") + botao("map", "🗺️ Mapa da cidade")
      + botao("scenes", "💬 Cenas e NPCs") + botao("city", "🏘️ Cidades") + '</div>';
  }
  function bindCityMode() { root.querySelectorAll('[data-city-mode]').forEach(b => b.onclick = () => { mode = b.dataset.cityMode; render(); }); }
  function conversations(slot) {
    if (!Array.isArray(slot.conversations) || !slot.conversations.length) {
      slot.conversations=[{id:'inicial',texto:slot.dialog||'',requisito:{},efeito:{renome:0,fato:'',item_id:''},uma_vez:false}];
    }
    return slot.conversations;
  }
  function conversationEditor(slot) {
    return '<div class="cityed-conversations"><b>Conversas e desbloqueios</b>' + conversations(slot).map((conv,index)=>{
      const req=conv.requisito||{}, effect=conv.efeito||{};
      return '<fieldset class="cityed-conversation"><legend>Conversa '+(index+1)+'</legend><label>Texto<textarea data-conv-text data-npc-id="'+esc(slot.id)+'" data-conv-id="'+esc(conv.id)+'">'+esc(conv.texto||'')+'</textarea></label><div class="cityed-coords"><label>Renome mínimo<input type="number" min="0" data-conv-req="renome_min" data-npc-id="'+esc(slot.id)+'" data-conv-id="'+esc(conv.id)+'" value="'+Number(req.renome_min||0)+'"></label><label>Nível mínimo<input type="number" min="0" data-conv-req="nivel_grupo_min" data-npc-id="'+esc(slot.id)+'" data-conv-id="'+esc(conv.id)+'" value="'+Number(req.nivel_grupo_min||0)+'"></label><label>Fato exigido<input data-conv-req="fato" data-npc-id="'+esc(slot.id)+'" data-conv-id="'+esc(conv.id)+'" value="'+esc(req.fato||'')+'"></label><label>Item exigido<input data-conv-req="item_id" data-npc-id="'+esc(slot.id)+'" data-conv-id="'+esc(conv.id)+'" value="'+esc(req.item_id||'')+'"></label></div><div class="cityed-coords"><label>Renome concedido<input type="number" data-conv-effect="renome" data-npc-id="'+esc(slot.id)+'" data-conv-id="'+esc(conv.id)+'" value="'+Number(effect.renome||0)+'"></label><label>Fato concedido<input data-conv-effect="fato" data-npc-id="'+esc(slot.id)+'" data-conv-id="'+esc(conv.id)+'" value="'+esc(effect.fato||'')+'"></label><label>Item concedido (id)<input data-conv-effect="item_id" data-npc-id="'+esc(slot.id)+'" data-conv-id="'+esc(conv.id)+'" value="'+esc(effect.item_id||'')+'"></label><label>Uso único<select data-conv-once data-npc-id="'+esc(slot.id)+'" data-conv-id="'+esc(conv.id)+'"><option value="true"'+(conv.uma_vez!==false?' selected':'')+'>Sim</option><option value="false"'+(conv.uma_vez===false?' selected':'')+'>Não</option></select></label></div><button type="button" data-remove-conv data-npc-id="'+esc(slot.id)+'" data-conv-id="'+esc(conv.id)+'">Remover conversa</button></fieldset>';
    }).join('') + '<button type="button" data-add-conv="'+esc(slot.id)+'">+ Adicionar conversa</button></div>';
  }
  function renderScenes() {
    const c = city();
    const cenas = (config.scenes || (config.scenes = {}))[cityId] || ((config.scenes[cityId]) = {});
    if (!cenas[selectedSceneId]) selectedSceneId = Object.keys(cenas)[0] || null;
    const pontos = (config.city_points || (config.city_points = {}))[cityId] || ((config.city_points[cityId]) = {});
    const cena = selectedSceneId ? cenas[selectedSceneId] : null;
    const cityButtons = '<div class="cityed-cities">' + (config.cities || []).map(x => '<button data-city="' + esc(x.id) + '" class="' + (x.id === cityId ? 'active' : '') + '">' + esc(x.nome) + '<small>' + esc(x.tipo || 'cidade') + '</small></button>').join('') + '</div>';
    const abasCena = '<div class="cityed-cities">' + Object.entries(cenas).map(([id, s]) =>
      '<button data-scene="' + esc(id) + '" class="' + (id === selectedSceneId ? 'active' : '') + '">'
      + esc(s.nome || id) + '<small>' + esc(id) + '</small></button>').join('')
      + '<button data-scene-new type="button">+ Nova cena</button></div>';
    const slots = (cena && cena.slots || []).filter(slot => !slot.removed); slots.forEach(conversations);
    if (!slots.some(slot => slot.id === selectedNpcId)) selectedNpcId = slots[0] && slots[0].id;
    // Pontos com tela própria (masmorra, caravana, guilda) despacham pelo tipo
    // antes da resolução de cena no jogo: uma cena presa a eles nunca abriria.
    const PONTO_PROPRIO = ["dungeon", "caravana", "guilda"];
    const pontoAtual = Object.keys(pontos).find(pid => pontos[pid].scene === selectedSceneId) || "";
    const opcoesPonto = Object.entries(pontos)
      .filter(([pid, p]) => pid === pontoAtual || PONTO_PROPRIO.indexOf(String(p.type || pid)) < 0)
      .map(([pid, p]) => '<option value="' + esc(pid) + '"' + (pid === pontoAtual ? ' selected' : '') + '>'
        + esc(p.name || pid) + ' (' + esc(p.type || pid) + ')</option>').join('');
    // O servidor re-liga sozinho um ponto à cena de MESMO id quando o ponto está
    // solto (_garantir_pontos_implicitos, roda a cada save). Nesse par, desligar
    // não pega — melhor não oferecer a ação do que oferecê-la sem efeito.
    const fixoPorId = pontoAtual && pontoAtual === selectedSceneId;
    const opcaoNenhum = fixoPorId
      ? '<option value="" disabled>— fixo: o ponto tem o mesmo id da cena —</option>'
      : '<option value=""' + (pontoAtual ? '' : ' selected') + '>— nenhum ponto —</option>';
    const metaCena = !cena ? '' : '<div class="cityed-tavern-assets"><label>Nome da cena<input data-scene-nome value="' + esc(cena.nome || '') + '"></label><label>Vinculada a<select data-scene-ponto>' + opcaoNenhum + opcoesPonto + '</select></label><button type="button" data-scene-novo-ponto>+ Criar ponto para esta cena</button><button type="button" data-scene-excluir>Excluir cena</button></div>';
    const sceneConfig = cena ? '<div class="cityed-tavern-assets"><label>Imagem de fundo<input data-scene-path="background" value="' + esc(cena.background || '') + '"></label><input id="cityed-bg-file" type="file" accept="image/png,image/jpeg,image/webp,image/gif"><button data-upload-tavern="background">Enviar fundo</button><label>Máscara transparente de NPCs<input data-scene-path="mask" value="' + esc(cena.mask || '') + '"></label><input id="cityed-mask-file" type="file" accept="image/png,image/jpeg,image/webp,image/gif"><button data-upload-tavern="mask">Enviar máscara</button></div>' : '';
    const tituloCena = cena ? esc(cena.nome || selectedSceneId) + ' — ' + esc(c.nome) : esc(c.nome);
    const painel = !cena
      ? '<section class="cityed-tavern"><h2>💬 Cenas de ' + esc(c.nome) + '</h2><p>Esta cidade ainda não tem nenhuma cena de conversa. Crie a primeira em “+ Nova cena”.</p></section>'
      : (slots.length
        ? '<section class="cityed-tavern"><h2>💬 ' + tituloCena + '</h2><p>Configure as falas, requisitos e recompensas narrativas de cada personagem da cena.</p>' + metaCena + sceneConfig + slots.map(slot => '<article class="cityed-npc"><img src="../' + esc(cena.mask || slot.image) + '" alt=""><div><label>Nome<input data-npc-name="' + esc(slot.id) + '" value="' + esc(slot.name) + '"></label>' + conversationEditor(slot) + '<div class="cityed-coords"><label>X %<input type="number" min="0" max="100" step="0.1" data-npc-pos="x" data-npc-id="' + esc(slot.id) + '" value="' + Number(slot.x) + '"></label><label>Y %<input type="number" min="0" max="100" step="0.1" data-npc-pos="y" data-npc-id="' + esc(slot.id) + '" value="' + Number(slot.y) + '"></label><label>Largura %<input type="number" min="1" max="100" step="0.1" data-npc-pos="w" data-npc-id="' + esc(slot.id) + '" value="' + Number(slot.w) + '"></label><label>Altura %<input type="number" min="1" max="100" step="0.1" data-npc-pos="h" data-npc-id="' + esc(slot.id) + '" value="' + Number(slot.h) + '"></label></div></div></article>').join('') + '</section>'
        : '<section class="cityed-tavern"><h2>💬 ' + tituloCena + '</h2><p>Esta cena ainda está vazia. Envie um fundo e adicione os personagens.</p>' + metaCena + sceneConfig + '</section>');
    root.innerHTML = '<div class="cityed"><header><div><h1>🏘️ Cidades e Lojas</h1><p>Edite as cenas de conversa, os NPCs e suas falas desbloqueáveis por renome, nível, fatos e itens.</p></div><button id="cityed-save" class="cityed-save">Salvar alterações</button></header>' + cityTabs() + cityButtons + abasCena + painel + '<div id="cityed-status"></div></div>';
    root.querySelectorAll('[data-city]').forEach(b => b.onclick = () => { cityId = b.dataset.city; selectedSceneId = null; render(); });
    bindCityMode();
    root.querySelectorAll('[data-scene]').forEach(b => b.onclick = () => { selectedSceneId = b.dataset.scene; selectedNpcId = null; render(); });
    const btnNova = root.querySelector('[data-scene-new]');
    if (btnNova) btnNova.onclick = () => {
      const nome = prompt('Nome da cena (ex.: Docas)'); if (!nome) return;
      const base = nome.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'cena';
      const id = base + '_' + Date.now().toString(36).slice(-4);
      cenas[id] = { nome: nome, background: '', art_ratio: 1.5, mode: 'individual', mask: '', slots: [] };
      selectedSceneId = id; selectedNpcId = null; render();
    };
    const inputNome = root.querySelector('[data-scene-nome]');
    if (inputNome) inputNome.oninput = () => { if (cena) cena.nome = inputNome.value; };
    const selPonto = root.querySelector('[data-scene-ponto]');
    if (selPonto) selPonto.onchange = () => {
      Object.values(pontos).forEach(p => { if (p.scene === selectedSceneId) delete p.scene; });
      if (selPonto.value && pontos[selPonto.value]) pontos[selPonto.value].scene = selectedSceneId;
      render();
    };
    const btnNovoPonto = root.querySelector('[data-scene-novo-ponto]');
    if (btnNovoPonto) btnNovoPonto.onclick = () => {
      const nome = prompt('Nome do ponto na ilustração', (cena && cena.nome) || 'Novo local'); if (!nome) return;
      const emoji = prompt('Emoji do marcador', '💬') || '💬';
      Object.values(pontos).forEach(p => { if (p.scene === selectedSceneId) delete p.scene; });
      pontos[selectedSceneId] = { x: 50, y: 50, type: 'cena', name: nome, emoji: emoji, scene: selectedSceneId };
      render();
    };
    const btnExcluir = root.querySelector('[data-scene-excluir]');
    if (btnExcluir) btnExcluir.onclick = () => {
      if (!window.confirm('Excluir esta cena? Os NPCs e as conversas dela serão apagados.')) return;
      const alvo = selectedSceneId;
      delete cenas[alvo];
      Object.values(pontos).forEach(p => { if (p.scene === alvo) delete p.scene; });
      selectedSceneId = null; selectedNpcId = null; render();
    };
    // Prévia WYSIWYG: o fundo e as camadas transparentes aparecem como no jogo.
    if (cena && slots.length) {
      const preview = document.createElement('div'); preview.className = 'cityed-tavern-preview';
      preview.innerHTML = '<img class="cityed-tavern-bg" src="../' + esc(cena.background || '') + '" alt="Fundo da cena">'
        + slots.map(slot => !slot.image ? '' : '<img draggable="false" class="cityed-tavern-layer ' + (slot.id === selectedNpcId ? 'selected' : '') + '" data-preview-slot="' + esc(slot.id) + '" src="../' + esc(slot.image) + '" style="left:' + Number(slot.x) + '%;top:' + Number(slot.y) + '%;width:' + Number(slot.w) + '%;height:' + Number(slot.h) + '%;z-index:' + (10 + Number(slot.z || 1)) + '" alt="' + esc(slot.name) + '" title="Selecione e arraste: ' + esc(slot.name) + '"><button type="button" class="cityed-resize" data-resize-slot="' + esc(slot.id) + '" style="left:' + (Number(slot.x)+Number(slot.w)) + '%;top:' + (Number(slot.y)+Number(slot.h)) + '%" aria-label="Redimensionar ' + esc(slot.name) + '"></button>').join('')
        + '<span class="cityed-preview-hint">Arraste os frequentadores para posicioná-los</span>';
      const section = root.querySelector('.cityed-tavern'); section.insertBefore(preview, section.querySelector('.cityed-npc'));
      // O editor visual trabalha apenas com fundo + elementos individuais.
      const maskPath = root.querySelector('[data-scene-path="mask"]');
      if (maskPath) maskPath.closest('label').remove();
      const maskFile = root.querySelector('#cityed-mask-file'); if (maskFile) maskFile.remove();
      const maskUpload = root.querySelector('[data-upload-tavern="mask"]'); if (maskUpload) maskUpload.remove();
      root.querySelectorAll('.cityed-npc').forEach((card, index) => {
        const slot = slots[index]; if (!slot) return;
        card.querySelector('img').src = slot.image ? '../' + slot.image : '';
        const controls = document.createElement('label'); controls.className = 'cityed-npc-image';
        controls.textContent = 'Imagem do frequentador';
        controls.innerHTML += '<input type="file" data-npc-file="' + esc(slot.id) + '" accept="image/png,image/jpeg,image/webp,image/gif"><button type="button" data-upload-npc="' + esc(slot.id) + '">Enviar imagem</button><button type="button" data-select-npc="' + esc(slot.id) + '">Selecionar e mover</button><button type="button" data-layer="front" data-npc-id="' + esc(slot.id) + '">Trazer para frente</button><button type="button" data-layer="back" data-npc-id="' + esc(slot.id) + '">Enviar para trás</button><button type="button" data-remove-npc="' + esc(slot.id) + '">Remover NPC da cena</button>';
        card.querySelector('div').insertBefore(controls, card.querySelector('label'));
      });
    }
    root.querySelectorAll('[data-npc-name]').forEach(input => input.oninput = () => { const slot=slots.find(s => s.id === input.dataset.npcName); if(slot) slot.name=input.value; });
    root.querySelectorAll('[data-npc-dialog]').forEach(input => input.oninput = () => { const slot=slots.find(s => s.id === input.dataset.npcDialog); if(slot) slot.dialog=input.value; });
    const getConv = input => { const slot=slots.find(s=>s.id===input.dataset.npcId); return slot && conversations(slot).find(c=>c.id===input.dataset.convId); };
    root.querySelectorAll('[data-conv-text]').forEach(input=>input.oninput=()=>{const c=getConv(input);if(c)c.texto=input.value;});
    root.querySelectorAll('[data-conv-req]').forEach(input=>input.oninput=()=>{const c=getConv(input);if(!c)return;c.requisito=c.requisito||{};c.requisito[input.dataset.convReq]=input.dataset.convReq.endsWith('_min')?Math.max(0,Number(input.value)||0):input.value;});
    root.querySelectorAll('[data-conv-effect]').forEach(input=>input.oninput=()=>{const c=getConv(input);if(!c)return;c.efeito=c.efeito||{};c.efeito[input.dataset.convEffect]=input.dataset.convEffect==='renome'?Number(input.value)||0:input.value;});
    root.querySelectorAll('[data-conv-once]').forEach(input=>input.onchange=()=>{const c=getConv(input);if(c)c.uma_vez=input.value==='true';});
    root.querySelectorAll('[data-add-conv]').forEach(btn=>btn.onclick=()=>{const slot=slots.find(s=>s.id===btn.dataset.addConv);if(!slot)return;const id='fala_'+Date.now().toString(36);conversations(slot).push({id,texto:'Nova conversa',requisito:{},efeito:{renome:0,fato:'',item_id:''},uma_vez:true});render();});
    root.querySelectorAll('[data-remove-conv]').forEach(btn=>btn.onclick=()=>{const slot=slots.find(s=>s.id===btn.dataset.npcId);if(!slot)return;slot.conversations=conversations(slot).filter(c=>c.id!==btn.dataset.convId);render();});
    root.querySelectorAll('[data-scene-path]').forEach(input => input.oninput = () => { if(cena) cena[input.dataset.scenePath]=input.value; });
    root.querySelectorAll('[data-npc-pos]').forEach(input => input.oninput = () => { const slot=slots.find(s => s.id === input.dataset.npcId); const n=Number(input.value); if(slot && Number.isFinite(n)) slot[input.dataset.npcPos]=n; });
    root.querySelectorAll('[data-upload-tavern]').forEach(btn => btn.onclick = async () => {
      const kind=btn.dataset.uploadTavern, file=root.querySelector(kind === 'background' ? '#cityed-bg-file' : '#cityed-mask-file').files[0];
      const status=root.querySelector('#cityed-status'); if(!file){ status.textContent='Escolha uma imagem primeiro.'; return; }
      status.textContent='Enviando imagem…';
      try { cena[kind]=await window.EDITOR_SAVE.uploadTavernArt(file); status.textContent='Imagem enviada. Salve as alterações para aplicá-la.'; render(); }
      catch(e){ status.textContent='Erro ao enviar: '+e.message; }
    });
    root.querySelectorAll('[data-upload-npc]').forEach(btn => btn.onclick = async () => {
      const slot=slots.find(s => s.id === btn.dataset.uploadNpc), file=root.querySelector('[data-npc-file="' + btn.dataset.uploadNpc + '"]').files[0], status=root.querySelector('#cityed-status');
      if(!slot || !file){ status.textContent='Escolha uma imagem do frequentador primeiro.'; return; }
      status.textContent='Enviando imagem…';
      try { slot.image=await window.EDITOR_SAVE.uploadTavernArt(file); delete slot.remove_image; cena.mode='individual'; render(); }
      catch(e){ status.textContent='Erro ao enviar: '+e.message; }
    });
    root.querySelectorAll('[data-remove-npc]').forEach(btn => btn.onclick = () => {
      const slot=slots.find(s => s.id === btn.dataset.removeNpc); if(!slot) return;
      slot.removed=true; selectedNpcId=null; root.querySelector('#cityed-status').textContent='NPC removido da cena. Salve para confirmar.'; render();
    });
    root.querySelectorAll('[data-layer]').forEach(btn => btn.onclick = () => {
      const slot=slots.find(s => s.id === btn.dataset.npcId); if(!slot) return;
      const levels=slots.map(s=>Number(s.z || 1)); slot.z=btn.dataset.layer === 'front' ? Math.max(...levels)+1 : Math.min(...levels)-1;
      render();
    });
    if (cena) {
      if (!Array.isArray(cena.slots)) cena.slots = [];
      const addNpc=document.createElement('button');
      addNpc.type='button'; addNpc.textContent='+ Adicionar NPC à cena';
      addNpc.onclick=()=>{ const id='npc_'+Date.now().toString(36), z=Math.max(0,...slots.map(s=>Number(s.z || 1)))+1; cena.slots.push({id,name:'Novo NPC',image:'',x:40,y:40,w:14,h:20,z,dialog:''}); selectedNpcId=id; render(); };
      root.querySelector('.cityed-tavern').appendChild(addNpc);
    }
    const previewStage = root.querySelector('.cityed-tavern-preview');
    // Alças nas bordas, além do canto: passar o mouse nas laterais permite
    // redimensionar como nos editores de imagem do sistema.
    if (previewStage) slots.filter(s => s.image).forEach(slot => {
      [['e',slot.x+slot.w,slot.y+slot.h/2],['s',slot.x+slot.w/2,slot.y+slot.h],
       ['w',slot.x,slot.y+slot.h/2],['n',slot.x+slot.w/2,slot.y]].forEach(([dir,x,y]) => {
        const h=document.createElement('button'); h.type='button'; h.className='cityed-resize cityed-resize-edge cityed-resize-'+dir;
        h.dataset.resizeSlot=slot.id; h.dataset.resizeDir=dir; h.style.left=x+'%'; h.style.top=y+'%';
        h.setAttribute('aria-label','Redimensionar '+slot.name); previewStage.appendChild(h);
      });
    });
    const selectNpc = id => {
      selectedNpcId=id;
      root.querySelectorAll('[data-preview-slot]').forEach(layer => layer.classList.toggle('selected', layer.dataset.previewSlot === id));
      root.querySelectorAll('[data-select-npc]').forEach(btn => btn.classList.toggle('active', btn.dataset.selectNpc === id));
      root.querySelectorAll('.cityed-npc').forEach(card => card.classList.toggle('selected', card.querySelector('[data-select-npc]')?.dataset.selectNpc === id));
      const card = Array.from(root.querySelectorAll('.cityed-npc')).find(x => x.querySelector('[data-select-npc]')?.dataset.selectNpc === id);
      const first = root.querySelector('.cityed-npc');
      if(card && first && card !== first) first.parentElement.insertBefore(card, first);
    };
    if(selectedNpcId) selectNpc(selectedNpcId);
    root.querySelectorAll('[data-select-npc]').forEach(btn => btn.onclick = () => selectNpc(btn.dataset.selectNpc));
    root.querySelectorAll('[data-preview-slot]').forEach(layer => {
      layer.onpointerdown = e => {
      const slot=slots.find(s => s.id === layer.dataset.previewSlot), preview=layer.parentElement, rect=preview.getBoundingClientRect();
      if(!slot || !rect.width || !rect.height) return;
      const startX=e.clientX, startY=e.clientY, x=Number(slot.x), y=Number(slot.y);
      e.preventDefault(); e.stopPropagation(); layer.classList.add('dragging');
      const move = move => {
        slot.x=Math.max(0,Math.min(100-Number(slot.w), Math.round((x+(move.clientX-startX)*100/rect.width)*10)/10));
        slot.y=Math.max(0,Math.min(100-Number(slot.h), Math.round((y+(move.clientY-startY)*100/rect.height)*10)/10));
        layer.style.left=slot.x+'%'; layer.style.top=slot.y+'%';
        root.querySelector('[data-npc-pos="x"][data-npc-id="'+slot.id+'"]').value=slot.x;
        root.querySelector('[data-npc-pos="y"][data-npc-id="'+slot.id+'"]').value=slot.y;
      };
      const end = () => { layer.classList.remove('dragging'); window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', end); window.removeEventListener('pointercancel', end); };
      window.addEventListener('pointermove', move); window.addEventListener('pointerup', end); window.addEventListener('pointercancel', end);
      };
    });
    // A cena recebe o arraste. O fundo tem pointer-events:none e nunca bloqueia
    // uma camada. Para camadas sobrepostas, selecione-a no respectivo card.
    root.querySelectorAll('[data-preview-slot]').forEach(layer => { layer.onpointerdown = null; });
    if (previewStage) {
      previewStage.onpointerdown = null;
      previewStage.onmousedown = e => {
      if (e.button !== 0) return;
      const hit = e.target.closest && e.target.closest('[data-preview-slot]');
      const id = hit ? hit.dataset.previewSlot : selectedNpcId;
      const slot = slots.find(s => s.id === id), rect = previewStage.getBoundingClientRect();
      if (!slot || !rect.width || !rect.height) return;
      selectNpc(id); e.preventDefault();
      const startX=e.clientX, startY=e.clientY, x=Number(slot.x), y=Number(slot.y);
      const move = move => {
        slot.x=Math.max(0,Math.min(100-Number(slot.w), Math.round((x+(move.clientX-startX)*100/rect.width)*10)/10));
        slot.y=Math.max(0,Math.min(100-Number(slot.h), Math.round((y+(move.clientY-startY)*100/rect.height)*10)/10));
        const layer=root.querySelector('[data-preview-slot="'+slot.id+'"]');
        if(layer){ layer.style.left=slot.x+'%'; layer.style.top=slot.y+'%'; }
        root.querySelectorAll('[data-resize-slot="'+slot.id+'"]').forEach(hd => { const d=hd.dataset.resizeDir; if(!d){hd.style.left=(slot.x+slot.w)+'%';hd.style.top=(slot.y+slot.h)+'%';} if(d==='e'){hd.style.left=(slot.x+slot.w)+'%';hd.style.top=(slot.y+slot.h/2)+'%';} if(d==='s'){hd.style.left=(slot.x+slot.w/2)+'%';hd.style.top=(slot.y+slot.h)+'%';} if(d==='w'){hd.style.left=slot.x+'%';hd.style.top=(slot.y+slot.h/2)+'%';} if(d==='n'){hd.style.left=(slot.x+slot.w/2)+'%';hd.style.top=slot.y+'%';} });
        root.querySelector('[data-npc-pos="x"][data-npc-id="'+slot.id+'"]').value=slot.x;
        root.querySelector('[data-npc-pos="y"][data-npc-id="'+slot.id+'"]').value=slot.y;
      };
      const end = () => { window.removeEventListener('mousemove', move); window.removeEventListener('mouseup', end); };
      window.addEventListener('mousemove', move); window.addEventListener('mouseup', end);
      };
    }
    root.querySelectorAll('[data-resize-slot]').forEach(handle => handle.onmousedown = e => {
      const slot=slots.find(s => s.id === handle.dataset.resizeSlot), rect=previewStage && previewStage.getBoundingClientRect();
      if(!slot || !rect || !rect.width || !rect.height) return;
      e.preventDefault(); e.stopPropagation(); const startX=e.clientX, startY=e.clientY, x=Number(slot.x), y=Number(slot.y), w=Number(slot.w), h=Number(slot.h), dir=handle.dataset.resizeDir || 'se';
      const move = move => {
        const dx=(move.clientX-startX)*100/rect.width, dy=(move.clientY-startY)*100/rect.height;
        if(dir === 'e' || dir === 'se') slot.w=Math.max(2,Math.min(100-x,Math.round((w+dx)*10)/10));
        if(dir === 's' || dir === 'se') slot.h=Math.max(2,Math.min(100-y,Math.round((h+dy)*10)/10));
        if(dir === 'w'){ const nx=Math.max(0,Math.min(x+w-2,Math.round((x+dx)*10)/10)); slot.x=nx; slot.w=Math.max(2,Math.round((w+x-nx)*10)/10); }
        if(dir === 'n'){ const ny=Math.max(0,Math.min(y+h-2,Math.round((y+dy)*10)/10)); slot.y=ny; slot.h=Math.max(2,Math.round((h+y-ny)*10)/10); }
        const layer=root.querySelector('[data-preview-slot="'+slot.id+'"]'), resize=root.querySelector('[data-resize-slot="'+slot.id+'"]');
        if(layer){ layer.style.width=slot.w+'%'; layer.style.height=slot.h+'%'; }
        if(resize){ resize.style.left=(slot.x+slot.w)+'%'; resize.style.top=(slot.y+slot.h)+'%'; }
        root.querySelectorAll('[data-resize-slot="'+slot.id+'"]').forEach(hd => { const d=hd.dataset.resizeDir; if(d==='e'){hd.style.left=(slot.x+slot.w)+'%';hd.style.top=(slot.y+slot.h/2)+'%';} if(d==='s'){hd.style.left=(slot.x+slot.w/2)+'%';hd.style.top=(slot.y+slot.h)+'%';} if(d==='w'){hd.style.left=slot.x+'%';hd.style.top=(slot.y+slot.h/2)+'%';} if(d==='n'){hd.style.left=(slot.x+slot.w/2)+'%';hd.style.top=slot.y+'%';} });
        if(layer){ layer.style.left=slot.x+'%'; layer.style.top=slot.y+'%'; }
        root.querySelector('[data-npc-pos="x"][data-npc-id="'+slot.id+'"]').value=slot.x;
        root.querySelector('[data-npc-pos="y"][data-npc-id="'+slot.id+'"]').value=slot.y;
        root.querySelector('[data-npc-pos="w"][data-npc-id="'+slot.id+'"]').value=slot.w;
        root.querySelector('[data-npc-pos="h"][data-npc-id="'+slot.id+'"]').value=slot.h;
      };
      const end=()=>{ window.removeEventListener('mousemove',move); window.removeEventListener('mouseup',end); };
      window.addEventListener('mousemove',move); window.addEventListener('mouseup',end);
    });
    if(window._cityTavernDeleteHandler) window.removeEventListener('keydown', window._cityTavernDeleteHandler);
    window._cityTavernDeleteHandler = e => {
      if(e.key !== 'Delete' || /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement && document.activeElement.tagName)) return;
      const slot=slots.find(s => s.id === selectedNpcId); if(!slot || !slot.image) return;
      e.preventDefault(); slot.image=''; slot.remove_image=true; root.querySelector('#cityed-status').textContent='Imagem removida da cena. Salve as alterações para confirmar.'; render();
    };
    window.addEventListener('keydown', window._cityTavernDeleteHandler);
    const sceneSave=document.createElement('button');
    sceneSave.type='button'; sceneSave.className='cityed-save cityed-save-local';
    sceneSave.textContent='Salvar cenas desta cidade'; sceneSave.onclick=saveAll;
    root.querySelector('.cityed-tavern').appendChild(sceneSave);
    root.querySelector('#cityed-save').onclick = saveAll;
  }
  async function saveAll() {
    const status = root.querySelector('#cityed-status'); status.textContent = 'Salvando…';
    try { config = await window.EDITOR_SAVE.saveCityShops(config.stock, config.scenes, config.city_points); status.textContent = '✓ Alterações salvas.'; render(); }
    catch (e) { status.textContent = 'Erro ao salvar: ' + e.message; }
  }
  function renderCityMap() {
    const c = city();
    const points = (config.city_points || (config.city_points = {}))[cityId] || ((config.city_points || (config.city_points = {}))[cityId] = {});
    const types = {ferreiro:'Ferreiro', mercador:'Mercador', templo:'Templo', taverna:'Taverna', guilda:'Guilda', caravana:'Caravana de Viagem', cena:'Local de conversa'};
    if (!points[selectedCityPointId]) selectedCityPointId = Object.keys(points)[0] || null;
    const selected = selectedCityPointId && points[selectedCityPointId];
    root.innerHTML = '<div class="cityed"><header><div><h1>Mapa de ' + esc(c.nome) + '</h1><p>Arraste os pontos sobre a imagem. Cada ponto pode abrir um tipo de loja.</p></div><button id="cityed-save" class="cityed-save">Salvar mapa da cidade</button></header>' + cityTabs()
      + '<div class="cityed-cities">' + (config.cities || []).map(x => '<button data-city="' + esc(x.id) + '" class="' + (x.id === cityId ? 'active' : '') + '">' + esc(x.nome) + '</button>').join('') + '</div>'
      + '<div class="worlded-layout"><div id="citymap-editor" class="worlded-map citymap-editor"><img src="../' + esc(c.imagem || '') + '" alt="' + esc(c.nome) + '"></div><aside class="worlded-panel"><button id="citymap-add" type="button">+ Adicionar ponto</button><div id="citymap-form"></div><button id="citymap-delete" type="button">Excluir ponto</button><button id="citymap-save" type="button">Salvar edição deste mapa</button><div id="cityed-status"></div></aside></div></div>';
    const map = root.querySelector('#citymap-editor'); let dragging = null;
    const marker = (id, point) => {
      const type = point.type || id, name = point.name || types[type] || id;
      const b = document.createElement('button'); b.type='button'; b.className='worlded-marker city ' + (id === selectedCityPointId ? 'selected' : ''); b.style.left=point.x+'%'; b.style.top=point.y+'%'; b.innerHTML='<span>✦</span><small>'+esc(name)+'</small>'; b.title=name;
      b.onpointerdown=e=>{dragging={id:id,point:point,el:b};b.setPointerCapture&&b.setPointerCapture(e.pointerId);e.preventDefault();}; b.onclick=()=>{selectedCityPointId=id;renderCityMap();}; map.appendChild(b);
    };
    Object.entries(points).forEach(([id, point]) => marker(id, point));
    map.onpointermove=e=>{if(!dragging)return;const r=map.getBoundingClientRect(),x=Math.max(0,Math.min(100,(e.clientX-r.left)*100/r.width)),y=Math.max(0,Math.min(100,(e.clientY-r.top)*100/r.height));dragging.point.x=Math.round(x*100)/100;dragging.point.y=Math.round(y*100)/100;dragging.el.style.left=x+'%';dragging.el.style.top=y+'%';};
    map.onpointerup=map.onpointercancel=()=>dragging=null;
    root.querySelectorAll('[data-city]').forEach(b=>b.onclick=()=>{cityId=b.dataset.city;selectedCityPointId=null;renderCityMap();}); bindCityMode();
    root.querySelector('#citymap-add').onclick=()=>{let n=1,id;do{id='ponto_'+n++;}while(points[id]);points[id]={x:50,y:50,type:'mercador',name:'Novo ponto'};selectedCityPointId=id;renderCityMap();};
    const form=root.querySelector('#citymap-form');
    if(selected){ const typeOptions=Object.entries(types).map(([id,label])=>'<option value="'+id+'"'+((selected.type||selectedCityPointId)===id?' selected':'')+'>'+label+'</option>').join(''); form.innerHTML='<h3>Ponto</h3><label>Nome<input id="citymap-name" value="'+esc(selected.name||'')+'"></label><label>Emoji do marcador<input id="citymap-emoji" maxlength="8" value="'+esc(selected.emoji||'')+'"></label><label>Tipo / loja vinculada<select id="citymap-type">'+typeOptions+'</select></label><div class="worlded-cost"><label>X %<input id="citymap-x" type="number" min="0" max="100" step="0.1" value="'+Number(selected.x)+'"></label><label>Y %<input id="citymap-y" type="number" min="0" max="100" step="0.1" value="'+Number(selected.y)+'"></label></div>';
      const sync=()=>{selected.name=root.querySelector('#citymap-name').value;const emoji=root.querySelector('#citymap-emoji').value.trim();if(emoji)selected.emoji=emoji;else delete selected.emoji;selected.type=root.querySelector('#citymap-type').value;selected.x=Math.max(0,Math.min(100,Number(root.querySelector('#citymap-x').value)||0));selected.y=Math.max(0,Math.min(100,Number(root.querySelector('#citymap-y').value)||0));};form.querySelectorAll('input,select').forEach(el=>el.onchange=sync);
    } else form.innerHTML='<p>Crie ou selecione um ponto.</p>';
    root.querySelector('#citymap-delete').disabled=!selected;root.querySelector('#citymap-delete').onclick=()=>{if(selected){delete points[selectedCityPointId];selectedCityPointId=null;renderCityMap();}};
    root.querySelector('#cityed-save').onclick=saveAll;
    root.querySelector('#citymap-save').onclick=async()=>{
      const status=root.querySelector('#cityed-status'); status.textContent='Salvando mapa da cidade…';
      try { config=await window.EDITOR_SAVE.saveCityShops(config.stock, config.scenes, config.city_points); status.textContent='✓ Mapa salvo e atualizado no jogo.'; renderCityMap(); }
      catch(e){ status.textContent='Erro ao salvar o mapa: '+e.message; }
    };
  }
  // ─── Painel de cidades ─────────────────────────────────────────────────────
  // O editor manda sempre o conjunto completo (criadas, overrides, exclusões e
  // a tabela de rotas); o servidor substitui o estado por ele.
  const BUILTIN_IDS = ["alva_e_luz", "vila_riacho", "vila_corvin", "graciero"];
  function cityInicial() { return config.city_inicial || "alva_e_luz"; }
  function customIds() { return config.custom_cities || []; }
  function slugify(nome) {
    return String(nome || "").normalize("NFD").replace(new RegExp("[\\u0300-\\u036f]", "g"), "")   // tira acentos
      .toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 48);
  }
  function novoIdCidade(nome) {
    const base = slugify(nome) || "cidade";
    let id = base, n = 2;
    while ((config.cities || []).some(c => c.id === id)) id = base + "_" + n++;
    return id;
  }
  function rotaEntre(a, b) {
    return (config.routes || []).find(r => (r.from === a && r.to === b) || (r.from === b && r.to === a));
  }
  function setRota(a, b, fome, sede) {
    if (!Array.isArray(config.routes)) config.routes = [];
    const atual = rotaEntre(a, b);
    if (atual) { atual.fome = fome; atual.sede = sede; return; }
    config.routes.push({ from: a, to: b, fome: fome, sede: sede });
  }
  // Estado completo no formato que o servidor espera.
  function estadoCidades() {
    const custom = new Set(customIds());
    const cities = (config.cities || []).filter(c => custom.has(c.id))
      .map(c => ({ id: c.id, nome: c.nome, tipo: c.tipo || "cidade", imagem: c.imagem || "", x: Number(c.x) || 0, y: Number(c.y) || 0 }));
    const overrides = {};
    (config.cities || []).filter(c => !custom.has(c.id))
      .forEach(c => { overrides[c.id] = { nome: c.nome, tipo: c.tipo || "cidade", imagem: c.imagem || "" }; });
    const deleted = BUILTIN_IDS.filter(id => !(config.cities || []).some(c => c.id === id));
    return { cities: cities, overrides: overrides, deleted: deleted, routes: config.routes || [] };
  }
  async function salvarCidades() {
    const status = root.querySelector("#cityed-status");
    status.textContent = "Salvando cidades…";
    const estado = estadoCidades();
    try {
      config = await window.EDITOR_SAVE.saveWorldCities(estado.cities, estado.overrides, estado.deleted, estado.routes);
      cityDraft = null;
      if (!(config.cities || []).some(c => c.id === cityId)) cityId = (config.cities[0] || {}).id;
      render();
      root.querySelector("#cityed-status").textContent = "✓ Cidades salvas e aplicadas no jogo.";
    } catch (e) { status.textContent = "Erro ao salvar: " + e.message; }
  }
  function abrirDraft(id) {
    const existente = (config.cities || []).find(c => c.id === id);
    cityDraft = existente
      ? { novo: false, id: existente.id, nome: existente.nome, tipo: existente.tipo || "cidade", imagem: existente.imagem || "", x: Number(existente.x) || 50, y: Number(existente.y) || 50 }
      : { novo: true, id: "", nome: "", tipo: "cidade", imagem: "", x: 50, y: 50 };
    mode = "city"; render();
  }
  function aplicarDraft() {
    const status = root.querySelector("#cityed-status");
    if (!cityDraft.nome.trim()) { status.textContent = "Dê um nome à cidade."; return false; }
    if (cityDraft.novo) {
      cityDraft.id = novoIdCidade(cityDraft.nome);
      config.cities.push({ id: cityDraft.id, nome: cityDraft.nome, tipo: cityDraft.tipo, imagem: cityDraft.imagem, x: cityDraft.x, y: cityDraft.y, servicos: true });
      config.custom_cities = customIds().concat([cityDraft.id]);
      config.stock[cityDraft.id] = {};
      cityId = cityDraft.id;
    } else {
      const alvo = (config.cities || []).find(c => c.id === cityDraft.id);
      if (alvo) { alvo.nome = cityDraft.nome; alvo.tipo = cityDraft.tipo; alvo.imagem = cityDraft.imagem; alvo.x = cityDraft.x; alvo.y = cityDraft.y; }
    }
    return true;
  }
  function excluirCidade(id) {
    if (id === cityInicial()) return;
    if (!window.confirm("Excluir esta cidade? As lojas, os pontos do mapa e a taverna dela serão apagados.")) return;
    config.cities = (config.cities || []).filter(c => c.id !== id);
    config.custom_cities = customIds().filter(x => x !== id);
    config.routes = (config.routes || []).filter(r => r.from !== id && r.to !== id);
    if (cityId === id) cityId = (config.cities[0] || {}).id;
    cityDraft = null;
    salvarCidades();
  }
  function renderCidades() {
    const c = city(), inicial = cityInicial();
    const lista = '<div class="cityed-cities">' + (config.cities || []).map(x => '<button data-city="' + esc(x.id) + '" class="' + (x.id === cityId ? "active" : "") + '">' + esc(x.nome) + '<small>' + esc(x.tipo || "cidade") + '</small></button>').join("") + '</div>';
    let painel = '<p>Selecione uma cidade para editar, ou crie uma nova.</p>';
    if (cityDraft) {
      // As 4 cidades originais têm a posição no mapa-múndi em world_map_points.json
      // (arrastar o marcador na aba "Mapa do Mundo"); o painel não a edita.
      const posEditavel = cityDraft.novo || customIds().indexOf(cityDraft.id) >= 0;
      const outras = (config.cities || []).filter(x => x.id && x.id !== cityDraft.id);
      const rotas = outras.map(x => {
        const r = (!cityDraft.novo && rotaEntre(cityDraft.id, x.id)) || { fome: 0, sede: 0 };
        return '<div class="cityed-route"><span>' + esc(x.nome) + '</span><label>🍖<input type="number" min="0" data-route-fome="' + esc(x.id) + '" value="' + Number(r.fome || 0) + '"></label><label>💧<input type="number" min="0" data-route-sede="' + esc(x.id) + '" value="' + Number(r.sede || 0) + '"></label></div>';
      }).join("") || '<small>Nenhuma outra cidade cadastrada.</small>';
      painel = '<h3>' + (cityDraft.novo ? "Nova cidade" : "Editando " + esc(cityDraft.nome)) + '</h3>'
        + '<label>Nome<input id="cityed-nome" value="' + esc(cityDraft.nome) + '"></label>'
        + '<label>Tipo<select id="cityed-tipo"><option value="cidade"' + (cityDraft.tipo === "cidade" ? " selected" : "") + '>Cidade</option><option value="vila"' + (cityDraft.tipo === "vila" ? " selected" : "") + '>Vila</option></select></label>'
        + '<label>Imagem de fundo<input id="cityed-img-file" type="file" accept="image/png,image/jpeg,image/webp,image/gif"></label>'
        + '<button id="cityed-img-upload" type="button">Enviar imagem</button>'
        + (cityDraft.imagem ? '<img class="cityed-city-preview" src="../' + esc(cityDraft.imagem) + '" alt="Prévia da cidade">' : '<small>Nenhuma imagem enviada ainda.</small>')
        + (posEditavel
          ? '<div class="worlded-cost"><label>X %<input id="cityed-x" type="number" min="0" max="100" step="0.1" value="' + Number(cityDraft.x) + '"></label><label>Y %<input id="cityed-y" type="number" min="0" max="100" step="0.1" value="' + Number(cityDraft.y) + '"></label></div>'
            + '<p>Posição no mapa-múndi. O ajuste fino também pode ser feito arrastando o marcador na aba “Mapa do Mundo”.</p>'
          : '<p>A posição de <b>' + esc(cityDraft.nome) + '</b> no mapa-múndi é ajustada arrastando o marcador na aba “Mapa do Mundo”.</p>')
        + '<div class="cityed-routes"><b>Custo de viagem</b><small>Deixe 0 para viagem gratuita.</small>' + rotas + '</div>'
        + '<button id="cityed-city-save" type="button">Salvar cidade</button>'
        + (cityDraft.novo || cityDraft.id === inicial ? "" : '<button id="cityed-city-delete" type="button">Excluir cidade</button>');
    }
    root.innerHTML = '<div class="cityed"><header><div><h1>🏘️ Cidades</h1><p>Crie uma cidade nova, edite as existentes e defina os custos de viagem.</p></div><button id="cityed-city-new" type="button">+ Nova cidade</button></header>'
      + cityTabs() + lista
      + '<div class="cityed-layout"><aside><h2>' + esc(c.nome || "") + '</h2><button id="cityed-city-edit" type="button">✏️ Editar esta cidade</button></aside><section id="cityed-city-form">' + painel + '</section></div><div id="cityed-status"></div></div>';
    root.querySelectorAll("[data-city]").forEach(b => b.onclick = () => { cityId = b.dataset.city; cityDraft = null; render(); });
    bindCityMode();
    root.querySelector("#cityed-city-new").onclick = () => abrirDraft(null);
    root.querySelector("#cityed-city-edit").onclick = () => abrirDraft(cityId);
    if (!cityDraft) return;
    const campo = (sel, chave, numero) => {
      const el = root.querySelector(sel); if (!el) return;
      el.oninput = () => { cityDraft[chave] = numero ? Math.max(0, Math.min(100, Number(el.value) || 0)) : el.value; };
      el.onchange = el.oninput;
    };
    campo("#cityed-nome", "nome"); campo("#cityed-tipo", "tipo");
    // Só as cidades criadas pelo usuário têm x/y no payload; nas originais os campos nem existem.
    if (cityDraft.novo || customIds().indexOf(cityDraft.id) >= 0) { campo("#cityed-x", "x", true); campo("#cityed-y", "y", true); }
    root.querySelector("#cityed-img-upload").onclick = async () => {
      const status = root.querySelector("#cityed-status"), file = root.querySelector("#cityed-img-file").files[0];
      if (!file) { status.textContent = "Escolha uma imagem primeiro."; return; }
      status.textContent = "Enviando imagem…";
      try { cityDraft.imagem = await window.EDITOR_SAVE.uploadCityArt(file); render(); }
      catch (e) { status.textContent = "Erro ao enviar: " + e.message; }
    };
    root.querySelector("#cityed-city-save").onclick = () => {
      const alvo = cityDraft.novo ? null : cityDraft.id;
      if (!aplicarDraft()) return;
      const id = alvo || cityDraft.id;
      root.querySelectorAll("[data-route-fome]").forEach(input => {
        const outra = input.dataset.routeFome;
        const sede = root.querySelector('[data-route-sede="' + outra + '"]');
        setRota(id, outra, Math.max(0, Number(input.value) || 0), Math.max(0, Number(sede && sede.value) || 0));
      });
      salvarCidades();
    };
    const del = root.querySelector("#cityed-city-delete");
    if (del) del.onclick = () => excluirCidade(cityDraft.id);
  }
  function render() {
    if (!config) {
      root.innerHTML = '<div class="cityed"><h1>🏘️ Editor de Cidades</h1><p>Carregando lojas…</p></div>';
      ensure().then(render).catch(e => { root.innerHTML = '<div class="cityed"><h1>🏘️ Editor de Cidades</h1><p class="cityed-error">' + esc(e.message) + '</p></div>'; });
      return;
    }
    if (mode === "scenes") { renderScenes(); return; }
    if (mode === "map") { renderCityMap(); return; }
    if (mode === "city") { renderCidades(); return; }
    if (!STORES[storeId]) storeId = "ferreiro";
    const st = stock(), currentStore = store();
    if (!tabId || !currentStore.tabs.some(t => t[0] === tabId)) tabId = currentStore.tabs[0][0];
    const source = sourceForTab(), selected = new Set(st[source] || []), c = city();
    const storeRows = Object.keys(STORES).map(id => {
      const s = STORES[id], active = storeActive(id);
      const count = s.sources.reduce((n, key) => n + ((st[key] || []).length), 0);
      return '<label class="cityed-shop ' + (id === storeId ? 'selected' : '') + '"><input type="checkbox" data-toggle-store="' + id + '" ' + (active ? 'checked' : '') + '> <button data-store="' + id + '">' + s.label + '</button><small>' + (active ? count + ' itens' : 'não existe') + '</small></label>';
    }).join('');
    const tabs = currentStore.tabs.map(t => '<button class="cityed-subtab ' + (tabId === t[0] ? 'active' : '') + '" data-stock-tab="' + t[0] + '">' + esc(t[1]) + '</button>').join('');
    const itemRows = itemsForTab().map(item => '<label class="cityed-item"><input type="checkbox" data-item="' + esc(item.id) + '" ' + (selected.has(item.id) ? 'checked' : '') + '>' + esc(item.emoji || '📦') + ' <b>' + esc(item.name) + '</b><small>' + Number(item.price || 0) + ' ouro</small></label>').join('') || '<p>Nenhum item nesta categoria.</p>';
    root.innerHTML = '<div class="cityed"><header><div><h1>🏘️ Cidades e Lojas</h1><p>Defina os estabelecimentos de cada cidade e separe o estoque pelas abas da loja.</p></div><button id="cityed-save" class="cityed-save">Salvar alterações</button></header>' + cityTabs() +
      '<div class="cityed-cities">' + (config.cities || []).map(x => '<button data-city="' + esc(x.id) + '" class="' + (x.id === cityId ? 'active' : '') + '">' + esc(x.nome) + '<small>' + esc(x.tipo || 'cidade') + '</small></button>').join('') + '</div>' +
      '<div class="cityed-layout"><aside><h2>' + esc(c.nome || '') + '</h2><p>Marque quais estabelecimentos existem neste local.</p>' + storeRows + '</aside><section><h2>' + currentStore.label + '</h2><div class="cityed-subtabs">' + tabs + '</div><p>Itens vendidos nesta aba.</p><div class="cityed-items">' + itemRows + '</div></section></div><div id="cityed-status"></div></div>';
    root.querySelectorAll('[data-city]').forEach(b => b.onclick = () => { cityId = b.dataset.city; render(); });
    bindCityMode();
    root.querySelectorAll('[data-store]').forEach(b => b.onclick = () => { storeId = b.dataset.store; tabId = null; render(); });
    root.querySelectorAll('[data-stock-tab]').forEach(b => b.onclick = () => { tabId = b.dataset.stockTab; render(); });
    root.querySelectorAll('[data-toggle-store]').forEach(input => input.onchange = () => {
      const id = input.dataset.toggleStore, s = STORES[id];
      if (input.checked) s.sources.forEach(key => { if (!Array.isArray(st[key])) st[key] = []; });
      else s.sources.forEach(key => delete st[key]);
      storeId = id; tabId = null; render();
    });
    root.querySelectorAll('[data-item]').forEach(input => input.onchange = () => {
      if (!Array.isArray(st[source])) st[source] = [];
      const id = input.dataset.item;
      if (input.checked && !st[source].includes(id)) st[source].push(id);
      if (!input.checked) st[source] = st[source].filter(x => x !== id);
      render();
    });
    root.querySelector('#cityed-save').textContent = 'Salvar lojas desta cidade';
    root.querySelector('#cityed-save').onclick = saveAll;
  }
  window.EDITOR_CITY = { render: render };
})();
