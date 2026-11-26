"""IA de flanqueio dos monstros espertos (spec 2026-11-25-ia-flanqueio)."""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []
def check(name, cond):
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond: FALHAS.append(name)

async def nada(*a, **k): return None

def sala():
    r = S.GameRoom("FLK")
    r.gm_say = nada; r.push_state = nada; r.send_to = nada; r.broadcast = nada
    r._broadcast_dado = nada; r.broadcast_city_state = nada
    r.phase = "playing"; r.map_w = r.map_h = 14
    r.tiles = [[S.FLOOR] * 14 for _ in range(14)]
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 14, "h": 14, "cx": 7, "cy": 7, "locked": False, "doors": []}]
    r.round_num = 1
    return r

def heroi(r, pos=(5, 5), facing=(0, 1)):
    p = S.make_player("p", "Ana", "warrior", 0)
    p["pos"] = list(pos); p["facing"] = list(facing); p["hp"] = p["max_hp"] = 200
    r.players["p"] = p
    return p

def monstro(r, tipo, pos, mid="m", mov=6):
    m = S.make_monster(next(d for d in S.MONSTER_DEFS if d["type"] == tipo), r.rooms[0])
    m["id"] = mid; m["pos"] = list(pos); m["alertado"] = True; m["movement"] = mov
    m["_water_moves_left"] = mov
    # Equipamento sorteado ao nascer: fixa um ataque corpo a corpo para o teste ser determinístico.
    m["attacks"] = [{"name": "Adaga", "atk_bonus": 4, "damage": "1d4", "reach": 1, "damage_types": ["physical"],
                     "num_attacks": 1, "attack_attribute": "dex", "range": None}]
    r.monsters[mid] = m
    return m

def alvos(p): return [{"kind": "player", "obj": p}]
def run(c): return asyncio.run(c)
def cheb(a, b): return max(abs(a[0] - b[0]), abs(a[1] - b[1]))

# Herói em (5,5) olhando para o sul [0,1]: as costas são as casas ao norte (y=4).
COSTAS = {(5, 4)}   # monstro só ataca em casa ORTOGONAL: a única casa de costas é a do norte

def main():
    print("\n[1] Esperto contorna para as costas")
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (9, 5))
    movido = run(r._monster_flank_premove(m, alvos(p)))
    check("bandido do flanco leste vai para as costas", movido and tuple(m["pos"]) in COSTAS)
    check("o passo gastou o orçamento de movimento", m["_water_moves_left"] < 6)

    print("\n[2] Quem não é esperto não se move")
    r = sala(); p = heroi(r); m = monstro(r, "orc", (9, 5))
    check("orc fica parado", not run(r._monster_flank_premove(m, alvos(p))) and m["pos"] == [9, 5])
    check("_monster_flanqueia: orc não, bandido sim", not r._monster_flanqueia(m)
          and r._monster_flanqueia(monstro(r, "bandido", (1, 1), mid="b")))
    for tipo in ("goblin_assassino", "lobo_cinzento", "bugbear_sombras"):
        mm = next((d for d in S.MONSTER_DEFS if d["type"] == tipo), None)
        check(f"{tipo} é esperto", mm is not None and r._monster_flanqueia({"type": tipo}))

    print("\n[2b] Flag e perfis")
    r = sala()
    check("flanqueia=True liga", r._monster_flanqueia({"type": "orc", "flanqueia": True}))
    check("flanqueia=False desliga", not r._monster_flanqueia({"type": "bandido", "flanqueia": False}))
    check("perfil personalizado tático liga",
          r._monster_flanqueia({"type": "x", "_personalizado": True, "ai_type": "tatico"}))
    check("perfil agressivo personalizado não",
          not r._monster_flanqueia({"type": "x", "_personalizado": True, "ai_type": "agressivo"}))

    print("\n[3] Nunca perde o ataque")
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (12, 5), mov=2)
    check("costas fora do orçamento: não se move", not run(r._monster_flank_premove(m, alvos(p))) and m["pos"] == [12, 5])
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (5, 4))
    check("já nas costas: fica", not run(r._monster_flank_premove(m, alvos(p))) and m["pos"] == [5, 4])
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (6, 5))
    check("no flanco com costas ao alcance: melhora para as costas",
          run(r._monster_flank_premove(m, alvos(p))) and tuple(m["pos"]) in COSTAS)
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (5, 6))
    run(r._monster_flank_premove(m, alvos(p)))
    check("na frente com orçamento: contorna até as costas", tuple(m["pos"]) in COSTAS)
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (12, 5), mov=0)
    check("sem movimento: nada", not run(r._monster_flank_premove(m, alvos(p))))

    print("\n[4] Casas ocupadas e perigosas")
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (9, 5))
    monstro(r, "orc", (5, 4), mid="o0")
    run(r._monster_flank_premove(m, alvos(p)))
    check("costas ocupadas: não entra, vai para o flanco", tuple(m["pos"]) not in COSTAS and m["pos"] in ([6, 5], [4, 5]))
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (9, 5))
    r._monster_known_hazard_tiles = lambda mm: set(COSTAS)
    run(r._monster_flank_premove(m, alvos(p)))
    check("costas perigosas: não entra nelas", tuple(m["pos"]) not in COSTAS)

    print("\n[5] Exclusões")
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (9, 5)); m["attacks"] = [{"name": "Arco", "range": 6, "atk_bonus": 3, "damage": "1d6"}]
    check("ataque à distância: não flanqueia", not run(r._monster_flank_premove(m, alvos(p))) and m["pos"] == [9, 5])
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (9, 5)); m["size"] = [2, 2]
    check("criatura 2×2: não flanqueia", not run(r._monster_flank_premove(m, alvos(p))))
    r = sala(); p = heroi(r); m = monstro(r, "bandido", (9, 5)); p["dormindo"] = True
    run(r._monster_flank_premove(m, alvos(p)))
    check("alvo incapaz (tudo é costas): perto basta, não desvia", m["pos"] == [9, 5] or cheb(m["pos"], [5, 5]) >= 1)

    print("\n[6] Pela IA real: o ataque sai pelas costas")
    async def golpe(flanqueia):
        r = sala(); p = heroi(r); m = monstro(r, "lobo_cinzento", (9, 5))
        m["flanqueia"] = flanqueia
        mods = []
        async def bc(msg, *a, **k):
            if isinstance(msg, dict) and msg.get("type") == "dice_roll" and msg.get("die") == "d20":
                mods.append(msg.get("modifier"))
        r.broadcast = bc
        await r._run_monster_ai(m, alvos(p))
        return m, mods
    m1, mods1 = run(golpe(True))
    m0, mods0 = run(golpe(False))
    check("com flanqueio o lobo termina nas costas", tuple(m1["pos"]) in COSTAS)
    check("sem flanqueio ele para na primeira casa adjacente (comportamento antigo)",
          tuple(m0["pos"]) not in COSTAS and abs(m0["pos"][0] - 5) + abs(m0["pos"][1] - 5) == 1)
    check("o ataque dele pelas costas soma +2 em relação ao do flanco (+1)",
          bool(mods1) and bool(mods0) and mods1[0] == mods0[0] + 1)

    print("\n[7] Seta de intenção mostra a casa de flanqueio e o setor")
    def intencao(flanqueia, facing=(0, 1)):
        r = sala(); p = heroi(r, facing=facing); p["connected"] = True; r.connections["p"] = object()
        m = monstro(r, "lobo_cinzento", (9, 5)); m["flanqueia"] = flanqueia
        return r._prever_intencoes("p"), r, p, m
    itens, r, p, m = intencao(True)
    check("esperto: casa_ataque é a das costas e o setor é 'costas'",
          len(itens) == 1 and itens[0]["casa_ataque"] == [5, 4] and itens[0]["setor"] == "costas")
    itens, *_ = intencao(False)
    check("não esperto: primeira casa adjacente (flanco) e setor 'flanco'",
          itens[0]["casa_ataque"] == [6, 5] and itens[0]["setor"] == "flanco")
    itens, r, p, m = intencao(True)
    p["facing"] = [0, -1]          # herói vira para o norte: as costas passam a ser o sul
    itens2 = r._prever_intencoes("p")
    check("a seta acompanha a direção nova do herói (cache invalidado)",
          itens2[0]["casa_ataque"] == [5, 6] and itens2[0]["setor"] == "costas")
    # a seta bate com o que a IA realmente faz
    r = sala(); p = heroi(r); m = monstro(r, "lobo_cinzento", (9, 5)); m["flanqueia"] = True
    p["connected"] = True; r.connections["p"] = object()
    previsto = r._prever_intencoes("p")[0]["casa_ataque"]
    run(r._monster_flank_premove(m, alvos(p)))
    check("a casa prevista é a casa onde o monstro de fato para", m["pos"] == previsto)

    print(f"\nFalhas: {len(FALHAS)}")
    sys.exit(1 if FALHAS else 0)

main()
