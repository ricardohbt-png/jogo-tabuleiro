"""Conserta um jogo salvo cujo herói ficou na névoa ao entrar na masmorra.

Partidas que entraram em Adhadal 1/2 ou na Caçada de Corvin antes da correção
da entrada fora da sala guardaram, na foto da masmorra, a névoa em cima dos
heróis: sem casas azuis, sem movimento. Este script abre a foto, revela em
volta de cada herói que está numa casa nunca explorada (o mesmo raio de visão
do jogo) e grava de volta. Nada mais muda: casas, vida, monstros e rodada
ficam iguais.

Com o servidor já atualizado isto acontece sozinho ao Continuar; o script
serve para consertar o arquivo sem depender disso.

Uso (com o servidor DESLIGADO, na pasta do jogo):
    python -X utf8 tools/consertar_nevoa_save.py "novo começo"
    python -X utf8 tools/consertar_nevoa_save.py "novo começo" --simular

Antes de gravar, copia o arquivo do jogo para backup_nevoa/<id>.json (para
desfazer, devolva a cópia a savegames/ com o servidor desligado).
"""
import json, os, shutil, sys, unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
import server as S  # noqa: E402


def _norm(t):
    t = unicodedata.normalize("NFKD", str(t or "")).encode("ascii", "ignore").decode()
    return " ".join(t.lower().split())


def consertar_foto(registro, rotulo):
    """Devolve (registro novo ou None se nada mudou, casas reveladas)."""
    corpo = S.foto_desempacotar(registro)
    if corpo is None:
        print(f"  {rotulo}: foto ilegível, deixada como está")
        return None, 0
    sala = corpo.get("sala") or {}
    r = S.GameRoom("CONSERTO")
    for campo in S.foto_campos_sala("foto") + S.foto_campos_sala("foto_pid"):
        if campo in sala:
            setattr(r, campo, sala[campo])
    arquivo = r._arquivo_da_foto(sala)
    r._load_portcullis_def(S.carregar_dungeon(arquivo) if arquivo else None)
    r._rebuild_decor_index()
    r._rebuild_pontes_index()
    r._rebuild_materiais_index()
    r.players = {}
    for pid, cid in (corpo.get("pids") or {}).items():
        ficha = (corpo.get("herois") or {}).get(cid)
        if isinstance(ficha, dict):
            r.players[pid] = ficha
    antes = set(r.explored)
    r._revelar_herois_na_nevoa()
    novas = len(r.explored - antes)
    for p in r.players.values():
        print(f"  {rotulo}: {p.get('name')} em {p.get('pos')} "
              f"{'(estava na névoa)' if tuple(p.get('pos') or ()) not in antes else '(já via)'}")
    if not novas:
        return None, 0
    sala["explored"] = r.explored
    resumo = {k: v for k, v in registro.items() if k not in ("versao", "gravado_em", "dados")}
    return S.foto_empacotar(corpo, **resumo), novas


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    simular = "--simular" in sys.argv
    if not args:
        print(__doc__)
        sys.exit(1)
    alvo = _norm(args[0])
    S.LOJA.carregar()
    jogos = [sg for sg in S.LOJA.listar("savegames").values()
             if isinstance(sg, dict) and (_norm(sg.get("name")) == alvo or sg.get("id") == args[0])]
    if not jogos:
        print(f"Nenhum jogo salvo chamado {args[0]!r}. Jogos encontrados:")
        for sg in S.LOJA.listar("savegames").values():
            if isinstance(sg, dict):
                print(f"  - {sg.get('name')}  ({sg.get('id')})")
        sys.exit(1)
    if len(jogos) > 1:
        print("Mais de um jogo com esse nome; rode de novo passando o id:")
        for sg in jogos:
            print(f"  - {sg.get('name')}  ({sg.get('id')}), atualizado em {sg.get('updated')}")
        sys.exit(1)
    sg = jogos[0]
    print(f"Jogo: {sg.get('name')} ({sg.get('id')})")

    mudou = 0
    reg = sg.get("dungeon_snapshot")
    if isinstance(reg, dict) and reg.get("onde") == "masmorra":
        novo, n = consertar_foto(reg, "foto atual")
        if novo:
            sg["dungeon_snapshot"] = novo
            mudou += n
    else:
        print("  O jogo não está salvo dentro de uma masmorra: ao entrar no mapa "
              "com o servidor atualizado, a correção já vale.")
    for chave, reg in list((sg.get("dungeon_snapshots") or {}).items()):
        if isinstance(reg, dict) and reg.get("onde") == "masmorra":
            novo, n = consertar_foto(reg, f"foto da rota {chave}")
            if novo:
                sg["dungeon_snapshots"][chave] = novo
                mudou += n

    if not mudou:
        print("Nada a consertar: nenhum herói estava na névoa.")
        return
    if simular:
        print(f"Simulação: {mudou} casa(s) seriam reveladas. Nada foi gravado.")
        return
    origem = os.path.join(S.SAVEGAMES_DIR, f"{sg['id']}.json")
    if os.path.exists(origem):
        # Fora da pasta de saves: lá dentro a cópia viraria outro jogo na lista.
        pasta = os.path.join(RAIZ, "backup_nevoa")
        os.makedirs(pasta, exist_ok=True)
        copia = os.path.join(pasta, f"{sg['id']}.json")
        shutil.copy2(origem, copia)
        print(f"Cópia do jogo antes do conserto: {copia}")
    S.write_savegame(sg)
    S.LOJA.descarregar()
    print(f"Pronto: {mudou} casa(s) reveladas em volta dos heróis. Pode continuar o jogo.")


if __name__ == "__main__":
    main()
