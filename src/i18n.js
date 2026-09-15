'use strict';
// ─── IDIOMA (i18n) — motor PURO do cliente ─────────────────────────────────
// Gêmeo do bloco de i18n do server.py: mesmo dicionário (src/lang/strings.js),
// mesma regra de fallback, mesma substituição de {parametro} por nome.
//
// Este módulo NÃO toca no DOM (regra do CLAUDE.md). Quem aplica na tela é o
// game.js, via _i18nApply(); quem persiste a escolha também é o game.js.
(function () {
  const DICT = (typeof window !== 'undefined' && window.LANG_STRINGS) || {};
  const PADRAO = 'pt';
  const SUPORTADOS = ['pt', 'en'];
  const PARAM = /\{(\w+)\}/g;

  let lang = PADRAO;
  const ouvintes = [];

  // Gêmeo do _param_texto do server.py: um parâmetro pode ser uma LISTA de
  // fragmentos, que se junta com separador do próprio idioma (" e " × " and ").
  // A recursão com t() termina porque `lista.separador` e `lista.ultimo` não
  // têm parâmetros — não dê parâmetros a elas.
  function _valor(v) {
    if (!Array.isArray(v)) return String(v);
    const itens = v.map(_valor);
    if (!itens.length)      return '';
    if (itens.length === 1) return itens[0];
    return itens.slice(0, -1).join(t('lista.separador'))
           + t('lista.ultimo') + itens[itens.length - 1];
  }

  // Sem tradução no idioma pedido → português. Sem a chave → devolve a própria
  // chave: aparece na tela (fica óbvio o que falta traduzir) e nada quebra.
  function t(key, params) {
    const entry = DICT[key];
    if (!entry) {
      console.warn('[i18n] chave ausente:', key);
      return key;
    }
    let text = entry[lang] || entry[PADRAO] || key;
    if (params) {
      text = text.replace(PARAM, (m, k) => (k in params ? _valor(params[k]) : m));
    }
    return text;
  }

  function setLang(code) {
    if (SUPORTADOS.indexOf(code) < 0 || code === lang) return;
    lang = code;
    for (const fn of ouvintes) {
      try { fn(code); } catch (e) { console.error('[i18n] ouvinte falhou:', e); }
    }
  }

  // ── Nomes de catálogo ──────────────────────────────────────────────────────
  // As chaves são cat.<família>.<id>.nome, geradas por tools/gerar_vocabulario.py.
  // O id já viaja no payload, então o nome traduzido é achado sem o servidor
  // precisar mandar nada novo. Ordem de busca por campo — não há colisão de id
  // entre famílias hoje, e o gerador falha alto se aparecer uma.
  const FAMILIAS_POR_CAMPO = {
    type: ['monstro', 'decor'],
    id:   ['item', 'guilda', 'magia', 'instrumento', 'armadilha', 'classe', 'local',
           'habilidade'],
  };
  const CAMPOS_NOME = ['name', 'nome'];
  // 'description' é como o servidor escreve a descrição das HABILIDADES de herói
  // (CLASSES[x].skills). Sem ele o nome traduzia e a descrição ficava em português.
  const CAMPOS_DESC = ['desc', 'descricao', 'description'];
  // Usada quando o id vem da CHAVE do dicionário pai, caso em que não há campo
  // interno indicando de que família ele é.
  const TODAS_FAMILIAS = ['monstro', 'decor', 'item', 'guilda', 'magia', 'habilidade',
                          'instrumento', 'armadilha', 'classe', 'local'];

  function tem(key) {
    return Object.prototype.hasOwnProperty.call(DICT, key);
  }

  // Primeiro prefixo cat.<família>.<id> que tenha nome OU descrição no
  // dicionário. Aceitar qualquer um dos dois importa: há entradas com descrição
  // traduzida e sem nome, e o contrário.
  // A busca inclui `ui.<família>.<id>` além de `cat.` porque nem todo objeto do
  // catálogo do CLIENTE tem contraparte no servidor: 40 itens do CATALOGO_ITENS
  // só existem em src/gameState.js, e para eles nunca haverá uma `cat.*`. Sem
  // isto uma chave ui.* sozinha nunca era encontrada — a base ficava nula e o
  // objeto passava intacto. O `cat.` vem primeiro para o comportamento de quem
  // TEM as duas continuar idêntico: quem escolhe entre elas é o aplicarCatalogo,
  // logo abaixo, e lá a ui.* é que vence.
  function _tentaFamilias(familias, id) {
    for (const fam of familias) {
      for (const pre of ['cat.', 'ui.']) {
        const base = pre + fam + '.' + id;
        if (tem(base + '.nome') || tem(base + '.desc')) {
          return 'cat.' + fam + '.' + id;
        }
      }
    }
    return null;
  }

  // `idPai` é a chave sob a qual este objeto estava no dicionário pai. Vários
  // payloads (lobby_state.classes, game_start.instrumentos_base) são dicionários
  // chaveados pelo id, com o valor sem nenhum campo de id dentro.
  function _chaveBase(o, idPai) {
    for (const campoId in FAMILIAS_POR_CAMPO) {
      const id = o[campoId];
      if (typeof id !== 'string' || !id) continue;
      const base = _tentaFamilias(FAMILIAS_POR_CAMPO[campoId], id);
      if (base) return base;
    }
    if (typeof idPai === 'string' && idPai) {
      const base = _tentaFamilias(TODAS_FAMILIAS, idPai);
      if (base) return base;
    }
    return null;
  }

  // ── Nomes compostos (etapa 4c) ─────────────────────────────────────────────
  // Gêmeo de nome_item / _instrumento_nome_T do server.py, lendo AS MESMAS
  // chaves (src/lang/composto.js). Existe porque o nome composto não está em
  // catálogo nenhum: o instrumento tem id único por combinação, e o sufixo de
  // corroído/contagem é derivado de CAMPO, não do nome — o servidor parou de
  // colar esses sufixos na string justamente para o nome poder ser traduzido.
  const GENERO_FEM = ['harpa', 'trompa', 'lira', 'flauta', 'gaita'];
  const COM_ORIGEM = ['elfica', 'ana'];

  function _instrumentoComposto(o) {
    if (o.tipo_item !== 'instrumento' || typeof o.base !== 'string') return null;
    const g = GENERO_FEM.indexOf(o.base) >= 0 ? 'f' : 'm';
    const adj = (n) => t('cat.instrumento.adj.' + n + '.' + g);
    const orig = o.origem || 'humana';
    const runico = o.encantamento === 'runico';
    const base = tem('cat.instrumento.' + o.base + '.nome')
      ? t('cat.instrumento.' + o.base + '.nome') : (o.name || o.nome || '');
    // Lendário: 3 eixos no máximo → substitui a qualidade E o sufixo Rúnico.
    if (o.qualidade === 'refinado' && COM_ORIGEM.indexOf(orig) >= 0 && runico) {
      return t('cat.instrumento.nome_composto',
               { base: base, ql: adj('lendario'), orig: adj(orig), run: '' });
    }
    return t('cat.instrumento.nome_composto', {
      base: base,
      ql:   adj(o.qualidade || 'padrao'),
      orig: COM_ORIGEM.indexOf(orig) >= 0 ? adj(orig) : '',
      run:  runico ? adj('runico') : '',
    });
  }

  // Recebe o nome JÁ traduzido pelo caminho normal e recoloca o que o filtro
  // comeria. Idempotente para item de catálogo (parte sempre do nome do
  // catálogo); para item autoral parte do nome cru, então não reaplique no
  // mesmo objeto — cada mensagem que chega é um objeto novo.
  function _comSufixos(o, nome) {
    if (o.ammo_count) {
      const curto = 'cat.item.' + o.id + '.nome_curto';
      return t('cat.item.municao_x',
               { nome: tem(curto) ? t(curto) : nome, n: o.ammo_count });
    }
    if (o.corrosao_inicial) return t('cat.item.corroido', { nome: nome });
    return nome;
  }

  // Percorre a estrutura e troca nome (e descrição, se soNome for falso) pelo
  // idioma ATUAL. Muta o objeto de propósito. Objeto sem chave no dicionário
  // fica intacto — é assim que item e monstro criados no editor mantêm o nome
  // autoral. Sem saída antecipada em português: os catálogos estáticos do
  // cliente precisam ser reescritos na volta ao português para restaurar o
  // texto original. A troca é por id, nunca por texto, então reaplicar noutro
  // idioma sempre parte da chave e nunca do texto já trocado.
  function aplicarCatalogo(obj, soNome) {
    const vistos = new Set();
    (function anda(o, idPai) {
      if (!o || typeof o !== 'object' || vistos.has(o)) return;
      vistos.add(o);
      if (Array.isArray(o)) { for (const v of o) anda(v, null); return; }
      const base = _chaveBase(o, idPai);
      // A chave ui.* (do CLIENTE) vence a cat.* (do servidor) quando as duas
      // existem: os catálogos do cliente guardam um card HTML com alcance e
      // efeito por rodada, contra uma frase curta no servidor. A etapa 3 evitou
      // o choque passando soNome=true e deixando a descrição de fora; a chave
      // própria resolve sem perder informação. Sem ui.*, tudo segue como antes —
      // e é isso que torna seguro ligar soNome=false antes de escrever todas as
      // chaves.
      const baseUi = base && base.replace(/^cat\./, 'ui.');
      const kNome = (baseUi && tem(baseUi + '.nome')) ? baseUi + '.nome'
                  : (base && tem(base + '.nome'))     ? base + '.nome' : null;
      const kDesc = (baseUi && tem(baseUi + '.desc')) ? baseUi + '.desc'
                  : (base && tem(base + '.desc'))     ? base + '.desc' : null;
      const composto = _instrumentoComposto(o);
      if (composto !== null) {
        for (const campo of CAMPOS_NOME) {
          if (typeof o[campo] === 'string') { o[campo] = composto; break; }
        }
      } else if (kNome) {
        for (const campo of CAMPOS_NOME) {
          if (typeof o[campo] === 'string') {
            o[campo] = _comSufixos(o, t(kNome)); break;
          }
        }
      } else if (typeof o.id === 'string' && (o.ammo_count || o.corrosao_inicial)) {
        // Item AUTORAL: sem chave de catálogo, o nome fica o do autor — mas o
        // sufixo ainda vale, senão o jogador não vê que a peça está corroída.
        for (const campo of CAMPOS_NOME) {
          if (typeof o[campo] === 'string') { o[campo] = _comSufixos(o, o[campo]); break; }
        }
      }
      if (kDesc && !soNome) {
        for (const campo of CAMPOS_DESC) {
          if (typeof o[campo] === 'string') { o[campo] = t(kDesc); break; }
        }
      }
      // `custo` é campo só do GRIMORIO_CLIENT (o servidor não o manda), então a
      // chave é sempre ui.<família>.<id>.custo — sem par cat.*.
      if (baseUi && !soNome && typeof o.custo === 'string' && tem(baseUi + '.custo')) {
        o.custo = t(baseUi + '.custo');
      }
      // `custo` é campo só do GRIMORIO_CLIENT (o servidor não o manda), então a
      // chave é sempre ui.<família>.<id>.custo — sem par cat.*.
      if (baseUi && !soNome && typeof o.custo === 'string' && tem(baseUi + '.custo')) {
        o.custo = t(baseUi + '.custo');
      }
      for (const k in o) anda(o[k], k);
    })(obj, null);
    return obj;
  }

  // Caminho das mensagens: em português não há o que trocar, e sair aqui deixa
  // o custo em zero no idioma padrão.
  function traduzirNomes(msg) {
    if (lang === PADRAO) return msg;
    return aplicarCatalogo(msg, false);
  }

  window.I18N = {
    t: t,
    tem: tem,
    traduzirNomes: traduzirNomes,
    aplicarCatalogo: aplicarCatalogo,
    setLang: setLang,
    on: function (fn) { if (typeof fn === 'function') ouvintes.push(fn); },
    get lang() { return lang; },
    SUPORTADOS: SUPORTADOS,
    PADRAO: PADRAO,
  };
})();
