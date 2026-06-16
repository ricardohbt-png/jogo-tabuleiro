"""Testes da magia Dominar Morto-Vivo (controle progressivo) e do Necromante.

Executar:  python _archive/test_dominar_morto_vivo.py
Força o resultado dos saves substituindo GameRoom._testar_save por uma fila.
"""
import asyncio, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server import GameRoom, GRIMORIO


def make_room(save_outcomes):
    """save_outcomes: lista de bool (True=passa) consumida a cada _testar_save."""
    room = GameRoom("TEST")
    fila = list(save_outcomes)

    def fake_save(alvo, tipo, dif, extra_mod=0):
        passou = fila.pop(0) if fila else False
        return (passou, 10, extra_mod, 10 + extra_mod)
    room._testar_save = fake_save
    return room


def mage(pid="P1", pos=(5, 5)):
    return {
        "id": pid, "name": "Pedro", "pos": list(pos), "alive": True,
        "class_id": "mage", "int_": 18, "level": 5, "ac": 12, "hp": 20, "max_hp": 20,
        "fome": 10, "sede": 10, "action_done": False, "animados": [],
    }


def undead(mid="M1", pos=(5, 6), tier=2):
    return {
        "id": mid, "name": "Esqueleto", "emoji": "💀", "type": "skeleton",
        "pos": list(pos), "hp": 10, "max_hp": 10, "ac": 13, "tier": tier,
        "movement": 4, "undead": True,
        "attacks": [{"name": "Espada", "damage": "1d6"}],
    }


def necromante(mid="N1", pos=(5, 7)):
    return {
        "id": mid, "name": "Necromante", "emoji": "🧙", "type": "necromante",
        "pos": list(pos), "hp": 16, "max_hp": 16, "ac": 13, "tier": 2, "int_": 16,
        "movement": 4, "atk_bonus": 2, "damage": "1d6",
        "attacks": [{"name": "Cajado", "damage": "1d6", "atk_bonus": 2, "num_attacks": 1}],
        "special_abilities": [{"id": "dominar_morto_vivo", "name": "Dominar Morto-Vivo",
                               "action_type": "acao", "range": 4, "circulo": 3}],
        "ai_type": "necromante",
    }


MAGIA = GRIMORIO["dominar_morto_vivo"]


async def t_passa_no_lancamento():
    room = make_room([True])           # passa no save do lançamento
    p = mage(); room.players[p["id"]] = p
    m = undead(); room.monsters[m["id"]] = m
    await room._executar_dominar_morto_vivo(p, MAGIA, {"target_id": m["id"]})
    assert m["id"] in room.monsters, "monstro deveria permanecer hostil"
    assert not p["animados"], "não deveria criar servo"
    print("OK  passa no lançamento → magia falha")


async def t_falha_vira_temporario():
    room = make_room([False])          # falha no lançamento
    p = mage(); room.players[p["id"]] = p
    m = undead(); room.monsters[m["id"]] = m
    await room._executar_dominar_morto_vivo(p, MAGIA, {"target_id": m["id"]})
    assert m["id"] not in room.monsters, "monstro deveria sair do tabuleiro"
    assert len(p["animados"]) == 1, "deveria criar 1 servo"
    a = p["animados"][0]
    assert a["por_dominacao"] and not a["dominacao"]["permanente"]
    assert a["dominacao"]["rodada"] == 2
    print("OK  falha no lançamento → servo temporário (rodada 2)")


async def t_tres_falhas_permanente():
    room = make_room([False, False, False])  # cast + 2 re-testes falham
    p = mage(); room.players[p["id"]] = p
    m = undead(); room.monsters[m["id"]] = m
    await room._executar_dominar_morto_vivo(p, MAGIA, {"target_id": m["id"]})
    await room._retestar_dominacao_jogador(p)   # re-teste 1 (falha 2/3)
    a = p["animados"][0]
    assert not a["dominacao"]["permanente"] and a["dominacao"]["rodada"] == 3
    await room._retestar_dominacao_jogador(p)   # re-teste 2 (falha 3/3 → permanente)
    assert p["animados"][0]["dominacao"]["permanente"], "deveria ser permanente após 3 falhas"
    print("OK  3 falhas seguidas → controle permanente")


async def t_passa_no_reteste_escapa():
    room = make_room([False, True])    # falha no cast, passa no re-teste
    p = mage(); room.players[p["id"]] = p
    m = undead(); room.monsters[m["id"]] = m
    await room._executar_dominar_morto_vivo(p, MAGIA, {"target_id": m["id"]})
    await room._retestar_dominacao_jogador(p)
    assert not p["animados"], "servo deveria escapar"
    assert m["id"] in room.monsters, "deveria voltar como monstro hostil"
    assert room.monsters[m["id"]]["hp"] >= 1
    print("OK  passa no re-teste → quebra controle, volta hostil")


async def t_relancar_libera_temporario():
    room = make_room([False, False])   # falha no 1º cast, falha no 2º cast
    p = mage(); room.players[p["id"]] = p
    m1 = undead("M1", (5, 6)); room.monsters[m1["id"]] = m1
    m2 = undead("M2", (5, 4)); room.monsters[m2["id"]] = m2
    await room._executar_dominar_morto_vivo(p, MAGIA, {"target_id": m1["id"]})
    await room._executar_dominar_morto_vivo(p, MAGIA, {"target_id": m2["id"]})
    ids = [a["id"] for a in p["animados"]]
    assert ids == ["M2"], f"só M2 deveria estar dominado, veio {ids}"
    assert "M1" in room.monsters, "M1 (temporário) deveria voltar ao tabuleiro"
    print("OK  relançar com temporário ativo → libera o anterior")


async def t_relancar_destroi_permanente():
    room = make_room([False, False, False, False])  # cast m1, 2 re-testes (perm), cast m2
    p = mage(); room.players[p["id"]] = p
    m1 = undead("M1", (5, 6)); room.monsters[m1["id"]] = m1
    m2 = undead("M2", (5, 4)); room.monsters[m2["id"]] = m2
    await room._executar_dominar_morto_vivo(p, MAGIA, {"target_id": m1["id"]})
    await room._retestar_dominacao_jogador(p)
    await room._retestar_dominacao_jogador(p)
    assert p["animados"][0]["dominacao"]["permanente"]
    await room._executar_dominar_morto_vivo(p, MAGIA, {"target_id": m2["id"]})
    ids = [a["id"] for a in p["animados"]]
    assert ids == ["M2"], f"só M2 dominado, veio {ids}"
    assert "M1" not in room.monsters, "M1 permanente deveria ser destruído (pó)"
    print("OK  relançar com permanente ativo → destrói o anterior (pó)")


async def t_necromante_rouba_e_animado_escapa():
    # Necromante rouba um animado do Pedro (falha do animado), depois animado escapa (passa).
    room = make_room([False, True])
    p = mage(); room.players[p["id"]] = p
    n = necromante(pos=(5, 7)); room.monsters[n["id"]] = n
    # Animado normal do Pedro (Animar Mortos) próximo do necromante
    a = {"id": "A1", "owner": p["id"], "nome": "Esqueleto Animado", "icone": "💀",
         "tipo": "skeleton", "nivel": 1, "slots": 1, "ca": 12, "vida_max": 10,
         "vida_atual": 10, "dano": "1d4", "movimento": 3, "moves_left": 3,
         "acted": False, "pos": [5, 6], "hostil": False}
    p["animados"].append(a)
    await room._ai_necromante(n, [])
    assert a.get("dominado_por_monstro") == n["id"], "necromante deveria roubar o animado"
    # Re-teste na fase dos monstros: passa → volta ao dono
    await room._agir_animados_dominados_por_monstro()
    assert not a.get("dominado_por_monstro"), "animado deveria escapar e voltar ao Pedro"
    assert a in p["animados"], "animado continua na lista do Pedro"
    print("OK  necromante rouba animado; animado passa no re-teste e volta ao dono")


async def t_necromante_morto_devolve():
    room = make_room([False])          # necromante rouba (falha do animado)
    p = mage(); room.players[p["id"]] = p
    n = necromante(pos=(5, 7)); room.monsters[n["id"]] = n
    a = {"id": "A1", "owner": p["id"], "nome": "Esqueleto Animado", "icone": "💀",
         "tipo": "skeleton", "nivel": 1, "slots": 1, "ca": 12, "vida_max": 10,
         "vida_atual": 10, "dano": "1d4", "movimento": 3, "moves_left": 3,
         "acted": False, "pos": [5, 6], "hostil": False}
    p["animados"].append(a)
    await room._ai_necromante(n, [])
    assert a.get("dominado_por_monstro") == n["id"]
    n["hp"] = 0                        # necromante morre
    await room._agir_animados_dominados_por_monstro()
    assert not a.get("dominado_por_monstro"), "sem necromante, animado volta ao dono"
    print("OK  necromante morto → animado volta ao dono")


async def main():
    for t in (t_passa_no_lancamento, t_falha_vira_temporario, t_tres_falhas_permanente,
              t_passa_no_reteste_escapa, t_relancar_libera_temporario,
              t_relancar_destroi_permanente, t_necromante_rouba_e_animado_escapa,
              t_necromante_morto_devolve):
        await t()
    print("\nTODOS OS TESTES PASSARAM ✅")


if __name__ == "__main__":
    asyncio.run(main())
