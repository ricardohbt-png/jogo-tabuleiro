# Veneno Agonia Sufocante (Sub-projeto E) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar o veneno lendário Agonia Sufocante — untado na arma (`coat_poison`), causa 1d4 de dano por rodada por até 1d4 rodadas, com um teste de Fortitude CD 14 por rodada que neutraliza o veneno imediatamente em caso de sucesso.

**Architecture:** Reusa 100% a entrega dos venenos existentes (loja `coat_poison` → `weapon_poison` → `_aplicar_veneno` no golpe). Adiciona duas capacidades GENÉRICAS ao sistema de venenos: `operacao:"dano"` (dano-por-rodada, registrado em `efeitos_veneno`) e `save_neutraliza_por_rodada` (teste por rodada em `_processar_venenos_turno` que encerra o efeito no sucesso).

**Tech Stack:** Python 3 + `websockets` (server.py); Vanilla JS (src/gameState.js — só catálogo); testes com o harness caseiro de `tools/test_*.py`.

---

## Estrutura de arquivos

| Arquivo | Mudança | Responsabilidade |
|---|---|---|
| `server.py` | Modificar | Entrada em `VENENOS`/`SHOP_MERCHANT`; ramo `operacao=="dano"` em `_aplicar_veneno`; tick de dano + save-por-rodada em `_processar_venenos_turno` |
| `src/gameState.js` | Modificar | 1 entrada em `CATALOGO_ITENS` (formato dos outros venenos) |
| `tools/test_veneno_agonia.py` | Criar | Testes (aplicação, tick falha/sucesso, duração, regressão de veneno de atributo) |

---

### Task 1: Veneno no catálogo + loja

**Files:**
- Modify: `server.py` — dict `VENENOS` (após `veneno_polvo_abissal`) e `SHOP_MERCHANT` (após os venenos existentes)
- Test: `tools/test_veneno_agonia.py`

- [ ] **Step 1: Criar o arquivo de teste com harness + teste [1]**

Crie `tools/test_veneno_agonia.py`:

```python
"""Testes do veneno Agonia Sufocante (Sub-projeto E).
Roda da raiz: python tools/test_veneno_agonia.py"""
import asyncio, sys, os, random
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, FLOOR, VENENOS, SHOP_MERCHANT

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK  {name}")
    else:    FAIL += 1; print(f"  XX  {name}  {extra}")

def setup(w=9, h=9):
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r._broadcast_dado = noop
    async def cap_send(pid, msg, *a, **k): pass
    r.send_to = cap_send
    r._is_turn = lambda pid: True
    r.phase = "playing"
    r.tiles = [[FLOOR] * w for _ in range(h)]
    r.map_w = w; r.map_h = h
    return r

def make_monster(r, mid, x, y, hp=40):
    m = {"id": mid, "name": "M"+mid, "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": 12, "alive": True, "tier": 1}
    r.monsters[mid] = m
    return m

async def main():
    random.seed(1)

    # ── [1] Catálogo + loja ────────────────────────────────────────────────────
    print("\n[1] Catálogo do veneno + loja")
    check("veneno no catálogo", "veneno_agonia_sufocante" in VENENOS)
    v = VENENOS.get("veneno_agonia_sufocante", {})
    check("operacao dano", v.get("operacao") == "dano")
    check("dano 1d4", v.get("dano") == "1d4")
    check("duracao 1d4", v.get("duracao") == "1d4")
    check("Fortitude CD 14", v.get("save") == "fortitude" and v.get("dificuldade") == 14)
    check("save por rodada", v.get("save_neutraliza_por_rodada") is True)
    shop = next((i for i in SHOP_MERCHANT if i["id"] == "veneno_agonia_sufocante"), None)
    check("vendável (coat_poison)", shop is not None and shop["effect"] == "coat_poison")
    check("aponta pro veneno", shop and shop.get("veneno_id") == "veneno_agonia_sufocante")

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_veneno_agonia.py`
Expected: FAIL — o veneno ainda não está no catálogo.

- [ ] **Step 3: Adicionar a entrada no `VENENOS`**

Dentro do dict `VENENOS`, após a entrada `"veneno_polvo_abissal": {…},` e antes do
`}` que fecha o dict, adicione:

```python
    "veneno_agonia_sufocante": {
        "nome": "Agonia Sufocante", "icone": "💀",
        "operacao": "dano", "dano": "1d4", "duracao": "1d4",
        "save": "fortitude", "dificuldade": 14,
        "save_neutraliza_por_rodada": True, "anula": False,
    },
```

- [ ] **Step 4: Adicionar o item em `SHOP_MERCHANT`**

Logo após a linha do `veneno_polvo_abissal` em `SHOP_MERCHANT`, adicione:

```python
    {"id": "veneno_agonia_sufocante", "name": "Agonia Sufocante", "emoji": "💀", "price": 40, "item_slot": "bag", "effect": "coat_poison", "value": 0, "veneno_id": "veneno_agonia_sufocante"},
```

- [ ] **Step 5: Rodar e ver passar**

Run: `python tools/test_veneno_agonia.py`
Expected: PASS — seção [1] OK.

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_veneno_agonia.py
git commit -m "feat(veneno): Agonia Sufocante no catalogo VENENOS + loja"
```

---

### Task 2: Ramo `operacao == "dano"` em `_aplicar_veneno`

**Files:**
- Modify: `server.py` — `_aplicar_veneno` (após a checagem de imunidade morto-vivo, ~server.py:10978, ANTES do save de aplicação)
- Test: `tools/test_veneno_agonia.py`

- [ ] **Step 1: Adicionar os testes [2] (aplicação) e [6] (regressão de veneno de atributo)**

Antes do `print(f"\n=== ...")` final:

```python
    # ── [2] Aplicação registra efeito de dano (sem save de aplicação) ──────────
    print("\n[2] _aplicar_veneno (dano)")
    r = setup()
    m = make_monster(r, "m1", 4, 4, hp=40)
    await r._aplicar_veneno(m, "veneno_agonia_sufocante")
    efs = [e for e in m.get("efeitos_veneno", []) if e.get("operacao") == "dano"]
    check("efeito de dano registrado", len(efs) == 1)
    check("dano 1d4", efs and efs[0]["dano"] == "1d4")
    check("duracao entre 1 e 4", efs and 1 <= efs[0]["duracao"] <= 4)
    check("save por rodada gravado", efs and efs[0]["save_neutraliza_por_rodada"] is True)

    # morto-vivo é imune (não registra efeito)
    mu = make_monster(r, "m2", 5, 5, hp=30); mu["undead"] = True
    await r._aplicar_veneno(mu, "veneno_agonia_sufocante")
    check("morto-vivo imune (sem efeito)", not mu.get("efeitos_veneno"))

    # ── [6] Regressão: veneno de atributo (reduzir) ainda funciona ─────────────
    print("\n[6] regressão: veneno de atributo")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); r.players["p1"] = p
    r._testar_save = lambda *a, **k: (False, 1, 0, 1)   # falha no save → aplica
    str0 = p.get("str_", 10)
    await r._aplicar_veneno(p, "veneno_aranha_sombria")   # operacao 'reduzir' (forca)
    check("aranha ainda reduz Força", p.get("str_", 10) < str0)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_veneno_agonia.py`
Expected: FAIL — o efeito de dano não é registrado (o ramo `operacao=="dano"` ainda
não existe; o veneno cai no fluxo padrão que espera `atributo`).

- [ ] **Step 3: Adicionar o ramo `operacao == "dano"` no `_aplicar_veneno`**

Em `_aplicar_veneno`, logo APÓS o bloco de imunidade morto-vivo/constructo
(`if not self._eh_jogador(alvo) and (alvo.get("undead") ...): return`, server.py:~10974-10978)
e ANTES do bloco de fraqueza/save de aplicação (`_save_pen = 0` …), adicione:

```python
        # Veneno de DANO (ex.: Agonia Sufocante): sem save de aplicação — o jogo é
        # o loop por rodada (dano + save que neutraliza), tratado em
        # _processar_venenos_turno. Registra o efeito e retorna.
        if veneno.get("operacao") == "dano":
            alvo.setdefault("efeitos_veneno", [])
            dur = self._rolar_dado(veneno.get("duracao", "1d4"))
            if any(w.get("type") == "veneno_dobrado" for w in alvo.get("weaknesses", [])):
                dur *= 2
                await self.gm_say(f"🧪 **{alvo_nome}** é sensível a venenos — duração dobrada!")
            alvo["efeitos_veneno"].append({
                "nome": nome, "operacao": "dano", "dano": veneno.get("dano", "1d4"),
                "duracao": dur, "save": veneno.get("save", "fortitude"),
                "dificuldade": veneno.get("dificuldade", 10),
                "save_neutraliza_por_rodada": bool(veneno.get("save_neutraliza_por_rodada")),
            })
            await self.gm_say(
                f"💀 **{alvo_nome}** é envenenado por **{nome}** — 1d4 de dano por "
                f"rodada (até {dur} rodada(s); Fortitude CD {veneno.get('dificuldade',10)} neutraliza)!")
            return
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_veneno_agonia.py`
Expected: PASS — seções [1], [2], [6] OK.

- [ ] **Step 5: Commit**

```bash
git add server.py tools/test_veneno_agonia.py
git commit -m "feat(veneno): _aplicar_veneno registra veneno de dano (sem save de aplicacao)"
```

---

### Task 3: Tick de dano + save-por-rodada em `_processar_venenos_turno`

**Files:**
- Modify: `server.py` — `_processar_venenos_turno` (topo do loop `for efeito in ...`, ANTES do `efeito["duracao"] -= 1`, server.py:~11099-11100)
- Test: `tools/test_veneno_agonia.py`

- [ ] **Step 1: Adicionar os testes [3]/[4]/[5]**

```python
    # ── [3] Tick — falha no save: sofre 1d4 e continua ─────────────────────────
    print("\n[3] tick — falha")
    def _efeito_dano(dur=3):
        return {"nome": "Agonia Sufocante", "operacao": "dano", "dano": "1d4",
                "duracao": dur, "save": "fortitude", "dificuldade": 14,
                "save_neutraliza_por_rodada": True}
    r = setup()
    m = make_monster(r, "m1", 4, 4, hp=40)
    m["efeitos_veneno"] = [_efeito_dano(3)]
    r._testar_save = lambda *a, **k: (False, 1, 0, 1)   # falha
    hp0 = m["hp"]
    await r._processar_venenos_turno(m)
    check("falha: sofreu 1..4 de dano", 1 <= (hp0 - m["hp"]) <= 4)
    ef = [e for e in m.get("efeitos_veneno", []) if e.get("operacao") == "dano"]
    check("falha: efeito continua", len(ef) == 1)
    check("falha: duracao decrementou p/ 2", ef and ef[0]["duracao"] == 2)

    # ── [4] Tick — sucesso no save: neutraliza sem dano ────────────────────────
    print("\n[4] tick — sucesso")
    r = setup()
    m = make_monster(r, "m1", 4, 4, hp=40)
    m["efeitos_veneno"] = [_efeito_dano(3)]
    r._testar_save = lambda *a, **k: (True, 20, 0, 20)   # sucesso
    hp0 = m["hp"]
    await r._processar_venenos_turno(m)
    check("sucesso: sem dano", m["hp"] == hp0)
    check("sucesso: efeito removido", not [e for e in m.get("efeitos_veneno", []) if e.get("operacao") == "dano"])

    # ── [5] Duração: expira em `duracao` rodadas falhando sempre ───────────────
    print("\n[5] duração expira")
    r = setup()
    m = make_monster(r, "m1", 4, 4, hp=100)
    m["efeitos_veneno"] = [_efeito_dano(2)]
    r._testar_save = lambda *a, **k: (False, 1, 0, 1)   # falha sempre
    await r._processar_venenos_turno(m)   # duracao 2→1
    await r._processar_venenos_turno(m)   # duracao 1→0 (expira)
    check("expira após `duracao` rodadas", not [e for e in m.get("efeitos_veneno", []) if e.get("operacao") == "dano"])
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_veneno_agonia.py`
Expected: FAIL — o efeito de dano é tratado pelo fluxo genérico (só decrementa
duração, sem aplicar dano nem save por rodada).

- [ ] **Step 3: Adicionar o ramo de dano no topo do loop de `_processar_venenos_turno`**

Em `_processar_venenos_turno`, DENTRO do `for efeito in alvo.get("efeitos_veneno", []):`
e como PRIMEIRA coisa do corpo do loop (antes do `efeito["duracao"] -= 1`,
server.py:~11100), adicione:

```python
            # Veneno de DANO com save-por-rodada (Agonia Sufocante): trata aqui e
            # segue (não usa o decremento/reversão genérico de efeitos de atributo).
            if efeito.get("operacao") == "dano":
                if efeito.get("save_neutraliza_por_rodada"):
                    ok, _d20, _sb, _st = self._testar_save(
                        alvo, efeito.get("save", "fortitude"), efeito.get("dificuldade", 10))
                    if ok:
                        await self.gm_say(
                            f"☑️ **{alvo_nome}** neutraliza **{efeito.get('nome','veneno')}**!")
                        continue   # remove o efeito (não entra em `restantes`)
                dano = self._rolar_dado(efeito.get("dano", "1d4"))
                # _dano_em_alvo já narra o dano (evita narração dupla, como no tick
                # de em_chamas/ácido); a flavor do veneno aparece só no neutralizar.
                await self._dano_em_alvo(alvo, dano, "veneno", None)
                efeito["duracao"] -= 1
                if efeito["duracao"] > 0 and (alvo.get("alive") or alvo.get("hp", 0) > 0):
                    restantes.append(efeito)
                continue
```

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_veneno_agonia.py`
Expected: PASS — seções [1]-[6] OK.

- [ ] **Step 5: Rodar a regressão de venenos/monstros**

Run: `python tools/test_devorador.py`
Expected: passa (o novo ramo `operacao=="dano"` não afeta corrosão nem os venenos
de atributo).

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_veneno_agonia.py
git commit -m "feat(veneno): tick de dano + save-por-rodada em _processar_venenos_turno"
```

---

### Task 4: Cliente — entrada de catálogo

**Files:**
- Modify: `src/gameState.js` — `CATALOGO_ITENS` (junto dos outros venenos, ~linha 577)
- Test: manual

- [ ] **Step 1: Adicionar a entrada no `CATALOGO_ITENS`**

Logo após a entrada `veneno_polvo_abissal` em `CATALOGO_ITENS`, adicione (formato
dos outros venenos):

```javascript
    veneno_agonia_sufocante: {
      id:'veneno_agonia_sufocante', nome:'Agonia Sufocante', tipo:'veneno', loja:'mercado', preco:40, icone:'💀',
      permitidoPara:['todos'],
      efeito:{ operacao:'dano', dano:'1d4', duracao:'1d4', save:'fortitude', dificuldade:14 },
      descricao:'LENDÁRIO. Untado na arma: 1d4 de dano por rodada por até 1d4 rodadas. A cada rodada, Fortitude CD 14 neutraliza o veneno.'
    },
```

- [ ] **Step 2: Verificar sintaxe**

Run: `node --check src/gameState.js`
Expected: sem erros.

- [ ] **Step 3: Commit**

```bash
git add src/gameState.js
git commit -m "feat(veneno): cliente — entrada de catalogo da Agonia Sufocante"
```

---

### Task 5: Verificação end-to-end

**Files:** nenhum

- [ ] **Step 1: Suíte do servidor**

Run: `python tools/test_veneno_agonia.py`
Run: `python tools/test_devorador.py`
Run: `python tools/test_arremessaveis.py`
Expected: todos `0 FALHAS` / `0 XX`.

- [ ] **Step 2: Syntax check do cliente**

Run: `node --check src/gameState.js`
Expected: sem erros.

- [ ] **Step 3: Verificação manual (`iniciar.bat`)**

Compre a Agonia Sufocante (💀) no mercado e, numa masmorra:
1. Clique direito nela → unta na arma (mensagem de veneno na arma)
2. Acerte um monstro corpo a corpo → ele é envenenado
3. No início do turno do monstro, ele testa Fortitude CD 14: **falha** → toma 1d4 e continua; **sucesso** → neutraliza (mensagem), sem mais dano
4. O veneno some após no máximo 1d4 rodadas mesmo sem passar no save
5. Mortos-vivos/esqueletos → imunes (mensagem)
6. Os outros 5 venenos seguem funcionando (untar, reduzir atributo, etc.)

- [ ] **Step 4: Commit final (se houver ajustes)**

```bash
git add -A
git commit -m "chore(veneno): ajustes da verificacao da Agonia Sufocante"
```

---

## Self-review (cobertura do spec)

- ✅ Entrada `VENENOS` + loja `coat_poison` → Task 1.
- ✅ `operacao:"dano"` em `_aplicar_veneno` (sem save de aplicação; imunidade morto-vivo mantida) → Task 2.
- ✅ Tick de dano + `save_neutraliza_por_rodada` (sucesso encerra, falha 1d4 + continua) + limite de duração → Task 3.
- ✅ Genéricos (operacao dano + save por rodada reusáveis) → Tasks 2, 3.
- ✅ Cliente reusa a entrega dos venenos (só catálogo) → Task 4.
- ✅ Regressão dos venenos de atributo + `test_devorador.py` → Tasks 2, 3, 5.

**Fora de escopo (confirmado):** tornar a Agonia arremessável, indicador visual do
status de veneno-de-dano, novos venenos além da Agonia.
```
