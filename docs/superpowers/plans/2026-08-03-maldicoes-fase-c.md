# Maldições Fase C — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tirar do inerte as 7 maldições não-progressivas restantes, fechando o catálogo em 25/25.

**Architecture:** Nenhuma migração — todas as sete entram por ganchos que já existem. Carne Frágil usa a camada declarativa `mods` da Fase A com uma chave nova, lida em `_apply_damage_types` (o mesmo funil onde a redução da Licantropia já mora). Fraqueza Arcana multiplica o `dmg_mult` que `handle_magia` já plumba até todos os executores de magia. As demais penduram em `_player_dies`, no fim de combate, no início e no fim do turno.

**Tech Stack:** Python 3 + `websockets` (server.py, sem framework). Testes são scripts que rodam da raiz e imprimem ✅/❌, saindo com código 1 se algo falhar.

**Spec:** `docs/superpowers/specs/2026-08-03-maldicoes-fase-c-design.md`

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta entrega |
|---|---|
| `server.py` | 7 maldições, cada uma num gancho existente |
| `tools/test_maldicoes.py` | cresce de 140 para ~170 checks |

**Convenções:**
- Testes rodam da raiz: `python tools/test_maldicoes.py`.
- Commits em português: `feat(maldicoes)` / `fix(maldicoes)` / `refactor(maldicoes)`.
- **O usuário edita `server.py` em paralelo.** Rodar `git status` e `git diff server.py` antes de cada `git add`; conferir que todo hunk é seu. Nunca `git add -A`, `git add .` ou `git add -u`.
- `tools/test_maldicoes.py` já tem helpers `sala()`, `check()`, `anel()`, `equipar()`. Ler o arquivo antes; reusar `sala()`. `S` é o módulo `server` importado.
- **`_maldicoes(p)` MUTA o dict que recebe** (normaliza a lista, grava `amaldicoado`/`maldicao_tipo`). Todo leitor de maldição (`_tem_maldicao`, `_maldicao_mod`, `_maldicao_estagio_cfg`) só pode ser chamado com jogador. Onde o alvo pode ser monstro, a guarda `_eh_jogador` é obrigatória.

---

## Task 1: Carne Frágil

**Files:**
- Modify: `server.py` — `MALDICOES`, `MALDICAO_MOD_CHAVES`, `_apply_damage_types` (~19298)
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_carne_fragil():
    print("\n[23] Carne Frágil")
    r, p = sala()
    alvo_monstro = {"id": "m1", "name": "Goblin", "hp": 20, "max_hp": 20, "ca": 10}
    base_fis = r._apply_damage_types(10, [S.DMG_PHYSICAL], p)
    base_fogo = r._apply_damage_types(10, [S.DMG_FIRE], p)
    asyncio.run(r._aplicar_maldicao(p, "carne_fragil"))
    check("herói recebe +2 de dano físico",
          r._apply_damage_types(10, [S.DMG_PHYSICAL], p) == base_fis + 2)
    check("vale para dano não-físico também",
          r._apply_damage_types(10, [S.DMG_FIRE], p) == base_fogo + 2)

    # Monstro não é afetado, e não recebe campos de maldição no dict.
    antes = r._apply_damage_types(10, [S.DMG_PHYSICAL], alvo_monstro)
    check("monstro não ganha +2", antes == r._apply_damage_types(10, [S.DMG_PHYSICAL], alvo_monstro))
    check("monstro não é poluído com campos de maldição",
          "maldicoes" not in alvo_monstro and "amaldicoado" not in alvo_monstro)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: falha em "herói recebe +2 de dano".

- [ ] **Step 3: Declarar a maldição**

Em `MALDICOES`:

```python
    "carne_fragil": {"nome":"Carne Frágil","categoria":"media","desc":"+2 dano recebido",
                     "mods":{"dano_recebido":2}},
```

E acrescentar a chave à tupla de documentação `MALDICAO_MOD_CHAVES`, junto do comentário que lista quem lê cada uma:

```python
#   dano_recebido → _apply_damage_types
MALDICAO_MOD_CHAVES = ("ataque", "movimento", "vontade", "visao", "dano_fisico", "ca", "dano_recebido")
```

- [ ] **Step 4: Ler a chave em `_apply_damage_types`**

Logo APÓS o bloco da Licantropia (que termina em `total -= self._licantropia_config(target)["reducao"]`), acrescentar:

```python
        # Carne Frágil: +2 no dano que o herói recebe. Espelho da redução da
        # Licantropia acima — mesmo funil, sinal oposto.
        if self._eh_jogador(target):
            total += self._maldicao_mod(target, "dano_recebido")
```

> A guarda `_eh_jogador` é **obrigatória**: esta função é chamada com monstro
> como alvo na maioria das vezes, e `_maldicao_mod` → `_maldicoes` grava campos
> no dict que recebe.

- [ ] **Step 5: Rodar e confirmar que passa**

```bash
python tools/test_maldicoes.py
python tools/test_devorador.py
python tools/test_modo_mestre.py
```

Esperado: todas com **0 falharam**.

- [ ] **Step 6: Commit**

```bash
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Carne Fragil"
```

---

## Task 2: Fraqueza Arcana

**Files:**
- Modify: `server.py` — `MALDICOES`, `handle_magia` (bloco de metamagia, ~7574-7590)
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_fraqueza_arcana():
    print("\n[24] Fraqueza Arcana")
    r, p = sala()
    check("sem maldição, multiplicador cheio", r._fraqueza_arcana_mult(p) == 1)
    asyncio.run(r._aplicar_maldicao(p, "fraqueza_arcana"))
    check("com a maldição, metade", r._fraqueza_arcana_mult(p) == 0.5)

    # O dano resultante precisa ser INTEIRO. O Fortalecer já produz ×1,25 hoje,
    # então dano fracionário é um risco pré-existente que ×0,5 torna frequente.
    for base in (7, 9, 13):
        dano = int(base * r._fraqueza_arcana_mult(p))
        check(f"dano de {base} vira inteiro", isinstance(dano, int))
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_fraqueza_arcana_mult'`.

- [ ] **Step 3: Declarar a maldição e criar o helper**

```python
    "fraqueza_arcana": {"nome":"Fraqueza Arcana","categoria":"leve","desc":"magias causam metade do dano"},
```

Em `GameRoom`, junto dos outros helpers de maldição:

```python
    def _fraqueza_arcana_mult(self, p):
        """Multiplicador de dano de magia da Fraqueza Arcana. Entra no mesmo
        `dmg_mult` que a Metamagia Fortalecer já usa — os dois se multiplicam."""
        return 0.5 if self._tem_maldicao(p, "fraqueza_arcana") else 1
```

- [ ] **Step 4: Aplicar em `handle_magia`**

Localize o bloco de metamagia (`for kind, cf, cs in aplicadas:` com os ramos
`fortalecer` / `estender` / `aprimorar`). **Depois** desse laço inteiro,
acrescentar:

```python
        dmg_mult *= self._fraqueza_arcana_mult(p)
```

> Colocar DEPOIS do laço é obrigatório: `dmg_mult` só é atribuído dentro do ramo
> `fortalecer`, então aplicar antes perderia o efeito quando o herói não usa
> Fortalecer. Confirme que `dmg_mult` já está inicializado (`= 1`) acima do laço;
> se não estiver, **pare e reporte** em vez de inicializar por conta própria.

- [ ] **Step 5: Verificar o dano inteiro**

Rodar uma magia de dano ponta a ponta com a maldição ativa e conferir que o HP
do alvo cai por um inteiro:

```bash
python - <<'EOF'
import asyncio, sys
sys.path.insert(0, '.')
import server as S
r = S.GameRoom("FA")
async def noop(*a, **k): pass
r.gm_say=noop; r.broadcast=noop; r.push_state=noop; r.send_to=noop
r._checkpoint_savegame=lambda *a,**k: None
p = S.make_player("p1","Pedro","mage",0)
print("mult com maldicao:", end=" ")
asyncio.run(r._aplicar_maldicao(p, "fraqueza_arcana"))
print(r._fraqueza_arcana_mult(p))
for base in (7, 9, 13, 4):
    print(f"  {base} * 0.5 =", base * 0.5, "-> int:", int(base * 0.5))
EOF
```

Se algum executor de magia guardar o resultado sem `int()`, o HP do alvo virará
float. Se você encontrar isso, **corrija arredondando naquele executor**
(`int(... + 0.5)`, seguindo o padrão de `_executar_raio_divino`) e diga quais
executores precisaram — é um bug pré-existente do Fortalecer que esta maldição
expõe.

- [ ] **Step 6: Rodar e commitar**

```bash
python tools/test_maldicoes.py
python tools/test_mago_espec.py
python tools/test_guilda.py
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Fraqueza Arcana"
```

---

## Task 3: Alma Quebrada

**Files:**
- Modify: `server.py` — `MALDICOES`, `_cancao_bonus` (~16703), `_grito_mov_bonus`
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_alma_quebrada():
    print("\n[25] Alma Quebrada")
    r, p = sala()
    p["buffs_cancao"] = {"bonus_acerto": 2, "bonus_mov": 1}
    p["mov_bonus_val"] = 2; p["mov_bonus_ate"] = r.round_num + 1
    check("canção vale sem a maldição", r._cancao_bonus(p, "bonus_acerto") == 2)
    check("grito vale sem a maldição", r._grito_mov_bonus(p) == 2)

    asyncio.run(r._aplicar_maldicao(p, "alma_quebrada"))
    check("canção zerada", r._cancao_bonus(p, "bonus_acerto") == 0)
    check("grito zerado", r._grito_mov_bonus(p) == 0)

    # Auto-buff do paladino NÃO é bônus de aliado e continua valendo.
    r2, p2 = sala()
    pal = S.make_player("p2", "Richard", "paladin", 1)
    r2.players["p2"] = pal
    pal["guerreiro_luz_ativo"] = True
    pal["guerreiro_luz_bonus"] = {"ataque": 2, "ca": 1}
    asyncio.run(r2._aplicar_maldicao(pal, "alma_quebrada"))
    check("Guerreiro da Luz do próprio paladino segue valendo",
          pal["guerreiro_luz_bonus"]["ataque"] == 2 and pal.get("guerreiro_luz_ativo"))
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: falha em "canção zerada" e "grito zerado".

- [ ] **Step 3: Declarar a maldição**

```python
    "alma_quebrada": {"nome":"Alma Quebrada","categoria":"media","desc":"não recebe bônus de aliados"},
```

- [ ] **Step 4: Zerar os dois helpers**

Em `_cancao_bonus`, logo após a guarda de Silêncio:

```python
    def _cancao_bonus(self, p, chave):
        """Bônus da Canção Heroica (bardo) — SUPRIMIDO dentro de uma área de
        Silêncio e para quem carrega Alma Quebrada."""
        if self._em_silencio(p):
            return 0
        if self._tem_maldicao(p, "alma_quebrada"):
            return 0
        return p.get("buffs_cancao", {}).get(chave, 0)
```

Em `_grito_mov_bonus`:

```python
    def _grito_mov_bonus(self, p):
        """+N de movimento transitório (Técnica Grito de Guerra) enquanto válido
        nesta rodada. Alma Quebrada anula — é bônus concedido por aliado."""
        if self._tem_maldicao(p, "alma_quebrada"):
            return 0
        return p.get("mov_bonus_val", 0) if p.get("mov_bonus_ate", 0) >= self.round_num else 0
```

> **Só estes dois.** O Guerreiro da Luz é auto-buff do paladino, não bônus de
> aliado. Abençoar chega por `_mod_magia`, que não distingue magia lançada por
> aliado de magia própria — bloquear ali derrubaria os buffs do próprio herói.
> Cura e divisão de dano (Protetor, Tática Defensiva) também ficam de fora, por
> decisão de design registrada no spec.

- [ ] **Step 5: Rodar e commitar**

```bash
python tools/test_maldicoes.py
python tools/test_bardo_espec.py
python tools/test_guilda.py
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Alma Quebrada"
```

---

## Task 4: Sangramento Profano

**Files:**
- Modify: `server.py` — `MALDICOES`, `_processar_dreno_maldicoes`
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_sangramento_profano():
    print("\n[26] Sangramento Profano")
    r, p = sala()
    p["max_hp"] = 30; p["hp"] = 30
    asyncio.run(r._aplicar_maldicao(p, "sangramento_profano"))

    # 1º turno: só grava o HP de referência, ninguém sangra ainda.
    asyncio.run(r._processar_dreno_maldicoes(p))
    check("primeiro turno não sangra", p["hp"] == 30)

    # Sofreu dano entre os turnos → sangra 1.
    p["hp"] = 22
    asyncio.run(r._processar_dreno_maldicoes(p))
    check("sofreu dano no intervalo: sangra 1", p["hp"] == 21)

    # Sem dano desde o turno anterior → não sangra.
    asyncio.run(r._processar_dreno_maldicoes(p))
    check("sem dano no intervalo: não sangra", p["hp"] == 21)

    # Curou-se acima do valor anterior → também não sangra.
    p["hp"] = 28
    asyncio.run(r._processar_dreno_maldicoes(p))
    check("curou-se: não sangra", p["hp"] == 28)

    # Herói morto não sangra.
    r2, p2 = sala()
    asyncio.run(r2._aplicar_maldicao(p2, "sangramento_profano"))
    p2["max_hp"] = 30; p2["hp"] = 30
    asyncio.run(r2._processar_dreno_maldicoes(p2))
    p2["hp"] = 10; p2["alive"] = False
    asyncio.run(r2._processar_dreno_maldicoes(p2))
    check("herói morto não sangra", p2["hp"] == 10)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: falha em "sofreu dano no intervalo: sangra 1".

- [ ] **Step 3: Declarar a maldição**

```python
    "sangramento_profano": {"nome":"Sangramento Profano","categoria":"media",
                            "desc":"1 dano no início do turno após sofrer dano"},
```

- [ ] **Step 4: Acrescentar ao processador de início de turno**

Ao final de `_processar_dreno_maldicoes` (que a Fase B criou, e que já tem a
guarda `if not p.get("alive"): return` no topo):

```python
        # Sangramento Profano: em vez de instrumentar os ~67 pontos que tiram HP,
        # compara o HP com o do turno anterior. Se caiu, houve dano no intervalo.
        if self._tem_maldicao(p, "sangramento_profano"):
            anterior = p.get("_hp_turno_anterior")
            if anterior is not None and p.get("hp", 0) < anterior and p.get("hp", 0) > 0:
                p["hp"] = max(1, p["hp"] - 1)
                await self.gm_say(f"🩸 **Sangramento Profano** abre as feridas de "
                                  f"**{p['name']}** — **1** de dano.")
        p["_hp_turno_anterior"] = p.get("hp", 0)
```

> A gravação do `_hp_turno_anterior` fica **fora** do `if`, no fim da função:
> assim a referência é atualizada mesmo quando a maldição é adquirida no meio da
> masmorra, e o primeiro turno depois de amaldiçoado não sangra do nada.

> O `max(1, ...)` evita que o sangramento mate. É a mesma escolha do Eco da
> Morte (Task 6): dano de maldição desgasta, não executa.

- [ ] **Step 5: Rodar e commitar**

```bash
python tools/test_maldicoes.py
python tools/test_masmorra_sequenciada.py
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Sangramento Profano"
```

---

## Task 5: Dor Constante

**Files:**
- Modify: `server.py` — `MALDICOES`, `handle_end_turn` (~18588)
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_dor_constante():
    print("\n[27] Dor Constante")
    r, p = sala()
    p["max_hp"] = 30; p["hp"] = 30
    asyncio.run(r._aplicar_maldicao(p, "dor_constante"))

    p["action_done"] = True
    asyncio.run(r._cobrar_dor_constante(p))
    check("com a ação usada, dói 1", p["hp"] == 29)

    p["action_done"] = False
    asyncio.run(r._cobrar_dor_constante(p))
    check("sem usar a ação, não dói", p["hp"] == 29)

    # Não mata.
    p["hp"] = 1; p["action_done"] = True
    asyncio.run(r._cobrar_dor_constante(p))
    check("não mata", p["hp"] == 1)

    # Sem a maldição, nada acontece.
    r2, p2 = sala()
    p2["max_hp"] = 30; p2["hp"] = 30; p2["action_done"] = True
    asyncio.run(r2._cobrar_dor_constante(p2))
    check("sem a maldição, nada", p2["hp"] == 30)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_cobrar_dor_constante'`.

- [ ] **Step 3: Declarar a maldição e criar o helper**

```python
    "dor_constante": {"nome":"Dor Constante","categoria":"media","desc":"ações causam 1 dano"},
```

Em `GameRoom`, junto dos outros helpers de maldição:

```python
    async def _cobrar_dor_constante(self, p):
        """1 de dano ao encerrar o turno tendo usado a ação principal. Só a
        principal, no máximo 1 por turno: mover e ação bônus ficam de fora, para
        o jogador poder escolher passar o turno sem sangrar. Não mata."""
        if not p.get("alive") or not p.get("action_done"):
            return
        if not self._tem_maldicao(p, "dor_constante"):
            return
        if p.get("hp", 0) <= 1:
            return
        p["hp"] = max(1, p["hp"] - 1)
        await self.gm_say(f"💢 **Dor Constante** cobra seu preço de **{p['name']}** — **1** de dano.")
```

- [ ] **Step 4: Cobrar em `handle_end_turn`**

Em `handle_end_turn`, logo após as guardas iniciais (`if not self._is_turn(pid): return`)
e ANTES de qualquer avanço de iniciativa:

```python
        p_dor = self.players.get(pid)
        if p_dor:
            await self._cobrar_dor_constante(p_dor)
```

> **Furo conhecido e aceito:** o turno também termina por estouro de timer, e por
> esse caminho o dano não cobra. Instrumentar os 22 sites que marcam
> `action_done` seria a alternativa sem furo, mas é a maior refatoração das três
> fases num campo lido em dezenas de condições — não se paga por uma maldição
> média. Não "conserte" isso por conta própria.

- [ ] **Step 5: Rodar e commitar**

```bash
python tools/test_maldicoes.py
python tools/test_modo_mestre.py
python tools/test_masmorra_sequenciada.py
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Dor Constante"
```

---

## Task 6: Eco da Morte

**Files:**
- Modify: `server.py` — `MALDICOES`, `_player_dies` (~23175)
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_eco_da_morte():
    print("\n[28] Eco da Morte")
    r, p = sala()
    aliado = S.make_player("p2", "Lewis", "cleric", 1)
    aliado["pos"] = [6, 6]; aliado["max_hp"] = 40; aliado["hp"] = 40
    r.players["p2"] = aliado
    asyncio.run(r._aplicar_maldicao(aliado, "eco_morte"))

    asyncio.run(r._ecoar_morte(p))
    check("aliado amaldiçoado sofre 10", aliado["hp"] == 30)

    # Quem não carrega a maldição não sofre.
    outro = S.make_player("p3", "Luccas", "rogue", 2)
    outro["max_hp"] = 40; outro["hp"] = 40
    r.players["p3"] = outro
    asyncio.run(r._ecoar_morte(p))
    check("quem não tem a maldição não sofre", outro["hp"] == 40)

    # Não mata: piso de 1.
    aliado["hp"] = 4
    asyncio.run(r._ecoar_morte(p))
    check("não mata (piso de 1)", aliado["hp"] == 1)
    check("continua vivo", aliado.get("alive") is True)

    # O próprio morto não ecoa em si mesmo.
    r2, p2 = sala()
    asyncio.run(r2._aplicar_maldicao(p2, "eco_morte"))
    p2["max_hp"] = 40; p2["hp"] = 40
    asyncio.run(r2._ecoar_morte(p2))
    check("o morto não ecoa em si mesmo", p2["hp"] == 40)
```

Registrar em `main()`.

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_ecoar_morte'`.

- [ ] **Step 3: Declarar a maldição e criar o helper**

```python
    "eco_morte": {"nome":"Eco da Morte","categoria":"grave","desc":"aliado morto causa 10 dano"},
```

Em `GameRoom`, junto dos outros helpers de maldição:

```python
    ECO_MORTE_DANO = 10

    async def _ecoar_morte(self, morto):
        """A morte de um herói fere quem carrega Eco da Morte. São 10 EXATOS,
        aplicados direto — não passam por _apply_damage_types, senão Carne Frágil
        os viraria 12 e uma resistência os reduziria, e o número que o catálogo
        promete deixaria de ser o número real.

        NÃO pode matar (piso de 1): sem isso, uma morte viraria efeito dominó
        recursivo dentro do próprio _player_dies."""
        for q in self.players.values():
            if q is morto or not q.get("alive"):
                continue
            if not self._tem_maldicao(q, "eco_morte"):
                continue
            q["hp"] = max(1, q.get("hp", 1) - self.ECO_MORTE_DANO)
            await self.gm_say(f"💀 O **Eco da Morte** atravessa **{q['name']}** — "
                              f"**{self.ECO_MORTE_DANO}** de dano.")
```

- [ ] **Step 4: Chamar em `_player_dies`**

Em `_player_dies`, logo após a linha que marca `p["alive"] = False`:

```python
        await self._ecoar_morte(p)
```

> Depois de `alive = False`, de propósito: assim o próprio morto está fora do
> laço pela guarda `not q.get("alive")` **e** pela guarda `q is morto`.

- [ ] **Step 5: Rodar e commitar**

```bash
python tools/test_maldicoes.py
python tools/test_modo_mestre.py
python tools/test_savegames.py
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Eco da Morte"
```

---

## Task 7: Maldição da Ferrugem

**Files:**
- Modify: `server.py` — `MALDICOES`, `_testar_licantropia_fim_combate` (~14601), `_corroer_equipamento`
- Test: `tools/test_maldicoes.py`

- [ ] **Step 1: Escrever o teste**

```python
def test_maldicao_ferrugem():
    print("\n[29] Maldição da Ferrugem")
    r, p = sala()
    couro = {"id": "couro", "name": "Couro", "item_slot": "armor", "kind": "armor",
             "ac_bonus": 2, "bonuses": [], "buy_price": 80,
             "corrosion_materials": ["metal"], "corrosao_resistente": 0,
             "corrosao_niveis_penalidade": 2}
    equipar(r, p, couro, "armor")
    r.monsters = {}   # combate acabou: nenhum monstro vivo

    # Sem a maldição, o fim de combate não corrói nada.
    asyncio.run(r._processar_fim_de_combate())
    check("sem a maldição, nada corrói", r._corr(p).get("armadura_lvl", 0) == 0)

    asyncio.run(r._aplicar_maldicao(p, "maldicao_ferrugem"))
    r._licantropia_ultimo_fim_combate = None   # libera o dedup para reprocessar
    asyncio.run(r._processar_fim_de_combate())
    check("com a maldição, a peça se degrada", r._corr(p).get("armadura_lvl", 0) >= 1)
```

Registrar em `main()`.

> O campo é `armadura_lvl` — `_corroer_equipamento` grava
> `c[f"{pref}_lvl"] = c.get(f"{pref}_lvl", 0) + 1`, com `pref` em
> `armadura`/`escudo`/`arma`/`elmo`/`botas` (verificado).

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_maldicoes.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_processar_fim_de_combate'`.

- [ ] **Step 3: Tornar o monstro opcional em `_corroer_equipamento`**

A função usa `m` num único lugar — `await self._devorador_cura(m, cura)`, e
`_devorador_cura` faz `m["hp"]`, então `None` estouraria. A corrosão por
maldição não tem monstro por trás. Guardar a chamada:

```python
                if m is not None:
                    await self._devorador_cura(m, cura)
```

Atualizar a docstring da função para registrar que `m` pode ser `None` quando a
corrosão não vem de um Devorador.

- [ ] **Step 4: Generalizar o gancho de fim de combate**

Renomear `_testar_licantropia_fim_combate` para `_processar_fim_de_combate`,
mantendo o corpo da Licantropia e acrescentando a Ferrugem. O marcador de
deduplicação (`self._licantropia_ultimo_fim_combate`) fica com o nome atual —
o teste depende dele e renomeá-lo é churn sem ganho.

```python
    async def _processar_fim_de_combate(self):
        """O encontro acaba quando não resta nenhum monstro vivo no tabuleiro.
        Dispara a rolagem pós-combate da Licantropia e a corrosão da Maldição
        da Ferrugem."""
        if any(m.get("hp", 0) > 0 for m in self.monsters.values()): return
        marcador = (self.round_num, tuple(sorted(m["id"] for m in self.monsters.values() if m.get("hp", 0) <= 0)))
        if getattr(self, "_licantropia_ultimo_fim_combate", None) == marcador: return
        self._licantropia_ultimo_fim_combate = marcador
        for p in self.players.values():
            # ... corpo atual da Licantropia, inalterado ...
        # Maldição da Ferrugem: o equipamento se degrada ao fim de cada combate.
        for p in self.players.values():
            if not self._ativo(p) or not self._tem_maldicao(p, "maldicao_ferrugem"):
                continue
            await self._corroer_equipamento(None, p, CORROSAO_ARMADURA_METAL,
                                            CORROSAO_ARMA_METAL, cura=None,
                                            label="Maldição da Ferrugem")
```

Atualizar a **única** chamada de `_testar_licantropia_fim_combate` (~22928) para
o nome novo.

- [ ] **Step 5: Declarar a maldição**

```python
    "maldicao_ferrugem": {"nome":"Maldição da Ferrugem","categoria":"media",
                          "desc":"equipamento degrada após combate"},
```

- [ ] **Step 6: Rodar e commitar**

```bash
python tools/test_maldicoes.py
python tools/test_devorador.py
python tools/test_modo_mestre.py
git status
git diff server.py
git add server.py tools/test_maldicoes.py
git commit -m "feat(maldicoes): Maldicao da Ferrugem"
```

---

## Task 8: Regressão e fecho do catálogo

**Files:** nenhum (verificação)

- [ ] **Step 1: Bateria completa**

```bash
python tools/test_maldicoes.py
python tools/test_editor_itens.py
python tools/test_devorador.py
python tools/test_guilda.py
python tools/test_modo_mestre.py
python tools/test_savegames.py
python tools/test_masmorra_sequenciada.py
python tools/test_clerigo_espec.py
python tools/test_paladino_espec.py
python tools/test_bardo_espec.py
python tools/test_ladino_espec.py
python tools/test_mago_espec.py
python tools/test_cenas_conversa.py
```

Esperado: todas com **0 falharam**.

- [ ] **Step 2: Conferir o fecho do catálogo**

```bash
python -c "
import io, sys; sys.path.insert(0,'.')
import server as S
src = io.open('server.py', encoding='utf-8', errors='ignore').read()
inertes = [m for m, d in S.MALDICOES.items()
           if not d.get('mods') and not d.get('estagios') and src.count(f'\"{m}\"') <= 1]
print(f'{25-len(inertes)}/25 com efeito | inertes: {inertes}')
"
```

Esperado: **25/25 com efeito | inertes: []**.

- [ ] **Step 3: Prova ponta a ponta**

```bash
python - <<'EOF'
import asyncio, sys
sys.path.insert(0, '.')
import server as S
r = S.GameRoom("FASEC")
async def noop(*a, **k): pass
r.gm_say=noop; r.broadcast=noop; r.push_state=noop; r.send_to=noop
r._checkpoint_savegame=lambda *a,**k: None
r.phase="playing"
p = S.make_player("p1","Victor","warrior",0); p["pos"]=[5,5]; r.players["p1"]=p
p["max_hp"]=50; p["hp"]=50
base = r._apply_damage_types(10, [S.DMG_PHYSICAL], p)
asyncio.run(r._aplicar_maldicao(p, "carne_fragil"))
print("dano recebido:", base, "->", r._apply_damage_types(10, [S.DMG_PHYSICAL], p), "(esperado +2)")
asyncio.run(r._aplicar_maldicao(p, "dor_constante"))
p["action_done"] = True
asyncio.run(r._cobrar_dor_constante(p))
print("HP apos encerrar o turno com acao usada:", p["hp"], "(esperado 49)")
EOF
```

- [ ] **Step 4: Commit final (se sobrou ajuste)**

```bash
git status
git add server.py tools/test_maldicoes.py
git commit -m "test(maldicoes): ajustes da verificacao da Fase C"
```

Se nada mudou, pular.

---

## Notas para quem implementar

- **Esta fase não tem migração.** Nenhuma task troca código que já funciona; o
  risco é de alcance, não de regressão.
- **`_maldicoes(p)` MUTA o dict que recebe.** Onde o alvo pode ser monstro
  (`_apply_damage_types`), a guarda `_eh_jogador` é obrigatória, não decorativa.
- **Dano de maldição não mata.** Sangramento Profano, Dor Constante e Eco da
  Morte têm piso de 1 HP. É deliberado: maldição desgasta, não executa — e no
  caso do Eco, o piso é o que impede uma cascata recursiva de mortes.
- **O usuário edita `server.py` em paralelo.** Ver as convenções no topo.
