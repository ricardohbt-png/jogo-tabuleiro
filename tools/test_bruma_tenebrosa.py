"""Carregamento e serialização do preset Bruma tenebrosa.
Roda da raiz: python -X utf8 tools/test_bruma_tenebrosa.py
"""
import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from test_dungeon_loader import sample_dungeon, setup_room  # noqa: E402


async def main():
    room = setup_room()
    room.mode = "authored"
    room.dungeon_def = sample_dungeon()
    room.dungeon_def["ambiente"] = "bruma_tenebrosa"
    room.selected_dungeon = "bruma_tenebrosa.json"
    await room.enter_dungeon("p1")
    assert room.ambiente == "bruma_tenebrosa"
    assert room._game_state_payload()["ambiente"] == "bruma_tenebrosa"
    print("✅ carregador e game_state preservam bruma_tenebrosa")


if __name__ == "__main__":
    asyncio.run(main())
