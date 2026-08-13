# Etapa 4b-ii do idioma — Narração do servidor, o que sobrou — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-13-idioma-etapa4b2-narracao-restante-design.md`

**Objetivo:** Migrar para `T(...)` e traduzir os ~126 `gm_say` que sobraram — 110 multilinha, 1 que atravessa a linha, 3 concatenações, as 30 frases do pool `gm()` e os 6 que recebem string pronta —, deixando o servidor sem nenhuma narração em português.

**Arquitetura:** Um migrador baseado no módulo `ast` (não regex) reescreve os spans das chamadas de trás para frente no arquivo. O pool `gm(key)` passa a sortear o índice e devolver `T`. O motor aprende a juntar listas com separador do próprio idioma, o que também fecha uma limitação registrada na 4c.

**Stack:** Python 3 (servidor, migrador, testes), JavaScript vanilla (motor e dicionário do cliente).

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** — regras obrigatórias do projeto.
- **O usuário edita `server.py` e `game.js` em paralelo.** Antes de cada commit rode `git status` e use só os caminhos do passo — **nunca** `git add -A` nem `git add .`. Não mate processo nenhum. **Combine com ele que o `server.py` fica pausado** antes de rodar a Task 3, que reescreve spans espalhados pelo arquivo inteiro.
- **Etapas 1–4c (prontas):** `T("chave", **params)` marca texto ainda não traduzido; `broadcast`/`send_to`/`err` o resolvem no idioma de cada conexão pelo `default` do `json.dumps`; `_param_texto` resolve parâmetro que é ele próprio um `T`; `nome_cat`/`nome_criatura`/`nome_item` resolvem nome de catálogo com guarda de igualdade.
- **O `T` se comporta como o texto em português** para quem o trate como string (`__len__`, `__contains__`, `__getattr__`) — isso mantém 24 mocks de teste funcionando, e é o que faz `if log:` continuar valendo quando o produtor passar a devolver `T`. **Não** o transforme em subclasse de `str`: o `json.dumps` pararia de chamar o `default`. E ele **não** funciona em `str.join` — use `str(x)` explícito ali.
- **`_load_lang()` funde TODOS os `.js` de `src/lang/`** — hoje `strings.js`, `catalogo.js`, `composto.js`, `erros.js`, `narracao.js`.
- Suítes verdes hoje: `test_idioma` (36), `test_vocabulario` (37), `test_erros` (9), `test_narracao` (48), `test_idioma_cliente` (16), `test_vocabulario_cliente` (40); regressão `test_modo_mestre` (336), `test_guilda` (54), `test_cenas_conversa` (57), `test_masmorra_sequenciada` (118), `test_instrumentos_bardo` (123), `test_reviver_mortos` (32), `test_editor_itens` (462), `test_bardo_espec` (101), `test_ladino_espec` (72), `test_paladino_espec` (47), `test_agarrao` (63).
- **`test_devorador` já tem 1 falha consistente** (`lagarto: tamanho 2x1 orientado`) e 2 intermitentes de dados aleatórios. Não são desta etapa; não tente consertá-las.

### Fatos medidos (não precisa re-verificar)

| forma | sites |
|---|---:|
| multilinha (texto na linha seguinte) | 110 |
| f-string que atravessa a linha | 1 |
| concatenação `prefix + f"…"` | 3 |
| `gm_say(gm(key))` | 6 chamadas / 30 frases (10 chaves × 3) |
| `gm_say(variavel)` | 6 |

Os 6 por variável, nominalmente:

| linha aprox. | expressão | tratamento |
|---|---|---|
| 26875 | `text = gm("victory") if victory else gm("defeat")` | resolvido pela Task 2 (pool) |
| 15747 | `log` de `_equip_into_slot`/`_equip_into_pair` | Task 5 |
| 26474 | `msg` de `_interromper_cancao(p, "Henrique foi incapacitado")` | Task 5 |
| 10902 | `motivo`, parâmetro de `_forcar_fim_de_turno` | Task 5 |
| 20802 | `msg` montado com `' e '.join(partes)` | Task 5, usando a lista da Task 1 |
| 26598 | `partes_txt` montado com `join` | Task 5, usando a lista da Task 1 |

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `server.py` | `_param_texto` junta listas; `gm()` devolve `T`; ~126 sites migrados; 3 produtores |
| `src/lang/strings.js` | 2 chaves do motor: `lista.separador`, `lista.ultimo` |
| `src/lang/narracao.js` | 30 chaves do pool + ~110 das narrações migradas |
| `src/i18n.js` | o `t()` do cliente junta listas |
| `tools/migrar_gm_say_ast.py` | **Criar.** Migrador por `ast`, uso único |
| `tools/test_narracao.py` | seções `[10]`–`[12]`; a `[2]` passa a cobrar |
| `tools/test_vocabulario_cliente.js` | junção de listas no cliente |

---

## Task 1: O motor aprende a juntar listas

**Arquivos:**
- Modificar: `server.py`, `src/lang/strings.js`, `src/i18n.js`, `tools/test_narracao.py`, `tools/test_vocabulario_cliente.js`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()` em `tools/test_narracao.py`:

```python
    print("\n[10] O motor junta listas com separador do idioma")
    S.LANG_STRINGS["narracao._teste_lista"] = {
        "pt": "Controla {quem}.", "en": "Controls {quem}."}
    def _lista(itens, lang):
        return S.t("narracao._teste_lista", lang, quem=itens)
    check("lista vazia não deixa separador solto", _lista([], "pt") == "Controla .")
    check("um item", _lista(["os animados"], "pt") == "Controla os animados.")
    check("dois itens em pt",
          _lista(["os animados", "o prisioneiro"], "pt")
          == "Controla os animados e o prisioneiro.")
    check("dois itens em en",
          _lista(["the minions", "the prisoner"], "en")
          == "Controls the minions and the prisoner.")
    check("três itens em pt",
          _lista(["a", "b", "c"], "pt") == "Controla a, b e c.")
    check("três itens em en",
          _lista(["a", "b", "c"], "en") == "Controls a, b and c.")
    # O elemento pode ser ele próprio um T — é o caso de nome de catálogo.
    check("elemento T é resolvido no idioma do leitor",
          _lista([S.T("cat.monstro.goblin.nome")], "en")
          == "Controls " + S.LANG_STRINGS["cat.monstro.goblin.nome"]["en"] + ".")
    S.LANG_STRINGS.pop("narracao._teste_lista", None)
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
python tools/test_narracao.py
```

Esperado: as checagens de 2 e 3 itens falham — hoje o `_param_texto` faz `str(valor)` numa lista e sai `"['a', 'b']"`.

- [ ] **Passo 3: Acrescentar as chaves do motor**

Em `src/lang/strings.js`, dentro do objeto `window.LANG_STRINGS`, junto das outras chaves de motor:

```js
  "lista.separador": { "pt": ", ",  "en": ", " },
  "lista.ultimo":    { "pt": " e ", "en": " and " },
```

- [ ] **Passo 4: Ensinar o `_param_texto` a juntar**

Em `server.py`, dentro de `_param_texto` (~linha 1195), **antes** do `return str(valor)`:

```python
    if isinstance(valor, (list, tuple)):
        # Lista de fragmentos: junta com separador do PRÓPRIO idioma (" e " ×
        # " and "). Cada elemento pode ser um T — é o caso de nome de catálogo.
        itens = [_param_texto(v, lang) for v in valor]
        if not itens:
            return ""
        if len(itens) == 1:
            return itens[0]
        return (t("lista.separador", lang).join(itens[:-1])
                + t("lista.ultimo", lang) + itens[-1])
```

- [ ] **Passo 5: Rodar**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py
```

Esperado: `IMPORT OK` e `55 passaram, 0 falharam`.

- [ ] **Passo 6: Escrever o teste do cliente**

Acrescentar em `tools/test_vocabulario_cliente.js`, logo antes da linha
`console.log("\n" + "=".repeat(62));`:

```js
console.log("\n[L] O t() do cliente junta listas");
DICT["teste.lista"] = { pt: "Controla {quem}.", en: "Controls {quem}." };
I18N.setLang("pt");
check("dois itens em pt",
      I18N.t("teste.lista", { quem: ["os animados", "o prisioneiro"] })
      === "Controla os animados e o prisioneiro.");
check("três itens em pt",
      I18N.t("teste.lista", { quem: ["a", "b", "c"] }) === "Controla a, b e c.");
I18N.setLang("en");
check("dois itens em en",
      I18N.t("teste.lista", { quem: ["the minions", "the prisoner"] })
      === "Controls the minions and the prisoner.");
check("lista vazia não deixa separador solto",
      I18N.t("teste.lista", { quem: [] }) === "Controls .");
I18N.setLang("pt");
```

- [ ] **Passo 7: Ensinar o `t()` do cliente**

Em `src/i18n.js`, dentro de `t()`, trocar a linha da substituição por:

```js
    if (params) {
      text = text.replace(PARAM, (m, k) => (k in params ? _valor(params[k]) : m));
    }
```

E acrescentar, **antes** de `function t(...)`:

```js
  // Gêmeo do _param_texto do server.py: um parâmetro pode ser uma LISTA de
  // fragmentos, que se junta com separador do próprio idioma (" e " × " and ").
  function _valor(v) {
    if (!Array.isArray(v)) return String(v);
    const itens = v.map(_valor);
    if (!itens.length)      return '';
    if (itens.length === 1) return itens[0];
    return itens.slice(0, -1).join(t('lista.separador'))
           + t('lista.ultimo') + itens[itens.length - 1];
  }
```

**Atenção:** `_valor` chama `t()` e `t()` chama `_valor` — a recursão termina porque
`lista.separador` e `lista.ultimo` não têm parâmetros. Não dê parâmetros a elas.

- [ ] **Passo 8: Rodar os testes do cliente**

```bash
node --check src/i18n.js && node tools/test_vocabulario_cliente.js && node tools/test_idioma_cliente.js
```

Esperado: `44 passaram, 0 falharam` e `16 passaram, 0 falharam`.

- [ ] **Passo 9: Fechar a limitação que a 4c registrou**

Em `server.py`, o site do Mestre dos Mortos (procure por `" e ".join(s["name"] for s in invocados)`):

```python
                nomes = [nome_criatura(s) for s in invocados]
```

e no `T(...)` daquela linha o parâmetro `nomes=nomes` passa a receber a lista. O
`_param_texto` junta e resolve cada nome no idioma de quem lê.

- [ ] **Passo 10: Rodar e commitar**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py && python tools/test_modo_mestre.py
```

Esperado: `IMPORT OK`, `55 passaram, 0 falharam` e `336 passaram, 0 falharam`.

```bash
git status --short
git add server.py src/lang/strings.js src/i18n.js tools/test_narracao.py tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): o motor junta listas com separador do idioma"
```

---

## Task 2: O pool `gm(key)`

**Arquivos:**
- Modificar: `server.py`, `src/lang/narracao.js`, `tools/test_narracao.py`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()`:

```python
    print("\n[11] O pool gm() sorteia uma vez e resolve por idioma")
    v = S.gm("intro")
    check("gm() devolve T", isinstance(v, S.T))
    check("a chave do pool existe no dicionário", v.key in S.LANG_STRINGS)
    check("a chave aponta para uma variante do GM",
          S.LANG_STRINGS[v.key]["pt"] in S.GM["intro"])
    # A regressão que mais importa: o sorteio é UM só. Dois jogadores em idiomas
    # diferentes têm de ler a MESMA variante — um sorteio por idioma seria
    # invisível num teste de uma conexão só.
    import asyncio, json as _json

    class RecWS:
        def __init__(self): self.sent = []
        async def send(self, data): self.sent.append(data)

    sala = S.GameRoom("TESTE_POOL")
    a, b = RecWS(), RecWS()
    sala.connections = {"g_pt": a, "g_en": b}
    S.LANG_BY_PID["g_pt"] = "pt"; S.LANG_BY_PID["g_en"] = "en"
    asyncio.run(sala.gm_say(S.gm("intro")))
    txt_pt = _json.loads(a.sent[-1])["text"]
    txt_en = _json.loads(b.sent[-1])["text"]
    i_pt = S.GM["intro"].index(txt_pt) if txt_pt in S.GM["intro"] else -1
    chave_en = next((k for k, val in S.LANG_STRINGS.items()
                     if k.startswith("narracao.gm.intro.") and val.get("en") == txt_en), "")
    i_en = int(chave_en.rsplit(".", 1)[1]) if chave_en else -2
    check("os dois leem a MESMA variante", i_pt == i_en and i_pt >= 0)
    for pid in ("g_pt", "g_en"):
        S.LANG_BY_PID.pop(pid, None)
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
python tools/test_narracao.py
```

Esperado: falha em "gm() devolve T" — hoje devolve `str`.

- [ ] **Passo 3: Semear as 30 chaves**

```python
# scratchpad/semear_pool.py — roda da raiz
import os, sys
RAIZ = r"C:\Users\RICARDO\Desktop\jogo tabuleiro"
sys.path.insert(0, os.path.join(RAIZ, "tools")); sys.path.insert(0, RAIZ)
import server as S, migrar_narracao as M

d = M.ler_existente()
n = 0
for chave, variantes in S.GM.items():
    for i, texto in enumerate(variantes):
        k = f"narracao.gm.{chave}.{i}"
        if k not in d:
            d[k] = {"pt": texto, "en": ""}; n += 1
M.escrever(d)
print("chaves do pool semeadas:", n)
```

```bash
python scratchpad/semear_pool.py
```

Esperado: `chaves do pool semeadas: 30`.

- [ ] **Passo 4: Trocar o `gm()`**

Em `server.py`, a função de uma linha `def gm(key): return random.choice(GM[key])` vira:

```python
def gm(key):
    """Uma variante sorteada do pool de narração de ambiente, como texto TARDIO.

    O sorteio acontece UMA vez e o idioma é resolvido no envio — senão dois
    jogadores na mesma sala leriam variantes diferentes do MESMO evento. O GM
    continua sendo a fonte do português; as chaves ficam no narracao.js."""
    return T(f"narracao.gm.{key}.{random.randrange(len(GM[key]))}")
```

- [ ] **Passo 5: Rodar**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py && python tools/test_modo_mestre.py && python tools/test_masmorra_sequenciada.py
```

Esperado: `IMPORT OK`, `60 passaram, 0 falharam`, `336 passaram, 0 falharam` e
`118 passou, 0 falhou`. A regressão importa porque `gm()` mudou de tipo de retorno e é
chamado em 6 lugares.

- [ ] **Passo 6: Commit**

```bash
git add server.py src/lang/narracao.js tools/test_narracao.py
git commit -m "feat(i18n): o pool de narracao de ambiente vira texto tardio"
```

---

## Task 3: O migrador por `ast`

**Arquivos:**
- Criar: `tools/migrar_gm_say_ast.py`
- Modificar (pelo script): `server.py`, `src/lang/narracao.js`

> **Antes de começar:** confirme com o usuário que ele pausou o `server.py`. Este passo
> reescreve spans espalhados pelo arquivo inteiro.

- [ ] **Passo 1: Escrever o script**

Criar `tools/migrar_gm_say_ast.py`:

```python
"""Migra para T("narracao.…") os gm_say que a etapa 4b-i deixou de fora:
multilinha, f-string que atravessa a linha e concatenação.

Roda da raiz:  python tools/migrar_gm_say_ast.py

Uso ÚNICO. Usa o módulo `ast`, não regex — e a etapa 4c provou por quê: um
`[^)]*` para o default de um `.get` aninhado deixou o arquivo sem parsear. Para
o `ast`, f-string multilinha, f-string de uma linha e concatenação implícita são
a MESMA árvore (JoinedStr), então as três formas saem pela mesma máquina.

A reescrita é por POSIÇÃO, de trás para frente, para os offsets não invalidarem;
toca só o span do argumento, deixando todo o resto byte-idêntico.
"""
import ast, io, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
from migrar_narracao import slug, nome_param, escrever, ler_existente

FONTE = os.path.join(RAIZ, "server.py")
RE_INTERP = re.compile(r"\{([^{}]+)\}")


def _partes(no, src):
    """(texto_logico, [(nome_param, expressao)]) de um JoinedStr/Constant/BinOp.
    Devolve None para qualquer forma que não seja só texto + interpolação."""
    if isinstance(no, ast.Constant) and isinstance(no.value, str):
        return no.value, []
    if isinstance(no, ast.BinOp) and isinstance(no.op, ast.Add):
        e = _partes(no.left, src); d = _partes(no.right, src)
        if e is None or d is None:
            return None
        return e[0] + d[0], e[1] + d[1]
    if not isinstance(no, ast.JoinedStr):
        return None
    texto, pares, usados = "", [], {}
    for v in no.values:
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            texto += v.value
        elif isinstance(v, ast.FormattedValue):
            expr = ast.get_source_segment(src, v.value)
            if expr is None or v.format_spec is not None or v.conversion not in (-1, 114):
                return None          # !r e format_spec ficam para a mão
            n = nome_param(expr)
            base, i = n, 2
            while n in usados and usados[n] != expr:
                n = f"{base}_{i}"; i += 1
            usados[n] = expr
            texto += "{" + n + "}"
            pares.append((n, expr))
        else:
            return None
    return texto, list(dict.fromkeys(pares))


def main():
    src = io.open(FONTE, encoding="utf-8").read()
    arvore = ast.parse(src)
    dic = ler_existente()
    por_chave = {k: v["pt"] for k, v in dic.items()}
    trocas, pulados = [], []

    for no in ast.walk(arvore):
        if not (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)
                and no.func.attr == "gm_say" and len(no.args) == 1):
            continue
        arg = no.args[0]
        # Já migrado (T(...)) ou vindo de variável/chamada: fora.
        if isinstance(arg, (ast.Name, ast.Call)):
            continue
        r = _partes(arg, src)
        if r is None:
            pulados.append(ast.get_source_segment(src, arg)[:60]); continue
        texto, pares = r
        ch = "narracao." + slug(RE_INTERP.sub("", texto))
        if ch in por_chave and por_chave[ch] != texto:
            base, i = ch, 2
            while f"{base}_{i}" in por_chave and por_chave[f"{base}_{i}"] != texto:
                i += 1
            ch = f"{base}_{i}"
        por_chave[ch] = texto
        dic[ch] = {"pt": texto, "en": dic.get(ch, {}).get("en", "")}
        args = ", ".join(f"{n}={e}" for n, e in pares)
        novo = f'T("{ch}"{", " + args if args else ""})'
        trocas.append((arg.lineno, arg.col_offset, arg.end_lineno, arg.end_col_offset, novo))

    linhas = src.split("\n")
    def off(l, c):
        return sum(len(x) + 1 for x in linhas[:l - 1]) + c
    saida = src
    for l1, c1, l2, c2, novo in sorted(trocas, key=lambda t: (t[0], t[1]), reverse=True):
        saida = saida[:off(l1, c1)] + novo + saida[off(l2, c2):]

    try:
        ast.parse(saida)
    except SyntaxError as e:
        print(f"❌ o resultado NÃO parseia ({e}) — nada foi escrito."); return 1

    io.open(FONTE, "w", encoding="utf-8", newline="\n").write(saida)
    escrever(dic)
    print(f"{len(trocas)} sites migrados.")
    print(f"{sum(1 for v in dic.values() if not v['en'])} chaves sem tradução.")
    if pulados:
        print(f"\n⚠️  {len(pulados)} forma(s) não reconhecida(s) — revise à mão:")
        for p in sorted(set(pulados))[:12]:
            print("   ", p.replace("\n", " ")[:70])
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Passo 2: Ensaiar sem gravar**

```bash
python -c "
import ast, io, sys; sys.path.insert(0,'tools'); sys.stdout.reconfigure(encoding='utf-8')
import migrar_gm_say_ast as M
src = io.open('server.py', encoding='utf-8').read()
n = 0
for no in ast.walk(ast.parse(src)):
    if (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)
            and no.func.attr == 'gm_say' and len(no.args) == 1
            and not isinstance(no.args[0], (ast.Name, ast.Call))):
        r = M._partes(no.args[0], src)
        if r and n < 3:
            print('TEXTO:', r[0][:90]); print('PARES:', r[1][:4]); print(); n += 1
"
```

Esperado: três frases legíveis, com os parâmetros batizados como `heroi`, `monstro`,
`alvo`, `dano`… Se algum texto sair truncado ou com `{` solto, **pare e reporte** — a
reconstrução é o coração do script.

- [ ] **Passo 3: Fazer backup e rodar**

```bash
cp server.py /tmp/server_antes_4bii.py && python tools/migrar_gm_say_ast.py
```

Esperado: em torno de `114 sites migrados.` e a lista de formas não reconhecidas (deve ser
curta ou vazia). Se o script relatar que não parseou, **nada foi escrito** — leia o erro e
reporte.

- [ ] **Passo 4: Conferir o diff estruturalmente**

```bash
python -c "
import re, subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')
d = subprocess.run(['git','diff','-U0','--','server.py'], capture_output=True,
                   text=True, encoding='utf-8').stdout
rem = [l[1:] for l in d.split(chr(10)) if l.startswith('-') and not l.startswith('---')]
add = [l[1:] for l in d.split(chr(10)) if l.startswith('+') and not l.startswith('+++')]
print('removidas:', len(rem), '| adicionadas:', len(add))
print('linhas + que NAO contem T(\"narracao.:',
      sum(1 for l in add if 'T(\"narracao.' not in l and l.strip()))
"
```

Esperado: menos linhas adicionadas que removidas (multilinha vira uma linha só), e
**zero** linhas adicionadas que não contenham `T("narracao.`. Qualquer outra coisa →
`git checkout server.py src/lang/narracao.js` e reporte.

- [ ] **Passo 5: Verificar import e regressão**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py && python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_editor_itens.py
```

Esperado: `IMPORT OK` e as quatro verdes (`336`, `54`, `462`). Se ficar vermelha, **pare e
reporte** em vez de tentar consertar — o script é reexecutável a partir do backup.

- [ ] **Passo 6: Commit**

```bash
git add server.py src/lang/narracao.js tools/migrar_gm_say_ast.py
git commit -m "feat(i18n): migra multilinha, concatenacao e f-string longa para T()"
```

---

## Task 4: Os nomes crus dos sites recém-migrados

**Arquivos:**
- Modificar (pelo script da 4c): `server.py`

Os 110 sites multilinha passavam `m['name']` cru. Agora que viraram `T(...)`, eles caem na
mesma superfície que o migrador de nomes da 4c já sabe varrer.

- [ ] **Passo 1: Medir antes**

```bash
python -c "
import io, re, sys, collections; sys.stdout.reconfigure(encoding='utf-8')
f = io.open('server.py', encoding='utf-8').read()
c = collections.Counter()
for m in re.finditer(r'T\(\s*\"narracao\.[^\"]+\"([^\n]*)\)', f):
    for a in re.finditer(r'(\w+)=([^,\)]+(?:\([^\)]*\))?)', m.group(1)):
        e = a.group(2).strip()
        if re.search(r'nome|name', e) and not e.startswith(('nome_criatura','nome_item','nome_cat')):
            c[e] += 1
print('cru:', sum(c.values())); print(c.most_common(12))
"
```

- [ ] **Passo 2: Rodar o migrador da 4c de novo**

```bash
python tools/migrar_nomes_narracao.py
```

Ele é reexecutável e tem as mesmas três travas (composta pulada, forma não reconhecida
intocada, `ast.parse` antes de gravar).

- [ ] **Passo 3: Conferir e rodar**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py && python tools/test_modo_mestre.py && python tools/test_masmorra_sequenciada.py
```

Esperado: `IMPORT OK` e as três verdes. Repita a medição do Passo 1: o que sobrar cru deve
ser só nome de JOGADOR (`p['name']`, `caster['name']`, …) e as formas que a 4c documentou
como fora das 8 famílias.

- [ ] **Passo 4: Commit**

```bash
git add server.py
git commit -m "feat(i18n): nomes de catalogo dos sites multilinha resolvidos"
```

---

## Task 5: Os produtores e o parâmetro

**Arquivos:**
- Modificar: `server.py`, `src/lang/narracao.js`, `tools/test_narracao.py`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()`:

```python
    print("\n[12] Produtores devolvem T, e continuam truthy")
    sala2 = S.GameRoom("TESTE_PROD")
    p_fake = {"name": "Thorin", "class_id": "warrior", "gear": {}, "bag": []}
    log = sala2._equip_into_slot(p_fake, {"id": "dagger", "name": "Adaga"}, "main_hand", "🗡️")
    check("_equip_into_slot devolve T", isinstance(log, S.T))
    check("o T da frase é truthy (o `if log:` do chamador continua valendo)", bool(log))
    check("frase vazia continua falsa", not bool(""))
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
python tools/test_narracao.py
```

Esperado: falha em "_equip_into_slot devolve T".

- [ ] **Passo 3: Migrar os dois produtores**

Em `server.py`, o fim de `_equip_into_slot`:

```python
        return T("narracao.equipou", log_emoji=log_emoji, heroi=p["name"],
                 item=nome_item(item))
```

Note o `nome_item`: o produtor interpola nome de item, então já entra resolvido, sem
precisar de uma segunda passada. Faça o mesmo no `return` de `_equip_into_pair`, que tem a
frase equivalente.

Em `src/lang/narracao.js`:

```js
  "narracao.equipou": {
    "pt": "{log_emoji} **{heroi}** equipou **{item}**!",
    "en": "{log_emoji} **{heroi}** equipped **{item}**!"
  },
```

Em `_interromper_cancao`, o `return` vira `T(...)` do mesmo jeito, e o parâmetro `motivo`
passa a receber um `T` do chamador — o literal `"Henrique foi incapacitado"` vira
`T("narracao.henrique_foi_incapacitado")`, com a chave:

```js
  "narracao.henrique_foi_incapacitado": {
    "pt": "Henrique foi incapacitado", "en": "Henrique was incapacitated"
  },
```

- [ ] **Passo 4: Migrar os chamadores de `_forcar_fim_de_turno`**

```bash
grep -n "_forcar_fim_de_turno(" server.py
```

Cada chamador passa um `motivo` literal em português. Troque por `T("narracao.…")` e crie
as chaves. O `if motivo:` dentro da função continua valendo — o `T` é truthy.

- [ ] **Passo 5: Migrar as duas frases montadas por pedaços**

O site do turno de controle (procure por `' e '.join(partes)`) vira:

```python
                msg = T("narracao.turno_de_controle_de_mova_e_encerre",
                        heroi=p["name"], partes=partes)
```

com `partes` sendo a **lista** de fragmentos (cada um já um `T`), que a Task 1 ensinou o
motor a juntar.

O site do objetivo cumprido monta a frase em três pedaços opcionais:

```python
        partes = [f"⭐ Objetivo **{nome}** cumprido!"]
        if xp_share:   partes.append(f"+{xp_share} XP")
        if ouro_share: partes.append(f"+{ouro_share} ouro")
        partes_txt = " ".join(partes[:1]) + (" " + ", ".join(partes[1:]) + " a cada heroi." if len(partes) > 1 else "")
        if itens_nomes:
            partes_txt += " 🎁 Recompensa largada: " + ", ".join(itens_nomes) + "."
        await self.gm_say(partes_txt)
```

Vira **uma chave com slots**, no padrão do nome de instrumento — cada slot vazio quando a
parte não existe, e o espaço embutido no slot para não sobrar espaço solto:

```python
        ganhos = []
        if xp_share:   ganhos.append(T("narracao.obj_xp", n=xp_share))
        if ouro_share: ganhos.append(T("narracao.obj_ouro", n=ouro_share))
        await self.gm_say(T(
            "narracao.objetivo_cumprido",
            nome=nome,
            ganhos=T("narracao.obj_ganhos", lista=ganhos) if ganhos else "",
            itens=T("narracao.obj_itens", lista=[nome_item(i) for i in itens_obj])
                  if itens_obj else ""))
```

```js
  "narracao.objetivo_cumprido": {
    "pt": "⭐ Objetivo **{nome}** cumprido!{ganhos}{itens}",
    "en": "⭐ Objective **{nome}** complete!{ganhos}{itens}"
  },
  "narracao.obj_ganhos": { "pt": " {lista} a cada herói.", "en": " {lista} each." },
  "narracao.obj_itens":  { "pt": " 🎁 Recompensa largada: {lista}.",
                           "en": " 🎁 Reward dropped: {lista}." },
  "narracao.obj_xp":     { "pt": "+{n} XP",   "en": "+{n} XP" },
  "narracao.obj_ouro":   { "pt": "+{n} ouro", "en": "+{n} gold" },
```

**Atenção:** hoje o código junta os nomes de item já como strings (`itens_nomes`). Passe a
lista dos **dicts** de item (`itens_obj`) e resolva com `nome_item`, para o nome sair no
idioma do leitor — do contrário a frase fica em inglês com os itens em português, o mesmo
defeito que a 4c corrigiu.

- [ ] **Passo 6: Rodar**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py && python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_bardo_espec.py
```

Esperado: `IMPORT OK` e as quatro verdes.

- [ ] **Passo 7: Commit**

```bash
git add server.py src/lang/narracao.js tools/test_narracao.py
git commit -m "feat(i18n): produtores de narracao devolvem texto tardio"
```

---

## Task 6: Traduzir as 30 frases do pool

**Arquivos:**
- Modificar: `src/lang/narracao.js` (só a coluna `en`)

Estas são a **voz autoral do mestre**, não texto funcional. Mantenha o tom épico e o ritmo
do português; se o `pt` termina em reticências, o `en` também. Vão num commit próprio para
o autor revisar de uma vez.

- [ ] **Passo 1: Listar**

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.stdout.reconfigure(encoding='utf-8')
import migrar_narracao as M
d = M.ler_existente()
for k in sorted(k for k in d if k.startswith('narracao.gm.')):
    print(k, '||', d[k]['pt'][:100])
"
```

- [ ] **Passo 2: Traduzir**

Mesmo método das etapas anteriores: um script no scratchpad com o dicionário `TRAD`,
`assert` de que a chave existe e de que ainda não tem `en`, e `M.escrever(d)` no fim.

- [ ] **Passo 3: Conferir e commitar**

```bash
python tools/test_narracao.py && python tools/test_erros.py
```

Esperado: verdes. A seção `[2]` do `test_erros.py` compara os `{parâmetros}` entre `pt` e
`en` de todas as chaves.

```bash
git add src/lang/narracao.js
git commit -m "feat(i18n): traduz a narracao de ambiente do mestre"
```

---

## Task 7: Traduzir as narrações migradas

**Arquivos:**
- Modificar: `src/lang/narracao.js` (só a coluna `en`)

**O registro é a voz do mestre contando o que acontece** — presente, direta, com energia.
Regras que valem mais que estilo: parâmetros são sagrados (mesmo nome no `pt` e no `en`);
emojis e `**negrito**` passam intactos; números, dados (`2d6`) e CDs são sagrados; nomes de
habilidade e item seguem o `en` das chaves `cat.*` em `src/lang/catalogo.js`.

**Glossário:** ação principal = main action, ação bônus = bonus action, recarga = cooldown,
rodada = round, turno = turn, alcance = range, 🍖 fome = hunger, 💧 sede = thirst, save =
saving throw, CD = DC, vantagem/desvantagem = advantage/disadvantage, Reflexos/Fortitude/
Vontade = Reflex/Fortitude/Will, servo = minion, CA = AC, ND = CR.

- [ ] **Passo 1: Traduzir a primeira metade**

Liste o que falta e pegue metade:

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.stdout.reconfigure(encoding='utf-8')
import migrar_narracao as M
d = M.ler_existente(); f = sorted(k for k, v in d.items() if not v['en'])
print(len(f), 'sem traducao'); print(chr(10).join(f[:len(f)//2]))
"
```

Aplique por script no scratchpad, como nas etapas anteriores.

```bash
git add src/lang/narracao.js
git commit -m "feat(i18n): traduz a primeira metade da narracao restante"
```

- [ ] **Passo 2: Traduzir o restante e conferir que zerou**

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.stdout.reconfigure(encoding='utf-8')
import migrar_narracao as M
d = M.ler_existente(); f = [k for k, v in d.items() if not v['en']]
print(len(f), 'ainda sem traducao (esperado 0)')
"
```

```bash
git add src/lang/narracao.js
git commit -m "feat(i18n): traduz o restante da narracao"
```

---

## Task 8: A varredura estática vira teste, e a verificação final

**Arquivos:**
- Modificar: `tools/test_narracao.py`, `CLAUDE.md`

- [ ] **Passo 1: A seção `[3]` passa a cobrar**

Em `tools/test_narracao.py`, a seção que hoje só **relata** os fora-de-escopo vira
cobrança:

```python
    print("\n[3] Nada de narração em português sobrou no servidor")
    linhas = FONTE.split("\n")
    multi = sum(1 for l in linhas
                if l.strip().endswith("gm_say(") and "async def" not in l)
    pool = len(re.findall(r"gm_say\(gm\(", FONTE))
    conc = sum(1 for l in linhas if "gm_say(" in l and "+" in l
               and not re.search(r'gm_say\((f?"|T\()', l) and "async def" not in l)
    check(f"nenhum gm_say multilinha ({multi})", multi == 0)
    check(f"nenhum gm_say(gm(...)) direto ({pool})", pool == 0)
    check(f"nenhuma concatenação em gm_say ({conc})", conc == 0)
```

- [ ] **Passo 2: Rodar tudo**

```bash
python tools/test_idioma.py && python tools/test_vocabulario.py && python tools/test_erros.py && python tools/test_narracao.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: `36`, `37`, `9`, o novo total, `16` e `44`, zero falhando.

- [ ] **Passo 3: Regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_cenas_conversa.py && python tools/test_masmorra_sequenciada.py && python tools/test_instrumentos_bardo.py && python tools/test_editor_itens.py && python tools/test_reviver_mortos.py && python tools/test_bardo_espec.py
```

Esperado: `336`, `54`, `57`, `118`, `123`, `462`, `32` e `101`, zero falhando.

- [ ] **Passo 4: Prova ponta a ponta, com o servidor REINICIADO**

Confirme com o usuário antes de subir ou derrubar qualquer servidor; se a porta 8765
estiver ocupada, é dele. Com um servidor novo no ar, entre com dois clientes na mesma
sala, um em cada idioma, e confirme numa **linha de combate** (multilinha migrada) e na
**narração de abertura** (pool) que cada um lê no seu idioma, e que a variante do pool é a
**mesma** para os dois.

- [ ] **Passo 5: Documentar no `CLAUDE.md`**

Acrescentar ao fim um bloco `>` no padrão dos anteriores, cobrindo: o migrador por `ast` e
por que não regex; o pool com sorteio único; a junção de listas no motor (e que ela fechou
a limitação do `nomes` da 4c); os produtores devolvendo `T`; e o que **continua em
português** (conteúdo autoral e a interface do cliente, etapa 5).

- [ ] **Passo 6: Commit final**

```bash
git add CLAUDE.md tools/test_narracao.py
git commit -m "docs(i18n): documenta a narracao restante do servidor"
```

---

## Fora deste plano (registrado, não esquecido)

- **Etapa 5** — a interface do cliente (~1.000 strings). É o que sobra do idioma.
- **Conteúdo autoral** — masmorras, campanhas, falas de NPC, itens e monstros do editor
  seguem no idioma em que o autor os escreveu, por definição.
- As **6 passagens de nome** que a 4c documentou como fora das 8 famílias de catálogo
  (nome de ataque em tupla literal, rótulo de status, nome de habilidade por parâmetro,
  `weapon_name`, nome de cidade). O `nomes` sai dessa lista na Task 1.
- **Maldições** não são família de catálogo; um `cat.maldicao.*` seria etapa própria.
