# CreatorOps documentation

Documentação pública do protótipo:

- [architecture.md](architecture.md): serviços locais, limites de domínio e fluxo de dados.
- [Visão geral do negócio](../README.md#fluxo-de-negócio): jornada da marca e do creator até
  a comissão, o pagamento e a reconciliação.
- [domain-rules.md](domain-rules.md): seis diagramas detalhados com responsáveis, decisões,
  estados, invariantes e regras financeiras.
- [../bruno/README.md](../bruno/README.md): execução da jornada completa pelo Bruno.

## Fluxos de negócio

1. [Programa e ativação do creator](domain-rules.md#programa-e-parceria)
2. [Venda e atribuição por cupom ou clique](domain-rules.md#atribuição)
3. [Comissão, liquidação e devoluções](domain-rules.md#comissão)
4. [Lote, reserva e pagamento](domain-rules.md#pagamento)
5. [Reconciliação e aprovação humana](domain-rules.md#controle-agêntico)
6. [Conteúdo social e mensuração](domain-rules.md#conteúdo-e-mensuração)

Materiais de pesquisa, documentos de vaga e anotações pessoais ficam somente em
`docs/private/`. Essa pasta é ignorada pelo Git para impedir publicação acidental de dados
pessoais ou de preparação para entrevista.
