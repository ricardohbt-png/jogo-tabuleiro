# Tutorial guiado — Fatia 1 (mecanismo) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar às lições do Campo de Treinamento um modelo de passos (`guia`), mensagens de avanço de passo e um halo pulsante nos elementos do HUD, sem mudar as regras de conclusão das lições.

**Architecture:** O servidor continua autoritativo. Cada lição ganha o campo opcional `guia` (lista de passos). Sem `guia`, o servidor gera um passo único a partir da tarefa. O passo atual de cada herói fica em `p["licao_passo"]`, vai no payload da `fala` e em `licao_passo`. O cliente ganha um módulo puro `src/guiaTutorial.js` (parse do alvo, seletor CSS, nível de dica por tempo) e o `game.js` desenha o halo e a janela com "Passo i de n".

**Tech Stack:** Python (`server.py`, `unittest`), JavaScript sem bundler (`src/gameState.js`, `src/guiaTutorial.js`, `game.js`), testes em node.

**Spec:** `docs/superpowers/specs/2026-10-07-tutorial-guiado-design.md`. Este plano cobre só a **fatia 1** da seção 10 da spec.

**Fora desta fatia (planos próprios depois):** halo no tabuleiro 2D/3D (`casa`, `monstro`, `porta`, `bolsa`, `slot`), caminho tracejado até a porta, dica por erro (`licao_dica`), `licao_resultado`, glossário, reescrita das 62 lições, editor de masmorras, remoção das seções [10]+ do `test_tutorial.py`.

**Desvios da spec, de propósito:** (1) a dica de nível 2 aparece como linha na janela da lição, não como balão; (2) o halo do HUD é um anel pulsante, sem seta (a seta vem com o halo do tabuleiro); (3) `conclui_com` usa o vocabulário `LICAO_VERBOS` já existente. Armar uma habilidade é uma ação só do cliente (sem evento no servidor), então um passo que ensina a armar é **informativo** (sem `conclui_com`) e o jogador o avança com "Entendi".

## Regras do repositório que valem para todas as tarefas

- `game.js`, `server.py` e `CLAUDE.md` usam **CRLF**. Use a ferramenta Edit; um script Python com `replace("...\n...")` não casa.
- Antes de cada commit, rode `git status --short` e `git diff --stat <arquivo>`. Se um arquivo que você tocou tiver mudanças que não são suas (o autor edita em paralelo), não use `git add` no arquivo inteiro: monte o commit só com os seus trechos (veja `memory/commit-por-tema-wip-misturado.md`).
- Nunca toque em `savegames/`, `accounts/` ou `groups/` reais.
- Não faça push; só quando o autor pedir.
- Um `GS.on('evento')` substitui o ouvinte anterior do mesmo evento. Registre um só por evento.
- Em `game.js`, não declare variável local chamada `t` (sombreia o tradutor) e não chame `t()` no nível de módulo.
- Texto de interface novo sempre por `t('ui.tutorial.<slug>')`, com `pt` e `en`.

## File Structure

| Arquivo | Responsabilidade |
|---|---|
| `server.py` | Constantes e validação do `guia`; helpers `_guia_*`; avanço de passo em `_licao_evento`; handler `avancar_passo`; campo `licao_passo` |
| `src/guiaTutorial.js` (novo) | Puro: `parseUi`, `seletor`, `nivelDica`, `textoDica`. Sem DOM nem `window` além do export |
| `src/gameState.js` | Encaminha `licao_passo`; `GS.avancarPasso()`; devolve o passo em `licaoAtual()` |
| `src/lang/tutorial.js` (novo) | Textos `ui.tutorial.*` em pt/en |
| `src/visualConfig.js` | `VC.tutorial` com os tempos das dicas |
| `game.js` | Janela da lição com passos, halo, relógio de dicas, `data-guia` no botão de encerrar turno |
| `game.css` | Estilos da janela com passos e `.guia-halo` |
| `index.html` | Carrega `src/lang/tutorial.js` e `src/guiaTutorial.js` |
| `tools/test_tutorial_guia.py` (novo) | Servidor: validação, derivação, avanço de passo, foto |
| `tools/test_guia_tutorial_cliente.js` (novo) | Node: módulo puro e fiação estática |
| `CLAUDE.md` | Parágrafo sobre o guia do tutorial |

---

### Task 1: Validar o campo `guia` no servidor

**Files:**
- Modify: `server.py` (constantes perto de `LICAO_EFEITOS`, ~linha 60; `validar_dungeon`, depois do bloco de `ordem`, ~linha 7642)
- Create: `tools/test_tutorial_guia.py`

- [ ] **Step 1: Confirmar que `re` já é importado**

Run: `grep -n "^import re\|^import .*\bre\b" server.py | head -3`
Expected: uma linha com `import re` (se não houver, acrescente `import re` junto dos outros imports no topo).

- [ ] **Step 2: Escrever o teste que falha**

Crie `tools/test_tutorial_guia.py`:

```python
"""Guia do tutorial (fatia 1): validação, passos, avanço e foto.

Roda da raiz:  python tools/test_tutorial_guia.py
Dados isolados: monta salas em memória, não escreve saves.
"""
import asyncio
import sys
import unittest
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server as S

D = S.carregar_dungeon('campo_de_treinamento.json')

GUIA_MIRA = [
    {"id": "s1", "texto": "Olhe a barra de habilidades.", "ui": "habilidade:mira_certeira"},
    {"id": "s2", "texto": "Ataque um boneco.", "ui": "monstro:boneco_treino",
     "conclui_com": {"tipo": "atacar", "alvo": "boneco_treino"},
     "dica": ["O boneco está logo à frente.", "Clique nele."]},
    {"id": "s3", "texto": "Arme a Mira e ataque.", "ui": "habilidade:mira_certeira"},
]


def dungeon_com_guia(guia):
    d = deepcopy(D)
    f = next(x for x in d['falas'] if x['id'] == 'treino_mira')
    if guia is not None:
        f['guia'] = guia
    return d


def room(cls='warrior', guia=None):
    r = S.GameRoom('GUIA_TEST')
    p = S.make_player('hero', 'Aluno', cls, 0)
    r.players[p['id']] = p
    r.load_authored_dungeon(dungeon_com_guia(guia))
    r.phase = 'playing'
    r._is_turn = lambda pid: True
    r.messages = []

    async def send(pid, msg): r.messages.append(msg)
    async def broadcast(msg): r.messages.append(msg)
    async def noop(*a, **k): pass
    r.send_to = send; r.broadcast = broadcast; r.gm_say = noop; r.push_state = noop
    return r, p


async def abrir_licao(r, p, ident):
    target = next(f for f in r.licoes if f['id'] == ident)
    done = [f['id'] for f in r.licoes if f.get('classe') == p['class_id']
            and f.get('ordem', 0) < target['ordem']]
    p['licoes_feitas'] = done
    p['licao_progresso'] = {i: 1 for i in done}
    p['licao_atual'] = None
    p['pos'] = list(target['pos'])
    await r._verificar_falas(p, r._room_containing_point(p['pos']))
    if p['licao_atual'] != ident:
        raise AssertionError((ident, p['licao_atual']))


class ValidacaoTests(unittest.TestCase):
    def test_guia_valido_passa(self):
        self.assertEqual(S.validar_dungeon(dungeon_com_guia(deepcopy(GUIA_MIRA))), (True, 'ok'))

    def test_guia_vazio_ou_longo_demais(self):
        ok, _ = S.validar_dungeon(dungeon_com_guia([]))
        self.assertFalse(ok)
        longo = [{"texto": f"p{i}"} for i in range(S.GUIA_MAX_PASSOS + 1)]
        ok, _ = S.validar_dungeon(dungeon_com_guia(longo))
        self.assertFalse(ok)

    def test_passo_sem_texto(self):
        ok, msg = S.validar_dungeon(dungeon_com_guia([{"texto": "  "}]))
        self.assertFalse(ok); self.assertIn("texto", msg)

    def test_ui_invalida(self):
        for ui in ("botao", "xyz:abc", "casa:3,4", "habilidade:Mira Certeira", 5):
            ok, _ = S.validar_dungeon(dungeon_com_guia([{"texto": "a", "ui": ui}]))
            self.assertFalse(ok, ui)
        for ui in ("botao:encerrar_turno", "habilidade:mira_certeira", "casa:[3,4]",
                   "porta:[10,2]", "monstro:boneco_treino", "hud:fome"):
            ok, msg = S.validar_dungeon(dungeon_com_guia([{"texto": "a", "ui": ui}]))
            self.assertTrue(ok, (ui, msg))

    def test_dica_e_conclui_com(self):
        ok, _ = S.validar_dungeon(dungeon_com_guia([{"texto": "a", "dica": ["x", "y", "z"]}]))
        self.assertFalse(ok)
        ok, _ = S.validar_dungeon(dungeon_com_guia([{"texto": "a", "dica": [""]}]))
        self.assertFalse(ok)
        ok, _ = S.validar_dungeon(dungeon_com_guia(
            [{"texto": "a", "conclui_com": {"tipo": "voar"}}]))
        self.assertFalse(ok)
        ok, _ = S.validar_dungeon(dungeon_com_guia([{"texto": "a", "conclui_com": "atacar"}]))
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main(verbosity=2)
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `python tools/test_tutorial_guia.py ValidacaoTests -v`
Expected: erros `AttributeError: module 'server' has no attribute 'GUIA_MAX_PASSOS'` (ou falhas porque o guia inválido passa).

- [ ] **Step 4: Acrescentar as constantes**

Em `server.py`, logo depois de `LICAO_EFEITOS = ("fome", "sede")` (use Edit), acrescente:

```python
# Guia do tutorial: uma lição pode listar PASSOS (`guia`) e cada passo aponta um
# elemento da tela (`ui`). O servidor só valida o formato; quem desenha é o cliente.
GUIA_MAX_PASSOS = 8
GUIA_UI_RE = re.compile(
    r"^(?:(?:botao|habilidade|bolsa|slot|monstro|hud):[a-z0-9_]+"
    r"|(?:casa|porta):\[\d+,\d+\])$")
```

- [ ] **Step 5: Validar o `guia` em `validar_dungeon`**

Em `server.py`, no laço das falas, logo **depois** do bloco `_ord = _f.get("ordem") ... "ordem de lição deve ser um inteiro."` e **antes** de `_tar = _f.get("tarefa")`, acrescente:

```python
        _guia = _f.get("guia")
        if _guia is not None:
            if not isinstance(_guia, list) or not _guia or len(_guia) > GUIA_MAX_PASSOS:
                return False, f"guia da lição deve ser uma lista de 1 a {GUIA_MAX_PASSOS} passos."
            for _ps in _guia:
                if not isinstance(_ps, dict) or not (_ps.get("texto") or "").strip():
                    return False, "passo do guia sem texto."
                _ui = _ps.get("ui")
                if _ui is not None and not (isinstance(_ui, str) and GUIA_UI_RE.match(_ui)):
                    return False, f"ui de passo inválida: {_ui!r}."
                _dica = _ps.get("dica")
                if _dica is not None and (not isinstance(_dica, list) or len(_dica) > 2
                                          or not all(isinstance(d, str) and d.strip() for d in _dica)):
                    return False, "dica de passo deve ser uma lista de até 2 textos."
                _cc = _ps.get("conclui_com")
                if _cc is not None and (not isinstance(_cc, dict) or _cc.get("tipo") not in LICAO_VERBOS):
                    return False, "conclui_com de passo inválido."
```

- [ ] **Step 6: Rodar e ver passar**

Run: `python tools/test_tutorial_guia.py ValidacaoTests -v`
Expected: 5 testes `ok`.

- [ ] **Step 7: Commit**

```bash
git status --short server.py tools/test_tutorial_guia.py
git diff --stat server.py
git add tools/test_tutorial_guia.py server.py
git commit -m "feat(tutorial): valida o campo guia das lições" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Passos, avanço e payload no servidor

**Files:**
- Modify: `server.py` (helpers de módulo perto de `_e_licao`; `make_player` ~linha 10010; `_carregar_licoes`; `_licao_concluir`; `_licao_evento`; `_disparar_fala`; `_tutorial_payload`; despacho `repetir_tutorial` ~linha 47610; novos métodos na classe)
- Test: `tools/test_tutorial_guia.py`

- [ ] **Step 1: Escrever os testes que falham**

Acrescente em `tools/test_tutorial_guia.py`, antes do `if __name__`:

```python
class DerivacaoTests(unittest.TestCase):
    def test_ui_padrao_por_tarefa(self):
        f = S._guia_ui_padrao
        self.assertEqual(f({"tipo": "encerrar_turno"}), "botao:encerrar_turno")
        self.assertEqual(f({"tipo": "usar_habilidade", "alvo": "mira_certeira"}), "habilidade:mira_certeira")
        self.assertEqual(f({"tipo": "usar_tecnica", "alvo": "brutalidade"}), "habilidade:brutalidade")
        self.assertEqual(f({"tipo": "mover_ate", "alvo": [5, 15]}), "casa:[5,15]")
        self.assertEqual(f({"tipo": "abrir_porta", "alvo": [13, 15]}), "porta:[13,15]")
        self.assertEqual(f({"tipo": "atacar", "alvo": "boneco_treino"}), "monstro:boneco_treino")
        self.assertEqual(f({"tipo": "usar_item", "alvo": "racao_viagem"}), "bolsa:racao_viagem")
        self.assertIsNone(f({"tipo": "pegar_item"}))
        self.assertIsNone(f({"tipo": "atacar", "alvo": "Boneco Treino"}))

    def test_passos_sem_guia_gera_um_passo_auto(self):
        lic = {"id": "x", "texto": "Longo.", "tarefa": {"tipo": "encerrar_turno"}}
        passos = S._guia_passos(lic)
        self.assertEqual(len(passos), 1)
        self.assertTrue(passos[0]["auto"])
        self.assertEqual(passos[0]["ui"], "botao:encerrar_turno")

    def test_payload_marca_informativo_e_limita_indice(self):
        lic = {"id": "x", "guia": deepcopy(GUIA_MIRA), "tarefa": {"tipo": "usar_habilidade"}}
        p0 = S._guia_payload(lic, 0)
        self.assertEqual((p0["i"], p0["n"], p0["informativo"]), (0, 3, True))
        p1 = S._guia_payload(lic, 1)
        self.assertFalse(p1["informativo"])
        self.assertEqual(p1["dica"], ["O boneco está logo à frente.", "Clique nele."])
        p9 = S._guia_payload(lic, 9)
        self.assertEqual(p9["i"], 2)
        self.assertFalse(p9["informativo"])


class AvancoTests(unittest.IsolatedAsyncioTestCase):
    async def test_fala_leva_o_passo_0(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        self.assertEqual(p['licao_passo'], 0)
        fala = next(m for m in r.messages if m.get('licao_id') == 'treino_mira')
        self.assertEqual(fala['passo']['i'], 0)
        self.assertEqual(fala['passo']['n'], 3)
        self.assertTrue(fala['passo']['informativo'])

    async def test_sem_guia_a_fala_leva_passo_auto(self):
        r, p = room('warrior', None)
        await abrir_licao(r, p, 'treino_mira')
        fala = next(m for m in r.messages if m.get('licao_id') == 'treino_mira')
        self.assertTrue(fala['passo']['auto'])
        self.assertEqual(fala['passo']['ui'], 'habilidade:mira_certeira')

    async def test_entendi_avanca_so_passo_informativo(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        await r.handle_avancar_passo('hero')
        self.assertEqual(p['licao_passo'], 1)
        msg = [m for m in r.messages if m.get('type') == 'licao_passo'][-1]
        self.assertEqual(msg['passo']['i'], 1)
        self.assertEqual(msg['licao_id'], 'treino_mira')
        await r.handle_avancar_passo('hero')          # passo 1 tem conclui_com: não pula
        self.assertEqual(p['licao_passo'], 1)

    async def test_evento_certo_avanca_e_errado_nao(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        await r.handle_avancar_passo('hero')
        await r._licao_evento(p, 'atacar', alvo='esqueleto_humano')
        self.assertEqual(p['licao_passo'], 1)
        await r._licao_evento(p, 'atacar', alvo='boneco_treino')
        self.assertEqual(p['licao_passo'], 2)

    async def test_ultimo_passo_nao_avanca_sozinho_e_a_tarefa_conclui(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        p['licao_passo'] = 2
        await r.handle_avancar_passo('hero')
        await r._licao_evento(p, 'atacar', alvo='boneco_treino')
        self.assertEqual(p['licao_passo'], 2)
        await r._licao_evento(p, 'usar_habilidade', alvo='mira_certeira')
        self.assertIn('treino_mira', p['licoes_feitas'])
        self.assertNotEqual(p.get('licao_atual'), 'treino_mira')
        self.assertEqual(p['licao_passo'], 0)

    async def test_sem_licao_pendente_nada_acontece(self):
        r, p = room('warrior', None)
        await r.handle_avancar_passo('hero')
        self.assertEqual(p['licao_passo'], 0)
        await r.handle_avancar_passo('nao_existe')

    async def test_tutorial_payload_leva_o_passo(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        bloco = r._tutorial_payload()['por_classe']['warrior']
        self.assertEqual(bloco['passo']['i'], 0)
        p['licao_atual'] = None
        self.assertIsNone(r._tutorial_payload()['por_classe']['warrior']['passo'])

    async def test_passos_sao_por_heroi(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        outro = S.make_player('hero2', 'Outro', 'mage', 1)
        r.players['hero2'] = outro
        await abrir_licao(r, p, 'treino_mira')
        await r.handle_avancar_passo('hero')
        self.assertEqual((p['licao_passo'], outro['licao_passo']), (1, 0))
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_tutorial_guia.py DerivacaoTests AvancoTests -v`
Expected: `AttributeError` para `_guia_ui_padrao`, `_guia_passos`, `_guia_payload`, `handle_avancar_passo`.

- [ ] **Step 3: Helpers de módulo**

Em `server.py`, logo depois da função `_e_licao`, acrescente:

```python
def _guia_ui_padrao(tar):
    """Elemento a destacar quando a lição não declara `guia`: deduzido da tarefa."""
    tipo, alvo = tar.get("tipo"), tar.get("alvo")
    if tipo == "encerrar_turno":
        return "botao:encerrar_turno"
    if tipo in ("mover_ate", "abrir_porta"):
        if isinstance(alvo, (list, tuple)) and len(alvo) == 2:
            return f"{'casa' if tipo == 'mover_ate' else 'porta'}:[{int(alvo[0])},{int(alvo[1])}]"
        return None
    if not isinstance(alvo, str) or not re.fullmatch(r"[a-z0-9_]+", alvo):
        return None
    if tipo in ("usar_habilidade", "usar_tecnica"):
        return f"habilidade:{alvo}"
    if tipo in ("atacar", "matar"):
        return f"monstro:{alvo}"
    if tipo in ("usar_item", "arremessar_item", "equipar"):
        return f"bolsa:{alvo}"
    return None


def _guia_passos(lic):
    """Passos da lição: o `guia` autorado, ou um passo único gerado da tarefa."""
    guia = lic.get("guia")
    if guia:
        return guia
    return [{"id": "auto", "texto": lic.get("texto", ""), "auto": True,
             "ui": _guia_ui_padrao(lic.get("tarefa") or {})}]


def _guia_payload(lic, i):
    """Passo `i` no formato que o cliente recebe (índice preso ao intervalo)."""
    passos = _guia_passos(lic)
    i = max(0, min(int(i or 0), len(passos) - 1))
    s = passos[i]
    return {"id": s.get("id"), "texto": s.get("texto", ""), "porque": s.get("porque", ""),
            "ui": s.get("ui"), "dica": list(s.get("dica") or []),
            "auto": bool(s.get("auto")), "i": i, "n": len(passos),
            "informativo": i < len(passos) - 1 and not s.get("conclui_com")}
```

- [ ] **Step 4: Campo `licao_passo`**

Em `make_player`, depois da linha `"licoes_feitas": [],  ...`, acrescente (Edit):

```python
        "licao_passo": 0,           # índice do passo atual da lição pendente (guia)
```

Em `_carregar_licoes`, depois de `p["licoes_feitas"] = []`, acrescente:

```python
            p["licao_passo"] = 0
```

Em `_licao_concluir`, troque o final por:

```python
        if p.get("licao_atual") == lic["id"]:
            p["licao_atual"] = None
            p["licao_passo"] = 0
```

- [ ] **Step 5: Avanço de passo em `_licao_evento`**

Em `_licao_evento`, troque

```python
        if not lic or tar.get("tipo") != verbo:
            return
```

por

```python
        if not lic:
            return
        # O passo avança por qualquer evento que ele declarar, mesmo que a tarefa
        # da lição seja outra (ex.: "atacar" no passo 2 de uma lição de habilidade).
        await self._guia_evento(p, lic, verbo, alvo)
        if tar.get("tipo") != verbo:
            return
```

Logo antes de `_licao_evento`, acrescente os métodos:

```python
    async def _guia_avancar(self, p, lic):
        passos = _guia_passos(lic)
        p["licao_passo"] = min(int(p.get("licao_passo", 0) or 0) + 1, len(passos) - 1)
        await self.send_to(p["id"], {"type": "licao_passo", "licao_id": lic["id"],
                                     "passo": _guia_payload(lic, p["licao_passo"])})

    async def _guia_evento(self, p, lic, verbo, alvo):
        """Avança o passo atual se o evento é o que ele declarou em `conclui_com`.
        O último passo nunca avança aqui: quem encerra a lição é a tarefa."""
        passos = _guia_passos(lic)
        i = int(p.get("licao_passo", 0) or 0)
        if i >= len(passos) - 1:
            return
        cond = passos[i].get("conclui_com")
        if not cond or cond.get("tipo") != verbo:
            return
        if not self._licao_alvo_ok(cond.get("alvo"), alvo):
            return
        await self._guia_avancar(p, lic)

    async def handle_avancar_passo(self, pid):
        """"Entendi": só avança passo informativo (sem `conclui_com`, não-último)."""
        p = self.players.get(pid)
        if not p:
            return
        lic = next((l for l in getattr(self, "licoes", []) if l["id"] == p.get("licao_atual")), None)
        if not lic:
            return
        passos = _guia_passos(lic)
        i = int(p.get("licao_passo", 0) or 0)
        if i >= len(passos) - 1 or passos[i].get("conclui_com"):
            return
        await self._guia_avancar(p, lic)
```

- [ ] **Step 6: Passo no payload da fala e no bloco `tutorial`**

Em `_disparar_fala`, depois de

```python
        if fala.get("tarefa"):
            p["licao_atual"] = fala["id"]
```

acrescente

```python
            p["licao_passo"] = 0
```

e, logo antes de `await self.send_to(p["id"], payload)`, acrescente

```python
        payload["passo"] = _guia_payload(fala, 0)
```

Em `_tutorial_payload`, dentro do dicionário `por_classe[cls] = {...}`, depois de `"vezes": ...`, acrescente:

```python
                "passo": _guia_payload(lic, p.get("licao_passo", 0)) if lic else None,
```

- [ ] **Step 7: Despachar a mensagem**

Em `server.py`, no `elif t == "repetir_tutorial":` (~linha 47610), acrescente logo depois do seu `if room:`:

```python
                elif t == "avancar_passo":
                    if room: await room.handle_avancar_passo(pid)
```

- [ ] **Step 8: Rodar tudo do arquivo**

Run: `python tools/test_tutorial_guia.py -v`
Expected: todos `ok`.

- [ ] **Step 9: Regressão das suítes vizinhas**

Run: `python tools/test_tutorial_salas.py && python tools/test_dungeon_loader.py`
Expected: sem falhas novas (`OK`/`0 falha(s)`).

- [ ] **Step 10: Commit**

```bash
git status --short server.py tools/test_tutorial_guia.py
git diff --stat server.py
git add tools/test_tutorial_guia.py server.py
git commit -m "feat(tutorial): passos do guia, avanço por evento e mensagem licao_passo" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: O passo sobrevive à foto da masmorra

**Files:**
- Test: `tools/test_tutorial_guia.py`
- Modify (só se o teste falhar): `server.py`

- [ ] **Step 1: Escrever o teste**

Acrescente em `tools/test_tutorial_guia.py`:

```python
class FotoTests(unittest.IsolatedAsyncioTestCase):
    async def test_licao_passo_faz_o_ciclo_da_foto(self):
        r, p = room('warrior', deepcopy(GUIA_MIRA))
        await abrir_licao(r, p, 'treino_mira')
        p['licao_passo'] = 2
        volta = S._foto_decodificar(S._foto_codificar(p))
        self.assertEqual(volta['licao_passo'], 2)
        self.assertEqual(volta['licao_atual'], 'treino_mira')

    def test_licao_guia_vai_na_foto_da_sala(self):
        # `licoes` e `falas` são categoria "foto": o guia autorado viaja junto.
        self.assertEqual(S.GameRoom.FOTO_SALA_CATEGORIAS.get('licoes') if hasattr(S.GameRoom, 'FOTO_SALA_CATEGORIAS')
                         else S.FOTO_SALA_CATEGORIAS.get('licoes'), 'foto')
```

- [ ] **Step 2: Rodar**

Run: `python tools/test_tutorial_guia.py FotoTests -v`
Expected: PASS. Se `_foto_codificar` levantar `FotoNaoSerializavel` para o jogador, descubra como `_gravar_foto_rodada` codifica os heróis (`grep -n "_gravar_foto_rodada" server.py`) e use a mesma chamada no teste. Se `FOTO_SALA_CATEGORIAS` estiver em outro lugar, `grep -n "FOTO_SALA_CATEGORIAS" server.py` e ajuste a referência.

- [ ] **Step 3: Rodar a suíte da foto**

Run: `python tools/test_salvar_masmorra.py`
Expected: sem falhas novas (a seção [2] varre atributos sem categoria; `licao_passo` é campo do jogador, não da sala, então não precisa de categoria).

- [ ] **Step 4: Commit**

```bash
git add tools/test_tutorial_guia.py
git commit -m "test(tutorial): licao_passo sobrevive à foto da masmorra" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Módulo puro `src/guiaTutorial.js`

**Files:**
- Create: `src/guiaTutorial.js`
- Create: `tools/test_guia_tutorial_cliente.js`

- [ ] **Step 1: Escrever o teste que falha**

Crie `tools/test_guia_tutorial_cliente.js`:

```javascript
// Guia do tutorial no cliente — roda da raiz: node tools/test_guia_tutorial_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

global.window = {};
const G = eval(fs.readFileSync(path.join(raiz, "src", "guiaTutorial.js"), "utf8") + "; window.GuiaTutorial");

console.log("\n[1] parseUi");
let r = G.parseUi("botao:encerrar_turno");
check("botão", r && r.tipo === "botao" && r.id === "encerrar_turno");
r = G.parseUi("habilidade:mira_certeira");
check("habilidade", r && r.tipo === "habilidade" && r.id === "mira_certeira");
r = G.parseUi("casa:[3,14]");
check("casa vira posição", r && r.tipo === "casa" && r.pos[0] === 3 && r.pos[1] === 14);
r = G.parseUi("porta:[10,2]");
check("porta vira posição", r && r.tipo === "porta" && r.pos[1] === 2);
check("lixo devolve null", G.parseUi("xyz") === null && G.parseUi("") === null
      && G.parseUi(null) === null && G.parseUi(5) === null);
check("tipo desconhecido devolve null", G.parseUi("voar:alto") === null);

console.log("\n[2] seletor (só o que o HUD desenha nesta fatia)");
let s = G.seletor("botao:encerrar_turno");
check("botão usa data-guia", s && s.css === '[data-guia="botao:encerrar_turno"]' && s.ancestral === null);
s = G.seletor("habilidade:mira_certeira");
check("habilidade acha o ícone e sobe ao botão",
      s && s.css === '[data-ability-id="mira_certeira"]' && s.ancestral === "button");
s = G.seletor("hud:fome");
check("medidor usa data-guia", s && s.css === '[data-guia="hud:fome"]');
check("casa ainda não tem seletor de HUD", G.seletor("casa:[1,2]") === null);
check("monstro ainda não tem seletor de HUD", G.seletor("monstro:boneco_treino") === null);
check("id com aspas não escapa do seletor", G.seletor('habilidade:a"b') === null);

console.log("\n[3] nivelDica");
const cfg = { dica1S: 12, dica2S: 30 };
check("recém-chegado: 0", G.nivelDica(0, 5000, cfg) === 0);
check("11,9 s: 0", G.nivelDica(0, 11900, cfg) === 0);
check("12 s: 1", G.nivelDica(0, 12000, cfg) === 1);
check("29,9 s: 1", G.nivelDica(0, 29900, cfg) === 1);
check("30 s: 2", G.nivelDica(0, 30000, cfg) === 2);
check("progresso reinicia", G.nivelDica(40000, 41000, cfg) === 0);
check("relógio andando para trás: 0", G.nivelDica(5000, 1000, cfg) === 0);

console.log("\n[4] textoDica");
const passo = { dica: ["primeira", "segunda"] };
check("nível 0 sem texto", G.textoDica(passo, 0) === "");
check("nível 1 = primeira", G.textoDica(passo, 1) === "primeira");
check("nível 2 = segunda", G.textoDica(passo, 2) === "segunda");
check("só uma dica: nível 2 repete a última", G.textoDica({ dica: ["única"] }, 2) === "única");
check("sem dica: vazio", G.textoDica({}, 2) === "" && G.textoDica(null, 1) === "");

console.log(`\n${PASS} ok, ${FAIL} falha(s)`);
process.exit(FAIL ? 1 : 0);
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: erro `ENOENT ... src/guiaTutorial.js`.

- [ ] **Step 3: Escrever o módulo**

Crie `src/guiaTutorial.js` (LF; é arquivo novo):

```javascript
// Guia do tutorial — lógica pura (sem DOM, canvas nem THREE).
// O game.js lê o passo recebido do servidor, pergunta aqui QUAL elemento
// destacar e QUANDO endurecer a dica; o desenho é dele.
(function () {
  const TIPOS_CASA = ['casa', 'porta'];
  const TIPOS_ID   = ['botao', 'habilidade', 'bolsa', 'slot', 'monstro', 'hud'];
  const ID_OK = /^[a-z0-9_]+$/;

  // "habilidade:mira_certeira" -> {tipo, id};  "casa:[3,14]" -> {tipo, pos:[3,14]}
  function parseUi(ui) {
    if (typeof ui !== 'string') return null;
    const i = ui.indexOf(':');
    if (i < 1) return null;
    const tipo = ui.slice(0, i), resto = ui.slice(i + 1);
    if (TIPOS_CASA.indexOf(tipo) >= 0) {
      const m = /^\[(\d+),(\d+)\]$/.exec(resto);
      return m ? { tipo, pos: [Number(m[1]), Number(m[2])] } : null;
    }
    if (TIPOS_ID.indexOf(tipo) >= 0 && ID_OK.test(resto)) return { tipo, id: resto };
    return null;
  }

  // Seletor CSS do elemento de HUD correspondente. Devolve null para o que
  // ainda não é HUD (casa, monstro, porta, bolsa, slot: fatia do tabuleiro).
  // `ancestral`: o elemento achado é um filho; o halo vai no ancestral indicado.
  function seletor(ui) {
    const a = parseUi(ui);
    if (!a) return null;
    if (a.tipo === 'botao' || a.tipo === 'hud')
      return { css: '[data-guia="' + a.tipo + ':' + a.id + '"]', ancestral: null };
    if (a.tipo === 'habilidade')
      return { css: '[data-ability-id="' + a.id + '"]', ancestral: 'button' };
    return null;
  }

  // 0 = sem dica; 1 = primeira dica; 2 = segunda. `desde` e `agora` em ms.
  function nivelDica(desde, agora, cfg) {
    const s = (agora - desde) / 1000;
    if (!(s >= 0)) return 0;
    if (s >= cfg.dica2S) return 2;
    if (s >= cfg.dica1S) return 1;
    return 0;
  }

  function textoDica(passo, nivel) {
    const d = (passo && passo.dica) || [];
    if (!nivel || !d.length) return '';
    return d[Math.min(nivel, d.length) - 1] || '';
  }

  window.GuiaTutorial = { parseUi, seletor, nivelDica, textoDica };
})();
```

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: `0 falha(s)`.

- [ ] **Step 5: Commit**

```bash
git add src/guiaTutorial.js tools/test_guia_tutorial_cliente.js
git commit -m "feat(tutorial): módulo puro do guia (alvo, seletor e nível de dica)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: `gameState.js` encaminha o passo

**Files:**
- Modify: `src/gameState.js` (`case 'fala'` ~linha 1863; funções do tutorial ~linha 2489; export ~linha 3822)
- Test: `tools/test_guia_tutorial_cliente.js`

- [ ] **Step 1: Acrescentar os testes**

Em `tools/test_guia_tutorial_cliente.js`, antes do `console.log(`\n${PASS} ok...`)` final, acrescente:

```javascript
console.log("\n[5] gameState: passo na lição, avanço e evento");
global.localStorage = { getItem: () => null, setItem: () => {} };
global.location = { search: "", protocol: "http:", host: "x" };
const GS = eval(fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8") + "; GS");
GS.injectPreviewState({
  type: "game_state", master_pid: "p1",
  players: [{ id: "p1", name: "G", class_id: "warrior", alive: true, pos: [1, 1] }],
  monsters: [], tiles: [[0]], rooms: [], explored: [], round: 1,
  tutorial: { por_classe: { warrior: { licao_id: "a", texto_curto: "Ataque", feito: 0, vezes: 1,
    concluidas: 0, total: 2, passo: { i: 1, n: 3, texto: "Passo", ui: "botao:encerrar_turno" } } } },
});
const lic = GS.licaoAtual();
check("licaoAtual traz o passo", lic && lic.passo && lic.passo.i === 1 && lic.passo.n === 3);
check("GS.avancarPasso existe", typeof GS.avancarPasso === "function");
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: falha em `GS.avancarPasso existe` (o `licaoAtual` já devolve o objeto inteiro, então o passo vem de graça).

- [ ] **Step 3: Implementar**

Em `src/gameState.js`, logo depois do `case 'fala':` (Edit), acrescente:

```javascript
      case 'licao_passo':
        _emit('licaoPasso', msg);   // {licao_id, passo:{i,n,texto,porque,ui,dica,informativo}}
        break;
```

Logo depois de `function repetirTutorial() {...}`, acrescente:

```javascript
  function avancarPasso() { send({ type: 'avancar_passo' }); }
```

No objeto exportado, troque `licaoAtual, repetirTutorial, podeRepetirTutorial,` por:

```javascript
    licaoAtual, repetirTutorial, podeRepetirTutorial, avancarPasso,
```

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_guia_tutorial_cliente.js && node tools/test_tutorial_cliente.js`
Expected: `0 falha(s)` nos dois.

- [ ] **Step 5: Commit**

```bash
git status --short src/gameState.js
git add src/gameState.js tools/test_guia_tutorial_cliente.js
git commit -m "feat(tutorial): gameState encaminha licao_passo e envia avancar_passo" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Textos, configuração e carga dos scripts

**Files:**
- Create: `src/lang/tutorial.js`
- Modify: `src/visualConfig.js`, `index.html`

- [ ] **Step 1: Criar o dicionário**

Crie `src/lang/tutorial.js`:

```javascript
// Textos do tutorial guiado (janela da lição com passos). Mantido à mão.
window.LANG_TUTORIAL = {
  "ui.tutorial.passo_de": {
    "en": "Step {i} of {n}",
    "pt": "Passo {i} de {n}"
  },
  "ui.tutorial.me_mostra": {
    "en": "Show me",
    "pt": "Me mostra"
  },
  "ui.tutorial.entendi": {
    "en": "Got it",
    "pt": "Entendi"
  },
  "ui.tutorial.dica": {
    "en": "Hint",
    "pt": "Dica"
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_TUTORIAL);
```

- [ ] **Step 2: Tempos em `VC.tutorial`**

Em `src/visualConfig.js`, dentro do objeto `window.VC = {`, depois da chave `dice: {...},` (use Edit na linha `  dice: {` para inserir antes dela), acrescente:

```javascript
  // Tutorial guiado: segundos sem progresso até cada nível de dica.
  tutorial: { dica1S: 12, dica2S: 30 },
```

- [ ] **Step 3: Carregar os scripts**

Em `index.html` (uma linha longa; use Edit):
- na linha dos idiomas, depois de `document.write('<script src="src/lang/narracao.js?v='+v+'"><\/script>');` acrescente `document.write('<script src="src/lang/tutorial.js?v='+v+'"><\/script>');`
- na linha do `gameState.js`, depois de `document.write('<script src="src/difficulty.js?v='+v+'"><\/script>');` acrescente `document.write('<script src="src/guiaTutorial.js?v='+v+'"><\/script>');`

- [ ] **Step 4: Conferir paridade de idioma e ordem dos scripts**

Run: `python tools/test_idioma.py && node tools/test_idioma_cliente.js`
Expected: sem falhas. Se o teste do cliente acusar chave órfã/ausente por não carregar `tutorial.js`, acrescente `tutorial.js` à lista de arquivos de idioma que o próprio teste carrega (ele já lista os outros cinco).

Run: `python tools/dividas.py`
Expected: nenhuma dívida nova de idioma.

- [ ] **Step 5: Commit**

```bash
git add src/lang/tutorial.js src/visualConfig.js index.html tools/test_idioma_cliente.js
git commit -m "feat(tutorial): textos, tempos de dica e carga do guia" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

(Se `tools/test_idioma_cliente.js` não mudou, tire-o do `git add`.)

---

### Task 7: Janela com passos e halo no `game.js`

**Files:**
- Modify: `game.js` (botão `#btn-end-turn` ~linha 439; bloco "Janela da lição do tutorial" ~linhas 53673–53699), `game.css` (depois da linha 1822)
- Test: `tools/test_guia_tutorial_cliente.js` (fiação estática)

- [ ] **Step 1: Escrever o teste de fiação (falha)**

Em `tools/test_guia_tutorial_cliente.js`, antes do resumo final, acrescente:

```javascript
console.log("\n[6] fiação estática no game.js, index.html e CSS");
const gameSrc = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
const indexSrc = fs.readFileSync(path.join(raiz, "index.html"), "utf8");
const cssSrc = fs.readFileSync(path.join(raiz, "game.css"), "utf8");
check("botão encerrar turno tem data-guia", /id="btn-end-turn"[^>]*data-guia="botao:encerrar_turno"|data-guia="botao:encerrar_turno"[^>]*id="btn-end-turn"/.test(gameSrc));
check("um único GS.on('licaoPasso')", (gameSrc.match(/GS\.on\('licaoPasso'/g) || []).length === 1);
check("janela usa GuiaTutorial.seletor", /GuiaTutorial\.seletor\(/.test(gameSrc));
check("janela usa nivelDica com VC.tutorial", /GuiaTutorial\.nivelDica\(/.test(gameSrc) && /VC\.tutorial/.test(gameSrc));
check("botão Entendi chama GS.avancarPasso", /GS\.avancarPasso\(\)/.test(gameSrc));
check("index.html carrega guiaTutorial.js e tutorial.js",
      /src\/guiaTutorial\.js/.test(indexSrc) && /src\/lang\/tutorial\.js/.test(indexSrc));
check("CSS do halo existe", /\.guia-halo\b/.test(cssSrc) && /@keyframes guia-pulso/.test(cssSrc));
check("textos pelo tradutor, não literais", /ui\.tutorial\.passo_de/.test(gameSrc) && /ui\.tutorial\.entendi/.test(gameSrc));
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: falhas nos 8 checks da seção [6].

- [ ] **Step 3: `data-guia` no botão de encerrar turno**

Em `game.js`, na linha do `<button type="button" class="btn-end-turn" id="btn-end-turn" disabled>` (~439) use Edit para trocar por:

```html
        <button type="button" class="btn-end-turn" id="btn-end-turn" data-guia="botao:encerrar_turno" disabled>
```

- [ ] **Step 4: Reescrever o bloco da janela da lição**

Em `game.js`, substitua `_mostrarJanelaLicao`, `_fecharJanelaLicao` e `_reabrirJanelaLicao` (do comentário "Janela da lição do tutorial" até a linha `function _reabrirJanelaLicao(){...}`) por:

```javascript
let _licaoUltima = null;
let _guiaPasso = null;          // passo atual recebido do servidor
let _guiaDesde = 0;             // performance.now() do último progresso
let _guiaTimer = null;
const _guiaCfg = () => ({ dica1S: 12, dica2S: 30, ...(window.VC && VC.tutorial) });

// Chave de idioma (ui.tutorial.*) ou texto autoral em português.
function _tutTexto(s){
  s = s || '';
  return s.indexOf('ui.tutorial.') === 0 ? t(s) : s;
}

function _guiaLimparHalo(){
  document.querySelectorAll('.guia-halo').forEach(el => el.classList.remove('guia-halo', 'guia-halo-forte'));
}

// O HUD é redesenhado por innerHTML a cada game_state e apaga a classe; por isso o
// halo é reaplicado num laço curto enquanto houver passo com alvo de HUD.
function _guiaAplicarHalo(){
  _guiaLimparHalo();
  if(!_guiaPasso || !_guiaPasso.ui) return;
  const sel = GuiaTutorial.seletor(_guiaPasso.ui);
  if(!sel) return;
  let el = document.querySelector(sel.css);
  if(el && sel.ancestral) el = el.closest(sel.ancestral);
  if(!el) return;
  el.classList.add('guia-halo');
  if(GuiaTutorial.nivelDica(_guiaDesde, performance.now(), _guiaCfg()) >= 1) el.classList.add('guia-halo-forte');
}

function _guiaAtualizarDica(){
  const host = $('licao-dica');
  if(!host) return;
  const nivel = GuiaTutorial.nivelDica(_guiaDesde, performance.now(), _guiaCfg());
  const txt = GuiaTutorial.textoDica(_guiaPasso, nivel);
  host.textContent = txt ? `${t('ui.tutorial.dica')}: ${_tutTexto(txt)}` : '';
  host.style.display = txt ? 'block' : 'none';
}

function _guiaTick(){
  if(!_guiaPasso){ _guiaLimparHalo(); return; }
  _guiaAplicarHalo();
  _guiaAtualizarDica();
}

function _guiaIniciar(passo){
  _guiaPasso = passo || null;
  _guiaDesde = performance.now();
  if(_guiaTimer) clearInterval(_guiaTimer);
  _guiaTimer = _guiaPasso ? setInterval(_guiaTick, 400) : null;
  _guiaTick();
}

function _guiaMostrar(){ _guiaDesde = performance.now(); _guiaTick(); }

function _mostrarJanelaLicao(msg){
  const host = $('licao-janela');
  if(!host) return;
  _licaoUltima = msg;
  const emoji = (msg.falante && msg.falante.emoji) || '💬';
  const nome  = (msg.falante && msg.falante.nome)  || '';
  const passo = msg.passo || null;
  const explicito = !!(passo && !passo.auto);
  const texto = explicito ? _tutTexto(passo.texto) : (msg.texto || '');
  const andamento = (explicito && passo.n > 1)
    ? `<div class="licao-passo">${_esc(t('ui.tutorial.passo_de', {i: passo.i + 1, n: passo.n}))}` +
      `<div class="licao-barra"><i style="width:${Math.round(((passo.i + 1) / passo.n) * 100)}%"></i></div></div>` : '';
  const porque = (explicito && passo.porque)
    ? `<div class="licao-porque">${_esc(_tutTexto(passo.porque))}</div>` : '';
  const botoes = (passo && passo.ui && GuiaTutorial.seletor(passo.ui))
    ? `<button type="button" class="licao-botao" onclick="_guiaMostrar()">${t('ui.tutorial.me_mostra')}</button>` : '';
  const entendi = (passo && passo.informativo)
    ? `<button type="button" class="licao-botao licao-botao-ok" onclick="GS.avancarPasso()">${t('ui.tutorial.entendi')}</button>` : '';
  host.innerHTML =
    `<div class="licao-topo"><span class="licao-emoji">${_esc(emoji)}</span>` +
    `<span class="licao-nome">${_esc(nome)}</span>` +
    `<button type="button" class="licao-fechar" onclick="_fecharJanelaLicao()"` +
    ` title="${t('ui.geral.fechar')}" aria-label="${t('ui.geral.fechar')}">✕</button></div>` +
    andamento +
    `<div class="licao-texto">${_esc(texto)}</div>` + porque +
    `<div class="licao-dica" id="licao-dica" style="display:none"></div>` +
    ((botoes || entendi) ? `<div class="licao-acoes">${botoes}${entendi}</div>` : '');
  host.classList.add('open');
  _guiaIniciar(passo);
}
// Fechar a janela não apaga o destaque: o halo vive até o passo mudar.
function _fecharJanelaLicao(){ $('licao-janela')?.classList.remove('open'); }
// O quadro ⚑ do HUD reabre a última lição — fechar não pode ser irreversível.
function _reabrirJanelaLicao(){ if(_licaoUltima) _mostrarJanelaLicao(_licaoUltima); }

GS.on('licaoPasso', msg => {
  if(!msg || !_licaoUltima || msg.licao_id !== _licaoUltima.licao_id) return;
  _licaoUltima = Object.assign({}, _licaoUltima, { passo: msg.passo });
  _mostrarJanelaLicao(_licaoUltima);
});
```

Atenção ao fazer a troca: o bloco `GS.on('fala', ...)` logo abaixo continua como está (chama `_mostrarJanelaLicao(msg)`; o `msg.passo` já vem no payload).

- [ ] **Step 5: CSS**

Em `game.css`, logo depois da linha `@media (max-width:900px){ #licao-janela{ ... } }` (~1822), acrescente:

```css
#licao-janela .licao-passo{ font-size:.68rem; letter-spacing:.5px; opacity:.85; margin-bottom:4px; }
#licao-janela .licao-barra{ height:4px; background:#ffffff1f; border-radius:2px; margin-top:3px; overflow:hidden; }
#licao-janela .licao-barra i{ display:block; height:100%; background:#f0c867; transition:width .3s; }
#licao-janela .licao-porque{ font-size:.78rem; opacity:.8; margin-top:6px; line-height:1.35; }
#licao-janela .licao-dica{ margin-top:8px; padding:6px 8px; border-left:3px solid #f0c867;
  background:#f0c8671f; font-size:.82rem; line-height:1.35; }
#licao-janela .licao-acoes{ display:flex; gap:8px; margin-top:8px; }
#licao-janela .licao-botao{ cursor:pointer; padding:5px 10px; border-radius:4px; font-size:.8rem;
  border:1px solid #f0c86788; background:#f0c8671a; color:inherit; }
#licao-janela .licao-botao:hover{ background:#f0c86733; }
#licao-janela .licao-botao-ok{ background:#f0c867; color:#241c0a; font-weight:700; }

.guia-halo{ position:relative; outline:3px solid #f0c867; outline-offset:2px; border-radius:6px;
  animation:guia-pulso 1.6s ease-in-out infinite; z-index:5; }
.guia-halo.guia-halo-forte{ outline-width:4px; animation-duration:.9s; }
@keyframes guia-pulso{
  0%,100%{ box-shadow:0 0 0 0 #f0c86799; }
  50%{ box-shadow:0 0 0 10px #f0c86700, 0 0 18px 4px #f0c867cc; }
}
@media (prefers-reduced-motion:reduce){ .guia-halo{ animation:none; box-shadow:0 0 14px 3px #f0c867cc; } }
```

- [ ] **Step 6: Rodar os testes e as checagens de sintaxe**

Run: `node --check game.js && node tools/test_guia_tutorial_cliente.js && node tools/test_tutorial_cliente.js`
Expected: sem erro de sintaxe e `0 falha(s)`.

Run: `python tools/test_interface.py`
Expected: sem literal novo em português no `game.js` (o placar de interface continua em zero). Se acusar `_tutTexto`/`'ui.tutorial.'`, é falso positivo de chave: confirme se o placar ignora chaves `ui.` (ele ignora; se não, ajuste o literal).

- [ ] **Step 7: Commit**

```bash
git status --short game.js game.css
git diff --stat game.js game.css
git add game.js game.css tools/test_guia_tutorial_cliente.js
git commit -m "feat(tutorial): janela da lição com passos e halo no HUD" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Prova no navegador

**Files:** nenhum (verificação).

O objetivo é ver o halo e a janela funcionando num jogo real, num servidor isolado.

- [ ] **Step 1: Subir uma cópia isolada do servidor**

```bash
RAIZ="C:/Users/RICARDO/Desktop/jogo tabuleiro"
TMP="$TEMP/lfh_guia"; rm -rf "$TMP"; mkdir -p "$TMP"
cd "$RAIZ" && git ls-files -z | grep -zv '^\(savegames\|accounts\|groups\)/' | xargs -0 -I{} cp --parents "{}" "$TMP"/
cd "$TMP" && LFH_PORT=8790 python server.py
```

Expected: o servidor sobe na 8790 (rode em segundo plano). Não use a 8765: é a do autor.

- [ ] **Step 2: Abrir e jogar**

Abra `http://[::1]:8790` no navegador do app, crie uma conta de teste local, escolha o Guerreiro Anão e entre no Campo de Treinamento. Em `localhost` pode criar conta de teste.

- [ ] **Step 3: Verificar a lição sem `guia` (derivada)**

Ande até a primeira lição de encerrar turno. Esperado: a janela da lição abre com o texto de sempre e, na lição `encerrar_turno`, o botão **Encerrar Turno** pulsa em dourado. Ao ficar 12 s parado o halo fica mais forte; a janela mostra o botão "Me mostra".

- [ ] **Step 4: Verificar o guia autorado no console**

No console do navegador, com a janela do jogo ativa:

```javascript
_mostrarJanelaLicao({licao_id:'x', falante:{nome:'Teste',emoji:'🧪'}, texto:'longo',
  passo:{i:0,n:3,texto:'Clique em Mira Certeira.',porque:'Soma +2 no acerto.',
         ui:'habilidade:mira_certeira',dica:['Está na barra de baixo.','É o ícone da mira.'],
         informativo:true,auto:false}});
```

Esperado: "Passo 1 de 3" com barra, o "porque", os botões "Me mostra" e "Entendi", e o botão da Mira Certeira com halo (se o guerreiro estiver na vez e a barra visível). Depois de 12 s aparece "Dica: Está na barra de baixo."; depois de 30 s, a segunda.

- [ ] **Step 5: Verificar `Entendi` ponta a ponta**

Com uma lição real aberta e um `guia` autorado (edite uma cópia do `campo_de_treinamento.json` na pasta isolada para a lição `treino_mira`), clique em "Entendi" e confira que chega `licao_passo` (`read_network_requests` ou `GS.on`) e o "Passo 2 de 3" aparece. Fechar a janela (✕) mantém o halo; o quadro ⚑ a reabre.

- [ ] **Step 6: Console limpo**

Use `read_console_messages` com `onlyErrors`. Esperado: nenhum erro.

- [ ] **Step 7: Encerrar**

Pare o servidor da 8790 e apague `$TEMP/lfh_guia`.

---

### Task 9: Documentar

**Files:**
- Modify: `CLAUDE.md` (CRLF; use Edit)

- [ ] **Step 1: Acrescentar o parágrafo**

Logo depois do parágrafo "Campo de Treinamento — salas por herói", acrescente:

```markdown
> **Tutorial guiado — fatia 1 (2026-10-07):** a lição pode declarar `guia` (1 a 8 passos `{texto, porque?, ui?, dica?[≤2], conclui_com?}`); sem `guia` o servidor gera um passo `auto` a partir da tarefa (`_guia_ui_padrao`). O passo atual de cada herói é `p["licao_passo"]`; vai no payload da `fala` (`passo`), no bloco `tutorial.por_classe[cls].passo` e na mensagem `licao_passo`. Um passo avança quando o evento que ele declarou em `conclui_com` chega a `_licao_evento` (mesmo que a tarefa da lição seja outra) ou pelo botão "Entendi" (`avancar_passo`, só para passo informativo: não-último e sem `conclui_com`). O último passo nunca avança sozinho: quem encerra a lição é a tarefa. Armar uma habilidade é ação só do cliente, então esse passo é informativo. `ui` aponta o elemento: `botao:|habilidade:|bolsa:|slot:|monstro:|hud:<id>` ou `casa:|porta:[x,y]` (`GUIA_UI_RE`). Cliente: `src/guiaTutorial.js` (puro: `parseUi`, `seletor`, `nivelDica`, `textoDica`); o `game.js` aplica `.guia-halo` por um laço de 400 ms (o HUD é redesenhado por innerHTML e apagaria a classe) e endurece a dica em `VC.tutorial.dica1S/dica2S`. Nesta fatia o halo só existe para HUD (`botao`, `habilidade`, `hud`); `casa`, `monstro`, `porta`, `bolsa` e `slot` são aceitos e ainda não desenhados. Textos de passo aceitam chave `ui.tutorial.*`. Spec/plano em `docs/superpowers/{specs,plans}/2026-10-07-tutorial-guiado*`. Testes: `tools/test_tutorial_guia.py` e `tools/test_guia_tutorial_cliente.js`.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: guia do tutorial (fatia 1) no CLAUDE.md" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

## Auto-revisão contra a spec

| Seção da spec | Onde está no plano |
|---|---|
| 1 Modelo de dados (passo, `guia`, `licao_passo`) | Tasks 1, 2, 3 |
| 2 Servidor: payload, avanço, validação | Tasks 1, 2 (dica por erro e `licao_resultado`: fatia 2) |
| 3.1 Vocabulário de `ui` | Task 1 (`GUIA_UI_RE`), Task 4 (`parseUi`) |
| 3.2 Alvo padrão por tarefa | Task 2 (`_guia_ui_padrao`) |
| 4.1 `guiaTutorial.js` | Task 4 |
| 4.2 Halo | Task 7 (só HUD); tabuleiro 2D/3D e porta: fatia 2 |
| 4.3 Janela com "Passo i de n", "Me mostra", "Entendi" | Task 7 |
| 4.4 Glossário, 4.5 resultado | Fatias 3 e 2 |
| 5 Conteúdo | Fatias 3 e 4 |
| 6 Parâmetros (`VC.tutorial`) | Task 6 |
| 7 Persistência e multiplayer | Task 3 e teste `test_passos_sao_por_heroi` (Task 2) |
| 8 Testes | Tasks 1–5 e 7; browser na Task 8 |

Consistência de nomes: `GUIA_MAX_PASSOS`, `GUIA_UI_RE`, `_guia_ui_padrao`, `_guia_passos`, `_guia_payload`, `_guia_avancar`, `_guia_evento`, `handle_avancar_passo`, `licao_passo` (campo, mensagem), `GS.avancarPasso`, `GuiaTutorial.{parseUi,seletor,nivelDica,textoDica}`, `VC.tutorial.{dica1S,dica2S}`. Todos aparecem com a mesma grafia em testes e implementação.
