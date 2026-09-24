"""Teste rápido da Tempestade de Ciclones em modo de protótipo."""
import asyncio, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import server as S

PASS = FAIL = 0
def check(label, value):
    global PASS, FAIL
    if value: PASS += 1; print(f"  ✅ {label}")
    else: FAIL += 1; print(f"  ❌ {label}")

def setup(level=5):
    r = S.GameRoom("TEST")
    r.events = []
    async def noop(*a, **k): pass
    async def send_to(*a, **k):
        if len(a) >= 2 and isinstance(a[1], dict):
            r.events.append(a[1])
    r.broadcast = noop; r.push_state = noop; r.gm_say = noop; r._broadcast_dado = noop; r.send_to = send_to
    r._tem_linha_de_visao = lambda *a, **k: True
    r._alcance_com_altura = lambda *a, **k: True
    r.map_w = r.map_h = 12
    r.tiles = [[S.FLOOR] * 12 for _ in range(12)]
    r.explored = {(x, y) for y in range(12) for x in range(12)}
    r.phase = "playing"; r.round_num = 1; r.monsters = {}; r.decorations = []
    r._rebuild_decor_index(); r.materiais = {}; r._rebuild_materiais_index()
    p = S.make_player("c", "Lewis", "cleric", 0)
    p.update(level=level, pos=[5, 5], alive=True, hp=100, max_hp=100,
             fome=50, sede=50, action_done=False, moves_left=6)
    p["magias_conhecidas"] = ["tempestade_ciclones"]
    r.players["c"] = p; r.player_order = ["c"]; r.initiative_active = True; r._rebuild_initiative()
    return r, p

async def main():
    r, p = setup(5)
    await r.handle_magia("c", {"magia_id":"tempestade_ciclones", "tx":5, "ty":5})
    z = next((z for z in r.zonas_especiais if z.get("tipo")=="tempestade_ciclones"), None)
    check("zona criada no nível 5", bool(z))
    check("área 4x4 no nível 5", z and z.get("lado") == 4 and len(z.get("tiles", [])) == 16)
    check("estágios de dano vêm do catálogo",
          z and z.get("dano_inicial") == "2d8" and z.get("dano_raio") == "1d8"
          and z.get("dano_ciclone") == "1d8")
    rolagem = z.get("ciclones_rolados", 0) if z else 0
    check("rola 2d4 ciclones", z and 2 <= rolagem <= 8 and z.get("ciclones_pendentes") == rolagem)
    check("pede a escolha das posições iniciais", any(e.get("type") == "tempestade_ciclones_prompt" and e.get("count") == rolagem for e in r.events))
    check("prompt informa o tamanho do ciclone", any(e.get("type") == "tempestade_ciclones_prompt" and e.get("ciclone_lado") == 1 for e in r.events))
    check("zona pendente não impõe vento", r._water_step_cost(p, 5, 6, [5, 5]) == 1)
    check("duração não começa antes da confirmação", z.get("expira_em") is None and z.get("proxima_descarga") is None)
    await r.handle_end_turn("c")
    check("não encerra o turno com posicionamento pendente",
          any(e.get("type") == "error" and "posições dos ciclones" in e.get("msg", "") for e in r.events))
    posicoes = [list(pos) for pos in z.get("tiles", [])[:rolagem]]
    await r.handle_tempestade_ciclones_posicoes("c", z["id"], posicoes)
    check("posições iniciais confirmadas", z.get("ciclones_pendentes") is None and len(z.get("ciclones", [])) == rolagem)
    check("duração começa na confirmação", z.get("expira_em") == r.round_num + z.get("duracao", 0))
    check("ciclones ocupam 1x1", z and all(len(r._tempestade_ciclone_tiles(c)) == 1 for c in z["ciclones"]))
    check("posições iniciais são únicas", len({tuple(c["pos"]) for c in z["ciclones"]}) == rolagem)
    check("vento custa 2", r._water_step_cost(p, 5, 6, [5, 5]) == 2)
    old = list(z["ciclones"][0]["pos"])
    ocupadas = {tuple(c["pos"]) for c in z["ciclones"]}
    destino = next(([x, y] for x, y in z["tiles"]
                    if (x, y) not in ocupadas
                    and max(abs(x - old[0]), abs(y - old[1])) <= 2), None)
    await r.handle_tempestade_ciclones_mover("c", z["id"], 1, destino)
    check("ciclone pode mover 2 casas no turno da conjuração", z["ciclones"][0]["pos"] != old)
    # O movimento é autoritativo: ids/posições malformados e colisões não
    # podem derrubar o handler nem alterar o estado do ciclone.
    r.round_num = 2
    antes_colisao = list(z["ciclones"][1]["pos"])
    await r.handle_tempestade_ciclones_mover("c", z["id"], "invalido", destino)
    check("id inválido do ciclone não quebra o servidor", any(e.get("type") == "error" for e in r.events))
    await r.handle_tempestade_ciclones_mover("c", z["id"], 2, z["ciclones"][0]["pos"])
    check("ciclones não podem ocupar a mesma casa", z["ciclones"][1]["pos"] == antes_colisao)
    r.round_num = 3
    await r._processar_zonas_turno()
    check("raio periódico agendado para a rodada 3", z.get("proxima_descarga") == 5)

    descargas = []
    async def registrar_descarga(zona):
        descargas.append(zona.get("id"))
    r._tempestade_descarga = registrar_descarga
    p["tempestade_ciclones_presos"] = {str(z.get("id")): 1, "zona-que-sobrevive": 2}
    z["expira_em"] = z["proxima_descarga"] = 4
    r.round_num = 4
    await r._processar_zonas_turno()
    check("raio acontece antes da expiração na mesma rodada", descargas == [z.get("id")])
    check("zona expira depois do raio final", z.get("ativa") is False)
    check("expiração limpa apenas a origem da zona", p.get("tempestade_ciclones_presos") == {"zona-que-sobrevive": 2})

    # O cooldown do ciclone precisa distinguir o namespace do alvo. Também não
    # pode cancelar o dano só porque o teste de voo já marcou uma queda.
    efeitos, ep = setup(5)
    await efeitos.handle_magia("c", {"magia_id": "tempestade_ciclones", "tx": 5, "ty": 5})
    ze = next(z for z in efeitos.zonas_especiais if z.get("tipo") == "tempestade_ciclones")
    quantidade_efeitos = int(ze.get("ciclones_pendentes", 0) or 0)
    await efeitos.handle_tempestade_ciclones_posicoes("c", ze["id"], [list(pos) for pos in ze["tiles"][:quantidade_efeitos]])
    ze["ciclones"][0]["pos"] = list(ep["pos"])
    monstro = {"id": "c", "pos": list(ep["pos"]), "hp": 100, "max_hp": 100, "size": [1, 1]}
    efeitos.monsters["m"] = monstro
    async def dano_teste(*args, **kwargs):
        return True
    async def aviso_teste(*args, **kwargs):
        return None
    efeitos._tempestade_dano = dano_teste
    efeitos._tempestade_notificar_alvo_ciclone = aviso_teste
    ze["quedas_tempestade_rodada"]["player:c"] = efeitos.round_num
    await efeitos._tempestade_aplicar_ciclone(ep, ze)
    await efeitos._tempestade_aplicar_ciclone(monstro, ze)
    check("cooldown do ciclone separa jogador e monstro com mesmo id",
          set(ze.get("alvos_ciclone_rodada", {})) == {"player:c", "monster:c"})

    parser, alvo_parser = setup(5)
    dados_parser = []
    dano_parser = []
    async def rolar_parser(n, faces, label, damage_type=None):
        dados_parser.append((n, faces, label))
        return 10
    async def save_parser(*args, **kwargs):
        return True, 10, 0, 10
    async def aplicar_parser(alvo, dano, elemento, *args, **kwargs):
        dano_parser.append((dano, elemento))
    parser._rolar_dano_mostrado = rolar_parser
    parser._save_mostrado = save_parser
    parser._dano_em_alvo = aplicar_parser
    await parser._tempestade_dano(alvo_parser, "3d6+2", S.DMG_LIGHTNING,
                                   "reflexos", 12, 1, "teste")
    check("dano da tempestade interpreta expressões configuráveis",
          dados_parser and dados_parser[0][:2] == (3, 6)
          and dano_parser == [(6, S.DMG_LIGHTNING)])

    defesa, alvo_defesa = setup(5)
    await defesa.handle_magia("c", {"magia_id": "tempestade_ciclones", "tx": 5, "ty": 5})
    zd = next(z for z in defesa.zonas_especiais if z.get("tipo") == "tempestade_ciclones")
    qd = int(zd.get("ciclones_pendentes", 0) or 0)
    await defesa.handle_tempestade_ciclones_posicoes("c", zd["id"], [list(pos) for pos in zd["tiles"][:qd]])
    zd["ciclones"][0]["pos"] = list(alvo_defesa["pos"])
    rolagem_defesa = []
    save_passou = {"value": False}
    async def rolar_defesa(n, faces, label, damage_type=None):
        rolagem_defesa.append((n, faces))
        return 8
    async def save_defesa(*args, **kwargs):
        ok = save_passou["value"]
        return ok, 10, 0, 10
    defesa._rolar_dano_mostrado = rolar_defesa
    defesa._save_mostrado = save_defesa
    imune = {"id": "imune", "pos": list(alvo_defesa["pos"]), "hp": 100,
             "max_hp": 100, "immunities": [S.DMG_PHYSICAL]}
    resistente = {"id": "resistente", "pos": list(alvo_defesa["pos"]), "hp": 100,
                  "max_hp": 100, "resistances": [{"type": S.DMG_PHYSICAL, "reduction": 2}]}
    defesa.monsters["imune"] = imune
    defesa.monsters["resistente"] = resistente
    await defesa._tempestade_aplicar_ciclone(imune, zd)
    await defesa._tempestade_aplicar_ciclone(resistente, zd)
    check("imunidade física zera o dano, mas não duplica a condição do ciclone",
          imune["hp"] == 100 and imune.get("turbilhao_perde_movimento")
          and imune.get("turbilhao_perde_acao"))
    check("resistência física é aplicada uma única vez",
          resistente["hp"] == 94 and rolagem_defesa[:2] == [(1, 8), (1, 8)])
    check("prisão registra a zona e o ciclone de origem",
          resistente.get("tempestade_ciclones_presos", {}).get(str(zd["id"])) == zd["ciclones"][0]["id"])
    zona_sobreposta = {"id": "zona-sobreposta"}
    ciclone_sobreposto = {"id": 99}
    defesa._tempestade_registrar_prisao(resistente, zona_sobreposta, ciclone_sobreposto, True)
    check("prisões de zonas sobrepostas mantêm origens separadas",
          resistente.get("tempestade_ciclones_presos") ==
          {str(zd["id"]): zd["ciclones"][0]["id"], "zona-sobreposta": 99})
    defesa._tempestade_registrar_prisao(resistente, zd, zd["ciclones"][0], False)
    check("liberar uma zona não remove a prisão da outra",
          resistente.get("tempestade_ciclones_presos") == {"zona-sobreposta": 99})
    defesa._limpar_tempestade_ciclones_presos(resistente)
    check("consumir a condição limpa as origens da prisão",
          "tempestade_ciclones_presos" not in resistente)
    save_passou["value"] = True
    resistente["id"] = "resistente-save"
    defesa.monsters["resistente-save"] = resistente
    await defesa._tempestade_aplicar_ciclone(resistente, zd)
    check("Reflexos reduz antes da resistência", resistente["hp"] == 92)

    morto, alvo_morto = setup(5)
    await morto.handle_magia("c", {"magia_id": "tempestade_ciclones", "tx": 5, "ty": 5})
    zm = next(z for z in morto.zonas_especiais if z.get("tipo") == "tempestade_ciclones")
    qm = int(zm.get("ciclones_pendentes", 0) or 0)
    await morto.handle_tempestade_ciclones_posicoes("c", zm["id"], [list(pos) for pos in zm["tiles"][:qm]])
    zm["ciclones"][0]["pos"] = list(alvo_morto["pos"])
    alvo_morto.pop("turbilhao_perde_movimento", None)
    alvo_morto.pop("turbilhao_perde_acao", None)
    async def dano_mortal(alvo, *args, **kwargs):
        alvo["hp"] = 0
        return False
    morto._tempestade_dano = dano_mortal
    morto._tempestade_notificar_alvo_ciclone = aviso_teste
    await morto._tempestade_aplicar_ciclone(alvo_morto, zm)
    check("alvo morto não recebe perda de movimento nem de ação",
          not alvo_morto.get("turbilhao_perde_movimento")
          and not alvo_morto.get("turbilhao_perde_acao"))

    entrada, _ = setup(5)
    await entrada.handle_magia("c", {"magia_id": "tempestade_ciclones", "tx": 5, "ty": 5})
    zi = next(z for z in entrada.zonas_especiais if z.get("tipo") == "tempestade_ciclones")
    qi = int(zi.get("ciclones_pendentes", 0) or 0)
    await entrada.handle_tempestade_ciclones_posicoes("c", zi["id"], [list(pos) for pos in zi["tiles"][:qi]])
    grande = {"id": "grande", "pos": [4, 5], "hp": 100, "max_hp": 100,
              "size": [2, 2], "voo": True, "altura": 2, "altura_max": 3}
    entrada.monsters["grande"] = grande
    testes_voo = []
    async def registrar_voo(*args, **kwargs):
        testes_voo.append(args[2] if len(args) > 2 else kwargs.get("motivo"))
        return False
    async def ignorar_ciclone(*args, **kwargs):
        return None
    entrada._tempestade_testar_voo = registrar_voo
    entrada._tempestade_aplicar_ciclone = ignorar_ciclone
    # O footprint antigo [3..4] já tocava a tempestade; mover a âncora para
    # [4..5] não é uma nova entrada para um monstro 2x2.
    await entrada._tempestade_verificar_entrada(grande, [3, 5], [4, 5])
    check("monstro grande parcialmente dentro não repete entrada", not testes_voo)
    grande["pos"] = [3, 5]
    await entrada._tempestade_verificar_entrada(grande, [2, 5], [3, 5])
    check("monstro grande testa voo ao cruzar a borda", testes_voo == ["entrada"])

    custo, _ = setup(5)
    await custo.handle_magia("c", {"magia_id": "tempestade_ciclones", "tx": 5, "ty": 5})
    zcusto = next(z for z in custo.zonas_especiais if z.get("tipo") == "tempestade_ciclones")
    qcusto = int(zcusto.get("ciclones_pendentes", 0) or 0)
    await custo.handle_tempestade_ciclones_posicoes("c", zcusto["id"], [list(pos) for pos in zcusto["tiles"][:qcusto]])
    grande_custo = {"id": "grande-custo", "pos": [2, 5], "hp": 100,
                    "max_hp": 100, "size": [2, 2]}
    custo.monsters["grande-custo"] = grande_custo
    check("vento considera o footprint inteiro do monstro grande",
          custo._water_step_cost(grande_custo, 3, 5, [2, 5]) == 2)

    # O teste de voo deve acontecer no máximo uma vez por alvo/zona/rodada,
    # mesmo quando os três gatilhos (entrada, início do turno e raio) ocorrem
    # na mesma rodada. Uma rodada nova libera exatamente um novo teste.
    voo, _ = setup(5)
    voador = {"id": "voador", "pos": [5, 5], "hp": 100,
              "max_hp": 100, "voo": True, "altura": 2, "altura_max": 3}
    voo.monsters["voador"] = voador
    zona_voo = {"id": "zona-voo", "caster": "c", "save_dif": 13,
                "quedas_tempestade_rodada": {}}
    saves_voo = []
    async def save_voo(*args, **kwargs):
        saves_voo.append(voo.round_num)
        return True, 15, 0, 15
    async def queda_voo(*args, **kwargs):
        return None
    voo._save_mostrado = save_voo
    voo._aplicar_queda = queda_voo
    await voo._tempestade_testar_voo(voador, zona_voo, "entrada")
    await voo._tempestade_testar_voo(voador, zona_voo, "inicio")
    await voo._tempestade_testar_voo(voador, zona_voo, "raio")
    check("voo passa uma única vez por rodada",
          saves_voo == [voo.round_num]
          and zona_voo.get("testes_voo_tempestade_rodada", {}).get("monster:voador") == voo.round_num)
    voo.round_num += 1
    await voo._tempestade_testar_voo(voador, zona_voo, "inicio")
    check("voo pode ser testado novamente na rodada seguinte", saves_voo == [1, 2])

    # A validação autoritativa do movimento também deve respeitar o footprint
    # completo quando o ciclone configurado é maior que 1x1.
    grande_ciclone, _ = setup(5)
    zona_grande = {"id": "zona-grande", "tipo": "tempestade_ciclones",
                   "ativa": True, "caster": "c", "tiles":
                   [[x, y] for y in range(3) for x in range(3)],
                   "ciclone_movimento": 2,
                   "ciclones": [{"id": 1, "pos": [0, 0], "lado": 2,
                                 "movido_em": None}]}
    grande_ciclone.zonas_especiais.append(zona_grande)
    await grande_ciclone.handle_tempestade_ciclones_mover("c", "zona-grande", 1, [2, 1])
    check("movimento respeita o footprint completo do ciclone",
          zona_grande["ciclones"][0]["pos"] == [0, 0])

    # O movimento do ciclone pertence ao turno principal do clérigo, não às
    # janelas transitórias de controle de servos ou Último Esforço.
    janela, _ = setup(5)
    await janela.handle_magia("c", {"magia_id": "tempestade_ciclones", "tx": 5, "ty": 5})
    zj = next(z for z in janela.zonas_especiais if z.get("tipo") == "tempestade_ciclones")
    qj = int(zj.get("ciclones_pendentes", 0) or 0)
    await janela.handle_tempestade_ciclones_posicoes("c", zj["id"],
        [list(pos) for pos in zj["tiles"][:qj]])
    cj = zj["ciclones"][0]
    destino_janela = next(([x, y] for x, y in zj["tiles"]
                           if [x, y] != cj["pos"]
                           and max(abs(x-cj["pos"][0]), abs(y-cj["pos"][1])) <= 2
                           and all([x, y] != o["pos"] for o in zj["ciclones"])), None)
    antes_janela = list(cj["pos"])
    janela.animados_phase_pid = "c"
    await janela.handle_tempestade_ciclones_mover("c", zj["id"], cj["id"], destino_janela)
    check("ciclone não se move durante a fase dos servos", cj["pos"] == antes_janela)
    janela.animados_phase_pid = None
    janela.last_stand_pid = "c"
    await janela.handle_tempestade_ciclones_mover("c", zj["id"], cj["id"], destino_janela)
    check("ciclone não se move durante o Último Esforço", cj["pos"] == antes_janela)

    janela.last_stand_pid = None
    janela.players["c"]["alive"] = False
    await janela.handle_tempestade_ciclones_mover("c", zj["id"], cj["id"], destino_janela)
    check("ciclone não se move após a morte do conjurador", cj["pos"] == antes_janela)
    janela.players["c"]["alive"] = True
    janela.players["c"]["connected"] = False
    await janela.handle_tempestade_ciclones_mover("c", zj["id"], cj["id"], destino_janela)
    check("ciclone não se move após desconexão do conjurador", cj["pos"] == antes_janela)

    cancelada, _ = setup(5)
    await cancelada.handle_magia("c", {"magia_id": "tempestade_ciclones", "tx": 5, "ty": 5})
    zc = next(z for z in cancelada.zonas_especiais if z.get("tipo") == "tempestade_ciclones")
    await cancelada._cancelar_tempestades_pendentes("c")
    check("prévia pendente é cancelável sem deixar zona fantasma", zc.get("ativa") is False)

    invalida, pi = setup(5)
    await invalida.handle_magia("c", {"magia_id": "tempestade_ciclones", "tx": -1, "ty": -1})
    check("mira inválida não cria zona", not invalida.zonas_especiais)
    check("mira inválida não consome a ação", pi.get("action_done") is False)
    print(f"\n{PASS} passaram, {FAIL} falharam")
    return 1 if FAIL else 0

sys.exit(asyncio.run(main()))
