"""Cenas de conversa por local — várias cenas por cidade, vinculadas a pontos.
  • CITY_SCENES[cidade][cena] substitui TAVERN_SCENES[cidade].
  • Migração: tavern_scenes.json vira a cena de id "taverna".
  • Conversa de uso único some do payload depois de resolvida.
  • Conversa bloqueada por requisito não vaza texto.
Roda da raiz: python tools/test_cenas_conversa.py"""
import asyncio, json, os, shutil, sys, tempfile
from copy import deepcopy
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def isolar_arquivos():
    """Redireciona os JSON para uma pasta temporária e devolve o restaurador."""
    tmpdir = tempfile.mkdtemp(prefix="cenas_teste_")
    arquivos = ("CITY_SCENES_FILE", "CITY_MAP_POINTS_FILE", "CITY_SHOPS_FILE", "WORLD_CITIES_FILE")
    originais = {nome: getattr(S, nome) for nome in arquivos}
    for nome in arquivos:
        setattr(S, nome, os.path.join(tmpdir, nome.lower() + ".json"))
    inicial = {"scenes": deepcopy(S.CITY_SCENES), "points": deepcopy(S.CITY_MAP_POINTS),
               "shops": deepcopy(S.CITY_SHOPS)}
    def restaurar():
        for nome, valor in originais.items(): setattr(S, nome, valor)
        for alvo, copia in ((S.CITY_SCENES, inicial["scenes"]),
                            (S.CITY_MAP_POINTS, inicial["points"]),
                            (S.CITY_SHOPS, inicial["shops"])):
            alvo.clear(); alvo.update(copia)
        shutil.rmtree(tmpdir, ignore_errors=True)
    return restaurar

def _rodar_verificacoes():
    print("\n[1] Estrutura CITY_SCENES")
    check("CITY_SCENES existe", isinstance(S.CITY_SCENES, dict))
    check("cena da taverna sob a chave 'taverna'",
          isinstance(S.CITY_SCENES.get("alva_e_luz", {}).get("taverna"), dict))
    cena = S.CITY_SCENES["alva_e_luz"]["taverna"]
    check("cena tem nome", cena.get("nome") == "Taverna")
    # O fundo real vem do city_scenes.json do usuário e não é previsível aqui;
    # o que importa é que a reestruturação preservou UM fundo válido.
    fundo = cena.get("background") or ""
    check("cena preserva um fundo válido", fundo.startswith("assets/") and fundo.endswith(".png"))
    check("cena preserva os slots da taverna", len(cena.get("slots", [])) >= 8)
    check("cidade sem cenas nasce dict vazio",
          isinstance(S.CITY_SCENES.get("vila_riacho"), dict))

    print("\n[2] _cena_vazia")
    vazia = S._cena_vazia("Docas")
    check("nome aplicado", vazia["nome"] == "Docas")
    check("sem slots", vazia["slots"] == [])
    check("modo padrão individual", vazia["mode"] == "individual")

    print("\n[3] Loader cria cena nova vinda do arquivo")
    with open(S.CITY_SCENES_FILE, "w", encoding="utf-8") as f:
        json.dump({"alva_e_luz": {"docas": {
            "nome": "Docas", "background": "assets/city/docas.png",
            "mode": "individual", "mask": "", "slots": [
                {"id": "npc_pescador", "name": "Pescador", "image": "assets/tavern/slots/barman.png",
                 "x": 10, "y": 20, "w": 12, "h": 24, "z": 1, "dialog": "O mar anda estranho.",
                 "conversations": [{"id": "boato", "texto": "Vi luzes no farol.",
                                    "requisito": {}, "efeito": {"renome": 1, "fato": "farol", "item_id": ""},
                                    "uma_vez": True}]}]}}}, f)
    S._load_city_scenes()
    docas = S.CITY_SCENES["alva_e_luz"].get("docas")
    check("cena nova criada pelo arquivo", isinstance(docas, dict))
    check("slot da cena nova carregado", len(docas.get("slots", [])) == 1)
    check("conversa da cena nova carregada",
          docas["slots"][0]["conversations"][0]["id"] == "boato")
    check("taverna continua existindo", "taverna" in S.CITY_SCENES["alva_e_luz"])

    print("\n[4] Saver grava o dicionário inteiro")
    S._save_city_scenes()
    with open(S.CITY_SCENES_FILE, "r", encoding="utf-8") as f: gravado = json.load(f)
    check("arquivo tem as duas cenas de Alva e Luz",
          set(gravado.get("alva_e_luz", {})) >= {"taverna", "docas"})

    print("\n[5] Migração do tavern_scenes.json")
    antigo = os.path.join(os.path.dirname(S.CITY_SCENES_FILE), "tavern_antigo.json")
    novo = os.path.join(os.path.dirname(S.CITY_SCENES_FILE), "city_novo.json")
    with open(antigo, "w", encoding="utf-8") as f:
        json.dump({"graciero": {"background": "assets/city/g.png", "mode": "individual",
                                "mask": "", "slots": []}}, f)
    guarda = (S.CITY_SCENES_FILE, S.TAVERN_SCENES_FILE)
    S.CITY_SCENES_FILE, S.TAVERN_SCENES_FILE = novo, antigo
    S._migrar_tavern_scenes()
    with open(novo, "r", encoding="utf-8") as f: convertido = json.load(f)
    check("cena antiga vira a cena 'taverna'", "taverna" in convertido.get("graciero", {}))
    check("nome padrão aplicado", convertido["graciero"]["taverna"].get("nome") == "Taverna")
    check("arquivo antigo continua existindo", os.path.exists(antigo))
    S._migrar_tavern_scenes()   # idempotente: não sobrescreve o que já existe
    with open(novo, "r", encoding="utf-8") as f: check("migração é idempotente", json.load(f) == convertido)
    S.CITY_SCENES_FILE, S.TAVERN_SCENES_FILE = guarda

    print("\n[6] Teto de 16 cenas por cidade")
    muitas = {f"cena_{i}": {"nome": f"C{i}", "background": "", "mode": "individual",
                            "mask": "", "slots": []} for i in range(30)}
    with open(S.CITY_SCENES_FILE, "w", encoding="utf-8") as f:
        json.dump({"vila_riacho": muitas}, f)
    S._load_city_scenes()
    check("no máximo 16 cenas por cidade", len(S.CITY_SCENES["vila_riacho"]) <= 16)

    print("\n[7] Ida e volta do editor não corrompe as cenas")
    payload = S._city_shops_editor_payload()
    check("payload do editor manda scenes", isinstance(payload.get("scenes"), dict))
    check("payload do editor não manda mais taverns", "taverns" not in payload)
    enviado = deepcopy(payload["scenes"])
    enviado.setdefault("alva_e_luz", {})["taverna"]["nome"] = "Taverna do Porto"
    ok_rt, _cfg = S._save_city_shops_upload(S.CITY_SHOPS, enviado, None)
    check("save aceito", ok_rt is True)
    check("nome da cena aplicado",
          S.CITY_SCENES["alva_e_luz"]["taverna"]["nome"] == "Taverna do Porto")
    check("nenhuma chave solta virou cena",
          all(isinstance(v, dict) and "slots" in v for v in S.CITY_SCENES["alva_e_luz"].values()))
    check("ids de cena continuam válidos",
          all(S.CENA_ID_RE.fullmatch(k) for k in S.CITY_SCENES["alva_e_luz"]))

    print("\n[8] Sincronia por cidade e vínculo do ponto")
    S.CITY_SCENES.setdefault("alva_e_luz", {})
    S._sincronizar_cidades_derivadas()
    ponto_taverna = S.CITY_MAP_POINTS["alva_e_luz"].get("taverna")
    check("ponto da taverna existe", isinstance(ponto_taverna, dict))
    check("ponto da taverna aponta para a cena taverna",
          ponto_taverna.get("scene") == "taverna")
    check("toda cidade tem entrada em CITY_SCENES",
          all(cid in S.CITY_SCENES for cid in S.WORLD_LOCATIONS))
    S.CITY_SCENES["cidade_fantasma"] = {}
    S._sincronizar_cidades_derivadas()
    check("cidade inexistente é removida", "cidade_fantasma" not in S.CITY_SCENES)

    print("\n[9] Payload das cenas")
    sala = S.GameRoom("CENA")
    async def noop(*a, **k): pass
    sala.gm_say = noop; sala.broadcast = noop; sala.send_to = noop
    sala._checkpoint_savegame = lambda *a, **k: None
    sala.phase = "city"; sala.world_location = "alva_e_luz"
    sala.players["p1"] = S.make_player("p1", "Victor", "warrior", 0)
    S.CITY_SCENES["alva_e_luz"]["provas"] = {
        "nome": "Provas", "background": "assets/city/x.png", "art_ratio": 1.5,
        "mode": "individual", "mask": "", "slots": [
            {"id": "npc_teste", "name": "Teste", "image": "assets/x.png",
             "x": 5, "y": 5, "w": 10, "h": 10, "z": 1, "dialog": "",
             "conversations": [
                 {"id": "livre",   "texto": "SEGREDO-LIVRE",   "requisito": {},
                  "efeito": {"renome": 0, "fato": "", "item_id": ""}, "uma_vez": False},
                 {"id": "unica",   "texto": "SEGREDO-UNICA",   "requisito": {},
                  "efeito": {"renome": 0, "fato": "", "item_id": ""}, "uma_vez": True},
                 {"id": "trancada","texto": "SEGREDO-TRANCADA",
                  "requisito": {"renome_min": 999},
                  "efeito": {"renome": 0, "fato": "", "item_id": ""}, "uma_vez": False},
             ]}]}
    cenas = sala._cenas_payload()
    check("payload traz a cena nova", "provas" in cenas)
    ids = [c["id"] for c in cenas["provas"]["slots"][0]["conversations"]]
    check("conversa livre aparece", "livre" in ids)
    check("conversa de uso único ainda não usada aparece", "unica" in ids)
    check("conversa trancada NÃO aparece", "trancada" not in ids)
    check("texto da trancada não vaza", "SEGREDO-TRANCADA" not in json.dumps(cenas))
    sala.scene_conversations_done.add("alva_e_luz:provas:npc_teste:unica")
    cenas2 = sala._cenas_payload()
    ids2 = [c["id"] for c in cenas2["provas"]["slots"][0]["conversations"]]
    check("uso único resolvido some do payload", "unica" not in ids2)
    check("uso repetido continua", "livre" in ids2)
    check("CITY_SCENES não foi mutado pela filtragem",
          len(S.CITY_SCENES["alva_e_luz"]["provas"]["slots"][0]["conversations"]) == 3)
    payload = sala._city_state_payload()
    check("city_state manda scenes", isinstance(payload.get("scenes"), dict))
    check("city_state não manda mais tavern", "tavern" not in payload)
    del S.CITY_SCENES["alva_e_luz"]["provas"]

    print("\n[10] handle_scene_npc")
    S.CITY_SCENES["alva_e_luz"]["provas"] = {
        "nome": "Provas", "background": "assets/city/x.png", "art_ratio": 1.5,
        "mode": "individual", "mask": "", "slots": [
            {"id": "npc_teste", "name": "Teste", "image": "assets/x.png",
             "x": 5, "y": 5, "w": 10, "h": 10, "z": 1, "dialog": "",
             "conversations": [
                 {"id": "unica", "texto": "Pronto.", "requisito": {},
                  "efeito": {"renome": 3, "fato": "pista_a", "item_id": ""}, "uma_vez": True}]}]}
    erros = []
    async def cap_send(pid, msg, *a, **k):
        if isinstance(msg, dict) and msg.get("type") == "error": erros.append(msg["msg"])
    sala.send_to = cap_send
    sala.renome = 0; sala.fatos = set(); sala.scene_conversations_done = set()
    asyncio.run(sala.handle_scene_npc("p1", "provas", "npc_teste", "unica"))
    check("renome concedido", sala.renome == 3)
    check("fato registrado", "pista_a" in sala.fatos)
    check("chave tem 4 partes",
          "alva_e_luz:provas:npc_teste:unica" in sala.scene_conversations_done)
    asyncio.run(sala.handle_scene_npc("p1", "provas", "npc_teste", "unica"))
    check("segunda vez recusada", any("já foi concluída" in e for e in erros))
    check("renome não subiu de novo", sala.renome == 3)
    erros.clear()
    asyncio.run(sala.handle_scene_npc("p1", "inexistente", "npc_teste", "unica"))
    check("cena inexistente recusada", any("Cena" in e for e in erros))
    erros.clear()
    asyncio.run(sala.handle_scene_npc("p1", "provas", "npc_fantasma", "unica"))
    check("npc inexistente recusado", any("Frequentador" in e for e in erros))
    del S.CITY_SCENES["alva_e_luz"]["provas"]

    print("\n[11] Migração das chaves de savegame")
    check("chave antiga de 3 partes ganha 'taverna'",
          S._migrar_chaves_conversa(["alva_e_luz:barman:inicial"])
          == {"alva_e_luz:taverna:barman:inicial"})
    check("chave nova de 4 partes fica intacta",
          S._migrar_chaves_conversa(["alva_e_luz:docas:npc_x:y"])
          == {"alva_e_luz:docas:npc_x:y"})
    check("lixo é descartado",
          S._migrar_chaves_conversa(["", "a:b", 42, None]) == set())
    check("lista vazia e None viram conjunto vazio",
          S._migrar_chaves_conversa([]) == set() and S._migrar_chaves_conversa(None) == set())

    print("\n[12] Save do editor: cena órfã, ponto tipo cena e emoji")
    S._sincronizar_cidades_derivadas()
    cenas_editor = {"alva_e_luz": {"docas": {
        "nome": "Docas", "background": "assets/city/docas.png", "mode": "individual",
        "mask": "", "slots": [
            {"id": "npc_pescador", "name": "Pescador", "image": "assets/tavern/slots/barman.png",
             "x": 10, "y": 20, "w": 12, "h": 24, "z": 1, "dialog": "Olá.",
             "conversations": [{"id": "boato", "texto": "Luzes no farol.", "requisito": {},
                                "efeito": {"renome": 1, "fato": "farol", "item_id": ""},
                                "uma_vez": True}]}]}}}
    pontos_editor = {"alva_e_luz": dict(S.CITY_MAP_POINTS["alva_e_luz"], **{
        "docas": {"x": 18, "y": 72, "type": "cena", "emoji": "🌊",
                  "name": "Docas", "scene": "docas"}})}
    ok, cfg = S._save_city_shops_upload(S.CITY_SHOPS, cenas_editor, pontos_editor)
    check("save aceito", ok is True)
    check("cena gravada", "docas" in S.CITY_SCENES["alva_e_luz"])
    check("ponto tipo cena aceito",
          S.CITY_MAP_POINTS["alva_e_luz"]["docas"].get("type") == "cena")
    check("emoji preservado", S.CITY_MAP_POINTS["alva_e_luz"]["docas"].get("emoji") == "🌊")
    check("vinculo preservado", S.CITY_MAP_POINTS["alva_e_luz"]["docas"].get("scene") == "docas")
    # Cena ausente do envio seguinte = excluída pelo autor.
    S.CITY_SCENES["alva_e_luz"]["orfa"] = S._cena_vazia("Órfã")
    S.CITY_MAP_POINTS["alva_e_luz"]["docas"]["scene"] = "orfa"
    pontos_orfa = {"alva_e_luz": dict(S.CITY_MAP_POINTS["alva_e_luz"])}
    S._save_city_shops_upload(S.CITY_SHOPS, cenas_editor, pontos_orfa)
    check("cena ausente do envio é excluída", "orfa" not in S.CITY_SCENES["alva_e_luz"])
    check("ponto perde o vínculo com a cena excluída",
          S.CITY_MAP_POINTS["alva_e_luz"]["docas"].get("scene") != "orfa")
    S.CITY_MAP_POINTS["alva_e_luz"].pop("docas", None)
    S.CITY_SCENES["alva_e_luz"].pop("docas", None)

def main():
    restaurar = isolar_arquivos()
    try: _rodar_verificacoes()
    finally: restaurar()
    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    sys.exit(1 if FAIL else 0)

main()
