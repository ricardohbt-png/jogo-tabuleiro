"""Textos das fichas de monstro e maldições em inglês.
Roda da raiz: python -X utf8 tools/test_textos_monstros.py"""
import asyncio
import json
import os
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_textos_monstros as G


class DicionarioTests(unittest.TestCase):
    def test_todo_texto_nativo_tem_ingles(self):
        faltam = [pt for pt in G.coletar(S.MONSTER_DEFS)
                  if not (S.LANG_STRINGS.get(G.chave_de(pt)) or {}).get("en")]
        self.assertEqual(faltam, [], "rode tools/gerar_textos_monstros.py e traduza")

    def test_toda_maldicao_tem_nome_e_efeito(self):
        for mid in S.MALDICOES:
            for k in (f"ui.maldicao.{mid}", f"ui.maldicao.{mid}.ef"):
                self.assertTrue((S.LANG_STRINGS.get(k) or {}).get("en"), k)


class ServidorTests(unittest.TestCase):
    def test_parametro_cru_de_habilidade_traduz(self):
        self.assertEqual(S._param_texto("Mordida", "en"), "Bite")
        self.assertEqual(S._param_texto("Mordida", "pt"), "Mordida")
        self.assertEqual(S._param_texto("Nome do Autor", "en"), "Nome do Autor")

    def test_popup_de_maldicao_em_ingles(self):
        r = S.GameRoom("MAL")
        r.players["p0"] = S.make_player("p0", "Ana", "warrior", 0)
        enviados = []

        async def send_to(pid, msg): enviados.append(msg)
        r.send_to = send_to
        asyncio.run(r._enviar_resultado_maldicao(r.players["p0"], "maos_tremulas", fonte="armadilha"))
        msg = enviados[0]
        self.assertEqual(S.t(msg["nome"].key, "en"), "Trembling Hands")
        extras_en = [S._param_texto(x, "en") for x in msg["efeitos_extra"]]
        self.assertTrue(any("Triggered by a trap" in x for x in extras_en), extras_en)
        self.assertTrue(all(not any(c in x for c in "ãçé") for x in extras_en), extras_en)


class ClienteTests(unittest.TestCase):
    def test_filtro_troca_so_texto_nativo(self):
        js = r"""
global.window = {LANG_STRINGS: {}};
for (const f of ['strings','catalogo','composto','interface','monstros']) require('./src/lang/' + f + '.js');
require('./src/i18n.js');
const I = window.I18N; I.setLang('en');
const msg = {monsters: [{type: 'zz', name: 'X', special_abilities: [
  {id: 'bola_fogo', name: 'Bola de Fogo', descricao: 'Igual à magia Bola de Fogo, conjurador de 6º nível; 1 vez por encontro.'},
  {id: 'autoral', name: 'Golpe do Autor', descricao: 'Texto do autor.'}],
  weaknesses: [{descricao: 'Resistência a perfurante (-2 dano)'}],
  attacks: [{name: 'Mordida'}]}],
  players: [{id: 'p', class_id: 'warrior', name: 'Mordida'}]};
I.traduzirNomes(msg);
console.log(JSON.stringify(msg));
"""
        out = subprocess.run(["node", "-e", js], cwd=RAIZ, capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        m = json.loads(out.stdout.strip().splitlines()[-1])
        ab = m["monsters"][0]["special_abilities"]
        self.assertEqual(ab[0]["descricao"], "Same as the Fireball spell, 6th-level caster; once per encounter.")
        self.assertEqual(ab[1]["name"], "Golpe do Autor")
        self.assertEqual(m["monsters"][0]["weaknesses"][0]["descricao"], "Resistance to piercing (-2 damage)")
        self.assertEqual(m["monsters"][0]["attacks"][0]["name"], "Bite")
        self.assertEqual(m["players"][0]["name"], "Mordida", "nome de herói não se traduz")


if __name__ == "__main__":
    unittest.main()
