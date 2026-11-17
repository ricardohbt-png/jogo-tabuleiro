"""Gera de antemao as miniaturas que o servidor entrega em `?w=<largura>`.

O servidor ja as cria sozinho no primeiro pedido (e ao subir, em segundo
plano); este script serve para deixar tudo pronto antes de abrir o jogo para
os amigos, ou como passo de build na hospedagem. Precisa do Pillow.

Uso (da raiz):  python -X utf8 tools/gerar_miniaturas.py
"""
import os
import sys
import time

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S


def main():
    inicio = time.time()
    feitas = antes = depois = 0
    for pasta, largura in S.MINIATURAS_PREAQUECER:
        base = os.path.join(S.BASE_DIR, pasta)
        for raiz, _dirs, nomes in os.walk(base):
            for nome in sorted(nomes):
                if os.path.splitext(nome)[1].lower() not in S._MINI_EXTS:
                    continue
                full = os.path.join(raiz, nome)
                rel = os.path.relpath(full, S.BASE_DIR).replace("\\", "/")
                st = os.stat(full)
                if not largura and (not nome.lower().endswith(".png")
                                    or st.st_size < S._REENC_MIN_BYTES):
                    continue
                mini = S._miniatura(full, rel, st, largura)
                feitas += 1
                antes += st.st_size
                depois += len(mini[0]) if mini else st.st_size
    if not feitas:
        print("nenhuma imagem encontrada")
        return
    print(f"{feitas} imagens: {antes / 1e6:.0f} MB -> {depois / 1e6:.0f} MB "
          f"({100 - depois * 100 // max(1, antes)}% menor) em {time.time() - inicio:.0f} s")
    try:
        import PIL  # noqa: F401
    except Exception:
        print("AVISO: Pillow nao instalado -- nada foi reduzido (pip install Pillow).")


if __name__ == "__main__":
    main()
