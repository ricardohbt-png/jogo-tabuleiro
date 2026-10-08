# Tutorial guiado — fatia 6: instrução clara, conclusão visível, recompensa e novos temas

Origem: teste com o Lucas (2026-10-07). Cinco achados:

1. O botão "Me mostra" (`ui.tutorial.me_mostra`, `_guiaMostrar`) mostra o halo mas o texto do passo não diz o que fazer.
2. Não há recompensa por cumprir as etapas.
3. Não há sinal claro de que um passo/lição terminou.
4. Os atalhos do jogo não são ensinados.
5. Resistência e suscetibilidade (vulnerabilidade) a dano não são ensinadas.

Fora de escopo: o sistema de cores de dano (RESISTIDO/VULNERÁVEL/METADE/DOBRADO/IMUNE) vive não commitado no worktree `codex/ceu-abismo`; esta fatia não toca nesses arquivos. A lição de resistência funciona sem as cores e as cita no texto assim que a branch for integrada.

## 1. Instruções acionáveis

- Auditar todos os textos de passo/tarefa das 62 lições + `guia_modelo` (geradas) e reescrever como ação concreta com o alvo: "Clique em ⚔ Atacar e depois no goblin".
- O "Me mostra" passa a ser reforço, não substituto: todo passo com `ui` precisa de texto com verbo de ação.
- Teste (`tools/test_tutorial_conteudo.py`): passo não-informativo sem verbo de ação (lista curta de verbos pt/en) reprova.

## 2. Conclusão visível

- Servidor: ao avançar um passo (`_guia_avancar`/`_guia_evento`) e ao concluir a lição (`_licao_concluir`), envia `licao_passo_ok {licao_id, passo, total}` e `licao_concluida {licao_id, recompensa}`.
- Cliente: ✓ verde animado no passo concluído, som curto (`SoundBank`, evento já existente de objetivo/UI; sem arquivo novo), barra "passo i/n" na janela da lição e selo "Lição concluída" com a recompensa. Textos em `src/lang/tutorial.js` (pt+en).

## 3. Recompensa

- Constantes `TUTORIAL_RECOMPENSA_OURO = 5`, `TUTORIAL_RECOMPENSA_XP = 10` por lição; bônus de trilha (`TUTORIAL_BONUS_TRILHA_*`) ao concluir todas as lições da classe.
- Concedida em `_licao_concluir` somente se o id ainda não está em `tutorial_history` (a mesma guarda já existente) — repetir o tutorial não repete o prêmio. XP via o caminho normal de ganho (com `_check_level_up`); ouro em `p["gold"]`.
- Sem campo `recompensa` por lição (YAGNI; evita mexer em `tools/editor.js`): só as constantes globais.

## 4. Lição de atalhos (comum)

Nova lição comum "Seus atalhos": atalho de habilidade/magia da barra existente (`_atalhosAbertos`), `R` (câmera 3D), `Esc` (cancelar mira) e clique na casa para andar. Como esses são eventos só do cliente, os passos são informativos ("Entendi") salvo o movimento, que já gera evento. Regra de ouro mantida: nenhum `conclui_com` para evento que possa ter ocorrido antes.

## 5. Lição de resistência e vulnerabilidade (comum)

Dois bonecos de treino com `resistances`/`weaknesses` de um elemento (usar o que `_apply_damage_types` já lê); o jogador ataca cada um. Passos: ler o resultado, entender resistência (menos dano) e vulnerabilidade (mais dano), imunidade. Glossário ganha `resistencia` e `vulnerabilidade`. Texto cita as cores/rótulos do sistema de dano; enquanto ele não está no `master`, o texto vem sem o nome da cor (dois textos selecionados por flag de capacidade do cliente — se a flag não existir, usar redação neutra e atualizar depois).

## Arquitetura e testes

Mesmo molde das fatias 3–4: conteúdo em `tools/tutorial_guia_comum.py` (+ glossário), gerador `gerar_guia_comum.py` → `src/lang/tutorial_guia.js`, lições novas em `configurar_tutorial_salas.py`. Testes: `test_tutorial_conteudo.py` (verbos, recompensa uma vez, lições novas), `test_tutorial_guia.py` (mensagens `licao_passo_ok`/`licao_concluida`), `test_guia_tutorial_cliente.js` (✓/barra/selo, glossário). Provar no navegador em servidor isolado (porta 8794, cópia dos dados em `%TEMP%`).
