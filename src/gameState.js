'use strict';
// gameState.js — Legends for Hire
//
// Pure game-logic module: ZERO DOM / canvas / pixel references.
// All mutable state, WebSocket layer, BFS helpers and action senders live here.
//
// The renderer (index.html) reads from GS.* and registers event callbacks via
// GS.on(eventName, fn).  It never touches WebSocket directly and never sets
// state variables except through GS setters or GS action methods.

const GS = (() => {
  'use strict';

  // ── Internal constants ─────────────────────────────────────────────────────
  const TILE_WALL  = 0;
  const TILE_FLOOR = 1;
  const TILE_DOOR  = 2;   // porta de sala (transponível só quando aberta)

  // Espelha server.MATERIAIS (campos solido/oclui). Mantido mínimo de propósito:
  // só ids com efeito precisam constar. Atualize junto com o catálogo do servidor.
  const MATERIAIS_SOLIDOS = new Set(['entulho']);
  const MATERIAIS_OPACOS  = new Set(['entulho']);

  // Prévia do editor (index.html?preview=1): a página roda dentro de um iframe,
  // sem servidor e sem lobby — o estado chega por postMessage e nada sai daqui.
  const PREVIEW = typeof location !== 'undefined' && /[?&]preview=1/.test(location.search);

  // ── Internal state ─────────────────────────────────────────────────────────
  let ws              = null;
  let myPid           = null;
  let myName          = '';
  let account   = null;   // apelido logado (ou null)
  let savegames = [];     // último savegames_list recebido
  let campaignsCache = []; // último campaigns recebido junto do savegames_list
  let gameState       = null;   // latest game_state message from server
  let lobbyState      = null;   // latest lobby_state message from server
  let cityState       = null;   // latest city_state message from server
  let pendingAction   = null;   // reserved for future use
  let pendingMove     = null;   // movimento selecionado, ainda não confirmado
  let pendingSkill    = null;   // skill waiting for map-click target
  let pendingInstrumento = null; // instrumento aguardando alvo no mapa: {id, base, alcance}
  let pendingThrow    = null;   // arremessável aguardando alvo no mapa: {id, alcance}
  let warriorSelected = [];     // warrior: ids de habilidades ARMADAS (toggle) —
                                // custo de fome/sede cobrado só na ação (ataque)
  let isMyTurn        = false;
  let activeShop      = null;   // id of the shop currently open in city UI
  let activeScene     = null;   // id da cena aberta no modal (null = nenhuma)
  let shopTabIdx      = 0;      // active tab index inside shop modal
  let pendingShopOpen = null;   // shop to open once city_state first arrives
  let guildCatalogCache = [];   // catálogo da Guilda (vem em city_state; cacheado p/ uso na masmorra)
  let instrumentoBaseCache = null;   // INSTRUMENTOS_BASE, cacheado no game_start

  // ── Event callbacks (set by renderer) ─────────────────────────────────────
  const _handlers = {};
  function on(ev, fn)           { _handlers[ev] = fn; }
  function _emit(ev, ...args)   { const h = _handlers[ev]; if (h) h(...args); }

  // ═══════════════════════════════════════════════════════════════════════════
  // SISTEMA DE FOME E SEDE (Sobrevivência)
  // ───────────────────────────────────────────────────────────────────────────
  // Lógica client-side pura (sem DOM). Escala 0–100, independente do antigo
  // campo fome/sede 0–10 do servidor. O estado vive em `survival` (pid → herói),
  // NÃO em gameState.players, para não colidir com o mirror autoritativo do
  // servidor (que reescreveria os valores a cada game_state).
  //
  // Logs saem via evento 'survivalLog' (adicionarLog) — o renderer registra
  // GS.on('survivalLog', fn) e escreve no painel de log, mantendo este módulo
  // livre de DOM conforme as regras de arquitetura.
  // ═══════════════════════════════════════════════════════════════════════════

  const SOBREVIVENCIA_CONFIG = {
    maximo: 100,
    inicioAventura: 80,
    inicioPosTaverna: 100,

    thresholds: [
      { id: 'saciado',  nome: 'Saciado',          min: 91,  max: 100, modificador:  1 },
      { id: 'neutro',   nome: 'Neutro',           min: 20,  max: 90,  modificador:  0 },
      { id: 'leve',     nome: 'Pressão Leve',     min: 11,  max: 19,  modificador: -1 },
      { id: 'moderada', nome: 'Pressão Moderada', min: 6,   max: 10,  modificador: -2 },
      { id: 'grave',    nome: 'Pressão Grave',    min: 1,   max: 5,   modificador: -3 },
      { id: 'colapso',  nome: 'Colapso',          min: 0,   max: 0,   modificador:  0 }
    ],

    consumo: {
      apenasMovimento:              { fome: 0,  sede: 1 },
      apenasAcao:                   { fome: 0,  sede: 1 },
      movimentoMaisAcao:            { fome: 1,  sede: 1 },
      habilidadeEspecialSemMover:   { fome: 1,  sede: 2 },
      habilidadeEspecialComMover:   { fome: 2,  sede: 3 },
      acaoBonus:                    { fome: 1,  sede: 1 },
      receberDano:                  { fome: 0,  sede: 1 },
      descansarTurno:               { fome: 1,  sede: 0 }
    },

    morteConfig: {
      turnosParaMorte: 10,
      penaltiesPorTurno: -5
    }
  };

  // pid → herói de sobrevivência { name, fome, sede, contadorMorte,
  //                                emColapsoTotal, modificadorTemporario,
  //                                morto, causaMorte }
  let survival = {};

  // adicionarLog — wrapper DOM-free: emite evento para o renderer logar.
  function adicionarLog(text) { _emit('survivalLog', text); }

  function inicializarSobrevivencia(heroi, veioTaverna = false) {
    const inicio = veioTaverna
      ? SOBREVIVENCIA_CONFIG.inicioPosTaverna
      : SOBREVIVENCIA_CONFIG.inicioAventura;

    heroi.fome = inicio;
    heroi.sede = inicio;
    heroi.contadorMorte = 0;
    heroi.emColapsoTotal = false;

    return heroi;
  }

  function consumirRecursos(heroi, tipoAcao) {
    const custo = SOBREVIVENCIA_CONFIG.consumo[tipoAcao];
    if (!custo) return heroi;

    const fomeAnterior = heroi.fome;
    const sedeAnterior = heroi.sede;

    heroi.fome = Math.max(0, heroi.fome - custo.fome);
    heroi.sede = Math.max(0, heroi.sede - custo.sede);

    // Log apenas se houve mudança
    if (heroi.fome !== fomeAnterior || heroi.sede !== sedeAnterior) {
      adicionarLog(
        `🍖 ${heroi.name} — ` +
        `Fome: ${fomeAnterior}→${heroi.fome} | ` +
        `Sede: ${sedeAnterior}→${heroi.sede}`
      );
    }

    return verificarEstadoSobrevivencia(heroi);
  }

  function getThreshold(valor) {
    return SOBREVIVENCIA_CONFIG.thresholds.find(
      t => valor >= t.min && valor <= t.max
    );
  }

  function getModificadorFinal(heroi) {
    const thresholdFome = getThreshold(heroi.fome);
    const thresholdSede = getThreshold(heroi.sede);

    const modFome = thresholdFome.modificador;
    const modSede = thresholdSede.modificador;

    // Ambos neutros ou positivos: soma normalmente
    if (modFome >= 0 && modSede >= 0) {
      return Math.max(modFome, modSede);
    }

    // Apenas um negativo: usa o individual
    if (modFome >= 0) return modSede;
    if (modSede >= 0) return modFome;

    // Ambos negativos: pior dos dois -1 extra
    return Math.min(modFome, modSede) - 1;
  }

  function verificarEstadoSobrevivencia(heroi) {
    const thresholdFome = getThreshold(heroi.fome);
    const thresholdSede = getThreshold(heroi.sede);

    // Colapso total — ambos em zero
    if (heroi.fome === 0 && heroi.sede === 0) {
      if (!heroi.emColapsoTotal) {
        heroi.emColapsoTotal = true;
        heroi.contadorMorte = 0;
        adicionarLog(`💀 ${heroi.name} entrou em colapso total!`);
        adicionarLog(_t('ui.sobrevivencia.aviso_colapso',
          `⚠️ Recupere fome ou sede em ${SOBREVIVENCIA_CONFIG.morteConfig.turnosParaMorte} turnos ou morrerá!`,
          { n: SOBREVIVENCIA_CONFIG.morteConfig.turnosParaMorte }));
      }
      return heroi;
    }

    // Recuperação do colapso total
    if (heroi.emColapsoTotal && (heroi.fome > 0 || heroi.sede > 0)) {
      heroi.emColapsoTotal = false;
      heroi.contadorMorte = 0;
      adicionarLog(`✅ ${heroi.name} se recuperou do colapso!`);
    }

    // Log de mudança de estado
    const estadoAtual = getModificadorFinal(heroi);
    if (estadoAtual < 0) {
      adicionarLog(
        `⚠️ ${heroi.name}: ` +
        `${_t('ui.sobrevivencia.fome', 'Fome')} ${_estadoNome(thresholdFome)} | ` +
        `${_t('ui.sobrevivencia.sede', 'Sede')} ${_estadoNome(thresholdSede)} | ` +
        `${_t('ui.sobrevivencia.modificador', 'Modificador')}: ${estadoAtual}`
      );
    }

    return heroi;
  }

  function processarColapsoTotal(heroi) {
    if (!heroi.emColapsoTotal) return heroi;

    heroi.contadorMorte += 1;
    const turnosRestantes =
      SOBREVIVENCIA_CONFIG.morteConfig.turnosParaMorte - heroi.contadorMorte;

    // Penalidade crescente
    heroi.modificadorTemporario =
      SOBREVIVENCIA_CONFIG.morteConfig.penaltiesPorTurno * heroi.contadorMorte;

    adicionarLog(
      `💀 ${heroi.name} em colapso — ` +
      `${turnosRestantes} turnos para morte permanente`
    );

    // Morte permanente
    if (heroi.contadorMorte >= SOBREVIVENCIA_CONFIG.morteConfig.turnosParaMorte) {
      heroi.morto = true;
      heroi.causaMorte = 'fome e sede';
      adicionarLog(`💀 ${heroi.name} morreu de fome e sede!`);
    }

    return heroi;
  }

  // ── Helpers de integração (resolvem o herói de sobrevivência de um pid) ─────

  // Garante/retorna o registro de sobrevivência do pid, criando-o se preciso.
  function _ensureSurvival(pid, veioTaverna = false) {
    if (!pid) return null;
    if (!survival[pid]) {
      const pl = (gameState?.players || cityState?.players || lobbyState?.players || [])
                   .find(p => p.id === pid);
      const h = { name: pl?.name || 'Herói', modificadorTemporario: 0, morto: false };
      inicializarSobrevivencia(h, veioTaverna);
      survival[pid] = h;
    }
    return survival[pid];
  }

  // (Re)inicializa o registro de sobrevivência de TODOS os jogadores conhecidos.
  // veioTaverna=false → início da aventura (80); true → pós-taverna/cidade (100).
  function _resetSurvivalAll(veioTaverna) {
    const players = gameState?.players || cityState?.players || lobbyState?.players || [];
    for (const pl of players) {
      const h = survival[pl.id] || { modificadorTemporario: 0, morto: false };
      h.name = pl.name || h.name || 'Herói';
      inicializarSobrevivencia(h, veioTaverna);
      survival[pl.id] = h;
    }
  }

  // Aplica consumo ao herói de sobrevivência do jogador local.
  function _consumeMine(tipoAcao) {
    const h = _ensureSurvival(myPid);
    if (h && !h.morto) {
      consumirRecursos(h, tipoAcao);
      _emit('survivalChanged', myPid);   // renderer atualiza barras/vinheta
    }
    return h;
  }

  // ── Atividade do turno (categorias são mutuamente exclusivas por turno) ─────
  // As funções de movimento/ataque/habilidade marcam flags aqui; o consumo
  // único do turno é resolvido em endTurn() escolhendo a categoria correta.
  let _turn = { moved: false, acted: false, special: false };
  function _resetTurnActivity() { _turn = { moved: false, acted: false, special: false }; }

  // Resolve a categoria de consumo do turno a partir das flags acumuladas.
  function _tipoAcaoDoTurno() {
    const t = _turn;
    if (t.special)               return t.moved ? 'habilidadeEspecialComMover' : 'habilidadeEspecialSemMover';
    if (t.moved && t.acted)      return 'movimentoMaisAcao';
    if (t.moved)                 return 'apenasMovimento';
    if (t.acted)                 return 'apenasAcao';
    return 'descansarTurno';
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // EQUIPAMENTO INICIAL DOS HERÓIS + CATÁLOGO
  // ───────────────────────────────────────────────────────────────────────────
  // Definição canônica (client-side) do equipamento inicial de cada herói e do
  // helper inicializarHeroi(). As três lojas da cidade (Ferreiro/Taverna/Mercado)
  // JÁ EXISTEM e são autoritativas no servidor (server.py: SHOP_WEAPONS,
  // SHOP_ARMORS, SHOP_MERCHANT, SHOP_TAVERN, SHOP_TEMPLE + handle_shop_buy);
  // o renderer já as abre via openShop(). Este bloco NÃO duplica a UI de loja —
  // apenas fornece o catálogo de equipamento inicial e a inicialização do herói
  // pedidos na spec.
  //
  // PORTADO PARA O SERVIDOR (autoritativo): server.py adota este modelo —
  // armas iniciais por classe (machado_basico/cajado_madeira/instrumento),
  // dual-wield via gear.off_hand (= secundario), finesse e ataque de mão
  // secundária. Mapeamento de slots: arma→weapon, armadura→armor, cabeca→head,
  // secundario→off_hand, magico1/2→item1/2. Este catálogo client-side é o
  // ESPELHO do equipamento inicial do servidor (ver VISUAL_CONTRACT.md →
  // "Lojas e Equipamento Inicial"). Identificadores de herói seguem aquele doc.
  // ═══════════════════════════════════════════════════════════════════════════

  // Base de cada herói (nome canônico + classe no tabuleiro/seleção).
  const HERO_DATA = {
    victorCoiceBravo: { key: 'victorCoiceBravo', nome: 'Victor Coice Bravo', classeTabuleiro: 'ranger',  classeSelecao: 'warrior' },
    richardCavaleiro: { key: 'richardCavaleiro', nome: 'Richard, o Cavaleiro', classeTabuleiro: 'paladin', classeSelecao: 'paladin' },
    lewis:            { key: 'lewis',            nome: 'Frade Lewis',        classeTabuleiro: 'cleric',  classeSelecao: 'cleric'  },
    luccas:           { key: 'luccas',           nome: 'Luccas, o Astuto',   classeTabuleiro: 'rogue',   classeSelecao: 'rogue'   },
    henrique:         { key: 'henrique',         nome: 'Henrique, o Bardo',  classeTabuleiro: 'bard',    classeSelecao: 'bard'    },
    pedro:            {
      key: 'pedro', nome: 'Pedro, o Tímido', classeTabuleiro: 'mage', classeSelecao: 'mage',

      // ── Sincronizado com HERO_DATA.pedro de game.js (habilidade de classe + magias) ──
      // NOTA: calcularSlots usa getBonusAtributo, definido em game.js (escopo
      // global). Resolvido em runtime via cadeia de escopo — ambos os scripts já
      // carregaram antes de qualquer chamada. Mantido assim para espelhar a spec.
      // nome/alcance/descricao saíram das DUAS cópias: não tinham leitor nenhum
      // (ver a nota gêmea em game.js).
      habilidadeClasse: {
        id:        'animar_mortos',
        tipo:      'habilidade_classe',
        icone:     '💀',
        acao:      'principal',
        custo:     { fome: 20, sede: 20 },

        calcularSlots(nivelPedro, inteligencia) {
          const bonus      = getBonusAtributo(inteligencia)
          const bonusNivel = Math.floor(nivelPedro / 2)
          return Math.max(1, bonus + bonusNivel) + magoReviverSlotsExtra()
        },

        // Chance de sucesso: tabela da Guilda "Reviver os Mortos" (Nível I/II/III),
        // dependente só do ND (nivelMonstro aqui já é o ND real/fracionário).
        calcularChance(nivelPedro, nivelMonstro) {
          return magoReviverChance(nivelMonstro)
        },

        // Zona hostil: falha catastrófica só existe acima do teto "seguro" para o
        // nível de Pedro — inalterada pelos Níveis da Guilda (ver CLAUDE.md).
        calcularZonaHostil(nivelPedro, nivelMonstro) {
          const nivelMax  = nivelPedro <= 2 ? 2 : nivelPedro <= 4 ? 4 : 5
          const diferenca = nivelMonstro - nivelMax
          return diferenca > 0 ? diferenca * 10 : 0
        },

        calcularSlotsOcupados(nivelMonstro) {
          return magoReviverSlotCusto(nivelMonstro)
        },

        interpretarResultado(rolagem, chance, zonaHostil) {
          if (rolagem <= zonaHostil) return 'hostil'
          if (rolagem <= chance)     return 'sucesso'
          return 'falha'
        }
      },

      animados:          [],
      magiasConhecidas:  [],
      magiasUsadasHoje:  { primeiro: 0, segundo: 0, terceiro: 0 }
    },
  };

  const EQUIPAMENTOS_INICIAIS = {
    victorCoiceBravo: {
      moedas: 20,
      equipado: {
        arma: { id: 'machado_basico', nome: 'Machado de Ferro', dano: '1d6', atributo: 'forca', escudo: true, arremesso: true, alcanceArremesso: 2, preco: 0 },
        armadura: null, cabeca: null, secundario: null, magico1: null, magico2: null
      },
      inventario: [null, null, null, null, null, null]
    },

    richardCavaleiro: {
      moedas: 20,
      equipado: {
        arma: { id: 'espada_curta', nome: 'Espada Curta', dano: '1d6', atributo: 'forca', escudo: true, arremesso: false, preco: 15 },
        armadura: null, cabeca: null, secundario: null, magico1: null, magico2: null
      },
      inventario: [null, null, null, null, null, null]
    },

    lewis: {
      moedas: 20,
      equipado: {
        arma: { id: 'cajado_madeira', nome: 'Cajado de Madeira', dano: '1d6', atributo: 'inteligencia', escudo: false, arremesso: false, preco: 0 },
        armadura: null, cabeca: null, secundario: null, magico1: null, magico2: null
      },
      inventario: [null, null, null, null, null, null]
    },

    luccas: {
      moedas: 20,
      equipado: {
        arma: { id: 'adaga', nome: 'Adaga', dano: '1d4', atributo: 'forcaOuDestreza', escudo: true, arremesso: true, alcanceArremesso: 3, preco: 5 },
        armadura: null, cabeca: null,
        secundario: { id: 'adaga_secundaria', nome: 'Adaga Secundária', dano: '1d4', atributo: 'forcaOuDestreza', escudo: false, arremesso: true, alcanceArremesso: 3, preco: 5 },
        magico1: null, magico2: null
      },
      inventario: [null, null, null, null, null, null]
    },

    henrique: {
      moedas: 20,
      equipado: {
        arma: { id: 'instrumento', nome: 'Instrumento Musical', dano: '—', atributo: 'carisma', escudo: false, arremesso: false, preco: 0 },
        armadura: null, cabeca: null,
        secundario: { id: 'adaga', nome: 'Adaga', dano: '1d4', atributo: 'forcaOuDestreza', escudo: false, arremesso: true, alcanceArremesso: 3, preco: 5 },
        magico1: null, magico2: null
      },
      inventario: [null, null, null, null, null, null]
    },

    pedro: {
      moedas: 20,
      equipado: {
        arma: { id: 'cajado_madeira', nome: 'Cajado de Madeira', dano: '1d6', atributo: 'inteligencia', escudo: false, arremesso: false, preco: 0 },
        armadura: null, cabeca: null, secundario: null, magico1: null, magico2: null
      },
      inventario: [null, null, null, null, null, null]
    }
  };

  // Aplica equipamento inicial + sobrevivência a um herói (deep copy, sem
  // referências compartilhadas entre heróis). Retorna o objeto herói.
  function inicializarHeroi(heroKey) {
    const config = EQUIPAMENTOS_INICIAIS[heroKey];
    if (!config) return null;
    const heroi = { ...(HERO_DATA[heroKey] || { key: heroKey }) };

    heroi.moedas = config.moedas;
    // Deep copy para isolar cada instância de herói.
    heroi.equipado = JSON.parse(JSON.stringify(config.equipado));
    heroi.inventario = config.inventario.map(s => (s ? { ...s } : null));

    // Inicializa sobrevivência (usa SOBREVIVENCIA_CONFIG do módulo).
    heroi.fome = SOBREVIVENCIA_CONFIG.inicioAventura;
    heroi.sede = SOBREVIVENCIA_CONFIG.inicioAventura;
    heroi.contadorMorte = 0;
    heroi.emColapsoTotal = false;
    heroi.efeitos = [];

    return heroi;
  }

  // Validação de equipar item (regras de classe / slot / duas mãos vs escudo).
  // `item.permitidoPara`: lista de heroKeys autorizados (ausente = sem restrição —
  //   ex.: varinhas terão permitidoPara: ['lewis','pedro'] e slot 'secundario').
  // `item.slot`: slot fixo do item (se declarado). `item.duasMaos`: arma 2 mãos.
  // `item.tipo`: ex. 'escudo'. Loga via 'survivalLog' (adicionarLog) — DOM-free.
  function podeEquipar(heroi, item, slot) {
    const nome = heroi.name || heroi.nome || 'Herói';

    // Restrição de classe/herói ('todos' = curinga; ausência = sem restrição)
    if (Array.isArray(item.permitidoPara) &&
        !item.permitidoPara.includes('todos') &&
        !item.permitidoPara.includes(heroi.key)) {
      adicionarLog(_t('ui.equipar.classe_nao_usa', `❌ ${nome} não pode usar ${item.nome}`, { heroi: nome, item: item.nome }));
      return false;
    }

    // Compatibilidade de slot (só valida se o item declara um slot fixo)
    if (item.slot && item.slot !== slot) {
      adicionarLog(_t('ui.equipar.slot_incompativel', `❌ ${item.nome} não pode ser equipado neste slot`, { item: item.nome }));
      return false;
    }

    // Arma de duas mãos vs escudo já equipado na secundária
    if (item.duasMaos && heroi.equipado?.secundario?.tipo === 'escudo') {
      adicionarLog(_t('ui.equipar.duas_maos', `❌ ${item.nome} requer duas mãos — remova o escudo primeiro`, { item: item.nome }));
      return false;
    }

    // Escudo na secundária vs arma de duas mãos já equipada
    if (slot === 'secundario' && item.tipo === 'escudo') {
      if (heroi.equipado?.arma?.duasMaos) {
        adicionarLog(_t('ui.equipar.escudo_com_duas_maos', '❌ Não pode usar escudo com arma de duas mãos'));
        return false;
      }
    }

    return true;
  }

  /*
   * LEGENDS FOR HIRE — LOCAIS DE VENDA
   *
   * FERREIRO:
   *   Armas corpo a corpo: adaga(5), chicote(10), martelo(10),
   *     cajado(10), espada curta(15), lança curta(20),
   *     espada longa(25), machado(35), lança longa(40),
   *     espada bastarda(50), instrumento(60), alabarda(80),
   *     espada duas mãos(90), machado grande(90)
   *   Armas à distância: besta de mão(20), arco curto(30),
   *     besta leve(40), arco longo(50)
   *   Armaduras: robes(10), couro leve(20), armadura couro(25),
   *     cota de malha(35), placas pesadas(50), armadura batalha(100)
   *   Escudos: escudo leve(10), escudo pesado(25)
   *   Acessórios: tocha(5)
   *   Munição: flechas(5), virotes(5),
   *     flechas incendiárias(20), virotes incendiários(20)
   *
   * TAVERNA:
   *   Comida: pão duro(2), ração viagem(5), carne seca(8),
   *     refeição completa(12), iguaria élfica(20)
   *   Bebida: cantil água(2), água fresca(5),
   *     suco fruta(4), cerveja anã(6), poção hidratante(15)
   *   Mistos: kit sobrevivência(15), banquete em frasco(30)
   *
   * MERCADO:
   *   Varinhas: simples(100), poder(300), arcana(600)
   *   Mochilas: encantada(30), viajante(80), dimensão(150)
   */
  // ═══════════════════════════════════════════════════════════════════════════
  // CATÁLOGO ÚNICO DE ITENS (CATALOGO_ITENS)
  // REGRA: todos os itens do jogo estão aqui. Nunca criar itens fora deste objeto.
  // ═══════════════════════════════════════════════════════════════════════════
  const CATALOGO_ITENS = {

    // ── FERREIRO — Armas corpo a corpo ──
    adaga:           { id:'adaga',           nome:'Adaga',                tipo:'arma', loja:'ferreiro', preco:5,  dano:'1d4', atributo:'destreza', bonusAtaque:'destreza', bonusDano:'destreza', escudo:true,  arremesso:true,  alcanceArremesso:3, duasMaos:false, permitidoPara:['todos'] },
    adaga_secundaria:{ id:'adaga_secundaria',nome:'Adaga Secundária',     tipo:'secundario', loja:'ferreiro', preco:5,  dano:'1d4', atributo:'destreza', bonusAtaque:'destreza', bonusDano:'destreza', arremesso:true,  alcanceArremesso:3, usoAcaoBonus:true, permitidoPara:['victorCoiceBravo','luccas','henrique'] },
    chicote:         { id:'chicote',         nome:'Chicote',              tipo:'arma', loja:'ferreiro', preco:10, dano:'1d4', atributo:'destreza', escudo:false, arremesso:false, duasMaos:false, alcanceEspecial:{ adjacente:2, diagonal:1, descricao:'2 quadrados adjacentes + 1 diagonal adjacente' }, permitidoPara:['luccas','pedro','henrique'] },
    martelo:         { id:'martelo',         nome:'Martelo',              tipo:'arma', loja:'ferreiro', preco:10, dano:'1d6', atributo:'forca', escudo:true,  arremesso:false, duasMaos:false, permitidoPara:['victorCoiceBravo','richardCavaleiro','lewis'] },
    bordao:          { id:'bordao',          nome:'Bordão',               tipo:'arma', loja:'ferreiro', preco:8, dano:'1d6', atributo:'forcaOuDestreza', finesse:true, escudo:true, arremesso:false, duasMaos:false, critNat20Atordoa:true, permitidoPara:['todos'] },
    cajado:          { id:'cajado',          nome:'Cajado',               tipo:'arma', loja:'ferreiro', preco:10, dano:'1d6', atributo:'inteligencia', escudo:false, arremesso:false, duasMaos:false, permitidoPara:['lewis','pedro'] },
    staff:           { id:'staff',           nome:'Cajado Arcano',         tipo:'arma', loja:'mercado', preco:10, dano:'1d6', atributo:'forca', finesse:true, escudo:false, arremesso:false, duasMaos:false, staffSpellDamageBonus:2, staffAreaDimensionBonus:1, staffExtraSpellCircle:'primeiro', staffExtraSpellCooldown:20, permitidoPara:['pedro','lewis'] },
    espada_curta:    { id:'espada_curta',    nome:'Espada Curta',         tipo:'arma', loja:'ferreiro', preco:15, dano:'1d6', atributo:'forca', escudo:true,  arremesso:false, duasMaos:false, permitidoPara:['victorCoiceBravo','richardCavaleiro','lewis','luccas','henrique'] },
    machado_basico:  { id:'machado_basico',  nome:'Machado de Ferro',      tipo:'arma', loja:'ferreiro', preco:0,  dano:'1d6', atributo:'forca', escudo:true,  arremesso:true,  alcanceArremesso:2, duasMaos:false, permitidoPara:['victorCoiceBravo'] },
    lanca_curta:     { id:'lanca_curta',     nome:'Lança Curta',          tipo:'arma', loja:'ferreiro', preco:20, dano:'1d6', atributo:'forca', escudo:true,  arremesso:true,  alcanceArremesso:4, duasMaos:false, alcanceEspecial:{ descricao:'Todos os 8 quadrados adjacentes' }, permitidoPara:['victorCoiceBravo','richardCavaleiro','lewis','luccas','henrique'] },
    lanca:           { id:'lanca',           nome:'Lança',                tipo:'arma', loja:'ferreiro', preco:14, dano:'1d8', atributo:'forca', escudo:true,  arremesso:true,  alcanceArremesso:4, duasMaos:false, alcanceEspecial:{ descricao:'2 casas adjacentes + 1 diagonal adjacente' }, permitidoPara:['victorCoiceBravo','richardCavaleiro'] },
    besta_mao:       { id:'besta_mao',       nome:'Besta de Mão',         tipo:'armaDistancia', loja:'ferreiro', preco:20, dano:'1d4', atributo:'destreza', bonusDano:'destreza', alcance:4, linhaVisao:true, slotSecundario:'livre',   duasMaos:false, permitidoPara:['todos'] },
    espada_longa:    { id:'espada_longa',    nome:'Espada Longa',         tipo:'arma', loja:'ferreiro', preco:25, dano:'1d8', atributo:'forca', escudo:true,  arremesso:false, duasMaos:false, permitidoPara:['victorCoiceBravo','richardCavaleiro'] },
    arco_curto:      { id:'arco_curto',      nome:'Arco Curto',           tipo:'armaDistancia', loja:'ferreiro', preco:30, dano:'1d6', atributo:'destreza', bonusDano:'destreza', alcance:6, linhaVisao:true, slotSecundario:'flechas', duasMaos:true,  permitidoPara:['victorCoiceBravo','richardCavaleiro','luccas'] },
    machado:         { id:'machado',         nome:'Machado',              tipo:'arma', loja:'ferreiro', preco:35, dano:'1d10', atributo:'forca', escudo:true,  arremesso:false, duasMaos:false, permitidoPara:['victorCoiceBravo','richardCavaleiro'] },
    besta_leve:      { id:'besta_leve',      nome:'Besta Leve',           tipo:'armaDistancia', loja:'ferreiro', preco:40, dano:'1d8', atributo:'destreza', bonusDano:'destreza', alcance:8, linhaVisao:true, slotSecundario:'livre',   duasMaos:true,  permitidoPara:['victorCoiceBravo','richardCavaleiro','luccas','henrique'] },
    lanca_longa:     { id:'lanca_longa',     nome:'Lança Longa',          tipo:'arma', loja:'ferreiro', preco:40, dano:'1d8', atributo:'forca', escudo:false, arremesso:false, duasMaos:true,  alcanceEspecial:{ descricao:'2 casas adjacentes + 1 diagonal adjacente' }, permitidoPara:['victorCoiceBravo','richardCavaleiro'] },
    arco_longo:      { id:'arco_longo',      nome:'Arco Longo',           tipo:'armaDistancia', loja:'ferreiro', preco:50, dano:'1d8', atributo:'destreza', bonusDano:'destreza', alcance:10, linhaVisao:true, slotSecundario:'flechas', duasMaos:true,  permitidoPara:['victorCoiceBravo','richardCavaleiro','luccas'] },
    espada_bastarda: { id:'espada_bastarda', nome:'Espada Bastarda',      tipo:'arma', loja:'ferreiro', preco:50, danoUmaMao:'1d10', danoDuasMaos:'3d4', atributo:'forca', escudo:true, arremesso:false, duasMaos:false, modosDuasMaos:true, permitidoPara:['richardCavaleiro'] },
    instrumento:     { id:'instrumento',     nome:'Instrumento Musical',  tipo:'arma', loja:'ferreiro', preco:60, dano:'—', atributo:'carisma', escudo:false, arremesso:false, duasMaos:false, permitidoPara:['henrique'] },
    alabarda:        { id:'alabarda',        nome:'Alabarda',             tipo:'arma', loja:'ferreiro', preco:80, dano:'1d10', atributo:'forca', escudo:false, arremesso:false, duasMaos:true,  alcanceEspecial:{ descricao:'2 casas adjacentes + 1 diagonal adjacente' }, permitidoPara:['victorCoiceBravo','richardCavaleiro'] },
    espada_duas_maos:{ id:'espada_duas_maos',nome:'Espada de Duas Mãos',  tipo:'arma', loja:'ferreiro', preco:90, dano:'1d12', atributo:'forca', escudo:false, arremesso:false, duasMaos:true,  permitidoPara:['victorCoiceBravo','richardCavaleiro'] },
    machado_grande:  { id:'machado_grande',  nome:'Machado Grande',       tipo:'arma', loja:'ferreiro', preco:90, dano:'2d6', atributo:'forca', escudo:false, arremesso:false, duasMaos:true,  permitidoPara:['victorCoiceBravo'] },

    // ── FERREIRO — Armaduras ──
    robes:           { id:'robes',           nome:'Robes',                tipo:'armadura', loja:'ferreiro', preco:10,  bonusCA:1, permitidoPara:['todos'] },
    couro_leve:      { id:'couro_leve',      nome:'Couro Leve',           tipo:'armadura', loja:'ferreiro', preco:20,  bonusCA:2, permitidoPara:['todos'] },
    armadura_couro:  { id:'armadura_couro',  nome:'Armadura de Couro',    tipo:'armadura', loja:'ferreiro', preco:25,  bonusCA:3, permitidoPara:['victorCoiceBravo','richardCavaleiro','lewis','luccas','henrique'] },
    cota_malha:      { id:'cota_malha',      nome:'Cota de Malha',        tipo:'armadura', loja:'ferreiro', preco:35,  bonusCA:4, permitidoPara:['victorCoiceBravo','richardCavaleiro','lewis'] },
    placas_pesadas:  { id:'placas_pesadas',  nome:'Placas Pesadas',       tipo:'armadura', loja:'ferreiro', preco:50,  bonusCA:6, permitidoPara:['victorCoiceBravo','richardCavaleiro'] },
    armadura_batalha:{ id:'armadura_batalha',nome:'Armadura de Batalha',  tipo:'armadura', loja:'ferreiro', preco:100, bonusCA:8, permitidoPara:['victorCoiceBravo','richardCavaleiro'] },

    // ── FERREIRO — Escudos e acessórios ──
    escudo_leve:     { id:'escudo_leve',     nome:'Escudo Leve',          tipo:'escudo', loja:'ferreiro', preco:10, bonusCA:1, permitidoPara:['victorCoiceBravo','richardCavaleiro','lewis','luccas'] },
    escudo_pesado:   { id:'escudo_pesado',   nome:'Escudo Pesado',        tipo:'escudo', loja:'ferreiro', preco:25, bonusCA:2, permitidoPara:['victorCoiceBravo','richardCavaleiro'] },
    tocha:           { id:'tocha',           nome:'Tocha',                tipo:'secundario', loja:'ferreiro', preco:5, bonusVisao:1, duracao:10, permitidoPara:['todos'] },
    vela_escuridao:  { id:'vela_escuridao',  nome:'Vela da Escuridão',     tipo:'consumivel', loja:'mercado', preco:50, effect:'veil_shadow', value:0, descricao:'Ação bônus. Fica oculto até o fim do turno; o próximo ataque tem vantagem. Para o Ladino, o próximo ataque ativa automaticamente o Ataque Furtivo.', permitidoPara:['todos'] },

    // ── FERREIRO — Munição ──
    flechas:               { id:'flechas',               nome:'Flechas (10)',                tipo:'municao', loja:'ferreiro', preco:5,  quantidade:10, danoExtra:null,  paraArmas:['arco_curto','arco_longo'], permitidoPara:['victorCoiceBravo','richardCavaleiro','luccas'] },
    virotes:               { id:'virotes',               nome:'Virotes (10)',                tipo:'municao', loja:'ferreiro', preco:5,  quantidade:10, danoExtra:null,  paraArmas:['besta_mao','besta_leve'], permitidoPara:['todos'] },
    flechas_prata:         { id:'flechas_prata',         nome:'Flechas de Prata (10)',       tipo:'municao', loja:'ferreiro', preco:30, quantidade:10, danoExtra:1, prata:true, paraArmas:['arco_curto','arco_longo'], permitidoPara:['victorCoiceBravo','richardCavaleiro','luccas'] },
    virotes_prata:         { id:'virotes_prata',         nome:'Virotes de Prata (10)',       tipo:'municao', loja:'ferreiro', preco:30, quantidade:10, danoExtra:1, prata:true, paraArmas:['besta_mao','besta_leve'], permitidoPara:['todos'] },
    flechas_incendiarias:  { id:'flechas_incendiarias',  nome:'Flechas Incendiárias (10)',   tipo:'municao', loja:'ferreiro', preco:20, quantidade:10, danoExtra:'1d4', tipoDano:'fogo', paraArmas:['arco_curto','arco_longo'], permitidoPara:['victorCoiceBravo','richardCavaleiro','luccas'] },
    virotes_incendiarios:  { id:'virotes_incendiarios',  nome:'Virotes Incendiários (10)',   tipo:'municao', loja:'ferreiro', preco:20, quantidade:10, danoExtra:'1d4', tipoDano:'fogo', paraArmas:['besta_mao','besta_leve'], permitidoPara:['todos'] },

    // ── TAVERNA — Itens de sobrevivência ──
    pao_duro:          { id:'pao_duro',          nome:'Pão Duro',            tipo:'consumivel', loja:'taverna', preco:2,  fome:10, sede:0,  permitidoPara:['todos'] },
    racao_viagem:      { id:'racao_viagem',      nome:'Ração de Viagem',     tipo:'consumivel', loja:'taverna', preco:5,  fome:20, sede:0,  permitidoPara:['todos'] },
    carne_seca:        { id:'carne_seca',        nome:'Carne Seca',          tipo:'consumivel', loja:'taverna', preco:8,  fome:30, sede:0,  permitidoPara:['todos'] },
    refeicao_completa: { id:'refeicao_completa', nome:'Refeição Completa',   tipo:'consumivel', loja:'taverna', preco:12, fome:50, sede:0,  permitidoPara:['todos'] },
    iguaria_elfica:    { id:'iguaria_elfica',    nome:'Iguaria Élfica',      tipo:'consumivel', loja:'taverna', preco:20, fome:70, sede:0,  permitidoPara:['todos'] },
    cantil_agua:       { id:'cantil_agua',       nome:'Cantil de Água',      tipo:'consumivel', loja:'taverna', preco:2,  fome:0,  sede:15, permitidoPara:['todos'] },
    agua_fresca:       { id:'agua_fresca',       nome:'Água Fresca',         tipo:'consumivel', loja:'taverna', preco:5,  fome:0,  sede:25, permitidoPara:['todos'] },
    suco_fruta:        { id:'suco_fruta',        nome:'Suco de Fruta',       tipo:'consumivel', loja:'taverna', preco:4,  fome:5,  sede:10, permitidoPara:['todos'] },
    cerveja_ana:       { id:'cerveja_ana',       nome:'Cerveja Anã',         tipo:'consumivel', loja:'taverna', preco:6,  fome:10, sede:10, permitidoPara:['todos'] },
    pocao_hidratante:  { id:'pocao_hidratante',  nome:'Poção Hidratante',    tipo:'consumivel', loja:'taverna', preco:15, fome:0,  sede:60, permitidoPara:['todos'] },
    kit_sobrevivencia: { id:'kit_sobrevivencia', nome:'Kit de Sobrevivência',tipo:'consumivel', loja:'taverna', preco:15, fome:25, sede:25, permitidoPara:['todos'] },
    banquete_frasco:   { id:'banquete_frasco',   nome:'Banquete em Frasco',  tipo:'consumivel', loja:'taverna', preco:30, fome:40, sede:40, permitidoPara:['todos'] },

    // ── MERCADO — Varinhas e itens mágicos ──
    varinha_simples:   { id:'varinha_simples',   nome:'Varinha Simples',     tipo:'varinha', loja:'mercado', preco:100, dano:'1d4', atributo:'inteligencia', slotsMagia:1, magias:[null],            descricao:'Armazena 1 magia. Usar magia = ação bônus.', permitidoPara:['lewis','pedro'] },
    varinha_poder:     { id:'varinha_poder',     nome:'Varinha de Poder',    tipo:'varinha', loja:'mercado', preco:300, dano:'1d4', atributo:'inteligencia', slotsMagia:2, magias:[null,null],       descricao:'Armazena 2 magias. Usar magia = ação bônus.', permitidoPara:['lewis','pedro'] },
    varinha_arcana:    { id:'varinha_arcana',    nome:'Varinha Arcana',      tipo:'varinha', loja:'mercado', preco:600, dano:'1d4', atributo:'inteligencia', slotsMagia:3, magias:[null,null,null], descricao:'Armazena 3 magias. Usar magia = ação bônus.', permitidoPara:['lewis','pedro'] },
    mochila_encantada: { id:'mochila_encantada', nome:'Mochila de Couro Encantada', tipo:'itemMagico', loja:'mercado', preco:30,  slotsExtras:2, descricao:'+2 slots de inventário livre.', slot:'magico', permitidoPara:['todos'] },
    mochila_viajante:  { id:'mochila_viajante',  nome:'Mochila do Viajante',        tipo:'itemMagico', loja:'mercado', preco:80,  slotsExtras:4, descricao:'+4 slots de inventário livre.', slot:'magico', permitidoPara:['todos'] },
    bolsa_dimensao:    { id:'bolsa_dimensao',    nome:'Bolsa de Dimensão',          tipo:'itemMagico', loja:'mercado', preco:150, slotsExtras:6, descricao:'+6 slots de inventário livre.', slot:'magico', permitidoPara:['todos'] },
    bota_alada:        { id:'bota_alada',        nome:'Bota Alada',                 tipo:'itemMagico', loja:'mercado', preco:0, item_slot:'boots', kind:'boots', effect:'voo', descricao:'Enquanto equipada, permite Voo por tempo indeterminado, com altura máxima 3.', permitidoPara:['todos'] },

    // ── MERCADO — Venenos (consumíveis aplicados na arma) ──
    // 1 slot de inventário cada. Usar = unta a arma equipada (ação bônus); o
    // próximo golpe certeiro transfere o veneno ao alvo (save Fortitude p/ resistir).
    veneno_aranha_sombria: {
      id:'veneno_aranha_sombria', nome:'Veneno da Aranha Sombria', tipo:'veneno', loja:'mercado', preco:8, icone:'🕷️',
      permitidoPara:['todos'],
      efeito:{ atributo:'forca', valor:'1d4', operacao:'reduzir', duracao:'1d6', save:'fortitude', dificuldade:8, anula:true },
      descricao:'Reduz 1d4 de Força por 1d6 rodadas. Fortitude dif. 8 anula.'
    },
    veneno_escorpiao_pedra: {
      id:'veneno_escorpiao_pedra', nome:'Veneno do Escorpião Pedra', tipo:'veneno', loja:'mercado', preco:12, icone:'🦂',
      permitidoPara:['todos'],
      efeito:{ atributo:['ataque','movimento'], valor:[-1,-1], operacao:'penalidade', duracao:'1d6', save:'fortitude', dificuldade:9, anula:true },
      descricao:'-1 em ataques e -1 quadrado de movimento por 1d6 rodadas. Fortitude dif. 9 anula.'
    },
    veneno_cobra_cuspidora: {
      id:'veneno_cobra_cuspidora', nome:'Veneno de Cobra Cuspidora', tipo:'veneno', loja:'mercado', preco:16, icone:'🐍',
      permitidoPara:['todos'],
      efeito:{ atributo:'constituicao', valor:'1d4', operacao:'reduzir', duracao:'1d6', save:'fortitude', dificuldade:10, anula:true, recalcularHP:true },
      descricao:'-1d4 de Constituição por 1d6 rodadas. Recalcula HP. Fortitude dif. 10 anula.'
    },
    veneno_basilisco: {
      id:'veneno_basilisco', nome:'Peçonha do Basilisco', tipo:'veneno', loja:'mercado', preco:20, icone:'🦎',
      permitidoPara:['todos'],
      efeito:{ atributo:'petrificado', valor:1, operacao:'status', duracao:1, duracaoFalha:'1d4', atributoFalha:'movimento', valorFalha:-1, save:'fortitude', dificuldade:12, anula:false },
      descricao:'Petrifica por 1 rodada (Fort. dif. 12). Falha parcial: -1 movimento por 1d4 rodadas.'
    },
    veneno_polvo_abissal: {
      id:'veneno_polvo_abissal', nome:'Tinta do Polvo Abissal', tipo:'veneno', loja:'mercado', preco:15, icone:'🐙',
      permitidoPara:['todos'],
      efeito:{ atributo:'cego', valor:'1d4', operacao:'status', penalidadeAtaque:-4, bloqueiaDistancia:true, duracaoFalha:'1d4', penalidadeFalha:-2, atributoFalha:'percepcao', save:'fortitude', dificuldade:11, anula:false },
      descricao:'Falha em Fortitude CD 11: cego por 1d4 rodadas, visão 1 quadrado, -5 percepção, -4 em ataques e sem ataques à distância. Sucesso: -2 percepção por 1d4 rodadas.'
    },
    veneno_fungo_acre: {
      id:'veneno_fungo_acre', nome:'Fungo Acre', tipo:'veneno', loja:'mercado', preco:10, icone:'🍄',
      permitidoPara:['todos'],
      efeito:{ operacao:'dano', dano:1, duracao:'1d4', save:'fortitude', dificuldade:10, anula:true, saveAplicacao:true },
      descricao:'Fortitude CD 10 anula. Se falhar, sofre 1 ponto de dano por rodada durante 1d4 rodadas.'
    },
    veneno_dor_escarlate: {
      id:'veneno_dor_escarlate', nome:'Dor Escarlate', tipo:'veneno', loja:'mercado', preco:20, icone:'🩸',
      permitidoPara:['todos'],
      efeito:{ operacao:'dano', dano:1, duracao:'1d6', save:'fortitude', dificuldade:12, anula:true, saveAplicacao:true },
      descricao:'Fortitude CD 12 anula. Se falhar, sofre 1 ponto de dano por rodada durante 1d6 rodadas.'
    },
    veneno_ardonia_negra: {
      id:'veneno_ardonia_negra', nome:'Ardonia Negra', tipo:'veneno', loja:'mercado', preco:50, icone:'🕷️',
      permitidoPara:['todos'],
      efeito:{ operacao:'dano', dano:1, duracao:'2d4', save:'fortitude', dificuldade:14, anula:true, saveAplicacao:true },
      descricao:'Fortitude CD 14 anula. Se falhar, sofre 1 ponto de dano por rodada durante 2d4 rodadas.'
    },
    veneno_agonia_sufocante: {
      id:'veneno_agonia_sufocante', nome:'Agonia Sufocante', tipo:'veneno', loja:'mercado', preco:40, icone:'💀',
      permitidoPara:['todos'],
      efeito:{ operacao:'dano', dano:'1d4', duracao:'1d4', save:'fortitude', dificuldade:14 },
      descricao:'LENDÁRIO. Untado na arma: 1d4 de dano por rodada por até 1d4 rodadas. A cada rodada, Fortitude CD 14 neutraliza o veneno.'
    },

    // ── MERCADO — Arremessáveis de fogo (consumíveis de bolsa; ver ARREMESSAVEIS no server) ──
    // Usados por clique direito → mira de alvo → throw_item. Ataque por DES vs CA.
    agua_benta: {
      id: 'agua_benta', nome: 'Água Benta', emoji: '💧✝️',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4, dano:'2d6', tipoDano:'sagrado',
      duracao: 2, permitidoPara:['todos'],
      descricao: 'Arremesse (4 quad., ataque por DES). Causa 2d6 de dano sagrado e cria uma zona sagrada por 2 rodadas.',
    },
    frasco_oleo: {
      id: 'frasco_oleo', nome: 'Frasco de Óleo Incendiário', emoji: '🔥',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4, dano:'1d6', tipoDano:'fogo',
      duracao: '1d4', permitidoPara:['todos'],
      descricao: 'Arremesse (4 quad., ataque por DES). 1d6 de fogo e o alvo pega ' +
                 'fogo (1/rodada por 1d4 rodadas). Apaga com Água ou gastando a ação.',
    },
    fogo_grego: {
      id: 'fogo_grego', nome: 'Fogo Grego', emoji: '🟢',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4, dano:'2d6', tipoDano:'fogo',
      duracao: '1d4', permitidoPara:['todos'],
      descricao: 'Arremesse (4 quad., ataque por DES). 2d6 de fogo e o alvo pega ' +
                 'fogo (1/rodada por 1d4 rodadas). Só a ação apaga — água não funciona.',
    },
    // ── MERCADO — Arremessáveis de ÁREA (Sub-projeto B; ver ARREMESSAVEIS no server) ──
    // Miram uma CASA (não um monstro): alcance vermelho + prévia de área verde.
    bomba_incendiaria: {
      id: 'bomba_incendiaria', nome: 'Bomba Incendiária', emoji: '💣',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alvo: 'area',
      alcance: 4, areaRaio: 1, dano:'2d6', tipoDano:'fogo', saveTipo:'reflexos', saveCD:12,
      duracao: '1d4', permitidoPara:['todos'],
      descricao: 'Área (raio 1, alcance 4). 2d6 de fogo, Reflexos CD 12 (metade). ' +
                 'Todos os atingidos pegam fogo. ACERTA ALIADOS — cuidado com o posicionamento.',
    },
    granada: {
      id: 'granada', nome: 'Granada Explosiva', emoji: '💣',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alvo: 'area',
      alcance: 4, areaRaio: 1, dano:'2d6', tipoDano:'explosao', saveTipo:'reflexos', saveCD:12,
      permitidoPara:['todos'],
      descricao: 'Área (raio 1, alcance 4). 2d6 de explosão, Reflexos CD 12 (metade). ' +
                 'ACERTA ALIADOS.',
    },
    granada_superior: {
      id: 'granada_superior', nome: 'Granada Superior', emoji: '💥',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alvo: 'area',
      alcance: 4, areaRaio: 1, dano:'3d6', tipoDano:'explosao', saveTipo:'reflexos', saveCD:15,
      permitidoPara:['todos'],
      descricao: 'Área (raio 1, alcance 4). 3d6 de explosão, Reflexos CD 15 (metade). ' +
                 'ACERTA ALIADOS.',
    },
    bomba_fumaca: {
      id: 'bomba_fumaca', nome: 'Bomba de Fumaça', emoji: '💨',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alvo: 'area',
      alcance: 4, areaRaio: 1, duracao: 2, permitidoPara:['todos'],
      descricao: 'Área (raio 1, alcance 4). Cria escuridão por 2 rodadas — bloqueia ' +
                 'a visão e cobre o recuo. Sem dano.',
    },
    // ── MERCADO — Arremessáveis de ÁCIDO (Sub-projeto C; ver ARREMESSAVEIS no server) ──
    frasco_acido: {
      id: 'frasco_acido', nome: 'Frasco de Ácido', emoji: '🧪',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4, dano:'1d6', tipoDano:'acido',
      permitidoPara:['todos'],
      descricao: 'Arremesse (4 quad., ataque por DES). 1d6 de ácido + metade na ' +
                 'rodada seguinte. Corrói a defesa do alvo (−1 CA por acerto).',
    },
    vidro_acido_grande: {
      id: 'vidro_acido_grande', nome: 'Vidro de Ácido Grande', emoji: '🫙',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4, dano:'2d6', tipoDano:'acido',
      permitidoPara:['todos'],
      descricao: 'Arremesse (4 quad., ataque por DES). 2d6 de ácido + metade na ' +
                 'rodada seguinte. Corrói a defesa do alvo (−2 CA por acerto).',
    },
    // ── MERCADO — Arremessáveis TÁTICOS (Sub-projeto D; ver ARREMESSAVEIS no server) ──
    cola_alquimica: {
      id: 'cola_alquimica', nome: 'Cola Alquímica', emoji: '🍯',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4, saveTipo:'reflexos', saveCD:12,
      duracao: 2, permitidoPara:['todos'],
      descricao: 'Arremesse (4 quad., ataque por DES). O alvo testa Reflexos CD 12; ' +
                 'se falhar, fica com o movimento reduzido à metade por 2 rodadas.',
    },
    rede_arremesso: {
      id: 'rede_arremesso', nome: 'Rede', emoji: '🕸️',
      tipo: 'consumivel', slot: 'bag', arremessavel: true, alcance: 4, saveTipo:'fortitude', saveCD:12,
      permitidoPara:['todos'],
      descricao: 'Arremesse (4 quad., ataque por DES). O alvo fica preso; para ' +
                 'escapar gasta o turno num teste de Fortitude CD 12.',
    },
  };

  // class_id (servidor) → heroKey (HERO_DATA / EQUIPAMENTOS_INICIAIS).
  function _classToHeroKey(classId) {
    return ({
      warrior: 'victorCoiceBravo', ranger: 'victorCoiceBravo',
      paladin: 'richardCavaleiro', cleric: 'lewis',
      rogue: 'luccas', bard: 'henrique', mage: 'pedro',
    })[classId] || null;
  }

  // Herói "ativo" (modelo client-side) — usado pela UI de loja. Mantém um cache
  // por pid criado via inicializarHeroi(); sincroniza moedas com o `gold` do
  // servidor na primeira criação. NOTA: modelo client-side — compras via a UI
  // de loja (comprarItem) ainda NÃO são autoritativas no servidor.
  let _heroiAtivoCache = {};
  function getHeroiAtivo() {
    const pid = myPid || '_local';
    const player = (gameState?.players || cityState?.players || lobbyState?.players || [])
                     .find(p => p.id === pid);
    if (!_heroiAtivoCache[pid]) {
      const heroKey = _classToHeroKey(player?.class_id) || 'victorCoiceBravo';
      const h = inicializarHeroi(heroKey) || { inventario: [null,null,null,null,null,null], equipado: {}, moedas: 20 };
      h.name = player?.name || h.nome || 'Herói';
      if (player && typeof player.gold === 'number') h.moedas = player.gold;
      _heroiAtivoCache[pid] = h;
    }
    return _heroiAtivoCache[pid];
  }

  // Usa um consumível: RECUPERA fome/sede do herói local (cap no máximo),
  // sai do colapso se aplicável, loga e notifica para as barras atualizarem.
  // Retorna o herói de sobrevivência afetado (ou null).
  function aplicarConsumivel(item) {
    if (!item) return null;
    const h = _ensureSurvival(myPid || '_local');
    if (!h) return null;
    const max = SOBREVIVENCIA_CONFIG.maximo;
    const fAntes = h.fome, sAntes = h.sede;
    if (item.fome) h.fome = Math.min(max, h.fome + item.fome);
    if (item.sede) h.sede = Math.min(max, h.sede + item.sede);
    if (h.emColapsoTotal && (h.fome > 0 || h.sede > 0)) {
      h.emColapsoTotal = false;
      h.contadorMorte = 0;
    }
    adicionarLog(
      `🍽️ ${h.name} usou ${item.nome} — ` +
      `Fome: ${fAntes}→${h.fome} | Sede: ${sAntes}→${h.sede}`
    );
    _emit('survivalChanged', myPid);
    return h;
  }

  // Slot de equipamento (heroi.equipado) para um item do catálogo.
  // null = não-equipável (consumível, munição).
  function _slotDoItem(item) {
    switch (item.tipo) {
      case 'arma':
      case 'armaDistancia': return 'arma';
      case 'armadura':      return 'armadura';
      case 'escudo':
      case 'secundario':
      case 'varinha':       return 'secundario';
      case 'itemMagico':    return 'magico';     // → magico1 / magico2
      default:              return null;
    }
  }

  // Equipa um item comprado (getHeroiAtivo().inventario[index]) no herói local.
  // Valida via podeEquipar. Troca com o ocupante do slot. Retorna true/false.
  function equiparItemComprado(index) {
    const heroi = getHeroiAtivo();
    const item = heroi && heroi.inventario ? heroi.inventario[index] : null;
    if (!item) return false;
    const fam = _slotDoItem(item);
    if (!fam) { adicionarLog(_t('ui.equipar.sem_slot', `❌ ${item.nome} não pode ser equipado`, { item: item.nome })); return false; }

    let slot = fam;
    if (fam === 'magico') {
      slot = !heroi.equipado.magico1 ? 'magico1'
           : (!heroi.equipado.magico2 ? 'magico2' : 'magico1');
    }
    // Normaliza o slot fixo do item (ex.: 'magico') para o slot concreto.
    const itemV = (item.slot && item.slot !== slot) ? { ...item, slot } : item;
    if (!podeEquipar(heroi, itemV, slot)) return false;   // podeEquipar loga a recusa

    const ocupante = heroi.equipado[slot] || null;
    heroi.equipado[slot] = item;
    heroi.inventario[index] = ocupante;        // ocupante volta ao inventário (ou null)
    adicionarLog(`🔧 ${heroi.name || heroi.nome || 'Herói'} equipou ${item.nome}`);
    return true;
  }

  // Desequipa um slot do herói local, devolvendo o item ao inventário (1º livre).
  function desequiparItemComprado(slot) {
    const heroi = getHeroiAtivo();
    const item = heroi && heroi.equipado ? heroi.equipado[slot] : null;
    if (!item) return false;
    const livre = heroi.inventario.findIndex(s => s === null);
    if (livre === -1) { adicionarLog(_t('ui.equipar.bolsa_cheia', '❌ Inventário cheio — sem espaço para desequipar')); return false; }
    heroi.equipado[slot] = null;
    heroi.inventario[livre] = item;
    adicionarLog(`📤 ${heroi.name || heroi.nome || 'Herói'} desequipou ${item.nome}`);
    return true;
  }

  // ── Portas: conjuntos abertas/fechadas a partir das salas ──────────────────
  // Cada sala traz `doors` (tiles DOOR) e `locked`. Uma porta é abierta só
  // quando a sala está destrancada; se uma porta serve duas salas e qualquer
  // uma segue trancada, a porta conta como FECHADA.
  function doorSets(state) {
    const open = new Set(), closed = new Set();
    const rooms = state && state.rooms ? state.rooms : [];
    const locked = new Set();
    const tiles = state && state.tiles ? state.tiles : [];
    for (let y = 0; y < tiles.length; y++) for (let x = 0; x < tiles[y].length; x++) {
      if (tiles[y][x] === 2) closed.add(`${x},${y}`);
    }
    for (const r of rooms) {
      const roomLocked = !!r.locked;
      for (const d of (r.doors || [])) {
        const k = `${d[0]},${d[1]}`;
        if (roomLocked) locked.add(k); else open.add(k);
      }
    }
    for (const k of open) if (!locked.has(k)) closed.delete(k);
    for (const k of locked) { closed.add(k); open.delete(k); }
    for (const d of ((state && state.opened_doors) || [])) {
      const k = `${d[0]},${d[1]}`;
      if (!locked.has(k)) { closed.delete(k); open.add(k); }
    }
    // Uma porta configurada com condição continua fisicamente fechada até
    // ser aberta, mesmo quando a sala foi salva como destrancada. O servidor
    // envia o estado de satisfação para impedir bypass no pathfinding cliente.
    for (const [k, condition] of Object.entries((state && state.door_conditions) || {})) {
      if (!condition || !condition.opened) { closed.add(k); open.delete(k); }
    }
    return { open, closed };
  }

  // Retorna os giros de 90° gravados pelo editor. O valor é relativo à
  // orientação inferida pelas paredes; null significa mapa antigo/procedural,
  // para que o renderer preserve seu fallback geométrico.
  function doorOrientation(state, x, y) {
    const key = `${x},${y}`;
    const top = state && state.door_orientations;
    if (top && Object.prototype.hasOwnProperty.call(top, key)) {
      const n = Number(top[key]);
      return Number.isFinite(n) ? ((Math.round(n) % 4) + 4) % 4 : null;
    }
    for (const room of (state && state.rooms) || []) {
      if (!(room.doors || []).some(d => d[0] === x && d[1] === y)) continue;
      const map = room.door_orientations;
      if (map && Object.prototype.hasOwnProperty.call(map, key)) {
        const n = Number(map[key]);
        return Number.isFinite(n) ? ((Math.round(n) % 4) + 4) % 4 : null;
      }
    }
    return null;
  }

  // Tile transponível por pathfinding: chão, ou porta de sala ABERTA.
  // Material sólido/opaco na casa (x,y), lido do game_state mais recente.
  function _matSolido(x, y) {
    const m = gameState && gameState.materiais;
    return !!(m && MATERIAIS_SOLIDOS.has(m[`${x},${y}`]));
  }
  function _matOpaco(x, y) {
    const m = gameState && gameState.materiais;
    return !!(m && MATERIAIS_OPACOS.has(m[`${x},${y}`]));
  }
  // Decorações sólidas ocupam as casas do seu footprint e bloqueiam rota,
  // exatamente como o renderer e o servidor. Decorações pisáveis (chão,
  // fogueira etc.) continuam permitindo passagem.
  function _decorSolida(x, y) {
    return (gameState?.decorations || []).some(d => !d.pisavel &&
      decorTilesOf(d).some(([dx, dy]) => dx === x && dy === y));
  }

  function _walkable(tiles, x, y, openDoors, occupied, moveCtx=null) {
    const t = tiles[y]?.[x];
    const illusion = (gameState?.secret_passages || []).some(p => p.type === 'illusion' && p.pos[0] === x && p.pos[1] === y);
    const vooLivre = !!(moveCtx?.actor?.voo && moveCtx.actor.ignora_obstaculos_voo);
    const onFloor = vooLivre ? t !== undefined
      : t === TILE_FLOOR || (t === TILE_DOOR && openDoors.has(`${x},${y}`)) || illusion;
    if (!onFloor) return false;
    if (!vooLivre && _matSolido(x, y)) return false;   // entulho: intransponível como parede
    if (!vooLivre && _decorSolida(x, y)) return false; // objeto sólido: contorna pelo menor caminho
    // Casa ocupada por outra entidade viva é intransponível (espelha o servidor).
    return !(occupied && occupied.has(`${x},${y}`));
  }

  // Casas ocupadas por um monstro. Os orientados legados 2×1 continuam em linha;
  // os retangulares usam comprimento para trás e largura perpendicular ao facing.
  function monsterTiles(m) {
    const [mx, my] = m.pos;
    if (m.oriented) {
      const f = m.facing || [-1, 0];
      const [w, h] = m.size || [2, 1];
      const [width, length] = h === 1 ? [1, w] : [w, h];
      const [px, py] = [-f[1], f[0]], out = [];
      for (let depth=0; depth<length; depth++)
        for (let lane=0; lane<width; lane++) out.push([mx - f[0]*depth + px*lane, my - f[1]*depth + py*lane]);
      return out;
    }
    const [w, h] = m.size || [1, 1];
    const out = [];
    for (let dx = 0; dx < w; dx++)
      for (let dy = 0; dy < h; dy++) out.push([mx + dx, my + dy]);
    return out;
  }

  // Conjunto "x,y" de casas ocupadas por entidades vivas: monstros (footprint
  // multi-tile via monsterTiles), outros jogadores e animados. A casa em (exX,exY)
  // — a do próprio herói que vai se mover — é excluída para não bloquear a origem.
  function _occupiedSet(exX, exY) {
    const occ = new Set();
    for (const m of (gameState.monsters || [])) {
      if (!m || m.hp <= 0) continue;
      for (const [tx, ty] of monsterTiles(m)) occ.add(`${tx},${ty}`);
    }
    for (const p of (gameState.players || [])) {
      if (!p || p.alive === false) continue;
      if (!(p.pos[0] === exX && p.pos[1] === exY)) occ.add(`${p.pos[0]},${p.pos[1]}`);
      for (const a of (p.animados || [])) {
        if (a && (a.vida_atual ?? 1) > 0) occ.add(`${a.pos[0]},${a.pos[1]}`);
      }
    }
    return occ;
  }

  // ── Linha de visão (espelha _tem_linha_de_visao do servidor) ───────────────
  // Supercover de Bresenham: paredes E portas fechadas barram ataques/magias à
  // distância. Os extremos (origem/alvo) não bloqueiam. Usado para impedir mira
  // através de paredes no cliente (o servidor já recusa, isto evita oferecer).
  function _losBlocks(tiles, closed, x, y, state, vooLivre=false) {
    if (y < 0 || x < 0 || y >= tiles.length || x >= tiles[0].length) return true;
    const key = `${x},${y}`;
    const decoracoes = (state?.decorations || []);
    const alto = decoracoes.some(d => d.alto && decorTilesOf(d).some(([dx, dy]) => dx === x && dy === y));
    const solido = decoracoes.some(d => !d.pisavel && decorTilesOf(d).some(([dx, dy]) => dx === x && dy === y));
    const materialOpaco = MATERIAIS_OPACOS.has(state?.materiais?.[key]);
    if (vooLivre) return alto || materialOpaco;
    return tiles[y][x] === TILE_WALL || closed.has(key) || solido || materialOpaco;
  }
  function hasLineOfSight(state, ax, ay, bx, by, observer=null) {
    const tiles = state && state.tiles;
    if (!tiles) return true;
    const closed = doorSets(state).closed;
    const origem = observer || [...(state.players || []), ...(state.monsters || [])]
      .find(entidade => entidade && entidade.pos?.[0] === (ax | 0) && entidade.pos?.[1] === (ay | 0));
    const vooLivre = !!(origem?.voo && origem.ignora_obstaculos_voo && alturaDe(origem) > 0);
    const bloqueia = (x, y) => _losBlocks(tiles, closed, x, y, state, vooLivre);
    const x1 = bx | 0, y1 = by | 0;
    let x = ax | 0, y = ay | 0, ix = 0, iy = 0;
    const dx = Math.abs(x1 - x), dy = Math.abs(y1 - y);
    const sx = x1 > x ? 1 : -1, sy = y1 > y ? 1 : -1;
    while (x !== x1 || y !== y1) {
      const tX = (2 * ix + 1) * dy, tY = (2 * iy + 1) * dx;
      if (tX < tY) { x += sx; ix++; }
      else if (tX > tY) { y += sy; iy++; }
      else {
        if (bloqueia(x + sx, y) || bloqueia(x, y + sy)) return false;
        x += sx; ix++; y += sy; iy++;
      }
      if (x === x1 && y === y1) break;
      if (y < 0 || x < 0 || y >= tiles.length || x >= tiles[0].length) return false;
      if (bloqueia(x, y)) return false;
    }
    return true;
  }

  // ── Pure logic: BFS — all reachable floor tiles within maxSteps ────────────
  function terrainMoveCost(moveCtx, x, y) {
    const actor = moveCtx?.actor || {};
    const vooNoAr = !!(actor.voo && alturaDe(actor) > 0);
    if (vooNoAr) return 1;
    const kind = moveCtx?.materiais?.[`${x},${y}`];
    if (kind === 'areia_deserto' || kind === 'lava') return 2;
    if (kind !== 'agua' && kind !== 'agua_profunda') return 1;
    if ((actor.special_abilities || []).some(h => h && h.id === 'movimento_erratico')) return 1;
    let cost = kind === 'agua_profunda' ? 3 : 2;
    const armor = actor.gear?.armor || {};
    const category = armor.armor_category;
    if (category === 'media') cost += 1;
    else if (category === 'pesada') cost += 2;
    else if (actor.natural_armor > 0) cost += 1;
    return Math.max(1, cost);
  }

  function bfsReachable(tiles, exploredSet, sx, sy, maxSteps, result, moveCtx=null) {
    if (!moveCtx && gameState) moveCtx = { materiais: gameState.materiais,
      actor: (gameState.players || []).find(p => p.pos?.[0] === sx && p.pos?.[1] === sy) || {} };
    const openDoors = doorSets(gameState).open;
    const occupied  = _occupiedSet(sx, sy);
    const swampStart = moveCtx?.materiais?.[`${sx},${sy}`] === 'pantano';
    const q   = [[sx, sy, 0, swampStart]];
    const best = new Map([[`${sx},${sy},${swampStart ? 1 : 0}`, 0]]);
    while (q.length) {
      q.sort((a,b) => a[2]-b[2]);
      const [x, y, s, swampUsed] = q.shift();
      result.add(`${x},${y}`);
      if (s >= maxSteps) continue;
      for (const [dx, dy] of [[0,-1],[0,1],[-1,0],[1,0]]) {
        const nx = x+dx, ny = y+dy, k = `${nx},${ny}`;
        const rawCost = terrainMoveCost(moveCtx, nx, ny);
        const vooNoAr = !!(moveCtx?.actor?.voo && alturaDe(moveCtx.actor) > 0);
        const entersSwamp = moveCtx?.materiais?.[k] === 'pantano' && !swampUsed && !vooNoAr;
        // Garantia de uma casa: no primeiro passo, água cara ainda pode ser
        // atravessada mesmo se o orçamento não cobrir o custo inteiro.
        const terrainCost = rawCost + (entersSwamp ? 1 : 0);
        const nextCost = (s === 0 && terrainCost > maxSteps) ? maxSteps : s + terrainCost;
        const nextSwampUsed = swampUsed || entersSwamp;
        const bestKey = `${k},${nextSwampUsed ? 1 : 0}`;
        if (exploredSet.has(k) && nextCost <= maxSteps && _walkable(tiles, nx, ny, openDoors, occupied, moveCtx)
            && (best.get(bestKey) === undefined || nextCost < best.get(bestKey))) {
          best.set(bestKey, nextCost);
          q.push([nx, ny, nextCost, nextSwampUsed]);
        }
      }
    }
  }

  // ── Pure logic: BFS pathfinding — returns [[dx,dy],...] or null ────────────
  // Quando partial=true, se o alvo estiver além do orçamento ou separado por
  // uma porta fechada, retorna o trecho acessível que termina mais perto dele.
  function findPath(tiles, exploredSet, fx, fy, tx, ty, maxSteps, partial=false, moveCtx=null) {
    if (!moveCtx && gameState) moveCtx = { materiais: gameState.materiais,
      actor: (gameState.players || []).find(p => p.pos?.[0] === fx && p.pos?.[1] === fy) || {} };
    const openDoors = doorSets(gameState).open;
    const occupied  = _occupiedSet(fx, fy);
    if (!exploredSet.has(`${tx},${ty}`)) return null;
    const targetWalkable = _walkable(tiles, tx, ty, openDoors, occupied, moveCtx);
    if (!partial && !targetWalkable) return null;
    if (fx === tx && fy === ty) return [];
    const swampStart = moveCtx?.materiais?.[`${fx},${fy}`] === 'pantano';
    const q   = [[fx, fy, [], 0, swampStart]];
    const bestCost = new Map([[`${fx},${fy},${swampStart ? 1 : 0}`, 0]]);
    let best = { path: [], dist: Math.abs(fx-tx) + Math.abs(fy-ty) };
    while (q.length) {
      q.sort((a,b) => a[3]-b[3]);
      const [x, y, path, spent, swampUsed] = q.shift();
      if (spent >= maxSteps) continue;
      for (const [dx, dy] of [[0,-1],[0,1],[-1,0],[1,0]]) {
        const nx = x+dx, ny = y+dy, k = `${nx},${ny}`;
        const rawCost = terrainMoveCost(moveCtx, nx, ny);
        const vooNoAr = !!(moveCtx?.actor?.voo && alturaDe(moveCtx.actor) > 0);
        const entersSwamp = moveCtx?.materiais?.[k] === 'pantano' && !swampUsed && !vooNoAr;
        const terrainCost = rawCost + (entersSwamp ? 1 : 0);
        const nextCost = (spent === 0 && terrainCost > maxSteps) ? maxSteps : spent + terrainCost;
        const nextSwampUsed = swampUsed || entersSwamp;
        const bestKey = `${k},${nextSwampUsed ? 1 : 0}`;
        if (!exploredSet.has(k) || nextCost > maxSteps || !_walkable(tiles, nx, ny, openDoors, occupied, moveCtx)
            || (bestCost.get(bestKey) !== undefined && bestCost.get(bestKey) <= nextCost)) continue;
        const np = [...path, [dx, dy]];
        if (nx === tx && ny === ty) return np;
        const dist = Math.abs(nx-tx) + Math.abs(ny-ty);
        if (dist < best.dist) best = { path: np, dist };
        bestCost.set(bestKey, nextCost);
        q.push([nx, ny, np, nextCost, nextSwampUsed]);
      }
    }
    return partial && best.path.length ? best.path : null;
  }

  // ── WebSocket helpers ──────────────────────────────────────────────────────
  function send(obj) {
    if (PREVIEW) return false;   // prévia é só leitura: nenhuma ação sai daqui
    if (!ws || ws.readyState !== 1) return false;
    ws.send(JSON.stringify(obj));
    return true;
  }

  // ── Idioma ────────────────────────────────────────────────────────────────
  // O servidor traduz narração e erros no idioma de cada conexão; esta é a
  // única coisa que ele precisa saber. Guardado aqui para ser reenviado em toda
  // (re)conexão — inclusive no rejoin automático depois de uma queda.
  let myLang = 'pt';
  function setLang(code) {
    myLang = code;
    send({ type: 'set_lang', lang: code });
  }

  // ── Filtro de mensagens ───────────────────────────────────────────────────
  // O renderer registra aqui uma função aplicada a TODA mensagem que chega,
  // antes do despacho — hoje é a tradução dos nomes de catálogo. Este módulo
  // não conhece o I18N nem o dicionário (regra do CLAUDE.md: nada de window
  // aqui); ele só chama o que recebeu.
  let _messageFilter = null;
  function setMessageFilter(fn) {
    _messageFilter = (typeof fn === 'function') ? fn : null;
  }

  // ── Tradutor injetado ─────────────────────────────────────────────────────
  // Mesmo contrato do filtro acima, e pela mesma razão: o `t` global mora em
  // window.I18N, e este módulo não pode tocar em window (regra do CLAUDE.md).
  // Quem conhece o I18N é o game.js, que injeta a função no boot. Sem injeção
  // — ou se o tradutor lançar — cai no texto em português recebido, que é o
  // mesmo contrato de fallback do resto da etapa 5.
  let _traduz = null;
  // Nome do estado de fome/sede: chave por id, com o `nome` do próprio objeto
  // como fallback em português (mesmo contrato do _t).
  function _estadoNome(estado) {
    return _t('ui.sobrevivencia.estado.' + (estado && estado.id), (estado && estado.nome) || '');
  }
  function setTranslator(fn) {
    _traduz = (typeof fn === 'function') ? fn : null;
  }
  function _t(chave, pt, params) {
    if (!_traduz) return pt;
    try {
      const s = _traduz(chave, params);
      // Chave ausente: o I18N devolve a própria chave. Preferimos o português a
      // mostrar `ui.algo.assim` na tela.
      return (typeof s === 'string' && s && s !== chave) ? s : pt;
    } catch (e) { return pt; }
  }

  // ── Sessão para reconexão ────────────────────────────────────────────────
  // Guardada quando o lobby confirma a sala; persiste em localStorage para o
  // jogador voltar à partida mesmo após F5/queda (mensagem `rejoin` no servidor).
  let _sessUrl  = null;
  let _sessCode = null;
  let _rejoinTries = 0;
  let _rejoinTimer = null;
  const REJOIN_MAX = 8, REJOIN_DELAY_MS = 2500;

  function _saveSession() {
    if (!_sessUrl || !_sessCode || !myName) return;
    try {
      // pid é gravado para o Mestre: ele não aparece em players[] durante
      // city/dungeon (só master_pid identifica), então myPid nunca seria
      // reencontrado por nome após um F5/reconexão sem persistir o pid aqui.
      localStorage.setItem('lfh_session',
        JSON.stringify({ url: _sessUrl, code: _sessCode, name: myName, pid: myPid }));
    } catch (e) {}
  }
  function savedSession() {
    try { return JSON.parse(localStorage.getItem('lfh_session') || 'null'); }
    catch (e) { return null; }
  }
  function clearSession() {
    _sessCode = null;
    try { localStorage.removeItem('lfh_session'); } catch (e) {}
  }

  // Saída voluntária: interrompe a reconexão automática e descarta o estado
  // local antes de fechar o socket. A tela/DOM permanecem responsabilidade do
  // renderer (game.js).
  function leaveSession() {
    clearTimeout(_rejoinTimer);
    _rejoinTimer = null;
    _rejoinTries = REJOIN_MAX;
    clearSession();
    _sessUrl = null;
    const socket = ws;
    ws = null;
    myPid = null;
    gameState = null;
    lobbyState = null;
    cityState = null;
    isMyTurn = false;
    pendingMove = null;
    pendingSkill = null;
    pendingAction = null;
    pendingThrow = null;
    pendingInstrumento = null;
    activeShop = null;
    activeScene = null;
    pendingShopOpen = null;
    if (socket && socket.readyState < 2) { try { socket.close(); } catch (e) {} }
  }

  // Liga os callbacks comuns a connect() e rejoin().
  function _wireWs() {
    ws.onmessage = e => {
      try {
        _rejoinTries = 0;   // qualquer mensagem válida = conexão saudável
        let msg = JSON.parse(e.data);
        if (_messageFilter) {
          // Um filtro com defeito não pode derrubar a partida: se ele estourar,
          // a mensagem segue crua (em português) em vez de se perder.
          try { msg = _messageFilter(msg) || msg; }
          catch (err) { console.error('filtro de mensagem falhou:', err); }
        }
        _handle(msg);
      }
      catch (err) { console.error('WS parse/handle error:', err, e.data?.slice?.(0, 200)); }
    };
    ws.onerror = () => _emit('wsError');
    ws.onclose = () => {
      _emit('wsClosed', gameState, cityState);
      _scheduleRejoin();
    };
  }

  // Tenta religar sozinho após queda — só quando há uma partida em andamento.
  function _scheduleRejoin() {
    const fimDeJogo = gameState && gameState.phase === 'ended';
    if (!_sessCode || !myName || fimDeJogo) return;
    if (_rejoinTries >= REJOIN_MAX) { _emit('reconnectFailed'); return; }
    _rejoinTries++;
    _emit('reconnecting', _rejoinTries, REJOIN_MAX);
    clearTimeout(_rejoinTimer);
    _rejoinTimer = setTimeout(() => rejoin(), REJOIN_DELAY_MS);
  }

  // Reconecta usando a sessão atual (ou a salva em localStorage após F5).
  // Retorna false se não houver sessão para retomar.
  function rejoin() {
    const s = (_sessUrl && _sessCode && myName)
      ? { url: _sessUrl, code: _sessCode, name: myName }
      : savedSession();
    if (!s || !s.url || !s.code || !s.name) return false;
    if (ws && ws.readyState < 2) { try { ws.close(); } catch (e) {} }
    myName    = s.name;
    _sessUrl  = s.url;
    _sessCode = s.code;
    // Restaura o pid salvo — essencial para o Mestre: como ele não está em
    // players[] durante city/dungeon, o lookup por nome em lobby_state/
    // city_state/game_state (`if (!myPid) ...`) nunca o encontraria sozinho.
    if (s.pid) myPid = s.pid;
    ws = new WebSocket(s.url);
    ws.onopen = () => {
      send({ type: 'set_lang', lang: myLang });   // antes do rejoin: erros já chegam traduzidos
      send({ type: 'rejoin', code: s.code, name: s.name });
    };
    _wireWs();
    return true;
  }

  // connect(url, playerName, mode, code?)
  //   mode = 'create' → sends {type:'create_room', name}
  //   mode = 'join'   → sends {type:'join_room', name, code}
  function connect(url, name, mode, code) {
    if (ws && ws.readyState < 2) { try { ws.close(); } catch (e) {} }
    myName          = name;
    myPid           = null;
    gameState       = null;
    lobbyState      = null;
    cityState       = null;
    isMyTurn        = false;
    pendingShopOpen = null;
    _sessUrl        = url;
    _sessCode       = null;   // confirmado quando lobby_state chegar
    _rejoinTries    = 0;

    ws = new WebSocket(url);

    ws.onopen = () => {
      send({ type: 'set_lang', lang: myLang });   // antes de entrar: erros já chegam traduzidos
      if      (mode === 'create') send({ type: 'create_room', name });
      else if (mode === 'join')   send({ type: 'join_room',   name, code });
      else if (mode === 'test')   send({ type: 'join_test_dungeon', token: code });
      // mode 'login': não cria/entra em sala aqui; a UI dispara login/create_account.
    };

    _wireWs();
  }

  // ── Message handler (updates state, then fires renderer callback) ──────────
  function _handle(msg) {
    switch (msg.type) {

      case 'lobby_state':
        lobbyState = msg;
        if (!myPid) {
          const me = msg.players.find(p => p.name === myName);
          if (me) myPid = me.id;
        }
        // Sala confirmada → grava a sessão para reconexão (queda ou F5)
        if (msg.code) { _sessCode = msg.code; _saveSession(); }
        _emit('lobbyState', msg);
        break;

      case 'game_start':
        cityState = null;
        pendingMove = null;
        if (msg.instrumentos_base) instrumentoBaseCache = msg.instrumentos_base;
        _resetSurvivalAll(false);   // início da aventura → fome/sede = 80
        _resetTurnActivity();
        _emit('gameStart');
        break;

      case 'city_state':
        cityState = msg;
        pendingMove = null;
        // Descarta o estado da masmorra ANTERIOR (simétrico ao enter_dungeon, que
        // limpa cityState). Sem isto, os leitores que preferem gameState — como o
        // modal de inventário (_currentPlayer) — mostram o paperdoll/bolsa
        // congelados da última masmorra na cidade: a armadura recém-comprada entra
        // em cityState.gear mas o modal continua lendo o gameState velho (o item
        // aparece ao vender, que lê cityState, mas não no boneco). Cidade e masmorra
        // são fases mutuamente exclusivas no cliente.
        gameState = null;
        if (msg.guild && Array.isArray(msg.guild.catalog)) guildCatalogCache = msg.guild.catalog;
        _captarStory(msg);
        if (msg.active_scene) _emit('sceneStart', msg.active_scene);
        if (!myPid) {
          const me = msg.players.find(p => p.name === myName);
          if (me) myPid = me.id;
        }
        _emit('cityState', msg);
        break;

      case 'shop_result':
        _emit('shopResult', msg);
        break;

      case 'refugio_state':
        _emit('refugioState', msg);
        break;

      case 'quarto_state':
        _emit('quartoState', msg);
        break;

      case 'enter_dungeon':
        _resetSurvivalAll(true);    // pós-taverna/cidade → fome/sede = 100
        cityState = null;           // (após reset, p/ ler o roster da cidade)
        // Descarta o estado da masmorra ANTERIOR. Sem isso, o renderer 3D
        // reconstrói a cena (init3D) a partir do mapa antigo — causando "tela
        // preta"/mapa errado na 2ª+ entrada. O game_state fresco (enviado pelo
        // servidor logo após este enter_dungeon) reconstrói com o mapa correto.
        gameState = null;
        pendingMove = null;
        _resetTurnActivity();
        _emit('enterDungeon');
        break;

      case 'game_state':
        gameState = msg;
        _captarStory(msg);
        if (msg.active_scene) _emit('sceneStart', msg.active_scene);
        // A sessão de teste não passa pelo lobby, onde normalmente o Mestre
        // aprende seu pid. Sem isto ele era tratado como espectador: aguardava
        // jogadores e o render ocultava os monstros pela névoa.
        if (!myPid && msg.test_mode && msg.master_pid) myPid = msg.master_pid;
        if (!myPid) {
          const me = msg.players.find(p => p.name === myName);
          if (me) myPid = me.id;
        }
        isMyTurn = msg.test_mode ? msg.master_pid === myPid
          : msg.current_turn === myPid || msg.last_stand_pid === myPid
            || msg.animados_turn === myPid;
        // A prévia só permanece válida enquanto o herói continua na mesma
        // casa, com o mesmo orçamento de movimento e ainda no turno. Isso
        // evita confirmar uma rota velha depois de uma atualização autoritativa.
        if (pendingMove && myPid) {
          const pme = msg.players.find(p => p.id === myPid);
          const mesmaOrigem = pme && Array.isArray(pendingMove.origin)
            && pme.pos?.[0] === pendingMove.origin[0]
            && pme.pos?.[1] === pendingMove.origin[1];
          const mesmoOrcamento = pme && Number(pme.moves_left) === Number(pendingMove.moves_left);
          if (!isMyTurn || !mesmaOrigem || !mesmoOrcamento) pendingMove = null;
        }
        // (Sobrevivência cliente 0–100 desativada — fome/sede são autoritativos do
        // servidor, escala 0–100. Sem consumo/colapso fantasma no cliente.)
        // Auto-clear pending skill when turn ends or action was processed
        if (pendingSkill && myPid) {
          const sme = msg.players.find(p => p.id === myPid);
          if (!isMyTurn || (sme && sme.action_done)) pendingSkill = null;
        }
        if (pendingInstrumento && myPid) {
          const sme = msg.players.find(p => p.id === myPid);
          if (!isMyTurn || (sme && sme.action_done)) pendingInstrumento = null;
        }
        // Warrior: ao deixar de ser meu turno, descarta habilidades armadas
        // (no próximo turno ficam selecionáveis de novo).
        if (warriorSelected.length && !isMyTurn) warriorSelected = [];
        _emit('gameState', msg);
        break;

      case 'scene_start':
        _emit('sceneStart', { scene: msg.scene, session: msg.session, paused: msg.paused });
        break;
      case 'scene_branch': _emit('sceneBranch', msg); break;
      case 'scene_test_result': _emit('sceneTestResult', msg); break;
      case 'scene_end_warning': _emit('sceneEndWarning', msg); break;
      case 'scene_end': _emit('sceneEnd', msg); break;

      case 'gm_narration':
        _emit('gmNarration', msg.text);
        break;

      case 'ability_activation':
        _emit('abilityActivation', msg);
        break;

      case 'fala':
        _emit('fala', msg);   // {falante:{nome,emoji}, texto, pos}
        break;

      case 'game_over':
        clearSession();   // aventura encerrada — não tentar reconectar depois
        _captarStory(msg);
        _emit('gameOver', msg);
        break;

      case 'dice_roll':
        _emit('diceRoll', msg);
        break;

      case 'attack_feedback':
        // Evento exclusivamente visual: o servidor já resolveu o ataque.
        _emit('attackFeedback', msg);
        break;

      case 'spell_animation':
        // Evento visual autoritativo (o caminho já foi resolvido pelo servidor).
        // O módulo de estado só roteia a mensagem; a animação pertence ao
        // renderer em game.js.
        _emit('spellAnimation', msg);
        break;

      case 'sorte_reacao':
        _emit('sorteReacao', msg);
        break;

      case 'trap_result':
        _emit('trapResult', msg);
        break;

      case 'fall_result':
        // A queda já foi resolvida pelo servidor; o renderer só apresenta o
        // resultado junto dos demais eventos de combate.
        _emit('fallResult', msg);
        break;

      case 'fire_prompt':
        _emit('firePrompt', msg);
        break;

      case 'condition_result':
        _emit('conditionResult', msg);
        break;

      case 'disease_result':
        _emit('diseaseResult', msg);
        break;

      case 'curse_result':
        _emit('curseResult', msg);
        break;

      case 'poison_result':
        _emit('poisonResult', msg);
        break;

      case 'equipment_damage_result':
        _emit('equipmentDamageResult', msg);
        break;

      case 'petrify_result':
        _emit('petrifyResult', msg);
        break;

      case 'mental_control_result':
        _emit('mentalControlResult', msg);
        break;

      case 'acid_spit_result':
        _emit('acidSpitResult', msg);
        break;

      case 'magic_damage_failure_result':
        _emit('magicDamageFailureResult', msg);
        break;

      case 'freezing_result':
        _emit('freezingResult', msg);
        break;

      case 'stun_result':
        _emit('stunResult', msg);
        break;

      case 'death_result':
        _emit('deathResult', msg);
        break;

      case 'sleep_result':
        _emit('sleepResult', msg);
        break;

      case 'animar_result':
        // Resultado autoritativo de Animar Mortos: sincroniza a lista de
        // animados do Pedro (modelo client-side) e repassa ao renderer, que
        // dispara a animação D100 e atualiza a ficha.
        if (HERO_DATA.pedro && Array.isArray(msg.animados)) {
          HERO_DATA.pedro.animados = msg.animados;
        }
        _emit('animarResult', msg);
        break;

      case 'entity_step':
        // Deslize fiel de 1 casa (monstro inimigo / servo auto-comandado).
        // O renderer interpola from→to; o game_state seguinte reconcilia.
        _emit('entityStep', msg);
        break;

      case 'explosion_area':
        _emit('explosionArea', msg);
        break;

      case 'spell_pick_prompt':
        _emit('spellPickPrompt', msg);   // {circulo, count, opcoes}
        break;

      case 'decor_loot':
        _emit('decor_loot', msg);
        break;

      case 'decor_mechanism':
        _emit('decor_mechanism', msg);
        break;

      case 'improviso_resultado':
        // Cascata 2d6 da Gaita (Fase 5) — quadro de resultado + fila de mira
        // dos passos que precisam de alvo (ver renderImprovisoQuadro em game.js).
        _emit('improvisoResultado', msg);
        break;

      case 'login_result':
        if (msg.ok) {
          account = msg.username;
          // O servidor normaliza o apelido (minúsculas) e o usa como nome do
          // jogador na sala do jogo salvo. Alinhar myName evita que a resolução
          // de myPid (por nome, em lobby/city/game_state) falhe por caixa.
          myName = msg.username;
        }
        _emit('loginResult', msg);   // {ok, username, error}
        break;

      case 'savegames_list':
        savegames = msg.savegames || [];
        // Cache "grudento": só substitui se a mensagem trouxer campaigns. Assim um
        // savegames_list parcial (ex.: resposta de apagar) não zera as campanhas já
        // conhecidas — o que esvaziava o seletor de campanha da tela "Meus Jogos".
        if (msg.campaigns) campaignsCache = msg.campaigns;
        _emit('savegamesList', savegames);
        break;

      case 'savegame_created':
        _emit('savegameCreated', msg.savegame);
        break;

      case 'campaign_vote_opened':
      case 'campaign_vote_updated':
        _emit('campaignVote', msg);
        break;

      case 'error':
        _emit('serverError', msg.msg);
        break;
    }
  }

  // ── Action senders (thin wrappers over send) ───────────────────────────────
  function move(dx, dy)    { _turn.moved = true; send({ type: 'move', dx, dy }); }
  function alterarAltura(delta, monsterId = null) {
    const msg = { type: 'alterar_altura', delta: Number(delta) };
    if (monsterId != null) msg.monster_id = monsterId;
    send(msg);
  }
  function endTurn()       {
    // Consumo de fome/sede é 100% autoritativo do servidor (escala 0–100).
    // O antigo consumo cliente foi desativado.
    // Habilidades do guerreiro só valem para o ataque que as envia. Encerrar o
    // turno sem atacar as descarta localmente, sem custo e sem gastar a
    // especialização de combinação da Guilda.
    clearWarriorSelected();
    return send({ type: 'end_turn' });
  }
  function sceneChoice(sceneId, eventId, optionId) { send({ type:'scene_choice', scene_id:sceneId, event_id:eventId, option_id:optionId }); }
  function sceneTest(sceneId, eventId) { send({ type:'scene_test', scene_id:sceneId, event_id:eventId }); }
  function sceneEnd(force) { send({ type:'scene_end', force:!!force }); }
  function sceneVisit(sceneId, eventId) { send({ type:'scene_visit', scene_id:sceneId, event_id:eventId }); }
  function setTurnTimer(enabled) { send({ type:'set_turn_timer', enabled:!!enabled }); }
  function setShortcut(slot, entry) { send({ type:'shortcut_set', slot, entry:entry || null }); }
  function shortcutActivated(entry, slot = null) {
    if (!entry || entry.kind !== 'skill' || !entry.id) return;
    const msg = { type:'shortcut_activate', entry: { kind:'skill', id:String(entry.id), source:entry.source || 'skill' } };
    if (Number.isInteger(slot) && slot >= 0 && slot < 10) msg.slot = slot;
    send(msg);
  }
  function useItem(id)     { send({ type: 'use_item',       item_id: id }); }
  function respondFireChoice(choice) {
    const value = ['water', 'action', 'none'].includes(choice) ? choice : 'none';
    send({ type: 'fire_choice', choice: value });
  }
  function throwItem(id, targetId, targetPos) { send({ type: 'throw_item', item_id: id, target_id: targetId, target_pos: targetPos }); }
  function throwItemArea(id, tx, ty) { send({ type: 'throw_item', item_id: id, tx, ty }); }
  // Arremesso de arma equipada. O slot é parte da ação para que o servidor
  // não precise adivinhar entre uma arma principal e uma segunda arma.
  function throwWeapon(slot, targetId) { send({ type: 'throw', slot, target_id: targetId }); }
  function apagarChamas()          { send({ type: 'apagar_chamas' }); }
  function estancarSangramento()   { send({ type: 'estancar_sangramento' }); }
  function escaparEstomago()       { send({ type: 'escapar_estomago' }); }
  function escaparBau()             { send({ type: 'escapar_bau' }); }
  function equipFromBag(i) { send({ type: 'equip_from_bag', slot_index: i }); }
  function quickEquipFromBag(i) { send({ type: 'quick_equip_from_bag', slot_index: i }); }
  function unequip(key)    { send({ type: 'unequip',        slot_key: key }); }
  function repairItem(slot, bagIndex = null) {
    send({ type: 'repair_item', slot, bag_index: bagIndex });
  }
  // Largar/pegar itens no chão (masmorra). Largar: source 'bag' → ref = index;
  // 'gear' → ref = slotKey. Pegar: id do item no chão.
  function dropItem(source, ref) {
    if (source === 'bag') send({ type: 'drop_item', source: 'bag',  index: ref });
    else                  send({ type: 'drop_item', source: 'gear', slot_key: ref });
  }
  function pickupItem(id) { send({ type: 'pickup_item', ground_id: id }); }
  // Resolver puro: item do chão é pegável por `player`? (adjacência Chebyshev ≤1)
  function groundItemPickable(gi, player) {
    if (!gi || !player || !player.pos) return false;
    return Math.max(Math.abs(player.pos[0] - gi.pos[0]),
                    Math.abs(player.pos[1] - gi.pos[1])) <= 1;
  }
  function reorderBag(fromIndex, toIndex) { send({ type: 'reorder_bag', from_index: fromIndex, to_index: toIndex }); }
  function equipOffhand(i)                { send({ type: 'equip_offhand',   slot_index: i }); }
  // Magias conhecidas (Pedro/Lewis): escolha de 2 magias de 1º círculo no lobby.
  function setKnownSpells(ids)       { send({ type: 'set_known_spells', ids }); }
  // Escolha da nova magia ao subir de nível (responde ao spell_pick_prompt).
  function escolherMagiaNivel(id)    { send({ type: 'escolher_magia_nivel', magia_id: id }); }
  // Animar Mortos (Pedro): anima o cadáver selecionado a até 3 casas.
  function animarMortos(cadaverId, versao) {
    const msg = { type: 'animar_mortos', cadaver_id: cadaverId };
    if (versao) msg.versao = versao;
    send(msg);
  }
  // Comanda os animados (ação bônus do Pedro): cada um move+ataca o monstro mais próximo.
  function comandarAnimados() { send({ type: 'comandar_animados' }); }
  // Controle manual de UM animado (no turno do Pedro).
  function moverAnimado(animadoId, dx, dy) { send({ type: 'mover_animado', animado_id: animadoId, dx, dy }); }
  function atacarAnimado(animadoId, targetId) { send({ type: 'atacar_animado', animado_id: animadoId, target_id: targetId }); }
  function usarHabilidadeAnimado(animadoId, abilityId, targetId) {
    send({ type: 'usar_habilidade_animado', animado_id: animadoId, ability_id: abilityId, target_id: targetId });
  }
  // Controle manual do prisioneiro liberto (janela pós-turno do resgatador) — 1 passo.
  function moverPrisioneiro(dx, dy) { send({ type: 'mover_prisioneiro', dx, dy }); }
  // ── Armadilhas (Passo 2) — Luccas cria/desarma armadilhas colocáveis ───────
  // tipo: id em ARMADILHAS (servidor). tx/ty opcionais (default = casa do Luccas).
  // venenoId só para 'fosso_envenenado' (consome 1 frasco da bolsa).
  function criarArmadilha(tipo, tx, ty, venenoId) {
    const msg = { type: 'criar_armadilha', tipo };
    if (tx !== undefined && tx !== null) { msg.tx = tx; msg.ty = ty; }
    if (venenoId) msg.veneno_id = venenoId;
    send(msg);
  }
  function desarmarArmadilha(tx, ty) {
    const msg = { type: 'desarmar_armadilha' };
    if (tx !== undefined && ty !== undefined) { msg.tx = tx; msg.ty = ty; }
    send(msg);
  }

  // ── Modo Mestre Jogador (Fase A) ────────────────────────────────────────
  // Assento no lobby: role = 'master' | 'hero'.
  function claimRole(role) { send({ type: 'claim_role', role }); }
  // Seleção em lote — troca o modo de controle de 1+ monstros.
  function mestreSetModo(monsterIds, modo) { send({ type: 'mestre_set_modo', monster_ids: monsterIds, modo }); }
  // Atribui alvo (herói) a monstros em modo Semi.
  function mestreSetAlvo(monsterIds, targetId) { send({ type: 'mestre_set_alvo', monster_ids: monsterIds, target_id: targetId }); }
  // Janela Manual: move o monstro 1 passo ortogonal.
  function mestreMoverMonstroPara(monsterId, tx, ty) { send({ type: 'mestre_mover_monstro_para', monster_id: monsterId, tx, ty }); }
  function mestreUsarHabilidade(monsterId, abilityId, targetId, tipoEsqueleto) {
    const msg = { type: 'mestre_usar_habilidade', monster_id: monsterId, ability_id: abilityId, target_id: targetId };
    if (tipoEsqueleto) msg.tipo_esqueleto = tipoEsqueleto;
    send(msg);
  }
  function mestreUsarMagia(monsterId, spellId, targetId, tx, ty, dir) {
    const msg = { type: 'mestre_usar_magia', monster_id: monsterId, spell_id: spellId, target_id: targetId };
    if (tx !== undefined && ty !== undefined) { msg.tx = tx; msg.ty = ty; }
    if (Array.isArray(dir)) msg.dir = dir;
    send(msg);
  }
  function mestreUsarItem(monsterId, itemId, targetId, tx, ty) { send({ type: 'mestre_usar_item', monster_id: monsterId, item_id: itemId, target_id: targetId, tx, ty }); }
  // Janela Manual: o monstro ataca um herói.
  function mestreAtacarMonstro(monsterId, targetId, attackIndex) {
    send({ type: 'mestre_atacar_monstro', monster_id: monsterId, target_id: targetId,
           attack_index: (attackIndex == null ? 0 : attackIndex) });
  }
  // Janela Manual: encerra a vez do monstro.
  function mestreEncerrarMonstro(monsterId) { send({ type: 'mestre_encerrar_monstro', monster_id: monsterId }); }
  function mestreSelecionarTeste(monsterId) { send({ type: 'mestre_selecionar_teste', monster_id: monsterId }); }
  // Camada B: implanta um reforço da reserva do mestre numa casa livre.
  function mestreImplantarReforco(monsterType, tx, ty) { send({ type: 'mestre_implantar_reforco', monster_type: monsterType, tx, ty }); }
  // Falas de NPC: o mestre dispara uma fala com gatilho manual.
  function dispararFala(falaId) { send({ type: 'disparar_fala', fala_id: falaId }); }
  // true se o jogador local é o mestre (checa lobby/city/game — o mestre não
  // aparece em players[] durante city/dungeon, só master_pid identifica).
  function isMaster() {
    const st = lobbyState || cityState || gameState;
    return !!(st && st.master_pid && st.master_pid === myPid);
  }
  function isCommandController() {
    return !!(gameState && (
      (gameState.command_control_pid === myPid && gameState.command_control) ||
      (gameState.mind_control_pid === myPid && gameState.mind_control)
    ));
  }
  function canControlMonster() { return isMaster() || isCommandController(); }
  // Prévia do editor: injeta um game_state pelo MESMO caminho de um estado
  // vindo do servidor, sem socket e sem duplicar normalização. Adotar o
  // master_pid do payload liga isMaster() → mapa inteiro à vista, sem névoa.
  function injectPreviewState(msg) {
    myPid  = msg.master_pid;
    myName = 'Prévia';
    _handle(msg);
  }
  // Id do monstro atualmente na janela Manual (ou null) — só existe em gameState.
  function masterManualMid() { return (gameState && gameState.master_manual_mid) || null; }
  // Bloco da janela Manual (null fora dela). Ver _master_manual_payload no servidor.
  function masterManual() {
    return (gameState && (gameState.master_manual || gameState.command_control || gameState.mind_control)) || null;
  }
  // Cargas restantes de um golpe pelo índice em attacks[]. O payload vem com
  // chaves string (JSON não tem chave inteira), por isso o String(idx).
  function masterAttackCharges(idx) {
    const mm = masterManual();
    if (!mm) return 0;
    return (mm.attack_charges || {})[String(idx)] || 0;
  }
  // true se a ação principal ainda pode virar ataque neste turno: ou está livre,
  // ou já foi comprometida com ataques e ainda restam cargas.
  function masterPodeAtacar() {
    const mm = masterManual();
    if (!mm) return false;
    return mm.acao == null || mm.acao === 'ataque';
  }

  // ── Tutorial ── Lição pendente do MEU herói, ou null. Leitura pura: o bloco
  // vem chaveado por classe porque game_state é um broadcast único.
  function licaoAtual() {
    if (!gameState || !gameState.tutorial) return null;
    const me = (gameState.players || []).find(p => p.id === myPid);
    if (!me || !me.class_id) return null;
    const lic = (gameState.tutorial.por_classe || {})[me.class_id];
    return (lic && lic.licao_id) ? lic : null;
  }

  // ── Guilda dos Heróis (Fase 0) ──────────────────────────────────────────
  function guildBuy(itemId)           { send({ type: 'guild_buy',   item_id: itemId }); }
  function worldTravel(destination)   { send({ type: 'world_travel', destination: destination }); }
  function worldAdventure(adventureId) { send({ type: 'world_adventure', adventure_id: adventureId }); }
  function talkSceneNpc(sceneId, npcId, conversationId) {
    send({ type: 'scene_npc', scene_id: sceneId, npc_id: npcId, conversation_id: conversationId });
  }
  // Cenas de conversa da cidade atual, como vieram do servidor.
  function scenes() { return (cityState && cityState.scenes) || {}; }
  // Pontos do mapa da cidade atual.
  function cityPoints() {
    const loc = cityState && cityState.world && cityState.world.location;
    return ((cityState && cityState.city_map_points) || {})[loc] || {};
  }
  // Id da cena vinculada a um ponto (null se o ponto não abre cena nenhuma).
  function sceneIdOfPoint(pointId) { return (cityPoints()[pointId] || {}).scene || null; }
  // A cena em si, ou null.
  function sceneOfPoint(pointId) {
    const ref = sceneIdOfPoint(pointId);
    return ref ? (scenes()[ref] || null) : null;
  }
  function saveWorldMapPoints(points) { send({ type: 'world_map_points', points: points }); }
  function saveCityMapPoints(cityId, points) { send({ type: 'city_map_points', city_id: cityId, points: points }); }
  function openRefugio() { send({ type: 'open_refugio' }); }
  function openQuarto(owner) { send({ type: 'open_quarto', owner: owner || null }); }
  function refugioStore(scope, source, ref) {
    const msg = { type:'refugio_store', scope, source };
    if(source === 'bag') msg.index = ref; else msg.slot_key = ref;
    send(msg);
  }
  function refugioTake(scope, index) { send({ type:'refugio_take', scope, index }); }
  function refugioGold(scope, action, amount) { send({ type:'refugio_gold', scope, action, amount }); }
  function quartoCustomize(background, trophies) { send({ type:'quarto_customize', background, trophies }); }
  function guildEquip(slot, itemId)   { send({ type: 'guild_equip', slot: slot, item_id: itemId }); }
  function usarTecnica(tid, targetId) { send({ type: 'usar_tecnica', tecnica_id: tid, target_id: targetId != null ? targetId : null }); }
  function responderSorteReacao(usar) { send({ type: 'sorte_reacao', usar: !!usar }); }
  function usarOportunidadeMovimento() { send({ type: 'usar_oportunidade_movimento' }); }
  // Getters puros: catálogo filtrado por classe, itens possuídos e equipados
  // pelo jogador (lidos de cityState.guild), e recarga restante de uma técnica
  // (lida de game_state.players[].technique_cooldowns + gameState.round).
  // Catálogo: na cidade vem em cityState.guild; na masmorra usa o cache (cityState=null).
  function guildCatalogFor(classId) {
    const catalog = (cityState && cityState.guild && cityState.guild.catalog) || guildCatalogCache || [];
    return catalog.filter(i => i.classe == null || i.classe === classId
      || (Array.isArray(i.classe) && i.classe.includes(classId)));
  }
  // Owned/equip: na cidade vêm de cityState.guild.players[pid]; na masmorra caem
  // para o player do game_state (que carrega guild_owned/guild_equip inteiros).
  function guildOwnedOf(pid) {
    const g = (cityState && cityState.guild) || null;
    if (g && g.players && g.players[pid] && g.players[pid].owned) return g.players[pid].owned;
    const gp = (gameState && gameState.players || []).find(p => p.id === pid);
    return (gp && gp.guild_owned) || { especializacoes: [], tecnicas: [] };
  }
  function guildEquipOf(pid) {
    const g = (cityState && cityState.guild) || null;
    const raw = (g && g.players && g.players[pid] && g.players[pid].equip)
      || ((gameState && gameState.players || []).find(p => p.id === pid) || {}).guild_equip;
    if (raw && Array.isArray(raw.tecnicas)) return { ...raw, tecnica: raw.tecnicas[0] || null };
    // Compatibilidade com estados/saves enviados antes dos slots genéricos.
    return { tecnicas: [raw && raw.tecnica || null] };
  }
  // Recarga restante (em rodadas) de uma técnica, lido do game_state.
  function tecnicaRestante(player, tid) {
    const cds = (player && player.technique_cooldowns) || {};
    const pronta = cds[tid];
    const round = (gameState && gameState.round) || 1;
    return pronta ? Math.max(0, pronta - round) : 0;
  }
  function tecnicaPendente(player, tid) {
    return !!(player && player.technique_pending && player.technique_pending[tid]);
  }
  // Fase I: técnicas concedidas por itens equipados (ids SEM o prefixo guild_).
  function tecnicasConcedidasPorItem(player) {
    const out = [];
    const gear = (player && player.gear) || {};
    Object.keys(gear).forEach(k => {
      const it = gear[k];
      const aid = it && it.granted_ability;
      if (aid && aid.indexOf('guild_') === 0) {
        const tid = aid.slice(6);
        if (out.indexOf(tid) < 0) out.push(tid);
      }
    });
    return out;
  }
  function sorrateiroAtivo() {
    return guildEquipOf(myPid).tecnicas.includes('sorrateiro');
  }

  // ── Instrumentos do Bardo (Fase 1/2) ─────────────────────────────────────
  // dir: [dx,dy] opcional — usado pela Trompa (Chamado do General, mira por
  // direção, mesmo padrão da Relâmpago). As demais habilidades não usam dir.
  function usarInstrumento(target, dir) {
    send({ type: 'usar_instrumento',
           target_id: (target && target.id != null) ? target.id : null,
           dir: dir || null });
  }
  function instrumentoBase(baseId) {
    return (instrumentoBaseCache && instrumentoBaseCache[baseId]) || null;
  }
  // O instrumento vive na mão do escudo (off_hand). Só conta se for de fato um
  // instrumento (o off_hand também pode ter escudo/2ª arma).
  function instrumentoEquipadoDe(pid) {
    const src = gameState || cityState;
    const gp = (src && src.players || []).find(p => p.id === pid);
    const inst = gp && gp.gear && gp.gear.off_hand;
    return (inst && inst.tipo_item === 'instrumento') ? inst : null;
  }
  // Porta leve de _instrumento_stats (só p/ rótulos; o servidor é autoritativo).
  function instrumentoStatsClient(inst) {
    const b = instrumentoBase(inst && inst.base);
    if (!b) return null;
    const q = inst.qualidade === 'refinado' ? 'padrao' : inst.qualidade;
    const st = Object.assign({}, b.stats[q]);
    st.custo_fome = b.custo_fome; st.custo_sede = b.custo_sede;
    const afixo = (bonus) => {
      if (bonus === 'fome') st.custo_fome -= 1;
      else if (bonus === 'sede') st.custo_sede -= 1;
      else if (bonus === 'fome_sede') { st.custo_fome -= 1; st.custo_sede -= 1; }
      else if (bonus === 'alcance') { if ('alcance' in st) st.alcance += 1; if ('raio' in st) st.raio += 1; if ('cone' in st) st.cone += 1; }
      else if (bonus === 'duracao') { if ('duracao' in st) st.duracao += 1; }
      else if (bonus === 'cd') st.cd_bonus = (st.cd_bonus || 0) + 1;
    };
    if (inst.qualidade === 'refinado') afixo(inst.refinado_bonus);
    if (inst.origem_bonus) afixo(inst.origem_bonus);
    if (inst.encantamento === 'runico' && b.runico) {   // camada Rúnica (Fase 4b)
      const r = b.runico;
      if ('dano_set' in r) st.dano = r.dano_set;
      if ('duracao_delta' in r && 'duracao' in st) st.duracao += r.duracao_delta;
      if ('medo_delta' in r && 'medo' in st) st.medo += r.medo_delta;
    }
    st.custo_fome = Math.max(0, st.custo_fome);
    st.custo_sede = Math.max(0, st.custo_sede);
    return st;
  }
  function instrumentoDisponivel(player) {
    const inst = player && player.gear && player.gear.off_hand;
    if (!inst || inst.tipo_item !== 'instrumento') return false;
    const b = instrumentoBase(inst.base);
    if (!b || b.modo !== 'ativada') return false;
    if (player.instrumento_usado) return false;
    if (b.maos === 2 && player.action_done) return false;
    return true;
  }
  // Fase 5 (Gaita/Improviso) — mira, em sequência, os passos pendentes da
  // cascata (res 7/9/11: Nota Cortante/Réquiem/Chamado do General
  // improvisados). O servidor resolve o 1º da fila (FIFO) a cada chamada.
  function improvisoAlvo(targetId, dir) {
    send({ type: 'improviso_alvo',
           target_id: targetId != null ? targetId : null,
           dir: dir || null });
  }

  // ── Editor de masmorras — seleção de dungeon ─────────────────────────────────
  // file: nome do arquivo da masmorra autoral, ou null para modo procedural.
  function selectDungeon(file) { send({ type: 'select_dungeon', file: file || null }); }
  // Armadilha colocável na casa do herói local OU cardinalmente adjacente — ou null.
  // Decisor puro p/ o renderer habilitar o botão de desarmar.
  function armadilhaAdjacente() {
    if (!gameState) return null;
    const myP = gameState.players.find(p => p.id === myPid && p.alive);
    if (!myP) return null;
    const arms = gameState.armadilhas || [];
    return arms.find(a => {
      const dx = Math.abs(myP.pos[0] - a.pos[0]);
      const dy = Math.abs(myP.pos[1] - a.pos[1]);
      return (dx + dy) <= 1;   // mesma casa ou cardinal adjacente
    }) || null;
  }
  // Cadáver no alcance de Animar Mortos (Chebyshev ≤ 3) ao herói local — ou null.
  // usado pelo renderer para habilitar/disparar Animar Mortos.
  function cadaverAdjacente() {
    if (!gameState) return null;
    const myP = gameState.players.find(p => p.id === myPid && p.alive);
    if (!myP) return null;
    const corpses = gameState.corpses || [];
    return corpses.find(c => {
      const dx = Math.abs(myP.pos[0] - c.pos[0]);
      const dy = Math.abs(myP.pos[1] - c.pos[1]);
      return Math.max(dx, dy) <= 3;
    }) || null;
  }

  // ── Inventário estilo Diablo — helpers puros (paperdoll/bolsa) ─────────────
  // Espelha server._slot_category_for_item (server.py) — client-side, só p/
  // feedback visual instantâneo. O servidor continua autoritativo: qualquer
  // rejeição real chega via mensagem `error`, o preview client-side é só uma
  // previsão.
  function _slotCategoryForItem(item){
    const s   = (item.item_slot || '').toLowerCase();
    const k   = (item.kind || '').toLowerCase();
    const iid = (item.id || '').toLowerCase();
    const nm  = (item.name || '').toLowerCase();
    // Instrumento do Bardo (Fase 1) vive na mão do escudo (off_hand) — espelha
    // server._slot_category_for_item; checado antes das demais categorias.
    if(s === 'instrumento' || item.tipo_item === 'instrumento') return 'off_hand';
    if(s === 'weapon' || k === 'weapon') return 'weapon';
    if(s === 'shield' || s === 'off_hand' || k === 'shield' || iid.includes('shield') || nm.includes('escudo')) return 'off_hand';
    if(s === 'ammo' || item.effect === 'ammo') return 'off_hand';
    if(s === 'head' || k === 'head' || ['elmo','capuz','tiara','capacete'].some(w => nm.includes(w))) return 'head';
    // !s: item_slot explícito vence name-sniffing — evita reclassificar itens
    // legados tipo "Botas Velozes" (item_slot="item"/"accessory") como boots
    // (mesma regressão corrigida no server em 93a4486).
    if(s === 'boots' || k === 'boots' || (!s && ['bota','botas','sapato'].some(w => nm.includes(w)))) return 'boots';
    if(s === 'ring' || k === 'ring' || nm.includes('anel')) return 'ring';
    if(['accessory','belt','gloves','backpack','item'].includes(s) ||
       ['accessory','belt','gloves','backpack'].includes(k) ||
       ['mochila','alforje','luva','cinto'].some(w => nm.includes(w))) return 'item';
    if(s === 'armor' || k === 'armor') return 'armor';
    if(item.die) return 'weapon';
    return 'bag';
  }

  // Adaga/chicote usáveis como 2ª arma (dual-wield) — mesma heurística já usada 2x em
  // game.js (_fcEhAdaga/ehAdaga), centralizada aqui p/ o modal novo não duplicar.
  function isDagger(item){
    if(!item) return false;
    const iid = (item.id || '').toLowerCase();
    const nm  = (item.name || '').toLowerCase();
    // Casa exatamente server._eh_adaga (server.py): startswith, não ===, p/
    // cobrir futuras variantes tipo "dagger_ferro".
    return (iid.startsWith('dagger') || nm.includes('adaga')) && !!(item.die || item.dano);
  }

  function isOffhandWeapon(item){
    if(!item || !(item.die || item.dano)) return false;
    const iid = (item.id || '').toLowerCase();
    const nm = (item.name || '').toLowerCase();
    return !!item.off_hand_weapon || isDagger(item) || iid === 'chicote' || nm.includes('chicote');
  }

  // Fonte única: a mão secundária fica bloqueada quando a arma principal é de
  // duas mãos. Consultada tanto por canPlaceItem quanto pelo renderer do
  // paperdoll (inventoryModal.js) p/ não duplicar a regra em dois lugares.
  function offHandBlockedByTwoHanded(gearSnapshot){
    const weapon = (gearSnapshot || {}).weapon;
    return !!(weapon && weapon.two_handed);
  }

  // gearSnapshot = objeto gear atual (p/ checar conflito de arma de 2 mãos).
  function canPlaceItem(item, slotKey, gearSnapshot){
    if(!item || !slotKey) return false;
    const cat = _slotCategoryForItem(item);
    if(cat === 'bag') return false;   // consumível não equipa em slot nenhum
    const gear = gearSnapshot || {};
    if(slotKey === 'weapon'){
      if(cat !== 'weapon') return false;
      if(item.two_handed){
        const off = gear.off_hand;
        const offOcupaMao = !!off && (off.kind === 'shield' || off.item_slot === 'shield' || !!off.die);
        if(offOcupaMao) return false;
      }
      return true;
    }
    if(slotKey === 'off_hand'){
      const isOffhandCat = cat === 'off_hand';
      if(!isOffhandCat && !isOffhandWeapon(item)) return false;
      if(offHandBlockedByTwoHanded(gear)) return false;
      return true;
    }
    if(slotKey === 'armor') return cat === 'armor';
    if(slotKey === 'head')  return cat === 'head';
    if(slotKey === 'boots') return cat === 'boots';
    if(slotKey === 'ring1' || slotKey === 'ring2') return cat === 'ring';
    if(slotKey === 'item1' || slotKey === 'item2') return cat === 'item';
    return false;
  }

  // Compara dois itens no formato de GS.CATALOGO_ITENS (bonusCA numérico,
  // dano em notação de dado tipo "1d8") pra tooltip com setas ↑/↓. Só compara
  // campos presentes em pelo menos um dos dois lados.
  function _diceAverage(diceStr){
    if(!diceStr) return null;
    const m = /^(\d+)d(\d+)$/.exec(String(diceStr).trim());
    if(!m) return null;
    const n = Number(m[1]), sides = Number(m[2]);
    return n * (sides + 1) / 2;
  }
  function compareItemStats(newItem, equippedItem){
    if(!newItem) return [];
    const fields = [
      { key: 'bonusCA', label: 'CA',   fmt: v => `+${v}` },
      { key: 'dano',    label: 'Dano', fmt: v => v, numeric: _diceAverage },
    ];
    const rows = [];
    for(const f of fields){
      const hasNew = newItem[f.key] != null;
      const hasOld = !!equippedItem && equippedItem[f.key] != null;
      if(!hasNew && !hasOld) continue;
      const newVal = hasNew ? (f.numeric ? f.numeric(newItem[f.key]) : newItem[f.key]) : null;
      const oldVal = hasOld ? (f.numeric ? f.numeric(equippedItem[f.key]) : equippedItem[f.key]) : null;
      let arrow = null;
      if(newVal != null && oldVal != null){
        if(newVal > oldVal) arrow = 'up';
        else if(newVal < oldVal) arrow = 'down';
      }
      rows.push({
        label: f.label,
        newDisplay: hasNew ? f.fmt(newItem[f.key]) : '—',
        oldDisplay: hasOld ? f.fmt(equippedItem[f.key]) : '—',
        arrow,
      });
    }
    return rows;
  }

  // ── Decorações de masmorra ────────────────────────────────────────────────────
  // Helper puro: retorna a lista de tiles [[x,y],...] ocupados por uma decoração.
  // Espelha _decor_tiles_at do servidor: o servidor já envia d.tiles resolvido;
  // se faltar, recalcula pelo size/facing (facing horizontal troca w↔h).
  function decorTilesOf(d) {
    if (Array.isArray(d.tiles)) return d.tiles;
    const [w, h] = d.size || [1, 1];
    const [ew, eh] = (d.facing && d.facing[0] !== 0) ? [h, w] : [w, h];
    const out = [];
    for (let i = 0; i < ew; i++) for (let j = 0; j < eh; j++) out.push([d.pos[0] + i, d.pos[1] + j]);
    return out;
  }
  // Senders: interação com decoração (fonte/loot) e retirada de item de decoração.
  function interagirDecor(decorId) { send({ type: 'interagir_decor', decor_id: decorId }); }
  function takeFromDecor(decorId, kind, index) { send({ type: 'take_from_decor', decor_id: decorId, kind, index }); }
  function takeAllFromDecor(decorId) { send({ type: 'take_all_from_decor', decor_id: decorId }); }
  function activateDecorMechanism(decorId) { send({ type: 'activate_decor_mechanism', decor_id: decorId }); }

  // ── Fase 3 (editor de masmorras): objetivos / saída / prisioneiro ─────────────
  // Getters dos campos servidos no game_state (null no procedural).
  function getObjectives() { return (gameState && gameState.objectives) || null; }
  function getExitPos()    { return (gameState && gameState.exit_pos) || null; }
  function getStartMode()  { return (gameState && gameState.start_mode) || 'entrance'; }
  function getHeroSpawns() { return (gameState && gameState.hero_spawns) || []; }
  function getPrisoner()   { return (gameState && gameState.prisoner) || null; }
  // Decisor puro: há prisioneiro cativo (vivo, não libertado) adjacente (Chebyshev ≤1)
  // ao herói local, e é o turno dele? Usado pelo renderer para habilitar o botão.
  function prisioneiroLibertavel() {
    const pr = getPrisoner();
    if (!pr || pr.freed || !pr.alive) return false;
    if (!gameState || gameState.current_turn !== myPid) return false;
    const me = (gameState.players || []).find(p => p.id === myPid && p.alive);
    if (!me) return false;
    return Math.max(Math.abs(me.pos[0] - pr.pos[0]), Math.abs(me.pos[1] - pr.pos[1])) <= 1;
  }
  // Sender: herói adjacente liberta o prisioneiro (ação principal no servidor).
  function libertarPrisioneiro() { send({ type: 'libertar_prisioneiro' }); }

  // Há objetivo principal cumprido aguardando o encerramento manual da fase?
  function missionCompletePending() { return !!(gameState && gameState.mission_complete_pending); }
  // Sender: encerra a missão (servidor faz a transição cidade/vitória).
  function encerrarMissao() { send({ type: 'encerrar_missao' }); }

  // ── Saída individual pela escada (masmorra sequenciada) ────────────────────
  // O herói sai sozinho, vai para a cidade e volta N rodadas depois. Enquanto
  // está fora, o servidor manda city_state só para ele (nunca game_state), então
  // o estado do ausente é lido do cityState.
  function voltarMasmorra() { send({ type: 'voltar_masmorra' }); }
  function foraMasmorraDe(p) { return (p && p.fora_masmorra) || null; }
  function _meNaCidade() {
    return cityState && (cityState.players || []).find(p => p.id === myPid);
  }
  function estouForaDaMasmorra() { return !!foraMasmorraDe(_meNaCidade()); }
  function rodadasParaVoltar() {
    const fora = foraMasmorraDe(_meNaCidade());
    return fora ? (fora.rodadas_restantes | 0) : 0;
  }

  // ── Fase 4a (campanha): estado da campanha em curso + seleção no lobby ────────
  // Getter do payload {name, phase, total} servido no game_state/city_state (null
  // fora de campanha). lobbyCampaigns lista as campanhas disponíveis no lobby.
  function getCampaign()       { return (gameState && gameState.campaign) || null; }
  function getLobbyCampaigns() { return (lobbyState && lobbyState.campaigns) || []; }
  // Sender: host escolhe uma campanha do lobby; file=null volta ao procedural.
  function selectCampaign(file) { send({ type: 'select_campaign', file: file || null }); }

  // ── Fase 4b (história): beat pendente + de-dup por key ───────────────────────
  // O servidor expõe um "beat" {key,text} em game_state.campaign.story (abertura),
  // city_state.campaign.story (encerramento) e game_over.story (final). Cada
  // jogador exibe/fecha localmente; o de-dup por key garante que apareça 1×.
  const _storyShown = new Set();
  let _lastStory = null;   // beat mais recente recebido (game_state/city_state/game_over)
  function _captarStory(msg) {
    const beat = (msg && msg.campaign && msg.campaign.story) || (msg && msg.story) || null;
    if (beat && beat.key) _lastStory = beat;
  }
  function pendingStory() {
    return (_lastStory && !_storyShown.has(_lastStory.key)) ? _lastStory : null;
  }
  function marcarStoryVista(key) { if (key) _storyShown.add(key); }

  // ── Hooks de sobrevivência chamados pelo renderer nos pontos de ação ───────
  // Ataque/magia/habilidade têm seus sends no renderer (game.js); ele notifica
  // a atividade do turno aqui. Magia conta como ataque ('acted').
  function notifyAttack()      { _turn.acted   = true; }   // ataque ou magia
  function notifySkill()       { _turn.special = true; }   // habilidade especial
  function notifyBonusAction() { _consumeMine('acaoBonus'); }
  function notifyDamageTaken() { _consumeMine('receberDano'); }

  // ── Attack resolver: pure decision, no DOM ─────────────────────────────────
  // Returns one of:
  //   {type:'none',   reason}          — no valid targets (show toast)
  //   {type:'direct', targetId}        — single target (send attack immediately)
  //   {type:'modal',  title, targets}  — multiple targets (open target modal)
  function alturaDe(entidade) {
    const valor = Number(entidade?.altura);
    return Number.isFinite(valor) ? Math.max(0, Math.min(10, Math.trunc(valor))) : 0;
  }

  function custoVerticalAlcance(alturaA, alturaB) {
    return Math.ceil(Math.abs(alturaDe({ altura: alturaA }) - alturaDe({ altura: alturaB })) / 2);
  }

  function faixaAlturaQueda(altura) {
    const n = alturaDe({ altura });
    if (n <= 0) return null;
    if (n <= 3) return 'baixo';
    if (n <= 7) return 'medio';
    return 'alto';
  }

  function expressaoDanoQueda(altura) {
    const faixa = faixaAlturaQueda(altura);
    return faixa === 'baixo' ? '2d6' : faixa === 'medio' ? '4d6' : faixa === 'alto' ? '6d6' : null;
  }

  function weaponCanReachTile(myP, tx, ty, targetAltitude = 0) {
    const weapon = myP?.weapon || {};
    const range = weapon.range;
    const dx = Math.abs(myP.pos[0] - tx), dy = Math.abs(myP.pos[1] - ty);
    if (range != null) {
      const alcance = Number(range) - custoVerticalAlcance(alturaDe(myP), targetAltitude);
      if (alcance < 1) return false;
      const distancia = Math.max(dx, dy);
      if (weapon.id === 'besta' || weapon.id === 'hand_crossbow')
        return (dx === 0 || dy === 0) && distancia <= alcance;
      if (weapon.id === 'arco_curto' || weapon.id === 'longbow') {
        const limite = (dx === 0 || dy === 0) ? alcance : Math.ceil(alcance / 2);
        return distancia <= limite;
      }
      return distancia <= alcance;
    }
    if (alturaDe(myP) !== alturaDe({ altura: targetAltitude })) return false;
    if (weapon.reach === 'lanca')
      return Math.max(dx, dy) === 1 || (dx === 0 && dy === 2) || (dx === 2 && dy === 0);
    if (weapon.id === 'lanca_curta' || weapon.reach === 'mangual' || weapon.reach === 'cajado')
      return Math.max(dx, dy) === 1;
    return (dx === 1 && dy === 0) || (dx === 0 && dy === 1);
  }

  function weaponReachInfo(myP, tx, ty, targetAltitude = 0) {
    const weapon = myP?.weapon || {};
    const ranged = weapon.range != null;
    const attackerAltitude = alturaDe(myP);
    const alvoAltitude = alturaDe({ altura: targetAltitude });
    const verticalCost = ranged ? custoVerticalAlcance(attackerAltitude, alvoAltitude) : 0;
    const horizontalDistance = Math.max(Math.abs((myP?.pos?.[0] || 0) - tx), Math.abs((myP?.pos?.[1] || 0) - ty));
    const effectiveRange = ranged ? Number(weapon.range) - verticalCost : null;
    return {
      attackerAltitude,
      targetAltitude: alvoAltitude,
      horizontalDistance,
      verticalCost,
      effectiveRange,
      inRange: weaponCanReachTile(myP, tx, ty, targetAltitude),
    };
  }

  function resolveAttack() {
    if (!gameState) return null;
    const myP = gameState.players.find(p => p.id === myPid && p.alive);
    if (!myP) return null;
    const wRange = myP.weapon?.range ?? null;
    const adj = gameState.monsters.filter(m => {
      if (!m || m.hp <= 0) return false;
      if (myP.engolido && m.id === myP.engolido_por) return true;
      const tiles = monsterTiles(m);   // atacável em qualquer casa do corpo
      if (wRange != null) {
        // À distância: alguma casa do corpo no alcance E com linha de visão.
        return tiles.some(([tx, ty]) => weaponCanReachTile(myP, tx, ty, m.altura)
          && hasLineOfSight(gameState, myP.pos[0], myP.pos[1], tx, ty));
      }
      // Corpo a corpo: adjacente a alguma casa do corpo. A lança curta inclui
      // as diagonais; as demais armas mantêm a regra ortogonal.
      return tiles.some(([tx, ty]) => weaponCanReachTile(myP, tx, ty, m.altura));
    });
    if (!adj.length) {
      const reason = wRange != null
        ? _t('ui.ataque.sem_alvo_distancia', `Nenhum inimigo a até ${wRange} quadrados!`, { n: wRange })
        : _t('ui.ataque.sem_alvo_adjacente', 'Nenhum inimigo adjacente. Mova-se para ao lado de um inimigo!');
      return { type: 'none', reason };
    }
    if (adj.length === 1) return { type: 'direct', targetId: adj[0].id };
    const title = wRange != null
      ? _t('ui.ataque.titulo_distancia', `Atacar à distância — Escolha o Alvo (alcance ${wRange})`, { n: wRange })
      : _t('ui.ataque.titulo_adjacente', 'Atacar — Escolha o Inimigo Adjacente');
    return { type: 'modal', title, targets: adj };
  }

  // Casas de monstro que podem receber o ataque básico agora. O renderer usa
  // esta consulta pura para a mira do joystick; o servidor continua validando
  // o ataque quando a mensagem é recebida.
  function attackTargetTiles() {
    if (!gameState || gameState.phase !== 'playing' || !isMyTurn) return [];
    const myP = gameState.players.find(p => p.id === myPid && p.alive);
    if (!myP || myP.action_done) return [];
    const ranged = myP.weapon?.range != null;
    const result = [], seen = new Set();
    for (const monster of gameState.monsters || []) {
      if (!monster || monster.hp <= 0) continue;
      for (const [tx, ty] of monsterTiles(monster)) {
        const swallowedTarget = myP.engolido && monster.id === myP.engolido_por;
        const inRange = swallowedTarget || weaponCanReachTile(myP, tx, ty, monster.altura);
        const lineClear = !ranged || swallowedTarget
          || hasLineOfSight(gameState, myP.pos[0], myP.pos[1], tx, ty);
        const key = `${tx},${ty}`;
        if (inRange && lineClear && !seen.has(key)) {
          seen.add(key);
          result.push({ x: tx, y: ty, targetId: monster.id });
        }
      }
    }
    return result;
  }

  // ── Skill activator: sets pendingSkill or sends directly ──────────────────
  // Returns: 'sent' | 'pending_enemy' | 'pending_ally' | 'no_targets'
  // Renderer uses return value to show appropriate toast / re-render panel.
  function activateSkill(skill, state) {
    const target = skill.target;
    if (target === 'self') {
      pendingSkill = null;
      notifySkill();   // habilidade especial → consumo no fim do turno
      send({ type: 'skill', skill_id: skill.id, target_id: myPid });
      return 'sent';
    }
    if (target === 'all_enemies' || target === 'all_allies') {
      pendingSkill = null;
      notifySkill();   // habilidade especial → consumo no fim do turno
      send({ type: 'skill', skill_id: skill.id, target_id: null });
      return 'sent';
    }
    if (target === 'enemy') {
      if (!state.monsters.filter(m => m.hp > 0).length) return 'no_targets';
      pendingSkill = skill;
      return 'pending_enemy';
    }
    if (target === 'ally') {
      pendingSkill = skill;
      return 'pending_ally';
    }
    return 'sent';
  }

  // ── Habilidades ARMADAS do warrior (toggle, custo cobrado na ação) ─────────
  // O custo de fome/sede NÃO é cobrado aqui — só quando o jogador ataca (o send
  // do ataque inclui os ids armados e o servidor cobra/aplica). Cumulativas.
  function isWarriorSkillSelected(id) { return warriorSelected.includes(id); }
  function toggleWarriorSkill(id) {
    const i = warriorSelected.indexOf(id);
    if (i >= 0) warriorSelected.splice(i, 1);
    else {
      warriorSelected.push(id);
      const p = (gameState?.players || []).find(q => q.id === myPid);
      if (p?.pos) _emit('abilityActivation', {
        player_id: myPid, ability_id: id, kind: 'skill',
        class_id: p.class_id, pos: [...p.pos]
      });
    }
    return warriorSelected.slice();
  }
  function getWarriorSelected()  { return warriorSelected.slice(); }
  function clearWarriorSelected() { warriorSelected = []; }
  // Teto de habilidades armadas do warrior pela posse de especializações da Guilda.
  function warriorComboCap() {
    const esp = (guildOwnedOf(myPid).especializacoes) || [];
    if (esp.includes('guerreiro_mestre_combate')) return 3;
    if (esp.includes('guerreiro_combinar_2'))     return 2;
    return 1;
  }

  // Níveis das especializações do Clérigo (Fase 1b) — lidos da posse; caem para o
  // player do game_state na masmorra (guildOwnedOf já trata cityState=null).
  function clericCuraTeto() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('clerigo_cura_3')) return 3;
    if (e.includes('clerigo_cura_2')) return 2;
    return 1;
  }
  function clericMassaNivel() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('clerigo_massa_3')) return 3;
    if (e.includes('clerigo_massa_2')) return 2;
    return 1;
  }
  function clericPurifTipos() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    const t = ['veneno'];
    if (e.includes('clerigo_purif_2')) t.push('doenca');
    if (e.includes('clerigo_purif_3')) t.push('maldicao', 'petrificacao');
    return t;
  }
  function clericRessurNivel() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('clerigo_ressur_3')) return 3;
    if (e.includes('clerigo_ressur_2')) return 2;
    return 1;
  }

  // Níveis das especializações do Paladino (Fase 1c) — mesmo padrão dos getters
  // do Clérigo: lidos da posse; caem para o player do game_state na masmorra.
  function paladinCuraMaosDados() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('paladino_cura_maos_2') ? 2 : 1;
  }
  function paladinCuraMaosExtra() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('paladino_cura_maos_3');
  }
  function paladinAtaqueSagradoDados() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('paladino_ataque_sagrado_2') ? 2 : 1;
  }
  function paladinLuzMaxAtributos() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('paladino_luz_3')) return 4;
    if (e.includes('paladino_luz_2')) return 3;
    return 2;
  }
  function paladinDefensorRaio() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('paladino_defensor_2') ? 5 : 4;
  }
  function paladinDefensorSplit() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('paladino_defensor_3') ? 40 : 50;
  }
  function paladinRegenRaio() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('paladino_regen_3')) return 2;
    if (e.includes('paladino_regen_2')) return 1;
    return 0;
  }

  // Níveis das especializações do Ladino (Fase 1d) — mesmo padrão dos getters
  // anteriores: lidos da posse; caem para o player do game_state na masmorra.
  function ladinoArmadilhasDesbloqueadas() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    const mapa = {
      armadilha_urso: 'ladino_armadilha_urso', fosso_estacas: 'ladino_fosso_estacas',
      fosso_envenenado: 'ladino_fosso_envenenado', rede: 'ladino_rede',
      armadilha_incendiaria: 'ladino_armadilha_incendiaria', mina_terrestre: 'ladino_mina_terrestre',
      lamina_escondida: 'ladino_lamina_escondida', lamina_pendulo: 'ladino_lamina_pendulo',
      nuvem_gas: 'ladino_nuvem_gas',
    };
    const tipos = ['buraco'];
    for (const [tipo, gid] of Object.entries(mapa)) if (e.includes(gid)) tipos.push(tipo);
    return tipos;
  }
  function ladinoFurtivoNivel() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('ladino_furtivo_3')) return 3;
    if (e.includes('ladino_furtivo_2')) return 2;
    return 1;
  }
  function ladinoDesarmeBonus() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    return (e.includes('ladino_desarme_2') || e.includes('ladino_desarme_3')) ? 2 : 0;
  }
  function ladinoDesarmeRecupera() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('ladino_desarme_3');
  }
  function ladinoVenenoMaxHits() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('ladino_veneno_2') ? 2 : 1;
  }
  function ladinoVeneno2Slots() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('ladino_veneno_3');
  }
  function ladinoEsconderBonus() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    return (e.includes('ladino_esconder_2') || e.includes('ladino_esconder_3')) ? 2 : 0;
  }
  function ladinoEsconderLivre() {
    return false;
  }
  function ladinoEsconderRevelaCA() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('ladino_esconder_3');
  }

  // ── Bardo (Fase 1e) ────────────────────────────────────────────────────────
  function bardoCancaoNivel(attr) {   // 'acerto'|'dano'|'ca'|'movimento'|'resistencia'
    return (guildOwnedOf(myPid).especializacoes || []).includes('bardo_cancao_' + attr) ? 2 : 1;
  }
  function bardoCancaoSuprema() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('bardo_cancao_suprema');
  }
  function bardoProvocacaoNivel() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('bardo_provocacao_3')) return 3;
    if (e.includes('bardo_provocacao_2')) return 2;
    return 1;
  }
  function bardoLendasSupremas() {
    return (guildOwnedOf(myPid).especializacoes || []).includes('bardo_lendas_supremas');
  }

  // ── Mago (Fase 1f) — Metamagia ─────────────────────────────────────────────
  function magoTecelagemCap() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('mago_tecelagem_3')) return 3;
    if (e.includes('mago_tecelagem_2')) return 2;
    return 1;
  }
  function magoFortalecerMult() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('mago_fortalecer_3')) return 2;
    if (e.includes('mago_fortalecer_2')) return 1.5;
    return 1.25;
  }
  function magoAprimorarBonus() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('mago_aprimorar_3')) return 3;
    if (e.includes('mago_aprimorar_2')) return 2;
    return 1;
  }
  function magoEstenderBonus() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('mago_estender_3')) return 3;
    if (e.includes('mago_estender_2')) return 2;
    return 1;
  }
  // Nível de Reviver os Mortos (1/2/3) — espelha server._reviver_nivel.
  // I: toda criatura ocupa 1 slot fixo, chance 100−ND×20%.
  // II/III: ocupa ND fracionário; chance 100−ND×15%/10%; III soma +2 Slots.
  function magoReviverNivel() {
    const e = (guildOwnedOf(myPid).especializacoes) || [];
    if (e.includes('mago_reviver_3')) return 3;
    if (e.includes('mago_reviver_2')) return 2;
    return 1;
  }
  function magoReviverSlotsExtra() {
    return magoReviverNivel() === 3 ? 2 : 0;
  }
  function magoReviverSlotCusto(nd) {
    return magoReviverNivel() === 1 ? 1 : Math.max(0.25, nd);
  }
  function magoReviverChance(nd) {
    const reducao = { 1: 20, 2: 15, 3: 10 }[magoReviverNivel()];
    const gp = (gameState && gameState.players || []).find(p => p.id === myPid);
    const bonusNivel = ((gp && gp.level) || 1) * 5;
    return Math.min(99, Math.max(1, Math.round(100 - nd * reducao + bonusNivel)));
  }

  // ── Tile-click resolver: pure decision, no DOM ─────────────────────────────
  // Called by the unified handleTileClick(tx, ty) in game.html.
  // Returns one of:
  //   null                                   — nothing to do / consume click silently
  //   {type:'skill_blocked', reason}         — melee range violation (show toast)
  //   {type:'skill',  skillId, targetId}     — execute skill send + clear pendingSkill
  //   {type:'attack', targetId}              — execute attack send
  //   {type:'move',   path}                  — execute move sends
  function resolveTileClick(tx, ty) {
    if (!gameState || gameState.phase !== 'playing' || !isMyTurn) return null;
    const myP = gameState.players.find(p => p.id === myPid && p.alive);
    if (!myP) return null;

    // ── Pending-skill targeting ──────────────────────────────────────────────
    if (pendingInstrumento) {
      const inst = pendingInstrumento;
      const m = gameState.monsters.find(mm => mm.hp > 0 &&
        monsterTiles(mm).some(([bx, by]) => bx === tx && by === ty));
      if (m) {
        const distancia = Math.max(Math.abs(myP.pos[0] - tx), Math.abs(myP.pos[1] - ty));
        const alcance = (inst.alcance || 0) - custoVerticalAlcance(alturaDe(myP), alturaDe(m));
        if (alcance < 1 || distancia > alcance) return { type: 'instrumento_blocked', reason: 'range' };
        if (!hasLineOfSight(gameState, myP.pos[0], myP.pos[1], tx, ty))
          return { type: 'instrumento_blocked', reason: 'wall' };
        return { type: 'instrumento', targetId: m.id };
      }
      return null;
    }

    if (pendingSkill) {
      const sk    = pendingSkill;
      if (sk.id === 'desarmar_armadilha') {
        const dx = Math.abs(myP.pos[0] - tx), dy = Math.abs(myP.pos[1] - ty);
        if (Math.max(dx, dy) <= 1) return { type: 'disarm_trap', tx, ty };
        return { type: 'skill_blocked', reason: 'trap_adjacent' };
      }
      const MELEE = ['heavy_blow', 'backstab', 'smite'];
      if (sk.target === 'enemy') {
        const m = gameState.monsters.find(m => m.hp > 0 &&
          monsterTiles(m).some(([bx, by]) => bx === tx && by === ty));
        if (m) {
          if (MELEE.includes(sk.id)) {
            const ddx = Math.abs(myP.pos[0] - tx);
            const ddy = Math.abs(myP.pos[1] - ty);
            if (!((ddx === 1 && ddy === 0) || (ddx === 0 && ddy === 1)))
              return { type: 'skill_blocked', reason: 'melee_adj' };
          }
          return { type: 'skill', skillId: sk.id, targetId: m.id };
        }
      } else if (sk.target === 'ally') {
        const pl = gameState.players.find(p => p.pos[0] === tx && p.pos[1] === ty && p.alive);
        if (pl) return { type: 'skill', skillId: sk.id, targetId: pl.id };
      }
      return null; // consume click, stay in pending mode (ESC to cancel)
    }

    // ── Pending-throw targeting (arremessável de bolsa) ──────────────────────
    if (pendingThrow) {
      const th   = pendingThrow;
      // Itens custom (Editor de Itens) não estão no CATALOGO_ITENS estático:
      // o alvo vem no próprio pendingThrow (carregado do item de bolsa).
      const alvo = (CATALOGO_ITENS[th.id] || {}).alvo || th.alvo || 'ataque_alvo';
      const ddx  = Math.abs(myP.pos[0] - tx);
      const ddy  = Math.abs(myP.pos[1] - ty);
      const alvoAltura = alvo === 'area' ? 0 : (() => {
        const alvoMonstro = gameState.monsters.find(mm => mm.hp > 0 &&
          monsterTiles(mm).some(([bx, by]) => bx === tx && by === ty));
        return alvoMonstro ? alturaDe(alvoMonstro) : 0;
      })();
      const alcance = Number(th.alcance || 0) - custoVerticalAlcance(alturaDe(myP), alvoAltura);
      const inRange = alcance >= 1 && Math.max(ddx, ddy) <= alcance;
      const losOk   = hasLineOfSight(gameState, myP.pos[0], myP.pos[1], tx, ty);
      if (alvo === 'area') {
        // Área: mira numa CASA (não precisa de monstro), valida alcance + LOS ao centro.
        if (inRange && losOk) return { type: 'throw_area', itemId: th.id, tx, ty };
        return { type: 'throw_blocked' };
      }
      // ataque_alvo (Sub-projeto A): precisa de um monstro na casa.
      const m = gameState.monsters.find(m => m.hp > 0 &&
        monsterTiles(m).some(([bx, by]) => bx === tx && by === ty));
      if (m) {
        if (inRange && losOk) return { type: 'throw', itemId: th.id, targetId: m.id, targetPos: [tx, ty] };
        return { type: 'throw_blocked' };   // fora de alcance / parede
      }
      return null; // consome o clique, permanece na mira (ESC cancela)
    }

    // ── Closed door: click to open (free action, must be adjacent) ────────────
    const { closed } = doorSets(gameState);
    if (closed.has(`${tx},${ty}`)) {
      const ch = Math.max(Math.abs(myP.pos[0] - tx), Math.abs(myP.pos[1] - ty));
      if (ch <= 1) return { type: 'open_door', x: tx, y: ty };
      // Caminha somente até a melhor casa acessível antes da porta. A porta
      // permanece fechada e a decisão de abri-la continua sendo do jogador.
      const expSet = new Set(gameState.explored.map(([x, y]) => `${x},${y}`));
      const path = findPath(gameState.tiles, expSet, myP.pos[0], myP.pos[1], tx, ty, myP.moves_left, true);
      if (path && path.length) {
        if (myP.petrificado) return { type: 'movement_blocked', reason: 'petrified' };
        return { type: 'move', path, stopAtDoor: true };
      }
      return { type: 'door_far' };
    }

    // ── Attack monster in range ──────────────────────────────────────────────
    const monster = gameState.monsters.find(m => m.hp > 0 &&
      monsterTiles(m).some(([bx, by]) => bx === tx && by === ty));
    if (monster && !myP.action_done) {
      if (myP.engolido && monster.id === myP.engolido_por)
        return { type: 'attack', targetId: monster.id, targetPos: [tx, ty] };
      const wRng = myP.weapon?.range ?? null;
      if (wRng != null) {
        if (weaponCanReachTile(myP, tx, ty, monster.altura)) {
          // Paredes/portas fechadas barram a linha de tiro.
          if (hasLineOfSight(gameState, myP.pos[0], myP.pos[1], tx, ty))
            return { type: 'attack', targetId: monster.id, targetPos: [tx, ty] };
          return { type: 'attack_blocked_wall' };
        }
      } else if (weaponCanReachTile(myP, tx, ty, monster.altura)) {
        return { type: 'attack', targetId: monster.id, targetPos: [tx, ty] };
      }
    }

    // ── Pathfind and move ────────────────────────────────────────────────────
    if (myP.petrificado) return { type: 'movement_blocked', reason: 'petrified' };
    if (myP.moves_left <= 0) return null;
    if (tx === myP.pos[0] && ty === myP.pos[1]) return null;
    const expSet = new Set(gameState.explored.map(([x, y]) => `${x},${y}`));
    const path   = findPath(gameState.tiles, expSet, myP.pos[0], myP.pos[1], tx, ty, myP.moves_left, true);
    if (path && path.length) return { type: 'move', path };
    return null;
  }

  // ── Contas / Jogos Salvos (Fase 3) ──────────────────────────────────────────
  function loginConta(url, name, password) {
    connect(url, name, 'login');
    const trySend = () => {
      if (ws && ws.readyState === 1) send({ type: 'login', username: name, password });
      else setTimeout(trySend, 60);
    };
    trySend();
  }
  function criarConta(url, name, password) {
    connect(url, name, 'login');
    const trySend = () => {
      if (ws && ws.readyState === 1) send({ type: 'create_account', username: name, password });
      else setTimeout(trySend, 60);
    };
    trySend();
  }
  function listSavegames()      { send({ type: 'list_savegames' }); }
  function createSavegame(opts) { send({ type: 'create_savegame', ...opts }); } // {name, mode, campaign_file, has_master}
  function campaignVote(voteId, approve) { send({ type: 'campaign_vote', vote_id: voteId, approve: !!approve }); }
  function abandonMasterCampaign(id) { send({ type: 'abandon_master_campaign', id }); }
  function loadSavegame(id)     { send({ type: 'load_savegame', id }); }
  function deleteSavegame(id)   { send({ type: 'delete_savegame', id }); }
  // Entra na sala de um amigo (jogo salvo dele) pela conexão JÁ LOGADA — sem
  // reconectar, para não perder a conta autenticada nesta conexão. O nome do
  // jogador é o próprio apelido (o servidor casa myPid por nome e vincula o
  // personagem à conta via account_by_pid). Só faz sentido após o login.
  function joinByCode(code) {
    if (!account) return false;
    myPid = null;   // sala nova → myPid é resolvido pelo próximo lobby_state
    send({ type: 'join_room', name: account, code: (code || '').toUpperCase() });
    return true;
  }

  // ── Public API ─────────────────────────────────────────────────────────────
  return {
    // ── Constants ──
    TILE_WALL,
    TILE_FLOOR,
    TILE_DOOR,

    // ── Portas ──
    doorSets,
    doorOrientation,

    // ── Linha de visão (paredes/portas barram ataques/magias à distância) ──
    hasLineOfSight,

    // ── Footprint de um monstro (1×1, bloco size, ou 2 casas orientadas) ──
    monsterTiles,

    // ── State getters (renderer reads these) ──
    get ws()              { return ws; },
    get myPid()           { return myPid; },
    get myName()          { return myName; },
    get gameState()       { return gameState; },
    get decorations()     { return (gameState && gameState.decorations) || []; },
    get materiais()       { return (gameState && gameState.materiais) || {}; },
    // Jogador local autoritativo (estado mais recente do servidor). Usado pela
    // ficha em jogo (abrirFichaEmJogo) para HP/atributos/CA reais. Mesmo padrão
    // de lookup de getHeroiAtivo; null se ainda não há jogador.
    get me()              {
      const players = gameState?.players || cityState?.players || lobbyState?.players || [];
      return players.find(p => p.id === myPid) || null;
    },
    get lobbyState()      { return lobbyState; },
    get lobbyDungeons()   { return (lobbyState && lobbyState.dungeons) || []; },
    get lobbyCampaigns()  { return getLobbyCampaigns(); },
    get lobbyMode()       { return (lobbyState && lobbyState.mode) || 'procedural'; },
    get lobbySelectedDungeon() { return (lobbyState && lobbyState.selected_dungeon) || null; },
    // Fase 3: objetivos / saída / prisioneiro (property getters — acessados sem parênteses).
    get objectives()            { return getObjectives(); },
    get exitPos()               { return getExitPos(); },
    get startMode()             { return getStartMode(); },
    get heroSpawns()            { return getHeroSpawns(); },
    get prisoner()              { return getPrisoner(); },
    get prisioneiroLibertavel() { return prisioneiroLibertavel(); },
    get missionCompletePending() { return missionCompletePending(); },
    // Fase 4a: campanha em curso (property getter — acessado sem parênteses).
    get campaign()              { return getCampaign(); },
    get cityState()       { return cityState; },
    get groundItems()     { return (gameState && gameState.ground_items) || []; },
    get isMyTurn()        { return isMyTurn; },
    get pendingAction()   { return pendingAction; },
    get pendingMove()     { return pendingMove; },
    get pendingSkill()    { return pendingSkill; },
    get pendingThrow()    { return pendingThrow; },
    get pendingInstrumento() { return pendingInstrumento; },
    get activeShop()      { return activeShop; },
    get activeScene()     { return activeScene; },
    get shopTabIdx()      { return shopTabIdx; },
    get pendingShopOpen() { return pendingShopOpen; },

    // ── State setters (renderer may mutate these directly) ──
    set pendingSkill(v)    { pendingSkill    = v; },
    set pendingThrow(v)    { pendingThrow    = v; },
    set pendingInstrumento(v) { pendingInstrumento = v; },
    set pendingAction(v)   { pendingAction   = v; },
    set pendingMove(v)     { pendingMove     = v; },
    set activeShop(v)      { activeShop      = v; },
    set activeScene(v)     { activeScene     = v; },
    set shopTabIdx(v)      { shopTabIdx      = v; },
    set pendingShopOpen(v) { pendingShopOpen = v; },

    // ── Callback registration ──
    on,

    // ── Pure logic ──
    bfsReachable,
    findPath,

    // ── Equipamento inicial / heróis ──
    HERO_DATA,
    EQUIPAMENTOS_INICIAIS,
    inicializarHeroi,
    podeEquipar,

    // ── Catálogo de itens / loja ──
    CATALOGO_ITENS,
    getHeroiAtivo,
    aplicarConsumivel,
    equiparItemComprado,
    desequiparItemComprado,
    classToHeroKey: _classToHeroKey,
    adicionarLog,

    // ── Sobrevivência (fome/sede) ──
    SOBREVIVENCIA_CONFIG,
    inicializarSobrevivencia,
    consumirRecursos,
    getThreshold,
    getModificadorFinal,
    verificarEstadoSobrevivencia,
    processarColapsoTotal,
    // Estado de sobrevivência (renderer lê para exibir barras/modificadores)
    get survival()              { return survival; },
    getSurvival(pid)            { return _ensureSurvival(pid || myPid); },
    survivalModifier(pid)       {
      const h = _ensureSurvival(pid || myPid);
      return h ? getModificadorFinal(h) : 0;
    },
    // Hooks de ação (renderer chama nos pontos de ataque/magia/bônus/dano)
    notifyAttack,
    notifySkill,
    notifyBonusAction,
    notifyDamageTaken,

    // ── Network ──
    connect,
    send,
    rejoin,                  // religa à partida (queda/F5) via mensagem `rejoin`
    savedSession,            // {url, code, name} persistidos — ou null
    clearSession,            // descarta a sessão salva (ex.: sair de propósito)
    leaveSession,            // encerra a conexão sem programar reconexão

    // ── Contas / Jogos Salvos (Fase 3) ──
    loginConta, criarConta, listSavegames, createSavegame, loadSavegame, deleteSavegame, joinByCode, campaignVote, abandonMasterCampaign,
    getAccount: () => account,
    getSavegames: () => savegames,
    getCampaigns: () => campaignsCache,

    // ── Actions ──
    move,
    alterarAltura,
    endTurn,
    sceneChoice,
    sceneTest,
    sceneEnd,
    sceneVisit,
    setTurnTimer,
    setShortcut,
    shortcutActivated,
    useItem,
    respondFireChoice,
    throwItem,
    throwItemArea,
    throwWeapon,
    apagarChamas,
    estancarSangramento,
    escaparEstomago,
    escaparBau,
    equipFromBag,
    quickEquipFromBag,
    unequip,
    repairItem,
    reorderBag,
    equipOffhand,
    dropItem,
    interagirDecor,
    takeFromDecor,
    takeAllFromDecor,
    activateDecorMechanism,
    pickupItem,
    groundItemPickable,
    canPlaceItem,
    slotCategoryForItem: _slotCategoryForItem,
    offHandBlockedByTwoHanded,
    compareItemStats,
    isDagger,
    isOffhandWeapon,
    setKnownSpells,
    escolherMagiaNivel,
    animarMortos,
    comandarAnimados,
    moverAnimado,
    atacarAnimado,
    usarHabilidadeAnimado,
    moverPrisioneiro,
    criarArmadilha,
    desarmarArmadilha,
    armadilhaAdjacente,

    // ── Modo Mestre Jogador (Fase A) ──
    claimRole,
    mestreSetModo,
    mestreSetAlvo,
    mestreMoverMonstroPara,
    mestreUsarHabilidade,
    mestreUsarMagia,
    mestreUsarItem,
    mestreAtacarMonstro,
    mestreEncerrarMonstro,
    mestreSelecionarTeste,
    mestreImplantarReforco,
    dispararFala,
    isMaster,
    isCommandController,
    canControlMonster,
    masterManualMid,
    masterManual,
    masterAttackCharges,
    masterPodeAtacar,
    licaoAtual,

    // ── Prévia do editor (index.html?preview=1) ──
    isPreview: PREVIEW,
    injectPreviewState,
    setLang,
    setMessageFilter,
    setTranslator,

    // ── Guilda dos Heróis (Fase 0) ──
    guildBuy,
    worldTravel,
    worldAdventure,
    talkSceneNpc,
    scenes,
    cityPoints,
    sceneIdOfPoint,
    sceneOfPoint,
    saveWorldMapPoints,
    saveCityMapPoints,
    openRefugio,
    openQuarto,
    refugioStore,
    refugioTake,
    refugioGold,
    quartoCustomize,
    guildEquip,
    usarTecnica,
    responderSorteReacao,
    usarOportunidadeMovimento,
    guildCatalogFor,
    guildOwnedOf,
    guildEquipOf,
    sorrateiroAtivo,
    tecnicaRestante,
    tecnicaPendente,
    tecnicasConcedidasPorItem,

    // ── Instrumentos do Bardo (Fase 1) ──
    usarInstrumento,
    instrumentoBase,
    instrumentoEquipadoDe,
    instrumentoStatsClient,
    instrumentoDisponivel,
    improvisoAlvo,          // Fase 5 (Gaita/Improviso) — sender (chamado com parênteses)

    selectDungeon,
    selectCampaign,        // Fase 4a: sender (chamado com parênteses)
    pendingStory,          // Fase 4b: beat de história pendente (ou null)
    marcarStoryVista,      // Fase 4b: marca um beat como já exibido (de-dup por key)
    libertarPrisioneiro,   // Fase 3: sender (chamado com parênteses)
    encerrarMissao,        // encerramento manual da missão (chamado com parênteses)

    // ── Saída individual pela escada ──
    voltarMasmorra,        // sender (chamado com parênteses)
    foraMasmorraDe,        // {rodadas_restantes} de um player, ou null
    estouForaDaMasmorra,
    rodadasParaVoltar,

    // ── Habilidades armadas do warrior (toggle; custo cobrado na ação) ──
    isWarriorSkillSelected,
    toggleWarriorSkill,
    getWarriorSelected,
    clearWarriorSelected,
    warriorComboCap,
    clericCuraTeto,
    clericMassaNivel,
    clericPurifTipos,
    clericRessurNivel,
    paladinCuraMaosDados,
    paladinCuraMaosExtra,
    paladinAtaqueSagradoDados,
    paladinLuzMaxAtributos,
    paladinDefensorRaio,
    paladinDefensorSplit,
    paladinRegenRaio,
    ladinoArmadilhasDesbloqueadas,
    ladinoFurtivoNivel,
    ladinoDesarmeBonus,
    ladinoDesarmeRecupera,
    ladinoVenenoMaxHits,
    ladinoVeneno2Slots,
    ladinoEsconderBonus,
    ladinoEsconderLivre,
    ladinoEsconderRevelaCA,
    bardoCancaoNivel,
    bardoCancaoSuprema,
    bardoProvocacaoNivel,
    bardoLendasSupremas,
    magoTecelagemCap,
    magoFortalecerMult,
    magoAprimorarBonus,
    magoEstenderBonus,
    magoReviverNivel,
    magoReviverSlotsExtra,
    magoReviverSlotCusto,
    magoReviverChance,

    // ── Decorações de masmorra ──
    decorTilesOf,
    interagirDecor,
    takeFromDecor,
    activateDecorMechanism,

    // ── Resolvers (no DOM — return data; renderer executes UI work) ──
    alturaDe,
    custoVerticalAlcance,
    faixaAlturaQueda,
    expressaoDanoQueda,
    weaponCanReachTile,
    weaponReachInfo,
    resolveAttack,
    attackTargetTiles,
    activateSkill,
    resolveTileClick,
    cadaverAdjacente,
  };
})();
