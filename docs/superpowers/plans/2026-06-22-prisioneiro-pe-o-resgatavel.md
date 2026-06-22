# Peão de prisioneiro resgatável e editável — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar ao prisioneiro do editor de masmorras stats próprios (CA 10, movimento 6, 7 HP), fazê-lo seguir o herói que o resgatou, levar ataques (d20 vs CA 10) que podem falhar o resgate, e permitir uma imagem/miniatura editável por upload, renderizada em 2D e 3D.

**Architecture:** Servidor Python autoritativo (`server.py`) cuida dos stats, movimento (após o turno do resgatador) e dano (fase inimiga). Editor (`tools/editor.js` + `tools/story_upload.js`) faz upload da imagem por WebSocket e grava o caminho no JSON da masmorra. Cliente (`game.js`) renderiza o peão em 2D (canvas) e 3D (billboard Three.js), com fallback para emoji quando não há imagem.

**Tech Stack:** Python 3 (`websockets`), Vanilla JS, Three.js r128. Testes de servidor: harness manual em `tools/test_objetivos.py` (rodar `python tools/test_objetivos.py`). Testes de cliente: `node --check` para sintaxe + verificação manual no navegador.

**Spec:** `docs/superpowers/specs/2026-06-22-prisioneiro-pe-o-resgatavel-design.md`

---

## File Structure

- `server.py` — constantes de stats, instanciação do prisioneiro, `handle_libertar_prisioneiro`, novo `_mover_prisioneiro_seguindo`, dano com CA em `_processar_prisioneiro_turno`, hook no `handle_end_turn`, helper de upload + handler `upload_prisoner`, validação.
- `tools/story_upload.js` — expõe `window.PRISONER_UPLOAD.upload(file)`.
- `tools/editor.js` — painel do prisioneiro com upload de imagem; `buildJSON`/load preservam `image`.
- `game.js` — render 2D (`renderMap`, ~4903) e 3D (sync de entidades, ~12345) do prisioneiro com imagem.
- `tools/test_objetivos.py` — testes de stats, movimento, dano com CA, upload.

---

## Task 1: Stats do prisioneiro (HP 7, CA 10, MOVE 6, campo image)

**Files:**
- Modify: `server.py:33` (constante `PRIS_HP`)
- Modify: `server.py:3653` (instanciação do prisioneiro)
- Modify: `server.py:1760` (validação)
- Test: `tools/test_objetivos.py` (test_instanciar)

- [ ] **Step 1: Atualizar o teste de instanciação (falha primeiro)**

Em `tools/test_objetivos.py`, dentro de `test_instanciar()`, após a checagem `"prisioneiro instanciado (cativo, vivo)"`, adicionar:

```python
    check("prisioneiro com 7 HP", r.prisoner["hp"] == 7 and r.prisoner["max_hp"] == 7)
    check("prisioneiro com CA 10", r.prisoner["ac"] == 10)
    check("prisioneiro com movimento 6", r.prisoner["move"] == 6)
    check("prisioneiro com campo image", "image" in r.prisoner)
    check("prisioneiro com rescuer_pid None", r.prisoner["rescuer_pid"] is None)
```

- [ ] **Step 2: Rodar o teste e confirmar a falha**

Run: `python tools/test_objetivos.py`
Expected: FAIL nos novos checks (`KeyError`/valores errados — hoje `PRIS_HP=12` e não há `ac`/`move`/`image`/`rescuer_pid`).

- [ ] **Step 3: Atualizar as constantes**

Em `server.py:33`, trocar:

```python
PRIS_HP = 12        # vida do prisioneiro (Fase 3)
```

por:

```python
PRIS_HP = 7         # vida do prisioneiro (Fase 3)
PRIS_AC = 10        # classe de armadura do prisioneiro
PRIS_MOVE = 6       # quadrados que o prisioneiro liberto anda por turno (segue o resgatador)
```

- [ ] **Step 4: Atualizar a instanciação**

Em `server.py:3653`, trocar o bloco:

```python
        pr = defn.get("prisoner")
        self.prisoner = ({"pos": [pr["pos"][0], pr["pos"][1]], "room_id": pr.get("room_id"),
                          "hp": PRIS_HP, "max_hp": PRIS_HP, "freed": False, "alive": True}
                         if pr else None)
```

por:

```python
        pr = defn.get("prisoner")
        self.prisoner = ({"pos": [pr["pos"][0], pr["pos"][1]], "room_id": pr.get("room_id"),
                          "hp": PRIS_HP, "max_hp": PRIS_HP, "ac": PRIS_AC, "move": PRIS_MOVE,
                          "image": pr.get("image"), "rescuer_pid": None,
                          "freed": False, "alive": True}
                         if pr else None)
```

- [ ] **Step 5: Validar `image` no carregador**

Em `server.py:1760`, ler o bloco que valida `prisoner` (começa em `pr = defn.get("prisoner")`). Após as checagens existentes de `pos`/`room_id` e antes do `return True` daquela seção, adicionar:

```python
        if pr.get("image") is not None and not isinstance(pr.get("image"), str):
            return False, "prisoner.image deve ser uma string (caminho do arquivo)."
```

- [ ] **Step 6: Rodar o teste e confirmar PASS**

Run: `python tools/test_objetivos.py`
Expected: PASS em todos os checks de `test_instanciar`.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat(prisioneiro): stats CA 10, movimento 6, 7 HP e campo image"
```

---

## Task 2: Gravar o resgatador ao libertar

**Files:**
- Modify: `server.py:12208` (`handle_libertar_prisioneiro`)
- Test: `tools/test_objetivos.py` (test_prisioneiro)

- [ ] **Step 1: Adicionar checagem ao teste (falha primeiro)**

Em `tools/test_objetivos.py`, dentro de `test_prisioneiro()`, logo após a linha `check("prisioneiro libertado por herói adjacente", r.prisoner["freed"] is True)`, adicionar:

```python
    check("libertar registra o resgatador", r.prisoner["rescuer_pid"] == "p1")
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_objetivos.py`
Expected: FAIL — `rescuer_pid` continua `None`.

- [ ] **Step 3: Gravar o rescuer_pid**

Em `server.py:12208`, no `handle_libertar_prisioneiro`, trocar:

```python
        self.prisoner["freed"] = True
        p["action_done"] = True
```

por:

```python
        self.prisoner["freed"] = True
        self.prisoner["rescuer_pid"] = pid
        p["action_done"] = True
```

- [ ] **Step 4: Rodar e confirmar PASS**

Run: `python tools/test_objetivos.py`
Expected: PASS no novo check.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat(prisioneiro): registra o resgatador ao libertar"
```

---

## Task 3: Movimento — segue o resgatador após o turno dele

**Files:**
- Modify: `server.py:12213` (`_processar_prisioneiro_turno` — remover movimento)
- Create: novo método `_mover_prisioneiro_seguindo` (perto do `_processar_prisioneiro_turno`)
- Modify: `server.py:9514` (`handle_end_turn` — chamar o novo método)
- Test: `tools/test_objetivos.py` (novo `test_prisioneiro_segue`)

- [ ] **Step 1: Escrever o teste novo (falha primeiro)**

Em `tools/test_objetivos.py`, adicionar esta função antes de `async def main():`:

```python
async def test_prisioneiro_segue():
    print("\n[6] prisioneiro liberto segue o resgatador (até 6, para adjacente)")
    r = setup_authored()
    r.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r.enter_dungeon("p1")
    # Tira os monstros do caminho para isolar o movimento.
    for m in r.monsters.values(): m["hp"] = 0
    pr = r.prisoner
    pr["freed"] = True; pr["alive"] = True; pr["rescuer_pid"] = "p1"
    # Coloca prisioneiro e resgatador na mesma linha, distância 8 (chão livre).
    pr["pos"] = [2, 8]
    r.players["p1"]["pos"] = [10, 8]
    r.players["p1"]["alive"] = True
    # Garante que a linha y=8, x∈[2..10] é chão.
    for x in range(2, 11):
        r.tiles[8][x] = server.FLOOR
    await r._mover_prisioneiro_seguindo("p1")
    dist = max(abs(pr["pos"][0] - 10), abs(pr["pos"][1] - 8))
    check("prisioneiro andou até 6 (de 8 → fica a 2 de distância)", dist == 2)

    # Se o pid que encerrou NÃO é o resgatador, não anda.
    pr["pos"] = [2, 8]
    await r._mover_prisioneiro_seguindo("p2")
    check("não anda no turno de quem não é o resgatador", pr["pos"] == [2, 8])

    # Resgatador morto → reatribui ao herói vivo mais próximo e anda no turno dele.
    r.players["p1"]["alive"] = False
    r.players["p2"]["alive"] = True
    r.players["p2"]["pos"] = [10, 8]
    pr["pos"] = [2, 8]
    await r._mover_prisioneiro_seguindo("p2")
    check("resgatador morto → segue novo herói", r.prisoner["rescuer_pid"] == "p2"
          and max(abs(pr["pos"][0] - 10), abs(pr["pos"][1] - 8)) == 2)
```

E registrar a chamada em `main()` após `await test_serializacao()`:

```python
    await test_prisioneiro_segue()
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_objetivos.py`
Expected: FAIL — `_mover_prisioneiro_seguindo` não existe (`AttributeError`).

- [ ] **Step 3: Criar `_mover_prisioneiro_seguindo` e remover o movimento de `_processar_prisioneiro_turno`**

Em `server.py:12213`, trocar o `_processar_prisioneiro_turno` atual:

```python
    async def _processar_prisioneiro_turno(self):
        """Prisioneiro libertado: 1 passo em direção ao herói vivo mais próximo;
        depois, cada monstro adjacente o fere. Morte → rescue_failed (não encerra)."""
        pr = self.prisoner
        if not pr or not pr.get("freed") or not pr.get("alive"):
            return
        herois = [p for p in self.players.values() if self._ativo(p)]
        if herois:
            alvo = min(herois, key=lambda p: max(abs(p["pos"][0] - pr["pos"][0]),
                                                 abs(p["pos"][1] - pr["pos"][1])))
            self._step_towards(pr, alvo["pos"])
        # Dano de monstros adjacentes (caminho dedicado, simples e isolado).
        for m in self.monsters.values():
            if m["hp"] <= 0:
                continue
            if max(abs(m["pos"][0] - pr["pos"][0]), abs(m["pos"][1] - pr["pos"][1])) <= 1:
                dano = random.randint(2, 5)
                pr["hp"] -= dano
                await self.gm_say(f"⚔️ Um monstro fere o prisioneiro ({dano})!")
                if pr["hp"] <= 0:
                    pr["alive"] = False
                    self.rescue_failed = True
                    await self.gm_say("☠️ O prisioneiro foi morto! O resgate falhou.")
                    break
```

por (mantendo só o dano — o dano com CA vem na Task 4; aqui só removemos o movimento):

```python
    async def _processar_prisioneiro_turno(self):
        """Prisioneiro libertado: cada monstro adjacente o fere. O MOVIMENTO fica
        em _mover_prisioneiro_seguindo (após o turno do resgatador)."""
        pr = self.prisoner
        if not pr or not pr.get("freed") or not pr.get("alive"):
            return
        for m in self.monsters.values():
            if m["hp"] <= 0:
                continue
            if max(abs(m["pos"][0] - pr["pos"][0]), abs(m["pos"][1] - pr["pos"][1])) <= 1:
                dano = random.randint(2, 5)
                pr["hp"] -= dano
                await self.gm_say(f"⚔️ Um monstro fere o prisioneiro ({dano})!")
                if pr["hp"] <= 0:
                    pr["alive"] = False
                    self.rescue_failed = True
                    await self.gm_say("☠️ O prisioneiro foi morto! O resgate falhou.")
                    break

    async def _mover_prisioneiro_seguindo(self, ended_pid):
        """Após o turno do resgatador, o prisioneiro liberto anda até PRIS_MOVE
        quadrados em direção a ele, parando ao ficar adjacente. Se o resgatador
        morreu, reatribui ao herói vivo mais próximo (verifica ANTES de comparar
        com ended_pid, para não travar)."""
        pr = self.prisoner
        if not pr or not pr.get("freed") or not pr.get("alive"):
            return
        herois = [p for p in self.players.values() if self._ativo(p)]
        if not herois:
            return
        resc = self.players.get(pr.get("rescuer_pid"))
        if not resc or not self._ativo(resc):
            novo = min(herois, key=lambda p: max(abs(p["pos"][0] - pr["pos"][0]),
                                                 abs(p["pos"][1] - pr["pos"][1])))
            pr["rescuer_pid"] = novo["id"]
            resc = novo
        if ended_pid != pr["rescuer_pid"]:
            return
        for _ in range(PRIS_MOVE):
            if max(abs(pr["pos"][0] - resc["pos"][0]),
                   abs(pr["pos"][1] - resc["pos"][1])) <= 1:
                break          # já adjacente — não pisa na casa do herói
            antes = list(pr["pos"])
            self._step_towards(pr, resc["pos"])
            if pr["pos"] == antes:
                break          # sem progresso (bloqueado)
```

Nota: `self._ativo(p)` é o mesmo helper já usado por `_processar_prisioneiro_turno` (heróis vivos/ativos). `make_player` define `p["id"]`; confirme que `resc["id"]` existe (é usado em `push_state` como `current_turn`/`p.id`).

- [ ] **Step 4: Chamar o novo método em `handle_end_turn`**

Em `server.py:9514`, logo após a linha `self.animados_phase_pid = None` (antes de `p["moves_left"] = p["spd"]`), adicionar:

```python
        # Fase 3: o prisioneiro liberto segue o herói que o resgatou, logo após o
        # turno dele (até PRIS_MOVE quadrados, parando adjacente).
        await self._mover_prisioneiro_seguindo(pid)
```

- [ ] **Step 5: Rodar e confirmar PASS**

Run: `python tools/test_objetivos.py`
Expected: PASS em `test_prisioneiro_segue`. (O `test_prisioneiro` antigo ainda passa: ele stuba `_step_towards` e chama `_processar_prisioneiro_turno` direto, que agora só causa dano.)

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat(prisioneiro): segue o resgatador (ate 6, para adjacente) apos o turno dele"
```

---

## Task 4: Dano de monstro com ataque vs CA 10

**Files:**
- Modify: `server.py` (`_processar_prisioneiro_turno`)
- Test: `tools/test_objetivos.py` (test_prisioneiro + novo check de CA)

- [ ] **Step 1: Atualizar o teste de morte para ser determinístico (falha primeiro)**

Em `tools/test_objetivos.py`, dentro de `test_prisioneiro()`, localizar o bloco de morte (que hoje faz `r2.prisoner["freed"] = True; r2.prisoner["hp"] = 1` e chama `_processar_prisioneiro_turno`). Substituir esse bloco por:

```python
    # morte do prisioneiro → falha, sem encerrar. Força o ataque a ACERTAR (d20=20).
    r2 = setup_authored()
    r2.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r2.enter_dungeon("p1")
    r2.prisoner["freed"] = True; r2.prisoner["hp"] = 1
    vit = {"c": False}
    async def fe(victory, story=None): vit["c"] = True
    r2.end_game = fe
    orig_attack = server.d20_attack
    server.d20_attack = lambda atk, ac: (True, 20, 20 + atk, True)   # sempre acerta
    try:
        m = next(iter(r2.monsters.values()))
        m["hp"] = 10; m["pos"] = [r2.prisoner["pos"][0] + 1, r2.prisoner["pos"][1]]   # adjacente
        await r2._processar_prisioneiro_turno()
    finally:
        server.d20_attack = orig_attack
    check("prisioneiro morto marca rescue_failed", r2.rescue_failed is True)
    check("morte do prisioneiro NÃO encerra a partida", vit["c"] is False)
    check("status do resgate = failed",
          r2._objetivo_status(r2.objectives["primary"]) == "failed")

    # CA 10 protege: ataque que ERRA (d20=1) não tira HP.
    r3 = setup_authored()
    r3.dungeon_def["objectives"] = {"primary": {"type": "rescue_prisoner"}, "secondary": []}
    await r3.enter_dungeon("p1")
    r3.prisoner["freed"] = True; r3.prisoner["hp"] = 5
    server.d20_attack = lambda atk, ac: (False, 1, 1 + atk, False)   # sempre erra
    try:
        m3 = next(iter(r3.monsters.values()))
        m3["hp"] = 10; m3["pos"] = [r3.prisoner["pos"][0] + 1, r3.prisoner["pos"][1]]
        await r3._processar_prisioneiro_turno()
    finally:
        server.d20_attack = orig_attack
    check("CA 10 protege: erro não tira HP", r3.prisoner["hp"] == 5)
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_objetivos.py`
Expected: FAIL no check "CA 10 protege" — hoje o dano é automático (`random.randint(2,5)`), sem rolagem.

- [ ] **Step 3: Aplicar o ataque vs CA no `_processar_prisioneiro_turno`**

Em `server.py`, no `_processar_prisioneiro_turno` (versão da Task 3), trocar o corpo do laço de monstros:

```python
            if max(abs(m["pos"][0] - pr["pos"][0]), abs(m["pos"][1] - pr["pos"][1])) <= 1:
                dano = random.randint(2, 5)
                pr["hp"] -= dano
                await self.gm_say(f"⚔️ Um monstro fere o prisioneiro ({dano})!")
                if pr["hp"] <= 0:
                    pr["alive"] = False
                    self.rescue_failed = True
                    await self.gm_say("☠️ O prisioneiro foi morto! O resgate falhou.")
                    break
```

por:

```python
            if max(abs(m["pos"][0] - pr["pos"][0]), abs(m["pos"][1] - pr["pos"][1])) <= 1:
                hit, _roll, _total, _crit = d20_attack(m.get("atk_bonus", 0), pr.get("ac", PRIS_AC))
                if not hit:
                    await self.gm_say(f"🛡️ O prisioneiro esquiva de um monstro!")
                    continue
                dano = roll_dice(m.get("damage", "1d4"))
                pr["hp"] -= dano
                await self.gm_say(f"⚔️ Um monstro fere o prisioneiro ({dano})!")
                if pr["hp"] <= 0:
                    pr["alive"] = False
                    self.rescue_failed = True
                    await self.gm_say("☠️ O prisioneiro foi morto! O resgate falhou.")
                    break
```

Antes de implementar, confirmar o nome da função de rolagem de dano do servidor: `grep -n "def roll_dice\|def rolar_dado\|def roll_damage" server.py`. Usar o nome real (ex.: se for `roll_dice(expr)` que aceita `"1d6"`). Se a assinatura diferir, ajustar a chamada de `dano = ...` para o helper existente que converte `m["damage"]` (ex.: `"1d8"`) em um inteiro.

- [ ] **Step 4: Rodar e confirmar PASS**

Run: `python tools/test_objetivos.py`
Expected: PASS em todos os checks de `test_prisioneiro` (morte com acerto forçado e proteção com erro forçado).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat(prisioneiro): monstros rolam d20+atk vs CA 10 para ferir"
```

---

## Task 5: Upload da imagem do prisioneiro (servidor)

**Files:**
- Modify: `server.py:12694` (generalizar/adicionar helper de gravação)
- Modify: `server.py:12377` (handler de mensagem `upload_prisoner`)
- Modify: `server.py` (`process_request` — confirmar allow-list de `assets/pawns/prisioneiros/`)
- Test: `tools/test_objetivos.py` (novo `test_upload_prisioneiro`)

- [ ] **Step 1: Escrever o teste (falha primeiro)**

Em `tools/test_objetivos.py`, adicionar antes de `main()`:

```python
async def test_upload_prisioneiro():
    print("\n[7] upload de imagem do prisioneiro grava em assets/pawns/prisioneiros/")
    import base64 as _b64
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # PNG 1x1 transparente válido.
    png = _b64.b64encode(_b64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")).decode()
    ok, name = server._save_prisoner_upload("captiva.png", png)
    check("upload ok devolve nome", ok and name == "captiva.png")
    dest = os.path.join(base, "assets", "pawns", "prisioneiros", "captiva.png")
    check("arquivo gravado em assets/pawns/prisioneiros/", os.path.exists(dest))
    if os.path.exists(dest): os.remove(dest)
    okx, _ = server._save_prisoner_upload("ruim.txt", png)
    check("rejeita extensão não-imagem", okx is False)
```

E registrar em `main()`:

```python
    await test_upload_prisioneiro()
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_objetivos.py`
Expected: FAIL — `_save_prisoner_upload` não existe.

- [ ] **Step 3: Adicionar o helper e generalizar o de história**

Em `server.py:12687`, ler o bloco do `_save_story_upload`. Logo após ele (após o `return True, base` na linha ~12722), adicionar:

```python
PRISONER_DIR = os.path.join(BASE_DIR, "assets", "pawns", "prisioneiros")

def _save_prisoner_upload(name, data_b64):
    """Grava uma imagem de prisioneiro em assets/pawns/prisioneiros/. Só imagens.
    Mesma proteção (path-traversal, tamanho) do _save_story_upload.
    Retorna (ok: bool, basename_salvo | mensagem_de_erro)."""
    base = os.path.basename(name or "")
    if not base or "\x00" in base:
        return False, "nome inválido"
    ext = os.path.splitext(base)[1].lower()
    if ext not in _STORY_IMG_EXT:
        return False, "extensão não permitida"
    if not isinstance(data_b64, str) or not data_b64:
        return False, "dados inválidos"
    if (len(data_b64) * 3) // 4 > STORY_UPLOAD_MAX:
        return False, "arquivo grande demais"
    try:
        raw = base64.b64decode(data_b64, validate=True)
    except Exception:
        return False, "dados inválidos"
    if len(raw) > STORY_UPLOAD_MAX:
        return False, "arquivo grande demais"
    try:
        os.makedirs(PRISONER_DIR, exist_ok=True)
        with open(os.path.join(PRISONER_DIR, base), "wb") as f:
            f.write(raw)
    except OSError:
        return False, "falha ao gravar"
    return True, base
```

- [ ] **Step 4: Rodar e confirmar PASS no helper**

Run: `python tools/test_objetivos.py`
Expected: PASS em `test_upload_prisioneiro`.

- [ ] **Step 5: Adicionar o handler de mensagem WebSocket**

Em `server.py:12377`, ler o bloco que trata `upload_story` (a linha `ok, res = _save_story_upload(...)` e seu envio de `upload_result`). Replicar logo abaixo, para `upload_prisoner`:

```python
                if t == "upload_prisoner":
                    ok, res = _save_prisoner_upload(msg.get("name"), msg.get("data"))
                    await ws.send(json.dumps({
                        "type": "upload_result", "upload_id": msg.get("upload_id"),
                        "ok": ok, **({"name": res} if ok else {"error": res})}))
                    continue
```

Ajustar a forma exata (variável do socket, `continue`/`return`, formato da resposta) para casar **idêntica** ao trecho do `upload_story` logo acima.

- [ ] **Step 6: Confirmar a rota estática serve a pasta**

Run: `grep -n "def process_request\|assets" server.py | head -40`
Verificar que a allow-list aceita caminhos sob `assets/` (a pasta `assets/pawns/prisioneiros/` é subpasta de `assets/`, igual a `assets/story/` que já é servida). Se a allow-list listar subpastas explicitamente, adicionar `assets/pawns/prisioneiros/`. Caso contrário (prefixo `assets/` genérico), nenhuma mudança é necessária — anotar a conclusão.

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_objetivos.py
git commit -m "feat(prisioneiro): upload de imagem para assets/pawns/prisioneiros/"
```

---

## Task 6: Cliente de upload no editor (story_upload.js)

**Files:**
- Modify: `tools/story_upload.js:93-115`

- [ ] **Step 1: Expor `PRISONER_UPLOAD.upload`**

Em `tools/story_upload.js`, após a função `upload(file)` (linha ~100) adicionar:

```javascript
  async function uploadPrisoner(file) {
    if (IMG.indexOf(extOf(file.name)) < 0)
      throw new Error("envie uma imagem (png/jpg/webp/gif)");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const data = await toBase64(file);
    const m = await request("upload_prisoner", { name: file.name, data: data });
    return m.name;
  }
```

E na exposição final (linha ~115), trocar:

```javascript
  window.STORY_UPLOAD = { upload: upload };
```

por:

```javascript
  window.STORY_UPLOAD = { upload: upload };
  window.PRISONER_UPLOAD = { upload: uploadPrisoner };
```

- [ ] **Step 2: Checar sintaxe**

Run: `node --check tools/story_upload.js`
Expected: sem saída (sucesso).

- [ ] **Step 3: Commit**

```bash
git add tools/story_upload.js
git commit -m "feat(prisioneiro): cliente PRISONER_UPLOAD.upload no editor"
```

---

## Task 7: Painel de imagem no editor (editor.js)

**Files:**
- Modify: `tools/editor.js:233` (painel do prisioneiro)
- Modify: `tools/editor.js:291` (`buildJSON`)
- Modify: `tools/editor.js:359` (load)

- [ ] **Step 1: Painel com preview + upload**

Em `tools/editor.js:233`, trocar:

```javascript
    } else if (k === "prisoner") {
      panel.innerHTML = `<b>🧍 Prisioneiro</b><div style="color:#8a7a5a;font-size:11px">sala ${ref.room_id ?? "—"}</div>`;
    } else {
```

por:

```javascript
    } else if (k === "prisoner") {
      const img = ref.image
        ? `<img src="../assets/pawns/prisioneiros/${ref.image}" style="max-width:64px;max-height:64px;display:block;margin:6px 0;border:1px solid #5a4a2a">`
        : `<div style="color:#8a7a5a;font-size:11px;margin:6px 0">sem imagem — usará o emoji padrão</div>`;
      panel.innerHTML = `<b>🧍 Prisioneiro</b>
        <div style="color:#8a7a5a;font-size:11px">sala ${ref.room_id ?? "—"}</div>
        ${img}
        <label>miniatura</label>
        <input type="file" id="p-pris-img" accept="image/png,image/jpeg,image/webp,image/gif">
        <div id="p-pris-status" style="color:#8a7a5a;font-size:11px;margin-top:4px"></div>`;
      const inp = document.getElementById("p-pris-img");
      const st = document.getElementById("p-pris-status");
      inp.onchange = async (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) return;
        st.textContent = "enviando…";
        try {
          const name = await window.PRISONER_UPLOAD.upload(file);
          ref.image = name;
          st.textContent = "enviada ✓";
          renderPanel(); render();
        } catch (err) {
          st.textContent = "falha: " + err.message;
        }
      };
    } else {
```

- [ ] **Step 2: Serializar `image` em `buildJSON`**

Em `tools/editor.js:291`, trocar:

```javascript
      prisoner: S.prisoner ? { pos: S.prisoner.pos.slice(), room_id: S.prisoner.room_id } : null,
```

por:

```javascript
      prisoner: S.prisoner ? { pos: S.prisoner.pos.slice(), room_id: S.prisoner.room_id, ...(S.prisoner.image ? { image: S.prisoner.image } : {}) } : null,
```

- [ ] **Step 3: Confirmar o load preserva `image`**

`tools/editor.js:359` já faz `S.prisoner = obj.prisoner || null`, que carrega `image` se presente. Nenhuma mudança necessária — confirmar lendo a linha.

- [ ] **Step 4: Checar sintaxe**

Run: `node --check tools/editor.js`
Expected: sem saída (sucesso).

- [ ] **Step 5: Commit**

```bash
git add tools/editor.js
git commit -m "feat(prisioneiro): painel do editor com upload de miniatura"
```

---

## Task 8: Renderização 2D com imagem + fallback (game.js)

**Files:**
- Modify: `game.js:4324` (adicionar loader `_getPrisoner2DImg`)
- Modify: `game.js:4903` (desenhar imagem ou emoji)

- [ ] **Step 1: Adicionar o loader de imagem do prisioneiro**

Em `game.js:4324`, logo após a função `_getMonster2DImg`, adicionar:

```javascript
// Miniatura 2D do prisioneiro (imagem editável). url completa em assets/pawns/prisioneiros/.
const _pris2DImg = {};
function _getPrisoner2DImg(imageName){
  if(!imageName) return null;
  let img = _pris2DImg[imageName];
  if(img === undefined){
    img = new Image();
    img.onload = () => { if(!mode3D && window.GS && GS.gameState){ try{ renderMap(GS.gameState); }catch(_){} } };
    img.src = _assetURL(`assets/pawns/prisioneiros/${imageName}`);
    _pris2DImg[imageName] = img;
  }
  return img;
}
```

- [ ] **Step 2: Desenhar a imagem (ou cair no emoji)**

Em `game.js:4910`, trocar:

```javascript
      drawMiniBase(ctx, cx, cy, _pris.freed?'#2e90c0':'#8a6d3b', false);
      ctx.font=`${Math.round(CELL*0.46)}px serif`;
      ctx.textAlign='center'; ctx.textBaseline='middle';
      ctx.fillText(_pris.freed?'🧍':'⛓️', cx, cy-3);
```

por:

```javascript
      drawMiniBase(ctx, cx, cy, _pris.freed?'#2e90c0':'#8a6d3b', false);
      const _pImg = _getPrisoner2DImg(_pris.image);
      if(_pImg && _pImg.complete && _pImg.naturalWidth){
        const sz = Math.round(CELL*0.78);
        ctx.drawImage(_pImg, cx - sz/2, cy - sz/2 - 3, sz, sz);
      } else {
        ctx.font=`${Math.round(CELL*0.46)}px serif`;
        ctx.textAlign='center'; ctx.textBaseline='middle';
        ctx.fillText(_pris.freed?'🧍':'⛓️', cx, cy-3);
      }
```

- [ ] **Step 3: Checar sintaxe**

Run: `node --check game.js`
Expected: sem saída (sucesso).

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(prisioneiro): render 2D com imagem editavel (fallback emoji)"
```

---

## Task 9: Renderização 3D do prisioneiro (game.js)

**Files:**
- Modify: `game.js:12297` (incluir prisioneiro na `entitySig`)
- Modify: `game.js:12359` (adicionar bloco do prisioneiro após os players)
- Create: builder `build3DPrisoner` (perto de `addHeroPawn3D`, ~`game.js:12716`)

- [ ] **Step 1: Incluir o prisioneiro na assinatura de entidades**

Em `game.js:12297`, dentro do array `entitySig`, adicionar uma linha (ex.: após `state.monsters.map(...)`):

```javascript
    state.prisoner ? [state.prisoner.pos, state.prisoner.alive, state.prisoner.freed, state.prisoner.image] : null,
```

- [ ] **Step 2: Builder do peão do prisioneiro**

Em `game.js:12716`, ler `addHeroPawn3D`/`_makeBillboardSprite` para o padrão (base + billboard). Logo após `addHeroPawn3D`, adicionar:

```javascript
// Peão 3D do prisioneiro: base + billboard com a imagem editável (fallback: base só).
function build3DPrisoner(T, pris){
  const grp = new T.Group();
  // Base do peão (cilindro achatado), tom conforme cativo/liberto.
  const baseCor = pris.freed ? 0x2e90c0 : 0x8a6d3b;
  const baseGeo = new T.CylinderGeometry(0.34, 0.38, 0.12, 24);
  const baseMat = new T.MeshStandardMaterial({ color: baseCor, roughness: 0.8 });
  const base = new T.Mesh(baseGeo, baseMat);
  base.position.y = 0.06;
  grp.add(base);
  if(pris.image){
    _makeBillboardSprite(T, grp, _assetURL(`assets/pawns/prisioneiros/${pris.image}`),
      `_pris_${pris.image}`, 0.12, 1.0, 'frente');
  }
  return grp;
}
```

Nota: confirmar a assinatura real de `_makeBillboardSprite` em `game.js:12762` — `(T, grp, texUrl, cacheKey, Y0, sizeFactor, mode)` — e ajustar os 3 últimos args (`Y0`, `sizeFactor`, `mode`) aos valores usados pelos heróis em `addHeroPawn3D` para o tamanho/altura ficarem consistentes.

- [ ] **Step 3: Adicionar o prisioneiro à cena 3D**

Em `game.js:12359`, logo após o laço `// Players` (antes de `// Monsters`), adicionar:

```javascript
  // Prisioneiro (Fase 3): peão com imagem editável; só quando visível/explorado.
  const _pris3D = state.prisoner;
  if(_pris3D && _pris3D.alive){
    const [prx,pry] = _pris3D.pos;
    if(visionSet.has(`${prx},${pry}`) || exploredSet.has(`${prx},${pry}`)){
      obterFig('prisoner',
        JSON.stringify([_pris3D.freed, _pris3D.image]),
        () => build3DPrisoner(g3.T, _pris3D),
        prx, pry);
    }
  }
```

- [ ] **Step 4: Checar sintaxe**

Run: `node --check game.js`
Expected: sem saída (sucesso).

- [ ] **Step 5: Commit**

```bash
git add game.js
git commit -m "feat(prisioneiro): render 3D (billboard com imagem editavel)"
```

---

## Task 10: Verificação manual ponta-a-ponta

**Files:** nenhum (verificação).

- [ ] **Step 1: Subir o servidor**

Run: `python server.py` (ou `iniciar.bat`). Abrir `http://localhost:8765/index.html`.

- [ ] **Step 2: Editor — colocar prisioneiro e enviar imagem**

Abrir o editor de masmorras, usar a ferramenta `prisioneiro`, selecioná-lo, escolher uma imagem PNG no painel. Confirmar status "enviada ✓", preview aparece, e o arquivo surge em `assets/pawns/prisioneiros/`. Salvar a masmorra e conferir no JSON salvo o campo `prisoner.image`.

- [ ] **Step 3: Jogo — resgate, seguir, dano**

Carregar a masmorra, aproximar um herói do prisioneiro, libertar. Encerrar o turno do resgatador e confirmar que o prisioneiro anda até ~6 quadrados na direção dele (2D e 3D, com a imagem). Levar o prisioneiro perto de um monstro e confirmar no log do GM as rolagens (esquiva/ferida) e, ao zerar HP, "o resgate falhou". Verificar que a imagem aparece tanto no canvas 2D quanto no 3D.

- [ ] **Step 4: Regressão dos testes de servidor**

Run: `python tools/test_objetivos.py`
Expected: `=== N passou, 0 falhou ===`.

- [ ] **Step 5: Commit (se houver ajustes de verificação)**

```bash
git add -A
git commit -m "test(prisioneiro): ajustes da verificacao ponta-a-ponta"
```

---

## Notas de execução

- **Não commitar** as mudanças de árvore de trabalho pré-existentes não relacionadas (peões `frente.png`, músicas, dungeons soltas etc.). Em cada `git add`, listar apenas os arquivos da tarefa (como nos comandos acima) — evitar `git add -A` exceto na verificação final, e mesmo lá conferir o `git status` antes.
- Confirmar nomes reais de helpers do servidor antes de usá-los: `_ativo`, `d20_attack`, e a função de rolagem de dano (`roll_dice`/equivalente). Os greps estão indicados nas tarefas.
- Three.js é r128: usar a API já presente (`_makeBillboardSprite`, `build3DFig`) em vez de introduzir construções novas.
