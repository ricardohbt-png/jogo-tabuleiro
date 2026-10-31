"""Servos animados (mortos-vivos e elementais) disparam armadilhas e distraem monstros.

Roda da raiz:  python -X utf8 tools/test_servo_armadilha.py

Antes, o movimento do servo não consultava as armadilhas: ele passava por cima de
uma mina sem nada acontecer, então não servia de sacrifício para limpar o caminho.
"""
import asyncio, os, random, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
from test_atravessar_aliados import montar, servo

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


def armar(r, tipo, pos):
    arm = {"id": f"arm_{tipo}", "tipo": tipo, "pos": list(pos), "criador": None,
           "visivel": False, "ativada": False, "efeitos_ativos": []}
    r.armadilhas.append(arm)
    return arm


async def cena(tipo):
    r = await montar(classe="mage")
    r.animados_phase_pid = "p1"
    a = servo(r, "p1", [2, 1], vida_atual=30, vida_max=30)
    armar(r, tipo, [3, 1])
    return r, a


def monstro(r, tipo, pos):
    d = next(x for x in S.MONSTER_DEFS if x["type"] == tipo)
    m = S.make_monster(d, {"id": 0, "cx": pos[0], "cy": pos[1]})
    m["pos"] = list(pos)
    m["alertado"] = True
    r.monsters[m["id"]] = m
    return m


async def secao_passo_manual():
    print("\n[1] Servo movido à mão dispara a armadilha em que pisa")
    random.seed(3)
    r, a = await cena("armadilha_urso")
    await r.handle_mover_animado("p1", "a1", 1, 0)
    check("servo chegou à casa da armadilha", a["pos"] == [3, 1], a["pos"])
    check("armadilha de urso consumida", not r.armadilhas, r.armadilhas)
    check("servo perdeu o movimento restante", a["moves_left"] == 0, a["moves_left"])


async def secao_caminho_para():
    print("\n[2] Um caminho para na armadilha (o servo não atravessa a mina de graça)")
    random.seed(3)
    r, a = await cena("armadilha_urso")
    await r.handle_mover_animado_caminho("p1", "a1", [[1, 0], [1, 0]])
    check("caminho parou na casa da armadilha", a["pos"] == [3, 1], a["pos"])


async def secao_mina_area():
    print("\n[3] Mina (área) atinge o servo que a pisou")
    random.seed(1)
    r, a = await cena("mina_terrestre")
    await r.handle_mover_animado("p1", "a1", 1, 0)
    check("servo sofreu dano da explosão", a["vida_atual"] < 30, a["vida_atual"])
    check("mina consumida", not r.armadilhas, r.armadilhas)


async def secao_sacrificio():
    print("\n[4] Sacrifício: a armadilha que mata o servo some do caminho do herói")
    random.seed(1)
    r, a = await cena("mina_terrestre")
    a["vida_atual"] = 1
    await r.handle_mover_animado("p1", "a1", 1, 0)
    check("servo destruído", a["vida_atual"] <= 0, a["vida_atual"])
    check("mina não está mais lá", not r._armadilha_no_tile(3, 1))


async def secao_comandar():
    print("\n[5] 'Comandar todos' também dispara a armadilha no caminho")
    random.seed(3)
    r, a = await cena("armadilha_urso")
    a["pos"] = [1, 1]
    monstro(r, "goblin", [5, 1])
    await r.handle_comandar_animados("p1")
    check("armadilha disparada no caminho", not r.armadilhas, r.armadilhas)
    check("servo parou na armadilha", a["pos"] == [3, 1], a["pos"])


async def secao_rede():
    print("\n[6] Rede: o servo perde a próxima janela de ação")
    random.seed(3)
    r, a = await cena("rede")
    await r.handle_mover_animado("p1", "a1", 1, 0)
    check("rede marcou perda de turno", a.get("perde_turno"), a)
    r.animados_phase_pid = None
    async def nada(*x, **k): pass
    r._advance_initiative = nada
    await r.handle_end_turn("p1")
    check("janela dos servos aberta", r.animados_phase_pid == "p1", r.animados_phase_pid)
    check("servo sem movimento", a["moves_left"] == 0, a["moves_left"])
    check("servo sem ação", a.get("acted") is True, a.get("acted"))
    check("flag consumida", not a.get("perde_turno"), a)


async def secao_distracao():
    print("\n[7] Distração: o monstro ataca o servo mais próximo, não o herói distante")
    random.seed(2)
    r = await montar(classe="mage")
    r.players["p1"]["pos"] = [0, 0]
    hp_heroi = r.players["p1"]["hp"]
    a = servo(r, "p1", [3, 1], vida_atual=50, vida_max=50, ac=5)
    m = monstro(r, "goblin", [4, 1])
    m["atk_bonus"] = 30
    for at in m.get("attacks") or []:
        at["atk_bonus"] = 30
    await r.gm_phase(m)
    check("servo atacado", a["vida_atual"] < 50, a["vida_atual"])
    check("herói intocado", r.players["p1"]["hp"] == hp_heroi)


async def main():
    for s in (secao_passo_manual, secao_caminho_para, secao_mina_area, secao_sacrificio,
              secao_comandar, secao_rede, secao_distracao):
        await s()
    print(f"\n{PASS} ok, {FAIL} falha(s)")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
