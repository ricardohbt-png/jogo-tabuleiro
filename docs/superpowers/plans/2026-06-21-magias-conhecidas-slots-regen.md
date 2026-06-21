# Magias conhecidas + slots com regeneração (Pedro & Lewis) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Substituir o sistema atual de slots de magia (contador por círculo resetado a cada turno, em modo teste) por magias conhecidas escolhidas pelo jogador + slots discretos que regeneram por rodadas, com timer independente por slot visível na ficha.

**Architecture:** O servidor (`server.py`) é autoritativo. Cada mago/clérigo guarda `magias_conhecidas` (ids do GRIMÓRIO) e `slots_cooldown` (por círculo, lista de rodadas em que cada slot gasto volta). A quantidade máxima de slots vem da tabela por nível. A disponibilidade é `max - len(cooldown)` após podar timers vencidos contra `self.round_num`. O cliente (`game.js` + `src/gameState.js`) só renderiza estado e envia escolhas via novas mensagens.

**Tech Stack:** Python 3.x (`websockets`), Vanilla JS, Three.js r128. Testes de servidor no estilo `tools/test_devorador.py` (stub da camada de rede + `make_player`).

**Spec:** `docs/superpowers/specs/2026-06-21-magias-conhecidas-slots-regen-design.md`

---

## File Structure

- **Modify `server.py`** — constantes de slots/regen, init do jogador, helpers de slot, `handle_magia`, `_check_level_up`, `handle_end_turn`, `_voltar_para_cidade`, `start_game`, novos handlers `handle_set_known_spells`/`handle_escolher_magia_nivel`/`_enviar_spell_pick_prompt`, roteamento de mensagens. Remover `CLERIC_SLOTS`/`MAGE_TESTE_LIVRE`/`slots_por_circulo`/`magias_usadas_hoje`.
- **Create `tools/test_magias_slots.py`** — testes da lógica de slots, regeneração, escolha de magias e level-up.
- **Modify `game.js`** — `renderMagiasFichaEmJogo` (cooldown countdown, sem modo teste), wiring da seleção na criação, overlay de level-up, remover `MAGE_TESTE_LIVRE`.
- **Modify `src/gameState.js`** — senders `setKnownSpells`/`escolherMagiaNivel`, handler do `spell_pick_prompt`.

**Convenção do timer:** slot gasto na rodada `R` registra `ready_at = R + REGEN[c]`. Fica disponível quando `round_num >= ready_at`. Poda mantém entradas com `ready_at > round_num`. Contagem regressiva exibida = `max(0, ready_at - round_num)`.

---

## Task 1: Modelo de slots no servidor (constantes, init, helpers)

**Files:**
- Modify: `server.py` (perto de `MAGE_SLOTS_POR_NIVEL` ~2196-2215; init do jogador ~2692-2694; adicionar métodos na classe `GameRoom`)
- Test: `tools/test_magias_slots.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_magias_slots.py`:

```python
"""Testes do sistema de magias conhecidas + slots com regeneração (Pedro/Lewis).
Roda da raiz: python tools/test_magias_slots.py
Stuba a camada de rede do GameRoom para testar a lógica isoladamente."""
import asyncio, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, SLOTS_POR_NIVEL, SLOT_REGEN, slots_max_para

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.round_num = 1
    r.phase = "playing"                     # _is_turn exige phase=="playing"
    r.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]   # piso vazio
    r._tem_linha_de_visao = lambda *a, **k: True    # sem paredes nos testes
    return r

def mk_mage(r, level=1):
    p = make_player("p1", "Pedro", "mage", 0)
    p["level"] = level
    r.players["p1"] = p
    return p

async def main():
    print("\n[1] Tabela de slots por nível + helpers")
    r = setup(); p = mk_mage(r, 1)
    check("nível 1 → 2 slots de 1º", slots_max_para(p)["primeiro"] == 2)
    check("nível 1 → 0 de 2º", slots_max_para(p)["segundo"] == 0)
    check("init cooldown vazio", p["slots_cooldown"] == {"primeiro": [], "segundo": [], "terceiro": []})
    check("disponíveis 1º = 2", r._slots_disponiveis(p, "primeiro") == 2)

    print("\n[2] Gastar slot adiciona cooldown correto")
    r.round_num = 5
    r._gastar_slot(p, "primeiro")
    check("1 cooldown registrado", len(p["slots_cooldown"]["primeiro"]) == 1)
    check("ready_at = round + 10", p["slots_cooldown"]["primeiro"][0] == 15)
    check("disponíveis caiu p/ 1", r._slots_disponiveis(p, "primeiro") == 1)

    print("\n[3] Regeneração após REGEN rodadas")
    r.round_num = 14
    check("ainda indisponível na rodada 14", r._slots_disponiveis(p, "primeiro") == 1)
    r.round_num = 15
    check("volta na rodada 15", r._slots_disponiveis(p, "primeiro") == 2)
    check("cooldown podado", p["slots_cooldown"]["primeiro"] == [])

    print("\n[4] Recarga total (descanso)")
    r.round_num = 1
    r._gastar_slot(p, "primeiro"); r._gastar_slot(p, "primeiro")
    check("2 gastos", r._slots_disponiveis(p, "primeiro") == 0)
    r._recarregar_slots(p)
    check("recarga zera cooldown", r._slots_disponiveis(p, "primeiro") == 2)

    print(f"\n{'='*40}\nPASS: {PASS}  FAIL: {FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```

- [ ] **Step 2: Rodar o teste e confirmar a falha**

Run: `python tools/test_magias_slots.py`
Expected: FAIL com `ImportError` (não existe `SLOTS_POR_NIVEL`/`slots_max_para`) ou `AttributeError` nos métodos `_slots_disponiveis`/`_gastar_slot`/`_recarregar_slots`.

- [ ] **Step 3: Adicionar constantes e função módulo-level**

Em `server.py`, substituir o bloco `CLERIC_SLOTS`/`MAGE_SLOTS_POR_NIVEL`/`slots_por_circulo` (linhas ~2192-2215) por:

```python
# Magos (Pedro) e clérigos (Lewis) NÃO usam MP. Cada magia custa 1 SLOT do seu
# círculo + 🍖-1/💧-1. Slots regeneram por rodadas (timer independente por slot).
# Tabela única para as duas classes. Nível 6+ = cap no nível 5 (TODO: estender).
SLOTS_POR_NIVEL = {
    1: {"primeiro": 2, "segundo": 0, "terceiro": 0},
    2: {"primeiro": 3, "segundo": 0, "terceiro": 0},
    3: {"primeiro": 3, "segundo": 1, "terceiro": 0},
    4: {"primeiro": 3, "segundo": 2, "terceiro": 0},
    5: {"primeiro": 3, "segundo": 2, "terceiro": 1},
}
# Rodadas para um slot gasto regenerar, por círculo.
SLOT_REGEN = {"primeiro": 10, "segundo": 15, "terceiro": 20}
# Ao SUBIR para este nível, o jogador escolhe 1 nova magia conhecida do círculo.
NIVEL_NOVA_MAGIA = {2: "primeiro", 3: "segundo", 4: "segundo", 5: "terceiro"}

def slots_max_para(p):
    """Máximo de slots por círculo do jogador, pela tabela de nível (cap no 5)."""
    nivel = min(max(p.get("level", 1), 1), 5)
    return SLOTS_POR_NIVEL[nivel]
```

- [ ] **Step 4: Atualizar o init do jogador**

Em `server.py` (~2692-2694), substituir:

```python
        # ── Magias de Lewis (cleric) — slots por círculo (não usa MP) ──────────────
        "magias_usadas_hoje":  {"primeiro": 0, "segundo": 0, "terceiro": 0},
        "magias_conhecidas":   [],     # ids do GRIMORIO memorizados (vazio = todas da classe)
    }
```

por:

```python
        # ── Magias (Pedro/mage, Lewis/cleric) — magias conhecidas + slots c/ regen ──
        "magias_conhecidas":   [],     # ids do GRIMORIO escolhidos (obrigatório p/ lançar)
        "slots_cooldown":      {"primeiro": [], "segundo": [], "terceiro": []},  # ready_at por slot gasto
        "pending_spell_pick":  [],     # fila de círculos a escolher ao subir de nível
    }
```

- [ ] **Step 5: Adicionar os métodos de slot na classe `GameRoom`**

Em `server.py`, logo antes de `async def handle_magia` (~6651), inserir:

```python
    # ── Slots de magia (Pedro/Lewis): pool por círculo com regen por rodadas ──
    def _slot_prune(self, p, circulo):
        """Remove os cooldowns já vencidos (ready_at <= round_num)."""
        cd = p.setdefault("slots_cooldown", {"primeiro": [], "segundo": [], "terceiro": []})
        cd[circulo] = [r for r in cd.get(circulo, []) if r > self.round_num]

    def _slots_disponiveis(self, p, circulo):
        """Slots livres no círculo = máximo do nível − gastos ainda em cooldown."""
        self._slot_prune(p, circulo)
        usados = len(p["slots_cooldown"].get(circulo, []))
        return slots_max_para(p).get(circulo, 0) - usados

    def _gastar_slot(self, p, circulo):
        """Marca 1 slot do círculo como gasto: volta em SLOT_REGEN[circulo] rodadas."""
        p.setdefault("slots_cooldown", {"primeiro": [], "segundo": [], "terceiro": []})
        p["slots_cooldown"][circulo].append(self.round_num + SLOT_REGEN[circulo])

    def _proximo_slot_rodadas(self, p, circulo):
        """Menor contagem regressiva (rodadas) até liberar 1 slot do círculo, ou None."""
        self._slot_prune(p, circulo)
        cd = p["slots_cooldown"].get(circulo, [])
        if not cd:
            return None
        return max(0, min(cd) - self.round_num)

    def _recarregar_slots(self, p):
        """Recarga total (descanso na cidade): zera todos os cooldowns."""
        p["slots_cooldown"] = {"primeiro": [], "segundo": [], "terceiro": []}
```

- [ ] **Step 6: Rodar o teste e confirmar que passa**

Run: `python tools/test_magias_slots.py`
Expected: PASS nos blocos [1]–[4].

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_magias_slots.py
git commit -m "feat: modelo de slots de magia com regen por rodadas (server)"
```

---

## Task 2: `handle_magia` usa magias conhecidas + slots

**Files:**
- Modify: `server.py` `handle_magia` (~6651-6743)
- Test: `tools/test_magias_slots.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao `main()` de `tools/test_magias_slots.py`, antes do print final:

```python
    print("\n[5] handle_magia: exige magia conhecida e gasta slot")
    r = setup(); p = mk_mage(r, 1)
    r.round_num = 1
    # sem magia conhecida → recusa
    erros = []
    async def cap_send(pid, m):
        if m.get("type") == "error": erros.append(m["msg"])
    r.send_to = cap_send
    r.player_order = ["p1"]; r.turn_index = 0
    p["action_done"] = False; p["fome"] = 10; p["sede"] = 10
    await r.handle_magia("p1", {"magia_id": "bola_fogo", "tx": 3, "ty": 3})
    check("recusa magia não conhecida", any("não conhece" in e.lower() or "conhecida" in e.lower() for e in erros))
    # conhecendo a magia, lança e gasta slot
    p["magias_conhecidas"] = ["bola_fogo"]
    p["action_done"] = False; erros.clear()
    disp_antes = r._slots_disponiveis(p, "primeiro")
    await r.handle_magia("p1", {"magia_id": "bola_fogo", "tx": 3, "ty": 3})
    check("gastou 1 slot de 1º", r._slots_disponiveis(p, "primeiro") == disp_antes - 1)
    # sem slots → recusa
    p["action_done"] = False; erros.clear()
    p["slots_cooldown"]["primeiro"] = [r.round_num + 10, r.round_num + 10]  # 2 gastos (max no nv1)
    await r.handle_magia("p1", {"magia_id": "bola_fogo", "tx": 3, "ty": 3})
    check("recusa sem slot livre", any("slot" in e.lower() for e in erros))
```

> Nota: `_executar_magia_grimorio` chama `gm_say`/`push_state` (stubados) e helpers de mapa. Para `bola_fogo` em casa vazia o efeito é inócuo; se algum acesso a `self.tiles` falhar, definir no `setup()` um grid mínimo: `r.tiles = [[server.FLOOR]*server.MAP_W for _ in range(server.MAP_H)]` e `r._tem_linha_de_visao = lambda *a, **k: True`.

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_magias_slots.py`
Expected: FAIL no bloco [5] (a lógica antiga usa `magias_usadas_hoje`/modo teste e não checa `magias_conhecidas`).

- [ ] **Step 3: Reescrever a checagem de elegibilidade e custo de slot**

Em `server.py` `handle_magia`, remover o uso de `livre`/`MAGE_TESTE_LIVRE`. Substituir o trecho de classe + implementação (~6659-6687) por:

```python
        if p.get("class_id") not in ("mage", "cleric"):
            await self.send_to(pid, {"type": "error", "msg": "Sua classe não lança magias do grimório."}); return
        if p.get("petrificado"):
            await self.send_to(pid, {"type": "error", "msg": "🗿 Você está petrificado e não pode lançar magias!"}); return
        if p.get("paralisado"):
            await self.send_to(pid, {"type": "error", "msg": "❄️ Você está paralisado e não pode lançar magias!"}); return
        if p.get("dormindo"):
            await self.send_to(pid, {"type": "error", "msg": "🌙 Você está dormindo e não pode lançar magias!"}); return
        if self._em_silencio(p):
            await self.send_to(pid, {"type": "error", "msg": "🔇 Você está numa área de Silêncio e não pode lançar magias!"}); return

        is_mage = p.get("class_id") == "mage"

        # Ação principal (1 por turno).
        if self._acao_bloqueada(p):
            await self.send_to(pid, {"type": "error", "msg": "Ação principal já usada neste turno."}); return

        magia_id = (data or {}).get("magia_id")
        magia = GRIMORIO.get(magia_id)
        if not magia:
            await self.send_to(pid, {"type": "error", "msg": "Magia desconhecida."}); return
        if magia_id not in p.get("magias_conhecidas", []):
            await self.send_to(pid, {"type": "error", "msg": f"{p['name']} não conhece {magia['nome']}."}); return
        if magia_id not in GRIMORIO_IMPLEMENTADAS:
            await self.send_to(pid, {"type": "error",
                "msg": f"{magia['icone']} {magia['nome']} ainda está em desenvolvimento."}); return
```

- [ ] **Step 4: Substituir a checagem de custo do círculo (slots)**

Substituir o bloco "Custo do círculo" (~6689-6696) por:

```python
        # Custo do círculo: 1 SLOT do mesmo círculo (estrito). Ninguém usa MP.
        circulo = magia.get("circulo", "primeiro")
        if self._slots_disponiveis(p, circulo) <= 0:
            falta = self._proximo_slot_rodadas(p, circulo)
            extra = f" (volta em {falta} rodada{'s' if (falta or 0) != 1 else ''})" if falta is not None else ""
            await self.send_to(pid, {"type": "error",
                "msg": f"Sem slot de magia de {circulo} círculo{extra}."}); return
```

- [ ] **Step 5: Substituir a cobrança do slot e remover o `livre`**

Substituir o bloco "Custo do círculo (SLOT...)" (~6724-6729) por:

```python
        # Cobra 1 SLOT do círculo + 🍖/💧 de sobrevivência.
        self._gastar_slot(p, circulo)
        p["fome"] = max(0, p.get("fome", 10) - 1)
        p["sede"] = max(0, p.get("sede", 10) - 1)
        self._verificar_estado_sobrevivencia(p)
```

E na finalização (~6741-6742) trocar:

```python
        if not livre:                      # MODO TESTE: não consome a ação do turno
            p["action_done"] = True
```

por:

```python
        p["action_done"] = True
```

Também remover as ocorrências restantes de `and not livre`/`if not livre:` dentro de `handle_magia` (metamagia ~6714) — a metamagia passa a sempre cobrar normalmente; trocar `if (mm_fome or mm_sede) and not livre:` por `if (mm_fome or mm_sede):`.

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_magias_slots.py`
Expected: PASS nos blocos [1]–[5].

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_magias_slots.py
git commit -m "feat: handle_magia exige magia conhecida e consome slot c/ regen"
```

---

## Task 3: Remover reset por-turno + recarga total na cidade

**Files:**
- Modify: `server.py` início de turno (~9453-9456) e `_voltar_para_cidade` (~6140-6150)
- Test: `tools/test_magias_slots.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao `main()`:

```python
    print("\n[6] Recarga total ao voltar para a cidade")
    r = setup(); p = mk_mage(r, 1)
    r.player_order = ["p1"]
    r.round_num = 3
    r._gastar_slot(p, "primeiro")
    check("1 slot gasto antes da cidade", r._slots_disponiveis(p, "primeiro") == 1)
    r._gerar_loja_pergaminhos = lambda: None     # evita dependências da loja
    r._cancelar_timer_turno  = lambda: None
    await r._voltar_para_cidade()
    check("slots recarregados na cidade", r._slots_disponiveis(p, "primeiro") == 2)
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_magias_slots.py`
Expected: FAIL no bloco [6] (cidade ainda não recarrega slots).

- [ ] **Step 3: Remover o reset por turno**

Em `server.py` (~9453-9456), remover o bloco:

```python
        if cur_p.get("class_id") in ("cleric", "mage"):
            # Recarrega os slots de magia (Lewis e Pedro) no início do turno — os
            # limites por círculo seguem CLERIC_SLOTS / MAGE_SLOTS_POR_NIVEL.
            cur_p["magias_usadas_hoje"] = {"primeiro": 0, "segundo": 0, "terceiro": 0}
```

(A regeneração agora é governada só pelos timers de rodada.)

- [ ] **Step 4: Recarregar slots na transição para a cidade**

Em `_voltar_para_cidade` (~6145-6149), dentro do loop `for pp in self.players.values():`, adicionar após `pp["taverna_refeicoes"] = []`:

```python
            if pp.get("class_id") in ("mage", "cleric"):
                self._recarregar_slots(pp)   # descanso → todos os slots voltam cheios
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python tools/test_magias_slots.py`
Expected: PASS nos blocos [1]–[6].

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_magias_slots.py
git commit -m "feat: remove reset por-turno e recarrega slots ao descansar na cidade"
```

---

## Task 4: Level-up concede slot + enfileira escolha; bloqueia end_turn

**Files:**
- Modify: `server.py` `_check_level_up` (~11952-11966), `handle_end_turn` (~9338-9340), novo método `_enviar_spell_pick_prompt`
- Test: `tools/test_magias_slots.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao `main()`:

```python
    print("\n[7] Level-up concede slot cheio + enfileira escolha; bloqueia end_turn")
    r = setup(); p = mk_mage(r, 1)
    r.player_order = ["p1"]; r.turn_index = 0
    prompts = []
    async def cap_send2(pid, m):
        if m.get("type") == "spell_pick_prompt": prompts.append(m)
    r.send_to = cap_send2
    p["xp"] = 999   # garante subir de nível
    await r._check_level_up(p)
    check("subiu para nível 2", p["level"] == 2)
    check("slot novo de 1º entra cheio (3)", r._slots_disponiveis(p, "primeiro") == 3)
    check("fila de escolha tem 1 círculo", p["pending_spell_pick"] == ["primeiro"])
    check("enviou spell_pick_prompt", len(prompts) == 1 and prompts[0]["circulo"] == "primeiro")
    # end_turn bloqueado enquanto há escolha pendente
    erros = []
    async def cap_err(pid, m):
        if m.get("type") == "error": erros.append(m["msg"])
    r.send_to = cap_err
    r.animados_phase_pid = None
    await r.handle_end_turn("p1")
    check("end_turn bloqueado com escolha pendente", any("magia" in e.lower() for e in erros))
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_magias_slots.py`
Expected: FAIL no bloco [7].

- [ ] **Step 3: Adicionar `_enviar_spell_pick_prompt`**

Em `server.py`, antes de `_check_level_up` (~11952), inserir:

```python
    async def _enviar_spell_pick_prompt(self, p):
        """Envia ao jogador o prompt da próxima escolha de magia pendente (fila)."""
        fila = p.get("pending_spell_pick") or []
        if not fila:
            return
        circ = fila[0]
        opcoes = [mid for mid, m in GRIMORIO.items()
                  if p["class_id"] in m.get("classe", [])
                  and m.get("circulo") == circ
                  and mid not in p.get("magias_conhecidas", [])]
        await self.send_to(p["id"], {
            "type": "spell_pick_prompt", "circulo": circ, "count": 1, "opcoes": opcoes})
```

- [ ] **Step 4: Conceder a escolha no level-up**

Em `_check_level_up`, após a linha `await self.gm_say(f"⭐ **{p['name']}** subiu para o nível ...")` (~11966), adicionar:

```python
            if p.get("class_id") in ("mage", "cleric"):
                # Slot novo do nível já entra cheio (slots_max_para usa o novo level).
                circ = NIVEL_NOVA_MAGIA.get(p["level"])
                if circ:
                    p.setdefault("pending_spell_pick", []).append(circ)
                    await self._enviar_spell_pick_prompt(p)
```

- [ ] **Step 5: Bloquear `end_turn` com escolha pendente**

Em `handle_end_turn`, logo após `p = self.players[pid]` (~9340), adicionar:

```python
        if p.get("pending_spell_pick"):
            await self.send_to(pid, {"type": "error",
                "msg": "Escolha sua nova magia antes de encerrar o turno."}); return
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_magias_slots.py`
Expected: PASS nos blocos [1]–[7].

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_magias_slots.py
git commit -m "feat: level-up concede slot e enfileira escolha de magia; bloqueia end_turn"
```

---

## Task 5: `set_known_spells` + gate no start_game + carry-over

**Files:**
- Modify: `server.py` novo `handle_set_known_spells`, `start_game` (~3142-3151), roteamento (~12289-12290)
- Test: `tools/test_magias_slots.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao `main()`:

```python
    print("\n[8] set_known_spells: validação e carry-over no start_game")
    r = setup(); r.phase = "lobby"
    p = make_player("p1", "Pedro", "mage", 0); p["level"] = 1
    r.players["p1"] = p
    r.broadcast_lobby = lambda: asyncio.sleep(0)
    erros = []
    async def cap_err3(pid, m):
        if m.get("type") == "error": erros.append(m["msg"])
    r.send_to = cap_err3
    # contagem errada
    await r.handle_set_known_spells("p1", ["bola_fogo"])
    check("recusa != 2 magias", any("2 magias" in e or "exatamente" in e.lower() for e in erros))
    erros.clear()
    # círculo errado (clarividencia é 1º; usar uma de 2º p/ falhar) — escolher 2 de 1º válidas
    await r.handle_set_known_spells("p1", ["bola_fogo", "relampago"])
    check("aceita 2 magias de 1º da classe", p["magias_conhecidas"] == ["bola_fogo", "relampago"])
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_magias_slots.py`
Expected: FAIL no bloco [8] (`handle_set_known_spells` não existe).

- [ ] **Step 3: Adicionar `handle_set_known_spells`**

Em `server.py`, logo após `select_class` (~3073), inserir:

```python
    async def handle_set_known_spells(self, pid, ids):
        """Lobby: mago/clérigo escolhe 2 magias de 1º círculo da própria classe."""
        p = self.players.get(pid)
        if not p or self.phase != "lobby":
            return
        if p.get("class_id") not in ("mage", "cleric"):
            await self.send_to(pid, {"type": "error", "msg": "Sua classe não escolhe magias."}); return
        ids = list(dict.fromkeys(ids or []))   # remove duplicatas, preserva ordem
        if len(ids) != 2:
            await self.send_to(pid, {"type": "error", "msg": "Escolha exatamente 2 magias de 1º círculo."}); return
        for mid in ids:
            m = GRIMORIO.get(mid)
            if not m or p["class_id"] not in m.get("classe", []) or m.get("circulo") != "primeiro":
                await self.send_to(pid, {"type": "error", "msg": "Magia inválida para sua classe/círculo."}); return
        p["magias_conhecidas"] = ids
        await self.broadcast_lobby()
```

- [ ] **Step 4: Gate + carry-over no `start_game`**

Em `start_game`, após o check de classes (~3142-3144), adicionar:

```python
        for pp in self.players.values():
            if pp["class_id"] in ("mage", "cleric") and len(pp.get("magias_conhecidas", [])) < 2:
                await self.send_to(pid, {"type": "error",
                    "msg": "Magos e clérigos devem escolher 2 magias antes de iniciar."}); return
```

E no loop de construção dos full players (~3148-3149), preservar as magias escolhidas:

```python
        full_players = {}
        for slot, (pid2, p) in enumerate(self.players.items()):
            novo = make_player(pid2, p["name"], p["class_id"], slot)
            novo["magias_conhecidas"] = list(p.get("magias_conhecidas", []))
            full_players[pid2] = novo
```

- [ ] **Step 5: Rotear a mensagem**

Em `server.py` (~12289), após o ramo `select_class`, adicionar:

```python
                elif t == "set_known_spells":
                    if room: await room.handle_set_known_spells(pid, msg.get("ids"))
```

- [ ] **Step 6: Rodar e confirmar que passa**

Run: `python tools/test_magias_slots.py`
Expected: PASS nos blocos [1]–[8].

- [ ] **Step 7: Commit**

```bash
git add server.py tools/test_magias_slots.py
git commit -m "feat: set_known_spells (lobby) + gate e carry-over no start_game"
```

---

## Task 6: `escolher_magia_nivel` + roteamento

**Files:**
- Modify: `server.py` novo `handle_escolher_magia_nivel`, roteamento (~12289)
- Test: `tools/test_magias_slots.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar ao `main()`:

```python
    print("\n[9] escolher_magia_nivel adiciona magia e libera o turno")
    r = setup(); p = mk_mage(r, 2)
    p["magias_conhecidas"] = ["bola_fogo", "relampago"]
    p["pending_spell_pick"] = ["primeiro"]
    r.send_to = lambda pid, m: asyncio.sleep(0)
    # magia de círculo errado é recusada
    erros = []
    async def cap_err4(pid, m):
        if m.get("type") == "error": erros.append(m["msg"])
    r.send_to = cap_err4
    await r.handle_escolher_magia_nivel("p1", "escudo_arcano_2circ_invalido")  # id inexistente
    check("recusa magia inválida", len(erros) >= 1)
    # uma 1ª válida ainda não conhecida
    nova = next(mid for mid, m in server.GRIMORIO.items()
                if "mage" in m.get("classe", []) and m.get("circulo") == "primeiro"
                and mid not in p["magias_conhecidas"])
    await r.handle_escolher_magia_nivel("p1", nova)
    check("magia adicionada às conhecidas", nova in p["magias_conhecidas"])
    check("fila esvaziada", p["pending_spell_pick"] == [])
```

- [ ] **Step 2: Rodar e confirmar a falha**

Run: `python tools/test_magias_slots.py`
Expected: FAIL no bloco [9] (`handle_escolher_magia_nivel` não existe).

- [ ] **Step 3: Adicionar `handle_escolher_magia_nivel`**

Em `server.py`, logo após `handle_set_known_spells`, inserir:

```python
    async def handle_escolher_magia_nivel(self, pid, magia_id):
        """Resolve a escolha de nova magia pendente (1 item da fila por vez)."""
        p = self.players.get(pid)
        if not p:
            return
        fila = p.get("pending_spell_pick") or []
        if not fila:
            await self.send_to(pid, {"type": "error", "msg": "Nenhuma escolha de magia pendente."}); return
        circ = fila[0]
        m = GRIMORIO.get(magia_id)
        if not m or p["class_id"] not in m.get("classe", []) or m.get("circulo") != circ:
            await self.send_to(pid, {"type": "error", "msg": "Magia inválida para este círculo/classe."}); return
        if magia_id in p.get("magias_conhecidas", []):
            await self.send_to(pid, {"type": "error", "msg": "Você já conhece essa magia."}); return
        p.setdefault("magias_conhecidas", []).append(magia_id)
        fila.pop(0)
        await self.gm_say(f"📖 **{p['name']}** aprendeu **{m['nome']}**!")
        if fila:
            await self._enviar_spell_pick_prompt(p)   # próxima da fila
        await self.push_state()
```

- [ ] **Step 4: Rotear a mensagem**

Em `server.py` (~12289), após `set_known_spells`, adicionar:

```python
                elif t == "escolher_magia_nivel":
                    if room: await room.handle_escolher_magia_nivel(pid, msg.get("magia_id"))
```

- [ ] **Step 5: Rodar e confirmar que passa**

Run: `python tools/test_magias_slots.py`
Expected: PASS em todos os blocos [1]–[9].

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_magias_slots.py
git commit -m "feat: escolher_magia_nivel resolve a fila de escolhas de magia"
```

---

## Task 7: Limpeza de referências mortas no servidor

**Files:**
- Modify: `server.py` (buscar resíduos de `magias_usadas_hoje`, `slots_por_circulo`, `CLERIC_SLOTS`, `MAGE_SLOTS_POR_NIVEL`, `MAGE_TESTE_LIVRE`/`livre`)

- [ ] **Step 1: Localizar resíduos**

Run: `python -c "import re; [print(i+1, l.rstrip()) for i,l in enumerate(open('server.py', encoding='utf-8')) if any(k in l for k in ['magias_usadas_hoje','slots_por_circulo','CLERIC_SLOTS','MAGE_SLOTS_POR_NIVEL','MAGE_TESTE_LIVRE'])]"`
Expected: lista de linhas restantes (idealmente vazia após as Tasks 1-6; se sobrar, tratar agora).

- [ ] **Step 2: Remover/ajustar cada resíduo**

Para cada linha listada que ainda referencie os símbolos removidos: apagar a linha (se for o init/reset já tratado) ou substituir `slots_por_circulo(p, c)` por `slots_max_para(p)[c]`. Não deve restar nenhuma definição de `CLERIC_SLOTS`, `MAGE_SLOTS_POR_NIVEL`, `slots_por_circulo`, `MAGE_TESTE_LIVRE` nem leitura de `livre` dentro de `handle_magia`.

- [ ] **Step 3: Verificar que o servidor importa e os testes passam**

Run: `python -c "import server; print('ok')"`
Expected: `ok` (sem `NameError`).

Run: `python tools/test_magias_slots.py`
Expected: PASS em todos os blocos.

Run: `python tools/test_devorador.py`
Expected: PASS (regressão — nada de magias deve ter quebrado o resto).

- [ ] **Step 4: Commit**

```bash
git add server.py
git commit -m "refactor: remove símbolos do antigo sistema de slots de magia"
```

---

## Task 8: Ficha do cliente — slots com regen + sem modo teste

**Files:**
- Modify: `game.js` `renderMagiasFichaEmJogo` (~8007-8061), `_magiasConhecidasIds` (~7994-8004), `const MAGE_TESTE_LIVRE` (~7992)

- [ ] **Step 1: Desligar o modo teste do cliente**

Em `game.js` (~7992), trocar:

```javascript
const MAGE_TESTE_LIVRE = true;
```

por:

```javascript
const MAGE_TESTE_LIVRE = false;   // sistema normal: só magias conhecidas
```

- [ ] **Step 2: Simplificar `_magiasConhecidasIds` (sem fallback de teste)**

Substituir a função (~7994-8004) por:

```javascript
// Magias conhecidas → ids escolhidos pelo jogador (vazio = nenhuma disponível).
function _magiasConhecidasIds(heroi) {
  const known = heroi && (heroi.magias_conhecidas
    || (Array.isArray(heroi.magiasConhecidas) ? heroi.magiasConhecidas.map(x => x.id || x) : null));
  return Array.isArray(known) ? known : [];
}
```

- [ ] **Step 3: Reescrever `renderMagiasFichaEmJogo` para slots com cooldown**

Substituir a função (~8007-8061) por:

```javascript
// Tabela de slots por nível (espelha SLOTS_POR_NIVEL no server) e regen por círculo.
const SLOTS_POR_NIVEL_CLIENT = {
  1: {primeiro:2, segundo:0, terceiro:0},
  2: {primeiro:3, segundo:0, terceiro:0},
  3: {primeiro:3, segundo:1, terceiro:0},
  4: {primeiro:3, segundo:2, terceiro:0},
  5: {primeiro:3, segundo:2, terceiro:1},
};

// Aba de magias em jogo: cartas por círculo + pips de slot com contagem regressiva.
function renderMagiasFichaEmJogo(heroi, cls) {
  cls = cls || (heroi && heroi.class_id) || 'mage';
  const nivel    = Math.min((heroi && (heroi.level || heroi.nivel)) || 1, 5);
  const known    = _magiasConhecidasIds(heroi);
  const limites  = SLOTS_POR_NIVEL_CLIENT[nivel];
  const cooldown = (heroi && heroi.slots_cooldown) || {primeiro:[], segundo:[], terceiro:[]};
  const round    = (window.GS && GS.round && GS.round()) || (heroi && heroi.__round) || 0;

  function renderCirculoMagias(circulo, label) {
    const magiasCirculo = known.filter(id => GRIMORIO_CLIENT[id] && GRIMORIO_CLIENT[id].circulo === circulo);
    const limite = limites[circulo] || 0;
    if (limite === 0) return `
      <div style="opacity:0.3; margin-bottom:12px;">
        <div style="color:#4a4a4a; font-size:9px; letter-spacing:2px;">${label} — disponível em nível maior</div>
      </div>`;

    // Contagens regressivas dos slots gastos (menores primeiro).
    const espera = (cooldown[circulo] || []).map(r => Math.max(0, r - round)).sort((a,b) => a - b);
    const livres = Math.max(0, limite - espera.length);

    const pips = Array.from({length: limite}).map((_, i) => {
      if (i < livres) {
        return `<div title="Pronto" style="width:16px; height:16px; border-radius:50%; background:#44cc88; border:1px solid #44cc88;"></div>`;
      }
      const falta = espera[i - livres];   // rodadas até liberar este slot
      return `<div title="Volta em ${falta} rodada(s)" style="width:16px; height:16px; border-radius:50%; background:#1a1a1a; border:1px solid #3a3a3a; display:flex; align-items:center; justify-content:center; color:#cc8844; font-size:9px;">${falta}</div>`;
    }).join('');

    return `
      <div style="margin-bottom:14px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <span style="color:#8a7a5a; font-size:9px; letter-spacing:2px;">${label}</span>
          <span style="color:${livres === 0 ? '#ff4136' : '#44cc88'}; font-size:10px;">${livres}/${limite} slots</span>
        </div>
        <div style="display:flex; gap:4px; margin-bottom:8px;">${pips}</div>
        <div style="display:flex; flex-wrap:wrap; gap:4px;">
          ${magiasCirculo.map((id, idx) => criarCartaMagia(id, false, livres > 0, livres === 0, 'jogo')).join('')}
          ${magiasCirculo.length === 0 ? `<div style="color:#4a4a4a; font-size:9px; font-style:italic; padding:8px;">Nenhuma magia memorizada</div>` : ''}
        </div>
      </div>`;
  }

  return `
    <div style="padding:4px 0;">
      ${renderCirculoMagias('primeiro', '1º CÍRCULO')}
      ${renderCirculoMagias('segundo',  '2º CÍRCULO')}
      ${renderCirculoMagias('terceiro', '3º CÍRCULO')}
    </div>`;
}
```

> `criarCartaMagia(id, selecionada, disponivel, usada, modo)` já existe (game.js ~7903). Aqui `disponivel = livres > 0` e `usada = livres === 0` controlam o estilo de carta lançável/esgotada.

- [ ] **Step 4: Expor `GS.round()` no estado do cliente**

Em `src/gameState.js`, no bloco que processa `case 'game_state':` (~992-1010), confirmar que `msg.round` é guardado (ex.: `gameState.round = msg.round`) e adicionar um getter `round` ao objeto exportado `GS` (junto dos demais getters), retornando `gameState && gameState.round || 0`. Se já existir um getter equivalente, reutilizá-lo no Step 3.

- [ ] **Step 5: Verificação manual no app**

Subir o servidor e abrir o cliente:

Run: `python server.py` (em background) e abrir `http://localhost:8765/index.html`.
Conferir, com um mago em jogo, que a aba de magias mostra só as magias conhecidas e que, ao lançar, o pip vira a contagem regressiva (número de rodadas). Usar o fluxo de verificação de preview (`preview_*`) se disponível; senão, validar visualmente.

- [ ] **Step 6: Commit**

```bash
git add game.js src/gameState.js
git commit -m "feat: ficha mostra magias conhecidas e slots com contagem regressiva"
```

---

## Task 9: Seleção de magias na criação (lobby)

**Files:**
- Modify: `game.js` tela de seleção de classe (`csConfirmClass` ~17111 e o render do lobby), `renderSelecaoMagias` (~8065-8087)
- Modify: `src/gameState.js` sender `setKnownSpells`

- [ ] **Step 1: Adicionar o sender no gameState**

Em `src/gameState.js`, junto dos outros action senders (perto de onde `select_class` é enviado), adicionar:

```javascript
  function setKnownSpells(ids) { send({ type: 'set_known_spells', ids: ids }); }
```

E exportá-lo no objeto `GS` (junto dos demais métodos, ex.: `setKnownSpells,`).

- [ ] **Step 2: Mostrar a seleção após escolher mago/clérigo**

Em `game.js`, no fluxo de seleção de classe: quando a classe escolhida for `mage` ou `cleric`, renderizar `renderSelecaoMagias(heroiKey, 'primeiro')` (heroiKey derivado da classe: mage→'pedro', cleric→'lewis') num painel do lobby. Ajustar `renderSelecaoMagias` (~8065) para filtrar por classe via parâmetro em vez do mapa fixo `heroiKey`:

```javascript
function renderSelecaoMagias(cls, circulo) {
  const limite = { primeiro: 2, segundo: 0, terceiro: 0 };
  const magiasDisponiveis = Object.values(GRIMORIO_CLIENT).filter(m =>
    m.circulo === circulo && m.classe.includes(cls));
  const selecionadas = window._magiasSelecionadas || [];
  const max = limite[circulo] || 0;
  return `
    <div id="selecao-magias">
      <div style="color:#8a7a5a; font-size:9px; letter-spacing:3px; margin-bottom:10px;">ESCOLHA ${max} MAGIA${max > 1 ? 'S' : ''} DE 1º CÍRCULO</div>
      <div style="display:flex; flex-wrap:wrap; gap:2px; margin-bottom:14px;">
        ${magiasDisponiveis.map(m => {
          const sel  = selecionadas.includes(m.id);
          const pode = sel || selecionadas.length < max;
          return criarCartaMagia(m.id, sel, pode, false);
        }).join('')}
      </div>
      <div style="padding:8px 10px; background:rgba(200,169,81,0.05); border:1px solid #c8a95133; color:#8a7a5a; font-size:9px; text-align:center; letter-spacing:1px;">
        ${selecionadas.length}/${max} magias selecionadas
        ${selecionadas.length === max ? ' — <span style="color:#44cc88;">✓ Pronto</span>' : ''}
      </div>
    </div>`;
}
```

E atualizar `window.selecionarMagia` (~8089-8102) para usar a lista única `window._magiasSelecionadas` (sem `heroiKey`) e re-renderizar via a classe atual guardada em `window._classeSelecaoMagia`:

```javascript
window.selecionarMagia = function(magiaId) {
  window._magiasSelecionadas = window._magiasSelecionadas || [];
  const lista = window._magiasSelecionadas;
  const max = 2;
  if (lista.includes(magiaId)) {
    window._magiasSelecionadas = lista.filter(id => id !== magiaId);
  } else if (lista.length < max) {
    lista.push(magiaId);
  }
  const container = document.getElementById('selecao-magias');
  if (container) container.outerHTML = renderSelecaoMagias(window._classeSelecaoMagia || 'mage', 'primeiro');
};
```

- [ ] **Step 3: Enviar a escolha ao confirmar**

Em `csConfirmClass` (~17111-17119), após `send({type:'select_class', ...})`, quando a classe for mage/cleric exigir 2 magias selecionadas e enviar:

```javascript
  if (csf.selectedId === 'mage' || csf.selectedId === 'cleric') {
    const ids = window._magiasSelecionadas || [];
    if (ids.length !== 2) { toast('Escolha 2 magias de 1º círculo.', 'var(--orange)'); return; }
    GS.setKnownSpells(ids);
  }
```

(Definir `window._classeSelecaoMagia = csf.selectedId` ao abrir o painel de seleção.)

- [ ] **Step 4: Verificação manual**

Run: `python server.py` e abrir dois clientes (ou um) no lobby. Escolher Pedro/Lewis, selecionar 2 magias, confirmar. Conferir que o botão "iniciar" só funciona com as 2 magias escolhidas (o servidor recusa com a mensagem da Task 5 caso contrário) e que, em jogo, a ficha mostra exatamente essas 2 magias.

- [ ] **Step 5: Commit**

```bash
git add game.js src/gameState.js
git commit -m "feat: seleção obrigatória de 2 magias de 1º círculo na criação"
```

---

## Task 10: Overlay de escolha de magia ao subir de nível

**Files:**
- Modify: `src/gameState.js` handler `case 'spell_pick_prompt'` + sender `escolherMagiaNivel`
- Modify: `game.js` overlay de escolha (novo) + registro do callback

- [ ] **Step 1: Tratar a mensagem no gameState**

Em `src/gameState.js`, no switch de mensagens (junto dos outros `case`), adicionar:

```javascript
      case 'spell_pick_prompt':
        _emit('spellPickPrompt', msg);   // {circulo, count, opcoes}
        break;
```

E adicionar o sender + exportá-lo em `GS`:

```javascript
  function escolherMagiaNivel(magiaId) { send({ type: 'escolher_magia_nivel', magia_id: magiaId }); }
```

- [ ] **Step 2: Construir o overlay no cliente**

Em `game.js`, adicionar uma função que monta um overlay modal listando `msg.opcoes` como cartas (`criarCartaMagia`) e, ao clicar numa, chama `GS.escolherMagiaNivel(id)` e fecha o overlay:

```javascript
function mostrarOverlayEscolhaMagia(msg) {
  const rotulo = {primeiro:'1º', segundo:'2º', terceiro:'3º'}[msg.circulo] || msg.circulo;
  const cartas = (msg.opcoes || []).map(id =>
    `<div onclick="window._escolherMagiaNivel('${id}')" style="cursor:pointer;">
       ${criarCartaMagia(id, false, true, false)}
     </div>`).join('');
  const el = document.createElement('div');
  el.id = 'overlay-escolha-magia';
  el.style.cssText = 'position:fixed; inset:0; background:rgba(0,0,0,0.85); z-index:9999; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:14px;';
  el.innerHTML = `
    <div style="color:#c8a951; font-size:14px; letter-spacing:3px;">SUBIU DE NÍVEL — ESCOLHA 1 MAGIA DE ${rotulo} CÍRCULO</div>
    <div style="display:flex; flex-wrap:wrap; gap:8px; max-width:680px; justify-content:center;">${cartas}</div>`;
  document.body.appendChild(el);
}

window._escolherMagiaNivel = function(id) {
  GS.escolherMagiaNivel(id);
  const el = document.getElementById('overlay-escolha-magia');
  if (el) el.remove();
};
```

- [ ] **Step 3: Registrar o callback**

Em `game.js`, onde os outros `GS.on(...)` são registrados na inicialização, adicionar:

```javascript
GS.on('spellPickPrompt', mostrarOverlayEscolhaMagia);
```

- [ ] **Step 4: Verificação manual**

Run: `python server.py`. Em jogo com um mago, conceder XP suficiente para subir de nível (matar monstros ou, em teste local, ajustar XP). Confirmar: o overlay aparece **só** para o jogador que subiu; ao escolher, a magia entra na ficha e o overlay fecha; tentar `encerrar turno` antes de escolher é recusado com a mensagem da Task 4.

- [ ] **Step 5: Commit**

```bash
git add game.js src/gameState.js
git commit -m "feat: overlay de escolha de magia ao subir de nível"
```

---

## Verificação final

- [ ] **Suíte de testes do servidor**

Run: `python tools/test_magias_slots.py`
Expected: PASS em todos os blocos [1]–[9].

Run: `python tools/test_devorador.py`
Expected: PASS (sem regressão).

- [ ] **Smoke test ponta a ponta (manual)**

1. Lobby: criar sala, escolher Pedro, selecionar 2 magias de 1º, iniciar.
2. Em jogo: lançar magia → pip vira contagem regressiva; lançar até esgotar → recusa "sem slot (volta em N rodadas)".
3. Passar N rodadas → o slot volta.
4. Voltar à cidade pela escada → todos os slots cheios.
5. Subir de nível → overlay de escolha; `end_turn` bloqueado até escolher; nova magia aparece na ficha.
6. Repetir até nível 5 → conferir 3/2/1 magias conhecidas e slots máximos 3/2/1.

---

## Notas de revisão (self-review)

- **Cobertura do spec:** seções 3 (modelo), 4 (progressão), 5 (fluxos), 6 (lançamento), 7 (cidade), 8 (remoção do reset), 9 (estado→cliente, via `push_state` que já envia players completos + `round`), 10 (ficha), 11 (limpeza), 12 (protocolo), 13 (bordas: rejoin usa estado persistido; fila de múltiplos level-ups) — todas mapeadas em tasks.
- **Cap nível 6+:** `slots_max_para` faz clamp em 5 e `NIVEL_NOVA_MAGIA` não tem entradas >5 → sem novas magias/slots (TODO no spec para estender).
- **Nomes consistentes:** `slots_cooldown`, `slots_max_para`, `_slots_disponiveis`, `_gastar_slot`, `_proximo_slot_rodadas`, `_recarregar_slots`, `pending_spell_pick`, `_enviar_spell_pick_prompt`, `handle_set_known_spells`, `handle_escolher_magia_nivel` — usados de forma idêntica entre tasks.
