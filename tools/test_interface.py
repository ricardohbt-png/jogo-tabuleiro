"""Interface do cliente (etapa 5) — placar por área.
Roda da raiz: python tools/test_interface.py

Enquanto uma área não fecha, este teste RELATA quanto falta. Quando a sub-etapa
dela fecha, mova o nome para COBRADAS e ele passa a falhar se algo voltar. É o
mesmo padrão da seção [3] do test_narracao.py, que começou como relatório e virou
cobrança quando a 4b-ii terminou."""
import io, os, re, sys
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

GAME = io.open(os.path.join(RAIZ, "game.js"), encoding="utf-8").read()
LINHAS = GAME.split("\n")
ACENTO = re.compile(r"[ãáàâçéêíóõôúÃÁÀÂÇÉÊÍÓÕÔÚ]")
# Caminho de arquivo e seletor CSS não são texto de interface.
IGNORAR = re.compile(r"\.(js|png|jpe?g|glb|css|html)|assets/|^#[\w-]+$")

# Início de cada área, pela definição das funções de render que a compõem.
MARCOS = [
    ("selecao_heroi",  r"function (renderClassSelect|_csApply|selectClass)"),
    ("hud_acoes",      r"function (renderMyPanel|renderPlayers|renderActions|_warriorSkill)"),
    ("ficha",          r"function (renderFicha|abrirFicha|renderConteudoAtributos)"),
    ("cidade",         r"function (openShop|_renderShop|openGuild|_renderGuild|_updateCity)"),
    ("modais",         r"function (openTargetModal|aplicarTooltip|_tooltip|abrirPainelLoot)"),
    ("mestre",         r"function (renderMasterHud|renderFichaMonstro|renderMinimapaCR)"),
    ("render3d",       r"function (init3D|build3DFig|startLoop3D|draw2D)"),
]
# Áreas cuja sub-etapa já fechou. Mova o nome para cá ao terminar cada uma.
COBRADAS = set()


def _areas():
    """{area: n_literais_em_portugues}, por intervalo de linhas."""
    inicio = {}
    for nome, pat in MARCOS:
        ms = [i for i, l in enumerate(LINHAS) if re.search(pat, l)]
        if ms: inicio[nome] = min(ms)
    ordem = sorted(inicio.items(), key=lambda kv: kv[1])
    cont = {nome: 0 for nome, _ in MARCOS}
    cont["topo"] = 0
    for i, l in enumerate(LINHAS):
        if not ACENTO.search(l): continue
        n = len([t for t in re.findall(r"""["'`]([^"'`\n]{4,140})["'`]""", l)
                 if ACENTO.search(t) and not IGNORAR.search(t)])
        if not n: continue
        reg = "topo"
        for nome, ini in ordem:
            if i >= ini: reg = nome
        cont[reg] += n
    return cont


def _rodar_verificacoes():
    print("\n[1] Placar por área")
    cont = _areas()
    total = sum(cont.values())
    for nome, n in sorted(cont.items(), key=lambda kv: -kv[1]):
        marca = "COBRADA" if nome in COBRADAS else "pendente"
        print(f"     {n:>4}  {nome:<16} ({marca})")
    print(f"     ----  total: {total}")
    check("placar emitido", True)

    print("\n[2] Áreas já fechadas continuam limpas")
    if not COBRADAS:
        check("nenhuma área cobrada ainda (fundação)", True)
    for nome in sorted(COBRADAS):
        check(f"{nome} sem literal em português ({cont.get(nome, 0)})",
              cont.get(nome, 0) == 0)

    print("\n[3] A fiação da fundação existe")
    # `MutationObserver in GAME` sozinho passa pelo motivo ERRADO: já havia um
    # observador para os ícones de habilidade antes desta etapa. O que se
    # verifica é que ele também aplica o i18n.
    check("o observador do body também aplica _i18nApply",
          bool(re.search(r"new MutationObserver\([\s\S]{0,600}?_i18nApply", GAME)))
    check("ele só trabalha quando o nó traz data-i18n",
          bool(re.search(r"\[data-i18n", GAME)))
    check("o ícone de habilidade é achado por data-ability-id",
          "data-ability-id" in GAME and "abilityId" in GAME)


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Interface do cliente (etapa 5)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
