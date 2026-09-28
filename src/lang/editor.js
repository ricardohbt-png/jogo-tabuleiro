// EDITOR (tools/editor.html e tools/*.js) — rótulos, botões e mensagens do editor.
//
// Separado do interface.js porque o editor é outra aplicação, carregada por outra
// página. Mantido À MÃO, como o interface.js/erros.js. Convenção de chave:
// ui.editor.<aba>.<slug>; a moldura (topo, abas, rodapé) usa ui.editor.topo.*.
// O servidor também funde este arquivo (_load_lang lê todo src/lang/*.js).
//
// REGRAS: JSON estrito DENTRO do objeto (aspas duplas, sem vírgula sobrando,
// sem comentário lá dentro). Parâmetros {nome}, iguais nos dois idiomas.
window.LANG_EDITOR = {
  "ui.editor.topo.titulo": {
    "en": "Dungeon Editor — Legends for Hire",
    "pt": "Editor de Masmorras — Legends for Hire"
  },
  "ui.editor.topo.idioma": {
    "en": "Language",
    "pt": "Idioma"
  },
  "ui.editor.topo.aba.masmorra": {
    "en": "Dungeon",
    "pt": "Masmorra"
  },
  "ui.editor.topo.aba.bestiario": {
    "en": "Bestiary",
    "pt": "Bestiário"
  },
  "ui.editor.topo.aba.editor_monstros": {
    "en": "Creature editor",
    "pt": "Editor de criaturas"
  },
  "ui.editor.topo.aba.editor_itens": {
    "en": "Item editor",
    "pt": "Editor de itens"
  },
  "ui.editor.topo.aba.cidade": {
    "en": "City",
    "pt": "Cidade"
  },
  "ui.editor.topo.aba.mapa_mundi": {
    "en": "World Map",
    "pt": "Mapa do Mundo"
  },
  "ui.editor.topo.aba.campanha": {
    "en": "Campaign",
    "pt": "Campanha"
  },
  "ui.editor.topo.aba.cenas": {
    "en": "Scenes",
    "pt": "Cenas"
  },
  "ui.editor.topo.nome": {
    "en": "name",
    "pt": "nome"
  },
  "ui.editor.topo.ambiente": {
    "en": "environment",
    "pt": "ambiente"
  },
  "ui.editor.topo.ambiente.masmorra": {
    "en": "Dungeon",
    "pt": "Masmorra"
  },
  "ui.editor.topo.ambiente.penumbra": {
    "en": "Dim (dark)",
    "pt": "Penumbra (escuro)"
  },
  "ui.editor.topo.ambiente.ar_livre": {
    "en": "Open air (bright)",
    "pt": "Ar livre (claro)"
  },
  "ui.editor.topo.saida_escada": {
    "en": "🚪 exit by the stairs",
    "pt": "🚪 saída pela escada"
  },
  "ui.editor.topo.saida_escada_dica": {
    "en": "If unchecked, heroes cannot leave the dungeon through the entrance stairs",
    "pt": "Se desmarcado, os heróis não podem deixar a masmorra pela escada de entrada"
  },
  "ui.editor.topo.aplicar_grid": {
    "en": "Apply grid",
    "pt": "Aplicar grid"
  },
  "ui.editor.topo.carregar": {
    "en": "Load",
    "pt": "Carregar"
  },
  "ui.editor.topo.salvar": {
    "en": "Save",
    "pt": "Salvar"
  },
  "ui.editor.topo.visualizar_3d": {
    "en": "◈ Preview in 3D",
    "pt": "◈ Visualizar em 3D"
  },
  "ui.editor.topo.visualizar_3d_dica": {
    "en": "Previews the current dungeon without saving",
    "pt": "Visualiza a masmorra atual sem salvar"
  },
  "ui.editor.topo.testar_mestre": {
    "en": "🧪 Test as Game Master",
    "pt": "🧪 Testar como Mestre"
  },
  "ui.editor.topo.abrindo_teste": {
    "en": "🧪 Opening test…",
    "pt": "🧪 Abrindo teste…"
  },
  "ui.editor.topo.testar_mestre_dica": {
    "en": "Opens a temporary session to test monsters and abilities",
    "pt": "Abre uma sessão temporária para testar monstros e habilidades"
  },
  "ui.editor.topo.painel_vazio": {
    "en": "Select a tool and draw.",
    "pt": "Selecione uma ferramenta e desenhe."
  },
  "ui.editor.topo.coordenadas_dica": {
    "en": "Square under the cursor: (x = column, y = row), counting from 0 at the top-left corner",
    "pt": "Casa sob o cursor: (x = coluna, y = linha), contando de 0 no canto superior esquerdo"
  },
  "ui.editor.masmorra.nome_padrao": {
    "en": "New Dungeon",
    "pt": "Nova Masmorra"
  },
  "ui.editor.masmorra.grupo.tiles": {
    "en": "tiles",
    "pt": "tiles"
  },
  "ui.editor.masmorra.grupo.entidades": {
    "en": "entities",
    "pt": "entidades"
  },
  "ui.editor.masmorra.grupo.acoes": {
    "en": "actions",
    "pt": "ações"
  },
  "ui.editor.masmorra.ferramenta.wall": {
    "en": "wall",
    "pt": "parede"
  },
  "ui.editor.masmorra.ferramenta.floor": {
    "en": "floor",
    "pt": "chão"
  },
  "ui.editor.masmorra.ferramenta.door": {
    "en": "door",
    "pt": "porta"
  },
  "ui.editor.masmorra.ferramenta.altura": {
    "en": "height",
    "pt": "altura"
  },
  "ui.editor.masmorra.ferramenta.ponte": {
    "en": "bridge",
    "pt": "ponte"
  },
  "ui.editor.masmorra.ferramenta.entrance": {
    "en": "entrance",
    "pt": "entrada"
  },
  "ui.editor.masmorra.ferramenta.hero_spawn": {
    "en": "hero start",
    "pt": "início herói"
  },
  "ui.editor.masmorra.ferramenta.exit": {
    "en": "exit",
    "pt": "saída"
  },
  "ui.editor.masmorra.ferramenta.monster": {
    "en": "monster",
    "pt": "monstro"
  },
  "ui.editor.masmorra.ferramenta.chest": {
    "en": "chest",
    "pt": "baú"
  },
  "ui.editor.masmorra.ferramenta.trap": {
    "en": "trap",
    "pt": "armadilha"
  },
  "ui.editor.masmorra.ferramenta.prisoner": {
    "en": "prisoner",
    "pt": "prisioneiro"
  },
  "ui.editor.masmorra.ferramenta.decor": {
    "en": "decoration",
    "pt": "decoração"
  },
  "ui.editor.masmorra.ferramenta.secret_mechanism": {
    "en": "secret passage",
    "pt": "passagem secreta"
  },
  "ui.editor.masmorra.ferramenta.illusion_wall": {
    "en": "illusory wall",
    "pt": "parede ilusória"
  },
  "ui.editor.masmorra.ferramenta.fala": {
    "en": "NPC line",
    "pt": "fala NPC"
  },
  "ui.editor.masmorra.ferramenta.room": {
    "en": "room",
    "pt": "sala"
  },
  "ui.editor.masmorra.ferramenta.select": {
    "en": "select",
    "pt": "selecionar"
  },
  "ui.editor.masmorra.ferramenta.erase": {
    "en": "erase",
    "pt": "apagar"
  },
  "ui.editor.masmorra.loot.armas": {
    "en": "Weapons",
    "pt": "Armas"
  },
  "ui.editor.masmorra.loot.armaduras": {
    "en": "Armor",
    "pt": "Armaduras"
  },
  "ui.editor.masmorra.loot.escudos": {
    "en": "Shields",
    "pt": "Escudos"
  },
  "ui.editor.masmorra.loot.venenos": {
    "en": "Poisons",
    "pt": "Venenos"
  },
  "ui.editor.masmorra.loot.arremessaveis": {
    "en": "Throwables",
    "pt": "Arremessáveis"
  },
  "ui.editor.masmorra.loot.instrumentos": {
    "en": "Instruments",
    "pt": "Instrumentos"
  },
  "ui.editor.masmorra.loot.municoes": {
    "en": "Ammunition",
    "pt": "Munições"
  },
  "ui.editor.masmorra.loot.pocoes": {
    "en": "Potions and consumables",
    "pt": "Poções e consumíveis"
  },
  "ui.editor.masmorra.loot.aneis": {
    "en": "Rings and accessories",
    "pt": "Anéis e acessórios"
  },
  "ui.editor.masmorra.loot.outros": {
    "en": "Other",
    "pt": "Outros"
  },
  "ui.editor.masmorra.licao.mover_ate": {
    "en": "reach a square",
    "pt": "chegar a uma casa"
  },
  "ui.editor.masmorra.licao.abrir_porta": {
    "en": "open a door",
    "pt": "abrir uma porta"
  },
  "ui.editor.masmorra.licao.atacar": {
    "en": "land an attack",
    "pt": "acertar um ataque"
  },
  "ui.editor.masmorra.licao.matar": {
    "en": "defeat a monster",
    "pt": "derrotar um monstro"
  },
  "ui.editor.masmorra.licao.pegar_item": {
    "en": "pick up an item",
    "pt": "pegar um item"
  },
  "ui.editor.masmorra.licao.equipar": {
    "en": "equip an item",
    "pt": "equipar um item"
  },
  "ui.editor.masmorra.licao.encerrar_turno": {
    "en": "end the turn",
    "pt": "encerrar o turno"
  },
  "ui.editor.masmorra.licao.usar_item": {
    "en": "use an item (eat, drink, potion)",
    "pt": "usar um item (comer, beber, poção)"
  },
  "ui.editor.masmorra.licao.usar_magia": {
    "en": "cast a spell",
    "pt": "lançar uma magia"
  },
  "ui.editor.masmorra.licao.usar_habilidade": {
    "en": "use a class ability",
    "pt": "usar uma habilidade de classe"
  },
  "ui.editor.masmorra.licao.usar_tecnica": {
    "en": "use a Guild technique",
    "pt": "usar uma técnica da Guilda"
  },
  "ui.editor.masmorra.licao.usar_instrumento": {
    "en": "play the instrument (bard)",
    "pt": "tocar o instrumento (bardo)"
  },
  "ui.editor.masmorra.licao.arremessar_item": {
    "en": "throw an item (oil, bomb)",
    "pt": "arremessar um item (óleo, bomba)"
  },
  "ui.editor.masmorra.licao.desarmar_armadilha": {
    "en": "disarm a trap",
    "pt": "desarmar uma armadilha"
  },
  "ui.editor.masmorra.visao.livre": {
    "en": "clear — does not block vision",
    "pt": "livre — não bloqueia a visão"
  },
  "ui.editor.masmorra.visao.baixo": {
    "en": "low — see and shoot over it, half cover (+2 AC)",
    "pt": "baixo — vê e atira por cima, meia cobertura (+2 CA)"
  },
  "ui.editor.masmorra.visao.alto": {
    "en": "tall — blocks vision and shots, casts a shadow",
    "pt": "alto — bloqueia visão e tiro, projeta sombra"
  },
  "ui.editor.masmorra.maldicao.leve": {
    "en": "Mild",
    "pt": "Leve"
  },
  "ui.editor.masmorra.maldicao.media": {
    "en": "Moderate",
    "pt": "Média"
  },
  "ui.editor.masmorra.maldicao.grave": {
    "en": "Severe",
    "pt": "Grave"
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_EDITOR);
