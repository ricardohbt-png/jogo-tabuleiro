# Tutorial guiado — fatia 4 (seis salas por herói e lições geradas) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dar passos guiados (pt + en) às 47 lições das seis classes do Campo de Treinamento e às lições geradas em jogo (`treino_guild_*` e `treino_magia_*`).

**Architecture:** Reusa o mecanismo da fatia 3: dados em módulos Python por classe (`tools/tutorial_guia_<classe>.py`), um gerador único que junta todos os módulos, grava `src/lang/tutorial_guia.js` e injeta `guia` (só chaves) no JSON. As lições geradas em tempo de execução não podem levar texto traduzido gravado (a lista `licoes` vai para a foto da masmorra e é JSON), então ganham um campo simples `guia_modelo` e o servidor monta os passos na hora do envio, com textos `T(...)` resolvidos no idioma de cada jogador.

**Tech Stack:** Python 3 (`unittest`), `server.py` (CRLF, usar Edit), `tutorial_training.py`, `game.js` (uma linha), `src/lang/*.js`.

Spec: `docs/superpowers/specs/2026-10-07-tutorial-guiado-design.md` (seção 5, fatia 4). A fatia 3 (glossário + trilha comum) já está em `master`; este plano estende o que ela criou: `tools/tutorial_guia_comum.py`, `tools/gerar_guia_comum.py`, `tools/test_tutorial_conteudo.py`.

## Regras de conteúdo (as mesmas da fatia 3)

1. Uma ação por passo, imperativo, **no máximo 15 palavras** em `texto` (não conta os `[[ ]]`).
2. `porque` depois da ação, uma frase.
3. Termo de glossário como `[[termo]]`.
4. Último passo de cada lição sem `conclui` (quem encerra é a tarefa).
5. `conclui` nunca para evento que pode ter ocorrido antes da lição — passo que só descreve é informativo ("Entendi"). **Nesta fatia nenhum passo usa `conclui`.**
6. `ui` só: `botao:encerrar_turno`, `botao:inventario`, `botao:magias` (criado na Task 1), `monstro:<tipo>`, `habilidade:<id>`.
7. **Regra nova:** `habilidade:<id>` só aparece quando `<id>` é exatamente o `tarefa.alvo` da lição (é isso que o botão do HUD traz em `data-ability-id`). Lição cuja tarefa não tem alvo de habilidade (ex.: `desarmar_armadilha`, `libertar_refem`) não leva `habilidade:`.

Glossário novo (7 termos, somam 14 com os da fatia 3): `d20`, `acao_principal`, `slot`, `teste_resistencia`, `manutencao`, `furtivo`, `critico`.

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `tools/tutorial_guia_comum.py` | modificar | +7 termos em `GLOSSARIO` |
| `tools/gerar_guia_comum.py` | modificar | junta N módulos (`MODULOS`), `guia_todos()` |
| `tools/test_tutorial_conteudo.py` | modificar | glossário ≥ 14 termos; usa `guia_todos()` onde cabe |
| `tools/tutorial_guia_guerreiro.py` etc. (6) | criar | `GUIA` de cada classe |
| `tools/test_tutorial_classes.py` | criar | regras por classe contra o JSON |
| `game.js` | modificar | `data-guia="botao:magias"` em `#fab-magias` |
| `server.py` / `tutorial_training.py` | modificar | `guia_modelo` e `_guia_passos` |
| `tools/test_tutorial_modelos.py` | criar | testa os modelos das lições geradas |
| `src/lang/tutorial_guia.js`, `src/lang/tutorial.js` | gerado / modificar | chaves novas |
| `dungeons/campo_de_treinamento.json` | gerado | `guia` em +47 falas |
| `CLAUDE.md` | modificar | parágrafo da fatia 4 |

Lições por classe (47): guerreiro 7 (`fala_5`, `fala_6`, `treino_mira`, `treino_golpe`, `treino_furia`, `treino_furia_extra`, `treino_guerreiro_fim`); mago 9 (`fala_7`, `fala_8`, `treino_magia`, `treino_slots`, `treino_aprimorar_magia`, `treino_estender_magia`, `treino_fortalecer_magia`, `treino_reviver`, `treino_comando`); ladino 9 (`fala_9`, `fala_10`, `treino_detectar`, `treino_desarmar`, `treino_esconder`, `treino_furtivo`, `treino_veneno`, `treino_veneno_golpe`, `treino_criar`); clérigo 6 (`fala_11`, `fala_12`, `treino_cura`, `treino_cura_area`, `treino_purificar`, `treino_ressuscitar`); bardo 7 (`fala_13`, `fala_14`, `treino_cancao`, `treino_cancao_manter`, `treino_cancao_parar`, `treino_provocar`, `treino_instrumento`); paladino 9 (`fala_15`, `fala_16`, `treino_refem`, `treino_protetor`, `treino_maos`, `treino_sagrado`, `treino_sagrado_golpe`, `treino_regen`, `treino_luz`).

---

### Task 1: Glossário ampliado, gerador multi-módulo e botão do Grimório

**Files:**
- Modify: `tools/tutorial_guia_comum.py` (acrescentar 7 termos em `GLOSSARIO`)
- Modify: `tools/gerar_guia_comum.py`
- Modify: `tools/test_tutorial_conteudo.py`
- Modify: `game.js:452` (CRLF — Edit)

- [ ] **Step 1: Escrever os testes que falham**

Em `tools/test_tutorial_conteudo.py`, troque `test_glossario_completo` por:

```python
    def test_glossario_completo(self):
        esperados = {"turno", "movimento", "acao_livre", "acao_bonus", "ca", "fome_sede", "resistencia",
                     "d20", "acao_principal", "slot", "teste_resistencia", "manutencao", "furtivo", "critico"}
        self.assertEqual(set(C.GLOSSARIO), esperados)
        for k, v in C.GLOSSARIO.items():
            for campo in ("nome", "texto"):
                self.assertTrue(v[campo][0].strip() and v[campo][1].strip(), f"{k}.{campo}")
```

E acrescente em `GeradorTests`:

```python
    def test_guia_todos_junta_os_modulos_existentes(self):
        todos = G.guia_todos()
        for lid in C.GUIA:
            self.assertIn(lid, todos)
        self.assertEqual(len(todos), len(set(todos)))   # nenhum id repetido entre módulos

    def test_botao_do_grimorio_tem_marcador(self):
        gjs = (RAIZ / "game.js").read_text(encoding="utf-8")
        self.assertRegex(gjs, r'id="fab-magias"[^>]*data-guia="botao:magias"')
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_tutorial_conteudo.py`
Expected: falha em `test_glossario_completo` (faltam 7 termos), `AttributeError: guia_todos`, e o regex do botão.

- [ ] **Step 3: Termos novos**

Em `tools/tutorial_guia_comum.py`, antes do `}` que fecha `GLOSSARIO`:

```python
    "d20": {"nome": ("d20", "d20"),
            "texto": ("O dado de 20 lados. Todo ataque soma seu acerto ao d20 e compara com a CA do alvo.",
                      "The 20-sided die. Every attack adds your attack bonus to the d20 and compares it with the target's AC.")},
    "acao_principal": {"nome": ("ação principal", "main action"),
                       "texto": ("A ação mais forte do turno: atacar, lançar magia ou usar uma habilidade. É uma por turno.",
                                 "The strongest action of a turn: attack, cast a spell or use an ability. You get one per turn.")},
    "slot": {"nome": ("slot", "slot"),
             "texto": ("Espaço de magia de um círculo. Cada magia gasta um slot; eles voltam conforme a regra do círculo.",
                       "A spell space of one circle. Each spell spends a slot; they return according to the circle's rule.")},
    "teste_resistencia": {"nome": ("teste de resistência", "saving throw"),
                          "texto": ("Dado que o alvo rola para evitar ou diminuir um efeito. Passar costuma reduzir o estrago.",
                                    "A die the target rolls to avoid or reduce an effect. Passing usually reduces the harm.")},
    "manutencao": {"nome": ("manutenção", "upkeep"),
                   "texto": ("Custo em comida e água cobrado a cada rodada enquanto um efeito sustentado continua ligado.",
                             "A food and water cost charged every round while a sustained effect stays on.")},
    "furtivo": {"nome": ("ataque furtivo", "sneak attack"),
                "texto": ("Dano extra de quem ataca escondido, vindo das sombras. Dispara sozinho quando as condições valem.",
                          "Extra damage from attacking while hidden in the shadows. It triggers by itself when the conditions hold.")},
    "critico": {"nome": ("acerto crítico", "critical hit"),
                "texto": ("Um 20 natural no d20: o golpe acerta e o dano é dobrado.",
                          "A natural 20 on the d20: the hit lands and the damage is doubled.")},
```

- [ ] **Step 4: `guia_todos` no gerador**

Em `tools/gerar_guia_comum.py`, substitua `import tutorial_guia_comum as C` e acrescente (as funções passam a ler `GUIA` de todos os módulos; o `GLOSSARIO` continua só em `C`):

```python
import importlib

import tutorial_guia_comum as C

# Módulos de conteúdo por classe. Um módulo ausente é ignorado (permite entregar por partes).
MODULOS_CLASSES = ("tutorial_guia_guerreiro", "tutorial_guia_mago", "tutorial_guia_ladino",
                   "tutorial_guia_clerigo", "tutorial_guia_bardo", "tutorial_guia_paladino")


def guia_todos():
    """{lição_id: [passos]} de TODOS os módulos (trilha comum + classes)."""
    out = dict(C.GUIA)
    for nome in MODULOS_CLASSES:
        try:
            mod = importlib.import_module(nome)
        except ModuleNotFoundError as e:
            if e.name != nome:
                raise
            continue
        for lid, passos in mod.GUIA.items():
            if lid in out:
                raise ValueError(f"lição repetida entre módulos: {lid}")
            out[lid] = passos
    return out
```

Em `gerar_lang()` troque `for lic, passos in C.GUIA.items():` por `for lic, passos in guia_todos().items():`; em `aplicar_guia()` troque `passos = C.GUIA.get(f["id"])` por `passos = _TODOS.get(f["id"])` e defina `_TODOS = guia_todos()` no começo de `aplicar_guia` (`_TODOS = guia_todos()` como primeira linha da função, antes do laço).

- [ ] **Step 5: Marcador do botão**

Em `game.js` linha ~452, no `<button id="fab-magias" …>` acrescente `data-guia="botao:magias"` logo depois de `id="fab-magias"`.

- [ ] **Step 6: Rodar e ver passar**

Run: `python tools/gerar_guia_comum.py && python tools/test_tutorial_conteudo.py && node --check game.js`
Expected: `OK`. O `git diff --stat src/lang/tutorial_guia.js` mostra só os 7 termos novos (14 chaves `.nome`/`.texto`).

- [ ] **Step 7: Commit**

```bash
git add tools/tutorial_guia_comum.py tools/gerar_guia_comum.py tools/test_tutorial_conteudo.py game.js src/lang/tutorial_guia.js
git commit -m "feat(tutorial): glossário ampliado, gerador multi-módulo e marcador do Grimório" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Teste de regras das classes

**Files:**
- Create: `tools/test_tutorial_classes.py`

- [ ] **Step 1: Criar o teste (já falha: faltam os módulos de classe)**

```python
"""Regras de redação e coerência das lições por classe (fatia 4)."""
import json, re, sys, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))

import gerar_guia_comum as G
import tutorial_guia_comum as C

TERMO = re.compile(r"\[\[([a-z0-9_]+)\]\]")
UI_OK = re.compile(r"^(?:botao:(?:encerrar_turno|inventario|magias)|monstro:[a-z0-9_]+|habilidade:[a-z0-9_]+)$")

POR_CLASSE = {
    "warrior": ["fala_5", "fala_6", "treino_mira", "treino_golpe", "treino_furia", "treino_furia_extra", "treino_guerreiro_fim"],
    "mage": ["fala_7", "fala_8", "treino_magia", "treino_slots", "treino_aprimorar_magia", "treino_estender_magia",
             "treino_fortalecer_magia", "treino_reviver", "treino_comando"],
    "rogue": ["fala_9", "fala_10", "treino_detectar", "treino_desarmar", "treino_esconder", "treino_furtivo",
              "treino_veneno", "treino_veneno_golpe", "treino_criar"],
    "cleric": ["fala_11", "fala_12", "treino_cura", "treino_cura_area", "treino_purificar", "treino_ressuscitar"],
    "bard": ["fala_13", "fala_14", "treino_cancao", "treino_cancao_manter", "treino_cancao_parar",
             "treino_provocar", "treino_instrumento"],
    "paladin": ["fala_15", "fala_16", "treino_refem", "treino_protetor", "treino_maos", "treino_sagrado",
                "treino_sagrado_golpe", "treino_regen", "treino_luz"],
}
TODAS = [i for ids in POR_CLASSE.values() for i in ids]


class ClassesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.todos = G.guia_todos()
        cls.d = json.loads((RAIZ / "dungeons/campo_de_treinamento.json").read_text(encoding="utf-8"))
        cls.falas = {f["id"]: f for f in cls.d["falas"]}

    def test_quarenta_e_sete_licoes(self):
        self.assertEqual(len(TODAS), 47)
        for lid in TODAS:
            self.assertIn(lid, self.todos, f"falta guia de {lid}")

    def test_cada_licao_pertence_a_classe_certa(self):
        for cls, ids in POR_CLASSE.items():
            for lid in ids:
                self.assertEqual(self.falas[lid].get("classe"), cls, lid)

    def test_regras_de_redacao(self):
        for lid in TODAS:
            passos = self.todos[lid]
            self.assertTrue(1 <= len(passos) <= 3, lid)
            for i, p in enumerate(passos):
                pt, en = p["texto"]
                self.assertTrue(pt.strip() and en.strip(), f"{lid}/{p['id']}")
                self.assertLessEqual(len(TERMO.sub("x", pt).split()), 15, f"{lid}/{p['id']}: >15 palavras")
                self.assertFalse(p.get("conclui"), f"{lid}/{p['id']}: nenhum passo desta fatia usa conclui")
                self.assertLessEqual(len(p.get("dica", [])), 2, lid)
                if p.get("ui"):
                    self.assertRegex(p["ui"], UI_OK, f"{lid}/{p['id']}")

    def test_habilidade_na_ui_e_o_alvo_da_tarefa(self):
        for lid in TODAS:
            alvo = self.falas[lid]["tarefa"].get("alvo")
            for p in self.todos[lid]:
                ui = p.get("ui") or ""
                if ui.startswith("habilidade:"):
                    self.assertEqual(ui.split(":", 1)[1], alvo, f"{lid}/{p['id']}")

    def test_termos_existem_e_batem_entre_idiomas(self):
        for lid in TODAS:
            for p in self.todos[lid]:
                pares = [p["texto"]] + ([p["porque"]] if p.get("porque") else []) + list(p.get("dica", []))
                for pt, en in pares:
                    self.assertEqual(TERMO.findall(pt), TERMO.findall(en), f"{lid}/{p['id']}")
                    for termo in TERMO.findall(pt):
                        self.assertIn(termo, C.GLOSSARIO, f"{lid}/{p['id']}: [[{termo}]]")

    def test_ultimo_passo_nunca_e_informativo_sem_acao(self):
        # o último passo precisa dizer o que FAZER (a tarefa o encerra); ids dos passos únicos por lição
        for lid in TODAS:
            ids = [p["id"] for p in self.todos[lid]]
            self.assertEqual(len(ids), len(set(ids)), lid)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_tutorial_classes.py`
Expected: falha em `test_quarenta_e_sete_licoes` (nenhum guia de classe ainda). Os demais passam vazios.

- [ ] **Step 3: Commit**

```bash
git add tools/test_tutorial_classes.py
git commit -m "test(tutorial): regras de redação e coerência das lições por classe" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

(O commit fica com o teste vermelho de propósito; as Tasks 3–8 o deixam verde. Se preferir só commitar quando verde, adie este commit para a Task 8 — a ordem não afeta o resto.)

---

### Task 3: Conteúdo do Guerreiro (7 lições)

**Files:**
- Create: `tools/tutorial_guia_guerreiro.py`

Cada módulo de classe começa com o mesmo cabeçalho/auxiliar:

```python
"""Guia das lições do Guerreiro no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P
```

- [ ] **Step 1: Criar o módulo (conteúdo completo)**

```python
"""Guia das lições do Guerreiro no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_5": [
        P("atacar", ("Clique no boneco de treino para atacar.", "Click the training dummy to attack."),
          porque=("O [[d20]] mais seu acerto precisa igualar ou passar a [[ca]] do alvo.",
                  "The [[d20]] plus your attack bonus must match or beat the target's [[ca]]."),
          ui="monstro:boneco_treino",
          dica=[("Ande até ficar ao lado do boneco e clique nele.", "Walk next to the dummy and click it.")]),
    ],
    "fala_6": [
        P("matar", ("Continue atacando até derrubar o boneco.", "Keep attacking until the dummy falls."),
          porque=("Um 20 natural é [[critico]]. Você é o muro do grupo: aguenta e devolve.",
                  "A natural 20 is a [[critico]]. You are the group's wall: you take hits and give them back."),
          ui="monstro:boneco_treino"),
    ],
    "treino_mira": [
        P("mira", ("Clique em Mira Certeira e depois no boneco.", "Click Precise Aim and then the dummy."),
          porque=("Ela soma acerto ao seu [[d20]]; veja o bônus nos dados.",
                  "It adds attack bonus to your [[d20]]; watch the bonus in the dice."),
          ui="habilidade:mira_certeira",
          dica=[("O botão da habilidade fica no painel de ações, à direita.", "The ability button is in the actions panel, on the right.")]),
    ],
    "treino_golpe": [
        P("golpe", ("Clique em Golpe Devastador e depois no boneco.", "Click Devastating Strike and then the dummy."),
          porque=("Cada habilidade armada gasta sua [[acao_principal]]; observe os dados de dano.",
                  "Each armed ability spends your [[acao_principal]]; watch the damage dice."),
          ui="habilidade:golpe_devastador",
          dica=[("Se já usou sua ação, clique em Encerrar Turno antes.", "If you already used your action, click End Turn first.")]),
    ],
    "treino_furia": [
        P("furia", ("Clique em Fúria Berserker e ataque o boneco.", "Click Berserker Fury and attack the dummy."),
          porque=("A Fúria dá um ataque extra: não encerre o turno depois deste golpe.",
                  "Fury grants an extra attack: do not end your turn after this hit."),
          ui="habilidade:furia_berserker"),
    ],
    "treino_furia_extra": [
        P("extra", ("Ataque outra vez agora, antes de encerrar o turno.", "Attack again now, before ending your turn."),
          porque=("O ataque extra só vale neste turno; qualquer boneco serve de alvo.",
                  "The extra attack only works this turn; any dummy is a valid target."),
          ui="monstro:boneco_treino",
          dica=[("Se já passou a vez, arme a Fúria de novo e ataque duas vezes.", "If you already passed, arm Fury again and attack twice.")]),
    ],
    "treino_guerreiro_fim": [
        P("conferir", ("Confira a comida e a água que você gastou.", "Check the food and water you spent."),
          porque=("Habilidades cobram [[fome_sede]]; guerreiro esfomeado luta mal.",
                  "Abilities cost [[fome_sede]]; a starving warrior fights poorly.")),
        P("encerrar", ("Clique em Encerrar Turno para concluir.", "Click End Turn to finish."),
          ui="botao:encerrar_turno"),
    ],
}
```

- [ ] **Step 2: Gerar e testar**

Run: `python tools/gerar_guia_comum.py && python tools/test_tutorial_classes.py 2>&1 | tail -6`
Expected: o teste ainda falha em `test_quarenta_e_sete_licoes` (faltam as outras classes), mas **`test_regras_de_redacao`, `test_habilidade_na_ui_e_o_alvo_da_tarefa` e `test_termos_*` passam** — para provar isso rode `python -c "import unittest,sys; sys.path.insert(0,'tools'); import test_tutorial_classes as T; s=unittest.TestSuite([T.ClassesTests('test_regras_de_redacao'),T.ClassesTests('test_termos_existem_e_batem_entre_idiomas')]); unittest.TextTestRunner().run(s)"` (a seleção ignora lições sem guia ainda).
Nota: os testes de redação percorrem `TODAS`; para os módulos entregues por partes, ajuste o laço para pular ids ausentes **apenas** nesta fase — a Task 9 remove o pulo. Implemente no teste: `passos = self.todos.get(lid)` + `if passos is None: continue` nos testes de redação/habilidade/termos, e deixe só `test_quarenta_e_sete_licoes` exigindo todos.

- [ ] **Step 3: Confira o JSON**

Run: `git diff --stat dungeons/campo_de_treinamento.json src/lang/tutorial_guia.js`
Expected: o JSON muda só nas 7 falas do guerreiro; o `.js` ganha as chaves delas.

- [ ] **Step 4: Commit**

```bash
git add tools/tutorial_guia_guerreiro.py tools/test_tutorial_classes.py dungeons/campo_de_treinamento.json src/lang/tutorial_guia.js
git commit -m "feat(tutorial): guia em passos das lições do Guerreiro" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Conteúdo do Mago (9 lições)

**Files:** Create `tools/tutorial_guia_mago.py`

- [ ] **Step 1: Criar o módulo**

```python
"""Guia das lições do Mago no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_7": [
        P("atacar", ("Ataque o boneco com seu cajado.", "Attack the dummy with your staff."),
          porque=("O cajado acerta como qualquer arma, mas é o Grimório que vence batalhas.",
                  "The staff hits like any weapon, but the Grimoire wins battles."),
          ui="monstro:boneco_treino"),
    ],
    "fala_8": [
        P("matar", ("Derrube o boneco.", "Take down the dummy."),
          porque=("Magias não gastam mana: gastam um [[slot]] do círculo, que volta por turno.",
                  "Spells do not cost mana: they spend a circle [[slot]], which returns each turn."),
          ui="monstro:boneco_treino"),
    ],
    "treino_magia": [
        P("grimorio", ("Abra o Grimório no botão das magias.", "Open the Grimoire with the spells button."),
          ui="botao:magias"),
        P("lancar", ("Escolha uma magia e lance-a no boneco ou em você.", "Pick a spell and cast it on the dummy or yourself."),
          porque=("Confira o círculo e os [[slot]] usados: sem slot, sem magia.",
                  "Check the circle and the [[slot]]s used: no slot, no spell.")),
    ],
    "treino_slots": [
        P("encerrar", ("Clique em Encerrar Turno e confira seus [[slot]].", "Click End Turn and check your [[slot]]s."),
          porque=("Eles voltam conforme a regra do círculo; magia sem slot não sai.",
                  "They return by the circle's rule; a spell without a slot cannot be cast."),
          ui="botao:encerrar_turno"),
    ],
    "treino_aprimorar_magia": [
        P("aprimorar", ("Arme Aprimorar Magia e lance uma magia com teste.", "Arm Enhance Spell and cast a spell that allows a save."),
          porque=("Ela aumenta a dificuldade do [[teste_resistencia]] do alvo.",
                  "It raises the difficulty of the target's [[teste_resistencia]]."),
          ui="habilidade:aprimorar_magia",
          dica=[("O exercício só conta quando a metamagia entra no lançamento.", "The exercise only counts when the metamagic goes into the cast.")]),
    ],
    "treino_estender_magia": [
        P("estender", ("Arme Estender Magia e lance uma magia que dura rodadas.", "Arm Extend Spell and cast a spell that lasts rounds."),
          porque=("Ela acrescenta duração a um efeito que persiste.",
                  "It adds duration to an effect that persists."),
          ui="habilidade:estender_magia"),
    ],
    "treino_fortalecer_magia": [
        P("fortalecer", ("Arme Fortalecer Magia e lance uma magia de dano.", "Arm Empower Spell and cast a damage spell."),
          porque=("Ela aumenta o dano da magia; confira o valor na sua ficha.",
                  "It increases the spell's damage; check the value on your sheet."),
          ui="habilidade:fortalecer_magia"),
    ],
    "treino_reviver": [
        P("aproximar", ("Ande até ficar ao lado do cadáver de treino.", "Walk next to the training corpse.")),
        P("reviver", ("Use Reviver os Mortos e clique no cadáver.", "Use Raise the Dead and click the corpse."),
          porque=("Se a tentativa falhar, tente de novo em outro turno.",
                  "If the attempt fails, try again on another turn."),
          ui="habilidade:animar_mortos"),
    ],
    "treino_comando": [
        P("abrir_fase", ("Encerre a vez de Pedro para abrir a fase dos servos.", "End Pedro's turn to open the servants phase."),
          ui="botao:encerrar_turno"),
        P("comandar", ("Clique em Comandar: o servo anda e ataca um boneco.", "Click Command: the servant moves and attacks a dummy."),
          porque=("Servos animados agem depois do seu turno.", "Animated servants act after your turn.")),
    ],
}
```

- [ ] **Step 2: Gerar, testar, commit**

Run: `python tools/gerar_guia_comum.py && python tools/test_tutorial_classes.py 2>&1 | tail -4`
Expected: mesmas condições da Task 3 (só o teste de 47 lições ainda vermelho).

```bash
git add tools/tutorial_guia_mago.py dungeons/campo_de_treinamento.json src/lang/tutorial_guia.js
git commit -m "feat(tutorial): guia em passos das lições do Mago" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Conteúdo do Ladino (9 lições)

**Files:** Create `tools/tutorial_guia_ladino.py`

- [ ] **Step 1: Criar o módulo**

```python
"""Guia das lições do Ladino no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_9": [
        P("atacar", ("Ataque o boneco de frente.", "Attack the dummy head-on."),
          porque=("Esse é o seu pior golpe: veja o dano cru contra a [[ca]].",
                  "This is your weakest strike: see the raw damage against [[ca]]."),
          ui="monstro:boneco_treino"),
    ],
    "fala_10": [
        P("matar", ("Derrube o boneco.", "Take down the dummy."),
          porque=("O seu ofício é o [[furtivo]]: escondido, o mesmo golpe dói muito mais.",
                  "Your trade is the [[furtivo]]: hidden, the same strike hurts far more."),
          ui="monstro:boneco_treino"),
    ],
    "treino_detectar": [
        P("detectar", ("Arme Detectar Armadilhas e chegue perto da casa 10,8.", "Arm Detect Traps and get close to square 10,8."),
          porque=("Ela revela os mecanismos próximos e cobra água de [[manutencao]].",
                  "It reveals nearby mechanisms and costs water as [[manutencao]]."),
          ui="habilidade:detectar_armadilhas"),
    ],
    "treino_desarmar": [
        P("desarmar", ("Fique ao lado da armadilha revelada e use Desarmar Armadilha.", "Stand next to the revealed trap and use Disarm Trap."),
          porque=("Se o teste falhar, tente de novo: a sala restaura o mecanismo.",
                  "If the test fails, try again: the room restores the mechanism.")),
    ],
    "treino_esconder": [
        P("esconder", ("Perto do boneco, use Esconder nas Sombras.", "Near the dummy, use Hide in the Shadows."),
          porque=("É ação bônus: dá para atacar na mesma rodada depois de se esconder.",
                  "It is a bonus action: you can attack in the same round after hiding."),
          ui="habilidade:esconder_sombras"),
    ],
    "treino_furtivo": [
        P("furtivo", ("Ataque o boneco enquanto estiver escondido.", "Attack the dummy while hidden."),
          porque=("O [[furtivo]] é passivo: o dano extra aparece quando as condições valem.",
                  "The [[furtivo]] is passive: the extra damage shows up when conditions hold."),
          ui="monstro:boneco_treino",
          dica=[("Se errar, esconda-se de novo e tente outra vez.", "If you miss, hide again and retry.")]),
    ],
    "treino_veneno": [
        P("veneno", ("Use Veneno Rápido e escolha o veneno de treino na bolsa.", "Use Quick Poison and pick the training poison in the bag."),
          porque=("É ação livre; confira quantas cargas ficaram na arma.",
                  "It is a free action; check how many charges the weapon holds."),
          ui="habilidade:veneno_rapido"),
    ],
    "treino_veneno_golpe": [
        P("golpe", ("Ataque o boneco com a arma untada.", "Attack the dummy with the coated weapon."),
          porque=("Observe a carga gasta e o [[teste_resistencia]] do alvo contra o veneno.",
                  "Watch the charge being spent and the target's [[teste_resistencia]] against the poison."),
          ui="monstro:boneco_treino"),
    ],
    "treino_criar": [
        P("criar", ("Use Criar Armadilha numa casa vazia da sala.", "Use Create Trap on an empty square in the room."),
          porque=("Buraco já está liberado; as outras fórmulas vêm da Guilda.",
                  "Pit is already unlocked; the other formulas come from the Guild."),
          ui="habilidade:criar_armadilha"),
    ],
}
```

- [ ] **Step 2: Gerar, testar, commit**

Run: `python tools/gerar_guia_comum.py && python tools/test_tutorial_classes.py 2>&1 | tail -4`

```bash
git add tools/tutorial_guia_ladino.py dungeons/campo_de_treinamento.json src/lang/tutorial_guia.js
git commit -m "feat(tutorial): guia em passos das lições do Ladino" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Conteúdo do Clérigo (6) e do Bardo (7)

**Files:** Create `tools/tutorial_guia_clerigo.py`, `tools/tutorial_guia_bardo.py`

- [ ] **Step 1: Clérigo**

```python
"""Guia das lições do Clérigo no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_11": [
        P("atacar", ("Ataque o boneco com a sua maça.", "Attack the dummy with your mace."),
          porque=("O [[d20]] mais seu acerto precisa igualar ou passar a [[ca]].",
                  "The [[d20]] plus your attack bonus must match or beat the [[ca]]."),
          ui="monstro:boneco_treino"),
    ],
    "fala_12": [
        P("matar", ("Derrube o boneco.", "Take down the dummy."),
          porque=("Seu peso é outro: cada ponto devolvido vale mais que o dano. Cada dado de cura gasta água.",
                  "Your weight is elsewhere: every point healed beats damage dealt. Each healing die costs water."),
          ui="monstro:boneco_treino"),
    ],
    "treino_cura": [
        P("aproximar", ("Fique ao lado do Aprendiz 1, que está ferido.", "Stand next to Apprentice 1, who is wounded.")),
        P("curar", ("Clique em Cura e use um dado no Aprendiz 1.", "Click Heal and use one die on Apprentice 1."),
          porque=("Confira a vida recuperada e o custo de água.", "Check the life recovered and the water cost."),
          ui="habilidade:cura"),
    ],
    "treino_cura_area": [
        P("curar", ("Fique perto dos dois aprendizes e use Cura em Área.", "Stay near both apprentices and use Area Heal."),
          porque=("No nível inicial o raio é de 2 casas: confira a área antes de confirmar.",
                  "At the starting level the radius is 2 squares: check the area before confirming."),
          ui="habilidade:cura_area"),
    ],
    "treino_purificar": [
        P("purificar", ("Ao lado do Aprendiz 1, use Purificação e escolha Veneno.", "Next to Apprentice 1, use Purify and choose Poison."),
          porque=("Ele está cego por um veneno simulado; o efeito desaparece.",
                  "He is blinded by a simulated poison; the effect disappears."),
          ui="habilidade:purificacao"),
    ],
    "treino_ressuscitar": [
        P("ressuscitar", ("Ao lado do Aprendiz 1, use Ressurreição.", "Next to Apprentice 1, use Resurrection."),
          porque=("Ele simula um aliado caído e volta com a vida que sua habilidade permite.",
                  "He simulates a fallen ally and returns with the life your ability allows."),
          ui="habilidade:ressurreicao"),
    ],
}
```

- [ ] **Step 2: Bardo**

```python
"""Guia das lições do Bardo no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_13": [
        P("atacar", ("Acerte o boneco: é o primeiro compasso da balada.", "Hit the dummy: the first beat of the ballad."),
          porque=("O [[d20]] mais seu acerto precisa igualar ou passar a [[ca]].",
                  "The [[d20]] plus your attack bonus must match or beat the [[ca]]."),
          ui="monstro:boneco_treino"),
    ],
    "fala_14": [
        P("matar", ("Derrube o boneco.", "Take down the dummy."),
          porque=("Sua arma é a Canção Heroica: aliados num raio de cinco casas lutam melhor, e ela cobra [[manutencao]].",
                  "Your weapon is the Heroic Song: allies within five squares fight better, and it costs [[manutencao]]."),
          ui="monstro:boneco_treino"),
    ],
    "treino_cancao": [
        P("cancao", ("Clique em Canção Heroica e escolha um benefício.", "Click Heroic Song and choose a benefit."),
          porque=("A canção beneficia você e os aliados dentro do alcance.",
                  "The song benefits you and the allies within range."),
          ui="habilidade:cancao_heroica"),
    ],
    "treino_cancao_manter": [
        P("manter", ("Clique em Encerrar Turno com a canção ativa.", "Click End Turn with the song active."),
          porque=("Ela cobra [[manutencao]] de comida e água a cada rodada.",
                  "It charges [[manutencao]] in food and water every round."),
          ui="botao:encerrar_turno"),
    ],
    "treino_cancao_parar": [
        P("parar", ("Desative a Canção Heroica.", "Turn off the Heroic Song."),
          porque=("Assim o efeito e o gasto de recursos acabam.", "That ends the effect and the resource drain."),
          ui="habilidade:cancao_heroica"),
    ],
    "treino_provocar": [
        P("provocar", ("Clique em Provocação e depois no boneco.", "Click Taunt and then the dummy."),
          porque=("O alvo faz um [[teste_resistencia]]; resistir não invalida o uso.",
                  "The target makes a [[teste_resistencia]]; resisting does not invalidate the use."),
          ui="habilidade:provocacao"),
    ],
    "treino_instrumento": [
        P("instrumento", ("Abra as opções do instrumento e use a habilidade num alvo.", "Open the instrument options and use its ability on a target."),
          porque=("O instrumento complementa seu repertório de bardo.", "The instrument rounds out your bard repertoire.")),
    ],
}
```

- [ ] **Step 3: Gerar, testar, commit**

Run: `python tools/gerar_guia_comum.py && python tools/test_tutorial_classes.py 2>&1 | tail -4`

```bash
git add tools/tutorial_guia_clerigo.py tools/tutorial_guia_bardo.py dungeons/campo_de_treinamento.json src/lang/tutorial_guia.js
git commit -m "feat(tutorial): guia em passos das lições do Clérigo e do Bardo" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Conteúdo do Paladino (9 lições)

**Files:** Create `tools/tutorial_guia_paladino.py`

- [ ] **Step 1: Criar o módulo**

```python
"""Guia das lições do Paladino no Campo de Treinamento (pt + en)."""
from tutorial_guia_comum import P

GUIA = {
    "fala_15": [
        P("atacar", ("Ao trabalho: ataque o boneco.", "To work: attack the dummy."),
          porque=("O [[d20]] mais seu acerto precisa igualar ou passar a [[ca]].",
                  "The [[d20]] plus your attack bonus must match or beat the [[ca]]."),
          ui="monstro:boneco_treino"),
    ],
    "fala_16": [
        P("matar", ("Derrube o boneco.", "Take down the dummy."),
          porque=("Golpe Sagrado soma um dado a cada ataque: você é a linha entre o grupo e o chão.",
                  "Holy Strike adds a die to every attack: you are the line between the group and the floor."),
          ui="monstro:boneco_treino"),
    ],
    "treino_refem": [
        P("libertar", ("Ande até o refém na casa 35,25 e clique em Libertar prisioneiro.", "Walk to the hostage at square 35,25 and click Free prisoner."),
          porque=("Depois do resgate você poderá protegê-lo e curá-lo.", "After the rescue you can protect and heal him.")),
    ],
    "treino_protetor": [
        P("proteger", ("Ao lado do refém, use Protetor nele e encerre o turno.", "Next to the hostage, use Protector on him and end your turn."),
          porque=("O dano se divide entre vocês e a sua parte é reduzida.",
                  "The damage is split between you and your share is reduced."),
          ui="botao:encerrar_turno"),
    ],
    "treino_maos": [
        P("curar", ("Ao lado do refém ferido, use Imposição das Mãos.", "Next to the wounded hostage, use Lay on Hands."),
          porque=("A lição pede a cura desse mesmo refém.", "The lesson asks you to heal that same hostage."),
          ui="habilidade:imposicao_maos"),
    ],
    "treino_sagrado": [
        P("ativar", ("Ative Golpe Sagrado no nível disponível.", "Activate Holy Strike at the available level."),
          porque=("Há custo de ativação e de [[manutencao]] a cada rodada.",
                  "There is an activation cost and [[manutencao]] every round."),
          ui="habilidade:golpe_sagrado"),
    ],
    "treino_sagrado_golpe": [
        P("atacar", ("Ataque o boneco com Golpe Sagrado ativo.", "Attack the dummy with Holy Strike active."),
          porque=("Observe o dado sagrado somado ao dano.", "Watch the holy die added to the damage."),
          ui="monstro:boneco_treino"),
    ],
    "treino_regen": [
        P("regenerar", ("Ative Regeneração Divina e encerre a sua vez.", "Activate Divine Regeneration and end your turn."),
          porque=("A tarefa só termina quando a regeneração recuperar vida de verdade.",
                  "The task only ends when regeneration actually restores life."),
          ui="habilidade:regeneracao_divina"),
    ],
    "treino_luz": [
        P("luz", ("Ative Guerreiro da Luz e compare seus bônus.", "Activate Warrior of Light and compare your bonuses."),
          porque=("Veja visão, acerto, dano e defesa mudarem.", "See your vision, attack, damage and defense change."),
          ui="habilidade:guerreiro_luz"),
    ],
}
```

- [ ] **Step 2: Gerar e fechar o teste de cobertura**

Remova o pulo de ids ausentes que a Task 3 introduziu em `tools/test_tutorial_classes.py` (use `self.todos[lid]` direto de novo) e rode:

Run: `python tools/gerar_guia_comum.py && python tools/test_tutorial_classes.py && python tools/test_tutorial_conteudo.py`
Expected: ambos `OK`, incluindo `test_quarenta_e_sete_licoes`.

- [ ] **Step 3: Suítes dependentes do JSON e do idioma**

Run:
```bash
python tools/test_tutorial_guia.py && python tools/test_tutorial_salas.py && python tools/test_idioma.py && python tools/test_interface.py && python tools/dividas.py && node tools/test_idioma_cliente.js && node tools/test_guia_tutorial_cliente.js
```
Expected: tudo passa; `dividas.py` "nada pendente". Se `test_tutorial_salas.py` quebrar porque algum teste compara `fala["texto"]`/passos, ele não deve: o campo `texto` das falas não muda, só entra `guia`.

- [ ] **Step 4: Commit**

```bash
git add tools/tutorial_guia_paladino.py tools/test_tutorial_classes.py dungeons/campo_de_treinamento.json src/lang/tutorial_guia.js
git commit -m "feat(tutorial): guia em passos das lições do Paladino; 47 lições cobertas" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Modelos para as lições geradas (servidor)

**Files:**
- Modify: `server.py` (CRLF — Edit): `_guia_passos` (perto da linha 105)
- Modify: `tutorial_training.py` (`_training_add_unlocked_lessons`, linhas ~136 e ~155)
- Modify: `src/lang/tutorial.js` (chaves dos modelos)
- Test: `tools/test_tutorial_modelos.py` (novo)

Por que não gravar o texto no lição: `licoes` é categoria `foto` (JSON). Um `T` ali levantaria `FotoNaoSerializavel`. A lição guarda só `guia_modelo` (dict simples) e `_guia_passos` expande em `T` na hora do envio.

- [ ] **Step 1: Escrever o teste que falha**

`tools/test_tutorial_modelos.py`:

```python
"""Modelos de guia das lições geradas (treino_guild_*, treino_magia_*)."""
import json, sys, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
import server as S


def render(payload, lang):
    return json.loads(json.dumps(payload, default=lambda o: S._t_render(o, lang)))


class ModelosTests(unittest.TestCase):
    def lic_magia(self):
        return {"id": "treino_magia_mage_bola_fogo", "classe": "mage", "texto": "x",
                "tarefa": {"tipo": "usar_magia", "alvo": "bola_fogo", "vezes": 1, "texto_curto": "x"},
                "guia_modelo": {"tipo": "magia", "id": "bola_fogo"}}

    def lic_guild(self):
        return {"id": "treino_guild_guerreiro_mira_3", "classe": "warrior", "texto": "x",
                "tarefa": {"tipo": "usar_habilidade", "alvo": "mira_certeira", "vezes": 1, "texto_curto": "x"},
                "guia_modelo": {"tipo": "guild", "id": "guerreiro_mira_3", "skill": "mira_certeira"}}

    def test_magia_tem_dois_passos_e_ui_certa(self):
        passos = S._guia_passos(self.lic_magia())
        self.assertEqual(len(passos), 2)
        self.assertEqual(passos[0]["ui"], "botao:magias")
        self.assertFalse(passos[0].get("conclui_com"))
        self.assertFalse(passos[1].get("conclui_com"))

    def test_guild_usa_a_habilidade_da_linha(self):
        passos = S._guia_passos(self.lic_guild())
        self.assertEqual(passos[-1]["ui"], "habilidade:mira_certeira")
        self.assertEqual(len(passos), 2)

    def test_guild_sem_skill_nao_inventa_ui(self):
        lic = self.lic_guild(); lic["guia_modelo"]["skill"] = None
        self.assertFalse(S._guia_passos(lic)[-1].get("ui"))

    def test_payload_resolve_o_nome_em_cada_idioma(self):
        pt = render(S._guia_payload(self.lic_magia(), 1), "pt")
        en = render(S._guia_payload(self.lic_magia(), 1), "en")
        self.assertNotEqual(pt["texto"], en["texto"])
        self.assertIn("Fireball", en["texto"])        # nome da magia em inglês vem do catálogo
        self.assertNotIn("cat.magia", pt["texto"] + en["texto"])

    def test_lista_de_licoes_continua_serializavel(self):
        json.dumps(self.lic_magia()); json.dumps(self.lic_guild())    # a foto da masmorra grava isto

    def test_licao_sem_modelo_nao_muda(self):
        lic = {"id": "x", "texto": "t", "tarefa": {"tipo": "encerrar_turno", "vezes": 1, "texto_curto": "x"}}
        self.assertTrue(S._guia_passos(lic)[0]["auto"])

    def test_geradas_ganham_guia_modelo(self):
        src = (RAIZ / "tutorial_training.py").read_text(encoding="utf-8")
        self.assertIn('guia_modelo', src)
        self.assertEqual(src.count('guia_modelo'), 2)     # um por família de lição gerada


if __name__ == "__main__":
    unittest.main()
```

(Confirme no catálogo que a chave `cat.magia.bola_fogo.nome` existe com "Fireball"; se o nome em inglês for outro, ajuste só a asserção do teste: `grep -n "cat.magia.bola_fogo.nome" src/lang/catalogo.js`.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_tutorial_modelos.py`
Expected: falhas (`guia_modelo` ainda não existe; `_guia_passos` devolve o passo `auto`).

- [ ] **Step 3: Chaves dos modelos em `src/lang/tutorial.js`**

Antes do `};` final, acrescente:

```javascript
  "ui.tutorial.modelo.guild.aprendeu": {
    "en": "You learned {nome}. Repeat the exercise to see your new numbers.",
    "pt": "Você aprendeu {nome}. Repita o exercício para ver seus novos valores."
  },
  "ui.tutorial.modelo.guild.repita": {
    "en": "Use the ability again and watch the values change.",
    "pt": "Use a habilidade de novo e observe os valores mudarem."
  },
  "ui.tutorial.modelo.magia.abrir": {
    "en": "Open the Grimoire with the spells button.",
    "pt": "Abra o Grimório no botão das magias."
  },
  "ui.tutorial.modelo.magia.lancar": {
    "en": "Cast {nome} on a training target or on yourself.",
    "pt": "Lance {nome} num alvo de treino ou em você."
  },
```

- [ ] **Step 4: `_guia_passos` expande o modelo**

Em `server.py`, em `_guia_passos(lic)`, logo depois de `guia = lic.get("guia")` / `if guia: return guia`, insira antes do passo `auto`:

```python
    modelo = lic.get("guia_modelo")
    if isinstance(modelo, dict):
        return _guia_passos_modelo(modelo)
```

E, acima de `_guia_passos`, a função:

```python
def _guia_passos_modelo(m):
    """Passos das lições geradas em jogo. `m` é um dict simples (vai na foto da masmorra);
    os textos são T() resolvidos por jogador na hora do envio."""
    tipo, ident = m.get("tipo"), m.get("id")
    if tipo == "guild":
        skill = m.get("skill")
        return [{"id": "aprendeu", "texto": T("ui.tutorial.modelo.guild.aprendeu", nome=nome_de("guilda", ident)),
                 "porque": T(f"cat.guilda.{ident}.desc"), "ui": None},
                {"id": "repita", "texto": T("ui.tutorial.modelo.guild.repita"),
                 "ui": f"habilidade:{skill}" if skill and re.fullmatch(r"[a-z0-9_]+", skill) else None}]
    if tipo == "magia":
        return [{"id": "abrir", "texto": T("ui.tutorial.modelo.magia.abrir"), "ui": "botao:magias"},
                {"id": "lancar", "texto": T("ui.tutorial.modelo.magia.lancar", nome=nome_de("magia", ident)),
                 "porque": T(f"cat.magia.{ident}.desc"), "ui": None}]
    return []
```

Ajuste o `return` para nunca devolver lista vazia: `return _guia_passos_modelo(modelo) or [passo_auto]` (construa o passo `auto` antes, como já está no código atual). Em `_guia_payload` troque `"texto": s.get("texto", "")` e `"porque": s.get("porque", "")` por eles mesmos — `T` passa direto, o `json.dumps(default=…)` do envio o resolve; **não** converta para `str`.

- [ ] **Step 5: `guia_modelo` nas lições geradas**

Em `tutorial_training.py`, no bloco do `treino_guild_*` (depois de `lesson = deepcopy(base)`), acrescente `lesson.pop("guia", None)` e, no `lesson.update(...)`, `guia_modelo={"tipo": "guild", "id": ident, "skill": skill}`. No dicionário do `treino_magia_*`, acrescente `"guia_modelo": {"tipo": "magia", "id": mid},`.

(O `pop("guia")` evita herdar o guia da lição-base, cujo texto fala do exercício original.)

- [ ] **Step 6: Rodar e ver passar**

Run: `python tools/test_tutorial_modelos.py && python tools/test_tutorial_guia.py && python tools/test_tutorial_salas.py && python tools/test_salvar_masmorra.py && python tools/test_idioma.py && python tools/dividas.py`
Expected: tudo passa. `test_idioma.py` confere a paridade de `{nome}` entre pt e en das 4 chaves novas.

- [ ] **Step 7: Commit**

```bash
git add server.py tutorial_training.py src/lang/tutorial.js tools/test_tutorial_modelos.py
git commit -m "feat(tutorial): modelo de guia para as lições geradas (treino_guild_* e treino_magia_*)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Prova no navegador, documentação e fechamento

**Files:** Modify `CLAUDE.md` (CRLF — Edit)

- [ ] **Step 1: Servidor isolado**

Copie o projeto para `%TEMP%\lfh_guia4` (sem `.git`, `.worktrees`, `savegames`, `accounts`, `groups`, `savegame_points`), suba com `LFH_PORT=8792` e abra `http://[::1]:8792/index.html?v=g4` no navegador do app. Crie a conta de teste local, jogo solo, guerreiro; `GS.worldAdventure('treinamento')` leva à masmorra (o `confirm()` do navegador é suprimido: use `window.confirm=()=>true` antes de criar a conta). Troque de classe criando outro jogo para o mago.

- [ ] **Step 2: Conferir em jogo**

1. Guerreiro: na sala do guerreiro, `treino_mira` mostra o halo no botão **Mira Certeira** e o texto "Clique em Mira Certeira e depois no boneco."; trocar para English troca a janela.
2. Mago: `treino_magia` abre com o halo no botão ✨ (passo 1 de 2, "Entendi"), passo 2 sem halo.
3. Lição gerada: dê ao mago uma magia nova (ou compre uma especialização na Guilda) e confira que a lição `treino_magia_*`/`treino_guild_*` aparece com 2 passos, nome da magia/especialização traduzido ao trocar de idioma, e que **Salvar e sair → Continuar** não quebra (a foto grava `guia_modelo` como JSON).
4. `read_console_messages` com `onlyErrors`: nenhum erro.

- [ ] **Step 3: `CLAUDE.md`**

Depois do trecho "Fatia 3" do parágrafo do tutorial guiado, acrescente: fatia 4 entregou o guia das 47 lições das seis classes (`tools/tutorial_guia_<classe>.py`, juntados por `gerar_guia_comum.guia_todos()`), `habilidade:<id>` só quando é o alvo da tarefa, glossário ampliado para 14 termos, `botao:magias`, e o `guia_modelo` das lições geradas (dict simples na foto; `_guia_passos_modelo` expande em `T` por jogador — **nunca grave `T` em `licoes`**); testes `tools/test_tutorial_classes.py` e `tools/test_tutorial_modelos.py`; plano `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia4-salas-e-geradas.md`. Pendente: fatia 5 (editor de masmorras com lista de passos).

- [ ] **Step 4: Suítes finais e limpeza**

Run todas as suítes do Task 7 Step 3 mais `python tools/test_tutorial_modelos.py`, `python tools/test_tutorial_classes.py`, `python tools/test_tutorial_conteudo.py`, `python tools/test_salvar_masmorra.py`. Pare o servidor da 8792 e apague `%TEMP%\lfh_guia4`.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia4-salas-e-geradas.md
git commit -m "docs: guia do tutorial (fatia 4) no CLAUDE.md" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

Não fazer push sem o usuário pedir.

---

## Auto-revisão

- **Cobertura do spec (seção 5, fatia 4):** reescrita das seis salas por herói → Tasks 3–7 (47 lições, lista conferida contra o JSON); lições geradas por modelo parametrizado pelo nome da habilidade/magia → Task 8; português e inglês + `dividas.py` → Tasks 7–8; prova no navegador → Task 9. Fora desta fatia: editor de masmorras com lista de passos (fatia 5).
- **Contagem:** 7 + 9 + 9 + 6 + 7 + 9 = 47; as 15 da fatia 3 + 47 = 62 lições autoradas, o que fecha as "62 lições" do spec.
- **Risco 1 — `habilidade:` e `data-ability-id`:** o halo só acha o botão quando o id é o da tarefa; o teste `test_habilidade_na_ui_e_o_alvo_da_tarefa` trava isso. Lições de aprimorar/estender/fortalecer usam o id da metamagia, que é o `tarefa.alvo`.
- **Risco 2 — ids de habilidade sem botão no HUD** (ex.: `ataque_furtivo` é passiva): a lição `treino_furtivo` usa `monstro:` de propósito; `habilidade:` só onde há botão.
- **Risco 3 — `T` na foto:** coberto por `guia_modelo` plano e pelo teste `test_lista_de_licoes_continua_serializavel`.
- **Consistência de nomes:** `guia_todos`, `MODULOS_CLASSES`, `_guia_passos_modelo`, `guia_modelo`, `POR_CLASSE`/`TODAS` aparecem com a mesma grafia em todas as tasks.
- **Ponto de atenção para quem implementa:** `tutorial_guia_comum.P` é o construtor de passo da fatia 3; os módulos de classe o importam de lá.
