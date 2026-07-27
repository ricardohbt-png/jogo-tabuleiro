# Editor de Itens — Fase H: Venenos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Destravar a sub-aba Venenos (última 🔒) do Editor de Itens, cobrindo as 5 operações do subsistema `VENENOS`, fechando as 8 sub-abas.

**Architecture:** Um veneno custom precisa de uma entrada no dict `VENENOS` (definição do efeito) e de um item de bolsa com `effect:"coat_poison"` + `veneno_id` — nos nativos ambos usam o MESMO id, convenção mantida aqui. `_aplicar_veneno` já é data-driven nas 5 operações, então o motor não muda. O cliente também não muda: `coat_poison` é tratado genericamente (loja por `effect`, tooltip lendo `descricao`/`efeito` do próprio item).

**Tech Stack:** Python 3 (`server.py`), Vanilla JS (`tools/editor_items_*.js`), testes: `python tools/test_editor_itens.py` e `node tools/test_editor_items_logic.js`.

---

## ⚠️ Receita de partial staging (server.py) — LER ANTES DAS TASKS 2, 3 e 4

O usuário reworka `server.py` em paralelo (WIP "Barreira Arcana" + lojas por cidade). **NUNCA** `git add server.py` nem `git add -A`.

```bash
git add tools/test_editor_itens.py            # teste é seguro (fora do WIP)
git diff -- server.py > /tmp/all.patch        # contém SEUS hunks + o WIP
# Leia /tmp/all.patch, identifique os @@ hunks QUE VOCÊ escreveu e monte
# /tmp/mine.patch = header (4 linhas: diff/index/---/+++) + APENAS esses hunks.
git apply --cached /tmp/mine.patch
git diff --cached -- server.py                # confira a olho: só o seu código
git diff --cached --stat
```

Se vazar qualquer linha do WIP: `git reset server.py` e refaça. `git add -p` é interativo e **não funciona** aqui.

As funções novas ficam na região contígua de itens custom (~22150–22500), longe do WIP. **Atenção na Task 4**: o retoque da mensagem fica em `_aplicar_veneno` (~15037) — confira a vizinhança de hunks do WIP antes de extrair.

## ⚠️ A suíte de testes aborta no working tree (pré-existente)

Com o WIP do usuário, `python tools/test_editor_itens.py` **crasha na seção `[7]`** (lojas por cidade mudaram `handle_shop_buy`). Isso é **pré-existente e não é seu** — não tente consertar, não toque em `handle_shop_buy`. Para verificar as seções novas, importe o módulo e chame as funções diretamente:

```bash
python -c "
import sys; sys.path.insert(0,'tools'); sys.path.insert(0,'.')
import importlib.util
spec=importlib.util.spec_from_file_location('t','tools/test_editor_itens.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.test_validacao_veneno()
print(f'{m.PASS} passaram, {m.FAIL} falharam')
"
```

(No HEAD commitado, sem o WIP, a suíte roda inteira — é assim que a Task 5 verifica.)

---

## File Structure

- **Modify:** `tools/editor_items_logic.js` — catálogos `POISON_*`, `serializePoison`/`validatePoisonDraft`/`suggestPricePoison`.
- **Modify:** `tools/test_editor_items_logic.js` — casos node de veneno.
- **Modify:** `server.py` — 4 sets novos, `_validate_custom_poison`, `_custom_poison_defn`, `_custom_poison_inventory_dict`, cleanup + ramo em `_apply_custom_items`, retoque da mensagem de `penalidade`.
- **Modify:** `tools/test_editor_itens.py` — seção `[H1]`–`[H5]`.
- **Modify:** `tools/editor_items_editor.js` — destravar sub-aba, form de veneno.
- **Modify:** `CLAUDE.md` — nota da Fase H.

---

## Task 1: Lógica pura (cliente) — serializePoison

**Files:**
- Modify: `tools/editor_items_logic.js`
- Test: `tools/test_editor_items_logic.js`

- [ ] **Step 1: Escrever os testes node que falham**

Acrescente ANTES da linha final `console.log(...)` em `tools/test_editor_items_logic.js`:

```javascript
// Fase H — venenos
check("POISON_OPS tem as 5 operações",
  L.POISON_OPS.length === 5 && L.POISON_OPS.indexOf("dano") >= 0
  && L.POISON_OPS.indexOf("petrificar") >= 0 && L.POISON_OPS.indexOf("cegar") >= 0);
check("POISON_ATTRS / POISON_PENS / POISON_SAVES",
  L.POISON_ATTRS.indexOf("forca") >= 0 && L.POISON_PENS.indexOf("ataque") >= 0
  && L.POISON_SAVES.indexOf("fortitude") >= 0);
const pDano = L.serializePoison({name:"Bile Ácida", operacao:"dano", save:"fortitude",
  dificuldade:12, anula:true, dur_qtd:1, dur_faces:6,
  dano_fixo:false, dano_qtd:1, dano_faces:4, modelo_save:"aplicacao",
  descricao:"Corrói por dentro.",
  disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:20});
check("serializePoison id/slot/effect/veneno_id",
  pDano.id === "bile_acida" && pDano.item_slot === "bag"
  && pDano.effect === "coat_poison" && pDano.item_type === "poison");
check("serializePoison dano por dado", pDano.operacao === "dano" && pDano.dano === "1d4");
check("serializePoison duracao", pDano.duracao === "1d6");
check("serializePoison save_aplicacao", pDano.save_aplicacao === true
  && pDano.save_neutraliza_por_rodada === undefined);
check("serializePoison guarda descricao", pDano.descricao === "Corrói por dentro.");
const pRodada = L.serializePoison({name:"X", operacao:"dano", dano_fixo:true, dano_valor:2,
  modelo_save:"rodada", dur_qtd:1, dur_faces:4});
check("dano fixo vira número", pRodada.dano === 2);
check("modelo rodada grava save_neutraliza_por_rodada",
  pRodada.save_neutraliza_por_rodada === true && pRodada.save_aplicacao === undefined);
const pRed = L.serializePoison({name:"Y", operacao:"reduzir", atributo:"constituicao",
  val_qtd:1, val_faces:4, dur_qtd:1, dur_faces:6});
check("reduzir grava atributo e valor",
  pRed.operacao === "reduzir" && pRed.atributo === "constituicao" && pRed.valor === "1d4");
const pPen = L.serializePoison({name:"Z", operacao:"penalidade",
  atributos:[{chave:"ataque", valor:2},{chave:"movimento", valor:1},{chave:"xpto", valor:9}],
  dur_qtd:1, dur_faces:6});
check("penalidade normaliza pares negativos",
  JSON.stringify(pPen.atributos) === JSON.stringify([["ataque",-2],["movimento",-1]]));
const pPet = L.serializePoison({name:"W", operacao:"petrificar", dur_qtd:1, dur_faces:4,
  durfalha_qtd:1, durfalha_faces:4, penalidade_falha:[{chave:"movimento", valor:1}]});
check("petrificar grava duracao_falha e penalidade_falha",
  pPet.duracao_falha === "1d4"
  && JSON.stringify(pPet.penalidade_falha) === JSON.stringify([["movimento",-1]]));
const pCeg = L.serializePoison({name:"V", operacao:"cegar", dur_qtd:1, dur_faces:4,
  penalidade_ataque:4, bloqueia_distancia:true});
check("cegar grava penalidade_ataque negativa e bloqueio",
  pCeg.penalidade_ataque === -4 && pCeg.bloqueia_distancia === true);
check("icone default ☠️", L.serializePoison({name:"Q", operacao:"dano"}).emoji === "☠️");
check("validatePoisonDraft aceita valido",
  L.validatePoisonDraft({name:"X", operacao:"dano"}).ok);
check("validatePoisonDraft rejeita sem nome",
  !L.validatePoisonDraft({name:"", operacao:"dano"}).ok);
check("validatePoisonDraft rejeita operacao invalida",
  !L.validatePoisonDraft({name:"X", operacao:"explodir"}).ok);
check("validatePoisonDraft rejeita reduzir sem atributo valido",
  !L.validatePoisonDraft({name:"X", operacao:"reduzir", atributo:"carisma"}).ok);
check("validatePoisonDraft rejeita penalidade sem pares",
  !L.validatePoisonDraft({name:"X", operacao:"penalidade", atributos:[]}).ok);
check("suggestPricePoison cresce com a CD",
  L.suggestPricePoison({dificuldade:16}) > L.suggestPricePoison({dificuldade:8}));
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `node tools/test_editor_items_logic.js`
Expected: FAIL (`L.POISON_OPS` indefinido / `serializePoison is not a function`).

- [ ] **Step 3: Implementar em `tools/editor_items_logic.js`**

3a. Acrescente `, K_POISON = 3` à linha de constantes `K_*` existente.

3b. Adicione os quatro catálogos perto de `THROW_TARGETS`:

```javascript
  var POISON_OPS = ["dano", "reduzir", "penalidade", "petrificar", "cegar"];
  var POISON_ATTRS = ["forca", "constituicao", "destreza", "inteligencia"];
  var POISON_PENS = ["ataque", "movimento", "dano", "ca", "percepcao"];
  var POISON_SAVES = ["fortitude", "reflexos", "vontade"];
```

3c. Adicione as funções logo após `suggestPriceThrowable`:

```javascript
  // Pares [chave, valor] de penalidade: filtra chaves desconhecidas e força negativo.
  function poisonPares(lista) {
    return (lista || []).filter(function (o) {
      return o && POISON_PENS.indexOf(o.chave) >= 0;
    }).map(function (o) {
      return [o.chave, -Math.abs(+o.valor || 0)];
    });
  }
  function serializePoison(d) {
    var op = POISON_OPS.indexOf(d.operacao) >= 0 ? d.operacao : "dano";
    var item = {
      id: slugify(d.id || d.name), name: String(d.name || "").trim().slice(0, 60),
      emoji: d.emoji || "☠️", item_type: "poison", item_slot: "bag",
      effect: "coat_poison", custom: true, operacao: op,
      save: POISON_SAVES.indexOf(d.save) >= 0 ? d.save : "fortitude",
      dificuldade: Math.max(1, Math.min(40, +d.dificuldade || 10)),
      anula: d.anula !== false,
      duracao: buildDie(d.dur_qtd, d.dur_faces || 4),
      allowed_classes: (d.allowed_classes || []).slice(),
      price: Math.max(0, +d.price || 0),
      disponibilidade: {
        loja: !!(d.disponibilidade || {}).loja, baus: !!(d.disponibilidade || {}).baus,
        loot_monstro: !!(d.disponibilidade || {}).loot_monstro,
      },
    };
    var desc = String(d.descricao || "").trim().slice(0, 160);
    if (desc) item.descricao = desc;
    if (op === "dano") {
      item.dano = d.dano_fixo ? Math.max(1, +d.dano_valor || 1) : buildDie(d.dano_qtd, d.dano_faces || 4);
      if (d.modelo_save === "rodada") item.save_neutraliza_por_rodada = true;
      else item.save_aplicacao = true;
    } else if (op === "reduzir") {
      item.atributo = POISON_ATTRS.indexOf(d.atributo) >= 0 ? d.atributo : "forca";
      item.valor = buildDie(d.val_qtd, d.val_faces || 4);
    } else if (op === "penalidade") {
      item.atributos = poisonPares(d.atributos);
    } else if (op === "petrificar" || op === "cegar") {
      item.duracao_falha = buildDie(d.durfalha_qtd, d.durfalha_faces || 4);
      item.penalidade_falha = poisonPares(d.penalidade_falha);
      if (op === "cegar") {
        item.penalidade_ataque = -Math.abs(+d.penalidade_ataque || 4);
        item.bloqueia_distancia = !!d.bloqueia_distancia;
      }
    }
    return item;
  }
  function validatePoisonDraft(d) {
    if (!String(d.name || "").trim()) return { ok: false, msg: "informe o nome" };
    if (POISON_OPS.indexOf(d.operacao) < 0) return { ok: false, msg: "efeito inválido" };
    if (d.operacao === "reduzir" && POISON_ATTRS.indexOf(d.atributo) < 0)
      return { ok: false, msg: "atributo inválido" };
    if (d.operacao === "penalidade" && !poisonPares(d.atributos).length)
      return { ok: false, msg: "adicione ao menos uma penalidade" };
    return { ok: true };
  }
  function suggestPricePoison(item) {
    return Math.max(1, Math.round(K_POISON * (+item.dificuldade || 10)));
  }
```
Note: `slugify`, `buildDie` e `K_POISON` (3a) já existem no módulo.

3d. Adicione ao objeto `api`:

```javascript
              serializePoison: serializePoison,
              validatePoisonDraft: validatePoisonDraft,
              suggestPricePoison: suggestPricePoison,
              POISON_OPS: POISON_OPS, POISON_ATTRS: POISON_ATTRS,
              POISON_PENS: POISON_PENS, POISON_SAVES: POISON_SAVES,
```

- [ ] **Step 4: Rodar e ver passar**

Run: `node tools/test_editor_items_logic.js`
Expected: PASS — todos verdes, incluindo os casos pré-existentes.

- [ ] **Step 5: Commit (arquivos de cliente — seguros)**

```bash
git add tools/editor_items_logic.js tools/test_editor_items_logic.js
git commit -m "feat(itens): lógica de venenos custom (5 operações)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Servidor — validação de veneno

**Files:**
- Modify: `server.py` (4 sets novos; `_validate_custom_item`; nova `_validate_custom_poison`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_editor_itens.py`, adicione logo após `throwable_sample`:

```python
def poison_sample(**over):
    base = {"id": "veneno_teste", "name": "Veneno Teste", "emoji": "☠️",
            "item_type": "poison", "operacao": "dano", "dano": "1d4",
            "save": "fortitude", "dificuldade": 12, "anula": True, "duracao": "1d6",
            "save_aplicacao": True, "descricao": "Dói.",
            "allowed_classes": [], "price": 20,
            "disponibilidade": {"loja": True, "baus": False, "loot_monstro": False}}
    base.update(over); return base

def test_validacao_veneno():
    print("\n[H1] Validacao de veneno")
    ok, it = S._validate_custom_item(poison_sample())
    check("aceita veneno de dano", ok)
    check("item_type/slot/effect",
          ok and it.get("item_type") == "poison" and it.get("item_slot") == "bag"
          and it.get("effect") == "coat_poison")
    check("campos comuns preservados",
          ok and it.get("save") == "fortitude" and it.get("dificuldade") == 12
          and it.get("anula") is True and it.get("duracao") == "1d6")
    check("dano + save_aplicacao", ok and it.get("dano") == "1d4" and it.get("save_aplicacao") is True)
    check("descricao preservada", ok and it.get("descricao") == "Dói.")
    okr, itr = S._validate_custom_item(poison_sample(id="veneno_red", operacao="reduzir",
        atributo="constituicao", valor="1d4"))
    check("aceita reduzir", okr and itr.get("operacao") == "reduzir"
          and itr.get("atributo") == "constituicao" and itr.get("valor") == "1d4")
    okp, itp = S._validate_custom_item(poison_sample(id="veneno_pen", operacao="penalidade",
        atributos=[["ataque", -2], ["movimento", -1], ["xpto", -9]]))
    check("penalidade filtra chave invalida",
          okp and itp.get("atributos") == [["ataque", -2], ["movimento", -1]])
    okt, itt = S._validate_custom_item(poison_sample(id="veneno_pet", operacao="petrificar",
        anula=False, duracao_falha="1d4", penalidade_falha=[["movimento", -1]]))
    check("aceita petrificar", okt and itt.get("operacao") == "petrificar"
          and itt.get("duracao_falha") == "1d4"
          and itt.get("penalidade_falha") == [["movimento", -1]])
    okc, itc = S._validate_custom_item(poison_sample(id="veneno_ceg", operacao="cegar",
        anula=False, penalidade_ataque=-4, bloqueia_distancia=True, duracao_falha="1d4"))
    check("aceita cegar", okc and itc.get("operacao") == "cegar"
          and itc.get("penalidade_ataque") == -4 and itc.get("bloqueia_distancia") is True)
    oko, _ = S._validate_custom_item(poison_sample(operacao="explodir"))
    check("rejeita operacao invalida", not oko)
    oka, _ = S._validate_custom_item(poison_sample(operacao="reduzir", atributo="carisma"))
    check("rejeita atributo invalido em reduzir", not oka)
    okv, _ = S._validate_custom_item(poison_sample(operacao="penalidade", atributos=[]))
    check("rejeita penalidade sem pares", not okv)
    okn, _ = S._validate_custom_item(poison_sample(id="veneno_fungo_acre"))
    check("rejeita id nativo de VENENOS", not okn)
    oks, _ = S._validate_custom_item(poison_sample(save="carisma"))
    check("save invalido cai para fortitude",
          oks and S._validate_custom_item(poison_sample(save="carisma"))[1].get("save") == "fortitude")
```

Registre no `if __name__ == "__main__":`, logo APÓS `test_arremessavel_merge(); test_arremessavel_uso_alvo(); test_arremessavel_uso_area()`:

```python
    test_validacao_veneno()
```

- [ ] **Step 2: Rodar e ver falhar**

Use o comando de import direto (ver topo) chamando `m.test_validacao_veneno()`.
Expected: FAIL — `_validate_custom_item` retorna "tipo de item não suportado" para `poison`.

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione os 4 sets logo após as linhas `_ITEM_THROW_TARGETS`/`_ITEM_THROW_ELEMENTS`:

```python
# Operações/atributos/penalidades/saves válidos p/ veneno custom (Fase H).
_ITEM_POISON_OPS = {"dano", "reduzir", "penalidade", "petrificar", "cegar"}
_ITEM_POISON_ATTRS = {"forca", "constituicao", "destreza", "inteligencia"}
_ITEM_POISON_PENS = {"ataque", "movimento", "dano", "ca", "percepcao"}
_ITEM_POISON_SAVES = {"fortitude", "reflexos", "vontade"}
```

3b. Em `_validate_custom_item`, adicione o dispatch antes do `return False`:

```python
    if it == "throwable":
        return _validate_custom_throwable(raw)
    if it == "poison":
        return _validate_custom_poison(raw)
    return False, "tipo de item não suportado"
```

3c. Adicione a nova função imediatamente após `_validate_custom_throwable`:

```python
def _validate_custom_poison(raw):
    """Valida veneno custom (Fase H). Gera DUAS coisas no merge: a entrada de
    VENENOS (definição do efeito, via _custom_poison_defn) e o item de bolsa
    'coat_poison' que unta a arma. Convenção dos nativos: o MESMO id serve aos dois.
    _aplicar_veneno é data-driven nas 5 operações — o motor não muda."""
    iid = str(raw.get("id") or "").strip().lower()
    if not iid or not all(c.isalnum() or c == "_" for c in iid):
        return False, "id use apenas letras, números e _"
    name = str(raw.get("name") or "").strip()[:60]
    if not name:
        return False, "informe o nome do veneno"
    native = {i["id"] for shop in (SHOP_MERCHANT, SHOP_TEMPLE, SHOP_TAVERN)
              for i in shop if not i.get("custom")}
    native |= {k for k, v in VENENOS.items() if not v.get("custom")}
    if iid in native:
        return False, "o id não pode substituir um item nativo"
    op = raw.get("operacao")
    if op not in _ITEM_POISON_OPS:
        return False, "efeito de veneno inválido"
    def _int0(v):
        try: return int(v or 0)
        except (TypeError, ValueError): return 0
    def _dur(v, padrao="1d4"):
        """Duração/valor: aceita dado NdX ou int >= 1."""
        if isinstance(v, bool):
            return padrao
        if isinstance(v, int):
            return max(1, v)
        return str(v).lower() if _die_ok(v) else padrao
    def _pares(lista):
        out = []
        for par in (lista or []):
            if isinstance(par, (list, tuple)) and len(par) == 2 and par[0] in _ITEM_POISON_PENS:
                out.append([par[0], -abs(_int0(par[1]))])
        return out
    classes = [c for c in (raw.get("allowed_classes") or []) if c in _ITEM_CLASSES]
    try: price = max(0, int(raw.get("price", 0)))
    except (TypeError, ValueError): price = 0
    disp = raw.get("disponibilidade") or {}
    save = raw.get("save") if raw.get("save") in _ITEM_POISON_SAVES else "fortitude"
    item = {
        "id": iid, "name": name, "emoji": str(raw.get("emoji") or "☠️")[:8],
        "item_type": "poison", "item_slot": "bag", "effect": "coat_poison", "custom": True,
        "operacao": op, "save": save,
        "dificuldade": max(1, min(40, _int0(raw.get("dificuldade", 10)) or 10)),
        "anula": bool(raw.get("anula", True)),
        "duracao": _dur(raw.get("duracao"), "1d4"),
        "allowed_classes": classes, "price": price,
        "disponibilidade": {"loja": bool(disp.get("loja")), "baus": bool(disp.get("baus")),
                             "loot_monstro": bool(disp.get("loot_monstro"))},
    }
    desc = str(raw.get("descricao") or "").strip()[:160]
    if desc:
        item["descricao"] = desc
    if op == "dano":
        item["dano"] = _dur(raw.get("dano"), "1d4")
        if raw.get("save_neutraliza_por_rodada"):
            item["save_neutraliza_por_rodada"] = True
        else:
            item["save_aplicacao"] = True
    elif op == "reduzir":
        if raw.get("atributo") not in _ITEM_POISON_ATTRS:
            return False, "atributo de veneno inválido"
        item["atributo"] = raw["atributo"]
        item["valor"] = _dur(raw.get("valor"), "1d4")
    elif op == "penalidade":
        pares = _pares(raw.get("atributos"))
        if not pares:
            return False, "informe ao menos uma penalidade válida"
        item["atributos"] = pares
    else:   # petrificar | cegar
        item["duracao_falha"] = _dur(raw.get("duracao_falha"), "1d4")
        item["penalidade_falha"] = _pares(raw.get("penalidade_falha"))
        if op == "cegar":
            item["penalidade_ataque"] = -abs(_int0(raw.get("penalidade_ataque", -4)) or 4)
            item["bloqueia_distancia"] = bool(raw.get("bloqueia_distancia"))
    return True, item
```
Note: `SHOP_MERCHANT`, `SHOP_TEMPLE`, `SHOP_TAVERN`, `VENENOS`, `_ITEM_CLASSES`, `_die_ok` e os sets de 3a já são module-level. Se algum faltar, pare e reporte NEEDS_CONTEXT.

- [ ] **Step 4: Rodar e ver passar**

Use o comando de import direto chamando `m.test_validacao_veneno()`.
Expected: `[H1]` totalmente verde (0 falharam).

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Hunks: os 4 sets, o ramo em `_validate_custom_item`, a função `_validate_custom_poison`.

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# montar /tmp/mine.patch só com esses hunks, então:
git apply --cached /tmp/mine.patch
git diff --cached -- server.py
git commit -m "feat(itens): validação de venenos custom (5 operações)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Servidor — merge em VENENOS + uso ponta-a-ponta

**Files:**
- Modify: `server.py` (`_custom_poison_defn`, `_custom_poison_inventory_dict`, cleanup + ramo em `_apply_custom_items`)
- Test: `tools/test_editor_itens.py`

- [ ] **Step 1: Escrever os testes que falham**

Em `tools/test_editor_itens.py`, adicione após `test_validacao_veneno`:

```python
def test_veneno_merge():
    print("\n[H2] Merge de veneno (VENENOS + lojas)")
    ok, it = S._validate_custom_item(poison_sample(
        disponibilidade={"loja": True, "baus": True, "loot_monstro": True}))
    S._apply_custom_items([it])
    check("entra em VENENOS", "veneno_teste" in S.VENENOS)
    check("defn carrega operacao/dificuldade",
          S.VENENOS.get("veneno_teste", {}).get("operacao") == "dano"
          and S.VENENOS["veneno_teste"].get("dificuldade") == 12)
    check("defn usa 'nome' (formato nativo)", S.VENENOS.get("veneno_teste", {}).get("nome") == "Veneno Teste")
    check("loja: entra em SHOP_MERCHANT", any(i["id"] == "veneno_teste" for i in S.SHOP_MERCHANT))
    _inv = next(i for i in S.SHOP_MERCHANT if i["id"] == "veneno_teste")
    check("item aponta veneno_id", _inv.get("veneno_id") == "veneno_teste")
    check("item carrega efeito p/ tooltip",
          (_inv.get("efeito") or {}).get("dificuldade") == 12
          and (_inv.get("efeito") or {}).get("save") == "fortitude")
    check("item carrega descricao", _inv.get("descricao") == "Dói.")
    check("baus: entra em _DUNGEON_ITEM_CATALOG", "veneno_teste" in S._DUNGEON_ITEM_CATALOG)
    check("loot: entra em LOOT_POOL_PROCEDURAL", "veneno_teste" in S.LOOT_POOL_PROCEDURAL)
    check("nativo VENENOS intacto", "veneno_fungo_acre" in S.VENENOS)
    S._apply_custom_items([it])
    check("reaplicar nao duplica em SHOP_MERCHANT",
          sum(1 for i in S.SHOP_MERCHANT if i["id"] == "veneno_teste") == 1)
    S._apply_custom_items([])
    check("lista vazia remove de VENENOS", "veneno_teste" not in S.VENENOS)
    check("lista vazia remove de SHOP_MERCHANT", not any(i["id"] == "veneno_teste" for i in S.SHOP_MERCHANT))
    check("nativos de VENENOS sobrevivem ao clear", "veneno_fungo_acre" in S.VENENOS)

def test_veneno_uso():
    print("\n[H3] Untar a arma e envenenar no acerto")
    ok, it = S._validate_custom_item(poison_sample(dificuldade=40))   # CD 40 → alvo sempre falha
    S._apply_custom_items([it])
    r, p = _room_com_alvo()
    p["weapon"] = {"id": "wt", "name": "Lâmina", "die": "1d8", "stat": "str_",
                   "categoria": "cortante", "poison_slots": []}
    p["bag"] = [dict(S._custom_poison_inventory_dict(it))]
    asyncio.run(r.handle_use_item("p1", "veneno_teste"))
    check("arma recebeu carga de veneno", r._weapon_poison_slots(p) == ["veneno_teste"])
    check("frasco consumido", not any(i["id"] == "veneno_teste" for i in p["bag"]))
    import random; random.seed(99)
    asyncio.run(r.handle_attack("p1", "m1"))
    efeitos = r.monsters["m1"].get("efeitos_veneno", [])
    check("alvo envenenado no acerto", any(e.get("nome") == "Veneno Teste" for e in efeitos))
    check("carga consumida", r._weapon_poison_slots(p) == [])
    S._apply_custom_items([])

def test_veneno_efeitos():
    print("\n[H4] Efeitos de reduzir e cegar")
    # reduzir: derruba o atributo do alvo (CD 40 garante falha)
    okr, itr = S._validate_custom_item(poison_sample(id="veneno_red", operacao="reduzir",
        atributo="forca", valor="1d4", dificuldade=40))
    S._apply_custom_items([itr])
    r, p = _room_com_alvo()
    alvo = r.monsters["m1"]
    alvo["penalidades"] = {}
    asyncio.run(r._aplicar_veneno(alvo, "veneno_red"))
    check("reduzir registra efeito", any(e.get("operacao") == "reduzir"
          for e in alvo.get("efeitos_veneno", [])))
    # cegar: liga o status e a penalidade de ataque
    okc, itc = S._validate_custom_item(poison_sample(id="veneno_ceg", operacao="cegar",
        anula=False, dificuldade=40, penalidade_ataque=-4, bloqueia_distancia=True))
    S._apply_custom_items([itc])
    r2, p2 = _room_com_alvo()
    alvo2 = r2.monsters["m1"]
    alvo2["penalidades"] = {}
    asyncio.run(r2._aplicar_veneno(alvo2, "veneno_ceg"))
    check("cegar liga o status", alvo2.get("cego") is True)
    check("cegar aplica penalidade de ataque", alvo2["penalidades"].get("ataque") == -4)
    check("cegar bloqueia distancia", alvo2.get("bloqueia_distancia") is True)
    S._apply_custom_items([])
```

Registre no `if __name__ == "__main__":`, logo APÓS `test_validacao_veneno()`:

```python
    test_veneno_merge(); test_veneno_uso(); test_veneno_efeitos()
```

- [ ] **Step 2: Rodar e ver falhar**

Import direto, chamando as três funções.
Expected: FAIL — `_custom_poison_inventory_dict` não existe; veneno não entra em `VENENOS`.

- [ ] **Step 3: Implementar em `server.py`**

3a. Adicione as duas funções imediatamente após `_custom_throwable_inventory_dict`:

```python
def _custom_poison_defn(item):
    """Entrada de VENENOS para um veneno custom (formato nativo: 'nome'/'icone').
    'custom' marca o registro p/ o cleanup idempotente em _apply_custom_items."""
    defn = {"nome": item["name"], "icone": item["emoji"], "operacao": item["operacao"],
            "save": item["save"], "dificuldade": item["dificuldade"],
            "anula": item["anula"], "duracao": item["duracao"], "custom": True}
    op = item["operacao"]
    if op == "dano":
        defn["dano"] = item["dano"]
        if item.get("save_neutraliza_por_rodada"):
            defn["save_neutraliza_por_rodada"] = True
        else:
            defn["save_aplicacao"] = True
    elif op == "reduzir":
        defn["atributo"] = item["atributo"]
        defn["valor"] = item["valor"]
    elif op == "penalidade":
        defn["atributos"] = [list(par) for par in item["atributos"]]
    else:   # petrificar | cegar
        defn["duracao_falha"] = item["duracao_falha"]
        defn["penalidade_falha"] = [list(par) for par in item["penalidade_falha"]]
        if op == "cegar":
            defn["penalidade_ataque"] = item["penalidade_ataque"]
            defn["bloqueia_distancia"] = item["bloqueia_distancia"]
    return defn

def _custom_poison_inventory_dict(item):
    """Veneno custom — frasco de bolsa/loja (effect 'coat_poison'). 'efeito' e
    'descricao' alimentam o tooltip do cliente, que já os lê do próprio item."""
    inv = {"id": item["id"], "name": item["name"], "emoji": item["emoji"],
           "item_slot": "bag", "effect": "coat_poison", "value": 0,
           "veneno_id": item["id"], "custom": True, "price": item["price"],
           "efeito": {"save": item["save"], "dificuldade": item["dificuldade"],
                       "anula": item["anula"]}}
    if item.get("descricao"):
        inv["descricao"] = item["descricao"]
    if item["allowed_classes"]:
        inv["allowed_classes"] = list(item["allowed_classes"])
    return inv
```

3b. Em `_apply_custom_items`, logo APÓS o bloco de cleanup dos arremessáveis (as linhas com `ARREMESSAVEIS.pop(k, None)`), adicione:

```python
    # Venenos custom vivem no dict VENENOS (mesmo padrão de ARREMESSAVEIS).
    for k in [k for k, v in VENENOS.items() if v.get("custom")]:
        VENENOS.pop(k, None)
```

3c. No laço `for raw in records:`, adicione o ramo imediatamente APÓS o ramo de arremessável (`if it == "throwable": ... continue`):

```python
        if it == "poison":
            disp = item["disponibilidade"]
            VENENOS[item["id"]] = _custom_poison_defn(item)
            inv = _custom_poison_inventory_dict(item)
            if disp["loja"]:
                SHOP_MERCHANT.append(inv)
            if disp["baus"] or disp["loot_monstro"]:
                _DUNGEON_ITEM_CATALOG[item["id"]] = inv
            if disp["loot_monstro"]:
                LOOT_POOL_PROCEDURAL.append(item["id"])
            continue
```

- [ ] **Step 4: Rodar e ver passar**

Import direto, chamando `m.test_veneno_merge(); m.test_veneno_uso(); m.test_veneno_efeitos()`.
Expected: `[H2]`–`[H4]` verdes (0 falharam). Rode também `m.test_validacao_veneno()` para confirmar que `[H1]` não regrediu.

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Hunks: as 2 funções novas, o cleanup de `VENENOS` e o ramo `if it == "poison"`.

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# montar /tmp/mine.patch só com esses hunks, então:
git apply --cached /tmp/mine.patch
git diff --cached -- server.py
git commit -m "feat(itens): merge de venenos custom em VENENOS e no mercador

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: Servidor — mensagem de penalidade com os valores reais

**Files:**
- Modify: `server.py` (`_aplicar_veneno`, ramo `elif op == "penalidade"`, ~15037)
- Test: `tools/test_editor_itens.py`

Esta é a **única** mudança fora da região de itens custom. Ao extrair o patch, confira a vizinhança de hunks do WIP nessa área antes de aplicar.

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_editor_itens.py`, adicione após `test_veneno_efeitos`:

```python
def test_veneno_msg_penalidade():
    print("\n[H5] Mensagem de penalidade reflete os valores reais")
    ok, it = S._validate_custom_item(poison_sample(id="veneno_pen2", operacao="penalidade",
        atributos=[["ataque", -3], ["ca", -2]], dificuldade=40))
    S._apply_custom_items([it])
    r, p = _room_com_alvo()
    falas = []
    async def cap(msg): falas.append(msg)
    r.gm_say = cap
    alvo = r.monsters["m1"]
    alvo["penalidades"] = {}
    asyncio.run(r._aplicar_veneno(alvo, "veneno_pen2"))
    txt = " ".join(falas)
    check("mensagem cita -3 ataque", "-3 ataque" in txt)
    check("mensagem cita -2 ca", "-2 ca" in txt)
    check("mensagem nao usa o texto fixo antigo", "-1 ataque e -1 movimento" not in txt)
    check("penalidades aplicadas de fato",
          alvo["penalidades"].get("ataque") == -3 and alvo["penalidades"].get("ca") == -2)
    S._apply_custom_items([])
```

Registre no `if __name__ == "__main__":`, após `test_veneno_merge(); test_veneno_uso(); test_veneno_efeitos()`:

```python
    test_veneno_msg_penalidade()
```

- [ ] **Step 2: Rodar e ver falhar**

Import direto chamando `m.test_veneno_msg_penalidade()`.
Expected: FAIL — a mensagem atual é fixa ("-1 ataque e -1 movimento"), então "-3 ataque" não aparece.

- [ ] **Step 3: Implementar em `server.py`**

No ramo `elif op == "penalidade":` de `_aplicar_veneno`, a última linha é hoje:

```python
            await self.gm_say(f"☠️ **{nome}**: -1 ataque e -1 movimento em **{alvo_nome}** por {duracao} rodada(s).")
```

Substitua por (montando o texto a partir dos pares reais):

```python
            _txt = ", ".join(f"{val:+d} {attr}" for attr, val in atribs) or "sem efeito"
            await self.gm_say(f"☠️ **{nome}**: {_txt} em **{alvo_nome}** por {duracao} rodada(s).")
```
Note: `atribs` já existe algumas linhas acima, no mesmo ramo (`atribs = [(attr, val * dobro) for attr, val in veneno.get("atributos", [])]`). O formato `{val:+d}` imprime `-3` (valores já são negativos).

- [ ] **Step 4: Rodar e ver passar**

Import direto chamando `m.test_veneno_msg_penalidade()`.
Expected: `[H5]` verde. Rode também `m.test_validacao_veneno(); m.test_veneno_merge(); m.test_veneno_uso(); m.test_veneno_efeitos()` para confirmar que nada regrediu.

- [ ] **Step 5: Commit (partial staging — ver receita no topo)**

Hunk único, em `_aplicar_veneno`. **Confirme que o hunk staged contém só a mudança da mensagem.**

```bash
git add tools/test_editor_itens.py
git diff -- server.py > /tmp/all.patch
# montar /tmp/mine.patch só com o hunk da mensagem, então:
git apply --cached /tmp/mine.patch
git diff --cached -- server.py
git commit -m "fix(venenos): mensagem de penalidade usa os valores reais do efeito

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Editor — destravar sub-aba Venenos

**Files:**
- Modify: `tools/editor_items_editor.js`

Sem teste headless. Verificação: parse + node verde. Leia o arquivo antes para confirmar os nomes reusados (`TYPES`, `novoDraftThrowable`, `novoDraftFor`, `renderForm`, `seccao`/`campo`/`numInput`/`chk`/`chkLbl`/`esc`/`selectOpts`, `CLASSES`, `previewFn`, `root`, `draft`, `artFile`, `artURL`, `L`). Se algum diferir, pare e reporte NEEDS_CONTEXT.

- [ ] **Step 1: Destravar a sub-aba**

Troque `["venenos","Venenos",false]];` por `["venenos","Venenos",true]];`.

- [ ] **Step 2: Draft + roteamento**

2a. Adicione após `novoDraftThrowable`:
```javascript
  function novoDraftPoison() {
    return { name:"", emoji:"☠️", item_type:"poison", operacao:"dano", descricao:"",
      save:"fortitude", dificuldade:12, anula:true, dur_qtd:1, dur_faces:6,
      dano_fixo:false, dano_valor:1, dano_qtd:1, dano_faces:4, modelo_save:"aplicacao",
      atributo:"forca", val_qtd:1, val_faces:4,
      atributos:[{chave:"ataque", valor:1}],
      durfalha_qtd:1, durfalha_faces:4, penalidade_falha:[{chave:"movimento", valor:1}],
      penalidade_ataque:4, bloqueia_distancia:false,
      allowed_classes:[], disponibilidade:{loja:true,baus:false,loot_monstro:false}, price:0, id:"" };
  }
```
2b. Em `novoDraftFor`, antes do `return novoDraft();`:
```javascript
    if (type === "venenos") return novoDraftPoison();
```

- [ ] **Step 3: Dispatch em `renderForm`**

Após o dispatch de `arremessaveis`:
```javascript
    if (activeType === "venenos") { renderPoisonForm(f); return; }
```

- [ ] **Step 4: Form + linhas de penalidade + leitura + preview + bind + save**

Adicione após `onSaveThrowable`:
```javascript
  var POISON_OP_LABELS = { dano:"Dano por rodada", reduzir:"Reduzir atributo",
    penalidade:"Penalidade (ataque/movimento/…)", petrificar:"Petrificar", cegar:"Cegar" };
  var POISON_ATTR_LABELS = { forca:"Força", constituicao:"Constituição",
    destreza:"Destreza", inteligencia:"Inteligência" };
  var POISON_PEN_LABELS = { ataque:"Ataque", movimento:"Movimento", dano:"Dano",
    ca:"CA", percepcao:"Percepção" };

  // Linhas dinâmicas de penalidade (chave + valor). `cls` separa as duas listas
  // (penalidade da operação × penalidade do save parcial) no mesmo formulário.
  function penRowsHTML(cls, lista) {
    var opts = (L.POISON_PENS || []).map(function (k) {
      return '<option value="' + k + '">' + esc(POISON_PEN_LABELS[k] || k) + '</option>'; }).join("");
    var linhas = (lista || []).map(function (o) {
      return '<span class="ie-elem-row ' + cls + '-row">' +
        '<select class="' + cls + '-k">' + opts + '</select> −' +
        '<input type="number" class="' + cls + '-v" value="' + (Math.abs(+o.valor) || 1) + '" min="1" max="20">' +
        ' <button class="' + cls + '-del">✕</button></span>'; }).join("");
    return '<div class="' + cls + '-box">' + linhas + '</div>' +
      '<button class="' + cls + '-add">+ penalidade</button>';
  }

  function renderPoisonForm(f) {
    var op = draft.operacao;
    var faces = [4,6,8,10,12];
    var dieSel = function (id, sel) {
      return '<select id="' + id + '">' + faces.map(function (x) {
        return '<option' + (x === sel ? " selected" : "") + '>' + x + '</option>'; }).join("") + '</select>'; };
    var blocos = "";
    if (op === "dano") {
      blocos = seccao("Dano por rodada",
        campo("Valor fixo (em vez de dado)", chk("ie-danofixo", draft.dano_fixo)) +
        (draft.dano_fixo ? campo("Dano", numInput("ie-danoval", draft.dano_valor, 1, 99))
          : campo("Quantidade", numInput("ie-danoq", draft.dano_qtd, 1, 10)) +
            campo("Dado", dieSel("ie-danof", draft.dano_faces))) +
        campo("Modelo de resistência", '<select id="ie-modelosave">' +
          '<option value="aplicacao"' + (draft.modelo_save === "rodada" ? "" : " selected") + '>Testa 1× ao aplicar</option>' +
          '<option value="rodada"' + (draft.modelo_save === "rodada" ? " selected" : "") + '>Testa a cada rodada (neutraliza)</option></select>'));
    } else if (op === "reduzir") {
      blocos = seccao("Redução de atributo",
        campo("Atributo", '<select id="ie-patributo">' + (L.POISON_ATTRS || []).map(function (a) {
          return '<option value="' + a + '"' + (a === draft.atributo ? " selected" : "") + '>' + esc(POISON_ATTR_LABELS[a] || a) + '</option>'; }).join("") + '</select>') +
        campo("Quantidade", numInput("ie-valq", draft.val_qtd, 1, 10)) +
        campo("Dado", dieSel("ie-valf", draft.val_faces)) +
        '<span class="ie-hint">Constituição recalcula PV máximo e Fortitude automaticamente.</span>');
    } else if (op === "penalidade") {
      blocos = seccao("Penalidades", penRowsHTML("iepen", draft.atributos));
    } else {
      blocos = seccao("Sucesso parcial (save bem-sucedido)",
        campo("Duração (quantidade)", numInput("ie-durfq", draft.durfalha_qtd, 1, 10)) +
        campo("Duração (dado)", dieSel("ie-durff", draft.durfalha_faces)) +
        penRowsHTML("iepf", draft.penalidade_falha)) +
        (op === "cegar" ? seccao("Cegueira",
          campo("Penalidade de ataque (−)", numInput("ie-penatk", draft.penalidade_ataque, 1, 20)) +
          campo("Bloqueia ataques à distância", chk("ie-bloqdist", draft.bloqueia_distancia))) : "");
    }
    f.innerHTML = [
      seccao("Identidade",
        campo("Nome", '<input id="ie-name" value="' + esc(draft.name) + '">') +
        campo("Ícone", '<input id="ie-emoji" size="3" value="' + esc(draft.emoji) + '">') +
        campo("Descrição (tooltip)", '<input id="ie-desc" value="' + esc(draft.descricao) + '">')),
      seccao("Efeito",
        campo("Tipo", '<select id="ie-pop">' + (L.POISON_OPS || []).map(function (o) {
          return '<option value="' + o + '"' + (o === op ? " selected" : "") + '>' + esc(POISON_OP_LABELS[o] || o) + '</option>'; }).join("") + '</select>')),
      seccao("Resistência",
        campo("Save", '<select id="ie-psave">' + (L.POISON_SAVES || []).map(function (s) {
          return '<option value="' + s + '"' + (s === draft.save ? " selected" : "") + '>' + esc(s) + '</option>'; }).join("") + '</select>') +
        campo("CD", numInput("ie-pcd", draft.dificuldade, 1, 40)) +
        campo("Sucesso anula o efeito", chk("ie-panula", draft.anula))),
      seccao("Duração",
        campo("Quantidade", numInput("ie-durq", draft.dur_qtd, 1, 10)) +
        campo("Dado", dieSel("ie-durf", draft.dur_faces))),
      blocos,
      seccao("Restrição de classe (vazio = todas)",
        CLASSES.map(function (c) { return '<label class="ie-cls">' +
          '<input type="checkbox" class="ie-class" value="' + c[0] + '"> ' + esc(c[1]) + '</label>'; }).join("")),
      seccao("Disponibilidade",
        chkLbl("ie-disp-loja", "Loja (Mercador)", draft.disponibilidade.loja) +
        chkLbl("ie-disp-baus", "Baús / recompensas", draft.disponibilidade.baus) +
        chkLbl("ie-disp-loot", "Loot de monstro", draft.disponibilidade.loot_monstro)),
      seccao("Preço",
        campo("Ouro", numInput("ie-price", draft.price, 0, 99999)) +
        '<span id="ie-price-sug" class="ie-hint"></span>'),
      seccao("Imagem",
        '<input type="file" id="ie-art" accept="image/png"> ' +
        '<span id="ie-art-name" class="ie-hint"></span>'),
      '<div class="ie-actions"><button id="ie-save">💾 Salvar veneno</button>' +
        '<span id="ie-status" class="ie-hint"></span></div>',
    ].join("");
    // Restaura os selects de chave das linhas de penalidade (o HTML não os marca).
    ["iepen", "iepf"].forEach(function (cls) {
      var fonte = cls === "iepen" ? draft.atributos : draft.penalidade_falha;
      root.querySelectorAll("." + cls + "-row").forEach(function (row, i) {
        var sel = row.querySelector("." + cls + "-k");
        if (sel && fonte && fonte[i]) sel.value = fonte[i].chave;
      });
    });
    previewFn = renderPoisonPreview;
    bindPoisonForm();
    renderPoisonPreview();
  }

  function lerPenRows(cls) {
    return Array.prototype.map.call(root.querySelectorAll("." + cls + "-row"), function (row) {
      return { chave: row.querySelector("." + cls + "-k").value,
               valor: Math.abs(+row.querySelector("." + cls + "-v").value || 1) };
    });
  }

  function currentPoisonDraftFromForm() {
    var g = function (id) { return root.querySelector("#" + id); };
    draft.name = g("ie-name").value; draft.emoji = g("ie-emoji").value;
    draft.descricao = g("ie-desc").value;
    draft.operacao = g("ie-pop").value;
    draft.save = g("ie-psave").value;
    draft.dificuldade = Math.max(1, Math.min(40, +g("ie-pcd").value || 10));
    draft.anula = g("ie-panula").checked;
    draft.dur_qtd = Math.max(1, +g("ie-durq").value || 1);
    draft.dur_faces = +g("ie-durf").value || 4;
    var df = g("ie-danofixo"); if (df) draft.dano_fixo = df.checked;
    var dv = g("ie-danoval"); if (dv) draft.dano_valor = Math.max(1, +dv.value || 1);
    var dq = g("ie-danoq"); if (dq) draft.dano_qtd = Math.max(1, +dq.value || 1);
    var dfa = g("ie-danof"); if (dfa) draft.dano_faces = +dfa.value || 4;
    var ms = g("ie-modelosave"); if (ms) draft.modelo_save = ms.value;
    var at = g("ie-patributo"); if (at) draft.atributo = at.value;
    var vq = g("ie-valq"); if (vq) draft.val_qtd = Math.max(1, +vq.value || 1);
    var vf = g("ie-valf"); if (vf) draft.val_faces = +vf.value || 4;
    if (root.querySelector(".iepen-box")) draft.atributos = lerPenRows("iepen");
    if (root.querySelector(".iepf-box")) draft.penalidade_falha = lerPenRows("iepf");
    var dfq = g("ie-durfq"); if (dfq) draft.durfalha_qtd = Math.max(1, +dfq.value || 1);
    var dff = g("ie-durff"); if (dff) draft.durfalha_faces = +dff.value || 4;
    var pa = g("ie-penatk"); if (pa) draft.penalidade_ataque = Math.max(1, +pa.value || 4);
    var bd = g("ie-bloqdist"); if (bd) draft.bloqueia_distancia = bd.checked;
    draft.allowed_classes = Array.prototype.map.call(root.querySelectorAll(".ie-class:checked"), function (c) { return c.value; });
    draft.disponibilidade = { loja: g("ie-disp-loja").checked, baus: g("ie-disp-baus").checked, loot_monstro: g("ie-disp-loot").checked };
    draft.price = +g("ie-price").value || 0;
    return draft;
  }

  function renderPoisonPreview() {
    currentPoisonDraftFromForm();
    var item = L.serializePoison(draft);
    root.querySelector("#ie-price-sug").textContent = "sugerido: " + L.suggestPricePoison(item) + " 🪙";
    var parts = [POISON_OP_LABELS[item.operacao] || item.operacao,
                 item.save + " CD " + item.dificuldade + (item.anula ? " (anula)" : " (parcial)"),
                 "dura " + item.duracao];
    if (item.dano) parts.push("dano " + item.dano);
    if (item.atributo) parts.push("−" + item.valor + " " + (POISON_ATTR_LABELS[item.atributo] || item.atributo));
    if (item.atributos && item.atributos.length)
      parts.push(item.atributos.map(function (p) { return p[1] + " " + p[0]; }).join(", "));
    if (item.penalidade_ataque) parts.push(item.penalidade_ataque + " ataque (cego)");
    var topo = artURL ? '<img class="ie-card-img" src="' + artURL + '" alt="">'
      : '<div class="ie-card-emoji">' + esc(item.emoji) + '</div>';
    root.querySelector("#ie-preview").innerHTML =
      '<div class="ie-card">' + topo +
      '<div class="ie-card-name">' + esc(item.name || "(sem nome)") + '</div>' +
      '<div class="ie-card-stats">' + esc(parts.join(" · ")) + '</div>' +
      '<div class="ie-card-id">id: ' + esc(item.id) + '</div></div>';
  }

  function bindPoisonForm() {
    root.querySelectorAll("#ie-form input,#ie-form select").forEach(function (el) {
      if (el.id === "ie-art") return;
      el.onchange = renderPoisonPreview; el.oninput = renderPoisonPreview;
    });
    // Trocar a operação (ou o modo do dano) troca QUAIS campos existem.
    ["ie-pop", "ie-danofixo"].forEach(function (id) {
      var el = root.querySelector("#" + id);
      if (el) el.onchange = function () { currentPoisonDraftFromForm(); renderPoisonForm(root.querySelector("#ie-form")); };
    });
    // Linhas de penalidade: adicionar/remover re-renderiza o form.
    ["iepen", "iepf"].forEach(function (cls) {
      var add = root.querySelector("." + cls + "-add");
      if (add) add.onclick = function () {
        currentPoisonDraftFromForm();
        var alvo = cls === "iepen" ? "atributos" : "penalidade_falha";
        draft[alvo] = (draft[alvo] || []).concat([{ chave: "ataque", valor: 1 }]);
        renderPoisonForm(root.querySelector("#ie-form"));
      };
      root.querySelectorAll("." + cls + "-del").forEach(function (btn, i) {
        btn.onclick = function () {
          currentPoisonDraftFromForm();
          var alvo = cls === "iepen" ? "atributos" : "penalidade_falha";
          draft[alvo] = (draft[alvo] || []).filter(function (_, j) { return j !== i; });
          renderPoisonForm(root.querySelector("#ie-form"));
        };
      });
    });
    (draft.allowed_classes || []).forEach(function (c) {
      var el = root.querySelector('.ie-class[value="' + c + '"]'); if (el) el.checked = true; });
    root.querySelector("#ie-art").onchange = function (e) {
      artFile = e.target.files[0] || null;
      if (artURL) { URL.revokeObjectURL(artURL); artURL = null; }
      if (artFile) artURL = URL.createObjectURL(artFile);
      root.querySelector("#ie-art-name").textContent = artFile ? artFile.name : "";
      renderPoisonPreview();
    };
    root.querySelector("#ie-save").onclick = onSavePoison;
  }

  async function onSavePoison() {
    currentPoisonDraftFromForm();
    var v = L.validatePoisonDraft(draft);
    var status = root.querySelector("#ie-status");
    if (!v.ok) { status.textContent = "⚠️ " + v.msg; return; }
    var item = L.serializePoison(draft);
    status.textContent = "salvando…";
    try {
      if (artFile) { await window.EDITOR_SAVE.uploadItemArt(artFile, item.id); }
      var saved = await window.EDITOR_SAVE.saveCustomItem(item);
      status.textContent = "✅ salvo: " + saved.id;
      window.EDITOR_CUSTOM_ITEMS = (window.EDITOR_CUSTOM_ITEMS || []).filter(function (r) { return r.id !== saved.id; });
      window.EDITOR_CUSTOM_ITEMS.push(saved);
    } catch (e) { status.textContent = "❌ " + (e && e.message || "falha ao salvar"); }
  }
```

- [ ] **Step 5: Verificar e commitar**

Run: `node -e "new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('parse OK')"`
Expected: `parse OK`

Run: `node tools/test_editor_items_logic.js`
Expected: PASS.

```bash
git add tools/editor_items_editor.js
git commit -m "feat(itens): editor destrava sub-aba Venenos (fecha as 8 sub-abas)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Verificação isolada + docs + memória

**Files:**
- Modify: `CLAUDE.md`
- Modify (fora do repo): memória em `C:\Users\RICARDO\.claude\projects\C--Users-RICARDO-Desktop-jogo-tabuleiro\memory\`

- [ ] **Step 1: Rodar a suíte no estado COMMITADO isolado**

```bash
git worktree add --detach /tmp/lfh_verify_h HEAD
cd /tmp/lfh_verify_h
python tools/test_editor_itens.py
node tools/test_editor_items_logic.js
node -e "new Function(require('fs').readFileSync('tools/editor_items_editor.js','utf8')); console.log('editor OK')"
cd "C:/Users/RICARDO/Desktop/jogo tabuleiro"
git worktree remove /tmp/lfh_verify_h --force
```
Expected: `[H1]`–`[H5]` verdes e node verde; nenhuma seção anterior quebrada. **Atenção:** o teste `tools/test_devorador.py` e `tools/test_roteamento_itens.py` têm falhas pré-existentes — não são desta fase. Rode também `python tools/test_editor_itens.py` esperando 0 falhas.

- [ ] **Step 2: Nota no `CLAUDE.md`**

Adicione um parágrafo de citação após a nota da Fase G resumindo a Fase H: sub-aba Venenos destravada (**fecha as 8 sub-abas**); as 5 operações (`dano` com os 2 modelos de save, `reduzir`, `penalidade`, `petrificar`, `cegar`); um id serve item e veneno (convenção nativa); `_validate_custom_poison` + `_custom_poison_defn` (entrada em `VENENOS` com cleanup próprio via `custom:True`) + `_custom_poison_inventory_dict` (com `veneno_id`/`descricao`/`efeito` p/ o tooltip); `_aplicar_veneno` intocado (data-driven); **cliente sem mudanças** (`coat_poison` é genérico); e o fix da mensagem de `penalidade`. Cite os arquivos e o teste `[H1]`–`[H5]`.

- [ ] **Step 3: Commit docs**

```bash
git add CLAUDE.md docs/superpowers/plans/2026-07-26-editor-itens-fase-h-venenos.md
git commit -m "docs(itens): registra o Editor de Itens — Fase H (venenos)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

- [ ] **Step 4: Atualizar memória**

Crie `memory/editor-itens-fase-h-venenos.md` (tipo `project`): o que foi feito, estado (branch `feat/instrumentos-bardo-fase5`, não mergeada), contagem de checks, que esta fase **fecha as 8 sub-abas do Editor de Itens**, e o follow-up de smoke in-app. Adicione a linha-índice no topo de `MEMORY.md`, linkando `[[editor-itens-fase-g-arremessaveis]]` e `[[lojas-por-cidade-itens-custom]]`.

- [ ] **Step 5: Follow-up manual (usuário)**

Smoke test in-app: `python server.py` → `tools/editor.html` → "Editor de itens" → sub-aba Venenos: criar um de dano (1d4/rodada, Fortitude CD 12) e um de cegar; salvar. Como o checkbox "Loja" está afetado pelo WIP de lojas por cidade, marcar **"Baús / recompensas"** para testar em jogo: pegar o frasco, usá-lo (ação bônus, unta a arma) e acertar um monstro para ver o veneno aplicado.

---

## Self-Review (autor do plano)

- **Cobertura do spec:** 4 sets novos (T2) ✓; `_validate_custom_poison` com as 5 operações, flags de save exclusivas, native-id incluindo `VENENOS` (T2) ✓; `_custom_poison_defn` com `custom:True` e formato nativo `nome`/`icone` (T3) ✓; `_custom_poison_inventory_dict` com `veneno_id`/`descricao`/`efeito` (T3) ✓; cleanup + merge (T3) ✓; retoque da mensagem de `penalidade` (T4) ✓; lógica pura + UI com blocos condicionais e linhas dinâmicas (T1/T5) ✓; testes [H1]–[H5] incl. ponta-a-ponta (T2/T3/T4) ✓; verificação isolada + docs + memória (T6) ✓; cliente sem mudanças (por design) ✓.
- **Nomes cliente × servidor:** o cliente emite `dur_qtd`/`dur_faces` etc. e o `serializePoison` já os converte para os campos do formato do servidor (`duracao`, `dano`, `valor`, `duracao_falha`) — o servidor recebe o item **já serializado**, então os nomes batem. Os testes do servidor usam o formato final (`duracao:"1d6"`), como o `serializePoison` produz.
- **Pares de penalidade:** o cliente produz `[["ataque",-2]]` (lista de listas, JSON-safe) e o servidor valida com `isinstance(par, (list, tuple))` — casa. O motor faz `for attr, val in ...`, que desempacota listas de 2.
- **CD 40 nos testes:** garante falha do save (o alvo `m1` é sintético, sem bônus altos), tornando `[H3]`/`[H4]`/`[H5]` determinísticos quanto ao efeito aplicado.
- **Sem placeholders:** todos os passos têm código/comando concreto.
