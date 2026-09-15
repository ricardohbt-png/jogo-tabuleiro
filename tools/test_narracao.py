"""Narração do servidor (etapa 4b-i) — migração para T() e tradução.
Roda da raiz: python tools/test_narracao.py"""
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
# EXATAMENTE o mesmo padrão que o script de migração reconhece. Se o teste
# cobrisse mais do que o script sabe fazer, ficaria vermelho por trabalho que
# ninguém combinou.
RE_UMA_LINHA = re.compile(r'gm_say\((f?)"([^"]*)"\)')


def _rodar_verificacoes():
    print("\n[1] Dicionário de narração carregado")
    check("existe src/lang/narracao.js",
          os.path.isfile(os.path.join(RAIZ, "src", "lang", "narracao.js")))
    check("o servidor funde as chaves de narração",
          any(k.startswith("narracao.") for k in S.LANG_STRINGS))

    print("\n[2] Migração do lote mecânico")
    restantes = RE_UMA_LINHA.findall(FONTE)
    check(f"nenhum gm_say de uma linha com literal sobrou ({len(restantes)})",
          not restantes)
    for _, t in restantes[:6]:
        print("     sobrou:", t[:70])

    print("\n[3] Nenhuma narração em português sobrou no servidor")
    # Até a etapa 4b-i isto era só um RELATÓRIO — as formas difíceis seguiam em
    # português de propósito e o teste não podia cobrá-las. A 4b-ii as migrou
    # todas, então o placar virou cobrança: se alguma voltar, fica vermelho.
    #
    # A varredura é por `ast`, não por linha: multilinha, concatenação e
    # f-string que atravessa a linha são a MESMA árvore para o parser, e uma
    # heurística de texto erraria justamente nelas.
    import ast as _ast
    cruas = []
    for _no in _ast.walk(_ast.parse(FONTE)):
        if not (isinstance(_no, _ast.Call) and isinstance(_no.func, _ast.Attribute)
                and _no.func.attr == "gm_say" and len(_no.args) == 1):
            continue
        _a = _no.args[0]
        # T(...) e gm(...) já devolvem texto tardio; Name é variável que guarda um;
        # `T(...) if x else T(...)` escolhe entre dois tardios — também vale.
        def _tardio(n):
            if isinstance(n, _ast.Name): return True
            if isinstance(n, _ast.Call) and isinstance(n.func, _ast.Name) and n.func.id in ("T", "gm"): return True
            if isinstance(n, _ast.IfExp): return _tardio(n.body) and _tardio(n.orelse)
            return False
        if _tardio(_a):
            continue
        cruas.append((_no.lineno, (_ast.get_source_segment(FONTE, _a) or "?")
                      .replace("\n", " ")[:70]))
    check(f"nenhum gm_say com texto em português ({len(cruas)})", not cruas)
    for _l, _s in cruas[:6]:
        print(f"     L{_l}: {_s}")

    print("\n[4] Chaves usadas e chaves sem uso")
    usadas = set(re.findall(r'T\(\s*"(narracao\.[^"]+)"', FONTE))
    faltando = sorted(k for k in usadas if k not in S.LANG_STRINGS)
    check(f"nenhuma chave de narração órfã (usadas: {len(usadas)})", not faltando)
    if faltando:
        print("     órfãs:", ", ".join(faltando[:8]))
    no_dic = {k for k in S.LANG_STRINGS if k.startswith("narracao.")}
    sem_uso = sorted(no_dic - usadas)
    check(f"relatório de chaves sem uso emitido ({len(sem_uso)})", True)
    if sem_uso:
        print("     sem uso:", ", ".join(sem_uso[:8]))

    print("\n[5] Uma narração migrada chega em dois idiomas, pelo broadcast real")
    import asyncio

    class RecWS:
        def __init__(self): self.sent = []
        async def send(self, data): self.sent.append(data)

    chave = next((k for k, v in S.LANG_STRINGS.items()
                  if k.startswith("narracao.") and v.get("en")), None)
    if not chave:
        check("há ao menos uma narração traduzida para provar", False)
    else:
        sala = S.GameRoom("TESTE_NARR")
        ws_pt, ws_en = RecWS(), RecWS()
        sala.connections = {"n_pt": ws_pt, "n_en": ws_en}
        S.LANG_BY_PID["n_pt"] = "pt"
        S.LANG_BY_PID["n_en"] = "en"
        asyncio.run(sala.gm_say(S.T(chave)))
        pt = json.loads(ws_pt.sent[-1])["text"]
        en = json.loads(ws_en.sent[-1])["text"]
        check("sai em português para quem está em pt", pt == S.LANG_STRINGS[chave]["pt"])
        check("sai em inglês para quem está em en", en == S.LANG_STRINGS[chave]["en"])
        for pid in ("n_pt", "n_en"):
            S.LANG_BY_PID.pop(pid, None)

    print("\n[6] Nomes de catálogo dentro da frase")

    def _r(x, lang):
        """Renderiza como o json.dumps faria para uma conexão naquele idioma."""
        return S.t(x.key, lang, **x.params) if isinstance(x, S.T) else str(x)

    # Monstro NATIVO: traduz.
    orc_pt = S.LANG_STRINGS["cat.monstro.orc.nome"]["pt"]
    orc = {"type": "orc", "name": orc_pt}
    check("monstro nativo usa o en do catálogo",
          _r(S.nome_criatura(orc), "en") == S.LANG_STRINGS["cat.monstro.orc.nome"]["en"])
    check("monstro nativo em pt continua igual", _r(S.nome_criatura(orc), "pt") == orc_pt)

    # Monstro AUTORAL: sem chave → sai cru, nos dois idiomas.
    autoral = {"type": "soldado_do_autor", "name": "Soldado do Autor"}
    check("monstro autoral sai cru", _r(S.nome_criatura(autoral), "en") == "Soldado do Autor")

    # Nativo RENOMEADO no editor: tem chave, mas o nome não bate → sai cru.
    renomeado = {"type": "orc", "name": "Orc Veterano de Khaz"}
    check("nativo renomeado preserva o nome do autor",
          _r(S.nome_criatura(renomeado), "en") == "Orc Veterano de Khaz")

    # Jogador: nunca traduz, mesmo com nome igual ao de um monstro.
    check("nome de jogador nunca é traduzido",
          _r(S.nome_criatura({"class_id": "warrior", "name": orc_pt}), "en") == orc_pt)

    # Item nativo. Sem `if`: se o id sumir do catálogo, o teste tem de ficar
    # vermelho — um `if item:` silencioso já deixou esta checagem sem rodar.
    antid = next(i for i in S.SHOP_MERCHANT if i["id"] == "antidote")
    check("item nativo traduz",
          _r(S.nome_item(dict(antid)), "en") == S.LANG_STRINGS["cat.item.antidote.nome"]["en"])
    # Item autoral (id que não existe no catálogo) sai cru.
    check("item autoral sai cru",
          _r(S.nome_item({"id": "espada_do_autor", "name": "Espada do Autor"}), "en")
          == "Espada do Autor")

    print("\n[7] Nome composto do instrumento")
    # Esta tabela é A MESMA da seção [N] de tools/test_vocabulario_cliente.js, de
    # propósito: a composição tem DUAS implementações (_instrumento_nome_T aqui e
    # _instrumentoComposto no src/i18n.js) e nada além destes dois testes impede
    # que elas divirjam. Mexeu numa, confira a outra.
    # (base, qualidade, origem, encantamento, pt esperado, en esperado)
    casos = [
        ("harpa",  "padrao",   "humana", "nenhum", "Harpa Padrão",           "Standard Harp"),
        ("harpa",  "velho",    "humana", "nenhum", "Harpa Velha",            "Old Harp"),
        ("tambor", "velho",    "humana", "nenhum", "Tambor de Guerra Velho", "Old War Drum"),
        ("harpa",  "rustico",  "elfica", "nenhum", "Harpa Rústica Élfica",   "Rustic Elven Harp"),
        ("harpa",  "padrao",   "humana", "runico", "Harpa Padrão Rúnica",    "Standard Runic Harp"),
        ("harpa",  "refinado", "elfica", "runico", "Harpa Lendária Élfica",  "Legendary Elven Harp"),
        ("alaude", "refinado", "ana",    "runico", "Alaúde Lendário Anão",   "Legendary Dwarven Lute"),
    ]
    for base, ql, orig, enc, esp_pt, esp_en in casos:
        inst = S.criar_instrumento(base, ql, origem=orig, encantamento=enc)
        rot = f"{base}/{ql}/{orig}/{enc}"
        # O nome GRAVADO no estado continua sendo português puro — é ele que vai
        # a disco no savegame. Estas 7 checagens são a rede que garante que a
        # etapa 4c não mexeu no `_instrumento_nome`.
        check(f"{rot} — name gravado em pt", inst["name"] == esp_pt)
        tt = S._instrumento_nome_T(inst)
        check(f"{rot} — T em pt", _r(tt, "pt") == esp_pt)
        check(f"{rot} — T em en", _r(tt, "en") == esp_en)

    print("\n[8] Sufixos compostos, derivados de campo e não de mutação de nome")

    alab = next(i for i in S.SHOP_WEAPONS if i["id"] == "alabarda_prata")
    corroido = dict(alab, corrosao_inicial=1)
    check("item corroído — pt",
          _r(S.nome_item(corroido), "pt") == f"{alab['name']} (corroído)")
    check("item corroído — en",
          _r(S.nome_item(corroido), "en") == "Silver Halberd (corroded)")

    virotes = next(i for i in S.SHOP_AMMO if i["id"] == "virotes")
    loot = dict(virotes, ammo_count=7)
    check("munição — pt", _r(S.nome_item(loot), "pt") == "Virotes (×7)")
    check("munição — en", _r(S.nome_item(loot), "en") == "Bolts (×7)")

    animado = {"tipo": "goblin", "nome": "Goblin Animado",
               "nome_base": "Goblin", "vida_atual": 5}
    check("servo animado — pt", _r(S.nome_criatura(animado), "pt") == "Goblin Animado")
    check("servo animado — en", _r(S.nome_criatura(animado), "en") == "Animated Goblin")

    # As mutações de nome têm de ter sumido do fonte: se voltarem, o sufixo
    # apareceria DUAS vezes (uma na string, outra composta pelo nome_item).
    # Procura a ATRIBUIÇÃO, não a palavra: o comentário que explica a regra
    # também contém "(corroído)".
    check("server.py não muta mais o nome com (corroído)",
          not re.search(r'\["name"\]\s*=.*corroído', FONTE))
    # Só a MUTAÇÃO some; o SKU de loja "Virotes (×10)" continua no SHOP_AMMO.
    check("server.py não muta mais o nome dos virotes",
          'virote_loot["name"]' not in FONTE)
    # Tem de ser o SITE DE CRIAÇÃO do animado — `"nome_base" in FONTE` sozinho
    # passa por causa do próprio helper `nome_criatura`, que lê o campo.
    check("handle_animar_mortos grava nome_base",
          bool(re.search(r'"nome_base"\s*:\s*corpse\[', FONTE)))

    print("\n[9] Nome trocado em runtime")
    # Nome trocado em runtime nunca casa a guarda de igualdade — sairia cru para
    # sempre. O campo `name_key` é a saída explícita.
    elem = {"type": "elemental_eletrico", "name": "Elemental Descontrolado",
            "name_key": "cat.monstro.elemental_descontrolado"}
    check("name_key vence a guarda de igualdade — pt",
          _r(S.nome_criatura(elem), "pt") == "Elemental Descontrolado")
    check("name_key vence a guarda de igualdade — en",
          _r(S.nome_criatura(elem), "en") == "Uncontrolled Elemental")
    check("o pergaminho marca a chave no elemental",
          bool(re.search(r'"name_key"\]\s*=\s*"cat\.monstro\.elemental_descontrolado"', FONTE)))

    print("\n[10] O motor junta listas com separador do idioma")
    S.LANG_STRINGS["narracao._teste_lista"] = {
        "pt": "Controla {quem}.", "en": "Controls {quem}."}

    def _lista(itens, lang):
        return S.t("narracao._teste_lista", lang, quem=itens)

    check("lista vazia não deixa separador solto", _lista([], "pt") == "Controla .")
    check("um item", _lista(["os animados"], "pt") == "Controla os animados.")
    check("dois itens em pt",
          _lista(["os animados", "o prisioneiro"], "pt")
          == "Controla os animados e o prisioneiro.")
    check("dois itens em en",
          _lista(["the minions", "the prisoner"], "en")
          == "Controls the minions and the prisoner.")
    check("três itens em pt", _lista(["a", "b", "c"], "pt") == "Controla a, b e c.")
    check("três itens em en", _lista(["a", "b", "c"], "en") == "Controls a, b and c.")
    # O elemento pode ser ele próprio um T — é o caso de nome de catálogo.
    check("elemento T é resolvido no idioma do leitor",
          _lista([S.T("cat.monstro.orc.nome")], "en")
          == "Controls " + S.LANG_STRINGS["cat.monstro.orc.nome"]["en"] + ".")
    S.LANG_STRINGS.pop("narracao._teste_lista", None)

    print("\n[11] O pool gm() sorteia uma vez e resolve por idioma")
    v = S.gm("intro")
    check("gm() devolve T", isinstance(v, S.T))
    check("a chave do pool existe no dicionário", v.key in S.LANG_STRINGS)
    check("a chave aponta para uma variante do GM",
          S.LANG_STRINGS.get(v.key, {}).get("pt") in S.GM["intro"])
    check("há uma chave para cada variante de cada pool",
          all(f"narracao.gm.{k}.{i}" in S.LANG_STRINGS
              for k, vs in S.GM.items() for i in range(len(vs))))

    # A regressão que mais importa: o sorteio é UM só. Dois jogadores em idiomas
    # diferentes têm de ler a MESMA variante — um sorteio por idioma seria
    # invisível num teste de uma conexão só.
    import asyncio as _aio

    class _RecWS:
        def __init__(self): self.sent = []
        async def send(self, data): self.sent.append(data)

    sala_p = S.GameRoom("TESTE_POOL")
    wa, wb = _RecWS(), _RecWS()
    sala_p.connections = {"g_pt": wa, "g_en": wb}
    S.LANG_BY_PID["g_pt"] = "pt"; S.LANG_BY_PID["g_en"] = "en"
    escolhido = S.gm("intro")
    _aio.run(sala_p.gm_say(escolhido))
    txt_pt = json.loads(wa.sent[-1])["text"]
    txt_en = json.loads(wb.sent[-1])["text"]
    check("quem está em pt lê o pt daquela variante",
          txt_pt == S.LANG_STRINGS[escolhido.key]["pt"])
    check("quem está em en lê o en da MESMA variante",
          txt_en == (S.LANG_STRINGS[escolhido.key].get("en")
                     or S.LANG_STRINGS[escolhido.key]["pt"]))
    for pid in ("g_pt", "g_en"):
        S.LANG_BY_PID.pop(pid, None)

    print("\n[12] Produtores devolvem T — e T não concatena, de propósito")
    sala_e = S.GameRoom("TESTE_PROD")
    p_fake = {"name": "Thorin", "class_id": "warrior", "gear": {}, "bag": [],
              "bag_size": 6}
    log = sala_e._equip_into_slot(p_fake, {"id": "dagger", "name": "Adaga"},
                                  "main_hand", "🗡️")
    check("_equip_into_slot devolve T", isinstance(log, S.T))
    # O `if log:` dos chamadores continua valendo porque T tem __len__.
    check("a frase é truthy", bool(log))
    check("sai traduzida", "equipped" in S.t(log.key, "en", **log.params))

    # T NÃO tem __add__ de propósito: operadores são buscados no TIPO e não
    # passam pelo __getattr__, então `T + str` estoura alto em vez de perder a
    # tradução em silêncio. Foi assim que o site da 2ª arma foi pego — nenhuma
    # suíte exercitava aquele caminho.
    estourou = False
    try:
        log + " sufixo"
    except TypeError:
        estourou = True
    check("T + str estoura em vez de perder a tradução", estourou)
    check("nenhum gm_say concatena com o T de um produtor",
          "log + " not in FONTE)

    env = S.T("narracao.equipou_2a_arma_mao_esquerda", frase=log)
    check("a frase envolvida resolve o T aninhado",
          "(2nd weapon" in S.t(env.key, "en", **env.params)
          and "equipped" in S.t(env.key, "en", **env.params))

    # 2ª ocorrência da MESMA classe (2026-08-27): o rótulo do d20 DESCARTADO
    # concatenava `T("dado.ataque_mao_principal") + " — descartado"`, e TODO
    # ataque de jogador com vantagem/desvantagem estourava TypeError dentro do
    # handle_attack — munição debitada, dano nunca resolvido, "erro interno" na
    # tela. A varredura acima (`"log + "`) é estreita demais para pegar isso,
    # então aqui o caminho é exercitado de verdade: `_rolar_ataque` devolve um
    # d20 descartado (é o que vantagem/desvantagem produzem) e o ataque roda.
    dados_desc = []

    async def _cap_dado(msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "dice_roll" and msg.get("discarded"):
            dados_desc.append(msg)

    async def _noop_async(*a, **k): pass

    sala_d = S.GameRoom("TESTE_DESCARTE")
    sala_d.phase = "playing"; sala_d.round_num = 1
    sala_d.gm_say = _noop_async; sala_d.push_state = _noop_async
    sala_d.send_to = _noop_async; sala_d.broadcast = _cap_dado
    sala_d.current_pid = lambda: "h"; sala_d._is_turn = lambda pid: True
    heroi = S.make_player("h", "Heroi", "warrior", 0)
    heroi["pos"] = [0, 0]; heroi["alive"] = True
    heroi["fome"] = 20; heroi["sede"] = 20
    heroi["weapon"] = {"id": "machado_basico", "name": "Machado", "die": "1d6", "stat": "str_"}
    sala_d.players["h"] = heroi
    sala_d.monsters = {"m1": {"id": "m1", "name": "Alvo", "nome": "Alvo", "pos": [0, 1],
                              "hp": 30, "max_hp": 30, "ac": 10, "ca": 10, "alive": True}}
    sala_d._rolar_ataque = lambda *a, **k: (True, 15, 18, False, 7)
    _erro_ataque = None
    try:
        _aio.run(sala_d.handle_attack("h", "m1"))
    except Exception as exc:            # pragma: no cover - é o que se quer evitar
        _erro_ataque = exc
    check("ataque com d20 descartado não estoura", _erro_ataque is None)
    check("o d20 descartado foi anunciado", len(dados_desc) == 1)
    _rot = dados_desc[0]["label"] if dados_desc else None
    check("o rótulo do descartado é um T, não uma string montada",
          isinstance(_rot, S.T))
    if isinstance(_rot, S.T):
        check("o descartado sai em português",
              "descartado" in S.t(_rot.key, "pt", **_rot.params))
        check("o descartado sai em inglês",
              "discarded" in S.t(_rot.key, "en", **_rot.params))


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Narração do servidor (etapa 4b-i)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
