"""Roda a verificação de integridade em todas as masmorras de dungeons/.

Só lista avisos (não altera nenhum mapa). A regra é a mesma do botão
"🔍 Verificar integridade" do editor: server.avisos_integridade_masmorra.

Uso, da raiz:
    python -X utf8 tools/auditar_masmorras.py            # todas, em português
    python -X utf8 tools/auditar_masmorras.py --en       # em inglês
    python -X utf8 tools/auditar_masmorras.py elara_*    # só as que casam o padrão
"""
import fnmatch
import glob
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server  # noqa: E402


def main(argv):
    lang = "en" if "--en" in argv else "pt"
    padroes = [a for a in argv if not a.startswith("--")] or ["*"]
    arquivos = sorted(glob.glob(os.path.join(RAIZ, "dungeons", "*.json")))
    total = com_aviso = 0
    for caminho in arquivos:
        nome = os.path.splitext(os.path.basename(caminho))[0]
        if not any(fnmatch.fnmatch(nome, p) for p in padroes):
            continue
        total += 1
        try:
            defn = json.load(open(caminho, encoding="utf-8"))
        except Exception as e:
            print(f"\n## {nome}\n  ✗ não abre: {e}")
            com_aviso += 1
            continue
        avisos = server.avisos_integridade_masmorra(defn)
        if not avisos:
            continue
        com_aviso += 1
        print(f"\n## {nome} ({len(avisos)})")
        for a in avisos:
            texto = server.t(a["texto"].key, lang, **a["texto"].params)
            onde = f" ({a['pos'][0]},{a['pos'][1]})" if a.get("pos") else ""
            print(f"  • [{a['codigo']}]{onde} {texto}")
    print(f"\n{com_aviso} de {total} masmorra(s) com aviso.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
