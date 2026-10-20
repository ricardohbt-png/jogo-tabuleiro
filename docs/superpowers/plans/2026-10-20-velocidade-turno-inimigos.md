# Velocidade do turno dos inimigos — plano de implementação

> **Para quem executar:** use superpowers:executing-plans (execução inline) ou
> superpowers:subagent-driven-development. Os passos usam caixas `- [ ]`.

**Objetivo:** o jogador escolhe a velocidade do turno dos inimigos; cada monstro
em combate que atacou mostra uma faixa de resumo no alto da tela, com anel
vermelho no monstro agindo.

**Arquitetura:** o servidor (autoritativo) segura a fila de iniciativa entre um
monstro e o próximo, coleta os ataques do monstro via `_emitir_feedback_ataque`
e manda `resumo_ataque_inimigo`; o cliente só renderiza e envia a escolha/o
clique. Nível "atual" não executa nada novo (byte-idêntico).

**Stack:** Python/websockets (`server.py`), JS vanilla (`src/gameState.js`,
`game.js`), dicionário PT/EN em `src/lang/interface.js`.

**Spec:** `docs/superpowers/specs/2026-10-20-velocidade-turno-inimigos-design.md`

## Restrições globais

- `game.js`, `server.py` e `CLAUDE.md` estão em **CRLF**: edite com a ferramenta
  Edit, nunca com `replace` multilinha de script.
- `GS.on` mantém um callback por evento: **não** crie um segundo `GS.on` do mesmo
  evento; estenda o existente.
- Estado primeiro, visual depois: `gameState.js` não referencia DOM/THREE.
- Nada de texto em português cru no cliente/servidor novos: `t('ui.turno_inimigo.*')`
  e `T("...")` com PT e EN. Sem `t` local sombreando o tradutor.
- Nível `atual` = comportamento atual, provado por teste.
- Valores: níveis `atual | lento | muito_lento | passo`; tempos Lento 3 s, Muito
  lento 6 s (constantes `RITMO_SEGUNDOS`); auto do passo: 0/3/6/10 s; teto de
  espera por clique **90 s** (`RITMO_TETO_CLIQUE_S`).
- Não commitar o WIP de outra sessão (Bomba de Flash) presente no checkout:
  commite só os arquivos/trechos desta feature.

## Revisão de foco (Review Focus)

- Monstro que morre durante o próprio turno antes da faixa → faixa ainda sai com o
  que fez, sem quebrar. (Task 3)
- Ataque que mata o último herói e encerra a partida → sem espera. (Task 3)
- Desconexão do jogador no Solo durante a espera → espera termina. (Task 3)
- Falha dentro da espera não congela a iniciativa. (Task 3)
- Monstro em combate fora da visão → faixa genérica, sem nome/habilidade. (Task 3)
- Reabrir o jogo salvo: a escolha persiste, a espera não. (Task 1)

## Rulings já tomados (revisar se discordar)

- O resultado de ataque (`attack_feedback`) não traz o dano. O dano da faixa é a
  **perda de PV do alvo** medida entre o `start` do ataque e o `start` seguinte
  (ou o fim do turno do monstro). Reduções do Protetor ou cura no meio podem
  deslocar o número; aceito para a v1.
- O "tipo" no resumo usa `impacto` (cortante/perfurante/contundente/natural) que o
  `start` já carrega; ataques sem `impacto` não mostram tipo.
- **Habilidade especial** = `attack_name`. Habilidades que não passam por
  `_emitir_feedback_ataque` (buff, magia sem ataque) ficam fora da faixa na v1.
- Ids dos monstros que ainda vão agir viajam a todos; o cliente só desenha o
  tracejado nos que já renderiza (visíveis).

---

### Task 1: Estado da sala, mensagem e persistência (servidor)

**Arquivos:**
- Modificar: `server.py` (init ~12004; `FOTO_SALA_CATEGORIAS` ~3590; carga do save
  ~3770; gravação ~26683; payloads `game_state` ~52122 e `city_state` ~13331; lista
  de mensagens permitidas ~52645 e despacho ~53684)
- Testar: `tools/test_velocidade_inimigos.py` (novo)

**Interfaces:**
- Produz: atributos de sala `velocidade_inimigos: str = "atual"` e
  `ritmo_auto_segundos: int = 0`; `async handle_set_velocidade_inimigos(self, pid,
  nivel, auto_segundos=0)`; constantes de módulo `RITMO_NIVEIS`,
  `RITMO_SEGUNDOS = {"lento": 3, "muito_lento": 6}`, `RITMO_AUTO_OPCOES = (0, 3, 6, 10)`,
  `RITMO_TETO_CLIQUE_S = 90`; chaves `velocidade_inimigos` e `ritmo_auto_segundos` nos
  dois payloads.

- [ ] **Passo 1: testes que falham** em `tools/test_velocidade_inimigos.py`, usando o
  padrão de `tools/test_atravessar_aliados.py` (sala real, `send_to` capturado):
  `test_padrao_atual`, `test_anfitriao_muda_nivel`, `test_nao_anfitriao_recusado`,
  `test_passo_recusado_no_multiplayer`, `test_passo_aceito_no_solo`,
  `test_nivel_invalido_recusado`, `test_auto_fora_das_opcoes_vira_zero`,
  `test_persiste_no_jogo_salvo` (grava e reabre), `test_aparece_nos_dois_payloads`.
- [ ] **Passo 2:** `python -X utf8 tools/test_velocidade_inimigos.py` →
  esperado: FALHA (atributo/handler inexistente).
- [ ] **Passo 3:** implementar o handler espelhando `handle_set_atravessar_aliados`
  (13831): `_eh_anfitriao`; `nivel in RITMO_NIVEIS`; `passo` só quando
  `self._jogo_salvo_solo()` for verdadeiro (12946); `auto_segundos` fora de
  `RITMO_AUTO_OPCOES` vira 0; chamar `_checkpoint_savegame`; `push_state` na masmorra
  ou `broadcast_city_state` na cidade. Registrar os dois campos como `"jogo_salvo"` em
  `FOTO_SALA_CATEGORIAS`, no init, na carga do save, na gravação e nos payloads; novas
  mensagens `set_velocidade_inimigos` e `continuar_turno_inimigo` na allow-list e no
  despacho (a segunda chama `handle_continuar_turno_inimigo`, criado na Task 3).
  Erros novos em `src/lang/erros.js`: `erro.somente_o_anfitriao_pode_alterar_velocidade`,
  `erro.velocidade_invalida`, `erro.passo_a_passo_so_no_solo`.
- [ ] **Passo 4:** rodar o teste → PASSA; rodar
  `python -X utf8 tools/test_salvar_masmorra.py` (varre atributos sem categoria) e
  `python -X utf8 tools/test_erros.py`.
- [ ] **Passo 5: commit** só os trechos desta feature.

### Task 2: Coletor de ataques do monstro (servidor)

**Arquivos:** `server.py` (`_emitir_feedback_ataque` ~32045; helpers novos próximos);
teste em `tools/test_velocidade_inimigos.py` (seção nova).

**Interfaces:**
- Produz: `self._ritmo_coletor: dict | None`; `_ritmo_iniciar(monstro)`;
  `_ritmo_finalizar() -> list[dict]` com itens
  `{"alvo_id", "alvo_nome", "alvo_pid", "ataque", "impacto", "acertou", "critico", "rolagem", "total", "dano"}`;
  `_hp_de(alvo) -> int` (`hp` se existir, senão `vida_atual`).

- [ ] **Passo 1: testes que falham:** `test_coletor_ignora_outro_atacante`,
  `test_coletor_registra_start_result`, `test_dano_pelo_delta_de_pv`,
  `test_dano_do_ultimo_ataque_no_fim_do_turno`, `test_alvo_de_area_sem_id_ignorado`,
  `test_sem_coletor_nada_muda` (payload do `attack_feedback` idêntico ao atual).
- [ ] **Passo 2:** rodar → FALHA.
- [ ] **Passo 3:** no início de `_emitir_feedback_ataque`, se `self._ritmo_coletor`
  existe, o `atacante["id"]` é o do coletor e `alvo.get("id")` não é `None`: no
  `start`, fechar a entrada aberta (dano = `max(0, hp_antes - _hp_de(alvo))`) e abrir
  nova com `ataque`, `impacto` (de `resultado`) e `hp_antes`; no `result`, preencher
  `acertou/critico/rolagem/total` da entrada com o mesmo `attack_id`. O coletor não
  altera o que é transmitido.
- [ ] **Passo 4:** rodar → PASSA; `python -X utf8 tools/test_sons_impacto.py` e
  `tools/test_projeteis.py` (usam o feedback) continuam verdes.
- [ ] **Passo 5: commit.**

### Task 3: Ritmo na fila de iniciativa, espera e visibilidade (servidor)

**Arquivos:** `server.py` (`_activate_initiative_actor`/`monster_step` ~18429;
`handle_disconnect_em_jogo` ~18711; helpers novos); testes na mesma suíte e nova
seção de regressão.

**Interfaces:**
- Consome: Task 1 (campos, constantes) e Task 2 (coletor).
- Produz: mensagens do servidor
  `turno_inimigo_agindo {monstro_id: str|None, proximos: [str]}` e
  `resumo_ataque_inimigo {monstro_id, generico: bool, atacante_nome: str|None,
  ataques: [...], espera: "tempo"|"clique", segundos: int}` e
  `resumo_inimigo_fechado {}`; `async handle_continuar_turno_inimigo(self, pid)`;
  `async _ritmo_apos_turno(self, monstro) -> None`; `_ritmo_visao_para(pid, monstro)
  -> "completo" | "generico" | None`.

- [ ] **Passo 1: testes que falham:** `test_atual_nao_espera_nem_envia` (regressão),
  `test_lento_espera_e_avanca` (com `asyncio.sleep` trocado por relógio falso),
  `test_muito_lento_usa_6s`, `test_passo_espera_clique_e_libera`,
  `test_passo_tem_teto_de_90s`, `test_passo_auto_fecha_pelo_tempo`,
  `test_so_andou_nao_gera_faixa`, `test_dormente_pulado_sem_mensagem`,
  `test_monstro_morto_no_turno_ainda_resume`, `test_fim_de_jogo_nao_espera`,
  `test_desconexao_solo_libera_espera`, `test_falha_na_espera_nao_congela`
  (força exceção em `_ritmo_apos_turno` e confirma que `_advance_initiative` roda),
  `test_clique_de_quem_nao_deve_ignorado`, `test_visao_generica_para_monstro_nao_visto`,
  `test_alvo_de_outro_jogador_sem_visao_nao_recebe`, `test_trocar_nivel_cancela_espera`.
- [ ] **Passo 2:** rodar → FALHA.
- [ ] **Passo 3:** em `monster_step`: se `_ritmo_ativo_para(monstro)` (nível ≠ atual,
  `phase == "playing"`, não `test_mode`, `_monstro_ativo_em_combate`), enviar
  `turno_inimigo_agindo` (personalizado por `_ritmo_visao_para`) e iniciar o coletor;
  rodar `monster_corpo` dentro de `_isolar` como hoje; chamar
  `await self._isolar(self._ritmo_apos_turno(monstro), ...)`; limpar o coletor e
  enviar `turno_inimigo_agindo` vazio; só então `_advance_initiative()`.
  `_ritmo_apos_turno`: sem entradas ou `phase != "playing"` → retorna; envia o resumo
  personalizado via `broadcast(personalize=...)` (completo/genérico/ausente por
  destinatário); espera com `asyncio.Event` (`self._ritmo_evento`): `tempo` →
  `wait_for(timeout=RITMO_SEGUNDOS[nivel])`; `passo` → `wait_for(timeout=auto_segundos
  or RITMO_TETO_CLIQUE_S)`; no fim envia `resumo_inimigo_fechado`. O evento é liberado
  por `handle_continuar_turno_inimigo` (só `passo`, `pid` conectado desta sala),
  por `handle_disconnect_em_jogo` no Solo, por troca de nível e por fim de partida.
- [ ] **Passo 4:** rodar a suíte nova; rodar a regressão da cadeia de turnos:
  `python -X utf8 tools/test_simulador_turno.py`, `tools/test_fosso.py`,
  `tools/test_modo_mestre.py`, `tools/test_handler_smoke.py` e
  `tools/test_broadcast_otimizado.py`.
- [ ] **Passo 5: commit.**

### Task 4: Estado e envio no cliente (`gameState.js`)

**Arquivos:** `src/gameState.js` (perto de `setAtravessarAliados` ~2485 e do tratamento
de mensagens); teste novo `tools/test_turno_inimigo_cliente.js`.

**Interfaces:**
- Consome: mensagens da Task 3 e campos da Task 1.
- Produz: `GS.velocidadeInimigos` (lê de `gameState`/`cityState`),
  `GS.ritmoAutoSegundos`, `GS.setVelocidadeInimigos(nivel, autoSegundos)`,
  `GS.continuarTurnoInimigo()`, `GS.turnoInimigo()` →
  `{ agindo, proximos, resumo }`; eventos `turnoInimigo` e `resumoInimigo`
  (um `GS.on` por evento, registrados em `game.js` na Task 5).

- [ ] **Passo 1: teste que falha** (padrão dos `tools/test_*_cliente.js`, carregando
  o `gameState.js` real): `setVelocidadeInimigos` envia
  `{type:'set_velocidade_inimigos', nivel, auto_segundos}`; `continuarTurnoInimigo`
  envia `{type:'continuar_turno_inimigo'}`; `turno_inimigo_agindo` atualiza o estado e
  dispara `turnoInimigo`; `resumo_ataque_inimigo` guarda o resumo e dispara
  `resumoInimigo`; `resumo_inimigo_fechado` limpa; um `game_state` novo não apaga o
  resumo em curso; saída da masmorra limpa tudo.
- [ ] **Passo 2:** `node tools/test_turno_inimigo_cliente.js` → FALHA.
- [ ] **Passo 3:** implementar sem DOM/`window`.
- [ ] **Passo 4:** → PASSA; `node tools/test_estado_diferido_cliente.js` verde.
- [ ] **Passo 5: commit.**

### Task 5: Faixa, anel e seletor (`game.js`)

**Arquivos:** `game.js` (painel ⚙️ ~35623 e `_refreshAtravessarOption` ~35868 como
molde; `_toggleConfigPop` ~35891; renderização 2D/3D; fim de `renderMap`);
`src/lang/interface.js`; teste `tools/test_turno_inimigo_cliente.js` (seção de fonte).

**Interfaces:**
- Consome: `GS.*` da Task 4.
- Produz: `_refreshVelocidadeInimigosOption()` (chamada ao lado das outras em
  `_toggleConfigPop`), `_renderFaixaInimigo()` (`#faixa-inimigo`, fixa no alto, com
  botão "Continuar" só quando `espera === 'clique'`), `_inimigoAnel2D`/anel 3D
  (vermelho no `agindo`, tracejado nos `proximos` renderizados), chaves
  `ui.turno_inimigo.*` e `ui.menu.velocidade_*` PT/EN.

- [ ] **Passo 1: teste que falha** (análise do fonte, como `test_ignus_fatus_cliente.js`):
  seletor só mostra "Passo a passo" quando o jogo é Solo; só o anfitrião habilita o
  controle; a faixa chama `GS.continuarTurnoInimigo`; Enter/Espaço e o botão de confirmar
  do controle fecham a faixa; o anel respeita a névoa (usa a mesma visão do desenho de
  peões); um único `GS.on('turnoInimigo')` e um único `GS.on('resumoInimigo')`.
- [ ] **Passo 2:** rodar → FALHA.
- [ ] **Passo 3:** implementar. Opção de tempo automático aparece só com "Passo a
  passo". Texto da faixa completa: quem, em quem, "acertou/errou (roll contra CA)", dano
  e tipo, nome do ataque; genérica: "Um inimigo atacou {alvo}: …". Estilo no padrão do
  painel (sem emoji novo além dos já usados).
- [ ] **Passo 4:** → PASSA; `python -X utf8 tools/test_interface.py`,
  `python -X utf8 tools/test_idioma.py`, `python -X utf8 tools/dividas.py --strict`
  (sem dívida nova); `node --check game.js`.
- [ ] **Passo 5: commit.**

### Task 6: Prova em partida, documentação e fechamento

**Arquivos:** `CLAUDE.md` (parágrafo novo "Velocidade do turno dos inimigos"),
`docs/` (nada além).

- [ ] **Passo 1:** subir um servidor de teste isolado (porta própria, sem tocar em
  `accounts/` do usuário; padrão do `run_teste.py` do worktree) e provar no navegador,
  nos quatro níveis: faixa, anel, tracejado, botão "Continuar", tempo automático e teto;
  repetir em tela de 390×844. Lembrar do polyfill de `requestAnimationFrame` com o painel
  oculto e do cache-buster ao recarregar o cliente.
- [ ] **Passo 2:** suíte relacionada completa verde (as das Tasks 1–5 mais
  `test_ignus_fatus.py`, `test_bomba_fumaca_reacao.py` para a fila com janelas de reação).
  Falhas pré-existentes conhecidas (`test_simulador_turno` goblin-throw,
  `test_charcos_fluxo.test_masmorras_gravadas`, `test_campanha_sombras`,
  `test_interface` draggable) devem ser apenas relatadas.
- [ ] **Passo 3:** documentar em `CLAUDE.md` (níveis, mensagens, constantes, regra "um
  `GS.on` por evento", testes). Commit final, sem arrastar o WIP de outra sessão.
