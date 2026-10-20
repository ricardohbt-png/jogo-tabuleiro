"""Velocidade do turno dos inimigos — servidor.

Roda da raiz:  python -X utf8 tools/test_velocidade_inimigos.py

REGRA
  • Quatro níveis: atual (padrão, nada muda), lento (3 s), muito_lento (6 s) e
    passo (espera o clique; só no Solo).
  • Só o anfitrião muda. O passo a passo é recusado fora do Solo.
  • A escolha vai nos dois payloads e no jogo salvo; a espera não é salva.
"""
import asyncio, os, sys
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


async def sala(solo=False):
    r = S.GameRoom("VELOC")
    r.players["p1"] = S.make_player("p1", "Ana", "warrior", 0)
    r.players["p2"] = S.make_player("p2", "Bia", "rogue", 1)
    r.phase = "city"; r.host_pid = "p1"
    r.erros = []
    async def send_to(pid, msg):
        if msg.get("type") == "error": r.erros.append(msg.get("msg"))
    async def push_state(): pass
    async def broadcast(msg, skip=None, personalize=None): pass
    async def broadcast_city_state(): pass
    r.send_to = send_to; r.push_state = push_state; r.broadcast = broadcast
    r.broadcast_city_state = broadcast_city_state
    r._jogo_salvo_solo = lambda: solo
    return r


async def main():
    print("\n[1] Padrão e constantes")
    r = await sala()
    check("sala nova começa em 'atual'", r.velocidade_inimigos == "atual")
    check("tempo automático começa desligado", r.ritmo_auto_segundos == 0)
    check("tempos dos níveis", S.RITMO_SEGUNDOS == {"lento": 3, "muito_lento": 6})
    check("teto de espera por clique é 90 s", S.RITMO_TETO_CLIQUE_S == 90)
    check("opções do tempo automático", S.RITMO_AUTO_OPCOES == (0, 3, 6, 10))
    check("os quatro níveis", S.RITMO_NIVEIS == ("atual", "lento", "muito_lento", "passo"))

    print("\n[2] Quem pode mudar")
    r = await sala()
    await r.handle_set_velocidade_inimigos("p2", "lento")
    check("jogador comum é recusado", r.velocidade_inimigos == "atual" and r.erros, r.erros)
    r.erros.clear()
    await r.handle_set_velocidade_inimigos("p1", "lento")
    check("anfitrião muda para lento", r.velocidade_inimigos == "lento" and not r.erros)
    await r.handle_set_velocidade_inimigos("p1", "muito_lento")
    check("anfitrião muda para muito lento", r.velocidade_inimigos == "muito_lento")
    r.erros.clear()
    await r.handle_set_velocidade_inimigos("p1", "turbo")
    check("nível inválido é recusado e não muda", r.velocidade_inimigos == "muito_lento" and r.erros)

    print("\n[3] Passo a passo só no Solo")
    r = await sala(solo=False)
    await r.handle_set_velocidade_inimigos("p1", "passo")
    check("multiplayer recusa o passo a passo", r.velocidade_inimigos == "atual" and r.erros, r.erros)
    r = await sala(solo=True)
    await r.handle_set_velocidade_inimigos("p1", "passo", 6)
    check("Solo aceita o passo a passo", r.velocidade_inimigos == "passo")
    check("Solo aceita tempo automático de 6 s", r.ritmo_auto_segundos == 6)
    await r.handle_set_velocidade_inimigos("p1", "passo", 7)
    check("tempo automático fora das opções vira 0", r.ritmo_auto_segundos == 0)
    await r.handle_set_velocidade_inimigos("p1", "lento", 10)
    check("fora do passo a passo o tempo automático é ignorado (0)", r.ritmo_auto_segundos == 0)

    print("\n[4] Payloads e jogo salvo")
    r = await sala(solo=True)
    r.phase = "playing"
    await r.handle_set_velocidade_inimigos("p1", "passo", 3)
    g = r._game_state_payload()
    check("vai no game_state", g.get("velocidade_inimigos") == "passo" and g.get("ritmo_auto_segundos") == 3, g.get("velocidade_inimigos"))
    r.savegame = {}
    r._checkpoint_savegame()
    check("vai para o jogo salvo", r.savegame.get("velocidade_inimigos") == "passo"
          and r.savegame.get("ritmo_auto_segundos") == 3)
    check("lê do jogo salvo", S._ritmo_de_save(r.savegame) == ("passo", 3))
    check("save antigo cai no padrão", S._ritmo_de_save({}) == ("atual", 0))
    check("save com valor ruim cai no padrão", S._ritmo_de_save({"velocidade_inimigos": "x", "ritmo_auto_segundos": 99}) == ("atual", 0))
    r2 = await sala(solo=True)
    r2.phase = "city"
    check("vai no city_state", r2._city_state_payload().get("velocidade_inimigos") == "atual")
    check("payloads dizem se o passo a passo é permitido (Solo)",
          r2._city_state_payload().get("ritmo_passo_permitido") is True
          and (await sala(solo=False))._game_state_payload().get("ritmo_passo_permitido") is False)

    print("\n[5] Mensagens da conexão e despacho")
    check("set_velocidade_inimigos fala pela conexão", "set_velocidade_inimigos" in S.MENSAGENS_DA_CONEXAO)
    check("continuar_turno_inimigo fala pela conexão", "continuar_turno_inimigo" in S.MENSAGENS_DA_CONEXAO)

    print("\n[6] Coletor de ataques do monstro")
    r = await sala()
    enviados = []
    async def bc(msg, skip=None, personalize=None): enviados.append(msg)
    r.broadcast = bc
    orc = {"id": "m1", "name": "Orc", "pos": [3, 3], "hp": 10}
    outro = {"id": "m2", "name": "Goblin", "pos": [4, 3], "hp": 5}
    ana = r.players["p1"]; ana.update({"hp": 20, "pos": [2, 3]})
    bia = r.players["p2"]; bia.update({"hp": 15, "pos": [2, 4]})

    await r._emitir_feedback_ataque("start", orc, ana, "Machado", "normal", impacto="cortante")
    check("sem coletor nada é registrado e o feedback sai igual",
          r._ritmo_coletor is None and enviados[-1]["phase"] == "start"
          and enviados[-1]["attack_name"] == "Machado" and enviados[-1]["impacto"] == "cortante")

    r._ritmo_iniciar(orc)
    check("coletor guarda o id do monstro", r._ritmo_coletor["monstro_id"] == "m1")
    aid = await r._emitir_feedback_ataque("start", orc, ana, "Machado", "normal", impacto="cortante")
    await r._emitir_feedback_ataque("result", orc, ana, "Machado", "normal", attack_id=aid,
                                    roll=14, total=18, hit=True, crit=False)
    ana["hp"] = 15
    aid2 = await r._emitir_feedback_ataque("start", orc, bia, "Pancada", "normal")
    await r._emitir_feedback_ataque("result", orc, bia, "Pancada", "normal", attack_id=aid2,
                                    roll=3, total=7, hit=False, crit=False)
    # alvo sem id (área) e outro atacante não entram
    await r._emitir_feedback_ataque("start", orc, {"id": None, "pos": [1, 1]}, "Sopro", "normal")
    await r._emitir_feedback_ataque("start", outro, ana, "Mordida", "normal")
    bia["hp"] = 15
    ent = r._ritmo_finalizar()
    check("duas entradas (área e outro monstro ficam de fora)", len(ent) == 2, ent)
    e1, e2 = ent[0], ent[1]
    check("1º ataque: alvo, nome, tipo", e1["alvo_nome"] == "Ana" and e1["ataque"] == "Machado"
          and e1["impacto"] == "cortante")
    check("1º ataque: acertou, rolagem e total", e1["acertou"] is True and e1["critico"] is False
          and e1["rolagem"] == 14 and e1["total"] == 18)
    check("1º ataque: dano = PV perdidos até o próximo ataque", e1["dano"] == 5, e1)
    check("2º ataque errou e não causou dano (fecha no fim do turno)",
          e2["acertou"] is False and e2["dano"] == 0 and e2["alvo_nome"] == "Bia", e2)
    check("entrada traz o dono do alvo", e1["alvo_pid"] == "p1" and e2["alvo_pid"] == "p2")
    check("finalizar zera o coletor", r._ritmo_coletor is None)

    r._ritmo_iniciar(orc)
    aid = await r._emitir_feedback_ataque("start", orc, ana, "Machado", "normal")
    await r._emitir_feedback_ataque("result", orc, ana, "Machado", "normal", attack_id=aid, hit=True, crit=True, roll=20, total=25)
    ana["hp"] = 0
    ent = r._ritmo_finalizar()
    check("dano de ataque que mata não passa dos PV que o alvo tinha", ent[0]["dano"] == 15 and ent[0]["critico"] is True, ent)
    check("sem ataque o coletor devolve lista vazia", (r._ritmo_iniciar(orc), r._ritmo_finalizar())[1] == [])

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    return FAIL


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
