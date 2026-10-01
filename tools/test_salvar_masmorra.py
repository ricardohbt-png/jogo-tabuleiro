"""Foto da masmorra (Etapa 2 do salvamento) — passos 1 e 2.

Roda da raiz:  python tools/test_salvar_masmorra.py

O QUE COBRA
  [1] Codificador/decodificador puros: ida e volta de set, tupla, dict com chave
      tupla/int/"$…", aninhados; recusa alta de T, objeto e número não finito;
      saída determinística (mesma foto → mesmo JSON).
  [2] Cobertura: TODO atributo de GameRoom — os escritos como `self.x =` na
      classe E os que aparecem na sala de verdade depois de entrar na masmorra —
      está classificado em FOTO_SALA_CATEGORIAS; nenhuma entrada sobra.
  [3] Só JSON, em masmorras reais: para cada arquivo de dungeons/ e uma
      procedural, os campos "foto"/"foto_pid" e as fichas dos heróis passam por
      json.dumps SEM `default=` e voltam idênticos.

Spec: docs/superpowers/specs/2026-10-01-salvar-aventura-design.md (seção 5).
"""
import ast, asyncio, io, json, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

# As seções [4]/[5] trocam a gravação em disco por uma lista; a [6] usa o
# armazenamento de verdade (numa pasta temporária) e precisa das originais.
_ORIGINAIS = {n: getattr(S, n) for n in ("write_savegame", "_agendar_descarga", "load_savegame")}

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


def ida_e_volta(valor):
    texto = json.dumps(S._foto_codificar(valor), ensure_ascii=False)   # sem default=
    return S._foto_decodificar(json.loads(texto)), texto


def secao_codec():
    print("\n[1] Codificador e decodificador")
    casos = {
        "escalares": [1, 2.5, "x", True, None, False, 0],
        "set de tuplas": {(1, 2), (3, 4), (0, 0)},
        "tupla": (1, "a", (2, 3)),
        "dict chave tupla": {(1, 2): "lava", (3, 4): {"dano": "2d6"}},
        "dict chave int": {1: "a", 2: [1, 2]},
        "dict chave $": {"$set": 1, "normal": 2},
        "dict chave bool": {True: 1, False: 0},
        "aninhado": {"monstros": {"m1": {"pos": [1, 2], "tags": {"a", "b"}}},
                     "zonas": [{"tiles": {(0, 1), (1, 1)}}]},
        "vazios": {"l": [], "d": {}, "s": set(), "t": ()},
    }
    for nome, valor in casos.items():
        volta, _ = ida_e_volta(valor)
        check(f"ida e volta: {nome}", volta == valor and type(volta) is type(valor), repr(volta))
    _, a = ida_e_volta({(5, 5), (1, 1), (3, 3)})
    _, b = ida_e_volta({(3, 3), (5, 5), (1, 1)})
    check("set gera o mesmo JSON em qualquer ordem", a == b)
    _, a = ida_e_volta({(2, 0): 1, (1, 0): 2})
    _, b = ida_e_volta({(1, 0): 2, (2, 0): 1})
    check("dict com chave tupla gera o mesmo JSON em qualquer ordem", a == b)

    for rotulo, ruim in (("T (texto tardio)", {"log": [S.T("narracao.abre_uma_porta", heroi="Ana")]}),
                         ("objeto qualquer", {"x": object()}),
                         ("evento asyncio", {"ev": asyncio.Event()}),
                         ("número não finito", {"x": float("inf")})):
        try:
            S._foto_codificar(ruim)
            check(f"recusa {rotulo}", False, "não levantou")
        except S.FotoNaoSerializavel as e:
            check(f"recusa {rotulo} com o caminho do valor", "foto." in str(e), str(e))
    check("FotoNaoSerializavel é TypeError (falha alta)", issubclass(S.FotoNaoSerializavel, TypeError))


def atributos_da_classe():
    """Todo `self.<attr> = …` (inclusive em tupla e +=) dentro de class GameRoom."""
    src = io.open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
    cls = next(n for n in ast.parse(src).body
               if isinstance(n, ast.ClassDef) and n.name == "GameRoom")
    attrs = set()
    for node in ast.walk(cls):
        alvos = []
        if isinstance(node, ast.Assign): alvos = node.targets
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)): alvos = [node.target]
        for t in alvos:
            for e in [t] + (list(t.elts) if isinstance(t, ast.Tuple) else []):
                if (isinstance(e, ast.Attribute) and isinstance(e.value, ast.Name)
                        and e.value.id == "self"):
                    attrs.add(e.attr)
    return attrs


async def sala_na_masmorra(arquivo=None, classes=("warrior", "mage", "rogue"), pids=None):
    r = S.GameRoom("FOTO")
    async def noop(*a, **k): pass
    r.broadcast = noop; r.send_to = noop; r.push_state = noop
    pids = pids or [f"p{i}" for i in range(len(classes))]
    for i, c in enumerate(classes):
        r.players[pids[i]] = S.make_player(pids[i], f"H{i}", c, i)
    r.player_order = list(r.players)
    r.phase = "city"; r.host_pid = pids[0]
    if arquivo:
        defn = S.carregar_dungeon(arquivo)
        if not defn:
            return None, "não carregou"
        ok, motivo = S.validar_dungeon(defn)
        if not ok:
            return None, motivo
        r.mode = "authored"; r.selected_dungeon = arquivo; r.dungeon_def = defn
    await r.enter_dungeon(pids[0])
    return r, None


async def secao_cobertura():
    print("\n[2] Todo atributo de GameRoom está classificado")
    cat = S.FOTO_SALA_CATEGORIAS
    check("categorias usadas são todas válidas",
          set(cat.values()) <= S.FOTO_CATEGORIAS_VALIDAS,
          sorted(set(cat.values()) - S.FOTO_CATEGORIAS_VALIDAS))
    da_classe = atributos_da_classe()
    r, _ = await sala_na_masmorra()
    da_sala = set(vars(r))
    # Os mocks deste teste (broadcast/send_to/push_state) viram atributos de
    # instância só aqui; na sala real são métodos.
    da_sala -= {"broadcast", "send_to", "push_state"}
    todos = da_classe | da_sala
    faltando = sorted(todos - set(cat))
    check(f"nenhum atributo sem categoria ({len(todos)} atributos)", not faltando,
          "classifique em FOTO_SALA_CATEGORIAS (server.py): " + ", ".join(faltando))
    # Entrada que não existe mais na sala é lixo — exceto as que a classe só cria
    # em situações específicas (sala de teste do editor).
    sobrando = sorted(set(cat) - todos - {"test_mode"})
    check("nenhuma entrada classificada sobrando", not sobrando, ", ".join(sobrando))
    check("há campos para a foto", len(S.foto_campos_sala("foto")) > 40)


async def secao_json_real():
    print("\n[3] Só JSON, em masmorras reais")
    pasta = os.path.join(RAIZ, "dungeons")
    arquivos = [None] + sorted(f for f in os.listdir(pasta) if f.endswith(".json"))
    campos = S.foto_campos_sala("foto") + S.foto_campos_sala("foto_pid")
    pulados = []
    for arq in arquivos:
        rotulo = arq or "procedural"
        r, motivo = await sala_na_masmorra(arq)
        if r is None:
            pulados.append(f"{rotulo} ({motivo})")
            continue
        foto = {"sala": {k: getattr(r, k) for k in campos if hasattr(r, k)},
                "herois": {p["class_id"]: p for p in r.players.values()}}
        try:
            volta, texto = ida_e_volta(foto)
        except S.FotoNaoSerializavel as e:
            check(f"{rotulo}: a foto cabe em JSON", False, str(e))
            continue
        iguais = volta == foto
        diff = ""
        if not iguais:
            for parte in ("sala", "herois"):
                for k in foto[parte]:
                    if volta[parte].get(k) != foto[parte][k]:
                        diff = f"{parte}.{k} mudou na ida e volta"; break
                if diff: break
        check(f"{rotulo}: ida e volta idêntica ({len(texto)//1024} KB)", iguais, diff)
    if pulados:
        print("  (masmorras que o validador recusa, puladas: " + "; ".join(pulados) + ")")


async def secao_gravacao():
    print("\n[4] Gravação da foto na virada de rodada")
    gravados = []
    S.write_savegame = lambda sg: gravados.append(sg.get("dungeon_snapshot"))
    S._agendar_descarga = lambda: None

    r, _ = await sala_na_masmorra("floresta_2.json")
    r.dungeon_intro_active = False
    check("sem jogo salvo, não grava", r._gravar_foto_rodada() is False and not gravados)

    r.savegame = {"id": "sg_teste"}
    check("com jogo salvo, grava", r._gravar_foto_rodada() is True and len(gravados) == 1)
    reg = r.savegame.get("dungeon_snapshot") or {}
    check("registro traz versão, rodada, masmorra e onde",
          reg.get("versao") == S.FOTO_VERSAO and reg.get("rodada") == r.round_num
          and reg.get("masmorra") == "floresta_2.json" and reg.get("onde") == "masmorra")
    check("a mesma foto fica em memória", r._ultima_foto is reg)
    check(f"comprimida cabe com folga ({len(reg.get('dados', ''))//1024} KB, era ~330 KB)",
          len(reg.get("dados", "")) < 64 * 1024)
    corpo = S.foto_desempacotar(reg)
    check("desempacota", isinstance(corpo, dict))
    if isinstance(corpo, dict):
        campos = S.foto_campos_sala("foto") + S.foto_campos_sala("foto_pid")
        check("campos da sala voltam idênticos",
              all(corpo["sala"].get(k) == getattr(r, k) for k in campos if hasattr(r, k)))
        check("ficha inteira de cada herói, chaveada pela classe",
              set(corpo["herois"]) == {p["class_id"] for p in r.players.values()}
              and all(corpo["herois"][p["class_id"]] == p for p in r.players.values()))
        check("mapa pid → classe para a retomada",
              corpo["pids"] == {pid: p["class_id"] for pid, p in r.players.items()})
        check("conexões e timers ficam de fora",
              not ({"connections", "initiative_task", "gm_log", "master_pid"} & set(corpo["sala"])))

    print("  — janelas pendentes adiam a foto —")
    for nome, valor in (("master_manual_mid", "m1"), ("last_stand_pid", "p0"),
                        ("sorte_reacao", {"pid": "p0"}), ("animados_phase_pid", "p0"),
                        ("dungeon_intro_active", True)):
        antes = len(gravados)
        setattr(r, nome, valor)
        check(f"{nome} aberto: não grava", r._gravar_foto_rodada() is False and len(gravados) == antes)
        setattr(r, nome, None if nome != "dungeon_intro_active" else False)
    p0 = r.players["p0"]
    p0["improviso_pendente"] = [{"passo": 7}]
    check("Improviso esperando alvo: não grava", r._gravar_foto_rodada() is False)
    p0["improviso_pendente"] = []
    check("janelas fechadas: volta a gravar", r._gravar_foto_rodada() is True)
    r.test_mode = True
    check("sala de teste do editor nunca grava", r._gravar_foto_rodada() is False)
    r.test_mode = False
    r.phase = "city"
    check("fora da masmorra, não grava", r._gravar_foto_rodada() is False)
    r.phase = "playing"

    print("  — foto ruim vira None, nunca erro —")
    check("versão desconhecida", S.foto_desempacotar(dict(reg, versao=999)) is None)
    check("dados corrompidos", S.foto_desempacotar(dict(reg, dados="não é base64!")) is None)
    check("ausente", S.foto_desempacotar(None) is None)

    print("  — integração: a virada real da rodada grava —")
    r2, _ = await sala_na_masmorra()
    r2.savegame = {"id": "sg_teste2"}
    r2.dungeon_intro_active = False
    r2._intro_masmorra_bloqueada = lambda: False
    rodada = r2.round_num
    gravados.clear()
    r2.initiative_index = len(r2.initiative_order) - 1
    await r2._advance_initiative()
    reg2 = r2.savegame.get("dungeon_snapshot") or {}
    check("rodada virou e a foto foi gravada com a rodada nova",
          r2.round_num == rodada + 1 and reg2.get("rodada") == rodada + 1 and len(gravados) == 1,
          f"rodada {rodada}->{r2.round_num}, foto {reg2.get('rodada')}, gravações {len(gravados)}")
    for t in (getattr(r2, "turn_timer_task", None), getattr(r2, "initiative_task", None)):
        if t and not t.done():
            t.cancel()


def _assinatura_monstros(r):
    return sorted((m["type"], tuple(m["pos"]), m["hp"]) for m in r.monsters.values())


async def jogar_e_salvar(arquivo, classe="warrior", pid_real=False):
    """Sala A: entra na masmorra, mexe no mundo e grava a foto. Devolve
    (sala, jogo_salvo) — o jogo salvo é o que iria para o disco. Com
    `pid_real`, o herói tem um pid no formato do jogo (id_N), como no servidor;
    sem ele, "p0" — exercitando a troca por casamento exato."""
    pid0 = S.new_id() if pid_real else "p0"
    r, _ = await sala_na_masmorra(arquivo, classes=(classe,), pids=[pid0])
    if pid_real:
        # Uma referência ao pid guardada num monstro (como fazem a memória da
        # IA e os alvos forçados) tem de acompanhar o pid novo na retomada.
        for m in list(r.monsters.values())[:1]:
            m["_ref_teste_pid"] = pid0
    r.savegame = {"id": "sg_retomar", "owner": "conta", "status": "active",
                  "members": {"conta": {"class_id": classe}}}
    r.dungeon_intro_active = False
    p = r.players[pid0]
    # Mexe em coisas que um recomeço desfaria: posição, vida, bolsa, névoa,
    # monstro ferido, baú esvaziado, item no chão, rodada.
    livres = [(x, y) for y in range(r.map_h) for x in range(r.map_w)
              if r.tiles[y][x] == S.FLOOR and not r._blocks_tile(x, y)
              and [x, y] != p["pos"] and not any([x, y] in r._monster_tiles(m) for m in r.monsters.values())]
    p["pos"] = list(livres[len(livres) // 2])
    p["hp"] = max(1, p["hp"] - 3)
    p["gold"] = 777
    r.explored |= {livres[0], livres[-1]}
    for m in list(r.monsters.values())[:1]:
        m["hp"] = max(1, m["hp"] - 2)
    for c in r.chests.values():
        c["gold"] = 0
        c["items"] = []
    r.ground_items["g_teste"] = {"id": "g_teste", "item": {"id": "pocao", "name": "Poção"},
                                 "pos": list(livres[1])}
    r.round_num = 7
    check(f"{arquivo or 'procedural'}: foto gravada na sala A", r._gravar_foto_rodada())
    return r, r.savegame


async def abrir_e_retomar(sg, classe="warrior", pid=None):
    """Sala B: servidor 'novo' — sala vazia, pid novo — abre o jogo salvo e
    inicia como o lobby faz."""
    r = S.GameRoom("RETOMA")
    enviados = []
    async def broadcast(msg, skip=None): enviados.append(msg)
    async def send_to(pid_, msg): enviados.append(msg)
    async def push_state(): enviados.append({"type": "game_state"})
    r.broadcast = broadcast; r.send_to = send_to; r.push_state = push_state
    r.savegame = sg
    r.savegame_id = sg.get("id")
    r._foto_pendente = sg.get("dungeon_snapshot")
    pid = pid or S.new_id()
    r.players[pid] = {"id": pid, "name": "Ana", "class_id": classe, "magias_conhecidas": []}
    r.host_pid = pid
    r.phase = "lobby"
    await r.start_game(pid)
    t = r.dungeon_intro_task
    if t and not t.done():
        t.cancel()
    return r, pid, enviados


async def secao_retomada():
    print("\n[5] Retomada da masmorra (solo)")
    import copy
    for arquivo, pid_real in (("amostra.json", False), ("campo_de_treinamento.json", True),
                              (None, True)):
        rotulo = (arquivo or "procedural") + (" (pid id_N)" if pid_real else " (pid p0)")
        a, sg = await jogar_e_salvar(arquivo, pid_real=pid_real)
        pa = next(iter(a.players.values()))
        ids_antigos = set(a.monsters) | set(a.chests) | set(a.players)
        b, pid, enviados = await abrir_e_retomar(copy.deepcopy(sg))
        pb = b.players.get(pid, {})
        check(f"{rotulo}: volta para DENTRO da masmorra", b.phase == "playing"
              and any(m.get("type") == "enter_dungeon" for m in enviados),
              f"fase {b.phase}")
        check(f"{rotulo}: na rodada salva", b.round_num == 7)
        check(f"{rotulo}: herói na casa, com a vida e o ouro salvos",
              pb.get("pos") == pa["pos"] and pb.get("hp") == pa["hp"] and pb.get("gold") == 777)
        check(f"{rotulo}: o herói usa o pid da conexão nova", pb.get("id") == pid)
        check(f"{rotulo}: mesma bolsa e equipamento",
              pb.get("bag") == pa.get("bag") and pb.get("gear") == pa.get("gear"))
        check(f"{rotulo}: monstros iguais (tipo, casa, vida)",
              _assinatura_monstros(b) == _assinatura_monstros(a))
        check(f"{rotulo}: baús esvaziados continuam vazios",
              all(c["gold"] == 0 and not c["items"] for c in b.chests.values())
              and len(b.chests) == len(a.chests))
        check(f"{rotulo}: item no chão continua lá",
              any(g["pos"] == a.ground_items["g_teste"]["pos"] for g in b.ground_items.values()))
        check(f"{rotulo}: névoa explorada igual", b.explored == a.explored)
        check(f"{rotulo}: mapa igual", b.tiles == a.tiles and b.map_w == a.map_w)
        novos = set(b.monsters) | set(b.chests) | set(b.ground_items)
        check(f"{rotulo}: nenhum id antigo sobrevive (ids renomeados)",
              not (novos & ids_antigos) and pid not in set(b.monsters) | set(b.chests))
        check(f"{rotulo}: índices derivados refeitos",
              b._decor_block_tiles == a._decor_block_tiles
              and b._mat_solid_tiles == a._mat_solid_tiles)
        check(f"{rotulo}: iniciativa montada com o herói novo",
              b.initiative_active and any(e["kind"] == "player" and e["id"] == pid
                                          for e in b.initiative_order))
        check(f"{rotulo}: transição de entrada ligada", b.dungeon_intro_active is True)
        refs = [m["_ref_teste_pid"] for m in b.monsters.values() if "_ref_teste_pid" in m]
        if pid_real and refs:
            check(f"{rotulo}: referência ao pid num monstro passa ao pid novo", refs == [pid])
        await b._liberar_intro_masmorra(False, retomada=True)
        check(f"{rotulo}: depois da transição alguém tem a vez", b.current_actor() is not None)
        chaves_log = [getattr(x, "key", None) for x in b.gm_log]
        check(f"{rotulo}: o log diz 'A aventura continua' e não 'descem novamente as escadas'",
              "narracao.a_aventura_continua" in chaves_log
              and "narracao.os_aventureiros_descem_novamente_as_esca" not in chaves_log, chaves_log[-3:])
        for t in (getattr(b, "turn_timer_task", None), getattr(b, "initiative_task", None)):
            if t and not t.done():
                t.cancel()

    print("  — quando a foto não serve, segue da cidade —")
    a, sg = await jogar_e_salvar("amostra.json")
    ruim = copy.deepcopy(sg)
    corpo = S.foto_desempacotar(ruim["dungeon_snapshot"])
    corpo["sala"]["map_w"] += 1          # como se o autor tivesse redimensionado o mapa
    ruim["dungeon_snapshot"] = S.foto_empacotar(corpo, onde="masmorra", rodada=7,
                                                masmorra="amostra.json")
    b, _, enviados = await abrir_e_retomar(ruim)
    check("masmorra editada: grupo na cidade", b.phase == "city")
    check("masmorra editada: foto descartada do jogo salvo", "dungeon_snapshot" not in ruim)
    check("masmorra editada: o grupo é avisado",
          any(m.get("type") == "error" and "foto_masmorra_descartada" in str(getattr(m.get("msg"), "key", ""))
              for m in enviados))

    estragado = copy.deepcopy(sg)
    estragado["dungeon_snapshot"]["dados"] = "lixo"
    b, _, _ = await abrir_e_retomar(estragado)
    check("foto corrompida: grupo na cidade, foto descartada",
          b.phase == "city" and "dungeon_snapshot" not in estragado)

    outro = copy.deepcopy(sg)
    b, _, _ = await abrir_e_retomar(outro, classe="rogue")
    check("herói diferente do salvo: cidade, foto mantida para o passo 5",
          b.phase == "city" and "dungeon_snapshot" in outro)

    print("  — masmorra encerrada não volta no próximo Continuar —")
    def fim_de_missao(r):
        r.dungeon_generated = False     # como handle_encerrar_missao faz antes
        return r._voltar_para_cidade()
    for rotulo, encerrar in (("fim de missão", fim_de_missao),
                             ("vitória", lambda r: r.end_game(True)),
                             ("derrota total", lambda r: r.end_game(False))):
        a, sg_fim = await jogar_e_salvar("amostra.json")
        a.broadcast_city_state = lambda: asyncio.sleep(0)
        await encerrar(a)
        check(f"{rotulo}: a foto sai do jogo salvo",
              "dungeon_snapshot" not in sg_fim and a._ultima_foto is None)

    print("  — abrir o jogo salvo pendura a foto para o start_game —")
    sg_disco = copy.deepcopy(sg)
    S.load_savegame = lambda sid: sg_disco
    rooms = {}
    sala, erro = S.try_open_savegame_room("conta", "sg_retomar", rooms)
    check("try_open_savegame_room guarda a foto em _foto_pendente",
          erro is None and sala._foto_pendente is sg_disco["dungeon_snapshot"], erro)
    S.SAVEGAMES_IN_USE.pop("sg_retomar", None)


class _WSFalso:
    def __init__(self): self.sent = []
    async def send(self, data): self.sent.append(json.loads(data))


async def grupo_salvo(arquivo="amostra.json"):
    """Sala A com guerreiro (conta 'ana') e ladino (conta 'bia') dentro da
    masmorra, em casas distintas; grava a foto. Devolve (sala, jogo_salvo,
    pids)."""
    pids = [S.new_id(), S.new_id()]
    r, _ = await sala_na_masmorra(arquivo, classes=("warrior", "rogue"), pids=pids)
    r.savegame = {"id": "sg_grupo", "owner": "ana", "status": "active",
                  "members": {"ana": {"class_id": "warrior"}, "bia": {"class_id": "rogue"}}}
    r.dungeon_intro_active = False
    livres = [[x, y] for y in range(r.map_h) for x in range(r.map_w)
              if r.tiles[y][x] == S.FLOOR and not r._blocks_tile(x, y)
              and not any([x, y] in r._monster_tiles(m) for m in r.monsters.values())]
    r.players[pids[0]]["pos"] = livres[0]
    r.players[pids[1]]["pos"] = livres[-1]
    r.players[pids[1]]["gold"] = 444
    for m in list(r.monsters.values())[:1]:
        m["_ref_teste_pid"] = pids[1]       # um monstro "lembra" do ladino
    r.round_num = 5
    assert r._gravar_foto_rodada()
    return r, r.savegame, pids


async def abrir_com(sg, presentes):
    """Sala B com os heróis `presentes` [(classe, nome)]; o 1º é o anfitrião."""
    r = S.GameRoom("RETOMA_GRUPO")
    async def broadcast(msg, skip=None): pass
    async def send_to(pid_, msg): pass
    async def push_state(): pass
    r.broadcast = broadcast; r.send_to = send_to; r.push_state = push_state
    r.savegame = sg; r.savegame_id = sg.get("id")
    r._foto_pendente = sg.get("dungeon_snapshot")
    pids = []
    for classe, nome in presentes:
        pid = S.new_id(); pids.append(pid)
        r.players[pid] = {"id": pid, "name": nome, "class_id": classe, "magias_conhecidas": []}
    r.host_pid = pids[0]; r.phase = "lobby"
    await r.start_game(pids[0])
    t = r.dungeon_intro_task
    if t and not t.done():
        t.cancel()
    return r, pids


def _cancelar_tarefas(r):
    for t in (getattr(r, "turn_timer_task", None), getattr(r, "initiative_task", None),
              getattr(r, "dungeon_intro_task", None)):
        if t and not t.done():
            t.cancel()


async def secao_grupo():
    print("\n[7] Grupo incompleto (passo 5)")
    import copy
    a, sg, pids_a = await grupo_salvo()
    casa_bia = list(a.players[pids_a[1]]["pos"])

    b, (pid_ana,) = await abrir_com(copy.deepcopy(sg), [("warrior", "Ana")])
    bia = next((p for p in b.players.values() if p.get("class_id") == "rogue"), None)
    check("só a Ana: a masmorra é retomada mesmo assim", b.phase == "playing" and bia is not None)
    if bia:
        check("a Bia ausente fica fora do tabuleiro e desconectada",
              bia["pos"] == [-1, -1] and bia.get("connected") is False and not b._ativo(bia))
        check("…lembrando a casa onde estava", bia.get("_pos_retomada") == casa_bia)
        check("…com a ficha salva (ouro 444)", bia.get("gold") == 444)
        check("…e a conta dela vinculada (para religar)", b.account_by_pid.get(bia["id"]) == "bia")
        check("a iniciativa só tem a Ana entre os heróis",
              [e["id"] for e in b.initiative_order if e["kind"] == "player"] == [pid_ana])
        refs = [m["_ref_teste_pid"] for m in b.monsters.values() if "_ref_teste_pid" in m]
        check("a lembrança do monstro aponta para o pid novo da Bia", refs == [bia["id"]], refs)
        ws = _WSFalso()
        pid_bia = await b.religar_heroi(bia, ws, S.new_id(), "Bia")
        check("a Bia chega e volta para a casa salva",
              pid_bia == bia["id"] and bia["pos"] == casa_bia and bia.get("connected") is True
              and "_pos_retomada" not in bia)
        check("…recebendo a tela da masmorra", any(m.get("type") == "enter_dungeon" for m in ws.sent))
        _cancelar_tarefas(b)

        # Na próxima foto (só a Ana jogando) a Bia vai ausente; no dia em que
        # as duas voltam, a Bia joga normalmente, na casa de antes.
        b2, (pa2,) = await abrir_com(copy.deepcopy(sg), [("warrior", "Ana")])
        b2.savegame = sg2 = copy.deepcopy(sg)
        b2.dungeon_intro_active = False   # a transição de 3 s terminou
        assert b2._gravar_foto_rodada()
        c, pids_c = await abrir_com(copy.deepcopy(sg2), [("warrior", "Ana"), ("rogue", "Bia")])
        bia_c = c.players[pids_c[1]]
        check("ausente numa foto, presente depois: joga, na casa salva",
              bia_c.get("connected") is True and bia_c["pos"] == casa_bia
              and c._ativo(bia_c) and "_pos_retomada" not in bia_c)
        _cancelar_tarefas(b2); _cancelar_tarefas(c)

    # Ocupada: alguém está na casa salva quando ela volta.
    b, _ = await abrir_com(copy.deepcopy(sg), [("warrior", "Ana")])
    bia = next(p for p in b.players.values() if p.get("class_id") == "rogue")
    ana = next(p for p in b.players.values() if p.get("class_id") == "warrior")
    ana["pos"] = list(casa_bia)
    await b.religar_heroi(bia, _WSFalso(), S.new_id(), "Bia")
    check("casa salva ocupada: volta na casa livre ao lado",
          bia["pos"] != casa_bia and max(abs(bia["pos"][0] - casa_bia[0]),
                                         abs(bia["pos"][1] - casa_bia[1])) <= 1)
    _cancelar_tarefas(b)

    # Quem não estava na foto chega como quem subiu a escada.
    b, pids_b = await abrir_com(copy.deepcopy(sg), [("warrior", "Ana"), ("paladin", "Caio")])
    caio = b.players[pids_b[1]]
    check("herói novo (não estava na foto): fica na cidade e desce na próxima rodada",
          b.phase == "playing" and caio["pos"] == [-1, -1]
          and caio.get("fora_masmorra") == {"rodadas_restantes": 0})
    _cancelar_tarefas(b)

    # Ninguém da foto presente: a masmorra espera.
    sg_so_caio = copy.deepcopy(sg)
    b, _ = await abrir_com(sg_so_caio, [("paladin", "Caio")])
    check("ninguém da foto presente: grupo na cidade e a foto fica guardada",
          b.phase == "city" and "dungeon_snapshot" in sg_so_caio)

    # Caído na sessão anterior (na foto: fora do tabuleiro, desconectado).
    a.players[pids_a[1]]["connected"] = False
    a.players[pids_a[1]]["pos"] = [-1, -1]
    assert a._gravar_foto_rodada()
    b, pids_b = await abrir_com(copy.deepcopy(a.savegame), [("warrior", "Ana"), ("rogue", "Bia")])
    bia = b.players[pids_b[1]]
    check("estava caído na foto e está presente: conectado, desce pela escada",
          bia.get("connected") is True and bia.get("fora_masmorra") == {"rodadas_restantes": 0})
    _cancelar_tarefas(b)


async def secao_handler_real():
    print("\n[6] Pelo laço de conexão real: entrar → Continuar → dentro da masmorra")
    import shutil, tempfile
    import test_continuar_jogo as C
    for nome, fn in _ORIGINAIS.items():
        setattr(S, nome, fn)
    tmp = tempfile.mkdtemp()
    velha = S.LOJA
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(tmp)); S.LOJA.carregar()
    try:
        acc, e = await S.create_account("foto_solo", C.SENHA)
        assert acc, e
        sid, _, _ = await C.criar_jogo("foto_solo", "Fotografia", "warrior")
        C.limpar_salas()
        # Uma sala procedural com o mesmo herói tira a foto (como se o grupo
        # tivesse jogado até a rodada 7 e fechado o jogo).
        a, _ = await sala_na_masmorra(None, classes=("warrior",), pids=[S.new_id()])
        heroi = next(iter(a.players.values()))
        heroi["gold"] = 555
        a.round_num = 7
        sg = S.load_savegame(sid)
        a.savegame = sg
        a.dungeon_intro_active = False
        check("foto gravada no jogo salvo de verdade", a._gravar_foto_rodada())
        a.savegame = None

        async def esperar_masmorra():
            await C.esperar(lambda: C.sala_do_jogo(sid) and C.sala_do_jogo(sid).phase == "playing")
        ws = C.FakeWS([C.login("foto_solo"), {"type": "load_savegame", "id": sid}, esperar_masmorra])
        await S.handler(ws)
        r = C.sala_do_jogo(sid)
        check("sem tela de herói (lobby só com auto_start)",
              all(l.get("auto_start") for l in ws.msgs("lobby_state")))
        check("recebeu enter_dungeon, não a cidade",
              bool(ws.msgs("enter_dungeon")) and not ws.msgs("city_state"),
              [m.get("type") for m in ws.msgs()][:12])
        gs = ws.msgs("game_state")
        eu = next((p for p in (gs[-1].get("players") if gs else []) if p.get("class_id") == "warrior"), {})
        check("game_state na rodada salva, com a ficha da foto (ouro 555)",
              gs and gs[-1].get("round") in (7, None) and eu.get("gold") == 555
              and r is not None and r.round_num == 7, (eu.get("gold"), r and r.round_num))
        check("o log diz que a aventura continua",
              any("aventura continua" in str(x) for x in (gs[-1].get("gm_log") if gs else [])))
        check("sem erro interno", C.sem_erro_interno(ws), ws.erros())
    finally:
        C.limpar_salas()
        S.LOJA = velha
        shutil.rmtree(tmp, ignore_errors=True)


async def secao_cidade_com_masmorra():
    print("\n[8] Cidade com a masmorra aberta (passo 6)")
    import copy
    for arquivo in ("amostra.json", None):
        rotulo = arquivo or "procedural"
        a, sg = await jogar_e_salvar(arquivo)
        morto = next(iter(a.monsters))
        del a.monsters[morto]                       # um monstro já morreu
        sig = _assinatura_monstros(a)
        chao = dict(a.ground_items)
        a.broadcast_city_state = lambda: asyncio.sleep(0)
        await a._voltar_para_cidade()               # todos subiram a escada
        foto = sg.get("dungeon_snapshot") or {}
        check(f"{rotulo}: volta à cidade grava a foto 'cidade_com_masmorra'",
              foto.get("onde") == "cidade_com_masmorra" and a._ultima_foto is None,
              foto.get("onde"))
        corpo = S.foto_desempacotar(foto) or {}
        check(f"{rotulo}: a foto da cidade não leva fichas (o checkpoint as grava)",
              corpo.get("herois") == {} and corpo.get("pids"))

        b, pid, enviados = await abrir_e_retomar(copy.deepcopy(sg))
        tipos = [m.get("type") for m in enviados]
        check(f"{rotulo}: Continuar abre na cidade, com a masmorra em memória",
              b.phase == "city" and b.dungeon_generated and "enter_dungeon" not in tipos,
              (b.phase, b.dungeon_generated, tipos))
        check(f"{rotulo}: monstro morto continua morto, os outros iguais",
              _assinatura_monstros(b) == sig and len(b.monsters) == len(sig))
        check(f"{rotulo}: item no chão e baús esvaziados voltam",
              sorted(i["pos"] for i in b.ground_items.values())
              == sorted(i["pos"] for i in chao.values())
              and all(not c.get("items") and not c.get("gold") for c in b.chests.values()))
        check(f"{rotulo}: a foto fica no jogo salvo até o grupo entrar",
              b.savegame.get("dungeon_snapshot", {}).get("onde") == "cidade_com_masmorra")

        b.world_location = "alva_e_luz"
        await b.enter_dungeon(pid)
        _cancelar_tarefas(b)
        check(f"{rotulo}: entrar retoma a MESMA masmorra (não gera outra)",
              b.phase == "playing" and _assinatura_monstros(b) == sig,
              (b.phase, len(b.monsters), len(sig)))

    print("  — partir para outro destino abandona a masmorra aberta —")
    a, sg = await jogar_e_salvar("amostra.json")
    a.broadcast_city_state = lambda: asyncio.sleep(0)
    await a._voltar_para_cidade()
    fonte = open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
    ini = fonte.index("async def handle_world_adventure")
    trecho = fonte[ini:fonte.index("async def ", ini + 10)]
    check("handle_world_adventure apaga a foto ao zerar dungeon_generated",
          "self.dungeon_generated = False" in trecho and "self._apagar_foto()" in trecho)

    print("  — foto da cidade de masmorra alterada é descartada —")
    a, sg = await jogar_e_salvar("amostra.json")
    a.broadcast_city_state = lambda: asyncio.sleep(0)
    await a._voltar_para_cidade()
    corpo = S.foto_desempacotar(sg["dungeon_snapshot"])
    corpo["sala"]["map_w"] = corpo["sala"]["map_w"] + 3
    sg["dungeon_snapshot"] = S.foto_empacotar(corpo, onde="cidade_com_masmorra",
                                              rodada=1, masmorra="amostra.json")
    b, _, enviados = await abrir_e_retomar(sg)
    check("grade mudou: cidade sem masmorra aberta e foto descartada com aviso",
          b.phase == "city" and not b.dungeon_generated
          and "dungeon_snapshot" not in sg
          and any(m.get("type") == "error" for m in enviados))


async def secao_cliente_e_saida():
    print("\n[9] Meus Jogos, Salvar e sair e herói que caiu (passo 7)")
    import copy, re as _re
    # — resumo da foto no cartão —
    a, sg = await jogar_e_salvar("amostra.json")
    nome = (S.carregar_dungeon("amostra.json") or {}).get("name")
    res = S._resumo_foto(sg["dungeon_snapshot"])
    check("resumo da foto: onde, rodada e nome legível da masmorra",
          res and res["onde"] == "masmorra" and res["rodada"] == 7 and res["masmorra"] == nome, res)
    check("sem foto, o cartão não ganha linha", S._resumo_foto(None) is None)
    a.broadcast_city_state = lambda: asyncio.sleep(0)
    await a._voltar_para_cidade()
    res = S._resumo_foto(sg["dungeon_snapshot"])
    check("resumo da cidade com masmorra aberta",
          res and res["onde"] == "cidade_com_masmorra" and res["masmorra"] == nome, res)
    fonte = open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
    ini = fonte.index("def list_savegames")
    check("list_savegames manda o resumo da foto",
          '"foto": _resumo_foto(sg.get("dungeon_snapshot"))' in fonte[ini:ini + 2500])

    # — Salvar e sair —
    a, sg = await jogar_e_salvar("amostra.json")
    pid = next(iter(a.players))
    enviados = []
    async def send_to(p_, msg): enviados.append(msg)
    a.send_to = send_to
    check("game_state avisa que há jogo salvo", a._game_state_payload().get("tem_jogo_salvo") is True)
    a._ultima_foto = None
    sg.pop("dungeon_snapshot", None)
    await a.handle_salvar_e_sair(pid)
    resp = [m for m in enviados if m.get("type") == "salvo_para_sair"]
    check("na masmorra sem foto ainda: grava a da rodada e confirma",
          resp and resp[0]["onde"] == "masmorra" and resp[0]["rodada"] == 7
          and sg.get("dungeon_snapshot", {}).get("onde") == "masmorra", resp)
    sem = S.GameRoom("SEMSG")
    msgs = []
    async def st2(p_, msg): msgs.append(msg)
    sem.send_to = st2
    await sem.handle_salvar_e_sair("x")
    check("partida sem jogo salvo: recusa", msgs and msgs[0].get("type") == "error"
          and sem._city_state_payload().get("tem_jogo_salvo") is False)

    # — herói que cai guarda a casa; sem ninguém conectado a foto congela —
    a, sg = await jogar_e_salvar("amostra.json")
    pid = next(iter(a.players)); p = a.players[pid]
    casa = list(p["pos"])
    foto_antes = sg["dungeon_snapshot"]
    async def nada(*x, **k): pass
    a._forcar_fim_turno = nada
    await a.handle_disconnect_em_jogo(pid)
    check("ao cair na masmorra, o herói guarda a casa (_pos_ao_cair)",
          p["pos"] == [-1, -1] and p.get("_pos_ao_cair") == casa)
    a.round_num = 8
    check("solo saiu: a virada não regrava a foto",
          a._gravar_foto_rodada() is False and sg["dungeon_snapshot"] is foto_antes)
    b, _, _ = await abrir_e_retomar(copy.deepcopy(sg))
    pb = next(iter(b.players.values()))
    check("Continuar devolve o herói à casa onde estava", pb["pos"] == casa and "_pos_ao_cair" not in pb)

    # — grupo: um cai, a foto seguinte o guarda fora do mapa, mas com a casa —
    a, sg, pids = await grupo_salvo()
    casa_b = list(a.players[pids[1]]["pos"])
    a._forcar_fim_turno = nada
    await a.handle_disconnect_em_jogo(pids[1])
    a.round_num = 6
    check("grupo: com alguém conectado a foto segue gravando", a._gravar_foto_rodada())
    b, bp = await abrir_com(copy.deepcopy(sg), [("warrior", "Ana"), ("rogue", "Bia")])
    _cancelar_tarefas(b)
    check("grupo: quem tinha caído volta na casa em que caiu (não pela escada)",
          b.players[bp[1]]["pos"] == casa_b and not b.players[bp[1]].get("fora_masmorra"),
          (b.players[bp[1]]["pos"], casa_b))
    b, bp = await abrir_com(copy.deepcopy(sg), [("warrior", "Ana")])
    _cancelar_tarefas(b)
    ausente = next(q for q in b.players.values() if q.get("class_id") == "rogue")
    check("grupo: ausente que tinha caído fica com a casa para religar",
          ausente.get("_pos_retomada") == casa_b and "_pos_ao_cair" not in ausente)

    # — rejoin na mesma sessão continua pela escada —
    ini = fonte.index("async def religar_heroi")
    check("religar_heroi descarta _pos_ao_cair (só a retomada a usa)",
          'alvo.pop("_pos_ao_cair", None)' in fonte[ini:ini + 900])

    # — cliente —
    js = open(os.path.join(RAIZ, "game.js"), encoding="utf-8").read()
    gs = open(os.path.join(RAIZ, "src", "gameState.js"), encoding="utf-8").read()
    check("⚙️ tem o botão Salvar e sair, condicionado a tem_jogo_salvo",
          'id="cfg-salvar-sair"' in js and "tem_jogo_salvo" in js)
    check("um único ouvinte de salvoParaSair (GS.on substitui o anterior)",
          len(_re.findall(r"GS\.on\('salvoParaSair'", js)) == 1)
    check("gameState: salvarESair exportado e salvo_para_sair tratado",
          "function salvarESair()" in gs and "case 'salvo_para_sair':" in gs and "    salvarESair," in gs)
    check("cartão de Meus Jogos mostra onde parou", "_ondeParouHTML(sg.foto)" in js)
    check("painel de jogadores marca o herói ausente", "ui.hud.aguardando_jogador" in js)
    chaves = ("ui.menu.salvar_sair", "ui.save.salvar_sair_confirm_cidade",
              "ui.save.salvar_sair_confirm_masmorra", "ui.save.salvo_saindo",
              "ui.save.foto_masmorra", "ui.save.foto_cidade", "ui.save.masmorra_generica",
              "ui.hud.aguardando_jogador", "erro.esta_partida_nao_tem_jogo_salvo")
    faltam = [k for k in chaves if not (S.LANG_STRINGS.get(k, {}).get("pt") and S.LANG_STRINGS.get(k, {}).get("en"))]
    check("chaves novas com pt e en", not faltam, faltam)


async def secao_mestre():
    print("\n[10] Retomada com Mestre humano")
    hp, mp = S.new_id(), S.new_id()
    a, _ = await sala_na_masmorra(None, classes=("warrior",), pids=[hp])
    a.master_pid, a.master_name = mp, "Mestre"
    a.connections[mp] = object()
    a.savegame = {"id": "sg_mestre", "owner": "mestre", "status": "active", "has_master": True,
                  "master_account": "mestre", "members": {"ana": {"class_id": "warrior"}}}
    a.dungeon_intro_active = False
    mons = list(a.monsters.values())
    check("amostra tem 2+ monstros", len(mons) >= 2, len(mons))
    mons[0].update(control_mode="manual", alertado=True)
    mons[1].update(control_mode="semi", alertado=True, master_target_id=hp)
    a.master_reserve = {"goblin": 2}
    a.round_num = 3
    check("grava com Mestre na sala", a._gravar_foto_rodada())
    corpo = S.foto_desempacotar(a.savegame["dungeon_snapshot"])
    check("Mestre não entra nas fichas da foto", set(corpo["herois"]) == {"warrior"},
          sorted(corpo["herois"]))
    check("pid do Mestre não vira herói no mapa de pids", mp not in corpo["pids"])
    _cancelar_tarefas(a)

    b = S.GameRoom("RETOMA_MESTRE")
    async def noop(*x, **k): pass
    b.broadcast = noop; b.send_to = noop; b.push_state = noop
    b.savegame = a.savegame; b.savegame_id = "sg_mestre"
    b._foto_pendente = a.savegame["dungeon_snapshot"]
    mp2, hp2 = S.new_id(), S.new_id()
    b.players[mp2] = {"id": mp2, "name": "Mestre", "class_id": None, "is_master": True,
                      "ready": True, "connected": True, "slot": 0}
    b.players[hp2] = {"id": hp2, "name": "Ana", "class_id": "warrior", "magias_conhecidas": []}
    b.connections[mp2] = object(); b.connections[hp2] = object()
    b.host_pid = mp2; b.phase = "lobby"
    await b.start_game(mp2)
    _cancelar_tarefas(b)
    check("retomou dentro da masmorra", b.phase == "playing" and b.round_num == 3,
          (b.phase, b.round_num))
    check("Mestre religado pelo pid novo", b.master_pid == mp2 and b._mestre_ativo(), b.master_pid)
    check("Mestre fora de players", mp2 not in b.players and list(b.players) == [hp2],
          list(b.players))
    ordem = [e.get("id") if isinstance(e, dict) else e for e in b.initiative_order]
    check("Mestre fora da iniciativa", mp2 not in ordem)
    novos = {m.get("type"): m for m in b.monsters.values()}
    modos = sorted(m.get("control_mode", "auto") for m in b.monsters.values())
    check("modos dos monstros preservados", modos.count("manual") >= 1 and modos.count("semi") >= 1,
          modos)
    semi = next(m for m in b.monsters.values() if m.get("control_mode") == "semi")
    check("alvo do Semi aponta para o herói da sessão nova", semi.get("master_target_id") == hp2,
          semi.get("master_target_id"))
    check("monstros acordados continuam acordados",
          all(m.get("alertado") for m in b.monsters.values() if m.get("control_mode") in ("manual", "semi")),
          [(m.get("type"), m.get("control_mode"), m.get("alertado")) for m in b.monsters.values() if m.get("control_mode")])
    check("reserva de reforços preservada", b.master_reserve == {"goblin": 2}, b.master_reserve)
    check("Mestre sem janela Manual pendurada da sessão velha", not b.master_manual_mid)


async def main():
    secao_codec()
    await secao_cobertura()
    await secao_json_real()
    await secao_gravacao()
    await secao_retomada()
    await secao_grupo()
    await secao_cidade_com_masmorra()
    await secao_cliente_e_saida()
    await secao_mestre()
    await secao_handler_real()
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    return FAIL


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
