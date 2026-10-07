"""Escolha de magia ao subir de nível com vários heróis na mesma conexão.

Roda da raiz:  python tools/test_escolha_magia_grupo.py

Bug (2026-10-06): no Solo com grupo, mago e clérigo sobem de nível juntos (o XP
é dividido num laço só) e os dois avisos chegavam em sequência; o cliente tem
UM painel de escolha, então o 2º apagava o 1º e o herói do aviso perdido ficava
preso: "escolha sua nova magia antes de encerrar o turno", sem painel nenhum.

  [1] Um aviso por vez, na ordem do grupo; escolher o do 1º manda o do 2º.
  [2] O aviso nomeia o herói (o painel diz de quem é a escolha).
  [3] Encerrar o turno com escolha pendente reenvia o aviso e não cobra nada.
  [4] O início do turno de quem tem escolha pendente reenvia o aviso.
  [5] Multiplayer (conexões diferentes): cada um recebe o seu, ao mesmo tempo.
"""
import asyncio, json, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


class FakeWS:
    def __init__(self): self.sent = []
    async def send(self, data): self.sent.append(json.loads(data))
    def prompts(self): return [m for m in self.sent if m.get("type") == "spell_pick_prompt"]
    def erros(self): return [m for m in self.sent if m.get("type") == "error"]


def sala_grupo():
    """Conexão "c1" = clérigo (principal) + mago extra, os dois no nível 1."""
    r = S.GameRoom("ESCMAG")
    ws = FakeWS()
    r.connections["c1"] = ws
    cle = S.make_player("c1", "Lewis", "cleric", 0)
    mag = S.make_player("m1", "Pedro", "mage", 1)
    mag["controlador"] = "c1"
    r.players = {"c1": cle, "m1": mag}
    r.player_order = ["c1", "m1"]
    r.host_pid = "c1"
    r.phase = "playing"
    async def nada(*a, **k): pass
    r.push_state = nada
    r.gm_say = nada
    return r, ws, cle, mag


async def subir_todos(r):
    """Igual à morte de um monstro: XP para todos num laço só."""
    for p in r.players.values():
        p["xp"] = p["level"] * S.XP_POR_NIVEL
        await r._check_level_up(p)


def magia_de(p, circ):
    return next(mid for mid, m in S.GRIMORIO.items()
                if p["class_id"] in m.get("classe", []) and m.get("circulo") == circ
                and mid not in p.get("magias_conhecidas", []))


async def secao_ordem():
    print("\n[1]/[2] Um aviso por vez, na ordem do grupo")
    r, ws, cle, mag = sala_grupo()
    await subir_todos(r)
    check("os dois ficaram com escolha pendente",
          cle.get("pending_spell_pick") and mag.get("pending_spell_pick"))
    pr = ws.prompts()
    check("só UM aviso chegou (o 2º não apaga o 1º)", len(pr) == 1, [p.get("heroi") for p in pr])
    check("é o do 1º herói do grupo (clérigo)", pr and pr[0].get("heroi") == "c1", pr)
    check("[2] o aviso nomeia o herói", pr and pr[0].get("heroi_nome") == "Lewis", pr)
    ws.sent.clear()
    await r.handle_escolher_magia_nivel("c1", magia_de(cle, cle["pending_spell_pick"][0]))
    pr = ws.prompts()
    check("escolhida a do clérigo, chega a do mago", len(pr) == 1 and pr[0].get("heroi") == "m1", pr)
    check("[2] com o nome do mago", pr and pr[0].get("heroi_nome") == "Pedro", pr)
    ws.sent.clear()
    await r.handle_escolher_magia_nivel("m1", magia_de(mag, mag["pending_spell_pick"][0]))
    check("escolhida a do mago, não sobra aviso nem pendência",
          not ws.prompts() and not cle.get("pending_spell_pick") and not mag.get("pending_spell_pick"))


async def secao_encerrar():
    print("\n[3] Encerrar o turno com escolha pendente")
    r, ws, cle, mag = sala_grupo()
    await subir_todos(r)
    await r.handle_escolher_magia_nivel("c1", magia_de(cle, cle["pending_spell_pick"][0]))
    ws.sent.clear()
    # Painel perdido (recarregou a página, por exemplo): é a vez do mago.
    r.initiative_active = True
    r.initiative_order = [{"kind": "player", "id": "m1"}]
    r.initiative_index = 0
    r._is_turn = lambda pid: pid == "m1"
    cobrado = []
    async def dor(p): cobrado.append(p["id"])
    r._cobrar_dor_constante = dor
    await r.handle_end_turn("m1")
    pr = ws.prompts()
    check("recusa o encerramento",
          any(getattr(e.get("msg"), "key", e.get("msg")) for e in ws.erros()), ws.sent)
    check("e reenvia o aviso do mago", len(pr) == 1 and pr[0].get("heroi") == "m1", pr)
    check("sem cobrar efeitos de fim de turno (Dor Constante)", cobrado == [], cobrado)


async def secao_inicio_turno():
    print("\n[4] O início do turno reenvia o aviso pendente")
    r, ws, cle, mag = sala_grupo()
    await subir_todos(r)
    ws.sent.clear()
    await r._start_initiative_player_turn(cle)
    pr = ws.prompts()
    check("turno do clérigo com escolha pendente: aviso reenviado",
          len(pr) == 1 and pr[0].get("heroi") == "c1", pr)


async def secao_multiplayer():
    print("\n[5] Multiplayer: cada conexão recebe o seu")
    r = S.GameRoom("ESCMP")
    wa, wb = FakeWS(), FakeWS()
    r.connections = {"a": wa, "b": wb}
    r.players = {"a": S.make_player("a", "Ana", "cleric", 0),
                 "b": S.make_player("b", "Bia", "mage", 1)}
    r.phase = "playing"
    async def nada(*a, **k): pass
    r.push_state = nada; r.gm_say = nada
    await subir_todos(r)
    check("Ana recebe o dela", len(wa.prompts()) == 1)
    check("Bia recebe o dela ao mesmo tempo", len(wb.prompts()) == 1)


async def main():
    await secao_ordem()
    await secao_encerrar()
    await secao_inicio_turno()
    await secao_multiplayer()


if __name__ == "__main__":
    print("=" * 62); print("  ESCOLHA DE MAGIA NA SUBIDA DE NÍVEL (grupo)"); print("=" * 62)
    asyncio.run(main())
    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    sys.exit(1 if FAIL else 0)
