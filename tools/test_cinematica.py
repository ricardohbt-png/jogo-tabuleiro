"""Cinemática cartum nos slides de história (src/cinematica.js) e a cena da morte do Gilo na Praça viva.
Roda da raiz: python -X utf8 tools/test_cinematica.py"""
import os
import shutil
import subprocess
import sys
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ); sys.path.insert(0, os.path.join(RAIZ, "tools"))
import server as S
import gerar_elara_graciero as GG


class SlideTests(unittest.TestCase):
    def test_slide_so_com_cinematica_vale(self):
        n = S._story_norm({"slides": [{"cinematica": "gilo_morte"}]})
        self.assertEqual(n["slides"][0]["cinematica"], "gilo_morte")

    def test_cinematica_desconhecida_e_descartada(self):
        self.assertEqual(S._story_norm({"slides": [{"cinematica": "nao_existe"}]})["slides"], [])
        ok, _ = S._validar_story({"slides": [{"cinematica": "nao_existe", "text": "x"}]}, "t")
        self.assertFalse(ok)

    def test_validar_e_gravar_preservam(self):
        campo = {"slides": [{"cinematica": "gilo_morte", "text": "legenda"}]}
        self.assertTrue(S._validar_story(campo, "t")[0])
        self.assertEqual(S._clean_story_field(campo)["slides"][0]["cinematica"], "gilo_morte")

    def test_story_beat_entrega_a_cinematica_ao_cliente(self):
        b = S._story_beat("k", [{"slides": [{"cinematica": "gilo_morte", "text": "t"}]}])
        self.assertEqual(b["slides"][0]["cinematica"], "gilo_morte")


class PracaVivaTests(unittest.TestCase):
    def test_so_quem_viu_o_gilo_cair_assiste(self):
        d = GG.destinos()["elara_graciero_praca_viva"]
        outro = d["dungeons"][0]["outro"]
        self.assertEqual(outro["slides"][0]["cinematica"], "gilo_morte")
        viu = S._story_beat("k", [outro], lambda r: r.get("fato") == "elara_viu_gilo_morrer")
        nao = S._story_beat("k", [outro], lambda r: False)
        self.assertEqual(viu["slides"][0]["cinematica"], "gilo_morte")
        self.assertIsNone(nao)

    def test_praca_morta_nao_tem_cinematica(self):
        d = GG.destinos()["elara_graciero_praca_morta"]
        self.assertEqual(d["dungeons"][0]["outro"], "")

    def test_gravado_em_disco(self):
        import json
        with open(os.path.join(RAIZ, "world_adventures.json"), encoding="utf-8") as f:
            d = json.load(f)["elara_graciero_praca_viva"]
        self.assertEqual(d["dungeons"][0]["outro"]["slides"][0]["cinematica"], "gilo_morte")


@unittest.skipUnless(shutil.which("node"), "node ausente")
class ModuloTests(unittest.TestCase):
    def test_desenha_o_roteiro_inteiro_sem_erro(self):
        js = r"""
        const fs = require('fs'); global.window = global;
        eval(fs.readFileSync('src/cinematica.js', 'utf8'));
        const chamadas = [];
        const ctx = new Proxy({}, { get: (a, k) => k === 'measureText' ? () => ({width: 100})
            : k === 'createLinearGradient' || k === 'createRadialGradient' ? () => ({addColorStop(){}})
            : (typeof k === 'string' ? (...x) => { chamadas.push(k); } : undefined), set: () => true });
        const ids = Cinematica.ids; if (!ids.includes('gilo_morte')) throw new Error('sem gilo_morte');
        const dur = Cinematica.duracao('gilo_morte');
        for (let t = 0; t <= dur + 1; t += 0.25) Cinematica.desenhar(ctx, 1280, 720, t, {falas: ['a','b','c','d'], tec: 'T'}, 'gilo_morte');
        Cinematica.desenhar(ctx, 100, 100, 5, null, 'id_que_nao_existe');
        console.log(dur, chamadas.length > 1000 ? 'ok' : 'poucas');
        """
        r = subprocess.run(["node", "-e", js], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ok", r.stdout)


if __name__ == "__main__":
    unittest.main()
