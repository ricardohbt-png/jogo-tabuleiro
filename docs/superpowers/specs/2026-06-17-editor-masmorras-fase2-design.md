# Editor de Masmorras — Fase 2: Editor Visual (offline)

**Data:** 2026-06-17
**Projeto:** Legends for Hire (RPG de tabuleiro multiplayer)
**Status:** Aprovado — pronto para plano de implementação

---

## Contexto: onde a Fase 2 entra

Segunda das 4 fases do editor de masmorras (ver [[editor-masmorras-fases]] na memória e o
spec da Fase 1 em `docs/superpowers/specs/2026-06-16-editor-masmorras-fase1-design.md`).

- **Fase 1 (concluída, mergeada em master):** o servidor carrega masmorras autoradas de
  `dungeons/*.json` (grid variável), selecionáveis no lobby. Esquema JSON completo já
  definido; `validar_dungeon` / `load_authored_dungeon` no `server.py`.
- **Fase 2 (este spec):** um **editor visual offline** que desenha masmorras e salva o
  JSON no formato da Fase 1, para não ter de escrever JSON à mão.
- Fases 3 (objetivos/prisioneiro/saída em jogo) e 4 (campanha) seguem depois.

O editor autora o **esquema completo** (incl. salas com role/locked/portas, objetivos,
prisioneiro, saída) — mesmo os campos que só ganham vida na Fase 3 — para que as
masmorras já fiquem prontas.

---

## Decisões de arquitetura (aprovadas no brainstorm)

1. **Editor offline, desacoplado:** arquivos em `tools/`, abertos direto no navegador
   (`file://`). Canvas esquemático próprio — **não** reusa `game.js`/Three.js nem exige
   o servidor rodando.
2. **Catálogos por gerador (fonte única):** um script Python extrai os catálogos do
   `server.py` e escreve um `.js` que o editor inclui — sem digitar listas à mão, sem
   drift quando o servidor muda.
3. **Salvar = download / Carregar = upload:** o editor gera o JSON e dispara um download;
   carrega via `<input type=file>`. Nenhuma mudança no `server.py`.
4. **Validação no editor:** réplica em JS das checagens práticas de `validar_dungeon`
   (conveniência, bloqueia salvar se inválida); o servidor continua autoridade final.

---

## Arquivos

| Arquivo | Tipo | Responsabilidade |
|---|---|---|
| `tools/export_catalog.py` | Criar | Gerador: importa `server` e extrai os catálogos → escreve `tools/editor_catalog.js` |
| `tools/editor_catalog.js` | Gerado | `window.EDITOR_CATALOG = {monsters, items, traps, venoms}` |
| `tools/editor.html` | Criar | Shell + layout (barra, grid, painel). Inclui `editor_catalog.js` e `editor.js` via `<script>` |
| `tools/editor.css` | Criar | Estilos do editor (ou `<style>` embutido no HTML, se enxuto) |
| `tools/editor.js` | Criar | Lógica: estado, render do canvas, ferramentas, painel, validação, IO |
| `tools/test_export_catalog.py` | Criar | Teste do gerador (coerência catálogo↔servidor) |

> **Scripts simples, sem ES modules:** `editor.html` carrega `editor_catalog.js` e
> `editor.js` por `<script src>` com globais (`window.EDITOR_CATALOG`, etc.) — `import`
> de ES module é bloqueado em `file://` por vários navegadores. Mesmo padrão do jogo
> (`game.js` + `src/gameState.js` como scripts, não módulos).

---

## 1. Gerador de catálogo (`tools/export_catalog.py`)

Roda da raiz: `python tools/export_catalog.py`. Importa `server` e serializa **apenas os
campos que o editor precisa**, escrevendo `tools/editor_catalog.js`:

```javascript
// GERADO por tools/export_catalog.py — não editar à mão.
window.EDITOR_CATALOG = {
  "monsters": [ {"type":"goblin","name":"Goblin","emoji":"👺"}, ... ],   // de MONSTER_DEFS (com ai_type; + boss)
  "items":    [ {"id":"health_potion","name":"Poção de Vida","emoji":"🧪"}, ... ], // de CHEST_ITEMS
  "traps":    [ {"tipo":"fosso_estacas","nome":"Fosso com Estacas","icone":"⛏️","precisa_veneno":false}, ... ], // de ARMADILHAS
  "venoms":   [ {"id":"veneno_aranha_sombria","name":"Veneno da Aranha Sombria"}, ... ]  // de VENENOS
};
```

- `monsters`: de `MONSTER_DEFS`. Inclui o campo `boss` quando presente (para o editor
  marcar/saber). Espelha o que `load_authored_dungeon` aceita (qualquer `type` em
  `MONSTER_DEFS`).
- `items`: de `CHEST_ITEMS` (catálogo de baú do servidor — o mesmo que
  `_DUNGEON_ITEM_CATALOG` usa na validação).
- `traps`: de `ARMADILHAS`; `precisa_veneno = (tipo == "fosso_envenenado")` ou
  `meta.get("custo_veneno")`.
- `venoms`: de `VENENOS` (para o seletor de veneno do `fosso_envenenado`).

O arquivo é escrito como atribuição JS (não JSON puro) para carregar via `<script>` sem
`fetch` (que `file://` bloqueia). Você roda o gerador **quando os catálogos do servidor
mudarem**; o `editor_catalog.js` gerado é commitado para o editor abrir sem passo extra.

---

## 2. Modelo de dados do editor (`editor.js`)

Estado em memória = exatamente o esquema da Fase 1, em camadas:

- **grid**: `{w, h}` (1..60; editável; redimensionar preserva conteúdo no recorte).
- **tiles**: matriz `h × w` de `0` (WALL) / `1` (FLOOR) / `2` (DOOR).
- **rooms[]**: `{id, x, y, w, h, role, locked, doors:[[x,y],…]}`.
- **entrance**: `{x, y}` | null. **exit**: `{x, y}` | null. **prisoner**: `{pos, room_id}` | null.
- **monsters[]**: `{type, pos, room_id, boss, target}`.
- **chests[]**: `{pos, gold, items:[{id}], key_objective}`.
- **traps[]**: `{tipo, pos, veneno_id?}`.
- **objectives**: `{primary:{type}, secondary:[{type}]}`.
- meta: `{schema_version:1, id, name}`.

Exporta para JSON idêntico ao consumido por `validar_dungeon`/`load_authored_dungeon`;
importa do mesmo formato (edita masmorras existentes, incl. `dungeons/test_fase1.json`).

---

## 3. Render do canvas (esquemático)

Um `<canvas>` (ou grid de divs) desenha o tabuleiro em escala fixa por célula:
- tiles: WALL escuro, FLOOR claro, DOOR em destaque (âmbar);
- salas: contorno do retângulo + rótulo (`role`); salas `locked` com hachura/ícone de
  cadeado;
- entidades: ícone/emoji na casa (entrada=escada, saída=bandeira, monstro=emoji do tipo,
  baú, armadilha=ícone do tipo, prisioneiro);
- seleção: realce da entidade/sala ativa.

Redesenha a cada mutação de estado. Coordenadas do mouse → célula `(x,y)` por divisão
pelo tamanho da célula (como o cliente faz em `game.js`).

---

## 4. Ferramentas (barra)

| Ferramenta | Ação |
|---|---|
| parede / chão / porta | Pinta o tile (clicar e arrastar). |
| sala | Arrasta um retângulo → cria `room` (id incremental); painel define `role`/`locked`. |
| porta | Pinta tile `2` numa borda de sala e **vincula automaticamente** ao `doors[]` da(s) sala(s) cuja borda toca aquela casa. Apagar a porta remove o vínculo. |
| entrada / saída / prisioneiro | Únicos: clicar numa casa de chão define/realoca; clicar de novo realoca. |
| monstro / baú / armadilha | Múltiplos: clicar numa casa de chão adiciona um na casa (com defaults do catálogo). |
| selecionar | Clica entidade/sala → painel de propriedades. |
| apagar | Remove a entidade/porta da casa clicada (ou pinta WALL no modo tile). |

**Vínculo porta↔sala (detalhe):** ao colocar uma porta em `(x,y)`, o editor procura salas
cuja borda (anel externo do retângulo) é adjacente/contém `(x,y)` e adiciona `[x,y]` ao
`doors[]` delas; uma casa de porta pode servir 2 salas (corredor entre duas). Apagar
reverte. Isso reproduz o que a Fase 1 espera (`door_rooms` é montado de `rooms[].doors`).

---

## 5. Painel de propriedades

Mostra os campos do item selecionado, com selects populados pelo `EDITOR_CATALOG`:
- **monstro:** `type` (select), `room_id` (número/auto), `boss` (check), `target` (check).
- **baú:** `gold` (número), `items` (lista; adicionar/remover via select de `items`),
  `key_objective` (check).
- **armadilha:** `tipo` (select); se `fosso_envenenado`, `veneno_id` (select de `venoms`).
- **sala:** `role` (select), `locked` (check); mostra `id` e `doors` (somente leitura).
- **masmorra (sem seleção):** `id`, `name`, `grid w/h`, e os **objetivos**
  (principal: select dos 5 tipos; secundários: lista de selects).

Tipos de objetivo (do esquema): `kill_target`, `kill_all`, `reach_exit`,
`open_key_chest`, `rescue_prisoner`.

---

## 6. Salvar / carregar

- **Salvar:** monta o dict do esquema → roda a validação do editor → se válida, serializa
  com `JSON.stringify(…, null, 2)` e dispara download `Blob` com nome `<id>.json`. Você
  move o arquivo para `dungeons/`. Se inválida, não salva e lista os erros.
- **Carregar:** `<input type=file>` → `FileReader` → `JSON.parse` → repopula o estado
  (tiles, salas, entidades, objetivos). Tolera campos ausentes (defaults). Permite editar
  masmorras existentes.

Nenhuma rota nova no servidor; o ciclo fecha com o seletor de masmorra da Fase 1.

---

## 7. Validação no editor (réplica prática em JS)

`validarEditor(state) -> {ok, erros:[]}` espelha as checagens de `validar_dungeon` que
importam para autoria (não precisa ser bit-a-bit; o servidor é a autoridade ao carregar):

- `grid.w/h` em 1..60; `tiles` com as dimensões certas e valores ∈ {0,1,2};
- `entrance` definida e em FLOOR;
- ≥1 sala e ≥1 sala com `role=="entrance"`;
- cada `monster.pos`/`chest.pos`/`trap.pos`/`prisoner.pos` em FLOOR ou DOOR (não WALL);
- `monster.type` ∈ catálogo; `monster.room_id` existe; `chest.items[].id` ∈ catálogo;
  `trap.tipo` ∈ catálogo; `fosso_envenenado` com `veneno_id` ∈ catálogo;
- cada `[x,y]` em `rooms[].doors` é tile DOOR;
- ≥6 casas de chão alcançáveis a partir da entrada (BFS).

Status ao vivo no painel (verde "válida" / lista de erros). **Salvar fica bloqueado**
enquanto houver erro.

---

## 8. Teste

- **`tools/test_export_catalog.py`** (estilo dos `tools/test_*.py`, com `check()`):
  gera o catálogo em memória e confere que todo `monsters[].type` ∈ `MONSTER_DEFS`,
  `items[].id` ∈ `CHEST_ITEMS`, `traps[].tipo` ∈ `ARMADILHAS`, `venoms[].id` ∈ `VENENOS`;
  que `editor_catalog.js` foi escrito e começa com `window.EDITOR_CATALOG =`.
- **Ida-e-volta:** um JSON de exemplo "salvo" no formato do editor passa em
  `server.validar_dungeon` (reusa `dungeons/test_fase1.json` como referência do formato).
- **Editor (HTML/JS):** verificação manual no navegador — desenhar uma masmorra pequena,
  salvar, colocá-la em `dungeons/`, e carregá-la no jogo pelo seletor da Fase 1 (fecha o
  ciclo). Sem harness JS automatizado (consistente com o projeto).

---

## 9. Fora de escopo (fases seguintes)

Lógica em jogo de objetivos/prisioneiro/saída (Fase 3); ordem de fases, campanha,
progressão (Fase 4); gravar direto em `dungeons/` por endpoint (decidido: download);
pré-visualização com o visual 3D do jogo (canvas esquemático basta).

---

## 10. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| `file://` bloquear `fetch`/ES modules | Catálogo como `<script>` (global), scripts simples, IO por download/upload. |
| Drift entre catálogo do editor e servidor | Gerador é a fonte única; `test_export_catalog.py` cobre coerência; regerar ao mudar o servidor. |
| Vínculo porta↔sala inconsistente | Ferramenta "porta" cuida do `doors[]` automaticamente; validação confere que porta declarada é tile `2`. |
| Validação do editor divergir do servidor | Editor é conveniência; servidor (`validar_dungeon`) é autoridade ao carregar — masmorra inválida é recusada lá também. |
| `editor.js` crescer demais | Manter responsabilidades separadas (estado / render / ferramentas / IO / validação) em funções coesas; se passar do confortável, dividir em `editor_io.js` etc. (scripts simples). |
