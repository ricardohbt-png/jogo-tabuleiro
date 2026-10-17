"""Gerador da campanha "A Maré do Charco" (Vila dos Charcos).

Roda da raiz do projeto:
    python tools/gerar_campanha_charcos.py            # valida e grava
    python tools/gerar_campanha_charcos.py --simular  # só relata (ND, XP, artes pedidas)
    python tools/gerar_campanha_charcos.py --forcar   # regrava masmorra editada à mão

Spec: docs/superpowers/specs/2026-10-17-campanha-mare-do-charco-design.md

Só toca no que é dele: as 5 masmorras `charcos_*.json`, os destinos `charcos_*` de
world_adventures.json, as conversas `charcos_*` da taverna da Vila dos Charcos, o modificador de
preço da vila e o troféu `ferrao_do_brejo`. Tudo o mais é relido e regravado intacto.
"""
import argparse
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import server as S  # noqa: E402
from gerar_campanha_sombras import (  # noqa: E402,F401
    Mapa, monstro, decor, fala, masmorra, nd_por_sala, faixa, salas_alcancaveis,
    _etapa, _ler_json, _gravar_json, assinatura, Conflito)
import gerar_campanha_sombras as _sombras  # noqa: E402

WALL, FLOOR, DOOR = S.WALL, S.FLOOR, S.DOOR

ARQUIVOS = ("charcos_1_bordas.json", "charcos_2_palafitas.json", "charcos_3_travessia.json",
            "charcos_4a_arredores.json", "charcos_4b_aldeia.json")
FATO_GANCHO = "charcos_criancas_sumidas"
FATO_MORTE = "charcos_criancas_mortas"
FATO_FERRAO = "charcos_ferrao_morto"
ITEM_TROFEU = "ferrao_do_brejo"
CIDADE = "vila_dos_charcos"
ASSINATURAS = os.path.join(RAIZ, "tools", ".charcos_assinaturas.json")
MUSICA_ABERTURA = "assets/story/a_song_of_old_stones.mp3"
MUSICA_FERRAO = "assets/story/the_kraken_s_overture.mp3"

# Cada slide só leva texto; a arte pedida fica em ARTES_PEDIDAS (o autor sobe as imagens pelo editor).
ARTES_PEDIDAS = []


def historia(chave, slides, audio=None):
    """Como `gerar_campanha_sombras.historia`, mas com a lista de artes DESTE gerador."""
    out = []
    for i, (texto, arte, *resto) in enumerate(slides):
        ARTES_PEDIDAS.append((f"{chave}#{i + 1}", arte))
        slide = {"text": texto, "fit": "contain"}
        if resto:      # condição do slide: {"requisito": {...}, "negar": bool}
            slide.update(resto[0])
        out.append(slide)
    h = {"slides": out}
    if audio:
        h["audio"] = audio
    return h


def _req(**campos):
    return S._clean_requirement(campos)


# ─── Destinos e história ─────────────────────────────────────────────────────
def destinos():
    ARTES_PEDIDAS.clear()
    base_x, base_y = S.WORLD_LOCATIONS[CIDADE]["x"], S.WORLD_LOCATIONS[CIDADE]["y"]

    def perto(dx, dy):
        return round(max(0, min(100, base_x + dx)), 2), round(max(0, min(100, base_y + dy)), 2)

    bordas_intro = historia("bordas.intro", [
        ("As crianças da Vila dos Charcos somem uma a uma, sempre ao anoitecer. Os rastros pequenos "
         "levam para a mata fechada, onde a lama engole o caminho.",
         "mata fechada ao entardecer, pegadas pequenas na lama"),
        ("Atrás de cada tronco, olhos que acompanham os heróis sem piscar.",
         "olhos brilhando entre árvores e capim alto"),
    ], MUSICA_ABERTURA)
    bordas_outro = historia("bordas.outro", [
        ("Ossos roídos, marcas de arrasto e um sapatinho enlameado. Ninguém ali — mas o rastro "
         "segue, atravessa uma ponte quebrada e desce para as palafitas.",
         "sapatinho de criança caído junto a ossos e uma ponte quebrada"),
    ])
    palafitas_intro = historia("palafitas.intro", [
        ("A aldeia de pescadores sobre estacas foi abandonada depois de ataques que ninguém soube "
         "explicar. As passarelas rangem sozinhas.",
         "casas de madeira sobre estacas num charco, névoa baixa"),
    ], MUSICA_ABERTURA)
    palafitas_outro = historia("palafitas.outro", [
        ("Numa carta, um pescador fala de homens encapuzados e de algo que tem medo do fogo. No "
         "depósito, óleo e piche — e rastros arrastados que descem para o pântano.",
         "carta amassada sobre um barril de piche, lamparina ao lado"),
    ])
    travessia_intro = historia("travessia.intro", [
        ("O pântano cobre tudo de verde-escuro. Cada passo afunda; cada sombra na água pode ter "
         "dentes.", "pântano de águas escuras com ilhotas e raízes"),
    ], MUSICA_ABERTURA)
    travessia_outro = historia("travessia.outro", [
        ("Fumaça. Cantos baixos. Do alto de uma ilhota, os heróis avistam a paliçada de uma aldeia "
         "que não está em nenhum mapa.", "paliçada de troncos entre névoa e totens de ossos"),
    ])
    arredores_intro = historia("arredores.intro", [
        ("Vigias de osso andam pelo caminho de tábuas. Os bruxos dos charcos não deixam os mortos "
         "descansarem.", "esqueletos e zumbis vigiando uma paliçada"),
        ("Daqui até o fim os lugares se emendam: o que for gasto não se recupera.",
         "portão de troncos entreaberto, fogo vermelho lá dentro"),
    ], MUSICA_ABERTURA)
    arredores_outro = historia("arredores.outro", [
        ("O portão cede. Dentro, a praça dos bruxos: totens, caldeirões e, ao fundo, um cercado "
         "de onde vêm vozes de criança.", "praça de aldeia de bruxos, caldeirões fumegantes, cercado ao fundo"),
    ])
    aldeia_intro = historia("aldeia.intro", [
        ("Atrás de uma parede de pedra e lama, algo respira. Os bruxos o chamam de arma. Mas ele "
         "não obedece a ninguém: o Ferrão dos Charcos Adulto, mais forte que o grupo.",
         "cova murada com uma criatura enorme de ferrão erguido", ),
        ("Fogo, piche e uma alavanca. O que os heróis fizerem com isso decide quem sai vivo.",
         "frasco de piche e uma alavanca de madeira"),
    ], MUSICA_FERRAO)
    aldeia_outro = historia("aldeia.outro", [
        ("O último passo é a fuga — ou o último golpe.", "portão da aldeia visto de dentro"),
    ])
    fim_rota = historia("aldeia.fim", [
        ("Os pequenos voltam para os braços das mães, sujos, assustados e vivos. A Vila dos Charcos "
         "acende todas as lamparinas da praça naquela noite.",
         "mães abraçando crianças na praça de uma vila de pescadores",
         {"requisito": _req(sem_fato=FATO_MORTE)}),
        ("O Ferrão tomba entre as chamas do piche, e com ele cai o poder dos bruxos. O nome do grupo "
         "vai de boca em boca, e o ferrão da fera passa a ser troféu de quem o venceu.",
         "o Ferrão caído em meio ao fogo, bruxos fugindo",
         {"requisito": _req(fato=FATO_FERRAO, sem_fato=FATO_MORTE)}),
        ("A fera ficou para trás, e o rugido seguiu os heróis até o rio. Dizem que ela ainda "
         "espera no charco. A vila agradece as crianças — e teme o que ficou vivo lá dentro.",
         "heróis cruzando um rio ao amanhecer com as crianças, silhueta enorme na névoa",
         {"requisito": _req(sem_fato=FATO_FERRAO)}),
        ("O Ferrão tomba, mas as crianças não vão voltar. A vila vira o rosto para o grupo; nas "
         "portas, o silêncio pesa mais que qualquer grito.",
         "heróis de cabeça baixa diante de uma vila de portas fechadas",
         {"requisito": _req(fato=FATO_MORTE)}),
        ("Mais fundo no charco, dizem os velhos, existe algo muito maior que o Adulto. Outras "
         "estradas esperam por vocês no mapa.", "mapa-múndi aberto sobre a mesa da taverna",
         {"requisito": _req(sem_fato=FATO_MORTE)}),
    ])

    def destino(did, nome, dx, dy, custo, etapas, requisito, renome, outro_rota=""):
        x, y = perto(dx, dy)
        return {"id": did, "nome": nome, "x": x, "y": y, "fome": custo, "sede": custo,
                "dungeons": etapas, "espera_retorno": {"modo": "fixa", "rodadas": 0, "dados": ""},
                "oculto_ate_liberar": True, "revisitavel": False, "outro_rota": outro_rota,
                "requisito": S._clean_requirement(requisito), "renome_recompensa": renome}

    return {
        "charcos_bordas": destino("charcos_bordas", "Bordas da Mata", 5, 3, 1,
                                  [_etapa("charcos_1_bordas.json", bordas_intro, bordas_outro)],
                                  {"fato": FATO_GANCHO}, 1),
        "charcos_palafitas": destino("charcos_palafitas", "Palafitas dos Pescadores", 10, 7, 2,
                                     [_etapa("charcos_2_palafitas.json", palafitas_intro, palafitas_outro)],
                                     {"aventura_id": "charcos_bordas"}, 1),
        "charcos_travessia": destino("charcos_travessia", "Travessia do Pântano", 15, 11, 2,
                                     [_etapa("charcos_3_travessia.json", travessia_intro, travessia_outro)],
                                     {"aventura_id": "charcos_palafitas"}, 1),
        "charcos_aldeia": destino("charcos_aldeia", "Aldeia dos Bruxos", 20, 15, 3,
                                  [_etapa("charcos_4a_arredores.json", arredores_intro, arredores_outro, encadear=True),
                                   _etapa("charcos_4b_aldeia.json", aldeia_intro, aldeia_outro)],
                                  {"aventura_id": "charcos_travessia"}, 2, outro_rota=fim_rota),
    }


# ─── Taverna, preços e troféu ────────────────────────────────────────────────
def _conversa(cid, texto, requisito=None, efeito=None, uma_vez=True):
    return {"id": cid, "texto": texto, "requisito": requisito or {},
            "efeito": efeito or {"renome": 0, "fato": "", "item_id": ""}, "uma_vez": uma_vez}


def conversas_taverna():
    """{slot_id: [conversa]} da taverna da Vila dos Charcos."""
    return {
        "npc_ms42peq8": [
            _conversa("charcos_gancho",
                      "Foram três crianças só esta semana. Minha Lia... saiu para buscar lenha ao anoitecer "
                      "e não voltou. Os rastros vão para a mata e, dizem, para as palafitas abandonadas, "
                      "rio abaixo. Por favor, tragam-nas de volta.",
                      {"sem_fato": FATO_MORTE}, {"renome": 0, "fato": FATO_GANCHO, "item_id": ""}),
            _conversa("charcos_gratidao",
                      "Minha Lia dorme em casa de novo. Não sei como agradecer. A vila inteira fala de vocês.",
                      {"sem_fato": FATO_MORTE, "aventura_id": "charcos_aldeia"}),
            _conversa("charcos_hostil_ysa",
                      "Saiam da minha frente. Prometeram trazê-las de volta. Prometeram.",
                      {"fato": FATO_MORTE}, uma_vez=False),
        ],
        "npc_ms42qx5t": [
            _conversa("charcos_rumor_taverneiro",
                      "Quem vive de pesca sabe: tem bicho no charco que não gosta de fogo. Se forem "
                      "mexer com ele, levem óleo — e algo que pegue fogo de longe.",
                      {"sem_fato": FATO_MORTE}),
            _conversa("charcos_hostil_taverneiro",
                      "Aqui o preço agora é o preço. Não gosto de dizer, mas a vila não quer vocês por perto.",
                      {"fato": FATO_MORTE}, uma_vez=False),
        ],
        "npc_ms42snq6": [
            _conversa("charcos_rumor_velho",
                      "Já ouvi falar do bicho que os encapuzados guardam: um ferrão grande como uma "
                      "lança. Nem eles o controlam. Se algo o solta, quem estiver perto é o primeiro.",
                      {"sem_fato": FATO_MORTE}),
            _conversa("charcos_hostil_velho",
                      "Foi por causa de vocês. Foi sim. Vão-se embora.",
                      {"fato": FATO_MORTE}, uma_vez=False),
        ],
    }


NOMES_NPC = {"npc_ms42peq8": "Ysa", "npc_ms42qx5t": "Bento", "npc_ms42snq6": "Velho Quim"}


def modificadores():
    return {CIDADE: [{"fato": FATO_MORTE, "preco_mult": 1.5}]}


def trofeu_bruto():
    return {"id": ITEM_TROFEU, "name": "Ferrão do Brejo", "emoji": "🗡️", "item_type": "weapon",
            "custom": True, "die": "1d6", "stat": "dex", "categoria": "perfurante", "finesse": True,
            "two_handed": False, "atk_bonus": 1, "damage_bonus": 0, "material": "metal",
            "extra_damages": [], "allowed_classes": [], "price": 400,
            "disponibilidade": {"loja": False, "baus": True, "loot_monstro": False}}


# ─── Masmorras (os mapas moram em tools/charcos_mapas.py) ────────────────────
def masmorras(so_dados=False):
    if so_dados:
        return {}
    import charcos_mapas as M
    return {"charcos_1_bordas.json": M.masmorra_bordas(), "charcos_2_palafitas.json": M.masmorra_palafitas(),
            "charcos_3_travessia.json": M.masmorra_travessia(), "charcos_4a_arredores.json": M.masmorra_arredores(),
            "charcos_4b_aldeia.json": M.masmorra_aldeia()}


# ─── Montagem e gravação ─────────────────────────────────────────────────────
def preparar(so_dados=False):
    """Monta e valida TUDO em memória. Levanta ValueError na primeira invalidez.

    Registrar o troféu com `S._apply_custom_items` MUTA os catálogos globais do processo (é
    assim que o baú da aldeia o encontra na validação) — mesma ressalva do gerador anterior."""
    ok, trofeu = S._validate_custom_item(trofeu_bruto())
    if not ok:
        raise ValueError(f"troféu inválido: {trofeu}")
    outros = [r for r in S._read_custom_items() if isinstance(r, dict) and r.get("id") != ITEM_TROFEU]
    S._apply_custom_items(outros + [trofeu])
    mm = masmorras(so_dados)
    for arquivo, defn in mm.items():
        ok, msg = S.validar_dungeon(defn)
        if not ok:
            raise ValueError(f"{arquivo}: {msg}")
    dst = destinos()
    if not so_dados:
        if set(mm) != set(ARQUIVOS):
            raise ValueError(f"masmorras() != ARQUIVOS: {sorted(mm)} vs {sorted(ARQUIVOS)}")
    for did, destino in dst.items():
        for etapa in destino["dungeons"]:
            if etapa["file"] not in ARQUIVOS:
                raise ValueError(f"{did}: etapa referencia arquivo desconhecido {etapa['file']!r}")
    conv = {sid: S._clean_scene_conversations(cs, "") for sid, cs in conversas_taverna().items()}
    return {"masmorras": mm, "destinos": dst, "trofeu": trofeu, "conversas": conv,
            "modificadores": modificadores()}


def caminhos_padrao():
    c = _sombras.caminhos_padrao()
    c["assinaturas"] = ASSINATURAS
    c["mods"] = S.CITY_PRICE_MODS_FILE
    return c


def aplicar(artefatos, caminhos=None, forcar=False, regen_editor=True):
    """Grava os artefatos. Só toca no que é da campanha. Tudo ou nada: confere
    conflitos antes de gravar o primeiro arquivo."""
    c = dict(caminhos_padrao(), **(caminhos or {}))
    assin = _ler_json(c["assinaturas"], {})
    conflitos = []
    for arquivo in artefatos["masmorras"]:
        caminho = os.path.join(c["dungeons_dir"], arquivo)
        if os.path.exists(caminho) and not forcar:
            atual = _ler_json(caminho, None)
            if atual is None or assin.get(arquivo) != assinatura(atual):
                conflitos.append(arquivo)
    if conflitos:
        raise Conflito("editadas depois de geradas (use --forcar): " + ", ".join(conflitos))
    cenas = _ler_json(c["scenes"], {})
    slots = ((cenas.get(CIDADE) or {}).get("taverna") or {}).get("slots") or []
    por_id = {s.get("id"): s for s in slots if isinstance(s, dict)}
    faltam = [sid for sid in artefatos["conversas"] if sid not in por_id]
    if faltam:
        raise ValueError(f"city_scenes.json: slots da taverna da Vila dos Charcos não encontrados: {faltam}")

    os.makedirs(c["dungeons_dir"], exist_ok=True)
    for arquivo, defn in artefatos["masmorras"].items():
        _gravar_json(os.path.join(c["dungeons_dir"], arquivo), defn)
        assin[arquivo] = assinatura(defn)
    _gravar_json(c["assinaturas"], assin)

    aventuras = _ler_json(c["adventures"], {})
    for did, dest in artefatos["destinos"].items():
        aventuras[did] = dest
    _gravar_json(c["adventures"], aventuras)

    for sid, convs in artefatos["conversas"].items():
        slot = por_id[sid]
        if slot.get("name") in (None, "", "Novo NPC") and sid in NOMES_NPC:
            slot["name"] = NOMES_NPC[sid]
        manter = [cv for cv in (slot.get("conversations") or []) if not str(cv.get("id", "")).startswith("charcos_")]
        slot["conversations"] = manter + convs
    _gravar_json(c["scenes"], cenas)

    mods = _ler_json(c["mods"], {})
    if not isinstance(mods, dict):
        mods = {}
    mods.update(artefatos["modificadores"])
    _gravar_json(c["mods"], mods)

    itens = [r for r in _ler_json(c["items"], []) if isinstance(r, dict) and r.get("id") != ITEM_TROFEU]
    itens.append(artefatos["trofeu"])
    _gravar_json(c["items"], itens)
    antigo = S.CUSTOM_ITEMS_INDEX
    S.CUSTOM_ITEMS_INDEX = c["items_index"]
    try:
        S._regen_custom_items_index(itens)
    finally:
        S.CUSTOM_ITEMS_INDEX = antigo
    if regen_editor:
        S._regen_dungeons_index()


def relatorio(artefatos):
    linhas = []
    for arquivo, defn in artefatos["masmorras"].items():
        poder = defn["expected_party"]["heroes"] * defn["expected_party"]["level"]
        linhas.append(f"{arquivo}  (poder {poder})")
        for rid, nd in nd_por_sala(defn).items():
            linhas.append(f"   sala {rid}: ND {nd:g} -> {faixa(nd, poder)} ({nd / poder:.2f})")
    linhas.append("Artes pedidas pelos slides:")
    linhas += [f"   {k}: {arte}" for k, arte in ARTES_PEDIDAS]
    return "\n".join(linhas)


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Gera a campanha A Maré do Charco.")
    ap.add_argument("--simular", action="store_true", help="só relata, não grava")
    ap.add_argument("--forcar", action="store_true", help="regrava masmorra editada à mão")
    args = ap.parse_args(argv)
    try:
        artefatos = preparar()
    except (ValueError, NotImplementedError) as e:
        print(f"ERRO: {e}  (nada foi gravado)")
        return 1
    print(relatorio(artefatos))
    if args.simular:
        return 0
    try:
        aplicar(artefatos, forcar=args.forcar)
    except (Conflito, ValueError) as e:
        print(f"RECUSADO: {e}  (nada foi gravado)")
        return 2
    print("OK: 5 masmorras, 4 destinos, conversas da taverna, modificador de preço e troféu gravados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
