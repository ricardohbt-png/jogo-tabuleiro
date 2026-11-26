"""Bônus posicional nos ataques, Furtivo e end_turn.facing (spec 2026-11-25)."""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

FALHAS = []
def check(name, cond):
    print(("  ✅ " if cond else "  ❌ ") + name)
    if not cond: FALHAS.append(name)


async def nada(*a, **k): return None


def sala():
    r = GameRoom("DIR")
    r.gm_say = nada; r.push_state = nada; r.send_to = nada; r.broadcast = nada
    r._broadcast_dado = nada; r.broadcast_city_state = nada
    r.phase = "playing"
    r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.rooms = [{"id": 0, "x": 0, "y": 0, "w": 12, "h": 12, "cx": 6, "cy": 6, "locked": False, "doors": []}]
    r.round_num = 1
    return r


def goblin(r, mid, pos, facing):
    m = S.make_monster(next(d for d in S.MONSTER_DEFS if d["type"] == "goblin"), r.rooms[0])
    m["id"] = mid; m["pos"] = list(pos); m["facing"] = list(facing); m["hp"] = m["max_hp"] = 50
    m["alertado"] = True
    r.monsters[mid] = m
    return m


def main():
    print("\n[1] Herói: _modificadores_ataque_heroi soma costas/flanco/altura")
    r = sala()
    p = make_player("p1", "Ana", "warrior", 0); p["pos"] = [5, 6]; r.players["p1"] = p
    m = goblin(r, "m1", (5, 5), (0, 1))                 # olha para o sul = para o herói
    base = r._modificadores_ataque_heroi(p, m, [5, 5], None, previa=True)
    check("de frente: bônus posicional 0", base["posicional"]["total"] == 0)
    m["facing"] = [0, -1]                                # de costas para o herói
    costas = r._modificadores_ataque_heroi(p, m, [5, 5], None, previa=True)
    check("pelas costas: eff_atk +2", costas["eff_atk"] == base["eff_atk"] + 2)
    check("pelas costas: posicional.setor", costas["posicional"]["setor"] == "costas")
    m["facing"] = [1, 0]
    flanco = r._modificadores_ataque_heroi(p, m, [5, 5], None, previa=True)
    check("pelo flanco: eff_atk +1", flanco["eff_atk"] == base["eff_atk"] + 1)
    r._elevacao_terreno = lambda x, y: 3 if (x, y) == (5, 6) else 0
    alto = r._modificadores_ataque_heroi(p, m, [5, 5], None, previa=True)
    check("flanco + altura 2 = +3", alto["eff_atk"] == base["eff_atk"] + 3)

    print("\n[2] Monstro atacando herói (simétrico)")
    async def golpe(facing_heroi):
        r = sala()
        heroi = make_player("p", "Ana", "warrior", 0)
        heroi["pos"] = [5, 5]; heroi["facing"] = list(facing_heroi); heroi["hp"] = heroi["max_hp"] = 500
        r.players["p"] = heroi
        m = goblin(r, "m", (5, 6), (0, -1))             # ataca do sul
        capt = {}
        async def bc(msg, *a, **k):
            if isinstance(msg, dict) and msg.get("type") == "dice_roll" and msg.get("die") == "d20":
                capt["atk"] = msg.get("modifier")
        r.broadcast = bc
        await r._execute_one_monster_attack(m, m["attacks"][0], {"kind": "player", "obj": heroi})
        return capt.get("atk")
    de_frente = asyncio.run(golpe((0, 1)))              # herói olha para o sul, o goblin está ao sul
    de_costas = asyncio.run(golpe((0, -1)))             # herói olha para o norte, goblin pelas costas
    check("monstro nas costas do herói acerta com +2", de_frente is not None and de_costas == de_frente + 2)

    print("\n[3] Ataque Furtivo do Ladino")
    r = sala()
    lad = make_player("l", "Luccas", "rogue", 0); lad["pos"] = [5, 4]; r.players["l"] = lad
    alvo = goblin(r, "t", (5, 5), (0, 1))               # olha para o sul; ladino ao norte = costas
    check("nível base: pelas costas dispara", r._verificar_ataque_furtivo(lad, alvo) is True)
    lad["pos"] = [6, 5]
    check("nível base: pelo flanco NÃO dispara", r._verificar_ataque_furtivo(lad, alvo) is False)
    lad["pos"] = [5, 6]
    check("nível base: de frente NÃO dispara", r._verificar_ataque_furtivo(lad, alvo) is False)
    lad["guild_owned"]["especializacoes"] = ["ladino_furtivo_2"]
    lad["pos"] = [6, 5]
    check("nível II: pelo flanco dispara", r._verificar_ataque_furtivo(lad, alvo) is True)
    lad["pos"] = [5, 6]
    check("nível II: de frente sem aliado NÃO dispara", r._verificar_ataque_furtivo(lad, alvo) is False)
    amigo = make_player("a", "Ana", "warrior", 1); amigo["pos"] = [4, 5]; r.players["a"] = amigo
    check("nível II: aliado adjacente ao alvo continua valendo", r._verificar_ataque_furtivo(lad, alvo) is True)
    del r.players["a"]
    lad["guild_owned"]["especializacoes"] = []
    lad["invisivel_sombras"] = True
    check("oculto continua disparando", r._verificar_ataque_furtivo(lad, alvo) is True)
    lad.pop("invisivel_sombras"); lad["pos"] = [5, 4]
    alvo["defesa_impecavel_ate"] = 99
    check("Defesa Impecável continua imunizando", r._verificar_ataque_furtivo(lad, alvo) is False)
    alvo.pop("defesa_impecavel_ate")
    alvo["dormindo"] = True; alvo["dormindo_rodadas"] = 2; lad["pos"] = [5, 6]
    check("alvo dormindo conta como costas", r._verificar_ataque_furtivo(lad, alvo) is True)
    check("descrição do nível II cita flanco", "flanco" in S.GUILD_CATALOG["ladino_furtivo_2"]["desc"].lower())

    print("\n[4] end_turn aplica a direção escolhida")
    async def fim_de_turno(facing, depois_de_recusa=False):
        r = sala()
        p = make_player("p1", "Ana", "warrior", 0); p["pos"] = [3, 3]; p["facing"] = [0, 1]
        q = make_player("p2", "Bia", "warrior", 1); q["pos"] = [1, 1]
        r.players = {"p1": p, "p2": q}; r.player_order = ["p1", "p2"]
        r.initiative_active = True; r._rebuild_initiative()
        r.initiative_index = next(i for i, e in enumerate(r.initiative_order) if e["id"] == "p1")
        if depois_de_recusa:
            p["pending_spell_pick"] = {"x": 1}
        r._enviar_spell_pick_prompt = nada
        try:
            await r.handle_end_turn("p1", facing=facing)
        except TypeError as e:
            return "TypeError"
        return p.get("facing")
    check("facing válido é gravado", asyncio.run(fim_de_turno([-1, 0])) == [-1, 0])
    check("facing diagonal é ignorado", asyncio.run(fim_de_turno([1, 1])) == [0, 1])
    check("facing lixo é ignorado", asyncio.run(fim_de_turno("norte")) == [0, 1])
    check("sem facing mantém", asyncio.run(fim_de_turno(None)) == [0, 1])
    check("end_turn recusado (magia pendente) não muda a direção",
          asyncio.run(fim_de_turno([-1, 0], depois_de_recusa=True)) == [0, 1])
    check("o dispatch repassa msg.facing", 'facing=msg.get("facing")' in open(S.__file__, encoding="utf-8").read().replace(" ", "")
          or "msg.get(\"facing\")" in open(S.__file__, encoding="utf-8").read())

    print(f"\nFalhas: {len(FALHAS)}")
    sys.exit(1 if FALHAS else 0)


main()
