// Reações elementais — lógica PURA do cliente (sem DOM/canvas/THREE).
(function () {
  const ESTILOS = {
    choque:   { cor: '#7fd4ff', duracaoMs: 700 },
    incendio: { cor: '#ff8a2a', duracaoMs: 900 },
    congelar: { cor: '#bfefff', duracaoMs: 900 },
    crosta:   { cor: '#8a5a44', duracaoMs: 900 },
    explosao_gas: { cor: '#ffb347', duracaoMs: 1100 },
    derreter: { cor: '#a8e4ff', duracaoMs: 1000 },
  };
  function estilo(tipo) { return ESTILOS[tipo] ? Object.assign({}, ESTILOS[tipo]) : null; }

  function _restantes(state, key) {
    const exp = state && state.terrenos_temp && state.terrenos_temp[key];
    return exp == null ? null : Math.max(0, Number(exp) - Number(state.round));
  }

  // Crostas de lava que se desfazem na próxima virada (≤ 1 rodada restante).
  function crostasAcabando(state) {
    const out = [];
    const mats = (state && state.materiais) || {};
    for (const key of Object.keys(mats)) {
      if (mats[key] !== 'lava_solidificada') continue;
      const resta = _restantes(state, key);
      if (resta != null && resta <= 1) out.push(key.split(',').map(Number));
    }
    return out;
  }

  function _sobPonte(state, x, y) {
    return ((state && state.pontes) || []).some(p => ((p && p.tiles) || []).some(t => t && t[0] === x && t[1] === y));
  }

  function descreverCasa(state, x, y) {
    const key = `${x},${y}`;
    const mat = state && state.materiais && state.materiais[key];
    if (mat === 'piche') {
      const emChamas = ((state && state.zonas_especiais) || []).some(z => z && z.ativa && z.tipo === 'chamas_piche'
        && (z.tiles || []).some(t => `${t[0]},${t[1]}` === key));
      return { chave: emChamas ? 'ui.reacao.casa.piche_chamas' : 'ui.reacao.casa.piche', params: {} };
    }
    // Água sob ponte não protege (o servidor ignora a água sob a ponte): sem promessa.
    const ehAgua = mat === 'agua' || mat === 'agua_profunda' || mat === 'rodamoinho' || mat === 'rodamoinho_profundo';
    if (ehAgua && _sobPonte(state, x, y)) return null;
    // toda água (rasa, profunda, redemoinho) conduz choque, congela e protege do fogo
    if (ehAgua) return { chave: 'ui.reacao.casa.agua', params: {} };
    if (mat === 'pantano') return { chave: 'ui.reacao.casa.pantano', params: {} };
    // gelo e neve (fora de ponte): o fogo derrete em água
    if ((mat === 'piso_congelado' || mat === 'planicie_nevada') && !_sobPonte(state, x, y))
      return { chave: 'ui.reacao.casa.gelo', params: {} };
    if (mat === 'lava_solidificada')
      return { chave: 'ui.reacao.casa.crosta', params: { n: Math.max(1, _restantes(state, key) || 1) } };
    return null;
  }

  // ── Prévia da reação na mira ────────────────────────────────────────────────
  // ESPELHO das regras de terrain_reactions.py (_rx_regiao, _rx_choque, _rx_incendiar_piche,
  // _rx_explodir_gas, _rx_derreter_gelo, _rx_congelar_agua, _rx_crosta_lava). Mudou regra lá? Mude aqui:
  // tools/test_destaque_mira.py roda os mesmos cenários no servidor e neste módulo e compara as casas.
  const RAIO_CHOQUE = 6, TETO_CHOQUE = 24, TETO_PICHE = 40, RAIO_DERRETER = 4, TETO_DERRETER = 24;
  const AGUAS = ['agua', 'agua_profunda', 'rodamoinho', 'rodamoinho_profundo'];
  const GELOS = ['piso_congelado', 'planicie_nevada'];
  const TILE_PISO = 1, TILE_PORTA = 2;   // espelham server.FLOOR / server.DOOR

  function _mat(state, x, y) { return state && state.materiais ? state.materiais[`${x},${y}`] : undefined; }
  function _ehAgua(state, x, y) { return AGUAS.indexOf(_mat(state, x, y)) >= 0 && !_sobPonte(state, x, y); }
  function _ehGelo(state, x, y) { return GELOS.indexOf(_mat(state, x, y)) >= 0 && !_sobPonte(state, x, y); }
  function _chave(c) { return `${c[0]},${c[1]}`; }

  // Casas conectadas (4 vizinhos) que satisfazem `pred`, a partir das sementes, dentro de `raio`
  // (Chebyshev, null = sem limite) e até `teto`. Mesma ordem de visita do servidor (importa no teto).
  function _regiao(sementes, pred, raio, teto) {
    const vistas = new Set(), sem = [];
    for (const c of sementes) {
      const k = _chave(c);
      if (vistas.has(k) || !pred(c[0], c[1])) continue;
      vistas.add(k); sem.push([c[0], c[1]]);
    }
    sem.sort((a, b) => (a[1] - b[1]) || (a[0] - b[0]));
    const lista = sem.slice(), conj = new Set(sem.map(_chave));
    let i = 0;
    while (i < lista.length && lista.length < teto) {
      const [x, y] = lista[i++];
      for (const [dx, dy] of [[0, -1], [1, 0], [0, 1], [-1, 0]]) {
        const nx = x + dx, ny = y + dy, k = `${nx},${ny}`;
        if (conj.has(k) || !pred(nx, ny)) continue;
        if (raio != null) {
          let m = Infinity;
          for (const s of sem) m = Math.min(m, Math.max(Math.abs(nx - s[0]), Math.abs(ny - s[1])));
          if (m > raio) continue;
        }
        conj.add(k); lista.push([nx, ny]);
        if (lista.length >= teto) break;
      }
    }
    return lista.slice(0, teto);
  }

  // Casas cobertas por uma zona de gás ativa (Câmara = piso/porta da sala; Nuvem = casas próprias).
  function _casasDoGas(state, z) {
    if (z.tipo === 'camara_gas') {
      const sala = ((state && state.rooms) || []).find(r => String(r.id) === String(z.room_id));
      const out = [];
      if (!sala || !state.tiles) return out;
      for (let y = sala.y; y < sala.y + sala.h; y++)
        for (let x = sala.x; x < sala.x + sala.w; x++) {
          const t = state.tiles[y] && state.tiles[y][x];
          if (t === TILE_PISO || t === TILE_PORTA) out.push([x, y]);
        }
      return out;
    }
    return (z.tiles || []).map(c => [Number(c[0]), Number(c[1])]);
  }

  // elemento: 'fire' | 'cold' | 'lightning'; casas: [[x,y],...] atingidas diretamente.
  // Devolve só os tipos que reagem: { choque, ignicao, congelar, gas, derreter } -> [[x,y],...].
  function preverReacoes(state, elemento, casas) {
    const out = {};
    const lista = (casas || []).map(c => [Number(c[0]), Number(c[1])]);
    if (!state || !lista.length) return out;
    if (elemento === 'lightning') {
      const r = _regiao(lista, (x, y) => _ehAgua(state, x, y), RAIO_CHOQUE, TETO_CHOQUE);
      if (r.length) out.choque = r;
    } else if (elemento === 'cold') {
      const r = lista.filter(c => _ehAgua(state, c[0], c[1])
        || (_mat(state, c[0], c[1]) === 'lava' && !_sobPonte(state, c[0], c[1])));
      if (r.length) out.congelar = r;
    } else if (elemento === 'fire') {
      const zonas = (state.zonas_especiais || []).filter(z => z && z.ativa);
      const emChamas = new Set();
      for (const z of zonas) if (z.tipo === 'chamas_piche') for (const c of (z.tiles || [])) emChamas.add(_chave(c));
      const piche = _regiao(lista,
        (x, y) => _mat(state, x, y) === 'piche' && !_sobPonte(state, x, y) && !emChamas.has(`${x},${y}`),
        null, TETO_PICHE);
      if (piche.length) out.ignicao = piche;
      const atingidas = new Set(lista.map(_chave));
      const gas = [], vistoGas = new Set();
      for (const z of zonas) {
        if (z.tipo !== 'camara_gas' && z.tipo !== 'nuvem_gas') continue;
        const cs = _casasDoGas(state, z);
        if (!cs.some(c => atingidas.has(_chave(c)))) continue;
        for (const c of cs) { const k = _chave(c); if (!vistoGas.has(k)) { vistoGas.add(k); gas.push(c); } }
      }
      if (gas.length) { gas.sort((a, b) => (a[1] - b[1]) || (a[0] - b[0])); out.gas = gas; }
      const gelo = _regiao(lista, (x, y) => _ehGelo(state, x, y), RAIO_DERRETER, TETO_DERRETER);
      if (gelo.length) out.derreter = gelo;
    }
    return out;
  }

  // Casas ocupadas por criaturas que sofreriam dano da reação (anel na mira). `tilesDe(criatura)` devolve
  // as casas do footprint (o game.js passa GS.monsterTiles para monstros).
  function alvosDasReacoes(state, previsao, casas, tilesDe) {
    const out = [];
    if (!state || !previsao) return out;
    const dentro = (lista, c) => lista.some(t => t[0] === c[0] && t[1] === c[1]);
    const atingidas = (casas || []).map(c => [Number(c[0]), Number(c[1])]);
    const criaturas = [];
    for (const p of (state.players || [])) if (p && p.alive !== false && (p.hp == null || p.hp > 0) && Array.isArray(p.pos) && p.pos[0] >= 0) criaturas.push(p);
    for (const m of (state.monsters || [])) if (m && m.hp > 0 && Array.isArray(m.pos)) criaturas.push(m);
    for (const c of criaturas) {
      const tiles = (tilesDe ? tilesDe(c) : [c.pos]).map(t => [Number(t[0]), Number(t[1])]);
      const voa = Number(c.altura || 0) > 0;
      let afeta = false;
      if (previsao.gas && tiles.some(t => dentro(previsao.gas, t))) afeta = true;            // o gás ocupa o ar também
      if (!voa) {
        if (previsao.choque && tiles.some(t => dentro(previsao.choque, t))
            && !tiles.some(t => dentro(atingidas, t))) afeta = true;                          // quem levou o golpe não repete
        if (previsao.congelar && tiles.some(t => dentro(previsao.congelar, t))) afeta = true;
        if (previsao.ignicao && tiles.some(t => dentro(previsao.ignicao, t))) afeta = true;
      }
      if (afeta) for (const t of tiles) out.push(t);
    }
    return out;
  }

  window.ReacoesElementais = { estilo, crostasAcabando, descreverCasa, preverReacoes, alvosDasReacoes };
})();
