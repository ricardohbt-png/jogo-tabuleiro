# Etapa 4a do idioma — Mensagens de erro do servidor — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-10-idioma-etapa4a-erros-design.md`

**Objetivo:** Migrar as 471 mensagens de erro do `server.py` para `T(...)` e traduzi-las.

**Arquitetura:** A chave é um slug derivado do próprio texto em português, então a deduplicação cai de graça — as 390 ocorrências de texto fixo viram 306 chaves distintas. Os 390 são migrados por um script determinístico; as 81 com parâmetro vão à mão, porque cada uma exige batizar o parâmetro. O dicionário vive num arquivo novo `src/lang/erros.js`, mantido à mão (depois da migração o código não tem mais o texto português, então não há de onde gerar de novo).

**Stack:** Python 3 (servidor e script), JavaScript vanilla (dicionário do cliente), testes `tools/test_*.py`.

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** — regras obrigatórias do projeto.
- **O usuário edita `server.py`, `game.js` e outros em paralelo, e sobe/derruba um servidor na porta 8765.** Antes de cada commit rode `git status` e use só os caminhos do passo — nunca `git add -A` nem `git add .`. Não mate processo nenhum.
- **Etapas 1–3 (prontas):** `T("chave", **params)` marca texto não traduzido; `broadcast`/`send_to`/`err` resolvem o `T` no idioma de cada conexão via o parâmetro `default` do `json.dumps`; `t()` resolve parâmetro que é ele próprio um `T`; `nome_de(familia, id)` devolve o nome de catálogo como texto tardio. O carregador `_load_lang()` funde **todos** os `.js` de `src/lang/` (hoje `strings.js` e `catalogo.js`).
- Suítes verdes hoje: `test_idioma.py` (32), `test_vocabulario.py` (37), `test_idioma_cliente.js` (16), `test_vocabulario_cliente.js` (29), e as de regressão `test_modo_mestre.py` (336), `test_guilda.py` (54), `test_cenas_conversa.py` (57), `test_masmorra_sequenciada.py` (118).

### Fatos medidos (não precisa re-verificar)

| Forma de chamada | Texto fixo | Com parâmetro | Total |
|---|---:|---:|---:|
| `"msg": "…"` | 382 | 80 | 462 |
| `await err("…")` | 8 | 1 | 9 |
| **Total** | **390** | **81** | **471** |

- Os 390 de texto fixo deduplicam para **306 textos distintos**. "Alvo inválido." aparece 18×, "Ação principal já usada neste turno." 12×, "Aliado inválido." 10×.
- **Todos** os 462 `"msg":` têm o texto na MESMA linha — nenhum quebra linha. Isso é o que torna a substituição por regex segura.
- **Um único site serializa cru**, sem o encoder que resolve o `T`: `server.py:6941`,
  `await ws.send(json.dumps({"type": "error", "msg": "Sala cheia (máximo 6 heróis + 1 mestre)."}))`.
  Um `T` ali estouraria `TypeError: Object of type T is not JSON serializable`. **A Task 1 conserta isso antes de a migração rodar.** (O outro `ws.send(json.dumps(...))` de erro, na linha ~25358, já recebeu `default=` na etapa 1.)
- As 630 chaves traduzidas hoje têm paridade de `{parâmetros}` entre `pt` e `en` — nenhuma divergente. A Task 1 transforma isso em teste permanente.

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `src/lang/erros.js` | **Criar.** Dicionário das mensagens de erro, `window.LANG_ERROS`. |
| `index.html` | Carrega `src/lang/erros.js` depois de `catalogo.js`. |
| `server.py` | O site cru ganha `default=`; 471 mensagens viram `T(...)`. |
| `tools/migrar_erros.py` | **Criar.** Script de uso único: slug, reescrita do fonte, geração do dicionário. |
| `tools/test_erros.py` | **Criar.** Os 5 testes do spec, em 7 seções. |

---

## Task 1: Fundação — arquivo, encoder e o teste de paridade

**Arquivos:**
- Criar: `src/lang/erros.js`
- Criar: `tools/test_erros.py`
- Modificar: `index.html`, `server.py` (linha ~6941)

- [ ] **Passo 1: Escrever o teste que falha**

Criar `tools/test_erros.py`:

```python
"""Mensagens de erro do servidor (etapa 4a) — migração para T() e tradução.
Roda da raiz: python tools/test_erros.py"""
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
# As duas formas de mandar erro no servidor. Capturam só literais — o que já
# virou T(...) não casa, que é justamente como medimos o progresso.
RE_MSG = re.compile(r'"msg":\s*(f?)"([^"]{2,200})"')
RE_ERR = re.compile(r'await err\((f?)"([^"]{2,200})"')
RE_PARAM = re.compile(r"\{(\w+)\}")


def _rodar_verificacoes():
    print("\n[1] Dicionário de erros carregado")
    check("existe src/lang/erros.js",
          os.path.isfile(os.path.join(RAIZ, "src", "lang", "erros.js")))
    check("o servidor funde as chaves de erro",
          any(k.startswith("erro.") for k in S.LANG_STRINGS))

    print("\n[2] Paridade de parâmetros entre pt e en")
    # A falha mais provável numa tradução em lote, e a mais visível: se o "en"
    # perde um {nome}, o jogador lê a chave crua na tela. Vale para TODOS os
    # arquivos de idioma, não só os desta etapa.
    divergentes = []
    traduzidas = 0
    for k, v in S.LANG_STRINGS.items():
        en = v.get("en")
        if not en:
            continue
        traduzidas += 1
        if set(RE_PARAM.findall(v.get("pt") or "")) != set(RE_PARAM.findall(en)):
            divergentes.append(k)
    check(f"nenhum parâmetro divergente ({traduzidas} chaves traduzidas)", not divergentes)
    if divergentes:
        print("     divergentes:", ", ".join(divergentes[:10]))

    print("\n[3] O site que serializa cru resolve T")
    # server.py:6941 manda o erro por ws.send(json.dumps(...)) direto, sem passar
    # por send_to nem err — e é o encoder deles que resolve o T. Sem default=,
    # um T ali estoura TypeError.
    crus = []
    linhas = FONTE.split("\n")
    for i, l in enumerate(linhas):
        if '"msg":' not in l or "json.dumps" not in l:
            continue
        ctx = "\n".join(linhas[i:i + 3])
        if "send_to" in ctx or "await err" in ctx or "broadcast" in ctx:
            continue
        if "default=" not in ctx:
            crus.append(i + 1)
    check("nenhum site de erro serializa sem o encoder", not crus)
    if crus:
        print("     linhas:", crus)


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Mensagens de erro (etapa 4a)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
python tools/test_erros.py
```

Esperado: `1 passaram, 3 falharam` — falta o arquivo, falta a chave `erro.` e o site cru está lá. (A paridade passa, porque hoje não há divergência.)

- [ ] **Passo 3: Criar o dicionário de erros**

Criar `src/lang/erros.js`:

```js
// Mensagens de RECUSA do servidor ao jogador (etapa 4a do idioma).
//
// Diferente do catalogo.js, este arquivo é mantido À MÃO: depois da migração o
// server.py não contém mais o texto em português, só a chave, então não há de
// onde gerar de novo. A chave é o slug do texto original, o que garante que a
// mesma recusa use sempre a mesma frase.
window.LANG_ERROS = {
  "erro.sala_cheia_maximo_6_herois_1_mestre": {
    "pt": "Sala cheia (máximo 6 heróis + 1 mestre).",
    "en": "Room full (max 6 heroes + 1 master)."
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_ERROS);
```

- [ ] **Passo 4: Carregar no `index.html`**

Em `index.html`, na linha que faz `document.write` dos scripts síncronos, acrescentar `src/lang/erros.js` **depois** de `src/lang/catalogo.js` e **antes** de `src/i18n.js`. Ou seja, inserir este trecho na sequência:

```js
document.write('<script src="src/lang/erros.js?v='+v+'"><\/script>');
```

A ordem importa: o arquivo termina com `Object.assign(window.LANG_STRINGS, …)` e precisa que o `strings.js` já tenha criado esse objeto.

- [ ] **Passo 5: Consertar o site que serializa cru**

Em `server.py`, por volta da linha 6941, dentro de `add_player`, trocar:

```python
                await ws.send(json.dumps({"type": "error", "msg": "Sala cheia (máximo 6 heróis + 1 mestre)."}))
```

por:

```python
                # Este site manda direto pelo ws, sem passar por send_to/err —
                # então precisa do mesmo encoder, senão o T não é resolvido.
                await ws.send(json.dumps(
                    {"type": "error", "msg": T("erro.sala_cheia_maximo_6_herois_1_mestre")},
                    default=lambda o: _t_render(o, _lang_de(pid))))
```

`pid` é parâmetro de `add_player`, então está em escopo.

- [ ] **Passo 6: Rodar os testes**

```bash
python tools/test_erros.py && python tools/test_vocabulario.py && python tools/test_idioma.py
```

Esperado: `4 passaram, 0 falharam`, `37 passaram, 0 falharam` e `32 passaram, 0 falharam`.

- [ ] **Passo 7: Commit**

```bash
git add src/lang/erros.js index.html server.py tools/test_erros.py
git commit -m "feat(i18n): dicionario de erros, carregamento e teste de paridade de parametros"
```

---

## Task 2: Script de migração e os 390 de texto fixo

**Arquivos:**
- Criar: `tools/migrar_erros.py`
- Modificar: `server.py` (pelo script), `src/lang/erros.js` (pelo script)
- Modificar: `tools/test_erros.py`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()` em `tools/test_erros.py`:

```python
    print("\n[4] Migração do texto fixo")
    fixos_msg = [t for f, t in RE_MSG.findall(FONTE) if not f]
    fixos_err = [t for f, t in RE_ERR.findall(FONTE) if not f]
    check("nenhum literal de erro de texto fixo sobrou no server.py",
          not fixos_msg and not fixos_err)
    if fixos_msg or fixos_err:
        for t in (fixos_msg + fixos_err)[:6]:
            print("     sobrou:", t[:70])

    print("\n[5] Toda chave erro.* usada existe no dicionário")
    usadas = set(re.findall(r'T\(\s*"(erro\.[^"]+)"', FONTE))
    faltando = sorted(k for k in usadas if k not in S.LANG_STRINGS)
    check(f"nenhuma chave de erro órfã (usadas: {len(usadas)})", not faltando)
    if faltando:
        print("     órfãs:", ", ".join(faltando[:8]))

    print("\n[6] Chave do erros.js sem uso é relatada")
    # Não falha: um texto pode voltar a ser usado. O relatório evita o arquivo
    # virar depósito de frases mortas.
    no_dic = {k for k in S.LANG_STRINGS if k.startswith("erro.")}
    sem_uso = sorted(no_dic - usadas)
    check(f"relatório de chaves sem uso emitido ({len(sem_uso)})", True)
    if sem_uso:
        print("     sem uso:", ", ".join(sem_uso[:8]))
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
python tools/test_erros.py
```

Esperado: a seção [4] falha, listando os textos fixos que ainda estão crus (389 deles — o da "Sala cheia" já foi migrado na Task 1).

- [ ] **Passo 3: Escrever o script de migração**

Criar `tools/migrar_erros.py`:

```python
"""Migra as mensagens de erro de TEXTO FIXO do server.py para T("erro.…").

Roda da raiz:  python tools/migrar_erros.py

Uso ÚNICO. Depois de rodar, o server.py não tem mais o texto em português —
só a chave — então não há de onde gerar de novo, e src/lang/erros.js passa a
ser mantido à mão.

NÃO toca nas mensagens com f-string: cada uma exige batizar o parâmetro, e é
onde um script erraria em silêncio. Elas são migradas à mão depois.
"""
import io, json, os, re, sys, unicodedata
# Sem isto o script escreve os arquivos e SÓ DEPOIS estoura no print (o
# console do Windows é cp1252 e a saída tem →): a migração fica aplicada
# enquanto o operador vê um traceback e acha que nada aconteceu.
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, "server.py")
DICIONARIO = os.path.join(RAIZ, "src", "lang", "erros.js")

RE_MSG = re.compile(r'"msg":\s*(f?)"([^"]{2,200})"')
RE_ERR = re.compile(r'await err\((f?)"([^"]{2,200})"')


def slug(texto, limite=40):
    """Slug do texto em português. Emojis e acentos somem no encode ascii —
    são formatação, não conteúdo, e o texto restante identifica bem a frase."""
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "_", t).strip("_").lower()
    t = t[:limite].rstrip("_")
    return t or "mensagem"


def montar_chaves(textos):
    """{texto: chave}, com dedup por construção e colisão relatada.
    Mesmo texto → mesmo slug → uma chave só para todas as ocorrências."""
    por_slug = {}
    chaves = {}
    colisoes = []
    for texto in textos:
        if texto in chaves:
            continue
        base = slug(texto)
        s = base
        n = 2
        while s in por_slug and por_slug[s] != texto:
            colisoes.append((s, por_slug[s], texto))
            s = f"{base}_{n}"
            n += 1
        por_slug[s] = texto
        chaves[texto] = "erro." + s
    return chaves, colisoes


def ler_existente():
    try:
        raw = io.open(DICIONARIO, encoding="utf-8").read()
        m = re.search(r"^\s*window\.LANG_ERROS\s*=", raw, re.MULTILINE)
        return json.loads(raw[raw.index("{", m.end()):raw.rindex("}") + 1])
    except Exception:
        return {}


def escrever(dicionario):
    corpo = json.dumps(dicionario, ensure_ascii=False, indent=2, sort_keys=True)
    with io.open(DICIONARIO, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "// Mensagens de RECUSA do servidor ao jogador (etapa 4a do idioma).\n"
            "//\n"
            "// Mantido À MÃO: depois da migração o server.py não contém mais o texto\n"
            "// em português, só a chave, então não há de onde gerar de novo. A chave é\n"
            "// o slug do texto original, o que garante que a mesma recusa use sempre a\n"
            "// mesma frase.\n"
            "window.LANG_ERROS = " + corpo + ";\n"
            "Object.assign(window.LANG_STRINGS, window.LANG_ERROS);\n")


def main():
    fonte = io.open(FONTE, encoding="utf-8").read()
    fixos = [t for f, t in RE_MSG.findall(fonte) if not f]
    fixos += [t for f, t in RE_ERR.findall(fonte) if not f]
    chaves, colisoes = montar_chaves(fixos)

    def troca_msg(m):
        if m.group(1):          # f-string: fica para a migração à mão
            return m.group(0)
        return '"msg": T("%s")' % chaves[m.group(2)]

    def troca_err(m):
        if m.group(1):
            return m.group(0)
        return 'await err(T("%s")' % chaves[m.group(2)]

    novo = RE_MSG.sub(troca_msg, fonte)
    novo = RE_ERR.sub(troca_err, novo)

    dic = ler_existente()
    for texto, chave in chaves.items():
        entrada = dic.get(chave) or {}
        dic[chave] = {"pt": texto, "en": entrada.get("en", "")}

    with io.open(FONTE, "w", encoding="utf-8", newline="\n") as f:
        f.write(novo)
    escrever(dic)

    print(f"{len(fixos)} ocorrências de texto fixo → {len(chaves)} chaves distintas.")
    print(f"{sum(1 for v in dic.values() if not v['en'])} sem tradução para o inglês.")
    if colisoes:
        print(f"\n⚠️  {len(colisoes)} colisão(ões) de slug — revise à mão:")
        for s, a, b in colisoes:
            print(f"   {s}\n      {a[:60]}\n      {b[:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

Repare no `troca_err`: ele fecha só o `T("…")` e **não** o parêntese do `err(`, porque o
parêntese de fechamento original continua no fonte logo depois do literal.

- [ ] **Passo 4: Rodar o script**

```bash
python tools/migrar_erros.py
```

Esperado: `389 ocorrências de texto fixo → 305 chaves distintas.` Duas colisões de slug
são **esperadas e corretas** — o jogo tem "Ouro insuficiente." e "Ouro insuficiente!", e
duas variantes de "abra espaço". O script sufixa `_2` e relata; **não unifique**, porque
rever o conteúdo das mensagens está fora do escopo desta etapa e unificar mudaria o texto
em português. O relatório é informativo.

Esperado ainda: (o da "Sala cheia" já saiu na Task 1) e o mesmo número sem tradução. Se aparecer aviso de colisão, **pare e reporte** — a resolução é escolha humana.

- [ ] **Passo 5: Conferir o diff antes de confiar**

```bash
git diff --stat server.py && git diff server.py | head -40
```

Esperado: ~389 linhas alteradas, cada uma trocando um literal por `T("erro.…")`, e nenhuma outra mudança. Leia o começo do diff para confirmar a forma. Se qualquer linha alterada não for uma troca de mensagem, **pare e reverta** (`git checkout server.py`).

- [ ] **Passo 6: Confirmar que o servidor ainda importa e os testes passam**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_erros.py && python tools/test_modo_mestre.py
```

Esperado: `IMPORT OK`, `7 passaram, 0 falharam` e `336 passaram, 0 falharam`. A suíte de regressão é obrigatória aqui: o script tocou centenas de linhas do arquivo central do jogo.

- [ ] **Passo 7: Commit**

```bash
git add server.py src/lang/erros.js tools/migrar_erros.py tools/test_erros.py
git commit -m "feat(i18n): migra as mensagens de erro de texto fixo para T()"
```

---

## Task 3: As 81 mensagens com parâmetro, à mão

**Arquivos:**
- Modificar: `server.py`, `src/lang/erros.js`

Cada uma exige batizar o parâmetro. O padrão:

```python
# antes
await self.send_to(pid, {"type": "error", "msg": f"Requer antes: {nome_req}."})
# depois
await self.send_to(pid, {"type": "error", "msg": T("erro.requer_antes", requisito=nome_req)})
```

E a entrada correspondente em `src/lang/erros.js`:

```js
  "erro.requer_antes": { "pt": "Requer antes: {requisito}.", "en": "Requires first: {requisito}." },
```

**Três regras para batizar:**

1. O nome do parâmetro descreve o **papel** na frase, não a variável de origem:
   `{nome_req}` vira `{requisito}`, `{msg}` vira `{motivo}`.
2. Expressão vira parâmetro avaliado no site da chamada:
   `f"{CLASSES[cls_id]['name']} já está em uso"` vira
   `T("erro.classe_em_uso", classe=CLASSES[cls_id]["name"])`.
3. Se o nome do que entra é um **nome de catálogo**, prefira `nome_de(familia, id)` em vez
   do texto já resolvido — assim ele também sai traduzido. Exemplo:
   `T("erro.item_sem_espaco", item=nome_de("item", it["id"]))`.

- [ ] **Passo 1: Listar o que falta**

```bash
python -c "
import io,re,sys
sys.stdout.reconfigure(encoding='utf-8')
s=io.open('server.py',encoding='utf-8').read()
for pat in (r'\"msg\":\s*f\"([^\"]{2,200})\"', r'await err\(f\"([^\"]{2,200})\"'):
    for t in re.findall(pat, s): print(' ', t[:100])
" | head -90
```

Esperado: 81 linhas. Use a lista como roteiro.

- [ ] **Passo 2: Migrar as 40 primeiras**

Edite site a site com a ferramenta Edit, seguindo o padrão e as três regras acima, e
acrescente cada chave a `src/lang/erros.js` com o `"en"` já preenchido (são poucas e o
contexto está fresco).

Conferir o andamento:

```bash
python -c "
import io,re
s=io.open('server.py',encoding='utf-8').read()
n=len(re.findall(r'\"msg\":\s*f\"',s))+len(re.findall(r'await err\(f\"',s))
print(n,'mensagens com parametro ainda cruas')
"
```

Esperado: `41 mensagens com parametro ainda cruas`.

- [ ] **Passo 3: Commit parcial**

```bash
git add server.py src/lang/erros.js
git commit -m "feat(i18n): migra metade das mensagens de erro com parametro"
```

- [ ] **Passo 4: Migrar as 41 restantes**

Mesmo método. Conferir:

```bash
python -c "
import io,re
s=io.open('server.py',encoding='utf-8').read()
n=len(re.findall(r'\"msg\":\s*f\"',s))+len(re.findall(r'await err\(f\"',s))
print(n,'mensagens com parametro ainda cruas')
"
```

Esperado: `0 mensagens com parametro ainda cruas`.

- [ ] **Passo 4b: Acrescentar a prova ponta a ponta ao teste**

Acrescentar ao fim de `_rodar_verificacoes()` em `tools/test_erros.py`:

```python
    print("
[7] Um erro migrado chega traduzido, pelo send_to real")
    import asyncio

    class RecWS:
        """WebSocket falso que guarda o JSON cru — prova que dois jogadores
        receberam a MESMA recusa em idiomas diferentes."""
        def __init__(self): self.sent = []
        async def send(self, data): self.sent.append(data)

    chave = next((k for k, v in S.LANG_STRINGS.items()
                  if k.startswith("erro.") and v.get("en")), None)
    if not chave:
        check("há ao menos uma mensagem de erro traduzida para provar", False)
    else:
        sala = S.GameRoom("TESTE_ERRO")
        ws_pt, ws_en = RecWS(), RecWS()
        sala.connections = {"e_pt": ws_pt, "e_en": ws_en}
        S.LANG_BY_PID["e_pt"] = "pt"
        S.LANG_BY_PID["e_en"] = "en"
        asyncio.run(sala.send_to("e_pt", {"type": "error", "msg": S.T(chave)}))
        asyncio.run(sala.send_to("e_en", {"type": "error", "msg": S.T(chave)}))
        pt = json.loads(ws_pt.sent[-1])["msg"]
        en = json.loads(ws_en.sent[-1])["msg"]
        check("sai em português para quem está em pt", pt == S.LANG_STRINGS[chave]["pt"])
        check("sai em inglês para quem está em en", en == S.LANG_STRINGS[chave]["en"])
        for pid in ("e_pt", "e_en"):
            S.LANG_BY_PID.pop(pid, None)
```

- [ ] **Passo 5: Rodar tudo**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_erros.py && python tools/test_modo_mestre.py && python tools/test_guilda.py
```

Esperado: `IMPORT OK`, `9 passaram, 0 falharam`, `336 passaram, 0 falharam` e `54 passaram, 0 falharam`.

O teste de paridade de parâmetros (seção [2]) é o que pega um `{requisito}` no `pt` que
virou `{requirement}` no `en`. Se ele ficar vermelho, a chave apontada tem o `en` com
placeholder diferente do `pt`.

- [ ] **Passo 6: Commit**

```bash
git add server.py src/lang/erros.js
git commit -m "feat(i18n): migra as mensagens de erro com parametro"
```

---

## Task 4: Traduzir as ~306 mensagens

**Arquivos:**
- Modificar: `src/lang/erros.js` (só a coluna `en`)

**Registro:** são recusas do sistema ao jogador. Direto e impessoal — "Not your turn.", não
"It appears it may not be your turn right now." Frase curta, ponto final, sem floreio.

**Glossário** (o das etapas 2 e 3 continua valendo):

| Português | Inglês |
|---|---|
| ação principal / ação bônus | main action / bonus action |
| recarga | cooldown |
| rodada / turno | round / turn |
| alcance / área | range / area |
| 🍖 fome / 💧 sede | hunger / thirst |
| alvo / aliado / inimigo | target / ally / enemy |
| adjacente | adjacent |
| masmorra / sala / cidade | dungeon / room / town |
| anfitrião / mestre | host / game master |
| bolsa / equipamento | bag / gear |

**Emojis e `**negrito**` passam intactos** — são formatação, não texto. Nomes de habilidade
seguem o `"en"` das chaves `cat.*.nome`; consulte `src/lang/catalogo.js` quando a mensagem
citar uma.

- [ ] **Passo 1: Traduzir a primeira metade**

Aplicar por script, para o formato sair idêntico ao que o migrador escreve:

```python
# scratchpad/traduzir_erros_1.py
import io, json, os, re, sys
RAIZ = r"C:\Users\RICARDO\Desktop\jogo tabuleiro"
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import migrar_erros as M

TRAD = {
    "erro.alvo_invalido": "Invalid target.",
    # ... a primeira metade
}

d = M.ler_existente()
faltando = [k for k in TRAD if k not in d]
assert not faltando, f"chaves inexistentes: {faltando}"
for k, en in TRAD.items():
    d[k]["en"] = en
M.escrever(d)
print("aplicadas:", len(TRAD))
```

- [ ] **Passo 2: Commit**

```bash
git add src/lang/erros.js
git commit -m "feat(i18n): traduz a primeira metade das mensagens de erro"
```

- [ ] **Passo 3: Traduzir o restante**

Mesmo script, com o resto das chaves. Conferir que zerou:

```bash
python -c "
import os,sys; sys.path.insert(0,'tools'); sys.stdout.reconfigure(encoding='utf-8')
import migrar_erros as M
d=M.ler_existente()
f=[k for k,v in d.items() if not v['en']]
print(len(f),'mensagens de erro sem traducao')
print('\n'.join(f[:10]))
"
```

Esperado: `0 mensagens de erro sem traducao`.

- [ ] **Passo 4: Rodar o teste de paridade**

```bash
python tools/test_erros.py
```

Esperado: `9 passaram, 0 falharam`. A seção [2] é a que importa aqui — ela compara os
`{parâmetros}` do `pt` e do `en` de todas as chaves.

- [ ] **Passo 5: Commit**

```bash
git add src/lang/erros.js
git commit -m "feat(i18n): traduz o restante das mensagens de erro"
```

---

## Task 5: Verificação final

**Arquivos:**
- Modificar: `CLAUDE.md`

- [ ] **Passo 1: Rodar todas as suítes de idioma**

```bash
python tools/test_idioma.py && python tools/test_vocabulario.py && python tools/test_erros.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: `32`, `37`, `9`, `16` e `29` passando, zero falhando.

- [ ] **Passo 2: Rodar as suítes de regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_cenas_conversa.py && python tools/test_masmorra_sequenciada.py
```

Esperado: `336`, `54`, `57` e `118`, zero falhando. Esta é a verificação mais importante da
etapa: o script tocou centenas de linhas do arquivo central do jogo.

- [ ] **Passo 3: Provar ponta a ponta com dois idiomas**

Com um servidor rodando (`python server.py`, ou o do usuário se a porta 8765 estiver
ocupada), rode:

```python
# scratchpad/prova_erros.py — roda da raiz
import asyncio, json, websockets

async def erro_em(lang):
    async with websockets.connect("ws://localhost:8765", open_timeout=8) as ws:
        await ws.send(json.dumps({"type": "set_lang", "lang": lang}))
        # entrar numa sala inexistente é uma recusa determinística
        await ws.send(json.dumps({"type": "join_room", "name": "X", "code": "ZZZZ"}))
        for _ in range(6):
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=3))
            if m.get("type") == "error":
                return m["msg"]
    return None

for lang in ("pt", "en"):
    print(lang, "->", asyncio.run(erro_em(lang)))
```

Esperado: a mesma recusa em português e em inglês — a prova de que a migração chega ao
jogador. Se as duas saírem iguais, a mensagem não foi migrada ou a tradução está vazia.

- [ ] **Passo 4: Documentar no CLAUDE.md**

Em `CLAUDE.md`, acrescentar ao fim:

```markdown
> **Idioma — erros do servidor (etapa 4a de 5):** as **471 mensagens de recusa** migradas
> para `T(...)` e traduzidas. A chave é o **slug do texto em português**
> (`erro.alvo_invalido`), o que **deduplica por construção**: as 390 ocorrências de texto
> fixo viram 306 chaves, e a mesma recusa passa a sair sempre com a mesma frase — o que o
> jogo não garantia nem em português ("Alvo inválido." aparecia 18× no fonte). Dicionário
> em `src/lang/erros.js`, **mantido à mão**: depois da migração o `server.py` não tem mais
> o texto, só a chave, então não há de onde gerar de novo (ao contrário do `catalogo.js`).
> O `tools/migrar_erros.py` é de uso único e fica no repositório como registro do método.
> **Duas formas de chamada** precisaram ser reconhecidas: o dicionário
> `{"type":"error","msg":…}` e o atalho local `await err(…)` do handler. **Um site
> serializava cru** (`ws.send(json.dumps(...))` em `add_player`, sem passar por
> `send_to`/`err`) e teria estourado `TypeError` com um `T` dentro — ganhou o mesmo
> `default=`. **Teste novo que vale para todas as etapas:** paridade de `{parâmetros}`
> entre `pt` e `en` em TODAS as chaves de TODOS os arquivos de idioma — é a falha mais
> provável numa tradução em lote e a mais visível para o jogador, porque o `{nome}` aparece
> cru na tela. Testes: `tools/test_erros.py`. **Falta:** narração do servidor (544, etapa
> 4b) e interface do cliente (~1.000, etapa 5). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-10-idioma-etapa4a-erros*`.
```

- [ ] **Passo 5: Commit final**

```bash
git add CLAUDE.md
git commit -m "docs(i18n): documenta a migracao dos erros do servidor"
```
