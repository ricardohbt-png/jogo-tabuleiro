# Popup de Resultado de Armadilha — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Quando um personagem cai numa armadilha (buraco procedural genérico ou
qualquer uma das 8 armadilhas do catálogo `ARMADILHAS`), o jogador afetado vê
uma caixa de texto dedicada — nome/tipo, se escapou ou não, e o efeito/dano
sofrido — em vez de depender só do log de texto do Mestre.

**Architecture:** Nova mensagem WebSocket `trap_result`, enviada via
`send_to(pid, ...)` (nunca broadcast) a partir de 4 pontos do `server.py` onde
armadilhas já são resolvidas hoje. `gameState.js` só repassa o evento
(`_emit('trapResult', msg)`, zero lógica). `game.js` ganha um novo overlay
modal (mesmo padrão do `#chest-overlay` já existente) com fila simples, tema
visual de perigo, e um efeito sonoro curto no caso de falha.

**Tech Stack:** Python 3 (`websockets`), vanilla JS (sem framework), WebAudio
API já existente (`_sfxBus`).

Spec completa: [`docs/superpowers/specs/2026-07-06-popup-armadilha-design.md`](../specs/2026-07-06-popup-armadilha-design.md)

---

## Task 1: Extrair `_verificar_trap_procedural` (buraco de sala procedural)

O buraco genérico gerado no mapa procedural (`self.traps`, distinto do
catálogo `ARMADILHAS`) hoje é resolvido inline dentro de `handle_move`. Vamos
extraí-lo pra um método próprio — isso permite testar a lógica isolada, sem
precisar simular um `handle_move` completo (colisões, portas, decorações
etc.), e é exatamente o bloco que precisamos tocar para adicionar o popup.

**Files:**
- Modify: `server.py:5643-5661` (bloco `# Check trap` dentro de `handle_move`)
- Test: `tools/test_armadilha_popup.py` (novo arquivo)

- [ ] **Step 1: Criar o arquivo de teste com a base (setup/check/trap_msgs) e o primeiro cenário, que vai FALHAR (método ainda não existe)**

```python
"""Teste do popup de resultado de armadilha (trap_result): buraco procedural,
armadilha de 1 alvo, armadilha de área (save_reduz), tick progressivo da
Incendiária, e roteamento pro resgatador do prisioneiro.
Roda da raiz: python tools/test_armadilha_popup.py"""
import asyncio, sys, os
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
from server import GameRoom, make_player, make_monster, MONSTER_DEFS, ARMADILHAS

def setup():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r._broadcast_dado = noop
    r._tem_linha_de_visao = lambda *a, **k: True
    r.tiles = [[server.FLOOR] * server.MAP_W for _ in range(server.MAP_H)]
    r.phase = "playing"
    r._is_turn = lambda pid: True
    r.sent = []
    async def capture(pid, msg):
        r.sent.append((pid, msg))
    r.send_to = capture
    return r

def trap_msgs(r, pid=None):
    """Mensagens trap_result capturadas, opcionalmente filtradas por destinatário."""
    return [m for p, m in r.sent if m.get("type") == "trap_result" and (pid is None or p == pid)]

def fake_rng(d20):
    """Substituto de random.randint: `d20` pra rolagens de d20 (b==20);
    fixa em 3 qualquer outra rolagem de dado (dano/veneno/reduzir_con)."""
    def f(a, b):
        return d20 if b == 20 else 3
    return f

def fake_rng_seq(d20_seq):
    """Como fake_rng, mas consome uma sequência de valores de d20 em ordem
    (uma chamada por save de d20; damage dice sempre fixo em 3)."""
    it = iter(d20_seq)
    def f(a, b):
        return next(it) if b == 20 else 3
    return f

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

async def main():
    # ── [1] Buraco procedural (self.traps) ─────────────────────────────────────
    print("\n[1] Buraco procedural — popup de sucesso e de falha")
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    r.traps = [{"id": "t1", "pos": [6, 5], "damage": 5, "triggered": False, "room_id": None}]
    _o = server.random.randint; server.random.randint = lambda a, b: 20   # sempre passa (20+0>=13)
    await r._verificar_trap_procedural("p1", p, 6, 5)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("1 popup enviado", len(msgs) == 1)
    check("nome genérico correto", msgs[0]["nome"] == "Buraco Escondido")
    check("sucesso=True, dano=0", msgs[0]["sucesso"] is True and msgs[0]["dano"] == 0)

    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    r.traps = [{"id": "t1", "pos": [6, 5], "damage": 5, "triggered": False, "room_id": None}]
    _o = server.random.randint; server.random.randint = lambda a, b: 1   # sempre falha (1+0<13)
    await r._verificar_trap_procedural("p1", p, 6, 5)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("popup de falha: sucesso=False", msgs and msgs[0]["sucesso"] is False)
    check("popup de falha: dano correto", msgs[0]["dano"] == 5)
    check("popup de falha: menciona o dano", any("dano" in t for t in msgs[0]["efeitos_extra"]))
    check("trap não dispara 2x (triggered)", r.traps[0]["triggered"] is True)

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
```

- [ ] **Step 2: Rodar e confirmar que falha (método não existe ainda)**

Run: `python tools/test_armadilha_popup.py`
Expected: `AttributeError: 'GameRoom' object has no attribute '_verificar_trap_procedural'`

- [ ] **Step 3: Extrair o método em `server.py`**

Em `server.py`, localize este bloco dentro de `handle_move` (linhas ~5643-5661):

```python
        # Check trap
        for trap in self.traps:
            if trap["pos"] == [nx, ny] and not trap["triggered"]:
                if "detect_trap" not in [s for s in p.get("status", [])]:
                    trap["triggered"] = True
                    prefix = random.choice(GM["room_trap"])
                    save_roll = random.randint(1, 20)
                    cancao_res = self._cancao_bonus(p, "bonus_res")
                    passed = save_roll + p["ref_"] + self._modificador_sobrevivencia(p) + cancao_res >= 13
                    await self.broadcast({"type": "dice_roll", "die": "d20",
                                           "value": save_roll, "label": "Reflexos"})
                    if passed:
                        await self.gm_say(prefix + f" **{p['name']}** passou no teste de **Reflexos** (CD 13) e se esquivou!")
                    else:
                        p["hp"] = max(0, p["hp"] - trap["damage"])
                        await self.gm_say(prefix + f" **{p['name']}** falhou em **Reflexos** (CD 13) e sofre **{trap['damage']}** de dano!")
                        if p["hp"] <= 0:
                            await self._player_dies(pid)
```

Substitua por uma única chamada:

```python
        # Check trap
        await self._verificar_trap_procedural(pid, p, nx, ny)
```

Agora adicione o método novo logo depois do fim de `handle_move` (que termina em
`await self.push_state()`, antes de `async def handle_open_door`, ~linha 5677):

```python
    async def _verificar_trap_procedural(self, pid, p, nx, ny):
        """Buraco genérico de sala procedural (self.traps, distinto do catálogo
        ARMADILHAS) — testa Reflexos CD13, aplica dano e envia o popup
        trap_result pra quem pisou."""
        for trap in self.traps:
            if trap["pos"] == [nx, ny] and not trap["triggered"]:
                if "detect_trap" in [s for s in p.get("status", [])]:
                    continue
                trap["triggered"] = True
                prefix = random.choice(GM["room_trap"])
                save_roll = random.randint(1, 20)
                cancao_res = self._cancao_bonus(p, "bonus_res")
                passed = save_roll + p["ref_"] + self._modificador_sobrevivencia(p) + cancao_res >= 13
                await self.broadcast({"type": "dice_roll", "die": "d20",
                                       "value": save_roll, "label": "Reflexos"})
                if passed:
                    await self.gm_say(prefix + f" **{p['name']}** passou no teste de **Reflexos** (CD 13) e se esquivou!")
                    await self._enviar_trap_result(
                        p, "Buraco Escondido", "🕳️", sucesso=True, dano=0, metade=False,
                        descricao="Um buraco disfarçado se abre sob seus pés.",
                        efeitos_extra=[])
                else:
                    p["hp"] = max(0, p["hp"] - trap["damage"])
                    await self.gm_say(prefix + f" **{p['name']}** falhou em **Reflexos** (CD 13) e sofre **{trap['damage']}** de dano!")
                    await self._enviar_trap_result(
                        p, "Buraco Escondido", "🕳️", sucesso=False, dano=trap["damage"], metade=False,
                        descricao="Um buraco disfarçado se abre sob seus pés.",
                        efeitos_extra=[f"💥 Sofreu {trap['damage']} de dano"])
                    if p["hp"] <= 0:
                        await self._player_dies(pid)
```

Note que `_enviar_trap_result` ainda não existe — é o próximo Task. Por
enquanto o teste continua falhando (agora com `AttributeError:
'_enviar_trap_result'`), o que é esperado.

- [ ] **Step 4: Rodar de novo e confirmar a nova falha esperada**

Run: `python tools/test_armadilha_popup.py`
Expected: `AttributeError: 'GameRoom' object has no attribute '_enviar_trap_result'`

(Isso confirma que a extração do Step 3 está correta — o erro mudou pro
próximo elo que falta, não é mais sobre `_verificar_trap_procedural`.)

---

## Task 2: Adicionar `_enviar_trap_result` (helper de roteamento)

**Files:**
- Modify: `server.py` (novo método, logo antes de `_disparar_armadilha`, ~linha 10770)
- Test: `tools/test_armadilha_popup.py` (já escrito no Task 1 — só roda de novo)

- [ ] **Step 1: Adicionar o helper em `server.py`, imediatamente antes de `async def _disparar_armadilha`**

```python
    async def _enviar_trap_result(self, alvo, nome, icone, sucesso, dano, metade,
                                   descricao, efeitos_extra, tick=False):
        """Envia o popup trap_result pra quem está no controle de `alvo`: o
        próprio jogador, ou o resgatador do prisioneiro (rescuer_pid). Monstros
        e servos animados não têm cliente — não enviamos nada pra eles."""
        if self._eh_jogador(alvo):
            pid = alvo["id"]
        elif alvo is self.prisoner:
            pid = self.prisoner.get("rescuer_pid")
        else:
            return
        if not pid:
            return
        await self.send_to(pid, {
            "type": "trap_result", "nome": nome, "icone": icone,
            "sucesso": sucesso, "dano": dano, "metade": metade,
            "descricao": descricao, "efeitos_extra": efeitos_extra, "tick": tick,
        })
```

- [ ] **Step 2: Rodar o teste e confirmar que passa (os 2 cenários do buraco procedural)**

Run: `python tools/test_armadilha_popup.py`
Expected: `===== RESULTADO: 7 passaram, 0 falharam =====`

- [ ] **Step 3: Commit**

```bash
git add server.py tools/test_armadilha_popup.py
git commit -m "feat(armadilha): extrai trap procedural e envia popup trap_result"
```

---

## Task 3: `_aplicar_efeito_armadilha` retorna (dano, texto) em vez de None

Hoje cada efeito (dano/perder_movimento/perder_rodada/veneno/reduzir_con) só
manda `gm_say` — precisamos que devolva um resumo pro chamador acumular no
popup.

**Files:**
- Modify: `server.py:10828-10869` (método `_aplicar_efeito_armadilha`)
- Test: `tools/test_armadilha_popup.py`

- [ ] **Step 1: Adicionar ao teste os cenários [2] e [2b], que vão FALHAR (o retorno ainda é `None`, não uma tupla)**

Adicione ao `tools/test_armadilha_popup.py`, entre o bloco `[1]` e o
`print(f"\n===== RESULTADO...` final:

```python
    # ── [2] Armadilha de 1 alvo (Armadilha de Urso: dano + perder_movimento) ───
    print("\n[2] Armadilha de Urso — falha (dano + efeito) e sucesso (evita)")
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    arm = {"id": "a1", "tipo": "armadilha_urso", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = fake_rng(1)   # d20=1: falha (dif 10)
    await r._disparar_armadilha(p, arm)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("popup enviado", len(msgs) == 1)
    check("nome/ícone corretos", msgs[0]["nome"] == "Armadilha de Urso" and msgs[0]["icone"] == "🪤")
    check("sucesso=False", msgs[0]["sucesso"] is False)
    check("dano > 0 (1d4 fixo em 3)", msgs[0]["dano"] == 3)
    check("efeitos_extra tem dano + movimento",
          any("dano" in t for t in msgs[0]["efeitos_extra"])
          and any("movimento" in t for t in msgs[0]["efeitos_extra"]))

    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    arm = {"id": "a2", "tipo": "armadilha_urso", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = fake_rng(15)   # d20=15: passa (dif 10)
    await r._disparar_armadilha(p, arm)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("popup de sucesso: sucesso=True, dano=0", msgs and msgs[0]["sucesso"] is True and msgs[0]["dano"] == 0)
    check("popup de sucesso: sem efeitos_extra", msgs[0]["efeitos_extra"] == [])

    # ── [2b] Buraco colocável: só efeito, sem dano nenhum ───────────────────────
    print("\n[2b] Buraco colocável — falha só com efeito, sem dano")
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    arm = {"id": "a3", "tipo": "buraco", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = fake_rng(1)   # falha (dif 10)
    await r._disparar_armadilha(p, arm)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("dano=0 mesmo na falha (só efeito)", msgs and msgs[0]["dano"] == 0)
    check("efeitos_extra só tem o efeito, sem linha de dano",
          msgs[0]["efeitos_extra"] == ["🦵 Perdeu o movimento"])
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_armadilha_popup.py`
Expected: falhas em "popup enviado" (0 mensagens — `_disparar_armadilha` ainda
não chama `_enviar_trap_result`).

- [ ] **Step 3: Reescrever `_aplicar_efeito_armadilha` em `server.py` (linhas ~10828-10869) pra devolver `(dano, texto)`**

Texto atual a substituir:

```python
    async def _aplicar_efeito_armadilha(self, alvo, ef, arm):
        tipo_ef = ef.get("tipo")
        alvo_nome = alvo.get("name") or alvo.get("nome", "Alvo")

        if tipo_ef == "dano":
            if ef.get("rodada", 1) > 1:
                # Dano progressivo: agenda p/ rodadas seguintes (ver _processar_efeitos_armadilha_turno).
                # O prisioneiro não tem "id" → sentinela dedicada para o lookup por turno.
                aid = "__prisioneiro__" if alvo is self.prisoner else alvo.get("id")
                arm.setdefault("efeitos_ativos", []).append({
                    "alvo_id": aid, "valor": ef["valor"],
                    "elemento": ef.get("elemento", "fisico"), "rodadas_restantes": ef["rodada"] - 1,
                })
                return
            dano = self._rolar_dado(ef["valor"])
            if ef.get("metade"):
                dano = max(1, dano // 2)
            await self._dano_em_alvo(alvo, dano, ef.get("elemento", "fisico"), arm.get("criador"))

        elif tipo_ef == "perder_movimento":
            alvo["moves_left"] = 0
            alvo["movimento_perdido"] = True
            await self.gm_say(f"🦵 **{alvo_nome}** perde o movimento!")

        elif tipo_ef == "perder_rodada":
            alvo["moves_left"] = 0
            if self._eh_jogador(alvo):
                alvo["action_done"] = True
                alvo["bonus_action_used"] = True
            else:
                alvo["perde_turno"] = True
            await self.gm_say(f"⏸️ **{alvo_nome}** perde a rodada inteira!")

        elif tipo_ef == "veneno":
            if arm.get("veneno_id"):
                await self._aplicar_veneno(alvo, arm["veneno_id"], fonte="armadilha")

        elif tipo_ef == "reduzir_con":
            valor = self._rolar_dado(ef["valor"])
            if ef.get("metade"):
                valor = max(1, valor // 2)
            await self._reduzir_con_temporario(alvo, valor, ef.get("duracao", 3))
```

Novo texto:

```python
    async def _aplicar_efeito_armadilha(self, alvo, ef, arm):
        """Aplica um efeito de armadilha em `alvo`. Retorna (dano_aplicado,
        texto): `texto` é a linha pronta pro popup trap_result, ou None quando
        o efeito não gera linha própria (ex.: dano progressivo agendado, cujo
        dano aparece nos popups de tick de _processar_efeitos_armadilha_turno)."""
        tipo_ef = ef.get("tipo")
        alvo_nome = alvo.get("name") or alvo.get("nome", "Alvo")

        if tipo_ef == "dano":
            if ef.get("rodada", 1) > 1:
                # Dano progressivo: agenda p/ rodadas seguintes (ver _processar_efeitos_armadilha_turno).
                # O prisioneiro não tem "id" → sentinela dedicada para o lookup por turno.
                aid = "__prisioneiro__" if alvo is self.prisoner else alvo.get("id")
                arm.setdefault("efeitos_ativos", []).append({
                    "alvo_id": aid, "valor": ef["valor"],
                    "elemento": ef.get("elemento", "fisico"), "rodadas_restantes": ef["rodada"] - 1,
                })
                return 0, None
            dano = self._rolar_dado(ef["valor"])
            if ef.get("metade"):
                dano = max(1, dano // 2)
            await self._dano_em_alvo(alvo, dano, ef.get("elemento", "fisico"), arm.get("criador"))
            return dano, None

        elif tipo_ef == "perder_movimento":
            alvo["moves_left"] = 0
            alvo["movimento_perdido"] = True
            await self.gm_say(f"🦵 **{alvo_nome}** perde o movimento!")
            return 0, "🦵 Perdeu o movimento"

        elif tipo_ef == "perder_rodada":
            alvo["moves_left"] = 0
            if self._eh_jogador(alvo):
                alvo["action_done"] = True
                alvo["bonus_action_used"] = True
            else:
                alvo["perde_turno"] = True
            await self.gm_say(f"⏸️ **{alvo_nome}** perde a rodada inteira!")
            return 0, "⏸️ Perdeu a rodada inteira"

        elif tipo_ef == "veneno":
            if arm.get("veneno_id"):
                await self._aplicar_veneno(alvo, arm["veneno_id"], fonte="armadilha")
                veneno_nome = VENENOS.get(arm["veneno_id"], {}).get("nome", "Veneno")
                return 0, f"☠️ Envenenado ({veneno_nome})"
            return 0, None

        elif tipo_ef == "reduzir_con":
            valor = self._rolar_dado(ef["valor"])
            if ef.get("metade"):
                valor = max(1, valor // 2)
            duracao = ef.get("duracao", 3)
            await self._reduzir_con_temporario(alvo, valor, duracao)
            return 0, f"🌫️ -{valor} CON por {duracao} rodadas"

        return 0, None
```

- [ ] **Step 4: Rodar de novo — ainda deve falhar (os chamadores não usam o retorno nem enviam popup ainda), mas sem exceções novas**

Run: `python tools/test_armadilha_popup.py`
Expected: mesmas falhas de "popup enviado" (0 mensagens), sem erro de tipo/exceção.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_armadilha_popup.py
git commit -m "refactor(armadilha): _aplicar_efeito_armadilha devolve (dano, texto)"
```

---

## Task 4: `_disparar_armadilha` envia o popup (armadilha de 1 alvo)

**Files:**
- Modify: `server.py:10770-10792` (método `_disparar_armadilha`, branch não-área)
- Test: `tools/test_armadilha_popup.py` (já escrito no Task 3)

- [ ] **Step 1: Reescrever o branch não-área de `_disparar_armadilha`**

Texto atual a substituir (dentro de `_disparar_armadilha`):

```python
        if tipo.get("area"):
            await self._aplicar_armadilha_area(arm, tipo)
        else:
            save_ok, d20, sb, stot = self._testar_save(alvo, tipo["save"], tipo["dificuldade"])
            sb_str = f"+{sb}" if sb >= 0 else str(sb)
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20,
                                  "label": f"{alvo_nome} — {tipo['save']}"})
            await self.gm_say(f"🎲 Save {tipo['save']}: d20({d20}){sb_str}={stot} vs dif "
                              f"{tipo['dificuldade']} → {'evitou' if save_ok else 'falhou'}.")
            if not save_ok:
                for ef in tipo["efeitos"]:
                    await self._aplicar_efeito_armadilha(alvo, ef, arm)
            else:
                await self.gm_say(f"✅ **{alvo_nome}** evitou **{nome}** sem dano!")
```

Novo texto:

```python
        if tipo.get("area"):
            await self._aplicar_armadilha_area(arm, tipo)
        else:
            save_ok, d20, sb, stot = self._testar_save(alvo, tipo["save"], tipo["dificuldade"])
            sb_str = f"+{sb}" if sb >= 0 else str(sb)
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20,
                                  "label": f"{alvo_nome} — {tipo['save']}"})
            await self.gm_say(f"🎲 Save {tipo['save']}: d20({d20}){sb_str}={stot} vs dif "
                              f"{tipo['dificuldade']} → {'evitou' if save_ok else 'falhou'}.")
            if not save_ok:
                dano_total = 0
                efeitos_extra = []
                for ef in tipo["efeitos"]:
                    dano, texto = await self._aplicar_efeito_armadilha(alvo, ef, arm)
                    dano_total += dano
                    if texto:
                        efeitos_extra.append(texto)
                if dano_total:
                    efeitos_extra.insert(0, f"💥 Sofreu {dano_total} de dano")
                await self._enviar_trap_result(alvo, nome, tipo["icone"], sucesso=False,
                                                dano=dano_total, metade=False,
                                                descricao=tipo["descricao"], efeitos_extra=efeitos_extra)
            else:
                await self.gm_say(f"✅ **{alvo_nome}** evitou **{nome}** sem dano!")
                await self._enviar_trap_result(alvo, nome, tipo["icone"], sucesso=True,
                                                dano=0, metade=False,
                                                descricao=tipo["descricao"], efeitos_extra=[])
```

- [ ] **Step 2: Rodar o teste — Tasks 1-4 devem passar agora (cenários [1], [2], [2b])**

Run: `python tools/test_armadilha_popup.py`
Expected: `0 falharam` no resumo final (todos os cenários [1], [2] e [2b] passam —
não se preocupe com o número exato de "passaram", só confirme que `FAIL == 0`).

- [ ] **Step 3: Commit**

```bash
git add server.py
git commit -m "feat(armadilha): _disparar_armadilha envia popup trap_result"
```

---

## Task 5: `_aplicar_armadilha_area` envia popup por alvo (Mina/Nuvem de Gás)

**Files:**
- Modify: `server.py:10804-10826` (método `_aplicar_armadilha_area`)
- Test: `tools/test_armadilha_popup.py`

- [ ] **Step 1: Adicionar o cenário [3] ao teste (vai FALHAR — 0 popups ainda)**

```python
    # ── [3] Armadilha de área com save_reduz (Mina Terrestre) ───────────────────
    print("\n[3] Mina Terrestre (área) — 1 alvo falha, 1 resiste com metade")
    r = setup()
    p1 = make_player("p1", "A", "warrior", 0); p1["ref_"] = 0; p1["pos"] = [5, 5]
    p2 = make_player("p2", "B", "rogue", 1);   p2["ref_"] = 0; p2["pos"] = [6, 5]
    r.players = {"p1": p1, "p2": p2}
    arm = {"id": "m1", "tipo": "mina_terrestre", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    # dificuldade 12: p1 rola d20=2 (falha), p2 rola d20=18 (passa, mas save_reduz→metade)
    _o = server.random.randint; server.random.randint = fake_rng_seq([2, 18])
    await r._disparar_armadilha(p1, arm)
    server.random.randint = _o
    m1 = trap_msgs(r, "p1"); m2 = trap_msgs(r, "p2")
    check("p1 recebeu seu próprio popup", len(m1) == 1)
    check("p2 recebeu seu próprio popup", len(m2) == 1)
    check("p1 falhou: dano cheio (2d6 fixo em 3+3=6), metade=False",
          m1[0]["sucesso"] is False and m1[0]["metade"] is False and m1[0]["dano"] == 6)
    check("p2 resistiu: metade=True, ainda sofre dano reduzido (6→3)",
          m2[0]["sucesso"] is True and m2[0]["metade"] is True and m2[0]["dano"] == 3)
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_armadilha_popup.py`
Expected: "p1 recebeu seu próprio popup" e "p2 recebeu seu próprio popup" falham (0 mensagens).

- [ ] **Step 3: Reescrever `_aplicar_armadilha_area` em `server.py`**

Texto atual a substituir:

```python
    async def _aplicar_armadilha_area(self, arm, tipo):
        """Armadilhas de área (mina\gás): cada alvo no raio testa o próprio save."""
        cx, cy = arm["pos"]
        r = tipo.get("area", 1)
        alvos = [p for p in self.players.values()
                 if p["alive"] and abs(p["pos"][0]-cx) <= r and abs(p["pos"][1]-cy) <= r]
        alvos += [m for m in self.monsters.values()
                  if m["hp"] > 0 and abs(m["pos"][0]-cx) <= r and abs(m["pos"][1]-cy) <= r]
        pr = self.prisoner
        if pr and pr.get("alive") and pr.get("freed") \
                and abs(pr["pos"][0]-cx) <= r and abs(pr["pos"][1]-cy) <= r:
            alvos.append(pr)
        for alvo in alvos:
            alvo_nome = alvo.get("name") or alvo.get("nome", "Alvo")
            save_ok, d20, sb, stot = self._testar_save(alvo, tipo["save"], tipo["dificuldade"])
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20,
                                  "label": f"{alvo_nome} — {tipo['save']}"})
            if save_ok and not tipo.get("save_reduz"):
                await self.gm_say(f"✅ **{alvo_nome}** evitou **{tipo['nome']}**!")
                continue
            metade = bool(save_ok and tipo.get("save_reduz"))
            for ef in tipo["efeitos"]:
                await self._aplicar_efeito_armadilha(alvo, {**ef, "metade": metade}, arm)
```

Novo texto:

```python
    async def _aplicar_armadilha_area(self, arm, tipo):
        """Armadilhas de área (mina\gás): cada alvo no raio testa o próprio save."""
        cx, cy = arm["pos"]
        r = tipo.get("area", 1)
        alvos = [p for p in self.players.values()
                 if p["alive"] and abs(p["pos"][0]-cx) <= r and abs(p["pos"][1]-cy) <= r]
        alvos += [m for m in self.monsters.values()
                  if m["hp"] > 0 and abs(m["pos"][0]-cx) <= r and abs(m["pos"][1]-cy) <= r]
        pr = self.prisoner
        if pr and pr.get("alive") and pr.get("freed") \
                and abs(pr["pos"][0]-cx) <= r and abs(pr["pos"][1]-cy) <= r:
            alvos.append(pr)
        for alvo in alvos:
            alvo_nome = alvo.get("name") or alvo.get("nome", "Alvo")
            save_ok, d20, sb, stot = self._testar_save(alvo, tipo["save"], tipo["dificuldade"])
            await self.broadcast({"type": "dice_roll", "die": "d20", "value": d20,
                                  "label": f"{alvo_nome} — {tipo['save']}"})
            if save_ok and not tipo.get("save_reduz"):
                await self.gm_say(f"✅ **{alvo_nome}** evitou **{tipo['nome']}**!")
                await self._enviar_trap_result(alvo, tipo["nome"], tipo["icone"], sucesso=True,
                                                dano=0, metade=False, descricao=tipo["descricao"],
                                                efeitos_extra=[])
                continue
            metade = bool(save_ok and tipo.get("save_reduz"))
            dano_total = 0
            efeitos_extra = []
            for ef in tipo["efeitos"]:
                dano, texto = await self._aplicar_efeito_armadilha(alvo, {**ef, "metade": metade}, arm)
                dano_total += dano
                if texto:
                    efeitos_extra.append(texto)
            if dano_total:
                efeitos_extra.insert(0, f"💥 Sofreu {dano_total} de dano")
            await self._enviar_trap_result(alvo, tipo["nome"], tipo["icone"], sucesso=save_ok,
                                            dano=dano_total, metade=metade, descricao=tipo["descricao"],
                                            efeitos_extra=efeitos_extra)
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_armadilha_popup.py`
Expected: `0 falharam` no resumo final (cenário [3] passa também — não se preocupe
com o número exato de "passaram", só confirme que `FAIL == 0`).

- [ ] **Step 5: Commit**

```bash
git add server.py
git commit -m "feat(armadilha): _aplicar_armadilha_area envia popup por alvo atingido"
```

---

## Task 6: Tick de dano progressivo (Incendiária) envia popup

**Files:**
- Modify: `server.py:11162-11180` (método `_processar_efeitos_armadilha_turno`)
- Test: `tools/test_armadilha_popup.py`

- [ ] **Step 1: Adicionar o cenário [4] ao teste (vai FALHAR — sem popup de tick)**

```python
    # ── [4] Tick progressivo (Incendiária) ──────────────────────────────────────
    print("\n[4] Armadilha Incendiária — tick de dano progressivo")
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0); p["ref_"] = 0; r.players["p1"] = p
    arm = {"id": "i1", "tipo": "armadilha_incendiaria", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = fake_rng(1)   # falha o save inicial
    await r._disparar_armadilha(p, arm)
    server.random.randint = _o
    r.round_num += 1
    await r._processar_efeitos_armadilha_turno()
    msgs = trap_msgs(r, "p1")
    ticks = [m for m in msgs if m.get("tick")]
    check("disparo inicial gerou popup (tick=False)", msgs and msgs[0]["tick"] is False)
    check("dano progressivo gerou ao menos 1 popup de tick", len(ticks) >= 1)
    check("popup(s) de tick têm dano > 0", all(t["dano"] > 0 for t in ticks))
```

- [ ] **Step 2: Rodar e confirmar que falha**

Run: `python tools/test_armadilha_popup.py`
Expected: "dano progressivo gerou ao menos 1 popup de tick" falha (0 ticks).

- [ ] **Step 3: Reescrever `_processar_efeitos_armadilha_turno` em `server.py`**

Texto atual a substituir:

```python
    async def _processar_efeitos_armadilha_turno(self):
        """Tica o dano progressivo (incendiária) uma vez por rodada."""
        for arm in list(self.armadilhas):
            restantes = []
            for ef in arm.get("efeitos_ativos", []):
                aid = ef["alvo_id"]
                alvo = self.players.get(aid) or self.monsters.get(aid)
                if alvo is None and aid == "__prisioneiro__":
                    alvo = self.prisoner
                if alvo and (alvo.get("alive") or alvo.get("hp", 0) > 0):
                    dano = self._rolar_dado(ef["valor"])
                    await self._dano_em_alvo(alvo, dano, ef.get("elemento", "fogo"), arm.get("criador"))
                ef["rodadas_restantes"] -= 1
                if ef["rodadas_restantes"] > 0:
                    restantes.append(ef)
            arm["efeitos_ativos"] = restantes
        # Remove armadilhas gastas sem dano residual pendente.
        self.armadilhas = [a for a in self.armadilhas
                           if not (a.get("esgotada") and not a.get("efeitos_ativos"))]
```

Novo texto:

```python
    async def _processar_efeitos_armadilha_turno(self):
        """Tica o dano progressivo (incendiária) uma vez por rodada."""
        for arm in list(self.armadilhas):
            restantes = []
            tipo_meta = ARMADILHAS.get(arm["tipo"], {})
            for ef in arm.get("efeitos_ativos", []):
                aid = ef["alvo_id"]
                alvo = self.players.get(aid) or self.monsters.get(aid)
                if alvo is None and aid == "__prisioneiro__":
                    alvo = self.prisoner
                if alvo and (alvo.get("alive") or alvo.get("hp", 0) > 0):
                    dano = self._rolar_dado(ef["valor"])
                    await self._dano_em_alvo(alvo, dano, ef.get("elemento", "fogo"), arm.get("criador"))
                    await self._enviar_trap_result(
                        alvo, tipo_meta.get("nome", arm["tipo"]), tipo_meta.get("icone", "🔥"),
                        sucesso=False, dano=dano, metade=False,
                        descricao=f"A {tipo_meta.get('nome', 'armadilha')} continua causando dano.",
                        efeitos_extra=[], tick=True)
                ef["rodadas_restantes"] -= 1
                if ef["rodadas_restantes"] > 0:
                    restantes.append(ef)
            arm["efeitos_ativos"] = restantes
        # Remove armadilhas gastas sem dano residual pendente.
        self.armadilhas = [a for a in self.armadilhas
                           if not (a.get("esgotada") and not a.get("efeitos_ativos"))]
```

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `python tools/test_armadilha_popup.py`
Expected: `0 falharam` no resumo final (cenário [4] passa também — não se preocupe
com o número exato de "passaram", só confirme que `FAIL == 0`).

- [ ] **Step 5: Commit**

```bash
git add server.py
git commit -m "feat(armadilha): tick de dano progressivo envia popup (tick=True)"
```

---

## Task 7: Casos do prisioneiro e de monstro (roteamento, já cobertos pelo helper)

Esses dois cenários não exigem mudança de código adicional — servem pra
provar que o roteamento do `_enviar_trap_result` (Task 2) já cobre
corretamente o prisioneiro (vai pro `rescuer_pid`) e ignora monstros (sem
cliente).

**Files:**
- Test: `tools/test_armadilha_popup.py`

- [ ] **Step 1: Adicionar os cenários [5] e [6] ao teste**

```python
    # ── [5] Prisioneiro — popup vai pro resgatador ──────────────────────────────
    print("\n[5] Armadilha no prisioneiro — popup vai pro rescuer_pid")
    r = setup()
    rescuer = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = rescuer
    r.prisoner = {"pos": [5, 5], "alive": True, "freed": True, "rescuer_pid": "p1",
                  "name": "Prisioneiro", "hp": 7, "max_hp": 7}
    arm = {"id": "a4", "tipo": "armadilha_urso", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = fake_rng(1)
    await r._disparar_armadilha(r.prisoner, arm)
    server.random.randint = _o
    msgs = trap_msgs(r, "p1")
    check("popup do prisioneiro foi pro resgatador", len(msgs) == 1)

    # ── [6] Monstro pisando em armadilha — sem popup (sem cliente) ──────────────
    print("\n[6] Monstro na armadilha — nenhum popup enviado")
    r = setup()
    mob_def = next(m for m in MONSTER_DEFS if m["type"] == "urso_negro")
    mob = make_monster(mob_def, {"id": 1, "cx": 5, "cy": 5}); mob["pos"] = [5, 5]
    r.monsters[mob["id"]] = mob
    arm = {"id": "a5", "tipo": "armadilha_urso", "pos": [5, 5], "ativada": False}
    r.armadilhas = [arm]
    _o = server.random.randint; server.random.randint = fake_rng(1)
    await r._disparar_armadilha(mob, arm)
    server.random.randint = _o
    check("nenhuma mensagem trap_result enviada", trap_msgs(r) == [])
```

- [ ] **Step 2: Rodar e confirmar que TUDO passa (nenhuma mudança de código nesta task)**

Run: `python tools/test_armadilha_popup.py`
Expected: `0 falharam` no resumo final (todos os 6 cenários passam — não se preocupe
com o número exato de "passaram", só confirme que `FAIL == 0`).

- [ ] **Step 3: Commit**

```bash
git add tools/test_armadilha_popup.py
git commit -m "test(armadilha): cobre roteamento pro prisioneiro e ausência de popup em monstro"
```

---

## Task 8: Cliente — `src/gameState.js` repassa o evento `trap_result`

**Files:**
- Modify: `src/gameState.js:1040-1042`

- [ ] **Step 1: Adicionar o novo `case` logo após `case 'dice_roll':`**

Texto atual:

```javascript
      case 'dice_roll':
        _emit('diceRoll', msg);
        break;

      case 'animar_result':
```

Novo texto:

```javascript
      case 'dice_roll':
        _emit('diceRoll', msg);
        break;

      case 'trap_result':
        _emit('trapResult', msg);
        break;

      case 'animar_result':
```

- [ ] **Step 2: Verificar que não há erro de sintaxe**

Run: `node --check src/gameState.js`
Expected: sem saída (exit code 0).

- [ ] **Step 3: Commit**

```bash
git add src/gameState.js
git commit -m "feat(armadilha): gameState repassa o evento trap_result"
```

---

## Task 9: Cliente — HTML e CSS do popup (`game.js` / `game.css`)

**Files:**
- Modify: `game.js:203-211` (bloco HTML do template, logo após `#chest-overlay`)
- Modify: `game.css:373-375` (logo após `.chest-empty-msg`)

- [ ] **Step 1: Adicionar o HTML do overlay em `game.js`, logo após o fechamento de `#chest-overlay` e antes de `#tooltip`**

Texto atual:

```html
<!-- Chest Loot Window -->
<div id="chest-overlay">
  <div class="chest-box">
    <h3 id="chest-title">🎁 Baú de Tesouro</h3>
    <div class="chest-subtitle" id="chest-subtitle">Aproxime-se do baú para coletar</div>
    <div id="chest-items-list"></div>
    <button class="btn-cancel" style="margin-top:10px" onclick="closeChestWindow()">Fechar</button>
  </div>
</div>

<div id="tooltip"></div>
```

Novo texto:

```html
<!-- Chest Loot Window -->
<div id="chest-overlay">
  <div class="chest-box">
    <h3 id="chest-title">🎁 Baú de Tesouro</h3>
    <div class="chest-subtitle" id="chest-subtitle">Aproxime-se do baú para coletar</div>
    <div id="chest-items-list"></div>
    <button class="btn-cancel" style="margin-top:10px" onclick="closeChestWindow()">Fechar</button>
  </div>
</div>

<!-- Trap Result Popup -->
<div id="trap-overlay">
  <div class="trap-box">
    <div class="trap-icon" id="trap-icon">🪤</div>
    <h3 id="trap-title">Armadilha</h3>
    <div class="trap-status" id="trap-status"></div>
    <p class="trap-desc" id="trap-desc"></p>
    <ul class="trap-effects" id="trap-effects"></ul>
    <button class="btn-cancel" onclick="closeTrapWindow()">Fechar</button>
  </div>
</div>

<div id="tooltip"></div>
```

- [ ] **Step 2: Adicionar o CSS em `game.css`, logo após `.chest-empty-msg` e antes do comentário `/* GM LOG ... */`**

Texto atual:

```css
.chest-empty-msg { text-align: center; color: var(--text2); font-size: .82rem; padding: 14px 0; }

/* GM LOG — lives at the bottom of #map-panel */
```

Novo texto:

```css
.chest-empty-msg { text-align: center; color: var(--text2); font-size: .82rem; padding: 14px 0; }

/* Trap result popup — tema de perigo, distinto do dourado do baú */
#trap-overlay { position: fixed; inset: 0; background: #000c; display: none;
                align-items: center; justify-content: center; z-index: 120; }
#trap-overlay.open { display: flex; }
.trap-box { background: var(--bg2); border: 2px solid var(--red); border-radius: 12px;
             padding: 20px 24px; min-width: 300px; max-width: 420px; text-align: center; }
.trap-icon { font-size: 2.4rem; line-height: 1; margin-bottom: 4px; }
.trap-box h3 { color: var(--text); margin: 0 0 8px; font-size: 1.05rem; }
.trap-status { font-size: .95rem; font-weight: bold; padding: 6px 10px; border-radius: var(--radius);
                margin-bottom: 10px; }
.trap-status--success { color: var(--green); background: #113a20; }
.trap-status--partial { color: #f39c12; background: #3a2a08; }
.trap-status--fail { color: var(--red); background: #3a1414; }
.trap-status--tick { color: #e67e22; background: #3a2408; }
.trap-desc { font-size: .82rem; color: var(--text2); margin: 0 0 10px; text-align: left; }
.trap-effects { list-style: none; padding: 0; margin: 0 0 6px; text-align: left; }
.trap-effects li { font-size: .82rem; padding: 4px 8px; background: var(--bg3);
                    border-radius: var(--radius); margin-bottom: 5px; }

/* GM LOG — lives at the bottom of #map-panel */
```

- [ ] **Step 3: Commit**

```bash
git add game.js game.css
git commit -m "feat(armadilha): HTML e CSS do popup de resultado de armadilha"
```

---

## Task 10: Cliente — lógica do popup em `game.js` (fila, som, fechar)

**Files:**
- Modify: `game.js` (novas funções, logo após `abrirPainelLoot`, ~linha 10509, antes do comentário `// ── Histórico de rolagens ...`)
- Modify: `game.js` (novo `GS.on('trapResult', ...)`, logo após `GS.on('diceRoll', ...)`, ~linha 20107)

- [ ] **Step 1: Adicionar as funções do popup em `game.js`, logo após o fim de `abrirPainelLoot` (a chave `}` que fecha a função, seguida da linha em branco antes de `// ── Histórico de rolagens`)**

Texto atual (fim de `abrirPainelLoot` seguido do comentário do histórico):

```javascript
  $('chest-overlay').classList.add('open');
}

// ── Histórico de rolagens — faixa fixa sob o cabeçalho do log do Mestre ─────
```

Novo texto:

```javascript
  $('chest-overlay').classList.add('open');
}

// ── Popup de resultado de armadilha ─────────────────────────────────────────
// Fila simples: se um novo trap_result chegar com o popup atual aberto/agendado,
// entra na fila e aparece em sequência (caso raro: 2 armadilhas na mesma casa
// andada — o buraco procedural + uma colocável sobrepostos).
const _trapQueue = [];
let _trapShowTimer = null;

function queueTrapResult(msg){
  _trapQueue.push(msg);
  if(_trapShowTimer) return;   // já tem um agendado/aberto
  _trapShowTimer = setTimeout(_advanceTrapQueue, 1200);
}

function _advanceTrapQueue(){
  _trapShowTimer = null;
  const msg = _trapQueue.shift();
  if(!msg) return;
  _showTrapResult(msg);
}

function _showTrapResult(msg){
  $('trap-icon').textContent = msg.icone || '🪤';
  $('trap-title').textContent = msg.nome || 'Armadilha';
  $('trap-desc').textContent = msg.descricao || '';

  const effectsEl = $('trap-effects');
  effectsEl.innerHTML = '';
  (msg.efeitos_extra || []).forEach(txt => {
    const li = document.createElement('li');
    li.textContent = txt;
    effectsEl.appendChild(li);
  });

  const statusEl = $('trap-status');
  if(msg.tick){
    statusEl.className = 'trap-status trap-status--tick';
    statusEl.textContent = `🔥 Dano contínuo: ${msg.dano}`;
  } else if(msg.metade){
    statusEl.className = 'trap-status trap-status--partial';
    statusEl.textContent = '🟡 Você resistiu parcialmente!';
  } else if(msg.sucesso){
    statusEl.className = 'trap-status trap-status--success';
    statusEl.textContent = '✅ Você escapou!';
  } else {
    statusEl.className = 'trap-status trap-status--fail';
    statusEl.textContent = '❌ Você foi atingido!';
    tocarSomArmadilha();
  }

  $('trap-overlay').classList.add('open');
}

function closeTrapWindow(){
  $('trap-overlay').classList.remove('open');
  if(_trapQueue.length) _trapShowTimer = setTimeout(_advanceTrapQueue, 300);
}

// Clique fora da caixa fecha o popup (só se o clique foi no fundo, não na caixa).
$('trap-overlay').addEventListener('click', e => {
  if(e.target.id === 'trap-overlay') closeTrapWindow();
});

// Esc fecha o popup se estiver aberto.
document.addEventListener('keydown', e => {
  if(e.key === 'Escape' && $('trap-overlay').classList.contains('open')) closeTrapWindow();
});

// Som curto de impacto ao FALHAR numa armadilha (grave/dissonante). Sucesso e
// resultado parcial não têm som dedicado — o som do dado já cobre o momento.
function tocarSomArmadilha(){
  const ctx = getAudioContext();
  if(!ctx || ctx.state !== 'running') return;
  try{
    const now = ctx.currentTime;
    [196.00, 146.83].forEach((f, i) => {   // G3 → D3, dissonante e grave
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = 'sawtooth';
      o.frequency.value = f;
      const t0 = now + i * 0.09;
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(0.22, t0 + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.45);
      o.connect(g); g.connect(_sfxBus());
      o.start(t0); o.stop(t0 + 0.5);
    });
  } catch(e){}
}

// ── Histórico de rolagens — faixa fixa sob o cabeçalho do log do Mestre ─────
```

- [ ] **Step 2: Registrar o listener do evento, logo após `GS.on('diceRoll', ...)`**

Texto atual:

```javascript
GS.on('diceRoll',    msg  => { handleDiceRoll(msg); updateDiceHistory(msg); });
```

Novo texto:

```javascript
GS.on('diceRoll',    msg  => { handleDiceRoll(msg); updateDiceHistory(msg); });

GS.on('trapResult',  msg  => queueTrapResult(msg));
```

- [ ] **Step 3: Verificar que não há erro de sintaxe**

Run: `node --check game.js`
Expected: sem saída (exit code 0).

- [ ] **Step 4: Commit**

```bash
git add game.js
git commit -m "feat(armadilha): fila, som e fechamento do popup de resultado de armadilha"
```

---

## Task 11: Documentar em `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md` (tabela Server → Client + novo parágrafo)

- [ ] **Step 1: Adicionar `trap_result` na lista de mensagens Server → Client**

Texto atual:

```markdown
`game_state`, `gm_narration`, `game_over`, `dice_roll`, `animar_result`, `error`,
`decor_loot`
```

Novo texto:

```markdown
`game_state`, `gm_narration`, `game_over`, `dice_roll`, `animar_result`, `error`,
`decor_loot`, `trap_result`
```

- [ ] **Step 2: Adicionar um parágrafo explicando a feature, logo após o parágrafo do `animar_result` (antes de "**História (slides):**")**

Texto atual:

```markdown
> `game_state` inclui `corpses` (cadáveres) e `armadilhas` (colocáveis — ver
> abaixo). `animar_result` traz
> `resultado`/`rolagem`/`d10_dezena`/`d10_unidade`/`chance`/`zona_hostil`/`animados`.

> **História (slides):**
```

Novo texto:

```markdown
> `game_state` inclui `corpses` (cadáveres) e `armadilhas` (colocáveis — ver
> abaixo). `animar_result` traz
> `resultado`/`rolagem`/`d10_dezena`/`d10_unidade`/`chance`/`zona_hostil`/`animados`.

> **Popup de resultado de armadilha:** ao cair numa armadilha (buraco
> procedural genérico de `self.traps` ou qualquer uma das 8 do catálogo
> `ARMADILHAS`), o servidor manda `trap_result` (`send_to`, nunca broadcast —
> só quem foi afetado recebe) com `nome`/`icone`/`sucesso`/`dano`/`metade`/
> `descricao`/`efeitos_extra`/`tick`. Disparado em 4 pontos:
> `_verificar_trap_procedural` (buraco de sala), `_disparar_armadilha`
> (armadilha de 1 alvo), `_aplicar_armadilha_area` (Mina Terrestre/Nuvem de
> Gás — cada alvo atingido recebe o seu), e `_processar_efeitos_armadilha_turno`
> (tick de dano progressivo da Incendiária, com `tick:true`). Roteamento vai
> pro próprio jogador, ou pro `rescuer_pid` se o alvo for o prisioneiro
> (monstros/servos animados não recebem — sem cliente). Cliente: `game.js`
> abre `#trap-overlay` ~1,2s depois do evento (dá tempo da animação do dado
> terminar), com fila simples pra disparos simultâneos; fecha por botão, clique
> fora, ou Esc; tema de perigo (borda vermelha), com som curto só na falha.

> **História (slides):**
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: documenta a mensagem trap_result no protocolo WebSocket"
```

---

## Task 12: Rodar a suíte completa e checklist manual final

**Files:** nenhum (verificação)

- [ ] **Step 1: Rodar o teste novo isoladamente**

Run: `python tools/test_armadilha_popup.py`
Expected: `0 falharam` no resumo final (todos os 6 cenários passam — não se preocupe
com o número exato de "passaram", só confirme que `FAIL == 0`).

- [ ] **Step 2: Rodar a suíte de regressão existente que toca em armadilhas/devorador (garante que nada quebrou)**

Run: `python tools/test_devorador.py`
Expected: `FAIL == 0` no resumo final (a suíte já cobre corrosão/monstros e não
deveria ter sido afetada por essa mudança, mas roda rápido e serve de rede de
segurança).

- [ ] **Step 3: Checklist manual (jogo real — não automatizável por ser um servidor WebSocket multiplayer)**

Suba o servidor (`iniciar.bat` ou `python server.py`, depois abra
`http://localhost:8765/index.html` em 1 aba) e verifique:

- [ ] Entrar numa masmorra com uma sala do tipo `trap` (procedural) ou uma
      armadilha colocada pelo Luccas/editor; andar sobre ela.
- [ ] Popup aparece ~1-2s depois da animação do dado, com nome/ícone corretos.
- [ ] Falhar no save: banner vermelho, descrição, linha de dano (e/ou
      efeito, ex. "Perdeu o movimento").
- [ ] Passar no save (armadilha sem `save_reduz`): banner verde, sem dano.
- [ ] Mina Terrestre/Nuvem de Gás com 2 jogadores próximos: cada um vê seu
      próprio popup (o outro jogador NÃO vê popup do parceiro).
- [ ] Fechar por: botão "Fechar", clique fora da caixa, tecla Esc — todos
      funcionam.
- [ ] Som de impacto toca só na falha; nenhum som extra no sucesso.
- [ ] Se 2 armadilhas disparam na mesma casa andada, o 2º popup aparece
      em sequência após fechar o 1º (fila).

- [ ] **Step 4: Commit final (se algum ajuste manual foi necessário) ou encerrar**

```bash
git status
```

Se tudo já foi commitado nas tasks anteriores, não há nada a fazer aqui —
esse step é só a rede de segurança final antes de considerar a feature
completa.
