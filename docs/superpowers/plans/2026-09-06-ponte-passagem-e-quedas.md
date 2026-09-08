# Ponte como passagem e quedas só por empurrão — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A ponte passa a derivar a própria altura do terreno (nunca mais fica no fundo do vão), e nenhum movimento voluntário — de herói, monstro, servo, prisioneiro ou licantropo — pode terminar em queda; só o empurrão derruba.

**Architecture:** Duas fontes únicas de verdade. `_ponte_altura(ponte)` deriva a altura da menor das duas pontas, lendo a elevação **crua**; `_queda_no_passo(criatura, origem, destino)` responde "este passo terminaria em queda?" e é usada pelos DOIS lados — pelo novo portão `_passo_seguro`, que recusa o passo antes de mover, e pela `_aplicar_queda_terreno`, que aplica o dano quando o deslocamento é forçado. O cliente espelha `_queda_no_passo` em `_walkable` para o azul bater com o servidor.

**Tech Stack:** Python 3 (`server.py`, sem framework), JavaScript vanilla (`src/gameState.js`, `tools/editor.js`), testes caseiros (`tools/test_*.py` com `check()`, `tools/test_*.js` com `node`).

**Spec:** `docs/superpowers/specs/2026-09-06-ponte-passagem-e-quedas-design.md`

---

## Contexto que o implementador precisa saber

**Como rodar um teste:** `python tools/test_x.py` ou `node tools/test_x.js`, sempre **da raiz** do projeto. Não há pytest nem jest — cada arquivo é um script que imprime `✅`/`❌` e termina com um resumo. O padrão é:

```python
PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")
```

**Armadilha 1 — o servidor rodando trava a escrita.** Se houver um `python server.py` ativo na porta 8765, gravar `server.py` ou `game.js` pode estourar `OSError: [Errno 22] Invalid argument`. É transitório: repita a gravação. Ao editar com ferramenta, se falhar, tente de novo.

**Armadilha 2 — chave de `self.elevacoes` é TUPLA no servidor** (`(x, y)`) e **STRING no cliente** (`"x,y"`). Não são intercambiáveis.

**Armadilha 3 — NÃO COMMITE NADA.** O autor tem trabalho não commitado espalhado por `server.py`, `game.js`, `tools/editor.js` e `dungeons/caverna_vulcanica.json`. `git add server.py` adiciona o arquivo **INTEIRO**, WIP dele junto — listar o caminho exato não protege nada quando o arquivo já está sujo. Isto foi tentado e desfeito: um commit levou 671 linhas de `server.py` que não eram desta tarefa.

**Deixe todo o trabalho no working tree.** O autor commita o que quiser, quando quiser. Nenhuma tarefa deste plano commita.

**Estado atual, já medido (não re-investigar):** o servidor já permite platô→ponte→platô e já recusa desnível maior que 1; a névoa já revela a ponte; `pontes` já viaja no `game_state`; o BFS do cliente já trata casa de ponte como piso. As 12 geometrias (vertical/horizontal × largura 1/2/3 × vão parede/chão) já atravessam. O único caso quebrado é `altura` desatualizada.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta mudança |
|---|---|
| `server.py` | `_elevacao_bruta`, `_ponte_altura`, `_queda_no_passo`, `_passo_seguro`; apertar 4 portões; remover 9 quedas voluntárias |
| `src/gameState.js` | `_quedaNoPasso` + uso em `_walkable` (espelho do servidor) |
| `tools/editor.js` | `bridgeAltura` derivada; usar no desenho, no salvar e no validador |
| `tools/test_ponte_passagem.py` | **novo** — altura derivada, portões, e a garantia de que o empurrão continua derrubando |
| `tools/test_elevacao_rampa.js` | estender — matriz de 12 geometrias + paridade servidor/cliente |

---

## Task 1: Altura da ponte derivada do terreno

**Files:**
- Create: `tools/test_ponte_passagem.py`
- Modify: `server.py` (perto de `_rebuild_pontes_index`, ~linha 13111)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_ponte_passagem.py` com o conteúdo abaixo. Ele monta uma sala sem passar pelo `__init__` (padrão já usado em `tools/test_modo_mestre.py`) porque só precisa do índice de pontes.

```python
"""Ponte como passagem e quedas só por empurrão.
Roda da raiz: python tools/test_ponte_passagem.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sala(elev_esq=3, elev_dir=3, altura_json=0, transicao="rampa", vao_parede=True):
    """Dois platôs separados por um vão na coluna x=5, ponte de (4,5) a (6,5).

    `altura_json` é o valor GRAVADO no arquivo — o defeito real do editor era
    gravar 0 aqui quando a ponte nasce antes de o autor pintar a elevação.
    """
    W = H = 11
    r = S.GameRoom.__new__(S.GameRoom)
    r.map_w, r.map_h = W, H
    r.tiles = [[S.FLOOR] * W for _ in range(H)]
    if vao_parede:
        for y in range(H):
            r.tiles[y][5] = S.WALL
    r.elevacoes = {}
    for y in range(H):
        for x in range(W):
            if x < 5:   r.elevacoes[(x, y)] = elev_esq
            elif x > 5: r.elevacoes[(x, y)] = elev_dir
    r.decorations = []; r.materiais = {}
    r._decor_block_tiles = set(); r._mat_solid_tiles = set()
    r._decor_tall_tiles = set(); r._mat_oclui_tiles = set()
    r.monsters = {}; r.players = {}; r.prisoner = None
    r.explored = set(); r.rooms = []
    # Filas efêmeras do feedback visual. São criadas no __init__, e uma fixture
    # de __new__ não as tem — sem elas `_dano_em_alvo` estoura AttributeError
    # em `_damage_visual_context` assim que o teste [7] empurra alguém. Já foi
    # a causa de várias suítes vermelhas no projeto; esta fixture foi rodada
    # contra o código atual antes de entrar no plano.
    r._combat_damage_events = []; r._positive_effect_events = []
    r._resistance_events = []; r._damage_visual_context = {}
    r.transicao_altura = transicao
    r.pontes = [{"id": "p1", "inicio": [4, 5], "fim": [6, 5],
                 "largura": 1, "altura": altura_json}]
    r._rebuild_pontes_index()
    return r

print("\n[1] A altura da ponte vem do TERRENO, não do JSON")
r = sala(altura_json=0)
check("ponte com altura 0 no arquivo assume a elevação dos platôs (3)",
      r._ponte_alturas[(5, 5)] == 3)
check("o valor derivado é gravado de volta, para o payload sair certo",
      r.pontes[0]["altura"] == 3)
check("_elevacao_terreno concorda com o índice",
      r._elevacao_terreno(5, 5) == 3)

print("\n[2] Pontas divergentes usam a MAIS BAIXA")
r2 = sala(elev_esq=3, elev_dir=4, altura_json=9)
check("pontas 3 e 4 resolvem para 3", r2._ponte_alturas[(5, 5)] == 3)
r3 = sala(elev_esq=4, elev_dir=2, altura_json=0)
check("pontas 4 e 2 resolvem para 2", r3._ponte_alturas[(5, 5)] == 2)

print("\n[3] A superfície da ponte é plana")
r4 = sala(altura_json=0)
check("todas as casas da ponte têm a mesma altura",
      len({r4._ponte_alturas[t] for t in r4._ponte_tiles}) == 1)

print("\n" + "=" * 62)
print(f"  {PASS} passaram, {FAIL} falharam")
print("=" * 62)
sys.exit(1 if FAIL else 0)
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_ponte_passagem.py`
Expected: FAIL — `ponte com altura 0 no arquivo assume a elevação dos platôs (3)` falha, porque `_rebuild_pontes_index` ainda lê `ponte.get("altura", 0)` e devolve 0.

- [ ] **Step 3: Implementar a derivação**

Em `server.py`, **logo antes** de `def _rebuild_pontes_index(self):` (~linha 13111), acrescentar os dois helpers:

```python
    def _elevacao_bruta(self, x, y):
        """Elevação AUTORADA da casa, sem consultar pontes.

        A ponte não pode descobrir a própria altura por `_elevacao_terreno`:
        aquela lê `_ponte_alturas`, que é justamente o índice sendo construído.
        Usar a versão crua quebra a dependência circular.
        """
        try:
            return max(ELEVACAO_TERRENO_MIN,
                       min(ELEVACAO_TERRENO_MAX,
                           int(getattr(self, "elevacoes", {}).get((int(x), int(y)), 0))))
        except (TypeError, ValueError):
            return 0

    def _ponte_altura(self, ponte):
        """Altura da superfície da ponte: a MAIS BAIXA das duas pontas.

        DERIVADA, nunca lida do JSON. O campo `altura` que o editor grava é um
        snapshot do momento da criação e não acompanha a pintura de elevação
        posterior: quem criava a ponte antes de levantar os platôs ficava com
        ela deitada no fundo do vão, e nenhuma casa dela entrava no alcance.
        A ponta mais alta vira um degrau comum — de 1, transponível; de 2 ou
        mais, bloqueado pela regra de passo.
        """
        inicio = ponte.get("inicio") or ponte.get("start") or [0, 0]
        fim = ponte.get("fim") or ponte.get("end") or inicio
        try:
            return min(self._elevacao_bruta(inicio[0], inicio[1]),
                       self._elevacao_bruta(fim[0], fim[1]))
        except (TypeError, ValueError, IndexError):
            return 0
```

Depois, **dentro** de `_rebuild_pontes_index`, trocar o bloco que lê a altura. De:

```python
        for ponte in getattr(self, "pontes", []) or []:
            try:
                altura = int(ponte.get("altura", 0))
            except (TypeError, ValueError):
                altura = 0
```

Para:

```python
        for ponte in getattr(self, "pontes", []) or []:
            altura = self._ponte_altura(ponte)
            # Grava de volta: `_serializar_pontes` emite este campo, e é dele
            # que o cliente tira a altura em `_elevacaoTerreno`. Sem isto o
            # servidor andaria certo e o azul do cliente continuaria errado.
            ponte["altura"] = altura
```

- [ ] **Step 4: Rodar até passar**

Run: `python tools/test_ponte_passagem.py`
Expected: PASS — todas as linhas `✅` e `0 falharam`. (Não crave o número total: o projeto já teve teste vermelho por cravar contagem de itens que cresceram depois.)

- [ ] **Step 5: Provar que a masmorra real do autor continua correta**

Run:
```bash
python -c "import sys,os; sys.path.insert(0,'.'); import json,server as S; d=json.load(open('dungeons/caverna_vulcanica.json',encoding='utf-8')); print('ponte no arquivo:', d['pontes'][0])"
```
Expected: mostra `'altura': 3`. Esse arquivo já está correto; o teste garante que um arquivo ERRADO passa a ser corrigido na carga.

- [ ] **Step 6: NÃO commitar**

Deixe as mudanças no working tree (ver Armadilha 3). Se algum dia forem
commitadas, a mensagem sugerida é:

```
fix(ponte): derivar a altura do terreno em vez de ler o snapshot do JSON

O campo `altura` era gravado na criacao da ponte e nunca acompanhava a
pintura de elevacao posterior: criar a ponte antes de levantar os platos
deixava ela no fundo do vao, e nenhuma casa dela entrava no alcance.
Agora a altura e derivada da menor das duas pontas, na carga.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

---

## Task 2: `_queda_no_passo` como fonte única, e o portão `_passo_seguro`

**Files:**
- Modify: `server.py` — `_aplicar_queda_terreno` (~linha 26850) e perto de `_passo_elevacao_permitido` (~linha 13184)
- Test: `tools/test_ponte_passagem.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar ao fim de `tools/test_ponte_passagem.py`, **antes** do bloco que imprime o resumo:

```python
print("\n[4] _queda_no_passo: a mesma pergunta que a queda faz, feita ANTES de mover")
r = sala(altura_json=0)                      # platôs 3, ponte 3, vão 0
heroi = {"id": "h", "name": "H", "class_id": "warrior", "alive": True,
         "hp": 10, "pos": [4, 5], "altura": 0}
check("plano não é queda",            r._queda_no_passo(heroi, [3, 5], [4, 5]) is False)
check("subir não é queda",            r._queda_no_passo(heroi, [3, 4], [3, 5]) is False)
check("sair da ponte para o vão é queda",
      r._queda_no_passo(heroi, [5, 5], [5, 4]) is True)

# Degrau de 1 fora da ponte: seguro no modo rampa, queda no modo declive.
rr = sala(elev_esq=3, elev_dir=2, altura_json=0, vao_parede=False)
check("descer 1 fora da ponte NÃO é queda (rampa)",
      rr._queda_no_passo(heroi, [4, 5], [6, 5]) is False)
rd = sala(elev_esq=3, elev_dir=2, altura_json=0, vao_parede=False, transicao="declive")
check("descer 1 fora da ponte É queda (declive)",
      rd._queda_no_passo(heroi, [4, 5], [6, 5]) is True)

print("\n[5] _passo_seguro = permitido pela elevação E sem queda")
r = sala(altura_json=0)
check("platô -> ponte é seguro",   r._passo_seguro(heroi, [4, 5], [5, 5]) is True)
check("ponte -> platô é seguro",   r._passo_seguro(heroi, [5, 5], [6, 5]) is True)
check("ponte -> vão lateral NÃO é seguro",
      r._passo_seguro(heroi, [5, 5], [5, 4]) is False)
rd = sala(elev_esq=3, elev_dir=2, altura_json=0, vao_parede=False, transicao="declive")
check("declive: descer 1 deixa de ser oferecido",
      rd._passo_seguro(heroi, [4, 5], [6, 5]) is False)
check("declive: o EMPURRÃO que desce 1 continua sendo queda",
      rd._queda_no_passo(heroi, [4, 5], [6, 5]) is True)

print("\n[6] Voo continua isento")
voador = {"id": "v", "name": "V", "class_id": "mage", "alive": True,
          "hp": 10, "pos": [5, 5], "altura": 2, "voo": True}
r = sala(altura_json=0)
check("quem voa acima do solo não sofre queda de terreno",
      r._queda_no_passo(voador, [5, 5], [5, 4]) is False)
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_ponte_passagem.py`
Expected: FAIL com `AttributeError: 'GameRoom' object has no attribute '_queda_no_passo'`

- [ ] **Step 3: Extrair `_queda_no_passo` de `_aplicar_queda_terreno`**

Em `server.py`, dentro de `_aplicar_queda_terreno`, substituir o bloco de decisão. De:

```python
        if not alvo or self._voo_imune_terreno(alvo):
            return None
        if not (isinstance(origem, (list, tuple)) and len(origem) >= 2
                and isinstance(destino, (list, tuple)) and len(destino) >= 2):
            return None
        nivel_origem = self._elevacao_terreno(*origem[:2])
        nivel_destino = self._elevacao_terreno(*destino[:2])
        queda = nivel_origem - nivel_destino
        if queda <= 0:
            return None
        # Sair da lateral de uma ponte é uma queda mesmo quando a diferença
        # seria de apenas um nível. A regra de rampa vale para o piso comum;
        # a ponte não possui rampa lateral.
        saiu_da_ponte = (self._ponte_em(origem[0], origem[1])
                         and not self._ponte_em(destino[0], destino[1]))
        if (getattr(self, "transicao_altura", "rampa") == "rampa"
                and queda <= 1 and not saiu_da_ponte):
            return None
```

Para:

```python
        if not self._queda_no_passo(alvo, origem, destino):
            return None
        nivel_origem = self._elevacao_terreno(*origem[:2])
        nivel_destino = self._elevacao_terreno(*destino[:2])
        queda = nivel_origem - nivel_destino
```

- [ ] **Step 4: Criar os dois métodos novos**

Em `server.py`, **logo depois** de `_passo_elevacao_permitido` (~linha 13188), acrescentar:

```python
    def _queda_no_passo(self, criatura, origem, destino):
        """Este deslocamento de uma casa terminaria em queda por desnível?

        FONTE ÚNICA da regra de queda por terreno. É consultada nos dois
        sentidos: `_passo_seguro` a usa para RECUSAR o passo voluntário antes
        de mover, e `_aplicar_queda_terreno` a usa para decidir se aplica o
        dano quando o deslocamento é FORÇADO (empurrão). Duplicar a regra nos
        dois lugares faria o azul do cliente e o dano do servidor divergirem no
        primeiro ajuste de balanceamento.
        """
        if not criatura or self._voo_imune_terreno(criatura):
            return False
        if not (isinstance(origem, (list, tuple)) and len(origem) >= 2
                and isinstance(destino, (list, tuple)) and len(destino) >= 2):
            return False
        queda = (self._elevacao_terreno(*origem[:2])
                 - self._elevacao_terreno(*destino[:2]))
        if queda <= 0:
            return False
        # Sair da lateral de uma ponte é queda mesmo com desnível de 1: a
        # ponte não tem rampa lateral. A regra de rampa vale para o piso comum.
        saiu_da_ponte = (self._ponte_em(origem[0], origem[1])
                         and not self._ponte_em(destino[0], destino[1]))
        if (getattr(self, "transicao_altura", "rampa") == "rampa"
                and queda <= 1 and not saiu_da_ponte):
            return False
        return True

    def _passo_seguro(self, criatura, origem, destino, facing_destino=None):
        """Portão do movimento VOLUNTÁRIO: permitido pela elevação E sem queda.

        Movimento voluntário nunca derruba ninguém. Onde o passo terminaria em
        queda ele simplesmente não é oferecido — antes, o jogador clicava numa
        casa e caía, o que é erro de jogo, não decisão. Queda por desnível
        passa a existir só quando alguém é EMPURRADO: `_empurrar` nunca
        consultou este portão e continua sem consultá-lo.
        """
        if not self._passo_elevacao_permitido(criatura, origem, destino,
                                              facing_destino):
            return False
        return not self._queda_no_passo(criatura, origem, destino)
```

- [ ] **Step 5: Rodar até passar**

Run: `python tools/test_ponte_passagem.py`
Expected: PASS — `0 falharam`

- [ ] **Step 6: Provar que nada de queda regrediu**

Run: `python tools/test_voo_altura.py && python tools/test_queda_altura.py`
Expected: ambos PASS. Eles cobrem a tabela de dano de queda e o alcance vertical; `_aplicar_queda_terreno` mudou de forma, não de comportamento.

- [ ] **Step 7: NÃO commitar**

Deixe as mudanças no working tree (ver Armadilha 3). Se algum dia forem
commitadas, a mensagem sugerida é:

```
refactor(queda): extrair _queda_no_passo e criar o portao _passo_seguro

_aplicar_queda_terreno passa a consultar _queda_no_passo em vez de decidir
inline. A mesma pergunta agora pode ser feita ANTES de mover, que e o que
_passo_seguro faz. Sem mudanca de comportamento ainda: os portoes so passam
a usar _passo_seguro na proxima tarefa.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

---

## Task 3: Apertar os portões e remover as quedas voluntárias

Os nove caminhos voluntários passam por **quatro** funções de validação. Apertar as quatro cobre os nove.

**Files:**
- Modify: `server.py` — linhas 13730, 16234, 21923, 21995, 29502, 29957 (portões) e 13747, 16336, 17073, 21949, 21999, 22830, 29539, 31061, 36647 (quedas a remover)
- Test: `tools/test_ponte_passagem.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `tools/test_ponte_passagem.py`, antes do resumo:

```python
import inspect, re

print("\n[7] O empurrão CONTINUA derrubando (a prova de que não cortamos demais)")
# `_empurrar` é testável sozinho: não exige turno, iniciativa nem push_state.
# É de propósito o único caminho que ainda chama _aplicar_queda_terreno.
r = sala(altura_json=0)
r.round_num = 1
async def noop(*a, **k): pass
r.broadcast = noop; r.send_to = noop; r.gm_say = noop
async def _dado(q, f, label=None): return q * f
r._rolar_dano_mostrado = _dado
h = {"id": "h", "name": "H", "class_id": "warrior", "alive": True, "hp": 40,
     "max_hp": 40, "pos": [5, 5], "altura": 0, "resistances": []}
r.players = {"h": h}
asyncio.run(r._empurrar(h, 0, -1, 1))
check("empurrar da ponte para o vão custa HP", h["hp"] < 40)

print("\n[8] Os portões usam _passo_seguro")
for nome in ("handle_move", "_tile_livre_para_animado", "_passo_monstro",
             "_commit_monster_step", "_monster_can_occupy",
             "_passo_livre_licantropo"):
    corpo = inspect.getsource(getattr(S.GameRoom, nome))
    check(f"{nome} usa _passo_seguro", "_passo_seguro" in corpo)

print("\n[9] Nenhum caminho VOLUNTÁRIO aplica queda")
# Varredura estática: `await self._aplicar_queda_terreno` só pode sobrar dentro
# de _empurrar. Um `await` novo em qualquer outro lugar reabre o defeito —
# jogador caindo num clique — e nenhum teste de comportamento pegaria os nove
# caminhos de uma vez.
fonte = inspect.getsource(S)
chamadas = [m.start() for m in re.finditer(r"await self\._aplicar_queda_terreno", fonte)]
corpo_empurrar = inspect.getsource(S.GameRoom._empurrar)
check("sobraram exatamente 2 chamadas de queda", len(chamadas) == 2)
check("as 2 estão dentro de _empurrar",
      corpo_empurrar.count("await self._aplicar_queda_terreno") == 2)
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `python tools/test_ponte_passagem.py`
Expected: FAIL — os seis checks do `[8]` falham (nenhum portão usa `_passo_seguro` ainda) e o `[9]` acusa 11 chamadas de queda em vez de 2.

- [ ] **Step 3: Trocar os quatro portões**

Todas as trocas são de `_passo_elevacao_permitido` para `_passo_seguro`, **mantendo os argumentos**.

`server.py:13730` (dentro de `handle_move`):
```python
        if not voo_livre and not self._passo_seguro(p, p["pos"], [nx, ny]):
```

`server.py:16234` (dentro de `_tile_livre_para_animado` — cobre servos e prisioneiro):
```python
            if not self._passo_seguro(criatura, origem, [nx, ny]):
                return False
```

`server.py:21995` (dentro de `_passo_monstro`):
```python
                    and self._passo_seguro(m, m["pos"], [nx, ny], [adx, ady]):
```

`server.py:29502` (dentro de `_commit_monster_step` — cobre IA e o mestre no manual):
```python
        if not self._passo_seguro(m, [old_x, old_y], [nx, ny], step_facing):
```

`server.py:29957` (dentro de `_monster_can_occupy` — cobre `_monster_move_step` e o BFS de alcance do mestre):
```python
        if from_anchor is not None and not self._passo_seguro(m, from_anchor, [ax, ay], facing):
            return False
```

- [ ] **Step 4: Dar um portão ao licantropo**

`_passo_livre_licantropo` (~linha 21923) não valida elevação nenhuma hoje. Acrescentar a checagem **antes** do `return` final:

```python
    def _passo_livre_licantropo(self, p, nx, ny):
        if p.get("rodamoinho_preso") or p.get("rodamoinho_profundo_preso"): return False
        if not (0 <= nx < self.map_w and 0 <= ny < self.map_h): return False
        if self.tiles[ny][nx] == WALL and not self._is_illusion_wall(nx, ny) and not self._ponte_em(nx, ny): return False
        if (self._is_closed_door(nx, ny) and not self._ponte_em(nx, ny)) or self._blocks_tile(nx, ny): return False
        if any(m.get("hp", 0) > 0 and [nx, ny] in self._monster_tiles(m) for m in self.monsters.values()): return False
        if any(q.get("alive") and q["id"] != p["id"] and q.get("pos") == [nx, ny] for q in self.players.values()): return False
        # Perda de controle não é empurrão: a forma lupina anda sozinha, mas
        # não se joga de um penhasco. Sem este portão ela seria o único
        # caminho voluntário capaz de matar por queda.
        if not self._passo_seguro(p, p["pos"], [nx, ny]): return False
        return not self._animado_em([nx, ny])
```

- [ ] **Step 5: Remover as nove quedas de caminho voluntário**

Apagar a linha `await self._aplicar_queda_terreno(...)` — e **só ela** — nestes nove pontos. As linhas seguintes (`if not p.get("alive"): ...`) ficam: são baratas e continuam corretas caso a criatura morra por outra via no mesmo passo.

| linha (antes das edições) | função | linha a apagar |
|---|---|---|
| 13747 | `handle_move` | `await self._aplicar_queda_terreno(p, old_pos, p["pos"])` |
| 16336 | `handle_comandar_animados` | `await self._aplicar_queda_terreno(a, frm, a["pos"], p.get("id"))` |
| 17073 | `handle_mover_animado` | `await self._aplicar_queda_terreno(a, old_pos, a["pos"], pid)` |
| 21949 | `_turno_licantropo` | `await self._aplicar_queda_terreno(p, antes, p["pos"])` |
| 21999 | `_passo_monstro` | `await self._aplicar_queda_terreno(m, origem, m["pos"])` |
| 22830 | `_animado_ataca_jogador` | `await self._aplicar_queda_terreno(a, antes, a["pos"])` |
| 29539 | `_commit_monster_step` | `await self._aplicar_queda_terreno(m, [old_x, old_y], m["pos"])` |
| 31061 | `_monster_move_step` | `await self._aplicar_queda_terreno(m, frm, m["pos"])` |
| 36647 | `handle_mover_prisioneiro` | `await self._aplicar_queda_terreno(pr, old_pos, pr["pos"], pid)` |

**Não tocar** nas duas chamadas dentro de `_empurrar` (~23667 e ~23677). São a única fonte de queda que sobra.

Depois de apagar, confirme:

Run: `grep -n "await self._aplicar_queda_terreno" server.py`
Expected: exatamente **2** linhas, ambas dentro de `_empurrar`. É a mesma invariante que o check `[9]` cobra.

- [ ] **Step 6: Rodar até passar**

Run: `python tools/test_ponte_passagem.py`
Expected: PASS — `0 falharam`

- [ ] **Step 7: Rodar as suítes que tocam movimento**

Run: `python tools/test_voo_altura.py && python tools/test_queda_altura.py && python tools/test_modo_mestre.py && python tools/test_agarrao.py && python tools/test_objetivos.py`
Expected: todos PASS. `test_modo_mestre` e `test_agarrao` exercitam `_commit_monster_step`, que mudou de portão.

- [ ] **Step 8: NÃO commitar**

Deixe as mudanças no working tree (ver Armadilha 3). Se algum dia forem
commitadas, a mensagem sugerida é:

```
feat(movimento): passo voluntario nunca termina em queda

Os nove caminhos de deslocamento passo-a-passo (heroi, IA, mestre manual,
servos, prisioneiro, licantropo) passam pelos quatro portoes, que agora
exigem _passo_seguro; o passo que cairia deixa de ser oferecido em vez de
ser permitido-com-dano. _empurrar segue intocado e continua derrubando.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

---

## Task 4: O cliente espelha a regra

Sem isto o azul ofereceria casas que o servidor recusa — o jogador clica e nada acontece.

**Files:**
- Modify: `src/gameState.js` — perto de `_custoElevacao` (~linha 953) e `_walkable` (~linha 961)
- Test: `tools/test_elevacao_rampa.js`

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar ao fim de `tools/test_elevacao_rampa.js`, **antes** do bloco de resumo:

```js
// ── Paridade com o servidor: o azul não pode oferecer o que o servidor recusa ──
console.log("\n[7] O BFS do cliente respeita a regra de passo seguro");
global.window = {};
global.localStorage = { getItem: () => null, setItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");

const FLOOR = 1, WALL = 0, W = 15, H = 15;

// Dois platôs de altura 3 com um fosso de 2 casas; ponte cruzando.
function cenario({ vertical, largura, vaoParede, transicao = "rampa" }) {
  const tiles = [];
  for (let y = 0; y < H; y++) tiles.push(new Array(W).fill(FLOOR));
  const elevacoes = {};
  const noFosso = (x, y) => vertical ? (y === 6 || y === 7) : (x === 6 || x === 7);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    if (noFosso(x, y)) { elevacoes[`${x},${y}`] = 0; if (vaoParede) tiles[y][x] = WALL; }
    else elevacoes[`${x},${y}`] = 3;
  }
  const inicio = vertical ? [8, 5] : [5, 8];
  const fim    = [8, 8];
  const bt = [];
  if (inicio[1] === fim[1]) {
    const y0 = inicio[1] - Math.floor(largura / 2);
    for (let y = y0; y < y0 + largura; y++)
      for (let x = Math.min(inicio[0], fim[0]); x <= Math.max(inicio[0], fim[0]); x++) bt.push([x, y]);
  } else {
    const x0 = inicio[0] - Math.floor(largura / 2);
    for (let x = x0; x < x0 + largura; x++)
      for (let y = Math.min(inicio[1], fim[1]); y <= Math.max(inicio[1], fim[1]); y++) bt.push([x, y]);
  }
  const explored = [];
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) explored.push([x, y]);
  const hx = vertical ? inicio[0] : inicio[0] - 1;
  const hy = vertical ? inicio[1] - 1 : inicio[1];
  GS.injectPreviewState({
    type: "game_state", master_pid: null,
    players: [{ id: "p1", name: "H", class_id: "warrior", alive: true,
                pos: [hx, hy], altura: 0, moves_left: 12, spd: 12 }],
    monsters: [], tiles, rooms: [], explored, round: 1, current_turn: "p1",
    elevacoes, materiais: {}, decorations: [],
    pontes: [{ id: "b", inicio, fim, largura, altura: 3, tiles: bt }],
    transicao_altura: transicao,
  });
  const st = GS.gameState;
  const res = new Set();
  GS.bfsReachable(st.tiles, new Set(explored.map(([x, y]) => `${x},${y}`)),
    hx, hy, 12, res,
    { materiais: st.materiais, elevacoes: st.elevacoes, state: st, actor: st.players[0] });
  const ox = vertical ? fim[0] : fim[0] + 1;
  const oy = vertical ? fim[1] + 1 : fim[1];
  return { res, bt, outroLado: res.has(`${ox},${oy}`) };
}

// as 12 geometrias atravessam
let atravessam = 0, total = 0;
for (const vertical of [true, false])
  for (const largura of [1, 2, 3])
    for (const vaoParede of [false, true]) {
      total++;
      if (cenario({ vertical, largura, vaoParede }).outroLado) atravessam++;
    }
check(`as ${total} geometrias de ponte atravessam (${atravessam}/${total})`,
      atravessam === total);

// o fosso ao lado da ponte NUNCA entra no alcance
const c = cenario({ vertical: true, largura: 1, vaoParede: false });
check("fosso ao lado da ponte fica fora do alcance",
      !c.res.has("7,6") && !c.res.has("9,6"));

// modo declive: descer 1 nível andando deixa de ser oferecido
const tiles2 = [];
for (let y = 0; y < H; y++) tiles2.push(new Array(W).fill(FLOOR));
const elev2 = {};
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) elev2[`${x},${y}`] = x < 5 ? 3 : 2;
const explored2 = [];
for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) explored2.push([x, y]);
function alcanceDegrau(transicao) {
  GS.injectPreviewState({
    type: "game_state", master_pid: null,
    players: [{ id: "p1", name: "H", class_id: "warrior", alive: true,
                pos: [4, 5], altura: 0, moves_left: 6, spd: 6 }],
    monsters: [], tiles: tiles2, rooms: [], explored: explored2, round: 1,
    current_turn: "p1", elevacoes: elev2, materiais: {}, decorations: [],
    pontes: [], transicao_altura: transicao,
  });
  const st = GS.gameState;
  const res = new Set();
  GS.bfsReachable(st.tiles, new Set(explored2.map(([x, y]) => `${x},${y}`)),
    4, 5, 6, res,
    { materiais: st.materiais, elevacoes: st.elevacoes, state: st, actor: st.players[0] });
  return res;
}
check("rampa: descer 1 degrau continua no alcance",
      alcanceDegrau("rampa").has("5,5"));
check("declive: descer 1 degrau sai do alcance",
      !alcanceDegrau("declive").has("5,5"));
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `node tools/test_elevacao_rampa.js`
Expected: FAIL em `declive: descer 1 degrau sai do alcance` — o cliente ainda não conhece `transicao_altura`.

- [ ] **Step 3: Implementar o espelho**

Em `src/gameState.js`, **logo depois** de `_custoElevacao` (~linha 958), acrescentar:

```js
  // Espelho de `_queda_no_passo` do server.py. Existe para o azul não oferecer
  // casa que o servidor recusaria: o jogador clicaria e nada aconteceria, sem
  // explicação — pior que o defeito original. Movimento voluntário nunca cai;
  // queda por desnível só por empurrão, que não passa por aqui.
  function _quedaNoPasso(moveCtx, fromX, fromY, x, y) {
    const actor = moveCtx?.actor || {};
    if (actor.voo && alturaDe(actor) > 0) return false;
    const queda = _elevacaoTerreno(fromX, fromY, moveCtx)
                - _elevacaoTerreno(x, y, moveCtx);
    if (queda <= 0) return false;
    const estado = moveCtx?.state || gameState;
    // A ponte não tem rampa lateral: sair dela é queda mesmo com desnível 1.
    const saiuDaPonte = _ponteEm(fromX, fromY, estado) && !_ponteEm(x, y, estado);
    const modo = estado?.transicao_altura || 'rampa';
    if (modo === 'rampa' && queda <= 1 && !saiuDaPonte) return false;
    return true;
  }
```

Depois, em `_walkable`, trocar a linha do custo. De:

```js
    if (fromX != null && fromY != null && _custoElevacao(moveCtx, fromX, fromY, x, y) > 1) return false;
```

Para:

```js
    if (fromX != null && fromY != null
        && (_custoElevacao(moveCtx, fromX, fromY, x, y) > 1
            || _quedaNoPasso(moveCtx, fromX, fromY, x, y))) return false;
```

- [ ] **Step 4: Rodar até passar**

Run: `node tools/test_elevacao_rampa.js`
Expected: PASS

- [ ] **Step 5: Verificar sintaxe e as suítes de cliente**

Run: `node --check src/gameState.js && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js && node tools/test_tutorial_cliente.js`
Expected: todos PASS

- [ ] **Step 6: NÃO commitar**

Deixe as mudanças no working tree (ver Armadilha 3). Se algum dia forem
commitadas, a mensagem sugerida é:

```
feat(cliente): o alcance azul espelha a regra de passo seguro

_walkable passa a recusar o passo que terminaria em queda, usando os mesmos
criterios de _queda_no_passo no servidor (transicao_altura e saida lateral
de ponte, ambos ja no game_state). Sem isto o azul ofereceria casa que o
servidor recusa.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

---

## Task 5: O editor deriva a altura da ponte

Fecha a origem do defeito: o editor deixa de gravar um valor que envelhece.

**Files:**
- Modify: `tools/editor.js` — novo `bridgeAltura` (depois de `bridgeTilesOf`, ~1392), `placeBridge` (~1406), serialização do salvar (~3007)

O validador (~3213) **não muda**: ele já avisa `ponte X liga alturas diferentes` quando as pontas divergem, e essa continua sendo a única situação que merece aviso — a ponte agora se ajusta sozinha ao terreno.

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar ao fim de `tools/test_elevacao_rampa.js`, antes do resumo:

```js
console.log("\n[8] O editor deriva a altura da ponte, não a congela");
const editorSrc = semComentarios(fs.readFileSync(path.join(raiz, "tools/editor.js"), "utf8"));
check("editor.js tem um helper bridgeAltura", /function\s+bridgeAltura\s*\(/.test(editorSrc));
check("placeBridge usa o helper em vez de elevationAt cru",
      /placeBridge[\s\S]{0,400}altura:\s*bridgeAltura\(/.test(editorSrc));
check("a serialização também deriva",
      /pontes:\s*S\.pontes\.map[\s\S]{0,200}altura:\s*bridgeAltura\(/.test(editorSrc));
```

- [ ] **Step 2: Rodar para ver falhar**

Run: `node tools/test_elevacao_rampa.js`
Expected: FAIL nos três checks do `[8]`.

- [ ] **Step 3: Criar o helper e usá-lo**

Em `tools/editor.js`, **logo depois** de `bridgeTilesOf` (~linha 1392), acrescentar:

```js
  // Altura da superfície da ponte: a MAIS BAIXA das duas pontas, derivada na
  // hora. O campo `altura` deixou de ser fonte de verdade — gravá-lo na
  // criação e nunca atualizar era o que deixava a ponte no fundo do vão
  // quando o autor pintava a elevação depois de traçá-la.
  function bridgeAltura(bridge) {
    const a = bridge?.inicio, b = bridge?.fim || a;
    if (!Array.isArray(a) || !Array.isArray(b)) return 0;
    return Math.min(elevationAt(a[0], a[1]), elevationAt(b[0], b[1]));
  }
```

Em `placeBridge` (~1409), trocar:
```js
    S.pontes.push({ id: "ponte_" + S.nextPonteId++, inicio: drag.start, fim: drag.end,
      largura: drag.width, altura: bridgeAltura({ inicio: drag.start, fim: drag.end }) });
```

Na serialização do salvar (~3007), trocar:
```js
      pontes: S.pontes.map(p => ({ id: p.id, inicio: p.inicio.slice(), fim: p.fim.slice(),
        largura: p.largura | 0, altura: bridgeAltura(p) })),
```

- [ ] **Step 4: Rodar até passar**

Run: `node tools/test_elevacao_rampa.js`
Expected: PASS

- [ ] **Step 5: Verificar sintaxe do editor**

Run: `node --check tools/editor.js`
Expected: sem saída (sintaxe válida)

- [ ] **Step 6: NÃO commitar**

Deixe as mudanças no working tree (ver Armadilha 3). Se algum dia forem
commitadas, a mensagem sugerida é:

```
fix(editor): derivar a altura da ponte ao criar e ao salvar

bridgeAltura() calcula a menor das duas pontas na hora, em vez de congelar o
valor no momento do traco. Fecha a origem do defeito: pintar a elevacao
depois de criar a ponte deixava ela no fundo do vao.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

---

## Task 6: Verificação final

- [ ] **Step 1: Rodar a bateria inteira**

Run:
```bash
for f in tools/test_*.py; do python "$f" >/dev/null 2>&1 || echo "VERMELHA: $f"; done
for f in tools/test_*.js; do node "$f" >/dev/null 2>&1 || echo "VERMELHA: $f"; done
```
Expected: nenhuma linha `VERMELHA`. A baseline antes deste plano é **127/127 verde** — qualquer vermelha aqui é regressão desta mudança.

**Atenção:** não rode a bateria enquanto edita arquivos. `test_devorador` já apareceu vermelho em execução concorrente e passa 171/0 isolado.

- [ ] **Step 2: Verificar no jogo de verdade**

Parar o servidor antigo (ele carrega a masmorra na entrada e pode ser de antes das mudanças), subir de novo, entrar na `caverna_vulcanica` e conferir:
1. as casas da ponte ficam azuis a partir do platô;
2. o alcance atravessa para o platô de baixo;
3. o fosso ao lado da ponte nunca fica azul;
4. andar até a borda da ponte e tentar sair pela lateral não é oferecido.

Run: `node --check game.js && python -c "import ast;ast.parse(open('server.py',encoding='utf-8').read());print('ok')"`
Expected: `ok`

- [ ] **Step 3: Relatar, sem commitar**

Deixe tudo no working tree e relate o estado ao orquestrador.

---

## Cobertura do spec

| Requisito do spec | Tarefa |
|---|---|
| Altura derivada, ponta mais baixa | Task 1 |
| `_serializar_pontes` emite o derivado; cliente não muda | Task 1, Step 3 |
| Masmorra antiga corrigida na carga, sem migração | Task 1, teste `[1]` |
| Superfície plana | Task 1, teste `[3]` |
| `_passo_seguro` = elevação permitida E sem queda | Task 2 |
| `_queda_no_passo` como fonte única | Task 2, Step 3 |
| Nove caminhos voluntários sem queda | Task 3 |
| `_empurrar` intocado e ainda derrubando | Task 3, teste `[7]` |
| Licantropo incluído | Task 3, Step 4 |
| Cliente espelha | Task 4 |
| Editor deriva | Task 5 |
| Matriz de 12 geometrias | Task 4, teste `[7]` |
| Paridade servidor/cliente | Task 4 (declive) + Task 6, Step 2 |
| Voo isento | Task 2, teste `[6]` |
| Empurrão em `declive` ainda derruba | Task 2, teste `[5]` |
| Nenhuma queda sobra fora de `_empurrar` | Task 3, teste `[9]` |
