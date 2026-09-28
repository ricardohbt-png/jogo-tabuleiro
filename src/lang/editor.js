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
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_EDITOR);
