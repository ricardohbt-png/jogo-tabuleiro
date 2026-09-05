"""Tutorial por herói — Fase 1 (motor de lições). Roda da raiz: python tools/test_tutorial.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def mapa_base(**extra):
    """Masmorra mínima válida: 6x6, uma sala, entrada e saída."""
    tiles = [[S.WALL]*6 for _ in range(6)]
    for y in range(1, 5):
        for x in range(1, 5):
            tiles[y][x] = S.FLOOR
    d = {
        "schema_version": 1, "id": "t", "name": "t",
        "grid": {"w": 6, "h": 6}, "tiles": tiles,
        "rooms": [{"id": 0, "x": 1, "y": 1, "w": 4, "h": 4,
                   "role": "entrance", "locked": False, "doors": []}],
        "entrance": {"x": 1, "y": 1}, "exit": {"x": 4, "y": 4},
        "monsters": [], "chests": [], "traps": [], "decorations": [],
        "secret_passages": [], "falas": [],
        "objectives": {"primary": {"type": "kill_all"}, "secondary": []},
    }
    d.update(extra)
    return d

def licao(**kw):
    """Uma lição autorada, com os campos obrigatórios já preenchidos."""
    base = {"id": "lic_1", "pos": [2, 2], "falante": {"nome": "Mestre", "emoji": "🧙"},
            "texto": "Ande até a marca.", "trigger": {"tipo": "proximidade", "raio": 2},
            "classe": "warrior", "ordem": 1,
            "tarefa": {"tipo": "mover_ate", "alvo": [3, 3], "vezes": 1,
                       "texto_curto": "Ande até a marca"}}
    base.update(kw)
    return base


def sala(falas=None):
    """Sala em 'playing' com mapa 6x6, uma sala e as falas dadas já carregadas."""
    r = GameRoom("TEST")
    falas_msg = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "fala":
            falas_msg.append((pid, msg))
    async def cap_bcast(msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "fala":
            falas_msg.append((None, msg))
    r.gm_say = noop; r.push_state = noop; r._broadcast_dado = noop
    r.broadcast = cap_bcast; r.send_to = cap_send
    r._is_turn = lambda pid: True
    r.phase = "playing"
    r.map_w = 6; r.map_h = 6
    r.tiles = [[S.WALL]*6 for _ in range(6)]
    for y in range(1, 5):
        for x in range(1, 5):
            r.tiles[y][x] = S.FLOOR
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 4, "h": 4, "role": "entrance",
                "locked": False, "doors": [], "cleared": True, "looted": True}]
    r.monsters = {}; r.chests = {}; r.ground_items = {}
    r._carregar_licoes({"falas": falas or []})
    r._falas_msg = falas_msg
    return r

def heroi(r, pid="h1", classe="warrior", pos=(2, 2)):
    p = make_player(pid, "Herói", classe, 0)
    p["pos"] = list(pos); p["alive"] = True
    r.players[pid] = p
    return p


async def main():
    print("\n[1] Validação dos campos novos da lição")
    ok, _ = S.validar_dungeon(mapa_base(falas=[licao()]))
    check("lição bem formada passa", ok is True)

    ok, msg = S.validar_dungeon(mapa_base(falas=[licao(classe="druida")]))
    check("classe desconhecida é recusada", ok is False and "classe" in msg)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(tarefa={"tipo": "dancar", "vezes": 1, "texto_curto": "x"})]))
    check("verbo desconhecido é recusado", ok is False and "tipo" in msg)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(tarefa={"tipo": "encerrar_turno", "vezes": 1, "texto_curto": ""})]))
    check("tarefa sem texto_curto é recusada", ok is False)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(tarefa={"tipo": "encerrar_turno", "vezes": 0, "texto_curto": "x"})]))
    check("vezes menor que 1 é recusado", ok is False)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(id="a", ordem=1), licao(id="b", ordem=1)]))
    check("ordem duplicada na mesma classe é recusada", ok is False and "ordem" in msg)

    ok, _ = S.validar_dungeon(mapa_base(falas=[
        licao(id="a", ordem=1, classe="warrior"),
        licao(id="b", ordem=1, classe="mage")]))
    check("mesma ordem em classes diferentes passa", ok is True)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(trigger={"tipo": "manual"})]))
    check("lição com gatilho manual é recusada", ok is False and "manual" in msg)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(tarefa={"tipo": "mover_ate", "alvo": [99, 99], "vezes": 1,
                      "texto_curto": "x"})]))
    check("alvo de mover_ate fora do grid é recusado", ok is False)

    ok, _ = S.validar_dungeon(mapa_base(falas=[
        {"id": "f", "pos": [2, 2], "falante": {"nome": "", "emoji": "🧙"},
         "texto": "oi", "trigger": {"tipo": "manual"}}]))
    check("fala comum sem os campos novos continua válida", ok is True)

    ok, msg = S.validar_dungeon(mapa_base(falas=[licao(ordem=True)]))
    check("ordem booleana é recusada", ok is False and "ordem" in msg)

    ok, msg = S.validar_dungeon(mapa_base(falas=[
        licao(tarefa={"tipo": "encerrar_turno", "vezes": True, "texto_curto": "x"})]))
    check("vezes booleano é recusado", ok is False and "vezes" in msg)

    print("\n[2] Carga das lições")
    r = sala([licao(id="a"), {"id": "f", "pos": [2, 2],
                              "falante": {}, "texto": "oi",
                              "trigger": {"tipo": "manual"}}])
    check("só a lição entra em self.licoes", [l["id"] for l in r.licoes] == ["a"])
    check("as duas continuam em self.falas", len(r.falas) == 2)
    check("licoes_feitas começa vazio", r.licoes_feitas == set())

    p = heroi(r)
    check("jogador nasce sem lição atual", p["licao_atual"] is None)
    check("jogador nasce com progresso vazio", p["licao_progresso"] == {})
    check("jogador nasce sem lições feitas", p["licoes_feitas"] == [])

    print(f"\n{'='*50}\n  {PASS} passaram, {FAIL} falharam\n{'='*50}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
