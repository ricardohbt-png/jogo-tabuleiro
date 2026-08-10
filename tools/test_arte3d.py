# -*- coding: utf-8 -*-
"""Sincronia entre as tabelas de arte 3D do cliente, o disco e o servidor.

O sintoma que este teste evita é o pior de todos: a criatura ou o objeto some do
tabuleiro (vira peão genérico / caixa procedural) sem nenhum erro, porque a
tabela do cliente aponta para um arquivo que não existe, ou porque um .glb novo
foi adicionado em assets/ e ninguém o registrou.

Rodar da raiz:  python tools/test_arte3d.py
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server                                          # noqa: E402

# O console do Windows usa cp1252 por padrão e estoura nos emojis do relatório.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, TypeError):
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME_JS = os.path.join(BASE, "game.js")

_ok = _fail = 0
_avisos = []


def check(nome, cond, detalhe=""):
    global _ok, _fail
    if cond:
        _ok += 1
        print(u"  ✅ " + nome)
    else:
        _fail += 1
        print(u"  ❌ " + nome + ((" — " + detalhe) if detalhe else ""))


def aviso(txt):
    _avisos.append(txt)


def tabela_js(fonte, nome):
    """Extrai um dicionário literal `const NOME = {...}` do game.js.

    Regex em vez de parser porque só precisamos dos pares chave→'caminho', e o
    game.js não é um módulo importável (é script clássico do navegador)."""
    m = re.search(r"const %s = (?:Object\.freeze\()?\{(.*?)\n\}\)?;" % nome, fonte, re.S)
    if not m:
        return {}
    return {k.strip("'"): v
            for k, v in re.findall(r"([\w'\.]+)\s*:\s*'([^']+)'", m.group(1))}


def main():
    fonte = io.open(GAME_JS, encoding="utf-8", errors="replace").read()
    mon_glb = tabela_js(fonte, "_MONSTER_GLB_MODELS")
    dec_tipo = tabela_js(fonte, "DECOR_GLB_TYPES")
    dec_img = tabela_js(fonte, "DECOR_GLB_MODELS")

    print("\n[1] Tabelas do cliente foram lidas")
    check("_MONSTER_GLB_MODELS tem entradas", len(mon_glb) > 0)
    check("DECOR_GLB_TYPES tem entradas", len(dec_tipo) > 0)

    print("\n[2] Todo GLB referenciado existe em disco")
    for tabela, nome in ((mon_glb, "_MONSTER_GLB_MODELS"),
                         (dec_tipo, "DECOR_GLB_TYPES"),
                         (dec_img, "DECOR_GLB_MODELS")):
        faltando = sorted({v for v in tabela.values()
                           if not os.path.isfile(os.path.join(BASE, v.replace("/", os.sep)))})
        check("%s sem referência quebrada" % nome, not faltando, ", ".join(faltando))

    print("\n[3] Todo GLB em disco está registrado em alguma tabela")
    usados_obj = {v.split("/")[-1] for v in list(dec_tipo.values()) + list(dec_img.values())}
    usados_mon = {v.split("/")[-1] for v in mon_glb.values()}
    for pasta, usados in ((os.path.join("assets", "objetos"), usados_obj),
                          (os.path.join("assets", "models3d", "monstros"), usados_mon)):
        disco = {f for f in os.listdir(os.path.join(BASE, pasta)) if f.endswith(".glb")}
        orfaos = sorted(disco - usados)
        # Órfão é AVISO, não falha: um .glb pode ser adicionado antes do tipo que
        # vai usá-lo. Referência quebrada ([2]) é que quebra o jogo.
        if orfaos:
            aviso(u"%s: .glb sem tipo/imagem que o use → %s" % (pasta, ", ".join(orfaos)))
        check("%s existe e foi varrida" % pasta, len(disco) > 0)

    print("\n[4] DECOR_MODEL3D (servidor) casa com DECOR_GLB_TYPES (cliente)")
    # As duas tabelas descrevem a MESMA coisa; se divergirem, o servidor manda um
    # model3d que o cliente não esperava (ou deixa de mandar o que ele precisa).
    srv = getattr(server, "DECOR_MODEL3D", {})
    so_no_servidor = sorted(set(srv) - set(dec_tipo))
    so_no_cliente = sorted(set(dec_tipo) - set(srv))
    divergentes = sorted(t for t in set(srv) & set(dec_tipo) if srv[t] != dec_tipo[t])
    check("mesmos tipos nos dois lados", not so_no_servidor and not so_no_cliente,
          "só no servidor: %s | só no cliente: %s" % (so_no_servidor, so_no_cliente))
    check("mesmos caminhos nos dois lados", not divergentes, ", ".join(divergentes))

    # O cliente completa o `image` de tipos legados (goblin, skeleton…) e tem
    # miniaturas procedurais DEDICADAS para alguns deles: sem espelhar as duas
    # coisas aqui, o teste acusaria falta de arte onde ela existe.
    img_padrao = tabela_js(fonte, "_MONSTER_TYPE_DEFAULT_IMAGE")
    com_mini_propria = set(re.findall(r"case '(\w+)':\s+_mini\w+\(grp", fonte))

    custom = {m.get("type") for m in server._read_custom_monsters() if isinstance(m, dict)}

    def arte_de(mdef):
        tipo = mdef.get("type")
        img = mdef.get("image") or img_padrao.get(tipo)
        tem_glb = bool(mon_glb.get(img) or mon_glb.get(tipo))
        tem_png = bool(img) and os.path.isfile(
            os.path.join(BASE, "assets", "pawns", "monstros", img, img + ".png"))
        return img, tem_glb, tem_png

    print("\n[5] Toda criatura tem arte utilizável (GLB, PNG ou mini dedicada)")
    # Sem nenhuma das três, o peão cai na miniatura GENÉRICA: é exatamente o
    # "monstro virou boneco genérico" que motivou este teste.
    sem_arte, sem_arte_custom = [], []
    for mdef in server.MONSTER_DEFS:
        tipo = mdef.get("type")
        img, tem_glb, tem_png = arte_de(mdef)
        if tem_glb or tem_png or tipo in com_mini_propria:
            continue
        (sem_arte_custom if tipo in custom else sem_arte).append("%s (image=%s)" % (tipo, img))
    check("nenhuma criatura NATIVA sem arte", not sem_arte, "; ".join(sem_arte))
    if sem_arte_custom:
        # Criatura do editor é responsabilidade do autor: avisa, não reprova.
        aviso(u"criaturas personalizadas sem arte (envie o PNG no editor): %s"
              % "; ".join(sem_arte_custom))

    print("\n[6] O `image` de cada criatura aponta para um PNG que existe")
    # Pega o caso lorde_vampiro: image="lorde_vampirico", pasta="lorde_vampiro".
    quebrados, quebrados_custom = [], []
    for mdef in server.MONSTER_DEFS:
        img = mdef.get("image")
        if not img:
            continue
        if not os.path.isfile(os.path.join(BASE, "assets", "pawns", "monstros",
                                           img, img + ".png")):
            alvo = quebrados_custom if mdef.get("type") in custom else quebrados
            alvo.append("%s -> %s" % (mdef.get("type"), img))
    check("nenhum `image` NATIVO apontando para PNG inexistente", not quebrados,
          "; ".join(quebrados))
    if quebrados_custom:
        aviso(u"criaturas personalizadas com `image` sem PNG: %s" % "; ".join(quebrados_custom))

    print("\n[7] Prévia e teste abrem o cliente pelo servidor, nunca em file://")
    # Com o editor aberto por duplo clique, um caminho relativo faz o jogo abrir
    # em file:// — e aí o GLTFLoader (XHR) é bloqueado e NENHUM .glb carrega.
    # Foi essa a causa de "peões genéricos e objetos sem modelo" no teste.
    upload_js = io.open(os.path.join(BASE, "tools", "story_upload.js"),
                        encoding="utf-8", errors="replace").read()
    check("story_upload.js expõe EDITOR_CLIENTE.url",
          "window.EDITOR_CLIENTE" in upload_js and "clienteURL" in upload_js)
    for arq in ("editor_preview_3d.js", "editor.js"):
        js = io.open(os.path.join(BASE, "tools", arq), encoding="utf-8",
                     errors="replace").read()
        usa_helper = "EDITOR_CLIENTE.url(" in js
        check("%s usa EDITOR_CLIENTE.url" % arq, usa_helper,
              "voltou a montar o endereço na mão")

    if _avisos:
        print("\n⚠️  AVISOS (não falham o teste)")
        for a in _avisos:
            print("   - " + a)
    print("\n=== %d passou, %d falhou ===" % (_ok, _fail))
    return 1 if _fail else 0


if __name__ == "__main__":
    sys.exit(main())
