"""Entrada autorada fora da sala de entrada: o herói começa vendo em volta.

No modo "entrance" o servidor revelava só a sala com role "entrance". Em mapas
cujo ponto de entrada fica fora dela (Adhadal 1 e 2, a Caçada de Corvin), o
herói nascia numa casa nunca explorada e o cliente, que só calcula alcance
sobre casas exploradas, não mostrava casas azuis nem deixava andar.

Rodar: python -X utf8 tools/test_entrada_fora_da_sala.py
"""
import asyncio, json, os, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
import server as S  # noqa: E402

falhas = []


def check(cond, msg):
    print(("  ok  " if cond else "  FALHOU  ") + msg)
    if not cond:
        falhas.append(msg)


async def nada(*a, **k):
    pass


async def entrar(arquivo):
    with open(os.path.join(S.DUNGEONS_DIR, arquivo), encoding="utf-8") as f:
        d = json.load(f)
    r = S.GameRoom("ENT")
    r.players["p0"] = S.make_player("p0", "W", "warrior", 0)
    r.players["p1"] = S.make_player("p1", "M", "mage", 1)
    r.host_pid = "p0"; r.phase = "city"; r.player_order = ["p0", "p1"]
    r.mode = "authored"; r.dungeon_def = d
    r.broadcast = nada; r.send_to = nada; r.gm_say = nada
    await r.enter_dungeon("p0")
    r._cancelar_intro_masmorra()
    return r, d


async def main():
    for arquivo in ("elara_adhadal_1.json", "elara_adhadal_2.json", "elara_corvin_cacada.json"):
        print(f"[{arquivo}]")
        r, d = await entrar(arquivo)
        for p in r.players.values():
            x, y = p["pos"]
            check((x, y) in r.explored, f"{p['name']} começa numa casa explorada {p['pos']}")
            vizinhas = [(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                        if 0 <= x + dx < r.map_w and 0 <= y + dy < r.map_h
                        and r.tiles[y + dy][x + dx] != S.WALL]
            check(any(v in r.explored for v in vizinhas),
                  f"{p['name']} tem casa vizinha explorada para andar")

    # Mapa comum (entrada dentro da sala): a revelação inicial não muda.
    print("[mapa com a entrada dentro da sala]")
    r, d = await entrar("campo_de_treinamento.json")
    sala = next(s for s in r.rooms if s["role"] == "entrance")
    fora = [c for c in r.explored
            if not (sala["x"] - 1 <= c[0] <= sala["x"] + sala["w"]
                    and sala["y"] - 1 <= c[1] <= sala["y"] + sala["h"])]
    check(not fora, "só a sala de entrada e sua borda ficam reveladas")


async def jogo_salvo_antigo():
    """Partida salva antes da correção: a foto guarda a névoa sobre o herói.
    Ao continuar, o jogo tem de revelar em volta dele."""
    print("[jogo salvo antes da correção, retomado]")
    r, d = await entrar("elara_adhadal_1.json")
    r.selected_dungeon = "elara_adhadal_1.json"
    sala = next(s for s in r.rooms if s["role"] == "entrance")
    r.explored = {c for c in r.explored
                  if sala["x"] - 1 <= c[0] <= sala["x"] + sala["w"]
                  and sala["y"] - 1 <= c[1] <= sala["y"] + sala["h"]}
    casas = {p["class_id"]: tuple(p["pos"]) for p in r.players.values()}
    check(all(c not in r.explored for c in casas.values()),
          "a foto antiga tem a névoa sobre os heróis")
    registro = S.foto_empacotar(r._montar_foto(), onde="masmorra", rodada=r.round_num,
                                masmorra="elara_adhadal_1.json", masmorra_nome="x")

    n = S.GameRoom("RET")
    n.players["q0"] = S.make_player("q0", "W", "warrior", 0)
    n.players["q1"] = S.make_player("q1", "M", "mage", 1)
    n.host_pid = "q0"; n.player_order = ["q0", "q1"]
    n.mode = "authored"; n.dungeon_def = d; n.selected_dungeon = "elara_adhadal_1.json"
    n.broadcast = nada; n.send_to = nada; n.gm_say = nada; n.push_state = nada
    ok = await n._retomar_masmorra(registro)
    n._cancelar_intro_masmorra()
    check(ok, "a retomada aceita a foto")
    for p in n.players.values():
        pos = tuple(p["pos"])
        check(pos == casas[p["class_id"]], f"{p['name']} volta à casa salva {list(pos)}")
        check(pos in n.explored, f"{p['name']} já não está na névoa ao continuar")


asyncio.run(main())
asyncio.run(jogo_salvo_antigo())
print("\nOK" if not falhas else f"\n{len(falhas)} falha(s)")
sys.exit(1 if falhas else 0)
