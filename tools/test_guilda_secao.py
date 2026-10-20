"""Guilda — Disparo Duplo e Arremesso Rápido aparecem em Técnicas (recarga zero).

Roda da raiz:  python -X utf8 tools/test_guilda_secao.py
          e:   node tools/test_guilda_secao_cliente.js

REGRA
  • Só muda ONDE aparecem: as duas continuam sendo especializações passivas
    (sempre ativas depois de compradas, sem ocupar o 4º slot).
  • O catálogo marca `secao: "tecnica"` para o cliente listá-las na faixa de
    recarga zero das Técnicas da Guilda.
"""
import os, sys
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

print("\n[1] Catálogo")
for gid in ("disparo_duplo", "arremesso_rapido"):
    item = S.GUILD_CATALOG[gid]
    check(f"{gid}: listada na seção Técnicas", item.get("secao") == "tecnica", item.get("secao"))
    check(f"{gid}: continua especialização passiva (regras intactas)",
          item["categoria"] == "especializacao" and item["recarga_rodadas"] == 0
          and not item.get("automatica") and item["preco"] == 250)
    check(f"{gid}: chega ao cliente com o campo", any(
        i["id"] == gid and i.get("secao") == "tecnica" for i in S.guild_items_for_class("warrior")))
check("só essas duas usam a seção emprestada",
      sorted(k for k, v in S.GUILD_CATALOG.items() if v.get("secao")) == ["arremesso_rapido", "disparo_duplo"])
check("as demais especializações seguem na seção delas",
      all(v.get("secao") is None for k, v in S.GUILD_CATALOG.items()
          if v["categoria"] == "especializacao" and k not in ("disparo_duplo", "arremesso_rapido")))

print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
sys.exit(1 if FAIL else 0)
