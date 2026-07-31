# Cenas de conversa por local — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generalizar a cena de conversa da taverna para qualquer ponto da cidade, com várias cenas por cidade, e fazer a conversa de uso único sumir do menu depois de resolvida.

**Architecture:** `TAVERN_SCENES[cidade]` (uma cena) vira `CITY_SCENES[cidade][cena]` (várias), persistido em `city_scenes.json`. O vínculo mora no ponto do mapa (`CITY_MAP_POINTS[cidade][ponto]["scene"]`), garantindo no máximo uma cena por ponto. O cliente passa a abrir o modal pelo **id do ponto** em vez do tipo do prédio, montando as abas como *[cena] + [loja]*. A taverna migra para a cena de id `taverna` — sem caso especial.

**Tech Stack:** Python 3 + `websockets` (server.py, sem framework), JS vanilla (game.js, src/gameState.js, tools/editor_city.js), CSS puro (game.css). Testes são scripts Python que rodam da raiz e imprimem ✅/❌.

**Spec:** `docs/superpowers/specs/2026-07-30-cenas-de-conversa-por-local-design.md`

---

## Estrutura de arquivos

| Arquivo | Responsabilidade nesta entrega |
|---|---|
| `server.py` | `CITY_SCENES`, loader/saver, migração, payload, `handle_scene_npc`, validação do editor |
| `city_scenes.json` | Persistência das cenas (novo; substitui `tavern_scenes.json`) |
| `src/gameState.js` | `talkSceneNpc`, getters de cena, estado `activeScene` |
| `game.js` | Abertura por ponto, montagem de abas, render da cena, pontos da ilustração |
| `game.css` | Renomeação `tavern-*` → `cena-*` |
| `tools/editor_city.js` | Aba "Cenas e NPCs": lista de cenas, vínculo, ponto novo |
| `tools/test_cenas_conversa.py` | Teste novo (criado na Task 1, cresce a cada task de servidor) |
| `tools/test_cidades_editor.py` | Adaptado na Task 1 (o import quebra sem isso) e verificado na Task 12 |

**Armadilha de teste descoberta na Task 1:** `isolar_arquivos()` redireciona os
JSON para uma pasta temporária, mas `CITY_SCENES` **já foi populado no import**
a partir dos arquivos reais do usuário. Então nenhuma asserção pode comparar
com os valores hardcoded no código — o `tavern_scenes.json` do usuário
sobrescreve o default (o fundo dele é `assets/tavern/taverna.png`, não
`assets/city/taverna.png`). Asserções sobre conteúdo de cena devem verificar
**forma** (fundo começa com `assets/`, há pelo menos 8 slots), nunca valor
exato.

**Convenções do projeto que valem aqui:**
- Testes rodam da raiz: `python tools/test_x.py`. Saem com código 1 se algo falhar.
- Todo teste que grava em disco **isola os JSON reais numa pasta temporária** (ver `isolar_arquivos()` em `tools/test_cidades_editor.py`) — nunca tocar nos dados do usuário.
- Commits em português, prefixo `feat(...)`/`refactor(...)`/`test(...)`.
- **Antes de qualquer `git add`, rodar `git status`**: o usuário edita `server.py` e outros arquivos em paralelo. Adicionar apenas os arquivos da task, nominalmente. Nunca `git add -A` nem `git add .`.

---

## Task 1: `CITY_SCENES` — estrutura, loader, saver e migração de arquivo

**Files:**
- Modify: `server.py:413-529` (bloco `TAVERN_SCENES` inteiro)
- Test: `tools/test_cenas_conversa.py` (criar)

- [ ] **Step 1: Escrever o teste que falha**

Criar `tools/test_cenas_conversa.py`:

```python
"""Cenas de conversa por local — várias cenas por cidade, vinculadas a pontos.
  • CITY_SCENES[cidade][cena] substitui TAVERN_SCENES[cidade].
  • Migração: tavern_scenes.json vira a cena de id "taverna".
  • Conversa de uso único some do payload depois de resolvida.
  • Conversa bloqueada por requisito não vaza texto.
Roda da raiz: python tools/test_cenas_conversa.py"""
import asyncio, json, os, shutil, sys, tempfile
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def isolar_arquivos():
    """Redireciona os JSON para uma pasta temporária e devolve o restaurador."""
    tmpdir = tempfile.mkdtemp(prefix="cenas_teste_")
    arquivos = ("CITY_SCENES_FILE", "CITY_MAP_POINTS_FILE", "CITY_SHOPS_FILE", "WORLD_CITIES_FILE")
    originais = {nome: getattr(S, nome) for nome in arquivos}
    for nome in arquivos:
        setattr(S, nome, os.path.join(tmpdir, nome.lower() + ".json"))
    inicial = {"scenes": deepcopy(S.CITY_SCENES), "points": deepcopy(S.CITY_MAP_POINTS),
               "shops": deepcopy(S.CITY_SHOPS)}
    def restaurar():
        for nome, valor in originais.items(): setattr(S, nome, valor)
        for alvo, copia in ((S.CITY_SCENES, inicial["scenes"]),
                            (S.CITY_MAP_POINTS, inicial["points"]),
                            (S.CITY_SHOPS, inicial["shops"])):
            alvo.clear(); alvo.update(copia)
        shutil.rmtree(tmpdir, ignore_errors=True)
    return restaurar

def _rodar_verificacoes():
    print("\n[1] Estrutura CITY_SCENES")
    check("CITY_SCENES existe", isinstance(S.CITY_SCENES, dict))
    check("cena da taverna sob a chave 'taverna'",
          isinstance(S.CITY_SCENES.get("alva_e_luz", {}).get("taverna"), dict))
    cena = S.CITY_SCENES["alva_e_luz"]["taverna"]
    check("cena tem nome", cena.get("nome") == "Taverna")
    check("cena preserva o fundo original", cena.get("background") == "assets/city/taverna.png")
    check("cena preserva os 8 slots", len(cena.get("slots", [])) == 8)
    check("cidade sem cenas nasce dict vazio",
          isinstance(S.CITY_SCENES.get("vila_riacho"), dict))

    print("\n[2] _cena_vazia")
    vazia = S._cena_vazia("Docas")
    check("nome aplicado", vazia["nome"] == "Docas")
    check("sem slots", vazia["slots"] == [])
    check("modo padrão individual", vazia["mode"] == "individual")

    print("\n[3] Loader cria cena nova vinda do arquivo")
    with open(S.CITY_SCENES_FILE, "w", encoding="utf-8") as f:
        json.dump({"alva_e_luz": {"docas": {
            "nome": "Docas", "background": "assets/city/docas.png",
            "mode": "individual", "mask": "", "slots": [
                {"id": "npc_pescador", "name": "Pescador", "image": "assets/tavern/slots/barman.png",
                 "x": 10, "y": 20, "w": 12, "h": 24, "z": 1, "dialog": "O mar anda estranho.",
                 "conversations": [{"id": "boato", "texto": "Vi luzes no farol.",
                                    "requisito": {}, "efeito": {"renome": 1, "fato": "farol", "item_id": ""},
                                    "uma_vez": True}]}]}}}, f)
    S._load_city_scenes()
    docas = S.CITY_SCENES["alva_e_luz"].get("docas")
    check("cena nova criada pelo arquivo", isinstance(docas, dict))
    check("slot da cena nova carregado", len(docas.get("slots", [])) == 1)
    check("conversa da cena nova carregada",
          docas["slots"][0]["conversations"][0]["id"] == "boato")
    check("taverna continua existindo", "taverna" in S.CITY_SCENES["alva_e_luz"])

    print("\n[4] Saver grava o dicionário inteiro")
    S._save_city_scenes()
    with open(S.CITY_SCENES_FILE, "r", encoding="utf-8") as f: gravado = json.load(f)
    check("arquivo tem as duas cenas de Alva e Luz",
          set(gravado.get("alva_e_luz", {})) >= {"taverna", "docas"})

    print("\n[5] Migração do tavern_scenes.json")
    antigo = os.path.join(os.path.dirname(S.CITY_SCENES_FILE), "tavern_antigo.json")
    novo = os.path.join(os.path.dirname(S.CITY_SCENES_FILE), "city_novo.json")
    with open(antigo, "w", encoding="utf-8") as f:
        json.dump({"graciero": {"background": "assets/city/g.png", "mode": "individual",
                                "mask": "", "slots": []}}, f)
    guarda = (S.CITY_SCENES_FILE, S.TAVERN_SCENES_FILE)
    S.CITY_SCENES_FILE, S.TAVERN_SCENES_FILE = novo, antigo
    S._migrar_tavern_scenes()
    with open(novo, "r", encoding="utf-8") as f: convertido = json.load(f)
    check("cena antiga vira a cena 'taverna'", "taverna" in convertido.get("graciero", {}))
    check("nome padrão aplicado", convertido["graciero"]["taverna"].get("nome") == "Taverna")
    check("arquivo antigo continua existindo", os.path.exists(antigo))
    S._migrar_tavern_scenes()   # idempotente: não sobrescreve o que já existe
    with open(novo, "r", encoding="utf-8") as f: check("migração é idempotente", json.load(f) == convertido)
    S.CITY_SCENES_FILE, S.TAVERN_SCENES_FILE = guarda

    print("\n[6] Teto de 16 cenas por cidade")
    muitas = {f"cena_{i}": {"nome": f"C{i}", "background": "", "mode": "individual",
                            "mask": "", "slots": []} for i in range(30)}
    with open(S.CITY_SCENES_FILE, "w", encoding="utf-8") as f:
        json.dump({"vila_riacho": muitas}, f)
    S._load_city_scenes()
    check("no máximo 16 cenas por cidade", len(S.CITY_SCENES["vila_riacho"]) <= 16)

def main():
    restaurar = isolar_arquivos()
    try: _rodar_verificacoes()
    finally: restaurar()
    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

main()
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

```bash
python tools/test_cenas_conversa.py
```

Esperado: `AttributeError: module 'server' has no attribute 'CITY_SCENES'`.

- [ ] **Step 3: Implementar — substituir o bloco `server.py:413-529`**

Trocar `TAVERN_SCENES = {...}` por `CITY_SCENES` com o nível de cena. O dicionário literal de `alva_e_luz` fica **idêntico**, só descendo um nível e ganhando `"nome": "Taverna"`:

```python
CITY_SCENES = {
    "alva_e_luz": {"taverna": {
        "nome": "Taverna",
        "background": "assets/city/taverna.png",
        "art_ratio": 1.5,
        "mode": "individual",
        "mask": "assets/tavern/frequentadores.png",
        "slots": [
            # ... os 8 slots atuais, sem nenhuma alteração ...
        ],
    }},
}
MAX_CENAS_POR_CIDADE = 16
CENA_ID_RE = re.compile(r"[a-z0-9_-]{1,48}")

def _cena_vazia(nome="Nova cena"):
    """Cena editável e sem conteúdo — o estado inicial de uma cena criada no editor."""
    return {"nome": str(nome)[:60], "background": "", "art_ratio": 1.5,
            "mode": "individual", "mask": "", "slots": []}
```

Renomear `_clean_tavern_conversations` → `_clean_scene_conversations` (mesmo corpo; atualizar as 4 chamadas: no próprio bloco de boot, em `_load_city_scenes`, em `handle_scene_npc` e em `_save_city_shops_upload`).

Semeadura das cidades (substitui `server.py:470-477`):

```python
for _cena_city_id in WORLD_LOCATIONS:
    if _cena_city_id in CITY_SCENES:
        continue
    CITY_SCENES[_cena_city_id] = (deepcopy(CITY_SCENES["alva_e_luz"])
                                  if _cena_city_id in _BUILTIN_WORLD_LOCATIONS else {})
for _cena_city_id in [c for c in CITY_SCENES if c not in WORLD_LOCATIONS]:
    del CITY_SCENES[_cena_city_id]

CITY_SCENES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "city_scenes.json")
TAVERN_SCENES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tavern_scenes.json")
```

Loader novo — diferente do antigo em um ponto essencial: **cria cenas inteiras**, porque a partir de agora a maioria não existe no código.

```python
def _cena_slot_novo(slot_id):
    return {"id": slot_id, "name": "Novo NPC", "image": "", "x": 40, "y": 40,
            "w": 14, "h": 20, "z": 1, "dialog": ""}

def _aplicar_cena_editada(current, scene):
    """Aplica sobre `current` os campos válidos de `scene` (arquivo ou editor)."""
    if isinstance(scene.get("nome"), str) and scene["nome"].strip():
        current["nome"] = scene["nome"].strip()[:60]
    for key in ("background", "mask"):
        value = scene.get(key)
        if value == "":
            current[key] = ""
        elif isinstance(value, str) and value.startswith("assets/"):
            current[key] = value
    if scene.get("mode") in ("individual", "mask"):
        current["mode"] = scene["mode"]
    by_id = {slot["id"]: slot for slot in current.get("slots", [])}
    for edited in scene.get("slots") or []:
        if not isinstance(edited, dict): continue
        if edited.get("id") not in by_id:
            new_id = str(edited.get("id") or "")
            if not re.fullmatch(r"npc_[a-zA-Z0-9_-]{1,48}", new_id) or len(by_id) >= 32: continue
            target = _cena_slot_novo(new_id)
            current["slots"].append(target); by_id[new_id] = target
        else: target = by_id[edited["id"]]
        for key in ("name", "dialog"):
            if isinstance(edited.get(key), str): target[key] = edited[key][:1200]
        if isinstance(edited.get("conversations"), list):
            target["conversations"] = _clean_scene_conversations(edited["conversations"], target.get("dialog", ""))
        if edited.get("remove_image") is True:
            target["image"] = ""
        elif isinstance(edited.get("image"), str) and edited["image"].startswith("assets/"):
            target["image"] = edited["image"]
        if isinstance(edited.get("removed"), bool): target["removed"] = edited["removed"]
        for key in ("x", "y", "w", "h", "z"):
            try:
                value = round(float(edited[key]), 2)
                if ((-100 <= value <= 100) if key == "z" else (0 <= value <= 100)):
                    target[key] = value
            except (KeyError, TypeError, ValueError): pass

def _migrar_tavern_scenes():
    """tavern_scenes.json (uma cena por cidade) → city_scenes.json (cena 'taverna').
    Roda uma única vez, quando o arquivo novo ainda não existe. O antigo fica
    intocado como rede de segurança."""
    if os.path.exists(CITY_SCENES_FILE) or not os.path.exists(TAVERN_SCENES_FILE):
        return
    try:
        with open(TAVERN_SCENES_FILE, "r", encoding="utf-8") as f: raw = json.load(f)
        if not isinstance(raw, dict): return
        convertido = {}
        for city_id, scene in raw.items():
            if isinstance(scene, dict):
                scene = dict(scene); scene.setdefault("nome", "Taverna")
                convertido[city_id] = {"taverna": scene}
        with open(CITY_SCENES_FILE, "w", encoding="utf-8") as f:
            json.dump(convertido, f, ensure_ascii=False, indent=2)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass

def _load_city_scenes():
    try:
        with open(CITY_SCENES_FILE, "r", encoding="utf-8") as f: raw = json.load(f)
        if not isinstance(raw, dict): return
        for city_id, cenas in raw.items():
            if city_id not in CITY_SCENES or not isinstance(cenas, dict): continue
            alvo = CITY_SCENES[city_id]
            for scene_id, scene in cenas.items():
                scene_id = str(scene_id or "").strip().lower()
                if not CENA_ID_RE.fullmatch(scene_id) or not isinstance(scene, dict): continue
                if scene_id not in alvo:
                    if len(alvo) >= MAX_CENAS_POR_CIDADE: continue
                    alvo[scene_id] = _cena_vazia(scene.get("nome") or scene_id)
                _aplicar_cena_editada(alvo[scene_id], scene)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        pass

def _save_city_scenes():
    temp = CITY_SCENES_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f: json.dump(CITY_SCENES, f, ensure_ascii=False, indent=2)
    os.replace(temp, CITY_SCENES_FILE)

_migrar_tavern_scenes()
_load_city_scenes()
for _cenas in CITY_SCENES.values():
    for _scene in _cenas.values():
        for _z_index, _slot in enumerate(_scene.get("slots", []), start=1):
            _slot.setdefault("z", _z_index)
            _slot["conversations"] = _clean_scene_conversations(_slot.get("conversations"), _slot.get("dialog", ""))
```

Apagar `TAVERN_SCENES`, `_cena_taverna_vazia`, `_load_tavern_scenes` e `_save_tavern_scenes`.

- [ ] **Step 4: Rodar o teste e confirmar que passa**

```bash
python tools/test_cenas_conversa.py
```

Esperado: `RESULTADO: 19 passaram, 0 falharam` (as seções [1]-[6]). Se o import de `server` quebrar, é porque sobrou alguma referência a `TAVERN_SCENES` — resolver nas próximas tasks só as que o interpretador acusar aqui.

- [ ] **Step 5: Commit**

```bash
git status
git add server.py tools/test_cenas_conversa.py
git commit -m "feat(cenas): CITY_SCENES por cidade com loader, saver e migracao"
```

---

## Task 2: Sincronia por cidade e vínculo do ponto da taverna

**Files:**
- Modify: `server.py:5030-5071` (`_sincronizar_cidades_derivadas`, `_garantir_pontos_implicitos`)
- Test: `tools/test_cenas_conversa.py`

- [ ] **Step 1: Escrever o teste que falha**

Adicionar em `_rodar_verificacoes()`, antes do `def main()`:

```python
    print("\n[7] Sincronia por cidade e vínculo do ponto")
    S.CITY_SCENES.setdefault("alva_e_luz", {})
    S._sincronizar_cidades_derivadas()
    ponto_taverna = S.CITY_MAP_POINTS["alva_e_luz"].get("taverna")
    check("ponto da taverna existe", isinstance(ponto_taverna, dict))
    check("ponto da taverna aponta para a cena taverna",
          ponto_taverna.get("scene") == "taverna")
    check("toda cidade tem entrada em CITY_SCENES",
          all(cid in S.CITY_SCENES for cid in S.WORLD_LOCATIONS))
    S.CITY_SCENES["cidade_fantasma"] = {}
    S._sincronizar_cidades_derivadas()
    check("cidade inexistente é removida", "cidade_fantasma" not in S.CITY_SCENES)
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_cenas_conversa.py
```

Esperado: falha em "ponto da taverna aponta para a cena taverna" (o campo `scene` ainda não existe).

- [ ] **Step 3: Implementar**

Em `_sincronizar_cidades_derivadas`, trocar as duas linhas de `TAVERN_SCENES`:

```python
    for cid in [c for c in CITY_SCENES if c not in WORLD_LOCATIONS]:
        del CITY_SCENES[cid]
    for cid in WORLD_LOCATIONS:
        CITY_SHOPS.setdefault(cid, {})
        CITY_MAP_POINTS.setdefault(cid, {})
        CITY_SCENES.setdefault(cid, {})
```

Em `_garantir_pontos_implicitos`, depois do laço que cria os pontos, ligar cada ponto à cena de mesmo id quando ela existir e o ponto ainda não tiver vínculo:

```python
        # Vínculo implícito: um ponto cujo id casa com o id de uma cena da cidade
        # já nasce ligado a ela. É o que faz a taverna migrada abrir sozinha,
        # sem nenhum caso especial no runtime.
        cenas = CITY_SCENES.get(cid, {})
        for pid_ponto, ponto in pontos.items():
            if not ponto.get("scene") and pid_ponto in cenas:
                ponto["scene"] = pid_ponto
```

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
python tools/test_cenas_conversa.py
```

Esperado: **0 falharam** — os 4 checks novos da seção [7] entram no total.

- [ ] **Step 5: Commit**

```bash
git status
git add server.py tools/test_cenas_conversa.py
git commit -m "feat(cenas): sincronia por cidade e vinculo implicito ponto-cena"
```

---

## Task 3: Payload — `city_state.scenes` com omissão das conversas indisponíveis

**Files:**
- Modify: `server.py:6839-6851` (`_tavern_payload`), `server.py:6812` (`_city_state_payload`)
- Test: `tools/test_cenas_conversa.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[8] Payload das cenas")
    reset = S._sincronizar_cidades_derivadas
    sala = S.GameRoom("CENA")
    async def noop(*a, **k): pass
    sala.gm_say = noop; sala.broadcast = noop; sala.send_to = noop
    sala._checkpoint_savegame = lambda *a, **k: None
    sala.phase = "city"; sala.world_location = "alva_e_luz"
    sala.players["p1"] = S.make_player("p1", "Victor", "warrior", 0)
    S.CITY_SCENES["alva_e_luz"]["provas"] = {
        "nome": "Provas", "background": "assets/city/x.png", "art_ratio": 1.5,
        "mode": "individual", "mask": "", "slots": [
            {"id": "npc_teste", "name": "Teste", "image": "assets/x.png",
             "x": 5, "y": 5, "w": 10, "h": 10, "z": 1, "dialog": "",
             "conversations": [
                 {"id": "livre",   "texto": "SEGREDO-LIVRE",   "requisito": {},
                  "efeito": {"renome": 0, "fato": "", "item_id": ""}, "uma_vez": False},
                 {"id": "unica",   "texto": "SEGREDO-UNICA",   "requisito": {},
                  "efeito": {"renome": 0, "fato": "", "item_id": ""}, "uma_vez": True},
                 {"id": "trancada","texto": "SEGREDO-TRANCADA",
                  "requisito": {"renome_min": 999},
                  "efeito": {"renome": 0, "fato": "", "item_id": ""}, "uma_vez": False},
             ]}]}
    cenas = sala._cenas_payload()
    check("payload traz a cena nova", "provas" in cenas)
    ids = [c["id"] for c in cenas["provas"]["slots"][0]["conversations"]]
    check("conversa livre aparece", "livre" in ids)
    check("conversa de uso único ainda não usada aparece", "unica" in ids)
    check("conversa trancada NÃO aparece", "trancada" not in ids)
    check("texto da trancada não vaza", "SEGREDO-TRANCADA" not in json.dumps(cenas))
    sala.scene_conversations_done.add("alva_e_luz:provas:npc_teste:unica")
    cenas2 = sala._cenas_payload()
    ids2 = [c["id"] for c in cenas2["provas"]["slots"][0]["conversations"]]
    check("uso único resolvido some do payload", "unica" not in ids2)
    check("uso repetido continua", "livre" in ids2)
    payload = sala._city_state_payload()
    check("city_state manda scenes", isinstance(payload.get("scenes"), dict))
    check("city_state não manda mais tavern", "tavern" not in payload)
    del S.CITY_SCENES["alva_e_luz"]["provas"]
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_cenas_conversa.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute '_cenas_payload'`.

- [ ] **Step 3: Implementar**

Substituir `_tavern_payload` por:

```python
    def _cenas_payload(self):
        """Cenas da cidade atual. Conversa bloqueada por requisito ou de uso
        único já resolvida NÃO entra no payload — o texto não sai do servidor,
        e o cliente não precisa de filtro."""
        cenas = deepcopy(CITY_SCENES.get(self.world_location) or {})
        for scene_id, scene in cenas.items():
            for slot in scene.get("slots", []):
                disponiveis = []
                for conversation in slot.get("conversations", []):
                    available, _reasons = self._avaliar_requisito(conversation.get("requisito"))
                    key = f"{self.world_location}:{scene_id}:{slot.get('id')}:{conversation.get('id')}"
                    gasta = conversation.get("uma_vez") and key in self.scene_conversations_done
                    if available and not gasta:
                        disponiveis.append(conversation)
                slot["conversations"] = disponiveis
        return cenas
```

Em `_city_state_payload` (`server.py:6812`), trocar:

```python
            "scenes": self._cenas_payload(),
```

Renomear o atributo em `server.py:6283`:

```python
        self.scene_conversations_done = set()
```

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
python tools/test_cenas_conversa.py
```

Esperado: **0 falharam** — os 9 checks novos da seção [8] entram no total.

- [ ] **Step 5: Commit**

```bash
git status
git add server.py tools/test_cenas_conversa.py
git commit -m "feat(cenas): payload city_state.scenes omitindo conversas indisponiveis"
```

---

## Task 4: `handle_scene_npc` e a chave de 4 partes

**Files:**
- Modify: `server.py:8591-8624` (`handle_tavern_npc`), `server.py:23145` (dispatch)
- Test: `tools/test_cenas_conversa.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[9] handle_scene_npc")
    S.CITY_SCENES["alva_e_luz"]["provas"] = {
        "nome": "Provas", "background": "assets/city/x.png", "art_ratio": 1.5,
        "mode": "individual", "mask": "", "slots": [
            {"id": "npc_teste", "name": "Teste", "image": "assets/x.png",
             "x": 5, "y": 5, "w": 10, "h": 10, "z": 1, "dialog": "",
             "conversations": [
                 {"id": "unica", "texto": "Pronto.", "requisito": {},
                  "efeito": {"renome": 3, "fato": "pista_a", "item_id": ""}, "uma_vez": True}]}]}
    erros = []
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": erros.append(msg["msg"])
    sala.send_to = cap_send
    sala.renome = 0; sala.fatos = set(); sala.scene_conversations_done = set()
    asyncio.run(sala.handle_scene_npc("p1", "provas", "npc_teste", "unica"))
    check("renome concedido", sala.renome == 3)
    check("fato registrado", "pista_a" in sala.fatos)
    check("chave tem 4 partes",
          "alva_e_luz:provas:npc_teste:unica" in sala.scene_conversations_done)
    asyncio.run(sala.handle_scene_npc("p1", "provas", "npc_teste", "unica"))
    check("segunda vez recusada", any("já foi concluída" in e for e in erros))
    check("renome não subiu de novo", sala.renome == 3)
    erros.clear()
    asyncio.run(sala.handle_scene_npc("p1", "inexistente", "npc_teste", "unica"))
    check("cena inexistente recusada", any("Cena" in e for e in erros))
    del S.CITY_SCENES["alva_e_luz"]["provas"]
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_cenas_conversa.py
```

Esperado: `AttributeError: 'GameRoom' object has no attribute 'handle_scene_npc'`.

- [ ] **Step 3: Implementar**

Renomear `handle_tavern_npc` → `handle_scene_npc` com o parâmetro novo e a resolução da cena:

```python
    async def handle_scene_npc(self, pid, scene_id, npc_id, conversation_id):
        if not self._em_cidade(pid) or pid not in self.players:
            return
        cenas = CITY_SCENES.get(self.world_location) or {}
        scene = cenas.get(str(scene_id or ""))
        if not scene:
            await self.send_to(pid, {"type":"error", "msg":"Cena não encontrada."}); return
        slot = next((s for s in scene.get("slots", []) if s.get("id") == str(npc_id) and not s.get("removed")), None)
        if not slot:
            await self.send_to(pid, {"type":"error", "msg":"Frequentador não encontrado."}); return
        conversations = _clean_scene_conversations(slot.get("conversations"), slot.get("dialog", ""))
        conversation = next((c for c in conversations if c["id"] == str(conversation_id)), None)
        if not conversation:
            await self.send_to(pid, {"type":"error", "msg":"Conversa não encontrada."}); return
        key = f"{self.world_location}:{scene_id}:{slot['id']}:{conversation['id']}"
        if conversation.get("uma_vez") and key in self.scene_conversations_done:
            await self.send_to(pid, {"type":"error", "msg":"Esta conversa já foi concluída."}); return
        # ... daqui em diante o corpo atual, sem alteração, trocando apenas
        # self.tavern_conversations_done.add(key) por self.scene_conversations_done.add(key)
```

Dispatch (`server.py:23145`):

```python
                elif t == "scene_npc":
                    if room: await room.handle_scene_npc(pid, msg.get("scene_id"), msg.get("npc_id"), msg.get("conversation_id"))
```

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
python tools/test_cenas_conversa.py
```

Esperado: **0 falharam** — os 6 checks novos da seção [9] entram no total.

- [ ] **Step 5: Commit**

```bash
git status
git add server.py tools/test_cenas_conversa.py
git commit -m "feat(cenas): handle_scene_npc com chave cidade:cena:npc:conversa"
```

---

## Task 5: Migração das chaves de savegame

**Files:**
- Modify: `server.py:1302`, `server.py:1313`, `server.py:1496`, `server.py:13047`
- Test: `tools/test_cenas_conversa.py`

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[10] Migração das chaves de savegame")
    check("chave antiga de 3 partes ganha 'taverna'",
          S._migrar_chaves_conversa(["alva_e_luz:barman:inicial"])
          == {"alva_e_luz:taverna:barman:inicial"})
    check("chave nova de 4 partes fica intacta",
          S._migrar_chaves_conversa(["alva_e_luz:docas:npc_x:y"])
          == {"alva_e_luz:docas:npc_x:y"})
    check("lixo é descartado",
          S._migrar_chaves_conversa(["", "a:b", 42, None]) == set())
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_cenas_conversa.py
```

Esperado: `AttributeError: module 'server' has no attribute '_migrar_chaves_conversa'`.

- [ ] **Step 3: Implementar**

Helper module-level, perto das outras funções de savegame:

```python
def _migrar_chaves_conversa(raw):
    """Chaves de conversa concluída. O formato antigo tinha 3 partes
    (cidade:npc:conversa, quando só existia a taverna); o novo tem 4
    (cidade:cena:npc:conversa). Insere 'taverna' nas antigas para o jogador
    não ver conversas já resolvidas voltarem."""
    saida = set()
    for k in raw or []:
        if not isinstance(k, str): continue
        partes = k[:200].split(":")
        if len(partes) == 4: saida.add(":".join(partes))
        elif len(partes) == 3: saida.add(f"{partes[0]}:taverna:{partes[1]}:{partes[2]}")
    return saida
```

Na carga do savegame (`server.py:1496`), aceitar a chave nova com fallback para a antiga:

```python
    room.scene_conversations_done = _migrar_chaves_conversa(
        sg.get("scene_conversations_done") or sg.get("tavern_conversations_done") or [])
```

Na gravação (`server.py:13047`):

```python
        self.savegame["scene_conversations_done"] = sorted(self.scene_conversations_done)
```

Nos dois lugares que listam as chaves do savegame (`server.py:1302` e `server.py:1313`), trocar `"tavern_conversations_done"` por `"scene_conversations_done"`.

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
python tools/test_cenas_conversa.py
python tools/test_jogos_salvos.py
```

Esperado: o primeiro com **0 falharam** (3 checks novos na seção [10]); o segundo sem regressão. Se `tools/test_jogos_salvos.py` não existir com esse nome, localizar com `ls tools/test_*.py` e rodar o de savegames.

- [ ] **Step 5: Commit**

```bash
git status
git add server.py tools/test_cenas_conversa.py
git commit -m "feat(cenas): migra chaves de conversa concluida de 3 para 4 partes"
```

---

## Task 6: Editor no servidor — payload, validação de cenas, ponto `cena` e emoji

**Files:**
- Modify: `server.py` — bloco de pontos de `_save_city_shops_upload`
- Test: `tools/test_cenas_conversa.py`

> **Escopo reduzido na execução.** A renomeação da chave do payload
> (`taverns` → `scenes`), o bloco que aplica as cenas em `_save_city_shops_upload`
> e as chamadas a `_save_city_scenes` foram **antecipados para a Task 1**. Motivo:
> a Task 1 mudou a forma do payload sem mudar o caminho de gravação, e a revisão
> de qualidade reproduziu um `KeyError` — e, no ramo que não estoura, a escrita de
> `background`/`mask` soltos dentro do dicionário de cenas, corrompendo o
> `city_scenes.json`. Cinco tasks com risco de corromper dados do usuário não é um
> estado intermediário aceitável. Sobra para esta task: **remoção de cena órfã**,
> **tipo de ponto `cena`**, **`emoji`** e **campo `scene` no ponto**.

- [ ] **Step 1: Escrever o teste que falha**

```python
    print("\n[11] Save do editor: cenas, ponto tipo cena e emoji")
    S._sincronizar_cidades_derivadas()
    cenas_editor = {"alva_e_luz": {"docas": {
        "nome": "Docas", "background": "assets/city/docas.png", "mode": "individual",
        "mask": "", "slots": [
            {"id": "npc_pescador", "name": "Pescador", "image": "assets/tavern/slots/barman.png",
             "x": 10, "y": 20, "w": 12, "h": 24, "z": 1, "dialog": "Olá.",
             "conversations": [{"id": "boato", "texto": "Luzes no farol.", "requisito": {},
                                "efeito": {"renome": 1, "fato": "farol", "item_id": ""},
                                "uma_vez": True}]}]}}}
    pontos_editor = {"alva_e_luz": dict(S.CITY_MAP_POINTS["alva_e_luz"], **{
        "docas": {"x": 18, "y": 72, "type": "cena", "emoji": "🌊",
                  "name": "Docas", "scene": "docas"}})}
    ok, cfg = S._save_city_shops_upload(S.CITY_SHOPS, cenas_editor, pontos_editor)
    check("save aceito", ok is True)
    check("cena gravada", "docas" in S.CITY_SCENES["alva_e_luz"])
    check("ponto tipo cena aceito",
          S.CITY_MAP_POINTS["alva_e_luz"]["docas"].get("type") == "cena")
    check("emoji preservado", S.CITY_MAP_POINTS["alva_e_luz"]["docas"].get("emoji") == "🌊")
    check("vinculo preservado", S.CITY_MAP_POINTS["alva_e_luz"]["docas"].get("scene") == "docas")
    S.CITY_SCENES["alva_e_luz"]["orfa"] = S._cena_vazia("Órfã")
    S.CITY_MAP_POINTS["alva_e_luz"]["docas"]["scene"] = "orfa"
    S._save_city_shops_upload(S.CITY_SHOPS, cenas_editor, pontos_editor)
    check("cena ausente do envio é excluída", "orfa" not in S.CITY_SCENES["alva_e_luz"])
    check("ponto perde o vínculo com a cena excluída",
          S.CITY_MAP_POINTS["alva_e_luz"]["docas"].get("scene") != "orfa")
    S.CITY_MAP_POINTS["alva_e_luz"].pop("docas", None)
    S.CITY_SCENES["alva_e_luz"].pop("docas", None)
```

- [ ] **Step 2: Rodar e confirmar que falha**

```bash
python tools/test_cenas_conversa.py
```

Esperado: falha em "cena gravada" (o parâmetro ainda é `taverns`, com o formato antigo).

- [ ] **Step 3: Implementar**

Em `_save_city_shops_upload`, o laço de cenas já existe (Task 1). Acrescentar ao final dele, ainda dentro do `for city_id, cenas in scenes.items()`, a exclusão de cena órfã:

```python
            # Cena removida no editor some do servidor. Como o editor sempre
            # envia o conjunto completo da cidade, ausência = exclusão.
            for orfa in [s for s in alvo if s not in cenas]:
                del alvo[orfa]
                for ponto in CITY_MAP_POINTS.get(city_id, {}).values():
                    if ponto.get("scene") == orfa: ponto.pop("scene", None)
```

No bloco de pontos, ampliar os tipos e aceitar `emoji` e `scene`:

```python
        valid_types = {"ferreiro", "mercador", "templo", "taverna", "guilda",
                       "dungeon", "caravana", "cena"}
        ...
                if point_type in valid_types: item["type"] = point_type
                name = str(point.get("name") or "").strip()
                if name: item["name"] = name[:60]
                emoji = str(point.get("emoji") or "").strip()
                if emoji: item["emoji"] = emoji[:8]
                scene_ref = str(point.get("scene") or "").strip().lower()
                if scene_ref and scene_ref in CITY_SCENES.get(city_id, {}):
                    item["scene"] = scene_ref
```

As chamadas a `_save_city_scenes()` e o dispatch com `msg.get("scenes")` já foram feitos na Task 1 — conferir que continuam certos, sem mexer.

- [ ] **Step 4: Rodar e confirmar que passa**

```bash
python tools/test_cenas_conversa.py
python tools/test_cidades_editor.py
```

Esperado: os dois com **0 falharam** (7 checks novos na seção [11]).

> `tools/test_cidades_editor.py` já foi adaptado na Task 1 — remover `TAVERN_SCENES` quebrava o import dele, e deixá-lo vermelho por cinco tasks esconderia regressões de verdade. Aqui ele só precisa continuar passando.

- [ ] **Step 5: Commit**

```bash
git status
git add server.py tools/test_cenas_conversa.py tools/test_cidades_editor.py
git commit -m "feat(cenas): editor grava cenas, ponto tipo cena, emoji e vinculo"
```

---

## Task 7: Cliente — camada de estado

**Files:**
- Modify: `src/gameState.js:1458` (`talkTavernNpc`), `src/gameState.js:2388` (export), handler de `city_state`
- Test: manual (a camada não tem teste automatizado no projeto)

- [ ] **Step 1: Implementar**

Trocar a função de envio:

```javascript
  function talkSceneNpc(sceneId, npcId, conversationId) {
    send({ type: 'scene_npc', scene_id: sceneId, npc_id: npcId, conversation_id: conversationId });
  }
```

Adicionar o estado da cena aberta e os getters, perto dos outros getters de cidade:

```javascript
  let activeScene = null;   // id da cena aberta no modal (null = nenhuma)

  // Cenas da cidade atual, como vieram do servidor.
  function scenes() { return (cityState && cityState.scenes) || {}; }
  // Cena vinculada a um ponto do mapa da cidade (null se o ponto não tem uma).
  function sceneOfPoint(pointId) {
    const pontos = ((cityState && cityState.city_map_points) || {})[cityState && cityState.location] || {};
    const ref = (pontos[pointId] || {}).scene;
    return ref ? (scenes()[ref] || null) : null;
  }
  function sceneIdOfPoint(pointId) {
    const pontos = ((cityState && cityState.city_map_points) || {})[cityState && cityState.location] || {};
    return (pontos[pointId] || {}).scene || null;
  }
```

Exportar `talkSceneNpc`, `scenes`, `sceneOfPoint`, `sceneIdOfPoint` e o par get/set de `activeScene` no objeto exportado (linha ~2388), no mesmo estilo dos vizinhos.

Conferir se `cityState.location` é o campo certo — no payload a cidade atual está em `city_state.world.location` (`server.py:6795`). Usar `cityState.world && cityState.world.location`.

- [ ] **Step 2: Verificar que o módulo carrega**

```bash
node --check src/gameState.js
```

Esperado: sem saída (sintaxe válida).

- [ ] **Step 3: Commit**

```bash
git status
git add src/gameState.js
git commit -m "feat(cenas): camada de estado do cliente para cenas por ponto"
```

---

## Task 8: Cliente — abrir pelo ponto e montar as abas

**Files:**
- Modify: `game.js:1488-1495` (`_cityHotspotClick`), `game.js:1568`, `game.js:1266-1273` (`_cityClick`), `game.js:1956-1997` (`openShop`), `game.js:2104-2110` (`_renderShopItems`)

- [ ] **Step 1: Implementar o despacho por ponto**

`_cityHotspotClick` passa a receber id do ponto e tipo:

```javascript
function _cityHotspotClick(pointId, type){
  const t = type || pointId;
  // Destinos próprios continuam despachando pelo tipo, antes da resolução de
  // cena/loja — e o editor não oferece esses pontos no vínculo de cena.
  if(t === 'dungeon'){ triggerDungeonEntrance(); return; }
  if(t === 'caravana'){ showWorldMap(); return; }
  if(t === 'guilda'){ openGuild(); return; }
  openShop(pointId, t);
}
```

Nos três pontos de chamada, passar os dois argumentos:
- `game.js:1440` — `_cityHotspotClick(bd.id, bd.id)`
- `game.js:1568` — `_cityHotspotClick(id, point.type)`
- `game.js:1266-1273` (`_cityClick`, 3D) — resolve o tipo para o primeiro ponto daquele tipo na cidade:

```javascript
function _pontoDoTipo(type){
  const st = GS.cityState || {};
  const pontos = (st.city_map_points || {})[(st.world || {}).location] || {};
  const achado = Object.keys(pontos).find(id => (pontos[id].type || id) === type);
  return achado || type;
}
```

e no `_cityClick`, trocar `openShop(id)` por `_cityHotspotClick(_pontoDoTipo(id), id)`.

- [ ] **Step 2: Implementar a montagem de abas em `openShop`**

`openShop(pointId, type)`:

```javascript
function openShop(pointId, type){
  if(!GS.cityState){ GS.pendingShopOpen = pointId; send({type:'get_city_state'}); toast('Carregando loja…','var(--blue)'); return; }
  GS.pendingShopOpen = null;
  const shopId = type || pointId;
  const sceneId = GS.sceneIdOfPoint(pointId);
  const scene   = GS.sceneOfPoint(pointId);
  GS.activeShop = shopId; GS.activeScene = scene ? sceneId : null; GS.shopTabIdx = 0;
  ...
  const shopTabs = shopId==='ferreiro' ? ['⚔ Armas','🛡 Armaduras','🏹 Munição','💰 Vender']
    : shopId==='mercador' ? ['🛒 Comprar','🎵 Instrumentos','☠️ Venenos','📜 Pergaminhos','💰 Vender']
    : shopId==='taverna'  ? ['🍺 Alimentos']
    : [];
  const tabDefs = (scene ? ['💬 ' + (scene.nome || 'Conversas')] : []).concat(shopTabs);
```

A aba de cena, quando existe, é sempre a de índice 0. `_renderShopItems` deixa de testar taverna e passa a testar a cena:

```javascript
  if(GS.activeScene && GS.shopTabIdx === 0){ _renderTavernConversations(); return; }
```

> Nesta task a função de render **ainda se chama** `_renderTavernConversations` — a Task 10 é que a renomeia para `_renderCenaConversas` e atualiza esta chamada. Não antecipar o nome novo aqui, ou o código quebra entre as duas tasks.

Como a aba de cena consome o índice 0, os índices das abas de venda deslocam 1 quando há cena. Corrigir os dois roteamentos de venda usando um offset:

```javascript
  const off = GS.activeScene ? 1 : 0;
  if(GS.activeShop==='ferreiro' && GS.shopTabIdx===3+off){ _renderSellItems('gear'); return; }
  if(GS.activeShop==='mercador' && GS.shopTabIdx===4+off){ _renderSellItems('bag');  return; }
```

e aplicar o mesmo `off` em todo lugar de `_renderShopItems` que compara `GS.shopTabIdx` com um número para escolher a lista de itens da loja (bloco `if(GS.activeShop==='ferreiro'){ ... }` em diante).

A taverna perde a aba "💬 Conversas" hardcoded: ela agora vem da cena vinculada ao ponto.

- [ ] **Step 3: Verificar sintaxe**

```bash
node --check game.js
```

Esperado: sem saída.

- [ ] **Step 4: Commit**

```bash
git status
git add game.js
git commit -m "feat(cenas): abre o modal pelo ponto e monta abas cena + loja"
```

---

## Task 9: Cliente — pontos da ilustração com tipo `cena` e emoji livre

**Files:**
- Modify: `game.js:1527-1569`

- [ ] **Step 1: Implementar**

`pointMeta` ganha o tipo `cena`:

```javascript
  const pointMeta = {
    ferreiro:{name:'Ferreiro',emoji:'⚒'}, mercador:{name:'Mercador',emoji:'🛒'},
    templo:{name:'Templo',emoji:'⛪'}, taverna:{name:'Taverna',emoji:'🍺'},
    guilda:{name:'Guilda',emoji:'⚔'}, caravana:{name:'Caravana de Viagem',emoji:'🧭'},
    dungeon:{name:'Entrada da masmorra',emoji:'🚪'}, cena:{name:'Local',emoji:'💬'}
  };
```

`pointAllowed` libera `cena` (não depende de loja):

```javascript
  const pointAllowed = type => type === 'caravana' || type === 'guilda' || type === 'dungeon'
    || type === 'cena' || isAlva || hasShopPoint(type);
```

O emoji do ponto sobrepõe o do tipo, quando presente:

```javascript
    const emoji = point.emoji || meta.emoji;
    btn.innerHTML='<span class="ch-glow" aria-hidden="true"></span><span class="ch-pin"><span class="ch-emoji">'+emoji+'</span><span class="ch-name">'+label+'</span></span>';
```

- [ ] **Step 2: Verificar sintaxe**

```bash
node --check game.js
```

- [ ] **Step 3: Commit**

```bash
git status
git add game.js
git commit -m "feat(cenas): ponto tipo cena e emoji livre na ilustracao da cidade"
```

---

## Task 10: Renomear `tavern-*` → `cena-*`

**Files:**
- Modify: `game.css:496-540`, `game.js:2005-2100`

- [ ] **Step 1: Renomear no CSS**

Em `game.css`, trocar os seletores: `.tavern-scene`→`.cena-palco`, `.tavern-bg`→`.cena-bg`, `.tavern-mask-layer`→`.cena-mask-layer`, `.tavern-npc`→`.cena-npc`, `.tavern-mask`→`.cena-mask`, `.tavern-back`→`.cena-back`, `.tavern-hint`→`.cena-hint`, `.tavern-hud`→`.cena-hud`, `.tavern-dialogue*`→`.cena-dialogo*`, `.tavern-empty`→`.cena-vazia`, `#shop-modal.tavern-cena`→`#shop-modal.modo-cena`, `#shop-modal.shop-taverna .shop-box`→ manter (é da loja, não da cena).

Atenção ao seletor composto `#shop-modal.tavern-cena .tavern-scene>.tavern-hint`, que precisa dos três nomes trocados.

- [ ] **Step 2: Renomear no JS**

Em `game.js`: `_renderTavernConversations`→`_renderCenaConversas`, `_showTavernDialogue`→`_showCenaDialogo`, `_openTavernNpcId`→`_openCenaNpcId`, e todas as strings de `className` correspondentes. A chamada `GS.talkTavernNpc(slot.id, conv.id)` vira `GS.talkSceneNpc(GS.activeScene, slot.id, conv.id)`.

`_renderCenaConversas` passa a ler a cena ativa em vez de `GS.cityState.tavern`:

```javascript
function _renderCenaConversas(){
  const list=$('shop-items-list'); if(!list) return;
  const cena = GS.scenes()[GS.activeScene];
  if(!cena || !cena.background){
    list.innerHTML='<div class="cena-vazia">Este local ainda não possui frequentadores configurados.</div>';
    return;
  }
  const modal=$('shop-modal'); if(modal) modal.classList.add('modo-cena');
  // ... resto idêntico, trocando `tavern` por `cena` nas leituras de campo ...
```

O filtro `conversations.filter(conv=>!conv.oculta)` **some**: o servidor já omite. A variável passa a ser a lista crua:

```javascript
  const discovered = conversations;
```

- [ ] **Step 3: Verificar que nenhuma referência antiga sobrou**

```bash
grep -n "tavern" game.js game.css
```

Esperado: apenas ocorrências legítimas — `shop-taverna` (classe da loja), `taverna` como id de loja/prédio, e caminhos `assets/tavern/`. Nenhuma `tavern-scene`, `tavern-npc`, `tavern-dialogue`, `tavern-hud`, `_renderTavernConversations`, `_showTavernDialogue`, `talkTavernNpc`.

```bash
node --check game.js
```

- [ ] **Step 4: Commit**

```bash
git status
git add game.js game.css
git commit -m "refactor(cenas): renomeia tavern-* para cena-* no cliente"
```

---

## Task 11: Editor — lista de cenas e vínculo com o ponto

**Files:**
- Modify: `tools/editor_city.js:52` (rótulo da aba), `:67-238` (`renderTavern`), `:239-243` (`saveAll`)

- [ ] **Step 1: Implementar**

Rótulo da aba (`cityTabs`): `botao("tavern", "💬 Taverna e NPCs")` → `botao("scenes", "💬 Cenas e NPCs")`, e `mode = "scenes"` no despacho de `render()`.

Estado do módulo ganha `selectedSceneId` (junto de `selectedNpcId`, linha 5).

`renderTavern` vira `renderScenes`, lendo `config.scenes[cityId]` (dicionário) em vez de `config.taverns[cityId]` (cena única). No topo da seção, antes do bloco de assets:

```javascript
    const cenas = (config.scenes || {})[cityId] || ((config.scenes = config.scenes || {})[cityId] = {});
    if (!cenas[selectedSceneId]) selectedSceneId = Object.keys(cenas)[0] || null;
    const abasCena = '<div class="cityed-cities">' + Object.entries(cenas).map(([id, s]) =>
      '<button data-scene="' + esc(id) + '" class="' + (id === selectedSceneId ? 'active' : '') + '">'
      + esc(s.nome || id) + '<small>' + esc(id) + '</small></button>').join('')
      + '<button data-scene-new type="button">+ Nova cena</button></div>';
```

O painel da cena selecionada é o de hoje (fundo, máscara, NPCs, conversas, prévia) mais dois campos:

```javascript
    const pontos = (config.city_points || {})[cityId] || {};
    const VINCULAVEIS = id => !['dungeon','caravana','guilda'].includes(pontos[id].type || id);
    const vinculado = Object.keys(pontos).find(id => pontos[id].scene === selectedSceneId) || '';
    const campoNome = '<label>Nome da cena<input data-scene-nome value="' + esc(cena.nome || '') + '"></label>';
    const campoVinc = '<label>Vinculada a<select data-scene-ponto><option value="">— nenhum ponto —</option>'
      + Object.keys(pontos).filter(VINCULAVEIS).map(id =>
        '<option value="' + esc(id) + '"' + (id === vinculado ? ' selected' : '') + '>'
        + esc(pontos[id].name || id) + '</option>').join('')
      + '</select></label><button type="button" data-scene-novo-ponto>+ Criar ponto para esta cena</button>';
```

Bindings:

```javascript
    root.querySelectorAll('[data-scene]').forEach(b => b.onclick = () => { selectedSceneId = b.dataset.scene; render(); });
    const btnNova = root.querySelector('[data-scene-new]');
    if (btnNova) btnNova.onclick = () => {
      const nome = prompt('Nome da cena (ex.: Docas)'); if (!nome) return;
      const id = (nome.toLowerCase().normalize('NFD').replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'cena') + '_' + Date.now().toString(36).slice(-4);
      cenas[id] = { nome: nome, background: '', art_ratio: 1.5, mode: 'individual', mask: '', slots: [] };
      selectedSceneId = id; render();
    };
    const selPonto = root.querySelector('[data-scene-ponto]');
    if (selPonto) selPonto.onchange = () => {
      // Um ponto tem no máximo uma cena: limpa o vínculo anterior antes de gravar.
      Object.values(pontos).forEach(p => { if (p.scene === selectedSceneId) delete p.scene; });
      if (selPonto.value && pontos[selPonto.value]) pontos[selPonto.value].scene = selectedSceneId;
      render();
    };
    const btnNovoPonto = root.querySelector('[data-scene-novo-ponto]');
    if (btnNovoPonto) btnNovoPonto.onclick = () => {
      const nome = prompt('Nome do ponto na ilustração', cena.nome || 'Novo local'); if (!nome) return;
      const emoji = prompt('Emoji do marcador', '💬') || '💬';
      const id = selectedSceneId;
      Object.values(pontos).forEach(p => { if (p.scene === id) delete p.scene; });
      pontos[id] = { x: 50, y: 50, type: 'cena', name: nome, emoji: emoji, scene: id };
      (config.city_points = config.city_points || {})[cityId] = pontos;
      render();
    };
```

`saveAll` passa a mandar `config.scenes`:

```javascript
    config = await window.EDITOR_SAVE.saveCityShops(config.stock, config.scenes, config.city_points);
```

(as duas chamadas: em `saveAll` e em `renderCityMap`).

Em `renderCityMap`, o dropdown de tipos ganha `cena:'Local de conversa'` e um campo de emoji ao lado do nome.

- [ ] **Step 2: Ajustar o envio no cliente do editor**

Em `tools/story_upload.js` (ou onde `EDITOR_SAVE.saveCityShops` monta a mensagem), renomear a chave `taverns` para `scenes` no payload de `save_city_shops`. Localizar com:

```bash
grep -rn "taverns" tools/
```

- [ ] **Step 3: Verificar sintaxe**

```bash
node --check tools/editor_city.js
```

- [ ] **Step 4: Commit**

```bash
git status
git add tools/editor_city.js tools/story_upload.js
git commit -m "feat(cenas): editor com lista de cenas, vinculo e ponto novo"
```

---

## Task 12: Verificação ponta a ponta no jogo

**Files:** nenhum (verificação)

- [ ] **Step 1: Rodar a bateria de testes de servidor**

```bash
python tools/test_cenas_conversa.py
python tools/test_cidades_editor.py
python tools/test_masmorra_sequenciada.py
python tools/test_guilda.py
```

Esperado: todos com `0 falharam`. Anotar qualquer falha **pré-existente** antes de atribuí-la a esta entrega — conferir contra `git stash` se necessário.

- [ ] **Step 2: Subir o jogo e abrir a taverna migrada**

Usar `preview_start` (nunca `python server.py` pelo Bash). Entrar numa sala, escolher um herói, iniciar. Na cidade:

1. clicar na Taverna → a cena abre em tela cheia, com a aba "💬 Taverna" e "🍺 Alimentos";
2. clicar num frequentador → o painel de conversa aparece;
3. resolver uma conversa de uso único → ela **some** da lista sem recarregar a página;
4. trocar para "🍺 Alimentos" → volta o modal normal;
5. clicar no Ferreiro → só abas de compra, layout idêntico ao de antes.

- [ ] **Step 3: Criar uma cena nova pelo editor e testar no jogo**

No editor de cidades, aba "💬 Cenas e NPCs": criar a cena "Docas", enviar um fundo, adicionar um NPC com uma conversa, criar o ponto pelo botão, salvar. No jogo (recarregar a cidade), o marcador 🌊 Docas aparece na ilustração e abre a cena só com a aba de conversa.

- [ ] **Step 4: Conferir que nada vaza no payload**

Com uma conversa bloqueada por renome alto configurada, no console do navegador:

```javascript
JSON.stringify(GS.cityState.scenes).includes('TEXTO-DA-CONVERSA-BLOQUEADA')
```

Esperado: `false`.

- [ ] **Step 5: Commit final**

Se as tasks anteriores deixaram algum ajuste solto, commitar **só os arquivos tocados**, nominalmente:

```bash
git status
git add game.js game.css server.py tools/editor_city.js tools/test_cenas_conversa.py
git commit -m "test(cenas): ajustes da verificacao ponta a ponta"
```

Se nada mudou, pular o commit. Nunca usar `git add -A`, `git add .` ou `git add -u` — o usuário mantém trabalho em andamento em `server.py` e em `tools/` que não faz parte desta entrega.

---

## Notas para quem implementar

- **Restrição consciente do vínculo implícito (descoberta na Task 2).**
  `_garantir_pontos_implicitos` religa um ponto à cena de mesmo id sempre que o
  ponto não tem vínculo — e ela roda no boot **e** no save do editor. Isso é o
  que faz a taverna migrada abrir sozinha (o ponto `taverna` já existe no
  `city_map_points.json` do usuário, então não bastaria ligar na criação). O
  efeito colateral: um ponto cujo id casa exatamente com o de uma cena **não
  pode ficar sem cena** — escolher "nenhum ponto" para essa cena não gruda.
  Apontar o ponto para OUTRA cena funciona normalmente (o guard respeita
  vínculo existente). Na prática isso só atinge o par `taverna`/`taverna`.
  **Task 11:** o dropdown "Vinculada a" não deve oferecer a opção de desvincular
  quando o id da cena é igual ao id do ponto atualmente vinculado — prometer uma
  ação que não gruda é pior que não oferecê-la.
- **A taverna fica quebrada no meio do caminho, e isso é esperado.** A Task 3 remove `city_state.tavern`, mas o render só passa a ler `city_state.scenes` na Task 10. Entre as duas, abrir a taverna no jogo mostra "não possui frequentadores". Não é regressão — não tentar consertar antes da hora. O primeiro smoke test que vale é o da Task 12.

- **`deepcopy` no payload**: `_cenas_payload` copia antes de filtrar. Sem isso a filtragem apagaria conversas do `CITY_SCENES` global — bug de estado permanente que só apareceria depois da primeira conversa resolvida.
- **`_em_cidade(pid)`, não `phase != "city"`**: `handle_scene_npc` usa o mesmo portão do handler atual, que já cobre o herói que saiu individualmente da masmorra.
- **Ordem de boot é load-bearing**: `_migrar_tavern_scenes()` → `_load_city_scenes()` → normalização dos slots → `_sincronizar_cidades_derivadas()`. Inverter qualquer par quebra a semeadura ou o vínculo implícito.
- **O usuário edita `server.py` em paralelo.** Rodar `git status` antes de cada `git add` e adicionar só os arquivos nominalmente citados na task.
