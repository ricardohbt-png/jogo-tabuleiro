# Etapa 5.0 do idioma — Fundação da interface — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-14-idioma-etapa5-interface-design.md`

**Objetivo:** Deixar a base pronta para traduzir as 7 telas — tradução ao vivo sem depender de disciplina, o `ABILITY_NAME_TO_ID` desacoplado do português, e o teste-placar que vai acompanhar as sub-etapas.

**Arquitetura:** Um `MutationObserver` aplica `_i18nApply` em qualquer nó inserido que traga `[data-i18n]`, o que elimina a classe de bug "traduzi mas não aparece". O ícone de habilidade passa a ser achado por `data-ability-id` emitido no render, com o scan por texto em português mantido só como retaguarda. **Nenhuma string é traduzida nesta etapa** — ela só prepara o terreno.

**Stack:** JavaScript vanilla (`game.js`, `src/i18n.js`), testes `node` e `python`.

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** — regras obrigatórias do projeto.
- **O usuário edita `game.js` e `server.py` em paralelo.** Antes de cada commit rode `git status` e use só os caminhos do passo — **nunca** `git add -A`. Não mate processo nenhum. Hoje há WIP de monstros e GLB na árvore.
- **O motor de idioma já existe e funciona** (etapas 1–4c). No cliente: `I18N.t/setLang/on/tem/traduzirNomes/aplicarCatalogo` em `src/i18n.js`; o atalho `t()` e o `_i18nApply(root)` em `game.js`.
- **`_i18nApply(root)`** preenche `[data-i18n]` (textContent), `[data-i18n-ph]` (placeholder) e `[data-i18n-title]` (title). O `_setLang` chama `_i18nApply(document.body)` na troca de idioma.
- **O dicionário é JSON estrito** dentro do objeto: `src/lang/strings.js` não aceita comentário DENTRO das chaves. Está documentado no cabeçalho dele e quebra alto se violado.
- Suítes verdes hoje: `test_idioma` (36), `test_vocabulario` (38), `test_erros` (9), `test_narracao` (67), `test_idioma_cliente` (16), `test_vocabulario_cliente` (45).

### Fatos medidos (não precisa re-verificar)

| fato | valor |
|---|---|
| literais em português no `game.js` | 636 |
| atribuições a `innerHTML` | 163 |
| chamadas de `_i18nApply` | 4 |
| chamadas `_refreshX()` (o sintoma da dívida) | 9 |
| sites que geram `.skill-name` / `.cs-skill-icon` / `.gi-icon` | 17 / 3 / 3 |

**Os dois usos de `ABILITY_NAME_TO_ID` são muito diferentes:**

```js
// game.js:126 — JÁ prefere o id. Só cai no nome quando não há id.
const id = typeof ability === 'string' ? ability
         : ability?.id || ABILITY_NAME_TO_ID[ability?.name || ability?.nome];

// game.js:140 — ESTE é o frágil: varre o TEXTO RENDERIZADO procurando o nome
// em português. Com o nome em inglês, não casa e o ícone some.
const match = Object.entries(ABILITY_NAME_TO_ID)
  .find(([name]) => element.textContent.includes(name));
```

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `game.js` | `MutationObserver`; `replaceAbilityEmoji` prefere `data-ability-id`; `abilityIconHtml` emite o atributo |
| `tools/test_interface.py` | **Criar.** Varredura-placar por área (relata, ainda não cobra) |
| `tools/test_idioma_cliente.js` | Testes do observador e do `data-ability-id` |

---

## Task 1: O teste-placar por área

**Arquivos:**
- Criar: `tools/test_interface.py`

Este teste é o instrumento das 7 sub-etapas: começa **relatando** quanto falta em cada
área e passa a **cobrar** cada uma conforme sua sub-etapa fecha. Vem antes de tudo para
o placar existir desde o primeiro commit.

- [ ] **Passo 1: Escrever o teste**

Criar `tools/test_interface.py`:

```python
"""Interface do cliente (etapa 5) — placar por área.
Roda da raiz: python tools/test_interface.py

Enquanto uma área não fecha, este teste RELATA quanto falta. Quando a sub-etapa
dela fecha, mova o nome para COBRADAS e ele passa a falhar se algo voltar. É o
mesmo padrão da seção [3] do test_narracao.py, que começou como relatório e virou
cobrança quando a 4b-ii terminou."""
import io, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

GAME = io.open(os.path.join(RAIZ, "game.js"), encoding="utf-8").read()
LINHAS = GAME.split("\n")
ACENTO = re.compile(r"[ãáàâçéêíóõôúÃÁÀÂÇÉÊÍÓÕÔÚ]")
# Caminho de arquivo e seletor CSS não são texto de interface.
IGNORAR = re.compile(r"\.(js|png|jpe?g|glb|css|html)|assets/|^#[\w-]+$")

# Início de cada área, pela definição das funções de render que a compõem.
MARCOS = [
    ("selecao_heroi",  r"function (renderClassSelect|_csApply|selectClass)"),
    ("hud_acoes",      r"function (renderMyPanel|renderPlayers|renderActions|_warriorSkill)"),
    ("ficha",          r"function (renderFicha|abrirFicha|renderConteudoAtributos)"),
    ("cidade",         r"function (openShop|_renderShop|openGuild|_renderGuild|_updateCity)"),
    ("modais",         r"function (openTargetModal|aplicarTooltip|_tooltip|abrirPainelLoot)"),
    ("mestre",         r"function (renderMasterHud|renderFichaMonstro|renderMinimapaCR)"),
    ("render3d",       r"function (init3D|build3DFig|startLoop3D|draw2D)"),
]
# Áreas cuja sub-etapa já fechou. Mova o nome para cá ao terminar cada uma.
COBRADAS = set()


def _areas():
    """{area: n_literais_em_portugues}, por intervalo de linhas."""
    inicio = {}
    for nome, pat in MARCOS:
        ms = [i for i, l in enumerate(LINHAS) if re.search(pat, l)]
        if ms: inicio[nome] = min(ms)
    ordem = sorted(inicio.items(), key=lambda kv: kv[1])
    cont = {nome: 0 for nome, _ in MARCOS}
    cont["topo"] = 0
    for i, l in enumerate(LINHAS):
        if not ACENTO.search(l): continue
        n = len([t for t in re.findall(r"""["'`]([^"'`\n]{4,140})["'`]""", l)
                 if ACENTO.search(t) and not IGNORAR.search(t)])
        if not n: continue
        reg = "topo"
        for nome, ini in ordem:
            if i >= ini: reg = nome
        cont[reg] += n
    return cont


def _rodar_verificacoes():
    print("\n[1] Placar por área")
    cont = _areas()
    total = sum(cont.values())
    for nome, n in sorted(cont.items(), key=lambda kv: -kv[1]):
        marca = "COBRADA" if nome in COBRADAS else "pendente"
        print(f"     {n:>4}  {nome:<16} ({marca})")
    print(f"     ----  total: {total}")
    check("placar emitido", True)

    print("\n[2] Áreas já fechadas continuam limpas")
    if not COBRADAS:
        check("nenhuma área cobrada ainda (fundação)", True)
    for nome in sorted(COBRADAS):
        check(f"{nome} sem literal em português ({cont.get(nome, 0)})",
              cont.get(nome, 0) == 0)

    print("\n[3] A fiação da fundação existe")
    check("MutationObserver de i18n instalado",
          "MutationObserver" in GAME and "_i18nApply" in GAME)
    check("o ícone de habilidade é achado por data-ability-id",
          "data-ability-id" in GAME or "abilityId" in GAME)


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Interface do cliente (etapa 5)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
python tools/test_interface.py
```

Esperado: o placar sai com as 8 áreas somando **636**, e as duas checagens da seção
`[3]` falham (nem o observador nem o `data-ability-id` existem ainda). Algo como
`2 passaram, 2 falharam`.

Se o total divergir muito de 636, **pare e reporte** — os marcos de área podem ter saído
do lugar por edição do usuário, e o placar inteiro depende deles.

- [ ] **Passo 3: Commit**

```bash
git status --short
git add tools/test_interface.py
git commit -m "test(i18n): placar por area da interface do cliente"
```

---

## Task 2: O `MutationObserver`

**Arquivos:**
- Modificar: `game.js`, `tools/test_idioma_cliente.js`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `tools/test_idioma_cliente.js`, antes do bloco de resultado:

```js
console.log("\n[O] O observador traduz markup inserido depois");
// Checagem estática: o teste não carrega o game.js (ele monta o DOM inteiro no
// load), então verificamos a fiação no fonte — mesmo padrão da seção [8] do
// test_vocabulario_cliente.js.
const gamejsObs = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("existe um MutationObserver ligado ao i18n",
      /new MutationObserver\([\s\S]{0,400}?_i18nApply/.test(gamejsObs));
check("o observador escuta o body com subtree",
      /observe\(\s*document\.body\s*,\s*\{[^}]*subtree\s*:\s*true/.test(gamejsObs));
check("o observador só age quando o nó traz data-i18n",
      /data-i18n/.test(gamejsObs) && /querySelector\(\s*['"]\[data-i18n/.test(gamejsObs));
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
node tools/test_idioma_cliente.js
```

Esperado: `16 passaram, 3 falharam`.

- [ ] **Passo 3: Implementar o observador**

Em `game.js`, logo **depois** da função `_i18nApply` (procure por `function _i18nApply(root)`):

```js
// ── Tradução ao vivo do markup gerado ──────────────────────────────────────
// O cliente monta HTML por template string e o insere com innerHTML em 163
// lugares. Sem isto, cada um teria de lembrar de chamar _i18nApply — e a
// dívida já aparecia nos 9 _refreshX() manuais que o _setLang carregava.
//
// O observador só faz trabalho quando o nó inserido REALMENTE traz [data-i18n];
// no resto das inserções ele custa um matches/querySelector e sai.
function _i18nObservarInsercoes() {
  if (typeof MutationObserver === 'undefined' || !document.body) return null;
  const obs = new MutationObserver(muts => {
    for (const m of muts) {
      for (const no of m.addedNodes) {
        if (no.nodeType !== 1) continue;                    // só elementos
        if (no.matches?.('[data-i18n],[data-i18n-ph],[data-i18n-title]')
            || no.querySelector?.('[data-i18n],[data-i18n-ph],[data-i18n-title]')) {
          _i18nApply(no);
        }
      }
    }
  });
  obs.observe(document.body, { childList: true, subtree: true });
  return obs;
}
```

E chame-o no mesmo ponto do boot em que hoje se faz `_i18nApply(document.body)` —
procure a linha `_i18nApply(document.body);` que roda na inicialização (não a que está
dentro de `_setLang`) e acrescente logo abaixo:

```js
  _i18nObservarInsercoes();
```

- [ ] **Passo 4: Rodar os testes**

```bash
node --check game.js && node tools/test_idioma_cliente.js && python tools/test_interface.py
```

Esperado: `19 passaram, 0 falharam` no primeiro e, no `test_interface.py`, a checagem
"MutationObserver de i18n instalado" agora verde.

- [ ] **Passo 5: Medir o custo, com o teto do spec**

O spec fixa o teto em **1% do tempo de frame** (0,16 ms/frame a 60fps; ~300 ms em 30 s).
Suba o servidor e meça em combate:

```javascript
// No console do navegador, com uma partida em andamento:
(() => {
  let total = 0, chamadas = 0;
  const orig = window._i18nApply;
  window._i18nApply = function (root) {
    const t0 = performance.now();
    const r = orig.apply(this, arguments);
    total += performance.now() - t0; chamadas++;
    return r;
  };
  setTimeout(() => {
    console.log('30s:', chamadas, 'chamadas,', total.toFixed(1), 'ms total');
    window._i18nApply = orig;
  }, 30000);
})()
```

**Se passar de 300 ms**, não adote o observador: reverta a Task 2, use chamada manual de
`_i18nApply` nos pontos de inserção de cada sub-etapa, e **registre a medição e a decisão
no `CLAUDE.md`**. Se ficar abaixo, registre o número no corpo do commit — assim ninguém
re-discute isso na sub-etapa seguinte.

- [ ] **Passo 6: Commit**

```bash
git status --short
git add game.js tools/test_idioma_cliente.js
git commit -m "feat(i18n): observador traduz markup inserido depois"
```

---

## Task 3: O ícone de habilidade sem depender do português

**Arquivos:**
- Modificar: `game.js`, `tools/test_idioma_cliente.js`

O `replaceAbilityEmoji` varre o **texto renderizado** procurando o nome da habilidade em
português. Traduzir esse nome na sub-etapa 5b faria os ícones sumirem — em silêncio,
porque nenhum teste olha ícone.

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar em `tools/test_idioma_cliente.js`:

```js
console.log("\n[A] O ícone de habilidade não depende do nome em português");
const gamejsAb = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
check("abilityIconHtml emite o id no markup",
      /data-ability-id\s*=/.test(gamejsAb));
check("replaceAbilityEmoji prefere o data-ability-id ao texto",
      /dataset\.abilityId/.test(gamejsAb));
check("o scan por texto em português continua como retaguarda",
      /ABILITY_NAME_TO_ID/.test(gamejsAb));
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
node tools/test_idioma_cliente.js
```

Esperado: `19 passaram, 2 falharam` (a terceira já passa — o `ABILITY_NAME_TO_ID` existe).

- [ ] **Passo 3: `abilityIconHtml` passa a emitir o id**

Em `game.js`, a função (~linha 125) vira:

```js
function abilityIconHtml(ability, fallback = '') {
  const id = typeof ability === 'string' ? ability
           : ability?.id || ABILITY_NAME_TO_ID[ability?.name || ability?.nome];
  const src = ABILITY_ICON_ASSETS[id];
  // O id vai no markup para o replaceAbilityEmoji não precisar adivinhar pelo
  // TEXTO — que muda de idioma.
  return src ? `<img class="ability-icon" src="${src}" data-ability-id="${id}" alt="" aria-hidden="true">` : fallback;
}
```

- [ ] **Passo 4: `replaceAbilityEmoji` prefere o id**

No corpo do `for (const element of elements)` (~linha 140), **antes** da linha do
`Object.entries(...).find(...)`:

```js
    // 1º: o id, se o render o emitiu. É o caminho que sobrevive à tradução.
    const porId = element.dataset.abilityId
               || element.querySelector?.('[data-ability-id]')?.dataset.abilityId;
    // 2º: retaguarda pelo TEXTO em português, para os sites que ainda não
    // emitem o id. Some sozinha conforme as sub-etapas migram cada render.
    const match = porId && ABILITY_ICON_ASSETS[porId]
                ? [null, porId]
                : Object.entries(ABILITY_NAME_TO_ID)
                    .find(([name]) => element.textContent.includes(name));
```

O resto do corpo (que usa `match[1]`) continua igual.

- [ ] **Passo 5: Rodar**

```bash
node --check game.js && node tools/test_idioma_cliente.js && python tools/test_interface.py
```

Esperado: `21 passaram, 0 falharam` e o `test_interface.py` com a seção `[3]` inteira
verde.

- [ ] **Passo 6: Verificar no jogo — os ícones continuam lá**

Este é o passo que os testes não cobrem. Confirme com o usuário antes de subir servidor
(se a porta 8765 estiver ocupada, é dele). Com o jogo aberto e uma partida iniciada,
confira que os ícones das habilidades aparecem no painel do herói **como antes** — a
mudança é de mecanismo, o resultado visual tem de ser idêntico.

- [ ] **Passo 7: Commit**

```bash
git status --short
git add game.js tools/test_idioma_cliente.js
git commit -m "refactor(i18n): icone de habilidade achado por id, nao por texto"
```

---

## Task 4: Fechamento

**Arquivos:**
- Modificar: `CLAUDE.md`

- [ ] **Passo 1: Rodar tudo**

```bash
python tools/test_interface.py && python tools/test_idioma.py && python tools/test_vocabulario.py && python tools/test_erros.py && python tools/test_narracao.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: `test_interface` verde, `36`, `38`, `9`, `67`, `21` e `45`, zero falhando.

- [ ] **Passo 2: Regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_editor_itens.py && python tools/test_masmorra_sequenciada.py
```

Esperado: `336`, `54`, `462` e `118`, zero falhando.

- [ ] **Passo 3: Documentar no `CLAUDE.md`**

Acrescentar ao fim o bloco abaixo, **substituindo `<N>` e `<M>` pelos números que você
mediu** no Passo 5 da Task 2 (é a única lacuna deliberada deste plano: o número não
existe antes de a medição rodar):

```markdown
> **Idioma — fundação da interface (etapa 5.0 de 5):** prepara o terreno para traduzir as
> 7 telas do cliente; **nenhuma string é traduzida aqui**. Três peças:
>
> **`MutationObserver`** (`_i18nObservarInsercoes` em `game.js`): aplica `_i18nApply` em
> qualquer nó inserido que traga `[data-i18n]`. O cliente monta HTML por template string e
> o insere com `innerHTML` em **163 lugares** contra apenas 4 chamadas de `_i18nApply` —
> sem o observador, cada tela traduzida dependeria de alguém lembrar de aplicar, e a
> dívida já aparecia nos 9 `_refreshX()` que o `_setLang` carregava. O observador só faz
> trabalho quando o nó REALMENTE traz `data-i18n`. **Medido em combate:** `<N>` chamadas
> em 30 s, `<M>` ms no total — teto do spec era 300 ms (1% do tempo de frame).
>
> **O ícone de habilidade deixou de ser achado por TEXTO.** O `replaceAbilityEmoji`
> varria o texto renderizado procurando o nome em `ABILITY_NAME_TO_ID`, uma tabela
> chaveada em **português**: traduzir o nome faria os ícones sumirem, em silêncio, porque
> nenhum teste olha ícone. Agora o `abilityIconHtml` emite `data-ability-id` no markup e o
> scan o prefere; a busca por texto fica como retaguarda e some sozinha conforme cada
> render migra.
>
> **Convenção de chave da interface: `ui.<área>.<slug>`** (`ui.hud.encerrar_turno`),
> espelhando `narracao.<slug>` e `erro.<slug>`. As 38 chaves `ui.*` da etapa 1 já seguem.
>
> **`tools/test_interface.py` é o placar** das 7 sub-etapas: relata quantos literais em
> português restam por área e **cobra** as que já fecharam. Ao terminar uma sub-etapa,
> mova o nome da área para o conjunto `COBRADAS` no topo do arquivo — é isso que impede a
> área de regredir. Spec em
> `docs/superpowers/specs/2026-08-14-idioma-etapa5-interface-design.md`.
```

- [ ] **Passo 4: Commit final**

```bash
git add CLAUDE.md
git commit -m "docs(i18n): fundacao da interface do cliente"
```

---

## Fora deste plano (registrado, não esquecido)

- As **7 sub-etapas** (5a–5g), cada uma com plano próprio. Nenhuma string é traduzida
  aqui — esta etapa só prepara o terreno.
- **5b (HUD, 153) e 5f (mestre, 135)** mexem pesado no `game.js`. Combine a pausa do
  arquivo com o usuário antes de começar, como se fez com o `server.py` na 4b-ii.
- O **editor** (`tools/*.js`) fica fora da etapa 5 inteira.
