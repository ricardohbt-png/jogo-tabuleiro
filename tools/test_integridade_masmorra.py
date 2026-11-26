"""Verificação de integridade das masmorras (avisos, nunca bloqueio).

Confere se as peças autoradas funcionam juntas no motor: armadilha de sala fora
de sala, mecanismo escondido, referência quebrada, objetivo sem peça, peça
inalcançável e peça em cima de parede.

Roda da raiz: python -X utf8 tools/test_integridade_masmorra.py
"""
import asyncio
import json
import os
import sys
from copy import deepcopy

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server

PASS = FAIL = 0


def check(label, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✅ {label}")
    else:
        FAIL += 1
        print(f"  ❌ {label}")


def base():
    """Mapa 9x5: sala A (x1-3) | parede com porta (4,2) | corredor fora de sala (x5-7)."""
    W, F, D = server.WALL, server.FLOOR, server.DOOR
    tiles = [[W] * 9 for _ in range(5)]
    for y in range(1, 4):
        for x in (1, 2, 3, 5, 6, 7):
            tiles[y][x] = F
    tiles[2][4] = D
    return {
        "schema_version": 1, "id": "t", "name": "t",
        "grid": {"w": 9, "h": 5}, "tiles": tiles,
        "rooms": [{"id": 1, "x": 1, "y": 1, "w": 3, "h": 3, "role": "entrance", "locked": False, "doors": [[4, 2]]}],
        "entrance": {"x": 1, "y": 1},
        "exit": {"x": 7, "y": 3},
        "monsters": [], "chests": [], "traps": [], "decorations": [], "secret_passages": [],
        "objectives": {"primary": {"type": "reach_exit"}, "secondary": []},
    }


def codigos(defn):
    return [a["codigo"] for a in server.avisos_integridade_masmorra(defn)]


def main():
    print("\n[1] Mapa limpo não gera aviso")
    check("sem avisos", codigos(base()) == [])

    print("\n[2] Armadilha de sala fora de sala desenhada")
    d = base(); d["traps"] = [{"id": "g", "tipo": "camara_gas", "pos": [6, 2]}]
    check("Câmara de Gás no corredor: aviso de área fechada", "gas_fora_de_sala" in codigos(d))
    d = base(); d["traps"] = [{"id": "g", "tipo": "camara_gas", "pos": [2, 2]}]
    check("Câmara de Gás dentro da sala: sem aviso", "gas_fora_de_sala" not in codigos(d))
    d = base(); d["traps"] = [{"id": "t", "tipo": "teto_esmagador", "pos": [6, 2]}]
    check("Teto Esmagador fora de sala: não funciona", "teto_fora_de_sala" in codigos(d))

    print("\n[3] Mecanismo escondido e referência quebrada")
    d = base()
    d["traps"] = [{"id": "g", "tipo": "camara_gas", "pos": [2, 2]}]
    d["decorations"] = [{"id": "lar", "type": "lareira", "pos": [3, 1], "disable_trap_ids": ["g"],
                         "escondido": True, "cd_busca": 12, "loot": {"gold": 1, "items": []}}]
    check("objeto que desliga armadilha marcado como esconderijo", "mecanismo_escondido" in codigos(d))
    d["decorations"][0]["disable_trap_ids"] = ["nao_existe"]
    check("objeto desliga armadilha que não existe", "desliga_inexistente" in codigos(d))

    print("\n[4] Objetivo sem peça")
    d = base(); d["objectives"]["primary"] = {"type": "kill_target"}
    check("matar alvo sem monstro marcado", "objetivo_sem_alvo" in codigos(d))
    d = base(); d["objectives"]["primary"] = {"type": "open_key_chest"}
    check("baú-chave sem baú ou objeto-chave", "objetivo_sem_bau_chave" in codigos(d))
    d = base(); d["objectives"]["primary"] = {"type": "rescue_prisoner"}
    check("resgate sem refém", "objetivo_sem_refem" in codigos(d))
    d = base(); d.pop("exit")
    check("chegar à saída sem saída", "objetivo_sem_saida" in codigos(d))
    d = base(); d["objectives"]["secondary"] = [{"type": "kill_target"}]
    check("vale também para objetivo secundário", "objetivo_sem_alvo" in codigos(d))

    print("\n[5] Peça inalcançável a partir da entrada")
    d = base(); d["tiles"][2][4] = server.WALL; d["rooms"][0]["doors"] = []
    check("saída do outro lado de uma parede fechada", "inalcancavel" in codigos(d))
    d2 = deepcopy(d); d2["secret_passages"] = [{"id": "p", "type": "mechanism", "pos": [4, 2], "key_decor_ids": ["k"]}]
    d2["decorations"] = [{"id": "k", "type": "estante", "pos": [1, 3], "key_objective": True}]
    check("passagem secreta conta como caminho", "inalcancavel" not in codigos(d2))
    d = base(); d["monsters"] = [{"type": "orc", "pos": [7, 1], "target": True}]
    d["objectives"]["primary"] = {"type": "kill_target"}
    check("alvo alcançável não gera aviso", "inalcancavel" not in codigos(d))

    print("\n[6] Peça em cima de parede")
    d = base(); d["chests"] = [{"pos": [0, 0], "gold": 1, "items": []}]
    check("baú dentro da parede", "peca_na_parede" in codigos(d))
    d = base(); d["monsters"] = [{"type": "orc", "pos": [4, 4]}]
    check("monstro dentro da parede", "peca_na_parede" in codigos(d))

    print("\n[7] Os avisos têm texto traduzível e posição")
    d = base(); d["traps"] = [{"id": "g", "tipo": "camara_gas", "pos": [6, 2]}]
    av = server.avisos_integridade_masmorra(d)[0]
    check("texto é um T com chave da verificação", getattr(av["texto"], "key", "").startswith("ui.editor.masmorra.integ."))
    check("posição da peça", av.get("pos") == [6, 2])
    check("o texto resolve em pt e en sem a chave crua",
          not server.t(av["texto"].key, "pt", **av["texto"].params).startswith("ui.")
          and not server.t(av["texto"].key, "en", **av["texto"].params).startswith("ui."))

    print("\n[8] O mapa real da casa da viela")
    real = json.load(open(os.path.join(RAIZ, "dungeons", "casa_secreta.json"), encoding="utf-8"))
    cs = codigos(real)
    check("aponta a Câmara de Gás fora de sala", "gas_fora_de_sala" in cs)
    check("aponta a lareira escondida que desliga a armadilha", "mecanismo_escondido" in cs)

    print("\n[9] Mensagem do editor")
    msgs = []

    async def send(m):
        msgs.append(m)
    srv = open(os.path.join(RAIZ, "server.py"), encoding="utf-8").read()
    check("o servidor atende verificar_integridade", '"verificar_integridade"' in srv)
    ed = open(os.path.join(RAIZ, "tools", "editor.js"), encoding="utf-8").read()
    check("o editor tem o botão de verificar", "verificarIntegridade" in ed)

    print(f"\n===== RESULTADO: {PASS} passaram, {FAIL} falharam =====")
    raise SystemExit(1 if FAIL else 0)


main()
