"""Gera src/lang/monstros.js — os textos das fichas de monstro nativas que não
são o nome do monstro: nome e descrição das habilidades especiais, nome dos
ataques e descrição das fraquezas/resistências.

Roda da raiz:  python -X utf8 tools/gerar_textos_monstros.py
               python -X utf8 tools/gerar_textos_monstros.py --importar <arquivo.json>

Por que a chave é o TEXTO e não o id: a mesma habilidade tem descrições
diferentes conforme o monstro (o Ferrão do jovem é CD 14, o do adulto CD 16), e
o cliente que recebe a ficha não sabe de que monstro veio cada habilidade. A
troca é feita só quando o texto é IDÊNTICO ao português nativo — é a mesma guarda
do `nome_cat`: habilidade escrita pelo autor no editor sai como ele escreveu.

Idempotente: preserva todo "en" já preenchido, acrescenta texto novo com "en"
vazio e relata (sem apagar) as chaves órfãs. `--importar` lê {pt: en} e preenche.
"""
import hashlib, json, os, re, sys, unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

DESTINO = os.path.join(RAIZ, "src", "lang", "monstros.js")
CAMPOS = {"name", "nome", "descricao", "description", "desc", "label"}
SUBARVORES = {"special_abilities", "attacks", "weaknesses", "resistances", "garra_attack"}
LETRA = re.compile(r"[A-Za-zÀ-ÿ]{2,}")

# Nomes que o servidor grava crus nos dados (comparados ou salvos na foto) e
# que precisam sair traduzidos na tela e na narração: entram pelo mesmo índice.
EXTRAS = {
    "Coronhada da besta": "Crossbow butt",
    "Moedas de Ouro": "Gold Coins",
    "a fonte do olhar": "the source of the gaze",
    "Nuvem de Gás": "Gas Cloud",
    "Baú-armadilha": "Trapped chest",
    "armadilha de dardos": "dart trap",
}


def chave_de(texto):
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_")[:32].strip("_") or "t"
    h = hashlib.sha1(texto.encode("utf-8")).hexdigest()[:6]
    return f"cat.texto.{base}_{h}"


def coletar(monster_defs):
    """Todos os textos das subárvores de ficha, na ordem em que aparecem."""
    vistos = {}

    def anda(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in CAMPOS and isinstance(v, str):
                    s = v.strip()
                    if s == v and LETRA.search(s):
                        vistos.setdefault(s, None)
                else:
                    anda(v)
        elif isinstance(o, list):
            for v in o:
                anda(v)

    for md in monster_defs:
        for k, v in md.items():
            if k in SUBARVORES:
                anda(v)
    return list(vistos)


def ler_existente():
    if not os.path.exists(DESTINO):
        return {}
    src = open(DESTINO, encoding="utf-8").read()
    m = re.search(r"^window\.LANG_MONSTROS = (\{.*?\n\});", src, re.S | re.M)
    return json.loads(m.group(1)) if m else {}


def gravar(dic):
    corpo = json.dumps(dict(sorted(dic.items())), ensure_ascii=False, indent=2)
    with open(DESTINO, "w", encoding="utf-8", newline="\n") as f:
        f.write("// GERADO por tools/gerar_textos_monstros.py — não edite as CHAVES à mão.\n"
                "// A chave é o TEXTO português da ficha nativa (ver o cabeçalho do\n"
                "// gerador). Preencha só a coluna \"en\".\n")
        f.write("window.LANG_MONSTROS = " + corpo + ";\n")
        f.write("Object.assign(window.LANG_STRINGS, window.LANG_MONSTROS);\n")


def main():
    import server as S
    atual = ler_existente()
    # A biblioteca de habilidades do editor também vira ficha de monstro
    # personalizado, com o mesmo texto nativo.
    biblioteca = S._base_ability_library()
    biblioteca = list(biblioteca.values()) if isinstance(biblioteca, dict) else list(biblioteca)
    textos = coletar(S.MONSTER_DEFS)
    for t in coletar([{"special_abilities": biblioteca}]) + list(EXTRAS):
        if t not in textos:
            textos.append(t)
    novo = {}
    for pt in textos:
        k = chave_de(pt)
        novo[k] = {"en": (atual.get(k) or {}).get("en", "") or EXTRAS.get(pt, ""), "pt": pt}
    if "--importar" in sys.argv:
        trad = json.load(open(sys.argv[sys.argv.index("--importar") + 1], encoding="utf-8"))
        for ent in novo.values():
            if not ent["en"] and trad.get(ent["pt"]):
                ent["en"] = trad[ent["pt"]]
    orfas = sorted(set(atual) - set(novo))
    gravar({**{k: atual[k] for k in orfas}, **novo})
    falta = [v["pt"] for v in novo.values() if not v["en"]]
    print(f"{len(novo)} textos de ficha; {len(falta)} sem inglês; {len(orfas)} órfãs.")
    for k in orfas:
        print("   órfã:", k)


if __name__ == "__main__":
    main()
