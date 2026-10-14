# Água protege do fogo — design

Data: 2026-10-13. Complementa as reações elementais (`docs/superpowers/specs/2026-10-13-reacoes-elementais-design.md`).

## Objetivo

Quem está dentro da água sofre **metade** do dano de fogo e **não pega fogo**; quem já está queimando e entra na água é **apagado**. O jogo já tem a ideia pela metade (`chamas_agua_apaga`: o frasco de óleo é apagável com água, o Fogo Grego não). Esta regra a estende ao **terreno**.

## Regras

**Quem conta como "na água".** A criatura está em água quando **todas** as casas do seu footprint são água rasa, água profunda ou redemoinho (raso/profundo), e não há ponte sobre a casa (`_water_tile_kind`). Criatura de uma casa só = a própria casa; monstro grande (`_monster_tiles`) precisa de todas as casas. Criatura voadora acima do chão (`_voo_imune_terreno`) **nunca** conta — a água não a alcança. Vale para heróis, monstros, servos animados, prisioneiro.

**Pântano** conta só para a **imunidade a pegar fogo** (não para a metade do dano). Mesmo critério de footprint, mesmos voadores excluídos.

**1. Metade do dano de fogo.** Todo dano de tipo fogo (`DMG_FIRE`) recebido por criatura na água passa por uma resistência de metade (`{"type": fire, "mode": "half"}`) injetada no funil `_apply_damage_types`, sem passar por outro caminho. Isso cobre de graça Bola de Fogo, Prisão de Chamas, zonas de fogo (`bola_fogo`, `chamas_piche`, `molochus_chamas`), armadilha incendiária, armas e ataques de monstro com fogo, frascos de óleo/bomba e o tick de chamas residuais. Soma com resistências já existentes (criatura com resistência a fogo na água sofre um quarto); imunidade a fogo continua dando 0. O contexto visual já marca o dano como "resistido".

**2. Imune a pegar fogo.** `_aplicar_em_chamas(alvo, rodadas, agua_apaga)` não aplica o status quando o alvo está na água (ou no pântano) e `agua_apaga` é verdadeiro. Não há mensagem de erro: o dano inicial do golpe segue a regra 1, só o status não pega. O alvo continua podendo ser ferido normalmente.

**3. Água apaga.** Criatura com `em_chamas_rodadas > 0` que está na água (regra 1) e cujas chamas são apagáveis (`chamas_agua_apaga` verdadeiro) tem o status zerado:
- imediatamente depois de cada passo/deslocamento (junto do gancho que já existe em `_aplicar_lava_se_pisar`, que roda para herói, monstro, servo, prisioneiro);
- como rede de segurança no início de `_processar_em_chamas_turno` (cobre empurrão, teleporte, redemoinho e qualquer caminho sem o gancho).
Narração: "{nome} mergulha na água e as chamas se apagam." (`narracao.chamas_apagadas_na_agua`). Pântano também apaga.

**4. Fogo Grego.** `chamas_agua_apaga == False` (Fogo Grego) ignora toda a regra: o status pega mesmo na água, não é apagado ao entrar e o dano — inicial e o tick de chamas — **não** recebe a metade. Para o dano inicial usa-se uma marca de escopo `self._fogo_ignora_agua` ligada pela resolução do arremesso enquanto o dano do item é aplicado (e desligada em `finally`); o tick lê a flag do próprio alvo (`alvo["chamas_agua_apaga"]`).

Decisões conscientes da revisão:
- Enquanto o alvo queima com Fogo Grego (`em_chamas_rodadas > 0` e `chamas_agua_apaga` falso), a água não protege de **nenhum** dano de fogo dele, inclusive o de uma Bola de Fogo recebida no mesmo período. Decisão deliberada, mais simples que escopar a exceção por tick.
- Resistências, incluindo a metade da água, são puladas por armas com `ignora_resistencia_fisica` (limite herdado do laço de resistências de `_apply_damage_types`).
- Limites de cobertura: o servo animado (`vida_atual`) toma dano de fogo por `_ajustar_dano_elemental`, fora de `_apply_damage_types`, e não recebe a metade nesses caminhos (a imunidade a pegar fogo e o apagar valem). O ramo de herói/prisioneiro de `_aplicar_dano_alvo`/`_dano_em_alvo` não chama `_apply_damage_types` (quem chama é o executor de cada fonte); por isso as fontes que chegavam ali sem passar por ele (Bola de Fogo inicial e zona residual, explosão do Elemental de Fogo, arremesso de área de herói em aliado, armadilha incendiária e outros efeitos de armadilha de fogo) passaram a chamar `_dano_fogo_na_agua` (metade uma única vez; regra única em `_agua_reduz_fogo`, compartilhada com `_apply_damage_types`). Fontes que já usavam `_apply_damage_types` (Prisão de Chamas, lava, fogueira, chama viva, brasa, Molochus, tick de chamas, retaliação, ataques/sopros/habilidades de monstro, corpo energético) não foram tocadas, para não duplicar.

## Interações

- **Reações elementais:** nada muda. Piche e água não ocupam a mesma casa; o choque em poça e o congelamento seguem como estão. Criatura que acabou de ser congelada (casa vira `piso_congelado`) deixa de estar na água para esta regra.
- **Lava e Ira da Rocha:** a casa de lava não é água; a regra só importa para fogo vindo de fora, em quem está na água.
- **Intenção dos monstros:** o preview é só leitura e não calcula dano de fogo; **fora de escopo** fazer a IA preferir a água quando em chamas.
- **Persistência:** a regra é derivada da posição e do material; não há estado novo nem campo na foto.

## Cliente

- Tooltip de casa de água ganha a linha "🌊 Na água: metade do dano de fogo e imune a chamas" (`descreverCasa` em `src/reacoesElementais.js`, textos em `src/lang/interface.js`, pt e en); pântano: "imune a chamas".
- O dano resistido já aparece como resistido; a narração do servidor cobre o apagar. Sem som novo.

## Testes

`tools/test_agua_protege_fogo.py`: metade do dano (herói, monstro 1×1, monstro 2×2 todo e meio dentro da água), voador, pântano (imune ao status, dano cheio), `_aplicar_em_chamas` bloqueado, entrar na água apaga (passo e rede de segurança no tick), sair da água não reacende, Fogo Grego (status pega, dano cheio, não apaga), resistência existente soma, imunidade a fogo continua 0, Bola de Fogo e tick de chamas na água, congelar remove a proteção. Cliente: tooltip da casa de água/pântano (`tools/test_reacoes_cliente.js`). Bateria da feature de reações permanece verde.

## Fora de escopo

IA preferindo água; água como defesa contra outros elementos; proteção parcial por casa de footprint; mudar a regra do Fogo Grego além do descrito.
