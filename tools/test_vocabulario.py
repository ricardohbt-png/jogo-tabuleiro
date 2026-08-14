"""Vocabulário (etapa 2) — geração das chaves de nome de catálogo.
Roda da raiz: python tools/test_vocabulario.py"""
import importlib, json, os, shutil, subprocess, sys, tempfile
try: sys.stdout.reconfigure(encoding="utf-8")
except Exception: pass
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S

PASS = 0; FAIL = 0
def check(name, cond):
    global PASS, FAIL
    if cond: PASS += 1; print(f"  ✅ {name}")
    else:    FAIL += 1; print(f"  ❌ {name}")

import gerar_vocabulario as G   # tools/ entra no sys.path abaixo


def _rodar_verificacoes():
    print("\n[1] Coleta das famílias")
    vocab = G.coletar()
    # Sem contagem cravada: o catálogo é VIVO — o usuário acrescenta itens,
    # monstros e técnicas o tempo todo, e um número fixo aqui deixaria a suíte
    # vermelha por motivo falso a cada conteúdo novo. O que se verifica é a
    # RELAÇÃO entre o catálogo e as chaves geradas, que não depende do tamanho.
    # A LISTA de famílias também é viva — a `local` entrou depois das 8
    # originais. O que importa é que as conhecidas continuem lá e que nenhuma
    # família declarada venha vazia (isso sim seria fonte quebrada).
    ESPERADAS = {"armadilha", "classe", "decor", "guilda",
                 "instrumento", "item", "magia", "monstro"}
    check(f"as famílias conhecidas existem ({len(vocab)} no total)",
          ESPERADAS <= set(vocab))
    vazias = [f for f, v in vocab.items() if not v]
    check(f"nenhuma família declarada está vazia ({vazias})", not vazias)
    check("todo id coletado vira exatamente uma chave de nome",
          len(G.achatar(vocab)) == sum(len(d) for d in vocab.values()))

    print("\n[2] Formato da chave")
    check("chave de item usa o id", "dagger" in vocab["item"])
    check("chave de monstro usa o type", "goblin" in vocab["monstro"])
    check("o pt vem do próprio catálogo", vocab["item"]["dagger"] == "Adaga")
    check("monta cat.<familia>.<id>.nome",
          G.chave("item", "dagger") == "cat.item.dagger.nome")

    print("\n[3] Colisões são erro, não escolha silenciosa")
    try:
        G.fundir_item({"a": "Nome Um"}, {"a": "Nome Dois"}, "TESTE")
        check("id repetido com nome diferente levanta erro", False)
    except G.ColisaoDeId:
        check("id repetido com nome diferente levanta erro", True)
    ok = True
    try:
        G.fundir_item({"a": "Igual"}, {"a": "Igual"}, "TESTE")
    except G.ColisaoDeId:
        ok = False
    check("id repetido com o MESMO nome é aceito", ok)

    print("\n[4] Escrita e releitura do arquivo")
    tmp = tempfile.mkdtemp(prefix="vocab_")
    try:
        alvo = os.path.join(tmp, "catalogo.js")
        G.escrever(alvo, {"cat.item.x.nome": {"pt": "Xis", "en": ""}})
        lido = G.ler_existente(alvo)
        check("o que foi escrito é relido igual",
              lido == {"cat.item.x.nome": {"pt": "Xis", "en": ""}})
        check("o arquivo declara window.LANG_CATALOGO",
              "window.LANG_CATALOGO" in open(alvo, encoding="utf-8").read())
        check("o arquivo funde em LANG_STRINGS",
              "Object.assign(window.LANG_STRINGS" in open(alvo, encoding="utf-8").read())

        print("\n[5] Idempotência: tradução feita à mão sobrevive")
        G.escrever(alvo, {"cat.item.x.nome": {"pt": "Xis", "en": "Ex"}})
        novo, orfas = G.mesclar(G.ler_existente(alvo),
                                {"cat.item.x.nome": "Xis", "cat.item.y.nome": "Ípsilon"})
        check("preserva o en já traduzido", novo["cat.item.x.nome"]["en"] == "Ex")
        check("acrescenta a chave nova com en vazio", novo["cat.item.y.nome"]["en"] == "")
        check("atualiza o pt a partir do catálogo", novo["cat.item.y.nome"]["pt"] == "Ípsilon")
        check("nenhuma órfã neste caso", orfas == [])

        print("\n[6] Órfã é relatada e NÃO apagada")
        novo2, orfas2 = G.mesclar({"cat.item.sumiu.nome": {"pt": "Sumiu", "en": "Gone"}},
                                  {"cat.item.x.nome": "Xis"})
        check("a órfã é relatada", orfas2 == ["cat.item.sumiu.nome"])
        check("a órfã continua no dicionário", "cat.item.sumiu.nome" in novo2)
        check("a tradução da órfã é preservada", novo2["cat.item.sumiu.nome"]["en"] == "Gone")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n[7] O servidor funde todos os .js de src/lang/")
    check("o dicionário do servidor tem chave do strings.js",
          "erro.porta_longe" in S.LANG_STRINGS)
    check("o dicionário do servidor tem chave do catalogo.js",
          "cat.monstro.goblin.nome" in S.LANG_STRINGS)
    check("o nome em pt veio do catálogo",
          S.t("cat.monstro.goblin.nome", "pt") == "Goblin")
    # Nenhuma chave do arquivo pode apontar para item que saiu do catálogo: se
    # apontasse, o jogo mostraria em inglês um nome que não existe mais.
    plano = G.achatar(G.coletar(), G.coletar("desc"))
    no_arquivo = G.ler_existente(G.DESTINO)
    check("nenhuma chave órfã no catalogo.js gerado",
          sorted(k for k in no_arquivo if k not in plano) == [])

    print("\n[8] Parâmetro que é ele próprio traduzível")
    S.LANG_STRINGS["_teste.frase"] = {"pt": "{quem} atacou!", "en": "{quem} attacked!"}
    check("resolve o T aninhado em inglês",
          S.t("_teste.frase", "en", quem=S.T("cat.monstro.goblin.nome"))
          == S.t("cat.monstro.goblin.nome", "en") + " attacked!")
    check("resolve o T aninhado em português",
          S.t("_teste.frase", "pt", quem=S.T("cat.monstro.goblin.nome")) == "Goblin atacou!")
    check("parâmetro comum continua funcionando",
          S.t("_teste.frase", "pt", quem="Thorin") == "Thorin atacou!")
    check("T aninhado com parâmetro próprio também resolve",
          S.t("_teste.frase", "pt", quem=S.T("narracao.abre_porta", nome="Lyra"))
          == "🚪 **Lyra** abre uma porta! atacou!")
    S.LANG_STRINGS.pop("_teste.frase", None)

    print("\n[9] nome_de devolve um T com a chave certa")
    marcado = S.nome_de("monstro", "goblin")
    check("nome_de devolve T", isinstance(marcado, S.T))
    check("nome_de monta a chave", marcado.key == "cat.monstro.goblin.nome")
    check("nome_de rende o nome", S._t_render(marcado, "pt") == "Goblin")

    print("\n[12] Descrições")
    desc = G.coletar("desc")
    check("as seis famílias com descrição têm entradas",
          all(desc.get(f) for f in ("guilda", "magia", "armadilha",
                                    "instrumento", "classe", "item")))
    check("chave de descrição usa o sufixo .desc",
          G.chave("guilda", "brutalidade", "desc") == "cat.guilda.brutalidade.desc")
    check("chave de nome continua com .nome por padrão",
          G.chave("guilda", "brutalidade") == "cat.guilda.brutalidade.nome")
    nomes = G.coletar()
    check("achatar soma nomes e descrições, sem perder nem duplicar",
          len(G.achatar(nomes, desc))
          == sum(len(d) for d in nomes.values()) + sum(len(d) for d in desc.values()))
    # Unitário, com dados sintéticos: robusto a qualquer conteúdo que o usuário
    # acrescente ao jogo.
    check("entrada sem descrição não gera chave .desc",
          G.achatar({"x": {"a": "Nome"}}, {"x": {}}) == {"cat.x.a.nome": "Nome"})
    check("o arquivo gerado contém tudo que o catálogo manda",
          set(G.ler_existente(G.DESTINO)) >= set(G.achatar(nomes, desc)))
    # Idempotência com as DUAS famílias de chave: o que importa é que uma
    # descrição traduzida à mão sobreviva à próxima execução do gerador.
    novo, _ = G.mesclar({"cat.guilda.x.desc": {"pt": "Antigo", "en": "Old"}},
                        {"cat.guilda.x.desc": "Novo"})
    check("descrição traduzida à mão sobrevive", novo["cat.guilda.x.desc"]["en"] == "Old")
    check("o pt da descrição é atualizado do catálogo",
          novo["cat.guilda.x.desc"]["pt"] == "Novo")


if __name__ == "__main__":
    print("=" * 62); print("  TESTE — Vocabulário (nomes de catálogo)"); print("=" * 62)
    _rodar_verificacoes()
    print("\n" + "=" * 62)
    print(f"  {PASS} passaram, {FAIL} falharam")
    print("=" * 62)
    sys.exit(1 if FAIL else 0)
