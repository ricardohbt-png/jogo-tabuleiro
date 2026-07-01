# Ficha — Ícones de Arma e Armadura com Totais Efetivos

**Data:** 2026-06-21
**Branch sugerida:** `feat/ficha-arma-armadura-totais`
**Escopo:** Ficha do próprio herói (`#my-stats`) apenas.

---

## 1. Objetivo

Na ficha do personagem, os dois ícones lado a lado — **⚔ ARMA** e **🛡 ARMADURA** —
devem mostrar valores **efetivos finais**, somando todos os modificadores ativos,
em vez de apenas dado-da-arma + atributo (arma) e CA-base (armadura).

Comportamentos pedidos:

- **⚔ ARMA:** dano da arma somado a **todos** os modificadores ativos (bônus de
  atributo, de magia, de armas mágicas), apresentado como **uma expressão
  consolidada**. Habilidades que **multiplicam** o dano ou **adicionam um dado**
  aparecem neste marcador. Ao passar o mouse sobre o ícone, o mapa destaca em
  **quadrados vermelhos** o alcance da arma equipada.
- **🛡 ARMADURA:** valor **total** da CA efetiva — base + bônus de magia
  (positivos/negativos) + efeitos temporários (enquanto durarem) + itens mágicos +
  qualquer modificador. O valor exibido é o **resultado final**, com **badges
  inline** por modificador ativo (e contador de turnos para os temporários).

---

## 2. Decisões de produto (confirmadas)

| Tema | Decisão |
|---|---|
| Formato do dano | **Uma expressão combinada** — `1d8 +6`; dados extras viram termos (`+1d8`); multiplicadores viram sufixo (`×2`). |
| Quais bônus entram no número principal | **Sempre-ativos + toggles ativos** (atributo, arma mágica, item, e buffs ATUALMENTE ativos: Golpe Sagrado, Canção, Saciado). **Exclui** aleatoriedade por rolagem (crítico ×2). |
| Quadrados de alcance (hover) | **Reutilizar a prévia existente** (respeita linha de visão), ligá-la ao ícone ⚔ ARMA e **corrigir armas de alcance** (Lança/Alabarda mostram 2 casas; Cajado Chebyshev 1) em vez de só as 4 adjacentes. |
| Detalhe da CA | **Total + badges inline** por modificador ativo, com contador de turnos nos temporários. |
| Armas mágicas | Incluir **buffs de magia** existentes agora (`mods_magia.dano`) + **ponto de extensão** limpo para um futuro campo `+N` de item. **Não** criar sistema de item mágico nesta tarefa. |
| Onde aplicar | **Somente a ficha própria** (`#my-stats`). Overlay de outros heróis e mini-cards ficam como estão. |
| Onde vive a lógica | **Servidor autoritativo** computa e envia o breakdown; cliente apenas renderiza (+ overlay client-only para skills armadas). |

---

## 3. Arquitetura

### 3.1 Princípio: fonte única da verdade

O número exibido **nunca pode mentir** em relação ao dano realmente rolado / à CA
realmente usada. Por isso:

- O **servidor** (`server.py`), que já possui toda a regra de bônus
  (`_player_effective_ac` e a pilha de dano em `handle_attack`), computa o
  breakdown e o envia no payload do jogador.
- O **cliente** (`game.js`) apenas **renderiza** o que o servidor enviou.
- A única exceção são as **skills armadas do warrior** (Golpe Devastador ×2, etc.),
  que só existem como estado do cliente até o ataque ser enviado. Essas o cliente
  sobrepõe — conjunto **disjunto** do conjunto sustentado do servidor, então não há
  dupla contagem.

### 3.2 Pilha de dano real (referência — `handle_attack`)

Bônus **plano** num acerto armado (hoje):

```
stat_bonus            # mod(atributo da arma); finesse = max(FOR, DES)
+ surv_mod            # saciado +1 / exaustão -1 ou -2
+ cancao_dano         # Canção Heroica (suprimida em Silêncio)
+ gl_dano             # Guerreiro da Luz (toggle Richard)
+ _mod_magia(p,"dano")# Arma Mágica / Abençoar (tem rodadas)
- _corrosao_arma_pen  # arma de madeira corroída (persistente)
```

Dados **extras / multiplicadores**:

- Golpe Devastador (`skill_dobrar_dano`): **dado ×2** — armado por ataque (cliente).
- Golpe Sagrado (`golpe_sagrado_ativo`): **+1d8** (×2 vs morto-vivo/demônio) — sustentado (servidor).
- Ataque Furtivo (rogue, `_verificar_ataque_furtivo`): **+Nd4** — condicional ao alvo.
- Crítico: ×2 — aleatório por rolagem. **Excluído** do display.
- Munição incendiária: +dado de fogo — situacional por projétil. Fora de escopo do número.

### 3.3 CA efetiva real (referência — `_player_effective_ac`)

```
p["ac"]                      # base (inclui armadura/escudo/atributo já embutidos)
+ temp_def                   # def. temporária (temp_def_turnos = duração)
+ _cancao_bonus(p,"bonus_ca")# Canção (toggle)
+ guerreiro_luz ca           # Guerreiro da Luz (toggle)
+ _mod_magia(p,"ca")         # magia (mods_magia.rodadas = duração)
- _corrosao_ca_pen           # corrosão de armadura (persistente)
```

---

## 4. Mudanças no servidor (`server.py`)

### 4.1 Helper puro de dano

Extrair a matemática **sustentada** de dano de `handle_attack` para:

```python
def _weapon_damage_breakdown(self, p):
    """Breakdown de dano SUSTENTADO (sem alvo) p/ exibir na ficha.
    handle_attack chama o mesmo helper p/ o cálculo plano — uma fonte só."""
```

Retorno (dict):

```python
{
  "die": "1d8",            # str do dado da arma, ou None (desarmado → base 1)
  "stat": "str_",          # atributo usado (ou "finesse")
  "flat_bonus": 6,         # soma plana sustentada (ver 3.2; inclui hook +N futuro)
  "extra_dice": [          # dados extras SUSTENTADOS
     {"die": "1d8", "label": "Golpe Sagrado", "note": "dobra vs morto-vivo"}
  ],
  "conditionals": [        # passivas condicionais (NÃO entram no número principal)
     {"text": "+Nd4 furtivo", "note": "se aliado adjacente ao alvo ou invisível"}
  ]
}
```

`handle_attack` passa a obter `flat_bonus` desse helper (mesmo código), garantindo
que display == rolagem. A duplicação dos dados (rolagem aleatória) permanece em
`handle_attack`; o helper só descreve a estrutura.

**Ponto de extensão de arma mágica:** `flat_bonus` soma `weapon.get("dano_bonus", 0)`
(campo inexistente hoje → 0). Quando um item mágico definir `dano_bonus`, entra
automaticamente, sem refatorar.

### 4.2 CA efetiva + breakdown no payload

No serializador do jogador (onde `ac` já é enviado), adicionar:

```python
"effective_ac": self._player_effective_ac(p),
"ac_breakdown": [ {"label": ..., "value": ..., "turns": <opcional>}, ... ],
"weapon_damage": self._weapon_damage_breakdown(p),
```

`ac_breakdown` (apenas entradas com valor ≠ 0; base sempre presente):

| label | value | turns |
|---|---|---|
| Base | `p["ac"]` | — |
| Magia | `_mod_magia(p,"ca")` | `mods_magia.rodadas` |
| Temporário | `temp_def` | `temp_def_turnos` (ou 1) |
| Canção | `_cancao_bonus(p,"bonus_ca")` | — (toggle) |
| Guerreiro da Luz | `gl ca` | — (toggle) |
| Corrosão | `-_corrosao_ca_pen(p)` | — (persistente) |

O servidor é a fonte de `turns` — sem timers no cliente.

---

## 5. Mudanças no cliente

### 5.1 `gameState.js` — lógica pura de alcance

Mover/alocar o cálculo de **forma de alcance** (hoje `_computeWeaponRangeTiles` em
`game.js`) para um helper puro `GS.weaponRangeTiles(state, me)` — respeitando a
regra "lógica em gameState, render em game.js". Ele:

- Lê `state.tiles`, `state.explored`, usa `GS.hasLineOfSight`.
- **Ranged** (`weapon.range != null`): Chebyshev ≤ range **com linha de visão**.
- **Lança** (`reach === "lanca"`): 2 ortogonais em linha reta / 1 diagonal
  (espelha `_lanca_no_alcance_jogador`).
- **Cajado** (`reach === "cajado"`): Chebyshev 1, incluindo diagonais.
- **Melee com `range` explícito** (ex.: Chicote 2, Alabarda 2): Chebyshev ≤ range
  com linha de visão.
- **Melee padrão:** 4 casas ortogonais adjacentes (comportamento atual).

### 5.2 `game.js` — ícone ⚔ ARMA

- `dmgFmt` passa a vir de `me.weapon_damage`:
  - Principal: `${die} ${flat_bonus>=0?'+':''}${flat_bonus}` (desarmado: `1 ±N`).
  - Dados extras sustentados: anexa ` +1d8` por entrada de `extra_dice`.
  - Multiplicador client-only: se Golpe Devastador estiver **armado**
    (`GS.getWarriorSelected()` contém o id), anexa ` ×2`.
  - Condicionais (`conditionals`): exibidas como termo/badge marcado (ex.: `+Nd4*`),
    com tooltip/nota — **fora** do número principal.
  - Cor: leve realce dourado quando o total estiver acima do base (algum buff ativo).
- Remover os tags coloridos separados antigos (`_cancaoTag('bonus_dano')`,
  `_richardTag('dano')`, `_golpeSagradoTag()`) do ícone, já que agora estão
  consolidados — Golpe Sagrado vira um termo `+1d8` da expressão.
- **Hover de alcance:** adicionar `mouseenter`/`mouseleave` no `.equip-item` da arma
  (o que contém `#weapon-canvas`) setando `window._weaponRangePreview` e chamando
  `renderMap` — idêntico aos handlers já existentes no slot de inventário
  (`game.js` ~9077). Funciona em 2D e 3D (a prévia já cobre ambos).

### 5.3 `game.js` — ícone 🛡 ARMADURA

- Headline: `CA ${me.effective_ac}` (em vez de `me.ac`).
- Badges inline a partir de `me.ac_breakdown` (pular a entrada Base):
  - Formato: `<sinal><valor>` + `(<turns>t)` quando houver `turns`.
  - Ex.: `✨+2 (2t)` (magia), `🎵+1` (canção), `🗡−1` (corrosão).
  - Valores negativos em vermelho; positivos em dourado/azul.
- Remover os tags antigos `_cancaoTag('bonus_ca')` / `_richardTag('ca')` do headline
  da CA (agora cobertos pelos badges).

---

## 6. Casos de borda

- **Desarmado:** `die = None` → base 1 + FOR; expressão `1 ±N`. Sem dados extras de arma.
- **Henrique (instrumento, sem dado):** trata como desarmado para o número (já é o caso hoje).
- **Silêncio:** Canção suprimida → servidor já zera `_cancao_bonus`; badge/termo some sozinho.
- **Corrosão destruiu a arma:** `_corrosao_arma_pen` retorna 0 (vira soco); breakdown reflete soco.
- **Sem buffs:** breakdown = die + stat apenas; nenhum badge de CA além de Base; cor neutra.
- **Hover sem arma equipada:** não mostra alcance (guard `if(!weapon) return`).

---

## 7. Não-objetivos (YAGNI)

- Nenhum novo sistema de itens mágicos (apenas o hook `dano_bonus`/`ac_bonus`).
- Sem alterar overlay de outros heróis nem mini-cards.
- Sem exibir crítico nem dano de munição no número.
- Sem mudar a mecânica real de combate — apenas exposição/exibição.

---

## 8. Verificação

- Servidor: `_weapon_damage_breakdown` e `handle_attack` produzem o mesmo
  `flat_bonus` para um mesmo estado (teste/inspeção manual).
- Cliente (preview): ficha do mago/clérigo/guerreiro mostra expressão consolidada;
  ativar Canção/Golpe Sagrado/Abençoar muda o número e os badges; hover na arma
  pinta os quadrados vermelhos corretos (melee adjacente, lança 2 casas, arco raio).
- Conferir CA: aplicar def. temporária (mago) e ver badge com contador de turnos
  decrescendo a cada rodada.
