"""Maça do Voto Guardião, Espada do Juramento Inquebrantável e Espadas do Veredito Radiante.

Cobre o catálogo (preço, classe, bônus, variantes de material, arte, ferrarias)
e as três habilidades: cura opcional após o acerto (Clérigo), reação que reduz o
dano de um aliado (Paladino) e dano sagrado opcional/automático (Paladino).
Roda da raiz:  python -X utf8 tools/test_armas_voto_juramento_veredito.py
"""
import asyncio
import json
import os
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server as S

MACA = "maca_voto_guardiao"
JURAMENTO = "espada_juramento_inquebrantavel"
VEREDITO1 = "espada_bastarda_veredito_radiante_mais_1"
VEREDITO3 = "espada_bastarda_veredito_radiante_mais_3"
MATERIAIS = ("aco_damasco", "obsidiana_ferro", "liga_titanio")


def shop(item_id):
    return next(i for i in S.SHOP_WEAPONS if i["id"] == item_id)


class CatalogoTests(unittest.TestCase):
    def test_precos_e_classes(self):
        esperado = {MACA: (1600, ["cleric"]), JURAMENTO: (2000, ["paladin"]),
                    VEREDITO1: (3000, ["paladin"]), VEREDITO3: (8000, ["paladin"])}
        for item_id, (preco, classes) in esperado.items():
            it = shop(item_id)
            self.assertEqual(it["price"], preco, item_id)
            self.assertEqual(it["allowed_classes"], classes, item_id)
            self.assertTrue(it["magical"], item_id)
            self.assertIn(item_id, S.WEAPONS, item_id)

    def test_perfil_de_combate(self):
        self.assertEqual((shop(MACA)["die"], shop(MACA)["crit_nat20_multiplier"]), ("1d8", 3))
        self.assertNotIn("atk_bonus", shop(MACA))
        self.assertEqual((shop(JURAMENTO)["die"], shop(JURAMENTO)["crit_min_nat_roll"]), ("1d8", 19))
        v1, v3 = shop(VEREDITO1), shop(VEREDITO3)
        self.assertEqual((v1["atk_bonus"], v1["damage_bonus"]), (1, 1))
        self.assertEqual((v3["atk_bonus"], v3["damage_bonus"]), (3, 3))
        self.assertEqual((v1["die"], v1["crit_min_nat_roll"]), ("1d10", 19))
        self.assertFalse(v1.get("veredito_radiante_critico"))
        self.assertTrue(v3.get("veredito_radiante_critico"))
        for v in (v1, v3):
            self.assertEqual(v["veredito_radiante_dano"], "2d8")
            self.assertEqual(v["veredito_radiante_cooldown"], 10)

    def test_variantes_de_material(self):
        for base in (MACA, JURAMENTO):
            preco_base = shop(base)["price"]
            hab = "voto_guardiao" if base == MACA else "protecao_juramento"
            for mat in MATERIAIS:
                it = shop(f"{base}_{mat}")
                self.assertEqual(it["allowed_classes"], shop(base)["allowed_classes"], it["id"])
                self.assertTrue(it.get(hab), f"{it['id']} perdeu a habilidade")
                self.assertTrue(it["magical"], it["id"])
            aco = shop(f"{base}_aco_damasco")
            self.assertEqual(aco["price"], preco_base + 20)
            self.assertEqual(aco.get("atk_bonus"), 1)
            self.assertEqual(aco.get("corrosao_resistente"), 1)
            obs = shop(f"{base}_obsidiana_ferro")
            self.assertEqual(obs.get("damage_bonus"), 1)
            self.assertEqual(obs["price"], preco_base + 20)
            tit = shop(f"{base}_liga_titanio")
            self.assertEqual(tit["price"], preco_base + 30)
            self.assertEqual((tit.get("corrosao_resistente"), tit.get("corrosao_niveis_penalidade")), (2, 3))
            self.assertFalse(tit.get("atk_bonus") or tit.get("damage_bonus"))
            prata = shop(f"{base}_prata")
            self.assertEqual(prata["price"], preco_base * 10)
            self.assertTrue(prata["silver"])
            self.assertEqual((prata["corrosion_max"], prata["corrosion_free_levels"]), (2, 1))
            self.assertTrue(prata.get(hab))
            self.assertEqual(prata["allowed_classes"], shop(base)["allowed_classes"])

    def test_variantes_chegam_ao_combate(self):
        for base in (MACA, JURAMENTO):
            for suf in MATERIAIS + ("prata",):
                self.assertIn(f"{base}_{suf}", S.WEAPONS)
        self.assertTrue(S.WEAPONS[f"{MACA}_prata"]["silver"])
        self.assertTrue(S.WEAPONS[f"{JURAMENTO}_prata"].get("protecao_juramento"))

    def test_arte_existe_em_disco(self):
        ids = [MACA, JURAMENTO, VEREDITO1, VEREDITO3]
        ids += [f"{b}_{s}" for b in (MACA, JURAMENTO) for s in MATERIAIS + ("prata",)]
        for item_id in ids:
            icone = shop(item_id)["icon"]
            self.assertTrue((ROOT / icone).is_file(), f"{item_id}: falta {icone}")

    def test_nas_cinco_ferrarias(self):
        dados = json.loads((ROOT / "city_shops.json").read_text(encoding="utf8"))
        ids = [MACA, JURAMENTO, VEREDITO1, VEREDITO3]
        ids += [f"{b}_{s}" for b in (MACA, JURAMENTO) for s in MATERIAIS + ("prata",)]
        cidades = dados.get("cities") or dados
        ferrarias = 0
        for cidade, lojas in cidades.items():
            lista = (lojas or {}).get("ferreiro_weapon")
            if lista is None:
                continue
            ferrarias += 1
            for item_id in ids:
                self.assertIn(item_id, lista, f"{item_id} fora do ferreiro de {cidade}")
        self.assertEqual(ferrarias, 5)

    def test_campos_de_regra_sobrevivem_a_compra(self):
        """Os campos da habilidade têm de estar nas listas que a compra e o combate copiam."""
        fonte = (ROOT / "server.py").read_text(encoding="utf8")
        for campo in ("voto_guardiao", "voto_guardiao_cooldown", "protecao_juramento",
                      "protecao_juramento_die", "veredito_radiante", "veredito_radiante_dano",
                      "veredito_radiante_cooldown", "veredito_radiante_critico"):
            self.assertGreaterEqual(fonte.count(f'"{campo}"'), 3, campo)


class Base(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.room = S.GameRoom("ARMAS_TEST")
        self.room.phase = "playing"
        self.room.round_num = 3
        self.room.tiles = [[S.FLOOR] * S.MAP_W for _ in range(S.MAP_H)]
        self.msgs = []

        async def noop(*a, **k):
            pass

        async def capture(*a, **k):
            self.msgs.append(a[-1])

        self.room.push_state = self.room.broadcast_city_state = noop
        self.room.gm_say = noop
        self.room.broadcast = self.room.send_to = capture
        self.room._is_turn = lambda pid: True
        self.room._tem_linha_de_visao = lambda *a: True
        self.room._apply_damage_types = lambda dmg, *a, **k: dmg
        definicao = next(m for m in S.MONSTER_DEFS if m["type"] == "urso_negro")
        self.alvo = S.make_monster(definicao, {"id": 1, "cx": 6, "cy": 5})
        self.alvo.update(pos=[6, 5], hp=500, max_hp=500, ac=10)
        self.room.monsters[self.alvo["id"]] = self.alvo

    def heroi(self, pid, classe, pos, item_id=None, hp=None):
        p = S.make_player(pid, pid, classe, 0)
        p.update(pos=list(pos), action_done=False, bonus_action_used=False, fome=80, sede=80,
                 connected=True, alive=True)
        p["bag"] = []
        if hp is not None:
            p["hp"] = hp
        if item_id:
            arma = deepcopy(shop(item_id))
            p["gear"]["weapon"] = arma
            self.room._sincronizar_arma_de_combate(p, arma)
        self.room.players[pid] = p
        self.room.connections[pid] = object()
        return p

    def tipos(self, tipo):
        return [m for m in self.msgs if isinstance(m, dict) and m.get("type") == tipo]

    async def atacar(self, pid, acerta=True, critico=False):
        with patch.object(S, "d20_attack", return_value=(acerta, 12 if not critico else 20, 20, critico)), \
                patch.object(S, "roll_dice", return_value=4):
            await self.room.handle_attack(pid, self.alvo["id"])


class VotoGuardiaoTests(Base):
    async def test_acerto_oferece_cura_a_aliado_ferido_e_inicia_recarga(self):
        cl = self.heroi("cl", "cleric", (5, 5), MACA)
        ali = self.heroi("ali", "warrior", (4, 5), hp=1)
        ali["max_hp"] = 20
        await self.atacar("cl")
        prompts = self.tipos("voto_guardiao_prompt")
        self.assertEqual(len(prompts), 1)
        ids = [t["id"] for t in prompts[0]["targets"]]
        self.assertIn("ali", ids)
        req = prompts[0]["request_id"]
        with patch.object(S, "roll_dice", return_value=4):
            await self.room.handle_voto_guardiao_choice("cl", {"request_id": req, "target_id": "ali"})
        self.assertEqual(ali["hp"], 5)
        pronta = cl["gear"]["weapon"]["voto_guardiao_ready_round"]
        self.assertEqual(pronta, self.room.round_num + 10)
        self.assertEqual(cl["weapon"]["voto_guardiao_ready_round"], pronta)
        self.assertNotIn("voto_guardiao_pending", cl)

    async def test_cura_nao_passa_do_maximo(self):
        cl = self.heroi("cl", "cleric", (5, 5), MACA)
        ali = self.heroi("ali", "warrior", (4, 5))
        ali["max_hp"], ali["hp"] = 10, 9
        await self.atacar("cl")
        req = self.tipos("voto_guardiao_prompt")[0]["request_id"]
        with patch.object(S, "roll_dice", return_value=6):
            await self.room.handle_voto_guardiao_choice("cl", {"request_id": req, "target_id": "ali"})
        self.assertEqual(ali["hp"], 10)

    async def test_recarga_impede_nova_oferta(self):
        cl = self.heroi("cl", "cleric", (5, 5), MACA, hp=1)
        cl["max_hp"] = 30
        cl["gear"]["weapon"]["voto_guardiao_ready_round"] = self.room.round_num + 5
        await self.atacar("cl")
        self.assertEqual(self.tipos("voto_guardiao_prompt"), [])

    async def test_sem_ferido_no_alcance_nao_oferece(self):
        self.heroi("cl", "cleric", (5, 5), MACA)
        longe = self.heroi("longe", "warrior", (20, 20), hp=1)
        longe["max_hp"] = 20
        await self.atacar("cl")
        self.assertEqual(self.tipos("voto_guardiao_prompt"), [])

    async def test_erro_no_ataque_nao_oferece(self):
        cl = self.heroi("cl", "cleric", (5, 5), MACA, hp=1)
        cl["max_hp"] = 30
        await self.atacar("cl", acerta=False)
        self.assertEqual(self.tipos("voto_guardiao_prompt"), [])

    async def test_recusar_nao_gasta_recarga(self):
        cl = self.heroi("cl", "cleric", (5, 5), MACA, hp=1)
        cl["max_hp"] = 30
        await self.atacar("cl")
        req = self.tipos("voto_guardiao_prompt")[0]["request_id"]
        await self.room.handle_voto_guardiao_choice("cl", {"request_id": req, "target_id": None})
        self.assertNotIn("voto_guardiao_pending", cl)
        self.assertEqual(cl["gear"]["weapon"].get("voto_guardiao_ready_round", 0), 0)

    async def test_pedido_com_id_errado_e_ignorado(self):
        cl = self.heroi("cl", "cleric", (5, 5), MACA, hp=1)
        cl["max_hp"] = 30
        await self.atacar("cl")
        await self.room.handle_voto_guardiao_choice("cl", {"request_id": "falso", "target_id": "cl"})
        self.assertEqual(cl["hp"], 1)
        self.assertIn("voto_guardiao_pending", cl)

    async def test_alvo_fora_da_lista_e_recusado(self):
        cl = self.heroi("cl", "cleric", (5, 5), MACA, hp=1)
        cl["max_hp"] = 30
        cheio = self.heroi("cheio", "warrior", (4, 5))
        await self.atacar("cl")
        req = self.tipos("voto_guardiao_prompt")[0]["request_id"]
        self.msgs.clear()
        await self.room.handle_voto_guardiao_choice("cl", {"request_id": req, "target_id": "cheio"})
        self.assertEqual(str(self.tipos("error")[0]["msg"]), str(S.T("erro.alvo_invalido")))
        self.assertEqual(cheio["hp"], cheio["max_hp"])
        self.assertEqual(cl["gear"]["weapon"].get("voto_guardiao_ready_round", 0), 0)

    async def test_outra_classe_com_a_maca_nao_recebe_oferta(self):
        guerreiro = self.heroi("g", "warrior", (5, 5), MACA, hp=1)
        guerreiro["max_hp"] = 30
        await self.atacar("g")
        self.assertEqual(self.tipos("voto_guardiao_prompt"), [])

    async def test_pendente_some_no_fim_do_turno(self):
        cl = self.heroi("cl", "cleric", (5, 5), MACA, hp=1)
        cl["max_hp"] = 30
        await self.atacar("cl")
        self.assertIn("voto_guardiao_pending", cl)
        self.room._reset_fim_turno_jogador(cl)
        self.assertNotIn("voto_guardiao_pending", cl)


class VeredictoTests(Base):
    async def ofertar(self, paladino, weapon, crit, escolha):
        tarefa = asyncio.ensure_future(
            self.room._oferecer_veredito_radiante_apos_acerto(paladino, self.alvo, weapon, crit))
        for _ in range(50):
            await asyncio.sleep(0)
            if paladino.get("veredito_radiante_pending") or tarefa.done():
                break
        if escolha is not None and paladino.get("veredito_radiante_pending"):
            req = paladino["veredito_radiante_pending"]["request_id"]
            await self.room.handle_veredito_radiante_choice(
                paladino["id"], {"request_id": req, "choice": escolha})
        return await asyncio.wait_for(tarefa, 3)

    async def test_mais_1_usar_causa_2d8_sagrado_e_inicia_recarga(self):
        pal = self.heroi("pal", "paladin", (5, 5), VEREDITO1)
        with patch.object(S, "roll_dice", return_value=9):
            dano = await self.ofertar(pal, pal["weapon"], False, "use")
        self.assertEqual(dano, 9)
        self.assertEqual(len(self.tipos("veredito_radiante_prompt")), 1)
        pronta = pal["gear"]["weapon"]["veredito_radiante_ready_round"]
        self.assertEqual(pronta, self.room.round_num + 10)
        self.assertEqual(pal["weapon"]["veredito_radiante_ready_round"], pronta)

    async def test_mais_1_recusar_nao_causa_dano_nem_recarga(self):
        pal = self.heroi("pal", "paladin", (5, 5), VEREDITO1)
        dano = await self.ofertar(pal, pal["weapon"], False, "skip")
        self.assertEqual(dano, 0)
        self.assertEqual(pal["gear"]["weapon"].get("veredito_radiante_ready_round", 0), 0)
        self.assertNotIn("veredito_radiante_pending", pal)

    async def test_mais_1_em_recarga_nao_pergunta(self):
        pal = self.heroi("pal", "paladin", (5, 5), VEREDITO1)
        pal["gear"]["weapon"]["veredito_radiante_ready_round"] = self.room.round_num + 4
        dano = await self.ofertar(pal, pal["weapon"], False, None)
        self.assertEqual(dano, 0)
        self.assertEqual(self.tipos("veredito_radiante_prompt"), [])

    async def test_mais_1_critico_nao_e_automatico(self):
        pal = self.heroi("pal", "paladin", (5, 5), VEREDITO1)
        dano = await self.ofertar(pal, pal["weapon"], True, "skip")
        self.assertEqual(dano, 0)
        self.assertEqual(len(self.tipos("veredito_radiante_prompt")), 1)

    async def test_mais_3_critico_e_automatico_e_nao_gasta_recarga(self):
        pal = self.heroi("pal", "paladin", (5, 5), VEREDITO3)
        with patch.object(S, "roll_dice", return_value=11):
            dano = await self.ofertar(pal, pal["weapon"], True, None)
        self.assertEqual(dano, 11)
        self.assertEqual(self.tipos("veredito_radiante_prompt"), [])
        self.assertEqual(pal["gear"]["weapon"].get("veredito_radiante_ready_round", 0), 0)

    async def test_mais_3_sem_critico_continua_opcional(self):
        pal = self.heroi("pal", "paladin", (5, 5), VEREDITO3)
        with patch.object(S, "roll_dice", return_value=7):
            dano = await self.ofertar(pal, pal["weapon"], False, "use")
        self.assertEqual(dano, 7)
        self.assertEqual(len(self.tipos("veredito_radiante_prompt")), 1)

    async def test_outra_classe_nao_recebe_oferta(self):
        g = self.heroi("g", "warrior", (5, 5), VEREDITO3)
        dano = await self.ofertar(g, g["weapon"], True, None)
        self.assertEqual(dano, 0)

    async def test_alvo_morto_nao_gera_oferta(self):
        pal = self.heroi("pal", "paladin", (5, 5), VEREDITO1)
        self.alvo["hp"] = 0
        dano = await self.ofertar(pal, pal["weapon"], False, None)
        self.assertEqual((dano, self.tipos("veredito_radiante_prompt")), (0, []))

    async def test_integrado_ao_ataque_o_critico_do_mais_3_soma_o_sagrado(self):
        pal = self.heroi("pal", "paladin", (5, 5), VEREDITO3)
        await self.atacar("pal", critico=True)
        dados = [m for m in self.msgs if isinstance(m, dict) and m.get("expression") == "2d8"]
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]["damage_type"], S.DMG_HOLY)
        self.assertLess(self.alvo["hp"], 500)


class JuramentoTests(Base):
    async def reagir(self, alvo, dano, usar, atacante_id=1):
        tarefa = asyncio.ensure_future(
            self.room._oferecer_protecao_juramento(alvo, dano, atacante_id))
        for _ in range(50):
            await asyncio.sleep(0)
            if self.room.sorte_reacao or tarefa.done():
                break
        if usar is not None and self.room.sorte_reacao:
            await self.room.handle_sorte_reacao(self.room.sorte_reacao["pid"], usar)
        return await asyncio.wait_for(tarefa, 3)

    def cena(self, dist=2):
        pal = self.heroi("pal", "paladin", (5, 5), JURAMENTO)
        ali = self.heroi("ali", "warrior", (5 + dist, 5))
        return pal, ali

    async def test_aceitar_reduz_o_dano_e_inicia_recarga(self):
        pal, ali = self.cena(3)
        with patch.object(S, "roll_dice", return_value=4):
            dano = await self.reagir(ali, 10, True)
        self.assertEqual(dano, 6)
        pronta = pal["gear"]["weapon"]["protecao_juramento_ready_round"]
        self.assertEqual(pronta, self.room.round_num + 10)
        self.assertEqual(pal["weapon"]["protecao_juramento_ready_round"], pronta)
        self.assertEqual(len(self.tipos("sorte_reacao")), 1)

    async def test_reducao_nunca_deixa_dano_negativo(self):
        pal, ali = self.cena()
        with patch.object(S, "roll_dice", return_value=6):
            dano = await self.reagir(ali, 2, True)
        self.assertEqual(dano, 0)

    async def test_recusar_mantem_o_dano_e_nao_gasta_recarga(self):
        pal, ali = self.cena()
        dano = await self.reagir(ali, 10, False)
        self.assertEqual(dano, 10)
        self.assertEqual(pal["gear"]["weapon"].get("protecao_juramento_ready_round", 0), 0)
        self.assertIsNone(self.room.sorte_reacao)

    async def test_alem_de_3_casas_nao_oferece(self):
        pal, ali = self.cena(4)
        dano = await self.reagir(ali, 10, None)
        self.assertEqual((dano, self.tipos("sorte_reacao")), (10, []))

    async def test_paladino_nao_protege_a_si_mesmo(self):
        pal, ali = self.cena()
        dano = await self.reagir(pal, 10, None)
        self.assertEqual((dano, self.tipos("sorte_reacao")), (10, []))

    async def test_em_recarga_nao_oferece(self):
        pal, ali = self.cena()
        pal["gear"]["weapon"]["protecao_juramento_ready_round"] = self.room.round_num + 3
        dano = await self.reagir(ali, 10, None)
        self.assertEqual((dano, self.tipos("sorte_reacao")), (10, []))

    async def test_dano_zero_nao_oferece(self):
        pal, ali = self.cena()
        dano = await self.reagir(ali, 0, None)
        self.assertEqual((dano, self.tipos("sorte_reacao")), (0, []))

    async def test_outra_classe_com_a_espada_nao_reage(self):
        g = self.heroi("g", "warrior", (5, 5), JURAMENTO)
        ali = self.heroi("ali", "mage", (6, 5))
        dano = await self.reagir(ali, 10, None)
        self.assertEqual((dano, self.tipos("sorte_reacao")), (10, []))

    async def test_paladino_desconectado_nao_reage(self):
        pal, ali = self.cena()
        pal["connected"] = False
        dano = await self.reagir(ali, 10, None)
        self.assertEqual((dano, self.tipos("sorte_reacao")), (10, []))

    async def test_integrado_so_ataques_acionam_a_reacao(self):
        """O dano de ataque passa pela reação; dano que não é ataque (is_attack=False) não."""
        pal, ali = self.cena()
        ali["hp"] = ali["max_hp"] = 40
        with patch.object(S, "roll_dice", return_value=3):
            await self.room._aplicar_dano_alvo(ali, 8, S.DMG_PHYSICAL, 1, is_attack=False)
        self.assertEqual(self.tipos("sorte_reacao"), [])
        self.assertEqual(ali["hp"], 32)

    async def test_integrado_ataque_oferece_a_reacao_e_aplica_o_dano_reduzido(self):
        pal, ali = self.cena()
        ali["hp"] = ali["max_hp"] = 40
        tarefa = asyncio.ensure_future(
            self.room._aplicar_dano_alvo(ali, 8, S.DMG_PHYSICAL, 1, is_attack=True))
        for _ in range(50):
            await asyncio.sleep(0)
            if self.room.sorte_reacao or tarefa.done():
                break
        with patch.object(S, "roll_dice", return_value=3):
            await self.room.handle_sorte_reacao("pal", True)
            await asyncio.wait_for(tarefa, 3)
        self.assertEqual(ali["hp"], 35)


if __name__ == "__main__":
    unittest.main(verbosity=1)
