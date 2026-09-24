"""Ponte como passagem e quedas só por empurrão.
Roda da raiz: python tools/test_ponte_passagem.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def sala(elev_esq=3, elev_dir=3, altura_json=0, transicao="rampa", vao_parede=True):
    """Dois platôs separados por um vão na coluna x=5, ponte de (4,5) a (6,5).

    `altura_json` é o valor GRAVADO no arquivo — o defeito real do editor era
    gravar 0 aqui quando a ponte nasce antes de o autor pintar a elevação.
    """
    W = H = 11
    r = S.GameRoom.__new__(S.GameRoom)
    r.map_w, r.map_h = W, H
    r.tiles = [[S.FLOOR] * W for _ in range(H)]
    if vao_parede:
        for y in range(H):
            r.tiles[y][5] = S.WALL
    r.elevacoes = {}
    for y in range(H):
        for x in range(W):
            if x < 5:   r.elevacoes[(x, y)] = elev_esq
            elif x > 5: r.elevacoes[(x, y)] = elev_dir
    r.decorations = []; r.materiais = {}
    r._decor_block_tiles = set(); r._mat_solid_tiles = set()
    r._decor_tall_tiles = set(); r._mat_oclui_tiles = set()
    r.monsters = {}; r.players = {}; r.prisoner = None
    r.explored = set(); r.rooms = []
    # Filas efêmeras do feedback visual. São criadas no __init__, e uma fixture
    # de __new__ não as tem — sem elas `_dano_em_alvo` estoura AttributeError
    # em `_damage_visual_context` assim que o teste [7] empurra alguém. Já foi
    # a causa de várias suítes vermelhas no projeto; esta fixture foi rodada
    # contra o código atual antes de entrar no plano.
    r._combat_damage_events = []; r._positive_effect_events = []
    r._resistance_events = []; r._damage_visual_context = {}
    r.transicao_altura = transicao
    r.pontes = [{"id": "p1", "inicio": [4, 5], "fim": [6, 5],
                 "largura": 1, "altura": altura_json}]
    r._rebuild_pontes_index()
    return r

print("\n[1] A altura da ponte vem do TERRENO, não do JSON")
r = sala(altura_json=0)
check("ponte com altura 0 no arquivo assume a elevação dos platôs (3)",
      r._ponte_alturas[(5, 5)] == 3)
check("o valor derivado é gravado de volta, para o payload sair certo",
      r.pontes[0]["altura"] == 3)
check("_elevacao_terreno concorda com o índice",
      r._elevacao_terreno(5, 5) == 3)

print("\n[2] Pontas divergentes usam a MAIS BAIXA")
r2 = sala(elev_esq=3, elev_dir=4, altura_json=9)
check("pontas 3 e 4 resolvem para 3", r2._ponte_alturas[(5, 5)] == 3)
r3 = sala(elev_esq=4, elev_dir=2, altura_json=0)
check("pontas 4 e 2 resolvem para 2", r3._ponte_alturas[(5, 5)] == 2)

print("\n[3] A superfície da ponte é plana")
r4 = sala(altura_json=0)
check("todas as casas da ponte têm a mesma altura",
      len({r4._ponte_alturas[t] for t in r4._ponte_tiles}) == 1)

print("\n[4] _queda_no_passo: a mesma pergunta que a queda faz, feita ANTES de mover")
r = sala(altura_json=0)                      # platôs 3, ponte 3, vão 0
heroi = {"id": "h", "name": "H", "class_id": "warrior", "alive": True,
         "hp": 10, "pos": [4, 5], "altura": 0}
check("plano não é queda",            r._queda_no_passo(heroi, [3, 5], [4, 5]) is False)
check("subir não é queda",            r._queda_no_passo(heroi, [3, 4], [3, 5]) is False)
check("sair da ponte para o vão é queda",
      r._queda_no_passo(heroi, [5, 5], [5, 4]) is True)

# Degrau de 1 fora da ponte: seguro no modo rampa, queda no modo declive.
# Cenário PRÓPRIO, sem ponte: na `sala` acima as duas pontas do vão SÃO ponte,
# então lá a diferença entre elas é sempre zero e o degrau não existe.
def sala_degrau(transicao="rampa"):
    """Sem ponte nenhuma: coluna x<=4 no nível 3, x>=5 no nível 2.
    O passo (4,y) -> (5,y) é um degrau ADJACENTE de exatamente 1."""
    W = H = 11
    r = S.GameRoom.__new__(S.GameRoom)
    r.map_w, r.map_h = W, H
    r.tiles = [[S.FLOOR] * W for _ in range(H)]
    r.elevacoes = {(x, y): (3 if x <= 4 else 2) for y in range(H) for x in range(W)}
    r.decorations = []; r.materiais = {}
    r._decor_block_tiles = set(); r._mat_solid_tiles = set()
    r._decor_tall_tiles = set(); r._mat_oclui_tiles = set()
    r.monsters = {}; r.players = {}; r.prisoner = None
    r.explored = set(); r.rooms = []
    r._combat_damage_events = []; r._positive_effect_events = []
    r._resistance_events = []; r._damage_visual_context = {}
    r.transicao_altura = transicao
    r.pontes = []
    r._rebuild_pontes_index()
    return r

rr = sala_degrau()
check("descer 1 fora da ponte NÃO é queda (rampa)",
      rr._queda_no_passo(heroi, [4, 5], [5, 5]) is False)
rd = sala_degrau(transicao="declive")
check("descer 1 fora da ponte É queda (declive)",
      rd._queda_no_passo(heroi, [4, 5], [5, 5]) is True)

print("\n[5] _passo_seguro = permitido pela elevação E sem queda")
r = sala(altura_json=0)
check("platô -> ponte é seguro",   r._passo_seguro(heroi, [4, 5], [5, 5]) is True)
check("ponte -> platô é seguro",   r._passo_seguro(heroi, [5, 5], [6, 5]) is True)
check("ponte -> vão lateral NÃO é seguro",
      r._passo_seguro(heroi, [5, 5], [5, 4]) is False)
check("rampa: descer 1 degrau continua sendo oferecido",
      sala_degrau()._passo_seguro(heroi, [4, 5], [5, 5]) is True)
rd = sala_degrau(transicao="declive")
check("declive: descer 1 deixa de ser oferecido",
      rd._passo_seguro(heroi, [4, 5], [5, 5]) is False)
check("declive: o EMPURRÃO que desce 1 continua sendo queda",
      rd._queda_no_passo(heroi, [4, 5], [5, 5]) is True)

print("\n[6] Voo continua isento")
voador = {"id": "v", "name": "V", "class_id": "mage", "alive": True,
          "hp": 10, "pos": [5, 5], "altura": 2, "voo": True}
r = sala(altura_json=0)
check("quem voa acima do solo não sofre queda de terreno",
      r._queda_no_passo(voador, [5, 5], [5, 4]) is False)

import inspect, re

print("\n[7] O empurrão CONTINUA derrubando (a prova de que não cortamos demais)")
# `_empurrar` é testável sozinho: não exige turno, iniciativa nem push_state.
# É de propósito o único caminho que ainda chama _aplicar_queda_terreno.
r = sala(altura_json=0)
r.round_num = 1
async def noop(*a, **k): pass
r.broadcast = noop; r.send_to = noop; r.gm_say = noop
async def _dado(q, f, label=None, damage_type=None):
    assert damage_type == S.DMG_PHYSICAL, damage_type
    return q * f
r._rolar_dano_mostrado = _dado
h = {"id": "h", "name": "H", "class_id": "warrior", "alive": True, "hp": 40,
     "max_hp": 40, "pos": [5, 5], "altura": 0, "resistances": []}
r.players = {"h": h}
asyncio.run(r._empurrar(h, 0, -1, 1))
check("empurrar da ponte para o vão custa HP", h["hp"] < 40)

print("\n[8] Os portões usam _passo_seguro")
for nome in ("handle_move", "_tile_livre_para_animado", "_passo_monstro",
             "_commit_monster_step", "_monster_can_occupy",
             "_passo_livre_licantropo"):
    corpo = inspect.getsource(getattr(S.GameRoom, nome))
    check(f"{nome} usa _passo_seguro", "_passo_seguro" in corpo)

print("\n[9] Nenhum caminho VOLUNTÁRIO aplica queda")
# Varredura estática: `await self._aplicar_queda_terreno` só pode sobrar dentro
# de _empurrar. Um `await` novo em qualquer outro lugar reabre o defeito —
# jogador caindo num clique — e nenhum teste de comportamento pegaria os nove
# caminhos de uma vez.
fonte = inspect.getsource(S)
chamadas = [m.start() for m in re.finditer(r"await self\._aplicar_queda_terreno", fonte)]
corpo_empurrar = inspect.getsource(S.GameRoom._empurrar)
check("sobraram exatamente 2 chamadas de queda", len(chamadas) == 2)
check("as 2 estão dentro de _empurrar",
      corpo_empurrar.count("await self._aplicar_queda_terreno") == 2)

print("\n" + "=" * 62)
print(f"  {PASS} passaram, {FAIL} falharam")
print("=" * 62)
sys.exit(1 if FAIL else 0)
