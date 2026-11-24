"""Atualiza o jogo do master sem perder o que você editou nos arquivos de dados.

Quando o editor grava `world_adventures.json`, `city_map_points.json` ou
`city_scenes.json`, o `git pull` recusa atualizar ("Your local changes would be
overwritten") e o jogo fica preso na versão antiga desses arquivos. Este script
junta as duas coisas, item por item (cada destino, cada ponto da cidade, cada
cena e conversa):

- o que só você mudou é mantido;
- o que só o master mudou é atualizado;
- o que os dois mudaram no mesmo item fica com a versão do master, e o script
  lista esses itens: são as suas edições que seriam perdidas.

Sem opções ele só MOSTRA o que vai acontecer e não muda nada. Com --aplicar,
guarda uma cópia dos arquivos em backup_atualizacao/, atualiza o jogo do
master e grava os arquivos juntados.

Uso (na pasta do jogo, com o servidor DESLIGADO):
    git fetch origin
    git checkout origin/master -- tools/atualizar_com_edicoes.py
    python -X utf8 tools/atualizar_com_edicoes.py
    python -X utf8 tools/atualizar_com_edicoes.py --aplicar
(O `git checkout` traz o script sem passar pelo `>` do PowerShell, que grava
o arquivo num formato que o Python não lê.)
"""
import json, os, shutil, subprocess, sys, time

ARQUIVOS = ("world_adventures.json", "city_map_points.json", "city_scenes.json")
REMOTO = "origin/master"
AUSENTE = object()


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} falhou:\n{r.stderr.strip()}")
    return r


def versao(ref, arquivo):
    r = git("show", f"{ref}:{arquivo}", check=False)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def juntar(base, meu, deles, caminho, perdidas):
    """Junta três versões. Dicionário desce item por item; o resto é atômico."""
    if meu == deles:
        return meu
    if meu == base:
        return deles          # só o master mudou
    if deles == base:
        return meu            # só você mudou
    if isinstance(meu, dict) and isinstance(deles, dict):
        base = base if isinstance(base, dict) else {}
        out = {}
        for k in list(deles) + [k for k in meu if k not in deles]:
            v = juntar(base.get(k, AUSENTE), meu.get(k, AUSENTE), deles.get(k, AUSENTE),
                       caminho + [k], perdidas)
            if v is not AUSENTE:
                out[k] = v
        return out
    # Listas do mesmo tamanho (etapas de um destino, NPCs de uma cena) descem
    # posição por posição; tamanhos diferentes contam como um item só.
    if (isinstance(meu, list) and isinstance(deles, list) and isinstance(base, list)
            and len(meu) == len(deles) == len(base)):
        return [juntar(b, m, d, caminho + [i], perdidas)
                for i, (b, m, d) in enumerate(zip(base, meu, deles))]
    perdidas.append((caminho, meu, deles))
    return deles              # os dois mudaram: fica a versão do master


def resumo(v):
    if v is AUSENTE:
        return "(não existe)"
    t = json.dumps(v, ensure_ascii=False)
    return t if len(t) <= 160 else t[:157] + "..."


def principal():
    aplicar = "--aplicar" in sys.argv
    if not os.path.exists(".git"):
        raise SystemExit("Rode na pasta do jogo (a que tem a pasta .git).")
    git("fetch", "-q", "origin")
    base_ref = git("merge-base", "HEAD", REMOTO).stdout.strip()

    sujos = [l[3:] for l in git("status", "--porcelain").stdout.splitlines() if l[:2].strip() == "M"]
    outros = [f for f in sujos if f not in ARQUIVOS]
    vindos = set(git("diff", "--name-only", "HEAD", REMOTO).stdout.split())
    bloqueiam = [f for f in outros if f in vindos]

    juntados, total_perdidas = {}, 0
    for arq in ARQUIVOS:
        if not os.path.exists(arq):
            continue
        with open(arq, encoding="utf-8") as f:
            meu = json.load(f)
        base, deles = versao(base_ref, arq), versao(REMOTO, arq)
        if deles is None:
            continue
        perdidas = []
        juntados[arq] = juntar(base if base is not None else {}, meu, deles, [], perdidas)
        minhas = meu != base
        print(f"\n== {arq} ==")
        if not minhas:
            print("  sem edições suas: só recebe a atualização.")
            continue
        if not perdidas:
            print("  suas edições são mantidas por inteiro.")
        for caminho, mv, dv in perdidas:
            total_perdidas += 1
            print("  PERDIDA em " + " > ".join(map(str, caminho)))
            print("     sua versão:   " + resumo(mv))
            print("     fica a do jogo: " + resumo(dv))

    if outros:
        print("\nOutros arquivos com mudanças suas (o script não mexe neles): " + ", ".join(outros))
    if bloqueiam:
        print("ATENÇÃO: estes também mudaram no master e vão impedir a atualização: "
              + ", ".join(bloqueiam) + ". Me mande o nome deles antes de continuar.")
        return
    print(f"\nEdições suas que seriam perdidas: {total_perdidas}.")
    if not aplicar:
        print("Nada foi mudado. Para atualizar, rode de novo com --aplicar.")
        return

    pasta = os.path.join("backup_atualizacao", time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(pasta, exist_ok=True)
    for arq in juntados:
        shutil.copy2(arq, os.path.join(pasta, arq))
    git("checkout", "--", *juntados)
    r = git("merge", "--ff-only", REMOTO, check=False)
    if r.returncode != 0:
        for arq in juntados:
            shutil.copy2(os.path.join(pasta, arq), arq)
        raise SystemExit("A atualização não pôde ser feita; seus arquivos foram devolvidos.\n"
                         + r.stderr.strip())
    for arq, dados in juntados.items():
        if dados == versao(REMOTO, arq):
            continue   # nada seu a manter: fica o arquivo do master como veio
        with open(arq, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(dados, indent=2, ensure_ascii=False) + "\n")
    print(f"Pronto: jogo atualizado. Cópia dos seus arquivos antigos em {pasta}.")
    print("Reinicie o servidor.")


if __name__ == "__main__":
    principal()
