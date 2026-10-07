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
  },
  "ui.editor.masmorra.barra.hint_heroi": {
    "en": "Click the map to place or move this hero.",
    "pt": "Clique no mapa para posicionar ou mover este herói."
  },
  "ui.editor.masmorra.barra.decor_chao": {
    "en": "Floor decorations",
    "pt": "Decorações de chão"
  },
  "ui.editor.masmorra.barra.decor_parede": {
    "en": "Wall decorations",
    "pt": "Decorações de parede"
  },
  "ui.editor.masmorra.barra.girar_90": {
    "en": "rotate 90° (R)",
    "pt": "girar 90° (R)"
  },
  "ui.editor.masmorra.barra.pincel_ativo": {
    "en": "🖌️ area brush active",
    "pt": "🖌️ pincel de área ativo"
  },
  "ui.editor.masmorra.barra.pincel_usar": {
    "en": "🖌️ use copy as brush",
    "pt": "🖌️ usar cópia como pincel"
  },
  "ui.editor.masmorra.barra.pincel_title": {
    "en": "With the brush active, drag on the map to fill the area with copies.",
    "pt": "Com o pincel ativo, arraste no mapa para preencher a área com cópias."
  },
  "ui.editor.masmorra.barra.arraste_preencher": {
    "en": "Drag to fill; invalid squares are ignored.",
    "pt": "Arraste para preencher; casas inválidas são ignoradas."
  },
  "ui.editor.masmorra.barra.porta_girar": {
    "en": "↻ door 90° (R)",
    "pt": "↻ porta 90° (R)"
  },
  "ui.editor.masmorra.barra.porta_girar_title": {
    "en": "Rotate the selected door's image",
    "pt": "Girar a imagem da porta selecionada"
  },
  "ui.editor.masmorra.barra.movimento_penalidade": {
    "en": " (−{n} movement)",
    "pt": " (−{n} movimento)"
  },
  "ui.editor.masmorra.barra.balde_on": {
    "en": "bucket: ON",
    "pt": "balde: ON"
  },
  "ui.editor.masmorra.barra.balde_off": {
    "en": "bucket: OFF",
    "pt": "balde: OFF"
  },
  "ui.editor.masmorra.barra.balde_title": {
    "en": "Fills the contiguous region of the same structure",
    "pt": "Preenche a região contígua de mesma estrutura"
  },
  "ui.editor.masmorra.barra.nivel.depressao": {
    "en": "depression",
    "pt": "depressão"
  },
  "ui.editor.masmorra.barra.nivel.nivelar": {
    "en": "level out",
    "pt": "nivelar"
  },
  "ui.editor.masmorra.barra.nivel.elevado": {
    "en": "raised",
    "pt": "elevado"
  },
  "ui.editor.masmorra.barra.nivel.muito_elevado": {
    "en": "very raised",
    "pt": "muito elevado"
  },
  "ui.editor.masmorra.barra.nivel_generico": {
    "en": "level {n}",
    "pt": "nível {n}"
  },
  "ui.editor.masmorra.barra.altura_parede_dica": {
    "en": "On a wall: 0 to +10 sets its height; −1 returns it to automatic (follows the highest floor around it)",
    "pt": "Em parede: 0 a +10 fixa a altura; −1 volta ao automático (acompanha o chão mais alto ao redor)"
  },
  "ui.editor.masmorra.barra.transicao_title": {
    "en": "Chooses the appearance of transitions between different levels",
    "pt": "Escolhe a aparência das transições entre níveis diferentes"
  },
  "ui.editor.masmorra.barra.transicao_rampa": {
    "en": "transition: ramp",
    "pt": "transição: rampa"
  },
  "ui.editor.masmorra.barra.transicao_declive": {
    "en": "transition: slope",
    "pt": "transição: declive"
  },
  "ui.editor.masmorra.barra.altura_hint": {
    "en": "Click and drag on the floor; height is only visual in this phase.",
    "pt": "Clique e arraste no chão; a altura é apenas visual nesta fase."
  },
  "ui.editor.masmorra.barra.ponte_largura_singular": {
    "en": "width: {n} square",
    "pt": "largura: {n} quadrado"
  },
  "ui.editor.masmorra.barra.ponte_largura_plural": {
    "en": "width: {n} squares",
    "pt": "largura: {n} quadrados"
  },
  "ui.editor.masmorra.barra.ponte_material_madeira": {
    "en": "material: wood",
    "pt": "material: madeira"
  },
  "ui.editor.masmorra.barra.ponte_material_pedra": {
    "en": "material: rough stone",
    "pt": "material: pedra rústica"
  },
  "ui.editor.masmorra.barra.ponte_hint": {
    "en": "Drag between points of the same height; the bridge doesn't change the terrain below.",
    "pt": "Arraste entre pontos da mesma altura; a ponte não altera o terreno abaixo."
  },
  "ui.editor.masmorra.painel.nenhuma_posicao_inicial": {
    "en": "No starting position defined yet.",
    "pt": "Nenhuma posição inicial definida."
  },
  "ui.editor.masmorra.painel.titulo": {
    "en": "Dungeon",
    "pt": "Masmorra"
  },
  "ui.editor.masmorra.painel.modo_inicio": {
    "en": "start mode",
    "pt": "modo de início"
  },
  "ui.editor.masmorra.painel.entrada_tradicional": {
    "en": "Traditional entrance",
    "pt": "Entrada tradicional"
  },
  "ui.editor.masmorra.painel.herois_separados": {
    "en": "Separate heroes",
    "pt": "Heróis separados"
  },
  "ui.editor.masmorra.painel.posicione_classe": {
    "en": "Position each class with the <b>hero start</b> tool. The dungeon won't have an entrance staircase.",
    "pt": "Posicione cada classe com a ferramenta <b>início herói</b>. A masmorra não terá escada de entrada."
  },
  "ui.editor.masmorra.painel.objetivo_principal": {
    "en": "primary objective",
    "pt": "objetivo principal"
  },
  "ui.editor.masmorra.painel.objetivos_secundarios": {
    "en": "secondary objectives",
    "pt": "objetivos secundários"
  },
  "ui.editor.masmorra.painel.remover": {
    "en": "remove",
    "pt": "remover"
  },
  "ui.editor.masmorra.painel.secundario": {
    "en": "secondary",
    "pt": "secundário"
  },
  "ui.editor.masmorra.painel.reforcos_mestre": {
    "en": "master's reinforcements",
    "pt": "reforços do mestre"
  },
  "ui.editor.masmorra.painel.nenhum_reforco": {
    "en": "No reinforcement registered yet.",
    "pt": "Nenhum reforço cadastrado."
  },
  "ui.editor.masmorra.painel.grupo_esperado": {
    "en": "expected party",
    "pt": "grupo esperado"
  },
  "ui.editor.masmorra.painel.herois": {
    "en": "heroes",
    "pt": "heróis"
  },
  "ui.editor.masmorra.painel.nivel": {
    "en": "level",
    "pt": "nível"
  },
  "ui.editor.masmorra.objetivo.kill_target": {
    "en": "Defeat the target",
    "pt": "derrotar o alvo"
  },
  "ui.editor.masmorra.objetivo.kill_all": {
    "en": "Defeat every monster",
    "pt": "eliminar todos os monstros"
  },
  "ui.editor.masmorra.objetivo.reach_exit": {
    "en": "Reach the exit",
    "pt": "chegar à saída"
  },
  "ui.editor.masmorra.objetivo.all_heroes_at_exit": {
    "en": "All heroes at the exit",
    "pt": "todos os heróis na saída"
  },
  "ui.editor.masmorra.objetivo.open_key_chest": {
    "en": "Open the key chest",
    "pt": "abrir o baú-chave"
  },
  "ui.editor.masmorra.objetivo.rescue_prisoner": {
    "en": "Rescue the prisoner",
    "pt": "resgatar o prisioneiro"
  },
  "ui.editor.masmorra.objetivo.salas_obrigatorias": {
    "en": "Required rooms",
    "pt": "salas obrigatórias"
  },
  "ui.editor.masmorra.painel.ponte_titulo": {
    "en": "Bridge",
    "pt": "Ponte"
  },
  "ui.editor.masmorra.painel.ponte_info": {
    "en": "{casas} squares · width {largura} · height {altura}",
    "pt": "{casas} casas · largura {largura} · altura {altura}"
  },
  "ui.editor.masmorra.painel.material": {
    "en": "Material",
    "pt": "Material"
  },
  "ui.editor.masmorra.painel.madeira": {
    "en": "Wood",
    "pt": "Madeira"
  },
  "ui.editor.masmorra.painel.pedra_rustica": {
    "en": "Rough stone",
    "pt": "Pedra rústica"
  },
  "ui.editor.masmorra.painel.ponte_hint": {
    "en": "The bridge doesn't change the terrain below. Creatures can fall off the sides when pushed.",
    "pt": "A ponte não altera o terreno abaixo. Criaturas podem cair pelas laterais ao serem empurradas."
  },
  "ui.editor.masmorra.painel.deletar_ponte": {
    "en": "Delete bridge",
    "pt": "Deletar ponte"
  },
  "ui.editor.masmorra.painel.porta_titulo": {
    "en": "Door",
    "pt": "Porta"
  },
  "ui.editor.masmorra.painel.frente_imagem": {
    "en": "Image front: {frente}",
    "pt": "Frente da imagem: {frente}"
  },
  "ui.editor.masmorra.painel.giros_aplicados": {
    "en": "Rotations applied: {n} × 90°",
    "pt": "Giros aplicados: {n} × 90°"
  },
  "ui.editor.masmorra.painel.girar_90_r": {
    "en": "Rotate 90° (R)",
    "pt": "Girar 90° (R)"
  },
  "ui.editor.masmorra.painel.seta_dourada_hint": {
    "en": "The golden arrow on the map shows the front. The orientation is saved on this door.",
    "pt": "A seta dourada no mapa mostra a frente. A orientação é salva nesta porta."
  },
  "ui.editor.masmorra.painel.condicao_abertura": {
    "en": "Optional opening condition",
    "pt": "Condição opcional de abertura"
  },
  "ui.editor.masmorra.painel.sem_condicao": {
    "en": "No condition",
    "pt": "Sem condição"
  },
  "ui.editor.masmorra.painel.item_chave": {
    "en": "Key item",
    "pt": "Item-chave"
  },
  "ui.editor.masmorra.painel.objeto_chave_ativado": {
    "en": "Activated key object",
    "pt": "Objeto-chave ativado"
  },
  "ui.editor.masmorra.painel.licao_cumprida": {
    "en": "Lesson completed",
    "pt": "Lição cumprida"
  },
  "ui.editor.masmorra.painel.crie_fala_tarefa": {
    "en": "Create a line with a task first.",
    "pt": "Crie primeiro uma fala com tarefa."
  },
  "ui.editor.masmorra.painel.licao_necessaria": {
    "en": "required lesson",
    "pt": "lição necessária"
  },
  "ui.editor.masmorra.painel.item_necessario": {
    "en": "required item",
    "pt": "item necessário"
  },
  "ui.editor.masmorra.painel.modo_ativacoes": {
    "en": "activation mode",
    "pt": "modo das ativações"
  },
  "ui.editor.masmorra.painel.qualquer_objeto": {
    "en": "any object",
    "pt": "qualquer objeto"
  },
  "ui.editor.masmorra.painel.todos_objetos": {
    "en": "all objects",
    "pt": "todos os objetos"
  },
  "ui.editor.masmorra.painel.objetos_chave": {
    "en": "key objects",
    "pt": "objetos-chave"
  },
  "ui.editor.masmorra.painel.marque_decor_chave": {
    "en": "Mark a decoration as a key object first.",
    "pt": "Marque primeiro uma decoração como objeto-chave."
  },
  "ui.editor.masmorra.painel.inicio_classe": {
    "en": "Start: {classe}",
    "pt": "Início: {classe}"
  },
  "ui.editor.masmorra.painel.trocar_heroi_hint": {
    "en": "To change the hero, select the \"hero start\" tool and choose another class.",
    "pt": "Para trocar de herói, selecione a ferramenta \"início herói\" e escolha outra classe."
  },
  "ui.editor.masmorra.painel.monstro_titulo": {
    "en": "Monster",
    "pt": "Monstro"
  },
  "ui.editor.masmorra.painel.tipo": {
    "en": "type",
    "pt": "tipo"
  },
  "ui.editor.masmorra.painel.chefe_boss": {
    "en": "boss",
    "pt": "chefe (boss)"
  },
  "ui.editor.masmorra.painel.alvo_objetivo": {
    "en": "objective target",
    "pt": "alvo do objetivo"
  },
  "ui.editor.masmorra.painel.voo_altitude": {
    "en": "Flight and altitude",
    "pt": "Voo e altitude"
  },
  "ui.editor.masmorra.painel.altura_escala_hint": {
    "en": "Height uses the 0–10 scale and affects weapon range.",
    "pt": "A altura usa a escala 0–10 e afeta o alcance das armas."
  },
  "ui.editor.masmorra.painel.altura_inicial": {
    "en": "starting height",
    "pt": "altura inicial"
  },
  "ui.editor.masmorra.painel.altura_maxima": {
    "en": "maximum height",
    "pt": "altura máxima"
  },
  "ui.editor.masmorra.painel.pode_subir_descer": {
    "en": "can go up/down",
    "pt": "pode subir/descer"
  },
  "ui.editor.masmorra.painel.custo_vertical": {
    "en": "vertical cost",
    "pt": "custo vertical"
  },
  "ui.editor.masmorra.painel.movimento_por_ponto": {
    "en": "movement per point",
    "pt": "movimento por ponto"
  },
  "ui.editor.masmorra.painel.ignora_obstaculos_voo": {
    "en": "ignores obstacles while flying",
    "pt": "ignora obstáculos no voo"
  },
  "ui.editor.masmorra.painel.sem_voo": {
    "en": "This type doesn't have the Flight ability.",
    "pt": "Este tipo não possui a habilidade Voo."
  },
  "ui.editor.masmorra.painel.tamanho_visual_sprite": {
    "en": "Sprite visual size",
    "pt": "Tamanho visual do sprite"
  },
  "ui.editor.masmorra.painel.tamanho_visual_hint": {
    "en": "doesn't change occupied squares or combat rules.",
    "pt": "não muda as casas ocupadas nem as regras de combate."
  },
  "ui.editor.masmorra.painel.escala_largura": {
    "en": "width scale",
    "pt": "escala largura"
  },
  "ui.editor.masmorra.painel.escala_altura": {
    "en": "height scale",
    "pt": "escala altura"
  },
  "ui.editor.masmorra.painel.bau_titulo": {
    "en": "Chest",
    "pt": "Baú"
  },
  "ui.editor.masmorra.painel.ouro": {
    "en": "gold",
    "pt": "ouro"
  },
  "ui.editor.masmorra.painel.bau_chave": {
    "en": "key chest",
    "pt": "baú-chave"
  },
  "ui.editor.masmorra.painel.itens": {
    "en": "items",
    "pt": "itens"
  },
  "ui.editor.masmorra.painel.item": {
    "en": "item",
    "pt": "item"
  },
  "ui.editor.masmorra.painel.armadilha_titulo": {
    "en": "Trap",
    "pt": "Armadilha"
  },
  "ui.editor.masmorra.painel.ajustes_armadilha": {
    "en": "Adjustments for this trap",
    "pt": "Ajustes desta armadilha"
  },
  "ui.editor.masmorra.painel.cd_teste": {
    "en": "Test DC",
    "pt": "CD do teste"
  },
  "ui.editor.masmorra.painel.dano_principal": {
    "en": "primary damage",
    "pt": "dano principal"
  },
  "ui.editor.masmorra.painel.formato_dano": {
    "en": "Format: 1d6, 2d8+2, or 3.",
    "pt": "Formato: 1d6, 2d8+2 ou 3."
  },
  "ui.editor.masmorra.painel.sem_dano_configuravel": {
    "en": "This trap doesn't have configurable direct damage.",
    "pt": "Esta armadilha não possui dano direto configurável."
  },
  "ui.editor.masmorra.painel.apague_valor_padrao": {
    "en": "Clear the value to go back to the catalog default.",
    "pt": "Apague o valor para voltar ao padrão do catálogo."
  },
  "ui.editor.masmorra.painel.veneno": {
    "en": "poison",
    "pt": "veneno"
  },
  "ui.editor.masmorra.painel.opcional": {
    "en": "(optional)",
    "pt": "(opcional)"
  },
  "ui.editor.masmorra.painel.ponto_saida_xy": {
    "en": "exit point (x, y)",
    "pt": "ponto de saída (x, y)"
  },
  "ui.editor.masmorra.painel.selecionar_saida_mapa": {
    "en": "Select exit on the map",
    "pt": "Selecionar saída no mapa"
  },
  "ui.editor.masmorra.painel.casa_chao_hint": {
    "en": "Floor square; if occupied in-game, uses the nearest free adjacent one.",
    "pt": "Casa de chão; se ocupada no jogo, usa a adjacente livre mais próxima."
  },
  "ui.editor.masmorra.painel.imagem": {
    "en": "Image",
    "pt": "Imagem"
  },
  "ui.editor.masmorra.painel.imagem_hint_armadilha": {
    "en": "PNG from assets/objetos — only visible in-game once the trap is revealed.",
    "pt": "PNG de assets/objetos — visível no jogo só quando a armadilha for revelada."
  },
  "ui.editor.masmorra.painel.recarregar_lista": {
    "en": "reload list",
    "pt": "recarregar lista"
  },
  "ui.editor.masmorra.painel.clique_casa_chao": {
    "en": "Click a floor square on the map now to set the exit.",
    "pt": "Clique agora em uma casa de chão no mapa para definir a saída."
  },
  "ui.editor.masmorra.painel.nenhuma_icone_padrao": {
    "en": "(none — default icon)",
    "pt": "(nenhuma — ícone padrão)"
  },
  "ui.editor.masmorra.painel.atual_sufixo": {
    "en": "(current)",
    "pt": "(atual)"
  },
  "ui.editor.masmorra.painel.offline_lista_upload": {
    "en": "(offline: list/upload unavailable)",
    "pt": "(offline: lista/upload indisponível)"
  },
  "ui.editor.masmorra.painel.servidor_offline": {
    "en": "server offline",
    "pt": "servidor offline"
  },
  "ui.editor.masmorra.painel.enviando": {
    "en": "uploading…",
    "pt": "enviando…"
  },
  "ui.editor.masmorra.painel.enviada_ok": {
    "en": "uploaded ✓",
    "pt": "enviada ✓"
  },
  "ui.editor.masmorra.painel.falha_dois_pontos": {
    "en": "failed: ",
    "pt": "falha: "
  },
  "ui.editor.masmorra.painel.valor_invalido_dano": {
    "en": "Invalid value. Use 1d6, 2d8+2, or 3.",
    "pt": "Valor inválido. Use 1d6, 2d8+2 ou 3."
  },
  "ui.editor.masmorra.painel.fala_licao_titulo": {
    "en": "Line / lesson",
    "pt": "Fala / lição"
  },
  "ui.editor.masmorra.painel.emoji_falante": {
    "en": "speaker emoji",
    "pt": "emoji do falante"
  },
  "ui.editor.masmorra.painel.nome_falante": {
    "en": "speaker name",
    "pt": "nome do falante"
  },
  "ui.editor.masmorra.painel.texto": {
    "en": "text",
    "pt": "texto"
  },
  "ui.editor.masmorra.painel.gatilho": {
    "en": "trigger",
    "pt": "gatilho"
  },
  "ui.editor.masmorra.painel.gatilho_proximidade": {
    "en": "proximity (radius)",
    "pt": "proximidade (raio)"
  },
  "ui.editor.masmorra.painel.gatilho_sala": {
    "en": "enter the room",
    "pt": "entrar na sala"
  },
  "ui.editor.masmorra.painel.gatilho_manual": {
    "en": "manual (game master)",
    "pt": "manual (mestre)"
  },
  "ui.editor.masmorra.painel.raio_casas": {
    "en": "radius (squares)",
    "pt": "raio (casas)"
  },
  "ui.editor.masmorra.painel.licao_tutorial": {
    "en": "Tutorial lesson",
    "pt": "Lição de tutorial"
  },
  "ui.editor.masmorra.painel.para_a_classe": {
    "en": "for the class",
    "pt": "para a classe"
  },
  "ui.editor.masmorra.painel.todas_classes": {
    "en": "all classes",
    "pt": "todas as classes"
  },
  "ui.editor.masmorra.painel.ordem_na_trilha": {
    "en": "order in the track (empty = no order)",
    "pt": "ordem na trilha (vazio = sem ordem)"
  },
  "ui.editor.masmorra.painel.cobra_tarefa": {
    "en": "requires a task",
    "pt": "cobra uma tarefa"
  },
  "ui.editor.masmorra.painel.tarefa": {
    "en": "task",
    "pt": "tarefa"
  },
  "ui.editor.masmorra.painel.alvo": {
    "en": "target",
    "pt": "alvo"
  },
  "ui.editor.masmorra.painel.alvo_hint_casa": {
    "en": "(square x,y — empty = any)",
    "pt": "(casa x,y — vazio = qualquer)"
  },
  "ui.editor.masmorra.painel.alvo_hint_tipo": {
    "en": "(monster type or item id — empty = any)",
    "pt": "(tipo do monstro ou id do item — vazio = qualquer)"
  },
  "ui.editor.masmorra.painel.vezes": {
    "en": "times",
    "pt": "vezes"
  },
  "ui.editor.masmorra.painel.texto_curto_hud": {
    "en": "short text (shown in the HUD)",
    "pt": "texto curto (aparece no HUD)"
  },
  "ui.editor.masmorra.painel.exemplo_ataque_boneco": {
    "en": "Attack the training dummy",
    "pt": "Ataque o boneco de treino"
  },
  "ui.editor.masmorra.painel.licao_altera_fome_sede": {
    "en": "the lesson changes hunger/thirst when triggered",
    "pt": "a lição altera fome/sede ao disparar"
  },
  "ui.editor.masmorra.painel.sentir_regra_hint": {
    "en": "For the player to FEEL the rule: arrive starving at the provisions room.",
    "pt": "Para o jogador SENTIR a regra: chegar esfomeado à sala de provisões."
  },
  "ui.editor.masmorra.painel.fome_0_100": {
    "en": "hunger (0–100, empty = don't change)",
    "pt": "fome (0–100, vazio = não mexer)"
  },
  "ui.editor.masmorra.painel.sede_0_100": {
    "en": "thirst (0–100, empty = don't change)",
    "pt": "sede (0–100, vazio = não mexer)"
  },
  "ui.editor.masmorra.painel.dispara_uma_vez_hint": {
    "en": "Triggers once per hero. Lessons don't accept a manual trigger.",
    "pt": "Dispara uma vez por herói. Lição não aceita gatilho manual."
  },
  "ui.editor.masmorra.painel.sala_n": {
    "en": "Room #{n}",
    "pt": "Sala #{n}"
  },
  "ui.editor.masmorra.painel.role": {
    "en": "role",
    "pt": "role"
  },
  "ui.editor.masmorra.painel.trancada": {
    "en": "locked",
    "pt": "trancada"
  },
  "ui.editor.masmorra.painel.sala_obrigatoria": {
    "en": "required room",
    "pt": "sala obrigatória"
  },
  "ui.editor.masmorra.painel.modo": {
    "en": "mode",
    "pt": "modo"
  },
  "ui.editor.masmorra.painel.limpar_matar_monstros": {
    "en": "clear (kill monsters)",
    "pt": "limpar (matar monstros)"
  },
  "ui.editor.masmorra.painel.visitar_entrar": {
    "en": "visit (enter)",
    "pt": "visitar (entrar)"
  },
  "ui.editor.masmorra.painel.portas_n": {
    "en": "doors: {n}",
    "pt": "portas: {n}"
  },
  "ui.editor.masmorra.painel.deletar_sala": {
    "en": "Delete room",
    "pt": "Deletar sala"
  },
  "ui.editor.masmorra.painel.deletar_sala_confirmacao": {
    "en": "Delete room #{n}?",
    "pt": "Deletar a sala #{n}?"
  },
  "ui.editor.masmorra.painel.deletar_manter_chao": {
    "en": "Delete (keep floor)",
    "pt": "Deletar (manter chão)"
  },
  "ui.editor.masmorra.painel.deletar_limpar_chao": {
    "en": "Delete (clear floor)",
    "pt": "Deletar (limpar chão)"
  },
  "ui.editor.masmorra.painel.sem_imagem_2d_prisioneiro": {
    "en": "no 2D image — will use the default emoji in this view",
    "pt": "sem imagem 2D — usará o emoji padrão nessa visão"
  },
  "ui.editor.masmorra.painel.modelo_3d": {
    "en": "3D model: {nome}",
    "pt": "modelo 3D: {nome}"
  },
  "ui.editor.masmorra.painel.sem_modelo_3d_prisioneiro": {
    "en": "no 3D model — will use the 2D image on the 3D board",
    "pt": "sem modelo 3D — usará a imagem 2D no tabuleiro 3D"
  },
  "ui.editor.masmorra.painel.prisioneiro_titulo": {
    "en": "Prisoner",
    "pt": "Prisioneiro"
  },
  "ui.editor.masmorra.painel.imagem_2d_formatos": {
    "en": "2D image (PNG/JPG/WebP/GIF)",
    "pt": "imagem 2D (PNG/JPG/WebP/GIF)"
  },
  "ui.editor.masmorra.painel.miniatura_3d_glb": {
    "en": "3D miniature (GLB)",
    "pt": "miniatura 3D (GLB)"
  },
  "ui.editor.masmorra.painel.parede_ilusoria": {
    "en": "Illusory wall",
    "pt": "Parede ilusória"
  },
  "ui.editor.masmorra.painel.passagem_secreta": {
    "en": "Secret passage",
    "pt": "Passagem secreta"
  },
  "ui.editor.masmorra.painel.parede_ilusoria_hint": {
    "en": "Passable from the start; only the rogue can spot it while Finding Traps.",
    "pt": "Atravessável desde o início; somente o ladino a identifica durante Encontrar Armadilhas."
  },
  "ui.editor.masmorra.painel.passagem_secreta_hint": {
    "en": "Opens permanently when its key decorations are activated.",
    "pt": "Abre permanentemente quando suas decorações-chave forem ativadas."
  },
  "ui.editor.masmorra.painel.textura_parede": {
    "en": "wall texture",
    "pt": "textura da parede"
  },
  "ui.editor.masmorra.painel.ativacao": {
    "en": "activation",
    "pt": "ativação"
  },
  "ui.editor.masmorra.painel.qualquer_chave": {
    "en": "any key",
    "pt": "qualquer chave"
  },
  "ui.editor.masmorra.painel.todas_chaves": {
    "en": "all keys",
    "pt": "todas as chaves"
  },
  "ui.editor.masmorra.painel.decoracoes_chave": {
    "en": "key decorations",
    "pt": "decorações-chave"
  },
  "ui.editor.masmorra.painel.marque_decor_chave_primeiro": {
    "en": "Mark a decoration as a key object first.",
    "pt": "Marque uma decoração como objeto-chave primeiro."
  },
  "ui.editor.masmorra.painel.alto_oclui_visao": {
    "en": "tall (blocks sight)",
    "pt": "alto (oclui visão)"
  },
  "ui.editor.masmorra.painel.pisavel": {
    "en": "walkable",
    "pt": "pisável"
  },
  "ui.editor.masmorra.painel.decor_parede_hint": {
    "en": "Mounted on the wall. Rotating switches to a free face; at corners, it can switch to the neighboring wall. With only one available face, orientation is automatic.",
    "pt": "Presa à parede. Girar troca para uma face livre; em cantos, pode trocar para a parede vizinha. Com apenas uma face disponível, a orientação é automática."
  },
  "ui.editor.masmorra.painel.visao_label": {
    "en": "vision",
    "pt": "visão"
  },
  "ui.editor.masmorra.painel.padrao_do_tipo": {
    "en": "type default ({v})",
    "pt": "padrão do tipo ({v})"
  },
  "ui.editor.masmorra.painel.so_muda_visao": {
    "en": "Only changes vision:",
    "pt": "Só muda a visão:"
  },
  "ui.editor.masmorra.painel.objeto_continua_pisavel": {
    "en": "the object is still walkable.",
    "pt": "o objeto continua pisável."
  },
  "ui.editor.masmorra.painel.objeto_continua_barrando": {
    "en": "the object still blocks movement.",
    "pt": "o objeto continua barrando o passo."
  },
  "ui.editor.masmorra.painel.trocar_face": {
    "en": "swap face",
    "pt": "trocar face"
  },
  "ui.editor.masmorra.painel.girar_90": {
    "en": "rotate 90°",
    "pt": "girar 90°"
  },
  "ui.editor.masmorra.painel.duplicar_casa_adjacente": {
    "en": "Duplicate to adjacent square",
    "pt": "Duplicar em casa adjacente"
  },
  "ui.editor.masmorra.painel.copiar_preencher_area": {
    "en": "Copy and fill area",
    "pt": "Copiar e preencher área"
  },
  "ui.editor.masmorra.painel.depois_arraste_hint": {
    "en": "Then drag on the map. Esc disables the brush.",
    "pt": "Depois, arraste no mapa. Esc desativa o pincel."
  },
  "ui.editor.masmorra.painel.cargas": {
    "en": "charges",
    "pt": "cargas"
  },
  "ui.editor.masmorra.painel.mensagem_placa": {
    "en": "plaque message",
    "pt": "mensagem da placa"
  },
  "ui.editor.masmorra.painel.placa_placeholder": {
    "en": "Write the message the heroes will find...",
    "pt": "Escreva a mensagem que os heróis encontrarão..."
  },
  "ui.editor.masmorra.painel.placa_hint": {
    "en": "Up to 600 characters. The message appears when a hero interacts with the plaque.",
    "pt": "Até 600 caracteres. A mensagem aparece quando um herói interagir com a placa."
  },
  "ui.editor.masmorra.painel.contem_loot": {
    "en": "contains loot",
    "pt": "contém loot"
  },
  "ui.editor.masmorra.painel.bau_armadilha": {
    "en": "trap chest",
    "pt": "baú-armadilha"
  },
  "ui.editor.masmorra.painel.monstro_que_surge": {
    "en": "monster that appears",
    "pt": "monstro que surge"
  },
  "ui.editor.masmorra.painel.bau_armadilha_hint": {
    "en": "On the first click, Reflex DC 12; the loot only opens on the next click.",
    "pt": "No primeiro clique, Reflexos CD 12; o loot só abre no próximo clique."
  },
  "ui.editor.masmorra.painel.contem_armadilha": {
    "en": "contains a trap",
    "pt": "contém armadilha"
  },
  "ui.editor.masmorra.painel.armadilha": {
    "en": "trap",
    "pt": "armadilha"
  },
  "ui.editor.masmorra.painel.local_saida": {
    "en": "exit location",
    "pt": "local de saída"
  },
  "ui.editor.masmorra.painel.dispara_investigar_hint": {
    "en": "Triggers when investigated. Finding Traps reveals the object and allows disarming it.",
    "pt": "Dispara ao investigar. Encontrar Armadilhas revela o objeto e permite desarmá-lo."
  },
  "ui.editor.masmorra.painel.mecanismo_desativa_armadilhas": {
    "en": "mechanism disables traps on the map",
    "pt": "mecanismo desativa armadilhas do mapa"
  },
  "ui.editor.masmorra.painel.armadilhas_desligadas_objeto": {
    "en": "Traps disabled by this object",
    "pt": "Armadilhas desligadas por este objeto"
  },
  "ui.editor.masmorra.painel.crie_armadilha_mapa": {
    "en": "Create a trap on the map first.",
    "pt": "Crie primeiro uma armadilha no mapa."
  },
  "ui.editor.masmorra.painel.ativar_objeto_desativa_hint": {
    "en": "Activating this object in-game permanently disables the selected traps.",
    "pt": "Ao ativar este objeto no jogo, as armadilhas selecionadas são desativadas permanentemente."
  },
  "ui.editor.masmorra.painel.objeto_chave": {
    "en": "key object",
    "pt": "objeto-chave"
  },
  "ui.editor.masmorra.painel.objeto_chave_hint": {
    "en": "completes “Open the key chest” on interaction",
    "pt": "conclui “Abrir o baú-chave” ao interagir"
  },
  "ui.editor.masmorra.painel.tamanho": {
    "en": "Size",
    "pt": "Tamanho"
  },
  "ui.editor.masmorra.painel.footprint_hint": {
    "en": "footprint in squares (occupied tiles)",
    "pt": "footprint em casas (quadrados ocupados)"
  },
  "ui.editor.masmorra.painel.largura": {
    "en": "width",
    "pt": "largura"
  },
  "ui.editor.masmorra.painel.altura": {
    "en": "height",
    "pt": "altura"
  },
  "ui.editor.masmorra.painel.tamanho_visual": {
    "en": "Visual size",
    "pt": "Tamanho visual"
  },
  "ui.editor.masmorra.painel.presa_face_parede_hint": {
    "en": "stays attached to a single wall face.",
    "pt": "fica presa a uma única face da parede."
  },
  "ui.editor.masmorra.painel.tamanho_visual_altura_hint": {
    "en": "visual size (doesn't change squares; height grows upward)",
    "pt": "tamanho visual (não muda casas; altura cresce p/ cima)"
  },
  "ui.editor.masmorra.painel.posicao_visual_hint": {
    "en": "visual position (doesn't change squares; use ±0.45 to touch the wall)",
    "pt": "posição visual (não muda casas; use ±0,45 para encostar na parede)"
  },
  "ui.editor.masmorra.painel.deslocamento_x": {
    "en": "X offset",
    "pt": "deslocamento X"
  },
  "ui.editor.masmorra.painel.deslocamento_y": {
    "en": "Y offset",
    "pt": "deslocamento Y"
  },
  "ui.editor.masmorra.painel.centralizar_objeto": {
    "en": "Center object",
    "pt": "Centralizar objeto"
  },
  "ui.editor.masmorra.painel.imagem_miniatura_3d": {
    "en": "Image (3D miniature)",
    "pt": "Imagem (miniatura 3D)"
  },
  "ui.editor.masmorra.painel.imagem_hint_decor": {
    "en": "PNG from assets/objetos — extruded silhouette in-game.",
    "pt": "PNG de assets/objetos — silhueta extrudada no jogo."
  },
  "ui.editor.masmorra.painel.offline_digite_upload": {
    "en": "(offline: type/upload unavailable)",
    "pt": "(offline: digite/upload indisponível)"
  },
  "ui.editor.masmorra.painel.sem_casa_adjacente_livre": {
    "en": "There's no free adjacent square for this copy.",
    "pt": "Não há uma casa adjacente livre para esta cópia."
  },
  "ui.editor.masmorra.painel.nao_cabe_revertido": {
    "en": "doesn't fit (wall/out of bounds/overlap) — reverted",
    "pt": "não cabe (parede/fora/sobreposição) — revertido"
  },
  "ui.editor.masmorra.painel.nenhuma_procedural": {
    "en": "(none — procedural)",
    "pt": "(nenhuma — procedural)"
  },
  "ui.editor.masmorra.painel.entrada": {
    "en": "Entrance",
    "pt": "Entrada"
  },
  "ui.editor.masmorra.painel.saida": {
    "en": "Exit",
    "pt": "Saída"
  },
  "ui.editor.masmorra.painel.saida_precisa_ser_chao": {
    "en": "The exit must be chosen on a floor square.",
    "pt": "A saída precisa ser escolhida em uma casa de chão."
  },
  "ui.editor.masmorra.painel.escolha_casa_chao": {
    "en": "Choose a floor square on the map.",
    "pt": "Escolha uma casa de chão no mapa."
  },
  "ui.editor.material.pedra_cinza": {
    "en": "Gray stone",
    "pt": "Pedra cinza"
  },
  "ui.editor.material.terra": {
    "en": "Dirt",
    "pt": "Terra"
  },
  "ui.editor.material.grama": {
    "en": "Grass",
    "pt": "Grama"
  },
  "ui.editor.material.agua": {
    "en": "Water",
    "pt": "Água"
  },
  "ui.editor.material.agua_profunda": {
    "en": "Deep water",
    "pt": "Água profunda"
  },
  "ui.editor.material.rodamoinho": {
    "en": "Whirlpool",
    "pt": "Rodamoinho"
  },
  "ui.editor.material.rodamoinho_profundo": {
    "en": "Deep whirlpool",
    "pt": "Rodamoinho profundo"
  },
  "ui.editor.material.piso_congelado": {
    "en": "Frozen floor",
    "pt": "Piso congelado"
  },
  "ui.editor.material.planicie_nevada": {
    "en": "Snowy plain",
    "pt": "Planície nevada"
  },
  "ui.editor.material.lava": {
    "en": "Lava",
    "pt": "Lava"
  },
  "ui.editor.material.pantano": {
    "en": "Swamp",
    "pt": "Pântano"
  },
  "ui.editor.material.areia_deserto": {
    "en": "Desert sand",
    "pt": "Areia do deserto"
  },
  "ui.editor.material.duna_deserto": {
    "en": "Desert dune",
    "pt": "Duna do deserto"
  },
  "ui.editor.material.caverna_congelada": {
    "en": "Frozen cave wall",
    "pt": "Parede de caverna congelada"
  },
  "ui.editor.material.duna_neve": {
    "en": "Snow dune",
    "pt": "Duna de neve"
  },
  "ui.editor.material.rocha": {
    "en": "Rock",
    "pt": "Rocha"
  },
  "ui.editor.material.rocha_marrom": {
    "en": "Brown rock",
    "pt": "Rocha marrom"
  },
  "ui.editor.material.pedra_negra": {
    "en": "Black stone",
    "pt": "Pedra negra"
  },
  "ui.editor.material.madeira_escura": {
    "en": "Dark plank floor",
    "pt": "Piso de tábuas escuras"
  },
  "ui.editor.material.entulho": {
    "en": "Rubble",
    "pt": "Entulho"
  },
  "ui.editor.material.pedra_normal": {
    "en": "Regular stone",
    "pt": "Pedra normal"
  },
  "ui.editor.material.enegrecida": {
    "en": "Blackened stone",
    "pt": "Pedra enegrecida"
  },
  "ui.editor.material.pedra_caverna": {
    "en": "Cave stone",
    "pt": "Pedra de caverna"
  },
  "ui.editor.material.desmoronada": {
    "en": "Crumbled wall",
    "pt": "Parede desmoronada"
  },
  "ui.editor.material.madeira": {
    "en": "Varnished wood wall",
    "pt": "Parede de madeira envernizada"
  },
  "ui.editor.masmorra.menu_copia.copiar": {
    "en": "Copy object",
    "pt": "Copiar objeto"
  },
  "ui.editor.masmorra.menu_copia.pincel": {
    "en": "Use as area brush",
    "pt": "Usar como pincel de área"
  },
  "ui.editor.masmorra.menu_copia.colar": {
    "en": "Paste object here",
    "pt": "Colar objeto aqui"
  },
  "ui.editor.masmorra.menu_copia.regiao_copiar": {
    "en": "Copy selected area",
    "pt": "Copiar área selecionada"
  },
  "ui.editor.masmorra.menu_copia.regiao_recortar": {
    "en": "Cut selected area",
    "pt": "Recortar área selecionada"
  },
  "ui.editor.masmorra.menu_copia.regiao_apagar": {
    "en": "Delete selected area",
    "pt": "Apagar área selecionada"
  },
  "ui.editor.masmorra.menu_copia.regiao_colar": {
    "en": "Paste area here",
    "pt": "Colar área aqui"
  },
  "ui.editor.masmorra.menu_copia.regiao_sala_parcial": {
    "en": "Select the whole room to copy or cut it.",
    "pt": "Selecione a sala inteira para copiá-la ou recortá-la."
  },
  "ui.editor.masmorra.menu_copia.regiao_objeto_parcial": {
    "en": "The selection cuts through an object. Expand it to include the whole object.",
    "pt": "A seleção atravessa um objeto. Amplie a área para incluí-lo por inteiro."
  },
  "ui.editor.masmorra.menu_copia.regiao_destino_invalido": {
    "en": "That destination overlaps existing objects or is outside the map.",
    "pt": "Esse destino sobrepõe objetos existentes ou fica fora do mapa."
  },
  "ui.editor.masmorra.ferramenta.select_hint": {
    "en": "Drag on an empty tile to select an area. Hold Shift to start over an object. Drag the selected area to move it; right-click for copy/cut/paste.",
    "pt": "Arraste sobre uma casa vazia para selecionar uma área. Segure Shift para começar sobre um objeto. Arraste a área selecionada para movê-la; clique com o botão direito para copiar, recortar ou colar."
  },
  "ui.editor.masmorra.canvas.frente": {
    "en": "FRONT",
    "pt": "FRENTE"
  },
  "ui.editor.masmorra.armadilha.efeito_rodada": {
    "en": " — round {n}",
    "pt": " — rodada {n}"
  },
  "ui.editor.masmorra.armadilha.efeito_dano": {
    "en": "{valor} damage{elemento}{rodada}{area}",
    "pt": "{valor} de dano{elemento}{rodada}{area}"
  },
  "ui.editor.masmorra.armadilha.em_area": {
    "en": " in an area",
    "pt": " em área"
  },
  "ui.editor.masmorra.armadilha.perde_movimento": {
    "en": "Loses movement",
    "pt": "Perde o movimento"
  },
  "ui.editor.masmorra.armadilha.perde_rodada": {
    "en": "Loses the turn",
    "pt": "Perde a rodada"
  },
  "ui.editor.masmorra.armadilha.aplica_veneno": {
    "en": "Applies the chosen poison",
    "pt": "Aplica o veneno escolhido"
  },
  "ui.editor.masmorra.armadilha.efeito_reduzir_con": {
    "en": "{valor} CON for {duracao} rounds{area}",
    "pt": "{valor} CON por {duracao} rodadas{area}"
  },
  "ui.editor.masmorra.armadilha.reducao": {
    "en": "reduction",
    "pt": "redução"
  },
  "ui.editor.masmorra.armadilha.algumas": {
    "en": "a few",
    "pt": "algumas"
  },
  "ui.editor.masmorra.armadilha.efeito_especial": {
    "en": "special effect",
    "pt": "efeito especial"
  },
  "ui.editor.masmorra.armadilha.sem_teste": {
    "en": "No standard save",
    "pt": "Sem teste padrão"
  },
  "ui.editor.masmorra.armadilha.sala_inteira": {
    "en": "Whole room",
    "pt": "Sala inteira"
  },
  "ui.editor.masmorra.armadilha.area_casa": {
    "en": "Area: {n} tile",
    "pt": "Área: {n} casa"
  },
  "ui.editor.masmorra.armadilha.area_casas": {
    "en": "Area: {n} tiles",
    "pt": "Área: {n} casas"
  },
  "ui.editor.masmorra.armadilha.alvo_casa": {
    "en": "Target on the tile",
    "pt": "Alvo na casa"
  },
  "ui.editor.masmorra.armadilha.duracao_rodadas": {
    "en": "{n} rounds",
    "pt": "{n} rodadas"
  },
  "ui.editor.masmorra.armadilha.permanece": {
    "en": "Stays active",
    "pt": "Permanece ativa"
  },
  "ui.editor.masmorra.armadilha.uso_unico": {
    "en": "Single use",
    "pt": "Uso único"
  },
  "ui.editor.masmorra.armadilha.dano": {
    "en": "💥 Damage: {v}",
    "pt": "💥 Dano: {v}"
  },
  "ui.editor.masmorra.armadilha.custo": {
    "en": "🪙 Cost: {n} gold",
    "pt": "🪙 Custo: {n} ouro"
  },
  "ui.editor.masmorra.armadilha.sucesso_reduz": {
    "en": "🛡️ Success reduces the damage",
    "pt": "🛡️ Sucesso reduz o dano"
  },
  "ui.editor.masmorra.armadilha.exige_veneno": {
    "en": "☠️ Requires poison",
    "pt": "☠️ Exige veneno"
  },
  "ui.editor.masmorra.armadilha.veneno_opcional": {
    "en": "☠️ Optional poison",
    "pt": "☠️ Veneno opcional"
  },
  "ui.editor.masmorra.armadilha.revela": {
    "en": "👁️ Revealed after triggering",
    "pt": "👁️ Revela após ativar"
  },
  "ui.editor.masmorra.armadilha.escape": {
    "en": "↗️ Escape: {v}{cd}",
    "pt": "↗️ Escape: {v}{cd}"
  },
  "ui.editor.masmorra.armadilha.so_objeto": {
    "en": "📦 Only on an object/decoration",
    "pt": "📦 Só em objeto/decoração"
  },
  "ui.editor.masmorra.armadilha.efeitos": {
    "en": "Effects",
    "pt": "Efeitos"
  },
  "ui.editor.masmorra.maldicao.texto_carta": {
    "en": "Letter text...",
    "pt": "Texto da carta..."
  },
  "ui.editor.masmorra.maldicao.ao_ler": {
    "en": "curse when read",
    "pt": "maldição ao ler"
  },
  "ui.editor.masmorra.maldicao.sem": {
    "en": "No curse",
    "pt": "Sem maldição"
  },
  "ui.editor.masmorra.maldicao.escolhida": {
    "en": "Chosen curse",
    "pt": "Maldição escolhida"
  },
  "ui.editor.masmorra.maldicao.aleatoria_gravidade": {
    "en": "Random by severity",
    "pt": "Aleatória por gravidade"
  },
  "ui.editor.masmorra.maldicao.aplicada": {
    "en": "applied curse",
    "pt": "maldição aplicada"
  },
  "ui.editor.masmorra.maldicao.nao_progressiva": {
    "en": "Picks a non-progressive curse of this severity.",
    "pt": "Escolhe uma maldição não progressiva desta gravidade."
  },
  "ui.editor.masmorra.recompensa.xp": {
    "en": "XP (total, split among the living)",
    "pt": "XP (total, dividido entre os vivos)"
  },
  "ui.editor.masmorra.recompensa.ouro": {
    "en": "gold (total, split)",
    "pt": "ouro (total, dividido)"
  },
  "ui.editor.masmorra.recompensa.itens": {
    "en": "reward items",
    "pt": "itens de recompensa"
  },
  "ui.editor.masmorra.recompensa.add_item": {
    "en": "+ item",
    "pt": "+ item"
  },
  "ui.editor.masmorra.design.sem_avisos": {
    "en": "No design warnings.",
    "pt": "Sem avisos de design."
  },
  "ui.editor.masmorra.design.avisos": {
    "en": "Design warnings ({n})",
    "pt": "Avisos de design ({n})"
  },
  "ui.editor.masmorra.termometro.titulo": {
    "en": "thermometer (power {poder})",
    "pt": "termômetro (poder {poder})"
  },
  "ui.editor.masmorra.termometro.total": {
    "en": "Total",
    "pt": "Total"
  },
  "ui.editor.masmorra.termometro.pior_sala": {
    "en": "Worst room",
    "pt": "Pior sala"
  },
  "ui.editor.masmorra.termometro.preview": {
    "en": "preview players:",
    "pt": "preview jogadores:"
  },
  "ui.editor.masmorra.canvas.fora_de_sala": {
    "en": "outside any room",
    "pt": "fora de sala"
  },
  "ui.editor.masmorra.canvas.sala_n": {
    "en": "room #{n}",
    "pt": "sala #{n}"
  },
  "ui.editor.masmorra.ponte.invalida": {
    "en": "The bridge must be straight, fit on the map, not overlap another bridge and connect points of the same height.",
    "pt": "A ponte precisa ser reta, caber no mapa, não sobrepor outra ponte e ligar pontos da mesma altura."
  },
  "ui.editor.masmorra.valid.carta_bau": {
    "en": "Chest card at {pos}",
    "pt": "Carta do baú em {pos}"
  },
  "ui.editor.masmorra.valid.carta_decor": {
    "en": "Decoration card at {pos}",
    "pt": "Carta da decoração em {pos}"
  },
  "ui.editor.masmorra.valid.carta_modo": {
    "en": "{rotulo}: invalid curse mode",
    "pt": "{rotulo}: modo de maldição inválido"
  },
  "ui.editor.masmorra.valid.carta_maldicao": {
    "en": "{rotulo}: invalid specific curse",
    "pt": "{rotulo}: maldição específica inválida"
  },
  "ui.editor.masmorra.valid.carta_gravidade": {
    "en": "{rotulo}: invalid curse severity",
    "pt": "{rotulo}: gravidade da maldição inválida"
  },
  "ui.editor.masmorra.valid.falta_entrada": {
    "en": "the entrance is missing",
    "pt": "falta a entrada"
  },
  "ui.editor.masmorra.valid.entrada_em_chao": {
    "en": "the entrance must be on floor",
    "pt": "entrada precisa estar em chão"
  },
  "ui.editor.masmorra.valid.falta_spawn": {
    "en": "at least one hero starting position is missing",
    "pt": "falta ao menos uma posição inicial de herói"
  },
  "ui.editor.masmorra.valid.spawn_classe_invalida": {
    "en": "invalid starting class: {classe} at {pos}",
    "pt": "classe inicial inválida: {classe} em {pos}"
  },
  "ui.editor.masmorra.valid.spawn_classe_duplicada": {
    "en": "duplicate starting class: {classe}",
    "pt": "classe inicial duplicada: {classe}"
  },
  "ui.editor.masmorra.valid.spawn_em_parede": {
    "en": "starting position inside a wall: {pos}",
    "pt": "posição inicial em parede: {pos}"
  },
  "ui.editor.masmorra.valid.sem_sala": {
    "en": "needs at least one room",
    "pt": "precisa de ao menos uma sala"
  },
  "ui.editor.masmorra.valid.sem_sala_entrada": {
    "en": "no room with role 'entrance'",
    "pt": "nenhuma sala com role 'entrance'"
  },
  "ui.editor.masmorra.valid.monstro_tipo_invalido": {
    "en": "invalid monster type: {tipo} at {pos}",
    "pt": "monstro tipo inválido: {tipo} em {pos}"
  },
  "ui.editor.masmorra.valid.monstro_em_parede": {
    "en": "monster inside a wall: {pos}",
    "pt": "monstro em parede: {pos}"
  },
  "ui.editor.masmorra.valid.monstro_room_id": {
    "en": "monster at {pos} with nonexistent room_id: {room}",
    "pt": "monstro em {pos} com room_id inexistente: {room}"
  },
  "ui.editor.masmorra.valid.bau_em_parede": {
    "en": "chest inside a wall: {pos}",
    "pt": "baú em parede: {pos}"
  },
  "ui.editor.masmorra.valid.item_invalido_bau": {
    "en": "invalid item: {id} in the chest at {pos}",
    "pt": "item inválido: {id} no baú em {pos}"
  },
  "ui.editor.masmorra.valid.armadilha_tipo_invalido": {
    "en": "invalid trap type: {tipo} at {pos}",
    "pt": "armadilha tipo inválido: {tipo} em {pos}"
  },
  "ui.editor.masmorra.valid.armadilha_so_objeto": {
    "en": "{tipo} at {pos} can only be placed on a decoration/object",
    "pt": "{tipo} em {pos} só pode ser colocado em uma decoração/objeto"
  },
  "ui.editor.masmorra.valid.armadilha_em_parede": {
    "en": "trap inside a wall: {pos}",
    "pt": "armadilha em parede: {pos}"
  },
  "ui.editor.masmorra.valid.armadilha_cd": {
    "en": "{tipo} at {pos} with invalid DC: {cd}",
    "pt": "{tipo} em {pos} com CD inválida: {cd}"
  },
  "ui.editor.masmorra.valid.armadilha_dano": {
    "en": "{tipo} at {pos} with invalid damage: {dano}",
    "pt": "{tipo} em {pos} com dano inválido: {dano}"
  },
  "ui.editor.masmorra.valid.armadilha_veneno": {
    "en": "{tipo} at {pos} without a valid poison",
    "pt": "{tipo} em {pos} sem veneno válido"
  },
  "ui.editor.masmorra.valid.armadilha_tp_saida": {
    "en": "teleport trap at {pos} without an exit on floor",
    "pt": "armadilha de teletransporte em {pos} sem saída em chão"
  },
  "ui.editor.masmorra.valid.maldicao_modo": {
    "en": "armadilha_maldicao at {pos} with invalid mode",
    "pt": "armadilha_maldicao em {pos} com modo inválido"
  },
  "ui.editor.masmorra.valid.maldicao_sem": {
    "en": "armadilha_maldicao at {pos} without a valid curse",
    "pt": "armadilha_maldicao em {pos} sem maldição válida"
  },
  "ui.editor.masmorra.valid.maldicao_gravidade": {
    "en": "armadilha_maldicao at {pos} with invalid severity",
    "pt": "armadilha_maldicao em {pos} com gravidade inválida"
  },
  "ui.editor.masmorra.valid.prisioneiro_em_parede": {
    "en": "prisoner inside a wall: {pos}",
    "pt": "prisioneiro em parede: {pos}"
  },
  "ui.editor.masmorra.valid.porta_nao_door": {
    "en": "declared door is not a DOOR tile: {porta}",
    "pt": "porta declarada não é tile DOOR: {porta}"
  },
  "ui.editor.masmorra.valid.poucas_casas": {
    "en": "fewer than 6 floor tiles reachable from the entrance",
    "pt": "menos de 6 casas de chão alcançáveis da entrada"
  },
  "ui.editor.masmorra.valid.spawn_inacessivel": {
    "en": "unreachable starting position: {classe} at {pos}",
    "pt": "posição inicial inacessível: {classe} em {pos}"
  },
  "ui.editor.masmorra.valid.objetivo_saida": {
    "en": "the all_heroes_at_exit objective requires an exit",
    "pt": "o objetivo all_heroes_at_exit exige uma saída"
  },
  "ui.editor.masmorra.valid.decor_tipo_invalido": {
    "en": "invalid decoration type: {tipo} at {pos}",
    "pt": "decoração tipo inválido: {tipo} em {pos}"
  },
  "ui.editor.masmorra.valid.placa_sem_mensagem": {
    "en": "plaque {id} at {pos} needs a message",
    "pt": "placa {id} em {pos} precisa de uma mensagem"
  },
  "ui.editor.masmorra.valid.placa_longa": {
    "en": "plaque {id} at {pos} exceeds 600 characters",
    "pt": "placa {id} em {pos} excede 600 caracteres"
  },
  "ui.editor.masmorra.valid.decor_parede_fora": {
    "en": "wall decoration {tipo} must be on a wall at {x},{y}",
    "pt": "decoração de parede {tipo} precisa estar em uma parede em {x},{y}"
  },
  "ui.editor.masmorra.valid.decor_parede_face": {
    "en": "wall decoration {tipo} must face an adjacent floor tile at {x},{y}",
    "pt": "decoração de parede {tipo} precisa apontar para um chão adjacente em {x},{y}"
  },
  "ui.editor.masmorra.valid.decor_parede_sobrepostas": {
    "en": "overlapping decorations on the same wall face at {x},{y}",
    "pt": "decorações sobrepostas na mesma face de parede em {x},{y}"
  },
  "ui.editor.masmorra.valid.loot_item_invalido": {
    "en": "invalid loot item: {id} in the decoration at {pos}",
    "pt": "item de loot inválido: {id} na decoração em {pos}"
  },
  "ui.editor.masmorra.valid.decor_fora_chao": {
    "en": "decoration {tipo} off the floor at {x},{y}",
    "pt": "decoração {tipo} fora do chão em {x},{y}"
  },
  "ui.editor.masmorra.valid.decor_sobrepostas": {
    "en": "overlapping decorations at {x},{y}",
    "pt": "decorações sobrepostas em {x},{y}"
  },
  "ui.editor.masmorra.valid.bau_armadilha_monstro": {
    "en": "trapped chest at {pos} with an invalid monster",
    "pt": "baú-armadilha em {pos} com monstro inválido"
  },
  "ui.editor.masmorra.valid.decor_trap_invalida": {
    "en": "invalid decoration trap at {pos}",
    "pt": "armadilha de decoração inválida em {pos}"
  },
  "ui.editor.masmorra.valid.decor_trap_cd": {
    "en": "{tipo} on the decoration at {pos} with invalid DC",
    "pt": "{tipo} na decoração em {pos} com CD inválida"
  },
  "ui.editor.masmorra.valid.decor_trap_dano": {
    "en": "{tipo} on the decoration at {pos} with invalid damage",
    "pt": "{tipo} na decoração em {pos} com dano inválido"
  },
  "ui.editor.masmorra.valid.decor_trap_veneno": {
    "en": "{tipo} on the decoration at {pos} without a valid poison",
    "pt": "{tipo} na decoração em {pos} sem veneno válido"
  },
  "ui.editor.masmorra.valid.decor_trap_tp_saida": {
    "en": "teleport trap on the decoration at {pos} without an exit on floor",
    "pt": "armadilha de teletransporte na decoração em {pos} sem saída em chão"
  },
  "ui.editor.masmorra.valid.decor_maldicao_modo": {
    "en": "decoration trap at {pos} with invalid curse mode",
    "pt": "armadilha de decoração em {pos} com modo de maldição inválido"
  },
  "ui.editor.masmorra.valid.decor_maldicao_sem": {
    "en": "decoration trap at {pos} without a valid curse",
    "pt": "armadilha de decoração em {pos} sem maldição válida"
  },
  "ui.editor.masmorra.valid.decor_maldicao_gravidade": {
    "en": "decoration trap at {pos} with invalid severity",
    "pt": "armadilha de decoração em {pos} com gravidade inválida"
  },
  "ui.editor.masmorra.valid.porta_cond_invalida": {
    "en": "invalid door opening condition: {chave}",
    "pt": "condição de abertura em porta inválida: {chave}"
  },
  "ui.editor.masmorra.valid.porta_cond_tipo": {
    "en": "invalid door condition type at {chave}",
    "pt": "tipo de condição de porta inválido em {chave}"
  },
  "ui.editor.masmorra.valid.porta_item_chave": {
    "en": "invalid key item on door {chave}: {id}",
    "pt": "item-chave inválido na porta {chave}: {id}"
  },
  "ui.editor.masmorra.valid.porta_licao": {
    "en": "door {chave} points to a lesson that does not exist or has no task",
    "pt": "porta {chave} aponta para uma lição que não existe ou não tem tarefa"
  },
  "ui.editor.masmorra.valid.porta_sem_chaves": {
    "en": "door {chave} without valid key objects",
    "pt": "porta {chave} sem objetos-chave válidos"
  },
  "ui.editor.masmorra.valid.porta_chave_repetida": {
    "en": "door {chave} repeats a key object",
    "pt": "porta {chave} repete um objeto-chave"
  },
  "ui.editor.masmorra.valid.porta_modo_chaves": {
    "en": "invalid key-object mode on door {chave}",
    "pt": "modo de objetos-chave inválido na porta {chave}"
  },
  "ui.editor.masmorra.valid.porta_objeto_nao_chave": {
    "en": "object {id} at {pos} of door {chave} must be marked as a key object",
    "pt": "objeto {id} em {pos} da porta {chave} precisa estar marcado como objeto-chave"
  },
  "ui.editor.masmorra.valid.passagem_id": {
    "en": "duplicate or empty secret passage id",
    "pt": "id de passagem secreta duplicado ou vazio"
  },
  "ui.editor.masmorra.valid.passagem_parede": {
    "en": "secret passage {id} at {pos} must be on a wall",
    "pt": "passagem secreta {id} em {pos} deve ficar em uma parede"
  },
  "ui.editor.masmorra.valid.passagem_textura": {
    "en": "invalid secret passage texture at {pos}",
    "pt": "textura da passagem secreta em {pos} inválida"
  },
  "ui.editor.masmorra.valid.passagem_chave_invalida": {
    "en": "passage at {pos} with an invalid key decoration",
    "pt": "passagem em {pos} com decoração-chave inválida"
  },
  "ui.editor.masmorra.valid.passagem_sem_chave": {
    "en": "secret passage at {pos} without a key decoration",
    "pt": "passagem secreta em {pos} sem decoração-chave"
  },
  "ui.editor.masmorra.valid.fala_em_parede": {
    "en": "NPC line inside a wall: {pos}",
    "pt": "fala de NPC em parede: {pos}"
  },
  "ui.editor.masmorra.valid.fala_sem_texto": {
    "en": "NPC line at {pos} without text",
    "pt": "fala de NPC em {pos} sem texto"
  },
  "ui.editor.masmorra.valid.fala_gatilho": {
    "en": "NPC line at {pos} with invalid trigger: {tipo}",
    "pt": "fala de NPC em {pos} com gatilho inválido: {tipo}"
  },
  "ui.editor.masmorra.valid.licao_manual": {
    "en": "lesson {id} at {pos} cannot have a manual trigger",
    "pt": "lição {id} em {pos} não pode ter gatilho manual"
  },
  "ui.editor.masmorra.valid.licao_classe": {
    "en": "lesson {id} at {pos} with invalid class: {classe}",
    "pt": "lição {id} em {pos} com classe inválida: {classe}"
  },
  "ui.editor.masmorra.valid.todas_classes": {
    "en": "all classes",
    "pt": "todas as classes"
  },
  "ui.editor.masmorra.valid.licao_ordem_duplicada": {
    "en": "two lessons with the same order {ordem} for {classe}",
    "pt": "duas lições com a mesma ordem {ordem} para {classe}"
  },
  "ui.editor.masmorra.valid.licao_tarefa": {
    "en": "lesson {id} at {pos} with invalid task: {tipo}",
    "pt": "lição {id} em {pos} com tarefa inválida: {tipo}"
  },
  "ui.editor.masmorra.valid.licao_sem_texto_curto": {
    "en": "lesson {id} at {pos} without short text",
    "pt": "lição {id} em {pos} sem texto curto"
  },
  "ui.editor.masmorra.valid.licao_alvo": {
    "en": "lesson {id}: target should be an x,y tile",
    "pt": "lição {id}: alvo deveria ser uma casa x,y"
  },
  "ui.editor.masmorra.valid.material_invalido": {
    "en": "invalid material: {id}",
    "pt": "material inválido: {id}"
  },
  "ui.editor.masmorra.valid.material_parede_fora": {
    "en": "wall material {id} outside a wall at {chave}",
    "pt": "material de parede {id} fora de parede em {chave}"
  },
  "ui.editor.masmorra.valid.material_piso_fora": {
    "en": "floor material {id} outside floor at {chave}",
    "pt": "material de piso {id} fora de chão em {chave}"
  },
  "ui.editor.masmorra.valid.rodamoinho_2x2": {
    "en": "deep whirlpool must occupy at least one continuous 2x2 area",
    "pt": "rodamoinho profundo precisa ocupar no mínimo uma área contínua de 2x2 casas"
  },
  "ui.editor.masmorra.valid.ponte_id": {
    "en": "bridge with duplicate or empty id",
    "pt": "ponte com id duplicado ou vazio"
  },
  "ui.editor.masmorra.valid.ponte_reta": {
    "en": "bridge {id} must be straight and have distinct start/end",
    "pt": "ponte {id} precisa ser reta e ter início/fim distintos"
  },
  "ui.editor.masmorra.valid.ponte_fora": {
    "en": "bridge {id} ({inicio}→{fim}) outside the grid",
    "pt": "ponte {id} ({inicio}→{fim}) fora do grid"
  },
  "ui.editor.masmorra.valid.ponte_extremos": {
    "en": "bridge {id} ({inicio}→{fim}) must start and end on floor or a door",
    "pt": "ponte {id} ({inicio}→{fim}) precisa começar e terminar em chão ou porta"
  },
  "ui.editor.masmorra.valid.ponte_alturas": {
    "en": "bridge {id} ({inicio}→{fim}) connects different heights",
    "pt": "ponte {id} ({inicio}→{fim}) liga alturas diferentes"
  },
  "ui.editor.masmorra.valid.pontes_sobrepostas": {
    "en": "overlapping bridges at {chave}",
    "pt": "pontes sobrepostas em {chave}"
  },
  "ui.editor.masmorra.valid.elevacao_fora": {
    "en": "elevation outside the grid at {chave}",
    "pt": "elevação fora do grid em {chave}"
  },
  "ui.editor.masmorra.valid.elevacao_nao_chao": {
    "en": "elevation on a tile that is not floor: {chave}",
    "pt": "elevação em casa que não é chão: {chave}"
  },
  "ui.editor.masmorra.valid.elevacao_invalida": {
    "en": "invalid elevation at {chave}",
    "pt": "elevação inválida em {chave}"
  },
  "ui.editor.masmorra.valid.altura_parede_fora": {
    "en": "wall height outside the grid at {chave}",
    "pt": "altura de parede fora do grid em {chave}"
  },
  "ui.editor.masmorra.valid.altura_parede_nao_parede": {
    "en": "wall height on a tile that is not a wall: {chave}",
    "pt": "altura de parede em casa que não é parede: {chave}"
  },
  "ui.editor.masmorra.valid.altura_parede_invalida": {
    "en": "invalid wall height at {chave}",
    "pt": "altura de parede inválida em {chave}"
  },
  "ui.editor.masmorra.valid.transicao_invalida": {
    "en": "invalid height transition",
    "pt": "transição de altura inválida"
  },
  "ui.editor.masmorra.status.valida": {
    "en": "✓ valid — ready to save",
    "pt": "✓ válida — pronta para salvar"
  },
  "ui.editor.masmorra.status.problemas": {
    "en": "✗ {n} problem(s): {lista}{mais}",
    "pt": "✗ {n} problema(s): {lista}{mais}"
  },
  "ui.editor.masmorra.design.r4": {
    "en": "R4: room {sala} is cut off from the main map.",
    "pt": "R4: sala {sala} isolada do mapa principal."
  },
  "ui.editor.masmorra.design.r2r5_sem_boss": {
    "en": "R2/R5: no room with role 'boss' (rules skipped).",
    "pt": "R2/R5: sem sala com role 'boss' (regras puladas)."
  },
  "ui.editor.masmorra.design.r2": {
    "en": "R2: boss only {dist} room(s) from the spawn (min {min}).",
    "pt": "R2: boss a só {dist} sala(s) do spawn (mín {min})."
  },
  "ui.editor.masmorra.design.r5": {
    "en": "R5: no rest room (low CR) right before the boss.",
    "pt": "R5: sem sala de descanso (ND baixo) logo antes do boss."
  },
  "ui.editor.masmorra.design.r1": {
    "en": "R1: single route — no alternative path to the boss (bottleneck at {gargalos}).",
    "pt": "R1: rota única — sem caminho alternativo até o boss (gargalo em {gargalos})."
  },
  "ui.editor.masmorra.design.r3r6_sem_obrigatoria": {
    "en": "R3/R6: no room marked as required (critical route).",
    "pt": "R3/R6: nenhuma sala marcada como obrigatória (rota crítica)."
  },
  "ui.editor.masmorra.design.r6": {
    "en": "R6: heavy critical route (average CR {media} > cap {teto}).",
    "pt": "R6: rota crítica pesada (ND médio {media} > teto {teto})."
  },
  "ui.editor.masmorra.design.r3": {
    "en": "R3: CR spike between rooms {a} and {b} (Δ={delta}).",
    "pt": "R3: pico de ND entre salas {a} e {b} (Δ={delta})."
  },
  "ui.editor.masmorra.salvar.nome_padrao": {
    "en": "Dungeon",
    "pt": "Masmorra"
  },
  "ui.editor.masmorra.salvar.invalida": {
    "en": "Invalid dungeon:\n- {lista}",
    "pt": "Masmorra inválida:\n- {lista}"
  },
  "ui.editor.masmorra.salvar.salvando": {
    "en": "Saving to dungeons/…",
    "pt": "Salvando em dungeons/…"
  },
  "ui.editor.masmorra.salvar.salva": {
    "en": "✓ saved to dungeons/{arquivo} — available in the Campaign tab",
    "pt": "✓ salva em dungeons/{arquivo} — disponível na aba Campanha"
  },
  "ui.editor.masmorra.salvar.offline": {
    "en": "⚠ server offline ({erro}) — downloaded to Downloads",
    "pt": "⚠ servidor offline ({erro}) — baixada em Downloads"
  },
  "ui.editor.masmorra.salvar.teste_sem_servidor": {
    "en": "Start the server to test the dungeon.",
    "pt": "Inicie o servidor para testar a masmorra."
  },
  "ui.editor.masmorra.salvar.teste_invalida": {
    "en": "Fix the dungeon before testing:\n- {lista}",
    "pt": "Corrija a masmorra antes de testar:\n- {lista}"
  },
  "ui.editor.masmorra.salvar.teste_falhou": {
    "en": "Could not start the test: {erro}",
    "pt": "Não foi possível iniciar o teste: {erro}"
  },
  "ui.editor.masmorra.salvar.json_invalido": {
    "en": "Invalid JSON: {erro}",
    "pt": "JSON inválido: {erro}"
  },
  "ui.editor.masmorra.direcao.norte": {
    "en": "↑ north",
    "pt": "↑ norte"
  },
  "ui.editor.masmorra.direcao.leste": {
    "en": "→ east",
    "pt": "→ leste"
  },
  "ui.editor.masmorra.direcao.sul": {
    "en": "↓ south",
    "pt": "↓ sul"
  },
  "ui.editor.masmorra.direcao.oeste": {
    "en": "← west",
    "pt": "← oeste"
  },
  "ui.editor.masmorra.painel.tamanho_casas": {
    "en": "{w}×{h} squares",
    "pt": "{w}×{h} casas"
  },
  "ui.editor.masmorra.armadilha.so_ponte": {
    "en": "🌉 Bridge only, with a floor 1 level below",
    "pt": "🌉 Só em ponte com piso inferior 1 nível abaixo"
  },
  "ui.editor.masmorra.painel.armadilha_permanente": {
    "en": "permanent trap — can trigger again until disarmed",
    "pt": "armadilha permanente — pode disparar novamente até ser desarmada"
  },
  "ui.editor.masmorra.painel.armadilha_permanente_curta": {
    "en": "permanent trap — triggers again until disarmed",
    "pt": "armadilha permanente — dispara novamente até ser desarmada"
  },
  "ui.editor.masmorra.painel.permanente_xp": {
    "en": "Grants no XP when triggered; successfully disarming it grants double.",
    "pt": "Não concede XP ao disparar; desarmá-la com sucesso concede o dobro."
  },
  "ui.editor.masmorra.painel.bau_permanente_xp": {
    "en": "A permanent trap grants no XP when triggered; successfully disarming it grants double.",
    "pt": "Armadilha permanente não concede XP ao disparar; desarmá-la com sucesso concede o dobro."
  },
  "ui.editor.masmorra.valid.armadilha_permanente_invalido": {
    "en": "{tipo} at {pos} with invalid permanent flag",
    "pt": "{tipo} em {pos} com permanente inválido"
  },
  "ui.editor.masmorra.valid.chao_permanente": {
    "en": "chao_illusorio at {pos} cannot be permanent because the bridge collapses when triggered",
    "pt": "chao_illusorio em {pos} não pode ser permanente porque a ponte colapsa no disparo"
  },
  "ui.editor.masmorra.valid.chao_sem_ponte": {
    "en": "chao_illusorio at {pos} must be on a bridge",
    "pt": "chao_illusorio em {pos} precisa estar sobre uma ponte"
  },
  "ui.editor.masmorra.valid.chao_ponte_diferente": {
    "en": "chao_illusorio at {pos} is linked to a different bridge",
    "pt": "chao_illusorio em {pos} está vinculado a uma ponte diferente"
  },
  "ui.editor.masmorra.valid.chao_sem_piso": {
    "en": "chao_illusorio at {pos} needs FLOOR directly below",
    "pt": "chao_illusorio em {pos} precisa ter FLOOR diretamente abaixo"
  },
  "ui.editor.masmorra.valid.chao_sem_queda": {
    "en": "chao_illusorio at {pos} needs at least 1 level of drop",
    "pt": "chao_illusorio em {pos} precisa ter pelo menos 1 nível de queda"
  },
  "ui.editor.masmorra.valid.bau_permanente_invalido": {
    "en": "trapped chest at {pos} with invalid permanent flag",
    "pt": "baú-armadilha em {pos} com permanente inválido"
  },
  "ui.editor.masmorra.valid.bau_permanente_sem_monstro": {
    "en": "trapped chest at {pos} without a monster type",
    "pt": "baú-armadilha em {pos} sem tipo de monstro"
  },
  "ui.editor.masmorra.valid.decor_trap_permanente_invalido": {
    "en": "{tipo} in the decoration at {pos} with invalid permanent flag",
    "pt": "{tipo} na decoração em {pos} com permanente inválido"
  },
  "ui.editor.masmorra.valid.decor_chao_permanente": {
    "en": "chao_illusorio in the decoration at {pos} cannot be permanent",
    "pt": "chao_illusorio na decoração em {pos} não pode ser permanente"
  },
  "ui.editor.masmorra.hostilidade.titulo": {
    "en": "Hostility for this placement",
    "pt": "Hostilidade desta colocação"
  },
  "ui.editor.masmorra.hostilidade.so_este": {
    "en": "This choice applies only to this monster on the map.",
    "pt": "Esta escolha vale só para este monstro no mapa."
  },
  "ui.editor.masmorra.hostilidade.bestiario": {
    "en": "Use the Bestiary default",
    "pt": "Usar padrão do Bestiário"
  },
  "ui.editor.masmorra.hostilidade.nenhuma": {
    "en": "No hostility",
    "pt": "Sem hostilidade"
  },
  "ui.editor.masmorra.hostilidade.escolher": {
    "en": "Choose hostility for this monster",
    "pt": "Escolher hostilidade para este monstro"
  },
  "ui.editor.masmorra.hostilidade.todos": {
    "en": "Hostile to all monsters",
    "pt": "Hostil a todos os monstros"
  },
  "ui.editor.masmorra.hostilidade.subtipos": {
    "en": "Subtypes ({n})",
    "pt": "Subtipos ({n})"
  },
  "ui.editor.masmorra.hostilidade.criaturas": {
    "en": "Specific creatures ({n})",
    "pt": "Criaturas específicas ({n})"
  },
  "ui.editor.masmorra.hostilidade.ou": {
    "en": "Filters are combined with OR.",
    "pt": "Os filtros são combinados por OU."
  },
  "ui.editor.subtipo.animal": {
    "en": "Animal",
    "pt": "Animal"
  },
  "ui.editor.subtipo.abissal": {
    "en": "Abyssal",
    "pt": "Abissal"
  },
  "ui.editor.subtipo.aberracao": {
    "en": "Aberration",
    "pt": "Aberração"
  },
  "ui.editor.subtipo.besta_magica": {
    "en": "Magical Beast",
    "pt": "Besta Mágica"
  },
  "ui.editor.subtipo.construto": {
    "en": "Construct",
    "pt": "Construto"
  },
  "ui.editor.subtipo.morto_vivo": {
    "en": "Undead",
    "pt": "Morto-Vivo"
  },
  "ui.editor.subtipo.vegetal": {
    "en": "Plant",
    "pt": "Vegetal"
  },
  "ui.editor.subtipo.raca_padrao": {
    "en": "Standard Race",
    "pt": "Raça Padrão"
  },
  "ui.editor.masmorra.painel.intervalo_fumarola": {
    "en": "burst every N rounds",
    "pt": "rajada a cada N rodadas"
  }
};
Object.assign(window.LANG_STRINGS, window.LANG_EDITOR);
