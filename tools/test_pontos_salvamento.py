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

    print("\n[9b] Jogo abandonado pelo Mestre: um jogador abre o próximo capítulo")
    mm = jogo(owner="mestre", membros=("bia", "caio"), play_mode="multiplayer", has_master=True)
    ok, e = S.abandon_master_campaign(mm["id"], "mestre")
    check("Mestre abandonou", ok and S.load_savegame(mm["id"])["status"] == "ended_master_left", e)
    check("estranho não retoma", not S.try_novo_capitulo("zé", mm["id"], "x", None)[0])
    S.SAVEGAMES_IN_USE[mm["id"]] = "ABCD"
    try:
        check("jogo aberto recusa retomar", not S.try_novo_capitulo("bia", mm["id"], "x", None)[0])
    finally:
        S.SAVEGAMES_IN_USE.pop(mm["id"], None)
    ok, e = S.try_novo_capitulo("bia", mm["id"], "Sem Mestre", None)
    mm = S.load_savegame(mm["id"])
    check("jogadora criou o capítulo", ok, e)
    check("jogo ativo de novo", mm["status"] == "active")
    check("ela virou a dona/anfitriã", mm["owner"] == "bia" and S._anfitriao_do_jogo(mm) == "bia")
    check("sem Mestre", mm["has_master"] is False and mm.get("master_account") is None)
    check("multiplayer", mm["play_mode"] == "multiplayer")
    check("capítulo 2 existe", mm["capitulo_atual"] == 2 and len(mm["capitulos"]) == 2)

    print("\n[9c] Sala parada com o mesmo jogo")
    sg = jogo()
    p, _ = S.registrar_ponto(sg, "manual", nome="z"); S.write_savegame(sg)
    sala = S.GameRoom("PARADA")
    sala.savegame = sg; sala.savegame_id = sg["id"]
    S.rooms["PARADA"] = sala
    try:
        sala.connections["x"] = object()
        check("sala com alguém conectado recusa carregar",
              not S.try_carregar_ponto("ana", sg["id"], p["id"])[0])
        check("e recusa apagar o jogo", not S.delete_savegame(sg["id"], "ana")[0])
        check("a sala segue ligada", "PARADA" in S.rooms and sala.savegame is sg)
        sala.connections.clear()
        ok, e = S.try_carregar_ponto("ana", sg["id"], p["id"])
        check("sala vazia: carregar funciona", ok, e)
        check("e a sala foi desligada e recolhida",
              "PARADA" not in S.rooms and sala.savegame is None and sala.savegame_id is None)
    finally:
        S.rooms.pop("PARADA", None)


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
    antes = next((p for p in pai["capitulos"][0]["pontos"] if p.get("rotulo") == "antes_de_fundir"), None)
    doc = antes and S.LOJA.ler("pontos", f"{pai['id']}_{antes['id']}")
    check("pai guardou 'antes de fundir' no capítulo dele",
          bool(doc) and doc["estado"]["characters"]["warrior"]["gold"] == 10)
    S.migrar_continuacoes_para_capitulos()
    check("rodar de novo não muda nada", len(S.load_savegame(pai["id"])["capitulos"]) == 2)
    print("\n[11b] Cadeia, filho malformado e queda no meio")
    a = jogo(owner="ana"); b_ = jogo(owner="ana"); c = jogo(owner="ana")
    a["created"] = "2020-01-01"; b_["created"] = "2020-01-02"; c["created"] = "2020-01-03"
    b_["parent_campaign_id"] = a["id"]; c["parent_campaign_id"] = b_["id"]
    c["characters"]["warrior"]["gold"] = 555
    S.registrar_ponto(c, "manual", nome="do c")
    for x in (a, b_, c): S.write_savegame(x)
    S.migrar_continuacoes_para_capitulos()
    a2 = S.load_savegame(a["id"])
    check("cadeia: 3 capítulos na raiz", len(a2["capitulos"]) == 3 and a2["capitulo_atual"] == 3)
    check("cadeia: estado vivo = do C", a2["characters"]["warrior"]["gold"] == 555)
    check("cadeia: B e C apagados", S.load_savegame(b_["id"]) is None and S.load_savegame(c["id"]) is None)
    check("cadeia: ponto do C no capítulo 3",
          any(p["nome"] == "do c" for p in a2["capitulos"][2]["pontos"]))

    pai = jogo(owner="ana"); pai["created"] = "2021-01-01"; S.write_savegame(pai)
    ruim = jogo(owner="ana"); ruim["created"] = "2021-01-02"
    ruim["parent_campaign_id"] = pai["id"]
    ruim["capitulos"] = [{"pontos": [{}]}]; S.write_savegame(ruim)
    bom = jogo(owner="ana"); bom["created"] = "2021-01-03"
    bom["parent_campaign_id"] = pai["id"]; S.write_savegame(bom)
    try:
        S.migrar_continuacoes_para_capitulos(); lancou = False
    except Exception:
        lancou = True
    check("malformado não levanta", not lancou)
    check("malformado continua intacto", S.load_savegame(ruim["id"]) is not None)
    check("irmão válido fundiu", S.load_savegame(bom["id"]) is None
          and len(S.load_savegame(pai["id"])["capitulos"]) == 2)

    pai = jogo(owner="ana"); pai["created"] = "2022-01-01"; S.write_savegame(pai)
    fil = jogo(owner="ana"); fil["created"] = "2022-01-02"; fil["parent_campaign_id"] = pai["id"]
    S.registrar_ponto(fil, "manual", nome="f"); S.write_savegame(fil)
    S.migrar_continuacoes_para_capitulos()
    # simula queda: filho e seu documento de ponto reaparecem; pai já fundido
    S.write_savegame(fil)
    for cap in fil["capitulos"]:
        for p in cap["pontos"]:
            S.LOJA.gravar("pontos", S._ponto_chave(fil["id"], p["id"]), {"sid": fil["id"], "id": p["id"], "capitulo": 1, "estado": {}})
    S.migrar_continuacoes_para_capitulos()
    check("queda: não duplica capítulos", len(S.load_savegame(pai["id"])["capitulos"]) == 2)
    check("queda: filho e documentos limpos", S.load_savegame(fil["id"]) is None and docs_de(fil["id"]) == [])


async def secao_sala():
    print("\n[12] Pontos gravados pela sala")
    sg = jogo(owner="ana")
    r = S.GameRoom("PONTO")
    enviados = []
    async def broadcast(msg, skip=None): enviados.append(msg)
    async def send_to(pid, msg): enviados.append(msg)
    async def push_state(): pass
    r.broadcast = broadcast; r.send_to = send_to; r.push_state = push_state
    r.savegame = sg; r.savegame_id = sg["id"]
    r.players["p0"] = S.make_player("p0", "Ana", "warrior", 0)
    r.player_order = ["p0"]; r.host_pid = "p0"; r.phase = "city"
    r.account_by_pid["p0"] = "ana"
    await r.enter_dungeon("p0")
    await r._liberar_intro_masmorra(True)
    r._ultima_foto = None
    rotulos = lambda: [p.get("rotulo") for p in S.capitulo_atual(sg)["pontos"]]
    r._foto_janela_pendente = lambda: "sorte_reacao"
    antes = len(S.capitulo_atual(sg)["pontos"]); enviados.clear()
    await r.handle_salvar_ponto("p0", "cedo")
    check("sem foto e com janela aberta: recusa salvar",
          any(getattr(m.get("msg"), "key", None) == "erro.aguarde_para_salvar" for m in enviados)
          and len(S.capitulo_atual(sg)["pontos"]) == antes)
    del r._foto_janela_pendente
    check("1ª foto da visita grava ponto de entrada", r._gravar_foto_rodada() and "entrada_masmorra" in rotulos())
    r.round_num = S.PONTO_AUTO_RODADAS
    r._gravar_foto_rodada()
    check("a cada 5 rodadas grava ponto 'rodada'", "rodada" in rotulos())
    r.round_num = S.PONTO_AUTO_RODADAS + 1
    antes = len(S.capitulo_atual(sg)["pontos"])
    r._gravar_foto_rodada()
    check("rodada que não é múltipla de 5 não grava ponto", len(S.capitulo_atual(sg)["pontos"]) == antes)
    await r.handle_salvar_ponto("p0", "Antes do Troll")
    manual = next((p for p in S.capitulo_atual(sg)["pontos"] if p["tipo"] == "manual"), None)
    check("salvar agora grava ponto manual com nome e autor",
          manual and manual["nome"] == "Antes do Troll" and manual["por"] == "ana")
    check("e responde ponto_salvo", any(m.get("type") == "ponto_salvo" for m in enviados))
    check("o ponto manual da masmorra guarda a rodada", manual["onde"] == "masmorra")
    await r.handle_salvar_e_sair("p0")
    check("salvar e sair grava ponto 'sair'", "sair" in rotulos())
    r.test_mode = True
    antes = len(S.capitulo_atual(sg)["pontos"])
    r._ponto_automatico("cidade")
    check("sala de teste não grava ponto", len(S.capitulo_atual(sg)["pontos"]) == antes)


def secao_fiacao():
    print("\n[13] Mensagens de conta despachadas no handler")
    src = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "server.py"),
               encoding="utf-8").read()
    for t, fn in (("carregar_ponto", "try_carregar_ponto"), ("apagar_ponto", "try_apagar_ponto"),
                  ("novo_capitulo", "try_novo_capitulo"), ("arquivar_jogo", "try_arquivar_jogo")):
        check(f"{t} -> {fn}", f'"{t}"' in src and f'{fn}(account["name"]' in src)
        check(f"{t} é mensagem da conexão", t in S.MENSAGENS_DA_CONEXAO)
    check("salvar_ponto é mensagem da conexão", "salvar_ponto" in S.MENSAGENS_DA_CONEXAO)


def main():
    loja_tmp()
    try:
        secao_nucleo()
        secao_conta()
        secao_migracao()
        asyncio.run(secao_sala())
        secao_fiacao()
    finally:
        loja_volta()
    print(f"\n{PASS} ok, {FAIL} falha(s)")
    sys.exit(1 if FAIL else 0)

if __name__ == "__main__":
    main()
