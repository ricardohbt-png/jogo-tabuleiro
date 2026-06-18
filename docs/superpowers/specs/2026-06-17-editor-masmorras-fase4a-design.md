# Editor de Masmorras — Fase 4a: Runtime de Campanha

**Data:** 2026-06-17
**Projeto:** Legends for Hire (RPG de tabuleiro multiplayer)
**Status:** Aprovado — pronto para plano de implementação

---

## Contexto

Quarta fase do editor de masmorras (ver [[editor-masmorras-fases]] e os specs das Fases
1–3). A Fase 4 original juntava **runtime de campanha** + **aba de campanha no editor**.
Foi dividida: esta é a **Fase 4a (runtime)**; a **Fase 4b (aba no editor)** é um ciclo
separado depois. Por ora o `campaign.json` é escrito à mão.

Uma **campanha** é uma sequência ordenada de masmorras autoradas (Fase 1). Concluir o
objetivo (Fase 3) de uma fase leva à **cidade/loja** e depois à **próxima fase**;
concluir a última = **vitória da campanha**.

### Decisões de produto (aprovadas no brainstorm)

- **4a agora, 4b depois** (campaign.json à mão por enquanto).
- **HP carrega entre fases**; heróis curam/reequipam na cidade (templo/loja) gastando ouro.
- **Cidade/loja entre as fases**: concluir a fase N → cidade → anfitrião entra na fase N+1.
- **Wipe → derrota** encerra a campanha (`end_game(defeat)`, como hoje).
- Procedural e masmorra única (Fase 1) continuam funcionando inalterados.

---

## Arquitetura atual relevante (verificada)

- Laço cidade↔masmorra já existe e **persiste os heróis**: `start_game` monta os players
  (`make_player`) e vai para `phase="city"` (`server.py:3036`); `handle_exit_dungeon`
  (escada) volta para `phase="city"` (`server.py:6013`); `enter_dungeon`
  (`server.py:3453`) só **gera/carrega** na 1ª entrada (`dungeon_generated`) e **retoma**
  nas voltas. HP/XP/ouro/itens ficam no dict do jogador e não são resetados ao reentrar.
- Modo autorado (Fase 1): `self.mode`/`self.selected_dungeon`/`self.dungeon_def`;
  `handle_select_dungeon` carrega+valida o `defn`; `enter_dungeon` ramifica
  `autorada = self.mode == "authored" and self.dungeon_def is not None` e chama
  `load_authored_dungeon`.
- Conclusão por objetivo (Fase 3): `_check_objectives` (hook em `push_state`) avalia o
  objetivo principal e, quando cumprido, concede bônus dos secundários e chama
  `end_game(victory=True)`. Guardas: `self.objectives`, `phase=="playing"`,
  `self._objetivo_concluido`.
- Helpers de arquivo: `listar_dungeons()`, `carregar_dungeon(file)`,
  `validar_dungeon(defn)` (`server.py`); `DUNGEONS_DIR`.
- `lobby_state` (`broadcast_lobby`) traz `dungeons`/`mode`/`selected_dungeon`; cliente:
  `GS.lobbyDungeons`/`GS.selectDungeon` (Fase 1).

---

## 1. Formato `campaigns/*.json`

Nova pasta `campaigns/` na raiz (lida pelo `server.py`, como `dungeons/`).

```jsonc
{
  "schema_version": 1,
  "id": "campanha_cripta",
  "name": "A Cripta dos Sussurros",
  "dungeons": ["test_fase1.json", "test_fase3.json"]   // arquivos em dungeons/, em ordem
}
```

Helpers (espelham os de dungeon, no `server.py`):
- `CAMPAIGNS_DIR = .../campaigns`.
- `carregar_campanha(file)` — lê+parseia (proteção a path traversal como `carregar_dungeon`).
- `validar_campanha(defn) -> (ok, msg)` — `schema_version==1`; `dungeons` lista não vazia;
  cada arquivo existe em `dungeons/` (`carregar_dungeon` != None) e passa em
  `validar_dungeon`. Mensagem aponta a fase problemática.
- `listar_campanhas() -> [{id, name, file}]` — varre `campaigns/*.json` e devolve as válidas.

---

## 2. Seleção no lobby

- `lobby_state` ganha `campaigns: [{id, name, file}]` (de `listar_campanhas()`).
- Nova mensagem **`select_campaign`** `{file|null}` (só host):
  - `file` válido → `self.mode = "campaign"`, `self.campaign = defn` (dict carregado),
    `self.campaign_phase = 0`, `self.selected_dungeon = None`; reemite `lobby_state`.
  - inválido → `error` ao host, sem mudar estado.
  - `null` → volta para procedural (`self.mode="procedural"`, limpa campaign).
- `select_dungeon` (Fase 1) continua; escolher uma masmorra avulsa limpa `self.campaign`
  (`self.mode="authored"`). Escolher "Procedural" limpa ambos.
- `lobby_state` reporta `mode` (`procedural`/`authored`/`campaign`) e o nome selecionado.

---

## 3. Estado da sala + entrada da fase

- `GameRoom.__init__` (defaults): `self.campaign = None`, `self.campaign_phase = 0`.
  (`self.mode` já existe; passa a aceitar `"campaign"`.)
- `enter_dungeon`, no início do bloco `nova` (1ª entrada de cada fase): se
  `self.mode == "campaign"`, define
  `self.dungeon_def = carregar_dungeon(self.campaign["dungeons"][self.campaign_phase])`
  **antes** do cálculo de `autorada` (ou recomputa `autorada` para incluir campanha).
  Resultado: `autorada` é verdadeiro e o carregamento segue o caminho autorado da Fase 1
  (`load_authored_dungeon`).
- `autorada` passa a ser:
  `autorada = self.mode in ("authored", "campaign") and self.dungeon_def is not None`.
- Resets por-masmorra (névoa, monstros, baús, corrosão, vinho) ocorrem como hoje no bloco
  `nova`. **HP/XP/nível/ouro/itens NÃO são resetados** (já é o comportamento — confirmar).

---

## 4. Avanço de fase (em `_check_objectives`)

Hoje, principal cumprido → `end_game(victory=True)`. No modo campanha, ramificar:

```text
quando o principal está cumprido (e não concluído ainda):
    self._objetivo_concluido = True
    conceder bônus dos secundários cumpridos        # como na Fase 3
    se mode == "campaign" e campaign_phase < len(dungeons) - 1:
        self.campaign_phase += 1
        self.dungeon_generated = False              # próxima entrada carrega a nova fase
        self._objetivo_concluido = False            # a nova fase tem seus próprios objetivos
        narrar "Fase N concluída! Retornem à cidade."
        ir para a CIDADE: phase="city"; _gerar_loja_pergaminhos(); reset de turno dos
            jogadores (moves/action) como handle_exit_dungeon; broadcast_city_state()
    senão:
        await self.end_game(victory=True)            # última fase (ou modo não-campanha)
```

- "Ir para a cidade" reaproveita o que `handle_exit_dungeon` já faz (phase=city, renovar
  loja, resetar moves/action dos jogadores) — extrair um helper `_voltar_para_cidade()`
  para reuso e evitar duplicação.
- Não concluir a fase (resgate falhou / sair pela escada) → cidade **sem** avançar
  (`campaign_phase` intacto, `dungeon_generated` segue True): reentrar **retoma a mesma
  fase**.
- Wipe → `end_game(defeat)` (caminho atual, inalterado).

---

## 5. Serialização + cliente

`push_state`/`city_state` ganham um bloco de progresso de campanha (presente só no modo
campanha; `null` caso contrário):

- `campaign`: `{name, phase, total}` (`phase` = `campaign_phase + 1`, `total` =
  `len(dungeons)`), ou `null`.

Cliente:
- `gameState.js`: getter `campaign()`; sender `selectCampaign(file)`; getter
  `lobbyCampaigns()`.
- `game.js`:
  - dropdown do lobby ganha o grupo **Campanhas** (além de Procedural e masmorras),
    chamando `GS.selectCampaign`;
  - **indicador de progresso** "Fase N de M — *nome*" no HUD (perto do HUD de objetivos)
    e/ou na cidade;
  - na cidade, quando há próxima fase, o botão de entrar exibe **"Entrar na próxima fase:
    *nome*"** (o nome da próxima masmorra, se disponível; senão genérico).
- Regra estado-vs-render do CLAUDE.md respeitada.

---

## 6. Protocolo (resumo das mudanças)

**Client → Server**

| Mensagem | Campos | Nota |
|---|---|---|
| `select_campaign` | `file` (string ou `null`) | Só host. `null` = procedural. |

**Server → Client**

`lobby_state` ganha `campaigns`. `game_state` e `city_state` ganham `campaign`
(`{name,phase,total}` ou `null`).

---

## 7. Teste

Headless de `GameRoom` (estilo `tools/test_*.py`, stub de rede):
- Criar `campaigns/test_campanha.json` referenciando 2 masmorras pequenas e válidas de
  `dungeons/` (ex.: uma `kill_all` rápida e a `test_fase3.json`).
- **Seleção:** `select_campaign` → `mode=="campaign"`, `campaign_phase==0`. Inválida →
  erro, sem mudar estado.
- **Avanço:** entrar fase 0 → cumprir o objetivo → vai para `phase=="city"`,
  `campaign_phase==1`, `dungeon_generated False`, **HP/ouro do grupo preservados**.
- **Carga da próxima fase:** reentrar → carrega a fase 1 (grid/monstros da 2ª masmorra).
- **Vitória final:** cumprir o objetivo da última fase → `end_game(victory=True)` chamado.
- **Retomar mesma fase:** sair pela escada sem concluir → cidade sem avançar; reentrar
  retoma a mesma fase.
- **Validação:** `validar_campanha` recusa lista vazia / arquivo inexistente / fase inválida.
- **Regressão:** procedural (boss-kill → vitória) e masmorra única (Fase 1/3) intactos.

---

## 8. Fora de escopo

- **Fase 4b:** aba de campanha no editor (montar/ordenar campanhas visualmente).
- Salvar/retomar progresso de campanha entre sessões/servidor (o estado vive na sala em
  memória, como o resto do jogo).
- Ramificações/escolhas de fase (campanha é uma sequência linear).

---

## 9. Riscos e mitigações

| Risco | Mitigação |
|---|---|
| `_check_objectives` ramificar errado e encerrar quando deveria avançar | Branch explícito por `mode=="campaign"` e índice; teste de avanço vs. vitória final. |
| Duplicar a lógica de "voltar à cidade" | Extrair `_voltar_para_cidade()` reaproveitado por `handle_exit_dungeon` e pelo avanço. |
| `autorada` não incluir campanha → cair no procedural | `autorada = mode in ("authored","campaign") and dungeon_def is not None`; teste de carga da fase. |
| Campanha referenciando masmorra inválida | `validar_campanha` valida cada fase via `validar_dungeon`; recusa no `select_campaign`. |
| Reset indevido de HP/itens ao avançar | Avanço só mexe em `campaign_phase`/`dungeon_generated`/cidade; resets por-masmorra do `enter_dungeon` não tocam HP/XP/ouro/itens (confirmado). Teste de preservação. |
| Campos novos quebrarem clientes antigos | `campaign`/`campaigns` sempre presentes com `null`/vazio; cliente trata ausência. |
