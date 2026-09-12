# CreatorOps — frontend local

Interface em português para os quatro papéis do backend. React/Vite/TypeScript,
TanStack Router e Query, Tailwind, componentes shadcn/ui adaptados sobre Radix,
React Hook Form e validação Zod a partir do contrato OpenAPI.

## Executar

Na raiz do repositório:

```sh
make up
make seed
make demo
```

Na pasta `frontend/`:

```sh
npm ci
npm run dev
```

Abra http://localhost:5173. A API deve responder em http://localhost:8000/health/ready.
`owner@creatorops.dev`, `ops@creatorops.dev` e `finance@creatorops.dev` usam a senha
local `CreatorOps123!` e a marca `creatorops-demo`. Para creators, crie um perfil na
interface ou use o e-mail retornado pelo cenário abaixo; selecione **Creator** no login.
Essas são contas sintéticas da demonstração local.

Downloads de pacotes foram autorizados para instalação. Fontes Manrope, ícones e
assets são empacotados localmente; nenhuma CDN, telemetria, API social ou serviço cloud
é usado pelo frontend. Não é necessário servidor Node adicional à ferramenta Vite.

Durante `npm run dev`, o Vite encaminha `/api/*` para a API local na porta 8000.
Isso mantém as chamadas na origem do frontend e evita falhas de conexão do navegador
embutido. O build usa a origem documentada `http://localhost:8000` diretamente.

## Jornadas

- **Owner/ops:** Programas → detalhe → termos; planos são criados por owner/finance.
  Ative o programa após configurar termos e plano padrão. Campanhas, parcerias e
  convites ficam nas abas do programa. Convites mostram o link somente ao serem criados.
- **Creator:** descubra programas ativos, envie candidatura; após a revisão, abra
  a própria parceria, leia e aceite os termos vigentes. Assets e resultados aparecem
  na parceria. Novo termo obrigatório exige outro aceite.
- **Conteúdo:** importe posts preenchendo o formulário ou carregando JSON local
  (`{ "posts": [...] }` ou um array). Revise antes de confirmar. As métricas têm
  entradas numéricas; o worker faz matching e mantém a revisão humana na reimportação.
- **Financeiro:** comissões e ledger são separados. Criar lote produz snapshot;
  aprovar reserva saldo. Pagamento `unknown` permanece reservado e aponta à reconciliação.
- **Agentic:** reconciliação → divergência → gerar proposta → executar gates → aprovar
  com comentário → executar correção. A interface não aprova nem executa automaticamente.
  Encerrar a divergência manualmente não altera o ledger.
- **Resultados:** selecione um programa (staff) ou parceria própria (creator).
  Resultados de campanha ficam no detalhe da campanha. Valores vêm do backend,
  sem somar páginas ou ratear payout por campanha no navegador.

## Cenário financeiro para demonstração

`make demo` termina com a proposta executada. Para parar no estado desconhecido:

```sh
npm run demo:unknown
```

O comando cria registros sintéticos novos na API local, ativa um creator, envia uma
venda pelo webhook assinado **fora do navegador**, liquida a comissão e aprova um lote
com `timeout_after`. Exibe IDs, e-mail do creator e URL do lote; nunca imprime JWT ou
segredo HMAC. O segredo vem de `COMMERCE_WEBHOOK_SECRET`, do `.env` da raiz, ou do valor
local padrão do backend. A senha do creator desse cenário é `CreatorOps123!`.

Entre como finance, abra o lote retornado e siga reconciliação → divergência → proposta.
As ações permanecem explícitas; a reserva não é liberada por timeout.

## Contrato e organização

```sh
npm run api:generate   # exige OpenAPI local disponível; atualiza snapshot e tipos
npm run typecheck
npm run build
npm run test
npm run test:e2e       # API, worker e Vite ativos; usa Chrome local
npm run format:check
```

`src/api/` centraliza fetch, bearer, erros, query keys e tipos gerados.
`src/features/` define páginas, permissões, ações e composição dos domínios.
`src/components/` contém tabelas, estados, formulários e diálogos acessíveis.
`src/app/` mantém sessão, rotas, navegação e parâmetros de URL.
`scripts/` prepara cenários e gera contratos; não é importado pelo runtime do browser.

O token fica somente em `sessionStorage`; logout e `401` limpam token/cache e cancelam
leituras pendentes. Cada comando invalida as leituras relacionadas pelo namespace da API.
Mutations não têm retry nem atualização otimista. Diálogos de resultado ficam em um
provider independente para sobreviver à alteração dos botões após uma transição.

Toda lista usa paginação do servidor e seu `total`. Filtros/paginação ficam na URL;
as listas internas usam prefixos para não misturar parâmetros. Atualização é manual ou
opt-in por até um minuto, a cada três segundos, pausada em segundo plano. Pagamentos e
runs deixam de consultar ao atingir estados sem processamento pendente. A importação
não expõe um job consultável, portanto o acompanhamento de posts é limitado por tempo.

Dinheiro é mantido como string e formatado sem conversão numérica. Horários exibem o
fuso do navegador no cabeçalho; datas de formulário são enviadas como ISO com timezone.

## Decisões visuais e acessibilidade

Marfim, verde-petróleo e Manrope local, com números tabulares, espaço entre grupos e
superfícies discretas. Navegação se adapta ao papel. Menu lateral vira menu mobile;
tabelas mantêm rolagem interna em telas pequenas. Assets oferecem cópia de cupom/link.
Gates mostram código, resultado individual e evidência textual do servidor.

Radix gerencia foco, Escape e semântica de diálogos; botões têm feedback imediato,
focus visível e rótulos. Estados incluem texto/código além da cor. Há link de pular
para conteúdo e alternativas para movimento/transparência reduzidos e contraste maior.

## Limites e divergências verificadas

- API, models, migrations e regras de negócio não foram alterados.
- Não existe lista global de campanhas/memberships staff: a UI exige contexto do programa.
- `/payouts` e `/ledger-entries` são exclusivos de owner/finance. Creator usa somente
  contratos das próprias memberships; não existe listagem própria detalhada de payouts.
- Não existe detalhe individual de payout: abrir um pagamento leva ao snapshot do lote.
- Não existe endpoint de job de importação nem comando de matching manual. Matching é
  feito pelo worker. A UI permite importação, acompanhamento e nova revisão.
- O detalhe do post não expõe legenda nem URL; são exibidos os campos realmente retornados.
- A descoberta de programas por creator retorna ativos e ignora `program_status`; a UI
  não oferece esse filtro para creators.
- O backend envia `X-Request-ID`, mas não o expõe em CORS. O cliente mostra o ID quando
  acessível no header ou `meta`; no desenvolvimento, o proxy Vite permite ler o header.
  No build com chamadas diretas, permanece a limitação de CORS do backend.
- Explicações de domínio e evidências retornadas pelo backend podem estar em inglês;
  rótulos da interface são traduzidos e códigos reais permanecem próximos.
- Programas não têm datas no schema atual; somente campanhas expõem início e fim.
- Os testes E2E criam dados sintéticos persistentes com identificadores exclusivos; não
  apagam histórico nem alteram registros existentes. Não há mocks de API nos testes E2E.

Execute também `make verify` na raiz antes da revisão do diff. Resultados de screenshots
ficam em `test-results/`, ignorado pelo Git. Nenhum deploy faz parte desta entrega.
