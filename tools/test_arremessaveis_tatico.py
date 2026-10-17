"""Testes dos arremessáveis TÁTICOS (Sub-projeto D: Cola e Rede).
Roda da raiz: python tools/test_arremessaveis_tatico.py"""
import asyncio, sys, os, random
from copy import deepcopy
from pathlib import Path
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player, FLOOR, WALL, ARREMESSAVEIS, SHOP_MERCHANT

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  OK  {name}")
    else:    FAIL += 1; print(f"  XX  {name}  {extra}")

def setup(w=9, h=9):
    r = GameRoom("TEST")
    errs = []
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            errs.append(msg.get("msg", ""))
    r.gm_say = noop; r.broadcast = noop; r.push_state = noop
    r.broadcast_city_state = noop; r._broadcast_dado = noop
    r.send_to = cap_send
    r._is_turn = lambda pid: True
    r.phase = "playing"
    r.tiles = [[FLOOR] * w for _ in range(h)]
    r.map_w = w; r.map_h = h
    r._decor_block_tiles = set()
    r._mat_solid_tiles = set()
    r._is_closed_door = lambda x, y: False
    r._errs = errs
    return r

def throwable(iid):
    return deepcopy(next(i for i in SHOP_MERCHANT if i["id"] == iid))

def make_monster(r, mid, x, y, hp=40, ac=1, movement=6):
    m = {"id": mid, "name": "M"+mid, "pos": [x, y], "hp": hp, "max_hp": hp,
         "ac": ac, "alive": True, "movement": movement}
    r.monsters[mid] = m
    return m

# Save determinístico: substitui _save_mostrado por um que sempre passa/falha.
def _mk_save(passou):
    async def _s(alvo, tipo, cd, *a, **k):
        return (passou, 1, 0, 1)   # (passou, d20, bonus, total)
    return _s

# d20 fixo no arremesso; dados de dano usam o RNG real.
_REAL_RANDINT = random.randint
def _fixed_d20(value):
    def fake(a, b):
        return value if (a, b) == (1, 20) else _REAL_RANDINT(a, b)
    return fake

async def main():
    random.seed(1)

    # ── [1] Catálogo + loja ────────────────────────────────────────────────────
    print("\n[1] Catálogo tático + loja")
    for iid in ("cola_alquimica", "cola_alquimica_superior", "rede_arremesso"):
        check(f"{iid} no catálogo", iid in ARREMESSAVEIS)
        check(f"{iid} alvo=ataque_alvo", ARREMESSAVEIS.get(iid, {}).get("alvo") == "ataque_alvo")
        check(f"{iid} sem dano", "dano" not in ARREMESSAVEIS.get(iid, {}))
        check(f"{iid} vendável", any(i["id"] == iid for i in SHOP_MERCHANT))
    cola_superior_loja = next((i for i in SHOP_MERCHANT if i["id"] == "cola_alquimica_superior"), {})
    check("cola superior: preço 30", cola_superior_loja.get("price") == 30)
    check("cola superior: mesma imagem da cola", cola_superior_loja.get("icon") == "assets/itens/cola_alquimica.png")
    check("cola superior: disponível no mercador de Alva e Luz",
          any(i["id"] == "cola_alquimica_superior" for i in S._city_shop_items("alva_e_luz", "mercador")))
    r = setup(); r.phase = "city"; r.world_location = "alva_e_luz"
    async def noop(*a, **k): pass
    r.push_state_or_city = noop
    comprador = make_player("p1", "V", "warrior", 0); comprador["gold"] = 50
    r.players["p1"] = comprador
    await r.handle_shop_buy("p1", "mercador", "cola_alquimica_superior")
    comprada = next((i for i in comprador["bag"] if i.get("id") == "cola_alquimica_superior"), None)
    check("cola superior: compra debita 30 moedas", comprador["gold"] == 20)
    check("cola superior: compra coloca o item com imagem na bolsa",
          comprada is not None and comprada.get("buy_price") == 30
          and comprada.get("icon") == "assets/itens/cola_alquimica.png")
    cola = ARREMESSAVEIS["cola_alquimica"]["controle"]
    check("cola: mov_reduzido", cola["tipo"] == "mov_reduzido")
    check("cola: resist Reflexos CD15", cola["resist_save"] == {"tipo": "reflexos", "cd": 15})
    check("cola: duracao 2", cola["duracao"] == 2)
    ui = Path(__file__).resolve().parents[1] / "src" / "gameState.js"
    interface = Path(__file__).resolve().parents[1] / "src" / "lang" / "interface.js"
    check("cola: tooltip atualizado", "Reflexos CD 15" in ui.read_text(encoding="utf-8")
          and "perde todo o movimento por 2 rodadas" in ui.read_text(encoding="utf-8"))
    check("cola: descrição de interface atualizada", "Reflexos CD 15" in interface.read_text(encoding="utf-8")
          and "perde todo o movimento por 2 rodadas" in interface.read_text(encoding="utf-8"))
    game_state_text = ui.read_text(encoding="utf-8")
    interface_text = interface.read_text(encoding="utf-8")
    check("cola superior: catálogo cliente com preço, imagem e CD18",
          "cola_alquimica_superior" in game_state_text
          and "preco: 30" in game_state_text
          and "assets/itens/cola_alquimica.png" in game_state_text
          and "saveCD: 18" in game_state_text)
    check("cola superior: nome e descrição traduzidos",
          '"ui.item.cola_alquimica_superior.nome"' in interface_text
          and '"ui.item.cola_alquimica_superior.desc"' in interface_text
          and "Reflex DC 18" in interface_text
          and "Reflexos CD 18" in interface_text)
    cola_superior = ARREMESSAVEIS.get("cola_alquimica_superior", {}).get("controle", {})
    check("cola superior: mesmo efeito, Reflexos CD18 e 2 rodadas",
          cola_superior == {"tipo": "mov_reduzido",
                            "resist_save": {"tipo": "reflexos", "cd": 18}, "duracao": 2})
    rede = ARREMESSAVEIS["rede_arremesso"]["controle"]
    check("rede: enredado", rede["tipo"] == "enredado")
    check("rede: escape Fortitude CD12", rede["escape_save"] == {"tipo": "fortitude", "cd": 12})

    # ── [2] _aplicar_controle_arremesso ────────────────────────────────────────
    print("\n[2] _aplicar_controle_arremesso")
    cola_ctrl = ARREMESSAVEIS["cola_alquimica"]["controle"]
    rede_ctrl = ARREMESSAVEIS["rede_arremesso"]["controle"]

    # cola: falha no Reflexos → perde todo o movimento
    r = setup(); r._save_mostrado = _mk_save(False)
    m = make_monster(r, "m1", 4, 4, movement=6)
    await r._aplicar_controle_arremesso(m, cola_ctrl)
    check("cola: movement 6→0", m["movement"] == 0)
    check("cola: bloqueio de movimento ativo", m.get("cola_sem_movimento") is True
          and m.get("_water_moves_left", 0) == 0 and m.get("master_moves_left", 0) == 0)
    check("cola: mov_reduzido_rodadas=2", m.get("mov_reduzido_rodadas") == 2)
    check("cola: guardou original 6", m.get("mov_reduzido_orig") == 6)

    # cola: sucesso no Reflexos → sem efeito
    r._save_mostrado = _mk_save(True)
    m2 = make_monster(r, "m2", 5, 5, movement=6)
    await r._aplicar_controle_arremesso(m2, cola_ctrl)
    check("cola resist: movement intacto", m2["movement"] == 6 and not m2.get("mov_reduzido_rodadas"))

    # cola: reaplicar renova duração sem cortar de novo
    r._save_mostrado = _mk_save(False)
    m["mov_reduzido_rodadas"] = 1
    await r._aplicar_controle_arremesso(m, cola_ctrl)
    check("cola reaplicar: movement fica 0 (não acumula)", m["movement"] == 0)
    check("cola reaplicar: renova p/ 2", m["mov_reduzido_rodadas"] == 2)

    # rede: marca enredado + guarda o save de escape
    r = setup()
    m3 = make_monster(r, "m3", 6, 6)
    await r._aplicar_controle_arremesso(m3, rede_ctrl)
    check("rede: enredado", m3.get("enredado") is True)
    check("rede: enredado_save fortitude", m3.get("enredado_save") == "fortitude")
    check("rede: enredado_cd 12", m3.get("enredado_cd") == 12)

    # ── [3] mov_reduzido tica e expira (restaura movement) ─────────────────────
    print("\n[3] tick de mov_reduzido em _status_monstro_turno")
    r = setup()
    m = make_monster(r, "m1", 4, 4, movement=6)
    m["movement"] = 0; m["mov_reduzido_orig"] = 6; m["mov_reduzido_rodadas"] = 2
    m["cola_sem_movimento"] = True
    res = await r._status_monstro_turno(m, [m])
    check("mov_reduzido não pula o turno", res != "pulou")
    check("cola sem movimento 1: tica p/ 1 e mantém movement 0", m["mov_reduzido_rodadas"] == 1 and m["movement"] == 0)
    await r._status_monstro_turno(m, [m])
    check("cola sem movimento 2: tica p/ 0 e ainda mantém movement 0", m.get("mov_reduzido_rodadas", 0) == 0 and m["movement"] == 0)
    await r._status_monstro_turno(m, [m])
    check("expira: movement restaurado p/ 6", m["movement"] == 6)
    check("flag e backup limpos", "mov_reduzido_rodadas" not in m and "mov_reduzido_orig" not in m
          and "cola_sem_movimento" not in m)

    # ── [4] _processar_enredado_turno (escape) ─────────────────────────────────
    print("\n[4] _processar_enredado_turno")
    r = setup()
    m = make_monster(r, "m1", 4, 4)
    m["enredado"] = True; m["enredado_save"] = "fortitude"; m["enredado_cd"] = 12

    r._save_mostrado = _mk_save(False)   # falha → continua preso, turno gasto
    consumiu = await r._processar_enredado_turno(m)
    check("falha: turno consumido", consumiu is True)
    check("falha: continua preso", m.get("enredado") is True)

    r._save_mostrado = _mk_save(True)    # sucesso → solta, turno gasto
    consumiu = await r._processar_enredado_turno(m)
    check("sucesso: turno consumido", consumiu is True)
    check("sucesso: soltou", not m.get("enredado"))
    check("sucesso: limpou save/cd", "enredado_cd" not in m and "enredado_save" not in m)

    m2 = make_monster(r, "m2", 5, 5)     # não enredado → não consome
    check("não enredado → False", (await r._processar_enredado_turno(m2)) is False)

    # ── [5] Arremesso da Cola e da Rede (acerto) ───────────────────────────────
    print("\n[5] handle_throw_item (cola/rede) — acerto")
    S.random.randint = _fixed_d20(15)   # acerto não-crítico, não-nat1

    r = setup(); r._save_mostrado = _mk_save(False)   # falha no Reflexos → cola pega
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("cola_alquimica")]
    m = make_monster(r, "m1", 4, 6, ac=1, movement=6)
    await r.handle_throw_item("p1", {"item_id": "cola_alquimica", "target_id": "m1"})
    check("cola: movement zerado (6→0)", m["movement"] == 0)
    check("cola: mov_reduzido_rodadas=2", m.get("mov_reduzido_rodadas") == 2)
    pos_antes = list(m["pos"])
    await r._monster_move_step(m, p["pos"])
    check("cola: IA não desloca o alvo", m["pos"] == pos_antes)
    check("cola: orçamento de movimento zero", r._water_turn_moves(m, 12) == 0)
    m["master_moves_left"] = 6
    check("cola: movimento manual bloqueado", r._manual_move_paths(m) == {}
          and await r._commit_monster_step(m, pos_antes[0], pos_antes[1] + 1) is False)
    check("cola: item consumido", len(p["bag"]) == 0)
    check("cola: sem dano (hp intacto)", m["hp"] == 40)

    if cola_superior_loja and cola_superior:
        r = setup()
        save_calls = []
        async def save_cd18(alvo, tipo, cd, *a, **k):
            save_calls.append((tipo, cd))
            return (False, 1, 0, 1)
        r._save_mostrado = save_cd18
        p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["atk_bonus"] = 5
        r.players["p1"] = p; p["bag"] = [throwable("cola_alquimica_superior")]
        m = make_monster(r, "m1", 4, 6, ac=1, movement=6)
        await r.handle_throw_item("p1", {"item_id": "cola_alquimica_superior", "target_id": "m1"})
        check("cola superior: arremesso aplica save Reflexos CD18", save_calls == [("reflexos", 18)])
        check("cola superior: falha zera o movimento por 2 rodadas",
              m["movement"] == 0 and m.get("cola_sem_movimento") is True
              and m.get("mov_reduzido_rodadas") == 2)
        check("cola superior: consumida após o arremesso", len(p["bag"]) == 0)
    else:
        check("cola superior: arremesso aplica save Reflexos CD18", False)
        check("cola superior: falha zera o movimento por 2 rodadas", False)
        check("cola superior: consumida após o arremesso", False)

    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("rede_arremesso")]
    m = make_monster(r, "m1", 4, 6, ac=1)
    await r.handle_throw_item("p1", {"item_id": "rede_arremesso", "target_id": "m1"})
    check("rede: enredado", m.get("enredado") is True)
    check("rede: item consumido", len(p["bag"]) == 0)

    # ── [6] Erro: item consumido, sem efeito ───────────────────────────────────
    print("\n[6] handle_throw_item (tático) — erro")
    r = setup()
    p = make_player("p1", "V", "warrior", 0); p["pos"] = [4, 4]; p["atk_bonus"] = 5
    r.players["p1"] = p; p["bag"] = [throwable("cola_alquimica")]
    m = make_monster(r, "m1", 4, 6, ac=99, movement=6)   # 15+5 < 99 → erro
    await r.handle_throw_item("p1", {"item_id": "cola_alquimica", "target_id": "m1"})
    check("erro: movement intacto", m["movement"] == 6)
    check("erro: sem mov_reduzido", not m.get("mov_reduzido_rodadas"))
    check("erro: item consumido", len(p["bag"]) == 0)
    S.random.randint = _REAL_RANDINT

    print(f"\n=== {PASS} OK / {FAIL} FALHAS ===")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    asyncio.run(main())
