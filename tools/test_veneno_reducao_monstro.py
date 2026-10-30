"""Veneno de redução de atributo: o monstro sofre a MESMA regra do herói.

Antes, o monstro perdia FOR como -1 de dano fixo e CON como PV direto (1-4),
e DES/INT viravam -1 de dano por engano. Agora o efeito deriva do modificador
real (FOR->dano, CON->PV máximo por ND e Fortitude, DES->CA/Reflexos/visão,
INT->Vontade/visão), é recalculado a partir dos efeitos ativos (sem deriva
quando expiram fora de ordem) e nunca deixa o PV máximo abaixo de 1.

Roda da raiz:
    python -X utf8 tools/test_veneno_reducao_monstro.py
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


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} {extra}")


def sala():
    r = S.GameRoom("TEST")

    async def noop(*a, **k):
        return None
    r.gm_say = noop
    r.broadcast = noop
    r.push_state = noop
    r.send_to = noop
    r.phase = "playing"
    # save sempre falha; dados determinísticos (dígito = valor fixo, NdX = 3)
    r._testar_save = lambda *a, **k: (False, 5, 0, 5)
    r._rolar_dado = lambda d: int(d) if str(d).isdigit() else 3
    return r


def monstro(r, mid="m1", **kw):
    m = {"id": mid, "name": "Orc", "pos": [4, 4], "hp": 40, "max_hp": 40, "ac": 12,
         "alive": True, "tier": 1, "cr": 2, "str_": 16, "dex": 14, "int_": 12,
         "con_": 14, "fort": 2, "ref_": 1, "will": 0, "base_movement": 6}
    m.update(kw)
    r.monsters[mid] = m
    return m


def veneno(vid, atributo, valor, duracao):
    S.VENENOS[vid] = {"nome": vid, "icone": "x", "operacao": "reduzir", "atributo": atributo,
                      "valor": str(valor), "duracao": str(duracao), "save": "fortitude",
                      "dificuldade": 10, "anula": True}
    return vid


async def main():
    veneno("t_for4", "forca", 4, 5)
    veneno("t_for2", "forca", 2, 1)
    veneno("t_con4", "constituicao", 4, 5)
    veneno("t_dex4", "destreza", 4, 5)
    veneno("t_int4", "inteligencia", 4, 5)

    print("\n[1] FOR: o dano cai pela queda real do modificador")
    r = sala()
    m = monstro(r)
    await r._aplicar_veneno(m, "t_for4")        # 16 (+3) -> 12 (+1)
    check("dano -2 (não o -1 fixo de antes)", r._pen(m, "dano") == -2, r._pen(m, "dano"))
    check("score bruto do monstro intacto", m["str_"] == 16)
    r2 = sala()
    m2 = monstro(r2, str_=10)
    await r2._aplicar_veneno(m2, "t_for4")      # 10 (0) -> 6 (-2)
    check("FOR 10 -> 6: dano -2", r2._pen(m2, "dano") == -2)

    print("\n[2] CON: PV máximo por ND + Fortitude, PV atual limitado")
    r = sala()
    m = monstro(r)                               # CON 14 (+2) -> 10 (0); ND 2
    await r._aplicar_veneno(m, "t_con4")
    check("PV máximo 40 -> 36 (2 x ND 2)", m["max_hp"] == 36, m["max_hp"])
    check("PV atual limitado ao novo máximo", m["hp"] == 36, m["hp"])
    check("Fortitude -2", r._veneno_save_bonus(m, "fortitude") == 0, r._veneno_save_bonus(m, "fortitude"))
    r._curar_veneno_status(m)
    check("cura devolve o PV máximo", m["max_hp"] == 40, m["max_hp"])
    check("cura devolve a Fortitude", r._veneno_save_bonus(m, "fortitude") == 2)
    check("sem efeito de veneno depois da cura", not m.get("efeitos_veneno"))

    r = sala()
    m = monstro(r, max_hp=3, hp=3, cr=5)         # nunca abaixo de 1
    await r._aplicar_veneno(m, "t_con4")
    check("PV máximo nunca abaixo de 1", m["max_hp"] >= 1 and m["hp"] >= 1, (m["max_hp"], m["hp"]))
    r._curar_veneno_status(m)
    check("e volta ao valor original", m["max_hp"] == 3, m["max_hp"])

    print("\n[3] DES: CA, Reflexos e visão; nunca o dano")
    r = sala()
    m = monstro(r)                               # DES 14 (+2) -> 10 (0)
    ref0 = r._veneno_save_bonus(m, "reflexos")
    await r._aplicar_veneno(m, "t_dex4")
    check("Reflexos -2", r._veneno_save_bonus(m, "reflexos") == ref0 - 2)
    check("CA efetiva -2", r._ca_veneno_atributo(m) == -2, r._ca_veneno_atributo(m))
    check("DES não reduz o dano (bug antigo)", r._pen(m, "dano") == 0)
    check("visão = fórmula com DES efetivo",
          r._get_raio_visao_monstro(m) == max(1, 6 + (S.mod(12) + S.mod(10)) // 2))

    print("\n[4] INT: Vontade e visão")
    r = sala()
    m = monstro(r)                               # INT 12 (+1) -> 8 (-1)
    will0 = r._veneno_save_bonus(m, "vontade")
    await r._aplicar_veneno(m, "t_int4")
    check("Vontade -2", r._veneno_save_bonus(m, "vontade") == will0 - 2)
    check("visão = fórmula com INT efetivo",
          r._get_raio_visao_monstro(m) == max(1, 6 + (S.mod(8) + S.mod(14)) // 2))
    check("INT não reduz o dano", r._pen(m, "dano") == 0)

    print("\n[5] Dois venenos expirando fora de ordem não deixam resíduo")
    r = sala()
    m = monstro(r)
    await r._aplicar_veneno(m, "t_for4")         # dura 5
    await r._aplicar_veneno(m, "t_for2")         # dura 1; acumulado 6: 16 -> 10 (-3)
    check("acumulado: dano -3", r._pen(m, "dano") == -3, r._pen(m, "dano"))
    await r._processar_venenos_turno(m)          # o de 1 rodada expira
    check("sobra só o de FOR 4: dano -2 exato", r._pen(m, "dano") == -2, r._pen(m, "dano"))
    for _ in range(5):
        await r._processar_venenos_turno(m)
    check("tudo expirado: dano 0", r._pen(m, "dano") == 0, r._pen(m, "dano"))
    check("sem efeitos restantes", not m.get("efeitos_veneno"))

    print("\n[6] CON expirando também devolve o PV máximo")
    r = sala()
    m = monstro(r)
    await r._aplicar_veneno(m, "t_con4")
    for _ in range(6):
        await r._processar_venenos_turno(m)
    check("PV máximo restaurado", m["max_hp"] == 40, m["max_hp"])
    check("sem resto de bookkeeping", not m.get("_veneno_hp_perdido"))

    print("\n[7] Efeito no formato antigo (save/foto anterior) ainda reverte")
    r = sala()
    m = monstro(r, max_hp=36, hp=36)
    m["penalidades"] = {"dano": -1}
    m["efeitos_veneno"] = [{"operacao": "reduzir", "atributo": "constituicao", "valor": 4,
                            "duracao": 1, "hp_perdido": 4},
                           {"operacao": "reduzir", "atributo": "forca", "valor": 3,
                            "duracao": 1, "pen_dano": 1}]
    await r._processar_venenos_turno(m)
    check("PV devolvido pelo formato antigo", m["max_hp"] == 40, m["max_hp"])
    check("penalidade de dano antiga devolvida", m["penalidades"]["dano"] == 0)

    print("\n[8] Herói continua igual (score bruto reduzido e restaurado)")
    r = sala()
    h = S.make_player("h1", "Heroi", "warrior", 0)
    h.update(alive=True, pos=[1, 1], connected=True)
    r.players["h1"] = h
    antes = h["str_"]
    await r._aplicar_veneno(h, "t_for4")
    check("FOR do herói cai 4", h["str_"] == antes - 4, (antes, h["str_"]))
    check("herói não recebe a penalidade derivada do monstro", r._pen(h, "dano") == 0)
    for _ in range(6):
        await r._processar_venenos_turno(h)
    check("FOR do herói volta", h["str_"] == antes, h["str_"])

    print("\n[9] Medusa usa a mesma regra no monstro")
    r = sala()
    S.VENENOS.setdefault("veneno_medusa", S.VENENOS.get("veneno_medusa"))
    if S.VENENOS.get("veneno_medusa"):
        m = monstro(r, hp=60, max_hp=60)
        await r._aplicar_veneno(m, "veneno_medusa")
        # FOR 16 -2 -> 14 (+2): -1 ; CON 14 -2 -> 12 (+1): -1 x ND 2
        check("Medusa: FOR deriva do modificador", r._pen(m, "dano") == -1, r._pen(m, "dano"))
        check("Medusa: CON deriva do ND", m["max_hp"] <= 58, m["max_hp"])


asyncio.run(main())
print(f"\n{'=' * 50}\n  {PASS} passaram, {FAIL} falharam\n{'=' * 50}")
sys.exit(1 if FAIL else 0)
