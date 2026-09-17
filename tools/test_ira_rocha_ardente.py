"""Testes da magia Ira da Rocha Ardente.

Roda da raiz:
    python -X utf8 tools/test_ira_rocha_ardente.py
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


PASS = 0
FAIL = 0


def check(name, condition):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}")


def setup():
    room = S.GameRoom("TEST")
    messages = []

    async def noop(*args, **kwargs):
        return None

    async def send_to(pid, msg, *args, **kwargs):
        messages.append((pid, msg))

    room.broadcast = noop
    room.push_state = noop
    room.gm_say = noop
    room._broadcast_dado = noop
    room.send_to = send_to
    room._tem_linha_de_visao = lambda *args, **kwargs: True
    room._alcance_com_altura = lambda *args, **kwargs: True
    room.map_w = room.map_h = 10
    room.tiles = [[S.FLOOR] * 10 for _ in range(10)]
    room.explored = {(x, y) for y in range(10) for x in range(10)}
    room.phase = "playing"
    room.monsters = {}
    room.decorations = []
    room._rebuild_decor_index()
    room.materiais = {}
    room._rebuild_materiais_index()
    room.round_num = 1
    return room, messages


def add_cleric(room, level=6, pos=(4, 4)):
    cleric = S.make_player("c", "Lewis", "cleric", 0)
    cleric.update(level=level, pos=list(pos), alive=True, hp=50, max_hp=50,
                  fome=40, sede=40, action_done=False)
    cleric["magias_conhecidas"] = ["ira_rocha_ardente"]
    room.players["c"] = cleric
    room.player_order = ["c"]
    room.initiative_active = True
    room._rebuild_initiative()
    return cleric


async def cast(room, messages, center=(4, 4)):
    old_roll = S.roll_dice

    def fixed_roll(expr):
        expr = str(expr)
        if expr == "1d4":
            return 3
        if expr == "2d4":
            return 4
        if expr == "2d6":
            return 7
        return old_roll(expr)

    S.roll_dice = fixed_roll
    try:
        await room.handle_magia("c", {
            "magia_id": "ira_rocha_ardente",
            "tx": center[0],
            "ty": center[1],
        })
    finally:
        S.roll_dice = old_roll
    return next(z for z in room.zonas_especiais
                if z.get("tipo") == "ira_rocha_ardente")


async def cast_dur_minima(room, messages, center=(4, 4)):
    """Lança forçando o PIOR 1d4 (=1), o caso que zerava a janela das Chamas."""
    old_roll = S.roll_dice

    def fixed_roll(expr):
        expr = str(expr)
        if expr == "1d4":
            return 1
        if expr == "2d4":
            return 4
        if expr == "2d6":
            return 7
        return old_roll(expr)

    S.roll_dice = fixed_roll
    try:
        await room.handle_magia("c", {
            "magia_id": "ira_rocha_ardente",
            "tx": center[0],
            "ty": center[1],
        })
    finally:
        S.roll_dice = old_roll
    return next(z for z in room.zonas_especiais
                if z.get("tipo") == "ira_rocha_ardente")


async def main():
    print("\n[1] Escala, duração, alcance e dano inicial")
    room, messages = setup()
    cleric = add_cleric(room, level=6)
    zone = await cast(room, messages)
    check("área 5x5 no nível 6", zone["lado"] == 5 and len(zone["tiles"]) == 25)
    check("duração 5 no nível 6", zone["duracao"] == 5)
    check("lava aplicada às casas", all(room.materiais.get(tuple(tile)) == "lava" for tile in zone["tiles"]))
    check("dano inicial de lava aplicado", cleric["hp"] == 44)
    check("chamas ficam disponíveis só na 2ª rodada",
          zone["disponivel_em"] == room.round_num + 1)
    check("área das chamas é 1x1 maior que a lava",
          len(zone["chamas_permitidas"]) > len(zone["tiles"])
          and [2, 2] in zone["chamas_permitidas"])

    print("\n[2] Escolha parcial cria Chamas Vivas e preserva o restante")
    permitidos = zone["chamas_permitidas"]
    escolhidos = [[4, 4]]
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], escolhidos)
    check("escolha na 1ª rodada foi recusada", not room.decorations)
    room.round_num = zone["disponivel_em"]
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], escolhidos)
    flames = [d for d in room.decorations if d.get("type") == "chama_viva"]
    check("uma decoração foi criada", len(flames) == 1)
    check("posições escolhidas foram respeitadas",
          {tuple(d["pos"]) for d in flames} == {tuple(p) for p in escolhidos})
    check("chamas restantes continuam pendentes", zone["chamas_pendentes"] == 3)
    check("casa usada saiu das opções futuras", [4, 4] not in zone["chamas_permitidas"])
    check("chamas ficam indexadas como 2d4",
          all(room._fire_damage_tiles.get(tuple(p)) == "2d4" for p in escolhidos))
    check("dano da chama soma ao dano da lava", cleric["hp"] < 44)

    posteriores = zone["chamas_permitidas"][:3]
    room.round_num += 1
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], posteriores)
    flames = [d for d in room.decorations if d.get("type") == "chama_viva"]
    check("o restante pode ser colocado em rodada posterior", len(flames) == 4)
    check("nenhuma chama ficou pendente", zone["chamas_pendentes"] == 0)

    print("\n[3] A área expira e restaura o mapa")
    base_tile = tuple(zone["tiles"][0])
    room.round_num = zone["expira_em"]
    await room._processar_zonas_turno()
    check("zona ficou inativa", not zone["ativa"])
    check("lava foi removida", room.materiais.get(base_tile) != "lava")
    check("Chamas Vivas foram removidas", not any(
        d.get("ira_rocha_ardente_id") == zone["id"] for d in room.decorations))

    print("\n[4] Validação rejeita escolha vazia e excesso")
    room, messages = setup()
    add_cleric(room, level=6)
    zone = await cast(room, messages)
    room.round_num = zone["disponivel_em"]
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], [])
    check("escolha vazia foi recusada", not room.decorations)
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], zone["chamas_permitidas"] + [[999, 999]])
    check("escolha acima do restante foi recusada", not room.decorations)
    check("erro foi enviado", any(msg.get("type") == "error" for _, msg in messages))

    print("\n[5] A janela para colocar as Chamas Vivas nunca é vazia")
    # As chamas liberam em `disponivel_em` = rodada+1 e a lava morre em
    # `expira_em` = rodada+duração. Com 1d4=1 no nível 1 os dois coincidiam: a
    # zona expirava exatamente na rodada em que as chamas liberariam, então o
    # slot de 4º círculo era gasto e as Chamas Vivas eram IMPOSSÍVEIS.
    room, messages = setup()
    cleric = add_cleric(room, level=1)
    zone = await cast_dur_minima(room, messages)
    check("duração mínima 2 (piso) mesmo com 1d4=1", zone["duracao"] == 2)
    check("sobra ao menos 1 rodada para colocar",
          zone["expira_em"] > zone["disponivel_em"])
    # E a colocação funciona de verdade nessa única rodada. O avanço passa
    # por _processar_zonas_turno, como no jogo: era ELE que desativava a zona
    # antes de o clérigo ter qualquer chance de escolher as casas.
    room.round_num = zone["disponivel_em"]
    await room._processar_zonas_turno()
    escolhidos = zone["chamas_permitidas"][:zone["chamas_pendentes"]]
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], escolhidos)
    check("as chamas realmente entram nessa rodada",
          len([d for d in room.decorations if d.get("type") == "chama_viva"]) == len(escolhidos))
    check("a zona ainda estava ativa quando as chamas entraram", zone["ativa"])

    print("\n[6] Mira inválida não cobra slot, fome/sede nem ação (preflight)")
    # A validação de centro/alcance/parede/piso morava DENTRO do executor,
    # depois do pagamento em handle_magia: uma parede no caminho devolvia o
    # erro com o slot de 4º círculo, 🍖/💧 e a ação já gastos. Aqui a LOS e o
    # alcance são os REAIS (a suíte acima os mocka).
    def setup_real():
        room, messages = setup()
        del room._tem_linha_de_visao
        del room._alcance_com_altura
        room.map_w = room.map_h = 12
        room.tiles = [[S.FLOOR] * 12 for _ in range(12)]
        room.explored = {(x, y) for y in range(12) for x in range(12)}
        return room, messages

    def recursos(p):
        return (room._slots_disponiveis(p, "quarto"), p["fome"], p["sede"], p["action_done"])

    async def tenta(room, messages, tx, ty):
        messages.clear()
        await room.handle_magia("c", {"magia_id": "ira_rocha_ardente", "tx": tx, "ty": ty})
        return [m for _, m in messages if m.get("type") == "error"]

    room, messages = setup_real()
    cleric = add_cleric(room, level=6, pos=(4, 5))
    for y in range(12):
        room.tiles[y][6] = S.WALL          # parede vertical em x=6
    antes = recursos(cleric)
    erros = await tenta(room, messages, 8, 5)  # alcance 7, atrás da parede
    check("parede: erro enviado", bool(erros))
    check("parede: slot/fome/sede/ação intactos", recursos(cleric) == antes)
    check("parede: nenhuma zona criada",
          not any(z.get("ativa") for z in room.zonas_especiais))
    room.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    cleric["pos"] = [0, 0]
    antes = recursos(cleric)
    erros = await tenta(room, messages, 11, 11)  # dist 11 > alcance 7
    check("fora do alcance: erro enviado", bool(erros))
    check("fora do alcance: recursos intactos", recursos(cleric) == antes)
    erros = await tenta(room, messages, "x", None)
    check("centro inválido: recursos intactos", recursos(cleric) == antes)
    erros = await tenta(room, messages, 2, 2)  # válido
    check("mira válida: slot e ação gastos", recursos(cleric) != antes)
    check("mira válida: zona criada",
          any(z.get("ativa") for z in room.zonas_especiais))

    print("\n[7] A área das Chamas Vivas é um anel completo ao redor da lava")
    # `lado + 1` com a âncora de quadrado par deixava a casa extra só de UM
    # lado (direita/abaixo no lado ímpar, esquerda/acima no lado par). "1x1
    # maior" é o anel inteiro: lado + 2 com a mesma âncora.
    for level, lado in ((1, 3), (3, 4), (6, 5)):
        room, messages = setup()
        room.map_w = room.map_h = 16
        room.tiles = [[S.FLOOR] * 16 for _ in range(16)]
        room.explored = {(x, y) for y in range(16) for x in range(16)}
        add_cleric(room, level=level, pos=(8, 8))
        zone = await cast(room, messages, center=(8, 8))
        lava = {tuple(t) for t in zone["tiles"]}
        anel = {(x + dx, y + dy) for x, y in lava for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
        check(f"nível {level} (lado {lado}): permitidas == lava + anel de 1 casa",
              set(map(tuple, zone["chamas_permitidas"])) == anel)

    print("\n[8] Empoderar Magia (×1,5) vale para a lava da Ira")
    # `_magia_tem_dano` reconhece `dano_lava`, então a técnica exclusiva era
    # consumida (recarga 8 + 🍖/💧) — mas o despacho não passava `dmg_mult` à
    # Ira e a lava usava "2d6" cravado. O multiplicador tem de valer no dano
    # inicial E em quem pisa/inicia o turno na lava enquanto a zona existe.
    room, messages = setup()
    cleric = add_cleric(room, level=6)
    cleric["tec_ex_empoderar_armado"] = True
    # 2d6 fixo em 7 → ×1,5 = 10,5 → 11; o Escudo Pequeno do Lewis tira 1 de
    # cada instância (é por isso que a seção [1] espera 44, e não 43).
    zone = await cast(room, messages)
    check("dano inicial multiplicado (7 × 1,5 → 11, −1 do escudo)", cleric["hp"] == 50 - 10)
    check("técnica consumida no lançamento", not cleric.get("tec_ex_empoderar_armado"))
    old_roll = S.roll_dice
    S.roll_dice = lambda expr: 7 if str(expr) == "2d6" else old_roll(expr)
    try:
        hp = cleric["hp"]
        await room._aplicar_lava_se_pisar(cleric)
        check("pisar/iniciar turno na lava da Ira também multiplica", cleric["hp"] == hp - 10)
        outro = S.make_player("w", "Ana", "warrior", 1)
        outro.update(level=1, pos=[0, 0], alive=True, hp=50, max_hp=50)
        room.players["w"] = outro
        room.materiais[(0, 0)] = "lava"        # lava do MAPA, fora da zona
        room._rebuild_materiais_index()
        await room._aplicar_lava_se_pisar(outro)
        check("lava fora da zona continua 2d6 sem multiplicador", outro["hp"] == 50 - 7)
    finally:
        S.roll_dice = old_roll

    print("\n[9] Chama Viva sob qualquer casa do footprint de um monstro grande")
    # `_aplicar_fogueira_se_pisar` lia só `pos` (a âncora); a lava, por
    # contraste, usa o footprint. Um troll 2×2 com a chama sob a casa de trás
    # não sofria nada — nem ao ser colocada, nem ao pisar.
    room, messages = setup()
    room.map_w = room.map_h = 16
    room.tiles = [[S.FLOOR] * 16 for _ in range(16)]
    room.explored = {(x, y) for y in range(16) for x in range(16)}
    add_cleric(room, level=6, pos=(2, 2))
    mdef = next(d for d in S.MONSTER_DEFS if d["type"] == "troll")
    troll = S.make_monster(mdef, {"cx": 9, "cy": 9, "id": 0})
    troll.update(id="m1", pos=[9, 9], size=[2, 2], hp=100, max_hp=100, resistances=[])
    troll.pop("oriented", None)
    room.monsters["m1"] = troll
    zone = await cast(room, messages, center=(8, 8))   # lava 5x5: 6..10 — troll dentro
    room.round_num = zone["disponivel_em"]
    hp = troll["hp"]
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], [[10, 10]])   # casa de trás
    check("chama colocada sob casa não-âncora causa dano", troll["hp"] < hp)
    hp = troll["hp"]
    troll["pos"] = [8, 8]                     # footprint 8..9 — sai da chama
    await room._aplicar_fogueira_se_pisar(troll)
    check("footprint fora da chama: sem dano", troll["hp"] == hp)
    troll["pos"] = [9, 9]                     # volta: chama sob (10,10), não sob a âncora
    await room._aplicar_fogueira_se_pisar(troll)
    check("footprint que cobre a chama ao pisar: dano", troll["hp"] < hp)

    print("\n[10] Servo animado e prisioneiro também queimam ao pisar na Chama Viva")
    # Os caminhos de movimento deles chamavam `_aplicar_lava_se_pisar` mas
    # nunca `_aplicar_fogueira_se_pisar`: passavam por chamas (e fogueiras)
    # sem sofrer nada, ao contrário de heróis e monstros.
    room, messages = setup()
    cleric = add_cleric(room, level=6, pos=(1, 1))
    zone = await cast(room, messages, center=(5, 5))
    room.round_num = zone["disponivel_em"]
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], [[8, 8], [8, 2]])   # anel, fora da lava (3..7)
    check("chamas colocadas fora da lava",
          room._fire_damage_tiles.get((8, 8)) == "2d4" and room._fire_damage_tiles.get((8, 2)) == "2d4")
    room.animados_phase_pid = "c"
    servo = {"id": "a1", "tipo": "goblin", "nome_base": "Goblin", "vida_atual": 30, "vida_max": 30,
             "pos": [8, 9], "moves_left": 3, "ataque": 1, "dano": "1d6"}
    cleric["animados"] = [servo]
    await room.handle_mover_animado("c", "a1", 0, -1)          # (8,9) → (8,8)
    check("servo andou para a chama", servo["pos"] == [8, 8])
    check("servo sofreu o dano da chama", servo["vida_atual"] < 30)
    room.prisoner = {"name": "Prisioneiro", "freed": True, "alive": True, "rescuer_pid": "c",
                     "moves_left": 3, "pos": [9, 2], "hp": 20, "max_hp": 20}
    await room.handle_mover_prisioneiro("c", -1, 0)            # (9,2) → (8,2)
    check("prisioneiro andou para a chama", room.prisoner["pos"] == [8, 2])
    check("prisioneiro sofreu o dano da chama", room.prisoner["hp"] < 20)

    print("\n[11] Colocação revalida as casas e narra as rodadas RESTANTES")
    room, messages = setup()
    add_cleric(room, level=6, pos=(1, 1))
    zone = await cast(room, messages, center=(5, 5))
    # Uma decoração que surgiu DEPOIS da conjuração (a lista `chamas_permitidas`
    # era calculada uma vez e nunca conferida de novo) não pode receber chama.
    room.decorations.append({"id": "d_novo", "type": "barril", "pos": [8, 8], "facing": [0, 1]})
    room._rebuild_decor_index()
    room.round_num = zone["disponivel_em"] + 1          # 2 rodadas depois de lançar
    narrado = []
    async def gm_say(msg, *a, **k):
        narrado.append(msg)
    room.gm_say = gm_say
    await room.handle_ira_rocha_ardente_chamas("c", zone["id"], [[8, 8], [8, 2]])
    flames = {tuple(d["pos"]) for d in room.decorations if d.get("type") == "chama_viva"}
    check("casa ocupada por decoração nova foi recusada", (8, 8) not in flames)
    check("as demais casas válidas entraram", (8, 2) in flames)
    restantes = zone["expira_em"] - room.round_num
    narr = next((m for m in narrado if getattr(m, "key", "") == "narracao.ira_da_rocha_chamas_vivas_colocadas"), None)
    check("narração cita as rodadas restantes, não a duração total",
          narr is not None and narr.params.get("dur") == restantes and restantes != zone["duracao"])

    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    return 1 if FAIL else 0


sys.exit(asyncio.run(main()))
