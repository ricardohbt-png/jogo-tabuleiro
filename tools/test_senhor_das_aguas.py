"""Senhor das Águas (3º círculo, clérigo). Roda da raiz:
python tools/test_senhor_das_aguas.py

Cobre a COTA ACUMULADA dos redemoinhos: a janela abre na segunda rodada da
magia e fica aberta até a magia acabar. O clérigo marca casas em qualquer
rodada dessa janela até somar `nível ÷ 2` no total — não é um disparo único.
"""
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

def setup(lado=10):
    r = GameRoom("TEST"); errs = []; log = []
    async def noop(*a, **k): pass
    async def say(msg, *a, **k): log.append(str(msg))
    async def cap(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(str(msg.get("msg", "")))
    r.gm_say = say; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = noop; r.push_state = noop; r.send_to = cap
    r._tem_linha_de_visao = lambda *a, **k: True
    r._alcance_com_altura  = lambda *a, **k: True
    r.phase = "playing"; r._errs = errs; r._log = log
    r.map_w = r.map_h = lado
    r.tiles = [[S.FLOOR] * lado for _ in range(lado)]
    r.explored = {(x, y) for y in range(lado) for x in range(lado)}
    return r

def lewis(r, nivel=6, pos=(4, 4)):
    p = make_player("c", "Lewis", "cleric", 0)
    p.update(pos=list(pos), level=nivel, alive=True, fome=40, sede=40)
    p["magias_conhecidas"] = ["senhor_das_aguas"]
    r.players["c"] = p; r.player_order = ["c"]
    # Caminho REAL do jogo: a rodada vira em _advance_initiative (o fallback
    # sem iniciativa de handle_end_turn foi removido).
    r.initiative_active = True
    r._rebuild_initiative()
    return p

async def conjurar(r, terreno="agua", tx=4, ty=4):
    await r.handle_magia("c", {"magia_id": "senhor_das_aguas",
                               "terreno": terreno, "tx": tx, "ty": ty})
    return r._senhor_das_aguas_zona_ativa("c")

async def criar(r, tiles):
    r._errs.clear()
    await r.handle_senhor_das_aguas_rodamoinhos("c", tiles)
    return list(r._errs)

async def main():
    print("\n[1] Conjuração abre a janela para a rodada seguinte")
    r = setup(); lewis(r, nivel=6)
    z = await conjurar(r)
    check("zona criada", bool(z))
    check("disponível só na rodada seguinte", z["disponivel_em"] == r.round_num + 1)
    check("cota = nível ÷ 2 (6 → 3)", z["redemoinho_max"] == 3)
    check("nenhum redemoinho ainda", z["redemoinhos"] == [])

    print("\n[2] Na rodada da conjuração ainda não dá")
    errs = await criar(r, [[4, 4]])
    check("recusa na 1ª rodada", any("segunda rodada" in e for e in errs))
    check("nada foi criado", z["redemoinhos"] == [])

    print("\n[3] A cota é gasta aos poucos, em rodadas diferentes")
    await r.handle_end_turn("c"); await asyncio.sleep(0)
    check("virou a rodada", r.round_num == 2)
    check("1ª marcação aceita", await criar(r, [[4, 4]]) == [])
    check("gastou 1 da cota", len(z["redemoinhos"]) == 1)
    check("terreno virou rodamoinho", r.materiais.get((4, 4)) == "rodamoinho")

    await r.handle_end_turn("c"); await asyncio.sleep(0)
    check("rodada 3", r.round_num == 3)
    # ESTE é o coração da mudança: a janela continua aberta.
    check("2ª marcação, noutra rodada, aceita", await criar(r, [[3, 3]]) == [])
    check("cota acumulou (2 de 3)", len(z["redemoinhos"]) == 2)
    check("as duas casas persistem",
          r.materiais.get((4, 4)) == "rodamoinho" and r.materiais.get((3, 3)) == "rodamoinho")

    print("\n[4] A cota é um teto total, não por rodada")
    await r.handle_end_turn("c"); await asyncio.sleep(0)
    errs = await criar(r, [[5, 5], [5, 6]])       # só resta 1
    check("recusa quando pede mais que o restante", errs != [])
    check("nada parcial foi aplicado", len(z["redemoinhos"]) == 2)
    check("3ª marcação (a última) aceita", await criar(r, [[5, 5]]) == [])
    check("cota cheia (3 de 3)", len(z["redemoinhos"]) == 3)

    print("\n[5] Esgotada a cota, a janela fecha")
    await r.handle_end_turn("c"); await asyncio.sleep(0)
    errs = await criar(r, [[6, 6]])
    check("recusa com a cota cheia", errs != [])
    check("continua com 3", len(z["redemoinhos"]) == 3)
    check("a casa recusada não virou rodamoinho", r.materiais.get((6, 6)) != "rodamoinho")

    print("\n[6] Casa já marcada não consome cota de novo")
    r = setup(); lewis(r, nivel=6); z = await conjurar(r)
    await r.handle_end_turn("c"); await asyncio.sleep(0)
    await criar(r, [[4, 4]])
    errs = await criar(r, [[4, 4]])
    check("repetir a mesma casa é recusado", errs != [])
    check("cota intacta (1)", len(z["redemoinhos"]) == 1)

    print("\n[7] Fora da área continua fora")
    errs = await criar(r, [[0, 0]])
    check("casa fora da área recusada", errs != [])
    check("cota intacta", len(z["redemoinhos"]) == 1)

    print("\n[8] Água profunda gera redemoinho profundo")
    r = setup(); lewis(r, nivel=6); z = await conjurar(r, terreno="agua_profunda")
    await r.handle_end_turn("c"); await asyncio.sleep(0)
    check("marcação aceita", await criar(r, [[4, 4]]) == [])
    check("virou rodamoinho_profundo", r.materiais.get((4, 4)) == "rodamoinho_profundo")

    print("\n[9] O cliente recebe a cota e o que já foi gasto")
    pay = r._game_state_payload()
    zc = next((x for x in pay["zonas_especiais"] if x.get("tipo") == "senhor_das_aguas"), None)
    check("zona no payload", bool(zc))
    check("payload traz redemoinho_max", zc and "redemoinho_max" in zc)
    check("payload traz a lista de redemoinhos", zc and zc.get("redemoinhos") == [[4, 4]])

    print("\n" + "=" * 62)
    print("\n[R1] Quem estava preso é liberado quando a água some (expiração)")
    # Nenhum hook de início de turno conferia se a criatura AINDA está numa
    # casa de redemoinho: com a zona expirada e o chão seco, a vítima seguia
    # presa, perdia movimento/ação, afogava (1d6) e pagava 🍖/💧 por turno.
    async def falha(*a, **k):
        return (False, 1, 0, 0)
    for terreno, flag in (("agua", "rodamoinho_preso"), ("agua_profunda", "rodamoinho_profundo_preso")):
        r = setup(14); lewis(r, nivel=5, pos=(1, 1))
        w = make_player("w", "Ana", "warrior", 1)
        w.update(level=1, pos=[6, 6], alive=True, hp=60, max_hp=60, moves_left=4, fome=30, sede=30)
        r.players["w"] = w
        z = await conjurar(r, terreno, 6, 6)
        r._save_mostrado = falha
        r.round_num = z["disponivel_em"]
        await criar(r, [[6, 6]])
        check(f"{terreno}: Ana presa pelo redemoinho", w.get(flag) is True)
        r.round_num = z["expira_em"]
        await r._processar_zonas_turno()
        check(f"{terreno}: água sumiu", r.materiais.get((6, 6)) is None)
        check(f"{terreno}: liberada já na expiração", not w.get(flag))
        w["moves_left"] = 4; w["action_done"] = False; hp, fome = w["hp"], w["fome"]
        if terreno == "agua":
            ok = await r._testar_rodamoinho_inicio_turno(w)
        else:
            ok = await r._testar_rodamoinho_profundo_inicio_turno(w)
        check(f"{terreno}: no turno seguinte age normalmente", ok is True and w["moves_left"] == 4 and not w["action_done"])
        check(f"{terreno}: sem afogamento nem 🍖/💧 em chão seco", w["hp"] == hp and w["fome"] == fome)

    print("\n[R2] Liberação também ao ser arrastado/teleportado para fora e no cancelamento")
    r = setup(14); lewis(r, nivel=5, pos=(1, 1))
    r.players["c"]["magias_conhecidas"].append("ira_rocha_ardente")
    w = make_player("w", "Ana", "warrior", 1)
    w.update(level=1, pos=[6, 6], alive=True, hp=60, max_hp=60, moves_left=4, fome=30, sede=30)
    r.players["w"] = w
    z = await conjurar(r, "agua_profunda", 6, 6)
    r._save_mostrado = falha
    r.round_num = z["disponivel_em"]
    await criar(r, [[6, 6]])
    w["pos"] = [0, 0]                       # empurrada/teleportada para fora, zona ainda ativa
    w["moves_left"] = 4; w["action_done"] = False; hp = w["hp"]
    ok = await r._testar_rodamoinho_profundo_inicio_turno(w)
    check("fora da casa do redemoinho: o teste de turno libera sem afogar", ok is True and not w.get("rodamoinho_profundo_preso") and w["hp"] == hp)
    w["pos"] = [6, 6]; w.pop("_rodamoinho_profundo_ultima_pos", None)
    await r._aplicar_rodamoinho_profundo_se_pisar(w)
    check("voltou e foi presa de novo", w.get("rodamoinho_profundo_preso") is True)
    r.players["c"]["action_done"] = False; r.round_num += 1
    await r.handle_magia("c", {"magia_id": "ira_rocha_ardente", "tx": 11, "ty": 11})   # cancela a água
    check("Ira cancelou a água", r.materiais.get((6, 6)) is None)
    check("cancelamento também libera", not w.get("rodamoinho_profundo_preso"))

    print("\n[R3] Mira inválida não cobra slot, 🍖/💧 nem ação (preflight)")
    # Só o `terreno` era validado antes do pagamento; alcance/parede/chão
    # ficavam no executor, depois de handle_magia cobrar tudo.
    r = setup(14); c = lewis(r, nivel=5, pos=(1, 1))
    del r._tem_linha_de_visao; del r._alcance_com_altura
    def recursos(p):
        return (r._slots_disponiveis(p, "terceiro"), p["fome"], p["sede"], p["action_done"])
    async def tenta(dados):
        r._errs.clear()
        await r.handle_magia("c", {"magia_id": "senhor_das_aguas", "terreno": "agua", **dados})
        return list(r._errs)
    antes = recursos(c)
    check("fora do alcance: erro", bool(await tenta({"tx": 13, "ty": 13})))     # dist 12 > 10
    check("fora do alcance: recursos intactos", recursos(c) == antes)
    for y in range(14):
        r.tiles[y][4] = S.WALL
    check("parede no caminho: erro", bool(await tenta({"tx": 8, "ty": 1})))
    check("parede no caminho: recursos intactos", recursos(c) == antes)
    r.tiles = [[S.WALL] * 14 for _ in range(14)]; r.tiles[1][1] = S.FLOOR
    check("sem chão na área: erro", bool(await tenta({"tx": 1, "ty": 3})))
    check("sem chão na área: recursos intactos", recursos(c) == antes)
    r.tiles = [[S.FLOOR] * 14 for _ in range(14)]
    check("mira válida: slot e ação gastos",
          not await tenta({"tx": 1, "ty": 6}) and recursos(c) != antes)

    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    return 1 if FAIL else 0

sys.exit(asyncio.run(main()))
