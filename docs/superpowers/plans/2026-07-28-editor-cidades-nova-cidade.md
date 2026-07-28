# Editor de Cidades — criar, editar e excluir cidades — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir, pela aba "Cidades" do editor, criar uma cidade nova (com upload da ilustração e posição no mapa-múndi), editar as existentes e excluí-las, com as rotas de viagem virando dados editáveis.

**Architecture:** As 4 cidades originais continuam declaradas em `server.py` (`WORLD_LOCATIONS`/`WORLD_ROUTES`) como base imutável; um arquivo novo `cidades_personalizadas.json` é uma camada por cima (adiciona / edita / remove), aplicada no boot por `_aplicar_estado_cidades()` — a mesma função usada pelo handler de save do editor, o que garante que arquivo e edição ao vivo produzam exatamente o mesmo estado. Lojas, pontos do mapa da cidade e cena de taverna são derivados: cada cidade em `WORLD_LOCATIONS` ganha uma entrada vazia, e cidades removidas têm a sua apagada.

**Tech Stack:** Python 3 + `websockets` (servidor); JS vanilla sem bundler (`tools/editor_city.js`, `tools/story_upload.js`); testes = scripts Python rodados da raiz.

**Spec:** `docs/superpowers/specs/2026-07-28-editor-cidades-nova-cidade-design.md`

---

## Contexto que o implementador precisa saber

- **Rodar o servidor:** `python server.py` (porta 8765, serve página + WebSocket). O editor abre em `http://localhost:8765/tools/editor.html`.
- **Rodar um teste:** sempre da raiz do projeto, ex. `python tools/test_cidades_editor.py`. Os testes deste projeto **não usam pytest** — são scripts que importam `server as S`, contam `PASS`/`FAIL` com uma função `check(nome, condicao)` e terminam com `sys.exit(1 if FAIL else 0)`. Siga esse formato (veja `tools/test_ficha_cidade.py` como modelo).
- **⚠️ O working tree tem trabalho em andamento do usuário** em `server.py`, `game.js`, `tools/editor.js` e outros. **Nunca** rode `git add -A`, `git add .` ou `git commit -a`. Sempre `git add <caminho exato>` dos arquivos daquela task.
- **Ordem de declaração em `server.py` importa muito** nesta feature. As posições relevantes hoje:
  - linha 41 `WORLD_LOCATIONS`, linha 51 `WORLD_ROUTES`
  - linha 62–88 pontos do mapa-múndi (`_load_world_map_points()`)
  - linha 182 `CITY_MAP_POINTS` + linha 233 `_load_city_map_points()`
  - linha 237 `TAVERN_SCENES` + linha 267 loop que copia a cena de Alva e Luz + linha 313 `_load_tavern_scenes()`
  - linha 4470 `CITY_SHOPS = _default_city_shops()` + linha 4495 `_load_city_shops()`
  - Os números de linha vão mudar conforme você edita; localize pelo nome do símbolo.

## Estrutura de arquivos

| Arquivo | Responsabilidade | Ação |
|---|---|---|
| `cidades_personalizadas.json` | Camada de dados: cidades criadas, edições nas originais, exclusões e custos de rota | Criado em runtime pelo servidor (não versionar conteúdo de exemplo) |
| `server.py` (bloco novo após `WORLD_ROUTES`) | Validação, aplicação e persistência do estado de cidades | Modificar |
| `server.py` (`CITY_MAP_POINTS`, `TAVERN_SCENES`) | Semear/podar subsistemas derivados por cidade | Modificar |
| `server.py` (`handle_world_travel`, `broadcast_city_state`) | Rota ausente = viagem grátis | Modificar |
| `server.py` (dispatch do editor, ~linha 21078) | Mensagens `upload_city_art` e `save_world_cities` | Modificar |
| `tools/story_upload.js` | API cliente `EDITOR_SAVE.uploadCityArt` / `saveWorldCities` | Modificar |
| `tools/editor_city.js` | Painel de cidade (criar/editar/excluir/rotas) + taverna vazia editável | Modificar |
| `tools/test_cidades_editor.py` | Testes do servidor desta feature | Criar |

---

### Task 1: Camada de dados das cidades (validação, aplicação, persistência)

**Files:**
- Modify: `server.py` — inserir um bloco novo logo **após** a declaração de `WORLD_ROUTES` (hoje termina na linha 58) e **antes** de `WORLD_MAP_POINTS_FILE`
- Test: `tools/test_cidades_editor.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Crie `tools/test_cidades_editor.py` com este conteúdo:

```python
"""Editor de cidades — criar, editar e excluir cidades pelo editor.
  • _aplicar_estado_cidades monta WORLD_LOCATIONS a partir das originais + edições.
  • Cidade nova nasce vazia (sem lojas, sem pontos de mapa, sem NPCs de taverna).
  • Rota sem custo definido = viagem grátis; par com custo debita o valor.
  • Excluir limpa os subsistemas derivados; Alva e Luz nunca é excluída.
Roda da raiz: python tools/test_cidades_editor.py"""
import asyncio, json, os, sys, tempfile
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

CIDADE_NOVA = {"id": "porto_negro", "nome": "Porto Negro", "tipo": "cidade",
               "imagem": "assets/city/porto_negro.png", "x": 60.1, "y": 44.0}

def reset_mundo():
    """Volta o mundo às 4 cidades originais, sem nenhuma edição do editor."""
    S._aplicar_estado_cidades([], {}, [], None)

def main():
    print("\n[1] Criar cidade")
    reset_mundo()
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [], None)
    check("cidade nova entra no mundo", "porto_negro" in S.WORLD_LOCATIONS)
    check("nome preservado", S.WORLD_LOCATIONS["porto_negro"]["nome"] == "Porto Negro")
    check("coordenadas preservadas", S.WORLD_LOCATIONS["porto_negro"]["x"] == 60.1)
    check("as 4 originais continuam", all(c in S.WORLD_LOCATIONS for c in
          ("alva_e_luz", "vila_riacho", "vila_corvin", "graciero")))

    print("\n[2] Editar cidade original (override)")
    reset_mundo()
    S._aplicar_estado_cidades([], {"graciero": {"nome": "Graciero Velho", "tipo": "vila",
                                                "imagem": "assets/city/novo.png"}}, [], None)
    check("nome editado", S.WORLD_LOCATIONS["graciero"]["nome"] == "Graciero Velho")
    check("tipo editado", S.WORLD_LOCATIONS["graciero"]["tipo"] == "vila")
    check("imagem editada", S.WORLD_LOCATIONS["graciero"]["imagem"] == "assets/city/novo.png")
    check("rota antiga intacta",
          S.WORLD_ROUTES[frozenset(("alva_e_luz", "graciero"))]["fome"] == 14)

    print("\n[3] Excluir cidade")
    reset_mundo()
    S._aplicar_estado_cidades([], {}, ["vila_corvin"], None)
    check("cidade removida do mundo", "vila_corvin" not in S.WORLD_LOCATIONS)
    check("rotas dela sumiram",
          not any("vila_corvin" in par for par in S.WORLD_ROUTES))
    reset_mundo()
    S._aplicar_estado_cidades([], {}, ["alva_e_luz"], None)
    check("Alva e Luz não pode ser excluída", "alva_e_luz" in S.WORLD_LOCATIONS)

    print("\n[4] Validação recusa entrada inválida")
    reset_mundo()
    S._aplicar_estado_cidades([{"id": "sem nome", "nome": "", "x": 10, "y": 10}], {}, [], None)
    check("id/nome inválidos recusados", len(S.WORLD_LOCATIONS) == 4)
    S._aplicar_estado_cidades([dict(CIDADE_NOVA, x=180)], {}, [], None)
    check("coordenada fora do mapa recusada", "porto_negro" not in S.WORLD_LOCATIONS)
    S._aplicar_estado_cidades([dict(CIDADE_NOVA, id="alva_e_luz")], {}, [], None)
    check("id duplicado não sobrescreve original",
          S.WORLD_LOCATIONS["alva_e_luz"]["nome"] == "Alva e Luz")

    print("\n[5] Round-trip pelo arquivo")
    reset_mundo()
    tmp = os.path.join(tempfile.gettempdir(), "cidades_teste.json")
    original_file = S.WORLD_CITIES_FILE
    S.WORLD_CITIES_FILE = tmp
    try:
        S._aplicar_estado_cidades([CIDADE_NOVA], {"graciero": {"nome": "Graciero Velho"}},
                                  ["vila_corvin"],
                                  [{"from": "porto_negro", "to": "alva_e_luz", "fome": 8, "sede": 8}])
        S._save_world_cities()
        reset_mundo()
        check("reset limpou a cidade nova", "porto_negro" not in S.WORLD_LOCATIONS)
        S._load_world_cities()
        check("cidade nova voltou do arquivo", "porto_negro" in S.WORLD_LOCATIONS)
        check("override voltou do arquivo", S.WORLD_LOCATIONS["graciero"]["nome"] == "Graciero Velho")
        check("exclusão voltou do arquivo", "vila_corvin" not in S.WORLD_LOCATIONS)
        check("rota voltou do arquivo",
              S.WORLD_ROUTES[frozenset(("porto_negro", "alva_e_luz"))]["sede"] == 8)
    finally:
        S.WORLD_CITIES_FILE = original_file
        if os.path.exists(tmp): os.remove(tmp)
        reset_mundo()

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

main()
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python tools/test_cidades_editor.py`
Expected: FAIL com `AttributeError: module 'server' has no attribute '_aplicar_estado_cidades'`

- [ ] **Step 3: Implementar o bloco de dados**

Em `server.py`, logo **depois** do fechamento de `WORLD_ROUTES` (a linha `}` que fecha o dict, hoje linha 58) e **antes** do comentário `# As posições são conteúdo do mapa…`, insira:

```python
# ─── CIDADES DO EDITOR ────────────────────────────────────────────────────────
# As 4 cidades acima são a base imutável. O editor grava uma camada por cima em
# cidades_personalizadas.json (cria, edita e remove), aplicada aqui no boot pela
# MESMA função usada pelo handler de save — arquivo e edição ao vivo convergem.
_BUILTIN_WORLD_LOCATIONS = deepcopy(WORLD_LOCATIONS)
_BUILTIN_WORLD_ROUTES = dict(WORLD_ROUTES)
CITY_INICIAL = "alva_e_luz"      # cidade de partida e fallback; nunca excluível
_CITY_TIPOS = ("cidade", "vila")
WORLD_CITIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cidades_personalizadas.json")
WORLD_CITIES = {"cities": [], "overrides": {}, "deleted": [], "routes": []}

def _cidade_valida(raw):
    """Valida um registro de cidade (do arquivo ou do editor).
    Retorna (True, dict_limpo) ou (False, mensagem)."""
    if not isinstance(raw, dict):
        return False, "cidade inválida"
    cid = str(raw.get("id") or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9_-]{1,48}", cid):
        return False, "id inválido"
    nome = str(raw.get("nome") or "").strip()
    if not nome:
        return False, "nome obrigatório"
    tipo = raw.get("tipo") if raw.get("tipo") in _CITY_TIPOS else "cidade"
    imagem = str(raw.get("imagem") or "")
    if imagem and not imagem.startswith("assets/"):
        return False, "imagem inválida"
    try:
        x, y = round(float(raw.get("x", 50)), 2), round(float(raw.get("y", 50)), 2)
    except (TypeError, ValueError):
        return False, "coordenadas inválidas"
    if not (0 <= x <= 100 and 0 <= y <= 100):
        return False, "coordenadas fora do mapa"
    return True, {"id": cid, "nome": nome[:60], "tipo": tipo, "imagem": imagem,
                  "x": x, "y": y, "servicos": bool(raw.get("servicos", True))}

def _override_valido(patch):
    """Edições permitidas numa cidade existente. Ignora campos desconhecidos."""
    limpo = {}
    if not isinstance(patch, dict):
        return limpo
    nome = str(patch.get("nome") or "").strip()
    if nome: limpo["nome"] = nome[:60]
    if patch.get("tipo") in _CITY_TIPOS: limpo["tipo"] = patch["tipo"]
    imagem = str(patch.get("imagem") or "")
    if imagem.startswith("assets/"): limpo["imagem"] = imagem
    return limpo

def _rota_valida(raw):
    """Retorna (frozenset(par), {"fome":n,"sede":n}) ou None. Exige as duas
    cidades já presentes em WORLD_LOCATIONS — chame depois de aplicá-las."""
    if not isinstance(raw, dict):
        return None
    a, b = str(raw.get("from") or ""), str(raw.get("to") or "")
    if a == b or a not in WORLD_LOCATIONS or b not in WORLD_LOCATIONS:
        return None
    try:
        fome, sede = max(0, int(raw.get("fome", 0))), max(0, int(raw.get("sede", 0)))
    except (TypeError, ValueError):
        return None
    return frozenset((a, b)), {"fome": fome, "sede": sede}

def _aplicar_estado_cidades(cities, overrides, deleted, routes):
    """Reconstrói WORLD_LOCATIONS/WORLD_ROUTES a partir das originais + edições.
    `routes=None` mantém a tabela de custos original (boot sem arquivo); uma
    lista substitui a tabela inteira (o editor sempre envia a tabela completa).
    Deixa em WORLD_CITIES o estado limpo que vai para o arquivo."""
    global WORLD_CITIES
    coords = {cid: (loc.get("x"), loc.get("y")) for cid, loc in WORLD_LOCATIONS.items()}
    limpo = {"cities": [], "overrides": {}, "deleted": [], "routes": []}
    WORLD_LOCATIONS.clear()
    for cid, base in _BUILTIN_WORLD_LOCATIONS.items():
        loc = deepcopy(base)
        if cid in coords:                      # preserva o arraste no mapa-múndi
            loc["x"], loc["y"] = coords[cid]
        WORLD_LOCATIONS[cid] = loc
    for row in list(cities or [])[:60]:
        ok, city = _cidade_valida(row)
        if not ok or city["id"] in WORLD_LOCATIONS:
            continue
        if city["id"] in coords:
            city["x"], city["y"] = coords[city["id"]]
        WORLD_LOCATIONS[city["id"]] = city
        limpo["cities"].append(city)
    for cid, patch in (overrides or {}).items():
        if cid not in WORLD_LOCATIONS:
            continue
        edicao = _override_valido(patch)
        if edicao:
            WORLD_LOCATIONS[cid].update(edicao)
            limpo["overrides"][cid] = edicao
    for cid in list(deleted or [])[:60]:
        cid = str(cid)
        if cid == CITY_INICIAL or cid not in WORLD_LOCATIONS:
            continue
        del WORLD_LOCATIONS[cid]
        if cid in _BUILTIN_WORLD_LOCATIONS:
            limpo["deleted"].append(cid)
        limpo["cities"] = [c for c in limpo["cities"] if c["id"] != cid]
        limpo["overrides"].pop(cid, None)
    novas_rotas = dict(_BUILTIN_WORLD_ROUTES) if routes is None else {}
    for row in list(routes or [])[:400]:
        rota = _rota_valida(row)
        if rota:
            novas_rotas[rota[0]] = rota[1]
    WORLD_ROUTES.clear()
    for par, custo in novas_rotas.items():
        if set(par) <= set(WORLD_LOCATIONS):   # rota de cidade excluída não sobra
            WORLD_ROUTES[par] = custo
            limpo["routes"].append({"from": tuple(par)[0], "to": tuple(par)[1], **custo})
    if routes is None:
        limpo["routes"] = []                   # nada a persistir: são as originais
    WORLD_CITIES = limpo

def _load_world_cities():
    """Aplica cidades_personalizadas.json sobre as cidades originais."""
    try:
        with open(WORLD_CITIES_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return
    if not isinstance(raw, dict):
        return
    rotas = raw.get("routes")
    _aplicar_estado_cidades(raw.get("cities"), raw.get("overrides"), raw.get("deleted"),
                            rotas if isinstance(rotas, list) else None)

def _save_world_cities():
    tmp = WORLD_CITIES_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(WORLD_CITIES, f, ensure_ascii=False, indent=2)
    os.replace(tmp, WORLD_CITIES_FILE)

_load_world_cities()
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `python tools/test_cidades_editor.py`
Expected: PASS — `0 falharam` (19 checks)

- [ ] **Step 5: Confirmar que o jogo continua subindo**

Run: `python -c "import server; print(len(server.WORLD_LOCATIONS), len(server.WORLD_ROUTES))"`
Expected: `4 6`

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_cidades_editor.py
git commit -m "feat(cidades): camada de dados de cidades personalizadas"
```

---

### Task 2: Cidade nova nasce vazia (lojas, pontos e taverna)

**Files:**
- Modify: `server.py` — `CITY_MAP_POINTS` (após o dict literal, antes de `_load_city_map_points()`), o loop de `TAVERN_SCENES` (hoje linha 267–269), e após `_load_city_shops()` (hoje linha 4495)
- Test: `tools/test_cidades_editor.py`

- [ ] **Step 1: Escrever o teste que falha**

Em `tools/test_cidades_editor.py`, troque a função `reset_mundo` por esta versão e acrescente a seção `[6]` **antes** da linha do `print(f"\n===== RESULTADO…")`:

```python
def reset_mundo():
    """Volta o mundo às 4 cidades originais, sem nenhuma edição do editor."""
    S._aplicar_estado_cidades([], {}, [], None)
    S._sincronizar_cidades_derivadas()
```

```python
    print("\n[6] Cidade nova nasce vazia; excluir limpa os derivados")
    reset_mundo()
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [], None)
    S._sincronizar_cidades_derivadas()
    check("sem lojas", S.CITY_SHOPS.get("porto_negro") == {})
    check("sem pontos no mapa da cidade", S.CITY_MAP_POINTS.get("porto_negro") == {})
    cena = S.TAVERN_SCENES.get("porto_negro") or {}
    check("cena de taverna existe", isinstance(cena.get("slots"), list))
    check("taverna sem NPCs copiados de Alva e Luz", cena.get("slots") == [])
    check("taverna sem fundo", not cena.get("background"))
    check("Alva e Luz mantém seus NPCs",
          len((S.TAVERN_SCENES.get("alva_e_luz") or {}).get("slots") or []) >= 8)
    S._aplicar_estado_cidades([], {}, [], None)
    S._sincronizar_cidades_derivadas()
    check("excluir limpa lojas", "porto_negro" not in S.CITY_SHOPS)
    check("excluir limpa pontos", "porto_negro" not in S.CITY_MAP_POINTS)
    check("excluir limpa taverna", "porto_negro" not in S.TAVERN_SCENES)
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python tools/test_cidades_editor.py`
Expected: FAIL com `AttributeError: module 'server' has no attribute '_sincronizar_cidades_derivadas'`

- [ ] **Step 3: Semear os pontos do mapa da cidade**

Em `server.py`, logo **depois** do dict literal `CITY_MAP_POINTS = {…}` (a linha `}` que o fecha, hoje linha 195) e **antes** de `CITY_MAP_POINTS_FILE = …`, insira:

```python
# Toda cidade tem sua entrada (as criadas no editor começam sem nenhum ponto);
# cidades removidas somem daqui. Precisa vir antes de _load_city_map_points(),
# que só aceita ids já presentes neste dicionário.
CITY_MAP_POINTS = {cid: CITY_MAP_POINTS.get(cid, {}) for cid in WORLD_LOCATIONS}
```

- [ ] **Step 4: Fazer a taverna nascer vazia**

Em `server.py`, substitua o bloco atual (hoje linhas 265–269):

```python
# Cada cidade guarda sua própria cena. Elas começam com a mesma composição-base,
# mas o editor salva fundo, imagens, posições e diálogos por ID de cidade.
for _tavern_city_id in WORLD_LOCATIONS:
    if _tavern_city_id not in TAVERN_SCENES:
        TAVERN_SCENES[_tavern_city_id] = deepcopy(TAVERN_SCENES["alva_e_luz"])
```

por:

```python
def _cena_taverna_vazia():
    """Cena editável e sem conteúdo — o estado inicial de uma cidade criada no editor."""
    return {"background": "", "art_ratio": 1.5, "mode": "individual", "mask": "", "slots": []}

# As 4 cidades originais começam com a mesma composição-base de Alva e Luz; as
# criadas no editor nascem vazias e ganham fundo e NPCs pela aba Taverna.
for _tavern_city_id in WORLD_LOCATIONS:
    if _tavern_city_id in TAVERN_SCENES:
        continue
    TAVERN_SCENES[_tavern_city_id] = (deepcopy(TAVERN_SCENES["alva_e_luz"])
                                      if _tavern_city_id in _BUILTIN_WORLD_LOCATIONS
                                      else _cena_taverna_vazia())
for _tavern_city_id in [c for c in TAVERN_SCENES if c not in WORLD_LOCATIONS]:
    del TAVERN_SCENES[_tavern_city_id]
```

- [ ] **Step 5: Criar o sincronizador usado em runtime**

Em `server.py`, logo **depois** da chamada `_load_city_shops()` (hoje linha 4495), insira:

```python
def _sincronizar_cidades_derivadas():
    """Garante uma entrada vazia de lojas/pontos/taverna para cada cidade e
    remove as sobras de cidades excluídas. Usado após salvar pelo editor (no
    boot cada subsistema já se semeia na sua própria declaração)."""
    for cid in [c for c in CITY_SHOPS if c not in WORLD_LOCATIONS]:
        del CITY_SHOPS[cid]
    for cid in [c for c in CITY_MAP_POINTS if c not in WORLD_LOCATIONS]:
        del CITY_MAP_POINTS[cid]
    for cid in [c for c in TAVERN_SCENES if c not in WORLD_LOCATIONS]:
        del TAVERN_SCENES[cid]
    for cid in WORLD_LOCATIONS:
        CITY_SHOPS.setdefault(cid, {})
        CITY_MAP_POINTS.setdefault(cid, {})
        TAVERN_SCENES.setdefault(cid, _cena_taverna_vazia())

_sincronizar_cidades_derivadas()
```

- [ ] **Step 6: Rodar o teste e confirmar que passa**

Run: `python tools/test_cidades_editor.py`
Expected: PASS — `0 falharam` (28 checks)

- [ ] **Step 7: Confirmar que as cidades originais não regrediram**

Run: `python tools/test_ficha_cidade.py`
Expected: `0 falharam`

- [ ] **Step 8: Commit**

```bash
git add server.py tools/test_cidades_editor.py
git commit -m "feat(cidades): cidade nova nasce sem lojas, pontos ou taverna"
```

---

### Task 3: Rota sem custo definido = viagem grátis

**Files:**
- Modify: `server.py` — `handle_world_travel` (hoje linha 7758) e `broadcast_city_state` (hoje linha 6089)
- Test: `tools/test_cidades_editor.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescente em `tools/test_cidades_editor.py`, **antes** do `print(f"\n===== RESULTADO…")`:

```python
    print("\n[7] Rota ausente = viagem grátis")
    reset_mundo()
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [], [])   # tabela de custos vazia
    S._sincronizar_cidades_derivadas()
    sala = S.GameRoom("TEST")
    enviados = []
    async def noop(*a, **k): pass
    async def cap_broadcast(msg, *a, **k): enviados.append(msg)
    sala.gm_say = noop; sala.broadcast = cap_broadcast; sala.send_to = noop
    sala._checkpoint_savegame = lambda *a, **k: None
    sala.phase = "city"; sala.host_pid = "p1"; sala.world_location = "alva_e_luz"
    heroi = S.make_player("p1", "Victor", "warrior", 0)
    heroi["fome"], heroi["sede"] = 20, 20
    sala.players["p1"] = heroi
    asyncio.run(sala.handle_world_travel("p1", "porto_negro"))
    check("viajou para a cidade nova", sala.world_location == "porto_negro")
    check("não gastou fome", heroi["fome"] == 20)
    check("não gastou sede", heroi["sede"] == 20)

    print("\n[8] Rota com custo debita; payload cobre todos os pares")
    reset_mundo()
    S._aplicar_estado_cidades([CIDADE_NOVA], {}, [],
                              [{"from": "alva_e_luz", "to": "porto_negro", "fome": 5, "sede": 3}])
    S._sincronizar_cidades_derivadas()
    sala.world_location = "alva_e_luz"; heroi["fome"], heroi["sede"] = 20, 20
    asyncio.run(sala.handle_world_travel("p1", "porto_negro"))
    check("custo de fome debitado", heroi["fome"] == 15)
    check("custo de sede debitado", heroi["sede"] == 17)
    enviados.clear()
    asyncio.run(sala.broadcast_city_state())
    rotas = (enviados[-1].get("world") or {}).get("routes") or []
    n_cidades = len(S.WORLD_LOCATIONS)
    check("payload traz todos os pares", len(rotas) == n_cidades * (n_cidades - 1) // 2)
    par = next((r for r in rotas if {r["from"], r["to"]} == {"porto_negro", "vila_riacho"}), None)
    check("par sem custo vai como 0/0", par is not None and par["fome"] == 0 and par["sede"] == 0)
    reset_mundo()
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python tools/test_cidades_editor.py`
Expected: FAIL em "viajou para a cidade nova" (o servidor recusa hoje com "Não existe rota conhecida")

- [ ] **Step 3: Tornar a rota ausente gratuita na viagem**

Em `server.py`, dentro de `handle_world_travel`, substitua:

```python
        cost = WORLD_ROUTES.get(frozenset((self.world_location, destination)))
        if not cost:
            await self.send_to(pid, {"type": "error", "msg": "Não existe rota conhecida para esse destino."})
            return
```

por:

```python
        # Sem custo cadastrado a viagem é gratuita: a tabela guarda preços, não
        # a lista de trajetos existentes.
        cost = WORLD_ROUTES.get(frozenset((self.world_location, destination))) or {"fome": 0, "sede": 0}
```

- [ ] **Step 4: Emitir uma rota para todos os pares**

Em `server.py`, dentro de `broadcast_city_state`, substitua:

```python
                "routes": [{"from": tuple(route)[0], "to": tuple(route)[1], **cost}
                           for route, cost in WORLD_ROUTES.items()],
```

por:

```python
                # Todo par aparece (custo salvo ou 0/0) para o cliente nunca
                # tratar um destino como inalcançável.
                "routes": [{"from": origem, "to": destino,
                            **(WORLD_ROUTES.get(frozenset((origem, destino))) or {"fome": 0, "sede": 0})}
                           for indice, origem in enumerate(WORLD_LOCATIONS)
                           for destino in list(WORLD_LOCATIONS)[indice + 1:]],
```

- [ ] **Step 5: Rodar o teste e confirmar que passa**

Run: `python tools/test_cidades_editor.py`
Expected: PASS — `0 falharam` (35 checks)

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_cidades_editor.py
git commit -m "feat(cidades): rota sem custo cadastrado vira viagem gratuita"
```

---

### Task 4: Handler de save do editor (com realocação de salas)

**Files:**
- Modify: `server.py` — acrescentar após `_save_city_shops_upload` (hoje termina na linha 22852) e alterar `_city_shops_editor_payload` (hoje linha 22775)
- Test: `tools/test_cidades_editor.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescente em `tools/test_cidades_editor.py`, **antes** do `print(f"\n===== RESULTADO…")`:

```python
    print("\n[9] Handler de save do editor")
    reset_mundo()
    tmp2 = os.path.join(tempfile.gettempdir(), "cidades_teste2.json")
    original_file = S.WORLD_CITIES_FILE
    S.WORLD_CITIES_FILE = tmp2
    try:
        ok, payload = S._save_world_cities_upload([CIDADE_NOVA], {}, [], [])
        check("save aceito", ok is True)
        check("payload devolve a cidade nova",
              any(c["id"] == "porto_negro" for c in (payload or {}).get("cities", [])))
        check("payload traz a tabela de rotas", isinstance((payload or {}).get("routes"), list))
        check("payload informa a cidade inicial", (payload or {}).get("city_inicial") == "alva_e_luz")
        check("arquivo gravado", os.path.exists(tmp2))
        with open(tmp2, encoding="utf-8") as f: gravado = json.load(f)
        check("arquivo contém a cidade", gravado["cities"][0]["id"] == "porto_negro")
        check("derivados sincronizados pelo handler", S.CITY_SHOPS.get("porto_negro") == {})

        ok2, erro = S._save_world_cities_upload("não é lista", {}, [], [])
        check("payload inválido recusado", ok2 is False and isinstance(erro, str))

        sala2 = S.GameRoom("TEST2")
        sala2.phase = "city"; sala2.world_location = "porto_negro"
        S.rooms["TEST2"] = sala2
        try:
            S._save_world_cities_upload([], {}, [], [])
            check("sala em cidade excluída volta para Alva e Luz",
                  sala2.world_location == "alva_e_luz")
        finally:
            S.rooms.pop("TEST2", None)
    finally:
        S.WORLD_CITIES_FILE = original_file
        if os.path.exists(tmp2): os.remove(tmp2)
        reset_mundo()
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python tools/test_cidades_editor.py`
Expected: FAIL com `AttributeError: module 'server' has no attribute '_save_world_cities_upload'`

- [ ] **Step 3: Implementar o handler**

Em `server.py`, logo **depois** de `_save_city_shops_upload` (antes de `async def _refresh_city_states_after_editor_save():`), insira:

```python
def _save_world_cities_upload(cities, overrides, deleted, routes):
    """Aplica e grava o estado de cidades vindo do editor. O editor envia sempre
    o conjunto completo (cidades criadas, overrides, exclusões e a tabela de
    rotas), então isto é uma substituição, não um merge incremental."""
    if not isinstance(cities, list) or not isinstance(routes, list):
        return False, "dados de cidades inválidos"
    if not isinstance(overrides, dict) or not isinstance(deleted, list):
        return False, "dados de cidades inválidos"
    _aplicar_estado_cidades(cities, overrides, deleted, routes)
    _sincronizar_cidades_derivadas()
    for sala in rooms.values():
        if getattr(sala, "world_location", None) not in WORLD_LOCATIONS:
            sala.world_location = CITY_INICIAL
    try:
        _save_world_cities()
        _save_city_shops()
        _save_tavern_scenes()
        _save_city_map_points()
    except OSError as e:
        return False, str(e)
    return True, _city_shops_editor_payload()
```

- [ ] **Step 4: Levar rotas e cidade inicial ao payload do editor**

Em `server.py`, substitua o `return` de `_city_shops_editor_payload()`:

```python
    return {"cities": list(WORLD_LOCATIONS.values()), "shops": CITY_SHOP_LABELS,
            "stock": CITY_SHOPS, "catalog": catalog, "taverns": TAVERN_SCENES,
            "city_points": CITY_MAP_POINTS}
```

por:

```python
    rotas = [{"from": origem, "to": destino,
              **(WORLD_ROUTES.get(frozenset((origem, destino))) or {"fome": 0, "sede": 0})}
             for indice, origem in enumerate(WORLD_LOCATIONS)
             for destino in list(WORLD_LOCATIONS)[indice + 1:]]
    return {"cities": list(WORLD_LOCATIONS.values()), "shops": CITY_SHOP_LABELS,
            "stock": CITY_SHOPS, "catalog": catalog, "taverns": TAVERN_SCENES,
            "city_points": CITY_MAP_POINTS, "routes": rotas,
            "custom_cities": [c["id"] for c in WORLD_CITIES.get("cities", [])],
            "city_inicial": CITY_INICIAL}
```

- [ ] **Step 5: Rodar o teste e confirmar que passa**

Run: `python tools/test_cidades_editor.py`
Expected: PASS — `0 falharam` (44 checks)

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_cidades_editor.py
git commit -m "feat(cidades): handler de save do editor com realocacao de salas"
```

---

### Task 5: Upload da ilustração e mensagens WebSocket

**Files:**
- Modify: `server.py` — `_save_city_art_upload` junto de `_save_tavern_art_upload` (hoje linha 22943) e o dispatch do editor (hoje linha 21078–21102)
- Test: `tools/test_cidades_editor.py`

- [ ] **Step 1: Escrever o teste que falha**

Acrescente em `tools/test_cidades_editor.py`, **antes** do `print(f"\n===== RESULTADO…")`:

```python
    print("\n[10] Upload da ilustração da cidade")
    import base64
    png = base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 64).decode()
    ok, caminho = S._save_city_art_upload("porto negro.png", png)
    check("upload aceito", ok is True)
    check("caminho em assets/city", str(caminho).startswith("assets/city/"))
    arquivo = os.path.join(S.BASE_DIR, str(caminho).replace("/", os.sep))
    check("arquivo gravado no disco", os.path.exists(arquivo))
    if os.path.exists(arquivo): os.remove(arquivo)
    ok2, _ = S._save_city_art_upload("mapa.exe", png)
    check("extensão inválida recusada", ok2 is False)
    ok3, _ = S._save_city_art_upload("../fuga.png", png)
    check("path traversal neutralizado",
          ok3 is False or ".." not in str(_))
    ok4, _ = S._save_city_art_upload("grande.png", "A" * (S.STORY_UPLOAD_MAX * 2))
    check("arquivo grande demais recusado", ok4 is False)
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `python tools/test_cidades_editor.py`
Expected: FAIL com `AttributeError: module 'server' has no attribute '_save_city_art_upload'`

- [ ] **Step 3: Implementar o upload**

Em `server.py`, logo **depois** de `_save_tavern_art_upload` (antes de `PRISONER_DIR = …`), insira:

```python
CITY_ASSET_DIR = os.path.join(BASE_DIR, "assets", "city")

def _save_city_art_upload(name, data_b64):
    """Grava a ilustração de uma cidade em assets/city/. Mesmas proteções do
    _save_tavern_art_upload (extensão, tamanho e path traversal)."""
    base = os.path.basename(name or "")
    if not base or "\x00" in base or os.path.splitext(base)[1].lower() not in _STORY_IMG_EXT:
        return False, "imagem inválida"
    if not isinstance(data_b64, str) or not data_b64 or (len(data_b64) * 3) // 4 > STORY_UPLOAD_MAX:
        return False, "dados inválidos ou arquivo grande demais"
    try: raw = base64.b64decode(data_b64, validate=True)
    except Exception: return False, "dados inválidos"
    if len(raw) > STORY_UPLOAD_MAX: return False, "arquivo grande demais"
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", base)
    try:
        os.makedirs(CITY_ASSET_DIR, exist_ok=True)
        with open(os.path.join(CITY_ASSET_DIR, safe), "wb") as f: f.write(raw)
    except OSError: return False, "falha ao gravar"
    return True, "assets/city/" + safe
```

- [ ] **Step 4: Ligar as duas mensagens no dispatch do editor**

Em `server.py`, logo **depois** do bloco `if t == "upload_tavern_art": … continue` (hoje linha 21085), insira:

```python
                if t == "upload_city_art":
                    ok, res = _save_city_art_upload(msg.get("name"), msg.get("data"))
                    payload = {"type": "upload_result", "kind": "city_art",
                               "upload_id": msg.get("upload_id"), "ok": ok}
                    if ok: payload["path"] = res
                    else: payload["error"] = res
                    await ws.send(json.dumps(payload))
                    continue

                if t == "save_world_cities":
                    ok, res = _save_world_cities_upload(msg.get("cities"), msg.get("overrides"),
                                                        msg.get("deleted"), msg.get("routes"))
                    if ok:
                        await _refresh_city_states_after_editor_save()
                    payload = {"type": "upload_result", "kind": "world_cities",
                               "upload_id": msg.get("upload_id"), "ok": ok}
                    if ok: payload["config"] = res
                    else: payload["error"] = res
                    await ws.send(json.dumps(payload))
                    continue
```

- [ ] **Step 5: Rodar o teste e confirmar que passa**

Run: `python tools/test_cidades_editor.py`
Expected: PASS — `0 falharam` (50 checks)

- [ ] **Step 6: Commit**

```bash
git add server.py tools/test_cidades_editor.py
git commit -m "feat(cidades): upload da ilustracao e mensagens WS do editor"
```

---

### Task 6: API cliente do editor (`EDITOR_SAVE`)

**Files:**
- Modify: `tools/story_upload.js` — junto de `uploadTavernArt` (hoje linha 154) e no `window.EDITOR_SAVE` (hoje linha 189)

Este arquivo é a ponte WebSocket do editor; não há teste automatizado para ele (a verificação é a Task 9, no navegador).

- [ ] **Step 1: Acrescentar as duas funções**

Em `tools/story_upload.js`, logo **depois** da função `uploadTavernArt`, insira:

```javascript
  async function uploadCityArt(file) {
    if (IMG.indexOf(extOf(file.name)) < 0) throw new Error("envie uma imagem PNG, JPG, WebP ou GIF");
    if (file.size > MAX) throw new Error("arquivo grande demais");
    const m = await request("upload_city_art", { name: file.name, data: await toBase64(file) });
    return m.path;
  }

  // Envia o conjunto completo de cidades: criadas, edições nas originais,
  // exclusões e a tabela de custos de viagem. Resolve com a config atualizada.
  function saveWorldCities(cities, overrides, deleted, routes) {
    return request("save_world_cities", {
      cities: cities, overrides: overrides, deleted: deleted, routes: routes,
    }).then((m) => m.config);
  }
```

- [ ] **Step 2: Exportar no `window.EDITOR_SAVE`**

Na linha do `window.EDITOR_SAVE = { … }`, acrescente as duas chaves antes do fechamento:

```javascript
  window.EDITOR_SAVE = { saveDungeon: saveDungeon, saveCampaign: saveCampaign, saveCustomMonster: saveCustomMonster, uploadMonsterArt: uploadMonsterArt, saveCustomItem: saveCustomItem, uploadItemArt: uploadItemArt, uploadTavernArt: uploadTavernArt, uploadCityArt: uploadCityArt, loadCityShops: loadCityShops, saveCityShops: saveCityShops, saveWorldCities: saveWorldCities, loadWorldAdventures: loadWorldAdventures, saveWorldAdventures: saveWorldAdventures };
```

- [ ] **Step 3: Verificar a sintaxe**

Run: `node --check tools/story_upload.js`
Expected: sem saída (sintaxe válida)

- [ ] **Step 4: Commit**

```bash
git add tools/story_upload.js
git commit -m "feat(cidades): API cliente para upload de arte e save de cidades"
```

---

### Task 7: Painel de cidade no editor (criar / editar / excluir / rotas)

**Files:**
- Modify: `tools/editor_city.js` — estado do módulo (linha 5), `cityTabs()` (linha 48), `render()` (linha 252) e um bloco novo de funções

- [ ] **Step 1: Acrescentar o modo "cidade" ao estado e às abas**

Em `tools/editor_city.js`, na linha do estado do módulo, acrescente as variáveis do painel:

```javascript
  let config = null, cityId = null, storeId = "ferreiro", tabId = null, mode = "shops", loading = null, selectedNpcId = null, selectedCityPointId = null;
  let cityDraft = null;   // cidade em edição/criação no painel (null = painel fechado)
```

E substitua a função `cityTabs()` inteira (que hoje tem uma linha morta antes do `return` final) por:

```javascript
  function cityTabs() {
    const botao = (id, rotulo) => '<button data-city-mode="' + id + '" class="' + (mode === id ? "active" : "") + '">' + rotulo + '</button>';
    return '<div class="cityed-mode">' + botao("shops", "🛒 Lojas") + botao("map", "🗺️ Mapa da cidade")
      + botao("tavern", "💬 Taverna e NPCs") + botao("city", "🏘️ Cidades") + '</div>';
  }
```

- [ ] **Step 2: Escrever o painel**

Ainda em `tools/editor_city.js`, insira estas funções logo **antes** de `function render() {`:

```javascript
  // ─── Painel de cidades ─────────────────────────────────────────────────────
  // O editor manda sempre o conjunto completo (criadas, overrides, exclusões e
  // a tabela de rotas); o servidor substitui o estado por ele.
  const BUILTIN_IDS = ["alva_e_luz", "vila_riacho", "vila_corvin", "graciero"];
  function cityInicial() { return config.city_inicial || "alva_e_luz"; }
  function customIds() { return config.custom_cities || []; }
  function slugify(nome) {
    return String(nome || "").normalize("NFD").replace(new RegExp("[\\u0300-\\u036f]", "g"), "")   // tira acentos
      .toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "").slice(0, 48);
  }
  function novoIdCidade(nome) {
    const base = slugify(nome) || "cidade";
    let id = base, n = 2;
    while ((config.cities || []).some(c => c.id === id)) id = base + "_" + n++;
    return id;
  }
  function rotaEntre(a, b) {
    return (config.routes || []).find(r => (r.from === a && r.to === b) || (r.from === b && r.to === a));
  }
  function setRota(a, b, fome, sede) {
    if (!Array.isArray(config.routes)) config.routes = [];
    const atual = rotaEntre(a, b);
    if (atual) { atual.fome = fome; atual.sede = sede; return; }
    config.routes.push({ from: a, to: b, fome: fome, sede: sede });
  }
  // Estado completo no formato que o servidor espera.
  function estadoCidades() {
    const custom = new Set(customIds());
    const cities = (config.cities || []).filter(c => custom.has(c.id))
      .map(c => ({ id: c.id, nome: c.nome, tipo: c.tipo || "cidade", imagem: c.imagem || "", x: Number(c.x) || 0, y: Number(c.y) || 0 }));
    const overrides = {};
    (config.cities || []).filter(c => !custom.has(c.id))
      .forEach(c => { overrides[c.id] = { nome: c.nome, tipo: c.tipo || "cidade", imagem: c.imagem || "" }; });
    const deleted = BUILTIN_IDS.filter(id => !(config.cities || []).some(c => c.id === id));
    return { cities: cities, overrides: overrides, deleted: deleted, routes: config.routes || [] };
  }
  async function salvarCidades() {
    const status = root.querySelector("#cityed-status");
    status.textContent = "Salvando cidades…";
    const estado = estadoCidades();
    try {
      config = await window.EDITOR_SAVE.saveWorldCities(estado.cities, estado.overrides, estado.deleted, estado.routes);
      cityDraft = null;
      if (!(config.cities || []).some(c => c.id === cityId)) cityId = (config.cities[0] || {}).id;
      render();
      root.querySelector("#cityed-status").textContent = "✓ Cidades salvas e aplicadas no jogo.";
    } catch (e) { status.textContent = "Erro ao salvar: " + e.message; }
  }
  function abrirDraft(id) {
    const existente = (config.cities || []).find(c => c.id === id);
    cityDraft = existente
      ? { novo: false, id: existente.id, nome: existente.nome, tipo: existente.tipo || "cidade", imagem: existente.imagem || "", x: Number(existente.x) || 50, y: Number(existente.y) || 50 }
      : { novo: true, id: "", nome: "", tipo: "cidade", imagem: "", x: 50, y: 50 };
    mode = "city"; render();
  }
  function aplicarDraft() {
    const status = root.querySelector("#cityed-status");
    if (!cityDraft.nome.trim()) { status.textContent = "Dê um nome à cidade."; return false; }
    if (cityDraft.novo) {
      cityDraft.id = novoIdCidade(cityDraft.nome);
      config.cities.push({ id: cityDraft.id, nome: cityDraft.nome, tipo: cityDraft.tipo, imagem: cityDraft.imagem, x: cityDraft.x, y: cityDraft.y, servicos: true });
      config.custom_cities = customIds().concat([cityDraft.id]);
      config.stock[cityDraft.id] = {};
      cityId = cityDraft.id;
    } else {
      const alvo = (config.cities || []).find(c => c.id === cityDraft.id);
      if (alvo) { alvo.nome = cityDraft.nome; alvo.tipo = cityDraft.tipo; alvo.imagem = cityDraft.imagem; alvo.x = cityDraft.x; alvo.y = cityDraft.y; }
    }
    return true;
  }
  function excluirCidade(id) {
    if (id === cityInicial()) return;
    if (!window.confirm("Excluir esta cidade? As lojas, os pontos do mapa e a taverna dela serão apagados.")) return;
    config.cities = (config.cities || []).filter(c => c.id !== id);
    config.custom_cities = customIds().filter(x => x !== id);
    config.routes = (config.routes || []).filter(r => r.from !== id && r.to !== id);
    if (cityId === id) cityId = (config.cities[0] || {}).id;
    cityDraft = null;
    salvarCidades();
  }
  function renderCidades() {
    const c = city(), inicial = cityInicial();
    const lista = '<div class="cityed-cities">' + (config.cities || []).map(x => '<button data-city="' + esc(x.id) + '" class="' + (x.id === cityId ? "active" : "") + '">' + esc(x.nome) + '<small>' + esc(x.tipo || "cidade") + '</small></button>').join("") + '</div>';
    let painel = '<p>Selecione uma cidade para editar, ou crie uma nova.</p>';
    if (cityDraft) {
      const outras = (config.cities || []).filter(x => x.id && x.id !== cityDraft.id);
      const rotas = outras.map(x => {
        const r = (!cityDraft.novo && rotaEntre(cityDraft.id, x.id)) || { fome: 0, sede: 0 };
        return '<div class="cityed-route"><span>' + esc(x.nome) + '</span><label>🍖<input type="number" min="0" data-route-fome="' + esc(x.id) + '" value="' + Number(r.fome || 0) + '"></label><label>💧<input type="number" min="0" data-route-sede="' + esc(x.id) + '" value="' + Number(r.sede || 0) + '"></label></div>';
      }).join("") || '<small>Nenhuma outra cidade cadastrada.</small>';
      painel = '<h3>' + (cityDraft.novo ? "Nova cidade" : "Editando " + esc(cityDraft.nome)) + '</h3>'
        + '<label>Nome<input id="cityed-nome" value="' + esc(cityDraft.nome) + '"></label>'
        + '<label>Tipo<select id="cityed-tipo"><option value="cidade"' + (cityDraft.tipo === "cidade" ? " selected" : "") + '>Cidade</option><option value="vila"' + (cityDraft.tipo === "vila" ? " selected" : "") + '>Vila</option></select></label>'
        + '<label>Imagem de fundo<input id="cityed-img-file" type="file" accept="image/png,image/jpeg,image/webp,image/gif"></label>'
        + '<button id="cityed-img-upload" type="button">Enviar imagem</button>'
        + (cityDraft.imagem ? '<img class="cityed-city-preview" src="../' + esc(cityDraft.imagem) + '" alt="Prévia da cidade">' : '<small>Nenhuma imagem enviada ainda.</small>')
        + '<div class="worlded-cost"><label>X %<input id="cityed-x" type="number" min="0" max="100" step="0.1" value="' + Number(cityDraft.x) + '"></label><label>Y %<input id="cityed-y" type="number" min="0" max="100" step="0.1" value="' + Number(cityDraft.y) + '"></label></div>'
        + '<p>Posição no mapa-múndi. O ajuste fino também pode ser feito arrastando o marcador na aba “Mapa do Mundo”.</p>'
        + '<div class="cityed-routes"><b>Custo de viagem</b><small>Deixe 0 para viagem gratuita.</small>' + rotas + '</div>'
        + '<button id="cityed-city-save" type="button">Salvar cidade</button>'
        + (cityDraft.novo || cityDraft.id === inicial ? "" : '<button id="cityed-city-delete" type="button">Excluir cidade</button>');
    }
    root.innerHTML = '<div class="cityed"><header><div><h1>🏘️ Cidades</h1><p>Crie uma cidade nova, edite as existentes e defina os custos de viagem.</p></div><button id="cityed-city-new" type="button">+ Nova cidade</button></header>'
      + cityTabs() + lista
      + '<div class="cityed-layout"><aside><h2>' + esc(c.nome || "") + '</h2><button id="cityed-city-edit" type="button">✏️ Editar esta cidade</button></aside><section id="cityed-city-form">' + painel + '</section></div><div id="cityed-status"></div></div>';
    root.querySelectorAll("[data-city]").forEach(b => b.onclick = () => { cityId = b.dataset.city; cityDraft = null; render(); });
    bindCityMode();
    root.querySelector("#cityed-city-new").onclick = () => abrirDraft(null);
    root.querySelector("#cityed-city-edit").onclick = () => abrirDraft(cityId);
    if (!cityDraft) return;
    const campo = (sel, chave, numero) => {
      const el = root.querySelector(sel); if (!el) return;
      el.oninput = () => { cityDraft[chave] = numero ? Math.max(0, Math.min(100, Number(el.value) || 0)) : el.value; };
      el.onchange = el.oninput;
    };
    campo("#cityed-nome", "nome"); campo("#cityed-tipo", "tipo");
    campo("#cityed-x", "x", true); campo("#cityed-y", "y", true);
    root.querySelector("#cityed-img-upload").onclick = async () => {
      const status = root.querySelector("#cityed-status"), file = root.querySelector("#cityed-img-file").files[0];
      if (!file) { status.textContent = "Escolha uma imagem primeiro."; return; }
      status.textContent = "Enviando imagem…";
      try { cityDraft.imagem = await window.EDITOR_SAVE.uploadCityArt(file); render(); }
      catch (e) { status.textContent = "Erro ao enviar: " + e.message; }
    };
    root.querySelector("#cityed-city-save").onclick = () => {
      const alvo = cityDraft.novo ? null : cityDraft.id;
      if (!aplicarDraft()) return;
      const id = alvo || cityDraft.id;
      root.querySelectorAll("[data-route-fome]").forEach(input => {
        const outra = input.dataset.routeFome;
        const sede = root.querySelector('[data-route-sede="' + outra + '"]');
        setRota(id, outra, Math.max(0, Number(input.value) || 0), Math.max(0, Number(sede && sede.value) || 0));
      });
      salvarCidades();
    };
    const del = root.querySelector("#cityed-city-delete");
    if (del) del.onclick = () => excluirCidade(cityDraft.id);
  }
```

- [ ] **Step 3: Despachar o modo novo em `render()`**

Em `tools/editor_city.js`, dentro de `render()`, logo **depois** da linha `if (mode === "map") { renderCityMap(); return; }`, acrescente:

```javascript
    if (mode === "city") { renderCidades(); return; }
```

- [ ] **Step 4: Estilo mínimo do painel**

Em `tools/editor.css`, no fim do arquivo, acrescente:

```css
.cityed-route { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
.cityed-route span { flex: 1; }
.cityed-route input { width: 64px; }
.cityed-routes { margin: 12px 0; }
.cityed-city-preview { display: block; max-width: 260px; margin: 8px 0; border-radius: 6px; }
```

- [ ] **Step 5: Verificar a sintaxe**

Run: `node --check tools/editor_city.js`
Expected: sem saída (sintaxe válida)

- [ ] **Step 6: Commit**

```bash
git add tools/editor_city.js tools/editor.css
git commit -m "feat(cidades): painel de criar/editar/excluir cidade no editor"
```

---

### Task 8: Editor de taverna funcionando com cena vazia

**Files:**
- Modify: `tools/editor_city.js` — `renderTavern()` (hoje linha 53)

Hoje, quando a cidade não tem nenhum NPC, `renderTavern` mostra só a frase "Esta cidade ainda não possui uma cena de taverna configurada" — sem upload de fundo e sem o botão de adicionar NPC. Sem isto, uma cidade criada do zero nunca ganha taverna.

- [ ] **Step 1: Mostrar os controles também com a cena vazia**

Em `tools/editor_city.js`, dentro de `renderTavern`, localize o trecho do `root.innerHTML` que termina com:

```javascript
'</section>' : '<section class="cityed-tavern"><h2>🍺 Taverna de ' + esc(c.nome) + '</h2><p>Esta cidade ainda não possui uma cena de taverna configurada.</p></section>')
```

e substitua por:

```javascript
'</section>' : '<section class="cityed-tavern"><h2>🍺 Taverna de ' + esc(c.nome) + '</h2><p>Esta taverna ainda está vazia. Envie um fundo e adicione os frequentadores.</p>' + sceneConfig + '</section>')
```

- [ ] **Step 2: Garantir o botão "+ Adicionar NPC" na cena vazia**

Ainda em `renderTavern`, o bloco que cria o botão de adicionar NPC (`const addNpc = document.createElement('button')`) já roda fora do `if (scene && slots.length)`, mas ele quebra quando não existe `scene`. Substitua:

```javascript
    const addNpc=document.createElement('button');
    addNpc.type='button'; addNpc.textContent='+ Adicionar NPC à cena';
    addNpc.onclick=()=>{ const id='npc_'+Date.now().toString(36), z=Math.max(0,...slots.map(s=>Number(s.z || 1)))+1; scene.slots.push({id,name:'Novo NPC',image:'',x:40,y:40,w:14,h:20,z,dialog:''}); selectedNpcId=id; render(); };
    root.querySelector('.cityed-tavern').appendChild(addNpc);
```

por:

```javascript
    if (scene) {
      if (!Array.isArray(scene.slots)) scene.slots = [];
      const addNpc=document.createElement('button');
      addNpc.type='button'; addNpc.textContent='+ Adicionar NPC à cena';
      addNpc.onclick=()=>{ const id='npc_'+Date.now().toString(36), z=Math.max(0,...slots.map(s=>Number(s.z || 1)))+1; scene.slots.push({id,name:'Novo NPC',image:'',x:40,y:40,w:14,h:20,z,dialog:''}); selectedNpcId=id; render(); };
      root.querySelector('.cityed-tavern').appendChild(addNpc);
    }
```

- [ ] **Step 3: Verificar a sintaxe**

Run: `node --check tools/editor_city.js`
Expected: sem saída (sintaxe válida)

- [ ] **Step 4: Commit**

```bash
git add tools/editor_city.js
git commit -m "feat(cidades): editor de taverna aceita cena vazia"
```

---

### Task 9: Verificação ponta a ponta

**Files:** nenhum (verificação)

- [ ] **Step 1: Rodar a suíte desta feature**

Run: `python tools/test_cidades_editor.py`
Expected: `0 falharam`

- [ ] **Step 2: Rodar as suítes vizinhas para conferir que nada regrediu**

Run cada um e confirme `0 falharam`:

```bash
python tools/test_ficha_cidade.py
```

```bash
python tools/test_campanha.py
```

```bash
python tools/test_savegames.py
```

Se algum deles já falhava **antes** desta feature, confirme com `git stash` + nova execução antes de tratar como regressão (o repositório tem falhas pré-existentes conhecidas).

- [ ] **Step 3: Smoke test no navegador**

1. `python server.py`
2. Abrir `http://localhost:8765/tools/editor.html`, ir na aba de cidades e depois na sub-aba "🏘️ Cidades".
3. "+ Nova cidade" → nome "Porto Negro", tipo Cidade, enviar um PNG, X/Y 60/44, custo 5🍖/3💧 para Alva e Luz → "Salvar cidade".
4. Confirmar: a cidade aparece na lista; nas sub-abas "🛒 Lojas" ela está sem nenhum estabelecimento marcado; em "🗺️ Mapa da cidade" o fundo é a imagem enviada e não há nenhum ponto; em "💬 Taverna e NPCs" aparecem o upload de fundo e o "+ Adicionar NPC".
5. Na aba "🧭 Mapa do Mundo", o marcador de Porto Negro aparece e pode ser arrastado.
6. Abrir o jogo (`http://localhost:8765/index.html`), criar sala, iniciar, e na cidade abrir o mapa-múndi: Porto Negro está lá, a viagem cobra 5🍖/3💧 a partir de Alva e Luz, e a partir de outra cidade custa 0/0.
7. Voltar ao editor, excluir Porto Negro e confirmar que ela some do mapa-múndi do jogo.

- [ ] **Step 4: Verificar que `cidades_personalizadas.json` não entra no versionamento por engano**

Run: `git status --short cidades_personalizadas.json`
Expected: aparece como `??` (não rastreado). Deixe assim — é conteúdo do usuário, não código. Se o projeto preferir versioná-lo, isso é decisão do dono do repositório.

- [ ] **Step 5: Atualizar a documentação de arquitetura**

Em `CLAUDE.md`, na seção de blocos `>` de estado do projeto (após o bloco dos antídotos), acrescente:

```markdown
> **Cidades editáveis (editor):** a aba "🏘️ Cidades" do editor cria cidades novas,
> edita as existentes (nome/tipo/imagem) e as exclui. As 4 originais continuam
> declaradas em `WORLD_LOCATIONS`/`WORLD_ROUTES` (base imutável, snapshot em
> `_BUILTIN_WORLD_LOCATIONS`/`_BUILTIN_WORLD_ROUTES`); `cidades_personalizadas.json`
> é a camada por cima (`cities`/`overrides`/`deleted`/`routes`), aplicada no boot e
> no save do editor pela MESMA função `_aplicar_estado_cidades`. Lojas
> (`CITY_SHOPS`), pontos (`CITY_MAP_POINTS`) e taverna (`TAVERN_SCENES`) são
> derivados: cada cidade ganha uma entrada vazia e as excluídas somem
> (`_sincronizar_cidades_derivadas`; no boot cada subsistema se semeia na própria
> declaração). **Mudança de regra:** `WORLD_ROUTES` virou tabela de PREÇOS — par sem
> entrada = viagem grátis (`handle_world_travel`), e `broadcast_city_state`/
> `_city_shops_editor_payload` emitem uma rota para TODOS os pares, então o cliente
> nunca vê destino bloqueado. `alva_e_luz` (`CITY_INICIAL`) nunca é excluível e é o
> fallback de salas cuja cidade sumiu. Upload da ilustração: `upload_city_art` →
> `assets/city/`. Teste: `tools/test_cidades_editor.py`.
```

- [ ] **Step 6: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(cidades): registra o editor de cidades na arquitetura"
```

---

## Notas de risco

- **Ordem de boot** é o ponto mais frágil: `_load_world_cities()` precisa rodar antes de `_load_world_map_points()`, de `CITY_MAP_POINTS`, do loop de `TAVERN_SCENES` e de `_default_city_shops()`. Se uma cidade criada não aparecer com lojas/pontos, é aqui que se olha primeiro.
- **`_aplicar_estado_cidades` preserva x/y** das cidades já carregadas, porque `world_map_points.json` (arraste no mapa-múndi) continua sendo o dono dessas coordenadas para as originais.
- **Rota gratuita muda comportamento existente**: destinos antes bloqueados por falta de rota passam a ser alcançáveis a custo zero. Com as 4 cidades originais todos os 6 pares já existem, então nada muda para elas.
