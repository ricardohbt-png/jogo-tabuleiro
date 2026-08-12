// NOMES COMPOSTOS — as peças que montam um nome que não existe pronto em
// catálogo nenhum (etapa 4c do idioma).
//
// Mantido À MÃO, como o erros.js e o narracao.js: o gerador
// (tools/gerar_vocabulario.py) só emite .nome e .desc a partir dos catálogos do
// server.py, então nada aqui pode nascer dele.
//
// Nos adjetivos de instrumento o ESPAÇO vem embutido no lado certo de cada
// idioma — " Velha" em português (adjetivo depois) e "Old " em inglês (antes).
// É isso que faz uma parte ausente não deixar espaço solto, e é o que permite a
// cada idioma escolher a sua ordem no template. Os rótulos em português têm de
// bater EXATAMENTE com _QUALIDADE_LABEL / _ORIGEM_LABEL / _RUNICO_LABEL /
// _LENDARIO_LABEL do server.py.
window.LANG_COMPOSTO = {
  "cat.monstro.animado":                 {"pt": "{nome} Animado",    "en": "Animated {nome}"},
  "cat.monstro.elemental_descontrolado": {"pt": "Elemental Descontrolado",
                                          "en": "Uncontrolled Elemental"},
  "cat.item.corroido":                   {"pt": "{nome} (corroído)", "en": "{nome} (corroded)"},
  "cat.item.municao_x":                  {"pt": "{nome} (×{n})",     "en": "{nome} (×{n})"},

  "cat.item.flechas.nome_curto":            {"pt": "Flechas", "en": "Arrows"},
  "cat.item.virotes.nome_curto":            {"pt": "Virotes", "en": "Bolts"},
  "cat.item.flechas_prata.nome_curto":      {"pt": "Flechas de Prata", "en": "Silver Arrows"},
  "cat.item.virotes_prata.nome_curto":      {"pt": "Virotes de Prata", "en": "Silver Bolts"},
  "cat.item.virote_incendiario.nome_curto": {"pt": "Virote Incendiário",
                                             "en": "Incendiary Bolt"},
  "cat.item.flecha_incendiaria.nome_curto": {"pt": "Flecha Incendiária",
                                             "en": "Incendiary Arrow"},

  "cat.instrumento.nome_composto": {"pt": "{base}{ql}{orig}{run}",
                                    "en": "{ql}{run}{orig}{base}"},

  "cat.instrumento.adj.velho.m":    {"pt": " Velho",    "en": "Old "},
  "cat.instrumento.adj.velho.f":    {"pt": " Velha",    "en": "Old "},
  "cat.instrumento.adj.rustico.m":  {"pt": " Rústico",  "en": "Rustic "},
  "cat.instrumento.adj.rustico.f":  {"pt": " Rústica",  "en": "Rustic "},
  "cat.instrumento.adj.padrao.m":   {"pt": " Padrão",   "en": "Standard "},
  "cat.instrumento.adj.padrao.f":   {"pt": " Padrão",   "en": "Standard "},
  "cat.instrumento.adj.refinado.m": {"pt": " Refinado", "en": "Refined "},
  "cat.instrumento.adj.refinado.f": {"pt": " Refinada", "en": "Refined "},
  "cat.instrumento.adj.elfica.m":   {"pt": " Élfico",   "en": "Elven "},
  "cat.instrumento.adj.elfica.f":   {"pt": " Élfica",   "en": "Elven "},
  "cat.instrumento.adj.ana.m":      {"pt": " Anão",     "en": "Dwarven "},
  "cat.instrumento.adj.ana.f":      {"pt": " Anã",      "en": "Dwarven "},
  "cat.instrumento.adj.runico.m":   {"pt": " Rúnico",   "en": "Runic "},
  "cat.instrumento.adj.runico.f":   {"pt": " Rúnica",   "en": "Runic "},
  "cat.instrumento.adj.lendario.m": {"pt": " Lendário", "en": "Legendary "},
  "cat.instrumento.adj.lendario.f": {"pt": " Lendária", "en": "Legendary "}
};
Object.assign(window.LANG_STRINGS, window.LANG_COMPOSTO);
