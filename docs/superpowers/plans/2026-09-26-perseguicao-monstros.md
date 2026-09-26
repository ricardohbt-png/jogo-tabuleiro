# Perseguição dos monstros — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Todo dano que um herói causa num monstro, por qualquer ação, grava de onde veio o ataque; e o monstro que chega à última posição conhecida sem ver o herói faz um teste de Percepção para seguir o rastro.

**Architecture:** Dois acréscimos à memória de perseguição que já existe (`ai_last_seen`, `_monster_register_attack_alert`, `_monster_search_last_seen`). O rastro é um passo novo dentro de `_monster_search_last_seen`. O "todo dano alerta" é uma foto do HP dos monstros antes e depois de cada mensagem de herói no laço `handler`, no mesmo padrão do `_ability_watch` que já existe ali.

**Tech Stack:** Python 3 (`server.py`, suíte `tools/test_*.py` com `check()` próprio), dicionário `src/lang/narracao.js`.

**Spec:** `docs/superpowers/specs/2026-09-26-perseguicao-monstros-design.md`

---

## Antes de começar — regras deste repositório

- Trabalhe no worktree `C:\Users\RICARDO\Desktop\jogo tabuleiro\.claude\worktrees\perseguicao` (branch `feat/perseguicao-monstros`). Nunca no checkout principal.
- `server.py` e `CLAUDE.md` estão em **CRLF**, e muitos comentários têm acentos corrompidos (`nÃ­vel`). Edite com a ferramenta Edit copiando o texto exatamente como o Read mostra. Não use PowerShell nem `replace("...\n...")` por script.
- Rode as suítes da raiz do worktree com `PYTHONIOENCODING=utf-8` e confira o **texto** (`N passaram, 0 falharam`, nenhum `❌`), não só o exit code.
- Não suba servidor na porta 8765: ela é do autor.

## Estrutura de arquivos

| Arquivo | Mudança |
|---|---|
| `server.py` | `_heroi_rastreavel`, `_monster_tentar_rastro` e `_monster_search_last_seen` reescrita (Task 1); `_hp_monstros`, `_alertar_monstros_feridos`, `_MENSAGENS_SEM_ALERTA_DE_DANO` e o gancho no `handler` (Task 2) |
| `src/lang/narracao.js` | chave `narracao.encontra_o_rastro` |
| `tools/test_perseguicao.py` | **novo** |
| `CLAUDE.md` | nota nova |

---

### Task 1: Rastro por Percepção

**Files:**
- Modify: `server.py` — `_monster_search_last_seen` (~15023; logo antes de `def _heroi_enxerga_monstro`)
- Modify: `src/lang/narracao.js`
- Create: `tools/test_perseguicao.py`

- [ ] **Step 1: Criar a suíte (falha)**

Create `tools/test_perseguicao.py`:

```python
"""Perseguição dos monstros: todo dano alerta e rastro por Percepção.
Roda da raiz: python tools/test_perseguicao.py
Spec: docs/superpowers/specs/2026-09-26-perseguicao-monstros-design.md
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


HEROI_LONGE = [15, 3]      # do outro lado da parede em x=10
ORC_POS = [7, 5]


def cena(fechada=False):
    """Sala 18×10 cortada por uma parede em x=10; passagem em y=10 (sem ela se
    `fechada`). Um orc no lado esquerdo e o Luccas escondido no direito."""
    r = S.GameRoom("PERSEG")
    narr = []
    async def noop(*a, **k):
        pass
    async def say(txt, *a, **k):
        narr.append(str(txt))
    r.gm_say = say; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 11):
        for x in range(1, 19):
            r.tiles[y][x] = S.FLOOR
    for y in range(1, 11):
        if fechada or y != 10:
            r.tiles[y][10] = S.WALL
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 18, "h": 10, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    h = S.make_player("h", "Luccas", "rogue", 0)
    h["pos"] = list(HEROI_LONGE)
    r.players = {"h": h}
    orc = next(d for d in S.MONSTER_DEFS if d["type"] == "orc")
    m = S.make_monster(orc, {"id": 0, "cx": ORC_POS[0], "cy": ORC_POS[1]})
    m["pos"] = list(ORC_POS)
    r.monsters = {m["id"]: m}
    return r, h, m, narr


def lembrar(r, m, pos=None):
    """O orc 'viu' o Luccas pela última vez em `pos` (padrão: onde o orc está)."""
    m["ai_last_seen"] = {"target_id": "h", "pos": list(pos or m["pos"]),
                         "round": r.round_num, "room_id": m.get("room_id")}


class Dado:
    """Fixa o d20 (random.randint(1, 20)) durante o bloco."""
    def __init__(self, valor):
        self.valor = valor
    def __enter__(self):
        self.orig = S.random.randint
        S.random.randint = lambda a, b: self.valor if (a, b) == (1, 20) else self.orig(a, b)
    def __exit__(self, *exc):
        S.random.randint = self.orig


def espiar_percepcao(r):
    """Conta os testes de rastro (cada teste lê a Percepção uma vez)."""
    chamadas = []
    orig = r._get_percepcao_monstro
    def spy(mm):
        chamadas.append(1)
        return orig(mm)
    r._get_percepcao_monstro = spy
    return chamadas


async def turno(r, m):
    await r.gm_phase(only_monster=m)
    r.round_num += 1


# ─── [1] rastro com sucesso ──────────────────────────────────────────────────
async def secao_sucesso():
    print("\n[1] Chegou à última posição sem ver o herói e passou no teste")
    r, h, m, narr = cena()
    lembrar(r, m)
    rodada = r.round_num
    check("orc não enxerga o Luccas", not r._monstro_enxerga_alvo(m, {"obj": h}))
    with Dado(1):
        await turno(r, m)
    mem = m.get("ai_last_seen") or {}
    check("a pista passou à posição atual do herói", mem.get("pos") == HEROI_LONGE)
    check("o prazo não foi renovado (round igual)", mem.get("round") == rodada)
    check("conta como a 1ª busca", mem.get("searches") == 1)
    check("o orc saiu do lugar atrás da pista", m["pos"] != ORC_POS)
    check("narrou o rastro", any("rastro" in t for t in narr))


# ─── [2] rastro com falha e um teste por chegada ─────────────────────────────
async def secao_falha():
    print("\n[2] Falhou no teste: fica procurando e não testa de novo no mesmo ponto")
    r, h, m, narr = cena()
    lembrar(r, m)
    testes = espiar_percepcao(r)
    with Dado(20):
        await turno(r, m)
    mem = m.get("ai_last_seen") or {}
    check("memória continua no ponto antigo", mem.get("pos") == ORC_POS)
    check("o orc ficou parado", m["pos"] == ORC_POS)
    check("marcou onde testou", mem.get("rastro_testado_em") == ORC_POS)
    check("sem narração na falha", not any("rastro" in t for t in narr))
    with Dado(1):
        await turno(r, m)
    check("parado no mesmo ponto: só 1 teste em 2 turnos", len(testes) == 1)
    check("e a pista não mudou", (m.get("ai_last_seen") or {}).get("pos") == ORC_POS)


# ─── [3] quem não deixa rastro ───────────────────────────────────────────────
async def secao_invisivel():
    print("\n[3] Herói invisível não deixa rastro, exceto para quem tem Faro Implacável")
    r, h, m, narr = cena()
    h["invisivel_sombras"] = True
    lembrar(r, m)
    testes = espiar_percepcao(r)
    with Dado(1):
        await turno(r, m)
    check("invisível: nenhum teste", len(testes) == 0)
    check("invisível: pista intacta", (m.get("ai_last_seen") or {}).get("pos") == ORC_POS)

    r, h, m, narr = cena()
    h["invisivel_sombras"] = True
    m["special_abilities"] = [{"id": "faro_implacavel_minotauro"}]
    lembrar(r, m)
    with Dado(1):
        await turno(r, m)
    check("com Faro Implacável o rastro existe",
          (m.get("ai_last_seen") or {}).get("pos") == HEROI_LONGE)

    r, h, m, narr = cena()
    h["fora_masmorra"] = {"rodadas_restantes": 2}
    lembrar(r, m)
    testes = espiar_percepcao(r)
    with Dado(1):
        await turno(r, m)
    check("herói na cidade não deixa rastro", len(testes) == 0)


# ─── [4] prazo de 3 rodadas e reencontro ─────────────────────────────────────
async def secao_prazo():
    print("\n[4] Prazo de 3 rodadas sem ver o herói, mesmo rastreando; ver de novo zera")
    r, h, m, narr = cena(fechada=True)
    lembrar(r, m)
    with Dado(1):
        await turno(r, m)
        check("rodada 1: achou o rastro", (m.get("ai_last_seen") or {}).get("pos") == HEROI_LONGE)
        await turno(r, m)
        check("rodada 2: ainda procurando", m.get("ai_last_seen") is not None)
        await turno(r, m)
    check("rodada 3 sem ver o herói: desistiu", m.get("ai_last_seen") is None)

    r, h, m, narr = cena()
    lembrar(r, m)
    m["ai_last_seen"]["searches"] = 2
    h["pos"] = [8, 5]                     # colado no orc: ele vê
    await turno(r, m)
    mem = m.get("ai_last_seen") or {}
    check("viu de novo: memória nova, busca zerada",
          mem.get("pos") == [8, 5] and not mem.get("searches"))


async def main():
    await secao_sucesso()
    await secao_falha()
    await secao_invisivel()
    await secao_prazo()
    print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
    sys.exit(1 if FAIL else 0)


asyncio.run(main())
```

A cena é uma sala 18×10 cortada por uma parede em x=10, com passagem em y=10 (sem passagem com `fechada=True`). O orc (legado, `MONSTER_DEFS` tipo `orc`) fica em [7,5] e o Luccas em [15,3], fora da visão dele. `Dado` fixa só `random.randint(1, 20)`.

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_perseguicao.py`
Expected: 7 `❌`, entre eles "a pista passou à posição atual do herói", "marcou onde testou" e "com Faro Implacável o rastro existe".

- [ ] **Step 3: Implementar o rastro**

Em `server.py`, substitua o método inteiro `async def _monster_search_last_seen(self, m):`, da linha `async def _monster_search_last_seen(self, m):` até o `return moveu` final inclusive, por:

```python
    def _heroi_rastreavel(self, m, alvo_id):
        """Herói que ainda deixa rastro para o monstro `m`: vivo, no tabuleiro,
        com posição e visível. Invisibilidade (Sombras, magia, Vela) apaga o
        rastro, exceto para quem tem Faro Implacável."""
        p = self.players.get(alvo_id)
        if not self._ativo(p) or not p.get("pos"):
            return None
        if ((p.get("invisivel_sombras") or p.get("invisivel_magico") or p.get("oculto_vela"))
                and not self._tem_habilidade(m, "faro_implacavel_minotauro")):
            return None
        return p

    async def _monster_tentar_rastro(self, m, memoria):
        """Teste de Percepção ao chegar à última posição conhecida sem ver o herói.

        Sucesso se d20 + (distância até o herói ÷ 2) <= Percepção da ficha. No
        sucesso a pista passa à posição ATUAL do herói (o prazo de 3 rodadas não
        é renovado). Um teste por chegada: parado no mesmo ponto, não testa de
        novo. Spec: 2026-09-26-perseguicao-monstros-design.md."""
        pos = list(m.get("pos", []))
        if memoria.get("rastro_testado_em") == pos:
            return None
        p = self._heroi_rastreavel(m, memoria.get("target_id"))
        if not p:
            return None
        memoria["rastro_testado_em"] = pos
        dist = max(abs(pos[0] - p["pos"][0]), abs(pos[1] - p["pos"][1]))
        if random.randint(1, 20) + dist // 2 > self._get_percepcao_monstro(m):
            return None
        memoria["pos"] = list(p["pos"])
        await self.gm_say(T("narracao.encontra_o_rastro",
                            monstro=nome_criatura(m), heroi=p["name"]))
        return list(p["pos"])

    async def _monster_search_last_seen(self, m):
        """Procura a última posição conhecida; ao chegar sem ver o herói, tenta
        seguir o rastro (`_monster_tentar_rastro`)."""
        goal = self._monster_last_seen_goal(m)
        if not goal:
            return False

        # Uma chamada corresponde ao turno de busca deste monstro. Contar o
        # turno desde o início garante exatamente três tentativas, mesmo que a
        # criatura ainda esteja a caminho do ponto conhecido — e mesmo que ela
        # ache o rastro: o rastro não renova o prazo.
        memoria = m.get("ai_last_seen") or {}
        memoria["searches"] = int(memoria.get("searches", 0) or 0) + 1
        buscas = memoria["searches"]

        # Passo a passo pelo BFS/ocupação já usado pelo restante da IA. Ao
        # chegar à pista, testa o rastro UMA vez por turno; no sucesso a pista
        # passa à posição atual do herói e o monstro segue com o movimento que
        # sobrou.
        moveu = False
        rastreou = False
        while True:
            if list(m.get("pos", [])) == goal:
                if rastreou:
                    break
                novo = await self._monster_tentar_rastro(m, memoria)
                if not novo:
                    break
                goal, rastreou = novo, True
            if m.get("_water_moves_left", 0) <= 0:
                break
            antes = list(m.get("pos", []))
            await self._monster_move_to_goal(m, goal)
            if list(m.get("pos", [])) == antes:
                break
            moveu = True
        if buscas >= 3:
            m.pop("ai_last_seen", None)
            m.pop("ai_alert_until", None)
        return moveu
```

`random`, `T` e `nome_criatura` já existem no módulo.

Em `src/lang/narracao.js`, logo após a entrada `"narracao.a_barreira_arcana_de_termina": {…},` (a primeira do arquivo), acrescente:

```js
  "narracao.encontra_o_rastro": {
    "en": "🐾 {monstro} picks up {heroi}'s trail!",
    "pt": "🐾 {monstro} encontra o rastro de {heroi}!"
  },
```

- [ ] **Step 4: Rodar e ver passar**

Run:
```bash
PYTHONIOENCODING=utf-8 python tools/test_perseguicao.py
PYTHONIOENCODING=utf-8 python tools/test_idioma.py | tail -2
PYTHONIOENCODING=utf-8 python tools/dividas.py
```
Expected: `20 passaram, 0 falharam`; idioma `0 falharam`; dívidas "nada pendente".

- [ ] **Step 5: Commit**

```bash
git add server.py src/lang/narracao.js tools/test_perseguicao.py
git commit -m "feat(ia): monstro que chega a ultima posicao sem ver o heroi testa Percepcao para seguir o rastro

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Todo dano alerta

**Files:**
- Modify: `server.py` — logo depois de `_monster_register_attack_alert` (~14964); módulo, antes de `async def handler(ws):` (~42356); dentro do `handler` (foto após o bloco `_ability_watch` ~42391; alerta junto do "depois" do `_ability_watch` ~43267)
- Modify: `tools/test_perseguicao.py`

- [ ] **Step 1: Seções [5] e [6] na suíte (falha)**

Em `tools/test_perseguicao.py`, antes de `async def main():`, insira:

```python
# ─── [5] todo dano alerta ────────────────────────────────────────────────────
async def secao_alerta():
    print("\n[5] Dano de qualquer ação do herói dá ao monstro a origem do ataque")
    r, h, m, narr = cena()
    h["pos"] = [15, 9]
    antes = r._hp_monstros()
    await r._dano_em_alvo(m, 3, "fogo", "h")          # ex.: uma magia
    await r._alertar_monstros_feridos("h", antes)
    mem = m.get("ai_last_seen") or {}
    check("magia: grava a posição do herói", mem.get("pos") == [15, 9])
    check("magia: marcada como ataque", mem.get("reason") == "attack")

    r, h, m, narr = cena()
    antes = r._hp_monstros()
    await r._alertar_monstros_feridos("h", antes)
    check("sem dano: nada gravado", "ai_last_seen" not in m)

    r, h, m, narr = cena()
    antes = r._hp_monstros()
    m["hp"] = 0
    await r._alertar_monstros_feridos("h", antes)
    check("monstro morto na ação: nada gravado", "ai_last_seen" not in m)

    r, h, m, narr = cena()
    h["fora_masmorra"] = {"rodadas_restantes": 2}
    antes = r._hp_monstros()
    m["hp"] -= 2
    await r._alertar_monstros_feridos("h", antes)
    check("herói fora do tabuleiro: nada gravado", "ai_last_seen" not in m)

    r, h, m, narr = cena()
    antes = r._hp_monstros()
    m["hp"] -= 2
    await r._alertar_monstros_feridos("mestre", antes)
    check("pid que não é herói: nada gravado", "ai_last_seen" not in m)

# ─── [6] gancho no laço de mensagens ─────────────────────────────────────────
def secao_gancho():
    print("\n[6] O laço de mensagens chama o alerta, exceto no fim de turno e no controle de servos")
    src = open(S.__file__, encoding="utf-8").read()
    check("exclusões declaradas",
          S._MENSAGENS_SEM_ALERTA_DE_DANO == frozenset(
              {"end_turn", "comandar_animados", "mover_animado", "atacar_animado"}))
    check("foto do HP antes do despacho", "_hp_watch = room._hp_monstros()" in src)
    check("alerta depois do despacho", "await room._alertar_monstros_feridos(pid, _hp_watch)" in src)
```

E no `main`, depois de `await secao_prazo()`, acrescente:

```python
    await secao_alerta()
    secao_gancho()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `PYTHONIOENCODING=utf-8 python tools/test_perseguicao.py`
Expected: `AttributeError: 'GameRoom' object has no attribute '_hp_monstros'`

- [ ] **Step 3: Métodos do alerta**

Em `server.py`, logo depois do fim de `_monster_register_attack_alert` (a linha `aliado["alertado"] = True` dentro do `if self._mestre_ativo():`), insira:

```python

    def _hp_monstros(self):
        """{id: hp} dos monstros vivos — a foto de antes de uma ação do herói,
        comparada por `_alertar_monstros_feridos` depois dela."""
        return {mid: m.get("hp", 0) for mid, m in self.monsters.items()
                if m.get("hp", 0) > 0}

    async def _alertar_monstros_feridos(self, pid, hp_antes):
        """Todo monstro que perdeu HP durante a ação do herói `pid` ganha a
        posição dele como origem do ataque — cobre magia, arremesso,
        instrumento, técnica e qualquer fonte futura, sem gancho por executor.
        Spec: 2026-09-26-perseguicao-monstros-design.md."""
        heroi = self.players.get(pid)
        if not self._ativo(heroi) or not hp_antes:
            return
        for mid, hp in hp_antes.items():
            m = self.monsters.get(mid)
            if m and m.get("hp", 0) < hp:
                self._monster_register_attack_alert(heroi, m)
```

- [ ] **Step 4: Gancho no laço de mensagens**

Logo antes de `async def handler(ws):`, insira:

```python
# Mensagens em que a queda de HP dos monstros NÃO é um ataque do herói que a
# enviou: o turno dos monstros roda DENTRO do end_turn (zonas, retaliação,
# veneno), e o controle de servos já grava a posição do SERVO no alerta.
_MENSAGENS_SEM_ALERTA_DE_DANO = frozenset(
    {"end_turn", "comandar_animados", "mover_animado", "atacar_animado"})


```

Dentro do `handler`, logo depois do bloco que monta o `_ability_watch` (termina com o `}` do dicionário e antes da linha `try:` que começa com o comentário "Idioma desta conexão"), insira no mesmo nível do `_ability_watch = None`:

```python
            # Todo dano que o herói causar nesta ação dá aos monstros feridos a
            # origem do ataque (ver _alertar_monstros_feridos).
            _hp_watch = None
            if (room and room.phase == "playing" and pid in room.players
                    and t not in _MENSAGENS_SEM_ALERTA_DE_DANO):
                _hp_watch = room._hp_monstros()
```

E logo antes da linha `if _ability_watch and room:` (o bloco "depois", dentro do `try`), no mesmo nível dela, insira:

```python
                if _hp_watch is not None and room:
                    await room._alertar_monstros_feridos(pid, _hp_watch)
```

- [ ] **Step 5: Rodar**

Run:
```bash
PYTHONIOENCODING=utf-8 python tools/test_perseguicao.py
PYTHONIOENCODING=utf-8 python tools/test_handler_smoke.py | tail -2
```
Expected: `29 passaram, 0 falharam`; smoke `0 falharam` (é a suíte que passa pelo laço de mensagens de verdade).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_perseguicao.py
git commit -m "feat(ia): todo dano de uma acao do heroi da ao monstro a origem do ataque

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Bateria e documentação

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Bateria**

Run (script do scratchpad que relata exit code e contagem de ❌):
```bash
python "C:/Users/RICARDO/AppData/Local/Temp/claude/C--Users-RICARDO-Desktop-jogo-tabuleiro/481c0e8d-419c-46f6-ab59-86095bdc3420/scratchpad/suites.py" test_perseguicao test_modo_mestre test_simulador_turno test_agarrao test_devorador test_handler_smoke test_projeteis test_tirano test_idioma test_campanha_sombras test_masmorra_sequenciada test_objetivos test_instrumentos_bardo test_tecnicas_espec test_ataque_giratorio
```
Expected: `0 com problema`. Vermelha: confira a memória `testes-pre-existentes-quebrados.md` antes de tratar como regressão; se for regressão, pare e relate.

- [ ] **Step 2: Nota no `CLAUDE.md`**

Acrescente um parágrafo ao fim do arquivo:

```markdown
> **Perseguição dos monstros (2026-09-26):** a memória que já existia (`ai_last_seen`,
> `_monster_remember_visible_targets`, `_monster_register_attack_alert`,
> `_monster_search_last_seen`: ver o herói ou ser atacado → busca a última posição por 3
> rodadas, alerta compartilhado com a sala de origem) ganhou dois acréscimos. **Todo dano
> alerta:** o `handler` tira uma foto do HP dos monstros (`_hp_monstros`) antes de cada mensagem
> de herói na masmorra e chama `_alertar_monstros_feridos` depois — magia, arremesso,
> instrumento e técnica passam a gravar a origem do ataque sem gancho por executor. Ficam de
> fora (`_MENSAGENS_SEM_ALERTA_DE_DANO`) o `end_turn`, porque o turno dos monstros roda dentro
> dele, e o controle de servos, que já grava a posição do servo. **Rastro:** ao chegar à última
> posição sem ver o herói, `_monster_tentar_rastro` testa `d20 + distância÷2 ≤ Percepção` da
> ficha; no sucesso a pista vira a posição atual do herói (sem renovar o prazo), uma vez por
> chegada, por monstro. Invisível não deixa rastro, salvo Faro Implacável. Teste:
> `tools/test_perseguicao.py`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-09-26-perseguicao-monstros*`.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: perseguicao dos monstros

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
