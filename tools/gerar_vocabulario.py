"""Gera src/lang/catalogo.js — as chaves de NOME dos catálogos do server.py.

Roda da raiz:  python tools/gerar_vocabulario.py

É idempotente: preserva todo "en" já traduzido, acrescenta as chaves novas com
"en" vazio, atualiza o "pt" a partir do catálogo e RELATA (sem apagar) as chaves
órfãs — aquelas cujo item saiu do catálogo. Rode-o depois de criar item ou
monstro novo: a saída diz exatamente o que falta traduzir.
"""
import json, os, re, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import server as S

DESTINO = os.path.join(RAIZ, "src", "lang", "catalogo.js")


class ColisaoDeId(Exception):
    """Dois catálogos dão nomes diferentes ao mesmo id — ambíguo, então falhamos
    alto em vez de escolher um em silêncio."""


def chave(familia, ident, sufixo="nome"):
    """Sufixo "nome" ou "desc". O padrão mantém as chamadas antigas válidas."""
    return f"cat.{familia}.{ident}.{sufixo}"


def _texto(entrada, tipo):
    """O jogo escreve o mesmo campo de duas formas conforme o catálogo:
    name/nome e desc/descricao. Aceitamos as duas em cada tipo."""
    if tipo == "desc":
        return entrada.get("desc") or entrada.get("descricao")
    return entrada.get("name") or entrada.get("nome")


def _entradas(catalogo, campo_id, tipo="nome"):
    """Devolve {id: texto} de um catálogo (lista ou dict). Quando o campo de id
    não existe na entrada, cai para a chave do dict — vários catálogos do jogo
    identificam o item pela chave, não por um campo. Entrada sem o texto pedido
    é omitida: é o que evita gerar chave .desc para quem não tem descrição."""
    itens = catalogo.items() if isinstance(catalogo, dict) else ((None, e) for e in catalogo)
    out = {}
    for chave_dict, entrada in itens:
        if not isinstance(entrada, dict):
            continue
        texto = _texto(entrada, tipo)
        ident = entrada.get(campo_id) or chave_dict
        if ident and texto:
            out[str(ident)] = texto
    return out


def fundir_item(destino, novos, origem):
    """Funde {id: nome} no acumulador de itens, recusando nomes divergentes."""
    for ident, nome in novos.items():
        anterior = destino.get(ident)
        if anterior is not None and anterior != nome:
            raise ColisaoDeId(
                f"id '{ident}' tem nomes diferentes: '{anterior}' e '{nome}' (em {origem})")
        destino[ident] = nome
    return destino


def coletar(tipo="nome"):
    """Devolve {familia: {id: texto_pt}} a partir dos catálogos do server.py.
    `tipo` é "nome" ou "desc" — a mesma varredura serve para os dois."""
    item = {}
    for nome_cat, campo in (("WEAPONS", "id"), ("SHOP_WEAPONS", "id"), ("SHOP_ARMORS", "id"),
                            ("SHOP_MERCHANT", "id"), ("SHOP_TEMPLE", "id"), ("SHOP_TAVERN", "id"),
                            ("SHOP_AMMO", "id"),
                            ("ARREMESSAVEIS", "id"), ("VENENOS", "id")):
        fundir_item(item, _entradas(getattr(S, nome_cat), campo, tipo), nome_cat)
    return {
        "item":        item,
        "guilda":      _entradas(S.GUILD_CATALOG, "id", tipo),
        "monstro":     _entradas(S.MONSTER_DEFS, "type", tipo),
        "decor":       _entradas(S.DECOR_TYPES, "id", tipo),
        "magia":       _entradas(S.GRIMORIO, "id", tipo),
        "armadilha":   _entradas(S.ARMADILHAS, "id", tipo),
        "instrumento": _entradas(S.INSTRUMENTOS_BASE, "id", tipo),
        "classe":      _entradas(S.CLASSES, "id", tipo),
        # _BUILTIN_WORLD_LOCATIONS e NÃO WORLD_LOCATIONS, de propósito: o
        # segundo inclui as cidades criadas no editor, que não devem ganhar
        # chave nenhuma — sem chave, o nome do autor sai intacto. É a mesma
        # proteção da guarda de igualdade da etapa 4c, aplicada na fonte.
        "local":       _entradas(S._BUILTIN_WORLD_LOCATIONS, "id", tipo),
    }


def achatar(vocab, vocab_desc=None):
    """{familia: {id: texto}} → {chave: texto_pt}, juntando nomes e descrições."""
    out = {chave(fam, ident, "nome"): texto
           for fam, entradas in vocab.items()
           for ident, texto in entradas.items()}
    for fam, entradas in (vocab_desc or {}).items():
        for ident, texto in entradas.items():
            out[chave(fam, ident, "desc")] = texto
    return out


def ler_existente(caminho):
    """Lê o catalogo.js já gerado (se houver). Ausente ou ilegível → {}."""
    try:
        with open(caminho, encoding="utf-8") as f:
            raw = f.read()
        m = re.search(r"^\s*window\.LANG_CATALOGO\s*=", raw, re.MULTILINE)
        ini = raw.index("{", m.end())
        return json.loads(raw[ini:raw.rindex("}") + 1])
    except Exception:
        return {}


def mesclar(existente, plano):
    """Une o que já existe com o que o catálogo manda agora.
    Devolve (dicionário, lista de chaves órfãs). Órfã é relatada, nunca apagada:
    um item pode ter sido renomeado por engano, e jogar a tradução fora seria
    perder trabalho de forma irreversível."""
    saida = {}
    for k, pt in plano.items():
        saida[k] = {"pt": pt, "en": (existente.get(k) or {}).get("en", "")}
    orfas = sorted(k for k in existente if k not in plano)
    for k in orfas:
        saida[k] = existente[k]
    return saida, orfas


def escrever(caminho, dicionario):
    corpo = json.dumps(dicionario, ensure_ascii=False, indent=2, sort_keys=True)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            "// GERADO por tools/gerar_vocabulario.py — não edite as CHAVES à mão.\n"
            "// Preencha só a coluna \"en\"; rodar o gerador de novo preserva o que\n"
            "// você já traduziu e acrescenta o que for novo.\n"
            "window.LANG_CATALOGO = " + corpo + ";\n"
            "Object.assign(window.LANG_STRINGS, window.LANG_CATALOGO);\n")


def main():
    plano = achatar(coletar(), coletar("desc"))
    novo, orfas = mesclar(ler_existente(DESTINO), plano)
    escrever(DESTINO, novo)
    faltando = sorted(k for k, v in novo.items() if not v.get("en"))
    print(f"{len(plano)} chaves no catálogo, {len(novo)} no arquivo.")
    print(f"{len(faltando)} sem tradução para o inglês.")
    if orfas:
        print(f"\n⚠️  {len(orfas)} chave(s) órfã(s) — o item saiu do catálogo. "
              f"Foram MANTIDAS; apague à mão se forem mesmo lixo:")
        for k in orfas:
            print("   ", k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
