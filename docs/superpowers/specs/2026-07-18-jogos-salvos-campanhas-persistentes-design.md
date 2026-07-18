# Jogos Salvos — Campanhas Persistentes por Conta

**Data:** 2026-07-18
**Status:** Aprovado (brainstorming) — pronto para plano de implementação

## Problema

Hoje, a única coisa que persiste entre jogos são as compras da **Guilda**, salvas em
`saves/<class_id>.json` — **por personagem, global ao servidor inteiro**. Isso faz as
habilidades da Guilda "vazarem" para qualquer jogo novo: o mago (Pedro) sempre carrega
as mesmas compras, em qualquer sala. Ouro, HP, nível, itens da bolsa, equipamento e
tesouros **não** persistem — são recriados do zero pelo `make_player` a cada jogo.

O objetivo é o modelo de **"jogo salvo" (instância de campanha)**:

1. O host cria um **jogo novo** para um grupo jogar uma campanha do começo ao fim.
2. Durante esse jogo, **tudo** do personagem (itens, habilidades, HP, ouro, tesouros,
   nível) é guardado **naquele jogo**.
3. O jogo pode ser **fechado e continuado depois**.
4. Se o **mesmo personagem** começar um **jogo diferente**, ele começa **do zero** —
   sem acesso às conquistas do outro jogo.

Ou seja: a persistência deixa de ser "global por personagem" e passa a ser
**"por jogo salvo × personagem"**. Esta é uma implantação central e não pode deixar
buracos de consistência.

## Decisões de design (do brainstorming)

| Tema | Decisão |
|---|---|
| Identidade do save | **Conta de usuário / login** (apelido + PIN simples) |
| Peso do login | **Nome + PIN** (PBKDF2+salt; sem senha "de verdade", sem OAuth) |
| Conta × personagem | **Fixo por jogo salvo** — cada jogador segue seu personagem até o fim daquela campanha |
| Presença parcial | **Ausentes ficam de fora** na sessão; progresso preservado; volta quando o dono aparecer |
| Ponto de save | **Pontos seguros** (cidade / ao concluir cada fase). Sair no meio da masmorra = refaz aquela masmorra |
| Papel do Mestre | **Membro fixo do jogo salvo** — a conta é "o Mestre daquela campanha"; sem ficha/progresso |
| Formato em disco | **1 arquivo JSON por jogo salvo** (`savegames/<id>.json`), gravação atômica `.tmp`+`replace` + 1 `.bak` |

### Suposições assumidas

- **Tudo mora no host.** O servidor roda no PC do host; amigos entram pelo túnel. Contas
  e jogos salvos são arquivos JSON no host. Sem nuvem.
- **Fluxo de retomar:** host abre "Continuar jogo" → escolhe o save → abre lobby → cada
  amigo conecta, loga (apelido+PIN) e, se a conta é membro, o personagem carrega
  automaticamente com o progresso. O **código de sala** continua existindo, mas só como
  endereço da sessão ao vivo; a identidade durável é **conta + jogo salvo**.
- **Compras da Guilda passam a ser por-jogo.** O `saves/<class_id>.json` global sai de
  cena; num jogo novo o personagem começa **sem** compras da Guilda. Os saves globais
  atuais são **ignorados** (importação única fica fora do escopo v1).
- **O mesmo personagem** pode existir em vários jogos salvos diferentes, independentes.

## Modelo de dados

### `accounts/<apelido>.json`

Uma conta por jogador. O apelido normalizado (minúsculas, sem espaços nas bordas) é a
chave/nome do arquivo.

```json
{
  "username": "ricardo",
  "pin_hash": "pbkdf2_sha256$<iter>$<salt_b64>$<hash_b64>",
  "created": "2026-07-18T14:00:00Z"
}
```

- PIN nunca em texto puro. Hash via `hashlib.pbkdf2_hmac` com salt por conta.
- Carregar/criar/verificar espelham o padrão tolerante do `load_guild_save`
  (ausente/corrompido → tratado sem crash).

### `savegames/<id>.json`

Um jogo salvo. `id` é um token curto único (ex.: `sg_ab12cd`).

```json
{
  "id": "sg_ab12cd",
  "name": "Campanha da Guilda",
  "owner": "ricardo",
  "created": "2026-07-18T14:00:00Z",
  "updated": "2026-07-18T15:30:00Z",
  "mode": "campaign",
  "campaign_file": "resgate_de_elara.json",
  "campaign_phase": 2,
  "has_master": true,
  "master_account": "ricardo",
  "members": {
    "joao":  { "class_id": "warrior" },
    "maria": { "class_id": "mage" }
  },
  "characters": {
    "warrior": { "...ficha durável..." },
    "mage":    { "...ficha durável..." }
  }
}
```

- `campaign_phase` é o progresso **do grupo** (em que fase da campanha estão).
- `members` é o vínculo **conta → personagem** (uma classe por conta, uma conta por classe).
- `characters` é indexado por `class_id` (só um de cada classe por jogo).
- `mode: "procedural"` → `campaign_file: null` e a fase não se aplica (jogo avulso ainda
  pode ser salvo/retomado com as fichas, mas sem progressão de campanha).

### Ficha durável (`snapshot_character` / `restore_character`)

`snapshot_character(player) -> dict` extrai **apenas** os campos duráveis:

- `gold`, `hp` (atual), `max_hp`, `level`, `xp`
- `bag` (bolsa), `gear` (8 slots de equipamento)
- `guild_owned` (especializacoes/tecnicas), `guild_equip`
- `magias_conhecidas`
- venenos na arma (`poison_slots` da arma equipada)
- instrumento no `off_hand` (já vive dentro de `gear`, então coberto por `gear`)

`restore_character(player, snap)` sobrepõe esses campos num `make_player` fresco e
re-aplica os efeitos derivados de equipamento (`_apply_gear_effect`) e a cópia de
combate da arma (`p["weapon"]`), como o `_rescue_equip`/`apply_guild_save` já fazem hoje.

**Não** entram no snapshot (resetam por sessão): recargas de técnica
(`technique_cooldowns`), buffs temporários, `facing`/posição, iniciativa, fome/sede
runtime, flags de turno.

## Ciclo de vida

### Login (todos, ao conectar)

1. Cliente mostra tela **apelido + PIN**.
2. `login {username, pin}`: se a conta existe, confere o PIN; senão, erro pedindo criar.
   `create_account {username, pin}`: cria se o apelido estiver livre.
3. Ao autenticar, a conexão é atada à conta (`self.account_by_pid[pid] = username`).
4. Uma conta só pode estar autenticada em **uma** sessão ao vivo por vez (recusa a 2ª).

### Criar jogo (host)

1. Home → "Novo jogo" → nome + campanha (ou procedural) + "tem Mestre?".
2. `create_savegame {name, mode, campaign_file, has_master}`: grava
   `savegames/<id>.json` vazio (`members`/`characters` vazios, `campaign_phase: 0`,
   `owner` = conta do host).
3. Abre o lobby ligado a esse save (`room.savegame_id = id`).

### Escolher personagem no lobby

- **1ª vez** (conta ainda não em `members`): escolhe uma classe livre → grava o vínculo
  em `members` e cria a ficha fresca (`make_player`) em `characters`.
- **Retomando** (conta já em `members`): a classe é **auto-atribuída** e a ficha é
  carregada de `characters`.
- Recusa: pegar uma classe que já é de **outra** conta naquele jogo
  ("personagem de outro jogador").
- Mestre: se `has_master`, a `master_account` assume o papel; se ele for o host que
  criou o save, já entra como mestre.

### Iniciar / Retomar sessão

1. `start_game`: para cada **membro presente**, `make_player` cria a base e
   `restore_character` sobrepõe a ficha salva de `characters[class_id]`. Membros ausentes
   são **pulados** (ficha permanece intacta no arquivo).
2. `campaign_phase` vem do save (a campanha entra na fase correta).
3. Mestre: a `master_account` presente vira `master_pid`.

### Pontos de save (gravação)

Gatilhos: (a) ao entrar na **cidade** (`broadcast_city_state` / `_voltar_para_cidade`),
(b) ao **concluir cada fase** da campanha.

Em cada gatilho, `write_savegame` grava, de forma atômica:

- Para cada personagem **presente**: `characters[class_id] = snapshot_character(player)`.
- `campaign_phase` atualizado.
- `updated` = agora.

Fichas de membros ausentes **não** são tocadas. Se o grupo sair no meio de uma masmorra,
perdem no máximo o progresso daquela masmorra (voltam à última cidade/fase salva).

## Mudanças no servidor (`server.py`)

- **Camada de contas** (novo bloco perto de `GUILD_SAVE_DIR`): `ACCOUNTS_DIR`,
  `account_path`, `hash_pin`, `verify_pin`, `load_account`, `create_account`.
- **Camada de savegames** (novo bloco): `SAVEGAMES_DIR`, `savegame_path`, `list_savegames`
  (filtra por conta dona/membro), `load_savegame` (valida + fallback `.bak`),
  `write_savegame` (atômico `.tmp`+`replace`, rotaciona `.bak`), `delete_savegame`.
- **`snapshot_character` / `restore_character`** (substituem `apply_guild_save`; os
  `write_guild_save` espalhados viram parte do `write_savegame` nos checkpoints).
- **`GameRoom`** ganha: `savegame_id`, `savegame` (dict carregado), `account_by_pid`.
- **Mensagens WS novas** (client→server): `login`, `create_account`, `list_savegames`,
  `create_savegame`, `load_savegame`, `delete_savegame`. Respostas: `login_result`,
  `savegames_list`, e reuso de `lobby_state`/`error`.
- **Travas:** um `savegame_id` só roda em **uma** sessão ao vivo por vez (novo lock,
  `SAVEGAMES_IN_USE = {id: room_code}`, no lugar do `CHARACTERS_IN_USE` global). Dentro da
  sala, uma classe cada (mantém). A mesma classe **pode** existir em savegames diferentes.
  Uma conta só em uma sessão por vez.

## Mudanças no cliente (`game.js` / `src/gameState.js`)

- **Tela de login** (apelido+PIN) na abertura, antes do menu.
- **Home:** "Novo jogo" vs "Continuar jogo" (lista `list_savegames` da conta).
- **Novo jogo:** formulário nome + campanha + toggle Mestre.
- **Lobby:** mostra qual conta é qual personagem; ao retomar, faz o auto-vínculo e
  desabilita a troca de classe de membros já vinculados.
- `src/gameState.js`: senders `login`/`createAccount`/`createSavegame`/`loadSavegame`/
  `listSavegames`/`deleteSavegame`; estado de conta logada; getters da lista de saves.

## Robustez / casos de borda

- Escrita atômica (`.tmp` + `os.replace`) + 1 backup `.bak`. Ao carregar: valida a forma;
  se corrompido, cai no `.bak`; se ambos falham, erro claro, **nunca crasha** (mesmo
  espírito do `load_guild_save`).
- PIN errado → erro, não conecta. Conta já logada ao vivo em outro lugar → recusa.
- Savegame já aberto em outra sessão → recusa carregar (lock).
- Pegar classe de outra conta no mesmo save → recusa.
- Saves globais antigos (`saves/<class_id>.json`) → ignorados no modelo novo.
- `savegames/` e `accounts/` entram no `.gitignore` (como `saves/` já está).

## Testes

`tools/test_savegames.py` (servidor, sem cliente):

- Conta: criar, verificar PIN certo/errado, apelido duplicado, arquivo corrompido.
- Savegame: criar, listar (por dono/membro), carregar, deletar, gravação atômica.
- Vínculo: 1ª escolha grava `members`; retomar auto-atribui; recusa classe de outra conta.
- `snapshot_character`/`restore_character`: ida-e-volta preserva ouro/HP/nível/bolsa/
  gear/guilda/magias/veneno; campos runtime não vazam.
- Checkpoint: entrar na cidade grava as fichas dos presentes e não toca nos ausentes.
- Retomar: sobreposição carrega a ficha certa e a fase certa da campanha.
- Travas: savegame em uso recusa 2ª sessão; conta em uso recusa 2º login.
- Fallback: arquivo `.json` corrompido carrega do `.bak`.

## Fases de implementação (mesmo spec)

1. **Fase 1 — Contas + camada de savegames + CRUD.** `accounts/`, `savegames/`, hash de
   PIN, `login`/`create_account`, `create_savegame`/`list`/`load`/`delete`, travas.
   Sem overlay de gameplay ainda. Testável isolada.
2. **Fase 2 — Snapshot/restore + checkpoints + retomar.** `snapshot_character`/
   `restore_character`, gravação nos pontos seguros, `restore` no `start_game`,
   vínculo conta↔personagem no lobby, presença parcial.
3. **Fase 3 — UI do cliente.** Login, Novo/Continuar jogo, lobby com auto-vínculo.

## Fora de escopo (v1)

- Snapshot tático mid-masmorra (posições/HP de monstros/iniciativa).
- Importação dos saves globais antigos para um jogo salvo.
- Senhas fortes / OAuth / contas na nuvem.
- Um jogador assumir o personagem de um ausente.
