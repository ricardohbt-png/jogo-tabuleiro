"""Perseguição dos monstros: todo dano alerta e rastro por Percepção.
Roda da raiz: python tools/test_perseguicao.py
Spec: docs/superpowers/specs/2026-09-26-perseguicao-monstros-design.md
"""
import asyncio
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S  # noqa: E402

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


HEROI_LONGE = [15, 3]      # do outro lado da parede em x=10
ORC_POS = [7, 5]


def cena(fechada=False):
    """Sala 18×10 cortada por uma parede em x=10; passagem em y=10 (sem ela se
    `fechada`). Um orc no lado esquerdo e o Luccas escondido no direito."""
    r = S.GameRoom("PERSEG")
    narr = []
    async def noop(*a, **k):
        pass
    async def say(txt, *a, **k):
        narr.append(str(txt))
    r.gm_say = say; r.broadcast = noop; r.push_state = noop; r.send_to = noop
    r._broadcast_dado = noop
    r.tiles = [[S.WALL] * S.MAP_W for _ in range(S.MAP_H)]
    for y in range(1, 11):
        for x in range(1, 19):
            r.tiles[y][x] = S.FLOOR
    for y in range(1, 11):
        if fechada or y != 10:
            r.tiles[y][10] = S.WALL
    r.rooms = [{"id": 0, "x": 1, "y": 1, "w": 18, "h": 10, "locked": False}]
    r.phase = "playing"
    r.round_num = 1
    h = S.make_player("h", "Luccas", "rogue", 0)
    h["pos"] = list(HEROI_LONGE)
    r.players = {"h": h}
    orc = next(d for d in S.MONSTER_DEFS if d["type"] == "orc")
    m = S.make_monster(orc, {"id": 0, "cx": ORC_POS[0], "cy": ORC_POS[1]})
    m["pos"] = list(ORC_POS)
    r.monsters = {m["id"]: m}
    return r, h, m, narr


def lembrar(r, m, pos=None):
    """O orc 'viu' o Luccas pela última vez em `pos` (padrão: onde o orc está)."""
    m["ai_last_seen"] = {"target_id": "h", "pos": list(pos or m["pos"]),
                         "round": r.round_num, "room_id": m.get("room_id")}


class Dado:
    """Fixa o d20 (random.randint(1, 20)) durante o bloco."""
    def __init__(self, valor):
        self.valor = valor
    def __enter__(self):
        self.orig = S.random.randint
        S.random.randint = lambda a, b: self.valor if (a, b) == (1, 20) else self.orig(a, b)
    def __exit__(self, *exc):
        S.random.randint = self.orig


def espiar_percepcao(r):
    """Conta os testes de rastro (cada teste lê a Percepção uma vez)."""
    chamadas = []
    orig = r._get_percepcao_monstro
    def spy(mm):
        chamadas.append(1)
        return orig(mm)
    r._get_percepcao_monstro = spy
    return chamadas


async def turno(r, m):
    await r.gm_phase(only_monster=m)
    r.round_num += 1


# ─── [1] rastro com sucesso ──────────────────────────────────────────────────
async def secao_sucesso():
    print("\n[1] Chegou à última posição sem ver o herói e passou no teste")
    r, h, m, narr = cena()
    lembrar(r, m)
    rodada = r.round_num
    check("orc não enxerga o Luccas", not r._monstro_enxerga_alvo(m, {"obj": h}))
    with Dado(1):
        await turno(r, m)
    mem = m.get("ai_last_seen") or {}
    check("a pista passou à posição atual do herói", mem.get("pos") == HEROI_LONGE)
    check("o prazo não foi renovado (round igual)", mem.get("round") == rodada)
    check("conta como a 1ª busca", mem.get("searches") == 1)
    check("o orc saiu do lugar atrás da pista", m["pos"] != ORC_POS)
    check("narrou o rastro", any("rastro" in t for t in narr))


# ─── [2] rastro com falha e um teste por chegada ─────────────────────────────
async def secao_falha():
    print("\n[2] Falhou no teste: fica procurando e não testa de novo no mesmo ponto")
    r, h, m, narr = cena()
    lembrar(r, m)
    testes = espiar_percepcao(r)
    with Dado(20):
        await turno(r, m)
    mem = m.get("ai_last_seen") or {}
    check("memória continua no ponto antigo", mem.get("pos") == ORC_POS)
    check("o orc ficou parado", m["pos"] == ORC_POS)
    check("marcou onde testou", mem.get("rastro_testado_em") == ORC_POS)
    check("sem narração na falha", not any("rastro" in t for t in narr))
    with Dado(1):
        await turno(r, m)
    check("parado no mesmo ponto: só 1 teste em 2 turnos", len(testes) == 1)
    check("e a pista não mudou", (m.get("ai_last_seen") or {}).get("pos") == ORC_POS)


# ─── [3] quem não deixa rastro ───────────────────────────────────────────────
async def secao_invisivel():
    print("\n[3] Herói invisível não deixa rastro, exceto para quem tem Faro Implacável")
    r, h, m, narr = cena()
    h["invisivel_sombras"] = True
    lembrar(r, m)
    testes = espiar_percepcao(r)
    with Dado(1):
        await turno(r, m)
    check("invisível: nenhum teste", len(testes) == 0)
    check("invisível: pista intacta", (m.get("ai_last_seen") or {}).get("pos") == ORC_POS)

    r, h, m, narr = cena()
    h["invisivel_sombras"] = True
    m["special_abilities"] = [{"id": "faro_implacavel_minotauro"}]
    lembrar(r, m)
    with Dado(1):
        await turno(r, m)
    check("com Faro Implacável o rastro existe",
          (m.get("ai_last_seen") or {}).get("pos") == HEROI_LONGE)

    r, h, m, narr = cena()
    h["fora_masmorra"] = {"rodadas_restantes": 2}
    lembrar(r, m)
    testes = espiar_percepcao(r)
    with Dado(1):
        await turno(r, m)
    check("herói na cidade não deixa rastro", len(testes) == 0)


# ─── [4] prazo de 3 rodadas e reencontro ─────────────────────────────────────
async def secao_prazo():
    print("\n[4] Prazo de 3 rodadas sem ver o herói, mesmo rastreando; ver de novo zera")
    r, h, m, narr = cena(fechada=True)
    lembrar(r, m)
    with Dado(1):
        await turno(r, m)
        check("rodada 1: achou o rastro", (m.get("ai_last_seen") or {}).get("pos") == HEROI_LONGE)
        await turno(r, m)
        check("rodada 2: ainda procurando", m.get("ai_last_seen") is not None)
        await turno(r, m)
    check("rodada 3 sem ver o herói: desistiu", m.get("ai_last_seen") is None)

    r, h, m, narr = cena()
    lembrar(r, m)
    m["ai_last_seen"]["searches"] = 2
    h["pos"] = [8, 5]                     # colado no orc: ele vê
    await turno(r, m)
    mem = m.get("ai_last_seen") or {}
    check("viu de novo: memória nova, busca zerada",
          mem.get("pos") == [8, 5] and not mem.get("searches"))


# ─── [5] todo dano alerta ────────────────────────────────────────────────────
async def secao_alerta():
    print("\n[5] Dano de qualquer ação do herói dá ao monstro a origem do ataque")
    r, h, m, narr = cena()
    h["pos"] = [15, 9]
    antes = r._hp_monstros()
    await r._dano_em_alvo(m, 3, "fogo", "h")          # ex.: uma magia
    await r._alertar_monstros_feridos("h", antes)
    mem = m.get("ai_last_seen") or {}
    check("magia: grava a posição do herói", mem.get("pos") == [15, 9])
    check("magia: marcada como ataque", mem.get("reason") == "attack")

    r, h, m, narr = cena()
    antes = r._hp_monstros()
    await r._alertar_monstros_feridos("h", antes)
    check("sem dano: nada gravado", "ai_last_seen" not in m)

    r, h, m, narr = cena()
    antes = r._hp_monstros()
    m["hp"] = 0
    await r._alertar_monstros_feridos("h", antes)
    check("monstro morto na ação: nada gravado", "ai_last_seen" not in m)

    r, h, m, narr = cena()
    h["fora_masmorra"] = {"rodadas_restantes": 2}
    antes = r._hp_monstros()
    m["hp"] -= 2
    await r._alertar_monstros_feridos("h", antes)
    check("herói fora do tabuleiro: nada gravado", "ai_last_seen" not in m)

    r, h, m, narr = cena()
    antes = r._hp_monstros()
    m["hp"] -= 2
    await r._alertar_monstros_feridos("mestre", antes)
    check("pid que não é herói: nada gravado", "ai_last_seen" not in m)

# ─── [6] gancho no laço de mensagens ─────────────────────────────────────────
def secao_gancho():
    print("\n[6] O laço de mensagens chama o alerta, exceto no fim de turno e no controle de servos")
    src = open(S.__file__, encoding="utf-8").read()
    check("exclusões declaradas",
          S._MENSAGENS_SEM_ALERTA_DE_DANO == frozenset(
              {"end_turn", "comandar_animados", "mover_animado", "atacar_animado"}))
    check("foto do HP antes do despacho", "_hp_watch = room._hp_monstros()" in src)
    check("alerta depois do despacho", "await room._alertar_monstros_feridos(pid, _hp_watch)" in src)


# ─── [7] indicador "!" de monstro procurando ─────────────────────────────────
def _procurando_no_payload(r, m):
    snap = next(x for x in r._game_state_payload()["monsters"] if x["id"] == m["id"])
    return snap.get("procurando")


async def secao_indicador():
    print("\n[7] Campo `procurando` do game_state (o \"!\" vermelho sobre o monstro)")
    r, h, m, narr = cena()
    check("sem pista: não está procurando", _procurando_no_payload(r, m) is False)
    lembrar(r, m)
    check("com pista e sem ver o herói: procurando", _procurando_no_payload(r, m) is True)
    h["pos"] = [8, 5]
    check("vendo o herói: não está procurando (está lutando)", _procurando_no_payload(r, m) is False)
    h["pos"] = list(HEROI_LONGE)
    r.round_num += 4
    check("pista vencida (mais de 3 rodadas): não está procurando",
          _procurando_no_payload(r, m) is False)
    check("a checagem não apaga a memória (só lê)", m.get("ai_last_seen") is not None)

    r, h, m, narr = cena()
    antes = r._hp_monstros()
    m["hp"] -= 2
    await r._alertar_monstros_feridos("h", antes)
    check("atingido de longe: procurando já antes do turno dele", _procurando_no_payload(r, m) is True)


def secao_cliente():
    print("\n[8] O cliente desenha o \"!\" no 2D e no 3D a partir do campo")
    js = open(os.path.join(os.path.dirname(S.__file__), "game.js"), encoding="utf-8").read()
    check("2D desenha o badge quando m.procurando", "if(m.procurando)" in js and "_drawProcurandoBadge2D(" in js)
    check("3D sincroniza o sprite pelo campo", "_syncProcurandoMark3D(_monFig3D, m)" in js)
    check("3D anima o sprite no laço", "_atualizarProcurandoMarks3D(now)" in js)
    check("assinatura 3D inclui o campo (senão o sprite não troca)", "!!m.procurando]" in js)


async def main():
    await secao_sucesso()
    await secao_falha()
    await secao_invisivel()
    await secao_prazo()
    await secao_alerta()
    secao_gancho()
    await secao_indicador()
    secao_cliente()
    print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
    sys.exit(1 if FAIL else 0)


asyncio.run(main())
