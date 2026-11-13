"""Servos do mago/clérigo continuam ao sair e voltar à partida; morrem com o dono.

Roda da raiz:  python -X utf8 tools/test_servo_persistencia.py

- A ficha salva (snapshot_character) leva os servos vivos; restore_character os
  devolve com id novo (new_id recomeça a cada boot e colidiria com monstros da
  sessão nova) e com o dono apontando para o pid da conexão nova.
- Servo destruído ou roubado por um necromante não volta.
- O mago que morre leva os servos junto, na hora, e o cliente recebe as casas
  onde eles viraram pó. Ressuscitar o mago não os traz de volta.
"""
import asyncio, os, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
from test_atravessar_aliados import montar, servo

PASS = FAIL = 0
def check(label, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {label}")
    else:    FAIL += 1; print(f"  ❌ {label}" + (f"\n     {extra}" if extra else ""))


def secao_salvar_e_voltar():
    print("\n[1] Servos vão na ficha salva e voltam com id e dono novos")
    mago = S.make_player("velho", "Pedro", "mage", 0)
    mago["animados"] = [
        {"id": "id_7", "owner": "velho", "nome": "Esqueleto Animado", "vida_atual": 5, "vida_max": 8, "pos": [3, 3]},
        {"id": "elemental_fogo_1", "owner": "velho", "summoned_by": "velho", "tipo": "elemental",
         "vida_atual": 12, "vida_max": 12, "pos": [4, 3]},
        {"id": "id_9", "owner": "velho", "vida_atual": 0, "vida_max": 8, "pos": [5, 3]},
        {"id": "id_10", "owner": "velho", "vida_atual": 6, "vida_max": 8, "pos": [6, 3],
         "dominado_por_monstro": "id_3"},
    ]
    snap = S.snapshot_character(mago)
    check("a ficha salva leva os servos", "animados" in snap, list(snap))
    novo = S.make_player("novo", "Pedro", "mage", 0)
    S.restore_character(novo, snap)
    vivos = novo.get("animados") or []
    check("voltam só os 2 servos vivos e leais", len(vivos) == 2, vivos)
    ids = [a["id"] for a in vivos]
    check("ids renovados", not ({"id_7", "elemental_fogo_1"} & set(ids)), ids)
    check("ids distintos", len(set(ids)) == len(ids), ids)
    check("dono é o pid novo", all(a["owner"] == "novo" for a in vivos), vivos)
    elem = next((a for a in vivos if a.get("tipo") == "elemental"), {})
    check("elemental aponta o invocador novo", elem.get("summoned_by") == "novo", elem)
    check("vida preservada", sorted(a["vida_atual"] for a in vivos) == [5, 12], vivos)
    check("a ficha original não foi alterada", mago["animados"][0]["id"] == "id_7")


async def secao_morte_do_mago():
    print("\n[2] O mago morre e os servos viram pó na hora")
    r = await montar(classe="mage")
    eventos = []
    async def broadcast(msg, **kw): eventos.append(msg)
    r.broadcast = broadcast
    servo(r, "p1", [2, 1])
    servo(r, "p1", [3, 1], id="a2")
    await r._player_dies("p1")
    p = r.players["p1"]
    check("servos destruídos", p.get("animados") == [], p.get("animados"))
    po = [e for e in eventos if e.get("type") == "servos_viram_po"]
    check("cliente recebe o aviso do pó", len(po) == 1, [e.get("type") for e in eventos])
    if po:
        check("com as casas de cada servo", sorted(map(tuple, po[0]["posicoes"])) == [(2, 1), (3, 1)], po[0])
    p["alive"] = True; p["hp"] = 1      # ressuscitado
    check("ressuscitar não traz os servos", not p.get("animados"))


async def secao_sem_servos():
    print("\n[3] Mago sem servos morre sem aviso de pó")
    r = await montar(classe="mage")
    eventos = []
    async def broadcast(msg, **kw): eventos.append(msg)
    r.broadcast = broadcast
    await r._player_dies("p1")
    check("nenhum aviso de pó", not any(e.get("type") == "servos_viram_po" for e in eventos))


async def secao_entra_na_masmorra():
    print("\n[4] O servo restaurado reaparece junto do mago na masmorra nova")
    velho = S.make_player("v", "Pedro", "mage", 0)
    velho["animados"] = [{"id": "id_3", "owner": "v", "nome": "Esqueleto Animado", "tipo": "skeleton",
                          "vida_atual": 5, "vida_max": 8, "movimento": 4, "pos": [99, 99]}]
    snap = S.snapshot_character(velho)
    r = S.GameRoom("REST_SERVO")
    async def noop(*a, **k): pass
    r.broadcast = noop; r.send_to = noop
    p = S.make_player("novo", "Pedro", "mage", 0)
    S.restore_character(p, snap)
    r.players["novo"] = p; r.phase = "city"; r.host_pid = "novo"
    await r.enter_dungeon("novo")
    a = p["animados"][0]
    dist = max(abs(a["pos"][0] - p["pos"][0]), abs(a["pos"][1] - p["pos"][1]))
    check("servo perto do mago (raio 4)", dist <= 4, (p["pos"], a["pos"]))
    check("servo conta como aliado do mago", a in r._all_animados() and a["owner"] == "novo")


async def main():
    secao_salvar_e_voltar()
    await secao_entra_na_masmorra()
    await secao_morte_do_mago()
    await secao_sem_servos()
    print(f"\n{PASS} ok, {FAIL} falha(s)")
    sys.exit(1 if FAIL else 0)

asyncio.run(main())
