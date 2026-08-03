# Maldições Fase A — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fazer 6 maldições do catálogo saírem do inerte, migrar as 3 numéricas já existentes para uma camada declarativa, e consertar as penalidades de veneno que o servidor grava no jogador e ninguém lê.

**Architecture:** Cada entrada de `MALDICOES` ganha um dicionário opcional `mods` (`{"ataque": -2}`, `{"visao": -2}`…); um helper único `_maldicao_mod(p, chave)` soma o que estiver ativo, e cinco pontos de cálculo passam a consultá-lo. As maldições que não são um número somado (Aura Profana, Fortuna Roubada, Azar Sobrenatural) têm gancho próprio. As leituras novas caem em **funis únicos** já existentes — `_player_effective_ac` e `_resolver_dano_ataque_basico` — que é onde as penalidades de veneno inertes também passam a ser lidas.

**Tech Stack:** Python 3 + `websockets` (server.py, sem framework). Testes são scripts Python que rodam da raiz e imprimem ✅/❌, saindo com código 1 se algo falhar.

**Spec:** `docs/superpowers/specs/2026-07-31-maldicoes-fase-a-design.md`

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta entrega |
|---|---|
| `server.py` | catálogo `mods`, `_maldicao_mod`, 5 pontos de leitura, 3 ganchos comportamentais, helper `_ganhar_ouro` |
| `tools/test_maldicoes.py` | cresce de 38 para ~70 checks |

**Convenções que valem aqui:**
- Testes rodam da raiz: `python tools/test_maldicoes.py`.
- Commits em português, prefixo `feat(maldicoes)` / `fix(maldicoes)` / `refactor(maldicoes)`.
- **O usuário edita `server.py` em paralelo.** Rodar `git status` e `git diff server.py` antes de cada `git add`; conferir que todo hunk é seu. Se houver WIP dele misturado, montar o blob a partir de `git show HEAD:server.py` mais suas edições, gravar com `git hash-object -w --path server.py` e stagear com `git update-index --cacheinfo`, **sem mutar o working tree**. Nunca `git add -A`, `git add .` ou `git add -u`.

---

## Task 1: Camada declarativa e migração das três existentes

**Files:**
- Modify: `server.py` — dicionário `MALDICOES`, `handle_attack` (`eff_atk`), `_moves_base`, `_testar_save`
- Test: `tools/test_maldicoes.py`

Esta task é uma **refatoração sob rede de proteção**, não uma feature. Os testes são de caracterização: passam ANTES e DEPOIS. Se algum mudar de resultado, a migração quebrou algo.

- [ ] **Step 1: Escrever os testes de caracterização**

Adicionar em `tools/test_maldicoes.py`, antes de `def main():`

```python
def test_camada_declarativa():
    print("\n[11] Camada declarativa — os três números não mudam")
    # Caracterização: estes valores valem hoje (checagens hardcoded) e têm de
    # continuar valendo depois da migração para MALDICOES[...]["mods"].
    r, p = sala()
    r.round_num = 1
    mov0 = r._moves_base(p)
    asyncio.run(r._aplicar_maldicao(p, "correntes_invisiveis"))
    check("Correntes Invisíveis: -3 de movimento", r._moves_base(p) == mov0 - 3)

    # Vontade: _testar_save devolve (passou, d20, bonus, total) — compara o
    # `bonus`, que é determinístico, em vez do d20.
    r2, p2 = sala()
    base = r2._testar_save(p2, "vontade", 99)[2]
    asyncio.run(r2._aplicar_maldicao(p2, "espirito_covarde"))
    check("Espírito Covarde: -2 em Vontade",
          r2._testar_save(p2, "vontade", 99)[2] == base - 2)

    r3, p3 = sala()
    check("sem maldição, o modificador é 0", r3._maldicao_mod(p3, "ataque") == 0)
    asyncio.run(r3._aplicar_maldicao(p3, "maos_tremulas"))
    check("Mãos Trêmulas: -2 de ataque", r3._maldicao_mod(p3, "ataque") == -2)
    asyncio.run(r3._aplicar_maldicao(p3, "correntes_invisiveis"))
    check("chaves diferentes não se misturam",
          r3._maldicao_mod(p3, "ataque") == -2 and r3._maldicao_mod(p3, "movimento") == -3)
    check("chave sem ninguém devolve 0", r3._maldicao_mod(p3, "visao") == 0)
```

E registrar em `main()`, na lista de chamadas:

```python
    test_camada_declarativa()
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_maldicao_mod'`.

- [ ] **Step 3: Acrescentar `mods` ao catálogo**

No dicionário `MALDICOES` (server.py, perto da linha 700), acrescentar o campo às três já implementadas:

```python
    "maos_tremulas": {"nome":"Mãos Trêmulas","categoria":"leve","desc":"-2 em ataques",
                      "mods":{"ataque":-2}},
    "correntes_invisiveis": {"nome":"Correntes Invisíveis","categoria":"media","desc":"-3 movimento",
                             "mods":{"movimento":-3}},
    "espirito_covarde": {"nome":"Espírito Covarde","categoria":"grave","desc":"-2 Vontade; falha contra medo",
                         "mods":{"vontade":-2}},
```

Logo abaixo da declaração de `MALDICAO_MAX_POR_HEROI`, documentar as chaves:

```python
# Chaves de `mods` lidas pelo motor. Acrescentar uma maldição numérica nova é
# só declarar aqui — nenhum código novo. Quem lê cada chave:
#   ataque      → eff_atk em handle_attack
#   movimento   → _moves_base
#   vontade     → _testar_save
#   visao       → _get_raio_visao
#   dano_fisico → _resolver_dano_ataque_basico
#   ca          → _player_effective_ac
MALDICAO_MOD_CHAVES = ("ataque", "movimento", "vontade", "visao", "dano_fisico", "ca")
```

- [ ] **Step 4: Criar o helper**

Em `GameRoom`, logo depois de `_tem_maldicao`:

```python
    def _maldicao_mod(self, p, chave):
        """Soma os modificadores das maldições ativas para uma chave de
        MALDICAO_MOD_CHAVES. É o único ponto que sabe ler o campo `mods`."""
        return sum(MALDICOES[m["id"]].get("mods", {}).get(chave, 0)
                   for m in self._maldicoes(p))
```

- [ ] **Step 5: Migrar os três pontos hardcoded**

Em `handle_attack`, trocar:

```python
            maldicao_atk = -2 if self._tem_maldicao(p, "maos_tremulas") else 0
```

por:

```python
            maldicao_atk = self._maldicao_mod(p, "ataque")
```

Em `_moves_base`, trocar:

```python
        maldicao_mov = -3 if self._tem_maldicao(p, "correntes_invisiveis") else 0
```

por:

```python
        maldicao_mov = self._maldicao_mod(p, "movimento")
```

Em `_testar_save`, trocar:

```python
        if tipo_save == "vontade" and self._eh_jogador(alvo) and self._tem_maldicao(alvo, "espirito_covarde"):
            bonus -= 2
```

por:

```python
        if tipo_save == "vontade" and self._eh_jogador(alvo):
            bonus += self._maldicao_mod(alvo, "vontade")
```

> A guarda `_eh_jogador` **fica**: `_maldicao_mod` chama `_maldicoes`, que grava
> campos no dict; rodá-la em monstro poluiria o estado do monstro.

- [ ] **Step 6: Rodar e confirmar que passa**

```bash
python tools/test_maldicoes.py
```

Esperado: **0 falharam**. Se algum dos três números mudou, a migração está errada — não "ajustar o teste".

- [ ] **Step 7: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "refactor(maldicoes): camada declarativa de modificadores"
```

---

## Task 2: Olhos da Escuridão, Marca do Caçador e o `_pen` de CA

**Files:**
- Modify: `server.py` — `MALDICOES`, `_get_raio_visao`, `_player_effective_ac`
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever os testes**

```python
def test_visao_e_ca():
    print("\n[12] Olhos da Escuridão e Marca do Caçador")
    r, p = sala()
    v0 = r._get_raio_visao(p)
    asyncio.run(r._aplicar_maldicao(p, "olhos_escuridao"))
    check("visão cai 2", r._get_raio_visao(p) == v0 - 2)
    p["spd"] = 1; p["int_"] = 10; p["dex"] = 10
    check("piso de 1 respeitado", r._get_raio_visao(p) >= 1)

    r2, p2 = sala()
    ca0 = r2._player_effective_ac(p2)
    asyncio.run(r2._aplicar_maldicao(p2, "marca_cacador"))
    check("CA efetiva cai 1", r2._player_effective_ac(p2) == ca0 - 1)

def test_pen_veneno_no_jogador():
    print("\n[13] Penalidades de veneno saem do inerte")
    r, p = sala()
    ca0 = r._player_effective_ac(p)
    p["penalidades"] = {"ca": -2}
    check("penalidade de CA do veneno agora vale",
          r._player_effective_ac(p) == ca0 - 2)
```

Registrar as duas em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: falha em "visão cai 2", "CA efetiva cai 1" e "penalidade de CA do veneno agora vale".

- [ ] **Step 3: Declarar as duas maldições**

```python
    "olhos_escuridao": {"nome":"Olhos da Escuridão","categoria":"leve","desc":"-2 alcance de visão",
                        "mods":{"visao":-2}},
    "marca_cacador": {"nome":"Marca do Caçador","categoria":"leve","desc":"inimigos recebem +1 contra você",
                      "mods":{"ca":-1}},
```

- [ ] **Step 4: Ler `visao` e `ca`**

Em `_get_raio_visao`, na linha do `return`:

```python
        return max(1, raio_base + bonus_atributos + bonus_item + bonus_luz
                   + self._maldicao_mod(p, "visao"))
```

Em `_player_effective_ac`:

```python
        return (p["ac"] + self.temp_def.get(p["id"], 0)
                + self._cancao_bonus(p, "bonus_ca")
                + gl_ca + self._mod_magia(p, "ca")
                - self._corrosao_ca_pen(p)
                + self._pen(p, "ca")              # penalidade de veneno (era inerte)
                + self._maldicao_mod(p, "ca"))    # Marca do Caçador
```

> `_pen` devolve valor **já assinado** (≤ 0), por isso soma em vez de subtrair —
> confira a docstring dele antes de inverter o sinal.

Atualizar a docstring de `_player_effective_ac` para citar veneno e maldição.

- [ ] **Step 5: Rodar e confirmar que passa**

```bash
python tools/test_maldicoes.py
```

Esperado: **0 falharam**.

- [ ] **Step 6: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Olhos da Escuridao e Marca do Cacador"
```

---

## Task 3: Lâmina Enferrujada e o `_pen` de dano

**Files:**
- Modify: `server.py` — `MALDICOES`, `_resolver_dano_ataque_basico`
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever os testes**

```python
def test_dano_fisico():
    print("\n[14] Lâmina Enferrujada e penalidade de dano do veneno")
    # Dado fixo para o teste não depender de sorte.
    import random as _rnd
    r, p = sala()
    p["weapon"] = {"id": "t", "name": "Espada", "die": "1d1", "stat": "str_"}
    p["str_"] = 10   # mod 0 → dano base previsível
    alvo = {"id": "m1", "name": "Alvo", "hp": 50, "ca": 10, "pos": [5, 6]}
    def dano():
        d, *_ = r._resolver_dano_ataque_basico(p, alvo, False, 10)
        return d
    base = dano()
    asyncio.run(r._aplicar_maldicao(p, "lamina_enferrujada"))
    check("dano da arma cai 2", dano() == max(1, base - 2))

    r2, p2 = sala()
    p2["weapon"] = {"id": "t", "name": "Espada", "die": "1d1", "stat": "str_"}
    p2["str_"] = 10
    b2 = r2._resolver_dano_ataque_basico(p2, alvo, False, 10)[0]
    p2["penalidades"] = {"dano": -2}
    check("penalidade de dano do veneno agora vale",
          r2._resolver_dano_ataque_basico(p2, alvo, False, 10)[0] == max(1, b2 - 2))

    r3, p3 = sala()
    p3["weapon"] = {"id": "t", "name": "Faca", "die": "1d1", "stat": "str_"}
    p3["str_"] = 10
    asyncio.run(r3._aplicar_maldicao(p3, "lamina_enferrujada"))
    check("piso de 1 respeitado",
          r3._resolver_dano_ataque_basico(p3, alvo, False, 10)[0] >= 1)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: falha em "dano da arma cai 2" e "penalidade de dano do veneno agora vale".

- [ ] **Step 3: Declarar a maldição**

```python
    "lamina_enferrujada": {"nome":"Lâmina Enferrujada","categoria":"leve","desc":"-2 dano físico",
                           "mods":{"dano_fisico":-2}},
```

- [ ] **Step 4: Ler `dano_fisico`**

Em `_resolver_dano_ataque_basico`, **apenas no ramo armado** (dentro do `if die_str:`), acrescentar os dois termos ao `max(1, ...)`:

```python
            dmg = max(1, dmg + surv_mod + cancao_dano + gl_dano
                      + self._mod_magia(p, "dano") + self._tecnica_bonus_dano(p)
                      + bonus_extra + weapon.get("dmg_bonus", 0)
                      + p.get("skill_bonus_dano", 0) - self._corrosao_arma_pen(p)
                      + self._pen(p, "dano")                      # veneno (era inerte)
                      + self._maldicao_mod(p, "dano_fisico"))     # Lâmina Enferrujada
```

> **Só no ramo armado, de propósito.** O ramo desarmado (`else`) nunca incluiu
> `skill_bonus_dano` nem corrosão — a docstring da função registra essa
> assimetria como intencional. Lâmina Enferrujada é sobre a arma; somar no soco
> mudaria comportamento fora do escopo.

- [ ] **Step 5: Rodar e confirmar que passa**

```bash
python tools/test_maldicoes.py
```

Esperado: **0 falharam**.

- [ ] **Step 6: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Lamina Enferrujada e penalidade de dano do veneno"
```

---

## Task 4: Aura Profana

**Files:**
- Modify: `server.py` — `MALDICOES`, `handle_attack` (`eff_atk`)
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_aura_profana():
    print("\n[15] Aura Profana")
    r, p = sala()
    aliado = S.make_player("p2", "Lewis", "cleric", 1)
    aliado["pos"] = [5, 6]   # adjacente a [5,5]
    r.players["p2"] = aliado
    check("sem maldição, ninguém sofre", r._aura_profana_pen(aliado) == 0)
    asyncio.run(r._aplicar_maldicao(p, "aura_profana"))
    check("aliado adjacente leva -1", r._aura_profana_pen(aliado) == -1)
    check("o próprio portador não sofre", r._aura_profana_pen(p) == 0)
    aliado["pos"] = [5, 9]
    check("aliado longe não sofre", r._aura_profana_pen(aliado) == 0)
    aliado["pos"] = [5, 6]; aliado["alive"] = True
    p["alive"] = False
    check("portador morto não irradia", r._aura_profana_pen(aliado) == 0)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_aura_profana_pen'`.

- [ ] **Step 3: Declarar a maldição e criar o helper**

No catálogo (sem `mods` — não é um número somado ao próprio portador):

```python
    "aura_profana": {"nome":"Aura Profana","categoria":"media","desc":"aliados adjacentes: -1 ataque"},
```

Em `GameRoom`, junto dos outros helpers de maldição:

```python
    def _aura_profana_pen(self, p):
        """-1 de ataque por aliado VIVO adjacente que carrega Aura Profana.
        O próprio portador não é afetado — a maldição irradia para fora."""
        return -sum(1 for outro in self.players.values()
                    if outro is not p and self._ativo(outro)
                    and self._no_raio(p, outro, 1)
                    and self._tem_maldicao(outro, "aura_profana"))
```

- [ ] **Step 4: Consultar no ataque**

Em `handle_attack`, dentro do cálculo de `eff_atk`, acrescentar uma linha ao somatório:

```python
                       + self._aura_profana_pen(p)               # Aura Profana de aliado adjacente
```

- [ ] **Step 5: Rodar e confirmar que passa**

```bash
python tools/test_maldicoes.py
```

Esperado: **0 falharam**.

- [ ] **Step 6: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Aura Profana"
```

---

## Task 5: Fortuna Roubada

**Files:**
- Modify: `server.py` — `MALDICOES`, `handle_take_from_chest`, `handle_take_from_decor`, `_conceder_objetivo_reward`
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_fortuna_roubada():
    print("\n[16] Fortuna Roubada")
    r, p = sala()
    p["gold"] = 0
    asyncio.run(r._ganhar_ouro(p, 100, "do baú"))
    check("sem maldição, recebe tudo", p["gold"] == 100)
    asyncio.run(r._aplicar_maldicao(p, "fortuna_roubada"))
    p["gold"] = 0
    asyncio.run(r._ganhar_ouro(p, 100, "do baú"))
    check("com a maldição, recebe metade", p["gold"] == 50)
    p["gold"] = 0
    asyncio.run(r._ganhar_ouro(p, 1, "do baú"))
    check("arredonda para baixo", p["gold"] == 0)
    p["gold"] = 0
    asyncio.run(r._ganhar_ouro(p, 0, "do baú"))
    check("zero continua zero", p["gold"] == 0)
    # Os três sites de ouro achado precisam MESMO usar o helper — sem isto, o
    # teste passaria com um deles esquecido. Mesma técnica do teste de
    # sincronia [N2] em tools/test_editor_itens.py.
    import os as _os
    fonte = open(_os.path.join(_os.path.dirname(_os.path.dirname(
        _os.path.abspath(__file__))), "server.py"), encoding="utf-8", errors="ignore").read()
    check("os 3 sites de ouro achado usam o helper",
          fonte.count("await self._ganhar_ouro(") >= 3)
    # E a venda continua creditando direto — patrimônio próprio, não achado.
    check("venda de item não passa pelo helper",
          'p["gold"] += sell_price' in fonte)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_ganhar_ouro'`.

- [ ] **Step 3: Declarar a maldição e criar o helper**

```python
    "fortuna_roubada": {"nome":"Fortuna Roubada","categoria":"leve","desc":"recebe metade do ouro"},
```

Em `GameRoom`:

```python
    async def _ganhar_ouro(self, p, quantia, motivo=""):
        """Credita ouro ACHADO (baú, container, recompensa de objetivo) aplicando
        Fortuna Roubada. Venda de item não passa por aqui de propósito: é
        patrimônio próprio, e receber metade do preço anunciado confundiria.
        Devolve o quanto foi realmente creditado."""
        quantia = max(0, int(quantia))
        if quantia and self._tem_maldicao(p, "fortuna_roubada"):
            perdido = quantia - quantia // 2
            quantia = quantia // 2
            await self.gm_say(f"☠️ **Fortuna Roubada** consome **{perdido}** ouros "
                              f"{motivo} de **{p['name']}**.")
        p["gold"] = p.get("gold", 0) + quantia
        return quantia
```

- [ ] **Step 4: Usar o helper nos três sites de ouro achado**

Em `handle_take_from_chest`, trocar:

```python
            p["gold"] += amount
            chest["gold"] = 0
            await self.gm_say(f"🪙 **{p['name']}** pegou **{amount}** ouros do baú!")
```

por:

```python
            recebido = await self._ganhar_ouro(p, amount, "do baú")
            chest["gold"] = 0
            await self.gm_say(f"🪙 **{p['name']}** pegou **{recebido}** ouros do baú!")
```

Em `handle_take_from_decor`, trocar:

```python
            p["gold"] += amount
            loot["gold"] = 0
            await self.gm_say(f"🪙 **{p['name']}** pegou **{amount}** ouros do objeto!")
```

por:

```python
            recebido = await self._ganhar_ouro(p, amount, "do objeto")
            loot["gold"] = 0
            await self.gm_say(f"🪙 **{p['name']}** pegou **{recebido}** ouros do objeto!")
```

Em `_conceder_objetivo_reward`, trocar:

```python
            if ouro_share: p["gold"] += ouro_share
```

por:

```python
            if ouro_share: await self._ganhar_ouro(p, ouro_share, "da recompensa")
```

> `_conceder_objetivo_reward` **já é `async def`** (verificado) — o `await`
> entra direto, sem mudar a assinatura nem os chamadores.

- [ ] **Step 5: Rodar e confirmar que passa**

```bash
python tools/test_maldicoes.py
python tools/test_modo_mestre.py
```

Esperado: os dois com **0 falharam**. O segundo cobre objetivos e recompensa.

- [ ] **Step 6: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Fortuna Roubada"
```

---

## Task 6: Azar Sobrenatural

**Files:**
- Modify: `server.py` — `MALDICOES`, `handle_attack`, `enter_dungeon`
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_azar_sobrenatural():
    print("\n[17] Azar Sobrenatural")
    r, p = sala()
    check("sem maldição, o 20 crita", r._azar_consome_critico(p, 20) is False)
    asyncio.run(r._aplicar_maldicao(p, "azar_sobrenatural"))
    check("o primeiro 20 da masmorra não crita", r._azar_consome_critico(p, 20) is True)
    check("o segundo 20 crita", r._azar_consome_critico(p, 20) is False)
    check("um 19 nunca consome a flag", r._azar_consome_critico(p, 19) is False)
    p.pop("azar_20_gasto", None)   # é o que enter_dungeon faz
    check("entrar de novo na masmorra rearma", r._azar_consome_critico(p, 20) is True)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_azar_consome_critico'`.

- [ ] **Step 3: Declarar a maldição e criar o helper**

```python
    "azar_sobrenatural": {"nome":"Azar Sobrenatural","categoria":"leve","desc":"primeiro 20 natural não crita"},
```

Em `GameRoom`:

```python
    def _azar_consome_critico(self, p, roll):
        """True quando Azar Sobrenatural rouba ESTE crítico. Só o primeiro 20
        natural de cada masmorra é consumido; a flag é zerada em enter_dungeon.
        Efeito colateral: marca a flag quando devolve True."""
        if roll != 20 or not self._tem_maldicao(p, "azar_sobrenatural"):
            return False
        if p.get("azar_20_gasto"):
            return False
        p["azar_20_gasto"] = True
        return True
```

- [ ] **Step 4: Consultar no ataque**

Em `handle_attack`, logo APÓS o bloco que força o crítico (as duas rolagens —
normal e reroll da Sorte — já aconteceram nesse ponto):

```python
            if hit and _forca_critico:
                crit = True
            if crit and self._azar_consome_critico(p, roll):
                crit = False
                await self.gm_say(f"☠️ **Azar Sobrenatural** rouba o crítico de **{p['name']}** — "
                                  f"o golpe acerta, mas sem a força que prometia.")
```

- [ ] **Step 5: Rearmar ao entrar na masmorra**

Em `enter_dungeon`, junto dos outros resets "por masmorra nova" (os mesmos que
são suprimidos quando `self._emendando` — corrosão, vinho, cerveja, chamas):

```python
                p.pop("azar_20_gasto", None)
```

> **Deliberado:** numa etapa encadeada (`_emendando`) o reset é suprimido, como
> todos os outros. A regra da masmorra sequenciada é "nada se recupera" —
> ganhar um crítico de volta ao emendar contrariaria isso.

- [ ] **Step 6: Rodar e confirmar que passa**

```bash
python tools/test_maldicoes.py
python tools/test_masmorra_sequenciada.py
```

Esperado: os dois com **0 falharam**.

- [ ] **Step 7: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Azar Sobrenatural"
```

---

## Task 7: Regressão e verificação no jogo

**Files:** nenhum (verificação)

- [ ] **Step 1: Bateria completa**

```bash
python tools/test_maldicoes.py
python tools/test_editor_itens.py
python tools/test_devorador.py
python tools/test_guilda.py
python tools/test_modo_mestre.py
python tools/test_savegames.py
python tools/test_roteamento_itens.py
python tools/test_masmorra_sequenciada.py
python tools/test_cenas_conversa.py
```

Esperado: todas com **0 falharam**. `handle_attack`, `_moves_base`,
`_testar_save`, `_get_raio_visao`, `_player_effective_ac` e
`_resolver_dano_ataque_basico` são atravessados por quase toda suíte — é aqui
que uma migração errada da Task 1 apareceria.

- [ ] **Step 2: Conferir a cobertura do catálogo**

```bash
python -c "
import sys; sys.path.insert(0,'.')
import server as S
implementadas = {m for m in S.MALDICOES if S.MALDICOES[m].get('mods')}
implementadas |= {'passos_pesados','corpo_exausto','silencio_deuses','voz_quebrada',
                  'aura_profana','fortuna_roubada','azar_sobrenatural'}
for cat in ('leve','media','grave'):
    op = [m for m,d in S.MALDICOES.items() if d['categoria']==cat and not d.get('progressiva')]
    inertes = [m for m in op if m not in implementadas]
    print(f'{cat}: {len(op)-len(inertes)}/{len(op)} com efeito, inertes: {inertes}')
"
```

Esperado: `leve: 6/8`. Se der menos, alguma task não fechou.

- [ ] **Step 3: Smoke test no jogo**

Subir com `preview_start` (nunca `python server.py` pelo Bash). Criar sala,
escolher o Guerreiro, entrar na masmorra. No console do navegador, conferir o
raio de visão antes e depois — a maldição precisa de um caminho real para ser
aplicada, então usar uma armadilha de maldição específica de `olhos_escuridao`
numa masmorra de teste, ou o Modo Mestre com a habilidade Amaldiçoar.

Confirmar visualmente: a névoa revela um raio menor, e o quadro de maldição
abre com `amaldicoado.png` e a explicação do efeito.

- [ ] **Step 4: Commit final (se sobrou ajuste)**

```bash
git status
git add server.py tools/test_maldicoes.py
git commit -m "test(maldicoes): ajustes da verificacao da Fase A"
```

Se nada mudou, pular.

---

## Notas para quem implementar

- **A Task 1 é a única perigosa.** As outras acrescentam; ela troca código que
  já funciona. Se um teste de caracterização mudar de resultado, o erro está na
  migração — nunca no teste.
- **`_pen` devolve valor já assinado (≤ 0).** Some, não subtraia. Inverter o
  sinal transformaria penalidade de veneno em bônus.
- **`_maldicoes()` muta o dict do jogador** (normaliza a lista, grava
  `amaldicoado`/`maldicao_tipo`). Por isso `_maldicao_mod` só deve ser chamado
  com jogador — as guardas `_eh_jogador` existentes ficam onde estão.
- **O usuário edita `server.py` em paralelo.** Ver as convenções no topo.
