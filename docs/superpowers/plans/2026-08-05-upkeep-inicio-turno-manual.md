# Upkeep de Início de Turno no Modo Manual — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer o monstro sob controle do mestre passar pelo mesmo upkeep de início de turno que o monstro da IA já sofre, acabando com a imunidade dele a veneno, Réquiem e a todo o controle de multidão.

**Architecture:** O bloco de upkeep da `gm_phase` é um prólogo coeso que termina decidindo se o monstro age. Ele é extraído inteiro para `_upkeep_inicio_turno_monstro(m, alive_monsters) -> bool`, chamado pela `gm_phase` (que faz `continue` no `False`) e pelo `_master_manual_window` (que retorna sem abrir a janela). Extração pura, ordem preservada: a IA fica byte-idêntica.

**Tech Stack:** Python 3 + `websockets` (server.py, arquivo único, classe `GameRoom`). Testes: `python tools/test_modo_mestre.py` (harness próprio, sem pytest).

**Spec:** `docs/superpowers/specs/2026-08-05-upkeep-inicio-turno-manual-design.md`

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta mudança |
|---|---|
| `server.py` | Novo `_upkeep_inicio_turno_monstro`; `gm_phase` e `_master_manual_window` passam a chamá-lo |
| `tools/test_modo_mestre.py` | Seções `[37]`, `[38]`, `[39]` |

Sem arquivo novo: `server.py` é grande por convenção do projeto e o código pertence à região do Modo Mestre que já existe.

---

## Invariante

**Sem mestre, ou com o monstro em `auto`, o comportamento tem de ser byte-idêntico.** É extração pura: mesma ordem, mesmas chamadas, `continue` virando `return False`. A Task 1 testa isso explicitamente.

**Estado atual da suíte: 272 passaram, 0 falharam.** O arquivo de teste vai até a seção `[36c]`.

---

## Task 1: Extrair o prólogo e religar a `gm_phase`

**Files:**
- Modify: `server.py` — novo método + `gm_phase` (bloco atual nas linhas 23038-23076)
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `tools/test_modo_mestre.py`, imediatamente antes da linha `print(f"\n=== {PASS} passaram, {FAIL} falharam ===")`:

```python
    print("\n[37] _upkeep_inicio_turno_monstro — devolve se o monstro pode agir")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    # Os processadores de efeito são neutralizados aqui de propósito: esta seção
    # testa a RAMIFICAÇÃO do prólogo (age × perde o turno), não o que cada efeito
    # faz. Sem os stubs, um dict de monstro mínimo pode estourar dentro deles por
    # falta de campos. A seção [39] prova que eles são de fato chamados.
    async def _noop(*a, **k): pass
    r._processar_mare_viva_turno = _noop
    r._processar_venenos_turno = _noop
    r._processar_mods_magia_turno = _noop
    r._processar_requiem_turno = _noop
    async def _sem_status(mm, vivos): return None
    r._status_monstro_turno = _sem_status
    async def _sem_enredo(mm): return False
    r._processar_enredado_turno = _sem_enredo
    def _mon(**kw):
        base = {"id": "g1", "name": "Coisa", "type": "goblin", "hp": 10, "max_hp": 10,
                "pos": [2, 2], "size": [1, 1], "movement": 4}
        base.update(kw); return base
    # saudável → pode agir
    m = _mon()
    check("monstro saudável pode agir", await r._upkeep_inicio_turno_monstro(m, [m]) is True)
    # petrificado → perde o turno
    m = _mon(petrificado=True)
    check("petrificado perde o turno", await r._upkeep_inicio_turno_monstro(m, [m]) is False)
    # preso em rede → perde o turno e o flag é consumido
    m = _mon(perde_turno=True)
    check("rede perde o turno", await r._upkeep_inicio_turno_monstro(m, [m]) is False)
    check("rede consome o flag", m["perde_turno"] is False)
    # inabalavel ignora a rede
    m = _mon(perde_turno=True, special_abilities=[{"id": "inabalavel", "action_type": "passiva"}])
    check("inabalavel ignora a rede", await r._upkeep_inicio_turno_monstro(m, [m]) is True)
    check("inabalavel limpa o flag", "perde_turno" not in m)
    # morto durante o upkeep → não age
    m = _mon(hp=0)
    check("monstro morto não age", await r._upkeep_inicio_turno_monstro(m, [m]) is False)

    print("\n[37b] lobisomem regenera dentro do prólogo")
    # Mesmos stubs de [37] seguem valendo: a regeneração é inline no prólogo.
    m = _mon(type="lobisomem", hp=8, max_hp=30)
    check("regenerou +2", (await r._upkeep_inicio_turno_monstro(m, [m])) is True and m["hp"] == 10)
    check("fúria abaixo de 12 PV", m.get("furia_lobisomem") is True)
    m = _mon(type="lobisomem", hp=8, max_hp=30, regeneracao_bloqueada=True)
    await r._upkeep_inicio_turno_monstro(m, [m])
    check("regeneração bloqueada não cura", m["hp"] == 8)
    check("bloqueio é consumido", "regeneracao_bloqueada" not in m)
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA com `AttributeError: 'GameRoom' object has no attribute '_upkeep_inicio_turno_monstro'`

- [ ] **Step 3: Implementar**

Em `server.py`, adicionar o método logo **antes** de `async def gm_phase(self, only_monster=None):`:

```python
    async def _upkeep_inicio_turno_monstro(self, m, alive_monsters):
        """Prólogo de início de turno do monstro: efeitos que ticam/expiram e os
        estados que fazem PERDER o turno. Retorna True se o monstro ainda pode
        agir, False se o turno foi consumido.

        Ponto único usado pela gm_phase (IA) e pela janela do Manual (mestre) —
        sem isso o monstro do mestre ficava imune a veneno, Réquiem e a todo o
        controle de multidão, por não passar pela gm_phase.

        A ordem é a mesma de sempre; era um bloco inline com `continue`, que
        virou `return False`."""
        await self._processar_mare_viva_turno(m)
        # Venenos: tica/expira efeitos no início do turno do monstro.
        await self._processar_venenos_turno(m)
        await self._processar_mods_magia_turno(m)   # Amaldiçoar expira por rodada
        if m.get("type") == "lobisomem":
            if not m.pop("regeneracao_bloqueada", False):
                m["hp"] = min(m.get("max_hp", m["hp"]), m["hp"] + 2)
            if m.get("hp", 0) <= 12:
                m["furia_lobisomem"] = True
        if m["hp"] <= 0:
            return False
        # Réquiem Final (Violino): dano crescente no início do turno do alvo.
        await self._processar_requiem_turno(m)
        if m["hp"] <= 0:
            return False
        # Petrificado: perde o turno (não move nem ataca).
        if m.get("petrificado"):
            await self.gm_say(f"🗿 **{m['name']}** está petrificado e perde o turno!")
            return False
        # Paralisado (Raio Congelante): novo Fortitude; se falhar, perde o turno.
        if m.get("paralisado"):
            if await self._processar_paralisacao_turno(m):
                return False
        if m.get("perde_turno"):
            if self._tem_habilidade(m, "inabalavel"):
                m.pop("perde_turno", None)
            else:
                m["perde_turno"] = False
                await self.gm_say(f"🕸️ **{m['name']}** está preso (rede) e perde o turno!")
                return False
        # Enredado (Rede): gasta o turno tentando escapar. (Enquanto preso, o
        # tick de mov_reduzido/Cola fica em pausa — o monstro nem se move.)
        if m.get("enredado") and self._tem_habilidade(m, "inabalavel"):
            m.pop("enredado", None); m.pop("enredado_save", None); m.pop("enredado_cd", None)
        elif await self._processar_enredado_turno(m):
            return False
        # Status de magia (Sono/Comando/Dominar/Medo/Lentidão): pode consumir o turno.
        if await self._status_monstro_turno(m, alive_monsters) == "pulou":
            return False
        return True
```

Em `gm_phase`, apagar as linhas 23038 a 23076 (do `await self._processar_mare_viva_turno(m)` até o `continue` do `_status_monstro_turno`) e pôr no lugar:

```python
            if not await self._upkeep_inicio_turno_monstro(m, alive_monsters):
                continue
```

A linha imediatamente seguinte, `targets = self._alvos_visiveis_para_monstro(m, _targets())`, fica intocada.

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: seções `[37]`/`[37b]` verdes, total 272 → 283 passaram, 0 falharam.

- [ ] **Step 5: Rodar as suítes vizinhas para provar a byte-identidade da IA**

Run: `python tools/test_bugbear.py`
Run: `python tools/test_ogro.py`
Run: `python tools/test_agua.py`

Expected: os mesmos resultados de antes da mudança. Estas suítes exercitam a IA dos monstros e são a prova real de que a extração não mexeu no comportamento. **Falhas pré-existentes conhecidas em `test_bugbear` e `test_ogro` não contam** — compare com o HEAD anterior (`git stash` ou `git show HEAD:server.py`) antes de culpar esta mudança, e diga no relatório o que encontrou.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "refactor(monstros): extrai _upkeep_inicio_turno_monstro da gm_phase"
```

---

## Task 2: A janela Manual passa pelo prólogo

**Files:**
- Modify: `server.py` — `_master_manual_window`
- Test: `tools/test_modo_mestre.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar antes da linha de totais:

```python
    print("\n[38] turno perdido não abre a janela do Manual")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    # Petrificado: a janela retorna na hora, sem abrir.
    m = {"id": "g1", "name": "Estátua", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "petrificado": True}
    r.monsters = {"g1": m}
    await r._master_manual_window(m)          # não bloqueia: o turno foi consumido
    check("não setou master_manual_mid", r.master_manual_mid is None)
    check("não criou a janela", r.master_manual_event is None)
    check("não montou cargas de ataque", "master_attack_charges" not in m)

    print("\n[38b] monstro são abre a janela normalmente")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    check("abriu a janela", r.master_manual_mid == "g1")
    check("montou cargas", m.get("master_attack_charges") == {0: 1})
    r.master_manual_event.set()
    await task
```

> `r.master_manual_event` começa `None` num `GameRoom` recém-criado, por isso a
> checagem "não criou a janela" é significativa. Se a janela tivesse aberto, o
> `await` do passo anterior travaria o teste — o próprio fato de o teste terminar
> já é parte da prova.

Acrescente também esta checagem ao fim de `[38b]`, provando o argumento `[m]`:

```python
    print("\n[38c] a janela passa [m] como alive_monsters, igual à gm_phase(monster)")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    visto = {}
    async def espiao(mm, vivos): visto["vivos"] = vivos; return None
    r._status_monstro_turno = espiao
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    outro = {"id": "g2", "name": "Outro", "type": "goblin", "hp": 10, "max_hp": 10,
             "pos": [8, 8], "size": [1, 1], "movement": 4}
    r.monsters = {"g1": m, "g2": outro}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    check("recebeu só o próprio monstro", visto.get("vivos") == [m])
    r.master_manual_event.set()
    await task
```

- [ ] **Step 2: Rodar o teste e ver falhar**

Run: `python tools/test_modo_mestre.py`
Expected: FALHA — hoje a janela abre para qualquer monstro, então "não setou master_manual_mid" falha; e o teste pode travar no `await`, o que também é falha (interrompa com Ctrl+C se travar e trate como vermelho).

- [ ] **Step 3: Implementar**

Em `server.py`, em `_master_manual_window`, inserir no **topo do método**, antes da linha `self.master_manual_mid = m["id"]`:

```python
        # O monstro do mestre passa pelo MESMO prólogo de início de turno da IA:
        # veneno, Réquiem, petrificação, paralisia, rede, enredado, sono/medo.
        # Se o turno foi consumido, não abre janela — `monster_step` chama
        # `_advance_initiative()` logo depois, então a iniciativa segue sozinha.
        # O 2º argumento é `[m]` de propósito: no laço de iniciativa a IA entra
        # por `gm_phase(monster)`, que monta `alive_monsters = [monster]`. Passar
        # a lista inteira daria ao Manual um comportamento diferente no caso do
        # monstro Dominado, que usa essa lista para escolher em quem bater.
        if not await self._upkeep_inicio_turno_monstro(m, [m]):
            return
```

Nada mais no método muda. Repare que `_upkeep_inicio_turno_manual(m)` — expiração do ocultamento e tique das recargas, da Task 7 do plano da ficha — já fica depois disso no corpo do método, então ele só roda quando o prólogo passou. É exatamente a paridade exigida: sob a IA, um monstro que perde o turno também não tica recarga, porque o tique vive dentro das rotinas de IA por espécie.

- [ ] **Step 4: Rodar o teste e ver passar**

Run: `python tools/test_modo_mestre.py`
Expected: `[38]`/`[38b]`/`[38c]` verdes, total 283 → 289 passaram, 0 falharam.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_modo_mestre.py
git commit -m "fix(mestre): monstro em Manual passa pelo upkeep de inicio de turno"
```

---

## Task 3: Provas de efeito e de paridade

**Files:**
- Test: `tools/test_modo_mestre.py`

Esta task não muda produção — trava o comportamento que as Tasks 1 e 2 destravaram.

- [ ] **Step 1: Escrever os testes**

Adicionar antes da linha de totais:

```python
    print("\n[39] veneno e Réquiem alcançam o monstro do mestre")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    ticou = {"veneno": 0, "requiem": 0}
    async def fake_veneno(mm): ticou["veneno"] += 1
    async def fake_requiem(mm): ticou["requiem"] += 1
    r._processar_venenos_turno = fake_veneno
    r._processar_requiem_turno = fake_requiem
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}]}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    check("veneno ticou no Manual", ticou["veneno"] == 1)
    check("Réquiem ticou no Manual", ticou["requiem"] == 1)
    r.master_manual_event.set()
    await task

    print("\n[39b] paridade: recarga NÃO anda no turno perdido")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    m = {"id": "g1", "name": "Estátua", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "petrificado": True,
         "ability_cooldowns": {"golpe_brutal": 3},
         "monster_ability_cooldowns": {"hero_warrior_mira_certeira": 2}}
    r.monsters = {"g1": m}
    await r._master_manual_window(m)
    check("ability_cooldowns intacto no turno perdido", m["ability_cooldowns"]["golpe_brutal"] == 3)
    check("monster_ability_cooldowns intacto", m["monster_ability_cooldowns"]["hero_warrior_mira_certeira"] == 2)

    print("\n[39c] recarga anda no turno normal (não regrediu)")
    r = playing_room_com_mestre()
    r.players = {"hA": {"id": "hA", "name": "Vic", "pos": [5, 5], "alive": True, "hp": 10}}
    m = {"id": "g1", "name": "Orc", "type": "goblin", "hp": 10, "max_hp": 10,
         "pos": [2, 2], "size": [1, 1], "movement": 4, "control_mode": "manual",
         "attacks": [{"name": "Machado", "num_attacks": 1}],
         "ability_cooldowns": {"golpe_brutal": 3}}
    r.monsters = {"g1": m}
    task = asyncio.create_task(r._master_manual_window(m))
    await asyncio.sleep(0)
    check("recarga andou no turno normal", m["ability_cooldowns"]["golpe_brutal"] == 2)
    r.master_manual_event.set()
    await task
```

- [ ] **Step 2: Rodar e ver passar direto**

Run: `python tools/test_modo_mestre.py`
Expected: `[39]`/`[39b]`/`[39c]` verdes, total 288 → 295 passaram, 0 falharam.

Se `[39b]` falhar, a ordem dentro de `_master_manual_window` está errada: o prólogo tem de vir **antes** de `_upkeep_inicio_turno_manual`. Conserte a ordem, não o teste.

- [ ] **Step 3: Commit**

```bash
git add tools/test_modo_mestre.py
git commit -m "test(mestre): veneno/Requiem no Manual e paridade de recarga"
```

---

## Task 4: Verificação final

**Files:** nenhum — verificação.

- [ ] **Step 1: Suíte do Modo Mestre**

Run: `python tools/test_modo_mestre.py`
Expected: `=== 295 passaram, 0 falharam ===`

- [ ] **Step 2: Suítes que exercitam a IA dos monstros**

```bash
python tools/test_bugbear.py && python tools/test_ogro.py && python tools/test_agua.py && python tools/test_devorador.py
```

Expected: mesmos resultados do HEAD anterior à Task 1. Falhas pré-existentes conhecidas (`test_bugbear`, `test_ogro`, e `test_devorador` que é intermitente) **não** contam como regressão — confirme contra o HEAD antes de reportar qualquer uma.

- [ ] **Step 3: Smoke in-app com dois navegadores**

Subir o servidor, abrir `http://localhost:8765/index.html` em duas janelas, uma como herói e outra como Mestre. Marcar cada item:

- [ ] Um monstro em Manual envenenado perde PV no início do turno dele.
- [ ] Um monstro em Manual petrificado **não** abre a janela do mestre e a iniciativa passa direto.
- [ ] Um monstro em Manual paralisado faz o teste de Fortitude e, ao falhar, perde o turno.
- [ ] Um monstro em Manual preso na rede perde o turno uma vez e volta a agir depois.
- [ ] A narração do turno perdido aparece para o mestre e para os heróis.
- [ ] Um monstro em `auto` continua se comportando como antes.

---

## Ordem e dependências

Task 1 → Task 2 → Task 3 → Task 4, em ordem. A Task 2 depende do método criado na Task 1; a Task 3 depende da ordem estabelecida na Task 2.
