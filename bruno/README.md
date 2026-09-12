# Coleção Bruno — CreatorOps Local

Esta coleção cobre todos os endpoints públicos da API principal e os endpoints do provedor
financeiro simulado. Ela também funciona como uma demonstração encadeada da regra de negócio.

## Como executar

1. Suba e alimente o backend com `make up` e `make seed`.
2. Abra a pasta `bruno/` no Bruno.
3. Selecione o ambiente `local`.
4. Execute a coleção inteira na ordem apresentada pelo Collection Runner.

O primeiro request cria um `run_id` novo e limpa as variáveis transitórias. Os scripts de
pós-resposta salvam IDs, tokens, cupom, link, clique, payout, finding e proposal para os
requests seguintes. Portanto, não é necessário copiar UUIDs manualmente.

## Jornada principal

```text
setup → autenticação → programa → creators → clique → venda → listening
      → reimportação segura → liquidação → payout unknown → reconciliação
      → gates → aprovação → execução → contratos de leitura e gestão
```

O webhook é assinado localmente no pre-request script com o segredo público do ambiente de
desenvolvimento. Os waits usados na ingestão e no payout existem porque o worker e o Pub/Sub
Emulator são assíncronos.

Os requests de `11-contract-checks` esperam respostas `401`, `403` e `409`; esses status
são sucesso do teste, pois comprovam segurança e idempotência. A pasta
`12-frontend-contracts` percorre convites, retirada de candidatura, seleção de campanha,
leituras paginadas, relatórios, auditoria e mudanças de estado. Seus dois últimos
requests comprovam que um lote fora de rascunho e um finding resolvido não podem ser
cancelados/encerrados.
