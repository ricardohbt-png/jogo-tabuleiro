"""Refúgio dos Heróis — baú compartilhado da campanha + baú privado do quarto.
  • Guardar da bolsa e do equipamento (gear) nos dois escopos; retirar volta p/ a bolsa.
  • Capacidade: baú cheio recusa e NÃO consome o item; bolsa cheia recusa a retirada.
  • Ouro: depositar/retirar nos dois escopos; retirada é limitada ao saldo do baú.
  • Privacidade: o quarto é sempre o de QUEM pediu — não há como mexer no do outro,
    e `open_quarto` de um quarto alheio não manda os itens.
  • Índice inválido em `refugio_take` é recusado (não pode virar "pega o item 0").
Roda da raiz: python tools/test_refugio.py"""
import asyncio, sys, os
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import GameRoom, make_player, SHOP_WEAPONS, WEAPONS

def setup():
    r = GameRoom("TEST")
    sent, errs = [], []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict):
            sent.append(msg)
            if msg.get("type") == "error": errs.append(msg.get("msg", ""))
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.push_state = noop; r.broadcast_city_state = noop; r.push_state_or_city = noop
    r.send_to = cap_send
    r._checkpoint_savegame = lambda *a, **k: None
    r.phase = "city"
    r.refugio_state["unlocked"] = True
    r._refugio_unlocked = lambda point=None: True
    r._em_cidade = lambda pid: True
    r._sent = sent; r._errs = errs
    return r

def heroi(r, pid="p1", conta="conta1"):
    p = make_player(pid, "Victor", "warrior", 0)
    r.players[pid] = p
    r.account_by_pid[pid] = conta
    p["bag"] = []
    return p

def item(iid, nome=None):
    return {"id": iid, "name": nome or iid, "emoji": "📦", "item_slot": "bag"}

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

async def main():
    # [1] Bolsa → baú compartilhado, e de volta
    print("\n[1] Baú compartilhado: guardar da bolsa e retirar")
    r = setup(); p = heroi(r)
    p["bag"] = [item("pocao"), item("corda")]
    await r.handle_refugio_store("p1", "shared", "bag", 0)
    check("item saiu da bolsa", [i["id"] for i in p["bag"]] == ["corda"])
    check("item entrou no baú", [i["id"] for i in r.refugio_state["items"]] == ["pocao"])
    check("guardou UMA vez só", len(r.refugio_state["items"]) == 1)
    await r.handle_refugio_take("p1", "shared", 0)
    check("baú esvaziou", r.refugio_state["items"] == [])
    check("item voltou p/ bolsa", [i["id"] for i in p["bag"]] == ["corda", "pocao"])

    # [2] Equipamento → baú (desequipa de verdade)
    print("\n[2] Baú compartilhado: guardar direto do equipamento")
    r = setup(); p = heroi(r)
    p["gear"]["head"] = {"id": "helm", "name": "Elmo", "emoji": "⛑", "item_slot": "head"}
    await r.handle_refugio_store("p1", "shared", "gear", None, "head")
    check("slot ficou vazio", p["gear"].get("head") is None)
    check("elmo está no baú", [i["id"] for i in r.refugio_state["items"]] == ["helm"])

    # [3] Capacidade do baú: recusa e NÃO come o item
    print("\n[3] Baú cheio recusa sem consumir o item")
    r = setup(); p = heroi(r)
    r.refugio_state["slot_limit"] = 2
    r.refugio_state["items"] = [item("a"), item("b")]
    p["bag"] = [item("c")]
    await r.handle_refugio_store("p1", "shared", "bag", 0)
    check("item continua na bolsa", [i["id"] for i in p["bag"]] == ["c"])
    check("baú continua com 2", len(r.refugio_state["items"]) == 2)
    check("avisou o jogador", any("cheio" in e.lower() for e in r._errs))

    # [4] Bolsa cheia recusa a retirada
    print("\n[4] Bolsa cheia recusa a retirada")
    r = setup(); p = heroi(r)
    p["bag"] = [item(f"x{i}") for i in range(p["bag_size"])]
    r.refugio_state["items"] = [item("tesouro")]
    await r.handle_refugio_take("p1", "shared", 0)
    check("item continua no baú", [i["id"] for i in r.refugio_state["items"]] == ["tesouro"])
    check("avisou bolsa cheia", any("bolsa" in e.lower() for e in r._errs))

    # [5] Índice inválido não pode virar "pega o item 0"
    print("\n[5] Índice inválido é recusado")
    r = setup(); p = heroi(r)
    r.refugio_state["items"] = [item("primeiro"), item("segundo")]
    await r.handle_refugio_take("p1", "shared", 99)
    check("nada saiu do baú", len(r.refugio_state["items"]) == 2)
    check("bolsa continua vazia", p["bag"] == [])
    check("avisou espaço inválido", any("inválid" in e.lower() for e in r._errs))

    # [6] Quarto privado: guardar/retirar no escopo 'room'
    print("\n[6] Baú do quarto: guardar e retirar")
    r = setup(); p = heroi(r)
    p["bag"] = [item("diario")]
    await r.handle_refugio_store("p1", "room", "bag", 0)
    quarto, conta = r._quarto_do_jogador(p)
    check("guardou no quarto da conta", [i["id"] for i in quarto["items"]] == ["diario"])
    check("NÃO foi para o baú compartilhado", r.refugio_state["items"] == [])
    check("saiu da bolsa", p["bag"] == [])
    await r.handle_refugio_take("p1", "room", 0)
    check("voltou p/ a bolsa", [i["id"] for i in p["bag"]] == ["diario"])
    check("quarto esvaziou", quarto["items"] == [])

    # [7] Privacidade: cada um só alcança o próprio quarto
    print("\n[7] O quarto alcançado é sempre o de quem pediu")
    r = setup()
    a = heroi(r, "p1", "contaA"); b = heroi(r, "p2", "contaB")
    a["bag"] = [item("segredo_a")]
    await r.handle_refugio_store("p1", "room", "bag", 0)
    qa, _ = r._quarto_do_jogador(a); qb, _ = r._quarto_do_jogador(b)
    check("item foi p/ o quarto de A", [i["id"] for i in qa["items"]] == ["segredo_a"])
    check("quarto de B segue vazio", qb["items"] == [])
    await r.handle_refugio_take("p2", "room", 0)   # B tenta pegar o índice 0
    check("B não tirou nada de A", [i["id"] for i in qa["items"]] == ["segredo_a"])
    check("bolsa de B continua vazia", b["bag"] == [])

    # [8] open_quarto: só o dono recebe os itens
    print("\n[8] open_quarto de quarto alheio não vaza os itens")
    r = setup()
    a = heroi(r, "p1", "contaA"); b = heroi(r, "p2", "contaB")
    a["bag"] = [item("segredo_a")]
    await r.handle_refugio_store("p1", "room", "bag", 0)
    r._sent.clear()
    await r.handle_open_quarto("p2", "contaA")
    pay = next((m for m in r._sent if m.get("type") == "quarto_state"), {})
    check("veio o payload do quarto", bool(pay))
    check("can_edit falso", pay.get("can_edit") is False)
    check("sem itens no payload", "items" not in pay)
    r._sent.clear()
    await r.handle_open_quarto("p1", None)
    meu = next((m for m in r._sent if m.get("type") == "quarto_state"), {})
    check("o dono recebe os itens", [i["id"] for i in meu.get("items", [])] == ["segredo_a"])
    check("o dono pode editar", meu.get("can_edit") is True)

    # [9] Ouro nos dois escopos
    print("\n[9] Depositar e retirar ouro")
    r = setup(); p = heroi(r)
    p["gold"] = 100
    await r.handle_refugio_gold("p1", "shared", "deposit", 30)
    check("ouro saiu do herói", p["gold"] == 70)
    check("ouro entrou no baú", r.refugio_state["gold"] == 30)
    await r.handle_refugio_gold("p1", "shared", "withdraw", 999)
    check("saque limitado ao saldo", r.refugio_state["gold"] == 0 and p["gold"] == 100)
    await r.handle_refugio_gold("p1", "room", "deposit", 40)
    quarto, _ = r._quarto_do_jogador(p)
    check("cofre do quarto guarda", quarto["gold"] == 40 and p["gold"] == 60)
    check("compartilhado não mudou", r.refugio_state["gold"] == 0)
    await r.handle_refugio_gold("p1", "shared", "deposit", 999)
    check("depósito sem saldo é recusado", p["gold"] == 60 and r.refugio_state["gold"] == 0)

    # [10] Sala SEM conta (jogo rápido): apelido faz as vezes da conta
    #      Antes, guardar escrevia em hero_rooms[apelido] e abrir lia hero_rooms[""]:
    #      o item sumia da janela e o painel marcava o próprio quarto como alheio.
    print("\n[10] Sala sem conta: as três resoluções de chave concordam")
    r = setup()
    p = make_player("p1", "Victor", "warrior", 0)
    r.players["p1"] = p; p["bag"] = [item("pocao")]      # sem account_by_pid
    await r.handle_refugio_store("p1", "room", "bag", 0)
    r._sent.clear()
    await r.handle_open_quarto("p1", None)
    pay = next((m for m in r._sent if m.get("type") == "quarto_state"), {})
    check("o quarto é meu", pay.get("can_edit") is True)
    check("o item guardado aparece", [i["id"] for i in pay.get("items", [])] == ["pocao"])
    check("limite normalizado (3)", pay.get("slot_limit") == 3)
    salas = r._refugio_payload(p)["rooms"]
    check("painel marca o quarto como seu", [(s["owner"], s["can_edit"]) for s in salas] == [("Victor", True)])
    check("uma sala só (sem chave órfã)", list(r.hero_rooms.keys()) == ["Victor"])

    # [11] Retirar procura o encaixe do item antes da bolsa
    print("\n[11] Item equipável sai do baú direto para o encaixe livre")
    r = setup(); p = heroi(r)
    p["gear"]["weapon"] = None; p["weapon"] = {**WEAPONS["unarmed"]}
    r.refugio_state["items"] = [deepcopy(next(w for w in SHOP_WEAPONS if w["id"] == "longsword"))]
    await r.handle_refugio_take("p1", "shared", 0)
    check("equipou na mão principal", (p["gear"].get("weapon") or {}).get("id") == "longsword")
    check("NÃO foi parar na bolsa", p["bag"] == [])
    check("cópia de combate sincronizada", (p.get("weapon") or {}).get("id") == "longsword")
    check("baú esvaziou", r.refugio_state["items"] == [])

    # [11b] Encaixe ocupado → bolsa (não desequipa nada por conta própria)
    print("\n[11b] Encaixe ocupado continua caindo na bolsa")
    r = setup(); p = heroi(r)
    equipada = deepcopy(next(w for w in SHOP_WEAPONS if w["id"] == "longsword"))
    p["gear"]["weapon"] = equipada; p["weapon"] = deepcopy(equipada)
    r.refugio_state["items"] = [deepcopy(next(w for w in SHOP_WEAPONS if w["id"] == "dagger"))]
    await r.handle_refugio_take("p1", "shared", 0)
    check("arma equipada intocada", (p["gear"].get("weapon") or {}).get("id") == "longsword")
    check("a nova foi p/ a bolsa", [i["id"] for i in p["bag"]] == ["dagger"])

    # [11c] Consumível não tem encaixe: sempre bolsa
    print("\n[11c] Item sem encaixe vai para a bolsa")
    r = setup(); p = heroi(r)
    r.refugio_state["items"] = [item("pocao")]
    antes = {k: (v or {}).get("id") for k, v in p["gear"].items()}
    await r.handle_refugio_take("p1", "shared", 0)
    check("poção na bolsa", [i["id"] for i in p["bag"]] == ["pocao"])
    check("equipamento intocado", {k: (v or {}).get("id") for k, v in p["gear"].items()} == antes)

    # [11d] Bolsa cheia deixa de barrar o que vai para o encaixe
    print("\n[11d] Bolsa cheia não impede retirar algo equipável")
    r = setup(); p = heroi(r)
    p["gear"]["weapon"] = None; p["weapon"] = {**WEAPONS["unarmed"]}
    p["bag"] = [item(f"x{i}") for i in range(p["bag_size"])]
    r.refugio_state["items"] = [deepcopy(next(w for w in SHOP_WEAPONS if w["id"] == "longsword")), item("pocao")]
    await r.handle_refugio_take("p1", "shared", 0)
    check("equipou apesar da bolsa cheia", (p["gear"].get("weapon") or {}).get("id") == "longsword")
    r._errs.clear()
    await r.handle_refugio_take("p1", "shared", 0)     # agora a poção, que só cabe na bolsa
    check("sem encaixe + bolsa cheia = recusa", [i["id"] for i in r.refugio_state["items"]] == ["pocao"])
    check("avisou bolsa cheia", any("bolsa" in e.lower() for e in r._errs))

    # [12] A arma INICIAL volta lutando. O dict do gear inicial é só de exibição
    #      (sem die/stat), então a sincronia de `p["weapon"]` precisa cair no
    #      catálogo WEAPONS pelo id — senão o herói fica equipado e desarmado.
    print("\n[12] Arma inicial volta do baú com os dados de combate")
    for cls in ("warrior", "mage", "rogue", "cleric", "paladin", "bard"):
        r = setup(); p = make_player("p1", "Herói", cls, 0)
        r.players["p1"] = p; r.account_by_pid["p1"] = "conta1"; p["bag"] = []
        arma_id = p["weapon"]["id"]
        await r.handle_refugio_store("p1", "shared", "gear", None, "weapon")
        await r.handle_refugio_take("p1", "shared", 0)
        ok = (p["gear"].get("weapon") or {}).get("id") == arma_id \
             and (p.get("weapon") or {}).get("id") == arma_id and p["weapon"].get("die")
        check(f"{cls}: reequipou {arma_id} com dado de dano", bool(ok))

    print(f"\n{'='*46}\n  {PASS} passaram · {FAIL} falharam\n{'='*46}")
    return 1 if FAIL else 0

sys.exit(asyncio.run(main()))
