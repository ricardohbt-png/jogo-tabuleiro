"""kill_target/kill_all não cumprem enquanto o Troll caído ainda vai se erguer.
Roda da raiz: python -X utf8 tools/test_objetivo_troll_regenera.py"""
import os, sys
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

r = S.GameRoom("TRL")
t = {"id": "t1", "type": "troll", "hp": 0, "max_hp": 30, "authored_target": True}
r.monsters = {"t1": t}
ok = True
def chk(n, c):
    global ok
    print(("✅ " if c else "❌ ") + n); ok = ok and c
t["troll_regenerando"] = True
chk("regenerando: kill_target não cumprido", not r._objetivo_cumprido({"type": "kill_target"}))
chk("regenerando: kill_all não cumprido", not r._objetivo_cumprido({"type": "kill_all"}))
t.pop("troll_regenerando")
chk("morte definitiva: kill_target cumprido", r._objetivo_cumprido({"type": "kill_target"}))
chk("morte definitiva: kill_all cumprido", r._objetivo_cumprido({"type": "kill_all"}))
sys.exit(0 if ok else 1)
