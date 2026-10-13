# Reações elementais Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer fogo, frio e eletricidade reagirem com o terreno (água, piche, lava) por uma tabela de reações central, com piche como terreno pintável e como frasco arremessável.

**Architecture:** Um mixin de servidor `terrain_reactions.py` (padrão do `monster_intent.py`) guarda a tabela de reações e o motor `evento_elemental` (escopo por ação) + `_rx_registrar` (fontes dizem "este elemento atingiu estas casas"). O escopo acumula as casas até o fim da ação e resolve cada reação uma vez, o que dá o dedupe por evento. As mudanças de terreno reaproveitam o registro de camadas temporárias do Chamado do Inverno (`_aplicar_camadas_terreno_inverno` / `_expirar_terrenos_inverno`). O cliente só desenha (mensagem `reacao_elemental`, tooltips, aviso da crosta).

**Tech Stack:** Python 3 (`websockets`, mixin de `GameRoom`), JS vanilla, Three.js r128, testes por script (`python -X utf8 tools/test_*.py`, `node tools/test_*.js`).

**Spec:** `docs/superpowers/specs/2026-10-13-reacoes-elementais-design.md`

## Ajustes ao spec (achados na leitura do código; o Task 8 atualiza o spec)

- `custo_mov` em `MATERIAIS` é só metadado: o custo real está **fixo** em `GameRoom._water_step_cost` (servidor) e `terrainMoveCost` (`src/gameState.js`). O piche entra nos dois lugares com **custo 2 por casa** (igual à areia do deserto e à lava), não "custo_mov=1".
- A lava da Ira da Rocha Ardente **é material** (`"lava"` pintado pelo mesmo registro de camadas): o frio a apaga como a lava autoral. O risco anotado no spec está resolvido.
- Dedupe por evento: em vez de ids, o motor usa um **escopo por ação** (`evento_elemental`). As fontes registram casas durante a ação; o escopo resolve uma vez no fim, sobre a união das casas.
- Na ignição do piche quem já está na mancha também sofre 1d6 + "em chamas" imediatamente (além de entrar/início do turno).
- O aviso da crosta usa um campo novo `terrenos_temp` no `game_state` (`"x,y" → expira_em`).

## Global Constraints

- Servidor autoritativo; `src/gameState.js` sem `document`/`window`/`canvas`/`THREE`; `game.js` só renderiza (CLAUDE.md).
- Elementos canônicos: `DMG_FIRE="fire"`, `DMG_COLD="cold"`, `DMG_LIGHTNING="lightning"`. O mixin define `RX_FIRE/RX_COLD/RX_LIGHTNING` com os mesmos valores; um teste confere igualdade com `server.DMG_*`.
- Poça: região conectada (4 vizinhos) de água rasa (`agua`), teto **24** casas, raio **6** (Chebyshev) do impacto. Mancha de piche: teto **40**. Profundidade máxima de cadeia: **2**.
- Choque: dano elétrico = `max(1, dano_da_fonte // 2)`, Reflexos para metade (CD da fonte, senão **12**); quem já foi atingido pela fonte não toma o choque; voadores (`_voo_imune_terreno`) não são atingidos.
- Chamas de piche: **1d6** de fogo + `_aplicar_em_chamas(alvo, 1d4, True)`; só no piso (`normalizar_altura(alvo.get("altura", ALTURA_MIN)) > ALTURA_MIN` é ignorado); duram **3 rodadas** (`expira_em = round_num + 3`).
- Congelar água: `piso_congelado` por **3 rodadas**; Reflexos (CD da fonte, senão 12); falha → `alvo["moves_left"] = 0` e `alvo["movimento_perdido"] = True` (o mesmo efeito de `perder_movimento` das armadilhas).
- Crosta: lava → `lava_solidificada` por **3 rodadas**. Frasco de piche: 3×3 por **4 rodadas**, sem dano e sem teste.
- Todo atributo novo de `GameRoom` precisa de categoria em `FOTO_SALA_CATEGORIAS` (`"efemero"`).
- Texto de interface: chaves PT/EN (`src/lang/*.js`); `python tools/dividas.py` e `python tools/test_interface.py` não podem piorar; nada de `t()` no nível de módulo; nenhum `t` local sombreando o tradutor; **nenhum `GS.on` duplicado** (GS.on substitui o ouvinte anterior).
- Edite `server.py`, `game.js`, `src/gameState.js` e `CLAUDE.md` **só com a ferramenta de edição** (substituição exata). Neste worktree os arquivos são LF; na árvore principal do autor são CRLF.
- Execução em worktree do `master`; commits só com caminhos explícitos; sem push sem pedido; trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Falhas que já existem no `master` e não são desta feature: `test_salvar_masmorra` [2] (atributos de marcadores cooperativos sem categoria), `test_interface.py` (2) e `test_sons_cliente.js` (2).

## Review Focus

- **Criatura voadora sobre a poça / criatura já atingida pela fonte:** não toma o choque (Task 2).
- **Dano de reação reentrando no motor:** não reentra; sem laço (Task 2).
- **Várias criaturas atingidas pela mesma ação na mesma poça:** um choque só (Task 2).
- **Fogo duas vezes na mesma mancha / mancha já em chamas:** uma zona só (Task 3).
- **Fonte sem criatura (casa vazia):** fogo em piche vazio ainda incendeia (Task 3 e 4).
- **Crosta de lava expirando com alguém em cima:** dano de lava normal no próximo turno (Task 3).
- **Frasco de piche sobre lava, água ou abismo:** não pinta nessas casas (Task 3).
- **Salvar e continuar com camadas e zonas ativas:** sobrevivem (Task 8).

---

## File Structure

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `terrain_reactions.py` | criar | Mixin `TerrainReactions`: tabela `REACOES`, `evento_elemental`, `_rx_registrar`, efeitos (choque, congelar, crosta, incendiar piche), helpers de região e camadas |
| `server.py` | modificar | herdar o mixin; atributos efêmeros + categorias; materiais; custo de movimento; frasco; zona `chamas_piche`; ganchos nos funis e nas fontes; payload `terrenos_temp` |
| `src/gameState.js` | modificar | custo do piche no BFS/caminho; caso `reacao_elemental`; item `frasco_piche` no catálogo |
| `src/reacoesElementais.js` | criar | Módulo puro `window.ReacoesElementais` (estilo da reação, crostas acabando, descrição de casa) |
| `game.js` | modificar | paletas/pintores dos materiais; animações 2D/3D; tooltip; pulso da crosta |
| `index.html` | modificar | carregar `src/reacoesElementais.js` |
| `src/lang/*.js` | modificar | chaves de materiais, item, narração, tooltip |
| `tools/export_catalog.py` / `tools/editor_catalog.js` | regenerar | `piche` e `lava_solidificada` na paleta do editor |
| `tools/test_terrain_reactions.py` | criar | testes do servidor |
| `tools/test_reacoes_cliente.js` | criar | testes do cliente |
| `CLAUDE.md`, spec | modificar | documentação |

---

### Task 1: Materiais `piche` e `lava_solidificada`

**Files:**
- Modify: `server.py` (`MATERIAIS` ~9466; `_water_step_cost` ~34544)
- Modify: `src/gameState.js` (`terrainMoveCost` ~1189)
- Modify: `game.js` (`MAT_PALETTE_2D` ~13339; seletor de textura 3D ~44060; pintores `paintLava`/`paintSwamp`)
- Modify: `src/lang/editor.js` (chaves `ui.editor.material.*`); regenerar `tools/editor_catalog.js` por `python tools/export_catalog.py`
- Test: `tools/test_terrain_reactions.py` (criar), `tools/test_reacoes_cliente.js` (criar)

**Interfaces:**
- Produces: materiais `piche` (`terreno="piche"`) e `lava_solidificada` (`terreno="crosta_lava"`); `_water_step_cost` devolve 2 para `piche`, 1 para `lava_solidificada`.

- [ ] **Step 1: Teste do servidor que falha** — crie `tools/test_terrain_reactions.py`:

```python
"""Reações elementais (terreno x elemento). Roda da raiz: python -X utf8 tools/test_terrain_reactions.py
Spec: docs/superpowers/specs/2026-10-13-reacoes-elementais-design.md
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S  # noqa: E402

PASS = 0
FAIL = 0


def check(nome, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        print(f"  ❌ {nome}")


def sala():
    """Sala 20x12 de chão, fase 'playing', sem rede; captura broadcasts e narração."""
    r = S.GameRoom("REACOES")
    r.msgs = []
    r.narr = []
    async def noop(*a, **k):
        pass
    async def bc(msg, *a, **k):
        r.msgs.append(msg)
    async def say(txt, *a, **k):
        r.narr.append(str(txt))
    r.gm_say = say; r.broadcast = bc; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 13):
        for x in range(1, 21):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 20, "h": 12, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    r.materiais = {}
    return r


def heroi(r, pid, nome, classe, pos):
    h = S.make_player(pid, nome, classe, len(r.players))
    h["pos"] = list(pos)
    r.players[pid] = h
    r.player_order = list(r.players)
    return h


def monstro(r, tipo, pos):
    d = next(d for d in S.MONSTER_DEFS if d["type"] == tipo)
    m = S.make_monster(d, {"id": 0, "cx": pos[0], "cy": pos[1]})
    m["pos"] = list(pos)
    r.monsters[m["id"]] = m
    return m


def pinta(r, material, tiles):
    for t in tiles:
        r.materiais[tuple(t)] = material
    r._rebuild_materiais_index()


def roda(coro):
    return asyncio.run(coro)


print("[1] materiais novos")
check("piche é piso com terreno piche",
      S.MATERIAIS["piche"]["categoria"] == "piso" and S.MATERIAIS["piche"]["terreno"] == "piche")
check("lava_solidificada é piso transitável",
      S.MATERIAIS["lava_solidificada"]["categoria"] == "piso"
      and not S.MATERIAIS["lava_solidificada"]["solido"])
r = sala()
h = heroi(r, "a", "Ana", "warrior", [2, 2])
pinta(r, "piche", [(5, 5)])
pinta(r, "lava_solidificada", [(6, 5)])
pinta(r, "lava", [(7, 5)])
check("entrar no piche custa 2", r._water_step_cost(h, 5, 5) == 2)
check("entrar na crosta custa 1", r._water_step_cost(h, 6, 5) == 1)
check("entrar na lava custa 2", r._water_step_cost(h, 7, 5) == 2)
check("a crosta não é lava", not r._is_lava_tile(6, 5) and r._is_lava_tile(7, 5))

print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar e ver falhar** — `python -X utf8 tools/test_terrain_reactions.py` → `KeyError: 'piche'`.

- [ ] **Step 3: Implementar no servidor.** Em `MATERIAIS` (ao lado de `pantano`) acrescente:

```python
    "piche":         _mat("Piche", "piso", "#1b1410", terreno="piche"),
    "lava_solidificada": _mat("Lava solidificada", "piso", "#3a2a26", terreno="crosta_lava"),
```
Em `_water_step_cost`, troque `if material in {"areia_deserto", "lava"}:` por `if material in {"areia_deserto", "lava", "piche"}:` (a crosta cai no custo normal 1 por não estar em nenhum conjunto).

Em `src/gameState.js`, em `terrainMoveCost`, troque a linha `if (kind === 'areia_deserto' || kind === 'lava') return Math.max(2 + custoElevacao, vento);` por `if (kind === 'areia_deserto' || kind === 'lava' || kind === 'piche') return Math.max(2 + custoElevacao, vento);`.

- [ ] **Step 4: Teste do cliente** — crie `tools/test_reacoes_cliente.js` seguindo o molde de `tools/test_chamado_inverno_cliente.js` (ele extrai `bfsReachable`/`findPath` reais de `src/gameState.js` com stubs; leia-o primeiro e copie o carregamento). Asserções desta etapa: (a) com `materiais` marcando uma faixa horizontal como `piche` e 4 de movimento, o alcance entra em no máximo 2 casas de piche; na mesma faixa de chão normal entra 4; (b) `lava_solidificada` custa como chão (4 casas); (c) `game.js` contém `piche` e `lava_solidificada` em `MAT_PALETTE_2D` (regex no fonte).

- [ ] **Step 5: Visual e catálogo.** Em `game.js`: acrescente a `MAT_PALETTE_2D`:

```javascript
  piche:       { base: [27, 20, 16], accent: 'pitch' },
  lava_solidificada: { base: [58, 42, 38], accent: 'crust' },
```
No seletor de textura 3D (`switch(matId)`, ao lado de `case 'lava'`): `case 'piche': paintPitch(c,0,0,S,r); break;` e `case 'lava_solidificada': paintCrust(c,0,0,S,r); break;`. Escreva `paintPitch` (fundo `#1b1410`, manchas brilhantes `rgba(255,255,255,.10)` e 6 bolhas pequenas) e `paintCrust` (fundo `#3a2a26`, placas irregulares `#2a1f1c`, fissuras `#d63b13` com opacidade .55) modelando-se em `paintLava`/`paintSwamp` (mesma assinatura `(c,x,y,S,r)`). Se o 2D usa `accent` por nome (procure o consumidor de `accent` com `lava`/`swamp`), acrescente os acentos `pitch` e `crust` no mesmo lugar.

- [ ] **Step 6: Nomes PT/EN e catálogo do editor.** Procure como `pantano` é traduzido (`"ui.editor.material.pantano"` em `src/lang/editor.js`) e acrescente `ui.editor.material.piche` (`pt: "Piche"`, `en: "Pitch"`) e `ui.editor.material.lava_solidificada` (`pt: "Lava solidificada"`, `en: "Solidified lava"`). Rode `python tools/export_catalog.py` (regenera `tools/editor_catalog.js`; confira com `git diff --stat` que só os dois materiais entraram). Rode `python tools/test_editor_idioma.py`.

- [ ] **Step 7: Rodar e ver passar** — `python -X utf8 tools/test_terrain_reactions.py`, `node tools/test_reacoes_cliente.js`, `node --check game.js`, `node tools/test_chamado_inverno_cliente.js`, `python -X utf8 tools/dividas.py`.

- [ ] **Step 8: Commit**

```bash
git add server.py src/gameState.js game.js src/lang/editor.js tools/editor_catalog.js tools/test_terrain_reactions.py tools/test_reacoes_cliente.js
git commit -m "feat: materiais piche e lava solidificada (movimento, visual e editor)"
```

---

### Task 2: Motor de reações + choque, congelar água e crosta de lava

**Files:**
- Create: `terrain_reactions.py`
- Modify: `server.py` (import + herança de `GameRoom`; `__init__` perto de `self._terrenos_inverno = {}` ~11440; `FOTO_SALA_CATEGORIAS` ~3563; `_processar_zonas_turno` ~34091)
- Modify: `src/lang/narracao.js`
- Test: `tools/test_terrain_reactions.py`

**Interfaces:**
- Produces (todas em `GameRoom` via mixin):
  - `evento_elemental(origem: dict)` — `@asynccontextmanager`; abre um escopo (reaproveita o aberto, se houver) e resolve ao sair.
  - `async _rx_registrar(elemento, casas, *, dano=None, atingidos=(), origem=None)` — soma casas ao escopo aberto; sem escopo, abre um implícito e resolve já. Ignora se `_rx_em_reacao` ou elemento fora de `RX_ELEMENTOS`.
  - `_rx_origem_atual(**kw)` — mescla campos (ex. `cd`, `dano`) na origem do escopo aberto.
  - `async _rx_registrar_alvo(alvo, elemento, dano, caster_id=None)` — atalho dos funis: registra as casas da criatura com `atingidos={alvo id}`.
  - `_rx_tiles_area(cx, cy, raio=None, lado=None) -> list[tuple]` — casas de chão de uma área.
  - `_rx_tiles_da(criatura) -> list[tuple]`, `_rx_estado(estado, tile) -> bool`, `_rx_regiao(sementes, pred, *, raio, teto) -> list[tuple]`, `_rx_encadear(elemento, casas, esc, profundidade)`.
  - Mensagem pública `reacao_elemental {tipo: "choque"|"incendio"|"congelar"|"crosta", casas:[[x,y]…], origem:[x,y]}`.
  - Atributos: `_rx_escopo`, `_rx_em_reacao`, `_rx_seq`.
- `REACOES` (lista de dicts) é módulo-nível e mutável (os testes injetam linhas).

- [ ] **Step 1: Testes que falham** (acrescente antes do resumo `print(f"\n{PASS} ok…")`):

```python
import terrain_reactions as TR

print("[2] constantes e tabela")
check("elementos canônicos iguais aos do servidor",
      (TR.RX_FIRE, TR.RX_COLD, TR.RX_LIGHTNING) == (S.DMG_FIRE, S.DMG_COLD, S.DMG_LIGHTNING))
ids = [l["id"] for l in TR.REACOES]
check("tabela tem as 4 reações ativas + gelo desligada",
      ids == ["choque_na_poca", "incendiar_piche", "congelar_agua", "crosta_de_lava", "derreter_gelo"]
      and [l["ativa"] for l in TR.REACOES] == [True, True, True, True, False])

print("[3] choque na poça")
r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
a = heroi(r, "a", "Ana", "mage", [3, 5])      # já atingida pelo raio
b = heroi(r, "b", "Bia", "warrior", [8, 5])    # na poça, não atingida
c = heroi(r, "c", "Cris", "warrior", [8, 8])   # fora da poça

async def raio_na_poca():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "a", "cd": 12}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10, atingidos={"a"})
roda(raio_na_poca())
check("quem estava na poça e não foi atingido toma o choque", b["hp"] < b["max_hp"])
check("quem já foi atingido não toma o choque", a["hp"] == a["max_hp"])
check("quem está fora da poça não toma", c["hp"] == c["max_hp"])
check("um broadcast de choque com as casas da poça",
      sum(1 for m in r.msgs if m.get("type") == "reacao_elemental" and m.get("tipo") == "choque") == 1)

r = sala()
pinta(r, "agua", [(x, 5) for x in range(1, 21)])           # poça comprida
longe = heroi(r, "l", "Longe", "warrior", [14, 5])          # a 11 do impacto
perto = heroi(r, "p", "Perto", "warrior", [8, 5])           # a 5 do impacto
async def raio2():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
roda(raio2())
check("raio 6: perto toma, longe não", perto["hp"] < perto["max_hp"] and longe["hp"] == longe["max_hp"])

r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
b = heroi(r, "b", "Bia", "warrior", [6, 5])
v = heroi(r, "v", "Vera", "warrior", [7, 5])
v["voo"] = True; v["altura"] = 3
async def raio3():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
roda(raio3())
check("voador sobre a poça não toma o choque", v["hp"] == v["max_hp"] and b["hp"] < b["max_hp"])

r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
b = heroi(r, "b", "Bia", "warrior", [6, 5]); d = heroi(r, "d", "Davi", "warrior", [7, 5])
async def raio4():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
        await r._rx_registrar(S.DMG_LIGHTNING, [(4, 5)], dano=10)   # segunda criatura atingida na mesma ação
roda(raio4())
check("duas notificações na mesma ação: um choque só",
      sum(1 for m in r.msgs if m.get("tipo") == "choque") == 1)

r = sala()
pinta(r, "agua_profunda", [(x, 5) for x in range(3, 10)])
b = heroi(r, "b", "Bia", "warrior", [6, 5])
async def raio5():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
roda(raio5())
check("água profunda não conduz (v1)", b["hp"] == b["max_hp"])

print("[4] frio: congelar água e crosta de lava")
r = sala()
pinta(r, "agua", [(5, 5), (6, 5)])
b = heroi(r, "b", "Bia", "warrior", [5, 5]); b["moves_left"] = 6
async def frio():
    async with r.evento_elemental({"tipo": "magia", "id": "raio_congelante", "caster_id": "x", "cd": 99}):
        await r._rx_registrar(S.DMG_COLD, [(5, 5), (6, 5)])
roda(frio())
check("água vira piso congelado", r.materiais[(5, 5)] == "piso_congelado" and r.materiais[(6, 5)] == "piso_congelado")
check("quem falha no Reflexos perde o movimento (CD 99)", b["moves_left"] == 0 and b.get("movimento_perdido"))
r.round_num = 3
r._expirar_terrenos_inverno()
check("ainda congelada na rodada 3", r.materiais[(5, 5)] == "piso_congelado")
r.round_num = 4
r._expirar_terrenos_inverno()
check("volta a ser água na rodada 4 (3 rodadas)", r.materiais[(5, 5)] == "agua")

r = sala()
pinta(r, "lava", [(8, 5)])
async def frio2():
    async with r.evento_elemental({"tipo": "magia", "id": "raio_congelante", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_COLD, [(8, 5)])
roda(frio2())
check("lava vira lava_solidificada", r.materiais[(8, 5)] == "lava_solidificada" and not r._is_lava_tile(8, 5))
r.round_num = 4
r._expirar_terrenos_inverno()
check("a lava volta depois de 3 rodadas", r._is_lava_tile(8, 5))

r = sala()
pinta(r, "lava", [(8, 5)])
r._aplicar_camadas_terreno_inverno([(8, 5)], "lava", "ira_1", permanente=False, expira_em=10)   # lava da Ira
async def frio3():
    async with r.evento_elemental({"tipo": "magia", "id": "raio_congelante", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_COLD, [(8, 5)])
roda(frio3())
check("lava da Ira também vira crosta", r.materiais[(8, 5)] == "lava_solidificada")
r.round_num = 4
r._expirar_terrenos_inverno()
check("ao acabar a crosta, a lava da Ira (ainda ativa) volta", r._is_lava_tile(8, 5))

print("[5] travas")
r = sala()
pinta(r, "agua", [(x, 5) for x in range(3, 10)])
b = heroi(r, "b", "Bia", "warrior", [6, 5])
vezes = []
orig = S.GameRoom._rx_choque
async def espiao(self, tiles, origem, pend, prof):
    vezes.append(1)
    return await orig(self, tiles, origem, pend, prof)
S.GameRoom._rx_choque = espiao
async def reentrada():
    async with r.evento_elemental({"tipo": "magia", "id": "relampago", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_LIGHTNING, [(3, 5)], dano=10)
roda(reentrada())
S.GameRoom._rx_choque = orig
check("o dano do choque não reentra no motor (um choque, não um por vítima)", len(vezes) == 1)

# cadeia: linha de teste fogo->fogo que se encadeia sempre; o limite é profundidade 2
r = sala()
pinta(r, "piche", [(5, 5)])
conta = []
async def _rx_teste_cadeia(self, tiles, origem, pend, prof):
    conta.append(prof)
    await self._rx_encadear(TR.RX_FIRE, tiles, {"origem": origem, "pend": {}}, prof)
S.GameRoom._rx_teste_cadeia = _rx_teste_cadeia
TR.REACOES.append({"id": "teste", "elemento": TR.RX_FIRE, "estado": "piche", "efeito": "_rx_teste_cadeia", "ativa": True})
# desliga a linha real de incendiar para isolar o teste de cadeia
real = next(l for l in TR.REACOES if l["id"] == "incendiar_piche")
real["ativa"] = False
async def cadeia():
    async with r.evento_elemental({"tipo": "teste", "caster_id": "x"}):
        await r._rx_registrar(TR.RX_FIRE, [(5, 5)])
roda(cadeia())
TR.REACOES[:] = [l for l in TR.REACOES if l["id"] != "teste"]
real["ativa"] = True
check("cadeia respeita a profundidade máxima 2 (prof 0,1,2)", conta == [0, 1, 2])

print(f"\n{PASS} ok, {FAIL} falhas")
sys.exit(1 if FAIL else 0)
```
(Remova o `print(f"\n{PASS} ok…")`/`sys.exit` duplicados do Step 1 da Task 1: o arquivo termina com um só resumo, no fim.)

- [ ] **Step 2: Rodar e ver falhar** — `ModuleNotFoundError: terrain_reactions`.

- [ ] **Step 3: Implementar o mixin** (`terrain_reactions.py`):

```python
"""Reações elementais (terreno × elemento).

Mixin de GameRoom. Cada fonte elementar diz "este elemento atingiu estas casas"
(`_rx_registrar`) dentro de um escopo por ação (`evento_elemental`); ao fim da
ação o escopo resolve cada linha de `REACOES` UMA vez sobre a união das casas
(é o dedupe por evento). Mudanças de terreno usam o registro de camadas
temporárias do Chamado do Inverno (`_aplicar_camadas_terreno_inverno`).

Spec: docs/superpowers/specs/2026-10-13-reacoes-elementais-design.md
"""
import contextlib

# Mesmos valores de server.DMG_FIRE / DMG_COLD / DMG_LIGHTNING (um teste confere).
RX_FIRE = "fire"
RX_COLD = "cold"
RX_LIGHTNING = "lightning"
RX_ELEMENTOS = (RX_FIRE, RX_COLD, RX_LIGHTNING)

RX_PROFUNDIDADE_MAX = 2
RX_CHOQUE_RAIO = 6
RX_CHOQUE_TETO = 24
RX_PICHE_TETO = 40
RX_DURACAO_GELO = 3
RX_DURACAO_CROSTA = 3
RX_CD_PADRAO = 12

# Tabela de dados: elemento × estado da casa → efeito (nome do método).
# `efeito: None` + `ativa: False` = linha reservada (fogo + gelo, fora da v1).
REACOES = [
    {"id": "choque_na_poca",  "elemento": RX_LIGHTNING, "estado": "agua_rasa", "efeito": "_rx_choque",          "ativa": True},
    {"id": "incendiar_piche", "elemento": RX_FIRE,      "estado": "piche",     "efeito": "_rx_incendiar_piche", "ativa": True},
    {"id": "congelar_agua",   "elemento": RX_COLD,      "estado": "agua_rasa", "efeito": "_rx_congelar_agua",   "ativa": True},
    {"id": "crosta_de_lava",  "elemento": RX_COLD,      "estado": "lava",      "efeito": "_rx_crosta_lava",     "ativa": True},
    {"id": "derreter_gelo",   "elemento": RX_FIRE,      "estado": "gelo",      "efeito": None,                  "ativa": False},
]


class TerrainReactions:
    # ── escopo por ação ──────────────────────────────────────────────────────
    @contextlib.asynccontextmanager
    async def evento_elemental(self, origem):
        """Abre o escopo de uma ação; aninhado reaproveita o escopo aberto."""
        if self._rx_escopo is not None:
            yield self._rx_escopo
            return
        esc = {"origem": dict(origem or {}), "pend": {}}
        self._rx_escopo = esc
        try:
            yield esc
        finally:
            self._rx_escopo = None
        await self._rx_resolver(esc, 0)

    def _rx_origem_atual(self, **kw):
        if self._rx_escopo is not None:
            self._rx_escopo["origem"].update({k: v for k, v in kw.items() if v is not None})

    async def _rx_registrar(self, elemento, casas, *, dano=None, atingidos=(), origem=None):
        if self._rx_em_reacao or elemento not in RX_ELEMENTOS or not casas:
            return
        implicito = self._rx_escopo is None
        esc = self._rx_escopo if not implicito else {"origem": dict(origem or {}), "pend": {}}
        pend = esc["pend"].setdefault(elemento, {"casas": set(), "dano": 0, "atingidos": set()})
        pend["casas"].update((int(x), int(y)) for x, y in casas)
        if dano:
            pend["dano"] = max(pend["dano"], int(dano))
        pend["atingidos"].update(atingidos)
        if origem and not implicito:
            esc["origem"].update({k: v for k, v in origem.items() if v is not None})
        if implicito:
            await self._rx_resolver(esc, 0)

    async def _rx_registrar_alvo(self, alvo, elemento, dano, caster_id=None):
        """Atalho dos funis de dano: registra as casas da criatura atingida."""
        if elemento not in RX_ELEMENTOS or self._rx_em_reacao:
            return
        await self._rx_registrar(
            elemento, self._rx_tiles_da(alvo), dano=dano,
            atingidos={alvo.get("id")}, origem={"tipo": "dano", "caster_id": caster_id})

    # ── geometria e estado das casas ────────────────────────────────────────
    def _rx_tiles_da(self, criatura):
        pos = criatura.get("pos")
        if not isinstance(pos, (list, tuple)) or len(pos) < 2:
            return []
        if self.monsters.get(criatura.get("id")) is criatura:
            return [(int(x), int(y)) for x, y in self._monster_tiles(criatura)]
        return [(int(pos[0]), int(pos[1]))]

    def _rx_tiles_area(self, cx, cy, raio=None, lado=None):
        """Casas de chão de uma área quadrada: `lado` explícito, ou o quadrado de
        raio Chebyshev `raio` (lado 2*raio+1, âncora simétrica)."""
        lado = int(lado) if lado else 2 * int(raio or 0) + 1
        return [(int(x), int(y)) for x, y in self._inverno_area_tiles(cx, cy, lado)]

    def _rx_estado(self, estado, tile):
        x, y = tile
        mat = self.materiais.get((x, y))
        if estado == "agua_rasa":
            return self._water_tile_kind(x, y) == "agua"
        if estado == "piche":
            return mat == "piche" and not self._ponte_em(x, y)
        if estado == "lava":
            return self._is_lava_tile(x, y)
        if estado == "gelo":
            return mat in {"piso_congelado", "planicie_nevada"}
        return False

    def _rx_regiao(self, sementes, pred, *, raio, teto):
        """Casas conectadas (4 vizinhos) que satisfazem `pred`, a partir das
        sementes, dentro de `raio` (Chebyshev, None = sem limite) e até `teto`."""
        sem = sorted({tuple(s) for s in sementes if pred(tuple(s))}, key=lambda t: (t[1], t[0]))
        vistos = list(sem)
        conj = set(sem)
        i = 0
        while i < len(vistos) and len(vistos) < teto:
            x, y = vistos[i]
            i += 1
            for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
                n = (x + dx, y + dy)
                if n in conj or not pred(n):
                    continue
                if raio is not None and min(max(abs(n[0] - s[0]), abs(n[1] - s[1])) for s in sem) > raio:
                    continue
                conj.add(n)
                vistos.append(n)
                if len(vistos) >= teto:
                    break
        return vistos[:teto]

    # ── resolução ───────────────────────────────────────────────────────────
    async def _rx_resolver(self, esc, profundidade):
        if profundidade > RX_PROFUNDIDADE_MAX:
            return
        antes = self._rx_em_reacao
        self._rx_em_reacao = True
        try:
            for elemento in sorted(esc["pend"]):
                pend = esc["pend"][elemento]
                casas = sorted(pend["casas"], key=lambda t: (t[1], t[0]))
                for linha in REACOES:
                    if not linha["ativa"] or not linha["efeito"] or linha["elemento"] != elemento:
                        continue
                    alvo_casas = [t for t in casas if self._rx_estado(linha["estado"], t)]
                    if not alvo_casas:
                        continue
                    await getattr(self, linha["efeito"])(alvo_casas, esc["origem"], pend, profundidade)
        finally:
            self._rx_em_reacao = antes

    async def _rx_encadear(self, elemento, casas, esc, profundidade):
        """Uma reação que dispara outra: novo escopo, profundidade + 1."""
        filho = {"origem": dict(esc.get("origem", {})),
                 "pend": {elemento: {"casas": {tuple(c) for c in casas}, "dano": 0, "atingidos": set()}}}
        await self._rx_resolver(filho, profundidade + 1)

    def _rx_id(self, tipo):
        self._rx_seq += 1
        return f"rx_{tipo}_{self.round_num}_{self._rx_seq}"

    async def _rx_anunciar(self, tipo, casas, origem_pos):
        await self.broadcast({"type": "reacao_elemental", "tipo": tipo,
                              "casas": [list(c) for c in casas], "origem": list(origem_pos)})

    # ── efeitos ─────────────────────────────────────────────────────────────
    async def _rx_choque(self, tiles, origem, pend, prof):
        regiao = self._rx_regiao(tiles, lambda t: self._rx_estado("agua_rasa", t),
                                 raio=RX_CHOQUE_RAIO, teto=RX_CHOQUE_TETO)
        await self._rx_anunciar("choque", regiao, tiles[0])
        await self.gm_say(self._rx_T("narracao.reacao.choque"))
        base = int(pend.get("dano") or origem.get("dano") or 0)
        if base <= 0:
            return
        cd = int(origem.get("cd") or RX_CD_PADRAO)
        for alvo in self._alvos_no_inverno(regiao):
            if alvo.get("id") in pend["atingidos"] or self._voo_imune_terreno(alvo):
                continue
            ok, *_ = await self._save_mostrado(alvo, "reflexos", cd, mitigacao="half_damage")
            d = max(1, base // 2)
            if ok:
                d = max(1, d // 2)
            if "vida_atual" not in alvo:
                d = self._apply_damage_types(d, [RX_LIGHTNING], alvo)
            if d > 0:
                await self._dano_em_alvo(alvo, d, "eletricidade", origem.get("caster_id"))

    async def _rx_congelar_agua(self, tiles, origem, pend, prof):
        zid = self._rx_id("gelo")
        self._aplicar_camadas_terreno_inverno(
            tiles, "piso_congelado", zid, permanente=False,
            expira_em=self.round_num + RX_DURACAO_GELO)
        await self._rx_anunciar("congelar", tiles, tiles[0])
        await self.gm_say(self._rx_T("narracao.reacao.congelar"))
        cd = int(origem.get("cd") or RX_CD_PADRAO)
        for alvo in self._alvos_no_inverno(tiles):
            if self._voo_imune_terreno(alvo):
                continue
            ok, *_ = await self._save_mostrado(alvo, "reflexos", cd)
            if not ok:
                alvo["moves_left"] = 0
                alvo["movimento_perdido"] = True

    async def _rx_crosta_lava(self, tiles, origem, pend, prof):
        zid = self._rx_id("crosta")
        self._aplicar_camadas_terreno_inverno(
            tiles, "lava_solidificada", zid, permanente=False,
            expira_em=self.round_num + RX_DURACAO_CROSTA)
        await self._rx_anunciar("crosta", tiles, tiles[0])
        await self.gm_say(self._rx_T("narracao.reacao.crosta"))
```
Notas de integração (resolva lendo o código real; não mude o comportamento descrito):
- O mixin não importa `server`. No corpo de `GameRoom` (em `server.py`) defina estes dois adaptadores, que o mixin usa:
```python
    def _rx_T(self, chave, **kw):
        return T(chave, **kw)

    def _rx_altura(self, alvo):
        """1 se a criatura está acima do piso (voando), senão 0."""
        return 1 if normalizar_altura(alvo.get("altura", ALTURA_MIN)) > ALTURA_MIN else 0
```
- Em `_save_mostrado` confira a assinatura real (`alvo, tipo, dif, extra_mod=0, desvantagem=False, …, mitigacao=…`) e o retorno `(ok, …)`; ajuste os kwargs se necessário.

No `server.py`:
1. Junto ao import de `monster_intent`: `from terrain_reactions import TerrainReactions`; `class GameRoom(TutorialTraining, MonsterIntent, TerrainReactions):`.
2. No `__init__`, ao lado de `self._terrenos_inverno = {}`:
```python
        self._rx_escopo = None     # escopo da ação em curso (TerrainReactions)
        self._rx_em_reacao = False # True enquanto uma reação aplica dano: não reentra
        self._rx_seq = 0           # ids únicos de camadas de reação
```
3. `FOTO_SALA_CATEGORIAS`: `"_rx_escopo": "efemero", "_rx_em_reacao": "efemero", "_rx_seq": "efemero",`.
4. Junto ao `__init__`/`_voltar_para_cidade`/nova masmorra onde `_terrenos_inverno` é zerado (linhas ~15619 e ~16695), zere também `self._rx_escopo = None; self._rx_em_reacao = False`.
5. Narração em `src/lang/narracao.js` (formato das entradas vizinhas): `narracao.reacao.choque` (pt "⚡ O raio corre pela poça!", en "⚡ The lightning surges through the pool!"), `narracao.reacao.congelar` (pt "❄️ A água congela!", en "❄️ The water freezes over!"), `narracao.reacao.crosta` (pt "❄️ A lava endurece numa crosta escura.", en "❄️ The lava hardens into a dark crust.").

- [ ] **Step 4: Rodar e ver passar** — `python -X utf8 tools/test_terrain_reactions.py` (todas as seções); `python -X utf8 tools/test_salvar_masmorra.py` (os atributos `_rx_*` não podem aparecer na lista de falhas); `python -X utf8 tools/test_narracao.py`; `python -X utf8 tools/dividas.py`.

- [ ] **Step 5: Commit**

```bash
git add terrain_reactions.py server.py src/lang/narracao.js tools/test_terrain_reactions.py
git commit -m "feat: motor de reações elementais (choque, congelar água, crosta de lava)"
```

---

### Task 3: Piche em chamas, gancho da criatura em chamas e frasco de piche

**Files:**
- Modify: `terrain_reactions.py` (efeito `_rx_incendiar_piche`, `_rx_fogo_piche`, `_consumir_piche`, `_rx_alvo_na_zona`)
- Modify: `server.py` (`ARREMESSAVEIS` ~7267; loja `SHOP_MERCHANT` ~7186; `_throw_item_area` ~20972; `_processar_zonas_turno` ~34091; `_processar_zona_molochus_inicio_turno` ~38300; `_verificar_entrada_zona_molochus` ~38307; `_aplicar_lava_se_pisar` ~34624)
- Modify: `src/gameState.js` (`CATALOGO_ITENS` ~673), `src/lang/catalogo.js` (via `python tools/gerar_vocabulario.py`), `src/lang/narracao.js`
- Test: `tools/test_terrain_reactions.py`

**Interfaces:**
- Consumes: Task 2 (`_rx_regiao`, `_rx_estado`, `_rx_anunciar`, `_rx_id`, `evento_elemental`).
- Produces: zona `{"tipo":"chamas_piche","tiles":[[x,y]…],"expira_em":int,"ativa":True,"caster":id}`; `_consumir_piche(tiles)`; `_rx_fogo_piche(alvo, zona, motivo)`; item `frasco_piche` em `ARREMESSAVEIS` com `"terreno": {"material": "piche", "duracao": 4}`.

- [ ] **Step 1: Testes que falham** (antes do resumo final):

```python
print("[6] piche em chamas")
r = sala()
pinta(r, "piche", [(5, 5), (6, 5), (7, 5), (12, 9)])      # (12,9) é outra mancha, não conectada
no_piche = heroi(r, "a", "Ana", "warrior", [6, 5])
fora = heroi(r, "b", "Bia", "warrior", [10, 10])
async def fogo():
    async with r.evento_elemental({"tipo": "magia", "id": "bola_fogo", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_FIRE, [(5, 5)])           # casa sem ninguém
roda(fogo())
zonas = [z for z in r.zonas_especiais if z.get("tipo") == "chamas_piche" and z.get("ativa")]
check("cria UMA zona de chamas de piche", len(zonas) == 1)
check("a zona cobre a mancha conectada e não a outra",
      sorted(map(tuple, zonas[0]["tiles"])) == [(5, 5), (6, 5), (7, 5)])
check("a casa atingida (5,5) estava vazia: a fonte sem criatura incendiou mesmo assim",
      (5, 5) in {tuple(t) for t in zonas[0]["tiles"]} and no_piche["pos"] != [5, 5])
check("quem estava na mancha sofre na ignição", no_piche["hp"] < no_piche["max_hp"])
check("quem estava fora não sofre", fora["hp"] == fora["max_hp"])
check("quem estava na mancha fica em chamas", no_piche.get("em_chamas_rodadas", 0) > 0)
async def fogo2():
    async with r.evento_elemental({"tipo": "magia", "id": "bola_fogo", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_FIRE, [(6, 5)])
roda(fogo2())
check("fogo de novo na mancha já em chamas: não cria outra zona",
      len([z for z in r.zonas_especiais if z.get("tipo") == "chamas_piche" and z.get("ativa")]) == 1)

# início do turno e entrada
hp0 = no_piche["hp"]
roda(r._processar_zona_molochus_inicio_turno(no_piche))
check("início do turno na mancha em chamas causa dano", no_piche["hp"] < hp0)
entra = heroi(r, "c", "Cris", "warrior", [3, 5])
hp0 = entra["hp"]
roda(r._verificar_entrada_zona_molochus(entra, 5, 5))
check("entrar na mancha em chamas causa dano", entra["hp"] < hp0)

# voador não é atingido
r2 = sala()
pinta(r2, "piche", [(5, 5), (6, 5)])
voa = heroi(r2, "v", "Vera", "warrior", [5, 5]); voa["voo"] = True; voa["altura"] = 3
async def fogo3():
    async with r2.evento_elemental({"tipo": "magia", "id": "bola_fogo", "caster_id": "x"}):
        await r2._rx_registrar(S.DMG_FIRE, [(5, 5)])
roda(fogo3())
check("voador sobre a mancha não é atingido", voa["hp"] == voa["max_hp"])

# fim das chamas: piche autoral vira pedra_negra; mancha temporária volta ao material original
r.round_num = 4
roda(r._processar_zonas_turno())
check("a zona acaba na rodada 4", not any(z.get("ativa") for z in r.zonas_especiais if z.get("tipo") == "chamas_piche"))
check("piche autoral consumido vira pedra_negra", r.materiais[(5, 5)] == "pedra_negra")
check("a outra mancha segue intacta", r.materiais[(12, 9)] == "piche")

r = sala()
pinta(r, "terra", [(5, 5), (6, 5)])
r._aplicar_camadas_terreno_inverno([(5, 5), (6, 5)], "piche", "frasco_1", permanente=False, expira_em=5)
async def fogo4():
    async with r.evento_elemental({"tipo": "item", "id": "bomba_incendiaria", "caster_id": "x"}):
        await r._rx_registrar(S.DMG_FIRE, [(5, 5)])
roda(fogo4())
r.round_num = 4
roda(r._processar_zonas_turno())
check("mancha temporária consumida volta ao material original", r.materiais[(5, 5)] == "terra" and r.materiais[(6, 5)] == "terra")

# gancho: criatura em chamas entra no piche
r = sala()
pinta(r, "piche", [(5, 5), (6, 5)])
g = heroi(r, "g", "Gus", "warrior", [5, 5]); g["em_chamas_rodadas"] = 2
roda(r._aplicar_lava_se_pisar(g))
check("criatura em chamas sobre piche incendeia a mancha",
      any(z.get("tipo") == "chamas_piche" and z.get("ativa") for z in r.zonas_especiais))
r = sala()
pinta(r, "piche", [(5, 5), (6, 5)])
g = heroi(r, "g", "Gus", "warrior", [5, 5])
roda(r._aplicar_lava_se_pisar(g))
check("criatura que NÃO está em chamas não incendeia", not r.zonas_especiais)

print("[7] frasco de piche")
d = S.ARREMESSAVEIS["frasco_piche"]
check("frasco de piche: área, sem dano, terreno piche por 4 rodadas",
      d["alvo"] == "area" and not d.get("dano") and d["terreno"] == {"material": "piche", "duracao": 4})
r = sala()
pinta(r, "lava", [(9, 9)])
pinta(r, "agua", [(9, 8)])
h = heroi(r, "a", "Ana", "warrior", [8, 7]); h["bag"] = [{"id": "frasco_piche", "name": "Frasco de Piche", "emoji": "🛢️"}]
h["action_done"] = False
roda(r._throw_item_area(h, d, h["bag"][0], 8, 9, None))
pintadas = [t for t, m in r.materiais.items() if m == "piche"]
check("pinta o 3x3 em volta (9 casas), menos a lava e a água (7 casas)",
      (7, 8) in pintadas and (8, 9) in pintadas
      and (9, 9) not in pintadas and (9, 8) not in pintadas and len(pintadas) == 7)
r.round_num = 5
r._expirar_terrenos_inverno()
check("o piche do frasco some depois de 4 rodadas", not any(m == "piche" for m in r.materiais.values()))
```

- [ ] **Step 2: Rodar e ver falhar** — `AttributeError: _rx_incendiar_piche` / `KeyError: 'frasco_piche'`.

- [ ] **Step 3: Efeitos no mixin** (acrescente a `terrain_reactions.py`, dentro de `TerrainReactions`; adicione `RX_DURACAO_CHAMAS = 3` e `RX_DADO_CHAMAS = "1d6"` no topo do módulo):

```python
    # ── piche em chamas ─────────────────────────────────────────────────────
    def _rx_em_zona_chamas(self, tile):
        for z in self.zonas_especiais:
            if z.get("tipo") == "chamas_piche" and z.get("ativa") \
                    and any((int(a), int(b)) == tile for a, b in z.get("tiles", [])):
                return True
        return False

    def _rx_alvo_na_zona(self, alvo, zona):
        area = {(int(a), int(b)) for a, b in zona.get("tiles", [])}
        return any(t in area for t in self._rx_tiles_da(alvo))

    async def _rx_incendiar_piche(self, tiles, origem, pend, prof):
        regiao = self._rx_regiao(
            tiles, lambda t: self._rx_estado("piche", t) and not self._rx_em_zona_chamas(t),
            raio=None, teto=RX_PICHE_TETO)
        if not regiao:
            return
        zona = {"id": self._rx_id("chamas_piche"), "tipo": "chamas_piche",
                "tiles": [list(t) for t in regiao], "criado_em": self.round_num,
                "expira_em": self.round_num + RX_DURACAO_CHAMAS, "ativa": True,
                "caster": origem.get("caster_id")}
        self.zonas_especiais.append(zona)
        await self._rx_anunciar("incendio", regiao, tiles[0])
        await self.gm_say(self._rx_T("narracao.reacao.piche_pegou_fogo"))
        for alvo in self._alvos_no_inverno(regiao):
            await self._rx_fogo_piche(alvo, zona, "ignição")

    async def _rx_fogo_piche(self, alvo, zona, motivo):
        """1d6 de fogo + em chamas, só no piso. Não reentra no motor."""
        if not self._vivo(alvo) or self._voo_imune_terreno(alvo):
            return
        if self._rx_altura(alvo) > 0:
            return
        antes = self._rx_em_reacao
        self._rx_em_reacao = True
        try:
            raw = self._rolar_dado(RX_DADO_CHAMAS)
            await self.broadcast({"type": "dice_roll", "die": "d6", "value": raw,
                                  "label": self._rx_T("dado.chamas_de_piche"),
                                  "damage_type": RX_FIRE})
            dano = raw if "vida_atual" in alvo else self._apply_damage_types(raw, [RX_FIRE], alvo)
            await self._dano_em_alvo(alvo, dano, "fogo", zona.get("caster"))
            if self._vivo(alvo):
                self._aplicar_em_chamas(alvo, self._rolar_dado("1d4"), True)
        finally:
            self._rx_em_reacao = antes

    def _consumir_piche(self, tiles):
        """O fogo consumiu o piche: mancha temporária volta ao material original;
        piche pintado no editor (base == piche) vira pedra_negra."""
        for t in (tuple(x) for x in tiles):
            reg = self._terrenos_inverno.get(t)
            if reg:
                reg["camadas"] = [c for c in reg.get("camadas", []) if c.get("material") != "piche"]
                if reg["camadas"]:
                    self.materiais[t] = reg["camadas"][-1]["material"]
                else:
                    base = reg.get("base")
                    novo = "pedra_negra" if base == "piche" else base
                    if novo is None:
                        self.materiais.pop(t, None)
                    else:
                        self.materiais[t] = novo
                    self._terrenos_inverno.pop(t, None)
            elif self.materiais.get(t) == "piche":
                self.materiais[t] = "pedra_negra"
        self._rebuild_materiais_index()
```
`_rx_altura(alvo)` e `_rx_T(chave)` já foram definidos em `server.py` na Task 2 (adaptadores do mixin); só use-os.

- [ ] **Step 4: Ganchos em `server.py`.**
  - `_processar_zonas_turno`: acrescente à cadeia `elif z.get("tipo") == …` (ao lado de `molochus_chamas`):
```python
            elif z.get("tipo") == "chamas_piche":
                if self.round_num >= int(z.get("expira_em", 0) or 0):
                    z["ativa"] = False
                    self._consumir_piche(z.get("tiles", []))
                    await self.gm_say(T("narracao.reacao.piche_consumido"))
```
  - `_processar_zona_molochus_inicio_turno(self, alvo)`: **antes** do laço existente, acrescente
```python
        for zona in list(self.zonas_especiais):
            if zona.get("tipo") == "chamas_piche" and zona.get("ativa") and self._rx_alvo_na_zona(alvo, zona):
                await self._rx_fogo_piche(alvo, zona, "início do turno")
                if not self._vivo(alvo):
                    return
```
  - `_verificar_entrada_zona_molochus(self, alvo, nx, ny)`: **antes** do laço existente, acrescente
```python
        for zona in list(self.zonas_especiais):
            if zona.get("tipo") == "chamas_piche" and zona.get("ativa") \
                    and any((int(a), int(b)) == (nx, ny) for a, b in zona.get("tiles", [])):
                await self._rx_fogo_piche(alvo, zona, "entrada")
                if not self._vivo(alvo):
                    return
                break
```
  (Os dois ganham um comentário `# também serve às chamas de piche (reações elementais)`; assim os 4 pontos de início de turno e os 3 de entrada que já chamam estas funções valem sem tocar neles.)
  - `_aplicar_lava_se_pisar`: logo **depois** de `if not criatura or self._voo_imune_terreno(criatura): return` e **antes** de `lava = self._lava_tiles_of(criatura)`:
```python
        if criatura.get("em_chamas_rodadas", 0) > 0:      # gancho: criatura em chamas inflama o piche
            await self._rx_registrar(
                DMG_FIRE, self._rx_tiles_da(criatura),
                origem={"tipo": "criatura_em_chamas", "id": criatura.get("id")})
```
  - `ARREMESSAVEIS` (ao lado de `bomba_fumaca`):
```python
    "frasco_piche": {
        "id": "frasco_piche", "name": "Frasco de Piche", "emoji": "🛢️",
        "alcance": 4, "alvo": "area", "area_raio": 1,
        "terreno": {"material": "piche", "duracao": 4},
    },
```
  - `_throw_item_area`: depois do bloco `zona = defn.get("zona") …` e **antes** de `await self.push_state()`:
```python
        terreno = defn.get("terreno")
        if terreno:
            casas = [t for t in self._inverno_area_tiles(cx, cy, 3)
                     if not self._water_tile_kind(t[0], t[1]) and not self._is_lava_tile(t[0], t[1])
                     and self.materiais.get((t[0], t[1])) not in {"ceu_abismo"}
                     and not self._ponte_em(t[0], t[1])]
            if casas:
                self._aplicar_camadas_terreno_inverno(
                    casas, terreno["material"], self._rx_id("frasco"), permanente=False,
                    expira_em=self.round_num + int(terreno.get("duracao", 4)))
                await self.gm_say(T("narracao.reacao.piche_espalhado"))
```
  - Loja: em `SHOP_MERCHANT`, ao lado da entrada `frasco_oleo`: `{"id": "frasco_piche", "name": "Frasco de Piche", "emoji": "🛢️", "price": 12, "item_slot": "bag", "effect": "throwable", "value": 0},`.
  - Narração PT/EN em `src/lang/narracao.js`: `narracao.reacao.piche_pegou_fogo` ("🔥 O piche pega fogo!" / "🔥 The pitch catches fire!"), `narracao.reacao.piche_consumido` ("As chamas consomem o piche." / "The flames burn away the pitch."), `narracao.reacao.piche_espalhado` ("🛢️ O piche se espalha pelo chão." / "🛢️ Pitch spreads across the ground."); rótulo de dado `dado.chamas_de_piche` ("Chamas de piche" / "Pitch fire") no arquivo onde vivem as chaves `dado.*`.
  - Cliente (`src/gameState.js`, `CATALOGO_ITENS`, após `bomba_fumaca`):
```javascript
    frasco_piche: {
      id: 'frasco_piche', nome: 'Frasco de Piche', emoji: '🛢️',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alvo: 'area',
      alcance: 4, areaRaio: 1, duracao: 4, permitidoPara:['todos'],
      descricao: 'Área (raio 1, alcance 4). Espalha piche por 4 rodadas — o chão fica lento ' +
                 'e INFLAMÁVEL. Sem dano.',
    },
```
  - Vocabulário: `python tools/gerar_vocabulario.py` (cria `cat.item.frasco_piche.nome`); preencha o `en` ("Pitch Flask") em `src/lang/catalogo.js` e a descrição `ui.item.frasco_piche.desc` se o gerador/placar pedir (siga o molde de `bomba_fumaca`). Rode `python -X utf8 tools/test_vocabulario.py` e `node tools/test_vocabulario_cliente.js`.

- [ ] **Step 5: Rodar e ver passar** — `python -X utf8 tools/test_terrain_reactions.py`; `python -X utf8 tools/test_narracao.py`; `python -X utf8 tools/test_salvar_masmorra.py` (sem atributos novos fora da lista de falhas conhecida); `python -X utf8 tools/dividas.py`.

- [ ] **Step 6: Commit**

```bash
git add terrain_reactions.py server.py src/gameState.js src/lang/catalogo.js src/lang/narracao.js tools/test_terrain_reactions.py
git commit -m "feat: piche em chamas, gancho da criatura em chamas e frasco de piche"
```

---

### Task 4: Fontes — escopos, funis, magias e itens

**Files:**
- Modify: `server.py` (`_aplicar_dano_alvo` ~30172; `_dano_em_alvo` ~36926; `_executar_magia_grimorio` ~28723; `handle_throw_item`/`_throw_item_alvo`/`_throw_item_area` ~20972; executores `_executar_bola_fogo` ~33081, `_executar_relampago` ~33298, `_executar_raio_congelante` ~33373, `_executar_prisao_chamas` ~32291, `_processar_zona_bola_fogo` ~33197; `_executar_tempestade_ciclones` ~31929)
- Modify: `terrain_reactions.py` (constante `FONTES_COM_REGISTRO`)
- Test: `tools/test_terrain_reactions.py`

**Interfaces:**
- Consumes: Task 2 (`evento_elemental`, `_rx_registrar`, `_rx_registrar_alvo`, `_rx_origem_atual`, `_rx_tiles_area`).
- Produces: `FONTES_COM_REGISTRO` — dict `nome_da_função_do_servidor → elemento` das fontes que chamam `_rx_registrar` no próprio corpo (o teste estático confere por AST).

- [ ] **Step 1: Teste estático e de cenário que falham** (antes do resumo):

```python
print("[8] fontes de magia e item")
import ast
fonte = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py"), encoding="utf-8").read()
arvore = ast.parse(fonte)
def corpo(nome):
    for n in ast.walk(arvore):
        if isinstance(n, (ast.AsyncFunctionDef, ast.FunctionDef)) and n.name == nome:
            return ast.get_source_segment(fonte, n)
    return None
for nome, elem in TR.FONTES_COM_REGISTRO.items():
    seg = corpo(nome)
    check(f"{nome} existe e registra {elem}", seg is not None and "_rx_registrar(" in seg)
check("funil _aplicar_dano_alvo notifica o motor", "_rx_registrar_alvo" in (corpo("_aplicar_dano_alvo") or ""))
check("funil _dano_em_alvo notifica o motor", "_rx_registrar_alvo" in (corpo("_dano_em_alvo") or ""))
check("magias rodam dentro de um escopo elemental", "evento_elemental" in (corpo("_executar_magia_grimorio") or "")
      or "evento_elemental" in (corpo("handle_magia") or ""))

# cenários reais: o executor da magia/item dispara a reação
r = sala()
pinta(r, "piche", [(8, 5), (9, 5)])
mago = heroi(r, "m", "Pedro", "mage", [3, 5])
mago["known_spells"] = ["bola_fogo"]
data = {"tx": 8, "ty": 5}
magia = S.GRIMORIO["bola_fogo"]
roda(r._executar_magia_grimorio(mago, magia, data))
check("Bola de Fogo em piche vazio incendeia a mancha",
      any(z.get("tipo") == "chamas_piche" and z.get("ativa") for z in r.zonas_especiais))

r = sala()
pinta(r, "agua", [(x, 5) for x in range(4, 9)])
mago = heroi(r, "m", "Pedro", "mage", [3, 5])
alvo_na_poca = heroi(r, "b", "Bia", "warrior", [7, 5])
magia = S.GRIMORIO["relampago"]
roda(r._executar_magia_grimorio(mago, magia, {"dir": [1, 0]}))
check("Relâmpago em linha sobre a poça dispara o choque (alguém na poça sofreu ou houve broadcast)",
      alvo_na_poca["hp"] < alvo_na_poca["max_hp"] or any(m.get("tipo") == "choque" for m in r.msgs))

r = sala()
pinta(r, "agua", [(8, 5)])
mago = heroi(r, "m", "Pedro", "mage", [3, 5])
magia = S.GRIMORIO["raio_congelante"]
roda(r._executar_magia_grimorio(mago, magia, {"tx": 8, "ty": 5}))
check("Raio Congelante sobre a água a congela", r.materiais.get((8, 5)) == "piso_congelado")

r = sala()
pinta(r, "piche", [(8, 5)])
heroi_ = heroi(r, "a", "Ana", "warrior", [5, 5])
item = {"id": "bomba_incendiaria", "name": "Bomba Incendiária", "emoji": "💣"}
heroi_["bag"] = [item]; heroi_["action_done"] = False
roda(r._throw_item_area(heroi_, S.ARREMESSAVEIS["bomba_incendiaria"], item, 8, 5, None))
check("Bomba Incendiária em piche incendeia", any(z.get("tipo") == "chamas_piche" for z in r.zonas_especiais))
```
(Os `data` exatos dos executores — chaves `tx/ty/dir/target_id` — seguem o que `handle_magia` passa; leia a seção do `handle_magia` para cada magia e ajuste o dict do teste, sem mudar a regra. Se um executor exigir alvo vivo, ponha um monstro parado na casa.)

- [ ] **Step 2: Rodar e ver falhar** — `AttributeError: FONTES_COM_REGISTRO`.

- [ ] **Step 3: Implementar.**
  1. `terrain_reactions.py`: no topo, `FONTES_COM_REGISTRO = {"_executar_bola_fogo": RX_FIRE, "_executar_relampago": RX_LIGHTNING, "_executar_raio_congelante": RX_COLD, "_executar_prisao_chamas": RX_FIRE, "_throw_item_area": RX_FIRE, "_processar_zona_bola_fogo": RX_FIRE}` (acrescente `"_executar_tempestade_ciclones": RX_LIGHTNING` **só** se a leitura do executor mostrar descargas elétricas; senão deixe de fora e registre o motivo no relatório).
  2. **Escopo das magias:** renomeie `_executar_magia_grimorio` para `_executar_magia_grimorio_impl` e crie, com o nome antigo, o invólucro (não reindenta o corpo):
```python
    async def _executar_magia_grimorio(self, caster, magia, data, *args, **kwargs):
        async with self.evento_elemental({"tipo": "magia", "id": magia.get("id"),
                                          "caster_id": caster.get("id")}):
            return await self._executar_magia_grimorio_impl(caster, magia, data, *args, **kwargs)
```
  Confira por `grep` que todos os chamadores passam pelo nome antigo e que a assinatura repassa tudo.
  3. **Escopo dos itens:** envolva, no despacho de `handle_throw_item` (a(s) linha(s) que chamam `_throw_item_area` e `_throw_item_alvo`), cada chamada em `async with self.evento_elemental({"tipo": "item", "id": item_id, "caster_id": pid}):` (só a instrução chamada é indentada).
  4. **Funis:** no início de `_aplicar_dano_alvo` e de `_dano_em_alvo`, depois das guardas de retorno inicial (`dano <= 0`, `_fosso_protegido`) e **antes** do dano:
```python
        await self._rx_registrar_alvo(
            alvo, _NORM_ELEMENTO.get(str(elemento or "").strip().lower(), elemento), dano, killer_pid)
```
  5. **Casas sem criatura** (uma linha em cada fonte, no ponto em que a área é conhecida; passe o `dano` rolado quando ele existir e a CD quando conhecida via `self._rx_origem_atual(cd=…)`):
     - `_executar_bola_fogo`: `await self._rx_registrar(DMG_FIRE, self._rx_tiles_area(cx, cy, raio=raio, lado=area_lado), dano=dano_r1)` e `self._rx_origem_atual(cd=save_dif)` (use as variáveis reais do executor: centro, `raio`, `area_lado`, `dano_r1`, `save_dif`).
     - `_processar_zona_bola_fogo`: a cada tick ativo, `await self._rx_registrar(DMG_FIRE, self._rx_tiles_area(zona["cx"], zona["cy"], raio=zona.get("raio", 2), lado=zona.get("area_lado")))` (as chamas residuais acendem o piche que surgir); esta chamada acontece fora de escopo, então o registro é implícito.
     - `_executar_relampago`: registre `DMG_LIGHTNING` nas casas do caminho que o executor já calcula (`_caminho_relampago`) com o `dano` rolado, e `self._rx_origem_atual(cd=…)` se o executor tem CD.
     - `_executar_raio_congelante`: `DMG_COLD` na casa do alvo (e na trajetória, se o executor já a calcula) com o `dano`.
     - `_executar_prisao_chamas`: `DMG_FIRE` nas casas das paredes de chama (a zona já guarda `tiles`).
     - `_throw_item_area`: depois de resolver o dano, `elem = _NORM_ELEMENTO.get(str(defn.get("elemento") or "").lower())`; se `elem in (DMG_FIRE, DMG_COLD, DMG_LIGHTNING)`: `await self._rx_registrar(elem, self._rx_tiles_area(cx, cy, raio=raio), dano=raw_ou_None)`.
     - `_throw_item_alvo` (óleo, fogo grego sobre uma criatura): coberto pelo funil; se o item acerta uma **casa** (sem criatura) e tem `elemento` fogo, registre a casa do alvo.
  6. `__init__`/categorias: nada novo (já feito na Task 2).

- [ ] **Step 4: Rodar e ver passar** — `python -X utf8 tools/test_terrain_reactions.py`; regressões: `python -X utf8 tools/test_guerreiro_espec.py` (usa `handle_attack`), `python -X utf8 tools/test_ira_rocha_ardente.py`, `python -X utf8 tools/test_prisao_chamas.py`, `python -X utf8 tools/test_tempestade_correcoes.py`, `python -X utf8 tools/test_chamado_inverno.py`, `python -X utf8 tools/test_perseguicao.py`, `python -X utf8 tools/test_modo_mestre.py`, `python -X utf8 tools/test_handler_smoke.py`. Falha nova nesses = regressão da branch: corrija.

- [ ] **Step 5: Commit**

```bash
git add server.py terrain_reactions.py tools/test_terrain_reactions.py
git commit -m "feat: magias e itens elementais disparam reações (escopo por ação, funis e casas vazias)"
```

---

### Task 5: Fontes — armadilhas, armas e monstros

**Files:**
- Modify: `server.py` (`_disparar_armadilha` ~35790 e a armadilha incendiária ~8948/37366; `handle_attack` (bloco de `extra_damages`/flecha incendiária); `_execute_one_monster_attack`; ataques de elementais)
- Modify: `terrain_reactions.py` (`FONTES_COM_REGISTRO`)
- Test: `tools/test_terrain_reactions.py`

**Interfaces:**
- Consumes: `evento_elemental`, `_rx_registrar`, `_rx_registrar_alvo`.
- Produces: todo dano elemental de arma, monstro, elemental e armadilha passa por um escopo e registra suas casas.

- [ ] **Step 1: Teste que falha** (antes do resumo):

```python
print("[9] armadilhas, armas e monstros")
for nome in ("_disparar_armadilha", "handle_attack", "_execute_one_monster_attack"):
    check(f"{nome} roda dentro de um escopo elemental",
          "evento_elemental" in (corpo(nome) or ""))
check("armadilha incendiária registra fogo", "_rx_registrar" in (corpo("_disparar_armadilha") or "")
      or "_rx_registrar" in (corpo("_aplicar_armadilha_area") or ""))

r = sala()
pinta(r, "piche", [(5, 5)])
r.armadilhas = [{"id": "t1", "tipo": "armadilha_incendiaria", "pos": [5, 5], "ativada": False,
                 "visivel": True, "aliada": False, "criador": None}]
pisa = heroi(r, "a", "Ana", "warrior", [5, 5])
roda(r._disparar_armadilha(pisa, r.armadilhas[0]))
check("armadilha incendiária sobre piche incendeia",
      any(z.get("tipo") == "chamas_piche" for z in r.zonas_especiais))

r = sala()
pinta(r, "agua", [(x, 5) for x in range(4, 10)])
ele = monstro(r, "elemental_eletrico", [4, 5])
alvo = heroi(r, "a", "Ana", "warrior", [5, 5])
vitima = heroi(r, "b", "Bia", "warrior", [9, 5])
roda(r._execute_one_monster_attack(ele, alvo, ele["attacks"][0]))   # confira a assinatura real
check("ataque elétrico de monstro dentro d'água choca quem está na poça",
      vitima["hp"] < vitima["max_hp"] or any(m.get("tipo") == "choque" for m in r.msgs))
```
(Leia a assinatura real de `_execute_one_monster_attack` e `_disparar_armadilha` e a estrutura real da armadilha em `ARMADILHAS["armadilha_incendiaria"]`; ajuste os dicts do teste sem mudar a regra. Para a arma, crie um teste em que o herói ataque um monstro sobre piche com `weapon["extra_damages"] = [{"die": "1d4", "type": "fire"}]` por `handle_attack` e verifique a zona; se `handle_attack` exigir mais estado, use o molde de `tools/test_guerreiro_espec.py` para montar a sala.)

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Implementar.**
  1. **Invólucros de escopo** (renomeie o original para `…_impl` e recrie o nome antigo com `async with self.evento_elemental(...)`; confira por `grep` que nada depende da assinatura): `handle_attack` (origem `{"tipo": "arma", "caster_id": pid}`), `_execute_one_monster_attack` (origem `{"tipo": "monstro", "id": atacante.get("id"), "caster_id": None}`), `_disparar_armadilha` (origem `{"tipo": "armadilha", "id": arm.get("tipo")}`).
  2. **Armas** (`handle_attack`): no ponto em que `extra_damages` elementais e munição incendiária são aplicados ao alvo, registre o elemento canônico (via `_NORM_ELEMENTO`) nas casas do alvo: `await self._rx_registrar(elem, self._rx_tiles_da(target), dano=dano_elemental, atingidos={target.get("id")})`. Esse trecho aplica o dano sem passar pelos funis, por isso o registro é explícito.
  3. **Monstros/elementais** (`_execute_one_monster_attack`): onde o dano é aplicado com `damage_types` elementais, registre cada tipo em `(DMG_FIRE, DMG_COLD, DMG_LIGHTNING)` nas casas do alvo (e, para raios em linha, nas casas da linha). O raio do Elemental Elétrico tem seu próprio executor de linha: registre `DMG_LIGHTNING` nas casas da linha com o dano rolado. Localize-o por `grep -n "elemental_raio\|raio" server.py` perto de `atacar_animado`/`_execute_one_monster_attack`.
  4. **Armadilhas** (`_disparar_armadilha` / `_aplicar_armadilha_area` / tick `_processar_efeitos_armadilha_turno`): armadilha incendiária registra `DMG_FIRE` na casa (e na área, se for de área); armadilha de Raio Congelante registra `DMG_COLD`; mina terrestre é `explosao` (sem reação).
  5. `FONTES_COM_REGISTRO` ganha as fontes explícitas novas que chamam `_rx_registrar` no próprio corpo (`"_disparar_armadilha": RX_FIRE`, e o nome da função de arma/monstro onde o registro explícito foi colocado). Os wrappers (`handle_attack`, `_execute_one_monster_attack`) entram só no teste `evento_elemental`.

- [ ] **Step 4: Rodar e ver passar** — `python -X utf8 tools/test_terrain_reactions.py` e as regressões da Task 4 mais `python -X utf8 tools/test_armadilhas.py` (se existir; `ls tools/test_*armadilha*`), `python -X utf8 tools/test_tirano.py`, `python -X utf8 tools/test_monster_intent.py`.

- [ ] **Step 5: Commit**

```bash
git add server.py terrain_reactions.py tools/test_terrain_reactions.py
git commit -m "feat: armadilhas, armas e monstros elementais disparam reações"
```

---

### Task 6: Cliente — animações, tooltip por material e aviso da crosta

**Files:**
- Create: `src/reacoesElementais.js`
- Modify: `index.html` (tag do módulo, na linha de `document.write` ao lado de `src/intencaoMonstros.js`)
- Modify: `src/gameState.js` (`case 'reacao_elemental'`)
- Modify: `server.py` (payload `terrenos_temp` em `_game_state_payload`)
- Modify: `game.js` (animações 2D/3D; tooltip de casa; pulso da crosta)
- Modify: `src/lang/interface.js` (chaves do tooltip) e `src/lang/narracao.js` (aviso da crosta)
- Test: `tools/test_reacoes_cliente.js`, `tools/test_terrain_reactions.py` (payload)

**Interfaces:**
- Produces (`window.ReacoesElementais`, puro):
  - `estilo(tipo) -> {cor: string, duracaoMs: number}` com `choque #7fd4ff / 700`, `incendio #ff8a2a / 900`, `congelar #bfefff / 900`, `crosta #8a5a44 / 900`; tipo desconhecido → `null`.
  - `crostasAcabando(state) -> [[x,y]…]`: casas com material `lava_solidificada` e `terrenos_temp["x,y"] - state.round <= 1`.
  - `descreverCasa(state, x, y) -> {chave, params}|null`: `piche` → `ui.reacao.casa.piche`; `agua` → `ui.reacao.casa.agua`; `lava_solidificada` → `ui.reacao.casa.crosta` com `{n}` = rodadas restantes (`terrenos_temp - round`, mínimo 1); outros → `null`.
- Server → cliente: `game_state.terrenos_temp = {"x,y": expira_em}` para toda casa com camada temporária ativa em `_terrenos_inverno`.

- [ ] **Step 1: Testes que falham.** Em `tools/test_reacoes_cliente.js` (acrescente antes do resumo):

```javascript
global.window = global.window || {};
const RE = eval(fs.readFileSync(path.join(raiz, "src", "reacoesElementais.js"), "utf8") + "; window.ReacoesElementais");
console.log("[2] estilo");
check("choque azul 700ms", RE.estilo("choque").cor === "#7fd4ff" && RE.estilo("choque").duracaoMs === 700);
check("incendio laranja", RE.estilo("incendio").cor === "#ff8a2a");
check("tipo desconhecido -> null", RE.estilo("xxx") === null);
console.log("[3] crosta acabando");
const st = { round: 5, materiais: { "3,3": "lava_solidificada", "4,3": "lava_solidificada", "5,3": "lava" },
             terrenos_temp: { "3,3": 6, "4,3": 8 } };
check("só a crosta com ≤1 rodada restante", JSON.stringify(RE.crostasAcabando(st)) === JSON.stringify([[3, 3]]));
check("estado vazio não quebra", RE.crostasAcabando({}).length === 0 && RE.crostasAcabando(null).length === 0);
console.log("[4] tooltip por material");
check("piche", RE.descreverCasa(st, 9, 9) === null);
const st2 = { round: 5, materiais: { "1,1": "piche", "2,1": "agua", "3,1": "lava_solidificada" }, terrenos_temp: { "3,1": 8 } };
check("piche -> chave", RE.descreverCasa(st2, 1, 1).chave === "ui.reacao.casa.piche");
check("água -> chave", RE.descreverCasa(st2, 2, 1).chave === "ui.reacao.casa.agua");
const c = RE.descreverCasa(st2, 3, 1);
check("crosta -> rodadas restantes", c.chave === "ui.reacao.casa.crosta" && c.params.n === 3);
console.log("[5] fiação");
const jogo2 = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("GS trata reacao_elemental", fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8").includes("case 'reacao_elemental'"));
check("game.js ouve reacaoElemental uma vez", (jogo2.match(/GS\.on\('reacaoElemental'/g) || []).length === 1);
check("game.js não duplica GS.on('gameState')", (jogo2.match(/^GS\.on\('gameState'/gm) || []).length === 1);
check("index.html carrega o módulo", fs.readFileSync(path.join(raiz, "index.html"), "utf8").includes("src/reacoesElementais.js"));
const lang = fs.readFileSync(path.join(raiz, "src", "lang", "interface.js"), "utf8").replace(/\n/g, " ");
for (const k of ["ui.reacao.casa.piche", "ui.reacao.casa.agua", "ui.reacao.casa.crosta"])
  check("chave " + k + " pt+en", new RegExp('"' + k.replace(/\./g, "\\.") + '":\\s*\\{[^}]*"pt"[^}]*"en"|"' + k.replace(/\./g, "\\.") + '":\\s*\\{[^}]*"en"[^}]*"pt"').test(lang));
```
E em `tools/test_terrain_reactions.py`:

```python
print("[10] payload terrenos_temp")
r = sala()
pinta(r, "lava", [(8, 5)])
r._aplicar_camadas_terreno_inverno([(8, 5)], "lava_solidificada", "rx_1", permanente=False, expira_em=7)
pl = r._game_state_payload()
check("terrenos_temp expõe a expiração da camada", pl.get("terrenos_temp", {}).get("8,5") == 7)
```

- [ ] **Step 2: Rodar e ver falhar.**

- [ ] **Step 3: Módulo puro** (`src/reacoesElementais.js`):

```javascript
// Reações elementais — lógica PURA do cliente (sem DOM/canvas/THREE).
(function () {
  const ESTILOS = {
    choque:   { cor: '#7fd4ff', duracaoMs: 700 },
    incendio: { cor: '#ff8a2a', duracaoMs: 900 },
    congelar: { cor: '#bfefff', duracaoMs: 900 },
    crosta:   { cor: '#8a5a44', duracaoMs: 900 },
  };
  function estilo(tipo) { return ESTILOS[tipo] ? Object.assign({}, ESTILOS[tipo]) : null; }

  function _restantes(state, key) {
    const exp = state && state.terrenos_temp && state.terrenos_temp[key];
    return exp == null ? null : Math.max(0, Number(exp) - Number(state.round));
  }

  // Crostas de lava que se desfazem na próxima virada (≤ 1 rodada restante).
  function crostasAcabando(state) {
    const out = [];
    const mats = (state && state.materiais) || {};
    for (const key of Object.keys(mats)) {
      if (mats[key] !== 'lava_solidificada') continue;
      const resta = _restantes(state, key);
      if (resta != null && resta <= 1) out.push(key.split(',').map(Number));
    }
    return out;
  }

  function descreverCasa(state, x, y) {
    const key = `${x},${y}`;
    const mat = state && state.materiais && state.materiais[key];
    if (mat === 'piche') return { chave: 'ui.reacao.casa.piche', params: {} };
    if (mat === 'agua') return { chave: 'ui.reacao.casa.agua', params: {} };
    if (mat === 'lava_solidificada')
      return { chave: 'ui.reacao.casa.crosta', params: { n: Math.max(1, _restantes(state, key) || 1) } };
    return null;
  }

  window.ReacoesElementais = { estilo, crostasAcabando, descreverCasa };
})();
```
`index.html`: na linha de `document.write`, depois da entrada `src/intencaoMonstros.js`, acrescente `document.write('<script src="src/reacoesElementais.js?v='+v+'"><\/script>');` (Edit com o trecho exato).

- [ ] **Step 4: Servidor — `terrenos_temp`.** Em `_game_state_payload` (onde `materiais` é serializado), acrescente `"terrenos_temp"`: dict `"x,y" → max(expira_em das camadas ativas)` para cada casa de `self._terrenos_inverno` com camadas.

- [ ] **Step 5: `game.js` e `src/gameState.js`.**
  - `gameState.js`: depois de `case 'previsao_ataque'`, `case 'reacao_elemental': _emit('reacaoElemental', msg); break;`.
  - `game.js` (uma única vez, perto de `_intencoesDesenhar2D`): `const _reacoesAnims = [];` e
```javascript
GS.on('reacaoElemental', msg => {
  const est = ReacoesElementais.estilo(msg && msg.tipo);
  if(!est || !Array.isArray(msg.casas)) return;
  _reacoesAnims.push({ tipo: msg.tipo, casas: msg.casas, origem: msg.origem, t0: performance.now(), est });
  _tocarSomReacao(msg.tipo, msg.origem);
  if(GS.gameState){ if(mode3D && g3) renderMap3D(GS.gameState); else renderMap(GS.gameState); }
});
```
  - `_tocarSomReacao(tipo, pos)`: `choque → sfx('relampago',{pos})`, `incendio → sfx('incendio',{pos})`, `congelar`/`crosta →` o evento de gelo que existir em `src/soundBank.js` (`grep -n "gelo\|frio\|congel\|raio_congelante" src/soundBank.js`; se não houver, nenhum som). `sfx()` devolve `false` sem amostra; ignore o retorno.
  - **2D:** `_reacoesDesenhar2D(ctx, state, visionSet)` chamada no fim de `renderMap` (junto de `_intencoesDesenhar2D`), que descarta animações vencidas e, para cada casa visível, desenha por tipo: `choque` linhas em zigue-zague azuis entre as casas (alterne um deslocamento determinístico por índice e tempo), `incendio` 3 labaredas (reuse `_desenharChamasPeao2D(ctx, cx, baseY, larg, now, seed)`), `congelar` cristais (losangos claros que crescem), `crosta` brilho laranja que apaga. Agende redesenho enquanto houver animações (`_agendarChamas2D()`).
  - **3D:** em `_reacoes3DAtualizar()` (chamada no laço do `startLoop3D`, ao lado de `_intencoesAtualizar3D();`): para cada animação nova crie UM grupo temporário (planos `PlaneGeometry(0.9,0.9)` deitados, uma `Line` em zigue-zague para `choque`, material `MeshBasicMaterial` transparente com `depthTest:false`), anime a opacidade/escala pelo progresso e **remova e dê `dispose` em geometrias e materiais ao vencer**. São eventos raros: criar malhas por evento é aceito aqui (diferente do pool das setas). Limpe tudo em `dispose3D`.
  - **Filtro de visão:** use o mesmo `visionSet`/`_guiaVisao3D(state)` das setas; casa fora da visão não anima.
  - **Tooltip de casa:** localize o tooltip de casa existente (`grep -n "_sombraTooltipHTML\|Visão bloqueada\|getElementById('tooltip')"`; o tooltip de casa 2D/3D usa `get3DTilePlane` no 3D) e acrescente, para a casa sob o cursor, `ReacoesElementais.descreverCasa(state, x, y)` renderizado com `t(chave, params)`.
  - **Pulso da crosta:** em `_reacoesDesenhar2D` e `_reacoes3DAtualizar`, para cada casa de `ReacoesElementais.crostasAcabando(state)` visível, pulse um anel laranja (`0.5 + 0.5*Math.sin(agora/180)`). Sem `t()` no nível de módulo; sem variável local `t` sombreando o tradutor.
  - Aviso no log (servidor, uma vez por rodada): em `_processar_zonas_turno`, depois de `_expirar_terrenos_inverno()`, se alguma camada `lava_solidificada` tem `expira_em - round_num == 1` e ainda não avisou naquela rodada (`self._rx_avisou_crosta != self.round_num`), `await self.gm_say(T("narracao.reacao.crosta_acabando"))` e grave `self._rx_avisou_crosta = self.round_num` (atributo novo em `__init__` + categoria `"efemero"`); texto pt "⚠️ A crosta de lava está se desfazendo!" / en "⚠️ The lava crust is breaking apart!".
  - `src/lang/interface.js`: `ui.reacao.casa.piche` (pt "Piche: inflamável, +1 de movimento" / en "Pitch: flammable, +1 movement"), `ui.reacao.casa.agua` (pt "Água: conduz eletricidade" / en "Water: conducts electricity"), `ui.reacao.casa.crosta` (pt "Lava solidificada: volta em {n} rodada(s)" / en "Solidified lava: reverts in {n} round(s)"), no formato multi-linha das entradas vizinhas.

- [ ] **Step 6: Rodar e ver passar** — `node tools/test_reacoes_cliente.js`, `python -X utf8 tools/test_terrain_reactions.py`, `node --check game.js`, `node tools/test_intencoes_cliente.js`, `python -X utf8 tools/test_interface.py`, `python -X utf8 tools/dividas.py`, `node tools/test_idioma_cliente.js`, `python -X utf8 tools/test_idioma.py`, `node tools/test_sons_cliente.js` (só as 2 falhas conhecidas).

- [ ] **Step 7: Commit**

```bash
git add src/reacoesElementais.js index.html src/gameState.js server.py game.js src/lang/interface.js src/lang/narracao.js tools/test_reacoes_cliente.js tools/test_terrain_reactions.py
git commit -m "feat: animações, tooltip por material e aviso da crosta das reações elementais"
```

---

### Task 7: Persistência e fim do turno da crosta

**Files:**
- Modify: `server.py` (se algo do registro de camadas não estiver na foto)
- Test: `tools/test_terrain_reactions.py`, `tools/test_salvar_masmorra.py` (só execução)

**Interfaces:**
- Consumes: `_terrenos_inverno`, `zonas_especiais`, foto da masmorra (`foto_empacotar`).

- [ ] **Step 1: Teste que falha** (antes do resumo): crie uma sala com piche temporário, uma zona `chamas_piche` ativa e uma crosta, serialize e reidrate com as funções reais da foto e confira que os três voltam idênticos.

```python
print("[11] foto da masmorra")
r = sala()
pinta(r, "terra", [(5, 5)])
r._aplicar_camadas_terreno_inverno([(5, 5)], "piche", "frasco_9", permanente=False, expira_em=9)
r.zonas_especiais.append({"id": "z1", "tipo": "chamas_piche", "tiles": [[5, 5]], "expira_em": 6, "ativa": True, "caster": None})
pacote = S.foto_empacotar({"_terrenos_inverno": r._terrenos_inverno, "zonas_especiais": r.zonas_especiais, "materiais": r.materiais})
volta = S.foto_desempacotar(pacote)
check("a camada temporária de piche sobrevive à foto", volta["_terrenos_inverno"][(5, 5)]["camadas"][0]["material"] == "piche")
check("a zona de chamas sobrevive à foto", volta["zonas_especiais"][0]["tipo"] == "chamas_piche")
check("o material sobrevive à foto", volta["materiais"][(5, 5)] == "piche")
```
(Se os nomes `foto_empacotar`/`foto_desempacotar`/`_foto_codificar` forem outros, leia `server.py` e `tools/test_salvar_masmorra.py` [3] e use os reais; o teste existente de round-trip é o molde. Se `_terrenos_inverno` ainda não estiver em `FOTO_SALA_CATEGORIAS`, adicione-o como `"foto"` e `_rx_avisou_crosta` como `"efemero"`.)

- [ ] **Step 2: Rodar e ver falhar/passar** — se já passar, registre no relatório que o registro de camadas já era persistido (nenhum código novo).

- [ ] **Step 3: Implementar** o que faltar (categoria do `_terrenos_inverno`, chaves tupla na codificação etiquetada `$tup`/`$map`).

- [ ] **Step 4: Rodar** — `python -X utf8 tools/test_terrain_reactions.py`; `python -X utf8 tools/test_salvar_masmorra.py` (só as falhas conhecidas de marcadores cooperativos).

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_terrain_reactions.py
git commit -m "test: camadas de terreno e zonas de chamas sobrevivem à foto da masmorra"
```

---

### Task 8: Documentação, spec e bateria final

**Files:**
- Modify: `CLAUDE.md` (seção nova depois do bloco "Intenção dos monstros"), `docs/superpowers/specs/2026-10-13-reacoes-elementais-design.md`
- Test: bateria

- [ ] **Step 1: CLAUDE.md** (≈15 linhas, estilo dos blocos `> **...**`, em português): o que é; `terrain_reactions.py` (tabela `REACOES`, `evento_elemental`, `_rx_registrar`, dedupe por escopo, `profundidade 2`, `_rx_em_reacao` evita reentrada); as quatro reações e os números; piche (material, custo 2, frasco 3×3/4 rodadas, zona `chamas_piche` com lista de casas, gancho da criatura em chamas em `_aplicar_lava_se_pisar`); crosta; mensagem `reacao_elemental`; `terrenos_temp`; **como acrescentar uma fonte** (registrar casas dentro de um escopo; entrar em `FONTES_COM_REGISTRO`) e **como acrescentar uma reação** (linha em `REACOES` + método `_rx_*`); fora de escopo; testes `tools/test_terrain_reactions.py` e `tools/test_reacoes_cliente.js`.

- [ ] **Step 2: Spec.** Atualize a seção "Piche" (custo 2 como a areia/lava; `custo_mov` é metadado), "Risco a conferir" (lava da Ira é material: resolvido), "Pontos de ligação" (escopo por ação em vez de id de evento) e acrescente a nota da ignição imediata e do payload `terrenos_temp`.

- [ ] **Step 3: Bateria** (registre comandos e resultados): `python -X utf8 tools/test_terrain_reactions.py`; `node tools/test_reacoes_cliente.js`; `python -X utf8 tools/test_monster_intent.py`; `node tools/test_intencoes_cliente.js`; `python -X utf8 tools/test_perseguicao.py`; `python -X utf8 tools/test_modo_mestre.py`; `python -X utf8 tools/test_handler_smoke.py`; `python -X utf8 tools/test_chamado_inverno.py`; `python -X utf8 tools/test_ira_rocha_ardente.py`; `python -X utf8 tools/test_prisao_chamas.py`; `python -X utf8 tools/test_senhor_das_aguas.py`; `python -X utf8 tools/test_tempestade_correcoes.py`; `python -X utf8 tools/test_salvar_masmorra.py`; `python -X utf8 tools/test_interface.py`; `python -X utf8 tools/dividas.py`; `python -X utf8 tools/test_idioma.py`; `node tools/test_idioma_cliente.js`; `python -X utf8 tools/test_editor_idioma.py`; `node --check game.js`. Falhas conhecidas do `master`: ver Global Constraints. Qualquer outra falha: determine se a branch a causou e corrija.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/superpowers/specs/2026-10-13-reacoes-elementais-design.md
git commit -m "docs: documenta as reações elementais e atualiza o spec"
```

(A prova no navegador, em servidor isolado e **depois** da última correção, fica a cargo do controlador, fora das tarefas: raio em poça, fogo em piche com e sem criatura, frio em água e em lava, e FPS.)

---

## Self-Review

- **Cobertura do spec:** §1 motor/tabela → Task 2; §2 piche (terreno, frasco, fogo, gancho) → Tasks 1 e 3; §3 números → Tasks 2 e 3 (constantes em Global Constraints); §4 fontes e travas → Tasks 4 e 5 (escopo, funis, `FONTES_COM_REGISTRO`, teste por fonte); §5 feedback → Task 6; §6 testes e persistência → Tasks 2 a 7 e bateria da Task 8; editor (piche na paleta) → Task 1.
- **Tipos e nomes consistentes:** `evento_elemental`, `_rx_registrar`, `_rx_registrar_alvo`, `_rx_origem_atual`, `_rx_tiles_area`, `_rx_tiles_da`, `_rx_estado`, `_rx_regiao`, `_rx_encadear`, `_rx_resolver`, `_rx_anunciar`, `_rx_id`, `_rx_T`, `_rx_altura`, `_rx_fogo_piche`, `_consumir_piche`, `REACOES`, `FONTES_COM_REGISTRO`, `ReacoesElementais.{estilo,crostasAcabando,descreverCasa}`, `terrenos_temp` — iguais em todas as tarefas.
- **Riscos abertos para o implementador:** a assinatura real de `_save_mostrado`, `_executar_*` e `_execute_one_monster_attack`; os kwargs de `data` por magia; a existência de som de gelo em `soundBank.js`; a forma real de `foto_empacotar`. Cada um tem a instrução de leitura e o fallback na própria tarefa.
