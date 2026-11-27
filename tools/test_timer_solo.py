"""Limite de tempo por turno: desligado no jogo Solo novo, ligado no Multiplayer.

Roda da raiz: python -X utf8 tools/test_timer_solo.py
"""
import os
import shutil
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S  # noqa: E402

FALHAS = []


def check(nome, cond):
    print(("  ✅ " if cond else "  ❌ ") + nome)
    if not cond:
        FALHAS.append(nome)


def main():
    tmp = tempfile.mkdtemp()
    antiga = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp))
    S.LOJA.carregar()
    try:
        print("\n[1] Ao criar o jogo")
        solo = S.create_savegame("Solo", "ana", "procedural", None, False, play_mode="solo")
        check("Solo nasce com o limite desligado", solo.get("turn_timer_enabled") is False)
        multi = S.create_savegame("Multi", "ana", "procedural", None, False, play_mode="multiplayer")
        check("Multiplayer nasce com o limite ligado", multi.get("turn_timer_enabled") is True)
        mestre = S.create_savegame("Mestre", "ana", "procedural", None, True, play_mode="solo")
        check("com Mestre (sempre multiplayer) nasce ligado", mestre.get("turn_timer_enabled") is True)
        sem_modo = S.create_savegame("Antigo", "ana", "procedural", None, False)
        check("sem modo informado (cliente antigo) segue ligado, como antes",
              sem_modo.get("turn_timer_enabled") is True)

        print("\n[2] Continuação herda a escolha do jogo de origem")
        origem = dict(solo, turn_timer_enabled=True)
        cont = S.create_savegame("Cont", "ana", "procedural", None, False, play_mode="solo", inherited=origem)
        check("Solo que o jogador ligou continua ligado na continuação", cont.get("turn_timer_enabled") is True)

        print("\n[3] Ao abrir o jogo, a sala usa o valor salvo")
        rooms = {}
        sala, erro = S.try_open_savegame_room("ana", solo["id"], rooms)
        check(f"o Solo abre ({erro or 'ok'})", sala is not None)
        check("a sala do Solo abre com o limite desligado", sala is not None and sala.turn_timer_enabled is False)
        if sala is not None:
            S.SAVEGAMES_IN_USE.pop(solo["id"], None)
        sala, erro = S.try_open_savegame_room("ana", multi["id"], rooms)
        check("a sala do Multiplayer abre com o limite ligado", sala is not None and sala.turn_timer_enabled is True)
        if sala is not None:
            S.SAVEGAMES_IN_USE.pop(multi["id"], None)
        velho = S.load_savegame(sem_modo["id"])
        velho.pop("turn_timer_enabled", None)
        S.write_savegame(velho)
        sala, erro = S.try_open_savegame_room("ana", sem_modo["id"], rooms)
        check("jogo salvo antigo, sem o campo, continua ligado", sala is not None and sala.turn_timer_enabled is True)
    finally:
        S.LOJA = antiga
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\nFalhas: {len(FALHAS)}")
    sys.exit(1 if FALHAS else 0)


main()
