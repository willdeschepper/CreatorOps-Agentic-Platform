# Regras de domínio para estudo

Este documento serve como roteiro para explicar o projeto em uma entrevista. Para cada regra,
procure responder três perguntas: qual risco de negócio ela evita, onde é aplicada no código e
qual teste a comprova.

## Programa e parceria

- Programa é uma operação contínua; campanha é uma ativação limitada dentro dele.
- Um programa só ativa depois de possuir ao menos um termo e um plano padrão de comissão.
- Aprovar candidatura cria membership em `awaiting_terms`, nunca já ativa.
- Publicar novo termo obrigatório desativa os assets e exige novo aceite.
- Pausar/offboard não apaga histórico, comissão ou saldo.
- Handles normalizados são únicos por rede.

## Atribuição

- O sistema guarda tanto o cupom quanto o clique recebido no campo `signals`.
- Cupom válido vence mesmo quando o clique aponta para outro creator.
- Clique precisa estar dentro da janela e ligado a membership/asset ativos.
- Pedido sem sinal continua registrado e aparece como não atribuído.
- A primeira atribuição persistida é a decisão oficial; correção futura deve virar ajuste
  auditável.

## Comissão

- O GMV mensal incluindo a venda atual escolhe a faixa.
- A taxa escolhida vale somente para a venda atual; não recalcula pedidos anteriores.
- Bônus tem unique por creator, regra e período.
- `eligible_at` materializa a janela de devolução.
- Reembolso antes da liquidação afeta `pending`; depois afeta `available`.
- A comissão grava `plan_id` e `plan_version` para preservar o cálculo histórico.

## Pagamento

- O lote `draft` é um snapshot. Aprovar compara o snapshot ao saldo atual sob lock.
- Aprovação move saldo disponível para reservado e cria a outbox.
- `failed` devolve a reserva; `unknown` mantém a reserva.
- O simulador persiste por idempotency key e recusa a mesma chave com payload diferente.
- `timeout_after` é o caso perigoso: a transferência existe apesar da ausência de resposta.

## Controle agêntico

- Detecção registra fatos e versões; não prescreve nem muda estado.
- Geração propõe uma ação estruturada; não executa.
- Gates são código determinístico e seus resultados ficam persistidos.
- Aprovação exige papel financeiro/owner e comentário, mas ainda não executa.
- Executor repete os gates dentro da transação. Versão alterada torna a proposta `stale`.
- A correção financeira adiciona lançamentos; não edita o passado.

## Perguntas para se testar

1. Por que a constraint do webhook é composta por marca, provedor e event ID?
2. O que aconteceria se o worker caísse depois de publicar e antes de marcar a outbox?
3. Por que `unknown` não pode liberar a reserva?
4. Por que aprovação e execução são etapas diferentes?
5. Como a versão do payout impede um TOCTOU entre gate e execução?
6. Qual estado é fonte da verdade quando Pub/Sub e Postgres discordam?
7. Em que momento um microsserviço separado seria justificável?
