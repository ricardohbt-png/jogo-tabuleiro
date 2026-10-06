"""Capítulos e pontos de salvamento. Roda da raiz: python tools/test_pontos_salvamento.py"""
import asyncio, sys, os, tempfile, shutil, copy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond, extra=""):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name} {extra}")

_PILHA = []
def loja_tmp():
    raiz = tempfile.mkdtemp()
    _PILHA.append((S.LOJA, raiz))
    S.LOJA = S.LojaDocumentos(S.AdaptadorArquivo(raiz))
    S.LOJA.carregar()
def loja_volta():
    loja, raiz = _PILHA.pop()
    S.LOJA = loja
    shutil.rmtree(raiz, ignore_errors=True)

def jogo(owner="ana", membros=("ana",), play_mode="solo", has_master=False):
    sg = S.create_savegame("Teste", owner, "procedural", None, has_master, play_mode=play_mode)
    for m in membros:
        sg["members"][m] = {"class_id": "warrior", "status": "active"}
    sg["characters"]["warrior"] = {"gold": 10}
    S.write_savegame(sg)
    return sg

def docs_de(sid):
    return [k for k in S.LOJA.listar("pontos") if k.startswith(sid + "_")]

def secao_nucleo():
    print("\n[1] Jogo novo nasce com o capítulo 1 vazio")
    sg = jogo()
    caps = sg.get("capitulos")
    check("um capítulo", isinstance(caps, list) and len(caps) == 1)
    check("capítulo 1 sem pontos", caps[0]["n"] == 1 and caps[0]["pontos"] == [])
    check("capitulo_atual = 1", sg.get("capitulo_atual") == 1)
    check("arquivado_por vazio", sg.get("arquivado_por") == [])

    print("\n[2] Automáticos rodam: ficam só os 3 mais recentes")
    ids = []
    for i in range(4):
        meta, e = S.registrar_ponto(sg, "auto", rotulo="cidade")
        ids.append(meta["id"])
    autos = [p for p in S.capitulo_atual(sg)["pontos"] if p["tipo"] == "auto"]
    check("3 automáticos no índice", len(autos) == 3, len(autos))
    check("o mais antigo saiu do índice", ids[0] not in [p["id"] for p in autos])
    check("e o documento dele foi apagado", len(docs_de(sg["id"])) == 3)
    check("o mais novo vem primeiro", autos[0]["id"] == ids[-1])

    print("\n[3] Manuais: teto de 10 por capítulo")
    for i in range(S.PONTOS_MANUAIS_MAX):
        meta, e = S.registrar_ponto(sg, "manual", nome=f"m{i}", por="ana")
        if e: break
    check("10 manuais aceitos", e is None)
    meta, e = S.registrar_ponto(sg, "manual", nome="demais", por="ana")
    check("o 11º é recusado", meta is None and e is not None)
    check("manual guarda nome e autor",
          any(p["nome"] == "m0" and p["por"] == "ana" for p in S.capitulo_atual(sg)["pontos"]))

    print("\n[4] O ponto é uma cópia profunda do estado")
    sg2 = jogo(owner="bia", membros=("bia",))
    meta, _ = S.registrar_ponto(sg2, "manual", nome="antes", por="bia")
    sg2["characters"]["warrior"]["gold"] = 999
    doc = S.LOJA.ler("pontos", f"{sg2['id']}_{meta['id']}")
    check("mudar o jogo não muda o ponto", doc["estado"]["characters"]["warrior"]["gold"] == 10)
    check("ponto lembra o capítulo", doc["capitulo"] == 1)
    check("local da cidade vem do nome do mundo", meta["onde"] == "cidade" and meta["local"] == "Alva e Luz")

def main():
    loja_tmp()
    try:
        secao_nucleo()
    finally:
        loja_volta()
    print(f"\n{PASS} ok, {FAIL} falha(s)")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
