"""Prévia 3D do editor. Roda da raiz: python tools/test_preview_editor.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK   {name}")
    else:    FAIL += 1; print(f"  FALHA {name}")

def dungeon_min():
    """Masmorra 6x5 válida: 1 sala, 1 monstro, 1 decoração sem image própria."""
    tiles = [[S.FLOOR] * 6 for _ in range(5)]
    for x in range(6):
        tiles[0][x] = S.WALL; tiles[4][x] = S.WALL
    for y in range(5):
        tiles[y][0] = S.WALL; tiles[y][5] = S.WALL
    return {
        "schema_version": 1, "id": "prev", "name": "Prévia",
        "grid": {"w": 6, "h": 5}, "tiles": tiles,
        "entrance": {"x": 1, "y": 1},
        "rooms": [{"id": "r1", "x": 1, "y": 1, "w": 4, "h": 3,
                   "role": "entrance", "doors": []}],
        "monsters": [{"type": "goblin", "pos": [3, 2], "room_id": "r1"}],
        "decorations": [{"type": "barril", "pos": [2, 2], "facing": [0, 1]}],
        "chests": [], "traps": [],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }


async def main():
    print("\n[1] _game_state_payload é equivalente ao dict que push_state envia")
    r = GameRoom("PREV")
    r.phase = "playing"
    r.load_authored_dungeon(dungeon_min())
    enviados = []
    async def cap(msg, *a, **k): enviados.append(msg)
    r.broadcast = cap
    await r.push_state()
    check("push_state enviou um game_state",
          len(enviados) == 1 and enviados[0].get("type") == "game_state")
    check("payload direto é igual ao enviado", r._game_state_payload() == enviados[0])

    print("\n[2] prévia monta o estado a partir da masmorra do editor")
    ok, st, avisos = S._preview_dungeon_state(dungeon_min())
    check("ok", ok is True)
    check("sem avisos", avisos == [])
    check("tipo game_state", st["type"] == "game_state")
    check("sem heróis", st["players"] == [])
    check("sem turno", st["current_turn"] is None)
    check("master_pid preenchido", st["master_pid"] == S.PREVIEW_PID)
    check("mapa todo explorado", len(st["explored"]) == 6 * 5)
    check("1 monstro", len(st["monsters"]) == 1 and st["monsters"][0]["type"] == "goblin")
    dec = st["decorations"][0]
    check("decoração com image do DECOR_TYPES",
          dec.get("image") == S.DECOR_TYPES["barril"].get("image"))

    print("\n[3] masmorra incompleta gera aviso, não erro")
    d = dungeon_min(); d.pop("entrance")
    ok, st, avisos = S._preview_dungeon_state(d)
    check("ainda monta", ok is True)
    check("avisou da entrada", any("entrada" in a.lower() for a in avisos))
    check("entrada suprida", st["stairs_pos"] is not None)

    print("\n[2b] resumo conta o que a prévia realmente montou")
    ok, st, avisos = S._preview_dungeon_state(dungeon_min())
    r = st["preview_resumo"]
    check("1 monstro no resumo", r["monstros"] == 1)
    check("1 objeto no resumo", r["objetos"] == 1)
    check("resumo bate com o payload",
          r["objetos"] == len(st["decorations"]) and r["monstros"] == len(st["monsters"]))

    print("\n[3c] decoração de tipo desconhecido some — e a prévia avisa")
    d = dungeon_min()
    d["decorations"] = [{"type": "nao_existe", "pos": [2, 2], "facing": [0, 1]}]
    ok, st, avisos = S._preview_dungeon_state(d)
    check("ainda monta", ok is True)
    check("decoração sumiu do payload", st["decorations"] == [])
    check("avisou do tipo", any("nao_existe" in a for a in avisos))
    check("resumo reflete a perda", st["preview_resumo"]["objetos"] == 0)

    print("\n[3b] monstro de tipo desconhecido é descartado com aviso")
    d = dungeon_min()
    d["monsters"] = [{"type": "nao_existe", "pos": [3, 2], "room_id": "r1"}]
    ok, st, avisos = S._preview_dungeon_state(d)
    check("ainda monta", ok is True)
    check("sem monstros", st["monsters"] == [])
    check("avisou do tipo", any("nao_existe" in a for a in avisos))

    print("\n[4] masmorra irrecuperável devolve erro")
    ok, res, avisos = S._preview_dungeon_state({"schema_version": 1})
    check("não ok", ok is False)
    check("erro é texto", isinstance(res, str) and bool(res))

    print("\n[4b] resposta estática declara que a conexão fecha")
    # A lib websockets fecha a conexão depois de responder. Sem "Connection: close"
    # o navegador supõe keep-alive, reusa o socket e a requisição seguinte morre na
    # rede — o que derrubava os .glb pedidos sob demanda (ProgressEvent status 0).
    resp = S._http(200, "OK", b"x", "model/gltf-binary")
    check("Connection: close presente",
          resp.headers.get("Connection", "").lower() == "close")
    check("Content-Length continua correto", resp.headers.get("Content-Length") == "1")

    print("\n[5] a prévia não deixa rastro numa sala real")
    check("nenhuma sala criada", "PREVIEW" not in S.rooms)

    print(f"\n{'=' * 46}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 46}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
