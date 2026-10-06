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

def secao_conta():
    print("\n[5] Carregar devolve o estado e guarda o de antes")
    sg = jogo()
    alvo, _ = S.registrar_ponto(sg, "auto", rotulo="cidade")      # gold 10
    S.registrar_ponto(sg, "auto", rotulo="cidade")
    S.registrar_ponto(sg, "auto", rotulo="cidade")                  # alvo é o mais antigo
    sg["characters"]["warrior"]["gold"] = 99
    sg["dungeon_snapshot"] = {"onde": "masmorra", "rodada": 3, "masmorra_nome": "Minas"}
    S.write_savegame(sg)
    ok, e = S.try_carregar_ponto("ana", sg["id"], alvo["id"])
    sg = S.load_savegame(sg["id"])
    check("carregou", ok, e)
    check("ouro voltou a 10", sg["characters"]["warrior"]["gold"] == 10)
    check("foto que não existia no ponto saiu", "dungeon_snapshot" not in sg)
    antes = next((p for p in S.capitulo_atual(sg)["pontos"] if p.get("rotulo") == "antes_de_carregar"), None)
    check("ponto 'antes de carregar' criado", antes is not None)
    doc = S.LOJA.ler("pontos", f"{sg['id']}_{antes['id']}")
    check("ele guarda o estado substituído (99)", doc["estado"]["characters"]["warrior"]["gold"] == 99)
    check("o ponto carregado não foi apagado pela rotação",
          S._achar_ponto(sg, alvo["id"])[1] is not None)

    print("\n[6] Só o anfitrião carrega/apaga; jogo aberto recusa")
    mp = jogo(owner="ana", membros=("ana", "bia"), play_mode="multiplayer")
    p, _ = S.registrar_ponto(mp, "manual", nome="x", por="bia"); S.write_savegame(mp)
    ok, e = S.try_carregar_ponto("bia", mp["id"], p["id"])
    check("convidado não carrega", not ok)
    ok, e = S.try_apagar_ponto("bia", mp["id"], p["id"])
    check("convidado não apaga", not ok)
    check("estranho não carrega", not S.try_carregar_ponto("zé", mp["id"], p["id"])[0])
    S.SAVEGAMES_IN_USE[mp["id"]] = "ABCD"
    try:
        check("jogo aberto recusa carregar", not S.try_carregar_ponto("ana", mp["id"], p["id"])[0])
    finally:
        S.SAVEGAMES_IN_USE.pop(mp["id"], None)
    ok, e = S.try_apagar_ponto("ana", mp["id"], p["id"])
    check("anfitrião apaga", ok and S._achar_ponto(S.load_savegame(mp["id"]), p["id"])[1] is None)
    check("documento do ponto apagado", S.LOJA.ler("pontos", f"{mp['id']}_{p['id']}") is None)
    com_mestre = jogo(owner="ana", membros=("bia",), play_mode="multiplayer", has_master=True)
    q, _ = S.registrar_ponto(com_mestre, "manual", nome="y"); S.write_savegame(com_mestre)
    check("com Mestre, o anfitrião é o Mestre", S._anfitriao_do_jogo(com_mestre) == "ana")
    com_mestre.pop("master_account", None)
    check("Mestre legado sem master_account: anfitrião é o dono", S._anfitriao_do_jogo(com_mestre) == "ana")

    print("\n[7] Novo capítulo no mesmo jogo")
    sg = jogo()
    sg["campaign_phase"] = 3
    sg["dungeon_snapshot"] = {"onde": "masmorra", "rodada": 2}
    S.write_savegame(sg)
    ok, e = S.try_novo_capitulo("ana", sg["id"], "Parte dois", None)
    sg = S.load_savegame(sg["id"])
    check("criou", ok, e)
    check("dois capítulos, atual = 2", len(sg["capitulos"]) == 2 and sg["capitulo_atual"] == 2)
    check("fase zerada e foto limpa", sg["campaign_phase"] == 0 and "dungeon_snapshot" not in sg)
    check("heróis mantidos", sg["characters"]["warrior"]["gold"] == 10)
    check("capítulo 1 fechou com 'fim do capítulo'",
          sg["capitulos"][0]["pontos"][0].get("rotulo") == "fim_capitulo")
    check("convidado não cria capítulo", not S.try_novo_capitulo("zé", sg["id"], "x", None)[0])

    print("\n[8] Arquivar é por conta")
    mp = jogo(owner="ana", membros=("ana", "bia"), play_mode="multiplayer")
    ok, e = S.try_arquivar_jogo("bia", mp["id"], True)
    check("arquivou", ok, e)
    da_bia = next(s for s in S.list_savegames("bia") if s["id"] == mp["id"])
    da_ana = next(s for s in S.list_savegames("ana") if s["id"] == mp["id"])
    check("para a bia está arquivado", da_bia["arquivado"] is True)
    check("para a ana não", da_ana["arquivado"] is False)
    check("lista leva anfitrião e capítulos",
          da_ana["anfitriao"] == "ana" and da_ana["capitulos"][0]["n"] == 1 and da_ana["capitulo_atual"] == 1)
    S.try_arquivar_jogo("bia", mp["id"], False)
    check("desarquivar volta", next(s for s in S.list_savegames("bia") if s["id"] == mp["id"])["arquivado"] is False)

    print("\n[9] Apagar o jogo apaga os pontos")
    sg = jogo()
    S.registrar_ponto(sg, "manual", nome="a"); S.write_savegame(sg)
    check("tem ponto", len(docs_de(sg["id"])) == 1)
    ok, _ = S.delete_savegame(sg["id"], "ana")
    check("apagou jogo e pontos", ok and docs_de(sg["id"]) == [])


def secao_migracao():
    print("\n[10] Jogo antigo ganha capítulo 1 com 1 ponto, uma vez só")
    sg = jogo()
    for k in ("capitulos", "capitulo_atual", "arquivado_por"):
        sg.pop(k, None)
    S.write_savegame(sg)
    check("ensure migra", S.ensure_campaign_schema(sg) is True)
    pontos = sg["capitulos"][0]["pontos"]
    check("1 ponto 'migrado'", len(pontos) == 1 and pontos[0]["rotulo"] == "migrado")
    S.ensure_campaign_schema(sg)
    check("idempotente", len(sg["capitulos"]) == 1 and len(sg["capitulos"][0]["pontos"]) == 1)
    novo = jogo()
    check("jogo novo não ganha ponto de migração", novo["capitulos"][0]["pontos"] == [])
    check("dict sem id não quebra", S.garantir_capitulos({"members": {}, "characters": {}}) is True)

    print("\n[11] Continuação antiga vira capítulo do jogo de origem")
    pai = jogo(owner="ana")
    filho = jogo(owner="ana")
    filho["parent_campaign_id"] = pai["id"]
    filho["characters"]["warrior"]["gold"] = 77
    S.registrar_ponto(filho, "manual", nome="do filho"); S.write_savegame(filho)
    orfao = jogo(owner="ana")
    orfao["parent_campaign_id"] = "sg_zzzzzz"; S.write_savegame(orfao)
    S.migrar_continuacoes_para_capitulos()
    pai = S.load_savegame(pai["id"])
    check("filho sumiu", S.load_savegame(filho["id"]) is None)
    check("pai tem 2 capítulos, atual = 2", len(pai["capitulos"]) == 2 and pai["capitulo_atual"] == 2)
    check("estado vivo do pai = o do filho", pai["characters"]["warrior"]["gold"] == 77)
    manual = next(p for p in pai["capitulos"][1]["pontos"] if p["nome"] == "do filho")
    doc = S.LOJA.ler("pontos", f"{pai['id']}_{manual['id']}")
    check("ponto do filho mudou de dono", doc is not None and doc["sid"] == pai["id"] and doc["capitulo"] == 2)
    check("nenhum documento do filho sobrou", docs_de(filho["id"]) == [])
    check("órfão ficou como jogo próprio", S.load_savegame(orfao["id"]) is not None)
    S.migrar_continuacoes_para_capitulos()
    check("rodar de novo não muda nada", len(S.load_savegame(pai["id"])["capitulos"]) == 2)


def main():
    loja_tmp()
    try:
        secao_nucleo()
        secao_conta()
        secao_migracao()
    finally:
        loja_volta()
    print(f"\n{PASS} ok, {FAIL} falha(s)")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
