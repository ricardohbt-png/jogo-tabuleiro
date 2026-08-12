# Etapa 4c do idioma — Nomes de catálogo dentro da frase — Plano de Implementação

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar tarefa a tarefa. Os passos usam caixas (`- [ ]`).

**Spec:** `docs/superpowers/specs/2026-08-11-idioma-etapa4c-nomes-na-narracao-design.md`

**Objetivo:** Fazer os 295 nomes de catálogo interpolados nas 390 narrações já migradas serem resolvidos no idioma de quem lê, sem quebrar conteúdo autoral nem perder os sufixos dos nomes compostos.

**Arquitetura:** Três helpers no `server.py` (`nome_cat`, `nome_criatura`, `nome_item`) substituem a passagem crua do nome. `nome_cat` só traduz quando o nome cru ainda é o do catálogo — é essa guarda de igualdade que torna a mudança segura para monstro e item autorais. Os nomes compostos (instrumento, servo animado, item corroído, munição) param de ser montados por mutação de string e passam a ser compostos na hora de render, a partir de campos que o objeto já carrega.

**Stack:** Python 3 (servidor), JavaScript vanilla (dicionário e filtro do cliente), testes `tools/test_*.py` e `tools/test_*.js`.

---

## Contexto que o executor precisa saber

- **`CLAUDE.md` na raiz** — regras obrigatórias do projeto.
- **O usuário edita `game.js` e outros em paralelo, e sobe/derruba um servidor na porta 8765.** Antes de cada commit rode `git status` e use só os caminhos do passo — **nunca** `git add -A` nem `git add .`. Não mate processo nenhum. Hoje há WIP de 3D em `game.js` e `.glb` novos em `assets/` que não são desta etapa.
- **Etapas 1–4b-i (prontas):** `T("chave", **params)` marca texto ainda não traduzido; `broadcast`/`send_to`/`err` o resolvem no idioma de cada conexão pelo `default` do `json.dumps`; `t()` resolve parâmetro que é ele próprio um `T`; `nome_de(familia, id)` devolve nome de catálogo como texto tardio.
- **O `T` se comporta como o texto em português** para quem o trate como string — isso mantém 24 mocks de teste funcionando. **Não** transforme `T` em subclasse de `str`: o `json.dumps` pararia de chamar o `default` e a tradução morreria em silêncio.
- **`_load_lang()` funde TODOS os `.js` de `src/lang/`** — um arquivo novo é lido sozinho, sem registrar em lugar nenhum no servidor. No **cliente** é preciso acrescentar o `<script>` no `index.html`.
- Suítes verdes hoje: `test_idioma.py` (36), `test_vocabulario.py` (37), `test_erros.py` (9), `test_narracao.py` (8), `test_idioma_cliente.js` (16), `test_vocabulario_cliente.js` (29); regressão `test_modo_mestre.py` (336), `test_guilda.py` (54), `test_cenas_conversa.py` (57), `test_masmorra_sequenciada.py` (118).

### Fatos medidos (não precisa re-verificar)

716 parâmetros nos 390 `T("narracao.…")`, em 187 expressões. Deles:

| forma | passagens | nesta etapa? |
|---|---:|---|
| nome de jogador (`p['name']`, `caster['name']`, `next_p['name']`, `bardo['name']`, `richard['name']`, `p.get('name'`) | 158 | não — correto cru |
| acesso direto a dict | 216 em 37 expressões | **sim** |
| variável local (`nome` 28, `alvo_nome` 24, `tgt_name` 15, `nome_peca` 3, `name` 3, `dono_nome` 2, `weapon_name` 1, `nomes` 1, +2) | 79 em 10 expressões | **sim** |
| números, dados, CDs | 263 | não |

Mutações de nome em runtime, todas a serem removidas ou compostas:

| origem | linha | campo que já existe |
|---|---|---|
| `item["name"] = f"{item['name']} (corroído)"` | ~24780 | `corrosao_inicial` |
| `virote_loot["name"] = f"Virotes (×{n})"` | ~22507 | `ammo_count` |
| animado `"nome": f"{corpse['nome']} Animado"` | ~12422 | `tipo` (falta `nome_base`) |
| `m["name"] = "Elemental Descontrolado"` | ~19697 | — literal, vira chave |
| `_instrumento_nome(inst)` | ~1066 | `base`/`qualidade`/`origem`/`encantamento` |

**Sem armadilha:** as 16 armas de prata (`Alabarda de Prata`) são compostas no boot e já entraram no `catalogo.js` com tradução. Não mexer.

### Mapa de arquivos

| Arquivo | O que muda |
|---|---|
| `src/lang/composto.js` | **Criar.** Chaves escritas à mão: template e adjetivos do instrumento, `cat.monstro.animado`, `cat.item.corroido`, `cat.item.municao_x`, `cat.item.<id>.nome_curto`, `cat.monstro.elemental_descontrolado`. |
| `index.html` | Carrega `src/lang/composto.js` depois de `strings.js`. |
| `server.py` | `nome_cat`/`nome_criatura`/`nome_item`/`_instrumento_nome_T`; 295 parâmetros; 3 mutações removidas; `nome_base` no animado. |
| `tools/gerar_vocabulario.py` | `SHOP_AMMO` nas fontes. |
| `src/lang/catalogo.js` | Regerado — ganha as 6 munições. |
| `src/i18n.js` | Compositor de nome de instrumento + sufixo de corroído + contagem de munição. |
| `tools/test_narracao.py` | Seção `[6]` — nomes dentro da frase. |
| `tools/test_vocabulario_cliente.js` | Seção nova — compositor do cliente bate com o do servidor. |

---

## Task 1: Os três helpers de nome

**Arquivos:**
- Criar: `src/lang/composto.js`
- Modificar: `index.html`, `server.py`, `tools/test_narracao.py`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()` em `tools/test_narracao.py`:

```python
    print("\n[6] Nomes de catálogo dentro da frase")

    def _en(x):
        """Renderiza como o json.dumps faria para uma conexão em inglês."""
        return S.t(x.key, "en", **x.params) if isinstance(x, S.T) else str(x)

    # Monstro NATIVO: traduz.
    goblin = {"type": "goblin", "name": "Goblin"}
    check("monstro nativo traduz", _en(S.nome_criatura(goblin)) == "Goblin")
    orc = {"type": "orc", "name": S.LANG_STRINGS["cat.monstro.orc.nome"]["pt"]}
    check("monstro nativo usa o en do catálogo",
          _en(S.nome_criatura(orc)) == S.LANG_STRINGS["cat.monstro.orc.nome"]["en"])

    # Monstro AUTORAL: sem chave → sai cru, nos dois idiomas.
    autoral = {"type": "soldado_do_autor", "name": "Soldado do Autor"}
    check("monstro autoral sai cru", _en(S.nome_criatura(autoral)) == "Soldado do Autor")

    # Nativo RENOMEADO no editor: tem chave, mas o nome não bate → sai cru.
    renomeado = {"type": "orc", "name": "Orc Veterano de Khaz"}
    check("nativo renomeado preserva o nome do autor",
          _en(S.nome_criatura(renomeado)) == "Orc Veterano de Khaz")

    # Jogador: nunca traduz.
    heroi = {"class_id": "warrior", "name": "Goblin"}   # nome igual ao de um monstro
    check("nome de jogador nunca é traduzido", _en(S.nome_criatura(heroi)) == "Goblin")
    heroi2 = {"class_id": "mage", "name": "Pedro"}
    check("nome de jogador sai cru", _en(S.nome_criatura(heroi2)) == "Pedro")

    # Item nativo.
    poc = next((i for i in S.SHOP_MERCHANT if i["id"] == "potion"), None)
    if poc:
        check("item nativo traduz",
              _en(S.nome_item(dict(poc))) == S.LANG_STRINGS["cat.item.potion.nome"]["en"])
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
python tools/test_narracao.py
```

Esperado: falha com `AttributeError: module 'server' has no attribute 'nome_criatura'`.

- [ ] **Passo 3: Criar o dicionário dos nomes compostos**

Criar `src/lang/composto.js`:

```js
// NOMES COMPOSTOS — as peças que montam um nome que não existe pronto em
// catálogo nenhum (etapa 4c do idioma).
//
// Mantido À MÃO, como o erros.js e o narracao.js: o gerador
// (tools/gerar_vocabulario.py) só emite .nome e .desc a partir dos catálogos do
// server.py, então nada aqui pode nascer dele.
//
// Nos adjetivos de instrumento o ESPAÇO vem embutido no lado certo de cada
// idioma — " Velha" em português (adjetivo depois) e "Old " em inglês (antes).
// É isso que faz uma parte ausente não deixar espaço solto, e é o que permite a
// cada idioma escolher a sua ordem no template.
window.LANG_COMPOSTO = {
  "cat.monstro.animado":                 {"pt": "{nome} Animado",    "en": "Animated {nome}"},
  "cat.monstro.elemental_descontrolado": {"pt": "Elemental Descontrolado",
                                          "en": "Uncontrolled Elemental"},
  "cat.item.corroido":                   {"pt": "{nome} (corroído)", "en": "{nome} (corroded)"},
  "cat.item.municao_x":                  {"pt": "{nome} (×{n})",     "en": "{nome} (×{n})"},

  "cat.item.flechas.nome_curto":            {"pt": "Flechas",  "en": "Arrows"},
  "cat.item.virotes.nome_curto":            {"pt": "Virotes",  "en": "Bolts"},
  "cat.item.flechas_prata.nome_curto":      {"pt": "Flechas de Prata", "en": "Silver Arrows"},
  "cat.item.virotes_prata.nome_curto":      {"pt": "Virotes de Prata", "en": "Silver Bolts"},
  "cat.item.virote_incendiario.nome_curto": {"pt": "Virote Incendiário", "en": "Incendiary Bolt"},
  "cat.item.flecha_incendiaria.nome_curto": {"pt": "Flecha Incendiária", "en": "Incendiary Arrow"},

  "cat.instrumento.nome_composto": {"pt": "{base}{ql}{orig}{run}",
                                    "en": "{ql}{run}{orig}{base}"},

  "cat.instrumento.adj.velho.m":    {"pt": " Velho",    "en": "Old "},
  "cat.instrumento.adj.velho.f":    {"pt": " Velha",    "en": "Old "},
  "cat.instrumento.adj.rustico.m":  {"pt": " Rústico",  "en": "Rustic "},
  "cat.instrumento.adj.rustico.f":  {"pt": " Rústica",  "en": "Rustic "},
  "cat.instrumento.adj.padrao.m":   {"pt": " Padrão",   "en": "Standard "},
  "cat.instrumento.adj.padrao.f":   {"pt": " Padrão",   "en": "Standard "},
  "cat.instrumento.adj.refinado.m": {"pt": " Refinado", "en": "Refined "},
  "cat.instrumento.adj.refinado.f": {"pt": " Refinada", "en": "Refined "},
  "cat.instrumento.adj.elfica.m":   {"pt": " Élfico",   "en": "Elven "},
  "cat.instrumento.adj.elfica.f":   {"pt": " Élfica",   "en": "Elven "},
  "cat.instrumento.adj.ana.m":      {"pt": " Anão",     "en": "Dwarven "},
  "cat.instrumento.adj.ana.f":      {"pt": " Anã",      "en": "Dwarven "},
  "cat.instrumento.adj.runico.m":   {"pt": " Rúnico",   "en": "Runic "},
  "cat.instrumento.adj.runico.f":   {"pt": " Rúnica",   "en": "Runic "},
  "cat.instrumento.adj.lendario.m": {"pt": " Lendário", "en": "Legendary "},
  "cat.instrumento.adj.lendario.f": {"pt": " Lendária", "en": "Legendary "}
};
Object.assign(window.LANG_STRINGS, window.LANG_COMPOSTO);
```

**Confira contra o `server.py` antes de seguir:** os rótulos em português têm de bater
exatamente com `_QUALIDADE_LABEL`, `_ORIGEM_LABEL`, `_RUNICO_LABEL` e `_LENDARIO_LABEL`
(~linhas 957–967). Se algum divergir, o teste de paridade da Task 3 acusa.

- [ ] **Passo 4: Carregar no `index.html`**

Na linha 14 do `index.html`, acrescentar o script **depois** de `strings.js` (o arquivo
termina com `Object.assign(window.LANG_STRINGS, …)` e precisa que esse objeto já exista):

```js
document.write('<script src="src/lang/composto.js?v='+v+'"><\/script>');
```

- [ ] **Passo 5: Escrever os helpers**

No `server.py`, logo **depois** de `def nome_de(...)` (~linha 1284):

```python
def nome_cat(familia, ident, cru):
    """Nome de catálogo como texto TARDIO, mas SÓ quando o nome cru ainda é o do
    catálogo.

    A guarda de igualdade é o que torna esta etapa segura por construção: monstro
    ou item criado no editor não tem entrada e sai cru; um nativo renomeado por
    `overwrite_native` tem entrada mas com outro texto, e também sai cru,
    preservando o nome que o autor escolheu. Sem lista de exceções para manter."""
    if isinstance(cru, T):
        return cru                      # já resolvido — não reembrulha
    ent = LANG_STRINGS.get(f"cat.{familia}.{ident}.nome")
    if isinstance(ent, dict) and ent.get("pt") == cru:
        return T(f"cat.{familia}.{ident}.nome")
    return cru

def nome_criatura(x):
    """Nome de criatura resolvido no idioma do leitor.

    `alvo` e `target` são ora herói, ora monstro, ora servo animado — o mesmo
    parâmetro, em ~45 sites. A informação só existe em runtime, na forma do dict,
    e é por isso que o despacho mora aqui e não no ponto da frase."""
    if not isinstance(x, dict):
        return x
    nome = x.get("name") or x.get("nome") or ""
    if "class_id" in x:                                 # herói
        return nome
    # Saída explícita para nome trocado em runtime, que por definição não casa a
    # guarda de igualdade (o Elemental Descontrolado é o caso de hoje).
    if x.get("name_key") in LANG_STRINGS:
        return T(x["name_key"])
    if "vida_atual" in x and x.get("tipo"):             # servo animado do Pedro
        return T("cat.monstro.animado",
                 nome=nome_cat("monstro", x["tipo"], x.get("nome_base") or nome))
    if x.get("type"):                                   # monstro
        return nome_cat("monstro", x["type"], nome)
    return nome

def nome_item(it):
    """Nome de item resolvido no idioma do leitor, com os sufixos compostos a
    partir dos campos que o item já carrega — nunca reparseando a string."""
    if not isinstance(it, dict):
        return it
    nome = it.get("name") or it.get("nome") or ""
    ident = it.get("id")
    if not ident:
        return nome
    if it.get("ammo_count"):
        curto = f"cat.item.{ident}.nome_curto"
        base = T(curto) if curto in LANG_STRINGS else nome
        return T("cat.item.municao_x", nome=base, n=it["ammo_count"])
    base = nome_cat("item", ident, nome)
    if it.get("corrosao_inicial"):
        return T("cat.item.corroido", nome=base)
    return base
```

- [ ] **Passo 6: Rodar os testes**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py && python tools/test_idioma.py
```

Esperado: `IMPORT OK`, `15 passaram, 0 falharam` e `36 passaram, 0 falharam`.

- [ ] **Passo 7: Commit**

```bash
git add src/lang/composto.js index.html server.py tools/test_narracao.py
git commit -m "feat(i18n): helpers de nome de catalogo para a narracao"
```

---

## Task 2: Nome composto do instrumento

**Arquivos:**
- Modificar: `server.py`, `tools/test_narracao.py`

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()`:

```python
    print("\n[7] Nome composto do instrumento")
    casos = [
        # (base, qualidade, origem, encantamento, pt esperado, en esperado)
        ("harpa",  "padrao",   "humana", None,     "Harpa Padrão",            "Standard Harp"),
        ("harpa",  "velho",    "humana", None,     "Harpa Velha",             "Old Harp"),
        ("tambor", "velho",    "humana", None,     "Tambor de Guerra Velho",  "Old War Drum"),
        ("harpa",  "rustico",  "elfica", None,     "Harpa Rústica Élfica",    "Rustic Elven Harp"),
        ("harpa",  "padrao",   "humana", "runico", "Harpa Padrão Rúnica",     "Standard Runic Harp"),
        ("harpa",  "refinado", "elfica", "runico", "Harpa Lendária Élfica",   "Legendary Elven Harp"),
        ("alaude", "refinado", "ana",    "runico", "Alaúde Lendário Anão",    "Legendary Dwarven Lute"),
    ]
    for base, ql, orig, enc, esp_pt, esp_en in casos:
        inst = S.criar_instrumento(base, ql, origem=orig, encantamento=enc)
        # O nome gravado no estado continua sendo português puro.
        check(f"{base}/{ql}/{orig}/{enc} — pt", inst["name"] == esp_pt)
        tt = S._instrumento_nome_T(inst)
        check(f"{base}/{ql}/{orig}/{enc} — pt via T", S.t(tt.key, "pt", **tt.params) == esp_pt)
        check(f"{base}/{ql}/{orig}/{enc} — en", S.t(tt.key, "en", **tt.params) == esp_en)
```

- [ ] **Passo 2: Confirmar a assinatura de `criar_instrumento` antes de rodar**

```bash
python -c "
import inspect, sys; sys.path.insert(0,'.'); sys.stdout.reconfigure(encoding='utf-8')
import server as S
print(inspect.signature(S.criar_instrumento))
print(S.criar_instrumento('harpa','refinado',origem='elfica',encantamento='runico')['name'])
"
```

Se a assinatura não aceitar `origem=`/`encantamento=` como palavra-chave, ajuste as
chamadas do teste para a ordem posicional real **antes** de seguir — não invente
parâmetros.

- [ ] **Passo 3: Rodar e confirmar que falha**

```bash
python tools/test_narracao.py
```

Esperado: falha em `_instrumento_nome_T` (atributo inexistente). Os `check` de `pt`
puro devem **passar** — eles descrevem o comportamento atual e são a rede que garante
que a Task não muda o nome gravado no estado.

- [ ] **Passo 4: Escrever `_instrumento_nome_T`**

No `server.py`, logo depois de `_instrumento_nome` (~linha 1082):

```python
def _instrumento_nome_T(inst):
    """Irmã tardia de `_instrumento_nome`: mesmas regras, mas devolve um T para a
    frase ser montada no idioma do leitor.

    `_instrumento_nome` continua devolvendo português puro — é ela que grava
    `inst["name"]`, que vai a disco no savegame. Esta aqui só entra na narração.
    A ORDEM das partes é do template (o inglês põe o adjetivo antes), e o espaço
    vem embutido em cada adjetivo, no lado certo de cada idioma."""
    b = INSTRUMENTOS_BASE[inst["base"]]
    g = "f" if inst["base"] in _INSTRUMENTO_GENERO_FEM else "m"
    orig = inst.get("origem", "humana")
    runico = inst.get("encantamento") == "runico"
    base = nome_cat("instrumento", inst["base"], b["nome"])
    adj = lambda nome: T(f"cat.instrumento.adj.{nome}.{g}")
    # Lendário: 3 eixos no máximo (Refinado + Origem ≠ Humana + Rúnico) →
    # substitui a qualidade E o sufixo Rúnico; a origem permanece.
    if inst.get("qualidade") == "refinado" and orig in _ORIGEM_LABEL and runico:
        return T("cat.instrumento.nome_composto", base=base, ql=adj("lendario"),
                 orig=adj(orig), run="")
    return T("cat.instrumento.nome_composto", base=base,
             ql=adj(inst.get("qualidade") or "padrao"),
             orig=adj(orig) if orig in _ORIGEM_LABEL else "",
             run=adj("runico") if runico else "")
```

- [ ] **Passo 5: Rodar os testes**

```bash
python tools/test_narracao.py && python tools/test_instrumentos_bardo.py
```

Esperado: `36 passaram, 0 falharam` no `test_narracao.py`, e o `test_instrumentos_bardo.py`
**exatamente** com a contagem que tinha antes desta Task (rode-o antes se não souber).
Ele é o dono do `_instrumento_nome`; qualquer mudança de contagem ali é regressão.

- [ ] **Passo 6: Commit**

```bash
git add server.py tools/test_narracao.py
git commit -m "feat(i18n): nome composto de instrumento como texto tardio"
```

---

## Task 3: Parar de mutar os nomes compostos

**Arquivos:**
- Modificar: `server.py`, `tools/test_narracao.py`

Três mutações somem e passam a ser compostas na hora de render. O princípio é o mesmo nas
três: **carregar as partes, nunca reparsear a string pronta.**

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()`:

```python
    print("\n[8] Sufixos compostos, sem mutar o nome")

    alab = next((i for i in S.SHOP_WEAPONS if i["id"] == "alabarda_prata"), None)
    if alab:
        corroido = dict(alab, corrosao_inicial=1)
        check("item corroído — pt",
              S.t(S.nome_item(corroido).key, "pt", **S.nome_item(corroido).params)
              == f"{alab['name']} (corroído)")
        check("item corroído — en",
              S.t(S.nome_item(corroido).key, "en", **S.nome_item(corroido).params)
              == "Silver Halberd (corroded)")

    virotes = next((i for i in S.SHOP_AMMO if i["id"] == "virotes"), None)
    loot = dict(virotes, ammo_count=7)
    check("munição — pt", _en_pt(S.nome_item(loot), "pt") == "Virotes (×7)")
    check("munição — en", _en_pt(S.nome_item(loot), "en") == "Bolts (×7)")

    animado = {"tipo": "goblin", "nome": "Goblin Animado",
               "nome_base": "Goblin", "vida_atual": 5}
    check("servo animado — pt", _en_pt(S.nome_criatura(animado), "pt") == "Goblin Animado")
    check("servo animado — en", _en_pt(S.nome_criatura(animado), "en") == "Animated Goblin")
```

E, junto do `_en` já definido na seção `[6]`, acrescentar o irmão que recebe o idioma:

```python
    def _en_pt(x, lang):
        return S.t(x.key, lang, **x.params) if isinstance(x, S.T) else str(x)
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
python tools/test_narracao.py
```

Esperado: falha em "servo animado" (o `nome_base` ainda não é gravado pelo servidor — o
teste o passa à mão, então este deve **passar**; o que falha é a munição, porque
`nome_curto` existe mas o item de loja carrega `ammo_count` e o esperado muda). Leia a
saída antes de seguir: o objetivo do passo é ver **quais** falham, não quantos.

- [ ] **Passo 3: Remover a mutação do item corroído**

No `server.py`, no bloco de loot do Devorador (~linha 24780), apagar a linha que
concatena o sufixo, mantendo a que marca o campo:

```python
                    if roll > 10:
                        item["corrosao_inicial"] = 1
```

- [ ] **Passo 4: Remover a mutação da munição**

No bloco de loot de virotes (~linha 22507), apagar a linha
`virote_loot["name"] = f"Virotes (×{virotes_rest})"`, mantendo o `ammo_count`:

```python
                    virote_loot = deepcopy(virote_base)
                    virote_loot["ammo_count"] = virotes_rest
                    items_sempre.append(virote_loot)
```

- [ ] **Passo 5: Gravar `nome_base` no servo animado**

Em `handle_animar_mortos` (~linha 12422), ao lado do `nome` composto:

```python
                "nome":       f"{corpse['nome']} Animado",
                "nome_base":  corpse["nome"],   # p/ compor o nome no idioma do leitor
```

- [ ] **Passo 6: Rodar os testes**

```bash
python tools/test_narracao.py && python tools/test_devorador.py && python tools/test_reviver_mortos.py
```

Esperado: `test_narracao.py` todo verde; `test_devorador.py` e `test_reviver_mortos.py`
com a mesma contagem de antes. Se o `test_devorador.py` cobrar o texto `(corroído)` no
nome, **pare e reporte** — é uma decisão de produto que o spec tomou (o sufixo passa a
ser derivado do campo), e o teste precisa ser ajustado com essa justificativa no commit,
não silenciosamente.

- [ ] **Passo 7: Commit**

```bash
git add server.py tools/test_narracao.py
git commit -m "feat(i18n): sufixos compostos derivam de campo, nao de mutacao de nome"
```

---

## Task 4: Munição no gerador de vocabulário

**Arquivos:**
- Modificar: `tools/gerar_vocabulario.py`, `src/lang/catalogo.js`

`SHOP_AMMO` ficou fora das fontes do gerador na etapa 2, então os 6 nomes de munição não
têm chave nenhuma e aparecem em português na bolsa de quem joga em inglês. É um furo da
etapa 2, e fechá-lo aqui é barato.

- [ ] **Passo 1: Acrescentar a fonte**

Em `tools/gerar_vocabulario.py`, na tupla de catálogos de item (~linha 69):

```python
    for nome_cat, campo in (("WEAPONS", "id"), ("SHOP_WEAPONS", "id"), ("SHOP_ARMORS", "id"),
                            ("SHOP_MERCHANT", "id"), ("SHOP_TEMPLE", "id"), ("SHOP_TAVERN", "id"),
                            ("SHOP_AMMO", "id"),
                            ("ARREMESSAVEIS", "id"), ("VENENOS", "id")):
```

- [ ] **Passo 2: Rodar o gerador**

```bash
python tools/gerar_vocabulario.py
```

Esperado: relata as 6 chaves novas sem tradução. O gerador é idempotente e **preserva** o
`en` existente; se ele relatar chaves órfãs ou colisão de nome, leia antes de seguir.

- [ ] **Passo 3: Traduzir as 6**

```python
# scratchpad/traduzir_municao.py — roda da raiz
import io, json, re, os
RAIZ = r"C:\Users\RICARDO\Desktop\jogo tabuleiro"
CAM = os.path.join(RAIZ, "src", "lang", "catalogo.js")
TRAD = {
    "cat.item.flechas.nome":            "Arrows (×10)",
    "cat.item.virotes.nome":            "Bolts (×10)",
    "cat.item.flechas_prata.nome":      "Silver Arrows (×10)",
    "cat.item.virotes_prata.nome":      "Silver Bolts (×10)",
    "cat.item.virote_incendiario.nome": "Incendiary Bolt",
    "cat.item.flecha_incendiaria.nome": "Incendiary Arrow",
}
raw = io.open(CAM, encoding="utf-8").read()
m = re.search(r"^\s*window\.LANG_CATALOGO\s*=", raw, re.MULTILINE)
ini, fim = raw.index("{", m.end()), raw.rindex("}") + 1
d = json.loads(raw[ini:fim])
faltando = [k for k in TRAD if k not in d]
assert not faltando, f"chaves inexistentes: {faltando}"
for k, en in TRAD.items():
    d[k]["en"] = en
novo = raw[:ini] + json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + raw[fim:]
io.open(CAM, "w", encoding="utf-8", newline="\n").write(novo)
print("aplicadas:", len(TRAD))
```

Rodar e conferir que o gerador continua idempotente:

```bash
python scratchpad/traduzir_municao.py && python tools/gerar_vocabulario.py
```

Esperado: a 2ª execução do gerador não relata nada novo e não desfaz as traduções.

- [ ] **Passo 4: Rodar os testes**

```bash
python tools/test_vocabulario.py && node tools/test_vocabulario_cliente.js
```

Esperado: `test_vocabulario.py` verde (as asserções são de **relação** — toda entrada vira
exatamente uma chave —, não de contagem crava; foi lição da etapa 3), e o node verde.

- [ ] **Passo 5: Commit**

```bash
git add tools/gerar_vocabulario.py src/lang/catalogo.js
git commit -m "feat(i18n): municao entra no vocabulario gerado"
```

---

## Task 5: Os 216 parâmetros de acesso direto

**Arquivos:**
- Criar: `tools/migrar_nomes_narracao.py`
- Modificar (pelo script): `server.py`

- [ ] **Passo 1: Escrever o script**

Criar `tools/migrar_nomes_narracao.py`:

```python
"""Troca, dentro dos T("narracao.…"), a passagem CRUA de nome de catálogo pelo
helper que resolve no idioma do leitor.

Roda da raiz:  python tools/migrar_nomes_narracao.py

Uso ÚNICO. Cobre só o acesso DIRETO a dict (`m['name']`, `item['name']`,
`alvo.get('name')`…). Os 79 que chegam por variável local ficam de fora de
propósito — cada um exige olhar a atribuição, e é a Task 6.

Nome de JOGADOR não entra: é escolhido pelo jogador e sai cru, correto.
"""
import io, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTE = os.path.join(RAIZ, "server.py")

# Variáveis que guardam um JOGADOR — o nome sai cru.
JOGADOR = {"p", "caster", "next_p", "bardo", "richard", "jogador", "dono", "rescuer"}
# Variáveis que guardam um ITEM.
ITEM = {"item", "defn", "scroll", "elixir", "potion", "it", "gi", "arma", "weapon"}
# Variáveis que guardam um SERVO ANIMADO (dicts com 'nome', não 'name').
ANIMADO = {"a", "animado"}
# O resto de quem tem ['name'] é criatura: m, alvo, target, t, c, monstro,
# atacante, ator, extra, obj, tgt…

# Casa `nome=<expr>` dentro de uma chamada T("narracao.…").
RE_T = re.compile(r'T\(\s*"narracao\.[^"]+"[^\n]*\)')
RE_ARG = re.compile(r"""(\w+)=(\w+)(?:\[(['"])(name|nome)\3\]|\.get\((['"])(name|nome)\5)""")


def helper_para(var):
    if var in JOGADOR: return None            # fica cru
    if var in ITEM:    return "nome_item"
    if var in ANIMADO: return "nome_criatura"  # o despacho reconhece o animado
    return "nome_criatura"


def main():
    fonte = io.open(FONTE, encoding="utf-8").read()
    trocas = [0]
    pulados = []

    def na_chamada(mt):
        txt = mt.group(0)

        def troca_arg(ma):
            param, var = ma.group(1), ma.group(2)
            h = helper_para(var)
            if h is None:
                pulados.append(var)
                return ma.group(0)
            trocas[0] += 1
            return f"{param}={h}({var})"

        return RE_ARG.sub(troca_arg, txt)

    novo = RE_T.sub(na_chamada, fonte)
    io.open(FONTE, "w", encoding="utf-8", newline="\n").write(novo)
    print(f"{trocas[0]} parâmetros trocados.")
    print(f"{len(pulados)} deixados crus (jogador): "
          f"{', '.join(sorted(set(pulados)))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Passo 2: Ensaiar a classificação antes de tocar no arquivo**

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.stdout.reconfigure(encoding='utf-8')
import migrar_nomes_narracao as M
for v in ['m','alvo','p','caster','item','a','animado','target','defn','next_p']:
    print(f'  {v:<10} -> {M.helper_para(v)}')
"
```

Esperado: `m`→`nome_criatura`, `alvo`→`nome_criatura`, `p`→`None`, `caster`→`None`,
`item`→`nome_item`, `a`→`nome_criatura`, `animado`→`nome_criatura`,
`target`→`nome_criatura`, `defn`→`nome_item`, `next_p`→`None`.

Se algum não bater, **pare e reporte** — a classificação é o coração do script.

- [ ] **Passo 3: Rodar a migração**

```bash
python tools/migrar_nomes_narracao.py
```

Esperado: em torno de `216 parâmetros trocados.` e a lista de pulados contendo
`caster, next_p, p`.

- [ ] **Passo 4: Conferir o diff estruturalmente**

```bash
python -c "
import subprocess, sys, re
sys.stdout.reconfigure(encoding='utf-8')
d = subprocess.run(['git','diff','-U0','--','server.py'], capture_output=True,
                   text=True, encoding='utf-8').stdout
rem = [l[1:] for l in d.split(chr(10)) if l.startswith('-') and not l.startswith('---')]
add = [l[1:] for l in d.split(chr(10)) if l.startswith('+') and not l.startswith('+++')]
print('removidas:', len(rem), '| adicionadas:', len(add))
# A ÚNICA diferença permitida é X['name'] -> nome_xxx(X). Desfazendo a troca, as
# duas linhas têm de ficar idênticas.
def desfaz(l):
    l = re.sub(r'nome_criatura\((\w+)\)', r\"\1['name']\", l)
    return re.sub(r'nome_item\((\w+)\)', r\"\1['name']\", l)
anom = 0
for a, b in zip(rem, add):
    if desfaz(a) != desfaz(b):
        anom += 1
        if anom <= 5:
            print('  ANOMALIA:'); print('    -', a.strip()[:110]); print('    +', b.strip()[:110])
print('anomalias:', anom, '(esperado: só as de [\\'nome\\'] e .get, que o desfaz nao cobre)')
"
```

O `desfaz` normaliza só a forma `['name']`; linhas que usavam `['nome']` ou `.get('name')`
vão aparecer como anomalia **esperada**. Leia-as: cada uma deve ser exatamente a troca do
acesso pelo helper, sem nada mais mudando na linha. Qualquer outra coisa → **pare e
reverta** (`git checkout server.py`) e reporte. O script é reexecutável.

- [ ] **Passo 5: Verificar import e regressão**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py && python tools/test_modo_mestre.py && python tools/test_guilda.py
```

Esperado: `IMPORT OK`, `test_narracao.py` verde, `336 passaram, 0 falharam` e
`54 passaram, 0 falharam`. O script tocou centenas de linhas do arquivo central do jogo;
se a regressão ficar vermelha, **pare e reporte** em vez de tentar consertar.

- [ ] **Passo 6: Commit**

```bash
git add server.py tools/migrar_nomes_narracao.py
git commit -m "feat(i18n): nomes de acesso direto resolvidos no idioma do leitor"
```

---

## Task 6: Os 79 parâmetros que chegam por variável

**Arquivos:**
- Modificar: `server.py`

Estes não dão para roteirizar: a variável nasce longe da frase e às vezes é usada em outra
coisa. São 10 expressões — `nome` (28), `alvo_nome` (24), `tgt_name` (15), `nome_peca` (3),
`name` (3), `dono_nome` (2), `weapon_name` (1), `nomes` (1), e mais duas de uma passagem.

- [ ] **Passo 1: Listar os sites**

```bash
python -c "
import io,re,sys; sys.stdout.reconfigure(encoding='utf-8')
f=io.open('server.py',encoding='utf-8').read().split(chr(10))
alvo=('nome','alvo_nome','tgt_name','nome_peca','name','dono_nome','weapon_name','nomes')
for i,l in enumerate(f):
    if 'T(\"narracao.' not in l: continue
    for v in alvo:
        if re.search(r'=' + v + r'[,\)]', l):
            print(f'{i+1}: {l.strip()[:130]}'); break
" > scratchpad/sites_variavel.txt && wc -l scratchpad/sites_variavel.txt && head -20 scratchpad/sites_variavel.txt
```

- [ ] **Passo 2: Resolver no ponto da frase, um a um**

Para **cada** site listado, suba no arquivo até a atribuição da variável e aplique a regra:

| a variável recebe… | troca |
|---|---|
| `X["name"]` de um monstro/alvo | passe `nome_criatura(X)` no `T(...)`, deixando a variável quieta |
| `X["name"]` de um item | passe `nome_item(X)` |
| nome de peça de equipamento (`nome_peca`) | `nome_item(peca)` |
| nome de jogador | **não mexa** |
| um texto que não é nome de catálogo (rótulo, motivo) | **não mexa** |

**Regra dura:** mude o argumento no `T(...)`, **não** a atribuição da variável — a variável
costuma ser usada também em comparações e em outras frases, e trocá-la por um `T` espalha
o efeito para fora do que este plano cobre.

Quando o objeto não estiver no escopo da frase (a variável é o único que sobrou), aí sim
mude a atribuição para já guardar o helper — e anote o site no corpo do commit.

- [ ] **Passo 3: Conferir que não sobrou nada**

```bash
python -c "
import io,re,sys,collections; sys.stdout.reconfigure(encoding='utf-8')
f=io.open('server.py',encoding='utf-8').read()
c=collections.Counter()
for m in re.finditer(r'T\(\s*\"narracao\.[^\"]+\"([^\n]*)\)', f):
    for a in re.finditer(r'(\w+)=([^,\)]+(?:\([^\)]*\))?)', m.group(1)):
        e=a.group(2).strip()
        if re.search(r'nome|name', e) and not e.startswith(('nome_criatura','nome_item','nome_cat')):
            c[e]+=1
for e,n in c.most_common(30): print(f'{n:>4}  {e}')
print('total ainda cru:', sum(c.values()))
"
```

Esperado: só o que é nome de **jogador** (`p['name']`, `caster['name']`, `next_p['name']`,
`bardo['name']`, `richard['name']`, `p.get('name'`) e o que não é nome de catálogo
(maldição, aventura, habilidade de monstro). Nada de `m['name']` ou `item['name']`.

- [ ] **Passo 4: Rodar tudo**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py && python tools/test_modo_mestre.py && python tools/test_masmorra_sequenciada.py
```

Esperado: `IMPORT OK` e as três verdes (`336` e `118` nas duas últimas).

- [ ] **Passo 5: Commit**

```bash
git add server.py
git commit -m "feat(i18n): nomes que chegam por variavel resolvidos na frase"
```

---

## Task 7: O cliente — compositor de instrumento e sufixos

**Arquivos:**
- Modificar: `src/i18n.js`, `tools/test_vocabulario_cliente.js`

O filtro `traduzirNomes` troca `name` pelo nome do catálogo quando o id tem chave. Isso
deixa dois buracos no inventário de quem joga em inglês, e os dois já existem hoje:

- **item corroído** aparece como "Silver Halberd", sem o "(corroded)" — o jogador não vê
  que a peça está corroída;
- **instrumento** tem id único por combinação (`instrumento_harpa_velho_elfica`), que não
  está no catálogo, então fica em português.

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `tools/test_vocabulario_cliente.js` (siga o estilo de `check` que o
arquivo já usa):

```js
console.log('\n[N] Nomes compostos no cliente');
I18N.setLang('en');

const corroido = {id: 'alabarda_prata', name: 'Alabarda de Prata', corrosao_inicial: 1};
I18N.traduzirNomes(corroido);
check('item corroído mantém o sufixo em inglês',
      corroido.name === 'Silver Halberd (corroded)');

const municao = {id: 'virotes', name: 'Virotes (×10)', ammo_count: 7};
I18N.traduzirNomes(municao);
check('munição compõe a contagem', municao.name === 'Bolts (×7)');

const harpa = {id: 'instrumento_harpa_refinado_elfica_runico', tipo_item: 'instrumento',
               name: 'Harpa Lendária Élfica', base: 'harpa', qualidade: 'refinado',
               origem: 'elfica', encantamento: 'runico'};
I18N.traduzirNomes(harpa);
check('instrumento composto', harpa.name === 'Legendary Elven Harp');

I18N.setLang('pt');
```

- [ ] **Passo 2: Rodar e confirmar que falha**

```bash
node tools/test_vocabulario_cliente.js
```

Esperado: as três novas falham; as 29 antigas continuam passando.

- [ ] **Passo 3: Implementar o compositor no `src/i18n.js`**

Dentro do IIFE, **antes** de `aplicarCatalogo`:

```js
  // ── Nomes compostos ────────────────────────────────────────────────────────
  // Gêmeo de nome_item/_instrumento_nome_T do server.py, lendo AS MESMAS chaves
  // (src/lang/composto.js). Existe porque o nome composto não está em catálogo
  // nenhum: o instrumento tem id único por combinação, e o sufixo de corroído/
  // contagem é derivado de campo, não do nome.
  const GENERO_FEM = ['harpa', 'trompa', 'lira', 'flauta', 'gaita'];
  const COM_ORIGEM = ['elfica', 'ana'];

  function _instrumentoComposto(o) {
    if (o.tipo_item !== 'instrumento' || typeof o.base !== 'string') return null;
    const g = GENERO_FEM.indexOf(o.base) >= 0 ? 'f' : 'm';
    const adj = (n) => t('cat.instrumento.adj.' + n + '.' + g);
    const orig = o.origem || 'humana';
    const runico = o.encantamento === 'runico';
    const base = tem('cat.instrumento.' + o.base + '.nome')
      ? t('cat.instrumento.' + o.base + '.nome') : (o.name || '');
    if (o.qualidade === 'refinado' && COM_ORIGEM.indexOf(orig) >= 0 && runico) {
      return t('cat.instrumento.nome_composto',
               {base: base, ql: adj('lendario'), orig: adj(orig), run: ''});
    }
    return t('cat.instrumento.nome_composto', {
      base: base,
      ql:   adj(o.qualidade || 'padrao'),
      orig: COM_ORIGEM.indexOf(orig) >= 0 ? adj(orig) : '',
      run:  runico ? adj('runico') : '',
    });
  }

  // Recebe o nome JÁ traduzido pelo caminho normal e recoloca o que o filtro
  // comeria: o sufixo mora num campo, então sobrevive à troca pelo catálogo.
  function _comSufixos(o, nome) {
    if (o.ammo_count) {
      const curto = 'cat.item.' + o.id + '.nome_curto';
      return t('cat.item.municao_x',
               {nome: tem(curto) ? t(curto) : nome, n: o.ammo_count});
    }
    if (o.corrosao_inicial) return t('cat.item.corroido', {nome: nome});
    return nome;
  }
```

E, dentro de `aplicarCatalogo`, substituir o bloco que troca o nome por:

```js
      const composto = _instrumentoComposto(o);
      if (composto !== null) {
        for (const campo of CAMPOS_NOME) {
          if (typeof o[campo] === 'string') { o[campo] = composto; break; }
        }
      } else if (base && tem(base + '.nome')) {
        for (const campo of CAMPOS_NOME) {
          if (typeof o[campo] === 'string') {
            o[campo] = _comSufixos(o, t(base + '.nome'));
            break;
          }
        }
      } else if (typeof o.id === 'string' && (o.ammo_count || o.corrosao_inicial)) {
        // Sem chave de catálogo (item autoral), mas o sufixo ainda vale.
        for (const campo of CAMPOS_NOME) {
          if (typeof o[campo] === 'string') { o[campo] = _comSufixos(o, o[campo]); break; }
        }
      }
```

**Atenção:** o `base` de hoje é calculado por `_chaveBase(o, idPai)` e o bloco de descrição
que vem logo abaixo continua usando `base` — mantenha o `if (base)` original em volta da
parte de descrição, ou guarde a descrição num `if (base && !soNome && …)` próprio. Não
apague o caminho de descrição.

- [ ] **Passo 4: Rodar os testes do cliente**

```bash
node tools/test_vocabulario_cliente.js && node tools/test_idioma_cliente.js
```

Esperado: as duas verdes, com as 3 checagens novas passando.

- [ ] **Passo 5: Commit**

```bash
git add src/i18n.js tools/test_vocabulario_cliente.js
git commit -m "feat(i18n): cliente compoe nome de instrumento e sufixos de item"
```

---

## Task 8: `Elemental Descontrolado`

**Arquivos:**
- Modificar: `server.py`

O nome deste monstro é trocado em runtime (`server.py:19874`), então por definição não casa
a guarda de igualdade e sairia cru para sempre. A frase daquele site **não** cita o nome —
ele vaza depois, nas narrações de turno e de ataque, via `nome_criatura`. A saída é o
campo `name_key`, que a Task 1 já ensinou o `nome_criatura` a preferir.

- [ ] **Passo 1: Escrever o teste que falha**

Acrescentar ao fim de `_rodar_verificacoes()` em `tools/test_narracao.py`:

```python
    print("\n[9] Nome trocado em runtime")
    elem = {"type": "elemental_eletrico", "name": "Elemental Descontrolado",
            "name_key": "cat.monstro.elemental_descontrolado"}
    check("name_key vence a guarda de igualdade — pt",
          _en_pt(S.nome_criatura(elem), "pt") == "Elemental Descontrolado")
    check("name_key vence a guarda de igualdade — en",
          _en_pt(S.nome_criatura(elem), "en") == "Uncontrolled Elemental")
```

- [ ] **Passo 2: Marcar a chave no site do pergaminho**

Em `server.py:19874`, ao lado da troca do nome:

```python
        m["name"] = "Elemental Descontrolado"
        m["name_key"] = "cat.monstro.elemental_descontrolado"
```

O `name` gravado no estado continua sendo português puro, como todo `name` — é o
`name_key` que carrega a tradução para quem lê.

- [ ] **Passo 3: Rodar**

```bash
python -c "import server; print('IMPORT OK')" && python tools/test_narracao.py && python tools/test_modo_mestre.py
```

Esperado: `IMPORT OK` e as duas verdes.

- [ ] **Passo 4: Commit**

```bash
git add server.py tools/test_narracao.py
git commit -m "feat(i18n): elemental descontrolado vira chave"
```

---

## Task 9: Verificação final

**Arquivos:**
- Modificar: `CLAUDE.md`

- [ ] **Passo 1: Todas as suítes de idioma**

```bash
python tools/test_idioma.py && python tools/test_vocabulario.py && python tools/test_erros.py && python tools/test_narracao.py && node tools/test_idioma_cliente.js && node tools/test_vocabulario_cliente.js
```

Esperado: `36`, `37`, `9`, o novo total do `test_narracao.py`, `16` e `32`, zero falhando.

- [ ] **Passo 2: Regressão**

```bash
python tools/test_modo_mestre.py && python tools/test_guilda.py && python tools/test_cenas_conversa.py && python tools/test_masmorra_sequenciada.py && python tools/test_instrumentos_bardo.py && python tools/test_devorador.py && python tools/test_reviver_mortos.py
```

Esperado: `336`, `54`, `57`, `118` e as três últimas com a contagem que tinham antes.

- [ ] **Passo 3: Prova ponta a ponta, com o servidor REINICIADO**

Armadilha registrada pela 4b-i: um servidor já rodando na porta 8765 pode ser de antes da
migração, e a prova sai toda em português. Pergunte ao usuário antes de derrubar o
processo dele; nunca mate processo por conta própria.

Com o servidor novo no ar, entre com dois clientes na mesma sala, um em cada idioma, e
confirme numa narração que cite monstro: o jogador em inglês lê o nome em inglês, o em
português lê em português, **na mesma frase do mesmo evento**.

- [ ] **Passo 4: Documentar no `CLAUDE.md`**

Acrescentar ao fim:

```markdown
> **Idioma — nomes de catálogo dentro da frase (etapa 4c de 5):** fecha a lacuna que a
> 4b-i deixou registrada — a frase traduzia mas o nome saía cru ("Round 1 — **Elemental
> Elétrico**'s initiative"). Os **295 parâmetros** que carregam nome de catálogo (216 de
> acesso direto + 79 por variável; os 158 de nome de JOGADOR seguem crus, corretos)
> passam por três helpers novos: **`nome_cat(familia, ident, cru)`** — devolve `T` só
> quando o nome cru **ainda é o do catálogo**, e é essa **guarda de igualdade** que torna
> a etapa segura por construção para conteúdo autoral (monstro/item do editor não tem
> chave, e nativo renomeado por `overwrite_native` tem chave com outro texto: os dois
> saem crus, preservando o nome do autor); **`nome_criatura(x)`** — despacha pela FORMA
> do dict (`class_id`→herói cru, `vida_atual`+`tipo`→servo animado, `type`→monstro),
> porque `alvo`/`target` são ora herói ora monstro ora servo **no mesmo parâmetro**, em
> ~45 sites, e a informação só existe em runtime; **`nome_item(it)`**. **Nomes compostos
> — princípio único: carregar as partes, nunca reparsear a string pronta.** Três mutações
> de `name` foram REMOVIDAS e viraram composição na hora de render, a partir de campo que
> o objeto já tinha: `(corroído)` ← `corrosao_inicial`, `Virotes (×N)` ← `ammo_count`, e o
> servo animado ← `tipo` + `nome_base` (campo novo). O **instrumento** ganhou
> `_instrumento_nome_T`, irmã tardia de `_instrumento_nome` (que segue devolvendo
> português puro — é ela que grava `inst["name"]`, e isso vai a disco no savegame): a
> ordem das partes é do **template** (`cat.instrumento.nome_composto`), porque em inglês o
> adjetivo vem ANTES do substantivo, e o **espaço vem embutido no lado certo de cada
> idioma** em cada adjetivo (" Velha" × "Old "), que é o que faz parte ausente não deixar
> espaço solto. O gênero existe só no `pt`. `Harpa Lendária Élfica` → `Legendary Elven
> Harp`. Chaves escritas à mão em **`src/lang/composto.js`** (o gerador só emite
> `.nome`/`.desc`, então nada disso poderia nascer dele). **Dois bugs pré-existentes
> fechados de quebra:** `SHOP_AMMO` estava fora das fontes do `gerar_vocabulario.py` desde
> a etapa 2 (6 munições sem chave nenhuma), e o filtro `traduzirNomes` do cliente comia o
> "(corroído)" da bolsa em inglês — o jogador não via que a peça estava corroída. O
> cliente ganhou um **compositor gêmeo** em `src/i18n.js` (o instrumento tem id único por
> combinação, que não existe no catálogo), lendo as MESMAS chaves; um teste compara as
> duas implementações nos 5 arranjos para que não divirjam. **Continua em português de
> propósito:** monstro/item autoral, nome de jogador, e os 153 sites da **4b-ii**, que
> segue pendente. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-11-idioma-etapa4c-nomes-na-narracao*`. Testes:
> `tools/test_narracao.py`, `tools/test_vocabulario_cliente.js`.
```

- [ ] **Passo 5: Commit final**

```bash
git add CLAUDE.md
git commit -m "docs(i18n): documenta os nomes de catalogo dentro da frase"
```

---

## Fora deste plano (registrado, não esquecido)

- **Maldições** (`MALDICOES`) não são uma família de catálogo, então `mal['nome']`
  continua em português dentro da frase em inglês. Fechar isso é acrescentar uma 9ª
  família ao gerador e traduzir os nomes — **não** está no spec aprovado; proponha ao
  usuário como etapa própria em vez de fazer por conta.
- **Habilidade de monstro** (`ability['name']`, `ab['name']`) e **aventura**
  (`adventure['nome']`) idem: são conteúdo autorado ou fora das 8 famílias.
- **Etapa 4b-ii** — os 153 `gm_say` ainda não migrados.
- **Etapa 5** — a interface do cliente (~1.000 strings).
