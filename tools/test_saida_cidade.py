"""Saída pela escada: a cidade abre ao sair e a espera só conta depois de
clicar em "Voltar à masmorra".

- Multiplayer: a masmorra não para. Na cidade, a vez do herói é pulada; ao
  clicar em voltar começa a espera; ao terminar, ele reaparece sozinho.
- Solo (jogo salvo de um jogador, com um ou mais heróis): a masmorra fica
  parada na vez de quem saiu enquanto ele compra; ao clicar em voltar a vez
  dele acaba e a espera começa.
- Espera do destino no mapa-múndi; "fixa 0" ou ausente vira 1d4.

Roda da raiz: python -X utf8 tools/test_saida_cidade.py"""
import asyncio, os, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server
import test_masmorra_sequenciada as base

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")


def _com_espera(espera):
    server.WORLD_ADVENTURES["test_seq"]["espera_retorno"] = espera


def test_espera_padrao():
    print("\n[1] espera: a do destino; fixa 0 ou ausente vira 1d4")
    r = base.setup_room()
    r.world_adventure_id = "test_seq"
    for rotulo, esp in (("fixa 0", {"modo": "fixa", "rodadas": 0, "dados": ""}),
                        ("ausente", None)):
        _com_espera(esp)
        rol = {r._rolar_espera_saida() for _ in range(200)}
        check(f"{rotulo} rola 1d4 (1..4)", rol <= {1, 2, 3, 4} and len(rol) > 1)
        check(f"{rotulo} aparece como 1d4 no aviso", r._espera_saida_texto() == "1d4")
    _com_espera({"modo": "fixa", "rodadas": 6, "dados": ""})
    check("fixa 6 vale 6", r._rolar_espera_saida() == 6 and r._espera_saida_texto() == "6")
    _com_espera({"modo": "dados", "rodadas": 0, "dados": "2d4"})
    rol = {r._rolar_espera_saida() for _ in range(200)}
    check("dados 2d4 rola 2..8", rol <= set(range(2, 9)) and r._espera_saida_texto() == "2d4")
    r.world_adventure_id = None
    check("masmorra fora do mapa-múndi também usa 1d4", r._espera_saida_texto() == "1d4")


async def test_multiplayer():
    print("\n[2] multiplayer: a masmorra segue; a espera começa no clique")
    r = base.setup_room()
    p = await base._entrar_e_posicionar_na_escada(r)
    _com_espera({"modo": "fixa", "rodadas": 2, "dados": ""})
    p["fome"] = 10; p["sede"] = 10
    await r.handle_exit_dungeon("p1")
    fora = p.get("fora_masmorra") or {}
    check("está na cidade", fora.get("fase") == "cidade")
    check("a espera ainda não começou", "rodadas_restantes" not in fora)
    check("pode comprar", r._em_cidade("p1") is True)
    check("a vez dele passou (a masmorra segue)", r.current_pid() != "p1")
    for _ in range(5):
        await r._tick_retorno_masmorra()
    check("rodadas na cidade não o trazem de volta", (p.get("fora_masmorra") or {}).get("fase") == "cidade")
    await r.handle_voltar_masmorra("p1")
    fora = p.get("fora_masmorra") or {}
    check("clicou voltar: a caminho", fora.get("fase") == "voltando")
    check("espera da aventura (2)", fora.get("rodadas_restantes") == 2)
    check("a caminho não compra", r._em_cidade("p1") is False)
    p["gold"] = 999; antes = len(p["bag"])
    await r.handle_shop_buy("p1", "mercador", "antidote")
    check("compra recusada a caminho", len(p["bag"]) == antes)
    await r.handle_voltar_masmorra("p1")
    check("clicar de novo não reinicia a espera", p["fora_masmorra"]["rodadas_restantes"] == 2)
    await r._tick_retorno_masmorra()   # fecho da rodada do clique: não conta
    check("o fecho da rodada do clique não conta", p["fora_masmorra"]["rodadas_restantes"] == 2)
    await r._tick_retorno_masmorra()
    check("1 rodada depois resta 1", p["fora_masmorra"]["rodadas_restantes"] == 1)
    await r._tick_retorno_masmorra()
    check("ao zerar reaparece sozinho", p.get("fora_masmorra") is None)
    check("de volta ao tabuleiro", r._ativo(p) is True and list(p["pos"]) == list(r.stairs_pos))


def _solo(r):
    """Jogo salvo Solo com grupo: p2 é herói extra da conexão p1."""
    r._jogo_salvo_solo = lambda: True
    r.savegame = {}                     # um Solo sempre tem jogo salvo
    r.players["p2"]["controlador"] = "p1"
    r.connections = {"p1": object()}


async def test_solo_pausa():
    print("\n[3] solo: a masmorra para na vez de quem saiu")
    r = base.setup_room()
    _solo(r)
    q = await base._entrar_e_posicionar_na_escada(r, "p2")
    r.initiative_order = [
        {"kind": "player", "id": "p2", "seq": 0, "initiative": 99, "dex": 0, "int": 0},
        {"kind": "player", "id": "p1", "seq": 1, "initiative": 50, "dex": 0, "int": 0}]
    r.initiative_index = 0
    _com_espera({"modo": "fixa", "rodadas": 2, "dados": ""})
    q["fome"] = 10; q["sede"] = 10
    enviados = []
    async def cap(pid, msg): enviados.append((pid, msg.get("type")))
    r.send_to = cap
    r.turn_timer_task = None
    await r.handle_exit_dungeon("p2")
    check("p2 na cidade", (q.get("fora_masmorra") or {}).get("fase") == "cidade")
    check("a vez continua sendo de p2 (masmorra parada)", r.current_pid() == "p2")
    check("p2 pode comprar", r._em_cidade("p2") is True)
    check("p1 (dentro da masmorra) não compra", r._em_cidade("p1") is False)
    check("a conexão vai para a tela da cidade", "p1" in r._conexoes_fora())
    check("recebeu city_state", ("p2", "city_state") in enviados)
    check("sem timer de turno enquanto compra", r.turn_timer_task is None)
    enviados.clear()
    await r.handle_voltar_masmorra("p2")
    fora = q.get("fora_masmorra") or {}
    check("clicou voltar: a caminho", fora.get("fase") == "voltando" and fora.get("rodadas_restantes") == 2)
    check("a vez passou para p1", r.current_pid() == "p1")
    check("a conexão volta à masmorra", "p1" not in r._conexoes_fora())
    check("cliente recebe enter_dungeon", ("p2", "enter_dungeon") in enviados)


async def test_compat_antiga():
    print("\n[4] estado antigo sem 'fase' conta como a caminho")
    r = base.setup_room()
    p = await base._entrar_e_posicionar_na_escada(r)
    p["fora_masmorra"] = {"rodadas_restantes": 0}
    p["pos"] = [-1, -1]
    check("não compra", r._em_cidade("p1") is False)
    await r._tick_retorno_masmorra()
    check("volta na rodada seguinte", p.get("fora_masmorra") is None)


async def test_templo_ressuscita():
    print("\n[5] templo: quem saiu ressuscita o companheiro morto, que volta junto")
    r = base.setup_room()
    _solo(r)
    q = await base._entrar_e_posicionar_na_escada(r, "p2")
    morto = server.make_player("p3", "Pedro", "mage", 2)
    morto["controlador"] = "p1"; morto["alive"] = False; morto["hp"] = 0; morto["pos"] = [5, 5]
    r.players["p3"] = morto
    r.hero_corpses["p3"] = {"pos": [5, 5]}
    r.initiative_order = [
        {"kind": "player", "id": "p2", "seq": 0, "initiative": 99, "dex": 0, "int": 0},
        {"kind": "player", "id": "p1", "seq": 1, "initiative": 50, "dex": 0, "int": 0}]
    r.initiative_index = 0
    _com_espera({"modo": "fixa", "rodadas": 2, "dados": ""})
    q["fome"] = 10; q["sede"] = 10; q["gold"] = 50
    erros = []
    async def cap(pid, msg):
        if msg.get("type") == "error": erros.append(str(msg.get("msg")))
    r.send_to = cap
    await r.handle_templo_ressuscitar("p2", "p3")
    check("dentro da masmorra não ressuscita", not morto["alive"])
    await r.handle_exit_dungeon("p2")
    await r.handle_templo_ressuscitar("p2", "p3")
    check("na cidade (grupo na masmorra) ressuscita com 1 PV", morto["alive"] and morto["hp"] == 1)
    check("cobrou 30", q["gold"] == 20)
    check("o cadáver some do tabuleiro", "p3" not in r.hero_corpses)
    check("o ressuscitado fica na cidade, fora do tabuleiro",
          (morto.get("fora_masmorra") or {}).get("fase") == "cidade" and morto["pos"] == [-1, -1]
          and r._ativo(morto) is False)
    await r.handle_voltar_masmorra("p2")
    check("quem o trouxe parte de volta", (q.get("fora_masmorra") or {}).get("fase") == "voltando")
    check("…e o ressuscitado parte junto, com a mesma espera",
          (morto.get("fora_masmorra") or {}).get("fase") == "voltando"
          and morto["fora_masmorra"].get("rodadas_restantes") == q["fora_masmorra"]["rodadas_restantes"])
    for _ in range(3):
        await r._tick_retorno_masmorra()
    check("os dois reaparecem na masmorra", r._ativo(q) and r._ativo(morto))


async def main():
    test_espera_padrao()
    await test_multiplayer()
    await test_solo_pausa()
    await test_compat_antiga()
    await test_templo_ressuscita()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
