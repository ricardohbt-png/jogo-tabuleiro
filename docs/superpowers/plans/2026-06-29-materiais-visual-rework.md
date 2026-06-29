# Materiais — rework visual + UX do editor — Plano

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Fazer grama/terra parecerem grama/terra de verdade, paredes de caverna com pedra irregular e enegrecida com tijolo preto — no 2D e no 3D — e dobrar a escolha de material nas ferramentas chão/parede do editor (removendo a ferramenta "material").

**Architecture:** Client-only. Painters procedurais genéricos `paint*(ctx, ox, oy, size, r)` compartilhados pelo 2D (tile de `CELL`) e pelo 3D (textura de canvas cacheada). Sem assets, sem mudanças no servidor/protocolo/ids.

**Tech Stack:** Vanilla JS, Canvas 2D, Three.js r128 (`CanvasTexture`).

**Spec:** `docs/superpowers/specs/2026-06-29-materiais-visual-rework-design.md`

**Verificação:** não há teste unitário de aparência — a verificação é visual (preview: showcase em canvas + screenshot + amostragem de pixels) e funcional (editor no navegador). `python tools/test_materiais.py` deve seguir 40/40 (nada de servidor muda).

---

## Task 1: Painters procedurais genéricos + RNG (game.js)

**Files:** Modify `game.js` — inserir logo antes de `const MAT_PALETTE_2D = {` (linha ~5259).

- [ ] **Step 1: Inserir o RNG e os painters**

```js
// ── PAINTERS PROCEDURAIS DE MATERIAL (compartilhados 2D tile + 3D textura) ────
// Cada painter desenha UMA superfície preenchendo [ox,oy, ox+size, oy+size].
// r = função RNG determinística (0..1). Usados pelo 2D (size=CELL) e pelo 3D
// (size=256, textura cacheada) para a aparência ser idêntica nas duas vistas.
function _rng(seed){ let s=(seed>>>0)||1; return function(){ s=(s*1664525+1013904223)>>>0; return s/4294967296; }; }

function paintGrass(ctx, ox, oy, size, r){
  const g=ctx.createLinearGradient(ox,oy,ox,oy+size);
  g.addColorStop(0,'#3f7a35'); g.addColorStop(1,'#2c5a26');
  ctx.fillStyle=g; ctx.fillRect(ox,oy,size,size);
  for(let n=0;n<Math.round(size*0.36);n++){ const px=ox+r()*size,py=oy+r()*size,rr=size*(0.05+r()*0.13);
    ctx.fillStyle = r()<0.5 ? 'rgba(58,110,44,0.5)' : 'rgba(96,150,60,0.4)';
    ctx.beginPath(); ctx.ellipse(px,py,rr,rr*0.7,r()*3,0,Math.PI*2); ctx.fill(); }
  const blades=Math.round(size*1.15);
  for(let n=0;n<blades;n++){ const px=ox+r()*size,py=oy+size*0.06+r()*size*0.94,h=size*(0.06+r()*0.14),lean=(r()-0.5)*size*0.08;
    const sh=70+r()*70; ctx.strokeStyle=`rgb(${(sh*0.45)|0},${sh|0},${(sh*0.35)|0})`;
    ctx.lineWidth=Math.max(1,size/64); ctx.beginPath(); ctx.moveTo(px,py); ctx.lineTo(px+lean,py-h); ctx.stroke(); }
}

function paintDirt(ctx, ox, oy, size, r){
  ctx.fillStyle='#6b4a2e'; ctx.fillRect(ox,oy,size,size);
  for(let n=0;n<Math.round(size*0.47);n++){ const px=ox+r()*size,py=oy+r()*size,rr=size*(0.06+r()*0.18);
    ctx.fillStyle = r()<0.5 ? 'rgba(60,40,24,0.5)' : 'rgba(120,88,54,0.45)';
    ctx.beginPath(); ctx.ellipse(px,py,rr,rr*0.8,r()*3,0,Math.PI*2); ctx.fill(); }
  for(let n=0;n<Math.round(size*0.2);n++){ const px=ox+r()*size,py=oy+r()*size,rr=size*(0.012+r()*0.025);
    const s=80+r()*60; ctx.fillStyle=`rgb(${s|0},${(s*0.85)|0},${(s*0.7)|0})`;
    ctx.beginPath(); ctx.ellipse(px,py,rr,rr*0.8,0,0,Math.PI*2); ctx.fill();
    ctx.fillStyle='rgba(0,0,0,0.3)'; ctx.beginPath(); ctx.ellipse(px+rr*0.4,py+rr*0.4,rr,rr*0.7,0,0,Math.PI*2); ctx.fill(); }
}

function paintBrick(ctx, ox, oy, size, r, base, mortar){
  ctx.fillStyle=mortar; ctx.fillRect(ox,oy,size,size);
  const rh=size*0.17, bw=size*0.5; let row=0;
  for(let by=oy; by<oy+size; by+=rh){ const off=(row%2)?bw*0.5:0;
    for(let bx=ox-off; bx<ox+size; bx+=bw){ const v=(r()*16-8)|0;
      ctx.fillStyle=`rgb(${Math.max(0,base[0]+v)},${Math.max(0,base[1]+v)},${Math.max(0,base[2]+v)})`;
      ctx.fillRect(bx+1.5, by+1.5, bw-3, rh-3);
      ctx.fillStyle='rgba(255,255,255,0.05)'; ctx.fillRect(bx+1.5, by+1.5, bw-3, Math.max(1,size/40)); }
    row++; }
}

function paintCave(ctx, ox, oy, size, r){
  ctx.fillStyle='#1c160f'; ctx.fillRect(ox,oy,size,size);
  const step=size*0.25, pts=[];
  for(let gy=0;gy<4;gy++) for(let gx=0;gx<4;gx++)
    pts.push([ox+gx*step+step*0.3+(r()-0.5)*step*0.55, oy+gy*step+step*0.3+(r()-0.5)*step*0.55]);
  for(const p of pts){ const rad=size*(0.10+r()*0.09), nv=6+(r()*3|0), base=70+r()*45;
    ctx.fillStyle=`rgb(${base|0},${(base*0.9)|0},${(base*0.74)|0})`;
    ctx.beginPath();
    for(let k=0;k<nv;k++){ const a=k/nv*Math.PI*2, rr=rad*(0.7+r()*0.5);
      const xx=p[0]+Math.cos(a)*rr, yy=p[1]+Math.sin(a)*rr; k?ctx.lineTo(xx,yy):ctx.moveTo(xx,yy); }
    ctx.closePath(); ctx.fill();
    ctx.strokeStyle='rgba(0,0,0,0.5)'; ctx.lineWidth=Math.max(1,size/42); ctx.stroke();
    ctx.fillStyle='rgba(255,235,200,0.10)';
    ctx.beginPath(); ctx.ellipse(p[0]-rad*0.3,p[1]-rad*0.3,rad*0.4,rad*0.3,0,0,Math.PI*2); ctx.fill(); }
}

function paintRubble(ctx, ox, oy, size, r){
  ctx.fillStyle='#2b2620'; ctx.fillRect(ox,oy,size,size);
  for(let n=0;n<Math.round(size*0.13);n++){ const px=ox+size*0.06+r()*size*0.88,py=oy+size*0.06+r()*size*0.88,
      rw=size*(0.06+r()*0.13),rh=size*(0.05+r()*0.10), t=60+r()*55;
    ctx.fillStyle=`rgb(${t|0},${(t-7)|0},${(t-16)|0})`;
    ctx.beginPath(); ctx.ellipse(px,py,rw,rh,(r()-0.5)*3,0,Math.PI*2); ctx.fill();
    ctx.strokeStyle='rgba(0,0,0,0.5)'; ctx.lineWidth=Math.max(1,size/64); ctx.stroke();
    ctx.fillStyle='rgba(255,235,200,0.10)'; ctx.fillRect(px-rw*0.5,py-rh*0.7,rw,Math.max(1.5,size/40)); }
}
```

- [ ] **Step 2: Verificar sintaxe**

Run: `node --check game.js`
Expected: sem erro.

- [ ] **Step 3: Commit**

```bash
git add game.js
git commit -m "feat(materiais): painters procedurais genéricos (grama/terra/tijolo/caverna/escombro)"
```

---

## Task 2: 2D — pisos por estilo (game.js)

**Files:** Modify `game.js` — `MAT_PALETTE_2D` (~5259) e `drawFloor3D` (~5281).

- [ ] **Step 1: Ajustar `MAT_PALETTE_2D` (pisos)**

Trocar as 5 linhas de pisos no objeto `MAT_PALETTE_2D` por:
```js
  pedra_cinza: { base: [44, 42, 50],  accent: 'stone' },
  terra:       { base: [74, 56, 38],  accent: 'dirt'  },
  grama:       { base: [46, 78, 40],  accent: 'grass' },
  pedra_negra: { base: [20, 19, 24],  accent: 'stone' },
  entulho:     { base: [70, 66, 58],  accent: 'rubble' },
```
(pedra_negra fica mais escura; o resto mantém os ids/accents.)

- [ ] **Step 2: Despachar o desenho do chão por estilo em `drawFloor3D`**

No início de `drawFloor3D`, logo após `const [BR, BG, BB] = pal.base;`, há o bloco da lajota `const sub=2, sp=...; for(...){...}`. Envolver esse bloco num `else` e desviar grama/terra para os painters. Trocar:
```js
  const sub=2, sp=CELL/sub, grt=2;
```
(início do bloco da lajota) por uma guarda antes dele:
```js
  if(pal.accent==='grass'){ paintGrass(ctx, X, Y, CELL, _rng((x*53^y*97^7)>>>0)); }
  else if(pal.accent==='dirt'){ paintDirt(ctx, X, Y, CELL, _rng((x*29^y*71^3)>>>0)); }
  else {
  const sub=2, sp=CELL/sub, grt=2;
```
e fechar o `else` com `}` imediatamente ANTES do comentário `// Reachable tile highlight (blue)` (fim do for da lajota). Ou seja, todo o bloco da lajota (o `for` de sub-slabs, incluindo as variações inline de grama/terra adicionadas antes) fica dentro do `else`.

Dentro desse bloco da lajota, **remover** os dois `if` inline antigos (`pal.accent==='grass'` tufo e `pal.accent==='dirt'` seixo) — agora a grama/terra têm painter próprio. Os realces (reachable/attackable/weaponPreview) seguem após o `else`, valendo para todos.

- [ ] **Step 3: Verificar e checar visual**

Run: `node --check game.js` → sem erro.
Verificação visual no preview (Task 6) com showcase: grama = gramado verde com lâminas; terra = solo marrom mosqueado com seixos; cinza/negra = lajota.

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(materiais): pisos 2D por estilo (grama e terra de verdade)"
```

---

## Task 3: 2D — paredes por estilo (game.js)

**Files:** Modify `game.js` — `MAT_PALETTE_2D` (paredes) e `drawWallTop3D` (~5547).

- [ ] **Step 1: Ajustar accents das paredes em `MAT_PALETTE_2D`**

Trocar as 4 linhas de paredes por:
```js
  pedra_normal:  { base: [132, 130, 140], accent: 'wallStone' },
  enegrecida:    { base: [24, 23, 28],   accent: 'blackbrick' },
  pedra_caverna: { base: [104, 92, 74],  accent: 'cave' },
  desmoronada:   { base: [96, 88, 76],   accent: 'wallRubble' },
```

- [ ] **Step 2: Despachar `drawWallTop3D` por estilo**

Logo após `const [BR, BG, BB] = pal.base;` no topo de `drawWallTop3D`, inserir o desvio para os novos estilos (os demais caem no corpo atual):
```js
  if(pal.accent==='cave'){ paintCave(ctx, X, Y, CELL, _rng((x*41^y*23^9)>>>0)); return; }
  if(pal.accent==='blackbrick'){ paintBrick(ctx, X, Y, CELL, _rng((x*7^y*13)>>>0), [22,21,26], '#070709'); return; }
```
> `pedra_normal` (wallStone) e `desmoronada` (wallRubble) continuam usando o corpo atual de `drawWallTop3D` (que já trata `wallRubble` com as juntas quebradas). O `drawWallSouthFace` (face frontal) permanece tingido pela base — sem mudança.

- [ ] **Step 3: Verificar e commit**

Run: `node --check game.js` → sem erro.
```bash
git add game.js
git commit -m "feat(materiais): paredes 2D por estilo (tijolo preto + caverna irregular)"
```

---

## Task 4: 3D — textura por material (game.js)

**Files:** Modify `game.js` — `makeMaterialTex` (novo, perto de `generateTexture`) + laço de construção dos tiles 3D (~11150 chão, ~11167 entulho, ~11183 parede).

- [ ] **Step 1: Adicionar `makeMaterialTex` com cache**

Inserir perto da definição de `generateTexture`/`floorBaseMat` (ex.: logo antes de `const floorBaseMat = new`, ~linha 10950):
```js
  // Textura de canvas por material (cache por id). Usa os MESMOS painters do 2D.
  const _matTexCache = {};
  function makeMaterialTex(matId){
    if(_matTexCache[matId]) return _matTexCache[matId];
    const S=256, cv=document.createElement('canvas'); cv.width=cv.height=S;
    const c=cv.getContext('2d'); const r=_rng((matId.length*2654435761)>>>0);
    switch(matId){
      case 'grama':         paintGrass(c,0,0,S,r); break;
      case 'terra':         paintDirt(c,0,0,S,r); break;
      case 'enegrecida':    paintBrick(c,0,0,S,r,[22,21,26],'#070709'); break;
      case 'pedra_caverna': paintCave(c,0,0,S,r); break;
      case 'desmoronada':   paintRubble(c,0,0,S,r); break;
      case 'entulho':       paintRubble(c,0,0,S,r); break;
      default: return null;   // pedra_cinza/normal/negra: usam a textura base tingida
    }
    const tex=new T.CanvasTexture(cv); tex.wrapS=tex.wrapT=T.RepeatWrapping;
    _matTexCache[matId]=tex; return tex;
  }
```

- [ ] **Step 2: Usar a textura no mesh do chão**

No laço de tiles, no ramo do chão, após `mat.color.setRGB(...)` (linha ~11154), inserir:
```js
        const ftex = makeMaterialTex(mid3);
        if(ftex){ mat.map = ftex; mat.color.setRGB(1,1,1); }
```
> Se `makeMaterialTex` retorna `null` (cinza/negra), mantém a textura base de pedra tingida pela cor (comportamento atual).

- [ ] **Step 3: Usar a textura no mesh da parede**

No ramo da parede, após `mat.color.setRGB(...)` (linha ~11185), inserir:
```js
        const wtex = makeMaterialTex(matId3);
        if(wtex){ mat.map = wtex; mat.color.setRGB(1,1,1); }
```

- [ ] **Step 4: Usar a textura de escombros no bloco de entulho**

No bloco do entulho (onde cria `eMat`/`eMesh`, ~11167), após `eMat.color.setRGB(ec[0],ec[1],ec[2]);` inserir:
```js
          const etex = makeMaterialTex('entulho');
          if(etex){ eMat.map = etex; eMat.color.setRGB(1,1,1); }
```

- [ ] **Step 5: Verificar e commit**

Run: `node --check game.js` → sem erro.
Verificação visual (Task 6): renderizar `makeMaterialTex(id).image` num canvas + screenshot (a cena 3D completa não roda no worktree por falta de `ambientes`).
```bash
git add game.js
git commit -m "feat(materiais): textura 3D por material (grama/terra/tijolo preto/caverna/escombro)"
```

---

## Task 5: Editor — material junto de chão/parede (tools/editor.js)

**Files:** Modify `tools/editor.js` — `TOOLS` (~313), estado `S` (matFloor/matWall), `buildToolbar` (~342-353 do bloco material), pintura (`paintTile`/`paintMaterial`/handlers), render swatch já existe.

- [ ] **Step 1: Estado e remoção da ferramenta**

- Em `TOOLS`, **remover** a linha `{ id: "material", label: "material", group: "tiles" },`.
- No objeto `S`, trocar `matId: (MAT[0] ? MAT[0].id : "grama"),` por:
```js
    matFloor: "pedra_cinza",
    matWall: "pedra_normal",
```
(mantém `materiais: {}` e `matFill: false`).

- [ ] **Step 2: Dropdowns nas ferramentas chão/parede em `buildToolbar`**

Remover o bloco `if (S.tool === "material") { ... }` inteiro e inserir, no mesmo lugar:
```js
    if (S.tool === "floor" || S.tool === "wall") {
      const opts = MAT.filter(m => S.tool === "wall"
        ? (m.categoria === "parede" || m.id === "entulho")
        : (m.categoria === "piso" && m.id !== "entulho"));
      const cur = S.tool === "wall" ? S.matWall : S.matFloor;
      const sel = document.createElement("select"); sel.id = "mat-id";
      sel.innerHTML = opts.map(m =>
        `<option value="${m.id}"${m.id === cur ? " selected" : ""}>${m.categoria === "parede" ? "🧱" : (m.id === "entulho" ? "⛰️" : "▦")} ${m.nome}</option>`).join("");
      sel.onchange = e => { if (S.tool === "wall") S.matWall = e.target.value; else S.matFloor = e.target.value; };
      tb.appendChild(sel);
      const fill = document.createElement("button");
      fill.textContent = S.matFill ? "balde: ON" : "balde: OFF";
      fill.title = "Preenche a região contígua de mesma estrutura";
      fill.onclick = () => { S.matFill = !S.matFill; buildToolbar(); };
      tb.appendChild(fill);
    }
```

- [ ] **Step 3: Pintura — estrutura + material juntos**

Reescrever `paintTile` para aplicar o material do tool e tratar o entulho:
```js
  function paintTile(x, y) {
    if (S.tool === "wall") {
      if (S.matWall === "entulho") { S.tiles[y][x] = FLOOR; S.materiais[x + "," + y] = "entulho"; return; }
      S.tiles[y][x] = WALL;
      _applyMat(x, y, S.matWall, "parede");
    } else if (S.tool === "floor") {
      S.tiles[y][x] = FLOOR;
      _applyMat(x, y, S.matFloor, "piso");
    } else if (S.tool === "door") {
      S.tiles[y][x] = DOOR; doorLink(x, y);
      const mid = S.materiais[x + "," + y];
      if (mid && !matCompat(mid, x, y)) delete S.materiais[x + "," + y];
    }
  }
  // Aplica material M na casa (limpa se for o default da categoria → JSON esparso).
  function _applyMat(x, y, M, cat) {
    if (M === MAT_DEFAULT[cat]) delete S.materiais[x + "," + y];
    else S.materiais[x + "," + y] = M;
  }
```
> `_applyMat` substitui o antigo `_setMat` — **remover a função `_setMat`** (não é
> mais usada; referenciava `S.matId`, que deixou de existir). `matCompat`/`_structKind`
> continuam. Confirmar com `grep -n "S.matId\|_setMat" tools/editor.js` que não sobrou
> nenhuma referência a `S.matId`/`_setMat`.

- [ ] **Step 4: Balde para chão/parede (`paintMaterial` → flood do tool)**

Trocar `paintMaterial` por uma versão que pinta a região com a estrutura+material do tool (reusa o flood 4-conexo de mesma estrutura):
```js
  function paintMaterial(x, y) {
    if (!S.matFill) { paintTile(x, y); return; }
    const kind = _structKind(x, y);
    const seen = new Set([x + "," + y]); const st = [[x, y]];
    while (st.length) {
      const [cx, cy] = st.pop();
      if (_structKind(cx, cy) === kind) paintTile(cx, cy);
      for (const [dx, dy] of [[1,0],[-1,0],[0,1],[0,-1]]) {
        const nx = cx + dx, ny = cy + dy, k = nx + "," + ny;
        if (nx>=0 && ny>=0 && nx<S.grid.w && ny<S.grid.h && !seen.has(k) && _structKind(nx,ny)===kind) { seen.add(k); st.push([nx,ny]); }
      }
    }
  }
```
> O balde preenche a região de mesma estrutura da casa clicada, aplicando o tool atual em cada casa (chão→material de piso; parede→material de parede; parede+entulho→chão-entulho).

- [ ] **Step 5: Handlers de mouse**

Em mousedown (~806-807): trocar
```js
    if (["wall", "floor", "door"].includes(S.tool)) { painting = true; paintTile(x, y); render(); }
    else if (S.tool === "material") { painting = true; paintMaterial(x, y); render(); updateStatus(); }
```
por
```js
    if (["wall", "floor", "door"].includes(S.tool)) { painting = true; (S.matFill && S.tool!=="door" ? paintMaterial : paintTile)(x, y); render(); updateStatus(); }
```
Em mousemove (~837-839): trocar
```js
      if (S.tool === "material") { paintMaterial(c[0], c[1]); updateStatus(); }
      else paintTile(c[0], c[1]);
```
por
```js
      if ((S.tool === "floor" || S.tool === "wall") && S.matFill) { paintMaterial(c[0], c[1]); updateStatus(); }
      else paintTile(c[0], c[1]);
```

- [ ] **Step 6: Verificar e commit**

Run: `node --check tools/editor.js` → sem erro.
Verificação manual (Task 6): chão/parede têm dropdown; pintar coloca material; entulho via parede vira chão-bloqueante; balde funciona; save/load preservam `materiais`.
```bash
git add tools/editor.js
git commit -m "feat(materiais): editor escolhe material junto de chão/parede (remove ferramenta material)"
```

---

## Task 6: Verificação visual + funcional

- [ ] **Step 1: Tests de servidor (não-regressão)**

Run: `python tools/test_materiais.py` → 40/40. `python tools/test_decoracoes.py` → sem regressão.

- [ ] **Step 2: Showcase 2D + 3D no preview**

Iniciar o servidor do worktree (`python server.py`) e attachar o preview. Via `preview_eval`, desenhar num canvas: (a) cada piso/parede 2D pelas funções `drawFloor3D`/`drawWallTop3D`; (b) cada `makeMaterialTex(id).image`. Tirar `preview_screenshot` e amostrar pixels (grama verde-dominante, terra marrom, tijolo preto escuro com argamassa, caverna irregular).

- [ ] **Step 3: Editor no preview**

Abrir `/tools/editor.html`, selecionar "chão"→grama e pintar; "parede"→enegrecida e pintar; "parede"→entulho e confirmar que vira chão-bloqueante; ligar balde e preencher; salvar e recarregar conferindo `materiais`.

- [ ] **Step 4: Commit (se houver ajuste fino de cor)**

```bash
git add game.js
git commit -m "fix(materiais): ajuste fino de paletas após verificação visual"
```

---

## Riscos / lembretes
- **Perf 3D:** `makeMaterialTex` cacheia por id (uma textura por material, não por casa).
- **2D/3D coerentes:** os mesmos painters alimentam as duas vistas.
- **Entulho** é o único caso cruzado (dropdown de parede, mas pinta chão); isolado em `paintTile`.
- **Compat:** ids e modelo de dados inalterados; masmorras existentes ganham o visual novo.
