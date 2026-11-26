"""Direção, flanco, costas e altura (spec 2026-11-25). Roda da raiz: python -X utf8 tools/test_direcao_flanco.py"""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")


def setup():
    r = GameRoom("TEST")
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.push_state = noop; r.broadcast_city_state = noop
    r.errs = []
    async def cap(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": r.errs.append(msg)
    r.send_to = cap
    r.phase = "playing"
    r.elev = {}
    r._elevacao_terreno = lambda x, y: r.elev.get((x, y), 0)
    return r


def mon(r, mid, pos, facing=None, size=(1, 1), **kw):
    m = {"id": mid, "type": "goblin", "name": "Goblin", "pos": list(pos), "hp": 10, "max_hp": 10,
         "ac": 10, "size": list(size)}
    if facing is not None: m["facing"] = list(facing)
    m.update(kw)
    r.monsters[mid] = m
    return m


def hero(r, pid="h1", pos=(0, 0), facing=None, cls="warrior"):
    p = make_player(pid, "Heroi", cls, 0)
    p["pos"] = list(pos)
    if facing is not None: p["facing"] = list(facing)
    else: p.pop("facing", None)
    r.players[pid] = p
    return p


# Alvo em (5,5). Para cada direção, setor esperado de cada casa vizinha (dx,dy do atacante).
def esperado(f, rel):
    dot = rel[0] * f[0] + rel[1] * f[1]
    cruz = abs(rel[0] * f[1] - rel[1] * f[0])
    if dot < 0 and -dot >= cruz: return "costas"
    if cruz > abs(dot): return "flanco"
    return "frente"


def main():
    print("\n[1] Tabela 3/2/3 nas 4 direções")
    for f in ([0, 1], [0, -1], [1, 0], [-1, 0]):
        r = setup(); alvo = mon(r, "t", (5, 5), facing=f)
        cont = {"frente": 0, "flanco": 0, "costas": 0}
        ok = True
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if not (dx or dy): continue
                a = hero(r, "a", (5 + dx, 5 + dy))
                s = r._setor_ataque(a, alvo)
                cont[s] += 1
                ok &= (s == esperado(f, (dx, dy)))
        check(f"direção {f}: setores corretos", ok)
        check(f"direção {f}: 3 frente / 2 flanco / 3 costas", cont == {"frente": 3, "flanco": 2, "costas": 3})

    print("\n[2] Direção padrão e à distância")
    r = setup(); h = hero(r, "h", (5, 5))
    a = mon(r, "a", (5, 8))
    check("herói sem facing olha para o sul", r._facing_de(h) == [0, 1])
    check("atacante ao sul de herói sem facing = frente", r._setor_ataque(a, h) == "frente")
    a2 = mon(r, "a2", (5, 2))
    check("atacante ao norte de herói sem facing = costas", r._setor_ataque(a2, h) == "costas")
    mo = mon(r, "o", (9, 9), oriented=True, size=(2, 1))
    check("monstro orientado sem facing olha para oeste", r._facing_de(mo) == [-1, 0])
    mn = mon(r, "n", (9, 3))
    check("monstro comum sem facing olha para o sul", r._facing_de(mn) == [0, 1])
    mn["facing"] = [1, 1]
    check("facing inválido cai no padrão", r._facing_de(mn) == [0, 1])
    far = hero(r, "far", (5, 14))
    alvo = mon(r, "t", (5, 5), facing=[0, 1])
    check("à distância: ângulo dentro de 45° do sul = frente", r._setor_ataque(far, alvo) == "frente")
    far["pos"] = [5, -4]
    check("à distância: ao norte = costas", r._setor_ataque(far, alvo) == "costas")
    far["pos"] = [14, 5]
    check("à distância: ao leste = flanco", r._setor_ataque(far, alvo) == "flanco")

    print("\n[3] Alvo 2×2 (centro do footprint)")
    r = setup(); g = mon(r, "g", (5, 5), facing=[0, 1], size=(2, 2))
    check("2×2 ao norte com facing sul = costas", r._setor_ataque(hero(r, "a", (5, 3)), g) == "costas")
    check("2×2 diagonal traseira = costas", r._setor_ataque(hero(r, "b", (7, 3)), g) == "costas")
    check("2×2 lateral = flanco", r._setor_ataque(hero(r, "c", (7, 5)), g) == "flanco")
    check("2×2 pela frente = frente", r._setor_ataque(hero(r, "d", (5, 7)), g) == "frente")

    print("\n[4] Alvo incapaz conta como costas")
    r = setup(); h = hero(r, "h", (5, 5), facing=[0, 1]); a = mon(r, "a", (5, 6))
    check("ativo olhando para o atacante = frente", r._setor_ataque(a, h) == "frente")
    for chave in ("dormindo", "paralisado", "petrificado", "enredado", "perde_turno"):
        h2 = hero(r, "h2", (5, 5), facing=[0, 1]); h2[chave] = True
        check(f"herói {chave} = costas", r._setor_ataque(a, h2) == "costas")
    d = mon(r, "d", (8, 8), facing=[0, 1]); d["dormindo"] = True; d["dormindo_rodadas"] = 3
    check("monstro dormindo = costas", r._setor_ataque(hero(r, "x", (8, 9)), d) == "costas")
    r2 = setup(); r2._monstro_ativo_em_combate = lambda m: False
    inerte = mon(r2, "i", (5, 5), facing=[0, 1])
    check("monstro inativo (sala trancada/dormente) = costas", r2._setor_ataque(hero(r2, "y", (5, 6)), inerte) == "costas")

    print("\n[5] Altura")
    r = setup(); alvo = mon(r, "t", (5, 5), facing=[0, 1]); a = hero(r, "a", (5, 6))
    check("mesmo nível = 0", r._bonus_altura(a, alvo) == 0)
    r.elev[(5, 6)] = 1
    check("1 nível acima = +1", r._bonus_altura(a, alvo) == 1)
    r.elev[(5, 6)] = 3
    check("3 níveis acima = +2 (teto)", r._bonus_altura(a, alvo) == 2)
    r.elev[(5, 6)] = 0; r.elev[(5, 5)] = 2
    check("abaixo do alvo = 0 (sem penalidade)", r._bonus_altura(a, alvo) == 0)
    r.elev[(5, 5)] = 0; r.elev[(5, 6)] = 2; a["altura"] = 4
    check("voo não soma altura", r._bonus_altura(a, alvo) == 2)

    print("\n[6] Bônus posicional total")
    r = setup(); alvo = mon(r, "t", (5, 5), facing=[0, 1])
    b = r._bonus_posicional(hero(r, "a", (5, 4)), alvo)
    check("costas = +2", b["total"] == 2 and b["setor"] == "costas" and b["costas"] == 2)
    b = r._bonus_posicional(hero(r, "b", (6, 5)), alvo)
    check("flanco = +1", b["total"] == 1 and b["flanco"] == 1)
    b = r._bonus_posicional(hero(r, "c", (5, 6)), alvo)
    check("frente = 0", b["total"] == 0)
    r.elev[(5, 4)] = 5
    b = r._bonus_posicional(hero(r, "d", (5, 4)), alvo)
    check("costas + altura 2 = +4 (teto)", b["total"] == 4 and b["altura"] == 2)
    r.elev[(5, 4)] = 5
    assert S.BONUS_POSICIONAL_MAX == 4
    check("monstro atacando herói de costas também ganha +2",
          r._bonus_posicional(mon(r, "m", (3, 2)), hero(r, "alvo", (3, 3), facing=[0, 1]))["total"] == 2)

    print("\n[7] Paridade servidor × cliente (gameState.js via node)")
    import json, random, subprocess
    rnd = random.Random(7)
    r = setup(); casos = []; srv = []
    for i in range(120):
        f = rnd.choice(([0, 1], [0, -1], [1, 0], [-1, 0]))
        grande = rnd.random() < 0.3
        alvo_monstro = rnd.random() < 0.7
        tp = (rnd.randint(4, 8), rnd.randint(4, 8))
        if alvo_monstro:
            alvo = mon(r, f"t{i}", tp, facing=f, size=(2, 2) if grande else (1, 1))
            if rnd.random() < 0.15: alvo["dormindo"] = True; alvo["dormindo_rodadas"] = 2
        else:
            alvo = hero(r, f"ht{i}", tp, facing=f)
        ap = (rnd.randint(0, 12), rnd.randint(0, 12))
        if rnd.random() < 0.5:
            atac = hero(r, f"ha{i}", ap)
        else:
            atac = mon(r, f"ma{i}", ap, size=(2, 2) if rnd.random() < 0.3 else (1, 1))
        if tuple(atac["pos"]) == tuple(alvo["pos"]): continue
        srv.append(r._setor_ataque(atac, alvo))
        casos.append([atac, alvo])
    script = (
        'const fs=require("fs");global.WebSocket=class{send(){}close(){}};global.window={};'
        'global.localStorage={getItem:()=>null,setItem(){},removeItem(){}};global.location={search:"",protocol:"http:",host:"x"};'
        'global.setTimeout=()=>0;global.clearTimeout=()=>{};'
        'const GS=eval(fs.readFileSync("src/gameState.js","utf8")+";GS");'
        'const c=JSON.parse(fs.readFileSync(0,"utf8"));'
        'console.log(JSON.stringify(c.map(([a,b])=>GS.setorAtaque({},a,b))));')
    out = subprocess.run(["node", "-e", script], input=json.dumps(casos), capture_output=True, text=True,
                         encoding="utf-8", cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cli = json.loads(out.stdout) if out.returncode == 0 else None
    check(f"{len(casos)} casos aleatórios: cliente = servidor", cli == srv)
    check("o conjunto tem frente, flanco e costas", {"frente", "flanco", "costas"} <= set(srv))

    print("\n[8] Helper de teste: virar_para tira o bônus de posição")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from posicao_util import virar_para
    r = setup()
    for pos in ((6, 5), (4, 5), (5, 4), (5, 6)):
        alvo = mon(r, "t", (5, 5)); atac = hero(r, "a", pos)
        f = virar_para(alvo, atac["pos"])
        check(f"virar_para {pos}: alvo olha {f} e o atacante fica de frente",
              r._setor_ataque(atac, alvo) == "frente" and r._bonus_posicional(atac, alvo)["total"] == 0)

    print(f"\nTotal: {PASS} ok, {FAIL} falhas")
    sys.exit(1 if FAIL else 0)


main()
