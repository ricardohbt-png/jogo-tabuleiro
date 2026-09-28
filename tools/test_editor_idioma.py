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


# Texto que fica sempre na própria língua (as opções do seletor de idioma).
HTML_INTENCIONAIS = {"Português", "English"}


class _Moldura(HTMLParser):
    """Texto e atributos de interface do editor.html que ficaram SEM marcador."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pilha = []          # [(tag, attrs)]
        self.sem_marca = []      # textos pt sem data-i18n no elemento pai
        self.attr_sem_marca = [] # title/placeholder pt sem data-i18n-title/-ph
        self.chaves = set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for k in ("data-i18n", "data-i18n-title", "data-i18n-ph"):
            if a.get(k): self.chaves.add(a[k])
        for attr, marca in (("title", "data-i18n-title"), ("placeholder", "data-i18n-ph")):
            v = (a.get(attr) or "").strip()
            if v and parece_portugues(v) and not a.get(marca):
                self.attr_sem_marca.append(f"<{tag} {attr}={v!r}>")
        if tag not in ("input", "meta", "link", "br", "img"):
            self.pilha.append((tag, a))
    def handle_endtag(self, tag):
        while self.pilha:
            t_, _ = self.pilha.pop()
            if t_ == tag: break
    def handle_data(self, data):
        txt = data.strip()
        if not txt or not self.pilha: return
        tag, a = self.pilha[-1]
        if tag in ("script", "style"): return
        if txt in HTML_INTENCIONAIS: return
        if parece_portugues(txt) and not a.get("data-i18n"):
            self.sem_marca.append(txt)


def secao_html():
    print("\n[2b] editor.html: scripts, seletor e moldura")
    html = ler("tools", "editor.html")
    ordem = ["../src/lang/strings.js", "../src/lang/catalogo.js", "../src/lang/composto.js",
             "../src/lang/interface.js", "../src/lang/editor.js", "../src/i18n.js",
             "editor_i18n.js", "editor.js"]
    pos = [html.find('"' + s + '"') for s in ordem]
    check("carrega idioma → motor → cola → módulos, nessa ordem",
          all(p >= 0 for p in pos) and pos == sorted(pos))
    check("seletor de idioma #ed-lang com pt e en",
          re.search(r'<select id="ed-lang"[^>]*>\s*<option value="pt">Português</option>\s*'
                    r'<option value="en">English</option>\s*</select>', html) is not None)
    p = _Moldura(); p.feed(html)
    check(f"nenhum texto da moldura sem data-i18n ({p.sem_marca[:4]})", not p.sem_marca)
    check(f"nenhum title/placeholder sem marcador ({p.attr_sem_marca[:3]})", not p.attr_sem_marca)
    faltam = sorted(k for k in p.chaves if k not in S.LANG_STRINGS)
    check(f"toda chave data-i18n do editor.html existe ({faltam[:4]})", not faltam)


# Arquivos do editor medidos pelo placar. Gerados e testes ficam de fora.
MODULOS = ["editor.js", "editor_monster_editor.js", "editor_items_editor.js",
           "editor_items_logic.js", "editor_city.js", "editor_world.js",
           "editor_bestiary.js", "editor_scenes.js", "editor_campaign.js",
           "story_upload.js", "editor_preview_3d.js", "editor_story.js"]
RE_CHAVE_USADA = re.compile(r"""\bt\(\s*['"`](ui\.editor\.[\w.]+)['"`]""")


def secao_chaves_usadas():
    print("\n[3] Chaves ui.editor.* usadas nos módulos existem")
    usadas = set()
    for f in MODULOS + ["editor_i18n.js"]:
        usadas |= set(RE_CHAVE_USADA.findall(ler("tools", f)))
    faltam = sorted(k for k in usadas if not k.endswith(".") and k not in S.LANG_STRINGS)
    check(f"toda chave usada existe ({len(usadas)} usadas; faltam {faltam[:4]})", not faltam)


# Funções de "topo" dos módulos do editor: os módulos são IIFEs, então o topo
# fica a 2 espaços (`  function x(` / `  const x = (…) =>`). Arquivos sem IIFE
# (story_upload.js, editor_story.js) têm topo na coluna 0 — o 2º ramo cobre.
RE_FN_ED = re.compile(
    r"^(?:  )?(?:async\s+)?function\s+(\w+)"
    r"|^(?:  )?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:function\b|\(?[\w,\s]*\)?\s*=>)")

# Arquivos (ou "arquivo:função") já traduzidos: o placar COBRA zero neles. Cada
# fase acrescenta os seus ao fechar. Fase 0 não fecha módulo nenhum — a moldura
# (editor.html) é cobrada pela seção [2b].
FECHADAS = set()

# Um `t` local SOMBREIA o window.t global dentro do módulo (IIFE): t('chave') ali
# vira TypeError em runtime. Renomeie o local antes de migrar o arquivo.
RE_T_SOMBREADO = re.compile(
    r"\b(?:const|let|var)\s+t\s*[=,;]"      # const t = …
    r"|\(\s*t\s*[,)]"                       # (t) => / function (t, …)
    r"|(?<![\w$.])t\s*=>")                  # t => …


def _pendentes_por_funcao(arquivo):
    src = ler("tools", arquivo)
    dono, atual = {}, "@topo"
    for i, l in enumerate(src.split("\n")):
        m = RE_FN_ED.match(l)
        if m: atual = m.group(1) or m.group(2)
        dono[i + 1] = atual
    cont = collections.Counter()
    for linha, _txt in texto_de_interface(src):
        cont[dono.get(linha, "@topo")] += 1
    return cont


def secao_placar():
    print("\n[4] Placar: textos em português restantes nos módulos do editor")
    total = 0
    por_arquivo = {}
    for f in MODULOS:
        c = _pendentes_por_funcao(f)
        por_arquivo[f] = c
        total += sum(c.values())
    for f, c in sorted(por_arquivo.items(), key=lambda x: -sum(x[1].values())):
        n = sum(c.values())
        if n:
            print(f"     {n:4d}  {f}" + ("  (FECHADO)" if f in FECHADAS else ""))
    print(f"     total: {total}")
    regrediu = []
    for alvo in FECHADAS:
        f, _, fn = alvo.partition(":")
        c = por_arquivo.get(f, collections.Counter())
        n = c.get(fn, 0) if fn else sum(c.values())
        if n: regrediu.append(f"{alvo} ({n})")
    check(f"nenhum arquivo/função fechado regrediu ({len(FECHADAS)} fechados; {regrediu[:4]})",
          not regrediu)


def secao_sombreado():
    print("\n[5] `t` local que sombreia o t() global")
    achados = {}
    for f in MODULOS:
        linhas = [i + 1 for i, l in enumerate(ler("tools", f).split("\n"))
                  if RE_T_SOMBREADO.search(l)]
        if linhas: achados[f] = linhas
    for f, ls in sorted(achados.items()):
        print(f"     {f}: linhas {ls[:8]}{' …' if len(ls) > 8 else ''}")
    fechados_com_t = [f for f in achados if f in {a.partition(':')[0] for a in FECHADAS}]
    check(f"nenhum arquivo fechado tem `t` sombreado ({fechados_com_t})", not fechados_com_t)


if __name__ == "__main__":
    secao_dicionario()
    secao_editor_js()
    secao_html()
    secao_chaves_usadas()
    secao_placar()
    secao_sombreado()
    print(f"\n  {PASS} passaram, {FAIL} falharam")
    sys.exit(1 if FAIL else 0)
