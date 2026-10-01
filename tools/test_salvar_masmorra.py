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


async def sala_na_masmorra(arquivo=None, classes=("warrior", "mage", "rogue")):
    r = S.GameRoom("FOTO")
    async def noop(*a, **k): pass
    r.broadcast = noop; r.send_to = noop; r.push_state = noop
    for i, c in enumerate(classes):
        r.players[f"p{i}"] = S.make_player(f"p{i}", f"H{i}", c, i)
    r.phase = "city"; r.host_pid = "p0"
    if arquivo:
        defn = S.carregar_dungeon(arquivo)
        if not defn:
            return None, "não carregou"
        ok, motivo = S.validar_dungeon(defn)
        if not ok:
            return None, motivo
        r.mode = "authored"; r.selected_dungeon = arquivo; r.dungeon_def = defn
    await r.enter_dungeon("p0")
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


async def main():
    secao_codec()
    await secao_cobertura()
    await secao_json_real()
    await secao_gravacao()
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    return FAIL


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
