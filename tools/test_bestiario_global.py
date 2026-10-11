"""Cobertura do bestiário persistente por conta (sem gravar dados reais)."""
import copy
import asyncio
import inspect
import os
import sys
from unittest.mock import AsyncMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  ✅ " + name)
    else:
        FAIL += 1
        print("  ❌ " + name)


def main():
    accounts = {
        "alpha": {"username": "alpha", "password_hash": "x", "profile": {
            "bestiary": {"orc": {"kills": 13}, "slime": {"kills": 29}, "skeleton": {"kills": 49}}}},
        "beta": {"username": "beta", "password_hash": "x", "profile": {"bestiary": {}}},
    }
    original_load, original_write = server.load_account, server.write_account
    server.load_account = lambda username: copy.deepcopy(accounts.get(username))
    server.write_account = lambda account: accounts.__setitem__(account["username"], copy.deepcopy(account))
    try:
        print("[1] marcos progressivos e persistência individual")
        r14 = server._bestiary_increment("alpha", "orc")
        r15 = server._bestiary_increment("alpha", "orc")
        r30 = server._bestiary_increment("alpha", "slime")
        r50 = server._bestiary_increment("alpha", "skeleton")
        check("14 abates não liberam marco", r14["kills"] == 14 and r14["milestone"] is None and r14["level"] == 0)
        check("15 libera nível 1", r15["kills"] == 15 and r15["milestone"] == 15 and r15["level"] == 1)
        check("30 libera nível 2", r30["milestone"] == 30 and r30["level"] == 2)
        check("50 libera nível 3", r50["milestone"] == 50 and r50["level"] == 3)
        check("progresso foi escrito no perfil da conta", accounts["alpha"]["profile"]["bestiary"]["orc"]["kills"] == 15)
        check("outra conta mantém progresso independente", accounts["beta"]["profile"]["bestiary"] == {})

        print("[2] payload do bestiário é isolado por jogador")
        room = server.GameRoom("BESTIARY")
        room.account_by_pid = {"p1": "alpha", "p2": "beta"}
        payload_alpha = room._bestiary_payload_for_pid("p1")
        payload_beta = room._bestiary_payload_for_pid("p2")
        check("alpha recebe somente o próprio perfil", payload_alpha.get("orc") == 15 and "skeleton" in payload_alpha)
        check("beta não recebe conhecimento de alpha", payload_beta == {})

        push_state_source = inspect.getsource(server.GameRoom.push_state)
        check("broadcast não inclui bestiário nem níveis", "bestiary_levels" not in push_state_source
              and '"bestiary"' not in push_state_source)
        check("inspeção privada de monstro tem handler dedicado",
              hasattr(server.GameRoom, "handle_inspect_monster"))

        print("[3] inspeção só retorna conhecimento ao solicitante visível")
        room = server.GameRoom("INSPECT")
        room.phase = "playing"
        room.players = {"p1": {"id": "p1", "pos": [1, 1], "spd": 5, "hp": 10,
                                "alive": True, "class_id": "fighter"}}
        room.monsters = {"orc1": {"id": "orc1", "type": "orc", "name": "Orc", "pos": [2, 1],
                                   "hp": 8, "size": [1, 1]}}
        room.account_by_pid = {"p1": "alpha"}
        room.savegame = {"members": {"alpha": {}}}
        room._em_cidade = lambda _pid: False
        room._get_raio_visao = lambda _player: 5
        room._tem_linha_de_visao = lambda _a, _b: True
        room.send_to = AsyncMock()
        asyncio.run(room.handle_inspect_monster("p1", "orc1"))
        private_result = room.send_to.await_args.args[1]
        check("resposta privada retorna só nível/autorização", private_result == {
            "type": "monster_knowledge_state", "monster_id": "orc1", "level": 1,
            "knowledge_source": "bestiary"})
        room.send_to.reset_mock()
        room._tem_linha_de_visao = lambda _a, _b: False
        asyncio.run(room.handle_inspect_monster("p1", "orc1"))
        check("monstro sem linha de visão não gera resposta", room.send_to.await_count == 0)

        print("[4] migração sanitiza contadores inválidos")
        legacy = {"username": "legacy", "password_hash": "x", "profile": {
            "bestiary": {"orc": {"kills": 4}, "bad id": {"kills": 7}, "rat": -1}}}
        server.ensure_account_profile(legacy)
        check("preserva entrada válida e descarta IDs/formas inválidas",
              legacy["profile"]["bestiary"] == {"orc": {"kills": 4}})
    finally:
        server.load_account, server.write_account = original_load, original_write
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    raise SystemExit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
