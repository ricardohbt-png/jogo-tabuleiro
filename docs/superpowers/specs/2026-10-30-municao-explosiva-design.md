# Munição Explosiva

## Intenção

Adicionar flechas e virotes explosivos, usando `assets/itens magicos/municao_explosiva.png`, vendidos pelos ferreiros e resolvidos pelo combate normal de armas à distância.

## Regras aprovadas

- Dois tipos de munição e pilha independentes: `flechas_explosivas` e `virotes_explosivos`.
- Cada compra entrega 5 projéteis e custa 60 moedas; as duas variantes usam o mesmo ícone.
- O disparo usa a ação/ataque e alcance normais da arma e consome 1 projétil mesmo se errar.
- Só um acerto detona: o alvo principal sofre o dano normal da arma +1d6 de explosão.
- As outras criaturas vivas em raio 1 sofrem 1d6 de explosão; Reflexos CD 12 reduz à metade. Há fogo amigo; o alvo principal não recebe uma segunda aplicação da área.
- A explosão toca som e animação quando o projétil chega ao alvo.
- As duas munições são vendidas em `ferreiro_ammo` nas cinco cidades. Não alterar a geração aleatória de munição dos monstros.

## Integração

Usar os fluxos de munição existentes para compatibilidade de armas, pilhas, aljavas e venenos. O servidor aplica o dano da área a todos os alvos elegíveis e respeita bloqueio por parede e redução física. O cliente sincroniza os efeitos de explosão ao impacto do `attack_feedback` no modo 3D e ao resultado do ataque no modo 2D.

## Fora de escopo

Não criar um novo tipo de dano, não alterar granadas e munições incendiárias/de prata, nem incluir munição explosiva nos equipamentos aleatórios de monstros.
