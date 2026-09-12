# CreatorOps documentation

Documentação pública do protótipo:

- [architecture.md](architecture.md): serviços locais, limites de domínio e fluxo de dados.
- [Visão geral do negócio](../README.md#fluxo-de-negócio): jornada da marca e do creator até
  a comissão, o pagamento e a reconciliação.
- [domain-rules.md](domain-rules.md): seis diagramas detalhados com responsáveis, decisões,
  estados, invariantes e regras financeiras.
- [frontend-handoff.md](frontend-handoff.md): papéis, telas, contratos HTTP, paginação e erros
  para construir a interface local sem mocks.
- [../bruno/README.md](../bruno/README.md): execução da jornada completa pelo Bruno.

## Fluxos de negócio

1. [Programa e ativação do creator](domain-rules.md#programa-e-parceria)
2. [Venda e atribuição por cupom ou clique](domain-rules.md#atribuição)
3. [Comissão, liquidação e devoluções](domain-rules.md#comissão)
4. [Lote, reserva e pagamento](domain-rules.md#pagamento)
5. [Reconciliação e aprovação humana](domain-rules.md#controle-agêntico)
6. [Conteúdo social e mensuração](domain-rules.md#conteúdo-e-mensuração)
