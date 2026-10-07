# Tutorial guiado — fatia 3 (glossário e trilha comum) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reescrever em passos curtos as 15 lições da trilha comum do Campo de Treinamento (`fala_0` a `fala_38`) e dar ao texto do tutorial um glossário de termos de RPG com balão.

**Architecture:** O conteúdo mora num módulo de dados Python (`tools/tutorial_guia_comum.py`, pt + en). Um gerador (`tools/gerar_guia_comum.py`) grava `src/lang/tutorial_guia.js` (chaves `ui.tutorial.guia.*` e `ui.tutorial.glossario.*`) e injeta `guia` (só chaves) nas falas de `dungeons/campo_de_treinamento.json`; `configurar_tutorial_salas.py` chama o mesmo `aplicar_guia` para o conteúdo sobreviver a uma regeneração. O cliente ganha `GuiaTutorial.segmentos` (puro) e o `game.js` desenha os termos sublinhados e o balão.

**Tech Stack:** Python 3 (`unittest`), JS puro (node para teste), `src/lang/*.js`, `game.js`/`game.css` (CRLF, usar a ferramenta Edit).

Spec: `docs/superpowers/specs/2026-10-07-tutorial-guiado-design.md` (seções 4.4 e 5). Fatias 1 e 2 já estão em `master`.

## Regras de conteúdo (valem para todos os passos)

1. Uma ação por passo; verbo no imperativo; **no máximo 15 palavras** em `texto`.
2. O `porque` vem depois da ação e explica o motivo em uma frase.
3. Termo do glossário aparece como `[[termo]]` (ex.: `[[ca]]`).
4. O último passo de cada lição **nunca** tem `conclui_com` (quem encerra é a tarefa).
5. **Nunca use `conclui_com` para um evento que o jogador pode ter feito ANTES da lição começar** (ex.: `pegar_item` de baú compartilhado: se ele pegou tudo antes, o passo trava). Passo que descreve uma ação já possível é **informativo** (botão "Entendi").
6. `ui` só usa ids confirmados: `botao:encerrar_turno`, `botao:inventario`, `casa:[x,y]`, `porta:[x,y]`, `bolsa:<id do item>`, `monstro:<tipo>`.

Glossário (7 termos): `turno`, `movimento`, `acao_livre`, `acao_bonus`, `ca`, `fome_sede`, `resistencia`.

## Estrutura de arquivos

| Arquivo | Ação | Responsabilidade |
|---|---|---|
| `src/guiaTutorial.js` | modificar | `segmentos(texto, vistos)` puro: quebra o texto em pedaços de texto e de termo |
| `tools/test_guia_tutorial_cliente.js` | modificar | seção [15] do glossário |
| `game.js` | modificar | `_tutHTML` (termos sublinhados + balão) usado em texto, porquê e dica |
| `game.css` | modificar | `.guia-termo` e `#guia-balao` |
| `tools/tutorial_guia_comum.py` | criar | dados: `GLOSSARIO` e `GUIA` (pt + en) |
| `tools/gerar_guia_comum.py` | criar | `aplicar_guia(d)`, `gerar_lang()`, `main()` |
| `tools/test_tutorial_conteudo.py` | criar | regras de conteúdo, paridade pt/en, validação pelo servidor |
| `tools/configurar_tutorial_salas.py` | modificar | chama `aplicar_guia(d)` antes de gravar |
| `src/lang/tutorial_guia.js` | gerado | chaves do guia e do glossário |
| `index.html` | modificar | carrega `tutorial_guia.js` |
| `dungeons/campo_de_treinamento.json` | gerado | `guia` nas 15 falas |
| `CLAUDE.md` | modificar | parágrafo da fatia 3 |

---

### Task 1: `segmentos` — glossário puro

**Files:**
- Modify: `src/guiaTutorial.js` (antes do `window.GuiaTutorial = …`)
- Test: `tools/test_guia_tutorial_cliente.js` (nova seção antes do `console.log` final)

- [ ] **Step 1: Escrever o teste que falha**

Acrescente antes do `console.log` final do arquivo (use o helper `check`/`ok` que o arquivo já usa; abra o arquivo e siga o estilo das seções [7]–[14]):

```javascript
// [15] glossário: [[termo]] vira segmento; só o 1º de cada termo é sublinhado
{
  const vistos = new Set();
  const a = GuiaTutorial.segmentos('Gaste [[movimento]] e depois [[movimento]] de novo, com [[ca]].', vistos);
  check('[15] pedaços na ordem', a.map(s => s.termo ? '#' + s.termo : s.texto).join('|')
    === 'Gaste |#movimento| e depois |#movimento| de novo, com |#ca|.');
  check('[15] 1ª ocorrência é "primeira"', a[1].primeira === true);
  check('[15] 2ª ocorrência não é "primeira"', a[3].primeira === false);
  check('[15] vistos guarda os termos', vistos.has('movimento') && vistos.has('ca'));
  const b = GuiaTutorial.segmentos('Outro [[movimento]].', vistos);
  check('[15] vistos persiste entre chamadas', b[1].primeira === false);
  const c = GuiaTutorial.segmentos('sem marcas', new Set());
  check('[15] texto sem marca vira 1 pedaço', c.length === 1 && c[0].texto === 'sem marcas' && !c[0].termo);
  const d = GuiaTutorial.segmentos('[[Inválido]] e [[ok_1]]', new Set());
  check('[15] só id minúsculo vira termo', d.some(s => s.termo === 'ok_1') && !d.some(s => s.termo === 'Inválido'));
  check('[15] entrada não-string é segura', GuiaTutorial.segmentos(null, new Set()).length === 0);
}
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: erro `GuiaTutorial.segmentos is not a function`.

- [ ] **Step 3: Implementar**

Em `src/guiaTutorial.js`, antes de `window.GuiaTutorial = …`:

```javascript
  // Quebra o texto em pedaços: {texto} ou {termo, primeira}. `[[termo]]` só vale com
  // id minúsculo; `vistos` (Set) guarda o que já apareceu para sublinhar só a 1ª vez.
  function segmentos(texto, vistos) {
    if (typeof texto !== 'string' || !texto) return [];
    const ve = vistos || new Set();
    const out = [];
    const re = /\[\[([a-z0-9_]+)\]\]/g;
    let ultimo = 0, m;
    while ((m = re.exec(texto))) {
      if (m.index > ultimo) out.push({ texto: texto.slice(ultimo, m.index) });
      out.push({ termo: m[1], primeira: !ve.has(m[1]) });
      ve.add(m[1]);
      ultimo = m.index + m[0].length;
    }
    if (ultimo < texto.length) out.push({ texto: texto.slice(ultimo) });
    return out;
  }
```

E na exportação: `window.GuiaTutorial = { parseUi, seletor, alvoTabuleiro, caminhoAbsoluto, nivelDica, textoDica, segmentos };`

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: `… ok, 0 falha(s)` (90 ok aproximadamente), nenhuma falha.

- [ ] **Step 5: Commit**

```bash
git add src/guiaTutorial.js tools/test_guia_tutorial_cliente.js
git commit -m "feat(tutorial): glossário puro no módulo do guia (segmentos)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Desenho do glossário e balão no cliente

**Files:**
- Modify: `game.js` (CRLF — use Edit): perto de `_tutTexto` (~linha 53699) e em `_mostrarJanelaLicao`
- Modify: `game.css`
- Test: `tools/test_guia_tutorial_cliente.js` (checagens estáticas de fiação)

- [ ] **Step 1: Escrever o teste de fiação que falha**

Acrescente após a seção [15] (o arquivo já lê `game.js` como texto nas seções anteriores; reutilize essa variável — procure por `readFileSync` no topo):

```javascript
// [16] fiação do glossário no game.js e no css
{
  const gjs = fs.readFileSync(path.join(__dirname, '..', 'game.js'), 'utf8');
  const css = fs.readFileSync(path.join(__dirname, '..', 'game.css'), 'utf8');
  check('[16] game.js usa GuiaTutorial.segmentos', /GuiaTutorial\.segmentos\(/.test(gjs));
  check('[16] game.js define _tutHTML', /function _tutHTML\(/.test(gjs));
  check('[16] texto da lição passa por _tutHTML', /class="licao-texto">\$\{_tutHTML\(/.test(gjs));
  check('[16] balão do glossário existe', /guia-balao/.test(gjs) && /#guia-balao/.test(css));
  check('[16] termo sublinhado no css', /\.guia-termo/.test(css));
  check('[16] chave de definição usa ui.tutorial.glossario', /ui\.tutorial\.glossario\./.test(gjs));
}
```

(Se o arquivo já importa `fs`/`path` com outros nomes, use os existentes.)

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_guia_tutorial_cliente.js`
Expected: falhas em `[16]`.

- [ ] **Step 3: Implementar em `game.js`**

Logo abaixo de `_tutTexto`, acrescente:

```javascript
// Termos já sublinhados nesta sessão do navegador (só a 1ª vez de cada um).
const _guiaTermosVistos = new Set();

// Texto do tutorial -> HTML seguro. `[[termo]]` vira botão sublinhado na 1ª vez e texto
// simples nas seguintes; o nome e a definição vêm de ui.tutorial.glossario.<termo>.
function _tutHTML(s){
  const bruto = _tutTexto(s);
  return GuiaTutorial.segmentos(bruto, _guiaTermosVistos).map(seg => {
    if(!seg.termo) return _esc(seg.texto);
    const nome = t('ui.tutorial.glossario.' + seg.termo + '.nome');
    return seg.primeira
      ? `<button type="button" class="guia-termo" data-termo="${_esc(seg.termo)}">${_esc(nome)}</button>`
      : _esc(nome);
  }).join('');
}

function _guiaBalao(botao){
  let b = document.getElementById('guia-balao');
  if(!b){ b = document.createElement('div'); b.id = 'guia-balao'; document.body.appendChild(b); }
  const termo = botao.dataset.termo;
  b.innerHTML = `<b>${_esc(t('ui.tutorial.glossario.' + termo + '.nome'))}</b><br>` +
                _esc(t('ui.tutorial.glossario.' + termo + '.texto'));
  const r = botao.getBoundingClientRect();
  b.style.left = Math.max(8, Math.min(r.left, window.innerWidth - 268)) + 'px';
  b.style.top = Math.max(8, r.top - b.offsetHeight - 8) + 'px';
  b.classList.add('open');
  clearTimeout(_guiaBalao._t);
  _guiaBalao._t = setTimeout(() => b.classList.remove('open'), 7000);
}
document.addEventListener('click', ev => {
  const b = ev.target.closest && ev.target.closest('.guia-termo');
  if(b) { _guiaBalao(b); return; }
  document.getElementById('guia-balao')?.classList.remove('open');
});
```

Em `_mostrarJanelaLicao`, troque o texto e o porquê para usar `_tutHTML` (a lição sem `guia` explícito continua em texto puro escapado):

```javascript
  const textoHtml = explicito ? _tutHTML(passo.texto) : _esc(msg.texto || '');
```

(remova a linha `const texto = …`), e no template: `` `<div class="licao-texto">${textoHtml}</div>` `` ; o `porque` vira `` `<div class="licao-porque">${_tutHTML(passo.porque)}</div>` `` (sem `_esc` em volta, `_tutHTML` já escapa). A dica (`_guiaAtualizarDica`) usa `host.innerHTML = txt ? \`${_esc(t('ui.tutorial.dica'))}: ${_tutHTML(txt)}\` : ''`.

Atenção: o regex do teste espera `class="licao-texto">${_tutHTML(`; escreva o template com `_tutHTML(` diretamente se preferir (`<div class="licao-texto">${_tutHTML(passo.texto)}</div>` quando `explicito`, e mantenha o ramo sem guia explícito com `_esc`). Uma forma que passa o teste e preserva os dois ramos:

```javascript
    `<div class="licao-texto">${explicito ? _tutHTML(passo.texto) : _esc(msg.texto || '')}</div>` + porque +
```

- [ ] **Step 4: CSS em `game.css`**

```css
.guia-termo{background:none;border:0;padding:0;margin:0;font:inherit;color:inherit;cursor:help;
  border-bottom:1px dotted var(--gold,#d9b45a)}
#guia-balao{position:fixed;z-index:10050;max-width:260px;padding:8px 10px;border-radius:8px;
  background:#1c1a26;border:1px solid var(--gold,#d9b45a);color:#eee;font-size:12.5px;line-height:1.35;
  box-shadow:0 4px 16px rgba(0,0,0,.5);display:none}
#guia-balao.open{display:block}
```

- [ ] **Step 5: Rodar e ver passar**

Run: `node --check game.js && node tools/test_guia_tutorial_cliente.js`
Expected: sem erro de sintaxe; `0 falha(s)`.

- [ ] **Step 6: Commit**

```bash
git add game.js game.css tools/test_guia_tutorial_cliente.js
git commit -m "feat(tutorial): termos do glossário sublinhados com balão na janela da lição" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Dados do conteúdo e teste de regras

**Files:**
- Create: `tools/tutorial_guia_comum.py`
- Test: `tools/test_tutorial_conteudo.py`

Formato de dados: cada passo é `dict(id, texto=(pt, en), porque=(pt, en)|None, ui=str|None, dica=[(pt, en),...], conclui=dict|None)`. O gerador converte em chaves `ui.tutorial.guia.<lição>.<id>.<campo>`.

- [ ] **Step 1: Escrever o teste que falha**

Crie `tools/test_tutorial_conteudo.py`:

```python
"""Conteúdo do guia da trilha comum: regras de redação, paridade pt/en e validação."""
import json, re, sys, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "tools"))

import tutorial_guia_comum as C

IDS_ESPERADOS = ["fala_0", "fala_1", "fala_2", "fala_3", "fala_4", "fala_18", "fala_19",
                 "fala_29", "fala_30", "fala_31", "fala_32", "fala_33", "fala_36", "fala_37", "fala_38"]
UI_OK = re.compile(r"^(?:(?:botao|bolsa|monstro):[a-z0-9_]+|(?:casa|porta):\[\d+,\d+\])$")
TERMO = re.compile(r"\[\[([a-z0-9_]+)\]\]")


def textos(passo):
    yield passo["texto"]
    if passo.get("porque"): yield passo["porque"]
    yield from passo.get("dica", [])


class ConteudoTests(unittest.TestCase):
    def test_cobre_as_quinze_licoes(self):
        self.assertEqual(sorted(C.GUIA), sorted(IDS_ESPERADOS))

    def test_regras_de_redacao(self):
        for lid, passos in C.GUIA.items():
            self.assertTrue(1 <= len(passos) <= 3, lid)
            for i, p in enumerate(passos):
                pt, en = p["texto"]
                limpo = TERMO.sub("x", pt)
                self.assertLessEqual(len(limpo.split()), 15, f"{lid}/{p['id']}: >15 palavras")
                self.assertTrue(pt.strip() and en.strip(), f"{lid}/{p['id']}")
                if p.get("ui"):
                    self.assertRegex(p["ui"], UI_OK, f"{lid}/{p['id']}")
                if i == len(passos) - 1:
                    self.assertFalse(p.get("conclui"), f"{lid}: último passo não conclui")
                self.assertLessEqual(len(p.get("dica", [])), 2, lid)

    def test_conclui_com_nunca_depende_de_evento_anterior(self):
        # evento que o jogador pode ter feito antes da lição travaria o passo
        for lid, passos in C.GUIA.items():
            for p in passos:
                c = p.get("conclui")
                if c: self.assertNotIn(c["tipo"], ("pegar_item", "equipar", "usar_item"), f"{lid}/{p['id']}")

    def test_termos_existem_no_glossario(self):
        for lid, passos in C.GUIA.items():
            for p in passos:
                for par in textos(p):
                    for lang in par:
                        for termo in TERMO.findall(lang):
                            self.assertIn(termo, C.GLOSSARIO, f"{lid}/{p['id']}: [[{termo}]]")

    def test_termos_iguais_em_pt_e_en(self):
        for lid, passos in C.GUIA.items():
            for p in passos:
                for pt, en in textos(p):
                    self.assertEqual(TERMO.findall(pt), TERMO.findall(en), f"{lid}/{p['id']}")

    def test_glossario_completo(self):
        self.assertEqual(sorted(C.GLOSSARIO),
                         sorted(["turno", "movimento", "acao_livre", "acao_bonus", "ca", "fome_sede", "resistencia"]))
        for k, v in C.GLOSSARIO.items():
            for campo in ("nome", "texto"):
                self.assertTrue(v[campo][0].strip() and v[campo][1].strip(), f"{k}.{campo}")

    def test_ui_bate_com_a_tarefa_da_licao(self):
        d = json.loads((RAIZ / "dungeons/campo_de_treinamento.json").read_text(encoding="utf-8"))
        falas = {f["id"]: f for f in d["falas"]}
        for lid, passos in C.GUIA.items():
            tar = falas[lid]["tarefa"]
            for p in passos:
                ui = p.get("ui") or ""
                if ui.startswith("casa:") or ui.startswith("porta:"):
                    self.assertEqual(ui.split(":", 1)[1], json.dumps(tar.get("alvo")).replace(" ", ""), lid)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_tutorial_conteudo.py`
Expected: `ModuleNotFoundError: No module named 'tutorial_guia_comum'`.

- [ ] **Step 3: Criar os dados**

Crie `tools/tutorial_guia_comum.py` com este conteúdo completo:

```python
"""Conteúdo do guia da trilha comum do Campo de Treinamento (pt + en).

Cada texto é uma tupla (pt, en). `[[termo]]` chama o glossário.
`conclui` só em passos que NÃO são o último (ver regras no plano da fatia 3).
"""

GLOSSARIO = {
    "turno": {"nome": ("turno", "turn"),
              "texto": ("Sua vez de agir. Quando você passa a vez, os outros agem e depois o turno volta.",
                        "Your time to act. When you pass, the others act and then the turn comes back.")},
    "movimento": {"nome": ("movimento", "movement"),
                  "texto": ("Quantas casas você anda por turno. Acabou, só o próximo turno devolve.",
                            "How many squares you walk per turn. When it runs out, only the next turn restores it.")},
    "acao_livre": {"nome": ("ação livre", "free action"),
                   "texto": ("Algo que não gasta nada do turno, como equipar uma arma.",
                             "Something that costs nothing from your turn, like equipping a weapon.")},
    "acao_bonus": {"nome": ("ação bônus", "bonus action"),
                   "texto": ("Uma ação extra e curta por turno. Não gasta a ação principal: dá para beber e ainda atacar.",
                             "A short extra action each turn. It does not use your main action: you can drink and still attack.")},
    "ca": {"nome": ("CA", "AC"),
           "texto": ("Classe de Armadura: quanto o alvo é difícil de acertar. Seu ataque precisa igualar ou passar.",
                     "Armor Class: how hard the target is to hit. Your attack must match or beat it.")},
    "fome_sede": {"nome": ("fome e sede", "hunger and thirst"),
                  "texto": ("Barras que caem com o tempo e com habilidades. Vazias, trazem penalidades.",
                            "Bars that drop over time and with abilities. When empty, they bring penalties.")},
    "resistencia": {"nome": ("resistência", "resistance"),
                    "texto": ("A criatura sofre menos dano de certo tipo de golpe, como corte ou impacto.",
                              "The creature takes less damage from a type of hit, such as slashing or impact.")},
}


def P(id, texto, porque=None, ui=None, dica=(), conclui=None):
    return {"id": id, "texto": texto, "porque": porque, "ui": ui, "dica": list(dica), "conclui": conclui}


GUIA = {
    "fala_0": [
        P("ver", ("Veja seu [[movimento]]: são os passos que você tem neste [[turno]].",
                  "Check your [[movimento]]: the steps you have this [[turno]]."),
          porque=("Quando os passos acabam, só o próximo turno os devolve.",
                  "When the steps run out, only the next turn gives them back.")),
        P("andar", ("Clique na casa com o anel dourado para andar até lá.",
                    "Click the square with the golden ring to walk there."),
          ui="casa:[5,15]",
          dica=[("O anel dourado está no chão do tabuleiro, à sua frente.",
                 "The golden ring is on the board floor, ahead of you."),
                ("Clique uma vez; o herói anda sozinho até a casa.",
                 "Click once; the hero walks there by itself.")]),
    ],
    "fala_1": [
        P("pegar", ("Abra o baú e pegue uma arma; ela vai para a bolsa.",
                    "Open the chest and take a weapon; it goes to your bag."),
          porque=("Cada herói só usa certas armas; o baú tem uma para cada classe.",
                  "Each hero can only use certain weapons; the chest has one for every class."),
          dica=[("Ande até ficar ao lado do baú e clique nele.", "Walk next to the chest and click it."),
                ("Clique na arma para pegá-la.", "Click the weapon to take it.")]),
    ],
    "fala_2": [
        P("abrir", ("Abra a bolsa no botão da mochila.", "Open the bag with the backpack button."),
          ui="botao:inventario"),
        P("equipar", ("Clique na arma e equipe-a.", "Click the weapon and equip it."),
          porque=("Equipar é [[acao_livre]]: não gasta nada do seu [[turno]].",
                  "Equipping is a [[acao_livre]]: it costs nothing from your [[turno]]."),
          dica=[("A arma está na bolsa, entre os quadrados do inventário.",
                 "The weapon is in the bag, among the inventory squares.")]),
    ],
    "fala_3": [
        P("entender", ("Quando terminar o que quer fazer, você passa a vez.",
                       "When you finish what you want to do, you pass your turn."),
          porque=("No próximo [[turno]] seus passos e ações voltam.",
                  "On the next [[turno]] your steps and actions come back.")),
        P("encerrar", ("Clique em Encerrar Turno, no canto inferior direito.",
                       "Click End Turn, in the bottom-right corner."),
          ui="botao:encerrar_turno",
          dica=[("O botão verde grande fica embaixo, à direita.", "The big green button is bottom-right.")]),
    ],
    "fala_4": [
        P("porta", ("Atravesse a porta aberta ao fundo.", "Walk through the open door at the back."),
          porque=("Porta aberta deixa passar; em outras masmorras, abrir porta é gratuito.",
                  "An open door lets you through; in other dungeons, opening a door is free."),
          ui="porta:[13,15]",
          dica=[("Clique na casa da porta; o herói segue o caminho tracejado.",
                 "Click the door square; the hero follows the dotted path.")]),
    ],
    "fala_18": [
        P("pegar", ("O baú ao lado tem rações e água. Pegue uma ração.",
                    "The chest nearby has rations and water. Take a ration."),
          porque=("Comida e água mantêm [[fome_sede]] longe da zona de penalidade.",
                  "Food and water keep [[fome_sede]] out of the penalty zone.")),
        P("comer", ("Abra a bolsa e coma a ração de viagem.", "Open the bag and eat the travel ration."),
          porque=("Comer é [[acao_bonus]]: dá para comer e ainda lutar no mesmo turno.",
                  "Eating is a [[acao_bonus]]: you can eat and still fight in the same turn."),
          ui="bolsa:racao_viagem",
          dica=[("Se a bolsa está fechada, use o botão da mochila.", "If the bag is closed, use the backpack button.")]),
    ],
    "fala_19": [
        P("beber", ("Beba duas garrafas de água pela bolsa.", "Drink two bottles of water from the bag."),
          porque=("Água rende menos que comida. Habilidades cobram goles: curas, magias e canções.",
                  "Water restores less than food. Abilities cost sips: heals, spells and songs."),
          ui="bolsa:garrafa_agua",
          dica=[("Clique na garrafa na bolsa e use-a duas vezes.", "Click the bottle in the bag and use it twice.")]),
    ],
    "fala_29": [
        P("pegar", ("Pegue os três itens do baú: óleo, veneno e poção.",
                    "Take the chest's three items: oil, poison and potion."),
          porque=("São itens que se gastam, e você vai precisar deles na última sala.",
                  "These items get used up, and you will need them in the last room."),
          dica=[("Clique em cada item do baú até a lista esvaziar.", "Click each chest item until the list is empty.")]),
    ],
    "fala_30": [
        P("escolher", ("Escolha o Frasco de Óleo na bolsa.", "Pick the Oil Flask in the bag."),
          ui="bolsa:frasco_oleo"),
        P("arremessar", ("Clique num boneco para arremessar o óleo.", "Click a dummy to throw the oil."),
          porque=("Você rola destreza contra a [[ca]] do alvo; se acertar, ele pega fogo.",
                  "You roll dexterity against the target's [[ca]]; on a hit, it catches fire."),
          ui="monstro:boneco_treino",
          dica=[("O boneco de treino está na sala, parado.", "The training dummy is in the room, standing still.")]),
    ],
    "fala_31": [
        P("untar", ("Use o Fungo Acre na bolsa para untar a arma.", "Use the Acrid Fungus in the bag to coat your weapon."),
          porque=("Veneno não se bebe: unta-se na lâmina. Qualquer classe pode fazer isso.",
                  "Poison is not drunk: it is coated on the blade. Any class can do it."),
          ui="bolsa:veneno_fungo_acre",
          dica=[("Clique no frasco de veneno na bolsa.", "Click the poison flask in the bag.")]),
    ],
    "fala_32": [
        P("atacar", ("Ataque um boneco com a arma untada.", "Attack a dummy with the coated weapon."),
          porque=("O veneno só age se o golpe acertar; errar gasta o turno, não a dose.",
                  "Poison only works if the hit lands; a miss wastes the turn, not the dose."),
          ui="monstro:boneco_treino",
          dica=[("Ande até ficar ao lado do boneco e clique nele.", "Walk next to the dummy and click it.")]),
    ],
    "fala_33": [
        P("beber", ("Beba a poção de cura pela bolsa.", "Drink the healing potion from the bag."),
          porque=("Beber é [[acao_bonus]]: dá para se curar e atacar no mesmo turno.",
                  "Drinking is a [[acao_bonus]]: you can heal and attack in the same turn."),
          ui="bolsa:health_potion_small",
          dica=[("Memorize onde ela fica: na hora do aperto não haverá tempo.", "Remember where it is: in a pinch there is no time.")]),
    ],
    "fala_36": [
        P("atacar", ("Ataque o esqueleto com a arma que está na sua mão.", "Attack the skeleton with the weapon in your hand."),
          porque=("Corte entra a menos: o esqueleto tem [[resistencia]] a lâminas.",
                  "Slashing lands for less: the skeleton has [[resistencia]] to blades."),
          ui="monstro:esqueleto_humano",
          dica=[("Compare o número do dano com o de um golpe normal.", "Compare the damage number with a normal hit.")]),
    ],
    "fala_37": [
        P("pegar", ("Pegue a maça do baú desta sala.", "Take the mace from this room's chest."),
          porque=("Osso racha com impacto, e a maça causa impacto.",
                  "Bone cracks under impact, and the mace deals impact.")),
        P("equipar", ("Abra a bolsa e equipe a maça.", "Open the bag and equip the mace."),
          ui="bolsa:maca_treino",
          dica=[("Equipar é [[acao_livre]], não gasta o turno.", "Equipping is a [[acao_livre]], it does not use your turn.")]),
    ],
    "fala_38": [
        P("matar", ("Derrube o esqueleto com a maça.", "Take down the skeleton with the mace."),
          porque=("Compare com o golpe anterior: trocar de arma rende uns três pontos a mais por acerto.",
                  "Compare with the earlier hit: switching weapons adds about three points per hit."),
          ui="monstro:esqueleto_humano",
          dica=[("Escolher a arma certa vale mais que rolar bem o dado.", "Choosing the right weapon beats rolling well.")]),
    ],
}
```

Nota para quem implementa: `fala_2` passo "abrir" é informativo (sem `conclui`), por isso o jogador toca em "Entendi"; o mesmo vale para os passos "ver", "entender", "pegar" e "escolher".

- [ ] **Step 4: Rodar e ver passar**

Run: `python tools/test_tutorial_conteudo.py`
Expected: 7 testes `OK`. (`test_conclui_com_nunca_depende_de_evento_anterior` passa porque nenhum passo declara `conclui`; é uma trava para edições futuras.)

- [ ] **Step 5: Commit**

```bash
git add tools/tutorial_guia_comum.py tools/test_tutorial_conteudo.py
git commit -m "feat(tutorial): conteúdo em passos da trilha comum e regras de redação testadas" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Gerador (lang + JSON) e fiação

**Files:**
- Create: `tools/gerar_guia_comum.py`
- Modify: `tools/configurar_tutorial_salas.py` (antes da gravação final), `index.html:14`
- Generate: `src/lang/tutorial_guia.js`, `dungeons/campo_de_treinamento.json`
- Test: `tools/test_tutorial_conteudo.py` (novos testes)

- [ ] **Step 1: Escrever os testes que falham**

Acrescente em `tools/test_tutorial_conteudo.py`, antes do `if __name__`:

```python
import gerar_guia_comum as G


class GeradorTests(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((RAIZ / "dungeons/campo_de_treinamento.json").read_text(encoding="utf-8"))

    def test_aplicar_guia_injeta_so_chaves_e_valida(self):
        import server
        G.aplicar_guia(self.d)
        for f in self.d["falas"]:
            if f["id"] in C.GUIA:
                self.assertEqual(len(f["guia"]), len(C.GUIA[f["id"]]))
                for s in f["guia"]:
                    self.assertTrue(s["texto"].startswith("ui.tutorial.guia."), s)
        ok, msg = server.validar_dungeon(self.d)
        self.assertTrue(ok, msg)

    def test_aplicar_guia_e_idempotente(self):
        G.aplicar_guia(self.d); a = json.dumps(self.d, sort_keys=True)
        G.aplicar_guia(self.d); self.assertEqual(a, json.dumps(self.d, sort_keys=True))

    def test_lang_tem_pt_e_en_para_toda_chave_usada(self):
        lang = G.gerar_lang()
        G.aplicar_guia(self.d)
        usadas = set()
        for f in self.d["falas"]:
            for s in f.get("guia", []):
                for campo in ("texto", "porque"):
                    if s.get(campo): usadas.add(s[campo])
                usadas.update(s.get("dica", []))
        self.assertTrue(usadas)
        for k in usadas:
            self.assertIn(k, lang, k)
            self.assertTrue(lang[k]["pt"] and lang[k]["en"], k)
        for termo in C.GLOSSARIO:
            self.assertIn(f"ui.tutorial.glossario.{termo}.nome", lang)
            self.assertIn(f"ui.tutorial.glossario.{termo}.texto", lang)

    def test_arquivo_gerado_esta_em_dia(self):
        arq = (RAIZ / "src/lang/tutorial_guia.js").read_text(encoding="utf-8")
        self.assertEqual(arq, G.render_lang(), "rode: python tools/gerar_guia_comum.py")
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `python tools/test_tutorial_conteudo.py`
Expected: `ModuleNotFoundError: No module named 'gerar_guia_comum'`.

- [ ] **Step 3: Criar o gerador**

`tools/gerar_guia_comum.py`:

```python
"""Gera src/lang/tutorial_guia.js e injeta `guia` nas lições da trilha comum.

Uso (da raiz): python tools/gerar_guia_comum.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tutorial_guia_comum as C

JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"
LANG_JS = RAIZ / "src" / "lang" / "tutorial_guia.js"


def _chave(lic, passo_id, campo, n=None):
    base = f"ui.tutorial.guia.{lic}.{passo_id}.{campo}"
    return base if n is None else f"{base}.{n}"


def gerar_lang():
    """{chave: {pt, en}} de todo o guia e do glossário."""
    out = {}
    for lic, passos in C.GUIA.items():
        for p in passos:
            out[_chave(lic, p["id"], "texto")] = dict(zip(("pt", "en"), p["texto"]))
            if p.get("porque"):
                out[_chave(lic, p["id"], "porque")] = dict(zip(("pt", "en"), p["porque"]))
            for n, d in enumerate(p.get("dica", []), 1):
                out[_chave(lic, p["id"], "dica", n)] = dict(zip(("pt", "en"), d))
    for termo, v in C.GLOSSARIO.items():
        for campo in ("nome", "texto"):
            out[f"ui.tutorial.glossario.{termo}.{campo}"] = dict(zip(("pt", "en"), v[campo]))
    return out


def render_lang():
    corpo = json.dumps(gerar_lang(), ensure_ascii=False, indent=2, sort_keys=True)
    return ("// GERADO por tools/gerar_guia_comum.py a partir de tools/tutorial_guia_comum.py. Não edite à mão.\n"
            "window.LANG_TUTORIAL_GUIA = " + corpo + ";\n"
            "Object.assign(window.LANG_STRINGS, window.LANG_TUTORIAL_GUIA);\n")


def aplicar_guia(d):
    """Grava `guia` (só chaves de idioma) nas falas da trilha comum de `d` (dict da masmorra)."""
    for f in d["falas"]:
        passos = C.GUIA.get(f["id"])
        if not passos:
            continue
        guia = []
        for p in passos:
            s = {"id": p["id"], "texto": _chave(f["id"], p["id"], "texto")}
            if p.get("porque"):
                s["porque"] = _chave(f["id"], p["id"], "porque")
            if p.get("ui"):
                s["ui"] = p["ui"]
            if p.get("dica"):
                s["dica"] = [_chave(f["id"], p["id"], "dica", n) for n in range(1, len(p["dica"]) + 1)]
            if p.get("conclui"):
                s["conclui_com"] = p["conclui"]
            guia.append(s)
        f["guia"] = guia
    return d


def main():
    LANG_JS.write_text(render_lang(), encoding="utf-8", newline="\n")
    d = json.loads(JSON_CAMPO.read_text(encoding="utf-8"))
    aplicar_guia(d)
    JSON_CAMPO.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ok: {len(gerar_lang())} chaves; {len(C.GUIA)} lições com guia")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Ligar ao `configurar_tutorial_salas.py`**

Antes da linha final `path.write_text(json.dumps(d,…))`, acrescente:

```python
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from gerar_guia_comum import aplicar_guia
aplicar_guia(d)
```

Em `index.html` linha 14, logo depois de `tutorial.js`: `document.write('<script src="src/lang/tutorial_guia.js?v='+v+'"><\/script>');`

- [ ] **Step 5: Gerar e rodar**

Run: `python tools/gerar_guia_comum.py && python tools/test_tutorial_conteudo.py`
Expected: `ok: <N> chaves; 15 lições com guia` e todos os testes `OK`.

Confira o diff do JSON: `git diff --stat dungeons/campo_de_treinamento.json` deve tocar **apenas** as 15 falas (nenhuma geometria). Se o diff trouxer outras mudanças (por diferença de formatação), pare e compare com `git diff -w` antes de seguir.

- [ ] **Step 6: Suítes que dependem do JSON e do idioma**

Run:
```bash
python tools/test_tutorial_guia.py && python tools/test_tutorial_salas.py && python tools/test_idioma.py && python tools/test_interface.py && python tools/dividas.py && node tools/test_idioma_cliente.js && node tools/test_guia_tutorial_cliente.js
```
Expected: todas passam; `dividas.py` imprime "nada pendente". Se `test_idioma_cliente.js` acusar `tutorial_guia.js` fora da lista de arquivos carregados, acrescente o arquivo à lista que ele lê (o teste cita "os seis arquivos de src/lang/", como o `index.html`).

- [ ] **Step 7: Commit**

```bash
git add tools/gerar_guia_comum.py tools/configurar_tutorial_salas.py tools/test_tutorial_conteudo.py index.html src/lang/tutorial_guia.js dungeons/campo_de_treinamento.json
git commit -m "feat(tutorial): guia em passos nas 15 lições da trilha comum" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Prova no navegador, documentação e fechamento

**Files:**
- Modify: `CLAUDE.md` (CRLF — usar Edit)

- [ ] **Step 1: Servidor isolado**

Copie o projeto/dados para `%TEMP%\lfh_guia3` (nunca use `savegames/`, `accounts/`, `groups/` reais), suba com `LFH_PORT=8791` e abra `http://[::1]:8791/index.html?v=guia3`. Crie uma conta de teste só em localhost e entre no Campo de Treinamento com o guerreiro.

- [ ] **Step 2: Conferir em jogo**

1. `fala_0`: a janela mostra "Passo 1 de 2", **movimento** e **turno** sublinhados; tocar em "movimento" abre o balão com a definição; "Entendi" leva ao passo 2 com o halo na casa.
2. Em `fala_2`, "ação livre" aparece sublinhada **só uma vez** na sessão; na segunda lição que a cita sai texto simples.
3. Troque o idioma para English no painel ⚙️: janela, balão e dicas saem em inglês.
4. Complete `fala_0` a `fala_4` e confira que cada passo avança e a lição fecha pela tarefa.
5. `read_console_messages` com `onlyErrors`: nenhum erro.

- [ ] **Step 3: Documentar em `CLAUDE.md`**

Depois do parágrafo "Tutorial guiado — fatia 1", acrescente (com Edit, mantendo CRLF) um parágrafo curto: a fatia 3 entregou o glossário (`GuiaTutorial.segmentos`, `_tutHTML`, balão `#guia-balao`, termos `[[termo]]`, 1ª ocorrência por sessão) e o guia em passos das 15 lições da trilha comum, com conteúdo em `tools/tutorial_guia_comum.py`, gerado por `tools/gerar_guia_comum.py` para `src/lang/tutorial_guia.js` e para o JSON; regra de ouro: `conclui_com` nunca para evento que pode acontecer antes da lição (usar passo informativo); testes `tools/test_tutorial_conteudo.py`. Plano: `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia3-trilha-comum.md`. Pendente: fatia 4 (seis salas e lições geradas).

- [ ] **Step 4: Suítes finais e limpeza**

Run as suítes do Task 4 Step 6 mais `python tools/test_salvar_masmorra.py`. Pare o servidor da 8791 e apague `%TEMP%\lfh_guia3`.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia3-trilha-comum.md
git commit -m "docs: guia do tutorial (fatia 3) no CLAUDE.md" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

Não fazer push sem o usuário pedir.

---

## Auto-revisão

- **Cobertura do spec (4.4 e 5):** glossário com primeira ocorrência e balão → Tasks 1–2; reescrita da trilha comum com passos curtos, imperativo ≤15 palavras, porquê depois da ação, termo marcado → Tasks 3–4; pt + en e `dividas.py` → Task 4 Step 6; gravação por `configurar_tutorial_salas.py` → Task 4 Step 4. Fora desta fatia, de propósito: seis salas por herói e lições geradas (`treino_guild_*`, `treino_magia_*`) = fatia 4; editor de passos = fatia 5.
- **Lacuna conhecida:** `fala_5` a `fala_17` e outras falas **sem tarefa** (apresentações) não entram; só as 15 com tarefa da trilha comum. O teste `test_cobre_as_quinze_licoes` trava o conjunto.
- **Consistência de nomes:** `segmentos`, `_tutHTML`, `_guiaTermosVistos`, `_guiaBalao`, `aplicar_guia`, `gerar_lang`, `render_lang`, `C.GUIA`, `C.GLOSSARIO` aparecem com a mesma grafia em todas as tasks.
- **Risco:** o teste `test_ui_bate_com_a_tarefa_da_licao` compara `casa`/`porta` com o `alvo` da tarefa; se o autor mover a porta no editor, o teste acusa e o dado precisa ser atualizado.
