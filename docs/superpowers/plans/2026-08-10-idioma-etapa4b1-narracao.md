# Etapa 4b-i do idioma — Narração do servidor (lote mecânico) — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-10-idioma-etapa4b1-narracao-design.md`

**Objetivo:** Migrar para `T(...)` e traduzir os 390 `gm_say` mecânicos — os que cabem inteiros numa linha, no formato `gm_say("…")` ou `gm_say(f"…")`.

**Arquitetura:** Um script determinístico faz a migração inteira, inclusive o batismo dos parâmetros: identificador simples vira ele mesmo, `X['name']` vira `X`, o resto vira slug da expressão, com uma tabela mínima de apelidos (`p`→`heroi`, `m`→`monstro`). A chave é o slug do texto **sem** as interpolações, então a dedup cai de graça. O dicionário vive em `src/lang/narracao.js`, mantido à mão depois da migração.

**Stack:** Python 3 (servidor e script), JavaScript vanilla (dicionário do cliente), testes `tools/test_*.py`.

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** — regras obrigatórias do projeto.
- **O usuário edita `server.py` e outros em paralelo, e sobe/derruba um servidor na porta 8765.** Antes de cada commit rode `git status` e use só os caminhos do passo — nunca `git add -A` nem `git add .`. Não mate processo nenhum.
- **Etapas 1–4a (prontas):** `T("chave", **params)` marca texto não traduzido; `broadcast`/`send_to`/`err` o resolvem no idioma de cada conexão pelo `default` do `json.dumps`; `t()` resolve parâmetro que é ele próprio um `T`; `nome_de(familia, id)` devolve nome de catálogo como texto tardio. O `T` **se comporta como o texto em português** para quem o trate como string — não mude isso, é o que mantém 24 mocks de teste funcionando. O carregador funde todos os `.js` de `src/lang/` (hoje `strings.js`, `catalogo.js`, `erros.js`).
- **O `tools/migrar_erros.py`** da etapa 4a é o modelo direto deste script, e o `slug()` dele é reusado aqui por import.
- Suítes verdes: `test_idioma.py` (36), `test_vocabulario.py` (37), `test_erros.py` (9), `test_idioma_cliente.js` (16), `test_vocabulario_cliente.js` (29); regressão `test_modo_mestre.py` (336), `test_guilda.py` (54), `test_cenas_conversa.py` (57), `test_masmorra_sequenciada.py` (118).

### Fatos medidos (não precisa re-verificar)

| Forma | Sites | Neste escopo? |
|---|---:|---|
| `gm_say(f"…")` ou `gm_say("…")` fechando na MESMA linha | 390 | **sim** |
| f-string que **começa** na linha do `gm_say(` e continua na seguinte | 28 | não — 4b-ii |
| `gm_say(` com o texto começando na linha seguinte | 109 | não — 4b-ii |
| `gm_say(prefix + f"…")` | 3 | não |
| `gm_say(variavel)` | 7 | não |
| `gm_say(gm("chave"))` — pool de 30 variantes | 6 | não |

764 interpolações nas 399 f-strings, em 207 expressões distintas. **300 são identificador simples.** As mais comuns: `p['name']` 144×, `m['name']` 87×, `alvo['name']` 41×, `caster['name']` 17×, `item['name']` 14×, `target['name']` 12×.

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `src/lang/narracao.js` | **Criar.** Dicionário da narração, `window.LANG_NARRACAO`. |
| `index.html` | Carrega `src/lang/narracao.js` depois de `erros.js`. |
| `server.py` | 390 `gm_say` viram `T(...)`. |
| `tools/migrar_narracao.py` | **Criar.** Script de uso único. |
| `tools/test_narracao.py` | **Criar.** Os 5 testes do spec. |

---

## Task 1: Fundação — dicionário e teste

**Arquivos:**
- Criar: `src/lang/narracao.js`, `tools/test_narracao.py`
- Modificar: `index.html`

- [ ] **Passo 1: Escrever o teste que falha**

Criar `tools/test_narracao.py`:

```python
"""Narração do servidor (etapa 4b-i) — migração para T() e tradução.
Roda da raiz: python tools/test_narracao.py"""
import io, json, os, re, sys
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

FONTE = io.open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
# EXATAMENTE o mesmo padrão que o script de migração reconhece. Se o teste
# cobrasse mais do que o script sabe fazer, ficaria vermelho por trabalho que
# ninguém combinou.
RE_UMA_LINHA = re.compile(r'gm_say\((f?)"([^"]*)"\)')


def _rodar_verificacoes():
    print("\n[1] Dicionário de narração carregado")
    check("existe src/lang/narracao.js",
          os.path.isfile(os.path.join(RAIZ, "src", "lang", "narracao.js")))
    check("o servidor funde as chaves de narração",
          any(k.startswith("narracao.") for k in S.LANG_STRINGS))

    print("\n[2] Migração do lote mecânico")
    restantes = RE_UMA_LINHA.findall(FONTE)
    check(f"nenhum gm_say de uma linha com literal sobrou ({len(restantes)})",
          not restantes)
    for _, t in restantes[:6]:
        print("     sobrou:", t[:70])

    print("\n[3] Fora de escopo — contagem, não cobrança")
    # Estes seguem em português de propósito; são a etapa 4b-ii. O teste os
    # RELATA para o placar ficar visível, e nunca falha por causa deles.
    linhas = FONTE.split("\n")
    multi = sum(1 for l in linhas
                if l.strip().endswith("gm_say(") and "async def" not in l)
    pool = len(re.findall(r"gm_say\(gm\(", FONTE))
    conc = sum(1 for l in linhas if "gm_say(" in l and "+" in l
               and not re.search(r'gm_say\((f?"|T\()', l) and "async def" not in l)
    print(f"     multilinha: {multi} | pool gm(): {pool} | concatenação: {conc}")
    check("relatório de fora-de-escopo emitido", True)

    print("\n[4] Chaves usadas e chaves sem uso")
    usadas = set(re.findall(r'T\(\s*"(narracao\.[^"]+)"', FONTE))
    faltando = sorted(k for k in usadas if k not in S.LANG_STRINGS)
    check(f"nenhuma chave de narração órfã (usadas: {len(usadas)})", not faltando)
    if faltando:
        print("     órfãs:", ", ".join(faltando[:8]))
    no_dic = {k for k in S.LANG_STRINGS if k.startswith("narracao.")}
    sem_uso = sorted(no_dic - usadas)
    check(f"relatório de chaves sem uso emitido ({len(sem_uso)})", True)
    if sem_uso:
        print("     sem uso:", ", ".join(sem_uso[:8]))


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Narração do servidor (etapa 4b-i)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
python tools/test_narracao.py
```

Esperado: `4 passaram, 2 falharam` — falta o arquivo `narracao.js` e sobram os 390 literais. (A chave `narracao.abre_porta` já existe no `strings.js` desde a etapa 1, então a segunda checagem de `[1]` já passa.)

- [ ] **Passo 3: Criar o dicionário**

Criar `src/lang/narracao.js`:

```js
// NARRAÇÃO do mestre — o log que conta o que acontece na partida
// (etapa 4b-i do idioma).
//
// Como o erros.js e ao contrário do catalogo.js, é mantido À MÃO: depois da
// migração o server.py não contém mais o texto em português, só a chave, então
// não há de onde gerar de novo. A chave é o slug do texto SEM as interpolações.
window.LANG_NARRACAO = {};
Object.assign(window.LANG_STRINGS, window.LANG_NARRACAO);
```

- [ ] **Passo 4: Carregar no `index.html`**

Em `index.html`, na linha que faz `document.write` dos scripts síncronos, acrescentar após o de `erros.js`:

```js
document.write('<script src="src/lang/narracao.js?v='+v+'"><\/script>');
```

A ordem importa: o arquivo termina com `Object.assign(window.LANG_STRINGS, …)` e precisa que o `strings.js` já tenha criado esse objeto.

- [ ] **Passo 5: Rodar os testes**

```bash
python tools/test_narracao.py && python tools/test_erros.py && python tools/test_idioma.py
```

Esperado: `5 passaram, 1 falharam` (só a migração falta), `9 passaram, 0 falharam` e `36 passaram, 0 falharam`.

- [ ] **Passo 6: Commit**

```bash
git add src/lang/narracao.js index.html tools/test_narracao.py
git commit -m "feat(i18n): dicionario de narracao e teste do lote mecanico"
```

---

## Task 2: Script de migração

**Arquivos:**
- Criar: `tools/migrar_narracao.py`
- Modificar (pelo script): `server.py`, `src/lang/narracao.js`

- [ ] **Passo 1: Escrever o script**

Criar `tools/migrar_narracao.py`:

```python
"""Migra os gm_say MECÂNICOS do server.py para T("narracao.…").

Roda da raiz:  python tools/migrar_narracao.py

Uso ÚNICO. Cobre só as duas formas de UMA LINHA: gm_say("…") e gm_say(f"…").
Multilinha, concatenação, variável e o pool gm(...) ficam de fora de propósito
— são a etapa 4b-ii, e cada um pede um tratamento próprio.

Depois de rodar, o server.py não tem mais o texto em português, só a chave, e
src/lang/narracao.js passa a ser mantido à mão.
"""
import io, json, os, re, sys, unicodedata
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "tools"))
from migrar_erros import slug          # mesma regra de slug da etapa 4a

FONTE = os.path.join(RAIZ, "server.py")
DICIONARIO = os.path.join(RAIZ, "src", "lang", "narracao.js")

RE_UMA_LINHA = re.compile(r'gm_say\((f?)"([^"]*)"\)')
RE_INTERP = re.compile(r"\{([^{}]+)\}")
RE_SUBSCRITO_NOME = re.compile(r"""^(\w+)\[['"]name['"]\]$""")

# Só os dois nomes opacos e mais frequentes (231 das 764 interpolações). O resto
# já é legível pela regra: alvo['name'] vira {alvo}, item['name'] vira {item}.
APELIDOS = {"p": "heroi", "m": "monstro"}


def nome_param(expr):
    """Batismo determinístico, em três degraus."""
    e = expr.strip()
    if re.fullmatch(r"\w+", e):
        return APELIDOS.get(e, e)
    m = RE_SUBSCRITO_NOME.match(e)
    if m:
        return APELIDOS.get(m.group(1), m.group(1))
    return slug(e, 24) or "valor"


def preparar(texto):
    """Devolve (texto_com_nomes, [(nome, expressao)], colisoes).
    O texto sai com {expressao} trocado por {nome}, pronto para o dicionário."""
    exprs = RE_INTERP.findall(texto)
    usados = {}      # nome -> expressao
    nomes = []
    colisoes = []
    for e in exprs:
        n = nome_param(e)
        if n in usados and usados[n] != e:
            base, i = n, 2
            while f"{base}_{i}" in usados and usados[f"{base}_{i}"] != e:
                i += 1
            colisoes.append((base, usados[base], e))
            n = f"{base}_{i}"
        usados[n] = e
        nomes.append(n)
    it = iter(nomes)
    novo = RE_INTERP.sub(lambda m: "{" + next(it) + "}", texto)
    # dict.fromkeys preserva a ordem e remove o par repetido (mesma expressão
    # usada duas vezes na frase entra uma vez só na chamada).
    pares = list(dict.fromkeys(zip(nomes, exprs)))
    return novo, pares, colisoes


def chave_de(texto_sem_interp):
    return "narracao." + slug(texto_sem_interp)


def ler_existente():
    try:
        raw = io.open(DICIONARIO, encoding="utf-8").read()
        m = re.search(r"^\s*window\.LANG_NARRACAO\s*=", raw, re.MULTILINE)
        return json.loads(raw[raw.index("{", m.end()):raw.rindex("}") + 1])
    except Exception:
        return {}


def escrever(dicionario):
    corpo = json.dumps(dicionario, ensure_ascii=False, indent=2, sort_keys=True)
    with io.open(DICIONARIO, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "// NARRAÇÃO do mestre — o log que conta o que acontece na partida\n"
            "// (etapa 4b-i do idioma).\n"
            "//\n"
            "// Mantido À MÃO: depois da migração o server.py não contém mais o texto\n"
            "// em português, só a chave. A chave é o slug do texto SEM as interpolações.\n"
            "window.LANG_NARRACAO = " + corpo + ";\n"
            "Object.assign(window.LANG_STRINGS, window.LANG_NARRACAO);\n")


def main():
    fonte = io.open(FONTE, encoding="utf-8").read()
    dic = ler_existente()
    por_chave = {}          # chave -> texto_pt (para detectar colisão de chave)
    colisoes_param = []
    colisoes_chave = []
    sites = [0]

    def troca(m):
        texto = m.group(2)
        novo_texto, pares, col = preparar(texto)
        colisoes_param.extend(col)
        # A chave vem do texto SEM as interpolações: mais legível.
        sem_interp = RE_INTERP.sub("", texto)
        ch = chave_de(sem_interp)
        if ch in por_chave and por_chave[ch] != novo_texto:
            colisoes_chave.append((ch, por_chave[ch], novo_texto))
            base, i = ch, 2
            while f"{base}_{i}" in por_chave and por_chave[f"{base}_{i}"] != novo_texto:
                i += 1
            ch = f"{base}_{i}"
        por_chave[ch] = novo_texto
        entrada = dic.get(ch) or {}
        dic[ch] = {"pt": novo_texto, "en": entrada.get("en", "")}
        sites[0] += 1
        args = ", ".join(f"{n}={e}" for n, e in pares)
        return f'gm_say(T("{ch}"{", " + args if args else ""}))'

    novo = RE_UMA_LINHA.sub(troca, fonte)
    with io.open(FONTE, "w", encoding="utf-8", newline="\n") as f:
        f.write(novo)
    escrever(dic)

    print(f"{sites[0]} sites migrados → {len(por_chave)} chaves distintas.")
    print(f"{sum(1 for v in dic.values() if not v['en'])} sem tradução para o inglês.")
    if colisoes_param:
        print(f"\n⚠️  {len(colisoes_param)} colisão(ões) de PARÂMETRO dentro de uma frase:")
        for b, a, c in colisoes_param[:10]:
            print(f"   {b}: {a}  ×  {c}")
    if colisoes_chave:
        print(f"\n⚠️  {len(colisoes_chave)} colisão(ões) de CHAVE — revise:")
        for ch, a, b in colisoes_chave[:10]:
            print(f"   {ch}\n      {a[:64]}\n      {b[:64]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Passo 2: Ensaiar o batismo antes de tocar no arquivo**

Antes de rodar a migração, confira que a regra de nome faz o que se espera:

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.stdout.reconfigure(encoding='utf-8')
import migrar_narracao as M
for e in [\"p['name']\", \"m['name']\", \"alvo['name']\", 'dano', 'dur', \"item['name']\", 'alvo.get(\'name\')']:
    print(f'  {e:<24} -> {M.nome_param(e)}')
t, pares, col = M.preparar(\"🚪 **{p['name']}** ataca **{alvo['name']}** por {dano}!\")
print(); print('  texto :', t); print('  pares :', pares); print('  chave :', M.chave_de('🚪 **** ataca **** por !'))
"
```

Esperado: `p['name'] -> heroi`, `m['name'] -> monstro`, `alvo['name'] -> alvo`, `dano -> dano`; o texto vira `🚪 **{heroi}** ataca **{alvo}** por {dano}!` e a chave `narracao.ataca_por`.

Se algum desses não bater, **pare e reporte** — a regra de batismo é o coração do script.

- [ ] **Passo 3: Rodar a migração**

```bash
python tools/migrar_narracao.py
```

Esperado: `390 sites migrados → N chaves distintas.` com N em torno de 350–385 (há repetição, mas menos que nos erros). Colisões de parâmetro ou de chave são **relatadas**; se aparecerem, leia-as antes de seguir e reporte se alguma parecer errada — o script já resolve com sufixo, o relatório é para revisão.

- [ ] **Passo 4: Conferir o diff estruturalmente, não por amostragem**

```bash
python -c "
import subprocess, re, sys
sys.stdout.reconfigure(encoding='utf-8')
d = subprocess.run(['git','diff','-U0','--','server.py'], capture_output=True, text=True, encoding='utf-8').stdout
rem = [l[1:] for l in d.split('\n') if l.startswith('-') and not l.startswith('---')]
add = [l[1:] for l in d.split('\n') if l.startswith('+') and not l.startswith('+++')]
print('linhas removidas:', len(rem), '| adicionadas:', len(add))
RE_OLD = re.compile(r'gm_say\(f?\"[^\"]*\"\)')
RE_NEW = re.compile(r'gm_say\(T\(\"narracao\.[^\"]+\"(, .*?)?\)\)')
anom = 0
for a, b in zip(rem, add):
    if RE_OLD.sub('§', a) != RE_NEW.sub('§', b):
        anom += 1
        if anom <= 5: print('  ANOMALIA:\n    -', a.strip()[:90], '\n    +', b.strip()[:90])
print('anomalias:', anom, '(0 = so trocas de narracao)')
"
```

Esperado: mesmo número de linhas removidas e adicionadas, e **0 anomalias**. Se houver qualquer anomalia, **pare e reverta** (`git checkout server.py src/lang/narracao.js`) e reporte o que viu — o script é reexecutável, nada se perde.

- [ ] **Passo 5: Verificar que o servidor importa e a regressão está verde**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py && python tools/test_modo_mestre.py && python tools/test_guilda.py
```

Esperado: `IMPORT OK`, `8 passaram, 0 falharam`, `336 passaram, 0 falharam` e `54 passaram, 0 falharam`.

A regressão é obrigatória: o script tocou centenas de linhas do arquivo central do jogo. Se ficar vermelha, **pare e reporte** em vez de tentar consertar.

- [ ] **Passo 5b: Acrescentar a prova ponta a ponta ao teste**

Acrescentar ao fim de `_rodar_verificacoes()` em `tools/test_narracao.py`:

```python
    print("
[5] Uma narração migrada chega em dois idiomas, pelo broadcast real")
    import asyncio

    class RecWS:
        def __init__(self): self.sent = []
        async def send(self, data): self.sent.append(data)

    chave = next((k for k, v in S.LANG_STRINGS.items()
                  if k.startswith("narracao.") and v.get("en")), None)
    if not chave:
        check("há ao menos uma narração traduzida para provar", False)
    else:
        sala = S.GameRoom("TESTE_NARR")
        ws_pt, ws_en = RecWS(), RecWS()
        sala.connections = {"n_pt": ws_pt, "n_en": ws_en}
        S.LANG_BY_PID["n_pt"] = "pt"
        S.LANG_BY_PID["n_en"] = "en"
        asyncio.run(sala.gm_say(S.T(chave)))
        pt = json.loads(ws_pt.sent[-1])["text"]
        en = json.loads(ws_en.sent[-1])["text"]
        check("sai em português para quem está em pt", pt == S.LANG_STRINGS[chave]["pt"])
        check("sai em inglês para quem está em en", en == S.LANG_STRINGS[chave]["en"])
        for pid in ("n_pt", "n_en"):
            S.LANG_BY_PID.pop(pid, None)
```

Isso leva o teste de 6 para **8** checagens.

- [ ] **Passo 6: Commit**

```bash
git add server.py src/lang/narracao.js tools/migrar_narracao.py tools/test_narracao.py
git commit -m "feat(i18n): migra a narracao mecanica do servidor para T()"
```

---

## Task 3: Traduzir a narração

**Arquivos:**
- Modificar: `src/lang/narracao.js` (só a coluna `en`)

**O registro é diferente do dos erros.** Narração é a **voz do mestre** contando o que acontece — presente, direta, com energia:

- `**{heroi}** strikes **{alvo}** for **{dano}** damage!` — não "A hit has been performed."
- Se o português termina em `!`, o inglês também. A pontuação de entusiasmo é parte do tom.

**Regras que valem mais que estilo:**

- **Parâmetros são sagrados.** Se o `pt` tem `{heroi}`, o `en` tem `{heroi}`, com o nome idêntico. Um teste compara os dois conjuntos e falha se divergirem; e se você perder um, o jogador lê `{heroi}` cru no log.
- **Emojis e `**negrito**` passam intactos.** Abrem quase toda narração e são formatação.
- **Números, dados (`2d6`), CDs e valores entre `**` são sagrados.**
- **Nomes de habilidade e item** seguem o `"en"` das chaves `cat.*.nome` em `src/lang/catalogo.js`. Consulte quando a frase citar um.

**Glossário** (das etapas 2 a 4a): ação principal = main action, ação bônus = bonus action, recarga = cooldown, rodada = round, turno = turn, alcance = range, 🍖 fome = hunger, 💧 sede = thirst, save = saving throw, CD = DC, vantagem/desvantagem = advantage/disadvantage, Reflexos/Fortitude/Vontade = Reflex/Fortitude/Will, servo = minion.

- [ ] **Passo 1: Traduzir a primeira metade**

Liste o que falta e pegue a primeira metade:

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.stdout.reconfigure(encoding='utf-8')
import migrar_narracao as M
d=M.ler_existente(); f=sorted(k for k,v in d.items() if not v['en'])
print(len(f),'sem traducao'); print('\n'.join(f[:len(f)//2]))
"
```

Aplique por script, para o formato sair idêntico ao que o migrador escreve:

```python
# scratchpad/traduzir_narracao_1.py
import os, sys
RAIZ = r"C:\Users\RICARDO\Desktop\jogo tabuleiro"
sys.path.insert(0, os.path.join(RAIZ, "tools")); sys.path.insert(0, RAIZ)
import migrar_narracao as M

TRAD = {
    "narracao.abre_uma_porta": "🚪 **{heroi}** opens a door!",
    # ... a primeira metade
}

d = M.ler_existente()
faltando = [k for k in TRAD if k not in d]
assert not faltando, f"chaves inexistentes: {faltando}"
ja = [k for k in TRAD if d[k]["en"]]
assert not ja, f"ja tinham traducao (nao mexa): {ja}"
for k, en in TRAD.items():
    d[k]["en"] = en
M.escrever(d)
print("aplicadas:", len(TRAD))
```

- [ ] **Passo 2: Commit**

```bash
git add src/lang/narracao.js
git commit -m "feat(i18n): traduz a primeira metade da narracao"
```

- [ ] **Passo 3: Traduzir o restante**

Mesmo método, com as chaves que sobraram:

```python
# scratchpad/traduzir_narracao_2.py
import os, sys
RAIZ = r"C:\Users\RICARDO\Desktop\jogo tabuleiro"
sys.path.insert(0, os.path.join(RAIZ, "tools")); sys.path.insert(0, RAIZ)
import migrar_narracao as M

TRAD = {
    "narracao.exemplo": "Example!",
    # ... o restante
}

d = M.ler_existente()
faltando = [k for k in TRAD if k not in d]
assert not faltando, f"chaves inexistentes: {faltando}"
ja = [k for k in TRAD if d[k]["en"]]
assert not ja, f"ja tinham traducao (nao mexa): {ja}"
for k, en in TRAD.items():
    d[k]["en"] = en
M.escrever(d)
print("aplicadas:", len(TRAD))
```

Conferir que zerou:

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.stdout.reconfigure(encoding='utf-8')
import migrar_narracao as M
d=M.ler_existente(); f=[k for k,v in d.items() if not v['en']]
print(len(f),'ainda sem traducao (esperado 0)'); print('\n'.join(f[:10]))
"
```

- [ ] **Passo 4: Rodar o teste de paridade**

```bash
python tools/test_narracao.py && python tools/test_erros.py
```

Esperado: `8 passaram, 0 falharam` e `9 passaram, 0 falharam`. A seção `[2]` do `test_erros.py` é a que compara os `{parâmetros}` entre `pt` e `en` de **todas** as chaves, incluindo estas.

- [ ] **Passo 5: Commit**

```bash
git add src/lang/narracao.js
git commit -m "feat(i18n): traduz o restante da narracao"
```

---

## Task 4: Verificação final

**Arquivos:**
- Modificar: `CLAUDE.md`

- [ ] **Passo 1: Rodar todas as suítes de idioma**

```bash
python tools/test_idioma.py && python tools/test_vocabulario.py && python tools/test_erros.py && python tools/test_narracao.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: `36`, `37`, `9`, `8`, `16` e `29` passando, zero falhando.

- [ ] **Passo 2: Rodar as suítes de regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_cenas_conversa.py && python tools/test_masmorra_sequenciada.py
```

Esperado: `336`, `54`, `57` e `118`, zero falhando.

- [ ] **Passo 3: Provar ponta a ponta com dois idiomas**

Com um servidor rodando (`python server.py`, ou o do usuário se a porta 8765 estiver ocupada):

```python
# scratchpad/prova_narracao.py — roda da raiz
import asyncio, json, sys, websockets
sys.stdout.reconfigure(encoding="utf-8")

async def capturar(lang):
    """Cria uma sala e captura a narração de abertura no idioma pedido."""
    async with websockets.connect("ws://localhost:8765", open_timeout=8,
                                  max_size=34*1024*1024) as ws:
        await ws.send(json.dumps({"type": "set_lang", "lang": lang}))
        await ws.send(json.dumps({"type": "create_room", "name": "Prova"}))
        await asyncio.sleep(1)
        await ws.send(json.dumps({"type": "select_class", "class_id": "warrior"}))
        await asyncio.sleep(1)
        await ws.send(json.dumps({"type": "start_game"}))
        falas = []
        fim = asyncio.get_event_loop().time() + 6
        while asyncio.get_event_loop().time() < fim:
            try:
                m = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
            except Exception:
                break
            if m.get("type") == "gm_narration":
                falas.append(m["text"])
            elif m.get("type") in ("game_state", "city_state") and m.get("gm_log"):
                falas.extend(m["gm_log"][-3:])
        return falas

for lang in ("pt", "en"):
    print(f"\n=== {lang} ===")
    for f in capturar_falas := asyncio.run(capturar(lang))[:5]:
        print("  ", f[:100])
```

Esperado: as mesmas narrações, uma lista em português e outra em inglês. Se as duas saírem iguais, ou a frase não foi migrada ou a tradução está vazia.

- [ ] **Passo 4: Documentar no CLAUDE.md**

Em `CLAUDE.md`, acrescentar ao fim:

```markdown
> **Idioma — narração do servidor, lote mecânico (etapa 4b-i de 5):** os **390 `gm_say`
> mecânicos** (os que fecham numa linha só) migrados para `T(...)` e
> traduzidos, em `src/lang/narracao.js`. A chave é o slug do texto **sem** as
> interpolações (`narracao.abre_uma_porta`), o que a mantém legível. **Batismo
> determinístico dos parâmetros**, em três degraus: identificador simples vira ele mesmo,
> `X['name']` vira `X`, o resto vira slug da expressão — mais uma tabela mínima de apelidos
> (`p`→`heroi`, `m`→`monstro`, que sozinhos são 30% das 764 interpolações). Isso difere da
> etapa 4a de propósito: lá as 81 foram batizadas à mão pelo **papel** na frase; aqui, com
> 399 sites automáticos, determinismo vale mais que elegância. **Fora de escopo (etapa
> 4b-ii):** 109 chamadas multilinha — frases montadas por concatenação implícita, as linhas
> de combate —, 3 concatenações com `prefix +`, 7 sites que recebem variável, e 6 que puxam
> do pool `gm(...)`, um catálogo de 30 variantes aleatórias de narração ambiente. O
> `tools/test_narracao.py` **conta e relata** esses restantes em vez de cobrá-los, para a
> suíte não ficar vermelha por trabalho não combinado — e o relatório é o placar da 4b-ii.
> `tools/migrar_narracao.py` é de uso único e reusa o `slug()` do `migrar_erros.py`.
> **Falta:** a etapa 4b-ii e a interface do cliente (~1.000, etapa 5). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-10-idioma-etapa4b1-narracao*`.
```

- [ ] **Passo 5: Commit final**

```bash
git add CLAUDE.md
git commit -m "docs(i18n): documenta a narracao mecanica do servidor"
```
