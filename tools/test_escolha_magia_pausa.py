"""Escolha de magia ao subir de nível: abre na vez do herói e pausa o jogo.

Roda da raiz:  python -X utf8 tools/test_escolha_magia_pausa.py

Regra (2026-11-01):
  - Na masmorra o painel abre na VEZ do mago/clérigo que subiu. Se ele subiu na vez
    de outro herói, a escolha espera.
  - Enquanto a escolha está pendente na vez dele, ele não age e o relógio da vez
    fica parado; escolhida a magia, a vez continua e o relógio volta.
  - Na cidade o painel abre na hora (lá não há turno).
  - Mesa de teste do editor fica como estava.
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


def sala():
    """Multiplayer: guerreiro "w" e maga "m", cada um na sua conexão."""
    r = S.GameRoom("PAUSA")
    ww, wm = FakeWS(), FakeWS()
    r.connections = {"w": ww, "m": wm}
    r.players = {"w": S.make_player("w", "Ana", "warrior", 0),
                 "m": S.make_player("m", "Bia", "mage", 1)}
    r.player_order = ["w", "m"]
    r.phase = "playing"
    r.turn_timer_enabled = True
    r.initiative_active = True
    r.initiative_order = [{"kind": "player", "id": "w", "seq": 0, "initiative": 20, "dex": 0, "int": 0},
                          {"kind": "player", "id": "m", "seq": 1, "initiative": 10, "dex": 0, "int": 0}]
    r.initiative_index = 0
    async def nada(*a, **k): pass
    r.push_state = nada; r.gm_say = nada
    return r, ww, wm


async def subir(r, pid):
    p = r.players[pid]
    p["xp"] = p["level"] * S.XP_POR_NIVEL
    await r._check_level_up(p)


def magia_de(p):
    circ = p["pending_spell_pick"][0]
    return next(mid for mid, m in S.GRIMORIO.items()
                if p["class_id"] in m.get("classe", []) and m.get("circulo") == circ
                and mid not in p.get("magias_conhecidas", []))


def timer_ligado(r):
    return r.turn_timer_task is not None


async def secao_vez_de_outro():
    print("\n[1] Subiu na vez de outro herói: a escolha espera a vez dele")
    r, ww, wm = sala()
    await subir(r, "m")
    m = r.players["m"]
    check("ficou com escolha pendente", bool(m.get("pending_spell_pick")))
    check("nenhum painel agora (é a vez da Ana)", not wm.prompts(), wm.prompts())
    check("a Ana continua podendo agir", r._is_turn("w"))
    r.initiative_index = 1
    await r._start_initiative_player_turn(m)
    check("na vez da Bia o painel abre", len(wm.prompts()) == 1)
    check("…e ela não age enquanto não escolhe", not r._is_turn("m"))
    r._iniciar_timer_turno()
    check("…e o relógio da vez fica parado", not timer_ligado(r))
    await r.handle_escolher_magia_nivel("m", magia_de(m))
    check("escolheu: volta a agir", r._is_turn("m"))
    check("…e o relógio volta", timer_ligado(r))
    r._cancelar_timer_turno()


async def secao_vez_dele():
    print("\n[2] Subiu na própria vez: o painel abre na hora e pausa")
    r, ww, wm = sala()
    r.initiative_index = 1
    r._iniciar_timer_turno()
    check("(relógio corria antes)", timer_ligado(r))
    await subir(r, "m")
    check("painel na hora", len(wm.prompts()) == 1)
    check("relógio parado", not timer_ligado(r))
    check("não age até escolher", not r._is_turn("m"))
    await r.handle_escolher_magia_nivel("m", magia_de(r.players["m"]))
    check("escolheu: age de novo", r._is_turn("m"))
    r._cancelar_timer_turno()


async def secao_cidade():
    print("\n[3] Na cidade o painel abre na hora")
    r, ww, wm = sala()
    r.phase = "city"
    await subir(r, "m")
    check("painel na cidade, sem esperar turno", len(wm.prompts()) == 1)


async def main():
    await secao_vez_de_outro()
    await secao_vez_dele()
    await secao_cidade()
    print(f"\n=== {PASS} passou, {FAIL} falhou ===")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
