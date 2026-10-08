"""Gera src/lang/tutorial_guia.js e injeta `guia` nas lições da trilha comum.

Uso (da raiz): python tools/gerar_guia_comum.py
"""
import importlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import tutorial_guia_comum as C

JSON_CAMPO = RAIZ / "dungeons" / "campo_de_treinamento.json"
LANG_JS = RAIZ / "src" / "lang" / "tutorial_guia.js"

# Módulos de conteúdo por classe. Um módulo ausente é ignorado (permite entregar por partes).
MODULOS_CLASSES = ("tutorial_guia_guerreiro", "tutorial_guia_mago", "tutorial_guia_ladino",
                   "tutorial_guia_clerigo", "tutorial_guia_bardo", "tutorial_guia_paladino")


def modulos_de_guia():
    """Lista de dicts {lição_id: [passos]}: trilha comum + um por classe presente."""
    mods = [C.GUIA]
    for nome in MODULOS_CLASSES:
        try:
            mod = importlib.import_module(nome)
        except ModuleNotFoundError as e:
            if e.name != nome:
                raise
            continue
        mods.append(mod.GUIA)
    return mods


def guia_todos():
    """{lição_id: [passos]} de TODOS os módulos (trilha comum + classes)."""
    out = {}
    for guia in modulos_de_guia():
        for lid, passos in guia.items():
            if lid in out:
                raise ValueError(f"lição repetida entre módulos: {lid}")
            out[lid] = passos
    return out


def _chave(lic, passo_id, campo, n=None):
    base = f"ui.tutorial.guia.{lic}.{passo_id}.{campo}"
    return base if n is None else f"{base}.{n}"


def gerar_lang():
    """{chave: {pt, en}} de todo o guia e do glossário."""
    out = {}
    for lic, passos in guia_todos().items():
        for p in passos:
            out[_chave(lic, p["id"], "texto")] = dict(zip(("pt", "en"), p["texto"]))
            if p.get("porque"):
                out[_chave(lic, p["id"], "porque")] = dict(zip(("pt", "en"), p["porque"]))
            for n, d in enumerate(p.get("dica", []), 1):
                out[_chave(lic, p["id"], "dica", n)] = dict(zip(("pt", "en"), d))
    for termo, v in C.GLOSSARIO.items():
        for campo in ("nome", "texto"):
            out[f"ui.tutorial.glossario.{termo}.{campo}"] = dict(zip(("pt", "en"), v[campo]))
    return out


def render_lang():
    corpo = json.dumps(gerar_lang(), ensure_ascii=False, indent=2, sort_keys=True)
    return ("// GERADO por tools/gerar_guia_comum.py a partir de tools/tutorial_guia_comum.py. Não edite à mão.\n"
            "window.LANG_TUTORIAL_GUIA = " + corpo + ";\n"
            "Object.assign(window.LANG_STRINGS, window.LANG_TUTORIAL_GUIA);\n")


def aplicar_guia(d):
    """Grava `guia` (só chaves de idioma) nas falas da trilha comum de `d` (dict da masmorra)."""
    _TODOS = guia_todos()
    for f in d["falas"]:
        passos = _TODOS.get(f["id"])
        if not passos:
            continue
        guia = []
        for p in passos:
            s = {"id": p["id"], "texto": _chave(f["id"], p["id"], "texto")}
            if p.get("porque"):
                s["porque"] = _chave(f["id"], p["id"], "porque")
            if p.get("ui"):
                s["ui"] = p["ui"]
            if p.get("dica"):
                s["dica"] = [_chave(f["id"], p["id"], "dica", n) for n in range(1, len(p["dica"]) + 1)]
            if p.get("conclui"):
                s["conclui_com"] = p["conclui"]
            guia.append(s)
        f["guia"] = guia
    return d


def main():
    LANG_JS.write_text(render_lang(), encoding="utf-8", newline="\n")
    d = json.loads(JSON_CAMPO.read_text(encoding="utf-8"))
    aplicar_guia(d)
    JSON_CAMPO.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")  # arquivo versionado não tem \n final
    print(f"ok: {len(gerar_lang())} chaves; {len(guia_todos())} lições com guia")


if __name__ == "__main__":
    main()
