"""Treinamento + Solo com grupo: o baú de provisões mostra a cota de CADA herói da conexão.
Roda da raiz: python -X utf8 tools/test_provisoes_solo_grupo.py"""
import asyncio, json, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

FALHAS = []
def check(n, c):
    print(("  ✅ " if c else "  ❌ ") + n)
    if not c: FALHAS.append(n)

class WS:
    def __init__(self): self.msgs = []
    async def send(self, data): self.msgs.append(data)

async def main():
    r = S.GameRoom("PRV"); r.phase = "playing"
    d = json.load(open(os.path.join(RAIZ, "dungeons", "Arena.json"), encoding="utf-8"))
    r.load_authored_dungeon(d)
    r.connections["c0"] = WS()
    a = S.make_player("c0", "Ana", "warrior", 0); a["pos"] = [2, 2]
    b = S.make_player("h1", "Bia", "mage", 1); b["pos"] = [3, 2]; b["controlador"] = "c0"
    r.players["c0"], r.players["h1"] = a, b
    r.training_mode = True
    r.chests.clear()
    r.chests["c1"] = {"id": "c1", "pos": [3, 3], "gold": 0, "opened": False,
                      "items": [{"id": "banquete_viagem", "tutorial_provision": True} for _ in range(4)]}
    # a 1ª heroína já pegou toda a cota dela (2 banquetes)
    r._tutorial_provision_register("c0", {"id": "banquete_viagem", "tutorial_provision": True})
    r._tutorial_provision_register("c0", {"id": "banquete_viagem", "tutorial_provision": True})
    await r.push_state()
    bau = json.loads(r.connections["c0"].msgs[-1])["chests"][0]["items"]
    check("para a heroína 1 a cota acabou", all(i["tutorial_hidden"] for i in bau))
    por = [i["tutorial_hidden_por_heroi"] for i in bau]
    check("herói 1 (conexão) oculto", all(m["c0"] is True for m in por))
    check("herói 2 ainda vê a cota (2 itens)", sum(1 for m in por if m["h1"] is False) == 2)

async def armas():
    r = S.GameRoom("PRW"); r.phase = "playing"
    d = json.load(open(os.path.join(RAIZ, "dungeons", "Arena.json"), encoding="utf-8"))
    r.load_authored_dungeon(d)
    r.connections["c0"] = WS()
    a = S.make_player("c0", "Ana", "warrior", 0); a["pos"] = [2, 2]
    b = S.make_player("h1", "Bia", "mage", 1); b["pos"] = [3, 2]; b["controlador"] = "c0"
    r.players["c0"], r.players["h1"] = a, b
    r.training_mode = True
    r.chests.clear()
    r.chests["c1"] = {"id": "c1", "pos": [3, 3], "gold": 0, "opened": False,
                      "items": [{"id": "espada", "tutorial_class": "warrior"}, {"id": "adaga", "tutorial_class": "mage"}]}
    await r.push_state()
    it = json.loads(r.connections["c0"].msgs[-1])["chests"][0]["items"]
    check("arma da guerreira: oculta p/ maga, visível p/ ela", it[0]["tutorial_hidden_por_heroi"] == {"c0": False, "h1": True})
    check("arma da maga: visível p/ ela", it[1]["tutorial_hidden_por_heroi"] == {"c0": True, "h1": False})

asyncio.run(main())
asyncio.run(armas())
print(f"\n{'OK' if not FALHAS else 'FALHOU: ' + str(FALHAS)}")
sys.exit(1 if FALHAS else 0)
