"""Placar e checagens do EDITOR em PT/EN.

Roda da raiz:  python -X utf8 tools/test_editor_idioma.py

Seções:
  [1] dicionário src/lang/editor.js (carrega no servidor, tem en, paridade de {params})
  [2] editor.html: ordem dos scripts, seletor, moldura marcada com data-i18n
  [3] chaves ui.editor.* usadas nos tools/*.js e no editor.html existem
  [4] placar por arquivo/função (relata) + FECHADAS (cobra)
  [5] `t` sombreado: relata por arquivo, cobra nos FECHADOS
"""
import io, os, re, sys, collections
from html.parser import HTMLParser
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(RAIZ, "tools")
sys.path.insert(0, TOOLS)
sys.path.insert(0, RAIZ)
from js_strings import texto_de_interface, parece_portugues
import server as S   # funde todos os src/lang/*.js em S.LANG_STRINGS

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

def ler(*partes):
    return io.open(os.path.join(RAIZ, *partes), encoding="utf-8").read()

PARAM = re.compile(r"\{(\w+)\}")
EDITOR_DICT = S._load_lang_arquivo(os.path.join(RAIZ, "src", "lang", "editor.js"))


def secao_dicionario():
    print("\n[1] Dicionário src/lang/editor.js")
    check("arquivo carrega e tem chaves", len(EDITOR_DICT) > 0)
    check("toda chave é ui.editor.*", all(k.startswith("ui.editor.") for k in EDITOR_DICT))
    check("o servidor fundiu o dicionário do editor",
          all(k in S.LANG_STRINGS for k in EDITOR_DICT))
    sem_en = [k for k, v in EDITOR_DICT.items() if not v.get("en")]
    check(f"toda chave tem en ({len(sem_en)} sem)", not sem_en)
    ruins = [k for k, v in EDITOR_DICT.items()
             if set(PARAM.findall(v.get("pt", ""))) != set(PARAM.findall(v.get("en", "")))]
    check(f"paridade de {{parâmetros}} pt×en ({ruins[:3]})", not ruins)


def secao_editor_js():
    print("\n[2a] editor.js lembra a aba atual para o redesenho")
    src = ler("tools", "editor.js")
    i = src.index("function setTab(tab) {")
    corpo = src[i:i + 200]
    check("setTab grava window._abaAtualEditor logo no início",
          "window._abaAtualEditor = tab;" in corpo)
    check("aba inicial registrada junto do window.setTab",
          re.search(r"window\.setTab = setTab;\s*\n\s*window\._abaAtualEditor = window\._abaAtualEditor \|\| \"masmorra\";",
                    src) is not None)


if __name__ == "__main__":
    secao_dicionario()
    secao_editor_js()
    print(f"\n  {PASS} passaram, {FAIL} falharam")
    sys.exit(1 if FAIL else 0)
