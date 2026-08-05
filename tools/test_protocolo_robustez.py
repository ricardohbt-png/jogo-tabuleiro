"""Robustez do dispatcher WebSocket contra mensagens malformadas.

Um cliente alterado (ou com bug) pode mandar qualquer JSON. Duas garantias:

1. **A conexão nunca cai.** `t = msg.get("type")` ficava FORA do try interno, então
   um JSON válido mas não-objeto (`5`, `[]`, `"x"`, `null`) levantava AttributeError
   que escapava do catch-all e derrubava o WebSocket daquele jogador.
2. **Nenhum "Erro interno".** Campos usados como índice (`int(...)` cru) ou como
   CHAVE de dict (`x in self.monsters` com um `{}` → 'unhashable type') estouravam
   e viravam a mensagem inútil "Erro interno: TypeError" para o jogador.

Roda da raiz: python tools/test_protocolo_robustez.py
"""
import asyncio
import collections
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


class FakeWS:
    """Websocket de mentira: entrega as mensagens e guarda o que foi enviado."""
    remote_address = ("127.0.0.1", 1)

    def __init__(self, msgs):
        self.msgs = msgs
        self.sent = []

    def __aiter__(self):
        async def gen():
            for m in self.msgs:
                yield m
        return gen()

    async def send(self, data):
        self.sent.append(data)

    async def close(self, *a, **k):
        pass


def tipos_do_dispatcher():
    """Lê os `t == "..."` do dispatcher para cobrir TODO o protocolo — assim uma
    mensagem nova entra na varredura sozinha, sem ninguém lembrar de atualizar."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(base, "server.py"), encoding="utf-8", errors="replace").read()
    ini = src.index('            t = msg.get("type")')
    fim = src.index('            except Exception as e:', ini)
    return sorted(set(re.findall(r't == "([a-z_]+)"', src[ini:fim])))


# Valores hostis: não-hashable (chave de dict), não-numérico (índice),
# não-string (nome de arquivo) e path traversal.
MALFORMADOS = [{}, [], "xxx", -1, 99999, None, True, {"a": 1}, [1, 2], 3.7,
               "", "../../etc/passwd", {"x": {"y": [1]}}]

# Campos que o dispatcher lê e repassa aos handlers.
CAMPOS = ["target_id", "item_id", "monster_id", "chest_id", "ground_id", "index",
          "tx", "ty", "slot_index", "from_index", "to_index", "slot", "slot_key",
          "decor_id", "class_id", "skill_id", "tecnica_id", "magia_id", "animado_id",
          "adventure_id", "shop", "source", "fala_id", "maldicao_id", "monster_ids",
          "dx", "dy", "code", "name", "vote_id", "data", "kind", "points", "buffs",
          "target_pos", "dir", "atributos"]


async def main():
    print("\n[1] JSON válido mas não-objeto não derruba a conexão")
    ws = FakeWS(['5', '[]', '"oi"', 'null', 'true', '3.7', '{"type":"ping"}'])
    caiu = None
    try:
        await S.handler(ws)
    except Exception as e:
        caiu = f"{type(e).__name__}: {e}"
    check(f"handler sobrevive a 5 / [] / \"oi\" / null / true{'' if not caiu else ' — ' + caiu}",
          caiu is None)

    print("\n[2] JSON inválido (nem parseia) é ignorado")
    ws = FakeWS(['{', 'nao é json', ''])
    caiu = None
    try:
        await S.handler(ws)
    except Exception as e:
        caiu = f"{type(e).__name__}: {e}"
    check("handler sobrevive a lixo não-JSON", caiu is None)

    print("\n[3] Varredura: todo tipo de mensagem × valores malformados")
    tipos = tipos_do_dispatcher()
    check(f"dispatcher expõe muitos tipos ({len(tipos)})", len(tipos) > 100)

    # Preâmbulos: sem eles a varredura passa à toa. A maioria dos ramos é
    # `if room: await room.handle_x(...)` — sem sala o curto-circuito impede que
    # o handler seja alcançado. E os handlers de combate saem cedo no `_is_turn`,
    # então só uma partida em "playing" chega às buscas por id.
    PREAMBULOS = {
        "pré-lobby (sem sala)": [],
        "com sala (lobby)": [{"type": "create_room", "name": "H"}],
        "em partida (playing)": [{"type": "create_room", "name": "H"},
                                 {"type": "select_class", "class_id": "warrior"},
                                 {"type": "start_game"},
                                 {"type": "enter_dungeon"}],
    }

    async def varrer(preambulo):
        derrubadas = []
        internos = collections.OrderedDict()
        total = 0
        for t in tipos:
            for v in MALFORMADOS:
                total += 1
                msgs = [json.dumps(m) for m in preambulo]
                msgs.append(json.dumps({"type": t, **{c: v for c in CAMPOS}}))
                ws = FakeWS(msgs)
                try:
                    await S.handler(ws)
                except Exception as e:
                    derrubadas.append((t, repr(v)[:16], type(e).__name__))
                    continue
                if any('"Erro interno' in x for x in ws.sent):
                    internos.setdefault(t, repr(v)[:16])
        return total, derrubadas, internos

    for rotulo, preambulo in PREAMBULOS.items():
        total, derrubadas, internos = await varrer(preambulo)
        print(f"      [{rotulo}] {total} mensagens: {len(tipos)} tipos × {len(MALFORMADOS)} valores")
        check(f"{rotulo}: nenhuma mensagem derruba a conexão", derrubadas == [])
        if derrubadas:
            print(f"      derrubaram: {derrubadas[:5]}")
        check(f"{rotulo}: nenhuma mensagem produz 'Erro interno'", not internos)
        if internos:
            print(f"      com erro interno: {list(internos.items())[:8]}")

    print("\n[4] Trocar de sala na mesma conexão não vaza a trava de personagem")
    # A limpeza do `finally` só conhece a sala apontada por `room`. Um segundo
    # create_room na MESMA conexão sobrescrevia essa referência e deixava o
    # personagem preso em CHARACTERS_IN_USE para SEMPRE — indisponível para
    # todos os jogadores até reiniciar o servidor.
    preambulo = [{"type": "create_room", "name": "H"},
                 {"type": "select_class", "class_id": "warrior"},
                 {"type": "start_game"}]
    S.CHARACTERS_IN_USE.clear()
    ws = FakeWS([json.dumps(m) for m in preambulo]
                + [json.dumps({"type": "create_room", "name": "H2"})])
    await S.handler(ws)
    check("trava liberada ao fim da conexão", dict(S.CHARACTERS_IN_USE) == {})
    check("2ª sala na mesma conexão é recusada",
          any("já está em uma sala" in json.loads(x).get("msg", "") for x in ws.sent))
    # E o personagem continua utilizável depois disso.
    ws = FakeWS([json.dumps(m) for m in preambulo])
    await S.handler(ws)
    check("personagem continua disponível para a próxima sala",
          any(json.loads(x).get("type") == "game_start" for x in ws.sent))

    print("\n[5] Ids não-hashable nos handlers de combate (turno forçado)")
    # A varredura NÃO alcança `handle_attack`: logo após `enter_dungeon` a
    # iniciativa costuma estar num monstro, então o handler sai cedo no
    # `_is_turn` e a busca por id nem roda. Aqui posicionamos a iniciativa no
    # herói para exercitar de fato o caminho que o `_key` protege.
    from server import GameRoom, make_player

    async def sala_em_turno():
        r = GameRoom("HASH")
        async def noop(*a, **k): pass
        r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
        r.broadcast_city_state = noop; r.broadcast_lobby = noop
        r.phase = "playing"
        r.map_w = r.map_h = 10
        r.tiles = [[S.FLOOR] * 10 for _ in range(10)]
        r.rooms = []; r.monsters = {}; r.chests = {}; r.ground_items = {}
        r.decorations = []; r.materiais = {}
        p = make_player("h", "Vic", "warrior", 0)
        p["pos"] = [2, 2]; p["alive"] = True
        r.players["h"] = p; r.player_order = ["h"]; r.host_pid = "h"
        r.current_pid = lambda: "h"          # é a vez do herói
        return r, p

    # `_key` transforma o valor não-hashable em None ANTES do handler; simulamos
    # o dispatcher chamando com S._key(...), como o código real faz.
    for rotulo, valor in (("dict", {}), ("lista", [1, 2])):
        r, p = await sala_em_turno()
        erro = None
        try:
            await r.handle_attack("h", S._key(valor))
            await r.handle_pickup_item("h", S._key(valor))
            await r.handle_take_from_chest("h", S._key(valor), "gold", 0)
        except Exception as e:
            erro = f"{type(e).__name__}: {e}"
        check(f"target/ground/chest_id como {rotulo}: sem exceção"
              + (f" — {erro}" if erro else ""), erro is None)

    # E a prova de que o `_key` é mesmo necessário: sem ele, estoura.
    r, p = await sala_em_turno()
    cru = None
    try:
        await r.handle_attack("h", {})
    except Exception as e:
        cru = type(e).__name__
    check("sem _key o handler realmente estouraria (TypeError)", cru == "TypeError")

    # A varredura não consegue exercitar a LINHA do dispatcher que despacha
    # `attack` (o turno é do monstro). Como o handler acima prova que o id cru
    # estoura, conferimos por leitura que o despacho aplica o `_key` — sem isto,
    # remover a guarda passaria despercebido.
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(base, "server.py"), encoding="utf-8", errors="replace").read()
    ini = src.index('            t = msg.get("type")')
    fim = src.index('            except Exception as e:', ini)
    despacho = src[ini:fim]
    for handler, campo in (("handle_attack", "target_id"),
                           ("handle_pickup_item", "ground_id"),
                           ("handle_take_from_chest", "chest_id")):
        linhas = despacho.splitlines()
        i = next((n for n, l in enumerate(linhas) if f"room.{handler}(" in l), None)
        # A chamada pode quebrar em várias linhas (take_from_chest quebra), então
        # olhamos a linha do despacho e as 2 seguintes.
        trecho = "".join(linhas[i:i + 3]) if i is not None else ""
        check(f"despacho de {handler} protege {campo} com _key",
              f'_key(msg.get("{campo}"))' in trecho)

    print("\n[6] Helpers de coerção")
    check("_num converte texto numérico", S._num("7") == 7)
    check("_num usa o padrão em lixo", S._num({}) == -1 and S._num("x") == -1)
    check("_num respeita o padrão informado", S._num(None, 0) == 0)
    check("_key deixa passar id normal", S._key("m1") == "m1")
    check("_key anula valor não-hashable", S._key({}) is None and S._key([1]) is None)
    check("_delta continua limitando a 1 casa", S._delta(50) == 1 and S._delta(-9) == -1)
    check("_delta zera lixo", S._delta("x") == 0 and S._delta(None) == 0)

    print(f"\n{'='*52}\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    asyncio.run(main())
