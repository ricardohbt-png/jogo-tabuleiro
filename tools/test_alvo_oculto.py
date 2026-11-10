"""Monstro escondido nas sombras não pode ser alvo direto de herói.

O servidor manda o monstro escondido (Assassino Goblin, Bandido) no
`game_state` e quem o esconde é o cliente, na hora de desenhar. Só o ataque
básico recusava o alvo; magia, arremesso, técnica, instrumento, Provocação e o
Vínculo do escudo espinhoso aceitavam o `target_id` dele. A trava agora fica no
despachante de mensagens (`_recusar_alvo_oculto`), que cobre toda ação de herói
que mira um monstro pelo id. Área atinge quem estiver nela, escondido ou não.
"""
import asyncio
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []


def check(cond, msg):
    print(("  ok   " if cond else "  FALHA ") + msg)
    if not cond:
        FALHAS.append(msg)


def sala():
    r = S.GameRoom("OCULTO")
    r.erros = []

    async def send_to(pid, msg, **k):
        if msg.get("type") == "error":
            r.erros.append(str(msg.get("msg")))
    r.send_to = send_to
    r.phase = "playing"
    p = S.make_player("p1", "Ana", "rogue", 0)
    p["pos"] = [1, 1]
    r.players["p1"] = p
    r.monsters["m1"] = {"id": "m1", "type": "goblin_assassino", "hp": 9, "pos": [3, 1],
                        "size": [1, 1], "invisivel_sombras": True}
    r.monsters["m2"] = {"id": "m2", "type": "goblin", "hp": 9, "pos": [4, 1], "size": [1, 1]}
    return r


async def main():
    print("[1] ações que miram o monstro escondido são recusadas")
    for tipo in ("magia", "throw_item", "usar_tecnica", "usar_instrumento", "provocacao",
                 "use_thorn_bond_shield", "improviso_alvo"):
        r = sala()
        recusou = await r._recusar_alvo_oculto("p1", {"type": tipo, "target_id": "m1"})
        check(recusou and r.erros, f"{tipo}: recusado com aviso")

    print("[2] o que não deve ser recusado")
    r = sala()
    check(not await r._recusar_alvo_oculto("p1", {"type": "magia", "target_id": "m2"}),
          "monstro visível segue sendo alvo")
    check(not await r._recusar_alvo_oculto("p1", {"type": "magia", "tx": 3, "ty": 1}),
          "magia de área na casa do escondido não é recusada (área atinge quem estiver lá)")
    r.monsters["m1"]["revealed_by_arcane_vigilance"] = True
    r._lampada_vigilia_arcana_revela_monstro = lambda m: True
    check(not await r._recusar_alvo_oculto("p1", {"type": "magia", "target_id": "m1"}),
          "revelado pela Lâmpada da Vigília Arcana vira alvo")
    r = sala()
    r.master_pid = "mestre"
    check(not await r._recusar_alvo_oculto("mestre", {"type": "mestre_set_alvo", "target_id": "m1"}),
          "o Mestre não é barrado")
    r = sala()
    r.phase = "city"
    check(not await r._recusar_alvo_oculto("p1", {"type": "magia", "target_id": "m1"}),
          "fora da masmorra não interfere")

    print("[3] o despachante chama a trava antes de despachar")
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py"),
               encoding="utf-8").read()
    check(re.search(r"await room\._recusar_alvo_oculto\(pid, msg\)", src) is not None,
          "handler chama room._recusar_alvo_oculto(pid, msg)")


asyncio.run(main())
print()
if FALHAS:
    print(f"{len(FALHAS)} falha(s)")
    sys.exit(1)
print("todos passaram")
