"""Ferramenta de DESENVOLVIMENTO: leva um jogo salvo a um ponto da campanha "O Resgate de Elara".

Para testar a campanha sem refazer as etapas anteriores. Reescreve só o estado da campanha de Elara no jogo
salvo (fatos `elara_*`, progresso dos destinos `elara_*`, conversas `elara_*` já usadas e o relógio): o resto
do jogo (heróis, ouro, itens, fatos de outras campanhas) fica como está.

Pare o servidor ANTES (ele regrava o jogo salvo a cada checkpoint) e suba de novo depois; entre pelo "Continuar".

    python tools/dev_elara_fatos.py --listar
    python tools/dev_elara_fatos.py --jogo sg_ab12cd --ate rumo --ramo a --bardo gentil
    python tools/dev_elara_fatos.py --jogo sg_ab12cd --ate cais --ramo a --lento --limpar-foto
    python tools/dev_elara_fatos.py --jogo sg_ab12cd --ate praca --ramo b
    python tools/dev_elara_fatos.py --jogo sg_ab12cd --ate inicio      # zera a campanha de Elara

Pontos (`--ate`), em ordem; cada um inclui os anteriores:
  inicio      campanha zerada (nada feito)
  parte1      casa e fazenda feitas; o Templo já pressionou (use --lento para o relógio estourado)
  escolha     ramo escolhido (--ramo a|b)
  etapa1      ramo A: casa do Tomé feita e bardo exposto | ramo B: Floresta de Adhadal vencida
  etapa2      ramo A: decisão sobre o bardo (--bardo) e celeiro | ramo B: Corvin vencida, Gilo fugiu
  rumo        decidiu seguir para Graciero (você está em Graciero)
  beco        Becos de Graciero feitos
  cais        Cais feito (com --lento, o relógio de Graciero estourou: a Praça será a "morta")
  praca       Praça dos Escorpiões feita (Gilo morto; viva ou morta pelo relógio)
`--bardo` (só ramo A, a partir de etapa2): morto | interrogado | gentil | maltratado.
"""
import argparse
import os
import socket
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (RAIZ, os.path.join(RAIZ, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

PONTOS = ["inicio", "parte1", "escolha", "etapa1", "etapa2", "rumo", "beco", "cais", "praca"]
BARDOS = ["morto", "interrogado", "gentil", "maltratado"]


def _s():
    import server as S
    return S


def estado_ate(ate, ramo="a", bardo="gentil", lento=False):
    """(fatos, progresso, local) acumulados até o ponto `ate`. Puro: não toca em nenhum jogo."""
    if ate not in PONTOS:
        raise ValueError(f"ponto desconhecido: {ate} (use um de {PONTOS})")
    if ramo not in ("a", "b"):
        raise ValueError("ramo deve ser a ou b")
    if ramo == "a" and bardo not in BARDOS:
        raise ValueError(f"bardo deve ser um de {BARDOS}")
    import gerar_campanha_elara as P1
    import gerar_elara_riacho as RI
    import gerar_elara_gilo as GI
    import gerar_elara_graciero as GR
    import elara_gilo_mapas as GM
    import elara_graciero_mapas as GRM
    fatos, prog, local = set(), {}, "alva_e_luz"
    n = PONTOS.index(ate)
    if n >= 1:
        fatos |= {P1.F_PEDIU, P1.F_CASA, P1.F_FAZENDA, P1.F_PRESSIONOU}
        prog["elara_parte1"] = 2
        if lento:
            fatos.add(P1.F_LENTO)
    if n >= 2:
        fatos.add(RI.F_RAMO_A if ramo == "a" else GI.F_RAMO_B)
    if n >= 3:
        if ramo == "a":
            fatos |= {RI.F_T1_FEITO, RI.F_EXPOSTO}
            prog["elara_riacho_casa"] = 1
            local = "vila_riacho"
        else:
            fatos.add(GM.F_ADHADAL)
            prog["elara_adhadal"] = 2
            local = "vila_corvin"
    if n >= 4:
        if ramo == "a":
            fatos.add(RI.F_DECIDIDO)
            if bardo == "morto":
                fatos |= {RI.F_MORTO, RI.F_LEONEL_CAUTELOSO}
            elif bardo == "interrogado":
                fatos |= {RI.F_INTERROGADO, RI.F_VILA_ABALADA}
            else:
                fatos |= {RI.F_POUPADO, RI.F_FINAL}
                fatos |= ({RI.F_T1_GENTIL, RI.F_GENTIL} if bardo == "gentil" else {RI.F_T1_AMEACA, RI.F_MALTRATADO})
            fatos.add(RI.F_MOCAS)
            prog["elara_riacho_celeiro"] = 1
        else:
            fatos |= {GI.F_CHEGADA, GM.F_CACADA, GM.F_GILO_FUGIU, GM.F_PISTA}
            prog["elara_corvin"] = 2
    if n >= 5:
        fatos.add(GR.F_RUMO)
        local = "graciero"
    if n >= 6:
        fatos.add(GRM.F_BECO)
        prog["elara_graciero_beco"] = 1
    if n >= 7:
        fatos.add(GRM.F_CAIS)
        prog["elara_graciero_cais"] = 1
        if lento:
            fatos.add(GR.F_LENTO)
    if n >= 8:
        fatos.add(GR.F_GILO_MORREU)
        if lento:
            prog["elara_graciero_praca_morta"] = 1
        else:
            fatos |= {GRM.F_VIU_MORRER, GR.F_DICA_MONTANHA}
            prog["elara_graciero_praca_viva"] = 1
    return fatos, prog, local


def aplicar_ao_jogo(sg, ate, ramo="a", bardo="gentil", lento=False, limpar_foto=False):
    """Reescreve o estado de Elara em `sg` (dict de jogo salvo). Devolve o que mudou."""
    fatos, prog, local = estado_ate(ate, ramo, bardo, lento)
    antigos = {f for f in (sg.get("fatos") or []) if isinstance(f, str)}
    mantidos = {f for f in antigos if not f.startswith("elara_")}
    sg["fatos"] = sorted(mantidos | fatos)
    progresso = {k: v for k, v in (sg.get("world_adventure_progress") or {}).items()
                 if not str(k).startswith("elara_")}
    progresso.update(prog)
    sg["world_adventure_progress"] = progresso
    sg["scene_conversations_done"] = [c for c in (sg.get("scene_conversations_done") or [])
                                      if ":elara_" not in str(c) and not str(c).startswith("elara_")]
    sg["relogios"] = {k: v for k, v in (sg.get("relogios") or {}).items() if not str(k).startswith("elara_")}
    sg["story_beats_done"] = [b for b in (sg.get("story_beats_done") or []) if "elara_" not in str(b)]
    if ate != "inicio":
        sg["world_location"] = local
    if limpar_foto:
        sg.pop("dungeon_snapshot", None)
    return {"fatos": sorted(fatos), "progresso": prog, "local": local if ate != "inicio" else None}


def servidor_rodando(porta=8765):
    s = socket.socket()
    s.settimeout(0.3)
    try:
        return s.connect_ex(("127.0.0.1", porta)) == 0
    finally:
        s.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--listar", action="store_true", help="lista os jogos salvos")
    ap.add_argument("--jogo", help="id do jogo salvo (sg_xxxxxx)")
    ap.add_argument("--ate", choices=PONTOS, help="ponto da campanha")
    ap.add_argument("--ramo", choices=("a", "b"), default="a")
    ap.add_argument("--bardo", choices=BARDOS, default="gentil")
    ap.add_argument("--lento", action="store_true", help="relógios estourados (Parte 1 e Graciero)")
    ap.add_argument("--limpar-foto", action="store_true", help="descarta a foto da masmorra (volta à cidade)")
    ap.add_argument("--simular", action="store_true", help="só mostra o que faria")
    ap.add_argument("--forcar", action="store_true", help="grava mesmo com o servidor rodando")
    a = ap.parse_args(argv)
    S = _s()
    S.LOJA.carregar()          # o servidor só faz isto no boot: aqui lemos os arquivos do disco
    if a.listar:
        for sg in S.LOJA.listar("savegames").values():
            print(f"{sg.get('id')}  {sg.get('name')!r}  dono={sg.get('owner')}  local={sg.get('world_location')}  "
                  f"fatos_elara={sum(1 for f in sg.get('fatos') or [] if str(f).startswith('elara_'))}")
        return 0
    if not a.jogo or not a.ate:
        ap.error("informe --jogo e --ate (ou --listar)")
    sg = S.LOJA.listar("savegames").get(a.jogo)
    if not sg:
        print(f"jogo não encontrado: {a.jogo}")
        return 2
    if servidor_rodando() and not a.forcar and not a.simular:
        print("O servidor está rodando (porta 8765): pare-o antes, senão ele regrava o jogo por cima. "
              "Use --forcar para ignorar.")
        return 2
    try:
        mudou = aplicar_ao_jogo(sg, a.ate, a.ramo, a.bardo, a.lento, a.limpar_foto)
    except ValueError as e:
        print(f"RECUSADO: {e}")
        return 2
    print(f"{a.jogo}: {a.ate} (ramo {a.ramo}" + (f", bardo {a.bardo}" if a.ramo == 'a' and PONTOS.index(a.ate) >= 4 else "")
          + (", lento" if a.lento else "") + ")")
    print(f"  local: {mudou['local']}")
    print(f"  progresso: {mudou['progresso']}")
    print(f"  fatos: {', '.join(mudou['fatos']) or '(nenhum)'}")
    if a.simular:
        print("(simulação: nada foi gravado)")
        return 0
    S.write_savegame(sg)
    S.LOJA.descarregar()       # manda o documento sujo para o disco
    print("gravado. Suba o servidor e entre pelo Continuar.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
