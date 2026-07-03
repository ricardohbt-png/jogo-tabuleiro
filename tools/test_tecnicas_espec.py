"""Técnicas da Guilda — Recarga Curta (Fase 2a). Roda: python tools/test_tecnicas_espec.py"""
import asyncio, sys, os
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

def setup(phase="playing"):
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg",""))
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = noop; r.push_state = noop; r.send_to = cap_send
    r.phase = phase; r._errs = errs; r.round_num = 1
    return r

def hero(cls="warrior", tid=None, **kw):
    p = make_player("h", "Heroi", cls, 0)
    p["pos"] = [0, 0]; p["alive"] = True
    p["fome"] = 20; p["sede"] = 20
    if tid:
        p["guild_owned"]["tecnicas"] = [tid]
        p["guild_equip"]["tecnica"] = tid
    for k, v in kw.items(): p[k] = v
    return p

async def main():
    # [1] Catálogo
    print("\n[1] Catálogo — Recarga Curta")
    for tid in ["tecnica_mira_perfeita","tecnica_espirito_indomavel","tecnica_grito_guerra","tecnica_pressa"]:
        it = S.guild_item(tid)
        check(f"existe {tid}", it is not None)
        check(f"{tid} recarga 3", it and it["recarga_rodadas"] == 3)
        check(f"{tid} preco 100", it and it["preco"] == 100)
        check(f"{tid} classe None", it and it["classe"] is None)
    check("pressa custa 4/4", S.guild_item("tecnica_pressa")["custo_fome"] == 4
          and S.guild_item("tecnica_pressa")["custo_sede"] == 4)
    check("mira custa 2/2", S.guild_item("tecnica_mira_perfeita")["custo_fome"] == 2)

    # [2] Pressa
    print("\n[2] Pressa")
    r = setup()
    p = hero("warrior", "tecnica_pressa"); r.players["h"] = p
    r.current_pid = lambda: "h"
    spd = p["spd"]; p["moves_left"] = spd; f0, s0 = p["fome"], p["sede"]
    await r.handle_usar_tecnica("h", "tecnica_pressa")
    check("pressa: +spd de movimento", p["moves_left"] == spd + spd)
    check("pressa: custo 4/4", p["fome"] == f0 - 4 and p["sede"] == s0 - 4)
    check("pressa: recarga setada", r.tecnica_restante(p, "tecnica_pressa") > 0)

    # [3] Grito de Guerra
    print("\n[3] Grito de Guerra")
    r = setup(); r.current_pid = lambda: "h"
    p = hero("warrior", "tecnica_grito_guerra"); r.players["h"] = p
    ally = make_player("a", "Ana", "cleric", 1); ally["alive"] = True; ally["pos"] = [1,1]
    ally["moves_left"] = ally["spd"]; r.players["a"] = ally
    p["moves_left"] = p["spd"]
    await r.handle_usar_tecnica("h", "tecnica_grito_guerra")
    check("grito: usuário +2 movimento", p["moves_left"] == p["spd"] + 2)
    check("grito: aliado +2 movimento", ally["moves_left"] == ally["spd"] + 2)
    check("grito: buff transitório setado", p["mov_bonus_ate"] == r.round_num + 1)
    # O buff DEVE fluir pelo cálculo autoritativo de movimento (_moves_base),
    # que é o que roda no reset de início de turno (senão o buff é descartado).
    check("grito: _moves_base do aliado inclui +2", r._moves_base(ally) == ally["spd"] + 2)
    check("grito: _grito_mov_bonus = 2 na janela", r._grito_mov_bonus(ally) == 2)
    # mov_bonus_ate = round_num+1 → cobre a rodada seguinte (o turno do aliado nela)
    r.round_num += 1
    check("grito: ainda ativo na rodada seguinte (o 'por 1 rodada')", r._grito_mov_bonus(ally) == 2)
    r.round_num += 1   # 2 rodadas após ativar → expira
    check("grito: expira 2 rodadas após ativar", r._grito_mov_bonus(ally) == 0)
    check("grito: _moves_base volta ao spd após expirar", r._moves_base(ally) == ally["spd"])

    # [4] Espírito Indomável
    print("\n[4] Espírito Indomável")
    r = setup(); r.current_pid = lambda: "h"
    p = hero("warrior", "tecnica_espirito_indomavel"); r.players["h"] = p
    p["com_medo"] = True; p["medo_rodadas"] = 3; p["perde_turno"] = True; p["lentidao"] = True
    await r.handle_usar_tecnica("h", "tecnica_espirito_indomavel")
    check("indomável: remove medo", not p.get("com_medo"))
    check("indomável: remove atordoamento", not p.get("perde_turno"))
    check("indomável: remove lentidão", not p.get("lentidao"))
    check("indomável: imunidade a silêncio setada", p["imune_silencio_ate"] == r.round_num + 1)
    # _em_silencio respeita a imunidade mesmo dentro de zona
    r._zonas_ativas = lambda tipo: [{"cx":0,"cy":0,"raio":3}] if tipo == "silencio" else []
    r._em_zona_quadrada = lambda x,y,z: True
    check("indomável: imune a silêncio ativo", r._em_silencio(p) is False)

    print(f"\n{'='*40}\nPASS={PASS} FAIL={FAIL}\n{'='*40}")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
