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

    print("\n[5] handle_move dispara mover_ate")
    r = sala([licao(id="a", classe="warrior", pos=[1, 1],
                    trigger={"tipo": "proximidade", "raio": 9},
                    tarefa={"tipo": "mover_ate", "alvo": [3, 2], "vezes": 1,
                            "texto_curto": "Ande até a marca"})])
    g = heroi(r, "h1", "warrior", (2, 2))
    g["moves_left"] = 6
    await r.handle_move("h1", 1, 0)
    check("mover até a casa alvo cumpre a lição", "a" in g["licoes_feitas"])

    print("\n[5b] handle_end_turn dispara encerrar_turno")
    r = sala([licao(id="a", classe="warrior", pos=[2, 2],
                    trigger={"tipo": "proximidade", "raio": 9},
                    tarefa={"tipo": "encerrar_turno", "vezes": 1,
                            "texto_curto": "Encerre o turno"})])
    g = heroi(r, "h1", "warrior", (2, 2))
    g["moves_left"] = 6
    await r._verificar_falas(g, None)
    check("a lição está pendente", g["licao_atual"] == "a")
    async def _noop_adv(*a, **k): pass
    # Sem fila de iniciativa, handle_end_turn cai no bloco legado e divide por
    # len(self.player_order) — que é zero neste fixture. A fila ligada faz o
    # handler sair pelo caminho normal, depois do gancho da lição.
    r._advance_initiative = _noop_adv
    r.initiative_active = True
    await r.handle_end_turn("h1")
    check("encerrar o turno cumpre a lição", "a" in g["licoes_feitas"])

    print("\n[5c] Os outros cinco pontos de chamada existem")
    fonte = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "server.py"), encoding="utf-8").read()
    for verbo in ("abrir_porta", "atacar", "matar", "pegar_item", "equipar"):
        check(f"server.py chama _licao_evento com {verbo}",
              f'_licao_evento(p, "{verbo}"' in fonte
              or f'_licao_evento(p_dor, "{verbo}"' in fonte
              or f'_licao_evento(_matador, "{verbo}"' in fonte)

    print("\n[5d] Lição cumprida no passo libera a próxima no mesmo passo")
    r = sala([
        licao(id="a", classe="warrior", ordem=1, pos=[3, 2],
              trigger={"tipo": "proximidade", "raio": 9},
              tarefa={"tipo": "mover_ate", "alvo": [3, 2], "vezes": 1,
                      "texto_curto": "Ande até a marca"}),
        licao(id="b", classe="warrior", ordem=2, pos=[3, 2],
              trigger={"tipo": "proximidade", "raio": 9},
              tarefa={"tipo": "encerrar_turno", "vezes": 1,
                      "texto_curto": "Encerre o turno"}),
    ])
    g = heroi(r, "h1", "warrior", (2, 2))
    g["moves_left"] = 6
    await r.handle_move("h1", 1, 0)
    check("a primeira lição foi cumprida pelo passo", "a" in g["licoes_feitas"])
    check("a segunda já apareceu no mesmo passo", g["licao_atual"] == "b")

    print("\n[6] Porta com condição de lição")
    r = sala([licao(id="a", classe="warrior",
                    tarefa={"tipo": "encerrar_turno", "vezes": 1,
                            "texto_curto": "Encerre o turno"})])
    r.tiles[3][4] = S.DOOR
    r.rooms.append({"id": 1, "x": 5, "y": 1, "w": 1, "h": 4, "role": "monster",
                    "locked": True, "doors": [[4, 3]], "cleared": True, "looted": True})
    r.door_rooms = {(4, 3): [1]}
    r.door_conditions = {(4, 3): {"type": "licao", "licao_id": "a"}}
    r.door_condition_activated = {(4, 3): set()}
    check("porta fechada antes da lição", r._door_condition_satisfied((4, 3)) is False)
    r.licoes_feitas.add("a")
    check("porta abre depois da lição", r._door_condition_satisfied((4, 3)) is True)
    check("serializa sem estourar", "4,3" in r._serializar_condicoes_portas())

    print("\n[6b] Validação da porta de lição")
    def mapa_porta(cond):
        d = mapa_base(falas=[licao(id="a")])
        d["tiles"][3][4] = S.DOOR
        d["rooms"][0]["doors"] = [[4, 3]]
        d["door_conditions"] = {"4,3": cond}
        return d
    ok, _ = S.validar_dungeon(mapa_porta({"type": "licao", "licao_id": "a"}))
    check("porta apontando para lição existente passa", ok is True)
    ok, msg = S.validar_dungeon(mapa_porta({"type": "licao", "licao_id": "zzz"}))
    check("licao_id inexistente é recusado", ok is False and "zzz" in msg)

    print("\n[7] Bloco tutorial do game_state")
    r = sala([])
    check("masmorra sem lição não manda bloco", r._tutorial_payload() is None)

    r = sala([licao(id="a", classe="warrior", ordem=1,
                    tarefa={"tipo": "atacar", "alvo": "goblin", "vezes": 3,
                            "texto_curto": "Ataque o boneco"}),
              licao(id="b", classe="mage", ordem=1,
                    tarefa={"tipo": "encerrar_turno", "vezes": 1,
                            "texto_curto": "Encerre o turno"})])
    g = heroi(r, "h1", "warrior", (2, 2))
    g["licao_atual"] = "a"; g["licao_progresso"]["a"] = 1
    bloco = r._tutorial_payload()["por_classe"]["warrior"]
    check("mostra a lição atual", bloco["licao_id"] == "a")
    check("mostra o texto curto", bloco["texto_curto"] == "Ataque o boneco")
    check("mostra o progresso", bloco["feito"] == 1 and bloco["vezes"] == 3)
    check("total conta só as da classe", bloco["total"] == 1)
    check("mago sem herói na sala não aparece",
          "mage" not in r._tutorial_payload()["por_classe"])

    g["licao_atual"] = None; g["licoes_feitas"] = ["a"]
    bloco = r._tutorial_payload()["por_classe"]["warrior"]
    check("sem pendência, licao_id é nulo", bloco["licao_id"] is None)
    check("conta a concluída", bloco["concluidas"] == 1)

    print("\n[5e] Verbo que nao e movimento tambem libera a proxima licao")
    r = sala([
        licao(id="a", classe="warrior", ordem=1, pos=[2, 2],
              trigger={"tipo": "proximidade", "raio": 9},
              tarefa={"tipo": "encerrar_turno", "vezes": 1, "texto_curto": "Encerre"}),
        licao(id="b", classe="warrior", ordem=2, pos=[2, 2],
              trigger={"tipo": "proximidade", "raio": 9},
              tarefa={"tipo": "equipar", "vezes": 1, "texto_curto": "Equipe"}),
    ])
    g = heroi(r, "h1", "warrior", (2, 2))
    await r._verificar_falas(g, None)
    check("a primeira licao esta pendente", g["licao_atual"] == "a")
    await r._licao_evento(g, "encerrar_turno")
    check("cumprida por verbo sem movimento", "a" in g["licoes_feitas"])
    check("a proxima aparece sem o heroi andar", g["licao_atual"] == "b")
    print("\n[8] Entrada do tutorial pela cidade")
    adv = S.WORLD_ADVENTURES.get("treinamento")
    check("o destino existe", bool(adv))
    check("nao custa mantimento", (adv["fome"], adv["sede"]) == (0, 0))
    check("da para revisitar", adv.get("revisitavel") is True)
    check("nao rende renome", adv.get("renome_recompensa", 0) == 0)
    check("aponta para o mapa do tutorial",
          [d["file"] for d in adv["dungeons"]] == ["campo_de_treinamento.json"])
    check("o mapa do tutorial e valido",
          S.validar_dungeon(S.carregar_dungeon("campo_de_treinamento.json"))[0] is True)

    ponto = S.CITY_MAP_POINTS["alva_e_luz"].get("treinamento")
    check("o ponto existe em Alva e Luz", bool(ponto))
    check("o ponto e uma entrada de masmorra", ponto.get("type") == "dungeon")
    check("o ponto aponta para o destino", ponto.get("aventura") == "treinamento")
    check("o id nao e 'dungeon' (o loader descarta esse id)",
          "dungeon" not in S.CITY_MAP_POINTS["alva_e_luz"])

    r = sala([])
    r.phase = "city"
    heroi(r, "h1", "warrior", (2, 2))
    r.host_pid = "h1"; r.connections["h1"] = object()
    pts = r._city_points_payload()["alva_e_luz"]
    check("o ponto chega ao cliente", "treinamento" in pts)
    ids = [a.get("id") for a in (r._city_state_payload().get("world") or {}).get("adventures", [])]
    check("o destino chega ao cliente", "treinamento" in ids)

    await r.handle_world_adventure("h1", "treinamento")
    check("clicar leva para a masmorra", r.phase == "playing")
    # Relacao, nao numero cravado: o mapa ganha licoes conforme o tutorial cresce.
    _falas_mapa = S.carregar_dungeon("campo_de_treinamento.json")["falas"]
    _esperado = sum(1 for f in _falas_mapa
                    if f.get("classe") or f.get("tarefa") or f.get("efeito")
                    or f.get("ordem") is not None)
    check("todas as licoes do arquivo foram carregadas", len(r.licoes) == _esperado)
    check("entrar nao cobrou fome nem sede",
          (r.players["h1"]["fome"], r.players["h1"]["sede"]) == (100, 100))
    print("\n[9] Equipar rapido tambem cumpre a licao")
    r = sala([licao(id="a", classe="warrior", pos=[2, 2],
                    trigger={"tipo": "proximidade", "raio": 9},
                    tarefa={"tipo": "equipar", "alvo": "sword", "vezes": 1,
                            "texto_curto": "Equipe a espada"})])
    g = heroi(r, "h1", "warrior", (2, 2))
    await r._verificar_falas(g, None)
    check("a licao de equipar esta pendente", g["licao_atual"] == "a")
    g["bag"] = [dict(S._DUNGEON_ITEM_CATALOG["sword"])]
    await r.handle_quick_equip_from_bag("h1", 0)
    check("equipar pelo atalho cumpre a licao", "a" in g["licoes_feitas"])

    fonte = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "server.py"), encoding="utf-8").read()
    check("os DOIS caminhos de equipar chamam _licao_evento",
          fonte.count('_licao_evento(p, "equipar"') == 2)
    print("\n[10] Cada uma das seis classes tem trilha propria")
    _mapa = S.carregar_dungeon("campo_de_treinamento.json")
    _por_classe = {}
    for _f in _mapa["falas"]:
        _por_classe.setdefault(_f.get("classe") or "TODAS", []).append(_f["id"])
    check("as cinco licoes do atrio continuam la",
          all(f"atrio_0{i}" in _por_classe.get("TODAS", []) for i in range(1, 6)))
    _classes = ("warrior", "mage", "rogue", "cleric", "bard", "paladin")
    _tamanhos = {c: len(_por_classe.get(c, [])) for c in _classes}
    # O ladino tem uma a mais de proposito: so ele desarma armadilhas.
    check("nenhuma classe fica para tras", min(_tamanhos.values()) >= 3)
    check("o ladino tem a licao de desarme so dele",
          _tamanhos["rogue"] > min(_tamanhos.values()))
    check("nenhuma licao mira o goblin antigo",
          all((f.get("tarefa") or {}).get("alvo") != "goblin" for f in _mapa["falas"]))
    _bonecos = [m for m in _mapa["monsters"] if m["type"] == "boneco_treino"]
    check("ha bonecos para todos", len(_bonecos) >= 6)

    print("\n[10b] A trilha da classe dispara para o heroi certo")
    for _cls, _pref in (("cleric", "clerigo"), ("mage", "mago"), ("bard", "bardo")):
        r = GameRoom("T")
        async def _noop(*a, **k): pass
        r.gm_say = _noop; r.broadcast = _noop; r.send_to = _noop
        r.broadcast_city_state = _noop; r.push_state = _noop
        p = make_player("h1", "Heroi", _cls, 0)
        r.players["h1"] = p; r.host_pid = "h1"; r.connections["h1"] = object()
        r.phase = "lobby"
        await r.handle_select_dungeon("h1", "campo_de_treinamento.json")
        r.phase = "city"
        await r.enter_dungeon("h1")
        # o atrio ja foi: o heroi chega na sala dos bonecos
        p["licoes_feitas"] = [f"atrio_0{i}" for i in range(1, 6)]
        p["licao_progresso"] = {i: 1 for i in p["licoes_feitas"]}
        p["pos"] = [14, 3]
        await r._verificar_falas(p, None)
        check(f"{_cls} recebe {_pref}_01", p["licao_atual"] == f"{_pref}_01")

    print("\n[11] Um golpe que mata cumpre as duas licoes")
    r = sala([
        licao(id="a", classe="warrior", ordem=1, pos=[2, 2],
              trigger={"tipo": "proximidade", "raio": 9},
              tarefa={"tipo": "atacar", "vezes": 1, "texto_curto": "Acerte"}),
        licao(id="b", classe="warrior", ordem=2, pos=[2, 2],
              trigger={"tipo": "proximidade", "raio": 9},
              tarefa={"tipo": "matar", "vezes": 1, "texto_curto": "Derrube"}),
    ])
    g = heroi(r, "h1", "warrior", (2, 2))
    await r._verificar_falas(g, None)
    check("a licao de acertar esta pendente", g["licao_atual"] == "a")
    _m = {"id": "m1", "type": "boneco_treino", "name": "Boneco", "nome": "Boneco",
          "pos": [3, 2], "hp": 1, "max_hp": 1, "ac": 1, "alertado": True}
    r.monsters["m1"] = _m
    g["action_done"] = False
    await r.handle_attack("h1", "m1")
    check("o acerto cumpriu a primeira", "a" in g["licoes_feitas"])
    check("a morte no mesmo golpe cumpriu a segunda", "b" in g["licoes_feitas"])
    print("\n[12] O tutorial fecha e devolve o heroi a cidade")
    r = GameRoom("T")
    async def _noop(*a, **k): pass
    r.gm_say = _noop; r.broadcast = _noop; r.send_to = _noop
    r.broadcast_city_state = _noop; r.push_state = _noop
    p = make_player("h1", "Lewis", "cleric", 0)
    r.players["h1"] = p; r.host_pid = "h1"; r.connections["h1"] = object()
    r.phase = "city"
    await r.handle_world_adventure("h1", "treinamento")
    check("entrou pela cidade", r.phase == "playing")
    check("os bonecos estao la",
          sum(1 for m in r.monsters.values() if m["type"] == "boneco_treino") >= 6)
    _saida = S.carregar_dungeon("campo_de_treinamento.json")["exit"]
    p["pos"] = [_saida["x"], _saida["y"]]    # a saida vem do mapa, nao cravada
    await r._check_objectives()
    check("chegar a saida cumpre o objetivo", r.mission_complete_pending is True)
    await r.handle_encerrar_missao("h1")
    check("encerrar devolve o heroi a cidade", r.phase == "city")
    check("o tutorial nao cobra mantimento", (p["fome"], p["sede"]) == (100, 100))
    print("\n[13] Fase 2: os verbos novos")
    for _v in ("usar_item", "usar_magia", "usar_habilidade",
               "usar_tecnica", "usar_instrumento", "desarmar_armadilha"):
        check(f"{_v} esta no vocabulario", _v in S.LICAO_VERBOS)
    _fonte = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "server.py"), encoding="utf-8").read()
    for _v in ("usar_item", "usar_magia", "usar_tecnica",
               "usar_instrumento", "desarmar_armadilha"):
        check(f"server.py chama _licao_evento com {_v}",
              f'_licao_evento(p, "{_v}"' in _fonte)
    # Seis handlers de classe + o site das habilidades armadas do guerreiro,
    # que nao tem handler proprio (sao aplicadas dentro do handle_attack).
    check("usar_habilidade cobre as habilidades de classe",
          _fonte.count('_licao_evento(p, "usar_habilidade"') >= 6)
    check("e tambem as habilidades armadas do guerreiro",
          '_licao_evento(p, "usar_habilidade", alvo=_sk["id"])' in _fonte)

    print("\n[13b] usar_item cumpre a licao (comer e beber)")
    r = sala([licao(id="a", classe="warrior", pos=[2, 2],
                    trigger={"tipo": "proximidade", "raio": 9},
                    tarefa={"tipo": "usar_item", "alvo": "racao_viagem", "vezes": 1,
                            "texto_curto": "Coma uma racao"})])
    g = heroi(r, "h1", "warrior", (2, 2))
    await r._verificar_falas(g, None)
    check("a licao de comer esta pendente", g["licao_atual"] == "a")
    g["bag"] = [dict(S._DUNGEON_ITEM_CATALOG["racao_viagem"])]
    g["fome"] = g["sede"] = 30
    await r.handle_use_item("h1", "racao_viagem")
    check("comer cumpriu a licao", "a" in g["licoes_feitas"])
    check("a racao alimentou de verdade", g["fome"] > 30)

    print("\n[13c] O campo efeito faz o heroi sentir a regra")
    r = sala([licao(id="a", classe="warrior", pos=[2, 2],
                    trigger={"tipo": "proximidade", "raio": 9},
                    tarefa=None, efeito={"fome": 0, "sede": 0})])
    g = heroi(r, "h1", "warrior", (2, 2))
    check("comeca alimentado", (g["fome"], g["sede"]) == (100, 100))
    await r._verificar_falas(g, None)
    check("a licao zerou fome e sede", (g["fome"], g["sede"]) == (0, 0))
    check("e a penalidade de sobrevivencia aparece",
          r._modificador_sobrevivencia(g) < 0)

    print("\n[13d] Validacao do efeito")
    ok, _ = S.validar_dungeon(mapa_base(falas=[licao(efeito={"fome": 10})]))
    check("efeito bem formado passa", ok is True)
    ok, msg = S.validar_dungeon(mapa_base(falas=[licao(efeito={"ouro": 10})]))
    check("chave desconhecida e recusada", ok is False and "ouro" in msg)
    ok, msg = S.validar_dungeon(mapa_base(falas=[licao(efeito={"fome": 250})]))
    check("valor fora de 0-100 e recusado", ok is False)
    ok, msg = S.validar_dungeon(mapa_base(falas=[licao(efeito={})]))
    check("efeito vazio e recusado", ok is False)
    print("\n[14] A sala de Provisoes faz o heroi sentir fome e sede")
    r = GameRoom("T")
    async def _noop(*a, **k): pass
    r.gm_say = _noop; r.broadcast = _noop; r.send_to = _noop
    r.broadcast_city_state = _noop; r.push_state = _noop
    p = make_player("h1", "Thorin", "warrior", 0)
    r.players["h1"] = p; r.host_pid = "h1"; r.connections["h1"] = object()
    r.phase = "city"
    await r.handle_world_adventure("h1", "treinamento")
    r._is_turn = lambda pid: True
    # atalho: atrio e sala dos bonecos ja cumpridos
    p["licoes_feitas"] = [f"atrio_0{i}" for i in range(1, 6)] + ["guerreiro_01", "guerreiro_02"]
    p["licao_progresso"] = {i: 1 for i in p["licoes_feitas"]}

    check("entra alimentado", (p["fome"], p["sede"]) == (100, 100))
    _prov = next(f for f in S.carregar_dungeon("campo_de_treinamento.json")["falas"]
                 if f["id"] == "prov_01")
    p["pos"] = list(_prov["pos"])          # onde quer que a sala esteja
    await r._verificar_falas(p, None)
    check("a sala zera fome e sede", (p["fome"], p["sede"]) == (0, 0))
    check("a penalidade aparece", r._modificador_sobrevivencia(p) == -2)
    _hp = p["hp"]
    await r._aplicar_exaustao_rodada()
    check("e a exaustao custa vida de verdade", p["hp"] == _hp - 1)
    check("a licao manda comer", p["licao_atual"] == "prov_02")

    _bau = next(c for c in r.chests.values()
                if any(i["id"] == "racao_viagem" for i in c["items"]))
    for _ in range(4):
        _i = next((k for k, it in enumerate(_bau["items"]) if it["id"] == "garrafa_agua"), None)
        if _i is None: break
        await r.handle_take_from_chest("h1", _bau["id"], "item", _i)
    _i = next(k for k, it in enumerate(_bau["items"]) if it["id"] == "racao_viagem")
    await r.handle_take_from_chest("h1", _bau["id"], "item", _i)

    await r.handle_use_item("h1", "racao_viagem")
    check("comer cumpre e passa para a agua", p["licao_atual"] == "prov_03")
    await r.handle_use_item("h1", "garrafa_agua")
    check("uma garrafa nao basta", p["licao_atual"] == "prov_03")
    await r.handle_use_item("h1", "garrafa_agua")
    check("duas garrafas cumprem", "prov_03" in p["licoes_feitas"])
    check("e tiram o heroi da penalidade", r._modificador_sobrevivencia(p) == 0)

    _fecho = next(f for f in S.carregar_dungeon("campo_de_treinamento.json")["falas"]
                  if f["id"] == "prov_04")
    p["pos"] = list(_fecho["pos"])
    await r._verificar_falas(p, None)
    check("o fecho da sala dispara", "prov_04" in p["licoes_feitas"])
    _sai = S.carregar_dungeon("campo_de_treinamento.json")["exit"]
    p["pos"] = [_sai["x"], _sai["y"]]
    await r._check_objectives()
    check("a saida fica depois das provisoes", r.mission_complete_pending is True)
    print("\n[15] Sala de Kit: cada classe usa a propria habilidade")
    _acoes = {
        "warrior": ("guerreiro_03", lambda r, p, m: r.handle_attack("h1", m, buffs=["mira_certeira"])),
        "mage":    ("mago_03",      lambda r, p, m: r.handle_magia("h1", {"magia_id": "bola_fogo", "tx": p["pos"][0] + 1, "ty": p["pos"][1]})),
        "rogue":   ("ladino_03",    lambda r, p, m: r.handle_criar_armadilha("h1", {"tipo": "buraco"})),
        "cleric":  ("clerigo_03",   lambda r, p, m: r.handle_cura("h1", {"target_id": "h1", "num_dados": 1, "alcance_extra": 0})),
        "bard":    ("bardo_03",     lambda r, p, m: r.handle_ativar_cancao("h1", {"atributos": ["acerto"]})),
        "paladin": ("paladino_03",  lambda r, p, m: r.handle_golpe_sagrado("h1")),
    }
    for _cls, (_lid, _acao) in _acoes.items():
        r = GameRoom("T")
        async def _noop(*a, **k): pass
        r.gm_say = _noop; r.broadcast = _noop; r.send_to = _noop
        r.broadcast_city_state = _noop; r.push_state = _noop; r._broadcast_dado = _noop
        p = make_player("h1", "Heroi", _cls, 0)
        r.players["h1"] = p; r.host_pid = "h1"; r.connections["h1"] = object()
        r.phase = "city"
        await r.handle_world_adventure("h1", "treinamento")
        r._is_turn = lambda pid: True
        r._no_raio = lambda a, b, raio, *x, **k: True
        r._tem_linha_de_visao = lambda *a, **k: True
        p["magias_conhecidas"] = ["bola_fogo"]
        # atrio e sala dos bonecos cumpridos; o heroi entra na sala de kit
        _pref = {"warrior": "guerreiro", "mage": "mago", "rogue": "ladino",
                 "cleric": "clerigo", "bard": "bardo", "paladin": "paladino"}[_cls]
        p["licoes_feitas"] = [f"atrio_0{i}" for i in range(1, 6)] + [f"{_pref}_01", f"{_pref}_02"]
        p["licao_progresso"] = {i: 1 for i in p["licoes_feitas"]}
        p["pos"] = [21, 3]
        await r._verificar_falas(p, None)
        check(f"{_cls}: a licao de kit dispara", p["licao_atual"] == _lid)
        _alvo = next((m for m in r.monsters.values()
                      if m["type"] == "boneco_treino" and m["pos"][0] >= 20), None)
        # Guerreiro precisa de adjacencia; o mago, de alcance e linha de visao.
        if _cls in ("mage", "warrior"):
            p["pos"] = [_alvo["pos"][0] - 1, _alvo["pos"][1]]
        await _acao(r, p, _alvo["id"] if _cls == "warrior" else _alvo)
        check(f"{_cls}: usar a habilidade cumpre", _lid in p["licoes_feitas"])
    print("\n[16] Sala de Perigo: armadilha, resistencia e fraqueza")
    r = GameRoom("T")
    async def _noop(*a, **k): pass
    r.gm_say = _noop; r.broadcast = _noop; r.send_to = _noop
    r.broadcast_city_state = _noop; r.push_state = _noop; r._broadcast_dado = _noop
    p = make_player("h1", "Thorin", "warrior", 0)
    r.players["h1"] = p; r.host_pid = "h1"; r.connections["h1"] = object()
    r.phase = "city"
    await r.handle_world_adventure("h1", "treinamento")
    r._is_turn = lambda pid: True
    check("a armadilha autorada virou desarmavel", len(r.armadilhas) == 1)
    _esq = next((m for m in r.monsters.values() if m["type"] == "esqueleto_humano"), None)
    check("o esqueleto esta la", _esq is not None)

    p["licoes_feitas"] = ([f"atrio_0{i}" for i in range(1, 6)]
                          + ["guerreiro_01", "guerreiro_02", "guerreiro_03"]
                          + [f"prov_0{i}" for i in range(1, 5)])
    p["licao_progresso"] = {i: 1 for i in p["licoes_feitas"]}
    _esp = dict(S._DUNGEON_ITEM_CATALOG["sword"])
    p["gear"]["weapon"] = _esp; p["weapon"] = _esp
    p["pos"] = [34, 3]
    await r._verificar_falas(p, None)
    check("a licao do esqueleto dispara", p["licao_atual"] == "perigo_02")

    # Corte contra osso entra a MENOS; impacto entra a MAIS. A licao promete
    # cerca de tres pontos de diferenca — se a ficha do esqueleto mudar, isto
    # avisa antes de o texto virar mentira.
    def _dano(arma_id):
        import statistics
        S_ = S
        return arma_id
    async def _dano_medio(n=150):
        """Media de dano por ACERTO. Um golpe so nao serve: os dados se
        sobrepoem e a comparacao fica instavel — a licao promete uma
        diferenca media, e e isso que o teste tem de medir."""
        _tot = _acertos = 0
        for _ in range(n):
            _esq["hp"] = 999
            _a = _esq["hp"]
            p["action_done"] = False
            await r.handle_attack("h1", _esq["id"])
            if _esq["hp"] < _a:
                _tot += _a - _esq["hp"]; _acertos += 1
        return _tot / max(1, _acertos)

    _esq["hp"] = 999
    p["pos"] = [36, 3]
    _antes = _esq["hp"]
    while _esq["hp"] == _antes:
        p["action_done"] = False
        await r.handle_attack("h1", _esq["id"])
    check("acertar cumpre e pede a maca", p["licao_atual"] == "perigo_03")
    _corte = await _dano_medio()

    _bau = next(c for c in r.chests.values()
                if any(i["id"] == "maca_treino" for i in c["items"]))
    p["pos"] = list(_bau["pos"])
    await r.handle_take_from_chest("h1", _bau["id"], "item", 0)
    _i = next(i for i, it in enumerate(p["bag"]) if it.get("id") == "maca_treino")
    await r.handle_equip_from_bag("h1", _i)
    check("equipar a maca cumpre", "perigo_03" in p["licoes_feitas"])
    check("e passa para derrubar", p["licao_atual"] == "perigo_04")

    p["pos"] = [36, 3]          # voltar para perto: o bau fica longe do esqueleto
    _impacto = await _dano_medio()
    check("a maca doi mais que a espada no esqueleto", _impacto > _corte)
    # A diferenca real e ~2.9 (-1 resistido contra +2 vulneravel). O piso em
    # 1.2 com 150 amostras avisa se a ficha do esqueleto mudar e o texto da
    # licao virar mentira, sem ficar instavel pela variancia do dado.
    check("e a diferenca e a que a licao promete (~3)", _impacto - _corte > 1.2)

    # O golpe final pode errar (CA 12): insiste ate cair, como um jogador faria.
    for _ in range(20):
        if "perigo_04" in p["licoes_feitas"]: break
        _esq["hp"] = 1; p["action_done"] = False
        await r.handle_attack("h1", _esq["id"])
    check("derrubar fecha a sala", "perigo_04" in p["licoes_feitas"])
    _sai = S.carregar_dungeon("campo_de_treinamento.json")["exit"]
    p["pos"] = [_sai["x"], _sai["y"]]
    await r._check_objectives()
    check("e a saida encerra o tutorial", r.mission_complete_pending is True)

    print("\n[16b] So o ladino desarma")
    r = GameRoom("T")
    r.gm_say = _noop; r.broadcast = _noop; r.send_to = _noop
    r.broadcast_city_state = _noop; r.push_state = _noop; r._broadcast_dado = _noop
    p = make_player("h1", "Luccas", "rogue", 0)
    r.players["h1"] = p; r.host_pid = "h1"; r.connections["h1"] = object()
    r.phase = "city"
    await r.handle_world_adventure("h1", "treinamento")
    r._is_turn = lambda pid: True
    p["licoes_feitas"] = ([f"atrio_0{i}" for i in range(1, 6)]
                          + ["ladino_01", "ladino_02", "ladino_03"]
                          + [f"prov_0{i}" for i in range(1, 5)])
    p["licao_progresso"] = {i: 1 for i in p["licoes_feitas"]}
    p["pos"] = [34, 3]
    await r._verificar_falas(p, None)
    check("o ladino recebe a licao de desarme", p["licao_atual"] == "ladino_04")
    _arm = r.armadilhas[0]; _arm["visivel"] = True
    p["pos"] = [_arm["pos"][0] - 1, _arm["pos"][1]]
    for _ in range(15):
        if "ladino_04" in p["licoes_feitas"]: break
        p["action_done"] = False
        await r.handle_desarmar_armadilha("h1", {"tx": _arm["pos"][0], "ty": _arm["pos"][1]})
    check("desarmar cumpre a licao", "ladino_04" in p["licoes_feitas"])
    print(f"\n{'='*50}\n  {PASS} passaram, {FAIL} falharam\n{'='*50}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
