# Campanha de Elara — auditoria dos protótipos do autor

Data: 2026-10-21. Só leitura: nenhum arquivo do autor foi alterado. Números tirados com
`carregar_dungeon` + `validar_dungeon` + `nd_por_sala` (todos validam, exceto onde dito).

| Arquivo | Grid | Salas | Monstros | Armadilhas / baús / passagens / decor | Objetivo | Papel na campanha |
|---|---|---|---|---|---|---|
| `casa_secreta.json` | 11×16 | 1 | 0 | 0 / 0 / **4** / 12 | `reach_exit` | **Casa do bardo (Parte 1)** |
| `fazenda.json` | 19×17 | 1 | 0 | 0 / 0 / 0 / 79 | `kill_all` | **Fazenda (Parte 1)** |
| `passagens_secreta.json` | 17×13 | 2 | 3 | 0 / 1 / 0 / 2 | `kill_all` | Alternativa menor para a casa |
| `gustavo.json` | 17×13 | 2 | 7 | 0 / 1 / 4 / 4 | `kill_all` | Fecha o protótipo "casa suspeita" (floresta → casa → gustavo); sem papel na Parte 1 |
| `floresta.json` | 26×16 | 1 | 7 | 0 / 0 / 0 / 172 | `reach_exit` | Adhadal (Ramo B) |
| `floresta_2.json` | 43×42 | 1 | 15 | 0 / 0 / 0 / 574 | `kill_all` | Adhadal (Ramo B) |
| `resgate de elara.json` | 44×40 | **20** | 5 | **17** / **13** / 0 / 30 | `rescue_prisoner` | **Esconderijo do Leonel (Graciero)**; `expected_party` 1 herói nível 2 (ajustar) |
| `Introducao.json` | 24×19 | 18 | 22 | 6 / 4 / **23** / 3 | `kill_target` | Possível mansão do Leonel; `saida_permitida: false` |
| `caverna.json` | 16×60 | 8 | 14 | 0 / 4 / 0 / 0 | `kill_all` | Sem papel definido |
| `sala secreta.json`, `penhasco.json`, `resgate_prisioneiro.json` | pequenos | 1–2 | 0–1 | variável | variado | Sem papel definido |

## Decisões para a Parte 1

- **Casa do bardo:** `casa_secreta.json` serve **com ajustes feitos pelo autor no editor**:
  adicionar as armadilhas múltiplas (hoje 0), o corpo do bardo (decoração + fala), o baú das
  partituras, a fala que revela o endereço da fazenda ao abrir a passagem e o campo `relogio`
  com o mesmo `id` da fazenda (`relogio_desconto` numa das 4 passagens). Objetivo atual
  (`reach_exit`) basta, com o fato `elara_casa_vencida` no objetivo principal.
- **Fazenda:** `fazenda.json` serve **com ajustes**: 79 decorações já montam o cenário, mas não
  há monstros nem armadilhas. Faltam bandidos (o autor está criando um monstro `bandido` em outra
  frente: ver `docs/superpowers/plans/2026-10-21-bandido-bestiario.md`; enquanto não existe,
  usar `goblin_combatente`/`soldado`), armadilhas, o bandido ferido que confessa (fala `manual`
  ou de sala), os sinais do cenário (estábulos/celas vazios) e o objetivo com o fato
  `elara_fazenda_vencida`. Objetivo `kill_all` serve.
- **Mapas novos:** nenhum necessário se o autor fizer os ajustes acima. Se preferir que o Claude
  monte os ajustes por script, a alternativa é gerar cópias novas (`elara_casa.json`,
  `elara_fazenda.json`) no molde de `tools/charcos_mapas.py`, sem tocar nos originais.
- **Fora da Parte 1** (para os próximos planos): Adhadal (`floresta*.json`), esconderijo do Leonel
  (`resgate de elara.json`, o maior e mais completo) e uma possível mansão (`Introducao.json`).
