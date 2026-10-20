"""Velocidade do turno dos inimigos — ritmo na fila de iniciativa.

Roda da raiz:  python -X utf8 tools/test_velocidade_inimigos_fila.py

REGRA
  • Nível 'atual': nada novo é enviado nem esperado.
  • Lento / muito lento: depois de um monstro que ATACOU, uma faixa de resumo e
    uma espera por tempo antes de a iniciativa avançar.
  • Passo a passo (Solo): a espera termina no clique, no tempo automático, no
    teto de segurança, na queda do jogador ou na troca de nível.
  • Monstro dormente, que só andou ou sob controle manual não entra no ritmo.
  • Monstro fora da visão: faixa genérica, só para o dono do alvo.
  • Falha na espera nunca congela a iniciativa.
"""
import asyncio, contextlib, io, os, sys, time
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


async def fila(nivel="atual", solo=False, auto=0, ataques=(("p1", True, 4),), vistos=True):
    """Sala com um orc (m1) na vez, depois a Ana (p1). `ataques`: (alvo, acertou, dano)
    que o `gm_phase` falso executa. Devolve (sala, registro de eventos)."""
    r = S.GameRoom("RITMO")
    r.players["p1"] = S.make_player("p1", "Ana", "warrior", 0)
    r.players["p2"] = S.make_player("p2", "Bia", "rogue", 1)
    r.host_pid = "p1"; r.phase = "playing"
    r._jogo_salvo_solo = lambda: solo
    r.velocidade_inimigos = nivel; r.ritmo_auto_segundos = auto
    r.connections = {"p1": object(), "p2": object()}
    r.monsters = {"m1": {"id": "m1", "name": "Orc", "type": "orc", "pos": [3, 3], "hp": 10, "max_hp": 10}}
    r.players["p1"].update({"hp": 20, "alive": True, "connected": True, "pos": [3, 4] if vistos else [30, 30]})
    r.players["p2"].update({"hp": 20, "alive": True, "connected": True, "pos": [3, 5] if vistos else [31, 31]})
    r.initiative_active = True
    r.initiative_order = [{"kind": "monster", "id": "m1", "initiative": 12},
                          {"kind": "player", "id": "p1", "initiative": 5}]
    r.initiative_index = 0
    r._intro_masmorra_bloqueada = lambda: False
    r._heroi_enxerga_monstro = lambda h, m: vistos
    ev = {"enviados": [], "avancos": 0, "ordem": []}
    async def bc(msg, skip=None, personalize=None):
        por_pid = {pid: (personalize(pid, msg) if personalize else msg) for pid in r.connections}
        ev["enviados"].append((msg["type"], por_pid))
        ev["ordem"].append(msg["type"])
    async def avancar():
        ev["avancos"] += 1; ev["ordem"].append("avancou")
    async def send_to(pid, msg): pass
    async def push_state(): pass
    async def gm_phase(m=None):
        for alvo, acertou, dano in ataques:
            a = r.players[alvo]
            aid = await r._emitir_feedback_ataque("start", m, a, "Machado", "normal", impacto="cortante")
            await r._emitir_feedback_ataque("result", m, a, "Machado", "normal", attack_id=aid,
                                            roll=12, total=16, hit=acertou, crit=False)
            if acertou: a["hp"] -= dano
    r.broadcast = bc; r._advance_initiative = avancar; r.gm_phase = gm_phase
    r.send_to = send_to; r.push_state = push_state
    return r, ev


async def rodar_turno(r):
    await r._activate_initiative_actor()
    await r.initiative_task


def tipos(ev, tipo):
    return [e for e in ev["enviados"] if e[0] == tipo]


async def main():
    S.RITMO_SEGUNDOS = {"lento": 0.15, "muito_lento": 0.3}
    S.RITMO_TETO_CLIQUE_S = 0.5

    print("\n[1] Nível atual: nada novo")
    r, ev = await fila("atual")
    await rodar_turno(r)
    check("não envia marca nem faixa", not tipos(ev, "turno_inimigo_agindo") and not tipos(ev, "resumo_ataque_inimigo"))
    check("avança a iniciativa uma vez", ev["avancos"] == 1)
    check("sem coletor sobrando", r._ritmo_coletor is None)

    print("\n[2] Lento e muito lento")
    r, ev = await fila("lento")
    t0 = time.monotonic(); await rodar_turno(r); dt = time.monotonic() - t0
    check("espera o tempo do nível antes de avançar", dt >= 0.14, dt)
    o = ev["ordem"]
    check("ordem: marca, faixa, fechada, avança",
          o[:1] == ["turno_inimigo_agindo"] and "resumo_ataque_inimigo" in o
          and o.index("resumo_ataque_inimigo") < o.index("resumo_inimigo_fechado") < o.index("avancou"), o)
    res = tipos(ev, "resumo_ataque_inimigo")[0][1]["p1"]
    check("faixa completa: monstro, ataque, acerto, dano e tipo",
          res["generico"] is False and str(res["atacante_nome"]) == "Orc"
          and res["ataques"][0]["ataque"] == "Machado" and res["ataques"][0]["acertou"] is True
          and res["ataques"][0]["dano"] == 4 and res["ataques"][0]["impacto"] == "cortante", res)
    check("espera é por tempo", res["espera"] == "tempo" and res["segundos"] == 0.15, res)
    ag = tipos(ev, "turno_inimigo_agindo")
    check("anel acende no monstro e apaga no fim",
          ag[0][1]["p1"]["monstro_id"] == "m1" and ag[-1][1]["p1"]["monstro_id"] is None)
    check("o tracejado lista só monstros que ainda vão agir", ag[0][1]["p1"]["proximos"] == [], ag[0][1]["p1"])
    check("o anel fica aceso durante a faixa e só apaga depois dela",
          o.index("resumo_ataque_inimigo") < o.index("resumo_inimigo_fechado")
          < len(o) - 1 - o[::-1].index("turno_inimigo_agindo") < o.index("avancou"), o)
    r, ev = await fila("muito_lento")
    t0 = time.monotonic(); await rodar_turno(r); dt = time.monotonic() - t0
    check("muito lento espera mais", dt >= 0.29, dt)

    print("\n[3] Só andou / dormente / morto / fim de jogo")
    r, ev = await fila("lento", ataques=())
    t0 = time.monotonic(); await rodar_turno(r); dt = time.monotonic() - t0
    check("monstro que só andou: sem faixa e sem espera", not tipos(ev, "resumo_ataque_inimigo") and dt < 0.1, dt)
    check("mas o anel apareceu e apagou", len(tipos(ev, "turno_inimigo_agindo")) == 2)
    r, ev = await fila("lento")
    r._monstro_ativo_em_combate = lambda m: False
    await rodar_turno(r)
    check("monstro dormente: nenhuma mensagem de ritmo e avança",
          not tipos(ev, "turno_inimigo_agindo") and not tipos(ev, "resumo_ataque_inimigo") and ev["avancos"] == 1)
    r, ev = await fila("lento")
    async def gm_morre(m=None):
        a = r.players["p1"]
        aid = await r._emitir_feedback_ataque("start", m, a, "Machado", "normal")
        await r._emitir_feedback_ataque("result", m, a, "Machado", "normal", attack_id=aid, roll=15, total=19, hit=True, crit=False)
        a["hp"] -= 3; m["hp"] = 0
    r.gm_phase = gm_morre
    await rodar_turno(r)
    check("monstro que morre no próprio turno ainda mostra o que fez", len(tipos(ev, "resumo_ataque_inimigo")) == 1)
    r, ev = await fila("lento")
    base = r.gm_phase
    async def gm_fim(m=None):
        await base(m)
        r.phase = "ended"
    r.gm_phase = gm_fim
    t0 = time.monotonic(); await rodar_turno(r); dt = time.monotonic() - t0
    check("fim de jogo no turno: sem faixa e sem espera", not tipos(ev, "resumo_ataque_inimigo") and dt < 0.1, dt)

    print("\n[4] Passo a passo")
    r, ev = await fila("passo", solo=True)
    task = asyncio.create_task(rodar_turno(r))
    await asyncio.sleep(0.05)
    check("espera o clique (ainda não avançou)", ev["avancos"] == 0 and r._ritmo_evento is not None)
    res = tipos(ev, "resumo_ataque_inimigo")[0][1]["p1"]
    check("faixa pede clique", res["espera"] == "clique" and res["segundos"] == 0, res)
    await r.handle_continuar_turno_inimigo("p1")
    await task
    check("clique libera e avança", ev["avancos"] == 1 and r._ritmo_evento is None)
    r, ev = await fila("passo", solo=True)
    t0 = time.monotonic(); await rodar_turno(r); dt = time.monotonic() - t0
    check("sem clique, o teto de espera libera", 0.45 <= dt < 1.0 and ev["avancos"] == 1, dt)
    r, ev = await fila("passo", solo=True)
    r.ritmo_auto_segundos = 0.1   # tempo automático curto só para o teste
    t0 = time.monotonic(); await rodar_turno(r); dt = time.monotonic() - t0
    res = tipos(ev, "resumo_ataque_inimigo")[0][1]["p1"]
    check("tempo automático fecha antes do teto", dt < 0.4 and res["segundos"] == 0.1, (dt, res))
    r, ev = await fila("passo", solo=True)
    task = asyncio.create_task(rodar_turno(r)); await asyncio.sleep(0.05)
    await r.handle_continuar_turno_inimigo("intruso")
    check("clique de quem não está na sala é ignorado", ev["avancos"] == 0)
    await r.handle_disconnect_em_jogo("p1")
    await asyncio.wait_for(task, 0.3)
    check("queda do jogador solta a espera na hora", ev["avancos"] == 1)
    r, ev = await fila("lento")
    task = asyncio.create_task(rodar_turno(r)); await asyncio.sleep(0.05)
    await r.handle_continuar_turno_inimigo("p1")
    check("clique é ignorado fora do passo a passo", ev["avancos"] == 0)
    await r.handle_set_velocidade_inimigos("p1", "atual")
    await asyncio.wait_for(task, 0.3)
    check("trocar o nível solta a espera", ev["avancos"] == 1)

    print("\n[5] Falha na espera não congela a iniciativa")
    r, ev = await fila("lento")
    async def quebra(mid): raise RuntimeError("boom")
    r._ritmo_depois = quebra
    with contextlib.redirect_stderr(io.StringIO()):
        await rodar_turno(r)
    check("a iniciativa avança mesmo assim", ev["avancos"] == 1)
    check("e o anel não fica preso aceso", tipos(ev, "turno_inimigo_agindo")[-1][1]["p1"]["monstro_id"] is None)

    print("\n[6] Visibilidade")
    r, ev = await fila("lento", vistos=False)
    await rodar_turno(r)
    res = tipos(ev, "resumo_ataque_inimigo")[0][1]
    check("alvo do jogador, monstro não visto: faixa genérica sem nome nem habilidade",
          res["p1"]["generico"] is True and res["p1"]["atacante_nome"] is None
          and res["p1"]["ataques"][0]["ataque"] is None and res["p1"]["ataques"][0]["alvo_nome"] == "Ana"
          and res["p1"]["ataques"][0]["dano"] == 4, res["p1"])
    check("quem não é o alvo e não vê o monstro não recebe faixa", res["p2"] is None, res["p2"])
    ag = tipos(ev, "turno_inimigo_agindo")[0][1]
    check("sem visão, o anel não aponta o monstro", ag["p1"]["monstro_id"] is None)
    r, ev = await fila("lento", vistos=False)
    r.master_pid = "p2"
    r.monsters["m1"]["alertado"] = True
    await rodar_turno(r)
    res = tipos(ev, "resumo_ataque_inimigo")[0][1]
    check("o Mestre vê tudo", res["p2"]["generico"] is False and str(res["p2"]["atacante_nome"]) == "Orc")

    print("\n[7] Controle manual não entra no ritmo")
    r, ev = await fila("lento")
    r.monsters["m1"]["comando_pendente_pid"] = "p1"
    check("Comando pendente fica de fora", r._ritmo_ativo_para(r.monsters["m1"]) is False)
    r.monsters["m1"].pop("comando_pendente_pid")
    r._mestre_ativo = lambda: True
    r.monsters["m1"].update({"control_mode": "manual", "alertado": True})
    check("modo Manual do Mestre fica de fora", r._ritmo_ativo_para(r.monsters["m1"]) is False)
    r.monsters["m1"]["control_mode"] = "auto"
    check("auto do Mestre entra", r._ritmo_ativo_para(r.monsters["m1"]) is True)

    print(f"\n=== {PASS} passaram, {FAIL} falharam ===")
    return FAIL


if __name__ == "__main__":
    sys.exit(1 if asyncio.run(main()) else 0)
