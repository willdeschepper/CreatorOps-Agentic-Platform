# Arquitetura e decisões

## Limites internos

| Limite | Responsabilidade |
|---|---|
| `identity` | usuário, JWT, papel e marca ativa |
| `programs` | programa, campanha, termos e planos versionados |
| `partnerships` | creator, candidatura, convite, membership, seleção de campanha e assets |
| `attribution` | cliques, webhooks, pedido e decisão de atribuição |
| `commissions` | cálculo, liquidação e ledger |
| `listening` | documento bruto, matching e revisão humana |
| `finance` | lote, reserva, payout e provedor |
| `agent_control` | finding, proposta, gates, aprovação e execução |
| `reporting` | projeções de leitura por programa, campanha e creator |

Os limites estão em um monólito modular porque o objetivo é estudar regras transacionais.
Eles podem ser extraídos depois que volume, equipe ou isolamento operacional justificarem a
complexidade distribuída.

As listas HTTP usam envelope `{items, total, limit, offset}` e ordenação estável.
Detalhes e relatórios são escopados pela marca autenticada; leituras do creator são
escopadas pela própria identidade. O [handoff do frontend](frontend-handoff.md) descreve
papéis, filtros, estados e erros.

## Consistência

Operações que alteram decisão ou dinheiro abrem uma transação no service. Locks
`SELECT ... FOR UPDATE`, uniques e índices parciais protegem invariantes concorrentes. O
evento de domínio entra na outbox dentro da mesma transação. A publicação é assíncrona e
`at-least-once`; cada consumer registra a inbox antes de aceitar efeitos posteriores.

O ledger usa pares de lançamentos por bucket:

```text
accrual:         pending +25
settlement:      pending -25, available +25
reservation:     available -25, reserved +25
confirmation:    reserved -25, paid +25
failure:         reserved -25, available +25
```

O total econômico não é obtido somando todos os buckets históricos sem contexto; o saldo de
cada bucket é a soma dos lançamentos daquele bucket.

## Payout ambíguo

```mermaid
sequenceDiagram
    participant API
    participant DB as PostgreSQL
    participant W as Worker
    participant P as Provider local
    participant H as Finance
    API->>DB: aprova lote e reserva saldo
    DB-->>W: outbox payout.requested
    W->>P: transferência + mesma idempotency key
    P->>P: persiste confirmação
    P--xW: timeout depois de processar
    W->>DB: payout = unknown; reserva permanece
    API->>P: reconciliação por idempotency key
    API->>DB: finding imutável + evidência + hash
    API->>DB: proposta sem efeito colateral
    API->>DB: gates determinísticos
    H->>DB: aprovação com comentário
    API->>DB: revalida versão, confirma e move reserved → paid
```

A aplicação nunca inventa uma segunda chave depois do timeout. Consultar o provider pela
chave original separa “não recebi resposta” de “não processou”.

## Segurança local

- Assinatura HMAC usa o corpo bruto do webhook e comparação constante.
- JWT de staff carrega uma marca ativa, mas cada request confirma o membership no banco.
- Services filtram a marca antes de carregar ou bloquear recursos.
- Erros usam Problem Details sem devolver stack trace ou existência de dados de outro tenant.
- Configuração local falha se os hosts de emulador estiverem ausentes, evitando fallback
  acidental para GCP real.
- CORS aceita somente as duas origens Vite locais configuradas por padrão.
- A identidade de posts sociais é `(brand_id, network, external_post_id)` em Postgres,
  Firestore e no evento; reimportar conteúdo revisado não reverte a decisão humana.

## Portabilidade futura

API e worker não dependem de disco local. Postgres, Pub/Sub e Firestore são acessados por
interfaces oficiais; variáveis de ambiente trocam endpoints. Isso deixa a imagem compatível
com um runtime como Cloud Run, mas nenhum recurso ou deploy cloud é criado nesta fase.
