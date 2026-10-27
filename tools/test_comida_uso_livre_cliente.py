"""Comida é de uso livre: o cliente não pode tratar o Banquete de Viagem como ação bônus.
O servidor (handle_use_item) exclui food/meal_survival do limite de ação bônus; se o cliente
os listar em BONUS_ACTION_EFFECTS, a bolsa bloqueia o item quando a ação bônus já foi usada.
Roda da raiz: python -X utf8 tools/test_comida_uso_livre_cliente.py
"""
import os
import re
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ler(rel):
    with open(os.path.join(RAIZ, rel), encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


class ComidaLivreTests(unittest.TestCase):
    def test_cliente_nao_trata_comida_como_acao_bonus(self):
        js = ler("game.js")
        bloco = re.search(r"const BONUS_ACTION_EFFECTS = new Set\(\[(.*?)\]\);", js, re.S).group(1)
        efeitos = set(re.findall(r"'([a-z_]+)'", bloco))
        servidor = ler("server.py")
        livres = re.search(r"effect not in \{([^}]*)\}:\s*\n\s*#[^\n]*\n\s*#[^\n]*\n\s*ok = await self\._executar_acao_bonus", servidor)
        self.assertIsNotNone(livres, "o servidor deixou de listar as comidas livres")
        livres = set(re.findall(r'"([a-z_]+)"', livres.group(1)))
        self.assertTrue({"food", "meal_survival"} <= livres)
        self.assertEqual(efeitos & livres, set(), "comida marcada como ação bônus no cliente")


if __name__ == "__main__":
    unittest.main()
