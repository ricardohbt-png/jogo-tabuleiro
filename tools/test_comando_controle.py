"""Comando / Dominar Mente: a janela de controle nao pode parecer travamento.

A magia Comando entrega ao conjurador o controle do monstro no PROXIMO turno
dele. Enquanto essa janela esta aberta, quem lancou nao esta no proprio turno:
handle_magia e handle_end_turn recusam. A recusa costumava ser SILENCIOSA
(`if not self._is_turn(pid): return`), entao o jogador via a ficha sumir e nada
responder -- reportado como "o sistema travou".

Roda da raiz: python tools/test_comando_controle.py
"""
import asyncio, os, sys

try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, make_monster, MONSTER_DEFS

OK = FAIL = 0
def check(rotulo, cond, extra=""):
    global OK, FAIL
    if cond: OK += 1; print("  OK  ", rotulo)
    else:    FAIL += 1; print("  XX  ", rotulo, extra)

async def noop(*a, **k): pass

def montar():
    r = GameRoom("COMANDO")
    r.phase = "playing"
    r.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    r.rooms = [{"id":"r0","x":0,"y":0,"w":12,"h":12,"cx":6,"cy":6,"locked":False}]
    r.door_rooms = {}; r.zonas_especiais = []; r.armadilhas = []
    r.erros = {}
    async def snd(pid, m, *a, **k):
        if isinstance(m, dict) and m.get("type") == "error":
            r.erros.setdefault(pid, []).append(str(m.get("msg")))
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = snd
    p = make_player("p1", "Pedro", "mage", 0)
    p["pos"] = [5, 5]; p["alive"] = True; p["connected"] = True
    p["hp"] = 30; p["fome"] = 20; p["sede"] = 20
    p["magias_conhecidas"] = list(S.GRIMORIO_IMPLEMENTADAS)
    p["slots_por_circulo"] = {"primeiro": 9, "segundo": 9, "terceiro": 9}
    q = make_player("p2", "Outro", "warrior", 1)
    q["pos"] = [1, 1]; q["alive"] = True; q["connected"] = True
    r.players = {"p1": p, "p2": q}; r.player_order = ["p1", "p2"]
    # Alvo tem de ser encantável: mortos-vivos são IMUNES a encantamento, e o
    # Comando nem chega a abrir a janela contra eles. O primeiro item de
    # MONSTER_DEFS é o esqueleto, então a escolha aqui é explícita.
    alvo_def = next(d for d in MONSTER_DEFS
                    if not d.get("undead") and not d.get("construct"))
    m = make_monster(alvo_def, {"id":"r0","cx":6,"cy":5})
    m["id"] = "m1"; m["pos"] = [6, 5]; m["hp"] = 20; m["room_id"] = "r0"; m["alertado"] = True
    r.monsters = {"m1": m}
    r.initiative_active = True
    r._rebuild_initiative()
    r.initiative_index = next(i for i,e in enumerate(r.initiative_order) if e["kind"]=="player" and e["id"]=="p1")
    return r, p, q, m

async def abrir_janela(r, p, m):
    """Lanca Comando (save falha) e passa a vez ao monstro."""
    async def save_falha(*a, **k): return (False, 1, 0, 1)
    r._save_mostrado = save_falha
    r._testar_save = lambda *a, **k: (False, 1, 0, 1)
    p["action_done"] = False
    await r.handle_magia("p1", {"magia_id": "comando", "target_id": "m1"})
    await r.handle_end_turn("p1")
    await asyncio.sleep(0.2)

async def main():
    print("[1] a janela de Comando abre e tira o jogador do proprio turno")
    r, p, q, m = montar()
    await abrir_janela(r, p, m)
    check("o jogador controla o monstro", r.command_control_mid == "m1" and r.command_control_pid == "p1")
    check("nao e mais o turno dele", r._is_turn("p1") is False)

    print()
    print("[2] as recusas TEM de explicar o motivo (nao podem ser silenciosas)")
    r.erros.clear()
    p["action_done"] = False
    await r.handle_magia("p1", {"magia_id": "barreira_arcana"})
    msgs = r.erros.get("p1", [])
    check("lancar magia responde alguma coisa", bool(msgs), "(silencio)")
    check("a resposta cita o controle do monstro",
          any("control" in s.lower() for s in msgs), f"({msgs})")
    r.erros.clear()
    await r.handle_end_turn("p1")
    msgs = r.erros.get("p1", [])
    check("encerrar turno responde alguma coisa", bool(msgs), "(silencio)")
    check("a resposta cita o controle do monstro",
          any("control" in s.lower() for s in msgs), f"({msgs})")

    print()
    print("[3] quem NAO controla nada continua sem receber aviso alheio")
    r.erros.clear()
    await r.handle_end_turn("p2")          # p2 so nao esta no turno dele
    check("outro jogador nao recebe o aviso de controle",
          not any("control" in s.lower() for s in r.erros.get("p2", [])),
          f"({r.erros.get('p2')})")

    print()
    print("[4] encerrar a vez do monstro devolve o turno")
    await r.handle_mestre_encerrar_monstro("p1", "m1")
    await asyncio.sleep(0.2)
    check("a janela fechou", r.command_control_mid is None)
    # A vez segue a iniciativa: com dois herois ela vai para o PROXIMO ator,
    # nao de volta a p1. O que importa e que a janela nao bloqueia mais.
    check("a iniciativa voltou a andar", r.current_actor() is not None)
    r.initiative_index = next(i for i, e in enumerate(r.initiative_order)
                              if e["kind"] == "player" and e["id"] == "p1")
    check("no turno dele, o jogador age de novo", r._is_turn("p1") is True)
    r.erros.clear()
    p["action_done"] = False
    await r.handle_magia("p1", {"magia_id": "barreira_arcana"})
    check("volta a lancar magia", p.get("barreira_arcana_rodadas", 0) > 0,
          f"({r.erros.get('p1')})")

    print()
    print("[5] as OUTRAS acoes de turno tambem tem de explicar, nao so magia")
    # Quem esta confuso clica primeiro em mover e atacar. Se esses seguirem
    # mudos, o aviso do [2] nao adianta: sao 34 handlers com a mesma guarda.
    r2, p2_, q2, m2 = montar()
    await abrir_janela(r2, p2_, m2)
    casos = [
        ("mover",        r2.handle_move("p1", 1, 0)),
        ("atacar",       r2.handle_attack("p1", "m1")),
        ("abrir porta",  r2.handle_open_door("p1", 6, 5)),
        ("usar item",    r2.handle_use_item("p1", "health_potion")),
    ]
    for rotulo, coro in casos:
        r2.erros.clear()
        await coro
        msgs = r2.erros.get("p1", [])
        check(f"{rotulo}: explica em vez de silenciar",
              any("control" in s.lower() for s in msgs), f"({msgs})")

    print()
    print(f"===== {OK} OK / {FAIL} FALHAS =====")
    return 1 if FAIL else 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
