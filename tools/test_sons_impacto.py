"""Campo `impacto` do attack_feedback (sons do golpe). Spec:
docs/superpowers/specs/2026-09-23-sons-efeitos-sonoros-design.md"""
import sys, os, io, contextlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
with contextlib.redirect_stdout(io.StringIO()):
    import server as S

PASS = FAIL = 0
def check(nome, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {nome}")
    else:    FAIL += 1; print(f"  ❌ {nome}")

print("\n[1] Herói: pela categoria da arma")
check("espada longa → cortante", S._impacto_de({"id": "espada2m", "categoria": "cortante"}) == "cortante")
check("adaga → perfurante", S._impacto_de(S.WEAPONS["dagger"]) == "perfurante")
check("categoria contundente", S._impacto_de({"categoria": "contundente"}) == "contundente")
check("herói desarmado (None) → contundente", S._impacto_de(None) == "contundente")
check("arma de herói sem categoria → contundente", S._impacto_de({"id": "x", "name": "Garra"}) == "contundente")

print("\n[2] Monstro: nome natural vence a categoria")
check("Mordida perfurante → natural",
      S._impacto_de({"name": "Mordida", "categoria": "perfurante", "damage_types": ["physical"]}, monstro=True) == "natural")
check("Garras → natural", S._impacto_de({"name": "Garras"}, monstro=True) == "natural")
check("Ferrão (acento) → natural", S._impacto_de({"name": "Ferrão"}, monstro=True) == "natural")
check("Pinça → natural", S._impacto_de({"name": "Pinça"}, monstro=True) == "natural")
check("Chifrada → natural", S._impacto_de({"name": "Chifrada"}, monstro=True) == "natural")

print("\n[3] Monstro: arma pela categoria ou pelo nome")
check("Espada Curta com categoria", S._impacto_de({"name": "Espada Curta", "categoria": "cortante"}, monstro=True) == "cortante")
check("Clava Pesada sem categoria → contundente", S._impacto_de({"name": "Clava Pesada"}, monstro=True) == "contundente")
check("Lança Curta sem categoria → perfurante", S._impacto_de({"name": "Lança Curta"}, monstro=True) == "perfurante")
check("Machado sem categoria → cortante", S._impacto_de({"name": "Machado"}, monstro=True) == "cortante")

print("\n[4] Monstro: elemental e desconhecido não têm impacto")
check("Chama (fire) → None", S._impacto_de({"name": "Chama", "damage_types": ["fire"]}, monstro=True) is None)
check("Garra Congelante (cold) → None",
      S._impacto_de({"name": "Garra Congelante", "damage_types": ["cold"]}, monstro=True) is None)
check("'Ataque' genérico → contundente", S._impacto_de({"name": "Ataque"}, monstro=True) == "contundente")

print("\n[5] Todo ataque físico de MONSTER_DEFS tem impacto (nenhum None)")
sem = sorted({a.get("name") for d in S.MONSTER_DEFS for a in (d.get("attacks") or [])
              if (a.get("damage_types") or ["physical"]) == ["physical"]
              and S._impacto_de(a, monstro=True) is None})
print("     sem impacto:", sem)
check("nenhum ataque físico volta None", len(sem) == 0)

print("\n[6] _emitir_feedback_ataque: sem impacto a chave some")
import asyncio
r = S.GameRoom("TEST")
enviados = []
async def cap(msg, *a, **k): enviados.append(msg)
r.broadcast = cap
atacante = {"id": "a", "name": "A", "pos": [0, 0]}
alvo = {"id": "b", "name": "B", "pos": [1, 0]}
asyncio.run(r._emitir_feedback_ataque("start", atacante, alvo, "Espada", impacto="cortante"))
asyncio.run(r._emitir_feedback_ataque("start", atacante, alvo, "Soco", impacto=None))
check("com impacto a chave vai", enviados[0].get("impacto") == "cortante")
check("sem impacto a chave NÃO vai", "impacto" not in enviados[1])

print("\n[7] Ataque Giratório: o start emite impacto (fiação estática)")
with open(os.path.join(os.path.dirname(__file__), "..", "server.py"), encoding="utf-8") as fh:
    _src = fh.read()
_anc = _src.find("async def _executar_ataque_giratorio(")
check("achou a função do Ataque Giratório", _anc != -1)
_call = _src.find("_emitir_feedback_ataque(", _anc) if _anc != -1 else -1
check("achou a chamada _emitir_feedback_ataque dentro da função", _call != -1)
_janela = _src[_call:_call + 400] if _call != -1 else ""
check("chamada é de 'start'", '"start"' in _janela)
check("chamada inclui impacto=_impacto_de(", "impacto=_impacto_de(" in _janela)

print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
sys.exit(1 if FAIL else 0)
