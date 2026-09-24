// src/soundBank.js
// Banco de sons: catálogo declarativo + regras PURAS (audibilidade, variante,
// limitador, eventos por diferença de estado). Sem DOM, sem Web Audio.
// Exposto como window.SoundBank (browser) / global.SoundBank (node).
// Spec: docs/superpowers/specs/2026-09-23-sons-efeitos-sonoros-design.md
(function (root) {
  'use strict';

  const GANHO_NEVOA = 0.35;       // fora da visão: mais baixo e abafado
  const GANHO_LONGE = 0.4;        // piso de algo visível e distante
  const DIST_LONGE = 12;          // casas até chegar ao piso
  const TETO_SIMULTANEOS = 8;

  const FAMILIAS = ['humanoide', 'fera', 'morto_vivo', 'reptil_inseto', 'grande'];

  // `arquivos` são relativos a assets/sfx/. Lista vazia = sem amostra: o
  // chamador toca a síntese antiga (ou fica em silêncio se não houver).
  const E = (arquivos, volume, intervaloMs, extra) => Object.assign(
    { arquivos, volume, intervaloMs, pitchJitter: 0.05, volJitter: 0.08, canal: 'efeitos' }, extra || {});
  const n = (base, qtd) => Array.from({ length: qtd }, (_, i) => `${base}_${i + 1}.ogg`);
  const AMB = (arq) => E([arq], 0.5, 0, { canal: 'ambiente', pitchJitter: 0, volJitter: 0 });

  const SFX = {
    // combate
    golpe_cortante:    E(n('combate/golpe_cortante', 3), 0.80, 60),
    golpe_perfurante:  E(n('combate/golpe_perfurante', 3), 0.80, 60),
    golpe_contundente: E(n('combate/golpe_contundente', 3), 0.80, 60),
    golpe_natural:     E(n('combate/golpe_natural', 3), 0.80, 60),
    golpe_critico:     E(n('combate/golpe_critico', 2), 0.70, 60),
    golpe_erro:        E(n('combate/golpe_erro', 3), 0.55, 60),
    escudo_bloqueio:   E(n('combate/escudo_bloqueio', 2), 0.75, 60),
    dor_heroi:         E(n('combate/dor_heroi', 3), 0.60, 120),
    dor_criatura:      E(n('combate/dor_criatura', 3), 0.60, 120),
    // exploração e loot
    porta_abre:        E(n('exploracao/porta_abre', 3), 0.70, 150),
    moedas:            E(n('exploracao/moedas', 2), 0.60, 250),
    item_pegar:        E(n('exploracao/item_pegar', 2), 0.50, 200),
    equipar:           E(n('exploracao/equipar', 3), 0.50, 200),
    beber:             E(n('exploracao/beber', 2), 0.55, 300),
    escada:            E(n('exploracao/escada', 2), 0.60, 500),
    // interface e ritmo do turno
    sua_vez:           E(n('interface/sua_vez', 1), 0.50, 1000),
    nivel:             E(n('interface/nivel', 1), 0.80, 1000),
    objetivo:          E(n('interface/objetivo', 1), 0.80, 1000),
    clique:            E(n('interface/clique', 2), 0.25, 60, { pitchJitter: 0.03 }),
    recusa:            E(n('interface/recusa', 1), 0.35, 300),
    // ambiente (loop; canal próprio)
    amb_masmorra:      AMB('ambiente/amb_masmorra.ogg'),
    amb_penumbra:      AMB('ambiente/amb_penumbra.ogg'),
    amb_ar_livre:      AMB('ambiente/amb_ar_livre.ogg'),
  };
  for (const f of FAMILIAS) {
    SFX['rugido_' + f] = E(n('criaturas/rugido_' + f, 2), 0.75, 400);
    SFX['morte_' + f] = E(n('criaturas/morte_' + f, 2), 0.70, 150);
  }

  // Ordem importa: a 1ª regra que casar decide. `null` = criatura sem voz.
  const REGRAS_FAMILIA = [
    [/^(boneco_|sentinela_teste$|vela_de_fogo$|elemental_)/, null],
    [/^(skeleton|esqueleto_|zumbi_)/, 'morto_vivo'],
    [/^(dragon|tirano_|tiranossauro|troll|ogro_|gigante_|ciclope|minotauro|grande_)/, 'grande'],
    [/^(aranha_|cobra_|crocodilo_|escorpiao_|ferrao_charcos|lagarto_|grotao|devorador_|lacralion_)/, 'reptil_inseto'],
    [/^(lobo_|urso_|gato$|rato($|_)|pombo$|ovelha$|garaloux_|lobisomem|harpia|molochus_)/, 'fera'],
    [/^(goblin|orc($|_)|kobold_|bugbear_|dark_mage|necromante|soldado|xama_|medusa|lorde_vampiro|vampiro_|escravo_vampirico|estrangulador)/, 'humanoide'],
  ];

  function familiaDe(m) {
    const tipo = String((m && m.type) || '');
    for (const [re, fam] of REGRAS_FAMILIA) if (re.test(tipo)) return fam;
    const s = m && Array.isArray(m.size) ? m.size : [1, 1];
    return (Number(s[0]) || 1) * (Number(s[1]) || 1) > 1 ? 'grande' : 'humanoide';
  }

  // o = { pos, visao: Set('x,y')|null, mePos, mestre }
  // `visao === null` (ou ausente) = sem névoa a considerar (cidade/prévia do
  // editor): tudo é tratado como visível. Um Set VAZIO é o oposto — o herói
  // não vê casa nenhuma ainda, então tudo cai em abafado/névoa.
  function audibilidade(o) {
    o = o || {};
    const pos = o.pos;
    if (!Array.isArray(pos)) return { ganho: 1, abafado: false, panLivre: false };
    if (o.mestre) return { ganho: 1, abafado: false, panLivre: true };
    const k = Math.round(pos[0]) + ',' + Math.round(pos[1]);
    if (o.visao && !o.visao.has(k)) return { ganho: GANHO_NEVOA, abafado: true, panLivre: false };
    if (!Array.isArray(o.mePos)) return { ganho: 1, abafado: false, panLivre: true };
    const d = Math.max(Math.abs(pos[0] - o.mePos[0]), Math.abs(pos[1] - o.mePos[1]));
    return { ganho: 1 - (1 - GANHO_LONGE) * Math.min(1, d / DIST_LONGE), abafado: false, panLivre: true };
  }

  function escolherVariante(qtd, ultimo, rnd) {
    if (!(qtd > 0)) return -1;
    if (qtd === 1) return 0;
    const r = rnd || Math.random;
    // Sem anterior válido (primeira vez, ou índice fora do intervalo atual):
    // sorteia entre TODAS as variantes, senão a última nunca seria escolhida.
    if (!(ultimo >= 0) || ultimo >= qtd) return Math.floor(r() * qtd);
    let i = Math.floor(r() * (qtd - 1));
    if (i >= ultimo) i++;
    return i;
  }

  function criarLimitador(teto) {
    const max = teto || TETO_SIMULTANEOS;
    const ultimo = new Map();
    let ativos = [];
    return {
      pode(evento, agora) {
        const def = SFX[evento];
        if (!def) return false;
        const u = ultimo.get(evento);
        if (u != null && agora - u < (def.intervaloMs || 0)) return false;
        ativos = ativos.filter(a => a.fim > agora);
        return ativos.length < max;
      },
      registrar(evento, agora, duracaoMs, ganho) {
        ultimo.set(evento, agora);
        // `ganho` fica guardado no registro mas não é lido por `pode`/`reset`
        // hoje — reservado para uma futura política de descarte por volume.
        ativos.push({ fim: agora + (duracaoMs || 0), ganho });
      },
      reset() { ultimo.clear(); ativos = []; },
    };
  }

  const POCAO_EFEITOS = new Set(['heal', 'regeneration', 'atk_bonus', 'cure_poison', 'cure_petrification', 'cure_disease']);
  function dosesDePocao(bag) {
    let d = 0;
    for (const it of bag) if (it && POCAO_EFEITOS.has(it.effect)) d += (it.uses_left != null ? Number(it.uses_left) || 0 : 1);
    return d;
  }
  function assinaturaGear(gear) {
    if (!gear || typeof gear !== 'object') return '';
    return Object.keys(gear).sort().map(k => k + ':' + ((gear[k] && gear[k].id) || '')).join('|');
  }
  function snapMe(me) {
    if (!me) return null;
    const bag = Array.isArray(me.bag) ? me.bag.filter(Boolean) : [];
    return { ouro: Number(me.ouro) || 0, bagN: bag.length, doses: dosesDePocao(bag),
             gear: assinaturaGear(me.gear), nivel: Number(me.nivel) || 0 };
  }

  // atual = { portas:['x,y'], me:{ouro,bag,gear,nivel}|null, meuTurno, missao,
  //           monstros:[{id,type,size,pos}] (só os VISÍVEIS para mim) }
  // Devolve { eventos:[{evento,pos?}], snap } — o snap vira o `prev` seguinte.
  // Contrato do chamador: `prev = null` a cada NOVA masmorra (reseta `ouvidos`
  // — sem isso um monstro visto numa masmorra anterior nunca rugiria na
  // próxima). `beber` é detectado por doses de poção CAINDO na bolsa — então
  // LARGAR uma poção no chão da masmorra também toca o som (falso positivo
  // aceito); vender/guardar não passam por aqui porque diffSons não corre na
  // cidade (só na masmorra, onde não há loja).
  function diffSons(prev, atual) {
    atual = atual || {};
    const eventos = [];
    const portas = new Set(atual.portas || []);
    const me = snapMe(atual.me);
    const ouvidos = new Set(prev ? prev.ouvidos : []);
    const visiveis = atual.monstros || [];
    const snap = { portas, me, meuTurno: !!atual.meuTurno, missao: !!atual.missao, ouvidos };
    if (!prev) {
      for (const m of visiveis) ouvidos.add(String(m.id));
      return { eventos, snap };
    }
    for (const k of portas) {
      if (prev.portas.has(k)) continue;
      const [x, y] = k.split(',').map(Number);
      eventos.push({ evento: 'porta_abre', pos: [x, y] });
    }
    if (me && prev.me) {
      if (me.gear !== prev.me.gear) eventos.push({ evento: 'equipar' });
      else {
        if (me.bagN > prev.me.bagN) eventos.push({ evento: 'item_pegar' });
        if (me.doses < prev.me.doses) eventos.push({ evento: 'beber' });
      }
      if (me.ouro > prev.me.ouro) eventos.push({ evento: 'moedas' });
      if (me.nivel > prev.me.nivel) eventos.push({ evento: 'nivel' });
    }
    if (snap.meuTurno && !prev.meuTurno) eventos.push({ evento: 'sua_vez' });
    if (snap.missao && !prev.missao) eventos.push({ evento: 'objetivo' });
    let rugiu = false;
    for (const m of visiveis) {
      const id = String(m.id);
      if (ouvidos.has(id)) continue;
      ouvidos.add(id);
      const fam = familiaDe(m);
      if (fam && !rugiu) { eventos.push({ evento: 'rugido_' + fam, pos: m.pos }); rugiu = true; }
    }
    return { eventos, snap };
  }

  // Preset sem loop próprio (desconhecido OU sem arquivo) usa o da masmorra.
  function eventoAmbiente(preset) {
    const e = 'amb_' + preset;
    return (SFX[e] && SFX[e].canal === 'ambiente' && SFX[e].arquivos.length) ? e : 'amb_masmorra';
  }

  root.SoundBank = {
    SFX, FAMILIAS, familiaDe, audibilidade, escolherVariante, criarLimitador,
    diffSons, eventoAmbiente,
    GANHO_NEVOA, GANHO_LONGE, DIST_LONGE, TETO_SIMULTANEOS,
  };
})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
