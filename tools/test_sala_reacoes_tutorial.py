"""Sala das Reações de Terreno (Campo de Treinamento): gás permanente, porta `gas`,
verbos de lição, frasco de socorro e criação do gás. Roda da raiz:
python -X utf8 tools/test_sala_reacoes_tutorial.py
Spec: docs/superpowers/specs/2026-10-16-sala-reacoes-terreno-design.md"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S  # noqa: E402

PASS = 0
FAIL = 0


def check(nome, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        print(f"  ❌ {nome}")


def roda(coro):
    return asyncio.run(coro)


def sala():
    """Duas salas de chão lado a lado (0: x1-10, 1: x11-20), 'playing', sem rede."""
    r = S.GameRoom("SRT")
    r.msgs = []
    r.narr = []
    r.saves = []
    r.dados = []

    async def noop(*a, **k):
        pass

    async def bc(msg, *a, **k):
        r.msgs.append(msg)

    async def say(txt, *a, **k):
        r.narr.append(str(txt))
    r.gm_say = say; r.broadcast = bc; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 13):
        for x in range(1, 21):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 10, "h": 12, "locked": False},
               {"id": 1, "x": 11, "y": 1, "w": 10, "h": 12, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    r.materiais = {}
    return r


def heroi(r, pid, nome, classe, pos, hp=60):
    h = S.make_player(pid, nome, classe, len(r.players))
    h["pos"] = list(pos)
    h["hp"] = h["max_hp"] = hp
    r.players[pid] = h
    r.player_order = list(r.players)
    return h


def camara(r, sala_id=0, duracao=4, **extra):
    z = {"id": f"camara_gas_t{sala_id}", "tipo": "camara_gas", "room_id": sala_id,
         "duracao": duracao, "ativa": True, "created_round": r.round_num}
    z.update(extra)
    r.zonas_especiais.append(z)
    return z


def fixa(r, dado=8, passa=False):
    """Dado fixo (registra a expressão pedida em r.dados) e save fixo."""
    def rolar(expr):
        r.dados.append(expr)
        return dado
    r._rolar_dado = rolar

    async def save(alvo, tipo, cd, *a, **k):
        r.saves.append((tipo, cd))
        return passa, 10, 0, 10
    r._save_mostrado = save


async def fogo_em(r, casas, caster="x", origem=None):
    async with r.evento_elemental(origem or {"tipo": "item", "id": "frasco_oleo", "caster_id": caster}):
        await r._rx_registrar(S.DMG_FIRE, casas, dano=1)


def secao_1():
    print("[1] gás permanente e dano de explosão por zona")
    r = sala()
    z = camara(r, duracao=2, permanente=True)
    for _ in range(5):
        roda(r._processar_zonas_turno_impl())
    check("zona permanente não dissipa em 5 rodadas", z["ativa"] is True)
    r = sala()
    z = camara(r, duracao=2)
    for _ in range(2):
        roda(r._processar_zonas_turno_impl())
    check("sem a marca a câmara ainda dissipa", z["ativa"] is False)
    r = sala()
    z = camara(r, permanente=True)
    n = camara(r, sala_id=1, permanente=True)
    n.update(id="nuvem_t", tipo="nuvem_gas", tiles=[[12, 3]])
    for _ in range(6):
        roda(r._processar_zonas_turno_impl())
    check("nuvem de gás permanente também não dissipa", n["ativa"] is True)
    r = sala()
    fixa(r, dado=3)
    heroi(r, "a", "Ana", "warrior", [3, 3])
    camara(r, dano_explosao="1d4")
    roda(fogo_em(r, [(3, 3)]))
    check("dano_explosao da zona é a expressão rolada", "1d4" in r.dados and "2d6" not in r.dados)
    r = sala()
    fixa(r, dado=3)
    heroi(r, "a", "Ana", "warrior", [3, 3])
    camara(r)
    roda(fogo_em(r, [(3, 3)]))
    check("sem o campo a explosão continua 2d6", "2d6" in r.dados)


def masmorra_porta(cond):
    """Masmorra 12x9: sala A (y1-4) | porta [5,5] | sala B (y6-7)."""
    W, H = 12, 9
    tiles = [[S.WALL] * W for _ in range(H)]
    for y in list(range(1, 5)) + [6, 7]:
        for x in range(1, 11):
            tiles[y][x] = S.FLOOR
    tiles[5][5] = S.DOOR
    d = {
        "schema_version": 1, "id": "porta_gas", "name": "Porta do gás",
        "grid": {"w": W, "h": H}, "tiles": tiles, "entrance": {"x": 2, "y": 2},
        "rooms": [{"id": "a", "x": 1, "y": 1, "w": 10, "h": 4, "role": "entrance", "doors": []},
                  {"id": "b", "x": 1, "y": 6, "w": 10, "h": 2, "role": "empty", "locked": True,
                   "doors": [[5, 5]]}],
        "monsters": [], "decorations": [], "chests": [], "traps": [],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }
    if cond is not None:
        d["door_conditions"] = {"5,5": cond}
    return d


def secao_2():
    print("[2] condição de porta `gas`")
    ok, _ = S.validar_dungeon(masmorra_porta({"type": "gas", "zona_id": "gas_tutorial"}))
    check("validar_dungeon aceita {type:gas, zona_id}", ok is True)
    ok, _ = S.validar_dungeon(masmorra_porta({"type": "gas", "zona_id": ""}))
    check("zona_id vazio é recusado", ok is False)
    ok, _ = S.validar_dungeon(masmorra_porta({"type": "gas"}))
    check("zona_id ausente é recusado", ok is False)
    r = S.GameRoom("PGAS")
    r.phase = "playing"
    r.load_authored_dungeon(masmorra_porta({"type": "gas", "zona_id": "gas_tutorial"}))
    check("sem a zona a porta já está satisfeita", r._door_condition_satisfied((5, 5)) is True)
    z = camara(r, sala_id="b", duracao=9, permanente=True)
    z["id"] = "gas_tutorial"
    check("zona ativa: porta NÃO satisfeita", r._door_condition_satisfied((5, 5)) is False)
    z["ativa"] = False
    check("zona consumida: porta satisfeita", r._door_condition_satisfied((5, 5)) is True)
    z["ativa"] = True
    pl = r._game_state_payload()["door_conditions"]["5,5"]
    check("payload leva type, satisfied e zona_id",
          pl["type"] == "gas" and pl["satisfied"] is False and pl["zona_id"] == "gas_tutorial")
    # abrir a porta com o gás ativo responde com a mensagem própria
    erros = []

    async def captura(pid, m):
        if m.get("type") == "error":
            erros.append(m["msg"])
    r.send_to = captura
    h = heroi(r, "a", "Ana", "warrior", [5, 4])
    r.player_order = ["a"]
    roda(r.handle_open_door("a", 5, 5))
    check("abrir com gás ativo recusa com erro.porta_exige_gas_consumido",
          len(erros) == 1 and getattr(erros[0], "key", None) == "erro.porta_exige_gas_consumido")
    check("a porta continua fechada", (5, 5) not in r.opened_doors)
    z["ativa"] = False
    roda(r.handle_open_door("a", 5, 5))
    check("com o gás consumido a porta abre", (5, 5) in r.opened_doors)

    # O editor descartava condições de tipo desconhecido ao abrir a masmorra: salvar o
    # Campo de Treinamento por ele apagaria a trava de gás. O editor não roda sem DOM,
    # então a prova é estática: leitura e escrita do tipo `gas` + chave de idioma.
    ed = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "editor.js"),
              encoding="utf-8").read()
    check("editor.js carrega a condição gas (loadJSON)",
          'c.type === "gas" && typeof c.zona_id === "string"' in ed)
    check("editor.js grava a condição gas (buildJSON)", 'c.type === "gas" ? { type: "gas", zona_id' in ed)
    check("chave de idioma do editor para gas existe",
          '"ui.editor.masmorra.painel.gas_consumido"' in S._LANG_TEXTO if hasattr(S, "_LANG_TEXTO") else
          '"ui.editor.masmorra.painel.gas_consumido"' in open(os.path.join(
              os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "lang", "editor.js"),
              encoding="utf-8").read())


if __name__ == "__main__":
    secao_1()
    secao_2()
    print(f"\n{PASS} ok, {FAIL} falhas")
    sys.exit(1 if FAIL else 0)
