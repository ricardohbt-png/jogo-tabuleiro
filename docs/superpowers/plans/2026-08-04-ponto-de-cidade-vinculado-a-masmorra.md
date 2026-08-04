# Ponto da cidade vinculado a uma masmorra — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que um ponto da ilustração da cidade seja uma entrada de masmorra vinculada a um destino do mapa-múndi, criada por um botão próprio no editor (separado do botão de loja/local).

**Architecture:** O ponto ganha o campo `aventura` (id de `WORLD_ADVENTURES`) sobre o `type:"dungeon"` que já existe na allow-list do servidor. Nenhuma mensagem WebSocket nova: a confirmação envia `world_adventure`, o mesmo handler do mapa-múndi, que já cobre requisito, custo 🍖/💧, etapa encadeada, revisita, história e trava de anfitrião. O servidor filtra do payload os pontos cujo destino não é visível para a sala; o cliente extrai o painel do mapa-múndi para uma função compartilhada e o reusa num quadro de confirmação na cidade; o editor ganha um segundo botão de adicionar e um formulário próprio para o tipo `dungeon`.

**Tech Stack:** Python 3 + `websockets` (server.py, arquivo único autoritativo), JavaScript vanilla sem bundler (`game.js`, `tools/editor_city.js`), CSS puro (`game.css`), testes em script Python solto (`tools/test_*.py`, rodados da raiz) e `node --check` para sintaxe do cliente.

**Spec:** `docs/superpowers/specs/2026-08-04-ponto-de-cidade-vinculado-a-masmorra-design.md`

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta feature |
|---|---|
| `server.py` | Validar/preservar `aventura` no save do editor e no boot; `_city_points_payload` (filtro de spoiler); `adventures` no payload do editor |
| `game.js` | `_adventureInfo`/`_adventureGoButton` compartilhados; ramo `dungeon` em `pointAllowed` e `_cityHotspotClick`; quadro de confirmação `abrirEntradaMasmorra` |
| `game.css` | Estilo do quadro de confirmação `#city-dungeon-entry` |
| `tools/editor_city.js` | Segundo botão de adicionar + formulário do ponto de masmorra |
| `tools/test_cidades_editor.py` | Seções `[13]`–`[15]`: persistência do vínculo, filtro de payload, payload do editor |

Nenhum arquivo novo. O projeto concentra a lógica em `server.py` e a renderização em `game.js` por decisão de arquitetura (CLAUDE.md) — seguir esse padrão, não criar módulos novos.

---

## Task 1: Persistir o vínculo `aventura` no ponto

**Files:**
- Modify: `server.py` — `_load_city_map_points` (≈ linhas 394-410) e `_save_city_shops_upload` (≈ linhas 26018-26034)
- Test: `tools/test_cidades_editor.py` (seção nova `[13]`, inserir logo depois do bloco `[12]`, antes de `print("\n[11] Regressões apontadas na revisão")`)

- [ ] **Step 1: Escrever o teste que falha**

Inserir em `tools/test_cidades_editor.py`, imediatamente antes da linha `print("\n[11] Regressões apontadas na revisão")`:

```python
    print("\n[13] Ponto de masmorra vinculado a um destino")
    reset_mundo()
    S.WORLD_ADVENTURES["destino_teste"] = {
        "id": "destino_teste", "nome": "Cripta de Teste", "x": 50.0, "y": 50.0,
        "fome": 2, "sede": 2, "dungeons": [{"file": "a.json"}],
        "oculto_ate_liberar": False, "revisitavel": False,
        "requisito": {"renome_min": 0, "nivel_grupo_min": 0, "item_id": "",
                      "fato": "", "aventura_id": ""},
    }
    try:
        enviados = {"alva_e_luz": {
            "cripta": {"x": 40.0, "y": 55.0, "type": "dungeon", "name": "Cripta",
                       "emoji": "🚪", "aventura": "destino_teste"},
            "fantasma": {"x": 10.0, "y": 10.0, "type": "dungeon", "name": "Sem destino",
                         "aventura": "nao_existe"},
        }}
        ok_save, _ = S._save_city_shops_upload({}, None, enviados)
        salvos = S.CITY_MAP_POINTS["alva_e_luz"]
        check("save do editor aceito", ok_save is True)
        check("tipo dungeon preservado", salvos["cripta"].get("type") == "dungeon")
        check("vínculo válido preservado", salvos["cripta"].get("aventura") == "destino_teste")
        check("emoji do ponto preservado", salvos["cripta"].get("emoji") == "🚪")
        check("vínculo inexistente é descartado", "aventura" not in salvos["fantasma"])
        check("ponto sem vínculo continua salvo", "fantasma" in salvos)
        # Round-trip pelo arquivo: o vínculo tem de sobreviver ao boot.
        S._save_city_map_points()
        S.CITY_MAP_POINTS["alva_e_luz"].pop("cripta")
        S._load_city_map_points()
        check("vínculo sobrevive ao boot",
              S.CITY_MAP_POINTS["alva_e_luz"].get("cripta", {}).get("aventura") == "destino_teste")
        # O boot só checa FORMATO: sem WORLD_ADVENTURES carregado (arquivo ausente
        # ou corrompido) o vínculo não pode ser apagado da memória, senão o próximo
        # save do editor gravaria a perda em disco.
        guardado = dict(S.WORLD_ADVENTURES)
        S.WORLD_ADVENTURES.clear()
        S.CITY_MAP_POINTS["alva_e_luz"].pop("cripta")
        S._load_city_map_points()
        check("boot sem catálogo de destinos não apaga o vínculo",
              S.CITY_MAP_POINTS["alva_e_luz"].get("cripta", {}).get("aventura") == "destino_teste")
        S.WORLD_ADVENTURES.update(guardado)
    finally:
        S.WORLD_ADVENTURES.pop("destino_teste", None)
    reset_mundo()
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
python tools/test_cidades_editor.py
```

Esperado: a seção `[13]` aparece com ❌ em "vínculo válido preservado", "vínculo sobrevive ao boot" e "boot sem catálogo…" (o campo `aventura` é descartado hoje), e o resumo final termina com falhas. As seções anteriores continuam ✅.

- [ ] **Step 3: Preservar o vínculo no save do editor**

Em `server.py`, dentro de `_save_city_shops_upload`, logo depois do bloco do `scene_ref` (`if scene_ref and scene_ref in CITY_SCENES.get(city_id, {}): item["scene"] = scene_ref`) e antes de `cleaned[point_id] = item`:

```python
                # Vínculo do ponto de masmorra. A existência do destino é checada
                # AQUI (o autor está no editor e vê o resultado); um id que não
                # existe mais perde só o campo, o ponto continua salvo.
                aventura_ref = str(point.get("aventura") or "").strip()
                if aventura_ref in WORLD_ADVENTURES:
                    item["aventura"] = aventura_ref
```

- [ ] **Step 4: Preservar o vínculo no boot**

Em `server.py`, dentro de `_load_city_map_points`, logo depois do bloco do `scene_ref` e antes de `CITY_MAP_POINTS[city_id][point_id] = item`:

```python
                    # Só formato, como o `scene` acima: se WORLD_ADVENTURES ainda
                    # não estiver carregado (ou o arquivo estiver corrompido), uma
                    # checagem de existência aqui apagaria todos os vínculos da
                    # memória — e o próximo save do editor gravaria a perda.
                    aventura_ref = str(point.get("aventura") or "").strip()
                    if re.fullmatch(r"[a-z0-9_-]{1,64}", aventura_ref):
                        item["aventura"] = aventura_ref
```

- [ ] **Step 5: Rodar o teste e ver passar**

```bash
python tools/test_cidades_editor.py
```

Esperado: seção `[13]` toda ✅ e `RESULTADO: N passaram, 0 falharam`.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_cidades_editor.py
git commit -m "feat(cidades): ponto do mapa guarda o vinculo com um destino de masmorra"
```

---

## Task 2: Filtrar do payload os pontos de destino não visível

O payload de cidade manda `CITY_MAP_POINTS` inteiro (todas as cidades). Um destino marcado como oculto não pode ter nem seu id vazado — mesma regra que já vale para `world.adventures`.

**Files:**
- Modify: `server.py` — método novo `_city_points_payload` na classe `GameRoom` (colocar junto de `_aventura_visivel`, ≈ linha 9110) e a linha `"city_map_points": CITY_MAP_POINTS,` em `_city_state_payload` (≈ linha 7087)
- Test: `tools/test_cidades_editor.py` (seção nova `[14]`, logo após a `[13]`)

- [ ] **Step 1: Escrever o teste que falha**

Inserir em `tools/test_cidades_editor.py` logo depois do bloco `[13]`:

```python
    print("\n[14] Destino oculto não vaza no payload da cidade")
    reset_mundo()
    base_req = {"renome_min": 0, "nivel_grupo_min": 0, "item_id": "", "fato": "", "aventura_id": ""}
    S.WORLD_ADVENTURES["oculto_teste"] = {
        "id": "oculto_teste", "nome": "Cripta Secreta", "x": 10.0, "y": 10.0,
        "fome": 0, "sede": 0, "dungeons": [{"file": "a.json"}],
        "oculto_ate_liberar": True, "revisitavel": False,
        "requisito": dict(base_req, renome_min=50)}
    S.WORLD_ADVENTURES["bloqueado_teste"] = {
        "id": "bloqueado_teste", "nome": "Torre Fechada", "x": 20.0, "y": 20.0,
        "fome": 0, "sede": 0, "dungeons": [{"file": "a.json"}],
        "oculto_ate_liberar": False, "revisitavel": False,
        "requisito": dict(base_req, renome_min=50)}
    try:
        pontos_cidade = S.CITY_MAP_POINTS["alva_e_luz"]
        pontos_cidade["cripta_secreta"] = {"x": 40.0, "y": 55.0, "type": "dungeon",
                                           "aventura": "oculto_teste"}
        pontos_cidade["torre"] = {"x": 45.0, "y": 55.0, "type": "dungeon",
                                  "aventura": "bloqueado_teste"}
        pontos_cidade["solto"] = {"x": 46.0, "y": 56.0, "type": "dungeon"}
        sala = S.GameRoom("PAYLOAD")
        sala.phase = "city"; sala.world_location = "alva_e_luz"; sala.renome = 0
        visiveis = sala._city_points_payload()["alva_e_luz"]
        check("ponto de destino oculto some do payload", "cripta_secreta" not in visiveis)
        check("ponto de destino bloqueado (visível) permanece", "torre" in visiveis)
        check("ponto de masmorra sem vínculo some do payload", "solto" not in visiveis)
        check("ponto de loja não é afetado", "mercador" in visiveis)
        sala.renome = 99
        check("ponto aparece quando o requisito é cumprido",
              "cripta_secreta" in sala._city_points_payload()["alva_e_luz"])
        check("dicionário global não é mutado",
              "cripta_secreta" in S.CITY_MAP_POINTS["alva_e_luz"])
        check("outras cidades continuam no payload",
              "vila_riacho" in sala._city_points_payload())
    finally:
        S.WORLD_ADVENTURES.pop("oculto_teste", None)
        S.WORLD_ADVENTURES.pop("bloqueado_teste", None)
    reset_mundo()
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
python tools/test_cidades_editor.py
```

Esperado: erro `AttributeError: 'GameRoom' object has no attribute '_city_points_payload'` interrompendo a seção `[14]` (o método ainda não existe).

- [ ] **Step 3: Implementar o filtro**

Em `server.py`, na classe `GameRoom`, logo depois do método `_aventura_visivel`:

```python
    def _city_points_payload(self):
        """Cópia de CITY_MAP_POINTS sem os pontos de masmorra cujo destino não
        está visível para esta sala. `city_map_points` vai inteiro no payload,
        então sem isto o id de um destino oculto viajaria até o cliente — e o
        ponto de um destino que não existe mais viraria um marcador morto."""
        saida = {}
        for city_id, pontos in CITY_MAP_POINTS.items():
            limpos = {}
            for point_id, ponto in pontos.items():
                if str(ponto.get("type") or "") == "dungeon":
                    adventure = WORLD_ADVENTURES.get(str(ponto.get("aventura") or ""))
                    if not adventure or not self._aventura_visivel(adventure):
                        continue
                limpos[point_id] = ponto
            saida[city_id] = limpos
        return saida
```

- [ ] **Step 4: Usar o filtro no payload de cidade**

Em `server.py`, dentro de `_city_state_payload`, trocar

```python
            "city_map_points": CITY_MAP_POINTS,
```

por

```python
            "city_map_points": self._city_points_payload(),
```

Este é o **único** lugar que serializa `CITY_MAP_POINTS` para o cliente (confirmado por busca); o payload do editor (`_city_shops_editor_payload`) segue sem filtro de propósito — o autor precisa enxergar o que criou.

- [ ] **Step 5: Rodar o teste e ver passar**

```bash
python tools/test_cidades_editor.py
```

Esperado: seções `[13]` e `[14]` todas ✅ e `RESULTADO: N passaram, 0 falharam`.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_cidades_editor.py
git commit -m "feat(cidades): payload esconde ponto de masmorra de destino oculto"
```

---

## Task 3: Mandar os destinos ao editor de cidades

A aba de cidades não conhece as aventuras hoje (só a aba do mapa-múndi as carrega). O `<select>` de destino precisa delas.

**Files:**
- Modify: `server.py` — `_city_shops_editor_payload` (≈ linhas 25981-25985)
- Test: `tools/test_cidades_editor.py` (seção nova `[15]`, logo após a `[14]`)

- [ ] **Step 1: Escrever o teste que falha**

Inserir em `tools/test_cidades_editor.py` logo depois do bloco `[14]`:

```python
    print("\n[15] Editor recebe os destinos para vincular")
    reset_mundo()
    S.WORLD_ADVENTURES["destino_editor"] = {
        "id": "destino_editor", "nome": "Cripta do Editor", "x": 1.0, "y": 1.0,
        "fome": 0, "sede": 0, "dungeons": [{"file": "a.json"}, {"file": "b.json"}],
        "oculto_ate_liberar": True, "revisitavel": False,
        "requisito": {"renome_min": 99, "nivel_grupo_min": 0, "item_id": "",
                      "fato": "", "aventura_id": ""}}
    S.WORLD_ADVENTURES["destino_vazio"] = {
        "id": "destino_vazio", "nome": "Rascunho", "x": 2.0, "y": 2.0,
        "fome": 0, "sede": 0, "dungeons": [], "oculto_ate_liberar": False,
        "revisitavel": False, "requisito": {}}
    try:
        payload = S._city_shops_editor_payload()
        destinos = {a["id"]: a for a in payload.get("adventures", [])}
        check("destino chega ao editor", "destino_editor" in destinos)
        check("nome do destino", destinos.get("destino_editor", {}).get("nome") == "Cripta do Editor")
        check("nº de masmorras do destino", destinos.get("destino_editor", {}).get("dungeons") == 2)
        # Sem filtro: o autor precisa ver inclusive o oculto e o rascunho sem masmorra.
        check("destino oculto aparece para o autor", "destino_editor" in destinos)
        check("destino sem masmorra aparece com contagem 0",
              destinos.get("destino_vazio", {}).get("dungeons") == 0)
    finally:
        S.WORLD_ADVENTURES.pop("destino_editor", None)
        S.WORLD_ADVENTURES.pop("destino_vazio", None)
    reset_mundo()
```

- [ ] **Step 2: Rodar o teste e ver falhar**

```bash
python tools/test_cidades_editor.py
```

Esperado: seção `[15]` com ❌ em "destino chega ao editor", "nome do destino", "nº de masmorras do destino" e "destino sem masmorra…" (a chave `adventures` não existe no payload).

- [ ] **Step 3: Implementar**

Em `server.py`, em `_city_shops_editor_payload`, trocar o `return` por:

```python
    return {"cities": list(WORLD_LOCATIONS.values()), "shops": CITY_SHOP_LABELS,
            "stock": CITY_SHOPS, "catalog": catalog, "scenes": CITY_SCENES,
            "city_points": CITY_MAP_POINTS, "routes": rotas,
            # Lista enxuta para o <select> de destino do ponto de masmorra. NÃO
            # filtra ocultos: no editor o autor precisa ver o que criou.
            "adventures": [{"id": a["id"], "nome": a.get("nome", a["id"]),
                            "dungeons": len(a.get("dungeons") or [])}
                           for a in WORLD_ADVENTURES.values()],
            "custom_cities": [c["id"] for c in WORLD_CITIES.get("cities", [])],
            "city_inicial": CITY_INICIAL}
```

- [ ] **Step 4: Rodar o teste e ver passar**

```bash
python tools/test_cidades_editor.py
```

Esperado: `[13]`, `[14]` e `[15]` todas ✅ e `RESULTADO: N passaram, 0 falharam`.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_cidades_editor.py
git commit -m "feat(editor): payload de cidades traz a lista de destinos de masmorra"
```

---

## Task 4: Extrair o painel do destino em `game.js`

O quadro de confirmação da cidade mostra exatamente as mesmas regras (custo, etapa, requisito, rota concluída, trava de anfitrião) do painel do mapa-múndi. Extrair antes de reusar, para as duas telas não saírem de sincronia.

**Files:**
- Modify: `game.js` — `showWorldAdventurePreview` (≈ linhas 1698-1725)

- [ ] **Step 1: Criar as duas funções compartilhadas**

Em `game.js`, imediatamente **antes** de `function showWorldAdventurePreview(world, adventure){`:

```js
// Regras de exibição de um destino de masmorra — compartilhadas pelo painel do
// mapa-múndi e pelo quadro da entrada colocada na ilustração da cidade. As duas
// telas leem daqui para nunca divergirem em custo/etapa/requisito.
function _adventureInfo(adventure){
  const count = (adventure.dungeons || []).length;
  const progress = Math.max(0, Number(adventure.progresso || 0));
  const completed = count > 0 && progress >= count;
  const req = adventure.requisito || {};
  const reqText = [Number(req.renome_min)>0 ? 'renome '+req.renome_min : '', Number(req.nivel_grupo_min)>0 ? 'nível de grupo '+req.nivel_grupo_min : '', req.item_id ? 'item: '+req.item_id : '', req.fato ? 'informação: '+req.fato : '', req.aventura_id ? 'rota concluída: '+req.aventura_id : ''].filter(Boolean);
  const html = completed
    ? `<b>Rota concluída</b><small>O grupo já concluiu as ${count} masmorras deste destino.</small>`
    : `<b>Entrada de masmorra</b><small>Expedição: 🍖 -${adventure.fome || 0} e 💧 -${adventure.sede || 0} para cada herói.${count > 1 ? ' Próxima etapa: ' + (progress + 1) + ' de ' + count + '. As demais liberam após concluir a anterior.' : ''}${reqText.length ? ' Requisito: ' + reqText.join(' · ') + '.' : ''}</small>`;
  return {count, progress, completed, html};
}

function _adventureGoButton(adventure){
  const go = document.createElement('button');
  go.className = 'worldmap-travel';
  go.textContent = 'Entrar em ' + adventure.nome;
  go.disabled = GS.myPid !== GS.cityState.host;
  go.title = go.disabled ? 'Apenas o anfitrião inicia a expedição.' : '';
  go.onclick = () => {
    go.disabled = true; go.textContent = 'Iniciando expedição…';
    GS.worldAdventure(adventure.id);
  };
  return go;
}
```

- [ ] **Step 2: Fazer o painel do mapa-múndi usar as funções**

Em `game.js`, dentro de `showWorldAdventurePreview`, substituir o trecho que vai de `const count = (adventure.dungeons || []).length;` até o fechamento do `if(!completed){ … }` (inclusive) por:

```js
  const info = _adventureInfo(adventure);
  panel.innerHTML = info.html;
  if(!info.completed) panel.appendChild(_adventureGoButton(adventure));
```

As linhas seguintes (`frame.appendChild(panel); _worldMapEl.appendChild(frame);`) ficam como estão.

- [ ] **Step 3: Conferir sintaxe**

```bash
node --check game.js
```

Esperado: nenhuma saída (sucesso).

- [ ] **Step 4: Conferir que não sobrou o código antigo**

```bash
grep -n "Rota concluída" game.js
```

Esperado: **uma** ocorrência só, dentro de `_adventureInfo`.

- [ ] **Step 5: Commit**

```bash
git add game.js
git commit -m "refactor(cidade): extrai o painel de destino de masmorra para reuso"
```

---

## Task 5: Marcador e quadro de confirmação na cidade

**Files:**
- Modify: `game.js` — `pointAllowed` (≈ linhas 1549-1552), `_cityHotspotClick` (≈ linhas 1497-1507) e função nova `abrirEntradaMasmorra`
- Modify: `game.css` — bloco novo no fim do arquivo

- [ ] **Step 1: Ensinar `pointAllowed` a aceitar o ponto de masmorra**

Em `game.js`, dentro de `_refreshCityLocation`, substituir o bloco:

```js
  const pointAllowed = (type, point) => type === 'caravana' || type === 'guilda' || type === 'dungeon'
    || (type === 'cena'
      ? !!(point && point.scene && cityScenes[point.scene])
      : (isAlva || hasShopPoint(type)));
```

por:

```js
  // O ponto de masmorra depende do destino vinculado — o servidor já omite do
  // payload o destino oculto/inexistente, então aqui é só a checagem final.
  const worldAdventures = (world.adventures || []);
  const pointAllowed = (type, point) => type === 'caravana' || type === 'guilda'
    || (type === 'dungeon'
      ? !!(point && point.aventura && worldAdventures.some(a => a.id === point.aventura))
      : type === 'cena'
        ? !!(point && point.scene && cityScenes[point.scene])
        : (isAlva || hasShopPoint(type)));
```

- [ ] **Step 2: Trocar o destino do clique e abrir o quadro**

Em `game.js`, substituir a linha do ramo de masmorra em `_cityHotspotClick`:

```js
  if(t === 'dungeon'){ triggerDungeonEntrance(); return; }
```

por:

```js
  if(t === 'dungeon'){
    const st = GS.cityState;
    const loc = st && st.world && st.world.location;
    const ponto = ((st && st.city_map_points || {})[loc] || {})[pointId];
    const adventure = (((st && st.world && st.world.adventures) || [])
      .find(a => ponto && a.id === ponto.aventura));
    if(!adventure){ toast('⚠ Esta entrada não está vinculada a nenhum destino.','var(--red)'); return; }
    abrirEntradaMasmorra(adventure, (ponto && ponto.name) || adventure.nome);
    return;
  }
```

`triggerDungeonEntrance()` fica no arquivo, intocada — continua servindo o botão legado "⚔ Entrar na Masmorra".

- [ ] **Step 3: Escrever o quadro de confirmação**

Em `game.js`, logo depois de `_cityHotspotClick`:

```js
// Quadro de confirmação da entrada de masmorra colocada na ilustração da cidade.
// Mostra o mesmo conteúdo do painel do mapa-múndi (custo, etapa, requisito) sem
// precisar abrir o mapa; o "Entrar" é o mesmo botão, restrito ao anfitrião.
function abrirEntradaMasmorra(adventure, titulo){
  document.getElementById('city-dungeon-entry')?.remove();
  const info = _adventureInfo(adventure);
  const wrap = document.createElement('div'); wrap.id = 'city-dungeon-entry';
  const box = document.createElement('div'); box.className = 'cde-box';
  const h = document.createElement('h3'); h.textContent = '🚪 ' + (titulo || adventure.nome);
  box.appendChild(h);
  const panel = document.createElement('div'); panel.className = 'worldmap-location-info';
  panel.innerHTML = info.html;
  if(!info.completed) panel.appendChild(_adventureGoButton(adventure));
  box.appendChild(panel);
  const back = document.createElement('button'); back.className = 'btn-cancel';
  back.textContent = '← Voltar'; back.onclick = () => wrap.remove();
  box.appendChild(back);
  wrap.appendChild(box);
  wrap.addEventListener('click', e => { if(e.target === wrap) wrap.remove(); });
  document.body.appendChild(wrap);
}
```

- [ ] **Step 4: Estilizar o quadro**

Acrescentar ao fim de `game.css`:

```css
/* Entrada de masmorra colocada na ilustração da cidade */
#city-dungeon-entry{position:fixed;inset:0;z-index:60;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.62)}
#city-dungeon-entry .cde-box{width:min(92vw,420px);padding:18px 20px;border-radius:14px;text-align:center;background:rgba(18,14,10,.96);border:1px solid rgba(var(--gold-rgb),.5);box-shadow:0 18px 48px rgba(0,0,0,.6)}
#city-dungeon-entry h3{margin:0 0 12px;color:var(--gold)}
#city-dungeon-entry .btn-cancel{margin-top:12px}
```

- [ ] **Step 5: Conferir sintaxe**

```bash
node --check game.js
```

Esperado: nenhuma saída (sucesso).

- [ ] **Step 6: Commit**

```bash
git add game.js game.css
git commit -m "feat(cidade): entrada de masmorra na ilustracao com quadro de confirmacao"
```

---

## Task 6: Dois botões e o formulário no editor de cidades

**Files:**
- Modify: `tools/editor_city.js` — `renderCityMap` (≈ linhas 313-344)

- [ ] **Step 1: Rotular o marcador de masmorra e criar o segundo botão**

Em `tools/editor_city.js`, em `renderCityMap`, trocar a linha do mapa `types` por:

```js
    const types = {ferreiro:'Ferreiro', mercador:'Mercador', templo:'Templo', taverna:'Taverna', guilda:'Guilda', caravana:'Caravana de Viagem', cena:'Local de conversa'};
    // `dungeon` NÃO entra no dropdown: o tipo só se obtém pelo botão dedicado,
    // que é o que mantém as duas opções de criação realmente separadas.
    const rotulos = Object.assign({dungeon:'Entrada de masmorra'}, types);
    const adventures = config.adventures || [];
```

e, na linha do `marker`, trocar `types[type]` por `rotulos[type]`:

```js
      const type = point.type || id, name = point.name || rotulos[type] || id;
```

Na string do `root.innerHTML`, trocar

```js
<button id="citymap-add" type="button">+ Adicionar ponto</button>
```

por

```js
<button id="citymap-add" type="button">+ Adicionar ponto (loja/local)</button><button id="citymap-add-dungeon" type="button">+ Adicionar entrada de masmorra</button>
```

- [ ] **Step 2: Ligar o botão novo**

Logo depois da linha que liga `#citymap-add`, acrescentar:

```js
    root.querySelector('#citymap-add-dungeon').onclick=()=>{let n=1,id;do{id='masmorra_'+n++;}while(points[id]);points[id]={x:50,y:50,type:'dungeon',name:'Entrada de masmorra',emoji:'🚪'};selectedCityPointId=id;renderCityMap();};
```

- [ ] **Step 3: Formulário por tipo**

Substituir o bloco `if(selected){ … }` (a montagem do `form.innerHTML` e o `sync`) por:

```js
    if(selected){
      const isDungeon = (selected.type || selectedCityPointId) === 'dungeon';
      let campo;
      if(isDungeon){
        const escolhido = adventures.find(a => a.id === selected.aventura);
        const opts = ['<option value="">— nenhum destino —</option>'].concat(adventures.map(a =>
          '<option value="'+esc(a.id)+'"'+(selected.aventura===a.id?' selected':'')+'>'+esc(a.nome||a.id)+(a.dungeons?'':' (sem masmorra)')+'</option>')).join('');
        const aviso = !selected.aventura
          ? '<small class="cityed-warn">⚠ Sem destino vinculado: o marcador não aparece no jogo.</small>'
          : !escolhido
            ? '<small class="cityed-warn">⚠ O destino vinculado não existe mais.</small>'
            : !escolhido.dungeons
              ? '<small class="cityed-warn">⚠ Este destino ainda não tem masmorra.</small>' : '';
        campo = '<label>Destino vinculado<select id="citymap-aventura">'+opts+'</select></label>'+aviso;
      } else {
        const typeOptions=Object.entries(types).map(([id,label])=>'<option value="'+id+'"'+((selected.type||selectedCityPointId)===id?' selected':'')+'>'+label+'</option>').join('');
        campo = '<label>Tipo / loja vinculada<select id="citymap-type">'+typeOptions+'</select></label>';
      }
      form.innerHTML='<h3>'+(isDungeon?'Entrada de masmorra':'Ponto')+'</h3><label>Nome<input id="citymap-name" value="'+esc(selected.name||'')+'"></label><label>Emoji do marcador<input id="citymap-emoji" maxlength="8" value="'+esc(selected.emoji||'')+'"></label>'+campo+'<div class="worlded-cost"><label>X %<input id="citymap-x" type="number" min="0" max="100" step="0.1" value="'+Number(selected.x)+'"></label><label>Y %<input id="citymap-y" type="number" min="0" max="100" step="0.1" value="'+Number(selected.y)+'"></label></div>';
      const sync=()=>{
        selected.name=root.querySelector('#citymap-name').value;
        const emoji=root.querySelector('#citymap-emoji').value.trim();
        if(emoji)selected.emoji=emoji;else delete selected.emoji;
        if(isDungeon){
          const dest=root.querySelector('#citymap-aventura').value;
          selected.type='dungeon';
          if(dest)selected.aventura=dest;else delete selected.aventura;
        } else {
          selected.type=root.querySelector('#citymap-type').value;
          delete selected.aventura;
        }
        selected.x=Math.max(0,Math.min(100,Number(root.querySelector('#citymap-x').value)||0));
        selected.y=Math.max(0,Math.min(100,Number(root.querySelector('#citymap-y').value)||0));
      };
      form.querySelectorAll('input,select').forEach(el=>el.onchange=sync);
      root.querySelector('#citymap-aventura') && (root.querySelector('#citymap-aventura').onchange=()=>{sync();renderCityMap();});
    } else form.innerHTML='<p>Crie ou selecione um ponto.</p>';
```

O `onchange` extra do `<select>` de destino re-renderiza o painel para o aviso acompanhar a escolha na hora (mesmo padrão do `ie-manejo` no Editor de Itens).

- [ ] **Step 4: Estilo do aviso**

Acrescentar ao fim de `tools/editor.css` (é o único stylesheet do editor, carregado na linha 7 de `tools/editor.html`), junto das demais regras `.cityed-*`:

```css
.cityed-warn{display:block;margin:-4px 0 8px;color:#e8b34a;font-size:11px}
```

- [ ] **Step 5: Conferir sintaxe**

```bash
node --check tools/editor_city.js
```

Esperado: nenhuma saída (sucesso).

- [ ] **Step 6: Commit**

```bash
git add tools/editor_city.js tools/editor.css
git commit -m "feat(editor): botao proprio para criar entrada de masmorra na cidade"
```

---

## Task 7: Verificação final

- [ ] **Step 1: Rodar as suítes que tocam cidades/pontos/aventuras**

```bash
python tools/test_cidades_editor.py
```

```bash
python tools/test_cenas_conversa.py
```

```bash
python tools/test_masmorra_sequenciada.py
```

Esperado: `0 falharam` nas três. Se alguma falha aparecer em teste **não** relacionado a esta feature, conferir se já falhava antes das mudanças (`git stash` + rodar + `git stash pop`) antes de tratar como regressão — há falhas pré-existentes conhecidas no repositório.

- [ ] **Step 2: Sintaxe do cliente e do editor**

```bash
node --check game.js && node --check tools/editor_city.js && echo OK
```

Esperado: `OK`.

- [ ] **Step 3: Smoke test in-app**

Subir o servidor (`iniciar.bat` ou `python server.py`) e, no editor (`tools/editor.html`, aba 🏘️ Cidades → mapa da cidade):

1. Clicar em `+ Adicionar entrada de masmorra`, escolher um destino existente, arrastar o marcador e salvar.
2. No jogo, entrar numa sala, chegar à cidade e conferir: o marcador 🚪 aparece na ilustração, o clique abre o quadro com custo/etapa/requisito, o botão "Entrar" está desabilitado para quem não é anfitrião e a expedição começa ao confirmar.
3. Marcar o destino como oculto no editor de mapa-múndi, sem cumprir o requisito, e conferir que o marcador some da cidade.

- [ ] **Step 4: Atualizar o CLAUDE.md**

Acrescentar um parágrafo ao `CLAUDE.md` (bloco de notas de arquitetura, junto do parágrafo dos pontos da ilustração da cidade) resumindo: ponto `type:"dungeon"` + campo `aventura`; entrada reusa `world_adventure`; `_city_points_payload` filtra destino não visível; editor tem botão próprio; teste `tools/test_cidades_editor.py` seções [13]-[15].

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: ponto de cidade vinculado a masmorra no CLAUDE.md"
```
