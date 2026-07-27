# Editor de Cidades — criar, editar e excluir cidades

**Data:** 2026-07-28
**Status:** aprovado (brainstorming)

## Problema

As cidades do jogo são fixas em código: `WORLD_LOCATIONS` (server.py) declara as 4
originais (`alva_e_luz`, `vila_riacho`, `vila_corvin`, `graciero`) com `id`, `nome`,
`tipo`, `imagem`, `x`, `y`. Todo o resto do conteúdo de cidade já é editável e
persistido por `city_id` — lojas (`city_shops.json`), pontos do mapa da cidade
(`city_map_points.json`), taverna (`tavern_scenes.json`) e as posições no mapa-múndi
(`world_map_points.json`) — mas o **conjunto de cidades** não. Criar uma cidade nova
exige editar `server.py` na mão.

Objetivo: pela aba "Cidades" do editor de masmorras, criar uma cidade nova (com upload
da ilustração de fundo e posição no mapa-múndi), editar as existentes e excluí-las.

## Decisões tomadas no brainstorming

1. **Rotas de viagem** viram dados editáveis no editor (tabela por par de cidades),
   não código.
2. O formulário **cria novas e edita as existentes** (nome, tipo, imagem).
3. A cidade nova nasce **vazia** — sem lojas, sem pontos no mapa da cidade, sem cena
   de taverna. O conteúdo é adicionado aos poucos pelas abas que já existem.
4. **Rota sem custo definido = viagem grátis.** Toda cidade alcança todas; o custo
   em branco/zero significa 🍖-0/💧-0, não "rota inexistente".
5. **Qualquer cidade pode ser excluída, exceto Alva e Luz** (cidade inicial e destino
   de fallback dos saves).

## Arquitetura

### 1. Persistência — `cidades_personalizadas.json`

Arquivo novo na raiz, seguindo o padrão de `monstros_personalizados.json` e
`itens_personalizados.json`. As 4 originais continuam declaradas em `server.py` (base);
este arquivo é uma **camada por cima** que adiciona, edita e remove.

```json
{
  "cities": [
    {"id": "porto_negro", "nome": "Porto Negro", "tipo": "cidade",
     "imagem": "assets/city/porto_negro.png", "x": 60.1, "y": 44.0}
  ],
  "overrides": {
    "graciero": {"nome": "Graciero Velho", "tipo": "vila", "imagem": "assets/city/novo.png"}
  },
  "deleted": ["vila_corvin"],
  "routes": [
    {"from": "porto_negro", "to": "alva_e_luz", "fome": 8, "sede": 8}
  ]
}
```

- `cities` — cidades criadas pelo usuário (registro completo, mesmo formato de
  `WORLD_LOCATIONS`). `servicos` recebe `True` por padrão (o campo hoje é inerte:
  nenhum consumidor no servidor ou no cliente).
- `overrides` — edições nas cidades **originais**. Só `nome`, `tipo` e `imagem`;
  `x`/`y` continuam em `world_map_points.json`, que já é o dono dessas coordenadas.
  Editar uma cidade **criada pelo usuário** não gera override: atualiza o próprio
  registro em `cities`.
- `deleted` — ids de cidades originais removidas. `alva_e_luz` é ignorado se aparecer.
- `routes` — custos de viagem por par (não-direcionado; `from`/`to` são
  intercambiáveis). Substitui/complementa `WORLD_ROUTES`.

**Ordem de boot (crítica).** O merge roda logo depois da declaração de
`WORLD_LOCATIONS`/`WORLD_ROUTES` e **antes** de:

- `_load_world_map_points()` — só aceita ids presentes em `WORLD_LOCATIONS`;
- o loop `for _tavern_city_id in WORLD_LOCATIONS` que popula `TAVERN_SCENES`;
- a declaração/carga de `CITY_MAP_POINTS`;
- `_default_city_shops()` / `_load_city_shops()`.

É essa ordem que faz a cidade nova ser reconhecida por lojas, taverna e mapa da cidade
sem alterar nenhum desses subsistemas.

Estrutura das funções (espelhando os outros carregadores do arquivo):
`WORLD_CITIES_FILE`, `_load_world_cities()` (merge no boot), `_save_world_cities()`
(gravação atômica via `.tmp` + `os.replace`), `_world_cities_editor_payload()`,
`_save_world_cities_upload(cities, overrides, deleted, routes)`.

### 2. Rotas — mudança de regra

`WORLD_ROUTES` deixa de ser "a lista de rotas que existem" e passa a ser apenas "a
tabela de custos". Par sem entrada = 🍖0/💧0.

- `handle_world_travel` (server.py:7769) não recusa mais por rota ausente; usa
  `{"fome": 0, "sede": 0}` como padrão. A checagem de recursos insuficientes continua.
- `broadcast_city_state` passa a emitir uma entrada em `world.routes` para **todos** os
  pares de cidades (custo salvo ou 0).

Com isso o cliente (`game.js`) **não muda**: `_worldRouteCost` sempre acha a rota, o
marcador nunca recebe a classe `locked` e `showWorldLocationPreview` mostra o botão de
viajar com "🍖 -0 e 💧 -0".

### 3. Exclusão

`handle` de exclusão remove a cidade de `WORLD_LOCATIONS` e faz a limpeza:
`CITY_SHOPS`, `CITY_MAP_POINTS`, `TAVERN_SCENES` e toda rota que a envolva
(`WORLD_ROUTES` + entradas de `routes` no arquivo). Se era uma das 4 originais, o id
entra em `deleted`.

`alva_e_luz` nunca é excluível (validado no servidor, além de escondido na UI).

Salas ativas: o carregador de save já cai em `alva_e_luz` quando a cidade gravada não
existe (`server.py:1042`). Acrescentar o mesmo tratamento para salas **ao vivo** —
ao excluir, qualquer sala com `world_location` igual à cidade apagada passa a
`alva_e_luz` e recebe `city_state` novo.

### 4. Cidade nova vazia — dois ajustes necessários

1. **Taverna.** O loop que copia a cena de Alva e Luz para toda cidade de
   `WORLD_LOCATIONS` passa a valer só para as 4 originais (`_BUILTIN_CITY_IDS`).
   A cidade nova recebe uma cena vazia (`{"background": "", "mode": "individual",
   "slots": []}`), para que o editor de taverna tenha onde gravar.
2. **Editor de taverna.** `renderTavern` (`tools/editor_city.js`) só desenha o upload
   de fundo e o botão "+ Adicionar NPC" quando já existe pelo menos 1 slot; com cena
   vazia mostra "esta cidade ainda não possui uma cena de taverna configurada" e nada
   mais. Passa a desenhar os controles também no caso vazio — sem isso a cidade nova
   nunca ganha taverna.

Os demais subsistemas já lidam com o vazio: a aba Lojas tem checkbox por
estabelecimento (`data-toggle-store`) e a aba Mapa da cidade tem "+ Adicionar ponto".

### 5. Upload da ilustração

Nova mensagem WS `upload_city_art`, espelhando `upload_tavern_art`:
`_save_city_art_upload(name, data_b64)` grava em `assets/city/` e retorna
`"assets/city/<arquivo>"`. Mesmas proteções do original: extensão em `_STORY_IMG_EXT`,
teto `STORY_UPLOAD_MAX`, `os.path.basename` + sanitização do nome (path traversal).

A mesma imagem serve aos dois usos que já existem: fundo da tela da cidade
(`loc.imagem` em `showWorldLocationPreview`) e fundo do editor do mapa da cidade
(`c.imagem` em `renderCityMap`).

### 6. UI — aba "Cidades" (`tools/editor_city.js`)

Na faixa de botões de cidade (`.cityed-cities`), dois botões novos: **"+ Nova cidade"**
e **"✏️ Editar cidade"** (este último age sobre a cidade selecionada). Ambos abrem o
mesmo painel, em modo criação ou edição:

- **Nome** (texto) e **Tipo** (select: cidade / vila). O `id` é gerado do nome por
  slug (`[a-z0-9_]`, acentos removidos); colisão recebe sufixo numérico. Em edição o
  `id` é imutável.
- **Imagem de fundo**: `<input type="file">` + botão "Enviar imagem" → `upload_city_art`.
  Mostra prévia da imagem atual.
- **Posição no mapa-múndi**: campos X% e Y% (padrão 50/50). O ajuste fino continua
  sendo o arraste na aba "Mapa do Mundo", onde a cidade nova aparece automaticamente
  (é lida de `config.locations`).
- **Rotas**: uma linha por cidade existente com campos 🍖/💧 (vazio ou 0 = grátis).
- **Salvar cidade** e **Excluir cidade** (escondido para `alva_e_luz`).

Salvamento por nova mensagem WS `save_world_cities` (payload: `cities`, `overrides`,
`deleted`, `routes`). O carregamento vem de graça: `_city_shops_editor_payload()` já
devolve `cities`; passa a devolver também `routes`. Após salvar, o servidor reemite
`city_state` para as salas em fase de cidade — `_refresh_city_states_after_editor_save`
já existe e é reusado.

## Fora de escopo

- Editar `x`/`y` das cidades originais pelo painel (continua sendo o arraste no
  mapa-múndi, como hoje).
- Trocar a imagem do mapa-múndi em si (`assets/city/varluzia - Copia.png`, hardcoded).
- Rotas direcionais (ida ≠ volta) e rotas com pré-requisito.
- Migrar as 4 cidades originais para o arquivo de dados.

## Testes — `tools/test_cidades_editor.py`

1. **Criar**: cidade nova entra em `WORLD_LOCATIONS`; nasce com `CITY_SHOPS[id] == {}`,
   `CITY_MAP_POINTS[id] == {}` e cena de taverna vazia (sem os NPCs de Alva e Luz).
2. **Editar original**: `nome`/`tipo`/`imagem` de `graciero` persistem em `overrides` e
   sobrevivem a um reload; as rotas antigas ficam intactas.
3. **Excluir**: some de `WORLD_LOCATIONS`, `CITY_SHOPS`, `CITY_MAP_POINTS`,
   `TAVERN_SCENES` e das rotas; sala com `world_location` na cidade apagada vai para
   `alva_e_luz`; excluir `alva_e_luz` é recusado.
4. **Rotas**: par sem custo permite viajar gastando 0/0; par com custo debita o valor;
   `broadcast_city_state` emite rota para todos os pares.
5. **Validação**: id/nome vazio, nome longo demais, `x`/`y` fora de 0–100, id duplicado
   e tipo inválido são recusados sem corromper o estado.
6. **Upload**: extensão não permitida e arquivo acima do teto são recusados; sucesso
   grava em `assets/city/` e devolve o caminho relativo.
