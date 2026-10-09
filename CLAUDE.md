# Legends for Hire — Regras de Arquitetura

## Visão Geral

### Goblin Combatente — equipamento por instância (2026-10-08)

`make_monster` sorteia uniformemente uma arma entre `lanca_curta`, `bordao`,
`cajado_madeira`, `shortsword`, `maca` e `machado_basico`, antes de chamar
`_aplicar_equipamentos_monstro`. Rolagens independentes dão 10% de chance de
`escudo_p` (+1 CA) e 5% de `health_potion_small` na `equipment_consumables`.
`combatant_weapon_id` e `combatant_shield_id` (ID ou `None`) guardam a seleção;
`equipped_items` contém somente arma e escudo. Cada consumível é cópia do catálogo.
O ataque usa nome, dado, categoria e alcance do catálogo, com bônus +2; mantém o
crítico padrão dos monstros, sem importar propriedades de crítico dos heróis.
O subtipo nativo é explicitamente `raca_padrao`: a inferência por `ente` no nome
classificava esta ficha como vegetal e impedia aplicar equipamento.
O Combatente não tem adaga garantida nem Arremesso (`pode_arremessar=False`);
o Goblin Dual conserva ambos. A tabela de ouro permanece a original.
Na morte, os IDs equipados do Combatente resolvem pelo catálogo mesclado
`_DUNGEON_ITEM_CATALOG` (inclui o escudo da loja de armaduras), e o loot recebe
uma cópia dos consumíveis ainda em `equipment_consumables`, com seus metadados.
A IA genérica já cura 5 PV com a poção pequena a 50% dos PV ou menos,
remove a dose usada e continua o ataque normal; não foi alterada.
`image` publica `goblinCombatente_<arma>_<sem_escudo|com_escudo>` com base no
equipamento real. O cliente usa essa chave tanto para o PNG em
`assets/pawns/monstros/<chave>/<chave>.png` quanto para o GLB em
`assets/models3d/monstros/<chave>.glb`; ambas as famílias cobrem as mesmas 12
combinações de arma e escudo. O Goblin Dual e estados antigos sem chave
continuam usando os assets legados. Para reconstruir e validar a família 3D,
use `blender --background --python
tools/build_goblin_combatente_3d_variants.py`.
Testes: `python -X utf8 tools/test_goblin_combatente_equipamento.py`,
`python -X utf8 tools/test_goblin_combatente_loot.py` e
`python -X utf8 tools/test_goblin_combatente_variants.py`.
Spec: `docs/superpowers/specs/2026-10-08-variedade-goblin-combatente-design.md`.

### Orc simples — equipamento sorteado ao spawn (2026-10-08)

Só o tipo `orc` (não `orc_guerreiro`) recebe equipamento aleatório em
`make_monster`: espada de duas mãos, martelo de guerra com Escudo Grande ou
mangual com Escudo Grande, cada combinação com 1/3 de chance. Uma rolagem
independente seleciona Cota de Malha em 10%, Armadura de Couro em 20% e nenhuma
armadura em 70%; as armaduras nunca se acumulam. `equipment_enabled` aplica a
arma e os bônus defensivos; o loot usa os IDs realmente equipados. A imagem e os
assets de miniatura permanecem os mesmos.

### Kobold Lanceiro — armas sorteadas (2026-10-08)

`make_monster` escolhe uma de quatro combinações com chances iguais: lança curta,
adaga, espada curta com Escudo Pequeno ou bordão. A escolha fica em
`kobold_weapon_id`; o aplicador de equipamento ajusta ataque e CA, e a IA
especial de arremesso/recolhimento só é ativada para a lança. A arma e o escudo
escolhidos entram no loot; se a lança já estiver no chão, não é duplicada. A
chave visual continua `koboldlanceiro`: não há variantes nem alterações em PNG
ou modelo 3D.

### Campo de Treinamento — salas por herói (2026-10-01)

`tutorial_training.py` é o mixin autoritativo de `GameRoom` para cenários de treinamento. A flag autorada `tutorial_training` prepara aliados NPC separados de `players`, bonecos privados e o refém de Richard. `allowed_class` nas salas bloqueia movimento, porta, voo, teleporte e servos incompatíveis; cliente e editor conservam o contrato.

Lições aceitam `requisitos` (nível, Guilda, magia utilizável, tipo de magia, instrumento), `sala_exclusiva` e condições de resultado na tarefa. Eventos de cura contextualizam alvo e vida recuperada. A demonstração de Protetor usa o funil real de dano; o refém precisa ser protegido antes da cura. Eventos de manutenção, ataque extra, detecção, resgate, purificação e ressurreição avançam as trilhas.

`tutorial_history` integra a ficha durável. `training_mode`, `training_allies` e `training_state` integram a foto da sala. `repetir_tutorial` reinicia somente os exercícios da classe na própria sala; mantém o histórico. NPCs não ocupam vagas, fila de turnos ou fichas de campanha. Itens emprestados e servos de treino são limpos na saída. Autoria: `tools/configurar_tutorial_salas.py`; roteiro e limites: `docs/tutorial-salas-por-heroi.md`; cobertura: `tools/test_tutorial_salas.py`.

### Campo de Treinamento — missão introdutória ilustrada (2026-10-09)

O caminho comum começa com o briefing da Guilda, preparação do herói, câmera e movimento, inventário/equipamento, menus H (habilidades) e M (magias quando há magia utilizável), combate com bonecos, confirmação da ameaça dos esqueletos e retirada. O objetivo permanece `all_heroes_at_exit`; o grupo precisa se reunir junto à saída. Comida, consumíveis, hostilidade e atalhos continuam como lições opcionais. As trilhas exclusivas de classe continuam independentes e repetíveis.

O conteúdo do guia comum é autorado em `tools/tutorial_guia_comum.py`, aplicado pelo patch idempotente `tools/aplicar_tutorial_missao.py`, incluído em `tools/configurar_tutorial_salas.py`; `tools/gerar_guia_comum.py` gera `src/lang/tutorial_guia.js` e injeta as chaves no mapa. `fala_menu_magias` usa `requisitos.magia_tipo = qualquer`, que exige magia implementada com slot utilizável. O cliente avança esse passo quando o menu correspondente realmente abre.

Falantes podem trazer `falante.retrato` (`assets/portraits/*.png`) e `falante.cena` (`assets/tela de transição/tutorial/*.png`). O editor preserva e edita esses campos; o servidor aceita somente PNG local nesses diretórios. A abertura, a descoberta dos esqueletos e a retirada usam arte própria do Mestre de Armas com capelo. As cenas não contêm texto localizado.

> **Tutorial guiado — fatia 1 (2026-10-07):** a lição pode declarar `guia` (1 a 8 passos `{texto, porque?, ui?, dica?[≤2], conclui_com?}`); sem `guia` o servidor gera um passo `auto` a partir da tarefa (`_guia_ui_padrao`). O passo atual de cada herói é `p["licao_passo"]`; vai no payload da `fala` (`passo`), no bloco `tutorial.por_classe[cls].passo` e na mensagem `licao_passo`. Um passo avança quando o evento que ele declarou em `conclui_com` chega a `_licao_evento` (mesmo que a tarefa da lição seja outra) ou pelo botão "Entendi" (`avancar_passo`, só para passo informativo: não-último e sem `conclui_com`). O último passo nunca avança sozinho: quem encerra a lição é a tarefa. Armar uma habilidade é ação só do cliente, então esse passo é informativo. `ui` aponta o elemento: `botao:|habilidade:|bolsa:|slot:|monstro:|hud:<id>` ou `casa:|porta:[x,y]` (`GUIA_UI_RE`). Cliente: `src/guiaTutorial.js` (puro: `parseUi`, `seletor`, `nivelDica`, `textoDica`); o `game.js` aplica `.guia-halo` por um laço de 400 ms (o HUD é redesenhado por innerHTML e apagaria a classe), endurece a dica em `VC.tutorial.dica1S/dica2S` e encerra halo e janela (`_guiaEncerrar`) quando chega um `game_state` sem a lição. **Fatia 2 (2026-10-07):** o halo também vai ao tabuleiro e à bolsa. `casa`, `monstro` e `porta` são desenhados em 2D (`_guiaDesenhar2D`, fim do `renderMap`, redesenho ~12 fps por `_agendarChamas2D`) e em 3D (`g3.guiaMarca`, anel + seta; `_guiaAtualizar3D` no `startLoop3D`); a `porta` ganha a trilha do caminho até ela (`GuiaTutorial.caminhoAbsoluto`, teto `GUIA_TRILHA_MAX`=48). O halo nunca revela névoa (filtro de visão em `alvoTabuleiro`). `bolsa`/`slot` marcam `.inv-bagslot[data-item-id]`/`.inv-slot[data-slot-key]`, caindo no botão da mochila se o inventário está fechado. **Dica por erro:** o hook no início de `GameRoom.send_to` converte recusas conhecidas (`GUIA_DICA_POR_ERRO`/`_POR_PREFIXO`) em `licao_dica {licao_id, motivo}` (limite de 1 a cada 5 s por herói; `alvo_errado`/`longe_do_alvo` só em tarefa com alvo de combate), e `handle_attack` manda `licao_resultado {roll, bonus, total, ca}` durante a lição; o cliente mostra ambos em `#licao-aviso`. Chaves `ui.tutorial.dica_erro.*`/`resultado.*` em `src/lang/tutorial.js`. Plano: `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia2-tabuleiro.md`. Textos de passo aceitam chave `ui.tutorial.*`. Spec/plano em `docs/superpowers/{specs,plans}/2026-10-07-tutorial-guiado*`. Testes: `tools/test_tutorial_guia.py` e `tools/test_guia_tutorial_cliente.js`. **Fatia 3 (2026-10-07):** glossário e trilha comum. O texto de passo aceita `[[termo]]` (`GuiaTutorial.segmentos`, puro): o `game.js` (`_tutHTML`) sublinha o termo na 1ª vez da sessão e abre o balão `#guia-balao` ao tocar (definições em `ui.tutorial.glossario.<termo>.nome/.texto`); o termo só vira "visto" quando o passo muda (`_guiaFecharPasso`), para o sublinhado sobreviver a redesenhos, e `_setLang` redesenha a janela da lição aberta. As 15 lições comuns do Campo de Treinamento (`fala_0`–`fala_4`, `18`, `19`, `29`–`33`, `36`–`38`) ganharam `guia`: o conteúdo (pt+en) mora em `tools/tutorial_guia_comum.py`, `tools/gerar_guia_comum.py` grava `src/lang/tutorial_guia.js` (gerado, não edite) e injeta `guia` só com chaves no JSON, e o `configurar_tutorial_salas.py` chama o mesmo `aplicar_guia`. **Regra de ouro:** `conclui_com` nunca para evento que o jogador pode ter feito ANTES da lição (ex.: pegar item de baú compartilhado trava o passo); use passo informativo ("Entendi"). Testes: `tools/test_tutorial_conteudo.py`. Plano: `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia3-trilha-comum.md`. **Fatia 4 (2026-10-07):** as 47 lições das seis classes ganharam `guia` (conteúdo em `tools/tutorial_guia_<classe>.py`, juntado por `gerar_guia_comum.guia_todos()`; com a trilha comum são as 62 lições autoradas). Glossário em 14 termos (`d20`, `acao_principal`, `slot`, `teste_resistencia`, `manutencao`, `furtivo`, `critico` entraram) e `botao:magias` no ✨. **Regra:** `habilidade:<id>` só quando `<id>` é o `tarefa.alvo` da lição (é o que o botão do HUD traz em `data-ability-id`). O halo de `habilidade:` varre todos os candidatos e pega o primeiro **visível** com o ancestral pedido: o mesmo `data-ability-id` existe em telas escondidas (seleção de classe) e o `querySelector` simples acendia o ícone invisível. As lições geradas em jogo (`treino_guild_*`, `treino_magia_*`) levam `guia_modelo` (dict simples; `licoes` é categoria `foto` e **nunca** pode conter `T`) e `_guia_passos_modelo` expande em `T` por jogador na hora do envio, só com chaves de catálogo que existem. Testes: `tools/test_tutorial_classes.py`, `tools/test_tutorial_modelos.py`. Plano: `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia4-salas-e-geradas.md`. **Fatia 5 (2026-10-07):** o editor de masmorras **preserva** o `guia` ao abrir/salvar — antes `loadJSON`/`buildJSON` copiavam campo a campo e o apagavam, então salvar o Campo de Treinamento pelo editor zerava o guia das 62 lições — e edita os passos no painel da fala (`renderGuiaPassos`: ↑ ↓ ✕, destaque `ui` por tipo+valor, até 2 dicas, `conclui_com`). A lógica é o módulo puro `tools/editor_guia_logic.js` (`EDITOR_GUIA`: `carregar`/`serializar`/`validar`/`lerUi`/`montarUi`), sincronizado com `GUIA_UI_RE`/`GUIA_MAX_PASSOS`/`LICAO_VERBOS` do servidor por `tools/test_editor_guia.py`; a validação do editor usa `V(codigo)` com as chaves `ui.editor.masmorra.valid.guia_*`. Passo cujo texto é chave do dicionário (`ui.tutorial.*`, gerado por `gerar_guia_comum.py`) é somente leitura até "Converter em texto livre" — por isso o `editor.html` carrega `src/lang/tutorial_guia.js` (sem ele o painel mostrava a chave crua). Texto digitado é conteúdo autoral em português, sem campo por idioma. O campo de trabalho `p._uiTipo` guarda o tipo de destaque escolhido antes do valor e nunca vai ao JSON. O editor abre masmorra por arquivo JSON; `tools/editor_dungeons.js` é só um snapshot gerado para as abas de campanha/mapa-múndi. Testes: `tools/test_editor_guia_logic.js` (roundtrip das 62 lições reais) e `tools/test_editor_guia.py`. Plano: `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia5-editor.md` (o script de commit parcial do plano falha no Windows por converter `
` em CRLF no stdin: ver o relato da Task 4). Fora de escopo: escolher o `ui` clicando no mapa e campo de texto por idioma. **Fatia 6 (2026-10-08):** feedback do Lucas. O texto de passo traz o verbo de ação e o alvo (o "Me mostra" só destaca; teste `RedacaoAcionavelTests` em `tools/test_tutorial_conteudo.py`). O servidor manda `licao_passo_ok {licao_id, passo, total}` em `_guia_avancar` (o cliente anima o "✓ Passo concluído!", `.licao-ok`) e `licao_concluida {licao_id, recompensa:{ouro,xp,trilha}}` em `_licao_concluir` (selo `.licao-selo`). A recompensa (`TUTORIAL_RECOMPENSA_OURO/XP` = 5/10; `TUTORIAL_BONUS_TRILHA_OURO/XP` quando a última lição da trilha da classe fecha) é paga **uma vez por personagem**: a guarda é `tutorial_history` (repetir via `repetir_tutorial` mostra o selo sem prêmio). Não há campo `recompensa` por lição (só as constantes). Lições comuns novas: `fala_atalhos` (ordem 19, sala 23, `[42,16]`; passos H, R, Esc e clicar para andar), `fala_res` (20) e `fala_vuln` (21), ambas em `[43,17]`; as antigas `fala_36`–`fala_38` foram **removidas** (ordens 16–18 ficam vagas, `_licao_liberada` só compara `<`; `tutorial_history` com ids inexistentes é ignorado) e a `fala_vuln` absorveu pegar (`casa:[42,17]`, o baú da `maca_treino`) + equipar + atacar, com a dica "arma certa vale mais que rolar bem o dado". A sala 23 tem 2 esqueletos (`[44,15]` original e `[44,17]`): um por lição e um de folga contra beco sem saída. Glossário novo: `atalho`, `vulnerabilidade`. A resistência do esqueleto é **redução fixa por categoria de arma** (`weaknesses` com `bonus_flat`: cortante −1, perfurante −2, contundente +2), então o texto fala em "pontos", não em cores. O texto das cores RESISTIDO/VULNERÁVEL (`ui.menu.damage.status.resisted`) depende da integração de `codex/ceu-abismo` (ausente no master): quando entrar, acrescente-o ao passo `ler` de `fala_res`/`fala_vuln`. Cuidado: rodar o `configurar_tutorial_salas.py` por inteiro reordena as chaves do JSON da masmorra, por isso os blocos novos (falas, esqueletos) foram aplicados à parte, de forma idempotente. **Achar a sala da classe:** cada porta exclusiva tem uma `placa` (`placa_<classe>`, do lado de fora, a 1 casa da porta; o texto é lido ao clicar na placa estando adjacente, via `interagir_decor`/`decor_message`, e não viaja no `game_state`) e cada herói ganha a lição-ponte `porta_<classe>` (ordem 3, tarefa `mover_ate` na casa da porta, guia `porta:[x,y]`) logo depois da última lição comum (`fala_6/8/10/12/14/16`): o guia da lição comum acaba junto com a tarefa `matar`, então o halo tinha de morar numa lição própria; por isso as lições exclusivas de `configurar_tutorial_salas.py` agora nascem com `ordem+1`. Teste: `tools/test_tutorial_portas.py`. **Fatia 7 (2026-10-08, feedback do Lucas):** (a) cada trilha de classe termina numa lição-ponte `volta_<classe>` (ordem da última + 1, `trigger sala`, tarefa `mover_ate [28,15]`, que é onde a `fala_18` recomeça a trilha comum): como a lição final se conclui no instante da tarefa, a mensagem "volte ao corredor e siga para a próxima sala" só aparece como lição NOVA depois do selo (passo 1 `porta:` da sala, conclui ao pisar nela; passo 2 `casa:[28,15]`). Ids com prefixo `volta_` (`LICAO_FORA_DA_TRILHA_PREFIXOS`, em `tutorial_training.py`) não contam para o bônus da trilha (sai na última lição de verdade, uma vez) e o `repetir_tutorial` as refaz. (b) "Me mostra" agora ensina a USAR o item como o jogo faz: abrir a bolsa, **clique direito** no item (ou duplo clique; no controle, escolher USAR e confirmar; não existe botão "Usar") e, no frasco de óleo, clicar no inimigo dentro do alcance vermelho; `fala_31` e `fala_33` também dizem "botão direito". (c) Bug do tutorial travado: o óleo matava o `boneco_treino` que a lição do veneno (`fala_32`) ainda precisava. Agora o óleo tem o **`boneco_palha`** próprio (bestiário, 2 PV, `weaknesses` fogo ×2, então o dano mínimo do óleo já o mata de uma vez; 2 na sala 22, em `[38,17]`/`[38,18]`) e o veneno fica com 3 `boneco_treino` (8 PV) na mesma sala. A `fala_30` NÃO exige o tipo do alvo (um frasco jogado no boneco errado conclui a lição do mesmo jeito; exigir travaria, já que há um só frasco). Os textos das lições de dano falam das cores do dano (VULNERÁVEL em vermelho, RESISTIDO em azul, `ui.menu.damage.status.*`, integradas no commit 34c21b5). As mudanças do JSON da masmorra saem de `tools/aplicar_fatia7_tutorial.py` (idempotente, só acrescenta; também é chamado pelo `configurar_tutorial_salas.py`). Cuidado: o editor de masmorras reescreve o JSON inteiro ao salvar; quem estiver com o editor aberto desde antes precisa recarregar o arquivo, senão o próximo save apaga os bonecos e as lições `volta_*`. Testes: `tools/test_tutorial_fatia7.py` (inclui o óleo real matando a palha e o fluxo selo → mensagem → chegada nas 6 classes). Testes: `tools/test_tutorial_conteudo.py`, `tools/test_tutorial_guia.py`, `tools/test_guia_tutorial_cliente.js`. Plano: `docs/superpowers/plans/2026-10-07-tutorial-guiado-fatia6-feedback-lucas.md`. **Fatia 8 (2026-10-08):** (1) o golpe que MATA tira o monstro do `game_state` (`hp > 0`), então o cliente nunca via o número do dano nem a cor VULNERÁVEL/RESISTIDO dele (o servidor já mandava `damage_reaction`): o `boneco_palha` ficou com 24 PV (o óleo x2 não o derruba no 1º frasco) e `_detectHpChanges` ganhou `_golpesLetaisComReacao`, que desenha o número do golpe letal que tem reação. (2) `boneco_treino_veneno` (tipo novo, sem a imunidade de construto, fraqueza `poison` x2, Fortitude -20, 20 PV) ocupa o lugar dos `boneco_treino` da sala 22; o tique de veneno de MONSTRO agora passa por `_apply_damage_types` (antes ia direto a `_dano_em_alvo` e nenhuma fraqueza a veneno valia); `fala_32` exige `boneco_treino_veneno`. (3) Seguir adiante não trava: quando uma lição vai disparar e as que a seguram (a tarefa pendente e as anteriores não cumpridas da mesma trilha) JÁ ficaram para trás (`_licao_zona_contem`: raio do gatilho/sala, e a vizinhança do alvo de uma tarefa `mover_ate`), `_pular_etapas_abandonadas` as marca em `licoes_feitas`/`licao_progresso` e em `p["licoes_puladas"]` (sem prêmio, sem `tutorial_history`, fora de `room.licoes_feitas`, sem bônus de trilha) e manda `licao_pulada {licao_id}` antes da fala nova; basta UMA ainda ao alcance para nada ser pulado (lições em sequência na mesma zona esperam). Cliente: `GS.on('licaoPulada')` fecha a janela se for a aberta. Dados: `tools/aplicar_fatia8_tutorial.py` (cirúrgico, idempotente; também espelha `tools/editor_monsters_custom.js`). Testes: `tools/test_tutorial_fatia8.py`, `tools/test_tutorial_fatia8_cliente.js`. **Fatia 9 (2026-10-08):** o refém do Paladino atrapalhava as lições seguintes (o jogador tinha de comandá-lo a cada turno). Nova lição `treino_guiar_refem` (verbo `guiar_refem`, também em `LICAO_VERBOS_CASA`; `tarefa.alvo` = a casa [32,24], junto à porta da sala 38) logo depois de `treino_maos`; as posteriores do Paladino ganharam `ordem` +1 (`volta_paladin` 12). O refém de treino, que não andava, agora anda DENTRO da própria sala (`_training_refem_pode_ir`) na janela pós-turno de sempre (encerrar o turno abre a vez dele; o cliente já o seleciona sozinho). Ao terminar um passo na casa-alvo, `_training_refem_chegou` dispara `_licao_evento("guiar_refem", pos)` e, com a lição cumprida (prêmio normal), `_dispensar_prisioneiro` põe `self.prisoner = None` (sem `rescue_failed` nem derrota; encerra o Protetor que o tinha como alvo, narra `narracao.refem_agradece_e_se_retira`) e os handlers de movimento fecham a janela vazia (`_fechar_janela_sem_prisioneiro`). O molde do refém fica em `training_state["refem_modelo"]` (viaja na foto) e `repetir_tutorial` do Paladino recoloca o refém inteiro na casa de origem. O cliente não mudou: `game_state.prisoner` nulo já derruba o peão (`obterFig` descarta o não usado) e o botão. Dados: `tools/aplicar_fatia9_tutorial.py` (cirúrgico, idempotente; o `configurar_tutorial_salas.py` cria a mesma lição pelo `lesson()`). Testes: `tools/test_tutorial_refem.py`. **Fatia 10 (2026-10-08):** a placa da sala do herói (`placa_<class_id>`, achada por id, sem coordenada cravada) fica em evidência na vez dele até cumprir as lições de habilidade da classe. Regra derivada (`TutorialTraining._placa_em_evidencia`): enquanto existir lição autorada `treino_*` da classe (fora `treino_guild_*`/`treino_magia_*` geradas, as comuns `fala_*` e as pontes `porta_/volta_`) com requisitos cumpridos e fora de `licoes_feitas`; lição PULADA já está em `licoes_feitas`, então conta como cumprida (a placa não acende para sempre em quem abandonou a etapa); `repetir_tutorial` a reacende. Payload: `tutorial.por_classe[cls].placa = {id, pos}`, ausente quando não vale (placa removida do mapa, fora do `training_mode`). Cliente: `GuiaTutorial.placaEmEvidencia(state, myPid, visivel)` (puro; só com `current_turn === myPid`, que no Solo com grupo acompanha o herói em foco) alimenta o MESMO halo do tabuleiro: `_guiaPlacaDesenhar2D` (anel + seta, `_agendarChamas2D`) e a marca própria `g3.guiaPlaca` em `_guiaPlacaAtualizar3D` (sem trilha); respeita a névoa pelo mesmo filtro de visão e se omite se o passo da lição já marca a mesma casa. Testes: `tools/test_tutorial_placa.py` e `tools/test_placa_evidencia_cliente.js`. **Fatia 11 (2026-10-08):** a trilha do Bardo ensina os instrumentos de verdade. Um baú com a **Harpa Velha** (`instrumento_harpa_velho`) fica em [10,22] na sala 43; trilha final: `porta_bard`(3) → `treino_harpa`(4, verbo `equipar`: pega do baú e equipa no `off_hand`; o Alaúde vai à bolsa) → `treino_nota_cortante`(5, `usar_instrumento` com `alvo:"harpa"`, o MESMO `_licao_evento(p,"usar_instrumento",alvo=base)` que `handle_usar_instrumento` já emitia, então Tambor/Sino não concluem; boneco em [12,24], linha ortogonal a até 3 casas; erro "sem inimigo na linha" vira dica `sem_alvo_na_linha`) → `treino_alaude`(6, re-equipar o Alaúde, `alvo:"instrumento"`) → `treino_cancao`(7, nova tarefa `requer_sinfonia`: só conclui se algum atributo escolhido recebeu o +1 do Alaúde, p.ex. Acerto no Alaúde Velho; o servidor narra `narracao.sinfonia_reforca_a_cancao` e passa `contexto.sinfonia`; erro vira dica `sem_sinfonia`) → manter(8) → parar(9) → provocar(10) → `volta_bard`(11); o genérico `treino_instrumento` saiu. Os itens do baú de sala exclusiva levam `tutorial_loan` e `training_state.baus_modelo[classe]` guarda o molde: `_training_devolver_emprestimos` (saída da masmorra e `repetir_tutorial`) tira a harpa da bolsa/mão e devolve o Alaúde ao `off_hand`; `_training_recolocar_bau` recoloca o baú cheio. O botão do instrumento ganhou `data-guia="botao:instrumento"` (halo) e o glossário `sinfonia`. JSON via `tools/aplicar_fatia11_tutorial.py` (idempotente; `configurar_tutorial_salas.py` o chama). Testes: `tools/test_tutorial_bardo_instrumento.py`. **Fatia 12 (2026-10-08):** o texto do guia aceita `[[atalho:inventario]]` (`GuiaTutorial.segmentos` devolve `{atalho:id}`; `GuiaTutorial.chaveAtalho(id, controleAtivo)` escolhe `ui.tutorial.atalho.<id>.teclado|controle` em `src/lang/tutorial.js`). O `game.js` (`_guiaAtalhoTexto`) resolve na hora de desenhar: controle conectado (`_gamepadInput.active`; o jogo não rastreia o último dispositivo usado) mostra o botão real de `characterMenu` por `_gamepadButtonLabel` (View/Share por padrão, o mesmo rótulo do HUD de atalhos), senão "a tecla I" (o atalho real do `keydown` global). `_guiaAtualizarDispositivo`, chamada nas transições de `_pollGamepad`, redesenha a janela da lição aberta ao conectar/desconectar. Passos "Abra a bolsa…" (`fala_2`, `fala_30`, ração, maça, Harpa e Alaúde do Bardo) levam o token; o token conta como 1 palavra. Testes: `tools/test_tutorial_conteudo.py` (`AtalhoInventarioTests`) e `tools/test_guia_tutorial_cliente.js` [19]. **Fatia 13 (2026-10-08):** o refém do Paladino não andava ao jogar de verdade. Causa: `_walkable` (`src/gameState.js`) barrava toda casa de sala com `allowed_class` quando o ator não tinha o mesmo `class_id`; o refém não é jogador (`findPath` o via como ator `{}`), então o clique achava caminho nulo, desselecionava o refém em silêncio e nada ia ao servidor (o servidor sempre esteve certo: a fatia 9 foi provada só por protocolo). Agora a trava só vale para ator com `class_id` (a do refém continua no servidor, `_training_refem_pode_ir`). O destino de `treino_guiar_refem` passou de [32,24] (diagonal) para [32,25], a casa à frente da porta [31,25]; os textos do guia explicam o fluxo real (Encerrar Turno abre a vez, o refém já vem selecionado, anda até 6 casas, saia da casa marcada se estiver nela). Script idempotente: `tools/aplicar_fatia13_tutorial.py`. Testes: `tools/test_tutorial_refem.py` (`FluxoRealTests`, com iniciativa e `push_state` reais) e `tools/test_refem_caminho_cliente.js`. **Regra:** prova de fluxo de UI não pode ser só por mensagem de protocolo; clique no cliente real. **Fatia 14 (2026-10-08):** o aprendiz de treino (`training_allies`, nome "Aprendiz N") não aparecia porque nasce com `connected=False` e os laços de peões 2D/3D do `game.js` descartam desconectado. Agora o laço poupa `training_ally`, o servidor manda `pawn_override="soldado"` e `_metamorfoseVisualName` devolve `soldado` para todo `training_ally` (nunca vazio): o 2D usa `assets/pawns/monstros/soldado/soldado.png` e o 3D o `soldado.glb` do `MONSTER_GLB`, pela maquinaria de forma visual existente. O aprendiz mostra barra de vida e "Aprendiz N hp/max" no 2D e uma placa sprite (`_makeAprendizTag3D`, hp na assinatura da figura) no 3D. Testes: `tools/test_tutorial_aprendiz.py` e `tools/test_aprendiz_cliente.js`. **Fatia 15 (2026-10-08):** dentro da sala exclusiva do Mago (`allowed_class == "mage"`, só casas de piso: a porta e o corredor ficam fora) as magias não gastam slots. A regra é derivada da posição (`_slots_livres_treino`, em `tutorial_training.py`; só `training_mode`, só `class_id == "mage"`, nunca `test_hero`/clérigo), sem estado novo: `_slots_disponiveis` devolve 99 e `_gastar_slot` não faz nada na sala, então não há o que devolver ao sair e os slots de antes de entrar seguem iguais. Fome/sede (🍖/💧), metamagia e ação principal continuam cobradas. O `game_state` traz `slots_livres_treino` e `slots_remaining` vazio para o herói na sala (o HUD e o Menu de Magias mostram "ilimitados (sala de treino)"); `handle_move` manda `licao_dica` com motivo `slots_treino_liga`/`slots_treino_desliga` só nas transições (chaves `ui.tutorial.dica_erro.slots_treino_*`). `treino_magia`, `treino_slots` e `porta_mage` explicam a regra (`tools/aplicar_fatia15_tutorial.py`; a tarefa de `treino_slots` segue `encerrar_turno`). Testes: `tools/test_tutorial_mago_slots.py`. **Fatia 16 (2026-10-08):** o Clérigo ganhou a mesma regra na sala 35: `_slots_livres_treino` vale para `mage` e `cleric` quando `room.allowed_class == class_id` (Mago na sala do Clérigo e vice-versa não ativam); só as magias do Grimório deixam de gastar slot, Cura/Cura em Massa/Purificação/Ressurreição seguem cobrando 💧/🍖 como sempre; cliente e avisos `slots_treino_*` são os mesmos. Duas lições novas antes das habilidades de classe, logo após `porta_cleric`: `treino_grimorio` (ordem 4, `usar_magia` com `requisitos {magia_tipo: qualquer}`, guia `botao:magias`) e `treino_grimorio_turno` (ordem 5, `encerrar_turno`, porque lançar gasta a ação principal que a Cura exige); `treino_cura`..`treino_ressuscitar` viraram 6..9 e `volta_cleric` 10 (`tools/aplicar_fatia16_tutorial.py`, textos em `tutorial_guia_clerigo.py`). Teste: `tools/test_tutorial_clerigo_magias.py`. **Fatia 17 (2026-10-08):** a lição do Grimório mandava abrir o "botão ✨ Magias", mas `#player-fabs` (o ✨) só aparece em tela ≤820px: no desktop o halo `botao:magias` não achava elemento visível e o texto citava um botão inexistente; a aba `✨ MAGIAS` do painel (Mago e Clérigo) agora leva `data-guia="botao:magias"` e o texto diz "aba". O aprendiz (fora de `players`) era alvo inválido das magias de aliado (`abencoar_arma`, `saciar`, `visao_escuro`, `voo`, `regeneracao_magica`): `_alvo_aliado_magia` o aceita na própria sala. Erro de mira no executor da magia já cobrava ação/fome e disparava `usar_magia`, concluindo a lição à toa: `handle_magia` espia as recusas enviadas ao conjurador, não emite o evento e, no treino, devolve a ação. Texto e dicas por tipo de alvo (aliado: você/aprendiz; área: casa livre; Comando e Corpo Pesado não têm alvo ali). Testes em `tools/test_tutorial_clerigo_magias.py`.

RPG de tabuleiro multiplayer online (estilo HeroQuest / D&D) para até 6 jogadores.
Servidor WebSocket Python + cliente HTML/JS com renderização Three.js.

---

## Estrutura de Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `server.py` | Servidor WebSocket (porta 8765) — toda lógica de jogo autoritativa |
| `index.html` | Shell HTML: CDNs do Three.js + scripts com cache-buster |
| `game.js` | Renderização e UI: 2D (canvas) e 3D (Three.js) — substitui o antigo `game.html` |
| `game.css` | Estilos do cliente |
| `src/gameState.js` | Módulo de estado do cliente — ZERO referências a DOM/canvas/Three.js |
| `src/visualConfig.js` | `window.VC` — fonte única de cores/intensidades/fontes do visual |
| `src/main.js`, `src/ui/theme.js` | Bootstrap e injeção de CSS custom properties |
| `assets/` | Peões (PNG), modelos 3D (GLB), retratos, fontes |
| `tools/` | Scripts DEV do pipeline de miniaturas (rodar da raiz: `python tools/<x>.py`) — desnecessários para jogar |
| `iniciar.bat` | Script de inicialização: mata porta antiga, sobe o servidor (porta única 8765), abre browser |
| `online.py` / `iniciar-online.bat` | Sobe servidor + túnel HTTPS (cloudflared/ngrok) e imprime UM link público para jogar pela internet |

---

## Regras de Arquitetura (OBRIGATÓRIAS)

### 1. Separação estrita: lógica vs. renderização

- **`gameState.js`** é o único lugar para lógica de jogo no cliente:
  - Estado do jogo (`gameState`, `lobbyState`, `cityState`)
  - BFS (pathfinding, alcance de movimento)
  - Decisores puros (`resolveAttack`, `resolveTileClick`, `activateSkill`)
  - Camada WebSocket (`connect`, `send`, `move`, `endTurn`, etc.)
  - **NUNCA** importar ou referenciar `document`, `canvas`, `THREE`, `window` aqui

- **`game.js`** é o único lugar para renderização:
  - Canvas 2D e Three.js 3D ficam aqui
  - Lê estado via `GS.*` (getters)
  - Registra callbacks via `GS.on(evento, fn)`
  - **NUNCA** implementar lógica de jogo ou cálculos de BFS aqui

### 2. Ordem de implementação de features

> **Estado primeiro, visual depois.**

Para qualquer nova feature:
1. Atualizar `gameState.js` — adicionar estado, getters/setters e/ou lógica pura
2. Atualizar `server.py` se necessário — novo protocolo de mensagem
3. Atualizar `game.js` — refletir o novo estado visualmente

### 3. Comunicação renderer → estado

O renderer (`game.js`) se comunica com `gameState.js` **apenas** via:
- `GS.on(evento, fn)` — registrar callbacks para eventos do servidor
- `GS.setter = valor` — mutar estado de UI (`pendingSkill`, `activeShop`, etc.)
- `GS.método()` — chamar action senders ou resolvers

O renderer **nunca** escreve diretamente em variáveis internas do módulo GS.

---

## Stack Técnica

### Servidor (`server.py`)
- Python 3.x + biblioteca `websockets`
- Porta: `ws://0.0.0.0:8765`
- Lógica autoritativa: mapa procedural, combate, monstros, XP/level, loja

### Cliente (`game.js` + `src/gameState.js`)
- Vanilla JS — sem frameworks, sem bundler
- Three.js `r128` (única versão com `examples/js/` disponível no jsDelivr)
- OrbitControls: `https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js`
- **ATENÇÃO**: versões r148+ do Three.js removeram `examples/js/` — usar SEMPRE r128

### CDN (em `<head>` de `index.html`)
```html
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
```

---

## Protocolo WebSocket

### Client → Server
| Mensagem | Campos |
|---|---|
| `create_room` | `name` |
| `join_room` | `name`, `code` |
| `rejoin` | `name`, `code` — religa um jogador desconectado em partida (recusa se ainda conectado). O cliente (`gameState.js`) salva a sessão em `localStorage` (`lfh_session`) e tenta sozinho 8× a cada 2,5 s; tela inicial tem botão "Reconectar". Move: o servidor sanitiza `dx`/`dy` para -1/0/+1 (1 casa ortogonal). |
| `select_class` | `class_id` |
| `select_party` | `classes:[…]` — **Solo com grupo**: o anfitrião de um jogo salvo Solo novo marca de 1 a 6 classes; substitui a seleção anterior. Os heróis além do 1º nascem com `controlador` (pid da conexão); as magias de cada um vão por `set_known_spells {ids, heroi}`. Ver "Solo com grupo". |
| `start_game` | — |
| `move` | `dx`, `dy` |
| `move_path` | `path:[[dx,dy],…]` — caminho inteiro numa mensagem (clique numa casa distante; `GS.movePath`, 1 casa cai no `move`). O servidor (`handle_move_path`) roda cada passo pelo MESMO `handle_move` com `_push=False`, para no 1º passo recusado, emite um `entity_step` `kind:"player"` por casa para TODOS e manda UM `game_state` no fim — antes era um `game_state` completo por casa para todos, em rajada, e quem assistia via o peão saltar. Cliente: o deslize (`_serverStepAnim`) agora também move o peão de herói no 2D e no 3D (`getPeaoMesh`, giro pela raiz), no ritmo `DURACAO_PASSO_MS`; o próprio passo é ignorado enquanto o peão já anima localmente (3D); o som de passo de outro herói segue o trajeto do deslize. Teto `MAX_PASSOS_CAMINHO`=40. Teste: `tools/test_move_path.py`. |
| `attack` | `target_id` |
| `prever_ataque` | `target_id`, `target_pos`, `buffs`, `chave` — prévia do ataque básico para o tooltip do monstro (só leitura, não gasta nada). Resposta privada `previsao_ataque` (`chance` 0–100, `vantagem`, `desvantagem`, `dano_dado`, `dano_fixo`, `golpe_mult`, `furtivo_d4`, `chave`). Acerto/CA/vantagem vêm de `_modificadores_ataque_heroi`, o MESMO helper do `handle_attack` — modificador novo de ataque entra lá e vale para os dois. Cache no cliente (`GS.previsaoAtaque`/`pedirPrevisaoAtaque`), invalidado a cada `game_state`. Teste: `tools/test_previsao_ataque.py`. |
| `pedir_metamorfose_catalog` | — pede o catálogo de formas da Metamorfose (enviado ao abrir a janela de formas). Resposta privada `metamorfose_catalog` (`formas:[…]`), guardada em `GS.metamorfoseCatalog`. O catálogo saiu do `game_state`, onde era ~80% de cada pacote (~96 KB a cada passo, para todos) — não devolva dado estático ao `game_state`. Teste: `tools/test_metamorfose_catalogo.py`. |
| `animar_mortos` | `cadaver_id` (Pedro anima cadáver adjacente) |
| `comandar_animados` | — (só no turno dos servos: todos os animados movem+atacam o monstro mais próximo automaticamente) |
| `mover_animado` | `animado_id`, `dx`, `dy` (controle manual — 1 passo) |
| `atacar_animado` | `animado_id`, `target_id` opcional, `target_pos` opcional (controle manual — ataque; o Raio do Elemental Elétrico aceita uma casa vazia para escolher a direção e atinge todas as criaturas na linha) |
| `libertar_prisioneiro` | — (herói adjacente liberta o prisioneiro; grava `rescuer_pid`). O prisioneiro (`prisoner`: CA10/mov6/7HP) é **controlado pelo resgatador**, não anda sozinho. |
| `mover_prisioneiro` | `dx`, `dy` — controle manual do prisioneiro liberto (1 passo, só movimento). Habilitado na **janela pós-turno** do controlador (mesma do turno dos servos, `animados_phase_pid`): encerrar o turno abre a janela e dá `moves_left=6`; encerrar de novo avança. Se o resgatador morre, o controle passa ao herói vivo mais próximo. Dano vs CA10 dos monstros adjacentes continua na fase inimiga (`_processar_prisioneiro_turno`). O prisioneiro também **sofre armadilhas colocáveis** ao pisar nelas, como os heróis (saves a +0 em reflexos/fortitude); morte por qualquer fonte → `_prisioneiro_morre`/`rescue_failed`. |
| `mover_animado_caminho` / `mover_prisioneiro_caminho` | `animado_id` (só o servo), `path:[[dx,dy],…]` — caminho inteiro do servo/prisioneiro numa mensagem (o clique do cliente usa estas); cada passo passa pelo handler de 1 casa com `_push=False` e sai um `game_state` no fim. É o que permite **atravessar aliados** sem parar em cima. |
| `set_atravessar_aliados` | `enabled` — só o anfitrião; liga/desliga a regra da sala "🚶 Atravessar aliados" (ver abaixo). |
| `salvar_e_sair` | — "💾 Salvar e sair" do ⚙️ (só com jogo salvo): grava o pendente (checkpoint; na masmorra vale a foto da última virada) e responde `salvo_para_sair {onde, rodada}`; o cliente fecha a sessão e volta a "Meus Jogos". Ver "Foto da masmorra". |
| `encerrar_missao` | — (herói encerra a fase **após** o objetivo principal cumprido; só habilitado quando `game_state.mission_complete_pending`). Concluir o principal **não** encerra mais automaticamente: o servidor concede a recompensa, larga um baú e liga `mission_complete_pending`; o cliente mostra o botão "🏁 Encerrar missão" (com confirmação) que dispara esta mensagem. Recusa `pid` fora de `self.players`. |
| `exit_dungeon` | — (saída **individual** pela escada de entrada: exige turno próprio, estar em cima de `stairs_pos` e `saida_permitida` da masmorra; cobra ida+volta de 🍖/💧 da aventura e marca `fora_masmorra`. A masmorra continua para os demais.) |
| `voltar_masmorra` | — (o herói na cidade volta à masmorra assim que a espera zera; senão ele volta sozinho na rodada seguinte) |
| `open_chest` | — |
| `open_door` | `tx`, `ty` — herói abre uma porta adjacente (Chebyshev ≤1). Ação **gratuita** (não gasta movimento/ação). Destranca a(s) sala(s) ligada(s) à porta, revela seu interior e **desperta** os monstros (que passam a perseguir). Salas começam trancadas (exceto a entrada); monstros em sala trancada ficam dormentes e o interior fica oculto pela névoa. **Com mestre**, além de abrir porta, os monstros também acordam por **avistamento** (o herói ganha linha de visão a um deles — `_verificar_avistamento`): o herói que avista acorda a **sala inteira** do monstro (flag `alertado`), narra "⚔️ Combate!" e coloca esses monstros em **Manual** por padrão (o mestre passa a dirigi-los); sem mestre a dormência é só por sala-trancada (byte-idêntica). **Clarividência** (`magia`, `alvoLivre`): alcance = mapa inteiro (mira em qualquer casa, mesmo na névoa — no 3D via `get3DTilePlane`); revela a área, os monstros ali (visibilidade ao vivo por 2 rodadas via `magic_reveal`) e as armadilhas do local, sem abrir a porta nem despertar os monstros. |
| `use_item` | `item_id`, `target_id` opcional; origem da bolsa por padrão. Do cinto: `source:"utility_belt"`, `gear_slot`, `pocket_index`, `belt_token` capturado ao iniciar a ação. |
| `throw_item` | `item_id`, `target_id` (ou `tx`/`ty` para área) — arremessa um consumível (id em `ARREMESSAVEIS`). Origem da bolsa por padrão; do cinto usa os mesmos campos de origem de `use_item`. Ação principal; teste de ataque por DES vs CA; consome o item em acerto E erro; dano de fogo + status `em_chamas_rodadas` (tica 1/rodada). |
| `apagar_chamas` | — (herói em chamas gasta a ação principal para se apagar; única via contra o Fogo Grego, que ignora água). |
| `end_turn` | — |
| `enter_dungeon` | — |
| `buy_item` | `shop_id`, `item_id` |
| `temple_resurrect` | `target_id` — na cidade, multiplayer, um herói vivo paga 30 moedas do próprio ouro para trazer um companheiro morto de volta com 1 HP; não disponível após derrota total. |
| `magia` | `magia_id` (id em `GRIMORIO`) + alvo conforme o tipo: `target_id` (alvo/aliado), `tx`/`ty` (área), `dir:[dx,dy]` (Relâmpago — linha), ou nenhum (auto-centrado). Pedro (mage)/Lewis (cleric) lançam (ação principal). Nenhuma classe usa MP: o custo é um **slot de magia do círculo** (Lewis: `CLERIC_SLOTS`; Pedro: `MAGE_SLOTS_POR_NIVEL`, progressão por nível, resetam por turno via `slots_por_circulo`) + 🍖-1/💧-1. Conjuráveis (`GRIMORIO_IMPLEMENTADAS`): `manto_escuridao`, `visao_escuro`, `bola_fogo`, `relampago`, `raio_congelante`; o resto retorna "em desenvolvimento". O servidor anima dados via broadcast `dice_roll` (dano + d20 de save). |
| `ativar_cancao` | `atributos` (Henrique liga a Canção Heroica com os atributos escolhidos) |
| `desativar_cancao` | — (Henrique encerra a Canção Heroica) |
| `provocacao` | `target_id` (Henrique provoca um inimigo — ação bônus) |
| `cura` | `target_id`, `num_dados` (1–3), `alcance_extra` (0–2) — Lewis cura 1–3d8+INT um aliado; 💧-1/dado, 🍖-1/alcance (1/4/7q) — ação principal |
| `cura_area` | `num_dados` (1–3) — Lewis cura 1–3d8+INT todos os aliados no raio 5; 🍖-4 💧-4 por dado — ação principal |
| `purificacao` | `tipo` (`veneno`/`doenca`/`maldicao`/`petrificacao`), `target_id` — Lewis remove o efeito de um aliado adjacente — ação principal |
| `ressurreicao` | `target_id` — Lewis revive um aliado morto adjacente com 1 HP; 🍖-10 💧-10 — ação principal |
| `imposicao_maos` | `target_id` (Richard cura aliado adjacente — ação principal) |
| `golpe_sagrado` | — (Richard ativa +1d8 sagrado por ataque — ação bônus) |
| `desativar_golpe_sagrado` | — (Richard encerra o Golpe Sagrado) |
| `protetor` | `target_id` (Richard divide o dano de um aliado — ação bônus) |
| `desativar_protetor` | — (Richard encerra o Protetor) |
| `acao_livre_richard` | `habilidade_id` (`regeneracao_divina`/`guerreiro_luz`), `bonus` opcional |
| `criar_armadilha` | `tipo` (id em `ARMADILHAS`), `tx`/`ty` opcionais (default = casa do Luccas), `veneno_id` (só `fosso_envenenado`) — Luccas coloca uma armadilha (ação principal) |
| `desarmar_armadilha` | — (Luccas desarma armadilha na própria casa/adjacente; teste de DES; nat1 dispara nele) |
| `interagir_decor` | `decor_id` — herói adjacente interage com uma decoração: fonte → recebe uma garrafa de água (consome 1 carga); container com loot → abre o painel de loot. Ação livre. |
| `take_from_decor` | `decor_id`, `kind` (`gold`/`item`), `index` — pega ouro/item de uma decoração-container (espelha `take_from_chest`; sem restrição de turno). |
| `scene_npc` | `scene_id`, `npc_id`, `conversation_id` — conversa com um NPC de uma **cena de conversa** da cidade (substitui `tavern_npc`). Concede renome/fato/item; conversa de uso único entra em `scene_conversations_done` (chave `cidade:cena:npc:conversa`) e some do payload. |
| `guild_buy` | `item_id` — compra uma especialização/técnica na **Guilda dos Heróis** (id em `GUILD_CATALOG`). Só na cidade; valida classe, pré-requisito, posse e ouro; grava o save do personagem. |
| `guild_equip` | `slot` (`tecnica`\|`tecnica_exclusiva`), `item_id` (ou `null` p/ desequipar) — equipa uma técnica possuída no 4º slot. Só na cidade. `tecnica_exclusiva` só para mago/clérigo e só técnicas `exclusiva:true`. |
| `usar_tecnica` | `tecnica_id`, `target_id` opcional — ativa a técnica equipada na masmorra (no turno do herói). Valida equipada/fora de recarga/fome-sede; aplica efeito, debita 🍖/💧 e entra em recarga (`round_num + recarga_rodadas`). |
| `usar_instrumento` | `target_id`/`dir` opcionais — o bardo (Henrique) ativa a habilidade do instrumento equipado na **mão do escudo** (`off_hand`; só se `tipo_item=="instrumento"` e `modo:"ativada"`). Nota Cortante (Harpa) exige uma direção ortogonal e atinge todos os monstros na linha até o alcance; paredes/portas bloqueiam sem ricochete. Sucesso em Reflexos reduz o dano à metade (arredondado para baixo, mínimo 1); Harpa Rúnica soma +2 à CD de Reflexos. Acorde Trovejante (Tambor) e Ecos Dolorosos (Sino) são auto-centrados; Sinfonia Heroica (Alaúde) é passiva (sem mensagem — reforça a Canção). Economia de ação: 2 mãos = atacar OU tocar; 1 mão = atacar E tocar; máx. 1 instrumento/turno (`instrumento_usado`, resetado no fim do turno). Custo em 🍖/💧 dos stats derivados; sem recarga. Gaita (Improviso): rola 2d6 numa cascata que invoca a habilidade de outro instrumento; passos que exigem alvo/direção (Nota Cortante ortogonal, Réquiem, Chamado) ficam enfileirados até o cliente responder com `improviso_alvo`. |
| `improviso_alvo` | `target_id` opcional, `dir` opcional — resolve um passo pendente do Improviso (Gaita) que precisa de alvo/direção: mira um monstro (Nota Cortante/Réquiem) ou escolhe direção (Chamado); o servidor processa a fila FIFO (`improviso_pendente`). |
| `claim_role` | `role` (`"master"`\|`"hero"`) — no lobby, um jogador assume/solta o papel de **Mestre** (Modo Mestre Jogador). Mestre: `class_id=None`, não conta no teto de 6 heróis, não escolhe classe. |
| `mestre_set_modo` | `monster_ids[]`, `modo` (`auto`\|`semi`\|`manual`) — o mestre troca o modo de controle de 1+ monstros (base da Seleção em Lote). Só na masmorra. |
| `mestre_set_alvo` | `monster_ids[]`, `target_id` — atribui um alvo (herói) a monstros em modo Semi. |
| `mestre_mover_monstro` | `monster_id`, `dx`, `dy` — Manual: move o monstro da janela 1 passo ortogonal. |
| `mestre_atacar_monstro` | `monster_id`, `target_id` — Manual: o monstro ataca um herói adjacente/no alcance (1×/turno). |
| `mestre_encerrar_monstro` | `monster_id` — Manual: encerra a vez do monstro e libera o laço de iniciativa. |
| `mestre_implantar_reforco` | `monster_type`, `tx`, `ty` — o mestre implanta um monstro da **reserva de reforços** (`master_reinforcements` da masmorra) numa casa livre. Ação livre, a qualquer momento; nasce `alertado`+`manual` e entra na iniciativa da próxima rodada. Só com mestre ativo. |
| `disparar_fala` | `fala_id` — o mestre dispara manualmente uma **fala de NPC** de gatilho `manual` (marcador autorado no editor). Só com mestre ativo; recusa falas não-manuais ou já disparadas. As falas `proximidade`/`sala` disparam sozinhas no `handle_move` (sem/com mestre). |
| `set_lang` | `lang` (`"pt"`\|`"en"`) — idioma desta conexão. Enviada no `onopen` e a cada troca no painel ⚙️. Guardada em `LANG_BY_PID` (módulo, chaveada pelo `pid` do `new_id()`), não na sala — vale antes de entrar em qualquer sala e cobre o Mestre, que sai de `self.players` no `start_game`. O servidor reenvia o estado ao recebê-la, para o log de narração reaparecer traduzido. Valor fora da lista cai em `pt`. |

### Server → Client

**Cintos de consumíveis:** `gear.item1`/`item2` guardam `utility_belt_slots` (4 posições para `cinto_utilidades`, 2 para `cinto_com_bolsos`). Cada pilha é `{item, quantity}` e pode carregar `remaining_items`: lista dos dicionários completos dos demais frascos, de comprimento `quantity - 1`. Sem a lista, os frascos após o atual são completos (compatibilidade com pilhas antigas). Movimentar ou consumir retira só o frasco atual e promove o próximo com suas doses preservadas. `utility_belt_token` identifica a ativação do equipamento; é renovado ao equipar e publicado nos estados da cidade/masmorra. Ações de cinto sem token ou com token antigo são recusadas sem consumir. `move_utility_belt_item {direction, gear_slot, pocket_index, bag_index}` move uma unidade entre bolsa e cinto; `direction` vale `to_belt` ou `to_bag`. Desequipar ou substituir cinto carregado preserva seu conteúdo e emite o aviso localizado de acesso indisponível. Testes: `tools/test_cinto_utilidades*.py`, `tools/test_cinto_utilidades*.js`, `tools/test_cinto_revisao_final.py`.

`lobby_state`, `game_start`, `city_state`, `shop_result`, `enter_dungeon`,
`game_state`, `gm_narration`, `game_over`, `dice_roll`, `animar_result`, `error`,
`decor_loot`, `trap_result`, `fala`, `armadilha_disparo`, `armadilha_impacto`, `armadilha_veneno_impacto`, `item_impacto`, `metamorfose_catalog`

> **`armadilha_disparo`** (`tipo_id`, `pos`, `alvos:[ids]`, `area?`, `area_sala?`, `tick?`) — broadcast público
> de `_avisar_armadilha`, emitido em TODO disparo: `_disparar_armadilha` (alvo único),
> `_aplicar_armadilha_area` (uma vez, com todos do raio), `_verificar_trap_procedural` (buraco) e
> o dano progressivo de `_processar_efeitos_armadilha_turno` (`tick:true`, 1 por alvo por rodada).
> Alimenta som e efeitos visuais no cliente: Dardos Envenenados, Armadilha Incendiária, Mina Terrestre,
> Lâmina Escondida, Guilhotina, Jato de Ácido e Armadilha de Raio Congelante animam o disparo quando a casa está visível. Lâmina Pêndulo calcula um corredor no mapa e anima uma alabarda que sai de uma parede, cruza até a oposta e recua; a extensão respeita a visão do cliente em 2D/3D. Teto Esmagador envia `area_sala:true` e anima a queda nas casas visíveis da sala em 2D/3D. O `trap_result` é privado de quem foi atingido;
> `alvos` diz de quem é o gemido (prisioneiro = `"__prisioneiro__"`).
>
> **`armadilha_impacto`** (`tipo_id`, `alvo_id`, `alvo_tipo`, `pos`, `sucesso`, `aplicada?`) — broadcast
> público com resultado do teste para animações condicionadas; o Buraco publica sucesso e falha,
> e a falha sincroniza o som seco da queda com o início do tombo.
> Fosso com Estacas e Fosso com Estacas Envenenadas tocam `fosso_estacas` no disparo;
> se o veneno da variante envenenada for realmente aplicado, o servidor publica
> `armadilha_veneno_impacto` e o cliente toca o chiado `fosso_veneno` na posição do alvo.
>
> **`item_impacto`** (`item_id`, `pos`, `area`) — broadcast público emitido no ramo de área de
> `_monster_throw_item` (granada do Soldado), antes dos saves. O arremesso de monstro não tem
> `attack_feedback`; o do herói não precisa disto (o `impact` da CombatScene já traz o `item_id`).

> `game_state` inclui `corpses` (cadáveres) e `armadilhas` (colocáveis — ver
> abaixo). `animar_result` traz
> `resultado`/`rolagem`/`d10_dezena`/`d10_unidade`/`chance`/`zona_hostil`/`animados`.
> Cada jogador em `game_state.players[]` também traz `facing` (`[dx,dy]`,
> ausente até o 1º passo — ver "Peão vira na direção do movimento" abaixo).

> **Popup de resultado de armadilha:** ao cair numa armadilha (buraco
> procedural genérico de `self.traps` ou qualquer uma das 8 do catálogo
> `ARMADILHAS`), o servidor manda `trap_result` (`send_to`, nunca broadcast —
> só quem foi afetado recebe) com `nome`/`icone`/`sucesso`/`dano`/`metade`/
> `descricao`/`efeitos_extra`/`tick`. Disparado em 4 pontos:
> `_verificar_trap_procedural` (buraco de sala), `_disparar_armadilha`
> (armadilha de 1 alvo), `_aplicar_armadilha_area` (Mina Terrestre/Nuvem de
> Gás — cada alvo atingido recebe o seu), e `_processar_efeitos_armadilha_turno`
> (tick de dano progressivo da Incendiária, com `tick:true`). Roteamento vai
> pro próprio jogador, ou pro `rescuer_pid` se o alvo for o prisioneiro
> (monstros/servos animados não recebem — sem cliente). Cliente: `game.js`
> abre `#trap-overlay` ~1,2s depois do evento (dá tempo da animação do dado
> terminar), com fila simples pra disparos simultâneos; fecha por botão, clique
> fora, ou Esc; tema de perigo (borda vermelha), com som curto só na falha.

> **História (slides):** os campos `intro`/`outro` da campanha e de cada fase
> aceitam string (legado) **ou** objeto `{slides:[{text?,image?,fit}], audio?}`.
> O servidor normaliza (`_story_norm`/`_story_beat`) e envia o beat
> `{key, slides, audio}` em `game_state.campaign.story` (abertura),
> `city_state.campaign.story` (encerramento) e `game_over.story` (final).
> Imagens/áudios ficam em `assets/story/` (servida) e são referenciados por
> caminho. Cliente: `renderStory` (slideshow layout A + áudio em loop).

> **Portas/salas trancadas:** `game_state.tiles` usa `DOOR=2` nas entradas das
> salas; cada `room` traz `locked` (bool) e `doors` (`[[x,y],…]`). Porta fechada
> bloqueia movimento, LOS e a revelação de névoa do interior. `game_state.revealed`
> lista tiles revelados temporariamente por Clarividência (visibilidade ao vivo de
> monstros, mesmo através de portas fechadas). Servidor: `_is_closed_door`,
> `_blocks_tile`, `_tile_in_locked_room`, `door_rooms`, `magic_reveal`,
> `handle_open_door`; cliente: `GS.doorSets(state)`, `TILE_DOOR`, `drawDoor2D`,
> `doorMeshes` (3D).

> **Objetivos com recompensa:** cada objetivo (`objectives.primary` e cada
> `objectives.secondary[i]`) aceita `xp` (int — total dividido igualmente entre os
> heróis vivos, `max(1, xp//vivos)`) e `reward { gold, items:[{id}] }` (ouro
> dividido; itens largados num único baú via `_spawn_chest` em casa livre perto do
> grupo). Campos ausentes usam o padrão antigo (secundário 50 XP/25 ouro; principal
> sem extra). As recompensas são concedidas ao cumprir o objetivo **principal**
> (`_conceder_objetivo_reward`); a fase só termina quando um herói clica em
> "Encerrar missão" (`encerrar_missao` → `handle_encerrar_missao`).
> `game_state.mission_complete_pending` sinaliza esse estado. No editor: é possível
> **deletar salas** (mantendo ou limpando o chão) e definir XP/recompensa por
> objetivo (principal e secundários).

> **Decorações (`game_state.decorations`):** objetos colocáveis no editor que
> ocupam 1/2/4 casas (footprint `size:[w,h]` + `facing`, giro 90°). Catálogo
> autoritativo `DECOR_TYPES` (server.py, 86 tipos) com `alto`/`pisavel`/`loot_capaz`/
> `special`. Decorações sólidas bloqueiam movimento (entram em `_blocks_tile` via
> `_decor_block_tiles`); as **altas** ocluem a revelação de névoa por raycast
> (`_tall_oclui_caminho` em `_reveal_around`). **Fogueira** (`special:campfire`,
> pisável): 1d4 de fogo a quem entra (heróis e monstros — `_aplicar_fogueira_se_pisar`
> após cada commit de passo). **Fonte** (`special:fountain`): `interagir_decor` dá
> `garrafa_agua` e gasta 1 `charges`. **Moita espinhosa** (`moita_espinhosa`, 1×1, pisável): quem entra sofre 1 de dano físico e, na 1ª moita do turno, perde 1 do movimento (`_apply_thorn_bush_entry_penalty`; começar o turno sobre ela também desconta 1); voo ignora. Empurrão/arrasto não espeta (`aplicar_espinhos=False`). `poco_balde` ocupa 2×2, é alto e sólido;
> fornece água até consumir suas 10 cargas iniciais e usa `poco_balde.png`/`.glb`.
> Cercas da fazenda são módulos 1×1 giráveis com PNG/GLB próprios: `cerca_reta` e
> `cerca_curva` bloqueiam; `cerca_quebrada` permite passagem. `porteira_fechada`
> bloqueia e `porteira_aberta` permite passagem; ambas têm placa PASTO e dobradiças.
> `celeiro_medieval` ocupa 4×4, é alto e bloqueia passagem; tem miniaturas PNG/GLB próprias.
> `galinheiro` ocupa 2×2, é alto e bloqueia passagem; inclui três ninhos frontais
> com ovos e usa miniaturas PNG/GLB próprias.
> `cabana_rustica` ocupa 3×3, é alta e bloqueia passagem; tem troncos, varanda
> coberta e chaminé, com miniaturas PNG/GLB próprias.
> `lago_patos` ocupa 3×3 e bloqueia passagem sem ocluir visão; tem margem rasa
> alinhada ao piso, água, pedras, juncos e patos-reais com formas mais naturais.
> Usa miniaturas PNG/GLB próprias; `DECOR_GLB_GROUND_Y` enterra levemente a borda
> para a superfície da água ficar junto ao plano do tabuleiro.
> **Containers** (`loot:{gold,items}`, qualquer tipo exceto fogueira):
> `interagir_decor`→`decor_loot`→`take_from_decor` (reusa o
> painel de baú via `abrirPainelLoot`; servidor re-envia `decor_loot` após cada take
> p/ atualizar o painel). Footprint resolvido por `_decor_tiles`/`_decor_tiles_at`
> (espelhado no cliente `GS.decorTilesOf` e no editor `decorTilesAt`). Render: 2D
> emoji + 3D geometria procedural (`DECOR_3D`/`decorMeshes`, preparado p/ GLB).
> Decorações `special:wall` ficam na face da parede e não ocupam o chão; `tocha_parede`
> combina `assets/objetos/tocha_parede.png` com o loop GLB de `chama_viva.glb` no 3D.
> `gruta_parede` é um relevo mural 1×1 com imagem de gruta entre rochas; não é portal
> nem entrada jogável e usa PNG/GLB próprios com transparência.
> `braseiro_parede` também usa o loop GLB de `chama_viva.glb`, com tigela suspensa de ferro.
> `pira_chamas` ocupa 1×1, bloqueia passagem e usa GLB com três línguas de fogo animadas sobre lenha carbonizada; é decorativa, sem dano.
> `vitral_templo` é uma decoração de parede com PNG/GLB próprios, arco de pedra e painéis de vidro colorido.
> `gargula_pedra` é uma decoração de parede 1×1, encaixável em qualquer face de parede, com PNG/GLB próprios e sem efeito mecânico.
> `sino_ritualistico` ocupa 1×1, bloqueia passagem e usa miniaturas PNG/GLB próprias, com campânula de bronze e suporte entalhado.
> `estatua_divindade` ocupa 1×1, é alta e sólida, sem efeito mecânico; usa miniaturas PNG/GLB próprias com figura serena em túnica, halo e pedestal de pedra.
> `monte_ossos` é decoração 1×1 baixa e atravessável, sem loot por padrão; usa
> `assets/objetos/monte_ossos.png` no editor/2D e `assets/objetos/monte_ossos.glb` no 3D.
> `bola_corrente` ocupa 1×1 e bloqueia movimento; `grilhoes_parede` é parede e
> não ocupa o chão. Ambas têm miniaturas PNG/GLB próprias.
> `tronco_musgo` ocupa 2×1, pode ser girado, bloqueia movimento e usa miniaturas
> PNG/GLB próprias para o editor/2D e o tabuleiro 3D.
> `moita_espinhosa` ocupa 1×1 e permite passagem; ao entrar, causa 1 de dano
> físico e consome 1 ponto do movimento total na primeira moita do turno
> (criaturas voadoras ignoram os espinhos). `capim_alto` ocupa 1×1 e é
> atravessável. Ambos têm miniaturas PNG/GLB próprias.
> `tronco_podre_fungos` ocupa 2×1, e `tocos_alagados` ocupa 1×1; ambos bloqueiam
> movimento e têm miniaturas PNG/GLB próprias.
> `juncos` ocupa 1×1 e permite passagem; `raizes_torcidas` ocupa 2×1,
> bloqueia passagem e pode ser girada. Ambos têm miniaturas PNG/GLB próprias.
> `estalactites_estalagmites` ocupa 1×1, é alta e bloqueia passagem; `fenda_fumegante`
> ocupa 1×1, é atravessável, puramente visual e tem vapor animado em loop.
> `geiser_lava` ocupa 1×1, permite passagem e aplica 1d8 de fogo no início do turno
> de quem ainda estiver sobre a casa (heróis, monstros, servos e refém; voo ignora).
> No GLB, a cratera fica em repouso por cerca de quatro segundos entre erupções
> curtas de lava; tem miniaturas PNG/GLB próprias.
> `fumarola` ocupa 1×1, permite passagem e, no começo da vez, empurra quem estiver
> sobre ela 1 ou 2 casas a cada intervalo configurável de 1 a 12 rodadas (padrão: 2;
> criaturas voadoras ignoram). O vapor irrompe em rajadas no GLB.
> `cacto_deserto` ocupa 1×1 e bloqueia passagem; `ossos_semi_enterrados` ocupa
> 1×1 e permite passagem. Ambos têm miniaturas PNG/GLB próprias.
> `arbusto_seco` ocupa 1×1 e bloqueia passagem; `capim_amarelado` ocupa 1×1
> e permite passagem. Ambos têm miniaturas PNG/GLB próprias.
> `estatua_soterrada` ocupa 1×1, é baixa, bloqueia passagem e exibe a cabeça
> de uma estátua antiga emergindo da areia; tem miniaturas PNG/GLB próprias.
> `rochas_rachadas` ocupa 1×1, é baixa e permite passagem; reúne placas de
> pedra partidas com fissuras escuras em miniaturas PNG/GLB próprias.
> `rocha_grande` ocupa 2×2, é alta e bloqueia passagem; uma massa única de pedra
> marrom com miniaturas PNG e modelo GLB próprios.
> `ninho_abutres` ocupa 1×1, é baixo e permite passagem; mostra galhos secos,
> ovos e um abutre pousado em miniaturas PNG/GLB próprias.
> `arco_pedra_deserto` ocupa 3×3, é alto e permite passagem; forma um marco de
> arenito erodido com abertura central, cascalho e miniaturas PNG/GLB próprias.
> `pedra_sacrificio` ocupa 2×2, é alta e bloqueia passagem; traz um altar de
> granito gasto, marcas rituais, velas apagadas e uma clareira de musgo e folhas.
> `oasis_pequeno` ocupa 4×4, é alto e bloqueia passagem; reúne água, pedras e
> três palmeiras em uma única miniatura PNG/GLB.
> `acampamento_abandonado` ocupa 2×2, é alto e bloqueia passagem; mostra lona
> rasgada sobre estacas partidas e uma fogueira fria de cinzas, pedra e carvão.
> `ruinas_pedra` ocupa 2×2, é alta e bloqueia passagem; reúne colunas partidas,
> trechos de muralha e escombros em miniaturas PNG/GLB próprias.
> `esqueleto_tiranossauro` ocupa 4×2, é baixo e sólido; mostra um grande fóssil
> tombado com crânio aberto, costelas, membros e cauda em miniaturas PNG/GLB próprias.
> GLBs com terra/areia própria usam `DECOR_GLB_GROUND_Y` no cliente para alinhar
> o plano do terreno ao piso, soterrando a base inferior. O carregamento mantém
> a elevação local do placeholder; o alinhamento acompanha a escala vertical.
> Validação em `validar_dungeon`; catálogo exportado p/ o editor via
> `export_catalog.py`. Testes: `tools/test_decoracoes.py`, `tools/test_decor_roundtrip.py`.

> **Sombra dos objetos (penumbra):** o servidor não revela a casa cuja linha de visão um
> objeto corta — decoração sólida (`_decor_block_tiles`, via `_tem_linha_de_visao`), alta
> (`_tall_oclui_caminho`) ou material opaco (entulho). Antes isso ficava no mesmo preto da
> névoa de sala nunca visitada. Agora `GS.sombraDeObjetos(state, hero, raio)` (puro,
> `src/gameState.js`) devolve as casas de chão no raio do herói com visão livre **só por
> parede/porta** (`hasLineOfSight(..., ignorarObjetos=true)`, espelho de `ignorar_objetos`)
> que a visão completa ou o traçado alto barram — excluindo a própria casa do objeto, sala
> trancada e `revealed` — e qual objeto tapa cada uma (`{tipo:'decor'|'material', id}`).
> `_altoOcluiCaminho` usa `_pyRound`: o `round()` do Python arredonda .5 para o par e o
> traçado tem de bater casa a casa. `game.js`: `_sombraObjetos` (cache por estado+posição+
> raio; vazio para Mestre/mesa de teste) → `_desenharSombraObjetos2D` (logo após a névoa:
> silhueta cinza-azulada hachurada sobre o preto, escurecimento sobre casa já explorada) e
> `_renderSombraObjetos3D` (placas hachuradas em `g3.sombraGroup`, reconstruídas só quando a
> assinatura muda); tooltip "🌑 Visão bloqueada — {objeto} tapa…" (`_sombraTooltipHTML`,
> no 3D via `get3DTilePlane` porque casa nunca vista não tem malha). Mostra o formato do
> chão, nunca o conteúdo. Por herói: cada jogador vê a própria sombra. Teste de paridade
> cliente×servidor: `tools/test_sombra_objetos.py`.
>
> **Três níveis de visão por objeto (sem campo novo — derivado de `pisavel`/`alto`):**
> **livre** (pisável: fogueira, placa, brasa, chão) não bloqueia nada; **baixo** (sólido e
> não alto: barril, mesa, cama, baú, altar, trono, grades, gaiola, lápide, mesa de tortura).
> `grades_prisao` usa `assets/objetos/grades_prisao.png` com fundo transparente no editor/2D
> e `assets/objetos/grades_prisao.glb` no tabuleiro 3D.
> barra o **passo** mas NÃO a visão nem o tiro — antes `_tem_linha_de_visao` bloqueava com
> todo `_decor_block_tiles`, contra o que a doc sempre disse, e o barril fazia sombra de
> coluna; **alto** (coluna, estante, árvore, cripta, casa, lareira, carroça) bloqueia visão e
> tiro, e só ele (mais o entulho) projeta a penumbra. Cliente espelha em `_losBlocks`.
> **Meia cobertura:** `_cobertura_baixa_bonus(atacante, alvo, alvo_tile)` (`COBERTURA_BAIXA_CA`
> = +2) quando a linha supercover do ataque passa por um objeto baixo numa casa
> **intermediária** (corpo a corpo adjacente nunca tem; quem está no ar não dá nem recebe);
> aplicada em `handle_attack`, `_throw_item_alvo` e `_execute_one_monster_attack`, com a
> narração `narracao.cobertura_baixa`. Espelho `GS.coberturaBaixa` alimenta a linha "🛡️ Meia
> cobertura" no tooltip do monstro (2D/3D, `_coberturaTooltipHTML`). Reclassificados:
> `mesa_tortura` baixa, `lareira`/`carroca` altas (`editor_catalog.js` editado à mão nos 3
> campos). Teste: `tools/test_sombra_objetos.py` [2], [6]–[8].
>
> **Visão por objeto (editor):** cada decoração colocada aceita `visao` (`livre`|`baixo`|
> `alto`, `DECOR_VISAO_NIVEIS`); ausente = padrão do tipo (`decor_visao_padrao`: alto →
> alto, pisável → livre, sólido → baixo). `decor_visao(d, meta)` é o ponto único: alimenta
> `_rebuild_decor_index` (`_decor_tall_tiles` ← alto, `_decor_low_tiles` ← baixo, a cobertura
> lê este último) e o payload (`_serializar_decoracoes` manda `visao` e o `alto` **efetivo**,
> então `_losBlocks`/sombra do cliente não mudaram; `GS.coberturaBaixa` lê `visao`). **Só a
> visão muda:** `_decor_block_tiles` (movimento) segue vindo de `pisavel` do tipo. Validado em
> `validar_dungeon`, preservado em `load_authored_dungeon`. Editor (`tools/editor.js`):
> seletor "👁️ visão" no painel da decoração (fora das de parede), `VISAO_NIVEIS` salvo/
> carregado em `buildJSON`/`loadJSON`; "padrão do tipo" apaga o campo. Teste:
> `tools/test_sombra_objetos.py` [9] (inclui sincronia dos níveis editor×servidor).

### Armadilhas colocáveis (`game_state.armadilhas`)
Sistema distinto das `traps` de masmorra. Cada item: `id`, `tipo`, `pos:[x,y]`,
`icone`, `nome`, `visivel`, `ativada`, `aliada` (criador é jogador), `so_luccas`.
Tipos em `ARMADILHAS` (server.py): `buraco`, `armadilha_urso`, `fosso_estacas`,
`rede`, `armadilha_incendiaria`, `mina_terrestre`, `fosso_envenenado`, `nuvem_gas`.
Save de Reflexos (gás = Fortitude); persistência/visibilidade por tipo; dano
progressivo (incendiária) tica em `_processar_efeitos_armadilha_turno`; `fosso_envenenado`
reusa `_aplicar_veneno`; `nuvem_gas` reduz CON via `_reduzir_con_temporario`.
Na falha do save do `buraco`, o servidor continua aplicando `perder_movimento`; o
cliente anima a queda não letal e o retorno do peão em 2D/3D via
`CombatScene.startFall`/`fallPoseFor`, sem alterar HP nem morte. O servidor também
publica `armadilha_impacto`; quando o save falha, o cliente toca `buraco_queda`
sincronizado à descida, sem afetar o som de outras quedas.
No `fosso`, a falha aplica o estado `fosso_oculto` e publica `armadilha_disparo`
antes do `trap_result` privado. O cliente usa `CombatScene.startPitFall` por 900 ms:
o peão tomba e some; depois os filtros existentes mantêm a peça oculta até o
servidor limpar `fosso_oculto` no fim da rodada perdida. O cliente registra o
início por herói para `armadilha_disparo` e `trap_result` não reiniciarem a queda
quando o popup chega depois dos 900 ms; libera esse registro quando o estado do
servidor remover `fosso_oculto`.
Na queda do fosso, `CombatScene` conserva a pose terminal invisível até
`endPitFall`, sem restaurar materiais ao expirar os 900 ms. A trava visual só
é liberada por um `gameState` que remova `fosso_oculto` após sua confirmação;
o resultado privado não consulta o estado antigo para liberar/reiniciar a
queda. Em 3D a raiz inteira é ocultada a cada frame ao terminar a descida,
incluindo base e acessórios, independentemente do cache de entidades. Em 2D
a trava também cobre o intervalo entre o evento e o estado autoritativo.
Nos `fosso_estacas` e `fosso_envenenado`, o cliente anima a abertura do piso e a
subida das estacas em 2D/3D; o fosso envenenado acrescenta brilho verde nas
pontas e névoa tóxica breve. Um aviso público de impacto inicia a queda curta do
alvo apenas quando ele falha no save. Os efeitos mecânicos existentes não mudam.
Na `armadilha_urso`, as mandíbulas fecham no alvo se ele falhar, ou ao lado dele
se escapar; faíscas e a reação curta de queda comunicam o impacto sem prender
visualmente o peão após o fim do disparo.
Na `rede`, a malha sobe e se abre antes de cair sobre o alvo; na falha, fecha-se
ao redor do peão, e no sucesso cai vazia para o lado. A perda da rodada continua
sendo aplicada pelo fluxo existente da armadilha. O disparo público também toca
`rede` no impacto da animação (240 ms): estalo da mola, sopro da malha e cordas
tensionando; o som toca mesmo quando o alvo passa no teste, pois representa o
mecanismo disparando.
No `bau_engolidor`, a transição autoritativa de `bau_engolido:false` para `true`
no `game_state` toca `bau_engolir` na posição do baú: abocanhada, sucção curta e
gole grave. O som é deduplicado por herói, compartilhado pela sala via as regras
de audibilidade do SoundBank, e não substitui a dor por perda de HP.
No `teto_esmagador`, o cliente toca `teto_esmagador` no impacto da animação
(240 ms): a queda de rocha do ataque do Elemental de Pedra seguida por uma
batida seca grave, posicionada no instante em que o teto chega ao chão.

---

**Chão Ilusório (`chao_illusorio`):** armadilha autorada somente em uma casa de
ponte com `FLOOR` diretamente abaixo e pelo menos 1 nível de desnível. Guarda
`ponte_id` e `pos`; Reflexos (CD padrão 14) permite atravessar. Na falha, usa a
tabela de dano de queda do desnível real, remove a tábua da ponte naquela casa
e coloca a criatura no piso inferior. O sucesso revela, mas mantém a armadilha
ativa para as próximas passagens. O servidor serializa as casas ainda existentes
da ponte em `pontes[].tiles`; cliente e pathfinding usam essa lista para mostrar
e bloquear corretamente a parte colapsada. Editor e `validar_dungeon` verificam
ponte vinculada, tipo de piso e altura inferior.

**Parede acompanha a elevação do terreno (2026-10-04):** no 3D, cada parede sobe sozinha até o
chão mais alto das 8 casas ao redor (`nivelParede3D` em `game.js`; chão/porta, chão afundado não
rebaixa) — antes um platô de nível alto passava por cima do próprio muro. A faixa de terreno é
−1 a +40; cada nível continua usando o passo visual existente de 0,24 no 3D. O limite de voo (10)
é independente. O autor fixa a altura de uma parede com a ferramenta **altura** do editor pintando
sobre ela: 0 a +40 grava em
`alturas_parede` (`"x,y"` → nível, só parede), −1 ou apagar volta ao automático; selo "▮n" no mapa
do editor. O campo é **só visual** (as regras seguem lendo `elevacoes`): validado em
`validar_dungeon`, carregado em `load_authored_dungeon`, enviado no `game_state` (o 0 vai junto —
é ele que trava a parede ao lado de um platô) e na foto da masmorra. Escala e posição da malha são
aplicadas antes de `_prepararTileProxy` (que congela a matriz). Acompanham: colunas de canto
(crescem com a parede mais alta do bloco), rodapés, tochas e enfeites de parede (`elevacaoEnfeiteParede3D`: chão à frente, sem passar da
parede). Junto: a lápide do monstro passou `x,y` ao `obterFig` (ficava enterrada no platô, a do
herói já assentava) e o anel/partículas da morte nascem no topo do terreno. A escada, a bandeira
de saída e os anéis de início dos heróis assentam no topo da casa (`topoSuperficie3D`: platô ou
ponte). Testes: `tools/test_altura_parede.py`,
`tools/test_altura_parede_cliente.js`.

**Porta só onde o autor criou (2026-10-07):** o `buildWallDetails` punha arco de pedras, pilares, folha de porta de madeira e dobradiças em toda casa de chão com parede dos dois lados ao lado de uma sala (resto da era procedural), sem olhar as portas do mapa — 53 no Calabouço da Morte. Removido: porta é só a casa `DOOR` (`doorMeshes`). Teste: `tools/test_porta_so_onde_autor.js`.

## Classes de Personagem

`warrior`, `mage`, `rogue`, `cleric`, `ranger`, `paladin` — cada uma com 3 habilidades únicas.

---

## Renderização 3D (Three.js)

### Técnicas implementadas
- **Outline escuro** — clone BackSide escalonado ×1.075 (`isOutline:true`)
- **Blob shadow** — `CircleGeometry` com `depthWrite:false`, achatado em Z (`isGroundDecal:true`)
- **Halo pulsante** — `TorusGeometry` (`isPulseRing:true`) + `PointLight` (`isHaloLight:true`), animados em `startLoop3D`
- **OrbitControls** — esq: orbitar, dir: pan, scroll: zoom; `enableDamping=true` requer `controls.update()` a cada frame
- **Reset de câmera** — botão `⌂` + tecla `R`; vista isométrica SW 225°/52°

### Limites da câmera
```javascript
controls.minZoom        = 0.28;
controls.maxZoom        = 4.0;
controls.minPolarAngle  = 8  * Math.PI / 180;   // nunca abaixo do tabuleiro
controls.maxPolarAngle  = 82 * Math.PI / 180;
```

### Drag guard
`_orbitDragMoved` — previne clique em tile após arrastar câmera.

---

## Como Rodar

```bat
iniciar.bat          # encerra porta antiga, sobe o servidor, abre index.html no browser
```

Ou manualmente:
```bash
python server.py                  # serve PÁGINA + WebSocket em 0.0.0.0:8765
# abrir http://localhost:8765/index.html
```

> **Porta única:** `server.py` serve os arquivos do cliente (index.html, game.js,
> `src/`, `assets/`) na MESMA porta 8765 via `process_request` (allow-list +
> proteção contra path traversal) — não há mais `http.server` separado. Assim um
> único túnel HTTPS cobre página + `wss` no mesmo domínio (sem mixed content). O
> cliente infere o endereço de onde a página foi servida (`defaultServerUrl()` em
> `game.js`): `wss://<host>` se https, senão `ws://localhost:8765`.

Para jogar pela **internet** (link único para os amigos):
```bat
iniciar-online.bat   # ou: python online.py
```
Sobe o servidor + um túnel HTTPS (`cloudflared` recomendado, ou `ngrok http 8765`)
e imprime UM link `https://…/index.html` para compartilhar.

---

## Estado do Projeto (2026-05-26)

- Jogo totalmente funcional: mapa procedural, fog of war, combate, habilidades, baús, armadilhas, XP/level up, narração do GM
- Visualização 2D (canvas) e 3D (Three.js) com alternância em tempo real
- Peões 3D com geometrias custom, outline, sombra blob, halo pulsante para turno ativo
- OrbitControls com limites, reset de câmera (botão + tecla R)
- Sistema de cidade e loja de itens entre dungeons

> **Ficha na cidade (autoritativa):** cada card de herói em `screen-city` mostra a
> foto do rosto (3:4, `HERO_PORTRAIT_PATHS`). Clicar abre `abrirFichaCidade(pid)` —
> painel lateral ESQUERDO deslizante (`#ficha-cidade-panel`) com atributos
> (`renderConteudoAtributosFichaJogo`) + equipamento (8 slots de `player.gear`) +
> inventário (`player.bag`). O próprio herói equipa/desequipa (botão/clique) e
> organiza a bolsa por **arrastar-e-soltar** (reordenar; arrastar item p/ um slot
> equipa; arrastar do slot p/ a bolsa desequipa); outros heróis abrem em
> **só-leitura**. Usa o modelo AUTORITATIVO do servidor:
> `equip_from_bag`/`equip_offhand`/`unequip`/`reorder_bag`, com broadcast ciente da
> fase (`push_state_or_city` → `broadcast_city_state` na cidade,
> `push_state`/`game_state` na masmorra). Cliente: `_updateCityHeroBar` (fotos +
> clique), `renderFichaCidadeBody`, `_refreshFichaCidadePanel` (re-render ao chegar
> `city_state`), `_fcDropOnGear`/`_fcDropOnBag` (drag-and-drop). Teste do servidor:
> `tools/test_ficha_cidade.py`.

> **Jogos salvos — continuar de onde parou (2026-10-01):** não existe mais jogo rápido sem
> salvamento no cliente: a tela inicial pede apelido + servidor + senha pelo botão "Acessar minha conta", e os
> jogos ficam na conta ("Meus Jogos"). O handler `create_room` segue no servidor (editor e
> testes o usam). **Continuar pula a escolha de herói:** em `add_player`, conta com personagem
> vinculado (`_classe_vinculada`) vai para `_continuar_jogo_salvo`, que copia as magias salvas
> para a casca (senão o `start_game` recusaria mago/clérigo) e chama `select_class(...,
> anunciar=False)`; no jogo **solo** (`_jogo_salvo_solo`: 1 membro ativo, sem Mestre) manda
> `lobby_state` com `auto_start:true` (o cliente aprende pid e código e `handleLobby` retorna
> sem desenhar) e inicia. Em grupo, o lobby é sala de espera com os heróis já marcados.
> **Qualquer membro abre; os outros entram pelo Continuar:** `load_savegame` primeiro procura
> `sala_aberta_do_jogo_salvo` (SAVEGAMES_IN_USE + alguém conectado) e, se houver,
> `entrar_em_jogo_salvo_aberto`: lobby → `add_player`; quem caiu → `religar_heroi`/
> `religar_mestre` (extraídos do `rejoin`, que os usa); partida na cidade →
> `entrar_com_jogo_em_andamento` (ficha por `_montar_heroi`, extraído do `start_game`); grupo
> na masmorra → chega com `fora_masmorra={"rodadas_restantes":0}` e desce na próxima rodada.
> Ao religar, o pid da conexão vira o antigo e **`ACCOUNTS_ONLINE` acompanha** (senão o
> `finally` não libera a conta). Sem anfitrião conectado, quem chega assume
> (`_assumir_anfitriao_se_vago`), exceto quando o anfitrião é o Mestre. `try_open_savegame_room`
> desliga e remove a sala velha sem ninguém do mesmo jogo. `city_state` traz `code` (quem cai
> direto na cidade grava a sessão de reconexão por ele). **A ficha só é salva na cidade:** com o
> grupo na masmorra, `_checkpoint_savegame` não grava a ficha de quem está lá dentro (só de quem
> está `fora_masmorra`), senão loot de masmorra inacabada ficava salvo e dava para repetir o
> saque. A masmorra em si é salva pela **foto** (ver abaixo), que guarda sala e fichas juntas.
> **Jogador NOVO com a partida em andamento:** `join_room` num jogo salvo em `city`/`playing`
> passa por `entrar_com_jogo_em_andamento`; sem personagem, vai para a sala de espera
> `GameRoom.aguardando` (FORA de `players`/`connections`: não recebe `game_state`/`city_state`,
> que o arrancariam da tela de heróis; `send_to` o alcança pelo `ws` guardado lá). Recebe um
> `lobby_state` só dele (`_enviar_escolha_tardia`: `entrada_tardia`, `host:null`,
> `taken_classes` = heróis na sala + membros ausentes). `select_class`/`handle_set_known_spells`
> operam sobre a casca do lobby OU da espera; com a classe (e 2 magias p/ mago/clérigo)
> `_tentar_entrada_tardia` o leva para dentro. Com votação, espera com `classe_pedida`; a
> aprovação em `handle_campaign_vote` o faz entrar, e o voto só manda `lobby_state` com
> `phase=="lobby"`. O `finally` da conexão limpa a espera. Cliente: `handleLobby` soma
> `taken_classes` e mostra `ui.selecao.entrada_tardia`; `csUpdateLobbyBar` esconde seletor de
> masmorra e botão de Mestre. Spec em
> `docs/superpowers/specs/2026-10-01-salvar-aventura-design.md`. Teste:
> `tools/test_continuar_jogo.py` (66, pelo `server.handler` real).

> **Foto da masmorra — continuar DENTRO da masmorra (Etapa 2, 2026-10-01):** a cada virada de
> rodada (`_advance_initiative` → `_gravar_foto_rodada`, via `_isolar_sync`) o jogo salvo ganha
> `dungeon_snapshot`: os campos de sala + a ficha inteira de cada herói por `class_id` + o mapa
> `pids` (pid desta sessão → classe). **Não grava** fora de jogo salvo, na sala de teste, fora
> de `playing`, com janela pendente (`_FOTO_JANELAS` + `improviso_pendente`) nem sem nenhum
> herói conectado (senão a masmorra seguiria girando e gravaria o grupo fora do tabuleiro).
> **Formato:** `foto_empacotar` = JSON etiquetado (`$set`/`$tup`/`$map`, `_foto_codificar`;
> tipo desconhecido levanta `FotoNaoSerializavel`) → gzip → base64; o resumo (`onde`,
> `rodada`, `masmorra`, `masmorra_nome`, `versao`, `gravado_em`) fica FORA da compressão para
> "Meus Jogos" ler sem abrir (`_resumo_foto` em `list_savegames`). ~16–42 KB por foto.
> **Campo novo em `GameRoom` precisa entrar em `FOTO_SALA_CATEGORIAS`** (foto / foto_pid /
> herois / jogo_salvo / derivado / conexao / janela / efemero / constante / teste) — o
> `test_salvar_masmorra` [2] varre a classe e fica vermelho com atributo sem categoria. Dict
> chaveado por pid vai em `foto_pid`; índice reconstruível é `derivado` (os `_rebuild_*`).
> **Ids:** `new_id()` recomeça a cada boot e é compartilhado por jogadores/monstros/baús, então
> `foto_renomear_ids` troca todo `id_N` (inclusive dentro de texto composto e em chaves) — pid
> antigo de herói vira o pid da conexão nova; o resto, id novo. **Retomar:**
> `try_open_savegame_room` pendura a foto em `_foto_pendente`; `start_game` despacha pelo
> `onde`. `"masmorra"` → `_retomar_masmorra`: confere a grade da masmorra autorada
> (`_foto_conferir_arquivo`; mudou/sumiu → `_descartar_foto` + `erro.foto_masmorra_descartada`),
> aplica a sala (`_foto_aplicar_sala`), sobrepõe a ficha mantendo `id`/`name`/`slot`, monta a
> iniciativa e entra pelo MESMO caminho da entrada normal (`enter_dungeon` + 3 s de transição,
> `_finalizar_intro_masmorra(..., retomada=True)`), narrando só `narracao.a_aventura_continua`
> (o `gm_log` não é salvo). **Grupo incompleto:** basta 1 herói da foto presente; o ausente
> entra como quem caiu (`connected=False`, `[-1,-1]`, conta em `account_by_pid`, casa em
> `_pos_retomada`) e `religar_heroi` o devolve à casa (`_casa_livre_retomada` se ocupada); quem
> não estava na foto chega com `fora_masmorra` 0. Nenhum da foto presente → grupo na cidade,
> foto guardada. **Quem cai na masmorra** guarda a casa em `_pos_ao_cair` (usada só pela
> retomada; o rejoin na mesma sessão a descarta e segue pela escada). **Cidade com masmorra
> aberta:** `_voltar_para_cidade` com `dungeon_generated` grava `onde="cidade_com_masmorra"`
> (`_gravar_foto_cidade`, só a sala); no Continuar, `_restaurar_masmorra_aberta` a devolve à
> memória e a próxima entrada a retoma. **A foto sai** (`_apagar_foto`) ao voltar à cidade com
> a masmorra encerrada, no `end_game`, ao emendar etapa e ao partir para outro destino.
> **Cliente:** cartão de "Meus Jogos" com "🗡️ Campo de Treinamento — rodada 4"
> (`_ondeParouHTML`); "💾 Salvar e sair" no ⚙️ (só com `tem_jogo_salvo`) → `salvar_e_sair` →
> `salvo_para_sair` → o cliente fecha a sessão e refaz o login com a senha da aba (código de
> login `em_uso` para tentar de novo enquanto a conexão velha fecha); herói que caiu com
> "⏳ aguardando {nome}…". **Aviso "💾 Progresso salvo":** `_avisar_salvo(onde)` faz broadcast
> `{type:"saved", where}` (numa tarefa à parte, porque as gravações são síncronas) no fim do
> `_checkpoint_savegame` **só com a sala na cidade** (na masmorra o checkpoint não guarda quem
> está lá dentro) e na **1ª** foto de cada visita à masmorra (`_ultima_foto is None`; na
> retomada ela já vem preenchida). O cliente mostra o selo `#aviso-salvo` no alto da tela, à
> parte do `#toast`; o da cidade (compras) no máximo 1 a cada 30 s, o da masmorra sempre.
> Provado no navegador com o servidor REINICIADO entre salvar e
> continuar: rodada, casa, PV, ouro, bolsa, 14 monstros, item no chão, baús e névoa idênticos.
> Teste: `tools/test_salvar_masmorra.py` (230; a seção [6] passa pelo `server.handler` real).
> Na conta, "Meus Jogos" separa saves em Solo/Multiplayer. Jogos novos persistem `play_mode`
> (seleção Solo/Multiplayer no formulário; Mestre força Multiplayer); saves antigos sem esse
> campo inferem Multiplayer por Mestre ou mais de uma conta vinculada, senão Solo. O botão de
> conta leva à lista privada após login; a lista mostra carregamento/erro com nova tentativa e
> saves encerrados informam o motivo e desabilitam "Continuar", deixando criar continuação.
> **Correção de visibilidade (2026-10-01):** a lista dentro de `.connect-panel` encolhia até
> altura 0 quando o formulário excedia a tela. Agora `.savegames-library` ocupa a área livre,
> separada de `.savegames-actions` (rolagem própria); listas em duas colunas no desktop e
> acima do formulário em telas pequenas. `index.html` atualiza o cache-buster do CSS.
> Reproduzido no navegador (0 px antes, 572 px após, viewport 1280×720); verificado também
> em 390×844, Continuar solo até a cidade e duas contas retomando o mesmo multiplayer,
> usando dados isolados na porta 8777, sem erros no console.

> **Capítulos e pontos de salvamento (2026-10-05):** cada jogo salvo é UM cartão em "Meus Jogos",
> com abas Solo | Multiplayer (`GS.agruparJogos`, puro; aba em `localStorage["lfh_aba_jogos"]`) e,
> em Multiplayer, "Que eu hospedo"/"Que eu participo". O documento do jogo segue sendo o estado vivo
> e guarda só o ÍNDICE `capitulos[].pontos[]`; o conteúdo de cada ponto vai para a coleção `pontos`
> da loja (`<sid>_<ptid>`, pasta `savegame_points/`) com a cópia de `CAMPOS_DO_PONTO`. Automáticos
> (`registrar_ponto(..., "auto", rotulo=…)`) na 1ª foto de cada visita à masmorra, a cada
> `PONTO_AUTO_RODADAS` (5) rodadas (no MESMO write da foto), ao voltar à cidade e no "Salvar e
> sair"; ficam os 3 mais recentes por capítulo. Manuais: `salvar_ponto {nome}` ("💾 Salvar agora"
> no ⚙️, resposta `ponto_salvo`), teto 10 por capítulo. Carregar/apagar ponto e "Novo capítulo" (o
> antigo "Continuar em sequência", que criava outro cartão) só pelo cartão, com o jogo FECHADO
> (`SAVEGAMES_IN_USE`) e só pelo anfitrião (`_anfitriao_do_jogo`: Mestre se houver, senão o dono);
> carregar guarda o estado substituído como "Antes de carregar" (`preservar` impede a rotação de
> apagar o ponto carregado). Arquivar é por conta (`arquivado_por`). Documento gravado nunca leva
> `T(...)`: o automático guarda um `rotulo` traduzido no cliente (`ui.save.ponto.<rotulo>`).
> Migração: `garantir_capitulos` (em `ensure_campaign_schema`) dá capítulo 1 + ponto "migrado" a
> jogo antigo; no boot, `migrar_continuacoes_para_capitulos` funde continuações antigas no jogo de
> origem — segue cadeias até a raiz, isola cada jogo num try/except (calcula tudo antes de gravar)
> e é idempotente mesmo após queda no meio. **Mestre fora da mesa (2026-10-06):** qualquer
participante abre um jogo com Mestre; sem ele, os monstros ficam na IA e um jogador é o anfitrião.
O Mestre que cai na cidade/masmorra passa o anfitrião a um jogador conectado
(`_mestre_saiu_passar_anfitriao`); ao voltar (`religar_mestre`) ou ao chegar a um jogo aberto sem
ele (`entrar_mestre_em_andamento`, ou o `add_player` no lobby) reassume Mestre e anfitrião. O
`game_start` enviado só a ele leva `pid` — fora do lobby o Mestre não está em `players[]` e o
cliente não acharia o próprio pid pelo nome. "Encerrar" encerra o capítulo: qualquer participante
(o Mestre inclusive) abre o próximo, e o jogo segue do Mestre; jogo encerrado não volta por ponto
de salvamento. Gerenciar pontos/capítulos com o jogo fechado continua só do Mestre. Teste:
`tools/test_mestre_substituto.py` (25). Fora de escopo: a Guilda segue por classe, sem voltar
> no tempo. Spec/plano em `docs/superpowers/{specs,plans}/2026-10-05-saves-organizados*`. Testes:
> `tools/test_pontos_salvamento.py` (79) e `tools/test_pontos_salvamento_cliente.js` (17).

> **Solo com grupo (2026-10-01):** no jogo salvo **Solo**, a tela de seleção marca de 1 a 6
> classes (`select_party`, só no lobby de um Solo novo, sem Mestre, só com a conta do dono;
> `lobby_state.grupo_solo` liga o modo) e o jogador controla todos. **Heróis por procuração:** o
> 1º herói tem o pid da conexão; os outros são entradas completas de `self.players` com pid
> próprio e `controlador` = pid da conexão — iniciativa, XP (já dividido pelos vivos), derrota,
> checkpoint e foto seguem sem mudança. **Quem age:** `GameRoom.heroi_da_acao(conexão, msg)`,
> chamado no `handler` antes do despacho: `msg.heroi` de herói desta conexão → ele; senão um
> extra desta conexão na vez → ele; senão a própria conexão. `heroi` de outro controlador →
> `erro.esse_heroi_nao_e_seu`. `MENSAGENS_DA_CONEXAO` (+ prefixos `mestre_`/`teste_`/`upload_`/
> `save_`/`load_`) nunca são traduzidas. Enquanto despacha, `pid` aponta para o herói e
> `_traduzido` guarda a conexão (restaurada no topo do laço e no `finally`). Checagem de
> anfitrião: `_eh_anfitriao(pid)` — **não a reescreva como `pid == self.host_pid`**: a forma com
> `in` existe para uma troca em massa desse padrão não a fazer chamar a si mesma. **Resposta:**
> `send_to(herói extra)` entrega na conexão do controlador, no idioma dela, e acrescenta
> `heroi: <pid do extra>` à mensagem — é assim que o cliente sabe de quem é um aviso privado.
> **Jogo salvo:** `members[conta]` mantém `class_id` (principal) e ganha `class_ids` (o grupo),
> gravados no `start_game` (`_vincular_grupo_solo`, também num Solo de 1 classe montado pelo
> `select_party`); `_continuar_jogo_salvo` recria as cascas (`_recriar_grupo_solo`, magias da
> ficha) e a foto mantém o `controlador` novo (`manter` em `_retomar_masmorra`). **Solo com
> grupo é fechado** (`_dono_grupo_solo`): outra conta não entra, e o `rejoin` ignora herói com
> `controlador` (senão quem soubesse o código tomava o "Pedro" pelo nome); Solo de 1 herói
> continua aceitando quem chega. **Queda/volta:** o `finally` derruba todos os heróis da conexão
> (extras primeiro, para o anfitrião não passar a um extra); `religar_heroi` religa os extras
> (`_religar_extras`) e põe cada um numa casa livre — `_casa_livre_retomada` procura em anéis
> uma casa de chão sem herói, monstro, baú ou objeto sólido. **Escada:** o herói que sai só
> espera — `_em_cidade` e o `skip` do `push_state` usam `_conexao_toda_fora` (todos os heróis da
> conexão fora); `_reentrar_masmorra` só manda `enter_dungeon` se a conexão inteira estava fora.
> **Cliente:** `connPid` = conexão; `myPid` = **herói em foco** (pula sozinho para o herói meu na
> vez, uma vez por turno; `GS.focarHeroi(pid)` troca à mão e emite `focoHeroi {pid, auto}`);
> `GS.meusHerois`/`temGrupo`/`ehMeuHeroi`/`cascaDaClasse`; com grupo, `send` acrescenta
> `heroi: myPid`; a sessão grava o `connPid`. Aviso que pede resposta (`_AVISOS_COM_RESPOSTA`:
> escolha de magia, Sorte, chamas, consentimentos de teleporte/metamorfose, posicionamento de
> ciclones) chegando com `heroi` de outro herói meu foca esse herói antes; enviada a resposta
> (`_RESPOSTAS_DE_AVISO`), o próximo `game_state` devolve o foco a quem estava (`_voltaFoco`,
> `focoHeroi {volta:true}`) — exceto se chegou outro aviso da fila, se o servidor recusou a
> resposta (`error`), se a vez trocou ou se o jogador trocou de herói à mão. Botões de anfitrião
> comparam `host` com a conexão (`GS.souAnfitriao(host)`), nunca com `myPid`. Cartões do HUD/
> cidade de heróis meus focam o herói (2º clique abre a ficha); `focoHeroi` centraliza a câmera;
> visão compartilhada sempre ligada no grupo. Seleção: `_csAlternarNoGrupo` (botão vira
> "Adicionar/Remover do grupo"), magias por herói via `setKnownSpells(ids, GS.cascaDaClasse(cls))`.
> Provado no navegador (servidor isolado na 8779): grupo de 3 montado pela interface, ficha do
> extra na cidade, vez passando entre os 3 com o foco junto, ação livre de outro herói fora da vez,
> Salvar e sair → Continuar de volta à masmorra com casas e PV idênticos. A escolha Solo/Multiplayer
> (`play_mode`) foi trazida do trabalho em andamento do autor só no trecho do servidor. Spec/plano
> em `docs/superpowers/{specs,plans}/2026-10-01-solo-com-grupo*`. Testes:
> `tools/test_solo_grupo.py` (72) e `tools/test_solo_grupo_cliente.js` (52).
>
> **XP e sons do grupo (2026-10-02):** o aviso de XP ao matar um monstro soma TODOS os meus heróis
> (`_ganhosXpMeusHerois`, "✨ +25 XP para cada um dos 3 heróis"), medindo em xp acumulado
> (`_xpAcumulado`, com `XP_POR_NIVEL_CLIENTE` = espelho do servidor) — antes a subida de nível
> zerava a diferença. Subir de nível de qualquer herói meu avisa (`_avisarNiveisDoGrupo`). O diff de
> sons (`_capturarSonsDeEstado`) descarta o `me` anterior quando o foco troca de herói (senão trocar
> o foco tocava equipar/moedas/nível) e toca "sua vez" quando a vez passa de um herói meu a outro.
> **Destaque do herói da vez** (todos com grupo, exceto onde dito): faixa central "Vez de Pedro" com
> o retrato quando a vez passa a um herói meu (`_destacarVezDeEstado`/`_mostrarBannerVez`,
> `#banner-vez`); cartão `.pcard.vez` com moldura dourada pulsante e rolagem até ele (em todos os
> modos); seta dourada sobre o peão da vez — no 3D um sprite PERMANENTE `g3.setaVez`, movido como a
> `haloLight` (não nasce/morre por turno), no 2D `_desenharSetaVez2D` (todos os modos, fora a mesa de
> teste); e o retrato do HUD ganha nome + "na vez"/"fora da vez — só ações livres"
> (`#my-hero-portrait-faixa`, moldura dourada quando na vez).
>
> **Escolha de magia na subida de nível com grupo (2026-10-06):** o XP é dividido num laço só,
> então mago e clérigo da mesma conexão sobem juntos — e o cliente tem UM painel de escolha
> (`#overlay-escolha-magia`): o 2º `spell_pick_prompt` apagava o 1º e o herói do aviso perdido
> ficava preso ("escolha sua nova magia antes de encerrar o turno", sem painel). Agora
> `_enviar_spell_pick_prompt` manda só o aviso do **1º herói pendente da conexão**
> (`_proximo_spell_pick`, na ordem do grupo) e `handle_escolher_magia_nivel` manda o do próximo
> quando a fila dele termina; a subida de nível só avisa se o herói que subiu é o próximo. O aviso
> leva `heroi` e `heroi_nome` (título "Lewis — SUBIU DE NÍVEL") e a resposta vai com o herói do
> **aviso**, não o do foco (`GS.escolherMagiaNivel(id, heroi)`). O aviso é reenviado no início do
> turno de quem tem escolha pendente e quando o `end_turn` é recusado por ela — recusa que agora
> vem ANTES da Dor Constante e dos eventos de fim de turno (antes cada tentativa cobrava). A volta
> do foco também roda no `city_state`. **Mesa de teste do editor:** os heróis-teste não têm conexão
> e o painel deles chega ao Mestre; `_dono_do_painel` (Mestre para `test_hero`, senão a conexão)
> põe todos na mesma fila, e a resposta vai por `teste_escolher_magia_nivel {hero_id, magia_id}`
> (`handle_teste_escolher_magia_nivel`, só o Mestre da sala descartável) — antes a escolha se
> perdia em silêncio, porque a mensagem comum caía na conexão do Mestre. O cliente escolhe o
> caminho em `GS.escolherMagiaNivel` (herói alheio + `test_mode` + sou o Mestre). Testes:
> `tools/test_escolha_magia_grupo.py` (23) e `tools/test_escolha_magia_grupo_cliente.js` (15).

> **Cidade × masmorra são exclusivos no cliente:** o handler de `city_state`
> (`gameState.js`) limpa `gameState = null` (espelhando o `enter_dungeon`, que limpa
> `cityState`). Sem isso, leitores que preferem `gameState` — como o modal de
> inventário (`InventoryModal._currentPlayer`, que lê `GS.gameState` e só cai para
> `GS.cityState`) — mostravam o paperdoll/bolsa **congelados** da última masmorra na
> cidade (bug: armadura recém-comprada aparecia ao vender, que lê `cityState`, mas
> não no boneco). Ao adicionar um novo leitor de estado, lembre que na cidade só o
> `cityState` está preenchido e na masmorra só o `gameState`.

> **Aquisição de itens — bolsa-primeiro (`_route_acquired_item`):** todo item
> adquirido por compra OU loot passa por `_route_acquired_item(p, item)` (server.py),
> que retorna `'bag' | 'equipped' | 'full'`: (1) bolsa com espaço → **bolsa** (NÃO
> auto-equipa, mesmo com o slot livre); (2) bolsa cheia + slot correspondente livre e
> compatível → **resgate-equipa** (`_rescue_equip`, que espelha `handle_equip_from_bag`
> — aplica `_apply_gear_effect` e, p/ arma, sincroniza a cópia de combate
> `p["weapon"]`); (3) bolsa cheia + slots ocupados/inequipável → `'full'` (compra
> estorna ouro; loot fica no baú/container). `_free_equip_slot_for` mapeia a categoria
> (`_slot_category_for_item`) ao slot livre e respeita restrição de classe e conflito
> de arma de 2 mãos × escudo/2ª arma. **Exceções:** munição (empilhamento próprio em
> off_hand/bolsa) e consumíveis (categoria `bag` → só a bolsa) não usam o passo 2.
> Pontos de chamada: `handle_shop_buy` (arma/armadura/escudo/anel/acessório/provisão),
> `handle_take_from_chest`, `handle_take_from_decor`. Como comprar não auto-equipa
> mais no slot vazio, o bloqueio pré-compra de arma-2-mãos × escudo foi removido (o
> item vai pra bolsa; o conflito é validado só ao equipar). Teste do servidor:
> `tools/test_roteamento_itens.py`.

> **Autoequipar flechas:** preferência por personagem `auto_equip_arrows_enabled`
> e `auto_equip_arrows_order`, incluída em `_DURABLE_FIELDS` e no snapshot da ficha.
> O jogador configura no modal de inventário (cidade ou masmorra) se deseja ativar
> e a ordem entre flechas comuns, incendiárias e de prata; o painel inicia recolhido
> e pode ser expandido/recolhido sem fechar o inventário. Ao consumir a última
> flecha equipada em arco, o servidor move da bolsa a primeira pilha disponível
> conforme a ordem, respeitando os tipos aceitos pela arma. Besta/virotes não usam
> essa preferência. Mensagem autoritativa de troca: `narracao.auto_equipou_municao`.

> **Largar/pegar itens no chão (`game_state.ground_items`):** na masmorra, o herói
> larga um item numa das 8 casas adjacentes e pega de volta — inclusive item largado
> por OUTRO herói (forma de passar itens e de descartar sem ir à cidade). Estado
> `self.ground_items` (`gid -> {id, item, pos}`) **persiste como `self.chests`**: fica
> na memória do `GameRoom` ao ir/voltar da cidade (mesmo lugar) e só é limpo no bloco
> de masmorra nova (`if nova:`, junto de corpses/chests), ou seja, após encerrar a
> missão. **Largar** (`drop_item {source:'bag'|'gear', index|slot_key}`): ação LIVRE
> a qualquer momento (sem `_is_turn`); da bolsa ou de um slot equipado (desequipa na
> hora — reverte `_apply_gear_effect` e reseta `p["weapon"]`); o servidor escolhe a
> 1ª casa livre via `_free_drop_tile_near` (chão livre de parede/porta/decoração
> sólida via `_blocks_tile`, monstro/jogador vivo, baú e outro item); sem casa → recusa.
> **Pegar** (`pickup_item {ground_id}`): ação livre, qualquer jogador, adjacente
> (Chebyshev ≤1), roteia pelo `_route_acquired_item` (bolsa-primeiro; bolsa+slot cheios
> → recusa, fica no chão). Cliente: `GS.groundItems`/`dropItem`/`pickupItem`/
> `groundItemPickable`; largar = arrastar o item pra FORA do modal (backdrop) na
> masmorra; render 2D (emoji + brilho) e 3D (`buildGroundItem3D`, sprite + brilho,
> `g3.groundItemMeshes`) espelham os baús; pegar = clicar na casa (hook unificado
> `handleTileClick`, cobre 2D e 3D). Teste do servidor: `tools/test_ground_items.py`.

> **Guilda dos Heróis (Fase 0):** novo prédio na cidade (hotspot `guilda` →
> `openGuild`) onde cada personagem compra aprimoramentos **permanentes**:
> **Especializações** (upgrades sempre-ativos das habilidades-base — conteúdo nas
> Fases 1+) e **Técnicas da Guilda** (habilidades ativas num **4º slot**; só 1
> equipada por vez, mago/clérigo têm 1 genérica + 1 exclusiva). Catálogo declarativo
> `GUILD_CATALOG` (server.py, estilo `GRIMORIO`/`DECOR_TYPES`); Fase 0 traz a técnica
> de referência **Brutalidade** (+2 dano de arma até o fim do turno; recarga 3
> rodadas; 🍖-2/💧-2). Dados no jogador: `guild_owned`/`guild_equip` (persistidos),
> `technique_cooldowns` (runtime). **Persistência:** save por personagem em
> `saves/<class_id>.json` (`load_guild_save`/`write_guild_save`/`apply_guild_save`,
> carregado no `start_game`; `saves/` é gitignored). **Trava de em-uso:**
> `CHARACTERS_IN_USE` impede escolher em duas salas o mesmo personagem — implicação:
> só um grupo joga cada personagem por vez no servidor (`select_class` trava;
> `release_character`/`_release_all_locks` liberam na desconexão). **Recarga:**
> `pronta_em = round_num + recarga_rodadas`; zera ao voltar à cidade
> (`_voltar_para_cidade`). Compra `handle_guild_buy` (bloco `guild` no `city_state`);
> equipar `handle_guild_equip` (na ficha); usar `handle_usar_tecnica` (4º botão no
> HUD). Cliente: `GS.guildBuy/guildEquip/usarTecnica` +
> `guildCatalogFor/guildOwnedOf/guildEquipOf/tecnicaRestante` (os getters caem para
> o player do `game_state` na masmorra, onde `cityState=null`; catálogo cacheado).
> Teste do servidor: `tools/test_guilda.py`.

> **Especializações do Guerreiro (Fase 1a):** upgrades permanentes sempre-ativos
> (não ocupam slot; sempre válidos) que aprimoram as 3 habilidades-base. **Baseline
> enfraquecido (grátis):** Mira +2 acerto, **Golpe ×1,5** (era ×2 — mudança de
> gameplay; Golpe III restaura ×2), Fúria +1 ataque extra, e **só 1 habilidade
> armada por turno**. **Compras** (`categoria:"especializacao"`, `classe:"warrior"`
> no `GUILD_CATALOG`): `guerreiro_combinar_2` (150, portão — arma 2/turno),
> `guerreiro_mestre_combate` (300, arma 3/turno), `guerreiro_mira_3` (+2 dano),
> `guerreiro_golpe_3` (×2), `guerreiro_furia_3` (2 ataques extras) — os quatro
> exigem `guerreiro_combinar_2`. Ouro é o único custo. Efeitos em `handle_attack`
> via `tem_espec` + helpers `_teto_combinacao`/`_golpe_raw`/`_furia_extras`/
> `_mira_dano_bonus`; o servidor **trunca** os `buffs` ao teto (autoritativo).
> Refactor: Fúria virou contador `skill_ataques_extras` (antes 2 booleanos);
> `skill_bonus_dano` novo (Mira III). Cliente: `GS.warriorComboCap()` limita a
> armação e as descrições dos botões refletem o nível possuído. Teste:
> `tools/test_guerreiro_espec.py`.

> **Especializações do Clérigo (Fase 1b):** gateiam os 4 milagres do Lewis
> (baseline enfraquecido — **mudança de gameplay**: Cura 3d8→**1d8**, Cura em Massa
> raio 5→**2**). **Compras** (`categoria:"especializacao"`, `classe:"cleric"`; II=150,
> III=200, III exige II por linha): `clerigo_cura_2/3` (máx 2d8/3d8),
> `clerigo_massa_2/3` (2d8 raio 4 / 3d8 raio 6), `clerigo_purif_2/3` (+doenças /
> +maldições **e petrificação**), `clerigo_ressur_2/3` (metade PV 🍖15💧15 / PV cheio
> 🍖20💧20). Gating em `handle_cura`/`handle_cura_area`/`handle_purificacao`/
> `handle_ressurreicao` via `_cura_teto`/`_massa_nivel`/`_purif_tipos`/`_ressur_nivel`
> (+`tem_espec`). O "custo crescente" do design já vem da escala existente (💧/dado,
> 🍖4💧4/dado, custo por tipo); a Ressurreição usa custo por nível 10/15/20. Cliente:
> `GS.clericCuraTeto/clericMassaNivel/clericPurifTipos/clericRessurNivel` limitam os
> painéis do Lewis. Teste: `tools/test_clerigo_espec.py`.

> **Especializações do Paladino (Fase 1c):** gateiam as 5 habilidades de Richard
> (baseline enfraquecido — **mudança de gameplay**: Guerreiro da Luz 4→**2**
> atributos simultâneos, Cura pelas Mãos 2d6→**1d6**, Golpe Sagrado 2d8→**1d8**,
> Defensor 50/50 fixo, Regeneração só cura o próprio Richard). **Compras**
> (`categoria:"especializacao"`, `classe:"paladin"`; II=150, III=200, III exige II
> por linha, exceto `ataque_sagrado` que só tem II): `paladino_cura_maos_2/3` (2d6;
> opção +1d6 por +2🍖+2💧, até 3×), `paladino_ataque_sagrado_2` (+2d8 sagrado),
> `paladino_luz_2/3` (3/4 atributos + **detecta armadilhas** em raio 2/3 — feature
> nova, quando Visão ativa), `paladino_defensor_2/3` (raio 5; split 40%/40%, 20%
> mitigado — era 50/50), `paladino_regen_2/3` (cura +1 HP também aliados em raio
> 1/2). Gating em `handle_imposicao_maos`/`handle_attack` (bloco Golpe Sagrado)/
> `_ativar_guerreiro_luz`/`handle_protetor`+`_processar_dano_protetor`+upkeep/
> `_processar_manutencao_richard` via `tem_espec` + helpers `_cura_maos_dados`/
> `_ataque_sagrado_dados`/`_gdl_max_atributos`/`_gdl_trap_raio`/`_defensor_raio`/
> `_defensor_split`/`_regen_raio`. A detecção de armadilhas do Guerreiro da Luz
> reusa `_revelar_armadilhas_raio` — generalização de `_revelar_armadilhas_luccas`
> (Ladino) por raio parametrizado; o Ladino mantém comportamento idêntico (chama o
> mesmo método com seu próprio raio de visão). Cliente:
> `GS.paladinCuraMaosDados/paladinCuraMaosExtra/paladinAtaqueSagradoDados/
> paladinLuzMaxAtributos/paladinDefensorRaio/paladinDefensorSplit/paladinRegenRaio`
> limitam os painéis de Richard (o teto de atributos do Guerreiro da Luz é
> bloqueado no cliente E recusado pelo servidor — autoritativo). Teste:
> `tools/test_paladino_espec.py`.

> **Especializações do Ladino (Fase 1d):** gateiam as 5 linhas de Luccas —
> inclui um **redesign real** (não só números) do Ataque Furtivo e um catálogo
> **extensível** de Fórmulas de Armadilha. **Ataque Furtivo:** baseline
> enfraquecido — hoje disparava com "aliado adjacente" de graça; isso vira
> `ladino_furtivo_2` (compra); o base fica só oculto/invisível
> (`invisivel_sombras`/`oculto_vela`). `ladino_furtivo_3` (Supremo) é uma
> **mecânica nova**: reação automática — quando qualquer aliado que não seja
> Luccas acerta um inimigo vivo, Luccas desfere um furtivo nele também
> (1×/inimigo/rodada, bloqueado se Luccas estiver petrificado/paralisado/
> imobilizado). Hookado em `handle_attack` e `handle_throw` via
> `_furtivo_reativo`; **fora de escopo**: ataque de mão secundária, arremesso de
> lança, animados controlados. **Fórmulas de Armadilha:** hoje todas as 8
> armadilhas de `ARMADILHAS` eram fabricáveis de graça — agora `buraco`
> continua sempre livre e as outras 7 exigem a fórmula correspondente. O
> catálogo é **gerado dinamicamente**: cada tipo em `ARMADILHAS` ganha campos
> opcionais `formula_guild_id`/`formula_preco`; `_gerar_catalogo_formulas_armadilha()`
> lê esses campos e popula `GUILD_CATALOG.update(...)` — armadilhas futuras só
> precisam desses 2 campos para aparecerem na Guilda automaticamente, sem tocar
> em mais nada. Gate em `handle_criar_armadilha` via `_armadilhas_desbloqueadas`.
> **Desarme:** `ladino_desarme_2/3` dão +2 no teste (não soma mais no III);
> `_3` também adiciona um 2º teste que, em sucesso, devolve o `custo_ouro` da
> armadilha. **Veneno Rápido:** o veneno mora na **arma equipada** como uma lista
> de cargas `poison_slots` (viaja com a arma ao trocar/desequipar; consumida por
> `pop(0)` no acerto) — helpers `_weapon_poison_slots`/`_set_weapon_poison_slots`/
> `_aplicar_veneno_na_arma`. Melee tem **1 marcador por padrão**; o teto sobe pelas
> specs via `_capacidade_poison_melee`: `ladino_veneno_2` → 2 cargas do mesmo veneno
> (dura 2 golpes); `ladino_veneno_3` → soma um 2º veneno DIFERENTE mantendo o
> anterior (máx. 2 distintos, FIFO — o antigo é gasto primeiro; reaplicar o mesmo
> recarrega e o move ao fim); combinadas: 2 venenos × 2 cargas = 4. À distância
> (arco/besta) usa `VENENO_CARGAS` projéteis (substitui). O efeito genérico de item
> `coat_poison` fica inalterado. **Esconder nas Sombras:** `ladino_esconder_2/3` dão +2 no
> teste; `_3` também faz a ativação **deixar de gastar a ação bônus** e, ao
> quebrar a invisibilidade (`_quebrar_invisibilidade`), concede +2 de CA por 1
> rodada via `self.temp_def` (mecanismo já existente que expira sozinho).
> Cliente: `GS.ladinoArmadilhasDesbloqueadas/ladinoFurtivoNivel/
> ladinoDesarmeBonus/ladinoDesarmeRecupera/ladinoVenenoMaxHits/
> ladinoVeneno2Slots/ladinoEsconderBonus/ladinoEsconderLivre` — o painel de
> criar armadilha filtra por fórmula destravada (com dica "🔒 Compre a fórmula
> na Guilda"). Teste: `tools/test_ladino_espec.py`.

> **Especializações do Bardo (Fase 1e):** gateiam as 3 linhas de Henrique.
> **Canção Heroica:** 5 nós `bardo_cancao_{acerto,dano,ca,movimento,resistencia}`
> (100 cada) sobem aquele atributo de +1 para +2 (`_cancao_nivel_atributo` em
> `_aplicar_buffs_cancao`); `bardo_cancao_suprema` (200) reduz a manutenção em
> -1🍖/-1💧 mín 0 (`_cancao_custo_reducao`, aplicado na ativação; `cancao_custo`
> guarda o valor já reduzido, então o upkeep herda a redução). **Provocação:**
> `bardo_provocacao_2` (150) faz a desvantagem durar toda a provocação (o reset de
> `provocado_turno_efeito` nos 2 sites de ataque de monstro é pulado enquanto o
> provocador tem a espec), dá +2 CA ao bardo (`_provocacao_ca_bonus` somado à
> `effective_ac` nos 2 sites) e vantagem ao bardo contra o alvo; `bardo_provocacao_3`
> (200, requer _2) estende a vantagem a todos os aliados por 1 rodada
> (`provocado_aliados_vantagem_round == round_num`). Vantagem via
> `_provocacao_atk_vantagem` em `handle_attack`. Helpers: `_provocador` (bardo vivo
> que provocou). **Lendas:** catálogo **gerado** de `MONSTER_DEFS`
> (`_gerar_catalogo_lendas` + `GUILD_CATALOG.update`, preço por tier T1 60/T2 90/T3
> 120/T4 200) — cada `lenda_<tipo>` dá +1 de ataque (`_lenda_atk_bonus` em `eff_atk`)
> e +1 de resistência (`_lenda_resist_bonus` via novo param `fonte` de `_testar_save`,
> passado nos 6 sites de habilidade de monstro vs jogador — modular, derrubar,
> agarrar, constrição, infecção, força descomunal — e no save de escape de agarrão;
> demais saves ficam inertes com `fonte=None`) contra a espécie; só Henrique na base.
> `bardo_lendas_supremas` (300) estende ambos os bônus a todo o grupo enquanto
> Henrique vive (`_bardo_lendas`). Cliente: `GS.bardoCancaoNivel/bardoCancaoSuprema/
> bardoProvocacaoNivel/bardoLendasSupremas` — o painel da Canção mostra +1/+2 por
> atributo e a manutenção reduzida; a descrição da Provocação reflete II/III. Teste:
> `tools/test_bardo_espec.py`.

> **Especializações do Mago (Fase 1f):** gateiam a **Metamagia** de Pedro
> (Aprimorar/Estender/Fortalecer). Baseline enfraquecido (**mudança de gameplay**):
> hoje as 3 metamagias empilhavam ilimitado → **1 por lançamento**; **Fortalecer**
> ×1,5 → **×1,25**. **Compras** (`categoria:"especializacao"`, `classe:"mage"`; III
> exige II): `mago_tecelagem_2/3` (empilhar 2/3 — 150/300), `mago_fortalecer_2/3`
> (×1,5/×2 — 200/250), `mago_aprimorar_2/3` (+2/+3 CD — 150/200), `mago_estender_2/3`
> (+2/+3 rodadas — 150/200). O núcleo é `_resolver_metamagia(p, magia)` — helper puro
> que substituiu o bloco inline de `handle_magia`: reúne as metamagias armadas E
> aplicáveis (dano/duração/save), trunca ao `_teto_metamagia(p)` na ordem
> Fortalecer→Estender→Aprimorar (as excedentes não aplicam nem cobram), e aplica as
> magnitudes via `_fortalecer_mult`/`_aprimorar_bonus`/`_estender_bonus`. A metamagia
> gravada em **pergaminho** (`gerar_pergaminho`) fica inalterada (+1/×1,5/+1).
> Cliente: `GS.magoTecelagemCap/magoFortalecerMult/magoAprimorarBonus/
> magoEstenderBonus` — as descrições dos botões refletem magnitude + teto de
> empilhamento. Teste: `tools/test_mago_espec.py`.

> **Técnicas de Recarga Curta (Fase 2a):** 1º lote das **Técnicas da Guilda** (4º
> slot, genéricas — `categoria:"tecnica"`, `classe:None`, recarga 3, preço 100).
> Fase 2 organizada por **faixa de recarga** (3/5/8/10 rodadas — quanto maior a
> recarga, mais forte/cara a técnica); a aba de Técnicas da Guilda é agrupada por
> faixa (`_renderGuild`). 4 técnicas, despachadas por `efeito.tipo` em
> `handle_usar_tecnica` (que já centraliza turno/recarga/custo e **não** consome a
> ação — "buff-and-act"): **Mira Perfeita** (`mira_perfeita` — próximo ataque à
> distância com vantagem +2 dano; flag `tecnica_mira_perfeita` capturada em
> `_mira_ranged` no `handle_attack`, consumida no ataque à distância mesmo em erro,
> expira no fim do turno), **Espírito Indomável** (`remove_status`, ação livre —
> limpa medo/atordoamento/lentidão + 1 rodada `imune_silencio_ate`, lido em
> `_em_silencio`), **Grito de Guerra** (`buff_aliados_mov` — +2 movimento a todos os
> aliados: bump imediato + `mov_bonus_ate`/`mov_bonus_val` somados dentro de
> `_moves_base` via `_grito_mov_bonus`, o cálculo autoritativo usado no reset de
> turno), **Pressa** (`mov_self_dobrar` — `moves_left += spd`; custo 4/4). Teste:
> `tools/test_tecnicas_espec.py`. Próximos lotes: 2b (5r), 2c reações
> (Contra-Ataque/Ataque Coordenado/Oportunidade/Sangue Frio — exigem framework de
> reação), 2d passivas (Último Esforço); Fase 3 exclusivas Mago/Clérigo.

> **Técnicas de Recarga Média (Fase 2b):** 2º lote das Técnicas da Guilda (recarga 5,
> preço 180, +4🍖/+4💧). **Investida Heroica** (`investida` — dobra movimento; se a
> carga for reta ≥2 casas desde a ativação e o ataque for corpo a corpo, vantagem +2
> dano; `_investida_tecnica_bonus` consumido em `handle_attack` — nome distinto do
> `_investida_bonus` do Ogro), **Defesa Impecável** (`defesa_impecavel` — até o próximo
> turno, ataques contra você com desvantagem via `_defesa_impecavel_ativa` nos 2 sites
> de ataque de monstro; + imune a furtivo em `_verificar_ataque_furtivo` — inerte hoje,
> nenhum monstro dá furtivo a jogador), **Pressão Constante** (`debuff_ca_alvo` —
> inimigo **adjacente** −2 CA por 2 rodadas via `_pressao_ca_pen` no `eff_target_ac`),
> **Tática Defensiva** (`tatica_defensiva` — aliado em raio 4, 1d4 rodadas, split 50/50
> generalizando `_processar_dano_protetor`: protetor genérico além do Protetor do
> paladino), **Passo Fantasma** (`passo_fantasma` — 1d4 rodadas: +2 movimento
> [compartilha `mov_bonus_*` com o Grito] + atravessa objetos em `handle_move`,
> mantendo paredes/portas/criaturas). Cliente: técnicas com campo `alvo`
> (`monstro_adjacente`/`aliado_raio4`) abrem `openTargetModal` no botão do 4º slot.
> Teste: `tools/test_tecnicas_espec.py`. **Foco Absoluto** adiado (vira reação
> "Resistência Absoluta" no lote de reações — resolver conflito de nome com a de 8r).

> **Técnicas de Reação (Fase 2c):** 3º lote das Técnicas da Guilda — **reações**
> que **auto-disparam** dentro de hooks de evento (sem prompt) e aplicam efeito
> **direto** (nunca re-chamam `handle_attack` → sem recursão), espelhando o
> `_furtivo_reativo` do Ladino (Fase 1d). Núcleo compartilhado
> `_ataque_basico_reativo(atacante, alvo)`: ataque fora-de-turno via `_rolar_ataque`
> vs CA do alvo, dano `roll_dice(die)+mod(stat)` (crít ×2), e — se o atacante for o
> **Ladino** e `_verificar_ataque_furtivo` passar — soma os d4 de furtivo
> (`_dados_furtivo`); mata via `_monster_dies`. 4 técnicas (recarga 5, preço 180,
> +4🍖/+4💧, salvo indicado): **Resistência Absoluta** (`buff_saves` — +2 em **todos**
> os saves por 2 rodadas; `resistencia_saves_ate`/`_val`, somado em `_testar_save`
> junto ao `_lenda_resist_bonus`), **Sangue Frio** (`sangue_frio` — arma a re-rolagem
> do **1º erro** de ataque do turno; `sangue_frio_armado` consumido em `handle_attack`
> logo após o `_rolar_ataque` do jogador, antes de limpar os flags de Mira/Investida —
> 2🍖/2💧), **Ataque Coordenado** (`ataque_coordenado`, `alvo:"aliado"` — marca um
> aliado vivo como par [`coordenado_alvo`/`coordenado_turno`]; quando **você** acerta
> um monstro no seu turno, o par desfere um `_ataque_basico_reativo` se o alvo estiver
> no alcance da arma dele [`_alvo_no_alcance_arma`]; disparado em `handle_attack` após
> o custo de sobrevivência; reset no fim do turno), **Contra-Ataque**
> (`contra_ataque`, recarga **8**, preço 280, +6🍖/+6💧 — `contra_ataque_ate =
> round_num+1`; quando um monstro **erra** um ataque contra você, revida com
> `_ataque_basico_reativo` a **cada** erro na janela; **só armas corpo a corpo** via
> `_arma_contra_ataque_ok` [exclui arco/besta pesada de `RANGED_AMMO`, mas **inclui a
> besta de mão** `hand_crossbow`] e o alvo precisa estar no alcance de ameaça da arma
> [`_alvo_no_alcance_arma` respeita `range`/`reach:lanca`/`reach:cajado`/adjacência];
> hookado nos **2 sites de erro de monstro** — `_execute_one_monster_attack` e o loop
> legado). Cliente: técnica com `alvo:"aliado"` abre `openTargetModal` (par, qualquer
> distância) no 4º slot. Teste: `tools/test_tecnicas_espec.py` (seções [12]-[17]).
> **Oportunidade** (adiada desta fase) virou um mini-lote próprio — ver Fase 2d abaixo;
> deixou de ser uma reação de ordem-de-turno.

> **Oportunidade (Fase 2d):** mini-lote adiado da 2c — **redesenhado em
> brainstorming**: não é mais uma reação, é uma técnica de suporte. Tier **10**
> (novo, acima do 8 do Contra-Ataque): 350 ouro, +6🍖/+6💧, recarga 10, `alvo:"aliado"`
> (nunca você mesmo). Concede um **crédito de ação extra** reservado para o PRÓPRIO
> turno do aliado (não imediato) — expira sozinho se `round_num` avançar antes de ser
> usado (`oportunidade_credito`/`oportunidade_round`, comparado no momento do uso, sem
> precisar de reset explícito). Duas vias mutuamente exclusivas para o mesmo crédito
> booleano: **(1) ação principal extra** — unificado com o mecanismo já existente da
> magia Velocidade dentro do helper `_acao_bloqueada` (2 branches paralelos: Velocidade
> e Oportunidade, cada um consome seu próprio crédito e libera a ação); **(2) movimento
> extra** — novo handler `handle_usar_oportunidade_movimento` (`+spd` em `moves_left`).
> Para a via 1 cobrir TODAS as ações principais (não só ataque/magia, que já usavam
> `_acao_bloqueada`), migrou 9 handlers que faziam checagem crua de `action_done`
> (`handle_animar_mortos/cura/cura_area/purificacao/ressurreicao/imposicao_maos/
> criar_armadilha/desarmar_armadilha/libertar_prisioneiro`) para usar `_acao_bloqueada`
> — efeito colateral aceito: a Velocidade agora também vale nessas 9 (antes só valia em
> ataque/magia), tratado como correção de inconsistência pré-existente. Cliente:
> `GS.usarOportunidadeMovimento()` + botão no HUD condicionado a
> `me.oportunidade_credito && me.oportunidade_round === state.round` (o round-check
> foi um catch de code-review — sem ele o botão apareceria com crédito já expirado).
> Teste: `tools/test_tecnicas_espec.py` (seções [18]-[22]).

> **Reviver os Mortos (Fase 1g):** gateia a habilidade de classe de Pedro (não
> mexida nas Fases 1a–1f). Slots de Controle = mod(INT) + nível_Pedro÷2 (mín. 1;
> **mantido** o termo de nível de Pedro, ao contrário do padrão "baseline
> enfraquecido" das outras linhas). **Compras** (`categoria:"especializacao"`,
> `classe:"mage"`; III exige II): `mago_reviver_2` (200, ND passa a ocupar Slots
> fracionários **exatos** — antes toda criatura ocupava sempre 1 Slot — e chance
> de sucesso 100%−ND×15%), `mago_reviver_3` (300, +2 Slots de Controle e chance
> 100%−ND×10%). Nível I (baseline) mantém 1 Slot fixo por criatura e chance
> 100%−ND×20%. **Bônus de nível de Pedro:** todos os Níveis da Guilda somam
> +5% de chance por nível de Pedro (`p["level"]×5`, antes do teto/piso 1–99%) —
> ex. Pedro nível 3 animando ND1 no Nível II: 85%+15% = 100%→clamp 99%. **Zona hostil preservada e inalterada pelos Níveis:** a falha
> catastrófica (cadáver ressuscita vivo e hostil) continua a fórmula original —
> só existe risco quando o ND do monstro excede o teto "seguro" pro nível de
> Pedro (`nivel_max` 2/4/5 conforme nível 1-2/3-4/5+; `zona_hostil = max(0,
> (ND−nivel_max)×10)`); comprar a Guilda só melhora a chance de sucesso "normal",
> não reduz esse risco. ND agora é o CR fracionário real do monstro (`corpse["nd"]`,
> gravado em `_monster_dies`; monstros sem `cr` caem para `tier` como ND inteiro),
> distinto do `corpse["nivel"]` (inteiro, ≥1, usado só como bônus de ataque do
> animado). Helpers: `_reviver_nivel`/`_reviver_slots_max`/`_reviver_slot_custo`/
> `_reviver_chance`, usados em `handle_animar_mortos`. Cliente:
> `GS.magoReviverNivel/magoReviverSlotsExtra/magoReviverSlotCusto/magoReviverChance`
> — o duplicado de `HERO_DATA.pedro.habilidadeClasse` em `game.js` (ficha/tooltip,
> não autoritativo) chama esses getters em vez de recalcular. Teste:
> `tools/test_reviver_mortos.py`.

> **Técnicas de Recarga Longa (Fase 2e):** 4º lote das Técnicas da Guilda, tier
> **10** (350 ouro, recarga 10; +6🍖/+6💧 em três delas — **Sorte** é a exceção, só
> +2🍖/+2💧). **Instinto de Sobrevivência** (`passiva_evitar_morte`) é automática:
> segue o padrão já existente do `_player_dies` (mesmo ramo da Regeneração do
> Paladino) — se o dano zeraria o HP, sobrevive com 1 e entra em recarga. **Último
> Esforço** (`passiva_ultimo_esforco`) também é automática e sobrevive com 1 HP,
> mas além disso abre uma sub-fase de **2 mini-turnos** ("last stand"): mecanismo
> final usa `self.last_stand_pid`/`self.last_stand_event` (`asyncio.Event`),
> `_is_turn` alargado para aceitar `last_stand_pid == pid` (espelhado no cliente,
> ver abaixo), `_abrir_ultimo_esforco` (que aguarda o Event antes de deixar
> `_player_dies` prosseguir para a finalização normal da morte — não há mais
> `return` antecipado nesse ramo), e `_fechar_mini_turno_ultimo_esforco` (decrementa
> os turnos restantes e fecha o Event no fim, hookado em `handle_end_turn` e em
> `handle_disconnect_em_jogo`), com um timer de segurança dedicado
> (`_iniciar_timer_ultimo_esforco`/`_cancelar_timer_ultimo_esforco`/
> `_ultimo_esforco_timer_expira`) que espelha o timer de turno normal já existente,
> **incluindo a mesma guarda de auto-cancelamento** (`t is not
> asyncio.current_task()`) do `_cancelar_timer_turno` pré-existente. Dois
> reforços de concorrência que NÃO estavam no plano original e só surgiram em
> revisão: (a) o ramo do `_player_dies` só abre uma nova janela se
> `self.last_stand_pid is None` — evita que uma segunda morte simultânea corrompa
> uma janela já aberta (o segundo jogador simplesmente não recebe o efeito da
> técnica dessa vez, sem gastar a recarga); (b) o `_cancelar_timer_ultimo_esforco`
> tem a mesma guarda de auto-cancelamento do `_cancelar_timer_turno`. **Golpe
> Decisivo** (`golpe_decisivo`) é manual (arma-e-age): força o próximo ataque
> básico a ser crítico automático no acerto, e triplica (em vez de dobrar) num
> natural 20 enquanto armado. Isso generalizou o multiplicador de crítico de
> `handle_attack` — antes um `dmg *= 2` fixo, agora `dmg *= 3 if (_forca_critico and
> roll == 20) else 2`, onde `_forca_critico = golpe_decisivo_armado OR
> ultimo_esforco_ativo`; sem nenhuma das duas técnicas ativas o comportamento é
> byte-idêntico ao anterior (risco real de regressão, testado explicitamente).
> **Sorte** (`sorte`) é reativa — mas **diferente** do Sangue Frio (Fase 2c, que
> arma a re-rolagem ANTES do ataque): o jogador só decide gastar a Sorte DEPOIS de
> ver o erro, e a re-rolagem usa os modificadores **congelados** do ataque
> original (`ultimo_ataque_perdido`: `eff_atk`/`eff_target_ac`/`vantagem`/
> `desvantagem`/`surv_mod`/`cancao_dano`/`gl_dano`), não os recomputados ao vivo —
> distinção provada por teste dedicado (muda `atk_bonus` do jogador entre o erro e
> o reroll e confirma que o reroll ignora a mudança). O dano do reroll e do ataque
> normal agora passam pelo helper extraído `_resolver_dano_ataque_basico`, que
> preserva uma assimetria real pré-existente entre as fórmulas de dano armado/
> desarmado (o rascunho do próprio plano tinha errado esse detalhe; o
> implementador percebeu e corrigiu durante o Passo). **Auto-cura bloqueada
> durante o Último Esforço:** `handle_use_item` (poção, `effect == "heal"`),
> `handle_cura` (recusa alvo = o próprio caster) e `handle_cura_area` (pula o
> próprio caster no loop de aliados). Lacuna real encontrada e fechada em
> revisão: itens de equipamento com efeito `"maxhp"` (ex. `ring_vita`) davam
> top-up instantâneo de HP ao equipar via `_apply_gear_effect` — como equipar é
> uma ação livre e sempre disponível (nem passa por `_is_turn`), isso furava a
> regra "não pode se curar"; o fix suprime só o bump imediato de HP enquanto
> `ultimo_esforco_ativo` (o aumento de `max_hp` em si continua valendo). Também
> corrigido: uma tentativa de poção de cura recusada não gasta mais a ação
> bônus/recursos do jogador à toa. **Recusa de ativação manual de técnicas
> automáticas:** `handle_usar_tecnica` agora rejeita técnicas com
> `item.get("automatica")` antes de rodar o rodapé comum (recarga/custo) —
> corrigindo um bug pré-existente real em que tentar ativar manualmente uma
> técnica automática gastava fome/sede/recarga à toa, sem nenhum efeito. Cliente:
> `isMyTurn` (em `src/gameState.js`) alargado para aceitar `last_stand_pid ===
> myPid` (espelha o `_is_turn` do servidor); o botão do 4º slot desabilita
> técnicas `automatica` (continua visível, só não clicável) e rotula "AUTOMÁTICA" em vez de "GUILDA"; um banner de
> status ("🔥 ÚLTIMO ESFORÇO — N turno(s) restante(s)") em `renderMyPanel`,
> estilizado como a família já existente de banners de status (regeneração/
> saciado/exaustão) — colocado deliberadamente em `renderMyPanel` (agnóstico de
> classe) em vez de perto do indicador de `animados_turn` sugerido no plano
> original, porque esse indicador só aparece em painéis específicos de classe
> (Pedro/Lewis) e não seria visível para as outras classes. Teste:
> `tools/test_tecnicas_espec.py`, seções `[23]`-`[29]` (com subseções extras
> `[27b]`/`[27c]`/`[28b]`/`[28c]`/`[28d]` adicionadas em ciclos de revisão,
> incluindo um teste ponta-a-ponta do ciclo completo do Último Esforço e a prova
> congelado-vs-ao-vivo da Sorte).

> **Técnicas Exclusivas (Fase 3 — Mago/Clérigo):** primeiro uso real do 2º slot
> (`tecnica_exclusiva`), reservado desde a Fase 0 mas nunca ocupado até agora.
> 7 técnicas (`categoria:"tecnica"`, `classe:["mage","cleric"]`, `exclusiva:True`)
> que aprimoram a **próxima magia** lançada — mesmo padrão "arma e age" das
> demais técnicas, mas rodando dentro de `handle_magia` em vez de `handle_attack`.
> **Recarga 5 (180🪙/2🍖2💧, exceto Canalização Arcana 4🍖4💧):** Aprimorar Magia
> (+1 CD do save), Estender Magia (+1 duração se a magia tiver `duracao`, senão +1
> alcance), Canalização Arcana (ignora Silêncio — "não pode ser interrompida" fica
> inerte, sem mecanismo de interrupção de magia no jogo). **Recarga 8 (280🪙/4🍖4💧,
> exceto Geminada 6🍖6💧):** Empoderar Magia (×1,5 dano ofensivo), Magia Geminada
> (2º alvo escolhido **na ativação** — modal combinado aliado+monstro, `alvo:
> "qualquer_vivo"` — reexecuta o mesmo efeito nele se elegível: vivo, no alcance,
> e do tipo certo pro `tipo` da magia), Canalização Perfeita (o alvo testa
> resistência com desvantagem). **Recarga 10 (350🪙/6🍖6💧):** Magia Acelerada (a
> magia não marca `action_done` — libera a ação principal do turno). Todas
> **independentes** da Metamagia do Mago (Fase 1f, toggle permanente e gratuito):
> os bônus de Aprimorar/Estender se somam e os multiplicadores de dano
> (Empoderar/Fortalecer) multiplicam em cadeia se ambos estiverem ativos no mesmo
> lançamento — decisão de brainstorming, para não duplicar a lógica dos toggles
> existentes nem criar uma relação de exclusividade sem necessidade real de
> design. Nota: Empoderar e Geminada nunca coexistem no mesmo personagem (as duas
> são `exclusiva:True`, disputando o mesmo slot único); a combinação realmente
> alcançável em jogo — e a testada — é Fortalecer (Metamagia, sem slot) +
> Geminada, provando que a bonificação ×1,25 se aplica aos DOIS alvos. Duas
> generalizações retrocompatíveis: `classe` no catálogo passa a aceitar lista
> (`_guild_classe_ok`, usado em `guild_items_for_class`/`handle_guild_buy`;
> `guildCatalogFor` no cliente ganha o mesmo `Array.isArray`); `_testar_save`/
> `_save_mostrado` ganham `desvantagem` (rola 2d20, usa o pior — só chega a
> `_executar_raio_congelante` hoje, a única magia de alvo único com save
> implementada; os próximos executores de alvo único devem seguir o mesmo
> padrão). Interação com o Último Esforço (Fase 2e): decidido em brainstorming
> **não bloquear** — o TODO deixado em `game.js` foi resolvido sem nova
> restrição, já que `GS.isMyTurn` já cobre a janela do Último Esforço. Cliente:
> badge "★ Exclusiva Mago/Clérigo" em `_guildItemRow`; nenhuma seção nova na UI
> (as 7 técnicas caem nas faixas de recarga já existentes). Teste:
> `tools/test_guilda_fase3_espec.py`.

> **Peão vira na direção do movimento:** o peão GLB 3D (hoje só `paladin`)
> agora encara o lado do último passo dado, em incrementos de 90°. Servidor:
> `handle_move` grava `p["facing"] = [dx, dy]` a cada passo válido (mesmo
> formato/mecanismo que `m["facing"]` já usava pros monstros orientados —
> crocodilo/lagarto); `enter_dungeon` limpa esse campo ao (re)posicionar os
> jogadores na entrada, então toda masmorra começa com o peão olhando pro
> Sul. Vai automaticamente no `game_state` (serialização crua do dicionário
> do jogador, sem view filtrada). Cliente: `_facingToRotY` (`game.js`)
> converte o vetor num ângulo múltiplo de 90°; `build3DFig` reaproveita o
> parâmetro `mFacing` (já existente pros monstros orientados) pra também
> carregar a direção do peão de herói, já que nenhum herói passa pelo ramo
> de monstro orientado. Sem animação — a rotação encaixa instantaneamente a
> cada passo confirmado. Teste: `tools/test_peao_facing.py`.
>
> **Peão de herói não é mais reconstruído ao virar nem ao passar a vez (2026-09-30):**
> a assinatura do peão (`obterFig` no laço de heróis de `renderMap3D`) incluía `isCur` e
> `p.facing`, então passar o turno refazia DOIS peões (GLB clonado, contornos, materiais)
> só para ligar o anel dourado, e cada passo com mudança de direção refazia o de quem
> andou. Agora `build3DFig` cria o anel em **todo** peão de herói (`classId`), com
> `visible` só na vez (`grp.userData.turnRing`), e `_sincronizarPeaoHeroi3D(fig, isCur,
> facing, selecionado)` roda após o `obterFig`: liga/desliga o anel + `isCurrentFig` e gira
> a raiz via `_girarRaizPeao3D`. A raiz tem rotações temporárias próprias (giro do ataque,
> redemoinho, tempestade, pose de combate) que guardam uma base e a restauram ao fim — a
> direção nova vai para a **base** delas, senão o fim do efeito desfaria o giro; o peão
> **selecionado** (que gira devagar sem base) não é arrancado do giro. Só gira pela raiz
> quem tem `userData.giraRaiz` (GLB de herói sem metamorfose): billboard não tem frente e o
> metamorfoseado gira dentro do modelo de monstro (por isso a assinatura mantém `p.facing`
> **só** com `formaVisual`). O GLB que carrega depois lê `userData._facingRotY` em vez do
> `rotY` capturado. O deslize do `move_path` usa o mesmo `_girarRaizPeao3D`. Medido no
> navegador, mesmo roteiro (4 turnos andando): **20 → 0** chamadas de `build3DFig`.
> **Monstros, servos animados e herói metamorfoseado** seguem o mesmo princípio:
> `m.facing`/`a.facing`/`p.facing` saíram das assinaturas e `_setMonsterMeshFacing3D` é
> chamado após o `obterFig`. Para isso ele acha o grupo de direção **aninhado**
> (`_grupoDirecaoMonstro3D`: o wrap do GLB mora em raiz → corpo → wrap, e antes só filho
> direto era visto — por isso o deslize nunca girava GLB de monstro), guarda
> `userData._facingAtual` na raiz (o `montar` do GLB que chega depois o reaplica) e move os
> efeitos presos ao meio das 2 casas da criatura orientada (`userData._fxMeio`: fogo/gelo);
> o sprite orientado que carrega depois respeita o espelho atual. **Exceção:** o monstro
> ORIENTADO com GLB (2 casas, ex.: crocodilo) tem base/sombra dimensionadas pela direção
> (largura×comprimento trocam) e fora do grupo que gira — `_eixoDirecaoSig` põe só o
> **eixo** (h/v) na assinatura: virar 180° apenas gira, virar 90° reconstrói. Medido no
> navegador com o servidor congelado e GLBs carregados (3 monstros × 6 viradas):
> **18 → 0** reconstruções, e cada modelo girando para o ângulo certo. Teste:
> `tools/test_peao_sem_reconstrucao.js` (43).

> **Instrumentos do Bardo (Fase 1):** equipamento exclusivo do bardo (Henrique)
> que concede uma habilidade de assinatura escalável por qualidade. **Modelo
> 3-eixos:** `INSTRUMENTOS_BASE` (server.py) define 4 bases — `harpa`/`tambor`/`sino`/
> `alaude` — com `maos` (1/2, só economia de ação), `modo` (`ativada`/`passiva`),
> `habilidade_nome`, `desc`, `efeito`, custo-base e stats por qualidade
> (`velho`/`rustico`/`padrao`). Uma instância é criada por `criar_instrumento(base,
> qualidade, origem, encantamento, refinado_bonus, origem_bonus)` (item com
> `tipo_item:"instrumento"`, `name`/`emoji`/`item_slot`, `allowed_classes:["bard"]`) —
> guarda só os atributos; os números efetivos são derivados por `_instrumento_stats`
> (camadas Qualidade→Refinado→Origem→Encantamento; Origem/Encantamento plumbados mas
> não gerados na Fase 1). CD do save = `_instrumento_cd` = `8 + mod(DES)`. "Lendário"
> é só o rótulo do máximo dos 3 eixos. **Slot — mão do escudo:** o instrumento vive
> no `off_hand` (sem slot dedicado; compete com escudo/2ª arma). `_slot_category_for_item`
> mapeia `tipo_item=="instrumento"` → `off_hand`; o equipar reusa o pipeline de gear
> (`_executar_equip_from_bag`, ramo `off_hand`), com bard-only garantido por
> `allowed_classes`. Aquisição bolsa-primeiro (`_route_acquired_item`, sem
> auto-equipar); loja via `instrumento_sku` em `SHOP_MERCHANT`; loot reusa o pipeline
> de item. **Ativação:** `handle_usar_instrumento` (msg `usar_instrumento`) lê o
> `off_hand` (checando `tipo_item`), valida turno + economia de ação (flag
> `instrumento_usado`, resetada no fim do turno: 2 mãos = atacar OU tocar; 1 mão =
> atacar E tocar; máx. 1/turno) + custo 🍖/💧, e despacha por efeito:
> `_instr_nota_cortante` (Harpa, alvo único, save Reflexos meia), `_instr_acorde_trovejante`
> (Tambor, AoE raio, save + empurrão; `push=0` grava `mov_pen_*` — leitura no
> movimento do monstro é lacuna aceita da Fase 1), `_instr_ecos_dolorosos` (Sino, aura
> ativada por `duracao` rodadas; retaliação `_instr_ecos_retaliar` hookada em
> `_execute_one_monster_attack`, só melee via `not atk_def.get("range")`). **Sinfonia
> Heroica** (Alaúde) é passiva: `_cancao_nivel_atributo`/`_sinfonia_bonus` somam +1 aos
> atributos cobertos da Canção conforme a qualidade do Alaúde no `off_hand` (empilha
> com a espec. da Canção da Fase 1e). **Loadout de Henrique:** adaga real na mão
> principal + Alaúde Velho no `off_hand` (passiva → +1 Acerto na Canção);
> `test_bardo_espec` limpa o `off_hand` para isolar a base da Canção. **Cliente:**
> `game.js` `_bardInstrumentoBtn`/`acionarInstrumento` (botão no HUD só p/ instrumento
> ativado; Nota Cortante abre `openTargetModal`) + `aplicarTooltipInstrumento`/
> `_tooltipInstrumentoHTML` (quadro de hover com habilidade, `desc`, custo e stats —
> no botão do HUD e nos slots do paperdoll/bolsa, já que instrumentos não estão em
> `CATALOGO_ITENS`); `src/gameState.js` exporta `usarInstrumento`/`instrumentoBase`/
> `instrumentoEquipadoDe`/`instrumentoStatsClient`/`instrumentoDisponivel` (lêem o
> `off_hand`) e mapeia a categoria em `canPlaceItem`/`_slotCategoryForItem`; a tabela
> `INSTRUMENTOS_BASE` é enviada no `game_start`. **Fases 2–5 pendentes:** 2 Trompa/
> Lira/Flauta, 3 Réquiem Final (Violino), 4 Origens Élfica/Anã + Rúnico + Lendário +
> loot procedural, 5 Improviso/Gaita. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-10-instrumentos-bardo-fase1*`. Teste:
> `tools/test_instrumentos_bardo.py`.

> **Fase 2 (Trompa/Lira/Flauta):** Chamado do General (Trompa, `chamado_general`) —
> cone direcional (`dir:[dx,dy]`, reusa `_cone_tiles`), Vontade → falha: medo
> (`com_medo`/`medo_rodadas`, reusa `_fugir_monstro`) + penalidade de movimento; sucesso:
> penalidade menor. A penalidade usa `_reduzir_mov_monstro`, que reusa o mecanismo da Cola
> (`mov_reduzido_orig`/`mov_reduzido_rodadas`, restaurado em `_processar_*_turno`) e **fecha
> a lacuna** do Tambor Velho da Fase 1 (o ramo `push=0` agora reduz o movimento de verdade).
> Dueto Marcial (Lira, `dueto_marcial`) — buff `dueto_marcial_ate`; o hook
> `_reacoes_instrumento_apos_ataque` (em `handle_attack`, site principal do acerto) faz o
> bardo revidar `_ataque_basico_reativo` quando um aliado adjacente ao bardo acerta um
> inimigo também adjacente; cota `_dueto_marcial_cap` = 1/rodada (2 se Rúnico — plumbado
> p/ Fase 4). Dueto Fantasma (Flauta, `dueto_fantasma`) — buff `dueto_fantasma_ate`/`_fracao`;
> o mesmo hook ecoa uma fração do dano do ataque básico do bardo no mesmo alvo (sem novo
> teste, sem recursão, só quando acerta). Guardas do Ecos (bardo vivo + instrumento ainda
> no `off_hand`) valem p/ Lira e Flauta. Cliente: `usarInstrumento(target, dir)` repassa
> direção; `acionarInstrumento` abre um seletor de 8 direções (`escolherDirecaoInstrumento`)
> p/ o Chamado; Lira/Flauta são auto-centrados. Loja: SKUs em `SHOP_MERCHANT`. Fases 3–5
> pendentes. Testes: `tools/test_instrumentos_bardo.py`.

> **Fase 3 (Réquiem Final / Violino):** habilidade sustentada de alvo único (2 mãos,
> `requiem_final`). Ativação `_instr_requiem_final` (alvo com LOS + `alcance` por qualidade;
> grava `requiem_alvo`/`requiem_contador` no bardo e `requiem_por` no monstro); toggle-off
> tratado cedo em `handle_usar_instrumento` (grátis, sempre disponível, mesmo após agir). DoT
> `_processar_requiem_turno` (no turno do alvo, junto de paralisia/veneno): contador sobe até
> o teto por qualidade (velho 3 / rústico 4 / padrão 5), Vontade → falha `contador×dado`
> (d2/d4/d6), sucesso sem dano; matar o alvo encerra. Taunt `_requiem_forca_bardo` (o alvo +
> monstros a ≤3 do bardo são forçados a atacá-lo — integrado em `_get_monster_primary_target`
> e nos 3 booleanos `forcado`). Concentração `_concentracao_requiem` (Vontade CD 8+dano ao
> sofrer dano; falha encerra) hookada no ataque de monstro + ticks de veneno/chamas/armadilha
> (todos via `_dano_em_alvo`); Origem Anã +2 plumbada p/ Fase 4. Manutenção
> `_cobrar_manutencao_requiem` (-2🍖/-2💧 no turno do bardo; sem recursos encerra).
> `_encerrar_requiem` (idempotente) chamado em morte do alvo/bardo, quebra de concentração,
> sem recursos, desequipar, recast e toggle. Cliente: mira como Nota Cortante (ou toggle-off
> se já ativo) + banner de status roxo em `renderMyPanel`. Animação visual: notas carmesim
> orbitam o alvo nos modos 2D/3D durante a sustentação; no turno em que o alvo falha Vontade,
> o enxame converge no impacto. Eventos `spell_animation` start/attack/end acompanham a ativação,
> dano e todos os caminhos de encerramento sem alterar a mecânica. Fase 4 Rúnico: Violino Rúnico dá
> -1 Vontade ao alvo. Testes: `tools/test_instrumentos_bardo.py`.

> **Fase 4a (Origens Élfica/Anã):** popula o eixo Origem (plumbado desde a Fase 1). Afixos por
> origem — Élfica {`cd`,`alcance`,`duracao`}, Anã {`fome_sede`(−1🍖−1💧),`duracao`,
> `concentracao`(+2 no Réquiem, lido em `_concentracao_requiem`)} — pré-rolados e filtrados por
> `_afixo_aplicavel`/`_afixos_validos_origem` (Élfica sem afixo aplicável, ex.: Alaúde, rebaixa
> p/ Humana). `_aplicar_afixo` ganhou `fome_sede`. `_instrumento_nome` acrescenta o adjetivo de
> origem com concordância de gênero (Élfica/Élfico, Anã/Anão). Roller procedural
> `gerar_instrumento_aleatorio` (ponderado: qualidade 35/30/25/10, origem 70/15/15; base sem
> afixo Élfico aplicável vira Humana). Loot: token autoral `{"tipo":"instrumento_aleatorio"}`
> resolvido por `_resolver_loot_instrumento` em `hidratar_itens_bau` (baús/recompensas) e na
> cadeia de loot de `_monster_dies` (drop) — designers posicionam o token; placement de
> referência no Bugbear das Sombras (3%). Loja: SKUs de origem (`instrumento_sku` com
> `origem`/`origem_bonus`; id `instrumento_{base}_{qualidade}_{origem}`) adicionados **para
> teste**. Cliente: `instrumentoStatsClient` espelha `fome_sede`/`cone`. Fase 4b: Encantamento
> Rúnico (8 efeitos) + Lendário + Rúnico no roller. Testes: `tools/test_instrumentos_bardo.py`.

> **Fase 4b (Encantamento Rúnico — framework + efeitos simples):** popula o 3º eixo. Camada
> Rúnica em `_instrumento_stats` (`_aplicar_runico` lê o dict `runico` do base quando
> `encantamento=="runico"`): Sino `dano→1d6`, Flauta `duracao +2` (3/4/5), Trompa `medo +1`
> (Amedrontado 2r). Violino Rúnico: `_processar_requiem_turno` passa `extra_mod=-1` no save de
> Vontade do alvo. Lira Rúnica: 2×/rodada (já plumbado em `_dueto_marcial_cap`). Nome
> (`_instrumento_nome`): sufixo "Rúnico/a"; **Lendário** (Refinado + origem≠Humana + Rúnico)
> substitui por "Lendária/o {Origem}" (ex.: "Harpa Lendária Élfica"). Roller sorteia Rúnico
> ~4% (independente de origem/qualidade). `instrumento_sku` ganhou `encantamento` (id
> `..._runico`); SKUs Rúnicos + 1 Lendário na loja **para teste**. Cliente:
> `instrumentoStatsClient` espelha a camada Rúnica. Fase 4c (efeitos Rúnicos bespoke): Harpa
> (Nota Cortante em linha), Tambor (Atordoa/−1 Ataque), Alaúde (+resistências na Canção) —
> uma Rúnica dessas 3 bases já pode ser gerada/comprada, mas seu efeito dedicado só chega na
> 4c. Testes: `tools/test_instrumentos_bardo.py`.

> **Fase 4c (Encantamento Rúnico — efeitos bespoke):** fecha os 8 efeitos Rúnicos. **Harpa**
> Rúnica: Nota Cortante vira reta direcional (`_nota_cortante_linha`, reusa `_caminho_relampago`;
> cada alvo Reflexos-meia); o cliente usa o seletor de direção do Chamado quando a Harpa é Rúnica.
> **Tambor** Rúnico: no Acorde, falha → `perde_turno` (Atordoado), sucesso → −1 Ataque até o
> próximo turno (`acorde_atk_pen_ate` lido por `_acorde_atk_pen`, somado ao `m_atk` no ataque
> modular `_execute_one_monster_attack` E no loop legado). **Alaúde** Rúnico:
> `_alaude_runico_resist` soma +1 em Fortitude/Vontade aos aliados sob a Canção (via `_testar_save`,
> escopo amplo; "sob a Canção" = chave `buffs_cancao` presente). Fase 5: Improviso/Gaita. Testes:
> `tools/test_instrumentos_bardo.py`.

> **Animação da Nota Cortante:** o servidor emite `spell_animation` após validar alvo/linha, sem
> interferir na resolução; `game.js` desenha a lâmina de vento atravessando o trajeto e a clave de
> sol dissonante no impacto, tanto em 2D quanto em 3D. Harpa Rúnica anima cada alvo da linha em
> sequência espacial. Testes: `tools/test_instrumentos_bardo.py`.

> **Fase 5 (Improviso/Gaita):** fecha o roadmap dos instrumentos. Base nova `gaita` (🪗, 1 mão,
> ativada, custo 3🍖/3💧) com a habilidade **Improviso**: `_instr_improviso` rola uma cascata 2d6
> (`_improviso_rolar_cascata`) numa **tabela meta** que invoca a habilidade de assinatura de outro
> instrumento **no tier da qualidade da Gaita** — sintetizando um instrumento virtual
> (`_improviso_virt_st`) e reusando os `_instr_*` existentes. Tabela: 2 Desafinado (bardo -1
> ataque/CD, `desafinado_ate`), 3 Falha, 4 Ecos/5 Dueto Marcial/6 Dueto Fantasma/10 Sinfonia
> (forçados a 1 rodada; Sinfonia via `sinfonia_temp_ate`), 8 Acorde (auto), 7 Nota Cortante/9
> Réquiem-1ª-rodada (`_improviso_requiem_tick`)/11 Chamado (enfileirados em `improviso_pendente`,
> mirados pelo cliente via `improviso_alvo`). **12 = Encore:** rola +2×; 2º 12 → **Encore Menor**
> (`_aplicar_encore_menor`: aliados em raio 5 gastam -1🍖/💧 por 1 rodada + Mago/Clérigo 1 magia
> grátis); a Gaita **Rúnica** recursa em cada 12 e um 3º 12 → **Grande Encore**
> (`_aplicar_grande_encore`: 1d4 rodadas — todos sob a Canção agem sem custo, Mago/Clérigo magias
> ilimitadas). O desconto de custo passa por um **helper central novo**
> `_pagar_fome_sede`/`_custo_fome_sede_efetivo`, para o qual os débitos de fome/sede das ações
> ativas (magia, curas, imposição, técnica, armadilha, instrumentos, manutenções Canção/Réquiem)
> foram migrados. Hooks de aura (`_instr_ecos_retaliar`, `_bardo_dueto_marcial`, Dueto Fantasma,
> `_sinfonia_bonus`) passam a aceitar `off base=="gaita"`. Aquisição: SKUs na loja + `gaita` em
> `_ROLLER_BASES` (loot procedural). Cliente: `game.js` `renderImprovisoQuadro` (quadro da
> cascata) + fila de mira; `src/gameState.js` `improvisoAlvo` + evento `improvisoResultado`.
> **Animações da Gaita:** `desafinado_gaita` desenha notas tortas tremendo e se desfazendo;
> resultado 10 reaproveita `cancao_heroica`; `gaita_encore` divide a nota em pares e, no Grande
> Encore, expande uma onda dourada até os aliados sob a Canção. Efeitos em 2D/3D, sem alterar regras.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-07-12-instrumentos-bardo-fase5*`. Teste:
> `tools/test_instrumentos_bardo.py`.

> **Modo Mestre Jogador (Fase A — núcleo de controle):** modo opcional em que um
> humano assume o papel de **mestre** (7º participante, sem herói) e controla os
> monstros já colocados. Rastreado por `self.master_pid`/`self.master_name` (NÃO
> fica em `self.players` durante a partida — extraído em `start_game` —, então todo
> laço que itera heróis segue intocado; a conexão fica em `self.connections`, então
> os broadcasts o alcançam). Assento no lobby via `claim_role` (`is_master`; teto 6
> heróis + 1 mestre; `_can_start` ignora o mestre). Cada monstro tem `control_mode`
> (`auto`/`semi`/`manual`, lido via `.get(...,"auto")`); `_mestre_ativo()` (mestre
> conectado) — quando False, todo monstro é tratado como `auto` e a partida é
> **byte-idêntica** à do jogo sem mestre. Despacho no ramo de monstro de
> `_activate_initiative_actor` (`monster_step`): **auto/semi** → `gm_phase(monster)`
> (o Semi força o alvo em `_get_monster_primary_target`, abaixo de
> réquiem/provocação/taunt); **manual** → `_master_manual_window` (janela bloqueante
> via `asyncio.Event` + timer anti-AFK de 60s que resolve via IA, espelhando o
> Último Esforço). Handlers `handle_mestre_set_modo`/`set_alvo` (guarda de fase
> `playing`) e `handle_mestre_mover_monstro`/`atacar_monstro`/`encerrar_monstro`
> (guarda `pid==master_pid` + `monster_id==master_manual_mid`; move reusa
> `_commit_monster_step`, ataque reusa `_execute_one_monster_attack` com alcance
> melee/ranged). `master_pid`/`master_manual_mid` vão nos payloads city/game_state.
> Desconexão do mestre: `_on_master_disconnect` fecha a janela Manual aberta (o
> monstro interrompido age via IA) e os monstros voltam ao auto; reconexão pelo
> `rejoin` (casado por `master_name`). Vitória/derrota do mestre saem de graça dos
> fluxos existentes (TPK / objetivo cumprido); sem métrica de Tensão (Camada D).
> Cliente da Fase A: lobby toggle + HUD do mestre + visão sem névoa. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-13-modo-mestre-jogador-fase-a*`.
> Teste do servidor: `tools/test_modo_mestre.py`.

> **Modo Mestre — Combate ao avistar, controle manual e ficha do monstro:** camada
> seguinte à Fase A (só ativa com `_mestre_ativo()`; sem mestre, tudo byte-idêntico).
> **Despertar por avistamento:** `_verificar_avistamento` (idempotente, chamado após
> `handle_move` e `handle_open_door`) — se um herói vivo (`_ativo`) tem linha de visão
> a um monstro dormente (`_heroi_enxerga_monstro`: raio de visão do HERÓI +
> `_tem_linha_de_visao` + oclusão por objetos altos `_tall_oclui_caminho`), acorda a
> **sala inteira** dele: seta `alertado=True` e `control_mode="manual"` em cada
> monstro do grupo (por `room_id`; sem sala → só ele) e narra "⚔️ Combate!" uma vez
> por sala. **Dormência generalizada:** `_monstro_ativo_em_combate(m)` é o predicado
> único que decide se um monstro age / é controlável / é alvo — COM mestre: só se
> `alertado`; SEM mestre: ativo a menos que a sala esteja trancada (comportamento
> antigo). O despacho de iniciativa (`monster_step` em `_activate_initiative_actor`)
> e o alvo de habilidades pulam o monstro quando o predicado é falso — um monstro
> ainda não avistado fica parado e **não** abre a janela Manual quando sua iniciativa
> chega. **Cliente (puro, sem servidor):** a tela de seleção troca o carrossel de
> peões pela **imagem do mestre** (`assets/portraits/mestre_do_jogo.jpeg`) quando você
> assume o papel (`_csApplyMasterMode` cria `#cs-master-portrait`); e o mestre abre a
> **ficha do monstro** (`renderFichaMonstro` → painel `#ficha-monstro` no canto
> inferior-esquerdo: HP/CA/movimento, atributos, ataques e habilidades) clicando num
> monstro no tabuleiro (ramo de mestre em `handleTileClick` via `_monstroEmCasa`) ou
> numa linha do HUD do mestre; a ficha some ao sair da masmorra e para não-mestres.
> Os dados vêm do dict completo do monstro serializado em `game_state.monsters`
> (`push_state` faz `dict(m,…)`), cobrindo monstros de ficha nova (`attacks`/
> `special_abilities`) e legados (`atk_bonus`/`damage`). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-14-modo-mestre-combate-controle*`.
> Teste do servidor: `tools/test_modo_mestre.py` (75 checks).

> **Modo Mestre — Camada B: Reforços do Mestre:** o autor grava
> `master_reinforcements: [{type,count}]` na masmorra (editor, seção "Reforços do
> Mestre" no painel de nível de masmorra; validado em `validar_dungeon`). Ao entrar
> na dungeon o servidor materializa `self.master_reserve` (`type→count`, via
> `_carregar_master_reserve`; inerte sem mestre). A mensagem `mestre_implantar_reforco`
> (`handle_mestre_implantar_reforco`) cria o monstro via `make_monster` numa casa livre
> (`_tile_livre_para_reforco`, espelha `_free_drop_tile_near`), `alertado`+`manual`;
> ele entra sozinho na iniciativa da próxima rodada (`_rebuild_initiative` itera
> `self.monsters` fresco). `master_reserve` vai no `game_state` enriquecido com
> name/emoji para o HUD. Cliente: `GS.mestreImplantarReforco` + seção "Reforços" no
> `renderMasterHud` com modo de clique-para-implantar (`window._modoImplantarReforco`,
> tratado no ramo de mestre de `handleTileClick`; Esc cancela). Só-mestre; sem mestre,
> byte-idêntico. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-15-modo-mestre-camada-b-reforcos*`.
> Teste: `tools/test_modo_mestre.py`.

> **Modo Mestre — Camada C: ND unificado + Termômetro (editor) + Minimapa (mestre):**
> auxílios de dificuldade — design-time no editor + leitura só-mestre em jogo; **nada
> muda no runtime** (o `expected_party` é só referência). **ND unificado:** todo
> monstro tem `cr`; helper module-level `monster_cr(mdef)` (cr explícito, senão
> fallback `_CR_POR_TIER` por `tier`; sem tier→tier1). Os 6 legados ganharam `cr`
> (goblin .25/skeleton .5/orc .75/dark_mage .5/troll 1.5/dragon 5). **Grupo esperado:**
> campo `expected_party {heroes 1-6, level ≥1}` da masmorra (`_norm_expected_party`,
> `validar_dungeon`, default {4,1}), serializado em `game_state`. **Módulo compartilhado
> `src/difficulty.js`** (`window.Difficulty`): `crFromEntry`/`poder(h,l)=h×l`/
> `faixa(nd,pod)` (Fácil<0.4 / Equilibrada<0.8 / Difícil<1.2 / Mortal, cores) — ponto
> ÚNICO de calibração; incluído em `index.html` e `tools/editor.html`. **Termômetro no
> editor** (`tools/editor.js`, painel `!S.sel`): total + pior sala (por `room_id`) +
> preview 2/4/6. **Minimapa de CR do mestre em jogo** (`game.js`, só `GS.isMaster()`):
> o `#ficha-fab` (🎒 Inventário) vira 🗺️ "Mapa de CR" (`_atualizarFichaFab` no hook de
> `gameState`); `abrirMinimapaCR`/`renderMinimapaCR` desenham as salas de
> `game_state.rooms` coloridas pela faixa, CR por sala (`_crPorSalaMapa` de
> `monsters[].cr`/`room_id`), **CR médio = média das salas** no topo, seletor 2/4/6;
> nunca visível aos jogadores (só UI). Spec/planos em
> `docs/superpowers/{specs,plans}/2026-07-15-modo-mestre-camada-c*`. Teste servidor:
> `tools/test_modo_mestre.py` (seções [19]/[20]).

> **Camada C — ND/XP de armadilha:** cada tipo de `ARMADILHAS` tem `cr`; helpers
> module-level `trap_cr(meta)` (cr explícito, senão derivado da `dificuldade`, senão
> 0.3) e `trap_xp(cr)=round(cr×TRAP_XP_POR_CR)` (=20). Só armadilhas **autoradas**
> (não as `aliada` do Luccas nem os buracos procedurais). **XP:** `_conceder_xp_armadilha`
> concede uma vez (flag `xp_concedido`), dividido entre os heróis vivos (com
> `_check_level_up`), ao **desarmar** (`handle_desarmar_armadilha`, sucesso) OU ao
> **disparar e o herói-alvo sobreviver** (`_disparar_armadilha`, nos 3 pontos de saída:
> alvo-único, teletransporte e dardos). **cr no termômetro/minimapa:** o `cr` das
> autoradas vai em `game_state.armadilhas` (`_serializar_armadilhas`; `aliada`→0) e no
> catálogo do editor (`export_catalog.py` → `editor_catalog.js`); `_crPorSalaMapa`
> (game.js) e `_ndPorSala` (editor.js) somam as armadilhas por sala (casando `pos` à
> sala que a contém). Teste: `tools/test_modo_mestre.py` (seções [21]/[22]).

> **Camada C — Salas obrigatórias:** cada sala aceita `required` (bool) +
> `required_mode` (`visit`|`clear`, default `clear`), marcado no painel da sala do
> editor. Novo tipo de objetivo `salas_obrigatorias` (principal/secundário no dropdown
> `OBJ`): cumprido quando TODAS as salas `required` atendem sua condição — `clear` =
> sem monstros vivos com aquele `room_id` (sala vazia já conta); `visit` = um herói
> entrou (rastreado em `self.salas_visitadas`, populado em `handle_move` reusando o
> `entered = player_room(...)`). Helpers `_sala_obrigatoria_ok`/
> `_salas_obrigatorias_progresso`; o payload de status (`_objetivo_payload`) inclui
> `progresso {feitas,total}` → o HUD (`_objRow` em game.js) mostra "N/M salas".
> `validar_dungeon` rejeita `salas_obrigatorias` sem salas marcadas e `required_mode`
> inválido. Só design-time/objetivo (sem trava de encerramento extra). Teste:
> `tools/test_modo_mestre.py` (seção [23]).

> **Camada C — Validador de design (editor):** só-avisa (nunca bloqueia). Em
> `tools/editor.js`, funções `_grafoSalas` (grafo de salas via BFS nos tiles de chão:
> conectividade da entrada + adjacência parando ao entrar noutra sala + distância) +
> `_ndSalaMap` (ND por sala, reusa a lógica do termômetro) + `_validarDesign`. 5 regras
> viram avisos: **R4** conectividade (sala isolada), **R2** distância spawn→boss (nº de
> salas, mín. `VALID_MIN_SALAS`=3), **R5** descanso antes do boss (vizinha com ND ≤
> `poder×VALID_REST_FATOR` ou role `empty`), **R6** teto do ND **médio** da rota crítica
> (=salas `required`; > `poder×VALID_R6_FATOR`), **R3** picos entre salas obrigatórias
> consecutivas (Δ > `VALID_MAX_PICO`). Boss/entrada por `role`. UI: seção "⚠️ Avisos de
> design" no painel de nível de masmorra (`_avisosDesignHTML` após o termômetro), live.
> Limiares = constantes no topo do módulo (tunáveis). **R1** rota alternativa: detecção de
> gargalo/cut-vertex (`_alcancaSemSala` — remove cada sala intermediária e vê se o boss ainda
> alcança a entrada; por Menger ⇔ ≥2 caminhos vértice-disjuntos). Editor não roda no MCP (arquivos externos viram snapshot) — grafo
> validado por teste node sintético. Spec: `docs/superpowers/specs/2026-07-16-validador-masmorra-design.md`.

> **Modo Mestre — Camada B: Falas de NPC:** marcadores de fala autorados no editor
> que exibem um **balão leve** em jogo (`#fala-popup`, distinto do log `gm_narration`
> e da story de tela cheia). Cada fala = `{id, pos, falante:{nome,emoji}, texto,
> trigger}`; **3 gatilhos** (`trigger.tipo`): `proximidade` (herói a ≤`raio` Chebyshev
> do marcador), `sala` (herói entra na sala do marcador) e `manual` (botão do mestre
> no HUD). Cada uma dispara **uma vez** (flag `disparada`). Servidor: `self.falas`
> carregado na entrada da masmorra (`disparada=False`); `_verificar_falas(p, entered)`
> hookado em `handle_move` (proximidade + sala, reusa o `entered=player_room` do
> rastreio de visita); `_disparar_fala` (idempotente) → broadcast `{type:"fala",
> falante, texto, pos}`; `handle_disparar_fala`+dispatch `disparar_fala` (guarda
> `pid==master_pid` + `_mestre_ativo()` + só `manual` + não-disparada). As
> `proximidade`/`sala` disparam **com ou sem mestre** (CPU no papel); a `manual` só
> com mestre humano (ninguém clica sem ele). `push_state` serializa as `manual`
> não-disparadas em `game_state.falas` (p/ o HUD). `validar_dungeon`: texto
> não-vazio, gatilho válido, `pos` no grid. Editor (`tools/editor.js`): ferramenta
> "fala NPC" + entidade `S.falas` + painel (emoji/nome/texto/gatilho/raio) + marcador
> 💬 no mapa + seleção/mover/apagar + save/load + validação. Cliente: `game.js` balão
> com fila (auto-dismiss 5s, clique avança) + seção "💬 Falas" no `renderMasterHud`
> (dispara as manuais); `src/gameState.js` `dispararFala(id)` + evento `fala`.
> Spec: `docs/superpowers/specs/2026-07-16-falas-npc-design.md`. Teste:
> `tools/test_modo_mestre.py` (seção [24]).

> **Modo Mestre — Controle manual do monstro (SP1):** na janela Manual, o monstro
> se move como um herói — as casas alcançáveis (BFS footprint-aware sobre o
> `movement` real, autoritativo em `_master_reach_bfs`/`_master_monster_reach`,
> enviado em `game_state.master_manual_reach`) aparecem em azul; clicar numa delas
> anda até lá via `mestre_mover_monstro_para`→`handle_mestre_mover_monstro_para`
> (path-walk por `_master_path_to` + `_commit_monster_step`, gastando
> `master_moves_left`). As setas do HUD saíram. Clicar num herói no alcance ataca
> (reusa `mestre_atacar_monstro`). A ficha (`renderFichaMonstro`, agora à direita
> abaixo do HUD) ganhou seção **Ações**: habilidades ativas resolvíveis por
> `_use_monster_ability` (save+dc — as do editor de criaturas) têm botão **Ativar**
> (`mestre_usar_habilidade`→`handle_mestre_usar_habilidade`, mira um herói, consome
> a ação via `_master_acted`, mostra usos/recarga de `ability_uses`/
> `ability_cooldowns`); as demais aparecem como "IA apenas"
> (`_habilidade_ativavel_manual` é o ponto de plugagem futuro). Sem mestre,
> byte-idêntico. SP2 (pendente): inventário de itens do monstro. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-17-modo-mestre-controle-manual-monstro-sp1*`.
> Teste: `tools/test_modo_mestre.py` (seções [25]/[26]).

> **Modo Mestre — Inventário do monstro (SP2):** o mestre usa os itens de bolsa da
> criatura e ativa TODAS as habilidades especiais dela na janela Manual. Apoia-se no
> sistema de equipamento já existente (`equipment_enabled`/`equipped_items` →
> `_aplicar_equipamentos_monstro`, que equipa arma/armadura afetando ataque/CA e
> coleta `m["equipment_consumables"]`, os itens `item_slot=="bag"`). **Itens:**
> `use_item`-do-mestre via `mestre_usar_item`→`handle_mestre_usar_item` (reusa
> `_monster_throw_item` p/ arremessáveis mirando um herói; heal/regeneration/atk_bonus/
> coat_poison/antidote/veil_shadow p/ alvo-próprio; pergaminho `scroll` só se
> `_monster_e_conjurador` via `_executar_magia_grimorio`; food/ração/vinho/cerveja
> recusados — sem efeito em monstros). Economia **espelha o jogador**: consumível de
> bolsa = ação bônus (`_master_bonus_acted`), arremesso/pergaminho = principal
> (`_master_acted`), ambos resetados na abertura da janela. Itens não usados caem no
> loot na morte (comportamento de `equipped_items` já existente). **Habilidades de
> editor (herói/guilda):** o SP1 só tornava ativáveis as save+dc; agora as derivadas
> de herói/guilda (`source in {heroi,guilda}`, ex.: Mira Certeira) também são, via o
> helper `_ativar_editor_ability` (extraído de `_monster_try_editor_ability` e
> compartilhado IA+mestre — contadores `monster_ability_uses`/`monster_ability_cooldowns`);
> `_habilidade_ativavel_manual` e `handle_mestre_usar_habilidade` ganharam o ramo (b)
> self-buff (sem alvo). Cliente: `renderFichaMonstro` ganhou seções **Itens** (botão
> Usar; arremessável/pergaminho abrem mira num herói via `_mestreUsarItemFicha`;
> food/só-conjurador rotulados) e **Equipado** (arma/armadura em leitura);
> `ativavel`/`usosRest`/`cdRest` cobrem as duas famílias de contador (`ability_*` vs
> `monster_ability_*`); `mestreUsarItem` em `gameState.js`. Monstro exemplo:
> **"soldado"** em `monstros_personalizados.json`. Sem mestre, byte-idêntico. Spec/
> plano em `docs/superpowers/{specs,plans}/2026-07-17-modo-mestre-inventario-monstro-sp2*`.
> Teste: `tools/test_modo_mestre.py` (seções [27]/[28]).

> **Simulador do editor ("🧪 Testar como Mestre") — mesma tubulação de turno do
> jogo:** a sala descartável (`_criar_sala_teste_masmorra`) tem **heróis-teste**
> (`handle_mestre_adicionar_heroi_teste` → `make_player` + `test_hero=True` +
> `_equipar_kit_heroi_teste`: mago/clérigo recebem TODAS as magias implementadas da
> classe, o ladino um frasco de veneno) e uma **fila própria** `self.test_combat`
> (`_teste_combate_fila/_preparar_ator/_proximo/_avancar/_fechar_vez_atual`),
> deliberadamente separada de `initiative_order`. As ações do herói-teste passam por
> `handle_teste_acao_heroi` (ponte com lista explícita; a ação `hero_skill` supre os
> painéis que a ficha do simulador não tem — `tipo` da Purificação inferido do alvo,
> `bonus` do Guerreiro da Luz por preset, `atributos` da Canção). **Regra:** o
> simulador NÃO tem "preparação enxuta" — cada ator passa pelos MESMOS prólogos do
> jogo real: herói = `_start_initiative_player_turn` ao abrir e
> `_reset_fim_turno_jogador` (extraído de `handle_end_turn`) ao fechar; monstro =
> `_upkeep_inicio_turno_monstro` (False = turno consumido → a fila pula o ator) +
> `_processar_onda_envolvente_turno` + `_preparar_janela_controle_monstro` +
> `_upkeep_inicio_turno_manual`; virada de rodada = `_virada_de_rodada` (extraída de
> `_advance_initiative`). Sem isso recargas, ticks de veneno/chamas, regeneração,
> manutenções de classe, buffs de turno (Golpe Devastador/metamagia viravam
> permanentes) e todo o controle de multidão ficavam congelados ali. Troll a 0 HP
> (`troll_regenerando`) continua na fila (`_teste_combate_monstro_vivo`). **Fix
> irmão na janela Manual real:** `_upkeep_inicio_turno_monstro` grava
> `_cds_antes_prologo` e `_upkeep_inicio_turno_manual` não baixa de novo a recarga
> que o prólogo de espécie já baixou (Explosão de Vapor caía 6→4 por rodada). E o
> mesmo padrão recorrente de [[modo-mestre-manual-pula-gm-phase]] fechado para mais
> espécies: Caça em Bando/Derrubar do lobo (`_lobo_bando_atk`/`_lobo_derrubar`,
> IA+Manual), Mordida Corrosiva do Devorador de Metal (no ataque manual), Fúria Cega
> do orc e Concentração Sombria do necromante (snapshots de HP movidos para o
> prólogo comum; as IAs só leem `furia_cega`/`_sem_magia_turno`), e as técnicas
> `golpe_devastador_troll`/`pressao_constante_troll`/`investida_brutal_troll`
> (contador `_troll_move_count`), `arremesso` do goblin (`_goblin_arremesso_em`) e
> `dominar_morto_vivo` viraram ativáveis em `handle_mestre_usar_habilidade`
> (cliente: `_MP_HAB_EXTRAIDAS`/`_MP_HAB_SEM_MIRA`). Teste:
> `tools/test_simulador_turno.py` (42 checks, dirige a sala real sem navegador).

> **Agarrão de criatura (crocodilo/cobra) — efeito NO ACERTO mora no pipeline de
> ataque:** `agarrar` (Crocodilo, Fort CD 12) e `constricao` (Cobra, Fort CD 11)
> disparavam só dentro de `_ai_crocodilo_jovem`/`_ai_cobra_constritora`, depois da
> chamada de ataque — então sob **controle Manual** (Mestre, Comando, Dominar Mente),
> que ataca por `handle_mestre_atacar_monstro` → `_execute_one_monster_attack`, a
> mordida acertava e nada acontecia. O teste passou para `_agarrao_no_acerto`, chamado
> de dentro de `_execute_one_monster_attack` ao lado de `onda_envolvente`/`infeccao`
> (que sempre funcionaram justamente por estarem lá); a tabela `_AGARRAO_ON_HIT`
> (id → emoji/narração) é o ponto de extensão para novas espécies que agarrem, e a
> CD/save vêm da própria ficha. O dano automático em quem já está preso saiu das duas
> IAs para `_esmagar_preso` + `_preso_adjacente` (tabela `_ESMAGAR_PRESO`: dado padrão
> + narração), agora também **ativável pelo mestre** — `atq_mandibula`/`esmagar` passam
> na frente do corte de `action_type:"passiva"` em `_habilidade_ativavel_manual` e têm
> ramo próprio em `handle_mestre_usar_habilidade` (sem mira: o alvo é sempre o preso;
> custa a ação principal). **Arrastar** virou `_arrastar_preso`, chamado no fim de
> `_commit_monster_step` (comum a IA e Manual): quem está agarrado acompanha o monstro
> mantendo-se adjacente (`_casa_livre_ao_lado`, que prefere a casa recém-liberada e é
> footprint-aware); sem casa livre o agarrão se rompe, em vez de travar o preso. Isso
> substituiu o bloco da IA que teleportava o herói para CIMA do crocodilo. Cliente:
> `_MP_ESMAGAR_PRESO` em `game.js` espelha a exceção nas 3 pontas (filtro de
> `special_abilities` da ficha, `_mpAtivavel` e `_mestreAtivarHabilidade`).
> **O agarrão também prende MONSTRO, não só herói** — o gancho fica fora do ramo
> `is_player` (animados seguem de fora: usam `vida_atual`). Isso era obrigatório
> para a **mesa livre do editor** ("🧪 Testar como Mestre"), que nasce com
> `players = {}` e onde o único alvo possível é outra criatura — ali nenhum efeito
> no acerto contra herói (veneno, infecção, Onda Envolvente) é observável. Também
> cobre Comando/Dominar Mente, os outros dois casos em que `_alvo_manual_mestre`
> aceita alvo-monstro. O estado da criatura agarrada espelha o do herói:
> `_agarrados_por`/`_preso_adjacente` varrem heróis **e** monstros;
> `_commit_monster_step` recusa o passo de quem está preso (guarda `_captor_ativo`,
> que também zera as casas azuis em `_master_monster_reach`); a tentativa de escape
> entra no prólogo compartilhado `_upkeep_inicio_turno_monstro` reusando
> `_processar_escape_agarrar` (que já era genérico), e a falha zera o movimento sem
> tirar o ataque; `_monster_dies` solta heróis e criaturas. Teste:
> `tools/test_agarrao.py` (39 checks, cobre IA, Manual e mesa livre).

> **`ai_type` de espécie vale em ficha personalizada:** `_run_monster_ai` mandava
> TODA ficha com `_personalizado` para `_run_profile_ai`, o que tornava o campo
> `ai_type` inerte nelas — embora `_validate_custom_monster` valide esse campo
> justamente contra os `ai_type` existentes em `MONSTER_DEFS`. Consequência: salvar
> um nativo por cima dele mesmo no Editor de criaturas (`overwrite_native`) trocava
> a IA da espécie por "agressivo" em silêncio (o crocodilo perdia Mandíbula
> automática, arrasto e perseguição; o grotão, a Cauda Varredora; o lagarto, o Combo
> Devorador). Agora o desvio para o perfil genérico só acontece quando o `ai_type`
> é um dos **`AI_PROFILES`** (agressivo/tatico/cacador/conjurador/emboscador/
> protetor/covarde/irracional/sentinela); um `ai_type` de espécie cai na IA nativa
> daquela criatura. Inerte para as fichas existentes, que gravam `ai_type:
> "agressivo"`. **Armadilhas conhecidas do mesmo import** (dados, não código): o
> editor zera `resistances`, reescreve `weaknesses`, perde `garra_attack`/
> `loot_table`, zera `spawn_min/max`, normaliza `size` e — por ligar
> `apply_attribute_damage` mantendo o modificador embutido em `damage` — **dobra o
> bônus de atributo no dano** (o `damage` do editor é só o dado: "1d8", e o motor
> soma o modificador). Além disso `_apply_custom_monsters` força `m["movement"] = 6`
> em toda ficha personalizada, ignorando o valor do arquivo.

> **Hostilidade entre monstros no Bestiário:** cada ficha tem filtros próprios
> em `monster_hostility.json`, editados na aba Bestiário (`tools/editor_bestiary.js`)
> e validados em `server.py`. Os filtros são combinados por OU: todos os monstros,
> qualquer subtipo, ou tipos específicos pelo id estável da ficha. Sem regra,
> continua sem agressão automática entre monstros. A IA considera criaturas vivas
> da mesma sala que consiga perceber; a escolha genérica usa o executor normal de
> ataques e inclui o ataque básico das fichas legadas sem lista `attacks`. Um ataque
> tentado (mesmo se errar) dá ao alvo memória curta do agressor:
> ele prioriza a retaliação no próximo turno normal, procura a última posição
> conhecida se o agressor sair de vista, e esquece após três rodadas. Os modos do
> Mestre preservam o controle manual e os alvos forçados. Testes: `tools/test_monster_hostility.py`
> e `tools/test_modo_publico.py` (handler de gravação protegido no modo público).
> Cada monstro colocado no mapa da masmorra também pode herdar o Bestiário, desligar
> sua hostilidade ou definir filtros próprios de todos/subtipos/tipos. O override é
> salvo em `monsters[].hostility_override`, validado ao carregar a masmorra e tem
> precedência apenas para aquela colocação.

> **Campo de Treinamento — hostilidade (2026-10-08):** a ala 46–48 incorpora
> o layout de `Downloads/campo_de_treinamento (1).json`: a sala 46 ensina a
> abrir a porta, observar os monstros hostis entre si e usar a Granada Superior;
> as práticas de consumíveis ficam na 47 e as de resistência/vulnerabilidade na
> 48. `fala_hostilidade` e seus textos bilíngues vêm de
> `tools/tutorial_guia_comum.py`/`tools/gerar_guia_comum.py`. O campo opcional
> `monsters[].autonomous_hostility` preserva a luta automática ao despertar no
> Modo Mestre apenas para os monstros marcados; outras salas continuam em Manual
> quando despertadas por avistamento. O editor de masmorras mantém esse campo no
> roundtrip. Conhecimento das Lendas mostra “Hostil a todos os monstros” no
> tooltip completo do Bardo quando `hostility_override.rules.all_monsters` vale.
> **Integração da ala 46–48 (2026-10-08):** o layout novo desloca a trilha comum: a antiga sala 22 (consumíveis) virou a **47** (x 41) e a antiga 23 (esqueletos/maça) a **48** (x 48), com a **46** (hostilidade) no lugar da 22 e a saída em [53,15]; as salas 18–21 e todas as exclusivas (35, 38, 40–43) não se moveram. Tudo da antiga 22/23 andou +7 em x (baú dos consumíveis [42,14], maça [49,17], palha [45,17]/[45,18], bonecos de veneno, `fala_29`–`fala_33` em [42,15], `fala_34` [48,15], `fala_atalhos` [49,16], `fala_res`/`fala_vuln` [50,17]; ordens 10 = `fala_hostilidade`, 11–15 consumíveis, 16 `fala_34`) e as `ordem` 17–18 seguem vagas. **Regra que o autor pegou sem querer:** lição plantada DENTRO de uma sala só dispara com o herói nela (`_licao_no_lugar`), então a `fala_hostilidade` em [35,15] (sala 46) só aparecia depois da porta aberta e o passo 1 (`conclui_com abrir_porta` [33,15]) nunca recebia o evento; o marcador agora fica em [32,15], na sala 21, a uma casa da porta (`tools/aplicar_fatia18_tutorial.py`, idempotente). Os scripts `aplicar_fatia7/8_tutorial.py` e `configurar_tutorial_salas.py` usam as coordenadas novas e os testes `test_tutorial_fatia7/8/refem` derivam sala, posição e ordem do JSON (a fila de iniciativa real PULA monstro dormente; o harness do refém começa a vez no herói). Teste: `tools/test_tutorial_hostilidade.py` (layout das salas originais, ordens, fluxo antes da porta, granada, pulo, lutadores se ferindo).

> **Assassino Goblin:** ficha nativa `goblin_assassino`, com estatísticas e arte 2D
> `goblinDual` do Goblin Dual, GLB próprio `assassino_goblin.glb`, IA `goblin_assassin` e habilidades de esconder-se e
> ataque furtivo. Ao ser percebido, tenta Furtividade contra a maior Percepção dos
> heróis que o veem; se passar, fica invisível aos jogadores e espera o turno seguinte.
> Ao atacar, revela-se; o primeiro ataque recebe vantagem e, se acertar, +2d4. O
> monstro usa duas adagas (+4, 1d4+2 cada); mantém o arremesso do Goblin Dual como
> ação bônus, mas não o usa enquanto ainda está escondido. Seu saque garantido é uma
> adaga. Cada exemplar carrega um frasco de Fungo Acre, Dor Escarlate e Tinta do Polvo
> Abissal; um deles recebe ao menos uma melhoria e há 10% de chance de essa dose ter
> as três melhorias máximas (Fatal). Tem 40% de chance de soltar 10 moedas. O Mestre
> ainda vê e seleciona o peão escondido. Começa com a adaga envenenada com Fungo Acre;
> ao acertar, a IA consome a dose aplicada e prepara uma das doses restantes para o
> próximo acerto, respeitando as melhorias do frasco.
> Renderização 2D/3D e destaques de
> alvo ignoram o monstro escondido para os jogadores; o servidor também recusa um
> ataque direto enviado para esse alvo.

> **Editor de Itens — Fase 1 (Armas):** nova aba "Editor de itens" no editor de
> masmorras (`tools/editor.html` + `tools/editor_items_editor.js`); sub-aba
> **Armas** funcional, as outras 7 (armaduras/escudos/anéis/botas/poções/
> arremessáveis/venenos) visíveis mas desabilitadas (fases futuras). **Catálogo
> global vivo:** salvo em `itens_personalizados.json` + índice regenerado
> `tools/editor_items_custom.js` (`window.EDITOR_CUSTOM_ITEMS`), mesclado no boot
> por `_apply_custom_items` em `WEAPONS`/`SHOP_WEAPONS`/`_DUNGEON_ITEM_CATALOG`/
> `LOOT_POOL_PROCEDURAL` (server.py). Handlers WS `upload_custom_item` +
> `upload_item_art` (PNG → `assets/itens/<id>.png`). **Efeitos passivos
> funcionais** no combate (lidos de `p["weapon"]` em `handle_attack`): dado/
> categoria/stat/manejo, **alcance editável** em quadrados (`range`/`throw_range`),
> **acuidade** (`finesse` → dano usa o melhor de FOR/DES), bônus fixo
> **independentes** de ataque (`atk_bonus`) e de dano (`damage_bonus`), dano
> elemental adicional (`extra_damages`, lista de `{die,type}` em
> fire/cold/lightning/acid/holy), **munição** para armas à distância (`ammo`:
> flechas/virotes → registrado em `RANGED_AMMO` no merge), **material**
> (`material`: metal/madeira → registrado em `CORROSAO_ARMA_METAL`/`_MADEIRA`,
> define qual Devorador corrói) e **corrosão em dois eixos** — `corrosao_resistente`
> (N níveis sem penalidade) + `corrosao_niveis_penalidade` (M níveis com penalidade,
> escala −1/nível, quebra em N+M+1; lidos por `_corrosao_arma_pen`/
> `_corroer_equipamento`, byte-idêntico p/ armas base quando M=2). `granted_ability`
> (habilidade de Guilda/herói) é só **metadado** nesta fase. Compra/equipar preservam
> esses campos (whitelists de `handle_shop_buy`/`combat_fields`). **Disponibilidade**
> por item (loja/baús/loot de monstro); armas com `baus=true` aparecem no
> seletor de itens de baú/recompensa do editor (`CAT.items` em `tools/editor.js`).
> **Preço sugerido** e serialização/validação puras em
> `tools/editor_items_logic.js` (reusado pelo teste node). **Copiar-como-modelo:**
> itens base nunca são alterados; todo item salvo é sempre novo (id próprio).
> Testes: `tools/test_editor_itens.py` (servidor) e
> `tools/test_editor_items_logic.js` (node). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-20-editor-itens-fase1-armas*`.
> Fases seguintes: as outras 7 abas + habilidades ativáveis funcionais.

> **Editor de Itens — Fase 2a (Armaduras + Escudos):** habilita as sub-abas
> **Armaduras** e **Escudos** (as outras 5 seguem 🔒). `item_type` `"armor"`/`"shield"`,
> mesmo catálogo global vivo (`itens_personalizados.json`), mesclado por
> `_apply_custom_items` (despacho por `item_type`) em `SHOP_ARMORS`/
> `_DUNGEON_ITEM_CATALOG`/`LOOT_POOL_PROCEDURAL`. Campos: `ac_bonus` (CA base) +
> **motor de multi-efeito** `bonuses:[{effect,value}]` (`def_`/`maxhp`/`spd`, via
> `_apply_single_effect` extraído de `_apply_gear_effect`), `armor_category` (só
> armadura), `granted_ability` (metadado), `allowed_classes`, disponibilidade, preço.
> **Corrosão generalizada** para os slots de defesa (armadura/escudo/elmo/botas), com
> o modelo **N/M** das armas: `_corr` ganhou trilhas por slot; `_corroer_equipamento`
> degrada UMA peça na prioridade **armadura→escudo→arma→elmo→botas** (custom corrói por
> `corrosion_materials`, base por id-set; escudos base `escudo_p`/`escudo_g` agora em
> `CORROSAO_ARMADURA_METAL`); a penalidade (`_corrosao_ca_pen` CA; `_corrosao_spd_pen`
> velocidade em `_moves_base`) lê o N/M **cacheado** em `_corr` no momento da corrosão,
> então **persiste após a destruição**. Peças base sem N/M usam N=0/M=2 → byte-idêntico
> (uma correção só na destruição: CA vira base em vez de base−1; `test_devorador` ajustado).
> Elmo/botas ficam **engine-ready** (UI de material/N/M deles na sub-aba futura; base
> não recebe material). Compra/equipar preservam os campos (ramo `ferreiro_armor` +
> whitelists). Cliente: `serializeArmor`/`validateArmorDraft`/`suggestPriceArmor` em
> `editor_items_logic.js`; formulário armadura/escudo em `editor_items_editor.js`;
> `CAT.items` do editor de masmorras inclui armaduras/escudos custom. Testes:
> `tools/test_editor_itens.py` (seções [A1]-[A6]) + `tools/test_editor_items_logic.js`.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-07-21-editor-itens-fase2a-armaduras-escudos*`.
> Fases seguintes: **B** bônus de atributo (motor), **C** resistências de dano, **D**
> iniciativa; depois anéis/botas/poções/arremessáveis/venenos + habilidades ativáveis.

> **Editor de Itens — Fase B (motor de bônus de atributo):** os efeitos `str_`/`dex`/
> `con_`/`int_` na lista `bonuses` do motor de multi-efeito passam a ser **funcionais**.
> `_apply_single_effect` despacha esses efeitos para `_apply_attribute_delta(p, attr,
> delta)`, que muda o **atributo bruto** (`p[attr]`) e ajusta os derivados
> **armazenados** por Δ do modificador: **acerto** (`atk_bonus`/`base_atk_bonus`) só para
> a classe cujo atributo de ataque bate (`_CLASS_ATK_ATTR`: warrior/mage/cleric/paladin→
> `str_`, rogue/bard/ranger→`dex`); **CA** (`ac`/`ac_base`) e **Reflexos** (`ref_`) para
> DES; **Fortitude** (`fort`) e **PV máx** (`max_hp += Δ(get_bonus_constituicao)×nível`,
> com top-up de HP travado pelo Último Esforço) para CON; **Vontade** (`will`) para INT.
> **Dano, visão** (`_get_raio_visao` lê int/dex/spd) **e iniciativa** (`initiative_value`
> = dex + mod(int)) se atualizam **sozinhos** (leem o bruto). É **simétrico** e
> **independente de ordem** (o Δmod telescópica), então empilhar/remover itens sempre
> volta ao estado inicial. Validação (`_ITEM_BONUS_EFFECTS`) e editor (`BONUS_EFFECTS` +
> dropdown de bônus adicionais em `editor_items_editor.js`) ganharam as 4 opções.
> **Limitação conhecida** (aceita, igual ao veneno): subir de nível com item de +CON
> equipado pode dessincronizar o `max_hp`. Testes: `tools/test_editor_itens.py` [B1]-[B5].
> Spec/plano em `docs/superpowers/{specs,plans}/2026-07-21-editor-itens-fase-b-atributos*`.
> Fases seguintes: **C** resistências de dano do herói, **D** iniciativa como campo próprio.

> **Editor de Itens — Fase C (resistências de dano do herói):** um efeito **`resist`**
> na lista `bonuses` do motor de multi-efeito **adiciona/remove uma entrada em
> `p["resistances"]`** ao equipar/desequipar (via `_apply_resistance` no laço de
> `_apply_gear_effect`; roteado para lá em vez do `_apply_single_effect` escalar). A
> entrada carrega um `type` (um de `_RESIST_TYPES`, os 9 tipos de dano) e um modo pela
> convenção do `value`: **value≤0 → metade** (`{type,mode:"half"}`), **value>0 → redução
> fixa** (`{type,reduction:N}`). Como `_apply_damage_types` já é **genérico pelo alvo**
> (lê `target["resistances"]`) e é chamado com o jogador como alvo nos caminhos de dano
> tipado (ataque de monstro/elementais, armadilhas, gás/ácido, fogo…), a redução vale
> **automaticamente** — zero mudança nos ~24 sites. Empilha (uma entrada por item;
> desequipar remove uma igual). Validação (`_ITEM_BONUS_EFFECTS`+`resist`) **preserva o
> `type`** (descarta tipo desconhecido/ausente); cliente: `serializeArmor` preserva o
> `type` (`RESIST_TYPES`) e o editor tem um **dropdown de tipo** que só aparece quando o
> bônus é "Resistência". Testes: `tools/test_editor_itens.py` [C1]-[C3] + node. Fora de
> escopo: imunidade total e vulnerabilidade do herói. Fase seguinte: **D** iniciativa
> como campo próprio.

> **Editor de Itens — Fase D (bônus de iniciativa):** efeito escalar **`initiative`**
> no motor de multi-efeito (`_apply_single_effect`, ramo igual ao de `spd`) →
> `p["initiative_bonus"]`, somado em `initiative_value` (junto de `dex + mod(int)`).
> Vale a partir do próximo `_rebuild_initiative` (por encontro — igual ao efeito de
> DES/INT da Fase B). Valor pode ser **negativo** (armadura pesada −2). Validação
> (`_ITEM_BONUS_EFFECTS`) + cliente (`BONUS_EFFECTS` + opção "Iniciativa" no dropdown de
> bônus adicionais) ganharam o efeito; por ser escalar, cai no caminho comum do
> `serializeArmor` (sem tratamento especial como o `resist`). Fecha o trio **B/C/D** do
> Editor de Itens. Testes: `tools/test_editor_itens.py` [D1] + node. Fases seguintes: as
> outras sub-abas (anéis/botas/poções/arremessáveis/venenos) + habilidades ativáveis.

> **Faixa de iniciativa multiplayer:** `game_state` já envia `initiative_order` e
> `current_actor`; o cliente (`game.js`) mostra a ordem autoritativa numa faixa
> horizontal independente, imediatamente acima do log `#gm-log` (“MESTRE DO JOGO”).
> A faixa inclui heróis e monstros, destaca o ator atual e desloca a fila para mantê-lo
> visível quando necessário. Ela se oculta no modo de combate de teste, que tem fila
> própria, e permanece visível quando o log é minimizado.

> **Resumo pré-turno multiplayer:** logo abaixo da iniciativa e acima do log, o cliente
> mostra um painel apenas para o herói que está agindo ou será o próximo na fila. Ele
> resume dano/cura e condições recebidos desde a última vez, PV/condições atuais,
> inimigos visíveis ao alcance do ataque básico, slots de magia livres e aliados feridos.
> Alvos são filtrados pela visão local; dados vêm do `game_state`, sem alterar regras,
> turnos ou permissões. O painel se oculta para mestre, jogadores fora da vez e modo de teste.

> **Editor de Itens — bônus de visão:** efeito escalar **`vision`** no motor de multi-efeito
> (`_apply_single_effect`, mesmo ramo de `spd`/`initiative`) → `p["vision_bonus"]`, somado em
> `_get_raio_visao` **antes** do piso `max(1, …)`, ao lado do bônus de atributos e do Guerreiro
> da Luz — vale para heróis (raio de revelação da névoa em quadrados). Aceita negativo. Está no
> allow-list `_ITEM_BONUS_EFFECTS` (server) / `BONUS_EFFECTS` (`editor_items_logic.js`) e no
> dropdown "bônus adicionais" dos 4 forms de gear (armadura/escudo/anel/bota) como "Visão
> (quadrados)". Junto veio um fix do preview de armadura, que rotulava qualquer efeito fora de
> `def_/maxhp/spd` como "Velocidade" — os dois previews agora compartilham `BONUS_LBL`/
> `bonusLabel` em `editor_items_editor.js`. Testes: `tools/test_editor_itens.py` [M1] + node.

> **Editor de Itens — Fase E (Anéis + Botas):** destrava as sub-abas **Anéis** e
> **Botas** (as outras 3 seguem 🔒). Acessórios reusam o **motor de multi-efeito**
> (`bonuses:[{effect,value}]`) — sem CA-base nem `armor_category`; todo efeito vem da
> lista `bonuses`. `item_type` `"ring"`/`"boots"`, validados por
> `_validate_custom_accessory` (dispatch em `_validate_custom_item`), mesclados por
> `_apply_custom_items` no **mercador** (`SHOP_MERCHANT` — nova linha de cleanup dos
> customs, já que nenhum outro bloco o limpava) + `_DUNGEON_ITEM_CATALOG`/
> `LOOT_POOL_PROCEDURAL` (baús/loot). `_custom_accessory_inventory_dict` gera um dict
> único p/ loja e bolsa/baú (como os anéis nativos). O **equip já era funcional**:
> `_slot_category_for_item` mapeia `item_slot:"ring"`→`ring1`/`ring2` e
> `item_slot:"boots"`→ slot dedicado `boots`; `_apply_gear_effect` aplica a lista
> `bonuses`. **Novo efeito `atk_bonus`** (bônus fixo de acerto) adicionado a
> `_ITEM_BONUS_EFFECTS` (server) e `BONUS_EFFECTS` (cliente) — vale para anéis, botas
> **e** armaduras/escudos (motor compartilhado); `_apply_single_effect` já o tratava.
> **Botas corroem** só via `corrosion_materials` no dict (`_peca_corroivel` corrói
> peça custom por interseção de material; o slot `boots` já está no laço de
> `_corroer_equipamento`) — **não** são registradas nos sets `CORROSAO_ARMADURA_*`
> (evita poluir a detecção de metal dos monstros). **Anéis não corroem.** Cliente:
> `serializeAccessory`/`validateAccessoryDraft`/`suggestPriceAccessory` em
> `editor_items_logic.js` (filtro de bônus extraído p/ `filterBonuses`, DRY com
> `serializeArmor`); `editor_items_editor.js` destrava as sub-abas + form parametrizado
> (`renderAccessoryForm`, corrosão só em botas, rótulo "Loja (Mercador)"), com o
> template de bônus compartilhado `abonusTemplate` e a indireção `previewFn` (para as
> linhas de bônus reusarem o maquinário da armadura sem quebrar no preview de anel).
> Testes: `tools/test_editor_itens.py` [E1]–[E5] + `tools/test_editor_items_logic.js`.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-07-22-editor-itens-fase-e-aneis-botas*`.
> Fases seguintes: poções/arremessáveis/venenos (subsistemas próprios) + `granted_ability`
> ativável.

> **Editor de Itens — Fase F (Poções):** destrava a sub-aba **Poções** (as outras 2 —
> arremessáveis/venenos — seguem 🔒). Poções são **consumíveis de bolsa**
> (`item_slot:"bag"`) despachados por `effect` em `handle_use_item`; os 3 efeitos do
> escopo (`heal` com multi-dose, `regeneration`, `atk_bonus`) **já estão implementados**
> para o jogador, então esta fase **não toca no motor de combate** — só validar/mesclar/UI.
> `item_type:"potion"` → `_validate_custom_potion` (dispatch em `_validate_custom_item`;
> efeito validado contra o novo set `_ITEM_POTION_EFFECTS`; `max_uses`/`uses_left` só p/
> `heal`; protege ids nativos da união `SHOP_MERCHANT ∪ SHOP_TEMPLE ∪ SHOP_TAVERN`).
> `_custom_potion_inventory_dict` = dict plano único p/ loja e bolsa/baú. Merge por
> `_apply_custom_items` no **mercador** (`SHOP_MERCHANT`) + `_DUNGEON_ITEM_CATALOG`/
> `LOOT_POOL_PROCEDURAL` — **cleanup herdado** da Fase E (a linha do `SHOP_MERCHANT` + o
> bloco genérico `prev_custom_ids`; sem código de limpeza novo). O `atk_bonus` de poção
> (buff temporário do turno via `blessed`) é distinto do `atk_bonus` de gear da Fase E
> (lista `bonuses`) — sem colisão, pois a poção é consumível por `effect`. Cliente:
> `serializePotion`/`validatePotionDraft`/`suggestPricePotion` + `POTION_EFFECTS` em
> `editor_items_logic.js`; `editor_items_editor.js` destrava a sub-aba com `renderPotionForm`
> (seletor de efeito com rótulos amigáveis; campo Doses só p/ Cura, re-render no toggle como
> o `ie-manejo` das armas; rótulo "Loja (Mercador)"). Testes: `tools/test_editor_itens.py`
> [F1]–[F4] (inclui uso ponta-a-ponta via `handle_use_item` — cura/regen/buff + multi-dose)
> + `tools/test_editor_items_logic.js`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-23-editor-itens-fase-f-pocoes*`. Fases seguintes:
> arremessáveis/venenos (subsistemas próprios) + antídoto/cura de status (ramo novo no
> `handle_use_item`) + `granted_ability` ativável.

> **Editor de Itens — Fase G (Arremessáveis):** destrava a sub-aba **Arremessáveis** (só
> **Venenos** segue 🔒). Cobre os **dois modos de mira** do subsistema: `ataque_alvo` (teste de
> ataque por DES vs CA) e `area` (raio + save de Reflexos, metade no sucesso), com dano+elemento
> e o status **em chamas**. `item_type:"throwable"` → `_validate_custom_throwable` (dispatch em
> `_validate_custom_item`; `alvo` em `_ITEM_THROW_TARGETS`, `elemento` em `_ITEM_THROW_ELEMENTS`,
> alcance clamp 1–12, `area_raio` 1–3 e `save {tipo:"reflexos",cd}` só na área, `chamas_dur`/
> `chamas_agua_apaga` quando `em_chamas`; protege ids nativos da união das 3 lojas **∪
> `ARREMESSAVEIS`**). `_custom_throwable_defn` gera a entrada de `ARREMESSAVEIS` no formato
> nativo (marcada `custom:True` para o **cleanup próprio** em `_apply_custom_items`, espelhando
> o `prev_weapon_ids` de `WEAPONS`); `_custom_throwable_inventory_dict` é o dict de bolsa/loja e
> **carrega os metadados de mira** (`alvo`/`alcance`/`area_raio`). Merge no mercador +
> `_DUNGEON_ITEM_CATALOG`/`LOOT_POOL_PROCEDURAL` (limpeza de loja/baús/loot herdada da Fase E).
> **`handle_throw_item`/`_throw_item_alvo`/`_throw_item_area` ficam intocados** — leem tudo do
> `defn`. **Primeira fase do Editor de Itens a tocar o cliente de jogo:** a mira é decidida por
> `CATALOGO_ITENS[item.id]` (catálogo ESTÁTICO em `src/gameState.js`, que não conhece customs),
> então dois pontos ganharam fallback para os campos do próprio item — `resolveTileClick`
> (`src/gameState.js`, ramo `pendingThrow`: `… || th.alvo || 'ataque_alvo'`) e
> `_iniciarMiraArremesso` (`game.js`: `alvoTipo`/`alcance`/`area_raio` + `alvo` no
> `GS.pendingThrow`). Itens **nativos** mantêm a precedência do `CATALOGO_ITENS` (comportamento
> inalterado). Cliente: `serializeThrowable`/`validateThrowableDraft`/`suggestPriceThrowable` +
> `THROW_TARGETS`/`THROW_ELEMENTS` em `editor_items_logic.js`; `renderThrowableForm` com campos
> condicionais (área/dano/chamas re-renderizam no toggle, padrão do `ie-manejo`). **Fora de
> escopo:** efeitos bespoke do catálogo nativo — ácido residual (`residual`/`corrosao_ac`),
> controle (`controle`, cola/rede), zonas (`zona`, fumaça) e água benta. Testes:
> `tools/test_editor_itens.py` [G1]–[G4] (inclui arremesso mirado e de área ponta-a-ponta via
> `handle_throw_item`) + `tools/test_editor_items_logic.js`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-26-editor-itens-fase-g-arremessaveis*`.

> **Editor de Itens — Fase H (Venenos):** destrava a sub-aba **Venenos** e **fecha as 8
> sub-abas** do editor. Cobre as **5 operações** de `VENENOS`: `dano` (com os 2 modelos de
> resistência — `save_aplicacao`, testa 1× ao aplicar, ou `save_neutraliza_por_rodada`, testa a
> cada rodada), `reduzir` (atributo via `_VENENO_ATTR_MAP`; CON recalcula PV/Fortitude sozinho),
> `penalidade` (pares `[chave, valor]` em ataque/movimento/dano/ca/percepcao), `petrificar` e
> `cegar` (ambos com `duracao_falha`/`penalidade_falha` do sucesso parcial; `cegar` ainda com
> `penalidade_ataque` e `bloqueia_distancia`). **Um veneno vive em DUAS estruturas** — a entrada
> de `VENENOS` (definição do efeito) e um item de bolsa `effect:"coat_poison"` com `veneno_id`;
> nos nativos o id do item e a chave do veneno são o MESMO string, convenção mantida aqui.
> `item_type:"poison"` → `_validate_custom_poison` (sets `_ITEM_POISON_OPS`/`_ATTRS`/`_PENS`/
> `_SAVES`; CD clamp 1–40; duração/valores aceitam dado `NdX` ou int; protege ids nativos das 3
> lojas **∪ `VENENOS`**). `_custom_poison_defn` gera a entrada de `VENENOS` no formato nativo
> (`nome`/`icone`), marcada `custom:True` para o **cleanup próprio** (mesmo padrão de
> `ARREMESSAVEIS`); `_custom_poison_inventory_dict` é o frasco de bolsa/loja e carrega
> `veneno_id` + **`descricao`/`efeito {save,dificuldade,anula}`**, exatamente o que o tooltip do
> cliente já lê. **`_aplicar_veneno` fica intocado** — é data-driven nas 5 operações. **Cliente
> sem mudanças:** `coat_poison` é genérico (loja filtra por `effect`, tooltip lê do próprio
> item, uso pelo caminho comum de `use_item`). Único retoque fora da região de itens custom: a
> mensagem de `penalidade` em `_aplicar_veneno` era hardcoded ("−1 ataque e −1 movimento") e
> agora é montada dos pares reais — com valores custom ela mentia. Testes:
> `tools/test_editor_itens.py` [H1]–[H5] (inclui untar a arma → acertar → envenenar, e os ramos
> `reduzir`/`cegar`) + `tools/test_editor_items_logic.js`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-26-editor-itens-fase-h-venenos*`. **Com esta fase, as 8
> sub-abas do Editor de Itens estão completas**; o que resta são `granted_ability` ativável
> (habilidades concedidas por item) e antídoto/cura de status.

> **Editor de Itens — estoque por cidade (checkbox "Loja"):** com as lojas por cidade
> (`city_shops.json`), o catálogo global (`SHOP_WEAPONS`/`SHOP_ARMORS`/`SHOP_MERCHANT`) diz o que
> **existe** e a allow-list de ids de cada cidade diz o que a loja **vende** (`_city_shop_items`).
> Por isso o checkbox "Loja" sozinho não fazia o item custom aparecer em jogo. Agora o formulário
> tem um **seletor de cidades** (checkboxes na seção Disponibilidade dos 6 forms, desabilitados
> quando "Loja" está desmarcado): ao salvar, o cliente manda `cidades_loja` em `upload_custom_item`
> e `_save_custom_item(raw, city_ids)` chama `_sync_custom_item_city_stock(item, city_ids, old_id)`,
> que **retira o id de todas as lojas antes de inserir** (cobre renomear, trocar de tipo e desmarcar
> "Loja") e grava o `city_shops.json`. A loja de destino vem de `_custom_item_shop_id`
> (arma→`ferreiro_weapon`; armadura/escudo→`ferreiro_armor`; anel/bota/poção/arremessável/veneno→
> `mercador`), espelhado no cliente por `shopIdForItemType` (`editor_items_logic.js`) — há teste de
> sincronia dos dois mapas. `cidades_loja` ausente (cliente antigo) **não** mexe no estoque.
> **Fix de ordem de boot:** `_load_city_shops()` filtra os ids contra o catálogo vivo e roda antes
> de `_apply_custom_items`, então apagava todo id custom do estoque a cada boot (inclusive os
> adicionados pelo Editor de Cidades) — passou a rodar **de novo** logo após o merge dos customs.
> O `city_shops.json` continua sendo a **fonte única** do estoque: o item não guarda a lista de
> cidades; o editor lê o estoque atual para pré-marcar os checkboxes. Testes:
> `tools/test_editor_itens.py` [L1]–[L4] + `tools/test_editor_items_logic.js`.

> **Editor de Itens — Fase I (habilidades concedidas por item):** `granted_ability` deixa de ser
> metadado e vira poder real nos **5 tipos de item equipável** (arma/armadura/escudo/anel/bota).
> O núcleo é um helper module-level **`_habilidades_concedidas(player)`** (varre TODOS os slots
> de `gear` — assim elmo/acessórios futuros funcionam sem mexer aqui) + a extensão de **dois
> portões de uma linha**: `tem_espec` e `tem_tecnica_equipada` passam a aceitar
> `guild_<id>` vindo de um item. Com isso, **técnicas da Guilda** viram ativáveis (botão no HUD
> com efeito, recarga, custo e mira REAIS — reusa `handle_usar_tecnica`, sem tocar nos efeitos) e
> **especializações** viram passivas sempre-ativas. Como `technique_cooldowns` é indexado pelo id,
> ter a técnica no slot da Guilda **e** num item compartilha a mesma recarga (sem uso duplo); a
> restrição de classe da técnica é respeitada (o cliente só renderiza o que está em
> `guildCatalogFor`). **Fix necessário:** `handle_usar_tecnica` fazia a checagem **inline**
> (`tecnica_id not in (eq.get("tecnica"), eq.get("tecnica_exclusiva"))`) em vez de chamar o
> portão — sem passar a usar `tem_tecnica_equipada`, a concessão por item não chegava ao handler.
> **Amostra de 3 habilidades de herói** (`hero_<classe>_<skill>`): Detectar Armadilhas e Esconder
> nas Sombras (Ladino) e Imposição das Mãos (Paladino) — a trava de classe virou
> `class_id != X and <id> not in _habilidades_concedidas(p)`, e as mensagens que citavam
> "Richard"/"Luccas" como donos exclusivos foram generalizadas. `GRANTED_HERO_SKILLS` (mapa
> id→(classe, skill)) + `_granted_hero_skills(p)` injetado no `push_state` mandam a **definição
> real** da skill ao cliente (sem duplicar nomes/custos lá). **Por que só 3:** `handle_skill` é
> **legado e inerte** (retorna cedo; o guerreiro arma as habilidades no cliente e o efeito ocorre
> em `handle_attack` via `buffs`) — cada habilidade de classe é mensagem+handler+trava+painel
> próprios (há 24 checagens `class_id != …`), várias acopladas ao maquinário da classe. As outras
> ~17 ficam para uma **Fase J** com o padrão já validado. Validação: `_granted_ability_valida`
> rejeita ids não suportados nos 3 validadores (antes qualquer string virava metadado morto).
> Editor: o seletor "Habilidade concedida" — que só existia em armas — agora está nos 5 forms,
> com opções **filtradas e agrupadas** (Técnicas / Especializações / Herói). Cliente: técnicas
> concedidas entram no laço do 4º slot com rótulo **"ITEM"**; habilidades de herói ganham um bloco
> que reusa `_rogueSkillBtn`/`_paladinSkillBtn` (ambos agnósticos de classe). Testes:
> `tools/test_editor_itens.py` [I1]–[I6] + `tools/test_guilda.py`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-27-editor-itens-fase-i-habilidades-concedidas*`.

> **Fase J (habilidades de herói restantes concedidas por item):** completa o padrão da Fase I
> com mais **11 habilidades** — **14 no total**. Núcleo: **portão único**
> `_pode_hab_heroi(player, cls_id, aid)` (classe dona OU item concede) + `_tem_alguma_hab_heroi`
> (classe dona OU **qualquer** id de um conjunto — usado pelos upkeeps, que cobrem várias
> sustentadas de uma vez). As 3 travas da Fase I foram **retrofitadas** para o helper, então há um
> só padrão no código. **15 sites** tocados: clérigo (`handle_cura`, `handle_cura_area`,
> `handle_purificacao`, `handle_ressurreicao`), ladino (`handle_criar_armadilha`,
> `handle_veneno_rapido`), paladino (`handle_golpe_sagrado` + `desativar`, `handle_protetor` +
> `desativar`, `handle_acao_livre_richard`, `_processar_manutencao_richard`) e bardo
> (`handle_provocacao` + `_provocador`, que exigia `class_id=="bard"` e mataria os bônus da
> provocação concedida). Em `handle_acao_livre_richard` a trava passou a ser lida **depois** do
> `habilidade_id`, gateando por `hero_paladin_<habilidade_id>` — conceder Regeneração Divina não
> libera Guerreiro da Luz. **Fix de uma lacuna da Fase I:** os dois upkeeps
> (`_processar_inicio_turno_luccas`, `_processar_manutencao_richard`) eram travados por classe, de
> modo que uma habilidade **concedida** nunca pagava manutenção — agora pagam. Sem mudança em
> `_capacidade_poison_melee` (já retorna o base 1 para não-ladinos). Cliente: o bloco de
> habilidades concedidas ganhou os despachos de `_clericSkillBtn`/`_bardSkillBtn` (os quatro
> helpers de botão são agnósticos de classe). Editor: `GRANTED_HERO_IDS` cresceu para 14, com um
> **teste de sincronia** ([J6]) que lê o JS e compara com `GRANTED_HERO_SKILLS` — necessário
> porque `editor_catalog.js` é gerado e não podia ser regenerado. **Fora de escopo (Tier 3):**
> Canção Heroica, Animar Mortos, metamagias, Usar Instrumento (exige instrumento no `off_hand`),
> Mira/Golpe/Fúria do guerreiro (não têm handler — são armadas no cliente e aplicadas em
> `handle_attack` via `buffs`), Ataque Furtivo (passiva) e as 3 magias de MP legadas. Testes:
> `tools/test_editor_itens.py` [J0]–[J6] + as suítes de classe (`test_guilda`,
> `test_paladino_espec`, `test_bardo_espec`, `test_ladino_espec`, `test_clerigo_espec`). Spec/plano
> em `docs/superpowers/{specs,plans}/2026-07-27-fase-j-habilidades-heroi-concedidas*`.

> **Antídotos e curas de status (consumíveis):** três itens que **curam um status e imunizam
> temporariamente** contra ele — **Antídoto** (veneno), **Óleo Dissolvente** (petrificação) e
> **Elixir Depurativo** (doença), todos no mercador com `imunidade_dado:"1d4"`. A lógica de cura
> vivia **inline** dentro de `handle_purificacao`; foi extraída para `_curar_veneno_status` (reverte
> `efeitos_veneno` + cegueira) e `_curar_petrificacao` (`_curar_doenca` já existia), e a Purificação
> do clérigo passou a chamá-las. **Imunidade temporária genérica:**
> `_conceder_imunidade_status(p, status, rodadas)` grava `p["imunidades_status"][status] =
> round_num + N` (rodada absoluta, como os demais buffs) e `_imune_a_status(p, status)` lê;
> `_STATUS_IMUNIZAVEIS = {veneno, petrificacao, doenca}`. São **4 pontos de bloqueio**, levantados
> das fontes reais: `_aplicar_veneno` (veneno), o ramo `petrificar` do veneno **e** a habilidade de
> monstro `effect == "petrificado"` (fonte independente — por isso a imunidade à petrificação não é
> redundante), e o topo de `_aplicar_doenca`. **Três efeitos de consumível** (`cure_poison`/
> `cure_petrification`/`cure_disease`) em `handle_use_item`, como ação bônus: curam o alvo e
> concedem a imunidade rolando `imunidade_dado`. O item **é consumido mesmo sem o status presente**
> (imunidade preventiva é uso legítimo); a narração distingue os dois casos. **Alvo:** `use_item`
> ganhou **`target_id` opcional** (ausente = quem usou, retrocompatível); com alvo, valida jogador
> vivo e **adjacente** (`_no_raio ≤1`) **antes** do bloco de ação bônus, então alvo inválido não
> gasta item nem ação. Cliente: a decisão de mira mora dentro de `useItem` (game.js) — se o efeito
> é de cura e não veio alvo, abre o `openTargetModal` com o próprio herói + aliados adjacentes (com
> só o próprio por perto, o modal é pulado); `src/ui/inventoryModal.js` **não mudou**. **Mudança de
> gameplay:** o `antidote` nativo era `effect:"heal", value:6` — curava 6 HP e **não removia veneno
> nenhum** apesar do nome; agora cura de verdade. Editor: os 3 efeitos entram em
> `_ITEM_POTION_EFFECTS`/`POTION_EFFECTS` e o form da sub-aba Poções troca "Valor/Doses" pelos
> campos do **dado de imunidade**. Testes: `tools/test_editor_itens.py` [K1]–[K6] +
> `tools/test_editor_items_logic.js`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-28-antidotos-cura-de-status*`.

> **Cidades editáveis (editor):** a aba "🏘️ Cidades" do editor de cidades cria cidades novas,
> edita as existentes (nome/tipo/imagem) e as exclui. As 4 originais continuam declaradas em
> `WORLD_LOCATIONS`/`WORLD_ROUTES` como base imutável (snapshot em `_BUILTIN_WORLD_LOCATIONS`/
> `_BUILTIN_WORLD_ROUTES`); `cidades_personalizadas.json` é a camada por cima
> (`cities`/`overrides`/`deleted`/`routes`), aplicada no boot e no save do editor pela MESMA
> função `_aplicar_estado_cidades` — arquivo e edição ao vivo não podem divergir. Um arquivo
> **ilegível** (≠ ausente) liga `WORLD_CITIES_OK=False` e **bloqueia salvar**, senão o save
> gravaria a perda. Lojas (`CITY_SHOPS`), pontos (`CITY_MAP_POINTS`) e cenas (`CITY_SCENES`)
> são derivados: toda cidade ganha entrada vazia e as excluídas somem
> (`_sincronizar_cidades_derivadas`; no boot cada subsistema se semeia na própria declaração,
> **antes** do seu loader — ordem load-bearing). Cidade nova nasce **vazia** (sem lojas, sem
> pontos, sem cenas — `{}`), e o editor de cenas mostra o upload de fundo e o "+ Adicionar NPC"
> também com a cena vazia. **Mudança de regra:**
> `WORLD_ROUTES` virou tabela de **preços** — par sem entrada = viagem grátis
> (`handle_world_travel`), e `broadcast_city_state`/`_city_shops_editor_payload` emitem uma rota
> para TODOS os pares via `_tabela_rotas()`, então o cliente (`game.js`) **não mudou** e nunca vê
> destino bloqueado. O handler `_save_world_cities_upload` recusa `routes` vazio (zeraria os
> custos originais). `alva_e_luz` (`CITY_INICIAL`) nunca é excluível e é o fallback das salas cuja
> cidade sumiu. x/y: das **originais** vem do arraste no mapa-múndi (`world_map_points.json`, o
> painel nem mostra os campos); das **criadas** viaja no payload. Upload da ilustração:
> `upload_city_art` → `assets/city/`. Teste: `tools/test_cidades_editor.py` (64 checks). Spec/plano
> em `docs/superpowers/{specs,plans}/2026-07-28-editor-cidades-nova-cidade*`.

> **Pontos da ilustração da cidade — `CITY_MAP_POINTS` é a fonte única:** o cliente **não**
> desenha mais nenhum marcador fixo. Os hotspots nativos de `_CTY_BLDGS` e a Caravana embutida
> (`game.js`) só aparecem quando existe um ponto com o **mesmo id** em
> `game_state/city_state.city_map_points`; sem isso eles duplicavam o ponto equivalente criado no
> editor e ficavam numa posição fixa que o editor não listava nem reposicionava. Marcadores
> criados a partir de pontos do editor levam `dataset.cityExtra` e são **removidos** quando o
> ponto some (antes ficavam presos até rebuildar a cidade). Do lado do servidor,
> `_garantir_pontos_implicitos()` materializa como ponto editável tudo que a cidade mostraria
> sozinha — a **Caravana de Viagem** (sempre) e o **prédio de cada loja existente** (`_PONTO_LOJAS`,
> posições em `_PONTO_PADRAO`) — pulando o tipo que já tenha um ponto autoral (mesmo com outro id),
> para não duplicar. Roda em `_sincronizar_cidades_derivadas` (boot + save de cidades) e em
> `_save_city_shops_upload` (abrir uma loja nova numa cidade cria o ponto do prédio na hora).
> `handle_city_map_points` (ajuste "📍 Ajustar pontos" em jogo) passou a fazer `update` de x/y em
> vez de substituir o dict — antes o ajuste apagava `type`/`name` do ponto autoral. Teste:
> `tools/test_cidades_editor.py` seção [12].

> **Ponto da cidade vinculado a uma masmorra:** um ponto da ilustração pode ser uma **entrada
> de masmorra** — `type:"dungeon"` (que já existia na allow-list, sem nunca ser oferecido pelo
> editor) mais o campo novo **`aventura`**, o id de um destino do mapa-múndi (`WORLD_ADVENTURES`).
> **Nenhuma mensagem nova:** o clique confirma via `world_adventure`, o mesmo handler do
> mapa-múndi, então requisito, custo 🍖/💧, etapa encadeada, revisita, história e a trava de
> anfitrião vêm de graça. **Validação assimétrica de propósito:** `_save_city_shops_upload`
> (save do editor) só preserva `aventura` se o destino **existir** — id órfão perde o campo e o
> ponto continua salvo; `_load_city_map_points` (boot) checa **só o formato**, como já faz com
> `scene`, porque um `world_adventures.json` ausente/corrompido zeraria `WORLD_ADVENTURES` e uma
> checagem de existência ali apagaria todos os vínculos da memória — que o próximo save do
> editor gravaria em disco. **Spoiler:** `city_map_points` viaja inteiro no payload, então
> `GameRoom._city_points_payload()` (cópia rasa, usada em `_city_state_payload`) remove os pontos
> de masmorra cujo destino não passa em `_aventura_visivel` — nem o id do destino oculto chega ao
> cliente; destino visível porém bloqueado permanece e o clique explica o que falta. O payload do
> editor (`_city_shops_editor_payload`) **não** filtra e ganhou `adventures:[{id,nome,dungeons}]`
> para o `<select>`. Cliente: `pointAllowed` ganhou o ramo `dungeon` (só desenha com destino em
> `world.adventures`), `_cityHotspotClick` abre `abrirEntradaMasmorra` (overlay
> `#city-dungeon-entry`) em vez do legado `triggerDungeonEntrance` (que segue no arquivo, servindo
> o botão oculto); as regras de custo/etapa/requisito/anfitrião saíram do painel do mapa-múndi
> para `_adventureInfo`/`_adventureGoButton`, compartilhados pelas duas telas. Editor
> (`tools/editor_city.js`): **dois botões** de criar — "+ Adicionar ponto (loja/local)" e
> "+ Adicionar entrada de masmorra" —, `dungeon` **fora** do dropdown de tipo (o tipo só se obtém
> pelo botão dedicado) e formulário próprio com "Destino vinculado" + aviso quando falta destino
> ou o destino não tem masmorra. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-04-ponto-de-cidade-vinculado-a-masmorra*`. Teste:
> `tools/test_cidades_editor.py` seções [13]-[15].

> **Masmorra sequenciada + saída individual pela escada:** duas mudanças no fluxo de
> expedição. **(1) Etapas encadeadas:** cada etapa de uma aventura do mapa-múndi
> (`WORLD_ADVENTURES[...]["dungeons"]`) aceita **string (legado) ou objeto
> `{file, encadear, intro, outro}`** — normalizado por `_etapa_obj`/`_etapa_file`, mesmo
> padrão de `_fase_obj`/`_fase_file` das campanhas. Com `encadear`, `handle_encerrar_missao`
> chama `_emendar_proxima_etapa`, que carrega a próxima masmorra e entra nela **sem** passar
> por `_voltar_para_cidade` — e como é justamente `_voltar_para_cidade` quem recarrega slots,
> zera `technique_cooldowns` e renova refeições, o "**nada se recupera**" sai de graça (HP,
> fome/sede, slots, recargas e status atravessam a emenda). O flag `self._emendando` abre a
> guarda `phase != "city"` de `enter_dungeon` (único caminho que entra numa masmorra vindo de
> `playing`) e suprime os resets "por masmorra nova" (corrosão/vinho/cerveja/chamas). A
> história da emenda vai em `game_state.story` (`self._story_encadeada`, beat
> `outro da etapa N + intro da N+1`) — o cliente **não mudou**: `_captarStory` já lê
> `msg.story` de qualquer mensagem e deduplica por `key`. **(2) Saída individual:**
> `handle_exit_dungeon` deixou de levar o grupo inteiro — agora exige turno próprio, estar em
> cima de `stairs_pos` e a masmorra permitir (`saida_permitida`, campo novo da masmorra,
> default `True`), cobra **ida e volta** (`_custo_viagem_saida` = 2× o `fome`/`sede` da
> aventura; fora de aventura é grátis) e marca
> `p["fora_masmorra"] = {rodadas_restantes, ignorar_primeiro_fecho}`. O portão é o
> **`_ativo(p)`** — que já significa "está no tabuleiro, na iniciativa e é alvo válido" —
> estendido com `and not p.get("fora_masmorra")`: os 27 sites que o consultam tratam o ausente
> como um desconectado, sem serem tocados (o peão vai para `[-1,-1]`, espelhando
> `handle_disconnect_em_jogo`). Na cidade, `_em_cidade(pid)` (= sala na cidade **ou** este
> jogador fora) substitui `phase != "city"` em `handle_shop_buy`/`handle_shop_sell`/
> `handle_guild_buy`/`handle_guild_equip`/`handle_scene_npc`; ficam **de fora** de propósito
> `world_travel`, `world_adventure`, `enter_dungeon` e `city_map_points` (ações de grupo).
> `broadcast` ganhou `skip` e `push_state` **não** manda `game_state` a quem está fora (o
> cliente prefere `gameState` a `cityState` e mostraria o paperdoll da masmorra);
> `push_state_or_city` manda `city_state` individual (`_city_state_payload`/
> `send_city_state_to`). **Espera:** `_tick_retorno_masmorra` decrementa no fecho de rodada
> (`_advance_initiative`), guardando **rodadas restantes** e não uma rodada-alvo absoluta —
> assim sobrevive à emenda, que reinicia `round_num`; `ignorar_primeiro_fecho` faz o fecho da
> rodada em que o herói saiu não contar (senão a espera valeria N ou N-1 conforme o momento da
> saída). Ao zerar ele ganha 1 rodada de tolerância e volta sozinho na seguinte;
> `voltar_masmorra` (`handle_voltar_masmorra`) antecipa. `_reentrar_masmorra` recoloca na
> escada (casa vizinha só se ocupada) com turno cheio e manda `enter_dungeon` só para ele.
> `_checar_masmorra_vazia` (chamado na saída e em `_player_dies`) devolve a sala à cidade
> quando não sobra herói ativo dentro mas há alguém vivo na cidade — não é derrota. O ausente
> **participa** da divisão de XP/ouro (`_conceder_objetivo_reward` já itera por `alive`) e vai
> junto na etapa encadeada. Editor: checkbox "⛓️ emendar na próxima" + encerramento/abertura
> por etapa e **espera de retorno** (fixa em rodadas ou fórmula `NdX`, `_clean_espera`/
> `_rolar_espera`) em `tools/editor_world.js`; checkbox "🚪 saída pela escada" no painel da
> masmorra (`tools/editor.html`/`editor.js`). Cliente: `game_state` traz
> `saida_permitida`/`custo_saida`/`espera_saida` para a confirmação no clique da escada; card
> esmaecido "🏙️ na cidade — volta em N rodada(s)" em `renderPlayers`; banner com contador e
> botão "⛓️ Voltar à masmorra" em `_renderBannerForaMasmorra`; `GS.voltarMasmorra`/
> `foraMasmorraDe`/`estouForaDaMasmorra`/`rodadasParaVoltar`. **Atenção:** `GS.isMyTurn` é uma
> **propriedade booleana**, não função — chamá-la com `()` lança `TypeError`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-28-masmorra-sequenciada-saida-individual*`. Teste:
> `tools/test_masmorra_sequenciada.py`.

> **História em slides nas aventuras:** o `intro`/`outro` de cada etapa de aventura aceita
> **string** (1 slide de texto) ou **`{slides:[{text,image,fit}], audio}`** — o mesmo formato
> das campanhas, já normalizado por `_story_norm`. Ao salvar, `_clean_story_field` preserva o
> objeto (antes um `str(...)` o destruía) e **restringe a mídia a `assets/story/`**
> (`_story_media_ok`, sem `..`). **Três beats**, todos no campo `story` que o cliente já
> consome sem mudança (`_captarStory` lê `msg.story` de qualquer mensagem e deduplica por
> `key`): **abertura** da etapa em `handle_world_adventure` (`aventura:<id>:<i>`, vale para
> toda etapa iniciada pelo mapa), **transição** em `_emendar_proxima_etapa`
> (`encadeada:<id>:<i>`) e **encerramento** no ramo não-encadeado de `handle_encerrar_missao`
> (`fim:<id>:<i>`), que sai no `city_state`. `_voltar_para_cidade` ganhou o parâmetro
> `story=None`: ela limpa `_story_encadeada` e faz o broadcast na mesma chamada, então gravar
> o beat antes não sobreviveria. O encerramento cobre tanto a última etapa quanto uma
> intermediária sem `encadear` — nos dois casos o grupo volta à cidade. **Editor:** o painel
> de slides (miniatura, upload de imagem/áudio para `assets/story/` via `STORY_UPLOAD`,
> reordenar, pré-visualizar) saiu de `editor_campaign.js` para **`tools/editor_story.js`**
> (`window.EDITOR_STORY`, 8 funções) e agora serve as duas abas; cada etapa do mapa-múndi tem
> "📖 abertura" e "📖 encerramento" (estado em `_introSt`/`_outroSt`, serializado por
> `storyToSaved` no salvar). Em `editor_campaign.js` os apelidos `const` do módulo precisam
> vir **antes** de `const C`, que chama `emptyStory()` na inicialização. **Cliente:**
> `hideWorldMap()` no handler de `enterDungeon` — o mapa-múndi é um overlay sobre
> `screen-city` que só sumia quando a cidade mudava, então voltar da masmorra caía nele em vez
> da ilustração da cidade (`world_location` nunca muda ao entrar numa aventura). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-28-historia-em-slides-nas-aventuras*`. Teste:
> `tools/test_masmorra_sequenciada.py` seções [15]-[17].

> **Destino oculto no mapa-múndi:** cada destino de aventura aceita
> `oculto_ate_liberar` (bool, default `false`). Com o flag ligado, o destino **não entra**
> em `city_state.world.adventures` enquanto o requisito não é cumprido — o filtro é do
> servidor (`_aventura_visivel`, ao lado de `_avaliar_requisito`), então o cliente não muda
> e não há o que espiar no payload. `handle_world_adventure` responde **"Destino de aventura
> inválido."** (a mesma resposta de um id inexistente) quando o destino é oculto e ainda
> bloqueado; destinos visíveis mantêm a mensagem detalhada com o que falta. O payload do
> **editor** (`_world_adventures_editor_payload`) não filtra — o autor precisa enxergar o que
> criou. **Atenção:** requisito vazio **passa** em `_avaliar_requisito`, então o flag sozinho,
> sem nenhum requisito, não esconde nada; por isso o checkbox "🕵️ ocultar no mapa até liberar"
> (bloco de requisitos em `tools/editor_world.js`) fica desabilitado até haver um requisito
> preenchido, e preencher um re-renderiza o painel para habilitá-lo. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-29-destino-oculto-ate-liberar*`. Teste:
> `tools/test_masmorra_sequenciada.py` seções [18]-[18c].
> **Só na cidade (2026-09-26):** destino com `so_na_cidade` continua no payload (o ponto de
> masmorra da cidade depende dele), mas o mapa-múndi do cliente não desenha o marcador — entra-se
> só pelo ponto da ilustração. Checkbox "🏘️ só na cidade" no `tools/editor_world.js`. O Campo de
> Treinamento usa. Teste: seção [20].

> **Fim da rota:** além do `intro`/`outro` de cada etapa, o **destino** tem um campo de
> história próprio, `outro_rota` (mesmo formato: string ou `{slides, audio}`, salvo por
> `_clean_story_field`). No ramo não-encadeado de `handle_encerrar_missao` o beat `fim:` é
> montado com duas partes — `[etapa.outro]` e, **só quando `completed_index + 1 >=
> len(stages)`** (a etapa concluída era a última), também `adventure.outro_rota`. Como
> `_story_beat` concatena na ordem e descarta as partes vazias, sai de graça: etapa
> intermediária mostra só o encerramento dela; a última mostra encerramento da etapa **e**
> fim da rota no mesmo slideshow; destino sem `outro_rota` fica idêntico ao de antes. A
> `key` do beat não muda. Editor: botão "🏁 fim da rota" no painel do destino (abaixo de
> "Renome por etapa concluída"), estado `_outroRotaSt`, mesmo painel de slides do
> `EDITOR_STORY`. Não há mudança de momento: o beat viaja no `city_state` e o slideshow é
> um overlay de tela cheia, então o jogador lê antes de ver a cidade. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-29-fim-da-rota*`. Teste:
> `tools/test_masmorra_sequenciada.py` seções [19]/[19b].
> **Aventura na foto (2026-10-06):** `world_adventure_id`/`_index`/`_revisit` só existiam na sala
> (categoria `jogo_salvo`, mas nunca gravados); depois de "Salvar e sair" → Continuar dentro de uma
> etapa voltavam `None`, e "Encerrar missão" na última etapa caía no `end_game(victory=True)` em vez
> do fim da rota + cidade. Agora são categoria `foto`; foto antiga sem eles deduz o destino pelo
> arquivo da masmorra (`_deduzir_aventura_da_foto`, em `_foto_aplicar_sala`). Teste:
> `tools/test_aventura_retomada.py`.

> **Campanha "Sombras sob Alva e Luz" (2026-09-25):** primeira campanha de conteúdo, gerada por
> `tools/gerar_campanha_sombras.py` (reexecutável; só toca nas entradas `sombras_*`/
> `anel_garra_negra` e recusa sobrescrever masmorra editada à mão sem `--forcar`, por hash em
> `tools/.sombras_assinaturas.json`; `--simular` relata ND por sala e as artes pedidas pelos
> slides). Gancho: conversa `sombras_caravanas` do Bartender de Alva e Luz → fato → destinos
> ocultos em corrente Vau (escolta de Tomé até a saída, nível 1) → Minas (baú-chave com
> ácido/óleo e o bilhete, nível 2) → Covil (Salões com salas obrigatórias, emendados no Trono do
> Troll, nível 3). Chefe secreto: Bugbear das Sombras atrás da estante-mecanismo, guardando o
> **Anel da Garra Negra** (item custom: +1 acerto, +1 visão, concede Esconder nas Sombras).
> Achado no caminho: `load_authored_dungeon` descartava `required`/`required_mode` e o objetivo
> `salas_obrigatorias` se cumpria ao entrar — corrigido (`test_modo_mestre` [23b]). A curva de XP
> é a do master ("15 encontros por nível"); os objetivos da campanha não dão XP, e a seção [7]
> da suíte só relata o nível atingido (a fórmula dela ainda é a da curva antiga). Avisos do
> validador de design esperados: "sem boss" em Vau/Minas/Salões (sem chefe por design), "sem sala
> obrigatória" onde o objetivo é outro, e no Trono R2 (chefe perto da entrada) e R4 na sala #2 —
> o Esconderijo só se liga ao mapa quando a estante abre. Teste: `tools/test_campanha_sombras.py`.

> **Prévia fiel do editor (`index.html?preview=1`):** o botão "◈ Visualizar em 3D" do
> editor deixou de ter renderer próprio — `tools/editor_preview_3d.js` era uma
> reimplementação paralela de 183 linhas que divergia do jogo (decoração `special:floor`/
> `wall` virava caixa lisa em vez do PNG, `DECOR_GLB` incompleto, monstro sempre sprite
> chapado em vez de `MONSTER_GLB`, iluminação fixa em vez dos presets `VC.ambientes`).
> Agora ele só hospeda um `<iframe src="../index.html?preview=1">` — o **cliente real** — e
> injeta nele o `game_state` que o **servidor** monta com o **mesmo `load_authored_dungeon`**
> do jogo. Fidelidade estrutural: objeto, monstro ou material novo aparece na prévia sem
> ninguém tocar no editor. Fluxo: `EDITOR.buildJSON()` (sem gravar) → `preview_dungeon` pelo
> WebSocket (`EDITOR_SAVE.previewDungeon`, no `story_upload.js`) → `_preview_dungeon_state`
> (server.py) → `preview_state` → `postMessage` no iframe → `GS.injectPreviewState`.
> **Servidor:** `push_state` foi dividida em `_game_state_payload()` (dict puro) +
> `push_state` (await + broadcast), espelhando `_city_state_payload`/`broadcast_city_state`;
> `_preview_dungeon_state` monta um `GameRoom("PREVIEW")` descartável, marca todo o mapa
> como `explored` e usa `master_pid = PREVIEW_PID` — a **visão sem névoa sai do mecanismo já
> existente do Modo Mestre** (`isMaster()` = `master_pid == myPid`), sem caminho novo de
> render. É **tolerante**: masmorra em construção rende avisos (entrada suprida pela 1ª casa
> de chão, sala default do tabuleiro inteiro, monstro de tipo desconhecido descartado) em vez
> de recusa; só grid/tiles ausentes viram erro. **Cliente:** `GS.isPreview` (regex em
> `location.search`) faz `send()` virar no-op e expõe `injectPreviewState`, que passa pelo
> mesmo `case 'game_state'`; `game.js` pula login/lobby, vai direto a `screen-game` com
> `mode3D = true` e marca `body.preview-mode` (CSS esconde HUD/log/dados). O iframe avisa
> `preview_ready` antes de receber o estado — sem isso o `init3D` não teria onde desenhar.
> Como nada em `tools/*.js` usa mais `THREE`, o `editor.html` **deixou de carregar Three.js**.
> Prévia = só cenário (`players: []`, `current_turn: null`) e só câmera. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-07-28-previa-3d-fiel-editor*`. Teste:
> `tools/test_preview_editor.py`.

> **`Connection: close` nas respostas estáticas (bug de rede do servidor):** a lib
> `websockets` FECHA a conexão TCP depois que `process_request` responde, mas o `_http`
> não declarava isso. Em HTTP/1.1 a ausência do cabeçalho significa conexão persistente:
> o navegador guardava o socket no pool e reusava numa requisição **posterior**, que
> morria na rede (XHR com `status 0`, sem resposta). Batia justamente nos pedidos
> **tardios** — os `.glb` carregados sob demanda (`_loadDecorGLB`, `_loadMonsterGLB`) —
> e não no HTML/JS/PNG do carregamento inicial. Provado com socket cru: 1ª resposta
> `200`, 2ª na mesma conexão não existe. Afeta o **jogo**, não só a prévia do editor.
> Defesa em profundidade no cliente: `GLB_TENTATIVAS`/`_glbVaiRetentar` dão **uma
> tentativa extra** só para falha de conexão (`status 0` ou sem status) — 404/403
> desistem de imediato. Sem isso a 1ª falha marcava `'erro'` no cache, que é definitivo:
> o objeto sumia até a página ser recarregada. `_glbMotivo` traduz o `ProgressEvent`
> (antes virava `"[object ProgressEvent]"`). O servidor **não responde a HEAD** (a lib
> só aceita GET), então sondar status por HEAD não é opção. Teste:
> `tools/test_preview_editor.py` seção [4b].

> **Cenas de conversa por local:** a cena da taverna (ilustração em tela cheia com
> frequentadores clicáveis) deixou de ser exclusiva da taverna e virou um recurso de
> **qualquer ponto da cidade**, com **várias cenas por cidade**. `TAVERN_SCENES[cidade]`
> (uma cena) virou **`CITY_SCENES[cidade][cena]`**, persistido em `city_scenes.json`
> (`_load_city_scenes`/`_save_city_scenes`); `_migrar_tavern_scenes` converte o
> `tavern_scenes.json` antigo uma única vez no boot, deixando o arquivo antigo intocado
> como rede de segurança. Cada cena tem `nome` além de `background`/`mask`/`mode`/`slots`;
> teto de 16 cenas/cidade (`MAX_CENAS_POR_CIDADE`), id em `CENA_ID_RE`. `CITY_SCENES` é o
> 4º derivado por cidade, ao lado de `CITY_SHOPS`/`CITY_MAP_POINTS` (mesmo
> `_sincronizar_cidades_derivadas`), então criar/excluir cidade continua correto de graça.
> **O vínculo mora no ponto**, não na cena: `CITY_MAP_POINTS[cidade][ponto]` ganhou `scene`
> (id da cena), `emoji` (livre, sobrepõe o do tipo) e o tipo novo `cena` (local que só
> existe para conversar). A direção importa — um ponto tem **no máximo uma** cena, então
> "duas cenas disputando o mesmo local" não é estado representável. `_garantir_pontos_implicitos`
> religa um ponto à cena de **mesmo id** quando ele não tem vínculo: é isso que faz a
> taverna migrada abrir sozinha, sem caso especial no runtime. **Efeito colateral aceito:**
> esse par não pode ficar sem cena (o editor mostra a opção desabilitada em vez de prometer
> algo que não gruda), e por isso o botão "+ Criar ponto para esta cena" cria o ponto com id
> **próprio** (`ponto_<cena>`), mantendo o desvincular possível nas cenas novas.
> **Conversa de uso único agora SOME do menu:** `_cenas_payload` (ex-`_tavern_payload`)
> **omite do payload** tanto a conversa bloqueada por requisito quanto a `uma_vez` já
> resolvida — os campos `disponivel`/`oculta`/`bloqueio` deixaram de existir. Isso fechou de
> quebra um vazamento real: antes o texto da conversa bloqueada viajava no `city_state` e só
> o cliente não o desenhava. Com a omissão, o filtro do cliente sumiu e o fallback que
> sintetizava `{id:'inicial'}` de `slot.dialog` foi **removido** — ele ressuscitava justamente
> a opção omitida e gerava um botão que respondia "Conversa não encontrada". `conversations: []`
> hoje significa uma coisa só: não sobrou nada que este jogador possa escolher.
> Protocolo: `city_state.tavern` → **`city_state.scenes`**; `tavern_npc` → **`scene_npc`**
> (`handle_scene_npc`); a chave de conversa concluída passou de 3 para 4 partes
> (`cidade:cena:npc:conversa`) e `_migrar_chaves_conversa` converte as antigas dos savegames
> na carga (`scene_conversations_done`, com fallback de leitura para
> `tavern_conversations_done`). **Cliente:** `openShop(pointId, type)` recebe o **id do ponto**
> (antes o tipo do prédio) e resolve cena e loja de forma independente, montando as abas como
> *[💬 nome da cena] + [abas da loja]* — a taverna perdeu a aba hardcoded e virou a primeira
> cliente da regra geral. Dentro de `_renderShopItems` o índice de aba **relativo à loja**
> (`aba = shopTabIdx - (temCena ? 1 : 0)`) é o que vale em toda comparação, senão a lista de
> itens sai trocada. Ponto do tipo `cena` **sem** cena vinculada (ou apontando para cena
> inexistente) **não** é desenhado — senão viraria um marcador que abre um modal sem abas.
> `GS.scenes/cityPoints/sceneIdOfPoint/sceneOfPoint/activeScene/talkSceneNpc` em
> `src/gameState.js`; CSS e funções renomeados de `tavern-*` para `cena-*`. **Editor:** aba
> "💬 Cenas e NPCs" (ex-"Taverna e NPCs") com lista de cenas, "+ Nova cena", nome, "Vinculada
> a" (o dropdown não oferece `dungeon`/`caravana`/`guilda`, que têm tela própria) e excluir —
> cena ausente do envio = exclusão no servidor, que também limpa o vínculo do ponto.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-07-30-cenas-de-conversa-por-local*`.
> Testes: `tools/test_cenas_conversa.py` (57 checks) + `tools/test_cidades_editor.py`.

> **Idioma (i18n) — motor PT/EN:** o painel ⚙️ (o "menu geral", canto superior direito, em
> todas as telas, também por Esc) ganhou a linha **🌐 Idioma** (`<select>` Português/English)
> que troca o idioma **por jogador** — dois jogadores na mesma sala podem estar em idiomas
> diferentes. Dicionário ÚNICO em `src/lang/strings.js` (`{chave: {pt, en}}`), lido pelo
> cliente via `<script>` (síncrono: sem piscar português antes do inglês e sem depender de
> `fetch`) e pelo servidor via `json.loads` — mesmo padrão de `tools/editor_catalog.js`. Mora
> em `src/` porque a allow-list de estáticos é `("src","assets")`; na raiz daria 404. O
> recorte do objeto é ancorado por regex no **início da linha** `window.LANG_STRINGS =`, e não
> na primeira `{` do arquivo, para que comentários de seção possam conter chaves à vontade.
> **Cliente:** `src/i18n.js` é motor PURO (`I18N.t/setLang/on/lang`, zero DOM); `game.js` tem
> o atalho `t()`, a persistência (`lfh_lang` no localStorage) e `_i18nApply(root)`, que varre
> `[data-i18n]`/`[data-i18n-ph]`/`[data-i18n-title]`. **Cuidado:** só marque com `data-i18n`
> elemento cujo conteúdo INTEIRO seja o texto — `textContent` apaga filhos (por isso o rótulo
> do checkbox de Mestre em `screen-savegames` tem o texto num `<span>`). A propagação do
> idioma ao servidor é por **um ouvinte só** (`I18N.on(code => GS.setLang(code))`), que cobre
> tanto o clique no seletor quanto a restauração do localStorage no boot — fazer isso só no
> clique é um bug real já cometido: a interface ficava em inglês e a narração em português.
> **Servidor:** `T("chave", **params)` marca "texto ainda não traduzido"; `broadcast`/
> `send_to`/`err` resolvem pelo parâmetro `default` do `json.dumps`, no idioma da conexão,
> agrupando por idioma (um `json.dumps` por idioma presente na sala). Isso cobre de graça o
> `gm_log` dentro do `game_state` (que passa a guardar `T` — seguro, o log nunca vai a disco).
> **Regra de migração:** string crua continua string crua e sai em português para todos;
> migrar uma frase é envolvê-la em `T(...)` e acrescentar a chave. Sem `en` → cai no `pt`; sem
> a chave → devolve a própria chave. Idioma por conexão em `LANG_BY_PID` (dict de módulo,
> chaveado pelo `pid` do contador global `new_id()`), não na sala: vale antes de entrar em sala
> e cobre o Mestre, que sai de `self.players` no `start_game`; limpo no `finally` do `handler`.
> Ao receber `set_lang` o servidor reenvia o estado, e esse reenvio cai no caminho normal de
> render do cliente — não há função de re-render nova. **Amostra traduzida nesta etapa:** painel
> ⚙️, `screen-connect`, `screen-savegames`, a narração de abrir porta e o erro de porta
> distante. O resto (~546 `gm_say` + ~470 erros + a interface) é a etapa 2; o bloco `#hint-host`
> (que mistura `<b>`/`<code>`) e o conteúdo autoral (masmorras, campanhas, falas de NPC,
> itens/monstros custom) estão FORA de escopo. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-10-idioma-i18n*`. Testes: `tools/test_idioma.py` (31)
> e `tools/test_idioma_cliente.js` (16, node) — os dois têm varredura estática que aponta chave
> órfã, e é ela que diz, na etapa 2, o que ainda falta.

> **Idioma — vocabulário (etapa 2 de 5):** os **397 nomes** de catálogo traduzidos —
> `item` 140, `guilda` 125, `monstro` 51, `decor` 28, `magia` 27, `armadilha` 11,
> `instrumento` 9, `classe` 6. As chaves seguem `cat.<família>.<id>.nome` e são **geradas**
> por `tools/gerar_vocabulario.py` a partir dos catálogos do `server.py` para
> `src/lang/catalogo.js` — arquivo separado do `strings.js` escrito à mão, para o gerador
> nunca sobrescrever tradução manual. O gerador é idempotente (preserva o `en`, acrescenta
> chave nova, **relata sem apagar** as órfãs) e **falha alto** se dois catálogos derem nomes
> diferentes ao mesmo id. **Rode-o depois de criar item ou monstro novo** — a saída diz o que
> falta traduzir. `_load_lang()` agora funde TODOS os `.js` de `src/lang/` (leitura de um
> arquivo isolada em `_load_lang_arquivo`); um arquivo quebrado perde só as chaves dele.
> **Cliente:** `I18N.traduzirNomes(msg)` (puro, em `src/i18n.js`) percorre cada mensagem
> recebida e troca `name`/`nome` quando o `type` ou o `id` do objeto tem chave no dicionário;
> `gameState.js` ganhou `setMessageFilter(fn)`, aplicado no `ws.onmessage` antes do `_handle`
> — ele não conhece o I18N (regra do CLAUDE.md), só chama a função que o `game.js` registrou,
> dentro de um `try` para que filtro com defeito não derrube a partida. Isso deixa os **405
> pontos de render que leem `.name` intocados**, e faz item/monstro criados no editor
> manterem o nome autoral de graça (sem chave → sem troca). Em português a função retorna na
> primeira linha: custo zero. **Servidor:** `t()` resolve parâmetro que é ele próprio um `T`
> (sem isso, frase em inglês sairia com o nome em português cravado — era o bloqueio da etapa
> de narração), e `nome_de(familia, id)` devolve esse `T`. **Nenhum payload mudou** — eles
> seguem mandando o nome em português, que é o fallback de que o filtro depende. **Etapas
> restantes:** descrições de catálogo (185), erros (470) e narração (544) do servidor,
> interface do cliente (~1.000). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-10-idioma-etapa2-vocabulario*`. Testes:
> `tools/test_vocabulario.py` (36) e `tools/test_vocabulario_cliente.js` (16).

> **Idioma — alcance e descrições (etapa 3 de 5):** fecha três lacunas de alcance da etapa 2
> (53 nomes traduzidos que não chegavam à tela) e acrescenta as **189 descrições** de
> catálogo (`cat.<família>.<id>.desc` ao lado de `.nome`; o gerador emite `.desc` só para
> quem tem descrição). **(1) Id na chave do pai:** `lobby_state.classes` e
> `game_start.instrumentos_base` são dicionários chaveados pelo id, com o valor sem campo
> `id` dentro; o filtro passa a tentar a chave do dicionário pai como id, além dos campos
> internos. **(2) Catálogos estáticos do cliente:** `GRIMORIO_CLIENT` e `ARMADILHAS_LUCCAS`
> (`game.js`) e `CATALOGO_ITENS` (`src/gameState.js`) não vêm de payload — são reescritos
> por `I18N.aplicarCatalogo(obj, true)` no boot e a cada troca de idioma, num ouvinte
> SEPARADO do que avisa o servidor (manter aquela linha intacta preserva a checagem de
> fiação da etapa 2). O `true` é **só o nome**: a descrição que esses catálogos guardam é
> conteúdo próprio já divergente do servidor — a das magias é um card HTML com alcance e
> efeito por rodada, contra uma frase curta no servidor —, e trocá-la apagaria informação;
> esse texto é da etapa 5. `aplicarCatalogo` **não tem** a saída antecipada em português que
> o `traduzirNomes` tem, porque a volta ao português é justamente o que restaura o texto
> original; a troca é sempre por id, nunca por texto, o que a torna idempotente.
> **(3) Precedência do inventário:** `_converterBagParaInventario` fazia `cat ? {...cat}` e
> descartava o item do servidor inteiro quando o id existia nos dois catálogos (28 casos),
> devolvendo o nome ao português; virou `{ ...cat, nome: it.name || cat.nome }` — só o nome
> é sobreposto, os demais campos do catálogo do cliente seguem valendo.
> **Lição de teste:** a suíte da etapa 2 cravava contagens (`guilda: 125`, `total 397`) sobre
> um catálogo VIVO e ficou vermelha sozinha quando o autor criou duas armadilhas. As
> asserções passaram a ser de **relação** (toda entrada vira exatamente uma chave) — não
> crave tamanho de catálogo em teste. **Fora de escopo:** os 44 itens que só existem em
> `CATALOGO_ITENS`, o `resumo`/`descricao` HTML das magias e o `desc` próprio das armadilhas
> no cliente — todos etapa 5. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-10-idioma-etapa3-descricoes*`. Testes:
> `tools/test_vocabulario.py` (37) e `tools/test_vocabulario_cliente.js` (29).

> **Idioma — erros do servidor (etapa 4a de 5):** as **471 mensagens de recusa** migradas para
> `T(...)` e traduzidas (382 chaves). A chave é o **slug do texto em português**
> (`erro.alvo_invalido`), o que **deduplica por construção**: as 390 ocorrências de texto fixo
> viraram 305 chaves, e a mesma recusa passa a sair sempre com a mesma frase — o que o jogo
> não garantia nem em português ("Alvo inválido." aparecia 18× no fonte). Dicionário em
> `src/lang/erros.js`, **mantido à mão**: depois da migração o `server.py` não tem mais o
> texto, só a chave, então não há de onde gerar de novo (ao contrário do `catalogo.js`).
> `tools/migrar_erros.py` é de uso único e fica no repositório como registro do método.
> **Duas formas de chamada** precisaram ser reconhecidas: `{"type":"error","msg":…}` e o
> atalho local `await err(…)`. **Um site serializava cru** (`ws.send(json.dumps(...))` em
> `add_player`, sem passar por `send_to`/`err`) e teria estourado `TypeError` com um `T`
> dentro — ganhou o mesmo `default=`.
>
> **A mudança estrutural desta etapa: `T` agora se comporta como o texto em português.**
> Ganhou `__str__`, `__eq__`, `__hash__`, `__contains__`, `__len__` e um `__getattr__` que
> delega ao texto. Motivo: **24 arquivos de teste** mockam `send_to` capturando
> `msg.get("msg","")` **cru**, sem passar pelo `json.dumps(default=_t_render)` real — com um
> `T` ali, `.lower()` estourava `AttributeError`. Nove suítes quebraram na hora e as outras 15
> quebrariam na migração seguinte. Fazer o `T` se disfarçar de string resolveu a família
> inteira **sem tocar em nenhum teste**, e é coerente com o fallback do projeto ("na dúvida,
> português"). **O `T` NÃO pode virar subclasse de `str`**: se virasse, o `json.dumps` pararia
> de chamar o `default` e a tradução morreria em silêncio — há teste cobrindo isso. O
> `__getattr__` precisa da guarda contra `__`/slots, senão um acesso a `key` antes do
> `__init__` recursa infinitamente. Custo aceito: o `T` esconde uso indevido em vez de falhar
> alto.
>
> **Teste novo que vale para todas as etapas:** paridade de `{parâmetros}` entre `pt` e `en`
> em TODAS as chaves de TODOS os arquivos de idioma (hoje 1.011) — é a falha mais provável
> numa tradução em lote e a mais visível para o jogador, porque o `{nome}` aparece cru na
> tela. **Detalhe que salvou duas mensagens:** algumas terminam com espaço ou `": "` porque o
> servidor concatena o motivo depois; o `en` tem de preservar isso. Testes:
> `tools/test_erros.py` (9). **Falta:** narração do servidor (544, etapa 4b) e interface do
> cliente (~1.000, etapa 5). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-10-idioma-etapa4a-erros*`.

> **Idioma — narração do servidor, lote mecânico (etapa 4b-i de 5):** os **390 `gm_say` que
> cabem inteiros numa linha** migrados para `T(...)` e traduzidos — 380 chaves em
> `src/lang/narracao.js`. A chave é o slug do texto **sem** as interpolações
> (`narracao.abre_uma_porta`), o que a mantém legível. **Batismo determinístico dos
> parâmetros** pelo script, em três degraus: identificador simples vira ele mesmo,
> `X['name']` vira `X`, o resto vira slug da expressão — mais uma tabela mínima de apelidos
> (`p`→`heroi`, `m`→`monstro`, 30% das 764 interpolações). Difere da 4a de propósito: lá as
> 81 foram batizadas à mão pelo papel na frase; aqui, com 390 sites automáticos,
> determinismo vale mais que elegância. `tools/migrar_narracao.py` é de uso único e reusa o
> `slug()` do `migrar_erros.py`.
>
> **LACUNA CONHECIDA — nome de catálogo cru dentro da frase traduzida.** Das 325 passagens
> de `X["name"]` como parâmetro, ~140 são `p['name']` (nome de jogador, correto passar cru);
> as outras ~185 são monstro, alvo e item, cujo nome vem do catálogo. O script passou a
> expressão verbatim, então em inglês o log diz *"The adventurers leave town… Round 1 —
> **Elemental Elétrico**'s initiative"* — frase em inglês, nome em português. O
> `nome_de(familia, id)` existe desde a etapa 2 exatamente para isso (devolve o nome como
> texto TARDIO, resolvido no idioma de quem lê) e o `t()` resolve parâmetro aninhado desde
> então. Trocar esses ~185 sites é trabalho da etapa 4b-ii.
>
> **Fora de escopo (4b-ii):** 109 chamadas com o texto na linha seguinte, 28 f-strings que
> começam na linha do `gm_say(` e continuam depois, 3 concatenações com `prefix +`, 7 sites
> que recebem variável, e 6 que puxam do pool `gm(...)` — um catálogo de 30 variantes
> aleatórias de narração ambiente ("As criaturas avançam nas sombras…"), que continuam em
> português. O `tools/test_narracao.py` **conta e relata** esses restantes em vez de
> cobrá-los, para a suíte não ficar vermelha por trabalho não combinado — e o relatório é o
> placar da 4b-ii.
>
> **Armadilha de verificação:** um servidor já rodando na porta 8765 pode ser de ANTES da
> migração; a prova de dois idiomas saiu toda em português até o processo ser reiniciado.
> Sempre reinicie o servidor antes de provar mudança de servidor. Testes:
> `tools/test_narracao.py` (8). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-10-idioma-etapa4b1-narracao*`.

> **Idioma — nomes de catálogo dentro da frase (etapa 4c de 5):** fecha a lacuna que a
> 4b-i deixou registrada — a frase traduzia mas o nome saía cru (*"Round 1 — **Elemental
> Elétrico**'s initiative"*). Dos **295 parâmetros** de nome de catálogo nas 390 narrações
> já migradas, **288 foram resolvidos**; os 158+ de nome de JOGADOR seguem crus, que é o
> certo. Três helpers novos, ao lado do `nome_de`: **`nome_cat(familia, ident, cru)`** —
> devolve `T` só quando o nome cru **ainda é o do catálogo**, e é essa **guarda de
> igualdade** que torna a etapa segura por construção para conteúdo autoral (monstro/item
> do editor não tem chave; nativo renomeado por `overwrite_native` tem chave com outro
> texto — os dois saem crus, preservando o nome do autor, sem lista de exceções para
> manter); **`nome_criatura(x)`** — despacha pela **forma do dict** (`class_id`→herói cru,
> `name_key`→nome trocado em runtime, `vida_atual`+`tipo`→servo animado, `type`→monstro),
> porque `alvo`/`target` são ora herói, ora monstro, ora servo **no mesmo parâmetro**, em
> ~45 sites, e a informação só existe em runtime; **`nome_item(it)`**.
>
> **Nomes compostos — princípio único: carregar as partes, nunca reparsear a string
> pronta.** Três mutações de `name` foram REMOVIDAS e viraram composição na hora de
> render, a partir de campo que o objeto já tinha: `(corroído)` ← `corrosao_inicial`,
> `Virotes (×N)` ← `ammo_count`, servo animado ← `tipo` + `nome_base` (campo novo). O
> **instrumento** ganhou `_instrumento_nome_T`, irmã tardia de `_instrumento_nome` (que
> segue devolvendo português puro — é ela que grava `inst["name"]`, e isso vai a disco no
> savegame): a ordem das partes é do **template** (`cat.instrumento.nome_composto`),
> porque em inglês o adjetivo vem ANTES do substantivo, e o **espaço vem embutido no lado
> certo de cada idioma** em cada adjetivo (`" Velha"` × `"Old "`), que é o que faz parte
> ausente não deixar espaço solto. O gênero só existe no `pt`. `Harpa Lendária Élfica` →
> `Legendary Elven Harp`. Chaves escritas à mão em **`src/lang/composto.js`** (o gerador
> só emite `.nome`/`.desc`, então nada disso poderia nascer dele). Para nome trocado em
> runtime, que por definição não casa a guarda, a saída é o campo **`name_key`** (hoje só
> o Elemental Descontrolado).
>
> **O cliente ganhou um compositor gêmeo** em `src/i18n.js` (`_instrumentoComposto` +
> `_comSufixos`), lendo AS MESMAS chaves: o instrumento tem id único por combinação, que
> não existe no catálogo, então o filtro não o tocava. **Atenção:** a composição tem duas
> implementações e nada além dos testes impede que divirjam — `test_narracao.py` [7] e
> `test_vocabulario_cliente.js` [N] cravam a MESMA tabela de 7 arranjos e se citam.
>
> **Três bugs pré-existentes fechados de quebra:** (1) `SHOP_AMMO` estava fora das fontes
> do `gerar_vocabulario.py` desde a etapa 2 — 6 munições sem chave nenhuma; (2) o filtro
> `traduzirNomes` do cliente comia o `(corroído)` da bolsa em inglês, e o jogador não via
> que a peça estava corroída; (3) `test_editor_itens` estava VERMELHO desde `8b5fb13`
> porque fazia `" ".join(falas)` — o `T` se disfarça de string em `__contains__`, `__len__`
> e `__getattr__`, mas **não** em `str.join`, que exige `str` de verdade.
>
> **Continua em português de propósito:** monstro/item autoral, nome de jogador, e 7
> passagens que **não são das 8 famílias** de catálogo — nome de ataque em tupla literal
> (`"Garras"`, `"Mordida"`), rótulo de status, nome de habilidade passado como parâmetro,
> `weapon_name` (já chega como string do `_resolver_dano_ataque_basico`), nome de cidade, e
> um `nomes` já unido por `" e ".join` (juntar `T`s exigiria um `T` que saiba concatenar,
> que o motor não tem). **Maldições, habilidades de monstro e nomes de aventura** também
> ficam: não são famílias de catálogo. **Falta:** a etapa **4b-ii** (153 `gm_say` ainda não
> migrados) e a etapa **5** (interface do cliente, ~1.000). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-11-idioma-etapa4c-nomes-na-narracao*`. Testes:
> `tools/test_narracao.py` (48), `tools/test_vocabulario_cliente.js` (40).

> **Idioma — a narração que sobrou (etapa 4b-ii de 5):** fecha a narração do servidor.
> **Não há mais nenhum `gm_say` com texto em português no `server.py`** — a varredura por
> `ast` da seção `[3]` do `test_narracao.py`, que até a 4b-i só *relatava*, agora **cobra**.
> 134 sites migrados + as 30 frases do pool + os 6 que recebiam string pronta.
>
> **Migrador por `ast`, não por regex** (`tools/migrar_gm_say_ast.py`, uso único): para o
> `ast`, f-string multilinha, f-string de uma linha e concatenação implícita são a MESMA
> árvore (`JoinedStr`), então as três formas saem pela mesma máquina, sem adivinhar onde a
> string começa nem como os fragmentos se juntam. **Armadilha corrigida antes de rodar:** o
> `ast` reporta `col_offset` em **bytes UTF-8**, não em caracteres — e o `server.py` é cheio
> de emoji e acento, então fatiar por índice de caractere corromperia o arquivo em silêncio.
> Todo o corte é em bytes, de trás para frente. Três travas: forma não reconhecida é
> **pulada e relatada**; `ast.parse` **antes** de gravar; conferidor de diff estrutural.
>
> **O pool `gm(key)`** sorteia o ÍNDICE e devolve `T("narracao.gm.<pool>.<i>")`. A ordem é o
> ponto: se o idioma fosse escolhido antes do sorteio, dois jogadores na mesma sala leriam
> **variantes diferentes do mesmo evento** — e isso seria invisível num teste de uma conexão
> só. O teste abre duas conexões em idiomas diferentes e exige a mesma variante. O `GM`
> continua no `server.py` como fonte do português; as 30 chaves moram no `narracao.js`.
>
> **O motor aprendeu a juntar listas:** um parâmetro pode ser uma LISTA, e o `t()` a junta
> com `lista.separador`/`lista.ultimo` (`" e "` × `" and "`), no servidor (`_param_texto`) e
> no cliente (`_valor` em `src/i18n.js`). Cada elemento pode ser ele próprio um `T`. Isso
> fechou a limitação do `nomes = " e ".join(...)` que a 4c havia registrado.
>
> **BUG PEGO NA REVISÃO, não por teste:** ao fazer `_equip_into_slot` devolver `T`, o site da
> 2ª arma virou `gm_say(log + " (2ª arma…)")` — e **`T` não tem `__add__`**, porque
> operadores são buscados no TIPO e não passam pelo `__getattr__` que faz o `T` se disfarçar
> de string. Equipar uma 2ª arma na mão esquerda quebraria com `TypeError`, e **as 17 suítes
> passaram verdes com o bug no lugar**: nenhuma exercitava aquele caminho. A ausência de
> `__add__` é uma **feature** — transformou perda silenciosa de tradução em erro alto. Hoje
> há teste exigindo que `T + str` estoure, e uma varredura contra o padrão voltar.
>
> **As formas irregulares** (13) foram à mão, por três motivos distintos: **ternário com
> string literal dentro** (`{'arma' if novo else 'desarma'}`) vira DUAS chaves escolhidas
> pelo mesmo booleano — a ordem das palavras muda entre idiomas; **`format_spec`**
> (`{fome:.1f}`) é pré-formatado; **concatenação com sobra** vira `T` aninhado (vazio quando
> ausente) ou lista. Duas se revelaram melhores: o `prefix` das armadilhas procedurais era
> `random.choice(GM["room_trap"])` — o pool —, e o `_ESMAGAR_PRESO` guardava o TEXTO na
> tabela, que passou a guardar a CHAVE.
>
> **Continua em português de propósito:** conteúdo autoral (masmorras, campanhas, falas de
> NPC, itens e monstros do editor) e as ~6 passagens de nome que a 4c documentou como fora
> das 8 famílias de catálogo. **Falta só a etapa 5** — a interface do cliente (~1.000).
> Spec/plano em `docs/superpowers/{specs,plans}/2026-08-13-idioma-etapa4b2-narracao-restante*`.
> Testes: `tools/test_narracao.py` (67), `tools/test_vocabulario_cliente.js` (45).

> **Idioma — fundação da interface (etapa 5.0 de 5):** prepara o terreno para traduzir as
> 7 telas do cliente; **nenhuma string é traduzida aqui**. O servidor já está 100%
> traduzido; restam **636 literais** no `game.js`.
>
> **A tradução do markup gerado virou responsabilidade do observador que já existia.** O
> cliente monta HTML por template string e o insere com `innerHTML` em **163 lugares**,
> contra 4 chamadas de `_i18nApply` — sem isso, cada tela traduzida dependeria de alguém
> lembrar de aplicar, e a dívida já aparecia nos 9 `_refreshX()` que o `_setLang`
> carregava. O plano mandava criar um `MutationObserver` novo; ao escrever o teste
> descobriu-se que **já havia um** observando `document.body` com `childList`+`subtree`,
> para injetar o ícone de habilidade (`game.js:153`). Estendido em vez de duplicado — um
> observador, duas tarefas —, e o teste **exige que continue havendo um só**. O nó só é
> tocado quando realmente traz `[data-i18n]`. **Medido:** 1.000 nós com marcador custam
> 8,1 ms contra 2,8 ms dos mesmos sem marcador, ou seja **5,3 ms**, com zero nós sem
> traduzir; o teto do spec era 300 ms.
>
> **O ícone de habilidade deixou de ser achado por TEXTO.** O `replaceAbilityEmoji` varria
> o texto renderizado procurando o nome em `ABILITY_NAME_TO_ID`, tabela chaveada em
> **português**: traduzir o nome faria os ícones sumirem, em silêncio, porque nenhum teste
> olha ícone. Agora o elemento `.skill-name` traz `data-ability-id`, emitido pelo render, e
> o scan por texto é retaguarda que some sozinha conforme cada sub-etapa migra os seus
> renders. **Cada sub-etapa da 5 tem de emitir o atributo nos renders que tocar** — provado
> em navegador que nome traduzido SEM o id fica sem ícone.
>
> **Convenção de chave da interface: `ui.<área>.<slug>`** (`ui.hud.encerrar_turno`),
> espelhando `narracao.<slug>` e `erro.<slug>`. As 38 chaves `ui.*` da etapa 1 já seguem.
>
> **`tools/test_interface.py` é o placar** das 7 sub-etapas: relata quantos literais em
> português restam por área e **cobra** as que já fecharam. Ao terminar uma sub-etapa, mova
> o nome da área para o conjunto `COBRADAS` no topo do arquivo — é isso que impede a área
> de regredir. Placar inicial: hud_acoes 153, mestre 135, cidade 97, ficha 86,
> selecao_heroi 58, render3d 50, modais 29, topo 28.
>
> **ARMADILHA DE VERIFICAÇÃO, irmã da que a 4b-i registrou:** ao provar mudança de
> CLIENTE, o navegador serve o `game.js` do **cache** e a prova sai falsa — a primeira
> medição do observador deu "não funciona" por isso. Recarregue com cache-buster
> (`?v=algo`) e cheque no próprio script que a versão nova está carregada, antes de
> concluir qualquer coisa. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-08-14-idioma-etapa5*`.

> **Idioma — Lote 1 da etapa 5: os catálogos estáticos do cliente.** Traduz os **131
> textos que moram em ESTRUTURA DE DADOS** do `game.js` (não em template de render).
> Placar **707 → 562**. Dicionário novo `src/lang/interface.js` (à mão, como o
> `erros.js`/`narracao.js`), convenção `ui.<área>.<slug>`.
>
> **HÁ DOIS CAMINHOS DE TRADUÇÃO NO CLIENTE, e quem decide é o servidor.** Este é o
> fato central do lote, e o que mais custou a descobrir:
> **(1) `I18N.aplicarCatalogo(obj, soNome)`** — quando existe `cat.<família>.<id>` no
> dicionário do servidor. Ele **muta o objeto**, trocando `name`/`nome` e (com
> `soNome=false`) `desc`/`descricao`. Usado pelo `GRIMORIO_CLIENT`, `ARMADILHAS_LUCCAS`
> e `CATALOGO_ITENS`.
> **(2) `_rotulo(id, prefixo, padrao)`** (`game.js`) — resolve `ui.<prefixo>.<id>` no
> **ponto de render**. É o caminho para tudo que o (1) não alcança.
> Uma chave `ui.*` **sozinha nunca é encontrada**: `_chaveBase` só fixa a base quando
> existe uma `cat.*`. Por isso `_CSD`, `_ELEMENTAL_HABILIDADES_LEWIS` e os mapas de
> rótulo foram para o `_rotulo` — inclusive os que são `{id:{objeto}}`, forma que
> *parece* servir para o `aplicarCatalogo` e não serve.
>
> **A chave `ui.*` vence a `cat.*`** quando as duas existem (`aplicarCatalogo`). Os
> catálogos do cliente guardam um card HTML com alcance e efeito por rodada, contra uma
> frase curta no servidor; a etapa 3 evitava o choque com `soNome=true`, e a chave própria
> resolve sem perder informação. As **27 magias têm `cat.magia.<id>.desc`**, então virar
> `soNome=false` ANTES de escrever as chaves `ui.magia.*.desc` substituiria os 27 cards
> pela frase curta — a ordem é load-bearing.
>
> **`_CSD` (tela de seleção):** cada skill ganhou `id` (de `ABILITY_NAME_TO_ID`, que tem
> **24** entradas) e o objeto ficou só com o que não é texto. Isso consertou o ícone na
> raiz: `abilityIconHtml` resolve por `ability?.id` e só cai no `ABILITY_NAME_TO_ID[name]`
> como retaguarda — sem `id`, a arte dependia do nome em PORTUGUÊS e sumiria em inglês.
>
> **Texto sem leitor foi REMOVIDO, não mantido como fallback** (4 casos achados por grep:
> `HERO_DATA[*].class`, os 3 campos de `habilidadeClasse`, o `resumo` das 27 magias, o
> array `skills` do mago sombreado por `selectionSkills`). Português que ninguém lê não
> tem onde chamar `t()`, e o placar não o distingue de trabalho pendente. **Grepe os
> leitores antes de traduzir qualquer estrutura.**
>
> **O placar aprendeu a não contar o `pt` load-bearing** (`tools/test_interface.py`): o
> `aplicarCatalogo` traduz mutando, então a string em português TEM de continuar no
> arquivo — ela é a fonte. A regra é **dupla**: o literal precisa ser o `pt` de uma chave
> `cat.*`/`ui.*` **e** estar em `BLOCOS_NAO_PENDENTES` (`GRIMORIO_CLIENT`,
> `ARMADILHAS_LUCCAS`, `ABILITY_NAME_TO_ID`). Só o casamento de texto produziu ~13
> exclusões indevidas, medidas — `cat.item.cleanse.nome` ("Purificação") apagava a
> HABILIDADE de mesmo nome. A anti-regressão deste lote **não é o `FECHADAS`** (que guarda
> FUNÇÕES, e aqui o escopo foi por ESTRUTURA): é a seção `[5]`, que exige que as
> estruturas continuem sem texto. Testes: `tools/test_interface.py` (22),
> `tools/test_vocabulario_cliente.js` (55). Plano em
> `docs/superpowers/plans/2026-08-14-idioma-etapa5-lote1-catalogos.md`, com a revisão de
> meio-caminho e os quatro fatos medidos que a motivaram.

> **Idioma — Lote 2 da etapa 5: as funções grandes do `game.js`.** Traduz os **203
> literais das 11 maiores funções** — e, ao contrário do Lote 1 (estrutura de dados),
> este mexe em **templates de render**: `t('chave')` dentro do template, `t('chave',
> {param})` quando há interpolação, `data-i18n` só onde o elemento inteiro é um rótulo
> FIXO (o `_i18nApply` usa `textContent`, e um elemento cujo conteúdo vem de `_rotulo`
> seria sobrescrito). Placar **396 → 350**; ao todo a etapa 5 saiu de 707 para 350.
>
> **O placar passou a atribuir cada literal à função de TOPO** (`RE_FN` ancorada na
> coluna 0). Antes, uma arrow interna de uma linha — `const L = (txt) => …` dentro de um
> render — virava "dona" dos literais da função que a contém: `L`/`add`/`mkSelect`/
> `_wToggle` levavam 51 que não eram deles. Isso tornava o recorte por tamanho de função
> um artefato E deixava o conjunto `FECHADAS` sem sentido (marcar `L` não impede
> regressão nenhuma). Hoje `FECHADAS` tem 10 funções e é a anti-regressão do lote.
>
> **`tools/js_strings.py` ignora comentário HTML dentro de template.** Um template
> multilinha conta como UM literal, então um `<!-- FOME E SEDE -->` no meio mantinha a
> função inteira no placar mesmo com todos os rótulos traduzidos. O comentário é para o
> desenvolvedor e o jogador nunca o vê.
>
> **LOOKUP POR TEXTO EM PORTUGUÊS É O DEFEITO RECORRENTE DESTA ETAPA — já apareceu
> quatro vezes.** `ABILITY_NAME_TO_ID` (5.0), as skills do `_CSD` (Lote 1), o
> `trapImages` do popup de armadilha e o `includes('não encontrada')` da tela de conta.
> O modo de falha é sempre o mesmo: **a arte some ou o ramo não dispara, em silêncio**,
> sem erro no console e sem teste que olhe imagem. **Antes de traduzir uma função,
> procure mapas e condicionais chaveados por texto.** Os consertos seguem um padrão só —
> mandar um **id** e casar por ele: `data-ability-id` nos botões de habilidade, `tipo_id`
> no `trap_result` (`_enviar_trap_result`, 16 sítios de chamada; dois deles não tinham
> `arm` em escopo e usam o literal `'buraco_escondido'`). O caso da conta **ainda não foi
> consertado**: funciona só porque `server.py:1856` devolve string crua, fora do `T()` —
> migrá-la quebra o cliente. Está comentado nos dois lados.
>
> **Duas armadilhas de execução, as duas pagas:** `renderPurchasedItems` declara `const t
> = document.createElement('div')`, que **sombreia o `t()` global** (use `_rotulo` ali); e
> o servidor rodando **trava a escrita** de `server.py`/`game.js` (`OSError: Errno 22`) —
> pare o preview antes de gravar por script, e note que um `node --check` depois de um
> write que falhou valida o arquivo ANTIGO e dá falso verde. Testes:
> `tools/test_interface.py` (24, com a checagem cruzada dos ids de `trapImages` contra o
> `ARMADILHAS` do servidor), `tools/js_strings.py` (10). Plano em
> `docs/superpowers/plans/2026-08-15-idioma-etapa5-lote2-funcoes-grandes.md`.
> **Falta o Lote 3:** 350 no `game.js`, 69 no `gameState.js`, 9 no `inventoryModal.js`.

> **Idioma — ETAPA 5 CONCLUÍDA (Lote 3): a interface do cliente.** Os **427 literais
> restantes** traduzidos — 350 no `game.js`, 67 no `src/gameState.js`, 9 no
> `src/ui/inventoryModal.js`. Com isto **o jogo inteiro está em PT/EN**: servidor
> (etapas 1–4c) e cliente (etapa 5). O dicionário tem **~3.000 chaves**, das quais
> **1.259 em `src/lang/interface.js`**.
>
> **Sobra UM literal em português no `game.js`, de propósito:** o
> `includes('não encontrada')` de `handleTileClick`, que é **chave de lógica** sobre a
> resposta do servidor — `server.py:1856` devolve aquela recusa como string crua, fora
> do `T()`, e traduzi-la quebraria em silêncio o ramo que oferece criar conta. O
> conserto certo é um **código de erro no payload**, e é trabalho próprio. O placar
> passou de relatório a **cobrança** e crava exatamente esse conjunto: qualquer outro
> literal derruba a suíte.
>
> **A grande lição do lote — `t` no lugar errado quebra de dois jeitos, e nenhum teste
> pegava:**
> - **`t` SOMBREADO.** Cinco funções declaravam `const t = …` local (`type || pointId`,
>   `getElementById('item-tooltip')`, `state.tiles[y][x]`). Chamar `t('chave')` ali dá
>   `TypeError` em runtime. As locais foram **renomeadas** (`tipo`, `tip`, `tile`), e não
>   o contrário: `t` passa a significar só o tradutor.
> - **`t` no NÍVEL DE MÓDULO (TDZ).** Um `const` de módulo inicializado com `t(...)`
>   roda no CARREGAMENTO, antes de `const t = …` existir — `ReferenceError` que **aborta
>   o resto do `game.js`**. Aconteceu com o `GUERREIRO_LUZ_BONUS_CLIENT`: o placar ficou
>   zerado, `node --check` passou (é sintaxe válida) e o jogo simplesmente não carregava.
>   **Só o console do navegador acusou.** A seção `[6]` do `tools/test_interface.py`
>   agora varre isso (ancorada na coluna 0, como a `RE_FN`), e foi negativamente testada.
>   Mapa `{id:'texto'}` de módulo vira **função** (`_labelCirculo`, `_glLabel`,
>   `_cancaoLabel`, `_predioNome`, `_csNome`) — nunca um `const` com `t()` dentro.
>
> **O placar aprendeu três categorias que NÃO são dívida** (`_pendente(linha, txt)`,
> extraída para poder ser testada com entrada sintética):
> - **literal que contém `data-i18n`** — é markup cujo português é a FONTE que o
>   `_i18nApply` substitui, como o `GRIMORIO_CLIENT` é a fonte do `aplicarCatalogo`. São
>   3 no `game.js`, e um deles é o `document.body.innerHTML` **inteiro** (13 KB num
>   literal só). A garantia de que isso não esconde trabalho é a **seção `[7]`**, que
>   varre esses literais atrás de texto acentuado FORA de um elemento marcado — foi ela
>   que apontou os 6 nós + 6 `title` que faltavam marcar.
> - **argumento de `console.*`** — diagnóstico do desenvolvedor. A faixa é a **chamada
>   inteira**, achada por parênteses casados: a 1ª versão olhava só a linha de abertura
>   e deixava passar as continuações de um `console.warn` de 5 linhas.
> - **`LITERAIS_INTENCIONAIS`** — hoje uma entrada: o `<option>` do seletor de idioma,
>   que fica sempre na própria língua.
>
> **`data-i18n-html`** (novo): para o bloco que MISTURA markup com o texto — o
> `#hint-host` tem `<b>` e `<code>` no meio da frase, e o `data-i18n` normal usa
> `textContent` e apagaria as tags. Só para texto NOSSO, nunca para conteúdo do servidor
> ou do autor. Fecha a última sobra visível, que estava fora de escopo desde a etapa 1.
>
> **`gameState.js` traduz sem conhecer o I18N.** A regra do `CLAUDE.md` proíbe
> `window`/`document` ali, e o `t` global mora em `window.I18N`. A saída é a mesma que o
> módulo já usava para o filtro de mensagens: **`GS.setTranslator(fn)`**, preenchido pelo
> `game.js` no boot, mais um `_t(chave, pt, params)` interno que cai no **português
> recebido** se ninguém registrou, se a chave falta ou se o tradutor lança. Por isso o
> português CONTINUA no `gameState.js`: ali ele é fallback, não dívida.
>
> **`_tentaFamilias` passou a aceitar `ui.<família>.<id>` além de `cat.`** — e isso era
> o que faltava para a regra "a `ui.*` vence a `cat.*`" valer de verdade. **40 dos 73
> itens do `CATALOGO_ITENS` só existem no cliente** e nunca terão uma `cat.*`; sem essa
> mudança a base ficava nula e o objeto passava intacto — o sintoma exato que o Lote 1
> registrou como "chave `ui.*` sozinha nunca é encontrada". Com ela, e com as 26
> descrições de topo já cobertas por `ui.item.<id>.desc`, a chamada virou
> `aplicarCatalogo(GS.CATALOGO_ITENS, **false**)`. **A ORDEM é load-bearing**: virar o
> `soNome` ANTES de escrever as chaves faria a `cat.item.<id>.desc` do servidor (frase
> curta) substituir o texto mais rico do cliente.
>
> **Migrar por script exige que o texto venha do PLACAR, não de heurística.** A 1ª versão
> do migrador da cauda escolhia "o maior literal da linha" e, em 6 de 72 linhas, trocou um
> **ID ou uma cor CSS** por uma chamada de tradução (`'resistencia'`, `'passiva'`,
> `'var(--orange)'`, `'btn-tile-spacing-reset'`) — `node --check` passa e o estrago é
> silencioso. Refeito lendo `test_interface._literais_pendentes()`, que já sabe qual
> literal é texto de interface, e recusando linha com mais de um candidato.
>
> **Teste de REGRA não pode depender do conteúdo que a regra mede.** A checagem "texto
> não dicionarizado continua contando" cravava a frase `"Personagem já escolhido"` e ficou
> vermelha sozinha quando o lote a traduziu. Virou entrada **sintética**, cobrindo os três
> cruzamentos de dicionário × faixa. Na mesma linha, o `test_idioma_cliente.js` carregava
> **só o `strings.js`** e acusava como órfã toda chave `data-i18n` que morasse nos outros
> cinco arquivos de `src/lang/` — passou a carregar os seis, como o `index.html` faz.
>
> **UI MONTADA UMA VEZ não acompanha a troca de idioma — a lacuna que o Lote 3
> deixou passar.** O `_i18nApply` só alcança quem tem `data-i18n`, e um render que
> roda a cada `game_state` se conserta sozinho (o `set_lang` faz o servidor reenviar
> o estado). Quem NÃO se conserta é a UI com guarda de cache: `initCityImage` tem
> `if(_cityImg) return` e assa os rótulos dos hotspots no `innerHTML`; a seleção de
> herói (`initClassSelectFull`, `if(csf) return`) assa o nome do herói numa **textura
> de canvas** na placa do peão 3D. Quem entrava na cidade em português e trocava para
> inglês continuava vendo *Taverna/Ferraria/Mercado*. O `_setLang` já mantinha uma
> lista para "rótulos montados em JS" (`_refreshTurnTimerOption`,
> `_refreshBtnReconectar`); entraram nela **`_refreshCityHotspots`** (repinta rótulo,
> `title` e `aria-label`, pulando `data-city-nome-autoral` — nome do editor não se
> traduz) e **`_refreshClassSelectLang`** (derruba e remonta a cena, única forma de
> repintar a textura; preserva seleção, travas e retrato). **Regra: UI nova com guarda
> de "monta uma vez" precisa de uma linha no `_setLang`.**
>
> **Faixas de dificuldade:** `src/difficulty.js` é compartilhado com o editor e é **puro**
> (sem DOM, sem I18N — como o `gameState.js`), então ele segue entregando `label` em
> português; quem traduz é o `game.js`, por `ui.dificuldade.<key>` no render do minimapa
> de CR do mestre (`_faixaLabel`). Achado DEPOIS do fechamento, medindo os `src/*.js` que
> o placar não cobre: `Fácil`/`Equilibrada`/`Difícil`/`Mortal` apareciam na tela do
> mestre. **O placar mede o `game.js`; os outros módulos precisam de conferência à mão.**
>
> **Fora da etapa 5, de propósito:** o **editor** (`tools/*.js` — 423 literais de
> interface real, mais 813 de catálogo GERADO e 89 de teste), o **conteúdo autoral**
> (masmorras, campanhas, falas de NPC, itens e monstros do editor) e o nome de **jogador**.
> Testes: `tools/test_interface.py` (35), `tools/js_strings.py` (10),
> `tools/test_idioma_cliente.js` (32). Plano em
> `docs/superpowers/plans/2026-08-15-idioma-etapa5-lote3-cauda.md`.

> **Etapa 5 — dois furos achados DEPOIS do fechamento, os dois estruturais.** O placar
> cravava zero e o jogo ainda tinha português na tela. As causas não eram texto
> esquecido: eram o instrumento e o gerador olhando para o lugar errado.
>
> **1) O tokenizador pulava o conteúdo de `${...}`.** `js_strings.literais()` tratava a
> interpolação como "código, não texto" — correto para `${n}`, errado para
> `${cond ? `<b>Texto</b>` : ''}`. Funções como `renderMyPanel` devolvem TEMPLATE de
> dentro de uma IIFE no `${}`, e **31 textos do `game.js` nunca foram contados** — entre
> eles os banners do HUD (`SACIADO`, `EXAUSTÃO`, `EM CHAMAS`, `ÚLTIMO ESFORÇO`,
> `RÉQUIEM`, `REGENERAÇÃO DIVINA`), que o jogador em inglês via em português. O
> tokenizador passou a **RECURSAR**: o buraco segue marcado como `${}` no texto de fora
> e o que houver de string dentro vira literal por si. O placar saltou de 1 para 32 e
> voltou a 1 depois de traduzir.
>
> **2) O gerador de vocabulário não via as habilidades de herói.** Elas vivem em
> `CLASSES[x]["skills"]`, não num catálogo de topo, então nenhuma varredura as
> alcançava: **24 habilidades, 49 chaves, zero traduzidas**. O menu de habilidades e os
> botões do HUD mostravam "Veneno Rápido / Ação livre. Unta um veneno…" em inglês.
> `gerar_vocabulario.py` ganhou a família **`habilidade`** (helper `_skills_de_classe`),
> e o `src/i18n.js` a registrou em `FAMILIAS_POR_CAMPO.id` e em `TODAS_FAMILIAS`. Foi
> preciso ainda acrescentar **`description`** a `CAMPOS_DESC`: o servidor escreve a
> descrição da habilidade nesse campo, e sem ele o nome traduzia e a descrição não.
>
> **A lição comum:** *o placar mede o que o instrumento sabe olhar.* Zero no placar não
> é prova de tradução completa — é prova de que nada do que ele enxerga sobrou. As duas
> falhas só apareceram **rodando o jogo de verdade** (subir sala, escolher classe,
> entrar na masmorra e varrer o DOM em inglês), não em suíte nenhuma.

> **Etapa 5 — a rodada de bugs relatados pelo autor (o placar mentia de novo).**
> Quinze pontos de português na tela com o placar em zero. Três causas, todas de
> instrumento:
>
> **1) O check `[7]` só olhava texto ACENTUADO.** É a mesma armadilha que o Lote 2
> registrou ("o placar zerar não prova que a função está traduzida"), mas aplicada ao
> markup: `Iniciar Jogo`, `Encerrar Turno`, `Aventureiros`, `Fechar`, `SALA`, `Loja`,
> `Meu Personagem` — nenhum tem acento, e todos ficaram sem `data-i18n` no
> `document.body.innerHTML`. **34 marcadores** acrescentados. A varredura passou a ser
> independente de acento: dentro de markup, QUALQUER texto com letra sem `data-i18n`
> é dívida.
>
> **2) Os 42 rótulos de `dice_roll` do servidor nunca foram migrados.** Não são
> `gm_say` nem `err`, então a varredura da etapa 4b-ii não os via — e o dado 3D
> mostrava `Dano`/`Golpe Sagrado`/`⚔️ Ataque (Mão Principal)` em português. Agora são
> `T("dado.<slug>")`, resolvidos pelo `default=` do `json.dumps` como todo o resto.
> **Erro cometido e desfeito no caminho:** a 1ª migração trocou TODO `"label":` do
> `server.py`, inclusive no `CANCAO_ATRIBUTOS`, que é avaliado no CARREGAMENTO — o
> módulo parou de importar com `NameError: T`. É o TDZ do lado do Python. O conserto
> restringiu a troca ao contexto `dice_roll` (3 linhas acima) e o `label` do
> `CANCAO_ATRIBUTOS` saiu da estrutura: virou `ui.cancao.atributo.<id>`, resolvido na
> narração como **lista** de `T` — o motor já sabe juntar lista, e `", ".join` exigiria
> `str` de verdade, que o `T` não é.
>
> **3) `test_idioma` [10] acusava `ui.cancao.atributo.` como chave órfã** — é o PREFIXO
> de uma chave montada em runtime. Prefixo terminado em ponto nunca é chave real; o
> scanner passou a descartá-lo.
>
> **O que continua em português DE PROPÓSITO: conteúdo autoral.** Os itens que o autor
> relatou como "ainda em português" e que NÃO são bug: `Fazenda do Leste`
> (`city_map_points.json`), `Refugio dos Heróis`/`Area compartilhada`/`Quarto do herói`
> (`city_scenes.json`), `Vila dos Charcos` (`cidades_personalizadas.json`) e
> `esconderijo de Leonel` (`world_adventures.json`) — todos criados nos editores. A
> guarda por id preserva o texto do autor de propósito; traduzi-los exigiria um campo
> de nome por idioma no editor, que é feature, não correção.

> **Idioma — placar sem acento, fumaça do handler e placar único (2026-09-14).**
> (1) `tools/js_strings.py` deixou de contar só literal COM acento: `parece_portugues()`
> usa também um **vocabulário derivado do dicionário** (palavra em algum `pt` de
> `src/lang/*.js` e em nenhum `en`, com os `{parâmetros}` removidos), descartando
> identificador, seletor CSS e texto só dentro de tag. O placar saltou de 17 para 526 —
> `⚔ Atacar`, `Rodada`, `SUA VEZ`, `FALHOU`, `Continuar`… estavam em português no HUD em
> inglês com a etapa 5 "concluída". Traduzidos até sobrar o WIP do autor. O tokenizador
> também ganhou scanner recursivo de `${}` (string, template aninhado e regex dentro do
> buraco — `.replace(/'/g, …)` dessincronizava tudo). (2) **`tools/test_handler_smoke.py`**
> dirige o `server.handler` REAL com um WebSocket falso (async iterator; passos podem ser
> funções que leem `S.rooms`): ciclo do jogador em EN com queda e rejoin + mestre EN/herói
> PT simultâneos. É a única suíte que passa pelo laço de conexão — onde morava o bug do
> idioma no rejoin (`set_lang` grava `LANG_BY_PID` sob o pid da conexão nova; o rejoin
> troca `pid` pela identidade antiga; corrigido carregando a entrada nos dois ramos). Use
> `r._liberar_intro_masmorra(True)` em vez de dormir 3 s; leia posição DURANTE o roteiro
> (a queda põe o peão em `[-1,-1]`). (3) **`tools/dividas.py`** é o placar ÚNICO das
> dívidas de idioma — erros (inclusive f-string), `gm_say` cru, rótulos de `dice_roll`
> crus, chaves órfãs, interface do `game.js` por função e chaves sem `en` — para traduzir
> ao fechar cada feature; `--json` e `--strict` (sai 1 se houver dívida, p/ pre-commit).
> Ele revelou o que nenhuma suíte cobrava: 52 rótulos de dado e 20 erros em f-string.

> **Animação de combate híbrida (3D):** o atacante **arma, espera o d20 assentar e
> golpeia**; o alvo balança (acerto) ou esquiva (erro); **crítico e morte** ganham flash
> emissivo, empurrão maior, hit-stop, shake de câmera e partículas; o peão morto **tomba**
> antes de virar lápide. Núcleo: módulo puro `src/combatScene.js` (`window.CombatScene`,
> sem DOM/THREE, testável em node) com **uma cena por `attack_id`** — fases
> `FILA→ARMANDO→ESPERANDO_DADO→GOLPE→(HOLD)→RECUPERANDO→AGUARDANDO_HANDOFF/MORRENDO→FIM`
> — que devolve **poses por chave de entidade** (`poseFor(key, now)` → `{base,dx,dz,tilt,
> tiltDir,scaleY,flash,opacity,darken,dying}`) e comandos (`impact`/`end`). **Sem mudança
> de servidor:** `attack_feedback` (start/result) já traz tudo. Sincronia: o d20 3D chama
> `CombatScene.dieSettled` ao assentar e a cena mais antiga com `result` consome o primeiro
> dado; fallbacks `waitDieMs` (3,5 s), `instant` (colapsa), `result` sem `start` (só
> impacto), `expireMs` (6 s) — **timeouts NÃO passam pela `duration` injetada** (em
> `instant` ela devolve 0,001 ms e a cena expiraria no frame seguinte; foi um defeito do
> plano pego em revisão). **Hand-off:** `_detectHpChanges` entrega o dano
> (`CombatScene.pendingFor(key, now)` → `handoff`) à cena, que solta número/cue no golpe;
> hand-offs **acumulam** (`impact.feedbacks[]`) — a morte do herói chega por
> `_capturarDerrotasERessurreicoes` e o número pelo diff de HP, no mesmo golpe; uma cena já
> golpeada recebe o hand-off tardio como comando `tardio:true` (sem repetir partículas). Sem
> cena (magia, armadilha, veneno) o caminho comum mostra o dano pela variação de HP. Os
> números ficam acima e centralizados no footprint: em 3D usam o topo real da miniatura,
> em 2D o centro e tamanho do footprint.
> **Aplicação** em `_aplicarPoseCena` (fim do laço por peão de `startLoop3D`): a base é
> **`pose.base`** (posição autoritativa que veio no `attack_feedback`), gravada em
> `userData.gridX/gridY` na trava da pose — `gridX` sozinho fica DESATUALIZADO quando um
> monstro anda (`entity_step`) e ataca sem `game_state` no meio; inclinação por
> `rotateOnWorldAxis` (Euler XYZ + facing misturaria eixos); materiais **clonados por peão**
> no primeiro flash (`_sceneMats`; o GLB é marcado `isGroundDecal` E `isGLB` — o filtro é
> `isGroundDecal && !isGLB`, senão o flash nunca alcança a miniatura; contorno recebe só
> opacidade). **Shake**: subtrai o offset antes de `controls.update()` e soma depois (senão o
> OrbitControls absorve). **Morte** reusa `_mortesVisuaisPendentes` (`_agendarFimMorteVisual`
> espera `isDying`; o comando `end` chama `rec.concluir()` **sincronamente** antes da
> travessia do mesmo frame, senão o morto reaparece em pé por alguns quadros; herói é
> reinjetado `alive:true` em `_estadoComMortosVisuais`; cadáver `visible=false` até o fim).
> Vale para **monstro e herói**; servo animado e prisioneiro ficam **fora** (não há registro
> de morte pendente para eles — o peão some no próximo `game_state`; a cena expira sozinha).
> **Ressalva:** `rec.concluir()` é síncrono EXCETO enquanto uma miniatura anda
> (`renderMap3D` retorna cedo com `estadoMovimento.emMovimento`) — por isso o ramo `end`
> esconde a fig do morto (`visible=false`) ANTES de concluir; o reconcile a descarta depois.
> **Spoiler do resultado:** com cena, o banner legado (`_attackFeedbacks`) e o cue de
> crítico/erro NÃO saem no `result` (que chega 1–3 s antes do golpe): `_receiveAttackFeedback`
> põe `resultAt=Infinity` + `cueAdiado`, e o comando `impact` (não-tardio) revela e toca;
> `end` (cena expirada) e o tick do banner (cena sumida por `reset()`) destravam por segurança.
> Um d20 descartado no ar por `_clearDiceVisuals` (novo burst) chama `dieSettled` antes de
> sumir, senão a cena esperaria o `waitDieMs`. Uma cena cujo `result` já é ERRO nunca é
> candidata a hand-off (`cenaParaHandoff`) — senão absorveria o número do acerto seguinte.
> `dispose3D` faz `CombatScene.reset()`. Números em `VC.feedback.combat.scene`. Provado no
> navegador (2026-09-11): número do acerto saiu no golpe (2,36 s), 100 ms após o dado
> assentar; morte tombou e desvaneceu antes da lápide. Teste: `tools/test_combat_scene.js`
> (204 checks: módulo + checagens estáticas de fiação). Spec/plano em
> `docs/superpowers/{specs,plans}/2026-09-10-animacao-combate-hibrida*`.

> **Sacudida Jurássica do Tiranossauro Rex (passiva) + RD 4 só contra armas comuns:**
> a ficha do T-Rex (`server.py`, bloco dos tiranossaurídeos) trocou a **ação**
> `sacudida_brutal` (recarga 5) pela **passiva** `sacudida_jurassica` (`bite_damage`/
> `extra_damage`/`wall_damage`/`throw_distance`), e a RD virou `common_weapon_only`
> como nos outros dois tiranos. Dispara em `_tirano_inicio_turno` — chamado no prólogo
> `_upkeep_inicio_turno_monstro`, comum à IA e à janela Manual do mestre — para cada
> presa adjacente: `_tirano_sacudida_jurassica` narra, rola `mordida+2d6` (físico, sem
> save, passa pela RD da vítima), solta, arremessa `throw_distance` casas na direção
> "para longe" (`_direcao_para_longe`, medida da casa do footprint 2×2 mais próxima, não
> da âncora) e, se o voo parou num **obstáculo sólido**, soma `wall_damage`. **Com a
> passiva na ficha, as Mandíbulas NÃO aplicam o `automatic_damage`** (a mordida já vem
> embutida; a regra é do código, porque o validador do editor preenche o campo com
> default). O T-Rex age normalmente depois. Tirano da Mata/Ancestral seguem com
> `sacudida_brutal`+dano automático, byte-idênticos (`_tirano_bite_expr` foi extraído
> para os dois usarem). **`_empurrar` mudou para todo mundo:** a checagem `tiles == WALL`
> virou `_blocks_tile` (parede, porta fechada, decoração sólida) e a borda do mapa
> passou a marcar `parede=True` — antes qualquer empurrão atravessava porta fechada e
> decoração. Criatura no caminho continua interrompendo sem contar como parede. Editor:
> ramo `sacudida_jurassica` no validador (2 sites) e no `editor_monster_editor.js`
> (reusa os inputs `.me-tirano-shake-*`). Chaves `narracao.sacudida_jurassica` e
> `narracao.sacudida_jurassica_colisao`. Spec em
> `docs/superpowers/specs/2026-09-13-sacudida-jurassica-tiranossauro-design.md`. Teste:
> `tools/test_tirano.py` (seções [2b]–[2g]).

> **Projéteis no 3D (frente B):** flecha/virote/lança (malha procedural orientada pela
> trajetória) e itens arremessados (PNG do item girando; emoji em canvas como fallback)
> **voam do atacante ao alvo quando o d20 assenta** e o impacto acontece **na chegada**.
> **Servidor:** `_projetil_de(defn, monstro=False)` (module-level, ao lado de `RANGED_AMMO`)
> deriva `{"kind": arrow|bolt|spear}` — herói pela arma (`_PROJETIL_POR_ARMA`, `ammo` do
> editor **ou** a família de `RANGED_AMMO`, porque a cópia de combate `p["weapon"]` não
> carrega `ammo`; arma de haste com `range` como chicote/alabarda NÃO tem projétil),
> monstro/servo por `projectile` explícito no ataque ou `range≥2` + `perfurante` (kobold
> besteiro declara `bolt`; a lança do kobold, `spear`). Vai como campo opcional
> `projectile` no `attack_feedback start` (`_emitir_feedback_ataque` descarta `None`).
> **`handle_throw_item` passou a emitir `attack_feedback`**: `ataque_alvo` = start antes do
> d20 + result (`kind:"item"` + `item_id`/`item_emoji`/`item_elemento`); `area` = alvo
> sintético `{id:None, pos:[cx,cy]}` (`target_name` vazio) com `area`/`area_raio`/`sem_dado`
> e result imediato. Lacunas aceitas: `_monster_throw_item` (mestre/IA arremessando item)
> não emite feedback; `handle_arremesso_lanca` do herói é **código morto** (sem despacho);
> o save de criatura do editor descarta `categoria`/`projectile` da ficha.
> **Cena (`src/combatScene.js`):** `projectile` normalizado na cena (`enabled:false` no cfg
> ignora o campo), `melee=false`, `travelMs = clamp(dist×msPerTile[kind])` com cadeia de
> fallback por kind (override parcial de `msPerTile` não dá NaN) e passando pela `duration`
> (é animação, não timeout); `entrarGolpe` emite o comando **`launch`**
> `{kind,item_id,item_emoji,item_elemento,from,to,dir,travelMs,flightMs,hit,fumble,crit,area,area_raio}`
> e o `GOLPE` dura `travelMs` → impacto na chegada; erro estende `to` 1 casa além na
> **velocidade efetiva** (`flightMs = travelMs×(dist+1)/dist`; impacto/esquiva na passagem
> pelo alvo); fumble encurta `to` a meio caminho e o alvo **não** esquiva; `sem_dado` pula
> `ESPERANDO_DADO` e `dieSettled` ignora a cena (senão roubaria o d20 de um save); cena de
> área não tem `targetKey` (`cenaParaHandoff` a ignora) e fecha sozinha após recuperar.
> `impact` carrega `projectile`/`area`/`area_raio`. Sem `projectile` → byte-idêntico.
> **`areaImpactAt(pos, now)`** (irmã pura de `pendingFor`): instante estimado da chegada
> de um arremesso de ÁREA que cobre `pos` — o `game_state` com o dano chega **na mesma
> rajada** do `start`, antes de qualquer `tick`, então a estimativa pré-lançamento é
> `(phaseAt se ARMANDO, senão now) + windup + travelMs` (≤1 quadro de erro; cena enfileirada atrás de outra do mesmo
> atacante subestima — aceito, igual ao portão da bola de fogo). **Render (`game.js`):**
> `_projeteis` + `_projetilLancar/_projetilUpdate3D/_projetilQuebrar/_projetilDispose3D/`
> `_projetilTickTodos/_projetilLimparTodos` (família `_bolaFogo*`; parábola `from→to`,
> `lookAt` na tangente; PNG via `TextureLoader` trocando o mapa do sprite de emoji quando
> chega — esse material NÃO é clonado, o callback escreve nele; malhas clonam materiais uma
> vez no pouso, marcados `_projOwned`; seta errada crava com guinada `atan2(dx,dz)` +
> `rotateX(+0.19π)` — sinal positivo leva a ponta (+Z local) ao chão, validado; item errado
> cai a `y=0.15`; item acertado quebra com burst na cor do elemento
> `_PROJETIL_COR_ELEMENTO` + anel expansivo de 400 ms na área); tick em `_tickCombatScene`;
> limpeza em `dispose3D`/`init3D`. Números de área esperam a chegada por
> `_projetilFeedbackStartAt` (o mais tardio entre a lista de render e
> `CombatScene.areaImpactAt`; o diff de HP usa o mais tardio dele e de
> `_bolaFogoFeedbackStartAt`). Config em `VC.feedback.combat.scene.projectile`. Provado no
> navegador (2026-09-13): flecha do herói lançou ao assentar o d20 e a morte do goblin saiu
> em `impactAt`; flecha do arqueiro errou, cravou 1 casa além e sumiu após `stickMs`;
> frasco errado caiu 1 casa além; bomba: anel + números com `startAt` ≈ chegada
> (550/671 ms vs impacto 591); `instant` sem voo e sem erro no console. **Armadilha da
> prova:** com a janela do app oculta, `requestAnimationFrame` não dispara e a cena fica
> parada em `FILA` — polyfill de rAF por `setTimeout` + `startLoop3D()` e captura por
> `renderer.render()` + `toDataURL()` em vez de screenshot. Testes: `tools/test_projeteis.py`
> (servidor, 40 checks), `tools/test_combat_scene.js` (`[35]`–`[41]` + `[33]`, 264 checks).
> Spec/plano em `docs/superpowers/{specs,plans}/2026-09-12-projeteis-3d*`.

> **Sistema de MP removido (2026-09-15):** o fluxo genérico `skill` → `handle_skill` → `_apply_skill` (18 habilidades das 6 classes genéricas originais, custo em `mp`) era código morto — toda classe tinha `mp: 0`, nada o incrementava e o HUD nunca chegava ao ramo 💙. Saíram: a mensagem `skill`, `handle_skill`/`_apply_skill`, as 3 magias de MP da ficha do Pedro (`fireball`/`ice_lance`/`magic_shield`), os campos `mp`/`max_mp` do jogador (e da whitelist `_DURABLE_FIELDS` do savegame — save antigo com `mp` é ignorado), o estado que só elas alimentavam (`self.taunted`, `self.immune`, `self.smoke`, `self.temp_def_turnos` — `self.blessed` e `self.temp_def` FICAM, têm outros escritores), o ramo `skill` da mesa livre do editor, e no cliente `GS.activateSkill`/`notifySkill`, `beginSkill`, `_aimStartPendingSkill`/`_aimHoverPendingSkill` e os ramos `enemy`/`ally` de `pendingSkill` em `resolveTileClick` (o `pendingSkill` segue vivo só para o desarme de armadilha). 56 chaves de idioma órfãs apagadas (`dividas.py` limpo). Efeito colateral no instrumento: o placar de `test_interface.py` passou a reconhecer o 3º argumento de `_rotulo(id, prefixo, padrao)` como fallback (não dívida) — a sigla `DES` só era "inglês" porque a narração removida da Chuva de Flechas a continha.

> **Handlers órfãos e fallback de turno removidos (2026-09-15):** saíram os 3 handlers de *scaffolding* nunca despachados (`handle_ataque_adaga_secundaria`, `handle_arremesso_adaga_secundaria`, `handle_arremesso_lanca` + helpers) — usavam `stats_mod`/`gear['arma']`/`_get_personagem`, nada disso existe; o arremesso real é `throw`. E saiu o bloco `# Advance turn` de `handle_end_turn` (turno por `player_order`/ `turn_index`, anterior à iniciativa): `initiative_active` liga em `enter_dungeon` e nunca desliga, então o bloco era inalcançável no jogo real. **Bug real achado ao remover:** a conversão do Fosso (`fosso_pular_proximo_turno` → `fosso_turno_perdido`, que faz o herói perder a rodada e depois REAPARECER) só existia dentro desse bloco morto — no jogo real, quem caía num fosso ficava `fosso_oculto` (invisível e intocável) para sempre. Portada para `_start_initiative_player_turn`, ao lado do `perde_turno`. `test_fosso` e `test_senhor_das_aguas` passaram a montar a fila de iniciativa (`initiative_active=True`) em vez de depender do fallback. `turn_index` continua existindo (lido pelo Ataque Coordenado e pelo fallback de `current_pid`), mas já não era incrementado por ninguém. **Regra que se repete** (ver também "Manual pula a gm_phase"): ao implementar efeito de início de turno, o lugar é `_start_initiative_player_turn` (herói) / `_upkeep_inicio_turno_monstro` (monstro) — não `handle_end_turn`.

> **Miniaturas procedurais de herói removidas (2026-09-15):** as 14 funções `_miniWarrior/_miniMage/_miniRogue/_miniCleric/_miniVictor/_miniPaladin/_miniBard/_miniGenericHero` (peão 3D da masmorra) e `_cWarrior/_cMage/_cRogue/_cCleric/_cBard/_cPaladin` (vitrine da seleção), mais as 6 fábricas de material `_cClth/_cGold/_cLth/_cWood/_cSkin/_cGlow` que só elas usavam — ~2.680 linhas de `game.js` sem nenhuma referência. O herói na masmorra é GLB (`_GLB_ENABLED_CLASSES`) ou billboard PNG (`_makeCharacterPawn`); a seleção usa `_cHeroPNG`. As `_miniGoblin/_miniSkeleton/…` de **monstro** continuam vivas como último fallback (GLB → PNG → procedural) dos 6 legados.

> **Órfãs do cliente removidas (2026-09-15):** 21 funções do `game.js` sem nenhuma referência + os helpers que só elas usavam (~890 linhas) — resquícios do **modelo client-side de loja** (`renderPurchasedItems`, `renderFichaPedro`, `renderBotoesAcaoBonus`, `onClicarTaverna/Ferreiro/Mercado`, `usarItemComprado`/`equiparComprado`/`desequiparComprado`, `GS.aplicarConsumivel`/`equiparItemComprado`/`desequiparItemComprado`/`podeEquipar`), os **ícones 2D em canvas** (`drawWeapon`/`drawArmor`/`drawLegs` + 16 `_w*`/`_a*`; o sprite 2D procedural `drawWarrior…` FICA como fallback da `frente.png`), cópias antigas de coisas vivas (`_escolherDirecaoInstrumentoLegacy` → mira no tabuleiro; `_rogueDesarmarBtn` → ramo de `_rogueSkillBtn`; `_animationDuration` → `_animationProgressDuration`; `_getDiceArea`; `_getStoneTopTex`; `_tempestadeTargetMesh`; `_addLinha`; `_monConjurador`; `isMobile`; `aplicarTooltipAoItem`/`mostrarTooltip`; `_protecaoEnergiaHash`) e o **botão oculto "Entrar na Masmorra"** (`triggerDungeonEntrance`, `#city-dungeon-bar`, CSS) — a entrada é pelo ponto de masmorra (`abrirEntradaMasmorra`); no `_cityClick` da cidade 3D (`CITY_MODE` fixo em `'image'`) o id `dungeon` passa a cair no `_cityHotspotClick`. 45 chaves `ui.*` órfãs apagadas. **Ficaram por decisão do autor** (features prontas, nunca ligadas): `_abrirEscolhaLootOuAtaque` (escolha "pegar item ou atacar" com monstro sobre item) e `playHeroHurt`/`playCreatureHit` (sons de dano distintos).

> **Ira da Rocha Ardente — 7 correções de mecânica/animação (2026-09-17):** **(1)** a
> validação da mira (centro/alcance/parede/piso) saiu do executor para um
> **`_ira_rocha_preflight`** chamado em `handle_magia` ANTES de cobrar slot/🍖💧/ação
> (espelha `_tempestade_preflight`; antes um clique atrás de uma parede gastava o slot de
> 4º círculo sem efeito) e o cliente ganhou `MAGIAS_AREA_EXIGEM_LOS` em `_specAlvoMagia`
> — só as 7 magias de área cujo executor exige LOS ao centro (Silêncio/Clarividência ficam
> de fora). **(2)** a área das Chamas Vivas é `lado + 2` (anel completo); `lado + 1` caía na
> âncora assimétrica do quadrado par e a casa extra ficava só de um lado, mudando de lado
> com o nível. **(3)** `_iraRochaUpdate3D` usava `bright`, declarado só em `_iraRochaBuild3D`
> → `ReferenceError` no exato instante do impacto em 3D (onda nunca aparecia, véus ficavam,
> e `_iraRochaRaf` guardava um id morto, então NENHUMA Ira seguinte animava na sessão).
> Paleta em `IRA_ROCHA_CORES`; `_tickIraRocha` isola o erro por animação e renova o raf num
> `finally`. **(4)** `dmg_mult` (Empoderar Magia ×1,5) agora chega à Ira e fica gravado na
> zona (`dano_lava`/`dano_mult`); `_aplicar_lava_se_pisar` consulta `_dano_lava_em(tiles)`
> — lava do mapa segue 2d6. **(5)** `_aplicar_fogueira_se_pisar` é footprint-aware (chama sob
> a casa de trás de um monstro 2×2 queima; conta 1× por criatura, vale o dado mais forte).
> **(6)** servo animado, prisioneiro e licantropo passaram a chamar a fogueira ao pisar (5
> caminhos de movimento só aplicavam lava). **(7)** portão `_iraRochaFeedbackStartAt` em
> `_detectHpChanges` (números de dano esperam a onda chegar à casa, como a Bola de Fogo) e
> crosta `IRA_ROCHA_CROSTA_OPACIDADE=0.92` com `depthTest:true` (a lava autoritativa chega no
> `game_state` junto do `start`; com 0.22 estava 78% visível desde o 1º quadro). Menores: a
> colocação das chamas revalida contra as decorações de agora; a narração cita rodadas
> RESTANTES. Testes: `tools/test_ira_rocha_ardente.py` (51, seções [6]–[11]) e
> `tools/test_ira_rocha_cliente.js` (19, node — extrai as funções do `game.js` e roda com
> stubs de THREE). **Atenção ao editar:** `game.js`, `server.py` e `CLAUDE.md` estão em
> **CRLF** — script Python com `replace("...\n...")` não casa; use a ferramenta de edição.

> **Tempestade de Ciclones — 6 correções (2026-09-17):** **(1+2)** o prólogo do monstro
> (`_upkeep_inicio_turno_monstro`) consome `turbilhao_perde_movimento` com **`pop`** — com
> `get`, o `return False` da perda de ação pulava os `pop` tardios de `gm_phase` e o monstro
> que falhava o Reflexos perdia o movimento em DOIS turnos; e o caminho legado da IA (fichas
> sem `ai_type`: skeleton/orc/dark_mage/dragon/pombo/rato/gato/ovelha) não tinha `pop`
> nenhum — um esqueleto atingido uma vez ficava imóvel para sempre. **(3)** o BFS de alcance
> do cliente cobra o vento: `terrainMoveCost` (`src/gameState.js`) soma
> `_custoVentoTempestade` (2 por casa de tempestade confirmada, também para voadores — a
> prévia com `ciclones_pendentes` não conta), espelhando `_water_step_cost`; antes as casas
> azuis mostravam o dobro do alcance e o caminho parava no meio com erro do servidor.
> **(6)** `handle_comandar_animados`, `_animado_ataca_jogador` e `_turno_licantropo` chamam
> `_tempestade_verificar_entrada` ao pisar (só os caminhos manuais chamavam). **(4+5,
> só no cliente e dependentes do WIP da reconciliação de ciclones):** a prévia pendente
> entra em `ativos` no `_tempestadeSyncFromState` (a anim do `start` era morta pelo
> `game_state` que chega junto dele) e `_tempestadeUpdate3D` refaz o grupo quando
> `cycloneMeshes` não bate com `anim.ciclones` (as malhas nasciam com 0 ciclones e o
> resolve nunca as criava — tempestade sem tornado em 3D); `_tempestadeBuild3D` zera as
> 8 listas, não 4 (rebuild acumulava malhas do grupo descartado). Testes:
> `tools/test_tempestade_correcoes.py` (15) e `tools/test_tempestade_cliente.js` (12; as
> seções [1]/[2] se pulam num checkout sem a reconciliação).

> **Prisão de Chamas — 4 correções (2026-09-17):** **(1)** `_prisao_chamas_preflight`
> (lado ∈ {2,3,4}, centro, alcance, LOS, chão) chamado em `handle_magia` ANTES de cobrar
> slot/🍖💧/ação — e antes de consumir as técnicas armadas: uma mira inválida desarmava o
> Empoderar de graça. **(2)** `dano_mult` gravado na zona e lido ao pisar e no início do
> turno (Empoderar ×1,5 / Fortalecer ×1,25 valiam só no impacto), igual à lava da Ira.
> **(3)** portão único `_zonaFogoLiberada(z)` (despacha por tipo: Bola de Fogo →
> `_bolaFogoZonaLiberada`, Prisão → `_prisaoChamasZonaLiberada`) nos 3 pontos de render
> das zonas de fogo — a parede persistente (`spellLivingFlameFx`/overlay 2D) acendia com o
> projétil ainda no ar, porque o portão antigo só olhava as anims da Bola de Fogo; o tick
> da Prisão faz `renderMap3D` no impacto para reavaliar o portão (como o da Bola de Fogo).
> Portão de feedback `_prisaoChamasFeedbackStartAt` (chama e calor a ≤1 casa) em
> `_detectHpChanges`. **(4)** o `motivo` do rótulo do dado era texto cru em português
> dentro de um `T()` (em EN saía "Prison of Flames — calor no início do turno") — virou
> 5 chaves `dado.prisao_de_chamas.<motivo>` resolvidas por `T` aninhado. Regra que fica:
> **parâmetro de `T()` que é frase também tem de ser `T`** — o `dividas.py` não vê
> literal passado como parâmetro. Testes: `tools/test_prisao_chamas.py` (14→30, seções
> [2]–[4]) e `tools/test_prisao_chamas_cliente.js` (12).

> **Senhor das Águas — 3 correções (2026-09-17):** **(1)** quem estava preso num
> redemoinho continuava preso depois que a água sumia — expirada ou cancelada por Ira/
> Chamado — e, no profundo, **afogava em chão seco** (1d6 + −1🍖/💧 por turno, sem movimento
> nem ação, até passar Reflexos 18). Raiz: `_testar_rodamoinho_inicio_turno` e
> `_testar_rodamoinho_profundo_inicio_turno` não conferiam se a criatura ainda está sobre
> uma casa de redemoinho; agora liberam quando `_rodamoinho(_profundo)_tiles_of` é vazio
> (cobre também arrasto/teleporte). Varredura `_liberar_presos_sem_rodamoinho` em
> `_expirar_terrenos_inverno` e `_cancelar_magias_terreno_exclusivas` para o estado não
> ficar "preso" até o turno da vítima. **(2)** `_senhor_das_aguas_preflight` em `handle_magia`
> (só o `terreno` era pré-validado; alcance/parede/chão cobravam o slot de 3º círculo).
> **(3)** véu `TERRENO_MAGIA_VEU_OPACIDADE`/`_COR` por casa na animação compartilhada com o
> Chamado do Inverno (3D com `depthTest`, 2D em `source-over` dentro do `lighter`), que
> desvanece com o `reveal` da frente — a água/gelo chegava no `game_state` junto do `start`.
> Só no cast; a marcação de redemoinhos não tem véu. **As 4 magias de terreno/área do
> clérigo e do mago agora seguem o mesmo molde:** preflight em `handle_magia` antes de
> cobrar; multiplicador de dano gravado na zona; véu/portão visual até a chegada. Testes:
> `tools/test_senhor_das_aguas.py` (30→51, seções [R1]–[R3]) e
> `tools/test_senhor_aguas_cliente.js` (36→43, seção [V]).

> **Chamado do Inverno — 3 correções (2026-09-17):** **(1)** `_chamado_inverno_preflight`
> em `handle_magia` (terreno, custo do permanente, alcance, parede, chão) antes de cobrar —
> o pré-check antigo só via terreno e o +20/+20; alcance/parede/chão cobravam o slot de 2º
> círculo. Com isto **as cinco magias de terreno/área** (Ira, Tempestade, Prisão, Senhor,
> Chamado) seguem o mesmo molde. **(2)** `handle_mover_prisioneiro` chama
> `_aplicar_piso_congelado_se_pisar` (era o único caminho de movimento sem o gelo; o hook já
> roda os dois de redemoinho por dentro, que estavam ali soltos). **(3)** o BFS de alcance do
> cliente e o `findPath` (`src/gameState.js`) modelam a neve: entrar na Planície Nevada
> divide pela metade o movimento RESTANTE (espelho de `_apply_snow_entry_penalty`), então cada
> nó carrega um **teto efetivo** por caminho e o "melhor por casa" passou a ser medido em
> movimento restante, não em custo gasto (um caminho que pisou a neve mais tarde tem mais
> sobra); quem começa o turno na neve (ou já tem `_snow_movement_reduced`) não divide de
> novo, porque o `moves_left` do servidor já veio reduzido. Medido: com 6 de movimento o
> servidor anda 3 casas de neve; o cliente mostrava 6 e o caminho parava no meio com erro —
> mesma classe do vento da Tempestade. Vale para neve autoral também. Testes:
> `tools/test_chamado_inverno.py` (17) e `tools/test_chamado_inverno_cliente.js` (9, extrai
> `bfsReachable`/`findPath` reais com stubs de `_walkable`).

> **Cajado Arcano nas 5 magias de terreno (2026-09-17):** o `staff` promete "+1 quadrado em
> cada dimensão" a toda magia de área, mas Ira da Rocha Ardente, Tempestade de Ciclones,
> Definhar, Senhor das Águas e Prisão de Chamas o ignoravam no servidor — e a prévia verde do
> cliente, com o cajado equipado, usava `_cajadoArcanoAreaLado` (`area_lado + 1`, cego ao
> nível) em vez do lado por nível: a lava da Ira crescia e a prévia ficava em 4x4. Agora há
> **dois helpers** no servidor: `_cajado_arcano_area_lado` (devolve o lado inteiro — Manto,
> Clarividência, Silêncio, Chamado do Inverno e as magias de `area_raio`) e
> `_cajado_arcano_area_bonus` (0/1 **aditivo** ao lado por nível/escolha — os 5 preflights de
> terreno; na Prisão soma DEPOIS de validar o 2/3/4 escolhido, que é o que o cliente envia via
> `_prisaoChamasLadoEscolhido`, nunca `mode.areaLado`). Cliente: `_areaLadoMiraMagia` (puro,
> extraído de `_iniciarModoMagia`) + `MAGIAS_AREA_CAJADO_ADITIVO` + `_cajadoArcanoAreaBonus`
> (espelho só pelo `tipo`, porque a Prisão não tem `area_lado` no catálogo). Magia de área
> nova: somar o bônus no preflight E na prévia. Testes: `tools/test_ira_rocha_ardente.py`
> [12] e `tools/test_ira_rocha_cliente.js` [6].

> **Ataque Giratório da Guilda (2026-09-21):** nova técnica universal de recarga de 6
> rodadas, custo extra de 4🍖/4💧 e preço intermediário 220 (entre os tiers de 5 e 8
> rodadas). Consome a ação principal, faz um único d20 compartilhado pelos alvos e rola
> o dano separadamente por inimigo nos quatro quadrados ortogonais adjacentes, incluindo
> footprints grandes uma única vez. Permite desarmado e armas arremessáveis sem arremessá-las;
> rejeita arcos/bestas e outros projéteis. Executor autoritativo em `server.py`, catálogo e
> traduções gerados, com regressão em `tools/test_ataque_giratorio.py`.

> **Redemoinho da Morte (2026-09-21):** evolução do Ataque Giratório, exclusiva do Guerreiro
> Anão e dependente da técnica anterior. O menu permite escolher 1 giro (4🍖/4💧, recarga 6),
> 2 giros (8🍖/8💧, recarga 8) ou 3 giros (14🍖/14💧, recarga 10); o terceiro exige a
> especialização `guerreiro_furia_3` (Fúria Berserker III). A sequência consome uma única
> ação e reavalia os inimigos adjacentes a cada giro. Preço: 350🪙, igual ao tier de 10
> rodadas. Cliente envia a quantidade escolhida em `usar_tecnica.ataques`.

> **Animação do giro (2026-09-21):** `attack_feedback` de Ataque Giratório/Redemoinho
> carrega `spin_id`, `spin_index`, `spin_count` e `ability_id`; o cliente agrupa os alvos
> pelo `spin_id` para girar o peão uma única vez por varredura. O 3D aplica 360° ao peão
> após a pose do `CombatScene`, com anel e quatro rastros radiais; o 2D gira o sprite e
> desenha cortes/anel equivalentes. Redemoinho da Morte usa aura vermelho-sangue distinta.

> **Golpe Sagrado — corte de luz no ataque 3D:** o `attack_feedback start` de um ataque
> corpo a corpo carrega `holy_strike` quando o buff está ativo. O corte inicia ao entrar
> na fase `GOLPE` da `CombatScene`, junto do avanço do peão; `impact` é fallback. O acerto mostra glifo no alvo, enquanto o erro só mostra o
> arco. O nível vai no feedback visual: nível 2 aumenta faixa/brilho em 20%, nível 3 em
> 40%, nos renderizadores 2D/3D. Após acerto no nível 3, o prenúncio visual do Raio Divino
> começa 84 ms após o início do arco e o feixe chega ao alvo em 210 ms (metade do arco),
> sem disparar magia, dano ou dado. As faixas 3D
> usam geometria dinâmica com `frustumCulled=false` e atualizam a bounding sphere; não
> deixar geometrias vazias serem renderizadas antes do golpe e depois
> mudar seus vértices sem invalidar os limites, pois o frustum pode ocultá-las no tabuleiro.

> **Cores semânticas dos dados de dano (2026-09-22):** `dice_roll.damage_type` escolhe a
> paleta em `VC.dice.damageTypeVariants` (`src/visualConfig.js`), compartilhada pela rolagem
> 2D/3D. Físico usa grafite/preto com números marfim e contorno escuro; fogo vermelho, frio
> azul, ácido verde, veneno roxo, eletricidade amarela e sagrado/luz dourado. D20 de ataque,
> cura, regeneração e dano sem um dos tipos mapeados mantêm o tema anterior; rótulos e ícones
> permanecem. Ao acrescentar rolagem de dano, enviar `damage_type` canônico no `dice_roll`;
> não inferir pelo texto localizado do rótulo. Tipos ainda sem paleta (ex.: água/som) caem na
> cor do formato do dado.

> **Sons e efeitos sonoros (2026-09-24):** 68 amostras CC0 em `assets/sfx/<grupo>/`
> (`combate`, `exploracao`, `criaturas`, `interface`, `ambiente`; origem e licença de cada
> arquivo em `assets/sfx/LICENCAS.md`) para combate físico, exploração/loot, criaturas,
> interface e ambiente; as magias seguem sintetizadas. **`src/soundBank.js`** (puro,
> `window.SoundBank`) guarda o catálogo `SFX` (`evento → {arquivos, volume, intervaloMs,
> pitchJitter, volJitter, canal}`), `familiaDe` (tipo de monstro → humanoide/fera/morto_vivo/
> reptil_inseto/grande; `null` = sem voz, ex. elementais e bonecos), `audibilidade` (fora da
> visão: 0,35, abafado, sem pan; mestre nunca abafado; `visao=null` = sem névoa, Set vazio =
> tudo na névoa), `escolherVariante`, `criarLimitador` (intervalo por evento, teto 8
> simultâneos — o novo é descartado) e `diffSons` (porta/ouro/bolsa/equipar/poção/nível/
> turno/objetivo/rugido por diferença de estado; o chamador passa `prev=null` a cada
> masmorra nova; largar poção no chão toca "beber" — falso positivo aceito). No `game.js`,
> **`sfx(evento, {pos})`** devolve `true` quando tratou o som e `false` quando não há
> amostra pronta — aí o chamador toca a síntese antiga (`_playCombatCue`,
> `_playDefeatSound`): nada fica mudo. Variante não carregada cai numa irmã já pronta. O pan
> é pela projeção na câmera (a câmera orbita). Ganchos: golpe/erro/escudo/dor no `impact`
> da `CombatScene` (e no `result` sem cena), dor também no dano físico sem cena
> (`_detectHpChanges`), morte em `_somMorteMonstro`, estado em `_capturarSonsDeEstado`
> (dentro de try/catch — som nunca pode derrubar a atualização de estado), clique delegado
> em botões, recusa no `serverError`. Ambiente: `_ambienciaGarantir(state)` (idempotente, a
> cada `game_state`, só com `#screen-game` ativo) toca o loop do preset `ambiente`;
> `_ambienciaParar` em `cityState`, `showScreen` fora da masmorra, `handleGameOver` e
> `reconnectFailed`. Servidor: só o campo opcional **`impacto`** (`cortante|perfurante|
> contundente|natural`) no `attack_feedback start`, por `_impacto_de` ao lado de
> `_projetil_de` (herói pela `categoria` da arma, desarmado/sem categoria → `contundente`;
> monstro: nome natural > categoria > nome da arma > `contundente`), inclusive no Ataque
> Giratório. **Ausência do campo = "não é golpe físico"** (só ataque elemental de monstro e
> item arremessado): o cliente então não toca golpe nem *whoosh* e deixa a síntese do
> elemento. Golpe que mata não toca dor (a morte toca no lugar); falha de rede no carregar
> tem 1 nova tentativa (404 não). **`GS.on`
> substitui o ouvinte anterior** — havia dois `GS.on('serverError')` e o primeiro (limpar a
> prévia do Ataque Giratório) nunca rodava; foram fundidos, e `tools/test_sons_cliente.js`
> [10] proíbe `GS.on` duplicado. Trocar um som = trocar o arquivo; volume = número no
> catálogo; preparar um arquivo novo: `python tools/preparar_sfx.py <origem> <destino>`
> (`--loop`, `--ss/--to`, `--pitch`). Provado em partida (sala de teste do editor):
> ambiente, golpe, erro, crítico, dor, morte, clique e recusa tocam uma vez cada; 68
> arquivos decodificam sem erro. Testes: `tools/test_sound_bank.js`,
> `tools/test_sons_cliente.js`, `tools/test_sons_impacto.py`, `tools/test_sfx_arquivos.js`.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-09-23-sons-efeitos-sonoros*`.
> **Passos dos peões:** o som sintetizado `tocarSomPasso` ganhou canal próprio (`_stepsBus`,
> slider "👣 Movimento dos peões" no painel ⚙️, salvo como `steps` em `lfh_audio`) e ganho de
> saída ×6 **depois** do compressor (medido: o pico era 0,05, abaixo do clique, e sumia sob o
> ambiente). Soa para todos os peões: o seu no 3D pela animação (`_animarPasso`); monstros e
> servos auto-comandados no pouso de cada `entity_step` (`_onEntityStep`, exceto `kind:'player'`);
> os outros heróis — que no movimento comum não recebem `entity_step`, só mudam de casa entre
> dois `game_state` — por diff de posição (`_sonsPassosDeEstado`, um passo por casa, espaçado
> em `DURACAO_PASSO_MS`; salto >4 casas = teleporte, sem som; o seu peão entra aqui só no 2D; a
> mesa de teste do editor fica de fora). Passo em casa fora da sua visão não soa
> (`_somPassoEm`). Teste: `tools/test_sons_cliente.js` [11].
> **Passo em água/pântano:** casa de chegada com `materiais` em `agua`/`agua_profunda`/
> `rodamoinho`/`rodamoinho_profundo`/`pantano` (e sem ponte — `baseSuperficiePonte3D`) toca
> `passo_agua` (3 versões em `exploracao/passo_agua_*`: passo molhado + borbulha curta) em vez da
> batida sintetizada. O evento é do canal **`passos`** — o `sfx()` só toca `efeitos`, então quem
> toca é o próprio `tocarSomPasso` (`_passoMolhadoEm` + `_tocarPassoAgua`, direto no `_stepsBus`,
> slider "Movimento dos peões"); sem amostra pronta, cai na batida. O seu peão no 3D passa a
> casa por `opts.casa` (sem pan, como antes); os demais já passavam `pos`. Pico medido 0,37 contra
> 0,28–0,36 do passo seco. Teste: `tools/test_sons_cliente.js` [22].
> **Morte Explosiva do Elemental de Fogo invocado:** `_executar_conjurar_elemental` copia a
> ficha do Bestiário para o servo. Em `_animado_morre`, a passiva `morte_explosiva` usa
> `_morte_explosiva` (4d6, raio 1, Reflexos CD 13 e chamas persistentes conforme a ficha),
> igual à morte do monstro. O servidor emite `explosion_area`; o cliente destaca a área, toca
> `sfx('explosao')` no centro e inicia a animação 2D/3D da Mina Terrestre. O legado
> `especial: explosao_6d6` continua no caminho antigo.
> **Voz dos elementais:** os 6 elementais (`elemental_fogo|ar|agua|pedra|eletrico|gelo`) têm
> família própria `elem_<elemento>` (`FAMILIAS_ELEMENTO` em `src/soundBank.js`; `familiaDe`
> casa `^elemental_<x>$` ANTES das regras — os demais `elemental_*`, como o Descontrolado,
> seguem sem voz). Cada família tem `rugido_`/`dor_`/`morte_` (2 versões, 36 arquivos em
> `assets/sfx/criaturas/*_elem_*`): labareda, ventania, correnteza, desmoronamento,
> faíscas/trovão e gelo rachando. A dor de elemental vale para **qualquer** tipo de dano (a
> magia que o acerta também soa nele), via `_familiaElementalDaChave` em `_somDor`; os outros
> monstros seguem com dor só no dano físico. `tools/preparar_sfx.py` ganhou `--fade=S` (rampa
> de entrada/saída para trechos cortados de som contínuo).
> **Correções achadas na mesa do editor (2026-09-24):** (1) a dor do elemental toca
> `ATRASO_DOR_ELEMENTAL_MS` (90 ms) depois do golpe — no mesmo instante a batida e o crítico a
> encobriam; decide-se na hora por `_sfxPronto` (amostra decodificada?) para o recuo continuar
> funcionando. (2) Golpe de elemental soa o próprio elemento: `ataque_elem_<x>` (mesmos arquivos
> da aparição) no `impact` da cena e no `result` sem cena, por `_somAtaqueElemental`; o elemental
> não tem `impacto` físico, então antes só soava o genérico. (3) **Rugido na primeira ação**
> (`_somRugidoAoAgir`, no `start` do `attack_feedback`): o rugido "ao entrar na visão" nunca
> dispara para quem já estava à vista no 1º estado (linha de base) — a mesa de teste e a visão
> total do mestre começam assim; conjunto `_rugiram` (zerado em `_sonsReset`, alimentado pelo `id`
> que o `diffSons` passou a mandar no rugido) garante 1 rugido por monstro; elemental não ruge ao
> agir. (4) `_familiaElementalDaChave` reconhece também o elemental **invocado** (`a:<id>`, servo
> com `tipo:'elemental'` + `tipo_elemental`). (5) O raio do Elemental Elétrico em linha
> (`spell_animation` `elemental_raio`) toca `relampago` (estalo de trovão) ao sair.
> **Vozes das criaturas ampliadas (2026-09-24):** cada família (`humanoide`, `fera`,
> `morto_vivo`, `reptil_inseto`, `grande`) tem 4 aparições, 3 mortes e — novo — **3 gemidos de
> dano próprios** (`dor_<família>`; antes todo monstro gemia com o mesmo `dor_criatura`). A fera
> usa os rosnados guturais do RPG Sound Pack (`NPC/gutteral beast`), o morto-vivo os lamentos das
> sombras (`NPC/shade`), o grande ogro/gigante, o inseto chiados/estalos, o humanoide gemidos
> humanos. `_somDor` resolve a família por `_familiaDaChave` e toca 90 ms depois do golpe (mesmo
> motivo do elemental: no mesmo instante era encoberto); sem família (boneco) ou sem amostra,
> `dor_criatura`. Teste: `tools/test_sons_cliente.js` [20].
> **Subir de nível e objetivo — fanfarras (2026-09-24):** as vinhetas antigas (Kenney Music
> Jingles PIZZI07/PIZZI03) terminavam em acorde **menor** e a de nível ainda descia 3,5 st —
> soavam como falha. Trocadas por fanfarras CC0 medidas (contorno melódico + acorde final por
> cromagrama): `nivel_1` = abertura da *Victory Fanfare Short* (cynicmusic; sobe 19 st, termina
> no topo em Mi maior, 2,2 s); `objetivo_1` = trecho da *Just a random fanfare* (Spring Spring;
> metais e pratos, sobe 24 st, Dó maior, 2,9 s). **Critério para som de "vitória":** ascendente
> e acorde final maior — conferir antes de trocar, sem depender de ouvir.
> **Manto da Escuridão — nuvem de sombras (2026-09-24):** irmã da nuvem da bomba de fumaça,
> em tom enegrecido, para TODA zona `escuridao` que não seja fumaça (`_ehZonaSombra`): o Manto
> do herói e o do monstro (Bugbear das Sombras, que antes só tinha o véu por casa). Substituiu a
> animação antiga do Manto (anéis roxo/ciano, faíscas, halo — removida) e o véu roxo por casa
> dessas zonas; o som grave do Manto ficou (`_tocarSomMantoEscuridao`, ligado ao nascimento e à
> dissipação da nuvem). `_sombrasSync` distribui os novelos pelas casas REAIS da zona
> (`_sombraCasasRelativas`, mesmas `_addQuadrado`/`_addCheb` do realce — com Cajado Arcano o
> lado 8 usa a âncora assimétrica), nasce em onda do centro para fora (só se criada nesta rodada;
> `visual_id manto_escuridao_<c>_<rodada>_<x>_<y>` ou id `escuridao_<m>_<rodada>`), acompanha o
> conjurador deslizando (`_sombraCentro`; salto > 3 casas encaixa) e alguns novelos são fios que
> sobem. 3D: sprites com a textura da fumaça, `toneMapped:false` (o ACES acinzentava o preto).
> 2D: o piso é escuro (luminância ~30/255, medido), então preto não se lê — cada novelo tem uma
> orla violeta-acinzentada (contorno) e um miolo escuro com teto baixo (o peão fica meio
> encoberto). Teste: `tools/test_manto_sombras_cliente.js`.
> **Incendiários (Fogo Grego, Frasco de Óleo, Bomba Incendiária):** evento `incendio` (3 versões
> em `combate/incendio_*`: estouro curto e grave + "vuuush" de ignição + labaredas crepitando que
> somem em ~1,6 s; montado de explosões da Kenney Sci-Fi + `air_02` + `fire-1`). O mapa
> `SOM_IMPACTO_ITEM` (game.js, `item_id → evento`) substituiu o conjunto das granadas; área soa
> sempre, acerto em alvo (óleo, fogo grego) só no **acerto** (`c.area || c.hit` no impact;
> `f.area || msg.hit` no `result` sem cena, que agora guarda `itemId` — antes a granada ficava
> muda no 2D). O arremesso de monstro com item de alvo também manda `item_impacto` com `hit`.
> **Bomba de fumaça — nuvem (2026-09-24):** a zona continua sendo a `escuridao` de sempre
> (mecânica intocada); o servidor só passa `visual_id="fumaca_<quem>_<rodada>_<cx>_<cy>"` nos dois
> arremessos (`_throw_item_area` do herói e `_monster_throw_item` do Soldado). No cliente,
> `_ehZonaFumaca` tira essas zonas da névoa roxa do Manto e `_fumacaSync` (no topo do
> `renderMap`, 2D e 3D) mantém `_fumacaNuvens`: nasce na chegada do frasco
> (`CombatScene.areaImpactAt`) com anel rente ao chão + 16 novelos (sprites com textura de canvas)
> que incham, toca `fumaca_puff` e `fumaca_chiado` (+120 ms), fica viva enquanto a zona existir,
> afina na última rodada (`duracao <= 1`) e se desfaz para cima em 1,6 s quando a zona some.
> Zona já ativa no 1º estado ou de rodada anterior (entrar/reconectar) nasce pronta e muda
> (`_fumacaBaseline` + rodada do `visual_id`). 3D em `_updateFumaca3D` (laço do `startLoop3D`);
> 2D em `_fumacaDraw2D` (disco com borda esfumaçada, máx. ~65% no miolo), com tick a ~8 quadros/s
> quando parada. Opacidade calibrada **medindo** o render (a 1ª versão só escurecia o piso claro
> em 13 níveis). Nota: no 2D, monstro dentro de zona de escuridão já não era desenhado (regra
> antiga, vale também para o Manto); no 3D ele aparece meio encoberto pela nuvem. Testes:
> `tools/test_sons_cliente.js` [19], `tools/test_som_armadilha.py` [6].
> **Armadilhas de gás:** reutilizam a textura volumétrica da bomba em paleta verde-amarelada.
> `nuvem_gas` nasce pelo aviso público `armadilha_disparo`, cobre apenas pisos visíveis no
> raio afetado e se dissipa; `camara_gas` nasce/some sincronizada à zona autoritativa e
> distribui os novelos pelas casas de piso/porta da sala (`room_id`). A fumaça é visual;
> saves, dano e duração continuam autoritativos no servidor. A névoa verde plana antiga da
> Câmara foi removida para não competir com a fumaça.
> **Choque da aura (Dano de Retaliação):** `_dano_retaliacao` manda no `dice_roll` também
> `retaliacao_tipo` (tipo da criatura que retaliou) e `retaliacao_pos` (casa de quem levou o
> choque). No cliente, `_somRetaliacao` (no `GS.on('diceRoll')`) toca `ataque_elem_<x>` quando
> quem retaliou é elemental — faísca do Elétrico, labareda do de Fogo; outras criaturas seguem
> com o som de dano. **Tempo:** o dado chega quando o servidor resolve o ataque, 1–3 s antes do
> golpe aparecer (a cena espera o d20); por isso o choque espera a dor do elemental
> (`_retaliacaoAposDor`, chamado de `_somDor`) e soa 120 ms depois dela; se a dor tocou há
> <600 ms (sem cena), sai já; se nada vier, rede de segurança em 3,5 s. Testes:
> `tools/test_som_armadilha.py` [5], `tools/test_sons_cliente.js` [18].
> **Teste de som** (⚙️ → Áudio → "🎧 Teste de som", `abrirSoundTest`): overlay `#som-teste`
> que lista TODO o `SoundBank.SFX`, agrupado pela pasta do 1º arquivo (combate/exploracao/
> criaturas/interface/ambiente), com um ▶ por versão (tooltip = caminho do arquivo) + os sons
> gerados (`_SOMTESTE_SINTETIZADOS`: passo, arpejo do baú, armadilha). Toca direto no canal do
> evento, sem limitador/névoa/sorteio, um por vez (`_somTesteAtual`, botão Parar; fechar para).
> Nomes: `ui.somteste.ev.<evento>` ou, para criatura, `ui.somteste.acao.<rugido|ataque|dor|morte>`
> + `ui.somteste.familia.<família>`. **Evento novo no catálogo precisa de nome** — o
> `test_sons_cliente.js` [17] cobra pt/en de todo nome que o painel pede. O clique delegado de
> botões ignora `#som-teste` (senão o clique se misturaria ao som ouvido).
> **Armadilha de prova:** com o painel do navegador oculto o `requestAnimationFrame` não roda e
> a CombatScene nunca chega ao `impact` — nenhum som de golpe sai. Troque o rAF por
> `setTimeout` antes de medir.
> **Baú velho:** `openChestWindow` toca `bau_abre` (3 versões em `exploracao/bau_abre_*`: dobradiça
> rangendo em tom grave + tampa de madeira batendo, montadas de rangidos da Kenney com batidas de
> madeira) e só cai no arpejo sintetizado `tocarSomBau` sem amostra pronta.
> **Corrosão por ácido:** evento `acido` (3 versões em `combate/acido_*`: respingo viscoso +
> borbulha + chiado de fritura — o crepitar do `fire-1` em passa-alta 2,2 kHz — que some em
> ~1,5 s). Toca em três pontos: (1) **Frasco de Ácido / Vidro de Ácido Grande** no acerto, pelo
> `SOM_IMPACTO_ITEM`; (2) **cuspe do Grotão** no impacto da animação (`_tocarSomCuspeAcidoImpacto(anim)`,
> na casa atingida; o baque sintetizado ficou de recuo); (3) **equipamento de herói corroído**
> (Devorador, cuspe, Maldição da Ferrugem) — sem mensagem pública (o `equipment_damage_result` é
> privado), então vem do estado: `_sonsCorrosaoDeEstado` soma os `*_lvl` de `player.corrosao` e
> toca quando sobe. Como o `game_state` chega antes do golpe aparecer, o chiado espera a dor do
> herói (`_corrosaoAposDor`, chamado em `_somDor`) se `CombatScene.awaitingHit(chave)` diz que há
> golpe ainda não desferido (rede de segurança 3,5 s); sem golpe pendente toca já; com cuspe em voo
> no herói não repete. A **armadilha Jato de Ácido** (`jato_acido`) toca `acido` no disparo
> (`SOM_DISPARO_ARMADILHA`) e marca os atingidos em `_acidoArmadilhaAte` (4 s), para a corrosão
> que ela causa não repetir o chiado. Testes: `tools/test_sons_cliente.js` [21], `tools/test_combat_scene.js` [12].
> **Chamas vivas no peão (status `em_chamas_rodadas`):** o 🔥 parado sobre a cabeça virou fogo
> animado no corpo. 3D: `_makeChamasFx3D(raio)` (7 labaredas-sprite com textura de gota de fogo
> + 7 brasas subindo, texturas compartilhadas não `_owned`) em `build3DFig` e em
> `_buildOrientedCreature3D`; `_updateChamasFx3D` (laço do `startLoop3D`) tremula, sobe as brasas e
> **puxa o anel para o lado da câmera** (no espaço local do grupo, 1,4× o raio) — sem isso o próprio
> modelo escondia ~60% do fogo; solta do registro a figura fora da cena há >1 s. Medido na mesa de
> teste: mistura **aditiva** sumia sobre piso claro (fogo + branco = branco) e o **tone mapping**
> ACES (exposição 1,55) desbotava o laranja — por isso mistura normal e `toneMapped:false`. 2D:
> `_desenharChamasPeao2D` (3 labaredas + brasas aos pés), que agenda um redesenho a ~12 quadros/s
> (`_agendarChamas2D`) enquanto houver alguém em chamas à vista. O ícone 🔥 da fileira de status
> 2D continua. Teste: `tools/test_chamas_peao.js`.
> **Todo fogo contínuo acende o peão (2026-09-26):** as chamas vivas passaram a seguir o campo
> `queimando` do `game_state` (herói e monstro), calculado no servidor por `_queimando(ent)` —
> SÓ LEITURA, com a mesma regra de quem sofre o dano: status em chamas, fogo progressivo da
> Armadilha Incendiária (`efeitos_ativos` da armadilha), lava sob os pés (`_lava_tiles_of`),
> parede da Prisão de Chamas (`_prisao_chamas_relacao == "chamas"`; o calor ao lado não conta),
> chamas residuais da Bola de Fogo (no chão) e do Molochus. A fogueira fica de fora (só queima ao
> pisar). Cliente: helper `_queimando(x)` (recua para `em_chamas_rodadas` se o campo faltar) no 2D
> e nas 6 linhas do 3D (assinatura, chave e argumento do `build3DFig`); o ícone 🔥, o banner "EM
> CHAMAS" e o botão "Apagar chamas" seguem no STATUS, que é o que se apaga. **Bug corrigido junto:**
> o arremesso de ÁREA do monstro (Bomba Incendiária do Soldado) só dava o dano da explosão e nunca
> aplicava o status em chamas — o do herói aplicava. Teste: `tools/test_queimando.py`.
> **Armadilhas — gemido de quem foi atingido (2026-09-24):** `_somDisparoArmadilha` marca cada
> chave de `alvos` em `_dorArmadilha` (validade 4 s); quando a vida dela cai, `_somDor` consulta
> `_somDorArmadilha` ANTES do filtro de dano físico e toca o gemido do atingido (`dor_heroi`,
> `dor_<família>`, elemental, ou `dor_criatura`) depois do som do disparo, para **qualquer** tipo
> de dano (fogo/ácido caíam no som gerado). O popup "atingido" não toca mais o aviso dissonante
> `tocarSomArmadilha`. Som do disparo em `SOM_DISPARO_ARMADILHA`: mina → `explosao` (volume 1,75 — o mesmo das granadas; `incendio` 1,6; picos medidos 0,79–0,94, logo abaixo do corte;
> antes 1,3/0,63), incendiária → `incendio`, lâmina escondida/guilhotina → `armadilha_lamina`
> (= `golpe_cortante_1`). Testes: `tools/test_sons_cliente.js` [13], `tools/test_som_armadilha.py` [8].
> **Explosão da mina:** `GS.on('armadilhaDisparo')` → `_somDisparoArmadilha` toca `explosao`
> (3 versões em `combate/explosao_*`, baque grave + estrondo da Kenney Sci-Fi Sounds) na casa da
> mina, 240 ms depois (impacto da animação de armadilha), para toda a sala — inclusive quando
> quem pisa é monstro e mesmo que o herói passe no save. Mapa `SOM_DISPARO_ARMADILHA` (só
> `mina_terrestre` hoje). Testes: `tools/test_som_armadilha.py`, `tools/test_sons_cliente.js` [13].
> **Explosão das granadas** (`granada`, `granada_superior` — `ITENS_EXPLOSIVOS`): o mesmo `explosao`,
> por `_somExplosaoItem`. Arremesso do herói: no comando `impact` não-tardio da CombatScene, que
> passou a carregar `item_id` (toca quando o frasco chega à casa). Arremesso do Soldado: pela
> mensagem `item_impacto`, na hora. Testes: `tools/test_som_armadilha.py` [3]/[4],
> `tools/test_sons_cliente.js` [14].

> **Perseguição dos monstros (2026-09-26):** a memória que já existia (`ai_last_seen`,
> `_monster_remember_visible_targets`, `_monster_register_attack_alert`,
> `_monster_search_last_seen`: ver o herói ou ser atacado → busca a última posição por 3
> rodadas, alerta compartilhado com a sala de origem) ganhou dois acréscimos. **Todo dano
> alerta:** o `handler` tira uma foto do HP dos monstros (`_hp_monstros`) antes de cada mensagem
> de herói na masmorra e chama `_alertar_monstros_feridos` depois — magia, arremesso,
> instrumento e técnica passam a gravar a origem do ataque sem gancho por executor. Ficam de
> fora (`_MENSAGENS_SEM_ALERTA_DE_DANO`) o `end_turn`, porque o turno dos monstros roda dentro
> dele, e o controle de servos, que já grava a posição do servo. **Rastro:** ao chegar à última
> posição sem ver o herói, `_monster_tentar_rastro` testa `d20 + distância÷2 ≤ Percepção` da
> ficha; no sucesso a pista vira a posição atual do herói (sem renovar o prazo), uma vez por
> chegada, por monstro. Invisível não deixa rastro, salvo Faro Implacável. **"!" vermelho:**
> cada monstro do `game_state` traz `procurando` (`_monstro_procurando`, SÓ LEITURA: pista
> válida há ≤3 rodadas e nenhum alvo à vista — liga logo após um ataque de longe, desliga ao
> ver o herói ou esquecer). Cliente: `_drawProcurandoBadge2D` (acima do nome) e
> `_makeProcurandoSprite3D`/`_syncProcurandoMark3D`/`_atualizarProcurandoMarks3D`, espelhando a
> marca 😠 da Provocação; com os dois ativos o "!" vai para o lado. O campo entra na assinatura
> de entidades do 3D, senão o sprite não troca. Teste: `tools/test_perseguicao.py`. Spec/plano em
> `docs/superpowers/{specs,plans}/2026-09-26-perseguicao-monstros*`.

> **Tempestade de Ciclones — posicionamento por levas (2026-09-27):** o clérigo pode
> confirmar de 1 até o número de ciclones restantes em cada seleção. A primeira leva
> ativa a tempestade e inicia duração/descargas; `ciclones_pendentes` conserva a cota
> restante para os próximos turnos, acessível no painel de ações e na aba Magias. Cada
> leva soma ciclones à zona, preserva os IDs já colocados e rejeita footprints ocupados.
> A tempestade parcialmente posicionada continua ativa, pode ser movida/encerrada e
> expira normalmente; a prévia sem nenhuma colocação ainda exige uma leva inicial.

> **Tempestade de Ciclones — criaturas grandes (2026-09-27):**
> `_tempestade_aplicar_ciclone` resolve cada ciclone que cruza qualquer casa do footprint
> do alvo, com um teste de Reflexos e dano por ciclone a cada rodada. Perda de movimento
> e de ação permanece agregada; uma falha preserva a perda de ação mesmo se outro ciclone
> for evitado na mesma rodada.

> **Ferrão dos Charcos — pântano (2026-09-27):** Jovem, Adulto e Ancião carregam
> `ignora_pantano` na passiva `movimento_aquatico`. O servidor consulta a exceção ao
> montar movimento no início do turno e ao entrar no pântano; `src/gameState.js` também
> a espelha no alcance/caminho previsto. Água e água profunda continuam usando a regra
> existente de movimento aquático. Catálogo do editor sincronizado em
> `tools/editor_catalog.js`.

> **Crocodilo Jovem — deslocamento aquático (2026-09-27):** habilidade passiva
> `movimento_agua_sem_penalidade` marca `ignora_penalidade_agua`; servidor e previsão
> do cliente cobram custo normal em Água e Água Profunda. O ID não ativa a imunidade
> separada a redemoinhos (`_ignora_rodamoinho`).

> **Jacaré (ND 2):** ficha nativa em `MONSTER_DEFS` reutiliza a IA específica
> `crocodilo_jovem` para perseguição, agarrão, mandíbula automática e arrasto; seu
> dano automático vem de `special_abilities[].damage`. `image: "jacare"` seleciona
> `assets/pawns/monstros/jacare/jacare.png` em 2D e
> `assets/models3d/monstros/jacare.glb` em 3D. Catálogo sincronizado com
> `python tools/export_catalog.py`.

> **Veneno Ensaio sobre a Cegueira — alvos monstros (2026-09-27):** cegueira parcial
> e total agora afetam a percepção e o raio de visão dos monstros através dos mesmos
> campos de efeito usados para heróis; a IA também recusa ataques marcados à distância
> enquanto estiver cega. A cegueira reaplicada após falha no reteste de Fortitude começa
> a contar no próximo turno do alvo, sem perder uma rodada no mesmo processamento.

> **Editor em inglês — Fase 0 (infraestrutura, 2026-09-28):** o editor (`tools/editor.html`)
> carrega o motor de idioma do jogo (`src/lang/*.js` + `src/i18n.js`) e a cola
> **`tools/editor_i18n.js`**: `t()` global, `nomeCat(família, id, padrão)` (nome de catálogo
> pelo id; sem chave → nome do autor), `data-i18n`/`-title`/`-ph` na moldura, idioma em
> `localStorage["lfh_lang"]` (a MESMA chave do jogo — só compartilha se o editor for aberto pelo
> servidor, não por `file://`) e `trocarIdioma`, que reaplica a moldura e chama
> `setTab(window._abaAtualEditor, true)`. O 2º argumento (`soRedesenhar`) faz a aba Cenas
> redesenhar sem recarregar do servidor e chama o `sincronizar()` dos editores de Criaturas e
> Itens antes do `render()` — eles guardam texto digitado só no DOM até salvar, e o redesenho o
> apagaria. **Aba nova com formulário que só lê os campos ao salvar precisa de um
> `sincronizar()` do mesmo jeito.** Seletor 🌐 `#ed-lang` na barra. Dicionário à mão
> **`src/lang/editor.js`** (`ui.editor.<aba>.<slug>`; moldura em `ui.editor.topo.*`). Rótulo
> com campo dentro leva o texto num `<span data-i18n>` (há checagem de `data-i18n` com filhos).
> Texto que o código troca em runtime também usa `t()` (o botão "Testar como Mestre").
> **Placar:** `tools/test_editor_idioma.py` ([4] por arquivo/função, `FECHADAS` cobradas —
> hoje 1.204 textos; [5] `t` local que sombreia o global — renomeie antes de migrar o arquivo).
> Cola testada em `tools/test_editor_i18n.js`. Próximas fases, uma aba por vez: Masmorra (a
> barra de ferramentas é montada uma vez por `buildToolbar()` e precisa ser remontada na troca)
> → Criaturas → Itens → Cidade → pequenas; por último as mensagens do servidor ao editor.
> Spec/plano em `docs/superpowers/{specs,plans}/2026-09-28-editor-em-ingles*`.

> **Editor em inglês — Fase 1 (aba Masmorra, 2026-09-28):** `tools/editor.js` fechado no placar
> (`FECHADAS = {"editor.js"}` em `tools/test_editor_idioma.py`; 304 textos → 0). Chaves em
> `src/lang/editor.js` sob `ui.editor.masmorra.<área>.<slug>` (`barra`, `painel`, `valid`,
> `armadilha`, `design`, `salvar`, `status`…) + `ui.editor.material.*` e `ui.editor.masmorra.direcao.*`.
> **Estruturas de módulo guardam id, não texto:** `TOOLS` (grupos `tiles`/`entidades`/`acoes`),
> `LOOT_ITEM_GROUPS` (o agrupamento de `lootItemCategory` decidia por texto em português — agora
> por id, com `semAcento`), `HERO_SPAWN_META`, `LICAO_VERBOS` (só `{v}`), `CURSE_CATEGORIES` e o
> rótulo de visão (`visaoRotulo`) resolvem o texto na hora de desenhar. Nome de catálogo por
> `nomeCat(família, id, padrão)` (armadilhas, itens de loot/recompensa, venenos, classes);
> descrição por `descCat` (novo, em `editor.js`); material por `nomeMaterial`. A barra é montada
> uma vez, então `setTab(tab, true)` chama `buildToolbar()` antes do redesenho. 50 `t` locais que
> sombreavam o tradutor foram renomeados. **Fica em português de propósito:** conteúdo autoral
> (nomes de sala, textos de fala, itens/monstros do editor) e os nomes de catálogo que não têm
> chave nenhuma no dicionário do jogo (ex.: armas colossais, Armadura Rúnica, Grotão) — lacuna do
> `gerar_vocabulario.py`, não do editor. Conferido no navegador em inglês: 136 painéis de
> entidade sem erro; trocar o idioma preserva a seleção e o texto digitado. Plano em
> `docs/superpowers/plans/2026-09-28-editor-em-ingles-fase1-masmorra.md`.

> **Visão compartilhada entre heróis (2026-09-30):** opção para cada jogador ver também o que os
> outros heróis do grupo enxergam. **Duas chaves:** o anfitrião **permite** (campo da sala
> `visao_compartilhada_permitida`, padrão `True`, mensagem `set_visao_compartilhada {enabled}` só
> do anfitrião — molde do limite de tempo por turno; salvo no jogo salvo e enviado no `game_state`
> e no `city_state`) e cada jogador **liga** a sua no painel ⚙️ → **Configurações de jogo** (caixa "👁️ Visão compartilhada",
> seção expansível que também contém o limite de tempo por turno e `Atravessar aliados` (opção da sala, só o anfitrião altera); preferência pessoal em
> `localStorage["lfh_visao_compartilhada"]`, padrão desligada; botão do anfitrião logo abaixo,
> `_refreshVisaoCompartilhadaOption`, chamada onde o limite de tempo já se atualiza). **Cálculo num
> ponto só:** `computeVisionSet` (`game.js`) soma, com o raio e a linha de visão de cada um, os
> heróis de `GS.heroisVisaoCompartilhada(state, myPid, ativa)` (puro): vivos, dentro da masmorra,
> fora o próprio; nada se o **seu** herói estiver cego. `_sombraObjetos` tira da penumbra as casas
> que um aliado vê. **Só a visão muda:** atacar/mirar seguem exigindo a linha de visão do seu
> herói (servidor); monstro escondido segue escondido. Servos e elemental **já** compartilhavam
> visão com todos (`_live_reveal_tiles`, raio 2, campo `revealed`) e seguem assim; o **prisioneiro
> resgatado** passou a entrar nessa mesma soma. Provado no navegador com dois jogadores (54 → 109
> casas visíveis para a Ana com a Bia a 29 casas). Testes: `tools/test_visao_compartilhada.py` (14)
> e `tools/test_visao_compartilhada_cliente.js` (15, roda o `computeVisionSet` real). Spec em
> `docs/superpowers/specs/2026-09-30-visao-compartilhada-design.md`.

> **Voar por cima depende do porte (2026-09-30):** a altura mínima para passar (e parar) por
> cima de algo deixou de ser fixa em 2 quadrados e passou a seguir o **porte de quem está
> embaixo** — `ALTURA_SOBREPOR_POR_PORTE`/`altura_para_sobrepor(porte)` (server.py, ao lado das
> constantes de altura; 2 pontos = 1 quadrado): minúsculo/pequeno/médio **1 quadrado**, grande
> **2**, enorme **3**; herói e porte ausente contam como médio. O campo `porte` é o MESMO que já
> escalava a miniatura (Editor de Criaturas). A diferença é medida contra a altura de quem está
> embaixo (se também voa), nos dois sentidos, em `_pode_compartilhar_casa_voando`. **Servos
> animados** deixaram de bloquear sempre (`_animado_em(..., actor=)`). **Objetos:** sem campo
> novo — objeto **baixo** conta como médio e **alto** como grande (`_voo_sobre_objeto`, lendo
> `_decor_tall_tiles`); vale em `handle_move` e `_monster_can_occupy` mesmo sem "ignora
> obstáculos em voo", que continua sendo a única forma de atravessar parede, porta e escombros.
> **Descer** sobre algo que deixaria de ser sobrevoado é recusado em `handle_alterar_altura`
> (`_pode_descer_ate`/`_sobreposicao_valida`, erro `erro.algo_embaixo_impede_descer`) — antes era
> possível pousar dentro de outra criatura. Cliente (`src/gameState.js`) espelha a tabela
> (`alturaParaSobrepor`, `_vooSobreObjeto`) nas casas azuis e no caminho; de quebra o
> `bfsReachable` passou a mandar o ator a `_occupiedSet` — sem isso as casas azuis nunca
> mostravam o caminho por cima de criaturas, embora o `findPath` aceitasse. Testes:
> `tools/test_voo_por_cima.py` (43) e `tools/test_voo_por_cima_cliente.js` (44), com a mesma
> tabela de casos; `test_voo_altura` atualizado para a regra nova.

> **Atravessar aliados (2026-09-30):** opção da sala que **só o anfitrião** liga (painel ⚙️,
> botão "🚶 Atravessar aliados", `_refreshAtravessarOption` chamada junto da visão
> compartilhada; campo `atravessar_aliados`, padrão desligado, no `game_state`/`city_state` e no
> jogo salvo; mensagem `set_atravessar_aliados`). Ligada, um **caminho** — `move_path` do herói e
> as novas `mover_animado_caminho`/`mover_prisioneiro_caminho` — pode cruzar a casa de herói,
> servo animado/elemental ou prisioneiro liberto, mas **nunca terminar** nela:
> `_destino_livre_ou_avisa` confere a última casa antes de andar (`erro.o_destino_esta_ocupado`),
> cada passo vai pelo handler de 1 casa com `_atravessar=True`, e um caminho interrompido em cima
> de alguém (armadilha, movimento acabou, queda) volta à última casa livre (`_recuar_para`, com
> `entity_step`). Passo isolado (setas) para dentro de aliado segue recusado. O "comandar" dos
> servos (passo a passo, guloso) só entra em casa de aliado com mais de 1 de movimento e recua se
> terminar em cima. Ocupante do grupo = `_ocupante_do_grupo_em` (respeita o sobrevoo por porte).
> Monstros — inclusive sob Comando/Dominar — e o prisioneiro **ainda preso** bloqueiam sempre.
> **Correção junto:** o prisioneiro passou a ocupar a casa também para os heróis (antes um herói
> podia parar em cima dele) e para a colocação de servos (`_tile_livre_para_animado`). Cliente:
> `_occupiedSet` põe as casas de aliado em `occ.aliados` com a opção ligada — `_walkable` as
> cruza, `bfsReachable` não as pinta de azul e `findPath` nunca termina nelas (nem no parcial);
> os cliques de servo/prisioneiro mandam o caminho inteiro (`GS.moverAnimadoCaminho`/
> `moverPrisioneiroCaminho`). Provado no navegador com duas jogadoras: desligada, o caminho da Bia
> contorna a Ana (4 passos); ligada, passa por ela (2 passos) e terminar em cima é recusado.
> Testes: `tools/test_atravessar_aliados.py` (28) e `tools/test_atravessar_aliados_cliente.js`
> (29). Spec em `docs/superpowers/specs/2026-09-30-atravessar-aliados-design.md`.

> **Animação da armadilha de teletransporte (2026-09-30):** `server.py` emite
> `armadilha_teleporte` com origem, alvo e resultado efetivo (resistiu/saída bloqueada ou
> teleportado e destino); `src/gameState.js` encaminha como `armadilhaTeleporte`. No cliente,
> `_receberDisparoTeletransporte` inicia o glifo na origem a partir de `armadilhaDisparo` e
> `_receberResultadoTeletransporteArmadilha` resolve o efeito: falha/resistência desfaz o glifo;
> sucesso desenha recomposição arcana e partículas no destino. Em 2D e 3D, o caminho entre as
> casas só aparece quando ambas são visíveis para aquele cliente; origem e destino são filtrados
> separadamente pela visão atual. Regras de save, saída e movimento permanecem no servidor.
> O sucesso agenda `sfx('teleporte')` para acompanhar a chegada; resistência e saída bloqueada
> ficam sem efeito sonoro de teletransporte. A amostra original `assets/sfx/combate/teleporte.ogg`
> foi criada por síntese procedural e está registrada em `assets/sfx/LICENCAS.md`.

> **Animação da Armadilha de Maldição:** `armadilha_disparo` inicia uma runa violeta
> na casa visível e elos que sobem em espiral ao redor do peão, em 2D e 3D. Após o
> teste autoritativo, `armadilha_impacto` informa `sucesso` e se a maldição foi
> aplicada: resistência (ou falha sem efeito aplicável) rompe os elos em partículas
> claras; maldição aplicada fecha os elos e revela uma caveira breve. O resultado
> visual é público, mas não contém o tipo de maldição. Mecânica, save e estado da
> maldição continuam no servidor; o renderer respeita a visão de cada cliente.

> **Botas Velozes no inventário:** `SHOP_MERCHANT` declara o item `boots` no
> slot `boots`, e `_slot_category_for_item`/`_slotCategoryForItem` reconhecem
> seu ID mesmo em cópias legadas com `item_slot="item"`. `restore_character`
> migra Botas Velozes já equipadas em `item1`/`item2` para `gear.boots` se o
> espaço estiver livre; assim o slot genérico volta a ficar disponível. O
> bônus de velocidade continua sendo aplicado pelo efeito `spd` do equipamento.

> **Seleção retangular no editor de masmorras:** `tools/editor.js` permite
> arrastar uma moldura na ferramenta Selecionar; `Shift` inicia a moldura mesmo
> sobre um objeto. Arrastar dentro da moldura move o bloco. O menu contextual e
> Ctrl+C/X/V copiam, recortam e colam terreno, materiais, elevações, salas e
> entidades inteiras, preservando offsets e remapeando IDs e vínculos internos.
> Recortes parciais de salas/footprints e destinos fora do mapa ou ocupados são
> recusados. O menu contextual oferece Apagar área selecionada quando o clique direito
> ocorre dentro da seleção; a ação apaga terreno e entidades inteiras contidas nela. Após
> colar por menu ou Ctrl+V, a seleção e a prancheta são limpas e a moldura some. A região copiada leva também as alturas manuais de parede (`alturas_parede`), no deslocamento certo.
