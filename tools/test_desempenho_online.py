"""Entrega dos arquivos pela internet: versao estavel dos scripts, cache da
arte fora do localhost, miniaturas (?w=) e PNG grande convertido em WebP.
Roda da raiz: python -X utf8 tools/test_desempenho_online.py"""
import gzip
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S

try:
    from PIL import Image, features
    TEM_WEBP = bool(features.check("webp"))
except Exception:                      # sem Pillow o servidor serve o original
    Image = None
    TEM_WEBP = False

FORA = {"Host": "mesa.trycloudflare.com"}
LOCAL = {"Host": "localhost:8765"}


class Pedido:
    def __init__(self, path, headers=None):
        self.path = path
        self.headers = dict(headers or {})


def corpo(resp):
    dados = resp.body or b""
    return gzip.decompress(dados) if resp.headers.get("Content-Encoding") == "gzip" else dados


class Base(unittest.TestCase):
    def setUp(self):
        self.raiz = tempfile.mkdtemp(prefix="lfh_online_")
        self.antiga = S.BASE_DIR
        S.BASE_DIR = self.raiz
        S._versao_memo.update(quando=0.0, base=None, valor="")
        os.makedirs(os.path.join(self.raiz, "src"))
        os.makedirs(os.path.join(self.raiz, "assets", "itens"))
        self.escrever("index.html", '<html>\n<head>\n<link href="game.css?v=antigo">'
                      '<script>var v=window.LFH_VER||Date.now();</script></head></html>')
        self.escrever("game.js", "console.log(1);" * 200)
        self.escrever("game.css", "body{}" * 300)
        self.escrever("src/gameState.js", "var a=1;" * 300)

    def tearDown(self):
        S.BASE_DIR = self.antiga
        S._versao_memo.update(quando=0.0, base=None, valor="")
        shutil.rmtree(self.raiz, ignore_errors=True)

    def escrever(self, rel, texto):
        with open(os.path.join(self.raiz, rel), "w", encoding="utf-8") as f:
            f.write(texto)

    def imagem(self, rel, lado=900, ruido=True):
        caminho = os.path.join(self.raiz, rel)
        im = Image.effect_noise((lado, lado), 80).convert("RGBA") if ruido \
            else Image.new("RGBA", (lado, lado), (200, 30, 30, 255))
        im.save(caminho, "PNG")
        return os.path.getsize(caminho)


class VersaoDoClienteTests(Base):
    def test_index_recebe_a_versao_e_os_scripts_ficam_imutaveis(self):
        r = S._serve_static(Pedido("/index.html", LOCAL))
        html = corpo(r).decode("utf-8")
        versao = S._versao_cliente()
        self.assertIn(f'window.LFH_VER="{versao}"', html)
        self.assertIn(f"game.css?v={versao}", html)
        self.assertEqual(r.headers["Cache-Control"], "no-cache")
        for caminho in ("/game.js", "/src/gameState.js", "/game.css"):
            r = S._serve_static(Pedido(f"{caminho}?v={versao}", LOCAL))
            self.assertIn("immutable", r.headers["Cache-Control"], caminho)

    def test_versao_errada_ou_ausente_nao_fica_imutavel(self):
        for caminho in ("/game.js?v=123", "/game.js"):
            r = S._serve_static(Pedido(caminho, FORA))
            self.assertEqual(r.headers["Cache-Control"], "no-cache", caminho)

    def test_mudar_um_script_muda_a_versao_e_o_etag_do_index(self):
        antes = S._versao_cliente()
        etag = S._serve_static(Pedido("/index.html", LOCAL)).headers["ETag"]
        self.assertEqual(S._serve_static(Pedido(
            "/index.html", dict(LOCAL, **{"If-None-Match": etag}))).status, 304)
        self.escrever("src/gameState.js", "var a=2;" * 301)
        S._versao_memo.update(quando=0.0)
        self.assertNotEqual(S._versao_cliente(), antes)
        r = S._serve_static(Pedido("/index.html", dict(LOCAL, **{"If-None-Match": etag})))
        self.assertEqual(r.status, 200)
        self.assertNotIn("Last-Modified", r.headers)


class CacheDaArteTests(Base):
    def test_arte_so_ganha_validade_fora_do_localhost(self):
        self.escrever("assets/itens/a.png", "x" * 50)
        fora = S._serve_static(Pedido("/assets/itens/a.png", FORA))
        self.assertIn("stale-while-revalidate", fora.headers["Cache-Control"])
        for host in ("localhost:8765", "127.0.0.1:8765", "[::1]:8765"):
            r = S._serve_static(Pedido("/assets/itens/a.png", {"Host": host}))
            self.assertEqual(r.headers["Cache-Control"], "no-cache", host)


@unittest.skipUnless(Image, "Pillow nao instalado")
class MiniaturaTests(Base):
    def test_largura_pedida_devolve_imagem_menor_e_fica_em_disco(self):
        tamanho = self.imagem("assets/itens/espada.png")
        r = S._serve_static(Pedido("/assets/itens/espada.png?w=192", LOCAL))
        self.assertEqual(r.status, 200)
        self.assertLess(len(r.body), tamanho // 4)
        self.assertTrue(r.headers["ETag"].endswith('-w192"'))
        import io
        self.assertEqual(Image.open(io.BytesIO(r.body)).width, 192)
        self.assertTrue(os.listdir(os.path.join(self.raiz, ".cache", "miniaturas")))
        de_novo = S._serve_static(Pedido("/assets/itens/espada.png?w=192", LOCAL))
        self.assertEqual(de_novo.body, r.body)

    def test_largura_fora_da_lista_e_fora_de_assets_servem_o_original(self):
        tamanho = self.imagem("assets/itens/espada.png")
        r = S._serve_static(Pedido("/assets/itens/espada.png?w=193", LOCAL))
        self.assertEqual(len(r.body), tamanho)
        self.assertEqual(r.headers["Content-Type"], "image/png")

    def test_imagem_que_nao_encolhe_vai_original(self):
        tamanho = self.imagem("assets/itens/pequena.png", lado=64)
        r = S._serve_static(Pedido("/assets/itens/pequena.png?w=192", LOCAL))
        self.assertEqual(len(r.body), tamanho)

    @unittest.skipUnless(TEM_WEBP, "Pillow sem WebP")
    def test_png_grande_vira_webp_so_para_quem_aceita(self):
        tamanho = self.imagem("assets/itens/fundo.png", lado=1000)
        self.assertGreater(tamanho, S._REENC_MIN_BYTES)
        aceita = S._serve_static(Pedido("/assets/itens/fundo.png",
                                        dict(FORA, Accept="image/avif,image/webp,*/*")))
        self.assertEqual(aceita.headers["Content-Type"], "image/webp")
        self.assertEqual(aceita.headers["Vary"], "Accept")
        self.assertLess(len(aceita.body), tamanho)
        import io
        self.assertEqual(Image.open(io.BytesIO(aceita.body)).size, (1000, 1000))
        nao = S._serve_static(Pedido("/assets/itens/fundo.png", dict(FORA, Accept="image/png")))
        self.assertEqual(nao.headers["Content-Type"], "image/png")
        self.assertEqual(len(nao.body), tamanho)
        self.assertNotEqual(aceita.headers["ETag"], nao.headers["ETag"])


class ClienteTests(unittest.TestCase):
    def test_cliente_usa_a_versao_carimbada_e_pede_icone_reduzido(self):
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        index = open(os.path.join(raiz, "index.html"), encoding="utf-8").read()
        self.assertNotIn("var v=Date.now()", index)
        self.assertEqual(index.count("window.LFH_VER||Date.now()"), 2)
        jogo = open(os.path.join(raiz, "game.js"), encoding="utf-8").read()
        self.assertIn("const _ASSET_VER = window.LFH_VER || Date.now();", jogo)
        self.assertIn("'w=192'", jogo)
        self.assertNotIn(".glb?v=${Date.now()}", jogo)


if __name__ == "__main__":
    unittest.main()
