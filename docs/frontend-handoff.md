# Handoff do frontend local

Este documento descreve o contrato **implementado** do MVP. A interface será outro projeto:
React puro, TanStack Router/Query, Tailwind e shadcn/ui. Não há dependência de serviços online.

## Rodar e autenticar

1. Neste repositório, execute `make up` e `make seed`.
2. Use `http://localhost:8000` como base da API; o Swagger está em `/docs`.
3. Chame `POST /v1/auth/token` com `email`, `password` e `brand_slug` para staff. Para
   creator, `brand_slug` é `null`.
4. Envie `Authorization: Bearer <access_token>`; `GET /v1/auth/me` retorna o papel e a marca.

O JWT dura 60 minutos e não há refresh token. Logout é apagar o token no frontend. CORS
aceita apenas `http://localhost:5173` e `http://127.0.0.1:5173` por padrão. Não use a
senha demonstrativa fora do ambiente local.

## Telas por papel

| Papel | Telas e operações centrais |
|---|---|
| `owner` | Programa, campanhas, creators, conteúdo, pedidos, relatórios, auditoria e visão financeira completa. |
| `ops` | Candidaturas, convites, memberships, participantes da campanha, posts, pedidos e relatórios operacionais. |
| `finance` | Planos de comissão, ledger, lotes, payouts, reconciliação, propostas, gates, aprovação e relatórios financeiros. |
| `creator` | Candidaturas próprias, convite por token, aceite de termos, memberships, assets, comissões e performance próprias. |

O frontend não envia `brand_id` para escolher o tenant: o backend deriva a marca do JWT.
Creator só pode acessar registros próprios. Nunca use um endpoint staff para montar uma
tela de creator.

## Mapa de navegação e endpoints

Todos os caminhos abaixo têm prefixo `/v1`, exceto `/r/{token}` e os health checks.

| Tela | Leituras | Ações |
|---|---|---|
| Programas | `GET /programs`, `/programs/{id}`, `/programs/{id}/terms`, `/programs/{id}/commission-plans` | Criar programa, mudar status, criar termos e planos. |
| Campanhas | `GET /programs/{id}/campaigns`, `/campaigns/{id}`, `/campaigns/{id}/participants` | Criar/mudar status; `POST /campaigns/{id}/participants` seleciona; `/participants/{membership_id}/status` remove ou retoma. |
| Candidaturas | `GET /applications` (staff), `/applications/me` (creator), `/applications/{id}` | Candidatar, revisar, retirar. |
| Convites | `GET /programs/{id}/invitations`, `/invitations/{token}` | Criar, revogar e aceitar. Token/link aparecem só na resposta de criação. |
| Parcerias | `GET /programs/{id}/memberships`, `/memberships/me`, `/memberships/{id}`, `/memberships/{id}/assets` | Aceitar termos e mudar status (staff). |
| Conteúdo | `GET /posts`, `/posts/{id}` | Importar fixtures em `/listening/imports`; revisar em `/posts/{id}/review`. |
| Vendas | `GET /orders`, `/orders/{id}` | Webhook é do simulador, não da UI; não há reatribuição manual. |
| Comissões | `GET /commissions`, `/memberships/{id}/commissions`, `/ledger-entries` | Liquidar em `/commissions/settle` (financeiro). Ledger é somente leitura. |
| Pagamentos | `GET /payout-batches`, `/payout-batches/{id}`, `/payouts` | Criar, aprovar ou cancelar lote **draft**. |
| Agentic | `GET /reconciliation/runs`, `/reconciliation/runs/{id}`, `/agent/findings`, `/agent/findings/{id}`, `/agent/proposals`, `/agent/proposals/{id}` | Rodar reconciliação, gerar proposta, rodar gates, aprovar/rejeitar, executar; encerrar finding manualmente com comentário. |
| Relatórios | `GET /reports/programs/{id}/overview`, `/reports/campaigns/{id}/overview`, `/reports/memberships/{id}/overview` | Somente leitura. |
| Auditoria | `GET /audit-logs` | Somente leitura. |

A especificação OpenAPI em `/openapi.json` é a fonte para tipos e campos exatos. Bruno em
`bruno/` oferece exemplos encadeados, inclusive cenários negativos.

## Paginação, filtros e estado

Todas as listas retornam `{ "items": [...], "total": 0, "limit": 25, "offset": 0 }`.
`limit` vai de 1 a 100, padrão 25; `offset` começa em zero. A ordenação é estável no
servidor. Preserve filtros na URL e use as chaves de query do OpenAPI: por exemplo
`application_status`, `membership_status`, `participant_status`, `content_status`,
`order_status`, `commission_status`, `commission_kind`, `bucket`, `program_id`,
`campaign_id`, `membership_id`, `actor_user_id`, `action`, `entity_type`, `from_at`, `to_at`.

Dinheiro vem como string decimal (`"29.00"`); nunca converta para `number` para cálculos.
Datas são ISO 8601 com timezone UTC. Estados são strings de enum; não crie estados
inventados no cliente. Após mutations, invalide as queries de detalhe, lista e relatório
do domínio relacionado. Para imports e payouts, o worker é assíncrono: refetch até o
estado terminal ou mostre um botão de atualizar.

## Erros e regras que a UI deve mostrar

Erros de domínio usam `application/problem+json`, com `status`, `code`, `detail`, `instance`
e `meta` opcional. `401` pede login; `403` nega papel/posse; `404` também protege dados
de outra marca; `409` sinaliza conflito de estado/versão/duplicidade; `422` indica dados
inválidos ou regra não atendida. Erros de validação Pydantic também usam `422`, conforme
OpenAPI. Exiba `detail` e nunca trate `409` como sucesso silencioso.

- Convite exige e-mail do creator autenticado; vencido, revogado ou utilizado por outra
  pessoa não cria membership.
- Aprovada a candidatura, a parceria fica `awaiting_terms` até o creator aceitar os
  termos vigentes; assets só atribuem quando programa, campanha opcional, participação,
  termos e membership estão válidos.
- Campanha é opcional na venda. Uma campanha pode ter plano de comissão específico.
- Reimportação de post aprovado/rejeitado preserva decisão e revisor; mudança de escopo
  após revisão retorna `409`.
- Payout `unknown` continua reservado. A UI deve distinguir `gate`, `approve` e
  `execute`: são três ações diferentes. Comentário é obrigatório na aprovação/rejeição e
  no encerramento manual do finding. Um finding encerrado não altera ledger nem payout.

## Fora de escopo

Não há refresh token, e-mail real, redes sociais reais, pagamentos reais, administração
de usuários staff, reatribuição manual de vendas, LLM ou deploy. A plataforma é um
protótipo técnico local, não um sistema financeiro de produção.
