# LEGENDS FOR HIRE — Contrato Visual
## LEIA ESTE ARQUIVO ANTES DE QUALQUER ALTERAÇÃO VISUAL

### Iluminação
- AmbientLight: intensidade 0.7, cor #fff5e0
- DirectionalLight principal: intensidade 1.8, cor #fffaf0
- DirectionalLight preenchimento: intensidade 0.6, cor #e8f0ff
- Fog máximo: FogExp2 density 0.02

### Chão
- Cor base tiles: #888888
- Rejunte: #444444
- emissive: #222222

### Paredes
- Cor base: #5a5a6a
- emissive: #111120
- Rejunte: #2a2a3a

### Dados
- Material: MeshLambertMaterial (emissive garante cor independente da iluminação da cena)
- emissiveIntensity: 0.4
- D4: #FFE000 | D6: #FF1111 | D8: #0055FF
- D10: #00DD44 | D12: #CC00FF | D20: #FF5500
- Números: preto #000000 com stroke branco #FFFFFF 12px, fonte Arial Black 140px
- D20 (faces triangulares): fontSize 90px (1 dígito) e 68px (2 dígitos), centralizado em y=155, canvas clipado ao triângulo [[128,20],[236,210],[20,210]]
- Escala: 1.30× (30% maior que a geometria base)
- Iluminação exclusiva: PointLight principal intensidade 3.0 dist 3.0 (acima y+2) + fill 1.5 dist 2.0 (abaixo y-1), ambas dentro do diceGroup

### Peões
- emissive: 10% da cor principal de cada herói
- Base: #111111 com borda emissive
- SpotLight individual sobre peão ativo: intensidade 1.2

### Peões — Acabamento de Miniatura de Plástico Pintada
- **Materiais (plástico satinado)**: roughness baixa-média define o volume
  - Tecido (`_mClth`/`_cClth`): roughness 0.52, metalness 0.02
  - Couro (`_mLeather`/`_cLth`): roughness 0.46, metalness 0.04
  - Pele (`_mSkin`/`_cSkin`): roughness 0.42, metalness 0.02
  - Madeira (`_mWood`/`_cWood`): roughness 0.62
  - Metal/armadura (`_mMtl`/`_cArmr`): roughness 0.18–0.26, metalness 0.86–0.92
- **Resolução de geometria** via `_withSmoothGeo(T, fn)` — envolve a construção de
  cada peão e força mínimos: Cylinder 24, Sphere 28×20, Cone 24, Torus 16×36.
  Box NÃO é afetado (faces planas devem ficar nítidas). Aplicado em `_cHero`
  (seleção) e `build3DFig` (tabuleiro).
- **Iluminação de estúdio (tela de seleção)**: Ambient 0xfff2e6 0.62 +
  HemisphereLight 0.55 + Key DirectionalLight 1.25 (com sombra) + Fill 0.42 +
  Rim 0.55 + SpotLight 1.4 sobre o selecionado.

### Tipografia
- Títulos: Cinzel Decorative
- Textos: Cinzel
- Cor dourada: #c8a951

### Personagens

**Victor Coice Bravo**
- Classe no tabuleiro: `ranger`; na seleção: `warrior`
- Nome canônico: **Victor Coice Bravo**
- Plaquinha da base: **VICTOR**
- Identificadores de código: `victorCoiceBravo`, `victor_coice_bravo`
- Foto para tela de seleção: `assets/portraits/victor.jpeg`

**Richard, o Cavaleiro**
- Classe no tabuleiro: `paladin`; na seleção: `paladin`
- Nome canônico: **Richard, o Cavaleiro**
- Plaquinha da base: **RICHARD**
- Identificadores de código: `richardCavaleiro`, `richard_cavaleiro`
- Foto para tela de seleção e ficha: `assets/portraits/richard.jpeg` (mesmo modelo do Victor)
- `_CSD.paladin.cls` = `'RICHARD'` (não `'PALADINO'` — renomeado por instrução explícita)

**Habilidades do Richard (5) — Regra Obrigatória**
- Richard **não usa mana** (`mp:0/max_mp:0`); todas as habilidades custam **fome/sede**.
  Botões dedicados via `_paladinSkillBtn` (fora do fluxo MP/toggle genérico).
- **💡 Guerreiro da Luz** (ação livre, toggle): painel flutuante com steppers +/-
  (`abrirPainelGuerreiroLuz`) para 4 bônus 0..2 — Visão/Ataque (pagam **sede**),
  Dano/CA (pagam **fome**). Bônus fixos até desativar; manutenção = custo escolhido/turno.
  Aplicado em combate: Ataque/Dano em `handle_attack`, CA na defesa em `gm_phase` (servidor).
  **Visão** expande dois raios distintos:
  - Servidor — `_get_raio_visao(p)`: névoa permanente (`explored`), **base 3 + bônus** (usado em `handle_move` e na revelação imediata ao ativar).
  - Cliente — `getSightRadius(me)`: detecção AO VIVO de inimigos/cadáveres em `computeVisionSet`, **base 6 + bônus**.
  - Bônus máximo de visão: **+2 quadrados** (Guerreiro da Luz nível 2). Botão ativo mostra `👁️ Visão +N quadrados` (`renderIndicadorVisao`).
- **✨ Regeneração Divina** (ação livre, toggle): **🍖-2 💧-1** ativar; **+1 HP/turno**
  (manutenção 🍖-1 💧-1) até HP máximo (auto-desativa). Botão desabilita com HP cheio.
- **⚔️ Golpe Sagrado** (ação bônus, toggle): **🍖-3 💧-3**; **+1d8** dano sagrado por
  ataque, **dobrado** vs. mortos-vivos/demônios. Manutenção 🍖-1 💧-1. Botão “● ativo” + parar.
- **🛡️ Protetor** (ação bônus): **🍖-2 💧-2**, **raio 4**. Aliado escolhido via
  `openTargetModal` (`iniciarModoProtetor`) recebe **metade** do dano; a outra metade
  vai para Richard (transferência em `_processar_dano_protetor`, servidor). Manutenção 🍖-1.
- **🙏 Imposição das Mãos** (ação principal): **🍖-3 💧-2**, aliado **adjacente** (raio 1)
  via `openTargetModal` (`iniciarModoImposicaoMaos`); cura **1d6 + mod(Força)**. Não funciona
  em si mesmo.
- Incapacitação de Richard zera todos os buffs sustentados (`_player_dies`, servidor).
- Mensagens WebSocket: `imposicao_maos {target_id}`, `golpe_sagrado` / `desativar_golpe_sagrado`,
  `protetor {target_id}` / `desativar_protetor`, `acao_livre_richard {habilidade_id, bonus?}`.

**Luccas, o Astuto**
- Classe no tabuleiro: `rogue`; na seleção: `rogue`
- Nome canônico: **Luccas, o Astuto** (substituiu "Ladino")
- Plaquinha da base: **LUCCAS**
- Foto para tela de seleção e ficha: `assets/portraits/luccas.jpeg` (mesmo modelo do Victor)
- `_CSD.rogue.cls` = `'LUCCAS'`; `server.py` CLASSES["rogue"]["name"] = "Luccas, o Astuto"

**Habilidades do Luccas (5) — Regra Obrigatória**
- Luccas **não usa mana** (`mp:0/max_mp:0`); habilidades custam **fome/sede** (+ ouro nas armadilhas).
  Botões dedicados via `_rogueSkillBtn` (fora do fluxo MP/toggle genérico).
- **🗡️ Ataque Furtivo** (passiva): +**Nd4** de dano na mão principal quando há **aliado
  adjacente ao alvo** OU Luccas está invisível. Escala por nível: 1–2 → 2d4, 3–4 → 3d4, 5+ → 4d4
  (`_dados_furtivo`/`_verificar_ataque_furtivo` no servidor, dentro de `handle_attack`).
- **🔍 Detectar Armadilhas** (ação bônus, toggle): revela armadilhas próximas (raio de visão →
  `explored`) e ativa o gate `detect_trap` (não dispara armadilhas da masmorra). Manutenção **💧-1/turno**.
- **🌑 Esconder nas Sombras** (ação bônus): **🍖-2 💧-1**; teste `d20+mod(DES)` vs `percepção + nº
  monstros`. Em sucesso fica **invisível** (filtrado de `_targets()` no `gm_phase` — monstros não o
  escolhem) e garante o furtivo. Quebra **apenas ao atacar** — mover-se NÃO revela. Manutenção 🍖-1 💧-1/turno.
- **☠️ Veneno Rápido** (ação livre): **💧-1** + consome 1 frasco da bolsa. Reusa
  `weapon_poison`/`VENENO_CARGAS` — os próximos golpes certeiros envenenam (`abrirPainelVenenoRapido`).
- **🪤 Criar Armadilha** (ação principal): **🍖-2 💧-1** + custo em ouro; 8 tipos
  (`ARMADILHAS_LUCCAS`/`ARMADILHAS`). Painel `abrirPainelCriarArmadilha` → modo **placement**
  (`window._modoPlacementArmadilha`, cursor crosshair + legenda), clique numa casa sua/adjacente em
  `on3DClick` → `onClickTileParaArmadilha` → `criar_armadilha {tipo, tx, ty, veneno_id?}`.
- **🔧 Desarmar Armadilha** (ação principal): botão extra exibido só com armadilha na casa/adjacente
  (`_temArmadilhaAdjacente`); teste de DES (nat1 dispara no próprio Luccas).
- Estado serializado no jogador (push_state envia o dict inteiro): `invisivel_sombras`,
  `detectar_ativo`, `weapon_poison`/`weapon_poison_hits`.
- Mensagens WebSocket: `detectar_armadilhas`, `esconder_sombras`, `veneno_rapido {veneno_id}`,
  `criar_armadilha {tipo, tx, ty, veneno_id?}`, `desarmar_armadilha`.

**Frade Lewis**
- Classe no tabuleiro: `cleric`; na seleção: `cleric`
- Nome canônico: **Frade Lewis** (substituiu "Clérigo")
- Plaquinha da base: **FRADE LEWIS**
- Foto para tela de seleção e ficha: `assets/portraits/lewis.jpeg` (mesmo modelo do Victor)
- `_CSD.cleric.cls` = `'FRADE LEWIS'`; `server.py` CLASSES["cleric"]["name"] = "Frade Lewis"

**Henrique, o Bardo**
- Classe no tabuleiro: `bard`; na seleção: `bard`
- Nome canônico: **Henrique, o Bardo** (substituiu "Bardo")
- Plaquinha da base: **HENRIQUE**
- Foto para tela de seleção e ficha: `assets/portraits/henrique.jpeg` (mesmo modelo do Victor)
- `_CSD.bard.cls` = `'HENRIQUE'`; `server.py` CLASSES["bard"]["name"] = "Henrique, o Bardo"

**Habilidades do Henrique (3) — Regra Obrigatória**
- Henrique **não usa mana** (`mp:0/max_mp:0`); suas habilidades custam **fome/sede**.
- **📖 Conhecimento das Lendas** (passiva, sempre ativa): com um Henrique vivo no
  grupo, o tooltip de QUALQUER inimigo (hover, 2D e 3D) vira a **ficha completa** —
  CA, HP exato, dano, acerto, nível, XP/ouro, tags (morto-vivo/chefe) e marca de
  provocado. Sem bardo vivo, o tooltip mostra só nome + HP/CA.
  Implementado em `fichaInimigoTooltipHTML()` + `_partyTemBardoVivo()`.
- **🎵 Canção Heroica** (ação principal, toggle): painel flutuante (`abrirPainelCancao`)
  para escolher entre 5 atributos (Acerto/Dano/Armadura/Movimento/Resistência);
  cada atributo custa **1 fome OU 1 sede/turno** (ativação + manutenção). Buffs em
  **raio Chebyshev 5**, desenhado como **círculo dourado** no tabuleiro (2D no
  `renderMap`; anel 3D `_sync3DCancaoRing` em `g3.scene`). Atacar sob a canção custa
  **+2🍖/+1💧** no 1º ataque do turno. Botão no painel mostra estado “● cantando”.
- **😤 Provocação** (ação bônus): custo **🍖-3 💧-3**, **raio 3**. Seleção de alvo via
  `openTargetModal` (`iniciarProvocacao`); força o inimigo a atacar Henrique por 3
  turnos + desvantagem no 1º ataque. Botão desabilita sem recurso ou com bônus já usado.
- Mensagens WebSocket: `ativar_cancao {atributos:[]}`, `desativar_cancao`, `provocacao {target_id}`.

**Pedro, o Tímido**
- Classe no tabuleiro: `mage`; na seleção: `mage`
- Nome canônico: **Pedro, o Tímido** (substituiu "Mago"/"Mago Negro")
- Plaquinha da base: **PEDRO**
- Foto para tela de seleção e ficha: `assets/portraits/pedro.jpeg` (mesmo modelo do Victor)
- `_CSD.mage.cls` = `'PEDRO'`; `server.py` CLASSES["mage"]["name"] = "Pedro, o Tímido"
- NÃO confundir com o monstro `dark_mage` ("Mago das Trevas") — inalterado

**Pedro — Aba de Magias e Animar Mortos** (cor temática roxa: `#cc44ff`, `#9900cc`)
- Pedro tem uma aba extra **"Magias"** na ficha (além de "Atributos"), alternada por
  `trocarAbaFicha(aba, heroKey)` dentro de `#conteudo-ficha-pedro`
  (`renderFichaPedro` / `renderAbaMagiasPedro`, em `game.js`).
- **Animar Mortos** — habilidade de classe, **sempre disponível**, ação principal,
  alcance adjacente ao cadáver; custo **−20 fome / −20 sede** por uso (cobrado
  independente do resultado). Dados em `HERO_DATA.pedro.habilidadeClasse`.
- **Animados** — genéricos, baseados no **nível do monstro** (não em tipos
  específicos); **slots ocupados = nível** do monstro; slots máximos =
  `mod(INT) + ⌊nível/2⌋` (mín. 1). Não podem ser curados, persistem entre
  aventuras, nunca recuperam vida; a 0 de vida viram pó permanentemente.
- **Hostis** (falha catastrófica) — permanentes, **não reaniméveis**, atacam o
  alvo mais próximo.
- **Rolagem D100** — animação de **dois d10** (dezena + unidade) antes de revelar
  o resultado (`animarRolagemD100`); faixas hostil/sucesso/falha derivadas da
  diferença de nível.
- STATUS: ficha (seleção + em jogo) e tooltips ligados; **Animar Mortos roteado**
  (fatia vertical — ver abaixo). `mostrarTooltipMagia` **implementado** (ver
  Cartas de Magia abaixo). Pendentes: animados como unidades de combate
  (agir/hostis/persistência), e o mapeamento Fome/Sede.

### Cartas de Magia (Grimório) — Regra Obrigatória
- Catálogo do cliente em `GRIMORIO_CLIENT` (`game.js`) — **espelha** `GRIMORIO`
  (`server.py`); os 27 ids/círculos batem 1:1. Renderização via
  `criarCartaMagia(id, selecionada, disponivel, usada)`.
- **Carta: 60×72px**, borda 2px, cor por **círculo**:
  1º dourado `#c8a951` · 2º azul `#4488ff` · 3º roxo `#cc44ff`.
- **Magia usada**: `opacity 0.35`, ícone **💤** no lugar do ícone da magia.
- **Selecionada**: fundo `rgba(cor,0.20)` + ponto inferior na cor do círculo.
- **Tooltip** `#tooltip-magia` (fixed, `z-index:999`, **220px**, segue o cursor):
  cabeçalho com ícone + nome + label do círculo, descrição completa (HTML) e linha
  de custo em laranja `#ff851b`. Mostrar/ocultar via `mostrarTooltipMagia(id, ev)`
  (aceita também a ordem antiga `(ev, id)`) / `ocultarTooltipMagia()`.
- **Abas de magia** de Pedro (mage) e Lewis (cleric) usam
  `renderMagiasFichaEmJogo(heroi, cls)` — cartas por círculo + pips de slot verde
  `#44cc88`. Sem lista explícita de conhecidas, mostra **todas as elegíveis pela
  classe** (alinhado ao gating por classe do servidor).
- **Lançamento (ligado):** clicar uma carta em jogo chama `castarMagia(id)`
  (`criarCartaMagia(..., 'jogo')`). Sem alvo de tabuleiro (ex.: Manto de Escuridão)
  → envia `{type:'magia', magia_id}` na hora. Com alvo → entra em **modo de mira**
  (`window._modoMagia`, banner `#legenda-magia`, cursor crosshair, ESC cancela) e o
  próximo clique no tabuleiro resolve o alvo: inimigo/aliado → `target_id`, área →
  `tx/ty`, linha → `segmentos`. O clique é capturado em `handleTileClick` (2D/3D) e
  em `on3DClick` (3D, antes do baú). Fora da vez/ação usada → `toast` de aviso.
- **Magias de dano de Pedro (revisadas — implementadas no servidor):**
  Bola de Fogo = `area_persistente` (R1 1d6/nível, R2 ½R1, R3 ½R2; zona persiste e
  causa dano ao pisar). Relâmpago = `linha_reflexiva` (1d6/nível por impacto; pode
  ferir aliados/caster). Raio Congelante = `alvo` (3d4 +2d4/2 níveis **sem save**;
  Fortitude evita paralisação de 1–2 rodadas). As cartas/tooltip já refletem isso.
### Feedback visual de magia — Regra Obrigatória
- **Dados na tela:** o servidor anima CADA dado via broadcast `dice_roll`
  (`handleDiceRoll`): cada dado de **dano** (`🔥/⚡/❄️ Dano`, ex.: 4×d6) e o **d20
  de resistência** de cada alvo (`Reflexos/Fortitude/Vontade ✓/✗`). Helpers no
  servidor: `_rolar_dano_mostrado(n,faces,label)` e `_save_mostrado(alvo,tipo,dif)`.
- **Realce de casas (2D e 3D):** ao ativar a carta entra-se em modo de mira
  (`window._modoMagia`); estado em `window._spellHL = {range,area,zonas}`.
  - **Alcance = VERMELHO** (`rgba(255,40,40,.22)` 2D / `0xff2a2a` 3D), fixo no caster.
  - **Área de efeito = VERDE** (`rgba(40,230,70,.34)` / `0x28e636`), **segue o cursor**
    ao vivo (área quadrada p/ `tile`, casa única p/ alvo único).
  - **Atingido 2× = VERDE ESCURO** (`rgba(8,90,25,.62)` / `0x0a5a16`). **Relâmpago**:
    tem um **orçamento de deslocamento = alcance** (7 no nível 1). Anda na direção do
    cursor; ao bater numa **parede**, ricocheteia e continua gastando o que sobrou
    (ex.: 5 até a parede + 2 de volta = 7). Casas pisadas **1× = verde claro**, casas
    pisadas **2× = verde escuro**. Pedro só é ferido se o ricochete voltar até a casa
    dele. Sem parede no caminho, vai reto e não há casas 2×. Mensagem: `dir:[dx,dy]`;
    caminho autoritativo em `_caminho_relampago` (servidor) e `_caminhoRelampagoCli`
    (cliente) — mesmos passos/ricochete.
  - **Zona de fogo persistente = LARANJA** (`0xff6a00`), desenhada sempre enquanto
    `game_state.zonas_especiais` tiver a zona ativa (Bola de Fogo R2/R3).
  - Durante a mira, os realces de **movimento/ataque ficam ocultos**.
  - 2D: `_desenharSpellHL2D(ctx)` em `renderMap` (passe 1.5). 3D: planos por tile
    `g3.spellRangeMeshes/spellZonaMeshes/spellAreaMeshes`, alternados em
    `_aplicarSpellHL3D()` (chamado em `renderMap3D` e no hover). Hover: `on3DMouseMove`
    e o `mousemove` do `#dungeon-canvas`. `area_centrada` (Manto) usa `self_area`:
    mostra a área no caster e confirma com um clique.

**Animar Mortos — fluxo WebSocket (fatia vertical)**
- Servidor rastreia **cadáveres** (`self.corpses`, criados em `_monster_dies` a
  partir de monstros não-boss; `tier`=nível). Enviados ao cliente em
  `game_state.corpses` e desenhados no tabuleiro 2D (ícone roxo esmaecido).
- Cliente: clicar no card **Animar Mortos** (ficha em jogo) → `usarAnimarMortos()`
  acha o cadáver adjacente (`GS.cadaverAdjacente`) e envia `animar_mortos`.
- Servidor `handle_animar_mortos` (async, roteado): valida Pedro (`class_id 'mage'`),
  ação principal, adjacência (Chebyshev≤1) e slots (`mod(INT)+⌊nível/2⌋`); custo
  −2 fome/−2 sede; rola d100 (dois d10); **sucesso** → animado entra em
  `player['animados']` e o cadáver some; **hostil** → o monstro morto revive vivo;
  **falha** → nada. Responde `animar_result` (animação D100 no cliente +
  sincroniza animados) e `push_state`.
- Animados são **entidades de combate** do dono (Pedro): nascem na casa do
  cadáver (`pos`), são desenhados no tabuleiro 2D (base roxa + ícone + barra de
  vida) e persistem entre masmorras.

**Animados em combate (sistema completo)**
- **Peão do monstro original:** o animado é desenhado no 2D com o sprite do monstro
  de origem (`tipo`) + anel roxo de aliado (branco se selecionado); barra de vida roxa.
- **Turno dos servos (logo após o mago):** ao "Encerrar Turno", se o mago tiver
  animados vivos, abre-se a **fase dos servos** (`animados_turn` = pid; badge roxo
  "💀 Servos de …") — o MESMO jogador controla; o próximo "Encerrar Turno" passa
  adiante. Cada animado tem `moves_left` (= `movimento`) e 1 ataque, resetados ao
  entrar na fase. Controle 2D: clique no servo → seleciona; clique em casa adjacente
  livre → move 1 passo (`mover_animado`); clique em monstro adjacente → ataca
  (`atacar_animado`, d20+nível vs CA). Atalho "⚔️ COMANDAR SERVOS" (aba Magias,
  `comandar_animados`) auto-resolve os servos restantes (respeita `moves_left`/`acted`).
- **Upkeep:** ao reanimar, cada cadáver custa **−1 fome e −1 sede por turno** ao mago
  (cobrado na entrada da fase dos servos; escala 0–10 do servidor, exibida em `#my-stats`).
- **Monstros miram animados também** (`gm_phase`): escolhem o alvo mais próximo
  entre jogadores vivos + animados; atacar um animado reduz `vida_atual`.
- **Pó (permanente):** animado a 0 HP é removido; se o **Pedro morre**, todos os
  seus animados viram pó imediatamente; nunca recuperam vida / não podem ser curados.
- **Hostis** (falha catastrófica) já revivem como monstro normal e atacam o mais
  próximo via `gm_phase`.

**Painel principal do Pedro = ficha com abas (em jogo)**
- O painel sempre-visível `#my-stats` do Pedro tem abas **📊 ATRIBUTOS** (stats de
  combate autoritativos) e **💀 MAGIAS** (`renderAbaMagiasPedro`), alternadas por
  `trocarAbaPainel(aba)` (estado em `_painelAbaPedro`). Substitui o antigo botão
  "VER FICHA COMPLETA" / tecla F (removidos). Demais heróis: só os atributos.

**Pedro — Metamagia (botões no `#skills-list`)** — 3 ações livres (toggles)
**EMPILHÁVEIS** que modificam a **magia do GRIMÓRIO** lançada no turno (mensagem WS
`magia` / `handle_magia`). **NÃO** o sistema legado `fireball/ice_lance/magic_shield`
(`skill`), que segue oculto e inerte (sem metamagia). Botões por `_mageSkillBtn(me, sk)`
(toggle simples → `send({type: sk.id})`; padrão `skill-btn`/`skill-active`), interceptados
no loop de skills (ids `aprimorar_magia`/`estender_magia`/`fortalecer_magia`).
- **🎯 Aprimorar Magia** — +1 na **CD do teste de resistência** (somado em `_dif_magia`
  via flag temporária `_mm_dc_bonus` no caster). Custo 🍖-3.
- **⏱️ Estender Magia** — **+1 turno** na duração (aditivo: executores fazem
  `_rolar_dado(duracao) + dur_bonus`). Custo 🍖-3 💧-3.
- **💥 Fortalecer Magia** — **dano ×1,5**, arredondado meio-pra-cima (`int(x*dmg_mult+0.5)`
  nos 5 executores de dano). Custo 🍖-6 💧-6.
- **Empilháveis**: pode armar as 3; custos somam. **Só cobra (e só aplica) se a habilidade
  tiver efeito** na magia: Fortalecer só com dano, Estender só com `"duracao"`, Aprimorar só
  com `"save"` (ver `handle_magia` + `_magia_tem_dano`). Custo pago AO LANÇAR. Flags limpas
  em `handle_end_turn`. Toggle OFF não reembolsa (nada foi cobrado ao armar).
- ❌ **Acelerar Magia e Magia Reflexa foram REMOVIDAS** (Pedro estava forte demais).
- STATUS: **verificado ao vivo** — os 3 botões armam; `velocidade`+(apr/est/fort) → só
  Estender (`+1 turno`); `bola_fogo`+(apr/est/fort) → Fortalecer (R1 = `int(3×1,5+0,5)=5`)
  + Aprimorar, custo somado 🍖-9 💧-6, Estender corretamente excluído.

**Ficha do herói durante o jogo (`abrirFichaEmJogo`)** — agora usada só para
**visualizar outro herói** (clique no mini-card de `#player-cards`); `ESC` fecha.
- Overlay (`#ficha-overlay-jogo`, `z-index:300`) com cabeçalho (retrato/nome/classe/
  nível) + conteúdo. Usa `GS.me` (jogador autoritativo do servidor) para HP/
  atributos/CA/nível; cai para `HERO_DATA[heroiKey]` (registro completo) quando
  fora de combate.
- **Tecla `F`** abre/fecha a ficha do herói ativo (ignorada em INPUT/TEXTAREA);
  **`ESC`** fecha. Também fecha por clique fora ou nos botões ✕ / FECHAR.
- Botão **`📋 VER FICHA COMPLETA`** + dica **`[F] FICHA`** no rodapé de `#my-stats`.
- **Clicar num mini-card** de `#player-cards` abre a ficha daquele herói
  (`_classIdParaHeroiKey(p.class_id)`).
- **Pedro**: ficha com abas **ATRIBUTOS** e **MAGIAS** (Animar Mortos);
  `trocarAbaFichaJogo` alterna as abas. **Demais heróis**: apenas atributos.
- NOTA: bloco Fome/Sede da ficha lê `hunger`/`thirst` (`/100`), mas o servidor usa
  `fome`/`sede` (0–10) — o bloco fica inerte em combate até mapear os campos.

**Victor — Habilidades de Guerreiro (custo Fome/Sede, sem MP)**
- **Warrior NÃO usa MP** — `CLASSES["warrior"]["mp"] = 0` / `max_mp = 0`. Suas
  habilidades custam **fome e sede** (campos `fome_cost`/`sede_cost` em cada skill),
  não mana. A barra de MP é **ocultada** no card do warrior em `renderPlayers`
  (`game.js`); fome/sede seguem nas `survival-bars`.
- **As 3 habilidades** (todas `target: 'self'`, definidas em `CLASSES["warrior"]["skills"]`).
  Custos (escala 0–10, cumulativos quando várias armadas):
  - ⚔️ **Mira Certeira** (`mira_certeira`) — +2 no acerto neste turno · 🍖0 / 💧2
  - 💥 **Golpe Devastador** (`golpe_devastador`) — dobra cada dado de dano neste turno · 🍖2 / 💧4
  - 🔥 **Fúria Berserker** (`furia_berserker`) — 2º ataque manual neste turno · 🍖5 / 💧5
  - **Ataque básico**: −1 fome por ação de ataque (`handle_attack`), somado aos buffs.
  - **SEM teto de custo**: o jogador pode armar/usar quantas quiser mesmo sem ter o
    recurso — fome/sede são debitadas e **clampadas em 0** (risco de exaustão). Não
    há rejeição por falta de recurso nem trava de botão por orçamento. Quem
    administra o recurso é o jogador.
- **Barras de Fome/Sede do HUD** = `player.fome`/`player.sede` do **servidor** (0–10),
  o recurso real que as habilidades/ataque consomem (`renderBarrasSobrevivencia(p)`).
  (Antes liam o sistema-cliente 0–100 `GS.survival`, que não refletia o consumo.)
- **Modelo TOGGLE (armar/desarmar) — custo cobrado só na AÇÃO (ataque):**
  - Clicar no botão da skill **arma** (seleciona) sem custo; clicar de novo **desarma**.
    Cumulativas — várias podem ficar armadas (limite = fome/sede disponível, com
    gating no cliente: não deixa armar combo que não cabe no orçamento).
  - O custo de fome/sede é pago **quando Victor ataca** (`handle_attack` recebe a
    lista `buffs` e cobra/aplica as flags **após** o range-check). Sem ataque = sem custo.
  - A seleção vive **no cliente** (`GS.warriorSelected`, toggle via
    `GS.toggleWarriorSkill`); o ataque envia `{type:'attack', target_id, buffs}` e
    `sendAttack` limpa a seleção. No **próximo turno** ficam selecionáveis de novo
    (auto-clear em `_handle` quando deixa de ser meu turno).
  - **Botões SEMPRE disponíveis durante o meu turno** — NÃO travam após atacar.
    Gating do toggle = `isMyTurn && alive && phase==='playing'` + orçamento (só não
    arma uma NOVA skill se o custo não couber em fome/sede; desarmar é sempre
    permitido). O custo só é pago ao atacar; o limite do uso contínuo é fome/sede.
  - `handle_skill` para skills sem `mp` virou **no-op** (custo migrou para o ataque),
    evitando cobrança dupla.
- **Modelo de flags = campos PLANOS no player** (não um dict `skill_flags`):
  `skill_bonus_acerto` (int), `skill_dobrar_dano` (bool), `skill_ataque_extra` (bool),
  `skill_extra_usado` (bool — Fúria: extra já concedido no turno).
  Inicializados em `make_player`, trafegam ao cliente via `push_state`,
  **limpos em `handle_end_turn`**.
- **Botões de skill mostram custo em 🍖 (fome) e 💧 (sede)** — nunca 💙 (MP).
- **Indicador de flags ativas no HUD** — `renderFlagsWarrior(me)` (`game.js`) desenha
  chips ⚔️ +N acerto / 💥 Dano ×2 / 🔥 Extra (a partir da seleção armada ou dos
  campos planos `me.skill_bonus_acerto` / `me.skill_dobrar_dano` / `me.skill_ataque_extra`).
- **Warrior não entra em modo de mira** — o botão de skill é um toggle de seleção;
  o ataque é que carrega os `buffs` armados.
- **Ataque extra (Fúria) = SEGUNDO ATAQUE MANUAL**: quando a Fúria está armada,
  `handle_attack` deixa `action_done=False` (e marca `skill_extra_usado=True`),
  liberando um 2º ataque manual no mesmo turno — o jogador clica atacar de novo e
  pode **rearmar habilidades** para esse golpe (pagando mais fome/sede). O 2º ataque
  cai no `else` e encerra a ação. No próximo turno tudo reabre (`handle_end_turn`).
- ✅ **STATUS — implementado e testado (in-process: ciclo completo de turnos +
  re-disponibilidade + limite por fome/sede; e verificado ao vivo no browser).**
  - **Servidor** (`handle_attack(pid, target_id, buffs)`): após o range-check, soma
    `fome_cost`/`sede_cost` das skills em `buffs`, valida saldo, debita, chama
    `_verificar_estado_sobrevivencia` e seta os campos planos; resolve o ataque
    (mão principal, 2ª mão e Fúria inline com acerto/dano dobrado). Recurso
    insuficiente → ataque rejeitado sem cobrar. `handle_skill` sem `mp` é no-op.
  - **Cliente**: `gameState.js` guarda a seleção (`warriorSelected` + toggle/getters,
    auto-clear ao trocar de turno); `renderMyPanel` desenha os botões como toggle
    (🍖/💧, gating por orçamento, trava por `action_done`, acessos a GS defensivos);
    `sendAttack` anexa `buffs` e limpa a seleção; `_CSD.warrior.skills` sincronizado.

**Richard — Cores da Miniatura 3D**
- Armadura prata polida: `#b8b8c0` roughness 0.20 metalness 0.90
- Armadura prata highlight: `#d0d4e0` roughness 0.14 metalness 0.96
- Entalhes e detalhes dourados: `#c8a951` roughness 0.28 metalness 0.82
- Capa azul real: `#1a3a8f` roughness 0.92 (DoubleSide)
- Escudo face azul: `#1a3a8f` roughness 0.70 metalness 0.04
- Lâmina da espada: `#d4dce8` roughness 0.14 metalness 0.96
- Pele: `#c8956a` (via `_mSkin`)
- Cabelo castanho: `#4a2e10`
- Escala: `scale(1.0, 1.0, 1.0)` — herói mais alto, referência de escala do grupo
- Iluminação especial: SpotLight branca intensidade 1.8 (topo) + PointLight azul `#1a3a8f` intensidade 0.4 (capa)

### Retratos de Heróis — Regra Obrigatória
- Retratos são **exclusivos da tela de seleção de personagem**, implementados em HTML puro
- O painel de retrato existe dentro de `#cs-portrait-frame` no `#cs-panel`
- Ao entrar no tabuleiro (`destroyClassSelectFull`), a imagem é zerada (`img.src = ''`)
- **NUNCA** adicionar mesh, sprite ou PlaneGeometry sobre o tabuleiro para retratos
- **NUNCA** usar `THREE.TextureLoader` ou `CanvasTexture` de retrato em `g3.scene`
- Para adicionar retrato de novo herói: inserir campo `portrait:` no objeto `_CSD[classId]`

### Atributos de Personagens — Regra Obrigatória
**Os únicos atributos exibidos são:** Força, Destreza, Inteligência, Constituição (nesta ordem)
- Escala: 1–25 (sistema D20 — mapeado para 0–100% na barra)
- Nenhum outro atributo (Magia, Sorte, Agilidade, etc.) deve ser exibido na tela de seleção
- Renderização: barra dourada (#c8a951) com label + valor numérico à direita
- Estrutura de dados: `stats: { forca, destreza, inteligencia, constituicao }`
- Valores espelham os campos `str_`, `dex`, `int_`, `con_` do `CLASSES` em server.py

### Consumo de Fome/Sede no Servidor — Sistema Unificado (Regra Obrigatória)
**Escala 0–100** (servidor = cliente; `SOBREVIVENCIA_MAX=100`, `FATOR_CONVERSAO=1`,
sem conversão). Variáveis autoritativas: `player["fome"]`, `player["sede"]`, **início = 100**.
As barras do HUD (`renderBarrasSobrevivencia(p)`) e a vinheta leem esses valores.
Custos por AÇÃO (não 1×/turno como no modelo antigo):
- **Caminhar** → −1 sede, **uma vez por turno** (1ª casa andada; flag `moved_this_turn`,
  resetada em `handle_end_turn`). Andar várias casas no mesmo turno custa só −1.
- **Ataque básico** → −1 fome por ataque (`handle_attack`, direto).
- **Habilidades do warrior** → custo próprio em `fome_cost`/`sede_cost` (cobrado no ataque).
- **Ação bônus** → −1 fome **e** −1 sede (`CONSUMO_ACOES['acao_bonus']={fome:1,sede:1}`),
  via `_consumir_recursos`/`_executar_acao_bonus` (equipar do inventário, poção/itens
  de bolsa, arremesso quando já agiu, ataque de mão secundária). `handle_unequip`
  ainda **não** cobra ação bônus.
- Tudo clampado em 0 (sem teto de gasto — risco de exaustão).
- **MODIFICADOR DE SOBREVIVÊNCIA** (`_modificador_sobrevivencia(p)` = bônus −
  penalidade), aplicado a **todos os acertos, testes de resistência e dano do
  jogador** (no `handle_attack` via `eff_atk` + dano mão principal/2ª mão; e nos
  saves, ex.: Reflexos de armadilha):
  - **BÔNUS +1 (SACIADO)**: quando **fome > 80 E sede > 80** (precisa dos dois;
    perde-se se qualquer um cair a ≤ 80).
  - **PENALIDADE**: **−1** por fome **< 20** e **−1** por sede **< 20** (somam → −2).
  - Faixa neutra (20–80, ou só um > 80) = **0**.
  - Marcador no HUD (`renderMyPanel`): faixa **verde "✦ +1 SACIADO"** ou
    **vermelha "⚠️ −N EXAUSTÃO"**; some na faixa neutra.
  - Aplica também às **magias de dano/acerto** de todas as classes (`_apply_skill`:
    fireball, ice_lance, backstab, smite, holy_light, double_shot, arrow_rain,
    piercing_shot, heavy_blow) — **não** afeta curas/buffs (não são "dano").
- **Custo de AÇÃO universal**: usar uma habilidade (`handle_skill`, caminho de MP)
  custa **−1 fome**, igual ao ataque básico (`handle_attack`). Assim o consumo por
  ação vale para todas as classes (o mago gasta fome ao conjurar, etc.).
- **EXAUSTÃO**: jogador com **fome OU sede em 0** perde **−1 HP por rodada**
  (`_aplicar_exaustao_rodada`, chamado no fim de cada rodada em `handle_end_turn`,
  roda mesmo sem monstros), até **ambos** voltarem acima de 0. **HP 0 = morte**
  (`_player_dies`). `_verificar_estado_sobrevivencia` continua placeholder (não usado
  para a exaustão).
- **Sistema-cliente paralelo (`GS.survival` 0–100) DESATIVADO**: `endTurn()` não
  consome mais no cliente e o colapso-cliente no início do turno foi removido. As
  funções antigas continuam definidas (compartilham `adicionarLog`/`SOBREVIVENCIA_CONFIG`
  com `inicializarHeroi`/`aplicarConsumivel`) mas o runtime inerte não roda.

### Ação Bônus — Regra Obrigatória
- Máximo **1 ação bônus por turno** (campo `bonus_action_used` no estado do jogador)
- Toda ação bônus consome via `_consumir_recursos(p, 'acao_bonus')` (0.1 Fome / 0.1 Sede na escala 0–10)
- Ações bônus válidas: beber poção, usar item mágico, envenenar arma, usar item de bolsa com effect `heal/mana/atk_bonus/antidote`
- **Equipar/trocar do inventário** (`handle_equip_from_bag`) custa ação bônus: controlador checa/marca `bonus_action_used` + `_consumir_recursos(p,'acao_bonus')`; lógica em `_executar_equip_from_bag` (inalterada, retorna True/False). Em falha de validação, nada é consumido.
- **Arremesso de adaga** após já ter agido também vira ação bônus (ver seção da Adaga)
- Reset automático em: início de turno, fim de turno, nova dungeon, novo round
- UI: botão "🎯 Usar (bônus)" quando disponível; "⚠ Ação bônus usada" (desabilitado) quando esgotada
- Painel de status exibe: 🍖 Fome (0–10), 💧 Sede (0–10), 🎯 Ação Bônus (livre/usada)
- Fome/Sede em vermelho quando ≤ 3

### Lojas e Equipamento Inicial — Regra Obrigatória

**Lojas da cidade (autoritativas no servidor).** O sistema de lojas já existe
e é completo, com `server.py` como fonte autoritativa. **Não criar UI de loja
paralela / client-side** — usar e estender a existente.
- Locais (tela `#screen-city`, abertos por `openShop(shopId)` em `game.js`):
  🔨 **Ferreiro** (armas + armaduras), 🍺 **Taverna** (comida/descanso),
  🛒 **Mercado/Mercador** (poções/acessórios), ⛪ **Templo** (bênçãos/curas).
- Catálogos no servidor: `SHOP_WEAPONS`, `SHOP_ARMORS`, `SHOP_MERCHANT`,
  `SHOP_TAVERN`, `SHOP_TEMPLE`. Campos de item: `id`, `name`, `emoji`, `die`,
  `stat`, `price`, `range`, `kind`, `effect`, `value`, `item_slot`.
- Compra/venda: `buyItem(shop, itemId)` → `{type:'shop_buy'}` →
  `handle_shop_buy` (desconta `gold`, equipa) → `shop_result` + `city_state`.
  Venda devolve `price // 3`. Ouro inicial: `start_gold: 20`.
- Abas do modal: Ferreiro = Armas / Armaduras / Vender; Mercador = Comprar /
  Vender (`shop-tabs` em `game.js`).

**Catálogo de equipamento inicial (client-side, em `src/gameState.js`).**
`GS.EQUIPAMENTOS_INICIAIS` + `GS.HERO_DATA` + `GS.inicializarHeroi(heroKey)`
definem o equipamento inicial canônico de cada herói. Identificadores de herói
seguem este arquivo: `victorCoiceBravo`, `richardCavaleiro`, `lewis`, `luccas`,
`henrique`, `pedro`.
- Todos começam com `moedas: 20` e `inventario` de 6 slots (todos `null`).
- Modelo de equipamento da spec: slots
  `arma / armadura / cabeca / secundario / magico1 / magico2`; itens com campos
  `id, nome, dano, atributo, escudo, arremesso, alcanceArremesso, preco`.
- Armas iniciais: Victor → Machado de Ferro (`machado_basico`); Richard →
  Espada Curta; Lewis → Cajado de Madeira; Luccas → Adaga + Adaga Secundária
  (dual-wield, arremesso alcance 3); Henrique → Instrumento Musical + Adaga;
  Pedro → Cajado de Madeira.
- `inicializarHeroi(heroKey)` faz **deep copy** (instâncias isoladas) e
  inicializa sobrevivência (fome/sede = `inicioAventura` = 80), `efeitos: []`.

**Equipamento inicial AUTORITATIVO no servidor (`server.py`).** O modelo da spec
foi portado para o servidor (autoritativo); o catálogo client-side acima é o
espelho. Mapeamento de slots (a spec é subconjunto do modelo do servidor, que é
preservado para não perder anéis/itens):
- `arma` → `gear.weapon` (+ `p["weapon"]` de combate) · `armadura` → `gear.armor`
- `cabeca` → `gear.head` · **`secundario` → `gear.off_hand`** (dual-wield/escudo)
- `magico1` / `magico2` → `gear.item1` / `gear.item2`
- `moedas` → `gold` (inicial 20) · `inventario` → `bag` (`bag_size` 6)

Armas iniciais por classe (`WEAPONS` + `CLASSES[*].weapon` + `_STARTING_OFFHAND`):
- warrior/Victor → `machado_basico` "Machado de Ferro" (1d6 FOR)
- paladin/Richard → `shortsword` "Espada Curta" (1d6 FOR)
- cleric/Lewis → `cajado_madeira` (1d6 **INT**) · mage/Pedro → `cajado_madeira` (1d6 INT)
- rogue/Luccas → `dagger` + off_hand `dagger` (dual-wield; `adaga_secundaria` foi retirada)
- bard/Henrique → `instrumento` (sem dano) + off_hand `dagger` (dual-wield)

Mecânicas de combate adicionadas (`handle_attack`):
- **Finesse** (`atributo: forcaOuDestreza`): arma com `finesse:true` (adagas)
  usa o **melhor** modificador entre FOR e DES no dano.
- **Dual-wield**: se `gear.off_hand` for arma (tem `die`) e o alvo seguir vivo e
  ao alcance, há um **ataque extra de mão secundária** (d20 vs CA própria; dano =
  `die` **sem** modificador de atributo; alcance = `range`/`throw_range`/1).
- `throw_range` (arremesso) está nos dados das adagas (alcance 3) e já habilita
  o alcance da mão secundária; o **arremesso da mão principal** ainda não é um
  modo separado (mão principal continua corpo-a-corpo) — melhoria futura.
- Decisões de design (ajustáveis): casters (cleric/mage) passam a usar **INT**
  no dano do cajado (era FOR); bardo usa instrumento sem dano (depende de
  habilidades) + adaga de mão secundária. Itens mágicos (`magico1/2`) usam os
  efeitos de item já existentes (`atk/def_/maxhp/spd/bagslots`) — sem novas
  mecânicas de magia por enquanto.
- Verificado por testes (26 unitários in-process + 9 end-to-end via WebSocket).

**REGRA — Equipamento inicial nunca alterado diretamente.** Os equipamentos
iniciais são definidos **somente** em `GS.EQUIPAMENTOS_INICIAIS` e **nunca**
devem ser mutados diretamente. Para criar um herói novo, use **sempre**
`GS.inicializarHeroi(heroKey)`, que faz deep copy (instâncias isoladas) +
inicializa sobrevivência/efeitos. Itens iniciais são **gratuitos** (não descontam
`moedas`); as 20 moedas iniciais servem para compras na taverna/ferreiro.
**Nenhum herói começa com armadura** (primeira compra importante).

**Validação de equipar — `GS.podeEquipar(heroi, item, slot)`.** Retorna
`true/false` e loga a recusa via evento `survivalLog`. Regras, na ordem:
1. **Restrição de classe**: `item.permitidoPara` (lista de heroKeys). Ausente =
   sem restrição. Ex.: varinhas → `permitidoPara: ['lewis','pedro']`.
2. **Slot fixo**: se `item.slot` for declarado, deve bater com `slot`.
3. **Arma de duas mãos vs escudo**: `item.duasMaos` é bloqueado se a secundária
   já tiver `tipo:'escudo'`.
4. **Escudo vs arma de duas mãos**: equipar escudo na `secundario` é bloqueado se
   `equipado.arma.duasMaos`.

**Varinhas (planejado).** 3 níveis — Varinha Simples (1 magia, 100🪙), de Poder
(2, 300🪙), Arcana (3, 600🪙); dano 1d4+INT. Regras: armazenam magia durante a
campanha (1 por slot), recarregáveis na cidade; usar = **ação bônus** (−1 fome /
−1 sede, **não** gasta MP — usa a carga); só **Lewis e Pedro** (`permitidoPara`),
ocupam o slot **`secundario`**. Local de venda (Mercador vs nova Loja Mágica)
e o sistema de cargas ainda **não implementados** — pendente de decisão.

### Catálogo de Itens e Loja (overlay) — Regra Obrigatória

**REGRA: todos os itens do jogo estão em `GS.CATALOGO_ITENS` (`src/gameState.js`).
Nunca criar itens fora deste objeto.** Fonte única, keyada por `id` — **49 itens**:
Ferreiro 31 (18 armas incl. 4 à distância + 6 armaduras + 2 escudos + tocha +
4 munições), Taverna 12 (consumíveis), Mercado 6 (3 varinhas + 3 mochilas). O topo
de `gameState.js` tem o comentário-resumo "LOCAIS DE VENDA" com todos os preços.
- Campos comuns: `id`, `nome`, `tipo`, `loja` (`'ferreiro'|'taverna'|'mercado'`),
  `preco`, `permitidoPara` (`['todos']` ou lista de heroKeys). Restrições de
  classe são **por item** (ex.: `cajado`→`['lewis','pedro']`, `instrumento`→
  `['henrique']`, `machado_grande`→`['victorCoiceBravo']`).
- Campos por `tipo`:
  - `arma`: `dano`, `atributo`, `escudo`, `arremesso`, `alcanceArremesso?`,
    `duasMaos`, `alcanceEspecial?{adjacente,diagonal,descricao}`; espada bastarda
    usa `modosDuasMaos:true` + `danoUmaMao`/`danoDuasMaos`.
  - `armaDistancia`: `dano`, `atributo`, `bonusDano`, `alcance`, `linhaVisao`,
    `slotSecundario` (`'livre'|'flechas'`), `duasMaos`.
  - `armadura`/`escudo`: `bonusCA` · `secundario` (tocha): `bonusVisao`, `duracao`
  - `consumivel`: `fome`, `sede` · `municao`: `quantidade`, `danoExtra?`,
    `tipoDano?`, `paraArmas[]`
  - `varinha`: `slotsMagia`, `magias[]`, `dano`, `atributo`, `slot?`,
    `permitidoPara:['lewis','pedro']` · `itemMagico`: `slotsExtras`, `slot:'magico'`
- `renderDescricaoItem(item)` (`game.js`) é um `switch(item.tipo)` cobrindo todos
  os tipos acima (inclui `alcanceEspecial`, `modosDuasMaos`, flechas/munição).

**Tooltip de item (`game.js`) — Regra Obrigatória.** **Todo elemento de item deve
ter tooltip aplicado via `aplicarTooltipAoItem(elemento, itemId)`** (loja,
inventário e HUD). Sistema global:
- Elemento único `#item-tooltip` (fixed, `z-index:999`, 240px, segue o cursor com
  margem e reposiciona para não sair da tela). Criado uma vez por `_initItemTooltip()`.
- `mostrarTooltip(itemId)` lê `GS.CATALOGO_ITENS[itemId]` (no-op se ausente),
  monta via `gerarConteudoTooltip(item)` e define a borda por raridade com
  `corBordaPorPreco(preco)`: ≥300 roxo `#cc44ff` (lendário) · ≥100 azul `#4a9eff`
  (raro) · ≥40 verde `#2ecc40` (incomum) · resto dourado `#c8a951` (comum).
- `esconderTooltip()` zera a opacidade. Eventos: `mouseenter`→mostrar,
  `mouseleave`→esconder.
- `gerarConteudoTooltip` → cabeçalho colorido por tipo (`coresTipo`), linhas via
  `renderLinhaTooltip(icone,label,valor)` (dano/atributo/CA/alcance/arremesso/
  fome/sede/duração/quantidade/slots…), bloco **HABILIDADE ESPECIAL**
  (`gerarHabilidadesEspeciais`: arremesso, chicote, lanças, alabarda, espada
  bastarda, incendiárias, tocha, varinhas, mochilas, duas-mãos), **PODE USAR**
  (mapeia `permitidoPara`→nomes) e **PREÇO**.
- Aplicado em: cada item da loja (overlay `abrirLoja`, via `data-item-id`), slots
  de equipamento e slots de inventário (`renderMyPanel`). NOTA: no HUD/inventário
  o tooltip só resolve quando o `id` do item (do servidor) existir em
  `CATALOGO_ITENS` — ids ainda divergem (ver nota de reconciliação).

**Loja reutilizável (overlay)** — `game.js` (toca o DOM; `gameState.js` é
DOM-free): `abrirLoja(nomeLocal, heroiAtivo)`, `renderDescricaoItem(item)`,
`comprarItem(itemId)`, `fecharLoja()`. Overlay `#loja-overlay` (fixed, `inset:0`,
`z-index:200`, fade 0.3s); cabeçalho mostra `💰 moedas` e ✕ FECHAR; lista filtra
`CATALOGO_ITENS` por `loja`. Botão por estado: **RESTRITO** (classe não permitida,
opacidade 0.4), **SEM OURO** (`moedas < preco`), **CHEIO** (inventário ≥ 6),
senão **COMPRAR**. Cor habilitada `#c8a951`; desabilitada `#4a4a4a`.
Handlers `onClicarFerreiro/Taverna/Mercado` → `abrirLoja(loja, GS.getHeroiAtivo())`.

**ESTADO DE INTEGRAÇÃO**: `comprarItem` agora é **autoritativo** — envia
`send({type:'shop_buy', shop, item_id})` ao servidor (resolve o shop via
`_resolverShopServidor`: `taverna`→`taverna`, `mercado`→`mercador`, `ferreiro`→
`ferreiro_weapon`/`ferreiro_armor` por tipo). `abrirLoja`/`fecharLoja` rastreiam
`window._lojaAtualAberta`. **Não muta mais** `getHeroiAtivo().inventario`.
⚠️ **BLOQUEADOR ABERTO — ids do catálogo não casam**: dos 49 itens de
`CATALOGO_ITENS`, só **3** existem nos catálogos do servidor (`chicote`,
`arco_curto`, `alabarda`); os outros **46 retornam "Item não encontrado"**
(ex.: `adaga`≠`dagger`, `espada_curta`≠`shortsword`, taverna `pao_duro`≠`meal`,
varinhas/mochilas inexistentes no servidor). Para a loja funcionar de verdade é
preciso **reconciliar os catálogos** (portar os itens do cliente para o
servidor, com tradução de schema). Além disso, o overlay ainda exibe
`moedas`/`inventario` do modelo client-side — precisa passar a ler `gold`/`bag`
do servidor para refletir as compras.

**Itens comprados → inventário → equipar ou ativar (`renderPurchasedItems` em
`game.js`).** As compras vão para `GS.getHeroiAtivo().inventario` (client-side, não
o `bag` do servidor). `renderMyPanel` renderiza, após o `bag` do servidor:
- **"Equipado (Loja)"** — slots `heroi.equipado`
  (`arma/armadura/cabeca/secundario/magico1/magico2`) com botão **✕ Remover**
  (`desequiparComprado` → `GS.desequiparItemComprado(slot)` devolve ao inventário).
- **"Comprados na Loja"** — `heroi.inventario`. **Consumíveis** → **▶ Usar**
  (`usarItemComprado` → `GS.aplicarConsumivel` recupera fome/sede, cap no `maximo`,
  atualiza as barras via `survivalChanged`). **Equipamentos** (arma/armadura/escudo/
  varinha/itemMagico) → **⚙ Equipar** (`equiparComprado` → `GS.equiparItemComprado`
  valida com `GS.podeEquipar` e move para `heroi.equipado`; munição não equipa).
- Todos os itens têm tooltip (`aplicarTooltipAoItem`).
- `GS.podeEquipar` trata `permitidoPara: ['todos']` como **curinga** (qualquer
  herói). Mapeamento tipo→slot: arma/armaDistancia→`arma`, armadura→`armadura`,
  escudo/secundario/varinha→`secundario`, itemMagico→`magico1`/`magico2`.
- ⚠️ **Client-side, não-autoritativo**: equipar aqui altera `heroi.equipado` mas
  **ainda não afeta o combate do servidor** (dano/CA usam `p["weapon"]`/`gear` do
  servidor). Consumíveis (fome/sede) são totalmente client-side e funcionam.

**Vínculo cidade → loja (`_cityClick` em `game.js`).** Clicar nos edifícios
**Ferreiro / Taverna / Mercado** abre o **overlay client-side `abrirLoja`** via
`MAPA_IDS_LOJA`, que traduz o id do mesh 3D `mercador`→`mercado` (sem alterar os
ids dos meshes). **Templo** e quaisquer ids não mapeados caem no `openShop`
**autoritativo do servidor** (Templo não existe em `CATALOGO_ITENS`). `dungeon`→
`triggerDungeonEntrance`; `guilda`→toast. ⚠️ Consequência: compras em
Ferreiro/Taverna/Mercado passam pelo overlay **não-autoritativo** (mutam o herói
client-side `GS.getHeroiAtivo()`) e não afetam `gold`/equipamento do servidor até
`comprarItem` ser religado a `shop_buy`.

### Adaga — Mão Secundária, Dual-Wield e Arremesso (servidor) — Regra Obrigatória

Mecânica de combate **autoritativa no servidor** (`server.py`). A adaga pode ser
equipada na **mão principal** (`gear.weapon` / `p["weapon"]`) ou na **mão
secundária** (`gear.off_hand`, no lugar do escudo).

- **Ataque de mão secundária (dual-wield)**: se a `off_hand` é arma (tem `die`),
  o ataque normal (`handle_attack`) dispara um **ataque extra** que **custa a
  ação bônus do turno** (`bonus_action_used` + −1 fome/−1 sede). Sem modificador
  de atributo no dano. Se a ação bônus já foi usada, não há ataque extra.
- **Arremesso** (`handle_throw`, mensagem `{type:'throw', target_id}`):
  - Detecta adaga arremessável (tem `throw_range`+`die`) na mão principal
    (via `p["weapon"]`) ou secundária. Alcance **3** (Chebyshev).
  - Ataque por **Destreza** (rola d20+atk; dano = `die` + **mod. DES**, ×2 em
    crítico nat-20).
  - A adaga **sai do equipamento** (mão principal → `unarmed`).
  - **1 natural** = adaga **perdida para sempre** (nenhum drop).
  - Qualquer outro resultado (acerto ou erro) = a adaga **cai no chão ao lado do
    monstro** como **baú recuperável** (`_spawn_chest` em tile livre adjacente,
    via `_free_tile_near`), recuperável pelo sistema de baús existente.
  - **Custo de ação**: `handle_throw` é o controlador; a lógica de execução está
    em **`_executar_arremesso`** (acerto/dano/destruição, inalterada, retorna
    True/False). Se o jogador **ainda não agiu** → arremesso é **ação principal**
    (`action_done=True`, consome `_consumir_recursos(p,'apenas_acao')`). Se **já
    usou a ação principal** → vira **ação bônus** (checa/marca `bonus_action_used`,
    consome `'acao_bonus'`). Em falha de validação, **nada é consumido**.
- **UI** (`game.js`, `renderMyPanel`): botão **🎯 Arremessar Adaga** aparece
  quando há adaga equipada (`me.weapon.throw_range` ou `me.gear.off_hand.
  throw_range`) e há monstro no alcance; `beginThrow()` envia `throw` (modal de
  alvo se houver mais de um).
- **ESTADO**: funciona para adagas que são **itens do servidor** (equipamento
  inicial de Luccas/Henrique). Para adagas **compradas na loja** terem a
  mecânica, falta a **consolidação loja→servidor** (Stage 2 — compras no `bag`
  autoritativo, equipáveis no servidor).

#### Adaga baseada em Destreza + Adaga Secundária (slot secundário)

Regras de catálogo/atributo (`CATALOGO_ITENS` em `src/gameState.js`):

- **Adaga** (`adaga`): atributo **Destreza** para **acerto E dano**
  (`atributo:'destreza'`, `bonusAtaque:'destreza'`, `bonusDano:'destreza'`;
  era `forcaOuDestreza`). Mantém `escudo`, `arremesso` (alcance 3).
- **Adaga Secundária** (`adaga_secundaria`): `tipo:'secundario'` (ocupa o slot
  secundário/escudo), `usoAcaoBonus:true`, **só ataque/arremesso como ação
  bônus**, 1d4 + DES. **Apenas Victor, Luccas e Henrique** podem equipar
  (`permitidoPara:['victorCoiceBravo','luccas','henrique']`).
- **Richard, Lewis e Pedro NÃO** podem usar adaga no slot secundário (usam
  escudo/grimório/varinhas — ver `SECUNDARIO_PERMITIDO`).
- **Tooltip** (`gerarHabilidadesEspeciais`, `game.js`): `adaga_secundaria` exibe
  Ataque Bônus, Arremesso Bônus e o aviso de incompatibilidade com duas mãos +
  restrição de personagens. **REAL/ativo.** (Obs.: como o item tem `arremesso`,
  o tooltip também mostra a linha genérica de Arremesso.)
- ⚠️ **ESTADO — scaffolding no servidor**: a validação de slot
  (`SECUNDARIO_PERMITIDO`/`handle_equip`), o cálculo `_calcular_ataque_adaga` e
  os handlers de ação bônus (`handle_ataque_adaga_secundaria`,
  `handle_arremesso_adaga_secundaria`) foram inseridos em `server.py` **verbatim
  da especificação, mas AINDA NÃO estão roteados nem integrados**: usam o modelo
  do cliente (chave de herói, slot `secundario`, `stats_mod`, `_get_bonus_atributo`,
  `_aplicar_dano`, `_distancia`, `_posicao_adjacente_ao_alvo`) que **não existe**
  no servidor (que usa `class_id`, `off_hand`, `p["dex"]`, `mod()`, `target["ac"]`,
  `_free_tile_near`). Idem `renderBotoesAcaoBonus` no cliente (não chamado por
  `renderMyPanel`). **Só o catálogo (cliente) e o tooltip estão ativos**; o resto
  aguarda a camada de integração + reconciliação catálogo↔servidor.

#### Highlight de Alcance do Arremesso (3D) — REAL/ativo

Modo de mira no tabuleiro 3D para arremessar a adaga secundária (`game.js`,
adaptado à infra real: `g3.scene`/`g3.T`, `casaParaMundo`, `get3DTile`,
`GS.gameState.tiles`/`monsters`). Disparado pelo botão **🎯 Mirar no Tabuleiro**
(aparece quando `me.gear.off_hand.throw_range`), via
`iniciarModoArremessoAdagaSecundaria()`.

- **Tiles de alcance**: `calcularTilesArremessoAdaga(pos, raio=3)` — Chebyshev ≤3,
  **somente linha reta ou diagonal perfeita**, com **linha de visão** (sem paredes
  no caminho, `temLinhaDeVisaoArremesso`).
- **Highlight**: planos sobre o piso — **laranja (`0xffaa00`, opacidade 0.30)**
  para tiles válidos, **vermelho (`0xff2222`, opacidade 0.55)** para tiles com
  inimigo. Pulso de opacidade contínuo (`_animarHighlightArremesso`).
- **Hover**: o tile sob o mouse é levemente escalado/elevado e desenha uma
  **linha tracejada amarela** (`LineDashedMaterial 0xffaa00`) do herói ao alvo.
- **Cursor**: muda para **`crosshair`** durante o modo arremesso.
- **ESC**: cancela o modo (`limparHighlightArremesso`, remove highlight, legenda,
  trajetória e restaura o cursor).
- **Legenda**: rodapé central explicando as cores e o ESC.
- **Execução**: clique num tile **com inimigo** envia a mensagem **real `throw`**
  (`{type:'throw', target_id}`) — tratada por `handle_throw`, que vira **ação
  bônus** se o jogador já tiver agido. (A mensagem `bonus_action` da spec não
  existe no servidor e não é usada.) Cliques inválidos mantêm o modo ativo p/
  nova tentativa; arremesso bem-sucedido sai do modo.
- **Integração**: roteado em `on3DClick`/`on3DMouseMove` quando
  `window._modoArremessoAtivo`. **Requer visão 3D** (`g3`); no 2D o botão avisa.

#### Highlight de Arremesso — Adaga Principal (mão de arma) — REAL/ativo

Sistema separado (`_highlightArremessoPrincipal`) com as **mesmas regras de
alcance/LOS** (`calcularTilesArremessoAdaga`) e hover compartilhado
(`_processarHoverArremesso`), porém **cor AZUL** para diferenciar da secundária.
Botão **🎯 Mirar (mão princ.)** em `renderMyPanel` (quando `me.weapon.throw_range`)
→ `iniciarModoArremessoAdagaPrincipal()`.

- **Cores dos highlights** (referência — sumário completo):
  - Adaga **principal**: **azul `#4488ff`** — ação principal OU bônus.
  - Adaga **secundária**: **laranja `#ffaa00`** — sempre ação bônus.
  - **Lança curta**: **verde `#44cc44`** — ação principal OU bônus.
  - Inimigo no tile: **vermelho `#ff2222`** — todos os sistemas.
  - Linha de trajetória: **amarelo `#ffaa00`** — todos os sistemas.
  - **ESC cancela qualquer modo** de arremesso ativo; os três modos são
    mutuamente exclusivos (`_modoArremessoLanca` / `_modoArremessoPrincipal` /
    `_modoArremessoAtivo`).

#### Lança Curta — Arremesso (verde) e cálculo por Força

- **Tooltip** (`gerarHabilidadesEspeciais`, `lanca_curta`): **REAL/ativo** — bloco
  custom com Arremesso (🏹 **Força**, 1d6+FOR), Alcance Lateral e o aviso de slot
  vazio pós-arremesso. A linha genérica de arremesso (que dizia "Destreza", errado
  p/ lança) passou a **excluir** `lanca_curta`.
- **Highlight verde** (`_highlightArremessoLanca`, `iniciarModoArremessoLanca`):
  client adaptado e roteado, mas ⚠️ **DORMENTE** — nenhum personagem equipa
  `lanca_curta` (o servidor só tem `lanca` range-2 **sem `throw_range`**); o botão
  **🏹 Arremessar Lança** só aparece quando `me.weapon.id === 'lanca_curta'`.
- **Servidor** (`_calcular_ataque_lanca_arremesso`, `handle_arremesso_lanca`):
  **scaffolding verbatim**, não roteado, com helpers inexistentes. Quando ligado,
  o `throw` real usa **Destreza** p/ todo arremesso — o cálculo por **Força** daqui
  é a regra pretendida da lança, ainda desconectada.
- **Principal vs bônus**: a legenda mostra **AÇÃO PRINCIPAL** (se `!me.action_done`)
  ou **AÇÃO BÔNUS** (se já agiu). A decisão real é do servidor: `handle_throw`
  usa ação principal se `!action_done`, senão ação bônus.
- **ESC** cancela **qualquer** modo de arremesso ativo (principal ou secundário);
  os modos são **mutuamente exclusivos** (cada `iniciar…` recusa se o outro está
  ativo). Roteamento em `on3DClick`/`on3DMouseMove` checa
  `_modoArremessoPrincipal` antes de `_modoArremessoAtivo`.
- ⚠️ **Limitação do servidor**: a mensagem `throw` **não carrega o slot** —
  `_executar_arremesso` varre `("weapon","off_hand")` e arremessa a **primeira**
  adaga arremessável. Logo, com adaga na mão principal, é sempre **ela** que voa
  (o modo secundário só arremessa a off_hand quando a mão principal não é
  arremessável, ex.: bardo com instrumento). A distinção visual principal/secundária
  é fiel ao **slot que será lançado** apenas quando os slots diferem nesse sentido.

### Sistema de Fome e Sede (Sobrevivência) — Regra Obrigatória

Sistema de sobrevivência client-side implementado em `src/gameState.js`
(lógica pura, sem DOM). Escala **0–100**, distinto e independente do campo
legado `fome`/`sede` 0–10 do servidor (`server.py`, consumido em ações bônus —
ver seção "Ação Bônus"). O estado vive no mapa `survival` (pid → herói) dentro
de GS, **não** em `gameState.players`, para não colidir com o mirror
autoritativo do servidor (que reescreveria os valores a cada `game_state`).

**Configuração (`SOBREVIVENCIA_CONFIG`)**
- `maximo: 100`
- `inicioAventura: 80` — fome/sede iniciais ao começar a aventura (`game_start`)
- `inicioPosTaverna: 100` — fome/sede iniciais ao entrar em dungeon vindo da
  cidade/taverna (`enter_dungeon`)

**Thresholds (faixa → modificador)**

| Estado            | Faixa     | Modificador |
|-------------------|-----------|-------------|
| Saciado           | 91–100    | +1          |
| Neutro            | 20–90     |  0          |
| Pressão Leve      | 11–19     | −1          |
| Pressão Moderada  | 6–10      | −2          |
| Pressão Grave     | 1–5       | −3          |
| Colapso           | 0         |  0          |

**Modificador final combinado (`getModificadorFinal`)** — combina os
thresholds de fome e sede:
- Ambos ≥ 0 (neutro/positivo): usa o **maior** dos dois (`Math.max`)
- Apenas um negativo: usa o valor **individual** do negativo
- Ambos negativos: usa o **pior** dos dois e aplica **−1 extra** (`min − 1`)

**Consumo por tipo de ação (fome / sede)** — categorias são **mutuamente
exclusivas por turno**; o consumo é resolvido **uma vez por turno** em
`endTurn()` (não por tile de movimento):

| Tipo de ação                 | Fome | Sede |
|------------------------------|------|------|
| `apenasMovimento`            | 0    | 1    |
| `apenasAcao`                 | 0    | 1    |
| `movimentoMaisAcao`          | 1    | 1    |
| `habilidadeEspecialSemMover` | 1    | 2    |
| `habilidadeEspecialComMover` | 2    | 3    |
| `acaoBonus`                  | 1    | 1    |
| `receberDano`                | 0    | 1    |
| `descansarTurno`             | 1    | 0    |

> **Magias consomem igual a ataques** (marcam a flag `acted` do turno).

**Colapso e morte (`morteConfig`)**
- Colapso total quando fome **e** sede chegam a 0 simultaneamente
  (`emColapsoTotal = true`, reseta `contadorMorte`)
- A cada turno em colapso (`processarColapsoTotal`, chamado no início do turno
  do herói): `contadorMorte += 1` e `modificadorTemporario = −5 × contadorMorte`
- **Morte permanente** ao atingir `turnosParaMorte: 10` turnos em colapso
  (`morto = true`, `causaMorte = 'fome e sede'`)
- Recuperação: se fome **ou** sede voltar a > 0 antes da morte, sai do colapso
  (`emColapsoTotal = false`, `contadorMorte = 0`)

**Integração (gameState.js → renderer)**
- Movimento: `GS.move()` marca `moved`; ataque/magia: `GS.notifyAttack()` marca
  `acted`; habilidade especial: `GS.notifySkill()` marca `special`
- Ação bônus e dano recebido: `GS.notifyBonusAction()` / `GS.notifyDamageTaken()`
  (consumo imediato, expostos para wiring futuro)
- Inicialização: `game_start` → 80; `enter_dungeon` → 100
- Logs saem via evento `survivalLog` (`adicionarLog`) — o renderer registra
  `GS.on('survivalLog', fn)` e escreve no painel do GM, mantendo `gameState.js`
  livre de DOM
- API pública: `GS.SOBREVIVENCIA_CONFIG`, `GS.getSurvival(pid)`,
  `GS.survivalModifier(pid)`, `GS.getModificadorFinal`, `GS.getThreshold`,
  `GS.consumirRecursos`, `GS.processarColapsoTotal`, `GS.survival`

**Barras visuais de Fome e Sede — sempre visíveis (Regra Obrigatória)**
- As barras de fome e sede ficam **sempre visíveis no HUD inferior**, dentro do
  mini-card de cada herói (`.pcard` em `#player-cards`), logo abaixo das barras
  de HP e MP. **Nunca** devem ser ocultadas durante o jogo.
- Renderizadas por `renderBarrasSobrevivencia(heroi)` em `game.js`, dentro de
  `<div class="survival-bars">`, e atualizadas em `renderPlayers()` a cada
  `game_state` e a cada evento `survivalChanged` (consumo/colapso em tempo real).
- Barra: altura 5px, trilho `#1a1a1a` borda `#2a2a2a`, largura = `valor/100`,
  `transition: width/background 0.5s ease`. Rótulo `'Cinzel'` 9px, label
  `#8a7a5a`, valor + nome do threshold na cor da barra.
- Cores da barra (`corBarra(pct)`): `>90` dourado `#f0c040` · `>19` cinza
  `#a0a0a0` · `>10` laranja `#ff851b` · `>5` laranja escuro `#ff4500` · resto
  vermelho `#ff1111`.
- Aviso de **colapso total**: faixa vermelha pulsante (`animation: piscar 1s
  infinite`) "⚠️ COLAPSO — N TURNOS", onde N = `turnosParaMorte − contadorMorte`.
- **Vinheta de pressão** (`#vinheta-sobrevivencia`, fixed, `inset:0`,
  `pointer-events:none`, `z-index:50`, sobre o canvas), via
  `atualizarEfeitosVisuais(heroLocal)`, baseada no pior estado
  `min(fome, sede)`: `≤5` vermelha pulsante (`inset 0 0 80px rgba(255,17,17,.4)`
  + `piscar 1.5s`) · `≤10` laranja fixa (`inset 0 0 60px rgba(255,69,0,.3)`) ·
  `≤19` sutil (`inset 0 0 40px rgba(255,133,27,.15)`) · acima: sem efeito.
- CSS global: `@keyframes piscar { 0%,100%{opacity:1} 50%{opacity:.3} }`.

### Movimento Animado do Peão (3D) — Regra Obrigatória
Em modo 3D, o peão do jogador local **anda casa por casa** seguindo o caminho do
pathfinding, com animação de levantar/avançar/pousar (`game.js`).
- Estado: **`estadoMovimento`** (`emMovimento`, `filaCaminho`, `peaoAtivo`,
  `onConclucao`); **`podeReceberInput()`** bloqueia clique enquanto anima.
- `moverPeaoAoCaminho(peao, heroi, caminho, onConclucao)` → fila →
  `_executarProximoPasso` → `_animarPasso` (3 fases: 0–0.3 levanta `easeOut`;
  0.3–0.7 avança `easeInOut`; 0.7–1 pousa `easeIn` + squash de impacto + som
  `tocarSomPasso`). `DURACAO_PASSO_MS=250`, `ALTURA_ELEVACAO=0.4`.
- **Som do passo (`tocarSomPasso`)**: Web Audio puro (sem arquivos), peão de
  plástico oco na madeira — 3 camadas (bandpass ~280Hz do plástico + sine
  140→80Hz da madeira + clique highpass 2400Hz) com variação aleatória, todas
  via um `DynamicsCompressor` (threshold −18, ratio 6). **Reusa o
  `getAudioContext()` existente** (não cria 2º contexto); no-op se o contexto
  não estiver `running`.
- **Câmera segue o peão** (`configCamera`, `atualizarCamera`,
  `iniciar/encerrarSeguimentoCamera`): durante o movimento a câmera desliza com
  **lerp `0.08`** acompanhando a base do peão (y=0, não o pulo), **preservando o
  ângulo isométrico** (captura/translada o offset câmera→alvo — não usa offset
  fixo, pois a câmera é ortográfica). **OrbitControls é desativado durante o
  movimento** (e seu `update()` pausado) e **re-sincronizado** ao final
  (`controls.target` no peão + `controls.update()` → sem cortes). O peão em
  movimento é **excluído** do y-lift de hover/seleção do loop de render.
  `atualizarCamera()` é chamado a cada frame em `startLoop3D`.
- **Integração** (`handleTileClick`, caso `move`): **anima localmente primeiro;
  ao concluir, envia os passos ao servidor** (`GS.move` por passo). Durante a
  animação não chega `game_state`, então o mesh do peão persiste; `renderMap3D`
  também é guardado por `if(estadoMovimento.emMovimento) return`. Em 2D (ou sem
  peão 3D), o movimento é instantâneo (comportamento anterior).
- Coordenadas: `casaParaMundo(x,z) = {x, y:0, z}` (tile == world, 1 unid/casa).
  Peões taggeados com `userData.pid`; `getPeaoMesh(pid)` busca no `g3.entityGroup`.
- **Consumo de fome/sede do movimento NÃO é feito no cliente** (a spec sugeria
  `GS.consumirRecursos` por casa) — isso re-divergiria do sistema unificado e
  tem assinatura incompatível. O consumo é autoritativo no servidor
  (`_consumir_recursos`); o consumo por movimento ainda não está wired (pendente).

#### Sistema de Venenos — REAL/ativo (cliente + servidor)

Venenos são consumíveis comprados no **mercado** (`loja:'mercado'`,
`tipo:'veneno'`, 1 slot de inventário). Usar = **unta a arma equipada** (ação
bônus); o próximo golpe certeiro **transfere o veneno** ao alvo, que faz **save
de Fortitude** (`d20 + bônus` vs dificuldade) para resistir.

- **Catálogo cliente** (`CATALOGO_ITENS`, `src/gameState.js`): 5 venenos —
  `veneno_aranha_sombria` (🕷️ 8💰), `veneno_escorpiao_pedra` (🦂 12💰),
  `veneno_cobra_cuspidora` (🐍 16💰), `veneno_basilisco` (🦎 20💰),
  `veneno_polvo_abissal` (🐙 15💰). Cada um tem bloco `efeito` (atributo,
  operação, duração, save, dificuldade, anula).
- **Catálogo servidor** (`VENENOS`, `server.py`): espelho autoritativo, adaptado
  ao modelo real (scores `str_`/`con_`, saves precomputados `fort`/`ref_`/`will`,
  `gm_say`). Os 5 venenos também entram em `SHOP_MERCHANT` com
  `effect:'coat_poison'` + `veneno_id` → comprados para o `bag` autoritativo.
- **Aplicação** (`server.py`):
  - `handle_use_item` (`effect=='coat_poison'`, ação bônus): seta
    `p['weapon_poison']` + `p['weapon_poison_hits']=VENENO_CARGAS` (3).
  - `handle_attack`: em **golpe certeiro** chama `_aplicar_veneno(alvo, vid)` e
    consome 1 carga (zera a untada ao acabar).
  - `_aplicar_veneno` é genérico (jogador OU monstro). **Mortos-vivos/constructos
    são imunes.** Save por Fortitude; `anula:True` resiste por completo no
    sucesso, `anula:False` aplica efeito **parcial** no sucesso.
- **Efeitos e processamento por rodada** (`_processar_venenos_turno`, chamado no
  início do turno de cada jogador em `handle_end_turn` e de cada monstro em
  `gm_phase`):
  - `reduzir` (FOR/CON): jogador perde score real; **CON recalcula `max_hp` e
    `fort`** via `get_bonus_constituicao`×nível; monstro traduz FOR→penalidade de
    dano, CON→perda de `max_hp`. Revertido na expiração.
  - `penalidade` (ataque/movimento): em `alvo['penalidades']` (valores assinados).
    `ataque` entra no `eff_atk` (jogador e monstro); `movimento` em `_moves_base`.
  - `petrificado` (flag + `petrificado_rodadas`): perde o turno — guarda em
    `handle_attack`/`handle_move` (jogador) e `gm_phase` (monstro).
  - `cego` (flag + `cego_rodadas`): -4 em ataques (`penalidades['ataque']`) e
    **bloqueia ataques à distância** (`bloqueia_distancia`).
- **Tooltip** (`gerarHabilidadesEspeciais`, `game.js`): `item.tipo==='veneno'`
  exibe Efeito, Save (Fortitude + dificuldade, anula/parcial) e Aplicação.
- **IDs casam** cliente↔servidor (`veneno_*`), então o tooltip do `CATALOGO_ITENS`
  funciona sobre os itens da loja do mercador do servidor.

#### Sistema de Armadilhas colocáveis — REAL/ativo (cliente + servidor) — Passo 2
Distinto das `traps` de masmorra. Criadas pelo Luccas (`class_id 'rogue'`) na
própria casa ou cardinalmente adjacente (ação principal; custo ouro + 🍖2/💧1).
- **Catálogo servidor** (`ARMADILHAS`, `server.py`): 8 tipos — `buraco` (🕳️),
  `armadilha_urso` (🪤), `fosso_estacas` (⛏️), `rede` (🕸️), `armadilha_incendiaria`
  (🔥), `mina_terrestre` (💣), `fosso_envenenado` (☠️), `nuvem_gas` (🌫️).
- **Estado** `game_state.armadilhas`: `id`, `tipo`, `pos`, `icone`, `nome`,
  `visivel`, `ativada`, `aliada`, `so_luccas`.
- **Render 2D** (`renderMap`, `game.js`): retângulo + ícone na casa; borda
  **verde** = armadilha de aliado, **vermelha** = já ativada, laranja = neutra.
- **Render 3D** (`renderMap3D` → `_armadilhaSprite3D`): sprite de emoji sobre o
  tile (opacity 0.6 se `so_luccas`; tint vermelho se `ativada`).
- **Senders** (`src/gameState.js`): `GS.criarArmadilha(tipo,tx,ty,venenoId)`,
  `GS.desarmarArmadilha()`, `GS.armadilhaAdjacente()` (decisor puro).
- A UI de criar/desarmar (botões do Luccas) entra no **Passo 3** (habilidades).

### REGRA PRINCIPAL
Nunca altere valores deste arquivo sem instrução explícita.
Ao fazer qualquer mudança no projeto, preserve todos os valores acima.
