"""Avisos pessoais de teia, cola e piche, sem alterar suas regras."""
import asyncio
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


class AvisosPrisao(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = server.GameRoom("PRISAO_TEST")
        self.hero = server.make_player("h1", "Teste", "warrior", 0)
        self.hero.update(pos=[3, 3], alive=True, hp=20)
        self.room.players = {"h1": self.hero}
        self.room.phase = "playing"
        self.sent = []

        async def capture(pid, msg):
            self.sent.append((pid, msg))

        async def noop(*args, **kwargs):
            pass

        self.room.send_to = capture
        self.room.broadcast = noop
        self.room.gm_say = noop
        self.room._aplicar_queda = noop

    async def test_teia_falha_avisa_so_alvo(self):
        spider = {"id": "spider", "name": "Aranha", "ability_uses": {}}
        ability = dict(next(d for d in server.MONSTER_DEFS if d["type"] == "aranha_sombria")["special_abilities"][0])
        self.room._testar_save = lambda *a, **k: (False, 1, 0, 1)
        await self.room._use_monster_ability(spider, ability, {"kind": "player", "obj": self.hero})
        notices = [m for pid, m in self.sent if m.get("tipo") == "prisao"]
        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0]["prisao_id"], "teia")
        self.assertEqual(notices[0]["duracao"], 1)
        self.assertTrue(self.hero["perde_turno"])

    async def test_teia_resistida_nao_avisa(self):
        ability = {"id": "disparo_teia", "name": "Teia", "save": "reflexos", "dc": 11, "effect": "perde_turno"}
        self.room._testar_save = lambda *a, **k: (True, 20, 0, 20)
        await self.room._use_monster_ability({"id": "spider", "name": "Aranha"}, ability, {"kind": "player", "obj": self.hero})
        self.assertFalse(self.sent)

    async def test_cola_duracao_sem_repetir_por_tick(self):
        self.hero.update(cola_sem_movimento=True, mov_reduzido_rodadas=3)
        await self.room._avisar_prisoes_aderentes()
        self.assertEqual(self.sent[0][1]["duracao"], 3)
        self.hero["mov_reduzido_rodadas"] = 2
        await self.room._avisar_prisoes_aderentes()
        self.assertEqual(len(self.sent), 1)
        self.hero.pop("cola_sem_movimento")
        await self.room._avisar_prisoes_aderentes()
        self.hero["cola_sem_movimento"] = True
        await self.room._avisar_prisoes_aderentes()
        self.assertEqual(len(self.sent), 2)

    async def test_piche_entrada_saida_nova_entrada(self):
        self.room.materiais = {(3, 3): "piche"}
        await self.room._avisar_prisoes_aderentes()
        self.assertEqual(self.sent[0][1]["prisao_id"], "piche")
        await self.room._avisar_prisoes_aderentes()
        self.assertEqual(len(self.sent), 1)
        self.hero["pos"] = [4, 3]
        await self.room._avisar_prisoes_aderentes()
        self.hero["pos"] = [3, 3]
        await self.room._avisar_prisoes_aderentes()
        self.assertEqual(len(self.sent), 2)

    async def test_rede_e_outros_estados_nao_disparam(self):
        self.hero.update(enredado=True, preso=True, paralisado=True, perde_turno=True)
        await self.room._avisar_prisoes_aderentes()
        self.assertFalse(self.sent)

    async def test_piche_voo_ponte_e_cidade_nao_avisam(self):
        self.room.materiais = {(3, 3): "piche"}
        self.room._voo_imune_terreno = lambda p: True
        await self.room._avisar_prisoes_aderentes()
        self.assertFalse(self.sent)
        self.room._voo_imune_terreno = lambda p: False
        self.room._ponte_em = lambda *a: True
        await self.room._avisar_prisoes_aderentes()
        self.assertFalse(self.sent)
        self.room._ponte_em = lambda *a: False
        self.hero["fora_masmorra"] = True
        await self.room._avisar_prisoes_aderentes()
        self.assertFalse(self.sent)

    async def test_push_state_dispara_aviso_e_nao_repete(self):
        self.room.materiais = {(3, 3): "piche"}
        await self.room.push_state()
        await self.room.push_state()
        notices = [m for _, m in self.sent if m.get("tipo") == "prisao"]
        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0]["prisao_id"], "piche")

    async def test_mesma_arte_e_apenas_herois(self):
        for kind in ("teia", "cola", "piche"):
            await self.room._enviar_resultado_prisao(self.hero, kind, 2)
        self.assertEqual({m["imagem"] for _, m in self.sent}, {"preso.png"})
        self.assertEqual({pid for pid, _ in self.sent}, {"h1"})
        await self.room._enviar_resultado_prisao({"id": "monster"}, "cola", 2)
        self.assertEqual(len(self.sent), 3)

    def captor(self, aid="agarrar", dc=12, saves=None):
        ability = {"id": aid, "dc": dc}
        if saves is not None:
            ability["escape_saves"] = saves
        monster = {"id": "c1", "name": "Crocodilo", "hp": 30,
                   "special_abilities": [ability], "pos": [4, 3]}
        self.room.monsters = {"c1": monster}
        self.hero.update(preso=True, preso_por="c1")
        return monster

    async def test_derrubado_lobo_turno_atual(self):
        wolf = {"id": "wolf", "name": "Lobo", "hp": 20,
                "special_abilities": [{"id": "derrubar", "dc": 11}]}
        self.room._testar_save = lambda *a, **k: (False, 1, 0, 1)
        self.hero["moves_left"] = 5
        await self.room._lobo_derrubar(wolf, {"kind": "player", "obj": self.hero}, True)
        self.assertEqual(self.hero["moves_left"], 0)
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.sent[0][1]["tipo"], "derrubado")
        self.assertEqual(self.sent[0][1]["turno_efeito"], "atual")
        self.assertEqual(self.sent[0][1]["imagem"], "derrubado.png")

    async def test_derrubado_lobo_resistiu_ou_errou_sem_aviso(self):
        wolf = {"id": "wolf", "name": "Lobo", "hp": 20,
                "special_abilities": [{"id": "derrubar", "dc": 11}]}
        self.room._testar_save = lambda *a, **k: (True, 20, 0, 20)
        await self.room._lobo_derrubar(wolf, {"kind": "player", "obj": self.hero}, True)
        await self.room._lobo_derrubar(wolf, {"kind": "player", "obj": self.hero}, False)
        self.assertFalse(self.sent)

    async def test_derrubado_cauda_proximo_turno(self):
        attack = {"name": "Cauda"}
        monster = {"id": "rex", "name": "Tirano", "hp": 20, "attacks": [{"name": "Mordida"}, attack],
                   "special_abilities": [{"id": "cauda_derrubadora", "attack_index": 1, "dc": 16}]}
        self.room._testar_save = lambda *a, **k: (False, 1, 0, 1)
        await self.room._cauda_derrubadora_no_acerto(monster, self.hero, attack)
        self.assertTrue(self.hero["derrubado_sem_movimento"])
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.sent[0][1]["turno_efeito"], "proximo")
        self.assertEqual(self.sent[0][1]["fonte"], "Tirano")
        await self.room.push_state()
        self.assertEqual(len([m for _, m in self.sent if m.get("tipo") == "derrubado"]), 1)

    async def test_derrubado_monstro_nao_recebe_popup(self):
        await self.room._enviar_resultado_derrubado({"id": "monster", "hp": 20}, "Monstro", "proximo")
        self.assertFalse(self.sent)

    async def test_derrubado_cauda_varredora_falha_e_resistencia(self):
        monster = {"id": "tail", "name": "Grotão", "hp": 20}
        async def damage(*args, **kwargs):
            pass
        self.room._aplicar_dano_alvo = damage
        ability = {"damage": "1", "dc": 12}
        with patch.object(server, "d20_attack", return_value=(True, 15, 20, False)):
            self.room._testar_save = lambda *a, **k: (False, 1, 0, 1)
            await self.room._usar_cauda_varredora(monster, [{"kind": "player", "obj": self.hero}], ability)
            self.assertTrue(self.hero["derrubado_sem_movimento"])
            self.assertEqual(len(self.sent), 1)
            self.assertEqual(self.sent[0][1]["turno_efeito"], "proximo")
            self.room._testar_save = lambda *a, **k: (True, 20, 0, 20)
            await self.room._usar_cauda_varredora(monster, [{"kind": "player", "obj": self.hero}], ability)
            self.assertEqual(len(self.sent), 1)

    async def test_agarrado_push_privado_dados_e_sem_repeticao(self):
        self.captor()
        await self.room.push_state()
        await self.room.push_state()
        notices = [(pid, m) for pid, m in self.sent if m.get("tipo") == "agarrado"]
        self.assertEqual(len(notices), 1)
        pid, msg = notices[0]
        self.assertEqual(pid, "h1")
        self.assertEqual(msg["imagem"], "agarrado.png")
        self.assertEqual(msg["escape_dc"], 12)
        self.assertEqual(msg["escape_saves"], ["fortitude", "reflexos"])
        self.assertEqual(msg["captor"], "Crocodilo")

    async def test_constricao_cd_especifica_escape_e_reagarrar(self):
        m = self.captor("constricao", 11, ["forca"])
        m["special_abilities"][0]["escape_dc"] = 15
        await self.room._avisar_agarrados()
        self.assertEqual(self.sent[0][1]["escape_dc"], 15)
        self.assertEqual(self.sent[0][1]["escape_saves"], ["forca"])
        self.room._testar_save = lambda *a, **k: (True, 20, 0, 20)
        await self.room._processar_escape_agarrar(self.hero)
        await self.room._avisar_agarrados()
        self.hero.update(preso=True, preso_por="c1")
        await self.room._avisar_agarrados()
        self.assertEqual(len(self.sent), 2)

    async def test_agarrado_sem_captor_vivo_ou_fora_nao_avisa(self):
        m = self.captor()
        m["hp"] = 0
        await self.room._avisar_agarrados()
        self.assertFalse(self.sent)
        m["hp"] = 30
        self.hero["fora_masmorra"] = True
        await self.room._avisar_agarrados()
        self.assertFalse(self.sent)

    async def test_agarrado_troca_captor_e_cobre_todas_habilidades(self):
        for aid in ("agarrar_aereo", "agarrar_lacralion", "mandibulas_colossais",
                    "tentaculos_imobilizar", "constricao_charcos", "onda_envolvente", "salto_selvagem"):
            m = self.captor(aid, 19, ["vontade"])
            m["id"] = aid
            self.room.monsters = {aid: m}
            self.hero["preso_por"] = aid
            await self.room._avisar_agarrados()
            self.assertEqual(self.sent[-1][1]["escape_dc"], 19)
            self.assertEqual(self.sent[-1][1]["escape_saves"], ["vontade"])
        self.assertEqual(len(self.sent), 7)


if __name__ == "__main__":
    unittest.main()
