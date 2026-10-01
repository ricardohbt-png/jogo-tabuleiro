"""Visão compartilhada — lado do servidor.

Roda da raiz:  python tools/test_visao_compartilhada.py

O QUE ELE COBRA
  • a sala nasce com a visão compartilhada PERMITIDA e o campo vai no payload
    da masmorra e da cidade (é o que o cliente lê para habilitar a opção)
  • só o anfitrião troca a permissão; outro jogador é recusado
  • a permissão é gravada no jogo salvo e lida de volta ao abrir a sala
  • o prisioneiro resgatado enxerga como um servo (entra em `revealed`);
    o prisioneiro ainda preso, não
"""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


def sala():
    r = S.GameRoom("VISAO")
    enviados = []
    async def noop(*a, **k): pass
    async def send_to(pid, msg): enviados.append((pid, msg))
    r.broadcast = noop; r.push_state = noop; r.broadcast_city_state = noop
    r.send_to = send_to
    for pid, nome, cls in (("p1", "Ana", "warrior"), ("p2", "Bia", "mage")):
        r.players[pid] = S.make_player(pid, nome, cls, len(r.players))
    r.host_pid = "p1"
    return r, enviados


async def main():
    print("\n[1] Padrão e payloads")
    r, _ = sala()
    check("nasce permitida", r.visao_compartilhada_permitida is True)
    r.phase = "city"
    check("vai no city_state", r._city_state_payload().get("visao_compartilhada_permitida") is True)
    r.map_w = r.map_h = 5
    r.tiles = [[S.FLOOR] * 5 for _ in range(5)]
    r.phase = "playing"
    check("vai no game_state", r._game_state_payload().get("visao_compartilhada_permitida") is True)

    print("\n[2] Só o anfitrião troca")
    r, enviados = sala()
    await r.handle_set_visao_compartilhada("p2", False)
    check("não-anfitrião não muda nada", r.visao_compartilhada_permitida is True)
    check("e recebe um erro", any(m.get("type") == "error" for _, m in enviados))
    await r.handle_set_visao_compartilhada("p1", False)
    check("anfitrião bloqueia", r.visao_compartilhada_permitida is False)
    await r.handle_set_visao_compartilhada("p1", True)
    check("anfitrião volta a permitir", r.visao_compartilhada_permitida is True)

    print("\n[3] Jogo salvo")
    r, _ = sala()
    r.savegame = {"id": "teste"}
    gravados = []
    orig = S.write_savegame
    S.write_savegame = lambda sg: gravados.append(dict(sg))
    try:
        await r.handle_set_visao_compartilhada("p1", False)
    finally:
        S.write_savegame = orig
    check("a permissão foi gravada", bool(gravados) and gravados[-1].get("visao_compartilhada_permitida") is False,
          str(gravados[-1:])[:200])
    fonte = open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
    check("e é lida de volta ao abrir a sala",
          'room.visao_compartilhada_permitida = sg.get("visao_compartilhada_permitida", True) is not False' in fonte)
    check("o handler é despachado",
          'elif t == "set_visao_compartilhada"' in fonte and "handle_set_visao_compartilhada(pid" in fonte)

    print("\n[4] Prisioneiro resgatado enxerga como um servo")
    r, _ = sala()
    r.map_w = r.map_h = 9
    r.tiles = [[S.FLOOR] * 9 for _ in range(9)]
    r.prisoner = {"pos": [4, 4], "alive": True, "freed": False, "rescuer_pid": None}
    check("preso: não revela nada", (5, 5) not in r._live_reveal_tiles())
    r.prisoner["freed"] = True
    vis = r._live_reveal_tiles()
    check("resgatado: revela em volta", (5, 5) in vis and (6, 4) in vis)
    check("resgatado: respeita o raio dos servos", (7, 4) not in vis)
    r.prisoner["alive"] = False
    check("morto: deixa de revelar", (5, 5) not in r._live_reveal_tiles())


asyncio.run(main())
print(f"\n{'=' * 62}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 62}")
sys.exit(1 if FAIL else 0)
