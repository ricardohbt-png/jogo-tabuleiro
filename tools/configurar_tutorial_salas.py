"""Autoria das lições do Campo de Treinamento; preserva a geometria do mapa."""
import json
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'dungeons/campo_de_treinamento.json'
d = json.loads(path.read_text(encoding='utf-8'))
rooms = {'warrior': 40, 'mage': 41, 'rogue': 42, 'cleric': 35, 'bard': 43, 'paladin': 38}
for r in d['rooms']:
    for cls, ident in rooms.items():
        if r['id'] == ident:
            r['allowed_class'] = cls
d['tutorial_training'] = True
for m in d['monsters']:
    if m['type'] in ['boneco_mira', 'boneco_golpe', 'boneco_furia']:
        m['room_id'] = 40

# Preservar as falas comuns e o combate introdutório. Corrigir destinos que
# ficaram na posição do mapa antigo após a reorganização feita no editor.
d['falas'] = [f for f in d['falas'] if not f.get('classe') or f.get('ordem', 0) <= 2]

# A primeira lição apresenta os controles antes de pedir que o herói caminhe.
d['falas'] = [f for f in d['falas'] if f['id'] != 'fala_camera']
d['falas'].insert(0, {
    'id': 'fala_camera', 'pos': [3, 15],
    'falante': {'nome': 'Mestre de Armas', 'emoji': '🛡️'},
    'texto': 'Vamos ajustar a visão do tabuleiro antes de mover seu herói.',
    'trigger': {'tipo': 'proximidade', 'raio': 9}, 'ordem': 0,
    'tarefa': {'tipo': 'encerrar_turno', 'vezes': 1,
               'texto_curto': 'Pratique a câmera e encerre o turno'},
})

for f in d['falas']:
    if f['id'] == 'fala_0':
        f['texto'] = 'Bem-vindo. Vamos ajustar a visão e depois mover seu herói.'
        f['tarefa']['alvo'] = [5, 15]
        f['tarefa']['texto_curto'] = 'Ande até a casa 5,15'
    if f['id'] in ['fala_1', 'fala_2']:
        f['tarefa'].pop('alvo', None)
        f['tarefa']['texto_curto'] = 'Pegue uma arma do baú' if f['id'] == 'fala_1' else 'Equipe a arma que pegou'
        f['texto'] = ('O baú contém armas para praticar. Pegue uma arma compatível com seu herói; ela vai para a bolsa.'
                      if f['id'] == 'fala_1' else 'Abra a bolsa, selecione a arma que pegou e equipe-a. Equipar é uma ação livre.')
    if f['id'] == 'fala_4':
        f['tarefa']['alvo'] = [13, 15]
        f['tarefa']['texto_curto'] = 'Atravesse a porta para a sala de combate'
    if f['id'] in ['fala_6', 'fala_8', 'fala_10', 'fala_12', 'fala_14', 'fala_16']:
        f['texto'] = f['texto'].split('Quando ele cair')[0].split(' Depois procure a porta')[0] + ' Depois procure a porta da sala exclusiva do seu herói para praticar suas habilidades.'

# O baú do átrio oferece somente a arma de treino da classe de cada herói.
d['chests'][0]['items'] = [
    {'id': 'sword', 'tutorial_class': 'warrior'},
    {'id': 'dagger', 'tutorial_class': 'mage'},
    {'id': 'lanca_curta', 'tutorial_class': 'rogue'},
    {'id': 'bordao', 'tutorial_class': 'cleric'},
    {'id': 'lanca_curta', 'tutorial_class': 'bard'},
    {'id': 'sword', 'tutorial_class': 'paladin'},
]
# O depósito oferece duas refeições, uma ração e um cantil por herói. O estoque
# cobre seis heróis; a serialização e os handlers aplicam cotas pessoais.
next(c for c in d['chests'] if c['pos'] == [29, 14])['items'] = [
    {'id': iid, 'tutorial_provision': True}
    for _ in range(6)
    for iid in ('banquete_viagem', 'banquete_viagem', 'racao_viagem', 'cantil_agua')
]
d['prisoner'] = {'pos': [35, 25], 'room_id': 38,
                 'image': 'soldado.png', 'model3d': 'soldado.glb'}

for cls, pos in [('warrior',[24,3]), ('mage',[24,24]), ('mage',[24,26]), ('rogue',[11,7]),
                 ('rogue',[12,7]), ('bard',[12,24]), ('paladin',[36,25])]:
    if not any(m['pos'] == pos for m in d['monsters']):
        d['monsters'].append({'type':'boneco_treino', 'pos':pos, 'room_id':rooms[cls], 'boss':False, 'target':False})
if not any(t['pos'] == [10,8] for t in d['traps']):
    d['traps'].append({'id':'trap_treino_luccas', 'tipo':'buraco', 'pos':[10,8], 'dificuldade':5})

import sys as _sys; _sys.path.insert(0, str(Path(__file__).resolve().parent))
import aplicar_fatia9_tutorial as _F9   # lição de guiar o refém (constantes)
import aplicar_fatia16_tutorial as _F16   # Clérigo: lançar magias (sala sem custo de slots)
import aplicar_fatia15_tutorial as _F15   # textos do Mago: na sala dele as magias não gastam slots
points={'warrior':[20,4],'mage':[22,24],'rogue':[9,7],'cleric':[32,6],'bard':[10,23],'paladin':[33,25]}
def lesson(cls, ident, order, skill, text, short, *, verb='usar_habilidade', requirements=None, target_id=None, effective=False, count=1, scene=None):
    f={'id':ident, 'pos':points[cls], 'falante':{'nome':'Mestre de Armas','emoji':'🎓', 'retrato':'assets/portraits/mestre_de_armas.png'},
       'texto':text, 'trigger':{'tipo':'sala'}, 'classe':cls, 'ordem':order + 2, 'sala_exclusiva':True,   # ordens 1–2 são o combate comum; 3 é a porta; 4 abre o treino da classe
       'tarefa':{'tipo':verb, 'vezes':count, 'texto_curto':short}}
    if scene:f['falante']['cena']=scene
    if skill is not None:f['tarefa']['alvo']=skill
    if target_id:f['tarefa']['alvo_id']=target_id
    if effective:f['tarefa']['cura_efetiva']=True
    if requirements:f['requisitos']=requirements
    d['falas'].append(f)

lesson('warrior','treino_atalhos_warrior',2,'mira_certeira',
       'Abra H e vincule Mira Certeira ao espaço 1. Depois use 1 para ativá-la; Esc cancela uma mira pendente. Habilidades alternáveis podem ser desligadas com o mesmo atalho; efeitos com duração fixa acabam sozinhos.', 'Vincule Mira Certeira ao atalho 1',verb='configurar_atalho')
lesson('warrior','treino_mira',3,'mira_certeira',
       'Selecione Mira Certeira e ataque o alvo ⚔️. A habilidade prepara seu golpe e melhora o teste de acerto. Observe o bônus nos dados.', 'Ataque com Mira Certeira')
lesson('warrior','treino_golpe',4,'golpe_devastador',
       'Encerre o turno se já usou sua ação. Arme Golpe Devastador e ataque o alvo 💥. Observe como a habilidade modifica os dados de dano.', 'Ataque com Golpe Devastador')
lesson('warrior','treino_furia',5,'furia_berserker',
       'Arme Fúria Berserker e ataque o alvo 🔥. Não encerre o turno depois desse golpe: a Fúria permite um ataque adicional.', 'Faça o primeiro ataque com Fúria')
lesson('warrior','treino_furia_extra',6,'furia_berserker',
       'Use o ataque extra agora, antes de encerrar o turno. O boneco comum próximo também serve de alvo. Se você já passou a vez, arme Fúria novamente e faça os dois ataques.', 'Use o ataque extra da Fúria',verb='ataque_extra')
lesson('warrior','treino_guerreiro_fim',7,None,
       'Você praticou as três habilidades. Confira a comida e a água consumidas e encerre seu turno. Ao aprender especializações na Guilda, volte para novos exercícios.', 'Encerre o turno para concluir',verb='encerrar_turno')

lesson('mage','treino_atalhos_mage',2,'aprimorar_magia',
       'Abra H e vincule Aprimorar Magia ao espaço 1. Depois use 1 para ativá-la; Esc cancela uma mira pendente. Habilidades alternáveis podem ser desligadas com o mesmo atalho; efeitos com duração fixa acabam sozinhos.', 'Vincule Aprimorar Magia ao atalho 1',verb='configurar_atalho')
lesson('mage','treino_menu_magias_mage',3,None,
       'Abra o grimório com M, confira as magias conhecidas, feche com M ou Esc e encerre o turno.', 'Conheça o grimório',verb='encerrar_turno',requirements={'magia_tipo':'qualquer'})
lesson('mage','treino_magia',4,None,
       _F15.MAGIA, 'Lance uma magia conhecida',verb='usar_magia',requirements={'magia_tipo':'qualquer'})
lesson('mage','treino_slots',5,None,
       _F15.SLOTS, _F15.SLOTS_CURTO,verb='encerrar_turno')
for order, ident, label, kind, explanation in [
 (6,'aprimorar_magia','Aprimorar Magia','save','melhora a dificuldade do teste de resistência'),
 (7,'estender_magia','Estender Magia','duracao','acrescenta duração a um efeito que persiste'),
 (8,'fortalecer_magia','Fortalecer Magia','dano','aumenta o dano de uma magia')]:
    lesson('mage','treino_'+ident,order,ident,
           f'Arme {label} e lance uma magia compatível: esta metamagia {explanation}. O exercício só conta quando ela for aplicada ao lançamento. Confira os valores da sua ficha.',
           f'Lance uma magia com {label}',requirements={'magia_tipo':kind})
lesson('mage','treino_reviver',9,'animar_mortos',
       'O cadáver de treinamento está no chão. Aproxime-se, use Reviver os Mortos e selecione o cadáver. Se a tentativa falhar, tente novamente em outro turno.', 'Anime o cadáver de treinamento')
lesson('mage','treino_comando',10,None,
       'Encerre a vez de Pedro para abrir a fase dos servos. Use Comandar para que seu morto animado se mova e ataque um boneco.', 'Comande o servo de treinamento',verb='comandar_servo')

lesson('rogue','treino_atalhos_rogue',2,'detectar_armadilhas',
       'Abra H e vincule Detectar Armadilhas ao espaço 1. Use 1 para ativá-la; Esc cancela uma mira pendente. Habilidades alternáveis podem ser desligadas com o mesmo atalho; efeitos com duração fixa acabam sozinhos.', 'Vincule Detectar Armadilhas ao atalho 1',verb='configurar_atalho')
lesson('rogue','treino_detectar',3,'detectar_armadilhas',
       'Ative Detectar Armadilhas e aproxime-se da casa 10,8. A detecção revela os mecanismos próximos. Confira a manutenção de água.', 'Revele a armadilha de treinamento')
lesson('rogue','treino_desarmar',4,None,
       'Fique ao lado da armadilha revelada e use Desarmar Armadilha. Se o teste falhar, tente novamente. A sala pode restaurar o mecanismo para você continuar.', 'Desarme a armadilha',verb='desarmar_armadilha')
lesson('rogue','treino_esconder',5,'esconder_sombras',
       'Perto do boneco, use Esconder nas Sombras. Essa é uma ação bônus: você pode atacar na mesma rodada após conseguir se esconder.', 'Esconda-se nas sombras')
lesson('rogue','treino_furtivo',6,'ataque_furtivo',
       'Ataque um boneco enquanto estiver escondido. Ataque Furtivo é uma passiva: o dano extra aparece quando as condições são cumpridas. Se errar, esconda-se e tente de novo.', 'Acerte um Ataque Furtivo')
lesson('rogue','treino_veneno',7,'veneno_rapido',
       'Use Veneno Rápido e escolha o veneno de treinamento na bolsa para untar sua arma. Essa é uma ação livre. Confira as cargas preparadas.', 'Unte a arma com Veneno Rápido')
lesson('rogue','treino_veneno_golpe',8,None,
       'Ataque um boneco com a arma untada. Observe o consumo da carga e o teste de resistência do alvo; ele pode resistir ao veneno.', 'Acerte o boneco com a arma untada',verb='atacar')
lesson('rogue','treino_criar',9,'criar_armadilha',
       'Use Criar Armadilha numa casa vazia da sala. Buraco já está disponível; as demais fórmulas dependem da Guilda. Escolha apenas um mecanismo que você conhece.', 'Crie uma armadilha conhecida')

lesson('cleric','treino_atalhos_cleric',2,'cura',
       'Abra H e vincule Cura ao espaço 1. Depois use 1 para ativá-la; Esc cancela uma mira pendente. Habilidades alternáveis podem ser desligadas com o mesmo atalho; efeitos com duração fixa acabam sozinhos.', 'Vincule Cura ao atalho 1',verb='configurar_atalho')
lesson('cleric','treino_menu_magias_cleric',3,None,
       'Abra o grimório com M, confira as magias conhecidas, feche com M ou Esc e encerre o turno.', 'Conheça o grimório',verb='encerrar_turno',requirements={'magia_tipo':'qualquer'})
lesson('cleric','treino_grimorio',4,None,
       _F16.GRIMORIO, _F16.GRIMORIO_CURTO,verb='usar_magia',requirements={'magia_tipo':'qualquer'})
lesson('cleric','treino_grimorio_turno',5,None,
       _F16.TURNO, _F16.TURNO_CURTO,verb='encerrar_turno')
lesson('cleric','treino_cura',6,'cura',
       'O Aprendiz 1 está ferido. Fique ao lado dele, selecione Cura e use um dado. Confira a vida recuperada e o custo de água.', 'Cure o Aprendiz 1',target_id='__treino_cleric_1',effective=True)
lesson('cleric','treino_cura_area',7,'cura_area',
       'Os dois aprendizes ficaram feridos para este exercício. Fique perto deles e use Cura em Área. No nível inicial o raio é de 2 casas; confira a área e o custo antes de confirmar.', 'Cure os dois aprendizes em área',count=2,effective=True)
lesson('cleric','treino_purificar',8,'purificacao',
       'O Aprendiz 1 está cego por um veneno simulado. Fique ao lado dele, use Purificação e escolha Veneno. Observe o efeito desaparecer.', 'Purifique o Aprendiz 1',target_id='__treino_cleric_1')
lesson('cleric','treino_ressuscitar',9,'ressurreicao',
       'O Aprendiz 1 simula um aliado caído. Fique ao lado dele e use Ressurreição. Ele retorna com a vida determinada pela sua habilidade.', 'Ressuscite o Aprendiz 1',target_id='__treino_cleric_1')

lesson('bard','treino_atalhos_bard',2,'cancao_heroica',
       'Abra H e vincule Canção Heroica ao espaço 1. Depois use 1 para ativá-la; Esc cancela uma mira pendente. Habilidades alternáveis podem ser desligadas com o mesmo atalho; efeitos com duração fixa acabam sozinhos.', 'Vincule Canção Heroica ao atalho 1',verb='configurar_atalho')
lesson('bard','treino_cancao',3,'cancao_heroica',
       'Ative Canção Heroica e escolha um benefício disponível. A canção beneficia você e aliados dentro do seu alcance. O aprendiz permite observar a aura.', 'Ative a Canção Heroica')
lesson('bard','treino_cancao_manter',4,None,
       'Confira o raio da canção e encerre o turno com ela ativa. Ela cobra manutenção enquanto você a sustenta.', 'Mantenha a canção por uma rodada',verb='manter_cancao')
lesson('bard','treino_cancao_parar',5,None,
       'Desative a Canção Heroica para encerrar o efeito e seu consumo de recursos. Não a deixe ativa sem necessidade.', 'Encerre a Canção Heroica',verb='encerrar_cancao')
lesson('bard','treino_provocar',6,'provocacao',
       'Selecione o boneco e use Provocação. Confira o teste de resistência e as consequências do efeito. Uma resistência do inimigo não torna seu uso inválido.', 'Use Provocação no boneco')
import aplicar_fatia11_tutorial as _F11   # baú da Harpa Velha, Nota Cortante e Sinfonia do Alaúde (renumera o Bardo)
_F11.aplicar(d)

lesson('paladin','treino_atalhos_paladin',2,'protetor',
       'Abra H e vincule Protetor ao espaço 1. Depois use 1 para ativá-lo; Esc cancela uma mira pendente. Habilidades alternáveis podem ser desligadas com o mesmo atalho; efeitos com duração fixa acabam sozinhos.', 'Vincule Protetor ao atalho 1',verb='configurar_atalho')
lesson('paladin','treino_refem',3,'__prisioneiro__',
       'O refém está em 35,25. Aproxime-se e clique em Libertar prisioneiro. Depois do resgate você poderá protegê-lo e curá-lo.', 'Liberte o refém',verb='libertar_refem')
lesson('paladin','treino_protetor',4,'__prisioneiro__',
       'O teto está desabando! Fique ao lado do refém, use Protetor e selecione-o. Encerre seu turno para protegê-lo das rochas. Observe a divisão do dano e a redução pessoal de Richard.', 'Proteja o refém durante um ataque',verb='proteger',scene='assets/tela de transição/tutorial/mestre_aula_protetor_refem.png')
lesson('paladin','treino_maos',5,'imposicao_maos',
       'Sua proteção manteve o refém vivo. Agora, no seu turno, fique ao lado dele e use Imposição das Mãos. A lição pede a cura desse mesmo refém ferido.', 'Cure o refém com Imposição das Mãos',target_id='__prisioneiro__',effective=True)
lesson('paladin','treino_guiar_refem',6,_F9.ALVO,_F9.TEXTO,_F9.CURTO,verb='guiar_refem')
lesson('paladin','treino_sagrado',7,'golpe_sagrado',
       'Ative Golpe Sagrado no nível disponível. Depois ataque o boneco e observe o dano sagrado acrescentado. Há custos de ativação e de manutenção.', 'Ative Golpe Sagrado')
lesson('paladin','treino_sagrado_golpe',8,None,
       'Ataque o boneco com Golpe Sagrado ativo para ver seu efeito no dano.', 'Acerte com Golpe Sagrado ativo',verb='atacar')
lesson('paladin','treino_regen',9,'regeneracao_divina',
       'O treino deixou dois pontos de vida para recuperar. Ative Regeneração Divina e encerre sua vez. A tarefa só termina quando a regeneração recuperar vida de verdade.', 'Recupere vida com Regeneração Divina',verb='regenerar')
lesson('paladin','treino_luz',10,'guerreiro_luz',
       'Ative Guerreiro da Luz e compare sua visão, acerto, dano e defesa. O bônus é o da habilidade disponível na sua ficha.', 'Ative Guerreiro da Luz')

# Placas na frente de cada sala exclusiva e lição-ponte até a sala (ordem 3 de cada classe).
# `porta` é o alvo de conclusão: em geral a casa da porta; para o Bardo, a primeira casa
# interna, pois o movimento diagonal pode entrar nela sem passar pela casa externa.
# `casa_placa` fica em chão livre, do lado de fora da sala, a 1 casa da porta.
PORTAS = {'warrior': ([22,7], [22,8], '🛡️', 'Guerreiro', 'fala_6', 'Mestre de Armas'),
          'mage': ([22,21], [22,20], '🔮', 'Mago', 'fala_8', 'Mestre de Armas'),
          'rogue': ([14,7], [15,7], '🗡️', 'Ladino', 'fala_10', 'Mestre de Armas'),
          'cleric': ([30,6], [29,6], '✝️', 'Clérigo', 'fala_12', 'Mestre de Armas'),
          # A tarefa aponta para a primeira casa interna: entrar diagonalmente
          # pela porta não pode deixar a lição-ponte pendente até o aprendiz.
          'bard': ([14,23], [16,23], '🎵', 'Bardo', 'fala_14', 'Mestre de Armas'),
          'paladin': ([31,25], [30,25], '⚔️', 'Paladino', 'fala_16', 'Mestre de Armas')}
for cls, (porta, casa_placa, emoji, nome, ultima, _) in PORTAS.items():
    # A posição da placa pode mudar quando a sala é reorganizada; o ID estável
    # permite atualizar a placa existente sem duplicá-la no JSON.
    placa_id = 'placa_' + cls
    placa = next((x for x in d['decorations'] if x.get('id') == placa_id), None)
    if placa is None:
        placa = {'id': placa_id}
        d['decorations'].append(placa)
    placa.update({'type': 'placa', 'pos': casa_placa, 'facing': [0, 1],
                  'loot': None, 'key_objective': False, 'image': 'placa_fincada.png',
                  'texto': f'{emoji} Sala do {nome} — só ele entra aqui.'})
    placa_idxs = [i for i, x in enumerate(d['decorations']) if x.get('id') == placa_id]
    for i in reversed(placa_idxs[1:]):
        del d['decorations'][i]
    if not any(f['id'] == 'porta_' + cls for f in d['falas']):
        base = next(f for f in d['falas'] if f['id'] == ultima)
        d['falas'].append({'id': 'porta_' + cls, 'pos': base['pos'], 'falante': base['falante'],
                           'texto': _F15.PORTA_MAGE if cls == 'mage' else _F16.PORTA_CLERIC if cls == 'cleric' else 'Muito bem! Agora vá até a porta marcada: ela leva à sala exclusiva do seu herói. Abra-a e entre.',
                           'trigger': {'tipo': 'sala'}, 'classe': cls, 'ordem': 3,
                           'tarefa': {'tipo': 'mover_ate', 'alvo': porta, 'vezes': 1,
                                      'texto_curto': 'Entre na sala do seu herói'}})

for f in d['falas']:
    if f['id'] == 'treino_veneno_golpe':f['tarefa']['requer_veneno'] = True
    if f['id'] == 'treino_sagrado_golpe':f['tarefa']['requer_sagrado'] = True
# Lição comum: atalhos. Última da trilha comum antiga (ordem 19; fala_36-38 foram removidas, ordens 16-18 vagas);
# o filtro do topo preserva falas sem classe, mas o `if not any` mantém a execução idempotente.
if not any(f['id'] == 'fala_atalhos' for f in d['falas']):
    d['falas'].append({
        'id': 'fala_atalhos', 'pos': [49, 16], 'falante': {'nome': 'Instrutor de Treinamento', 'emoji': '🎓'},
        'texto': 'R recentraliza a câmera 3D; Esc cancela uma mira pendente; clicar numa casa faz o herói andar até ela.',
        'trigger': {'tipo': 'proximidade', 'raio': 4}, 'ordem': 19,
        'tarefa': {'tipo': 'encerrar_turno', 'vezes': 1, 'texto_curto': 'Encerre o turno para concluir'}})
else:
    next(f for f in d['falas'] if f['id'] == 'fala_atalhos')['texto'] = 'R recentraliza a câmera 3D; Esc cancela uma mira pendente; clicar numa casa faz o herói andar até ela.'
# As lições de dano usam um único boneco imóvel. A lógica do treinamento aplica
# resistência/vulnerabilidade apenas a esta instância, sem alterar os outros bonecos.
d['monsters'] = [m for m in d['monsters']
                 if m.get('room_id') != 48 and 'esqueleto' not in str(m.get('type', '')).lower()]
d['monsters'].append({'type': 'boneco_treino', 'pos': [51, 15], 'room_id': 48,
                      'boss': False, 'target': False})
next(c for c in d['chests'] if c['pos'] == [49, 17])['items'] = [{'id': 'cajado_madeira'}]
for _fid, _ordem, _texto, _curto in [
    ('fala_res', 20, 'O boneco de treino reduz em 5 o dano cortante. Acerte-o com uma espada e observe o número azul com RESISTIDO.',
     'Acerte o boneco com uma arma cortante'),
    ('fala_vuln', 21, 'Agora pegue e equipe o Cajado de Madeira no baú. Ele causa dano contundente: o boneco é vulnerável e recebe +2. Acerte-o e observe o número vermelho com VULNERÁVEL.',
     'Acerte o boneco com o cajado')]:
    if not any(f['id'] == _fid for f in d['falas']):
        d['falas'].append({'id': _fid, 'pos': [51, 15] if _fid == 'fala_vuln' else [50, 17],
                           'falante': {'nome': 'Mestre de Armas', 'emoji': '🛡️'},
                           'texto': _texto,
                           'trigger': {'tipo': 'sala'} if _fid == 'fala_res' else {'tipo': 'proximidade', 'raio': 1},
                           'ordem': _ordem,
                           'tarefa': {'tipo': 'atacar', 'alvo': 'boneco_treino', 'vezes': 1,
                                      'texto_curto': _curto,
                                      'requer_categoria_arma': 'cortante' if _fid == 'fala_res' else 'contundente',
                                      'requer_sala_alvo': 48}})
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parent))
from aplicar_fatia7_tutorial import aplicar as _aplicar_fatia7   # bonecos de palha/treino da sala 22, fala_30 e lições volta_<classe>
_aplicar_fatia7(d)
from aplicar_fatia8_tutorial import aplicar as _aplicar_fatia8   # boneco de palha com 24 PV, bonecos sensíveis a veneno e fala_30/32
_aplicar_fatia8(d)
from gerar_guia_comum import aplicar_guia
import aplicar_fatia18_tutorial as _F18   # hostilidade antes da porta da ala
_F18.aplicar(d)
import aplicar_fatia19_tutorial as _F19   # apresentação inicial do tutorial
_F19.aplicar(d)
import aplicar_tutorial_missao as _Missao
_Missao.aplicar(d)
aplicar_guia(d)
path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
