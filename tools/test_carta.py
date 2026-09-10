"""Regressões da Carta narrativa. Rode da raiz: python tools/test_carta.py"""
import asyncio
import copy
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


def check(name, cond):
    print(f"  {'OK' if cond else 'XX'}  {name}")
    return cond


async def main():
    passed = 0
    failed = 0

    hydrated = server.hidratar_itens_bau([{
        "id": "carta", "texto": "Fraqueza: fogo.\nAtacar ao amanhecer."
    }])
    if check("hidrata carta com texto por instância", len(hydrated) == 1
             and hydrated[0]["texto"] == "Fraqueza: fogo.\nAtacar ao amanhecer."):
        passed += 1
    else:
        failed += 1

    cursed = server.hidratar_itens_bau([{
        "id": "carta", "texto": "Não leia em voz alta.",
        "curse_mode": "especifica", "curse_id": "maos_tremulas",
    }])
    if check("hidrata configuração de maldição da carta", len(cursed) == 1
             and cursed[0].get("curse_mode") == "especifica"
             and cursed[0].get("curse_id") == "maos_tremulas"):
        passed += 1
    else:
        failed += 1

    if check("valida configuração aleatória por gravidade",
             server._validar_config_maldicao_carta({
                 "id": "carta", "curse_mode": "aleatoria", "curse_category": "media"
             }) is None):
        passed += 1
    else:
        failed += 1
    if check("recusa maldição desconhecida na carta",
             server._validar_config_maldicao_carta({
                 "id": "carta", "curse_mode": "especifica", "curse_id": "inexistente"
             }) is not None):
        passed += 1
    else:
        failed += 1

    room = server.GameRoom("TEST")
    room.phase = "playing"
    room.player_order = ["p1"]
    room.turn_index = 0
    player = server.make_player("p1", "Pedro", "mage", 0)
    player["bag"] = [copy.deepcopy(hydrated[0])]
    room.players["p1"] = player
    sent = []

    async def capture(pid, message):
        sent.append((pid, message))

    room.send_to = capture
    await room.handle_use_item("p1", "carta")
    item_message = sent[-1][1] if sent else {}
    if check("ler carta envia mensagem sem consumi-la", item_message.get("type") == "item_message"
             and item_message.get("item", {}).get("texto") == hydrated[0]["texto"]
             and len(player["bag"]) == 1):
        passed += 1
    else:
        failed += 1

    player["bag"] = [copy.deepcopy(cursed[0])]
    sent.clear()
    await room.handle_read_item("p1", "carta", 0)
    curse_messages = [m for _, m in sent if m.get("type") == "curse_result"]
    if check("ler carta amaldiçoada aplica a maldição e preserva o item",
             curse_messages and player["bag"][0].get("curse_triggered")
             and any(x.get("id") == "maos_tremulas" for x in player.get("maldicoes", []))
             and len(player["bag"]) == 1):
        passed += 1
    else:
        failed += 1

    sent.clear()
    await room.handle_read_item("p1", "carta", 0)
    if check("a mesma carta não reaplica a maldição ao ser relida",
             not [m for _, m in sent if m.get("type") == "curse_result"]
             and len(player.get("maldicoes", [])) == 1):
        passed += 1
    else:
        failed += 1

    print(f"\n===== {passed} passaram, {failed} falharam =====")
    raise SystemExit(1 if failed else 0)


asyncio.run(main())
