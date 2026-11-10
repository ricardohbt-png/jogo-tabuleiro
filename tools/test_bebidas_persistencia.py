"""Penalidade de bebida não pode virar permanente ao salvar o jogo.

Rum, Hidromel, Vinho e Cerveja tiram ataque/Reflexos DIRETO da ficha
(`atk_bonus`, `ref_`) e só devolvem quando o efeito expira. A ficha salva
(`snapshot_character`) guarda `atk_bonus`/`ref_`; se não guardar também o
estado da bebida, quem salva com o efeito ativo (voltar à cidade, Salvar e
sair) volta com a perda para sempre. O Absinto já guardava o seu.

Para cada bebida: beber, salvar, carregar numa ficha nova e iniciar uma
masmorra nova (que limpa as bebidas) — os valores têm de voltar ao original.
"""
import asyncio
import copy
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

FALHAS = []


def check(cond, msg):
    print(("  ok   " if cond else "  FALHA ") + msg)
    if not cond:
        FALHAS.append(msg)


def sala():
    r = S.GameRoom("BEBIDAS")

    async def nada(*a, **k):
        return None
    r.push_state = nada
    r.broadcast = nada
    r.gm_say = nada
    r.send_to = nada
    return r


async def beber(bebida):
    r = sala()
    p = S.make_player("p1", "Ana", "warrior", 0)
    r.players["p1"] = p
    r.phase = "playing"
    r.initiative_active = True
    r.initiative_order = [{"kind": "player", "id": "p1"}]
    r.initiative_index = 0
    p["pos"] = [1, 1]
    p["fome"] = p["sede"] = 50
    item = copy.deepcopy(next(i for i in S.SHOP_TAVERN if i["id"] == bebida))
    item.pop("price", None)
    p["bag"] = [item]
    base = (p["atk_bonus"], p["ref_"])
    await r.handle_use_item("p1", bebida)
    return r, p, base


async def main():
    print("[1] salvar com a bebida ativa e recomeçar numa masmorra nova")
    for bebida in ("rum", "hidromel", "absinto", "garrafa_vinho", "caneca_cerveja", "cerveja_ana"):
        if not any(i["id"] == bebida for i in S.SHOP_TAVERN):
            continue
        r, p, base = await beber(bebida)
        efeito = (p["atk_bonus"], p["ref_"]) != base or p.get("cerveja_ana_ca_ativo")
        check(efeito, f"{bebida}: o efeito foi aplicado ao beber")
        novo = S.make_player("p2", "Ana", "warrior", 0)
        S.restore_character(novo, S.snapshot_character(p))
        r2 = sala()
        r2.players["p2"] = novo
        for reset in ("_resetar_rum", "_resetar_hidromel", "_resetar_absinto",
                      "_resetar_vinho", "_resetar_cerveja"):
            getattr(r2, reset)(novo)
        check((novo["atk_bonus"], novo["ref_"]) == base,
              f"{bebida}: ataque/Reflexos voltam ao normal depois de salvar e carregar "
              f"(base {base}, ficou {(novo['atk_bonus'], novo['ref_'])})")

    print("[2] o efeito continua contando depois de carregar")
    r, p, base = await beber("rum")
    novo = S.make_player("p2", "Ana", "warrior", 0)
    S.restore_character(novo, S.snapshot_character(p))
    r2 = sala()
    r2.players["p2"] = novo
    for _ in range(10):
        await r2._processar_rum_turno(novo)
    check((novo["atk_bonus"], novo["ref_"]) == base, "rum expira normalmente após 10 turnos na ficha carregada")


asyncio.run(main())
print()
if FALHAS:
    print(f"{len(FALHAS)} falha(s)")
    sys.exit(1)
print("todos passaram")
