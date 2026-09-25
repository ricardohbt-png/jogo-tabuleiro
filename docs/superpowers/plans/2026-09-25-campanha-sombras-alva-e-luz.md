# Campanha "Sombras sob Alva e Luz" — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gerar e publicar a campanha de 3 destinos / 4 masmorras "Sombras sob Alva e Luz" por um script reexecutável e não destrutivo, depois de consertar o objetivo `salas_obrigatorias`, que nunca funcionou numa masmorra real.

**Architecture:** `tools/gerar_campanha_sombras.py` monta TUDO em memória (masmorras, destinos com história, anel, conversa do Bartender), valida com as funções do próprio `server.py` e só então grava, tocando apenas nas entradas `sombras_*`/`anel_garra_negra` dos arquivos compartilhados — trabalha sobre o JSON cru de cada arquivo, nunca sobre as variáveis normalizadas do servidor, para o resto sair byte-idêntico. `tools/test_campanha_sombras.py` não depende dos arquivos gerados no repositório: grava as masmorras numa pasta temporária (`DUNGEONS_DIR`) e injeta destinos/conversa em memória, exercitando o caminho real do jogo (`handle_world_adventure` → `enter_dungeon`).

**Tech Stack:** Python 3 (sem dependências novas), `server.py` importado como módulo, suítes no padrão do repo (`check()` + `✅/❌`, `sys.exit(1 if FAIL else 0)`).

**Spec:** `docs/superpowers/specs/2026-09-25-campanha-sombras-alva-e-luz-design.md`

**Proveniência do código:** o gerador e a suíte abaixo foram escritos e executados como protótipo antes deste plano (fora do repositório). Com a correção da Task 1 simulada, a suíte completa deu `67 passaram, 0 falharam`; sem ela, a única falha é a checagem que a Task 1 conserta.

---

## Antes de começar — três regras deste repositório

1. **O autor edita `server.py`, `game.js`, `CLAUDE.md` e `tools/editor_dungeons.js` em paralelo.** Nunca `git add` desses arquivos inteiros sem conferir o diff. Para commitar só a sua mudança num arquivo com trabalho alheio, monte o conteúdo a partir do `HEAD` e ponha no índice (receita na Task 1, Step 6).
2. **Um servidor rodando na porta 8765 trava a escrita de arquivos** (`OSError: Errno 22`). Se uma gravação falhar assim, peça ao autor para parar o servidor; não mate processos dele.
3. **`server.py` e `CLAUDE.md` estão em CRLF.** Para editar, use a ferramenta de edição (Edit), não `replace("…\n…")` em script sem converter as quebras.

Execute todos os comandos **da raiz do repositório** (Git Bash). Use `PYTHONIOENCODING=utf-8` para os emojis das suítes. Ao rodar várias suítes num laço, confira **o código de saída E a contagem de `❌`** — o código de saída sozinho já mentiu neste repositório.

## Estrutura de arquivos

| Arquivo | Papel |
|---|---|
| `server.py` (modificar, 2 trechos) | carregador preserva `required`/`required_mode`; objetivo sem sala marcada não se cumpre sozinho |
| `tools/test_modo_mestre.py` (modificar) | regressão `[23b]` pelo carregador real |
| `tools/gerar_campanha_sombras.py` (criar) | montagem em memória + validação + gravação não destrutiva + CLI |
| `tools/test_campanha_sombras.py` (criar) | 7 seções, 67 checagens |
| `dungeons/sombras_*.json` (gerados) | as 4 masmorras |
| `world_adventures.json`, `city_scenes.json`, `itens_personalizados.json`, `tools/editor_items_custom.js`, `tools/editor_dungeons.js` (gerados, só as entradas da campanha) | destinos, conversa, anel, índices do editor |
| `tools/.sombras_assinaturas.json` (gerado) | hash de cada masmorra gerada — trava contra sobrescrever edição manual |

---

### Task 1: Salas obrigatórias sobrevivem ao carregador

`GameRoom.load_authored_dungeon` (`server.py`, bloco `self.rooms.append({…})` logo depois de `self.rooms = []`, perto da linha 12780) descarta `required`/`required_mode`; sem sala marcada, `_objetivo_cumprido` faz `all([])` e o objetivo `salas_obrigatorias` se cumpre ao entrar. A seção `[23]` de `test_modo_mestre.py` monta `r.rooms` à mão e por isso não pegou.

**Files:**
- Modify: `server.py` (bloco do `self.rooms.append` em `load_authored_dungeon`; ramo `salas_obrigatorias` de `_objetivo_cumprido`)
- Test: `tools/test_modo_mestre.py` (seção nova `[23b]`)

- [ ] **Step 1: Escrever o teste de regressão**

Em `tools/test_modo_mestre.py`, imediatamente antes da linha `    print("\n[24] Falas de NPC")`, insira:

```python
    print("\n[23b] Salas obrigatórias sobrevivem ao carregador de masmorra")
    d_req = {"schema_version": 1, "id": "req", "name": "req", "grid": {"w": 12, "h": 5},
             "tiles": [[S.FLOOR] * 12 for _ in range(5)], "entrance": {"x": 0, "y": 0},
             "rooms": [{"id": 0, "x": 0, "y": 0, "w": 4, "h": 5, "role": "entrance",
                        "locked": False, "doors": []},
                       {"id": 1, "x": 6, "y": 0, "w": 6, "h": 5, "role": "monster",
                        "locked": False, "doors": [], "required": True, "required_mode": "clear"}],
             "monsters": [{"type": "goblin", "pos": [8, 2], "room_id": 1}],
             "chests": [], "traps": [], "decorations": [], "secret_passages": [], "falas": [],
             "objectives": {"primary": {"type": "salas_obrigatorias"}, "secondary": []}}
    check("fixture válida", S.validar_dungeon(d_req)[0] is True)
    r = S.GameRoom("REQ")
    r.load_authored_dungeon(d_req)
    sala1 = next(rm for rm in r.rooms if rm["id"] == 1)
    check("o carregador preserva required", sala1.get("required") is True)
    check("o carregador preserva required_mode", sala1.get("required_mode") == "clear")
    obj_req = {"type": "salas_obrigatorias"}
    check("goblin vivo: objetivo NÃO cumprido", r._objetivo_cumprido(obj_req) is False)
    for m in r.monsters.values():
        m["hp"] = 0
    check("goblin morto: cumprido", r._objetivo_cumprido(obj_req) is True)
    r3 = playing_room_com_mestre()
    r3.rooms = [{"id": 0, "x": 0, "y": 0, "w": 3, "h": 3}]
    r3.monsters = {}
    check("nenhuma sala marcada: o objetivo NÃO se cumpre sozinho", r3._objetivo_cumprido(obj_req) is False)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_modo_mestre.py 2>&1 | grep -A9 "\[23b\]"`
Expected: `❌` em "o carregador preserva required", "o carregador preserva required_mode", "goblin vivo: objetivo NÃO cumprido" e "nenhuma sala marcada: o objetivo NÃO se cumpre sozinho".

- [ ] **Step 3: Preservar os campos no carregador**

Em `server.py`, dentro do `self.rooms.append({…})` de `load_authored_dungeon`, logo depois da linha `"doors": [list(d) for d in r.get("doors", [])],`, acrescente:

```python
                # Salas obrigatórias (Camada C). Sem estes dois campos o objetivo
                # salas_obrigatorias se cumpria no instante da entrada (all([]) é True).
                "required": bool(r.get("required", False)),
                "required_mode": (r.get("required_mode")
                                  if r.get("required_mode") in ("visit", "clear") else "clear"),
```

- [ ] **Step 4: Lista vazia não cumpre**

Em `server.py`, no método `_objetivo_cumprido`, troque

```python
        if t == "salas_obrigatorias":
            req = [rm for rm in self.rooms if rm.get("required")]
            return all(self._sala_obrigatoria_ok(rm) for rm in req)
```

por

```python
        if t == "salas_obrigatorias":
            req = [rm for rm in self.rooms if rm.get("required")]
            # validar_dungeon já recusa o objetivo sem sala marcada; a guarda é
            # defesa em profundidade contra o all([]) == True.
            return bool(req) and all(self._sala_obrigatoria_ok(rm) for rm in req)
```

- [ ] **Step 5: Rodar e ver passar (e as vizinhas)**

Run: `PYTHONIOENCODING=utf-8 python tools/test_modo_mestre.py 2>&1 | tail -3`
Expected: `0 falharam` — a suíte inteira, inclusive a `[23]` original.

Run:
```bash
for t in test_tutorial test_masmorra_sequenciada test_preview_editor; do out=$(PYTHONIOENCODING=utf-8 python tools/$t.py 2>&1); c=$?; echo "$t exit=$c falhas=$(echo "$out" | grep -c '❌')"; done
```
Expected: `exit=0 falhas=0` nas três.

- [ ] **Step 6: Commit só dos seus trechos do `server.py`**

O `server.py` tem trabalho do autor em andamento. Monte o arquivo a partir do `HEAD` com as duas mudanças e ponha só isso no índice. Salve este script como `$TMP/aplicar_task1.py`:

```python
import sys
s = open(sys.argv[1], "rb").read().decode("utf-8")
nl = "\r\n" if "\r\n" in s else "\n"

def rep(a, b):
    global s
    a, b = a.replace("\n", nl), b.replace("\n", nl)
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)

rep('                "doors": [list(d) for d in r.get("doors", [])],\n'
    '                # Rotação',
    '                "doors": [list(d) for d in r.get("doors", [])],\n'
    '                # Salas obrigatórias (Camada C). Sem estes dois campos o objetivo\n'
    '                # salas_obrigatorias se cumpria no instante da entrada (all([]) é True).\n'
    '                "required": bool(r.get("required", False)),\n'
    '                "required_mode": (r.get("required_mode")\n'
    '                                  if r.get("required_mode") in ("visit", "clear") else "clear"),\n'
    '                # Rotação')
rep('            req = [rm for rm in self.rooms if rm.get("required")]\n'
    '            return all(self._sala_obrigatoria_ok(rm) for rm in req)',
    '            req = [rm for rm in self.rooms if rm.get("required")]\n'
    '            # validar_dungeon já recusa o objetivo sem sala marcada; a guarda é\n'
    '            # defesa em profundidade contra o all([]) == True.\n'
    '            return bool(req) and all(self._sala_obrigatoria_ok(rm) for rm in req)')
open(sys.argv[2], "wb").write(s.encode("utf-8"))
```

Depois:

```bash
git show HEAD:server.py > "$TMP/server_head.py"
PYTHONIOENCODING=utf-8 python "$TMP/aplicar_task1.py" "$TMP/server_head.py" "$TMP/server_meu.py"
python -c "import ast,sys; ast.parse(open(sys.argv[1],encoding='utf-8').read())" "$TMP/server_meu.py"
git update-index --cacheinfo 100644,$(git hash-object -w "$TMP/server_meu.py"),server.py
git add tools/test_modo_mestre.py
git diff --cached --stat
git commit -m "fix(objetivos): salas obrigatorias sobrevivem ao carregador de masmorra

load_authored_dungeon descartava required/required_mode e o objetivo
salas_obrigatorias se cumpria no instante da entrada (all([]) == True).
O teste [23] montava r.rooms a mao e nao passava pelo carregador.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Expected: `git diff --cached --stat` mostra `server.py` com ~9 linhas e `tools/test_modo_mestre.py`; depois do commit, `git status` continua mostrando `server.py` modificado (o trabalho do autor, fora do commit). Se o `assert` do script falhar, o `HEAD` mudou: releia os dois trechos no `HEAD` e ajuste o texto de busca.

---

### Task 2: Gerador — montagem das masmorras, história, anel e conversa (em memória)

**Files:**
- Create: `tools/gerar_campanha_sombras.py`

- [ ] **Step 1: Criar o módulo com a montagem completa**

Crie `tools/gerar_campanha_sombras.py` com exatamente este conteúdo. A gravação, o relatório e o `main` entram na Task 4.

```python
"""Gerador da campanha "Sombras sob Alva e Luz".

Roda da raiz do projeto:
    python tools/gerar_campanha_sombras.py            # valida e grava
    python tools/gerar_campanha_sombras.py --simular  # só relata (ND por sala, avisos, artes)
    python tools/gerar_campanha_sombras.py --forcar   # regrava masmorra editada à mão

Spec: docs/superpowers/specs/2026-09-25-campanha-sombras-alva-e-luz-design.md

Só toca no que é dele: as 4 masmorras `sombras_*.json`, os destinos `sombras_*` de
world_adventures.json, a conversa `sombras_caravanas` do Bartender e o anel
`anel_garra_negra`. Tudo o mais é relido e regravado intacto.
"""
import argparse
import hashlib
import json
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
import server as S  # noqa: E402

WALL, FLOOR, DOOR = S.WALL, S.FLOOR, S.DOOR

ARQUIVOS = ("sombras_1_vau.json", "sombras_2_minas.json",
            "sombras_3a_saloes.json", "sombras_3b_trono.json")
ANEL_ID = "anel_garra_negra"
CONVERSA_ID = "sombras_caravanas"
FATO_GANCHO = "sombras_caravanas"
ASSINATURAS = os.path.join(RAIZ, "tools", ".sombras_assinaturas.json")
MUSICA_ABERTURA = "assets/story/a_song_of_old_stones.mp3"
MUSICA_TROLL = "assets/story/the_kraken_s_overture.mp3"


# ─── Mapa ────────────────────────────────────────────────────────────────────
class Mapa:
    """Grade de paredes onde se cavam salas retangulares separadas por UMA parede;
    a porta entre duas salas vizinhas é a casa dessa parede e entra na lista
    `doors` das duas (door_rooms destranca toda sala que a lista)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.tiles = [[WALL] * w for _ in range(h)]
        self.rooms = []

    def sala(self, rid, x, y, w, h, role="monster", locked=True, **extra):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.tiles[yy][xx] = FLOOR
        room = {"id": rid, "x": x, "y": y, "w": w, "h": h, "role": role,
                "locked": locked, "doors": []}
        room.update(extra)
        self.rooms.append(room)
        return room

    def porta(self, x, y, *rids):
        self.tiles[y][x] = DOOR
        for rid in rids:
            self._room(rid)["doors"].append([x, y])

    def _room(self, rid):
        return next(r for r in self.rooms if r["id"] == rid)

    def em(self, rid, dx, dy):
        """Casa absoluta a partir do canto da sala (dx, dy dentro dela)."""
        r = self._room(rid)
        assert 0 <= dx < r["w"] and 0 <= dy < r["h"], (rid, dx, dy)
        return [r["x"] + dx, r["y"] + dy]


def monstro(tipo, pos, rid, alvo=False):
    return {"type": tipo, "pos": pos, "room_id": rid, "boss": alvo, "target": alvo}


def decor(did, tipo, pos, **extra):
    d = {"id": did, "type": tipo, "pos": pos, "facing": [0, 1], "loot": None}
    d.update(extra)
    return d


def fala(fid, pos, nome, emoji, texto, raio=3):
    return {"id": fid, "pos": pos, "falante": {"nome": nome, "emoji": emoji},
            "texto": texto, "trigger": {"tipo": "proximidade", "raio": raio}}


def masmorra(did, nome, mapa, ambiente, nivel, objetivo, entrada, saida=None, **extra):
    d = {"schema_version": 1, "id": did, "name": nome, "ambiente": ambiente,
         "saida_permitida": True, "start_mode": "entrance",
         "grid": {"w": mapa.w, "h": mapa.h}, "tiles": mapa.tiles, "rooms": mapa.rooms,
         "door_conditions": {}, "entrance": {"x": entrada[0], "y": entrada[1]},
         "exit": ({"x": saida[0], "y": saida[1]} if saida else None),
         "monsters": [], "chests": [], "traps": [], "decorations": [],
         "secret_passages": [], "master_reinforcements": [], "falas": [],
         "expected_party": {"heroes": 4, "level": nivel},
         "objectives": {"primary": objetivo, "secondary": []}}
    d.update(extra)
    if d["exit"] is None:
        del d["exit"]
    return d


# ─── 1 · Emboscada no Vau ────────────────────────────────────────────────────
def masmorra_vau():
    m = Mapa(36, 12)
    m.sala(0, 1, 2, 10, 8, role="entrance", locked=False)     # Trilha
    m.sala(1, 12, 2, 10, 8)                                   # Carroça tombada
    m.sala(2, 23, 2, 12, 8)                                   # Acampamento
    m.porta(11, 5, 0, 1)
    m.porta(22, 5, 1, 2)
    d = masmorra("sombras_1_vau", "Emboscada no Vau", m, "ar_livre", 1,
                 {"type": "rescue_prisoner", "xp": 0, "reward": {"gold": 40, "items": []}},
                 entrada=m.em(0, 0, 3), saida=m.em(2, 11, 3))
    d["monsters"] = [
        monstro("goblin_arqueiro", m.em(0, 8, 1), 0),
        monstro("goblin_arqueiro", m.em(0, 8, 6), 0),
        monstro("goblin_combatente", m.em(0, 7, 3), 0),
        monstro("goblin_combatente", m.em(1, 4, 2), 1),
        monstro("goblin_combatente", m.em(1, 4, 5), 1),
        monstro("goblin_combatente", m.em(1, 6, 3), 1),
        monstro("lobo_cinzento_customizado", m.em(1, 7, 6), 1),
        monstro("goblin_combatente", m.em(2, 3, 2), 2),
        monstro("goblin_combatente", m.em(2, 3, 5), 2),
        monstro("goblin_arqueiro", m.em(2, 8, 1), 2),
        monstro("goblin_arqueiro", m.em(2, 8, 6), 2),
        monstro("goblin_dual", m.em(2, 6, 4), 2),
    ]
    d["traps"] = [{"tipo": "armadilha_urso", "pos": m.em(0, 4, 3)}]
    d["chests"] = [{"pos": m.em(1, 8, 1), "gold": 12, "items": []}]
    d["prisoner"] = {"pos": m.em(2, 10, 1), "room_id": 2}
    d["decorations"] = [
        decor("vau_carroca", "carroca", m.em(1, 1, 5)),
        decor("vau_arvore_1", "arvore", m.em(0, 1, 0)),
        decor("vau_arvore_2", "arvore_grande", m.em(0, 2, 6)),
        decor("vau_arvore_3", "arvore_seca", m.em(1, 0, 0)),
        decor("vau_arvore_4", "arvore", m.em(2, 0, 7)),
        decor("vau_fogueira", "fogueira", m.em(2, 5, 1)),
    ]
    d["falas"] = [fala("vau_tome", m.em(2, 10, 1), "Tomé", "🧔",
                       "Aqui! Tirem-me destas cordas! A estrada para casa segue logo ali.", 4)]
    return d


# ─── 2 · Minas de Pedra-Funda ────────────────────────────────────────────────
def masmorra_minas():
    m = Mapa(42, 12)
    m.sala(0, 1, 3, 8, 6, role="entrance", locked=False)      # Boca da mina
    m.sala(1, 10, 3, 10, 6, role="trap")                      # Ponte das estacas
    m.sala(2, 21, 3, 9, 6)                                    # Galerias fundas
    m.sala(3, 31, 2, 10, 8, role="chest")                     # Depósito
    m.porta(9, 5, 0, 1)
    m.porta(20, 5, 1, 2)
    m.porta(30, 5, 2, 3)
    carta = {"id": "carta", "texto":
             "Ordem da Garra Negra: levem tudo o que brilha ao Covil. O guardião que "
             "não morre não gosta de esperar — e nunca, NUNCA, levem fogo para perto dele."}
    d = masmorra("sombras_2_minas", "Minas de Pedra-Funda", m, "masmorra", 2,
                 {"type": "open_key_chest", "xp": 0, "reward": {"gold": 60, "items": []}},
                 entrada=m.em(0, 0, 2))
    d["monsters"] = [
        monstro("kobold_lanceiro", m.em(0, 5, 1), 0),
        monstro("kobold_lanceiro", m.em(0, 5, 4), 0),
        monstro("kobold_lanceiro", m.em(0, 6, 2), 0),
        monstro("kobold_besteiro", m.em(0, 7, 0), 0),
        monstro("kobold_besteiro", m.em(0, 7, 5), 0),
        monstro("kobold_besteiro", m.em(1, 9, 0), 1),
        monstro("kobold_besteiro", m.em(1, 9, 5), 1),
        monstro("aranha_sombria", m.em(2, 3, 1), 2),
        monstro("aranha_sombria", m.em(2, 3, 4), 2),
        monstro("aranha_sombria", m.em(2, 6, 0), 2),
        monstro("aranha_sombria", m.em(2, 6, 5), 2),
        monstro("cobra_venenosa", m.em(2, 7, 2), 2),
        monstro("ogro_clava", m.em(3, 7, 3), 3),
        monstro("goblin_dual", m.em(3, 5, 1), 3),
        monstro("kobold_lanceiro", m.em(3, 5, 6), 3),
        monstro("kobold_lanceiro", m.em(3, 3, 4), 3),
    ]
    d["traps"] = [{"tipo": "fosso_estacas", "pos": m.em(1, 3, 2)},
                  {"tipo": "buraco", "pos": m.em(1, 6, 3)}]
    d["chests"] = [{"pos": m.em(3, 9, 3), "gold": 60, "key_objective": True,
                    "items": [{"id": "frasco_acido"}, {"id": "frasco_acido"},
                              {"id": "frasco_oleo"}, carta]}]
    d["falas"] = [fala("minas_kobold", m.em(1, 0, 2), "Kobold ferido", "🦎",
                       "Cuidado com as estacas... o chefe manda pisar só nas pedras escuras.", 3)]
    return d


# ─── 3a · Covil — Salões de Cima ─────────────────────────────────────────────
def masmorra_saloes():
    m = Mapa(40, 12)
    m.sala(0, 1, 3, 5, 6, role="entrance", locked=False)      # Portão
    m.sala(1, 7, 2, 9, 8, required=True, required_mode="clear")    # Guarita
    m.sala(2, 17, 2, 10, 8, required=True, required_mode="clear")  # Salão de armas
    m.sala(3, 28, 2, 10, 8, required=True, required_mode="clear")  # Escadaria
    m.porta(6, 5, 0, 1)
    m.porta(16, 5, 1, 2)
    m.porta(27, 5, 2, 3)
    d = masmorra("sombras_3a_saloes", "Covil da Garra Negra — Salões de Cima", m,
                 "masmorra", 3,
                 {"type": "salas_obrigatorias", "xp": 0, "reward": {"gold": 0, "items": []}},
                 entrada=m.em(0, 0, 2))
    d["monsters"] = [
        monstro("goblin_dual", m.em(1, 5, 2), 1),
        monstro("goblin_dual", m.em(1, 5, 5), 1),
        monstro("goblin_arqueiro", m.em(1, 8, 1), 1),
        monstro("goblin_arqueiro", m.em(1, 8, 6), 1),
        monstro("orc_guerreiro", m.em(2, 5, 2), 2),
        monstro("orc_guerreiro", m.em(2, 5, 5), 2),
        monstro("goblin_combatente", m.em(2, 7, 1), 2),
        monstro("goblin_combatente", m.em(2, 7, 6), 2),
        monstro("orc_guerreiro", m.em(3, 5, 3), 3),
        monstro("dark_mage", m.em(3, 8, 4), 3),
        monstro("goblin_dual", m.em(3, 4, 1), 3),
        monstro("goblin_dual", m.em(3, 4, 6), 3),
    ]
    return d


# ─── 3b · Covil — O Trono de Pedra ───────────────────────────────────────────
def masmorra_trono():
    m = Mapa(24, 18)
    m.sala(0, 1, 1, 8, 8, role="entrance", locked=False)      # Poço antigo
    m.sala(1, 10, 1, 13, 10, role="boss")                     # Trono
    m.sala(2, 1, 10, 8, 6, locked=False)                      # Esconderijo (secreto)
    m.porta(9, 4, 0, 1)
    passagem = [4, 9]                  # parede entre o Poço (y ≤ 8) e o Esconderijo (y ≥ 10)
    d = masmorra("sombras_3b_trono", "Covil da Garra Negra — O Trono de Pedra", m,
                 "masmorra", 3,
                 {"type": "kill_target", "xp": 0, "reward": {"gold": 120, "items": []}},
                 entrada=m.em(0, 1, 1))
    d["monsters"] = [
        monstro("troll", m.em(1, 9, 4), 1, alvo=True),
        monstro("orc_guerreiro", m.em(1, 7, 2), 1),
        monstro("goblin_arqueiro", m.em(1, 11, 1), 1),
        monstro("goblin_arqueiro", m.em(1, 11, 8), 1),
        monstro("bugbear_sombras", m.em(2, 4, 4), 2),
        monstro("aranha_sombria", m.em(2, 1, 3), 2),
        monstro("aranha_sombria", m.em(2, 6, 3), 2),
    ]
    d["decorations"] = [
        decor("trono_fonte", "fonte", m.em(0, 5, 1), charges=3),
        decor("trono_estante", "estante_livros", m.em(0, 5, 6)),
        decor("trono_braseiro_1", "fogueira", m.em(1, 6, 1)),
        decor("trono_braseiro_2", "fogueira", m.em(1, 6, 8)),
    ]
    d["secret_passages"] = [{"id": "trono_passagem", "type": "mechanism", "pos": passagem,
                             "key_decor_ids": ["trono_estante"], "keys_mode": "any"}]
    d["chests"] = [{"pos": m.em(2, 6, 1), "gold": 30, "items": [{"id": ANEL_ID}]}]
    d["falas"] = [fala("trono_pista", m.em(0, 3, 5), "Vento", "🌬️",
                       "O vento assobia atrás da estante… como se houvesse um corredor do outro lado.", 2)]
    return d


def masmorras():
    return {"sombras_1_vau.json": masmorra_vau(), "sombras_2_minas.json": masmorra_minas(),
            "sombras_3a_saloes.json": masmorra_saloes(), "sombras_3b_trono.json": masmorra_trono()}


# ─── História ────────────────────────────────────────────────────────────────
# Cada slide só leva texto; a arte que ele pede fica em ARTES_PEDIDAS, que o
# --simular imprime (o autor sobe as imagens pelo editor depois).
ARTES_PEDIDAS = []


def historia(chave, slides, audio=None):
    out = []
    for i, (texto, arte) in enumerate(slides):
        ARTES_PEDIDAS.append((f"{chave}#{i + 1}", arte))
        out.append({"text": texto, "fit": "contain"})
    h = {"slides": out}
    if audio:
        h["audio"] = audio
    return h


def _etapa(arquivo, intro, outro, encadear=False):
    return {"file": arquivo, "encadear": encadear, "intro": intro, "outro": outro}


def destinos():
    ARTES_PEDIDAS.clear()
    base_x, base_y = S.WORLD_LOCATIONS["alva_e_luz"]["x"], S.WORLD_LOCATIONS["alva_e_luz"]["y"]

    def perto(dx, dy):
        return round(max(0, min(100, base_x + dx)), 2), round(max(0, min(100, base_y + dy)), 2)

    vau_intro = historia("vau.intro", [
        ("A Estrada do Vau atravessa o bosque a leste de Alva e Luz. Há três luas nenhuma "
         "caravana chega do outro lado.", "estrada de floresta ao entardecer, marcas de rodas na lama"),
        ("Na curva do rio, uma carroça tombada. Cordas cortadas. E, entre as árvores, o "
         "brilho de olhos pequenos e amarelos.", "carroça tombada, goblins espreitando no mato"),
    ], MUSICA_ABERTURA)
    vau_outro = historia("vau.outro", [
        ("— Não era só roubo — diz Tomé, esfregando os pulsos. — Eles levavam a carga para "
         "as velhas minas de Pedra-Funda. Falavam de uma garra negra.",
         "Tomé ferido junto à fogueira do acampamento"),
    ])
    minas_intro = historia("minas.intro", [
        ("As minas de Pedra-Funda foram abandonadas quando a veia de prata secou. Agora, "
         "dizem os mineiros, a montanha voltou a ranger à noite.",
         "entrada de mina escorada, trilhos enferrujados"),
        ("Pegadas miúdas e rastros de carga arrastada descem para o escuro.",
         "túnel com pegadas de kobold iluminado por tocha"),
    ], MUSICA_ABERTURA)
    minas_outro = historia("minas.outro", [
        ("No cofre, frascos que os kobolds nunca entenderam — ácido e óleo — e um bilhete "
         "com o sinal de uma garra negra: o Covil, e um guardião que não morre.",
         "cofre aberto com frascos e um bilhete marcado por uma garra"),
    ])
    covil_intro = historia("covil.intro", [
        ("O Covil da Garra Negra fica numa fortaleza em ruínas, na encosta sobre as minas.",
         "fortaleza em ruínas na encosta, fumaça saindo das seteiras"),
        ("Daqui não há volta até o fim: os andares se emendam, e o que for gasto lá dentro "
         "não se recupera.", "portão de pedra entreaberto, escuro lá dentro"),
    ], MUSICA_ABERTURA)
    saloes_outro = historia("covil.transicao", [
        ("A escadaria desce para o calor. Cheiro de fumaça e de carne podre. Algo enorme "
         "respira lá embaixo.", "escada de pedra descendo para um salão iluminado por braseiros"),
    ])
    trono_intro = historia("trono.intro", [
        ("No Trono de Pedra, entre braseiros, o guardião se levanta: um troll. As feridas "
         "que os heróis abrem se fecham diante dos olhos.",
         "troll enorme de pé diante de um trono de pedra, braseiros acesos"),
        ("Ácido e fogo. É o que diz o bilhete. É o que sobrou do cofre.",
         "mão segurando um frasco de ácido"),
    ], MUSICA_TROLL)
    trono_outro = historia("trono.outro", [
        ("O troll tomba de vez. O bando da Garra Negra se desfaz na noite.",
         "troll caído entre braseiros apagados"),
    ])
    fim_rota = historia("covil.fim", [
        ("Semanas depois, as caravanas voltam a cruzar o Vau. Em Alva e Luz, o nome do "
         "grupo corre de mesa em mesa na taverna.", "praça de Alva e Luz em festa, caravana chegando"),
        ("E, em algum lugar sob a fortaleza, uma estante esconde um segredo que talvez "
         "ninguém tenha encontrado.", "estante de livros na penumbra, uma fresta de escuridão atrás"),
    ])

    def destino(did, nome, dx, dy, custo, etapas, requisito, renome, outro_rota=""):
        x, y = perto(dx, dy)
        return {"id": did, "nome": nome, "x": x, "y": y, "fome": custo, "sede": custo,
                "dungeons": etapas, "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
                "oculto_ate_liberar": True, "revisitavel": False, "outro_rota": outro_rota,
                "requisito": S._clean_requirement(requisito), "renome_recompensa": renome}

    return {
        "sombras_vau": destino("sombras_vau", "Emboscada no Vau", 6, 3, 1,
                               [_etapa("sombras_1_vau.json", vau_intro, vau_outro)],
                               {"fato": FATO_GANCHO}, 1),
        "sombras_minas": destino("sombras_minas", "Minas de Pedra-Funda", 11, -4, 2,
                                 [_etapa("sombras_2_minas.json", minas_intro, minas_outro)],
                                 {"aventura_id": "sombras_vau"}, 1),
        "sombras_covil": destino("sombras_covil", "Covil da Garra Negra", 16, -9, 3,
                                 [_etapa("sombras_3a_saloes.json", covil_intro, saloes_outro, encadear=True),
                                  _etapa("sombras_3b_trono.json", trono_intro, trono_outro)],
                                 {"aventura_id": "sombras_minas"}, 2, outro_rota=fim_rota),
    }


# ─── Anel e conversa ─────────────────────────────────────────────────────────
def anel_bruto():
    return {"id": ANEL_ID, "name": "Anel da Garra Negra", "emoji": "💍", "item_type": "ring",
            "bonuses": [{"effect": "atk_bonus", "value": 1}, {"effect": "vision", "value": 1}],
            "granted_ability": "hero_rogue_esconder_sombras",
            "allowed_classes": [], "price": 250,
            "disponibilidade": {"loja": False, "baus": True, "loot_monstro": False}}


def conversa_bartender():
    return {"id": CONVERSA_ID,
            "texto": ("As caravanas que saem pela Estrada do Vau não chegam do outro lado. "
                      "O último cocheiro, Tomé, sumiu com a carga há três luas. Se vocês "
                      "forem para os lados do Vau... tomem cuidado com o mato."),
            "requisito": {}, "efeito": {"fato": FATO_GANCHO}, "uma_vez": True}


# ─── Medidas (compartilhadas com --simular e com os testes) ─────────────────
def nd_por_sala(defn):
    """ND por sala = monster_cr dos monstros + trap_cr das armadilhas dentro dela."""
    defs = {m["type"]: m for m in S.MONSTER_DEFS}
    nd = {r["id"]: 0.0 for r in defn["rooms"]}
    for mo in defn.get("monsters", []):
        nd[mo["room_id"]] += S.monster_cr(defs[mo["type"]])
    for t in defn.get("traps", []):
        for r in defn["rooms"]:
            if r["x"] <= t["pos"][0] < r["x"] + r["w"] and r["y"] <= t["pos"][1] < r["y"] + r["h"]:
                nd[r["id"]] += S.trap_cr(S.ARMADILHAS[t["tipo"]])
    return {rid: round(v, 3) for rid, v in nd.items()}


def faixa(nd, poder):
    """Mesmas faixas de src/difficulty.js (razão ND ÷ poder)."""
    razao = nd / max(1, poder)
    for chave, teto in (("facil", 0.4), ("equilibrada", 0.8), ("dificil", 1.2)):
        if razao < teto:
            return chave
    return "mortal"


def salas_alcancaveis(defn, passagens_abertas=False):
    """Ids das salas alcançáveis a pé a partir da entrada (FLOOR/DOOR ortogonal)."""
    tiles = [row[:] for row in defn["tiles"]]
    if passagens_abertas:
        for sp in defn.get("secret_passages", []):
            tiles[sp["pos"][1]][sp["pos"][0]] = FLOOR
    ini = (defn["entrance"]["x"], defn["entrance"]["y"])
    vistos, fila = {ini}, [ini]
    while fila:
        x, y = fila.pop()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (0 <= ny < len(tiles) and 0 <= nx < len(tiles[0])
                    and tiles[ny][nx] in (FLOOR, DOOR) and (nx, ny) not in vistos):
                vistos.add((nx, ny))
                fila.append((nx, ny))
    return {r["id"] for r in defn["rooms"]
            if any((x, y) in vistos for x in range(r["x"], r["x"] + r["w"])
                   for y in range(r["y"], r["y"] + r["h"]))}


# ─── Montagem ────────────────────────────────────────────────────────────────
def preparar():
    """Monta e valida TUDO em memória. Levanta ValueError na primeira invalidez."""
    ok, anel = S._validate_custom_item(anel_bruto())
    if not ok:
        raise ValueError(f"anel inválido: {anel}")
    outros = [r for r in S._read_custom_items() if isinstance(r, dict) and r.get("id") != ANEL_ID]
    S._apply_custom_items(outros + [anel])      # o baú do Trono precisa achar o anel
    mm = masmorras()
    for arquivo, defn in mm.items():
        ok, msg = S.validar_dungeon(defn)
        if not ok:
            raise ValueError(f"{arquivo}: {msg}")
    return {"masmorras": mm, "destinos": destinos(), "anel": anel,
            "conversa": S._clean_scene_conversations([conversa_bartender()], "")[0]}
```

Pontos de desenho que o código já trata (não "simplifique"):
- A porta entre duas salas vizinhas fica na parede de 1 casa entre elas e é listada nas **duas** salas (`door_rooms` destranca toda sala que a lista).
- A estante do Trono fica **ao lado** da casa que dá acesso à passagem (`[4,8]`), nunca em cima dela; e **não** tem `key_objective`.
- `preparar()` registra o anel em memória (`_apply_custom_items`) antes de validar as masmorras, porque o baú do Esconderijo o referencia.

- [ ] **Step 2: Conferir que monta e valida**

Run:
```bash
PYTHONIOENCODING=utf-8 python -c "import sys; sys.path.insert(0,'tools'); import gerar_campanha_sombras as G; a=G.preparar(); print(sorted(a)); print(sorted(a['masmorras'])); print(len(G.ARTES_PEDIDAS), 'artes')"
```
Expected:
```
['anel', 'conversa', 'destinos', 'masmorras']
['sombras_1_vau.json', 'sombras_2_minas.json', 'sombras_3a_saloes.json', 'sombras_3b_trono.json']
14 artes
```
(`preparar()` levanta `ValueError` se qualquer masmorra ou o anel for inválido.)

- [ ] **Step 3: Commit**

```bash
git add tools/gerar_campanha_sombras.py
git commit -m "feat(campanha): gerador monta as 4 masmorras, destinos, anel e conversa

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Suíte da campanha — mapas, corrente, objetivos, troll, segredo e curva

**Files:**
- Create: `tools/test_campanha_sombras.py`

- [ ] **Step 1: Criar a suíte**

Crie `tools/test_campanha_sombras.py` com exatamente este conteúdo. A seção `[6]`, de gravação, entra na Task 4.

```python
"""Campanha "Sombras sob Alva e Luz". Roda da raiz: python tools/test_campanha_sombras.py

Não depende dos arquivos gerados no repositório: monta tudo pelo gerador, grava
as masmorras numa pasta temporária (DUNGEONS_DIR) e os destinos/cena em memória,
e restaura o estado do servidor no fim de cada seção.
Spec: docs/superpowers/specs/2026-09-25-campanha-sombras-alva-e-luz-design.md
"""
import asyncio
import json
import os
import shutil
import sys
import tempfile
from copy import deepcopy

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for p in (RAIZ, AQUI):
    if p not in sys.path:
        sys.path.insert(0, p)
import server as S                       # noqa: E402
import gerar_campanha_sombras as G       # noqa: E402

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


ART = G.preparar()
MM = ART["masmorras"]

# Faixas planejadas na spec (ND arredondado, faixa pelo termômetro).
ESPERADO = {
    "sombras_1_vau.json": {0: (1.0, "facil"), 1: (1.25, "facil"), 2: (2.0, "equilibrada")},
    "sombras_2_minas.json": {0: (1.25, "facil"), 1: (0.95, "facil"), 2: (2.0, "facil"),
                             3: (3.5, "equilibrada")},
    "sombras_3a_saloes.json": {0: (0.0, "facil"), 1: (2.5, "facil"), 2: (2.5, "facil"),
                               3: (3.5, "facil")},
    "sombras_3b_trono.json": {0: (0.0, "facil"), 1: (5.5, "equilibrada"), 2: (2.5, "facil")},
}


# ─── Sala de jogo pelo caminho real ──────────────────────────────────────────
class Ambiente:
    """Masmorras numa pasta temporária + destinos e conversa injetados em memória.
    Restaura DUNGEONS_DIR, WORLD_ADVENTURES e a cena da taverna ao sair."""

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="sombras_")
        for arquivo, defn in MM.items():
            with open(os.path.join(self.tmp, arquivo), "w", encoding="utf-8") as f:
                json.dump(defn, f, ensure_ascii=False)
        self.dir_antigo = S.DUNGEONS_DIR
        self.aventuras_antigas = deepcopy(S.WORLD_ADVENTURES)
        self.cena_antiga = deepcopy(S.CITY_SCENES["alva_e_luz"]["taverna"])
        S.DUNGEONS_DIR = self.tmp
        S.WORLD_ADVENTURES.update(deepcopy(ART["destinos"]))
        barman = next(s for s in S.CITY_SCENES["alva_e_luz"]["taverna"]["slots"] if s.get("id") == "barman")
        barman["conversations"] = [c for c in barman.get("conversations", [])
                                   if c.get("id") != G.CONVERSA_ID] + [deepcopy(ART["conversa"])]
        return self

    def __exit__(self, *exc):
        S.DUNGEONS_DIR = self.dir_antigo
        S.WORLD_ADVENTURES.clear()
        S.WORLD_ADVENTURES.update(self.aventuras_antigas)
        S.CITY_SCENES["alva_e_luz"]["taverna"] = self.cena_antiga
        shutil.rmtree(self.tmp, ignore_errors=True)


def sala_na_cidade():
    r = S.GameRoom("SOMB")
    erros = []

    async def noop(*a, **k):
        pass

    async def cap(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            erros.append(str(msg.get("msg")))
    r.gm_say = noop
    r.broadcast = noop
    r.send_to = cap
    r.broadcast_city_state = noop
    r.push_state = noop
    r.push_state_or_city = noop
    r._broadcast_dado = noop
    r._checkpoint_savegame = lambda *a, **k: None
    for i, cls in enumerate(("warrior", "cleric", "rogue", "mage")):
        pid = f"h{i}"
        r.players[pid] = S.make_player(pid, cls, cls, i)
        r.connections[pid] = object()
    r.host_pid = "h0"
    r.phase = "city"
    r.world_location = "alva_e_luz"
    r._is_turn = lambda pid: True
    r._erros = erros
    return r


async def entrar(r, destino):
    await r.handle_world_adventure("h0", destino)
    await r._liberar_intro_masmorra(True)


def junto(r, pid, pos):
    """Põe o herói numa casa livre vizinha de `pos` (Chebyshev 1)."""
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        x, y = pos[0] + dx, pos[1] + dy
        if r.tiles[y][x] == S.FLOOR and not r._entity_blocks(x, y):
            r.players[pid]["pos"] = [x, y]
            return True
    return False


# ─── [1] Mapas ───────────────────────────────────────────────────────────────
def secao_mapas():
    print("\n[1] As 4 masmorras: validade, ocupação, ND e conectividade")
    check("o gerador produz as 4 masmorras", sorted(MM) == sorted(G.ARQUIVOS))
    for arquivo, defn in MM.items():
        ok, msg = S.validar_dungeon(defn)
        check(f"{arquivo}: validar_dungeon ({msg})", ok)
        ocupado, conflito = {}, []

        def por(p, oque):
            k = tuple(p)
            if k in ocupado:
                conflito.append((k, ocupado[k], oque))
            ocupado[k] = oque
        for mo in defn["monsters"]:
            por(mo["pos"], mo["type"])
        for de in defn["decorations"]:
            w, h = S.DECOR_TYPES[de["type"]].get("size", [1, 1])
            for dx in range(w):
                for dy in range(h):
                    por([de["pos"][0] + dx, de["pos"][1] + dy], de["id"])
        for ch in defn["chests"]:
            por(ch["pos"], "baú")
        for t in defn["traps"]:
            por(t["pos"], t["tipo"])
        if defn.get("prisoner"):
            por(defn["prisoner"]["pos"], "prisioneiro")
        por([defn["entrance"]["x"], defn["entrance"]["y"]], "entrada")
        if defn.get("exit"):
            por([defn["exit"]["x"], defn["exit"]["y"]], "saída")
        check(f"{arquivo}: nenhuma casa com duas coisas {conflito}", not conflito)
        poder = defn["expected_party"]["heroes"] * defn["expected_party"]["level"]
        nd = G.nd_por_sala(defn)
        medido = {rid: (round(v, 2), G.faixa(v, poder)) for rid, v in nd.items()}
        check(f"{arquivo}: ND e faixa por sala batem com a spec {medido}", medido == ESPERADO[arquivo])
        todas = {r["id"] for r in defn["rooms"]}
        if arquivo == "sombras_3b_trono.json":
            check("trono: o esconderijo NÃO é alcançável com a passagem fechada",
                  G.salas_alcancaveis(defn) == todas - {2})
            check("trono: com a passagem aberta, todas as salas são alcançáveis",
                  G.salas_alcancaveis(defn, passagens_abertas=True) == todas)
        else:
            check(f"{arquivo}: todas as salas alcançáveis da entrada", G.salas_alcancaveis(defn) == todas)
    party = {a: d["expected_party"] for a, d in MM.items()}
    check("curva-alvo: Vau 1, Minas 2, Covil 3",
          [party[a]["level"] for a in G.ARQUIVOS] == [1, 2, 3, 3]
          and all(p["heroes"] == 4 for p in party.values()))


# ─── [2] Destinos e corrente de requisitos ───────────────────────────────────
async def secao_corrente():
    print("\n[2] Destinos ocultos e corrente de requisitos")
    dest = ART["destinos"]
    for did, d in dest.items():
        check(f"{did}: oculto até liberar, não revisitável", d["oculto_ate_liberar"] and not d["revisitavel"])
        check(f"{did}: história já no formato limpo do servidor",
              all(S._clean_story_field(e["intro"]) == e["intro"] and S._clean_story_field(e["outro"]) == e["outro"]
                  for e in d["dungeons"]) and S._clean_story_field(d["outro_rota"]) == d["outro_rota"])
    check("Covil: 2 etapas, a primeira emendada",
          [e["encadear"] for e in dest["sombras_covil"]["dungeons"]] == [True, False])
    with Ambiente():
        r = sala_na_cidade()
        check("sem o fato, o Vau não aparece no mapa", not r._aventura_visivel(S.WORLD_ADVENTURES["sombras_vau"]))
        await r.handle_world_adventure("h0", "sombras_vau")
        check("…e entrar nele é recusado como destino inválido", r.phase == "city")
        await r.handle_scene_npc("h0", "taverna", "barman", G.CONVERSA_ID)
        check("a conversa do Bartender grava o fato", G.FATO_GANCHO in r.fatos)
        check("com o fato, o Vau aparece", r._aventura_visivel(S.WORLD_ADVENTURES["sombras_vau"]))
        check("as Minas continuam ocultas antes do Vau", not r._aventura_visivel(S.WORLD_ADVENTURES["sombras_minas"]))
        r.world_adventure_progress["sombras_vau"] = 1
        check("Vau concluído libera as Minas", r._aventura_visivel(S.WORLD_ADVENTURES["sombras_minas"]))
        check("o Covil ainda não", not r._aventura_visivel(S.WORLD_ADVENTURES["sombras_covil"]))
        r.world_adventure_progress["sombras_minas"] = 1
        check("Minas concluídas liberam o Covil", r._aventura_visivel(S.WORLD_ADVENTURES["sombras_covil"]))


# ─── [3] Objetivos ───────────────────────────────────────────────────────────
async def secao_objetivos():
    print("\n[3] Objetivos de cada masmorra")
    with Ambiente():
        r = sala_na_cidade()
        r.fatos.add(G.FATO_GANCHO)
        await entrar(r, "sombras_vau")
        check("Vau carrega pelo mapa-múndi", r.phase == "playing" and r.selected_dungeon == "sombras_1_vau.json")
        check("Vau é ar livre", r.ambiente == "ar_livre")
        junto(r, "h0", r.prisoner["pos"])
        await r.handle_libertar_prisioneiro("h0")
        check("Tomé é solto", r.prisoner.get("freed") is True)
        await r._check_objectives()
        check("soltar não basta: é preciso escoltá-lo", not r.mission_complete_pending)
        r.prisoner["pos"] = [r.exit_pos[0] - 1, r.exit_pos[1]]
        await r._check_objectives()
        check("Tomé junto da saída cumpre o objetivo", r.mission_complete_pending)

    with Ambiente():
        r = sala_na_cidade()
        r.world_adventure_progress["sombras_vau"] = 1
        await entrar(r, "sombras_minas")
        cid, bau = next((cid, c) for cid, c in r.chests.items()
                        if any(it.get("id") == "frasco_acido" for it in c["items"]))
        ids = sorted(it["id"] for it in bau["items"])
        check(f"o cofre traz 2 ácidos, 1 óleo e o bilhete {ids}",
              ids == ["carta", "frasco_acido", "frasco_acido", "frasco_oleo"])
        junto(r, "h0", bau["pos"])
        await r.handle_take_from_chest("h0", cid, "gold", 0)
        await r._check_objectives()
        check("abrir o cofre cumpre o objetivo das Minas", r.mission_complete_pending)

    with Ambiente():
        r = sala_na_cidade()
        r.world_adventure_progress.update({"sombras_vau": 1, "sombras_minas": 1})
        await entrar(r, "sombras_covil")
        check("o Covil começa nos Salões", r.selected_dungeon == "sombras_3a_saloes.json")
        await r._check_objectives()
        check("com monstros vivos, as salas obrigatórias não estão cumpridas", not r.mission_complete_pending)
        for m in r.monsters.values():
            m["hp"] = 0
        await r._check_objectives()
        check("limpar as 3 salas obrigatórias cumpre", r.mission_complete_pending)
        r.players["h1"]["hp"] = 3
        await r.handle_encerrar_missao("h0")
        await r._liberar_intro_masmorra(True)
        check("encerrar emenda direto no Trono", r.phase == "playing" and r.selected_dungeon == "sombras_3b_trono.json")
        check("…sem recuperar HP (3 → 3)", r.players["h1"]["hp"] == 3)
        troll = next(m for m in r.monsters.values() if m["type"] == "troll")
        bug = next(m for m in r.monsters.values() if m["type"] == "bugbear_sombras")
        check("o troll é o alvo do objetivo", troll.get("authored_target"))
        troll["troll_regeneracao_bloqueada"] = True
        troll["hp"] = 0
        await r._monster_dies(troll, "h0")
        await r._check_objectives()
        check("matar o troll cumpre o Trono", r.mission_complete_pending)
        check("…com o Bugbear ainda vivo (ele é opcional)", bug["hp"] > 0)


# ─── [4] Troll × ácido ───────────────────────────────────────────────────────
async def secao_troll():
    print("\n[4] O ácido do cofre para a regeneração do troll")
    with Ambiente():
        r = sala_na_cidade()
        r.world_adventure_progress.update({"sombras_vau": 1, "sombras_minas": 1})
        await entrar(r, "sombras_covil")
        for m in r.monsters.values():
            m["hp"] = 0
        await r._check_objectives()
        await r.handle_encerrar_missao("h0")
        await r._liberar_intro_masmorra(True)
        troll = next(m for m in r.monsters.values() if m["type"] == "troll")
        p = r.players["h2"]
        acido = next(dict(i) for i in S.SHOP_MERCHANT if i["id"] == "frasco_acido")
        junto(r, "h2", troll["pos"])
        for _ in range(40):
            if troll.get("troll_regeneracao_bloqueada"):
                break
            p["bag"].append(dict(acido))
            p["action_done"] = False
            await r.handle_throw_item("h2", {"item_id": "frasco_acido", "target_id": troll["id"]})
        check("acertar o frasco de ácido bloqueia a regeneração", troll.get("troll_regeneracao_bloqueada"))
        troll["hp"] = 20
        await r._processar_regeneracao_troll_inicio(troll)
        check("com a regeneração bloqueada, o troll não recupera PV", troll["hp"] == 20)


# ─── [5] Segredo do Bugbear ──────────────────────────────────────────────────
async def secao_segredo():
    print("\n[5] Estante, esconderijo e o Anel da Garra Negra")
    check("o anel passa no validador do Editor de Itens", ART["anel"]["id"] == G.ANEL_ID)
    check("o anel só aparece em baús", ART["anel"]["disponibilidade"] == {"loja": False, "baus": True, "loot_monstro": False})
    with Ambiente():
        r = sala_na_cidade()
        r.world_adventure_progress.update({"sombras_vau": 1, "sombras_minas": 1})
        await entrar(r, "sombras_covil")
        for m in r.monsters.values():
            m["hp"] = 0
        await r._check_objectives()
        await r.handle_encerrar_missao("h0")
        await r._liberar_intro_masmorra(True)
        sp = r.secret_passages[0]
        x, y = sp["pos"]
        check("a passagem começa fechada (parede)", r.tiles[y][x] == S.WALL and not sp["opened"])
        estante = next(d for d in r.decorations if d["id"] == "trono_estante")
        check("a estante NÃO marca objetivo de baú-chave", not estante.get("key_objective"))
        junto(r, "h0", estante["pos"])
        await r.handle_activate_decor_mechanism("h0", "trono_estante")
        check("ativar a estante abre a passagem", sp["opened"] and r.tiles[y][x] != S.WALL)
        bau = next(c for c in r.chests.values() if any(it.get("id") == G.ANEL_ID for it in c["items"]))
        check("o baú do esconderijo guarda o anel", bau is not None)
        guerreiro = r.players["h0"]
        anel = next(dict(it) for it in bau["items"] if it.get("id") == G.ANEL_ID)
        guerreiro["bag"].append(anel)
        await r.handle_equip_from_bag("h0", len(guerreiro["bag"]) - 1)
        check("equipado num guerreiro, concede Esconder nas Sombras",
              "hero_rogue_esconder_sombras" in S._habilidades_concedidas(guerreiro))


# ─── [7] Régua da curva de XP (relatório) ────────────────────────────────────
def secao_curva():
    print("\n[7] Régua da curva de XP — RELATÓRIO, não cobrança (conserto é o próximo subprojeto)")
    defs = {m["type"]: m for m in S.MONSTER_DEFS}
    nivel, xp = 1, 0
    for arquivo in G.ARQUIVOS:
        ini = nivel
        for mo in MM[arquivo]["monsters"]:
            if mo["type"] == "bugbear_sombras" or mo["room_id"] == 2 and arquivo == "sombras_3b_trono.json":
                continue    # o esconderijo é opcional
            cr = S.monster_cr(defs[mo["type"]])
            xp += max(1, int(150 * nivel * (2 ** (cr - 1))) // 4)
            if xp >= nivel * 30:
                xp -= nivel * 30
                nivel += 1
        print(f"     {arquivo}: entra no nível {ini}, sai no {nivel} "
              f"(alvo: {MM[arquivo]['expected_party']['level']})")
    check("relatório da curva produzido", True)


async def main():
    secao_mapas()
    await secao_corrente()
    await secao_objetivos()
    await secao_troll()
    await secao_segredo()
    secao_curva()
    print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
    sys.exit(1 if FAIL else 0)


asyncio.run(main())
```

- [ ] **Step 2: Rodar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_campanha_sombras.py 2>&1 | tail -12`
Expected: `59 passaram, 0 falharam`, com o relatório da seção `[7]` mostrando o nível disparando (Vau sai no 9, Minas no 22…) — é o registro do defeito da curva de XP, não uma falha.

Se "com monstros vivos, as salas obrigatórias não estão cumpridas" falhar, a Task 1 não está aplicada.

- [ ] **Step 3: Commit**

```bash
git add tools/test_campanha_sombras.py
git commit -m "test(campanha): mapas, corrente de requisitos, objetivos, troll, segredo e curva

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Gerador — gravação não destrutiva, relatório e linha de comando

**Files:**
- Modify: `tools/gerar_campanha_sombras.py` (acrescentar ao final)
- Modify: `tools/test_campanha_sombras.py` (seção `[6]` + chamada no `main`)

- [ ] **Step 1: Escrever o teste de gravação**

Em `tools/test_campanha_sombras.py`, insira imediatamente antes da linha que começa com `# ─── [7] Régua da curva de XP`:

```python
# ─── [6] Gravação não destrutiva ─────────────────────────────────────────────
def secao_gravacao():
    print("\n[6] O gerador só toca no que é dele")
    tmp = tempfile.mkdtemp(prefix="sombras_grava_")
    try:
        c = {"dungeons_dir": os.path.join(tmp, "dungeons"),
             "adventures": os.path.join(tmp, "world_adventures.json"),
             "scenes": os.path.join(tmp, "city_scenes.json"),
             "items": os.path.join(tmp, "itens_personalizados.json"),
             "items_index": os.path.join(tmp, "editor_items_custom.js"),
             "assinaturas": os.path.join(tmp, "assinaturas.json")}
        for chave, origem in (("adventures", S.WORLD_ADVENTURES_FILE), ("scenes", S.CITY_SCENES_FILE),
                              ("items", S.CUSTOM_ITEMS_FILE)):
            if os.path.exists(origem):
                shutil.copy(origem, c[chave])
            else:
                with open(c[chave], "w", encoding="utf-8") as f:
                    f.write("[]" if chave == "items" else "{}")
        antes = {k: json.load(open(c[k], encoding="utf-8")) for k in ("adventures", "scenes", "items")}
        G.aplicar(ART, caminhos=c, regen_editor=False)
        depois = {k: json.load(open(c[k], encoding="utf-8")) for k in ("adventures", "scenes", "items")}
        check("destinos alheios intactos",
              {k: v for k, v in depois["adventures"].items() if not k.startswith("sombras_")}
              == {k: v for k, v in antes["adventures"].items() if not k.startswith("sombras_")})
        check("os 3 destinos da campanha gravados", {"sombras_vau", "sombras_minas", "sombras_covil"} <= set(depois["adventures"]))
        def sem_conversa(cenas):
            cenas = deepcopy(cenas)
            for s in cenas["alva_e_luz"]["taverna"]["slots"]:
                if s.get("id") == "barman":
                    s["conversations"] = [cv for cv in s.get("conversations", []) if cv.get("id") != G.CONVERSA_ID]
            return cenas
        check("cenas intactas fora da conversa nova", sem_conversa(depois["scenes"]) == sem_conversa(antes["scenes"]))
        check("itens alheios intactos",
              [i for i in depois["items"] if i.get("id") != G.ANEL_ID] == [i for i in antes["items"] if i.get("id") != G.ANEL_ID])
        bytes1 = {k: open(c[k], "rb").read() for k in ("adventures", "scenes", "items")}
        G.aplicar(ART, caminhos=c, regen_editor=False)
        check("rodar de novo produz os mesmos bytes", all(open(c[k], "rb").read() == v for k, v in bytes1.items()))
        vau = os.path.join(c["dungeons_dir"], "sombras_1_vau.json")
        editado = json.load(open(vau, encoding="utf-8"))
        editado["name"] = "Emboscada no Vau (editada no editor)"
        json.dump(editado, open(vau, "w", encoding="utf-8"), ensure_ascii=False)
        cenas_antes = open(c["scenes"], "rb").read()
        try:
            G.aplicar(ART, caminhos=c, regen_editor=False)
            check("masmorra editada à mão faz o gerador recusar", False)
        except G.Conflito:
            check("masmorra editada à mão faz o gerador recusar", True)
        check("…sem gravar nada (tudo ou nada)",
              json.load(open(vau, encoding="utf-8"))["name"].endswith("(editada no editor)")
              and open(c["scenes"], "rb").read() == cenas_antes)
        G.aplicar(ART, caminhos=c, forcar=True, regen_editor=False)
        check("--forcar regrava", json.load(open(vau, encoding="utf-8"))["name"] == "Emboscada no Vau")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

E no `async def main()`, troque a linha `    await secao_segredo()` por:

```python
    await secao_segredo()
    secao_gravacao()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_campanha_sombras.py 2>&1 | tail -5`
Expected: `AttributeError: module 'gerar_campanha_sombras' has no attribute 'aplicar'`.

- [ ] **Step 3: Implementar a gravação**

Acrescente ao FINAL de `tools/gerar_campanha_sombras.py`:

```python
# ─── Gravação ────────────────────────────────────────────────────────────────
def caminhos_padrao():
    return {"dungeons_dir": S.DUNGEONS_DIR, "adventures": S.WORLD_ADVENTURES_FILE,
            "scenes": S.CITY_SCENES_FILE, "items": S.CUSTOM_ITEMS_FILE,
            "items_index": S.CUSTOM_ITEMS_INDEX, "assinaturas": ASSINATURAS}


def _ler_json(caminho, padrao):
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return padrao


def _gravar_json(caminho, dados):
    tmp = caminho + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    os.replace(tmp, caminho)


def assinatura(defn):
    texto = json.dumps(defn, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


class Conflito(Exception):
    pass


def aplicar(artefatos, caminhos=None, forcar=False, regen_editor=True):
    """Grava os artefatos. Só toca no que é da campanha. Tudo ou nada: confere
    conflitos antes de gravar o primeiro arquivo."""
    c = dict(caminhos_padrao(), **(caminhos or {}))
    assin = _ler_json(c["assinaturas"], {})
    conflitos = []
    for arquivo in artefatos["masmorras"]:
        caminho = os.path.join(c["dungeons_dir"], arquivo)
        if os.path.exists(caminho) and not forcar:
            atual = _ler_json(caminho, None)
            if atual is None or assin.get(arquivo) != assinatura(atual):
                conflitos.append(arquivo)
    if conflitos:
        raise Conflito("editadas depois de geradas (use --forcar): " + ", ".join(conflitos))
    cenas = _ler_json(c["scenes"], {})
    slots = ((cenas.get("alva_e_luz") or {}).get("taverna") or {}).get("slots") or []
    barman = next((s for s in slots if isinstance(s, dict) and s.get("id") == "barman"), None)
    if barman is None:
        raise ValueError("city_scenes.json: Bartender (alva_e_luz/taverna/barman) não encontrado.")

    os.makedirs(c["dungeons_dir"], exist_ok=True)
    for arquivo, defn in artefatos["masmorras"].items():
        _gravar_json(os.path.join(c["dungeons_dir"], arquivo), defn)
        assin[arquivo] = assinatura(defn)
    _gravar_json(c["assinaturas"], assin)

    aventuras = _ler_json(c["adventures"], {})
    for did, dest in artefatos["destinos"].items():
        aventuras[did] = dest
    _gravar_json(c["adventures"], aventuras)

    convs = [cv for cv in (barman.get("conversations") or []) if cv.get("id") != CONVERSA_ID]
    barman["conversations"] = convs + [artefatos["conversa"]]
    _gravar_json(c["scenes"], cenas)

    itens = [r for r in _ler_json(c["items"], []) if isinstance(r, dict) and r.get("id") != ANEL_ID]
    itens.append(artefatos["anel"])
    _gravar_json(c["items"], itens)
    antigo = S.CUSTOM_ITEMS_INDEX
    S.CUSTOM_ITEMS_INDEX = c["items_index"]
    try:
        S._regen_custom_items_index(itens)
    finally:
        S.CUSTOM_ITEMS_INDEX = antigo
    if regen_editor:
        S._regen_dungeons_index()


def relatorio(artefatos):
    linhas = []
    for arquivo, defn in artefatos["masmorras"].items():
        poder = defn["expected_party"]["heroes"] * defn["expected_party"]["level"]
        linhas.append(f"{arquivo}  (poder {poder})")
        for rid, nd in nd_por_sala(defn).items():
            linhas.append(f"   sala {rid}: ND {nd:g} -> {faixa(nd, poder)} ({nd / poder:.2f})")
    linhas.append("Artes pedidas pelos slides:")
    linhas += [f"   {k}: {arte}" for k, arte in ARTES_PEDIDAS]
    return "\n".join(linhas)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Gera a campanha Sombras sob Alva e Luz.")
    ap.add_argument("--simular", action="store_true", help="só relata, não grava")
    ap.add_argument("--forcar", action="store_true", help="regrava masmorra editada à mão")
    args = ap.parse_args(argv)
    try:
        artefatos = preparar()
    except ValueError as e:
        print(f"ERRO: {e}  (nada foi gravado)")
        return 1
    print(relatorio(artefatos))
    if args.simular:
        return 0
    try:
        aplicar(artefatos, forcar=args.forcar)
    except (Conflito, ValueError) as e:
        print(f"RECUSADO: {e}  (nada foi gravado)")
        return 2
    print("OK: 4 masmorras, 3 destinos, conversa do Bartender e anel gravados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Pontos de desenho:
- Conflitos são conferidos **antes** do primeiro arquivo gravado (tudo ou nada); o Bartender ausente também aborta antes.
- Os arquivos compartilhados são lidos crus e regravados com `indent=2, ensure_ascii=False` — o mesmo formato com que o servidor os grava —, então as entradas alheias saem byte-idênticas.
- O índice `editor_items_custom.js` é regravado pela própria função do servidor, com `CUSTOM_ITEMS_INDEX` apontado para o caminho pedido e restaurado no `finally`.

- [ ] **Step 4: Rodar e ver passar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_campanha_sombras.py 2>&1 | tail -3`
Expected: `67 passaram, 0 falharam`.

Run: `git status --short > "$TMP/antes.txt"; PYTHONIOENCODING=utf-8 python tools/gerar_campanha_sombras.py --simular; echo "exit=$?"; git status --short | diff "$TMP/antes.txt" - && echo "nada alterado"`
Expected: o ND por sala (Vau 1 / 1,25 / 2 · Minas 1,25 / 0,95 / 2 / 3,5 · Salões 0 / 2,5 / 2,5 / 3,5 · Trono 0 / 5,5 / 2,5), as 14 artes pedidas, `exit=0` e `nada alterado`.

- [ ] **Step 5: Commit**

```bash
git add tools/gerar_campanha_sombras.py tools/test_campanha_sombras.py
git commit -m "feat(campanha): gravacao nao destrutiva, --simular e --forcar

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Gerar a campanha de verdade e publicar o conteúdo

**Files (gerados):** `dungeons/sombras_1_vau.json`, `dungeons/sombras_2_minas.json`, `dungeons/sombras_3a_saloes.json`, `dungeons/sombras_3b_trono.json`, `tools/.sombras_assinaturas.json`, `world_adventures.json`, `city_scenes.json`, `itens_personalizados.json`, `tools/editor_items_custom.js`, `tools/editor_dungeons.js`

- [ ] **Step 1: Registrar o estado dos arquivos compartilhados**

Run: `git status --short world_adventures.json city_scenes.json itens_personalizados.json tools/editor_items_custom.js tools/editor_dungeons.js`
Anote quais já aparecem modificados: esses têm trabalho do autor e **não** podem ser commitados inteiros.

- [ ] **Step 2: Gerar**

Run: `PYTHONIOENCODING=utf-8 python tools/gerar_campanha_sombras.py`
Expected: o relatório e `OK: 4 masmorras, 3 destinos, conversa do Bartender e anel gravados.` Se sair `RECUSADO` ou `OSError`, pare e relate (servidor rodando trava a escrita).

- [ ] **Step 3: Conferir que nada alheio foi removido**

Run: `git diff world_adventures.json city_scenes.json itens_personalizados.json | grep '^-' | grep -v '^---'`
Expected: nenhuma linha, ou só linhas de estrutura (`]`, `}`) deslocadas pela entrada nova. Qualquer linha removida com conteúdo alheio: pare e relate.

- [ ] **Step 4: Rodar a bateria relacionada**

Run:
```bash
for t in test_campanha_sombras test_masmorra_sequenciada test_cenas_conversa test_cidades_editor test_editor_itens test_modo_mestre test_tutorial; do out=$(PYTHONIOENCODING=utf-8 timeout 400 python tools/$t.py 2>&1); c=$?; echo "$t exit=$c falhas=$(echo "$out" | grep -c '❌')"; done
```
Expected: `exit=0 falhas=0` em todas.

- [ ] **Step 5: Commit só do conteúdo da campanha**

```bash
git add dungeons/sombras_1_vau.json dungeons/sombras_2_minas.json dungeons/sombras_3a_saloes.json dungeons/sombras_3b_trono.json tools/.sombras_assinaturas.json
```

Para cada um de `world_adventures.json`, `city_scenes.json`, `itens_personalizados.json` e `tools/editor_items_custom.js`: se estava **limpo** no Step 1, `git add` nele. Se estava modificado, **não** o adicione; relate ao autor.

`tools/editor_dungeons.js` é um índice regenerado a partir de TODA a pasta `dungeons/`. Se estava modificado no Step 1, **não** o commite (levaria o trabalho do autor junto): deixe-o no working tree e avise o autor. Se estava limpo, adicione-o.

```bash
git diff --cached --stat
git commit -m "feat(campanha): Sombras sob Alva e Luz — 4 masmorras, 3 destinos, anel e gancho

Gerado por tools/gerar_campanha_sombras.py (reexecutavel; recusa sobrescrever
masmorra editada a mao sem --forcar). Destinos ocultos ate liberar, em
corrente: conversa do Bartender -> Vau -> Minas -> Covil (2 andares emendados).

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Conferência dentro do jogo e documentação

**Files:**
- Modify: `CLAUDE.md` (uma nota nova)

- [ ] **Step 1: Avisos do validador de design no editor**

Com um servidor rodando, abra `http://localhost:8765/tools/editor.html` (o editor em `file://` quebra os modelos 3D), carregue cada `sombras_*.json` e leia a seção "⚠️ Avisos de design".
Expected: nenhum aviso de conectividade (R4), de descanso antes do chefe (R5) ou de pico entre salas obrigatórias (R3). Avisos aceitos: R2 no Trono e R1 (rota alternativa) nas quatro. Registre o que apareceu.

- [ ] **Step 2: Jogar o Trono no simulador do editor**

No editor, com `sombras_3b_trono.json` aberto, "🧪 Testar como Mestre": adicione um herói-teste, inicie o combate e confira no navegador, em 2D e 3D:
- o Troll regenera 4 PV no início do turno dele;
- um Frasco de Ácido que acerta interrompe a regeneração;
- ativar a estante abre a passagem e revela o Esconderijo;
- o Bugbear conjura o Manto (nuvem de sombras).

Se o painel do navegador estiver oculto, o `requestAnimationFrame` não roda: troque-o por `setTimeout` e capture com `renderer.render()` + `toDataURL()`. Recarregue com cache-buster (`?v=algo`) antes de concluir qualquer coisa sobre o cliente.

- [ ] **Step 3: Nota no `CLAUDE.md`**

Acrescente um parágrafo depois do bloco que começa com `> **Fim da rota:**`:

```markdown
> **Campanha "Sombras sob Alva e Luz" (2026-09-25):** primeira campanha de conteúdo, gerada por
> `tools/gerar_campanha_sombras.py` (reexecutável; só toca nas entradas `sombras_*`/
> `anel_garra_negra` e recusa sobrescrever masmorra editada à mão sem `--forcar`, por hash em
> `tools/.sombras_assinaturas.json`; `--simular` relata ND por sala e as artes pedidas pelos
> slides). Gancho: conversa `sombras_caravanas` do Bartender de Alva e Luz → fato → destinos
> ocultos em corrente Vau (escolta de Tomé até a saída, nível 1) → Minas (baú-chave com
> ácido/óleo e o bilhete, nível 2) → Covil (Salões com salas obrigatórias, emendados no Trono do
> Troll, nível 3). Chefe secreto: Bugbear das Sombras atrás da estante-mecanismo, guardando o
> **Anel da Garra Negra** (item custom: +1 acerto, +1 visão, concede Esconder nas Sombras).
> Achado no caminho: `load_authored_dungeon` descartava `required`/`required_mode` e o objetivo
> `salas_obrigatorias` se cumpria ao entrar — corrigido (`test_modo_mestre` [23b]). A curva de XP
> ainda dispara (a suíte relata o nível atingido; o conserto é o próximo subprojeto). Teste:
> `tools/test_campanha_sombras.py`.
```

- [ ] **Step 4: Commit**

O `CLAUDE.md` pode ter edição do autor. Se `git diff CLAUDE.md` mostrar só o seu parágrafo, `git add CLAUDE.md`; senão, monte o conteúdo a partir do `HEAD` com a sua inserção (mesma receita da Task 1, Step 6) e use `git update-index`.

```bash
git commit -m "docs: campanha Sombras sob Alva e Luz

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
