"""Guilda dos Heróis — Fase 0. Roda da raiz: python tools/test_guilda.py"""
import asyncio, sys, os
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S
from server import GameRoom, make_player

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def setup(phase="city"):
    r = GameRoom("TEST")
    errs = []; calls = {"city": 0, "push": 0}
    async def noop(*a, **k): pass
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": errs.append(msg.get("msg",""))
    async def cap_city(*a, **k): calls["city"] += 1
    async def cap_push(*a, **k): calls["push"] += 1
    r.gm_say = noop; r.broadcast = noop; r._broadcast_dado = noop
    r.broadcast_city_state = cap_city; r.push_state = cap_push; r.send_to = cap_send
    r.phase = phase; r._errs = errs; r._calls = calls
    return r

async def main():
    import tempfile, shutil
    S.CHARACTERS_IN_USE.clear() if hasattr(S, "CHARACTERS_IN_USE") else None

    # [1] make_player tem os campos da guilda
    print("\n[1] Campos da guilda no make_player")
    p = make_player("p1", "Victor", "warrior", 0)
    check("guild_owned.especializacoes vazio", p["guild_owned"]["especializacoes"] == [])
    check("guild_owned.tecnicas vazio", p["guild_owned"]["tecnicas"] == [])
    check("guild_equip.tecnica None", p["guild_equip"]["tecnica"] is None)
    check("technique_cooldowns vazio", p["technique_cooldowns"] == {})

    # [2] save round-trip em pasta temporária
    print("\n[2] Save round-trip")
    tmp = tempfile.mkdtemp()
    old_dir = S.GUILD_SAVE_DIR
    S.GUILD_SAVE_DIR = tmp
    try:
        p["guild_owned"]["tecnicas"] = ["brutalidade"]
        p["guild_equip"]["tecnica"] = "brutalidade"
        S.write_guild_save(p)
        loaded = S.load_guild_save("warrior")
        check("carregou tecnicas", loaded["tecnicas"] == ["brutalidade"])
        check("carregou equip.tecnica", loaded["equip"]["tecnica"] == "brutalidade")
        check("classe sem save → vazio", S.load_guild_save("mage")["tecnicas"] == [])
        with open(os.path.join(tmp, "rogue.json"), "w", encoding="utf-8") as f:
            f.write("{lixo}")
        check("save corrompido → vazio", S.load_guild_save("rogue")["tecnicas"] == [])
        # valid JSON, wrong top-level type → vazio
        with open(os.path.join(tmp, "paladin.json"), "w", encoding="utf-8") as f:
            f.write("[1,2,3]")
        check("save JSON lista → vazio", S.load_guild_save("paladin")["tecnicas"] == [])
        # valid JSON, wrong field type → vazio (não vira ['o','o','p','s'])
        with open(os.path.join(tmp, "bard.json"), "w", encoding="utf-8") as f:
            f.write('{"tecnicas": "oops"}')
        check("save campo tipo errado → vazio", S.load_guild_save("bard")["tecnicas"] == [])
        q = make_player("p2", "Victor", "warrior", 0)
        S.apply_guild_save(q)
        check("apply_guild_save popula", q["guild_owned"]["tecnicas"] == ["brutalidade"]
              and q["guild_equip"]["tecnica"] == "brutalidade")
    finally:
        S.GUILD_SAVE_DIR = old_dir
        shutil.rmtree(tmp, ignore_errors=True)

    # [3] Catálogo
    print("\n[3] GUILD_CATALOG")
    b = S.guild_item("brutalidade")
    check("brutalidade existe", b is not None)
    check("categoria tecnica", b["categoria"] == "tecnica")
    check("recarga 3", b["recarga_rodadas"] == 3)
    check("custo 2/2", b["custo_fome"] == 2 and b["custo_sede"] == 2)
    itens_w = S.guild_items_for_class("warrior")
    check("brutalidade aplicável a warrior", any(i["id"] == "brutalidade" for i in itens_w))
    check("item None → não existe", S.guild_item("nao_existe") is None)

    # [4] Trava de personagem em uso
    print("\n[4] Trava de em-uso")
    S.CHARACTERS_IN_USE.clear()
    r1 = setup("lobby")
    r1.players["a"] = {"id": "a", "class_id": None}
    await r1.select_class("a", "mage")
    check("sala1 escolheu mage", r1.players["a"]["class_id"] == "mage")
    check("mage travado p/ TEST", S.CHARACTERS_IN_USE.get("mage") == "TEST")
    r2 = GameRoom("OUTRA")
    r2._errs = []
    async def cap2(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": r2._errs.append(msg["msg"])
    r2.send_to = cap2
    async def noop2(*a, **k): pass
    r2.broadcast_lobby = noop2
    r2.players["b"] = {"id": "b", "class_id": None}
    await r2.select_class("b", "mage")
    check("sala2 recusada (mage em uso)", r2.players["b"]["class_id"] is None and r2._errs)
    r1.release_character("a")
    check("release liberou mage", "mage" not in S.CHARACTERS_IN_USE)

    # [5] Carga do save ao iniciar
    print("\n[5] start_game carrega save")
    import tempfile, shutil
    tmp5 = tempfile.mkdtemp(); old5 = S.GUILD_SAVE_DIR; S.GUILD_SAVE_DIR = tmp5
    S.CHARACTERS_IN_USE.clear()
    try:
        seed = make_player("x", "Victor", "warrior", 0)
        seed["guild_owned"]["tecnicas"] = ["brutalidade"]
        S.write_guild_save(seed)
        r = setup("lobby")
        async def noop3(*a, **k): pass
        r.broadcast = noop3; r.broadcast_lobby = noop3
        r.players["a"] = {"id": "a", "name": "Victor", "class_id": "warrior", "ready": True}
        r.host_pid = "a"
        await r.start_game("a")
        check("save carregado no start (owned)",
              r.players["a"]["guild_owned"]["tecnicas"] == ["brutalidade"])
    finally:
        S.GUILD_SAVE_DIR = old5; shutil.rmtree(tmp5, ignore_errors=True); S.CHARACTERS_IN_USE.clear()

    # [6] Compra
    print("\n[6] handle_guild_buy")
    import tempfile, shutil
    tmp6 = tempfile.mkdtemp(); old6 = S.GUILD_SAVE_DIR; S.GUILD_SAVE_DIR = tmp6
    try:
        r = setup("city")
        w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
        w["gold"] = 200
        await r.handle_guild_buy("p1", "brutalidade")
        check("comprou brutalidade", "brutalidade" in w["guild_owned"]["tecnicas"])
        check("debitou ouro (200-120)", w["gold"] == 80)
        check("persistiu", "brutalidade" in S.load_guild_save("warrior")["tecnicas"])
        n0 = len(w["guild_owned"]["tecnicas"])
        await r.handle_guild_buy("p1", "brutalidade")
        check("não duplica compra", len(w["guild_owned"]["tecnicas"]) == n0)
        r2 = setup("city"); w2 = make_player("p2","Victor","warrior",0); r2.players["p2"]=w2
        w2["gold"] = 10
        await r2.handle_guild_buy("p2", "brutalidade")
        check("recusa sem ouro", "brutalidade" not in w2["guild_owned"]["tecnicas"] and r2._errs)
        await r2.handle_guild_buy("p2", "nao_existe")
        check("recusa item inexistente", len(r2._errs) >= 2)
    finally:
        S.GUILD_SAVE_DIR = old6; shutil.rmtree(tmp6, ignore_errors=True)

    # [7] Equipar
    print("\n[7] handle_guild_equip")
    tmp7 = tempfile.mkdtemp(); old7 = S.GUILD_SAVE_DIR; S.GUILD_SAVE_DIR = tmp7
    try:
        r = setup("city")
        w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
        w["guild_owned"]["tecnicas"] = ["brutalidade"]
        await r.handle_guild_equip("p1", "tecnica", "brutalidade")
        check("equipou brutalidade", w["guild_equip"]["tecnica"] == "brutalidade")
        check("persistiu equip", S.load_guild_save("warrior")["equip"]["tecnica"] == "brutalidade")
        await r.handle_guild_equip("p1", "tecnica", None)
        check("desequipou", w["guild_equip"]["tecnica"] is None)
        r._errs.clear()
        await r.handle_guild_equip("p1", "tecnica", "brutalidade_fantasma")
        check("recusa técnica não possuída", w["guild_equip"]["tecnica"] is None and r._errs)
        r._errs.clear()
        await r.handle_guild_equip("p1", "tecnica_exclusiva", "brutalidade")
        check("warrior recusa slot exclusivo", w["guild_equip"]["tecnica_exclusiva"] is None and r._errs)
        rm = setup("city"); m = make_player("m","Pedro","mage",0); rm.players["m"] = m
        m["guild_owned"]["tecnicas"] = ["brutalidade"]
        await rm.handle_guild_equip("m", "tecnica", "brutalidade")
        check("mago equipa genérica", m["guild_equip"]["tecnica"] == "brutalidade")
        rm._errs.clear()
        await rm.handle_guild_equip("m", "tecnica_exclusiva", "brutalidade")
        check("exclusiva recusa técnica não-exclusiva", m["guild_equip"]["tecnica_exclusiva"] is None and rm._errs)
    finally:
        S.GUILD_SAVE_DIR = old7; shutil.rmtree(tmp7, ignore_errors=True)

    # [8] Usar técnica de preparo (Brutalidade): custo/recarga ADIADOS para o efeito
    # Brutalidade é "buff_turno" (efeitos_adiados): ativar só arma o buff; o custo
    # de fome/sede e a recarga só começam quando o ataque que ela modifica é
    # executado (_consumir_tecnica_apos_efeito, chamado em handle_attack).
    print("\n[8] usar_tecnica + recarga (preparo adiado)")
    r = setup("playing")
    w = make_player("p1", "Victor", "warrior", 0); r.players["p1"] = w
    r.player_order = ["p1"]; r.turn_index = 0; r.round_num = 1
    w["guild_owned"]["tecnicas"] = ["brutalidade"]
    w["guild_equip"]["tecnica"] = "brutalidade"
    w["fome"] = 50; w["sede"] = 50
    await r.handle_usar_tecnica("p1", "brutalidade")
    check("buff de dano aplicado (+2)", w["tecnica_buff_dano_arma"] == 2)
    check("marcada como preparada (technique_pending)", w.get("technique_pending", {}).get("brutalidade") is True)
    check("custo NÃO debitado na ativação", w["fome"] == 50 and w["sede"] == 50)
    check("recarga NÃO inicia na ativação", "brutalidade" not in w["technique_cooldowns"])
    r._errs.clear()   # mesma lista capturada por cap_send (não rebind)
    await r.handle_usar_tecnica("p1", "brutalidade")
    check("reuso bloqueado enquanto preparada", len(r._errs) >= 1)
    # O ataque que usa a técnica consome o preparo → agora custo + recarga entram.
    consumiu = r._consumir_tecnica_apos_efeito(w, "brutalidade")
    check("consumo pós-efeito retorna True", consumiu is True)
    check("custo debitado no efeito (2/2)", w["fome"] == 48 and w["sede"] == 48)
    check("recarga inicia no efeito (round_num+3)", w["technique_cooldowns"]["brutalidade"] == 1 + 3)
    check("technique_pending limpo após consumo", "brutalidade" not in w.get("technique_pending", {}))
    r._errs.clear()
    await r.handle_usar_tecnica("p1", "brutalidade")
    check("reuso bloqueado em recarga", len(r._errs) >= 1)
    r._cancelar_timer_turno = lambda *a, **k: None   # sem loop de timer no teste
    await r._voltar_para_cidade()
    check("cidade zera cooldowns", w["technique_cooldowns"] == {})

    # [9] Prontidão via helper
    print("\n[9] tecnica_restante")
    r.round_num = 1
    w["technique_cooldowns"] = {"brutalidade": 4}
    check("restante = 3", r.tecnica_restante(w, "brutalidade") == 3)
    w["technique_cooldowns"] = {}
    check("restante = 0 quando ausente", r.tecnica_restante(w, "brutalidade") == 0)

    # [10] Bônus de dano da técnica no cálculo
    print("\n[10] bônus de dano da técnica")
    w["tecnica_buff_dano_arma"] = 2
    check("helper soma +2", r._tecnica_bonus_dano(w) == 2)
    w["tecnica_buff_dano_arma"] = 0
    check("helper soma 0 sem buff", r._tecnica_bonus_dano(w) == 0)

    print(f"\n{'='*40}\n  {PASS} passaram, {FAIL} falharam\n{'='*40}")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
