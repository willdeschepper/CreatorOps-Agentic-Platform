# Spec — Frontend local do CreatorOps Agentic Platform

## Missão do próximo chat

Construir uma interface navegável para estudar e demonstrar as **regras de negócio** do
CreatorOps, usando exclusivamente o backend local já implementado. O resultado deve
permitir que `owner`, `ops`, `finance` e `creator` percorram suas tarefas reais, sem
dados de domínio falsos no runtime. Esta especificação orienta **somente o frontend**;
não autoriza alterar API, models, migrations ou regras financeiras para acomodar a UI.

Antes de codar, leia [AGENTS.md](AGENTS.md),
[docs/frontend-handoff.md](docs/frontend-handoff.md),
[docs/domain-rules.md](docs/domain-rules.md) e o OpenAPI local em
`http://localhost:8000/openapi.json`. Em caso de divergência, confirme o comportamento
no código e no OpenAPI, registre a discrepância e não invente um contrato.

## Produto e escopo

CreatorOps é um protótipo com identidade própria para uma operação de creators e
afiliados. O fluxo principal é:

`programa → candidatura/convite → aceite de termos → assets → venda atribuída →
comissão → saldo disponível → payout → reconciliação → proposta → gates →
aprovação humana → execução auditada`

Campanhas são opcionais dentro do programa: selecionam creators, podem ter assets e plano
de comissão próprios. Conteúdo social segue uma trilha de importação, matching e revisão;
não gera comissão por si só. O frontend deve tornar essas distinções compreensíveis.

Não copiar identidade visual, textos, imagens nem UX de terceiros. Não há GCP, LLM,
pagamento, e-mail ou rede social real nesta fase. Todo acesso de runtime é local.

### Stack definida

- React com Vite e TypeScript; **sem Next.js** ou renderização no servidor.
- TanStack Router para rotas e guards; TanStack Query para estado remoto/cache.
- Tailwind CSS e componentes shadcn/ui, com tokens e composição próprios.
- Formulários tipados com validação alinhada ao OpenAPI; preferir React Hook Form + Zod
  se essas dependências estiverem disponíveis localmente.
- `frontend/` como aplicação separada dentro deste repositório por padrão. Não mover o
  backend nem misturar componentes React em `src/creatorops/`.
- Usar `npm` por padrão para comandos da aplicação; não adicionar um backend Node.

A instalação inicial de dependências pode exigir pacotes ainda ausentes no computador.
**Não acessar serviços online nesta fase.** Se faltar um pacote no cache local, pausar e
pedir autorização ao usuário antes de qualquer download. Build e runtime devem funcionar
apenas com a stack local.

## Contrato técnico com o backend

- API: `http://localhost:8000`; Swagger: `http://localhost:8000/docs`.
- Frontend Vite: `http://localhost:5173`; esta origem e
  `http://127.0.0.1:5173` estão permitidas no CORS do backend.
- `GET /health/ready` indica se API e PostgreSQL estão prontos.
- Autenticação: `POST /v1/auth/token`; enviar
  `Authorization: Bearer <access_token>` nas rotas protegidas. Para staff, solicitar
  `brand_slug`; para creator, enviar `null`. `GET /v1/auth/me` determina papel,
  identidade e marca ativa.
- JWT dura 60 minutos; não existe refresh token. Guardar o token apenas na sessão da
  aba (`sessionStorage`) para permitir reload local, limpar no logout e ao receber
  `401`. Nunca colocar token em URL, logs, telemetria ou repositório.
- Listas retornam `{items, total, limit, offset}`. Padrões: `limit=25`,
  `offset=0`; limite máximo 100. Preservar filtros e paginação na URL.
- Dinheiro chega como string decimal; não usar `number` para aritmética financeira.
  `Intl.NumberFormat` pode formatar **apenas para exibição**, sem alimentar cálculos.
  Renderizar datas ISO 8601/UTC com indicação clara do fuso na interface.
- Tratar `application/problem+json` (`code`, `detail`, `status`, `meta`) e
  `422` de validação. `409` deve mostrar conflito e oferecer recarregar estado; não
  repetir automaticamente mutations financeiras.
- O cliente não escolhe `brand_id`: a API deriva o tenant do JWT. Guards no frontend
  melhoram navegação, mas a autorização real continua no backend.
- Gerar ou manter tipos a partir do OpenAPI **local** quando possível. Centralizar
  `fetch`, base URL, bearer, parser de erro e query keys. Não espalhar requests pelos
  componentes nem codificar campos presumidos.

## Papéis, navegação e páginas

A navegação principal deve ser responsiva, acessível por teclado e adaptada ao papel.
Esconder ações sem permissão, mas manter telas informativas para estados `403`, `404`
e sessão expirada.

| Área | Páginas mínimas | Papel |
|---|---|---|
| Acesso | Login staff/creator, registro de creator, logout e convite por token | Todos/creator |
| Visão geral | Dashboard com KPIs reais, atalhos e estados vazios úteis | Cada papel |
| Programas | Lista, detalhe, termos versionados e planos; criar/mudar estado onde autorizado | owner/ops; finance para regras e leitura permitida |
| Campanhas | Lista/detalhe, datas, briefing, participantes selecionados/removidos, assets e relatório | owner/ops; finance leitura permitida |
| Parcerias | Candidaturas, revisão, convites, memberships, aceite de termos e assets próprios | owner/ops/creator |
| Conteúdo | Importação local, lista filtrável, detalhe, matching e nova decisão de revisão | owner/ops |
| Vendas | Lista/detalhe com sinais, decisão de atribuição, devoluções e comissão | owner/ops/finance conforme API |
| Financeiro | Comissões, buckets do ledger, lotes, payouts e detalhe do snapshot | owner/finance; creator vê apenas próprios |
| Agentic | Runs, findings, evidências, propostas, gates, aprovação/rejeição, execução e auditoria | owner/finance |
| Resultados | Relatórios de programa, campanha e membership própria | Staff/creator conforme API |
| Auditoria | Lista filtrável de ações por ator, entidade e período | Staff conforme API |

Rotas sugeridas: `/login`, `/register`, `/invite/$token`, `/app`,
`/app/programs`, `/app/programs/$programId`,
`/app/campaigns/$campaignId`, `/app/applications`,
`/app/memberships`, `/app/posts`, `/app/orders`,
`/app/finance/commissions`, `/app/finance/payout-batches`,
`/app/finance/reconciliation`, `/app/reports` e
`/app/audit`. Organizar em layouts staff/creator; nomes exatos de componentes ficam
a cargo da implementação.

### Jornadas que a UI deve explicar

1. **Ativação:** candidatura ou convite → aprovação/aceite do convite →
   `awaiting_terms` → aceite da versão vigente → `active` e assets. Novo termo
   obrigatório suspende assets até novo aceite. Rejeição/retirada de candidatura
   permite nova tentativa sem criar membership duplicada.
2. **Campanha:** selecionar memberships ativas do mesmo programa; seleção idempotente
   gera assets específicos. Remoção, pausa, data ou status inválido impedem novas
   atribuições, sem apagar histórico.
3. **Venda/comissão:** detalhe do pedido mostra cupom e clique, motivo da atribuição
   e comissão do plano vigente. Cupom válido vence clique conflitante. Comissão passa
   por `pending`, `available`, `reserved` e `paid`; reembolso cria ajuste,
   não edição da linha original.
4. **Conteúdo:** distinguir `detected`/`matched` de `approved`/`rejected`.
   Reimportar post revisado atualiza métricas, preservando decisão e revisor.
   Alterar escopo de post revisado retorna `409` e pede ação humana.
5. **Pagamento e agentic:** payout `unknown` mantém reserva. Exibir
   reconciliação → finding/evidência → proposta → gates individuais →
   aprovação humana com comentário → execução **em botão separado**, com
   revalidação. `blocked`, `rejected` e `stale` não podem executar.
   Encerrar finding manualmente não altera ledger nem payout.

## Padrões de interação

- Toda lista tem loading, vazio, erro, filtro, paginação e ação de atualizar.
  Exibir `total` retornado pela API, não supor que `items.length` seja o total.
- Detalhes mostram IDs copiáveis, datas, estados e atores da decisão quando existirem.
  Estados financeiros devem ter texto explicativo e cores redundantes com ícone/rótulo.
- Ações que mudam estados exigem confirmação contextual; ações financeiras e
  aprovação/rejeição agêntica pedem comentário quando o backend exige.
- Após mutation, invalidar queries relacionadas de lista, detalhe e relatório.
  Não aplicar atualização otimista em payout, ledger ou proposta.
- Pub/Sub/worker são assíncronos. Para importações e payouts, oferecer refetch ou
  polling curto e cancelável enquanto o estado não for terminal; nunca supor
  confirmação instantânea.
- Exibir `request_id`/correlation ID do erro quando disponível para facilitar
  investigação; não expor secrets ou tokens.
- UI em português claro; manter códigos de estado reais próximos às traduções para
  estudo. Layout próprio, legível, responsivo, com contraste e foco visível.
- Não inventar somatórios de payout por campanha: o relatório de campanha expõe
  GMV, devoluções, pedidos, conteúdo, métricas sociais e comissão líquida, mas não
  rateia pagamentos.

## API por área

Use [docs/frontend-handoff.md](docs/frontend-handoff.md) para o mapa resumido e
`/openapi.json` para os schemas exatos. Endpoints prioritários:

- Acesso: `/v1/auth/register`, `/v1/auth/token`, `/v1/auth/me`.
- Programa/campanha: `/v1/programs`,
  `/v1/programs/{id}/campaigns`, `/v1/campaigns/{id}`,
  `/v1/programs/{id}/terms`, `/v1/programs/{id}/commission-plans`,
  `/v1/commission-plans/{id}`.
- Creator/parceria: `/v1/applications`, `/v1/applications/me`,
  `/v1/invitations/{token}`, `/v1/programs/{id}/invitations`,
  `/v1/programs/{id}/memberships`, `/v1/memberships/me`,
  `/v1/memberships/{id}/assets`,
  `/v1/campaigns/{id}/participants`.
- Operação: `/v1/posts`, `/v1/listening/imports`,
  `/v1/orders`, `/v1/commissions`, `/v1/ledger-entries`.
- Financeiro/agentic: `/v1/payout-batches`, `/v1/payouts`,
  `/v1/reconciliation/runs`, `/v1/agent/findings`,
  `/v1/agent/proposals`, `/v1/audit-logs`.
- Relatórios: `/v1/reports/programs/{id}/overview`,
  `/v1/reports/campaigns/{id}/overview`,
  `/v1/reports/memberships/{id}/overview`.

**Não há endpoint de criar venda manualmente.** Vendas entram pelo webhook de comércio
assinado. Para popular a UI use `make demo` ou a coleção [Bruno](bruno/README.md);
não coloque segredo HMAC no browser nem simule vendas apenas no cliente.

## Estrutura sugerida da aplicação

```text
frontend/
  src/
    app/          providers, router, sessão e layout
    api/          cliente HTTP, tipos OpenAPI e query keys
    components/   UI compartilhada, estados e tabelas
    features/     auth, programs, campaigns, partnerships, listening,
                  orders, commissions, finance, agent-control, reports, audit
    lib/          formatadores e utilitários sem regra financeira
  tests/          testes de componentes e jornadas locais
```

Evitar um `api.ts` gigante e evitar que o layout conheça detalhes de payload. A
regra de negócio e o cálculo financeiro permanecem no backend; o frontend apresenta
decisões e chama comandos autorizados.

## Entrega em etapas

1. **Fundação:** Vite/React/TypeScript, Tailwind/shadcn, layout original, API client,
   tipos OpenAPI, sessão, guards e tratamento de erros. Login real com os usuários
   de `make seed`.
2. **Operação:** programas, campanhas, candidaturas/convites, memberships,
   participantes e assets, com papéis e paginação reais.
3. **Mensuração:** posts, pedidos, comissões e relatórios. Validar reimportação
   preservando revisão.
4. **Financeiro/agentic:** lotes, payout, ledger, runs, findings, gates,
   aprovação/rejeição e execução separada; auditoria.
5. **Qualidade:** estados vazios, acessibilidade, mobile, testes, build e
   jornada end-to-end na stack Docker local.

Não iniciar a etapa seguinte com telas falsas da anterior. Cada fatia vertical deve
usar endpoints reais e deixar uma jornada testável.

## Critérios de aceite

- `make up`, `make seed` e `make demo` preparam dados exibidos pela UI.
- `npm run dev` sobe o frontend em `localhost:5173`; `npm run build` passa.
- Login e autorização funcionam para os quatro papéis; logout limpa a sessão e
  sessão expirada volta ao login. Creator não vê dados de outro creator.
- Todas as listas implementadas respeitam envelope, `total`, filtros e paginação;
  acesso negado e conflitos têm mensagens claras.
- A UI não usa arrays de domínio hardcoded, fixtures como runtime, mocks de API,
  cloud, CDN ou serviços online.
- Financeiro consegue visualizar payout `unknown`, evidência, gates individuais,
  aprovação e execução separadas usando dados reais preparados localmente.
- Reimportar post revisado mantém status e revisor visíveis na tela.
- Valores monetários exibidos correspondem às strings da API; o frontend não
  recalcula comissão ou saldo.
- Há testes de navegação/RBAC, estado assíncrono e fluxos críticos, além de
  revisão visual em desktop e mobile.
- Documentar comandos, decisões de UX, limitações e como reproduzir o cenário
  sem depender de memória do chat.

## Fora do escopo

Deploy, hospedagem, GCP real, LLM, e-mail, redes sociais ou transferências reais,
administração de staff, refresh token, reatribuição manual de pedidos, schema drift,
gamificação e clonagem visual/funcional de qualquer produto existente.
