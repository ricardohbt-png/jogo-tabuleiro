# Etapa 2 do idioma — Vocabulário (nomes de catálogo) — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`) para acompanhamento.

**Spec:** `docs/superpowers/specs/2026-08-10-idioma-etapa2-vocabulario-design.md`

**Objetivo:** Traduzir para inglês os **397 nomes** de catálogo do jogo (itens, monstros, técnicas da Guilda, magias, decorações, armadilhas, instrumentos e classes), sem tocar nos 405 pontos do cliente que leem `.name`.

**Arquitetura:** As chaves (`cat.<família>.<id>.nome`) são **geradas** dos catálogos do `server.py` para `src/lang/catalogo.js`, arquivo separado do `strings.js` escrito à mão. O servidor passa a fundir todos os `.js` de `src/lang/`. No cliente, uma função **pura** em `src/i18n.js` percorre cada mensagem recebida e troca os nomes cujo id tem tradução; o `gameState.js` ganha um gancho que aplica essa função sem conhecê-la. No servidor, só duas mudanças: `t()` passa a resolver parâmetro que é ele próprio um `T`, e um helper `nome_de(familia, id)` devolve esse `T` — os dois pré-requisitos da etapa da narração.

**Stack:** Python 3 + `websockets` (servidor), JavaScript vanilla sem bundler (cliente), testes `tools/test_*.py` e `tools/test_*.js` (node).

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** — regras obrigatórias. A que mais importa aqui: `src/gameState.js` **nunca** pode referenciar `document`, `canvas`, `THREE` ou `window`. É por isso que o gancho de filtro recebe uma função de fora em vez de chamar o `I18N` diretamente. `src/i18n.js` pode usar `window` (como `src/visualConfig.js` faz), mas **não** pode tocar em `document`.
- **Nunca edite `game.js` por PowerShell/`sed`.** Use a ferramenta Edit. São ~25.900 linhas com todo o HTML do jogo numa template string.
- **O usuário edita `game.js`, `game.css` e arquivos `.glb` em paralelo.** Antes de cada commit rode `git status` e use só os caminhos listados no passo — nunca `git add -A` nem `git add .`.
- **Etapa 1 (já pronta):** dicionário `src/lang/strings.js` (`window.LANG_STRINGS`, formato `{chave: {pt, en}}`), motor puro `src/i18n.js` (`window.I18N` com `t/setLang/on/lang`), `_load_lang()`/`t()`/`T`/`_t_render()`/`_lang_de()`/`_lang_valido()` no `server.py`, mensagem `set_lang`, e tradução por conexão em `broadcast`/`send_to`. Testes: `tools/test_idioma.py` (31) e `tools/test_idioma_cliente.js` (16).

### Números medidos (use-os para conferir seu trabalho)

| Família | Origem | Chaves |
|---|---|---:|
| `item` | `WEAPONS` ∪ `SHOP_WEAPONS` ∪ `SHOP_ARMORS` ∪ `SHOP_MERCHANT` ∪ `SHOP_TEMPLE` ∪ `SHOP_TAVERN` ∪ `ARREMESSAVEIS` ∪ `VENENOS` | 140 |
| `guilda` | `GUILD_CATALOG` | 125 |
| `monstro` | `MONSTER_DEFS` (id no campo `type`) | 51 |
| `decor` | `DECOR_TYPES` | 28 |
| `magia` | `GRIMORIO` | 27 |
| `armadilha` | `ARMADILHAS` | 11 |
| `instrumento` | `INSTRUMENTOS_BASE` | 9 |
| `classe` | `CLASSES` | 6 |
| **Total** | | **397** |

Já verificado: os 8 catálogos de item somam 175 entradas com id que deduplicam em 140, e **nenhum id repetido carrega nome diferente**; e **não há colisão de id entre famílias** com nomes divergentes. É isso que torna seguro o filtro procurar as famílias em ordem.

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `tools/gerar_vocabulario.py` | **Criar.** Varre os catálogos e escreve `src/lang/catalogo.js`. Idempotente. |
| `src/lang/catalogo.js` | **Criar (gerado).** As 397 chaves. Nunca editado à mão nas chaves; só a coluna `en` é preenchida. |
| `server.py` | `_load_lang()` funde todos os `.js` de `src/lang/`; `t()` resolve `T` aninhado; helper `nome_de()`. |
| `index.html` | Carrega `src/lang/catalogo.js` depois de `strings.js`. |
| `src/i18n.js` | Ganha `tem(chave)` e `traduzirNomes(msg)` — puros, testáveis por node. |
| `src/gameState.js` | Ganha `setMessageFilter(fn)`, aplicado no `ws.onmessage`. |
| `game.js` | Uma linha: registra `I18N.traduzirNomes` como filtro. |
| `tools/test_vocabulario.py` | **Criar.** Gerador, idempotência, órfãs, colisões, `t()` aninhado, `nome_de`, loader multi-arquivo. |
| `tools/test_vocabulario_cliente.js` | **Criar.** O filtro de nomes. |

---

## Task 1: Gerador de vocabulário

**Arquivos:**
- Criar: `tools/gerar_vocabulario.py`
- Criar: `tools/test_vocabulario.py`
- Criar (gerado): `src/lang/catalogo.js`

- [ ] **Passo 1: Escrever o teste que falha**

Criar `tools/test_vocabulario.py`:

```python
"""Vocabulário (etapa 2) — geração das chaves de nome de catálogo.
Roda da raiz: python tools/test_vocabulario.py"""
import importlib, json, os, shutil, subprocess, sys, tempfile
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

import gerar_vocabulario as G   # tools/ entra no sys.path abaixo


def _rodar_verificacoes():
    print("\n[1] Coleta das famílias")
    vocab = G.coletar()
    esperado = {"item": 140, "guilda": 125, "monstro": 51, "decor": 28,
                "magia": 27, "armadilha": 11, "instrumento": 9, "classe": 6}
    for fam, n in esperado.items():
        check(f"{fam}: {n} chaves", len(vocab.get(fam, {})) == n)
    check("total de 397 chaves", sum(len(d) for d in vocab.values()) == 397)

    print("\n[2] Formato da chave")
    check("chave de item usa o id", "dagger" in vocab["item"])
    check("chave de monstro usa o type", "goblin" in vocab["monstro"])
    check("o pt vem do próprio catálogo", vocab["item"]["dagger"] == "Adaga")
    check("monta cat.<familia>.<id>.nome",
          G.chave("item", "dagger") == "cat.item.dagger.nome")

    print("\n[3] Colisões são erro, não escolha silenciosa")
    try:
        G.fundir_item({"a": "Nome Um"}, {"a": "Nome Dois"}, "TESTE")
        check("id repetido com nome diferente levanta erro", False)
    except G.ColisaoDeId:
        check("id repetido com nome diferente levanta erro", True)
    ok = True
    try:
        G.fundir_item({"a": "Igual"}, {"a": "Igual"}, "TESTE")
    except G.ColisaoDeId:
        ok = False
    check("id repetido com o MESMO nome é aceito", ok)

    print("\n[4] Escrita e releitura do arquivo")
    tmp = tempfile.mkdtemp(prefix="vocab_")
    try:
        alvo = os.path.join(tmp, "catalogo.js")
        G.escrever(alvo, {"cat.item.x.nome": {"pt": "Xis", "en": ""}})
        lido = G.ler_existente(alvo)
        check("o que foi escrito é relido igual",
              lido == {"cat.item.x.nome": {"pt": "Xis", "en": ""}})
        check("o arquivo declara window.LANG_CATALOGO",
              "window.LANG_CATALOGO" in open(alvo, encoding="utf-8").read())
        check("o arquivo funde em LANG_STRINGS",
              "Object.assign(window.LANG_STRINGS" in open(alvo, encoding="utf-8").read())

        print("\n[5] Idempotência: tradução feita à mão sobrevive")
        G.escrever(alvo, {"cat.item.x.nome": {"pt": "Xis", "en": "Ex"}})
        novo, orfas = G.mesclar(G.ler_existente(alvo),
                                {"cat.item.x.nome": "Xis", "cat.item.y.nome": "Ípsilon"})
        check("preserva o en já traduzido", novo["cat.item.x.nome"]["en"] == "Ex")
        check("acrescenta a chave nova com en vazio", novo["cat.item.y.nome"]["en"] == "")
        check("atualiza o pt a partir do catálogo", novo["cat.item.y.nome"]["pt"] == "Ípsilon")
        check("nenhuma órfã neste caso", orfas == [])

        print("\n[6] Órfã é relatada e NÃO apagada")
        novo2, orfas2 = G.mesclar({"cat.item.sumiu.nome": {"pt": "Sumiu", "en": "Gone"}},
                                  {"cat.item.x.nome": "Xis"})
        check("a órfã é relatada", orfas2 == ["cat.item.sumiu.nome"])
        check("a órfã continua no dicionário", "cat.item.sumiu.nome" in novo2)
        check("a tradução da órfã é preservada", novo2["cat.item.sumiu.nome"]["en"] == "Gone")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Vocabulário (nomes de catálogo)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
```

Acrescente, logo depois de `sys.path.insert(0, RAIZ)` e **antes** de `import server as S`:

```python
sys.path.insert(0, os.path.join(RAIZ, "tools"))
```

- [ ] **Passo 2: Rodar o teste e confirmar que falha**

```bash
python tools/test_vocabulario.py
```

Esperado: `ModuleNotFoundError: No module named 'gerar_vocabulario'`.

- [ ] **Passo 3: Implementar o gerador**

Criar `tools/gerar_vocabulario.py`:

```python
"""Gera src/lang/catalogo.js — as chaves de NOME dos catálogos do server.py.

Roda da raiz:  python tools/gerar_vocabulario.py

É idempotente: preserva todo "en" já traduzido, acrescenta as chaves novas com
"en" vazio, atualiza o "pt" a partir do catálogo e RELATA (sem apagar) as chaves
órfãs — aquelas cujo item saiu do catálogo. Rode-o depois de criar item ou
monstro novo: a saída diz exatamente o que falta traduzir.
"""
import json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

DESTINO = os.path.join(RAIZ, "src", "lang", "catalogo.js")


class ColisaoDeId(Exception):
    """Dois catálogos dão nomes diferentes ao mesmo id — ambíguo, então falhamos
    alto em vez de escolher um em silêncio."""


def chave(familia, ident):
    return f"cat.{familia}.{ident}.nome"


def _nome(entrada):
    return entrada.get("name") or entrada.get("nome")


def _entradas(catalogo, campo_id):
    """Devolve {id: nome} de um catálogo (lista ou dict). Quando o campo de id
    não existe na entrada, cai para a chave do dict — vários catálogos do jogo
    identificam o item pela chave, não por um campo."""
    itens = catalogo.items() if isinstance(catalogo, dict) else ((None, e) for e in catalogo)
    out = {}
    for chave_dict, entrada in itens:
        if not isinstance(entrada, dict):
            continue
        nome = _nome(entrada)
        ident = entrada.get(campo_id) or chave_dict
        if ident and nome:
            out[str(ident)] = nome
    return out


def fundir_item(destino, novos, origem):
    """Funde {id: nome} no acumulador de itens, recusando nomes divergentes."""
    for ident, nome in novos.items():
        anterior = destino.get(ident)
        if anterior is not None and anterior != nome:
            raise ColisaoDeId(
                f"id '{ident}' tem nomes diferentes: '{anterior}' e '{nome}' (em {origem})")
        destino[ident] = nome
    return destino


def coletar():
    """Devolve {familia: {id: nome_pt}} a partir dos catálogos do server.py."""
    item = {}
    for nome_cat, campo in (("WEAPONS", "id"), ("SHOP_WEAPONS", "id"), ("SHOP_ARMORS", "id"),
                            ("SHOP_MERCHANT", "id"), ("SHOP_TEMPLE", "id"), ("SHOP_TAVERN", "id"),
                            ("ARREMESSAVEIS", "id"), ("VENENOS", "id")):
        fundir_item(item, _entradas(getattr(S, nome_cat), campo), nome_cat)
    return {
        "item":        item,
        "guilda":      _entradas(S.GUILD_CATALOG, "id"),
        "monstro":     _entradas(S.MONSTER_DEFS, "type"),
        "decor":       _entradas(S.DECOR_TYPES, "id"),
        "magia":       _entradas(S.GRIMORIO, "id"),
        "armadilha":   _entradas(S.ARMADILHAS, "id"),
        "instrumento": _entradas(S.INSTRUMENTOS_BASE, "id"),
        "classe":      _entradas(S.CLASSES, "id"),
    }


def achatar(vocab):
    """{familia: {id: nome}} → {chave: nome_pt}."""
    return {chave(fam, ident): nome
            for fam, entradas in vocab.items()
            for ident, nome in entradas.items()}


def ler_existente(caminho):
    """Lê o catalogo.js já gerado (se houver). Ausente ou ilegível → {}."""
    try:
        with open(caminho, encoding="utf-8") as f:
            raw = f.read()
        m = re.search(r"^\s*window\.LANG_CATALOGO\s*=", raw, re.MULTILINE)
        ini = raw.index("{", m.end())
        return json.loads(raw[ini:raw.rindex("}") + 1])
    except Exception:
        return {}


def mesclar(existente, plano):
    """Une o que já existe com o que o catálogo manda agora.
    Devolve (dicionário, lista de chaves órfãs). Órfã é relatada, nunca apagada:
    um item pode ter sido renomeado por engano, e jogar a tradução fora seria
    perder trabalho de forma irreversível."""
    saida = {}
    for k, pt in plano.items():
        saida[k] = {"pt": pt, "en": (existente.get(k) or {}).get("en", "")}
    orfas = sorted(k for k in existente if k not in plano)
    for k in orfas:
        saida[k] = existente[k]
    return saida, orfas


def escrever(caminho, dicionario):
    corpo = json.dumps(dicionario, ensure_ascii=False, indent=2, sort_keys=True)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "// GERADO por tools/gerar_vocabulario.py — não edite as CHAVES à mão.\n"
            "// Preencha só a coluna \"en\"; rodar o gerador de novo preserva o que\n"
            "// você já traduziu e acrescenta o que for novo.\n"
            "window.LANG_CATALOGO = " + corpo + ";\n"
            "Object.assign(window.LANG_STRINGS, window.LANG_CATALOGO);\n")


def main():
    plano = achatar(coletar())
    novo, orfas = mesclar(ler_existente(DESTINO), plano)
    escrever(DESTINO, novo)
    faltando = sorted(k for k, v in novo.items() if not v.get("en"))
    print(f"{len(plano)} chaves no catálogo, {len(novo)} no arquivo.")
    print(f"{len(faltando)} sem tradução para o inglês.")
    if orfas:
        print(f"\n⚠️  {len(orfas)} chave(s) órfã(s) — o item saiu do catálogo. "
              f"Foram MANTIDAS; apague à mão se forem mesmo lixo:")
        for k in orfas:
            print("   ", k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Passo 4: Rodar o teste e confirmar que passa**

```bash
python tools/test_vocabulario.py
```

Esperado: `25 passaram, 0 falharam`.

- [ ] **Passo 5: Gerar o arquivo de verdade**

```bash
python tools/gerar_vocabulario.py
```

Esperado: `397 chaves no catálogo, 397 no arquivo.` seguido de `397 sem tradução para o inglês.` e nenhuma órfã.

- [ ] **Passo 6: Confirmar que rodar de novo não muda nada**

```bash
python tools/gerar_vocabulario.py && git diff --stat src/lang/catalogo.js
```

Esperado: a mesma saída e **nenhuma** diferença no `git diff` (o arquivo acabou de ser criado e ainda não está no git, então basta a saída ser idêntica; se já estiver commitado, o diff tem que vir vazio).

- [ ] **Passo 7: Commit**

```bash
git add tools/gerar_vocabulario.py tools/test_vocabulario.py src/lang/catalogo.js
git commit -m "feat(i18n): gerador das chaves de nome de catalogo"
```

---

## Task 2: Carregador multi-arquivo

**Arquivos:**
- Modificar: `server.py` (`_load_lang`, e as constantes `LANG_FILE` do bloco de i18n)
- Modificar: `index.html`
- Modificar: `tools/test_vocabulario.py`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()` em `tools/test_vocabulario.py`:

```python
    print("\n[7] O servidor funde todos os .js de src/lang/")
    check("o dicionário do servidor tem chave do strings.js",
          "erro.porta_longe" in S.LANG_STRINGS)
    check("o dicionário do servidor tem chave do catalogo.js",
          "cat.monstro.goblin.nome" in S.LANG_STRINGS)
    check("o nome em pt veio do catálogo",
          S.t("cat.monstro.goblin.nome", "pt") == "Goblin")
    # Nenhuma chave do arquivo pode apontar para item que saiu do catálogo: se
    # apontasse, o jogo mostraria em inglês um nome que não existe mais.
    plano = G.achatar(G.coletar())
    no_arquivo = G.ler_existente(G.DESTINO)
    check("nenhuma chave órfã no catalogo.js gerado",
          sorted(k for k in no_arquivo if k not in plano) == [])
```

- [ ] **Passo 2: Rodar o teste e confirmar que falha**

```bash
python tools/test_vocabulario.py
```

Esperado: as duas últimas checagens da seção [7] falham — o `_load_lang` ainda lê só o `strings.js`.

- [ ] **Passo 3: Implementar a fusão**

Em `server.py`, no bloco de i18n, trocar a constante:

```python
LANG_FILE = os.path.join(BASE_DIR, "src", "lang", "strings.js")
```

por:

```python
LANG_DIR = os.path.join(BASE_DIR, "src", "lang")
LANG_FILE = os.path.join(LANG_DIR, "strings.js")   # mantido: o teste da etapa 1 aponta para cá
```

E substituir a função `_load_lang()` inteira por:

```python
def _load_lang_arquivo(caminho):
    """Extrai o dicionário de UM arquivo de idioma. O formato é JS por causa do
    cliente (carrega por <script>, sem fetch); aqui achamos a linha de atribuição
    `window.LANG_<algo> =` e pegamos da sua { até a última } do arquivo.
    Ancorado no INÍCIO da linha: um comentário (sempre prefixado por //) nunca
    casa, então cabeçalhos e comentários de seção podem citar "LANG_STRINGS" ou
    conter chaves à vontade sem confundir o recorte."""
    with open(caminho, encoding="utf-8") as f:
        raw = f.read()
    m = re.search(r"^\s*window\.LANG_\w+\s*=", raw, re.MULTILINE)
    ini = raw.index("{", m.end())
    return json.loads(raw[ini:raw.rindex("}") + 1])

def _load_lang():
    """Funde TODOS os .js de src/lang/. São dois hoje: o strings.js escrito à mão
    e o catalogo.js gerado por tools/gerar_vocabulario.py — separados justamente
    para o gerador nunca sobrescrever tradução feita à mão. Falha em um arquivo
    não impede o servidor de subir nem descarta os outros."""
    out = {}
    try:
        arquivos = sorted(f for f in os.listdir(LANG_DIR) if f.endswith(".js"))
    except Exception as e:
        print(f"⚠️  i18n: não foi possível listar {LANG_DIR} ({type(e).__name__}: {e}) — "
              f"o jogo segue em português.")
        return out
    for nome in arquivos:
        caminho = os.path.join(LANG_DIR, nome)
        try:
            out.update(_load_lang_arquivo(caminho))
        except Exception as e:
            print(f"⚠️  i18n: não foi possível ler {caminho} ({type(e).__name__}: {e}) — "
                  f"as chaves deste arquivo ficam em português.")
    return out
```

- [ ] **Passo 4: Rodar os testes**

```bash
python tools/test_vocabulario.py && python tools/test_idioma.py
```

Esperado: `29 passaram, 0 falharam` no primeiro e `31 passaram, 0 falharam` no segundo. O teste da etapa 1 tem uma checagem que troca `S.LANG_FILE` por um caminho inexistente e espera `{}` — ela continua válida porque `_load_lang_arquivo` é quem lê um arquivo só; se ela quebrar, **pare e reporte**, não a altere.

- [ ] **Passo 5: Carregar o catálogo no `index.html`**

Em `index.html`, na linha que faz `document.write` dos scripts síncronos, acrescentar `src/lang/catalogo.js` **depois** de `src/lang/strings.js` e **antes** de `src/i18n.js`. A linha passa de:

```html
<script>(function(){var v=Date.now();document.write('<script src="src/lang/strings.js?v='+v+'"><\/script>');document.write('<script src="src/i18n.js?v='+v+'"><\/script>');document.write('<script src="src/visualConfig.js?v='+v+'"><\/script>');document.write('<script src="src/ui/theme.js?v='+v+'"><\/script>');})();</script>
```

para:

```html
<script>(function(){var v=Date.now();document.write('<script src="src/lang/strings.js?v='+v+'"><\/script>');document.write('<script src="src/lang/catalogo.js?v='+v+'"><\/script>');document.write('<script src="src/i18n.js?v='+v+'"><\/script>');document.write('<script src="src/visualConfig.js?v='+v+'"><\/script>');document.write('<script src="src/ui/theme.js?v='+v+'"><\/script>');})();</script>
```

A ordem é obrigatória: o `catalogo.js` termina com `Object.assign(window.LANG_STRINGS, …)` e precisa que o `strings.js` já tenha criado esse objeto.

- [ ] **Passo 6: Commit**

```bash
git add server.py index.html tools/test_vocabulario.py
git commit -m "feat(i18n): carregador funde todos os arquivos de src/lang"
```

---

## Task 3: Parâmetro aninhado e `nome_de` no servidor

**Arquivos:**
- Modificar: `server.py` (`t()` e o bloco de i18n)
- Modificar: `tools/test_vocabulario.py`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()` em `tools/test_vocabulario.py`:

```python
    print("\n[8] Parâmetro que é ele próprio traduzível")
    S.LANG_STRINGS["_teste.frase"] = {"pt": "{quem} atacou!", "en": "{quem} attacked!"}
    check("resolve o T aninhado em inglês",
          S.t("_teste.frase", "en", quem=S.T("cat.monstro.goblin.nome"))
          == S.t("cat.monstro.goblin.nome", "en") + " attacked!")
    check("resolve o T aninhado em português",
          S.t("_teste.frase", "pt", quem=S.T("cat.monstro.goblin.nome")) == "Goblin atacou!")
    check("parâmetro comum continua funcionando",
          S.t("_teste.frase", "pt", quem="Thorin") == "Thorin atacou!")
    check("T aninhado com parâmetro próprio também resolve",
          S.t("_teste.frase", "pt", quem=S.T("narracao.abre_porta", nome="Lyra"))
          == "🚪 **Lyra** abre uma porta! atacou!")
    S.LANG_STRINGS.pop("_teste.frase", None)

    print("\n[9] nome_de devolve um T com a chave certa")
    marcado = S.nome_de("monstro", "goblin")
    check("nome_de devolve T", isinstance(marcado, S.T))
    check("nome_de monta a chave", marcado.key == "cat.monstro.goblin.nome")
    check("nome_de rende o nome", S._t_render(marcado, "pt") == "Goblin")
```

- [ ] **Passo 2: Rodar o teste e confirmar que falha**

```bash
python tools/test_vocabulario.py
```

Esperado: a seção [8] falha com o texto contendo `T('cat.monstro.goblin.nome', {})`, e a [9] com `AttributeError: module 'server' has no attribute 'nome_de'`.

- [ ] **Passo 3: Implementar**

Em `server.py`, substituir a função `t()` inteira por:

```python
def _param_texto(valor, lang):
    """Um parâmetro pode ser ele próprio traduzível — é o caso de todo nome de
    monstro, item ou habilidade que aparece dentro de uma frase. Sem isto, o
    str() de um T devolveria o repr e a frase em inglês sairia com o nome em
    português cravado."""
    if isinstance(valor, T):
        return t(valor.key, lang, **valor.params)
    return str(valor)

def t(key, lang=LANG_DEFAULT, **params):
    """Traduz uma chave. Sem tradução no idioma pedido → português. Sem a chave
    → devolve a própria chave (aparece na tela, mas nada quebra)."""
    entry = LANG_STRINGS.get(key)
    if not isinstance(entry, dict):
        return key
    text = entry.get(lang) or entry.get(LANG_DEFAULT) or key
    if params:
        # Substituição por nome (e não .format) para que uma chave sem o
        # parâmetro — ou uma chave { solta no texto — nunca levante exceção.
        text = _LANG_PARAM_RE.sub(
            lambda m: _param_texto(params[m.group(1)], lang) if m.group(1) in params
            else m.group(0), text)
    return text
```

E acrescentar, logo depois da função `_lang_valido`:

```python
def nome_de(familia, ident):
    """Nome de catálogo como texto TARDIO, para entrar numa frase e ser resolvido
    no idioma de quem vai ler. Famílias: item, guilda, monstro, decor, magia,
    armadilha, instrumento, classe. Id sem tradução cai na própria chave, então
    prefira montar a frase com o nome já em mãos quando o item for autoral."""
    return T(f"cat.{familia}.{ident}.nome")
```

- [ ] **Passo 4: Rodar os testes**

```bash
python tools/test_vocabulario.py && python tools/test_idioma.py && python tools/test_modo_mestre.py
```

Esperado: `36 passaram, 0 falharam` (vocabulário), `31 passaram, 0 falharam` (idioma) e `336 passaram, 0 falharam` (modo mestre). A última é a linha de base de regressão — se ficar vermelha, **pare e reporte BLOCKED**.

- [ ] **Passo 5: Commit**

```bash
git add server.py tools/test_vocabulario.py
git commit -m "feat(i18n): t() resolve parametro aninhado e nome_de devolve T"
```

---

## Task 4: Filtro de nomes no motor do cliente

**Arquivos:**
- Modificar: `src/i18n.js`
- Criar: `tools/test_vocabulario_cliente.js`

- [ ] **Passo 1: Escrever o teste que falha**

Criar `tools/test_vocabulario_cliente.js`:

```js
// Filtro de nomes de catálogo — roda da raiz: node tools/test_vocabulario_cliente.js
const fs = require("fs");
const path = require("path");
const raiz = path.join(__dirname, "..");

let PASS = 0, FAIL = 0;
const check = (name, cond) => { if (cond) { PASS++; console.log("  ✅ " + name); }
                                else { FAIL++; console.log("  ❌ " + name); } };

global.window = {};
eval(fs.readFileSync(path.join(raiz, "src", "lang", "strings.js"), "utf8"));
eval(fs.readFileSync(path.join(raiz, "src", "lang", "catalogo.js"), "utf8"));
eval(fs.readFileSync(path.join(raiz, "src", "i18n.js"), "utf8"));
const DICT = global.window.LANG_STRINGS;
const I18N = global.window.I18N;

console.log("\n[1] O catálogo entrou no dicionário");
check("catalogo.js fundiu em LANG_STRINGS", !!DICT["cat.monstro.goblin.nome"]);
check("o pt do goblin veio do catálogo", DICT["cat.monstro.goblin.nome"].pt === "Goblin");

console.log("\n[2] tem() diz se a chave existe");
check("tem() acha chave existente", I18N.tem("cat.monstro.goblin.nome") === true);
check("tem() nega chave inexistente", I18N.tem("cat.monstro.nao_existe.nome") === false);

// Traduções de teste, independentes do estado real do catalogo.js.
DICT["cat.monstro.goblin.nome"] = { pt: "Goblin", en: "Goblin Scout" };
DICT["cat.item.dagger.nome"]    = { pt: "Adaga",  en: "Dagger" };

console.log("\n[3] Em português o filtro não mexe em nada");
I18N.setLang("pt");
const emPt = I18N.traduzirNomes({ monsters: [{ type: "goblin", name: "Goblin" }] });
check("nome fica intacto em pt", emPt.monsters[0].name === "Goblin");

console.log("\n[4] Em inglês traduz monstro e item");
I18N.setLang("en");
const msg = I18N.traduzirNomes({
  monsters: [{ type: "goblin", name: "Goblin" }],
  players: [{ id: "id_7", name: "Thorin",
              bag: [{ id: "dagger", name: "Adaga" }],
              gear: { main_hand: { id: "dagger", name: "Adaga" } } }],
});
check("monstro traduzido pelo type", msg.monsters[0].name === "Goblin Scout");
check("item da bolsa traduzido pelo id", msg.players[0].bag[0].name === "Dagger");
check("item equipado (aninhado em objeto) traduzido",
      msg.players[0].gear.main_hand.name === "Dagger");
check("nome do JOGADOR não é tocado", msg.players[0].name === "Thorin");

console.log("\n[5] Conteúdo autoral sobrevive intacto");
const autoral = I18N.traduzirNomes({
  monsters: [{ type: "meu_monstro_custom", name: "Guardião de Pedra" }],
  chests: [{ items: [{ id: "meu_item_custom", name: "Lâmina do Autor" }] }],
});
check("monstro do editor mantém o nome", autoral.monsters[0].name === "Guardião de Pedra");
check("item do editor mantém o nome", autoral.chests[0].items[0].name === "Lâmina do Autor");

console.log("\n[6] Campo 'nome' (catálogos que usam português) também é traduzido");
DICT["cat.guilda.brutalidade.nome"] = { pt: "Brutalidade", en: "Brutality" };
const guilda = I18N.traduzirNomes({ guild: [{ id: "brutalidade", nome: "Brutalidade" }] });
check("campo nome traduzido", guilda.guild[0].nome === "Brutality");

console.log("\n[7] Ciclos não travam o filtro");
const ciclo = { monsters: [{ type: "goblin", name: "Goblin" }] };
ciclo.eu = ciclo;
let travou = false;
try { I18N.traduzirNomes(ciclo); } catch (e) { travou = true; }
check("estrutura com referência circular não estoura", !travou);

console.log("\n" + "=".repeat(62));
console.log(`  ${PASS} passaram, ${FAIL} falharam`);
console.log("=".repeat(62));
process.exit(FAIL ? 1 : 0);
```

- [ ] **Passo 2: Rodar o teste e confirmar que falha**

```bash
node tools/test_vocabulario_cliente.js
```

Esperado: falha na seção [2] com `TypeError: I18N.tem is not a function`.

- [ ] **Passo 3: Implementar no motor**

Em `src/i18n.js`, logo **depois** da função `setLang` e **antes** do `window.I18N = {`, inserir:

```js
  // ── Nomes de catálogo ──────────────────────────────────────────────────────
  // As chaves são cat.<família>.<id>.nome, geradas por tools/gerar_vocabulario.py.
  // O id já viaja no payload, então o nome traduzido é achado sem o servidor
  // precisar mandar nada novo. Ordem de busca por campo — não há colisão de id
  // entre famílias hoje, e o gerador falha alto se aparecer uma.
  const FAMILIAS_POR_CAMPO = {
    type: ['monstro', 'decor'],
    id:   ['item', 'guilda', 'magia', 'instrumento', 'armadilha', 'classe'],
  };
  const CAMPOS_NOME = ['name', 'nome'];

  function tem(key) {
    return Object.prototype.hasOwnProperty.call(DICT, key);
  }

  // Devolve a chave de nome que serve para este objeto, ou null.
  function _chaveDeNome(o) {
    for (const campoId in FAMILIAS_POR_CAMPO) {
      const id = o[campoId];
      if (typeof id !== 'string' || !id) continue;
      for (const fam of FAMILIAS_POR_CAMPO[campoId]) {
        const key = 'cat.' + fam + '.' + id + '.nome';
        if (tem(key)) return key;
      }
    }
    return null;
  }

  // Percorre a mensagem recebida e troca os nomes de catálogo pelo idioma atual.
  // Muta o objeto de propósito: ele é JSON recém-parseado, ninguém mais o vê.
  // Objeto sem tradução para o seu id fica intacto — é assim que item e monstro
  // criados no editor mantêm o nome autoral.
  function traduzirNomes(msg) {
    if (lang === PADRAO) return msg;   // em português não há o que trocar
    const vistos = new Set();
    (function anda(o) {
      if (!o || typeof o !== 'object' || vistos.has(o)) return;
      vistos.add(o);
      if (Array.isArray(o)) { for (const v of o) anda(v); return; }
      const key = _chaveDeNome(o);
      if (key) {
        for (const campo of CAMPOS_NOME) {
          if (typeof o[campo] === 'string') { o[campo] = t(key); break; }
        }
      }
      for (const k in o) anda(o[k]);
    })(msg);
    return msg;
  }
```

E no objeto exportado, acrescentar as duas funções:

```js
  window.I18N = {
    t: t,
    tem: tem,
    traduzirNomes: traduzirNomes,
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

Esperado: `13 passaram, 0 falharam` no primeiro e `16 passaram, 0 falharam` no segundo.

- [ ] **Passo 5: Commit**

```bash
git add src/i18n.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): filtro que traduz nomes de catalogo no cliente"
```

---

## Task 5: Ligar o filtro à entrada de mensagens

**Arquivos:**
- Modificar: `src/gameState.js`
- Modificar: `game.js`
- Modificar: `tools/test_vocabulario_cliente.js`

> **Lembrete:** edite `game.js` **apenas** com a ferramenta Edit, e confira `git status` antes do commit — o usuário tem trabalho não commitado nesse arquivo.

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar em `tools/test_vocabulario_cliente.js`, logo **antes** do bloco final de resumo:

```js
console.log("\n[8] A fiação com o gameState existe");
// Checagem estática: o teste não consegue carregar game.js nem gameState.js
// (o primeiro monta o DOM inteiro no load), então verificamos a fiação no fonte.
const gamejs = fs.readFileSync(path.join(raiz, "game.js"), "utf8");
const gs = fs.readFileSync(path.join(raiz, "src", "gameState.js"), "utf8");
check("gameState expõe setMessageFilter", /setMessageFilter/.test(gs));
check("o filtro é aplicado antes do _handle",
      /_messageFilter[\s\S]{0,400}?_handle\(/.test(gs));
check("game.js registra I18N.traduzirNomes como filtro",
      /GS\.setMessageFilter\(\s*I18N\.traduzirNomes\s*\)/.test(gamejs));
```

- [ ] **Passo 2: Rodar o teste e confirmar que falha**

```bash
node tools/test_vocabulario_cliente.js
```

Esperado: as três checagens da seção [8] falham.

- [ ] **Passo 3: Implementar o gancho no `gameState.js`**

Em `src/gameState.js`, logo **depois** da função `setLang` (a que faz `send({ type: 'set_lang', lang: code })`), inserir:

```js
  // ── Filtro de mensagens ───────────────────────────────────────────────────
  // O renderer registra aqui uma função aplicada a TODA mensagem que chega,
  // antes do despacho — hoje é a tradução dos nomes de catálogo. Este módulo
  // não conhece o I18N nem o dicionário (regra do CLAUDE.md: nada de window
  // aqui); ele só chama o que recebeu.
  let _messageFilter = null;
  function setMessageFilter(fn) {
    _messageFilter = (typeof fn === 'function') ? fn : null;
  }
```

Em `src/gameState.js`, dentro de `_wireWs`, trocar:

```js
    ws.onmessage = e => {
      try {
        _rejoinTries = 0;   // qualquer mensagem válida = conexão saudável
        _handle(JSON.parse(e.data));
      }
      catch (err) { console.error('WS parse/handle error:', err, e.data?.slice?.(0, 200)); }
    };
```

por:

```js
    ws.onmessage = e => {
      try {
        _rejoinTries = 0;   // qualquer mensagem válida = conexão saudável
        let msg = JSON.parse(e.data);
        if (_messageFilter) {
          // Um filtro com defeito não pode derrubar a partida: se ele estourar,
          // a mensagem segue crua (em português) em vez de se perder.
          try { msg = _messageFilter(msg) || msg; }
          catch (err) { console.error('filtro de mensagem falhou:', err); }
        }
        _handle(msg);
      }
      catch (err) { console.error('WS parse/handle error:', err, e.data?.slice?.(0, 200)); }
    };
```

Em `src/gameState.js`, no objeto exportado (na lista onde estão `isPreview: PREVIEW,` e `setLang,`), acrescentar:

```js
    setMessageFilter,
```

- [ ] **Passo 4: Registrar o filtro no `game.js`**

Em `game.js`, no bloco de idioma, logo **depois** da linha `I18N.on(code => GS.setLang(code));`, inserir:

```js
// Nomes de item e monstro chegam do servidor em português; o filtro os troca
// pelo idioma atual assim que a mensagem entra, então os pontos de render
// continuam lendo .name sem saber que existe tradução.
GS.setMessageFilter(I18N.traduzirNomes);
```

- [ ] **Passo 5: Rodar os testes**

```bash
node tools/test_vocabulario_cliente.js && node tools/test_idioma_cliente.js && node --check game.js && node --check src/gameState.js
```

Esperado: `16 passaram, 0 falharam`, `16 passaram, 0 falharam`, e nenhuma saída dos dois `--check`.

- [ ] **Passo 6: Commit**

```bash
git add src/gameState.js game.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): filtro de nomes ligado a entrada de mensagens"
```

---

## Task 6: Traduzir os 397 nomes

**Arquivos:**
- Modificar: `src/lang/catalogo.js` (só a coluna `en`)

Esta é a tradução propriamente dita. **Não invente chaves nem mexa no `pt`** — a coluna `pt` vem do catálogo e o gerador a reescreve.

O plano não lista as 397 traduções de propósito: as chaves e o texto em português são **gerados** na Task 1 e só existem depois que o gerador roda. O que o plano fixa são as decisões — o glossário abaixo, que resolve a consistência, e os comandos de conferência, que provam que nada ficou de fora.

**Glossário — decida uma vez e use em tudo.** Estes termos aparecem dezenas de vezes; traduzi-los de formas diferentes em lugares diferentes é o erro mais fácil de cometer aqui:

| Português | Inglês |
|---|---|
| Adaga / Espada / Machado / Maça / Lança | Dagger / Sword / Axe / Mace / Spear |
| Arco / Besta / Virote / Flecha | Bow / Crossbow / Bolt / Arrow |
| Poção / Pergaminho / Frasco | Potion / Scroll / Vial |
| Couro / Cota de Malha / Placas | Leather / Chainmail / Plate |
| Golpe / Ataque / Investida | Strike / Attack / Charge |
| Fúria / Sagrado / Divino / Arcano | Rage / Holy / Divine / Arcane |
| Canção / Provocação / Lenda | Song / Taunt / Lore |
| Armadilha / Fosso / Rede | Trap / Pit / Net |
| Menor / Maior / Supremo | Lesser / Greater / Supreme |

Nomes próprios de herói (Henrique, Pedro, Lewis, Richard, Luccas) **não são traduzidos** — não estão neste arquivo, mas se cruzar com algum, deixe.

- [ ] **Passo 1: Traduzir itens (140 chaves)**

Preencher o `en` de todas as chaves `cat.item.*` em `src/lang/catalogo.js`. Conferir:

```bash
python -c "import json,re,io; raw=io.open('src/lang/catalogo.js',encoding='utf-8').read(); d=json.loads(raw[raw.index('{'):raw.rindex('}')+1]); f=[k for k,v in d.items() if k.startswith('cat.item.') and not v['en']]; print(len(f),'itens sem traducao'); print('\n'.join(f[:10]))"
```

Esperado: `0 itens sem traducao`.

- [ ] **Passo 2: Commit**

```bash
git add src/lang/catalogo.js
git commit -m "feat(i18n): traduz os nomes de item para ingles"
```

- [ ] **Passo 3: Traduzir Guilda e magias (152 chaves)**

Preencher o `en` das chaves `cat.guilda.*` e `cat.magia.*`. Conferir:

```bash
python -c "import json,re,io; raw=io.open('src/lang/catalogo.js',encoding='utf-8').read(); d=json.loads(raw[raw.index('{'):raw.rindex('}')+1]); f=[k for k,v in d.items() if (k.startswith('cat.guilda.') or k.startswith('cat.magia.')) and not v['en']]; print(len(f),'sem traducao')"
```

Esperado: `0 sem traducao`.

- [ ] **Passo 4: Commit**

```bash
git add src/lang/catalogo.js
git commit -m "feat(i18n): traduz os nomes da Guilda e das magias"
```

- [ ] **Passo 5: Traduzir monstros, decorações, armadilhas, instrumentos e classes (105 chaves)**

Preencher o `en` das chaves `cat.monstro.*`, `cat.decor.*`, `cat.armadilha.*`, `cat.instrumento.*` e `cat.classe.*`. Conferir que **nada** ficou de fora:

```bash
python -c "import json,io; raw=io.open('src/lang/catalogo.js',encoding='utf-8').read(); d=json.loads(raw[raw.index('{'):raw.rindex('}')+1]); f=[k for k,v in d.items() if not v['en']]; print(len(f),'chaves sem traducao no arquivo inteiro'); print('\n'.join(f[:10]))"
```

Esperado: `0 chaves sem traducao no arquivo inteiro`.

- [ ] **Passo 6: Confirmar que o gerador continua idempotente com as traduções**

```bash
python tools/gerar_vocabulario.py && git diff --stat src/lang/catalogo.js
```

Esperado: `397 chaves no catálogo, 397 no arquivo.`, `0 sem tradução para o inglês.`, nenhuma órfã e **nenhuma diferença** no `git diff` — provando que o gerador preserva o trabalho de tradução.

- [ ] **Passo 7: Commit**

```bash
git add src/lang/catalogo.js
git commit -m "feat(i18n): traduz monstros, decoracoes, armadilhas, instrumentos e classes"
```

---

## Task 7: Verificação final

**Arquivos:**
- Modificar: `CLAUDE.md`

- [ ] **Passo 1: Rodar as quatro suítes de idioma**

```bash
python tools/test_idioma.py && python tools/test_vocabulario.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: `31` (idioma), `36` (vocabulário), `16` (idioma cliente) e `16` (vocabulário cliente) passando, zero falhando.

- [ ] **Passo 2: Rodar as suítes de regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_cenas_conversa.py && python tools/test_masmorra_sequenciada.py
```

Esperado: `336`, `54`, `57` e `118`, zero falhando em todas. Essa é a linha de base medida antes da etapa 1; qualquer vermelha aqui é regressão de verdade.

- [ ] **Passo 3: Verificação no jogo**

Com o servidor rodando (`python server.py`) e o navegador em `http://localhost:8765/index.html`:

1. Trocar o idioma para **English** no painel ⚙️.
2. Criar uma sala, escolher um herói e entrar numa masmorra.
3. Abrir o inventário. Confirmar que os nomes dos itens da bolsa e do equipamento estão em **inglês**.
4. Olhar o tabuleiro e o log. Confirmar que os nomes dos monstros estão em **inglês**.
5. Abrir a ficha do herói e a aba de habilidades. Confirmar que as técnicas da Guilda e as magias estão em **inglês**.
6. Voltar o idioma para **Português** e confirmar que tudo volta ao português no mesmo instante (o servidor reenvia o estado, e ele passa pelo filtro de novo).
7. Abrir o console (F12) e confirmar que **não** há avisos `[i18n] chave ausente`.

Anote o resultado de cada item. Se algum falhar, corrija antes de seguir.

- [ ] **Passo 4: Documentar no CLAUDE.md**

Em `CLAUDE.md`, acrescentar ao fim (junto dos outros blocos `>`):

```markdown
> **Idioma — vocabulário (etapa 2 de 5):** os **397 nomes** de catálogo (item, guilda,
> monstro, decor, magia, armadilha, instrumento, classe) traduzidos. As chaves seguem
> `cat.<família>.<id>.nome` e são **geradas** por `tools/gerar_vocabulario.py` a partir dos
> catálogos do `server.py` para `src/lang/catalogo.js` — arquivo separado do `strings.js`
> escrito à mão, para o gerador nunca sobrescrever tradução manual. O gerador é idempotente
> (preserva o `en`, acrescenta chave nova, **relata sem apagar** as órfãs) e falha alto se
> dois catálogos derem nomes diferentes ao mesmo id. **Rode-o depois de criar item ou
> monstro novo** — a saída diz o que falta traduzir. `_load_lang()` agora funde TODOS os
> `.js` de `src/lang/`. **Cliente:** `I18N.traduzirNomes(msg)` (puro, em `src/i18n.js`)
> percorre cada mensagem recebida e troca `name`/`nome` quando o `type` ou o `id` do objeto
> tem chave no dicionário; `gameState.js` ganhou `setMessageFilter(fn)`, aplicado no
> `ws.onmessage` antes do `_handle` — ele não conhece o I18N (regra do CLAUDE.md), só chama
> a função que o `game.js` registrou. Isso deixa os **405 pontos de render que leem `.name`
> intocados**, e faz item/monstro criados no editor manterem o nome autoral de graça (sem
> chave → sem troca). Em português o filtro retorna na primeira linha, custo zero.
> **Servidor:** `t()` resolve parâmetro que é ele próprio um `T` (sem isso, frase em inglês
> sairia com nome em português cravado — era o bloqueio da etapa de narração), e
> `nome_de(familia, id)` devolve esse `T`. Nenhum payload mudou. **Etapas restantes:**
> descrições de catálogo (185), erros (470) e narração (544) do servidor, interface do
> cliente (~1.000). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-10-idioma-etapa2-vocabulario*`. Testes:
> `tools/test_vocabulario.py` e `tools/test_vocabulario_cliente.js`.
```

- [ ] **Passo 5: Commit final**

```bash
git add CLAUDE.md
git commit -m "docs(i18n): documenta o vocabulario da etapa 2"
```
