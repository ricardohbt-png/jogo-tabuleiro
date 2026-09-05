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

    print("\n[3] _licao_evento registra o progresso")
    r = sala([licao(id="a", tarefa={"tipo": "atacar", "alvo": "goblin",
                                    "vezes": 2, "texto_curto": "Ataque"})])
    p = heroi(r)
    p["licao_atual"] = "a"; p["licao_progresso"]["a"] = 0

    await r._licao_evento(p, "matar", alvo="goblin")
    check("verbo errado não conta", p["licao_progresso"]["a"] == 0)

    await r._licao_evento(p, "atacar", alvo="orc")
    check("alvo errado não conta", p["licao_progresso"]["a"] == 0)

    await r._licao_evento(p, "atacar", alvo="goblin")
    check("verbo e alvo certos contam", p["licao_progresso"]["a"] == 1)
    check("vezes=2 ainda não concluiu", p["licao_atual"] == "a")

    await r._licao_evento(p, "atacar", alvo="goblin")
    check("a segunda vez conclui", p["licao_atual"] is None)
    check("entrou nas feitas do jogador", "a" in p["licoes_feitas"])
    check("entrou nas feitas da sala", "a" in r.licoes_feitas)

    await r._licao_evento(p, "atacar", alvo="goblin")
    check("depois de concluída não conta mais", p["licao_progresso"]["a"] == 2)

    print("\n[3b] Alvo ausente aceita qualquer um")
    r = sala([licao(id="a", tarefa={"tipo": "atacar", "vezes": 1,
                                    "texto_curto": "Ataque"})])
    p = heroi(r)
    p["licao_atual"] = "a"; p["licao_progresso"]["a"] = 0
    await r._licao_evento(p, "atacar", alvo="qualquer_bicho")
    check("sem alvo na tarefa, qualquer alvo serve", "a" in p["licoes_feitas"])

    print("\n[3c] Alvo de casa compara coordenada")
    r = sala([licao(id="a", tarefa={"tipo": "mover_ate", "alvo": [3, 3],
                                    "vezes": 1, "texto_curto": "Ande"})])
    p = heroi(r)
    p["licao_atual"] = "a"; p["licao_progresso"]["a"] = 0
    await r._licao_evento(p, "mover_ate", alvo=[2, 3])
    check("casa errada não conta", p["licao_progresso"]["a"] == 0)
    await r._licao_evento(p, "mover_ate", alvo=[3, 3])
    check("casa certa conclui", "a" in p["licoes_feitas"])

    print("\n[4] Disparo da lição")
    r = sala([licao(id="a", classe="warrior", pos=[3, 3],
                    trigger={"tipo": "proximidade", "raio": 1},
                    tarefa={"tipo": "encerrar_turno", "vezes": 1,
                            "texto_curto": "Encerre o turno"})])
    g = heroi(r, "h1", "warrior", (3, 3))
    m = heroi(r, "h2", "mage", (3, 3))
    await r._verificar_falas(g, None)
    await r._verificar_falas(m, None)
    check("a lição chegou ao guerreiro", any(pid == "h1" for pid, _ in r._falas_msg))
    check("a lição NÃO chegou ao mago", not any(pid == "h2" for pid, _ in r._falas_msg))
    check("nada foi para broadcast", not any(pid is None for pid, _ in r._falas_msg))
    check("virou a lição atual do guerreiro", g["licao_atual"] == "a")
    check("o mago segue sem lição", m["licao_atual"] is None)

    n = len(r._falas_msg)
    await r._verificar_falas(g, None)
    check("não repete para o mesmo jogador", len(r._falas_msg) == n)

    print("\n[4b] Lição sem tarefa se conclui ao disparar")
    r = sala([licao(id="a", classe="warrior", pos=[3, 3],
                    trigger={"tipo": "proximidade", "raio": 1}, tarefa=None)])
    g = heroi(r, "h1", "warrior", (3, 3))
    await r._verificar_falas(g, None)
    check("sem tarefa não vira lição atual", g["licao_atual"] is None)
    check("sem tarefa já entra nas feitas", "a" in g["licoes_feitas"])

    print("\n[4c] A ordem segura a lição seguinte")
    r = sala([
        licao(id="a", classe="warrior", ordem=1, pos=[3, 3],
              trigger={"tipo": "proximidade", "raio": 5},
              tarefa={"tipo": "encerrar_turno", "vezes": 1, "texto_curto": "1"}),
        licao(id="b", classe="warrior", ordem=2, pos=[3, 3],
              trigger={"tipo": "proximidade", "raio": 5},
              tarefa={"tipo": "encerrar_turno", "vezes": 1, "texto_curto": "2"}),
    ])
    g = heroi(r, "h1", "warrior", (2, 2))
    await r._verificar_falas(g, None)
    check("só a de ordem 1 disparou", g["licao_atual"] == "a")
    await r._licao_evento(g, "encerrar_turno")
    await r._verificar_falas(g, None)
    check("cumprida a 1, a 2 dispara", g["licao_atual"] == "b")

    print("\n[4d] Fala comum não regrediu")
    r = sala([{"id": "f", "pos": [3, 3], "falante": {"nome": "N", "emoji": "🧙"},
               "texto": "oi", "trigger": {"tipo": "proximidade", "raio": 5}}])
    g = heroi(r, "h1", "warrior", (2, 2))
    m = heroi(r, "h2", "mage", (2, 2))
    await r._verificar_falas(g, None)
    check("fala comum vai por broadcast", any(pid is None for pid, _ in r._falas_msg))
    check("fala comum marca disparada", r.falas[0].get("disparada") is True)
    n = len(r._falas_msg)
    await r._verificar_falas(m, None)
    check("fala comum não repete para o segundo herói", len(r._falas_msg) == n)

    print("\n[4e] Duas lições no mesmo passo não se atropelam")
    r = sala([
        licao(id="a", classe="warrior", ordem=None, pos=[3, 3],
              trigger={"tipo": "proximidade", "raio": 5},
              tarefa={"tipo": "encerrar_turno", "vezes": 1, "texto_curto": "1"}),
        licao(id="b", classe="warrior", ordem=None, pos=[3, 3],
              trigger={"tipo": "proximidade", "raio": 5},
              tarefa={"tipo": "encerrar_turno", "vezes": 1, "texto_curto": "2"}),
    ])
    g = heroi(r, "h1", "warrior", (2, 2))
    await r._verificar_falas(g, None)
    check("só uma tarefa fica pendente por vez", g["licao_atual"] == "a")
    await r._licao_evento(g, "encerrar_turno")
    check("a primeira completa", "a" in g["licoes_feitas"])
    await r._verificar_falas(g, None)
    check("a segunda dispara no passo seguinte", g["licao_atual"] == "b")
    await r._licao_evento(g, "encerrar_turno")
    check("a segunda também completa", "b" in g["licoes_feitas"])

    print("\n[4f] Recarregar a masmorra devolve as lições ao jogador")
    r = sala([licao(id="a", classe="warrior", pos=[3, 3],
                    trigger={"tipo": "proximidade", "raio": 5},
                    tarefa={"tipo": "encerrar_turno", "vezes": 1,
                            "texto_curto": "Encerre o turno"})])
    g = heroi(r, "h1", "warrior", (2, 2))
    await r._verificar_falas(g, None)
    await r._licao_evento(g, "encerrar_turno")
    check("cumpriu na primeira visita", "a" in g["licoes_feitas"])

    r._carregar_licoes({"falas": [licao(id="a", classe="warrior", pos=[3, 3],
                                        trigger={"tipo": "proximidade", "raio": 5},
                                        tarefa={"tipo": "encerrar_turno", "vezes": 1,
                                                "texto_curto": "Encerre o turno"})]})
    check("recarga zera o progresso do jogador", g["licao_progresso"] == {})
    check("recarga zera as lições feitas do jogador", g["licoes_feitas"] == [])
    check("recarga zera a lição atual", g["licao_atual"] is None)
    await r._verificar_falas(g, None)
    check("a lição dispara de novo na revisita", g["licao_atual"] == "a")

    print(f"\n{'='*50}\n  {PASS} passaram, {FAIL} falharam\n{'='*50}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
