"""Lição da direção no Campo de Treinamento (spec 2026-11-25-ensino-direcao)."""
import asyncio, json, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

FALHAS = []
def check(name, cond):
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond: FALHAS.append(name)

async def nada(*a, **k): return None
def run(c): return asyncio.run(c)


def sala_treino(licoes):
    r = S.GameRoom("LIC")
    r.gm_say = nada; r.push_state = nada; r.send_to = nada; r.broadcast = nada
    r._broadcast_dado = nada; r.broadcast_city_state = nada
    r.phase = "playing"; r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 12, "h": 12, "cx": 6, "cy": 6, "locked": False, "doors": []}]
    r.round_num = 1
    r.training_mode = True; r.training_state = {}; r.falas = []
    r.licoes = licoes; r.licoes_feitas = set()
    return r


def lic_dir(passos=None):
    return {"id": "fala_direcao", "ordem": 34, "pos": [3, 3], "texto": "", "tarefa":
            {"tipo": "escolher_direcao", "vezes": 1, "texto_curto": "Escolha a direção"},
            "falante": {"nome": "Mestre", "emoji": "x"}, "trigger": {"tipo": "proximidade", "raio": 2},
            "guia": passos or [{"id": "a", "texto": "x"}, {"id": "b", "texto": "y"}]}


def heroi(r, pid="p1", slot=0):
    p = S.make_player(pid, "Ana", "warrior", slot)
    p["pos"] = [3, 3]; p["facing"] = [0, 1]
    p.update(licao_atual="fala_direcao", licoes_feitas=[], licao_progresso={"fala_direcao": 0},
             tutorial_history=[], licao_passo=0)
    r.players[pid] = p
    return p


async def fim_de_turno(facing, forcado=False, recusa=False):
    r = sala_treino([lic_dir()])
    p = heroi(r); q = S.make_player("p2", "Bia", "warrior", 1); q["pos"] = [1, 1]
    r.players["p2"] = q; r.player_order = ["p1", "p2"]
    r.initiative_active = True; r._rebuild_initiative()
    r.initiative_index = next(i for i, e in enumerate(r.initiative_order) if e["id"] == "p1")
    if recusa:
        p["pending_spell_pick"] = {"x": 1}; r._enviar_spell_pick_prompt = nada
    await r.handle_end_turn("p1", _forcado=forcado, facing=facing)
    return "fala_direcao" in p["licoes_feitas"]


def main():
    print("\n[1] Verbo e condição de setor")
    check("escolher_direcao é verbo de lição", "escolher_direcao" in S.LICAO_VERBOS)

    print("\n[2] end_turn com direção conclui a lição")
    check("direção válida conclui", run(fim_de_turno([-1, 0])))
    check("sem direção não conclui", not run(fim_de_turno(None)))
    check("direção diagonal não conclui", not run(fim_de_turno([1, 1])))
    check("fim forçado (timeout) não conta como prática", not run(fim_de_turno([0, 1], forcado=True)))
    check("end_turn recusado não conclui", not run(fim_de_turno([0, 1], recusa=True)))

    print("\n[3] Passo do guia que exige atacar pelas costas")
    passos = [{"id": "a", "texto": "x"},
              {"id": "b", "texto": "y", "conclui_com": {"tipo": "atacar", "alvo": "boneco_treino", "requer_setor": "costas"}},
              {"id": "c", "texto": "z"}]
    async def atacar(setor):
        r = sala_treino([lic_dir(passos)]); p = heroi(r); p["licao_passo"] = 1
        await r._licao_evento(p, "atacar", alvo="boneco_treino", contexto={"setor": setor, "sala_alvo_id": 48})
        return p["licao_passo"]
    check("ataque pela frente não avança o passo", run(atacar("frente")) == 1)
    check("ataque pelo flanco não avança (exige costas)", run(atacar("flanco")) == 1)
    check("ataque pelas costas avança", run(atacar("costas")) == 2)
    async def sem_setor():
        r = sala_treino([lic_dir(passos)]); p = heroi(r); p["licao_passo"] = 1
        await r._licao_evento(p, "atacar", alvo="boneco_treino", contexto={})
        return p["licao_passo"]
    check("ataque sem contexto de setor não avança", run(sem_setor()) == 1)

    print("\n[4] O ataque do herói informa o setor à lição")
    capt = {}
    async def golpe(facing_alvo):
        r = sala_treino([])
        r._is_turn = lambda pid: True
        p = S.make_player("p1", "Ana", "warrior", 0); p["pos"] = [5, 4]; p["atk_bonus"] = 50; p["alive"] = True
        p["connected"] = True; r.players["p1"] = p; r.connections["p1"] = object()
        m = S.make_monster(next(d for d in S.MONSTER_DEFS if d["type"] == "goblin"), r.rooms[0])
        m.update(id="m1", pos=[5, 5], hp=500, max_hp=500, ac=1, facing=list(facing_alvo), alertado=True)
        r.monsters["m1"] = m
        async def espia(pp, verbo, alvo=None, contexto=None):
            if verbo == "atacar": capt["setor"] = (contexto or {}).get("setor")
        r._licao_evento = espia
        await r.handle_attack("p1", "m1")
        return capt.get("setor")
    check("pelas costas: contexto.setor = costas", run(golpe((0, 1))) == "costas")
    check("de frente: contexto.setor = frente", run(golpe((0, -1))) == "frente")

    print("\n[5] Lição no Campo de Treinamento")
    d = json.load(open(os.path.join(RAIZ, "dungeons", "campo_de_treinamento.json"), encoding="utf-8"))
    fala = next((f for f in d["falas"] if f["id"] == "fala_direcao"), None)
    check("fala_direcao existe, ordem 34 e tarefa escolher_direcao",
          bool(fala) and fala["ordem"] == 34 and fala["tarefa"]["tipo"] == "escolher_direcao")
    check("o guia tem o passo de atacar pelas costas com requer_setor",
          bool(fala) and any((p.get("conclui_com") or {}).get("requer_setor") == "costas" for p in fala["guia"]))
    check("o guia marca a casa atrás do boneco", bool(fala) and any(str(p.get("ui", "")).startswith("casa:") for p in fala["guia"]))
    ok, msg = S.validar_dungeon(d)
    check(f"a masmorra continua válida ({msg if not ok else 'ok'})", ok)
    ordens = [f["ordem"] for f in d["falas"] if f.get("ordem") is not None and not f.get("classe")]
    check("nenhuma ordem comum repetida", len(ordens) == len(set(ordens)))

    print("\n[6] Fluxo real no Campo de Treinamento (boneco da sala 48)")
    sys.path.insert(0, os.path.join(RAIZ, "tools"))
    from test_tutorial_salas import room as sala_campo
    import copy
    from unittest.mock import patch
    async def campo(pos_heroi):
        r, p = sala_campo("warrior")
        for sala in r.rooms:
            sala["locked"] = False        # no jogo o herói já abriu a porta; sala trancada = monstro inativo
        anteriores = [f for f in r.licoes if f.get("ordem") is not None and f["ordem"] < 34 and not f.get("classe")]
        p["licoes_feitas"] = [f["id"] for f in anteriores]
        p["licao_progresso"] = {f["id"]: (f.get("tarefa") or {}).get("vezes", 1) for f in anteriores}
        p["licoes_puladas"] = []; p["licao_atual"] = None
        p["pos"] = [51, 16]; p["action_done"] = False
        await r._verificar_falas(p, r._room_containing_point(p["pos"]))
        achou = p["licao_atual"]
        boneco = next(m for m in r.monsters.values() if m.get("room_id") == 48)
        p["licao_passo"] = 2                    # passos "olhar" e "costas" já lidos
        p["pos"] = list(pos_heroi); p["action_done"] = False
        p["weapon"] = copy.deepcopy(S._DUNGEON_ITEM_CATALOG["cajado_madeira"])
        with patch.object(S.random, "randint", return_value=20), patch.object(S, "roll_dice", return_value=1):
            await r.handle_attack(p["id"], boneco["id"])
        return achou, p["licao_passo"], p["licao_atual"]
    achou, passo, atual = run(campo((51, 14)))
    check("perto do boneco, a vulnerabilidade concluída libera a lição da direção", achou == "fala_direcao")
    check("atacar o boneco PELAS COSTAS (casa [51,14]) avança o passo do guia", passo == 3 and atual == "fala_direcao")
    achou, passo, atual = run(campo((51, 16)))
    check("atacar de FRENTE (casa [51,16]) não avança o passo", passo == 2)
    achou, passo, atual = run(campo((50, 15)))
    check("atacar pelo FLANCO (casa [50,15]) não avança o passo", passo == 2)

    print(f"\nFalhas: {len(FALHAS)}")
    sys.exit(1 if FALHAS else 0)

main()
