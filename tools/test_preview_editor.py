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

    print(f"\n{'=' * 46}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 46}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
