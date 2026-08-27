"""Xamã Goblin — as 4 magias, a prioridade da IA e o Medo sem fogo amigo.

A ficha do Xamã é uma SOBRESCRITA nativa feita no editor de criaturas. O editor
grava as magias em `monster_spells` (aba Magias), mas a IA da espécie lia
`ability_uses` — o contador que vem de `special_abilities`. Como a sobrescrita
não declara magia ali, o Xamã tinha três magias na ficha e não lançava nenhuma.

Roda da raiz: python tools/test_xama_goblin.py
"""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(nome, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {nome}")
    else:    FAIL += 1; print(f"  ❌ {nome}")

FICHA = next(m for m in S.MONSTER_DEFS if m["type"] == "goblin_xama")


def sala():
    r = S.GameRoom("XAMA")
    r.phase = "playing"; r.round_num = 1
    r.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
    r.falas = []
    async def noop(*a, **k): pass
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    return r


def xama(r, pos=(5, 5)):
    m = S.make_monster(FICHA, {"id": "r0", "cx": pos[0], "cy": pos[1]})
    m["id"] = "x1"; m["pos"] = list(pos); m["alertado"] = True
    r.monsters[m["id"]] = m
    return m


def heroi(r, pid, cls, pos):
    p = S.make_player(pid, pid.upper(), cls, 0)
    p["pos"] = list(pos); p["alive"] = True; p["connected"] = True
    r.players[pid] = p
    return p


def goblin(r, gid, pos):
    g = S.make_monster(next(m for m in S.MONSTER_DEFS if m["type"] == "goblin"),
                       {"id": "r0", "cx": pos[0], "cy": pos[1]})
    g["id"] = gid; g["pos"] = list(pos)
    r.monsters[gid] = g
    return g


async def main():
    print("\n[1] A ficha declara as 4 magias e recuperou o que a sobrescrita zerou")
    ids = {s["id"] for s in FICHA.get("monster_spells", [])}
    for sid in ("silencio", "amaldicoar", "abencoar", "medo"):
        check(f"{sid} está em monster_spells", sid in ids)
    check("ai_type voltou a ser goblin_xama", FICHA.get("ai_type") == "goblin_xama")
    check("loot_table deixou de estar vazia", bool(FICHA.get("loot_table")))
    check("fraqueza -2 em Vontade restaurada",
          any(w.get("bonus_flat") == -2
              and "vontade" in (w.get("saves") or ([w["save"]] if w.get("save") else []))
              for w in FICHA.get("weaknesses", [])))
    editor_abs = [a for a in FICHA.get("special_abilities", [])
                  if a.get("source") in ("heroi", "guilda")]
    check("as 8 habilidades de herói/guilda continuam na ficha", len(editor_abs) == 8)
    inst = S.make_monster(FICHA, {"id": "r0", "cx": 1, "cy": 1})
    check("a instância nasce com os 4 usos de magia", len(inst.get("spell_uses", {})) == 4)

    print("\n[2] Silêncio vem primeiro, sobre um conjurador no alcance")
    r = sala(); m = xama(r); heroi(r, "p1", "warrior", (6, 5)); heroi(r, "p2", "mage", (8, 5))
    alvos = [{"kind": "player", "obj": p} for p in r.players.values()]
    check("lançou", await r._xama_tentar_magia(m, alvos))
    check("gastou o uso de Silêncio", m["spell_uses"]["silencio"] == 0)
    check("não gastou as outras", m["spell_uses"]["medo"] == 1)

    print("\n[3] Medo quando 2+ heróis se aglomeram e nenhum goblin está no raio")
    r = sala(); m = xama(r)
    heroi(r, "p1", "warrior", (8, 5)); heroi(r, "p2", "rogue", (8, 6))
    alvos = [{"kind": "player", "obj": p} for p in r.players.values()]
    check("lançou", await r._xama_tentar_magia(m, alvos))
    check("gastou o uso de Medo", m["spell_uses"]["medo"] == 0)
    check("não gastou Amaldiçoar", m["spell_uses"]["amaldicoar"] == 1)

    print("\n[4] Medo é pulado quando todo centro útil pegaria um goblin junto")
    # O quadro real: o bando já está engajado em corpo a corpo com os heróis.
    # Não existe centro de raio 2 que pegue os dois heróis e nenhum goblin.
    r = sala(); m = xama(r)
    heroi(r, "p1", "warrior", (8, 5)); heroi(r, "p2", "rogue", (8, 6))
    for i, pos in enumerate(((7, 5), (7, 6), (9, 5), (9, 6))):
        goblin(r, f"g{i}", pos)
    check("nenhum centro limpo para 2+ alvos", r._xama_centro_medo(m, 2) is None)
    check("nem para 1 alvo", r._xama_centro_medo(m, 1) is None)
    alvos = [{"kind": "player", "obj": p} for p in r.players.values()]
    check("lançou alguma coisa", await r._xama_tentar_magia(m, alvos))
    check("Medo intacto", m["spell_uses"]["medo"] == 1)
    check("caiu para Amaldiçoar", m["spell_uses"]["amaldicoar"] == 0)

    print("\n[5] Amaldiçoar com um herói só por perto e sem aglomeração")
    r = sala(); m = xama(r); heroi(r, "p1", "warrior", (6, 5))
    alvos = [{"kind": "player", "obj": r.players["p1"]}]
    check("lançou", await r._xama_tentar_magia(m, alvos))
    check("escolheu Amaldiçoar", m["spell_uses"]["amaldicoar"] == 0)
    check("Medo guardado para 2+ alvos", m["spell_uses"]["medo"] == 1)

    print("\n[6] Abençoar quando resta aliado por perto e mais nada a fazer")
    r = sala(); m = xama(r); heroi(r, "p1", "warrior", (14, 14)); goblin(r, "g1", (6, 5))
    m["spell_uses"]["silencio"] = 0; m["spell_uses"]["amaldicoar"] = 0
    alvos = [{"kind": "player", "obj": r.players["p1"]}]
    check("lançou", await r._xama_tentar_magia(m, alvos))
    check("escolheu Abençoar", m["spell_uses"]["abencoar"] == 0)

    print("\n[7] Medo com um alvo só, como último recurso")
    r = sala(); m = xama(r); heroi(r, "p1", "warrior", (8, 5))
    m["spell_uses"]["silencio"] = 0; m["spell_uses"]["amaldicoar"] = 0
    m["spell_uses"]["abencoar"] = 0
    alvos = [{"kind": "player", "obj": r.players["p1"]}]
    check("lançou", await r._xama_tentar_magia(m, alvos))
    check("gastou Medo", m["spell_uses"]["medo"] == 0)

    print("\n[8] Sem magia disponível não inventa nada")
    r = sala(); m = xama(r); heroi(r, "p1", "warrior", (6, 5))
    for sid in ("silencio", "amaldicoar", "abencoar", "medo"):
        m["spell_uses"][sid] = 0
    alvos = [{"kind": "player", "obj": r.players["p1"]}]
    check("devolve False", await r._xama_tentar_magia(m, alvos) is False)

    print("\n[9] Concentração Frágil: dano no turno anterior corta a conjuração")
    r = sala(); m = xama(r); heroi(r, "p1", "warrior", (6, 5))
    m["_cf_hp_ref"] = m["max_hp"]; m["hp"] = m["max_hp"] - 3
    alvos = [{"kind": "player", "obj": r.players["p1"]}]
    await r._ai_xama_goblin(m, alvos)
    check("nenhuma magia foi lançada", all(v == 1 for v in m["spell_uses"].values()))

    print(f"\n{'='*54}\n  {PASS} passaram, {FAIL} falharam\n{'='*54}")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    asyncio.run(main())
