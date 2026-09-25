"""Campanha "Sombras sob Alva e Luz". Roda da raiz: python tools/test_campanha_sombras.py

Não depende dos arquivos gerados no repositório: monta tudo pelo gerador, grava
as masmorras numa pasta temporária (DUNGEONS_DIR) e os destinos/cena em memória,
e restaura o estado do servidor no fim de cada seção.
Spec: docs/superpowers/specs/2026-09-25-campanha-sombras-alva-e-luz-design.md
"""
import asyncio
import json
import os
import shutil
import sys
import tempfile
from copy import deepcopy

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
for p in (RAIZ, AQUI):
    if p not in sys.path:
        sys.path.insert(0, p)
import server as S                       # noqa: E402
import gerar_campanha_sombras as G       # noqa: E402

PASS = 0
FAIL = 0


def check(nome, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {nome}")
    else:
        FAIL += 1
        print(f"  ❌ {nome}")


ART = G.preparar()
MM = ART["masmorras"]

# Faixas planejadas na spec (ND arredondado, faixa pelo termômetro).
ESPERADO = {
    "sombras_1_vau.json": {0: (1.0, "facil"), 1: (1.25, "facil"), 2: (2.0, "equilibrada")},
    "sombras_2_minas.json": {0: (1.25, "facil"), 1: (0.95, "facil"), 2: (2.0, "facil"),
                             3: (3.5, "equilibrada")},
    "sombras_3a_saloes.json": {0: (0.0, "facil"), 1: (2.5, "facil"), 2: (2.5, "facil"),
                               3: (3.5, "facil")},
    "sombras_3b_trono.json": {0: (0.0, "facil"), 1: (5.5, "equilibrada"), 2: (2.5, "facil")},
}


# ─── Sala de jogo pelo caminho real ──────────────────────────────────────────
class Ambiente:
    """Masmorras numa pasta temporária + destinos e conversa injetados em memória.
    Restaura DUNGEONS_DIR, WORLD_ADVENTURES e a cena da taverna ao sair."""

    def __enter__(self):
        self.tmp = tempfile.mkdtemp(prefix="sombras_")
        for arquivo, defn in MM.items():
            with open(os.path.join(self.tmp, arquivo), "w", encoding="utf-8") as f:
                json.dump(defn, f, ensure_ascii=False)
        self.dir_antigo = S.DUNGEONS_DIR
        self.aventuras_antigas = deepcopy(S.WORLD_ADVENTURES)
        self.cena_antiga = deepcopy(S.CITY_SCENES["alva_e_luz"]["taverna"])
        S.DUNGEONS_DIR = self.tmp
        S.WORLD_ADVENTURES.update(deepcopy(ART["destinos"]))
        barman = next(s for s in S.CITY_SCENES["alva_e_luz"]["taverna"]["slots"] if s.get("id") == "barman")
        barman["conversations"] = [c for c in barman.get("conversations", [])
                                   if c.get("id") != G.CONVERSA_ID] + [deepcopy(ART["conversa"])]
        return self

    def __exit__(self, *exc):
        S.DUNGEONS_DIR = self.dir_antigo
        S.WORLD_ADVENTURES.clear()
        S.WORLD_ADVENTURES.update(self.aventuras_antigas)
        S.CITY_SCENES["alva_e_luz"]["taverna"] = self.cena_antiga
        shutil.rmtree(self.tmp, ignore_errors=True)


def sala_na_cidade():
    r = S.GameRoom("SOMB")
    erros = []

    async def noop(*a, **k):
        pass

    async def cap(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error":
            erros.append(str(msg.get("msg")))
    r.gm_say = noop
    r.broadcast = noop
    r.send_to = cap
    r.broadcast_city_state = noop
    r.push_state = noop
    r.push_state_or_city = noop
    r._broadcast_dado = noop
    r._checkpoint_savegame = lambda *a, **k: None
    for i, cls in enumerate(("warrior", "cleric", "rogue", "mage")):
        pid = f"h{i}"
        r.players[pid] = S.make_player(pid, cls, cls, i)
        r.connections[pid] = object()
    r.host_pid = "h0"
    r.phase = "city"
    r.world_location = "alva_e_luz"
    r._is_turn = lambda pid: True
    r._erros = erros
    return r


async def entrar(r, destino):
    await r.handle_world_adventure("h0", destino)
    await r._liberar_intro_masmorra(True)


def junto(r, pid, pos):
    """Põe o herói numa casa livre vizinha de `pos` (Chebyshev 1)."""
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        x, y = pos[0] + dx, pos[1] + dy
        if r.tiles[y][x] == S.FLOOR and not r._entity_blocks(x, y):
            r.players[pid]["pos"] = [x, y]
            return True
    return False


# ─── [1] Mapas ───────────────────────────────────────────────────────────────
def secao_mapas():
    print("\n[1] As 4 masmorras: validade, ocupação, ND e conectividade")
    check("o gerador produz as 4 masmorras", sorted(MM) == sorted(G.ARQUIVOS))
    for arquivo, defn in MM.items():
        ok, msg = S.validar_dungeon(defn)
        check(f"{arquivo}: validar_dungeon ({msg})", ok)
        ocupado, conflito = {}, []

        def por(p, oque):
            k = tuple(p)
            if k in ocupado:
                conflito.append((k, ocupado[k], oque))
            ocupado[k] = oque
        for mo in defn["monsters"]:
            por(mo["pos"], mo["type"])
        for de in defn["decorations"]:
            w, h = S.DECOR_TYPES[de["type"]].get("size", [1, 1])
            for dx in range(w):
                for dy in range(h):
                    por([de["pos"][0] + dx, de["pos"][1] + dy], de["id"])
        for ch in defn["chests"]:
            por(ch["pos"], "baú")
        for t in defn["traps"]:
            por(t["pos"], t["tipo"])
        if defn.get("prisoner"):
            por(defn["prisoner"]["pos"], "prisioneiro")
        por([defn["entrance"]["x"], defn["entrance"]["y"]], "entrada")
        if defn.get("exit"):
            por([defn["exit"]["x"], defn["exit"]["y"]], "saída")
        check(f"{arquivo}: nenhuma casa com duas coisas {conflito}", not conflito)
        poder = defn["expected_party"]["heroes"] * defn["expected_party"]["level"]
        nd = G.nd_por_sala(defn)
        medido = {rid: (round(v, 2), G.faixa(v, poder)) for rid, v in nd.items()}
        check(f"{arquivo}: ND e faixa por sala batem com a spec {medido}", medido == ESPERADO[arquivo])
        todas = {r["id"] for r in defn["rooms"]}
        if arquivo == "sombras_3b_trono.json":
            check("trono: o esconderijo NÃO é alcançável com a passagem fechada",
                  G.salas_alcancaveis(defn) == todas - {2})
            check("trono: com a passagem aberta, todas as salas são alcançáveis",
                  G.salas_alcancaveis(defn, passagens_abertas=True) == todas)
        else:
            check(f"{arquivo}: todas as salas alcançáveis da entrada", G.salas_alcancaveis(defn) == todas)
    party = {a: d["expected_party"] for a, d in MM.items()}
    check("curva-alvo: Vau 1, Minas 2, Covil 3",
          [party[a]["level"] for a in G.ARQUIVOS] == [1, 2, 3, 3]
          and all(p["heroes"] == 4 for p in party.values()))


# ─── [2] Destinos e corrente de requisitos ───────────────────────────────────
async def secao_corrente():
    print("\n[2] Destinos ocultos e corrente de requisitos")
    dest = ART["destinos"]
    for did, d in dest.items():
        check(f"{did}: oculto até liberar, não revisitável", d["oculto_ate_liberar"] and not d["revisitavel"])
        check(f"{did}: história já no formato limpo do servidor",
              all(S._clean_story_field(e["intro"]) == e["intro"] and S._clean_story_field(e["outro"]) == e["outro"]
                  for e in d["dungeons"]) and S._clean_story_field(d["outro_rota"]) == d["outro_rota"])
    check("Covil: 2 etapas, a primeira emendada",
          [e["encadear"] for e in dest["sombras_covil"]["dungeons"]] == [True, False])
    with Ambiente():
        r = sala_na_cidade()
        check("sem o fato, o Vau não aparece no mapa", not r._aventura_visivel(S.WORLD_ADVENTURES["sombras_vau"]))
        await r.handle_world_adventure("h0", "sombras_vau")
        check("…e entrar nele é recusado como destino inválido", r.phase == "city")
        await r.handle_scene_npc("h0", "taverna", "barman", G.CONVERSA_ID)
        check("a conversa do Bartender grava o fato", G.FATO_GANCHO in r.fatos)
        check("com o fato, o Vau aparece", r._aventura_visivel(S.WORLD_ADVENTURES["sombras_vau"]))
        check("as Minas continuam ocultas antes do Vau", not r._aventura_visivel(S.WORLD_ADVENTURES["sombras_minas"]))
        r.world_adventure_progress["sombras_vau"] = 1
        check("Vau concluído libera as Minas", r._aventura_visivel(S.WORLD_ADVENTURES["sombras_minas"]))
        check("o Covil ainda não", not r._aventura_visivel(S.WORLD_ADVENTURES["sombras_covil"]))
        r.world_adventure_progress["sombras_minas"] = 1
        check("Minas concluídas liberam o Covil", r._aventura_visivel(S.WORLD_ADVENTURES["sombras_covil"]))


# ─── [3] Objetivos ───────────────────────────────────────────────────────────
async def secao_objetivos():
    print("\n[3] Objetivos de cada masmorra")
    with Ambiente():
        r = sala_na_cidade()
        r.fatos.add(G.FATO_GANCHO)
        await entrar(r, "sombras_vau")
        check("Vau carrega pelo mapa-múndi", r.phase == "playing" and r.selected_dungeon == "sombras_1_vau.json")
        check("Vau é ar livre", r.ambiente == "ar_livre")
        junto(r, "h0", r.prisoner["pos"])
        await r.handle_libertar_prisioneiro("h0")
        check("Tomé é solto", r.prisoner.get("freed") is True)
        await r._check_objectives()
        check("soltar não basta: é preciso escoltá-lo", not r.mission_complete_pending)
        r.prisoner["pos"] = [r.exit_pos[0] - 1, r.exit_pos[1]]
        await r._check_objectives()
        check("Tomé junto da saída cumpre o objetivo", r.mission_complete_pending)

    with Ambiente():
        r = sala_na_cidade()
        r.world_adventure_progress["sombras_vau"] = 1
        await entrar(r, "sombras_minas")
        cid, bau = next((cid, c) for cid, c in r.chests.items()
                        if any(it.get("id") == "frasco_acido" for it in c["items"]))
        ids = sorted(it["id"] for it in bau["items"])
        check(f"o cofre traz 2 ácidos, 1 óleo e o bilhete {ids}",
              ids == ["carta", "frasco_acido", "frasco_acido", "frasco_oleo"])
        junto(r, "h0", bau["pos"])
        await r.handle_take_from_chest("h0", cid, "gold", 0)
        await r._check_objectives()
        check("abrir o cofre cumpre o objetivo das Minas", r.mission_complete_pending)

    with Ambiente():
        r = sala_na_cidade()
        r.world_adventure_progress.update({"sombras_vau": 1, "sombras_minas": 1})
        await entrar(r, "sombras_covil")
        check("o Covil começa nos Salões", r.selected_dungeon == "sombras_3a_saloes.json")
        await r._check_objectives()
        check("com monstros vivos, as salas obrigatórias não estão cumpridas", not r.mission_complete_pending)
        for m in r.monsters.values():
            m["hp"] = 0
        await r._check_objectives()
        check("limpar as 3 salas obrigatórias cumpre", r.mission_complete_pending)
        r.players["h1"]["hp"] = 3
        await r.handle_encerrar_missao("h0")
        await r._liberar_intro_masmorra(True)
        check("encerrar emenda direto no Trono", r.phase == "playing" and r.selected_dungeon == "sombras_3b_trono.json")
        check("…sem recuperar HP (3 → 3)", r.players["h1"]["hp"] == 3)
        troll = next(m for m in r.monsters.values() if m["type"] == "troll")
        bug = next(m for m in r.monsters.values() if m["type"] == "bugbear_sombras")
        check("o troll é o alvo do objetivo", troll.get("authored_target"))
        troll["troll_regeneracao_bloqueada"] = True
        troll["hp"] = 0
        await r._monster_dies(troll, "h0")
        await r._check_objectives()
        check("matar o troll cumpre o Trono", r.mission_complete_pending)
        check("…com o Bugbear ainda vivo (ele é opcional)", bug["hp"] > 0)


# ─── [4] Troll × ácido ───────────────────────────────────────────────────────
async def secao_troll():
    print("\n[4] O ácido do cofre para a regeneração do troll")
    with Ambiente():
        r = sala_na_cidade()
        r.world_adventure_progress.update({"sombras_vau": 1, "sombras_minas": 1})
        await entrar(r, "sombras_covil")
        for m in r.monsters.values():
            m["hp"] = 0
        await r._check_objectives()
        await r.handle_encerrar_missao("h0")
        await r._liberar_intro_masmorra(True)
        troll = next(m for m in r.monsters.values() if m["type"] == "troll")
        p = r.players["h2"]
        acido = next(dict(i) for i in S.SHOP_MERCHANT if i["id"] == "frasco_acido")
        junto(r, "h2", troll["pos"])
        for _ in range(40):
            if troll.get("troll_regeneracao_bloqueada"):
                break
            p["bag"].append(dict(acido))
            p["action_done"] = False
            await r.handle_throw_item("h2", {"item_id": "frasco_acido", "target_id": troll["id"]})
        check("acertar o frasco de ácido bloqueia a regeneração", troll.get("troll_regeneracao_bloqueada"))
        troll["hp"] = 20
        await r._processar_regeneracao_troll_inicio(troll)
        check("com a regeneração bloqueada, o troll não recupera PV", troll["hp"] == 20)


# ─── [5] Segredo do Bugbear ──────────────────────────────────────────────────
async def secao_segredo():
    print("\n[5] Estante, esconderijo e o Anel da Garra Negra")
    check("o anel passa no validador do Editor de Itens", ART["anel"]["id"] == G.ANEL_ID)
    check("o anel só aparece em baús", ART["anel"]["disponibilidade"] == {"loja": False, "baus": True, "loot_monstro": False})
    with Ambiente():
        r = sala_na_cidade()
        r.world_adventure_progress.update({"sombras_vau": 1, "sombras_minas": 1})
        await entrar(r, "sombras_covil")
        for m in r.monsters.values():
            m["hp"] = 0
        await r._check_objectives()
        await r.handle_encerrar_missao("h0")
        await r._liberar_intro_masmorra(True)
        sp = r.secret_passages[0]
        x, y = sp["pos"]
        check("a passagem começa fechada (parede)", r.tiles[y][x] == S.WALL and not sp["opened"])
        estante = next(d for d in r.decorations if d["id"] == "trono_estante")
        check("a estante NÃO marca objetivo de baú-chave", not estante.get("key_objective"))
        junto(r, "h0", estante["pos"])
        await r.handle_activate_decor_mechanism("h0", "trono_estante")
        check("ativar a estante abre a passagem", sp["opened"] and r.tiles[y][x] != S.WALL)
        bau = next(c for c in r.chests.values() if any(it.get("id") == G.ANEL_ID for it in c["items"]))
        check("o baú do esconderijo guarda o anel", bau is not None)
        guerreiro = r.players["h0"]
        anel = next(dict(it) for it in bau["items"] if it.get("id") == G.ANEL_ID)
        guerreiro["bag"].append(anel)
        await r.handle_equip_from_bag("h0", len(guerreiro["bag"]) - 1)
        check("equipado num guerreiro, concede Esconder nas Sombras",
              "hero_rogue_esconder_sombras" in S._habilidades_concedidas(guerreiro))


# ─── [7] Régua da curva de XP (relatório) ────────────────────────────────────
def secao_curva():
    print("\n[7] Régua da curva de XP — RELATÓRIO, não cobrança (conserto é o próximo subprojeto)")
    defs = {m["type"]: m for m in S.MONSTER_DEFS}
    nivel, xp = 1, 0
    for arquivo in G.ARQUIVOS:
        ini = nivel
        for mo in MM[arquivo]["monsters"]:
            if mo["type"] == "bugbear_sombras" or mo["room_id"] == 2 and arquivo == "sombras_3b_trono.json":
                continue    # o esconderijo é opcional
            cr = S.monster_cr(defs[mo["type"]])
            xp += max(1, int(150 * nivel * (2 ** (cr - 1))) // 4)
            if xp >= nivel * 30:
                xp -= nivel * 30
                nivel += 1
        print(f"     {arquivo}: entra no nível {ini}, sai no {nivel} "
              f"(alvo: {MM[arquivo]['expected_party']['level']})")
    check("relatório da curva produzido", True)


async def main():
    secao_mapas()
    await secao_corrente()
    await secao_objetivos()
    await secao_troll()
    await secao_segredo()
    secao_curva()
    print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
    sys.exit(1 if FAIL else 0)


asyncio.run(main())
