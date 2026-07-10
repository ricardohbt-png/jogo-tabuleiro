# Sub-projeto D — Arremessáveis Táticos (Cola e Rede)

**Data:** 2026-07-10
**Status:** aprovado (brainstorming)

## Contexto

Quarto sub-projeto da família de arremessáveis do mercado (ver memória
`arremessaveis-roadmap`). **A** (fogo single-target), **B** (área com save) e **C**
(ácido) já estão mergeados. Este spec cobre os dois itens **táticos de controle**:
Cola Alquímica e Rede — arremesso single-target (teste de ataque por DES) **sem
dano**, que aplicam controle a um monstro.

## Infraestrutura existente reaproveitada

- **`_throw_item_alvo`** (Sub-projeto A): caminho single-target (mira vermelha,
  teste de ataque por DES vs CA, LOS/alcance, item consumido em acerto E erro,
  efeitos declarativos por campo do catálogo). Hoje ele **exige** `defn["dano"]`;
  será ajustado para tornar o dano **opcional** (itens de controle não têm dano).
- **`_save_mostrado(alvo, tipo, cd)`**: teste de resistência com animação de dado;
  monstros resolvem `reflexos`/`fortitude`/`vontade`. **Não há save de "Força" cru**
  no engine.
- **Loop de turno do monstro** (~server.py:14458-14491): trata petrificado /
  paralisado / `perde_turno` / status de magia (`_status_monstro_turno`) antes de
  despachar a IA (`_run_monster_ai`). É o ponto de hook dos dois status novos.
- **`m["movement"]`**: orçamento de passos do monstro, lido em ~20 sites da IA.

## Decisões de design

1. **Ação principal**; item consumido em acerto E erro; **sem dano**.
2. **Cola → `mov_reduzido`:** no acerto, o alvo testa **Reflexos CD 12**; falha →
   movimento reduzido à metade por 2 rodadas, **mas o monstro ainda ataca**.
3. **Rede → `enredado`:** no acerto, o monstro fica preso (sem save de resistência
   na chegada); escapar = gastar o turno num teste de **Fortitude CD 12**
   (mapeamento **Força→Fortitude**, pois o engine não tem save de Força cru).
4. Cola: **reaplicar renova a duração** (não corta o movimento de novo / não
   empilha).
5. Status resetam sozinhos por masmorra (monstros são recriados). A Cola restaura
   `m["movement"]` na expiração.

## Componentes

### 1. Catálogo + loja (`server.py`)

Duas entradas em `ARREMESSAVEIS` (`alvo:"ataque_alvo"`, `alcance:4`, **sem `dano`**),
com um campo `controle`:

```python
"cola_alquimica": {
    "id": "cola_alquimica", "name": "Cola Alquímica", "emoji": "🟢",
    "alcance": 4, "alvo": "ataque_alvo",
    "controle": {"tipo": "mov_reduzido",
                 "resist_save": {"tipo": "reflexos", "cd": 12}, "duracao": 2},
},
"rede_arremesso": {
    "id": "rede_arremesso", "name": "Rede", "emoji": "🕸️",
    "alcance": 4, "alvo": "ataque_alvo",
    "controle": {"tipo": "enredado",
                 "escape_save": {"tipo": "fortitude", "cd": 12}},
},
```

Duas entradas em `SHOP_MERCHANT` (`effect:"throwable"`), preços 15 / 18.

### 2. `_throw_item_alvo` — dano opcional + controle (`server.py`)

- Tornar o dano **opcional** no ramo de acerto: só rola/aplica dano se
  `defn.get("dano")`. Para itens de controle (sem `dano`), narrar o acerto e seguir
  para o efeito.
- Após os efeitos existentes (em_chamas / ácido), adicionar:
  ```python
  ctrl = defn.get("controle")
  if ctrl and target.get("hp", 0) > 0:
      await self._aplicar_controle_arremesso(target, ctrl)
  ```

### 3. Helper `_aplicar_controle_arremesso(alvo, ctrl)` (`server.py`)

```
tipo = ctrl["tipo"]
if tipo == "mov_reduzido":
    rs = ctrl.get("resist_save")
    if rs:
        ok, *_ = _save_mostrado(alvo, rs["tipo"], rs["cd"])
        if ok: gm_say("<alvo> se esquiva da cola!"); return
    dur = ctrl.get("duracao", 2)
    if not alvo.get("mov_reduzido_rodadas"):          # 1ª aplicação: corta pela metade
        alvo["mov_reduzido_orig"] = alvo.get("movement", 5)
        alvo["movement"] = max(1, alvo["mov_reduzido_orig"] // 2)
    alvo["mov_reduzido_rodadas"] = max(alvo.get("mov_reduzido_rodadas", 0), dur)  # renova
    gm_say("<alvo> fica preso na cola — movimento reduzido!")
elif tipo == "enredado":
    es = ctrl.get("escape_save", {"tipo": "fortitude", "cd": 12})
    alvo["enredado"] = True
    alvo["enredado_save"] = es["tipo"]     # guarda tipo/CD do save de escape
    alvo["enredado_cd"]   = es["cd"]
    gm_say("<alvo> fica preso na rede!")
```

### 4. Hooks no turno do monstro (`server.py`, ~14458-14491)

- **Enredado (escape):** junto dos checks de petrificado/`perde_turno`, antes do
  `_status_monstro_turno`:
  ```python
  if m.get("enredado"):
      passou, *_ = await self._save_mostrado(
          m, m.get("enredado_save", "fortitude"), m.get("enredado_cd", 12))
      if passou:
          m["enredado"] = False
          m.pop("enredado_save", None); m.pop("enredado_cd", None)
          gm_say("<m> se solta da rede!")
      else:
          gm_say("<m> continua preso na rede!")
      continue   # o turno é gasto tentando escapar (sucesso ou falha)
  ```
- **Mov_reduzido (tick/expiração):** em `_status_monstro_turno` (onde `lento_rodadas`
  já tica), adicionar (NÃO retorna "pulou" — só reduz movimento):
  ```python
  if m.get("mov_reduzido_rodadas", 0) > 0:
      m["mov_reduzido_rodadas"] -= 1
      if m["mov_reduzido_rodadas"] <= 0 and "mov_reduzido_orig" in m:
          m["movement"] = m.pop("mov_reduzido_orig")
          gm_say("<m> se solta da cola — movimento normal.")
  ```

> O corte de `m["movement"]` na aplicação + restauração na expiração evita tocar
> nos ~20 sites que leem `m["movement"]`, e a IA lê o valor já reduzido
> automaticamente.

### 5. Cliente (`src/gameState.js`)

- Duas entradas em `CATALOGO_ITENS` (`arremessavel:true`, `alvo:"ataque_alvo"`,
  `alcance:4`, **`permitidoPara:['todos']`**, tooltip do efeito). **Sem UI nova** —
  reusa a mira vermelha single-target do Sub-projeto A.

### 6. Imagens

- `assets/itens/cola_alquimica.png` / `assets/itens/rede_arremesso.png`
  (convenção `assets/itens/<id>.png`, fallback emoji 🟢 / 🕸️).

### 7. Itens (loja/mercado)

| Item | id | Emoji | Alcance | Ataque | Efeito | Preço |
|---|---|---|---|---|---|---|
| Cola Alquímica | `cola_alquimica` | 🟢 | 4 | DES vs CA | Reflexos CD 12; falha → mov ½ por 2 rodadas | 15 🪙 |
| Rede | `rede_arremesso` | 🕸️ | 4 | DES vs CA | preso; escapar = Fortitude CD 12 (gasta a ação) | 18 🪙 |

### 8. Testes (`tools/test_arremessaveis_tatico.py`)

- **Cola:** acerto + falha no Reflexos → `movement` cai à metade + `mov_reduzido_rodadas`
  setado; sucesso no Reflexos → sem efeito; expiração (tick) restaura o `movement`
  original; reaplicar renova a duração sem cortar de novo.
- **Rede:** acerto → `enredado`; no turno, Fortitude falha → continua preso (turno
  gasto); sucesso → solta (`enredado` limpo, turno gasto).
- **Erro** (CA alta, d20 fixo) → item consumido, sem efeito.
- Regressão: A (`test_arremessaveis.py`), B (`test_arremessaveis_area.py`) e C
  (`test_arremessaveis_acido.py`) seguem verdes (o dano opcional em `_throw_item_alvo`
  não pode quebrar os itens com dano).

## Fora de escopo (deste sub-projeto)

- Veneno Agonia Sufocante (Sub-projeto E).
- Indicador visual do status (cola/rede) sobre o monstro (YAGNI; os status
  serializam no `game_state`, dá pra adicionar depois).
- Efeito da Cola/Rede em jogadores (só se aplica a monstros, como todo
  `_throw_item_alvo`).
- Save de "Força" cru (mapeado para Fortitude).
