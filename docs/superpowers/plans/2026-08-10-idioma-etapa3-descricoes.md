# Etapa 3 do idioma — Alcance dos nomes + descrições — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-10-idioma-etapa3-descricoes-design.md`

**Objetivo:** Fazer os 53 nomes da etapa 2 que não chegavam à tela chegarem, e traduzir as 189 descrições de catálogo.

**Arquitetura:** O gerador passa a emitir também `cat.<família>.<id>.desc`. O filtro do cliente ganha três mudanças: resolve o prefixo uma vez e troca nome **e** descrição; aceita o id vindo da **chave do dicionário pai** (é assim que `lobby_state.classes` e `game_start.instrumentos_base` passam a ser alcançados); e expõe `aplicarCatalogo(obj, soNome)` sem a saída antecipada em português, para reescrever os catálogos **estáticos** do cliente a cada troca de idioma — inclusive na volta ao português, que é o que restaura o texto original.

**Stack:** Python 3 (gerador e servidor), JavaScript vanilla sem bundler (cliente), testes `tools/test_*.py` e `tools/test_*.js` (node).

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** — regras obrigatórias. `src/gameState.js` **nunca** referencia `document`, `canvas`, `THREE` ou `window`. `src/i18n.js` pode usar `window`, mas **não** `document`.
- **Nunca edite `game.js` por PowerShell/`sed`.** Use a ferramenta Edit. São ~25.900 linhas com todo o HTML do jogo numa template string.
- **O usuário edita `game.js`, `game.css` e `.glb` em paralelo, e sobe/derruba um servidor na porta 8765.** Antes de cada commit rode `git status` e use só os caminhos listados no passo — nunca `git add -A` nem `git add .`. Não mate processo nenhum.
- **Etapas 1 e 2 (prontas):** motor `src/i18n.js` (`window.I18N` com `t/tem/traduzirNomes/setLang/on/lang`); dicionário em `src/lang/strings.js` (à mão) + `src/lang/catalogo.js` (gerado, 397 chaves `.nome`); `gameState.js` com `setMessageFilter(fn)` aplicado no `ws.onmessage`; `game.js` registra `GS.setMessageFilter(I18N.traduzirNomes)`. Testes: `tools/test_idioma.py` (32), `tools/test_vocabulario.py` (36), `tools/test_idioma_cliente.js` (16), `tools/test_vocabulario_cliente.js` (16).

### Fatos já verificados (não precisa re-verificar)

- `lobby_state.classes` e `game_start.instrumentos_base` são dicionários chaveados pelo id, **sem campo `id` interno** — daí a extensão (b).
- `GRIMORIO_CLIENT` (`game.js:10487`), `ARMADILHAS_LUCCAS` (`game.js:9850`) e `CATALOGO_ITENS` (`src/gameState.js:519`) **têm `id` interno** em cada entrada, então o filtro atual já os alcança sem a extensão (b).
- Dos 72 itens de `CATALOGO_ITENS`, 28 ids coincidem com os do servidor, e **os 28 têm nome em português idêntico** nos dois lados. Por isso aplicar o filtro em português é inócuo para nomes.
- Descrições por família: guilda 127, magia 27, armadilha 13, instrumento 9, classe 6, item 7 = **189**. Com elas o `catalogo.js` vai de 397 para **586** chaves.

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `tools/gerar_vocabulario.py` | `chave()` ganha sufixo; `_entradas`/`coletar` parametrizados por tipo de texto; `achatar` emite `.nome` e `.desc`. |
| `src/lang/catalogo.js` | Regenerado com 586 chaves; a coluna `en` das 189 descrições é preenchida na Task 4. |
| `src/i18n.js` | `_chaveDeNome`→`_chaveBase`; troca descrição; id na chave do pai; `aplicarCatalogo(obj, soNome)` exportado. |
| `game.js` | Aplica `aplicarCatalogo` nos 3 catálogos estáticos (boot + troca de idioma); corrige a precedência em `_converterBagParaInventario`. |
| `tools/test_vocabulario.py` | +15 checagens (36 → 51). |
| `tools/test_vocabulario_cliente.js` | +13 checagens (16 → 29). |

---

## Task 1: Gerador emite as chaves de descrição

**Arquivos:**
- Modificar: `tools/gerar_vocabulario.py`
- Modificar: `tools/test_vocabulario.py`
- Regenerar: `src/lang/catalogo.js`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()` em `tools/test_vocabulario.py`:

```python
    print("\n[12] Descrições")
    desc = G.coletar("desc")
    esperado_desc = {"guilda": 127, "magia": 27, "armadilha": 13,
                     "instrumento": 9, "classe": 6, "item": 7}
    for fam, n in esperado_desc.items():
        check(f"{fam}: {n} descrições", len(desc.get(fam, {})) == n)
    check("total de 189 descrições", sum(len(d) for d in desc.values()) == 189)
    check("monstro e decor não têm descrição",
          not desc.get("monstro") and not desc.get("decor"))
    check("chave de descrição usa o sufixo .desc",
          G.chave("guilda", "brutalidade", "desc") == "cat.guilda.brutalidade.desc")
    check("chave de nome continua com .nome por padrão",
          G.chave("guilda", "brutalidade") == "cat.guilda.brutalidade.nome")

    plano = G.achatar(G.coletar(), G.coletar("desc"))
    check("achatar emite as 586 chaves", len(plano) == 586)
    check("item sem descrição não ganha chave .desc",
          "cat.monstro.goblin.desc" not in plano)
    check("o arquivo gerado tem 586 chaves",
          len(G.ler_existente(G.DESTINO)) == 586)
    # Idempotência com as DUAS famílias de chave: o que importa é que uma
    # descrição traduzida à mão sobreviva à próxima execução do gerador.
    novo, _ = G.mesclar({"cat.guilda.x.desc": {"pt": "Antigo", "en": "Old"}},
                        {"cat.guilda.x.desc": "Novo"})
    check("descrição traduzida à mão sobrevive", novo["cat.guilda.x.desc"]["en"] == "Old")
    check("o pt da descrição é atualizado do catálogo",
          novo["cat.guilda.x.desc"]["pt"] == "Novo")
```

- [ ] **Passo 2: Rodar o teste e confirmar que falha**

```bash
python tools/test_vocabulario.py
```

Esperado: falha na seção [12] com `TypeError: coletar() takes 0 positional arguments but 1 was given`.

- [ ] **Passo 3: Parametrizar o gerador por tipo de texto**

Em `tools/gerar_vocabulario.py`, substituir a função `chave`:

```python
def chave(familia, ident):
    return f"cat.{familia}.{ident}.nome"
```

por:

```python
def chave(familia, ident, sufixo="nome"):
    """Sufixo "nome" ou "desc". O padrão mantém as chamadas antigas válidas."""
    return f"cat.{familia}.{ident}.{sufixo}"
```

Substituir a função `_nome`:

```python
def _nome(entrada):
    return entrada.get("name") or entrada.get("nome")
```

por:

```python
def _texto(entrada, tipo):
    """O jogo escreve o mesmo campo de duas formas conforme o catálogo:
    name/nome e desc/descricao. Aceitamos as duas em cada tipo."""
    if tipo == "desc":
        return entrada.get("desc") or entrada.get("descricao")
    return entrada.get("name") or entrada.get("nome")
```

Substituir a função `_entradas` inteira por:

```python
def _entradas(catalogo, campo_id, tipo="nome"):
    """Devolve {id: texto} de um catálogo (lista ou dict). Quando o campo de id
    não existe na entrada, cai para a chave do dict — vários catálogos do jogo
    identificam o item pela chave, não por um campo. Entrada sem o texto pedido
    é omitida: é o que evita gerar chave .desc para quem não tem descrição."""
    itens = catalogo.items() if isinstance(catalogo, dict) else ((None, e) for e in catalogo)
    out = {}
    for chave_dict, entrada in itens:
        if not isinstance(entrada, dict):
            continue
        texto = _texto(entrada, tipo)
        ident = entrada.get(campo_id) or chave_dict
        if ident and texto:
            out[str(ident)] = texto
    return out
```

Substituir a função `coletar` inteira por:

```python
def coletar(tipo="nome"):
    """Devolve {familia: {id: texto_pt}} a partir dos catálogos do server.py.
    `tipo` é "nome" ou "desc" — a mesma varredura serve para os dois."""
    item = {}
    for nome_cat, campo in (("WEAPONS", "id"), ("SHOP_WEAPONS", "id"), ("SHOP_ARMORS", "id"),
                            ("SHOP_MERCHANT", "id"), ("SHOP_TEMPLE", "id"), ("SHOP_TAVERN", "id"),
                            ("ARREMESSAVEIS", "id"), ("VENENOS", "id")):
        fundir_item(item, _entradas(getattr(S, nome_cat), campo, tipo), nome_cat)
    return {
        "item":        item,
        "guilda":      _entradas(S.GUILD_CATALOG, "id", tipo),
        "monstro":     _entradas(S.MONSTER_DEFS, "type", tipo),
        "decor":       _entradas(S.DECOR_TYPES, "id", tipo),
        "magia":       _entradas(S.GRIMORIO, "id", tipo),
        "armadilha":   _entradas(S.ARMADILHAS, "id", tipo),
        "instrumento": _entradas(S.INSTRUMENTOS_BASE, "id", tipo),
        "classe":      _entradas(S.CLASSES, "id", tipo),
    }
```

Substituir a função `achatar` inteira por:

```python
def achatar(vocab, vocab_desc=None):
    """{familia: {id: texto}} → {chave: texto_pt}, juntando nomes e descrições."""
    out = {chave(fam, ident, "nome"): texto
           for fam, entradas in vocab.items()
           for ident, texto in entradas.items()}
    for fam, entradas in (vocab_desc or {}).items():
        for ident, texto in entradas.items():
            out[chave(fam, ident, "desc")] = texto
    return out
```

E em `main()`, substituir:

```python
    plano = achatar(coletar())
```

por:

```python
    plano = achatar(coletar(), coletar("desc"))
```

- [ ] **Passo 4: Regenerar o arquivo**

```bash
python tools/gerar_vocabulario.py
```

Esperado: `586 chaves no catálogo, 586 no arquivo.` e `189 sem tradução para o inglês.` (as 397 de nome já estão traduzidas), sem nenhuma órfã.

Se aparecer `ColisaoDeId`, **pare e reporte**: significa que dois catálogos dão descrições diferentes ao mesmo id de item, e a decisão de qual vale é do autor do jogo, não sua.

- [ ] **Passo 5: Rodar os testes**

```bash
python tools/test_vocabulario.py && python tools/test_idioma.py
```

Esperado: `51 passaram, 0 falharam` e `32 passaram, 0 falharam`.

- [ ] **Passo 6: Confirmar que as 397 traduções de nome sobreviveram**

```bash
python -c "import json,io; raw=io.open('src/lang/catalogo.js',encoding='utf-8').read(); d=json.loads(raw[raw.index('{'):raw.rindex('}')+1]); n=[k for k in d if k.endswith('.nome')]; print(len(n),'nomes,',sum(1 for k in n if d[k]['en']),'traduzidos')"
```

Esperado: `397 nomes, 397 traduzidos`.

- [ ] **Passo 7: Commit**

```bash
git add tools/gerar_vocabulario.py tools/test_vocabulario.py src/lang/catalogo.js
git commit -m "feat(i18n): gerador emite as chaves de descricao de catalogo"
```

---

## Task 2: Filtro do cliente — descrição, chave do pai e `aplicarCatalogo`

**Arquivos:**
- Modificar: `src/i18n.js`
- Modificar: `tools/test_vocabulario_cliente.js`

- [ ] **Passo 1: Escrever o teste que falha**

Em `tools/test_vocabulario_cliente.js`, inserir **antes** da seção `[8]` (a que faz as checagens estáticas de fiação):

```js
console.log("\n[9] Descrições");
DICT["cat.guilda.brutalidade.nome"] = { pt: "Brutalidade", en: "Brutality" };
DICT["cat.guilda.brutalidade.desc"] = { pt: "+2 de dano", en: "+2 damage" };
DICT["cat.classe.warrior.nome"]     = { pt: "Guerreiro", en: "Warrior" };
DICT["cat.classe.warrior.desc"]     = { pt: "Tanque", en: "Tank" };
I18N.setLang("en");
const comDesc = I18N.traduzirNomes({
  guild: [{ id: "brutalidade", nome: "Brutalidade", desc: "+2 de dano" }],
  outro: [{ id: "brutalidade", nome: "Brutalidade", descricao: "+2 de dano" }],
});
check("troca o campo desc", comDesc.guild[0].desc === "+2 damage");
check("troca o campo descricao", comDesc.outro[0].descricao === "+2 damage");
check("o nome continua sendo trocado", comDesc.guild[0].nome === "Brutality");
const semDesc = I18N.traduzirNomes({ a: [{ id: "dagger", name: "Adaga", desc: "texto autoral" }] });
check("sem chave .desc no dicionário, a descrição fica intacta",
      semDesc.a[0].desc === "texto autoral");

console.log("\n[10] Id na chave do dicionário pai");
const porChave = I18N.traduzirNomes({
  classes: { warrior: { name: "Guerreiro", desc: "Tanque", color: "#f00" } },
});
check("dicionário chaveado por id traduz o nome",
      porChave.classes.warrior.name === "Warrior");
check("dicionário chaveado por id traduz a descrição",
      porChave.classes.warrior.desc === "Tank");
check("campo que não é id não vira tradução por acidente",
      porChave.classes.warrior.color === "#f00");

console.log("\n[11] aplicarCatalogo — catálogos estáticos");
const estatico = { bola_fogo: { id: "bola_fogo", nome: "Bola de Fogo", descricao: "<b>HTML</b>" } };
DICT["cat.magia.bola_fogo.nome"] = { pt: "Bola de Fogo", en: "Fireball" };
DICT["cat.magia.bola_fogo.desc"] = { pt: "Frase curta", en: "Short line" };
I18N.aplicarCatalogo(estatico, true);
check("aplicarCatalogo(true) troca o nome", estatico.bola_fogo.nome === "Fireball");
check("aplicarCatalogo(true) NÃO toca na descrição do cliente",
      estatico.bola_fogo.descricao === "<b>HTML</b>");
// A volta ao português é o motivo de aplicarCatalogo não ter a saída antecipada.
I18N.setLang("pt");
I18N.aplicarCatalogo(estatico, true);
check("aplicar em português restaura o original", estatico.bola_fogo.nome === "Bola de Fogo");
I18N.setLang("en");
I18N.aplicarCatalogo(estatico, true);
check("aplicar de novo em inglês volta a traduzir", estatico.bola_fogo.nome === "Fireball");
```

- [ ] **Passo 2: Rodar o teste e confirmar que falha**

```bash
node tools/test_vocabulario_cliente.js
```

Esperado: falha na seção [9] — a descrição não é trocada — e depois `TypeError: I18N.aplicarCatalogo is not a function` na [11].

- [ ] **Passo 3: Implementar as três mudanças**

Em `src/i18n.js`, substituir o bloco que vai de `const CAMPOS_NOME = ['name', 'nome'];` até o fim da função `traduzirNomes` por:

```js
  const CAMPOS_NOME = ['name', 'nome'];
  const CAMPOS_DESC = ['desc', 'descricao'];
  // Usada quando o id vem da CHAVE do dicionário pai, caso em que não há campo
  // interno indicando de que família ele é.
  const TODAS_FAMILIAS = ['monstro', 'decor', 'item', 'guilda', 'magia',
                          'instrumento', 'armadilha', 'classe'];

  function tem(key) {
    return Object.prototype.hasOwnProperty.call(DICT, key);
  }

  // Primeiro prefixo cat.<família>.<id> que tenha nome OU descrição no
  // dicionário. Aceitar qualquer um dos dois importa: há entradas com descrição
  // traduzida e sem nome, e o contrário.
  function _tentaFamilias(familias, id) {
    for (const fam of familias) {
      const base = 'cat.' + fam + '.' + id;
      if (tem(base + '.nome') || tem(base + '.desc')) return base;
    }
    return null;
  }

  // `idPai` é a chave sob a qual este objeto estava no dicionário pai. Vários
  // payloads (lobby_state.classes, game_start.instrumentos_base) são dicionários
  // chaveados pelo id, com o valor sem nenhum campo de id dentro.
  function _chaveBase(o, idPai) {
    for (const campoId in FAMILIAS_POR_CAMPO) {
      const id = o[campoId];
      if (typeof id !== 'string' || !id) continue;
      const base = _tentaFamilias(FAMILIAS_POR_CAMPO[campoId], id);
      if (base) return base;
    }
    if (typeof idPai === 'string' && idPai) {
      const base = _tentaFamilias(TODAS_FAMILIAS, idPai);
      if (base) return base;
    }
    return null;
  }

  // Percorre a estrutura e troca nome (e descrição, se soNome for falso) pelo
  // idioma ATUAL. Muta o objeto de propósito. Objeto sem chave no dicionário
  // fica intacto — é assim que item e monstro criados no editor mantêm o nome
  // autoral. Sem saída antecipada em português: os catálogos estáticos do
  // cliente precisam ser reescritos na volta ao português para restaurar o
  // texto original. A troca é por id, nunca por texto, então reaplicar noutro
  // idioma sempre parte da chave e nunca do texto já trocado.
  function aplicarCatalogo(obj, soNome) {
    const vistos = new Set();
    (function anda(o, idPai) {
      if (!o || typeof o !== 'object' || vistos.has(o)) return;
      vistos.add(o);
      if (Array.isArray(o)) { for (const v of o) anda(v, null); return; }
      const base = _chaveBase(o, idPai);
      if (base) {
        if (tem(base + '.nome')) {
          for (const campo of CAMPOS_NOME) {
            if (typeof o[campo] === 'string') { o[campo] = t(base + '.nome'); break; }
          }
        }
        if (!soNome && tem(base + '.desc')) {
          for (const campo of CAMPOS_DESC) {
            if (typeof o[campo] === 'string') { o[campo] = t(base + '.desc'); break; }
          }
        }
      }
      for (const k in o) anda(o[k], k);
    })(obj, null);
    return obj;
  }

  // Caminho das mensagens: em português não há o que trocar, e sair aqui deixa
  // o custo em zero no idioma padrão.
  function traduzirNomes(msg) {
    if (lang === PADRAO) return msg;
    return aplicarCatalogo(msg, false);
  }
```

E no objeto exportado, acrescentar `aplicarCatalogo` junto de `traduzirNomes`:

```js
  window.I18N = {
    t: t,
    tem: tem,
    traduzirNomes: traduzirNomes,
    aplicarCatalogo: aplicarCatalogo,
    setLang: setLang,
    on: function (fn) { if (typeof fn === 'function') ouvintes.push(fn); },
    get lang() { return lang; },
    SUPORTADOS: SUPORTADOS,
    PADRAO: PADRAO,
  };
```

- [ ] **Passo 4: Rodar os testes**

```bash
node tools/test_vocabulario_cliente.js && node tools/test_idioma_cliente.js
```

Esperado: `27 passaram, 0 falharam` e `16 passaram, 0 falharam`.

- [ ] **Passo 5: Commit**

```bash
git add src/i18n.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): filtro troca descricao, aceita id na chave do pai e expoe aplicarCatalogo"
```

---

## Task 3: Catálogos estáticos e precedência do inventário

**Arquivos:**
- Modificar: `game.js`
- Modificar: `tools/test_vocabulario_cliente.js`

> **Lembrete:** edite `game.js` **apenas** com a ferramenta Edit, e confira `git status` antes do commit — o usuário tem trabalho não commitado nesse arquivo.

- [ ] **Passo 1: Escrever o teste que falha**

Em `tools/test_vocabulario_cliente.js`, acrescentar à seção `[8]` (as checagens estáticas), logo depois da última checagem que já existe lá:

```js
check("game.js aplica o catálogo nos 3 estáticos",
      /aplicarCatalogo\(\s*GRIMORIO_CLIENT/.test(gamejs)
      && /aplicarCatalogo\(\s*ARMADILHAS_LUCCAS/.test(gamejs)
      && /aplicarCatalogo\(\s*GS\.CATALOGO_ITENS/.test(gamejs));
check("a conversão do inventário prefere o nome do servidor",
      /\{\s*\.\.\.cat,\s*nome:\s*it\.name\s*\|\|\s*cat\.nome\s*\}/.test(gamejs));
```

- [ ] **Passo 2: Rodar o teste e confirmar que falha**

```bash
node tools/test_vocabulario_cliente.js
```

Esperado: as duas checagens novas da seção [8] falham.

- [ ] **Passo 3: Aplicar o catálogo nos estáticos**

Em `game.js`, logo **depois** da linha `GS.setMessageFilter(I18N.traduzirNomes);` (e do comentário que a acompanha), inserir:

```js
// Três catálogos vivem dentro do cliente e não vêm de payload nenhum, então o
// filtro de mensagens não os alcança: o painel de magias lê GRIMORIO_CLIENT, o
// de armadilhas lê ARMADILHAS_LUCCAS, e a loja/tooltip leem CATALOGO_ITENS.
// São reescritos aqui, no boot e a cada troca de idioma.
//
// SÓ O NOME (segundo argumento true): a descrição que esses catálogos guardam é
// conteúdo próprio do cliente, já divergente do servidor — a das magias é um
// card HTML com alcance e efeito por rodada, contra uma frase curta no servidor.
// Trocá-la pela tradução da frase do servidor apagaria informação.
function _aplicarCatalogosEstaticos(){
  if (typeof GRIMORIO_CLIENT   !== 'undefined') I18N.aplicarCatalogo(GRIMORIO_CLIENT, true);
  if (typeof ARMADILHAS_LUCCAS !== 'undefined') I18N.aplicarCatalogo(ARMADILHAS_LUCCAS, true);
  if (GS.CATALOGO_ITENS)                        I18N.aplicarCatalogo(GS.CATALOGO_ITENS, true);
}
// Ouvinte SEPARADO do que avisa o servidor: manter aquele intacto preserva a
// checagem de fiação da etapa 2, que casa com a forma exata daquela linha.
I18N.on(() => _aplicarCatalogosEstaticos());
```

- [ ] **Passo 4: Aplicar também no boot**

Em `game.js`, no IIFE `_audioInit`, trocar:

```js
(function _audioInit(){
  _langLoadPref();       // antes do painel: ele já nasce no idioma salvo
```

por:

```js
(function _audioInit(){
  _langLoadPref();       // antes do painel: ele já nasce no idioma salvo
  _aplicarCatalogosEstaticos();   // idioma salvo já vale para os catálogos do cliente
```

Isto é redundante quando `_langLoadPref` de fato troca o idioma (o ouvinte acima já dispara), mas cobre o caso em que o idioma salvo é o padrão e nenhum evento acontece. É idempotente e barato.

- [ ] **Passo 5: Corrigir a precedência do inventário**

Em `game.js`, em `_converterBagParaInventario`, trocar:

```js
    inv[i] = cat ? { ...cat }
                 : { id: it.id, nome: it.name || it.id, tipo: it.tipo || it.type || 'item', ...it };
```

por:

```js
    // O dado do servidor é a autoridade sobre o NOME (mesma regra que
    // normalizarItemTooltip já usa). Sem isto, um id que exista também no
    // catálogo do cliente descartava o item do servidor inteiro e o nome
    // voltava ao português. Só o nome é sobreposto de propósito: `tipo`,
    // `preco` e os demais campos do catálogo do cliente seguem valendo.
    inv[i] = cat ? { ...cat, nome: it.name || cat.nome }
                 : { id: it.id, nome: it.name || it.id, tipo: it.tipo || it.type || 'item', ...it };
```

- [ ] **Passo 6: Rodar os testes e checar a sintaxe**

```bash
node tools/test_vocabulario_cliente.js && node tools/test_idioma_cliente.js && node --check game.js
```

Esperado: `29 passaram, 0 falharam`, `16 passaram, 0 falharam`, e nenhuma saída do `--check`.

- [ ] **Passo 7: Commit**

```bash
git add game.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): traduz os catalogos estaticos do cliente e corrige a precedencia do inventario"
```

---

## Task 4: Traduzir as 189 descrições

**Arquivos:**
- Modificar: `src/lang/catalogo.js` (só a coluna `en` das chaves `.desc`)

São frases de regra, média de 69 caracteres. **Não toque no campo `pt` nem nas chaves `.nome`**, que já estão traduzidas.

**Duas exigências acima do normal.** *Precisão mecânica*: números, dados (`2d6`), durações e condições têm de sobreviver intactos — um "+2" que vira "+3" muda a regra que o jogador lê. *Consistência com os nomes*: uma descrição que cita "Canção Heroica" usa o mesmo "Heroic Song" que a chave `cat.guilda.*.nome` recebeu na etapa 2; consulte o próprio arquivo para conferir o termo já escolhido.

**Glossário de regra** (o da etapa 2 continua valendo):

| Português | Inglês |
|---|---|
| 🍖 fome / 💧 sede | hunger / thirst |
| recarga | cooldown |
| rodada / turno | round / turn |
| alcance / área | range / area |
| save, teste de resistência | saving throw |
| CD, dificuldade | DC |
| vantagem / desvantagem | advantage / disadvantage |
| Reflexos / Fortitude / Vontade | Reflex / Fortitude / Will |
| dano de fogo / gelo / ácido / sagrado | fire / cold / acid / holy damage |

- [ ] **Passo 1: Traduzir as 127 descrições da Guilda**

Aplicar por script, reusando o gerador para o formato sair idêntico:

```python
# scratchpad/traduzir_desc_guilda.py
import os, sys
RAIZ = r"C:\Users\RICARDO\Desktop\jogo tabuleiro"
sys.path.insert(0, os.path.join(RAIZ, "tools")); sys.path.insert(0, RAIZ)
import gerar_vocabulario as G

TRAD = {
    "cat.guilda.brutalidade.desc": "+2 weapon damage until end of turn.",
    # ... as 127
}

d = G.ler_existente(G.DESTINO)
faltando = [k for k in TRAD if k not in d]
assert not faltando, f"chaves inexistentes: {faltando}"
invasao = [k for k in TRAD if not (k.startswith("cat.guilda.") and k.endswith(".desc"))]
assert not invasao, f"fora do lote: {invasao}"
for k, en in TRAD.items():
    d[k]["en"] = en
G.escrever(G.DESTINO, d)
print("aplicadas:", len(TRAD))
```

Conferir:

```bash
python -c "import json,io; raw=io.open('src/lang/catalogo.js',encoding='utf-8').read(); d=json.loads(raw[raw.index('{'):raw.rindex('}')+1]); f=[k for k,v in d.items() if k.startswith('cat.guilda.') and k.endswith('.desc') and not v['en']]; print(len(f),'descricoes da guilda sem traducao')"
```

Esperado: `0 descricoes da guilda sem traducao`.

- [ ] **Passo 2: Commit**

```bash
git add src/lang/catalogo.js
git commit -m "feat(i18n): traduz as descricoes da Guilda"
```

- [ ] **Passo 3: Traduzir as 62 restantes**

As de `cat.magia.*` (27), `cat.armadilha.*` (13), `cat.instrumento.*` (9), `cat.classe.*` (6) e `cat.item.*` (7):

```python
# scratchpad/traduzir_desc_resto.py
import os, sys
RAIZ = r"C:\Users\RICARDO\Desktop\jogo tabuleiro"
sys.path.insert(0, os.path.join(RAIZ, "tools")); sys.path.insert(0, RAIZ)
import gerar_vocabulario as G

PREFIXOS = ("cat.magia.", "cat.armadilha.", "cat.instrumento.", "cat.classe.", "cat.item.")

TRAD = {
    "cat.classe.warrior.desc": "Melee tank. High HP and AC.",
    # ... as 62
}

d = G.ler_existente(G.DESTINO)
faltando = [k for k in TRAD if k not in d]
assert not faltando, f"chaves inexistentes: {faltando}"
invasao = [k for k in TRAD if not (k.startswith(PREFIXOS) and k.endswith(".desc"))]
assert not invasao, f"fora do lote: {invasao}"
for k, en in TRAD.items():
    d[k]["en"] = en
G.escrever(G.DESTINO, d)
print("aplicadas:", len(TRAD))
```

Conferir que o arquivo inteiro ficou traduzido:

```bash
python -c "import json,io; raw=io.open('src/lang/catalogo.js',encoding='utf-8').read(); d=json.loads(raw[raw.index('{'):raw.rindex('}')+1]); f=[k for k,v in d.items() if not v['en']]; print(len(f),'chaves sem traducao no arquivo inteiro'); print('\n'.join(f[:10]))"
```

Esperado: `0 chaves sem traducao no arquivo inteiro`.

- [ ] **Passo 4: Confirmar a idempotência com tudo traduzido**

```bash
python tools/gerar_vocabulario.py && git diff --stat src/lang/catalogo.js
```

Esperado: `586 chaves no catálogo, 586 no arquivo.`, `0 sem tradução para o inglês.`, nenhuma órfã e — depois do commit do passo 5 — **nenhuma diferença** no `git diff`.

- [ ] **Passo 5: Commit**

```bash
git add src/lang/catalogo.js
git commit -m "feat(i18n): traduz as descricoes de magia, armadilha, instrumento, classe e item"
```

---

## Task 5: Verificação final

**Arquivos:**
- Modificar: `CLAUDE.md`

- [ ] **Passo 1: Rodar as quatro suítes de idioma**

```bash
python tools/test_idioma.py && python tools/test_vocabulario.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: `32`, `51`, `16` e `29` passando, zero falhando.

- [ ] **Passo 2: Rodar as suítes de regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_cenas_conversa.py && python tools/test_masmorra_sequenciada.py
```

Esperado: `336`, `54`, `57` e `118`, zero falhando.

- [ ] **Passo 3: Provar o alcance com payload real**

O navegador embutido não consegue abrir WebSocket para o localhost, então a prova vem de puxar payloads reais do servidor e passar o filtro de verdade neles — foi assim que a etapa 2 foi verificada, e foi assim que as lacunas desta etapa apareceram.

Se a porta 8765 estiver livre, suba um servidor (`python server.py`); se estiver ocupada, ela é do usuário e serve igual. Então:

```python
# scratchpad/prova_etapa3.py — roda da raiz do projeto
import asyncio, json, subprocess, sys, websockets

async def capturar():
    msgs = []
    async with websockets.connect("ws://localhost:8765", open_timeout=8,
                                  max_size=34*1024*1024) as ws:
        async def ouvir(seg):
            fim = asyncio.get_event_loop().time() + seg
            while asyncio.get_event_loop().time() < fim:
                try:
                    msgs.append(json.loads(await asyncio.wait_for(
                        ws.recv(), timeout=max(.1, fim - asyncio.get_event_loop().time()))))
                except Exception:
                    break
        await ws.send(json.dumps({"type": "create_room", "name": "Prova"})); await ouvir(2)
        await ws.send(json.dumps({"type": "select_class", "class_id": "warrior"})); await ouvir(2)
        await ws.send(json.dumps({"type": "start_game"})); await ouvir(6)
    return msgs

msgs = asyncio.run(capturar())
alvo = {"lobby_state": None, "game_start": None, "city_state": None}
for m in msgs:
    if m.get("type") in alvo:
        alvo[m["type"]] = m
with open("scratchpad/payloads_etapa3.json", "w", encoding="utf-8") as f:
    json.dump(alvo, f, ensure_ascii=False)
print("capturados:", [k for k, v in alvo.items() if v])
```

Depois, o filtro real por node:

```js
// scratchpad/prova_etapa3.js — roda da raiz: node scratchpad/prova_etapa3.js
const fs = require("fs"), path = require("path");
global.window = {};
for (const f of ["src/lang/strings.js", "src/lang/catalogo.js", "src/i18n.js"])
  eval(fs.readFileSync(path.join(process.cwd(), f), "utf8"));
const I18N = global.window.I18N;
const p = JSON.parse(fs.readFileSync("scratchpad/payloads_etapa3.json", "utf8"));
I18N.setLang("en");
const lobby = I18N.traduzirNomes(p.lobby_state);
const gs    = p.game_start ? I18N.traduzirNomes(p.game_start) : null;
const city  = I18N.traduzirNomes(p.city_state);
console.log("classe warrior:", lobby.classes.warrior.name, "|", lobby.classes.warrior.desc);
if (gs && gs.instrumentos_base)
  console.log("instrumento harpa:", gs.instrumentos_base.harpa.nome, "|", gs.instrumentos_base.harpa.desc);
const g = (city.guild && city.guild.catalog) || {};
const k = Object.keys(g)[0];
console.log("guilda", k + ":", g[k].nome || g[k].name, "|", g[k].desc || g[k].descricao);
```

Esperado: as três linhas em **inglês** — é a prova de que as duas lacunas de alcance (chave do pai) fecharam e de que as descrições são trocadas.

- [ ] **Passo 4: Provar os catálogos estáticos**

```bash
node -e "
const fs=require('fs');
global.window={};
for (const f of ['src/lang/strings.js','src/lang/catalogo.js','src/i18n.js']) eval(fs.readFileSync(f,'utf8'));
const I18N=global.window.I18N;
const magias={bola_fogo:{id:'bola_fogo',nome:'Bola de Fogo',descricao:'<b>card HTML</b>'}};
I18N.setLang('en'); I18N.aplicarCatalogo(magias,true);
console.log('EN:', magias.bola_fogo.nome, '| descricao intacta:', magias.bola_fogo.descricao);
I18N.setLang('pt'); I18N.aplicarCatalogo(magias,true);
console.log('PT:', magias.bola_fogo.nome);
"
```

Esperado: `EN: Fireball | descricao intacta: <b>card HTML</b>` e `PT: Bola de Fogo` — o nome traduz e volta, e o HTML do cliente nunca é tocado.

- [ ] **Passo 5: Documentar no CLAUDE.md**

Em `CLAUDE.md`, acrescentar ao fim:

```markdown
> **Idioma — alcance e descrições (etapa 3 de 5):** fecha três lacunas de alcance da etapa
> 2 (53 nomes traduzidos que não chegavam à tela) e acrescenta as **189 descrições** de
> catálogo — `catalogo.js` vai a **586 chaves** (`cat.<família>.<id>.desc` ao lado de
> `.nome`; o gerador emite `.desc` só para quem tem descrição). **(1) Id na chave do pai:**
> `lobby_state.classes` e `game_start.instrumentos_base` são dicionários chaveados pelo id,
> com o valor sem campo `id` dentro; o filtro passa a tentar a chave do dicionário pai como
> id, além dos campos internos. **(2) Catálogos estáticos do cliente:** `GRIMORIO_CLIENT`
> (`game.js`), `ARMADILHAS_LUCCAS` (`game.js`) e `CATALOGO_ITENS` (`src/gameState.js`) não
> vêm de payload — são reescritos por `I18N.aplicarCatalogo(obj, true)` no boot e a cada
> troca de idioma, num ouvinte SEPARADO do que avisa o servidor (manter aquela linha intacta
> preserva a checagem de fiação da etapa 2). O `true` é **só o nome**: a descrição que esses
> catálogos guardam é conteúdo próprio já divergente do servidor — a das magias é um card
> HTML com alcance e efeito por rodada, contra uma frase curta no servidor —, e trocá-la
> apagaria informação; esse texto é da etapa 5. `aplicarCatalogo` **não tem** a saída
> antecipada em português que o `traduzirNomes` tem, porque a volta ao português é
> justamente o que restaura o texto original; a troca é sempre por id, nunca por texto, o
> que a torna idempotente. **(3) Precedência do inventário:** `_converterBagParaInventario`
> fazia `cat ? {...cat}` e descartava o item do servidor inteiro quando o id existia nos
> dois catálogos (28 casos), devolvendo o nome ao português; virou
> `{ ...cat, nome: it.name || cat.nome }` — só o nome é sobreposto, os demais campos do
> catálogo do cliente seguem valendo. **Fora de escopo:** os 44 itens que só existem em
> `CATALOGO_ITENS`, o `resumo`/`descricao` HTML das magias e o `desc` próprio das armadilhas
> no cliente — todos etapa 5. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-10-idioma-etapa3-descricoes*`. Testes:
> `tools/test_vocabulario.py` (51) e `tools/test_vocabulario_cliente.js` (29).
```

- [ ] **Passo 6: Commit final**

```bash
git add CLAUDE.md
git commit -m "docs(i18n): documenta o alcance e as descricoes da etapa 3"
```
