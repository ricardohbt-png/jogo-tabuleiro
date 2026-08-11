"""Mensagens de erro do servidor (etapa 4a) — migração para T() e tradução.
Roda da raiz: python tools/test_erros.py"""
import io, json, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

FONTE = io.open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
# As duas formas de mandar erro no servidor. Capturam só literais — o que já
# virou T(...) não casa, que é justamente como medimos o progresso.
RE_MSG = re.compile(r'"msg":\s*(f?)"([^"]{2,200})"')
RE_ERR = re.compile(r'await err\((f?)"([^"]{2,200})"')
RE_PARAM = re.compile(r"\{(\w+)\}")


def _rodar_verificacoes():
    print("\n[1] Dicionário de erros carregado")
    check("existe src/lang/erros.js",
          os.path.isfile(os.path.join(RAIZ, "src", "lang", "erros.js")))
    check("o servidor funde as chaves de erro",
          any(k.startswith("erro.") for k in S.LANG_STRINGS))

    print("\n[2] Paridade de parâmetros entre pt e en")
    # A falha mais provável numa tradução em lote, e a mais visível: se o "en"
    # perde um {nome}, o jogador lê a chave crua na tela. Vale para TODOS os
    # arquivos de idioma, não só os desta etapa.
    divergentes = []
    traduzidas = 0
    for k, v in S.LANG_STRINGS.items():
        en = v.get("en")
        if not en:
            continue
        traduzidas += 1
        if set(RE_PARAM.findall(v.get("pt") or "")) != set(RE_PARAM.findall(en)):
            divergentes.append(k)
    check(f"nenhum parâmetro divergente ({traduzidas} chaves traduzidas)", not divergentes)
    if divergentes:
        print("     divergentes:", ", ".join(divergentes[:10]))

    print("\n[3] O site que serializa cru resolve T")
    # server.py:6941 manda o erro por ws.send(json.dumps(...)) direto, sem passar
    # por send_to nem err — e é o encoder deles que resolve o T. Sem default=,
    # um T ali estoura TypeError.
    crus = []
    linhas = FONTE.split("\n")
    for i, l in enumerate(linhas):
        if '"msg":' not in l or "json.dumps" not in l:
            continue
        ctx = "\n".join(linhas[i:i + 3])
        if "send_to" in ctx or "await err" in ctx or "broadcast" in ctx:
            continue
        if "default=" not in ctx:
            crus.append(i + 1)
    check("nenhum site de erro serializa sem o encoder", not crus)
    if crus:
        print("     linhas:", crus)

    print("\n[4] Migração do texto fixo")
    fixos_msg = [t for f, t in RE_MSG.findall(FONTE) if not f]
    fixos_err = [t for f, t in RE_ERR.findall(FONTE) if not f]
    check("nenhum literal de erro de texto fixo sobrou no server.py",
          not fixos_msg and not fixos_err)
    if fixos_msg or fixos_err:
        for t in (fixos_msg + fixos_err)[:6]:
            print("     sobrou:", t[:70])

    print("\n[5] Toda chave erro.* usada existe no dicionário")
    usadas = set(re.findall(r'T\(\s*"(erro\.[^"]+)"', FONTE))
    faltando = sorted(k for k in usadas if k not in S.LANG_STRINGS)
    check(f"nenhuma chave de erro órfã (usadas: {len(usadas)})", not faltando)
    if faltando:
        print("     órfãs:", ", ".join(faltando[:8]))

    print("\n[6] Chave do erros.js sem uso é relatada")
    # Não falha: um texto pode voltar a ser usado. O relatório evita o arquivo
    # virar depósito de frases mortas.
    no_dic = {k for k in S.LANG_STRINGS if k.startswith("erro.")}
    sem_uso = sorted(no_dic - usadas)
    check(f"relatório de chaves sem uso emitido ({len(sem_uso)})", True)
    if sem_uso:
        print("     sem uso:", ", ".join(sem_uso[:8]))

    print("\n[7] Um erro migrado chega traduzido, pelo send_to real")
    import asyncio

    class RecWS:
        """WebSocket falso que guarda o JSON cru — prova que dois jogadores
        receberam a MESMA recusa em idiomas diferentes."""
        def __init__(self): self.sent = []
        async def send(self, data): self.sent.append(data)

    chave = next((k for k, v in S.LANG_STRINGS.items()
                  if k.startswith("erro.") and v.get("en")), None)
    if not chave:
        check("há ao menos uma mensagem de erro traduzida para provar", False)
    else:
        sala = S.GameRoom("TESTE_ERRO")
        ws_pt, ws_en = RecWS(), RecWS()
        sala.connections = {"e_pt": ws_pt, "e_en": ws_en}
        S.LANG_BY_PID["e_pt"] = "pt"
        S.LANG_BY_PID["e_en"] = "en"
        asyncio.run(sala.send_to("e_pt", {"type": "error", "msg": S.T(chave)}))
        asyncio.run(sala.send_to("e_en", {"type": "error", "msg": S.T(chave)}))
        pt = json.loads(ws_pt.sent[-1])["msg"]
        en = json.loads(ws_en.sent[-1])["msg"]
        check("sai em português para quem está em pt", pt == S.LANG_STRINGS[chave]["pt"])
        check("sai em inglês para quem está em en", en == S.LANG_STRINGS[chave]["en"])
        for pid in ("e_pt", "e_en"):
            S.LANG_BY_PID.pop(pid, None)


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Mensagens de erro (etapa 4a)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
