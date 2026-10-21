"""Marcador de entrada da masmorra: escada (padrão) ou poste.

Roda da raiz:  python -X utf8 tools/test_marcador_entrada.py

REGRA
  • `marcador_entrada` ∈ {"escada", "poste"}; ausente = "escada" (comportamento de sempre).
  • É só APRESENTAÇÃO: a casa de entrada, a saída pela escada e `saida_permitida` não mudam.
  • Vai no `game_state` e na foto da masmorra.
"""
import copy, json, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


def defn_base(**extra):
    d = S.carregar_dungeon("amostra.json")
    d = copy.deepcopy(d)
    d.update(extra)
    return d


print("\n[1] Validação")
ok, _ = S.validar_dungeon(defn_base())
check("masmorra sem o campo continua válida", ok)
for v in ("escada", "poste"):
    ok, msg = S.validar_dungeon(defn_base(marcador_entrada=v))
    check(f"'{v}' é válido", ok, msg)
for v in ("farol", "", 3, True, ["poste"]):
    ok, msg = S.validar_dungeon(defn_base(marcador_entrada=v))
    check(f"{v!r} é recusado", not ok)
ok, _ = S.validar_dungeon(defn_base(marcador_entrada=None))
check("null equivale a ausente", ok)

print("\n[2] Carga na sala")
def sala(**extra):
    r = S.GameRoom("MARC")
    r.load_authored_dungeon(defn_base(**extra))
    return r
check("sem o campo: escada", sala().marcador_entrada == "escada")
check("poste fica na sala", sala(marcador_entrada="poste").marcador_entrada == "poste")
check("valor desconhecido (arquivo antigo/corrompido) cai em escada", sala(marcador_entrada="x").marcador_entrada == "escada")
r1, r2 = sala(), sala(marcador_entrada="poste")
check("a casa de entrada é a mesma nos dois (só a apresentação muda)", r1.stairs_pos == r2.stairs_pos and r2.stairs_pos is not None)

print("\n[3] game_state e foto")
r = sala(marcador_entrada="poste")
check("o game_state leva o marcador", r._game_state_payload().get("marcador_entrada") == "poste")
check("sala nova (sem masmorra carregada) manda escada", S.GameRoom("X")._game_state_payload().get("marcador_entrada") == "escada")
check("o campo é da foto da masmorra", S.FOTO_SALA_CATEGORIAS.get("marcador_entrada") == "foto")

print("\n[4] Prévia do editor usa o mesmo carregador")
ok, payload, avisos = S._preview_dungeon_state(defn_base(marcador_entrada="poste"))
check("a prévia manda o marcador", ok and payload.get("marcador_entrada") == "poste", (ok, avisos))

print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
sys.exit(1 if FAIL else 0)
